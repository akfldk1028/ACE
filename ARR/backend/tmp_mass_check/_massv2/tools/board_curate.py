"""The selection board, assembled from the ledgers instead of by hand.

The board was curated manually three times in one evening, and each time a
family of near-identical partis slipped through in a different way. This
tool owns the whole path now: it collects every juried result (both tracks,
every round), computes each passer's composition family from its sentence,
keeps the best-scored member per family per track, and emits the board key.
Rendering and publishing read that key; nobody picks tiles by eye again.

    python tools/board_curate.py          # writes runs/board/board-key.json + ledger
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from family_key import family_key, one_per_family  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Every juried round, its track, and where its scores live. Anchor entries
# re-judged in later rounds keep their latest score (rounds listed newest
# last override).
ROUNDS = [
    ("K", "runs/judge-24/final-ranking.json", "final"),
    ("O", "runs/judge-ovs/vlm-shortlist.json", "shortlist"),
    ("O", "runs/judge-void-ovs/vlm-shortlist.json", "shortlist"),
    ("K", "runs/judge-void-kor/vlm-shortlist.json", "shortlist"),
    ("O", "runs/judge-refix/vlm-shortlist.json", "corrected"),
    ("O", "runs/judge-ovs2/vlm-shortlist.json", "shortlist"),
    ("O", "runs/vlm-ovs9-family/vlm-shortlist.json", "shortlist"),
    ("O", "runs/vlm-ovs10-new/vlm-shortlist.json", "shortlist"),
    # Rule 0's corollary: the smooth-curve renderer changed the drawings, so
    # the seated overseas entries were re-judged on the rebaked tiles under
    # the track's own rubric. Newest-last, so these scores override.
    ("O", "runs/vlm-board-rejudge-1/vlm-shortlist.json", "corrected"),
    # The partial correction above re-judged only the SEATED entries, and
    # curation then compared its new-rubric scores against merged-out
    # partners still holding old-rubric numbers - two scales, one contest,
    # and the board flipped. One ruler over the whole passing ledger:
    ("O", "runs/vlm-o-full-rejudge/vlm-shortlist.json", "corrected"),
    ("O", "runs/vlm-ovs11-new/vlm-shortlist.json", "shortlist"),
    # First anchor-corrected round: three seated entries rode anonymously and
    # --score removed the session's measured -0.36 drift before recording.
    ("O", "runs/vlm-ovs14-r2/vlm-shortlist.json", "shortlist"),
    # First English-authored round (the prompt-language probe): same brief,
    # instructions and whys in English. Anchor-corrected like every round.
    ("O", "runs/vlm-ovs15-en/vlm-shortlist.json", "shortlist"),
    # Roof-section round: the client said the gables were gone; these
    # win their seats through the jury instead of squatting in a canon row.
    ("O", "runs/vlm-ovs16-en/vlm-shortlist.json", "shortlist"),
    # Pilotis + wide-slab round (closed-loop r2): the lifted court ring
    # and the punched mat, seats won by jury after the canon row left.
    ("O", "runs/vlm-ovs17-en/vlm-shortlist.json", "shortlist"),
    # The first round authored, revised and juried by massagent itself -
    # three independent juror processes, anchor-corrected (drift -1.02).
    ("O", "runs/vlm-agent01/vlm-shortlist.json", "shortlist"),
    # agent02: authored, sheet-diagnosed and revised (r2) by massagent,
    # judged by the pinned sonnet jury under the no-shift rule.
    ("O", "runs/vlm-agent02/vlm-shortlist.json", "shortlist"),
    # sweep01: the first grammar-sweep round - 300 generated sentences,
    # 5,132 variants, first-ever 16/16 cell fill; jury drift -0.48 applied.
    ("O", "runs/vlm-sweep01/vlm-shortlist.json", "shortlist"),
    # 09-02 surgery day: executor, gates and renderer changed (height budget,
    # roof-on-top-tier, crumb width, shift span, fracture lean, ridge
    # vectors, structure-per-part). One ruler: the whole passing overseas
    # ledger re-judged on the final engine, then the first authored round
    # written against the empty-family map on that engine.
    ("O", "runs/vlm-board-rejudge-s7/vlm-shortlist.json", "corrected"),
    ("O", "runs/vlm-ovs18-en/vlm-shortlist.json", "shortlist"),
]
# The anchor-corrected pass thresholds recorded per round live in the
# shortlists as `pass`; the korea final ranking predates that format.
KOREA_FINAL_PASS = 3.5 - 0.5  # anchor-corrected cut of that round


def corpus() -> dict:
    book = {}
    # Sweep books live outside inputs/ so the authored canon stays clean,
    # but their sentences must still resolve once staged or juried.
    paths = sorted((ROOT / "inputs").glob("gen-*.json")) +         sorted((ROOT / "runs" / "sweeps").glob("*.json"))
    for path in paths:
        for scheme in json.loads(path.read_text(encoding="utf-8"))["schemes"]:
            book[scheme["name"]] = scheme
    return book


def main() -> int:
    book = corpus()
    ledger: dict[tuple, dict] = {}
    for track, rel, kind in ROUNDS:
        path = ROOT / rel
        if not path.exists():
            continue
        # Anchors ride a round to calibrate it; they are not re-contested by
        # it. Recording their ride-corrected scores let the ruler measure
        # itself - anchor spread compressed 23-48% per ride and one seat
        # drifted 3.29 -> 3.50 with no contest. New shortlists carry an
        # `anchor` flag; older ones are covered by the sibling key.json,
        # where an anchor row is any entry holding an `anchor` value.
        anchor_names: set[str] = set()
        key_path = path.parent / "key.json"
        if key_path.exists():
            anchor_names = {
                r["name"] for r in json.loads(key_path.read_text(encoding="utf-8"))
                if r.get("anchor") is not None
            }
        for row in json.loads(path.read_text(encoding="utf-8")):
            name = row["name"]
            if row.get("anchor") or name in anchor_names:
                continue
            score = float(row.get("corrected") or row.get("score") or 0.0)
            passed = bool(row.get("pass")) if "pass" in row else score >= KOREA_FINAL_PASS
            ledger[(track, name)] = {
                "track": track, "name": name, "score": round(score, 2),
                "pass": passed, "round": rel.split("/")[1],
            }
    passers = [item for item in ledger.values() if item["pass"]]

    def key_of(item):
        family = item["name"].split("~")[0].split("^")[0]
        scheme = book.get(family)
        # The canon layer competes only with itself: family_key cannot tell a
        # canonical cylinder from an experimental one, and without the layer
        # in the key one_per_family evicted the repertoire §11 promises is
        # always present. The layer's owner is the scheme record.
        layer = (scheme or {}).get("layer") or "experimental"
        return (item["track"], layer) + (family_key(scheme) if scheme else (family,))

    curated = one_per_family(passers, key_of=key_of,
                             score_of=lambda item: item["score"])
    # The family key is a partition of the LANGUAGE - opener, dominant verb,
    # stature - and two sentences built from different words can still be one
    # drawing: three court rings held three seats through three different
    # openers. The eye pass records who reads as whom (a blind judge, tiles
    # only, written to visual-groups.json as sentence names), and within a
    # visual group only the best score keeps its seat. The doctrine is old:
    # the cell final is judged by eyes.
    visual = ROOT / "runs" / "board" / "visual-groups.json"
    if visual.exists():
        groups = json.loads(visual.read_text(encoding="utf-8"))["groups"]
        # Entries are TRACK:sentence editions - a verdict is about the tile
        # the judge saw, and the K edition of a sentence is a different tile
        # from its O edition. Keying by bare sentence chained one edition's
        # verdict onto the other's partners and over-merged whole rows.
        def edition(name: str) -> str:
            if ":" in name:
                return name
            return "O:" + name.split("~")[0].split("^")[0]

        # Each recorded group is a CLIQUE the judge actually saw together.
        # Union-find chained overlapping groups transitively - a flat plate,
        # a rising wedge and stepped terraces shared one seat though
        # wedge-terraces was never judged as a pair - so groups no longer
        # merge with each other: an edition loses its seat only to a member
        # of a group it was directly judged in.
        cliques: list[tuple[list[str], str | None]] = []
        for group in groups:
            names = group["members"] if isinstance(group, dict) else group
            keep = group.get("keep") if isinstance(group, dict) else None
            cliques.append(([edition(n) for n in names],
                            edition(keep) if keep else None))
        member_of: dict[str, list[int]] = {}
        for index, (members, _keep) in enumerate(cliques):
            for name in members:
                member_of.setdefault(name, []).append(index)
        by_edition: dict[str, dict] = {}
        for item in curated:
            name = item["track"] + ":" +                 item["name"].split("~")[0].split("^")[0]
            held = by_edition.get(name)
            if held is None or item["score"] > held["score"]:
                by_edition[name] = item
        dropped_ids: set[int] = set()
        for members, keep in cliques:
            present = [by_edition[m] for m in members if m in by_edition]
            if len(present) < 2 and keep is None:
                continue
            if keep is not None and keep in by_edition:
                winner = by_edition[keep]
            elif present:
                winner = max(present, key=lambda it: it["score"])
            else:
                continue
            for item in present:
                if id(item) != id(winner):
                    dropped_ids.add(id(item))
        dropped = [item for item in curated if id(item) in dropped_ids]
        for item in dropped:
            print(f"  eye-merged out: {item['name'][:48]} ({item['score']:.2f})")
        curated = [item for item in curated if id(item) not in dropped_ids]

    # One sentence, one seat on the whole page: a sentence that passed both
    # juries held K6 and O2 at once, and to the client that is the same
    # building printed twice whatever the tracks' briefs did to its size.
    # Runs AFTER the eye pass: an edition the eye already merged away must not first evict its twin from the other track and then die itself, orphaning the sentence. No judge needed for this tier - same name is same drawing by
    # construction; the higher-scored edition represents it.
    best_by_sentence: dict[str, dict] = {}
    for item in curated:
        sentence = item["name"].split("~")[0].split("^")[0]
        held = best_by_sentence.get(sentence)
        if held is None or item["score"] > held["score"]:
            best_by_sentence[sentence] = item
    for item in curated:
        sentence = item["name"].split("~")[0].split("^")[0]
        if id(item) != id(best_by_sentence[sentence]):
            print(f"  cross-track duplicate out: {item['track']} "
                  f"{item['name'][:44]} ({item['score']:.2f})")
    curated = [item for item in curated
               if id(item) == id(best_by_sentence[
                   item["name"].split("~")[0].split("^")[0]])]

    board = []
    counters = {"K": 0, "O": 0}
    for track in ("K", "O"):
        for item in curated:
            if item["track"] != track:
                continue
            counters[track] += 1
            board.append({"label": f"{track}{counters[track]}",
                          "name": item["name"], "score": item["score"],
                          "round": item["round"]})
    # The canon is not a contestant. Section 11 promises the standard
    # repertoire is ALWAYS present, and for a season it wasn't: the canon
    # round was authored, closed-looped and never juried, so the wide slab,
    # the pilotis slab and the cylinder simply never appeared before the
    # client. Canon seats by right - base sentence, file order, jury score
    # shown when one exists but never required.
    # The representative is the canon run's own chosen VARIANT, not the bare
    # sentence: rebuilding a base name fits the unspread form to the full
    # footprint and the cylinder bakes as a squat drum. The latest canon run
    # is the owner of which variant shows each type.
    CANON_RUN = "ovs13-v4"
    canon_pick: dict[str, str] = {}
    canon_summary = ROOT / "runs" / CANON_RUN / "massv2-summary.json"
    if canon_summary.exists():
        # Fallback only - the real representative is the eye's pick below.
        # (The v3 detour proved the band IS the type's proportion: exempting
        # the canon from coverage bands locked every exemplar to its plan-wide
        # seed and the ridge flattened. Bands are back; the eye chooses which
        # band reads as the type, stature-honest.)
        for row in json.loads(canon_summary.read_text(encoding="utf-8"))["records"]:
            if row.get("status") != "compiled" or                     (row.get("plausibility") or {}).get("reasons"):
                continue
            sentence = row["name"].split("~")[0].split("^")[0]
            held = canon_pick.get(sentence)
            if held is None or (row["name"].endswith("^centred")
                                and not held.endswith("^centred")):
                canon_pick[sentence] = row["name"]
    # Eye/typology overrides: the run's cell picks optimise coverage spread,
    # but a canon tile's job is to READ as its type - the tallest honest
    # cylinder, the steepest honest ridge. Recorded per sentence, stature-
    # honest, in canon-picks.json.
    picks_path = ROOT / "runs" / "board" / "canon-picks.json"
    if picks_path.exists():
        canon_pick.update(json.loads(picks_path.read_text(encoding="utf-8")))
    canon_count = 0
    for path in sorted((ROOT / "inputs").glob("gen-*.json")):
        for scheme in json.loads(path.read_text(encoding="utf-8"))["schemes"]:
            if scheme.get("layer") != "canon":
                continue
            canon_count += 1
            shown = canon_pick.get(scheme["name"], scheme["name"])
            judged = ledger.get(("O", shown)) or ledger.get(("O", scheme["name"]))
            board.append({"label": f"C{canon_count}",
                          "name": shown,
                          "score": judged["score"] if judged else None,
                          "round": judged["round"] if judged else "canon"})
    out = ROOT / "runs" / "board"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ledger.json").write_text(
        json.dumps(sorted(ledger.values(), key=lambda r: (-r["score"], r["name"])),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "board-key.json").write_text(
        json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    kept = {"K": counters["K"], "O": counters["O"]}
    print(f"ledger {len(ledger)} entries, passers {len(passers)}, "
          f"board K{kept['K']} + O{kept['O']} (one per family)")
    for row in board:
        score = f"{row['score']:.2f}" if row["score"] is not None else "  - "
        print(f"  {row['label']:>4} {score} {row['name'][:52]}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
