"""Bounded numeric repair and section evidence for profiled legal meshes."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Sequence

import manifold3d as m3d
import numpy as np
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from .compiler import CompilationResult, revalidate_compilation_mesh
from .gate import GeometryGatePolicy, compilation_gate


FLOOR_CENTER_NUMERIC_EQUIVALENCE_SCHEMA = (
    "arr.maas.floor_center_numeric_equivalence.v1"
)
FLOOR_CENTER_NUMERIC_EQUIVALENCE_REPAIR_SCHEMA = (
    "arr.maas.floor_center_numeric_equivalence.v2"
)
MESH_NUMERIC_REPAIR_SCHEMA = "arr.maas.profiled_mesh_numeric_repair.v1"
SECTION_EXTRACTOR_EPSILON_M = 1e-6
SECTION_ROUNDING_BUDGET_M = 2e-8
MAXIMUM_CLEANUP_DISPLACEMENT_M = 5e-7
_COLLAPSE_THRESHOLDS_M = (1e-8, 3e-8, 1e-7, 3e-7, 5e-7)


@dataclass(frozen=True)
class ProfiledMeshNumericRepair:
    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]
    collapse_threshold_m: float
    max_physical_displacement_m: float
    raw_indexed_mesh_hash: str
    raw_gate_failure_codes: tuple[str, ...]
    clean_indexed_mesh_hash: str
    clean_gate_hard_pass: bool = True


def revalidated_profiled_mesh(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
) -> CompilationResult | None:
    result, failures = _revalidated_result(vertices, triangles)
    return result if not failures else None


def repair_profiled_indexed_mesh(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    *,
    effective_height_m: float,
) -> ProfiledMeshNumericRepair | None:
    """Collapse only a raw mesh whose sole unchanged-gate issue is tiny_edge."""

    _raw_result, raw_failures = _revalidated_result(vertices, triangles)
    if raw_failures != ("tiny_edge",):
        return None
    raw_hash = indexed_mesh_hash(vertices, triangles)
    for threshold in _COLLAPSE_THRESHOLDS_M:
        collapsed = _collapse_edges(
            vertices,
            triangles,
            maximum_length=threshold,
            effective_height_m=effective_height_m,
        )
        if collapsed is None:
            continue
        clean_vertices, clean_triangles, displacement = collapsed
        _clean_result, clean_failures = _revalidated_result(
            clean_vertices,
            clean_triangles,
        )
        if clean_failures:
            continue
        return ProfiledMeshNumericRepair(
            vertices=clean_vertices,
            triangles=clean_triangles,
            collapse_threshold_m=threshold,
            max_physical_displacement_m=displacement,
            raw_indexed_mesh_hash=raw_hash,
            raw_gate_failure_codes=raw_failures,
            clean_indexed_mesh_hash=indexed_mesh_hash(
                clean_vertices,
                clean_triangles,
            ),
        )
    return None


def section_numeric_epsilon_m(cleanup_displacement_m: float) -> float:
    displacement = float(cleanup_displacement_m)
    if displacement <= 0.0:
        return SECTION_EXTRACTOR_EPSILON_M
    if (
        not isfinite(displacement)
        or displacement > MAXIMUM_CLEANUP_DISPLACEMENT_M
    ):
        raise ValueError("mesh cleanup displacement exceeds numeric contract")
    return (
        SECTION_EXTRACTOR_EPSILON_M
        + displacement
        + SECTION_ROUNDING_BUDGET_M
    )


def floor_center_numeric_equivalence(
    measured: Any,
    expected: Any,
    *,
    epsilon_m: float = SECTION_EXTRACTOR_EPSILON_M,
    contour_count: int | None = None,
) -> dict[str, Any] | None:
    """Certify one reconstructed section without hiding topology changes."""

    if not _valid_polygonal(measured) or not _valid_polygonal(expected):
        return None
    measured_components = _components(measured)
    expected_components = _components(expected)
    measured_holes = sum(len(component.interiors) for component in measured_components)
    expected_holes = sum(len(component.interiors) for component in expected_components)
    area_delta = abs(float(measured.area) - float(expected.area))
    symdiff = float(measured.symmetric_difference(expected).area)
    hausdorff = float(
        measured.boundary.hausdorff_distance(expected.boundary)
    )
    area_bound = (
        SECTION_EXTRACTOR_EPSILON_M
        + float(expected.length) * float(epsilon_m)
    )
    hausdorff_bound = max(
        float(epsilon_m),
        SECTION_EXTRACTOR_EPSILON_M
        + MAXIMUM_CLEANUP_DISPLACEMENT_M
        + SECTION_ROUNDING_BUDGET_M,
    )
    values = (
        area_delta,
        symdiff,
        hausdorff,
        area_bound,
        hausdorff_bound,
    )
    if not all(isfinite(value) for value in values):
        return None
    failed_predicates = []
    if len(measured_components) != len(expected_components):
        failed_predicates.append("component_count_mismatch")
    if measured_holes != expected_holes:
        failed_predicates.append("hole_count_mismatch")
    if area_delta > area_bound:
        failed_predicates.append("area_delta_exceeds_bound")
    if symdiff > area_bound:
        failed_predicates.append("symmetric_difference_exceeds_bound")
    if hausdorff > hausdorff_bound:
        failed_predicates.append("hausdorff_distance_exceeds_bound")
    return {
        "hard_pass": not failed_predicates,
        "area_delta_m2": area_delta,
        "symdiff_m2": symdiff,
        "hausdorff_m": hausdorff,
        "area_bound_m2": area_bound,
        "hausdorff_bound_m": hausdorff_bound,
        "failed_predicates": failed_predicates,
        "component_count": len(measured_components),
        "hole_count": measured_holes,
        "expected_component_count": len(expected_components),
        "expected_hole_count": expected_holes,
        "contour_count": int(
            contour_count
            if contour_count is not None
            else len(measured_components) + measured_holes
        ),
    }


def indexed_mesh_section_polygon(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    z: float,
) -> Polygon | MultiPolygon | None:
    """Kernel-slice the final indexed payload without flattening topology."""

    measured = indexed_mesh_section_topology(vertices, triangles, z)
    return measured[0] if measured is not None else None


def indexed_mesh_section_topology(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    z: float,
) -> tuple[Polygon | MultiPolygon, int, int] | None:
    """Return complete polygonal section, contour count, and solid count."""

    try:
        mesh = m3d.Mesh(
            np.asarray(vertices, dtype=np.float64),
            np.asarray(triangles, dtype=np.uint32),
        )
        mesh.merge()
        solid = m3d.Manifold(mesh)
        section = solid.slice(float(z))
        contours = section.to_polygons()
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return None
    if (
        solid.is_empty()
        or "NoError" not in str(solid.status())
        or section.is_empty()
        or int(section.num_contour()) <= 0
        or len(contours) != int(section.num_contour())
    ):
        return None
    polygonal = _polygonal_from_contours(contours)
    if polygonal is None:
        return None
    return polygonal, int(section.num_contour()), len(solid.decompose())


def profiled_surface_section_polygon(
    surfaces: Sequence[Any],
    *,
    origin_xy: tuple[float, float],
    z: float,
) -> Polygon | MultiPolygon | None:
    """Kernel-slice a complete triangle-surface transport payload."""

    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for surface in surfaces:
        triangle = tuple(getattr(surface, "vertices_m", ()) or ())
        if len(triangle) != 3:
            return None
        offset = len(vertices)
        vertices.extend(
            (
                float(point[0]) + float(origin_xy[0]),
                float(point[1]) + float(origin_xy[1]),
                float(point[2]),
            )
            for point in triangle
        )
        triangles.append((offset, offset + 1, offset + 2))
    return indexed_mesh_section_polygon(
        tuple(vertices),
        tuple(triangles),
        z,
    )


def indexed_mesh_hash(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
) -> str:
    payload = {
        "vertices": [[float(value) for value in vertex] for vertex in vertices],
        "triangles": [[int(value) for value in triangle] for triangle in triangles],
    }
    return sha256(json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")).hexdigest()


def _revalidated_result(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
) -> tuple[CompilationResult, tuple[str, ...]]:
    result = revalidate_compilation_mesh(CompilationResult(
        program=None,  # type: ignore[arg-type]
        status="compiled",
        vertices=vertices,
        triangles=triangles,
    ))
    structural = (
        result.status == "compiled"
        and result.metrics.get("watertight") is True
        and result.metrics.get("closed_solid") is True
        and result.metrics.get("manifold") is True
        and result.metrics.get("self_intersection_checked_by_kernel") is True
        and result.metrics.get("outward_normals") is True
        and float(result.metrics.get("volume") or 0.0) > 0.0
        and int(result.metrics.get("component_count") or 0) >= 1
    )
    failures = tuple(
        issue.code
        for issue in compilation_gate(
            result,
            GeometryGatePolicy(maximum_components=max(
                1,
                int(result.metrics.get("component_count") or 0),
            )),
        )
    )
    if not structural and not failures:
        failures = ("mesh_structural_revalidation_failed",)
    return result, failures


def _collapse_edges(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    *,
    maximum_length: float,
    effective_height_m: float,
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, int, int], ...],
    float,
] | None:
    parent = list(range(len(vertices)))
    if not isfinite(effective_height_m) or effective_height_m <= 0.0:
        return None

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    edges = {
        tuple(sorted((int(triangle[left]), int(triangle[right]))))
        for triangle in triangles
        for left, right in ((0, 1), (1, 2), (2, 0))
    }
    collapsed_count = 0
    for left, right in sorted(edges, key=lambda edge: (
        sum(
            (vertices[edge[0]][axis] - vertices[edge[1]][axis]) ** 2
            for axis in range(2)
        ) + (
            (vertices[edge[0]][2] - vertices[edge[1]][2])
            * effective_height_m
        ) ** 2,
        vertices[edge[0]],
        vertices[edge[1]],
    )):
        distance_squared = (
            sum(
            (vertices[left][axis] - vertices[right][axis]) ** 2
            for axis in range(2)
            )
            + (
                (vertices[left][2] - vertices[right][2])
                * effective_height_m
            ) ** 2
        )
        if distance_squared >= maximum_length * maximum_length:
            continue
        left_root, right_root = root(left), root(right)
        if left_root == right_root:
            continue
        retained, removed = sorted(
            (left_root, right_root),
            key=lambda index: (vertices[index], index),
        )
        parent[removed] = retained
        collapsed_count += 1
    if not collapsed_count:
        return None

    remapped = tuple(
        tuple(root(index) for index in triangle)
        for triangle in triangles
    )
    surviving = tuple(
        triangle for triangle in remapped
        if len(set(triangle)) == 3
    )
    used = tuple(sorted(
        {index for triangle in surviving for index in triangle},
        key=lambda index: (vertices[index], index),
    ))
    compact = {old: new for new, old in enumerate(used)}
    compact_vertices = tuple(vertices[index] for index in used)
    compact_triangles = tuple(sorted(
        (
            _rotate_triangle(tuple(compact[index] for index in triangle))
            for triangle in surviving
        ),
        key=lambda triangle: tuple(
            compact_vertices[index]
            for index in triangle
        ),
    ))
    max_displacement = max(
        (
            sum(
            (
                vertices[index][axis]
                - vertices[root(index)][axis]
            ) ** 2
            for axis in range(2)
            )
            + (
                (
                    vertices[index][2]
                    - vertices[root(index)][2]
                )
                * effective_height_m
            ) ** 2
        ) ** 0.5
        for index in range(len(vertices))
    )
    if max_displacement > min(
        maximum_length,
        MAXIMUM_CLEANUP_DISPLACEMENT_M,
    ) + 1e-12:
        return None
    return compact_vertices, compact_triangles, max_displacement


def _components(value: Any) -> tuple[Polygon, ...]:
    if isinstance(value, Polygon):
        return (value,)
    if isinstance(value, MultiPolygon):
        return tuple(sorted(
            value.geoms,
            key=lambda component: component.normalize().wkb_hex,
        ))
    return ()


def _valid_polygonal(value: Any) -> bool:
    return bool(
        isinstance(value, (Polygon, MultiPolygon))
        and not value.is_empty
        and value.is_valid
        and isfinite(float(value.area))
        and float(value.area) > 1e-8
    )


def _polygonal_from_contours(contours: Sequence[Any]) -> Polygon | MultiPolygon | None:
    rings = []
    for contour in contours:
        coordinates = tuple(
            (float(point[0]), float(point[1]))
            for point in contour
        )
        ring = Polygon(coordinates)
        if ring.is_empty or not ring.is_valid or float(ring.area) <= 1e-8:
            return None
        rings.append(ring)
    parents: list[int | None] = []
    for index, ring in enumerate(rings):
        point = ring.representative_point()
        containers = [
            candidate
            for candidate, outer in enumerate(rings)
            if candidate != index
            and float(outer.area) > float(ring.area)
            and outer.covers(point)
        ]
        parents.append(
            min(containers, key=lambda item: rings[item].area)
            if containers else None
        )
    depths = []
    for index in range(len(rings)):
        depth = 0
        parent = parents[index]
        seen = {index}
        while parent is not None:
            if parent in seen:
                return None
            seen.add(parent)
            depth += 1
            parent = parents[parent]
        depths.append(depth)
    polygons = []
    for index, ring in enumerate(rings):
        if depths[index] % 2:
            continue
        holes = [
            tuple(rings[child].exterior.coords)
            for child, parent in enumerate(parents)
            if parent == index and depths[child] == depths[index] + 1
        ]
        polygons.append(Polygon(tuple(ring.exterior.coords), holes=holes))
    result = unary_union(polygons).normalize()
    return result if _valid_polygonal(result) else None


def _rotate_triangle(
    triangle: tuple[int, int, int],
) -> tuple[int, int, int]:
    rotations = (
        triangle,
        (triangle[1], triangle[2], triangle[0]),
        (triangle[2], triangle[0], triangle[1]),
    )
    return min(rotations)


__all__ = [
    "FLOOR_CENTER_NUMERIC_EQUIVALENCE_SCHEMA",
    "FLOOR_CENTER_NUMERIC_EQUIVALENCE_REPAIR_SCHEMA",
    "MAXIMUM_CLEANUP_DISPLACEMENT_M",
    "MESH_NUMERIC_REPAIR_SCHEMA",
    "ProfiledMeshNumericRepair",
    "floor_center_numeric_equivalence",
    "indexed_mesh_section_polygon",
    "indexed_mesh_section_topology",
    "profiled_surface_section_polygon",
    "repair_profiled_indexed_mesh",
    "revalidated_profiled_mesh",
    "section_numeric_epsilon_m",
]
