"""Closed estimand receipt schemas and deterministic reportability decisions."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Literal


EstimandName = Literal["tau_itt", "tau_cb", "psi_natural"]
Reportability = Literal["CERTIFIED", "BOUNDED", "NOT_CERTIFIED"]

ESTIMANDS: tuple[EstimandName, ...] = ("tau_itt", "tau_cb", "psi_natural")
_STATUSES = frozenset(("CERTIFIED", "BOUNDED", "NOT_CERTIFIED"))
_BINDING_ORDER = ("Z", "A", "E", "B", "T", "S", "G", "P")
_REASON_BY_BINDING = {
    "Z": "Z_binding_unverified",
    "A": "A_binding_unverified",
    "E": "execution_noncompliance",
    "B": "B_binding_unverified",
    "T": "T_binding_unverified",
    "S": "S_binding_unverified",
    "G": "G_binding_unverified",
    "P": "P_binding_unverified",
}
_GLOBAL_REASONS = (
    "trust_root_mismatch",
    "study_binding_mismatch",
    "unit_coverage_mismatch",
    "artifact_identity_invalid",
)
_AFFECTED_ESTIMANDS = {
    "Z_IDENTITY": frozenset(ESTIMANDS),
    "Z_ASSIGNMENT": frozenset(("tau_itt", "tau_cb")),
    "A": frozenset(("tau_cb",)),
    "E": frozenset(("tau_cb",)),
    "B": frozenset(ESTIMANDS),
    "T": frozenset(ESTIMANDS),
    "S": frozenset(ESTIMANDS),
    "G": frozenset(ESTIMANDS),
    "P": frozenset(("psi_natural",)),
}
_HEX = frozenset("0123456789abcdef")


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_exact_keys(
    value: object, keys: tuple[str, ...], label: str
) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(f"{label} keys")
    return value


def _require_schema(value: object, expected: str, label: str) -> None:
    if value != expected:
        raise ValueError(f"{label} schema")


def _require_string(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(label)
    return value


def _require_digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(label)
    return value


def _require_integer(value: object, label: str, *, maximum: int | None = None) -> int:
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(label)
    return value


def _require_number(value: object, label: str) -> float | int:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(label)
    return value


def _require_tuple(value: object, label: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(label)
    return value


def _require_sorted_unique_strings(
    value: object,
    label: str,
    *,
    nonempty: bool = False,
    digests: bool = False,
) -> tuple[str, ...]:
    items = _require_tuple(value, label)
    if nonempty and not items:
        raise ValueError(label)
    checked = tuple(
        _require_digest(item, label) if digests else _require_string(item, label)
        for item in items
    )
    if len(set(checked)) != len(checked) or checked != tuple(
        sorted(checked, key=lambda item: item.encode("utf-8"))
    ):
        raise ValueError(label)
    return checked


def _array(value: object, label: str) -> tuple[object, ...]:
    if type(value) is not list:
        raise ValueError(label)
    return tuple(value)


@dataclass(frozen=True)
class ScoreWeightV1:
    schema_version: str
    key: str
    weight: float

    _KEYS = ("schema_version", "key", "weight")

    def __post_init__(self) -> None:
        _require_schema(self.schema_version, "score-weight/v1", "score weight")
        _require_string(self.key, "score weight key")
        weight = _require_number(self.weight, "score weight")
        if weight < 0:
            raise ValueError("score weight")

    @classmethod
    def from_dict(cls, value: object) -> ScoreWeightV1:
        row = _require_exact_keys(value, cls._KEYS, "score weight")
        return cls(
            schema_version=row["schema_version"],
            key=row["key"],
            weight=row["weight"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "key": self.key,
            "weight": self.weight,
        }


def _validate_weights(value: object, label: str) -> tuple[ScoreWeightV1, ...]:
    items = _require_tuple(value, label)
    if not items or any(type(item) is not ScoreWeightV1 for item in items):
        raise ValueError(label)
    for item in items:
        ScoreWeightV1.from_dict(item.to_dict())
    keys = tuple(item.key for item in items)
    if len(set(keys)) != len(keys) or keys != tuple(
        sorted(keys, key=lambda item: item.encode("utf-8"))
    ):
        raise ValueError(label)
    if not math.isclose(
        math.fsum(item.weight for item in items),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(label)
    return items


def _scorer_binding(weights: tuple[ScoreWeightV1, ...]) -> str:
    effective = [item.to_dict() for item in weights if item.weight != 0.0]
    return _canonical_sha256(effective)


@dataclass(frozen=True)
class PolicyRecordV1:
    schema_version: str
    policy_id: str
    action_menu: tuple[str, ...]
    information_snapshot_sha256: str
    chosen_action: str
    propensity: float
    budget_limit: int
    realized_cost: float
    retry_limit: int
    decision_event_sha256: str

    _KEYS = (
        "schema_version",
        "policy_id",
        "action_menu",
        "information_snapshot_sha256",
        "chosen_action",
        "propensity",
        "budget_limit",
        "realized_cost",
        "retry_limit",
        "decision_event_sha256",
    )

    def __post_init__(self) -> None:
        _require_schema(self.schema_version, "policy-record/v1", "policy record")
        _require_string(self.policy_id, "policy id")
        menu = _require_sorted_unique_strings(
            self.action_menu, "action menu", nonempty=True
        )
        _require_digest(self.information_snapshot_sha256, "information snapshot digest")
        chosen = _require_string(self.chosen_action, "chosen action")
        if chosen not in menu:
            raise ValueError("chosen action")
        propensity = _require_number(self.propensity, "propensity")
        if not 0 < propensity <= 1:
            raise ValueError("propensity")
        budget = _require_integer(self.budget_limit, "budget limit")
        cost = _require_number(self.realized_cost, "realized cost")
        if cost < 0 or cost > budget:
            raise ValueError("realized cost")
        _require_integer(self.retry_limit, "retry limit")
        _require_digest(self.decision_event_sha256, "decision event digest")

    @classmethod
    def from_dict(cls, value: object) -> PolicyRecordV1:
        row = _require_exact_keys(value, cls._KEYS, "policy record")
        return cls(
            schema_version=row["schema_version"],
            policy_id=row["policy_id"],
            action_menu=_array(row["action_menu"], "action menu"),
            information_snapshot_sha256=row["information_snapshot_sha256"],
            chosen_action=row["chosen_action"],
            propensity=row["propensity"],
            budget_limit=row["budget_limit"],
            realized_cost=row["realized_cost"],
            retry_limit=row["retry_limit"],
            decision_event_sha256=row["decision_event_sha256"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "action_menu": list(self.action_menu),
            "information_snapshot_sha256": self.information_snapshot_sha256,
            "chosen_action": self.chosen_action,
            "propensity": self.propensity,
            "budget_limit": self.budget_limit,
            "realized_cost": self.realized_cost,
            "retry_limit": self.retry_limit,
            "decision_event_sha256": self.decision_event_sha256,
        }


@dataclass(frozen=True)
class BoundCertificateV1:
    schema_version: str
    certificate_id: str
    estimand: str
    binding: str
    observed_binding_sha256: str
    lower: float
    upper: float

    _KEYS = (
        "schema_version",
        "certificate_id",
        "estimand",
        "binding",
        "observed_binding_sha256",
        "lower",
        "upper",
    )

    def __post_init__(self) -> None:
        _require_schema(
            self.schema_version, "bound-certificate/v1", "bound certificate"
        )
        _require_string(self.certificate_id, "certificate id")
        if self.estimand not in ESTIMANDS:
            raise ValueError("certificate estimand")
        if self.binding not in ("B", "T", "S"):
            raise ValueError("certificate binding")
        _require_digest(self.observed_binding_sha256, "observed binding digest")
        lower = _require_number(self.lower, "certificate lower")
        upper = _require_number(self.upper, "certificate upper")
        domain_lower = 0.0 if self.estimand == "psi_natural" else -1.0
        if lower < domain_lower or upper > 1.0 or lower > upper:
            raise ValueError("certificate bounds")

    @classmethod
    def from_dict(cls, value: object) -> BoundCertificateV1:
        row = _require_exact_keys(value, cls._KEYS, "bound certificate")
        return cls(**{key: row[key] for key in cls._KEYS})

    def to_dict(self) -> dict[str, object]:
        return {key: getattr(self, key) for key in self._KEYS}


@dataclass(frozen=True)
class UnitCommitmentV1:
    schema_version: str
    unit_id: str
    site_id: str
    stratum_id: str
    assignment: int
    requested_action_id: str
    requested_members: tuple[str, ...]
    target_binding_sha256: str
    terminal_owner_id: str
    terminal_value_sha256: str
    scorer_weights: tuple[ScoreWeightV1, ...]
    protocol_version: str
    policy_record: PolicyRecordV1
    allowed_target_binding_sha256: tuple[str, ...]
    allowed_scorer_binding_sha256: tuple[str, ...]
    allowed_protocol_versions: tuple[str, ...]
    bound_certificates: tuple[BoundCertificateV1, ...]

    _KEYS = (
        "schema_version",
        "unit_id",
        "site_id",
        "stratum_id",
        "assignment",
        "requested_action_id",
        "requested_members",
        "target_binding_sha256",
        "terminal_owner_id",
        "terminal_value_sha256",
        "scorer_weights",
        "protocol_version",
        "policy_record",
        "allowed_target_binding_sha256",
        "allowed_scorer_binding_sha256",
        "allowed_protocol_versions",
        "bound_certificates",
    )

    def __post_init__(self) -> None:
        _require_schema(self.schema_version, "unit-commitment/v1", "unit commitment")
        for value, label in (
            (self.unit_id, "unit id"),
            (self.site_id, "site id"),
            (self.stratum_id, "stratum id"),
            (self.requested_action_id, "requested action id"),
            (self.terminal_owner_id, "terminal owner id"),
            (self.protocol_version, "protocol version"),
        ):
            _require_string(value, label)
        _require_integer(self.assignment, "assignment", maximum=1)
        _require_sorted_unique_strings(self.requested_members, "requested members")
        target = _require_digest(self.target_binding_sha256, "target binding digest")
        _require_digest(self.terminal_value_sha256, "terminal value digest")
        weights = _validate_weights(self.scorer_weights, "scorer weights")
        if type(self.policy_record) is not PolicyRecordV1:
            raise ValueError("policy record")
        PolicyRecordV1.from_dict(self.policy_record.to_dict())
        allowed_targets = _require_sorted_unique_strings(
            self.allowed_target_binding_sha256,
            "allowed target bindings",
            digests=True,
        )
        allowed_scorers = _require_sorted_unique_strings(
            self.allowed_scorer_binding_sha256,
            "allowed scorer bindings",
            digests=True,
        )
        allowed_protocols = _require_sorted_unique_strings(
            self.allowed_protocol_versions, "allowed protocol versions"
        )
        if target in allowed_targets:
            raise ValueError("primary target repeated")
        if _scorer_binding(weights) in allowed_scorers:
            raise ValueError("primary scorer repeated")
        if self.protocol_version in allowed_protocols:
            raise ValueError("primary protocol repeated")
        certificates = _require_tuple(self.bound_certificates, "bound certificates")
        if any(type(item) is not BoundCertificateV1 for item in certificates):
            raise ValueError("bound certificates")
        for item in certificates:
            BoundCertificateV1.from_dict(item.to_dict())
        identities = tuple(item.certificate_id for item in certificates)
        if len(set(identities)) != len(identities) or identities != tuple(
            sorted(identities, key=lambda item: item.encode("utf-8"))
        ):
            raise ValueError("bound certificates")

    @classmethod
    def from_dict(cls, value: object) -> UnitCommitmentV1:
        row = _require_exact_keys(value, cls._KEYS, "unit commitment")
        weight_rows = _array(row["scorer_weights"], "scorer weights")
        certificate_rows = _array(row["bound_certificates"], "bound certificates")
        return cls(
            schema_version=row["schema_version"],
            unit_id=row["unit_id"],
            site_id=row["site_id"],
            stratum_id=row["stratum_id"],
            assignment=row["assignment"],
            requested_action_id=row["requested_action_id"],
            requested_members=_array(row["requested_members"], "requested members"),
            target_binding_sha256=row["target_binding_sha256"],
            terminal_owner_id=row["terminal_owner_id"],
            terminal_value_sha256=row["terminal_value_sha256"],
            scorer_weights=tuple(ScoreWeightV1.from_dict(item) for item in weight_rows),
            protocol_version=row["protocol_version"],
            policy_record=PolicyRecordV1.from_dict(row["policy_record"]),
            allowed_target_binding_sha256=_array(
                row["allowed_target_binding_sha256"], "allowed target bindings"
            ),
            allowed_scorer_binding_sha256=_array(
                row["allowed_scorer_binding_sha256"], "allowed scorer bindings"
            ),
            allowed_protocol_versions=_array(
                row["allowed_protocol_versions"], "allowed protocol versions"
            ),
            bound_certificates=tuple(
                BoundCertificateV1.from_dict(item) for item in certificate_rows
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "unit_id": self.unit_id,
            "site_id": self.site_id,
            "stratum_id": self.stratum_id,
            "assignment": self.assignment,
            "requested_action_id": self.requested_action_id,
            "requested_members": list(self.requested_members),
            "target_binding_sha256": self.target_binding_sha256,
            "terminal_owner_id": self.terminal_owner_id,
            "terminal_value_sha256": self.terminal_value_sha256,
            "scorer_weights": [item.to_dict() for item in self.scorer_weights],
            "protocol_version": self.protocol_version,
            "policy_record": self.policy_record.to_dict(),
            "allowed_target_binding_sha256": list(self.allowed_target_binding_sha256),
            "allowed_scorer_binding_sha256": list(self.allowed_scorer_binding_sha256),
            "allowed_protocol_versions": list(self.allowed_protocol_versions),
            "bound_certificates": [item.to_dict() for item in self.bound_certificates],
        }


@dataclass(frozen=True)
class TrustRootV1:
    schema_version: str
    study_id: str
    commitments: tuple[UnitCommitmentV1, ...]
    commitments_sha256: str

    _KEYS = ("schema_version", "study_id", "commitments", "commitments_sha256")

    def __post_init__(self) -> None:
        _require_schema(self.schema_version, "trust-root/v1", "trust root")
        _require_string(self.study_id, "study id")
        commitments = _require_tuple(self.commitments, "commitments")
        if not commitments or any(
            type(item) is not UnitCommitmentV1 for item in commitments
        ):
            raise ValueError("commitments")
        for item in commitments:
            UnitCommitmentV1.from_dict(item.to_dict())
        identities = tuple(item.unit_id for item in commitments)
        if len(set(identities)) != len(identities) or identities != tuple(
            sorted(identities, key=lambda item: item.encode("utf-8"))
        ):
            raise ValueError("commitments")
        digest = _require_digest(self.commitments_sha256, "commitments digest")
        expected = _canonical_sha256([item.to_dict() for item in commitments])
        if digest != expected:
            raise ValueError("commitments digest mismatch")

    @classmethod
    def from_dict(cls, value: object) -> TrustRootV1:
        row = _require_exact_keys(value, cls._KEYS, "trust root")
        commitment_rows = _array(row["commitments"], "commitments")
        return cls(
            schema_version=row["schema_version"],
            study_id=row["study_id"],
            commitments=tuple(
                UnitCommitmentV1.from_dict(item) for item in commitment_rows
            ),
            commitments_sha256=row["commitments_sha256"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "commitments": [item.to_dict() for item in self.commitments],
            "commitments_sha256": self.commitments_sha256,
        }


@dataclass(frozen=True)
class ObservedArtifactV1:
    schema_version: str
    study_id: str
    unit_id: str
    site_id: str
    stratum_id: str
    assignment: int
    requested_action_id: str
    requested_members: tuple[str, ...]
    executed_action_id: str
    executed_members: tuple[str, ...]
    target_binding_sha256: str
    terminal_owner_id: str
    terminal_value_sha256: str
    scorer_weights: tuple[ScoreWeightV1, ...]
    protocol_version: str
    policy_record: PolicyRecordV1
    bound_certificate_ids: tuple[str, ...]
    payload_sha256: str

    _KEYS = (
        "schema_version",
        "study_id",
        "unit_id",
        "site_id",
        "stratum_id",
        "assignment",
        "requested_action_id",
        "requested_members",
        "executed_action_id",
        "executed_members",
        "target_binding_sha256",
        "terminal_owner_id",
        "terminal_value_sha256",
        "scorer_weights",
        "protocol_version",
        "policy_record",
        "bound_certificate_ids",
        "payload_sha256",
    )

    def __post_init__(self) -> None:
        _require_schema(
            self.schema_version, "observed-artifact/v1", "observed artifact"
        )
        for value, label in (
            (self.study_id, "study id"),
            (self.unit_id, "unit id"),
            (self.site_id, "site id"),
            (self.stratum_id, "stratum id"),
            (self.requested_action_id, "requested action id"),
            (self.executed_action_id, "executed action id"),
            (self.terminal_owner_id, "terminal owner id"),
            (self.protocol_version, "protocol version"),
        ):
            _require_string(value, label)
        _require_integer(self.assignment, "assignment", maximum=1)
        _require_sorted_unique_strings(self.requested_members, "requested members")
        _require_sorted_unique_strings(self.executed_members, "executed members")
        _require_digest(self.target_binding_sha256, "target binding digest")
        _require_digest(self.terminal_value_sha256, "terminal value digest")
        _validate_weights(self.scorer_weights, "scorer weights")
        if type(self.policy_record) is not PolicyRecordV1:
            raise ValueError("policy record")
        PolicyRecordV1.from_dict(self.policy_record.to_dict())
        _require_sorted_unique_strings(
            self.bound_certificate_ids, "bound certificate ids"
        )
        digest = _require_digest(self.payload_sha256, "artifact payload digest")
        if digest != _canonical_sha256(self._payload_dict()):
            raise ValueError("artifact payload digest mismatch")

    def _payload_dict(self) -> dict[str, object]:
        value = self.to_dict()
        del value["payload_sha256"]
        return value

    @classmethod
    def from_dict(cls, value: object) -> ObservedArtifactV1:
        row = _require_exact_keys(value, cls._KEYS, "observed artifact")
        weight_rows = _array(row["scorer_weights"], "scorer weights")
        return cls(
            schema_version=row["schema_version"],
            study_id=row["study_id"],
            unit_id=row["unit_id"],
            site_id=row["site_id"],
            stratum_id=row["stratum_id"],
            assignment=row["assignment"],
            requested_action_id=row["requested_action_id"],
            requested_members=_array(row["requested_members"], "requested members"),
            executed_action_id=row["executed_action_id"],
            executed_members=_array(row["executed_members"], "executed members"),
            target_binding_sha256=row["target_binding_sha256"],
            terminal_owner_id=row["terminal_owner_id"],
            terminal_value_sha256=row["terminal_value_sha256"],
            scorer_weights=tuple(ScoreWeightV1.from_dict(item) for item in weight_rows),
            protocol_version=row["protocol_version"],
            policy_record=PolicyRecordV1.from_dict(row["policy_record"]),
            bound_certificate_ids=_array(
                row["bound_certificate_ids"], "bound certificate ids"
            ),
            payload_sha256=row["payload_sha256"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "unit_id": self.unit_id,
            "site_id": self.site_id,
            "stratum_id": self.stratum_id,
            "assignment": self.assignment,
            "requested_action_id": self.requested_action_id,
            "requested_members": list(self.requested_members),
            "executed_action_id": self.executed_action_id,
            "executed_members": list(self.executed_members),
            "target_binding_sha256": self.target_binding_sha256,
            "terminal_owner_id": self.terminal_owner_id,
            "terminal_value_sha256": self.terminal_value_sha256,
            "scorer_weights": [item.to_dict() for item in self.scorer_weights],
            "protocol_version": self.protocol_version,
            "policy_record": self.policy_record.to_dict(),
            "bound_certificate_ids": list(self.bound_certificate_ids),
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True)
class ObservedReceiptV1:
    schema_version: str
    study_id: str
    trust_root_sha256: str
    artifacts: tuple[ObservedArtifactV1, ...]
    payload_sha256: str

    _KEYS = (
        "schema_version",
        "study_id",
        "trust_root_sha256",
        "artifacts",
        "payload_sha256",
    )

    def __post_init__(self) -> None:
        _require_schema(self.schema_version, "observed-receipt/v1", "observed receipt")
        _require_string(self.study_id, "study id")
        _require_digest(self.trust_root_sha256, "trust root digest")
        artifacts = _require_tuple(self.artifacts, "artifacts")
        if not artifacts or any(
            type(item) is not ObservedArtifactV1 for item in artifacts
        ):
            raise ValueError("artifacts")
        for item in artifacts:
            ObservedArtifactV1.from_dict(item.to_dict())
        identities = tuple(item.unit_id for item in artifacts)
        if len(set(identities)) != len(identities) or identities != tuple(
            sorted(identities, key=lambda item: item.encode("utf-8"))
        ):
            raise ValueError("artifacts")
        digest = _require_digest(self.payload_sha256, "receipt payload digest")
        if digest != _canonical_sha256(self._payload_dict()):
            raise ValueError("receipt payload digest mismatch")

    def _payload_dict(self) -> dict[str, object]:
        value = self.to_dict()
        del value["payload_sha256"]
        return value

    @classmethod
    def from_dict(cls, value: object) -> ObservedReceiptV1:
        row = _require_exact_keys(value, cls._KEYS, "observed receipt")
        artifact_rows = _array(row["artifacts"], "artifacts")
        return cls(
            schema_version=row["schema_version"],
            study_id=row["study_id"],
            trust_root_sha256=row["trust_root_sha256"],
            artifacts=tuple(
                ObservedArtifactV1.from_dict(item) for item in artifact_rows
            ),
            payload_sha256=row["payload_sha256"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "trust_root_sha256": self.trust_root_sha256,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True)
class GateDecisionV1:
    schema_version: str
    estimand: str
    status: str
    reason_codes: tuple[str, ...]
    failed_bindings: tuple[str, ...]
    bound_lower: float | None = None
    bound_upper: float | None = None

    _KEYS = (
        "schema_version",
        "estimand",
        "status",
        "reason_codes",
        "failed_bindings",
        "bound_lower",
        "bound_upper",
    )

    def __post_init__(self) -> None:
        _require_schema(self.schema_version, "gate-decision/v1", "gate decision")
        if self.estimand not in ESTIMANDS:
            raise ValueError("gate estimand")
        if self.status not in _STATUSES:
            raise ValueError("gate status")
        reasons = _require_tuple(self.reason_codes, "reason codes")
        bindings = _require_tuple(self.failed_bindings, "failed bindings")
        if any(type(item) is not str for item in reasons):
            raise ValueError("reason codes")
        if any(item not in _BINDING_ORDER for item in bindings):
            raise ValueError("failed bindings")
        if len(set(bindings)) != len(bindings) or bindings != tuple(
            item for item in _BINDING_ORDER if item in bindings
        ):
            raise ValueError("failed bindings")
        if len(set(reasons)) != len(reasons):
            raise ValueError("reason codes")
        binding_reasons = tuple(_REASON_BY_BINDING[item] for item in bindings)
        if bindings:
            if reasons != binding_reasons:
                raise ValueError("reason codes")
        elif reasons and (len(reasons) != 1 or reasons[0] not in _GLOBAL_REASONS):
            raise ValueError("reason codes")
        if self.status == "BOUNDED":
            lower = _require_number(self.bound_lower, "bound lower")
            upper = _require_number(self.bound_upper, "bound upper")
            if lower > upper:
                raise ValueError("decision bounds")
        elif self.bound_lower is not None or self.bound_upper is not None:
            raise ValueError("decision bounds")

    @classmethod
    def from_dict(cls, value: object) -> GateDecisionV1:
        row = _require_exact_keys(value, cls._KEYS, "gate decision")
        return cls(
            schema_version=row["schema_version"],
            estimand=row["estimand"],
            status=row["status"],
            reason_codes=_array(row["reason_codes"], "reason codes"),
            failed_bindings=_array(row["failed_bindings"], "failed bindings"),
            bound_lower=row["bound_lower"],
            bound_upper=row["bound_upper"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "estimand": self.estimand,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "failed_bindings": list(self.failed_bindings),
            "bound_lower": self.bound_lower,
            "bound_upper": self.bound_upper,
        }


def _global_decisions(reason: str) -> tuple[GateDecisionV1, ...]:
    return tuple(
        GateDecisionV1(
            schema_version="gate-decision/v1",
            estimand=estimand,
            status="NOT_CERTIFIED",
            reason_codes=(reason,),
            failed_bindings=(),
        )
        for estimand in ESTIMANDS
    )


def _matching_certificates(
    commitment: UnitCommitmentV1,
    artifact: ObservedArtifactV1,
    estimand: str,
    binding: str,
    observed_binding_sha256: str,
) -> tuple[BoundCertificateV1, ...]:
    cited = set(artifact.bound_certificate_ids)
    return tuple(
        certificate
        for certificate in commitment.bound_certificates
        if certificate.certificate_id in cited
        and certificate.estimand == estimand
        and certificate.binding == binding
        and certificate.observed_binding_sha256 == observed_binding_sha256
    )


def evaluate_reportability(
    receipt: ObservedReceiptV1,
    trust_root: TrustRootV1,
) -> tuple[GateDecisionV1, ...]:
    """Evaluate the closed binding lattice in fixed estimand order."""

    try:
        validated_root = TrustRootV1.from_dict(trust_root.to_dict())
    except (AttributeError, TypeError, ValueError):
        return _global_decisions("trust_root_mismatch")

    expected_root_digest = _canonical_sha256(validated_root.to_dict())
    try:
        if receipt.trust_root_sha256 != expected_root_digest:
            return _global_decisions("trust_root_mismatch")
        if receipt.study_id != validated_root.study_id or any(
            artifact.study_id != receipt.study_id for artifact in receipt.artifacts
        ):
            return _global_decisions("study_binding_mismatch")
    except (AttributeError, TypeError):
        return _global_decisions("artifact_identity_invalid")

    try:
        committed_ids = tuple(item.unit_id for item in validated_root.commitments)
        artifact_ids = tuple(item.unit_id for item in receipt.artifacts)
        if (
            len(artifact_ids) != len(committed_ids)
            or len(set(artifact_ids)) != len(artifact_ids)
            or set(artifact_ids) != set(committed_ids)
        ):
            return _global_decisions("unit_coverage_mismatch")
    except (AttributeError, TypeError):
        return _global_decisions("unit_coverage_mismatch")

    try:
        validated_receipt = ObservedReceiptV1.from_dict(receipt.to_dict())
    except (AttributeError, TypeError, ValueError):
        return _global_decisions("artifact_identity_invalid")

    commitments = {item.unit_id: item for item in validated_root.commitments}
    artifacts = {item.unit_id: item for item in validated_receipt.artifacts}
    failed: dict[str, set[str]] = {estimand: set() for estimand in ESTIMANDS}
    hard_failure: dict[str, bool] = {estimand: False for estimand in ESTIMANDS}
    bounds: dict[str, list[tuple[float, float]]] = {
        estimand: [] for estimand in ESTIMANDS
    }
    recoverable: dict[str, list[tuple[UnitCommitmentV1, ObservedArtifactV1, str]]] = {
        binding: [] for binding in ("B", "T", "S")
    }

    def add_hard(binding: str, affected: frozenset[str]) -> None:
        for estimand in affected:
            failed[estimand].add(binding)
            hard_failure[estimand] = True

    for unit_id in committed_ids:
        commitment = commitments[unit_id]
        artifact = artifacts[unit_id]
        if (
            artifact.unit_id != commitment.unit_id
            or artifact.site_id != commitment.site_id
            or artifact.stratum_id != commitment.stratum_id
        ):
            add_hard("Z", _AFFECTED_ESTIMANDS["Z_IDENTITY"])
        if artifact.assignment != commitment.assignment:
            add_hard("Z", _AFFECTED_ESTIMANDS["Z_ASSIGNMENT"])
        if (
            artifact.requested_action_id != commitment.requested_action_id
            or artifact.requested_members != commitment.requested_members
        ):
            add_hard("A", _AFFECTED_ESTIMANDS["A"])
        if (
            artifact.executed_action_id != commitment.requested_action_id
            or artifact.executed_members != commitment.requested_members
        ):
            add_hard("E", _AFFECTED_ESTIMANDS["E"])

        if artifact.target_binding_sha256 != commitment.target_binding_sha256:
            if (
                artifact.target_binding_sha256
                not in commitment.allowed_target_binding_sha256
            ):
                recoverable["B"].append(
                    (commitment, artifact, artifact.target_binding_sha256)
                )
        if (
            artifact.terminal_owner_id != commitment.terminal_owner_id
            or artifact.terminal_value_sha256 != commitment.terminal_value_sha256
        ):
            recoverable["T"].append(
                (
                    commitment,
                    artifact,
                    _canonical_sha256(
                        {
                            "terminal_owner_id": artifact.terminal_owner_id,
                            "terminal_value_sha256": artifact.terminal_value_sha256,
                        }
                    ),
                )
            )
        observed_scorer = _scorer_binding(artifact.scorer_weights)
        committed_scorer = _scorer_binding(commitment.scorer_weights)
        if observed_scorer != committed_scorer:
            if observed_scorer not in commitment.allowed_scorer_binding_sha256:
                recoverable["S"].append((commitment, artifact, observed_scorer))
        if (
            artifact.protocol_version != commitment.protocol_version
            and artifact.protocol_version not in commitment.allowed_protocol_versions
        ):
            add_hard("G", _AFFECTED_ESTIMANDS["G"])
        if artifact.policy_record != commitment.policy_record:
            add_hard("P", _AFFECTED_ESTIMANDS["P"])

    for binding in ("B", "T", "S"):
        mismatches = recoverable[binding]
        if not mismatches:
            continue
        for estimand in _AFFECTED_ESTIMANDS[binding]:
            failed[estimand].add(binding)
            covered_bounds: list[tuple[float, float]] = []
            fully_covered = True
            for commitment, artifact, observed_digest in mismatches:
                certificates = _matching_certificates(
                    commitment,
                    artifact,
                    estimand,
                    binding,
                    observed_digest,
                )
                if not certificates:
                    fully_covered = False
                    break
                covered_bounds.extend(
                    (certificate.lower, certificate.upper)
                    for certificate in certificates
                )
            if fully_covered:
                bounds[estimand].extend(covered_bounds)
            else:
                hard_failure[estimand] = True

    decisions: list[GateDecisionV1] = []
    for estimand in ESTIMANDS:
        binding_tuple = tuple(
            item for item in _BINDING_ORDER if item in failed[estimand]
        )
        reason_tuple = tuple(_REASON_BY_BINDING[item] for item in binding_tuple)
        if hard_failure[estimand]:
            status = "NOT_CERTIFIED"
            lower = upper = None
        elif bounds[estimand]:
            status = "BOUNDED"
            lower = min(item[0] for item in bounds[estimand])
            upper = max(item[1] for item in bounds[estimand])
        else:
            status = "CERTIFIED"
            lower = upper = None
        decisions.append(
            GateDecisionV1(
                schema_version="gate-decision/v1",
                estimand=estimand,
                status=status,
                reason_codes=reason_tuple,
                failed_bindings=binding_tuple,
                bound_lower=lower,
                bound_upper=upper,
            )
        )
    return tuple(decisions)
