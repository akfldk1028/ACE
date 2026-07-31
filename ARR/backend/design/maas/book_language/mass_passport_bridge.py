"""BOOK portfolio adapter for the core per-MASS execution passport."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from design.maas.geometry_language.execution_passport import (
    build_mass_execution_passport,
    enrich_mass_execution_passport,
)


def selected_candidate_execution_passport(
    *,
    compilation: Mapping[str, Any],
    downstream_row: Mapping[str, Any],
    source_metadata: Mapping[str, Any],
    program_evidence: Mapping[str, Any],
    descriptor: Mapping[str, Any],
    pnu: str,
) -> dict[str, Any]:
    """Merge already-computed candidate evidence; never rerun a hard gate."""

    capacity_projection = source_metadata.get("capacity_alternative_projection") or {}
    capacity_measurement = source_metadata.get("source_capacity_measurement") or {}
    shared_floor_contract = source_metadata.get("shared_floor_contract") or {}
    capacity_evidence = _resolved_capacity_evidence(
        capacity_projection=capacity_projection,
        capacity_measurement=capacity_measurement,
        shared_floor_contract=shared_floor_contract,
        descriptor=descriptor,
    )
    downstream_evidence = {
        "site": {
            **deepcopy(downstream_row.get("legal_generation_context_evidence") or {}),
            "status": "passed",
            "pnu": pnu,
        },
        "capacity": capacity_evidence,
        "law": deepcopy(downstream_row.get("legal_projection") or {}),
        "parking": deepcopy(downstream_row.get("parking_hard_gate") or {}),
        "program_fit": deepcopy(program_evidence),
        "selector": {
            "selected": True,
            "hard_pass": True,
            "selection_role": "portfolio_archive",
            "selection_effect": "none_shadow_only",
        },
    }
    vlm_audit = deepcopy(source_metadata.get("final_book_vlm_audit") or {})
    if str(vlm_audit.get("status") or "") in {"", "not_run", "not_evaluated"}:
        vlm_audit = {}
    certified_compilation = compilation.get("certified_compilation")
    if certified_compilation is not None:
        return build_mass_execution_passport(
            certified_compilation,
            vlm_result=vlm_audit or None,
            downstream_evidence=downstream_evidence,
            geometry_gate_evidence={
                "hard_pass": bool(compilation.get("combined_hard_pass")),
                "authority": "benchmark_final_hard_gates",
            },
            render_evidence=(
                compilation.get("archive_render_evidence")
                if isinstance(compilation.get("archive_render_evidence"), Mapping)
                else None
            ),
            certified_vlm_binding_required=True,
        )

    initial = deepcopy(
        downstream_row.get("mass_execution_passport")
        or compilation.get("execution_passport")
        or {}
    )
    if not initial:
        return {}
    return enrich_mass_execution_passport(
        initial,
        downstream_evidence=downstream_evidence,
        vlm_result=vlm_audit or None,
    )


def _resolved_capacity_evidence(
    *,
    capacity_projection: Mapping[str, Any],
    capacity_measurement: Mapping[str, Any],
    shared_floor_contract: Mapping[str, Any],
    descriptor: Mapping[str, Any],
) -> dict[str, Any]:
    projection = deepcopy(dict(capacity_projection or {}))
    resolution = resolve_capacity_band_evidence(
        projection,
        capacity_measurement=capacity_measurement,
        fallback_requested_hard_pass=bool(
            descriptor.get("capacity_target_hard_pass")
        ),
    )
    return {
        **projection,
        "measurement": deepcopy(dict(capacity_measurement or {})),
        "shared_floor_contract": deepcopy(dict(shared_floor_contract or {})),
        "floor_contract_hash": str(
            shared_floor_contract.get("floor_contract_hash") or ""
        ),
        "evaluated": bool(capacity_projection or capacity_measurement),
        **resolution,
        "hard_pass": resolution["resolved_capacity_hard_pass"],
        "status": (
            "passed"
            if resolution["resolved_capacity_hard_pass"]
            else "failed"
        ),
    }


def resolve_capacity_band_evidence(
    capacity_projection: Mapping[str, Any],
    *,
    capacity_measurement: Mapping[str, Any] | None = None,
    fallback_requested_hard_pass: bool = False,
) -> dict[str, Any]:
    projection = dict(capacity_projection or {})
    measurement = dict(capacity_measurement or {})
    selectable_measured = "selectable_capacity_hard_pass" in projection
    requested_id = str(
        projection.get("requested_capacity_alternative_id")
        or projection.get("alternative_id")
        or ""
    )
    requested_target = float(
        projection.get("requested_target_utilization")
        or projection.get("target_utilization")
        or 0.0
    )
    requested_hard_pass = bool(
        projection.get("target_hard_pass")
        if "target_hard_pass" in projection
        else fallback_requested_hard_pass
    )
    achieved = float(
        measurement.get("feasible_capacity_utilization")
        or measurement.get("utilization_ratio")
        or projection.get("achieved_utilization")
        or 0.0
    )
    minimum = max(
        0.70,
        float(projection.get("feasible_minimum_utilization") or 0.0),
    )
    if selectable_measured:
        resolved_id = str(
            projection.get("selectable_capacity_alternative_id") or ""
        )
        resolved_target = float(
            projection.get("selectable_capacity_target_utilization") or 0.0
        )
        resolved_hard_pass = bool(
            projection.get("selectable_capacity_hard_pass")
            and resolved_id
            and resolved_target > 0.0
            and achieved + 1e-9 >= max(minimum, resolved_target)
        )
    else:
        resolved_id = requested_id
        resolved_target = requested_target
        resolved_hard_pass = requested_hard_pass
    return {
        "requested_capacity_alternative_id": requested_id,
        "requested_capacity_target_utilization": requested_target,
        "requested_target_hard_pass": requested_hard_pass,
        "resolved_capacity_alternative_id": resolved_id,
        "resolved_capacity_target_utilization": resolved_target,
        "resolved_capacity_hard_pass": resolved_hard_pass,
        "resolved_capacity_minimum_utilization": minimum,
        "achieved_capacity_utilization": achieved,
    }


__all__ = [
    "resolve_capacity_band_evidence",
    "selected_candidate_execution_passport",
]
