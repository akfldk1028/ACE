"""The architect picks: the grid proposes, a person chooses.

Blind judging measured the top of this pipeline's pool at roughly one
fault-free drawing in four, which is a normal hit rate for massing studies
and the reason the final say was moved to eyes (관8). This tool takes the
same principle one step further back: instead of shipping one winner per
cell, it renders the strongest few per cell as one gallery, so the person
the sheet is for can pick from the pool the machine would otherwise pick
from alone.

    python tools/picksheet.py <run> [per_cell] [style]   # style: massing|clay
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from finalists import PNU, rebuild, scheme_of  # noqa: E402  (django setup inside)

from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(run: str, per_cell: int = 3, style: str = "massing") -> int:
    folder = ROOT / "runs" / run
    out = ROOT / "runs" / f"{run}-pick"
    out.mkdir(parents=True, exist_ok=True)
    summary = json.loads((folder / "massv2-summary.json").read_text(encoding="utf-8"))
    recs = [
        r for r in summary["records"]
        if "plausibility" in r
        and r["plausibility"]["occupiable"] and r["far_utilization"] >= 0.375
    ]
    parcel = float(summary["site"]["parcel_area_m2"])
    far_ratio = float(summary["site"]["far_capacity_m2"]) / parcel

    corpus = {}
    for p in sorted((ROOT / "inputs").glob("gen-*.json")):
        for s in json.loads(p.read_text(encoding="utf-8"))["schemes"]:
            corpus[s["name"]] = s

    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    height = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2))
    )
    ring = [(float(x), float(y)) for x, y in site.site_local_utm.exterior.coords[:-1]]

    cells = sorted({r["cell"] for r in recs})
    picks = []
    index = 0
    # One family, one appearance *per stature band* - not once in the whole
    # gallery. Ranked per cell alone, one strong family filled eight of
    # forty-four frames and the sheet was a worse offer than eight families
    # nobody had seen; deduped globally instead, a family that wins a seated
    # cell can never appear as the tower it also has, and the growth work that
    # raised twenty-seven families showed up on five tiles. A village at 8 m
    # and the same village at 40 m are two different offers to the person
    # choosing. Stature is the axis, so it is the unit of variety too, and a
    # family can still appear at most four times.
    # A family already on the sheet somewhere takes a slot only when no family
    # nobody has seen can fill it: fresh first, repeats after. Without that,
    # per-band dedup alone spent forty-six frames on thirty-two families.
    seen = set()
    families: dict[str, int] = defaultdict(int)
    for cell in cells:
        band = cell.split("|")[0]
        ranked = sorted(
            (r for r in recs if r["cell"] == cell),
            key=lambda r: r.get("spoken_force") or 0.0, reverse=True,
        )
        row = []
        for r in ranked:
            name = scheme_of(r["name"])
            fam = (name, band)
            # A family may show at two statures, never three. Ordering by
            # freshness instead was tried and does nothing here: there are
            # always enough unseen families to fill every slot, so no second
            # stature ever gets one and the sheet stays what it was.
            if fam in seen or families[name] >= 2:
                continue
            seen.add(fam)
            families[name] += 1
            row.append(r)
            if len(row) >= per_cell:
                break
        for r in row:
            rec = corpus[scheme_of(r["name"])]
            # The budget the grid handed this sentence, not the parcel's own.
            # `generate_massv2._height_budget` raises it to whatever `storeys`
            # the sentence declares, and passing the parcel's four-storey
            # default here drew a different, shorter building than the row's
            # numbers describe: i_bakgong_gori was measured at 48.6 m and drawn
            # at 11.5 m, on a sheet whose whole purpose is to be looked at.
            asked = max((float(op.get("storeys") or 0)
                         for op in rec.get("ops", [])), default=0.0)
            budget = max(height, asked * site.floor_height_m)
            src = rebuild(r["name"], corpus, site, buildable, axis, budget)
            if src is None:
                continue
            index += 1
            png = out / f"pick-{index:02d}.png"
            render_masses(
                [(r["name"], src, {"thesis": rec.get("formal_principle", "")})],
                png, site_ring=ring, columns=1, tile=(900, 760), style=style,
            )
            ground = (r.get("legal_fit") or {}).get("ground_area_m2") or 0.0
            picks.append({
                "id": index, "png": png.name, "cell": cell, "name": r["name"],
                "family": scheme_of(r["name"]),
                "principle": rec.get("formal_principle", ""),
                "height_m": (r.get("measurement") or {}).get("height_m"),
                "far_pct": round(r["far_utilization"] * far_ratio * 100),
                "coverage_pct": round(ground / parcel * 100),
            })
    (out / "picks.json").write_text(
        json.dumps({"run": run, "picks": picks}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"{len(picks)} picks -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(
        sys.argv[1],
        int(sys.argv[2]) if len(sys.argv) > 2 else 3,
        sys.argv[3] if len(sys.argv) > 3 else "massing",
    ))
