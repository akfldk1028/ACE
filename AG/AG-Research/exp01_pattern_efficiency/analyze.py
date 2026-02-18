"""
Experiment 01 Analysis: Pattern Efficiency
==========================================
- Category-level comparison (A vs B vs C vs D)
- Within-category agent count effect
- agent_count vs turn_count correlation
- Topology vs termination efficiency
- Heatmap: pattern × task_category
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

from config import (
    CATEGORY_NAMES,
    CATEGORY_COLORS,
    PATTERN_CATEGORY,
    RESULTS_DIR,
)

INPUT_DIR = RESULTS_DIR / "exp01"
PLOTS_DIR = INPUT_DIR / "plots"


def load_data() -> pd.DataFrame:
    csv_path = INPUT_DIR / "summary.csv"
    if not csv_path.exists():
        csv_path = INPUT_DIR / "summary_all.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No data at {csv_path}. Run exp01 first.")
    df = pd.read_csv(csv_path)
    df["task_category"] = df["task_id"].str.split("_").str[0]
    return df


def plot_box_by_pattern(df: pd.DataFrame):
    """Box plots: duration, turn_count, tokens grouped by pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics = [
        ("duration_sec", "Duration (seconds)"),
        ("turn_count", "Turn Count"),
        ("agent_turn_count", "Agent Turn Count"),
        ("total_tokens", "Total Tokens"),
        ("total_tokens_in", "Input Tokens"),
        ("total_tokens_out", "Output Tokens"),
    ]

    for col, label in metrics:
        fig, ax = plt.subplots(figsize=(14, 6))

        # Color by category
        palette = {p: CATEGORY_COLORS[PATTERN_CATEGORY[p]] for p in df["pattern"].unique()}
        order = sorted(df["pattern"].unique(), key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))

        sns.boxplot(data=df, x="pattern", y=col, order=order, palette=palette, ax=ax)
        ax.set_title(f"Exp01: {label} by Pattern")
        ax.set_xlabel("Pattern")
        ax.set_ylabel(label)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        fig.savefig(PLOTS_DIR / f"box_{col}.png", dpi=150)
        plt.close(fig)
        print(f"  Saved: box_{col}.png")


def plot_category_comparison(df: pd.DataFrame):
    """Compare categories A/B/C/D on key metrics."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    metrics = [
        ("duration_sec", "Duration (s)"),
        ("turn_count", "Turn Count"),
        ("agent_turn_count", "Agent Turn Count"),
    ]

    cat_order = ["A", "B1", "B2", "C", "D"]
    colors = [CATEGORY_COLORS[c] for c in cat_order]

    for ax, (col, label) in zip(axes, metrics):
        cat_data = [df[df["pattern_category"] == c][col].dropna() for c in cat_order]
        bp = ax.boxplot(cat_data, tick_labels=[f"{c}: {CATEGORY_NAMES[c]}" for c in cat_order],
                        patch_artist=True)
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_ylabel(label)
        ax.set_title(f"{label} by Category")

    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "category_comparison.png", dpi=150)
    plt.close(fig)
    print("  Saved: category_comparison.png")


def plot_agent_count_effect(df: pd.DataFrame):
    """Scatter: agent_count vs turn_count with regression."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6))

    for cat, color in CATEGORY_COLORS.items():
        mask = df["pattern_category"] == cat
        ax.scatter(
            df.loc[mask, "agent_count"] + np.random.uniform(-0.1, 0.1, mask.sum()),
            df.loc[mask, "turn_count"],
            c=color, alpha=0.4, label=f"{cat}: {CATEGORY_NAMES[cat]}",
            s=20,
        )

    # Spearman correlation
    valid = df[["agent_count", "turn_count"]].dropna()
    rho, pval = sp_stats.spearmanr(valid["agent_count"], valid["turn_count"])
    ax.set_title(f"Agent Count vs Turn Count (Spearman ρ={rho:.3f}, p={pval:.4f})")
    ax.set_xlabel("Agent Count")
    ax.set_ylabel("Turn Count")
    ax.legend()
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "agent_count_vs_turns.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: agent_count_vs_turns.png (ρ={rho:.3f})")


def plot_stop_reason_distribution(df: pd.DataFrame):
    """Stacked bar: stop reason distribution by pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Categorize stop reasons
    def classify_stop(row):
        if row.get("error"):
            return "error"
        tb = str(row.get("terminated_by", ""))
        if tb == "keyword":
            return "keyword"
        elif tb == "max_messages":
            return "max_messages"
        return "other"

    df = df.copy()
    df["stop_class"] = df.apply(classify_stop, axis=1)

    cross = pd.crosstab(df["pattern"], df["stop_class"], normalize="index")
    order = sorted(cross.index, key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    cross = cross.reindex(order)

    fig, ax = plt.subplots(figsize=(14, 6))
    cross.plot(kind="bar", stacked=True, ax=ax,
               color={"keyword": "#4C78A8", "max_messages": "#F58518", "error": "#E45756", "other": "#999999"})
    ax.set_title("Stop Reason Distribution by Pattern")
    ax.set_ylabel("Proportion")
    ax.legend(title="Stop Reason")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "stop_reason_dist.png", dpi=150)
    plt.close(fig)
    print("  Saved: stop_reason_dist.png")


def plot_heatmap_pattern_task(df: pd.DataFrame):
    """Heatmap: pattern × task_category (mean turn_count)."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    pivot = df.pivot_table(
        values="turn_count", index="pattern", columns="task_category", aggfunc="mean"
    )
    order = sorted(pivot.index, key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    pivot = pivot.reindex(order)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax)
    ax.set_title("Mean Turn Count: Pattern × Task Category")
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "heatmap_pattern_task.png", dpi=150)
    plt.close(fig)
    print("  Saved: heatmap_pattern_task.png")


def plot_token_efficiency(df: pd.DataFrame):
    """Box plot: tokens per agent turn by pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    df["tokens_per_turn"] = df["total_tokens"] / df["agent_turn_count"].replace(0, np.nan)

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))

    # Total tokens by pattern
    order = sorted(df["pattern"].unique(), key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    palette = {p: CATEGORY_COLORS[PATTERN_CATEGORY[p]] for p in df["pattern"].unique()}

    sns.boxplot(data=df, x="pattern", y="total_tokens", order=order, palette=palette, ax=axes[0])
    axes[0].set_title("Total Tokens by Pattern")
    axes[0].set_ylabel("Total Tokens")
    axes[0].tick_params(axis="x", rotation=45)

    # Tokens per turn by pattern
    sns.boxplot(data=df, x="pattern", y="tokens_per_turn", order=order, palette=palette, ax=axes[1])
    axes[1].set_title("Tokens per Agent Turn by Pattern")
    axes[1].set_ylabel("Tokens / Agent Turn")
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "token_efficiency.png", dpi=150)
    plt.close(fig)
    print("  Saved: token_efficiency.png")


def compute_stats(df: pd.DataFrame):
    """Statistical tests and summary table."""
    stats_lines = ["# Exp01 Statistical Analysis\n"]

    # 1. Category-level Kruskal-Wallis
    for metric in ["turn_count", "duration_sec"]:
        groups = [
            df[df["pattern_category"] == c][metric].dropna()
            for c in ["A", "B1", "B2", "C", "D"]
            if len(df[df["pattern_category"] == c][metric].dropna()) > 0
        ]
        if len(groups) >= 2:
            stat, pval = sp_stats.kruskal(*groups)
            stats_lines.append(f"## Kruskal-Wallis: {metric} across categories")
            stats_lines.append(f"H={stat:.3f}, p={pval:.6f}\n")

    # 2. Within-category: agent count effect (Spearman)
    for cat in ["A", "B1", "B2", "C"]:
        sub = df[df["pattern_category"] == cat][["agent_count", "turn_count"]].dropna()
        if len(sub) > 3:
            rho, pval = sp_stats.spearmanr(sub["agent_count"], sub["turn_count"])
            stats_lines.append(f"## Category {cat} ({CATEGORY_NAMES[cat]}): agent_count vs turn_count")
            stats_lines.append(f"Spearman ρ={rho:.3f}, p={pval:.4f}\n")

    # 3. Summary table
    summary = df.groupby("pattern").agg(
        category=("pattern_category", "first"),
        agents=("agent_count", "first"),
        runs=("task_id", "count"),
        mean_turns=("turn_count", "mean"),
        std_turns=("turn_count", "std"),
        mean_duration=("duration_sec", "mean"),
        mean_tokens=("total_tokens", "mean"),
        mean_tokens_in=("total_tokens_in", "mean"),
        mean_tokens_out=("total_tokens_out", "mean"),
        keyword_pct=("terminated_by", lambda x: (x == "keyword").mean()),
    ).round(2)

    stats_lines.append("## Summary Table\n")
    stats_lines.append(summary.to_markdown())

    stats_text = "\n".join(stats_lines)
    stats_path = INPUT_DIR / "stats.md"
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(stats_text)
    print(f"  Saved: stats.md")
    return stats_text


def analyze():
    """Run all exp01 analyses."""
    print("Exp01 Analysis")
    print("-" * 40)

    df = load_data()
    print(f"  Loaded {len(df)} rows")

    plot_box_by_pattern(df)
    plot_category_comparison(df)
    plot_agent_count_effect(df)
    plot_stop_reason_distribution(df)
    plot_heatmap_pattern_task(df)
    plot_token_efficiency(df)
    compute_stats(df)

    print("\nExp01 analysis complete.")


if __name__ == "__main__":
    analyze()
