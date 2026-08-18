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

import math
from dataclasses import dataclass, replace
from math import ceil, sqrt
from typing import Any

from shapely.geometry import Polygon

from design.maas.floor_viability import DEFAULT_MINIMUM_CLEAR_DEPTH_M
from design.maas.massv2.plausibility import DAYLIT_DEPTH_PER_STOREY

from .compile import _plan
from .form import MatrixForm, Placement, place, stack
from .ops import AFFINE_VERBS
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


@dataclass(frozen=True)
class Line:
    """An alignment or symmetry axis the composition is holding onto."""

    origin: tuple[float, float]
    direction: tuple[float, float]
    born: str = "site"


@dataclass(frozen=True)
class Centre:
    """A point operations turn about, or a void is centred on."""

    point: tuple[float, float]
    born: str = "site"


class _Frame:
    """The site's own box, the volumes standing in it, and what regulates them.

    Akin & Moustapha (Design Studies 25(1), 2004) watched six architects mass a
    building for two hours each and found the mechanism that structured all of
    it: regulating elements - symmetry axes, centres of rotation, alignment
    lines. What they let an architect do is add and remove masses freely while
    the underlying structure survives, and that survival is what separates a
    composition from a pile.

    This grammar had the machinery and no vocabulary. `ops.affine` already says
    "which volumes, which operator, about what pivot", but the pivot was the
    bounding-box centre of whatever the operation happened to pick, recomputed
    per call and thrown away - so no two operations could share one, and a
    sentence had no way to say "turn this about the line the split just cut".
    """

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
        # What the site gives, before any word is said. Nothing is invented
        # here: every one of these is already computed elsewhere in the package
        # and was being thrown away.
        along = (math.cos(math.radians(rotation)), math.sin(math.radians(rotation)))
        across = (-along[1], along[0])
        self.lines: dict[str, Line] = {
            "spine": Line((cx, cy), along, "site"),
            "cross": Line((cx, cy), across, "site"),
            "street": Line((cx, cy), axis, "site"),
        }
        self.centres: dict[str, Centre] = {"site": Centre((cx, cy), "site")}

    def regulates(self, name: str, element) -> None:
        """Record an axis or a centre an operation just brought into being.

        This is the half of the finding that matters. A regulating element is
        not drawn up front and obeyed - it is produced by a move and then
        honoured by the moves after it, which is how the structure survives
        being edited.
        """

        if isinstance(element, Line):
            self.lines[name] = element
        else:
            self.centres[name] = element

    def out(self, dx: float, dy: float) -> tuple[float, float]:
        """A displacement written in the frame's axes, said in world terms.

        The frame is the parcel's own rectangle and it is almost never square
        to north - Uijeongbu's bearing is -168.3 degrees, Gangnam's is 35.5.
        `_direction` returns its vectors in the frame's axes, and `box` was
        adding them straight onto a world centre, so a move written "along" ran
        along world east instead: at -168 degrees the cosine is -0.979 and the
        move went backwards.

        Both halves of a top-level `split` survive that, because they are
        symmetric about one centre and reversing the sides only swaps their
        names. A second `split` aimed at one of those halves does not: the
        parent's offset is a world quantity and the child's shift is a frame
        one, so the child crosses the gap the first cut opened. Measured on
        `kr_hansol_gym_is_its_own_body`, whose sentence cuts twice, `library`
        stood 0.00 m from `gym` across a 2.58 m declared gap.
        """

        if abs(self.rotation) < 1e-9:
            return (dx, dy)
        bearing = math.radians(self.rotation)
        cos_b, sin_b = math.cos(bearing), math.sin(bearing)
        return (dx * cos_b - dy * sin_b, dx * sin_b + dy * cos_b)

    def point(self, dx: float, dy: float) -> tuple[float, float]:
        """The world position of a frame offset, for the two verbs that place
        absolutely instead of through `box` - `taper` and `twist` hand a corner
        straight to `stack`."""

        world = self.out(dx, dy)
        return (self.cx + world[0], self.cy + world[1])

    def local(self, x: float, y: float) -> tuple[float, float]:
        """Where a world point sits in the frame's axes, from the frame centre."""

        if abs(self.rotation) < 1e-9:
            return (x - self.cx, y - self.cy)
        bearing = math.radians(-self.rotation)
        cos_b, sin_b = math.cos(bearing), math.sin(bearing)
        ox, oy = x - self.cx, y - self.cy
        return (ox * cos_b - oy * sin_b, ox * sin_b + oy * cos_b)

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
        turn: float = 0.0,
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
        world_dx, world_dy = self.out(dx, dy)
        return place(
            role,
            size=(max(w, 0.5), max(d, 0.5), max(h, least, 0.5)),
            at=(self.cx + world_dx - w / 2.0, self.cy + world_dy - d / 2.0, z),
            # Off the frame's bearing, not instead of it. A volume that
            # abandons the parcel's axis reads as a mistake; one sitting a few
            # degrees off it reads as having been placed.
            rotation_degrees=self.rotation + float(turn),
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
    # A named regulating element wins over the three site directions: a
    # sentence that says "along the line the split cut" means that line, and
    # the fallback below is what every existing sentence already gets.
    held = frame.lines.get(str(toward or ""))
    if held is not None:
        dx, dy = held.direction
        # Back into the frame's own axes, which is what every caller expects.
        bearing = math.radians(frame.rotation)
        cos_b, sin_b = math.cos(-bearing), math.sin(-bearing)
        return (dx * cos_b - dy * sin_b, dx * sin_b + dy * cos_b)
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


def _bounds_of(
    items: list[Placement], frame: "_Frame"
) -> tuple[float, float, float, float]:
    """Centre and span in plan of a set of volumes, in the frame's own axes.

    The spans have to be measured on the axes the boxes are built on. Every
    volume here is posed at the parcel's bearing, and this used to take the
    axis-aligned bounding box of the posed corners - which on a skewed parcel is
    larger than the box it encloses, by the cosine of the bearing on each side.
    So every verb that rebuilds a volume from these numbers rebuilt it bigger
    than the volume it replaced, on every site whose seed rectangle is not
    square to north.

    Measured on Mountain Dwellings: the `split` leaves `slope` 49.2 m long and
    the `grade` after it rebuilds its first step at 57.8 m, eating the 3.8 m
    gap the split had opened and closing what the sentence was about. The same
    inflation is why `lift` closed Villa dall'Ava's.

    The centre comes back in the frame's axes too, as an offset from the frame
    centre, which is the form every caller passes straight to `box`. It used to
    be returned in world coordinates and the callers subtracted `frame.cx`
    themselves, which left a world quantity being added to a frame one in the
    same expression - see `_Frame.out`.
    """

    corners = [corner for item in items for corner in item.corners()]
    xs = [x for x, _y, _z in corners]
    ys = [y for _x, y, _z in corners]
    centre_x = (min(xs) + max(xs)) / 2.0
    centre_y = (min(ys) + max(ys)) / 2.0
    offset = frame.local(centre_x, centre_y)
    if abs(frame.rotation) < 1e-9:
        return (offset[0], offset[1], max(xs) - min(xs), max(ys) - min(ys))
    bearing = math.radians(-frame.rotation)
    cos_b, sin_b = math.cos(bearing), math.sin(bearing)
    turned = [
        ((x - centre_x) * cos_b - (y - centre_y) * sin_b,
         (x - centre_x) * sin_b + (y - centre_y) * cos_b)
        for x, y, _z in corners
    ]
    us = [u for u, _v in turned]
    vs = [v for _u, v in turned]
    return (offset[0], offset[1], max(us) - min(us), max(vs) - min(vs))


def _plan_shrink(item: Placement, span_x: float, span_y: float) -> float:
    """How much a rebuilt box must shrink to hold no more plan than it had.

    Every verb that rebuilds a volume rebuilds it as a rectangle spanning the
    volume's bounding box, and every sentence starts from a parcel-shaped seed,
    so the rebuilt piece is larger than the piece it replaced. `_split` grew a
    building by 74% that way. The same arithmetic is here because `_grade` and
    `_lift` rebuild too, and measured on the corpus it is why their gaps close:
    Mountain Dwellings' `split` opens 3.8 m and its `grade` closes it to nothing,
    Villa dall'Ava's `split` opens 3.05 m and its `lift` closes it to nothing.
    The rebuilt piece grows sideways into the space the earlier word made.

    Returns 1.0 for a rectangle, so nothing that was already honest moves.
    """

    box = span_x * span_y
    if box <= 1e-9:
        return 1.0
    area = float(_plan(item).area)
    if area <= 1e-9 or area >= box:
        return 1.0
    return (area / box) ** 0.5


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
        cx, cy, span_x, span_y = _bounds_of([item], frame)
        along = span_x if abs(ux) >= abs(uy) else span_y
        # Cutting cannot make the building bigger. The pieces are rectangles
        # spanning the bounding box, so a plan that is not a rectangle - the
        # parcel-shaped volume every sentence starts from - grew every time it
        # was cut: Central Beheer's three splits took 3,342 m² to 5,815 m², a
        # 74% rise that put it over 건폐율 at 1.17 of the cap while the sentence
        # believed it was dividing a settlement. So the cross dimension is
        # whatever holds the plan area it was cut from, not the bounding box.
        # For a rectangle the two are the same and nothing changes.
        across_span = span_y if abs(ux) >= abs(uy) else span_x
        plan_area = float(_plan(item).area)
        across = (
            min(across_span, plan_area / along)
            if along > 1e-9 and plan_area > 1e-9
            else across_span
        )
        first = along * ratio - gap / 2.0
        second = along * (1.0 - ratio) - gap / 2.0
        for name, size, side in ((names[0], first, -1.0), (names[1], second, 1.0)):
            # A piece narrower than a room is not a piece of a building. The
            # floor used to be half a metre, which is a wall, and on a 264 m²
            # parcel in Gangnam `kr_hoeryong_nursery_three_low_wings` came out
            # as a 3.7 m body, a 2.1 m one and a 1.5 x 4.0 m needle standing
            # 7.6 m tall beside them. The plausibility gate passed it because it
            # weighs the whole mass and the needle is 18% of it - which is the
            # right question for that gate and the wrong place to catch this.
            #
            # Refusing the piece means a mass too small to cut comes through
            # uncut, and the silence gate then reports the `split` as a word
            # that did nothing. That is the honest outcome: on a plot this size
            # the sentence cannot be said, and it should say so rather than
            # deliver splinters.
            if size <= DEFAULT_MINIMUM_CLEAR_DEPTH_M or across <= DEFAULT_MINIMUM_CLEAR_DEPTH_M:
                continue
            shift = side * (along - size) / 2.0
            tall = (high - low) if size >= along / 2.0 else (high - low) / contrast
            made.append(
                frame.box(
                    name,
                    w=size if abs(ux) >= abs(uy) else across,
                    d=across if abs(ux) >= abs(uy) else size,
                    z=low, h=tall,
                    dx=cx + (ux * shift if abs(ux) >= abs(uy) else 0.0),
                    dy=cy + (uy * shift if abs(uy) > abs(ux) else 0.0),
                    kind=item.kind,
                    # A piece cut from a plan is not a copy of that plan. Cut a
                    # circular museum in two and you get two half-circles, not
                    # two circles - and this vocabulary has no half-circle, so
                    # the honest piece is the rectangle.
                    #
                    # Copying it was worse than either: a profile is normalized
                    # into the unit square and then scaled by each volume's own
                    # width and depth, so the same trapezoid came out at a
                    # different splay in every part. Lab City's three volumes
                    # measured 2.07, 1.64 and 2.33 to one, which drew three
                    # unrelated wedges where the building is one block with a
                    # diagonal street cut through it.
                    plan="square",
                    occupiable=item.occupiable,
                )
            )
        # The cut is an alignment line the rest of the sentence can hold onto.
        # It is the composition's own axis rather than the site's, and it is
        # exactly what an architect draws first and keeps.
        # Stored in world terms, because that is where a line lives and what
        # `_direction` turns back into the frame's axes when a later word names
        # it. The point and the direction are both frame quantities here.
        cut = (-uy, ux) if abs(ux) >= abs(uy) else (uy, -ux)
        frame.regulates(
            f"{names[0]}|{names[1]}",
            Line(
                (frame.cx + frame.out(cx, cy)[0], frame.cy + frame.out(cx, cy)[1]),
                frame.out(*cut),
                "split",
            ),
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
    # VIA 57 West holds three corners near 40 m and draws the fourth to 142 m -
    # a contrast of 3.5 inside one figure. A ceiling of 2.0 made that sentence
    # unwritable, so the cap is the built work's rather than a guess, and the
    # storey and structure gates decide whether the result stands.
    contrast = _clamp(float(op.params.get("contrast", 1.35)), MIN_TIER_CONTRAST, 3.5)
    # Which way the tiers change size. The corpus rule is that tiers are never
    # equal, not that they always get smaller: Vancouver House grows floor by
    # floor once it clears the bridge, and Korean briefs put the assembly hall
    # on the top storey - 만수6동's says so in as many words - where a long-span
    # roof costs least because nothing has to be carried over it.
    #
    # Shrinking upward was hard-coded, so the largest volume was always the
    # bottom one and "hall on top" was unbuildable. The strategy axis reported
    # zero `crown` schemes out of 888 candidates for that reason alone.
    growing = bool(op.params.get("grow"))
    if growing:
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
    if growing:
        # The plot is the size of the largest tier, whichever end of the stack
        # that is. Shrinking, the largest is the first and the series starts at
        # the seed; growing, it is the last, and starting at the seed anyway
        # multiplied the plot by the contrast once per tier:
        #
        #     vancouver_house  n=3 contrast=3.0 grow   1,866 -> 166,049 m² in plan
        #     via57            n=2 contrast=3.5 grow   2,375 ->  45,723 m²
        #
        # The alignment offset below is `(frame.width - w) / 2`, which is a
        # displacement to the flush face while `w` fits the plot and a throw off
        # the site once it does not: those two masses were built 269 m and 81 m
        # from the parcel centre, and only the growth loop's re-centring
        # brought them back.
        span = contrast ** (count - 1)
        w, d = w * span, d * span
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
        tier = frame.box(f"tier_{index}", w=w, d=d, z=z, h=tier_h,
                         dx=ux * (frame.width - w) / 2.0,
                         dy=uy * (frame.depth - d) / 2.0)
        frame.placements.append(tier)
        # Advance by what the tier actually came out at, not by what was asked
        # for. `box` holds an occupiable volume to a storey, so a stack of five
        # on a twelve-metre frame asks for 2.40 m tiers and gets 3.00 m ones -
        # and stepping by 2.40 buried each tier 0.60 m in the one below. The
        # growth loop then widened that to 1.65 m, and the compiler cut a band
        # at every overlap: nine prisms for five platforms, drawn as horizontal
        # stripes across the whole of Seattle. Which is the failure the comment
        # above already describes, arriving by a different route.
        z = tier.z_span()[1]
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
        cx, cy, item_x, item_y = _bounds_of([item], frame)
        # `stack` takes a world corner, not a frame offset - this verb does not
        # go through `box`, so the conversion has to happen here.
        world_x, world_y = frame.point(cx, cy)
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
                    world_x - item_x * low_scale / 2.0,
                    world_y - item_y * low_scale / 2.0,
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


def _grade(frame: _Frame, op: Operation) -> None:
    """Cut it back a step at a time, so the section becomes a stair.

    The book's own word - Grade, 단차화하다, "단계적으로 깎아 계단형 윤곽 생성" -
    and the grammar had no way to say it. Mountain Dwellings is the sentence
    that needed it: the parking ramp's slope is the section of the whole
    building and the dwellings are terraces on that slope. Written with `skew`,
    which leans a prism, the mass came out a box with an overhang - a sheared
    solid still has a flat top and a flat bottom, and a terrace is neither.

    A `taper` is the nearest thing already here and it is not this either: it
    narrows on every side as it rises, which is a ziggurat rather than a slope.
    A grade gives ground away on one side only, so the far edge stands where it
    always did and the near one walks back.

    Discrete on purpose. The book says 계단형 - stepped - and the terraces are
    the storeys, so the steps are storeys and not a smooth ramp.
    """

    picked, rest = _scope(frame, op)
    if not picked:
        return
    # How much of the plan the top step has given up. Below a fifth the stair
    # is a setback detail; above nine tenths the top step has no floor left.
    run = _clamp(float(op.params.get("run", 0.6)), 0.2, 0.9)
    ux, uy = _direction(frame, op.params.get("toward"))
    along_x = abs(ux) >= abs(uy)

    made: list[Placement] = []
    for item in picked:
        low, high = item.z_span()
        cx, cy, span_x, span_y = _bounds_of([item], frame)
        along = span_x if along_x else span_y
        # A step cannot be wider than the plan it steps out of. Without this the
        # stair walks sideways into whatever the sentence set beside it.
        shrink = _plan_shrink(item, span_x, span_y)
        across = (span_y if along_x else span_x) * shrink
        # One step per storey: the terraces are floors, and asking for more
        # resolution than the building has invents steps nobody stands on.
        steps = int(_clamp(
            round((high - low) / max(frame.storey, 1.0)),
            2, int(_clamp(float(op.params.get("steps", 6)), 2, 8)),
        ))
        band = (high - low) / steps
        # Stepping by the band asked for buries each step in the one below
        # whenever `box` holds it up to a storey - Mountain Dwellings asks for
        # 2.70 m over four steps and gets 3.00 m ones, so every step overlaps by
        # 0.30 and the compiler cuts a band at each overlap. Exactly the fault
        # `_stack` had; CopenHill escaped it only because its band happened to
        # land on the storey height. So the next step starts where the last one
        # actually ended.
        rises_at = low
        for index in range(steps):
            keep = along * (1.0 - run * index / max(steps - 1, 1))
            # A terrace narrower than a room is not a terrace, for the same
            # reason a split piece that narrow is not a piece - and the stair
            # runs into it first, because every step is narrower than the last.
            # On the 264 m² Gangnam parcel CopenHill's steps came out 6.1, 6.1,
            # 3.9 and then 1.0 m across, and the last one drew as a spike on the
            # roof. The stair simply stops where the building runs out of plan.
            if keep <= DEFAULT_MINIMUM_CLEAR_DEPTH_M or across <= DEFAULT_MINIMUM_CLEAR_DEPTH_M:
                break
            # The high side stands still and the low side steps back, so the
            # stair reads from one direction rather than as a symmetric pile.
            shift = (along - keep) / 2.0
            step = frame.box(
                    f"{item.role}_step_{index}",
                    w=keep if along_x else across,
                    d=across if along_x else keep,
                    z=rises_at,
                    h=band,
                    dx=cx + (ux * shift if along_x else 0.0),
                    dy=cy + (uy * shift if not along_x else 0.0),
                    kind=item.kind,
                    plan=item.plan,
                    occupiable=item.occupiable,
                )
            made.append(step)
            rises_at = step.z_span()[1]
    frame.placements = rest + made


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
        cx, cy, span_x, span_y = _bounds_of([item], frame)
        # Steps counted from the anchor, so a shear at one level moves
        # its volume by one step rather than by none.
        reach = ratio * (span_x if abs(ux) >= abs(uy) else span_y) * (index - anchored)
        moved.append(
            frame.box(item.role, w=span_x, d=span_y, z=low, h=high - low,
                      dx=cx + ux * reach,
                      dy=cy + uy * reach,
                      plan=item.plan, kind=item.kind, occupiable=item.occupiable)
        )
    frame.placements = rest + moved


def _carve(frame: _Frame, op: Operation) -> None:
    """Take a named room out of the mass, on the side the author aimed it."""

    # Sized and placed against the site's seed rectangle, not against the mass
    # that is standing. That looks like the wrong frame of reference - it is the
    # mistake `_lift` made three times - and aiming it at the standing mass was
    # tried and is not supported by the measurement. Removal as a share of the
    # compiled solid, over the thirteen sentences that carve, notch or puncture:
    #
    #     median 14.4%, and only one case under 5%
    #     big_tirpitz_blaavand at 1.6% - already reported silent by the gate
    #
    # Aiming at the mass moved two schemes up by about two points, two down by
    # about one, and left the rest flat; Tirpitz itself got worse, 2.3% to 1.6%.
    # So the compositions here stay close enough to the seed that the two frames
    # agree, and Tirpitz's weak carve has some other cause. Reverted rather than
    # kept on principle.
    share = _clamp(float(op.params.get("size", 0.35)), 0.15, 0.6)
    ux, uy = _direction(frame, op.params.get("at"))
    w, d = frame.width * share, frame.depth * share
    reach = (frame.width - w) / 2.0 * float(op.params.get("reach", 0.55))
    # How far up the void reaches. Every subtractive volume in this grammar was
    # written to go clean through - `z=-height, h=3*height` in carve, notch and
    # puncture alike - so there was no way to take out the lower part of a mass
    # and leave the upper part standing. That is an arch, and it is also CCTV:
    # "고리가 수평이 아니라 수직으로 서서, 두 다리와 공중의 귀환부가 하나의
    # 회로를 이룬다". Written with `loop`, which rings a court in plan, the mass
    # came out as a flat donut - the opposite of its own sentence, and the
    # critics tagged it `sentence-contradicted` in three rounds running.
    #
    # The compiler subtracts per band, so a cutter with a bounded z-range cuts
    # only the bands it spans. The machinery was there; the word was not.
    # 1.0 is through, which is what every existing sentence gets.
    up_to = _clamp(float(op.params.get("up_to", 1.0)), 0.2, 1.0)
    # And whether it goes all the way across. A court is inboard on both axes
    # and leaves building on every side of it; an arch is open at both ends, and
    # what is left either side of it are two legs. Without this the void stays
    # square in plan however large it is, so `up_to` alone made a low recess in
    # a face rather than a hole you can see the sky through - measured on CCTV,
    # whose whole sentence is the two legs.
    through = bool(op.params.get("through", False))
    # Measured against what is standing, not against the frame. `frame.height`
    # is what the parcel affords, and a sentence that extrudes to a third of it
    # has a mass a third as tall - so `up_to` read off the frame put the top of
    # the cutter above the building and cut clean through. Milstein extrudes to
    # 4.2 m and its 0.55 asked for 6.6, which drew a doughnut where the sentence
    # says the ground passes under a plate.
    standing = max(
        (item.z_span()[1] for item in frame.placements if item.kind == "additive"),
        default=frame.height,
    )
    # What was taken out is a place, and the rest of the sentence may want to
    # be about it - a court that later moves alone is a hole; a court the
    # building turns around is a courtyard.
    frame.regulates(
        "court",
        Centre(
            (
                frame.cx + frame.out(ux * reach, uy * reach)[0],
                frame.cy + frame.out(ux * reach, uy * reach)[1],
            ),
            "carve",
        ),
    )
    frame.placements.append(
        frame.box(
            "court",
            w=w if abs(ux) >= abs(uy) or not through else frame.width * 1.2,
            d=frame.depth * 1.2 if through and abs(ux) >= abs(uy) else d,
            z=-frame.height,
            # Up from below the ground to wherever the sentence says it stops.
            h=frame.height + standing * up_to,
            dx=ux * reach, dy=uy * reach,
            kind="subtractive",
        )
    )


def _notch(frame: _Frame, op: Operation) -> None:
    """Take a bite out of a corner.

    `carve` aims at a side and reaches in; a notch belongs to a corner, and the
    book keeps them apart because they read differently - a court is a room the
    building holds, a notch is the building declining to occupy a corner. Two of
    the twenty combinations the book records are notches (Notch + Notch, Shift +
    Notch), and neither is expressible as a carve.
    """

    share = _clamp(float(op.params.get("size", 0.3)), 0.15, 0.5)
    ux, uy = _direction(frame, op.params.get("at"))
    # A corner, so both axes are committed. The named direction picks the long
    # side and the cross sign follows it rather than being a second parameter.
    sy = 1.0 if ux >= 0.0 else -1.0
    w, d = frame.width * share, frame.depth * share
    frame.placements.append(
        frame.box(
            "notch",
            w=w, d=d, z=-frame.height, h=frame.height * 3.0,
            dx=(ux if abs(ux) >= abs(uy) else sy) * (frame.width - w) / 2.0,
            dy=(uy if abs(uy) > abs(ux) else sy) * (frame.depth - d) / 2.0,
            kind="subtractive",
        )
    )


def _puncture(frame: _Frame, op: Operation) -> None:
    """Drive a hole clean through, top to bottom.

    A court is open to the sky and stops at the ground; a puncture goes through
    the whole mass and is a route, a light well or a passage. `carve` already
    cuts a full-height void, so the difference the book draws is where it sits:
    a puncture is inboard, away from every edge, which is what makes it read as
    a hole rather than as a recess.
    """

    share = _clamp(float(op.params.get("size", 0.22)), 0.1, 0.45)
    count = int(_clamp(float(op.params.get("n", 1)), 1, 3))
    w, d = frame.width * share, frame.depth * share
    for index in range(count):
        # Spaced along the length rather than stacked on one spot, and kept off
        # the edges so each one is surrounded by building.
        along = (index + 1) / (count + 1) - 0.5
        frame.placements.append(
            frame.box(
                f"puncture_{index}",
                w=w, d=d, z=-frame.height, h=frame.height * 3.0,
                dx=along * (frame.width - w) * 0.8,
                dy=0.0,
                kind="subtractive",
            )
        )




def _twist(frame: _Frame, op: Operation) -> None:
    """Turn the section progressively as it rises.

    One affine cannot twist, for the same reason it cannot taper: the transform
    varies with height and a matrix is linear. `form.stack` was written for
    exactly this and carries a `twist_degrees` argument that nothing had ever
    passed. Vancouver House and the Shanghai Tower are this verb; so is half of
    what the corpus calls a tower.
    """

    turn = _clamp(float(op.params.get("degrees", 30.0)), 5.0, 90.0)
    picked, rest = _scope(frame, op)
    if not picked:
        return
    twisted: list[Placement] = []
    for item in picked:
        low, high = item.z_span()
        cx, cy, span_x, span_y = _bounds_of([item], frame)
        # As in `_taper`: a world corner, not a frame offset.
        world_x, world_y = frame.point(cx, cy)
        storeys = int(_clamp(round((high - low) / max(frame.storey, 1.0)), 3, 10))
        twisted.extend(
            stack(
                item.role,
                size=(span_x, span_y, high - low),
                at=(world_x - span_x / 2.0, world_y - span_y / 2.0, low),
                storeys=storeys,
                twist_degrees=turn,
                plan=item.plan,
                kind=item.kind,
                rotation_degrees=frame.rotation,
                occupiable=item.occupiable,
            )
        )
    frame.placements = rest + twisted


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
        # On the frame's own axes. This used to take the axis-aligned bounds of
        # the posed corners inline - the same inflation `_bounds_of` was fixed
        # for, copied here and left behind. Villa dall'Ava's `split` opens
        # 3.16 m and its `lift` rebuilt the raised half wide enough to close it
        # to 0.95, and the supports were innocent: measured, all four sit at
        # least 1.66 m from the other apartment and two of them entirely inside
        # the volume they hold up.
        centre_x, centre_y, span_x, span_y = _bounds_of([item], frame)
        # Raising a volume does not widen it. Rebuilt at its bounding box a
        # parcel-shaped piece grows on every side, and on `oma_villa_dall_ava`
        # that swallowed the 3.05 m the `split` before it had opened.
        shrink = _plan_shrink(item, span_x, span_y)
        raised.append(
            frame.box(item.role, w=span_x * shrink, d=span_y * shrink,
                      z=low + clearance, h=high - low,
                      dx=centre_x, dy=centre_y,
                      kind=item.kind, plan=item.plan, occupiable=item.occupiable)
        )
    # Four supports, a third of the plan each, so what is raised spans between
    # neighbours rather than corner to corner. Two of them left a slab spanning
    # 632 times its own depth, which the span rule refused and was right to.
    # Slim enough to read as legs. At a third of the plate each, four of them
    # cover about 40% of what they carry and the drawing shows four blocks under
    # a slab rather than a slab held in the air - both judges of the fixed
    # benchmark said "nothing floats" of Maison Bordeaux while its geometry had
    # a 3.4 m gap in it. The old value was set against the span rule with *two*
    # supports; with four the span is halved and the plate still stands.
    leg = 0.24
    # Where the lifted volume was before it went up.
    stood_at = min((item.z_span()[0] for item in picked), default=0.0)
    # Off the plate as it was built, not as it arrived. The raised volume is
    # rebuilt to hold its own plan area rather than its bounding box, so sizing
    # the legs from the original left them sticking out past the plate they
    # carry - measured on Villa dall'Ava, the plate stood 3.16 m from the other
    # apartment and a leg stood 1.66 m from it.
    base_x, base_y, base_w, base_d = _bounds_of(raised, frame)
    frame.placements = rest + raised + [
        # Under the volume that was lifted, not under the site. These bounds
        # were being computed and then ignored: the supports were sized and
        # placed from `frame.width`/`frame.depth`, so lifting one half of a
        # split building stood four legs across the whole parcel and welded the
        # two halves together. Villa dall'Ava's sentence is two apartments
        # standing apart, its `split` opens 3.8 m, and the `lift` after it closed
        # the mass to a single piece - it lost every pair it appeared in.
        frame.box("support", w=base_w * leg, d=base_d * leg,
                  occupiable=False,
                  # From wherever the lifted volume was standing, not from the
                  # ground. `z=0.0` was hardcoded, so lifting the top of a stack
                  # drew its legs at grade - buried inside the tiers below,
                  # seven metres under the gap they were meant to hold open.
                  # Maison Bordeaux says the heaviest dwelling does not touch
                  # what is under it; the gap was there at 7.2-10.6 m and
                  # nothing in the drawing showed anything holding it up.
                  #
                  # Exactly the clearance, not a hair over. Overlapping into
                  # the slab cut a sliver band whose depth was 5% of the leg,
                  # and the raised plate then measured 540 times its own depth
                  # across that sliver - a span rule reading a rounding error.
                  z=stood_at, h=clearance,
                  dx=base_x + sx * base_w * (0.5 - leg / 2.0) * 0.78,
                  dy=base_y + sy * base_d * (0.5 - leg / 2.0) * 0.78)
        for sx, sy in ((-1, -1), (1, 1), (1, -1), (-1, 1))
    ]


def _loop(frame: _Frame, op: Operation) -> None:
    """Four bars round a court, held apart at the corners.

    A ring rather than a block with a hole: the bars are separate volumes that
    meet, which is how CCTV returns its thrust and how Louvre-Lens's volumes
    touch. The corner clearance is the joint every one of them holds.
    """

    depth = _clamp(float(op.params.get("bar", 0.26)), 0.15, 0.4)
    # A ring's bars are bars. `bar` is a share of the frame, so on a 60 m field
    # the 0.4 ceiling builds four volumes 24 m deep, which is twice as deep as
    # daylight reaches from both sides - a block, not a bar - and the four of
    # them close the court to 4% of the plan. CCTV came out a solid box with a
    # light shaft in it. The ceiling is the depth the corpus already builds
    # every daylit bar to, stated one file over: twice the daylit reach.
    lit = DAYLIT_DEPTH_PER_STOREY * (frame.storey or 3.0)
    bar_w = min(frame.width * depth, 2.0 * lit)
    bar_d = min(frame.depth * depth, 2.0 * lit)
    share = _clamp(float(op.params.get("height", 1.0)), 0.1, 1.0)
    h = frame.height * share
    # The bars run the full width and meet at the corners. A ring is one
    # structure - CCTV returns its thrust through the opposite leg, which is
    # why its overhang is not a cantilever - and the corner clearance belongs
    # between separate enclosures, not inside a single closed figure. Held
    # apart it reported itself as two buildings, correctly.
    # The four bars are the same height unless the sentence says otherwise.
    # They used to be h, 0.72h, 0.86h and 0.58h, hardcoded - so every ring in
    # the corpus arrived already broken into four heights, and a sentence whose
    # one decisive move was "draw one corner up" had nothing to draw it up
    # against. Looked at full size, CCTV came out as a jumble of bars rather
    # than a ring, and the reason was in the verb, not in the sentence.
    #
    # A ring that wants a step says it: `stack` or `shift` or `lift` aimed at
    # one bar, which is what the corpus does and what `on` is for.
    step = _clamp(float(op.params.get("step", 1.0)), 0.4, 1.0)
    # A ring has a middle, and it is the thing the ring is about.
    frame.regulates("court", Centre((frame.cx, frame.cy), "loop"))
    frame.placements.extend([
        frame.box("bar_n", w=frame.width, d=bar_d, z=0.0, h=h,
                  dy=(frame.depth - bar_d) / 2.0),
        frame.box("bar_s", w=frame.width, d=bar_d, z=0.0, h=h * step,
                  dy=-(frame.depth - bar_d) / 2.0),
        frame.box("bar_e", w=bar_w, d=frame.depth, z=0.0, h=h,
                  dx=(frame.width - bar_w) / 2.0),
        frame.box("bar_w", w=bar_w, d=frame.depth, z=0.0, h=h * step,
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
        # Where the tie sits is the whole reading. It is Kanazawa's roof and
        # Grace Farms' ribbon - the comment said so and the code put it on the
        # ground at z=0, which is a plinth. A plinth fills the lanes: judging
        # the delivered field, four independent readers wrote "the continuous
        # plinth binds them and no street reads through", "they sit on one
        # continuous podium, so the leftover space is slab, not garden" and
        # "the podium slightly blunts their separateness" - for
        # `nishizawa_towada`, `sejima_inujima_art_houses` and
        # `kr_gusandong_library_of_five_houses`, whose sentences are all about
        # what runs between the volumes.
        #
        # Lifted to the top of the shortest object it is a canopy: every object
        # reaches it, the ground between them stays open, and the sentence
        # `big_bay_view_canopy` writes - three separate low buildings held
        # together not by touching but by one thin roof plane lifted clear above
        # all of them - becomes sayable rather than approximated.
        shortest = frame.height * share * (0.55 + 0.45 / spread)
        frame.placements.append(
            # A boundary, not a room, so it is exempt from the one-storey floor
            # for the same reason a support is. Held to a storey it grew as
            # thick as the objects it binds and swallowed them, and a `taper`
            # aimed at one of them then changed the compiled mass by nothing.
            frame.box("field_plate", w=frame.width, d=frame.depth,
                      z=max(0.0, shortest - frame.height * tie * 0.5),
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
        # And a bearing, which is the third property an object has and the only
        # one this verb left uniform. The argument in the docstring above - that
        # identical objects are the barracks again - was being applied to size
        # and to position and not to which way a thing faces. Measured over the
        # delivered sixteen, fifteen carried exactly one bearing in the entire
        # mass, which is what reads as a stack of bricks.
        #
        # Silent unless the sentence asks: a loose settlement is a claim about
        # this building, not a property of every field. Moriyama and the Inujima
        # houses sit askew of one another; Kanazawa's boxes do not.
        #
        # It is a parameter and not a verb on purpose. A turn written as its own
        # word costs the sentence a word, and `spoken_force` is the mean redraw
        # per word - measured, adding a `rotate` to ACC Gwangju drops it from
        # 0.303 to 0.283 even at 45 degrees, so the selector would refuse every
        # sentence that tried to stop looking like a brick.
        turn = float(op.params.get("turn", 0.0))
        turn *= (1 if (column * 2 + row) % 3 else -1)
        turn *= 0.4 + 0.6 * (index / max(count - 1, 1))
        frame.placements.append(
            frame.box(
                f"object_{index}",
                w=w, d=d, z=0.0,
                h=frame.height * share * (0.55 + 0.45 * scale),
                dx=(column + 0.5 + drift) * cell_w - frame.width / 2.0,
                dy=(row + 0.5 - drift) * cell_d - frame.depth / 2.0,
                turn=turn,
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
    # The book's own operation list runs to thirty and this grammar spoke nine
    # of them. These five ask nothing new of the machinery - the rotation and
    # lean terms have been in `place` since it was written, `form.stack` has
    # carried `twist_degrees` since it was written, and both were dead. What
    # was missing was a word.
    "notch": _notch,
    "puncture": _puncture,
    "twist": _twist,
    # Grade is the book's stepped profile, and the only way this grammar can
    # say a terraced section. `skew` leans a prism and `taper` narrows on every
    # side; neither is a slope you can stand on.
    "grade": _grade,
    # Verbs that are one matrix on volumes already standing live in `ops.affine`
    # and are written as (which volumes, which operator, about what pivot). The
    # ones above bring volumes into being or cut them, which is a different kind
    # of statement and stays here until it has a module of its own.
    **AFFINE_VERBS,
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
