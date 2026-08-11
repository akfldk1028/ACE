"""Measure 건축면적 the way 건축법 시행령 제119조 제1항 제2호 defines it.

건축면적 is the horizontal projection of the *building*, not of its ground
floor. So the only honest measurement is: project every surface of the mass
onto XY, union them, take the area. GFA divided by floor count is not this
number, and using it once already produced a wrong report (16/28 instead of
23/28).

The cap comes from the run itself (`bcr_footprint_capacity_m2`), never from a
literal typed here.
"""

import json
import re
import sys
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


def main(run_dir):
    cap = declared_capacity(run_dir)
    areas = []
    for record in archived_records(run_dir):
        area = projected_area(record)
        if area is not None:
            areas.append((area, str(record.get("geometry_hash") or "")[:8]))

    if not areas:
        print(f"{run_dir}: no archived mass carries surfaces")
        return

    over = [item for item in areas if item[0] > cap]
    areas.sort()
    median = areas[len(areas) // 2][0]
    print(f"=== {run_dir} ===")
    print(f"  건축면적 cap (from run): {cap:.3f} m2")
    print(f"  archived masses measured: {len(areas)}")
    print(f"  over cap: {len(over)}/{len(areas)}")
    print(f"  min {areas[0][0]:.1f}  median {median:.1f}  max {areas[-1][0]:.1f} m2")
    if over:
        worst = max(over)
        print(f"  worst: {worst[1]} at {worst[0]:.1f} m2 ({worst[0] / cap:.2f}x)")


if __name__ == "__main__":
    for target in sys.argv[1:]:
        main(target)
