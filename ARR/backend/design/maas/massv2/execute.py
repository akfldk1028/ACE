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
from typing import Any

from shapely.geometry import Polygon

from .form import MatrixForm, Placement, place
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


class _Frame:
    """The site's own box, and the volumes standing in it so far."""

    def __init__(self, buildable: Polygon, axis: tuple[float, float], height_m: float):
        cx, cy, width, depth, rotation = seed_rectangle(buildable, axis)
        self.cx, self.cy = cx, cy
        self.width, self.depth = width, depth
        self.rotation = rotation
        self.height = height_m
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
        plan: str = "square",
    ) -> Placement:
        """A volume centred on the site frame, offset in the frame's own axes."""

        return place(
            role,
            size=(max(w, 0.5), max(d, 0.5), max(h, 0.5)),
            at=(self.cx + dx - w / 2.0, self.cy + dy - d / 2.0, z),
            rotation_degrees=self.rotation,
            kind=kind,
            plan=plan,
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
    built work.
    """

    picked, rest = _scope(frame, op)
    if not picked:
        return
    ratio = _clamp(float(op.params.get("ratio", 0.62)), 0.3, 0.75)
    ux, uy = _direction(frame, op.params.get("along"))
    names = (str(op.params.get("first") or "part_a"), str(op.params.get("second") or "part_b"))
    gap = float(op.params.get("gap", 0.0)) * JOINT_CLEARANCE_M

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
            made.append(
                frame.box(
                    name,
                    w=size if abs(ux) >= abs(uy) else span_x,
                    d=span_y if abs(ux) >= abs(uy) else size,
                    z=low, h=high - low,
                    dx=cx - frame.cx + (ux * shift if abs(ux) >= abs(uy) else 0.0),
                    dy=cy - frame.cy + (uy * shift if abs(uy) > abs(ux) else 0.0),
                    kind=item.kind,
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
        frame.placements.append(
            frame.box(f"tier_{index}", w=w, d=d, z=z, h=tier_h * 1.02,
                      dx=ux * (frame.width - w) / 2.0,
                      dy=uy * (frame.depth - d) / 2.0)
        )
        z += tier_h
        w, d = w / contrast, d / contrast


def _taper(frame: _Frame, op: Operation) -> None:
    """Pull the top in. Applies to whatever is standing, not to a new volume."""

    ratio = _clamp(float(op.params.get("ratio", 0.7)), 0.3, 0.95)
    picked, rest = _scope(frame, op)
    if not picked:
        return
    tops = sorted(picked, key=lambda item: item.z_span()[0])
    keep = tops[:-1]
    highest = tops[-1]
    low, high = highest.z_span()
    cx, cy, span_x, span_y = _bounds_of([highest])
    frame.placements = rest + keep + [
        frame.box(
            highest.role,
            w=span_x * ratio,
            d=span_y * ratio,
            z=low,
            h=high - low,
            dx=cx - frame.cx,
            dy=cy - frame.cy,
        )
    ]


def _shear(frame: _Frame, op: Operation) -> None:
    """Displace the upper volumes, by a fraction of their own dimension.

    The magnitude is the corpus's and is clamped to it; the direction is the
    author's. Sliding every volume by the same absolute distance is what makes
    a shifted stack read as a stack that slipped rather than one that was
    moved.
    """

    ratio = _clamp(float(op.params.get("ratio", 0.26)), MIN_OFFSET_RATIO, MAX_OFFSET_RATIO)
    ux, uy = _direction(frame, op.params.get("toward"))
    picked, rest = _scope(frame, op)
    if not picked:
        return
    ordered = sorted(picked, key=lambda item: item.z_span()[0])
    moved: list[Placement] = []
    for index, item in enumerate(ordered):
        if index == 0:
            moved.append(item)
            continue
        low, high = item.z_span()
        corners = item.corners()
        span_x = max(x for x, _y, _z in corners) - min(x for x, _y, _z in corners)
        span_y = max(y for _x, y, _z in corners) - min(y for _x, y, _z in corners)
        reach = ratio * (span_x if abs(ux) >= abs(uy) else span_y) * index
        moved.append(
            frame.box(item.role, w=span_x, d=span_y, z=low, h=high - low,
                      dx=ux * reach, dy=uy * reach)
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
    """Raise what is standing and put a smaller thing under it."""

    picked, rest = _scope(frame, op)
    if not picked:
        return
    clearance = _clamp(float(op.params.get("clearance", 0.22)), 0.1, 0.4) * frame.height
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
                      kind=item.kind)
        )
    # Four supports, a third of the plan each, so what is raised spans between
    # neighbours rather than corner to corner. Two of them left a slab spanning
    # 632 times its own depth, which the span rule refused and was right to.
    leg = 0.32
    base_x, base_y, base_w, base_d = _bounds_of(picked)
    frame.placements = rest + raised + [
        frame.box("support", w=frame.width * leg, d=frame.depth * leg,
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

    count = int(_clamp(float(op.params.get("n", 4)), 2, 6))
    spread = max(MIN_TIER_CONTRAST, float(op.params.get("spread", 1.6)))
    share = _clamp(float(op.params.get("height", 0.8)), 0.1, 1.0)
    positions = [(-1, -1), (1, 1), (1, -1), (-1, 1), (0, 1), (-1, 0)][:count]
    size = 0.34
    # The boundary that makes a field one building. Kanazawa's boxes sit under
    # a single roof and Zollverein's rooms inside one cube; without it the
    # objects are what the gate said they were, five buildings on one parcel.
    tie = _clamp(float(op.params.get("tie", 0.18)), 0.08, 0.4)
    frame.placements.append(
        frame.box("field_plate", w=frame.width, d=frame.depth, z=0.0,
                  h=frame.height * tie)
    )
    for index, (sx, sy) in enumerate(positions):
        scale = size / (spread ** (index / max(count - 1, 1)))
        w, d = frame.width * scale, frame.depth * scale
        frame.placements.append(
            frame.box(
                f"object_{index}",
                w=w, d=d, z=0.0,
                h=frame.height * share / (1.0 + index * 0.3),
                dx=sx * (frame.width / 2.0 - w / 2.0 - JOINT_CLEARANCE_M) * 0.82,
                dy=sy * (frame.depth / 2.0 - d / 2.0 - JOINT_CLEARANCE_M) * 0.82,
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
) -> MatrixForm | None:
    """Turn a sentence into placed volumes on this parcel."""

    frame = _Frame(buildable, axis, height_m)
    for op in parti.ops:
        handler = _VERBS.get(op.verb)
        if handler is not None:
            handler(frame, op)
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


__all__ = ["execute"]
