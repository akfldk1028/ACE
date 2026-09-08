"""The run's corpus: the repertoire's families, with this round's book and the champions on top.

Twelve cycles ran only the round's own six sentences plus the carried
champions - 8 sentences, 181 variants in comp12 - while 1,578 sentences sat
in the corpus: the BIG, OMA and SANAA rounds, the sweeps, the twisting stack,
the sail over the court, the folded plate bar. None of them competed, so the
architect saw them vanish from the board without anyone deciding they should.

Running all 1,578 costs hours (about 2.6 s per sentence before variants).
The corpus holds 207 families under the curator's own key - opener, dominant
move, stature band - and the board seats one sentence per family anyway, so
the run competes one representative per family: the member the juries
scored highest, else the newest. That is the whole language every round at
a seventh of the cost.

MASS_RUN_SCOPE=families (default), cumulative (every sentence), round (this
round's book only, for a deliberate narrow test).
"""
import glob
import json
import os
from pathlib import Path
import sys


def _all_books(ws: Path) -> dict:
    """Every sentence the workspace holds, by name - same globs as band_probe.corpus()."""
    out = {}
    paths = sorted((ws / "inputs").glob("gen-*.json")) + sorted((ws / "runs" / "sweeps").glob("*.json"))
    for path in paths:
        try:
            schemes = json.loads(path.read_text(encoding="utf-8-sig"))["schemes"]
            if not all(isinstance(item, dict) and item.get("name") for item in schemes):
                raise ValueError("schemes must be records with names")
        except Exception as exc:  # noqa: BLE001 - a half-written book must not take the run down
            print(f"corpus: skipping {path.name} ({type(exc).__name__}: {exc})", file=sys.stderr)
            continue
        for scheme in schemes:
            out[scheme["name"]] = scheme
    return out


def _family_key(scheme: dict, ws: Path):
    """The curator's family key, from the engine. Tests replace this."""
    tools = ws / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import band_probe  # noqa: F401  (Django and the backend path, as every tool does)
    from design.maas.massv2.family import family_key
    return family_key(scheme)


def _best_scores(ws: Path) -> dict:
    """Highest jury score ever given to each authored sentence root: root -> (score, variant name)."""
    best: dict = {}
    for path in glob.glob(str(ws / "runs" / "vlm-*" / "vlm-shortlist.json")):
        try:
            rows = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for row in rows:
            name = str(row.get("name") or "")
            if row.get("anchor") or name.startswith("book:"):
                continue
            root = name.split("~")[0].split("^")[0]
            score = float(row.get("corrected") or row.get("score") or 0.0)
            if score > best.get(root, (0.0, ""))[0]:
                best[root] = (score, name)
    return best


def _representatives(books: dict, ws: Path) -> dict:
    """One sentence per family: the best-scored member, else the newest (last in book order)."""
    scores = _best_scores(ws)
    chosen: dict = {}
    for index, (name, scheme) in enumerate(books.items()):
        try:
            key = _family_key(scheme, ws)
        except Exception as exc:  # noqa: BLE001 - a scheme the engine cannot key is its own fault
            print(f"corpus: cannot key {name} ({type(exc).__name__}: {exc})", file=sys.stderr)
            continue
        score, variant = scores.get(name, (0.0, ""))
        rank = (score, index)
        if key not in chosen or rank > chosen[key][0]:
            # A representative competes as one variant: the one it was judged
            # as, else its bare form. Spreading the repertoire again is what
            # made a round seventeen hours; the round's own sentences spread.
            stamped = {**scheme, "repertoire_variant": variant or name}
            chosen[key] = (rank, name, stamped)
    return {name: scheme for _rank, name, scheme in chosen.values()}


def combine(primary, feedback, destination):
    source = json.loads(Path(primary).read_text(encoding="utf-8-sig"))
    scope = os.environ.get("MASS_RUN_SCOPE", "families").strip().lower()
    ws = Path(os.environ.get("MASSV2_WS") or Path(primary).resolve().parents[1])
    rows: dict = {}
    books = 0
    families = 0
    if scope in ("families", "cumulative"):
        everything = _all_books(ws)
        books = len(everything)
        if scope == "families":
            rows = _representatives(everything, ws)
            families = len(rows)
        else:
            rows = everything
    elif scope != "round":
        raise ValueError(f"MASS_RUN_SCOPE must be families, cumulative or round, not {scope!r}")
    # This round's book overrides a same-named sentence from the repertoire:
    # the author may revise, and the revision is the one being judged.
    for r in source["schemes"]:
        rows[r["name"]] = r
    if Path(feedback).exists():
        for row in json.loads(Path(feedback).read_text(encoding="utf-8-sig"))["schemes"]:
            existing = rows.get(row["name"])
            if existing is not None:
                # The repertoire's copy may carry the judged-variant stamp; the
                # guard is against a DIFFERENT scheme under this name.
                bare = {k: v for k, v in existing.items() if k != "repertoire_variant"}
                if bare != row:
                    raise ValueError(f"champion name collides with a different authored scheme: {row['name']}")
            rows[row["name"]] = row
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**source, "schemes": list(rows.values()),
                               "development_feedback": str(feedback),
                               "run_scope": scope, "repertoire_sentences": books,
                               "repertoire_families": families,
                               "round_sentences": len(source["schemes"])},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    print(f"generation candidates: {combine(*sys.argv[1:4])} "
          f"(scope {os.environ.get('MASS_RUN_SCOPE', 'families')})")
