"""Pre-outcome same-information and same-budget binding for the OACS study."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any

from .capability_binding import (
    CapabilityCrossoverPlan,
    ControllerCapabilityCatalog,
    validate_crossover_plan,
)
from .io import canonical_json
from .obligation_oracle import (
    BaselinePreOutcomeReadinessAuthority,
    MandatoryBaselineRoster,
    validate_baseline_pre_outcome_readiness,
)


_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_CORE_TREATMENT_IDS = (
    "solo",
    "rr3",
    "sel3",
    "swm3",
    "refl3",
    "debate3",
    "equal_information_router",
    "oacs",
)
_TREATMENT_FIELDS = (
    "model_binding_sha256",
    "public_input_projection_sha256",
    "token_budget",
    "call_budget",
    "timeout_seconds",
    "retry_policy_sha256",
    "common_synthesizer_sha256",
    "terminal_evaluator_sha256",
    "usage_accounting_sha256",
)
_TREATMENT_KEYS = frozenset(
    {
        "treatment_id",
        "treatment_family",
        "model_binding_sha256",
        "public_input_projection_sha256",
        "tool_catalog_sha256",
        "token_budget",
        "call_budget",
        "timeout_seconds",
        "retry_policy_sha256",
        "common_synthesizer_sha256",
        "terminal_evaluator_sha256",
        "usage_accounting_sha256",
    }
)
_CONTRACT_KEYS = frozenset(
    {
        "treatments",
        "capability_catalog",
        "capability_crossover_plan",
        "mandatory_baseline_roster",
        "e3_readiness",
    }
)
_EXPECTED_FAMILIES = {
    treatment_id: "core_mas" for treatment_id in _CORE_TREATMENT_IDS[:-1]
} | {"oacs": "oacs_capability"}


class StudyContractError(ValueError):
    """The frozen OACS mechanism-study comparison is invalid."""


class ParityFieldV1(str, Enum):
    MODEL_BINDING = "model_binding_sha256"
    PUBLIC_INPUT_PROJECTION = "public_input_projection_sha256"
    TOOL_CATALOG = "tool_catalog_sha256"
    TOKEN_BUDGET = "token_budget"
    CALL_BUDGET = "call_budget"
    TIMEOUT_SECONDS = "timeout_seconds"
    RETRY_POLICY = "retry_policy_sha256"
    COMMON_SYNTHESIZER = "common_synthesizer_sha256"
    TERMINAL_EVALUATOR = "terminal_evaluator_sha256"
    USAGE_ACCOUNTING = "usage_accounting_sha256"
    TREATMENT_CENSUS = "treatment_census"
    TREATMENT_ORDER = "treatment_order"
    CAPABILITY_CATALOG = "capability_catalog"
    CAPABILITY_CROSSOVER = "capability_crossover"
    E3_READINESS_ROSTER = "e3_readiness_roster"


def _text(value: Any, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(
            f"{field_name} must be nonempty without surrounding whitespace"
        )
    return value


def _sha256(value: Any, field_name: str) -> str:
    result = _text(value, field_name)
    if _SHA256_PATTERN.fullmatch(result) is None:
        raise ValueError(f"{field_name} must be an exact lowercase SHA-256")
    return result


def _positive_int(value: Any, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be a native integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _sequence(value: Any, field_name: str) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise TypeError(f"{field_name} must be an exact list or tuple")
    return tuple(value)


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise TypeError(f"{field_name} must be an exact dict")
    return value


def _exact_keys(
    payload: Mapping[str, Any], expected: frozenset[str], field_name: str
) -> None:
    if any(type(key) is not str for key in payload) or set(payload) != expected:
        missing = sorted(expected - set(payload))
        extra = sorted(str(key) for key in set(payload) - expected)
        raise ValueError(
            f"{field_name} must contain exact keys; missing={missing}, extra={extra}"
        )


@dataclass(frozen=True)
class TreatmentSpecV1:
    treatment_id: str
    treatment_family: str
    model_binding_sha256: str
    public_input_projection_sha256: str
    tool_catalog_sha256: str
    token_budget: int
    call_budget: int
    timeout_seconds: int
    retry_policy_sha256: str
    common_synthesizer_sha256: str
    terminal_evaluator_sha256: str
    usage_accounting_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "treatment_id", _text(self.treatment_id, "treatment_id")
        )
        object.__setattr__(
            self, "treatment_family", _text(self.treatment_family, "treatment_family")
        )
        for field_name in (
            "model_binding_sha256",
            "public_input_projection_sha256",
            "tool_catalog_sha256",
            "retry_policy_sha256",
            "common_synthesizer_sha256",
            "terminal_evaluator_sha256",
            "usage_accounting_sha256",
        ):
            object.__setattr__(
                self, field_name, _sha256(getattr(self, field_name), field_name)
            )
        for field_name in ("token_budget", "call_budget", "timeout_seconds"):
            object.__setattr__(
                self, field_name, _positive_int(getattr(self, field_name), field_name)
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TreatmentSpecV1":
        data = _mapping(payload, "treatment spec")
        _exact_keys(data, _TREATMENT_KEYS, "treatment spec")
        return cls(**dict(data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "treatment_id": self.treatment_id,
            "treatment_family": self.treatment_family,
            "model_binding_sha256": self.model_binding_sha256,
            "public_input_projection_sha256": self.public_input_projection_sha256,
            "tool_catalog_sha256": self.tool_catalog_sha256,
            "token_budget": self.token_budget,
            "call_budget": self.call_budget,
            "timeout_seconds": self.timeout_seconds,
            "retry_policy_sha256": self.retry_policy_sha256,
            "common_synthesizer_sha256": self.common_synthesizer_sha256,
            "terminal_evaluator_sha256": self.terminal_evaluator_sha256,
            "usage_accounting_sha256": self.usage_accounting_sha256,
        }


@dataclass(frozen=True)
class OacsStudyContractV1:
    treatments: tuple[TreatmentSpecV1, ...]
    capability_catalog: ControllerCapabilityCatalog
    capability_crossover_plan: CapabilityCrossoverPlan
    mandatory_baseline_roster: MandatoryBaselineRoster
    e3_readiness: tuple[BaselinePreOutcomeReadinessAuthority, ...]

    def __post_init__(self) -> None:
        treatments = _sequence(self.treatments, "treatments")
        if any(type(item) is not TreatmentSpecV1 for item in treatments):
            raise TypeError("treatments must contain exact TreatmentSpecV1 values")
        readiness = _sequence(self.e3_readiness, "e3_readiness")
        if any(
            type(item) is not BaselinePreOutcomeReadinessAuthority for item in readiness
        ):
            raise TypeError(
                "e3_readiness must contain exact BaselinePreOutcomeReadinessAuthority values"
            )
        if type(self.capability_catalog) is not ControllerCapabilityCatalog:
            raise TypeError(
                "capability_catalog must be an exact ControllerCapabilityCatalog"
            )
        if type(self.capability_crossover_plan) is not CapabilityCrossoverPlan:
            raise TypeError(
                "capability_crossover_plan must be an exact CapabilityCrossoverPlan"
            )
        if type(self.mandatory_baseline_roster) is not MandatoryBaselineRoster:
            raise TypeError(
                "mandatory_baseline_roster must be an exact MandatoryBaselineRoster"
            )
        object.__setattr__(self, "treatments", treatments)
        object.__setattr__(self, "e3_readiness", readiness)

    @property
    def required_treatment_ids(self) -> tuple[str, ...]:
        return _CORE_TREATMENT_IDS

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OacsStudyContractV1":
        data = _mapping(payload, "OACS study contract")
        _exact_keys(data, _CONTRACT_KEYS, "OACS study contract")
        catalog = ControllerCapabilityCatalog.from_dict(
            _mapping(data["capability_catalog"], "capability_catalog")
        )
        plan = CapabilityCrossoverPlan.from_dict(
            _mapping(data["capability_crossover_plan"], "capability_crossover_plan")
        )
        roster = MandatoryBaselineRoster.from_dict(data["mandatory_baseline_roster"])
        contract = cls(
            tuple(
                TreatmentSpecV1.from_dict(_mapping(item, "treatment spec"))
                for item in _sequence(data["treatments"], "treatments")
            ),
            catalog,
            plan,
            roster,
            tuple(
                BaselinePreOutcomeReadinessAuthority.from_dict(
                    _mapping(item, "baseline readiness record")
                )
                for item in _sequence(data["e3_readiness"], "e3_readiness")
            ),
        )
        validate_study_contract(contract)
        return contract

    @classmethod
    def from_bytes(cls, payload: bytes) -> "OacsStudyContractV1":
        if type(payload) is not bytes:
            raise TypeError("study contract bytes must be exact bytes")
        try:
            decoded = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("study contract bytes must be UTF-8") from error

        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        try:
            decoded_payload = json.loads(decoded, object_pairs_hook=reject_duplicates)
        except json.JSONDecodeError as error:
            raise ValueError("study contract bytes must be JSON") from error
        if type(decoded_payload) is not dict:
            raise ValueError("study contract bytes must encode an object")
        contract = cls.from_dict(decoded_payload)
        if payload != study_contract_bytes(contract):
            raise ValueError("study contract bytes are noncanonical")
        return contract

    def to_dict(self) -> dict[str, Any]:
        return {
            "treatments": [treatment.to_dict() for treatment in self.treatments],
            "capability_catalog": self.capability_catalog.to_dict(),
            "capability_crossover_plan": self.capability_crossover_plan.to_dict(),
            "mandatory_baseline_roster": self.mandatory_baseline_roster.to_dict(),
            "e3_readiness": [record.to_dict() for record in self.e3_readiness],
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def sha256(self) -> str:
        return hashlib.sha256(study_contract_bytes(self)).hexdigest()


def validate_study_contract(contract: OacsStudyContractV1) -> None:
    """Fail closed unless every core comparison surface is pre-outcome identical."""

    if type(contract) is not OacsStudyContractV1:
        raise TypeError("study contract must be an exact OacsStudyContractV1")
    observed_ids = tuple(treatment.treatment_id for treatment in contract.treatments)
    if "retrospective_oracle" in observed_ids:
        raise StudyContractError("retrospective oracle is not a deployable treatment")
    if len(observed_ids) != len(_CORE_TREATMENT_IDS) or set(observed_ids) != set(
        _CORE_TREATMENT_IDS
    ):
        raise StudyContractError(
            "treatment census must contain the exact eight core treatments"
        )
    if observed_ids != _CORE_TREATMENT_IDS:
        raise StudyContractError("treatment order must match the frozen core roster")
    for treatment in contract.treatments:
        if treatment.treatment_family != _EXPECTED_FAMILIES[treatment.treatment_id]:
            raise StudyContractError(
                "treatment family does not match the frozen core roster"
            )

    reference = contract.treatments[0]
    for field_name in _TREATMENT_FIELDS:
        if any(
            getattr(treatment, field_name) != getattr(reference, field_name)
            for treatment in contract.treatments[1:]
        ):
            raise StudyContractError(f"{field_name} parity is required")
    non_oacs = contract.treatments[:-1]
    if any(
        treatment.tool_catalog_sha256 != non_oacs[0].tool_catalog_sha256
        for treatment in non_oacs[1:]
    ):
        raise StudyContractError(
            "tool_catalog_sha256 parity is required outside randomized OACS"
        )
    try:
        validate_crossover_plan(
            contract.capability_catalog, contract.capability_crossover_plan
        )
    except (TypeError, ValueError) as error:
        raise StudyContractError("capability crossover binding is invalid") from error
    if (
        contract.treatments[-1].tool_catalog_sha256
        != contract.capability_catalog.sha256()
    ):
        raise StudyContractError(
            "capability crossover binding does not match the OACS tool catalog"
        )

    roster = contract.e3_readiness
    try:
        validate_baseline_pre_outcome_readiness(
            contract.mandatory_baseline_roster, roster
        )
    except (TypeError, ValueError) as error:
        raise StudyContractError("E3 readiness binding is invalid") from error
    if tuple(row.baseline_id.encode("utf-8") for row in roster) != tuple(
        sorted(row.baseline_id.encode("utf-8") for row in roster)
    ):
        raise StudyContractError("E3 readiness binding must be byte-sorted")


def study_contract_bytes(contract: OacsStudyContractV1) -> bytes:
    """Return the sole canonical UTF-8 contract representation, with one final LF."""

    validate_study_contract(contract)
    return (contract.canonical_json() + "\n").encode("utf-8")


__all__ = (
    "OacsStudyContractV1",
    "ParityFieldV1",
    "StudyContractError",
    "TreatmentSpecV1",
    "study_contract_bytes",
    "validate_study_contract",
)
