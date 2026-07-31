"""
Parse experiment output log to extract preliminary run data.
Useful when checkpoint didn't save (running process has old code).

Usage:
  python parse_log.py <log_file>
  python parse_log.py <log_file> --csv output.csv
"""

import re
import sys
import csv
from pathlib import Path
from collections import defaultdict


def parse_experiment_log(log_path: str) -> list[dict]:
    """Parse experiment output log and extract per-run metrics."""

    log_path = Path(log_path)
    if not log_path.exists():
        print(f"Error: {log_path} not found")
        return []

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    runs = []
    current_run = None
    sdk_calls = []
    error_in_current = False

    # Regex patterns
    progress_re = re.compile(
        r'\[(\d+)/(\d+)\].*pattern=(\w+)\s+task=(\w+)\s+repeat=(\d+)'
    )
    sdk_re = re.compile(
        r'SDK OK \(([0-9.]+)s.*in=(\d+), out=(\d+), text_chars=(\d+)\)'
    )
    error_re = re.compile(r'NameError|ValueError.*GroupChatError')
    exp_header = re.compile(r'Exp\d+: (\d+) patterns')

    for line in lines:
        # Match progress line
        pm = progress_re.search(line)
        if pm:
            # Save previous run
            if current_run is not None:
                current_run["sdk_calls"] = len(sdk_calls)
                current_run["total_tokens_in"] = sum(c["tok_in"] for c in sdk_calls)
                current_run["total_tokens_out"] = sum(c["tok_out"] for c in sdk_calls)
                current_run["total_tokens"] = current_run["total_tokens_in"] + current_run["total_tokens_out"]
                current_run["total_duration"] = sum(c["duration"] for c in sdk_calls)
                current_run["error"] = error_in_current
                runs.append(current_run)

            # Start new run
            idx, total, pattern, task_id, repeat = pm.groups()
            current_run = {
                "run_index": int(idx),
                "total_runs": int(total),
                "pattern": pattern,
                "task_id": task_id,
                "repeat": int(repeat),
            }
            sdk_calls = []
            error_in_current = False
            continue

        # Match SDK call
        sm = sdk_re.search(line)
        if sm and current_run is not None:
            dur, tok_in, tok_out, text_chars = sm.groups()
            sdk_calls.append({
                "duration": float(dur),
                "tok_in": int(tok_in),
                "tok_out": int(tok_out),
                "text_chars": int(text_chars),
            })
            continue

        # Match error
        if error_re.search(line) and current_run is not None:
            error_in_current = True

    # Save last run
    if current_run is not None and sdk_calls:
        current_run["sdk_calls"] = len(sdk_calls)
        current_run["total_tokens_in"] = sum(c["tok_in"] for c in sdk_calls)
        current_run["total_tokens_out"] = sum(c["tok_out"] for c in sdk_calls)
        current_run["total_tokens"] = current_run["total_tokens_in"] + current_run["total_tokens_out"]
        current_run["total_duration"] = sum(c["duration"] for c in sdk_calls)
        current_run["error"] = error_in_current
        runs.append(current_run)

    return runs


def summarize(runs: list[dict]):
    """Print summary statistics from parsed log."""
    if not runs:
        print("No runs found")
        return

    print(f"\nParsed {len(runs)} completed runs")
    print("=" * 60)

    # Group by pattern
    by_pattern = defaultdict(list)
    for r in runs:
        by_pattern[r["pattern"]].append(r)

    print(f"\n{'Pattern':<8} {'Runs':>5} {'Errors':>6} {'Avg SDK':>8} "
          f"{'Avg Dur':>8} {'Avg TokIn':>10} {'Avg TokOut':>10}")
    print("-" * 65)

    for pattern in sorted(by_pattern.keys()):
        patt_runs = by_pattern[pattern]
        n = len(patt_runs)
        errors = sum(1 for r in patt_runs if r["error"])
        avg_sdk = sum(r["sdk_calls"] for r in patt_runs) / n
        avg_dur = sum(r["total_duration"] for r in patt_runs) / n
        avg_in = sum(r["total_tokens_in"] for r in patt_runs) / n
        avg_out = sum(r["total_tokens_out"] for r in patt_runs) / n
        print(f"{pattern:<8} {n:>5} {errors:>6} {avg_sdk:>8.1f} "
              f"{avg_dur:>8.1f}s {avg_in:>10.0f} {avg_out:>10.0f}")

    # Error summary
    errors = [r for r in runs if r["error"]]
    if errors:
        print(f"\nErrors: {len(errors)}/{len(runs)} ({100*len(errors)/len(runs):.1f}%)")
        for e in errors:
            print(f"  {e['pattern']}/{e['task_id']}/repeat={e['repeat']}")

    # Task category breakdown
    print(f"\n{'Task Cat':<8} {'Runs':>5} {'Avg Dur':>8} {'Avg Tokens':>10}")
    print("-" * 35)
    by_task_cat = defaultdict(list)
    for r in runs:
        cat = r["task_id"].split("_")[0]
        by_task_cat[cat].append(r)
    for cat in sorted(by_task_cat.keys()):
        cat_runs = by_task_cat[cat]
        n = len(cat_runs)
        avg_dur = sum(r["total_duration"] for r in cat_runs) / n
        avg_tok = sum(r["total_tokens"] for r in cat_runs) / n
        print(f"{cat:<8} {n:>5} {avg_dur:>8.1f}s {avg_tok:>10.0f}")


def save_csv(runs: list[dict], output_path: str):
    """Save parsed data to CSV."""
    if not runs:
        return
    fieldnames = [
        "run_index", "pattern", "task_id", "repeat",
        "sdk_calls", "total_duration",
        "total_tokens_in", "total_tokens_out", "total_tokens",
        "error",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(runs)
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_log.py <log_file> [--csv output.csv]")
        sys.exit(1)

    log_file = sys.argv[1]
    runs = parse_experiment_log(log_file)
    summarize(runs)

    if "--csv" in sys.argv:
        csv_idx = sys.argv.index("--csv")
        if csv_idx + 1 < len(sys.argv):
            save_csv(runs, sys.argv[csv_idx + 1])
