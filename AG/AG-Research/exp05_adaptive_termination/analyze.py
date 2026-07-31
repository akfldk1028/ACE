"""
Experiment 05 Analysis: Adaptive Termination
=============================================
- Pareto frontier: tokens vs quality, colored by λ
- Adaptive vs baseline: paired comparison
- Optimal λ by pattern/category
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

from config import CATEGORY_NAMES, CATEGORY_COLORS, PATTERN_CATEGORY, RESULTS_DIR

INPUT_DIR = RESULTS_DIR / "exp05"
PLOTS_DIR = INPUT_DIR / "plots"


def load_data() -> pd.DataFrame:
    csv_path = INPUT_DIR / "summary.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No data at {csv_path}. Run exp05 first.")
    df = pd.read_csv(csv_path)

    # Parse experiment_id to extract condition and lambda
    df["condition"] = df["experiment_id"].apply(
        lambda x: "baseline" if "baseline" in x else "adaptive"
    )
    df["lambda_val"] = df["experiment_id"].apply(
        lambda x: float(x.split("_l")[-1]) if "_l" in x else 0.0
    )

    return df


def plot_pareto_frontier(df: pd.DataFrame):
    """Pareto frontier: X=total_tokens (or turn_count), Y=duration, colored by λ."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Use total_tokens as cost axis if available, else fall back to turn_count
    has_tokens = "total_tokens" in df.columns and df["total_tokens"].sum() > 0
    cost_col = "total_tokens" if has_tokens else "turn_count"
    cost_label = "Total Tokens" if has_tokens else "Turn Count (cost proxy)"

    fig, ax = plt.subplots(figsize=(10, 7))

    baseline = df[df["condition"] == "baseline"]
    adaptive = df[df["condition"] == "adaptive"]

    ax.scatter(baseline[cost_col], baseline["duration_sec"],
               c="gray", alpha=0.3, s=20, label="Baseline")

    if not adaptive.empty:
        scatter = ax.scatter(
            adaptive[cost_col],
            adaptive["duration_sec"],
            c=adaptive["lambda_val"],
            cmap="viridis",
            alpha=0.6,
            s=30,
        )
        plt.colorbar(scatter, ax=ax, label="λ (cost sensitivity)")

    ax.set_xlabel(cost_label)
    ax.set_ylabel("Duration (seconds)")
    ax.set_title("Adaptive vs Baseline: Cost-Efficiency Frontier")
    ax.legend()
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "pareto_frontier.png", dpi=150)
    plt.close(fig)
    print("  Saved: pareto_frontier.png")


def plot_adaptive_vs_baseline(df: pd.DataFrame):
    """Compare adaptive vs baseline on key metrics."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    has_tokens = "total_tokens" in df.columns and df["total_tokens"].sum() > 0
    metrics = [
        ("turn_count", "Turn Count"),
        ("duration_sec", "Duration (s)"),
        ("total_tokens" if has_tokens else "agent_turn_count",
         "Total Tokens" if has_tokens else "Agent Turns"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for ax, (col, label) in zip(axes, metrics):
        baseline = df[df["condition"] == "baseline"]
        adaptive = df[df["condition"] == "adaptive"]

        data = [baseline[col].dropna(), adaptive[col].dropna()]
        labels_list = ["Baseline", "Adaptive"]

        if all(len(d) > 0 for d in data):
            bp = ax.boxplot(data, tick_labels=labels_list, patch_artist=True)
            bp["boxes"][0].set_facecolor("#CCCCCC")
            bp["boxes"][1].set_facecolor("#4C78A8")
            for box in bp["boxes"]:
                box.set_alpha(0.7)

            # Paired t-test if sizes match
            if len(data[0]) > 1 and len(data[1]) > 1:
                stat, pval = sp_stats.mannwhitneyu(data[0], data[1], alternative="two-sided")
                ax.set_title(f"{label}\n(U={stat:.0f}, p={pval:.4f})")
            else:
                ax.set_title(label)
        else:
            ax.set_title(f"{label}\n(insufficient data)")

        ax.set_ylabel(label)

    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "adaptive_vs_baseline.png", dpi=150)
    plt.close(fig)
    print("  Saved: adaptive_vs_baseline.png")


def plot_lambda_effect(df: pd.DataFrame):
    """Effect of λ on turn count per pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    adaptive = df[df["condition"] == "adaptive"]
    if adaptive.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    for pattern in sorted(adaptive["pattern"].unique(),
                          key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p)):
        cat = PATTERN_CATEGORY.get(pattern, "?")
        color = CATEGORY_COLORS.get(cat, "#999999")
        sub = adaptive[adaptive["pattern"] == pattern]
        grouped = sub.groupby("lambda_val")["turn_count"].mean()
        ax.plot(grouped.index, grouped.values, color=color,
                label=f"{pattern} ({cat})", marker="o")

    ax.set_xlabel("λ (cost sensitivity)")
    ax.set_ylabel("Mean Turn Count")
    ax.set_title("Effect of λ on Turn Count by Pattern")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "lambda_effect.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Saved: lambda_effect.png")


def compute_optimal_lambda(df: pd.DataFrame):
    """Find optimal λ per pattern (minimizes turns while maintaining keyword termination)."""
    adaptive = df[df["condition"] == "adaptive"]
    if adaptive.empty:
        return pd.DataFrame()

    records = []
    has_tokens = "total_tokens" in adaptive.columns and adaptive["total_tokens"].sum() > 0

    for pattern in adaptive["pattern"].unique():
        for lam in adaptive["lambda_val"].unique():
            sub = adaptive[(adaptive["pattern"] == pattern) & (adaptive["lambda_val"] == lam)]
            if sub.empty:
                continue
            rec = {
                "pattern": pattern,
                "category": PATTERN_CATEGORY.get(pattern, "?"),
                "lambda": lam,
                "mean_turns": sub["turn_count"].mean(),
                "keyword_rate": (sub["terminated_by"] == "keyword").mean(),
            }
            if has_tokens:
                rec["mean_tokens"] = sub["total_tokens"].mean()
            records.append(rec)

    return pd.DataFrame(records)


def analyze():
    """Run all exp05 analyses."""
    print("Exp05 Analysis: Adaptive Termination")
    print("-" * 40)

    df = load_data()
    print(f"  Loaded {len(df)} rows")
    print(f"  Baseline: {(df['condition']=='baseline').sum()}, Adaptive: {(df['condition']=='adaptive').sum()}")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    plot_pareto_frontier(df)
    plot_adaptive_vs_baseline(df)
    plot_lambda_effect(df)

    opt_df = compute_optimal_lambda(df)
    if not opt_df.empty:
        opt_path = INPUT_DIR / "optimal_lambda.md"
        with open(opt_path, "w", encoding="utf-8") as f:
            f.write("# Optimal λ by Pattern\n\n")
            f.write(opt_df.round(3).to_markdown(index=False))
        print("  Saved: optimal_lambda.md")

    print("\nExp05 analysis complete.")


if __name__ == "__main__":
    analyze()
