"""Grow a scheme into the parcel until a law stops it.

The legal fit only ever reduces - it answers "is this lawful", never "is this
enough". So an authored composition whose proportions came from a building on a
different site stays at whatever it happened to land on: measured across the
built-work vocabulary on the Uijeongbu parcel, 용적률 came out at a median of
0.42 and one scheme at 0.16. Lawful, and an under-built site.

This is the other half. The scheme is grown until one of its own ceilings binds,
and the two directions are kept separate because the laws are:

  Height buys floor area at constant ground take, so it is tried first - the
  scheme keeps the footprint it was composed with.

  Plan buys both, so it is tried only when height has run out, and it moves the
  scheme along the coverage axis, which is a change of position rather than a
  change of size.

Growth stops at the first ceiling. Nothing here overrides `fit_to_site`; the fit
is re-run after every step and has the last word.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .form import MatrixForm
from .legal import LegalSite
from .legal_fit import (
    LegalFitResult,
    _gross_floor_area,
    _scaled_in_plan,
    fit_to_site,
    projected_ground_area,
)
from .variations import _stretched


# A scheme within this much of its floor-area ceiling is full; chasing the rest
# costs a storey and buys a rounding error.
_FULL_ENOUGH = 0.97
_MAX_STEPS = 24


@dataclass(frozen=True)
class FillResult:
    fit: LegalFitResult
    steps_taken: int
    grew_height: int
    grew_plan: int
    reason: str

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_fill.v1",
            "steps_taken": self.steps_taken,
            "grew_height": self.grew_height,
            "grew_plan": self.grew_plan,
            "stopped_because": self.reason,
        }


def _taller(form: MatrixForm, factor: float) -> MatrixForm:
    return replace(
        form,
        placements=tuple(
            _stretched(item, factor) if item.kind == "additive" else item
            for item in form.placements
        ),
    )


def _wider(form: MatrixForm, factor: float) -> MatrixForm:
    plans = [item for item in form.additive()]
    if not plans:
        return form
    corners = [corner for item in plans for corner in item.corners()]
    anchor = (
        (min(x for x, _y, _z in corners) + max(x for x, _y, _z in corners)) / 2.0,
        (min(y for _x, y, _z in corners) + max(y for _x, y, _z in corners)) / 2.0,
    )
    return replace(
        form,
        placements=tuple(_scaled_in_plan(item, factor, anchor) for item in form.placements),
    )


def fill_to_site(
    form: MatrixForm,
    site: LegalSite,
    *,
    allow_plan_growth: bool = True,
) -> FillResult:
    """Grow, refit, keep whatever the fit certifies, and stop at the first ceiling.

    Each step is proposed and then judged: the grown form goes back through
    `fit_to_site`, and a step is only kept if the fit still certifies it and the
    floor area actually rose. A step that the sunlight envelope claws straight
    back is not progress, and taking it on trust is how a growth loop turns into
    an oscillation.
    """

    best = fit_to_site(form, site)
    capacity = site.far_capacity_m2
    if capacity <= 0.0:
        return FillResult(best, 0, 0, 0, "no_far_capacity")

    current = best.form
    taller = wider = 0
    reason = "reached_step_limit"

    for step in range(_MAX_STEPS):
        if best.gross_floor_area_m2 >= capacity * _FULL_ENOUGH:
            reason = "far_capacity_reached"
            break

        # Ask for exactly the shortfall rather than a fixed increment: the step
        # size is a property of how far this scheme is from its ceiling.
        want = capacity / max(best.gross_floor_area_m2, 1.0)
        grown = _taller(current, min(1.35, max(1.02, want)))
        candidate = fit_to_site(grown, site)
        if candidate.satisfied and candidate.gross_floor_area_m2 > best.gross_floor_area_m2 + 1.0:
            best, current, taller = candidate, candidate.form, taller + 1
            continue

        if not allow_plan_growth:
            reason = "height_exhausted"
            break

        ground = projected_ground_area(current)
        headroom = site.ground_capacity_m2 / max(ground, 1.0)
        if headroom <= 1.01:
            reason = "both_ceilings_reached"
            break
        grown = _wider(current, min(1.20, headroom ** 0.5))
        candidate = fit_to_site(grown, site)
        if candidate.satisfied and candidate.gross_floor_area_m2 > best.gross_floor_area_m2 + 1.0:
            best, current, wider = candidate, candidate.form, wider + 1
            continue

        reason = "no_lawful_growth_left"
        break

    return FillResult(best, taller + wider, taller, wider, reason)
