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
    prompts = json.loads((out / "prompts.json").read_text(encoding="utf-8"))
    prompt = prompts.get("rubric_overseas") if track != "korea" else None
    prompt = prompt or prompts["rubric"]
    (out / "PROMPT.txt").write_text(
        "아래 타일 전부를 Read 도구로 실제로 보고 채점하십시오. key.json은 열지 마십시오.\n\n"
        + prompt, encoding="utf-8")
    # Anchors: two or three seated board entries ride along as ordinary
    # anonymous tiles. Absolute scores drift by judge session (measured
    # -0.9 to -0.007 across rounds with an unchanged rubric), so a raw 3.0
    # cut is a function of the session's mood; the anchors' known ledger
    # scores let --score convert every raw mean back onto the board's own
    # scale. v2 had this discipline and v3 had silently dropped it.
    board_path = ROOT / "runs" / "board" / "board-key.json"
    if track != "korea" and board_path.exists():
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from band_probe import corpus as _corpus  # noqa: E402
        from finalists import PNU as _PNU, rebuild as _rebuild  # noqa: E402
        from design.maas.massv2.legal import load_legal_site  # noqa: E402
        from design.maas.massv2.render import render_masses  # noqa: E402
        from design.maas.massv2.siting import open_side_direction  # noqa: E402
        seats = [row for row in json.loads(board_path.read_text(encoding="utf-8"))
                 if row["label"].startswith("O")]
        picks = [seats[0], seats[len(seats) // 2], seats[-1]] if len(seats) >= 3 else seats
        book = _corpus()
        site = load_legal_site(_PNU, building_type="제1종근린생활시설")
        buildable = site.plan_at(0.0)
        axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
        base = site.floor_height_m * max(
            1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
        key_rows = json.loads((out / "key.json").read_text(encoding="utf-8"))
        index = len(key_rows)
        for row in picks:
            family = row["name"].split("~")[0].split("^")[0]
            parti = book.get(family)
            if parti is None:
                continue
            asked = max((float(op.get("storeys") or 0)
                         for op in parti["ops"]), default=0.0)
            source = _rebuild(row["name"], book, site, buildable, axis,
                              max(base, asked * site.floor_height_m))
            if source is None:
                continue
            index += 1
            tile = f"t{index:02d}"
            render_masses(
                [(tile, source, {
                    "thesis": str(parti.get("formal_principle") or "")[:180]})],
                out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
                columns=1, tile=(900, 820), style="massing")
            key_rows.append({"tile": tile, "name": row["name"],
                             "anchor": row["score"]})
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
        for tile, value in re.findall(r"TILE\s+(t\d+)[\s\S]*?WEIGHTED\s+([0-9.]+)", text):
            if tile in per_tile:
                per_tile[tile].append(float(value))
    ranked = sorted(
        ((statistics.mean(v), t) for t, v in per_tile.items() if v), reverse=True)
    # Session drift, measured off the anchors: how much softer or harder this
    # jury was than the ledger's own scale. corrected = raw - drift, and the
    # curator already prefers `corrected` over `score`.
    deltas = [s - float(key[t]["anchor"])
              for s, t in ranked if key[t].get("anchor") is not None]
    drift = statistics.mean(deltas) if deltas else 0.0
    if deltas:
        print(f"   anchors {len(deltas)}, session drift {drift:+.2f}")
    result = [{
        "tile": t, "score": round(s, 2),
        "corrected": round(s - drift, 2),
        "pass": (s - drift) >= 3.0,
        "name": key[t]["name"], "coverage_pct": key[t].get("coverage_pct"),
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
