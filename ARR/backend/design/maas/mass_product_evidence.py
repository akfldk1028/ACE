"""Serialize one authoritative MASS floor product for API consumers.

The frontend must display the compiler and hard-gate evidence verbatim.  This
module deliberately normalizes existing typed evidence and never estimates
floor counts, areas, parking, or legal ratios from a rendered image.
"""

from __future__ import annotations

from typing import Any, Mapping

from design.maas.geometry_language.ast import GeometryProgram


def serialize_mass_product_evidence(
    *,
    program: GeometryProgram,
    capacity: Mapping[str, Any] | None = None,
    hard_gates: Mapping[str, Any] | None = None,
    passport: Mapping[str, Any] | None = None,
    compilation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return stable floor/legal/parking/matrix fields for archive manifests."""

    metadata = _mapping(program.metadata)
    capacity_evidence = _merged_capacity(capacity, passport)
    gates = _mapping(hard_gates)
    law_evidence = _stage_evidence(passport, "law")
    parking_evidence = _first_mapping(
        gates.get("parking"),
        _stage_evidence(passport, "parking"),
    )
    shared_floor = _first_mapping(
        metadata.get("shared_floor_contract"),
        capacity_evidence.get("shared_floor_contract"),
        law_evidence.get("shared_floor_contract"),
    )
    totals = _mapping(shared_floor.get("totals"))
    projected = _first_mapping(
        gates.get("projectedMetrics"),
        gates.get("projected_metrics"),
        law_evidence.get("projectedMetrics"),
        law_evidence.get("projected_metrics"),
    )
    floorwise = _first_mapping(
        metadata.get("floorwise_legal_matrix_stack"),
        metadata.get("floorwise_projection"),
    )
    matrix_stack = _matrix_stack(program, compilation)
    floor_capacity_plan_hash = _first_text(
        shared_floor.get("floor_capacity_plan_hash"),
        _mapping(shared_floor.get("identity")).get("floor_capacity_plan_hash"),
        capacity_evidence.get("floor_capacity_plan_hash"),
        floorwise.get("floor_capacity_plan_hash"),
    )
    floor_contract_hash = _first_text(
        shared_floor.get("floor_contract_hash"),
        projected.get("floor_contract_hash"),
        law_evidence.get("floor_contract_hash"),
    )

    return {
        "num_floors": _first_integer(
            totals.get("num_floors"),
            floorwise.get("floor_count"),
        ),
        "floor_height_m": _first_number(
            shared_floor.get("floor_height_m"),
            _derived_floor_height(floorwise),
        ),
        "total_floor_area_m2": _first_number(
            totals.get("total_floor_area_m2"),
            projected.get("floor_area_m2"),
            capacity_evidence.get("total_floor_area_m2"),
        ),
        "bcr_pct": _first_number(
            projected.get("bcr_pct"),
            law_evidence.get("bcr_pct"),
        ),
        "far_pct": _first_number(
            projected.get("far_pct"),
            totals.get("far_pct"),
            capacity_evidence.get("far_pct"),
        ),
        "parking_required": _first_integer(
            parking_evidence.get("required_spaces"),
            _mapping(parking_evidence.get("requirement")).get("required_spaces"),
        ),
        "parking_provided": _first_integer(
            parking_evidence.get("provided_spaces"),
        ),
        "floor_contract_hash": floor_contract_hash,
        "floor_capacity_plan_hash": floor_capacity_plan_hash,
        "elevation_status": _elevation_status(passport),
        "matrix_convention": _first_text(
            floorwise.get("matrix_convention"),
            metadata.get("matrix_convention"),
            "row_major_column_vector" if matrix_stack else "",
        ),
        "floor_matrix_stack": matrix_stack,
    }


def floor_capacity_plan_hash(
    *,
    program: GeometryProgram | None = None,
    capacity: Mapping[str, Any] | None = None,
    passport: Mapping[str, Any] | None = None,
) -> str:
    """Extract the law-derived floor-plan identity without deriving a new one."""

    metadata = _mapping(program.metadata) if program is not None else {}
    capacity_evidence = _merged_capacity(capacity, passport)
    shared_floor = _first_mapping(
        metadata.get("shared_floor_contract"),
        capacity_evidence.get("shared_floor_contract"),
    )
    stack = _mapping(metadata.get("floorwise_legal_matrix_stack"))
    return _first_text(
        shared_floor.get("floor_capacity_plan_hash"),
        _mapping(shared_floor.get("identity")).get("floor_capacity_plan_hash"),
        capacity_evidence.get("floor_capacity_plan_hash"),
        stack.get("floor_capacity_plan_hash"),
    )


def _merged_capacity(
    supplied: Mapping[str, Any] | None,
    passport: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        **_stage_evidence(passport, "capacity"),
        **_mapping(supplied),
    }


def _stage_evidence(
    passport: Mapping[str, Any] | None,
    stage_id: str,
) -> dict[str, Any]:
    payload = _mapping(passport)
    for stage in payload.get("stages") or ():
        if isinstance(stage, Mapping) and str(stage.get("id") or "") == stage_id:
            return _mapping(stage.get("evidence"))
    return {}


def _matrix_stack(
    program: GeometryProgram,
    compilation: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in _mapping(compilation).get("trace") or ():
        if not isinstance(row, Mapping) or not _is_matrix4(row.get("matrix4")):
            continue
        result.append({
            "node_id": str(row.get("node_id") or ""),
            "semantic_role": "",
            "matrix4": [
                [float(value) for value in matrix_row]
                for matrix_row in row["matrix4"]
            ],
        })
    if result:
        return result
    for node in program.topological_nodes():
        if node.operator != "matrix4":
            continue
        matrix = node.parameters.get("matrix4")
        if not _is_matrix4(matrix):
            continue
        result.append({
            "node_id": node.id,
            "semantic_role": node.semantic_role,
            "matrix4": [[float(value) for value in row] for row in matrix],
        })
    return result


def _elevation_status(passport: Mapping[str, Any] | None) -> str:
    payload = _mapping(passport)
    direct = _mapping(payload.get("elevation_evidence"))
    if direct.get("status"):
        return str(direct["status"])
    graph = _mapping(payload.get("activation_graph"))
    for node in graph.get("nodes") or ():
        if (
            isinstance(node, Mapping)
            and str(node.get("id") or "") == "elevation:result"
            and node.get("status")
        ):
            return str(node["status"])
    return "not_evaluated"


def _derived_floor_height(floorwise: Mapping[str, Any]) -> float | None:
    height = _number_or_none(floorwise.get("height_m"))
    floors = _integer_or_none(floorwise.get("floor_count"))
    if height is None or floors is None or floors <= 0:
        return None
    return height / floors


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _first_number(*values: Any) -> float | None:
    for value in values:
        number = _number_or_none(value)
        if number is not None:
            return number
    return None


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _first_integer(*values: Any) -> int | None:
    for value in values:
        number = _integer_or_none(value)
        if number is not None:
            return number
    return None


def _integer_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _is_matrix4(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) == 4
        and all(
            isinstance(row, (list, tuple))
            and len(row) == 4
            and all(isinstance(item, (int, float)) for item in row)
            for row in value
        )
    )


__all__ = [
    "floor_capacity_plan_hash",
    "serialize_mass_product_evidence",
]
