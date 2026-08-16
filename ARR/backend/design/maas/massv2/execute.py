"""Apply a parti to a site and get placed volumes.

The executor owns the metres. An author writes "stack three, shear toward the
open side, carve a court to the south" and never states a dimension, because
every dimension here is either the parcel's or a ratio the corpus fixes. That
split is the whole point of the grammar: the author supplies the sentence, and
the sentence is about this site; the executor supplies the syntax, and the
syntax is the same everywhere.

Which is why nothing here can be tuned into a house style. The offsets are
0.15-0.35 of the volume's own dimension because below that an offset reads as
a setting-out error and above it the volume stops reading as displaced. Tiers
contrast because three offices whose work looks nothing alike never once built
a mass of equal blocks. Volumes hold a joint instead of merging because that is
how two enclosures meet. What differs between two runs is which operations were
chosen and what they were aimed at, and both of those come from the parcel.
"""

from __future__ import annotations

from dataclasses import replace
from math import ceil, sqrt
from typing import Any

from shapely.geometry import Polygon

from design.maas.floor_viability import DEFAULT_MINIMUM_CLEAR_DEPTH_M

from .form import MatrixForm, Placement, place, stack
from .profiles import plan_names
from .grammar import (
    JOINT_CLEARANCE_M,
    MAX_OFFSET_RATIO,
    MIN_OFFSET_RATIO,
    MIN_TIER_CONTRAST,
    Operation,
    Parti,
    seed_rectangle,
)


def _clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


# How many volumes a field may hold. Six was a hardcoded table of corner slots
# and it was the ceiling on grade articulation for the entire grammar, because
# `split` divides a field rather than multiplying it. Korean competition winners
# average 3.4 separate masses, which six could reach; Moriyama's ten, Towada's
# one-per-artwork and Nishinoyama's ten dwellings could not be said at all.
MAX_FIELD_OBJECTS = 12

# How much the objects in a field may differ in size. The floor used to be
# MIN_TIER_CONTRAST, the same rule that stops `stack` making a barracks of equal
# tiers - but Nishizawa rejected volumes that were *identical*, not volumes that
# were *similar*, and at Moriyama and Towada the near-equality is the content:
# it is what makes the result read as a neighbourhood rather than as a house
# with outbuildings. Equal is still refused; close is now allowed.
MIN_FIELD_SPREAD = 1.05

# How tall an undercroft may be, in storeys of the building it belongs to.
# The corpus lifts to let the ground run under a building, not to stand it on
# towers: Rolex, Zollverein, Grace Farms and Kaktus all clear a storey or two.
# This is the ceiling that matches the floor `_lift` already had, and both are
# metres for the same reason - the person walking under is the same size on
# every site.
MAX_UNDERCROFT_STOREYS = 2.0


class _Frame:
    """The site's own box, and the volumes standing in it so far."""

    def __init__(
        self,
        buildable: Polygon,
        axis: tuple[float, float],
        height_m: float,
        storey_m: float = 0.0,
    ):
        cx, cy, width, depth, rotation = seed_rectangle(buildable, axis)
        self.cx, self.cy = cx, cy
        self.width, self.depth = width, depth
        self.rotation = rotation
        self.height = height_m
        # A room is at least a storey. Heights in a sentence are ratios of the
        # whole, and an author writing about a single-storey building writes a
        # small one - Louvre-Lens at 0.15 - which on a parcel affording four
        # storeys is 1.9 m, and after `aggregate` thins its later objects, 0.86.
        # That is a kerb, not a room: the diff check reported a `taper` aimed at
        # one of them as changing the mass by exactly 0.000.
        self.storey = max(0.0, storey_m)
        # The base shape this composition is made of, set once by the sentence.
        # A profile is a property of the building, not of one operation: a
        # circular museum is circular in every volume it is cut into.
        self.profile = "square"
        self.placements: list[Placement] = []

    def box(
        self,
        role: str,
        *,
        w: float,
        d: float,
        z: float,
        h: float,
        dx: float = 0.0,
        dy: float = 0.0,
        kind: str = "additive",
        plan: str = "",
        occupiable: bool = True,
    ) -> Placement:
        """A volume centred on the site frame, offset in the frame's own axes.

        `occupiable` is what separates a room from a piece of structure. A
        support under a lifted plate is allowed to be shorter than a storey
        because nobody stands in it; anything else is not.

        `plan` is the base shape, and defaults to whatever the sentence set for
        this composition rather than to the square. Ten of them are built
        (`profiles.plan_names`) and the grammar used one: measured across the
        forty-eight authored sentences, 302 of 302 placements were square. A
        matrix cannot turn a square into a circle, so a sentence with no way to
        name the shape has no way to say Kanazawa's 112.5 m circle or Casa da
        Música's faceted solid - and both of those came out as a `taper`, which
        is why that verb was carrying work it could never do.
        """

        least = self.storey if occupiable and kind == "additive" else 0.5
        plan = plan or self.profile
        return place(
            role,
            size=(max(w, 0.5), max(d, 0.5), max(h, least, 0.5)),
            at=(self.cx + dx - w / 2.0, self.cy + dy - d / 2.0, z),
            rotation_degrees=self.rotation,
            kind=kind,
            plan=plan,
            occupiable=occupiable,
        )


def _direction(frame: _Frame, toward: Any) -> tuple[float, float]:
    """Which way a move is aimed, in the frame's own axes.

    Named rather than numeric, because direction is the programmatic half of a
    move - the author says "toward the open side" and means the street, not an
    angle. Anything unrecognised aims along the site's length, which is the one
    direction every parcel has.
    """

    name = str(toward or "long").lower()
    if name in ("cross", "short", "side"):
        return (0.0, 1.0)
    if name in ("back", "away", "off_open"):
        return (-1.0, 0.0)
    return (1.0, 0.0)


def _scope(frame: _Frame, op: Operation) -> tuple[list[Placement], list[Placement]]:
    """Split what is standing into what this operation acts on, and the rest.

    Without this every verb reached everything, and a grammar whose verbs all
    have the same scope is barely a grammar - stack then shear then carve gives
    one family however the words are ordered, because each word sees the whole
    building. The combinations collapse into their union.

    `on` is matched as a prefix of the volume's role, so `on: "west"` catches
    `west`, `west_tier_0` and anything split out of them. Naming a part that is
    not there does nothing rather than falling back to everything: an operation
    aimed at a wing the scheme never grew should be silent, not global.
    """

    prefix = str(op.params.get("on") or "").strip()
    if not prefix:
        return list(frame.placements), []
    picked = [item for item in frame.placements if item.role.startswith(prefix)]
    rest = [item for item in frame.placements if not item.role.startswith(prefix)]
    return picked, rest


def _bounds_of(items: list[Placement]) -> tuple[float, float, float, float]:
    """Centre and span in plan of a set of volumes, in the site frame."""

    corners = [corner for item in items for corner in item.corners()]
    xs = [x for x, _y, _z in corners]
    ys = [y for _x, y, _z in corners]
    return (
        (min(xs) + max(xs)) / 2.0,
        (min(ys) + max(ys)) / 2.0,
        max(xs) - min(xs),
        max(ys) - min(ys),
    )


def _split(frame: _Frame, op: Operation) -> None:
    """Divide what it is aimed at into two named parts.

    This is the verb that makes the rest of the grammar productive. Once a mass
    has a `west` and an `east`, every other verb can be aimed at one of them,
    and the same four words describe a different building depending on where
    they land. It is also how the corpus works: OMA's patents transform a known
    type, and half of them begin by cutting it in two.

    The parts are unequal by default, because two equal masses do not occur in
    built work - and unequal in height as well as in plan. Cutting a box into
    a 62/38 pair of the same height and standing them flush produces a drawing
    identical to the box: the division is in the data and not in the building,
    and every later verb aimed at one half then acts on something nobody can
    see. `stack` has refused equal tiers since it was written, quoting the same
    corpus reading; the rule belongs to both verbs or to neither.
    """

    picked, rest = _scope(frame, op)
    if not picked:
        return
    ratio = _clamp(float(op.params.get("ratio", 0.62)), 0.3, 0.75)
    ux, uy = _direction(frame, op.params.get("along"))
    names = (str(op.params.get("first") or "part_a"), str(op.params.get("second") or "part_b"))
    gap = float(op.params.get("gap", 0.0)) * JOINT_CLEARANCE_M
    # The lesser part is the lower one. Held at the tier contrast, so the two
    # halves read as two volumes from any side rather than only in plan.
    contrast = max(MIN_TIER_CONTRAST, float(op.params.get("contrast", MIN_TIER_CONTRAST)))

    made: list[Placement] = []
    for item in picked:
        low, high = item.z_span()
        cx, cy, span_x, span_y = _bounds_of([item])
        along = span_x if abs(ux) >= abs(uy) else span_y
        first = along * ratio - gap / 2.0
        second = along * (1.0 - ratio) - gap / 2.0
        for name, size, side in ((names[0], first, -1.0), (names[1], second, 1.0)):
            if size <= 0.5:
                continue
            shift = side * (along - size) / 2.0
            tall = (high - low) if size >= along / 2.0 else (high - low) / contrast
            made.append(
                frame.box(
                    name,
                    w=size if abs(ux) >= abs(uy) else span_x,
                    d=span_y if abs(ux) >= abs(uy) else size,
                    z=low, h=tall,
                    dx=cx - frame.cx + (ux * shift if abs(ux) >= abs(uy) else 0.0),
                    dy=cy - frame.cy + (uy * shift if abs(uy) > abs(ux) else 0.0),
                    kind=item.kind,
                    plan=item.plan,
                    occupiable=item.occupiable,
                )
            )
    frame.placements = rest + made


def _extrude(frame: _Frame, op: Operation) -> None:
    share = _clamp(float(op.params.get("height", 1.0)), 0.1, 1.0)
    frame.placements.append(
        frame.box("body", w=frame.width, d=frame.depth, z=0.0, h=frame.height * share)
    )


def _stack(frame: _Frame, op: Operation) -> None:
    """Tiers that are never the same size.

    `contrast` is how much smaller each tier is than the one below, and it is
    held at or past `MIN_TIER_CONTRAST` whatever the author asked for. A stack
    of equal plates is the barracks Nishizawa refused, and it is what our
    archive was full of.
    """

    count = int(_clamp(float(op.params.get("n", 3)), 2, 6))
    contrast = max(MIN_TIER_CONTRAST, float(op.params.get("contrast", 1.35)))
    # Which way the tiers change size. The corpus rule is that tiers are never
    # equal, not that they always get smaller: Vancouver House grows floor by
    # floor once it clears the bridge, and Korean briefs put the assembly hall
    # on the top storey - 만수6동's says so in as many words - where a long-span
    # roof costs least because nothing has to be carried over it.
    #
    # Shrinking upward was hard-coded, so the largest volume was always the
    # bottom one and "hall on top" was unbuildable. The strategy axis reported
    # zero `crown` schemes out of 888 candidates for that reason alone.
    if bool(op.params.get("grow")):
        contrast = 1.0 / contrast
    share = _clamp(float(op.params.get("height", 1.0)), 0.1, 1.0)
    tier_h = frame.height * share / count
    # Which face stays flush as the tiers shrink. Centred is a wedding cake -
    # every tier steps back on all four sides at once, which is what a setback
    # regulation produces and not what an architect draws. Holding one face
    # gives the mass a front: the corpus's volumes share faces and edges, they
    # do not float concentrically inside one another.
    ux, uy = _direction(frame, op.params.get("align")) if op.params.get("align") else (0.0, 0.0)
    w, d = frame.width, frame.depth
    z = 0.0
    for index in range(count):
        # Tiers meet on a shared face, they do not overlap. Overlapping them by
        # 2% is what you do to keep a boolean kernel out of a degenerate case,
        # and this pipeline has no kernel: `compile` cuts bands at the z values
        # the volumes declare, so a 2% overlap declared one extra band per joint
        # carrying the lower tier's plan - a 0.16 m slice of a 8 m tier. The
        # renderer drew each as a false eaves line, so every stacked scheme read
        # as a pancake, and `large_span_strategy` read those slices as candidate
        # halls until it was taught to weigh volume instead of plan.
        frame.placements.append(
            frame.box(f"tier_{index}", w=w, d=d, z=z, h=tier_h,
                      dx=ux * (frame.width - w) / 2.0,
                      dy=uy * (frame.depth - d) / 2.0)
        )
        z += tier_h
        w, d = w / contrast, d / contrast


def _taper(frame: _Frame, op: Operation) -> None:
    """Narrow what is standing as it rises.

    A taper varies with height, and one affine matrix is linear, so no single
    box can be one - a box can only be *smaller*, which is a setback. That is
    what this used to build: it rebuilt the single highest volume at `ratio`
    and left everything else alone. Measured on the corpus, that volume is 1.0%
    of 79&Park, 1.6% of the New Museum and 1.7% of the Spiral, so the verb
    could not redraw a twentieth of the building whatever the author asked for.
    It was the silent word in eight of the twelve sentences the diff gate
    refused.

    An attempt to scale every picked volume by its own height fraction was
    worse (24 spoken to 21, cells 16/16 to 15/16) and the measurement said why:
    the volumes are not stacked. Timmerhuis' `field_plate` and its four objects
    all start at z=0, so interpolating by a volume's midpoint handed the tallest
    object 0.775 of the 0.55 the author wrote. Diluted, not tapered.

    The answer is the one the graphics literature gives and this package
    already had sitting unused: subdivide. `form.stack` cuts a volume into
    slabs, each with its own matrix, and that is what makes a continuously
    changing section representable at all - the same primitive that will carry
    bend, twist and pinch.

    The taper runs over the picked set as a whole, and each volume takes the
    part of it that its own z-range spans, so a tall object narrows more than a
    short one standing beside it and both belong to one silhouette.
    """

    ratio = _clamp(float(op.params.get("ratio", 0.7)), 0.3, 0.95)
    picked, rest = _scope(frame, op)
    if not picked:
        return
    base = min(item.z_span()[0] for item in picked)
    crest = max(item.z_span()[1] for item in picked)
    span = crest - base

    def scale_at(z: float) -> float:
        if span <= 1e-6:
            return ratio
        return 1.0 + (ratio - 1.0) * _clamp((z - base) / span, 0.0, 1.0)

    pulled: list[Placement] = []
    for item in picked:
        low, high = item.z_span()
        cx, cy, item_x, item_y = _bounds_of([item])
        low_scale, high_scale = scale_at(low), scale_at(high)
        # A slab per storey is as fine as the thing being described, and the
        # bands this produces are what the compiler and every measure read, so
        # the resolution is capped: past this the section is smooth enough and
        # the extra bands only cost.
        storeys = int(_clamp(round((high - low) / max(frame.storey, 1.0)), 2, 8))
        pulled.extend(
            stack(
                item.role,
                size=(item_x * low_scale, item_y * low_scale, high - low),
                at=(
                    cx - item_x * low_scale / 2.0,
                    cy - item_y * low_scale / 2.0,
                    low,
                ),
                storeys=storeys,
                taper=high_scale / low_scale,
                plan=item.plan,
                kind=item.kind,
                rotation_degrees=frame.rotation,
                occupiable=item.occupiable,
            )
        )
    frame.placements = rest + pulled


def _shear(frame: _Frame, op: Operation) -> None:
    """Displace the upper volumes, by a fraction of their own dimension.

    The magnitude is the corpus's and is clamped to it; the direction is the
    author's. Sliding every volume by the same absolute distance is what makes
    a shifted stack read as a stack that slipped rather than one that was
    moved.

    A volume keeps where it already stood. `frame.box` centres on the site
    frame, so rebuilding a volume through it without adding back its own offset
    teleports it to the middle of the parcel - and every other verb that
    rebuilds a volume (`split`, `lift`, `taper`) had remembered to add it back
    while this one had not. Measured: split a seed into `west` and `east` with
    a gap and the east half stands at x=45.5; shear it across, and its x snaps
    to 27.5, the frame centre, destroying the gap the split had just opened.

    That is where the missing articulation went. Kunsthal, Educatorium and the
    Netherlands Embassy all split and then shear a half, and the corpus measured
    1.86 separate bodies at grade against a 3.4 benchmark - not because the
    sentences failed to separate anything, but because the next word pulled the
    pieces back together. An authoring agent found it by writing sentences that
    should have worked and watching them not.
    """

    ratio = _clamp(float(op.params.get("ratio", 0.26)), MIN_OFFSET_RATIO, MAX_OFFSET_RATIO)
    ux, uy = _direction(frame, op.params.get("toward"))
    picked, rest = _scope(frame, op)
    if not picked:
        return
    ordered = sorted(picked, key=lambda item: item.z_span()[0])
    # What the move is measured against. Aimed at a stack, a shear is a stack
    # that slipped and the volume on the ground is what it slipped from, so
    # that one holds still. Aimed at something standing at one level - a tier,
    # an object, a leg of a ring - there is nothing above it in the picked set
    # to slip past, and anchoring the lowest picked volume meant the move did
    # nothing whatever: the diff check reported exactly 0.0 for eleven of the
    # corpus sentences, Seattle and De Rotterdam and CCTV among them.
    #
    # An earlier attempt anchored on the rest of the building for every scoped
    # shear, which sent a large split part a full step off the parcel and into
    # the clip. Narrowed here to the case that is actually broken.
    levels = {round(item.z_span()[0], 3) for item in ordered}
    anchored = 0 if len(levels) > 1 else -1
    moved: list[Placement] = []
    for index, item in enumerate(ordered):
        if index == anchored:
            moved.append(item)
            continue
        low, high = item.z_span()
        cx, cy, span_x, span_y = _bounds_of([item])
        # Steps counted from the anchor, so a shear at one level moves
        # its volume by one step rather than by none.
        reach = ratio * (span_x if abs(ux) >= abs(uy) else span_y) * (index - anchored)
        moved.append(
            frame.box(item.role, w=span_x, d=span_y, z=low, h=high - low,
                      dx=cx - frame.cx + ux * reach,
                      dy=cy - frame.cy + uy * reach,
                      plan=item.plan, kind=item.kind, occupiable=item.occupiable)
        )
    frame.placements = rest + moved


def _carve(frame: _Frame, op: Operation) -> None:
    """Take a named room out of the mass, on the side the author aimed it."""

    share = _clamp(float(op.params.get("size", 0.35)), 0.15, 0.6)
    ux, uy = _direction(frame, op.params.get("at"))
    w, d = frame.width * share, frame.depth * share
    reach = (frame.width - w) / 2.0 * float(op.params.get("reach", 0.55))
    frame.placements.append(
        frame.box(
            "court",
            w=w, d=d, z=-frame.height,
            h=frame.height * 3.0,
            dx=ux * reach, dy=uy * reach,
            kind="subtractive",
        )
    )


def _lift(frame: _Frame, op: Operation) -> None:
    """Raise what is standing and put a smaller thing under it.

    Clearance is the one magnitude in this grammar that is not scale-free.
    Everything else is a ratio because everything else is set by the building's
    own proportions - but what makes a lift a lift is that a person passes
    underneath, and a person is the same height on every site. Kaktus, Grove
    and Grace Farms all lift by 0.15 of their height, which is ten metres or
    more on the buildings they were measured from; the same ratio on a 12.6 m
    parcel is 1.89 m, a crawl space. All three came back silent on every one of
    their variants, and they were right to: nothing was standing up.

    So the ratio sets the intent and the floor-viability minimum sets the
    dimension. A building too short to give that clearance and still be a
    building simply does not get lifted.

    The same argument bounds it from above, and only the floor was there. On a
    commercial parcel `frame.height` is 65 m, so the same 0.22 asks for a 14 m
    undercroft standing on 4 m sticks - and the plausibility gate let it pass,
    because a support is exempt from being as wide as a storey and nothing
    asked how tall an exempt thing may be. Rolex and Milstein went out as four
    towers with a block on top. A person passes under a lifted building, and
    the height a person passes under is a storey or two whatever the building
    is; past that the legs are the building and the room above is its hat.
    """

    picked, rest = _scope(frame, op)
    if not picked:
        return
    asked = _clamp(float(op.params.get("clearance", 0.22)), 0.1, 0.4) * frame.height
    room = max(frame.storey, DEFAULT_MINIMUM_CLEAR_DEPTH_M)
    clearance = _clamp(asked, DEFAULT_MINIMUM_CLEAR_DEPTH_M, room * MAX_UNDERCROFT_STOREYS)
    raised: list[Placement] = []
    for item in picked:
        low, high = item.z_span()
        corners = item.corners()
        span_x = max(x for x, _y, _z in corners) - min(x for x, _y, _z in corners)
        span_y = max(y for _x, y, _z in corners) - min(y for _x, y, _z in corners)
        centre_x = (max(x for x, _y, _z in corners) + min(x for x, _y, _z in corners)) / 2.0
        centre_y = (max(y for _x, y, _z in corners) + min(y for _x, y, _z in corners)) / 2.0
        raised.append(
            frame.box(item.role, w=span_x, d=span_y, z=low + clearance, h=high - low,
                      dx=centre_x - frame.cx, dy=centre_y - frame.cy,
                      kind=item.kind, plan=item.plan, occupiable=item.occupiable)
        )
    # Four supports, a third of the plan each, so what is raised spans between
    # neighbours rather than corner to corner. Two of them left a slab spanning
    # 632 times its own depth, which the span rule refused and was right to.
    leg = 0.32
    base_x, base_y, base_w, base_d = _bounds_of(picked)
    frame.placements = rest + raised + [
        frame.box("support", w=frame.width * leg, d=frame.depth * leg,
                  occupiable=False,
                  # Exactly the clearance, not a hair over. Overlapping into
                  # the slab cut a sliver band whose depth was 5% of the leg,
                  # and the raised plate then measured 540 times its own depth
                  # across that sliver - a span rule reading a rounding error.
                  z=0.0, h=clearance,
                  dx=sx * frame.width * (0.5 - leg / 2.0) * 0.78,
                  dy=sy * frame.depth * (0.5 - leg / 2.0) * 0.78)
        for sx, sy in ((-1, -1), (1, 1), (1, -1), (-1, 1))
    ]


def _loop(frame: _Frame, op: Operation) -> None:
    """Four bars round a court, held apart at the corners.

    A ring rather than a block with a hole: the bars are separate volumes that
    meet, which is how CCTV returns its thrust and how Louvre-Lens's volumes
    touch. The corner clearance is the joint every one of them holds.
    """

    depth = _clamp(float(op.params.get("bar", 0.26)), 0.15, 0.4)
    bar_w, bar_d = frame.width * depth, frame.depth * depth
    share = _clamp(float(op.params.get("height", 1.0)), 0.1, 1.0)
    h = frame.height * share
    # The bars run the full width and meet at the corners. A ring is one
    # structure - CCTV returns its thrust through the opposite leg, which is
    # why its overhang is not a cantilever - and the corner clearance belongs
    # between separate enclosures, not inside a single closed figure. Held
    # apart it reported itself as two buildings, correctly.
    frame.placements.extend([
        frame.box("bar_n", w=frame.width, d=bar_d, z=0.0, h=h,
                  dy=(frame.depth - bar_d) / 2.0),
        frame.box("bar_s", w=frame.width, d=bar_d, z=0.0, h=h * 0.72,
                  dy=-(frame.depth - bar_d) / 2.0),
        frame.box("bar_e", w=bar_w, d=frame.depth, z=0.0, h=h * 0.86,
                  dx=(frame.width - bar_w) / 2.0),
        frame.box("bar_w", w=bar_w, d=frame.depth, z=0.0, h=h * 0.58,
                  dx=-(frame.width - bar_w) / 2.0),
    ])


def _aggregate(frame: _Frame, op: Operation) -> None:
    """Objects inside a boundary, no two the same.

    SANAA's second mode: a pure figure holding N inscribed things. The sizes
    fan out rather than repeating - the corpus spreads them ten to twenty times
    in plan - because identical objects are the barracks again, and because a
    field with no largest object has nothing to read first.
    """

    count = int(_clamp(float(op.params.get("n", 4)), 2, MAX_FIELD_OBJECTS))
    spread = max(MIN_FIELD_SPREAD, float(op.params.get("spread", 1.6)))
    share = _clamp(float(op.params.get("height", 0.8)), 0.1, 1.0)
    # The boundary that makes a field one building. Kanazawa's boxes sit under
    # a single roof and Zollverein's rooms inside one cube; without it the
    # objects are what the gate said they were, five buildings on one parcel.
    tie = _clamp(float(op.params.get("tie", 0.18)), 0.0, 0.4)
    if tie > 0.0:
        frame.placements.append(
            # The tie is a boundary, not a room - Kanazawa's roof, Grace Farms'
            # ribbon - so it is exempt from the one-storey floor for the same
            # reason a support is. Held to a storey it grew as thick as the
            # objects it binds and swallowed them, and a `taper` aimed at one of
            # them then changed the compiled mass by exactly nothing.
            frame.box("field_plate", w=frame.width, d=frame.depth, z=0.0,
                      h=frame.height * tie, occupiable=False)
        )
    # A field may have no boundary at all, and then the objects are separate
    # buildings sharing a plot - which is what Moriyama and the Inujima Art
    # Houses are: ten volumes that never touch, with the village lanes between
    # them doing the circulating. The floor of 0.08 was there because a field
    # with no tie once read as five buildings on one parcel, but that reading
    # is not wrong for these, and holding every field together is what kept
    # grade articulation pinned at one however many objects were placed.

    # Objects sit in the cells of a loose grid rather than in a table of corner
    # slots. The table held six, and six was the ceiling on how many bodies this
    # whole grammar could stand at grade - `split` divides a field, it does not
    # multiply one, so no combination of words could get past it. Moriyama is
    # ten volumes, Nishinoyama ten dwellings, Towada one per artwork; a field
    # that cannot count past six cannot say any of them.
    #
    # A grid also guarantees what the corner table only got away with at small
    # counts: every object has its own cell, so none of them overlap however
    # many there are.
    columns = max(1, int(ceil(sqrt(count))))
    rows = max(1, int(ceil(count / columns)))
    cell_w = frame.width / columns
    cell_d = frame.depth / rows
    for index in range(count):
        column, row = index % columns, index // columns
        # Size fans out across the whole field, and the smallest object is held
        # to a storey: the old height divisor of 1/(1+0.3i) put the ninth object
        # at a quarter of the first, which the storey gate refuses and rightly.
        scale = 1.0 / (spread ** (index / max(count - 1, 1)))
        w = (cell_w - JOINT_CLEARANCE_M) * 0.86 * scale
        d = (cell_d - JOINT_CLEARANCE_M) * 0.86 * scale
        # Cells alternate their offset so the result reads as a settlement
        # rather than as a barracks - the thing the size fan exists to avoid,
        # asked of position as well as of size.
        drift = 0.14 * (1 if (column + row) % 2 else -1)
        frame.placements.append(
            frame.box(
                f"object_{index}",
                w=w, d=d, z=0.0,
                h=frame.height * share * (0.55 + 0.45 * scale),
                dx=(column + 0.5 + drift) * cell_w - frame.width / 2.0,
                dy=(row + 0.5 - drift) * cell_d - frame.depth / 2.0,
            )
        )


_VERBS = {
    "split": _split,
    "extrude": _extrude,
    "stack": _stack,
    "taper": _taper,
    "shear": _shear,
    "carve": _carve,
    "lift": _lift,
    "loop": _loop,
    "aggregate": _aggregate,
}


def execute(
    parti: Parti,
    *,
    buildable: Polygon,
    axis: tuple[float, float],
    height_m: float,
    storey_height_m: float = 0.0,
) -> MatrixForm | None:
    """Turn a sentence into placed volumes on this parcel.

    The last frame of `execute_steps`, rather than a second copy of the same
    loop. There were two, and keeping them in step was left to whoever edited
    one: adding the base-shape parameter to the stepped loop alone meant the
    whole pipeline still built squares while the check that reads the steps
    reported the shapes correctly. One loop is the only version of this that
    cannot drift.
    """

    steps = execute_steps(
        parti, buildable=buildable, axis=axis, height_m=height_m,
        storey_height_m=storey_height_m,
    )
    return steps[-1][1] if steps else None


def execute_steps(
    parti: Parti,
    *,
    buildable: Polygon,
    axis: tuple[float, float],
    height_m: float,
    storey_height_m: float = 0.0,
) -> list[tuple[Operation, MatrixForm]]:
    """The same sentence, stopped after each word.

    A parti is published as an ordered list of moves with one caption each -
    79&Park is EXTRUSION, POROSITY, DAYLIGHT, LANDMARK, one drawing per line -
    and that sequence is what makes the offices' massing read as an argument
    rather than a shape. We were compiling the whole sentence and drawing only
    its last word, which throws away the reasoning the author already wrote:
    every operation carries its own `why`.

    Nothing new is generated here. Running the same handlers over the same
    frame and taking a copy after each one costs one extra compile per word.
    """

    frame = _Frame(buildable, axis, height_m, storey_m=storey_height_m)
    steps: list[tuple[Operation, MatrixForm]] = []
    for op in parti.ops:
        handler = _VERBS.get(op.verb)
        if handler is None:
            continue
        # A base shape belongs to the composition, so naming one anywhere in
        # the sentence sets it for everything the sentence goes on to build.
        named = str(op.params.get("profile") or "").strip().lower()
        if named in plan_names():
            frame.profile = named
        handler(frame, op)
        form = _form_from(frame, parti)
        if form is not None:
            steps.append((op, form))
    return steps


def _form_from(frame: _Frame, parti: Parti) -> MatrixForm | None:
    if not [item for item in frame.placements if item.kind == "additive"]:
        return None
    return MatrixForm(
        name=parti.name,
        placements=tuple(frame.placements),
        primary_language=parti.primary_language,
        secondary_language=parti.secondary_language,
        formal_principle=parti.formal_principle,
        dominant_gesture=parti.dominant_gesture,
        reference_basis=parti.reference_basis,
        floor_height_m=parti.floor_height_m,
        extra={
            "parti": parti.evidence(),
            "plot_mode": parti.plot_mode(),
            # A field spreads; it does not stack. Kanazawa is one storey, and
            # the objects in a field are small - let the growth loop buy floor
            # area with height and they come back as a bundle of sticks on a
            # plinth, which is what they did. If a field cannot fill its 용적률
            # lying down, the honest answer is that it does not fill it.
            "growth": "plan" if any(op.verb == "aggregate" for op in parti.ops) else "both",
        },
    )


__all__ = ["execute", "execute_steps"]
