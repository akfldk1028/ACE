"""
Figure 4: Experiment 01 Main Results - Pattern Efficiency Comparison
====================================================================
4-panel figure: (a) Duration, (b) Total Tokens, (c) SDK Calls, (d) Tokens per SDK Call
Grouped by 13 patterns across 4 categories with color coding.

Reads from: results/exp01/summary.csv (or preliminary_catA.csv for partial data)
Output: figures/fig4_exp01_main.png
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import csv
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp01')
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')

# Category styling
CATEGORY_META = {
    'A': {'name': 'Flat Sequential (Chain)', 'color': '#4C78A8', 'patterns': ['rr2', 'rr3', 'rr4']},
    'B1': {'name': 'Centralized Routing (Star)', 'color': '#F58518', 'patterns': ['sel3', 'sel4']},
    'B2': {'name': 'Decentralized Handoff (Mesh)', 'color': '#EECA3B', 'patterns': ['swm3', 'swm4']},
    'C': {'name': 'Structured Feedback', 'color': '#E45756', 'patterns': ['refl2', 'refl3', 'debate3', 'debate4']},
    'D': {'name': 'Composed/Nested', 'color': '#72B7B2', 'patterns': ['pipe', 'moa']},
}

PATTERN_CATEGORY = {}
PATTERN_COLOR = {}
for cat_id, meta in CATEGORY_META.items():
    for p in meta['patterns']:
        PATTERN_CATEGORY[p] = cat_id
        PATTERN_COLOR[p] = meta['color']

# Full pattern order
ALL_PATTERNS = ['rr2', 'rr3', 'rr4', 'sel3', 'sel4', 'swm3', 'swm4',
                'refl2', 'refl3', 'debate3', 'debate4', 'pipe', 'moa']


def load_data():
    """Load summary CSV. Try formal first, then preliminary."""
    for fname in ['summary.csv', 'summary_all.csv', 'preliminary_catA.csv']:
        csv_path = RESULTS_DIR / fname
        if csv_path.exists():
            runs = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Handle both formal and preliminary CSV formats
                    if 'error' in row:
                        is_error = row['error'] in ('True', 'true', '1')
                    else:
                        is_error = False

                    if is_error:
                        continue  # Skip error runs

                    run = {
                        'pattern': row.get('pattern', ''),
                        'task_id': row.get('task_id', ''),
                    }

                    # Duration
                    for key in ['duration_sec', 'total_duration']:
                        if key in row and row[key]:
                            run['duration'] = float(row[key])
                            break

                    # Total tokens
                    for key in ['total_tokens']:
                        if key in row and row[key]:
                            run['total_tokens'] = int(row[key])

                    # Tokens in/out
                    for key in ['total_tokens_in']:
                        if key in row and row[key]:
                            run['tokens_in'] = int(row[key])
                    for key in ['total_tokens_out']:
                        if key in row and row[key]:
                            run['tokens_out'] = int(row[key])

                    # SDK calls / turn count
                    for key in ['sdk_calls', 'turn_count']:
                        if key in row and row[key]:
                            run['sdk_calls'] = int(row[key])
                            break

                    runs.append(run)

            print(f"[OK] Loaded {len(runs)} runs from {csv_path.name}")
            return runs
    return []


def plot_main_figure(runs):
    """Create 4-panel main results figure."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    # Group by pattern
    by_pattern = defaultdict(list)
    for r in runs:
        by_pattern[r['pattern']].append(r)

    # Only plot patterns that have data
    patterns = [p for p in ALL_PATTERNS if p in by_pattern]
    if not patterns:
        print("[WARN] No pattern data found")
        return

    n = len(patterns)
    colors = [PATTERN_COLOR.get(p, '#999') for p in patterns]

    # --- Panel (a): Duration ---
    ax = axes[0, 0]
    data = [[r['duration'] for r in by_pattern[p] if 'duration' in r] for p in patterns]
    data = [d if d else [0] for d in data]
    bp = ax.boxplot(data, tick_labels=patterns, patch_artist=True, widths=0.6)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i])
        patch.set_alpha(0.7)
    ax.set_ylabel('Duration (seconds)', fontsize=11)
    ax.set_title('(a) Execution Duration', fontsize=12, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    # Add mean markers
    for i, d in enumerate(data):
        if d and d != [0]:
            ax.plot(i + 1, np.mean(d), 'D', color='black', markersize=4, zorder=5)

    # --- Panel (b): Total Tokens ---
    ax = axes[0, 1]
    data = [[r['total_tokens'] for r in by_pattern[p] if 'total_tokens' in r] for p in patterns]
    data = [d if d else [0] for d in data]
    bp = ax.boxplot(data, tick_labels=patterns, patch_artist=True, widths=0.6)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i])
        patch.set_alpha(0.7)
    ax.set_ylabel('Total Tokens', fontsize=11)
    ax.set_title('(b) Token Consumption', fontsize=12, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    for i, d in enumerate(data):
        if d and d != [0]:
            ax.plot(i + 1, np.mean(d), 'D', color='black', markersize=4, zorder=5)

    # --- Panel (c): SDK Calls ---
    ax = axes[1, 0]
    data = [[r['sdk_calls'] for r in by_pattern[p] if 'sdk_calls' in r] for p in patterns]
    data = [d if d else [0] for d in data]
    bp = ax.boxplot(data, tick_labels=patterns, patch_artist=True, widths=0.6)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i])
        patch.set_alpha(0.7)
    ax.set_ylabel('LLM Calls per Run', fontsize=11)
    ax.set_title('(c) LLM Call Count', fontsize=12, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    for i, d in enumerate(data):
        if d and d != [0]:
            ax.plot(i + 1, np.mean(d), 'D', color='black', markersize=4, zorder=5)

    # --- Panel (d): Tokens per SDK Call (efficiency) ---
    ax = axes[1, 1]
    data = []
    for p in patterns:
        ratios = []
        for r in by_pattern[p]:
            if 'tokens_out' in r and 'sdk_calls' in r and r['sdk_calls'] > 0:
                ratios.append(r['tokens_out'] / r['sdk_calls'])
        data.append(ratios if ratios else [0])

    bp = ax.boxplot(data, tick_labels=patterns, patch_artist=True, widths=0.6)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i])
        patch.set_alpha(0.7)
    ax.set_ylabel('Output Tokens / LLM Call', fontsize=11)
    ax.set_title('(d) Per-Call Output Efficiency', fontsize=12, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    for i, d in enumerate(data):
        if d and d != [0]:
            ax.plot(i + 1, np.mean(d), 'D', color='black', markersize=4, zorder=5)

    # Category legend
    legend_patches = []
    for cat_id, meta in CATEGORY_META.items():
        if any(p in by_pattern for p in meta['patterns']):
            legend_patches.append(
                mpatches.Patch(color=meta['color'], alpha=0.7,
                               label=f"Cat {cat_id}: {meta['name']}")
            )
    legend_patches.append(
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='black',
                   markersize=5, label='Mean')
    )
    fig.legend(handles=legend_patches, loc='upper center',
               bbox_to_anchor=(0.5, 0.99), ncol=len(legend_patches),
               fontsize=10, frameon=True, fancybox=True)

    fig.suptitle('Experiment 01: Pattern Efficiency Across Coordination Topologies',
                 fontsize=14, fontweight='bold', y=1.03)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    output_path = FIGURES_DIR / 'fig4_exp01_main.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")

    # Hi-res version
    output_hires = FIGURES_DIR / 'fig4_exp01_main_hires.png'
    plt.savefig(output_hires, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_hires}")
    plt.close()


def plot_task_category_heatmap(runs):
    """Create heatmap: pattern x task_category for duration and tokens."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    by_pattern = defaultdict(list)
    for r in runs:
        by_pattern[r['pattern']].append(r)

    patterns = [p for p in ALL_PATTERNS if p in by_pattern]
    task_cats = sorted(set(r['task_id'].split('_')[0] for r in runs))

    for idx, (metric, label) in enumerate([('duration', 'Mean Duration (s)'),
                                            ('total_tokens', 'Mean Total Tokens')]):
        ax = axes[idx]
        matrix = []
        for p in patterns:
            row = []
            for tc in task_cats:
                vals = [r[metric] for r in by_pattern[p]
                        if r['task_id'].startswith(tc) and metric in r]
                row.append(np.mean(vals) if vals else 0)
            matrix.append(row)

        matrix = np.array(matrix)
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(task_cats)))
        ax.set_xticklabels(task_cats)
        ax.set_yticks(range(len(patterns)))
        ax.set_yticklabels(patterns)
        ax.set_title(label, fontsize=12, fontweight='bold')

        # Add text annotations
        for i in range(len(patterns)):
            for j in range(len(task_cats)):
                val = matrix[i, j]
                if val > 0:
                    fmt = f'{val:.0f}' if metric == 'total_tokens' else f'{val:.0f}s'
                    color = 'white' if val > matrix.max() * 0.6 else 'black'
                    ax.text(j, i, fmt, ha='center', va='center',
                            fontsize=8, color=color)

        plt.colorbar(im, ax=ax, shrink=0.8)

    fig.suptitle('Pattern x Task Category Interaction',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    output_path = FIGURES_DIR / 'fig4b_task_heatmap.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    runs = load_data()
    if runs:
        plot_main_figure(runs)
        plot_task_category_heatmap(runs)
        print(f"\n[OK] Plotted {len(runs)} successful runs across {len(set(r['pattern'] for r in runs))} patterns")
    else:
        print("No data available. Run exp01 first.")
