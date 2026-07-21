"""Project accepted BOOK source masses through legal and parking hard gates.

This diagnostic never regenerates a replacement design.  It clips the exact
accepted SourceVolume graph by the PNU-derived buildable/sunlight envelope,
measures source retention, recomputes BCR/FAR/height, and then asks the
structured parking-rule and deterministic layout solvers to evaluate that
same projected footprint.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Iterable

from shapely.affinity import scale, translate
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from design.maas.legal_envelope import build_legal_envelope
from design.maas.geometry_language.execution_passport import enrich_mass_execution_passport
from design.maas.parking_requirements import (
    load_parking_requirement_rules,
    resolve_candidate_parking_requirement,
)
from design.maas.parking_strategy import infer_parking_strategy
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.maas.source_geometry.polygon_quality import repair_source_polygon
from design.services.site_geometry import wgs84_to_utm


@dataclass(frozen=True)
class LegalGenerationContext:
    """The legal domain supplied to generation, not a post-selection repair."""

    envelope: Any
    generation_site: Polygon
    sunlight_ring: tuple[tuple[float, float, float], ...]
    evidence: dict[str, Any]


def generation_site_at_height(
    context: LegalGenerationContext,
    height_m: float,
) -> Polygon | None:
    """Return the legal horizontal domain available at a requested height."""
    if not context.sunlight_ring:
        return context.generation_site
    sunlight_allowed = _clip_ring_by_min_height(list(context.sunlight_ring), height_m)
    if sunlight_allowed is None:
        return None
    return repair_source_polygon(
        context.generation_site.intersection(sunlight_allowed),
        minimum_area=1.0,
    )


def inscribed_span_host(legal_section: Polygon) -> Polygon:
    """Find a clean oriented span host fully inside an irregular legal field.

    Long-span program graphs need a coherent structural bay.  This bounded
    search derives one from the legal polygon itself; it contains no parcel
    coordinate or finished-building template.
    """
    rectangle = legal_section.minimum_rotated_rectangle
    origin = rectangle.centroid
    best: Polygon | None = None
    for x_step in range(20, 4, -1):
        for y_step in range(20, 4, -1):
            candidate = scale(
                rectangle,
                xfact=x_step / 20.0,
                yfact=y_step / 20.0,
                origin=origin,
            )
            if legal_section.covers(candidate) and (best is None or candidate.area > best.area):
                best = candidate
    repaired = repair_source_polygon(best, minimum_area=4.0) if best is not None else None
    return repaired if repaired is not None else legal_section


def fit_source_to_sunlight_field(
    source: SourceMass,
    context: LegalGenerationContext,
    *,
    height_m: float,
    floors: int,
) -> SourceMass:
    """Apply one bounded whole-graph fit before program/portfolio selection.

    Volumes and renderer surfaces share the same scale, while translation is
    represented by the transformed source centroid.  Program roles and BOOK
    topology are therefore preserved and re-evaluated after the modifier.
    """
    if not context.sunlight_ring or not source.volumes:
        return source
    source_union = unary_union([volume.footprint for volume in source.volumes])
    if source_union.is_empty:
        return source
    origin = source_union.centroid
    highest_allowed = generation_site_at_height(context, height_m)
    if highest_allowed is None:
        return source
    target = highest_allowed.centroid
    target_dx = float(target.x - origin.x)
    target_dy = float(target.y - origin.y)
    best = source
    best_score = _source_retention_proxy(source.volumes, context, height_m=height_m, floors=floors)
    best_transform = (1.0, 0.0, 0.0)
    for factor in (1.0, 0.96, 0.92, 0.88, 0.84):
        for shift_fraction in (0.0, 0.25, 0.50, 0.75, 1.0):
            dx = target_dx * shift_fraction
            dy = target_dy * shift_fraction
            volumes = tuple(SourceVolume(
                role=volume.role,
                footprint=translate(
                    scale(volume.footprint, xfact=factor, yfact=factor, origin=origin),
                    xoff=dx,
                    yoff=dy,
                ),
                bottom_fraction=volume.bottom_fraction,
                top_fraction=volume.top_fraction,
                verb=volume.verb,
            ) for volume in source.volumes)
            transformed_union = unary_union([volume.footprint for volume in volumes])
            if not context.generation_site.covers(transformed_union):
                continue
            score = _source_retention_proxy(volumes, context, height_m=height_m, floors=floors)
            if (score, factor, -shift_fraction) <= (
                best_score,
                best_transform[0],
                -((abs(best_transform[1]) + abs(best_transform[2])) / max(abs(target_dx) + abs(target_dy), 1e-9)),
            ):
                continue
            footprint = translate(
                scale(source.footprint, xfact=factor, yfact=factor, origin=origin),
                xoff=dx,
                yoff=dy,
            )
            upper = (
                translate(
                    scale(source.upper_footprint, xfact=factor, yfact=factor, origin=origin),
                    xoff=dx,
                    yoff=dy,
                )
                if source.upper_footprint is not None
                else None
            )
            surfaces = tuple(replace(
                surface,
                vertices_m=tuple((x * factor, y * factor, z) for x, y, z in surface.vertices_m),
            ) for surface in source.surfaces)
            best = replace(
                source,
                footprint=footprint,
                upper_footprint=upper,
                volumes=volumes,
                surfaces=surfaces,
            )
            best_score = score
            best_transform = (factor, dx, dy)
    if best is source:
        return source
    metadata = dict(best.metadata)
    evidence = dict(metadata.get("legal_generation_context_evidence") or {})
    evidence.update({
        "legal_field_fit_status": "materialized",
        "legal_field_fit_operator": "bounded_uniform_scale_translate",
        "legal_field_fit_scale": round(best_transform[0], 4),
        "legal_field_fit_translation_m": [round(best_transform[1], 3), round(best_transform[2], 3)],
        "predicted_volume_retention": round(best_score, 4),
    })
    metadata["legal_generation_context_evidence"] = evidence
    return replace(best, metadata=metadata)


def _source_retention_proxy(
    volumes: tuple[SourceVolume, ...],
    context: LegalGenerationContext,
    *,
    height_m: float,
    floors: int,
) -> float:
    source_total = projected_total = 0.0
    floor_step = height_m / max(1, floors)
    for volume in volumes:
        bottom = height_m * float(volume.bottom_fraction)
        top = height_m * float(volume.top_fraction)
        boundaries = [bottom]
        boundaries.extend(
            floor_step * index
            for index in range(1, max(1, floors) + 1)
            if bottom + 1e-6 < floor_step * index < top - 1e-6
        )
        boundaries.append(top)
        for slice_bottom, slice_top in zip(boundaries, boundaries[1:]):
            band_height = max(0.0, slice_top - slice_bottom)
            if band_height <= 1e-6:
                continue
            source_total += float(volume.footprint.area) * band_height
            allowed = context.generation_site
            sunlight_allowed = _clip_ring_by_min_height(list(context.sunlight_ring), slice_top)
            if sunlight_allowed is not None:
                allowed = allowed.intersection(sunlight_allowed)
            projected_total += float(volume.footprint.intersection(allowed).area) * band_height
    return projected_total / source_total if source_total > 0 else 0.0


def build_legal_generation_context(
    *,
    site_local_utm: Polygon,
    site_origin_utm: tuple[float, float],
    building_type: str,
    constraints: list[dict[str, Any]],
    sunlight_envelope: dict[str, Any] | None,
) -> LegalGenerationContext:
    """Materialize the exact envelope used by both generation and hard gates.

    The horizontal buildable footprint is safe at every height.  The sloped
    sunlight field remains height-dependent and is therefore evaluated on the
    compiled SourceVolume graph rather than flattened into one tiny maximum-
    height footprint.
    """
    envelope = build_legal_envelope(
        site_utm=site_local_utm,
        constraints=constraints,
        building_type=building_type,
        sunlight_envelope=None,
    )
    buildable = repair_source_polygon(envelope.buildable_footprint, minimum_area=1.0)
    if buildable is None:
        buildable = repair_source_polygon(site_local_utm, minimum_area=1.0)
    if buildable is None:
        raise ValueError("legal generation context has no buildable footprint")
    sunlight_ring = tuple(_local_sunlight_ring(sunlight_envelope, site_origin_utm))
    return LegalGenerationContext(
        envelope=envelope,
        generation_site=buildable,
        sunlight_ring=sunlight_ring,
        evidence={
            "schema_version": "arr.maas.legal_generation_context.v1",
            "status": "materialized",
            "generation_precedes_selection": True,
            "original_site_area_m2": round(float(site_local_utm.area), 3),
            "generation_site_area_m2": round(float(buildable.area), 3),
            "sunlight_field_status": "materialized" if sunlight_ring else "not_available",
            "bcr_limit_pct": envelope.bcr_limit,
            "far_limit_pct": envelope.far_limit,
            "height_limit_m": envelope.height_limit,
        },
    )


def evaluate_accepted_sources_downstream(
    candidates: Iterable[Any],
    *,
    site_local_utm: Polygon,
    site_origin_utm: tuple[float, float],
    pnu: str,
    building_type: str,
    height_m: float,
    floors: int,
    constraints: list[dict[str, Any]],
    regulation_evidence: dict[str, Any],
    sunlight_envelope: dict[str, Any] | None,
    parking_options: dict[str, Any] | None = None,
    generation_context: LegalGenerationContext | None = None,
) -> dict[str, Any]:
    items = tuple(candidates)
    context = generation_context or build_legal_generation_context(
        site_local_utm=site_local_utm,
        site_origin_utm=site_origin_utm,
        building_type=building_type,
        constraints=constraints,
        sunlight_envelope=sunlight_envelope,
    )
    envelope = context.envelope
    parking_rules = load_parking_requirement_rules(options=parking_options)
    rules = parking_rules.get("rules") if parking_rules.get("status") == "loaded" else None
    sunlight_ring = list(context.sunlight_ring)
    rows = []
    for candidate in items:
        rows.append(_evaluate_candidate(
            candidate,
            site_local_utm=site_local_utm,
            envelope=envelope,
            sunlight_ring=sunlight_ring,
            pnu=pnu,
            building_type=building_type,
            height_m=height_m,
            floors=floors,
            rules=rules,
            parking_options=parking_options,
        ))
    legal_failures = Counter(
        reason
        for row in rows
        for reason in row["legal_projection"]["failure_reasons"]
    )
    parking_failures = Counter(
        reason
        for row in rows
        for reason in row["parking_hard_gate"]["failure_reasons"]
    )
    geometry_failures = Counter(
        reason
        for row in rows
        for reason in row["legal_projection"]["geometry_failure_reasons"]
    )
    retentions = [float(row["legal_projection"]["volume_retention"]) for row in rows]
    return {
        "schema_version": "arr.maas.book_downstream_hard_gate.v1",
        "status": "pass" if rows and all(row["combined_hard_pass"] for row in rows) else "fail",
        "same_accepted_source": True,
        "generation_context": context.evidence,
        "candidate_count": len(rows),
        "legal_hard_pass_count": sum(row["legal_projection"]["hard_pass"] for row in rows),
        "geometry_retention_pass_count": sum(row["legal_projection"]["geometry_retention_pass"] for row in rows),
        "parking_hard_pass_count": sum(row["parking_hard_gate"]["hard_pass"] for row in rows),
        "combined_hard_pass_count": sum(row["combined_hard_pass"] for row in rows),
        "mean_volume_retention": round(sum(retentions) / len(retentions), 4) if retentions else 0.0,
        "minimum_volume_retention": round(min(retentions), 4) if retentions else 0.0,
        "legal_failure_reason_counts": dict(sorted(legal_failures.items())),
        "geometry_failure_reason_counts": dict(sorted(geometry_failures.items())),
        "parking_failure_reason_counts": dict(sorted(parking_failures.items())),
        "legal_context": {
            "constraint_source": "live_pnu_zone_regulation_calculator",
            "constraints": constraints,
            "regulation_evidence": regulation_evidence,
            "bcr_limit_pct": envelope.bcr_limit,
            "far_limit_pct": envelope.far_limit,
            "height_limit_m": envelope.height_limit,
            "buildable_footprint_area_m2": round(float(envelope.buildable_footprint.area), 3) if envelope.buildable_footprint is not None else 0.0,
            "sunlight_envelope_status": "materialized" if sunlight_ring else "not_available",
        },
        "parking_rule_source": {
            "status": parking_rules.get("status"),
            "source": parking_rules.get("source"),
            "graph_status": parking_rules.get("graph_status"),
            "reason": parking_rules.get("reason") or parking_rules.get("graph_reason"),
        },
        "rows": rows,
    }


def _evaluate_candidate(
    candidate: Any,
    *,
    site_local_utm: Polygon,
    envelope: Any,
    sunlight_ring: list[tuple[float, float, float]],
    pnu: str,
    building_type: str,
    height_m: float,
    floors: int,
    rules: dict[str, Any] | None,
    parking_options: dict[str, Any] | None,
) -> dict[str, Any]:
    source = candidate.source
    projected: list[SourceVolume] = []
    source_volume_total = projected_volume_total = 0.0
    weighted_intersection = weighted_union = 0.0
    clipped_volume_count = 0
    floor_step = height_m / max(1, floors)
    for volume in source.volumes:
        bottom_height = height_m * float(volume.bottom_fraction)
        top_height = height_m * float(volume.top_fraction)
        boundaries = [bottom_height]
        boundaries.extend(
            floor_step * floor_index
            for floor_index in range(1, max(1, floors) + 1)
            if bottom_height + 1e-6 < floor_step * floor_index < top_height - 1e-6
        )
        boundaries.append(top_height)
        original_clipped = False
        slice_count = max(0, len(boundaries) - 1)
        for slice_index, (slice_bottom, slice_top) in enumerate(zip(boundaries, boundaries[1:])):
            band_height = max(0.0, slice_top - slice_bottom)
            if band_height <= 1e-6:
                continue
            source_measure = float(volume.footprint.area) * band_height
            source_volume_total += source_measure
            allowed = envelope.buildable_footprint
            if allowed is not None and sunlight_ring:
                sunlight_allowed = _clip_ring_by_min_height(sunlight_ring, slice_top)
                allowed = allowed.intersection(sunlight_allowed) if sunlight_allowed is not None else None
            clipped = None if allowed is None else repair_source_polygon(
                volume.footprint.intersection(allowed),
                minimum_area=1.0,
            )
            if clipped is None:
                original_clipped = True
                continue
            if clipped.area < volume.footprint.area - 0.1:
                original_clipped = True
            projected_measure = float(clipped.area) * band_height
            projected_volume_total += projected_measure
            intersection = float(volume.footprint.intersection(clipped).area)
            union = float(volume.footprint.union(clipped).area)
            weighted_intersection += intersection * band_height
            weighted_union += union * band_height
            projected.append(SourceVolume(
                role=(f"{volume.role}__legal_band_{slice_index}" if slice_count > 1 else volume.role),
                footprint=clipped,
                bottom_fraction=slice_bottom / max(height_m, 1e-9),
                top_fraction=slice_top / max(height_m, 1e-9),
                verb=volume.verb,
            ))
        if original_clipped:
            clipped_volume_count += 1

    original_metrics = _metrics(source.volumes, site_local_utm, height_m=height_m, floors=floors)
    projected_metrics = _metrics(tuple(projected), site_local_utm, height_m=height_m, floors=floors)
    retention = projected_volume_total / source_volume_total if source_volume_total > 0 else 0.0
    weighted_iou = weighted_intersection / weighted_union if weighted_union > 0 else 0.0
    legal_failures = []
    if not projected:
        legal_failures.append("empty_after_legal_projection")
    if projected_metrics["bcr_pct"] > envelope.bcr_limit + 0.1:
        legal_failures.append("bcr_limit_exceeded")
    if projected_metrics["far_pct"] > envelope.far_limit + 0.1:
        legal_failures.append("far_limit_exceeded")
    if projected_metrics["height_m"] > envelope.height_limit + 0.1:
        legal_failures.append("height_limit_exceeded")
    landscaping_limit = _constraint_limit(envelope.outputs_def, "landscaping_pct")
    if landscaping_limit is not None and projected_metrics["open_pct"] < landscaping_limit - 0.1:
        legal_failures.append("landscaping_minimum_not_met")
    geometry_retention_pass = retention >= 0.80 and weighted_iou >= 0.75
    geometry_failures = []
    if retention < 0.80:
        geometry_failures.append("source_volume_retention_below_80_percent")
    if weighted_iou < 0.75:
        geometry_failures.append("weighted_plan_iou_below_75_percent")

    ground = _ground_footprint(tuple(projected))
    requirement = resolve_candidate_parking_requirement(
        pnu=pnu,
        building_type=building_type,
        facility_area_m2=projected_metrics["floor_area_m2"],
        options=parking_options,
        rules=rules,
    )
    parking_props = {
        "footprint_area": projected_metrics["footprint_area_m2"],
        "floor_area": projected_metrics["floor_area_m2"],
        "num_floors": floors,
        "height": height_m,
        "bcr": projected_metrics["bcr_pct"],
        "required_parking_spaces": requirement.get("required_spaces"),
        "required_accessible_parking_spaces": (requirement.get("accessible") or {}).get("accessible_min") or 0,
    }
    strategy = infer_parking_strategy(
        parking_props,
        site_area_m2=float(site_local_utm.area),
        building_type=building_type,
        footprint_utm=ground,
        site_utm=site_local_utm,
        road_context=(parking_options or {}).get("road_context"),
    )
    layout = strategy.get("layout_candidate") if isinstance(strategy.get("layout_candidate"), dict) else {}
    required = requirement.get("required_spaces")
    provided = int(layout.get("provided_spaces") or 0)
    parking_failures = []
    if str(requirement.get("status") or "") not in {"computed", "computed_estimate"} or not isinstance(required, int):
        parking_failures.append("parking_requirement_unresolved")
    if isinstance(required, int) and required > 0:
        if layout.get("status") != "pass":
            parking_failures.append(f"parking_layout_{layout.get('status') or 'missing'}")
        if provided < required:
            parking_failures.append("parking_spaces_below_required")

    legal_hard_pass = not legal_failures
    parking_hard_pass = not parking_failures
    legal_projection = {
        "evaluated": True,
        "hard_pass": legal_hard_pass,
        "failure_reasons": legal_failures,
        "source_volume_count": len(source.volumes),
        "projected_volume_count": len(projected),
        "clipped_volume_count": clipped_volume_count,
        "volume_retention": round(retention, 4),
        "weighted_plan_iou": round(weighted_iou, 4),
        "geometry_retention_pass": geometry_retention_pass,
        "geometry_failure_reasons": geometry_failures,
    }
    parking_hard_gate = {
        "evaluated": True,
        "hard_pass": parking_hard_pass,
        "failure_reasons": parking_failures,
        "requirement": requirement,
        "selected_strategy": strategy.get("selected_strategy"),
        "layout_status": layout.get("status"),
        "required_spaces": required,
        "provided_spaces": provided,
    }
    initial_passport = source.metadata.get("mass_execution_passport") or (
        source.metadata.get("geometry_program_compilation") or {}
    ).get("execution_passport") or {}
    mass_execution_passport = (
        enrich_mass_execution_passport(
            initial_passport,
            downstream_evidence={
                "site": {
                    **dict(source.metadata.get("legal_generation_context_evidence") or {}),
                    "status": "passed",
                    "pnu": pnu,
                },
                "capacity": {
                    **dict(source.metadata.get("capacity_alternative_projection") or {}),
                    "measurement": dict(source.metadata.get("source_capacity_measurement") or {}),
                    "evaluated": bool(
                        source.metadata.get("capacity_alternative_projection")
                        or source.metadata.get("source_capacity_measurement")
                    ),
                    "hard_pass": (source.metadata.get("source_capacity_measurement") or {}).get("hard_pass"),
                },
                "law": legal_projection,
                "parking": parking_hard_gate,
                "program_fit": dict(source.metadata.get("program_massing_evidence") or {}),
            },
        )
        if initial_passport
        else {}
    )
    return {
        "variant_id": str(candidate.feature.get("properties", {}).get("variant_id") or candidate.sequence.name),
        "source_sequence": candidate.sequence.name,
        "book_principle_id": candidate.principle_id,
        "book_scope": str((source.metadata.get("program_book_projection_evidence") or {}).get("scope", {}).get("base_volume_label") or "1/1"),
        "generation_host_mode": str((
            source.metadata.get("legal_generation_context_evidence") or {}
        ).get("generation_host_mode") or "unconstrained_site"),
        "legal_generation_context_evidence": source.metadata.get("legal_generation_context_evidence") or {},
        "original_metrics": original_metrics,
        "projected_metrics": projected_metrics,
        "legal_projection": legal_projection,
        "parking_hard_gate": parking_hard_gate,
        "mass_execution_passport": mass_execution_passport,
        "combined_hard_pass": bool(legal_hard_pass and geometry_retention_pass and parking_hard_pass),
    }


def _metrics(volumes: tuple[SourceVolume, ...], site: Polygon, *, height_m: float, floors: int) -> dict[str, float]:
    ground = _ground_footprint(volumes)
    footprint_area = float(ground.area) if ground is not None else 0.0
    floor_area = 0.0
    for floor in range(max(1, floors)):
        fraction = (floor + 0.5) / max(1, floors)
        active = [
            volume.footprint
            for volume in volumes
            if float(volume.bottom_fraction) <= fraction < float(volume.top_fraction)
        ]
        if active:
            floor_area += float(unary_union(active).area)
    site_area = max(float(site.area), 1e-9)
    maximum_height = max((height_m * float(volume.top_fraction) for volume in volumes), default=0.0)
    return {
        "footprint_area_m2": round(footprint_area, 3),
        "floor_area_m2": round(floor_area, 3),
        "bcr_pct": round(footprint_area / site_area * 100.0, 3),
        "far_pct": round(floor_area / site_area * 100.0, 3),
        "height_m": round(maximum_height, 3),
        "open_pct": round(max(0.0, site_area - footprint_area) / site_area * 100.0, 3),
    }


def _ground_footprint(volumes: tuple[SourceVolume, ...]) -> Polygon | None:
    grounded = [volume.footprint for volume in volumes if float(volume.bottom_fraction) <= 0.01]
    if not grounded:
        grounded = [volume.footprint for volume in volumes]
    return repair_source_polygon(unary_union(grounded), minimum_area=1.0) if grounded else None


def _constraint_limit(outputs: list[dict[str, Any]], name: str) -> float | None:
    for item in outputs:
        if item.get("type") == "Constraint" and item.get("name") == name:
            try:
                return float(item.get("val"))
            except (TypeError, ValueError):
                return None
    return None


def _local_sunlight_ring(
    sunlight_envelope: dict[str, Any] | None,
    origin_utm: tuple[float, float],
) -> list[tuple[float, float, float]]:
    slanted = (sunlight_envelope or {}).get("slanted_polygons") or []
    corners = (slanted[0].get("corners") or []) if slanted else []
    result = []
    for corner in corners:
        if not isinstance(corner, (list, tuple)) or len(corner) < 3:
            continue
        try:
            point = wgs84_to_utm(Point(float(corner[0]), float(corner[1])))
            result.append((point.x - origin_utm[0], point.y - origin_utm[1], float(corner[2])))
        except (TypeError, ValueError):
            continue
    if len(result) >= 2 and result[0][:2] == result[-1][:2]:
        result.pop()
    return result


def _clip_ring_by_min_height(
    ring: list[tuple[float, float, float]],
    height_m: float,
) -> Polygon | None:
    if len(ring) < 3:
        return None

    def inside(point: tuple[float, float, float]) -> bool:
        return point[2] >= height_m - 1e-6

    def crossing(left: tuple[float, float, float], right: tuple[float, float, float]):
        denominator = right[2] - left[2]
        if abs(denominator) < 1e-9:
            return right
        amount = (height_m - left[2]) / denominator
        amount = max(0.0, min(1.0, amount))
        return (
            left[0] + (right[0] - left[0]) * amount,
            left[1] + (right[1] - left[1]) * amount,
            height_m,
        )

    output = []
    previous = ring[-1]
    previous_inside = inside(previous)
    for current in ring:
        current_inside = inside(current)
        if current_inside:
            if not previous_inside:
                output.append(crossing(previous, current))
            output.append(current)
        elif previous_inside:
            output.append(crossing(previous, current))
        previous, previous_inside = current, current_inside
    if len(output) < 3:
        return None
    return repair_source_polygon(Polygon([(x, y) for x, y, _height in output]), minimum_area=1.0)


__all__ = [
    "LegalGenerationContext",
    "build_legal_generation_context",
    "generation_site_at_height",
    "inscribed_span_host",
    "fit_source_to_sunlight_field",
    "evaluate_accepted_sources_downstream",
]
