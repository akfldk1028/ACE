"""
Figure 6: Experiment 03 - Convergence Detection
================================================
Shows convergence curves (word overlap similarity) per category,
with KS-test thresholds and convergence points marked.

Reads from: results/exp03/convergence_data.csv
Output: figures/fig6_convergence.png
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from pathlib import Path

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp03')
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')

CATEGORY_COLORS = {
    'A': '#4C78A8', 'B1': '#F58518', 'B2': '#EECA3B', 'C': '#E45756', 'D': '#72B7B2'
}
CATEGORY_NAMES = {
    'A': 'Flat Sequential (Chain)', 'B1': 'Centralized Routing (Star)',
    'B2': 'Decentralized Handoff (Mesh)',
    'C': 'Structured Feedback', 'D': 'Composed/Nested'
}
PATTERN_CATEGORY = {
    'rr2': 'A', 'rr3': 'A', 'rr4': 'A',
    'sel3': 'B1', 'sel4': 'B1', 'swm3': 'B2', 'swm4': 'B2',
    'refl2': 'C', 'refl3': 'C', 'debate3': 'C', 'debate4': 'C',
    'pipe': 'D', 'moa': 'D',
}


def load_convergence_data():
    csv_path = RESULTS_DIR / "convergence_data.csv"
    if not csv_path.exists():
        print(f"[WARN] No data at {csv_path}. Run exp03 analysis first.")
        return None
    return pd.read_csv(csv_path)


def plot_convergence_by_category(df):
    """2x2 plot: convergence curves per category with threshold line."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    for idx, (cat, cat_name) in enumerate(CATEGORY_NAMES.items()):
        ax = axes[idx // 3, idx % 3]
        color = CATEGORY_COLORS[cat]

        cat_data = df[df['pattern_category'] == cat]
        if cat_data.empty:
            ax.text(0.5, 0.5, f'No data for Category {cat}',
                    transform=ax.transAxes, ha='center', va='center')
            ax.set_title(f'({chr(97+idx)}) {cat_name}', fontweight='bold')
            continue

        # Plot per-pattern curves
        for pattern in sorted(cat_data['pattern'].unique()):
            p_data = cat_data[cat_data['pattern'] == pattern]
            mean_sim = p_data.groupby('turn_pair')['similarity'].mean()
            ax.plot(mean_sim.index, mean_sim.values, 'o-', color=color,
                    alpha=0.6, markersize=3, label=pattern)

        # Convergence threshold
        ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax.text(ax.get_xlim()[1] * 0.95, 0.52, 'theta=0.5', ha='right',
                color='red', fontsize=8, alpha=0.7)

        ax.set_xlabel('Turn Pair Index')
        ax.set_ylabel('Word Overlap Similarity')
        ax.set_title(f'({chr(97+idx)}) {cat_name}', fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # Hide unused subplot (6th in 2x3 grid)
    if len(CATEGORY_NAMES) < 6:
        axes[1, 2].set_visible(False)

    fig.suptitle('Convergence Detection: Claim Similarity Between Consecutive Turns',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = FIGURES_DIR / 'fig6_convergence.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def plot_convergence_speed_comparison(df):
    """Box plot comparing convergence speed across categories."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get convergence point per run
    conv_points = df.groupby(['pattern', 'pattern_category', 'task_id', 'repeat_index']).agg(
        converged_at=('converged_at', 'first')
    ).reset_index()

    cats = ['A', 'B1', 'B2', 'C', 'D']
    cat_data = []
    valid_cats = []
    colors_list = []

    for cat in cats:
        data = conv_points[conv_points['pattern_category'] == cat]['converged_at'].dropna()
        if len(data) > 0:
            cat_data.append(data.values)
            valid_cats.append(cat)
            colors_list.append(CATEGORY_COLORS[cat])

    if not valid_cats:
        print("[WARN] No convergence data for comparison")
        return

    bp = ax.boxplot(cat_data, tick_labels=[f'{c}: {CATEGORY_NAMES[c]}' for c in valid_cats],
                    patch_artist=True, widths=0.6)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors_list[i])
        patch.set_alpha(0.7)

    ax.set_ylabel('Turn Pair Index at Convergence')
    ax.set_title('Convergence Speed by Category (lower = faster convergence)',
                 fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = FIGURES_DIR / 'fig6b_convergence_speed.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    df = load_convergence_data()
    if df is not None:
        plot_convergence_by_category(df)
        plot_convergence_speed_comparison(df)
    else:
        print("Run exp03 analysis first to generate convergence data.")
