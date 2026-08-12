"""How much ground a proposal takes, as a choice rather than a consequence.

건폐율 is a legal ceiling, not a target. A building may take all the ground the
law allows, or hold most of it as court and approach and take a fraction. Those
are different architectural propositions, and an architect picks between them -
so the pipeline has to be able to produce both.

It currently produces only the first. `build_capacity_alternative` derives plan
area from floor area:

    target_plan_area = ground_capacity * legal_field_yield_ratio

so a demanding floor-area target drives the yield ratio toward one and the plan
to the legal ceiling. The four capacity alternatives vary floor area, and plan
area follows them; it is a consequence, never a choice. Measured on PNU
4115011300106840001: 86 of 128 delivered masses within one percent of the cap.

The bands here make it a choice. They are fractions of the same 건폐율 capacity,
so they are legal by construction and say nothing about which is better.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class CoverageBand:
    """One position on the ground-take axis."""

    band_id: str
    label: str
    intent: str
    plan_fraction: float

    def evidence(self) -> dict[str, object]:
        return {
            "band_id": self.band_id,
            "label": self.label,
            "intent": self.intent,
            "plan_fraction": self.plan_fraction,
        }


# Four positions, matching the four capacity alternatives already in the
# pipeline so the two axes can be crossed without inventing a second cadence.
# The fractions are deliberately wide apart: neighbouring proposals that differ
# by a few percent of ground are the same proposal to an architect.
COVERAGE_BANDS: tuple[CoverageBand, ...] = (
    CoverageBand(
        "dispersed_ground",
        "Dispersed ground",
        "hold most of the parcel as court and approach; the building goes up "
        "or spreads thin rather than out",
        0.45,
    ),
    CoverageBand(
        "held_ground",
        "Held ground",
        "take a clear footprint and leave a usable remainder around it",
        0.65,
    ),
    CoverageBand(
        "worked_ground",
        "Worked ground",
        "take most of the ground, keeping the remainder for access and light",
        0.85,
    ),
    CoverageBand(
        "full_ground",
        "Full ground",
        "take the whole 건폐율 the law allows",
        1.00,
    ),
)

_BAND_BY_ID = {band.band_id: band for band in COVERAGE_BANDS}


def coverage_band_ids() -> tuple[str, ...]:
    return tuple(band.band_id for band in COVERAGE_BANDS)


def coverage_band(band_id: str) -> CoverageBand:
    band = _BAND_BY_ID.get(str(band_id))
    if band is None:
        raise KeyError(f"unknown coverage band: {band_id}")
    return band


def plan_area_for_band(
    ground_capacity_m2: float,
    band: CoverageBand | str,
) -> float:
    """Return the ground plate this band asks for, in square metres.

    `ground_capacity_m2` is the 건폐율 capacity the legal field already
    certifies, so every band is legal and the ceiling is never invented here.
    """

    resolved = band if isinstance(band, CoverageBand) else coverage_band(band)
    try:
        capacity = float(ground_capacity_m2)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(capacity) or capacity <= 0.0:
        return 0.0
    return capacity * resolved.plan_fraction


def capacities_under_band(
    floor_capacities: Sequence[float],
    *,
    ground_capacity_m2: float,
    band: CoverageBand | str,
) -> list[float]:
    """Bound every floor's plate by the ground this band takes.

    건축면적 is the horizontal projection of the whole building, so a band that
    holds the ground holds every plate, not only the lowest one. Bounding the
    whole vector is also what lets the stack answer: the floor-prefix selection
    downstream picks the shortest prefix carrying the target, so a smaller plate
    simply asks for more floors.
    """

    ceiling = plan_area_for_band(ground_capacity_m2, band)
    bounded: list[float] = []
    for value in floor_capacities:
        try:
            capacity = float(value)
        except (TypeError, ValueError):
            capacity = 0.0
        if not isfinite(capacity) or capacity <= 0.0:
            bounded.append(0.0)
            continue
        bounded.append(min(capacity, ceiling) if ceiling > 0.0 else capacity)
    return bounded
