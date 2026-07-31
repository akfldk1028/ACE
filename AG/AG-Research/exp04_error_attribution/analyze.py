"""
Experiment 04 Analysis: Error Attribution
=========================================
Scans exp01-03 results (no new runs needed).
- Error type distribution by pattern and category
- Agent count vs error rate correlation
- Confusion matrix of error types × patterns
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

from config import CATEGORY_NAMES, CATEGORY_COLORS, PATTERN_CATEGORY, RESULTS_DIR
from exp04_error_attribution.classifier import classify_run, ErrorType

OUTPUT_DIR = RESULTS_DIR / "exp04"
PLOTS_DIR = OUTPUT_DIR / "plots"


def load_all_results() -> list[dict]:
    """Load raw results from exp01 and exp02."""
    all_data = []

    for exp in ["exp01", "exp02"]:
        raw_path = RESULTS_DIR / exp / "raw.json"
        if raw_path.exists():
            with open(raw_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_data.extend(data)
            print(f"  Loaded {len(data)} runs from {exp}")

    return all_data


def classify_all(runs: list[dict]) -> pd.DataFrame:
    """Classify all runs and return DataFrame."""
    records = [classify_run(r) for r in runs]
    return pd.DataFrame(records)


def plot_error_rate_by_pattern(df: pd.DataFrame):
    """Bar chart: error rate per pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    error_rate = df.groupby("pattern")["has_error"].mean().sort_values(ascending=False)
    order = sorted(error_rate.index, key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    error_rate = error_rate.reindex(order)

    colors = [CATEGORY_COLORS[PATTERN_CATEGORY.get(p, "A")] for p in order]

    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(error_rate)), error_rate.values, color=colors)
    ax.set_xticks(range(len(error_rate)))
    ax.set_xticklabels(error_rate.index, rotation=45, ha="right")
    ax.set_ylabel("Error Rate")
    ax.set_title("Error Rate by Pattern")
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "error_rate_by_pattern.png", dpi=150)
    plt.close(fig)
    print("  Saved: error_rate_by_pattern.png")


def plot_error_type_distribution(df: pd.DataFrame):
    """Stacked bar: error type distribution by pattern."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    errors_only = df[df["has_error"]].copy()
    if errors_only.empty:
        print("  No errors found. Skipping error type distribution.")
        return

    cross = pd.crosstab(errors_only["pattern"], errors_only["error_type"], normalize="index")
    order = sorted(cross.index, key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    cross = cross.reindex(order)

    fig, ax = plt.subplots(figsize=(14, 6))
    cross.plot(kind="bar", stacked=True, ax=ax, colormap="Set2")
    ax.set_title("Error Type Distribution by Pattern")
    ax.set_ylabel("Proportion")
    ax.legend(title="Error Type", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "error_type_dist.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Saved: error_type_dist.png")


def plot_error_heatmap(df: pd.DataFrame):
    """Heatmap: error type × pattern (counts)."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    errors_only = df[df["has_error"]].copy()
    if errors_only.empty:
        return

    cross = pd.crosstab(errors_only["pattern"], errors_only["error_type"])
    order = sorted(cross.index, key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p))
    cross = cross.reindex(order)

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(cross, annot=True, fmt="d", cmap="YlOrRd", ax=ax)
    ax.set_title("Error Count: Pattern × Error Type")
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "error_heatmap.png", dpi=150)
    plt.close(fig)
    print("  Saved: error_heatmap.png")


def compute_agent_count_error_correlation(df: pd.DataFrame):
    """Spearman correlation: agent_count vs error_rate."""
    pattern_errors = df.groupby("pattern").agg(
        agent_count=("agent_count", "first"),
        error_rate=("has_error", "mean"),
        total_runs=("has_error", "count"),
    ).reset_index()

    if len(pattern_errors) < 3:
        return None

    rho, pval = sp_stats.spearmanr(pattern_errors["agent_count"], pattern_errors["error_rate"])
    return {"spearman_rho": round(rho, 4), "p_value": round(pval, 6)}


async def main(patterns=None, dry_run=False):
    """Run exp04 analysis (no new runs)."""
    analyze()


def analyze():
    """Run all exp04 analyses."""
    print("Exp04 Analysis: Error Attribution")
    print("-" * 40)

    runs = load_all_results()
    if not runs:
        print("  No data found. Run exp01/exp02 first.")
        return

    df = classify_all(runs)
    print(f"  Classified {len(df)} runs: {df['has_error'].sum()} with errors ({df['has_error'].mean():.1%})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    plot_error_rate_by_pattern(df)
    plot_error_type_distribution(df)
    plot_error_heatmap(df)

    # Agent count correlation
    corr = compute_agent_count_error_correlation(df)

    # Save report
    report_lines = ["# Exp04: Error Attribution Report\n"]

    error_summary = df.groupby("pattern").agg(
        category=("pattern_category", "first"),
        agents=("agent_count", "first"),
        total=("has_error", "count"),
        errors=("has_error", "sum"),
        error_rate=("has_error", "mean"),
    ).round(3)
    report_lines.append("## Error Rate by Pattern\n")
    report_lines.append(error_summary.to_markdown())

    if corr:
        report_lines.append(f"\n## Agent Count vs Error Rate")
        report_lines.append(f"Spearman ρ={corr['spearman_rho']}, p={corr['p_value']}\n")

    # Error type breakdown
    if df["has_error"].any():
        type_counts = df[df["has_error"]]["error_type"].value_counts()
        report_lines.append("\n## Error Type Breakdown\n")
        for etype, count in type_counts.items():
            report_lines.append(f"- {etype}: {count}")

    report_path = OUTPUT_DIR / "error_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"  Saved: error_report.md")

    # Save classified data
    df.to_csv(OUTPUT_DIR / "classified_errors.csv", index=False)

    print("\nExp04 analysis complete.")


if __name__ == "__main__":
    analyze()
