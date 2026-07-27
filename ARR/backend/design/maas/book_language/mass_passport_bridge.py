"""BOOK portfolio adapter for the core per-MASS execution passport."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from design.maas.geometry_language.execution_passport import enrich_mass_execution_passport


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

    initial = deepcopy(
        downstream_row.get("mass_execution_passport")
        or compilation.get("execution_passport")
        or {}
    )
    if not initial:
        return {}
    vlm_audit = deepcopy(source_metadata.get("final_book_vlm_audit") or {})
    if str(vlm_audit.get("status") or "") in {"", "not_run", "not_evaluated"}:
        vlm_audit = {}
    capacity_projection = source_metadata.get("capacity_alternative_projection") or {}
    capacity_measurement = source_metadata.get("source_capacity_measurement") or {}
    shared_floor_contract = source_metadata.get("shared_floor_contract") or {}
    return enrich_mass_execution_passport(
        initial,
        downstream_evidence={
            "site": {
                **deepcopy(downstream_row.get("legal_generation_context_evidence") or {}),
                "status": "passed",
                "pnu": pnu,
            },
            "capacity": {
                **deepcopy(capacity_projection),
                "measurement": deepcopy(capacity_measurement),
                "shared_floor_contract": deepcopy(shared_floor_contract),
                "floor_contract_hash": str(
                    shared_floor_contract.get("floor_contract_hash") or ""
                ),
                "evaluated": bool(capacity_projection or capacity_measurement),
                "hard_pass": bool(descriptor.get("capacity_target_hard_pass")),
            },
            "law": deepcopy(downstream_row.get("legal_projection") or {}),
            "parking": deepcopy(downstream_row.get("parking_hard_gate") or {}),
            "program_fit": deepcopy(program_evidence),
            "selector": {
                "status": "evaluated",
                "selection_role": "portfolio_archive",
                "selection_effect": "none_shadow_only",
            },
        },
        vlm_result=vlm_audit or None,
    )


__all__ = ["selected_candidate_execution_passport"]
