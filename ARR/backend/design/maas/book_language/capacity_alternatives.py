"""Site-derived FAR alternatives between program projection and hard gates.

The alternatives in this module are not additional building typologies and do
not author parcel geometry.  They derive several utilization targets from one
measured feasible-capacity contract, then ask the existing geometry compiler
to fit the same typed form language to the corresponding plan-area target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CAPACITY_ALTERNATIVE_SCHEMA = "arr.maas.capacity_alternative.v1"


@dataclass(frozen=True)
class CapacityAlternativeSpec:
    alternative_id: str
    label: str
    intent: str
    target_rule: str

    def to_manifest_item(self) -> dict[str, Any]:
        return {
            "id": self.alternative_id,
            "label": self.label,
            "intent": self.intent,
            "target_rule": self.target_rule,
            "generation_scope": "post_program_pre_hard_gate",
        }


CAPACITY_ALTERNATIVE_SPECS = (
    CapacityAlternativeSpec(
        "spatial_reserve",
        "Spatial reserve",
        "retain the feasible minimum while preserving void and public-space capacity",
        "feasible_minimum",
    ),
    CapacityAlternativeSpec(
        "balanced_yield",
        "Balanced yield",
        "split the interval between feasible minimum and the program brief target",
        "midpoint_of_minimum_and_brief_target",
    ),
    CapacityAlternativeSpec(
        "brief_target",
        "Brief target",
        "fit the typed form to the program-aware target utilization",
        "program_brief_target",
    ),
    CapacityAlternativeSpec(
        "maximum_feasible",
        "Maximum feasible",
        "test the upper design-yield band while retaining exact legal, parking and public-space gates",
        "midpoint_of_program_target_and_feasible_ceiling",
    ),
)

_SPEC_BY_ID = {spec.alternative_id: spec for spec in CAPACITY_ALTERNATIVE_SPECS}


def capacity_alternative_catalog() -> list[dict[str, Any]]:
    return [spec.to_manifest_item() for spec in CAPACITY_ALTERNATIVE_SPECS]


def capacity_alternative_for_lattice_index(index: int) -> CapacityAlternativeSpec:
    """Stratify the existing variation lattice without multiplying live VLM calls."""

    return CAPACITY_ALTERNATIVE_SPECS[int(index) % len(CAPACITY_ALTERNATIVE_SPECS)]


def capacity_alternative_for_host(
    index: int,
    base_contract: dict[str, Any] | None,
    *,
    host_area_m2: float,
    floor_count: int,
) -> CapacityAlternativeSpec:
    """Cycle only targets that the current legal generation host can reach.

    Some variations are intentionally born in a smaller sunlight-safe upper
    section. Assigning the near-maximum parcel target to that host by raw index
    creates a mathematically impossible candidate before geometry language is
    considered. This upper bound uses only host area, floor count and the
    measured feasible-capacity denominator; exact mesh capacity remains a
    downstream hard gate.
    """

    contract = base_contract or {}
    feasible_maximum = max(
        0.0,
        float(contract.get("feasible_maximum_floor_area_m2") or 0.0),
    )
    if feasible_maximum <= 1e-9:
        return capacity_alternative_for_lattice_index(index)
    host_capacity_upper_bound = (
        max(0.0, float(host_area_m2))
        * max(1, int(floor_count))
        / feasible_maximum
    )
    reachable = tuple(
        spec
        for spec in CAPACITY_ALTERNATIVE_SPECS
        if float(build_capacity_alternative(contract, spec)["target_utilization"])
        <= host_capacity_upper_bound + 1e-9
    )
    choices = reachable or (CAPACITY_ALTERNATIVE_SPECS[0],)
    return choices[int(index) % len(choices)]


def build_capacity_alternative(
    base_contract: dict[str, Any] | None,
    alternative: CapacityAlternativeSpec | str,
) -> dict[str, Any]:
    """Derive one target from measured site capacity, never a freehand ratio."""

    spec = _SPEC_BY_ID[str(alternative)] if isinstance(alternative, str) else alternative
    contract = base_contract or {}
    minimum = max(0.0, min(0.98, float(contract.get("minimum_utilization") or 0.0)))
    brief_target = max(
        minimum,
        min(0.98, float(contract.get("target_utilization") or minimum)),
    )
    # The upper design band is derived from the live program target and the
    # measured feasible ceiling.  A fixed 0.98 target made virtually every
    # expressive/voided form fail and left only legal-envelope-shaped boxes.
    # Taking the remaining interval's midpoint keeps the alternative truly
    # above the brief while leaving a measured design reserve for the same
    # public threshold, void and parking gates used by every other band.
    maximum_design_yield = brief_target + (1.0 - brief_target) * 0.5
    targets = {
        "spatial_reserve": minimum,
        "balanced_yield": minimum + (brief_target - minimum) * 0.5,
        "brief_target": brief_target,
        "maximum_feasible": maximum_design_yield,
    }
    target = max(minimum, min(0.98, targets[spec.alternative_id]))
    feasible_maximum = max(
        0.0,
        float(contract.get("feasible_maximum_floor_area_m2") or 0.0),
    )
    floor_count = max(1, int(contract.get("requested_floors") or 1))
    generation_area = max(
        0.0,
        float(contract.get("generation_site_area_m2") or 0.0),
    )
    target_floor_area = feasible_maximum * target
    target_plan_area = target_floor_area / floor_count
    target_plan_coverage = (
        min(0.95, target_plan_area / generation_area)
        if generation_area > 1e-9
        else 0.0
    )
    return {
        "schema_version": CAPACITY_ALTERNATIVE_SCHEMA,
        "alternative_id": spec.alternative_id,
        "label": spec.label,
        "intent": spec.intent,
        "target_rule": spec.target_rule,
        "stage": "post_program_pre_hard_gate",
        "feasible_minimum_utilization": round(minimum, 4),
        "program_brief_target_utilization": round(brief_target, 4),
        "target_utilization": round(target, 4),
        "feasible_maximum_floor_area_m2": round(feasible_maximum, 3),
        "target_floor_area_m2": round(target_floor_area, 3),
        "target_base_plan_area_m2": round(target_plan_area, 3),
        "target_base_plan_coverage": round(target_plan_coverage, 4),
        "projection_mode": "typed_form_plan_fit",
        "hard_gates_remain_downstream": True,
    }


def capacity_contract_for_alternative(
    base_contract: dict[str, Any] | None,
    alternative: dict[str, Any],
) -> dict[str, Any]:
    """Return a projected copy consumable by the existing source bridge."""

    projected = dict(base_contract or {})
    projected.update({
        "target_utilization": alternative.get("target_utilization", 0.0),
        "target_floor_area_m2": alternative.get("target_floor_area_m2", 0.0),
        "target_base_plan_area_m2": alternative.get("target_base_plan_area_m2", 0.0),
        "target_base_plan_coverage": alternative.get("target_base_plan_coverage", 0.0),
        "capacity_alternative_id": alternative.get("alternative_id", ""),
    })
    return projected


def evaluate_capacity_alternative(
    alternative: dict[str, Any],
    measurement: dict[str, Any] | None,
) -> dict[str, Any]:
    measured = measurement or {}
    achieved = max(
        0.0,
        float(measured.get("feasible_capacity_utilization") or 0.0),
    )
    target = max(0.0, float(alternative.get("target_utilization") or 0.0))
    return {
        **alternative,
        "achieved_utilization": round(achieved, 4),
        "target_gap": round(achieved - target, 4),
        "target_hard_pass": bool(achieved + 1e-9 >= target),
        "measurement_schema_version": measured.get("schema_version"),
    }


def capacity_fit_score(
    alternative: dict[str, Any],
    measurement: dict[str, Any] | None,
) -> float:
    """Balance requested-target fit with absolute feasible-capacity yield."""

    measured = measurement or {}
    achieved = min(
        1.0,
        max(0.0, float(measured.get("feasible_capacity_utilization") or 0.0)),
    )
    target = max(1e-9, float(alternative.get("target_utilization") or 0.0))
    target_fit = min(1.0, achieved / target)
    return round(target_fit * 0.70 + achieved * 0.30, 6)


def capacity_retry_plan_coverage(
    current_coverage: float,
    alternative: dict[str, Any],
    measurement: dict[str, Any] | None,
) -> float:
    """Derive one bounded plan-fit retry from measured target shortfall.

    Floor area scales approximately with plan area for the same typed vertical
    profile. The ratio is therefore evidence-derived, not a use-specific shape
    macro. A caller may retry once; exact capacity, legal and retention gates
    still decide whether the widened materialization survives.
    """

    coverage = max(0.0, min(0.95, float(current_coverage or 0.0)))
    measured = measurement or {}
    achieved = max(
        0.0,
        float(measured.get("feasible_capacity_utilization") or 0.0),
    )
    target = max(0.0, float(alternative.get("target_utilization") or 0.0))
    if achieved <= 1e-9 or achieved + 1e-9 >= target:
        return round(coverage, 6)
    return round(min(0.95, coverage * target / achieved), 6)


__all__ = [
    "CAPACITY_ALTERNATIVE_SCHEMA",
    "CAPACITY_ALTERNATIVE_SPECS",
    "CapacityAlternativeSpec",
    "build_capacity_alternative",
    "capacity_fit_score",
    "capacity_retry_plan_coverage",
    "capacity_alternative_catalog",
    "capacity_alternative_for_host",
    "capacity_alternative_for_lattice_index",
    "capacity_contract_for_alternative",
    "evaluate_capacity_alternative",
]
