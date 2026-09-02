"""Bring BOOK-stack masses to the massv2 jury.

Two pipelines, one shared IR: book_language compiles its 70-principle
vocabulary into the same SourceMass that massv2's post-compile funnel
consumes. This tool replays a book run's exact geometry artifacts
(GeometryProgram AST -> SourceMass on this parcel's legal host) and
stages them as anonymous jury tiles - PROMPT.txt, tNN.png, key.json,
with three current board seats riding as anchors - exactly the stage
layout judge.sh/score.sh already speak. Book masses then face the same
blind eyes as every massv2 family, which is what "use the book" means.

    python tools/book_import.py <book-run-dir> <stage-name>
    # e.g. python tools/book_import.py ../c250-t3 book01
    # then: judge with skills/mass-judge (stage name book01)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    book_dir = Path(sys.argv[1])
    if not book_dir.is_absolute():
        book_dir = (ROOT / book_dir).resolve()
    stage_name = sys.argv[2]

    from band_probe import corpus  # noqa: E402  (django setup side effect)
    from finalists import PNU, rebuild  # noqa: E402
    from design.maas.geometry_language.ast import GeometryProgram  # noqa: E402
    from design.maas.geometry_language.source_bridge import (  # noqa: E402
        compile_geometry_program_to_source_mass,
    )
    from design.maas.massv2.legal import load_legal_site  # noqa: E402
    from design.maas.massv2.render import render_masses  # noqa: E402
    from design.maas.massv2.siting import open_side_direction  # noqa: E402

    artifacts = json.loads(
        (book_dir / "maas-book-exact-geometry-artifacts.json").read_text(encoding="utf-8"))
    records = artifacts.get("records") or []
    if not records:
        print("FAIL: no records in book artifacts")
        return 1

    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))

    out = ROOT / "runs" / f"vlm-{stage_name}"
    out.mkdir(parents=True, exist_ok=True)
    for stale in list(out.glob("t*.png")) + [out / r for r in ("r1.txt", "r2.txt", "r3.txt")]:
        Path(stale).unlink(missing_ok=True)

    key_rows: list[dict] = []
    index = 0
    for rec in records:
        art = rec.get("geometry_artifact") or {}
        payload = art.get("authoredGeometryProgram") or art.get("geometryProgram")
        if not payload:
            continue
        try:
            program = GeometryProgram.from_dict(payload)
            source = compile_geometry_program_to_source_mass(
                program, buildable, name=rec.get("trace_sequence_name"))
        except Exception as exc:  # a book record that no longer compiles is news, not a crash
            print(f"  skip {rec.get('trace_sequence_name')}: {type(exc).__name__}: {exc}")
            continue
        if source is None:
            print(f"  skip {rec.get('trace_sequence_name')}: compiled to None")
            continue
        index += 1
        tile = f"t{index:02d}"
        thesis = str(art.get("bookPrincipleId") or art.get("bookScope") or "book principle")
        render_masses([(tile, source, {"thesis": thesis[:180]})],
                      out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
                      columns=1, tile=(900, 820), style="massing")
        key_rows.append({"tile": tile,
                         "name": f"book:{rec.get('trace_sequence_name') or tile}"})

    if not key_rows:
        print("FAIL: no book record compiled")
        return 1

    # The overseas rubric, verbatim from its owner - never retyped here.
    prompts = json.loads((ROOT / "inputs" / "judge-prompts.json").read_text(encoding="utf-8"))
    (out / "prompts.json").write_text(json.dumps(prompts, ensure_ascii=False), encoding="utf-8")
    (out / "PROMPT.txt").write_text(
        "아래 타일 전부를 Read 도구로 실제로 보고 채점하십시오. key.json은 열지 마십시오.\n\n"
        + (prompts.get("rubric_overseas") or prompts["rubric"]), encoding="utf-8")

    # Three board seats ride as anchors, same as every jury session.
    board_path = ROOT / "runs" / "board" / "board-key.json"
    if board_path.exists():
        seats = [r for r in json.loads(board_path.read_text(encoding="utf-8"))
                 if r["label"].startswith("O")]
        picks = [seats[0], seats[len(seats) // 2], seats[-1]] if len(seats) >= 3 else seats
        book = corpus()
        for row in picks:
            family = row["name"].split("~")[0].split("^")[0]
            parti = book.get(family)
            if parti is None:
                continue
            asked = max((float(op.get("storeys") or 0) for op in parti["ops"]), default=0.0)
            source = rebuild(row["name"], book, site, buildable, axis,
                             max(base, asked * site.floor_height_m))
            if source is None:
                continue
            index += 1
            tile = f"t{index:02d}"
            render_masses([(tile, source,
                            {"thesis": str(parti.get("formal_principle") or "")[:180]})],
                          out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
                          columns=1, tile=(900, 820), style="massing")
            key_rows.append({"tile": tile, "name": row["name"], "anchor": row["score"]})

    (out / "key.json").write_text(json.dumps(key_rows, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    candidates = sum(1 for r in key_rows if "anchor" not in r)
    print(f"{len(key_rows)} tiles staged ({candidates} book + "
          f"{len(key_rows) - candidates} anchors) -> {out}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
