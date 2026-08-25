"""The real plan area of each storey, not the average.

`floor_programme` divided 연면적 by the storey count, which is only true of a
prism. A mass that is wide on the ground and narrow above holds its 대회의실
on the floor that can take it, and the average hides that in both directions.
"""

import json, sys
from pathlib import Path
from shapely.ops import unary_union
from finalists import PNU, rebuild, scheme_of
from design.maas.massv2.legal import load_legal_site
from design.maas.massv2.siting import open_side_direction

ROOT = Path(__file__).resolve().parents[1]


def storey_areas(src, *, height_m: float, storey_m: float) -> list[float]:
    """Plan area at the middle of each storey, from the ground up."""

    floors = max(1, round(height_m / max(storey_m, 1e-6)))
    out = []
    for n in range(floors):
        z = (n + 0.5) * storey_m / max(height_m, 1e-6)
        plans = [v.footprint for v in src.volumes
                 if v.footprint is not None
                 and v.bottom_fraction - 1e-9 <= z <= v.top_fraction + 1e-9]
        out.append(float(unary_union(plans).area) if plans else 0.0)
    return out


def main(run: str) -> int:
    folder = ROOT / "runs" / run
    picks = json.loads((folder.parent / f"{run}-pick" / "picks.json").read_text(encoding="utf-8"))["picks"]
    records = {r["name"]: r for r in json.loads((folder / "massv2-summary.json").read_text(encoding="utf-8"))["records"]}
    corpus = {}
    for p in sorted((ROOT / "inputs").glob("gen-*.json")):
        for s in json.loads(p.read_text(encoding="utf-8"))["schemes"]:
            corpus[s["name"]] = s
    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))

    out = []
    for p in picks:
        rec = corpus.get(scheme_of(p["name"]))
        if rec is None:
            continue
        asked = max((float(op.get("storeys") or 0) for op in rec.get("ops", [])), default=0.0)
        storey = float(rec.get("floor_height_m") or site.floor_height_m)
        src = rebuild(p["name"], corpus, site, buildable, axis, max(base, asked * site.floor_height_m))
        if src is None:
            continue
        areas = storey_areas(src, height_m=float(p["height_m"] or 0.0), storey_m=storey)
        out.append({"id": p["id"], "family": p["family"], "storey_m": storey,
                    "areas_m2": [round(a, 1) for a in areas]})
    path = folder.parent / f"{run}-pick" / "floor_areas.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(out)} picks")
    for r in out[:6]:
        print(f"  #{r['id']:02d} {r['family'][:30]:<30} " +
              " ".join(f"{a:.0f}" for a in r["areas_m2"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
