"""Deterministic parking layout precheck helpers for MAAS.

This is a conservative capacity estimator, not a final parking layout solver.
It uses statutory/design module dimensions to decide whether a candidate mass
has a plausible parking envelope before a later solver places exact stalls,
aisles, ramps, turning paths, columns, and accessible routes.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import MultiPolygon, Polygon


DEFAULT_STALL_WIDTH_M = 2.5
DEFAULT_STALL_LENGTH_M = 5.0
DEFAULT_AISLE_WIDTH_M = 6.0
DEFAULT_ACCESSIBLE_WIDTH_M = 3.3
DEFAULT_ACCESSIBLE_LENGTH_M = 5.0
SMALL_ATTACHED_PARKING_MAX_SPACES = 8
TANDEM_ALLOWED_MAX_SPACES = 5
ATTACHED_PARKING_ENTRANCE_WIDTH_M = 3.0
ATTACHED_PARKING_DEAD_END_APPROVAL_ENTRANCE_WIDTH_M = 2.5
ROAD_AS_AISLE_UNDIVIDED_MAX_ROAD_WIDTH_M = 12.0
ROAD_AS_AISLE_PERPENDICULAR_REQUIRED_WIDTH_M = 6.0
ROAD_AS_AISLE_PARALLEL_REQUIRED_WIDTH_M = 4.0


def estimate_parking_capacity(
    envelope: Polygon | MultiPolygon | None,
    *,
    strategy: str,
    include_accessible: bool = True,
) -> dict[str, Any]:
    """Estimate 90-degree self-parking capacity in a candidate envelope."""
    polygon = _largest_polygon(envelope)
    if polygon is None or polygon.is_empty or polygon.area <= 0:
        return _empty("missing_or_empty_envelope", strategy)

    long_side, short_side = _oriented_rect_dimensions(polygon)
    usable_factor = _usable_factor(strategy)
    effective_area = polygon.area * usable_factor

    double_loaded = _module_capacity(
        length=long_side,
        depth=short_side,
        module_depth=DEFAULT_STALL_LENGTH_M * 2 + DEFAULT_AISLE_WIDTH_M,
        rows_per_module=2,
    )
    single_loaded = _module_capacity(
        length=long_side,
        depth=short_side,
        module_depth=DEFAULT_STALL_LENGTH_M + DEFAULT_AISLE_WIDTH_M,
        rows_per_module=1,
    )
    area_capacity = math.floor(effective_area / _planning_module_area(strategy))
    estimated = max(0, min(max(double_loaded, single_loaded), area_capacity))
    if strategy == "mechanical":
        estimated = None

    return {
        "status": "heuristic_only",
        "strategy": strategy,
        "envelope_area_m2": round(polygon.area, 2),
        "effective_area_m2": round(effective_area, 2),
        "oriented_rect": {
            "long_side_m": round(long_side, 2),
            "short_side_m": round(short_side, 2),
        },
        "module_dimensions": {
            "stall_width_m": DEFAULT_STALL_WIDTH_M,
            "stall_length_m": DEFAULT_STALL_LENGTH_M,
            "aisle_width_m": DEFAULT_AISLE_WIDTH_M,
            "double_loaded_depth_m": DEFAULT_STALL_LENGTH_M * 2 + DEFAULT_AISLE_WIDTH_M,
            "single_loaded_depth_m": DEFAULT_STALL_LENGTH_M + DEFAULT_AISLE_WIDTH_M,
            "accessible_width_m": DEFAULT_ACCESSIBLE_WIDTH_M if include_accessible else None,
            "accessible_length_m": DEFAULT_ACCESSIBLE_LENGTH_M if include_accessible else None,
        },
        "capacity_estimates": {
            "single_loaded_spaces": single_loaded,
            "double_loaded_spaces": double_loaded,
            "area_limited_spaces": area_capacity,
            "estimated_capacity_spaces": estimated,
        },
        "limitations": [
            "does_not_place_exact_stalls",
            "does_not_model_columns_or_core_obstructions",
            "does_not_check_ramp_slope_or_turning_swept_path",
            "does_not_verify_accessible_route",
        ],
    }


def generate_parking_layout_candidate(
    envelope: Polygon | MultiPolygon | None,
    *,
    required_spaces: int,
    strategy: str = "ground_surface",
    accessible_spaces: int = 0,
    road_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate deterministic stall coordinates for early MAAS parking review.

    This is a coordinate placer, not an optimizer. It creates a legally
    explainable first candidate that a later grid/MIP solver can improve.
    """
    polygon = _largest_polygon(envelope)
    if polygon is None or polygon.is_empty or polygon.area <= 0:
        return _layout_result(
            status="fail",
            strategy=strategy,
            placement_mode="none",
            required_spaces=required_spaces,
            accessible_spaces=accessible_spaces,
            stalls=[],
            reason="missing_or_empty_envelope",
        )

    relief = evaluate_small_attached_parking_relief(
        required_spaces=required_spaces,
        road_context=road_context,
    )
    road_as_aisle = any(option["available"] for option in relief["road_as_aisle_options"])
    if road_as_aisle:
        candidate = _place_road_as_aisle_stalls(
            polygon,
            required_spaces=required_spaces,
            accessible_spaces=accessible_spaces,
            allow_tandem=bool(relief["tandem_parking"]["available"]),
        )
        candidate["small_attached_parking_relief"] = relief
        if candidate["provided_spaces"] >= required_spaces:
            return candidate

    candidate = _place_internal_90_degree_stalls(
        polygon,
        required_spaces=required_spaces,
        accessible_spaces=accessible_spaces,
        strategy=strategy,
    )
    candidate["small_attached_parking_relief"] = relief
    return candidate


def evaluate_small_attached_parking_relief(
    *,
    required_spaces: int | None = None,
    road_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate small attached-parking layout exceptions without approving them."""
    context = road_context or {}
    road_width = _optional_float(context.get("road_width_m"))
    has_sidewalk_separation = _optional_bool(context.get("has_sidewalk_separation"))
    is_dead_end = bool(context.get("is_dead_end_road"))
    required_known = required_spaces is not None
    within_8 = required_spaces <= SMALL_ATTACHED_PARKING_MAX_SPACES if required_known else None
    within_5 = required_spaces <= TANDEM_ALLOWED_MAX_SPACES if required_known else None

    undivided_road_possible = (
        road_width is not None
        and road_width < ROAD_AS_AISLE_UNDIVIDED_MAX_ROAD_WIDTH_M
        and has_sidewalk_separation is False
        and (within_8 is not False)
    )
    wide_road_perpendicular_possible = (
        road_width is not None
        and road_width >= ROAD_AS_AISLE_UNDIVIDED_MAX_ROAD_WIDTH_M
        and has_sidewalk_separation is True
        and (within_5 is not False)
    )

    return {
        "status": "evaluated" if required_known else "needs_required_count",
        "source": "Parking Lot Act Enforcement Rule Article 11(5)",
        "applies_to": "attached_self_parking_total_spaces_8_or_less",
        "required_spaces": required_spaces,
        "road_context": {
            "road_width_m": road_width,
            "has_sidewalk_separation": has_sidewalk_separation,
            "is_dead_end_road": is_dead_end,
        },
        "road_as_aisle_options": [
            {
                "key": "undivided_road_under_12m",
                "available": bool(undivided_road_possible),
                "condition": "No sidewalk/roadway separation, road width under 12m, total attached self-parking spaces 8 or less.",
                "aisle_width_counting_road_m": ROAD_AS_AISLE_PERPENDICULAR_REQUIRED_WIDTH_M,
                "parallel_aisle_width_counting_road_m": ROAD_AS_AISLE_PARALLEL_REQUIRED_WIDTH_M,
                "road_inclusion_scope": "to_centerline_or_opposite_boundary_if_no_centerline",
            },
            {
                "key": "sidewalk_separated_road_12m_or_more_perpendicular",
                "available": bool(wide_road_perpendicular_possible),
                "condition": "Sidewalk/roadway separated road 12m or wider, total spaces 5 or less, no obstruction to parking use.",
                "parking_angle": "perpendicular_only",
                "needs_authority_review": True,
            },
        ],
        "tandem_parking": {
            "available": within_5 is not False,
            "condition": "For 5 or fewer stalls, up to two stalls may be placed in tandem from the aisle.",
            "max_depth_from_aisle": 2,
        },
        "entrance_width": {
            "min_width_m": ATTACHED_PARKING_ENTRANCE_WIDTH_M,
            "dead_end_road_approval_min_width_m": (
                ATTACHED_PARKING_DEAD_END_APPROVAL_ENTRANCE_WIDTH_M if is_dead_end else None
            ),
        },
        "limitations": [
            "does_not_replace_required_stall_count",
            "needs_actual_road_geometry_and_centerline",
            "needs_local_authority_no_traffic_obstruction_review",
        ],
    }


def _place_road_as_aisle_stalls(
    polygon: Polygon,
    *,
    required_spaces: int,
    accessible_spaces: int,
    allow_tandem: bool,
) -> dict[str, Any]:
    origin, u, v, length, depth = _oriented_frame(polygon)
    max_depth_rows = 2 if allow_tandem else 1
    depth_rows = min(max_depth_rows, max(0, math.floor(depth / DEFAULT_STALL_LENGTH_M)))
    if depth_rows <= 0:
        return _layout_result(
            status="fail",
            strategy="ground_surface",
            placement_mode="road_as_aisle",
            required_spaces=required_spaces,
            accessible_spaces=accessible_spaces,
            stalls=[],
            reason="insufficient_depth_for_stall",
        )

    stalls = _fill_rows(
        polygon,
        origin=origin,
        u=u,
        v=v,
        length=length,
        row_depth=DEFAULT_STALL_LENGTH_M,
        row_offsets=[i * DEFAULT_STALL_LENGTH_M for i in range(depth_rows)],
        required_spaces=required_spaces,
        accessible_spaces=accessible_spaces,
        mode="road_as_aisle_tandem" if depth_rows > 1 else "road_as_aisle_single_row",
    )
    return _layout_result(
        status="pass" if len(stalls) >= required_spaces else "fail",
        strategy="ground_surface",
        placement_mode="road_as_aisle_tandem" if depth_rows > 1 else "road_as_aisle_single_row",
        required_spaces=required_spaces,
        accessible_spaces=accessible_spaces,
        stalls=stalls,
        reason=None if len(stalls) >= required_spaces else "insufficient_frontage_or_depth",
    )


def _place_internal_90_degree_stalls(
    polygon: Polygon,
    *,
    required_spaces: int,
    accessible_spaces: int,
    strategy: str,
) -> dict[str, Any]:
    origin, u, v, length, depth = _oriented_frame(polygon)
    row_offsets: list[float] = []
    if depth >= DEFAULT_STALL_LENGTH_M * 2 + DEFAULT_AISLE_WIDTH_M:
        row_offsets = [0.0, DEFAULT_STALL_LENGTH_M + DEFAULT_AISLE_WIDTH_M]
        mode = "internal_double_loaded_90"
    elif depth >= DEFAULT_STALL_LENGTH_M + DEFAULT_AISLE_WIDTH_M:
        row_offsets = [0.0]
        mode = "internal_single_loaded_90"
    else:
        mode = "internal_90"

    stalls = _fill_rows(
        polygon,
        origin=origin,
        u=u,
        v=v,
        length=length,
        row_depth=DEFAULT_STALL_LENGTH_M,
        row_offsets=row_offsets,
        required_spaces=required_spaces,
        accessible_spaces=accessible_spaces,
        mode=mode,
    )
    return _layout_result(
        status="pass" if len(stalls) >= required_spaces else "fail",
        strategy=strategy,
        placement_mode=mode,
        required_spaces=required_spaces,
        accessible_spaces=accessible_spaces,
        stalls=stalls,
        reason=None if len(stalls) >= required_spaces else "insufficient_internal_module_capacity",
    )


def _fill_rows(
    polygon: Polygon,
    *,
    origin: tuple[float, float],
    u: tuple[float, float],
    v: tuple[float, float],
    length: float,
    row_depth: float,
    row_offsets: list[float],
    required_spaces: int,
    accessible_spaces: int,
    mode: str,
) -> list[dict[str, Any]]:
    stalls: list[dict[str, Any]] = []
    remaining_accessible = max(0, min(accessible_spaces, required_spaces))
    for row_index, offset in enumerate(row_offsets):
        cursor = 0.0
        while len(stalls) < required_spaces:
            is_accessible = remaining_accessible > 0
            width = DEFAULT_ACCESSIBLE_WIDTH_M if is_accessible else DEFAULT_STALL_WIDTH_M
            if cursor + width > length + 1e-9:
                break
            stall_polygon = _rect_from_frame(
                origin=origin,
                u=u,
                v=v,
                start_u=cursor,
                start_v=offset,
                width_u=width,
                width_v=row_depth,
            )
            if polygon.buffer(1e-7).contains(stall_polygon):
                stalls.append({
                    "stall_id": f"P{len(stalls) + 1:02d}",
                    "type": "accessible" if is_accessible else "standard",
                    "width_m": width,
                    "length_m": row_depth,
                    "row": row_index + 1,
                    "mode": mode,
                    "polygon": _polygon_coordinates(stall_polygon),
                })
                if is_accessible:
                    remaining_accessible -= 1
            cursor += width
    return stalls


def _layout_result(
    *,
    status: str,
    strategy: str,
    placement_mode: str,
    required_spaces: int,
    accessible_spaces: int,
    stalls: list[dict[str, Any]],
    reason: str | None,
) -> dict[str, Any]:
    unmet = max(0, required_spaces - len(stalls))
    result = {
        "schema_version": "arr.maas.parking_layout_candidate.v0",
        "status": status,
        "strategy": strategy,
        "placement_mode": placement_mode,
        "required_spaces": required_spaces,
        "required_accessible_spaces": accessible_spaces,
        "provided_spaces": len(stalls),
        "provided_accessible_spaces": sum(1 for stall in stalls if stall["type"] == "accessible"),
        "unmet_spaces": unmet,
        "stalls": stalls,
        "limitations": [
            "deterministic_first_candidate_not_global_optimum",
            "does_not_model_columns_core_or_swept_path",
            "does_not_replace_grid_mip_solver",
        ],
    }
    if reason:
        result["reason"] = reason
    if unmet > 0:
        result["repair_requests"] = [
            {
                "operation": "increase_parking_envelope_or_switch_strategy",
                "reason": f"{unmet} required parking spaces are not placed.",
                "target_agent": "maas_geometry_agent",
            }
        ]
    else:
        result["repair_requests"] = []
    return result


def _oriented_frame(polygon: Polygon) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], float, float]:
    rect = polygon.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    edges: list[tuple[float, int]] = []
    for i in range(min(4, len(coords) - 1)):
        edges.append((math.dist(coords[i], coords[i + 1]), i))
    if not edges:
        return (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0, 0.0
    long_len, long_idx = max(edges, key=lambda item: item[0])
    short_len = min(length for length, _idx in edges)
    p0 = coords[long_idx]
    p1 = coords[long_idx + 1]
    ux = (p1[0] - p0[0]) / long_len if long_len else 1.0
    uy = (p1[1] - p0[1]) / long_len if long_len else 0.0
    vx, vy = -uy, ux
    centroid = polygon.centroid
    test = (p0[0] + vx * short_len * 0.5, p0[1] + vy * short_len * 0.5)
    if math.dist((centroid.x, centroid.y), test) > math.dist((centroid.x, centroid.y), (p0[0] - vx * short_len * 0.5, p0[1] - vy * short_len * 0.5)):
        vx, vy = -vx, -vy
    return (p0[0], p0[1]), (ux, uy), (vx, vy), long_len, short_len


def _rect_from_frame(
    *,
    origin: tuple[float, float],
    u: tuple[float, float],
    v: tuple[float, float],
    start_u: float,
    start_v: float,
    width_u: float,
    width_v: float,
) -> Polygon:
    corners = [
        _frame_point(origin, u, v, start_u, start_v),
        _frame_point(origin, u, v, start_u + width_u, start_v),
        _frame_point(origin, u, v, start_u + width_u, start_v + width_v),
        _frame_point(origin, u, v, start_u, start_v + width_v),
    ]
    return Polygon(corners)


def _frame_point(
    origin: tuple[float, float],
    u: tuple[float, float],
    v: tuple[float, float],
    offset_u: float,
    offset_v: float,
) -> tuple[float, float]:
    return (
        origin[0] + u[0] * offset_u + v[0] * offset_v,
        origin[1] + u[1] * offset_u + v[1] * offset_v,
    )


def _polygon_coordinates(polygon: Polygon) -> list[list[float]]:
    return [[round(x, 4), round(y, 4)] for x, y in polygon.exterior.coords]


def _module_capacity(*, length: float, depth: float, module_depth: float, rows_per_module: int) -> int:
    modules = math.floor(depth / module_depth)
    stalls_per_row = math.floor(length / DEFAULT_STALL_WIDTH_M)
    return max(0, modules * rows_per_module * stalls_per_row)


def _oriented_rect_dimensions(polygon: Polygon) -> tuple[float, float]:
    rect = polygon.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    if len(coords) < 4:
        return 0.0, 0.0
    lengths = [
        math.dist(coords[i], coords[i + 1])
        for i in range(min(4, len(coords) - 1))
    ]
    if not lengths:
        return 0.0, 0.0
    unique = sorted(lengths)
    short_side = unique[0]
    long_side = unique[-1]
    return long_side, short_side


def _largest_polygon(geometry: Polygon | MultiPolygon | None) -> Polygon | None:
    if geometry is None:
        return None
    if isinstance(geometry, Polygon):
        return geometry
    if isinstance(geometry, MultiPolygon):
        polygons = [g for g in geometry.geoms if isinstance(g, Polygon) and not g.is_empty]
        if not polygons:
            return None
        return max(polygons, key=lambda g: g.area)
    return None


def _usable_factor(strategy: str) -> float:
    if strategy == "piloti_ground":
        return 0.62
    if strategy in {"basement", "semi_basement"}:
        return 0.75
    if strategy == "ground_surface":
        return 0.85
    if strategy == "mixed":
        return 0.70
    return 0.0


def _planning_module_area(strategy: str) -> float:
    if strategy in {"basement", "semi_basement"}:
        return 32.0
    if strategy == "piloti_ground":
        return 34.0
    return 30.0


def _empty(reason: str, strategy: str) -> dict[str, Any]:
    return {
        "status": "heuristic_only",
        "strategy": strategy,
        "reason": reason,
        "envelope_area_m2": 0.0,
        "capacity_estimates": {
            "single_loaded_spaces": 0,
            "double_loaded_spaces": 0,
            "area_limited_spaces": 0,
            "estimated_capacity_spaces": 0,
        },
    }


def _optional_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return None


__all__ = [
    "DEFAULT_ACCESSIBLE_LENGTH_M",
    "DEFAULT_ACCESSIBLE_WIDTH_M",
    "DEFAULT_AISLE_WIDTH_M",
    "DEFAULT_STALL_LENGTH_M",
    "DEFAULT_STALL_WIDTH_M",
    "evaluate_small_attached_parking_relief",
    "estimate_parking_capacity",
    "generate_parking_layout_candidate",
]
