"""Where on the parcel the building sits.

Ground take says how much of the site a scheme claims and the void band says
what kind of figure it is, and neither says where it stands. `seat_on_site`
answers that once, for every scheme, by putting it on the buildable centroid -
so every mass in the archive is centred, and a low-coverage scheme that could
have sat against the street, or held one corner and left a yard, sits in the
middle of an even margin instead.

That is a real architectural decision being made by default. A building pushed
to the road edge makes a forecourt behind it; the same building pushed back
makes a front garden; held to one side it leaves a yard wide enough to be a
place rather than a gap. Those are different proposals, not different pictures
of one proposal.

The anchors are read off the parcel rather than listed here, so this means the
same thing on any site: the buildable polygon's own centre, and the extremes of
its two principal directions. A square site and a long thin one both give four
positions that an architect would recognise, without a number being chosen.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import hypot

from shapely.geometry import Polygon
from shapely.ops import unary_union

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    translation_matrix4,
    validate_matrix4,
)

from .compile import _plan
from .form import MatrixForm


@dataclass(frozen=True)
class Siting:
    """One position on the parcel, named for what it does."""

    siting_id: str
    label: str
    # How far toward the parcel edge, as a share of the room the scheme has.
    # 0.0 is the centre; 1.0 is as far as it can go while staying inside.
    reach: float
    # Which principal direction, and which end of it.
    axis: int
    sign: float


SITINGS: tuple[Siting, ...] = (
    Siting("centred", "Centred on the parcel", 0.0, 0, 0.0),
    Siting("long_front", "Held to one end of the long axis", 0.85, 0, 1.0),
    Siting("long_back", "Held to the other end of the long axis", 0.85, 0, -1.0),
    Siting("cross_side", "Held to one side of the short axis", 0.85, 1, 1.0),
)


def principal_axes(buildable: Polygon) -> tuple[tuple[float, float], tuple[float, float]]:
    """The parcel's own long and short directions.

    Taken from the minimum rotated rectangle, which is the parcel's own idea of
    which way it runs - an axis-aligned bounding box would call a diagonal site
    square and put every "held to one end" copy in the same place as the centred
    one.
    """

    box = buildable.minimum_rotated_rectangle
    ring = list(box.exterior.coords)[:4]
    edges = [
        (ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1])
        for i in range(3)
    ]
    edges.sort(key=lambda e: hypot(e[0], e[1]), reverse=True)
    long_edge, short_edge = edges[0], edges[1]
    return _unit(long_edge), _unit(short_edge)


def _unit(vector: tuple[float, float]) -> tuple[float, float]:
    length = hypot(vector[0], vector[1])
    return (0.0, 0.0) if length <= 1e-9 else (vector[0] / length, vector[1] / length)


def _plan_union(form: MatrixForm) -> Polygon:
    return unary_union([_plan(item) for item in form.additive()])


def _moved(form: MatrixForm, dx: float, dy: float) -> MatrixForm:
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return form
    shift = translation_matrix4((dx, dy, 0.0))
    return replace(
        form,
        placements=tuple(
            replace(item, matrix=validate_matrix4(compose_matrix4(item.matrix, shift)))
            for item in form.placements
        ),
    )


def place_on_site(form: MatrixForm, buildable: Polygon, siting: Siting) -> MatrixForm | None:
    """Move the scheme to this position, or `None` if it has no room to move.

    The travel is bounded by what the scheme can spend without leaving the
    parcel: the difference between the parcel's extent along the axis and the
    scheme's own. A mass that already fills the site has nowhere to go, and
    returning it unchanged would put a duplicate in the archive rather than an
    alternative.
    """

    plan = _plan_union(form)
    if plan.is_empty or buildable.is_empty:
        return None

    here, there = plan.centroid, buildable.centroid
    centred_dx, centred_dy = float(there.x - here.x), float(there.y - here.y)
    if siting.reach <= 0.0:
        return _moved(form, centred_dx, centred_dy)

    axes = principal_axes(buildable)
    axis = axes[siting.axis]
    if axis == (0.0, 0.0):
        return None

    room = (_extent(buildable, axis) - _extent(plan, axis)) / 2.0
    if room <= 1e-6:
        return None
    travel = room * siting.reach * siting.sign
    return _moved(
        form, centred_dx + axis[0] * travel, centred_dy + axis[1] * travel
    )


def _extent(shape, direction: tuple[float, float]) -> float:
    values = [
        x * direction[0] + y * direction[1]
        for polygon in _polygons(shape)
        for x, y in polygon.exterior.coords
    ]
    return max(values) - min(values) if values else 0.0


def _polygons(shape) -> list[Polygon]:
    if shape is None or shape.is_empty:
        return []
    if isinstance(shape, Polygon):
        return [shape]
    return [item for item in getattr(shape, "geoms", ()) if isinstance(item, Polygon)]


def spread_across_siting(
    form: MatrixForm,
    *,
    buildable: Polygon,
    sitings: tuple[Siting, ...] = SITINGS,
) -> list[MatrixForm]:
    """One copy of this composition per position it can actually take."""

    out: list[MatrixForm] = []
    for siting in sitings:
        moved = place_on_site(form, buildable, siting)
        if moved is None:
            continue
        out.append(replace(
            moved,
            name=f"{form.name}^{siting.siting_id}",
            extra={**dict(moved.extra), "siting": siting.siting_id},
        ))
    return out


__all__ = ["SITINGS", "Siting", "place_on_site", "principal_axes", "spread_across_siting"]
