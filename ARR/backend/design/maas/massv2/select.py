"""Choose the sheet an architect would actually look at.

Eighty-eight masses of which forty were distinct compositions is not a portfolio,
it is a contact sheet with the same building printed four times. Filling a grid
cell is a label; the architect chooses between buildings.

Three rules, in order:

  A composition seen twice is one composition. Two copies of a scheme at
  different ground takes are the same building at different sizes, so the
  signature is deliberately scale-free.

  A mass that is lawful but not occupiable is not an option. That judgement is
  `plausibility`, which uses the project's own floor-viability rule.

  One per grid cell, and the one kept is the most articulate - the point of the
  grid was that its cells are different kinds of building, so a cell needs one
  good example, not five.
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
    """Dedupe by composition, drop what cannot be occupied, keep the best per cell."""

    seen: set[tuple] = set()
    unique: list[Candidate] = []
    for candidate in candidates:
        if require_occupiable and not candidate.plausibility.occupiable:
            continue
        signature = composition_signature(candidate.form)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(candidate)

    by_cell: dict[str, list[Candidate]] = {}
    for candidate in unique:
        by_cell.setdefault(candidate.cell, []).append(candidate)

    chosen: list[Candidate] = []
    for cell in sorted(by_cell):
        ranked = sorted(
            by_cell[cell],
            key=lambda item: (
                item.measurement.articulation(),
                # A tie on articulation goes to the scheme that uses the site.
                item.far_utilization,
            ),
            reverse=True,
        )
        chosen.extend(ranked[:max(1, per_cell)])
    return chosen


def summary(chosen: list[Candidate], *, considered: int) -> dict[str, Any]:
    return {
        "schema_version": "arr.maas.massv2_selection.v1",
        "considered": considered,
        "distinct_compositions": len({composition_signature(item.form) for item in chosen}),
        "chosen": len(chosen),
        "cells": sorted({item.cell for item in chosen}),
    }
