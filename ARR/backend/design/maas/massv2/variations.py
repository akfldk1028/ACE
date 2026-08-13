"""Move a composition to a different ground take without changing what it is.

The two axes are independent in a way the old language could not exploit. Ground
take is how much of the allowed footprint the building claims, and for a set of
placed volumes that is a plan scale. Void is a property of the composition - how
the pieces sit relative to one another - and plan scaling leaves it alone,
because scaling a figure and its holes together does not change the share of the
figure that is open.

So a courtyard scheme authored at one ground take can be carried across the
whole coverage axis, and the grid fills from the compositions that already
exist rather than from hand-authoring one scheme per cell. That is the
difference between a vocabulary and a lookup table.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.ops import unary_union

from design.maas.design_space import COVERAGE_BANDS, CoverageBand

from .compile import _plan
from .form import MatrixForm
from .legal_fit import _scaled_in_plan, projected_ground_area


def retarget_ground_take(form: MatrixForm, *, target_area_m2: float) -> MatrixForm | None:
    """Scale the whole composition in plan until it claims `target_area_m2`.

    Height is untouched. 건축면적 is a horizontal projection, so plan is the only
    term that pays for it, and changing height to hit a coverage target would
    silently trade one law against another.

    The scale is applied about the composition's own centre so relationships
    between volumes survive: a bar that overhung its plinth still overhangs it.
    """

    area = projected_ground_area(form)
    if area <= 1e-9 or target_area_m2 <= 1e-9:
        return None
    factor = (target_area_m2 / area) ** 0.5
    if abs(factor - 1.0) < 1e-4:
        return form
    bounds = unary_union([_plan(item) for item in form.additive()]).bounds
    anchor = ((bounds[0] + bounds[2]) / 2.0, (bounds[1] + bounds[3]) / 2.0)
    return replace(
        form,
        name=f"{form.name}@{int(round(target_area_m2))}",
        placements=tuple(_scaled_in_plan(item, factor, anchor) for item in form.placements),
    )


def spread_across_coverage(
    form: MatrixForm,
    *,
    ground_capacity_m2: float,
    bands: tuple[CoverageBand, ...] = COVERAGE_BANDS,
) -> list[MatrixForm]:
    """One copy of this composition per coverage band.

    Bands are fractions of the run's own certified capacity, so this means the
    same thing on any parcel.
    """

    out: list[MatrixForm] = []
    for band in bands:
        # Sit just inside the band's ceiling rather than on it: the legal fit
        # can only ever reduce area further, and a copy authored exactly at the
        # edge lands in the band below as soon as the sunlight envelope bites.
        target = ground_capacity_m2 * band.plan_fraction * 0.97
        moved = retarget_ground_take(form, target_area_m2=target)
        if moved is not None:
            out.append(replace(moved, name=f"{form.name}~{band.band_id}"))
    return out
