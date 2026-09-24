"""Deterministic clean Architecture commitments for the receipt study."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from iclr2027.estimand_receipts import (
    ObservedArtifactV1,
    PolicyRecordV1,
    ScoreWeightV1,
    TrustRootV1,
    UnitCommitmentV1,
)
from iclr2027.io import sha256_json


_STUDY_ID = "estimand-receipt-synthetic-v1"
_ACTION_MENU = ("action-baseline-v1", "action-receipt-v1")
_OBLIGATION_KEYS = ("geometry", "law", "parking", "program", "site_evidence")
_PROTOCOL_VERSION = "estimand-receipt-protocol-v1"
_COMPATIBLE_PROTOCOL_VERSION = "estimand-receipt-protocol-v1-compatible"
_POLICY_ID = "policy-balanced-v1"
_SCORE_DENOMINATOR = 4_294_967_295
_HEX = frozenset("0123456789abcdef")


def _require_digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(label)
    return value


@dataclass(frozen=True)
class SyntheticTargetV1:
    """Closed public input to one target-binding digest."""

    schema_version: str
    unit_id: str
    site_id: str
    target_index: int

    def __post_init__(self) -> None:
        if self.schema_version != "synthetic-target/v1":
            raise ValueError("synthetic target schema")
        if type(self.target_index) is not int or not 0 <= self.target_index < 8:
            raise ValueError("target index")
        expected_unit = f"syn-target-{self.site_id.removeprefix('syn-site-')}-{self.target_index:02d}"
        if self.site_id not in tuple(f"syn-site-{index:02d}" for index in range(8)):
            raise ValueError("site id")
        if self.unit_id != expected_unit:
            raise ValueError("unit id")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "unit_id": self.unit_id,
            "site_id": self.site_id,
            "target_index": self.target_index,
        }


@dataclass(frozen=True)
class RationalObligationScoreV1:
    """One exact synthetic obligation score without float ambiguity."""

    schema_version: str
    key: str
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.schema_version != "rational-obligation-score/v1":
            raise ValueError("obligation score schema")
        if self.key not in _OBLIGATION_KEYS:
            raise ValueError("obligation score key")
        if (
            type(self.numerator) is not int
            or not 0 <= self.numerator <= _SCORE_DENOMINATOR
        ):
            raise ValueError("obligation score numerator")
        if self.denominator != _SCORE_DENOMINATOR:
            raise ValueError("obligation score denominator")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "key": self.key,
            "numerator": self.numerator,
            "denominator": self.denominator,
        }


@dataclass(frozen=True)
class PolicyInformationSnapshotV1:
    """Closed pre-decision public information bound by a policy record."""

    schema_version: str
    study_id: str
    site_id: str
    unit_id: str
    stratum_id: str
    target_binding_sha256: str
    action_menu: tuple[str, ...]
    budget_limit: int
    retry_limit: int

    def __post_init__(self) -> None:
        if self.schema_version != "policy-information-snapshot/v1":
            raise ValueError("information snapshot schema")
        if self.study_id != _STUDY_ID:
            raise ValueError("study id")
        if self.action_menu != _ACTION_MENU:
            raise ValueError("action menu")
        if self.budget_limit != 5:
            raise ValueError("budget limit")
        if self.retry_limit != 0:
            raise ValueError("retry limit")
        _require_digest(self.stratum_id, "stratum id")
        _require_digest(self.target_binding_sha256, "target binding")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "site_id": self.site_id,
            "unit_id": self.unit_id,
            "stratum_id": self.stratum_id,
            "target_binding_sha256": self.target_binding_sha256,
            "action_menu": list(self.action_menu),
            "budget_limit": self.budget_limit,
            "retry_limit": self.retry_limit,
        }


@dataclass(frozen=True)
class PolicyDecisionEventV1:
    """Closed public inputs to the deterministic policy decision digest."""

    schema_version: str
    policy_id: str
    information_snapshot_sha256: str
    chosen_action: str
    propensity: float
    budget_limit: int
    realized_cost: float
    retry_limit: int

    def __post_init__(self) -> None:
        if self.schema_version != "policy-decision-event/v1":
            raise ValueError("decision event schema")
        if self.policy_id != _POLICY_ID:
            raise ValueError("policy id")
        _require_digest(self.information_snapshot_sha256, "information snapshot")
        if self.chosen_action not in _ACTION_MENU:
            raise ValueError("chosen action")
        if self.propensity != 0.5:
            raise ValueError("propensity")
        if self.budget_limit != 5:
            raise ValueError("budget limit")
        expected_cost = 1.0 if self.chosen_action == _ACTION_MENU[0] else 3.0
        if self.realized_cost != expected_cost:
            raise ValueError("realized cost")
        if self.retry_limit != 0:
            raise ValueError("retry limit")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "information_snapshot_sha256": self.information_snapshot_sha256,
            "chosen_action": self.chosen_action,
            "propensity": self.propensity,
            "budget_limit": self.budget_limit,
            "realized_cost": self.realized_cost,
            "retry_limit": self.retry_limit,
        }


@dataclass(frozen=True)
class CleanConstructionRowV1:
    """Independent public construction inputs and their sealed outputs."""

    schema_version: str
    study_id: str
    unit_id: str
    site_id: str
    stratum_id: str
    target_index: int
    assignment: int
    target: SyntheticTargetV1
    obligation_scores: tuple[RationalObligationScoreV1, ...]
    information_snapshot: PolicyInformationSnapshotV1
    decision_event: PolicyDecisionEventV1
    commitment_sha256: str
    artifact_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != "clean-construction-row/v1":
            raise ValueError("construction row schema")
        if self.study_id != _STUDY_ID:
            raise ValueError("study id")
        if (
            self.target.to_dict()
            != SyntheticTargetV1(
                schema_version="synthetic-target/v1",
                unit_id=self.unit_id,
                site_id=self.site_id,
                target_index=self.target_index,
            ).to_dict()
        ):
            raise ValueError("target")
        if self.assignment != self.target_index % 2:
            raise ValueError("assignment")
        expected_stratum = sha256_json(
            {"schema_version": "synthetic-stratum/v1", "site_id": self.site_id}
        )
        if self.stratum_id != expected_stratum:
            raise ValueError("stratum id")
        if tuple(item.key for item in self.obligation_scores) != _OBLIGATION_KEYS:
            raise ValueError("obligation scores")
        if self.information_snapshot.unit_id != self.unit_id:
            raise ValueError("information snapshot unit")
        if self.information_snapshot.site_id != self.site_id:
            raise ValueError("information snapshot site")
        if self.information_snapshot.stratum_id != self.stratum_id:
            raise ValueError("information snapshot stratum")
        if self.decision_event.information_snapshot_sha256 != sha256_json(
            self.information_snapshot.to_dict()
        ):
            raise ValueError("decision event snapshot")
        _require_digest(self.commitment_sha256, "commitment digest")
        _require_digest(self.artifact_sha256, "artifact digest")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "unit_id": self.unit_id,
            "site_id": self.site_id,
            "stratum_id": self.stratum_id,
            "target_index": self.target_index,
            "assignment": self.assignment,
            "target": self.target.to_dict(),
            "obligation_scores": [item.to_dict() for item in self.obligation_scores],
            "information_snapshot": self.information_snapshot.to_dict(),
            "decision_event": self.decision_event.to_dict(),
            "commitment_sha256": self.commitment_sha256,
            "artifact_sha256": self.artifact_sha256,
        }


@dataclass(frozen=True)
class CleanBenchmarkV1:
    """The exact clean 8-by-8 benchmark and its external trust root."""

    schema_version: str
    study_id: str
    ledger: tuple[CleanConstructionRowV1, ...]
    trust_root: TrustRootV1
    artifacts: tuple[ObservedArtifactV1, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "clean-benchmark/v1":
            raise ValueError("clean benchmark schema")
        if self.study_id != _STUDY_ID:
            raise ValueError("study id")
        if len(self.ledger) != 64 or len(self.artifacts) != 64:
            raise ValueError("clean benchmark census")
        if any(type(item) is not CleanConstructionRowV1 for item in self.ledger):
            raise ValueError("construction ledger")
        if type(self.trust_root) is not TrustRootV1:
            raise ValueError("trust root")
        if any(type(item) is not ObservedArtifactV1 for item in self.artifacts):
            raise ValueError("observed artifacts")
        TrustRootV1.from_dict(self.trust_root.to_dict())
        if self.trust_root.study_id != self.study_id:
            raise ValueError("trust root study")
        ledger_ids = tuple(item.unit_id for item in self.ledger)
        commitment_ids = tuple(item.unit_id for item in self.trust_root.commitments)
        artifact_ids = tuple(item.unit_id for item in self.artifacts)
        expected_ids = tuple(sorted(ledger_ids, key=lambda item: item.encode("utf-8")))
        if (
            len(self.trust_root.commitments) != 64
            or len(set(ledger_ids)) != 64
            or ledger_ids != expected_ids
            or commitment_ids != ledger_ids
            or artifact_ids != ledger_ids
        ):
            raise ValueError("clean benchmark identities")
        for row, commitment, artifact in zip(
            self.ledger, self.trust_root.commitments, self.artifacts, strict=True
        ):
            ObservedArtifactV1.from_dict(artifact.to_dict())
            expected_action = _ACTION_MENU[row.assignment]
            expected_members = _members(row.assignment)
            expected_target_binding = sha256_json(row.target.to_dict())
            partner_index = row.target_index ^ 2
            expected_partner_binding = sha256_json(
                SyntheticTargetV1(
                    schema_version="synthetic-target/v1",
                    unit_id=(f"syn-target-{row.site_id[-2:]}-{partner_index:02d}"),
                    site_id=row.site_id,
                    target_index=partner_index,
                ).to_dict()
            )
            expected_terminal_owner = f"terminal-owner-{row.unit_id}"
            expected_terminal_value = sha256_json(
                [item.to_dict() for item in row.obligation_scores]
            )
            expected_weights = tuple(
                ScoreWeightV1(schema_version="score-weight/v1", key=key, weight=0.2)
                for key in _OBLIGATION_KEYS
            )
            expected_snapshot = {
                "schema_version": "policy-information-snapshot/v1",
                "study_id": self.study_id,
                "site_id": row.site_id,
                "unit_id": row.unit_id,
                "stratum_id": row.stratum_id,
                "target_binding_sha256": expected_target_binding,
                "action_menu": list(_ACTION_MENU),
                "budget_limit": 5,
                "retry_limit": 0,
            }
            expected_snapshot_sha256 = sha256_json(expected_snapshot)
            expected_cost = 1.0 if row.assignment == 0 else 3.0
            expected_decision = {
                "schema_version": "policy-decision-event/v1",
                "policy_id": _POLICY_ID,
                "information_snapshot_sha256": expected_snapshot_sha256,
                "chosen_action": expected_action,
                "propensity": 0.5,
                "budget_limit": 5,
                "realized_cost": expected_cost,
                "retry_limit": 0,
            }
            expected_policy = PolicyRecordV1(
                schema_version="policy-record/v1",
                policy_id=_POLICY_ID,
                action_menu=_ACTION_MENU,
                information_snapshot_sha256=expected_snapshot_sha256,
                chosen_action=expected_action,
                propensity=0.5,
                budget_limit=5,
                realized_cost=expected_cost,
                retry_limit=0,
                decision_event_sha256=sha256_json(expected_decision),
            )

            if row.information_snapshot.to_dict() != expected_snapshot:
                raise ValueError("construction information snapshot")
            if row.decision_event.to_dict() != expected_decision:
                raise ValueError("construction decision event")
            commitment_fields = (
                commitment.schema_version,
                commitment.unit_id,
                commitment.site_id,
                commitment.stratum_id,
                commitment.assignment,
                commitment.requested_action_id,
                commitment.requested_members,
                commitment.target_binding_sha256,
                commitment.terminal_owner_id,
                commitment.terminal_value_sha256,
                commitment.scorer_weights,
                commitment.protocol_version,
                commitment.policy_record,
                commitment.allowed_target_binding_sha256,
                commitment.allowed_scorer_binding_sha256,
                commitment.allowed_protocol_versions,
                commitment.bound_certificates,
            )
            expected_commitment_fields = (
                "unit-commitment/v1",
                row.unit_id,
                row.site_id,
                row.stratum_id,
                row.assignment,
                expected_action,
                expected_members,
                expected_target_binding,
                expected_terminal_owner,
                expected_terminal_value,
                expected_weights,
                _PROTOCOL_VERSION,
                expected_policy,
                (expected_partner_binding,),
                (),
                (_COMPATIBLE_PROTOCOL_VERSION,),
                (),
            )
            if commitment_fields != expected_commitment_fields:
                raise ValueError("clean commitment cross binding")
            artifact_fields = (
                artifact.schema_version,
                artifact.study_id,
                artifact.unit_id,
                artifact.site_id,
                artifact.stratum_id,
                artifact.assignment,
                artifact.requested_action_id,
                artifact.requested_members,
                artifact.executed_action_id,
                artifact.executed_members,
                artifact.target_binding_sha256,
                artifact.terminal_owner_id,
                artifact.terminal_value_sha256,
                artifact.scorer_weights,
                artifact.protocol_version,
                artifact.policy_record,
                artifact.bound_certificate_ids,
            )
            expected_artifact_fields = (
                "observed-artifact/v1",
                self.study_id,
                row.unit_id,
                row.site_id,
                row.stratum_id,
                row.assignment,
                expected_action,
                expected_members,
                expected_action,
                expected_members,
                expected_target_binding,
                expected_terminal_owner,
                expected_terminal_value,
                expected_weights,
                _PROTOCOL_VERSION,
                expected_policy,
                (),
            )
            if artifact_fields != expected_artifact_fields:
                raise ValueError("clean artifact cross binding")
            if row.commitment_sha256 != sha256_json(commitment.to_dict()):
                raise ValueError("construction commitment digest")
            if row.artifact_sha256 != sha256_json(artifact.to_dict()):
                raise ValueError("construction artifact digest")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "ledger": [item.to_dict() for item in self.ledger],
            "trust_root": self.trust_root.to_dict(),
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


def _score_rows(unit_id: str, assignment: int) -> tuple[RationalObligationScoreV1, ...]:
    rows: list[RationalObligationScoreV1] = []
    for key in _OBLIGATION_KEYS:
        source = f"score/v1\0{unit_id}\0{key}\0{assignment}".encode("utf-8")
        numerator = int(hashlib.sha256(source).hexdigest()[:8], 16)
        rows.append(
            RationalObligationScoreV1(
                schema_version="rational-obligation-score/v1",
                key=key,
                numerator=numerator,
                denominator=_SCORE_DENOMINATOR,
            )
        )
    return tuple(rows)


def _members(assignment: int) -> tuple[str, ...]:
    if assignment == 0:
        return ("agent-builder",)
    return ("agent-builder", "agent-reviewer", "agent-router")


def _make_unit(
    site_index: int, target_index: int
) -> tuple[CleanConstructionRowV1, UnitCommitmentV1, ObservedArtifactV1]:
    site_id = f"syn-site-{site_index:02d}"
    unit_id = f"syn-target-{site_index:02d}-{target_index:02d}"
    assignment = target_index % 2
    action = _ACTION_MENU[assignment]
    members = _members(assignment)
    realized_cost = 1.0 if assignment == 0 else 3.0
    stratum_id = sha256_json(
        {"schema_version": "synthetic-stratum/v1", "site_id": site_id}
    )
    target = SyntheticTargetV1(
        schema_version="synthetic-target/v1",
        unit_id=unit_id,
        site_id=site_id,
        target_index=target_index,
    )
    target_binding_sha256 = sha256_json(target.to_dict())
    partner_index = target_index ^ 2
    partner_target = SyntheticTargetV1(
        schema_version="synthetic-target/v1",
        unit_id=f"syn-target-{site_index:02d}-{partner_index:02d}",
        site_id=site_id,
        target_index=partner_index,
    )
    partner_target_binding_sha256 = sha256_json(partner_target.to_dict())
    scores = _score_rows(unit_id, assignment)
    terminal_value_sha256 = sha256_json([item.to_dict() for item in scores])
    weights = tuple(
        ScoreWeightV1(schema_version="score-weight/v1", key=key, weight=0.2)
        for key in _OBLIGATION_KEYS
    )
    information_snapshot = PolicyInformationSnapshotV1(
        schema_version="policy-information-snapshot/v1",
        study_id=_STUDY_ID,
        site_id=site_id,
        unit_id=unit_id,
        stratum_id=stratum_id,
        target_binding_sha256=target_binding_sha256,
        action_menu=_ACTION_MENU,
        budget_limit=5,
        retry_limit=0,
    )
    information_snapshot_sha256 = sha256_json(information_snapshot.to_dict())
    decision_event = PolicyDecisionEventV1(
        schema_version="policy-decision-event/v1",
        policy_id=_POLICY_ID,
        information_snapshot_sha256=information_snapshot_sha256,
        chosen_action=action,
        propensity=0.5,
        budget_limit=5,
        realized_cost=realized_cost,
        retry_limit=0,
    )
    policy_record = PolicyRecordV1(
        schema_version="policy-record/v1",
        policy_id=_POLICY_ID,
        action_menu=_ACTION_MENU,
        information_snapshot_sha256=information_snapshot_sha256,
        chosen_action=action,
        propensity=0.5,
        budget_limit=5,
        realized_cost=realized_cost,
        retry_limit=0,
        decision_event_sha256=sha256_json(decision_event.to_dict()),
    )
    terminal_owner_id = f"terminal-owner-{unit_id}"
    commitment = UnitCommitmentV1(
        schema_version="unit-commitment/v1",
        unit_id=unit_id,
        site_id=site_id,
        stratum_id=stratum_id,
        assignment=assignment,
        requested_action_id=action,
        requested_members=members,
        target_binding_sha256=target_binding_sha256,
        terminal_owner_id=terminal_owner_id,
        terminal_value_sha256=terminal_value_sha256,
        scorer_weights=weights,
        protocol_version=_PROTOCOL_VERSION,
        policy_record=policy_record,
        allowed_target_binding_sha256=(partner_target_binding_sha256,),
        allowed_scorer_binding_sha256=(),
        allowed_protocol_versions=(_COMPATIBLE_PROTOCOL_VERSION,),
        bound_certificates=(),
    )
    artifact_payload: dict[str, object] = {
        "schema_version": "observed-artifact/v1",
        "study_id": _STUDY_ID,
        "unit_id": unit_id,
        "site_id": site_id,
        "stratum_id": stratum_id,
        "assignment": assignment,
        "requested_action_id": action,
        "requested_members": list(members),
        "executed_action_id": action,
        "executed_members": list(members),
        "target_binding_sha256": target_binding_sha256,
        "terminal_owner_id": terminal_owner_id,
        "terminal_value_sha256": terminal_value_sha256,
        "scorer_weights": [item.to_dict() for item in weights],
        "protocol_version": _PROTOCOL_VERSION,
        "policy_record": policy_record.to_dict(),
        "bound_certificate_ids": [],
    }
    artifact = ObservedArtifactV1.from_dict(
        {**artifact_payload, "payload_sha256": sha256_json(artifact_payload)}
    )
    row = CleanConstructionRowV1(
        schema_version="clean-construction-row/v1",
        study_id=_STUDY_ID,
        unit_id=unit_id,
        site_id=site_id,
        stratum_id=stratum_id,
        target_index=target_index,
        assignment=assignment,
        target=target,
        obligation_scores=scores,
        information_snapshot=information_snapshot,
        decision_event=decision_event,
        commitment_sha256=sha256_json(commitment.to_dict()),
        artifact_sha256=sha256_json(artifact.to_dict()),
    )
    return row, commitment, artifact


def generate_clean_benchmark() -> CleanBenchmarkV1:
    """Generate the exact deterministic 64-unit clean benchmark."""

    rows: list[CleanConstructionRowV1] = []
    commitments: list[UnitCommitmentV1] = []
    artifacts: list[ObservedArtifactV1] = []
    for site_index in range(8):
        for target_index in range(8):
            row, commitment, artifact = _make_unit(site_index, target_index)
            rows.append(row)
            commitments.append(commitment)
            artifacts.append(artifact)
    commitment_tuple = tuple(commitments)
    trust_root = TrustRootV1(
        schema_version="trust-root/v1",
        study_id=_STUDY_ID,
        commitments=commitment_tuple,
        commitments_sha256=sha256_json([item.to_dict() for item in commitment_tuple]),
    )
    return CleanBenchmarkV1(
        schema_version="clean-benchmark/v1",
        study_id=_STUDY_ID,
        ledger=tuple(rows),
        trust_root=trust_root,
        artifacts=tuple(artifacts),
    )


__all__ = [
    "CleanBenchmarkV1",
    "CleanConstructionRowV1",
    "PolicyDecisionEventV1",
    "PolicyInformationSnapshotV1",
    "RationalObligationScoreV1",
    "SyntheticTargetV1",
    "generate_clean_benchmark",
]
