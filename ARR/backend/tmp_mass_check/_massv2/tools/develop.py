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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from band_probe import corpus, schedule_of  # noqa: E402
from finalists import PNU, rebuild, BUILDING_TYPE  # noqa: E402

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
    site = load_legal_site(PNU, building_type=BUILDING_TYPE)
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    parcel = float(summary["site"]["parcel_area_m2"])

    family = variant.split("~")[0].split("^")[0]
    parent_scheme = book[family]
    out = ROOT / "runs" / f"develop-{family[:28]}"
    (out / "pairs").mkdir(parents=True, exist_ok=True)
    # A juror reads the folder, not mutants.json: a run that stages three
    # pairs where the last staged thirteen would be judged on ten images
    # nothing points at any more.
    for stale in (out / "pairs").glob("p*.png"):
        stale.unlink()

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

    def delivered_shape(source) -> tuple:
        """What the mass actually is, to the metre - plans and their heights.

        Two mutants that differ only in a parameter the growth loop then
        normalises away deliver this same tuple, and staging them as a choice
        asks a juror to compare an image with itself.
        """

        height = float(source.metadata.get("authored_height_m") or 0.0)

        def section_of(volume) -> tuple:
            # A pitch, a warp or a walkable slope changes the building without
            # moving a footprint or an elevation: `gabled_halves` applies a
            # pitch by replacing top_drop and ridge_along on the same volume.
            # Hashing plans alone called every such mutant a duplicate.
            return (
                round(float(getattr(volume, "top_drop", 0.0) or 0.0), 3),
                tuple(round(v, 3) for v in (getattr(volume, "drop_toward", None) or ())),
                tuple(round(v, 3) for v in (getattr(volume, "ridge_along", None) or ())),
                tuple((round(u, 3), round(h, 3))
                      for u, h in (getattr(volume, "top_profile", None) or ())),
                bool(getattr(volume, "top_walkable", False)),
                getattr(volume, "warp", None) is not None,
                str(getattr(volume, "verb", "")),
            )

        return tuple(sorted(
            (round(volume.footprint.area, 1),
             tuple(round(value, 1) for value in volume.footprint.bounds),
             round(float(volume.bottom_fraction) * height, 1),
             round(float(volume.top_fraction) * height, 1),
             # The plan's own shape, not just its box: a notch moved from one
             # end to the other is a mirror with the same area and bounds.
             tuple(sorted((round(x, 1), round(y, 1))
                          for x, y in volume.footprint.exterior.coords)),
             section_of(volume))
            for volume in source.volumes
        ))

    ledger = []
    kept = 0
    erased = 0
    seen_shapes = {delivered_shape(parent_source)}
    for child in mutants_of(parent_scheme, int(count)):
        child_family = child["name"]
        # the mutant keeps the parent's variant suffixes (siting/coverage)
        child_variant = variant.replace(family, child_family, 1)
        child_source = deliver(child, child_variant)
        if child_source is None:
            ledger.append({"name": child["name"], "delivered": False})
            continue
        shape = delivered_shape(child_source)
        if shape in seen_shapes:
            # Asked for something else and got this again: the mutation was
            # inside what the growth loop normalises, so there is nothing to
            # judge.
            erased += 1
            ledger.append({"name": child["name"], "delivered": True,
                           "erased_by_delivery": True})
            continue
        seen_shapes.add(shape)
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
    if erased:
        print(f"{erased} mutants arrived as a building already staged - the "
              "growth loop normalised the change away; not offered as a choice")
    print("next: blind pairwise judges pick A or B per pair; "
          "keep B only where preferred; repeat on the winner.")
    return 0


def _mutation_serial(name: str) -> int:
    """The mutation's own serial, read off the name mutants_of gave it."""

    hit = re.search(r"__d(\d+)_", name)
    return int(hit.group(1)) if hit else 10 ** 6


def _mutation_change(parent: dict, child: dict) -> str:
    """What the mutation moved, read off the two dicts rather than the name.

    The name says `bar+`; the brief has to say which op and by how much, or
    the next author cannot avoid re-proposing the parent's value.
    """

    moves = []
    for index, (before, after) in enumerate(zip(parent["ops"], child["ops"])):
        for key, value in after.items():
            if key != "why" and before.get(key) != value:
                moves.append(f"ops[{index}].{key} {before.get(key)} -> {value}")
    return ", ".join(moves) or "no parameter moved"


def _champion_pair(record: dict) -> tuple[dict, dict] | None:
    """The parent sentence and the champion's own, as dicts.

    The champion is the parent with one mutation applied, and mutants_of
    already builds exactly that dict deterministically - so the winner is
    regenerated from the parent by name rather than re-derived here. A second
    derivation of the same thing is the hand-copy the one-owner rule exists
    to stop; the extract gap parameter was written twice in two coordinate
    systems that way.
    """

    family = str(record["parent"]).split("~")[0].split("^")[0]
    parent = corpus().get(family)
    if parent is None:
        return None
    for child in mutants_of(parent, len(record["children"])):
        if child["name"] == record["champion"]:
            return parent, child
    return None


def _with_developed_why(parent: dict, child: dict) -> dict:
    """The champion's prose says what its value now is.

    The champion is the parent with one parameter moved, and it carried the
    parent's `why` unchanged - so a sentence that said "a 3 m gap so the
    court reads as a court" shipped with gap 4.5, and the next author read
    the argument for a value the mass no longer has. The moved op's why now
    ends with the move and how it was decided.
    """

    ops = []
    for before, after in zip(parent["ops"], child["ops"]):
        after = dict(after)
        moves = [f"{key} {before.get(key)} -> {value}"
                 for key, value in after.items()
                 if key != "why" and before.get(key) != value]
        if moves:
            why = str(after.get("why") or "").rstrip(". ")
            after["why"] = (f"{why}. Developed: {', '.join(moves)}, "
                            f"chosen over the parent by a unanimous blind pairwise jury.")
        ops.append(after)
    return {**child, "ops": ops}


def _seat_in_corpus(scheme: dict) -> str:
    """Append the winning sentence to the authored corpus.

    champion.json was written and then read by nothing: a development that
    beat its parent in front of a jury reached neither the corpus, nor the
    board, nor the next author, so the only real result a development round
    produces evaporated when the round ended. A run delivers what the books
    hold, so the champion belongs in a book.
    """

    path = ROOT / "inputs" / "gen-develop.json"
    book = (json.loads(path.read_text(encoding="utf-8"))
            if path.exists() else {"schemes": []})
    if any(seated.get("name") == scheme["name"] for seated in book["schemes"]):
        return f"already in {path.name}: {scheme['name']}"
    book["schemes"].append(scheme)
    path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + '\n',
                    encoding="utf-8")
    return f"seated in {path.name}: {scheme['name']}"


def score(family_dir: str, verdict_paths: list[str]) -> int:
    """Aggregate blind pairwise verdicts; a child wins only unanimously.

    Ties and splits go to the parent - the incumbent rule, because a
    development step that cannot convince every judge is not an improvement,
    it is drift. Writes champion.json naming the winning child - the one the
    most jurors voted for - and seats that child's sentence in the corpus so
    the next run can deliver it.
    """

    out = ROOT / "runs" / family_dir
    record = json.loads((out / "mutants.json").read_text(encoding="utf-8"))
    jurors = len(verdict_paths)
    votes: dict[str, list[str]] = {}
    for path in verdict_paths:
        for pair, choice in re.findall(r"PAIR\s+(p\d+):\s*([AB])",
                                       Path(path).read_text(encoding="utf-8")):
            votes.setdefault(pair, []).append(choice)
    winners: list[tuple[int, int, str]] = []
    for child in record["children"]:
        if not child.get("delivered"):
            continue
        # A mutant that arrived as a building already staged has no pair and
        # no vote: the growth loop normalised its change away, so there was
        # nothing for a judge to choose between. It stays in the ledger as
        # the measurement of that, and is not counted as a loss.
        if not child.get("pair"):
            child["votes"] = ""
            continue
        pair = child["pair"].removesuffix(".png")
        cast = votes.get(pair, [])
        # Unanimity has to mean every juror who was handed a sheet, not every
        # vote that happened to arrive: one verdict file saying B used to read
        # as a consensus, which is how a single opinion could rewrite the
        # corpus. Requiring one vote per file makes a one-juror round look
        # like a one-juror round, and champion.json records the count.
        if cast and len(cast) >= jurors and all(vote == "B" for vote in cast):
            winners.append((len(cast), _mutation_serial(child["name"]),
                            child["name"]))
        child["votes"] = "".join(cast)
    # The docstring promised the most decisive support and the code took
    # whichever child the ledger happened to list first - which is mutation
    # order, not jury order. Sort by how many jurors voted the pair, then by
    # the mutation serial so a tie goes to the smaller, earlier change: the
    # nearer development is the one the parent's virtues survive.
    winners.sort(key=lambda row: (-row[0], row[1]))
    names = [name for _, _, name in winners]
    record["unanimous_children"] = names
    record["champion"] = names[0] if names else None
    record["jurors"] = jurors
    seated = ""
    if record["champion"]:
        pair = _champion_pair(record)
        if pair is None:
            seated = (f"champion {record['champion']} not seated - the corpus "
                      f"has no parent named {record['parent']}")
        else:
            parent_scheme, champion_scheme = pair
            record["champion_change"] = _mutation_change(parent_scheme,
                                                         champion_scheme)
            seated = _seat_in_corpus(_with_developed_why(parent_scheme, champion_scheme))
    (out / "champion.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pairs judged {len(votes)}, jurors {jurors}, "
          f"unanimous child wins {len(names)}")
    for name in names:
        print("  WIN", name.split("__")[-1])
    print("champion:", record["champion"] or "parent holds (no unanimous win)")
    if seated:
        print(seated)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--score" in sys.argv:
        i = sys.argv.index("--score")
        sys.exit(score(sys.argv[1], sys.argv[i + 1:]))
    sys.exit(main(*sys.argv[1:4]))
