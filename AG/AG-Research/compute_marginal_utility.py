"""
Compute marginal utility ΔU(t) from existing exp02 data.

Uses turn-level G-Eval scores (quality) and token costs to verify that
ΔU(t) = ΔQ(t) - λ·ΔC(t) → 0 at the optimal stopping point.

Reads from:
  results/exp02/scores.csv   (276 turn-level quality scores)
  results/exp02/raw.json     (per-turn token counts)

Outputs:
  results/exp02/marginal_utility.csv
  figures/fig_marginal_utility.png
  figures/fig_marginal_utility_heatmap.png
"""

import sys
import io
import json
import csv
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from config import CATEGORY_COLORS, CATEGORY_NAMES, LAMBDA_VALUES

RESULTS_DIR = Path(__file__).parent / "results" / "exp02"
FIGURES_DIR = Path(__file__).parent / "figures"


def load_data():
    """Load and merge turn-level quality scores with token costs."""
    # Load quality scores
    scores_df = pd.read_csv(RESULTS_DIR / "scores.csv")
    scores_df.rename(columns={"overall": "quality"}, inplace=True)

    # Fix legacy B→B1/B2 categories from v1 data
    cat_remap = {"sel3": "B1", "sel4": "B1", "swm3": "B2", "swm4": "B2"}
    scores_df["pattern_category"] = scores_df.apply(
        lambda r: cat_remap.get(r["pattern"], r["pattern_category"]), axis=1
    )

    # Load raw JSON for per-turn token data
    with open(RESULTS_DIR / "raw.json", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Build per-turn token lookup: (pattern, task_id, turn_index) -> tokens
    token_map = {}
    for run in raw_data:
        pattern = run["pattern"]
        task_id = run["task_id"]
        for turn in run.get("turns", []):
            idx = turn["index"]
            if idx == 0:  # skip user turn
                continue
            tokens = turn["tokens_in"] + turn["tokens_out"]
            token_map[(pattern, task_id, idx)] = tokens

    # Merge tokens into scores
    scores_df["tokens"] = scores_df.apply(
        lambda r: token_map.get((r["pattern"], r["task_id"], r["turn_index"]), 0),
        axis=1,
    )
    # Convert to kilo-tokens for interpretable λ
    scores_df["tokens_kT"] = scores_df["tokens"] / 1000.0

    print(f"[OK] Loaded {len(scores_df)} turn scores with token data")
    print(f"  Patterns: {sorted(scores_df['pattern'].unique())}")
    print(f"  Token range: {scores_df['tokens'].min()}-{scores_df['tokens'].max()}")
    return scores_df


def compute_marginal_utility(df, lambda_values=None):
    """Compute ΔQ(t), ΔC(t), and ΔU(t) for each run × λ combination."""
    if lambda_values is None:
        lambda_values = LAMBDA_VALUES

    results = []

    for (pattern, task_id), group in df.groupby(["pattern", "task_id"]):
        group = group.sort_values("turn_index")
        cat = group["pattern_category"].iloc[0]
        turns = group["turn_index"].values
        qualities = group["quality"].values
        tokens_kT = group["tokens_kT"].values

        # Compute marginals
        # ΔQ(t) = Q(t) - Q(t-1), with Q(0) = 0
        delta_q = np.diff(qualities, prepend=0)  # first turn's ΔQ = Q(1) - 0

        # ΔC(t) = cost of turn t (already marginal — tokens for that specific turn)
        delta_c = tokens_kT

        # Cumulative cost
        cumul_c = np.cumsum(tokens_kT)

        for lam in lambda_values:
            delta_u = delta_q - lam * delta_c

            for i, t in enumerate(turns):
                results.append({
                    "pattern": pattern,
                    "pattern_category": cat,
                    "task_id": task_id,
                    "turn_index": int(t),
                    "quality": float(qualities[i]),
                    "delta_q": float(delta_q[i]),
                    "tokens_kT": float(tokens_kT[i]),
                    "delta_c": float(delta_c[i]),
                    "cumul_cost_kT": float(cumul_c[i]),
                    "lambda": lam,
                    "delta_u": float(delta_u[i]),
                    "U_t": float(qualities[i] - lam * cumul_c[i]),
                })

    result_df = pd.DataFrame(results)
    print(f"[OK] Computed ΔU(t) for {len(result_df)} entries "
          f"({len(df.groupby(['pattern','task_id']))} runs × {len(lambda_values)} λ)")
    return result_df


def find_optimal_stops(mu_df):
    """For each run, find t_optimal (peak quality) and t_mu_zero (ΔU ≤ 0)."""
    summary = []

    for (pattern, task_id, lam), group in mu_df.groupby(["pattern", "task_id", "lambda"]):
        group = group.sort_values("turn_index")
        cat = group["pattern_category"].iloc[0]

        qualities = group["quality"].values
        delta_u = group["delta_u"].values
        turns = group["turn_index"].values
        U_values = group["U_t"].values

        # t_optimal: turn with highest quality
        t_opt_idx = np.argmax(qualities)
        t_optimal = int(turns[t_opt_idx])
        q_optimal = float(qualities[t_opt_idx])

        # t_actual: last turn
        t_actual = int(turns[-1])
        q_actual = float(qualities[-1])

        # t_mu_zero: first turn where ΔU ≤ 0 (after first turn)
        t_mu_zero = t_actual  # default: never converges
        for i in range(1, len(delta_u)):  # skip first turn
            if delta_u[i] <= 0:
                t_mu_zero = int(turns[i])
                break

        # t_U_peak: turn with highest U(t)
        t_U_peak_idx = np.argmax(U_values)
        t_U_peak = int(turns[t_U_peak_idx])
        U_peak = float(U_values[t_U_peak_idx])

        # Quality loss from over-computation
        q_loss = q_optimal - q_actual

        # Regret: how many turns past optimal
        regret = t_actual - t_optimal

        summary.append({
            "pattern": pattern,
            "pattern_category": cat,
            "task_id": task_id,
            "lambda": lam,
            "t_optimal": t_optimal,
            "q_optimal": q_optimal,
            "t_actual": t_actual,
            "q_actual": q_actual,
            "t_mu_zero": t_mu_zero,
            "t_U_peak": t_U_peak,
            "U_peak": U_peak,
            "regret": regret,
            "q_loss": q_loss,
        })

    return pd.DataFrame(summary)


def plot_marginal_utility_curves(mu_df, lambda_val=0.1):
    """Plot ΔU(t) curves per pattern for a given λ."""
    patterns = sorted(mu_df["pattern"].unique())
    n_patterns = len(patterns)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes_flat = axes.flatten()

    subset = mu_df[mu_df["lambda"] == lambda_val]

    for idx, pattern in enumerate(patterns):
        if idx >= 6:
            break
        ax = axes_flat[idx]
        pat_data = subset[subset["pattern"] == pattern]
        cat = pat_data["pattern_category"].iloc[0]
        color = CATEGORY_COLORS.get(cat, "#999999")

        # Plot individual runs (light)
        for task_id, run in pat_data.groupby("task_id"):
            run = run.sort_values("turn_index")
            ax.plot(run["turn_index"], run["delta_u"],
                    color=color, alpha=0.2, linewidth=0.8)

        # Mean ΔU(t)
        mean_du = pat_data.groupby("turn_index")["delta_u"].mean()
        ax.plot(mean_du.index, mean_du.values, color=color,
                linewidth=2.5, label=f"Mean ΔU(t)")

        # Zero line
        ax.axhline(y=0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)

        # Mark first crossing of zero
        for t in mean_du.index:
            if t > mean_du.index[0] and mean_du[t] <= 0:
                ax.axvline(x=t, color="red", linewidth=1.5, linestyle=":",
                           alpha=0.7, label=f"ΔU≤0 at t={t}")
                ax.plot(t, mean_du[t], "rv", markersize=10)
                break

        cat_name = CATEGORY_NAMES.get(cat, cat)
        ax.set_title(f"({chr(97+idx)}) {pattern} [{cat_name}]",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel("Agent Turn")
        ax.set_ylabel("ΔU(t)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for i in range(n_patterns, 6):
        axes_flat[i].set_visible(False)

    fig.suptitle(f"Marginal Utility ΔU(t) = ΔQ(t) - λΔC(t)  [λ={lambda_val}]",
                 fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    output_path = FIGURES_DIR / "fig_marginal_utility.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"[OK] Saved: {output_path}")

    # Hi-res
    plt.savefig(FIGURES_DIR / "fig_marginal_utility_hires.png",
                dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()


def plot_lambda_sensitivity(summary_df):
    """Heatmap: pattern × λ showing t_mu_zero (when marginal utility hits zero)."""
    patterns = sorted(summary_df["pattern"].unique())
    lambdas = sorted(summary_df["lambda"].unique())

    # Pivot: mean t_mu_zero per pattern × λ
    pivot = summary_df.groupby(["pattern", "lambda"])["t_mu_zero"].mean().unstack("lambda")
    pivot = pivot.reindex(patterns)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Heatmap 1: t_mu_zero
    im1 = axes[0].imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    axes[0].set_xticks(range(len(lambdas)))
    axes[0].set_xticklabels([f"{l:.2f}" for l in lambdas])
    axes[0].set_yticks(range(len(patterns)))
    axes[0].set_yticklabels(patterns)
    axes[0].set_xlabel("λ (cost sensitivity)")
    axes[0].set_ylabel("Pattern")
    axes[0].set_title("Mean turn where ΔU(t) ≤ 0", fontweight="bold")
    plt.colorbar(im1, ax=axes[0], label="Turn")

    # Add text annotations
    for i in range(len(patterns)):
        for j in range(len(lambdas)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                axes[0].text(j, i, f"{val:.1f}", ha="center", va="center",
                             fontsize=9, color="black" if val < pivot.values.max() * 0.7 else "white")

    # Heatmap 2: quality at t_mu_zero vs t_optimal
    # Compare: quality preserved when stopping at ΔU≤0
    quality_preserved = summary_df.groupby(["pattern", "lambda"]).apply(
        lambda g: (g["q_actual"].mean() / g["q_optimal"].mean()) if g["q_optimal"].mean() > 0 else 1.0,
        include_groups=False,
    ).unstack("lambda")
    quality_preserved = quality_preserved.reindex(patterns)

    im2 = axes[1].imshow(quality_preserved.values, aspect="auto", cmap="RdYlGn", vmin=0.7, vmax=1.0)
    axes[1].set_xticks(range(len(lambdas)))
    axes[1].set_xticklabels([f"{l:.2f}" for l in lambdas])
    axes[1].set_yticks(range(len(patterns)))
    axes[1].set_yticklabels(patterns)
    axes[1].set_xlabel("λ (cost sensitivity)")
    axes[1].set_ylabel("Pattern")
    axes[1].set_title("Quality Preservation (Q_actual / Q_optimal)", fontweight="bold")
    plt.colorbar(im2, ax=axes[1], label="Ratio")

    for i in range(len(patterns)):
        for j in range(len(lambdas)):
            val = quality_preserved.values[i, j]
            if not np.isnan(val):
                axes[1].text(j, i, f"{val:.2f}", ha="center", va="center",
                             fontsize=9)

    plt.tight_layout()
    output_path = FIGURES_DIR / "fig_marginal_utility_heatmap.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"[OK] Saved: {output_path}")
    plt.close()


def plot_utility_curves(mu_df, lambda_val=0.1):
    """Plot absolute U(t) and ΔU(t) side by side for each pattern."""
    patterns = sorted(mu_df["pattern"].unique())
    subset = mu_df[mu_df["lambda"] == lambda_val]

    fig, axes = plt.subplots(2, len(patterns), figsize=(4 * len(patterns), 8),
                             sharex="col")

    for idx, pattern in enumerate(patterns):
        pat_data = subset[subset["pattern"] == pattern]
        cat = pat_data["pattern_category"].iloc[0]
        color = CATEGORY_COLORS.get(cat, "#999999")

        # Top row: U(t) = Q(t) - λC(t)
        ax_top = axes[0, idx]
        for task_id, run in pat_data.groupby("task_id"):
            run = run.sort_values("turn_index")
            ax_top.plot(run["turn_index"], run["U_t"],
                        color=color, alpha=0.2, linewidth=0.8)
        mean_U = pat_data.groupby("turn_index")["U_t"].mean()
        ax_top.plot(mean_U.index, mean_U.values, color=color, linewidth=2.5)
        # Mark peak
        peak_t = mean_U.idxmax()
        ax_top.axvline(x=peak_t, color="red", linestyle="--", alpha=0.5)
        ax_top.plot(peak_t, mean_U[peak_t], "r*", markersize=12)
        ax_top.set_title(f"{pattern}", fontsize=11, fontweight="bold")
        if idx == 0:
            ax_top.set_ylabel("U(t) = Q(t) - λC(t)")
        ax_top.grid(True, alpha=0.3)

        # Bottom row: ΔU(t)
        ax_bot = axes[1, idx]
        for task_id, run in pat_data.groupby("task_id"):
            run = run.sort_values("turn_index")
            ax_bot.plot(run["turn_index"], run["delta_u"],
                        color=color, alpha=0.2, linewidth=0.8)
        mean_dU = pat_data.groupby("turn_index")["delta_u"].mean()
        ax_bot.plot(mean_dU.index, mean_dU.values, color=color, linewidth=2.5)
        ax_bot.axhline(y=0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
        ax_bot.set_xlabel("Agent Turn")
        if idx == 0:
            ax_bot.set_ylabel("ΔU(t)")
        ax_bot.grid(True, alpha=0.3)

    fig.suptitle(f"Utility Analysis: U(t) vs ΔU(t)  [λ={lambda_val}]",
                 fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    output_path = FIGURES_DIR / "fig_utility_U_vs_dU.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"[OK] Saved: {output_path}")
    plt.close()


def print_summary_table(summary_df, lambda_val=0.1):
    """Print summary statistics for a given λ."""
    sub = summary_df[summary_df["lambda"] == lambda_val]

    print(f"\n{'='*80}")
    print(f"  Marginal Utility Summary (λ = {lambda_val})")
    print(f"{'='*80}")
    print(f"{'Pattern':<10} {'Cat':<4} {'t_opt':>5} {'t_ΔU≤0':>6} {'t_act':>5} "
          f"{'Q_opt':>5} {'Q_act':>5} {'Q_loss':>6} {'Regret':>6} {'U_peak':>6}")
    print("-" * 80)

    for pattern in sorted(sub["pattern"].unique()):
        p_data = sub[sub["pattern"] == pattern]
        cat = p_data["pattern_category"].iloc[0]
        t_opt = p_data["t_optimal"].mean()
        t_mu = p_data["t_mu_zero"].mean()
        t_act = p_data["t_actual"].mean()
        q_opt = p_data["q_optimal"].mean()
        q_act = p_data["q_actual"].mean()
        q_loss = p_data["q_loss"].mean()
        regret = p_data["regret"].mean()
        u_peak = p_data["U_peak"].mean()

        print(f"{pattern:<10} {cat:<4} {t_opt:>5.1f} {t_mu:>6.1f} {t_act:>5.1f} "
              f"{q_opt:>5.2f} {q_act:>5.2f} {q_loss:>6.2f} {regret:>6.1f} {u_peak:>6.2f}")

    # Key insight: correlation between t_mu_zero and t_optimal
    from scipy import stats
    t_opt_means = sub.groupby("pattern")["t_optimal"].mean()
    t_mu_means = sub.groupby("pattern")["t_mu_zero"].mean()
    if len(t_opt_means) > 2:
        r, p = stats.spearmanr(t_opt_means, t_mu_means)
        print(f"\nSpearman correlation (t_optimal vs t_ΔU≤0): r={r:.3f}, p={p:.4f}")

    # Across-λ analysis
    print(f"\n--- λ Sensitivity ---")
    for lam in sorted(summary_df["lambda"].unique()):
        lam_data = summary_df[summary_df["lambda"] == lam]
        mean_mu = lam_data["t_mu_zero"].mean()
        mean_reg = lam_data["regret"].mean()
        mean_loss = lam_data["q_loss"].mean()
        print(f"  λ={lam:.2f}: mean t_ΔU≤0={mean_mu:.1f}, regret={mean_reg:.1f}, Q_loss={mean_loss:.3f}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df = load_data()

    # 2. Compute marginal utility
    mu_df = compute_marginal_utility(df)

    # 3. Save
    mu_df.to_csv(RESULTS_DIR / "marginal_utility.csv", index=False, encoding="utf-8")
    print(f"[OK] Saved: {RESULTS_DIR / 'marginal_utility.csv'}")

    # 4. Find optimal stopping points
    summary_df = find_optimal_stops(mu_df)
    summary_df.to_csv(RESULTS_DIR / "marginal_utility_summary.csv", index=False, encoding="utf-8")
    print(f"[OK] Saved: {RESULTS_DIR / 'marginal_utility_summary.csv'}")

    # 5. Print summary tables
    for lam in [0.0, 0.1, 0.2]:
        print_summary_table(summary_df, lam)

    # 6. Generate figures
    plot_marginal_utility_curves(mu_df, lambda_val=0.1)
    plot_lambda_sensitivity(summary_df)
    plot_utility_curves(mu_df, lambda_val=0.1)

    print(f"\n[DONE] Marginal utility analysis complete!")


if __name__ == "__main__":
    main()
