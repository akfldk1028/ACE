"""Bounded whole-legal-field affine placement for one authored MASS solid.

The solver authors exactly one site-placement Matrix4.  It screens a small,
deterministic set of principal-frame/anisotropy/z-shear alternatives in 2D,
then compiles only the best few.  An unchanged authored solid is certified
first; exact floorwise legal CSG is available only to an explicitly authored
stepped body.  Floor capacity vectors remain provenance; only their aggregate
is a hard placement constraint.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import atan2, degrees, isfinite, sqrt
from typing import Any

from shapely.affinity import affine_transform
from shapely.geometry import MultiPoint, Polygon
from shapely.ops import unary_union

from .affine_matrix import (
    Matrix4,
    compose_matrix4,
    inverse_matrix4,
    rotation_matrix4,
    scale_matrix4,
    transform_point3,
    translation_matrix4,
)
from .ast import GeometryProgram
from .authored_legal_preservation import (
    AuthoredLegalPreservationResult,
    certify_authored_affine_program,
)
from .compiler import CompilationResult, compile_geometry_program
from .floorwise_legal_program import (
    FloorwiseLegalProgramResult,
    is_intentional_floorwise_stepped_program,
    _mesh_section_polygon,
)
from .gate import GeometryGatePolicy, compilation_gate
from .source_bridge import (
    HostFitTransform,
    append_site_placement_matrix,
)


@dataclass(frozen=True)
class LegalFieldAffineSelection:
    fit: HostFitTransform
    projection: (
        AuthoredLegalPreservationResult
        | FloorwiseLegalProgramResult
    )
    evidence: dict[str, Any]


@dataclass(frozen=True)
class _ScreenedAlternative:
    matrix4: Matrix4
    matrix_hash: str
    preclip_areas_m2: tuple[float, ...]
    clipped_areas_m2: tuple[float, ...]
    profile_distortion: float
    aggregate_retention: float
    minimum_floor_retention: float
    aggregate_area_m2: float
    orientation_degrees: int
    anisotropy: float
    area_factor: float
    shear_factor: float


def select_legal_field_affine_projection(
    program: GeometryProgram,
    *,
    legal_sections: tuple[Polygon, ...],
    target_floor_areas_m2: tuple[float, ...],
    floor_capacity_plan_hash: str,
    aggregate_target_area_m2: float | None = None,
    maximum_exact_candidates: int = 4,
    minimum_aggregate_target_ratio: float = 0.995,
) -> LegalFieldAffineSelection | None:
    """Select one capacity-valid affine pose against the complete legal field."""

    if (
        not legal_sections
        or len(legal_sections) != len(target_floor_areas_m2)
        or not floor_capacity_plan_hash.strip()
        or any(
            not isinstance(section, Polygon)
            or section.is_empty
            or not section.is_valid
            or not isfinite(float(section.area))
            or float(section.area) <= 1e-9
            for section in legal_sections
        )
    ):
        return None
    aggregate_target = (
        float(aggregate_target_area_m2)
        if aggregate_target_area_m2 is not None
        else sum(float(value) for value in target_floor_areas_m2)
    )
    if not isfinite(aggregate_target) or aggregate_target <= 1e-9:
        return None
    minimum_target_ratio = max(
        0.05,
        min(0.995, float(minimum_aggregate_target_ratio)),
    )
    compilation = compile_geometry_program(program)
    if (
        compilation.status != "compiled"
        or compilation_gate(
            compilation,
            GeometryGatePolicy(maximum_components=1),
        )
    ):
        return None
    source_sections = _source_floor_sections(
        compilation,
        floor_count=len(legal_sections),
    )
    if source_sections is None:
        return None
    alternatives = _screen_affine_alternatives(
        compilation,
        source_sections=source_sections,
        legal_sections=legal_sections,
        aggregate_target=aggregate_target,
        minimum_aggregate_target_ratio=minimum_target_ratio,
    )
    if not alternatives:
        return None

    exact_limit = max(1, min(4, int(maximum_exact_candidates)))
    exact_shortlist = _exact_shortlist(
        alternatives,
        limit=exact_limit,
    )
    exact_records: list[
        tuple[
            tuple[float, float, float, str],
            HostFitTransform,
            (
                AuthoredLegalPreservationResult
                | FloorwiseLegalProgramResult
            ),
            _ScreenedAlternative,
            tuple[float, ...],
        ]
    ] = []
    for alternative in exact_shortlist:
        world_vertices = tuple(
            transform_point3(alternative.matrix4, vertex)
            for vertex in compilation.vertices
        )
        fit = HostFitTransform(
            matrix4=alternative.matrix4,
            inverse_matrix4=inverse_matrix4(alternative.matrix4),
            world_vertices=world_vertices,
            achieved_plan_area_m2=float(
                MultiPoint([
                    (vertex[0], vertex[1])
                    for vertex in world_vertices
                ]).convex_hull.area
            ),
        )
        placed = append_site_placement_matrix(program, fit)
        projected = certify_authored_affine_program(
            placed,
            legal_sections=legal_sections,
            target_floor_areas_m2=target_floor_areas_m2,
            floor_capacity_plan_hash=floor_capacity_plan_hash,
            minimum_aggregate_target_ratio=minimum_target_ratio,
        )
        if projected is None:
            continue
        certificate = projected.certificate
        achieved = tuple(
            float(value)
            for value in projected.achieved_floor_areas_m2
        )
        achieved_total = sum(achieved)
        if (
            achieved_total + 1e-7
            < aggregate_target * minimum_target_ratio
            or certificate.get("hard_pass") is not True
            or certificate.get("manifold") is not True
            or certificate.get("watertight") is not True
            or certificate.get("all_sections_contained") is not True
        ):
            continue
        distortion = _profile_distortion(
            alternative.preclip_areas_m2,
            achieved,
        )
        band_profile = _conservative_band_profile(
            compilation,
            alternative.matrix4,
            projected.final_compilation,
            floor_count=len(legal_sections),
        )
        if band_profile is None:
            continue
        band_preclip, band_final = band_profile
        distortion = _profile_distortion(band_preclip, band_final)
        retention_by_floor = tuple(
            final_area / max(preclip_area, 1e-9)
            for final_area, preclip_area in zip(
                band_final,
                band_preclip,
            )
        )
        exact_records.append((
            (
                distortion,
                -min(retention_by_floor),
                -sum(band_final) / max(
                    sum(band_preclip),
                    1e-9,
                ),
                projected.program.program_hash(),
            ),
            fit,
            projected,
            alternative,
            achieved,
        ))
    if not exact_records:
        return None
    exact_records.sort(key=lambda record: record[0])
    _rank, fit, projection, selected, achieved = exact_records[0]
    evidence = {
        "schema_version": "arr.maas.legal_field_affine_placement.v1",
        "authority": "whole_legal_section_field",
        "screening_mode": (
            "bounded_2d_then_exact_authored_preservation"
        ),
        "projection_mode": projection.certificate["projection_mode"],
        "screened_candidate_count": len(alternatives),
        "exact_candidate_limit": exact_limit,
        "exact_compiled_candidate_count": min(
            exact_limit,
            len(exact_shortlist),
        ),
        "exact_feasible_candidate_count": len(exact_records),
        "aggregate_target_area_m2": round(aggregate_target, 8),
        "minimum_aggregate_target_ratio": minimum_target_ratio,
        "achieved_aggregate_area_m2": round(sum(achieved), 8),
        "profile_distortion": round(
            _rank[0],
            10,
        ),
        "preclip_floor_areas_m2": [
            round(value, 8)
            for value in selected.preclip_areas_m2
        ],
        "achieved_floor_areas_m2": [
            round(value, 8)
            for value in achieved
        ],
        "selected_matrix_hash": selected.matrix_hash,
        "orientation_degrees": selected.orientation_degrees,
        "anisotropy": selected.anisotropy,
        "area_factor": selected.area_factor,
        "shear_factor": selected.shear_factor,
        "floor_target_vector_authors_geometry": False,
        "single_site_placement_matrix": True,
    }
    return LegalFieldAffineSelection(
        fit=fit,
        projection=projection,
        evidence=evidence,
    )


def _source_floor_sections(
    compilation: CompilationResult,
    *,
    floor_count: int,
) -> tuple[Any, ...] | None:
    bounds = (compilation.metrics or {}).get("bounds") or ()
    if len(bounds) != 2 or len(bounds[0]) != 3 or len(bounds[1]) != 3:
        return None
    min_z = float(bounds[0][2])
    max_z = float(bounds[1][2])
    z_span = max_z - min_z
    if not isfinite(z_span) or z_span <= 1e-9:
        return None
    sections = tuple(
        _mesh_section_polygon(
            compilation,
            min_z + z_span * (index + 0.5) / floor_count,
        )
        for index in range(floor_count)
    )
    if any(
        section is None
        or section.is_empty
        or not isfinite(float(section.area))
        or float(section.area) <= 1e-9
        for section in sections
    ):
        return None
    return sections


def _screen_affine_alternatives(
    compilation: CompilationResult,
    *,
    source_sections: tuple[Any, ...],
    legal_sections: tuple[Polygon, ...],
    aggregate_target: float,
    minimum_aggregate_target_ratio: float,
) -> tuple[_ScreenedAlternative, ...]:
    bounds = (compilation.metrics or {}).get("bounds") or ()
    min_z = float(bounds[0][2])
    max_z = float(bounds[1][2])
    z_span = max_z - min_z
    source_plan = unary_union(source_sections).convex_hull
    source_angle, source_long, source_short = _principal_frame(source_plan)
    legal_frame = unary_union(legal_sections).convex_hull
    legal_angle, legal_long, legal_short = _principal_frame(legal_frame)
    if min(source_long, source_short, legal_long, legal_short) <= 1e-9:
        return ()
    source_reference_area = sum(
        float(section.area)
        for section in source_sections
    ) / len(source_sections)
    desired_plan_area = _waterfill_plan_area(
        tuple(float(section.area) for section in legal_sections),
        aggregate_target,
    )
    if desired_plan_area <= 1e-9 or source_reference_area <= 1e-9:
        return ()
    uniform_scale = sqrt(desired_plan_area / source_reference_area)
    source_aspect = source_long / source_short
    legal_aspect = legal_long / legal_short
    frame_anisotropy = max(
        0.67,
        min(1.28, sqrt(legal_aspect / max(source_aspect, 1e-9))),
    )
    anisotropies = _unique_floats((
        frame_anisotropy,
        0.78,
        1.0,
    ))
    # The legal prisms have piecewise-constant centroids inside each floor
    # band.  Include the unsheared and half-path poses so a linear z shear is
    # not forced to keep translating a solid after it has entered the upper
    # legal prism.
    shear_factors = (0.0, 0.5, 1.0)
    legal_centroids = tuple(section.centroid for section in legal_sections)
    alternatives: list[_ScreenedAlternative] = []
    seen_hashes: set[str] = set()

    for orientation_degrees in (0, 90, 180, 270):
        target_angle = legal_angle + float(orientation_degrees)
        for anisotropy in anisotropies:
            for shear_factor in shear_factors:
                def matrix_at(scale_multiplier: float) -> Matrix4:
                    return _pose_matrix(
                        source_sections=source_sections,
                        legal_centroids=legal_centroids,
                        source_plan=source_plan,
                        source_angle=source_angle,
                        target_angle=target_angle,
                        source_min_z=min_z,
                        source_max_z=max_z,
                        uniform_scale=uniform_scale,
                        anisotropy=anisotropy,
                        shear_factor=shear_factor,
                        scale_multiplier=scale_multiplier,
                    )

                seed_sections = _placed_sections(
                    matrix_at(1.0),
                    source_sections=source_sections,
                    source_min_z=min_z,
                    source_z_span=z_span,
                )
                if seed_sections is None:
                    continue
                _seed_angle, seed_long, seed_short = _principal_frame(
                    unary_union(seed_sections).convex_hull
                )
                if min(seed_long, seed_short) <= 1e-9:
                    continue
                scale_upper = max(
                    1.0,
                    legal_long / seed_long,
                    legal_short / seed_short,
                )
                scale_multiplier = (
                    _minimum_scale_multiplier(
                        matrix_at,
                        source_sections=source_sections,
                        legal_sections=legal_sections,
                        aggregate_target=aggregate_target,
                        source_min_z=min_z,
                        source_z_span=z_span,
                        scale_upper=scale_upper,
                    )
                    if minimum_aggregate_target_ratio >= 0.985
                    else _maximum_contained_scale_multiplier(
                        matrix_at,
                        source_sections=source_sections,
                        legal_sections=legal_sections,
                        source_min_z=min_z,
                        source_z_span=z_span,
                        scale_upper=scale_upper,
                    )
                )
                if scale_multiplier is None:
                    continue
                matrix = matrix_at(scale_multiplier)
                area_factor = scale_multiplier * scale_multiplier
                matrix_hash = _matrix_hash(matrix)
                if matrix_hash in seen_hashes:
                    continue
                seen_hashes.add(matrix_hash)
                screened = _screen_matrix(
                    matrix,
                    source_sections=source_sections,
                    legal_sections=legal_sections,
                    aggregate_target=aggregate_target,
                    minimum_aggregate_target_ratio=(
                        minimum_aggregate_target_ratio
                    ),
                    source_min_z=min_z,
                    source_z_span=z_span,
                    orientation_degrees=orientation_degrees,
                    anisotropy=anisotropy,
                    area_factor=area_factor,
                    shear_factor=shear_factor,
                    matrix_hash=matrix_hash,
                )
                if screened is not None:
                    alternatives.append(screened)
    alternatives.sort(key=lambda item: (
        item.profile_distortion,
        -item.minimum_floor_retention,
        -item.aggregate_retention,
        abs(item.aggregate_area_m2 - aggregate_target),
        item.matrix_hash,
    ))
    return tuple(alternatives)


def _pose_matrix(
    *,
    source_sections: tuple[Any, ...],
    legal_centroids: tuple[Any, ...],
    source_plan: Any,
    source_angle: float,
    target_angle: float,
    source_min_z: float,
    source_max_z: float,
    uniform_scale: float,
    anisotropy: float,
    shear_factor: float,
    scale_multiplier: float,
) -> Matrix4:
    source_z_span = source_max_z - source_min_z
    base = compose_matrix4(
        translation_matrix4((
            -source_plan.centroid.x,
            -source_plan.centroid.y,
            -source_min_z,
        )),
        rotation_matrix4((0.0, 0.0, -source_angle)),
        scale_matrix4((
            uniform_scale * anisotropy * scale_multiplier,
            uniform_scale / anisotropy * scale_multiplier,
            1.0 / source_z_span,
        )),
        rotation_matrix4((0.0, 0.0, target_angle)),
    )
    source_first = source_sections[0].centroid
    source_last = source_sections[-1].centroid
    base_first = transform_point3(
        base,
        (source_first.x, source_first.y, source_min_z),
    )
    base_last = transform_point3(
        base,
        (source_last.x, source_last.y, source_max_z),
    )
    source_delta = (
        base_last[0] - base_first[0],
        base_last[1] - base_first[1],
    )
    legal_delta = (
        legal_centroids[-1].x - legal_centroids[0].x,
        legal_centroids[-1].y - legal_centroids[0].y,
    )
    correction = (
        legal_delta[0] * shear_factor - source_delta[0],
        legal_delta[1] * shear_factor - source_delta[1],
    )
    shear = (
        (1.0, 0.0, correction[0], 0.0),
        (0.0, 1.0, correction[1], 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
    residuals: list[tuple[float, float]] = []
    for floor_index, (source_section, legal_centroid) in enumerate(zip(
        source_sections,
        legal_centroids,
    )):
        normalized_z = (floor_index + 0.5) / len(legal_centroids)
        source_z = source_min_z + source_z_span * normalized_z
        source_centroid = source_section.centroid
        placed_centroid = transform_point3(
            base,
            (source_centroid.x, source_centroid.y, source_z),
        )
        residuals.append((
            legal_centroid.x
            - placed_centroid[0]
            - correction[0] * normalized_z,
            legal_centroid.y
            - placed_centroid[1]
            - correction[1] * normalized_z,
        ))
    centroid_residual = (
        sum(value[0] for value in residuals) / len(residuals),
        sum(value[1] for value in residuals) / len(residuals),
    )
    return compose_matrix4(
        base,
        shear,
        translation_matrix4((
            centroid_residual[0],
            centroid_residual[1],
            0.0,
        )),
    )


def _placed_sections(
    matrix: Matrix4,
    *,
    source_sections: tuple[Any, ...],
    source_min_z: float,
    source_z_span: float,
) -> tuple[Any, ...] | None:
    placed = []
    floor_count = len(source_sections)
    for index, source_section in enumerate(source_sections):
        source_z = (
            source_min_z
            + source_z_span * (index + 0.5) / floor_count
        )
        transformed = affine_transform(
            source_section,
            (
                matrix[0][0],
                matrix[0][1],
                matrix[1][0],
                matrix[1][1],
                matrix[0][2] * source_z + matrix[0][3],
                matrix[1][2] * source_z + matrix[1][3],
            ),
        )
        if transformed.is_empty or float(transformed.area) <= 1e-9:
            return None
        placed.append(transformed)
    return tuple(placed)


def _minimum_scale_multiplier(
    matrix_at: Any,
    *,
    source_sections: tuple[Any, ...],
    legal_sections: tuple[Polygon, ...],
    aggregate_target: float,
    source_min_z: float,
    source_z_span: float,
    scale_upper: float,
) -> float | None:
    """Solve one aggregate-only 2D pose scale before bounded exact CSG."""

    required = min(
        sum(float(section.area) for section in legal_sections),
        aggregate_target / 0.985,
    )

    def achieved(scale_multiplier: float) -> float:
        placed = _placed_sections(
            matrix_at(scale_multiplier),
            source_sections=source_sections,
            source_min_z=source_min_z,
            source_z_span=source_z_span,
        )
        if placed is None:
            return 0.0
        return sum(
            float(source.intersection(legal).area)
            for source, legal in zip(placed, legal_sections)
        )

    sample_count = 12
    lower = 0.0
    upper = None
    for sample_index in range(1, sample_count + 1):
        probe = scale_upper * sample_index / sample_count
        if achieved(probe) + 1e-7 >= required:
            upper = probe
            break
        lower = probe
    if upper is None:
        return None
    for _iteration in range(12):
        probe = (lower + upper) / 2.0
        if achieved(probe) + 1e-7 >= required:
            upper = probe
        else:
            lower = probe
    return upper


def _maximum_contained_scale_multiplier(
    matrix_at: Any,
    *,
    source_sections: tuple[Any, ...],
    legal_sections: tuple[Polygon, ...],
    source_min_z: float,
    source_z_span: float,
    scale_upper: float,
) -> float | None:
    """Maximize one unchanged affine body inside every legal floor section."""

    def contained(scale_multiplier: float) -> bool:
        placed = _placed_sections(
            matrix_at(scale_multiplier),
            source_sections=source_sections,
            source_min_z=source_min_z,
            source_z_span=source_z_span,
        )
        return bool(
            placed is not None
            and all(
                legal.buffer(1e-7).covers(source)
                for source, legal in zip(placed, legal_sections)
            )
        )

    sample_count = 24
    best = None
    first_invalid_after_best = None
    for sample_index in range(1, sample_count + 1):
        probe = scale_upper * sample_index / sample_count
        if contained(probe):
            best = probe
        elif best is not None:
            first_invalid_after_best = probe
            break
    if best is None:
        return None
    if first_invalid_after_best is None:
        return best
    lower = best
    upper = first_invalid_after_best
    for _iteration in range(14):
        probe = (lower + upper) / 2.0
        if contained(probe):
            lower = probe
        else:
            upper = probe
    return lower


def _screen_matrix(
    matrix: Matrix4,
    *,
    source_sections: tuple[Any, ...],
    legal_sections: tuple[Polygon, ...],
    aggregate_target: float,
    minimum_aggregate_target_ratio: float,
    source_min_z: float,
    source_z_span: float,
    orientation_degrees: int,
    anisotropy: float,
    area_factor: float,
    shear_factor: float,
    matrix_hash: str,
) -> _ScreenedAlternative | None:
    preclip: list[float] = []
    clipped: list[float] = []
    retentions: list[float] = []
    floor_count = len(legal_sections)
    for index, (source_section, legal_section) in enumerate(zip(
        source_sections,
        legal_sections,
    )):
        normalized_z = (index + 0.5) / floor_count
        source_z = source_min_z + source_z_span * normalized_z
        transformed = affine_transform(
            source_section,
            (
                matrix[0][0],
                matrix[0][1],
                matrix[1][0],
                matrix[1][1],
                matrix[0][2] * source_z + matrix[0][3],
                matrix[1][2] * source_z + matrix[1][3],
            ),
        )
        clipped_section = transformed.intersection(legal_section)
        before = float(transformed.area)
        after = float(clipped_section.area)
        if (
            not isfinite(before)
            or not isfinite(after)
            or before <= 1e-9
            or after <= 1e-9
        ):
            return None
        preclip.append(before)
        clipped.append(after)
        retentions.append(after / before)
    aggregate = sum(clipped)
    if (
        aggregate + 1e-7
        < aggregate_target * minimum_aggregate_target_ratio
    ):
        return None
    return _ScreenedAlternative(
        matrix4=matrix,
        matrix_hash=matrix_hash,
        preclip_areas_m2=tuple(preclip),
        clipped_areas_m2=tuple(clipped),
        profile_distortion=_profile_distortion(preclip, clipped),
        aggregate_retention=sum(clipped) / max(sum(preclip), 1e-9),
        minimum_floor_retention=min(retentions),
        aggregate_area_m2=aggregate,
        orientation_degrees=orientation_degrees,
        anisotropy=round(anisotropy, 8),
        area_factor=area_factor,
        shear_factor=shear_factor,
    )


def _waterfill_plan_area(
    legal_caps: tuple[float, ...],
    aggregate_target: float,
) -> float:
    lower = 0.0
    upper = max(legal_caps)
    for _iteration in range(48):
        probe = (lower + upper) / 2.0
        achieved = sum(min(probe, cap) for cap in legal_caps)
        if achieved < aggregate_target:
            lower = probe
        else:
            upper = probe
    return upper


def _conservative_band_profile(
    authored: CompilationResult,
    matrix: Matrix4,
    final: CompilationResult,
    *,
    floor_count: int,
) -> tuple[tuple[float, ...], tuple[float, ...]] | None:
    """Measure the full band silhouettes used by the downstream source proxy."""

    bounds = (authored.metrics or {}).get("bounds") or ()
    if len(bounds) != 2:
        return None
    source_min_z = float(bounds[0][2])
    source_span = float(bounds[1][2]) - source_min_z
    if source_span <= 1e-9:
        return None
    preclip: list[float] = []
    clipped: list[float] = []
    for floor_index in range(floor_count):
        source_polygons = []
        final_polygons = []
        for offset in (0.03, 0.5, 0.97):
            normalized_z = (floor_index + offset) / floor_count
            source_z = source_min_z + source_span * normalized_z
            source_section = _mesh_section_polygon(authored, source_z)
            final_section = _mesh_section_polygon(final, normalized_z)
            if source_section is None or final_section is None:
                return None
            source_polygons.append(affine_transform(
                source_section,
                (
                    matrix[0][0],
                    matrix[0][1],
                    matrix[1][0],
                    matrix[1][1],
                    matrix[0][2] * source_z + matrix[0][3],
                    matrix[1][2] * source_z + matrix[1][3],
                ),
            ))
            final_polygons.append(final_section)
        source_union = unary_union(source_polygons)
        final_union = unary_union(final_polygons)
        before = float(source_union.area)
        after = float(final_union.area)
        if min(before, after) <= 1e-9:
            return None
        preclip.append(before)
        clipped.append(after)
    return tuple(preclip), tuple(clipped)


def _profile_distortion(
    authored_areas: Any,
    final_areas: Any,
) -> float:
    authored = tuple(float(value) for value in authored_areas)
    final = tuple(float(value) for value in final_areas)
    authored_total = max(sum(authored), 1e-9)
    final_total = max(sum(final), 1e-9)
    return sum(
        abs(
            authored_area / authored_total
            - final_area / final_total
        )
        for authored_area, final_area in zip(authored, final)
    )


def _principal_frame(polygon: Any) -> tuple[float, float, float]:
    rectangle = polygon.minimum_rotated_rectangle
    coordinates = list(rectangle.exterior.coords)[:4]
    edges = [
        (
            sqrt(
                (coordinates[(index + 1) % 4][0] - coordinates[index][0]) ** 2
                + (coordinates[(index + 1) % 4][1] - coordinates[index][1]) ** 2
            ),
            coordinates[index],
            coordinates[(index + 1) % 4],
        )
        for index in range(4)
    ]
    longest = max(edges, key=lambda edge: edge[0])
    shortest = min(edge[0] for edge in edges)
    angle = degrees(atan2(
        longest[2][1] - longest[1][1],
        longest[2][0] - longest[1][0],
    ))
    return angle, longest[0], shortest


def _matrix_hash(matrix: Matrix4) -> str:
    payload = [
        [round(float(value), 12) for value in row]
        for row in matrix
    ]
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _unique_floats(values: tuple[float, ...]) -> tuple[float, ...]:
    result: list[float] = []
    for value in values:
        if not any(abs(value - existing) <= 1e-8 for existing in result):
            result.append(value)
    return tuple(result)


def _exact_shortlist(
    alternatives: tuple[_ScreenedAlternative, ...],
    *,
    limit: int,
) -> tuple[_ScreenedAlternative, ...]:
    """Cover distinct axis responses without compiling 180-degree twins."""

    groups: dict[float, list[_ScreenedAlternative]] = {}
    for alternative in alternatives:
        group = groups.setdefault(alternative.anisotropy, [])
        if any(
            existing.shear_factor == alternative.shear_factor
            for existing in group
        ):
            continue
        group.append(alternative)
    selected: list[_ScreenedAlternative] = []
    for records in groups.values():
        selected.append(records[0])
        if len(selected) >= limit:
            return tuple(selected)
    for anisotropy in sorted(groups):
        records = groups[anisotropy]
        if len(records) > 1:
            # Spend the second exact slot on the next-best screened response,
            # beginning with the strongest distinct axis response rather than
            # a numerically different 180-degree twin of the same pose.
            selected.append(records[1])
        if len(selected) >= limit:
            return tuple(selected)
    for records in groups.values():
        for record in records[2:]:
            selected.append(record)
            if len(selected) >= limit:
                return tuple(selected)
    return tuple(selected)


__all__ = [
    "LegalFieldAffineSelection",
    "is_intentional_floorwise_stepped_program",
    "select_legal_field_affine_projection",
]
