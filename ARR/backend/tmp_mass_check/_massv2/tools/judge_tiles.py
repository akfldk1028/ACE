"""Anonymous tiles for a blind round, and the key that says what they were.

A judge who can read `kahn_kimbell_three_ranges_of_vaults` off the drawing is
not judging the drawing. So each mass is rendered on its own with a number and
its own thesis sentence - what the scheme is for, which a jury does get - and
nothing that says which sentence wrote it, which run made it, or whether it is
old or new.

The key is written beside the tiles rather than into them, so a round can be
scored first and attributed afterwards. `runs/judge/prompts.json` holds the
rubric; do not edit it between rounds.

    python tools/judge_tiles.py <run> [count] [out-dir-name]
    python tools/judge_tiles.py uij-many 10 judge-0831
"""

import json
import random
import sys
from pathlib import Path

from band_probe import corpus, schedule_of  # noqa: E402  (django setup inside)
from finalists import PNU, rebuild  # noqa: E402

from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(run: str, count: str = "10", out_name: str = "") -> int:
    summary = json.loads(
        (ROOT / "runs" / run / "massv2-summary.json").read_text(encoding="utf-8"))
    book = corpus()
    schedule = schedule_of(run)
    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    parcel = float(summary["site"]["parcel_area_m2"])

    chosen = (summary.get("selection") or {}).get("chosen_names") or []
    wanted = int(count)
    # Shuffled with a fixed seed: the order a judge reads them in should not be
    # the order the selector ranked them, or the first tile carries the
    # recommendation without anyone saying so.
    order = list(chosen)
    random.Random(20260831).shuffle(order)

    out = ROOT / "runs" / (out_name or f"judge-{run}")
    out.mkdir(parents=True, exist_ok=True)
    key = []
    made = 0
    for name in order:
        if made >= wanted:
            break
        family = name.split("~")[0].split("^")[0]
        parti = book.get(family)
        if parti is None:
            continue
        asked = max((float(op.get("storeys") or 0) for op in parti["ops"]), default=0.0)
        source = rebuild(name, book, site, buildable, axis,
                         max(base, asked * site.floor_height_m), schedule=schedule)
        if source is None:
            continue
        record = next((r for r in summary["records"] if r["name"] == name), None)
        fit = (record or {}).get("legal_fit") or {}
        ground = float(fit.get("ground_area_m2") or 0.0)
        gross = float(fit.get("gross_floor_area_m2") or 0.0)
        made += 1
        tile = f"t{made:02d}"
        render_masses(
            [(tile, source, {
                # The thesis, because a jury is told what an option is for. The
                # sentence's own name is not, because that is the answer sheet.
                "thesis": str(parti.get("formal_principle") or "")[:180],
                "건폐율": f"{ground / parcel * 100:.0f}%",
                "용적률": f"{gross / parcel * 100:.0f}%",
            })],
            out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
            columns=1, tile=(900, 820), style="massing",
        )
        key.append({"tile": tile, "run": run, "name": name,
                    "cell": (record or {}).get("cell"),
                    "coverage_pct": round(ground / parcel * 100, 1),
                    "storeys": round(gross / max(ground, 1e-9), 1)})

    # The rubric travels with the round it judged.
    (out / "prompts.json").write_text(
        (ROOT / "inputs" / "judge-prompts.json").read_text(encoding="utf-8"),
        encoding="utf-8")
    (out / "key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{made} tiles -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
