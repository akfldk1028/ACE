"""The arbitration stage: a VLM decides each cell final, not a proxy.

The full-set blind round measured every numeric judge this pipeline has
against pairwise VLM preference and none survived - spoken_force +0.27,
convexity -0.25, section +0.12 - while the judges' fault tags (one-lump,
envelope-residue, sentence-invisible) separated winners from losers cleanly.
Geometry proxies rank candidates well enough to shortlist; they cannot be
trusted with the final. So the grid's per-cell winner meets the strongest
different-family challenger in its cell, both rebuilt through the same
deterministic path the grid used, and a blind pairwise judgement takes the
cell. (QD-LLMs, GECCO 2026: vision-language evaluation in the loop.)

    python tools/finalists.py plan  <run>   -> renders + vlm-manifest/pairs
    python tools/finalists.py apply <run>   -> arbitrated alts.json from verdicts
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from design.maas.massv2.compile import compile_matrix_form  # noqa: E402
from design.maas.massv2.execute import execute as execute_parti  # noqa: E402
from design.maas.massv2.fill import fill_to_site  # noqa: E402
from design.maas.massv2.grammar import parti_from_record  # noqa: E402
from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import (  # noqa: E402
    OPEN_SIDE_SITINGS,
    SITINGS,
    open_side_direction,
    place_on_site,
)
from design.maas.massv2.variations import spread_across_coverage  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PNU = "4115011300106840001"


def scheme_of(name: str) -> str:
    return name.split("~")[0].split("^")[0]


def rebuild(name: str, corpus, site, buildable, axis, height):
    """One variant's delivered geometry, down the same path the grid walked."""

    rec = corpus.get(scheme_of(name))
    if rec is None:
        return None
    parti = parti_from_record(rec)
    if parti is None:
        return None
    storey = float(parti.floor_height_m or site.floor_height_m)
    form = execute_parti(
        parti, buildable=buildable, axis=axis, height_m=height,
        storey_height_m=storey,
    )
    if form is None:
        return None
    candidates = [form]
    candidates += spread_across_coverage(
        form,
        ground_capacity_m2=site.ground_capacity_m2,
        far_capacity_m2=site.far_capacity_m2,
        floor_height_m=site.floor_height_m,
    )
    open_side = open_side_direction(buildable, site.shared_edges)
    sitings = OPEN_SIDE_SITINGS if open_side is not None else SITINGS
    for base in list(candidates):
        for siting in sitings:
            moved = place_on_site(base, buildable, siting, open_side=open_side)
            if moved is not None:
                from dataclasses import replace
                candidates.append(replace(
                    moved, name=f"{base.name}^{siting.siting_id}",
                ))
    target = next((c for c in candidates if c.name == name), None)
    if target is None:
        return None
    grown = fill_to_site(target, site).fit.form
    return compile_matrix_form(
        grown, storey_height_m=storey, allowed_at=site.plan_at,
    )


def plan(run: str) -> int:
    folder = ROOT / "runs" / run
    out = ROOT / "runs" / f"{run}-arb"
    out.mkdir(parents=True, exist_ok=True)
    alts = json.loads((folder / "alts.json").read_text(encoding="utf-8"))["alternatives"]
    summary = json.loads((folder / "massv2-summary.json").read_text(encoding="utf-8"))
    recs = [r for r in summary["records"] if "plausibility" in r]

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

    # A challenger is the strongest candidate in the cell from a family the
    # sheet does not already hold - anywhere. Chosen per-cell without that
    # constraint, one strong all-rounder challenged ten cells and the blind
    # judges, who see one pair at a time, handed it five: the arbitration
    # was quietly undoing the sheet's own first rule, one sentence one tile.
    cards, pairs, duels = [], [], []
    taken = {scheme_of(a["name"]) for a in alts}
    used = set()
    for a in alts:
        cell = None
        for r in recs:
            if r["name"] == a["name"]:
                cell = r["cell"]; break
        if cell is None:
            continue
        family = scheme_of(a["name"])
        rivals = [
            r for r in recs
            if r["cell"] == cell
            and scheme_of(r["name"]) not in taken
            and scheme_of(r["name"]) not in used
            and r["plausibility"]["occupiable"] and r["far_utilization"] >= 0.375
        ]
        if not rivals:
            duels.append({"cell": a["cell"], "winner": a["name"], "challenger": None})
            continue
        rival = max(rivals, key=lambda r: r.get("spoken_force") or 0.0)
        used.add(scheme_of(rival["name"]))
        duels.append({"cell": a["cell"], "winner": a["name"], "challenger": rival["name"],
                      "challenger_record": {
                          "far_utilization": rival["far_utilization"],
                          "gfa_m2": rival.get("gfa_m2"),
                          "footprint_area_m2": (rival.get("measurement") or {}).get("footprint_area_m2"),
                      }})

    index = 0
    id_of = {}
    for duel in duels:
        for name in (duel["winner"], duel["challenger"]):
            if name is None or name in id_of:
                continue
            src = rebuild(name, corpus, site, buildable, axis, height)
            if src is None:
                continue
            index += 1
            cid = f"alt-{index:02d}"
            id_of[name] = cid
            rec = corpus[scheme_of(name)]
            png = out / f"{cid}.png"
            render_masses(
                [(name, src, {"thesis": rec.get("formal_principle", "")})],
                png, site_ring=ring, columns=1, tile=(900, 760),
            )
            cards.append({
                "id": cid, "png": str(png.resolve()), "scheme": name,
                "principle": rec.get("formal_principle", ""),
            })
    for duel in duels:
        w, c = duel["winner"], duel["challenger"]
        if c and w in id_of and c in id_of:
            pairs.append([id_of[w], id_of[c]])
            duel["pair"] = [id_of[w], id_of[c]]

    (out / "vlm-manifest.json").write_text(
        json.dumps({"run": f"{run}-arb", "cards": cards}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (out / "vlm-pairs.json").write_text(
        json.dumps({"run": f"{run}-arb", "pairs": pairs}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (out / "duels.json").write_text(
        json.dumps({"duels": duels}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(cards)} cards, {len(pairs)} duels -> {out}")
    return 0


def apply(run: str) -> int:
    folder = ROOT / "runs" / run
    out = ROOT / "runs" / f"{run}-arb"
    alts = json.loads((folder / "alts.json").read_text(encoding="utf-8"))
    duels = json.loads((out / "duels.json").read_text(encoding="utf-8"))["duels"]
    cards = {c["id"]: c for c in json.loads(
        (out / "vlm-manifest.json").read_text(encoding="utf-8"))["cards"]}
    verdicts = []
    for f in sorted(out.glob("vlm-verdict-*.json")):
        verdicts += json.loads(f.read_text(encoding="utf-8"))["verdicts"]
    won = {(v["a"], v["b"]): v for v in verdicts}
    summary = json.loads((folder / "massv2-summary.json").read_text(encoding="utf-8"))
    parcel = float(summary["site"]["parcel_area_m2"])
    far_ratio = float(summary["site"]["far_capacity_m2"]) / parcel

    corpus = {}
    for p in sorted((ROOT / "inputs").glob("gen-*.json")):
        for s in json.loads(p.read_text(encoding="utf-8"))["schemes"]:
            corpus[s["name"]] = s

    swaps = 0
    for a in alts["alternatives"]:
        duel = next((d for d in duels if d["winner"] == a["name"] and d.get("pair")), None)
        if duel is None:
            # keep, but point the tile at the arbitration render if we have it
            continue
        v = won.get(tuple(duel["pair"]))
        if v is None:
            continue
        w_id, c_id = duel["pair"]
        keep = v["winner"] == w_id
        chosen = w_id if keep else c_id
        card = cards[chosen]
        if not keep:
            swaps += 1
            rec = duel.get("challenger_record") or {}
            a["name"] = card["scheme"]
            a["thesis"] = corpus[scheme_of(card["scheme"])].get("formal_principle", "")
            if rec.get("far_utilization") is not None:
                a["용적률"] = f"{rec['far_utilization']*far_ratio*100:.0f}%"
            if rec.get("footprint_area_m2"):
                a["건폐율"] = f"{rec['footprint_area_m2']/parcel*100:.0f}%"
        a["png"] = f"{chosen}.png"
        a["arbitrated"] = True
        a["arb_why"] = v.get("why", "")
    (out / "alts.json").write_text(
        json.dumps(alts, ensure_ascii=False, indent=2), encoding="utf-8")
    # carry the summary over so the sheet builder finds it
    shutil.copy(folder / "massv2-summary.json", out / "massv2-summary.json")
    print(f"arbitrated: {swaps} cells swapped -> {out / 'alts.json'}")
    return 0


if __name__ == "__main__":
    mode, run = sys.argv[1], sys.argv[2]
    sys.exit(plan(run) if mode == "plan" else apply(run))
