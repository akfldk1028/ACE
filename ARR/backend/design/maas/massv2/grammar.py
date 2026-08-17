"""A mass as an ordered list of operations on a site-derived seed.

The archive repeated itself because the vocabulary was sixty-one finished
compositions - volume coordinates, authored once - and everything downstream
only resized and repositioned them. Sixteen grid cells came back as sixteen
variants of the same catalogue rather than sixteen buildings. A catalogue can
only ever be re-sorted.

So the unit of authorship is a sentence, not a picture. BIG publish their own
partis exactly this way, one operation per diagram caption - 79&Park is
EXTRUSION -> POROSITY -> DAYLIGHT -> LANDMARK - and every one of OMA's fifteen
patents in *Content* is a transformation of a known type rather than a form
from nothing. Across thirty-two built projects by BIG, OMA and SANAA, no mass
is a set of equal blocks: seven of ten BIG projects deform a single volume,
OMA runs one or three-to-five unequal peers, SANAA a single volume or a pure
boundary holding inscribed objects. Two equal masses never occurs, and neither
does six to ten undifferentiated lumps - which is precisely where our
`block_sw / block_se / block_nw / block_ne` compositions sat.

The seed comes from the parcel, so the site is present from the first move
rather than arriving at the end as a cutter. What the executor holds fixed is
grammar, not style: dimensioned offsets, no interpenetration, one dominant
volume. Those are legibility, and they are shared by three offices whose work
looks nothing like each other's - which is what tells you they are a property
of the medium rather than a preference. What the author chooses is which
operations, in what order, and toward what on this particular site. Magnitude
is geometric; direction is programmatic - Seattle's shear is 0.26 of its plan
depth, and its engineers state the direction was picked "not on structural
balance but rather to maximize views and capture desired light and shadow".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from shapely.geometry import Polygon

from .form import MatrixForm, Placement, place


# Below this an offset reads as a construction tolerance rather than a move;
# above it the volume stops reading as the same volume, displaced. Measured
# across the corpus: De Rotterdam 8.88 m on a 36 m plan depth = 0.25, Seattle
# 15.8 m on a 61 m plate = 0.26, Timmerhuis 21 m = exactly three 7.2 m modules.
MIN_OFFSET_RATIO = 0.15
# Seattle Central Library moves its platforms by half to nine tenths of their
# own plan, and the result is more legible for it, not less. The old ceiling
# said that past 0.35 "the volume stops reading as displaced", which is an
# observation this corpus contradicts: what it actually guaranteed was that
# every sentence came out moderate, and moderate composed three times is a
# composition rather than a diagram. Whether a displaced volume still stands is
# `structure`'s question and it is still asked.
MAX_OFFSET_RATIO = 0.9

# Repeated volumes are never the same size in built work - they spread ten to
# twenty times in plan and two to four in height. Nishizawa rejected identical
# units at Moriyama in as many words: they "looked like a barracks".
MIN_TIER_CONTRAST = 1.25

# Two volumes meeting hold a joint rather than merging: Toledo keeps 760 mm
# everywhere its cells meet, two glass walls and not one, and Louvre-Lens's five
# volumes touch only at their corners. One declared union in thirty-two projects.
JOINT_CLEARANCE_M = 0.76


PlotMode = Literal["inherit", "impose"]


@dataclass(frozen=True)
class Operation:
    """One move, and what it does to the site's shape.

    `plot_mode` is the finding that matters most here. Conforming to the plot
    is a property of the operation, not a setting for the whole run: stacking
    and shearing inherit the plot outline, while carving, looping and
    aggregating impose an independent shape and sit at 30-56% coverage.
    Kanazawa is a mathematically pure 112.5 m circle dropped on an irregular
    park. Applied globally, clipping turned every mass into a faceted cast of
    the parcel; refused globally, ground take collapsed to 0.38.
    """

    verb: str
    plot_mode: PlotMode
    params: dict[str, Any] = field(default_factory=dict)
    why: str = ""

    def evidence(self) -> dict[str, Any]:
        return {"verb": self.verb, "plot_mode": self.plot_mode, "params": dict(self.params), "why": self.why}


# The operations, with the plot relationship each one carries.
PLOT_MODES: dict[str, PlotMode] = {
    "split": "inherit",
    "extrude": "inherit",
    "stack": "inherit",
    "shear": "inherit",
    "taper": "inherit",
    "carve": "impose",
    "lift": "impose",
    "loop": "impose",
    "aggregate": "impose",
    # The ten below were added to the executor and never added here, so the
    # parser dropped them - six words across the corpus, and `skew` three times,
    # which is why Mountain Dwellings' 30-degree ramp never appeared. Worse
    # than being wrong: the postcondition check judges the ops it was *given*,
    # so a word lost at parse time is never reported silent. The sentence said
    # three things, two were built, and nothing anywhere said so.
    #
    # `_VERBS` and this table must name the same verbs; a test holds them equal.
    #
    # Which mode follows what the verb does to the figure. A void or a turn is
    # the point of the scheme and a clip to the boundary erases it, so those
    # impose; a slide or a size change is a move inside a mass that still takes
    # the plot's outline, so those inherit - the same reading that puts `shear`
    # and `taper` on one side and `carve` on the other.
    "grade": "impose",
    "notch": "impose",
    "puncture": "impose",
    "twist": "impose",
    "rotate": "impose",
    "skew": "inherit",
    "shift": "inherit",
    "offset": "inherit",
    "expand": "inherit",
    "compress": "inherit",
    "inflate": "inherit",
}


def plot_mode_of(ops: tuple[Operation, ...]) -> PlotMode:
    """One mode per composition: imposing anywhere means imposing.

    A scheme that carves a court out of a stack is not a cast of the parcel
    with a hole in it - the court is the point, and clipping it back to the
    boundary is what erases the move.
    """

    return "impose" if any(op.plot_mode == "impose" for op in ops) else "inherit"


@dataclass(frozen=True)
class Parti:
    """A named sequence of operations, with the reason each one is there."""

    name: str
    ops: tuple[Operation, ...]
    primary_language: str
    secondary_language: str = ""
    formal_principle: str = ""
    dominant_gesture: str = ""
    reference_basis: str = ""
    floor_height_m: float | None = None

    def plot_mode(self) -> PlotMode:
        return plot_mode_of(self.ops)

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_parti.v1",
            "name": self.name,
            "plot_mode": self.plot_mode(),
            "operations": [op.evidence() for op in self.ops],
        }


def parti_from_record(record: dict[str, Any]) -> Parti | None:
    """Read an authored sentence. Unknown verbs are dropped, not guessed at."""

    ops: list[Operation] = []
    for item in record.get("ops") or ():
        verb = str(item.get("op") or "").strip()
        mode = PLOT_MODES.get(verb)
        if mode is None:
            continue
        ops.append(Operation(
            verb=verb,
            plot_mode=mode,
            params={k: v for k, v in item.items() if k not in ("op", "why")},
            why=str(item.get("why") or ""),
        ))
    if not ops:
        return None
    return Parti(
        name=str(record.get("name") or "unnamed"),
        ops=tuple(ops),
        primary_language=str(record.get("primary_language") or "matrix_form"),
        secondary_language=str(record.get("secondary_language") or ""),
        formal_principle=str(record.get("formal_principle") or ""),
        dominant_gesture=str(record.get("dominant_gesture") or ""),
        reference_basis=str(record.get("reference_basis") or ""),
        floor_height_m=record.get("floor_height_m"),
    )


def seed_rectangle(buildable: Polygon, axis: tuple[float, float]) -> tuple[float, float, float, float, float]:
    """The site's own starting box: its widest rectangle, on its own axis.

    Taking the parcel's minimum rotated rectangle rather than an axis-aligned
    box is what lets a clean orthogonal composition sit in a skewed plot without
    being cut to pieces - the mass is turned to the site the way a building is,
    instead of meeting every boundary at an angle.

    Returns (centre x, centre y, width, depth, rotation in degrees).
    """

    from math import atan2, degrees, hypot

    box = buildable.minimum_rotated_rectangle
    ring = list(box.exterior.coords)[:4]
    edges = [
        (ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]) for i in range(3)
    ]
    edges.sort(key=lambda e: hypot(e[0], e[1]), reverse=True)
    width = hypot(edges[0][0], edges[0][1])
    depth = hypot(edges[1][0], edges[1][1])
    centre = box.centroid
    rotation = degrees(atan2(axis[1], axis[0])) if axis != (0.0, 0.0) else degrees(
        atan2(edges[0][1], edges[0][0])
    )
    return float(centre.x), float(centre.y), float(width), float(depth), float(rotation)


__all__ = [
    "JOINT_CLEARANCE_M",
    "MAX_OFFSET_RATIO",
    "MIN_OFFSET_RATIO",
    "MIN_TIER_CONTRAST",
    "Operation",
    "PLOT_MODES",
    "Parti",
    "PlotMode",
    "parti_from_record",
    "plot_mode_of",
    "seed_rectangle",
]
