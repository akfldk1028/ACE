"""
Figure 5: Experiment 02 - Quality Trajectories
===============================================
Per-turn G-Eval quality scores showing how quality evolves during execution.
Identifies termination regret (gap between actual and optimal stopping).

Reads from: results/exp02/quality_trajectories.csv
Output: figures/fig5_quality_trajectories.png
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp02')
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')

CATEGORY_COLORS = {
    'A': '#4C78A8', 'B1': '#F58518', 'B2': '#EECA3B', 'C': '#E45756', 'D': '#72B7B2'
}
CATEGORY_NAMES = {
    'A': 'Flat Sequential (Chain)', 'B1': 'Centralized Routing (Star)',
    'B2': 'Decentralized Handoff (Mesh)',
    'C': 'Structured Feedback', 'D': 'Composed/Nested'
}


def load_quality_data():
    """Load per-turn quality scores from exp02."""
    # exp02 runner saves as scores.csv
    for fname in ['scores.csv', 'quality_trajectories.csv']:
        csv_path = RESULTS_DIR / fname
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            # Normalize column names
            if 'overall' in df.columns and 'quality_score' not in df.columns:
                df['quality_score'] = df['overall']
            if 'repeat_index' not in df.columns:
                df['repeat_index'] = 0
            # Fix legacy B→B1/B2 categories from v1 data
            cat_remap = {"sel3": "B1", "sel4": "B1", "swm3": "B2", "swm4": "B2"}
            if "pattern" in df.columns:
                df["pattern_category"] = df.apply(
                    lambda r: cat_remap.get(r["pattern"], r.get("pattern_category", "")), axis=1
                )
            print(f"[OK] Loaded {len(df)} rows from {fname}")
            return df
    print(f"[WARN] No data found. Run exp02 first.")
    return None


def plot_quality_trajectories(df):
    """2x2 plot: quality trajectory per category representative."""
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

        # Plot per-task trajectories (light) and mean (bold)
        for _, group in cat_data.groupby(['task_id', 'repeat_index']):
            ax.plot(group['turn_index'], group['quality_score'],
                    color=color, alpha=0.15, linewidth=0.8)

        # Mean trajectory
        mean_traj = cat_data.groupby('turn_index')['quality_score'].mean()
        ax.plot(mean_traj.index, mean_traj.values, color=color,
                linewidth=2.5, label=f'Mean Q(t)')

        # Mark optimal stopping point
        if len(mean_traj) > 0:
            opt_turn = mean_traj.idxmax()
            opt_val = mean_traj.max()
            ax.axvline(x=opt_turn, color='red', linestyle='--', alpha=0.5)
            ax.plot(opt_turn, opt_val, 'r*', markersize=12,
                    label=f'Optimal stop (t={opt_turn})')

        ax.set_xlabel('Agent Turn')
        ax.set_ylabel('Quality Score Q(t)')
        ax.set_title(f'({chr(97+idx)}) {cat_name}', fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    # Hide unused subplot (6th in 2x3 grid)
    if len(CATEGORY_NAMES) < 6:
        axes[1, 2].set_visible(False)

    fig.suptitle('Quality Trajectories: G-Eval Score per Agent Turn',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = FIGURES_DIR / 'fig5_quality_trajectories.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def plot_termination_regret(df):
    """Bar chart of mean termination regret by pattern."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Compute regret per run
    regret_data = []
    for (pattern, task_id, repeat), group in df.groupby(['pattern', 'task_id', 'repeat_index']):
        scores = group.sort_values('turn_index')['quality_score'].values
        if len(scores) < 2:
            continue
        optimal_turn = np.argmax(scores)
        actual_turn = len(scores) - 1
        regret = actual_turn - optimal_turn
        regret_data.append({
            'pattern': pattern,
            'pattern_category': group['pattern_category'].iloc[0],
            'regret': regret,
        })

    if not regret_data:
        print("[WARN] No regret data computed")
        return

    regret_df = pd.DataFrame(regret_data)
    mean_regret = regret_df.groupby('pattern')['regret'].mean().sort_index()
    colors = [CATEGORY_COLORS.get(regret_df[regret_df['pattern']==p]['pattern_category'].iloc[0], '#999')
              for p in mean_regret.index]

    bars = ax.bar(range(len(mean_regret)), mean_regret.values, color=colors, alpha=0.7)
    ax.set_xticks(range(len(mean_regret)))
    ax.set_xticklabels(mean_regret.index, rotation=45)
    ax.set_ylabel('Mean Termination Regret (turns)')
    ax.set_title('Termination Regret by Pattern (positive = over-computation)')
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = FIGURES_DIR / 'fig5b_termination_regret.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    df = load_quality_data()
    if df is not None:
        plot_quality_trajectories(df)
        plot_termination_regret(df)
    else:
        print("Run exp02 first to generate quality trajectory data.")
