"""The VLM judging stage, wired to a run instead of run beside it.

Every part of this existed and none of it was in the delivery path. The run
selects with numeric leximin (`select.choose`), and the judges - who found the
entry masses nine of ten blind, and failed `sg_interlace` while the selector
kept picking it - only ever existed when a session spawned them by hand.

This closes that gap as a stage: it takes a finished run, renders the
selector's chosen masses as anonymous tiles under the stored rubric
(`inputs/judge-prompts.json` - fixed, never edited between rounds), and emits
the judging prompt plus a scoring template. The judges themselves are
subagents; the session runs them and writes their RANKING lines back with
`--score`, and this tool then writes `vlm-shortlist.json` naming the masses
the judges kept.

    python tools/vlm_shortlist.py <run> [count]          # stage tiles + prompt
    python tools/vlm_shortlist.py <run> --score r1.txt r2.txt [r3.txt]

The result is the sheet order for the final drawing: gates decide what may
stand, cells decide what is comparable, judges decide what is shown.
"""

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rubric_for(track: str) -> str:
    """The ruler for a track, from its owner file - never retyped.

    Korea: inputs/judge-prompts.json["rubric"] (a 주민센터 with a fixed
    소요면적표). Overseas: inputs/judge-prompts-overseas.json["rubric"] - the
    international panel, CONCEPT 0.35 / FEASIBILITY 0.25 / SITE 0.20 /
    EDITABILITY 0.20, where a cantilever costs only where it is
    implausible. From 09-01 to 09-02 every overseas round read a
    "rubric_overseas" that was the Korean rubric with the schedule removed
    (Aesthetics 0.15, Feasibility 0.35, Compliance 0.25) - a buildability
    ruler that dropped the twisting tower and seated the boxes; the real
    international rubric had no reader. One owner, read by every stage.
    """

    if track == "korea":
        return json.loads((ROOT / "inputs" / "judge-prompts.json")
                          .read_text(encoding="utf-8"))["rubric"]
    return json.loads((ROOT / "inputs" / "judge-prompts-overseas.json")
                      .read_text(encoding="utf-8"))["rubric"]


BLIND_PREAMBLE = "아래 타일 전부를 Read 도구로 실제로 보고 채점하십시오. key.json은 열지 마십시오.\n\n"


def certified_caption(source, site, thesis: str, *,
                      ground_m2: float | None = None,
                      gross_m2: float | None = None) -> dict:
    """The caption every jury tile carries, contest, anchor or book alike.

    Anchors once carried the thesis alone while contestants carried
    건폐율/용적률 - the ruler could be picked out of the line-up. 건폐율 is
    the building's projection as the law counts it (every volume's
    footprint united), not `source.footprint`, which keeps the largest
    grounded piece and printed 5% under a pilotis ring at full coverage.
    """

    from shapely.ops import unary_union
    from design.maas.massv2.measure import gross_floor_area_m2  # noqa: E402
    # A caller with its own certificate (the book stamps 연면적 at its own
    # storey height and floor count) passes it; massv2 masses are measured
    # here at the parcel's storey, the same ruler the legal fit uses.
    ground = (float(ground_m2) if ground_m2 is not None
              else float(unary_union([v.footprint for v in source.volumes]).area))
    gross = (float(gross_m2) if gross_m2 is not None
             else gross_floor_area_m2(source, floor_height_m=site.floor_height_m))
    parcel = float(site.parcel_area_m2)
    return {"thesis": str(thesis or "")[:180],
            "건폐율": f"{ground / parcel * 100:.0f}%",
            "용적률": f"{gross / parcel * 100:.0f}%"}


def rebuild_seat(name: str, book: dict, site, buildable, axis, base):
    """A board seat's delivered geometry and its caption, whatever its stack.

    massv2 names rebuild through finalists.rebuild at the declaration's own
    budget; `book:` names rebuild through book_import at the book's own
    size and height, captioned from the book's certificate. One owner for
    every tool that re-stages seats (anchor rides, full-ledger rejudges) -
    a book seat picked as an anchor was silently skipped and the ruler
    shrank to two anchors with no warning. Returns (source, caption) or
    (None, None).
    """

    if name.startswith("book:"):
        from book_import import book_rebuild, registry  # noqa: E402
        entry = registry().get(name) or {}
        source = book_rebuild(name, site, buildable)
        if source is None:
            return None, None
        return source, certified_caption(
            source, site, entry.get("thesis", ""),
            ground_m2=entry.get("footprint_m2") or None,
            gross_m2=entry.get("floor_area_m2") or None)
    from finalists import rebuild as _rebuild  # noqa: E402
    from design.maas.massv2.grammar import declared_height_m  # noqa: E402
    family = name.split("~")[0].split("^")[0]
    parti = book.get(family)
    if parti is None:
        return None, None
    source = _rebuild(name, book, site, buildable, axis,
                      max(base, declared_height_m(parti, site.floor_height_m)))
    if source is None:
        return None, None
    return source, certified_caption(source, site, parti.get("formal_principle") or "")


def ride_anchors(out: Path, key_rows: list, *, site=None) -> int:
    """Seat up to three current board entries among the tiles, anonymously.

    Absolute scores drift by judge session (measured -0.9 to -0.007 across
    rounds with an unchanged rubric), so a raw 3.0 cut is a function of the
    session's mood; the anchors' known ledger scores let --score convert
    every raw mean back onto the board's own scale. One owner for every
    stage that rides anchors (massv2 rounds, book imports): same picks,
    same rebuild, same caption. Appends to `key_rows`; returns how many.
    """

    board_path = ROOT / "runs" / "board" / "board-key.json"
    if not board_path.exists():
        return 0
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from band_probe import corpus as _corpus  # noqa: E402
    from finalists import PNU as _PNU  # noqa: E402
    from design.maas.massv2.legal import load_legal_site  # noqa: E402
    from design.maas.massv2.render import render_masses  # noqa: E402
    from design.maas.massv2.siting import open_side_direction  # noqa: E402
    seats = [row for row in json.loads(board_path.read_text(encoding="utf-8"))
             if row["label"].startswith("O")]
    picks = [seats[0], seats[len(seats) // 2], seats[-1]] if len(seats) >= 3 else seats
    book = _corpus()
    if site is None:
        site = load_legal_site(_PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    index = len(key_rows)
    added = 0
    for row in picks:
        source, caption = rebuild_seat(row["name"], book, site, buildable, axis, base)
        if source is None:
            print(f"   WARNING: anchor {row['name']} could not be rebuilt - riding without it")
            continue
        index += 1
        tile = f"t{index:02d}"
        render_masses(
            [(tile, source, caption)],
            out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
            columns=1, tile=(900, 820), style="massing")
        key_rows.append({"tile": tile, "name": row["name"], "anchor": row["score"]})
        added += 1
    return added


def stage(run: str, count: int) -> int:
    from judge_tiles import main as make_tiles  # noqa: E402  (django inside)

    out_name = f"vlm-{run}"
    make_tiles(run, str(count), out_name)
    out = ROOT / "runs" / out_name
    # The rubric matches the track: overseas rounds were being judged against
    # the Korean 과업 and every verdict said 규모 과대 about a track that has
    # no brief. Korea keeps "rubric"; overseas rounds use "rubric_overseas".
    track = (json.loads((ROOT / "runs" / run / "massv2-summary.json")
                        .read_text(encoding="utf-8"))
             .get("provenance") or {}).get("track")
    (out / "PROMPT.txt").write_text(BLIND_PREAMBLE + rubric_for(track or "overseas"),
                                    encoding="utf-8")
    # Anchors: two or three seated board entries ride along as ordinary
    # anonymous tiles. Absolute scores drift by judge session (measured
    # -0.9 to -0.007 across rounds with an unchanged rubric), so a raw 3.0
    # cut is a function of the session's mood; the anchors' known ledger
    # scores let --score convert every raw mean back onto the board's own
    # scale. v2 had this discipline and v3 had silently dropped it.
    if track != "korea":
        key_rows = json.loads((out / "key.json").read_text(encoding="utf-8"))
        ride_anchors(out, key_rows)
        (out / "key.json").write_text(
            json.dumps(key_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    tiles = sorted(p.name for p in out.glob("t*.png"))
    print(f"{len(tiles)} tiles staged -> {out}")
    print(f"judges read: {out / 'PROMPT.txt'} + the tiles; "
          f"then rerun with --score <their outputs>")
    return 0


def score(run: str, paths: list[str]) -> int:
    out = ROOT / "runs" / f"vlm-{run}"
    key = {r["tile"]: r for r in json.loads((out / "key.json").read_text(encoding="utf-8"))}
    per_tile: dict[str, list[float]] = {t: [] for t in key}
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        # One reading per juror per tile. A juror that re-lists its scores
        # in a summary block was counted twice (ovs17-en r3: 14 TILE lines
        # for 7 tiles) and outweighed the other two; the last statement of
        # a tile is the juror's verdict.
        seen: dict[str, float] = {}
        for tile, value in re.findall(
                r"TILE\s+t?0*(\d+)[\s\S]*?WEIGHTED\s+([0-9.]+)", text):
            seen[f"t{int(tile):02d}"] = float(value)
        missing = [t for t in key if t not in seen]
        if missing:
            print(f"   WARNING: {Path(path).name} scored no line for "
                  f"{', '.join(missing)}")
        for tile, value in seen.items():
            if tile in per_tile:
                per_tile[tile].append(value)
    unscored = [t for t, v in per_tile.items() if not v]
    if unscored:
        print(f"   WARNING: no juror scored {', '.join(unscored)} - "
              "dropped from the shortlist")
    ranked = sorted(
        ((statistics.mean(v), t) for t, v in per_tile.items() if v), reverse=True)
    # Session drift, measured off the anchors: how much softer or harder this
    # jury was than the ledger's own scale. corrected = raw - drift, and the
    # curator already prefers `corrected` over `score`.
    deltas = [s - float(key[t]["anchor"])
              for s, t in ranked if key[t].get("anchor") is not None]
    # Median, not mean: one wild anchor (a jury that simply dislikes one
    # seated scheme) must not drag every candidate's correction with it -
    # the mean once pushed a candidate to 5.04 on a 5-point scale.
    drift = statistics.median(deltas) if deltas else 0.0
    spread = (max(deltas) - min(deltas)) if deltas else 0.0
    # How the `corrected` column was made, on every row: a round with no
    # anchors and a round whose anchors disagreed both wrote raw scores
    # under the same key as a corrected round, and the curator read them
    # on one scale.
    correction = "median_drift" if deltas else "none_no_anchors"
    if deltas:
        print(f"   anchors {len(deltas)}, session drift {drift:+.2f} (median), "
              f"delta spread {spread:.2f}")
    if spread > 1.0:
        # No constant shift fits this jury. Applying one anyway once crowned a
        # candidate at 5.04/5 over a champion the jury simply disliked. When
        # the anchors cannot agree, do not shift: record raw (a harsh jury
        # underrates everyone equally - conservative for seating) and flag the
        # round so the curator and the next reader know the ruler slipped.
        print("   WARNING: anchors disagree beyond any constant shift "
              f"(spread {spread:.2f}) - recording RAW scores, no correction; "
              "an eye check should confirm any board-top change.")
        drift = 0.0
        correction = "none_anchor_spread"
    result = [{
        "tile": t, "score": round(s, 2),
        "corrected": round(min(5.0, max(1.0, s - drift)), 2),
        "pass": (s - drift) >= 3.0,
        "correction": correction,
        **({"anchor_spread": round(spread, 2)} if spread > 1.0 else {}),
        "name": key[t]["name"], "coverage_pct": key[t].get("coverage_pct"),
        # Anchors calibrate the session; they are not contestants. Without
        # this flag the curator re-recorded each anchor's ride-corrected
        # score as its current score, and the ruler measured itself: anchor
        # spread compressed 23-48% per ride and a seat gained +0.21 over two
        # rides with no contest. The flag lets the curator skip them.
        **({"anchor": True} if key[t].get("anchor") is not None else {}),
    } for s, t in ranked]
    (out / "vlm-shortlist.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    for row in result:
        print(f"   {row['score']:.2f}  {row['name'][:56]}")
    print(f"-> {out / 'vlm-shortlist.json'}")
    return 0


if __name__ == "__main__":
    if "--score" in sys.argv:
        i = sys.argv.index("--score")
        sys.exit(score(sys.argv[1], sys.argv[i + 1:]))
    sys.exit(stage(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 12))
