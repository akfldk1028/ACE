"""Certify an authored visual mesh against floorwise legal Matrix4 evidence.

Capacity plates remain the only GFA authority.  This module carries only the
renderer-visible profiled mesh through the already-certified floor transforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite, sqrt
from typing import Any, Iterable, Sequence

from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import unary_union

from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume

from .affine_matrix import Matrix4, transform_point3, validate_matrix4


@dataclass(frozen=True)
class FloorwiseVisualProjectionCertificate:
    status: str
    hard_pass: bool
    failure_reasons: tuple[str, ...] = ()
    visual_hash: str = ""
    source_surface_count: int = 0
    projected_surface_count: int = 0
    legal_sample_count: int = 0
    capacity_gfa_m2: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.floorwise_visual_projection.v1",
            "status": self.status,
            "hard_pass": self.hard_pass,
            "failure_reasons": list(self.failure_reasons),
            "visual_hash": self.visual_hash,
            "source_surface_count": self.source_surface_count,
            "projected_surface_count": self.projected_surface_count,
            "legal_sample_count": self.legal_sample_count,
            "capacity_gfa_m2": round(self.capacity_gfa_m2, 4),
            "capacity_authority": "floorwise_legal_volumes",
            "source_surface_coordinate_frame": (
                "source_footprint_centroid_local_xy_normalized_z"
            ),
            "projected_surface_coordinate_frame": (
                "capacity_source_centroid_local_xy_normalized_z"
            ),
            "matrix_convention": "row_major_column_vector",
        }


@dataclass(frozen=True)
class FloorwiseVisualProjection:
    surfaces: tuple[SourceSurface, ...]
    certificate: FloorwiseVisualProjectionCertificate


def project_floorwise_visual_mesh(
    source: SourceMass,
    legal_sections: Sequence[Any],
    floor_matrices: Sequence[Sequence[Sequence[float]]],
    capacity_plates: Sequence[SourceVolume],
    *,
    output_origin: Sequence[float] | None = None,
) -> FloorwiseVisualProjection:
    """Project a complete authored triangle skin through the legal matrix field."""

    capacity_gfa = sum(
        max(0.0, float(plate.footprint.area))
        for plate in capacity_plates
    )
    profiled = tuple(
        surface
        for surface in source.surfaces
        if surface.surface_type.startswith("profiled_")
    )
    if not profiled:
        return _not_applicable(
            "not_applicable_no_authored_mesh",
            capacity_gfa=capacity_gfa,
        )
    completeness_failure = _profiled_export_completeness_failure(
        source,
        profiled,
    )
    if completeness_failure:
        return _failed(
            completeness_failure,
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    try:
        matrices = tuple(validate_matrix4(matrix) for matrix in floor_matrices)
    except (TypeError, ValueError):
        return _failed(
            "invalid_floorwise_visual_matrix",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )
    if (
        not matrices
        or len(matrices) != len(legal_sections)
        or not capacity_plates
    ):
        return _failed(
            "incomplete_floorwise_visual_projection_evidence",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    capacity_origin = (
        _validated_output_origin(output_origin)
        if output_origin is not None
        else _capacity_origin(capacity_plates)
    )
    if capacity_origin is None:
        return _failed(
            "invalid_capacity_source_centroid",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )
    source_origin = source.footprint.centroid
    breakpoints = tuple(
        (index + 0.5) / len(matrices)
        for index in range(len(matrices))
    )
    tessellation_levels = tuple(sorted({
        *breakpoints,
        *(
            index / len(matrices)
            for index in range(1, len(matrices))
        ),
    }))
    projected: list[SourceSurface] = []
    legal_sample_count = 0

    for surface in profiled:
        world_triangle = tuple(
            (
                float(source_origin.x) + float(x),
                float(source_origin.y) + float(y),
                float(z),
            )
            for x, y, z in surface.vertices_m
        )
        if not _finite_triangle(world_triangle):
            return _failed(
                "invalid_authored_visual_triangle",
                capacity_gfa=capacity_gfa,
                source_surface_count=len(profiled),
            )

        sample_points = _section_evidence_points(
            world_triangle,
            floor_count=len(matrices),
        )
        for point in sample_points:
            transformed = _transform_with_matrix_field(
                matrices,
                point,
                breakpoints=breakpoints,
            )
            if not _legal_sections_cover_point(
                transformed,
                legal_sections=legal_sections,
            ):
                return _failed(
                    "projected_visual_mesh_outside_legal_section",
                    capacity_gfa=capacity_gfa,
                    source_surface_count=len(profiled),
                    legal_sample_count=legal_sample_count + 1,
                )
            legal_sample_count += 1

        pieces = _split_triangle_at_z_breakpoints(
            world_triangle,
            breakpoints=tessellation_levels,
        )
        for piece_index, piece in enumerate(pieces, start=1):
            transformed = tuple(
                _transform_with_matrix_field(
                    matrices,
                    point,
                    breakpoints=breakpoints,
                )
                for point in piece
            )
            if not _finite_triangle(transformed):
                return _failed(
                    "degenerate_projected_visual_triangle",
                    capacity_gfa=capacity_gfa,
                    source_surface_count=len(profiled),
                    legal_sample_count=legal_sample_count,
                )
            legal_indices = _legal_section_indices_for_triangle(
                transformed,
                section_count=len(legal_sections),
            )
            if not _legal_sections_cover_triangle(
                transformed,
                legal_sections=legal_sections,
                legal_indices=legal_indices,
            ):
                return _failed(
                    "projected_visual_mesh_outside_legal_section",
                    capacity_gfa=capacity_gfa,
                    source_surface_count=len(profiled),
                    legal_sample_count=legal_sample_count + len(legal_indices),
                )
            legal_sample_count += len(legal_indices)
            boundary_sample_count = _boundary_intersection_sample_count(
                transformed,
                legal_sections=legal_sections,
            )
            if boundary_sample_count is None:
                return _failed(
                    "projected_visual_mesh_outside_legal_section",
                    capacity_gfa=capacity_gfa,
                    source_surface_count=len(profiled),
                    legal_sample_count=legal_sample_count + 1,
                )
            legal_sample_count += boundary_sample_count
            local = tuple(
                (
                    x - capacity_origin[0],
                    y - capacity_origin[1],
                    z,
                )
                for x, y, z in transformed
            )
            projected.append(SourceSurface(
                role=(
                    surface.role
                    if len(pieces) == 1
                    else f"{surface.role}:projected_piece_{piece_index:02d}"
                ),
                volume_role=surface.volume_role,
                verb=surface.verb,
                surface_type=surface.surface_type,
                vertices_m=local,
                operator=surface.operator,
                semantic_patch_id=surface.semantic_patch_id,
            ))

    surfaces = tuple(projected)
    visual_hash = _stable_visual_hash(surfaces)
    return FloorwiseVisualProjection(
        surfaces=surfaces,
        certificate=FloorwiseVisualProjectionCertificate(
            status="certified",
            hard_pass=True,
            visual_hash=visual_hash,
            source_surface_count=len(profiled),
            projected_surface_count=len(surfaces),
            legal_sample_count=legal_sample_count,
            capacity_gfa_m2=capacity_gfa,
        ),
    )


def _not_applicable(
    status: str,
    *,
    capacity_gfa: float,
    source_surface_count: int = 0,
) -> FloorwiseVisualProjection:
    return FloorwiseVisualProjection(
        surfaces=(),
        certificate=FloorwiseVisualProjectionCertificate(
            status=status,
            hard_pass=True,
            source_surface_count=source_surface_count,
            capacity_gfa_m2=capacity_gfa,
        ),
    )


def _failed(
    reason: str,
    *,
    capacity_gfa: float,
    source_surface_count: int,
    legal_sample_count: int = 0,
) -> FloorwiseVisualProjection:
    return FloorwiseVisualProjection(
        surfaces=(),
        certificate=FloorwiseVisualProjectionCertificate(
            status="failed",
            hard_pass=False,
            failure_reasons=(reason,),
            source_surface_count=source_surface_count,
            legal_sample_count=legal_sample_count,
            capacity_gfa_m2=capacity_gfa,
        ),
    )


def _profiled_export_completeness_failure(
    source: SourceMass,
    surfaces: tuple[SourceSurface, ...],
) -> str:
    if (
        len(surfaces) != len(source.surfaces)
        or any(len(surface.vertices_m) != 3 for surface in surfaces)
    ):
        return "incomplete_authored_mesh_export"
    bridge = source.metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    raw_count = int(bridge.get("raw_mesh_triangle_count") or 0)
    exported_count = int(bridge.get("exported_surface_count") or 0)
    if raw_count or exported_count:
        return (
            ""
            if raw_count == exported_count == len(surfaces)
            else "incomplete_authored_mesh_export"
        )
    return (
        ""
        if _has_closed_directed_edge_topology(surfaces)
        else "unproven_authored_mesh_completeness"
    )


def _has_closed_directed_edge_topology(
    surfaces: tuple[SourceSurface, ...],
) -> bool:
    directed_counts: dict[
        tuple[tuple[float, float, float], tuple[float, float, float]],
        int,
    ] = {}
    for surface in surfaces:
        vertices = tuple(
            (round(float(x), 8), round(float(y), 8), round(float(z), 8))
            for x, y, z in surface.vertices_m
        )
        for left, right in zip(vertices, (*vertices[1:], vertices[0])):
            directed_counts[(left, right)] = (
                directed_counts.get((left, right), 0) + 1
            )
    return bool(directed_counts) and all(
        count == 1
        and directed_counts.get((right, left), 0) == 1
        for (left, right), count in directed_counts.items()
    )


def _capacity_origin(
    capacity_plates: Sequence[SourceVolume],
) -> tuple[float, float] | None:
    minimum_bottom = min(
        (float(plate.bottom_fraction) for plate in capacity_plates),
        default=None,
    )
    if minimum_bottom is None:
        return None
    ground = unary_union([
        plate.footprint
        for plate in capacity_plates
        if abs(float(plate.bottom_fraction) - minimum_bottom) <= 1e-8
    ])
    if ground.is_empty:
        return None
    center = ground.centroid
    if not (isfinite(float(center.x)) and isfinite(float(center.y))):
        return None
    return float(center.x), float(center.y)


def _validated_output_origin(
    output_origin: Sequence[float],
) -> tuple[float, float] | None:
    try:
        values = tuple(float(value) for value in output_origin)
    except (TypeError, ValueError):
        return None
    if len(values) != 2 or not all(isfinite(value) for value in values):
        return None
    return values


def _matrix_at_z(
    matrices: tuple[Matrix4, ...],
    z: float,
    *,
    breakpoints: tuple[float, ...],
) -> Matrix4:
    if len(matrices) == 1 or z <= breakpoints[0]:
        return matrices[0]
    if z >= breakpoints[-1]:
        return matrices[-1]
    for index, (lower, upper) in enumerate(zip(breakpoints, breakpoints[1:])):
        if lower <= z <= upper:
            amount = (z - lower) / max(upper - lower, 1e-12)
            return tuple(tuple(
                matrices[index][row][column] * (1.0 - amount)
                + matrices[index + 1][row][column] * amount
                for column in range(4)
            ) for row in range(4))
    return matrices[-1]


def _transform_with_matrix_field(
    matrices: tuple[Matrix4, ...],
    point: tuple[float, float, float],
    *,
    breakpoints: tuple[float, ...],
) -> tuple[float, float, float]:
    return transform_point3(
        _matrix_at_z(matrices, point[2], breakpoints=breakpoints),
        point,
    )


def _legal_sections_cover_point(
    point: tuple[float, float, float],
    *,
    legal_sections: Sequence[Any],
) -> bool:
    x, y, z = point
    count = len(legal_sections)
    probe = Point(x, y)
    if z <= 0.0:
        indices = (0,)
    elif z >= 1.0:
        indices = (count - 1,)
    else:
        scaled = z * count
        boundary = round(scaled)
        if abs(scaled - boundary) <= 1e-8 and 0 < boundary < count:
            indices = (boundary - 1, boundary)
        else:
            indices = (min(count - 1, int(scaled)),)
    return all(legal_sections[index].buffer(1e-7).covers(probe) for index in indices)


def _legal_section_indices_for_triangle(
    triangle: tuple[tuple[float, float, float], ...],
    *,
    section_count: int,
) -> tuple[int, ...]:
    minimum_z = max(0.0, min(1.0, min(point[2] for point in triangle)))
    maximum_z = max(0.0, min(1.0, max(point[2] for point in triangle)))
    middle_z = (minimum_z + maximum_z) / 2.0
    primary = min(section_count - 1, max(0, int(middle_z * section_count)))
    return (primary,)


def _legal_sections_cover_triangle(
    triangle: tuple[tuple[float, float, float], ...],
    *,
    legal_sections: Sequence[Any],
    legal_indices: Sequence[int],
) -> bool:
    coordinates = [(float(x), float(y)) for x, y, _z in triangle]
    polygon = Polygon(coordinates)
    projected = (
        polygon
        if not polygon.is_empty and polygon.area > 1e-12
        else LineString((*coordinates, coordinates[0]))
    )
    if projected.is_empty:
        return False
    return all(
        legal_sections[index].buffer(1e-7).covers(projected)
        for index in legal_indices
    )


def _boundary_intersection_sample_count(
    triangle: tuple[tuple[float, float, float], ...],
    *,
    legal_sections: Sequence[Any],
) -> int | None:
    count = len(legal_sections)
    sample_count = 0
    for boundary in range(1, count):
        level = boundary / count
        points = _triangle_plane_intersections(triangle, level)
        unique = tuple(dict.fromkeys(
            (
                round(float(x), 10),
                round(float(y), 10),
            )
            for x, y, _z in points
        ))
        if not unique:
            continue
        intersection = (
            Point(unique[0])
            if len(unique) == 1
            else MultiPoint(unique).convex_hull
        )
        if not all(
            legal_sections[index].buffer(1e-7).covers(intersection)
            for index in (boundary - 1, boundary)
        ):
            return None
        sample_count += 2
    return sample_count


def _section_evidence_points(
    triangle: tuple[tuple[float, float, float], ...],
    *,
    floor_count: int,
) -> tuple[tuple[float, float, float], ...]:
    points = list(triangle)
    points.extend(
        tuple((left[index] + right[index]) / 2.0 for index in range(3))
        for left, right in zip(triangle, (*triangle[1:], triangle[0]))
    )
    points.append(tuple(sum(vertex[index] for vertex in triangle) / 3.0 for index in range(3)))
    levels = {
        index / floor_count
        for index in range(floor_count + 1)
    } | {
        (index + 0.5) / floor_count
        for index in range(floor_count)
    }
    for level in sorted(levels):
        points.extend(_triangle_plane_intersections(triangle, level))
    unique = {
        (
            round(float(point[0]), 10),
            round(float(point[1]), 10),
            round(float(point[2]), 10),
        )
        for point in points
    }
    return tuple(sorted(unique))


def _triangle_plane_intersections(
    triangle: tuple[tuple[float, float, float], ...],
    level: float,
) -> tuple[tuple[float, float, float], ...]:
    points: list[tuple[float, float, float]] = []
    for left, right in zip(triangle, (*triangle[1:], triangle[0])):
        left_delta = left[2] - level
        right_delta = right[2] - level
        if abs(left_delta) <= 1e-10:
            points.append(left)
        if left_delta * right_delta < -1e-12:
            amount = (level - left[2]) / (right[2] - left[2])
            points.append(tuple(
                left[index] + (right[index] - left[index]) * amount
                for index in range(3)
            ))
    return tuple(points)


def _split_triangle_at_z_breakpoints(
    triangle: tuple[tuple[float, float, float], ...],
    *,
    breakpoints: Sequence[float],
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    polygons: list[tuple[tuple[float, float, float], ...]] = [triangle]
    for level in breakpoints:
        split: list[tuple[tuple[float, float, float], ...]] = []
        for polygon in polygons:
            minimum_z = min(point[2] for point in polygon)
            maximum_z = max(point[2] for point in polygon)
            if (
                maximum_z <= level + 1e-10
                or minimum_z >= level - 1e-10
            ):
                split.append(polygon)
                continue
            below = _clip_polygon_z(polygon, level=level, keep_below=True)
            above = _clip_polygon_z(polygon, level=level, keep_below=False)
            if len(below) >= 3:
                split.append(below)
            if len(above) >= 3:
                split.append(above)
        polygons = split
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    seen: set[tuple[tuple[float, float, float], ...]] = set()
    for polygon in polygons:
        for index in range(1, len(polygon) - 1):
            piece = (polygon[0], polygon[index], polygon[index + 1])
            key = tuple(sorted(
                (
                    round(float(x), 10),
                    round(float(y), 10),
                    round(float(z), 10),
                )
                for x, y, z in piece
            ))
            if _finite_triangle(piece) and key not in seen:
                seen.add(key)
                triangles.append(piece)
    return tuple(triangles)


def _clip_polygon_z(
    polygon: tuple[tuple[float, float, float], ...],
    *,
    level: float,
    keep_below: bool,
) -> tuple[tuple[float, float, float], ...]:
    def inside(point: tuple[float, float, float]) -> bool:
        return point[2] <= level + 1e-10 if keep_below else point[2] >= level - 1e-10

    result: list[tuple[float, float, float]] = []
    previous = polygon[-1]
    previous_inside = inside(previous)
    for current in polygon:
        current_inside = inside(current)
        if current_inside != previous_inside:
            amount = (level - previous[2]) / (current[2] - previous[2])
            result.append(tuple(
                previous[index] + (current[index] - previous[index]) * amount
                for index in range(3)
            ))
        if current_inside:
            result.append(current)
        previous = current
        previous_inside = current_inside
    return tuple(result)


def _finite_triangle(
    triangle: Iterable[tuple[float, float, float]],
) -> bool:
    vertices = tuple(triangle)
    if len(vertices) != 3 or not all(
        isfinite(value)
        for vertex in vertices
        for value in vertex
    ):
        return False
    left = tuple(vertices[1][index] - vertices[0][index] for index in range(3))
    right = tuple(vertices[2][index] - vertices[0][index] for index in range(3))
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    return sqrt(sum(value * value for value in cross)) > 1e-10


def _stable_visual_hash(surfaces: tuple[SourceSurface, ...]) -> str:
    payload = [
        {
            "role": surface.role,
            "volume_role": surface.volume_role,
            "surface_type": surface.surface_type,
            "semantic_patch_id": surface.semantic_patch_id,
            "vertices": [
                [round(float(x), 8), round(float(y), 8), round(float(z), 8)]
                for x, y, z in surface.vertices_m
            ],
        }
        for surface in surfaces
    ]
    return sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


__all__ = [
    "FloorwiseVisualProjection",
    "FloorwiseVisualProjectionCertificate",
    "project_floorwise_visual_mesh",
]
