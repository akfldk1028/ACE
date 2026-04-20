"""
Experiment 07: Difficulty x Pattern Interaction
================================================
Direction A — 15 tasks (5 domains x 3 difficulties) x 5 patterns x 3 repeats
= 225 runs + G-Eval scoring.

Patterns: solo, swm3, refl2, sel3, debate3 (one representative per category)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env BEFORE any other imports that need API keys
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)

from config import PATTERNS_DIFFICULTY_STUDY, RESULTS_DIR
from experiment_utils import (
    ExperimentRunner,
    TeamFactory,
    load_tasks,
    save_results_csv,
    save_results_json,
)

EXPERIMENT_ID = "exp07"
OUTPUT_DIR = RESULTS_DIR / "exp07"
REPEATS = 3


def load_difficulty_tasks() -> list[dict]:
    """Load difficulty-graded task suite."""
    path = Path(__file__).resolve().parent.parent / "task_suite_difficulty.json"
    return load_tasks(path)


async def main(patterns: list[str] | None = None, dry_run: bool = False, repeats_override: int | None = None):
    """Run exp07: difficulty x pattern interaction study."""
    patterns = patterns or PATTERNS_DIFFICULTY_STUDY
    tasks = load_difficulty_tasks()
    repeats = repeats_override or REPEATS

    if dry_run:
        patterns = patterns[:2]
        tasks = tasks[:3]
        repeats = 1

    total = len(patterns) * len(tasks) * repeats
    print(f"Exp07: Difficulty x Pattern Interaction")
    print(f"  Patterns: {patterns}")
    print(f"  Tasks: {len(tasks)} (5 domains x 3 difficulties)")
    print(f"  Repeats: {repeats}")
    print(f"  Total runs: {total}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def progress(done, total, pattern, task_id, rep):
        print(f"  [{done+1}/{total}] pattern={pattern} task={task_id} rep={rep}", flush=True)

    results = await ExperimentRunner.run_batch(
        patterns=patterns,
        tasks=tasks,
        experiment_id=EXPERIMENT_ID,
        repeats=repeats,
        progress_callback=progress,
        checkpoint_dir=OUTPUT_DIR,
    )

    # Save results
    save_results_csv(results, OUTPUT_DIR / "summary.csv")
    save_results_json(results, OUTPUT_DIR / "raw.json")

    errors = [r for r in results if r.error]
    print(f"\nExp07 complete: {len(results)} runs, {len(errors)} errors")
    print(f"  Saved to: {OUTPUT_DIR}")

    return results


async def score_results():
    """Score exp07 results using G-Eval (final output only)."""
    from exp02_termination_quality.scorer import score_single_turn, _is_handoff_turn

    raw_path = OUTPUT_DIR / "raw.json"
    if not raw_path.exists():
        print("No raw.json found. Run experiments first.")
        return

    with open(raw_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    tasks = load_difficulty_tasks()
    task_map = {t["id"]: t for t in tasks}

    scores_all = []
    for i, run_dict in enumerate(raw_data):
        task_id = run_dict["task_id"]
        if task_id not in task_map:
            continue
        if run_dict.get("error"):
            continue

        # Build cumulative text from all substantive turns
        cumulative = ""
        for turn in run_dict.get("turns", []):
            if turn.get("source") == "user":
                continue
            content = str(turn.get("content", ""))
            if _is_handoff_turn(content) or len(content.strip()) < 20:
                continue
            cumulative += f"\n[{turn.get('source', '?')}]: {content}\n"

        if not cumulative.strip():
            continue

        print(f"  [{i+1}/{len(raw_data)}] Scoring {task_id} / {run_dict['pattern']}...", flush=True)
        score = await score_single_turn(
            task_text=task_map[task_id]["task"],
            rubric=task_map[task_id].get("eval_rubric", "General quality"),
            cumulative_text=cumulative,
            turn_index=999,
        )

        scores_all.append({
            "task_id": task_id,
            "pattern": run_dict["pattern"],
            "repeat_index": run_dict.get("repeat_index", 0),
            "accuracy": score.accuracy,
            "completeness": score.completeness,
            "coherence": score.coherence,
            "usefulness": score.usefulness,
            "overall": score.overall,
            "total_tokens": run_dict.get("total_tokens", 0),
            "duration_sec": run_dict.get("duration_sec", 0),
        })

    import pandas as pd
    scores_df = pd.DataFrame(scores_all)
    scores_df.to_csv(OUTPUT_DIR / "scores.csv", index=False)
    print(f"\nScoring complete: {len(scores_all)} scored runs -> {OUTPUT_DIR / 'scores.csv'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Exp07: Difficulty x Pattern")
    parser.add_argument("--dry-run", action="store_true", help="Quick test with fewer runs")
    parser.add_argument("--score", action="store_true", help="Score existing results")
    parser.add_argument("--model", type=str, default=None,
                        help="Override base model (e.g., gpt-4o-mini, grok-3-mini-fast, gemini-2.0-flash)")
    parser.add_argument("--repeats", type=int, default=None, help="Override repeat count")
    args = parser.parse_args()

    # Override config.MODEL if --model is specified
    if args.model:
        import config
        config.MODEL = args.model
        config.MODEL_SELECTOR = args.model  # SelectorGroupChat also uses this
        # Use model-specific output dir
        model_tag = args.model.replace("-", "_").replace(".", "_")
        OUTPUT_DIR = RESULTS_DIR / f"exp07_{model_tag}"
        print(f"[MODEL OVERRIDE] Using {args.model}, output → {OUTPUT_DIR}")

    if args.score:
        asyncio.run(score_results())
    else:
        asyncio.run(main(dry_run=args.dry_run, repeats_override=args.repeats))
