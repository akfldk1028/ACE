"""Synthetic, zero-call Task 5A E1 contracts."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .obligation_oracle import (
    E2MechanismContract,
    SyntheticAssignmentCrossoverRecord,
    SyntheticE1ActionRosterV2,
    SyntheticExecutionConformanceRecord,
    SyntheticSoloExecutionConformanceV2,
    SyntheticTerminalBranch,
    _Record,
    _SCHEMA_PREFIX,
    _require_float,
    _require_hash,
    _require_identifier,
    _sha_value,
)


@dataclass(frozen=True, slots=True)
class EscalationContract(_Record):
    schema_version: str
    base_adjustment_schema_sha256: str
    difficulty_feature_schema_sha256: str
    site_fold_manifest_sha256: str
    calibration_spec_sha256: str
    learner_class_sha256: str
    learner_capacity_sha256: str
    tie_rule_sha256: str
    branch_outcome_schema_sha256: str
    analysis_code_sha256: str
    synthetic_only: bool
    contract_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "EscalationContract.v1"
    HASH_FIELD = "contract_sha256"

    def _validate(self) -> None:
        if self.schema_version != self.SCHEMA:
            raise ValueError("escalation contract schema mismatch")
        for name in (
            "base_adjustment_schema_sha256",
            "difficulty_feature_schema_sha256",
            "site_fold_manifest_sha256",
            "calibration_spec_sha256",
            "learner_class_sha256",
            "learner_capacity_sha256",
            "tie_rule_sha256",
            "branch_outcome_schema_sha256",
            "analysis_code_sha256",
        ):
            _require_hash(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class SyntheticEscalationLabel(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    declared_packet_roster_sha256: str
    repeat_census_sha256: str
    escalation_contract_sha256: str
    label: bool
    synthetic_only: bool
    label_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticEscalationLabel.v1"
    HASH_FIELD = "label_sha256"

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        _require_hash(self.declared_packet_roster_sha256, "declared_packet_roster_sha256")
        _require_hash(self.repeat_census_sha256, "repeat_census_sha256")
        _require_hash(self.escalation_contract_sha256, "escalation_contract_sha256")
        if type(self.label) is not bool:
            raise TypeError("label must be native bool")


@dataclass(frozen=True, slots=True)
class SyntheticCalibrationSummary(_Record):
    status: str
    site_fold_census_sha256: str
    label_census_sha256: str
    prediction_census_sha256: str
    escalation_contract_sha256: str
    calibration_value: float | None
    synthetic_only: bool
    summary_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticCalibrationSummary.v1"
    HASH_FIELD = "summary_sha256"

    def _validate(self) -> None:
        if self.status not in {"synthetic_complete", "non_estimable_support"}:
            raise ValueError("invalid calibration status")
        for name in (
            "site_fold_census_sha256",
            "label_census_sha256",
            "prediction_census_sha256",
            "escalation_contract_sha256",
        ):
            _require_hash(getattr(self, name), name)
        if self.status == "synthetic_complete":
            _require_float(self.calibration_value, "calibration_value", minimum=0.0)
        elif self.calibration_value is not None:
            raise ValueError("non-estimable calibration value must be None")


def _one_by_key(
    rows: tuple[object, ...],
    key_for: object,
    name: str,
) -> dict[object, object]:
    result: dict[object, object] = {}
    for row in rows:
        key = key_for(row)  # type: ignore[operator]
        if key in result:
            raise ValueError(f"duplicate {name}")
        result[key] = row
    return result


def build_synthetic_escalation_labels(
    e2_contract: E2MechanismContract,
    escalation_contract: EscalationContract,
) -> tuple[SyntheticEscalationLabel, ...]:
    if type(e2_contract) is not E2MechanismContract:
        raise TypeError("e2_contract must be exact E2MechanismContract")
    if type(escalation_contract) is not EscalationContract:
        raise TypeError("escalation_contract must be exact EscalationContract")
    if not e2_contract.e1_action_rosters:
        raise ValueError("escalation labels require declared action rosters")
    rosters = _one_by_key(
        e2_contract.e1_action_rosters,
        lambda row: (row.site_ref, row.case_ref, row.prefix_ref),
        "declared action roster target",
    )
    rosters_by_hash = {row.roster_sha256: row for row in rosters.values()}
    e1_assignments = []
    for row in e2_contract.assignments:
        roster = rosters_by_hash.get(row.immutable_target_roster_sha256)
        if roster is None:
            continue
        if (row.site_ref, row.case_ref, row.prefix_ref) != (
            roster.site_ref, roster.case_ref, roster.prefix_ref
        ):
            raise ValueError("E1 roster-owned assignment has foreign target")
        e1_assignments.append(row)
    assignments = _one_by_key(
        tuple(e1_assignments),
        lambda row: (
            row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed,
            row.assigned_actual_packet_id,
        ),
        "packet assignment cell",
    )
    executions = _one_by_key(
        tuple(
            row for row in e2_contract.execution_records
            if row.assignment_ref in {assignment.assignment_ref for assignment in e1_assignments}
        ),
        lambda row: row.assignment_ref,
        "packet execution assignment",
    )
    e1_execution_receipts = {
        row.post_run_execution_usage_conformance_receipt_sha256
        for row in executions.values()
    }
    solo_conformances = _one_by_key(
        e2_contract.solo_execution_records,
        lambda row: (row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed),
        "SOLO execution conformance cell",
    )
    packet_terminals = _one_by_key(
        tuple(
            row for row in e2_contract.terminal_branches
            if row.treatment_kind == "capability_packet"
            and row.execution_conformance_sha256 in e1_execution_receipts
        ),
        lambda row: (
            row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed,
            row.opaque_slot_id, row.actual_packet_id,
        ),
        "packet terminal cell",
    )
    solo_terminals = _one_by_key(
        tuple(row for row in e2_contract.terminal_branches if row.treatment_kind == "solo_synthesis"),
        lambda row: (row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed),
        "SOLO terminal cell",
    )
    e1_terminal_hashes = {
        *(row.record_sha256 for row in packet_terminals.values()),
        *(row.record_sha256 for row in solo_terminals.values()),
    }
    reached_assignments: set[str] = set()
    reached_executions: set[str] = set()
    reached_solo_conformances: set[str] = set()
    reached_terminals: set[str] = set()
    labels: list[SyntheticEscalationLabel] = []
    for target in sorted(rosters):
        roster = rosters[target]
        if type(roster) is not SyntheticE1ActionRosterV2:
            raise TypeError("declared action roster has foreign type")
        packet_means: list[float] = []
        solo: list[SyntheticTerminalBranch] = []
        for repeat_index, seed in roster.repeat_seed_cells:
            solo_key = (*target, repeat_index, seed)
            solo_conformance = solo_conformances.get(solo_key)
            solo_terminal = solo_terminals.get(solo_key)
            if (
                type(solo_conformance) is not SyntheticSoloExecutionConformanceV2
                or type(solo_terminal) is not SyntheticTerminalBranch
                or solo_conformance.common_synthesis_spec_sha256 != roster.common_synthesis_spec_sha256
                or solo_conformance.compliance_status != "verified"
                or solo_terminal.execution_conformance_sha256 != solo_conformance.record_sha256
            ):
                raise ValueError("SOLO label cell lacks matching verified conformance")
            reached_solo_conformances.add(solo_conformance.record_sha256)
            reached_terminals.add(solo_terminal.record_sha256)
            solo.append(solo_terminal)
        for packet_id in roster.packet_ids:
            packet_rows: list[SyntheticTerminalBranch] = []
            for repeat_index, seed in roster.repeat_seed_cells:
                assignment = assignments.get((*target, repeat_index, seed, packet_id))
                if (
                    type(assignment) is not SyntheticAssignmentCrossoverRecord
                ):
                    raise ValueError("declared packet cell lacks assignment")
                execution = executions.get(assignment.assignment_ref)
                terminal = packet_terminals.get(
                    (*target, repeat_index, seed, assignment.assigned_opaque_slot_id, packet_id)
                )
                if (
                    type(execution) is not SyntheticExecutionConformanceRecord
                    or type(terminal) is not SyntheticTerminalBranch
                    or execution.compliance_status != "verified"
                    or (execution.site_ref, execution.case_ref, execution.prefix_ref,
                        execution.repeat_index, execution.seed)
                    != (*target, repeat_index, seed)
                    or execution.assigned_opaque_slot_id != assignment.assigned_opaque_slot_id
                    or execution.assigned_actual_packet_id != packet_id
                    or execution.actual_opaque_slot_id != assignment.assigned_opaque_slot_id
                    or execution.actual_packet_id != packet_id
                    or execution.actual_complete_bundle_manifest_sha256
                    != assignment.assigned_complete_bundle_manifest_sha256
                    or terminal.execution_conformance_sha256
                    != execution.post_run_execution_usage_conformance_receipt_sha256
                ):
                    raise ValueError("declared packet label cell lacks verified closure")
                reached_assignments.add(assignment.record_sha256)
                reached_executions.add(execution.record_sha256)
                reached_terminals.add(terminal.record_sha256)
                packet_rows.append(terminal)
            packet_means.append(
                math.fsum(row.blind_terminal_quality for row in packet_rows) / len(packet_rows)
            )
        solo_mean = math.fsum(row.blind_terminal_quality for row in solo) / len(solo)
        labels.append(
            SyntheticEscalationLabel.create(
                site_ref=target[0],
                case_ref=target[1],
                prefix_ref=target[2],
                declared_packet_roster_sha256=_sha_value(list(roster.packet_ids)),
                repeat_census_sha256=_sha_value(
                    [[repeat, seed] for repeat, seed in roster.repeat_seed_cells]
                ),
                escalation_contract_sha256=escalation_contract.contract_sha256,
                label=max(packet_means) - solo_mean > 0.0,
            )
        )
    if reached_assignments != {row.record_sha256 for row in e1_assignments}:
        raise ValueError("unreached or extra packet assignment")
    if reached_executions != {row.record_sha256 for row in executions.values()}:
        raise ValueError("unreached or extra packet execution")
    if reached_solo_conformances != {row.record_sha256 for row in e2_contract.solo_execution_records}:
        raise ValueError("unreached or extra SOLO conformance")
    if reached_terminals != e1_terminal_hashes:
        raise ValueError("unreached or extra terminal")
    return tuple(labels)


def validate_synthetic_calibration(
    labels: tuple[SyntheticEscalationLabel, ...],
    predictions: tuple[tuple[str, str, float], ...],
    escalation_contract: EscalationContract,
) -> SyntheticCalibrationSummary:
    if type(labels) is not tuple or any(type(row) is not SyntheticEscalationLabel for row in labels):
        raise TypeError("labels must be an exact tuple of exact records")
    if type(predictions) is not tuple:
        raise TypeError("predictions must be an exact tuple")
    if type(escalation_contract) is not EscalationContract:
        raise TypeError("escalation_contract must be exact EscalationContract")
    label_by_hash: dict[str, SyntheticEscalationLabel] = {}
    for row in labels:
        if row.label_sha256 in label_by_hash:
            raise ValueError("duplicate escalation label")
        if row.escalation_contract_sha256 != escalation_contract.contract_sha256:
            raise ValueError("label escalation contract binding does not match")
        label_by_hash[row.label_sha256] = row
    observed: dict[str, tuple[str, float]] = {}
    for prediction in predictions:
        if type(prediction) is not tuple or len(prediction) != 3:
            raise TypeError("prediction must be an exact three-tuple")
        label_hash, site_ref, probability = prediction
        _require_hash(label_hash, "prediction label hash")
        _require_identifier(site_ref, "prediction site_ref")
        _require_float(probability, "prediction probability", minimum=0.0, maximum=1.0)
        if label_hash in observed:
            raise ValueError("duplicate calibration prediction")
        observed[label_hash] = (site_ref, probability)
    if set(observed) != set(label_by_hash):
        raise ValueError("prediction closure does not equal label closure")
    for key, (site_ref, _) in observed.items():
        if site_ref != label_by_hash[key].site_ref:
            raise ValueError("prediction site does not match label site")
    site_counts: dict[str, int] = {}
    for row in labels:
        site_counts[row.site_ref] = site_counts.get(row.site_ref, 0) + 1
    site_rows = [
        [site_ref, site_counts[site_ref]]
        for site_ref in sorted(site_counts, key=lambda value: value.encode("ascii"))
    ]
    label_census = [
        [row.site_ref, row.case_ref, row.prefix_ref, row.label_sha256, row.label]
        for row in labels
    ]
    prediction_census = [
        [key, observed[key][0], observed[key][1]] for key in sorted(observed)
    ]
    estimable = len(site_rows) >= 2 and len({row.label for row in labels}) == 2
    if estimable:
        brier = math.fsum(
            (observed[row.label_sha256][1] - float(row.label)) ** 2 for row in labels
        ) / len(labels)
        status = "synthetic_complete"
        value: float | None = brier
    else:
        status = "non_estimable_support"
        value = None
    return SyntheticCalibrationSummary.create(
        status=status,
        site_fold_census_sha256=_sha_value(site_rows),
        label_census_sha256=_sha_value(label_census),
        prediction_census_sha256=_sha_value(prediction_census),
        escalation_contract_sha256=escalation_contract.contract_sha256,
        calibration_value=value,
    )


__all__ = (
    "EscalationContract",
    "SyntheticEscalationLabel",
    "SyntheticCalibrationSummary",
    "build_synthetic_escalation_labels",
    "validate_synthetic_calibration",
)
