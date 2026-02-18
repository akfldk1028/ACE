"""
Domain × Pattern Cross-Analysis
================================
Analyzes exp01 v2 results by domain and pattern to answer:
1. Which patterns are domain-invariant vs domain-sensitive?
2. Does debate excel in argumentative domains (law, philosophy)?
3. Does sequential chain suffice for factual domains?
4. Which domain × pattern combinations are outliers?

Reads: results/exp01/summary.csv (v2: 8 patterns × 25 tasks)
       task_suite.json (domain mapping)
Outputs: figures/fig_domain_pattern_heatmap.png
         results/exp01/domain_analysis.csv
         Statistical test results (Kruskal-Wallis per domain)

Usage:
  cd AG/AG-Research && C:/Python313/python analyze_domain_pattern.py
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
from scipy import stats

from config import (
    CATEGORY_COLORS,
    CATEGORY_NAMES,
    PATTERN_CATEGORY,
    PATTERNS_REPRESENTATIVE,
    RESULTS_DIR,
)

BASE_DIR = Path(__file__).resolve().parent
FIGURES_DIR = BASE_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Domain order for consistent display
DOMAIN_ORDER = [
    "science", "CS", "history", "philosophy",
    "law_politics", "gaming", "engineering", "business", "medicine",
]
DOMAIN_SHORT = {
    "science": "Sci", "CS": "CS", "history": "Hist",
    "philosophy": "Phil", "law_politics": "Law",
    "gaming": "Game", "engineering": "Eng",
    "business": "Biz", "medicine": "Med",
}

# Pattern display order (by category)
PATTERN_ORDER = ["rr3", "sel3", "sel4", "swm3", "swm4", "refl2", "debate3", "pipe"]


def load_data():
    """Load exp01 v2 results and task metadata."""
    # Try v2 summary first, then checkpoint
    for fname in ["summary.csv", "summary_partial.csv"]:
        csv_path = RESULTS_DIR / "exp01" / fname
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            print(f"[OK] Loaded {len(df)} rows from {fname}")
            break
    else:
        # Try checkpoint.json
        ckpt = RESULTS_DIR / "exp01" / "checkpoint.json"
        if ckpt.exists():
            with open(ckpt, encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            print(f"[OK] Loaded {len(df)} rows from checkpoint.json")
        else:
            print("[ERROR] No exp01 results found. Run exp01 first.")
            return None, None

    # Load task metadata for domain mapping
    task_path = BASE_DIR / "task_suite.json"
    with open(task_path, encoding="utf-8") as f:
        tasks = json.load(f)

    task_map = {t["id"]: t for t in tasks}
    return df, task_map


def enrich_with_domain(df, task_map):
    """Add domain and cognitive_type columns from task metadata."""
    df["domain"] = df["task_id"].map(lambda x: task_map.get(x, {}).get("domain", "unknown"))
    df["cognitive_type"] = df["task_id"].map(lambda x: task_map.get(x, {}).get("category", "unknown"))
    df["difficulty"] = df["task_id"].map(lambda x: task_map.get(x, {}).get("difficulty", "unknown"))
    return df


def filter_successful(df):
    """Keep only successful runs (no errors)."""
    if "error" in df.columns:
        mask = df["error"].isna() | (df["error"] == "") | (df["error"] == "None")
        df_ok = df[mask].copy()
        n_err = len(df) - len(df_ok)
        if n_err > 0:
            print(f"[INFO] Filtered out {n_err} error runs, keeping {len(df_ok)}")
        return df_ok
    return df


def domain_pattern_summary(df):
    """Compute domain × pattern statistics."""
    # Group by domain × pattern
    grouped = df.groupby(["domain", "pattern"]).agg(
        n_runs=("total_tokens", "count"),
        mean_tokens=("total_tokens", "mean"),
        std_tokens=("total_tokens", "std"),
        mean_time=("duration_sec", "mean"),
        mean_turns=("turn_count", "mean"),
        mean_tokens_out=("total_tokens_out", "mean"),
    ).reset_index()

    # Compute tokens per turn
    grouped["tokens_per_turn"] = grouped["mean_tokens"] / grouped["mean_turns"].clip(lower=1)

    # Add category
    grouped["category"] = grouped["pattern"].map(PATTERN_CATEGORY)

    return grouped


def plot_heatmap(summary_df, metric="mean_tokens", title_suffix="Total Tokens"):
    """Domain × Pattern heatmap."""
    # Pivot for heatmap
    patterns = [p for p in PATTERN_ORDER if p in summary_df["pattern"].unique()]
    domains = [d for d in DOMAIN_ORDER if d in summary_df["domain"].unique()]

    pivot = summary_df.pivot_table(
        index="domain", columns="pattern", values=metric, aggfunc="mean"
    )
    # Reorder
    pivot = pivot.reindex(index=domains, columns=patterns)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Use short domain names for y-axis
    row_labels = [DOMAIN_SHORT.get(d, d) for d in pivot.index]

    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    # Labels
    ax.set_xticks(range(len(patterns)))
    ax.set_xticklabels(patterns, fontsize=11)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=11)

    # Category color bars on top
    for j, p in enumerate(patterns):
        cat = PATTERN_CATEGORY.get(p, "?")
        color = CATEGORY_COLORS.get(cat, "#999")
        ax.plot(j, -0.7, marker='s', color=color, markersize=12, clip_on=False)
        ax.text(j, -1.1, cat, ha='center', va='center', fontsize=9, fontweight='bold')

    # Annotate cells
    for i in range(len(row_labels)):
        for j in range(len(patterns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = "white" if val > pivot.values[~np.isnan(pivot.values)].mean() * 1.3 else "black"
                ax.text(j, i, f"{val:.0f}", ha='center', va='center',
                        fontsize=9, color=text_color, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label(title_suffix, fontsize=11)

    ax.set_title(f"Domain × Pattern: {title_suffix}", fontsize=14, fontweight='bold', pad=30)
    ax.set_xlabel("Pattern", fontsize=12)
    ax.set_ylabel("Domain", fontsize=12)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    safe_metric = metric.replace("/", "_")
    output_path = FIGURES_DIR / f"fig_domain_pattern_{safe_metric}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[OK] Saved: {output_path}")
    plt.close()


def statistical_tests(df):
    """Per-domain Kruskal-Wallis test: does pattern matter within each domain?"""
    print("\n=== Statistical Tests: Pattern Effect per Domain ===")
    print(f"{'Domain':<15} {'H stat':>8} {'p-value':>10} {'Sig':>5} {'Best Pattern':<12} {'Worst Pattern':<12}")
    print("-" * 75)

    results = []
    for domain in DOMAIN_ORDER:
        dom_data = df[df["domain"] == domain]
        if dom_data.empty:
            continue

        groups = [g["total_tokens"].values for _, g in dom_data.groupby("pattern") if len(g) > 0]

        if len(groups) < 2:
            continue

        h_stat, p_val = stats.kruskal(*groups)
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"

        means = dom_data.groupby("pattern")["total_tokens"].mean()
        best = means.idxmin()
        worst = means.idxmax()

        print(f"{domain:<15} {h_stat:>8.1f} {p_val:>10.4f} {sig:>5} {best:<12} {worst:<12}")

        results.append({
            "domain": domain,
            "h_stat": round(h_stat, 2),
            "p_value": round(p_val, 4),
            "significant": sig != "ns",
            "best_pattern": best,
            "worst_pattern": worst,
            "best_tokens": round(means[best]),
            "worst_tokens": round(means[worst]),
        })

    # Cross-pattern test: which patterns are domain-invariant?
    print("\n=== Pattern Domain-Sensitivity (CV of tokens across domains) ===")
    print(f"{'Pattern':<10} {'Mean':>8} {'Std':>8} {'CV':>8} {'Interpretation':<25}")
    print("-" * 65)

    for p in PATTERN_ORDER:
        p_data = df[df["pattern"] == p]
        if p_data.empty:
            continue
        domain_means = p_data.groupby("domain")["total_tokens"].mean()
        cv = domain_means.std() / domain_means.mean() if domain_means.mean() > 0 else 0
        interp = "Domain-invariant" if cv < 0.3 else "Moderate sensitivity" if cv < 0.5 else "Domain-sensitive"
        print(f"{p:<10} {domain_means.mean():>8.0f} {domain_means.std():>8.0f} {cv:>8.2f} {interp:<25}")

    return results


def domain_specific_findings(df):
    """Print key domain-specific findings for the paper."""
    print("\n=== Key Domain-Specific Findings ===\n")

    # 1. Argumentative domains (law, philosophy) - does debate/reflection shine?
    arg_domains = ["law_politics", "philosophy"]
    arg_data = df[df["domain"].isin(arg_domains)]
    if not arg_data.empty:
        arg_means = arg_data.groupby("pattern")["total_tokens"].mean().sort_values()
        print("Finding: Argumentative domains (law, philosophy)")
        print(f"  Most efficient: {arg_means.index[0]} ({arg_means.iloc[0]:.0f} tokens)")
        print(f"  Least efficient: {arg_means.index[-1]} ({arg_means.iloc[-1]:.0f} tokens)")
        # Check if debate/refl are relatively better here
        debate_rank = list(arg_means.index).index("debate3") if "debate3" in arg_means.index else -1
        print(f"  debate3 rank: {debate_rank + 1}/{len(arg_means)} (1=best)")

    # 2. Factual/technical domains - does sequential chain suffice?
    fact_data = df[(df["domain"].isin(["science", "CS"])) & (df["cognitive_type"] == "factual")]
    if not fact_data.empty:
        fact_means = fact_data.groupby("pattern")["total_tokens"].mean().sort_values()
        print(f"\nFinding: Factual tasks in science/CS domains")
        print(f"  Most efficient: {fact_means.index[0]} ({fact_means.iloc[0]:.0f} tokens)")
        print(f"  rr3 cost: {fact_means.get('rr3', 'N/A'):.0f} tokens")

    # 3. Creative domains - which patterns generate most content?
    crea_data = df[df["cognitive_type"] == "creative"]
    if not crea_data.empty:
        crea_means = crea_data.groupby("pattern")["total_tokens_out"].mean().sort_values(ascending=False)
        print(f"\nFinding: Creative tasks - output volume")
        print(f"  Most output: {crea_means.index[0]} ({crea_means.iloc[0]:.0f} output tokens)")
        print(f"  Least output: {crea_means.index[-1]} ({crea_means.iloc[-1]:.0f} output tokens)")

    # 4. Most expensive domain overall
    domain_means = df.groupby("domain")["total_tokens"].mean().sort_values(ascending=False)
    print(f"\nFinding: Domain cost ranking")
    for d in domain_means.index:
        print(f"  {d}: {domain_means[d]:.0f} avg tokens")


def main():
    df, task_map = load_data()
    if df is None:
        return

    df = enrich_with_domain(df, task_map)
    df = filter_successful(df)

    # Filter to representative patterns only
    df = df[df["pattern"].isin(PATTERNS_REPRESENTATIVE)]
    print(f"[INFO] Analyzing {len(df)} runs across {df['domain'].nunique()} domains, {df['pattern'].nunique()} patterns")

    # Summary stats
    summary = domain_pattern_summary(df)

    # Save summary CSV
    out_csv = RESULTS_DIR / "exp01" / "domain_analysis.csv"
    summary.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] Saved: {out_csv}")

    # Heatmaps
    plot_heatmap(summary, "mean_tokens", "Mean Total Tokens")
    plot_heatmap(summary, "mean_time", "Mean Duration (sec)")
    plot_heatmap(summary, "tokens_per_turn", "Tokens per Turn")

    # Statistical tests
    test_results = statistical_tests(df)

    # Key findings
    domain_specific_findings(df)

    print("\n=== Domain × Pattern Analysis Complete ===")


if __name__ == "__main__":
    main()
