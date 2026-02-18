"""
Experiment 01: Pattern Efficiency
=================================
v2: 8 representative patterns × 25 tasks × 1 repeat = 200 runs
(v1 was: 13 patterns × 20 tasks × 3 repeats = 780 runs)

Categories: A(Chain), B1(Star), B2(Mesh), C(Feedback), D(Composed)
Measures: duration, turn_count, agent_turn_count, token usage, stop_reason
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PATTERNS_ALL, REPEAT_COUNT, RESULTS_DIR
from experiment_utils import (
    ExperimentRunner,
    load_tasks,
    save_results_csv,
    save_results_json,
)

EXPERIMENT_ID = "exp01"
OUTPUT_DIR = RESULTS_DIR / "exp01"


def _progress(done: int, total: int, pattern: str, task_id: str, repeat: int):
    pct = (done / total * 100) if total > 0 else 0
    print(f"  [{done}/{total}] ({pct:.0f}%) pattern={pattern} task={task_id} repeat={repeat}", flush=True)


async def main(patterns: list[str] | None = None, dry_run: bool = False):
    """Run exp01: pattern efficiency comparison."""
    patterns = patterns or PATTERNS_ALL
    tasks = load_tasks()
    repeats = REPEAT_COUNT

    if dry_run:
        patterns = patterns[:1]
        tasks = tasks[:1]
        repeats = 1

    total = len(patterns) * len(tasks) * repeats
    print(f"Exp01: {len(patterns)} patterns × {len(tasks)} tasks × {repeats} repeats = {total} runs")

    results = await ExperimentRunner.run_batch(
        patterns=patterns,
        tasks=tasks,
        experiment_id=EXPERIMENT_ID,
        repeats=repeats,
        progress_callback=_progress,
        checkpoint_dir=OUTPUT_DIR,
    )

    # Save results - use pattern list hash for unique filenames per batch
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "_".join(sorted(set(r.pattern_category for r in results)))
    save_results_csv(results, OUTPUT_DIR / f"summary_{suffix}.csv")
    save_results_json(results, OUTPUT_DIR / f"raw_{suffix}.json")
    # Also write/append to combined files
    save_results_csv(results, OUTPUT_DIR / "summary.csv")
    save_results_json(results, OUTPUT_DIR / "raw.json")

    # Print summary
    print(f"\nExp01 complete: {len(results)} runs")
    print(f"  Saved to: {OUTPUT_DIR}")

    errors = [r for r in results if r.error]
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"    {e.pattern}/{e.task_id}: {e.error[:100]}")

    return results
