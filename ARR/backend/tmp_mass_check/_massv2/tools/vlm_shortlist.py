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
    result = [{
        "tile": t, "score": round(s, 2),
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
