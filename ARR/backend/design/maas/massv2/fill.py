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

from .compile import compile_matrix_form
from .form import MatrixForm
from .legal import LegalSite
from .measure import measure_form
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
# What a scheme asks for when it says nothing. Not 1.0: a brief that wants the
# whole capacity should have to say so, because the schemes that do not want it
# are the ones with something to say about form.
_DEFAULT_TARGET = 0.85
# How much of its articulation a scheme may lose in exchange for floor area.
# Not zero: growth legitimately rounds a composition off a little. But a step
# that costs a fifth of the move is buying area with the design.
_ARTICULATION_KEPT = 0.80


@dataclass(frozen=True)
class FillResult:
    fit: LegalFitResult
    steps_taken: int
    grew_height: int
    grew_plan: int
    reason: str
    target_utilization: float = 1.0

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_fill.v1",
            "steps_taken": self.steps_taken,
            "grew_height": self.grew_height,
            "grew_plan": self.grew_plan,
            "stopped_because": self.reason,
            "target_utilization": round(self.target_utilization, 3),
        }


def _articulation(form: MatrixForm, *, storey_height_m: float) -> float:
    source = compile_matrix_form(form, storey_height_m=storey_height_m)
    return measure_form(source).articulation() if source is not None else 0.0


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
    target_utilization: float | None = None,
) -> FillResult:
    """Grow toward the scheme's own target, refit each step, stop at a ceiling.

    `target_utilization` is a share of the 용적률 capacity, not a maximum to be
    chased. Filling the capacity is one brief among several: a shop block fills
    it, a gallery does not, and a scheme of small dispersed rooms cannot without
    ceasing to be one. Growing everything to the cap produced exactly the
    monoculture that follows from a single objective - Moriyama's scattered
    rooms came back as two sticks, because the only way to add area to a
    dispersed composition is to pull it upward.

    So the target comes from the scheme (`MatrixForm.extra["far_target"]`), then
    from the caller, and only then from a default. Growth still stops at the
    first legal ceiling; the target only says when to stop wanting more.

    Each step is proposed and then judged: the grown form goes back through
    `fit_to_site`, and a step is kept only if the fit still certifies it and the
    floor area actually rose. A step the sunlight envelope claws straight back
    is not progress, and taking it on trust is how a growth loop becomes an
    oscillation.
    """

    best = fit_to_site(form, site)
    capacity = site.far_capacity_m2
    if capacity <= 0.0:
        return FillResult(best, 0, 0, 0, "no_far_capacity", 0.0)

    authored = form.extra.get("far_target")
    share = float(
        authored if authored is not None
        else target_utilization if target_utilization is not None
        else _DEFAULT_TARGET
    )
    capacity = capacity * max(0.05, min(1.0, share))

    current = best.form
    storey = float(form.floor_height_m or site.floor_height_m)
    started_at = _articulation(current, storey_height_m=storey)
    floor = started_at * _ARTICULATION_KEPT
    taller = wider = 0
    reason = "reached_step_limit"

    def worth_taking(candidate: LegalFitResult) -> bool:
        """Lawful, larger, and still the same building.

        Floor area is not the only thing a step can spend. Grown without this,
        CCTV's two legs and high return came back as a slab - lawful, fuller,
        and no longer the move. A step that costs a fifth of the scheme's
        articulation is buying area with the design.
        """

        if not candidate.satisfied:
            return False
        if candidate.gross_floor_area_m2 <= best.gross_floor_area_m2 + 1.0:
            return False
        return _articulation(candidate.form, storey_height_m=storey) >= floor

    for step in range(_MAX_STEPS):
        if best.gross_floor_area_m2 >= capacity * _FULL_ENOUGH:
            reason = "far_capacity_reached"
            break

        # Ask for exactly the shortfall rather than a fixed increment: the step
        # size is a property of how far this scheme is from its ceiling.
        want = capacity / max(best.gross_floor_area_m2, 1.0)
        grown = _taller(current, min(1.35, max(1.02, want)))
        candidate = fit_to_site(grown, site)
        if worth_taking(candidate):
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
        if worth_taking(candidate):
            best, current, wider = candidate, candidate.form, wider + 1
            continue

        reason = "growth_would_cost_the_form"
        break

    return FillResult(best, taller + wider, taller, wider, reason, share)
