"""
Experiment 03 Analysis: Convergence Detection
==============================================
Reuses exp01/exp02 raw data (no new runs needed).
- Convergence curves per pattern
- Category-level convergence speed comparison
- KS-statistic between categories
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats as sp_stats

from config import CATEGORY_NAMES, CATEGORY_COLORS, PATTERN_CATEGORY, RESULTS_DIR
from experiment_utils import RunResult, TurnRecord
from exp03_convergence_detection.embeddings import (
    compute_convergence_curve,
    word_overlap_similarity,
)

INPUT_DIR = RESULTS_DIR / "exp01"  # Reuse exp01 raw data
OUTPUT_DIR = RESULTS_DIR / "exp03"
PLOTS_DIR = OUTPUT_DIR / "plots"


def load_runs() -> list[RunResult]:
    """Load raw run data from exp01."""
    raw_path = INPUT_DIR / "raw.json"
    if not raw_path.exists():
        raise FileNotFoundError(f"No raw data at {raw_path}. Run exp01 first.")

    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    runs = []
    for d in data:
        turns = [TurnRecord(**t) for t in d.get("turns", [])]
        r = RunResult(
            experiment_id=d["experiment_id"],
            task_id=d["task_id"],
            pattern=d["pattern"],
            repeat_index=d["repeat_index"],
            pattern_category=d["pattern_category"],
            agent_count=d["agent_count"],
            stop_reason=d.get("stop_reason"),
            duration_sec=d["duration_sec"],
            total_tokens_in=d["total_tokens_in"],
            total_tokens_out=d["total_tokens_out"],
            total_tokens=d["total_tokens"],
            turn_count=d["turn_count"],
            agent_turn_count=d["agent_turn_count"],
            terminated_by=d.get("terminated_by"),
            turns=turns,
            error=d.get("error"),
        )
        runs.append(r)

    return runs


def compute_heuristic_convergence(runs: list[RunResult]) -> pd.DataFrame:
    """Compute convergence using word overlap (no LLM, fast)."""
    records = []

    for run in runs:
        agent_turns = [t for t in run.turns if t.source != "user"]
        if len(agent_turns) < 2:
            continue

        sims = []
        for i in range(1, len(agent_turns)):
            sim = word_overlap_similarity(agent_turns[i - 1].content, agent_turns[i].content)
            sims.append(sim)

        # Detect convergence (theta=0.5, k=2)
        converged_at = None
        consecutive = 0
        for i, sim in enumerate(sims):
            if sim >= 0.5:
                consecutive += 1
                if consecutive >= 2:
                    converged_at = i - 1
                    break
            else:
                consecutive = 0

        for i, sim in enumerate(sims):
            records.append({
                "pattern": run.pattern,
                "pattern_category": run.pattern_category,
                "task_id": run.task_id,
                "repeat_index": run.repeat_index,
                "turn_pair": i,
                "similarity": sim,
                "converged_at": converged_at,
            })

    return pd.DataFrame(records)


def plot_convergence_curves(conv_df: pd.DataFrame):
    """Convergence curves by pattern (mean similarity over turn pairs)."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    for pattern in sorted(conv_df["pattern"].unique(),
                          key=lambda p: (PATTERN_CATEGORY.get(p, "Z"), p)):
        cat = PATTERN_CATEGORY.get(pattern, "?")
        color = CATEGORY_COLORS.get(cat, "#999999")
        sub = conv_df[conv_df["pattern"] == pattern]
        grouped = sub.groupby("turn_pair")["similarity"].mean()
        ax.plot(grouped.index, grouped.values, color=color, alpha=0.7,
                label=f"{pattern} ({cat})", marker="o", markersize=3)

    ax.axhline(y=0.5, color="red", linestyle="--", alpha=0.5, label="θ=0.5 threshold")
    ax.set_title("Convergence Curve: Word Overlap Similarity Between Consecutive Turns")
    ax.set_xlabel("Turn Pair Index")
    ax.set_ylabel("Jaccard Word Overlap")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "convergence_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Saved: convergence_curves.png")


def plot_convergence_by_category(conv_df: pd.DataFrame):
    """Compare convergence speed across categories."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Get converged_at per run (unique per pattern/task/repeat)
    conv_at = conv_df.groupby(["pattern", "pattern_category", "task_id", "repeat_index"]).agg(
        converged_at=("converged_at", "first"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    cat_order = ["A", "B1", "B2", "C", "D"]
    colors = [CATEGORY_COLORS[c] for c in cat_order]

    cat_data = [conv_at[conv_at["pattern_category"] == c]["converged_at"].dropna() for c in cat_order]
    valid_cats = [(c, d, col) for c, d, col in zip(cat_order, cat_data, colors) if len(d) > 0]

    if valid_cats:
        bp = ax.boxplot(
            [d for _, d, _ in valid_cats],
            tick_labels=[f"{c}: {CATEGORY_NAMES[c]}" for c, _, _ in valid_cats],
            patch_artist=True,
        )
        for i, (_, _, col) in enumerate(valid_cats):
            bp["boxes"][i].set_facecolor(col)
            bp["boxes"][i].set_alpha(0.7)

    ax.set_title("Convergence Speed by Category (lower = faster)")
    ax.set_ylabel("Turn Pair Index at Convergence")
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "convergence_by_category.png", dpi=150)
    plt.close(fig)
    print("  Saved: convergence_by_category.png")


def ks_test_categories(conv_df: pd.DataFrame):
    """KS-statistic between category pairs for convergence speed."""
    conv_at = conv_df.groupby(["pattern", "pattern_category", "task_id"]).agg(
        converged_at=("converged_at", "first"),
        mean_sim=("similarity", "mean"),
    ).reset_index()

    cats = ["A", "B1", "B2", "C", "D"]
    results = []

    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            data_i = conv_at[conv_at["pattern_category"] == cats[i]]["mean_sim"].dropna()
            data_j = conv_at[conv_at["pattern_category"] == cats[j]]["mean_sim"].dropna()
            if len(data_i) > 1 and len(data_j) > 1:
                stat, pval = sp_stats.ks_2samp(data_i, data_j)
                results.append({
                    "cat_pair": f"{cats[i]} vs {cats[j]}",
                    "ks_stat": round(stat, 4),
                    "p_value": round(pval, 6),
                })

    return pd.DataFrame(results)


async def main(patterns=None, dry_run=False):
    """Run exp03 analysis (no new runs, uses exp01 data)."""
    analyze()


def analyze():
    """Run all exp03 analyses."""
    print("Exp03 Analysis: Convergence Detection")
    print("-" * 40)

    runs = load_runs()
    print(f"  Loaded {len(runs)} runs from exp01")

    conv_df = compute_heuristic_convergence(runs)
    print(f"  Computed {len(conv_df)} similarity measurements")

    if conv_df.empty:
        print("  No convergence data. Skipping plots.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    plot_convergence_curves(conv_df)
    plot_convergence_by_category(conv_df)

    ks_df = ks_test_categories(conv_df)
    if not ks_df.empty:
        ks_path = OUTPUT_DIR / "ks_tests.md"
        with open(ks_path, "w", encoding="utf-8") as f:
            f.write("# KS-Test: Convergence Speed Between Categories\n\n")
            f.write(ks_df.to_markdown(index=False))
        print(f"  Saved: ks_tests.md")

    # Save convergence summary
    conv_df.to_csv(OUTPUT_DIR / "convergence_data.csv", index=False)
    print(f"  Saved: convergence_data.csv")

    print("\nExp03 analysis complete.")


if __name__ == "__main__":
    analyze()
