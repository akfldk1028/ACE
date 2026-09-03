"""The book's volume-to-volume family: what one body does to another.

Merge, Nest, Interlock, Lodge, Overlap, Extract and Inscribe (BOOK 045, 046,
052, 055, 056, 068, 069) were the seven operations of the book's thirty this
grammar could not say, and they are all the same kind of statement: a
relationship between bodies rather than a change to one. VitraHaus was
unsayable for exactly this gap - its bars lodge on each other - and the
aggregation fix that finally said it (`method: stack`) is a field-level word;
these are the pairwise ones.

Written in the grafting discipline: the relationship is said in the host's own
unit space and the host's matrix does the placing, so the same sentence lands
attached and bearing-correct on any parcel. Every body a verb creates carries
its host's role as a prefix, so a later word aimed at the host carries what
was done to it - the lesson of the lift legs that stayed behind when their
plate was shifted.
"""

from __future__ import annotations

from dataclasses import replace
from math import cos, radians, sin
from typing import Callable

from design.maas.geometry_language.affine_matrix import transform_point3

from ..form import Placement
from .grafting import _GRIP, _region
from .swept import _clamp


def _hosts(picked: list[Placement]) -> list[Placement]:
    return [item for item in picked if item.kind == "additive"]


def merge(frame, op) -> None:
    """Several bodies become one - the book's Merge, the one declared union.

    The corpus keeps volumes apart on purpose (`JOINT_CLEARANCE_M`), so a
    merge is a statement, not a default. The picked bodies are replaced by a
    single volume spanning their joint extent, measured on the frame's own
    axes - an axis-aligned box inflated Vancouver House by its bearing once
    already, and a merge must not grow what it fuses.

    A merge must not erase a roof either. The first version rebuilt its
    bodies as one plain box, so `aggregate + gable + merge` - fused gabled
    bars, the VitraHaus sentence - delivered a flat prism: the gable spoke at
    its own step and was gone from the drawing, the same derived-geometry
    class as the lift legs that stayed behind. So the fused box rises to the
    lowest eave, and what stands above it - each body's own roof wedge, or
    the top of a body the box does not reach - is kept as its own volume,
    named onto the merged body so later words carry it. Nothing overlaps:
    the floor-area reading sums volumes, and a body kept whole above a box
    that also spans it would be counted twice.
    """

    picked, rest = frame.pick(op)
    bodies = _hosts(picked)
    if len(bodies) < 2:
        return
    bearing = radians(frame.rotation)
    ax, ay = cos(bearing), sin(bearing)
    px, py = -ay, ax
    corners = [corner for item in bodies for corner in item.corners()]
    along = [x * ax + y * ay for x, y, _z in corners]
    across = [x * px + y * py for x, y, _z in corners]
    zs = [z for _x, _y, z in corners]
    centre_a = (min(along) + max(along)) / 2.0
    centre_c = (min(across) + max(across)) / 2.0
    world_x = centre_a * ax + centre_c * px
    world_y = centre_a * ay + centre_c * py
    dx, dy = frame.local(world_x, world_y)
    share = _clamp(float(op.params.get("height", 1.0)), 0.2, 1.0)
    kept = [item for item in picked if item not in bodies]

    # The fused box stops at the lowest eave among bodies that carry a
    # section; with no section anywhere it takes the joint height as before.
    # `box` floors an occupiable height at one storey, so the box's real top
    # is read back off the placement rather than assumed - a roof the box
    # swallowed is fused, which is what the word says happens where they meet.
    eaves = []
    for body in bodies:
        drop = float(body.top_drop or 0.0)
        if drop > 0.0 and (
            body.ridge_along is not None
            or body.drop_toward is not None
            or getattr(body, "top_profile", None) is not None
        ):
            low, high = body.z_span()
            eaves.append(high - (high - low) * drop)
    cap = min(eaves) if eaves else max(zs)
    fused = frame.box(
        bodies[0].role,
        w=max(along) - min(along), d=max(across) - min(across),
        z=min(zs), h=(cap - min(zs)) * share,
        dx=dx, dy=dy,
    )
    _low, box_top = fused.z_span()

    # Whatever a body holds above the box - a roof wedge, or whole storeys
    # the capped box does not reach - stays, windowed in the body's own unit
    # space so its plan and its section ride every later transform, and named
    # onto the merged body so later words carry it. A piece shorter than a
    # storey is a roof over the fused body, not a room, and says so.
    above: list[Placement] = []
    for index, body in enumerate(bodies):
        low, high = body.z_span()
        if high <= box_top + 1e-9 or high - low <= 1e-9:
            continue
        window = max(0.0, (box_top - low) / (high - low))
        piece = _region(
            body, f"{bodies[0].role}_roof_{index}",
            (0.0, 0.0, window), (1.0, 1.0, 1.0),
        )
        drop = float(body.top_drop or 0.0)
        kept_share = 1.0 - window
        profile = getattr(body, "top_profile", None)
        if profile is not None and kept_share > 1e-9:
            # Profile heights are shares of the whole body; the kept piece is
            # only its top, so the heights are re-read in the piece's terms.
            profile = tuple(
                (u, min(1.0, max(0.0, (h - window) / kept_share)))
                for u, h in profile
            )
        above.append(replace(
            piece, plan=body.plan,
            top_drop=min(1.0, drop / kept_share) if drop > 0.0 else 0.0,
            top_profile=profile,
            occupiable=body.occupiable and (high - low) * kept_share >= frame.storey - 1e-6,
        ))

    frame.placements = rest + kept + [fused] + above


def nest(frame, op) -> None:
    """A body inside a body, standing proud of the roof - the book's Nest.

    A solid hidden inside a solid is not a drawing, so the massing reading of
    a nest is the contained body showing where it can: above the host's top.
    `embed` exits a face; this word never touches one.
    """

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    size = _clamp(float(op.params.get("size", 0.35)), 0.15, 0.6)
    proud = _clamp(float(op.params.get("proud", 0.35)), 0.1, 1.0)
    # A nested body may stand turned inside its case - the tower that faces
    # the open side while the plinth keeps the street. Said here rather than
    # with a rotate after, because a region turned inside a non-square host's
    # unit space shears; the turned body is built in world space instead.
    turn = _clamp(float(op.params.get("turn", 0.0)), -60.0, 60.0)
    made: list[Placement] = []
    for host in hosts:
        if abs(turn) > 1e-6:
            corners = host.corners()
            xs = [x for x, _y, _z in corners]
            ys = [y for _x, y, _z in corners]
            zs = [z for _x, _y, z in corners]
            side = size * min(max(xs) - min(xs), max(ys) - min(ys))
            base, crest = min(zs), max(zs)
            dx, dy = frame.local((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
            made.append(frame.box(
                f"{host.role}_nested", w=side, d=side,
                z=base + (crest - base) * _GRIP,
                h=(crest - base) * (1.0 - _GRIP + proud),
                dx=dx, dy=dy, turn=turn,
            ))
            continue
        centre = 0.5 - size / 2.0
        made.append(_region(
            host, f"{host.role}_nested",
            (centre, centre, _GRIP), (centre + size, centre + size, 1.0 + proud),
        ))
    frame.placements = rest + picked + made


def interlock(frame, op) -> None:
    """Two arms from opposite faces, meshed at different heights.

    Each enters past the other's reach and each holds a band the other does
    not - clasped fingers rather than a lump. An overlap shares plan at one
    level; an interlock is the section event.
    """

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    bite = _clamp(float(op.params.get("bite", 0.55)), 0.3, 0.75)
    width = _clamp(float(op.params.get("size", 0.4)), 0.2, 0.6)
    reach = _clamp(float(op.params.get("reach", 0.3)), 0.1, 0.6)
    made: list[Placement] = []
    for host in hosts:
        centre = 0.5 - width / 2.0
        made.append(_region(
            host, f"{host.role}_jaw_low",
            (1.0 - bite, centre, _GRIP), (1.0 + reach, centre + width, 0.5),
        ))
        made.append(_region(
            host, f"{host.role}_jaw_high",
            (-reach, centre, 0.5), (bite, centre + width, 1.0),
        ))
    frame.placements = rest + picked + made


def lodge(frame, op) -> None:
    """A bar perched across the host's top, hanging past both sides.

    걸치다: what it rests on carries it, and the overhang is the word. This is
    VitraHaus's atomic relation said pairwise - the field-level version is
    `aggregate method: stack`.
    """

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    width = _clamp(float(op.params.get("size", 0.35)), 0.15, 0.6)
    over = _clamp(float(op.params.get("over", 0.25)), 0.05, 0.6)
    share = _clamp(float(op.params.get("height", 0.4)), 0.2, 1.0)
    at = _clamp(float(op.params.get("at", 0.5)), 0.0, 1.0)
    made: list[Placement] = []
    for host in hosts:
        x0 = at * (1.0 - width)
        # The bar lies ACROSS the host's long axis - which axis that is
        # belongs to the host, not to this verb. Assuming unit-x was the
        # length inverted the roles on a loop's side bars (unit-x is their
        # narrow width) and delivered `size` as a sliver of the bar's own
        # thinness stretched 1.7 sites long: the audit's paper-thin parallel
        # fins. Same lesson as `pinch`: direction cannot tell the bars apart,
        # proportion can - so the long axis is read off the matrix.
        length_x = (host.matrix[0][0] ** 2 + host.matrix[1][0] ** 2) ** 0.5
        length_y = (host.matrix[0][1] ** 2 + host.matrix[1][1] ** 2) ** 0.5
        if length_x >= length_y:
            low_corner = (x0, -over, 1.0 - _GRIP)
            high_corner = (x0 + width, 1.0 + over, 1.0 - _GRIP + share)
        else:
            low_corner = (-over, x0, 1.0 - _GRIP)
            high_corner = (1.0 + over, x0 + width, 1.0 - _GRIP + share)
        made.append(_region(
            host, f"{host.role}_lodged", low_corner, high_corner,
        ))
    frame.placements = rest + picked + made


def overlap(frame, op) -> None:
    """A twin displaced past its host so the two share part of their plan.

    겹치다 at one level: the shared region is the statement, and how much is
    shared is the parameter. Same ground, same height family - the section
    version of this thought is `interlock`.
    """

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    bite = _clamp(float(op.params.get("bite", 0.35)), 0.15, 0.6)
    side = _clamp(float(op.params.get("slip", 0.2)), 0.0, 0.5)
    share = _clamp(float(op.params.get("height", 0.8)), 0.2, 1.2)
    made: list[Placement] = []
    for host in hosts:
        shift = 1.0 - bite
        made.append(_region(
            host, f"{host.role}_twin",
            (shift, side, _GRIP), (shift + 1.0, side + 1.0, share),
        ))
    frame.placements = rest + picked + made


def extract(frame, op) -> None:
    """A piece pulled out of the body and stood beside its own socket.

    The book's Extract is both halves at once: the void where the piece was
    and the piece where it went. One without the other is a carve or a new
    volume; together they explain each other.
    """

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    size = _clamp(float(op.params.get("size", 0.3)), 0.15, 0.5)
    gap = _clamp(float(op.params.get("gap", 0.2)), 0.05, 0.6)
    share = _clamp(float(op.params.get("height", 0.6)), 0.2, 1.0)
    level = _clamp(float(op.params.get("level", 0.0)), 0.0, 0.8)
    made: list[Placement] = []
    for host in hosts:
        centre = 0.5 - size / 2.0
        z0 = level * (1.0 - share)
        socket = _region(
            host, f"{host.role}_socket",
            (1.0 - size, centre, z0), (1.0 + _GRIP, centre + size, z0 + share),
        )
        made.append(replace(socket, kind="subtractive", occupiable=False))
        made.append(_region(
            host, f"{host.role}_extracted",
            (1.0 + gap, centre, _GRIP), (1.0 + gap + size, centre + size, share),
        ))
    frame.placements = rest + picked + made


def inscribe(frame, op) -> None:
    """A figure sunk into the roof, touching no edge - the book's Inscribe.

    A notch reaches an edge and a puncture goes through; an inscription is
    contained on every side and shallow by definition. In massing terms it is
    the sunken court read from above.

    `at` and `across` place it, in the host's own plan, the way `lodge` places
    what it hangs. Without them the cut was always centred, so a sentence that
    inscribes twice cut the same hole twice: `sanaa_kanazawa_engraved_disc`
    declares 0.22 and then 0.24, and the second - the larger one - redrew 0.5%
    of the mass against the first's 2.5%, because all it could reach was a 1%
    ring around a hole that was already there. Both default to 0.5, which is the
    centred cut this made before.
    """

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    size = _clamp(float(op.params.get("size", 0.35)), 0.15, 0.6)
    depth = _clamp(float(op.params.get("depth", 0.25)), 0.1, 0.5)
    at = _clamp(float(op.params.get("at", 0.5)), 0.0, 1.0)
    across = _clamp(float(op.params.get("across", 0.5)), 0.0, 1.0)
    made: list[Placement] = []
    for host in hosts:
        x0 = at * (1.0 - size)
        y0 = across * (1.0 - size)
        cut = _region(
            host, f"{host.role}_inscribed",
            (x0, y0, 1.0 - depth), (x0 + size, y0 + size, 1.0 + _GRIP),
        )
        made.append(replace(cut, kind="subtractive", occupiable=False))
    frame.placements = rest + picked + made


def canopy(frame, op) -> None:
    """A thin plate the body wears past its edge - the eave, the marquee.

    The one element the language could not say below a storey: plausibility
    holds every occupiable volume to a 2.4 m clear room, so a SANAA roof or a
    deep eave over an approach was refused as a wall. This plate declares
    itself unoccupiable and lands in the structural bands the gates already
    exempt - the same channel `lift`'s legs ride. The structure gate still
    judges the overhang, which is why `reach` stops where `cantilever`'s does.

    `at` places it on the host's height (1.0 = the roof edge, lower is a
    marquee over a door); the plate grips the host a little and reaches out
    along `toward`, full width across.
    """

    from math import atan2, degrees

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    reach = _clamp(float(op.params.get("reach", 0.3)), 0.1, 0.45)
    at = _clamp(float(op.params.get("at", 1.0)), 0.3, 1.0)
    # `direction` answers in the FRAME's axes and the host's corners are in
    # the WORLD's - the exact mix-up `_Frame.out` exists to prevent, and the
    # first build of this verb made it anyway: the plate projected along
    # world east, the push-out too, and the turn subtracted frame.rotation
    # that `frame.box` adds right back - so on a merged full-parcel host the
    # whole plate landed outside the envelope and the legal clip deleted it.
    # The eave read as silent when it was in fact built, aimed at nothing.
    ffx, ffy = frame.direction(op.params.get("toward"))
    turn = degrees(atan2(ffy, ffx))  # frame-relative; frame.box adds rotation
    wx, wy = frame.out(ffx, ffy)
    norm = (wx * wx + wy * wy) ** 0.5 or 1.0
    fx, fy = wx / norm, wy / norm  # world unit vector for world corners
    # Of a storey - visibly a plate, never a floor. Authorable down to a true
    # roof thickness (0.1 of 3.4 m is 34 cm): three office lenses read the
    # same fault - not one plane on nineteen tiles thinner than a storey -
    # and the habitable slab can never legally be that plane; this one can.
    thickness_share = _clamp(float(op.params.get("thin", 0.35)), 0.1, 0.35)
    made: list[Placement] = []
    for host in hosts:
        corners = host.corners()
        xs = [x for x, _y, _z in corners]
        ys = [y for _x, y, _z in corners]
        zs = [z for _x, _y, z in corners]
        along = [x * fx + y * fy for x, y in zip(xs, ys)]
        span_t = max(along) - min(along)
        span_a = max(
            (x * -fy + y * fx) for x, y in zip(xs, ys)
        ) - min((x * -fy + y * fx) for x, y in zip(xs, ys))
        if span_t < 1e-6 or span_a < 1e-6:
            continue
        grip = 0.15 * span_t
        length = grip + reach * span_t
        # Centre sits so the plate covers the host's leading edge by `grip`
        # and reaches `reach` of the host's own span beyond it.
        cx = (min(xs) + max(xs)) / 2.0 + fx * (span_t / 2.0 - grip + length / 2.0)
        cy = (min(ys) + max(ys)) / 2.0 + fy * (span_t / 2.0 - grip + length / 2.0)
        base, crest = min(zs), max(zs)
        thin = thickness_share * frame.storey
        z = base + at * (crest - base) - thin
        dx, dy = frame.local(cx, cy)
        made.append(frame.box(
            f"{host.role}_canopy", w=length, d=span_a, z=z, h=thin,
            dx=dx, dy=dy, turn=turn, occupiable=False,
        ))
    frame.placements = rest + picked + made


def roof(frame, op) -> None:
    """A warped roof plate over each body - the flying eave.

    Every picked body gets its own thin plate above it, overhanging on all
    four sides by `eave` of the body's short span, its corners lifted by
    `rise` storeys and its edges curving between them by `sag` - the
    hyperbolic-paraboloid roof a whole family of competition winners rests
    on (MAD's Jiaxing pavilions, Kuma's canopies), which no one-axis section
    could draw. `corners` names which corners rise: "opposite" (two, the
    saddle), "one", "adjacent" (two on one side, a lean-to sweep), "all"
    (a dish on four points). The plate declares itself unoccupiable and
    lands in the structural bands; the eave beyond the body is judged by
    the structure gate like any cantilever.
    """

    from math import atan2, degrees

    picked, rest = frame.pick(op)
    hosts = _hosts(picked)
    if not hosts:
        return
    rise_share = _clamp(float(op.params.get("rise", 0.8)), 0.2, 1.5)      # of a storey
    eave = _clamp(float(op.params.get("eave", 0.25)), 0.0, 0.5)          # of the short span
    sag = _clamp(float(op.params.get("sag", 0.3)), 0.0, 0.6)             # of the plate's band
    thin = _clamp(float(op.params.get("thin", 0.12)), 0.06, 0.35)        # of a storey
    which = str(op.params.get("corners", "opposite")).strip().lower()
    lifted = {"opposite": (1, 0, 1, 0), "one": (1, 0, 0, 0),
              "adjacent": (1, 1, 0, 0), "all": (1, 1, 1, 1)}.get(which, (1, 0, 1, 0))
    made: list[Placement] = []
    for host in hosts:
        corners = host.corners()
        origin = transform_point3(host.matrix, (0.0, 0.0, 0.0))
        ex = transform_point3(host.matrix, (1.0, 0.0, 0.0))
        ey = transform_point3(host.matrix, (0.0, 1.0, 0.0))
        ax, ay = ex[0] - origin[0], ex[1] - origin[1]
        bx, by = ey[0] - origin[0], ey[1] - origin[1]
        span_u = (ax * ax + ay * ay) ** 0.5
        span_v = (bx * bx + by * by) ** 0.5
        if span_u < 1e-6 or span_v < 1e-6:
            continue
        ux, uy = ax / span_u, ay / span_u
        vx, vy = bx / span_v, by / span_v
        eave_m = eave * min(span_u, span_v)
        rise_m = rise_share * frame.storey
        thin_m = thin * frame.storey
        band = thin_m + rise_m
        zs = [z for _x, _y, z in corners]
        crest = max(zs)
        xs = [x for x, _y, _z in corners]
        ys = [y for _x, y, _z in corners]
        cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
        dx, dy = frame.local(cx, cy)
        turn = degrees(atan2(uy, ux)) - frame.rotation
        plate = frame.box(
            f"{host.role}_roof", w=span_u + 2 * eave_m, d=span_v + 2 * eave_m,
            z=crest, h=band, dx=dx, dy=dy, turn=turn, occupiable=False,
        )
        low_share = thin_m / band
        made.append(replace(
            plate,
            top_drop=rise_m / band,
            # The sixth term is the sheet's thickness as a share of its band,
            # so the underside follows the top at `thin` metres.
            warp=((ux, uy), (vx, vy),
                  tuple(1.0 if c else low_share for c in lifted), True, sag,
                  low_share),
        ))
    frame.placements = rest + picked + made


RELATIONAL_VERBS: dict[str, Callable] = {
    "roof": roof,
    "merge": merge,
    "nest": nest,
    "interlock": interlock,
    "lodge": lodge,
    "overlap": overlap,
    "extract": extract,
    "inscribe": inscribe,
    "canopy": canopy,
}
