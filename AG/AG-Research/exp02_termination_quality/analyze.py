"""
Experiment 02 Analysis: Termination Quality
============================================
- Quality curves Q(t) per pattern (category-colored)
- Optimal stop point vs actual stop point
- Overshoot analysis
- Category D (Composed) step-function quality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import CATEGORY_NAMES, CATEGORY_COLORS, PATTERN_CATEGORY, RESULTS_DIR

INPUT_DIR = RESULTS_DIR / "exp02"
PLOTS_DIR = INPUT_DIR / "plots"


def load_data():
    scores_path = INPUT_DIR / "scores.csv"
    summary_path = INPUT_DIR / "summary.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"No scores at {scores_path}. Run exp02 first.")
    scores = pd.read_csv(scores_path)
    summary = pd.read_csv(summary_path) if summary_path.exists() else None
    return scores, summary


def plot_quality_curves(scores: pd.DataFrame):
    """Quality curve Q(t) per pattern, colored by category."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    patterns = scores["pattern"].unique()
    for pattern in sorted(patterns, key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p)):
        cat = PATTERN_CATEGORY.get(pattern, "?")
        color = CATEGORY_COLORS.get(cat, "#999999")
        sub = scores[scores["pattern"] == pattern]

        # Average quality across tasks at each relative turn position
        grouped = sub.groupby("turn_index")["overall"].mean()
        ax.plot(grouped.index, grouped.values, color=color, alpha=0.7,
                label=f"{pattern} ({cat})", marker="o", markersize=3)

    ax.set_title("Quality Curve Q(t) by Pattern")
    ax.set_xlabel("Turn Index")
    ax.set_ylabel("Overall Quality (1-5)")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.set_ylim(0.5, 5.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "quality_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Saved: quality_curves.png")


def plot_overshoot(scores: pd.DataFrame, summary: pd.DataFrame):
    """Overshoot = actual_stop - optimal_stop per pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    overshoot_data = []

    for (pattern, task_id), group in scores.groupby(["pattern", "task_id"]):
        overall = group.sort_values("turn_index")["overall"].values
        if len(overall) == 0:
            continue

        optimal_stop = int(np.argmax(overall))
        actual_stop = len(overall) - 1
        overshoot = actual_stop - optimal_stop

        overshoot_data.append({
            "pattern": pattern,
            "pattern_category": PATTERN_CATEGORY.get(pattern, "?"),
            "task_id": task_id,
            "optimal_stop": optimal_stop,
            "actual_stop": actual_stop,
            "overshoot": overshoot,
            "peak_quality": float(np.max(overall)),
            "final_quality": float(overall[-1]),
        })

    if not overshoot_data:
        print("  No overshoot data to plot")
        return

    ov_df = pd.DataFrame(overshoot_data)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Box plot: overshoot by pattern
    order = sorted(ov_df["pattern"].unique(), key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    palette = {p: CATEGORY_COLORS[PATTERN_CATEGORY.get(p, "A")] for p in order}
    sns.boxplot(data=ov_df, x="pattern", y="overshoot", order=order, palette=palette, ax=axes[0])
    axes[0].set_title("Overshoot by Pattern")
    axes[0].set_ylabel("Overshoot (turns)")
    axes[0].tick_params(axis="x", rotation=45)

    # Box plot: overshoot by category
    cat_order = ["A", "B1", "B2", "C", "D"]
    colors = [CATEGORY_COLORS[c] for c in cat_order]
    cat_data = [ov_df[ov_df["pattern_category"] == c]["overshoot"].dropna() for c in cat_order]
    bp = axes[1].boxplot(
        [d for d in cat_data if len(d) > 0],
        tick_labels=[f"{c}: {CATEGORY_NAMES[c]}" for c, d in zip(cat_order, cat_data) if len(d) > 0],
        patch_artist=True,
    )
    for i, patch in enumerate(bp["boxes"]):
        idx = [j for j, d in enumerate(cat_data) if len(d) > 0][i]
        patch.set_facecolor(colors[idx])
        patch.set_alpha(0.7)
    axes[1].set_title("Overshoot by Category")
    axes[1].set_ylabel("Overshoot (turns)")

    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "overshoot.png", dpi=150)
    plt.close(fig)
    print("  Saved: overshoot.png")

    # Save overshoot stats
    ov_stats = ov_df.groupby("pattern").agg(
        category=("pattern_category", "first"),
        mean_overshoot=("overshoot", "mean"),
        mean_peak=("peak_quality", "mean"),
        mean_final=("final_quality", "mean"),
    ).round(2)

    stats_path = INPUT_DIR / "overshoot_stats.md"
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write("# Overshoot Analysis\n\n")
        f.write(ov_stats.to_markdown())
    print("  Saved: overshoot_stats.md")


def plot_quality_by_category(scores: pd.DataFrame):
    """Compare final quality across categories."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Get final turn score per pattern × task
    final_scores = scores.sort_values("turn_index").groupby(["pattern", "task_id"]).last().reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    cat_order = ["A", "B1", "B2", "C", "D"]
    colors = [CATEGORY_COLORS[c] for c in cat_order]

    cat_data = [final_scores[final_scores["pattern_category"] == c]["overall"].dropna() for c in cat_order]
    bp = ax.boxplot(
        [d for d in cat_data if len(d) > 0],
        tick_labels=[f"{c}: {CATEGORY_NAMES[c]}" for c, d in zip(cat_order, cat_data) if len(d) > 0],
        patch_artist=True,
    )
    for i, patch in enumerate(bp["boxes"]):
        idx = [j for j, d in enumerate(cat_data) if len(d) > 0][i]
        patch.set_facecolor(colors[idx])
        patch.set_alpha(0.7)

    ax.set_title("Final Quality Score by Category")
    ax.set_ylabel("Overall Quality (1-5)")
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "quality_by_category.png", dpi=150)
    plt.close(fig)
    print("  Saved: quality_by_category.png")


def analyze():
    """Run all exp02 analyses."""
    print("Exp02 Analysis")
    print("-" * 40)

    scores, summary = load_data()
    print(f"  Loaded {len(scores)} score rows")

    plot_quality_curves(scores)
    if summary is not None:
        plot_overshoot(scores, summary)
    plot_quality_by_category(scores)

    print("\nExp02 analysis complete.")


if __name__ == "__main__":
    analyze()
