"""
Experiment 02: Termination Quality
===================================
v2: 8 representative patterns × 25 tasks × 1 repeat (MaxMessages=25)
Each run is scored per-turn using G-Eval LLM-as-Judge.

Categories: A(Chain), B1(Star), B2(Mesh), C(Feedback), D(Composed)
Measures: quality curve Q(t), optimal_stop, overshoot, ΔU(t) marginal convergence
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PATTERNS_ALL, MAX_MESSAGES_HIGH, RESULTS_DIR
from experiment_utils import (
    ExperimentRunner,
    TeamFactory,
    load_tasks,
    save_results_csv,
    save_results_json,
)
from exp02_termination_quality.scorer import score_all_turns, TurnScore

EXPERIMENT_ID = "exp02"
OUTPUT_DIR = RESULTS_DIR / "exp02"


async def main(patterns: list[str] | None = None, dry_run: bool = False):
    """Run exp02: termination quality analysis."""
    patterns = patterns or PATTERNS_ALL
    tasks = load_tasks()
    task_map = {t["id"]: t for t in tasks}

    if dry_run:
        patterns = patterns[:1]
        tasks = tasks[:1]

    total = len(patterns) * len(tasks)
    print(f"Exp02: {len(patterns)} patterns × {len(tasks)} tasks = {total} runs (MaxMsg={MAX_MESSAGES_HIGH})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    all_scores = []
    done = 0

    for pattern in patterns:
        for task_meta in tasks:
            done += 1
            print(f"  [{done}/{total}] pattern={pattern} task={task_meta['id']}", flush=True)

            team = TeamFactory.build(pattern, max_messages=MAX_MESSAGES_HIGH)

            run_result = await ExperimentRunner.run_single(
                team=team,
                task_text=task_meta["task"],
                experiment_id=EXPERIMENT_ID,
                task_id=task_meta["id"],
                pattern=pattern,
            )

            # Score each turn
            if not run_result.error and run_result.turns:
                turn_scores = await score_all_turns(run_result, task_meta)

                for ts in turn_scores:
                    all_scores.append({
                        "pattern": pattern,
                        "pattern_category": run_result.pattern_category,
                        "task_id": task_meta["id"],
                        "task_category": task_meta["category"],
                        "turn_index": ts.turn_index,
                        "accuracy": ts.accuracy,
                        "completeness": ts.completeness,
                        "coherence": ts.coherence,
                        "usefulness": ts.usefulness,
                        "overall": ts.overall,
                    })

                # Set final quality
                if turn_scores:
                    run_result.quality_score = turn_scores[-1].overall

            all_results.append(run_result)

    # Save results
    save_results_csv(all_results, OUTPUT_DIR / "summary.csv")
    save_results_json(all_results, OUTPUT_DIR / "raw.json")

    # Save scores
    if all_scores:
        scores_path = OUTPUT_DIR / "scores.csv"
        fieldnames = list(all_scores[0].keys())
        with open(scores_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_scores)
        print(f"  Scores saved: {scores_path}")

    print(f"\nExp02 complete: {len(all_results)} runs, {len(all_scores)} turn scores")
    return all_results, all_scores
