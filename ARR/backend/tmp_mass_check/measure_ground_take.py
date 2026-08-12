"""Does the ground-take axis show up in the delivered masses?

건축면적 is measured the same way as measure_coverage.py - the union of every
surface projected onto XY (건축법 시행령 제119조 제1항 제2호). The question here is
not whether it stays under the cap but whether it *spreads*: 86 of 128 masses
within one percent of the cap is one proposal repeated, not a portfolio.

The band each mass was authored under is read from the run's own record, so a
band that is published but never reaches the geometry shows up as bands whose
delivered areas are identical.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union


def archived_records(run_dir):
    payload = json.loads(
        (Path(run_dir) / "maas-book-programs-summary.json").read_text(encoding="utf-8"),
    )
    records = []
    for program in payload.get("programs", []):
        archive = (program.get("counts") or {}).get("legal_mass_archive") or {}
        records.extend(archive.get("records") or [])
    return records


def declared_capacity(run_dir):
    text = (Path(run_dir) / "maas-book-programs-summary.json").read_text(encoding="utf-8")
    found = re.search(r'"bcr_footprint_capacity_m2"\s*:\s*([0-9.]+)', text)
    if not found:
        raise SystemExit("run declares no bcr_footprint_capacity_m2 - refusing to guess")
    return float(found.group(1))


def projected_area(record):
    faces = []
    for surface in record.get("final_authored_surface_payload") or []:
        vertices = surface.get("vertices_m") or []
        if len(vertices) < 3:
            continue
        flat = Polygon([(float(v[0]), float(v[1])) for v in vertices])
        if flat.is_valid and flat.area > 0.0:
            faces.append(flat)
    if not faces:
        return None
    return float(unary_union(faces).area)


def find_first(node, key):
    """First value stored under `key` anywhere inside one record."""

    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = find_first(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_first(value, key)
            if found is not None:
                return found
    return None


def void_of(record):
    """The solid/void position the delivered mass holds, from its own record."""

    band = find_first(record, "delivered_void")
    if isinstance(band, dict) and band.get("band_id"):
        return str(band["band_id"])
    ratio = find_first(record, "envelope_void_ratio")
    if ratio is None:
        return "(none)"
    try:
        measured = float(ratio)
    except (TypeError, ValueError):
        return "(none)"
    for ceiling, name in ((0.12, "solid_body"), (0.30, "carved_body"),
                          (0.50, "open_figure"), (1e9, "porous_field")):
        if measured <= ceiling:
            return name
    return "porous_field"


def band_of(record):
    band = find_first(record, "coverage_band")
    if isinstance(band, dict) and band.get("band_id"):
        return str(band["band_id"])
    return "(none)"


def floors_of(record):
    """Plates the delivered mass actually stacks, from its own measurements.

    The archive records GFA, not floor count, so the count is GFA divided by the
    measured horizontal projection. That is the number the ground-take axis is
    trading against: holding the ground means carrying the same area higher.
    """

    gfa = find_first(record, "floor_area_m2")
    plan = projected_area(record)
    try:
        if plan and float(gfa) > 0.0:
            return float(gfa) / plan
    except (TypeError, ValueError):
        pass
    return 0.0


def delivered_band(ratio):
    for ceiling, name in ((0.45, "dispersed_ground"), (0.65, "held_ground"),
                          (0.85, "worked_ground"), (1e9, "full_ground")):
        if ratio <= ceiling + 1e-9:
            return name
    return "full_ground"


def main(run_dir):
    cap = declared_capacity(run_dir)
    rows = []
    for record in archived_records(run_dir):
        area = projected_area(record)
        if area is None:
            continue
        rows.append((area / cap, area, band_of(record), floors_of(record)))

    if not rows:
        print(f"{run_dir}: no archived mass carries surfaces")
        return

    rows.sort()
    ratios = [row[0] for row in rows]
    at_cap = sum(1 for r in ratios if r >= 0.99)
    print(f"=== {run_dir} ===")
    print(f"  cap {cap:.3f} m2   n={len(rows)}")
    print(
        f"  ground take   min {ratios[0]:.3f}"
        f"   median {ratios[len(ratios) // 2]:.3f}"
        f"   max {ratios[-1]:.3f}"
    )
    print(f"  pinned at cap (>=0.99): {at_cap}/{len(rows)}")

    buckets = [(0.0, 0.55), (0.55, 0.75), (0.75, 0.90), (0.90, 0.99), (0.99, 9.9)]
    print("  distribution of 건축면적 / cap")
    for low, high in buckets:
        count = sum(1 for r in ratios if low <= r < high)
        label = f"  {low:.2f}-{high:.2f}" if high < 9 else "  >=0.99   "
        print(f"  {label:<14} {count:>3}  {'#' * count}")

    grid = defaultdict(int)
    for record in archived_records(run_dir):
        area = projected_area(record)
        if area is None:
            continue
        grid[(delivered_band(area / cap), void_of(record))] += 1
    print("  delivered grid  ground take x void")
    voids = ["solid_body", "carved_body", "open_figure", "porous_field", "(none)"]
    grounds = ["dispersed_ground", "held_ground", "worked_ground", "full_ground"]
    used_voids = [v for v in voids if any(grid.get((g, v)) for g in grounds)]
    header = "  " + " " * 18 + "".join(f"{v[:12]:>13}" for v in used_voids)
    print(header)
    for g in grounds:
        row = "".join(f"{grid.get((g, v), 0):>13}" for v in used_voids)
        print(f"  {g:<18}{row}")
    occupied = sum(1 for key, n in grid.items() if n)
    print(f"  occupied cells: {occupied}")

    by_band = defaultdict(list)
    for ratio, _area, band, floors in rows:
        by_band[band].append((ratio, floors))
    print(
        f"  {'band':<18} {'n':>3} {'min':>7} {'median':>7} {'max':>7}"
        f"  {'median plates':>13}"
    )
    for band, values in sorted(by_band.items()):
        values.sort()
        got = [value[0] for value in values]
        plates = sorted(value[1] for value in values)
        print(
            f"  {band:<18} {len(got):>3} {got[0]:>7.3f}"
            f" {got[len(got) // 2]:>7.3f} {got[-1]:>7.3f}"
            f"  {plates[len(plates) // 2]:>13.2f}"
        )


if __name__ == "__main__":
    for target in sys.argv[1:]:
        main(target)
