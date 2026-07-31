"""
Cross-Model Expansion: GPT-4o-mini on 3 additional patterns
=============================================================
Extends cross-model validation from 5 → 8 patterns.
Existing: solo, rr3, sel3, swm3, refl2 (125 runs)
New: sel4, swm4, debate3 (75 runs)

Usage:
  set OPENAI_API_KEY=sk-...
  python run_cross_model_expansion.py [--dry-run]
"""
import asyncio
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Override MODEL before importing experiment_utils
import config
config.MODEL = "gpt-4o-mini"
config.MODEL_SELECTOR = "gpt-4o-mini"

from experiment_utils import (
    ExperimentRunner,
    TeamFactory,
    load_tasks,
    save_results_csv,
    save_results_json,
)

EXPERIMENT_ID = "exp01_cross_gpt4omini"
OUTPUT_DIR = config.RESULTS_DIR / "exp01_cross_model"
NEW_PATTERNS = ["sel4", "swm4", "debate3"]


def _progress(done, total, pattern, task_id, repeat):
    print(f"  [{done+1}/{total}] pattern={pattern} task={task_id}", flush=True)


async def main(dry_run=False):
    # Verify API key
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set")
        return

    tasks = load_tasks()
    patterns = NEW_PATTERNS

    if dry_run:
        patterns = patterns[:1]
        tasks = tasks[:2]

    total = len(patterns) * len(tasks)
    print(f"Cross-Model Expansion (GPT-4o-mini)")
    print(f"  Patterns: {patterns}")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Total runs: {total}")
    print(f"  Model: {config.MODEL}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = await ExperimentRunner.run_batch(
        patterns=patterns,
        tasks=tasks,
        experiment_id=EXPERIMENT_ID,
        repeats=1,
        progress_callback=_progress,
        checkpoint_dir=OUTPUT_DIR,
    )

    save_results_csv(results, OUTPUT_DIR / "summary_expansion.csv")
    save_results_json(results, OUTPUT_DIR / "raw_expansion.json")

    # Print summary
    print(f"\nComplete: {len(results)} runs")
    errors = [r for r in results if r.error]
    if errors:
        print(f"  Errors: {len(errors)}")

    for pattern in patterns:
        p_results = [r for r in results if r.pattern == pattern and not r.error]
        if not p_results:
            continue
        import statistics
        tokens = [r.total_tokens for r in p_results]
        turns = [r.turn_count for r in p_results]
        kw_pct = sum(1 for r in p_results if r.terminated_by == 'keyword') / len(p_results) * 100

        print(f"\n  {pattern}:")
        print(f"    tokens: {statistics.mean(tokens):.0f} avg ± {statistics.stdev(tokens):.0f}")
        print(f"    turns:  {statistics.mean(turns):.1f} avg")
        print(f"    keyword: {kw_pct:.0f}%")

    return results


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(main(dry_run=dry_run))
