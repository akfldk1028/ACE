"""Read-only evidence for the 2026-09-06 massv2 handoff review.

The real cycle script is copied unchanged into a contained harness. All of
its workers, including rm, are shell stubs; no generation, jury, or board
mutation runs. Other probes execute existing pure functions against fixtures
or existing input files. This is an audit, not a completed production cycle.
"""

import ast
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MASS = HERE.parents[1]
PROJECT = HERE.parents[5]
BACKEND = PROJECT / "ARR/backend"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cycle_probe(top):
    case = "book_top" if top.startswith("book:") else "authored_top"
    harness = (HERE / "harness" / case).resolve()
    assert harness.is_relative_to(HERE.resolve())
    source = PROJECT / "agents/MassAgent/skills/mass-cycle/scripts/cycle.sh"
    script = harness / "skills/mass-cycle/scripts/cycle.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes(source.read_bytes())
    for folder in ("config", "backend", "workspace/inputs", "workspace/runs"):
        (harness / folder).mkdir(parents=True, exist_ok=True)
    (harness / "workspace/inputs/gen-review.json").write_text("{}", encoding="utf-8")
    (harness / "trace.txt").write_text("", encoding="utf-8")
    (harness / "config/massagent.env").write_text('''ARR_BACKEND="$ROOT/backend"
MASSV2_WS="$ROOT/workspace"
PNU=review_fixture
BOOK_COUNT=40
GROUND_CAPACITY_M2=1
PY=probe_python
audit() { printf '%s\\n' "$*" >> "$ROOT/trace.txt"; }
bash() { audit bash "$@"; }
node() { audit node "$@"; }
rm() { audit stubbed_rm "$@"; }
probe_python() {
  audit python "$@"
  if [ "${1:-}" = "-c" ]; then
    printf '%s\\n' "$REVIEW_TOP"
  else
    printf '%s\\n' 'stub worker completed'
  fi
}
''', encoding="utf-8")
    result = subprocess.run(
        ["C:/Program Files/Git/bin/bash.exe", script.as_posix(), "review", "18", "--from=8"],
        cwd=harness, env={**os.environ, "REVIEW_TOP": top},
        capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    trace = (harness / "trace.txt").read_text(encoding="utf-8")
    (harness / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (harness / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return {
        "original_script_sha256": digest(source),
        "copy_identical": digest(source) == digest(script),
        "requested_from": 8,
        "brief_ran": "mass-author/scripts/brief.sh" in trace,
        "run_ran": "mass-run/scripts/run.sh" in trace,
        "restaging_ran": "mass-judge/scripts/stage.sh" in trace,
        "fixture_authoring_ran": "--author-mode recipe_fixture" in trace,
        "develop_generation_ran": "tools/develop.py review" in trace,
        "develop_score_ran": bool(re.search(r"tools/develop\.py.*--score", trace)),
        "reported_complete": "=== cycle complete ===" in result.stdout,
        "trace_path": str(harness / "trace.txt"),
    }


def picks_probe():
    path = MASS / "tools/study_sheet.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_picks")
    namespace = {"ROOT": MASS, "json": json}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 str(path), "exec"), namespace)
    book = {}
    skipped = []
    for path in sorted((MASS / "inputs").glob("gen-*.json")) + sorted((MASS / "runs/sweeps").glob("*.json")):
        try:
            for row in json.loads(path.read_text(encoding="utf-8"))["schemes"]:
                book[row["name"]] = row
        except (ValueError, KeyError, TypeError) as exc:
            skipped.append({"path": str(path), "reason": str(exc)})
    result = {run: namespace["_picks"](run, book) for run in ("agent08", "book-llm01")}
    result["skipped_books"] = skipped
    return result


def section_probe():
    path = BACKEND / "design/maas/source_geometry/ir.py"
    spec = importlib.util.spec_from_file_location("mass_review_ir", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from shapely.geometry import Point, box
    common = dict(role="roof", footprint=box(0, 0, 10, 10),
                  bottom_fraction=0, top_fraction=1, verb="roof", top_drop=1)
    results = {}
    for name, plate, sag, z in (("thin_sheet", True, 0, 5), ("sag_body", False, .4, 8)):
        volume = module.SourceVolume(**common, warp=((1, 0), (0, 1), (1, 1, 1, 1), plate, sag, .1))
        top = volume.top_z(5, 5, 0, 10)
        bottom = volume.bottom_z(5, 5, 0, 10)
        section = volume.plan_at(z, 0, 10)
        results[name] = {
            "point": [5, 5], "z": z, "top_z": top, "bottom_z": bottom,
            "within_solid": bottom <= z <= top,
            "returned_section_covers_point": bool(section is not None and section.covers(Point(5, 5))),
            "returned_section_area": section.area if section is not None else 0,
        }
    return results


def artifact_probe():
    html = (MASS / "runs/study-after/study.html").read_text(encoding="utf-8")
    images = re.findall(r'<img src="data:image/png;base64,([^\"]+)"', html)
    hashes = {hashlib.sha256(base64.b64decode(raw)).hexdigest() for raw in images}
    paths = ("runs/agent08/parti-spine_vault_arcade.png",
             "runs/study-after/1-spine_vault_arcade.png")
    board = json.loads((MASS / "runs/board/board-key.json").read_text(encoding="utf-8"))
    board = [row for row in board if row["label"].startswith("O")]
    book_scores = json.loads((MASS / "runs/vlm-book-llm01/vlm-shortlist.json").read_text(encoding="utf-8"))
    summary = json.loads((MASS / "runs/agent08/massv2-summary.json").read_text(encoding="utf-8"))
    return {
        "embedded_in_current_html": {path: digest(MASS / path) in hashes for path in paths},
        "board_O_seats": len(board),
        "board_BOOK_seats": sum(row["name"].startswith("book:") for row in board),
        "BOOK_passed": sum(bool(row.get("pass")) and not row.get("anchor") for row in book_scores),
        "agent08_provenance": summary["provenance"],
    }


def main():
    protected = [MASS / path for path in (
        "runs/board/board-key.json", "runs/board/ledger.json", "runs/board/era.json",
        "runs/board/sheet_O.png", "runs/study-after/study.html",
        "runs/agent08/parti-spine_vault_arcade.png",
        "runs/vlm-agent08/vlm-shortlist.json", "runs/vlm-book-llm01/vlm-shortlist.json",
    )]
    before = {str(path): digest(path) for path in protected}
    evidence = {
        "scope": "existing-code review; workers stubbed; no production cycle or jury executed",
        "cycle_authored_top": cycle_probe("spine_vault_arcade~dispersed_ground^to_open"),
        "cycle_book_top": cycle_probe("book:fixture:winner"),
        "sheet_picks": picks_probe(),
        "section_contract": section_probe(),
        "artifacts": artifact_probe(),
    }
    evidence["production_artifacts_unchanged"] = before == {str(path): digest(path) for path in protected}
    evidence["artifact_sha256"] = before
    target = HERE / "evidence.json"
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in evidence.items() if key != "artifact_sha256"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
