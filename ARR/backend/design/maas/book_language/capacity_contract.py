"""Feasible building-capacity targets for BOOK geometry authors.

This module owns only the capacity contract. Legal envelope construction and
parking remain in their existing hard-gate modules; portfolio orchestration
only passes the resulting immutable dictionaries between stages.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon
from shapely.ops import unary_union

from design.maas.source_geometry.ir import SourceMass


def build_feasible_capacity_contract(
    context: Any,
    *,
    site_local_utm: Polygon,
    height_m: float,
    floors: int,
    target_utilization: float = 0.88,
    minimum_utilization: float = 0.78,
    floor_capacity_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure gross floor capacity from the live legal field, BCR and FAR."""
    # Local import keeps the dependency one-way: legal generation does not
    # need to know that an authoring-capacity policy exists.
    from .downstream_hard_gate import generation_site_at_height

    plan = (
        floor_capacity_plan
        if isinstance(floor_capacity_plan, dict)
        and floor_capacity_plan.get("schema_version")
        == "arr.maas.floor_capacity_plan.v1"
        and floor_capacity_plan.get("status") in {"materialized", "target_unreachable"}
        else None
    )
    floor_count = max(
        1,
        int(
            (plan or {}).get("selected_floor_count")
            or floors
        ),
    )
    effective_height = float(
        (plan or {}).get("selected_height_m")
        or height_m
    )
    parcel_area = max(float(site_local_utm.area), 1e-9)
    floor_step = max(0.0, effective_height) / floor_count
    legal_floor_areas = (
        [
            max(0.0, float(value))
            for value in plan.get("legal_floor_section_areas_m2") or ()
        ][:floor_count]
        if plan is not None
        else []
    )
    if len(legal_floor_areas) != floor_count:
        legal_floor_areas = []
        for floor_index in range(floor_count):
            section = generation_site_at_height(context, floor_step * (floor_index + 1))
            legal_floor_areas.append(float(section.area) if section is not None else 0.0)

    bcr_limit = max(0.0, float(context.envelope.bcr_limit))
    far_limit = max(0.0, float(context.envelope.far_limit))
    bcr_adjusted_areas = list(legal_floor_areas)
    if bcr_adjusted_areas:
        bcr_adjusted_areas[0] = min(
            bcr_adjusted_areas[0],
            parcel_area * bcr_limit / 100.0,
        )
    height_field_capacity = sum(bcr_adjusted_areas)
    far_capacity = parcel_area * far_limit / 100.0
    feasible_maximum = (
        max(0.0, float(plan.get("feasible_maximum_gfa_m2") or 0.0))
        if plan is not None
        else max(0.0, min(height_field_capacity, far_capacity))
    )
    target_ratio = max(0.50, min(0.98, float(target_utilization)))
    minimum_ratio = max(0.40, min(target_ratio, float(minimum_utilization)))
    target_floor_area = (
        max(0.0, float(plan.get("target_gfa_m2") or 0.0))
        if plan is not None
        else feasible_maximum * target_ratio
    )
    generation_area = max(float(context.generation_site.area), 1e-9)
    legal_field_yield_ratio = (
        min(1.0, target_floor_area / height_field_capacity)
        if height_field_capacity > 1e-9
        else 0.0
    )
    ground_capacity = (
        float(bcr_adjusted_areas[0])
        if bcr_adjusted_areas
        else generation_area
    )
    plan_floor_targets = (
        [
            max(0.0, float(value))
            for value in plan.get("target_floor_areas_m2") or ()
        ][:floor_count]
        if plan is not None
        else []
    )
    target_ground_plan = (
        min(ground_capacity, plan_floor_targets[0])
        if len(plan_floor_targets) == floor_count and plan_floor_targets
        else ground_capacity * legal_field_yield_ratio
    )
    return {
        "schema_version": "arr.maas.feasible_base_capacity.v1",
        "status": "materialized" if feasible_maximum > 0.0 else "infeasible",
        "derivation": "per_floor_legal_section_sum_capped_by_ground_bcr_and_far",
        "parcel_area_m2": round(parcel_area, 3),
        "generation_site_area_m2": round(generation_area, 3),
        "requested_height_m": round(effective_height, 3),
        "requested_floors": floor_count,
        "legal_floor_section_areas_m2": [round(value, 3) for value in legal_floor_areas],
        "bcr_adjusted_floor_areas_m2": [round(value, 3) for value in bcr_adjusted_areas],
        "bcr_limit_pct": round(bcr_limit, 3),
        "far_limit_pct": round(far_limit, 3),
        "height_field_capacity_m2": round(height_field_capacity, 3),
        "far_capacity_m2": round(far_capacity, 3),
        "feasible_maximum_floor_area_m2": round(feasible_maximum, 3),
        "target_utilization": round(target_ratio, 4),
        "minimum_utilization": round(minimum_ratio, 4),
        "target_floor_area_m2": round(target_floor_area, 3),
        "target_floor_areas_m2": [
            round(value, 3) for value in plan_floor_targets
        ],
        "minimum_floor_area_m2": round(feasible_maximum * minimum_ratio, 3),
        "legal_field_target_yield_ratio": round(legal_field_yield_ratio, 4),
        "target_base_plan_area_m2": round(target_ground_plan, 3),
        "target_base_plan_coverage": round(
            min(0.95, target_ground_plan / generation_area),
            4,
        ),
        "statutory_far_is_not_assumed_reachable": True,
        "parking_rechecked_downstream": True,
        "floor_capacity_plan_hash": str(
            (plan or {}).get("floor_capacity_plan_hash") or ""
        ),
        "floor_capacity_plan_status": str((plan or {}).get("status") or ""),
    }


def measure_source_capacity(
    source: SourceMass,
    contract: dict[str, Any],
    *,
    site_local_utm: Polygon,
    height_m: float,
    floors: int,
    shared_floor_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare one source graph with the same floorwise capacity contract."""
    shared = (
        shared_floor_contract
        if isinstance(shared_floor_contract, dict)
        and shared_floor_contract.get("schema_version") == "arr.maas.shared_floor_contract.v1"
        else None
    )
    if shared is not None:
        totals = shared.get("totals") if isinstance(shared.get("totals"), dict) else {}
        floor_area = float(totals.get("total_floor_area_m2") or 0.0)
    else:
        floor_count = max(1, int(floors))
        floor_area = 0.0
        for floor_index in range(floor_count):
            fraction = (floor_index + 0.5) / floor_count
            active = [
                volume.footprint
                for volume in source.volumes
                if float(volume.bottom_fraction) <= fraction < float(volume.top_fraction)
            ]
            if active:
                floor_area += float(unary_union(active).area)
    parcel_area = max(float(site_local_utm.area), 1e-9)
    feasible = max(float(contract.get("feasible_maximum_floor_area_m2") or 0.0), 1e-9)
    utilization = floor_area / feasible
    minimum = float(contract.get("minimum_utilization") or 0.0)
    return {
        "schema_version": "arr.maas.source_capacity_measurement.v1",
        "floor_area_m2": round(floor_area, 3),
        "far_pct": round(floor_area / parcel_area * 100.0, 3),
        "feasible_maximum_floor_area_m2": round(feasible, 3),
        "feasible_capacity_utilization": round(utilization, 4),
        "minimum_utilization": round(minimum, 4),
        "floor_contract_hash": str((shared or {}).get("floor_contract_hash") or ""),
        "hard_pass": bool(
            utilization + 1e-9 >= minimum
            and (shared is None or shared.get("hard_pass") is True)
        ),
    }


def recursive_plan_coverage_floor(
    building_type: str,
    contract: dict[str, Any] | None = None,
    *,
    host_area_m2: float | None = None,
) -> float:
    """Translate the live capacity contract into a plan-fit floor.

    Program role coverage is already carried by the compiled source union in
    ``source_bridge``.  Keeping a second use-specific floor here enlarged only
    neighborhood forms and made capacity behavior inconsistent across gym,
    cultural and other programs.
    """
    del building_type
    capacity = contract or {}
    target_area = float(capacity.get("target_base_plan_area_m2") or 0.0)
    if host_area_m2 and float(host_area_m2) > 0.0 and target_area > 0.0:
        capacity_floor = target_area / float(host_area_m2)
    else:
        capacity_floor = float(capacity.get("target_base_plan_coverage") or 0.0)
    return max(0.0, min(0.95, capacity_floor))


__all__ = [
    "build_feasible_capacity_contract",
    "measure_source_capacity",
    "recursive_plan_coverage_floor",
]
