"""
Preliminary Figure: Category A (rr2 vs rr3) comparison
Uses log-parsed data before formal CSV is available.

Output: figures/fig_preliminary_catA.png
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import numpy as np
import csv
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp01')
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')

COLORS = {
    'rr2': '#4C78A8',
    'rr3': '#72B7B2',
    'rr4': '#8B5CF6',  # Purple for later
}


def load_preliminary_data():
    """Load from preliminary CSV."""
    csv_path = RESULTS_DIR / 'preliminary_catA.csv'
    if not csv_path.exists():
        print(f"No data at {csv_path}")
        return []

    runs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['total_duration'] = float(row['total_duration'])
            row['total_tokens_in'] = int(row['total_tokens_in'])
            row['total_tokens_out'] = int(row['total_tokens_out'])
            row['total_tokens'] = int(row['total_tokens'])
            row['sdk_calls'] = int(row['sdk_calls'])
            row['error'] = row['error'] == 'True'
            runs.append(row)
    return runs


def plot_catA_comparison(runs):
    """Create 2x2 comparison plot for rr2 vs rr3."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    by_pattern = defaultdict(list)
    for r in runs:
        if not r['error']:
            by_pattern[r['pattern']].append(r)
    # Include patterns with at least 5 data points
    patterns = [p for p in ['rr2', 'rr3', 'rr4'] if len(by_pattern[p]) >= 5]
    if not patterns:
        print("Not enough data")
        return

    # 1. Duration by pattern
    ax = axes[0, 0]
    data = [[r['total_duration'] for r in by_pattern[p]] for p in patterns]
    bp = ax.boxplot(data, tick_labels=patterns, patch_artist=True)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(COLORS[patterns[i]])
        patch.set_alpha(0.7)
    ax.set_ylabel('Duration (seconds)')
    ax.set_title('Duration per Run')
    # Add means
    for i, d in enumerate(data):
        ax.text(i + 1, max(d) * 1.02, f'mean={np.mean(d):.1f}s',
                ha='center', fontsize=8, color='#666')

    # 2. Total tokens by pattern
    ax = axes[0, 1]
    data = [[r['total_tokens'] for r in by_pattern[p]] for p in patterns]
    bp = ax.boxplot(data, tick_labels=patterns, patch_artist=True)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(COLORS[patterns[i]])
        patch.set_alpha(0.7)
    ax.set_ylabel('Total Tokens')
    ax.set_title('Token Usage per Run')
    for i, d in enumerate(data):
        ax.text(i + 1, max(d) * 1.02, f'mean={np.mean(d):.0f}',
                ha='center', fontsize=8, color='#666')

    # 3. Duration by task category
    ax = axes[1, 0]
    task_cats = ['fact', 'crea', 'anal', 'tech']
    x = np.arange(len(task_cats))
    n_pat = len(patterns)
    width = 0.8 / n_pat
    for i, pattern in enumerate(patterns):
        means = []
        for tc in task_cats:
            tc_runs = [r for r in by_pattern[pattern] if r['task_id'].startswith(tc)]
            means.append(np.mean([r['total_duration'] for r in tc_runs]) if tc_runs else 0)
        ax.bar(x + (i - n_pat/2 + 0.5) * width, means, width, label=pattern,
               color=COLORS[pattern], alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(task_cats)
    ax.set_ylabel('Mean Duration (s)')
    ax.set_title('Duration by Task Category')
    ax.legend()

    # 4. SDK calls distribution
    ax = axes[1, 1]
    for pattern in patterns:
        calls = [r['sdk_calls'] for r in by_pattern[pattern]]
        ax.hist(calls, bins=range(1, max(calls) + 2), alpha=0.6,
                label=pattern, color=COLORS[pattern], edgecolor='white')
    ax.set_xlabel('SDK Calls per Run')
    ax.set_ylabel('Frequency')
    ax.set_title('SDK Call Distribution')
    ax.legend()

    fig.suptitle('Preliminary: Category A (Flat Sequential) Comparison',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = FIGURES_DIR / 'fig_preliminary_catA.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    runs = load_preliminary_data()
    if runs:
        plot_catA_comparison(runs)
        print(f"\n[OK] Plotted {len(runs)} runs")
    else:
        print("No data available")
