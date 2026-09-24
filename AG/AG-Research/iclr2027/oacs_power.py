"""Deterministic prospective cluster power plans for MAS/OACS domains."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re
from typing import Any

from scipy.optimize import brentq
from scipy.stats import nct, t

from iclr2027.oacs_domain_census import (
    DomainCensusError,
    DomainCensusV1,
    verify_domain_census_bytes,
)


_SCHEMA = "oacs-domain-power-plan/v1"
_DOMAINS = {"architecture", "jci"}
_DIRECTION = "one_sided_greater"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_FAMILY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_PLAN_KEYS = {
    "schema",
    "domain",
    "census_sha256",
    "direction",
    "alpha",
    "target_power",
    "cluster_count",
    "target_standardized_effect",
    "achieved_prospective_power",
    "minimum_detectable_effect",
    "multiplicity_family",
    "structural_floor_powered",
}


class PowerPlanError(ValueError):
    """Raised when a prospective power calculation or plan is invalid."""


def _require_cluster_count(cluster_count: object) -> int:
    if type(cluster_count) is not int:
        raise TypeError("cluster_count must be a native integer")
    if cluster_count < 3:
        raise PowerPlanError("cluster_count must be at least 3")
    return cluster_count


def _require_float(value: object, field: str) -> float:
    if type(value) is not float:
        raise TypeError(f"{field} must be a native float")
    if not math.isfinite(value):
        raise PowerPlanError(f"{field} must be finite")
    return value


def _require_alpha(alpha: object) -> float:
    value = _require_float(alpha, "alpha")
    if not 0.0 < value < 1.0:
        raise PowerPlanError("alpha must be strictly between 0 and 1")
    return value


def _require_nonnegative_float(value: object, field: str) -> float:
    result = _require_float(value, field)
    if result < 0.0 or (result == 0.0 and math.copysign(1.0, result) < 0.0):
        raise PowerPlanError(f"{field} must be nonnegative and not negative zero")
    return result


def paired_cluster_power(*, cluster_count: int, effect: float, alpha: float) -> float:
    """Return prospective power for a one-sided paired cluster-mean t test."""

    count = _require_cluster_count(cluster_count)
    standardized_effect = _require_nonnegative_float(effect, "effect")
    significance = _require_alpha(alpha)
    degrees_of_freedom = count - 1
    critical = t.ppf(1.0 - significance, degrees_of_freedom)
    noncentrality = standardized_effect * math.sqrt(count)
    power = float(1.0 - nct.cdf(critical, degrees_of_freedom, noncentrality))
    if not math.isfinite(power) or not 0.0 <= power <= 1.0:
        raise PowerPlanError("prospective power calculation did not converge")
    return power


def minimum_detectable_effect(
    *,
    cluster_count: int,
    alpha: float,
    target_power: float,
) -> float:
    """Invert prospective power for the minimum nonnegative standardized effect."""

    count = _require_cluster_count(cluster_count)
    significance = _require_alpha(alpha)
    target = _require_float(target_power, "target_power")
    if not significance < target < 1.0:
        raise PowerPlanError("target_power must be strictly between alpha and 1")

    def objective(effect: float) -> float:
        return (
            paired_cluster_power(
                cluster_count=count,
                effect=float(effect),
                alpha=significance,
            )
            - target
        )

    upper = 1.0
    while objective(upper) < 0.0 and upper < 1_048_576.0:
        upper *= 2.0
    if objective(upper) < 0.0:
        raise PowerPlanError("unable to bracket minimum detectable effect")
    try:
        result = brentq(objective, 0.0, upper, xtol=1e-13, rtol=1e-14, maxiter=200)
    except (RuntimeError, ValueError) as exc:
        raise PowerPlanError(
            "minimum detectable effect inversion did not converge"
        ) from exc
    result = float(result)
    if not math.isfinite(result) or result < 0.0:
        raise PowerPlanError(
            "minimum detectable effect inversion returned an invalid value"
        )
    return result


@dataclass(frozen=True)
class DomainPowerPlanV1:
    """One domain's pre-outcome prospective power authority."""

    schema: str
    domain: str
    census_sha256: str
    direction: str
    alpha: float
    target_power: float
    cluster_count: int
    target_standardized_effect: float
    achieved_prospective_power: float
    minimum_detectable_effect: float
    multiplicity_family: str
    structural_floor_powered: bool

    def __post_init__(self) -> None:
        if type(self.schema) is not str or self.schema != _SCHEMA:
            raise PowerPlanError("schema is not the closed power-plan schema")
        if type(self.domain) is not str or self.domain not in _DOMAINS:
            raise PowerPlanError("domain is not a closed enum")
        if (
            type(self.census_sha256) is not str
            or _HASH_RE.fullmatch(self.census_sha256) is None
        ):
            raise PowerPlanError("census_sha256 must be a lowercase SHA-256")
        if type(self.direction) is not str or self.direction != _DIRECTION:
            raise PowerPlanError("direction is not the closed one-sided greater test")
        _require_alpha(self.alpha)
        target = _require_float(self.target_power, "target_power")
        if not self.alpha < target < 1.0:
            raise PowerPlanError("target_power must be strictly between alpha and 1")
        _require_cluster_count(self.cluster_count)
        effect = _require_nonnegative_float(
            self.target_standardized_effect,
            "target_standardized_effect",
        )
        achieved = _require_float(
            self.achieved_prospective_power,
            "achieved_prospective_power",
        )
        if not 0.0 <= achieved <= 1.0:
            raise PowerPlanError("achieved_prospective_power must be between 0 and 1")
        mde = _require_nonnegative_float(
            self.minimum_detectable_effect,
            "minimum_detectable_effect",
        )
        if (
            type(self.multiplicity_family) is not str
            or _FAMILY_RE.fullmatch(self.multiplicity_family) is None
        ):
            raise PowerPlanError(
                "multiplicity_family must be a closed opaque identifier"
            )
        if type(self.structural_floor_powered) is not bool:
            raise TypeError("structural_floor_powered must be a native boolean")

        expected_achieved = paired_cluster_power(
            cluster_count=self.cluster_count,
            effect=effect,
            alpha=self.alpha,
        )
        if achieved != expected_achieved:
            raise PowerPlanError(
                "achieved prospective power does not match the frozen inputs"
            )
        expected_mde = minimum_detectable_effect(
            cluster_count=self.cluster_count,
            alpha=self.alpha,
            target_power=target,
        )
        if mde != expected_mde:
            raise PowerPlanError(
                "minimum detectable effect does not match the frozen inputs"
            )
        expected_status = expected_achieved >= target
        if self.structural_floor_powered is not expected_status:
            raise PowerPlanError(
                "structural floor powered status does not match prospective power"
            )

    @classmethod
    def create(
        cls,
        *,
        domain: str,
        census_sha256: str,
        direction: str,
        alpha: float,
        target_power: float,
        cluster_count: int,
        target_standardized_effect: float,
        multiplicity_family: str,
    ) -> DomainPowerPlanV1:
        """Create a plan from frozen pre-outcome inputs and deterministic calculations."""

        achieved = paired_cluster_power(
            cluster_count=cluster_count,
            effect=target_standardized_effect,
            alpha=alpha,
        )
        mde = minimum_detectable_effect(
            cluster_count=cluster_count,
            alpha=alpha,
            target_power=target_power,
        )
        return cls(
            schema=_SCHEMA,
            domain=domain,
            census_sha256=census_sha256,
            direction=direction,
            alpha=alpha,
            target_power=target_power,
            cluster_count=cluster_count,
            target_standardized_effect=target_standardized_effect,
            achieved_prospective_power=achieved,
            minimum_detectable_effect=mde,
            multiplicity_family=multiplicity_family,
            structural_floor_powered=achieved >= target_power,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "domain": self.domain,
            "census_sha256": self.census_sha256,
            "direction": self.direction,
            "alpha": self.alpha,
            "target_power": self.target_power,
            "cluster_count": self.cluster_count,
            "target_standardized_effect": self.target_standardized_effect,
            "achieved_prospective_power": self.achieved_prospective_power,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "multiplicity_family": self.multiplicity_family,
            "structural_floor_powered": self.structural_floor_powered,
        }

    @classmethod
    def from_dict(cls, value: object) -> DomainPowerPlanV1:
        if type(value) is not dict:
            raise TypeError("power plan must be an exact dict")
        if set(value) != _PLAN_KEYS:
            raise PowerPlanError("power plan keys do not match the closed schema")
        return cls(**value)


def domain_power_plan_bytes(plan: DomainPowerPlanV1) -> bytes:
    """Return canonical sorted-key compact UTF-8 JSON followed by exactly one LF."""

    if type(plan) is not DomainPowerPlanV1:
        raise TypeError("plan must be an exact DomainPowerPlanV1")
    try:
        encoded = json.dumps(
            plan.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PowerPlanError("power plan cannot be encoded as UTF-8 JSON") from exc
    return encoded + b"\n"


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PowerPlanError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def verify_domain_power_plan_bytes(raw: bytes) -> DomainPowerPlanV1:
    """Parse only the unique canonical representation of a valid domain plan."""

    if type(raw) is not bytes:
        raise TypeError("raw power plan must be bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                PowerPlanError(f"invalid JSON constant: {value}")
            ),
        )
    except PowerPlanError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PowerPlanError("invalid power-plan JSON") from exc
    plan = DomainPowerPlanV1.from_dict(payload)
    if raw != domain_power_plan_bytes(plan):
        raise PowerPlanError("power-plan bytes are not canonical JSON")
    return plan


def validate_plan_census_binding(
    *,
    plan: DomainPowerPlanV1,
    census_bytes: bytes,
) -> DomainCensusV1:
    """Bind a domain plan to the exact canonical domain census and its cluster count."""

    if type(plan) is not DomainPowerPlanV1:
        raise TypeError("plan must be an exact DomainPowerPlanV1")
    try:
        census = verify_domain_census_bytes(census_bytes)
    except (DomainCensusError, TypeError) as exc:
        raise PowerPlanError("invalid canonical domain census") from exc
    if sha256(census_bytes).hexdigest() != plan.census_sha256:
        raise PowerPlanError("census SHA-256 binding does not match the power plan")
    if any(unit.domain != plan.domain for unit in census.units):
        raise PowerPlanError("power plan and census must not pool domains")
    if census.cluster_count != plan.cluster_count:
        raise PowerPlanError(
            "cluster count binding does not match the canonical census"
        )
    return census


def validate_separate_power_plans(
    plans: tuple[DomainPowerPlanV1, DomainPowerPlanV1],
) -> tuple[DomainPowerPlanV1, DomainPowerPlanV1]:
    """Require powered Architecture and JCI plans in their canonical separate order."""

    if type(plans) is not tuple:
        raise TypeError("plans must be an exact tuple")
    if len(plans) != 2 or any(type(plan) is not DomainPowerPlanV1 for plan in plans):
        raise PowerPlanError("plans must contain exactly two domain power plans")
    if tuple(plan.domain for plan in plans) != ("architecture", "jci"):
        raise PowerPlanError(
            "plans must keep architecture and jci separate and ordered"
        )
    for plan in plans:
        expected_achieved = paired_cluster_power(
            cluster_count=plan.cluster_count,
            effect=plan.target_standardized_effect,
            alpha=plan.alpha,
        )
        if expected_achieved < plan.target_power:
            raise PowerPlanError(f"{plan.domain} prospective power insufficient")
    return plans


__all__ = [
    "DomainPowerPlanV1",
    "PowerPlanError",
    "domain_power_plan_bytes",
    "minimum_detectable_effect",
    "paired_cluster_power",
    "validate_plan_census_binding",
    "validate_separate_power_plans",
    "verify_domain_power_plan_bytes",
]
