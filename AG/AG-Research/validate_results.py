"""
Validate experiment results for completeness and integrity.

Usage:
  python validate_results.py           # Check all experiments
  python validate_results.py --exp 01  # Check specific experiment
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    PATTERNS_ALL, PATTERNS_FLAT,
    PATTERNS_CENTRALIZED, PATTERNS_DECENTRALIZED,
    PATTERNS_FEEDBACK, PATTERNS_COMPOSED,
    REPEAT_COUNT, RESULTS_DIR,
)


def validate_exp01():
    """Validate exp01 results."""
    print("=== Exp01: Pattern Efficiency ===")
    exp_dir = RESULTS_DIR / "exp01"

    # Check CSV
    csv_path = exp_dir / "summary.csv"
    if not csv_path.exists():
        print(f"  [FAIL] No summary.csv at {csv_path}")
        return False

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Total rows: {len(rows)}")

    # Check pattern coverage
    patterns_found = set(r['pattern'] for r in rows)
    expected = set(PATTERNS_ALL)
    missing = expected - patterns_found
    extra = patterns_found - expected
    print(f"  Patterns: {len(patterns_found)}/{len(expected)}")
    if missing:
        print(f"  [WARN] Missing patterns: {missing}")
    if extra:
        print(f"  [WARN] Unexpected patterns: {extra}")

    # Check per-pattern counts
    from collections import Counter
    from experiment_utils import load_tasks
    num_tasks = len(load_tasks())
    pattern_counts = Counter(r['pattern'] for r in rows)
    expected_per_pattern = num_tasks * REPEAT_COUNT
    for p, count in sorted(pattern_counts.items()):
        status = "[OK]" if count == expected_per_pattern else f"[WARN] expected {expected_per_pattern}"
        print(f"    {p}: {count} runs {status}")

    # Check errors
    errors = [r for r in rows if r.get('error') and r['error'] not in ('', 'None', 'False')]
    print(f"  Errors: {len(errors)}/{len(rows)} ({len(errors)/len(rows)*100:.1f}%)")

    # Check token tracking
    zero_tokens = [r for r in rows if int(r.get('total_tokens', 0)) == 0 and not r.get('error')]
    if zero_tokens:
        print(f"  [WARN] {len(zero_tokens)} runs with zero tokens (token tracking issue?)")
    else:
        print("  [OK] All successful runs have non-zero token counts")

    # Check raw JSON
    json_path = exp_dir / "raw.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        print(f"  Raw JSON: {len(raw)} runs")
        # Check turns data
        with_turns = sum(1 for r in raw if r.get('turns'))
        print(f"  Runs with turn data: {with_turns}/{len(raw)}")
    else:
        print(f"  [WARN] No raw.json (needed for exp03/04 analysis)")

    # Check category files
    for cat in ['A', 'B1', 'B2', 'C', 'D']:
        cat_csv = exp_dir / f"summary_{cat}.csv"
        cat_json = exp_dir / f"raw_{cat}.json"
        if cat_csv.exists():
            with open(cat_csv, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in csv.DictReader(f))
            print(f"  Category {cat}: {count} rows in summary_{cat}.csv")

    return len(missing) == 0


def validate_exp02():
    """Validate exp02 results."""
    print("\n=== Exp02: Termination Quality ===")
    exp_dir = RESULTS_DIR / "exp02"

    csv_path = exp_dir / "summary.csv"
    if not csv_path.exists():
        print(f"  [SKIP] No data yet")
        return True

    with open(csv_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"  Total rows: {len(rows)}")

    # Check scores
    scores_path = exp_dir / "scores.csv"
    if scores_path.exists():
        with open(scores_path, 'r', encoding='utf-8') as f:
            scores = list(csv.DictReader(f))
        print(f"  Turn scores: {len(scores)} entries")
    else:
        print(f"  [WARN] No scores.csv")

    return True


def validate_exp05():
    """Validate exp05 results."""
    print("\n=== Exp05: Adaptive Termination ===")
    exp_dir = RESULTS_DIR / "exp05"

    csv_path = exp_dir / "summary.csv"
    if not csv_path.exists():
        print(f"  [SKIP] No data yet")
        return True

    with open(csv_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"  Total rows: {len(rows)}")

    # Check baseline vs adaptive
    baseline = [r for r in rows if 'baseline' in r.get('experiment_id', '')]
    adaptive = [r for r in rows if 'adaptive' in r.get('experiment_id', '')]
    print(f"  Baseline: {len(baseline)}, Adaptive: {len(adaptive)}")

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', nargs='+', choices=['01', '02', '05'])
    args = parser.parse_args()

    exps = args.exp or ['01', '02', '05']

    all_ok = True
    for exp in exps:
        if exp == '01':
            all_ok &= validate_exp01()
        elif exp == '02':
            all_ok &= validate_exp02()
        elif exp == '05':
            all_ok &= validate_exp05()

    print(f"\n{'='*40}")
    print(f"Validation: {'PASS' if all_ok else 'ISSUES FOUND'}")


if __name__ == '__main__':
    main()
