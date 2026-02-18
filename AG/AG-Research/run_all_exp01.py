"""
Run exp01 Category-by-Category with checkpoint recovery.
Each category runs in a fresh process to pick up code fixes.

Usage:
  python run_all_exp01.py              # Run all remaining categories
  python run_all_exp01.py --category B  # Run specific category
  python run_all_exp01.py --skip A      # Skip completed categories
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    PATTERNS_FLAT, PATTERNS_CENTRALIZED, PATTERNS_DECENTRALIZED,
    PATTERNS_FEEDBACK, PATTERNS_COMPOSED,
    REPEAT_COUNT, RESULTS_DIR,
)
from experiment_utils import (
    ExperimentRunner, load_tasks,
    save_results_csv, save_results_json,
)

EXPERIMENT_ID = "exp01"
OUTPUT_DIR = RESULTS_DIR / "exp01"

CATEGORIES = {
    "A": ("Flat Sequential (Chain)", PATTERNS_FLAT),
    "B1": ("Centralized Routing (Star)", PATTERNS_CENTRALIZED),
    "B2": ("Decentralized Handoff (Mesh)", PATTERNS_DECENTRALIZED),
    "C": ("Structured Feedback", PATTERNS_FEEDBACK),
    "D": ("Composed/Nested", PATTERNS_COMPOSED),
}


def _progress(done, total, pattern, task_id, repeat):
    pct = (done / total * 100) if total > 0 else 0
    print(f"  [{done}/{total}] ({pct:.0f}%) pattern={pattern} task={task_id} repeat={repeat}", flush=True)


async def run_category(cat_id: str, dry_run: bool = False):
    """Run a single category and save results."""
    cat_name, patterns = CATEGORIES[cat_id]
    tasks = load_tasks()
    repeats = REPEAT_COUNT

    if dry_run:
        patterns = patterns[:1]
        tasks = tasks[:1]
        repeats = 1

    total = len(patterns) * len(tasks) * repeats
    print(f"\n{'='*60}")
    print(f"  Category {cat_id}: {cat_name}")
    print(f"  Patterns: {patterns}")
    print(f"  {len(patterns)} patterns x {len(tasks)} tasks x {repeats} repeats = {total} runs")
    print(f"{'='*60}\n")

    t0 = time.monotonic()

    results = await ExperimentRunner.run_batch(
        patterns=patterns,
        tasks=tasks,
        experiment_id=EXPERIMENT_ID,
        repeats=repeats,
        progress_callback=_progress,
        checkpoint_dir=OUTPUT_DIR,
    )

    elapsed = time.monotonic() - t0

    # Save category-specific results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_results_csv(results, OUTPUT_DIR / f"summary_{cat_id}.csv")
    save_results_json(results, OUTPUT_DIR / f"raw_{cat_id}.json")

    # Print summary
    errors = [r for r in results if r.error]
    print(f"\n  Category {cat_id} complete: {len(results)} runs in {elapsed:.0f}s")
    print(f"  Errors: {len(errors)}/{len(results)}")
    if errors:
        for e in errors[:5]:
            print(f"    {e.pattern}/{e.task_id}: {str(e.error)[:80]}")
    print(f"  Saved to: {OUTPUT_DIR}/summary_{cat_id}.csv")

    return results


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["A", "B1", "B2", "C", "D"])
    parser.add_argument("--skip", nargs="+", default=[], choices=["A", "B1", "B2", "C", "D"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.category:
        categories = [args.category]
    else:
        categories = ["A", "B1", "B2", "C", "D"]

    categories = [c for c in categories if c not in args.skip]

    print(f"Exp01: Running categories {categories}")
    all_results = []
    t0 = time.monotonic()

    for cat_id in categories:
        results = await run_category(cat_id, dry_run=args.dry_run)
        all_results.extend(results)

    # Merge ALL category results (including previously completed ones)
    from merge_results import merge_exp01
    merge_exp01()
    print(f"\nMerged all available category files into summary.csv / raw.json")

    elapsed = time.monotonic() - t0
    print(f"\nAll done in {elapsed:.0f}s ({elapsed/60:.1f} min)")


if __name__ == "__main__":
    asyncio.run(main())
