"""Project recursive solid programs into the real parcel/program SourceMass lane.

The manifold solid remains the visual authority.  A small set of measured
horizontal sections becomes the conservative 2.5D proxy used by existing
program, FAR, sunlight and parking hard gates.  No parcel coordinate or
completed building is stored in a geometry program.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import replace
from math import atan2, cos, degrees, hypot, isfinite, pi, sin
from typing import Any

from shapely import make_valid, set_precision
from shapely.affinity import affine_transform, translate
from shapely.errors import GEOSException
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import nearest_points, polygonize, unary_union

from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.source_geometry.coherence import evaluate_source_volume_coherence
from design.maas.source_geometry.polygon_quality import repair_source_polygon

from .ast import GeometryNode, GeometryProgram
from .affine_matrix import (
    compose_matrix4,
    matrix4_to_lists,
    rotation_matrix4,
    scale_matrix4,
    translation_matrix4,
)
from .base_seeds import BASE_SEED_SPECS
from .compiler import CompilationResult, compile_geometry_program
from .gate import GeometryGatePolicy, compilation_gate


_COMPILATION_CACHE: "OrderedDict[str, CompilationResult]" = OrderedDict()
_COMPILATION_CACHE_LIMIT = 512


def _allocate_profiled_floor_targets(
    *,
    planned_floor_areas_m2: tuple[float, ...],
    legal_floor_caps_m2: tuple[float, ...],
    authored_profile_ratios: tuple[float, ...],
) -> tuple[float, ...]:
    """Distribute one GFA budget without erasing the authored section profile.

    The law/capacity agent owns the total requested floor area. Geometry owns
    how that area is distributed through the authored vertical profile.
    Independent per-floor replacement by the planning vector made every AST
    converge to the same normalized legal step stack.
    """

    count = min(
        len(planned_floor_areas_m2),
        len(legal_floor_caps_m2),
        len(authored_profile_ratios),
    )
    if count <= 0:
        return ()
    planned = tuple(
        max(0.0, float(value))
        for value in planned_floor_areas_m2[:count]
    )
    caps = tuple(
        max(0.0, float(value))
        for value in legal_floor_caps_m2[:count]
    )
    desired_total = min(sum(planned), sum(caps))
    if desired_total <= 1e-9:
        return (0.0,) * count

    weights = [
        max(1e-6, planned[index])
        * max(0.05, float(authored_profile_ratios[index]))
        for index in range(count)
    ]
    allocated = [0.0] * count
    active = {
        index
        for index, cap in enumerate(caps)
        if cap > 1e-9
    }
    remaining = desired_total
    while active and remaining > 1e-7:
        weight_total = sum(weights[index] for index in active)
        if weight_total <= 1e-12:
            weight_total = float(len(active))
            shares = {index: remaining / weight_total for index in active}
        else:
            shares = {
                index: remaining * weights[index] / weight_total
                for index in active
            }
        saturated: set[int] = set()
        progress = 0.0
        for index in active:
            room = max(0.0, caps[index] - allocated[index])
            addition = min(room, shares[index])
            allocated[index] += addition
            progress += addition
            if room - addition <= 1e-7:
                saturated.add(index)
        remaining = max(0.0, desired_total - sum(allocated))
        active.difference_update(saturated)
        if progress <= 1e-9:
            break
    return tuple(allocated)


def _requested_plan_axis_scales(
    source: Any,
    host: Polygon,
    *,
    target_area: float,
) -> tuple[float, float] | None:
    """Return the least-anisotropic affine scales that can reach one target."""

    source_parts = _polygon_parts(source)
    if not source_parts:
        return None
    source_union = unary_union(source_parts)
    if source_union.is_empty or float(source_union.area) <= 1e-9:
        return None
    source_frame = source_union.convex_hull
    if not isinstance(source_frame, Polygon):
        return None
    _source_angle, source_width, source_depth = _principal_frame(source_frame)
    _host_angle, host_width, host_depth = _principal_frame(host)
    if min(source_width, source_depth, host_width, host_depth) <= 1e-9:
        return None
    requested_product = max(0.2, float(target_area)) / max(
        float(source_union.area),
        1e-9,
    )
    maximum_x = host_width / source_width * 0.995
    maximum_y = host_depth / source_depth * 0.995
    requested_product = min(requested_product, maximum_x * maximum_y)
    uniform = requested_product ** 0.5
    if uniform <= maximum_x and uniform <= maximum_y:
        return uniform, uniform
    x_scale = min(uniform, maximum_x)
    y_scale = requested_product / max(x_scale, 1e-9)
    if y_scale > maximum_y:
        y_scale = maximum_y
        x_scale = requested_product / max(y_scale, 1e-9)
    if min(x_scale, y_scale) <= 1e-9:
        return None
    return x_scale, y_scale


def _exact_authored_mesh_section(
    source: SourceMass,
    *,
    height_fraction: float,
) -> Any | None:
    """Measure one horizontal section from the complete authored mesh.

    ``SourceVolume`` bands are conservative legal proxies. They intentionally
    union several mesh slices and therefore cannot be the geometry source for
    a later floor plate: doing so erases shear, twist, cuts and curved plans.
    """

    bridge = source.metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    raw_triangle_count = int(bridge.get("raw_mesh_triangle_count") or 0)
    exported_surface_count = int(bridge.get("exported_surface_count") or 0)
    if (
        raw_triangle_count > 0
        and exported_surface_count > 0
        and exported_surface_count < raw_triangle_count
    ):
        return None
    mesh_surfaces = tuple(
        surface
        for surface in source.surfaces
        if (
            surface.surface_type == "profiled_recursive_solid_mesh"
            and len(surface.vertices_m) == 3
        )
    )
    if not mesh_surfaces:
        return None
    origin = source.footprint.centroid
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for surface in mesh_surfaces:
        offset = len(vertices)
        vertices.extend(
            (
                float(x) + float(origin.x),
                float(y) + float(origin.y),
                float(z),
            )
            for x, y, z in surface.vertices_m
        )
        triangles.append((offset, offset + 1, offset + 2))
    section = _mesh_section_polygon(
        tuple(vertices),
        tuple(triangles),
        max(1e-5, min(1.0 - 1e-5, float(height_fraction))),
    )
    if section is None or section.is_empty or float(section.area) <= 1e-9:
        return None
    return section


def materialize_floorwise_legal_source(
    source: SourceMass,
    *,
    legal_sections: tuple[Polygon, ...],
    target_plan_coverage: float,
    floor_capacity_plan_hash: str = "",
    target_floor_areas_m2: tuple[float, ...] = (),
) -> SourceMass | None:
    """Refit one authored AST body into one affine legal plate per floor.

    The input mesh/AST remains the design authority.  Each requested floor
    samples that body's existing vertical profile, then receives a derived
    homogeneous transform into the corresponding live legal section.  No
    parcel coordinate or completed form is stored in the reusable program.
    """

    if not source.volumes or not legal_sections:
        return None
    coverage = max(0.05, min(0.95, float(target_plan_coverage or 0.0)))
    floor_count = len(legal_sections)
    primary_role = max(
        source.volumes,
        key=lambda volume: (
            float(volume.footprint.area)
            * max(0.0, float(volume.top_fraction) - float(volume.bottom_fraction))
        ),
    ).role
    active_by_floor: list[Any] = []
    exact_mesh_section_count = 0
    for floor_index in range(floor_count):
        fraction = (floor_index + 0.5) / floor_count
        exact_section = _exact_authored_mesh_section(
            source,
            height_fraction=fraction,
        )
        if exact_section is not None:
            active_by_floor.append(exact_section)
            exact_mesh_section_count += 1
            continue
        active = [
            volume.footprint
            for volume in source.volumes
            if float(volume.bottom_fraction) <= fraction < float(volume.top_fraction)
        ]
        active_by_floor.append(unary_union(active) if active else None)
    ground_source = next(
        (
            geometry
            for geometry in active_by_floor
            if geometry is not None and not geometry.is_empty
        ),
        None,
    )
    if ground_source is None or float(ground_source.area) <= 1e-9:
        return None
    ground_source_area = float(ground_source.area)
    ground_legal = repair_source_polygon(legal_sections[0], minimum_area=1.0)
    if ground_legal is None or ground_legal.is_empty:
        return None
    source_reference_angle, _source_width, _source_depth = _principal_frame(
        ground_source.convex_hull
    )
    target_reference_angle, _target_width, _target_depth = _principal_frame(
        ground_legal
    )
    pose_rotation_degrees = target_reference_angle - source_reference_angle
    source_reference_center = ground_source.centroid
    target_reference_center = ground_legal.centroid

    prepared_floors: list[tuple[Any, Polygon, float, float]] = []
    for floor_index, (raw_source, raw_legal) in enumerate(zip(
        active_by_floor,
        legal_sections,
    )):
        legal = repair_source_polygon(raw_legal, minimum_area=1.0)
        if (
            raw_source is None
            or raw_source.is_empty
            or legal is None
            or legal.is_empty
        ):
            return None
        source_parts = _polygon_parts(raw_source)
        source_plan = unary_union(source_parts)
        if source_plan.is_empty or float(source_plan.area) <= 1e-9:
            return None
        vertical_profile_ratio = max(
            0.05,
            min(1.25, float(source_plan.area) / ground_source_area),
        )
        planned_floor_area = (
            max(0.0, float(target_floor_areas_m2[floor_index]))
            if floor_index < len(target_floor_areas_m2)
            else 0.0
        )
        prepared_floors.append((
            source_plan,
            legal,
            vertical_profile_ratio,
            (
                planned_floor_area
                if planned_floor_area > 0.0
                else float(legal.area) * coverage
            ),
        ))

    allocated_floor_targets = _allocate_profiled_floor_targets(
        planned_floor_areas_m2=tuple(
            planned_area
            for _source_plan, _legal, _profile_ratio, planned_area
            in prepared_floors
        ),
        legal_floor_caps_m2=tuple(
            float(legal.area) * 0.95
            for _source_plan, legal, _profile_ratio, _planned_area
            in prepared_floors
        ),
        authored_profile_ratios=tuple(
            profile_ratio
            for _source_plan, _legal, profile_ratio, _planned_area
            in prepared_floors
        ),
    )
    global_axis_scales = _requested_plan_axis_scales(
        ground_source,
        ground_legal,
        target_area=(
            allocated_floor_targets[0]
            if allocated_floor_targets
            else float(ground_legal.area) * coverage
        ),
    )
    if global_axis_scales is None:
        return None
    global_x_scale, global_y_scale = global_axis_scales
    global_anisotropy_ratio = global_x_scale / max(global_y_scale, 1e-9)

    fitted_floor_results: list[
        tuple[Any, tuple[tuple[float, float, float, float], ...]] | None
    ] = []
    for floor_index, (
        source_plan,
        legal,
        _vertical_profile_ratio,
        _planned_floor_area,
    ) in enumerate(prepared_floors):
        target_area = allocated_floor_targets[floor_index]
        source_dx = (
            float(source_plan.centroid.x) - float(source_reference_center.x)
        )
        source_dy = (
            float(source_plan.centroid.y) - float(source_reference_center.y)
        )
        source_theta = source_reference_angle * pi / 180.0
        target_theta = target_reference_angle * pi / 180.0
        local_u = source_dx * cos(source_theta) + source_dy * sin(source_theta)
        local_v = -source_dx * sin(source_theta) + source_dy * cos(source_theta)
        fitted_offset_x = (
            local_u * global_x_scale * cos(target_theta)
            - local_v * global_y_scale * sin(target_theta)
        )
        fitted_offset_y = (
            local_u * global_x_scale * sin(target_theta)
            + local_v * global_y_scale * cos(target_theta)
        )
        fitted_floor_results.append(_matrix_fit_polygon_to_host(
            source_plan,
            legal,
            target_area=target_area,
            target_center=(
                float(target_reference_center.x) + fitted_offset_x,
                float(target_reference_center.y) + fitted_offset_y,
            ),
            target_angle_offset_degrees=pose_rotation_degrees,
            anisotropy_ratio=global_anisotropy_ratio,
        ))

    requested_total = sum(allocated_floor_targets)
    strict_total = sum(
        float(fitted[0].area)
        for fitted in fitted_floor_results
        if fitted is not None
    )
    pose_fit_mode = (
        "single_global_rotation_translation_with_floor_relative_pose_preserved"
    )
    pose_fallback_used = (
        any(fitted is None for fitted in fitted_floor_results)
        or strict_total < requested_total * 0.78
    )
    if pose_fallback_used:
        # A geometrically infeasible offset must not make every candidate miss
        # the law-derived capacity floor. Reflow each authored floor plan into
        # its own legal section, while keeping the authored per-floor area
        # profile allocated above. Shift-only twins may collapse here and are
        # then correctly removed by the visual duplicate gate; taper, void,
        # wing and plan topology remain geometry evidence.
        fitted_floor_results = []
        for floor_index, (
            source_plan,
            legal,
            _vertical_profile_ratio,
            _planned_floor_area,
        ) in enumerate(prepared_floors):
            target_area = allocated_floor_targets[floor_index]
            scales = _requested_plan_axis_scales(
                source_plan,
                legal,
                target_area=target_area,
            )
            if scales is None:
                return None
            x_scale, y_scale = scales
            source_angle, _source_width, _source_depth = _principal_frame(
                source_plan.convex_hull
            )
            legal_angle, _legal_width, _legal_depth = _principal_frame(legal)
            fitted_floor_results.append(_matrix_fit_polygon_to_host(
                source_plan,
                legal,
                target_area=target_area,
                target_center=(
                    float(legal.centroid.x),
                    float(legal.centroid.y),
                ),
                target_angle_offset_degrees=legal_angle - source_angle,
                anisotropy_ratio=x_scale / max(y_scale, 1e-9),
            ))
        pose_fit_mode = (
            "floorwise_legal_reflow_with_authored_vertical_profile_budget"
        )
    if any(fitted is None for fitted in fitted_floor_results):
        return None

    volumes: list[SourceVolume] = []
    floor_evidence: list[dict[str, Any]] = []
    floor_unions: list[Any] = []
    for floor_index, (
        source_plan,
        legal,
        vertical_profile_ratio,
        planned_floor_area,
    ) in enumerate(prepared_floors):
        target_area = (
            allocated_floor_targets[floor_index]
            if floor_index < len(allocated_floor_targets)
            else 0.0
        )
        fitted = fitted_floor_results[floor_index]
        if fitted is None:
            return None
        occupied, matrix = fitted
        occupied_parts = _polygon_parts(occupied)
        if not occupied_parts:
            return None
        bottom = floor_index / floor_count
        top = (floor_index + 1) / floor_count
        for part_index, part in enumerate(occupied_parts, start=1):
            volumes.append(SourceVolume(
                # Height bands of one authored AST are one typed component.
                # A unique role per floor makes program hierarchy misread one
                # building as five unrelated siblings.
                role=primary_role,
                footprint=part,
                bottom_fraction=bottom,
                top_fraction=top,
                verb="floorwise_legal_matrix4",
            ))
        floor_union = unary_union(occupied_parts)
        floor_unions.append(floor_union)
        floor_evidence.append({
            "floor": floor_index + 1,
            "matrix4": matrix4_to_lists(matrix),
            "source_plan_area_m2": round(float(source_plan.area), 4),
            "legal_plan_area_m2": round(float(legal.area), 4),
            "planned_floor_area_m2": round(planned_floor_area, 4),
            "target_plan_area_m2": round(target_area, 4),
            "achieved_plan_area_m2": round(float(floor_union.area), 4),
            "target_plan_coverage": round(coverage, 4),
            "vertical_profile_ratio": round(vertical_profile_ratio, 4),
            "floor_capacity_plan_hash": str(floor_capacity_plan_hash or ""),
            "legal_csg_clip_area_m2": round(
                max(0.0, float(floor_union.difference(legal).area)),
                6,
            ),
        })

    ground = repair_source_polygon(floor_unions[0], minimum_area=1.0)
    upper = repair_source_polygon(floor_unions[-1], minimum_area=1.0)
    if ground is None or upper is None:
        return None
    # Law-derived floor plates remain the sole GFA authority.  A complete
    # authored triangle skin is carried separately through the same Matrix4
    # evidence so renderer/VLM diversity survives capacity materialization.
    from .floorwise_visual_projection import project_floorwise_visual_mesh

    visual_projection = project_floorwise_visual_mesh(
        source,
        legal_sections=legal_sections,
        floor_matrices=tuple(
            fitted[1]
            for fitted in fitted_floor_results
            if fitted is not None
        ),
        capacity_plates=tuple(volumes),
    )
    if not visual_projection.certificate.hard_pass:
        return None
    metadata = deepcopy(source.metadata)
    bridge = metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    metadata["floorwise_legal_matrix_stack"] = {
        "schema_version": "arr.maas.floorwise_legal_matrix_stack.v1",
        "status": "materialized",
        "floor_count": floor_count,
        "target_plan_coverage": round(coverage, 4),
        "matrix_convention": "row_major_column_vector",
        "pose_fit": pose_fit_mode,
        "pose_fallback_used": pose_fallback_used,
        "strict_pose_achieved_total_area_m2": round(strict_total, 4),
        "strict_pose_required_total_area_m2": round(
            requested_total * 0.78,
            4,
        ),
        "global_pose_rotation_degrees": round(pose_rotation_degrees, 6),
        "global_plan_axis_scales": [
            round(global_x_scale, 6),
            round(global_y_scale, 6),
        ],
        "global_plan_anisotropy_ratio": round(global_anisotropy_ratio, 6),
        "geometry_program_hash": str(bridge.get("program_hash") or ""),
        "geometry_hash": str(bridge.get("geometry_hash") or ""),
        "floor_capacity_plan_hash": str(floor_capacity_plan_hash or ""),
        "target_floor_areas_m2": [
            round(max(0.0, float(value)), 4)
            for value in target_floor_areas_m2[:floor_count]
        ],
        "floor_area_allocation": (
            "total_capacity_budget_weighted_by_authored_vertical_profile"
        ),
        "floor_section_source": (
            "exact_authored_manifold_mesh"
            if exact_mesh_section_count == floor_count
            else "conservative_source_volume_proxy"
        ),
        "exact_authored_mesh_section_count": exact_mesh_section_count,
        "allocated_floor_areas_m2": [
            round(max(0.0, float(value)), 4)
            for value in allocated_floor_targets
        ],
        "source_authority": "same_authored_geometry_program_ast",
        "primary_component_role": primary_role,
        "legal_section_source": "live_pnu_generation_context",
        "csg_role": "legal_containment_only",
        "completed_building_template": False,
        "parcel_coordinates_stored_in_geometry_program": False,
        "floors": floor_evidence,
    }
    metadata["continuous_surface_evidence"] = {
        "schema_version": "arr.maas.continuous_surface_evidence.v1",
        "status": "superseded_by_floorwise_legal_matrix_stack",
        "hard_pass": False,
        "source_geometry_program_preserved": True,
    }
    metadata["floorwise_visual_projection"] = (
        visual_projection.certificate.to_dict()
    )
    # Materialization changes the occupied plan on every level. Never retain
    # coherence evidence measured on the pre-fit BOOK body; downstream
    # program gates must judge the exact legal floor bands they will render.
    metadata["coherence_evidence"] = evaluate_source_volume_coherence(
        tuple(volumes)
    )
    return replace(
        source,
        footprint=ground,
        upper_footprint=upper,
        volumes=tuple(volumes),
        surfaces=visual_projection.surfaces,
        metadata=metadata,
    )


def floorwise_source_to_geometry_program(
    source: SourceMass,
    *,
    height_m: float,
    name: str | None = None,
) -> GeometryProgram:
    """Serialize the final legal floor plates as the exact replay program.

    The authored LLM/BOOK AST remains in provenance.  This projection program
    is the downstream executable handoff: single execution, renderer, VLM and
    elevation all compile the same law-derived affine-fitted plates that passed FAR,
    parking and shared-floor gates.
    """

    total_height = float(height_m)
    if total_height <= 0.0:
        raise ValueError("height_m must be positive")
    if not source.volumes:
        raise ValueError("floorwise source must contain at least one volume")
    stack = source.metadata.get("floorwise_legal_matrix_stack")
    if not isinstance(stack, dict) or stack.get("status") != "materialized":
        raise ValueError("source has no materialized floorwise legal matrix stack")

    origin = source.footprint.centroid
    nodes: list[GeometryNode] = []
    solid_ids: list[str] = []
    bands: set[tuple[float, float]] = set()
    ordered_volumes = sorted(
        source.volumes,
        key=lambda volume: (
            float(volume.bottom_fraction),
            float(volume.top_fraction),
            volume.role,
            round(float(volume.footprint.centroid.x), 8),
            round(float(volume.footprint.centroid.y), 8),
        ),
    )
    for index, volume in enumerate(ordered_volumes, start=1):
        bottom = float(volume.bottom_fraction)
        top = float(volume.top_fraction)
        band_height = (top - bottom) * total_height
        if band_height <= 1e-8:
            raise ValueError("floorwise volume has a non-positive height band")
        footprint = repair_source_polygon(volume.footprint, minimum_area=0.01)
        if footprint is None:
            raise ValueError("floorwise volume has no replayable footprint")
        # Manifold CrossSection uses winding to distinguish material from
        # void. Live PNU/GEOS operations may return either exterior winding;
        # normalize the transport contract before serializing the AST.
        footprint = orient(footprint, sign=1.0)
        bands.add((round(bottom, 8), round(top, 8)))
        primitive_id = f"floor_plate_{index:02d}"
        translated_id = f"floor_position_{index:02d}"
        nodes.append(GeometryNode(
            id=primitive_id,
            kind="primitive",
            operator="extruded_polygon",
            parameters={
                "points": _local_ring_points(
                    footprint.exterior.coords,
                    xoff=origin.x,
                    yoff=origin.y,
                ),
                "holes": [
                    _local_ring_points(
                        interior.coords,
                        xoff=origin.x,
                        yoff=origin.y,
                    )
                    for interior in footprint.interiors
                ],
                "height": round(band_height, 8),
            },
            semantic_role=volume.role or "floor_plate",
            provenance={
                "source": "floorwise_legal_matrix_stack",
                "volume_index": index,
                "verb": volume.verb,
                "bottom_fraction": round(bottom, 8),
                "top_fraction": round(top, 8),
            },
        ))
        nodes.append(GeometryNode(
            id=translated_id,
            kind="transform",
            operator="translate",
            inputs=(primitive_id,),
            parameters={"vector": [0.0, 0.0, round(bottom * total_height, 8)]},
            semantic_role=volume.role or "floor_plate",
            provenance={
                "source": "floorwise_legal_matrix_stack",
                "matrix_convention": stack.get("matrix_convention"),
            },
        ))
        solid_ids.append(translated_id)

    if len(solid_ids) == 1:
        root_id = solid_ids[0]
    else:
        root_id = "final_floorwise_union"
        nodes.append(GeometryNode(
            id=root_id,
            kind="boolean",
            operator="union",
            inputs=tuple(solid_ids),
            semantic_role="final_legal_mass",
            provenance={
                "source": "floorwise_legal_matrix_stack",
                "operation": "recompose_exact_floor_bands",
            },
        ))

    bridge = source.metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    authored_program = source.metadata.get("geometry_program")
    authored_program = authored_program if isinstance(authored_program, dict) else {}
    capacity_alternative = source.metadata.get("capacity_alternative_projection")
    capacity_alternative = (
        capacity_alternative if isinstance(capacity_alternative, dict) else {}
    )
    return GeometryProgram(
        nodes=tuple(nodes),
        root_id=root_id,
        name=name or f"{source.name}_floorwise_legal_projection",
        metadata={
            "family": "materialized_floorwise_legal_projection",
            "language_layer": "downstream_executable_projection",
            "floorwise_projection": {
                "schema_version": "arr.maas.floorwise_geometry_program.v1",
                "status": "executable",
                "floor_count": len(bands),
                "volume_count": len(ordered_volumes),
                "height_m": round(total_height, 6),
                "local_origin_utm": [
                    round(float(origin.x), 6),
                    round(float(origin.y), 6),
                ],
                "upstream_program_hash": str(
                    stack.get("geometry_program_hash")
                    or bridge.get("program_hash")
                    or ""
                ),
                "upstream_geometry_hash": str(
                    stack.get("geometry_hash")
                    or bridge.get("geometry_hash")
                    or ""
                ),
                "floor_capacity_plan_hash": str(
                    stack.get("floor_capacity_plan_hash") or ""
                ),
                "target_floor_areas_m2": [
                    round(max(0.0, float(value)), 4)
                    for value in (stack.get("target_floor_areas_m2") or ())
                ],
                "requested_capacity_alternative_id": str(
                    capacity_alternative.get("requested_capacity_alternative_id")
                    or capacity_alternative.get("alternative_id")
                    or ""
                ),
                "requested_target_utilization": float(
                    capacity_alternative.get("requested_target_utilization")
                    or capacity_alternative.get("target_utilization")
                    or 0.0
                ),
                "selectable_capacity_alternative_id": str(
                    capacity_alternative.get("selectable_capacity_alternative_id")
                    or ""
                ),
                "selectable_capacity_target_utilization": float(
                    capacity_alternative.get(
                        "selectable_capacity_target_utilization"
                    )
                    or 0.0
                ),
                "authored_program_name": str(authored_program.get("name") or ""),
                "matrix_convention": str(
                    stack.get("matrix_convention") or "row_major_column_vector"
                ),
                "source_authority": "final_legal_floorwise_source_mass",
                "completed_building_template": False,
                "parcel_coordinates_are_execution_only": True,
            },
        },
    )


def _local_ring_points(
    coordinates: Any,
    *,
    xoff: float,
    yoff: float,
) -> list[list[float]]:
    values = list(coordinates)
    if len(values) >= 2 and values[0][:2] == values[-1][:2]:
        values = values[:-1]
    return [
        [
            # One-micrometre transport precision is far below architectural
            # tolerances while avoiding sub-1e-10 m² triangulation slivers in
            # the independent single-execution geometry gate.
            round(float(point[0]) - float(xoff), 6),
            round(float(point[1]) - float(yoff), 6),
        ]
        for point in values
    ]


def _matrix_fit_polygon_to_host(
    source: Any,
    host: Polygon,
    *,
    target_area: float,
    target_center: tuple[float, float] | None = None,
    target_angle_offset_degrees: float = 0.0,
    anisotropy_ratio: float = 1.0,
) -> tuple[Any, tuple[tuple[float, float, float, float], ...]] | None:
    """Return the largest requested affine fit that stays inside ``host``."""

    source_parts = _polygon_parts(source)
    if not source_parts:
        return None
    source_union = unary_union(source_parts)
    if source_union.is_empty or float(source_union.area) <= 1e-9:
        return None
    source_frame_polygon = source_union.convex_hull
    if not isinstance(source_frame_polygon, Polygon):
        return None
    source_angle, source_width, source_depth = _principal_frame(source_frame_polygon)
    _host_angle, target_width, target_depth = _principal_frame(host)
    if min(source_width, source_depth, target_width, target_depth) <= 1e-9:
        return None
    source_center = source_union.centroid
    # The recursive source is already in the live site's coordinate frame.
    # Keep that authored centroid and angle through every floor. Re-centering
    # and independently aligning each plate to the legal host erased shift,
    # shear, twist and asymmetric setback relations before selection.
    resolved_target_center = (
        Point(float(target_center[0]), float(target_center[1]))
        if target_center is not None
        else source_center
    )
    target_angle = source_angle + float(target_angle_offset_degrees)
    requested_area_scale_product = (
        max(0.2, float(target_area)) / max(float(source_union.area), 1e-9)
    )
    maximum_x_scale = target_width / source_width * 0.995
    maximum_y_scale = target_depth / source_depth * 0.995
    available_area_scale_product = maximum_x_scale * maximum_y_scale
    requested_area_scale_product = min(
        requested_area_scale_product,
        available_area_scale_product,
    )
    if requested_area_scale_product <= 1e-9:
        return None
    ratio = max(0.25, min(4.0, float(anisotropy_ratio or 1.0)))
    requested_x_scale = (requested_area_scale_product * ratio) ** 0.5
    requested_y_scale = (requested_area_scale_product / ratio) ** 0.5
    bounded_uniform_factor = min(
        1.0,
        maximum_x_scale / max(requested_x_scale, 1e-9),
        maximum_y_scale / max(requested_y_scale, 1e-9),
    )
    requested_x_scale *= bounded_uniform_factor
    requested_y_scale *= bounded_uniform_factor
    if min(requested_x_scale, requested_y_scale) <= 1e-9:
        return None

    for shrink in (
        1.0, 0.99, 0.98, 0.97, 0.95, 0.93, 0.90, 0.86,
        0.82, 0.76, 0.68, 0.58, 0.48,
    ):
        x_scale = requested_x_scale * shrink
        y_scale = requested_y_scale * shrink
        matrix = compose_matrix4(
            translation_matrix4((-source_center.x, -source_center.y, 0.0)),
            rotation_matrix4((0.0, 0.0, -source_angle)),
            scale_matrix4((x_scale, y_scale, 1.0)),
            rotation_matrix4((0.0, 0.0, target_angle)),
            translation_matrix4((
                resolved_target_center.x,
                resolved_target_center.y,
                0.0,
            )),
        )
        fitted = affine_transform(
            source_union,
            [
                matrix[0][0],
                matrix[0][1],
                matrix[1][0],
                matrix[1][1],
                matrix[0][3],
                matrix[1][3],
            ],
        )
        if host.buffer(1e-7).covers(fitted):
            return fitted, matrix
    return None


def compile_geometry_program_to_source_mass(
    program: GeometryProgram,
    host: Polygon,
    *,
    upper_host: Polygon | None = None,
    upper_fit_strength: float = 0.0,
    target_plan_area: float | None = None,
    minimum_plan_area: float | None = None,
    name: str | None = None,
    volume_role: str = "recursive_solid_primary",
    max_volume_bands: int = 3,
    max_raw_surfaces: int = 2048,
    gate_policy: GeometryGatePolicy | None = None,
) -> SourceMass | None:
    """Fit one compiled solid into a normalized host and preserve its mesh.

    The fit is derived from the host's principal frame.  Legal clipping is not
    performed here; callers should supply the legal generation host and send
    the returned source through the unchanged downstream hard gates.
    """
    host = repair_source_polygon(host, minimum_area=1.0)
    if host is None:
        return None
    compilation = _compile_geometry_program_cached(program)
    # Compiler probes may study a bounded multi-solid relation, but an object
    # promoted into the program/legal/VLM lane must already be one connected
    # architectural body.  This prevents tiny detached pieces from surviving
    # long enough to be mistaken for a creative finished mass.
    source_gate_policy = gate_policy or GeometryGatePolicy(maximum_components=1)
    if compilation.status != "compiled" or compilation_gate(compilation, source_gate_policy):
        return None
    base_seed_plan_fraction = _base_seed_plan_occupancy_fraction(program)
    effective_target_plan_area = target_plan_area
    if base_seed_plan_fraction is not None and target_plan_area is None:
        base_seed_area_cap = float(host.area) * base_seed_plan_fraction
        effective_target_plan_area = base_seed_area_cap
    transformed = _fit_vertices_to_host(
        compilation,
        host,
        target_plan_area=effective_target_plan_area,
        minimum_plan_area=minimum_plan_area,
    )
    if transformed is None:
        return None
    world_vertices, _host_local_vertices = transformed
    legal_fit_mode = "principal_frame_bounded"
    fit_strength = max(0.0, min(1.0, float(upper_fit_strength)))
    if upper_host is not None and fit_strength > 1e-6:
        repaired_upper_host = repair_source_polygon(upper_host, minimum_area=1.0)
        upper_transformed = (
            _fit_vertices_to_host(
                compilation,
                repaired_upper_host,
                target_plan_area=effective_target_plan_area,
                minimum_plan_area=minimum_plan_area,
            )
            if repaired_upper_host is not None
            else None
        )
        if upper_transformed is not None:
            upper_vertices, _upper_local = upper_transformed
            world_vertices = tuple(
                (
                    lower[0] + (upper[0] - lower[0]) * lower[2] * fit_strength,
                    lower[1] + (upper[1] - lower[1]) * lower[2] * fit_strength,
                    lower[2],
                )
                for lower, upper in zip(world_vertices, upper_vertices)
            )
            legal_fit_mode = "height_interpolated_lower_upper_principal_frames"
    achieved_plan_area = _mesh_plan_projection_area(
        world_vertices,
        compilation.triangles,
    )
    minimum_plan_area_target = (
        max(0.2, float(minimum_plan_area))
        if minimum_plan_area is not None
        else None
    )
    minimum_plan_area_target_satisfied = (
        achieved_plan_area + 1e-7 >= minimum_plan_area_target
        if minimum_plan_area_target is not None
        else None
    )
    minimum_plan_area_shortfall_ratio = (
        max(0.0, (minimum_plan_area_target - achieved_plan_area) / minimum_plan_area_target)
        if minimum_plan_area_target is not None
        else None
    )
    band_count = max(1, min(3, int(max_volume_bands)))
    band_boundaries = tuple(index / band_count for index in range(band_count + 1))
    volume_records: list[SourceVolume] = []
    for band_index, (bottom, top) in enumerate(zip(band_boundaries, band_boundaries[1:])):
        # A single mid-height slice under-reports an undercut, setback or
        # lifted body.  The proxy is the conservative vertical occupancy of
        # each band: union of lower/middle/upper measured mesh sections.
        epsilon = max(1e-5, (top - bottom) * 0.03)
        sections = tuple(
            section
            for sample in (bottom + epsilon, (bottom + top) / 2.0, top - epsilon)
            for section in (
                _mesh_section_polygon(world_vertices, compilation.triangles, sample),
            )
            if section is not None
        )
        section = unary_union(sections) if sections else None
        if section is None:
            continue
        parts = _polygon_parts(section)
        for part_index, part in enumerate(parts[: max(1, 4 - len(volume_records))]):
            clipped = repair_source_polygon(part.intersection(host), minimum_area=max(0.2, host.area * 0.002))
            if clipped is None:
                continue
            volume_records.append(SourceVolume(
                # Height bands are legal proxies of one typed component, not
                # separate architectural fragments. Keep component identity
                # stable; bottom/top fractions still distinguish the bands.
                role=volume_role,
                footprint=clipped,
                bottom_fraction=bottom,
                top_fraction=top,
                verb="geometry_program",
            ))
    volumes = _merge_equal_band_footprints(tuple(volume_records))
    if not volumes:
        plan = repair_source_polygon(MultiPoint([(x, y) for x, y, _z in world_vertices]).convex_hull, minimum_area=0.2)
        if plan is None:
            return None
        clipped_plan = repair_source_polygon(plan.intersection(host), minimum_area=0.2)
        if clipped_plan is None:
            return None
        volumes = (SourceVolume(volume_role, clipped_plan, 0.0, 1.0, "geometry_program"),)
    if len(volumes) > max(1, min(5, int(max_volume_bands))):
        volumes = tuple(sorted(volumes, key=lambda value: value.footprint.area, reverse=True)[:max_volume_bands])
    footprint_union = unary_union([volume.footprint for volume in volumes if volume.bottom_fraction <= 1e-6])
    footprint = repair_source_polygon(footprint_union, minimum_area=0.2)
    if footprint is None:
        footprint = repair_source_polygon(unary_union([volume.footprint for volume in volumes]), minimum_area=0.2)
    if footprint is None:
        return None
    # SourceSurface vertices are local to SourceMass.footprint.centroid.  The
    # bridge host and the measured ground section can have different centres
    # (taper, shear, void and oblique cuts all cause this), so localise only
    # after the authoritative proxy footprint is known.
    surface_origin = footprint.centroid
    local_vertices = tuple(
        (x - surface_origin.x, y - surface_origin.y, z)
        for x, y, z in world_vertices
    )
    surfaces = _mesh_surfaces(
        local_vertices,
        compilation,
        volume_role=volume_role,
        max_raw_surfaces=max_raw_surfaces,
    )
    upper_candidates = [volume.footprint for volume in volumes if volume.top_fraction >= 1.0 - 1e-6]
    upper = repair_source_polygon(unary_union(upper_candidates), minimum_area=0.2) if upper_candidates else None
    operator_path = [node.operator for node in program.topological_nodes()]
    # Imported lazily to keep the compiler/adapter dependency one-way.
    from .vlm_adapter import build_geometry_graph_notes, build_geometry_graph_snapshot

    compilation_payload = compilation.to_dict(include_mesh=False)
    metadata = {
        "family": str(program.metadata.get("family") or program.name),
        "primary_language": str(program.metadata.get("family") or program.name),
        "formal_principle": str(program.metadata.get("family") or program.name),
        "dominant_gesture": str(program.metadata.get("family") or program.root_id),
        "reference_basis": str(program.metadata.get("reference_language") or "recursive_geometry_program"),
        "geometry_program": program.to_dict(),
        "geometry_program_compilation": compilation_payload,
        "mass_execution_passport": deepcopy(compilation_payload.get("execution_passport") or {}),
        "geometry_graph_notes": build_geometry_graph_notes(program, compilation),
        "geometry_graph_snapshot": build_geometry_graph_snapshot(program, compilation),
        "geometry_program_bridge_evidence": {
            "schema_version": "arr.maas.geometry_program_source_bridge.v1",
            "status": "materialized",
            "authoritative_visual_geometry": "manifold_compilation_mesh",
            "hard_gate_proxy": "measured_horizontal_mesh_sections",
            "proxy_section_mode": "conservative_band_vertical_occupancy_union",
            "geometry_hash": compilation.geometry_hash,
            "program_hash": program.program_hash(),
            "operator_path": operator_path,
            "proxy_volume_count": len(volumes),
            "raw_mesh_triangle_count": len(compilation.triangles),
            "exported_surface_count": len(surfaces),
            "surface_coordinate_frame": "source_footprint_centroid_local",
            "host_contains_all_proxy_volumes": all(host.covers(volume.footprint) for volume in volumes),
            "parcel_coordinates_in_program": False,
            "legal_fit_mode": legal_fit_mode,
            "legal_fit_strength": round(fit_strength, 4),
            "base_seed_plan_occupancy_fraction": (
                round(base_seed_plan_fraction, 4)
                if base_seed_plan_fraction is not None
                else None
            ),
            "effective_target_plan_area": (
                round(float(effective_target_plan_area), 4)
                if effective_target_plan_area is not None
                else None
            ),
            "explicit_target_plan_area_overrides_seed_occupancy_prior": bool(
                target_plan_area is not None
            ),
            # This is an authoring target, not a source-materialization gate.
            # Exact usable capacity and program fit remain downstream hard
            # gates, where a non-convex language can be measured honestly.
            "minimum_plan_area_target": (
                round(minimum_plan_area_target, 4)
                if minimum_plan_area_target is not None
                else None
            ),
            "achieved_mesh_plan_projection_area": round(achieved_plan_area, 4),
            "minimum_plan_area_target_satisfied": minimum_plan_area_target_satisfied,
            "minimum_plan_area_shortfall_ratio": (
                round(minimum_plan_area_shortfall_ratio, 4)
                if minimum_plan_area_shortfall_ratio is not None
                else None
            ),
        },
        "continuous_surface_evidence": {
            "schema_version": "arr.maas.continuous_surface.v1",
            "status": "materialized",
            "hard_pass": bool(surfaces),
            "principle": str(program.metadata.get("family") or program.name),
            "profiled_volume_count": 1,
            "surface_count": len(surfaces),
            "profiled_roles": [volume_role],
        },
    }
    return SourceMass(
        name=name or f"geometry_program__{program.name}",
        footprint=footprint,
        upper_footprint=upper,
        volumes=volumes,
        surfaces=surfaces,
        notes=(
            "source=recursive_geometry_program",
            "site_fit=principal_frame_bounded",
            f"legal_fit={legal_fit_mode}",
            "legal_proxy=measured_mesh_sections",
        ),
        metadata=metadata,
    )


def _base_seed_plan_occupancy_fraction(program: GeometryProgram) -> float | None:
    """Convert normalized base proportions into a bounded plan-occupancy prior.

    This does not prescribe a completed footprint.  It only prevents a tower,
    compact block and low slab from all expanding to the same host-filling box.
    The value is derived from the catalog's plan-area-to-height proportion, so
    new catalog seeds participate without a parcel-specific lookup table.
    """
    raw_seed = program.metadata.get("base_seed")
    seed_id = str(
        raw_seed.get("seed_id") or raw_seed.get("id") or ""
        if isinstance(raw_seed, dict)
        else raw_seed or ""
    )
    spec = next((item for item in BASE_SEED_SPECS if item.seed_id == seed_id), None)
    if spec is None:
        return None
    proportions = [
        (item.normalized_scale[0] * item.normalized_scale[1])
        / max(item.normalized_scale[2], 0.2)
        for item in BASE_SEED_SPECS
    ]
    plan_to_height = (
        spec.normalized_scale[0] * spec.normalized_scale[1]
    ) / max(spec.normalized_scale[2], 0.2)
    normalized = max(0.0, min(1.0, plan_to_height / max(proportions)))
    return max(0.3, min(0.9, 0.25 + 0.65 * normalized ** 0.5))


def _compile_geometry_program_cached(program: GeometryProgram) -> CompilationResult:
    """Reuse host-independent manifold compilation by canonical AST hash."""
    key = program.program_hash()
    cached = _COMPILATION_CACHE.get(key)
    if cached is not None:
        _COMPILATION_CACHE.move_to_end(key)
        # Metadata/provenance is not part of the canonical geometry hash. Keep
        # the caller's exact program attached to otherwise identical geometry.
        return replace(cached, program=program)
    result = compile_geometry_program(program)
    _COMPILATION_CACHE[key] = result
    _COMPILATION_CACHE.move_to_end(key)
    while len(_COMPILATION_CACHE) > _COMPILATION_CACHE_LIMIT:
        _COMPILATION_CACHE.popitem(last=False)
    return result


def replace_source_dominant_with_geometry_program(
    source: SourceMass,
    program: GeometryProgram,
    *,
    max_total_volumes: int = 5,
    containment_host: Polygon | None = None,
    upper_containment_host: Polygon | None = None,
    upper_fit_strength: float = 0.0,
    minimum_host_plan_coverage: float = 0.0,
) -> SourceMass | None:
    """Compose a recursive primary solid with an existing program role graph."""
    if not source.volumes:
        return None
    dominant = max(source.volumes, key=lambda volume: volume.footprint.area * (volume.top_fraction - volume.bottom_fraction))
    subordinate = tuple(volume for volume in source.volumes if volume is not dominant)
    # The recursive manifold is the physical mass authority. Every remaining
    # legacy component rectangle is a normalized program-role zone inside it,
    # not an orange Lego box attached beside it. Supports, bridges and annexes
    # that must be physical are authored explicitly in the GeometryProgram.
    program_zone_volumes = subordinate
    physical_subordinate: tuple[SourceVolume, ...] = ()
    upper_dominant_host = None
    if upper_containment_host is not None:
        upper_dominant_host = repair_source_polygon(
            upper_containment_host,
            minimum_area=1.0,
        )
    # The old data-backed component rectangle is a program area prior, not a
    # second legal boundary.  Fitting a curved/U/winged graph inside that box
    # punished its empty convex-hull space and made only compact wedges pass.
    # Fit inside the real legal host, then absorb the original physical
    # component union into the new dominant envelope.  Subordinate service/
    # entry rectangles become spatial zones below; targeting only the old
    # dominant area erased their occupied plan and made every calm recursive
    # solid fail program coverage.  The downstream BCR/retention gate remains
    # authoritative, so this target cannot bypass the legal envelope.
    recursive_host = containment_host or dominant.footprint
    original_program_union = unary_union([
        volume.footprint for volume in source.volumes
        if not volume.footprint.is_empty
    ])
    coverage_floor = max(0.0, min(0.95, float(minimum_host_plan_coverage or 0.0)))
    program_target_plan_area = min(
        float(recursive_host.area),
        max(
            float(original_program_union.area),
            float(recursive_host.area) * coverage_floor,
        ),
    )
    recursive = compile_geometry_program_to_source_mass(
        program,
        recursive_host,
        upper_host=upper_dominant_host,
        upper_fit_strength=upper_fit_strength,
        target_plan_area=program_target_plan_area,
        minimum_plan_area=(
            float(recursive_host.area) * coverage_floor
            if coverage_floor > 1e-9
            else None
        ),
        name=f"{source.name}__geometry_{program.name}",
        volume_role=dominant.role,
        max_volume_bands=max(1, min(3, max_total_volumes - len(physical_subordinate))),
    )
    if recursive is None:
        return None
    program_space_zones = _normalized_program_space_zones(
        program_zone_volumes,
        original_dominant=dominant,
    )
    physical_subordinate, subordinate_offsets = _reattach_subordinate_volumes(
        recursive.volumes,
        physical_subordinate,
        original_dominant=dominant,
        containment_host=containment_host,
    )
    volumes = tuple((*recursive.volumes, *physical_subordinate))
    if len(volumes) > max_total_volumes:
        return None
    dominant_surface_roles = {
        dominant.role,
        *(
            surface.volume_role
            for surface in source.surfaces
            if surface.volume_role == dominant.role
        ),
    }
    union = unary_union([volume.footprint for volume in volumes])
    footprint = repair_source_polygon(union, minimum_area=1.0)
    if footprint is None:
        return None
    recursive_surfaces = _rebase_surfaces(
        recursive.surfaces,
        from_origin=recursive.footprint.centroid,
        to_origin=footprint.centroid,
    )
    subordinate_surfaces = _rebase_surfaces(
        tuple(
        surface for surface in source.surfaces
        if surface.volume_role not in dominant_surface_roles
        and surface.volume_role not in {volume.role for volume in program_zone_volumes}
        ),
        from_origin=source.footprint.centroid,
        to_origin=footprint.centroid,
        role_offsets=subordinate_offsets,
    )
    surfaces = tuple((*recursive_surfaces, *subordinate_surfaces))
    metadata = dict(source.metadata)
    metadata.update({
        "family": recursive.metadata.get("family"),
        "primary_language": recursive.metadata.get("primary_language"),
        "formal_principle": recursive.metadata.get("formal_principle"),
        "dominant_gesture": recursive.metadata.get("dominant_gesture"),
        "reference_basis": recursive.metadata.get("reference_basis"),
        "geometry_program": recursive.metadata.get("geometry_program"),
        "geometry_program_compilation": recursive.metadata.get("geometry_program_compilation"),
        "geometry_graph_notes": recursive.metadata.get("geometry_graph_notes"),
        "geometry_graph_snapshot": recursive.metadata.get("geometry_graph_snapshot"),
        "geometry_program_bridge_evidence": recursive.metadata.get("geometry_program_bridge_evidence"),
        "continuous_surface_evidence": recursive.metadata.get("continuous_surface_evidence"),
        "program_space_zones": program_space_zones,
        "program_role_integration_evidence": {
            "schema_version": "arr.maas.program_role_integration.v1",
            "status": "materialized" if program_space_zones else "not_required",
            "mode": "normalized_spatial_zones_inside_dominant_envelope",
            "zone_count": len(program_space_zones),
            "external_program_box_count_removed": len(program_zone_volumes),
            "physical_subordinate_volume_count": len(physical_subordinate),
            "original_component_union_area_m2": round(float(original_program_union.area), 4),
            "recursive_target_plan_area_m2": round(program_target_plan_area, 4),
            "minimum_host_plan_coverage": round(coverage_floor, 4),
            "role_graph_preserved": True,
            "parcel_coordinates_stored": False,
        },
        # The dominant body's plan/section changed, so inherited coherence is
        # stale evidence. Re-measure the exact composed role volumes.
        "coherence_evidence": evaluate_source_volume_coherence(volumes),
    })
    return replace(
        source,
        name=recursive.name,
        footprint=footprint,
        upper_footprint=recursive.upper_footprint,
        volumes=volumes,
        surfaces=surfaces,
        notes=tuple((*source.notes, *recursive.notes)),
        metadata=metadata,
    )


def _is_internal_program_zone_role(role: str) -> bool:
    normalized = str(role).lower()
    return any(token in normalized for token in ("service", "entry", "canopy", "daylight", "monitor"))


def _normalized_program_space_zones(
    volumes: tuple[SourceVolume, ...],
    *,
    original_dominant: SourceVolume,
) -> list[dict[str, Any]]:
    if not volumes:
        return []
    angle, width, depth = _principal_frame(original_dominant.footprint)
    width = max(width, 1e-9)
    depth = max(depth, 1e-9)
    theta = angle * 3.141592653589793 / 180.0
    origin = original_dominant.footprint.centroid
    dominant_area = max(float(original_dominant.footprint.area), 1e-9)
    zones: list[dict[str, Any]] = []
    for volume in volumes:
        center = volume.footprint.centroid
        dx, dy = center.x - origin.x, center.y - origin.y
        normalized_long = max(0.0, min(1.0, 0.5 + (dx * cos(theta) + dy * sin(theta)) / width))
        normalized_short = max(0.0, min(1.0, 0.5 + (-dx * sin(theta) + dy * cos(theta)) / depth))
        nearest_side = min(
            (
                (normalized_long, "west"),
                (1.0 - normalized_long, "east"),
                (normalized_short, "south"),
                (1.0 - normalized_short, "north"),
            ),
            key=lambda item: item[0],
        )[1]
        zones.append({
            "zone_id": f"zone:{volume.role}",
            "role": volume.role,
            "relation": "embedded_in_dominant_envelope",
            "normalized_center": [
                round(normalized_long, 4),
                round(normalized_short, 4),
            ],
            "normalized_frame": "dominant_mass_principal_long_short_axes",
            "nearest_envelope_side": nearest_side,
            "plan_area_ratio": round(min(0.45, float(volume.footprint.area) / dominant_area), 4),
            "bottom_fraction": round(float(volume.bottom_fraction), 4),
            "top_fraction": round(float(volume.top_fraction), 4),
            "physical_envelope_owner_role": original_dominant.role,
        })
    return zones


def _fit_vertices_to_host(
    compilation: CompilationResult,
    host: Polygon,
    *,
    target_plan_area: float | None = None,
    minimum_plan_area: float | None = None,
) -> tuple[tuple[tuple[float, float, float], ...], tuple[tuple[float, float, float], ...]] | None:
    vertices = compilation.vertices
    if not vertices:
        return None
    plan = MultiPoint([(x, y) for x, y, _z in vertices]).convex_hull
    if not isinstance(plan, Polygon) or plan.area <= 1e-9:
        return None
    source_angle, source_width, source_depth = _principal_frame(plan)
    target_angle, target_width, target_depth = _principal_frame(host)
    if min(source_width, source_depth, target_width, target_depth) <= 1e-9:
        return None
    source_theta = source_angle * 3.141592653589793 / 180.0
    target_theta = target_angle * 3.141592653589793 / 180.0
    source_center = plan.centroid
    target_center = host.centroid
    requested_long_scale = target_width / source_width * 0.95
    requested_short_scale = target_depth / source_depth * 0.95
    # A uniform fit preserves the authored solid proportion while a fully
    # independent fit erases it.  The former implementation allowed a 3x
    # relative axis stretch; on the real benchmark parcel that mapped BLOCK,
    # SLAB, BAR and PROFILED_PRISM to the same ~1.5 plan aspect ratio.  In other
    # words the AST retained the base-seed label while the materialized geometry
    # lost the base language.  Keep a small, aspect-conditioned host response:
    # compact seeds remain compact, intermediate plates may follow the parcel a
    # little more, and long bars retain a visibly long plan.
    minimum_axis_scale = min(requested_long_scale, requested_short_scale)
    source_aspect = max(source_width, source_depth) / max(min(source_width, source_depth), 1e-9)
    if source_aspect <= 1.25:
        maximum_relative_stretch = 1.25
    elif source_aspect <= 2.2:
        maximum_relative_stretch = 1.4
    else:
        maximum_relative_stretch = 1.5
    long_scale = min(requested_long_scale, minimum_axis_scale * maximum_relative_stretch)
    short_scale = min(requested_short_scale, minimum_axis_scale * maximum_relative_stretch)
    min_z = min(vertex[2] for vertex in vertices)
    max_z = max(vertex[2] for vertex in vertices)
    z_span = max(max_z - min_z, 1e-9)
    source_projection_area = _mesh_plan_projection_area(vertices, compilation.triangles)
    for factor in (1.0, 0.94, 0.88, 0.82, 0.76, 0.68, 0.58, 0.48):
        world: list[tuple[float, float, float]] = []
        for x, y, z in vertices:
            dx, dy = x - source_center.x, y - source_center.y
            # Source principal coordinates -> bounded axis scaling -> target
            # principal frame.  This is still normalized and coordinate-free.
            local_long = dx * cos(source_theta) + dy * sin(source_theta)
            local_short = -dx * sin(source_theta) + dy * cos(source_theta)
            fitted_long = local_long * long_scale * factor
            fitted_short = local_short * short_scale * factor
            rx = fitted_long * cos(target_theta) - fitted_short * sin(target_theta) + target_center.x
            ry = fitted_long * sin(target_theta) + fitted_short * cos(target_theta) + target_center.y
            world.append((rx, ry, (z - min_z) / z_span))
        if _mesh_plan_projection_inside_host(
            tuple(world),
            compilation.triangles,
            host,
        ):
            if target_plan_area is not None and source_projection_area > 1e-9:
                fitted_projection_area = (
                    source_projection_area * long_scale * short_scale * factor * factor
                )
                area_factor = min(
                    1.0,
                    (max(0.2, float(target_plan_area)) / max(fitted_projection_area, 1e-9)) ** 0.5,
                )
                if area_factor < 1.0 - 1e-9:
                    world = [
                        (
                            target_center.x + (x - target_center.x) * area_factor,
                            target_center.y + (y - target_center.y) * area_factor,
                            z,
                        )
                        for x, y, z in world
                    ]
            # ``minimum_plan_area`` is an authoring target supplied by the
            # feasible-capacity contract. ``target_plan_area`` retains its older
            # independent meaning as a shrink target for direct bridge callers.
            # A thin curved wall can have a host-filling convex hull while its
            # real mesh projection occupies only a small fraction of the site.
            # Widen it as far as the legal host permits, but do not delete the
            # language here: exact capacity and VLM stages own that hard verdict.
            actual_projection_area = _mesh_plan_projection_area(
                tuple(world),
                compilation.triangles,
            )
            if (
                minimum_plan_area is not None
                and actual_projection_area + 1e-7 < max(0.2, float(minimum_plan_area))
            ):
                target_area = max(0.2, float(minimum_plan_area))
                required_short_growth = target_area / max(actual_projection_area, 1e-9)
                available_short_growth = requested_short_scale / max(
                    short_scale * area_factor,
                    1e-9,
                )
                short_growth = min(required_short_growth, available_short_growth)
                widened = _widen_vertices_in_frame(
                    world,
                    center=target_center,
                    theta=target_theta,
                    growth=short_growth,
                )
                if not _mesh_plan_projection_inside_host(
                    tuple(widened),
                    compilation.triangles,
                    host,
                ):
                    # An irregular host can prevent the rectangular-frame
                    # estimate from fitting. Find the widest contained result
                    # without converting this design target into a rejection.
                    lower_growth, upper_growth = 1.0, short_growth
                    for _iteration in range(10):
                        probe_growth = (lower_growth + upper_growth) / 2.0
                        probe = _widen_vertices_in_frame(
                            world,
                            center=target_center,
                            theta=target_theta,
                            growth=probe_growth,
                        )
                        if _mesh_plan_projection_inside_host(
                            tuple(probe),
                            compilation.triangles,
                            host,
                        ):
                            lower_growth = probe_growth
                            widened = probe
                        else:
                            upper_growth = probe_growth
                world = list(widened)
            local = tuple((x - target_center.x, y - target_center.y, z) for x, y, z in world)
            return tuple(world), local
    return None


def _widen_vertices_in_frame(
    vertices: list[tuple[float, float, float]],
    *,
    center,
    theta: float,
    growth: float,
) -> list[tuple[float, float, float]]:
    """Widen a fitted solid across its host-short axis without changing length."""
    widened: list[tuple[float, float, float]] = []
    for x, y, z in vertices:
        dx, dy = x - center.x, y - center.y
        fitted_long = dx * cos(theta) + dy * sin(theta)
        fitted_short = (-dx * sin(theta) + dy * cos(theta)) * growth
        widened.append((
            fitted_long * cos(theta) - fitted_short * sin(theta) + center.x,
            fitted_long * sin(theta) + fitted_short * cos(theta) + center.y,
            z,
        ))
    return widened


def _mesh_plan_projection_area(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
) -> float:
    """Top-view solid area without replacing a non-convex graph by its hull."""
    projected: list[Polygon] = []
    for triangle in triangles:
        coordinates = [
            (float(vertices[index][0]), float(vertices[index][1]))
            for index in triangle
        ]
        if not all(isfinite(value) for coordinate in coordinates for value in coordinate):
            continue
        polygon = Polygon(coordinates)
        if polygon.is_empty or polygon.area <= 1e-10:
            continue
        for part in _polygon_parts(make_valid(polygon)):
            if not part.is_empty and part.area > 1e-10:
                projected.append(part)
    if not projected:
        return 0.0

    # GEOS can occasionally report ``Ring edge missing`` when many mesh
    # triangles share nearly-identical projected edges.  Retry on successively
    # coarser metric grids; this changes coordinates by at most 0.01 mm while
    # retaining courts, notches and courtyards at architectural scale.
    for grid_size in (0.0, 1e-9, 1e-7, 1e-5):
        try:
            candidates = (
                projected
                if grid_size == 0.0
                else [
                    part
                    for polygon in projected
                    for part in _polygon_parts(set_precision(polygon, grid_size))
                    if not part.is_empty and part.area > 1e-10
                ]
            )
            if candidates:
                area = float(unary_union(candidates).area)
                if isfinite(area) and area >= 0.0:
                    return area
        except GEOSException:
            continue

    # A numerically pathological candidate must not abort an entire portfolio
    # run.  The largest valid projected triangle is a conservative lower bound,
    # so capacity gates can reject the candidate instead of receiving a false
    # positive from a convex-hull or summed-area fallback.
    return max(float(polygon.area) for polygon in projected)


def _mesh_plan_projection_inside_host(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    host: Polygon,
) -> bool:
    """Test the occupied mesh plan, not the empty space in its convex hull."""

    legal = host.buffer(1e-7)
    occupied_triangle_found = False
    for triangle in triangles:
        coordinates = [
            (float(vertices[index][0]), float(vertices[index][1]))
            for index in triangle
        ]
        if not all(isfinite(value) for coordinate in coordinates for value in coordinate):
            return False
        polygon = Polygon(coordinates)
        if polygon.is_empty or polygon.area <= 1e-10:
            continue
        occupied_triangle_found = True
        if not legal.covers(polygon):
            return False
    return occupied_triangle_found


def _rebase_surfaces(
    surfaces: tuple[SourceSurface, ...],
    *,
    from_origin: Any,
    to_origin: Any,
    role_offsets: dict[str, tuple[float, float]] | None = None,
) -> tuple[SourceSurface, ...]:
    """Preserve world coordinates while changing SourceMass local origin."""
    xoff = float(from_origin.x) - float(to_origin.x)
    yoff = float(from_origin.y) - float(to_origin.y)
    offsets = role_offsets or {}
    return tuple(
        replace(
            surface,
            vertices_m=tuple(
                (
                    x + xoff + offsets.get(surface.volume_role, (0.0, 0.0))[0],
                    y + yoff + offsets.get(surface.volume_role, (0.0, 0.0))[1],
                    z,
                )
                for x, y, z in surface.vertices_m
            ),
        )
        for surface in surfaces
    )


def _reattach_subordinate_volumes(
    recursive_volumes: tuple[SourceVolume, ...],
    subordinate: tuple[SourceVolume, ...],
    *,
    original_dominant: SourceVolume,
    containment_host: Polygon | None = None,
) -> tuple[tuple[SourceVolume, ...], dict[str, tuple[float, float]]]:
    """Re-materialize ``attach`` relations around a replaced primary solid.

    The source role graph is preserved, but the old attachment coordinates are
    not: each subordinate is placed against the new primary boundary using its
    original normalized direction. This avoids both disconnected LEGO pieces
    and large accidental collisions after a cube, taper or sweep replacement.
    """
    main = unary_union([volume.footprint for volume in recursive_volumes])
    if main.is_empty:
        return subordinate, {}
    main_center = main.centroid
    old_center = original_dominant.footprint.centroid
    moved: list[SourceVolume] = []
    offsets: dict[str, tuple[float, float]] = {}
    boundary_points = [
        point
        for polygon in _polygon_parts(main)
        for point in list(polygon.exterior.coords)[:-1]
    ]
    for volume in subordinate:
        center = volume.footprint.centroid
        dx0, dy0 = center.x - old_center.x, center.y - old_center.y
        length = hypot(dx0, dy0)
        if length <= 1e-9 or not boundary_points:
            moved.append(volume)
            continue
        ux, uy = dx0 / length, dy0 / length
        support = max(boundary_points, key=lambda point: (point[0] - main_center.x) * ux + (point[1] - main_center.y) * uy)
        subordinate_points = list(volume.footprint.exterior.coords)[:-1]
        half_extent = max(
            abs((point[0] - center.x) * ux + (point[1] - center.y) * uy)
            for point in subordinate_points
        ) if subordinate_points else 0.0
        # Fifteen percent embed gives a legible architectural joint without
        # turning the service/entry body into a redundant overlapping solid.
        desired_x = support[0] + ux * half_extent * 0.85
        desired_y = support[1] + uy * half_extent * 0.85
        xoff, yoff = desired_x - center.x, desired_y - center.y
        geometry = translate(volume.footprint, xoff=xoff, yoff=yoff)
        # Non-convex primaries can put the support vertex beside a re-entrant
        # corner. Close any residual gap by the exact nearest-point vector.
        if geometry.distance(main) > 0.12:
            target, current = nearest_points(main, geometry)
            correction_x = target.x - current.x
            correction_y = target.y - current.y
            geometry = translate(geometry, xoff=correction_x, yoff=correction_y)
            xoff += correction_x
            yoff += correction_y
        if containment_host is not None and not containment_host.buffer(1e-7).covers(geometry):
            # Search the same typed attachment vector for the furthest legal
            # placement. Never clip a service/entry body into debris.
            legal_choice: tuple[Any, float, float] | None = None
            for fraction in (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0):
                candidate = translate(volume.footprint, xoff=xoff * fraction, yoff=yoff * fraction)
                if containment_host.buffer(1e-7).covers(candidate) and candidate.distance(main) <= 0.12:
                    legal_choice = candidate, xoff * fraction, yoff * fraction
                    break
            if legal_choice is None:
                searched = _search_legal_attachment(
                    volume,
                    main,
                    containment_host,
                    preferred_direction=(ux, uy),
                )
                if searched is None:
                    geometry, xoff, yoff = volume.footprint, 0.0, 0.0
                else:
                    geometry, xoff, yoff = searched
            else:
                geometry, xoff, yoff = legal_choice
        moved.append(replace(volume, footprint=geometry))
        offsets[volume.role] = (xoff, yoff)
    return tuple(moved), offsets


def _search_legal_attachment(
    volume: SourceVolume,
    main: Any,
    host: Polygon,
    *,
    preferred_direction: tuple[float, float],
) -> tuple[Any, float, float] | None:
    """Find a bounded, host-contained attachment without clipping geometry."""
    center = volume.footprint.centroid
    main_center = main.centroid
    boundary: list[tuple[float, float]] = []
    for polygon in _polygon_parts(main):
        coordinates = list(polygon.exterior.coords)
        for left, right in zip(coordinates, coordinates[1:]):
            boundary.extend((left, ((left[0] + right[0]) / 2.0, (left[1] + right[1]) / 2.0)))
    candidates: list[tuple[float, Any, float, float]] = []
    host_buffer = host.buffer(1e-7)
    preferred_x, preferred_y = preferred_direction
    scale_ref = max(host.area ** 0.5, 1e-9)
    for scale_factor in (1.0,):
        body = volume.footprint
        body_center = body.centroid
        points = list(body.exterior.coords)[:-1]
        for point in boundary:
            vx, vy = point[0] - main_center.x, point[1] - main_center.y
            length = hypot(vx, vy)
            if length <= 1e-9:
                continue
            ux, uy = vx / length, vy / length
            half_extent = max(
                abs((vertex[0] - body_center.x) * ux + (vertex[1] - body_center.y) * uy)
                for vertex in points
            ) if points else 0.0
            target_x = point[0] + ux * half_extent * 0.86
            target_y = point[1] + uy * half_extent * 0.86
            xoff, yoff = target_x - body_center.x, target_y - body_center.y
            placed = translate(body, xoff=xoff, yoff=yoff)
            if not host_buffer.covers(placed) or placed.distance(main) > 0.12:
                continue
            overlap = float(placed.intersection(main).area) / max(float(placed.area), 1e-9)
            if overlap > 0.46:
                continue
            direction_fit = ux * preferred_x + uy * preferred_y
            movement = hypot(target_x - center.x, target_y - center.y) / scale_ref
            score = direction_fit * 1.6 - movement - abs(overlap - 0.14) * 0.5 + scale_factor * 0.2
            candidates.append((score, placed, target_x - center.x, target_y - center.y))
    if not candidates:
        return None
    _score, geometry, xoff, yoff = max(candidates, key=lambda item: item[0])
    return geometry, xoff, yoff


def _mesh_section_polygon(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
    z: float,
) -> Polygon | Any | None:
    segments: list[LineString] = []
    epsilon = 1e-7
    for triangle in triangles:
        points = [vertices[index] for index in triangle]
        intersections: list[tuple[float, float]] = []
        for left, right in zip(points, (*points[1:], points[0])):
            lz, rz = left[2] - z, right[2] - z
            if abs(lz) <= epsilon:
                intersections.append((left[0], left[1]))
            if lz * rz < -epsilon * epsilon:
                amount = (z - left[2]) / (right[2] - left[2])
                intersections.append((
                    left[0] + (right[0] - left[0]) * amount,
                    left[1] + (right[1] - left[1]) * amount,
                ))
        unique: list[tuple[float, float]] = []
        for point in intersections:
            if not any(hypot(point[0] - other[0], point[1] - other[1]) <= 1e-6 for other in unique):
                unique.append(point)
        if len(unique) >= 2:
            # Adjacent manifold triangles calculate the same plane/edge
            # intersection independently.  Their coordinates can differ by
            # ~1e-12 even though the kernel mesh is watertight.  GEOS
            # polygonize requires bit-identical endpoints; without this
            # metric-scale normalization, bent/split wing lower bands vanish
            # and the legal proxy contains only an arbitrary upper slice.
            # 1e-8 m is far below the tiny-edge gate and does not alter design
            # geometry, but it closes the section graph deterministically.
            segment = tuple(
                (round(float(point[0]), 8), round(float(point[1]), 8))
                for point in unique[:2]
            )
            if segment[0] != segment[1]:
                segments.append(LineString(segment))
    if not segments:
        return None
    polygons = tuple(polygonize(unary_union(segments)))
    if not polygons:
        return None
    hole_regions = tuple(
        Polygon(interior)
        for polygon in polygons
        for interior in polygon.interiors
    )
    retained = tuple(
        polygon
        for polygon in polygons
        if not any(
            hole.covers(polygon.representative_point())
            for hole in hole_regions
        )
    )
    return unary_union(retained or polygons)


def _mesh_surfaces(
    local_vertices: tuple[tuple[float, float, float], ...],
    compilation: CompilationResult,
    *,
    volume_role: str,
    max_raw_surfaces: int,
) -> tuple[SourceSurface, ...]:
    records: list[tuple[float, tuple[int, int, int], tuple[int, int, int]]] = []
    for triangle in compilation.triangles:
        a, b, c = (local_vertices[index] for index in triangle)
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        magnitude = max(hypot(hypot(nx, ny), nz), 1e-12)
        area = magnitude / 2.0
        normal_bucket = (
            int(round(nx / magnitude * 2.0)),
            int(round(ny / magnitude * 2.0)),
            int(round(nz / magnitude * 2.0)),
        )
        records.append((area, triangle, normal_bucket))
    records.sort(key=lambda item: item[0], reverse=True)
    # Do not make the review/VLM geometry a lossy subset of the solid that
    # passed the manifold gate. Dropping all but the largest triangles made
    # bends, arrays and sweeps render as open fragments even though the
    # compiler's authoritative mesh was watertight. Kernel triangles are a
    # transport detail; clean-mass complexity is measured by semantic normal
    # patches (``effective_surface_count``), not triangulation count.
    limit = max(8, min(4096, int(max_raw_surfaces)))
    root_operator = compilation.program.node_map[compilation.program.root_id].operator
    return tuple(
        SourceSurface(
            role=f"recursive_mesh_{index}",
            volume_role=volume_role,
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(local_vertices[vertex_index] for vertex_index in triangle),
            operator=root_operator,
            semantic_patch_id=f"{volume_role}:recursive_normal:{bucket[0]}:{bucket[1]}:{bucket[2]}",
        )
        for index, (_area, triangle, bucket) in enumerate(records[:limit])
    )


def _merge_equal_band_footprints(volumes: tuple[SourceVolume, ...]) -> tuple[SourceVolume, ...]:
    merged: list[SourceVolume] = []
    for volume in sorted(volumes, key=lambda item: (item.bottom_fraction, -item.footprint.area)):
        previous = merged[-1] if merged else None
        if (
            previous is not None
            and abs(previous.top_fraction - volume.bottom_fraction) <= 1e-8
            and previous.footprint.symmetric_difference(volume.footprint).area
            <= max(0.02, previous.footprint.area * 0.005)
        ):
            merged[-1] = replace(previous, top_fraction=volume.top_fraction)
        else:
            merged.append(volume)
    return tuple(merged)


def _polygon_parts(geometry: Any) -> tuple[Polygon, ...]:
    if geometry is None or geometry.is_empty:
        return ()
    if isinstance(geometry, Polygon):
        return (geometry,)
    return tuple(sorted(
        (
            part
            for child in getattr(geometry, "geoms", ())
            for part in _polygon_parts(child)
        ),
        key=lambda part: part.area,
        reverse=True,
    ))


def _principal_frame(poly: Polygon) -> tuple[float, float, float]:
    coordinates = list(poly.minimum_rotated_rectangle.exterior.coords)
    edges = [
        (hypot(x2 - x1, y2 - y1), degrees(atan2(y2 - y1, x2 - x1)))
        for (x1, y1), (x2, y2) in zip(coordinates, coordinates[1:])
    ]
    edges.sort(reverse=True)
    width = edges[0][0] if edges else 0.0
    depth = edges[-1][0] if edges else 0.0
    return (edges[0][1] if edges else 0.0), width, depth


__all__ = [
    "compile_geometry_program_to_source_mass",
    "floorwise_source_to_geometry_program",
    "materialize_floorwise_legal_source",
    "replace_source_dominant_with_geometry_program",
]
