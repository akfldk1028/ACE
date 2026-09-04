"""Make the parts land on a few lines, instead of only measuring whether they did.

`composition.py` reads the Akin-Moustapha finding - a small set of regulating
elements explains where every part sits - and scores a mass on it. Scoring is
half the idea. The architects they watched did not measure alignment after the
fact; they DREW to axes, and that is why the results read as one thing.

A generated mass has every part almost aligned: a bar's face lands 0.7 m off
its neighbour's, a tier's top sits 0.4 m above a storey line, a wing is turned
1.6 degrees off the parcel. None of it is wrong enough to fail a gate and all
of it is visible - it is exactly the difference between a drawing that reads
as disciplined and one that reads as approximate. The architect's word for
what is missing is 정갈함.

So this snaps what is nearly true into being true:

  * bearings, to the axes the composition already commits to (the parcel's own
    open-side direction and the leading body's), within a few degrees;
  * faces, to the lines a face of the leading body already occupies;
  * heights, to whole storeys.

It moves nothing far. The tolerance is the width of the slack a random
parameter leaves, not a design decision: a part that genuinely sits at its own
angle keeps it, because it is further off than the tolerance. And it runs
BEFORE the legal fit, so the envelope still has the last word on what stands.
"""

from __future__ import annotations

from dataclasses import replace
from math import atan2, cos, degrees, radians, sin

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    rotation_matrix4,
    translation_matrix4,
    validate_matrix4,
)

from .compile import _plan
from .form import MatrixForm, Placement

# How far a face may be nudged to reach a line another part already occupies.
# Wider than this and the part was not "nearly aligned", it was somewhere else,
# and moving it would be a design decision rather than a tidying.
FACE_SNAP_M = 1.2

# The same for a bearing. A part turned less than this off an axis the
# composition already uses reads as a failed attempt at that axis; past it, it
# reads as a deliberate turn - the pinwheel and the splayed wing both live out
# here and must survive untouched.
BEARING_SNAP_DEG = 4.0

# And for a level: a top or a base within this of a storey line is a storey
# line that missed. Half a storey would be a different room height; a fifth is
# the slack a growth loop leaves behind.
LEVEL_SNAP_SHARE = 0.2


def _bearing(placement: Placement) -> float:
    """The placement's own plan bearing, folded into [0, 180)."""

    ring = list(_plan(placement).exterior.coords)
    best, length = 0.0, 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if run > length:
            best, length = degrees(atan2(y1 - y0, x1 - x0)) % 180.0, run
    return best


def _turned(placement: Placement, delta_deg: float) -> Placement:
    """Turn a placement about its own plan centre."""

    if abs(delta_deg) < 1e-9:
        return placement
    centre = _plan(placement).centroid
    matrix = compose_matrix4(
        placement.matrix,
        translation_matrix4((-centre.x, -centre.y, 0.0)),
        rotation_matrix4((0.0, 0.0, delta_deg)),
        translation_matrix4((centre.x, centre.y, 0.0)),
    )
    return replace(placement, matrix=validate_matrix4(matrix))


def _moved(placement: Placement, dx: float, dy: float, dz: float = 0.0) -> Placement:
    if abs(dx) < 1e-9 and abs(dy) < 1e-9 and abs(dz) < 1e-9:
        return placement
    return replace(placement, matrix=validate_matrix4(compose_matrix4(
        placement.matrix, translation_matrix4((dx, dy, dz)))))


def _offsets_along(placement: Placement, normal: tuple[float, float]) -> list[float]:
    """Where this placement's faces sit along a normal direction."""

    nx, ny = normal
    return sorted({round(x * nx + y * ny, 3)
                   for x, y in _plan(placement).exterior.coords})


def regulated(form: MatrixForm, *, axis: tuple[float, float] | None = None,
              storey_m: float = 0.0) -> MatrixForm:
    """Snap near-alignments true: bearings, faces, then levels.

    `axis` is the parcel's open-side direction when the caller has one - the
    composition's outermost regulating element, and the one an architect
    draws to first.
    """

    additive = [item for item in form.placements if item.kind == "additive"]
    if len(additive) < 2:
        return form

    lead = max(additive, key=lambda item: _plan(item).area)
    axes = [_bearing(lead)]
    if axis is not None:
        axes.append(degrees(atan2(axis[1], axis[0])) % 180.0)

    items = list(form.placements)

    # 1. Bearings. A part within the tolerance of an axis the composition
    #    already commits to is turned onto it.
    for index, item in enumerate(items):
        if item is lead or item.kind != "additive":
            continue
        own = _bearing(item)
        for target in axes:
            turn = (target - own + 90.0) % 180.0 - 90.0
            if abs(turn) <= BEARING_SNAP_DEG:
                items[index] = _turned(item, turn)
                break

    # 2. Faces. The lines the leading body occupies are the composition's
    #    regulating elements; every other part's nearest face joins one when
    #    it is already close.
    for target in axes:
        normal = (cos(radians(target + 90.0)), sin(radians(target + 90.0)))
        lines = _offsets_along(lead, normal)
        if not lines:
            continue
        for index, item in enumerate(items):
            if item is lead or item.kind != "additive":
                continue
            own = _offsets_along(item, normal)
            best = None
            for face in own:
                for line in lines:
                    shift = line - face
                    if abs(shift) <= FACE_SNAP_M and (
                            best is None or abs(shift) < abs(best)):
                        best = shift
            if best is not None:
                items[index] = _moved(item, normal[0] * best, normal[1] * best)

    # 3. Levels. A base or a top within a fifth of a storey of a storey line
    #    is that line, so tiers read as floors rather than as near-misses.
    if storey_m > 1e-6:
        slack = LEVEL_SNAP_SHARE * storey_m
        for index, item in enumerate(items):
            if item.kind != "additive":
                continue
            low, _high = item.z_span()
            if low <= 1e-6:
                continue
            nearest = round(low / storey_m) * storey_m
            if 0.0 < abs(nearest - low) <= slack:
                items[index] = _moved(items[index], 0.0, 0.0, nearest - low)

    return replace(form, placements=tuple(items))
