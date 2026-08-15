"""Is this a building, or is it lawful geometry that nobody could occupy.

Both ceilings can be satisfied by a chimney. Measured on the live Uijeongbu
parcel, carrying a four-block composition down to a 45% ground take produced a
21 m2 footprint under 48 m of height - a slenderness of 10.4, entirely lawful
and not a 근린생활시설 anyone would propose. Eleven of eighty-eight schemes came
out past a slenderness of 4.

Nothing here invents a threshold. Floor viability comes from the project's own
shared rule in `design/maas/floor_viability.py`, which derives a minimum
occupied area from the parcel and holds a room to a 2.4 m clear depth, and the
slenderness bound comes from the parcel too - see `slenderness_limit`, which
reuses the 용적률-over-건폐율 storey count that already stops growth in `fill`.
Using the rules the project already lives by is the point: a second set of
numbers would be a second opinion about the same question.

Standing up is asked here too, by `structure`. It belongs at this gate rather
than in the fitness score for the reason the score itself demonstrated: the
scheme the critic called a collapsed deck of cards came *first* on every number
the sheet carries. A mass that cannot be held up is not a low-scoring option,
it is not an option, and a gate is the only place that distinction exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from design.maas.floor_viability import (
    evaluate_floor_section_viability,
    minimum_usable_floor_area_m2,
)
from design.maas.source_geometry.ir import SourceMass

from .structure import Standing, assess_standing


AUTHORED_MINIMUM_PLAN_DIMENSION_M = 1.5

# How far daylight reaches into a storey, as a multiple of its own height.
# Reinhart's rule of thumb puts the daylit zone at two to two and a half times
# the window head; in a storey of this height the head lands just under the
# ceiling, so the storey height is the dimension to scale from and the lower
# end of the range is the one to take. At 3 m that is 6 m from a façade, and a
# plate lit from both sides may be twelve across - which is the depth every
# daylit bar in the corpus is built to.
DAYLIT_DEPTH_PER_STOREY = 2.0

# How much of a plate may sit past daylight before it stops being a storey
# somebody occupies. A core, its stairs and back-of-house belong in the dark
# and run to about a fifth of a plate this size, so a quarter is the share
# above which the dark is no longer the servant space.
#
# Measured rather than guessed at: for a square plate the unlit share is
# ((s-12)/s)², so a half would only have refused something past 41 m across -
# on this parcel, nothing. A quarter refuses anything past 24 m square, and
# passes a 14 m bar of any length (0.11) and a courtyard block of the same
# outline as the slab it refuses (0.00), which is the distinction the rule
# exists to make.
MAX_UNLIT_SHARE = 0.25


def daylit_depth_m(floor_height_m: float) -> float:
    """How far in from a façade or a court a storey of this height is lit."""

    return DAYLIT_DEPTH_PER_STOREY * max(float(floor_height_m), 0.0)


def unlit_share(polygon, *, floor_height_m: float) -> float:
    """The part of a plate no window reaches, as a share of its own area.

    Eroding the plan by the daylit depth leaves exactly the points that are
    further than that from any edge - the same morphological test the void axis
    uses to ask whether a gap could be a room, asked here in the other
    direction. Courts count as edges because they are: `footprint` carries its
    interiors, so a courtyard block reads as lit and a solid one of the same
    outline does not, which is the whole reason a courtyard block exists.
    """

    area = float(polygon.area)
    if area <= 1e-9:
        return 0.0
    depth = daylit_depth_m(floor_height_m)
    if depth <= 0.0:
        return 0.0
    try:
        core = polygon.buffer(-depth)
    except Exception:  # pragma: no cover - GEOS refusing a degenerate erosion
        return 0.0
    return float(core.area) / area if not core.is_empty else 0.0


def slenderness_limit(*, far_capacity_m2: float, ground_capacity_m2: float) -> float:
    """How slender this parcel's own two limits say a building may be.

    The number used to be 12, quoted from `_is_reviewable_architectural_mass`
    in the other pipeline. Quoting was the right instinct and the wrong source:
    that gate judges authored masses on any site, and here it let through the
    exact case this module was written to refuse - the docstring above names a
    chimney at 10.4 as "not a 근린생활시설 anyone would propose" and then passed
    it. A limit that admits its own counterexample is not a limit.

    So it comes from the parcel, and from the number that already governs the
    other half of the same question: 용적률 divided by 건폐율 is how many storeys
    the parcel affords over the ground it allows, and `fill` already stops
    growth there. A building slenderer than the storeys its own site affords
    has stopped taking less ground and started going up instead.

    It travels correctly, which the constant did not. Uijeongbu at 20% and 100%
    affords 5, so a stick is refused. A commercial parcel at 60% and 800%
    affords 13.3, and there a slender tower is what the zoning is for. The same
    sentence gives the right answer on both because it is the site talking.
    """

    return max(1.0, float(far_capacity_m2) / max(float(ground_capacity_m2), 1e-9))


@dataclass(frozen=True)
class Plausibility:
    slenderness: float
    minimum_plan_dimension_m: float
    viable_band_share: float
    occupiable: bool
    reasons: tuple[str, ...]
    standing: Standing | None = None
    max_slenderness: float = 0.0

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_plausibility.v1",
            "slenderness": round(self.slenderness, 3),
            "minimum_plan_dimension_m": round(self.minimum_plan_dimension_m, 3),
            "viable_band_share": round(self.viable_band_share, 3),
            "occupiable": self.occupiable,
            "reasons": list(self.reasons),
            "structure": self.standing.evidence() if self.standing is not None else None,
            "max_slenderness": round(self.max_slenderness, 2),
            "basis": "design.maas.floor_viability + parcel slenderness + structure",
        }


def _min_dimension(polygon) -> float:
    min_x, min_y, max_x, max_y = polygon.bounds
    return float(min(max_x - min_x, max_y - min_y))


def assess(
    source: SourceMass,
    *,
    parcel_area_m2: float,
    max_slenderness: float,
    floor_height_m: float = 0.0,
) -> Plausibility:
    """Judge a compiled mass as a building rather than as a solid.

    `max_slenderness` is the parcel's own, from `slenderness_limit`. It has no
    default on purpose: the version with one was a constant that travelled to
    every site unchanged and let a chimney through on this one.
    """

    bands = tuple(source.volumes)
    if not bands:
        return Plausibility(0.0, 0.0, 0.0, False, ("no_bands",))

    height = float(source.metadata.get("authored_height_m") or 0.0)
    ground = source.footprint
    min_dimension = _min_dimension(ground)
    slenderness = height / min_dimension if min_dimension > 1e-6 else float("inf")

    viable = 0
    for volume in bands:
        verdict = evaluate_floor_section_viability(
            volume.footprint, parcel_area_m2=parcel_area_m2
        )
        if verdict.get("hard_pass"):
            viable += 1
    share = viable / len(bands)

    reasons: list[str] = []
    if slenderness > max_slenderness:
        reasons.append(f"slenderness_{slenderness:.1f}_over_{max_slenderness:.1f}")
    if min_dimension < AUTHORED_MINIMUM_PLAN_DIMENSION_M:
        reasons.append(f"plan_dimension_{min_dimension:.1f}m_under_minimum")
    if float(ground.area) < minimum_usable_floor_area_m2(parcel_area_m2):
        reasons.append("ground_floor_below_minimum_usable_area")
    if share <= 0.5:
        reasons.append(f"only_{share:.0%}_of_bands_occupiable")

    # A plate can satisfy both ceilings and still have a middle no window
    # reaches. Nothing else in this gate was asking how deep a storey is, so a
    # forty-metre-across slab passed as readily as a bar - and on a wide parcel
    # the growth loop makes exactly that, because filling 용적률 by spreading
    # is cheaper than by rising. This is the reason a courtyard block, a bar
    # and a comb exist at all, and it belongs at the gate rather than in the
    # score for the same reason standing up does.
    if floor_height_m > 0.0:
        dark = max(
            (unlit_share(volume.footprint, floor_height_m=floor_height_m)
             for volume in bands),
            default=0.0,
        )
        if dark > MAX_UNLIT_SHARE:
            reasons.append(f"{dark:.0%}_of_a_plate_is_past_daylight")

    standing = assess_standing(source, height_m=height)
    reasons.extend(standing.reasons)

    return Plausibility(
        slenderness=slenderness,
        minimum_plan_dimension_m=min_dimension,
        viable_band_share=share,
        occupiable=not reasons,
        reasons=tuple(reasons),
        standing=standing,
        max_slenderness=max_slenderness,
    )
