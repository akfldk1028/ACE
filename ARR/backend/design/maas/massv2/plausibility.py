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

from math import hypot

from dataclasses import dataclass
from typing import Any

from design.maas.floor_viability import (
    DEFAULT_MINIMUM_CLEAR_DEPTH_M,
    evaluate_floor_section_viability,
    minimum_usable_floor_area_m2,
)
from design.maas.source_geometry.ir import SourceMass

from .structure import Standing, assess_standing


AUTHORED_MINIMUM_PLAN_DIMENSION_M = 1.5

# How much of a plate must survive being eroded by the project's own minimum
# room depth before it stops being a storey somebody occupies.
#
# `floor_viability` erodes by half that depth, which asks whether one room fits
# and is the right question when the subject is a room. A storey is not one
# room: whatever is on it has to be reached, and the way up is a room too. So
# the same number is spent twice rather than halved, and the plate has to be
# wide enough to hold a room with something else beside it.
#
# This is the `lift` clearance lesson a second time. Every other magnitude in
# this grammar is a ratio because the building's own proportions set it; these
# are metres because a person sets them, and a person is the same size on every
# site. The measured consequence of not having it: on 강남 역삼 the parcel's own
# slenderness limit comes out at 16.25, so 4.2 m x 65 m sticks were lawful,
# stood up, were fully daylit, held a 2.4 m room - and went out as alternatives.
MINIMUM_STOREY_WIDTH_M = DEFAULT_MINIMUM_CLEAR_DEPTH_M

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

# Which uses Korean law actually asks a daylight question about.
#
# 건축법 시행령 제51조(거실의 채광 등): "단독주택 및 공동주택의 거실, 교육연구시설 중
# 학교의 교실, 의료시설의 병실 및 숙박시설의 객실". That list is the whole of it -
# 근린생활시설, 업무시설 and 판매시설 are not in it, and this tool was rejecting a
# 제1종근린생활시설 on a rule written for a dwelling. 297 of 533 refusals on the
# Uijeongbu parcel were that rule alone, more than half of everything refused.
#
# Two further things the statute says, which is why even the covered uses are not
# gated on plate depth here. The duty is a per-거실 window area - 피난·방화규칙
# 제17조①, "그 거실의 바닥면적의 10분의 1 이상" - not a distance from a façade, and
# it binds rooms rather than plates, so a deep plate whose core is 복도·창고·설비
# (not 거실, 건축법 제2조제1항제6호) is untouched by it. And it is defeasible: the
# same article exempts a 거실 lit to 별표 1의3 by lamps.
#
# No Korean provision anywhere limits how far a floor may extend from a window.
# The only statutory plan-depth number is egress - 시행령 제34조①, 보행거리 30 m,
# 50 m for 내화구조·불연재료 - and that one is use-blind. If this package ever wants
# one depth gate for every use, that is the number, and 6 m is not it.
#
# 정북일조 is the other half of the same question and is not affected: 법 제61조①
# triggers on 용도지역 (전용주거·일반주거) and says nothing about the building's use,
# so a 근린생활시설 there obeys it like anything else. It is enforced in `legal_fit`
# through the envelope, not here.
DAYLIGHT_IS_A_DUTY_FOR = (
    "단독주택", "공동주택", "학교", "병원", "의료시설", "숙박시설",
)


def daylight_is_required_for(building_type: str) -> bool:
    """Does 영 제51조 ask this use for daylight at all."""

    name = str(building_type or "")
    return any(token in name for token in DAYLIGHT_IS_A_DUTY_FOR)


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


def holds_a_storey(polygon) -> bool:
    """Could a room and the way to it stand side by side across this plate.

    Eroding by the minimum room depth leaves the points that have that much
    clearance on every side, so anything surviving has room for a second thing
    beside the first. It is the same morphological test `unlit_share` uses,
    asked in the other direction: that one finds the part of a plate no window
    reaches, this one finds whether the plate is a plate at all.
    """

    if polygon is None or polygon.is_empty:
        return False
    try:
        return not polygon.buffer(-MINIMUM_STOREY_WIDTH_M, join_style=2).is_empty
    except Exception:  # pragma: no cover - GEOS refusing a degenerate erosion
        return False


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
    occupiable_mass_share: float = 1.0
    standing: Standing | None = None
    max_slenderness: float = 0.0

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_plausibility.v1",
            "slenderness": round(self.slenderness, 3),
            "minimum_plan_dimension_m": round(self.minimum_plan_dimension_m, 3),
            "viable_band_share": round(self.viable_band_share, 3),
            "occupiable_mass_share": round(self.occupiable_mass_share, 3),
            "occupiable": self.occupiable,
            "reasons": list(self.reasons),
            "structure": self.standing.evidence() if self.standing is not None else None,
            "max_slenderness": round(self.max_slenderness, 2),
            "basis": "design.maas.floor_viability + parcel slenderness + structure",
        }


def _min_dimension(polygon) -> float:
    """How narrow this plan is across its own narrowest direction.

    On its own axes, not the world's. Every volume here is posed at the parcel's
    bearing and an axis-aligned box around a turned shape is wider than the
    shape - a 3 x 40 m bar reads 13.3 m across at 15 degrees, 30.4 m at 45. The
    three live parcels sit at -168.3, 35.5 and 165.0 degrees, so against a
    1.5 m floor this test could not fire on any of them.
    """

    if polygon is None or polygon.is_empty:
        return 0.0
    ring = list(polygon.minimum_rotated_rectangle.exterior.coords)[:4]
    if len(ring) < 3:
        min_x, min_y, max_x, max_y = polygon.bounds
        return float(min(max_x - min_x, max_y - min_y))
    # Adjacent edges. Sorting three of them takes the long one twice whenever
    # the ring starts on a short side - the fault `seed_rectangle` and
    # `principal_axes` both carried.
    sides = [
        hypot(ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1])
        for i in range(2)
    ]
    return float(min(sides))


def assess(
    source: SourceMass,
    *,
    parcel_area_m2: float,
    max_slenderness: float,
    floor_height_m: float = 0.0,
    building_type: str = "",
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

    structural = set(source.metadata.get("structural_bands") or ())
    viable = 0.0
    counted = 0.0
    room = 0.0
    occupied = 0.0
    holding = 0.0
    for index, volume in enumerate(bands):
        # A support is not asked to be a floor. The exemption is already granted
        # two rules below - a column is small next to what it holds up, and that
        # is what makes it a column - and it was missing here, so the thinner the
        # legs the worse the building scored. Counted rather than weighed, too:
        # four slim legs are four bands against one plate, so `lift` could only
        # ever stand a slab on stumps thick enough to read as blocks under it.
        # Both judges of the fixed benchmark said the same thing about Maison
        # Bordeaux - "nothing floats", "it plainly rests on the tier below" -
        # and the geometry had a 3.4 m gap in it the whole time.
        #
        # Same correction the storey rule already carries: weigh by how much
        # building each band is.
        if index in structural:
            continue
        verdict = evaluate_floor_section_viability(
            volume.footprint, parcel_area_m2=parcel_area_m2
        )
        weight = float(volume.footprint.area) * max(
            0.0, volume.top_fraction - volume.bottom_fraction
        )
        counted += weight
        if verdict.get("hard_pass"):
            viable += weight
        # Weighed by how much building each band is, not counted. Counting made
        # one thin terrace among Mountain Dwellings' thirteen bands worth as
        # much as the forty-metre plates beside it, and refused the scheme.
        bulk = float(volume.footprint.area) * max(
            0.0, volume.top_fraction - volume.bottom_fraction
        )
        if index in structural:
            holding += bulk
            continue
        occupied += bulk
        if holds_a_storey(volume.footprint):
            room += bulk
    share = (viable / counted) if counted > 1e-9 else 1.0
    storey_share = (room / occupied) if occupied > 1e-9 else 1.0
    held_share = holding / max(holding + occupied, 1e-9)

    reasons: list[str] = []
    if slenderness > max_slenderness:
        reasons.append(f"slenderness_{slenderness:.1f}_over_{max_slenderness:.1f}")
    if min_dimension < AUTHORED_MINIMUM_PLAN_DIMENSION_M:
        reasons.append(f"plan_dimension_{min_dimension:.1f}m_under_minimum")
    if float(ground.area) < minimum_usable_floor_area_m2(parcel_area_m2):
        reasons.append("ground_floor_below_minimum_usable_area")
    if share <= 0.5:
        reasons.append(f"only_{share:.0%}_of_bands_occupiable")
    # Every plate, not the ground alone. A mass may sit on a generous footprint
    # and taper into sticks above it, and `min_dimension` reads the ground only
    # - and reads a bounding box at that, so it cannot see a stick beside a
    # wide plate in the same band.
    if storey_share <= 0.5:
        reasons.append(f"only_{storey_share:.0%}_of_the_mass_is_wide_enough_to_occupy")
    # A column is exempt from being as wide as a storey because it is a column,
    # and what makes it one is that it is small next to what it holds up. The
    # exemption is granted by the verb - `lift` marks its supports - and nothing
    # re-examined it afterwards, so on 강남 the growth loop drew those supports
    # to 65 m and they carried the exemption all the way out: Rolex reported
    # every occupiable band wide enough because the four sticks it stands on had
    # stopped counting. Past half the mass it is not what holds the building up,
    # it is the building.
    if held_share > 0.5:
        reasons.append(f"{held_share:.0%}_of_the_mass_is_structure_rather_than_room")

    # A plate can satisfy both ceilings and still have a middle no window
    # reaches. Nothing else in this gate was asking how deep a storey is, so a
    # forty-metre-across slab passed as readily as a bar - and on a wide parcel
    # the growth loop makes exactly that, because filling 용적률 by spreading
    # is cheaper than by rising. This is the reason a courtyard block, a bar
    # and a comb exist at all, and it belongs at the gate rather than in the
    # score for the same reason standing up does.
    if floor_height_m > 0.0 and daylight_is_required_for(building_type):
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
        occupiable_mass_share=storey_share,
        occupiable=not reasons,
        reasons=tuple(reasons),
        standing=standing,
        max_slenderness=max_slenderness,
    )
