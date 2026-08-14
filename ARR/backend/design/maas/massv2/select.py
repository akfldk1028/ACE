"""Choose the sheet an architect would actually look at.

Eighty-eight masses of which forty were distinct compositions is not a portfolio,
it is a contact sheet with the same building printed four times. Filling a grid
cell is a label; the architect chooses between buildings.

Three rules, in order:

  A mass that is lawful but not occupiable is not an option. That judgement is
  `plausibility`, which uses the project's own floor-viability rule.

  A composition seen twice *in one cell* is one composition, and the signature
  is scale-free so that two drawings of the same idea collapse. It is not
  applied across cells: ground take is one of the grid's two axes, so a scheme
  carried along that axis has moved, not repeated. Deduping globally deleted
  the move before the cells were ever looked at - measured on the Uijeongbu
  parcel, raked_bar stood lawful and occupiable in four different cells at an
  articulation of 0.309 and only one copy survived, which handed
  dispersed|solid_body to a scheme scoring 0.280.

  One per grid cell, and the one kept is the most articulate. Cells are filled
  scarcest-first, and a cell prefers a composition no other cell has taken, so
  an abundant cell cannot spend the only occupant a thin cell had.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from design.maas.source_geometry.ir import SourceMass

from .form import MatrixForm
from .measure import FormMeasurement
from .plausibility import Plausibility


@dataclass(frozen=True)
class Candidate:
    form: MatrixForm
    source: SourceMass
    measurement: FormMeasurement
    plausibility: Plausibility
    cell: str
    ground_take: float
    far_utilization: float


def composition_signature(form: MatrixForm) -> tuple:
    """What this composition is, independent of how big it was drawn.

    Every volume is expressed as a fraction of the whole form's bounding box, so
    a scheme and the same scheme at 45% ground take collapse to one signature.
    Rounding is coarse on purpose: two volumes a few centimetres apart in a
    sixty-metre composition are the same design decision.
    """

    additive = form.additive()
    if not additive:
        return ()
    corners = [corner for item in additive for corner in item.corners()]
    min_x = min(x for x, _y, _z in corners)
    max_x = max(x for x, _y, _z in corners)
    min_y = min(y for _x, y, _z in corners)
    max_y = max(y for _x, y, _z in corners)
    min_z = min(z for _x, _y, z in corners)
    max_z = max(z for _x, _y, z in corners)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    span_z = max(max_z - min_z, 1e-6)

    entries = []
    for item in form.placements:
        item_corners = item.corners()
        xs = [x for x, _y, _z in item_corners]
        ys = [y for _x, y, _z in item_corners]
        zs = [z for _x, _y, z in item_corners]
        entries.append((
            item.kind,
            round((min(xs) - min_x) / span_x, 2),
            round((min(ys) - min_y) / span_y, 2),
            round((min(zs) - min_z) / span_z, 2),
            round((max(xs) - min(xs)) / span_x, 2),
            round((max(ys) - min(ys)) / span_y, 2),
            round((max(zs) - min(zs)) / span_z, 2),
        ))
    return tuple(sorted(entries))


def _shape_work(item: Candidate) -> float:
    """How much shaping this scheme did, by whichever means it chose.

    Carving in plan and changing in section are not two things a building owes;
    they are two ways of doing the same one. A courtyard block is carved and
    never steps. A stepped tower steps and is convex in every plan. Listing
    them as separate objectives asks each to be both, and balance then punishes
    whichever it is not - measured on the live parcel, that handed
    full_ground|solid_body to a scheme at 0.05 articulation over `stacked_45`
    at 0.55, purely because the stepped one was flat in plan.

    So they are one objective, taken by the larger. Balance belongs between
    things a scheme genuinely owes at the same time - floor area and form -
    and a maximum belongs between substitutes. Using the same rule for both is
    what went wrong, in each direction: a maximum over everything let a scheme
    win on plan void alone, and a leximin over everything let a scheme win by
    being mediocre evenly.
    """

    return max(item.measurement.convexity_drop, item.measurement.section_change)


# What a scheme is asked to be good at, once its cell has already said where it
# sits. Neither grid coordinate is here and that is deliberate: ground take and
# plan void are the axes, so scoring them scores the thing every occupant of a
# cell has in common.
OBJECTIVES: tuple[tuple[str, Any], ...] = (
    ("far_utilization", lambda item: item.far_utilization),
    ("shape_work", _shape_work),
)


def _balance_keys(pool: list[Candidate]) -> dict[int, tuple[float, ...]]:
    """Score every candidate on how balanced it is, with no weights.

    A single number decided cells until now and it picked the worse building.
    `splayed_fan` topped its cell at an articulation of 0.79 while measuring
    almost nothing in section or in carving, because a maximum only has to be
    large once - and all five schemes rewritten against the critic's notes lost
    to the versions they were meant to replace.

    So: normalise each objective across the pool, then compare candidates by
    their objectives sorted worst-first. A scheme wins by having no weak side,
    not by having one strong one. This is the criterion behind T-DominO (Gaier,
    Stoddart, Villaggi, Bentley, PPSN 2022), which reports that a quarter of
    NSGA-II's solutions clear the lower quartile on all five of its objectives
    against 99% of its own - the same "nothing passes on every count" symptom
    this sheet has had all along. Sorting is monotone in Pareto dominance, so a
    scheme better on every objective still wins outright; balance only decides
    the cases dominance leaves open, which is most of them.
    """

    spans: list[tuple[float, float]] = []
    for _name, read in OBJECTIVES:
        values = [float(read(item)) for item in pool]
        low, high = (min(values), max(values)) if values else (0.0, 0.0)
        spans.append((low, high))

    keys: dict[int, tuple[float, ...]] = {}
    for item in pool:
        scaled = []
        for (_name, read), (low, high) in zip(OBJECTIVES, spans):
            width = high - low
            scaled.append((float(read(item)) - low) / width if width > 1e-9 else 1.0)
        # Worst-first, so comparing two keys compares their weakest sides first.
        keys[id(item)] = tuple(sorted(scaled))
    return keys


def choose(
    candidates: Iterable[Candidate],
    *,
    require_occupiable: bool = True,
    per_cell: int = 1,
) -> list[Candidate]:
    """Drop what cannot be occupied, then fill each cell with its best occupant."""

    pool = [
        candidate
        for candidate in candidates
        if not (require_occupiable and not candidate.plausibility.occupiable)
    ]
    keys = _balance_keys(pool)

    def rank(item: Candidate) -> tuple:
        return (keys[id(item)], item.far_utilization)

    by_cell: dict[str, dict[tuple, Candidate]] = {}
    for candidate in pool:
        signature = composition_signature(candidate.form)
        cell = by_cell.setdefault(candidate.cell, {})
        held = cell.get(signature)
        if held is None or rank(candidate) > rank(held):
            cell[signature] = candidate

    # Scarcest cell first. A cell with one lawful occupant has no second choice,
    # so it picks before a cell holding a dozen - otherwise the abundant cell
    # takes the composition and the thin one is left empty or with junk.
    order = sorted(by_cell, key=lambda cell: (len(by_cell[cell]), cell))

    taken: set[str] = set()
    chosen: list[Candidate] = []
    for cell in order:
        ranked = sorted(
            by_cell[cell].values(),
            # An unseen composition first: the sheet is a set of options, and an
            # option the architect has already been shown is worth less than one
            # they have not, even when it measures a little better.
            key=lambda item: (family_of(item) not in taken, rank(item)),
            reverse=True,
        )
        for candidate in ranked[:max(1, per_cell)]:
            taken.add(family_of(candidate))
            chosen.append(candidate)
    return chosen


def family_of(candidate: Candidate) -> str:
    """Which composition this is, before the coverage axis restated it.

    Two cells apart, the same scheme is a move along an axis and belongs on the
    sheet twice - that is what deduping globally got wrong. Three cells apart it
    is the same drawing printed three times, which is what happened the moment
    the ranking changed: `hollow_market_arch` took the arch cell, then took two
    more, and the sixteen tiles read as nine buildings.

    Both suffixes have to be cut, not just the coverage one. A siting copy is
    the same composition standing somewhere else, and keeping `^off_open` in
    the key made it a new family - so `plate_on_four_supports` printed twice on
    one sheet, and `lifted_back_court` twice more.

    The geometry signature cannot police that either, because it is what the
    coverage variants legitimately differ in - growing a scheme wider and growing it
    taller both change its proportions, so its own copies stop matching it. The
    name the variants were derived from does not move, so that is what is
    remembered across cells. Within a cell the signature still rules, since
    there the question really is whether two drawings are one design.
    """

    name = candidate.form.name
    for mark in ("~", "^"):
        name = name.split(mark, 1)[0]
    return name


def summary(chosen: list[Candidate], *, considered: int) -> dict[str, Any]:
    return {
        "schema_version": "arr.maas.massv2_selection.v1",
        "considered": considered,
        "distinct_compositions": len({composition_signature(item.form) for item in chosen}),
        "chosen": len(chosen),
        "cells": sorted({item.cell for item in chosen}),
    }
