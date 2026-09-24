"""Byte-only public evaluators for the estimand-receipt benchmark."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from iclr2027.estimand_receipts import (
    ESTIMANDS,
    GateDecisionV1,
    ObservedArtifactV1,
    ObservedReceiptV1,
    TrustRootV1,
    UnitCommitmentV1,
    evaluate_reportability,
)


CONFIGURATIONS = (
    "completion_only",
    "hash_only",
    "trace_schema_closure",
    "field_complete_no_semantics",
    "ablate_E",
    "ablate_B",
    "ablate_T",
    "ablate_S",
    "ablate_G",
    "ablate_P",
    "full_estimand_gate",
)
_CONFIGURATION_INDEX = {name: index for index, name in enumerate(CONFIGURATIONS)}
_ESTIMAND_INDEX = {name: index for index, name in enumerate(ESTIMANDS)}
_BINDING_ORDER = ("Z", "A", "E", "B", "T", "S", "G", "P")
_STATUSES = frozenset(("CERTIFIED", "BOUNDED", "NOT_CERTIFIED"))
_HEX = frozenset("0123456789abcdef")
_PUBLIC_ROW_KEYS = ("schema_version", "case_id", "artifact")
_ARTIFACT_KEYS = (
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
_POLICY_KEYS = (
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
_WEIGHT_KEYS = ("schema_version", "key", "weight")
_TRUST_ROOT_KEYS = (
    "schema_version",
    "study_id",
    "commitments",
    "commitments_sha256",
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(label)
    return value


def _require_string_tuple(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or not item for item in value
    ):
        raise ValueError(label)
    if len(set(value)) != len(value):
        raise ValueError(label)
    return value


def _pairs_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _load_canonical(value: object, label: str) -> object:
    if type(value) is not bytes:
        raise ValueError(label)
    try:
        parsed = json.loads(
            value.decode("utf-8"),
            object_pairs_hook=_pairs_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(label) from exc
    try:
        canonical = _canonical_bytes(parsed)
    except (TypeError, ValueError) as exc:
        raise ValueError(label) from exc
    if canonical != value:
        raise ValueError(label)
    return parsed


@dataclass(frozen=True)
class ExactBoundsV1:
    lower: float | int
    upper: float | int

    def __post_init__(self) -> None:
        if (
            type(self.lower) not in (int, float)
            or type(self.upper) not in (int, float)
            or not math.isfinite(self.lower)
            or not math.isfinite(self.upper)
            or self.lower > self.upper
        ):
            raise ValueError("bounds")

    @classmethod
    def from_dict(cls, value: object) -> ExactBoundsV1:
        if type(value) is not dict or set(value) != {"lower", "upper"}:
            raise ValueError("bounds")
        return cls(lower=value["lower"], upper=value["upper"])

    def to_dict(self) -> dict[str, object]:
        return {"lower": self.lower, "upper": self.upper}


@dataclass(frozen=True)
class PublicEvaluatorDecisionV1:
    """One label-free public decision with a self-authenticating digest."""

    public_case_id: str
    configuration: str
    estimand: str
    status: str
    reason_codes: tuple[str, ...]
    failed_bindings: tuple[str, ...]
    bounds: ExactBoundsV1 | None
    canonical_decision_digest: str

    _KEYS = (
        "public_case_id",
        "configuration",
        "estimand",
        "status",
        "reason_codes",
        "failed_bindings",
        "bounds",
        "canonical_decision_digest",
    )

    def __post_init__(self) -> None:
        _require_digest(self.public_case_id, "public case id")
        if self.configuration not in CONFIGURATIONS:
            raise ValueError("configuration")
        if self.estimand not in ESTIMANDS:
            raise ValueError("estimand")
        if self.status not in _STATUSES:
            raise ValueError("status")
        _require_string_tuple(self.reason_codes, "reason codes")
        bindings = _require_string_tuple(self.failed_bindings, "failed bindings")
        if bindings != tuple(item for item in _BINDING_ORDER if item in bindings):
            raise ValueError("failed bindings")
        if self.status == "BOUNDED":
            if type(self.bounds) is not ExactBoundsV1:
                raise ValueError("bounds")
        elif self.bounds is not None:
            raise ValueError("bounds")
        digest = _require_digest(
            self.canonical_decision_digest, "canonical decision digest"
        )
        if digest != _sha256_json(self._payload_dict()):
            raise ValueError("canonical decision digest mismatch")

    @classmethod
    def create(
        cls,
        *,
        public_case_id: str,
        configuration: str,
        estimand: str,
        status: str,
        reason_codes: tuple[str, ...],
        failed_bindings: tuple[str, ...],
        bounds: ExactBoundsV1 | None,
    ) -> PublicEvaluatorDecisionV1:
        payload = {
            "public_case_id": public_case_id,
            "configuration": configuration,
            "estimand": estimand,
            "status": status,
            "reason_codes": list(reason_codes),
            "failed_bindings": list(failed_bindings),
            "bounds": None if bounds is None else bounds.to_dict(),
        }
        return cls(
            public_case_id=public_case_id,
            configuration=configuration,
            estimand=estimand,
            status=status,
            reason_codes=reason_codes,
            failed_bindings=failed_bindings,
            bounds=bounds,
            canonical_decision_digest=_sha256_json(payload),
        )

    @classmethod
    def from_dict(cls, value: object) -> PublicEvaluatorDecisionV1:
        if type(value) is not dict or set(value) != set(cls._KEYS):
            raise ValueError("public decision")
        reasons = value["reason_codes"]
        bindings = value["failed_bindings"]
        if type(reasons) is not list or type(bindings) is not list:
            raise ValueError("public decision")
        raw_bounds = value["bounds"]
        bounds = None if raw_bounds is None else ExactBoundsV1.from_dict(raw_bounds)
        return cls(
            public_case_id=value["public_case_id"],
            configuration=value["configuration"],
            estimand=value["estimand"],
            status=value["status"],
            reason_codes=tuple(reasons),
            failed_bindings=tuple(bindings),
            bounds=bounds,
            canonical_decision_digest=value["canonical_decision_digest"],
        )

    def _payload_dict(self) -> dict[str, object]:
        value = self.to_dict()
        del value["canonical_decision_digest"]
        return value

    def to_dict(self) -> dict[str, object]:
        return {
            "public_case_id": self.public_case_id,
            "configuration": self.configuration,
            "estimand": self.estimand,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "failed_bindings": list(self.failed_bindings),
            "bounds": None if self.bounds is None else self.bounds.to_dict(),
            "canonical_decision_digest": self.canonical_decision_digest,
        }


def _one_commitment_root(
    source: TrustRootV1, commitment: UnitCommitmentV1
) -> TrustRootV1:
    row = commitment.to_dict()
    return TrustRootV1.from_dict(
        {
            "schema_version": "trust-root/v1",
            "study_id": source.study_id,
            "commitments": [row],
            "commitments_sha256": _sha256_json([row]),
        }
    )


def _full_decisions(
    source_root: TrustRootV1,
    commitment: UnitCommitmentV1,
    artifact: ObservedArtifactV1,
) -> tuple[GateDecisionV1, ...]:
    one_root = _one_commitment_root(source_root, commitment)
    receipt_payload = {
        "schema_version": "observed-receipt/v1",
        "study_id": one_root.study_id,
        "trust_root_sha256": _sha256_json(one_root.to_dict()),
        "artifacts": [artifact.to_dict()],
    }
    receipt = ObservedReceiptV1.from_dict(
        {**receipt_payload, "payload_sha256": _sha256_json(receipt_payload)}
    )
    return evaluate_reportability(receipt, one_root)


def _ablate(decision: GateDecisionV1, binding: str) -> GateDecisionV1:
    if binding not in decision.failed_bindings:
        return decision
    retained = tuple(
        (failed, reason)
        for failed, reason in zip(
            decision.failed_bindings, decision.reason_codes, strict=True
        )
        if failed != binding
    )
    if not retained:
        return GateDecisionV1(
            schema_version="gate-decision/v1",
            estimand=decision.estimand,
            status="CERTIFIED",
            reason_codes=(),
            failed_bindings=(),
        )
    return GateDecisionV1(
        schema_version="gate-decision/v1",
        estimand=decision.estimand,
        status="NOT_CERTIFIED",
        reason_codes=tuple(item[1] for item in retained),
        failed_bindings=tuple(item[0] for item in retained),
    )


def _public_decision(
    case_id: str, configuration: str, decision: GateDecisionV1
) -> PublicEvaluatorDecisionV1:
    bounds = None
    if decision.status == "BOUNDED":
        bounds = ExactBoundsV1(
            lower=decision.bound_lower,
            upper=decision.bound_upper,
        )
    return PublicEvaluatorDecisionV1.create(
        public_case_id=case_id,
        configuration=configuration,
        estimand=decision.estimand,
        status=decision.status,
        reason_codes=decision.reason_codes,
        failed_bindings=decision.failed_bindings,
        bounds=bounds,
    )


def _certified_decisions() -> tuple[GateDecisionV1, ...]:
    return tuple(
        GateDecisionV1(
            schema_version="gate-decision/v1",
            estimand=estimand,
            status="CERTIFIED",
            reason_codes=(),
            failed_bindings=(),
        )
        for estimand in ESTIMANDS
    )


def _parse_trust_root(value: bytes) -> TrustRootV1:
    raw = _load_canonical(value, "trust root bytes")
    if type(raw) is not dict:
        raise ValueError("trust root bytes")
    try:
        return TrustRootV1.from_dict(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("trust root bytes") from exc


def _parse_public_envelope(value: bytes) -> tuple[str, dict[str, object]]:
    raw = _load_canonical(value, "public artifact bytes")
    if type(raw) is not dict or set(raw) != set(_PUBLIC_ROW_KEYS):
        raise ValueError("public artifact row")
    if raw["schema_version"] != "public-artifact-row/v1":
        raise ValueError("public artifact row")
    case_id = _require_digest(raw["case_id"], "public case id")
    artifact = raw["artifact"]
    if type(artifact) is not dict or not artifact:
        raise ValueError("public artifact row")
    return case_id, artifact


def _validate_artifact_hash(artifact: dict[str, object]) -> None:
    if "payload_sha256" not in artifact:
        raise ValueError("artifact payload hash")
    observed = _require_digest(artifact["payload_sha256"], "artifact payload hash")
    payload = dict(artifact)
    del payload["payload_sha256"]
    if observed != _sha256_json(payload):
        raise ValueError("artifact payload hash")


def _parse_referential_root(value: bytes) -> tuple[str, frozenset[str]]:
    raw = _load_canonical(value, "trust root bytes")
    if (
        type(raw) is not dict
        or set(raw) != set(_TRUST_ROOT_KEYS)
        or raw["schema_version"] != "trust-root/v1"
        or type(raw["study_id"]) is not str
        or not raw["study_id"]
        or type(raw["commitments"]) is not list
        or not raw["commitments"]
    ):
        raise ValueError("trust root bytes")
    unit_ids: list[str] = []
    for commitment in raw["commitments"]:
        if (
            type(commitment) is not dict
            or type(commitment.get("unit_id")) is not str
            or not commitment["unit_id"]
        ):
            raise ValueError("trust root bytes")
        unit_ids.append(commitment["unit_id"])
    if len(set(unit_ids)) != len(unit_ids):
        raise ValueError("trust root bytes")
    return raw["study_id"], frozenset(unit_ids)


def _validate_trace_schema(artifact: dict[str, object]) -> None:
    if (
        set(artifact) != set(_ARTIFACT_KEYS)
        or artifact["schema_version"] != "observed-artifact/v1"
        or type(artifact["scorer_weights"]) is not list
        or not artifact["scorer_weights"]
        or type(artifact["policy_record"]) is not dict
        or set(artifact["policy_record"]) != set(_POLICY_KEYS)
        or artifact["policy_record"]["schema_version"] != "policy-record/v1"
        or any(
            type(value) is not list
            for value in (
                artifact["requested_members"],
                artifact["executed_members"],
                artifact["bound_certificate_ids"],
            )
        )
        or any(
            type(weight) is not dict
            or set(weight) != set(_WEIGHT_KEYS)
            or weight["schema_version"] != "score-weight/v1"
            for weight in artifact["scorer_weights"]
        )
    ):
        raise ValueError("artifact schema closure")


def _trace_row(
    value: bytes, root_study_id: str, root_unit_ids: frozenset[str]
) -> tuple[str, dict[str, object]]:
    case_id, artifact = _parse_public_envelope(value)
    _validate_artifact_hash(artifact)
    _validate_trace_schema(artifact)
    if (
        artifact["study_id"] != root_study_id
        or artifact["unit_id"] not in root_unit_ids
    ):
        raise ValueError("artifact referential identity")
    return case_id, artifact


def _field_row(
    value: bytes, root_study_id: str, root_unit_ids: frozenset[str]
) -> tuple[str, ObservedArtifactV1]:
    case_id, raw_artifact = _trace_row(value, root_study_id, root_unit_ids)
    try:
        artifact = ObservedArtifactV1.from_dict(raw_artifact)
    except (TypeError, ValueError) as exc:
        raise ValueError("public artifact row") from exc
    return case_id, artifact


def _validate_public_input_tuple(public_artifact_bytes: tuple[bytes, ...]) -> None:
    if type(public_artifact_bytes) is not tuple or not public_artifact_bytes:
        raise ValueError("public artifact bytes")


def _validate_unique_case_ids(case_ids: tuple[str, ...]) -> None:
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("duplicate public case id")


def _baseline_rows(
    configuration: str,
    public_artifact_bytes: tuple[bytes, ...],
    trust_root_bytes: bytes,
) -> tuple[PublicEvaluatorDecisionV1, ...]:
    if configuration not in CONFIGURATIONS[:4]:
        raise ValueError("baseline configuration")
    _validate_public_input_tuple(public_artifact_bytes)
    referential_root = None
    if configuration in ("trace_schema_closure", "field_complete_no_semantics"):
        referential_root = _parse_referential_root(trust_root_bytes)

    parsed: list[tuple[str, object]] = []
    for value in public_artifact_bytes:
        if configuration == "completion_only":
            parsed.append(_parse_public_envelope(value))
        elif configuration == "hash_only":
            case_id, artifact = _parse_public_envelope(value)
            _validate_artifact_hash(artifact)
            parsed.append((case_id, artifact))
        elif configuration == "trace_schema_closure":
            parsed.append(_trace_row(value, *referential_root))
        else:
            parsed.append(_field_row(value, *referential_root))
    case_ids = tuple(item[0] for item in parsed)
    _validate_unique_case_ids(case_ids)
    decisions = _certified_decisions()
    output = tuple(
        _public_decision(case_id, configuration, decision)
        for case_id in case_ids
        for decision in decisions
    )
    return tuple(
        sorted(
            output,
            key=lambda row: (
                row.public_case_id.encode("utf-8"),
                _ESTIMAND_INDEX[row.estimand],
            ),
        )
    )


def _semantic_rows(
    public_artifact_bytes: tuple[bytes, ...], trust_root_bytes: bytes
) -> tuple[PublicEvaluatorDecisionV1, ...]:
    _validate_public_input_tuple(public_artifact_bytes)
    root = _parse_trust_root(trust_root_bytes)
    commitments = {item.unit_id: item for item in root.commitments}
    referential_root = (root.study_id, frozenset(commitments))
    parsed = tuple(
        _field_row(value, *referential_root) for value in public_artifact_bytes
    )
    _validate_unique_case_ids(tuple(item[0] for item in parsed))
    output: list[PublicEvaluatorDecisionV1] = []
    for case_id, artifact in parsed:
        commitment = commitments[artifact.unit_id]
        full = _full_decisions(root, commitment, artifact)
        decisions_by_configuration = {
            **{
                f"ablate_{binding}": tuple(
                    _ablate(decision, binding) for decision in full
                )
                for binding in ("E", "B", "T", "S", "G", "P")
            },
            "full_estimand_gate": full,
        }
        for configuration in CONFIGURATIONS[4:]:
            output.extend(
                _public_decision(case_id, configuration, decision)
                for decision in decisions_by_configuration[configuration]
            )
    output.sort(
        key=lambda row: (
            row.public_case_id.encode("utf-8"),
            _CONFIGURATION_INDEX[row.configuration],
            _ESTIMAND_INDEX[row.estimand],
        )
    )
    return tuple(output)


def evaluate_configuration(
    configuration: str,
    public_artifact_bytes: tuple[bytes, ...],
    trust_root_bytes: bytes,
) -> tuple[PublicEvaluatorDecisionV1, ...]:
    """Evaluate exactly one frozen information path."""

    if configuration not in CONFIGURATIONS:
        raise ValueError("configuration")
    if configuration in CONFIGURATIONS[:4]:
        return _baseline_rows(configuration, public_artifact_bytes, trust_root_bytes)
    return tuple(
        row
        for row in _semantic_rows(public_artifact_bytes, trust_root_bytes)
        if row.configuration == configuration
    )


def evaluate_frozen_artifacts(
    public_artifact_bytes: tuple[bytes, ...], trust_root_bytes: bytes
) -> tuple[PublicEvaluatorDecisionV1, ...]:
    """Evaluate supplied anonymous bytes without consulting ambient metadata."""

    output: list[PublicEvaluatorDecisionV1] = []
    for configuration in CONFIGURATIONS[:4]:
        output.extend(
            _baseline_rows(configuration, public_artifact_bytes, trust_root_bytes)
        )
    output.extend(_semantic_rows(public_artifact_bytes, trust_root_bytes))
    output.sort(
        key=lambda row: (
            row.public_case_id.encode("utf-8"),
            _CONFIGURATION_INDEX[row.configuration],
            _ESTIMAND_INDEX[row.estimand],
        )
    )
    return tuple(output)


def _validate_output_lattice(
    rows: tuple[PublicEvaluatorDecisionV1, ...],
) -> tuple[PublicEvaluatorDecisionV1, ...]:
    if (
        type(rows) is not tuple
        or not rows
        or any(type(item) is not PublicEvaluatorDecisionV1 for item in rows)
    ):
        raise ValueError("evaluator outputs")
    for item in rows:
        PublicEvaluatorDecisionV1.from_dict(item.to_dict())
    identities = tuple(
        (item.public_case_id, item.configuration, item.estimand) for item in rows
    )
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate evaluator output")
    case_ids = {item.public_case_id for item in rows}
    expected = {
        (case_id, configuration, estimand)
        for case_id in case_ids
        for configuration in CONFIGURATIONS
        for estimand in ESTIMANDS
    }
    if set(identities) != expected:
        raise ValueError("incomplete evaluator outputs")
    return rows


def freeze_evaluator_outputs(rows: tuple[PublicEvaluatorDecisionV1, ...]) -> bytes:
    """Freeze complete outputs in canonical public order."""

    checked = _validate_output_lattice(rows)
    ordered = sorted(
        checked,
        key=lambda row: (
            row.public_case_id.encode("utf-8"),
            _CONFIGURATION_INDEX[row.configuration],
            _ESTIMAND_INDEX[row.estimand],
        ),
    )
    return _canonical_bytes(
        {
            "schema_version": "estimand-evaluator-outputs/v1",
            "rows": [item.to_dict() for item in ordered],
        }
    )


def parse_frozen_evaluator_outputs(
    value: bytes,
) -> tuple[PublicEvaluatorDecisionV1, ...]:
    """Validate frozen output bytes while ignoring row order."""

    raw = _load_canonical(value, "evaluator output bytes")
    if (
        type(raw) is not dict
        or set(raw) != {"schema_version", "rows"}
        or raw["schema_version"] != "estimand-evaluator-outputs/v1"
        or type(raw["rows"]) is not list
    ):
        raise ValueError("evaluator output bytes")
    try:
        rows = tuple(PublicEvaluatorDecisionV1.from_dict(item) for item in raw["rows"])
    except (TypeError, ValueError) as exc:
        raise ValueError("evaluator output bytes") from exc
    return _validate_output_lattice(rows)


__all__ = [
    "CONFIGURATIONS",
    "ExactBoundsV1",
    "PublicEvaluatorDecisionV1",
    "evaluate_configuration",
    "evaluate_frozen_artifacts",
    "freeze_evaluator_outputs",
    "parse_frozen_evaluator_outputs",
]
