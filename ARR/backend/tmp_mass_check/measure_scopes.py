"""Report per-BOOK-scope survival and hierarchy for one run.

The scope gate is what target-20 kept failing after it started completing, and
the number that decides it is `dominant_component_ratio` - the largest
role-grouped plan area over the whole. Cultural's accepted band is (0.32, 0.75)
in `DOMINANT_RANGES`, so a scope whose supply averages 0.83 is one lump and
fails as a body, not as a bookkeeping error.

Reads only what the run recorded. No thresholds are typed here.
"""

import json
import sys
from pathlib import Path


def summary(run_dir):
    return json.loads(
        (Path(run_dir) / "maas-book-programs-summary.json").read_text(
            encoding="utf-8",
        ),
    )


def find(payload, key):
    if isinstance(payload, dict):
        for name, value in payload.items():
            if name == key:
                yield value
            else:
                yield from find(value, key)
    elif isinstance(payload, list):
        for value in payload[:3]:
            yield from find(value, key)


def run_state(run_dir):
    path = Path(run_dir) / "maas-run-state.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main(run_dir):
    payload = summary(run_dir)
    program = (payload.get("programs") or [{}])[0]
    stage_counts = next(find(program, "scope_stage_counts"), {}) or {}
    diagnostics = next(
        find(program, "program_gate_diagnostics_by_scope"), {}
    ) or {}
    state = run_state(run_dir)

    print(f"=== {run_dir} ===")
    print(
        f"  status={state.get('status')} "
        f"scopes={state.get('selected_scope_count')}/"
        f"{state.get('required_scope_count')} "
        f"selected={state.get('selected_mass_count')}"
    )
    header = (
        f"  {'scope':6} {'eval':>5} {'clean':>6} {'passed':>7} "
        f"{'dominant':>9} {'score':>7}  top gate failure"
    )
    print(header)
    for scope, counts in stage_counts.items():
        gate = diagnostics.get(scope) or {}
        metrics = gate.get("metric_summaries") or {}
        dominant = (metrics.get("dominant_component_ratio") or {}).get("mean")
        score = (metrics.get("dominant_ratio_score") or {}).get("mean")
        failures = gate.get("gate_failed_counts") or {}
        worst = max(failures.items(), key=lambda item: item[1], default=("", 0))
        print(
            f"  {scope:6} {counts.get('evaluated', 0):5} "
            f"{counts.get('clean', 0):6} {counts.get('program_passed', 0):7} "
            f"{dominant if dominant is not None else '-':>9} "
            f"{score if score is not None else '-':>7}  "
            f"{worst[0]}={worst[1]}" if worst[1] else ""
        )


if __name__ == "__main__":
    for target in sys.argv[1:]:
        main(target)
