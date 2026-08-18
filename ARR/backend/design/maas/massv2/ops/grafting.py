"""The book's Branch and Embed: new volumes said in the host's own unit space.

Branch is "하나의 줄기에서 여러 팔을 생성" - one trunk, several arms. Embed is
"제2 볼륨을 제1 볼륨에 삽입" - a second body sunk into the first, part in and
part proud of the face. Both attach something new to something standing, and
both are written here without one line of world arithmetic:

    arm = region(unit space of the trunk, beyond its face) . trunk.matrix

Unit coordinates are not confined to [0, 1] - an affine matrix carries any
region - so an arm is a box whose unit-y runs from the trunk's face outward,
and an embedded body is one that straddles the face. Composed with the trunk's
own matrix it lands attached, aligned and bearing-correct on any parcel, which
is the whole graphics discipline of this package: say the relationship in the
host's coordinates and let the matrix it already carries do the placing.

Each joint tucks 1% into the host. Exact face-sharing merges in mathematics
and splits in floating point - the pinch measured that before it was
understood - so a graft grips what it grows from.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    scale_matrix4,
    translation_matrix4,
    validate_matrix4,
)

from ..form import Placement
from .swept import _clamp


def _region(
    host: Placement,
    role: str,
    low: tuple[float, float, float],
    high: tuple[float, float, float],
) -> Placement:
    """A unit cube posed into a region of the host's own unit space."""

    size = tuple(max(1e-6, b - a) for a, b in zip(low, high))
    matrix = compose_matrix4(
        scale_matrix4(size),
        translation_matrix4(low),
        host.matrix,
    )
    return replace(host, role=role, plan="square", matrix=validate_matrix4(matrix))


# How far into the host a graft reaches, in host-unit terms. The tuck that
# keeps the joint one solid in floating point.
_GRIP = 0.01


def branch(frame, op) -> None:
    """Grow arms off the trunk, alternating sides - the book's Branch.

    The arms divide the trunk's length evenly and each reaches out from a
    different side, which is what makes the result read as a tree or a comb
    rather than as a wider slab. Everything about an arm is a share of the
    trunk it grows from, so the same sentence branches a bar on any parcel.
    """

    picked, rest = frame.pick(op)
    trunks = [item for item in picked if item.kind == "additive"]
    if not trunks:
        return
    count = int(_clamp(float(op.params.get("n", 3)), 2, 5))
    reach = _clamp(float(op.params.get("reach", 0.8)), 0.3, 1.5)
    share = _clamp(float(op.params.get("height", 1.0)), 0.2, 1.0)
    # Arms and the bays between them split the trunk evenly: n arms, n+1 gaps.
    bay = 1.0 / (2 * count + 1)

    made: list[Placement] = []
    for trunk in trunks:
        for index in range(count):
            x0 = bay * (2 * index + 1)
            side = index % 2  # alternating, which is the tree reading
            y0, y1 = (1.0 - _GRIP, 1.0 + reach) if side == 0 else (-reach, _GRIP)
            made.append(_region(
                trunk, f"{trunk.role}_arm_{index}",
                (x0, y0, 0.0), (x0 + bay, y1, share),
            ))
    frame.placements = rest + picked + made


def embed(frame, op) -> None:
    """Sink a second body into the host's face - the book's Embed.

    Part in, part proud: `depth` says how much of the body is inside the host
    and the rest stands out of the face the sentence aimed at. An embed that
    goes all the way through would be an intersect, and one that vanishes
    inside would be a nest; this word is for the body you can still see.
    """

    picked, rest = frame.pick(op)
    hosts = [item for item in picked if item.kind == "additive"]
    if not hosts:
        return
    size = _clamp(float(op.params.get("size", 0.35)), 0.15, 0.6)
    depth = _clamp(float(op.params.get("depth", 0.4)), 0.1, 0.9)
    share = _clamp(float(op.params.get("height", 0.6)), 0.2, 1.0)
    level = _clamp(float(op.params.get("level", 0.0)), 0.0, 1.0)
    face = str(op.params.get("at") or "cross").lower()
    role = str(op.params.get("first") or "embedded")

    made: list[Placement] = []
    for host in hosts:
        z0 = level * (1.0 - share)
        body = size  # the embedded body's footprint, as a share of the host's
        span = body * (1.0 + depth)  # what is inside plus what stands proud
        centre = 0.5 - body / 2.0
        if face in ("cross", "short", "side"):
            low = (centre, 1.0 - body * depth, z0)
            high = (centre + body, 1.0 - body * depth + span, z0 + share)
        elif face in ("back", "away", "off_open"):
            low = (-(span - body * depth), centre, z0)
            high = (body * depth, centre + body, z0 + share)
        else:  # long: out of the far x face
            low = (1.0 - body * depth, centre, z0)
            high = (1.0 - body * depth + span, centre + body, z0 + share)
        made.append(_region(host, role, low, high))
    frame.placements = rest + picked + made


GRAFTING_VERBS: dict[str, Callable] = {
    "branch": branch,
    "embed": embed,
}


__all__ = ["GRAFTING_VERBS", "branch", "embed"]
