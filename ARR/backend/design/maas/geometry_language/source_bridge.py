"""Project recursive solid programs into the real parcel/program SourceMass lane.

The manifold solid remains the visual authority.  A small set of measured
horizontal sections becomes the conservative 2.5D proxy used by existing
program, FAR, sunlight and parking hard gates.  No parcel coordinate or
completed building is stored in a geometry program.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import replace
from math import atan2, cos, degrees, hypot, sin
from typing import Any

from shapely.affinity import translate
from shapely.geometry import LineString, MultiPoint, Polygon
from shapely.ops import nearest_points, polygonize, unary_union

from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.source_geometry.coherence import evaluate_source_volume_coherence
from design.maas.source_geometry.polygon_quality import repair_source_polygon

from .ast import GeometryProgram
from .compiler import CompilationResult, compile_geometry_program
from .gate import GeometryGatePolicy, compilation_gate


_COMPILATION_CACHE: "OrderedDict[str, CompilationResult]" = OrderedDict()
_COMPILATION_CACHE_LIMIT = 512


def compile_geometry_program_to_source_mass(
    program: GeometryProgram,
    host: Polygon,
    *,
    upper_host: Polygon | None = None,
    upper_fit_strength: float = 1.0,
    target_plan_area: float | None = None,
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
    if compilation.status != "compiled" or compilation_gate(compilation, gate_policy):
        return None
    transformed = _fit_vertices_to_host(
        compilation,
        host,
        target_plan_area=target_plan_area,
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
                target_plan_area=target_plan_area,
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

    metadata = {
        "family": str(program.metadata.get("family") or program.name),
        "primary_language": str(program.metadata.get("family") or program.name),
        "formal_principle": str(program.metadata.get("family") or program.name),
        "dominant_gesture": str(program.metadata.get("family") or program.root_id),
        "reference_basis": str(program.metadata.get("reference_language") or "recursive_geometry_program"),
        "geometry_program": program.to_dict(),
        "geometry_program_compilation": compilation.to_dict(include_mesh=False),
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
    upper_fit_strength: float = 1.0,
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
    program_target_plan_area = min(
        float(recursive_host.area),
        float(original_program_union.area),
    )
    recursive = compile_geometry_program_to_source_mass(
        program,
        recursive_host,
        upper_host=upper_dominant_host,
        upper_fit_strength=upper_fit_strength,
        target_plan_area=program_target_plan_area,
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
    minx, miny, maxx, maxy = original_dominant.footprint.bounds
    width = max(maxx - minx, 1e-9)
    depth = max(maxy - miny, 1e-9)
    dominant_area = max(float(original_dominant.footprint.area), 1e-9)
    zones: list[dict[str, Any]] = []
    for volume in volumes:
        center = volume.footprint.centroid
        zones.append({
            "zone_id": f"zone:{volume.role}",
            "role": volume.role,
            "relation": "embedded_in_dominant_envelope",
            "normalized_center": [
                round(max(0.0, min(1.0, (center.x - minx) / width)), 4),
                round(max(0.0, min(1.0, (center.y - miny) / depth)), 4),
            ],
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
    # A uniform fit preserves a BAR's local aspect ratio even when the parcel
    # or program host is much broader, leaving most of a gym host empty.  A
    # fully independent fit would erase the base language.  Bound the relative
    # axis stretch so the solid responds to its host while a bar remains a bar
    # and a block remains compact.
    minimum_axis_scale = min(requested_long_scale, requested_short_scale)
    maximum_relative_stretch = 3.0
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
        hull = MultiPoint([(x, y) for x, y, _z in world]).convex_hull
        if host.buffer(1e-7).covers(hull):
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
            local = tuple((x - target_center.x, y - target_center.y, z) for x, y, z in world)
            return tuple(world), local
    return None


def _mesh_plan_projection_area(
    vertices: tuple[tuple[float, float, float], ...],
    triangles: tuple[tuple[int, int, int], ...],
) -> float:
    """Top-view solid area without replacing a non-convex graph by its hull."""
    projected = []
    for triangle in triangles:
        polygon = Polygon([(vertices[index][0], vertices[index][1]) for index in triangle])
        if not polygon.is_empty and polygon.area > 1e-10:
            projected.append(polygon)
    if not projected:
        return 0.0
    return float(unary_union(projected).area)


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
            segments.append(LineString((unique[0], unique[1])))
    if not segments:
        return None
    polygons = tuple(polygonize(unary_union(segments)))
    if not polygons:
        return None
    return unary_union(polygons)


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
    "replace_source_dominant_with_geometry_program",
]
