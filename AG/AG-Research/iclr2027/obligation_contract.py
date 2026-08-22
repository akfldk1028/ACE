"""Immutable, leakage-safe controller state for obligation-aware coordination."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import math
from typing import Any

from .io import canonical_json as _canonical_json
from .io import sha256_json


OBLIGATION_FAMILIES = frozenset(
    {"law", "parking", "program", "geometry", "site/evidence"}
)
OBLIGATION_STATUSES = frozenset({"resolved", "unresolved", "unknown"})

_FORBIDDEN_CONTROLLER_KEYS = frozenset(
    {
        "blocking_issue_codes_gold",
        "evaluator_obligation_status",
        "evaluator_output",
        "expected_decision",
        "gold",
        "hidden_issue_codes",
        "mutation_family",
    }
)
_SPEC_KEYS = frozenset(
    {"obligation_id", "family", "weight", "hard", "public_basis_ids"}
)
_BELIEF_KEYS = frozenset(
    {"obligation_id", "status", "unresolved_probability", "evidence_ids"}
)
_STATE_KEYS = frozenset(
    {"case_id", "prefix_id", "beliefs", "hard_gate_passed", "cumulative_cost"}
)


class CoordinationAction(str, Enum):
    STOP = "STOP"
    SOLO_SYNTHESIS = "SOLO_SYNTHESIS"
    ASK_LAW = "ASK_LAW"
    ASK_PARKING = "ASK_PARKING"
    ASK_PROGRAM = "ASK_PROGRAM"
    ASK_GEOMETRY = "ASK_GEOMETRY"


def _is_forbidden_controller_key(key: str) -> bool:
    lowered = key.casefold()
    return (
        lowered in _FORBIDDEN_CONTROLLER_KEYS
        or lowered.startswith("gold_")
        or lowered.endswith("_gold")
    )


def _assert_controller_safe(value: Any, path: str = "controller") -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            if _is_forbidden_controller_key(key):
                raise ValueError(f"forbidden controller key at {path}.{key}")
            _assert_controller_safe(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, item in enumerate(value):
            _assert_controller_safe(item, f"{path}[{index}]")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _require_exact_keys(
    payload: Mapping[str, Any], expected: frozenset[str], label: str
) -> None:
    if any(not isinstance(key, str) for key in payload) or set(payload) != expected:
        missing = sorted(expected - set(payload))
        extra = sorted(str(key) for key in set(payload) - expected)
        raise ValueError(
            f"{label} must contain exact keys; missing={missing}, extra={extra}"
        )


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    result = value.strip()
    if not result:
        raise ValueError(f"{field} must be nonempty")
    return result


def _string_tuple(
    value: Any,
    field: str,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError(f"{field} must be a sequence of strings")
    result = tuple(_required_text(item, field) for item in value)
    if require_nonempty and not result:
        raise ValueError(f"{field} must be nonempty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    return result


def _finite_number(value: Any, field: str, *, minimum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    if result < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return 0.0 if result == 0.0 else result


def _native_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a native boolean")
    return value


class _CanonicalContract:
    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def sha256(self) -> str:
        return sha256_json(self.to_dict())


@dataclass(frozen=True)
class ObligationSpec(_CanonicalContract):
    obligation_id: str
    family: str
    weight: float
    hard: bool
    public_basis_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "obligation_id", _required_text(self.obligation_id, "obligation_id")
        )
        family = _required_text(self.family, "family")
        if family not in OBLIGATION_FAMILIES:
            raise ValueError(f"unsupported obligation family: {family}")
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "weight", _finite_number(self.weight, "weight", minimum=0.0))
        object.__setattr__(self, "hard", _native_bool(self.hard, "hard"))
        object.__setattr__(
            self,
            "public_basis_ids",
            _string_tuple(
                self.public_basis_ids,
                "public_basis_ids",
                require_nonempty=True,
            ),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObligationSpec":
        data = _require_mapping(payload, "obligation spec")
        _assert_controller_safe(data)
        _require_exact_keys(data, _SPEC_KEYS, "obligation spec")
        return cls(
            obligation_id=data["obligation_id"],
            family=data["family"],
            weight=data["weight"],
            hard=data["hard"],
            public_basis_ids=data["public_basis_ids"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "family": self.family,
            "weight": self.weight,
            "hard": self.hard,
            "public_basis_ids": list(self.public_basis_ids),
        }


@dataclass(frozen=True)
class ObligationBelief(_CanonicalContract):
    obligation_id: str
    status: str
    unresolved_probability: float
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "obligation_id", _required_text(self.obligation_id, "obligation_id")
        )
        status = _required_text(self.status, "status")
        if status not in OBLIGATION_STATUSES:
            raise ValueError(f"unsupported obligation status: {status}")
        object.__setattr__(self, "status", status)
        probability = _finite_number(
            self.unresolved_probability,
            "unresolved_probability",
            minimum=0.0,
        )
        if probability > 1.0:
            raise ValueError("unresolved_probability must be within [0, 1]")
        object.__setattr__(self, "unresolved_probability", probability)
        object.__setattr__(
            self,
            "evidence_ids",
            _string_tuple(self.evidence_ids, "evidence_ids"),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObligationBelief":
        data = _require_mapping(payload, "obligation belief")
        _assert_controller_safe(data)
        _require_exact_keys(data, _BELIEF_KEYS, "obligation belief")
        return cls(
            obligation_id=data["obligation_id"],
            status=data["status"],
            unresolved_probability=data["unresolved_probability"],
            evidence_ids=data["evidence_ids"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "status": self.status,
            "unresolved_probability": self.unresolved_probability,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class ObligationState(_CanonicalContract):
    case_id: str
    prefix_id: str
    beliefs: tuple[ObligationBelief, ...]
    hard_gate_passed: bool
    cumulative_cost: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", _required_text(self.case_id, "case_id"))
        object.__setattr__(
            self, "prefix_id", _required_text(self.prefix_id, "prefix_id")
        )
        if isinstance(self.beliefs, (str, bytes, bytearray)) or not isinstance(
            self.beliefs, Sequence
        ):
            raise TypeError("beliefs must be a sequence")
        beliefs = tuple(self.beliefs)
        if any(not isinstance(belief, ObligationBelief) for belief in beliefs):
            raise TypeError("beliefs must contain ObligationBelief values")
        obligation_ids = tuple(belief.obligation_id for belief in beliefs)
        if len(obligation_ids) != len(set(obligation_ids)):
            raise ValueError("belief obligation IDs must be unique")
        object.__setattr__(self, "beliefs", beliefs)
        object.__setattr__(
            self,
            "hard_gate_passed",
            _native_bool(self.hard_gate_passed, "hard_gate_passed"),
        )
        object.__setattr__(
            self,
            "cumulative_cost",
            _finite_number(self.cumulative_cost, "cumulative_cost", minimum=0.0),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObligationState":
        data = _require_mapping(payload, "obligation state")
        _assert_controller_safe(data)
        _require_exact_keys(data, _STATE_KEYS, "obligation state")
        raw_beliefs = data["beliefs"]
        if isinstance(raw_beliefs, (str, bytes, bytearray)) or not isinstance(
            raw_beliefs, Sequence
        ):
            raise TypeError("beliefs must be a sequence")
        return cls(
            case_id=data["case_id"],
            prefix_id=data["prefix_id"],
            beliefs=tuple(
                ObligationBelief.from_dict(
                    _require_mapping(belief, "obligation belief")
                )
                for belief in raw_beliefs
            ),
            hard_gate_passed=data["hard_gate_passed"],
            cumulative_cost=data["cumulative_cost"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "prefix_id": self.prefix_id,
            "beliefs": [belief.to_dict() for belief in self.beliefs],
            "hard_gate_passed": self.hard_gate_passed,
            "cumulative_cost": self.cumulative_cost,
        }


__all__ = (
    "CoordinationAction",
    "OBLIGATION_FAMILIES",
    "OBLIGATION_STATUSES",
    "ObligationBelief",
    "ObligationSpec",
    "ObligationState",
)
