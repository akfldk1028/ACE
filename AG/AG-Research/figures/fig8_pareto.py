"""
Figure 8: Experiment 05 - Adaptive Termination Pareto Frontier
===============================================================
Shows quality vs cost tradeoff for different lambda values,
comparing adaptive termination against fixed baselines.

Reads from: results/exp05/summary.csv
Output: figures/fig8_pareto.png
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from pathlib import Path

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp05')
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')

CATEGORY_COLORS = {
    'A': '#4C78A8', 'B1': '#F58518', 'B2': '#EECA3B', 'C': '#E45756', 'D': '#72B7B2'
}
PATTERN_CATEGORY = {
    'rr2': 'A', 'rr3': 'A', 'rr4': 'A',
    'sel3': 'B1', 'sel4': 'B1', 'swm3': 'B2', 'swm4': 'B2',
    'refl2': 'C', 'refl3': 'C', 'debate3': 'C', 'debate4': 'C',
    'pipe': 'D', 'moa': 'D',
}
LAMBDA_MARKERS = {
    0.0: 'o',    # baseline (fixed)
    0.1: 's',
    0.3: '^',
    0.5: 'D',
    0.7: 'v',
    0.9: 'P',
}


def load_adaptive_data():
    csv_path = RESULTS_DIR / "summary.csv"
    if not csv_path.exists():
        print(f"[WARN] No data at {csv_path}. Run exp05 first.")
        return None
    df = pd.read_csv(csv_path)

    # Parse lambda from experiment_id: "exp05_baseline" -> 0.0, "exp05_adaptive_l0.1" -> 0.1
    def parse_lambda(exp_id):
        if 'baseline' in str(exp_id):
            return 0.0
        if '_l' in str(exp_id):
            try:
                return float(str(exp_id).split('_l')[-1])
            except ValueError:
                return -1
        return -1

    if 'lambda_value' not in df.columns:
        df['lambda_value'] = df['experiment_id'].apply(parse_lambda)

    # Also add quality_score if missing (use 0 placeholder)
    if 'quality_score' not in df.columns:
        df['quality_score'] = 0.0

    print(f"[OK] Loaded {len(df)} rows, lambda values: {sorted(df['lambda_value'].unique())}")
    return df


def plot_pareto_frontier(df):
    """Main Pareto plot: quality vs cost, colored by pattern category."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    categories = ['A', 'B1', 'B2', 'C', 'D']
    cat_names = {
        'A': 'Flat Sequential (Chain)', 'B1': 'Centralized Routing (Star)',
        'B2': 'Decentralized Handoff (Mesh)',
        'C': 'Structured Feedback', 'D': 'Composed/Nested'
    }

    for idx, cat in enumerate(categories):
        ax = axes[idx // 3, idx % 3]
        color = CATEGORY_COLORS[cat]

        cat_data = df[df['pattern_category'] == cat]
        if cat_data.empty:
            ax.text(0.5, 0.5, f'No data for Category {cat}',
                    transform=ax.transAxes, ha='center', va='center')
            ax.set_title(f'({chr(97+idx)}) {cat_names[cat]}', fontweight='bold')
            continue

        # Group by lambda and compute mean quality/cost
        for lam in sorted(cat_data['lambda_value'].unique()):
            lam_data = cat_data[cat_data['lambda_value'] == lam]
            mean_quality = lam_data['quality_score'].mean()
            mean_cost = lam_data['total_tokens'].mean()

            marker = LAMBDA_MARKERS.get(lam, 'o')
            label = f'lambda={lam}' if lam > 0 else 'Fixed baseline'
            ax.scatter(mean_cost, mean_quality, marker=marker, s=80,
                       color=color, edgecolors='black', linewidth=0.5,
                       label=label, zorder=5)

        # Connect Pareto-optimal points
        pareto_points = []
        for lam in sorted(cat_data['lambda_value'].unique()):
            lam_data = cat_data[cat_data['lambda_value'] == lam]
            pareto_points.append((lam_data['total_tokens'].mean(),
                                  lam_data['quality_score'].mean()))

        pareto_points.sort(key=lambda p: p[0])
        if len(pareto_points) > 1:
            px, py = zip(*pareto_points)
            ax.plot(px, py, '--', color=color, alpha=0.4, linewidth=1)

        ax.set_xlabel('Mean Total Tokens (cost)')
        ax.set_ylabel('Mean Quality Score')
        ax.set_title(f'({chr(97+idx)}) {cat_names[cat]}', fontsize=12, fontweight='bold')
        ax.legend(fontsize=7, loc='lower right')
        ax.grid(True, alpha=0.3)

    # Hide unused subplot (6th in 2x3 grid)
    if len(categories) < 6:
        axes[1, 2].set_visible(False)

    fig.suptitle('Adaptive Termination: Quality-Cost Pareto Frontier',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = FIGURES_DIR / 'fig8_pareto.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def plot_cost_reduction(df):
    """Bar chart: cost reduction percentage by pattern at iso-quality."""
    fig, ax = plt.subplots(figsize=(12, 6))

    patterns = sorted(df['pattern'].unique(),
                      key=lambda p: (PATTERN_CATEGORY.get(p, 'Z'), p))

    reductions = []
    colors_list = []
    for pattern in patterns:
        p_data = df[df['pattern'] == pattern]
        baseline = p_data[p_data['lambda_value'] == 0.0]['total_tokens'].mean()
        if baseline == 0 or np.isnan(baseline):
            reductions.append(0)
        else:
            # Find best adaptive lambda with quality >= 95% of baseline
            baseline_quality = p_data[p_data['lambda_value'] == 0.0]['quality_score'].mean()
            quality_threshold = baseline_quality * 0.95

            best_saving = 0
            for lam in p_data['lambda_value'].unique():
                if lam == 0.0:
                    continue
                lam_data = p_data[p_data['lambda_value'] == lam]
                if lam_data['quality_score'].mean() >= quality_threshold:
                    saving = (1 - lam_data['total_tokens'].mean() / baseline) * 100
                    best_saving = max(best_saving, saving)
            reductions.append(best_saving)

        colors_list.append(CATEGORY_COLORS.get(PATTERN_CATEGORY.get(pattern, 'A'), '#999'))

    ax.bar(range(len(patterns)), reductions, color=colors_list, alpha=0.7)
    ax.set_xticks(range(len(patterns)))
    ax.set_xticklabels(patterns, rotation=45)
    ax.set_ylabel('Token Cost Reduction (%)')
    ax.set_title('Cost Reduction from Adaptive Termination (at >=95% baseline quality)',
                 fontsize=12, fontweight='bold')
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = FIGURES_DIR / 'fig8b_cost_reduction.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    df = load_adaptive_data()
    if df is not None:
        plot_pareto_frontier(df)
        plot_cost_reduction(df)
    else:
        print("Run exp05 first to generate adaptive termination data.")
