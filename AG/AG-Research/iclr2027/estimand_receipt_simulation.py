"""Registered synthetic DGP, site-level inference, and finite witnesses.

The Monte Carlo path retains one small sufficient-statistics record per
replicate.  It never materializes or persists a cross-scenario unit-row table.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from fractions import Fraction
import numpy as np
from numpy.random import Generator, Philox
from scipy.stats import beta, t

import iclr2027.estimand_receipt_evaluators as _evaluator_module
from iclr2027.estimand_receipt_faults import apply_fault
from iclr2027.estimand_receipt_generator import generate_clean_benchmark
from iclr2027.estimand_receipt_theory import (
    BoundRow,
    contrast_error_bound_exact,
    selection_estimand_status,
    terminal_measured_contrast_exact,
)


SCHEMA_VERSION = "estimand-receipt-simulation/v1"
FAMILY_ORDER = ("E", "B", "T", "S", "G", "P")
ESTIMAND_ORDER = ("tau_itt", "tau_cb", "psi_natural")
STREAM_NAMES = (
    "site-effect",
    "unit-error",
    "assignment",
    "fault-E",
    "fault-B",
    "fault-T",
    "fault-S",
    "fault-G",
    "fault-P",
    "selection-MCAR",
    "selection-MAR",
    "selection-MNAR",
)
_STREAM_SET = frozenset(STREAM_NAMES)
_BLOCKING_FAMILIES = {
    "tau_itt": frozenset(("B", "T", "S", "G")),
    "tau_cb": frozenset(("E", "B", "T", "S", "G")),
    "psi_natural": frozenset(("B", "T", "S", "G", "P")),
}
_X1 = tuple(Fraction(value, 7) for value in (-7, -5, -3, -1, 1, 3, 5, 7))
_X2 = tuple(Fraction(value) for value in (-1, 1, -1, 1, -1, 1, -1, 1))
_POLICY = tuple(int(left + right >= 0) for left, right in zip(_X1, _X2, strict=True))
_DOMAIN_OFFSETS = (-0.08, -0.04, 0.0, 0.04, 0.08)
_T7_CRITICAL = float(t.ppf(0.975, 7))
_PROFILE_SCHEMA = "estimand-evaluator-profile/v1"
_PROFILE_SUBSETS = tuple(
    subset
    for size in range(len(FAMILY_ORDER) + 1)
    for subset in itertools.combinations(FAMILY_ORDER, size)
)


def _require_fraction(value: object, label: str) -> Fraction:
    if type(value) is not Fraction:
        raise ValueError(label)
    return value


def _require_finite_optional(value: object, label: str) -> float | None:
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(label)
    return float(value)


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


@dataclass(frozen=True)
class ScenarioV1:
    schema_version: str
    scenario_id: str
    primary: bool
    tau: Fraction
    icc: Fraction
    families: tuple[str, ...]
    fault_rate: Fraction
    registered_replications: int

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("scenario schema")
        if (
            type(self.scenario_id) is not str
            or not self.scenario_id
            or not self.scenario_id.isascii()
        ):
            raise ValueError("scenario id")
        if type(self.primary) is not bool:
            raise ValueError("scenario primary")
        tau = _require_fraction(self.tau, "scenario tau")
        icc = _require_fraction(self.icc, "scenario icc")
        rate = _require_fraction(self.fault_rate, "scenario fault rate")
        if tau not in (Fraction(-1, 10), Fraction(0), Fraction(1, 10)):
            raise ValueError("scenario tau")
        if icc not in (Fraction(1, 20), Fraction(1, 5), Fraction(2, 5)):
            raise ValueError("scenario icc")
        if type(self.families) is not tuple or any(
            item not in FAMILY_ORDER for item in self.families
        ):
            raise ValueError("scenario families")
        if self.families != tuple(
            item for item in FAMILY_ORDER if item in self.families
        ):
            raise ValueError("scenario families")
        if len(set(self.families)) != len(self.families) or len(self.families) > 2:
            raise ValueError("scenario families")
        if (
            (not self.families and rate != 0)
            or (self.families and rate <= 0)
            or rate > 1
        ):
            raise ValueError("scenario fault rate")
        if (
            type(self.registered_replications) is not int
            or self.registered_replications != 2000
        ):
            raise ValueError("registered replications")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "scenario_id": self.scenario_id,
            "primary": self.primary,
            "tau": {
                "numerator": self.tau.numerator,
                "denominator": self.tau.denominator,
            },
            "icc": {
                "numerator": self.icc.numerator,
                "denominator": self.icc.denominator,
            },
            "families": list(self.families),
            "fault_rate": {
                "numerator": self.fault_rate.numerator,
                "denominator": self.fault_rate.denominator,
            },
            "registered_replications": self.registered_replications,
        }


def _tau_label(tau: Fraction) -> str:
    return {Fraction(-1, 10): "m010", Fraction(0): "z000", Fraction(1, 10): "p010"}[tau]


def _rate_label(rate: Fraction) -> str:
    return f"p{int(rate * 100):03d}"


def _scenario(
    *,
    scenario_id: str,
    primary: bool,
    tau: Fraction,
    icc: Fraction,
    families: tuple[str, ...],
    fault_rate: Fraction,
) -> ScenarioV1:
    return ScenarioV1(
        schema_version=SCHEMA_VERSION,
        scenario_id=scenario_id,
        primary=primary,
        tau=tau,
        icc=icc,
        families=families,
        fault_rate=fault_rate,
        registered_replications=2000,
    )


def _build_scenarios() -> tuple[ScenarioV1, ...]:
    taus = (Fraction(-1, 10), Fraction(0), Fraction(1, 10))
    rates = (Fraction(1, 100), Fraction(1, 20), Fraction(1, 10), Fraction(1, 5))
    regimes = tuple((item,) for item in FAMILY_ORDER) + tuple(
        itertools.combinations(FAMILY_ORDER, 2)
    )
    rows: list[ScenarioV1] = []
    for tau in taus:
        tau_label = _tau_label(tau)
        rows.append(
            _scenario(
                scenario_id=f"primary-tau-{tau_label}-clean",
                primary=True,
                tau=tau,
                icc=Fraction(1, 5),
                families=(),
                fault_rate=Fraction(0),
            )
        )
        for families in regimes:
            family_label = "+".join(families)
            for rate in rates:
                rows.append(
                    _scenario(
                        scenario_id=f"primary-tau-{tau_label}-{family_label}-{_rate_label(rate)}",
                        primary=True,
                        tau=tau,
                        icc=Fraction(1, 5),
                        families=families,
                        fault_rate=rate,
                    )
                )
    for icc in (Fraction(1, 20), Fraction(2, 5)):
        icc_label = f"{int(icc * 100):03d}"
        for tau in taus:
            tau_label = _tau_label(tau)
            rows.append(
                _scenario(
                    scenario_id=f"sensitivity-icc-{icc_label}-tau-{tau_label}-clean",
                    primary=False,
                    tau=tau,
                    icc=icc,
                    families=(),
                    fault_rate=Fraction(0),
                )
            )
            for family in FAMILY_ORDER:
                rows.append(
                    _scenario(
                        scenario_id=f"sensitivity-icc-{icc_label}-tau-{tau_label}-{family}-p010",
                        primary=False,
                        tau=tau,
                        icc=icc,
                        families=(family,),
                        fault_rate=Fraction(1, 10),
                    )
                )
    output = tuple(rows)
    if len(output) != 297 or sum(item.primary for item in output) != 255:
        raise AssertionError("registered scenario census")
    return output


_REGISTERED_SCENARIOS = _build_scenarios()
_SCENARIO_BY_ID = {item.scenario_id: item for item in _REGISTERED_SCENARIOS}


def registered_scenarios() -> tuple[ScenarioV1, ...]:
    """Return the frozen 255-primary plus 42-sensitivity scenario census."""

    return _REGISTERED_SCENARIOS


def _require_registered_scenario(value: object) -> ScenarioV1:
    if type(value) is not ScenarioV1:
        raise TypeError("scenario")
    registered = _SCENARIO_BY_ID.get(value.scenario_id)
    if (
        registered is None
        or value != registered
        or value.registered_replications != 2000
    ):
        raise ValueError("unregistered scenario")
    return value


@dataclass(frozen=True)
class EvaluatorProfileCellV1:
    families: tuple[str, ...]
    configuration: str
    estimand: str
    status: str

    def __post_init__(self) -> None:
        if self.families not in _PROFILE_SUBSETS:
            raise ValueError("profile families")
        if self.configuration not in _evaluator_module.CONFIGURATIONS:
            raise ValueError("profile configuration")
        if self.estimand not in ESTIMAND_ORDER:
            raise ValueError("profile estimand")
        if self.status not in ("CERTIFIED", "BOUNDED", "NOT_CERTIFIED"):
            raise ValueError("profile status")

    def to_dict(self) -> dict[str, object]:
        return {
            "families": list(self.families),
            "configuration": self.configuration,
            "estimand": self.estimand,
            "status": self.status,
        }


def _profile_payload(
    entries: tuple[EvaluatorProfileCellV1, ...],
) -> dict[str, object]:
    return {
        "schema_version": _PROFILE_SCHEMA,
        "family_order": list(FAMILY_ORDER),
        "configurations": list(_evaluator_module.CONFIGURATIONS),
        "estimands": list(ESTIMAND_ORDER),
        "entries": [entry.to_dict() for entry in entries],
    }


@dataclass(frozen=True)
class EvaluatorProfileV1:
    schema_version: str
    entries: tuple[EvaluatorProfileCellV1, ...]
    canonical_bytes: bytes
    sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != _PROFILE_SCHEMA:
            raise ValueError("profile schema")
        expected_identities = tuple(
            (families, configuration, estimand)
            for families in _PROFILE_SUBSETS
            for configuration in _evaluator_module.CONFIGURATIONS
            for estimand in ESTIMAND_ORDER
        )
        if (
            type(self.entries) is not tuple
            or tuple(
                (entry.families, entry.configuration, entry.estimand)
                for entry in self.entries
            )
            != expected_identities
        ):
            raise ValueError("profile entries")
        if any(type(entry) is not EvaluatorProfileCellV1 for entry in self.entries):
            raise ValueError("profile entries")
        expected_bytes = _canonical_bytes(_profile_payload(self.entries))
        if (
            type(self.canonical_bytes) is not bytes
            or self.canonical_bytes != expected_bytes
        ):
            raise ValueError("profile bytes")
        expected_hash = hashlib.sha256(expected_bytes).hexdigest()
        if self.sha256 != expected_hash:
            raise ValueError("profile digest")

    @classmethod
    def create(cls, entries: tuple[EvaluatorProfileCellV1, ...]) -> EvaluatorProfileV1:
        payload = _profile_payload(entries)
        canonical = _canonical_bytes(payload)
        return cls(
            schema_version=_PROFILE_SCHEMA,
            entries=entries,
            canonical_bytes=canonical,
            sha256=hashlib.sha256(canonical).hexdigest(),
        )

    def lookup(
        self, families: tuple[str, ...], configuration: str, estimand: str
    ) -> EvaluatorProfileCellV1:
        if families not in _PROFILE_SUBSETS:
            raise KeyError(families)
        if configuration not in _evaluator_module.CONFIGURATIONS:
            raise KeyError(configuration)
        if estimand not in ESTIMAND_ORDER:
            raise KeyError(estimand)
        subset_index = _PROFILE_SUBSETS.index(families)
        configuration_index = _evaluator_module.CONFIGURATIONS.index(configuration)
        estimand_index = ESTIMAND_ORDER.index(estimand)
        index = (
            subset_index * len(_evaluator_module.CONFIGURATIONS) * len(ESTIMAND_ORDER)
            + configuration_index * len(ESTIMAND_ORDER)
            + estimand_index
        )
        return self.entries[index]


_REPRESENTATIVE_FAULTS = {
    "E": "execution_omit_geometry",
    "B": "target_rebind_same_site_same_assignment",
    "T": "terminal_stale_owner",
    "S": "scorer_drop_geometry",
    "G": "protocol_stale_incompatible",
    "P": "policy_menu_drift",
}


def build_evaluator_profile() -> EvaluatorProfileV1:
    """Freeze Task-6 decisions for all 64 family subsets without oracle access."""

    clean = generate_clean_benchmark()
    source = clean.artifacts[0]
    artifacts = {artifact.unit_id: artifact for artifact in clean.artifacts}
    partner_by_family = {
        "E": source,
        "B": artifacts["syn-target-00-04"],
        "T": source,
        "S": source,
        "G": source,
        "P": source,
    }
    root_bytes = _canonical_bytes(clean.trust_root.to_dict())
    entries: list[EvaluatorProfileCellV1] = []
    for families in _PROFILE_SUBSETS:
        artifact = source
        for family in families:
            artifact = apply_fault(
                artifact,
                _REPRESENTATIVE_FAULTS[family],
                partner=partner_by_family[family],
            )
        case_id = _sha256_json(
            {
                "schema_version": "evaluator-profile-case/v1",
                "families": list(families),
            }
        )
        public_bytes = _canonical_bytes(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": case_id,
                "artifact": artifact.to_dict(),
            }
        )
        for configuration in _evaluator_module.CONFIGURATIONS:
            decisions = _evaluator_module.evaluate_configuration(
                configuration,
                (public_bytes,),
                root_bytes,
            )
            if tuple(decision.estimand for decision in decisions) != ESTIMAND_ORDER:
                raise ValueError("Task-6 evaluator decision order")
            entries.extend(
                EvaluatorProfileCellV1(
                    families=families,
                    configuration=configuration,
                    estimand=decision.estimand,
                    status=decision.status,
                )
                for decision in decisions
            )
    return EvaluatorProfileV1.create(tuple(entries))


def fixed_covariates() -> tuple[
    tuple[Fraction, ...], tuple[Fraction, ...], tuple[int, ...]
]:
    """Return exact target-order covariates and the frozen policy decision."""

    return _X1, _X2, _POLICY


def philox_seed(
    scenario: ScenarioV1, replicate: int, site_index: int, stream_name: str
) -> int:
    """Derive the registered big-endian 128-bit Philox seed."""

    checked = _require_registered_scenario(scenario)
    if (
        type(replicate) is not int
        or replicate < 0
        or replicate >= checked.registered_replications
    ):
        raise ValueError("replicate")
    if type(site_index) is not int or site_index < 0 or site_index >= 8:
        raise ValueError("site index")
    if type(stream_name) is not str or stream_name not in _STREAM_SET:
        raise ValueError("stream name")
    payload = json.dumps(
        [SCHEMA_VERSION, checked.scenario_id, replicate, site_index, stream_name],
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def _rng(
    scenario: ScenarioV1, replicate: int, site_index: int, stream_name: str
) -> Generator:
    return Generator(Philox(philox_seed(scenario, replicate, site_index, stream_name)))


@dataclass(frozen=True)
class PotentialOutcomesV1:
    scenario_id: str
    replicate: int
    y0_complete: tuple[float, ...]
    y1_complete: tuple[float, ...]
    domain_scores_y0: tuple[tuple[float, ...], ...]
    domain_scores_y1: tuple[tuple[float, ...], ...]
    policy_decisions: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.scenario_id not in _SCENARIO_BY_ID:
            raise ValueError("population scenario")
        if type(self.replicate) is not int or not 0 <= self.replicate < 2000:
            raise ValueError("population replicate")
        if len(self.y0_complete) != 64 or len(self.y1_complete) != 64:
            raise ValueError("population outcomes")
        if any(
            not math.isfinite(item) or not 0 <= item <= 1
            for item in self.y0_complete + self.y1_complete
        ):
            raise ValueError("population outcomes")
        if len(self.domain_scores_y0) != 64 or len(self.domain_scores_y1) != 64:
            raise ValueError("domain scores")
        for rows in (self.domain_scores_y0, self.domain_scores_y1):
            if any(
                len(row) != 5
                or any(not math.isfinite(item) or not 0 <= item <= 1 for item in row)
                for row in rows
            ):
                raise ValueError("domain scores")
        if self.policy_decisions != _POLICY * 8:
            raise ValueError("population policy")

    @property
    def complete_bundle_effect(self) -> float:
        return (
            math.fsum(
                treated - control
                for control, treated in zip(
                    self.y0_complete, self.y1_complete, strict=True
                )
            )
            / 64.0
        )

    @property
    def policy_value(self) -> float:
        return (
            math.fsum(
                self.y1_complete[index]
                if self.policy_decisions[index]
                else self.y0_complete[index]
                for index in range(64)
            )
            / 64.0
        )


def _domain_scores(values: np.ndarray) -> tuple[tuple[float, ...], ...]:
    matrix = values[:, None] + np.asarray(_DOMAIN_OFFSETS, dtype=np.float64)[None, :]
    if np.any((matrix < 0.0) | (matrix > 1.0)):
        raise AssertionError("domain score construction")
    return tuple(tuple(float(item) for item in row) for row in matrix)


def generate_potential_outcomes(
    scenario: ScenarioV1, replicate: int
) -> PotentialOutcomesV1:
    """Generate one 8-by-8 finite population in canonical site-major order."""

    checked = _require_registered_scenario(scenario)
    if (
        type(replicate) is not int
        or replicate < 0
        or replicate >= checked.registered_replications
    ):
        raise ValueError("replicate")
    x1 = np.asarray([float(item) for item in _X1], dtype=np.float64)
    x2 = np.asarray([float(item) for item in _X2], dtype=np.float64)
    y0_rows: list[np.ndarray] = []
    y1_rows: list[np.ndarray] = []
    for site in range(8):
        site_effect = float(
            _rng(checked, replicate, site, "site-effect").standard_normal()
        )
        unit_errors = _rng(checked, replicate, site, "unit-error").standard_normal(
            8, dtype=np.float64
        )
        eta = (
            math.sqrt(float(checked.icc)) * site_effect
            + math.sqrt(1.0 - float(checked.icc)) * unit_errors
            + 0.25 * x1
            - 0.15 * x2
        )
        baseline = 0.5 + 0.18 * np.tanh(eta)
        delta = float(checked.tau) + 0.04 * x1
        y0_rows.append(np.asarray(baseline - delta / 2.0, dtype=np.float64))
        y1_rows.append(np.asarray(baseline + delta / 2.0, dtype=np.float64))
    y0 = np.concatenate(y0_rows).astype(np.float64, copy=False)
    y1 = np.concatenate(y1_rows).astype(np.float64, copy=False)
    if np.any((y0 < 0.0) | (y0 > 1.0) | (y1 < 0.0) | (y1 > 1.0)):
        raise AssertionError("potential outcome construction")
    return PotentialOutcomesV1(
        scenario_id=checked.scenario_id,
        replicate=replicate,
        y0_complete=tuple(float(item) for item in y0),
        y1_complete=tuple(float(item) for item in y1),
        domain_scores_y0=_domain_scores(y0),
        domain_scores_y1=_domain_scores(y1),
        policy_decisions=_POLICY * 8,
    )


def _matrix(value: object, label: str, *, binary: bool = False) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or array.shape[1] != 8:
        raise ValueError(label)
    if binary:
        if not np.all((array == 0) | (array == 1)):
            raise ValueError(label)
        return np.asarray(array, dtype=np.int8)
    array = np.asarray(array, dtype=np.float64)
    if not np.all(np.isfinite(array)) or not np.all((array >= 0.0) & (array <= 1.0)):
        raise ValueError(label)
    return array


def apply_fault_transforms(
    endpoint: object,
    y0_complete: object,
    assignment: object,
    policy_decisions: object,
    fault_masks: dict[str, object],
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the six registered transforms in frozen ``E,B,T,S,G,P`` order."""

    measured = _matrix(endpoint, "endpoint").copy()
    y0 = _matrix(y0_complete, "y0 complete")
    arms = _matrix(assignment, "assignment", binary=True)
    decisions = _matrix(policy_decisions, "policy decisions", binary=True).copy()
    if (
        measured.shape != y0.shape
        or measured.shape != arms.shape
        or measured.shape != decisions.shape
    ):
        raise ValueError("transform shape")
    if type(fault_masks) is not dict or tuple(fault_masks) != FAMILY_ORDER:
        raise ValueError("fault masks")
    masks: dict[str, np.ndarray] = {}
    for family in FAMILY_ORDER:
        mask = np.asarray(fault_masks[family])
        if mask.shape != measured.shape or mask.dtype.kind != "b":
            raise ValueError("fault mask")
        masks[family] = mask

    treated_omission = masks["E"] & (arms == 1)
    measured[treated_omission] = y0[treated_omission] + 0.8 * (
        measured[treated_omission] - y0[treated_omission]
    )
    before_binding = measured.copy()
    next_target = np.roll(before_binding, -1, axis=1)
    measured[masks["B"]] = next_target[masks["B"]]
    measured[masks["T"]] = 1.0 - measured[masks["T"]]
    measured[masks["S"]] += 0.02 * (2.0 * arms[masks["S"]] - 1.0)
    measured[masks["G"]] = (measured[masks["G"]] >= 0.5).astype(np.float64)
    decisions[masks["P"]] = 1 - decisions[masks["P"]]
    if not np.all(np.isfinite(measured)) or not np.all(
        (measured >= 0.0) & (measured <= 1.0)
    ):
        raise ValueError("transformed endpoint")
    return np.asarray(measured, dtype=np.float64), np.asarray(decisions, dtype=np.int8)


@dataclass(frozen=True)
class SiteInferenceV1:
    estimate: float
    standard_error: float
    lower: float
    upper: float


def t7_interval(site_estimates: object) -> SiteInferenceV1:
    """Return the registered mean and t(7) interval from eight site estimates."""

    values = np.asarray(site_estimates, dtype=np.float64)
    if values.shape != (8,) or not np.all(np.isfinite(values)):
        raise ValueError("site estimates")
    estimate = math.fsum(float(item) for item in values) / 8.0
    variance = math.fsum((float(item) - estimate) ** 2 for item in values) / 7.0
    standard_error = math.sqrt(variance / 8.0)
    return SiteInferenceV1(
        estimate=estimate,
        standard_error=standard_error,
        lower=estimate - _T7_CRITICAL * standard_error,
        upper=estimate + _T7_CRITICAL * standard_error,
    )


def policy_ipw_site(
    assignment: object,
    endpoint: object,
    policy_decisions: object,
    propensity: float = 0.5,
) -> float:
    """Return the eight-unit policy-value IPW estimate at known propensity 1/2."""

    arms = np.asarray(assignment)
    outcomes = np.asarray(endpoint, dtype=np.float64)
    decisions = np.asarray(policy_decisions)
    if arms.shape != (8,) or outcomes.shape != (8,) or decisions.shape != (8,):
        raise ValueError("policy IPW shape")
    if not np.all((arms == 0) | (arms == 1)) or np.count_nonzero(arms == 1) != 4:
        raise ValueError("policy IPW assignment")
    if not np.all((decisions == 0) | (decisions == 1)):
        raise ValueError("policy IPW decision")
    if not np.all(np.isfinite(outcomes)) or not np.all(
        (outcomes >= 0.0) & (outcomes <= 1.0)
    ):
        raise ValueError("policy IPW endpoint")
    if type(propensity) not in (int, float) or float(propensity) != 0.5:
        raise ValueError("policy IPW propensity")
    return (
        math.fsum(
            float(outcomes[index]) / 0.5
            for index in range(8)
            if int(arms[index]) == int(decisions[index])
        )
        / 8.0
    )


@dataclass(frozen=True)
class EstimateSufficientStatisticsV1:
    configuration: str
    estimand: str
    truth: float | None
    realized_truth: float | None
    estimate: float | None
    standard_error: float | None
    lower: float | None
    upper: float | None
    oracle_certified: bool
    reported_status: str
    reported: bool

    def __post_init__(self) -> None:
        if self.configuration not in _evaluator_module.CONFIGURATIONS:
            raise ValueError("configuration")
        if self.estimand not in ESTIMAND_ORDER:
            raise ValueError("estimand")
        truth = _require_finite_optional(self.truth, "truth")
        realized_truth = _require_finite_optional(self.realized_truth, "realized truth")
        estimate = _require_finite_optional(self.estimate, "estimate")
        standard_error = _require_finite_optional(self.standard_error, "standard error")
        lower = _require_finite_optional(self.lower, "lower")
        upper = _require_finite_optional(self.upper, "upper")
        for name, value in (
            ("truth", truth),
            ("realized_truth", realized_truth),
            ("estimate", estimate),
            ("standard_error", standard_error),
            ("lower", lower),
            ("upper", upper),
        ):
            object.__setattr__(self, name, value)
        if type(self.oracle_certified) is not bool or type(self.reported) is not bool:
            raise ValueError("certification flags")
        if self.reported_status not in (
            "CERTIFIED",
            "BOUNDED",
            "NOT_CERTIFIED",
        ) or self.reported != (self.reported_status == "CERTIFIED"):
            raise ValueError("reported status")
        inference = (estimate, standard_error, lower, upper)
        if estimate is None:
            if any(item is not None for item in inference[1:]) or self.reported:
                raise ValueError("inference closure")
        elif any(item is None for item in inference[1:]):
            raise ValueError("inference closure")
        if standard_error is not None and standard_error < 0:
            raise ValueError("standard error")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("interval")
        if self.oracle_certified and truth is None:
            raise ValueError("certified truth")


@dataclass(frozen=True)
class ReplicateSufficientStatisticsV1:
    replicate: int
    estimates: tuple[EstimateSufficientStatisticsV1, ...]
    site_assignment_counts: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        if type(self.replicate) is not int or not 0 <= self.replicate < 2000:
            raise ValueError("replicate")
        expected = tuple(
            (configuration, estimand)
            for configuration in _evaluator_module.CONFIGURATIONS
            for estimand in ESTIMAND_ORDER
        )
        if (
            type(self.estimates) is not tuple
            or tuple((item.configuration, item.estimand) for item in self.estimates)
            != expected
        ):
            raise ValueError("replicate estimates")
        if self.site_assignment_counts != ((4, 4),) * 8:
            raise ValueError("site assignment counts")

    def cell(
        self,
        estimand: str,
        configuration: str = "full_estimand_gate",
    ) -> EstimateSufficientStatisticsV1:
        if estimand not in ESTIMAND_ORDER:
            raise KeyError(estimand)
        if configuration not in _evaluator_module.CONFIGURATIONS:
            raise KeyError(configuration)
        index = _evaluator_module.CONFIGURATIONS.index(configuration) * len(
            ESTIMAND_ORDER
        ) + ESTIMAND_ORDER.index(estimand)
        return self.estimates[index]


@dataclass(frozen=True)
class BatchSufficientStatisticsV1:
    scenario_id: str
    evaluator_profile_sha256: str
    registered_replications: int
    start: int
    count: int
    replicates: tuple[ReplicateSufficientStatisticsV1, ...]

    def __post_init__(self) -> None:
        scenario = _SCENARIO_BY_ID.get(self.scenario_id)
        if scenario is None:
            raise ValueError("batch scenario")
        if (
            type(self.evaluator_profile_sha256) is not str
            or len(self.evaluator_profile_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.evaluator_profile_sha256
            )
        ):
            raise ValueError("batch evaluator profile")
        if (
            type(self.registered_replications) is not int
            or self.registered_replications != 2000
        ):
            raise ValueError("batch registered replications")
        if (
            type(self.start) is not int
            or type(self.count) is not int
            or self.start < 0
            or self.count <= 0
        ):
            raise ValueError("batch range")
        if self.start + self.count > self.registered_replications:
            raise ValueError("batch range")
        if type(self.replicates) is not tuple or len(self.replicates) != self.count:
            raise ValueError("batch replicates")
        if tuple(item.replicate for item in self.replicates) != tuple(
            range(self.start, self.start + self.count)
        ):
            raise ValueError("batch replicate order")

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "evaluator_profile_sha256": self.evaluator_profile_sha256,
            "registered_replications": self.registered_replications,
            "start": self.start,
            "count": self.count,
            "replicates": [
                {
                    "replicate": replicate.replicate,
                    "estimates": [
                        {
                            "configuration": cell.configuration,
                            "estimand": cell.estimand,
                            "truth": cell.truth,
                            "realized_truth": cell.realized_truth,
                            "estimate": cell.estimate,
                            "standard_error": cell.standard_error,
                            "lower": cell.lower,
                            "upper": cell.upper,
                            "oracle_certified": cell.oracle_certified,
                            "reported_status": cell.reported_status,
                            "reported": cell.reported,
                        }
                        for cell in replicate.estimates
                    ],
                    "site_assignment_counts": [
                        list(item) for item in replicate.site_assignment_counts
                    ],
                }
                for replicate in self.replicates
            ],
        }


def _assignment_matrix(scenario: ScenarioV1, replicate: int) -> np.ndarray:
    rows = []
    template = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int8)
    for site in range(8):
        rows.append(_rng(scenario, replicate, site, "assignment").permutation(template))
    return np.asarray(rows, dtype=np.int8)


def _fault_mask_matrices(scenario: ScenarioV1, replicate: int) -> dict[str, np.ndarray]:
    masks: dict[str, np.ndarray] = {}
    for family in FAMILY_ORDER:
        rows = []
        for site in range(8):
            if family in scenario.families:
                rows.append(
                    _rng(scenario, replicate, site, f"fault-{family}").random(8)
                    < float(scenario.fault_rate)
                )
            else:
                rows.append(np.zeros(8, dtype=bool))
        masks[family] = np.asarray(rows, dtype=bool)
    return masks


def _marginal_truths(scenario: ScenarioV1) -> dict[str, float]:
    execution_rate = scenario.fault_rate if "E" in scenario.families else Fraction(0)
    policy_increment = (
        sum(
            (
                Fraction(1, 2) - execution_rate / 5
                if _POLICY[target]
                else Fraction(-1, 2)
            )
            * (scenario.tau + _X1[target] / 25)
            for target in range(8)
        )
        / 8
    )
    return {
        "tau_itt": float((1 - execution_rate / 5) * scenario.tau),
        "tau_cb": float(scenario.tau),
        "psi_natural": float(Fraction(1, 2) + policy_increment),
    }


def _simulate_replicate(
    scenario: ScenarioV1,
    replicate: int,
    evaluator_profile: EvaluatorProfileV1,
) -> ReplicateSufficientStatisticsV1:
    population = generate_potential_outcomes(scenario, replicate)
    y0 = np.asarray(population.y0_complete, dtype=np.float64).reshape(8, 8)
    y1 = np.asarray(population.y1_complete, dtype=np.float64).reshape(8, 8)
    assignment = _assignment_matrix(scenario, replicate)
    masks = _fault_mask_matrices(scenario, replicate)
    endpoint = np.where(assignment == 1, y1, y0).astype(np.float64, copy=False)
    policy = np.tile(np.asarray(_POLICY, dtype=np.int8), (8, 1))
    measured, measured_policy = apply_fault_transforms(
        endpoint, y0, assignment, policy, masks
    )

    actual_y1 = y0 + np.where(masks["E"], 0.8, 1.0) * (y1 - y0)
    realized_truths = {
        "tau_itt": math.fsum(float(item) for item in (actual_y1 - y0).ravel()) / 64.0,
        "tau_cb": math.fsum(float(item) for item in (y1 - y0).ravel()) / 64.0,
        "psi_natural": math.fsum(
            float(actual_y1[site, target] if _POLICY[target] else y0[site, target])
            for site in range(8)
            for target in range(8)
        )
        / 64.0,
    }
    truths = _marginal_truths(scenario)
    contrasts = []
    policy_values = []
    for site in range(8):
        treated = measured[site][assignment[site] == 1]
        control = measured[site][assignment[site] == 0]
        contrasts.append(
            math.fsum(float(item) for item in treated) / 4.0
            - math.fsum(float(item) for item in control) / 4.0
        )
        policy_values.append(
            policy_ipw_site(assignment[site], measured[site], measured_policy[site])
        )
    intervals = {
        "tau_itt": t7_interval(contrasts),
        "tau_cb": t7_interval(contrasts),
        "psi_natural": t7_interval(policy_values),
    }
    any_fault = {family: bool(np.any(masks[family])) for family in FAMILY_ORDER}
    realized_families = tuple(family for family in FAMILY_ORDER if any_fault[family])
    estimates = tuple(
        EstimateSufficientStatisticsV1(
            configuration=configuration,
            estimand=estimand,
            truth=truths[estimand],
            realized_truth=realized_truths[estimand],
            estimate=intervals[estimand].estimate,
            standard_error=intervals[estimand].standard_error,
            lower=intervals[estimand].lower,
            upper=intervals[estimand].upper,
            oracle_certified=not any(
                any_fault[family] for family in _BLOCKING_FAMILIES[estimand]
            ),
            reported_status=evaluator_profile.lookup(
                realized_families,
                configuration,
                estimand,
            ).status,
            reported=(
                evaluator_profile.lookup(
                    realized_families,
                    configuration,
                    estimand,
                ).status
                == "CERTIFIED"
            ),
        )
        for configuration in _evaluator_module.CONFIGURATIONS
        for estimand in ESTIMAND_ORDER
    )
    return ReplicateSufficientStatisticsV1(
        replicate=replicate,
        estimates=estimates,
        site_assignment_counts=tuple(
            (int(np.count_nonzero(row == 0)), int(np.count_nonzero(row == 1)))
            for row in assignment
        ),
    )


def simulate_batch(
    scenario: ScenarioV1,
    start: int,
    count: int,
    *,
    evaluator_profile: EvaluatorProfileV1,
) -> BatchSufficientStatisticsV1:
    """Simulate one registered partition without changing the 2,000-rep census."""

    checked = _require_registered_scenario(scenario)
    if type(evaluator_profile) is not EvaluatorProfileV1:
        raise TypeError("evaluator profile")
    evaluator_profile = EvaluatorProfileV1(
        schema_version=evaluator_profile.schema_version,
        entries=evaluator_profile.entries,
        canonical_bytes=evaluator_profile.canonical_bytes,
        sha256=evaluator_profile.sha256,
    )
    if type(start) is not int or type(count) is not int or start < 0 or count <= 0:
        raise ValueError("batch range")
    if start + count > checked.registered_replications:
        raise ValueError("batch range")
    replicates = tuple(
        _simulate_replicate(checked, replicate, evaluator_profile)
        for replicate in range(start, start + count)
    )
    return BatchSufficientStatisticsV1(
        scenario_id=checked.scenario_id,
        evaluator_profile_sha256=evaluator_profile.sha256,
        registered_replications=checked.registered_replications,
        start=start,
        count=count,
        replicates=replicates,
    )


@dataclass(frozen=True)
class ExactFractionV1:
    numerator: int | None
    denominator: int | None
    lower: float | None
    upper: float | None
    interval_method: str | None

    def __post_init__(self) -> None:
        if self.numerator is None or self.denominator is None:
            if any(
                item is not None
                for item in (
                    self.numerator,
                    self.denominator,
                    self.lower,
                    self.upper,
                    self.interval_method,
                )
            ):
                raise ValueError("exact fraction")
            return
        if type(self.numerator) is not int or type(self.denominator) is not int:
            raise ValueError("exact fraction")
        if (
            self.numerator < 0
            or self.denominator <= 0
            or self.numerator > self.denominator
        ):
            raise ValueError("exact fraction")
        if self.interval_method != "clopper-pearson-95":
            raise ValueError("interval method")
        expected_lower = (
            0.0
            if self.numerator == 0
            else float(
                beta.ppf(
                    0.025,
                    self.numerator,
                    self.denominator - self.numerator + 1,
                )
            )
        )
        expected_upper = (
            1.0
            if self.numerator == self.denominator
            else float(
                beta.ppf(
                    0.975,
                    self.numerator + 1,
                    self.denominator - self.numerator,
                )
            )
        )
        if self.lower != expected_lower or self.upper != expected_upper:
            raise ValueError("Clopper-Pearson interval")

    def to_dict(self) -> dict[str, object]:
        return {
            "numerator": self.numerator,
            "denominator": self.denominator,
            "lower": self.lower,
            "upper": self.upper,
            "interval_method": self.interval_method,
        }


def exact_probability(numerator: int, denominator: int) -> ExactFractionV1:
    """Return an exact event count plus its registered 95% CP interval."""

    if type(numerator) is not int or type(denominator) is not int:
        raise ValueError("exact probability")
    if denominator == 0:
        if numerator != 0:
            raise ValueError("exact probability")
        return ExactFractionV1(None, None, None, None, None)
    if denominator < 0 or numerator < 0 or numerator > denominator:
        raise ValueError("exact probability")
    lower = (
        0.0
        if numerator == 0
        else float(beta.ppf(0.025, numerator, denominator - numerator + 1))
    )
    upper = (
        1.0
        if numerator == denominator
        else float(beta.ppf(0.975, numerator + 1, denominator - numerator))
    )
    return ExactFractionV1(
        numerator,
        denominator,
        lower,
        upper,
        "clopper-pearson-95",
    )


def _fraction(numerator: int, denominator: int) -> ExactFractionV1:
    return exact_probability(numerator, denominator)


_PROBABILITY_METRIC_ORDER = (
    "false_reportability_rate",
    "eligible_retention_rate",
    "abstention_rate",
    "conditional_report_accuracy",
    "joint_decision_accuracy",
    "coverage",
    "joint_coverage",
    "type_i_error",
    "power",
    "false_sign_probability",
    "joint_rejection_probability",
    "joint_correct_sign_probability",
)


@dataclass(frozen=True)
class ProbabilityContextV1:
    metric: str
    applicability: str
    status: str
    reason: str | None
    eligible_n: int
    reported_n: int

    def __post_init__(self) -> None:
        if self.metric not in _PROBABILITY_METRIC_ORDER:
            raise ValueError("probability metric")
        if self.applicability not in ("APPLICABLE", "INAPPLICABLE"):
            raise ValueError("probability applicability")
        if self.status not in (
            "ESTIMATED",
            "ZERO_DENOMINATOR",
            "INAPPLICABLE",
        ):
            raise ValueError("probability status")
        if (
            type(self.eligible_n) is not int
            or type(self.reported_n) is not int
            or self.eligible_n < 0
            or self.reported_n < 0
            or self.reported_n > self.eligible_n
        ):
            raise ValueError("probability counts")
        if self.applicability == "INAPPLICABLE":
            if self.status != "INAPPLICABLE" or not self.reason:
                raise ValueError("inapplicable probability")
        elif self.status == "INAPPLICABLE":
            raise ValueError("applicable probability")
        elif self.status == "ESTIMATED":
            if self.reason is not None:
                raise ValueError("estimated probability")
        elif not self.reason:
            raise ValueError("zero-denominator probability")

    def for_metric(self, metric: str) -> ProbabilityContextV1:
        return ProbabilityContextV1(
            metric=metric,
            applicability=self.applicability,
            status=self.status,
            reason=self.reason,
            eligible_n=self.eligible_n,
            reported_n=self.reported_n,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "applicability": self.applicability,
            "status": self.status,
            "reason": self.reason,
            "eligible_n": self.eligible_n,
            "reported_n": self.reported_n,
        }


def _applicable_probability_context(
    metric: str,
    probability: ExactFractionV1,
    *,
    eligible_n: int,
    reported_n: int,
    zero_reason: str,
) -> ProbabilityContextV1:
    if probability.denominator is None:
        status = "ZERO_DENOMINATOR"
        reason: str | None = zero_reason
    else:
        status = "ESTIMATED"
        reason = None
    return ProbabilityContextV1(
        metric=metric,
        applicability="APPLICABLE",
        status=status,
        reason=reason,
        eligible_n=eligible_n,
        reported_n=reported_n,
    )


def _inapplicable_probability_context(
    metric: str,
    *,
    reason: str,
    eligible_n: int,
    reported_n: int,
) -> ProbabilityContextV1:
    return ProbabilityContextV1(
        metric=metric,
        applicability="INAPPLICABLE",
        status="INAPPLICABLE",
        reason=reason,
        eligible_n=eligible_n,
        reported_n=reported_n,
    )


@dataclass(frozen=True)
class MetricRowV1:
    scenario_id: str
    configuration: str
    estimand: str
    total: int
    oracle_certified: int
    oracle_not_certified: int
    reported: int
    false_reported: int
    eligible_retained: int
    abstained: int
    exact_decisions: int
    false_reportability_rate: ExactFractionV1
    eligible_retention_rate: ExactFractionV1
    abstention_rate: ExactFractionV1
    conditional_report_accuracy: ExactFractionV1
    joint_decision_accuracy: ExactFractionV1
    bias: float | None
    rmse: float | None
    coverage: ExactFractionV1 | None
    joint_coverage: ExactFractionV1 | None
    type_i_error: ExactFractionV1 | None
    power: ExactFractionV1 | None
    false_sign_probability: ExactFractionV1 | None
    joint_rejection_probability: ExactFractionV1 | None
    joint_correct_sign_probability: ExactFractionV1 | None
    probability_contexts: tuple[ProbabilityContextV1, ...]

    def __post_init__(self) -> None:
        if tuple(item.metric for item in self.probability_contexts) != (
            _PROBABILITY_METRIC_ORDER
        ):
            raise ValueError("probability contexts")
        for context in self.probability_contexts:
            probability = getattr(self, context.metric)
            if context.applicability == "INAPPLICABLE":
                if probability is not None:
                    raise ValueError("inapplicable probability")
            elif type(probability) is not ExactFractionV1:
                raise ValueError("applicable probability")
            elif (probability.denominator is None) != (
                context.status == "ZERO_DENOMINATOR"
            ):
                raise ValueError("probability denominator status")

    def probability_context(self, metric: str) -> ProbabilityContextV1:
        if metric not in _PROBABILITY_METRIC_ORDER:
            raise ValueError("probability metric")
        return self.probability_contexts[_PROBABILITY_METRIC_ORDER.index(metric)]

    def to_dict(self) -> dict[str, object]:
        def rate(value: ExactFractionV1 | None) -> dict[str, object] | None:
            return None if value is None else value.to_dict()

        return {
            "scenario_id": self.scenario_id,
            "configuration": self.configuration,
            "estimand": self.estimand,
            "total": self.total,
            "oracle_certified": self.oracle_certified,
            "oracle_not_certified": self.oracle_not_certified,
            "reported": self.reported,
            "false_reported": self.false_reported,
            "eligible_retained": self.eligible_retained,
            "abstained": self.abstained,
            "exact_decisions": self.exact_decisions,
            "false_reportability_rate": self.false_reportability_rate.to_dict(),
            "eligible_retention_rate": self.eligible_retention_rate.to_dict(),
            "abstention_rate": self.abstention_rate.to_dict(),
            "conditional_report_accuracy": self.conditional_report_accuracy.to_dict(),
            "joint_decision_accuracy": self.joint_decision_accuracy.to_dict(),
            "bias": self.bias,
            "rmse": self.rmse,
            "coverage": rate(self.coverage),
            "joint_coverage": rate(self.joint_coverage),
            "type_i_error": rate(self.type_i_error),
            "power": rate(self.power),
            "false_sign_probability": rate(self.false_sign_probability),
            "joint_rejection_probability": rate(self.joint_rejection_probability),
            "joint_correct_sign_probability": rate(self.joint_correct_sign_probability),
            "probability_contexts": {
                item.metric: item.to_dict() for item in self.probability_contexts
            },
        }


def _metric_row(
    scenario: ScenarioV1,
    configuration: str,
    estimand: str,
    replicates: tuple[ReplicateSufficientStatisticsV1, ...],
) -> MetricRowV1:
    cells = tuple(item.cell(estimand, configuration) for item in replicates)
    total = len(cells)
    oracle_certified = sum(item.oracle_certified for item in cells)
    oracle_not_certified = total - oracle_certified
    reported = sum(item.reported for item in cells)
    false_reported = sum(item.reported and not item.oracle_certified for item in cells)
    eligible = tuple(
        item
        for item in cells
        if item.reported
        and item.oracle_certified
        and item.truth is not None
        and item.estimate is not None
    )
    eligible_retained = len(eligible)
    abstained = total - reported
    exact_decisions = sum(
        item.reported_status
        == ("CERTIFIED" if item.oracle_certified else "NOT_CERTIFIED")
        for item in cells
    )
    correct_reports = reported - false_reported
    joint_denominator = oracle_certified
    if eligible:
        errors = tuple(item.estimate - item.truth for item in eligible)
        bias = math.fsum(errors) / len(errors)
        rmse = math.sqrt(math.fsum(value * value for value in errors) / len(errors))
    else:
        bias = None
        rmse = None

    coverage_successes = sum(
        item.lower <= item.truth <= item.upper for item in eligible
    )
    coverage = _fraction(coverage_successes, eligible_retained)
    joint_coverage = _fraction(coverage_successes, joint_denominator)
    rejection_successes = sum(
        not (item.lower <= 0.0 <= item.upper) for item in eligible
    )
    if estimand == "psi_natural":
        type_i = None
        power = None
        false_sign = None
        joint_rejection = None
        joint_correct_sign = None
    elif scenario.tau == 0:
        type_i = _fraction(rejection_successes, eligible_retained)
        power = None
        false_sign = None
        joint_rejection = _fraction(rejection_successes, joint_denominator)
        joint_correct_sign = None
    else:
        type_i = None
        power = _fraction(rejection_successes, eligible_retained)
        direction = 1.0 if scenario.tau > 0 else -1.0
        false_sign_successes = sum(item.estimate * direction < 0.0 for item in eligible)
        false_sign = _fraction(false_sign_successes, eligible_retained)
        joint_rejection = _fraction(rejection_successes, joint_denominator)
        joint_correct_sign = _fraction(
            sum(item.estimate * direction > 0.0 for item in eligible),
            joint_denominator,
        )

    false_reportability_rate = _fraction(false_reported, oracle_not_certified)
    eligible_retention_rate = _fraction(eligible_retained, oracle_certified)
    abstention_rate = _fraction(abstained, total)
    conditional_report_accuracy = _fraction(correct_reports, reported)
    joint_decision_accuracy = _fraction(exact_decisions, total)
    conditional_zero_reason = (
        "NO_ORACLE_CERTIFIED_ESTIMATES"
        if oracle_certified == 0
        else "NO_REPORTED_ORACLE_CERTIFIED_ESTIMATES"
    )
    probability_contexts = [
        _applicable_probability_context(
            "false_reportability_rate",
            false_reportability_rate,
            eligible_n=oracle_not_certified,
            reported_n=false_reported,
            zero_reason="NO_ORACLE_NOT_CERTIFIED_ESTIMATES",
        ),
        _applicable_probability_context(
            "eligible_retention_rate",
            eligible_retention_rate,
            eligible_n=oracle_certified,
            reported_n=eligible_retained,
            zero_reason="NO_ORACLE_CERTIFIED_ESTIMATES",
        ),
        _applicable_probability_context(
            "abstention_rate",
            abstention_rate,
            eligible_n=total,
            reported_n=abstained,
            zero_reason="NO_REPLICATES",
        ),
        _applicable_probability_context(
            "conditional_report_accuracy",
            conditional_report_accuracy,
            eligible_n=reported,
            reported_n=reported,
            zero_reason="NO_REPORTED_DECISIONS",
        ),
        _applicable_probability_context(
            "joint_decision_accuracy",
            joint_decision_accuracy,
            eligible_n=total,
            reported_n=total,
            zero_reason="NO_REPLICATES",
        ),
        _applicable_probability_context(
            "coverage",
            coverage,
            eligible_n=oracle_certified,
            reported_n=eligible_retained,
            zero_reason=conditional_zero_reason,
        ),
        _applicable_probability_context(
            "joint_coverage",
            joint_coverage,
            eligible_n=oracle_certified,
            reported_n=eligible_retained,
            zero_reason="NO_ORACLE_CERTIFIED_ESTIMATES",
        ),
    ]
    if estimand == "psi_natural":
        structural_reason = "ESTIMAND_NOT_ZERO_EFFECT_TEST"
        probability_contexts.extend(
            _inapplicable_probability_context(
                metric,
                reason=structural_reason,
                eligible_n=oracle_certified,
                reported_n=eligible_retained,
            )
            for metric in (
                "type_i_error",
                "power",
                "false_sign_probability",
                "joint_rejection_probability",
                "joint_correct_sign_probability",
            )
        )
    elif scenario.tau == 0:
        probability_contexts.extend(
            (
                _applicable_probability_context(
                    "type_i_error",
                    type_i,
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                    zero_reason=conditional_zero_reason,
                ),
                _inapplicable_probability_context(
                    "power",
                    reason="NULL_SCENARIO",
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                ),
                _inapplicable_probability_context(
                    "false_sign_probability",
                    reason="NULL_SCENARIO",
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                ),
                _applicable_probability_context(
                    "joint_rejection_probability",
                    joint_rejection,
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                    zero_reason="NO_ORACLE_CERTIFIED_ESTIMATES",
                ),
                _inapplicable_probability_context(
                    "joint_correct_sign_probability",
                    reason="NULL_SCENARIO",
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                ),
            )
        )
    else:
        probability_contexts.extend(
            (
                _inapplicable_probability_context(
                    "type_i_error",
                    reason="NONNULL_SCENARIO",
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                ),
                _applicable_probability_context(
                    "power",
                    power,
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                    zero_reason=conditional_zero_reason,
                ),
                _applicable_probability_context(
                    "false_sign_probability",
                    false_sign,
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                    zero_reason=conditional_zero_reason,
                ),
                _applicable_probability_context(
                    "joint_rejection_probability",
                    joint_rejection,
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                    zero_reason="NO_ORACLE_CERTIFIED_ESTIMATES",
                ),
                _applicable_probability_context(
                    "joint_correct_sign_probability",
                    joint_correct_sign,
                    eligible_n=oracle_certified,
                    reported_n=eligible_retained,
                    zero_reason="NO_ORACLE_CERTIFIED_ESTIMATES",
                ),
            )
        )
    return MetricRowV1(
        scenario_id=scenario.scenario_id,
        configuration=configuration,
        estimand=estimand,
        total=total,
        oracle_certified=oracle_certified,
        oracle_not_certified=oracle_not_certified,
        reported=reported,
        false_reported=false_reported,
        eligible_retained=eligible_retained,
        abstained=abstained,
        exact_decisions=exact_decisions,
        false_reportability_rate=false_reportability_rate,
        eligible_retention_rate=eligible_retention_rate,
        abstention_rate=abstention_rate,
        conditional_report_accuracy=conditional_report_accuracy,
        joint_decision_accuracy=joint_decision_accuracy,
        bias=bias,
        rmse=rmse,
        coverage=coverage,
        joint_coverage=joint_coverage,
        type_i_error=type_i,
        power=power,
        false_sign_probability=false_sign,
        joint_rejection_probability=joint_rejection,
        joint_correct_sign_probability=joint_correct_sign,
        probability_contexts=tuple(probability_contexts),
    )


def finalize_metrics(parts: object) -> tuple[MetricRowV1, ...]:
    """Merge disjoint batches in replicate order and compute registered metrics."""

    if (
        type(parts) is not tuple
        or not parts
        or any(type(item) is not BatchSufficientStatisticsV1 for item in parts)
    ):
        raise ValueError("batch parts")
    scenario_ids = {item.scenario_id for item in parts}
    profile_ids = {item.evaluator_profile_sha256 for item in parts}
    if (
        len(scenario_ids) != 1
        or any(item.registered_replications != 2000 for item in parts)
        or len(profile_ids) != 1
    ):
        raise ValueError("batch parts")
    scenario_id = next(iter(scenario_ids))
    scenario = _SCENARIO_BY_ID[scenario_id]
    replicates = tuple(
        sorted(
            (replicate for part in parts for replicate in part.replicates),
            key=lambda item: item.replicate,
        )
    )
    identities = tuple(item.replicate for item in replicates)
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate replicate")
    return tuple(
        _metric_row(scenario, configuration, estimand, replicates)
        for configuration in _evaluator_module.CONFIGURATIONS
        for estimand in ESTIMAND_ORDER
    )


@dataclass(frozen=True)
class MQDBoundWitnessV1:
    name: str
    true_arm_laws: tuple[tuple[tuple[str, int, Fraction], ...], ...]
    measured_arm_laws: tuple[tuple[tuple[str, int, Fraction], ...], ...]
    declared_maps: tuple[tuple[tuple[str, str], ...], ...]

    def __post_init__(self) -> None:
        if self.name != "m_q_d":
            raise ValueError("m/q/d witness name")
        for label, arms in (
            ("true arm laws", self.true_arm_laws),
            ("measured arm laws", self.measured_arm_laws),
        ):
            if type(arms) is not tuple or len(arms) != 2:
                raise ValueError(label)
            for law in arms:
                self._validate_law(law, label)
        if type(self.declared_maps) is not tuple or len(self.declared_maps) != 2:
            raise ValueError("declared maps")
        for true_law, measured_law, declared_map in zip(
            self.true_arm_laws,
            self.measured_arm_laws,
            self.declared_maps,
            strict=True,
        ):
            if type(declared_map) is not tuple or not declared_map:
                raise ValueError("declared map")
            pairs: list[tuple[str, str]] = []
            for pair in declared_map:
                if (
                    type(pair) is not tuple
                    or len(pair) != 2
                    or any(type(value) is not str or not value for value in pair)
                ):
                    raise ValueError("declared map")
                pairs.append(pair)
            measured_keys = tuple(atom[0] for atom in measured_law)
            true_keys = {atom[0] for atom in true_law}
            if (
                tuple(source for source, _ in pairs) != measured_keys
                or pairs != sorted(pairs)
                or len({source for source, _ in pairs}) != len(pairs)
                or len({target for _, target in pairs}) != len(pairs)
                or any(target not in true_keys for _, target in pairs)
            ):
                raise ValueError("declared map")
        primitives = tuple(
            (row.replacement, row.omitted_mass, row.residual_tv) for row in self.rows
        )
        if (
            not any(replacement > 0 for replacement, _, _ in primitives)
            or not any(q > 0 for _, q, _ in primitives)
            or not any(d > 0 for _, _, d in primitives)
        ):
            raise ValueError("m/q/d primitives")
        if self.bound <= 0 or not self.attains_bound:
            raise ValueError("m/q/d bound witness")

    @staticmethod
    def _validate_law(law: tuple[tuple[str, int, Fraction], ...], label: str) -> None:
        if type(law) is not tuple or not law:
            raise ValueError(label)
        keys: list[str] = []
        total = Fraction(0)
        for atom in law:
            if type(atom) is not tuple or len(atom) != 3:
                raise ValueError(label)
            key, outcome, mass = atom
            if (
                type(key) is not str
                or not key
                or not key.isascii()
                or outcome not in (0, 1)
                or type(outcome) is not int
                or type(mass) is not Fraction
                or mass <= 0
            ):
                raise ValueError(label)
            keys.append(key)
            total += mass
        if keys != sorted(keys) or len(keys) != len(set(keys)) or total != 1:
            raise ValueError(label)

    @staticmethod
    def _mean(law: tuple[tuple[str, int, Fraction], ...]) -> Fraction:
        return sum((Fraction(outcome) * mass for _, outcome, mass in law), Fraction(0))

    @staticmethod
    def _arm_primitives(
        true_law: tuple[tuple[str, int, Fraction], ...],
        measured_law: tuple[tuple[str, int, Fraction], ...],
        declared_map: tuple[tuple[str, str], ...],
    ) -> tuple[int, Fraction, Fraction]:
        true = {key: (outcome, mass) for key, outcome, mass in true_law}
        mapped_targets = {target for _, target in declared_map}
        replacement = int(any(source != target for source, target in declared_map))
        omitted_mass = sum(
            (mass for key, (_, mass) in true.items() if key not in mapped_targets),
            Fraction(0),
        )
        if replacement:
            return replacement, omitted_mass, Fraction(0)
        retained_mass = sum((true[target][1] for target in mapped_targets), Fraction(0))
        true_outcome_mass = {
            outcome: sum(
                (
                    mass / retained_mass
                    for key, (value, mass) in true.items()
                    if key in mapped_targets and value == outcome
                ),
                Fraction(0),
            )
            for outcome in (0, 1)
        }
        measured_outcome_mass = {
            outcome: sum(
                (mass for _, value, mass in measured_law if value == outcome),
                Fraction(0),
            )
            for outcome in (0, 1)
        }
        residual_tv = (
            sum(
                (
                    abs(true_outcome_mass[outcome] - measured_outcome_mass[outcome])
                    for outcome in (0, 1)
                ),
                Fraction(0),
            )
            / 2
        )
        return replacement, omitted_mass, residual_tv

    @property
    def rows(self) -> tuple[BoundRow, ...]:
        return tuple(
            BoundRow(
                arm=arm,
                analysis_weight=Fraction(1),
                replacement=primitives[0],
                omitted_mass=primitives[1],
                residual_tv=primitives[2],
            )
            for arm, primitives in enumerate(
                self._arm_primitives(true_law, measured_law, declared_map)
                for true_law, measured_law, declared_map in zip(
                    self.true_arm_laws,
                    self.measured_arm_laws,
                    self.declared_maps,
                    strict=True,
                )
            )
        )

    @property
    def bound(self) -> Fraction:
        return contrast_error_bound_exact(self.rows)

    @property
    def true_contrast(self) -> Fraction:
        means = tuple(self._mean(law) for law in self.true_arm_laws)
        return means[1] - means[0]

    @property
    def measured_contrast(self) -> Fraction:
        means = tuple(self._mean(law) for law in self.measured_arm_laws)
        return means[1] - means[0]

    @property
    def attained_error(self) -> Fraction:
        return abs(self.measured_contrast - self.true_contrast)

    @property
    def attains_bound(self) -> bool:
        return self.attained_error == self.bound


@dataclass(frozen=True)
class BoundWitnessV1:
    name: str
    true_arm_laws: tuple[tuple[tuple[int, Fraction], ...], ...]
    measured_arm_laws: tuple[tuple[tuple[int, Fraction], ...], ...]

    def __post_init__(self) -> None:
        if self.name != "attainment_99_over_50":
            raise ValueError("bound witness name")
        for label, arms in (
            ("true arm laws", self.true_arm_laws),
            ("measured arm laws", self.measured_arm_laws),
        ):
            if type(arms) is not tuple or len(arms) != 2:
                raise ValueError(label)
            for law in arms:
                if type(law) is not tuple or not law:
                    raise ValueError(label)
                support: list[Fraction] = []
                total = Fraction(0)
                for atom in law:
                    if type(atom) is not tuple or len(atom) != 2:
                        raise ValueError(label)
                    outcome, mass = atom
                    if type(outcome) not in (int, Fraction):
                        raise ValueError(label)
                    outcome = Fraction(outcome)
                    if not 0 <= outcome <= 1:
                        raise ValueError(label)
                    if type(mass) is not Fraction or mass <= 0:
                        raise ValueError(label)
                    support.append(outcome)
                    total += mass
                if len(set(support)) != len(support) or support != sorted(support):
                    raise ValueError(label)
                if total != 1:
                    raise ValueError(label)
        if not self.attains_bound:
            raise ValueError("bound witness does not attain bound")
        if self.bound != Fraction(99, 50):
            raise ValueError("99/50 witness")

    @staticmethod
    def _mean(law: tuple[tuple[int, Fraction], ...]) -> Fraction:
        return sum((Fraction(value) * mass for value, mass in law), Fraction(0))

    @staticmethod
    def _tv(
        left: tuple[tuple[int, Fraction], ...],
        right: tuple[tuple[int, Fraction], ...],
    ) -> Fraction:
        left_mass = {Fraction(value): mass for value, mass in left}
        right_mass = {Fraction(value): mass for value, mass in right}
        support = set(left_mass) | set(right_mass)
        return (
            sum(
                (
                    abs(
                        left_mass.get(value, Fraction(0))
                        - right_mass.get(value, Fraction(0))
                    )
                    for value in support
                ),
                Fraction(0),
            )
            / 2
        )

    @property
    def true_arm_means(self) -> tuple[Fraction, Fraction]:
        return tuple(self._mean(law) for law in self.true_arm_laws)

    @property
    def measured_arm_means(self) -> tuple[Fraction, Fraction]:
        return tuple(self._mean(law) for law in self.measured_arm_laws)

    @property
    def arm_tv_distances(self) -> tuple[Fraction, Fraction]:
        return tuple(
            self._tv(true_law, measured_law)
            for true_law, measured_law in zip(
                self.true_arm_laws,
                self.measured_arm_laws,
                strict=True,
            )
        )

    @property
    def rows(self) -> tuple[BoundRow, ...]:
        return tuple(
            BoundRow(
                arm=arm,
                analysis_weight=Fraction(1),
                replacement=0,
                omitted_mass=Fraction(0),
                residual_tv=self.arm_tv_distances[arm],
            )
            for arm in (0, 1)
        )

    @property
    def bound(self) -> Fraction:
        return contrast_error_bound_exact(self.rows)

    @property
    def true_contrast(self) -> Fraction:
        return self.true_arm_means[1] - self.true_arm_means[0]

    @property
    def measured_contrast(self) -> Fraction:
        return self.measured_arm_means[1] - self.measured_arm_means[0]

    @property
    def attained_error(self) -> Fraction:
        return abs(self.measured_contrast - self.true_contrast)

    @property
    def attains_bound(self) -> bool:
        return self.attained_error == self.bound


_BOUND_WITNESSES = (
    MQDBoundWitnessV1(
        name="m_q_d",
        true_arm_laws=(
            (
                ("a", 0, Fraction(1, 2)),
                ("b", 0, Fraction(1, 4)),
                ("c", 0, Fraction(1, 4)),
            ),
            (("a", 1, Fraction(1)),),
        ),
        measured_arm_laws=(
            (("a", 1, Fraction(1, 2)), ("b", 1, Fraction(1, 2))),
            (("z", 0, Fraction(1)),),
        ),
        declared_maps=((("a", "a"), ("b", "b")), (("z", "a"),)),
    ),
    BoundWitnessV1(
        name="attainment_99_over_50",
        true_arm_laws=(((0, Fraction(1)),), ((1, Fraction(1)),)),
        measured_arm_laws=(
            ((0, Fraction(1, 100)), (1, Fraction(99, 100))),
            ((0, Fraction(99, 100)), (1, Fraction(1, 100))),
        ),
    ),
)


def bound_witnesses() -> tuple[MQDBoundWitnessV1 | BoundWitnessV1, ...]:
    return _BOUND_WITNESSES


@dataclass(frozen=True)
class MisclassificationWitnessV1:
    name: str
    mu0: Fraction
    mu1: Fraction
    se0: Fraction
    sp0: Fraction
    se1: Fraction
    sp1: Fraction

    @property
    def true_contrast(self) -> Fraction:
        return self.mu1 - self.mu0

    @property
    def measured_contrast(self) -> Fraction:
        return terminal_measured_contrast_exact(
            self.mu0, self.mu1, self.se0, self.sp0, self.se1, self.sp1
        )


_MISCLASSIFICATION_WITNESSES = (
    MisclassificationWitnessV1(
        "common_misclassification",
        Fraction(1, 5),
        Fraction(2, 5),
        Fraction(9, 10),
        Fraction(9, 10),
        Fraction(9, 10),
        Fraction(9, 10),
    ),
    MisclassificationWitnessV1(
        "differential_sign_reversal",
        Fraction(2, 5),
        Fraction(3, 5),
        Fraction(1),
        Fraction(1),
        Fraction(1, 2),
        Fraction(1),
    ),
)


def misclassification_witnesses() -> tuple[MisclassificationWitnessV1, ...]:
    return _MISCLASSIFICATION_WITNESSES


@dataclass(frozen=True)
class SelectionAtomV1:
    covariate: int
    outcome: int
    mass: Fraction
    selection_probability: Fraction

    def __post_init__(self) -> None:
        if self.covariate not in (0, 1) or self.outcome not in (0, 1):
            raise ValueError("selection atom")
        if type(self.mass) is not Fraction or self.mass <= 0:
            raise ValueError("selection atom mass")
        if (
            type(self.selection_probability) is not Fraction
            or not 0 < self.selection_probability <= 1
        ):
            raise ValueError("selection probability")


@dataclass(frozen=True)
class SelectionWorldV1:
    atoms: tuple[SelectionAtomV1, ...]

    def __post_init__(self) -> None:
        if not self.atoms or sum((item.mass for item in self.atoms), Fraction(0)) != 1:
            raise ValueError("selection world")

    @property
    def population_mean(self) -> Fraction:
        return sum((item.mass * item.outcome for item in self.atoms), Fraction(0))

    @property
    def complete_case_mean(self) -> Fraction:
        denominator = sum(
            (item.mass * item.selection_probability for item in self.atoms), Fraction(0)
        )
        numerator = sum(
            (
                item.mass * item.selection_probability * item.outcome
                for item in self.atoms
            ),
            Fraction(0),
        )
        return numerator / denominator

    @property
    def ipw_mean(self) -> Fraction:
        return sum(
            (
                item.mass
                * item.selection_probability
                * item.outcome
                / item.selection_probability
                for item in self.atoms
            ),
            Fraction(0),
        )

    @property
    def observed_law(self) -> tuple[tuple[tuple[int, int], Fraction], ...]:
        return tuple(
            sorted(
                (
                    (
                        (item.covariate, item.outcome),
                        item.mass * item.selection_probability,
                    )
                    for item in self.atoms
                ),
                key=lambda item: item[0],
            )
        )


@dataclass(frozen=True)
class SelectionWitnessV1:
    name: str
    worlds: tuple[SelectionWorldV1, ...]
    status: str


_SELECTION_WITNESSES = (
    SelectionWitnessV1(
        name="mcar",
        worlds=(
            SelectionWorldV1(
                (
                    SelectionAtomV1(0, 0, Fraction(1, 2), Fraction(1, 2)),
                    SelectionAtomV1(1, 1, Fraction(1, 2), Fraction(1, 2)),
                )
            ),
        ),
        status=selection_estimand_status("mcar"),
    ),
    SelectionWitnessV1(
        name="mar_ipw",
        worlds=(
            SelectionWorldV1(
                (
                    SelectionAtomV1(0, 0, Fraction(1, 2), Fraction(1, 4)),
                    SelectionAtomV1(1, 1, Fraction(1, 2), Fraction(3, 4)),
                )
            ),
        ),
        status=selection_estimand_status("mar+positivity"),
    ),
    SelectionWitnessV1(
        name="mnar_pair",
        worlds=(
            SelectionWorldV1(
                (
                    SelectionAtomV1(0, 0, Fraction(1, 2), Fraction(1)),
                    SelectionAtomV1(0, 1, Fraction(1, 2), Fraction(1, 2)),
                )
            ),
            SelectionWorldV1(
                (
                    SelectionAtomV1(0, 0, Fraction(5, 8), Fraction(4, 5)),
                    SelectionAtomV1(0, 1, Fraction(3, 8), Fraction(2, 3)),
                )
            ),
        ),
        status=selection_estimand_status("mnar"),
    ),
)


def selection_witnesses() -> tuple[SelectionWitnessV1, ...]:
    return _SELECTION_WITNESSES


@dataclass(frozen=True)
class OverlapWitnessV1:
    name: str
    family_units: tuple[frozenset[str], ...]

    @property
    def union_units(self) -> frozenset[str]:
        return frozenset().union(*self.family_units)

    @property
    def sum_count(self) -> int:
        return sum(len(item) for item in self.family_units)

    @property
    def union_count(self) -> int:
        return len(self.union_units)


_OVERLAP_WITNESSES = (
    OverlapWitnessV1("disjoint", (frozenset(("u0", "u1")), frozenset(("u2", "u3")))),
    OverlapWitnessV1("nested", (frozenset(("u0",)), frozenset(("u0", "u1")))),
    OverlapWitnessV1(
        "full_overlap", (frozenset(("u0", "u1")), frozenset(("u0", "u1")))
    ),
)


def overlap_witnesses() -> tuple[OverlapWitnessV1, ...]:
    return _OVERLAP_WITNESSES


__all__ = [
    "ESTIMAND_ORDER",
    "FAMILY_ORDER",
    "SCHEMA_VERSION",
    "STREAM_NAMES",
    "BatchSufficientStatisticsV1",
    "BoundWitnessV1",
    "EstimateSufficientStatisticsV1",
    "EvaluatorProfileCellV1",
    "EvaluatorProfileV1",
    "ExactFractionV1",
    "MetricRowV1",
    "MisclassificationWitnessV1",
    "OverlapWitnessV1",
    "PotentialOutcomesV1",
    "ReplicateSufficientStatisticsV1",
    "ScenarioV1",
    "SelectionAtomV1",
    "SelectionWitnessV1",
    "SelectionWorldV1",
    "SiteInferenceV1",
    "apply_fault_transforms",
    "bound_witnesses",
    "build_evaluator_profile",
    "exact_probability",
    "finalize_metrics",
    "fixed_covariates",
    "generate_potential_outcomes",
    "misclassification_witnesses",
    "overlap_witnesses",
    "philox_seed",
    "policy_ipw_site",
    "registered_scenarios",
    "selection_witnesses",
    "simulate_batch",
    "t7_interval",
]
