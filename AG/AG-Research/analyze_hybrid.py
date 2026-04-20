"""
Analyze hybrid termination experiment results.
Compares keyword_hybrid vs adaptive_hybrid termination,
token savings vs baseline, and quality preservation.

Usage: python analyze_hybrid.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import csv
import statistics
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results')
EXP05_DIR = RESULTS_DIR / 'exp05'


def load_hybrid_results():
    """Load hybrid experiment results."""
    path = EXP05_DIR / 'hybrid_results.json'
    if not path.exists():
        print(f"[ERROR] {path} not found. Run hybrid experiment first.")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_baseline_results():
    """Load baseline results from checkpoint or raw.json."""
    for fname in ['raw.json', 'checkpoint.json']:
        path = EXP05_DIR / fname
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Filter for baseline runs of swm4 and debate3
            baseline = [r for r in data
                        if r.get('experiment_id', '').endswith('_baseline')
                        and r.get('pattern') in ('swm4', 'debate3')
                        and not r.get('error')]
            return baseline
    return []


def analyze():
    hybrid = load_hybrid_results()
    baseline = load_baseline_results()

    if not hybrid:
        return

    # Filter successful runs
    hybrid_ok = [r for r in hybrid if not r.get('error')]

    print("=" * 60)
    print("HYBRID TERMINATION ANALYSIS")
    print("=" * 60)

    for pattern in ['swm4', 'debate3']:
        h_runs = [r for r in hybrid_ok if r['pattern'] == pattern]
        b_runs = [r for r in baseline if r['pattern'] == pattern]

        if not h_runs:
            print(f"\n  {pattern}: No hybrid results")
            continue

        # Termination type counts
        keyword_count = sum(1 for r in h_runs if r.get('terminated_by') == 'keyword_hybrid')
        adaptive_count = sum(1 for r in h_runs if r.get('terminated_by') == 'adaptive_hybrid')
        max_count = sum(1 for r in h_runs if r.get('terminated_by') == 'max_messages')
        total = len(h_runs)

        # Token stats
        h_tokens = [r['total_tokens'] for r in h_runs]
        h_turns = [r['turn_count'] for r in h_runs]

        print(f"\n{'='*40}")
        print(f"  {pattern.upper()} (N={total})")
        print(f"{'='*40}")
        print(f"  Termination breakdown:")
        print(f"    keyword_hybrid:  {keyword_count}/{total} ({keyword_count/total*100:.0f}%)")
        print(f"    adaptive_hybrid: {adaptive_count}/{total} ({adaptive_count/total*100:.0f}%)")
        print(f"    max_messages:    {max_count}/{total} ({max_count/total*100:.0f}%)")

        print(f"\n  Token stats (hybrid):")
        print(f"    mean:   {statistics.mean(h_tokens):.0f}")
        print(f"    median: {statistics.median(h_tokens):.0f}")
        print(f"    std:    {statistics.stdev(h_tokens):.0f}" if len(h_tokens) > 1 else "    std: N/A")
        print(f"    turns:  {statistics.mean(h_turns):.1f} avg")

        if b_runs:
            b_tokens = [r['total_tokens'] for r in b_runs]
            b_turns = [r['turn_count'] for r in b_runs]

            savings = 1 - statistics.mean(h_tokens) / statistics.mean(b_tokens)
            turn_savings = 1 - statistics.mean(h_turns) / statistics.mean(b_turns)

            print(f"\n  Baseline comparison:")
            print(f"    baseline mean tokens: {statistics.mean(b_tokens):.0f}")
            print(f"    hybrid mean tokens:   {statistics.mean(h_tokens):.0f}")
            print(f"    token savings:        {savings*100:+.1f}%")
            print(f"    turn savings:         {turn_savings*100:+.1f}%")

            # T-test for token difference
            if len(h_tokens) >= 5 and len(b_tokens) >= 5:
                try:
                    from scipy import stats
                    t_stat, p_val = stats.ttest_ind(h_tokens, b_tokens, equal_var=False)
                    print(f"    Welch t-test: t={t_stat:.3f}, p={p_val:.4f}")
                except ImportError:
                    print("    (scipy not available for t-test)")

        # Compare keyword-fired vs adaptive-fired token usage
        kw_tokens = [r['total_tokens'] for r in h_runs if r.get('terminated_by') == 'keyword_hybrid']
        ad_tokens = [r['total_tokens'] for r in h_runs if r.get('terminated_by') == 'adaptive_hybrid']

        if kw_tokens and ad_tokens:
            print(f"\n  Keyword vs Adaptive within hybrid:")
            print(f"    keyword-triggered: {statistics.mean(kw_tokens):.0f} avg tokens (N={len(kw_tokens)})")
            print(f"    adaptive-triggered: {statistics.mean(ad_tokens):.0f} avg tokens (N={len(ad_tokens)})")

    # Summary for paper
    print(f"\n{'='*60}")
    print("PAPER-READY SUMMARY")
    print(f"{'='*60}")

    for pattern in ['swm4', 'debate3']:
        h_runs = [r for r in hybrid_ok if r['pattern'] == pattern]
        b_runs = [r for r in baseline if r['pattern'] == pattern]

        if not h_runs:
            continue

        total = len(h_runs)
        keyword_pct = sum(1 for r in h_runs if r.get('terminated_by') == 'keyword_hybrid') / total * 100
        adaptive_pct = sum(1 for r in h_runs if r.get('terminated_by') == 'adaptive_hybrid') / total * 100

        h_mean = statistics.mean([r['total_tokens'] for r in h_runs])
        b_mean = statistics.mean([r['total_tokens'] for r in b_runs]) if b_runs else 0
        savings = (1 - h_mean / b_mean) * 100 if b_mean > 0 else 0

        print(f"  {pattern}: keyword={keyword_pct:.0f}%, adaptive={adaptive_pct:.0f}%, savings={savings:+.0f}%")

    print("\n[DONE]")


if __name__ == '__main__':
    analyze()
