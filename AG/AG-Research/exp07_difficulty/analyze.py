"""
Experiment 07 Analysis: 6-Model Difficulty x Pattern Interaction
================================================================
Extends single-model (Haiku) analysis to 6 models:
  Haiku 4.6, Opus 4.6, GPT-4o-mini, GPT-5.4, Grok 3 Mini, Gemini 2.0 Flash

Key findings:
  - Solo dominance on easy tasks: 5/6 models (GPT-5.4 ties with Refl-2)
  - Multi-agent benefit on hard tasks depends on base model capability
  - Feedback (refl2) advantage: strongest for Opus (+0.60 on hard)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats as sp_stats

from config import RESULTS_DIR, BASE_DIR

OUTPUT_DIR = RESULTS_DIR / "exp07"
FIGURES_DIR = BASE_DIR / "figures"

DIFFICULTY_ORDER = ["easy", "medium", "hard"]
PATTERN_ORDER = ["solo", "swm3", "sel3", "refl2", "debate3"]
PATTERN_LABELS = {
    "solo": "Solo (S)",
    "swm3": "Swarm-3 (B2)",
    "sel3": "Selector-3 (B1)",
    "refl2": "Reflect-2 (C)",
    "debate3": "Debate-3 (C)",
}

# Model directories — keyed by display name
MODEL_DIRS = {
    "Haiku 4.6": RESULTS_DIR / "exp07",
    "GPT-4o-mini": RESULTS_DIR / "exp07_gpt_4o_mini",
    "GPT-5.4": RESULTS_DIR / "exp07_gpt_5_4",
    "Grok 3 Mini": RESULTS_DIR / "exp07_grok_3_mini_fast",
    "Gemini 2.0 Flash": RESULTS_DIR / "exp07_gemini_2_0_flash",
    "Opus 4.6": RESULTS_DIR / "exp07_claude_opus_4_5_20251101",
}

# Ordered roughly by capability (weak → strong) for display
MODEL_ORDER = ["Grok 3 Mini", "GPT-4o-mini", "Haiku 4.6", "Gemini 2.0 Flash", "GPT-5.4", "Opus 4.6"]

MODEL_COLORS = {
    "Haiku 4.6": "#4C78A8",
    "GPT-4o-mini": "#F58518",
    "GPT-5.4": "#54A24B",
    "Grok 3 Mini": "#E45756",
    "Gemini 2.0 Flash": "#B279A2",
    "Opus 4.6": "#72B7B2",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_task_meta() -> pd.DataFrame:
    tasks_path = BASE_DIR / "task_suite_difficulty.json"
    with open(tasks_path, encoding="utf-8") as f:
        tasks = json.load(f)
    meta = pd.DataFrame(tasks)[["id", "difficulty", "domain"]]
    return meta.rename(columns={"id": "task_id"})


def load_all_data() -> pd.DataFrame:
    """Load scored results from all 6 model directories."""
    task_meta = _load_task_meta()
    frames = []
    for model_name, model_dir in MODEL_DIRS.items():
        scores_path = model_dir / "scores.csv"
        if not scores_path.exists():
            print(f"  WARNING: {scores_path} not found, skipping {model_name}")
            continue
        df = pd.read_csv(scores_path)
        df["model"] = model_name
        df = df.merge(task_meta, on="task_id", how="left")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_data() -> pd.DataFrame:
    """Load Haiku-only data (backward compat)."""
    task_meta = _load_task_meta()
    df = pd.read_csv(OUTPUT_DIR / "scores.csv")
    return df.merge(task_meta, on="task_id", how="left")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _eta_sq_h(h: float, k: int, n: int) -> float:
    """Epsilon-squared effect size for Kruskal-Wallis."""
    return max(0, (h - k + 1) / (n - k)) if n > k else 0.0


def compute_solo_advantage(df: pd.DataFrame) -> pd.DataFrame:
    """For each model x difficulty: solo_mean vs best_multi_mean."""
    rows = []
    for model in MODEL_ORDER:
        for diff in DIFFICULTY_ORDER:
            sub = df[(df["model"] == model) & (df["difficulty"] == diff)]
            if sub.empty:
                continue
            by_pat = sub.groupby("pattern")["overall"].mean()
            solo_mean = by_pat.get("solo", np.nan)
            multi_pats = [p for p in PATTERN_ORDER if p != "solo" and p in by_pat.index]
            if not multi_pats:
                continue
            best_multi = by_pat[multi_pats].max()
            best_multi_name = by_pat[multi_pats].idxmax()
            multi_avg = by_pat[multi_pats].mean()
            rows.append({
                "model": model,
                "difficulty": diff,
                "solo_mean": round(float(solo_mean), 2),
                "best_multi": round(float(best_multi), 2),
                "best_multi_name": best_multi_name,
                "multi_avg": round(float(multi_avg), 2),
                "solo_advantage": round(float(solo_mean - best_multi), 2),
                "solo_vs_multi_avg": round(float(solo_mean - multi_avg), 2),
                "solo_is_best": bool(solo_mean >= best_multi),
            })
    return pd.DataFrame(rows)


def anova_per_model(df: pd.DataFrame) -> pd.DataFrame:
    """Kruskal-Wallis tests per model + combined ('ALL')."""
    results = []
    for model in MODEL_ORDER + ["ALL"]:
        sub = df if model == "ALL" else df[df["model"] == model]
        n = len(sub)

        # Difficulty main effect
        groups = [g["overall"].values for _, g in sub.groupby("difficulty")]
        if len(groups) > 1:
            h, p = sp_stats.kruskal(*groups)
            eta = _eta_sq_h(h, len(groups), n)
            results.append({
                "model": model, "test": "difficulty_main",
                "H": round(h, 2), "p": round(p, 6),
                "eta_sq": round(eta, 3), "n": n,
            })

        # Pattern main effect
        groups = [g["overall"].values for _, g in sub.groupby("pattern")]
        if len(groups) > 1:
            h, p = sp_stats.kruskal(*groups)
            eta = _eta_sq_h(h, len(groups), n)
            results.append({
                "model": model, "test": "pattern_main",
                "H": round(h, 2), "p": round(p, 6),
                "eta_sq": round(eta, 3), "n": n,
            })

        # Pattern within each difficulty
        for diff_level in DIFFICULTY_ORDER:
            sub_d = sub[sub["difficulty"] == diff_level]
            groups = [g["overall"].values for _, g in sub_d.groupby("pattern")]
            if len(groups) > 1 and all(len(g) > 0 for g in groups):
                h, p = sp_stats.kruskal(*groups)
                eta = _eta_sq_h(h, len(groups), len(sub_d))
                results.append({
                    "model": model, "test": f"pattern_within_{diff_level}",
                    "H": round(h, 2), "p": round(p, 6),
                    "eta_sq": round(eta, 3), "n": len(sub_d),
                })

    return pd.DataFrame(results)


def refl2_vs_solo_tests(df: pd.DataFrame) -> list[dict]:
    """Mann-Whitney U: refl2 vs solo at each difficulty, per model."""
    rows = []
    for model in MODEL_ORDER:
        for diff in DIFFICULTY_ORDER:
            sub = df[(df["model"] == model) & (df["difficulty"] == diff)]
            solo_v = sub[sub["pattern"] == "solo"]["overall"].values
            refl2_v = sub[sub["pattern"] == "refl2"]["overall"].values
            if len(solo_v) == 0 or len(refl2_v) == 0:
                continue
            delta = float(np.mean(refl2_v) - np.mean(solo_v))
            row = {
                "model": model, "difficulty": diff,
                "solo_mean": round(float(np.mean(solo_v)), 2),
                "refl2_mean": round(float(np.mean(refl2_v)), 2),
                "delta": round(delta, 2),
                "n_solo": len(solo_v), "n_refl2": len(refl2_v),
            }
            if len(solo_v) >= 3 and len(refl2_v) >= 3:
                u, p = sp_stats.mannwhitneyu(refl2_v, solo_v, alternative="two-sided")
                pooled = np.sqrt((np.var(solo_v, ddof=1) + np.var(refl2_v, ddof=1)) / 2)
                d = delta / pooled if pooled > 0 else 0
                row.update({"U": round(float(u), 1), "p": round(float(p), 4),
                            "cohen_d": round(float(d), 2)})
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def plot_composite(df: pd.DataFrame, solo_adv: pd.DataFrame) -> None:
    """Create 4-panel figure: fig10_difficulty_analysis.png."""
    fig = plt.figure(figsize=(14, 11))
    gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.30)

    x_pos = np.arange(len(DIFFICULTY_ORDER))

    # ── Panel A: Solo advantage heatmap ──
    ax = fig.add_subplot(gs[0, 0])
    pivot = solo_adv.pivot(index="model", columns="difficulty", values="solo_advantage")
    pivot = pivot.reindex(index=MODEL_ORDER, columns=DIFFICULTY_ORDER)
    sns.heatmap(
        pivot, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
        vmin=-1.2, vmax=1.5, ax=ax,
        cbar_kws={"label": "Solo - Best Multi", "shrink": 0.8},
    )
    ax.set_title("(a) Solo Advantage (Model x Difficulty)", fontsize=11, fontweight="bold")
    ax.set_ylabel("")
    ax.set_xlabel("")
    # Black border on cells where solo wins
    for i, model in enumerate(MODEL_ORDER):
        for j, diff in enumerate(DIFFICULTY_ORDER):
            row = solo_adv[(solo_adv["model"] == model) & (solo_adv["difficulty"] == diff)]
            if not row.empty and row.iloc[0]["solo_is_best"]:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                                           edgecolor="black", lw=2.5))

    # ── Panel B: Multi-agent advantage lines ──
    ax = fig.add_subplot(gs[0, 1])
    for model in MODEL_ORDER:
        sub = solo_adv[solo_adv["model"] == model]
        vals = sub.set_index("difficulty").reindex(DIFFICULTY_ORDER)["solo_vs_multi_avg"]
        multi_adv = -vals  # positive = multi better
        ax.plot(x_pos, multi_adv, marker="o", label=model,
                color=MODEL_COLORS[model], linewidth=2, markersize=7)
    ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.capitalize() for d in DIFFICULTY_ORDER])
    ax.set_ylabel("Multi-Agent Advantage\n(multi_avg - solo)")
    ax.set_title("(b) Multi-Agent Advantage by Difficulty", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, loc="best")

    # ── Panel C: Refl-2 vs Solo delta ──
    ax = fig.add_subplot(gs[1, 0])
    for model in MODEL_ORDER:
        deltas = []
        for diff in DIFFICULTY_ORDER:
            sub = df[(df["model"] == model) & (df["difficulty"] == diff)]
            solo_m = sub[sub["pattern"] == "solo"]["overall"].mean()
            refl2_m = sub[sub["pattern"] == "refl2"]["overall"].mean()
            deltas.append(refl2_m - solo_m)
        ax.plot(x_pos, deltas, marker="s", label=model,
                color=MODEL_COLORS[model], linewidth=2, markersize=7)
    ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.capitalize() for d in DIFFICULTY_ORDER])
    ax.set_ylabel("Refl-2 - Solo ($\\Delta$ quality)")
    ax.set_title("(c) Feedback Advantage (Refl-2 vs Solo)", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, loc="best")

    # ── Panel D: Solo dominance frequency ──
    ax = fig.add_subplot(gs[1, 1])
    counts = []
    for diff in DIFFICULTY_ORDER:
        sub = solo_adv[solo_adv["difficulty"] == diff]
        counts.append(int(sub["solo_is_best"].sum()))
    bar_colors = ["#54A24B", "#EECA3B", "#E45756"]
    bars = ax.bar(x_pos, counts, color=bar_colors, edgecolor="black", linewidth=0.5, width=0.55)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.capitalize() for d in DIFFICULTY_ORDER])
    n_models = len(MODEL_ORDER)
    ax.set_ylabel(f"Models where Solo is Best (out of {n_models})")
    ax.set_ylim(0, n_models + 0.8)
    ax.set_yticks(range(n_models + 1))
    ax.set_title("(d) Solo Dominance Frequency", fontsize=11, fontweight="bold")
    for bar, c in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                f"{c}/{n_models}", ha="center", fontweight="bold", fontsize=13)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig10_difficulty_analysis.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure saved: {out_path}")


# ---------------------------------------------------------------------------
# LaTeX table generation
# ---------------------------------------------------------------------------

def generate_appendix_table(df: pd.DataFrame) -> str:
    """6-model x 3-difficulty x 5-pattern LaTeX table for appendix."""
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Six-model difficulty $\\times$ pattern quality "
        "(mean G-Eval overall $\\pm$ SD). Bold = highest per row. "
        "Models ordered by approximate capability (weak $\\to$ strong). "
        "Haiku/GPT-4o-mini: 3 repeats per cell; others: 1 repeat.}",
        "\\label{tab:difficulty_6model}",
        "\\vspace{-2mm}",
        "{\\footnotesize",
        "\\begin{tabular}{@{}llccccc@{}}",
        "\\toprule",
        "\\textbf{Model} & \\textbf{Diff.} & \\textbf{Solo} & "
        "\\textbf{Swm-3} & \\textbf{Sel-3} & \\textbf{Refl-2} & "
        "\\textbf{Deb-3} \\\\",
        "\\midrule",
    ]

    for i, model in enumerate(MODEL_ORDER):
        for j, diff in enumerate(DIFFICULTY_ORDER):
            sub = df[(df["model"] == model) & (df["difficulty"] == diff)]
            vals = {}
            stds = {}
            for pat in PATTERN_ORDER:
                psub = sub[sub["pattern"] == pat]["overall"]
                vals[pat] = psub.mean() if len(psub) > 0 else np.nan
                stds[pat] = psub.std() if len(psub) > 1 else 0.0

            valid = [v for v in vals.values() if not np.isnan(v)]
            best_val = max(valid) if valid else 0

            cells = []
            for pat in PATTERN_ORDER:
                v, s = vals[pat], stds[pat]
                if np.isnan(v):
                    cells.append("---")
                elif abs(v - best_val) < 0.005:
                    if s > 0:
                        cells.append(f"\\textbf{{{v:.2f}}}$\\pm${s:.2f}")
                    else:
                        cells.append(f"\\textbf{{{v:.2f}}}")
                else:
                    if s > 0:
                        cells.append(f"{v:.2f}$\\pm${s:.2f}")
                    else:
                        cells.append(f"{v:.2f}")

            mlabel = model if j == 0 else ""
            dlabel = diff.capitalize()
            lines.append(f"{mlabel} & {dlabel} & " + " & ".join(cells) + " \\\\")

        if i < len(MODEL_ORDER) - 1:
            lines.append("\\midrule")

    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "}",
        "\\end{table*}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Exp07: 6-Model Difficulty x Pattern Interaction Analysis")
    print("=" * 70)

    # 1. Load
    print("\n[1] Loading data from 6 models...")
    df = load_all_data()
    for model in MODEL_ORDER:
        n = len(df[df["model"] == model])
        print(f"  {model}: {n} rows")
    print(f"  TOTAL: {len(df)} rows")

    # 2. Per-model quality summary
    print("\n[2] Per-model quality summary...")
    for model in MODEL_ORDER:
        print(f"\n  === {model} ===")
        for diff in DIFFICULTY_ORDER:
            sub = df[(df["model"] == model) & (df["difficulty"] == diff)]
            by_pat = sub.groupby("pattern")["overall"].mean()
            vals = " | ".join(f"{p}={by_pat.get(p, 0):.2f}" for p in PATTERN_ORDER)
            best = by_pat.idxmax() if not by_pat.empty else "?"
            print(f"    {diff:6s}: {vals}  (best={best})")

    # 3. Solo advantage
    print("\n[3] Solo advantage matrix...")
    solo_adv = compute_solo_advantage(df)
    solo_adv.to_csv(OUTPUT_DIR / "solo_advantage_6model.csv", index=False)

    for _, row in solo_adv.iterrows():
        marker = "+" if row["solo_is_best"] else "-"
        print(f"  {row['model']:12s} {row['difficulty']:6s}: "
              f"solo={row['solo_mean']:.2f}  best_multi={row['best_multi']:.2f}"
              f"({row['best_multi_name']:8s})  delta={row['solo_advantage']:+.2f} [{marker}]")

    print("\n  Solo Dominance Frequency:")
    for diff in DIFFICULTY_ORDER:
        sub = solo_adv[solo_adv["difficulty"] == diff]
        count = int(sub["solo_is_best"].sum())
        models = list(sub[sub["solo_is_best"]]["model"])
        print(f"    {diff}: {count}/{len(MODEL_ORDER)}  ({', '.join(models)})")

    # 4. Kruskal-Wallis per model
    print("\n[4] Kruskal-Wallis tests...")
    anova_df = anova_per_model(df)
    anova_df.to_csv(OUTPUT_DIR / "anova_6model.csv", index=False)
    for _, row in anova_df.iterrows():
        sig = ("***" if row["p"] < 0.001 else "**" if row["p"] < 0.01
               else "*" if row["p"] < 0.05 else "ns")
        print(f"  [{row['model']:12s}] {row['test']:25s}: "
              f"H={row['H']:7.2f}  p={row['p']:.6f}  eta2={row['eta_sq']:.3f} {sig}")

    # 5. Refl-2 vs Solo pairwise
    print("\n[5] Refl-2 vs Solo at each difficulty...")
    refl2_rows = refl2_vs_solo_tests(df)
    refl2_df = pd.DataFrame(refl2_rows)
    refl2_df.to_csv(OUTPUT_DIR / "refl2_vs_solo_6model.csv", index=False)
    for r in refl2_rows:
        extra = ""
        if "U" in r:
            extra = f"  U={r['U']:.0f} p={r['p']:.4f} d={r['cohen_d']:.2f}"
        print(f"  {r['model']:12s} {r['difficulty']:6s}: "
              f"refl2={r['refl2_mean']:.2f} solo={r['solo_mean']:.2f} "
              f"delta={r['delta']:+.2f}{extra}")

    # 6. Figure
    print("\n[6] Generating figure...")
    plot_composite(df, solo_adv)

    # 7. LaTeX appendix table
    print("\n[7] LaTeX appendix table...")
    table_tex = generate_appendix_table(df)
    tex_path = OUTPUT_DIR / "table_6model.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(table_tex)
    print(f"  Saved: {tex_path}")

    # 8. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    easy_c = int(solo_adv[solo_adv["difficulty"] == "easy"]["solo_is_best"].sum())
    med_c = int(solo_adv[solo_adv["difficulty"] == "medium"]["solo_is_best"].sum())
    hard_c = int(solo_adv[solo_adv["difficulty"] == "hard"]["solo_is_best"].sum())
    print(f"  Easy:   Solo best in {easy_c}/6 models")
    print(f"  Medium: Solo best in {med_c}/6 models")
    print(f"  Hard:   Solo best in {hard_c}/6 models")

    # Combined Kruskal-Wallis
    all_row = anova_df[(anova_df["model"] == "ALL") & (anova_df["test"] == "difficulty_main")]
    if not all_row.empty:
        r = all_row.iloc[0]
        print(f"\n  Combined difficulty main: H={r['H']:.2f}, p={r['p']:.6f}, eta2={r['eta_sq']:.3f}")
    all_pat = anova_df[(anova_df["model"] == "ALL") & (anova_df["test"] == "pattern_main")]
    if not all_pat.empty:
        r = all_pat.iloc[0]
        print(f"  Combined pattern main:    H={r['H']:.2f}, p={r['p']:.6f}, eta2={r['eta_sq']:.3f}")

    print(f"\n  Outputs: {OUTPUT_DIR}")
    print(f"  Figure:  {FIGURES_DIR / 'fig10_difficulty_analysis.png'}")


if __name__ == "__main__":
    main()
