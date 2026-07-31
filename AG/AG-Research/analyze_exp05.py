"""
Experiment 05 Analysis: Adaptive Termination
=============================================
Compares adaptive ΔU(t) termination vs baseline (fixed max_messages).

Reads: results/exp05/summary.csv (baseline + adaptive runs)
       results/exp05/adaptive_stats.json (ΔU trajectories per run)
Outputs: figures/fig_exp05_*.png
         results/exp05/exp05_analysis.csv

Key metrics:
  - Turn reduction: (baseline_turns - adaptive_turns) / baseline_turns
  - Cost savings: (baseline_tokens - adaptive_tokens) / baseline_tokens
  - Adaptive stopped by: ΔU termination vs MaxMessage safety net
  - ΔU convergence speed by pattern and λ

Usage:
  cd AG/AG-Research && C:/Python313/python analyze_exp05.py
"""

import sys
import io
import json
import warnings

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore', category=FutureWarning)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

from config import (
    CATEGORY_COLORS,
    CATEGORY_NAMES,
    LAMBDA_VALUES,
    PATTERN_CATEGORY,
    PATTERNS_REPRESENTATIVE,
    RESULTS_DIR,
)

BASE_DIR = Path(__file__).resolve().parent
FIGURES_DIR = BASE_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = RESULTS_DIR / "exp05"


def load_data():
    """Load exp05 results and adaptive stats."""
    csv_path = OUTPUT_DIR / "summary.csv"
    if not csv_path.exists():
        csv_path = OUTPUT_DIR / "summary_partial.csv"
    if not csv_path.exists():
        print("[ERROR] No exp05 results found. Run exp05 first.")
        return None, None

    df = pd.read_csv(csv_path)
    print(f"[OK] Loaded {len(df)} runs from {csv_path.name}")

    # Separate baseline and adaptive
    df["condition"] = df["experiment_id"].apply(
        lambda x: "baseline" if "baseline" in x else "adaptive"
    )
    df["lambda_val"] = df["experiment_id"].apply(
        lambda x: float(x.split("_l")[-1]) if "_l" in x else None
    )
    df["category"] = df["pattern"].map(PATTERN_CATEGORY)

    # Load adaptive stats if available
    stats_path = OUTPUT_DIR / "adaptive_stats.json"
    stats = None
    if stats_path.exists():
        with open(stats_path, encoding="utf-8") as f:
            stats = json.load(f)
        print(f"[OK] Loaded {len(stats)} adaptive stats entries")

    return df, stats


def filter_successful(df):
    """Keep only successful runs."""
    if "error" in df.columns:
        mask = df["error"].isna() | (df["error"] == "") | (df["error"] == "None")
        df_ok = df[mask].copy()
        n_err = len(df) - len(df_ok)
        if n_err > 0:
            print(f"[INFO] Filtered out {n_err} error runs, keeping {len(df_ok)}")
        return df_ok
    return df


def compute_savings(df):
    """Compute turn and cost savings: adaptive vs baseline per (pattern, task)."""
    baseline = df[df["condition"] == "baseline"].set_index(["pattern", "task_id"])
    adaptive = df[df["condition"] == "adaptive"]

    rows = []
    for _, row in adaptive.iterrows():
        key = (row["pattern"], row["task_id"])
        if key not in baseline.index:
            continue
        bl = baseline.loc[key]
        if isinstance(bl, pd.DataFrame):
            bl = bl.iloc[0]

        bl_turns = bl["turn_count"]
        bl_tokens = bl["total_tokens"]
        ad_turns = row["turn_count"]
        ad_tokens = row["total_tokens"]

        turn_reduction = (bl_turns - ad_turns) / max(bl_turns, 1)
        cost_savings = (bl_tokens - ad_tokens) / max(bl_tokens, 1)

        rows.append({
            "pattern": row["pattern"],
            "task_id": row["task_id"],
            "category": row["category"],
            "lambda_val": row["lambda_val"],
            "baseline_turns": bl_turns,
            "adaptive_turns": ad_turns,
            "turn_reduction": turn_reduction,
            "baseline_tokens": bl_tokens,
            "adaptive_tokens": ad_tokens,
            "cost_savings": cost_savings,
            "stopped_by": row.get("terminated_by", "unknown"),
        })

    savings_df = pd.DataFrame(rows)
    print(f"[OK] Computed savings for {len(savings_df)} (pattern, task, λ) pairs")
    return savings_df


def plot_cost_savings_by_pattern(savings_df):
    """Bar chart: average cost savings by pattern and λ."""
    patterns = [p for p in PATTERNS_REPRESENTATIVE if p in savings_df["pattern"].unique()]
    lambdas = sorted(savings_df["lambda_val"].dropna().unique())

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 1. Turn reduction by pattern (aggregated across λ)
    ax = axes[0]
    means = savings_df.groupby("pattern")["turn_reduction"].mean()
    means = means.reindex(patterns)
    colors = [CATEGORY_COLORS.get(PATTERN_CATEGORY.get(p, "?"), "#999") for p in patterns]
    bars = ax.bar(patterns, means.values * 100, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_ylabel("Turn Reduction (%)")
    ax.set_title("Average Turn Reduction vs Baseline", fontweight='bold')
    ax.set_ylim(0, 100)
    ax.axhline(y=0, color='black', linewidth=0.5)
    for bar, val in zip(bars, means.values):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f"{val*100:.1f}%", ha='center', va='bottom', fontsize=9)

    # 2. Cost savings by pattern
    ax = axes[1]
    means = savings_df.groupby("pattern")["cost_savings"].mean()
    means = means.reindex(patterns)
    bars = ax.bar(patterns, means.values * 100, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_ylabel("Token Savings (%)")
    ax.set_title("Average Token Cost Savings vs Baseline", fontweight='bold')
    ax.set_ylim(0, 100)
    ax.axhline(y=0, color='black', linewidth=0.5)
    for bar, val in zip(bars, means.values):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f"{val*100:.1f}%", ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    output_path = FIGURES_DIR / "fig_exp05_savings_by_pattern.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def plot_lambda_sensitivity(savings_df):
    """Line chart: cost savings as a function of λ, one line per pattern."""
    fig, ax = plt.subplots(figsize=(10, 6))

    patterns = [p for p in PATTERNS_REPRESENTATIVE if p in savings_df["pattern"].unique()]
    lambdas = sorted(savings_df["lambda_val"].dropna().unique())

    for pattern in patterns:
        p_data = savings_df[savings_df["pattern"] == pattern]
        means = p_data.groupby("lambda_val")["cost_savings"].mean()
        cat = PATTERN_CATEGORY.get(pattern, "?")
        color = CATEGORY_COLORS.get(cat, "#999")
        ax.plot(means.index, means.values * 100, 'o-',
                label=f"{pattern} ({cat})", color=color, linewidth=2, markersize=6)

    ax.set_xlabel("λ (Cost Sensitivity)", fontsize=12)
    ax.set_ylabel("Token Cost Savings (%)", fontsize=12)
    ax.set_title("λ Sensitivity: Cost Savings by Pattern", fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(lambdas)

    plt.tight_layout()
    output_path = FIGURES_DIR / "fig_exp05_lambda_sensitivity.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def plot_delta_u_trajectories(adaptive_stats):
    """Plot ΔU(t) trajectories by pattern (from adaptive_stats.json)."""
    if not adaptive_stats:
        print("[SKIP] No adaptive stats available for ΔU trajectory plot")
        return

    fig, axes = plt.subplots(2, 4, figsize=(20, 10), sharex=False, sharey=True)
    axes_flat = axes.flatten()

    patterns = PATTERNS_REPRESENTATIVE
    # Use λ=0.1 as default showcase
    target_lambda = 0.1

    for idx, pattern in enumerate(patterns):
        if idx >= len(axes_flat):
            break
        ax = axes_flat[idx]
        p_stats = [s for s in adaptive_stats
                   if s["pattern"] == pattern and abs(s.get("lambda", 0) - target_lambda) < 0.001]

        if not p_stats:
            ax.set_title(f"{pattern}\n(no data)", fontsize=10)
            continue

        # Plot each run's ΔU trajectory as a thin line
        for s in p_stats:
            dus = s.get("delta_utilities", [])
            if dus:
                turns = range(1, len(dus) + 1)
                ax.plot(turns, dus, alpha=0.3, linewidth=0.8,
                        color=CATEGORY_COLORS.get(PATTERN_CATEGORY.get(pattern, "?"), "#999"))

        # Average trajectory
        max_len = max(len(s.get("delta_utilities", [])) for s in p_stats) if p_stats else 0
        if max_len > 0:
            avg_du = []
            for t in range(max_len):
                vals = [s["delta_utilities"][t] for s in p_stats
                        if len(s.get("delta_utilities", [])) > t]
                avg_du.append(np.mean(vals) if vals else 0)
            ax.plot(range(1, len(avg_du) + 1), avg_du, 'k-', linewidth=2.5, label='mean')

        ax.axhline(y=0, color='red', linewidth=1, linestyle='--', alpha=0.7)
        cat = PATTERN_CATEGORY.get(pattern, "?")
        ax.set_title(f"{pattern} ({cat})", fontsize=11, fontweight='bold')
        ax.set_xlabel("Turn")
        if idx % 4 == 0:
            ax.set_ylabel("ΔU(t)")

    fig.suptitle(f"ΔU(t) Trajectories by Pattern (λ={target_lambda})",
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    output_path = FIGURES_DIR / "fig_exp05_delta_u_trajectories.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def summary_table(df, savings_df):
    """Print summary tables for the paper."""
    print("\n=== Exp05 Summary: Baseline vs Adaptive ===\n")

    # Table: Pattern-level summary
    print(f"{'Pattern':<10} {'Cat':>4} {'BL turns':>10} {'AD turns':>10} {'Turn Δ%':>8} {'BL tok':>10} {'AD tok':>10} {'Tok Δ%':>8}")
    print("-" * 80)

    for p in PATTERNS_REPRESENTATIVE:
        p_savings = savings_df[savings_df["pattern"] == p]
        if p_savings.empty:
            continue
        cat = PATTERN_CATEGORY.get(p, "?")
        bl_t = p_savings["baseline_turns"].mean()
        ad_t = p_savings["adaptive_turns"].mean()
        turn_r = p_savings["turn_reduction"].mean() * 100
        bl_k = p_savings["baseline_tokens"].mean()
        ad_k = p_savings["adaptive_tokens"].mean()
        cost_r = p_savings["cost_savings"].mean() * 100
        print(f"{p:<10} {cat:>4} {bl_t:>10.1f} {ad_t:>10.1f} {turn_r:>7.1f}% {bl_k:>10.0f} {ad_k:>10.0f} {cost_r:>7.1f}%")

    # Table: Lambda sensitivity
    print(f"\n=== λ Sensitivity (averaged across patterns) ===\n")
    print(f"{'λ':>6} {'Avg Turn Δ%':>12} {'Avg Tok Δ%':>12} {'N':>6}")
    print("-" * 40)
    for lv in sorted(savings_df["lambda_val"].dropna().unique()):
        lv_data = savings_df[savings_df["lambda_val"] == lv]
        print(f"{lv:>6.2f} {lv_data['turn_reduction'].mean()*100:>11.1f}% {lv_data['cost_savings'].mean()*100:>11.1f}% {len(lv_data):>6}")

    # Table: Stopped by ΔU vs MaxMessage
    if "stopped_by" in savings_df.columns:
        print(f"\n=== Termination Source ===\n")
        for p in PATTERNS_REPRESENTATIVE:
            p_data = savings_df[savings_df["pattern"] == p]
            if p_data.empty:
                continue
            total = len(p_data)
            adaptive_stop = p_data[p_data["stopped_by"].str.contains("adaptive|functional", case=False, na=False)]
            max_msg_stop = p_data[p_data["stopped_by"].str.contains("max|safety", case=False, na=False)]
            print(f"  {p}: adaptive={len(adaptive_stop)}/{total} ({len(adaptive_stop)/total*100:.0f}%), "
                  f"max_msg={len(max_msg_stop)}/{total} ({len(max_msg_stop)/total*100:.0f}%)")


def main():
    df, adaptive_stats = load_data()
    if df is None:
        return

    df = filter_successful(df)

    baseline_count = len(df[df["condition"] == "baseline"])
    adaptive_count = len(df[df["condition"] == "adaptive"])
    print(f"[INFO] Baseline: {baseline_count}, Adaptive: {adaptive_count}")

    if baseline_count == 0 or adaptive_count == 0:
        print("[ERROR] Need both baseline and adaptive runs for comparison.")
        return

    # Compute savings
    savings_df = compute_savings(df)

    # Save analysis CSV
    out_csv = OUTPUT_DIR / "exp05_analysis.csv"
    savings_df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] Saved: {out_csv}")

    # Summary tables
    summary_table(df, savings_df)

    # Plots
    plot_cost_savings_by_pattern(savings_df)
    plot_lambda_sensitivity(savings_df)
    plot_delta_u_trajectories(adaptive_stats)

    print("\n=== Exp05 Analysis Complete ===")


if __name__ == "__main__":
    main()
