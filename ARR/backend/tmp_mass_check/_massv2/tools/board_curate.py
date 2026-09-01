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
]
# The anchor-corrected pass thresholds recorded per round live in the
# shortlists as `pass`; the korea final ranking predates that format.
KOREA_FINAL_PASS = 3.5 - 0.5  # anchor-corrected cut of that round


def corpus() -> dict:
    book = {}
    for path in sorted((ROOT / "inputs").glob("gen-*.json")):
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
        for row in json.loads(path.read_text(encoding="utf-8")):
            name = row["name"]
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
        return (item["track"],) + (family_key(scheme) if scheme else (family,))

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
        # The file accumulates passes, so one sentence can appear in two
        # recorded groups (judged against different partners at different
        # times); overlapping groups union, or a shared member silently
        # splits a group and a merged-out entry walks back onto the board.
        # A contradicted verdict is handled where it belongs: by removing
        # the superseded pair from the file, never by resolution order here.
        parent: dict[str, str] = {}

        def find(node: str) -> str:
            while parent.setdefault(node, node) != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        # Entries are TRACK:sentence editions - a verdict is about the tile
        # the judge saw, and the K edition of a sentence is a different tile
        # from its O edition. Keying by bare sentence chained one edition's
        # verdict onto the other's partners and over-merged whole rows.
        def edition(name: str) -> str:
            if ":" in name:
                return name
            return "O:" + name.split("~")[0].split("^")[0]

        for names in groups:
            editions = [edition(n) for n in names]
            for other in editions[1:]:
                parent[find(other)] = find(editions[0])
        group_of = {node: find(node) for node in parent}
        best_in_group: dict[str, dict] = {}
        for item in curated:
            sentence = item["track"] + ":" + \
                item["name"].split("~")[0].split("^")[0]
            gid = group_of.get(sentence)
            if gid is None:
                continue
            # One seat per visual group on the WHOLE page, not per track: the
            # client reads one board, and the K edition of a scheme is the
            # same building at brief size - chain_of_turned_rooms held K6 and
            # O2 at once. The two juries' scales differ, but the question
            # here is only which edition represents the scheme.
            held = best_in_group.get(gid)
            if held is None or item["score"] > held["score"]:
                best_in_group[gid] = item
        kept_ids = {id(v) for v in best_in_group.values()}
        dropped = [
            item for item in curated
            if group_of.get(
                item["track"] + ":"
                + item["name"].split("~")[0].split("^")[0]) is not None
            and id(item) not in kept_ids
        ]
        for item in dropped:
            print(f"  eye-merged out: {item['name'][:48]} ({item['score']:.2f})")
        curated = [item for item in curated if id(item) not in {id(d) for d in dropped}]

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
        print(f"  {row['label']:>4} {row['score']:.2f} {row['name'][:52]}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
