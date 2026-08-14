"""Fit a form to the parcel by moving its volumes, not by carving the result.

The existing path searches for one global 4x4 pose for the whole rigid body, and
when it cannot find one it says `whole_solid_affine_fit_infeasible`, falls back
to clipping the solid against the legal prism with CSG, and then demotes what
comes out to `legal_analysis_proxy_only` - a mass that can no longer be rendered
or scored. Authored intent is spent to buy legality.

Here every volume carries its own matrix, so an offending volume can be reduced
or moved on its own and the rest of the composition survives untouched. Two laws
are enforced, in the order they bind:

  건축면적 - 건축법 시행령 제119조 제1항 제2호. The horizontal projection of the
  whole building, unioned over every height, against the parcel's BCR ceiling.
  Because it is a projection, only plan dimensions can pay for it.

  정북일조 - the legal plan shrinks as height rises. A volume is checked at the
  top of its own span, which is where it is tightest, and pulled in there.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from shapely.ops import unary_union

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    scale_matrix4,
    translation_matrix4,
    validate_matrix4,
)

from .compile import _plan, compile_matrix_form
from .form import MatrixForm, Placement
from .legal import LegalSite
from .measure import gross_floor_area_m2, storeys_in


# Below this the shrink is not worth another pass; further passes chase float
# noise rather than area.
_CONVERGED = 0.995
_MAX_PASSES = 6
# Floor area is trimmed one storey at a time, so the bound is a storey count
# rather than a ratio. A building with more storeys than this over its capacity
# was authored for a different parcel.
_STOREY_TRIMS = 40
# Halvings used to find the height at which the sunlight envelope runs out. Ten
# brings a sixty-metre span inside six centimetres, which is finer than any
# dimension this language works in.
_BISECTIONS = 10


@dataclass(frozen=True)
class LegalFitResult:
    form: MatrixForm
    ground_area_m2: float
    ground_capacity_m2: float
    gross_floor_area_m2: float
    far_capacity_m2: float
    passes: int
    plan_scale_applied: float
    volumes_pulled_in: int
    satisfied: bool

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_legal_fit.v1",
            "ground_area_m2": round(self.ground_area_m2, 3),
            "ground_capacity_m2": round(self.ground_capacity_m2, 3),
            "ground_take": round(
                self.ground_area_m2 / max(self.ground_capacity_m2, 1e-9), 4
            ),
            "gross_floor_area_m2": round(self.gross_floor_area_m2, 3),
            "far_capacity_m2": round(self.far_capacity_m2, 3),
            "far_utilization": round(
                self.gross_floor_area_m2 / max(self.far_capacity_m2, 1e-9), 4
            ),
            "passes": self.passes,
            "plan_scale_applied": round(self.plan_scale_applied, 5),
            "volumes_pulled_in": self.volumes_pulled_in,
            "satisfied": self.satisfied,
            "method": "per_volume_affine_no_csg",
        }


def projected_ground_area(form: MatrixForm) -> float:
    """건축면적: the plan union over every height, not the ground floor.

    A mass whose ground floor is modest while its upper floors overhang to the
    cap still covers that much ground, and measuring the lowest band would file
    it as dispersed.
    """

    plans = [_plan(item) for item in form.additive()]
    plans = [item for item in plans if not item.is_empty and item.area > 0.0]
    if not plans:
        return 0.0
    return float(unary_union(plans).area)


def _gross_floor_area(form: MatrixForm, *, floor_height_m: float) -> float:
    """연면적 of a form, measured exactly the way it will be reported.

    Sharing the storey rule was not enough. The fit measured each placement over
    its own full height while the report measured the compiled bands, and a
    volume ten metres tall counts as three storeys whole but four once it is cut
    at five - so four schemes the fit had made lawful came back over the ceiling.

    Compiling here is affordable precisely because this language has no 3D CSG:
    a compile is band cuts and 2D shapely, not booleans and mesh traversals. One
    measure, one answer.

    "One measure" includes the storey height, which this dropped. A leaning
    volume is cut at storeys and an upright one is not, so compiling without it
    collapsed a raking bar into a single band - and the fit then certified a
    용적률 the report measured 26% higher. `opening_terraced_ell` was passed as
    lawful at 2268 m2 against a 2499.7 m2 ceiling while actually standing at
    3149.4. Same form, same rule, two answers, and the gate believed the
    forgiving one.
    """

    source = compile_matrix_form(form, storey_height_m=floor_height_m)
    if source is None:
        return 0.0
    return gross_floor_area_m2(source, floor_height_m=floor_height_m)


def _scaled_in_plan(placement: Placement, factor: float, anchor: tuple[float, float]) -> Placement:
    """Shrink a volume in plan about a shared anchor, leaving its height alone.

    건축면적 is a projection, so height cannot pay for it. Scaling about a shared
    anchor rather than each volume's own centre keeps the composition's
    relationships - a shifted stack stays shifted instead of collapsing into a
    concentric wedding cake.
    """

    matrix = compose_matrix4(
        placement.matrix,
        translation_matrix4((-anchor[0], -anchor[1], 0.0)),
        scale_matrix4((factor, factor, 1.0)),
        translation_matrix4((anchor[0], anchor[1], 0.0)),
    )
    return replace(placement, matrix=validate_matrix4(matrix))


def _shortened(placement: Placement, factor: float) -> Placement:
    """Lower the top, keeping the base where the author put it."""

    low, _high = placement.z_span()
    matrix = compose_matrix4(
        placement.matrix,
        translation_matrix4((0.0, 0.0, -low)),
        scale_matrix4((1.0, 1.0, max(1e-3, factor))),
        translation_matrix4((0.0, 0.0, low)),
    )
    return replace(placement, matrix=validate_matrix4(matrix))


def _lowered_under_envelope(placement: Placement, allowed_at) -> Placement | None:
    """Bring a volume down to the tallest height that still has an envelope.

    Bisection rather than fixed steps: the height where the envelope runs out is
    a property of the parcel, not a number to guess at, and halving finds it to
    within a few centimetres in the same handful of evaluations a coarse ladder
    would spend missing it.
    """

    low, high = placement.z_span()
    span = high - low
    if span <= 1e-6:
        return None
    lower, upper = 0.0, 1.0
    best: Placement | None = None
    for _step in range(_BISECTIONS):
        middle = (lower + upper) / 2.0
        candidate = _shortened(placement, middle)
        _clow, chigh = candidate.z_span()
        ceiling = allowed_at(chigh)
        if ceiling is not None and not ceiling.is_empty:
            best = candidate
            lower = middle
        else:
            upper = middle
    return best


def _pulled_inside(
    placement: Placement, allowed_at, *, minimum_plan_share: float = 0.45
) -> Placement | None:
    """Bring one volume inside the sunlight envelope, in plan or in height.

    정북일조 says step back as you rise, and a building may answer that two ways:
    move away from the boundary, or stop short of the height where the envelope
    bites. Paying only in plan - which is what this did first - pinches a tall
    volume into a sliver or drops it, when lowering its top would have kept the
    author's proportions intact. So plan is tried first, and if it would cost
    more than `minimum_plan_share` of the volume's footprint, height pays
    instead.

    Only this volume moves. The alternative in the existing pipeline is to clip
    the whole solid, which changes a mass the author did not design and forfeits
    its right to be rendered or scored.
    """

    low, high = placement.z_span()
    plan = _plan(placement)
    if plan.is_empty:
        return None

    allowed = allowed_at(high)
    if allowed is None or allowed.is_empty:
        # Nothing at all is buildable at this height - measured on the live
        # parcel, `plan_at` returns None from about 80 m up. Reading that as
        # "no envelope to check" and waving the volume through is a fail-open on
        # a legal check, and heights of 64 m were already being produced. The
        # volume has to come down to a height that does have an envelope.
        return _lowered_under_envelope(placement, allowed_at)

    if allowed.contains(plan):
        return placement

    inside = plan.intersection(allowed)
    share = float(inside.area) / float(plan.area) if float(plan.area) > 0.0 else 0.0
    if share >= minimum_plan_share:
        centre = plan.centroid
        factor = share ** 0.5
        for _attempt in range(_MAX_PASSES):
            candidate = _scaled_in_plan(placement, factor, (float(centre.x), float(centre.y)))
            if allowed.contains(_plan(candidate)):
                return candidate
            factor *= 0.94

    # Plan alone is too expensive here. Find the highest level whose envelope
    # still holds this footprint, and stop the volume there.
    span = high - low
    if span <= 1e-6:
        return None
    for step in range(1, _MAX_PASSES + 1):
        factor = 1.0 - step / (_MAX_PASSES + 1.0)
        candidate = _shortened(placement, factor)
        _clow, chigh = candidate.z_span()
        ceiling = allowed_at(chigh)
        if ceiling is not None and not ceiling.is_empty and ceiling.contains(_plan(candidate)):
            return candidate
    return None


def seat_on_site(form: MatrixForm, site: LegalSite) -> MatrixForm:
    """Move the whole form onto the buildable area before anything is checked.

    Families are authored in their own frame with a corner at the origin, which
    keeps the vocabulary readable and parcel-independent. The buildable area is
    inset from the parcel by setbacks, so a form left at the origin sits in the
    corner mostly outside it - and the per-volume check then legitimately drops
    every volume. Seating is a rigid move: it changes where the building is, not
    what it is.
    """

    plans = [_plan(item) for item in form.additive()]
    plans = [item for item in plans if not item.is_empty]
    if not plans:
        return form

    # Seat by the plan at the mass's own top, not at the ground. The sunlight
    # envelope is what binds, and it binds hardest up there: measured on this
    # parcel the buildable plan loses 450 m2 between the ground and 30 m, and
    # its centre moves 3.6 m southwest, because the envelope eats the northern
    # and eastern sides. Centring on the ground plan puts every mass in the
    # middle of the plot with an even margin all round - which is why they read
    # as objects set down on a site rather than buildings on a parcel - and
    # spends the one corner where height is actually available.
    top = max(item.z_span()[1] for item in form.additive())
    allowed = site.plan_at(top)
    if allowed is None or allowed.is_empty:
        allowed = site.plan_at(0.0)
    if allowed is None or allowed.is_empty:
        return form

    here = unary_union(plans).centroid
    there = allowed.centroid
    shift = translation_matrix4((float(there.x - here.x), float(there.y - here.y), 0.0))
    return replace(
        form,
        placements=tuple(
            replace(item, matrix=validate_matrix4(compose_matrix4(item.matrix, shift)))
            for item in form.placements
        ),
    )


def fit_to_site(form: MatrixForm, site: LegalSite) -> LegalFitResult:
    """Bring a form inside the parcel's limits by adjusting its volumes."""

    capacity = site.ground_capacity_m2
    current = seat_on_site(form, site)
    total_scale = 1.0
    passes = 0

    # 건축면적 first: it is a whole-building projection, so fixing it volume by
    # volume would just move the overshoot around.
    for _pass in range(_MAX_PASSES):
        area = projected_ground_area(current)
        if capacity <= 0.0 or area <= capacity:
            break
        passes += 1
        factor = (capacity / area) ** 0.5
        bounds = unary_union([_plan(item) for item in current.additive()]).bounds
        anchor = ((bounds[0] + bounds[2]) / 2.0, (bounds[1] + bounds[3]) / 2.0)
        current = replace(
            current,
            placements=tuple(
                _scaled_in_plan(item, factor, anchor) for item in current.placements
            ),
        )
        total_scale *= factor
        if factor >= _CONVERGED:
            break

    # 정북일조 next, per volume, at the top of each volume's own span.
    pulled = 0
    kept: list[Placement] = []
    for placement in current.placements:
        if placement.kind == "subtractive":
            kept.append(placement)
            continue
        adjusted = _pulled_inside(placement, site.plan_at)
        if adjusted is None:
            # Nothing of this volume is legal at its own height. Dropping it is
            # honest; keeping a sliver would report a form the author never made.
            pulled += 1
            continue
        if adjusted is not placement:
            pulled += 1
        kept.append(adjusted)

    fitted = replace(current, placements=tuple(kept))

    # 용적률 last, and paid in height. Floor area is plan times storeys, and plan
    # has already been spent on 건축면적; taking it again would drive the ground
    # take away from the position the scheme was authored at. Height is the free
    # term here, and lowering a volume is the move an architect would make.
    far_capacity = site.far_capacity_m2
    floor_height = float(fitted.floor_height_m or site.floor_height_m)
    if far_capacity > 0.0 and floor_height > 1e-6:
        # Floor area moves in whole storeys, because storeys are counted with
        # `round`. Scaling height by a continuous ratio can shave 1% off a
        # volume without removing a floor, so the loop converges on nothing and
        # leaves the scheme over the ceiling - which is what left two schemes
        # unlawful. Take a storey off the tallest volume instead, and take it
        # from the tallest because that is the one the envelope is tightest on.
        for _pass in range(_STOREY_TRIMS):
            gfa = _gross_floor_area(fitted, floor_height_m=floor_height)
            if gfa <= far_capacity:
                break
            passes += 1
            # Only volumes with a storey to spare are candidates. Picking the
            # tallest outright and stopping when *it* ran out left every other
            # volume untouched, which made this worse rather than better.
            trimmable = [
                item
                for item in fitted.placements
                if item.kind == "additive"
                # A storey can only be taken from something that has two. The
                # rule is the same `storeys_in` the area is measured with, so
                # the loop cannot trim a volume the measure calls one floor.
                and storeys_in(
                    item.z_span()[1] - item.z_span()[0], floor_height_m=floor_height
                ) >= 2
            ]
            if not trimmable:
                break
            tallest = max(trimmable, key=lambda item: item.z_span()[1] - item.z_span()[0])
            low, high = tallest.z_span()
            span = high - low
            trimmed = _shortened(tallest, (span - floor_height) / span)
            fitted = replace(
                fitted,
                placements=tuple(
                    trimmed if item is tallest else item for item in fitted.placements
                ),
            )

    final_area = projected_ground_area(fitted)
    final_gfa = _gross_floor_area(fitted, floor_height_m=floor_height)
    return LegalFitResult(
        form=fitted,
        ground_area_m2=final_area,
        ground_capacity_m2=capacity,
        gross_floor_area_m2=final_gfa,
        far_capacity_m2=far_capacity,
        passes=passes,
        plan_scale_applied=total_scale,
        volumes_pulled_in=pulled,
        satisfied=(
            bool(fitted.additive())
            and (capacity <= 0.0 or final_area <= capacity + 1e-6)
            and (far_capacity <= 0.0 or final_gfa <= far_capacity + 1e-6)
        ),
    )
