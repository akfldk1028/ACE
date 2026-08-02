"""Exact legal-solid clipping for authored floorwise profiled meshes.

The authored indexed manifold is tessellated through the existing piecewise
floor Matrix4 field, then intersected with the union of the matching legal
floor prisms. Capacity plates remain unchanged and remain the sole GFA
authority.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Sequence

import manifold3d as m3d
import numpy as np
from shapely.geometry import MultiPoint, Polygon
from shapely.geometry.polygon import orient

from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume

from .affine_matrix import Matrix4, validate_matrix4
from .ast import GeometryProgram
from .floorwise_visual_projection import (
    FloorwiseVisualProjection,
    FloorwiseVisualProjectionCertificate,
    _exact_surface_payload_hash,
    _split_triangle_at_z_breakpoints,
    _stable_visual_hash,
    _transform_with_matrix_field,
    floorwise_authority_binding_hash,
    profiled_sloped_mesh_evidence,
)
from .profiled_mesh_numeric_repair import (
    FLOOR_CENTER_NUMERIC_EQUIVALENCE_REPAIR_SCHEMA,
    FLOOR_CENTER_NUMERIC_EQUIVALENCE_SCHEMA,
    MESH_NUMERIC_REPAIR_SCHEMA,
    floor_center_numeric_equivalence as _floor_center_numeric_equivalence,
    indexed_mesh_section_polygon as _indexed_mesh_section_polygon,
    repair_profiled_indexed_mesh,
    revalidated_profiled_mesh as _revalidated_mesh,
    section_numeric_epsilon_m as _section_numeric_epsilon_m,
)


_MODE = "floorwise_profiled_legal_clip"
_OPERATION = "authored_profiled_mesh_legal_solid_intersection"
_EPSILON = 1e-8


def clip_profiled_mesh_to_floorwise_legal_solids(
    source: SourceMass,
    *,
    occupied_sections: Sequence[Polygon],
    legal_sections: Sequence[Polygon],
    floor_matrices: Sequence[Matrix4],
    capacity_plates: Sequence[SourceVolume],
    output_origin: tuple[float, float],
) -> FloorwiseVisualProjection:
    """Return one exact authored visual solid or a fail-closed certificate."""

    profiled = tuple(
        surface
        for surface in source.surfaces
        if (
            isinstance(surface, SourceSurface)
            and surface.surface_type == "profiled_recursive_solid_mesh"
            and len(surface.vertices_m) == 3
        )
    )
    floor_count = len(occupied_sections)
    canonical_capacity_plates = tuple(sorted(
        capacity_plates,
        key=lambda plate: (
            float(plate.bottom_fraction),
            float(plate.top_fraction),
            str(plate.role),
            str(plate.footprint.normalize().wkb_hex),
        ),
    ))
    capacity_gfa = sum(
        float(plate.footprint.area)
        for plate in canonical_capacity_plates
    )
    if not profiled:
        return _failed(
            "profiled_legal_clip_missing_authored_mesh",
            capacity_gfa=capacity_gfa,
            source_surface_count=0,
        )
    if not _complete_profiled_export(source, profiled):
        return _failed(
            "profiled_legal_clip_incomplete_authored_mesh",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )
    if (
        floor_count == 0
        or len(legal_sections) != floor_count
        or len(floor_matrices) != floor_count
        or any(
            not _single_ring(section)
            for section in (*occupied_sections, *legal_sections)
        )
    ):
        return _failed(
            "profiled_legal_clip_topology_ambiguous",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    stack = source.metadata.get("floorwise_legal_matrix_stack")
    stack = stack if isinstance(stack, dict) else {}
    from .floorwise_section_loft import floorwise_authority_component_hashes

    components, component_failure = floorwise_authority_component_hashes(
        occupied_sections,
        canonical_capacity_plates,
        floor_capacity_plan_hash=str(
            stack.get("floor_capacity_plan_hash") or ""
        ),
        floor_evidence=stack.get("floors"),
    )
    if components is None:
        return _failed(
            component_failure.replace("section_loft", "profiled_legal_clip"),
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )
    try:
        matrices = tuple(validate_matrix4(matrix) for matrix in floor_matrices)
        evidence_matrices = tuple(
            validate_matrix4(row["matrix4"])
            for row in stack["floors"]
        )
    except (KeyError, TypeError, ValueError):
        return _failed(
            "profiled_legal_clip_missing_authority_evidence",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )
    if matrices != evidence_matrices:
        return _failed(
            "profiled_legal_clip_matrix_authority_mismatch",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    try:
        if any(not _plan_only_matrix(matrix) for matrix in matrices):
            raise ValueError("floor Matrix4 changes normalized z")
        projected_authored = _source_world_matrix_field_manifold(
            source,
            profiled,
            matrices,
        )
        if (
            projected_authored.is_empty()
            or "NoError" not in str(projected_authored.status())
        ):
            raise ValueError("projected authored mesh is not a manifold")
    except (AttributeError, TypeError, ValueError):
        return _failed(
            "profiled_legal_clip_invalid_authored_manifold",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    try:
        legal_bands = []
        for floor_index, legal in enumerate(legal_sections):
            lower = floor_index / floor_count
            upper = (floor_index + 1) / floor_count
            legal_bands.append(_legal_prism(
                legal,
                lower_z=lower,
                upper_z=upper,
            ))
        legal_stack = m3d.Manifold.batch_boolean(
            legal_bands,
            m3d.OpType.Add,
        )
        projected = m3d.Manifold.batch_boolean(
            [projected_authored, legal_stack],
            m3d.OpType.Intersect,
        )
        if (
            projected.is_empty()
            or "NoError" not in str(projected.status())
            or len(projected.decompose()) != 1
        ):
            raise ValueError("profiled legal bands do not form one solid")
        surfaces, vertices, triangles = _surfaces_from_manifold(
            projected,
            output_origin=output_origin,
            volume_role=canonical_capacity_plates[0].role,
        )
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return _failed(
            "profiled_legal_clip_csg_failed",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    mesh_cleanup_schema = ""
    mesh_cleanup_collapse_threshold_m = 0.0
    effective_height_m = _effective_height_m(source)
    mesh_cleanup_max_physical_displacement_m = 0.0
    mesh_cleanup_raw_indexed_mesh_hash = ""
    mesh_cleanup_raw_gate_failure_codes: tuple[str, ...] = ()
    mesh_cleanup_clean_indexed_mesh_hash = ""
    mesh_cleanup_clean_gate_hard_pass = False
    revalidated = _revalidated_mesh(vertices, triangles)
    if revalidated is None:
        repair = repair_profiled_indexed_mesh(
            vertices,
            triangles,
            effective_height_m=effective_height_m,
        )
        if repair is not None:
            vertices = repair.vertices
            triangles = repair.triangles
            revalidated = _revalidated_mesh(vertices, triangles)
            surfaces = _surfaces_from_indexed_mesh(
                vertices,
                triangles,
                output_origin=output_origin,
                volume_role=canonical_capacity_plates[0].role,
            )
            mesh_cleanup_schema = MESH_NUMERIC_REPAIR_SCHEMA
            mesh_cleanup_collapse_threshold_m = (
                repair.collapse_threshold_m
            )
            mesh_cleanup_max_physical_displacement_m = (
                repair.max_physical_displacement_m
            )
            mesh_cleanup_raw_indexed_mesh_hash = (
                repair.raw_indexed_mesh_hash
            )
            mesh_cleanup_raw_gate_failure_codes = (
                repair.raw_gate_failure_codes
            )
            mesh_cleanup_clean_indexed_mesh_hash = (
                repair.clean_indexed_mesh_hash
            )
            mesh_cleanup_clean_gate_hard_pass = (
                repair.clean_gate_hard_pass
            )
    if revalidated is None:
        return _failed(
            "profiled_legal_clip_mesh_revalidation_failed",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    # Re-measure the emitted indexed payload. Inputs used to build the CSG
    # cannot certify the renderer-visible result. Kernel slicing avoids
    # rebuilding a closed contour from independently rounded line segments.
    section_numeric_epsilon_m = _section_numeric_epsilon_m(
        mesh_cleanup_max_physical_displacement_m
    )
    floor_center_schema = (
        FLOOR_CENTER_NUMERIC_EQUIVALENCE_REPAIR_SCHEMA
        if mesh_cleanup_max_physical_displacement_m > 0.0
        else FLOOR_CENTER_NUMERIC_EQUIVALENCE_SCHEMA
    )
    section_metrics: list[dict[str, float]] = []
    for floor_index, expected in enumerate(occupied_sections):
        measured = _indexed_mesh_section_polygon(
            vertices,
            triangles,
            (floor_index + 0.5) / floor_count,
        )
        metrics = _floor_center_numeric_equivalence(
            measured,
            expected,
            epsilon_m=section_numeric_epsilon_m,
        )
        if metrics is None:
            return _failed(
                "profiled_legal_clip_midplane_mismatch",
                capacity_gfa=capacity_gfa,
                source_surface_count=len(profiled),
            )
        section_metrics.append(metrics)

    max_section_area_delta_m2 = max(
        metric["area_delta_m2"] for metric in section_metrics
    )
    max_section_symdiff_m2 = max(
        metric["symdiff_m2"] for metric in section_metrics
    )
    max_section_hausdorff_m = max(
        metric["hausdorff_m"] for metric in section_metrics
    )
    max_section_area_bound_m2 = max(
        metric["area_bound_m2"] for metric in section_metrics
    )

    legal_sample_count = _legal_band_projection_sample_count(
        vertices,
        triangles,
        legal_sections,
    )
    if legal_sample_count is None:
        return _failed(
            "profiled_legal_clip_legal_revalidation_failed",
            capacity_gfa=capacity_gfa,
            source_surface_count=len(profiled),
        )

    exact_hash = _exact_surface_payload_hash(surfaces)
    authored_program_hash = _verified_authored_program_hash(source)
    sloped_evidence = profiled_sloped_mesh_evidence(
        surfaces,
        effective_height_m=effective_height_m,
    )
    if not authored_program_hash:
        sloped_evidence = profiled_sloped_mesh_evidence(
            (),
            effective_height_m=0.0,
        )
    authority_hash = floorwise_authority_binding_hash(
        **components,
        exact_surface_payload_hash=exact_hash,
        certification_mode=_MODE,
        visible_geometry_operation=_OPERATION,
        visible_step_fallback=False,
        authored_program_hash=authored_program_hash,
        effective_height_m=sloped_evidence["effective_height_m"],
        verified_profiled_sloped_surface_area=(
            sloped_evidence["sloped_surface_area"]
        ),
        verified_profiled_sloped_surface_ratio=(
            sloped_evidence["sloped_surface_ratio"]
        ),
        verified_profiled_sloped_surface_hash=(
            sloped_evidence["sloped_surface_hash"]
        ),
        section_numeric_epsilon_m=section_numeric_epsilon_m,
        mesh_numeric_repair_schema=mesh_cleanup_schema,
        mesh_cleanup_collapse_threshold_m=(
            mesh_cleanup_collapse_threshold_m
        ),
        mesh_cleanup_max_physical_displacement_m=(
            mesh_cleanup_max_physical_displacement_m
        ),
        mesh_cleanup_raw_indexed_mesh_hash=(
            mesh_cleanup_raw_indexed_mesh_hash
        ),
        mesh_cleanup_raw_gate_failure_codes=(
            mesh_cleanup_raw_gate_failure_codes
        ),
        mesh_cleanup_clean_indexed_mesh_hash=(
            mesh_cleanup_clean_indexed_mesh_hash
        ),
        mesh_cleanup_clean_gate_hard_pass=(
            mesh_cleanup_clean_gate_hard_pass
        ),
        floor_center_numeric_equivalence_schema=(
            floor_center_schema
        ),
        max_section_area_delta_m2=max_section_area_delta_m2,
        max_section_symdiff_m2=max_section_symdiff_m2,
        max_section_hausdorff_m=max_section_hausdorff_m,
        max_section_area_bound_m2=max_section_area_bound_m2,
    )
    return FloorwiseVisualProjection(
        surfaces=surfaces,
        certificate=FloorwiseVisualProjectionCertificate(
            status="certified",
            hard_pass=True,
            visual_hash=_stable_visual_hash(surfaces),
            source_surface_count=len(profiled),
            projected_surface_count=len(surfaces),
            legal_sample_count=legal_sample_count,
            capacity_gfa_m2=capacity_gfa,
            floor_count=floor_count,
            certification_mode=_MODE,
            visible_geometry_operation=_OPERATION,
            exact_surface_payload_hash=exact_hash,
            capacity_authority="floorwise_legal_volumes",
            visible_step_fallback=False,
            section_profile_hash=components["section_profile_hash"],
            capacity_volume_hash=components["capacity_volume_hash"],
            floor_capacity_plan_hash=components["floor_capacity_plan_hash"],
            matrix4_stack_hash=components["matrix4_stack_hash"],
            authored_program_hash=authored_program_hash,
            effective_height_m=sloped_evidence["effective_height_m"],
            verified_profiled_sloped_surface_area=(
                sloped_evidence["sloped_surface_area"]
            ),
            verified_profiled_sloped_surface_ratio=(
                sloped_evidence["sloped_surface_ratio"]
            ),
            verified_profiled_sloped_surface_hash=(
                sloped_evidence["sloped_surface_hash"]
            ),
            section_numeric_epsilon_m=section_numeric_epsilon_m,
            mesh_numeric_repair_schema=mesh_cleanup_schema,
            mesh_cleanup_collapse_threshold_m=(
                mesh_cleanup_collapse_threshold_m
            ),
            mesh_cleanup_max_physical_displacement_m=(
                mesh_cleanup_max_physical_displacement_m
            ),
            mesh_cleanup_raw_indexed_mesh_hash=(
                mesh_cleanup_raw_indexed_mesh_hash
            ),
            mesh_cleanup_raw_gate_failure_codes=(
                mesh_cleanup_raw_gate_failure_codes
            ),
            mesh_cleanup_clean_indexed_mesh_hash=(
                mesh_cleanup_clean_indexed_mesh_hash
            ),
            mesh_cleanup_clean_gate_hard_pass=(
                mesh_cleanup_clean_gate_hard_pass
            ),
            floor_center_numeric_equivalence_schema=(
                floor_center_schema
            ),
            max_section_area_delta_m2=max_section_area_delta_m2,
            max_section_symdiff_m2=max_section_symdiff_m2,
            max_section_hausdorff_m=max_section_hausdorff_m,
            max_section_area_bound_m2=max_section_area_bound_m2,
            authority_binding_hash=authority_hash,
        ),
    )


def _complete_profiled_export(
    source: SourceMass,
    surfaces: Sequence[SourceSurface],
) -> bool:
    bridge = source.metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    try:
        raw = int(bridge.get("raw_mesh_triangle_count") or 0)
        exported = int(bridge.get("exported_surface_count") or 0)
    except (TypeError, ValueError):
        return False
    return bool(
        raw
        and exported
        and raw == exported == len(surfaces) == len(source.surfaces)
    )


def _verified_authored_program_hash(source: SourceMass) -> str:
    payload = source.metadata.get("geometry_program")
    bridge = source.metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    if not isinstance(payload, dict):
        return ""
    try:
        program = GeometryProgram.from_dict(payload)
    except (TypeError, ValueError):
        return ""
    program_hash = program.program_hash()
    return (
        program_hash
        if (
            not program.validate()
            and str(bridge.get("program_hash") or "") == program_hash
        )
        else ""
    )


def _effective_height_m(source: SourceMass) -> float:
    contexts = (
        source.metadata.get("program_dimensional_context"),
        source.metadata.get("candidate_floor_context"),
        source.metadata.get("legal_generation_context_evidence"),
    )
    for context in contexts:
        if not isinstance(context, dict):
            continue
        for field in (
            "effective_height_m",
            "height_m",
            "requested_program_height_m",
        ):
            try:
                value = float(context.get(field) or 0.0)
            except (TypeError, ValueError):
                continue
            if isfinite(value) and value > 0.0:
                return value
    return 0.0


def _single_ring(value: Any) -> bool:
    return bool(
        isinstance(value, Polygon)
        and not value.is_empty
        and value.is_valid
        and isfinite(float(value.area))
        and float(value.area) > _EPSILON
        and len(value.interiors) == 0
    )


def _plan_only_matrix(matrix: Matrix4) -> bool:
    return (
        abs(matrix[0][2]) <= _EPSILON
        and abs(matrix[1][2]) <= _EPSILON
        and abs(matrix[2][0]) <= _EPSILON
        and abs(matrix[2][1]) <= _EPSILON
        and abs(matrix[2][2] - 1.0) <= _EPSILON
        and abs(matrix[2][3]) <= _EPSILON
    )


def _source_world_matrix_field_manifold(
    source: SourceMass,
    surfaces: Sequence[SourceSurface],
    matrices: tuple[Matrix4, ...],
) -> m3d.Manifold:
    origin = source.footprint.centroid
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
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    indices: dict[tuple[float, float, float], int] = {}
    for surface in surfaces:
        world_triangle = tuple(
            (
                float(x) + float(origin.x),
                float(y) + float(origin.y),
                float(z),
            )
            for x, y, z in surface.vertices_m
        )
        if (
            not all(
                all(isfinite(value) for value in vertex)
                for vertex in world_triangle
            )
            or any(
                vertex[2] < 0.0 or vertex[2] > 1.0
                for vertex in world_triangle
            )
        ):
            raise ValueError("invalid authored mesh vertex")
        for piece in _split_triangle_at_z_breakpoints(
            world_triangle,
            breakpoints=tessellation_levels,
        ):
            triangle = []
            for point in piece:
                vertex = _transform_with_matrix_field(
                    matrices,
                    point,
                    breakpoints=breakpoints,
                )
                triangle.append(indices.setdefault(vertex, len(indices)))
                if triangle[-1] == len(vertices):
                    vertices.append(vertex)
            triangles.append(tuple(triangle))
    mesh = m3d.Mesh(
        np.asarray(vertices, dtype=np.float64),
        np.asarray(triangles, dtype=np.uint32),
    )
    mesh.merge()
    return m3d.Manifold(mesh)


def _legal_prism(
    polygon: Polygon,
    *,
    lower_z: float,
    upper_z: float,
) -> m3d.Manifold:
    normalized = orient(polygon, sign=1.0)
    coordinates = [
        (float(x), float(y))
        for x, y in tuple(normalized.exterior.coords)[:-1]
    ]
    start = min(range(len(coordinates)), key=coordinates.__getitem__)
    exterior = coordinates[start:] + coordinates[:start]
    return (
        m3d.CrossSection([exterior])
        .extrude(float(upper_z) - float(lower_z))
        .translate((0.0, 0.0, float(lower_z)))
    )


def _legal_band_projection_sample_count(
    vertices: Sequence[tuple[float, float, float]],
    triangles: Sequence[tuple[int, int, int]],
    legal_sections: Sequence[Polygon],
) -> int | None:
    """Prove whole emitted faces against half-open legal floor bands."""

    floor_count = len(legal_sections)
    boundaries = tuple(
        index / floor_count
        for index in range(1, floor_count)
    )
    buffered = tuple(section.buffer(1e-7) for section in legal_sections)
    checked = 0
    for triangle in triangles:
        world_triangle = tuple(vertices[index] for index in triangle)
        for piece in _split_triangle_at_z_breakpoints(
            world_triangle,
            breakpoints=boundaries,
        ):
            z_values = tuple(float(point[2]) for point in piece)
            minimum_z = min(z_values)
            maximum_z = max(z_values)
            if minimum_z < -_EPSILON or maximum_z > 1.0 + _EPSILON:
                return None
            if maximum_z - minimum_z <= _EPSILON:
                scaled = minimum_z * floor_count
                boundary = round(scaled)
                if (
                    abs(scaled - boundary) <= _EPSILON
                    and 0 < boundary < floor_count
                ):
                    # A horizontal terrace exposed at a setback boundary is
                    # the top cap of the lower half-open legal band.
                    floor_index = boundary - 1
                else:
                    floor_index = min(
                        floor_count - 1,
                        max(0, int(scaled)),
                    )
            else:
                center_z = sum(z_values) / len(z_values)
                floor_index = min(
                    floor_count - 1,
                    max(0, int(center_z * floor_count)),
                )
            projection = MultiPoint([
                (float(x), float(y))
                for x, y, _z in piece
            ]).convex_hull
            if (
                projection.is_empty
                or not buffered[floor_index].covers(projection)
            ):
                return None
            checked += 1
    return checked if checked else None


def _surfaces_from_indexed_mesh(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    *,
    output_origin: tuple[float, float],
    volume_role: str,
) -> tuple[SourceSurface, ...]:
    local_vertices = tuple(
        (
            vertex[0] - float(output_origin[0]),
            vertex[1] - float(output_origin[1]),
            vertex[2],
        )
        for vertex in vertices
    )
    return tuple(
        SourceSurface(
            role=f"floorwise_profiled_legal_clip_{index:04d}",
            volume_role=volume_role,
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(local_vertices[vertex] for vertex in triangle),
        )
        for index, triangle in enumerate(triangles)
    )


def _surfaces_from_manifold(
    solid: m3d.Manifold,
    *,
    output_origin: tuple[float, float],
    volume_role: str,
) -> tuple[
    tuple[SourceSurface, ...],
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, int, int], ...],
]:
    mesh = solid.to_mesh64()
    world_vertices = tuple(
        tuple(float(value) for value in row[:3])
        for row in mesh.vert_properties
    )
    raw_triangles = tuple(
        tuple(int(value) for value in row)
        for row in mesh.tri_verts
    )
    triangles = tuple(sorted(
        (_rotate_triangle(triangle) for triangle in raw_triangles),
        key=lambda triangle: tuple(
            world_vertices[index]
            for index in triangle
        ),
    ))
    local_vertices = tuple(
        (
            vertex[0] - float(output_origin[0]),
            vertex[1] - float(output_origin[1]),
            vertex[2],
        )
        for vertex in world_vertices
    )
    surfaces = tuple(
        SourceSurface(
            role=f"floorwise_profiled_legal_clip_{index:04d}",
            volume_role=volume_role,
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(local_vertices[vertex] for vertex in triangle),
            operator="intersection",
            semantic_patch_id="floorwise_legal:profiled_mesh_clip",
        )
        for index, triangle in enumerate(triangles, start=1)
    )
    return surfaces, world_vertices, triangles


def _rotate_triangle(
    triangle: tuple[int, int, int],
) -> tuple[int, int, int]:
    rotations = (
        triangle,
        (triangle[1], triangle[2], triangle[0]),
        (triangle[2], triangle[0], triangle[1]),
    )
    return min(rotations)


def _failed(
    reason: str,
    *,
    capacity_gfa: float,
    source_surface_count: int,
) -> FloorwiseVisualProjection:
    return FloorwiseVisualProjection(
        surfaces=(),
        certificate=FloorwiseVisualProjectionCertificate(
            status="failed",
            hard_pass=False,
            failure_reasons=(reason,),
            source_surface_count=source_surface_count,
            capacity_gfa_m2=capacity_gfa,
            certification_mode=_MODE,
            visible_geometry_operation=_OPERATION,
            visible_step_fallback=False,
        ),
    )


__all__ = ["clip_profiled_mesh_to_floorwise_legal_solids"]
