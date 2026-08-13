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
from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    scale_matrix4,
    translation_matrix4,
    validate_matrix4,
)

from .compile import _plan
from .form import MatrixForm
from .legal_fit import _gross_floor_area, _scaled_in_plan, projected_ground_area


def retarget_ground_take(
    form: MatrixForm,
    *,
    target_area_m2: float,
    hold_programme: bool = True,
    far_capacity_m2: float = 0.0,
    floor_height_m: float = 3.0,
) -> MatrixForm | None:
    """Scale the composition in plan to claim `target_area_m2`.

    The scale is applied about the composition's own centre so relationships
    between volumes survive: a bar that overhung its plinth still overhangs it.

    `hold_programme` is what makes the copy a real alternative rather than a
    smaller picture of the same building. Taking less ground with the same height
    means building less - measured before this, a 45% copy delivered 45% of the
    floor area and read as an under-built site at 9% 용적률. An architect who
    disperses builds *taller* to hold the same programme, so height rises by the
    inverse of the plan scale. The legal fit still owns both ceilings and will
    cut the height back if 용적률 or the sunlight envelope says so.
    """

    area = projected_ground_area(form)
    if area <= 1e-9 or target_area_m2 <= 1e-9:
        return None
    factor = (target_area_m2 / area) ** 0.5
    if abs(factor - 1.0) < 1e-4:
        return form
    bounds = unary_union([_plan(item) for item in form.additive()]).bounds
    anchor = ((bounds[0] + bounds[2]) / 2.0, (bounds[1] + bounds[3]) / 2.0)
    lift = (
        _programme_lift(
            form, factor=factor, far_capacity_m2=far_capacity_m2, floor_height_m=floor_height_m
        )
        if hold_programme
        else 1.0
    )
    return replace(
        form,
        name=f"{form.name}@{int(round(target_area_m2))}",
        placements=tuple(
            _stretched(_scaled_in_plan(item, factor, anchor), lift)
            for item in form.placements
        ),
    )


def _stretched(placement, lift: float):
    """Raise a volume's top by `lift`, keeping its base where it is."""

    if abs(lift - 1.0) < 1e-6:
        return placement
    low, _high = placement.z_span()
    matrix = compose_matrix4(
        placement.matrix,
        translation_matrix4((0.0, 0.0, -low)),
        scale_matrix4((1.0, 1.0, max(1e-3, lift))),
        translation_matrix4((0.0, 0.0, low)),
    )
    return replace(placement, matrix=validate_matrix4(matrix))


def _programme_lift(
    form: MatrixForm, *, factor: float, far_capacity_m2: float, floor_height_m: float
) -> float:
    """How much taller the copy has to be to hold the same programme.

    The inverse of the plan scale, but never past the 용적률 ceiling. Holding the
    programme unconditionally holds whatever the author wrote, and an authored
    scheme is free to be over capacity - measured here, a U covering most of the
    buildable plan carried 7,183 m2 against a 2,500 m2 ceiling. Preserving that
    at 45% ground take asked for 6.6 times the height, produced an 80 m building,
    and no amount of trimming afterwards could bring it back.

    So the programme this holds is the lawful one: whichever is smaller, what the
    author drew or what the parcel allows.
    """

    if factor <= 1e-9:
        return 1.0
    inverse = 1.0 / (factor * factor)
    if far_capacity_m2 <= 0.0:
        return inverse
    current = _gross_floor_area(form, floor_height_m=floor_height_m)
    if current <= 1e-9:
        return inverse
    # After the plan scale the copy carries `current * factor^2`; the lift
    # multiplies that again.
    scaled = current * factor * factor
    if scaled <= 1e-9:
        return inverse
    return max(0.05, min(inverse, far_capacity_m2 / scaled))


def spread_across_coverage(
    form: MatrixForm,
    *,
    ground_capacity_m2: float,
    far_capacity_m2: float = 0.0,
    floor_height_m: float = 3.0,
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
        moved = retarget_ground_take(
            form,
            target_area_m2=target,
            far_capacity_m2=far_capacity_m2,
            floor_height_m=floor_height_m,
        )
        if moved is not None:
            out.append(replace(moved, name=f"{form.name}~{band.band_id}"))
    return out
