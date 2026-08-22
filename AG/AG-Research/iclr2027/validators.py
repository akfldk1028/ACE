"""Independent validators and terminal admissibility for architecture evidence."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Mapping

from .io import sha256_json
from .schema import (
    ArchitectureEvidencePacket,
    ArchitectureGoldRecord,
    ArchitecturePublicCase,
    ArchitectureReviewState,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ATTEMPT_IDENTITY_SCHEMA = "ace.iclr2027.portfolio_attempt_identity.v2"
_SUMMARY_SCHEMA = "arr.maas.book_program_portfolios.v1"
_PROGRESS_SCHEMA = "arr.maas.mass_progress.v1"
_COMPLETION_SCHEMA = "arr.maas.portfolio_completion.v1"
_DOWNSTREAM_SCHEMA = "arr.maas.book_downstream_hard_gate.v1"


@dataclass(frozen=True)
class EvidenceValidationResult:
    blocking_issue_codes: tuple[str, ...]
    missing_evidence_codes: tuple[str, ...]
    checked_evidence_ids: tuple[str, ...]

    @property
    def expected_decision(self) -> str:
        if self.blocking_issue_codes:
            return "STOP_REJECT"
        if self.missing_evidence_codes:
            return "CONTINUE"
        return "STOP_ACCEPT"


@dataclass(frozen=True)
class AdmissibilityResult:
    admissible: bool
    expected_decision: str
    blocking_issue_codes: tuple[str, ...]
    missing_evidence_codes: tuple[str, ...]
    reasons: tuple[str, ...]


ArchitectureCase = ArchitectureEvidencePacket | ArchitecturePublicCase


def _evidence_index(packet: ArchitectureCase) -> dict[str, Mapping[str, Any]]:
    return {
        str(item.get("evidence_id") or ""): item
        for item in packet.evidence
        if item.get("evidence_id")
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nonnegative_integer(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and float(value).is_integer()
        and float(value) >= 0.0
    )


def _strict_integer(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _zero_integer(value: Any) -> bool:
    return _strict_integer(value) and value == 0


def _zero_real(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and float(value) == 0.0
    )


def _finite_real(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return value
    return ()


def _exact_keys(value: Mapping[str, Any], expected: set[str]) -> bool:
    return set(value) == expected


def _portfolio_attempt_validation(
    packet: ArchitectureCase,
) -> EvidenceValidationResult:
    evidence = _evidence_index(packet)
    checked = tuple(sorted(evidence))
    record = _mapping(evidence.get("evidence:portfolio_attempt"))
    manifest = _mapping(record.get("evidence"))
    stage = packet.attempt_stage
    expected_status = "incomplete" if stage == "candidate_floor_context" else "failed"
    incomplete = any(
        (
            set(evidence) != {"evidence:portfolio_attempt"},
            not _exact_keys(record, {"evidence_id", "domain", "status", "evidence"}),
            record.get("domain") != "program",
            record.get("status") != expected_status,
            manifest.get("schema_version") != _ATTEMPT_IDENTITY_SCHEMA,
            manifest.get("source_schema_version") != _SUMMARY_SCHEMA,
            manifest.get("source_artifact_sha256")
            != packet.source_artifact_sha256,
            manifest.get("program") != packet.program,
            manifest.get("attempt_stage") != stage,
            manifest.get("route_kind") != packet.route_kind,
            not _zero_integer(manifest.get("selected_count")),
            not _zero_integer(manifest.get("row_count")),
        )
    )
    base_manifest_keys = {
        "schema_version",
        "source_artifact_sha256",
        "source_schema_version",
        "program",
        "attempt_stage",
        "route_kind",
        "selected_count",
        "row_count",
        "mass_progress",
        "portfolio_completion",
        "downstream_hard_gate",
    }
    expected_manifest_keys = set(base_manifest_keys)
    if stage == "selection":
        expected_manifest_keys.update(
            {"target_count", "record_count", "records_truncated", "candidates"}
        )
    elif stage in {"materialization", "candidate_floor_context"}:
        expected_manifest_keys.update({"ledger", "stage_evidence"})
    elif stage == "preflight":
        expected_manifest_keys.add("stage_evidence")
    if not _exact_keys(manifest, expected_manifest_keys):
        incomplete = True
    expected_attempt_id = "attempt:" + sha256_json(
        {
            "source_artifact_sha256": packet.source_artifact_sha256,
            "program": packet.program,
            "attempt_stage": stage,
        }
    )
    if packet.attempt_id != expected_attempt_id:
        incomplete = True

    progress = _mapping(manifest.get("mass_progress"))
    evaluated_count = progress.get("evaluated_count")
    compiled_count = progress.get("compiled_count")
    individual_count = progress.get("individual_hard_pass_count")
    compatible_count = progress.get("compatible_selected_count")
    if (
        progress.get("schema_version") != _PROGRESS_SCHEMA
        or not _exact_keys(
            progress,
            {"schema_version", "evaluated_count", "compiled_count"}
            if stage == "selection"
            else {
                "schema_version",
                "evaluated_count",
                "compiled_count",
                "individual_hard_pass_count",
                "compatible_selected_count",
            },
        )
        or not _strict_integer(evaluated_count)
        or not _strict_integer(compiled_count)
        or (
            stage != "selection"
            and (
                not _strict_integer(individual_count)
                or not _strict_integer(compatible_count)
            )
        )
        or (
            _strict_integer(evaluated_count)
            and _strict_integer(compiled_count)
            and compiled_count > evaluated_count
        )
    ):
        incomplete = True

    completion = _mapping(manifest.get("portfolio_completion"))
    if (
        completion.get("schema_version") != _COMPLETION_SCHEMA
        or not _exact_keys(
            completion,
            {"schema_version", "hard_pass", "selected_count", "diagnostic_only"}
            if stage == "selection"
            else {
                "schema_version",
                "hard_pass",
                "selected_count",
                "selected_scope_count",
                "diagnostic_only",
            },
        )
        or completion.get("hard_pass") is not False
        or not _zero_integer(completion.get("selected_count"))
        or completion.get("diagnostic_only") is not True
        or (
            stage != "selection"
            and not _zero_integer(completion.get("selected_scope_count"))
        )
    ):
        incomplete = True
    downstream = _mapping(manifest.get("downstream_hard_gate"))
    if (
        downstream.get("schema_version") != _DOWNSTREAM_SCHEMA
        or not _exact_keys(
            downstream,
            {"schema_version", "status", "candidate_count", "row_count"},
        )
        or downstream.get("status") != "fail"
        or not _zero_integer(downstream.get("candidate_count"))
        or not _zero_integer(downstream.get("row_count"))
    ):
        incomplete = True

    if stage == "selection":
        target_count = manifest.get("target_count")
        record_count = manifest.get("record_count")
        candidates = _sequence(manifest.get("candidates"))
        if (
            not _strict_integer(evaluated_count, minimum=1)
            or not _strict_integer(compiled_count, minimum=1)
            or not _strict_integer(target_count, minimum=1)
            or not _strict_integer(record_count, minimum=1)
            or target_count != record_count
            or record_count != len(candidates)
            or manifest.get("records_truncated") is not False
        ):
            incomplete = True
        candidate_ids: list[str] = []
        program_hashes: list[str] = []
        geometry_hashes: list[str] = []
        for raw_candidate in candidates:
            candidate = _mapping(raw_candidate)
            candidate_id = str(candidate.get("candidate_id") or "").strip()
            program_hash = str(candidate.get("program_hash") or "")
            geometry_hash = str(candidate.get("geometry_hash") or "")
            if (
                not _exact_keys(
                    candidate,
                    {
                        "candidate_id",
                        "program_hash",
                        "geometry_hash",
                        "selected",
                        "selection_status",
                        "selection_reason_count",
                        "passport_status",
                        "execution_id",
                        "final_legal_geometry_hash",
                    },
                )
                or not candidate_id
                or not _SHA256.fullmatch(program_hash)
                or not _SHA256.fullmatch(geometry_hash)
                or candidate.get("selected") is not False
                or candidate.get("selection_status") != "fail"
                or not _strict_integer(
                    candidate.get("selection_reason_count"), minimum=1
                )
                or candidate.get("passport_status") != "in_progress"
                or candidate.get("execution_id") is not None
                or candidate.get("final_legal_geometry_hash") is not None
            ):
                incomplete = True
            candidate_ids.append(candidate_id)
            program_hashes.append(program_hash)
            geometry_hashes.append(geometry_hash)
        if any(
            len(values) != len(set(values))
            for values in (candidate_ids, program_hashes, geometry_hashes)
        ) or candidate_ids != sorted(candidate_ids):
            incomplete = True
    elif stage in {"materialization", "candidate_floor_context"}:
        ledger = _mapping(manifest.get("ledger"))
        stage_evidence = _mapping(manifest.get("stage_evidence"))
        if (
            ledger.get("schema_version")
            != "arr.maas.portfolio_evaluation_ledger.v1"
            or not _exact_keys(
                ledger,
                {
                    "schema_version",
                    "target_count",
                    "record_count",
                    "records_truncated",
                },
            )
            or not _strict_integer(ledger.get("target_count"), minimum=3)
            or ledger.get("target_count") != 3
            or not _zero_integer(ledger.get("record_count"))
            or ledger.get("records_truncated") is not False
            or not _strict_integer(evaluated_count, minimum=1)
            or individual_count != 0
            or compatible_count != 0
            or not _strict_integer(
                stage_evidence.get("evaluated_count"), minimum=1
            )
            or stage_evidence.get("evaluated_count") != evaluated_count
        ):
            incomplete = True
        if stage == "materialization":
            common_stage_keys = {"evaluated_count", "compiled_count", "route_kind"}
            if packet.route_kind == "all_invocations_failed":
                expected_stage_keys = common_stage_keys | {
                    "exact_compile_invocation_count",
                    "materialization_invocation_count",
                    "terminal_failure_count",
                    "terminal_failure_record_count",
                    "terminal_failure_reason_total",
                    "qd_stream_candidates_released",
                }
            elif packet.route_kind == "capacity_admission_empty":
                expected_stage_keys = common_stage_keys | {
                    "admission_schema_version",
                    "admission_status",
                    "hard_pass_required",
                    "retained_count",
                    "excluded_count",
                }
            else:
                expected_stage_keys = common_stage_keys | {
                    "routing_schema_version",
                    "routing_input_count",
                    "canonical_hard_pass_count",
                    "development_only_excluded_count",
                    "final_routing_schema_version",
                    "final_input_count",
                    "final_row_count",
                    "final_combined_hard_pass_count",
                    "final_routed_candidate_count",
                }
            if (
                not _exact_keys(stage_evidence, expected_stage_keys)
                or not _strict_integer(stage_evidence.get("compiled_count"))
                or stage_evidence.get("compiled_count") != compiled_count
                or stage_evidence.get("route_kind") != packet.route_kind
            ):
                incomplete = True
            if packet.route_kind == "all_invocations_failed":
                terminal_count = stage_evidence.get("terminal_failure_count")
                if (
                    not _zero_integer(compiled_count)
                    or not _strict_integer(terminal_count, minimum=1)
                    or terminal_count != evaluated_count
                    or not _strict_integer(
                        stage_evidence.get("exact_compile_invocation_count"), minimum=1
                    )
                    or stage_evidence.get("exact_compile_invocation_count")
                    != terminal_count
                    or not _strict_integer(
                        stage_evidence.get("materialization_invocation_count"),
                        minimum=1,
                    )
                    or stage_evidence.get("materialization_invocation_count")
                    != terminal_count
                    or not _strict_integer(
                        stage_evidence.get("terminal_failure_record_count"), minimum=1
                    )
                    or stage_evidence.get("terminal_failure_record_count")
                    != terminal_count
                    or not _strict_integer(
                        stage_evidence.get("terminal_failure_reason_total"), minimum=1
                    )
                    or stage_evidence.get("terminal_failure_reason_total")
                    != terminal_count
                    or not _zero_integer(
                        stage_evidence.get("qd_stream_candidates_released")
                    )
                ):
                    incomplete = True
            elif packet.route_kind == "capacity_admission_empty":
                if (
                    stage_evidence.get("admission_schema_version")
                    != "arr.maas.capacity_selection_admission.v1"
                    or stage_evidence.get("admission_status") != "pass"
                    or stage_evidence.get("hard_pass_required") is not True
                    or not _zero_integer(stage_evidence.get("retained_count"))
                    or not _strict_integer(
                        stage_evidence.get("excluded_count"), minimum=1
                    )
                ):
                    incomplete = True
            elif packet.route_kind == "program_routing_empty":
                routing_input = stage_evidence.get("routing_input_count")
                if (
                    stage_evidence.get("routing_schema_version")
                    != "arr.maas.program_selection_routing.v1"
                    or not _strict_integer(routing_input, minimum=1)
                    or not _zero_integer(
                        stage_evidence.get("canonical_hard_pass_count")
                    )
                    or not _strict_integer(
                        stage_evidence.get("development_only_excluded_count"),
                        minimum=1,
                    )
                    or stage_evidence.get("development_only_excluded_count")
                    != routing_input
                    or stage_evidence.get("final_routing_schema_version")
                    != "arr.maas.final_vlm_applied_book_routing.v2"
                    or any(
                        not _zero_integer(stage_evidence.get(field))
                        for field in (
                            "final_input_count",
                            "final_row_count",
                            "final_combined_hard_pass_count",
                            "final_routed_candidate_count",
                        )
                    )
                ):
                    incomplete = True
            else:
                incomplete = True
        else:
            if (
                not _exact_keys(
                    stage_evidence,
                    {
                        "evaluated_count",
                        "candidate_floor_context_failed",
                        "dimensional_context_schema_version",
                        "dimensional_context_status",
                        "advisory_schema_version",
                        "advisory_authority",
                        "generation_continued",
                        "floor_capacity_plan_schema_version",
                        "floor_capacity_plan_status",
                        "floor_capacity_plan_hash",
                        "legal_floor_field_hash",
                        "admission_schema_version",
                        "admission_retained_count",
                        "admission_excluded_count",
                        "program_routing_schema_version",
                        "program_routing_input_count",
                        "final_routing_schema_version",
                        "final_routing_input_count",
                        "typed_failure_ledger_present",
                    },
                )
                or not _zero_integer(compiled_count)
                or stage_evidence.get("candidate_floor_context_failed")
                != evaluated_count
                or not _strict_integer(
                    stage_evidence.get("candidate_floor_context_failed"), minimum=1
                )
                or stage_evidence.get("typed_failure_ledger_present") is not False
                or stage_evidence.get("dimensional_context_schema_version")
                != "arr.maas.program_dimensional_context.v1"
                or stage_evidence.get("dimensional_context_status") != "adapted"
                or stage_evidence.get("advisory_schema_version")
                != "arr.maas.pre_generation_capacity_advisory.v1"
                or stage_evidence.get("advisory_authority") != "diagnostic_only"
                or stage_evidence.get("generation_continued") is not True
                or stage_evidence.get("floor_capacity_plan_schema_version")
                != "arr.maas.floor_capacity_plan.v1"
                or stage_evidence.get("floor_capacity_plan_status") != "materialized"
                or stage_evidence.get("admission_schema_version")
                != "arr.maas.capacity_selection_admission.v1"
                or not _zero_integer(
                    stage_evidence.get("admission_retained_count")
                )
                or not _zero_integer(
                    stage_evidence.get("admission_excluded_count")
                )
                or stage_evidence.get("program_routing_schema_version")
                != "arr.maas.program_selection_routing.v1"
                or not _zero_integer(
                    stage_evidence.get("program_routing_input_count")
                )
                or stage_evidence.get("final_routing_schema_version")
                != "arr.maas.final_vlm_applied_book_routing.v2"
                or not _zero_integer(
                    stage_evidence.get("final_routing_input_count")
                )
                or not _SHA256.fullmatch(
                    str(stage_evidence.get("floor_capacity_plan_hash") or "")
                )
                or not _SHA256.fullmatch(
                    str(stage_evidence.get("legal_floor_field_hash") or "")
                )
            ):
                incomplete = True
    elif stage == "preflight":
        stage_evidence = _mapping(manifest.get("stage_evidence"))
        if (
            not _exact_keys(
                stage_evidence,
                {
                    "early_stop_schema_version",
                    "early_stop_status",
                    "generation_attempted",
                    "dimensional_context_schema_version",
                    "dimensional_context_status",
                    "selected_subtype",
                    "effective_floor_count",
                    "effective_height_m",
                    "advisory_schema_version",
                    "advisory_authority",
                    "dimensional_context_infeasible",
                    "floor_capacity_plan_infeasible",
                    "failure_reason_count",
                    "floor_capacity_plan_schema_version",
                    "floor_capacity_plan_status",
                    "floor_capacity_plan_hash",
                    "legal_floor_field_hash",
                },
            )
            or any((evaluated_count, compiled_count, individual_count, compatible_count))
            or "ledger" in manifest
            or stage_evidence.get("early_stop_schema_version")
            != "arr.maas.program_site_early_stop.v1"
            or stage_evidence.get("early_stop_status")
            != "program_site_infeasible"
            or stage_evidence.get("generation_attempted") is not False
            or stage_evidence.get("dimensional_context_schema_version")
            != "arr.maas.program_dimensional_context.v1"
            or stage_evidence.get("dimensional_context_status") != "infeasible"
            or stage_evidence.get("selected_subtype") != "none"
            or not _zero_integer(stage_evidence.get("effective_floor_count"))
            or not _zero_real(stage_evidence.get("effective_height_m"))
            or stage_evidence.get("advisory_schema_version")
            != "arr.maas.pre_generation_capacity_advisory.v1"
            or stage_evidence.get("advisory_authority") != "diagnostic_only"
            or stage_evidence.get("dimensional_context_infeasible") is not True
            or stage_evidence.get("floor_capacity_plan_infeasible") is not False
            or not _strict_integer(
                stage_evidence.get("failure_reason_count"), minimum=1
            )
            or stage_evidence.get("floor_capacity_plan_schema_version")
            != "arr.maas.floor_capacity_plan.v1"
            or stage_evidence.get("floor_capacity_plan_status") != "materialized"
            or not _SHA256.fullmatch(
                str(stage_evidence.get("floor_capacity_plan_hash") or "")
            )
            or not _SHA256.fullmatch(
                str(stage_evidence.get("legal_floor_field_hash") or "")
            )
        ):
            incomplete = True
    else:
        incomplete = True

    issues: list[str] = []
    missing: list[str] = []
    if packet.attempt_hash != sha256_json(manifest):
        issues.append("identity.attempt_hash_mismatch")
    if incomplete:
        issues.append("evidence.portfolio_attempt_incomplete")
    elif stage == "selection":
        issues.append("selection.no_admitted_candidate")
    elif stage == "materialization":
        issues.append("materialization.no_candidate_reached_ledger")
    elif stage == "preflight":
        issues.append("preflight.program_site_infeasible")
    elif stage == "candidate_floor_context":
        missing.append("candidate_floor_context.typed_ledger_missing")
    return EvidenceValidationResult(tuple(issues), tuple(missing), checked)


def validate_evidence_packet(
    packet: ArchitectureCase,
) -> EvidenceValidationResult:
    """Recompute typed failures from measurements and identity bindings."""

    if packet.subject_kind == "portfolio_attempt":
        return _portfolio_attempt_validation(packet)

    evidence = _evidence_index(packet)
    issues: list[str] = []
    missing: list[str] = []

    site = _mapping(evidence.get("evidence:site_agent"))
    site_payload = _mapping(site.get("evidence"))
    if (
        site.get("status") != "passed"
        or site_payload.get("inside_site") is not True
    ):
        issues.append("site.boundary_failed")

    geometry = _mapping(evidence.get("evidence:geometry_agent"))
    geometry_payload = _mapping(geometry.get("evidence"))
    floor_count = int(geometry_payload.get("candidate_floor_count") or 0)
    achieved_gfa = float(geometry_payload.get("achieved_gfa_m2") or 0.0)
    if (
        geometry_payload.get("status") != "certified"
        or geometry_payload.get("hard_pass") is not True
        or floor_count <= 0
        or achieved_gfa <= 0.0
    ):
        issues.append("geometry.compilation_failed")

    has_law_evidence = "evidence:law_graph_agent" in evidence
    has_parking_evidence = "evidence:parking_agent" in evidence
    if not has_law_evidence:
        missing.append("law.required_evidence_missing")
    if not has_parking_evidence:
        missing.append("parking.required_evidence_missing")

    law = _mapping(evidence.get("evidence:law_graph_agent"))
    law_identity = _mapping(law.get("identity"))
    parking = _mapping(evidence.get("evidence:parking_agent"))
    parking_payload = _mapping(parking.get("evidence"))
    site_identity_key = (
        "pnu" if isinstance(packet, ArchitectureEvidencePacket) else "site_ref"
    )
    site_identity = getattr(packet, site_identity_key)
    identity_mismatches = [
        str(site_payload.get(site_identity_key) or "") != site_identity,
        str(site_payload.get("geometry_hash") or "") != packet.geometry_hash,
    ]
    if has_law_evidence:
        identity_mismatches.extend(
            (
            str(law_identity.get("execution_id") or "") != packet.execution_id,
            str(law_identity.get("program_hash") or "") != packet.program_hash,
            str(law_identity.get("geometry_hash") or "") != packet.geometry_hash,
            str(law_identity.get(site_identity_key) or "") != site_identity,
            )
        )
    if has_parking_evidence:
        identity_mismatches.append(
            str(parking_payload.get("geometry_hash") or "") != packet.geometry_hash,
        )
    if any(identity_mismatches):
        issues.append("identity.hash_mismatch")

    if has_law_evidence:
        law_payload = _mapping(law.get("evidence"))
        legal_projection = _mapping(law_payload.get("legal_projection"))
        numeric_preflight = _mapping(law_payload.get("numeric_preflight"))
        volume_raw = legal_projection.get("volume_retention")
        valid_volume = _finite_real(volume_raw)
        volume_retention = float(volume_raw) if valid_volume else 0.0
        if (
            law.get("status") != "passed"
            or numeric_preflight.get("evaluated") is not True
            or numeric_preflight.get("hard_pass") is not True
            or legal_projection.get("evaluated") is not True
            or legal_projection.get("hard_pass") is not True
            or not valid_volume
            or volume_retention < 0.98
        ):
            issues.append("law.projection_failed")

    if has_parking_evidence:
        required_raw = parking_payload.get("required_spaces")
        provided_raw = parking_payload.get("provided_spaces")
        valid_counts = _nonnegative_integer(required_raw) and _nonnegative_integer(
            provided_raw
        )
        required_spaces = int(required_raw) if valid_counts else -1
        provided_spaces = int(provided_raw) if valid_counts else -1
        if (
            parking.get("status") != "passed"
            or parking_payload.get("evaluated") is not True
            or parking_payload.get("hard_pass") is not True
            or not valid_counts
            or required_spaces < 0
            or provided_spaces < required_spaces
        ):
            issues.append("parking.supply_shortage")

    program = _mapping(evidence.get("evidence:program_agent"))
    program_payload = _mapping(program.get("evidence"))
    semantic = _mapping(program_payload.get("semantic_projection"))
    target_gfa = float(program_payload.get("candidate_target_gfa_m2") or 0.0)
    program_gfa = float(program_payload.get("achieved_gfa_m2") or 0.0)
    utilization = program_gfa / target_gfa if target_gfa > 0.0 else 0.0
    if (
        semantic.get("hard_pass") is not True
        or int(semantic.get("accepted_carrier_count") or 0) <= 0
        or utilization < 0.7
    ):
        issues.append("program.capacity_failed")

    checked = tuple(sorted(evidence))
    return EvidenceValidationResult(tuple(issues), tuple(missing), checked)


def gold_from_validation(
    packet: ArchitectureEvidencePacket,
    *,
    mutation_family: str,
) -> ArchitectureGoldRecord:
    result = validate_evidence_packet(packet)
    return ArchitectureGoldRecord(
        case_id=packet.case_id,
        expected_decision=result.expected_decision,  # type: ignore[arg-type]
        blocking_issue_codes=result.blocking_issue_codes,
        missing_evidence_codes=result.missing_evidence_codes,
        required_evidence_ids=tuple(
            str(item["evidence_id"]) for item in packet.evidence
        ),
        mutation_family=mutation_family,
    )


def validate_terminal_admissibility(
    packet: ArchitectureCase,
    state: ArchitectureReviewState,
) -> AdmissibilityResult:
    validation = validate_evidence_packet(packet)
    reasons: list[str] = []
    cited = set(state.evidence_ids)
    available = set(validation.checked_evidence_ids)
    if not cited.issubset(available):
        reasons.append("unknown_evidence_id")
    if not available.issubset(cited):
        reasons.append("required_evidence_not_cited")
    required_domains = {
        str(item.get("domain"))
        for item in packet.evidence
        if item.get("domain") in {"site", "law", "parking", "program", "geometry"}
    }
    if not required_domains.issubset(set(state.checked_domains)):
        reasons.append("required_domain_not_checked")
    if state.recommended_decision != validation.expected_decision:
        reasons.append("incorrect_terminal_decision")
    if set(validation.blocking_issue_codes) != set(state.blocking_issue_codes):
        reasons.append("blocking_issue_mismatch")
    if set(validation.missing_evidence_codes) != set(state.missing_evidence_codes):
        reasons.append("missing_evidence_mismatch")
    return AdmissibilityResult(
        admissible=not reasons,
        expected_decision=validation.expected_decision,
        blocking_issue_codes=validation.blocking_issue_codes,
        missing_evidence_codes=validation.missing_evidence_codes,
        reasons=tuple(reasons),
    )
