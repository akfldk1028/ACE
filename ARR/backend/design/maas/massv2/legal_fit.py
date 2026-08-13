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

from shapely.geometry import Polygon
from shapely.ops import unary_union

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    scale_matrix4,
    translation_matrix4,
    validate_matrix4,
)

from .compile import _plan
from .form import MatrixForm, Placement
from .legal import LegalSite


# Below this the shrink is not worth another pass; further passes chase float
# noise rather than area.
_CONVERGED = 0.995
_MAX_PASSES = 6


@dataclass(frozen=True)
class LegalFitResult:
    form: MatrixForm
    ground_area_m2: float
    ground_capacity_m2: float
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


def _pulled_inside(placement: Placement, allowed: Polygon) -> Placement | None:
    """Shrink one volume about its own centre until its plan is inside `allowed`.

    Only this volume moves. The alternative in the existing path is to clip the
    whole solid, which changes a mass the author did not design and forfeits its
    right to be rendered.
    """

    plan = _plan(placement)
    if plan.is_empty or allowed.is_empty:
        return None
    if allowed.contains(plan):
        return placement
    inside = plan.intersection(allowed)
    if inside.is_empty or float(inside.area) <= 1e-9:
        return None
    centre = plan.centroid
    factor = (float(inside.area) / float(plan.area)) ** 0.5
    for _attempt in range(_MAX_PASSES):
        candidate = _scaled_in_plan(placement, factor, (float(centre.x), float(centre.y)))
        if allowed.contains(_plan(candidate)):
            return candidate
        factor *= 0.94
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

    allowed = site.plan_at(0.0)
    if allowed is None or allowed.is_empty:
        return form
    plans = [_plan(item) for item in form.additive()]
    plans = [item for item in plans if not item.is_empty]
    if not plans:
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
        _low, high = placement.z_span()
        allowed = site.plan_at(high)
        if allowed is None or allowed.is_empty:
            kept.append(placement)
            continue
        adjusted = _pulled_inside(placement, allowed)
        if adjusted is None:
            # Nothing of this volume is legal at its own height. Dropping it is
            # honest; keeping a sliver would report a form the author never made.
            pulled += 1
            continue
        if adjusted is not placement:
            pulled += 1
        kept.append(adjusted)

    fitted = replace(current, placements=tuple(kept))
    final_area = projected_ground_area(fitted)
    return LegalFitResult(
        form=fitted,
        ground_area_m2=final_area,
        ground_capacity_m2=capacity,
        passes=passes,
        plan_scale_applied=total_scale,
        volumes_pulled_in=pulled,
        satisfied=bool(fitted.additive()) and (capacity <= 0.0 or final_area <= capacity + 1e-6),
    )
