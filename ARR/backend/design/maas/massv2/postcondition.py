"""Did the building do what the sentence said it did.

Everything else in this package checks the mass against the world - the law,
daylight, gravity, the parcel. Nothing checked it against its own sentence.

That gap is why the work on this language has been a sequence of patches. A
`split` whose halves stood flush at the same height drew a picture identical to
the box it cut, a `lift` of two metres under a twelve-metre plate read as a
plinth recess, a `carve` at the low end of its range came out as a skylight -
and each one was found by a person looking at a PNG, forming a hypothesis, and
changing code. Three faults, three rounds, and the next invisible verb would
have needed a fourth. The verb that failed was never the point: the point is
that no verifier ever asked whether a declared move happened.

So this asks. Every operation the author wrote is checked against the compiled
mass, and a sentence whose moves cannot be found in the building it produced is
refused - not scored down, refused, for the same reason a mass that cannot
stand up is not a low-scoring option. A grammar whose words can be silent is
not a grammar; it is a naming scheme, and the sheet fills with sixteen
different names for the same box.

The checks read the compiled `SourceMass`, which is what gets drawn and
measured, rather than the authored placements - a move that survives authoring
and is then dissolved by growth or by the legal clip is just as absent from the
drawing as one that never happened.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.geometry import Polygon
from shapely.ops import unary_union

from design.maas.floor_viability import minimum_usable_floor_area_m2
from design.maas.source_geometry.ir import SourceMass

from .grammar import MIN_OFFSET_RATIO


# A person has to be able to walk under a lifted mass for the lift to be a
# lift rather than a recess. The same clear height the floor-viability rule
# already treats as the least a room can be.
WALKABLE_CLEARANCE_M = 2.4

# Two volumes read as two when their tops differ by more than the thickness of
# the line between them. A storey is the smallest step anybody draws.
LEGIBLE_STEP_STOREYS = 1.0


@dataclass(frozen=True)
class Verdict:
    """Which declared moves can be found in the mass, and which cannot."""

    declared: tuple[str, ...]
    silent: tuple[str, ...]

    @property
    def honest(self) -> bool:
        return not self.silent

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_postcondition.v1",
            "declared": list(self.declared),
            "silent": list(self.silent),
            "honest": self.honest,
        }


def _levels(source: SourceMass) -> list[tuple[float, float, Any]]:
    height = float(source.metadata.get("authored_height_m") or 0.0)
    return [
        (volume.bottom_fraction * height, volume.top_fraction * height, volume.footprint)
        for volume in source.volumes
    ]


def _distinct_tops(source: SourceMass, *, floor_height_m: float) -> int:
    step = max(floor_height_m * LEGIBLE_STEP_STOREYS, 0.5)
    return len({round(top / step) for _low, top, _plan in _levels(source)})


def _shows_split(source: SourceMass, *, floor_height_m: float) -> bool:
    """Two parts, told apart from outside.

    Either they stop at different heights, or they stand apart in plan. A pair
    that does neither is one volume with a line drawn on it.
    """

    if _distinct_tops(source, floor_height_m=floor_height_m) >= 2:
        return True
    plans = [plan for _low, _top, plan in _levels(source)]
    if not plans:
        return False
    union = unary_union(plans)
    return getattr(union, "geom_type", "") == "MultiPolygon"


def _shows_lift(source: SourceMass, *, parcel_area_m2: float) -> bool:
    """Something is held up, and there is a room's worth of space under it.

    The first version asked what share of the raised plate was held from below
    and wanted it under a half. That is the wrong question, and it collided
    with the verb: `lift` puts four supports of about a third of the plan
    each under whatever it raises, which is 41% before the legal clip touches
    anything - so trimming the plate a little pushed the ratio past the
    threshold and the move failed its own test 138 times while the geometry was
    measured, separately, to be raised exactly as authored.

    What makes a lift a lift is the space under it, so that is what is
    measured: the open ground beneath the raised volume, against the same
    minimum this package uses everywhere else for a room.
    """

    least = minimum_usable_floor_area_m2(parcel_area_m2)
    levels = _levels(source)
    for low, _top, plan in levels:
        if low < WALKABLE_CLEARANCE_M:
            continue
        under = [
            other for _other_low, other_top, other in levels
            if other_top <= low + 1e-6 and other.intersects(plan)
        ]
        held = unary_union(under) if under else None
        open_ground = float(plan.area) - (
            float(plan.intersection(held).area) if held is not None else 0.0
        )
        if open_ground >= least:
            return True
    return False


def _shows_carve(source: SourceMass, *, parcel_area_m2: float) -> bool:
    """The court is a room, not a rooflight - and a notch counts.

    Sized against the same minimum the floor-viability rule uses for a usable
    floor: a void too small to be a room is not a court, by the rule this
    package already applies in the other direction to plan gaps.

    A court taken at the edge of the plan opens outward and leaves no interior
    ring at all - it is a notch, and reading only for holes called 133 of them
    silent when the drawing plainly shows the cut. The `reach` parameter is
    what decides which of the two a carve becomes, and the author is entitled
    to either, so the test is for a room-sized void by whichever shape.
    """

    least = minimum_usable_floor_area_m2(parcel_area_m2)
    for _low, _top, plan in _levels(source):
        for ring in getattr(plan, "interiors", ()):
            if float(Polygon(ring).area) >= least:
                return True
        # A notch is the same void with one side open: what the convex hull
        # holds and the plan does not.
        try:
            missing = float(plan.convex_hull.area) - float(plan.area)
        except Exception:  # pragma: no cover - GEOS refusing a degenerate hull
            continue
        if missing >= least:
            return True
    return False


def _shows_shear(source: SourceMass) -> bool:
    """An upper volume stands off the one below it by a readable fraction.

    Overlap is not required. A shear at the top of its range moves a volume
    clear of the one under it, which is the strongest version of the move and
    was being read as no move at all because the two no longer intersected.
    """

    levels = sorted(_levels(source), key=lambda item: item[0])
    for index, (low, _top, plan) in enumerate(levels):
        for _other_low, other_top, other in levels[:index]:
            if other_top < low - 1e-6:
                continue
            reach = plan.centroid.distance(other.centroid)
            minx, miny, maxx, maxy = plan.bounds
            span = max(maxx - minx, maxy - miny, 1e-6)
            if reach >= MIN_OFFSET_RATIO * span:
                return True
    return False


def check(
    form,
    source: SourceMass,
    *,
    floor_height_m: float,
    parcel_area_m2: float,
) -> Verdict:
    """Find every move the sentence declared in the mass it produced."""

    parti = (form.extra or {}).get("parti") or {}
    declared = tuple(
        str(op.get("verb") or "") for op in (parti.get("operations") or ())
    )
    if not declared or source is None or not source.volumes:
        return Verdict(declared, ())

    silent: list[str] = []
    for verb in dict.fromkeys(declared):
        if verb == "split" and not _shows_split(source, floor_height_m=floor_height_m):
            silent.append("split")
        elif verb == "lift" and not _shows_lift(source, parcel_area_m2=parcel_area_m2):
            silent.append("lift")
        elif verb == "carve" and not _shows_carve(source, parcel_area_m2=parcel_area_m2):
            silent.append("carve")
        elif verb == "shear" and not _shows_shear(source):
            silent.append("shear")
    return Verdict(declared, tuple(silent))


__all__ = ["Verdict", "check", "WALKABLE_CLEARANCE_M"]
