"""
Experiment 04: Error Attribution Analysis
==========================================
Analyzes error patterns and output characteristics from exp01 data.
Classifies stop reasons, error distributions, and content patterns by topology.

Reads: results/exp01/raw.json (v2, 200 runs)
       results/exp01/summary_all.csv (v1, 780 runs - for error data)
       results/exp01/summary.csv (v2, 200 runs)
Output: results/exp04/error_analysis.csv
        results/exp04/error_summary.csv
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import csv
import re
from pathlib import Path
from collections import defaultdict, Counter
import statistics

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results')
EXP01_DIR = RESULTS_DIR / 'exp01'
EXP04_DIR = RESULTS_DIR / 'exp04'
EXP04_DIR.mkdir(exist_ok=True)

CATEGORY_MAP = {
    'rr2': 'A', 'rr3': 'A', 'rr4': 'A',
    'sel3': 'B1', 'sel4': 'B1',
    'swm3': 'B2', 'swm4': 'B2',
    'refl2': 'C', 'refl3': 'C', 'debate3': 'C', 'debate4': 'C',
    'pipe': 'D', 'moa': 'D',
}


def classify_content_issues(content):
    """Classify potential content issues in agent output."""
    issues = []
    if not content:
        issues.append('empty_response')
        return issues

    # Check for truncation indicators
    if content.endswith('...') or len(content) > 1900:
        issues.append('possibly_truncated')

    # Check for TERMINATE presence
    if 'TERMINATE' in content:
        issues.append('contains_terminate')

    # Check for repetitive content
    sentences = re.split(r'[.!?]\s', content)
    if len(sentences) > 3:
        unique_ratio = len(set(s.strip().lower() for s in sentences if s.strip())) / len(sentences)
        if unique_ratio < 0.5:
            issues.append('repetitive_content')

    # Check for hedging/uncertainty
    hedging_words = ['however', 'although', 'but', 'nevertheless', 'on the other hand']
    hedging_count = sum(1 for w in hedging_words if w in content.lower())
    if hedging_count >= 3:
        issues.append('high_hedging')

    # Check for list-heavy responses (potential incompleteness)
    list_items = len(re.findall(r'^\s*[-*\d+\.]\s', content, re.MULTILINE))
    if list_items > 10:
        issues.append('list_heavy')

    return issues


def analyze_stop_patterns(runs):
    """Analyze termination patterns across all runs."""
    by_pattern = defaultdict(list)
    for r in runs:
        by_pattern[r['pattern']].append(r)

    print("\n=== Stop Reason Distribution by Pattern ===")
    print(f"{'Pattern':<10} {'Cat':<4} {'N':>4} {'Keyword%':>9} {'MaxMsg%':>8} {'Error%':>7} {'Other%':>7}")
    print("-" * 55)

    summary = []
    pattern_order = ['rr2', 'rr3', 'rr4', 'sel3', 'sel4', 'swm3', 'swm4',
                     'refl2', 'refl3', 'debate3', 'debate4', 'pipe', 'moa']

    for p in pattern_order:
        if p not in by_pattern:
            continue
        runs_p = by_pattern[p]
        n = len(runs_p)
        stops = Counter()
        for r in runs_p:
            sr = r.get('stop_reason', '') or ''
            tb = r.get('terminated_by', '') or ''
            has_error = bool(r.get('error'))

            if has_error:
                stops['error'] += 1
            elif 'TERMINATE' in sr or tb == 'keyword':
                stops['keyword'] += 1
            elif 'Maximum' in sr or tb == 'max_messages':
                stops['max_messages'] += 1
            else:
                stops['other'] += 1

        cat = CATEGORY_MAP.get(p, '?')
        kw_pct = stops['keyword'] / n * 100
        mm_pct = stops['max_messages'] / n * 100
        err_pct = stops['error'] / n * 100
        other_pct = stops['other'] / n * 100

        print(f"{p:<10} {cat:<4} {n:>4} {kw_pct:>8.1f}% {mm_pct:>7.1f}% {err_pct:>6.1f}% {other_pct:>6.1f}%")

        summary.append({
            'pattern': p,
            'category': cat,
            'n_runs': n,
            'keyword_pct': f"{kw_pct:.1f}",
            'max_messages_pct': f"{mm_pct:.1f}",
            'error_pct': f"{err_pct:.1f}",
            'other_pct': f"{other_pct:.1f}",
        })

    return summary


def analyze_content_patterns(raw_data):
    """Analyze content-level patterns in agent outputs."""
    by_pattern = defaultdict(list)
    for r in raw_data:
        if r.get('error'):
            continue
        by_pattern[r['pattern']].append(r)

    print("\n=== Content Pattern Analysis ===")
    print(f"{'Pattern':<10} {'Cat':<4} {'AvgLen':>7} {'Terminate%':>11} {'Trunc%':>7} {'Repet%':>7} {'Hedge%':>7}")
    print("-" * 60)

    content_summary = []
    pattern_order = ['rr3', 'sel3', 'sel4', 'swm3', 'swm4', 'refl2', 'debate3', 'pipe']

    for p in pattern_order:
        if p not in by_pattern:
            continue
        runs = by_pattern[p]
        n = len(runs)

        all_issues = Counter()
        all_lengths = []
        total_turns = 0

        for r in runs:
            agent_turns = [t for t in r.get('turns', [])
                          if t.get('source', '') != 'user' and t.get('content')]
            for t in agent_turns:
                content = t.get('content', '')
                all_lengths.append(len(content))
                issues = classify_content_issues(content)
                for issue in issues:
                    all_issues[issue] += 1
                total_turns += 1

        cat = CATEGORY_MAP.get(p, '?')
        avg_len = statistics.mean(all_lengths) if all_lengths else 0
        term_pct = all_issues['contains_terminate'] / total_turns * 100 if total_turns else 0
        trunc_pct = all_issues['possibly_truncated'] / total_turns * 100 if total_turns else 0
        repet_pct = all_issues['repetitive_content'] / total_turns * 100 if total_turns else 0
        hedge_pct = all_issues['high_hedging'] / total_turns * 100 if total_turns else 0

        print(f"{p:<10} {cat:<4} {avg_len:>7.0f} {term_pct:>10.1f}% {trunc_pct:>6.1f}% {repet_pct:>6.1f}% {hedge_pct:>6.1f}%")

        content_summary.append({
            'pattern': p,
            'category': cat,
            'n_runs': n,
            'total_agent_turns': total_turns,
            'avg_content_length': f"{avg_len:.0f}",
            'terminate_mention_pct': f"{term_pct:.1f}",
            'truncation_pct': f"{trunc_pct:.1f}",
            'repetitive_pct': f"{repet_pct:.1f}",
            'hedging_pct': f"{hedge_pct:.1f}",
        })

    return content_summary


def analyze_task_error_interaction(runs):
    """Analyze which task types are most error-prone for each pattern."""
    # Only relevant for v1 data with errors
    errors_by_task = defaultdict(lambda: defaultdict(int))
    totals_by_task = defaultdict(lambda: defaultdict(int))

    for r in runs:
        p = r.get('pattern', '')
        task = r.get('task_id', '')
        task_domain = task.split('_')[0] if task else 'unknown'
        totals_by_task[p][task_domain] += 1
        if r.get('error'):
            errors_by_task[p][task_domain] += 1

    # Only print patterns with errors
    has_errors = {p for p in errors_by_task if any(errors_by_task[p].values())}
    if has_errors:
        print("\n=== Error Distribution by Task Domain (patterns with errors) ===")
        for p in sorted(has_errors):
            print(f"\n  {p}:")
            for domain in sorted(totals_by_task[p].keys()):
                total = totals_by_task[p][domain]
                errs = errors_by_task[p].get(domain, 0)
                if total > 0:
                    print(f"    {domain}: {errs}/{total} errors ({errs/total*100:.1f}%)")
    else:
        print("\n=== No errors found in analyzed data (v2 = 0% error rate) ===")


def main():
    # Load v2 raw data (for content analysis)
    raw_data = []
    for fname in ['raw.json']:
        path = EXP01_DIR / fname
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            print(f"[OK] Loaded {len(raw_data)} runs from {fname}")
            break

    # Load v1 summary for error analysis (has actual errors)
    v1_runs = []
    v1_path = EXP01_DIR / 'summary_all.csv'
    if v1_path.exists():
        with open(v1_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                v1_runs.append(row)
        print(f"[OK] Loaded {len(v1_runs)} v1 runs for error analysis")

    # 1. Stop reason analysis (use v1 data for error distribution + v2 for clean patterns)
    if v1_runs:
        print("\n--- V1 Data (780 runs, has errors) ---")
        v1_summary = analyze_stop_patterns(v1_runs)
    if raw_data:
        print("\n--- V2 Data (200 runs, 0 errors) ---")
        v2_summary = analyze_stop_patterns(raw_data)

    # 2. Content pattern analysis (v2 raw data)
    if raw_data:
        content_summary = analyze_content_patterns(raw_data)

    # 3. Task-error interaction (v1 data)
    if v1_runs:
        analyze_task_error_interaction(v1_runs)

    # Save results
    if raw_data and content_summary:
        csv_path = EXP04_DIR / 'content_analysis.csv'
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(content_summary[0].keys()))
            writer.writeheader()
            writer.writerows(content_summary)
        print(f"\n[OK] Saved {csv_path}")

    # v1 error analysis
    if v1_runs:
        # Error rate by pattern and task type
        error_data = []
        for r in v1_runs:
            is_error = r.get('error', '') in ('True', 'true', '1')
            task = r.get('task_id', '')
            task_type = task.split('_')[0] if task else 'unknown'
            error_data.append({
                'pattern': r.get('pattern', ''),
                'category': CATEGORY_MAP.get(r.get('pattern', ''), '?'),
                'task_id': task,
                'task_domain': task_type,
                'error': is_error,
                'stop_reason': r.get('stop_reason', ''),
            })

        csv_path = EXP04_DIR / 'error_analysis_v1.csv'
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(error_data[0].keys()))
            writer.writeheader()
            writer.writerows(error_data)
        print(f"[OK] Saved {csv_path}")

    print("\n[DONE] Error attribution analysis complete")


if __name__ == '__main__':
    main()
