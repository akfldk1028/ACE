"""The book's Intersect: a second volume driven through what is standing.

"관통 교차하다 - 두 볼륨을 서로 관통시킴". Both volumes stay solid - this is
not a cut. Puncture takes material away; Intersect adds a body that passes
through and sticks out both sides, which is Kunsthal's ramp, CCTV's sky lobby,
Vitra's stair bar. The corpus has wanted this word for three sessions: the
Kunsthal sentence wrote "경사로가 상자를 관통하며" and the screen flagged 관통
as a claim no verb could carry, so the sentence had to be rewritten to say
less than the building does.

The bar is aimed and sized off the target's own matrix corners - which
volumes, which operator, about what point - and built through `frame.box`,
which is already one matrix composition. A climbing pierce is banded along its
own length with the same `_slab(axis=0)` discipline as `bend`: each segment a
flight, translated up in the bar's own unit space, so the ramp is flats of
real floor rather than a smoothed lie. The stepping is honest: these are the
landings a built ramp has, not an approximation of a plane the language
cannot say.
"""

from __future__ import annotations

from math import cos, radians, sin
from typing import Callable

from design.maas.geometry_language.affine_matrix import translation_matrix4

from .swept import _banded, _clamp


def intersect(frame, op) -> None:
    """Drive a bar through the picked volumes, out both sides."""

    picked, rest = frame.pick(op)
    if not picked:
        return

    # The target's own extent, from its corners. World coordinates, because
    # the bar is aimed across several volumes at once and their shared frame
    # is the world; the pose goes back through `frame.box`, which converts.
    #
    # Additive corners only. A subtractive cutter overshoots on purpose - carve
    # writes z=-height so its cut reaches cleanly through the ground face - and
    # measuring it put this bar's base at -12 m: the ramp pierced the basement
    # of a building that has none, and the diff gate read the whole compile
    # shifting by a storey. What a pierce crosses is what is standing.
    solid = [item for item in picked if item.kind == "additive"] or picked
    corners = [corner for item in solid for corner in item.corners()]
    xs = [x for x, _y, _z in corners]
    ys = [y for _x, y, _z in corners]
    zs = [z for _x, _y, z in corners]
    centre_x, centre_y = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    base, crest = min(zs), max(zs)

    turn = _clamp(float(op.params.get("degrees", 25.0)), -60.0, 60.0)
    bearing = radians(frame.rotation + turn)
    along = (cos(bearing), sin(bearing))
    across = (-along[1], along[0])

    def _extent(direction) -> float:
        values = [x * direction[0] + y * direction[1] for x, y in zip(xs, ys)]
        return max(values) - min(values)

    # Long enough to stick out both ends - a pierce that stops inside the mass
    # is an embed, which is a different word in the book.
    length = _extent(along) * 1.15
    width = _clamp(float(op.params.get("size", 0.25)), 0.12, 0.45) * _extent(across)
    thick = max(frame.storey, 0.5)

    # Where it passes, and whether it climbs. `level` is a share of the height
    # left after the bar's own thickness and rise are spent, so 0 grazes the
    # ground and 1 grazes the roof whatever the other two are.
    climb = _clamp(float(op.params.get("climb", 0.0)), 0.0, 1.0)
    rise = climb * max(0.0, (crest - base) - thick)
    level = _clamp(float(op.params.get("level", 0.35)), 0.0, 1.0)
    z_base = base + level * max(0.0, (crest - base) - thick - rise)

    role = str(op.params.get("first") or "pierce")
    dx, dy = frame.local(centre_x, centre_y)
    bar = frame.box(role, w=length, d=width, z=z_base, h=thick,
                    dx=dx, dy=dy, turn=turn)

    if rise <= 1e-6:
        made = [bar]
    else:
        # Flights: the bar sliced along its own length, each segment lifted a
        # step further in its own unit space. One flight per storey of rise.
        flights = int(_clamp(round(rise / max(frame.storey, 1.0)) + 1, 2, 6))

        def shape(index: int, t: float):
            return translation_matrix4((0.0, 0.0, rise * (index / (flights - 1)) / thick))

        made = _banded(bar, flights, shape, axis=0)

    frame.placements = rest + picked + made


PIERCING_VERBS: dict[str, Callable] = {
    "intersect": intersect,
}


__all__ = ["PIERCING_VERBS", "intersect"]
