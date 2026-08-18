"""Verbs whose transform varies with height: a matrix per storey band.

A single 4x4 is linear, so a taper, a twist or a stair cannot be one matrix -
but each *band* of one can. The old implementations knew that and built the
bands by hand: read the volume's bounds, compute a width, a centre and an
offset, and ask the frame for new boxes. Every coordinate bug this package has
had came out of exactly that arithmetic - `_bounds_of` measured on world axes,
`_taper` and `_twist` handing world corners to `stack` after the axes changed,
`_grade` rebuilding from an axis-aligned box and inflating with the parcel's
bearing, `_shear` forgetting to add a volume's own position back and
teleporting it to the frame centre.

None of that arithmetic exists here. A band is derived from the volume's own
matrix in unit space - slice the unit cube, then let the matrix it already
carries put the slice where the volume already is:

    band_i  =  slab(i, n) . item.matrix

and the shaping transform is composed either in unit space (scales, which then
act along the volume's own axes whatever the parcel's bearing - rotation
invariance by construction) or in world space about a pivot taken from the
volume's own matrix (rotations, which must preserve angles and therefore
cannot be composed in a normalized space).

Which volumes, which operator, about what point. Same contract as `affine`.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from design.maas.floor_viability import DEFAULT_MINIMUM_CLEAR_DEPTH_M
from design.maas.geometry_language.affine_matrix import (
    Matrix4,
    compose_matrix4,
    rotation_matrix4,
    scale_matrix4,
    transform_point3,
    translation_matrix4,
    validate_matrix4,
)

from ..form import Placement


def _clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def _slab(index: int, count: int) -> Matrix4:
    """The i-th of n equal z-bands of the unit cube, said in unit space."""

    return compose_matrix4(
        scale_matrix4((1.0, 1.0, 1.0 / count)),
        translation_matrix4((0.0, 0.0, index / count)),
    )


def _about_unit(pivot: tuple[float, float, float], operator: Matrix4) -> Matrix4:
    """An operator applied about a unit-space point."""

    return compose_matrix4(
        translation_matrix4((-pivot[0], -pivot[1], -pivot[2])),
        operator,
        translation_matrix4(pivot),
    )


def _banded(
    item: Placement,
    count: int,
    shape: Callable[[int, float], Matrix4 | None],
) -> list[Placement]:
    """Slice one volume into bands and shape each with its own matrix.

    `shape` receives the band index and its midpoint as a 0..1 share of the
    volume's height, and returns a unit-space matrix - or None to end the
    series, which is how a stair stops when the building runs out of plan.
    """

    made: list[Placement] = []
    for index in range(count):
        t = (index + 0.5) / count
        shaping = shape(index, t)
        if shaping is None:
            break
        matrix = compose_matrix4(_slab(index, count), shaping, item.matrix)
        made.append(replace(item, matrix=validate_matrix4(matrix)))
    return made


def _storeys(item: Placement, storey_m: float, low: int, high: int) -> int:
    z0, z1 = item.z_span()
    return int(_clamp(round((z1 - z0) / max(storey_m, 1.0)), low, high))


def _span_along_unit_axis(item: Placement, axis: int) -> float:
    """The volume's own width along one of its own axes, in metres.

    Read off the matrix, not off a bounding box: the length of the image of a
    unit step along that axis. This is what makes every threshold here mean
    the same thing at any bearing.
    """

    origin = transform_point3(item.matrix, (0.0, 0.0, 0.0))
    step = [0.0, 0.0, 0.0]
    step[axis] = 1.0
    tip = transform_point3(item.matrix, tuple(step))
    return sum((a - b) ** 2 for a, b in zip(tip, origin)) ** 0.5


def _along_is_x(params: dict) -> bool:
    named = str(params.get("toward") or params.get("along") or "long").lower()
    return named not in ("cross", "short", "side")


def taper(frame, op) -> None:
    """Draw the plan in as it rises, about each volume's own centre.

    The taper runs over the picked set as a whole - each volume takes the part
    of the ramp its own z-range spans, so a tall object narrows more than a
    short one beside it and both belong to one silhouette.
    """

    ratio = _clamp(float(op.params.get("ratio", 0.7)), 0.3, 0.95)
    picked, rest = frame.pick(op)
    if not picked:
        return
    base = min(item.z_span()[0] for item in picked)
    crest = max(item.z_span()[1] for item in picked)
    span = max(crest - base, 1e-6)

    made: list[Placement] = []
    for item in picked:
        z0, z1 = item.z_span()
        count = _storeys(item, frame.storey, 2, 8)

        def shape(index: int, t: float, z0=z0, z1=z1, count=count) -> Matrix4:
            z = z0 + (z1 - z0) * t
            scale = 1.0 + (ratio - 1.0) * _clamp((z - base) / span, 0.0, 1.0)
            return _about_unit(
                (0.5, 0.5, 0.0), scale_matrix4((scale, scale, 1.0))
            )

        made.extend(_banded(item, count, shape))
    frame.placements = rest + made


def twist(frame, op) -> None:
    """Turn the plan progressively as it rises, about each volume's own axis.

    The turn is composed in world space, because rotation is the one transform
    a normalized space would distort - a turn in unit coordinates of a bar is
    a smear. The pivot is the volume's own plan centre, read off its matrix.
    """

    turn = _clamp(float(op.params.get("degrees", 30.0)), 5.0, 90.0)
    picked, rest = frame.pick(op)
    if not picked:
        return

    made: list[Placement] = []
    for item in picked:
        count = _storeys(item, frame.storey, 3, 10)
        pivot = transform_point3(item.matrix, (0.5, 0.5, 0.0))

        def shape(index: int, t: float) -> Matrix4:
            return compose_matrix4()  # identity; the turn is world-side below

        for index, band in enumerate(_banded(item, count, shape)):
            angle = turn * ((index + 0.5) / count)
            world = compose_matrix4(
                translation_matrix4((-pivot[0], -pivot[1], 0.0)),
                rotation_matrix4((0.0, 0.0, angle)),
                translation_matrix4((pivot[0], pivot[1], 0.0)),
            )
            made.append(replace(
                band, matrix=validate_matrix4(compose_matrix4(band.matrix, world))
            ))
    frame.placements = rest + made


def grade(frame, op) -> None:
    """Cut it back a step at a time, holding one face still.

    The scale is composed in unit space, so it acts along the volume's own
    axis whatever the parcel's bearing - the fault the old implementation had
    to be taught out of twice, once for the stride and once for the bbox. The
    stair simply stops where the building runs out of room: a terrace narrower
    than a room is not a terrace.
    """

    run = _clamp(float(op.params.get("run", 0.6)), 0.2, 0.9)
    picked, rest = frame.pick(op)
    if not picked:
        return
    along_x = _along_is_x(op.params)
    axis = 0 if along_x else 1

    made: list[Placement] = []
    for item in picked:
        count = int(_clamp(
            _storeys(item, frame.storey, 2, 8),
            2, int(_clamp(float(op.params.get("steps", 6)), 2, 8)),
        ))
        full = _span_along_unit_axis(item, axis)
        across = _span_along_unit_axis(item, 1 - axis)

        def shape(index: int, t: float, count=count) -> Matrix4 | None:
            keep = 1.0 - run * index / max(count - 1, 1)
            if full * keep <= DEFAULT_MINIMUM_CLEAR_DEPTH_M or across <= DEFAULT_MINIMUM_CLEAR_DEPTH_M:
                return None
            # The high side stands still: pivot on the face at unit 0 of the
            # graded axis, so the low side is what steps back.
            vector = (keep, 1.0, 1.0) if along_x else (1.0, keep, 1.0)
            return _about_unit((0.0, 0.0, 0.0), scale_matrix4(vector))

        made.extend(_banded(item, count, shape))
    frame.placements = rest + made


def shear(frame, op) -> None:
    """Displace the upper volumes, each by a step of its own dimension.

    One translation per volume, composed onto the matrix it already carries -
    so a volume keeps where it stood, which is the invariant the old
    implementation broke by rebuilding through `frame.box` without adding the
    volume's own offset back. The anchor rule is unchanged: a stack slips past
    the volume it stands on; a set standing at one level has nothing above it
    to slip past, so everything picked moves.
    """

    from ..grammar import MAX_OFFSET_RATIO, MIN_OFFSET_RATIO

    ratio = _clamp(float(op.params.get("ratio", 0.26)), MIN_OFFSET_RATIO, MAX_OFFSET_RATIO)
    picked, rest = frame.pick(op)
    if not picked:
        return
    ux, uy = frame.out(*frame.direction(op.params.get("toward")))
    ordered = sorted(picked, key=lambda item: item.z_span()[0])
    levels = {round(item.z_span()[0], 3) for item in ordered}
    anchored = 0 if len(levels) > 1 else -1

    moved: list[Placement] = []
    for index, item in enumerate(ordered):
        if index == anchored:
            moved.append(item)
            continue
        axis = 0 if abs(ux) >= abs(uy) else 1
        reach = ratio * _span_along_unit_axis(item, axis) * (index - anchored)
        slide = translation_matrix4((ux * reach, uy * reach, 0.0))
        moved.append(replace(
            item, matrix=validate_matrix4(compose_matrix4(item.matrix, slide))
        ))
    frame.placements = rest + moved


SWEPT_VERBS: dict[str, Callable] = {
    "taper": taper,
    "twist": twist,
    "grade": grade,
    "shear": shear,
}


__all__ = ["SWEPT_VERBS"]
