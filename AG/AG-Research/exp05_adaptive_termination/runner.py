"""
Experiment 05: Adaptive Termination
====================================
v2: 8 representative patterns × 5 λ values × 25 tasks × 2 conditions
= 200 baseline + 1000 adaptive = 1200 runs

Compares adaptive termination using marginal utility ΔU(t) = ΔQ(t) - λΔC(t) → 0
vs baseline (keyword/MaxMsg). Optimal stopping: dQ/dt = λ·dC/dt.
Checkpoint saves after each pattern (baseline) or each λ×pattern block (adaptive).
"""

import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autogen_agentchat.conditions import (
    FunctionalTermination,
    MaxMessageTermination,
    TextMentionTermination,
)
from autogen_agentchat.base import OrTerminationCondition

from config import (
    LAMBDA_VALUES,
    PATTERNS_ALL,
    PATTERNS_REPRESENTATIVE,
    PATTERN_MAX_MESSAGES,
    RESULTS_DIR,
)
from dataclasses import asdict
from experiment_utils import (
    ExperimentRunner,
    RunResult,
    TeamFactory,
    load_tasks,
    save_results_csv,
    save_results_json,
)
from exp05_adaptive_termination.adaptive_condition import AdaptiveTerminationState

EXPERIMENT_ID = "exp05"
OUTPUT_DIR = RESULTS_DIR / "exp05"
CHECKPOINT_PATH = OUTPUT_DIR / "checkpoint.json"


def _build_adaptive_team(pattern: str, lambda_val: float, max_messages: int = 20):
    """Build a team with adaptive termination condition."""
    team = TeamFactory.build(pattern, max_messages=max_messages)

    state = AdaptiveTerminationState(
        lambda_cost=lambda_val,
        patience=2,
        min_turns=2,
    )

    adaptive_term = FunctionalTermination(state.should_terminate)
    safety_term = MaxMessageTermination(max_messages=max_messages)
    combined = OrTerminationCondition(adaptive_term, safety_term)

    if hasattr(team, '_is_composed'):
        return team, state

    team._termination_condition = combined
    return team, state


# Pattern-specific keywords used by TeamFactory
_PATTERN_KEYWORDS = {
    "solo": ["TERMINATE"],
    "rr2": ["TERMINATE"], "rr3": ["TERMINATE"], "rr4": ["TERMINATE"],
    "sel3": ["TERMINATE"], "sel4": ["TERMINATE"],
    "swm3": ["TERMINATE"], "swm4": ["TERMINATE"],
    "refl2": ["APPROVED", "TERMINATE"], "refl3": ["APPROVED", "TERMINATE"],
    "debate3": ["VERDICT", "TERMINATE"], "debate4": ["VERDICT", "TERMINATE"],
}


def _build_hybrid_team(pattern: str, lambda_val: float, max_messages: int | None = None):
    """Build a team with hybrid termination: keyword OR adaptive OR max_messages.

    Unlike _build_adaptive_team which replaces keyword termination,
    hybrid KEEPS the original keyword condition and adds adaptive as a safety net.
    """
    mm = max_messages or PATTERN_MAX_MESSAGES.get(pattern, 20)
    team = TeamFactory.build(pattern, max_messages=mm)

    state = AdaptiveTerminationState(
        lambda_cost=lambda_val,
        patience=2,
        min_turns=2,
    )

    # Build termination conditions
    conditions = []

    # 1. Original keyword conditions (preserved from TeamFactory)
    for kw in _PATTERN_KEYWORDS.get(pattern, ["TERMINATE"]):
        conditions.append(TextMentionTermination(kw))

    # 2. Adaptive (ΔU) condition as safety net
    adaptive_term = FunctionalTermination(state.should_terminate)
    conditions.append(adaptive_term)

    # 3. Safety max_messages
    conditions.append(MaxMessageTermination(max_messages=mm))

    combined = OrTerminationCondition(*conditions)

    if hasattr(team, '_is_composed'):
        return team, state

    team._termination_condition = combined
    return team, state


CSV_FIELDS = [
    "experiment_id", "task_id", "pattern", "repeat_index",
    "pattern_category", "agent_count",
    "stop_reason", "duration_sec",
    "total_tokens_in", "total_tokens_out", "total_tokens",
    "turn_count", "agent_turn_count", "terminated_by",
    "error", "quality_score", "converged_at",
]


def _save_checkpoint(new_results, prev_data, done, total):
    """Save checkpoint with ALL results (previous dicts + new RunResults)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    new_dicts = [asdict(r) for r in new_results]
    combined = prev_data + new_dicts
    # JSON
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False, default=str)
    # CSV
    csv_path = OUTPUT_DIR / "summary_partial.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for d in combined:
            writer.writerow(d)
    print(f"  [checkpoint] {len(combined)} results saved ({done}/{total})", flush=True)


def _load_checkpoint():
    """Load checkpoint if exists. Returns (results_list, done_keys_set)."""
    if not CHECKPOINT_PATH.exists():
        return [], set()
    try:
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Build done keys: (experiment_id, task_id, pattern)
        done_keys = set()
        for r in data:
            key = (r.get("experiment_id", ""), r.get("task_id", ""), r.get("pattern", ""))
            done_keys.add(key)
        print(f"  [checkpoint] Loaded {len(data)} previous results, {len(done_keys)} unique runs", flush=True)
        # We don't reconstruct RunResult objects - just track what's done
        return data, done_keys
    except Exception as e:
        print(f"  [checkpoint] Failed to load: {e}", flush=True)
        return [], set()


MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # seconds between retries
COOLDOWN_AFTER_ERROR = 3     # seconds after any error
COOLDOWN_AFTER_CRASH = 15    # seconds after exit code crash
MAX_CONSECUTIVE_FAILURES = 5
LONG_PAUSE = 60              # seconds after too many consecutive failures


async def _run_with_retry(team_factory, run_kwargs: dict, label: str) -> tuple[RunResult, dict | None]:
    """Run a single experiment with retry logic and crash recovery.

    team_factory: callable that returns team or (team, state)
    Returns: (RunResult, adaptive_stats_dict_or_None)
    """
    for attempt in range(MAX_RETRIES):
        team_or_tuple = team_factory()
        state = None
        if isinstance(team_or_tuple, tuple):
            team = team_or_tuple[0]
            state = team_or_tuple[1] if len(team_or_tuple) > 1 else None
        else:
            team = team_or_tuple

        # Reset adaptive state for retry
        if state is not None:
            state.reset()

        result = await ExperimentRunner.run_single(
            team=team, **run_kwargs
        )

        if not result.error:
            stats = state.stats if state else None
            return result, stats

        # Check for crash-type errors
        is_crash = "3221226091" in (result.error or "") or "exit code" in (result.error or "").lower()

        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            if is_crash:
                delay = max(delay, COOLDOWN_AFTER_CRASH)
            print(f"  [retry {attempt+1}/{MAX_RETRIES}] {label} failed: {result.error[:100]}... waiting {delay}s", flush=True)
            await asyncio.sleep(delay)
        else:
            # Last attempt also failed
            delay = COOLDOWN_AFTER_ERROR
            if is_crash:
                delay = COOLDOWN_AFTER_CRASH
            await asyncio.sleep(delay)

    stats = state.stats if state else None
    return result, stats  # Return last failed result


async def main(patterns: list[str] | None = None, dry_run: bool = False):
    """Run exp05: adaptive vs baseline comparison with checkpoint recovery."""
    patterns = patterns or PATTERNS_REPRESENTATIVE
    patterns = [p for p in patterns if p in PATTERNS_REPRESENTATIVE]

    if not patterns:
        print("Exp05: No representative patterns in selection. Skipping.")
        return

    tasks = load_tasks()
    lambdas = LAMBDA_VALUES

    if dry_run:
        patterns = patterns[:1]
        tasks = tasks[:1]
        lambdas = [0.0, 0.1]

    total_baseline = len(patterns) * len(tasks)
    total_adaptive = len(patterns) * len(lambdas) * len(tasks)
    total = total_baseline + total_adaptive

    print(f"Exp05: Adaptive Termination")
    print(f"  Patterns: {patterns}")
    print(f"  Lambda values: {lambdas}")
    print(f"  Baseline runs: {total_baseline}")
    print(f"  Adaptive runs: {total_adaptive}")
    print(f"  Total: {total}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load checkpoint
    prev_data, done_keys = _load_checkpoint()
    all_results = []
    adaptive_stats_list = []  # Collect ΔU trajectories for adaptive runs
    done = 0
    skipped = 0
    consecutive_failures = 0

    # Phase 1: Baseline runs
    print("\n--- Phase 1: Baseline ---")
    for pattern in patterns:
        pattern_new = 0
        for task_meta in tasks:
            done += 1
            exp_id = f"{EXPERIMENT_ID}_baseline"
            key = (exp_id, task_meta["id"], pattern)

            if key in done_keys:
                skipped += 1
                continue

            label = f"BASELINE pattern={pattern} task={task_meta['id']}"
            print(f"  [{done}/{total}] {label}", flush=True)

            # Check consecutive failure threshold
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"  [cooldown] {consecutive_failures} consecutive failures, pausing {LONG_PAUSE}s...", flush=True)
                await asyncio.sleep(LONG_PAUSE)
                consecutive_failures = 0

            run_kwargs = dict(
                task_text=task_meta["task"],
                experiment_id=exp_id,
                task_id=task_meta["id"],
                pattern=pattern,
            )
            result, _ = await _run_with_retry(
                lambda p=pattern: TeamFactory.build(p),
                run_kwargs, label,
            )

            if result.error:
                consecutive_failures += 1
            else:
                consecutive_failures = 0

            all_results.append(result)
            pattern_new += 1

        # Checkpoint after each pattern's baseline completes
        if pattern_new > 0:
            _save_checkpoint(all_results, prev_data, done, total)

    if skipped > 0:
        print(f"  [skip] {skipped} baseline runs already in checkpoint", flush=True)

    # Phase 2: Adaptive runs (per lambda)
    print("\n--- Phase 2: Adaptive ---")
    skipped = 0
    consecutive_failures = 0
    for lambda_val in lambdas:
        for pattern in patterns:
            block_new = 0
            for task_meta in tasks:
                done += 1
                exp_id = f"{EXPERIMENT_ID}_adaptive_l{lambda_val}"
                key = (exp_id, task_meta["id"], pattern)

                if key in done_keys:
                    skipped += 1
                    continue

                label = f"ADAPTIVE λ={lambda_val} pattern={pattern} task={task_meta['id']}"
                print(f"  [{done}/{total}] {label}", flush=True)

                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(f"  [cooldown] {consecutive_failures} consecutive failures, pausing {LONG_PAUSE}s...", flush=True)
                    await asyncio.sleep(LONG_PAUSE)
                    consecutive_failures = 0

                run_kwargs = dict(
                    task_text=task_meta["task"],
                    experiment_id=exp_id,
                    task_id=task_meta["id"],
                    pattern=pattern,
                )
                result, stats = await _run_with_retry(
                    lambda p=pattern, lv=lambda_val: _build_adaptive_team(p, lv),
                    run_kwargs, label,
                )

                if result.error:
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0

                all_results.append(result)

                # Save adaptive termination stats (ΔU trajectory)
                if stats is not None:
                    adaptive_stats_list.append({
                        "experiment_id": exp_id,
                        "task_id": task_meta["id"],
                        "pattern": pattern,
                        "lambda": lambda_val,
                        **stats,
                    })

                block_new += 1

            # Checkpoint after each λ×pattern block
            if block_new > 0:
                _save_checkpoint(all_results, prev_data, done, total)

    if skipped > 0:
        print(f"  [skip] {skipped} adaptive runs already in checkpoint", flush=True)

    # Save final results (prev_data dicts + new RunResult objects)
    final_dicts = prev_data + [asdict(r) for r in all_results]
    with open(OUTPUT_DIR / "raw.json", "w", encoding="utf-8") as f:
        json.dump(final_dicts, f, indent=2, ensure_ascii=False, default=str)
    with open(OUTPUT_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for d in final_dicts:
            writer.writerow(d)

    # Save adaptive stats (ΔU trajectories per run)
    if adaptive_stats_list:
        stats_path = OUTPUT_DIR / "adaptive_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(adaptive_stats_list, f, indent=2, ensure_ascii=False, default=str)
        print(f"  Adaptive stats saved: {len(adaptive_stats_list)} entries -> {stats_path}")

    total_count = len(final_dicts)
    print(f"\nExp05 complete: {total_count} runs ({len(prev_data)} recovered + {len(all_results)} new)")
    print(f"  Saved to: {OUTPUT_DIR}")

    errors = [r for r in all_results if r.error]
    if errors:
        print(f"  Errors: {len(errors)}")

    return all_results


async def run_hybrid(patterns: list[str] | None = None, dry_run: bool = False):
    """Run hybrid termination experiment: keyword OR adaptive OR max_messages.

    Tests specified patterns (default: 6 representative across all categories)
    with λ=0.1, 25 tasks. Checkpoints to avoid re-running completed combos.
    Hybrid KEEPS original keyword and adds ΔU as safety net.
    """
    ALL_HYBRID_PATTERNS = ["swm4", "debate3", "rr3", "sel3", "refl2", "pipe"]
    patterns = patterns or ALL_HYBRID_PATTERNS
    patterns = [p for p in patterns if p in PATTERNS_ALL]

    if not patterns:
        print("Exp05-Hybrid: No valid patterns. Skipping.")
        return

    lambda_val = 0.1
    tasks = load_tasks()

    if dry_run:
        tasks = tasks[:2]

    total = len(patterns) * len(tasks)

    print(f"Exp05-Hybrid: Keyword OR Adaptive Termination")
    print(f"  Patterns: {patterns}")
    print(f"  λ = {lambda_val}")
    print(f"  Total runs: {total}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing hybrid results as checkpoint
    hybrid_path = OUTPUT_DIR / "hybrid_results.json"
    prev_data = []
    done_keys = set()
    if hybrid_path.exists():
        try:
            with open(hybrid_path, encoding="utf-8") as f:
                prev_data = json.load(f)
            for r in prev_data:
                done_keys.add((r.get("task_id", ""), r.get("pattern", "")))
            print(f"  [checkpoint] Loaded {len(prev_data)} existing hybrid results, {len(done_keys)} unique", flush=True)
        except Exception as e:
            print(f"  [checkpoint] Failed to load: {e}", flush=True)

    all_results = []
    adaptive_stats_list = []
    consecutive_failures = 0
    skipped = 0

    for pattern in patterns:
        for task_meta in tasks:
            # Skip already-completed runs
            if (task_meta["id"], pattern) in done_keys:
                skipped += 1
                continue

            label = f"HYBRID λ={lambda_val} pattern={pattern} task={task_meta['id']}"
            print(f"  [{len(prev_data)+len(all_results)+1}/{total}] {label}", flush=True)

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"  [cooldown] pausing {LONG_PAUSE}s...", flush=True)
                await asyncio.sleep(LONG_PAUSE)
                consecutive_failures = 0

            run_kwargs = dict(
                task_text=task_meta["task"],
                experiment_id=f"{EXPERIMENT_ID}_hybrid_l{lambda_val}",
                task_id=task_meta["id"],
                pattern=pattern,
            )

            result, stats = await _run_with_retry(
                lambda p=pattern, lv=lambda_val: _build_hybrid_team(p, lv),
                run_kwargs, label,
            )

            # Post-process terminated_by for hybrid distinction
            if result and not result.error:
                sr = str(result.stop_reason or "").lower()
                if any(kw in sr for kw in ["terminate", "approved", "verdict", "analysis_done"]):
                    result.terminated_by = "keyword_hybrid"
                elif "max" in sr:
                    result.terminated_by = "max_messages"
                else:
                    result.terminated_by = "adaptive_hybrid"

            if result.error:
                consecutive_failures += 1
            else:
                consecutive_failures = 0

            all_results.append(result)

            if stats is not None:
                adaptive_stats_list.append({
                    "experiment_id": f"{EXPERIMENT_ID}_hybrid_l{lambda_val}",
                    "task_id": task_meta["id"],
                    "pattern": pattern,
                    "lambda": lambda_val,
                    **stats,
                })

    if skipped > 0:
        print(f"  [skip] {skipped} hybrid runs already in checkpoint", flush=True)

    # Save results (merge with existing checkpoint)
    result_dicts = prev_data + [asdict(r) for r in all_results]

    with open(hybrid_path, "w", encoding="utf-8") as f:
        json.dump(result_dicts, f, indent=2, ensure_ascii=False, default=str)

    with open(OUTPUT_DIR / "hybrid_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for d in result_dicts:
            writer.writerow(d)

    if adaptive_stats_list:
        with open(OUTPUT_DIR / "hybrid_adaptive_stats.json", "w", encoding="utf-8") as f:
            json.dump(adaptive_stats_list, f, indent=2, ensure_ascii=False, default=str)

    # Print summary
    print(f"\nExp05-Hybrid complete: {len(all_results)} runs")

    for pattern in patterns:
        p_results = [r for r in all_results if r.pattern == pattern and not r.error]
        keyword_count = sum(1 for r in p_results if r.terminated_by == "keyword_hybrid")
        adaptive_count = sum(1 for r in p_results if r.terminated_by == "adaptive_hybrid")
        max_count = sum(1 for r in p_results if r.terminated_by == "max_messages")
        avg_tokens = sum(r.total_tokens for r in p_results) / max(len(p_results), 1)

        print(f"\n  {pattern}:")
        print(f"    keyword_hybrid: {keyword_count}/{len(p_results)}")
        print(f"    adaptive_hybrid: {adaptive_count}/{len(p_results)}")
        print(f"    max_messages: {max_count}/{len(p_results)}")
        print(f"    avg tokens: {avg_tokens:.0f}")

    errors = [r for r in all_results if r.error]
    if errors:
        print(f"\n  Errors: {len(errors)}")

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Exp05: Adaptive/Hybrid Termination")
    parser.add_argument("--hybrid", action="store_true",
                        help="Run hybrid (keyword OR adaptive) experiment (default: 6 patterns)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run with minimal tasks for testing")
    parser.add_argument("--patterns", nargs="*",
                        help="Override pattern list (baseline/adaptive mode)")
    args = parser.parse_args()

    if args.hybrid:
        asyncio.run(run_hybrid(patterns=args.patterns, dry_run=args.dry_run))
    else:
        asyncio.run(main(patterns=args.patterns, dry_run=args.dry_run))
