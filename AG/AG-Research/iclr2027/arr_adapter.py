"""Convert canonical ARR portfolio artifacts into research evidence packets."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from .io import sha256_json
from .schema import ArchitectureEvidencePacket, ArchitectureGoldRecord


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUMMARY_SCHEMA = "arr.maas.book_program_portfolios.v1"
_LEDGER_SCHEMA = "arr.maas.portfolio_evaluation_ledger.v1"
_CANDIDATE_SCHEMA = "arr.maas.candidate_evaluation.v1"
_PASSPORT_SCHEMA = "arr.maas.mass_execution_passport.v1"
_PROGRESS_SCHEMA = "arr.maas.mass_progress.v1"
_COMPLETION_SCHEMA = "arr.maas.portfolio_completion.v1"
_DOWNSTREAM_SCHEMA = "arr.maas.book_downstream_hard_gate.v1"
_ATTEMPT_IDENTITY_SCHEMA = "ace.iclr2027.portfolio_attempt_identity.v2"
_ADMISSION_SCHEMA = "arr.maas.capacity_selection_admission.v1"
_ROUTING_SCHEMA = "arr.maas.program_selection_routing.v1"
_FINAL_ROUTING_SCHEMA = "arr.maas.final_vlm_applied_book_routing.v2"
_EARLY_STOP_SCHEMA = "arr.maas.program_site_early_stop.v1"
_DIMENSIONAL_SCHEMA = "arr.maas.program_dimensional_context.v1"
_ADVISORY_SCHEMA = "arr.maas.pre_generation_capacity_advisory.v1"
_FLOOR_PLAN_SCHEMA = "arr.maas.floor_capacity_plan.v1"
_TERMINAL_CERTIFICATE_SCHEMA = (
    "arr.maas.authored_visual_authority_terminal_certificate.v1"
)


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return copy.deepcopy(dict(value))


def _exact_schema(value: Mapping[str, Any], expected: str, field: str) -> None:
    if value.get("schema_version") != expected:
        raise ValueError(f"unsupported {field} schema")


def _strict_integer(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _zero_real(value: Any, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or float(value) != 0.0
    ):
        raise ValueError(f"{field} must be numeric zero")
    return float(value)


def _sha256(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not _SHA256.fullmatch(text):
        raise ValueError(f"{field} must be a lowercase SHA-256")
    return text


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be nonempty")
    return text


def _select_program(summary: Mapping[str, Any], program: str) -> dict[str, Any]:
    programs = summary.get("programs")
    if not isinstance(programs, list):
        raise ValueError("ARR summary has no programs list")
    for item in programs:
        if isinstance(item, Mapping) and str(item.get("slug") or "") == program:
            return dict(item)
    raise ValueError(f"program not found in ARR summary: {program}")


def _row_gate_results(row: Mapping[str, Any]) -> dict[str, bool]:
    """Recompute acceptance from authoritative evidence, not summary booleans."""

    finalization = row.get("candidate_finalization_evidence")
    legal = row.get("legal_projection")
    law = row.get("law_graph_agent_evidence")
    parking = row.get("parking_hard_gate")
    semantic = row.get("semantic_projection_hard_gate")
    parking_required = (
        int(parking.get("required_spaces"))
        if isinstance(parking, Mapping)
        and parking.get("required_spaces") is not None
        else -1
    )
    parking_provided = (
        int(parking.get("provided_spaces"))
        if isinstance(parking, Mapping)
        and parking.get("provided_spaces") is not None
        else -1
    )
    return {
        "inside_site": row.get("inside_site") is True,
        "finalization": bool(
            isinstance(finalization, Mapping)
            and finalization.get("status") == "certified"
            and finalization.get("hard_pass") is True
        ),
        "legal_projection": bool(
            isinstance(legal, Mapping) and legal.get("hard_pass") is True
        ),
        "law_graph": bool(
            isinstance(law, Mapping) and law.get("status") == "passed"
        ),
        "parking": bool(
            isinstance(parking, Mapping)
            and parking.get("evaluated") is True
            and parking.get("hard_pass") is True
            and parking_required >= 0
            and parking_provided >= parking_required
        ),
        "program": row.get("program_hard_pass") is True,
        "semantic_projection": bool(
            isinstance(semantic, Mapping) and semantic.get("hard_pass") is True
        ),
    }


def _select_row(program_record: Mapping[str, Any]) -> dict[str, Any]:
    rows = program_record.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("ARR program has no candidate rows")
    candidates = [dict(row) for row in rows if isinstance(row, Mapping)]
    if not candidates:
        raise ValueError("ARR program rows are malformed")

    def rank(row: Mapping[str, Any]) -> tuple[bool, int, float, str]:
        gates = _row_gate_results(row)
        return (
            all(gates.values()),
            sum(gates.values()),
            float(row.get("score") or 0.0),
            str(row.get("selected_execution_id") or row.get("variant_id") or ""),
        )

    return max(
        candidates,
        key=rank,
    )


def _verify_identity(
    row: Mapping[str, Any],
    *,
    pnu: str,
) -> tuple[str, str, str]:
    execution_id = str(row.get("selected_execution_id") or "").strip()
    program_hash = str(row.get("final_legal_program_hash") or "").strip()
    geometry_hash = str(row.get("final_legal_geometry_hash") or "").strip()
    passport = _mapping(row.get("mass_execution_passport"), "mass_execution_passport")
    if str(passport.get("program_hash") or "") != program_hash:
        raise ValueError("passport program hash mismatch")
    if str(passport.get("final_legal_geometry_hash") or "") != geometry_hash:
        raise ValueError("passport geometry hash mismatch")

    law = _mapping(row.get("law_graph_agent_evidence"), "law_graph_agent_evidence")
    law_identity = _mapping(law.get("identity"), "law_graph_agent_evidence.identity")
    expected_identity = {
        "execution_id": execution_id,
        "program_hash": program_hash,
        "geometry_hash": geometry_hash,
        "pnu": pnu,
    }
    for key, expected in expected_identity.items():
        if str(law_identity.get(key) or "") != expected:
            raise ValueError(f"law evidence {key} mismatch")

    parking = _mapping(row.get("parking_hard_gate"), "parking_hard_gate")
    if str(parking.get("geometry_hash") or "") != geometry_hash:
        raise ValueError("parking geometry hash mismatch")
    return execution_id, program_hash, geometry_hash


def _status(passed: bool) -> str:
    return "passed" if passed else "failed"


def _build_evidence(
    row: Mapping[str, Any],
    *,
    pnu: str,
) -> tuple[dict[str, Any], ...]:
    finalization = _mapping(
        row.get("candidate_finalization_evidence"),
        "candidate_finalization_evidence",
    )
    legal_projection = _mapping(row.get("legal_projection"), "legal_projection")
    law = _mapping(row.get("law_graph_agent_evidence"), "law_graph_agent_evidence")
    parking = _mapping(row.get("parking_hard_gate"), "parking_hard_gate")
    semantic = _mapping(
        row.get("semantic_projection_hard_gate"),
        "semantic_projection_hard_gate",
    )

    gates = _row_gate_results(row)
    geometry_pass = gates["inside_site"] and gates["finalization"]
    law_pass = gates["law_graph"] and gates["legal_projection"]
    parking_pass = gates["parking"]
    program_pass = gates["program"] and gates["semantic_projection"]
    combined_pass = geometry_pass and law_pass and parking_pass and program_pass

    law["evidence_id"] = "evidence:law_graph_agent"
    law["domain"] = "law"
    law_payload = law.get("evidence")
    if not isinstance(law_payload, Mapping):
        law_payload = {}
    law["evidence"] = {
        **copy.deepcopy(dict(law_payload)),
        "legal_projection": legal_projection,
    }
    return (
        {
            "evidence_id": "evidence:site_agent",
            "domain": "site",
            "status": _status(gates["inside_site"]),
            "evidence": {
                "pnu": pnu,
                "inside_site": row.get("inside_site"),
                "geometry_hash": row.get("final_legal_geometry_hash"),
            },
        },
        {
            "evidence_id": "evidence:geometry_agent",
            "domain": "geometry",
            "status": _status(geometry_pass),
            "evidence": finalization,
        },
        law,
        {
            "evidence_id": "evidence:parking_agent",
            "domain": "parking",
            "status": _status(parking_pass),
            "evidence": parking,
        },
        {
            "evidence_id": "evidence:program_agent",
            "domain": "program",
            "status": _status(program_pass),
            "evidence": {
                "semantic_projection": semantic,
                "candidate_target_gfa_m2": finalization.get(
                    "candidate_target_gfa_m2"
                ),
                "achieved_gfa_m2": finalization.get("achieved_gfa_m2"),
            },
        },
        {
            "evidence_id": "evidence:review_agent",
            "domain": "review",
            "status": _status(combined_pass),
            "evidence": {
                "combined_hard_pass": combined_pass,
                "reported_combined_hard_pass": row.get("combined_hard_pass"),
                "independent_gate_results": gates,
                "review_status": row.get("review_status"),
                "review_reasons": copy.deepcopy(row.get("review_reasons") or []),
            },
        },
    )


def _blocking_issues(evidence: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    issue_by_evidence = {
        "evidence:geometry_agent": "geometry.compilation_failed",
        "evidence:law_graph_agent": "law.projection_failed",
        "evidence:parking_agent": "parking.supply_shortage",
        "evidence:program_agent": "program.capacity_failed",
        "evidence:review_agent": "review.combined_gate_failed",
    }
    return tuple(
        issue_by_evidence[item["evidence_id"]]
        for item in evidence
        if item.get("status") != "passed"
    )


def _attempt_candidate_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    _exact_schema(record, _CANDIDATE_SCHEMA, "candidate evaluation")
    candidate_id = _required_text(record.get("candidate_id"), "candidate_id")
    program_hash = _sha256(record.get("program_hash"), "candidate program_hash")
    geometry_hash = _sha256(record.get("geometry_hash"), "candidate geometry_hash")
    if record.get("selected") is not False:
        raise ValueError("portfolio attempt candidate must not be selected")
    for field in (
        "selected_execution_id",
        "final_legal_program_hash",
        "final_legal_geometry_hash",
    ):
        if record.get(field) is not None:
            raise ValueError(f"portfolio attempt candidate has final identity: {field}")

    stages = _mapping(record.get("stages"), "candidate stages")
    required_stages = {"geometry", "law", "parking", "selection"}
    if not required_stages.issubset(stages):
        raise ValueError("portfolio attempt candidate stages are incomplete")
    geometry = _mapping(stages.get("geometry"), "candidate geometry stage")
    law = _mapping(stages.get("law"), "candidate law stage")
    parking = _mapping(stages.get("parking"), "candidate parking stage")
    selection = _mapping(stages.get("selection"), "candidate selection stage")
    if geometry.get("stage") != "geometry" or geometry.get("status") != "pass":
        raise ValueError("portfolio attempt geometry stage is invalid")
    if law.get("stage") != "law" or law.get("status") != "not_evaluated":
        raise ValueError("portfolio attempt law stage must be not_evaluated")
    if parking.get("stage") != "parking" or parking.get("status") != "not_evaluated":
        raise ValueError("portfolio attempt parking stage must be not_evaluated")
    if selection.get("stage") != "selection" or selection.get("status") != "fail":
        raise ValueError("portfolio attempt selection stage must fail")
    selection_reasons = selection.get("reasons")
    if (
        not isinstance(selection_reasons, list)
        or not selection_reasons
        or any(not str(reason).strip() for reason in selection_reasons)
    ):
        raise ValueError("portfolio attempt selection reasons are incomplete")

    geometry_evidence = _mapping(
        geometry.get("evidence"), "candidate geometry evidence"
    )
    passport = _mapping(
        geometry_evidence.get("execution_passport"), "candidate execution passport"
    )
    _exact_schema(passport, _PASSPORT_SCHEMA, "execution passport")
    if passport.get("status") != "in_progress":
        raise ValueError("portfolio attempt passport must be in_progress")
    if passport.get("program_hash") != program_hash:
        raise ValueError("portfolio attempt passport program hash mismatch")
    if passport.get("geometry_hash") != geometry_hash:
        raise ValueError("portfolio attempt passport geometry hash mismatch")
    if (
        passport.get("execution_id") is not None
        or passport.get("final_legal_geometry_hash") is not None
    ):
        raise ValueError("portfolio attempt passport contains final execution identity")

    return {
        "candidate_id": candidate_id,
        "program_hash": program_hash,
        "geometry_hash": geometry_hash,
        "selected": False,
        "selection_status": "fail",
        "selection_reason_count": len(selection_reasons),
        "passport_status": "in_progress",
        "execution_id": None,
        "final_legal_geometry_hash": None,
    }


def _build_selection_attempt(
    summary: Mapping[str, Any],
    program_record: Mapping[str, Any],
    *,
    source_artifact_sha256: str,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    _exact_schema(summary, _SUMMARY_SCHEMA, "ARR summary")
    rows = program_record.get("rows")
    if not isinstance(rows, list) or rows:
        raise ValueError("portfolio attempt requires exactly zero admitted rows")
    if _strict_integer(program_record.get("selected_count"), "selected_count") != 0:
        raise ValueError("portfolio attempt selected_count must be zero")

    progress = _mapping(program_record.get("mass_progress"), "mass_progress")
    _exact_schema(progress, _PROGRESS_SCHEMA, "mass progress")
    evaluated_count = _strict_integer(
        progress.get("evaluated_count"), "evaluated_count", minimum=1
    )
    compiled_count = _strict_integer(
        progress.get("compiled_count"), "compiled_count", minimum=1
    )
    if compiled_count > evaluated_count:
        raise ValueError("compiled_count exceeds evaluated_count")

    completion = _mapping(
        program_record.get("portfolio_completion"), "portfolio_completion"
    )
    _exact_schema(completion, _COMPLETION_SCHEMA, "portfolio completion")
    if (
        completion.get("hard_pass") is not False
        or _strict_integer(
            completion.get("selected_count"), "completion selected_count"
        )
        != 0
        or completion.get("diagnostic_only") is not True
    ):
        raise ValueError("portfolio completion is not a zero-admission diagnostic")

    downstream = _mapping(
        program_record.get("downstream_hard_gate"), "downstream_hard_gate"
    )
    _exact_schema(downstream, _DOWNSTREAM_SCHEMA, "downstream hard gate")
    downstream_rows = downstream.get("rows")
    if (
        downstream.get("status") != "fail"
        or _strict_integer(
            downstream.get("candidate_count"), "downstream candidate_count"
        )
        != 0
        or not isinstance(downstream_rows, list)
        or downstream_rows
    ):
        raise ValueError("downstream hard gate must contain zero admitted rows")

    ledger = _mapping(
        program_record.get("portfolio_evaluation"), "portfolio_evaluation"
    )
    _exact_schema(ledger, _LEDGER_SCHEMA, "portfolio evaluation ledger")
    if str(ledger.get("pnu") or "") != pnu:
        raise ValueError("portfolio evaluation PNU mismatch")
    if str(ledger.get("program_slug") or "") != program:
        raise ValueError("portfolio evaluation program mismatch")
    _required_text(ledger.get("run_id"), "portfolio evaluation run_id")
    records = ledger.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("portfolio evaluation records must not be empty")
    record_count = _strict_integer(
        ledger.get("record_count"), "portfolio evaluation record_count", minimum=1
    )
    target_count = _strict_integer(
        ledger.get("target_count"), "portfolio evaluation target_count", minimum=1
    )
    if record_count != len(records) or target_count != record_count:
        raise ValueError("portfolio evaluation counts do not match complete records")
    if ledger.get("records_truncated") is not False:
        raise ValueError("portfolio evaluation ledger must be untruncated")

    candidates = [
        _attempt_candidate_identity(_mapping(record, "candidate evaluation"))
        for record in records
    ]
    for field in ("candidate_id", "program_hash", "geometry_hash"):
        values = [candidate[field] for candidate in candidates]
        if len(values) != len(set(values)):
            raise ValueError(f"portfolio attempt contains duplicate {field}")
    candidates.sort(key=lambda candidate: candidate["candidate_id"])

    attempt_manifest = {
        "schema_version": _ATTEMPT_IDENTITY_SCHEMA,
        "source_artifact_sha256": source_artifact_sha256,
        "source_schema_version": _SUMMARY_SCHEMA,
        "program": program,
        "attempt_stage": "selection",
        "route_kind": None,
        "selected_count": 0,
        "row_count": 0,
        "target_count": target_count,
        "record_count": record_count,
        "records_truncated": False,
        "mass_progress": {
            "schema_version": _PROGRESS_SCHEMA,
            "evaluated_count": evaluated_count,
            "compiled_count": compiled_count,
        },
        "portfolio_completion": {
            "schema_version": _COMPLETION_SCHEMA,
            "hard_pass": False,
            "selected_count": 0,
            "diagnostic_only": True,
        },
        "downstream_hard_gate": {
            "schema_version": _DOWNSTREAM_SCHEMA,
            "status": "fail",
            "candidate_count": 0,
            "row_count": 0,
        },
        "candidates": candidates,
    }
    attempt_id = "attempt:" + sha256_json(
        {
            "source_artifact_sha256": source_artifact_sha256,
            "program": program,
            "attempt_stage": "selection",
        }
    )
    evidence = (
        {
            "evidence_id": "evidence:portfolio_attempt",
            "domain": "program",
            "status": "failed",
            "evidence": attempt_manifest,
        },
    )
    packet = ArchitectureEvidencePacket(
        case_id=case_id,
        pnu=pnu,
        program=program,  # type: ignore[arg-type]
        condition="native",
        execution_id=None,
        program_hash=None,
        geometry_hash=None,
        evidence=evidence,
        subject_kind="portfolio_attempt",
        source_artifact_sha256=source_artifact_sha256,
        attempt_id=attempt_id,
        attempt_hash=sha256_json(attempt_manifest),
        attempt_stage="selection",
        route_kind=None,
    )
    from .validators import gold_from_validation

    return packet, gold_from_validation(packet, mutation_family="")


def _zero_admission_common(
    program_record: Mapping[str, Any],
    *,
    minimum_evaluated: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = program_record.get("rows")
    if not isinstance(rows, list) or rows:
        raise ValueError("portfolio attempt requires exactly zero admitted rows")
    if _strict_integer(program_record.get("selected_count"), "selected_count") != 0:
        raise ValueError("portfolio attempt selected_count must be zero")

    progress = _mapping(program_record.get("mass_progress"), "mass_progress")
    _exact_schema(progress, _PROGRESS_SCHEMA, "mass progress")
    evaluated = _strict_integer(
        progress.get("evaluated_count"),
        "mass progress evaluated_count",
        minimum=minimum_evaluated,
    )
    compiled = _strict_integer(
        progress.get("compiled_count"), "mass progress compiled_count"
    )
    individual = _strict_integer(
        progress.get("individual_hard_pass_count"),
        "mass progress individual_hard_pass_count",
    )
    compatible = _strict_integer(
        progress.get("compatible_selected_count"),
        "mass progress compatible_selected_count",
    )
    if compiled > evaluated:
        raise ValueError("compiled_count exceeds evaluated_count")

    completion = _mapping(
        program_record.get("portfolio_completion"), "portfolio_completion"
    )
    _exact_schema(completion, _COMPLETION_SCHEMA, "portfolio completion")
    if (
        completion.get("hard_pass") is not False
        or _strict_integer(
            completion.get("selected_count"), "completion selected_count"
        )
        != 0
        or _strict_integer(
            completion.get("selected_scope_count"),
            "completion selected_scope_count",
        )
        != 0
        or completion.get("diagnostic_only") is not True
    ):
        raise ValueError("portfolio completion is not a zero-admission diagnostic")

    downstream = _mapping(
        program_record.get("downstream_hard_gate"), "downstream_hard_gate"
    )
    _exact_schema(downstream, _DOWNSTREAM_SCHEMA, "downstream hard gate")
    downstream_rows = downstream.get("rows")
    if (
        downstream.get("status") != "fail"
        or _strict_integer(
            downstream.get("candidate_count"), "downstream candidate_count"
        )
        != 0
        or not isinstance(downstream_rows, list)
        or downstream_rows
    ):
        raise ValueError("downstream hard gate must contain zero admitted rows")
    return progress, completion, downstream, {
        "evaluated_count": evaluated,
        "compiled_count": compiled,
        "individual_hard_pass_count": individual,
        "compatible_selected_count": compatible,
    }


def _zero_ledger(
    program_record: Mapping[str, Any], *, pnu: str, program: str
) -> dict[str, Any]:
    ledger = _mapping(
        program_record.get("portfolio_evaluation"), "portfolio_evaluation"
    )
    _exact_schema(ledger, _LEDGER_SCHEMA, "portfolio evaluation ledger")
    if ledger.get("pnu") != pnu or ledger.get("program_slug") != program:
        raise ValueError("portfolio evaluation private identity mismatch")
    _required_text(ledger.get("run_id"), "portfolio evaluation run_id")
    records = ledger.get("records")
    if not isinstance(records, list) or records:
        raise ValueError("zero-row portfolio evaluation records must be empty")
    if (
        _strict_integer(ledger.get("target_count"), "portfolio target_count") != 3
        or _strict_integer(ledger.get("record_count"), "portfolio record_count")
        != 0
        or ledger.get("records_truncated") is not False
    ):
        raise ValueError("zero-row portfolio ledger is incomplete")
    return ledger


def _zero_downstream_counts(downstream: Mapping[str, Any]) -> None:
    for field in (
        "legal_hard_pass_count",
        "geometry_retention_pass_count",
        "parking_hard_pass_count",
        "capacity_hard_pass_count",
        "combined_hard_pass_count",
    ):
        if _strict_integer(downstream.get(field), f"downstream {field}") != 0:
            raise ValueError("downstream hard-pass counts must all be zero")


def _attempt_packet(
    *,
    source_artifact_sha256: str,
    pnu: str,
    program: str,
    case_id: str,
    stage: str,
    route_kind: str | None,
    status: str,
    manifest: Mapping[str, Any],
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    attempt_id = "attempt:" + sha256_json(
        {
            "source_artifact_sha256": source_artifact_sha256,
            "program": program,
            "attempt_stage": stage,
        }
    )
    packet = ArchitectureEvidencePacket(
        case_id=case_id,
        pnu=pnu,
        program=program,  # type: ignore[arg-type]
        condition="native",
        execution_id=None,
        program_hash=None,
        geometry_hash=None,
        evidence=(
            {
                "evidence_id": "evidence:portfolio_attempt",
                "domain": "program",
                "status": status,
                "evidence": dict(manifest),
            },
        ),
        subject_kind="portfolio_attempt",
        source_artifact_sha256=source_artifact_sha256,
        attempt_id=attempt_id,
        attempt_hash=sha256_json(manifest),
        attempt_stage=stage,  # type: ignore[arg-type]
        route_kind=route_kind,  # type: ignore[arg-type]
    )
    from .validators import gold_from_validation

    return packet, gold_from_validation(packet, mutation_family="")


def _base_attempt_manifest(
    *,
    source_artifact_sha256: str,
    program: str,
    stage: str,
    route_kind: str | None,
    progress_counts: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": _ATTEMPT_IDENTITY_SCHEMA,
        "source_artifact_sha256": source_artifact_sha256,
        "source_schema_version": _SUMMARY_SCHEMA,
        "program": program,
        "attempt_stage": stage,
        "route_kind": route_kind,
        "selected_count": 0,
        "row_count": 0,
        "mass_progress": {
            "schema_version": _PROGRESS_SCHEMA,
            **dict(progress_counts),
        },
        "portfolio_completion": {
            "schema_version": _COMPLETION_SCHEMA,
            "hard_pass": False,
            "selected_count": 0,
            "selected_scope_count": 0,
            "diagnostic_only": True,
        },
        "downstream_hard_gate": {
            "schema_version": _DOWNSTREAM_SCHEMA,
            "status": "fail",
            "candidate_count": 0,
            "row_count": 0,
        },
    }


def _build_materialization_attempt(
    summary: Mapping[str, Any],
    program_record: Mapping[str, Any],
    *,
    source_artifact_sha256: str,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    _exact_schema(summary, _SUMMARY_SCHEMA, "ARR summary")
    progress, _, downstream, progress_counts = _zero_admission_common(
        program_record, minimum_evaluated=1
    )
    _zero_downstream_counts(downstream)
    _zero_ledger(program_record, pnu=pnu, program=program)
    if (
        progress_counts["individual_hard_pass_count"] != 0
        or progress_counts["compatible_selected_count"] != 0
    ):
        raise ValueError("materialization attempt cannot contain admitted hard passes")

    counts = _mapping(program_record.get("counts"), "counts")
    evaluated = _strict_integer(counts.get("evaluated"), "counts evaluated", minimum=1)
    compiled = _strict_integer(counts.get("compiled"), "counts compiled")
    if (
        evaluated != progress_counts["evaluated_count"]
        or compiled != progress_counts["compiled_count"]
    ):
        raise ValueError("materialization mass/count totals disagree")

    signatures: list[str] = []
    terminal_count = _strict_integer(
        counts.get("terminal_materialization_failure_count"),
        "terminal materialization failure count",
    )
    exact_count = _strict_integer(
        counts.get("exact_compile_invocation_count"), "exact compile invocation count"
    )
    materialization_count = _strict_integer(
        counts.get("materialization_invocation_count"),
        "materialization invocation count",
    )
    failures = counts.get("terminal_materialization_failures")
    reason_counts = counts.get("terminal_materialization_failure_reason_counts")
    if terminal_count > 0 and compiled == 0:
        if not isinstance(failures, list) or not isinstance(reason_counts, Mapping):
            raise ValueError("terminal materialization ledger is malformed")
        if not (
            evaluated
            == exact_count
            == materialization_count
            == terminal_count
            == len(failures)
            == sum(
                _strict_integer(value, "terminal failure reason count")
                for value in reason_counts.values()
            )
        ):
            raise ValueError("terminal materialization count equation failed")
        for failure in failures:
            failure_record = _mapping(failure, "terminal materialization failure")
            certificate = _mapping(
                failure_record.get("terminal_certificate_evidence"),
                "terminal materialization certificate",
            )
            _exact_schema(
                certificate,
                _TERMINAL_CERTIFICATE_SCHEMA,
                "terminal materialization certificate",
            )
            _sha256(certificate.get("program_hash"), "terminal program_hash")
        stage_counts = _mapping(
            counts.get("capacity_stage_counts"), "capacity stage counts"
        )
        if _strict_integer(
            stage_counts.get("qd_stream_candidates_released"),
            "qd_stream_candidates_released",
        ) != 0:
            raise ValueError("terminal materialization released a candidate")
        signatures.append("all_invocations_failed")

    admission = _mapping(
        counts.get("capacity_selection_admission"), "capacity selection admission"
    )
    _exact_schema(admission, _ADMISSION_SCHEMA, "capacity selection admission")
    exclusions = admission.get("exclusions")
    retained_count = _strict_integer(
        admission.get("retained_count"), "capacity admission retained_count"
    )
    excluded_count = _strict_integer(
        admission.get("excluded_count"), "capacity admission excluded_count"
    )
    if (
        admission.get("status") == "pass"
        and admission.get("hard_pass_required") is True
        and retained_count == 0
        and isinstance(exclusions, list)
        and excluded_count == len(exclusions)
        and len(exclusions) > 0
    ):
        for exclusion in exclusions:
            exclusion_record = _mapping(exclusion, "capacity admission exclusion")
            _required_text(
                exclusion_record.get("reason"), "capacity admission exclusion reason"
            )
            _required_text(
                exclusion_record.get("resolved_capacity_alternative_id"),
                "capacity admission alternative",
            )
            for field in (
                "achieved_capacity_utilization",
                "minimum_capacity_utilization",
            ):
                value = exclusion_record.get(field)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or float(value) < 0.0
                ):
                    raise ValueError(f"capacity admission {field} is invalid")
        signatures.append("capacity_admission_empty")

    final_routing: Mapping[str, Any] = {}
    routing = _mapping(
        counts.get("program_selection_routing"), "program selection routing"
    )
    _exact_schema(routing, _ROUTING_SCHEMA, "program selection routing")
    routing_input = _strict_integer(routing.get("input_count"), "routing input_count")
    canonical_hard_pass_count = _strict_integer(
        routing.get("canonical_hard_pass_count"), "canonical hard pass count"
    )
    development_only_excluded_count = _strict_integer(
        routing.get("development_only_excluded_count"),
        "development-only excluded count",
    )
    if (
        routing_input > 0
        and canonical_hard_pass_count == 0
        and development_only_excluded_count == routing_input
    ):
        final_routing = _mapping(counts.get("final_vlm_routing"), "final VLM routing")
        _exact_schema(final_routing, _FINAL_ROUTING_SCHEMA, "final VLM routing")
        for field in (
            "input_count",
            "row_count",
            "combined_hard_pass_count",
            "routed_applied_book_candidate_count",
        ):
            if _strict_integer(final_routing.get(field), f"final routing {field}") != 0:
                raise ValueError("final routing counts must be zero")
        signatures.append("program_routing_empty")

    if len(signatures) != 1:
        raise ValueError("materialization route signature must be unique")
    route_kind = signatures[0]
    manifest = _base_attempt_manifest(
        source_artifact_sha256=source_artifact_sha256,
        program=program,
        stage="materialization",
        route_kind=route_kind,
        progress_counts=progress_counts,
    )
    manifest["ledger"] = {
        "schema_version": _LEDGER_SCHEMA,
        "target_count": 3,
        "record_count": 0,
        "records_truncated": False,
    }
    stage_evidence: dict[str, Any] = {
        "evaluated_count": evaluated,
        "compiled_count": compiled,
        "route_kind": route_kind,
    }
    if route_kind == "all_invocations_failed":
        stage_evidence.update(
            {
                "exact_compile_invocation_count": exact_count,
                "materialization_invocation_count": materialization_count,
                "terminal_failure_count": terminal_count,
                "terminal_failure_record_count": len(failures),
                "terminal_failure_reason_total": sum(reason_counts.values()),
                "qd_stream_candidates_released": 0,
            }
        )
    elif route_kind == "capacity_admission_empty":
        stage_evidence.update(
            {
                "admission_schema_version": _ADMISSION_SCHEMA,
                "admission_status": "pass",
                "hard_pass_required": True,
                "retained_count": 0,
                "excluded_count": len(exclusions),
            }
        )
    else:
        stage_evidence.update(
            {
                "routing_schema_version": _ROUTING_SCHEMA,
                "routing_input_count": routing_input,
                "canonical_hard_pass_count": 0,
                "development_only_excluded_count": routing_input,
                "final_routing_schema_version": _FINAL_ROUTING_SCHEMA,
                "final_input_count": final_routing["input_count"],
                "final_row_count": final_routing["row_count"],
                "final_combined_hard_pass_count": final_routing[
                    "combined_hard_pass_count"
                ],
                "final_routed_candidate_count": final_routing[
                    "routed_applied_book_candidate_count"
                ],
            }
        )
    manifest["stage_evidence"] = stage_evidence
    return _attempt_packet(
        source_artifact_sha256=source_artifact_sha256,
        pnu=pnu,
        program=program,
        case_id=case_id,
        stage="materialization",
        route_kind=route_kind,
        status="failed",
        manifest=manifest,
    )


def _floor_plan_identity(plan: Mapping[str, Any], *, program: str) -> tuple[str, str]:
    _exact_schema(plan, _FLOOR_PLAN_SCHEMA, "floor capacity plan")
    if plan.get("status") != "materialized" or plan.get("program_id") != program:
        raise ValueError("floor capacity plan identity mismatch")
    return (
        _sha256(plan.get("floor_capacity_plan_hash"), "floor capacity plan hash"),
        _sha256(plan.get("legal_floor_field_hash"), "legal floor field hash"),
    )


def _build_preflight_attempt(
    summary: Mapping[str, Any],
    program_record: Mapping[str, Any],
    *,
    source_artifact_sha256: str,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    _exact_schema(summary, _SUMMARY_SCHEMA, "ARR summary")
    if program_record.get("generation_status") != "program_site_infeasible":
        raise ValueError("preflight attempt status mismatch")
    if "portfolio_evaluation" in program_record:
        raise ValueError("preflight attempt must not contain an execution ledger")
    _, _, downstream, progress_counts = _zero_admission_common(
        program_record, minimum_evaluated=0
    )
    if any(progress_counts.values()):
        raise ValueError("preflight mass progress counts must all be zero")
    for field in (
        "legal_hard_pass_count",
        "geometry_retention_pass_count",
        "parking_hard_pass_count",
        "combined_hard_pass_count",
    ):
        if _strict_integer(downstream.get(field), f"downstream {field}") != 0:
            raise ValueError("preflight downstream counts must all be zero")
    if downstream.get("failure_reasons") != ["program_site_infeasible"]:
        raise ValueError("preflight downstream status is inconsistent")

    counts = _mapping(program_record.get("counts"), "counts")
    for field in ("evaluated", "compiled", "clean", "program_passed"):
        if _strict_integer(counts.get(field), f"counts {field}") != 0:
            raise ValueError("preflight generation counts must all be zero")
    selection_trace = _mapping(counts.get("selection_trace"), "selection trace")
    for field in ("raw_pool_count", "unique_candidate_count", "post_rebalance_count"):
        if _strict_integer(selection_trace.get(field), f"selection trace {field}") != 0:
            raise ValueError("preflight selection counts must all be zero")

    early_stop = _mapping(counts.get("early_stop"), "early stop")
    _exact_schema(early_stop, _EARLY_STOP_SCHEMA, "early stop")
    if (
        early_stop.get("status") != "program_site_infeasible"
        or early_stop.get("generation_attempted") is not False
        or any(
            _strict_integer(early_stop.get(field), f"early stop {field}") != 0
            for field in (
                "evaluated_count",
                "compiled_count",
                "clean_count",
                "program_passed_count",
            )
        )
    ):
        raise ValueError("preflight early-stop record is inconsistent")

    context = _mapping(
        program_record.get("program_dimensional_context"),
        "program dimensional context",
    )
    _exact_schema(context, _DIMENSIONAL_SCHEMA, "program dimensional context")
    reasons = context.get("failure_reasons")
    if (
        context.get("program_id") != program
        or context.get("status") != "infeasible"
        or context.get("selected_subtype") != "none"
        or _strict_integer(
            context.get("effective_floors"), "effective floor count"
        )
        != 0
        or _zero_real(context.get("effective_height_m"), "effective height") != 0.0
        or not isinstance(reasons, list)
        or not reasons
    ):
        raise ValueError("preflight dimensional context is inconsistent")
    plan_hash = _sha256(context.get("floor_capacity_plan_hash"), "context plan hash")
    advisory = _mapping(
        context.get("pre_generation_capacity_advisory"), "preflight advisory"
    )
    _exact_schema(advisory, _ADVISORY_SCHEMA, "preflight advisory")
    if (
        advisory.get("authority") != "diagnostic_only"
        or advisory.get("generation_continued") is not False
        or advisory.get("dimensional_context_infeasible") is not True
        or advisory.get("floor_capacity_plan_infeasible") is not False
        or advisory.get("failure_reasons") != reasons
    ):
        raise ValueError("preflight advisory is inconsistent")
    floor_plan = _mapping(counts.get("floor_capacity_plan"), "floor capacity plan")
    observed_plan_hash, legal_hash = _floor_plan_identity(floor_plan, program=program)
    if observed_plan_hash != plan_hash:
        raise ValueError("preflight floor plan hash mismatch")
    embedded_context = _mapping(
        early_stop.get("dimensional_evidence"), "early stop dimensional evidence"
    )
    embedded_plan = _mapping(
        early_stop.get("floor_capacity_plan_evidence"),
        "early stop floor capacity plan evidence",
    )
    _exact_schema(embedded_context, _DIMENSIONAL_SCHEMA, "embedded dimensional context")
    embedded_plan_hash, embedded_legal_hash = _floor_plan_identity(
        embedded_plan, program=program
    )
    counts_context = _mapping(
        counts.get("program_dimensional_context"),
        "counts program dimensional context",
    )
    if (
        counts_context != context
        or embedded_context != context
        or embedded_plan != floor_plan
        or embedded_context.get("program_id") != program
        or embedded_context.get("status") != "infeasible"
        or embedded_context.get("floor_capacity_plan_hash") != plan_hash
        or embedded_plan_hash != plan_hash
        or embedded_legal_hash != legal_hash
    ):
        raise ValueError("preflight embedded evidence identity mismatch")

    manifest = _base_attempt_manifest(
        source_artifact_sha256=source_artifact_sha256,
        program=program,
        stage="preflight",
        route_kind=None,
        progress_counts=progress_counts,
    )
    manifest["stage_evidence"] = {
        "early_stop_schema_version": _EARLY_STOP_SCHEMA,
        "early_stop_status": "program_site_infeasible",
        "generation_attempted": False,
        "dimensional_context_schema_version": _DIMENSIONAL_SCHEMA,
        "dimensional_context_status": "infeasible",
        "selected_subtype": "none",
        "effective_floor_count": 0,
        "effective_height_m": 0.0,
        "advisory_schema_version": _ADVISORY_SCHEMA,
        "advisory_authority": "diagnostic_only",
        "dimensional_context_infeasible": True,
        "floor_capacity_plan_infeasible": False,
        "failure_reason_count": len(reasons),
        "floor_capacity_plan_schema_version": _FLOOR_PLAN_SCHEMA,
        "floor_capacity_plan_status": "materialized",
        "floor_capacity_plan_hash": plan_hash,
        "legal_floor_field_hash": legal_hash,
    }
    return _attempt_packet(
        source_artifact_sha256=source_artifact_sha256,
        pnu=pnu,
        program=program,
        case_id=case_id,
        stage="preflight",
        route_kind=None,
        status="failed",
        manifest=manifest,
    )


def _build_candidate_floor_context_attempt(
    summary: Mapping[str, Any],
    program_record: Mapping[str, Any],
    *,
    source_artifact_sha256: str,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    _exact_schema(summary, _SUMMARY_SCHEMA, "ARR summary")
    _, _, downstream, progress_counts = _zero_admission_common(
        program_record, minimum_evaluated=1
    )
    _zero_downstream_counts(downstream)
    _zero_ledger(program_record, pnu=pnu, program=program)
    if (
        progress_counts["compiled_count"] != 0
        or progress_counts["individual_hard_pass_count"] != 0
        or progress_counts["compatible_selected_count"] != 0
    ):
        raise ValueError("candidate floor context mass counts are inconsistent")
    counts = _mapping(program_record.get("counts"), "counts")
    evaluated = _strict_integer(counts.get("evaluated"), "counts evaluated", minimum=1)
    if evaluated != progress_counts["evaluated_count"]:
        raise ValueError("candidate floor context evaluated counts disagree")
    for field in (
        "compiled",
        "clean",
        "program_passed",
        "exact_compile_invocation_count",
        "materialization_invocation_count",
        "terminal_materialization_failure_count",
    ):
        if _strict_integer(counts.get(field), f"counts {field}") != 0:
            raise ValueError("candidate floor context downstream counts must be zero")
    stage_counts = _mapping(counts.get("capacity_stage_counts"), "capacity stage counts")
    if (
        _strict_integer(
            stage_counts.get("candidate_floor_context_failed"),
            "candidate floor context failed",
            minimum=1,
        )
        != evaluated
        or _strict_integer(
            stage_counts.get("qd_stream_candidates_released"),
            "qd stream candidates released",
        )
        != 0
        or _strict_integer(
            stage_counts.get("qd_stream_compaction_count"),
            "qd stream compaction count",
        )
        != 0
        or _strict_integer(
            stage_counts.get("qd_stream_peak_candidate_count"),
            "qd stream peak candidate count",
        )
        != 0
    ):
        raise ValueError("candidate floor context aggregate is inconsistent")
    for field, schema in (
        ("capacity_selection_admission", _ADMISSION_SCHEMA),
        ("program_selection_routing", _ROUTING_SCHEMA),
        ("final_vlm_routing", _FINAL_ROUTING_SCHEMA),
    ):
        _exact_schema(_mapping(counts.get(field), field), schema, field)
    admission = _mapping(
        counts.get("capacity_selection_admission"), "capacity selection admission"
    )
    if (
        admission.get("status") != "pass"
        or admission.get("hard_pass_required") is not True
        or _strict_integer(
            admission.get("retained_count"), "candidate floor admission retained_count"
        )
        != 0
        or _strict_integer(
            admission.get("excluded_count"), "candidate floor admission excluded_count"
        )
        != 0
        or admission.get("exclusions") != []
    ):
        raise ValueError("candidate floor admission must be an empty typed record")
    routing = _mapping(counts.get("program_selection_routing"), "program routing")
    if any(
        _strict_integer(routing.get(field), f"candidate floor routing {field}") != 0
        for field in (
            "input_count",
            "canonical_hard_pass_count",
            "development_only_excluded_count",
        )
    ):
        raise ValueError("candidate floor program routing counts must be zero")
    final_routing = _mapping(counts.get("final_vlm_routing"), "final VLM routing")
    if any(
        _strict_integer(
            final_routing.get(field), f"candidate floor final routing {field}"
        )
        != 0
        for field in (
            "input_count",
            "row_count",
            "combined_hard_pass_count",
            "routed_applied_book_candidate_count",
        )
    ):
        raise ValueError("candidate floor final routing counts must be zero")

    context = _mapping(
        program_record.get("program_dimensional_context"),
        "program dimensional context",
    )
    _exact_schema(context, _DIMENSIONAL_SCHEMA, "program dimensional context")
    if context.get("program_id") != program or context.get("status") != "adapted":
        raise ValueError("candidate floor dimensional context is inconsistent")
    if _mapping(
        counts.get("program_dimensional_context"),
        "counts program dimensional context",
    ) != context:
        raise ValueError("candidate floor dimensional context copies disagree")
    advisory = _mapping(
        context.get("pre_generation_capacity_advisory"),
        "candidate floor pre-generation advisory",
    )
    _exact_schema(advisory, _ADVISORY_SCHEMA, "candidate floor advisory")
    if (
        advisory.get("authority") != "diagnostic_only"
        or advisory.get("generation_continued") is not True
        or advisory.get("dimensional_context_infeasible") is not False
        or advisory.get("floor_capacity_plan_infeasible") is not False
    ):
        raise ValueError("candidate floor advisory is inconsistent")
    context_hash = _sha256(
        context.get("floor_capacity_plan_hash"), "context floor capacity plan hash"
    )
    plan = _mapping(counts.get("floor_capacity_plan"), "floor capacity plan")
    plan_hash, legal_hash = _floor_plan_identity(plan, program=program)
    if plan_hash != context_hash:
        raise ValueError("candidate floor capacity plan hash mismatch")

    manifest = _base_attempt_manifest(
        source_artifact_sha256=source_artifact_sha256,
        program=program,
        stage="candidate_floor_context",
        route_kind=None,
        progress_counts=progress_counts,
    )
    manifest["ledger"] = {
        "schema_version": _LEDGER_SCHEMA,
        "target_count": 3,
        "record_count": 0,
        "records_truncated": False,
    }
    manifest["stage_evidence"] = {
        "evaluated_count": evaluated,
        "candidate_floor_context_failed": evaluated,
        "dimensional_context_schema_version": _DIMENSIONAL_SCHEMA,
        "dimensional_context_status": "adapted",
        "advisory_schema_version": _ADVISORY_SCHEMA,
        "advisory_authority": "diagnostic_only",
        "generation_continued": True,
        "floor_capacity_plan_schema_version": _FLOOR_PLAN_SCHEMA,
        "floor_capacity_plan_status": "materialized",
        "floor_capacity_plan_hash": plan_hash,
        "legal_floor_field_hash": legal_hash,
        "admission_schema_version": _ADMISSION_SCHEMA,
        "admission_retained_count": 0,
        "admission_excluded_count": 0,
        "program_routing_schema_version": _ROUTING_SCHEMA,
        "program_routing_input_count": 0,
        "final_routing_schema_version": _FINAL_ROUTING_SCHEMA,
        "final_routing_input_count": 0,
        "typed_failure_ledger_present": False,
    }
    return _attempt_packet(
        source_artifact_sha256=source_artifact_sha256,
        pnu=pnu,
        program=program,
        case_id=case_id,
        stage="candidate_floor_context",
        route_kind=None,
        status="incomplete",
        manifest=manifest,
    )


def _build_portfolio_attempt(
    summary: Mapping[str, Any],
    program_record: Mapping[str, Any],
    *,
    source_artifact_sha256: str,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    if program_record.get("generation_status") == "program_site_infeasible":
        return _build_preflight_attempt(
            summary,
            program_record,
            source_artifact_sha256=source_artifact_sha256,
            pnu=pnu,
            program=program,
            case_id=case_id,
        )
    ledger = _mapping(
        program_record.get("portfolio_evaluation"), "portfolio_evaluation"
    )
    record_count = _strict_integer(
        ledger.get("record_count"), "portfolio evaluation record_count"
    )
    if record_count > 0:
        return _build_selection_attempt(
            summary,
            program_record,
            source_artifact_sha256=source_artifact_sha256,
            pnu=pnu,
            program=program,
            case_id=case_id,
        )
    counts = _mapping(program_record.get("counts"), "counts")
    stage_counts = counts.get("capacity_stage_counts")
    if isinstance(stage_counts, Mapping) and _strict_integer(
        stage_counts.get("candidate_floor_context_failed", 0),
        "candidate floor context failed",
    ) > 0:
        return _build_candidate_floor_context_attempt(
            summary,
            program_record,
            source_artifact_sha256=source_artifact_sha256,
            pnu=pnu,
            program=program,
            case_id=case_id,
        )
    return _build_materialization_attempt(
        summary,
        program_record,
        source_artifact_sha256=source_artifact_sha256,
        pnu=pnu,
        program=program,
        case_id=case_id,
    )


def packet_from_arr_artifacts(
    summary_path: Path,
    *,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]:
    """Build one native case from a canonical ARR portfolio summary."""

    source_bytes = summary_path.read_bytes()
    source_artifact_sha256 = hashlib.sha256(source_bytes).hexdigest()
    summary = json.loads(source_bytes.decode("utf-8"))
    if not isinstance(summary, Mapping):
        raise ValueError("ARR summary root must be an object")
    _exact_schema(summary, _SUMMARY_SCHEMA, "ARR summary")
    if str(summary.get("pnu") or "") != pnu:
        raise ValueError("summary PNU mismatch")
    program_record = _select_program(summary, program)
    if isinstance(program_record.get("rows"), list) and not program_record["rows"]:
        return _build_portfolio_attempt(
            summary,
            program_record,
            source_artifact_sha256=source_artifact_sha256,
            pnu=pnu,
            program=program,
            case_id=case_id,
        )
    row = _select_row(program_record)
    execution_id, program_hash, geometry_hash = _verify_identity(row, pnu=pnu)
    evidence = _build_evidence(row, pnu=pnu)
    packet = ArchitectureEvidencePacket(
        case_id=case_id,
        pnu=pnu,
        program=program,  # type: ignore[arg-type]
        condition="native",
        execution_id=execution_id,
        program_hash=program_hash,
        geometry_hash=geometry_hash,
        evidence=evidence,
        subject_kind="execution",
        source_artifact_sha256=source_artifact_sha256,
    )
    from .validators import validate_evidence_packet

    validation = validate_evidence_packet(packet)
    gold = ArchitectureGoldRecord(
        case_id=case_id,
        expected_decision=validation.expected_decision,  # type: ignore[arg-type]
        blocking_issue_codes=validation.blocking_issue_codes,
        missing_evidence_codes=validation.missing_evidence_codes,
        required_evidence_ids=tuple(item["evidence_id"] for item in evidence),
        mutation_family="",
    )
    return packet, gold
