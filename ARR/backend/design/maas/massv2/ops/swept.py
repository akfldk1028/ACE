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


def _slab(index: int, count: int, axis: int = 2) -> Matrix4:
    """The i-th of n equal bands of the unit cube along one axis, in unit space.

    Axis 2 slices by height, which is what a taper or a twist wants. Axis 0
    slices by length, which is what the book's Bend and Pinch want - both act
    along a bar, not up it. Same discipline either way: the band is a piece of
    the unit cube and the volume's own matrix puts it where the volume already
    is, so nothing here knows or cares which way the parcel faces.
    """

    scale = [1.0, 1.0, 1.0]
    scale[axis] = 1.0 / count
    offset = [0.0, 0.0, 0.0]
    offset[axis] = index / count
    return compose_matrix4(
        scale_matrix4(tuple(scale)),
        translation_matrix4(tuple(offset)),
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
    axis: int = 2,
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
        matrix = compose_matrix4(_slab(index, count, axis), shaping, item.matrix)
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

    # `smooth: true` keeps the volume whole and tilts its top instead of
    # cutting steps. This is the word CopenHill's sentence needed from the
    # start - "지붕이 정상에서 지면까지 끊기지 않고 내려온다" - and a staircase
    # could only approximate it, worse the finer it stepped. The tilt is a
    # term on the volume (`top_drop`, along the volume's own axis said in
    # world), the compiler carries it to the top band, the renderer draws it,
    # and the law still counts the full prism, which is the stricter reading.
    if bool(op.params.get("smooth")):
        # Signed, so "toward: back" tilts the other way - the first version
        # used the unsigned axis and a roof asked to rise toward the
        # neighbours fell toward them instead. "corner" is the diagonal: BIG's
        # most frequent single move (the survey counted corner pull five times
        # in sixteen works) is one corner drawn up while the plan stays
        # orthogonal, and a planar top through the diagonal is exactly that.
        named = str(op.params.get("toward") or "long").lower()
        if named in ("corner", "diagonal"):
            fx, fy = 1.0, 1.0
        else:
            fx, fy = frame.direction(op.params.get("toward"))
        direction = frame.out(fx, fy)
        length = (direction[0] ** 2 + direction[1] ** 2) ** 0.5 or 1.0
        unit = (direction[0] / length, direction[1] / length)
        frame.placements = rest + [
            replace(item, top_drop=run, drop_toward=unit) for item in picked
        ]
        return

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
    # A derived body is not a tier. Verbs name what they make after the volume
    # they made it for - `tier_2_support`, `bar_nested` - and the scope brings
    # those bodies along, which is right. But this verb grades displacement by
    # stacking order, and counted as steps of the stair the four legs under
    # Maison Bordeaux's raised tier took indices 0-3, each slid a different
    # amount, and the plate slid off all of them: 3 of 22 occupiable fell to
    # 0 of 18 the day the legs learned to follow. An attachment rides its
    # owner rigidly - the grading is over owners alone.
    primary = [
        item for item in picked
        if not any(
            other is not item and item.role.startswith(other.role + "_")
            for other in picked
        )
    ]
    primary_ids = {id(item) for item in primary}
    ordered = sorted(primary, key=lambda item: item.z_span()[0])
    levels = {round(item.z_span()[0], 3) for item in ordered}
    anchored = 0 if len(levels) > 1 else -1

    moved: list[Placement] = []
    slides: dict[str, tuple[float, float]] = {}
    for index, item in enumerate(ordered):
        if index == anchored:
            moved.append(item)
            slides.setdefault(item.role, (0.0, 0.0))
            continue
        axis = 0 if abs(ux) >= abs(uy) else 1
        reach = ratio * _span_along_unit_axis(item, axis) * (index - anchored)
        slides.setdefault(item.role, (ux * reach, uy * reach))
        slide = translation_matrix4((ux * reach, uy * reach, 0.0))
        moved.append(replace(
            item, matrix=validate_matrix4(compose_matrix4(item.matrix, slide))
        ))
    for item in picked:
        if id(item) in primary_ids:
            continue
        owner = max(
            (role for role in slides if item.role.startswith(role + "_")),
            key=len,
        )
        dx, dy = slides[owner]
        if abs(dx) < 1e-12 and abs(dy) < 1e-12:
            moved.append(item)
            continue
        slide = translation_matrix4((dx, dy, 0.0))
        moved.append(replace(
            item, matrix=validate_matrix4(compose_matrix4(item.matrix, slide))
        ))
    frame.placements = rest + moved


def bend(frame, op) -> None:
    """Kink the bar while keeping it connected - the book's Bend.

    "연결을 유지하며 방향을 꺾음". The volume is sliced along its own length and
    each segment turns a little further about the joint it shares with the one
    before, a forward-kinematic chain: the joint's world position is read off
    the chain built so far, so the pieces stay connected by construction. Two
    segments are the book's single kink; more approach an arc.

    This is the verb `big_vm_houses_orestad` needed all along - its sentence
    says "each part is bent off the axis" and the corpus had to say it with a
    `rotate`, which turns a part in place but cannot kink one.
    """

    turn = _clamp(float(op.params.get("degrees", 25.0)), -60.0, 60.0)
    picked, rest = frame.pick(op)
    if not picked:
        return
    count = int(_clamp(float(op.params.get("segments", 2)), 2, 6))

    made: list[Placement] = []
    for item in picked:
        chain = compose_matrix4()  # identity: the first segment holds still
        step = turn / max(count - 1, 1)
        for index in range(count):
            band = compose_matrix4(_slab(index, count, 0), item.matrix, chain)
            made.append(replace(item, matrix=validate_matrix4(band)))
            joint = transform_point3(
                compose_matrix4(item.matrix, chain),
                ((index + 1) / count, 0.5, 0.0),
            )
            chain = compose_matrix4(
                chain,
                translation_matrix4((-joint[0], -joint[1], 0.0)),
                rotation_matrix4((0.0, 0.0, step)),
                translation_matrix4((joint[0], joint[1], 0.0)),
            )
    frame.placements = rest + made


def pinch(frame, op) -> None:
    """Narrow the middle from both sides - the book's Pinch.

    "중앙 양측을 깎아 좁힘". Sliced along the length, each segment scaled across
    itself about its own centreline, deepest at the middle of the run - a
    triangular waist, which is what a prism language can say of one. Eight
    House is pinched across its waist and not around it: this is the verb that
    sentence used `compress` as a stand-in for.
    """

    # Up to 0.9: at 0.7 a ring's bars pull toward each other and stop short,
    # which is a waist; past ~0.8 their inner faces cross and the figure closes
    # into two courts, which is what 8 House's sentence actually claims.
    depth = _clamp(float(op.params.get("ratio", 0.4)), 0.15, 0.9)
    picked, rest = frame.pick(op)
    if not picked:
        return
    across_y = _along_is_x(op.params)

    # The composition's own centreline and run, for the bow below. Thinning
    # each volume about itself is a notch, and two judges called it exactly
    # that - "the waist pressed to ground is barely a notch, not a split". A
    # waist is the whole figure drawing in: every band is also pulled toward
    # the centreline by how deep the waist is at its station along the run,
    # so a ring's long sides bow together at the middle the way 8 House's do.
    # A single centred volume has no offset from the centreline, so the bow
    # is silently the old pure thinning there.
    solid = [item for item in picked if item.kind == "additive"] or picked
    corners = [corner for item in solid for corner in item.corners()]
    run_dir = frame.out(1.0, 0.0) if across_y else frame.out(0.0, 1.0)
    across_dir = (-run_dir[1], run_dir[0])
    stations = [x * run_dir[0] + y * run_dir[1] for x, y, _z in corners]
    run_lo, run_hi = min(stations), max(stations)
    run_span = max(run_hi - run_lo, 1e-9)
    centre_across = sum(
        x * across_dir[0] + y * across_dir[1] for x, y, _z in corners
    ) / max(len(corners), 1)

    made: list[Placement] = []
    for item in picked:
        # Only volumes that actually run with the waist are banded. A ring's
        # end bars lie across the run: banding them slices them across their
        # own width and the waist thins them along the run, which punched four
        # pinholes into the corners of the drawing. Direction cannot tell the
        # bars apart - every box a frame poses has its unit-x on the frame's
        # long axis and the bars differ by proportion, not bearing - so the
        # test is proportion: a volume is banded when it is longer along the
        # run than across it. The end bars are held anyway by the bowing bars
        # meeting them, since the pull is zero at the run's ends.
        along_run = _span_along_unit_axis(item, 0 if across_y else 1)
        across_run = _span_along_unit_axis(item, 1 if across_y else 0)
        if along_run < across_run:
            made.append(item)
            continue
        # A bar standing off the centreline bows; a bar standing on it thins.
        # Both at once cancel: thinned to 0.15 of its width at the waist, a
        # bowed bar's inner face retreats as fast as its centre advances, and
        # a ring asked to close into two courts still read one - measured at
        # 0.85 with the peak on a boundary, gap 3.96 m. 8 House's bars keep
        # their width and bend; a bowtie's single centred slab keeps its place
        # and narrows. The volume's own offset says which it is.
        item_centre = transform_point3(item.matrix, (0.5, 0.5, 0.0))
        item_offset = abs(
            (item_centre[0] * across_dir[0] + item_centre[1] * across_dir[1])
            - centre_across
        )
        bows = item_offset > 0.25 * max(across_run, 1e-9)
        count = int(_clamp(float(op.params.get("segments", 6)), 3, 8))
        # An even count, always: the waist's deepest point is t = 0.5, and the
        # bow interpolates linearly inside each band, so the peak is only
        # reached if a band boundary lands on it. Five segments put t = 0.5
        # mid-band and the chord undershot the pull by a fifth - a ring asked
        # to close into two courts at 0.85 still read one court.
        count += count % 2

        def shape(index: int, t: float, bows=bows) -> Matrix4:
            waist = 1.0 if bows else 1.0 - depth * (1.0 - abs(2.0 * t - 1.0))
            # A hair of overlap along the run, so adjacent segments share a
            # face in floating point and not only in mathematics - a rotated
            # pinch union came back as pieces split by 1e-9 slivers. About each
            # band's OWN centre: scaled about the shared centre the joint edges
            # of both neighbours land on the same line and still only touch.
            grip = 1.002
            vector = (grip, waist, 1.0) if across_y else (waist, grip, 1.0)
            pivot = (t, 0.5, 0.0) if across_y else (0.5, t, 0.0)
            return _about_unit(pivot, scale_matrix4(vector))

        a_run, a_across = (0, 1) if across_y else (1, 0)
        for band in _banded(item, count, shape, axis=a_run):
            # The bow varies linearly WITHIN the band, so neighbouring bands
            # meet exactly - a per-band translation stepped the pull 4 m at a
            # joint and the ring came apart into corner-touching pieces. A
            # shear whose lateral term interpolates the pull between the
            # band's own two end stations is C0-continuous by construction,
            # and at the run's ends the waist is 1 so the pull is 0 and the
            # ring's corner bars stay attached without being told to.
            ends = []
            if not bows:
                made.append(band)
                continue
            for x_unit in (0.0, 1.0):
                point = [0.5, 0.5, 0.0]
                point[a_run] = x_unit
                world = transform_point3(band.matrix, tuple(point))
                station = (
                    (world[0] * run_dir[0] + world[1] * run_dir[1]) - run_lo
                ) / run_span
                waist = 1.0 - depth * (1.0 - abs(2.0 * station - 1.0))
                offset = (
                    world[0] * across_dir[0] + world[1] * across_dir[1]
                ) - centre_across
                ends.append(-(1.0 - waist) * offset)
            breadth = max(_span_along_unit_axis(band, a_across), 1e-6)
            slope = (ends[1] - ends[0]) / breadth
            base = ends[0] / breadth
            bow = [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
            bow[a_across][a_run] = slope
            bow[a_across][3] = base
            made.append(replace(
                band,
                matrix=validate_matrix4(compose_matrix4(
                    tuple(tuple(row) for row in bow), band.matrix
                )),
            ))
    frame.placements = rest + made


def gable(frame, op) -> None:
    """A pitched roof: two wedges meeting at a ridge - Herzog's house profile.

    This verb existed once as a staircase and was reverted by measurement: the
    stepped approximation read worse the finer it was cut (5 steps 0.29
    articulation, 24 steps 0.09), and the memory of that revert is why the
    corpus said 박공 with nothing for two sessions. With `top_drop` in the IR
    the roof is two real planes: the volume is halved across the ridge in its
    own unit space and each half's top descends outward from the ridge, so the
    silhouette is the triangle a person draws when asked for a house.

    The ridge runs along the volume's own long axis unless `along: "cross"`.
    Legal counting stays on the full prisms - stricter, as everywhere.

    `pitch` is a slope - rise per unit of run, 1.0 is 45 degrees - not a share
    of the volume's height. As a height share it drew a 45-degree roof on a
    six-metre house bar and a five-degree tilt on a twenty-metre slab from the
    same word: the fused-gables sentence spoke 박공 and delivered a plane. The
    house unit already converts its geometry to a height share before calling
    `gabled_halves` ((d/2)/h); this verb now does the same per volume, capped
    at what the body can hold. And "long" means the volume's actually longer
    world axis, read off its matrix - as a fixed unit axis, a bar built
    deep-in-y wore its ridge across its own body.
    """

    pitch = _clamp(float(op.params.get("pitch", 0.5)), 0.15, 1.2)
    # A wide body wearing ONE ridge is a nearly flat tent; the roof a wide
    # body actually wears is a row of ridges - M-roofs, sawtooth gables,
    # terraced housing. `bays` splits the body across the ridge into that
    # many strips, each a whole primitive with its own ridge, so the row
    # survives every later transform the way one ridge does.
    bays = int(_clamp(float(op.params.get("bays", 1)), 1, 6))
    # Where the ridge sits across the body. 0.5 is the symmetric gable and
    # stays on the ridge primitive; anywhere else is a saltbox - same pitch
    # both sides, the longer side reaching lower - said as a top profile.
    at = _clamp(float(op.params.get("at", 0.5)), 0.15, 0.85)
    picked, rest = frame.pick(op)
    if not picked:
        return
    long_named = _along_is_x({"along": op.params.get("along", "long")})

    def _pitched(volume, across_w: float, body: float, ridge_x: bool) -> list:
        if abs(at - 0.5) < 1e-6:
            share = _clamp((across_w / 2.0) * pitch / body, 0.15, 0.95)
            return gabled_halves(frame, volume, share, ridge_x=ridge_x)
        origin = transform_point3(volume.matrix, (0.0, 0.0, 0.0))
        tip = transform_point3(
            volume.matrix, (0.0, 1.0, 0.0) if ridge_x else (1.0, 0.0, 0.0)
        )
        ax, ay = tip[0] - origin[0], tip[1] - origin[1]
        norm = (ax * ax + ay * ay) ** 0.5 or 1.0
        left = _clamp(pitch * at * across_w / body, 0.0, 0.95)
        right = _clamp(pitch * (1.0 - at) * across_w / body, 0.0, 0.95)
        return [replace(
            volume,
            top_drop=max(left, right),
            drop_toward=None,
            ridge_along=None,
            top_profile=((0.0, 1.0 - left), (at, 1.0), (1.0, 1.0 - right)),
            profile_across=(ax / norm, ay / norm),
        )]

    made: list[Placement] = []
    for item in picked:
        if item.kind != "additive":
            made.append(item)
            continue
        origin = transform_point3(item.matrix, (0.0, 0.0, 0.0))
        tip_x = transform_point3(item.matrix, (1.0, 0.0, 0.0))
        tip_y = transform_point3(item.matrix, (0.0, 1.0, 0.0))
        span_x = ((tip_x[0] - origin[0]) ** 2 + (tip_x[1] - origin[1]) ** 2) ** 0.5
        span_y = ((tip_y[0] - origin[0]) ** 2 + (tip_y[1] - origin[1]) ** 2) ** 0.5
        ridge_x = (span_x >= span_y) if long_named else (span_x < span_y)
        across = span_y if ridge_x else span_x
        low, high = item.z_span()
        body = max(high - low, 1e-6)
        # A slice of a circle is not a smaller circle, so only the square
        # plan family splits into bays; anything else keeps its one ridge.
        rows = bays if bays > 1 and item.plan == "square" else 1
        if rows == 1:
            made.extend(_pitched(item, across, body, ridge_x))
            continue
        axis = 1 if ridge_x else 0
        size = [1.0, 1.0, 1.0]
        size[axis] = 1.0 / rows
        for k in range(rows):
            low_corner = [0.0, 0.0, 0.0]
            low_corner[axis] = k / rows
            strip = replace(
                item,
                role=f"{item.role}_bay{k}",
                matrix=validate_matrix4(compose_matrix4(
                    scale_matrix4(tuple(size)),
                    translation_matrix4(tuple(low_corner)),
                    item.matrix,
                )),
            )
            made.extend(_pitched(strip, across / rows, body, ridge_x))
    frame.placements = rest + made


def _profile_axes(item, long_named: bool):
    """The fold axis choice for a section verb, on the volume's own matrix.

    Returns (ridge_x, across_metres, across_unit_world, body_metres): which
    unit axis the fold runs along, how wide the volume is across it, the
    world direction stations are measured along, and the volume's height.
    """

    origin = transform_point3(item.matrix, (0.0, 0.0, 0.0))
    tip_x = transform_point3(item.matrix, (1.0, 0.0, 0.0))
    tip_y = transform_point3(item.matrix, (0.0, 1.0, 0.0))
    span_x = ((tip_x[0] - origin[0]) ** 2 + (tip_x[1] - origin[1]) ** 2) ** 0.5
    span_y = ((tip_y[0] - origin[0]) ** 2 + (tip_y[1] - origin[1]) ** 2) ** 0.5
    ridge_x = (span_x >= span_y) if long_named else (span_x < span_y)
    tip = tip_y if ridge_x else tip_x
    ax, ay = tip[0] - origin[0], tip[1] - origin[1]
    norm = (ax * ax + ay * ay) ** 0.5 or 1.0
    low, high = item.z_span()
    return ridge_x, (span_y if ridge_x else span_x), (ax / norm, ay / norm), max(high - low, 1e-6)


def butterfly(frame, op) -> None:
    """Two planes falling to an inner valley - the V roof.

    Breuer's Geller House, the section drawn when a house wants its rain in
    the middle and its eyes up at both edges. The valley runs along the
    volume's own long axis unless `along: "cross"`; `at` places it. Said as
    a top profile - the primitive the gable's ridge generalised into - so it
    survives every later transform whole.
    """

    pitch = _clamp(float(op.params.get("pitch", 0.5)), 0.15, 1.2)
    at = _clamp(float(op.params.get("at", 0.5)), 0.2, 0.8)
    picked, rest = frame.pick(op)
    if not picked:
        return
    long_named = _along_is_x({"along": op.params.get("along", "long")})
    made: list[Placement] = []
    for item in picked:
        if item.kind != "additive":
            made.append(item)
            continue
        _rx, across, unit, body = _profile_axes(item, long_named)
        # One valley has one depth: the shorter run sets it, so the declared
        # pitch is the steeper side's and the longer side lies back.
        depth = _clamp(pitch * min(at, 1.0 - at) * across / body, 0.15, 0.95)
        made.append(replace(
            item,
            top_drop=depth,
            drop_toward=None,
            ridge_along=None,
            top_profile=((0.0, 1.0), (at, 1.0 - depth), (1.0, 1.0)),
            profile_across=unit,
        ))
    frame.placements = rest + made


def mansard(frame, op) -> None:
    """Steep shoulders, a near-flat crown - the Haussmann section.

    `shoulder` is how far in from each eave the steep face runs before the
    crown; the crown itself stays level. Four breakpoints of the same top
    profile the gable and the butterfly use.
    """

    pitch = _clamp(float(op.params.get("pitch", 0.8)), 0.15, 1.2)
    shoulder = _clamp(float(op.params.get("shoulder", 0.25)), 0.1, 0.4)
    picked, rest = frame.pick(op)
    if not picked:
        return
    long_named = _along_is_x({"along": op.params.get("along", "long")})
    made: list[Placement] = []
    for item in picked:
        if item.kind != "additive":
            made.append(item)
            continue
        _rx, across, unit, body = _profile_axes(item, long_named)
        # The fold lives at the cornice: a mansard's roof is a storey or two,
        # never half the building. On a wide body a shoulder fraction of the
        # width is tens of metres of run, and the crown collapsed to a tent -
        # so the drop is capped at two storeys and the shoulder is re-read
        # from the declared pitch, which the steep face actually keeps.
        drop_m = min(pitch * shoulder * across, 1.5 * frame.storey)
        share = _clamp(drop_m / body, 0.15, 0.95)
        shoulder_u = min(0.45, max(0.02, (share * body / pitch) / max(across, 1e-6)))
        made.append(replace(
            item,
            top_drop=share,
            drop_toward=None,
            ridge_along=None,
            top_profile=(
                (0.0, 1.0 - share), (shoulder_u, 1.0),
                (1.0 - shoulder_u, 1.0), (1.0, 1.0 - share),
            ),
            profile_across=unit,
        ))
    frame.placements = rest + made


def gabled_halves(frame, item, pitch: float, *, ridge_x: bool = True) -> list:
    """A volume as the archetypal house: ONE volume whose top is a ridge.

    Two earlier representations failed in sequence and both are worth
    remembering. Halving the whole volume made each half a sliver the storey
    gate refused. Keeping the body whole and splitting only the roof drew
    correctly out of the executor - and then a coverage retarget, which
    scales every volume about its own centre, pulled the two roof wedges
    apart into a slot along the ridge. A section is a base shape, not an
    assembly: `ridge_along` says the pentagon on one volume, and one volume
    survives every later transform whole.
    """

    # The ridge runs along the VOLUME's own axis, read off its matrix - a
    # turned bar's ridge turns with it. Read off the frame instead, every
    # unit of a crosswise pile wore a ridge diagonal to its own body, and
    # three gates downstream measured the diagonal and objected in three
    # different vocabularies before the cause was found once.
    origin = transform_point3(item.matrix, (0.0, 0.0, 0.0))
    tip = transform_point3(
        item.matrix, (1.0, 0.0, 0.0) if ridge_x else (0.0, 1.0, 0.0)
    )
    along = (tip[0] - origin[0], tip[1] - origin[1])
    length = (along[0] ** 2 + along[1] ** 2) ** 0.5 or 1.0
    return [replace(
        item,
        top_drop=pitch,
        ridge_along=(along[0] / length, along[1] / length),
        drop_toward=None,
    )]


SWEPT_VERBS: dict[str, Callable] = {
    "taper": taper,
    "twist": twist,
    "grade": grade,
    "shear": shear,
    "bend": bend,
    "pinch": pinch,
    "gable": gable,
    "butterfly": butterfly,
    "mansard": mansard,
}


__all__ = ["SWEPT_VERBS"]
