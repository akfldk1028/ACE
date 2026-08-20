"""Can this stand up. Asked of the geometry, not of the score.

Two measurements were reported as high-quality today and both were the same
mistake: `splayed_fan` came top of its cell on every number the sheet carries -
articulation 0.79, ground take 0.94, 용적률 0.98 - and reads as a collapsed deck
of cards leaning off a box. The critic named what the numbers could not, which
was that nothing holds the leaves up.

Adding a shape rule against that one drawing is how the last three rounds went:
"no volume more than 1.5x its neighbour" is a sentence about one symptom and
there is always another symptom. Physics is not like that. A cantilever has a
backspan or it does not; a body's centre of mass is over its support or it
falls. Those two questions are finite, they are the same two questions on every
parcel, and they are answerable from the band plans this compiler already has.

Mezghanni et al. (CVPR 2021) is the direct precedent and also the warning: they
measured a learned plausibility discriminator and a geometric-plausibility
function against physical stability and *both failed to predict it*, while an
explicit support-polygon computation succeeded. Geometric plausibility and
physical stability are not correlated. So this is computed, not scored.

The cantilever bound is a proportion rather than a dimension, and therefore
says the same thing on a 20 m parcel and a 200 m one. It is taken at the
generous end - what a storey-deep truss reaches, not what an ordinary beam
does - for the reason the span bound already states: this is here to refuse
the impossible, not to referee the ambitious. At the ordinary-beam value it
refused Milstein Hall and Seattle Central Library, both of which are built.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any, Iterable

from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import nearest_points, unary_union

from design.maas.source_geometry.ir import SourceMass


# A cantilever reaches about its own backspan and a half when it is designed
# as one and the member is a building, not a beam.
#
# This constant has now been raised twice by the same evidence, which is the
# tell worth recording. A third is the AISC rule of thumb for an ordinary
# beam, and at a third this gate refused Milstein Hall (~40%) and every VIA 57
# West and Seattle variant - refereeing the ambitious rather than refusing the
# impossible, the exact thing the span rule below says it is not for. Raised
# to a half. At a half it refused the VitraHaus pile: twelve gabled houses on
# five levels, cantilevered up to fifteen metres in the built work (Weil am
# Rhein, 2010), measuring ~1.45 of backspan in this gate's own band-wise
# terms, standing for sixteen years. MVRDV's Balancing Barn holds half its
# whole length in the air - ratio 1.0 as a counterweighted see-saw.
#
# A cantilever that far is a storey-deep truss rather than a beam, which is
# the same structure the span rule already takes the generous end for
# (SPAN_TO_DEPTH_RATIO below). 1.6 clears what is built and refuses what is
# not; the floating-slab case - nothing under a band at all - still refuses
# at infinity. The gates that judge whether the result is a building - it
# stands on something, a plate holds a room, a storey is lit - are unchanged.
CANTILEVER_BACKSPAN_RATIO = 1.6
# A member held at both ends is a span, and a storey-deep steel transfer truss
# runs to roughly ten to fifteen times its depth. The generous end is taken on
# purpose: this is here to refuse the impossible, not to referee the ambitious.
SPAN_TO_DEPTH_RATIO = 15.0
# Two volumes meeting at a shared edge are float-noise apart, not cantilevered.
_CONTACT_TOLERANCE_M = 0.05
# An overhang smaller than a floor tile is a modelling artefact of the band cut.
_MEANINGFUL_OVERHANG_M2 = 1.0

# How many bodies a scheme may stand as. One was the rule, and one is wrong: a
# 별동 - a detached annex holding the gym or the assembly hall - is one of the
# four ways Korean winners place a large span, and this gate refused every one
# of them. The grid has a `detached` column that could only ever be filled by
# schemes whose halves secretly touched.
#
# The bound was 4, from Kim (2026, SNU): 3.4 masses per Korean winning entry.
# That number is a fact about a jury, not about standing up - and applied as
# physics it refused the other canon wholesale: Moriyama House stands as ten
# boxes on one Tokyo parcel, Inujima scatters five pavilions, Nishinoyama is
# ten houses under twenty-one roofs, and every SANAA dispersal in the corpus
# came back "not one building" - 0 of 64 variants occupiable across the three
# sentences whose whole argument is separateness. The same evidence pattern
# that moved the cantilever constant: when the built canon trips the gate, the
# gate is wrong. How near a scheme sits to a jury's habits is the selection's
# question and `_piece_distance` already asks it on briefed runs; this gate
# keeps only the physical backstop at the canon's built extreme, past which
# the supply is rubble rather than a composition. Each body still answers
# every other question on its own.
MAX_SEPARATE_BODIES = 10


@dataclass(frozen=True)
class Standing:
    """What holds this mass up, and by how much."""

    grounded_share: float
    body_count: int
    cantilever_ratio: float
    cantilever_reach_m: float
    span_to_depth: float
    overturning_margin_m: float
    centre_of_mass_height_m: float
    potential_well_m: float
    reasons: tuple[str, ...]

    @property
    def stands(self) -> bool:
        return not self.reasons

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_structure.v1",
            "grounded_share": round(self.grounded_share, 3),
            "body_count": self.body_count,
            "cantilever_ratio": round(self.cantilever_ratio, 3),
            "cantilever_reach_m": round(self.cantilever_reach_m, 3),
            "cantilever_limit_ratio": round(CANTILEVER_BACKSPAN_RATIO, 3),
            "span_to_depth": round(self.span_to_depth, 3),
            "span_to_depth_limit": round(SPAN_TO_DEPTH_RATIO, 3),
            "overturning_margin_m": round(self.overturning_margin_m, 3),
            "centre_of_mass_height_m": round(self.centre_of_mass_height_m, 3),
            "potential_well_m": round(self.potential_well_m, 3),
            "stands": self.stands,
            "reasons": list(self.reasons),
            "basis": "AISC cantilever rule of thumb + Mezghanni CVPR 2021 support polygon",
        }


def _polygons(shape) -> list[Polygon]:
    if shape is None or shape.is_empty:
        return []
    if isinstance(shape, Polygon):
        return [shape]
    if isinstance(shape, MultiPolygon):
        return [item for item in shape.geoms if isinstance(item, Polygon)]
    return [item for item in getattr(shape, "geoms", ()) if isinstance(item, Polygon)]


def bands_of(source: SourceMass) -> list[tuple[float, float, Polygon]]:
    """One plan per height band, lowest first.

    A band arrives as several volume records when it is in pieces - two bars
    with a gap between them. They are one storey and have to be unioned before
    anything is asked about support, or each bar reports itself unsupported by
    the other bar it was never sitting on.
    """

    grouped: dict[tuple[float, float], list[Polygon]] = {}
    for volume in source.volumes:
        key = (round(float(volume.bottom_fraction), 4), round(float(volume.top_fraction), 4))
        grouped.setdefault(key, []).append(volume.footprint)
    out: list[tuple[float, float, Polygon]] = []
    for (low, high), parts in sorted(grouped.items()):
        shape = parts[0] if len(parts) == 1 else unary_union(parts)
        merged = _polygons(shape)
        if merged:
            out.append((low, high, shape if isinstance(shape, Polygon) else unary_union(merged)))
    return out


def _extent_along(shape, direction: tuple[float, float]) -> float:
    """How far a plan reaches along one axis - the backspan, once aimed."""

    ux, uy = direction
    values = [
        x * ux + y * uy
        for polygon in _polygons(shape)
        for x, y in polygon.exterior.coords
    ]
    return max(values) - min(values) if values else 0.0


def worst_members(source: SourceMass, *, height_m: float) -> tuple[float, float, float]:
    """Grade every unsupported piece as the member it actually is.

    Support is the band directly below, not everything below: load runs down
    through what a thing is standing on, and a plate two storeys up is not held
    by a plinth it does not touch.

    Then the piece is asked how it is held, because there are two answers and
    one rule cannot cover both. A piece touching its support in one place is a
    cantilever and obeys the third-of-the-backspan rule. A piece touching in two
    separated places is a span - the CCTV building, a bar bridging two towers -
    and it obeys a span-to-depth rule instead. Applying the cantilever rule to
    both is what threw out every bridge in the vocabulary on the first run:
    `loop_bridge` was graded as reaching 3.4 times its backspan when in truth
    both its ends were standing on something.

    The reach is measured from the point of the overhang furthest from its
    support and the backspan along that same direction, so a bar cantilevering
    off its short end and one cantilevering off its long end are told apart -
    which an area ratio cannot do.

    Returns (worst cantilever ratio, its reach in metres, worst span-to-depth).
    """

    bands = bands_of(source)
    worst_ratio = 0.0
    worst_reach = 0.0
    worst_slenderness = 0.0
    for index in range(1, len(bands)):
        low, high, plan = bands[index]
        support = bands[index - 1][2]
        if plan.is_empty or support.is_empty:
            continue
        overhang = plan.difference(support.buffer(_CONTACT_TOLERANCE_M))
        for piece in _polygons(overhang):
            if float(piece.area) < _MEANINGFUL_OVERHANG_M2:
                continue
            contacts = _polygons(
                piece.buffer(_CONTACT_TOLERANCE_M * 2.0).intersection(support)
            )
            if len(contacts) >= 2:
                depth = max(0.0, high - low) * height_m
                slenderness = _span_to_depth(piece, contacts, depth)
                worst_slenderness = max(worst_slenderness, slenderness)
                continue
            tip = max(
                (Point(point) for point in piece.exterior.coords),
                key=lambda point: point.distance(support),
            )
            reach = float(tip.distance(support))
            if reach <= 1e-6:
                continue
            root, _ = nearest_points(support, tip)
            dx, dy = tip.x - root.x, tip.y - root.y
            length = hypot(dx, dy)
            if length <= 1e-9:
                continue
            direction = (dx / length, dy / length)
            carried = plan.intersection(support)
            backspan = _extent_along(carried, direction)
            if backspan <= 1e-6:
                # Nothing of this band sits on the one below: it is not a
                # cantilever at all, it is a floating slab.
                return float("inf"), reach, worst_slenderness
            ratio = reach / backspan
            if ratio > worst_ratio:
                worst_ratio, worst_reach = ratio, reach
    return worst_ratio, worst_reach, worst_slenderness


def _span_to_depth(piece: Polygon, contacts: list[Polygon], depth_m: float) -> float:
    """How far a member reaches BETWEEN supports, for the depth it is given.

    Along the line joining the two largest things holding it up - which is the
    direction the span is actually in, whatever orientation the bar was drawn
    at. The span is the largest CLEAR opening between neighbouring supports,
    not the member's whole length: measured end to end, a canopy resting on
    ten houses read as one forty-metre span and Nishinoyama's tie - lanes of
    three to six metres between dwellings - was refused as a transfer fantasy
    it never was. A continuous plate over many supports is many short spans;
    a plate that really has only two supports forty metres apart still reads
    forty. A band with no thickness cannot span at all, so it returns an
    infinite slenderness rather than dividing by zero.
    """

    largest = sorted(contacts, key=lambda item: float(item.area), reverse=True)[:2]
    first, second = largest[0].centroid, largest[1].centroid
    dx, dy = second.x - first.x, second.y - first.y
    length = hypot(dx, dy)
    if length <= 1e-9:
        return 0.0
    direction = (dx / length, dy / length)
    if depth_m <= 1e-6:
        return float("inf")
    # Every support as an interval along the span line, then the widest gap
    # between neighbouring intervals is the clear span.
    intervals = []
    for contact in contacts:
        values = [
            x * direction[0] + y * direction[1]
            for x, y in contact.exterior.coords
        ]
        intervals.append((min(values), max(values)))
    intervals.sort()
    span = 0.0
    reach = intervals[0][1]
    for lo, hi in intervals[1:]:
        span = max(span, lo - reach)
        reach = max(reach, hi)
    return max(span, 0.0) / depth_m


def centre_of_mass(source: SourceMass, *, height_m: float) -> tuple[float, float, float]:
    """Volume-weighted centre of the built bands, in site-local metres."""

    total = 0.0
    sum_x = sum_y = sum_z = 0.0
    for low, high, plan in bands_of(source):
        thickness = max(0.0, high - low) * height_m
        weight = float(plan.area) * thickness
        if weight <= 1e-9:
            continue
        centre = plan.centroid
        total += weight
        sum_x += weight * float(centre.x)
        sum_y += weight * float(centre.y)
        sum_z += weight * ((low + high) / 2.0 * height_m)
    if total <= 1e-9:
        return 0.0, 0.0, 0.0
    return sum_x / total, sum_y / total, sum_z / total


def support_polygon(source: SourceMass) -> Polygon | None:
    """What the building stands on: the convex hull of its ground contacts.

    The hull, not the union, and the difference is the whole check. A table
    stands because its centre of mass is between its legs, not over one of
    them; measured against the union of the legs every table in the world falls
    over. Measured that way here, a pair of splayed bars - two grounded volumes
    with a courtyard between them - reported its centre of mass 2.6 m outside
    its own support and was thrown out as unbuildable.

    The convex hull of the contact region is the textbook support polygon and
    the one Mezghanni computes. A body tips when the vertical through its centre
    of mass leaves that hull, because that is when the reaction can no longer be
    balanced anywhere on the ground it touches.
    """

    grounded = [plan for low, _high, plan in bands_of(source) if low <= 1e-6]
    if not grounded:
        return None
    shape = grounded[0] if len(grounded) == 1 else unary_union(grounded)
    if shape.is_empty:
        return None
    hull = shape.convex_hull
    return hull if isinstance(hull, Polygon) and not hull.is_empty else None



def band_parts(source: SourceMass) -> list[tuple[float, float, Polygon]]:
    """Every plan piece with its own band, kept separate.

    `bands_of` unions a band's pieces because the questions it answers are about
    the storey. Connectivity is about the pieces: two bars with a gap between
    them are one band and two things, and unioning them first is what let a
    composition of separated fragments read as a single connected body.
    """

    out: list[tuple[float, float, Polygon]] = []
    for volume in source.volumes:
        piece = volume.footprint
        if piece is None or piece.is_empty:
            continue
        out.append(
            (round(float(volume.bottom_fraction), 4), round(float(volume.top_fraction), 4), piece)
        )
    return sorted(out, key=lambda item: (item[0], item[1]))


def _touching(a: tuple[float, float, Polygon], b: tuple[float, float, Polygon]) -> bool:
    """Do these two pieces share material - overlapping in plan and in height."""

    a_low, a_high, a_plan = a
    b_low, b_high, b_plan = b
    if min(a_high, b_high) < max(a_low, b_low) - 1e-9:
        return False
    if a_plan.is_empty or b_plan.is_empty:
        return False
    contact = a_plan.buffer(_CONTACT_TOLERANCE_M).intersection(b_plan)
    return not contact.is_empty and float(contact.area) > _MEANINGFUL_OVERHANG_M2


def connectivity(source: SourceMass) -> tuple[float, int]:
    """Share of the mass with a load path to the ground, and how many bodies.

    Neither question was being asked, and both are the difference between a
    building and a picture of blocks. The overturning check uses the convex hull
    of the ground contacts - which is right, a table stands between its legs -
    and that is exactly why a cloud of separated fragments passed it: their hull
    is generous and none of them is holding another up.

    A piece is grounded when it sits on the ground or touches a grounded piece.
    Touching means overlapping in plan *and* in height, so a block hovering
    above another block is not resting on it.

    Returns (share of floor area with a path down, number of separate bodies).
    """

    pieces = band_parts(source)
    if not pieces:
        return 0.0, 0

    ground = min(low for low, _high, _plan in pieces)
    reached = {
        index for index, (low, _high, _plan) in enumerate(pieces) if low <= ground + 1e-6
    }
    frontier = list(reached)
    while frontier:
        current = frontier.pop()
        for index, piece in enumerate(pieces):
            if index in reached:
                continue
            if _touching(pieces[current], piece):
                reached.add(index)
                frontier.append(index)

    total = sum(float(plan.area) for _low, _high, plan in pieces)
    held = sum(float(pieces[i][2].area) for i in reached)

    # Separate bodies: the same touching relation, without starting from the
    # ground. Two wings that never meet are two buildings on one parcel.
    seen: set[int] = set()
    bodies = 0
    for start in range(len(pieces)):
        if start in seen:
            continue
        bodies += 1
        stack = [start]
        seen.add(start)
        while stack:
            current = stack.pop()
            for index, piece in enumerate(pieces):
                if index in seen:
                    continue
                if _touching(pieces[current], piece):
                    seen.add(index)
                    stack.append(index)

    return (held / total if total > 1e-9 else 0.0), bodies


def assess_standing(source: SourceMass, *, height_m: float) -> Standing:
    """Two physical questions, asked of the compiled bands."""

    reasons: list[str] = []

    # Asked first, because the other three assume there is one body to ask about.
    grounded, bodies = connectivity(source)
    if grounded < 1.0 - 1e-6:
        reasons.append(f"only_{grounded:.0%}_of_the_mass_reaches_the_ground")
    if bodies > MAX_SEPARATE_BODIES:
        reasons.append(f"{bodies}_separate_bodies_not_one_building")

    ratio, reach, slenderness = worst_members(source, height_m=height_m)
    if ratio > CANTILEVER_BACKSPAN_RATIO:
        label = "unsupported" if ratio == float("inf") else f"{ratio:.2f}"
        reasons.append(f"cantilever_{label}_of_backspan_over_{CANTILEVER_BACKSPAN_RATIO:.2f}")
    if slenderness > SPAN_TO_DEPTH_RATIO:
        reasons.append(f"span_{slenderness:.0f}x_its_depth_over_{SPAN_TO_DEPTH_RATIO:.0f}")

    support = support_polygon(source)
    x, y, z = centre_of_mass(source, height_m=height_m)
    if support is None:
        margin = 0.0
        reasons.append("nothing_touches_the_ground")
    else:
        point = Point(x, y)
        distance = float(point.distance(support.boundary))
        margin = distance if support.contains(point) else -distance
        if margin <= 0.0:
            reasons.append(f"centre_of_mass_{-margin:.1f}m_outside_support")

    return Standing(
        grounded_share=grounded,
        body_count=bodies,
        cantilever_ratio=ratio,
        cantilever_reach_m=reach,
        span_to_depth=slenderness,
        overturning_margin_m=margin,
        centre_of_mass_height_m=z,
        # Mezghanni's potential well: how far the centre of mass can travel
        # before it leaves the support, against how far it would fall.
        potential_well_m=margin - z,
        reasons=tuple(reasons),
    )


__all__ = [
    "CANTILEVER_BACKSPAN_RATIO",
    "band_parts",
    "connectivity",
    "SPAN_TO_DEPTH_RATIO",
    "Standing",
    "assess_standing",
    "bands_of",
    "centre_of_mass",
    "support_polygon",
    "worst_members",
]
