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

# The pass cut, once. It lived as `>= 3.0` here and as `3.5 - 0.5` in the
# curator's KOREA_FINAL_PASS - two literals that happened to agree.
PASS_CUT = 3.0


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


# A tile is now the mass over its own operation sequence, so the rubric has to
# say what the strip is - a juror shown an unexplained band of small drawings
# reads it as clutter and marks the scheme down for it.
BLIND_PREAMBLE = (
    "아래 타일 전부를 Read 도구로 실제로 보고 채점하십시오. key.json은 열지 마십시오.\n"
    "타일 위쪽은 배달된 매스(백색 모형 액소노메트릭 + 배치도)입니다. 아래에 띠가 있으면 "
    "그 매스가 만들어진 조작 순서입니다 - 문장의 단어 하나가 프레임 하나이고, 마지막 "
    "프레임이 법규 한도까지 자란 결과입니다. 띠는 논지의 증거이지 별개의 안이 아닙니다. "
    "띠가 없는 타일은 순서 기록이 없는 안이며, 그것만으로 감점하지 마십시오.\n\n"
)


def certified_caption(source, site, thesis: str, *,
                      ground_m2: float | None = None,
                      gross_m2: float | None = None,
                      storey_m: float | None = None) -> dict:
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
    # At the SCHEME's own storey height, which is the height the legal gate
    # counted floors at. Measured at the parcel's default instead, a mass
    # built on 3.4 m storeys was counted in 3.0 m floors and gained 13% of
    # floor area: `cascade_ramp_tower` passed the gate at 97% of the 용적률
    # capacity and was captioned 265% on a 250% parcel - a sheet that claims
    # legality while printing a number over the cap.
    gross = (float(gross_m2) if gross_m2 is not None
             else gross_floor_area_m2(
                 source,
                 floor_height_m=float(storey_m or site.floor_height_m)))
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
    storey = float(parti.get("floor_height_m") or site.floor_height_m)
    source = _rebuild(name, book, site, buildable, axis,
                      max(base, declared_height_m(parti, site.floor_height_m)))
    if source is None:
        return None, None
    return source, certified_caption(source, site, parti.get("formal_principle") or "",
                                     storey_m=storey)


def shape_id(source) -> str:
    """The identity of what the renderer draws, as a short hash.

    A score belongs to a picture. When the engine changes, a seat's picture
    can change while its name and its ledger score do not, and an anchor
    whose picture changed is not an anchor: three anchors carried deltas
    spread 1.32 apart because the top seat had been redrawn under a
    regulating snap, the ruler refused to move, and a whole round was
    recorded raw - unchanged pictures fell 0.4 to 1.0 with no contest.

    Geometry, not pixels: the tile label and caption are outside it, and so
    is the renderer's own code. Every field the renderer reads is inside.
    """

    import hashlib
    rows = []
    for v in source.volumes:
        fp = v.footprint
        ring = () if fp is None or fp.is_empty else tuple(
            (round(x, 3), round(y, 3)) for x, y in fp.exterior.coords)
        rows.append((
            ring, round(float(v.bottom_fraction), 4), round(float(v.top_fraction), 4),
            getattr(v, "role", ""), getattr(v, "verb", ""),
            round(float(getattr(v, "top_drop", 0.0) or 0.0), 4),
            getattr(v, "drop_toward", None), getattr(v, "ridge_along", None),
            getattr(v, "top_profile", None), getattr(v, "profile_across", None),
            getattr(v, "profile_span", None), bool(getattr(v, "top_walkable", False)),
            getattr(v, "warp", None),
        ))
    meta = source.metadata or {}
    rows.sort(key=repr)
    text = repr((rows, round(float(meta.get("authored_height_m") or 0.0), 3),
                 round(float(meta.get("datum_m") or 0.0), 3),
                 tuple(sorted(meta.get("structural_bands") or ()))))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def seat_context(site=None):
    """Everything a seat needs to be rebuilt: (book, site, buildable, axis, base)."""

    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from band_probe import corpus as _corpus  # noqa: E402
    from finalists import PNU as _PNU, BUILDING_TYPE  # noqa: E402
    from design.maas.massv2.legal import load_legal_site  # noqa: E402
    from design.maas.massv2.siting import open_side_direction  # noqa: E402
    book = _corpus()
    if site is None:
        site = load_legal_site(_PNU, building_type=BUILDING_TYPE)
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    return book, site, buildable, axis, base


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
    from finalists import PNU as _PNU, BUILDING_TYPE  # noqa: E402
    from design.maas.massv2.legal import load_legal_site  # noqa: E402
    from design.maas.massv2.render import render_masses  # noqa: E402
    from design.maas.massv2.siting import open_side_direction  # noqa: E402
    seats = [row for row in json.loads(board_path.read_text(encoding="utf-8"))
             if row["label"].startswith("O")]
    # Top, middle and bottom of the board first, so the anchors span the
    # scale; then the rest, for when one of those cannot serve. Three
    # anchors is the ride; fewer is a weaker ruler, and it says so.
    order = []
    if seats:
        first = list(dict.fromkeys([0, len(seats) // 2, len(seats) - 1]))
        order = [seats[i] for i in first]
        order += [row for i, row in enumerate(seats) if i not in first]
    book, site, buildable, axis, base = seat_context(site)
    index = len(key_rows)
    added = 0
    # A contestant cannot be its own ruler: the round's own seats are not
    # anchors for that round (the vault arcade rode as tile t12 and stood
    # as contest tile t01 in one stage), and neither is any seat whose
    # score came from the round being re-judged.
    contestants = {str(r.get("name")) for r in key_rows}
    for row in order:
        if added >= 3:
            break
        if row["name"] in contestants or str(row.get("round") or "") == out.name:
            continue
        source, caption = rebuild_seat(row["name"], book, site, buildable, axis, base)
        if source is None:
            print(f"   WARNING: anchor {row['name']} could not be rebuilt - riding without it")
            continue
        # A score belongs to a picture. A seat whose current drawing is not
        # the one its score was given to cannot calibrate anything.
        known = row.get("shape_id")
        current = shape_id(source)
        if not known:
            print(f"   anchor {row['name'][:48]}: no recorded picture identity - not riding it")
            continue
        if known != current:
            print(f"   anchor {row['name'][:48]}: picture changed since it was scored - not riding it")
            continue
        index += 1
        tile = f"t{index:02d}"
        render_masses(
            [(tile, source, caption)],
            out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
            columns=1, tile=(900, 820), style="massing")
        key_rows.append({"tile": tile, "name": row["name"], "anchor": row["score"],
                         "shape_id": current})
        added += 1
    if added < 3:
        print(f"   WARNING: only {added} anchor(s) rode - the session ruler is weaker")
    return added


def _with_sequence(tile_png: Path, run: str, name: str) -> None:
    """Paste the scheme's operation sequence under its axonometric, in place.

    The sequence sheet is wide and short; the tile is tall. Scaled to the
    tile's width and joined below it, the juror reads the moves that made the
    mass in the same glance as the mass - which is the pairing every massing
    convention in the literature publishes and the one this pipeline drew and
    then threw away.
    """

    from PIL import Image  # noqa: E402  (Pillow is already a render dependency)

    strip_path = ROOT / "runs" / run / f"parti-{name}.png"
    if not strip_path.exists() or not tile_png.exists():
        return
    tile = Image.open(tile_png).convert("RGB")
    strip = Image.open(strip_path).convert("RGB")
    width = tile.width
    height = max(1, round(strip.height * width / strip.width))
    # A strip taller than the mass would make the tile a sequence sheet with a
    # picture on top; half the tile is the most the argument may take.
    if height > tile.height // 2:
        scale = (tile.height // 2) / height
        height = max(1, int(height * scale))
    strip = strip.resize((width, height), Image.LANCZOS)
    joined = Image.new("RGB", (width, tile.height + height), (255, 255, 255))
    joined.paste(tile, (0, 0))
    joined.paste(strip, (0, tile.height))
    joined.save(tile_png)


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
    key_rows = json.loads((out / "key.json").read_text(encoding="utf-8"))
    # Every contest tile records the identity of the picture it was judged
    # as, so it can serve as an anchor later only while that picture holds.
    book, site, buildable, axis, base = seat_context()
    for row in key_rows:
        if row.get("anchor") is not None or row.get("shape_id"):
            continue
        source, _caption = rebuild_seat(row["name"], book, site, buildable, axis, base)
        if source is not None:
            row["shape_id"] = shape_id(source)
    if track != "korea":
        ride_anchors(out, key_rows, site=site)
    (out / "key.json").write_text(
        json.dumps(key_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    # The argument under the outcome, for every contest tile that has one.
    for row in json.loads((out / "key.json").read_text(encoding="utf-8")):
        if row.get("anchor") is not None:
            continue
        family = str(row["name"]).split("~")[0].split("^")[0]
        _with_sequence(out / f"{row['tile']}.png", run, family)
    tiles = sorted(p.name for p in out.glob("t*.png"))
    print(f"{len(tiles)} tiles staged -> {out}")
    print(f"judges read: {out / 'PROMPT.txt'} + the tiles; "
          f"then rerun with --score <their outputs>")
    return 0


# A tile block opens on its own line - every juror file ever written puts
# TILE at the start of a line, with or without the `t` and with or without
# the leading zero ("TILE 7" and "TILE t07" both appear in the ledger).
_TILE_OPENS = re.compile(r"^\s*TILE\s+t?0*(\d+)\b")
_WEIGHTED = re.compile(r"WEIGHTED\s+(\S+)")


class VerdictError(ValueError):
    """A juror's file cannot be read tile by tile, so the round does not score.

    Numbers that are not bound to the tile the juror was looking at are
    worse than no numbers: they seat the wrong mass on the board, and
    nothing downstream - not the curator, not the ledger, not an eye check
    on the sheet - can tell a mis-bound score from an honest one.
    """


def read_verdict(path: Path, key_tiles) -> dict[str, float]:
    """One juror's file as {tile: weighted score}, read block by block.

    A TILE line opens a block and the next TILE line closes it, so the
    WEIGHTED a tile gets is the one the juror wrote underneath it. The
    reading this replaces was a single non-greedy regex over the whole file
    (`TILE ... WEIGHTED`), which let a juror who wrote a TILE block and
    omitted its WEIGHTED line take the NEXT tile's number: two tiles shared
    one score, one tile's score belonged to another drawing, and the round
    published both without a word. judge.sh cannot catch it either - it
    counts `^TILE` lines, and in that failure the count is right and only
    the binding is wrong.

    So this refuses instead of skipping, on every way the binding can go
    wrong: a block with no WEIGHTED, a WEIGHTED that is not a score in
    1..5, and a tile the round's key.json does not contain. A tile stated
    twice with the same number is a juror restating its own table
    (ovs17-en r3 wrote a seven-row summary under its seven blocks) and the
    last statement stands, as it always did; a tile stated twice with two
    different numbers is a contradiction no reader can resolve, so that
    refuses too.
    """

    name = Path(path).name
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    opens = [i for i, line in enumerate(lines) if _TILE_OPENS.match(line)]
    seen: dict[str, float] = {}
    for n, start in enumerate(opens):
        end = opens[n + 1] if n + 1 < len(opens) else len(lines)
        tile = f"t{int(_TILE_OPENS.match(lines[start]).group(1)):02d}"
        if tile not in key_tiles:
            raise VerdictError(
                f"{name}: scores {tile}, which this round has no tile for - "
                "the juror was reading a different stage")
        found = next((m for m in (_WEIGHTED.search(line) for line in
                                  lines[start:end]) if m), None)
        if found is None:
            raise VerdictError(
                f"{name}: TILE {tile} has no WEIGHTED line in its block - "
                "refusing to score the round rather than lend it the next "
                "tile's number")
        raw = found.group(1)
        try:
            value = float(raw)
        except ValueError:
            raise VerdictError(
                f"{name}: TILE {tile} has WEIGHTED {raw!r}, which is not a "
                "number") from None
        if not 1.0 <= value <= 5.0:
            raise VerdictError(
                f"{name}: TILE {tile} has WEIGHTED {value}, outside the "
                "rubric's 1..5 - a stray number read as a score moves the "
                "session drift for every other tile")
        if tile in seen and seen[tile] != value:
            raise VerdictError(
                f"{name}: TILE {tile} is scored twice and the two disagree "
                f"({seen[tile]} then {value}) - no reader can say which the "
                "juror meant")
        seen[tile] = value
    return seen


def score(run: str, paths: list[str]) -> int:
    out = ROOT / "runs" / f"vlm-{run}"
    key = {r["tile"]: r for r in json.loads((out / "key.json").read_text(encoding="utf-8"))}
    per_tile: dict[str, list[float]] = {t: [] for t in key}
    for path in paths:
        seen = read_verdict(Path(path), key)
        missing = [t for t in key if t not in seen]
        if missing:
            print(f"   WARNING: {Path(path).name} scored no line for "
                  f"{', '.join(missing)}")
        for tile, value in seen.items():
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
        "pass": (s - drift) >= PASS_CUT,
        "correction": correction,
        **({"anchor_spread": round(spread, 2)} if spread > 1.0 else {}),
        "name": key[t]["name"], "coverage_pct": key[t].get("coverage_pct"),
        **({"shape_id": key[t]["shape_id"]} if key[t].get("shape_id") else {}),
        # Anchors calibrate the session; they are not contestants. Without
        # this flag the curator re-recorded each anchor's ride-corrected
        # score as its current score, and the ruler measured itself: anchor
        # spread compressed 23-48% per ride and a seat gained +0.21 over two
        # rides with no contest. The flag lets the curator skip them.
        **({"anchor": True} if key[t].get("anchor") is not None else {}),
    } for s, t in ranked]
    (out / "vlm-shortlist.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    # The round's manifest: what the curator needs to seat it, written by
    # the tool that scored it. ROUNDS was a hand-edited list in
    # board_curate.py - a scored round nobody typed in was invisible to the
    # board, and "forgotten" looked exactly like "excluded".
    summary_path = ROOT / "runs" / run / "massv2-summary.json"
    track = "O"
    if summary_path.exists():
        provenance = (json.loads(summary_path.read_text(encoding="utf-8"))
                      .get("provenance") or {})
        track = "K" if provenance.get("track") == "korea" else "O"
    (out / "round.json").write_text(json.dumps({
        "track": track,
        "kind": "corrected" if run.startswith("board-rejudge") else "shortlist",
        "cut": PASS_CUT, "correction": correction,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    for row in result:
        print(f"   {row['score']:.2f}  {row['name'][:56]}")
    print(f"-> {out / 'vlm-shortlist.json'}")
    return 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        # One juror file against the round's key: the same reading --score
        # does, so a file the scorer would refuse is refused at the jury
        # step, where the juror can be run again, instead of at the end of
        # the cycle. judge.sh counted `^TILE` lines and passed files whose
        # scores were not bound to their tiles.
        i = sys.argv.index("--verify")
        out = ROOT / "runs" / f"vlm-{sys.argv[1]}"
        key_tiles = {r["tile"] for r in json.loads((out / "key.json").read_text(encoding="utf-8"))}
        try:
            verdict = read_verdict(Path(sys.argv[i + 1]), key_tiles)
        except VerdictError as exc:
            print(f"REFUSED: {exc}")
            sys.exit(1)
        missing = sorted(key_tiles - set(verdict))
        if missing:
            print(f"REFUSED: no score for {', '.join(missing)}")
            sys.exit(1)
        print(f"ok: {len(verdict)} tiles bound to scores")
        sys.exit(0)
    if "--score" in sys.argv:
        i = sys.argv.index("--score")
        sys.exit(score(sys.argv[1], sys.argv[i + 1:]))
    sys.exit(stage(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 12))
