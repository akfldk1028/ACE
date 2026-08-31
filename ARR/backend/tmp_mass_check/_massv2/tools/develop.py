"""The development loop: grow a chosen sentence instead of breeding new ones.

OMA makes a hundred and fifty models and then develops ONE through dozens of
passes; this pipeline only ever generated. The visible cost was measured all
week - first-legal-fit partis that read as diagrams next to the offices'
tuned models. This tool is the missing half: take a board winner, mutate its
OWN sentence locally (proportions, extremity, FAR attainment), deliver every
mutant down the same legal path, and stage parent-vs-mutant pairs for blind
pairwise judging - keep the child only when a judge prefers it.

Deterministic by construction: mutants vary by index, never by dice.

    python tools/develop.py <run> <variant-name> [count]
      -> runs/develop-<family>/ : mutant tiles + pairs/ + mutants.json
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from band_probe import corpus, schedule_of  # noqa: E402
from finalists import PNU, rebuild  # noqa: E402

from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# What development is allowed to touch, and how far. Caps mirror the
# vocabulary's own clamps - a mutant that leaves the language is not a
# development, it is a different sentence.
TUNABLE = {
    "pitch": (0.15, 1.2), "rise": (0.15, 1.2), "reach": (0.1, 0.45),
    "proud": (0.1, 1.0), "turn": (-60.0, 60.0), "height": (0.05, 1.0),
    "bar": (0.15, 0.4), "size": (0.15, 0.6), "ratio": (0.2, 0.8),
    "clearance": (0.1, 0.6), "at": (0.0, 1.0), "contrast": (1.0, 2.0),
    "spread": (1.0, 2.4), "over": (0.05, 0.6), "bite": (0.3, 0.75),
    "depth": (0.1, 0.5),
}
STEPS = (-0.30, -0.15, 0.15, 0.30)  # proportional nudges
FAR_FILL_STOREYS = (4, 5, 6, 7)     # the client axis: fill the volume


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def mutants_of(scheme: dict, count: int) -> list[dict]:
    """Local variations of one sentence, deterministic, in-language."""

    sites = []  # (op_index, param, base_value)
    for oi, op in enumerate(scheme["ops"]):
        for param, bounds in TUNABLE.items():
            if param in op and isinstance(op[param], (int, float)):
                sites.append((oi, param, float(op[param]), bounds))
    out = []
    serial = 0
    # 1) proportional nudges across every tunable site
    for oi, param, base_value, (lo, hi) in sites:
        for step in STEPS:
            if len(out) >= count:
                return out
            child = copy.deepcopy(scheme)
            child["ops"][oi][param] = round(_clamp(
                base_value * (1.0 + step) if param != "turn"
                else base_value + 60.0 * step, lo, hi), 3)
            serial += 1
            child["name"] = f"{scheme['name']}__d{serial:02d}_{param}{'+' if step > 0 else '-'}"
            out.append(child)
    # 2) extremize: push each site to its cap (the BIG rule - lukewarm
    #    parameters read as leftovers)
    for oi, param, base_value, (lo, hi) in sites:
        if len(out) >= count:
            return out
        child = copy.deepcopy(scheme)
        cap = hi if base_value >= (lo + hi) / 2 else lo
        child["ops"][oi][param] = cap
        serial += 1
        child["name"] = f"{scheme['name']}__d{serial:02d}_{param}cap"
        out.append(child)
    # 3) FAR attainment: the client wants the volume filled - say more storeys
    for storeys in FAR_FILL_STOREYS:
        if len(out) >= count:
            return out
        child = copy.deepcopy(scheme)
        opener = child["ops"][0]
        if float(opener.get("storeys") or 0) == storeys:
            continue
        opener["storeys"] = storeys
        opener["height"] = round(_clamp(
            float(opener.get("height") or 0.5) * storeys
            / max(1.0, float(opener.get("storeys") or 3)), 0.1, 1.0), 3)
        serial += 1
        child["name"] = f"{scheme['name']}__d{serial:02d}_far{storeys}f"
        out.append(child)
    return out


def main(run: str, variant: str, count: str = "24") -> int:
    summary = json.loads((ROOT / "runs" / run / "massv2-summary.json")
                         .read_text(encoding="utf-8"))
    book = corpus()
    schedule = schedule_of(run)
    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    parcel = float(summary["site"]["parcel_area_m2"])

    family = variant.split("~")[0].split("^")[0]
    parent_scheme = book[family]
    out = ROOT / "runs" / f"develop-{family[:28]}"
    (out / "pairs").mkdir(parents=True, exist_ok=True)

    def deliver(scheme, name_for_pipeline):
        local_book = dict(book)
        local_book[scheme["name"].split("~")[0].split("^")[0]] = scheme
        asked = max((float(op.get("storeys") or 0) for op in scheme["ops"]),
                    default=0.0)
        return rebuild(name_for_pipeline, local_book, site, buildable, axis,
                       max(base, asked * site.floor_height_m),
                       schedule=schedule)

    parent_source = deliver(parent_scheme, variant)
    if parent_source is None:
        print("parent rebuild failed"); return 1

    ledger = []
    kept = 0
    for child in mutants_of(parent_scheme, int(count)):
        child_family = child["name"]
        # the mutant keeps the parent's variant suffixes (siting/coverage)
        child_variant = variant.replace(family, child_family, 1)
        child_source = deliver(child, child_variant)
        if child_source is None:
            ledger.append({"name": child["name"], "delivered": False})
            continue
        kept += 1
        pair = out / "pairs" / f"p{kept:02d}.png"
        render_masses(
            [("A", parent_source, {}), ("B", child_source, {})],
            pair, site_ring=list(buildable.exterior.coords),
            columns=2, tile=(620, 560), style="massing")
        ledger.append({"name": child["name"], "delivered": True,
                       "pair": pair.name})
    (out / "mutants.json").write_text(
        json.dumps({"parent": variant, "children": ledger},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{kept} delivered mutants, pairs -> {out / 'pairs'}")
    print("next: blind pairwise judges pick A or B per pair; "
          "keep B only where preferred; repeat on the winner.")
    return 0


def score(family_dir: str, verdict_paths: list[str]) -> int:
    """Aggregate blind pairwise verdicts; a child wins only unanimously.

    Ties and splits go to the parent - the incumbent rule, because a
    development step that cannot convince every judge is not an improvement,
    it is drift. Writes champion.json naming the winning child (the one with
    the most decisive support), ready for the next development round.
    """

    import re

    out = ROOT / "runs" / family_dir
    record = json.loads((out / "mutants.json").read_text(encoding="utf-8"))
    votes: dict[str, list[str]] = {}
    for path in verdict_paths:
        for pair, choice in re.findall(r"PAIR\s+(p\d+):\s*([AB])",
                                       Path(path).read_text(encoding="utf-8")):
            votes.setdefault(pair, []).append(choice)
    winners = []
    for child in record["children"]:
        if not child.get("delivered"):
            continue
        pair = child["pair"].removesuffix(".png")
        cast = votes.get(pair, [])
        if cast and all(vote == "B" for vote in cast):
            winners.append(child["name"])
        child["votes"] = "".join(cast)
    record["unanimous_children"] = winners
    record["champion"] = winners[0] if winners else None
    (out / "champion.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pairs judged {len(votes)}, unanimous child wins {len(winners)}")
    for name in winners:
        print("  WIN", name.split("__")[-1])
    print("champion:", record["champion"] or "parent holds (no unanimous win)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--score" in sys.argv:
        i = sys.argv.index("--score")
        sys.exit(score(sys.argv[1], sys.argv[i + 1:]))
    sys.exit(main(*sys.argv[1:4]))
