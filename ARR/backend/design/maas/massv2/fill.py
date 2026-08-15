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
# How little a scheme is allowed to ask for. A brief may want less than the cap
# - a gallery is not a shop block - but a 근린생활시설 that uses 41% of its
# allowed floor area has left half the parcel's value unbuilt, and on the
# Uijeongbu sheet three of sixteen sat at 0.41, 0.50 and 0.63. The form is still
# protected: `worth_taking` refuses any step that costs the composition, so a
# scheme that genuinely cannot grow without ceasing to be itself stops early and
# keeps its own number.
_TARGET_FLOOR = 0.75
# How much of its articulation a scheme may lose in exchange for floor area.
# Not zero: growth legitimately rounds a composition off a little. But a step
# that costs a fifth of the move is buying area with the design.
_ARTICULATION_KEPT = 0.80
# A volume may run a little past the parcel's own storey count - a double-height
# hall, a parapet - without becoming a stick. Past this it is not a tall room,
# it is a different decision about where the building goes.
_VOLUME_HEIGHT_SLACK = 1.25


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


def _articulation(form: MatrixForm, *, storey_height_m: float, allowed_at=None) -> float:
    """The articulation of the building that gets delivered, not of a draft.

    Compiled without `allowed_at` this measures a mass nobody receives. Every
    area in `legal_fit` is taken through the clip, and the sheet compiles
    through it too, so growth was the one reader left looking at the uncut
    form - and it is the reader whose whole job is to refuse a step that costs
    the composition. A widening step that pushes a court out to the boundary
    closes it, because the clip takes the wall that was holding it open; uncut,
    the court is still there and the step reads as free. That is one building
    measured two ways, for the fourth time in this package.
    """

    source = compile_matrix_form(
        form, storey_height_m=storey_height_m, allowed_at=allowed_at
    )
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

    # A scheme placed on the coverage axis is there on purpose. Growing its plan
    # would move it off the band it was made to occupy, so those grow upward
    # only; the position is the point of the copy.
    if form.extra.get("coverage_band"):
        allow_plan_growth = False

    authored = form.extra.get("far_target")
    share = float(
        authored if authored is not None
        else target_utilization if target_utilization is not None
        else _DEFAULT_TARGET
    )
    share = max(_TARGET_FLOOR, min(1.0, share))
    capacity = capacity * share

    current = best.form
    storey = float(form.floor_height_m or site.floor_height_m)
    started_at = _articulation(current, storey_height_m=storey, allowed_at=site.plan_at)
    floor = started_at * _ARTICULATION_KEPT
    taller = wider = 0
    reason = "reached_step_limit"

    def _settled_to_parcel_height(form: MatrixForm) -> MatrixForm:
        """No single volume taller than the storeys this parcel affords.

        The whole-building ceiling is an average - floor area over projection -
        so a scheme can sit under it while one thin piece of it shoots up, and
        that is what a bundle of sticks on a plinth is. Refusing it by verb was
        a patch: fields were stopped from growing upward, and the next sheet
        came back with sticks made by `stack` on a split instead. The rule is
        about the piece's height, not about which word produced it.

        용적률 divided by 건폐율 again - the same number that bounds slenderness
        and stops the growth loop. Uijeongbu affords 4.2 storeys, so a volume
        past 12.5 m is going up where the parcel asked it to go out.
        """

        ceiling = storeys_allowed * storey * _VOLUME_HEIGHT_SLACK
        tallest = max(
            (item.z_span()[1] - item.z_span()[0] for item in form.additive()),
            default=0.0,
        )
        if tallest <= ceiling or tallest <= 1e-6:
            return form
        return _taller(form, ceiling / tallest)

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
        return _articulation(
            candidate.form, storey_height_m=storey, allowed_at=site.plan_at
        ) >= floor

    # How many storeys this parcel's own law implies: the floor area it allows
    # over the ground it allows. On the Uijeongbu parcel that is 2499.7 / 499.9
    # = 5. It is not a number anyone chose - it is 용적률 divided by 건폐율.
    #
    # Without it, the coverage axis manufactures towers. A scheme on the 45%
    # band that is told to fill its 용적률 needs 2499.7 / (0.45 * 499.9) = 11.1
    # storeys, so every low-coverage cell came out as a tower and no amount of
    # new vocabulary changed it. Above this line a scheme has stopped being a
    # building that takes less ground and started being a building that goes up
    # instead, which is a different decision and not the one the axis is about.
    #
    # Plan growth is not capped by it: widening buys storeys honestly, by taking
    # more ground, and that moves the scheme along the coverage axis where the
    # architect can see it.
    storeys_allowed = site.far_capacity_m2 / max(site.ground_capacity_m2, 1e-9)

    # Settle an over-tall scheme onto the parcel before growing it. Stopping
    # growth at the ceiling was not enough: a scheme authored tall arrives above
    # it, and nothing else pulls it down - eleven storeys on 45% of the ground
    # is entirely lawful here, so the legal fit has no reason to object. This is
    # the only place that says a tower is the wrong answer to a small footprint.
    # No single volume taller than the storeys this parcel affords. The ceiling
    # below is an average - floor area over projection - so a scheme can sit
    # under it while one thin piece shoots up, and that is what a bundle of
    # sticks on a plinth is. Refusing it by verb was a patch: fields were
    # stopped from rising and the next sheet came back with sticks made by
    # `stack` on a split instead. The rule is about a piece's height, not about
    # which word produced it. Settled once here rather than refused inside the
    # growth loop, where it made every scheme run all twenty-four steps.
    settled_height = fit_to_site(_settled_to_parcel_height(current), site)
    if settled_height.satisfied and settled_height.gross_floor_area_m2 > 0.0:
        best, current = settled_height, settled_height.form

    # Storeys standing = floor area over the ground it stands on, and both
    # numbers have to come off the same building. The fit already carries the
    # projection it certified through the clip, so taking it from there rather
    # than re-projecting the uncut form is one measurement instead of two: a
    # scheme hanging over the boundary was dividing a cut floor area by an
    # uncut footprint, reading short, and being told it had storeys to spare.
    standing = best.gross_floor_area_m2 / max(best.ground_area_m2, 1.0)
    if standing > storeys_allowed:
        settled = fit_to_site(_taller(current, storeys_allowed / standing), site)
        if settled.satisfied and settled.gross_floor_area_m2 > 0.0:
            best, current = settled, settled.form

    for step in range(_MAX_STEPS):
        if best.gross_floor_area_m2 >= capacity * _FULL_ENOUGH:
            reason = "far_capacity_reached"
            break

        standing = best.gross_floor_area_m2 / max(best.ground_area_m2, 1.0)
        if standing >= storeys_allowed:
            if not allow_plan_growth:
                reason = "parcel_storey_ceiling_reached"
                break
            grown = _wider(current, 1.12)
            candidate = fit_to_site(grown, site)
            if worth_taking(candidate):
                best, current, wider = candidate, candidate.form, wider + 1
                continue
            reason = "parcel_storey_ceiling_reached"
            break

        # Ask for exactly the shortfall rather than a fixed increment: the step
        # size is a property of how far this scheme is from its ceiling.
        #
        # Unless the scheme is a field, which buys area by spreading and never
        # by rising. Left to grow upward, a field's small objects came back as
        # a bundle of sticks on a plinth at 용적률 0.99 - lawful, slender enough
        # to pass, and not the building that was authored.
        if form.extra.get("growth") != "plan":
            want = capacity / max(best.gross_floor_area_m2, 1.0)
            grown = _taller(current, min(1.35, max(1.02, want)))
            candidate = fit_to_site(grown, site)
            if worth_taking(candidate):
                best, current, taller = candidate, candidate.form, taller + 1
                continue

        if not allow_plan_growth:
            reason = "height_exhausted"
            break

        headroom = site.ground_capacity_m2 / max(best.ground_area_m2, 1.0)
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
