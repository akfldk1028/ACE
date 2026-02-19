"""Compute mean, std, 95% CI for all experiment data grouped by pattern."""
import json
import math
import os
from collections import defaultdict

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

def load_runs(subdir):
    """Load all runs from raw*.json files in a subdirectory."""
    runs = []
    path = os.path.join(RESULTS_DIR, subdir)
    if not os.path.exists(path):
        return runs
    for f in sorted(os.listdir(path)):
        if f.startswith("raw") and f.endswith(".json"):
            with open(os.path.join(path, f), encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    runs.extend(data)
    return runs

def ci95(values):
    """Return (mean, std, ci_low, ci_high) for a list of numbers."""
    n = len(values)
    if n == 0:
        return (0, 0, 0, 0)
    mean = sum(values) / n
    if n == 1:
        return (mean, 0, mean, mean)
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    se = std / math.sqrt(n)
    # t-value for 95% CI (approximate for small n)
    t_vals = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
              7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 15: 2.145,
              20: 2.093, 25: 2.064, 30: 2.045, 50: 2.009, 100: 1.984}
    t = 1.96  # default
    for k in sorted(t_vals.keys()):
        if n - 1 <= k:
            t = t_vals[k]
            break
    ci_low = mean - t * se
    ci_high = mean + t * se
    return (mean, std, ci_low, ci_high)

def analyze_experiment(exp_name):
    """Analyze all runs for an experiment, grouped by pattern."""
    runs = load_runs(exp_name)
    if not runs:
        return {}

    by_pattern = defaultdict(list)
    for r in runs:
        p = r.get("pattern", "unknown")
        by_pattern[p].append(r)

    results = {}
    for pattern, pattern_runs in sorted(by_pattern.items()):
        # Filter out error runs
        valid = [r for r in pattern_runs if not r.get("error")]
        if not valid:
            continue

        tokens = [r["total_tokens"] for r in valid]
        durations = [r["duration_sec"] for r in valid]
        turns = [r["agent_turn_count"] for r in valid if r.get("agent_turn_count")]
        quality = [r["quality_score"] for r in valid if r.get("quality_score") is not None]

        results[pattern] = {
            "n": len(valid),
            "n_errors": len(pattern_runs) - len(valid),
            "tokens": ci95(tokens),
            "duration": ci95(durations),
            "turns": ci95(turns) if turns else None,
            "quality": ci95(quality) if quality else None,
        }

    return results

def fmt(stat, decimals=0):
    """Format (mean, std, ci_low, ci_high) as 'mean +/- std [ci_low, ci_high]'."""
    if stat is None:
        return "N/A"
    mean, std, ci_lo, ci_hi = stat
    if decimals == 0:
        return f"{mean:.0f} +/- {std:.0f} [{ci_lo:.0f}, {ci_hi:.0f}]"
    return f"{mean:.{decimals}f} +/- {std:.{decimals}f} [{ci_lo:.{decimals}f}, {ci_hi:.{decimals}f}]"

def print_table(title, results):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")
    print(f"{'Pattern':<12} {'N':>4} {'Err':>4}  {'Tokens (mean +/- std [95% CI])':<40} {'Duration (s)':<35} {'Turns':<25} {'Quality':<25}")
    print("-" * 160)
    for pattern, data in sorted(results.items()):
        print(f"{pattern:<12} {data['n']:>4} {data['n_errors']:>4}  "
              f"{fmt(data['tokens']):<40} "
              f"{fmt(data['duration'], 1):<35} "
              f"{fmt(data['turns'], 1) if data['turns'] else 'N/A':<25} "
              f"{fmt(data['quality'], 2) if data['quality'] else 'N/A':<25}")

def print_markdown_table(title, results):
    """Print in markdown format for direct paper insertion."""
    print(f"\n### {title}\n")
    print(f"| Pattern | N | Tokens (mean +/- std) | 95% CI | Duration (s) | Turns | Quality |")
    print(f"|---------|---|----------------------|--------|-------------|-------|---------|")
    for pattern, data in sorted(results.items()):
        t = data['tokens']
        d = data['duration']
        tr = data['turns']
        q = data['quality']
        print(f"| {pattern} | {data['n']} | "
              f"{t[0]:.0f} +/- {t[1]:.0f} | [{t[2]:.0f}, {t[3]:.0f}] | "
              f"{d[0]:.1f} +/- {d[1]:.1f} | "
              f"{f'{tr[0]:.1f} +/- {tr[1]:.1f}' if tr else 'N/A'} | "
              f"{f'{q[0]:.2f} +/- {q[1]:.2f}' if q else 'N/A'} |")

if __name__ == "__main__":
    for exp in ["exp01", "exp02", "exp05"]:
        results = analyze_experiment(exp)
        if results:
            print_table(f"Experiment: {exp}", results)
            print_markdown_table(f"Experiment: {exp}", results)
