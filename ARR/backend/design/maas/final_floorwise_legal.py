"""Fail-closed floorwise legality for MAAS review candidates."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any

from shapely.geometry import MultiPolygon, mapping
from shapely.ops import unary_union

from design.maas.floor_groups import build_floor_groups
from design.maas.legal_envelope import (
    LegalEnvelope,
    allowed_footprint_at_height,
    failed_constraint_metrics,
)
from design.maas.morphology_operators import largest_polygon
from design.services.site_geometry import geojson_to_polygon, utm_to_wgs84, wgs84_to_utm


_AREA_TOLERANCE_M2 = 0.05
_MIN_OCCUPIED_AREA_M2 = 1.0


@dataclass(frozen=True)
class FloorwiseLegalResult:
    feature: dict[str, Any] | None
    evidence: dict[str, Any]


def _polygon(value: Any):
    if not isinstance(value, dict):
        return None
    try:
        polygon = wgs84_to_utm(geojson_to_polygon(value))
    except Exception:
        return None
    if polygon.is_empty:
        return None
    if isinstance(polygon, MultiPolygon):
        polygon = largest_polygon(polygon)
    return polygon if polygon.area >= _MIN_OCCUPIED_AREA_M2 else None


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _canonical_volumes(feature: dict[str, Any]) -> list[dict[str, Any]]:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
    volumes = props.get("mass_volumes")
    if not isinstance(volumes, list):
        volumes = model.get("volumes")
    return [item for item in volumes or [] if isinstance(item, dict)]


def _explicit_plates(feature: dict[str, Any]) -> list[dict[str, Any]]:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
    plates = props.get("floor_plates")
    if not isinstance(plates, list):
        plates = model.get("floor_plates")
    return [item for item in plates or [] if isinstance(item, dict)]


def _occupied_sections_from_volumes(
    volumes: list[dict[str, Any]],
    *,
    floor_height: float,
) -> tuple[list[tuple[int, float, Any, list[str]]], list[str]]:
    parsed: list[tuple[float, float, Any, str]] = []
    failed_checks: list[str] = []
    for index, volume in enumerate(volumes):
        bottom = _float(volume.get("bottom_height"))
        top = _float(volume.get("top_height"))
        polygon = _polygon(volume.get("geometry"))
        if bottom is None or top is None or top <= bottom or polygon is None:
            failed_checks.append(f"invalid_mass_volume:{index}")
            continue
        parsed.append((bottom, top, polygon, str(volume.get("role") or "morphology_volume")))
    if failed_checks or not parsed:
        return [], failed_checks or ["missing_mass_volume_sections"]

    maximum_height = max(top for _, top, _, _ in parsed)
    floor_count = max(1, int(math.ceil(maximum_height / floor_height - 1e-9)))
    sections: list[tuple[int, float, Any, list[str]]] = []
    for floor in range(1, floor_count + 1):
        top_height = floor * floor_height
        active = [
            (polygon, role)
            for bottom, top, polygon, role in parsed
            if bottom < top_height + 1e-7 and top_height <= top + 1e-7
        ]
        if not active:
            if sections:
                break
            return [], [f"no_occupied_section_at_floor:{floor}"]
        occupied = unary_union([polygon for polygon, _ in active])
        if isinstance(occupied, MultiPolygon):
            occupied = largest_polygon(occupied)
        sections.append((floor, top_height, occupied, sorted({role for _, role in active})))
    return sections, []


def _occupied_sections_from_plates(
    plates: list[dict[str, Any]],
) -> tuple[list[tuple[int, float, Any, list[str]]], list[str]]:
    sections: list[tuple[int, float, Any, list[str]]] = []
    failed_checks: list[str] = []
    for index, plate in enumerate(plates):
        floor = int(plate.get("floor") or index + 1)
        top_height = _float(plate.get("top_height"))
        polygon = _polygon(plate.get("geometry"))
        if top_height is None or top_height <= 0 or polygon is None:
            failed_checks.append(f"invalid_floor_plate:{index}")
            continue
        sections.append((floor, top_height, polygon, ["floor_plate"]))
    if failed_checks or not sections:
        return [], failed_checks or ["missing_floor_plates"]
    sections.sort(key=lambda item: (item[1], item[0]))
    return sections, []


def _reject(
    *,
    source: str,
    failed_checks: list[str],
    checked_floor_count: int,
    original_height_m: float,
) -> FloorwiseLegalResult:
    return FloorwiseLegalResult(
        feature=None,
        evidence={
            "schema_version": "arr.maas.floorwise_legal.v1",
            "status": "fail",
            "source": source,
            "failed_checks": failed_checks,
            "checked_floor_count": checked_floor_count,
            "checked_mass_volume_count": 0,
            "original_height_m": round(original_height_m, 2),
        },
    )


def revalidate_final_floorwise_feature(
    feature: dict[str, Any],
    *,
    envelope: LegalEnvelope,
    sunlight_envelope: dict[str, Any] | None,
    building_type: str,
) -> FloorwiseLegalResult:
    """Return a feature whose canonical occupied geometry is legal per floor.

    Existing explicit floor plates are measured directly. Candidates without
    plates are sectioned from their canonical mass-volume bands. Every occupied
    section is clipped to the height-dependent legal footprint and rebound as
    both the explicit plates and canonical mass volumes used downstream.
    """
    candidate = copy.deepcopy(feature)
    props = candidate.get("properties") if isinstance(candidate.get("properties"), dict) else {}
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else {}
    floor_height = _float(props.get("floor_height")) or float(envelope.floor_height)
    if floor_height <= 0:
        return _reject(
            source="unknown",
            failed_checks=["invalid_floor_height"],
            checked_floor_count=0,
            original_height_m=_float(props.get("height")) or 0.0,
        )

    original_height = _float(props.get("height")) or 0.0
    original_plates = _explicit_plates(candidate)
    original_volumes = _canonical_volumes(candidate)
    if original_plates:
        source = "exact_floor_plates"
        sections, failed_checks = _occupied_sections_from_plates(original_plates)
    else:
        source = "derived_mass_volume_sections"
        sections, failed_checks = _occupied_sections_from_volumes(
            original_volumes,
            floor_height=floor_height,
        )
    if failed_checks:
        return _reject(
            source=source,
            failed_checks=failed_checks,
            checked_floor_count=0,
            original_height_m=original_height,
        )

    repaired = False
    truncation_reasons: list[str] = []
    plates: list[dict[str, Any]] = []
    canonical_volumes: list[dict[str, Any]] = []
    previous_top = 0.0
    for floor, top_height, occupied, roles in sections:
        if top_height > envelope.height_limit + 0.1:
            repaired = True
            truncation_reasons.append(f"height_limit_at_floor:{floor}")
            break
        allowed = allowed_footprint_at_height(envelope, top_height, sunlight_envelope)
        if allowed is None:
            repaired = True
            truncation_reasons.append(f"no_allowed_footprint_at_floor:{floor}")
            break
        legal = occupied.intersection(allowed)
        if legal.is_empty:
            repaired = True
            truncation_reasons.append(f"empty_legal_intersection_at_floor:{floor}")
            break
        if isinstance(legal, MultiPolygon):
            legal = largest_polygon(legal)
        if legal.area < _MIN_OCCUPIED_AREA_M2:
            repaired = True
            truncation_reasons.append(f"undersized_legal_intersection_at_floor:{floor}")
            break
        outside_area = float(occupied.difference(allowed).area)
        if outside_area > _AREA_TOLERANCE_M2:
            repaired = True
        geometry = mapping(utm_to_wgs84(legal))
        plate = {
            "floor": len(plates) + 1,
            "top_height": round(float(top_height), 2),
            "area": round(float(legal.area), 2),
            "geometry": geometry,
        }
        plates.append(plate)
        canonical_volumes.append({
            "band": len(canonical_volumes),
            "bottom_height": round(previous_top, 2),
            "top_height": round(float(top_height), 2),
            "geometry": geometry,
            "role": roles[0] if len(roles) == 1 else "floorwise_legal_union",
            "floorwise_legal": True,
        })
        previous_top = float(top_height)

    if not plates:
        return _reject(
            source=source,
            failed_checks=truncation_reasons or ["no_legal_occupied_floor"],
            checked_floor_count=0,
            original_height_m=original_height,
        )

    ground = _polygon(plates[0]["geometry"])
    if ground is None:
        return _reject(
            source=source,
            failed_checks=["invalid_repaired_ground_plate"],
            checked_floor_count=0,
            original_height_m=original_height,
        )
    site_area = float(envelope.site_area_m2)
    floor_area = sum(float(plate["area"]) for plate in plates)
    footprint_area = float(ground.area)
    props["building_type"] = building_type
    props["floor_height"] = floor_height
    props["num_floors"] = len(plates)
    props["height"] = round(float(plates[-1]["top_height"]), 2)
    props["footprint_area"] = round(footprint_area, 2)
    props["floor_area"] = round(floor_area, 2)
    props["bcr"] = round(footprint_area / site_area * 100.0, 2) if site_area > 0 else 0.0
    props["far"] = round(floor_area / site_area * 100.0, 2) if site_area > 0 else 0.0
    props["min_setback"] = round(float(ground.distance(envelope.site_utm.boundary)), 2)
    props["open_pct"] = round(max(0.0, 100.0 - props["bcr"]), 2)
    props["floor_plates"] = plates
    props["mass_volumes"] = canonical_volumes
    props["floor_groups"] = build_floor_groups(
        plates,
        site_area_m2=site_area,
        building_type=building_type,
    )
    props["typology_bands"] = [
        {
            "role": "floorwise_legal",
            "from_floor": plate["floor"],
            "to_floor": plate["floor"],
            "geometry": plate["geometry"],
        }
        for plate in plates
    ]
    candidate["geometry"] = plates[0]["geometry"]
    if len(plates) > 1:
        props["upper_geometry"] = plates[-1]["geometry"]
        props["lower_height"] = round(float(plates[-2]["top_height"]), 2)
        props["step_floor"] = len(plates) - 1

    legal_metrics = {
        key: props.get(key)
        for key in (
            "far",
            "bcr",
            "height",
            "num_floors",
            "footprint_area",
            "floor_area",
            "min_setback",
            "open_pct",
        )
    }
    model["floor_plates"] = plates
    model["floor_groups"] = props["floor_groups"]
    model["volumes"] = canonical_volumes
    model["legal_metrics"] = legal_metrics
    props["maas_model"] = model
    props["source_volumes"] = copy.deepcopy(canonical_volumes)
    model["source_volumes"] = copy.deepcopy(canonical_volumes)
    props.pop("source_surfaces", None)
    props.pop("section_source_surfaces", None)
    props.pop("section_profile_materialized", None)
    model.pop("source_surfaces", None)
    model.pop("section_source_surfaces", None)
    model.pop("section_profile_materialized", None)
    source_signature = props.get("source_signature")
    if not isinstance(source_signature, dict):
        source_signature = model.get("source_signature")
    if isinstance(source_signature, dict):
        source_signature = copy.deepcopy(source_signature)
        areas = [float(plate["area"]) for plate in plates]
        source_signature["volume_count"] = len(canonical_volumes)
        source_signature["surface_count"] = 0
        source_signature["effective_surface_count"] = 0
        source_signature["area_profile_m2"] = [round(area, 2) for area in areas]
        source_signature["upper_to_ground_ratio"] = round(
            areas[-1] / max(areas[0], 1e-9),
            4,
        )
        source_signature["floorwise_legal_revalidated"] = True
        props["source_signature"] = source_signature
        model["source_signature"] = copy.deepcopy(source_signature)
    geometry_resolution = {
        "schema_version": "arr.maas.geometry_resolution.v1",
        "status": "floorwise_legal_revalidated",
        "source": "final_floorwise_legal",
        "legal_action": "canonical_occupied_sections_clipped_and_rebound",
        "fallback": source,
    }
    props["geometry_resolution"] = geometry_resolution
    model["geometry_resolution"] = geometry_resolution

    metric_failures = failed_constraint_metrics(props, envelope)
    if metric_failures:
        return _reject(
            source=source,
            failed_checks=[f"constraint:{name}" for name in sorted(metric_failures)],
            checked_floor_count=len(plates),
            original_height_m=original_height,
        )

    evidence = {
        "schema_version": "arr.maas.floorwise_legal.v1",
        "status": "pass",
        "source": source,
        "repair_applied": repaired,
        "checked_floor_count": len(plates),
        "checked_mass_volume_count": len(canonical_volumes),
        "original_mass_volume_count": len(original_volumes),
        "original_height_m": round(original_height, 2),
        "validated_height_m": props["height"],
        "truncation_reasons": truncation_reasons,
        "checks": {
            "bcr": "pass",
            "far": "pass",
            "height": "pass",
            "setback": "pass",
            "sunlight_height_field": "pass",
            "occupied_sections": "pass",
        },
        "canonical_geometry_fields": [
            "geometry",
            "properties.floor_plates",
            "properties.mass_volumes",
            "properties.source_volumes",
            "properties.maas_model.floor_plates",
            "properties.maas_model.volumes",
            "properties.maas_model.source_volumes",
        ],
    }
    props["floorwise_legal_evidence"] = evidence
    model["floorwise_legal_evidence"] = evidence
    return FloorwiseLegalResult(feature=candidate, evidence=evidence)


__all__ = ["FloorwiseLegalResult", "revalidate_final_floorwise_feature"]
