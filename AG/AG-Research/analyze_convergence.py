"""
Experiment 03: Convergence Detection Analysis
=============================================
Analyzes turn-by-turn content from exp01 raw data to detect convergence signals.
Uses text similarity (Jaccard on n-grams) between consecutive turns as a proxy
for semantic convergence. No embeddings needed.

Reads: results/exp01/raw.json (v2, 200 runs, 8 patterns)
       results/exp01/raw_A_B1_B2_C_D.json (v1 merged, fallback)
Output: results/exp03/convergence_analysis.csv
        results/exp03/convergence_summary.csv
        figures/fig_convergence.png
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
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
EXP01_DIR = RESULTS_DIR / 'exp01'
EXP03_DIR = RESULTS_DIR / 'exp03'
EXP03_DIR.mkdir(exist_ok=True)

# Category mapping
CATEGORY_MAP = {
    'rr2': 'A', 'rr3': 'A', 'rr4': 'A',
    'sel3': 'B1', 'sel4': 'B1',
    'swm3': 'B2', 'swm4': 'B2',
    'refl2': 'C', 'refl3': 'C', 'debate3': 'C', 'debate4': 'C',
    'pipe': 'D', 'moa': 'D',
}


def get_ngrams(text, n=3):
    """Extract character n-grams from text."""
    text = re.sub(r'\s+', ' ', text.lower().strip())
    words = text.split()
    if len(words) < n:
        return set(tuple(words))
    return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))


def jaccard_similarity(set_a, set_b):
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def content_overlap_ratio(text_a, text_b):
    """Compute content overlap using shared unique words."""
    words_a = set(re.findall(r'\w+', text_a.lower()))
    words_b = set(re.findall(r'\w+', text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def analyze_run_convergence(run):
    """Analyze convergence for a single run."""
    turns = run.get('turns', [])
    # Filter to agent turns only (exclude user)
    agent_turns = [t for t in turns if t.get('source', '') != 'user' and t.get('content')]

    if len(agent_turns) < 2:
        return None

    # Compute pairwise similarity between consecutive turns
    similarities = []
    for i in range(1, len(agent_turns)):
        content_prev = agent_turns[i-1].get('content', '')
        content_curr = agent_turns[i].get('content', '')

        # Jaccard on 3-grams
        sim_jaccard = jaccard_similarity(get_ngrams(content_prev), get_ngrams(content_curr))
        # Word overlap
        sim_overlap = content_overlap_ratio(content_prev, content_curr)
        # Average
        sim_avg = (sim_jaccard + sim_overlap) / 2

        similarities.append({
            'turn': i + 1,  # 1-indexed for the second turn in comparison
            'jaccard': sim_jaccard,
            'overlap': sim_overlap,
            'avg_sim': sim_avg,
        })

    if not similarities:
        return None

    # Detect convergence point: first turn where similarity exceeds threshold
    # for 2 consecutive comparisons (if available)
    THRESHOLD = 0.25  # Moderate threshold for content convergence
    converged_at = None
    for i in range(len(similarities)):
        if similarities[i]['avg_sim'] >= THRESHOLD:
            if i + 1 < len(similarities) and similarities[i+1]['avg_sim'] >= THRESHOLD:
                converged_at = similarities[i]['turn']
                break
            elif i == len(similarities) - 1:
                # Last comparison, count as converged if above threshold
                converged_at = similarities[i]['turn']

    # Compute convergence metrics
    final_sim = similarities[-1]['avg_sim']
    max_sim = max(s['avg_sim'] for s in similarities)
    mean_sim = statistics.mean(s['avg_sim'] for s in similarities)

    # Check if similarity is increasing (monotonic trend)
    if len(similarities) >= 2:
        trend = similarities[-1]['avg_sim'] - similarities[0]['avg_sim']
    else:
        trend = 0

    return {
        'pattern': run['pattern'],
        'category': CATEGORY_MAP.get(run['pattern'], '?'),
        'task_id': run['task_id'],
        'agent_turns': len(agent_turns),
        'comparisons': len(similarities),
        'converged_at': converged_at,
        'converged': converged_at is not None,
        'final_similarity': final_sim,
        'max_similarity': max_sim,
        'mean_similarity': mean_sim,
        'trend': trend,
        'similarities': similarities,
    }


def load_raw_data():
    """Load raw JSON data."""
    for fname in ['raw.json', 'raw_A_B1_B2_C_D.json']:
        path = EXP01_DIR / fname
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[OK] Loaded {len(data)} runs from {fname}")
            return data
    return []


def main():
    data = load_raw_data()
    if not data:
        print("[ERROR] No raw data found")
        return

    # Analyze each run
    results = []
    for run in data:
        if run.get('error'):
            continue
        r = analyze_run_convergence(run)
        if r:
            results.append(r)

    print(f"[OK] Analyzed {len(results)} runs")

    # Save detailed results
    csv_path = EXP03_DIR / 'convergence_analysis.csv'
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'pattern', 'category', 'task_id', 'agent_turns', 'comparisons',
            'converged', 'converged_at', 'final_similarity', 'max_similarity',
            'mean_similarity', 'trend'
        ])
        writer.writeheader()
        for r in results:
            row = {k: v for k, v in r.items() if k != 'similarities'}
            writer.writerow(row)
    print(f"[OK] Saved {csv_path}")

    # Summary by pattern
    by_pattern = defaultdict(list)
    for r in results:
        by_pattern[r['pattern']].append(r)

    print("\n=== Convergence Summary by Pattern ===")
    print(f"{'Pattern':<10} {'Cat':<4} {'N':>4} {'Conv%':>6} {'MeanSim':>8} {'FinalSim':>9} {'ConvTurn':>9} {'Trend':>7}")
    print("-" * 65)

    summary_rows = []
    pattern_order = ['rr3', 'sel3', 'sel4', 'swm3', 'swm4', 'refl2', 'debate3', 'pipe']
    for p in pattern_order:
        if p not in by_pattern:
            continue
        runs = by_pattern[p]
        n = len(runs)
        conv_count = sum(1 for r in runs if r['converged'])
        conv_pct = conv_count / n * 100 if n else 0
        mean_sim = statistics.mean(r['mean_similarity'] for r in runs)
        final_sim = statistics.mean(r['final_similarity'] for r in runs)
        conv_turns = [r['converged_at'] for r in runs if r['converged_at'] is not None]
        avg_conv_turn = statistics.mean(conv_turns) if conv_turns else None
        trend = statistics.mean(r['trend'] for r in runs)

        cat = CATEGORY_MAP.get(p, '?')
        conv_turn_str = f"{avg_conv_turn:.1f}" if avg_conv_turn else "N/A"

        print(f"{p:<10} {cat:<4} {n:>4} {conv_pct:>5.1f}% {mean_sim:>8.3f} {final_sim:>9.3f} {conv_turn_str:>9} {trend:>+7.3f}")

        summary_rows.append({
            'pattern': p,
            'category': cat,
            'n_runs': n,
            'convergence_rate': f"{conv_pct:.1f}%",
            'mean_similarity': f"{mean_sim:.3f}",
            'final_similarity': f"{final_sim:.3f}",
            'avg_convergence_turn': conv_turn_str,
            'trend': f"{trend:+.3f}",
        })

    # Save summary
    summary_path = EXP03_DIR / 'convergence_summary.csv'
    with open(summary_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\n[OK] Saved {summary_path}")

    # Summary by category
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r['category']].append(r)

    print("\n=== Convergence Summary by Category ===")
    for cat in ['A', 'B1', 'B2', 'C', 'D']:
        if cat not in by_cat:
            continue
        runs = by_cat[cat]
        conv_count = sum(1 for r in runs if r['converged'])
        conv_pct = conv_count / len(runs) * 100
        mean_sim = statistics.mean(r['mean_similarity'] for r in runs)
        print(f"  {cat}: {len(runs)} runs, {conv_pct:.1f}% converged, mean_sim={mean_sim:.3f}")

    # Generate figure
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        colors = {
            'A': '#4C78A8', 'B1': '#F58518', 'B2': '#EECA3B',
            'C': '#E45756', 'D': '#72B7B2'
        }

        # Panel 1: Convergence rate by pattern
        ax = axes[0]
        patterns = pattern_order
        conv_rates = []
        bar_colors = []
        for p in patterns:
            if p in by_pattern:
                runs = by_pattern[p]
                rate = sum(1 for r in runs if r['converged']) / len(runs) * 100
                conv_rates.append(rate)
                bar_colors.append(colors.get(CATEGORY_MAP.get(p, 'A'), '#999'))
            else:
                conv_rates.append(0)
                bar_colors.append('#999')

        ax.bar(range(len(patterns)), conv_rates, color=bar_colors, alpha=0.7)
        ax.set_xticks(range(len(patterns)))
        ax.set_xticklabels(patterns, rotation=45)
        ax.set_ylabel('Convergence Rate (%)')
        ax.set_title('(a) Content Convergence Rate by Pattern')
        ax.set_ylim(0, 105)

        # Panel 2: Mean similarity by pattern
        ax = axes[1]
        mean_sims = []
        final_sims = []
        for p in patterns:
            if p in by_pattern:
                runs = by_pattern[p]
                mean_sims.append(statistics.mean(r['mean_similarity'] for r in runs))
                final_sims.append(statistics.mean(r['final_similarity'] for r in runs))
            else:
                mean_sims.append(0)
                final_sims.append(0)

        x = np.arange(len(patterns))
        ax.bar(x - 0.15, mean_sims, 0.3, label='Mean', color=[colors.get(CATEGORY_MAP.get(p, 'A'), '#999') for p in patterns], alpha=0.5)
        ax.bar(x + 0.15, final_sims, 0.3, label='Final', color=[colors.get(CATEGORY_MAP.get(p, 'A'), '#999') for p in patterns], alpha=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels(patterns, rotation=45)
        ax.set_ylabel('Content Similarity')
        ax.set_title('(b) Mean vs Final Turn Similarity')
        ax.legend()

        # Panel 3: Similarity trend (positive = converging)
        ax = axes[2]
        trends = []
        for p in patterns:
            if p in by_pattern:
                trends.append(statistics.mean(r['trend'] for r in by_pattern[p]))
            else:
                trends.append(0)

        bar_cols = ['green' if t > 0 else 'red' for t in trends]
        ax.bar(range(len(patterns)), trends, color=bar_cols, alpha=0.7)
        ax.set_xticks(range(len(patterns)))
        ax.set_xticklabels(patterns, rotation=45)
        ax.set_ylabel('Similarity Trend (Δ first→last)')
        ax.set_title('(c) Convergence Trend by Pattern')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)

        plt.suptitle('Experiment 03: Content Convergence Detection', fontsize=14, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.93])

        fig_path = FIGURES_DIR / 'fig_convergence_analysis.png'
        plt.savefig(fig_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"[OK] Saved {fig_path}")
        plt.close()
    except Exception as e:
        print(f"[WARN] Figure generation failed: {e}")


if __name__ == '__main__':
    main()
