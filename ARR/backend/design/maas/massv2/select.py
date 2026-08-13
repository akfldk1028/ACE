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


def choose(
    candidates: Iterable[Candidate],
    *,
    require_occupiable: bool = True,
    per_cell: int = 1,
) -> list[Candidate]:
    """Drop what cannot be occupied, then fill each cell with its best occupant."""

    by_cell: dict[str, dict[tuple, Candidate]] = {}
    for candidate in candidates:
        if require_occupiable and not candidate.plausibility.occupiable:
            continue
        signature = composition_signature(candidate.form)
        cell = by_cell.setdefault(candidate.cell, {})
        held = cell.get(signature)
        if held is None or _rank(candidate) > _rank(held):
            cell[signature] = candidate

    # Scarcest cell first. A cell with one lawful occupant has no second choice,
    # so it picks before a cell holding a dozen - otherwise the abundant cell
    # takes the composition and the thin one is left empty or with junk.
    order = sorted(by_cell, key=lambda cell: (len(by_cell[cell]), cell))

    taken: set[tuple] = set()
    chosen: list[Candidate] = []
    for cell in order:
        ranked = sorted(
            by_cell[cell].items(),
            # An unseen composition first: the sheet is a set of options, and an
            # option the architect has already been shown is worth less than one
            # they have not, even when it measures a little better.
            key=lambda entry: (entry[0] not in taken, _rank(entry[1])),
            reverse=True,
        )
        for signature, candidate in ranked[:max(1, per_cell)]:
            taken.add(signature)
            chosen.append(candidate)
    return chosen


def _rank(candidate: Candidate) -> tuple[float, float, float]:
    # What the scheme earned beyond its cell's own coordinate comes first: the
    # void band is half of what put it here, so ranking a porous cell on plan
    # void ranks it on the one thing all its occupants share. Overall shape
    # breaks the tie, and the site's use breaks that.
    return (
        candidate.measurement.earned_articulation(),
        candidate.measurement.articulation(),
        candidate.far_utilization,
    )


def summary(chosen: list[Candidate], *, considered: int) -> dict[str, Any]:
    return {
        "schema_version": "arr.maas.massv2_selection.v1",
        "considered": considered,
        "distinct_compositions": len({composition_signature(item.form) for item in chosen}),
        "chosen": len(chosen),
        "cells": sorted({item.cell for item in chosen}),
    }
