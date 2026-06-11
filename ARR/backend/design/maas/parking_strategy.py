"""Parking-aware strategy metadata for MAAS candidates.

This module does not decide legal parking compliance. It records deterministic
mass-generation intent so parking can constrain later repairs instead of being
left as a final checklist item.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import MultiPolygon, Polygon

from design.maas.parking_layout import (
    evaluate_small_attached_parking_relief,
    estimate_parking_capacity,
    generate_parking_layout_candidate,
)


PARKING_STRATEGIES = {
    "none",
    "ground_surface",
    "piloti_ground",
    "basement",
    "semi_basement",
    "mechanical",
    "mixed",
}


def attach_parking_strategy(
    props: dict[str, Any],
    *,
    site_area_m2: float,
    building_type: str,
    footprint_utm: Polygon | None = None,
    site_utm: Polygon | None = None,
    road_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach parking strategy metadata to candidate properties and maas_model."""
    strategy = infer_parking_strategy(
        props,
        site_area_m2=site_area_m2,
        building_type=building_type,
        footprint_utm=footprint_utm,
        site_utm=site_utm,
        road_context=road_context,
    )
    props["parking_strategy"] = strategy["selected_strategy"]
    props["parking_strategy_candidates"] = strategy["strategy_candidates"]
    props["parking_precheck"] = strategy
    model = props.get("maas_model")
    if isinstance(model, dict):
        model["parking_strategy"] = strategy["selected_strategy"]
        model["parking_precheck"] = strategy
    return strategy


def infer_parking_strategy(
    props: dict[str, Any],
    *,
    site_area_m2: float,
    building_type: str,
    footprint_utm: Polygon | None = None,
    site_utm: Polygon | None = None,
    road_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic parking strategy hints from mass metrics.

    The values here are planning heuristics. Required count still comes from
    the law graph plus floor/use schedule, and layout pass/fail must come from a
    later parking solver.
    """
    footprint_area = _float(props.get("footprint_area"))
    total_floor_area = _float(props.get("floor_area"))
    floors = max(int(_float(props.get("num_floors")) or 0), 0)
    bcr = _float(props.get("bcr"))
    open_area = max(site_area_m2 - footprint_area, 0.0)
    small_lot = site_area_m2 > 0 and site_area_m2 < 330.0
    dense_footprint = bcr >= 55.0 or (site_area_m2 > 0 and open_area / site_area_m2 < 0.35)
    residential_like = _is_residential_like(building_type)

    if floors <= 0 or total_floor_area <= 0:
        candidates = ["none"]
        selected = "none"
    elif small_lot and residential_like:
        candidates = ["piloti_ground", "mechanical", "semi_basement", "basement", "mixed"]
        selected = "piloti_ground"
    elif dense_footprint:
        candidates = ["piloti_ground", "basement", "mechanical", "mixed"]
        selected = "piloti_ground"
    elif floors >= 5:
        candidates = ["basement", "piloti_ground", "mixed", "mechanical"]
        selected = "basement"
    else:
        candidates = ["ground_surface", "piloti_ground", "semi_basement", "mixed"]
        selected = "ground_surface"

    layout_precheck = _layout_precheck(
        selected,
        footprint_area=footprint_area,
        open_area=open_area,
        footprint_utm=footprint_utm,
        site_utm=site_utm,
    )
    small_attached_parking = evaluate_small_attached_parking_relief(
        road_context=road_context or props.get("road_context") or props.get("parking_road_context")
    )
    required_spaces = _optional_int(_first_present(
        props.get("required_parking_spaces"),
        props.get("parking_required_spaces"),
        props.get("parking_count_required"),
    ))
    accessible_spaces = _optional_int(_first_present(
        props.get("required_accessible_parking_spaces"),
        props.get("accessible_parking_required_spaces"),
    )) or 0
    layout_candidate = None
    if required_spaces is not None and required_spaces >= 0:
        envelope = _parking_envelope(selected, footprint_utm=footprint_utm, site_utm=site_utm)
        layout_candidate = generate_parking_layout_candidate(
            envelope,
            required_spaces=required_spaces,
            accessible_spaces=accessible_spaces,
            strategy=selected,
            road_context=road_context or props.get("road_context") or props.get("parking_road_context"),
        )

    result = {
        "schema_version": "arr.maas.parking_strategy.v0",
        "status": "has_layout_candidate" if layout_candidate else "needs_parking_requirements",
        "selected_strategy": selected,
        "strategy_candidates": candidates,
        "basis": {
            "site_area_m2": _round(site_area_m2),
            "footprint_area_m2": _round(footprint_area),
            "open_area_m2": _round(open_area),
            "total_floor_area_m2": _round(total_floor_area),
            "num_floors": floors,
            "building_type": building_type,
            "small_lot": small_lot,
            "dense_footprint": dense_footprint,
            "residential_like": residential_like,
        },
        "mass_generation_constraints": _strategy_constraints(selected),
        "layout_precheck": layout_precheck,
        "small_attached_parking_relief": small_attached_parking,
        "required_count": {
            "status": "needs_graph_requirement",
            "reason": "Required parking count depends on local ordinance, use classification, and floor/use area schedule.",
            "facility_area_m2": _round(total_floor_area),
        },
        "repair_request_templates": _repair_templates(selected),
    }
    if layout_candidate:
        result["layout_candidate"] = layout_candidate
    return result


def _strategy_constraints(strategy: str) -> dict[str, Any]:
    common = {
        "vehicle_access": "needs_driveway_and_aisle_check",
        "pedestrian_access": "separate_from_vehicle_path_where_required",
        "accessible_parking": "needs_accessible_stall_and_route_check",
        "core_placement": "must_not_block_parking_access_or_primary_egress",
    }
    if strategy == "piloti_ground":
        return {
            **common,
            "ground_floor": "reserve_void_or_partial_void_for_parking",
            "column_grid": "needs_usable_bay_width_check",
            "lost_program_area": "deduct_or_reassign_1f_program",
        }
    if strategy in {"basement", "semi_basement"}:
        return {
            **common,
            "ramp": "needs_ramp_slope_width_and_turning_check",
            "excavation": "needs_feasibility_and_cost_review",
        }
    if strategy == "mechanical":
        return {
            **common,
            "equipment": "needs_mechanical_parking_type_and_clearance_check",
            "queueing": "needs_entry_waiting_space_check",
        }
    if strategy == "ground_surface":
        return {
            **common,
            "surface_yard": "use_open_area_before_cutting_mass",
        }
    return common


def _layout_precheck(
    strategy: str,
    *,
    footprint_area: float,
    open_area: float,
    footprint_utm: Polygon | None,
    site_utm: Polygon | None,
) -> dict[str, Any]:
    envelope = _parking_envelope(strategy, footprint_utm=footprint_utm, site_utm=site_utm)
    if envelope is not None:
        return estimate_parking_capacity(envelope, strategy=strategy)

    planning_module_area = 30.0
    if strategy == "ground_surface":
        estimated_capacity = math.floor(max(open_area, 0.0) / planning_module_area)
        envelope_area = open_area
    elif strategy == "piloti_ground":
        envelope_area = max(footprint_area * 0.62, 0.0)
        estimated_capacity = math.floor(envelope_area / planning_module_area)
    elif strategy in {"basement", "semi_basement"}:
        envelope_area = max(footprint_area * 0.75, 0.0)
        estimated_capacity = math.floor(envelope_area / planning_module_area)
    elif strategy == "mechanical":
        envelope_area = max(footprint_area * 0.18, 0.0)
        estimated_capacity = None
    else:
        envelope_area = 0.0
        estimated_capacity = 0
    return {
        "status": "heuristic_only",
        "planning_module_area_m2_per_space": planning_module_area,
        "candidate_parking_envelope_area_m2": _round(envelope_area),
        "estimated_capacity_spaces": estimated_capacity,
        "note": "This is not a legal layout pass. A parking solver must check stalls, aisles, turning, ramps, and accessible route.",
    }


def _parking_envelope(
    strategy: str,
    *,
    footprint_utm: Polygon | None,
    site_utm: Polygon | None,
) -> Polygon | MultiPolygon | None:
    if strategy in {"piloti_ground", "basement", "semi_basement", "mechanical", "mixed"}:
        return footprint_utm
    if strategy == "ground_surface" and site_utm is not None and footprint_utm is not None:
        try:
            return site_utm.difference(footprint_utm)
        except Exception:
            return None
    return None


def _repair_templates(strategy: str) -> list[dict[str, Any]]:
    templates = [
        {
            "operation": "move_core",
            "reason": "Core blocks parking aisle or accessible route.",
            "target_agent": "maas_geometry_agent",
        },
        {
            "operation": "reduce_or_split_footprint",
            "reason": "Open area or parking aisle is insufficient.",
            "target_agent": "maas_geometry_agent",
        },
    ]
    if strategy == "piloti_ground":
        templates.insert(0, {
            "operation": "reserve_piloti_void",
            "reason": "Ground floor must reserve enough covered parking envelope.",
            "target_agent": "maas_geometry_agent",
        })
    elif strategy in {"basement", "semi_basement"}:
        templates.insert(0, {
            "operation": "add_ramp_and_basement_parking",
            "reason": "Surface or piloti capacity is insufficient.",
            "target_agent": "maas_geometry_agent",
        })
    elif strategy == "mechanical":
        templates.insert(0, {
            "operation": "switch_to_mechanical_parking",
            "reason": "Conventional stall packing is infeasible on the parcel.",
            "target_agent": "maas_geometry_agent",
        })
    return templates


def _is_residential_like(building_type: str) -> bool:
    label = building_type or ""
    return any(token in label for token in ("주택", "공동", "다가구", "다세대", "오피스텔", "생활"))


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _optional_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _round(value: float) -> float:
    return round(float(value), 2)


__all__ = ["PARKING_STRATEGIES", "attach_parking_strategy", "infer_parking_strategy"]
