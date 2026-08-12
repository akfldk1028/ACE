"""Report how many program components each delivered mass actually carries.

The program gate's hierarchy number is the largest role-grouped plan area over
the whole, so a mass with one role is one lump by definition and only the
semantic zone term keeps it under the band ceiling. This reads the delivered
surfaces' `volume_role` - what was built, not what was planned - and pairs it
with plan solidity, because a mass may only honestly carry components when its
form has them.
"""

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union


def archived_records(run_dir):
    payload = json.loads(
        (Path(run_dir) / "maas-book-programs-summary.json").read_text(
            encoding="utf-8",
        ),
    )
    records = []
    for program in payload.get("programs", []):
        archive = (program.get("counts") or {}).get("legal_mass_archive") or {}
        records.extend(archive.get("records") or [])
    return records


def role_footprints(record):
    by_role = {}
    for surface in record.get("final_authored_surface_payload") or []:
        vertices = surface.get("vertices_m") or []
        if len(vertices) < 3:
            continue
        flat = Polygon([(float(v[0]), float(v[1])) for v in vertices])
        if flat.is_valid and flat.area > 0.0:
            by_role.setdefault(str(surface.get("volume_role") or "?"), []).append(flat)
    return {role: unary_union(parts) for role, parts in by_role.items()}


def main(run_dir):
    records = archived_records(run_dir)
    counts = Counter()
    shares = []
    solidity_by_count = {}
    for record in records:
        by_role = role_footprints(record)
        if not by_role:
            continue
        counts[len(by_role)] += 1
        areas = sorted((geometry.area for geometry in by_role.values()), reverse=True)
        shares.append(areas[0] / sum(areas))
        whole = unary_union(list(by_role.values()))
        solidity = float(whole.area) / max(float(whole.convex_hull.area), 1e-9)
        solidity_by_count.setdefault(len(by_role), []).append(solidity)

    print(f"=== {run_dir} ===")
    print(f"  masses measured: {sum(counts.values())}")
    print(f"  roles per mass: {dict(sorted(counts.items()))}")
    if shares:
        print(
            f"  largest role share: mean={statistics.mean(shares):.3f} "
            f"min={min(shares):.3f} max={max(shares):.3f}"
        )
    for role_count, values in sorted(solidity_by_count.items()):
        print(
            f"  {role_count} role(s): n={len(values):3} "
            f"plan solidity mean={statistics.mean(values):.3f}"
        )


if __name__ == "__main__":
    for target in sys.argv[1:]:
        main(target)
