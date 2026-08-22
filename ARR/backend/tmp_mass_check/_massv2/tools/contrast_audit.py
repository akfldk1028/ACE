"""Does the extreme a sentence declares survive to delivery?

A sentence that says "three corners pressed to the ground and one drawn up
to the extreme" is making a measurable claim: the tallest body should stand
several times the shortest. The postcondition gate only asks whether each
word changed the form at all, and spoken_force asks how much of the volume
a word accounts for. Neither asks whether the *ratio the sentence names*
arrived. via57 declares 6x and reads, on the sheet, as a box.

This walks the delivered picks and puts the two numbers side by side:
declared contrast (read off the operation arguments) against delivered
contrast (tallest body over shortest, measured on the geometry that shipped).

    python tools/contrast_audit.py <run>
"""

import json
import sys
from pathlib import Path

from finalists import PNU, rebuild, scheme_of  # noqa: E402  (django setup inside)

from design.maas.massv2.execute import execute as execute_parti  # noqa: E402
from design.maas.massv2.grammar import parti_from_record  # noqa: E402
from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def declared_contrast(rec):
    """The height ratio the sentence itself names, or None if it names none."""

    # The ratio a sentence names is between the height it gives the part it
    # presses down and the height it gives the part it draws up - not the
    # `contrast` argument, which only says how two tiers of one stack compare.
    heights = [
        float(op["height"]) for op in rec.get("ops", [])
        if op.get("height") is not None and float(op["height"]) > 0.0
    ]
    if len(heights) < 2:
        return None
    low, high = min(heights), max(heights)
    if low <= 0.0 or high / low < 1.15:
        return None
    return round(high / low, 2)


def delivered_contrast(src):
    """Highest top over lowest top, across the volumes that carry real plan.

    Measured per volume, not per body: a ring with one corner drawn up is a
    single connected body, so components cannot see the contrast the sentence
    is about. Slivers are excluded on the same 1%-of-plan rule the slenderness
    gate uses, so a parapet-sized offcut cannot fake a tall ratio.
    """

    vols = [v for v in src.volumes if v.footprint is not None]
    if len(vols) < 2:
        return None, len(vols)
    total = sum(v.footprint.area for v in vols)
    floor = max(10.0, 0.01 * total)
    tops = sorted(v.top_fraction for v in vols if v.footprint.area >= floor)
    if len(tops) < 2 or tops[0] <= 0.0:
        return None, len(vols)
    return round(tops[-1] / tops[0], 2), len(vols)


def main(run: str) -> int:
    folder = ROOT / "runs" / run
    picks = json.loads((folder.parent / f"{run}-pick" / "picks.json")
                       .read_text(encoding="utf-8"))["picks"]
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

    rows = []
    for p in picks:
        rec = corpus.get(scheme_of(p["name"]))
        if rec is None:
            continue
        src = rebuild(p["name"], corpus, site, buildable, axis, height)
        if src is None:
            continue
        got, n = delivered_contrast(src)
        # What this sentence could reach at all. The pressed-down part cannot
        # go below one storey - `box` holds every occupiable volume to one -
        # so on a budget of B metres with a storey of s, the deepest contrast
        # any sentence can express is B/s. via57 asks for 6.25x on a 12 m
        # budget where the ceiling is 4.14x, and nothing tells it so: the ring
        # is quietly raised from 1.92 m to 2.90 m and the sail becomes a box.
        asked_storeys = max((float(op.get("storeys") or 0)
                             for op in rec.get("ops", [])), default=0.0)
        storey = float(rec.get("floor_height_m") or site.floor_height_m)
        budget = max(height, asked_storeys * site.floor_height_m)
        # The same figure before any coverage or siting variant touched it.
        # The picked variant is one of many the grid spread the sentence
        # across, and spreading a tower over more ground shortens it - which
        # is the axis working, until it shortens the tower past the ratio the
        # sentence was about. Reading base against delivered separates "the
        # machine could not say it" from "a variant said it and then undid it".
        base = None
        parti = parti_from_record(rec)
        if parti is not None:
            form = execute_parti(
                parti, buildable=buildable, axis=axis, height_m=budget,
                storey_height_m=float(parti.floor_height_m or site.floor_height_m),
            )
            if form is not None:
                tops = sorted(
                    max(pl.matrix[2][0] * cx + pl.matrix[2][1] * cy
                        + pl.matrix[2][2] * cz + pl.matrix[2][3]
                        for cx in (0.0, 1.0) for cy in (0.0, 1.0) for cz in (0.0, 1.0))
                    for pl in form.placements
                    if getattr(pl, "kind", "additive") == "additive"
                )
                tops = [t for t in tops if t > 1e-6]
                if len(tops) >= 2:
                    base = round(tops[-1] / tops[0], 2)
        rows.append({
            "id": p["id"], "family": p["family"], "declared": declared_contrast(rec),
            "base": base, "delivered": got, "ceiling": round(budget / storey, 2),
            "volumes": n, "height_m": p["height_m"],
        })

    out = folder.parent / f"{run}-pick" / "contrast.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    named = [r for r in rows if r["declared"]]
    print(f"{len(rows)} picks, {len(named)} of them name a contrast")
    for r in sorted(named, key=lambda r: (r["delivered"] or 0.0) / r["declared"]):
        got = "한 조각" if r["delivered"] is None else f"{r['delivered']}x"
        base = "-" if r["base"] is None else f"{r['base']}x"
        if r["declared"] > r["ceiling"]:
            verdict = "  ← 예산이 못 담는 요구"
        elif r["base"] and r["delivered"] and r["delivered"] < r["base"] * 0.85:
            verdict = "  ← 변형이 문장을 되돌림"
        else:
            verdict = ""
        print(f"  #{r['id']:02d} {r['family'][:34]:<34} 선언 {r['declared']:>5}x"
              f"  상한 {r['ceiling']:>5}x  기본 {base:>6}  배달 {got}{verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
