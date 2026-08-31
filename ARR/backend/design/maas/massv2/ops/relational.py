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
        made.append(_region(
            host, f"{host.role}_lodged",
            (x0, -over, 1.0 - _GRIP), (x0 + width, 1.0 + over, 1.0 - _GRIP + share),
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


RELATIONAL_VERBS: dict[str, Callable] = {
    "merge": merge,
    "nest": nest,
    "interlock": interlock,
    "lodge": lodge,
    "overlap": overlap,
    "extract": extract,
    "inscribe": inscribe,
}
