"""
Compute standard deviations and 95% confidence intervals for key paper claims.
Output: paper_stats.txt
"""
import pandas as pd
import numpy as np
from scipy import stats
import sys

OUT = "D:/Data/25_ACE/AG/AG-Research/results/paper_stats.txt"
lines = []

def w(text=""):
    lines.append(text)
    print(text)

def ci95(data):
    """Compute 95% CI using t-distribution."""
    n = len(data)
    if n < 2:
        return (np.nan, np.nan)
    mean = np.mean(data)
    se = stats.sem(data)
    ci = stats.t.interval(0.95, df=n-1, loc=mean, scale=se)
    return ci

def format_ci(data, label=""):
    arr = np.array(data, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    mean = np.mean(arr)
    sd = np.std(arr, ddof=1)
    lo, hi = ci95(arr)
    return f"  {label}n={n}, mean={mean:.1f}, SD={sd:.1f}, 95% CI=[{lo:.1f}, {hi:.1f}]"


# ============================================================
# 1. EXP01: Pattern-level token statistics
# ============================================================
w("=" * 72)
w("PAPER STATISTICS REPORT")
w("Generated for: AG-Research (COLM 2026)")
w(f"Date: 2026-03-12")
w("=" * 72)

df1 = pd.read_csv("D:/Data/25_ACE/AG/AG-Research/results/exp01/summary.csv", encoding="utf-8")

w()
w("=" * 72)
w("1. EXP01: TOKEN USAGE BY PATTERN (total_tokens)")
w("=" * 72)
w()

patterns_exp01 = sorted(df1["pattern"].unique())
for pat in patterns_exp01:
    subset = df1[df1["pattern"] == pat]["total_tokens"].dropna()
    w(format_ci(subset, f"{pat:10s}: "))

w()
w("--- Key comparisons ---")

# swm3 vs rr3 (rr2 doesn't exist, use rr3)
swm3_tokens = df1[df1["pattern"] == "swm3"]["total_tokens"].dropna().values
rr3_tokens = df1[df1["pattern"] == "rr3"]["total_tokens"].dropna().values
solo_tokens = df1[df1["pattern"] == "solo"]["total_tokens"].dropna().values

if len(swm3_tokens) > 0 and len(rr3_tokens) > 0:
    t_stat, p_val = stats.mannwhitneyu(swm3_tokens, rr3_tokens, alternative="two-sided")
    w(f"  swm3 vs rr3 (Mann-Whitney U): U={t_stat:.1f}, p={p_val:.6f}")
    # Effect size (rank-biserial)
    n1, n2 = len(swm3_tokens), len(rr3_tokens)
    r = 1 - (2 * t_stat) / (n1 * n2)
    w(f"  Effect size (rank-biserial r): {r:.3f}")

if len(swm3_tokens) > 0 and len(solo_tokens) > 0:
    t_stat, p_val = stats.mannwhitneyu(swm3_tokens, solo_tokens, alternative="two-sided")
    w(f"  swm3 vs solo (Mann-Whitney U): U={t_stat:.1f}, p={p_val:.6f}")
    ratio = np.mean(swm3_tokens) / np.mean(solo_tokens)
    w(f"  swm3/solo token ratio: {ratio:.2f}x")

w()
w("--- Pairwise comparisons (all patterns) ---")
for i, p1 in enumerate(patterns_exp01):
    for p2 in patterns_exp01[i+1:]:
        d1 = df1[df1["pattern"] == p1]["total_tokens"].dropna().values
        d2 = df1[df1["pattern"] == p2]["total_tokens"].dropna().values
        u_stat, p_val = stats.mannwhitneyu(d1, d2, alternative="two-sided")
        ratio = np.mean(d1) / np.mean(d2)
        w(f"  {p1:8s} vs {p2:8s}: U={u_stat:7.1f}, p={p_val:.6f}, ratio={ratio:.2f}")

# ============================================================
# 1b. EXP01: Duration and turn statistics
# ============================================================
w()
w("=" * 72)
w("1b. EXP01: DURATION (sec) BY PATTERN")
w("=" * 72)
w()
for pat in patterns_exp01:
    subset = df1[df1["pattern"] == pat]["duration_sec"].dropna()
    w(format_ci(subset, f"{pat:10s}: "))

w()
w("=" * 72)
w("1c. EXP01: TURN COUNT BY PATTERN")
w("=" * 72)
w()
for pat in patterns_exp01:
    subset = df1[df1["pattern"] == pat]["turn_count"].dropna()
    w(format_ci(subset, f"{pat:10s}: "))

# ============================================================
# 2. EXP07: Quality scores by pattern x difficulty
# ============================================================
sc = pd.read_csv("D:/Data/25_ACE/AG/AG-Research/results/exp07/scores.csv", encoding="utf-8")
sc["difficulty"] = sc["task_id"].str.split("_").str[-1]
# Map to ordered
diff_order = ["easy", "med", "hard"]
pat_order_07 = sorted(sc["pattern"].unique())

w()
w("=" * 72)
w("2. EXP07: QUALITY SCORES (overall) BY PATTERN x DIFFICULTY")
w("=" * 72)
w()

for diff in diff_order:
    w(f"  --- {diff.upper()} ---")
    for pat in pat_order_07:
        subset = sc[(sc["pattern"] == pat) & (sc["difficulty"] == diff)]["overall"].dropna()
        if len(subset) > 0:
            w(format_ci(subset, f"    {pat:10s}: "))
    w()

# Overall by pattern (collapsed across difficulty)
w("  --- OVERALL (all difficulties) ---")
for pat in pat_order_07:
    subset = sc[sc["pattern"] == pat]["overall"].dropna()
    w(format_ci(subset, f"    {pat:10s}: "))

w()

# Overall by difficulty (collapsed across pattern)
w("  --- OVERALL (all patterns) ---")
for diff in diff_order:
    subset = sc[sc["difficulty"] == diff]["overall"].dropna()
    w(format_ci(subset, f"    {diff:10s}: "))

# ============================================================
# 2b. Quality sub-dimensions
# ============================================================
w()
w("=" * 72)
w("2b. EXP07: QUALITY SUB-DIMENSIONS BY PATTERN (all difficulties)")
w("=" * 72)
w()
dims = ["accuracy", "completeness", "coherence", "usefulness", "overall"]
for dim in dims:
    w(f"  --- {dim} ---")
    for pat in pat_order_07:
        subset = sc[sc["pattern"] == pat][dim].dropna()
        if len(subset) > 0:
            w(format_ci(subset, f"    {pat:10s}: "))
    w()

# ============================================================
# 3. EXP07: ANOVA / Kruskal-Wallis results + effect sizes
# ============================================================
w()
w("=" * 72)
w("3. EXP07: KRUSKAL-WALLIS RESULTS + EFFECT SIZES")
w("=" * 72)
w()

anova = pd.read_csv("D:/Data/25_ACE/AG/AG-Research/results/exp07/anova_results.csv", encoding="utf-8")
for _, row in anova.iterrows():
    w(f"  {row['test']:35s}: H={row['H_statistic']:8.3f}, p={row['p_value']:.6e}")

w()
w("  --- Effect sizes (eta-squared from H) ---")
w("  Formula: eta^2_H = (H - k + 1) / (N - k)")
w()

# Compute eta-squared for main effects from raw data
# difficulty_main: k=3 difficulties
overall_scores = sc["overall"].dropna()
N_total = len(overall_scores)

# Difficulty main effect
k_diff = 3
H_diff = anova[anova["test"] == "difficulty_main"]["H_statistic"].values[0]
eta2_diff = (H_diff - k_diff + 1) / (N_total - k_diff)
w(f"  difficulty_main: eta^2_H = ({H_diff:.3f} - {k_diff} + 1) / ({N_total} - {k_diff}) = {eta2_diff:.4f}")

# Pattern main effect
k_pat = len(pat_order_07)
H_pat = anova[anova["test"] == "pattern_main"]["H_statistic"].values[0]
eta2_pat = (H_pat - k_pat + 1) / (N_total - k_pat)
w(f"  pattern_main:    eta^2_H = ({H_pat:.3f} - {k_pat} + 1) / ({N_total} - {k_pat}) = {eta2_pat:.4f}")

w()
w("  Interpretation: eta^2_H")
w("    0.01-0.06 = small, 0.06-0.14 = medium, >0.14 = large")
w(f"  difficulty_main: eta^2_H = {eta2_diff:.4f} -> {'large' if eta2_diff > 0.14 else 'medium' if eta2_diff > 0.06 else 'small'}")
w(f"  pattern_main:    eta^2_H = {eta2_pat:.4f} -> {'large' if eta2_pat > 0.14 else 'medium' if eta2_pat > 0.06 else 'small'}")

# Within-group effect sizes
w()
w("  --- Within-group effect sizes ---")
for _, row in anova.iterrows():
    test_name = row["test"]
    if "within" in test_name:
        H_val = row["H_statistic"]
        if "difficulty_within" in test_name:
            pat_name = test_name.replace("difficulty_within_", "")
            subset = sc[sc["pattern"] == pat_name]["overall"].dropna()
            k = 3  # 3 difficulty levels
        elif "pattern_within" in test_name:
            diff_name = test_name.replace("pattern_within_", "")
            subset = sc[sc["difficulty"] == diff_name]["overall"].dropna()
            k = len(pat_order_07)  # 5 patterns
        else:
            continue
        n = len(subset)
        if n > k:
            eta2 = (H_val - k + 1) / (n - k)
            w(f"  {test_name:35s}: eta^2_H = {eta2:.4f} (N={n}, k={k})")

# ============================================================
# 4. EXP07: Post-hoc pairwise comparisons (pattern within each difficulty)
# ============================================================
w()
w("=" * 72)
w("4. EXP07: POST-HOC PAIRWISE COMPARISONS (Mann-Whitney U)")
w("=" * 72)

for diff in diff_order:
    w(f"\n  --- {diff.upper()} ---")
    diff_data = sc[sc["difficulty"] == diff]
    pats = sorted(diff_data["pattern"].unique())
    for i, p1 in enumerate(pats):
        for p2 in pats[i+1:]:
            d1 = diff_data[diff_data["pattern"] == p1]["overall"].dropna().values
            d2 = diff_data[diff_data["pattern"] == p2]["overall"].dropna().values
            if len(d1) > 0 and len(d2) > 0:
                u_stat, p_val = stats.mannwhitneyu(d1, d2, alternative="two-sided")
                # Cohen's d
                pooled_sd = np.sqrt(((len(d1)-1)*np.std(d1,ddof=1)**2 + (len(d2)-1)*np.std(d2,ddof=1)**2) / (len(d1)+len(d2)-2))
                if pooled_sd > 0:
                    cohens_d = (np.mean(d1) - np.mean(d2)) / pooled_sd
                else:
                    cohens_d = 0.0
                w(f"    {p1:8s} vs {p2:8s}: U={u_stat:6.1f}, p={p_val:.4f}, d={cohens_d:+.3f}, "
                  f"means={np.mean(d1):.2f} vs {np.mean(d2):.2f}")

# ============================================================
# 5. EXP07: Token usage by pattern x difficulty
# ============================================================
w()
w("=" * 72)
w("5. EXP07: TOKEN USAGE BY PATTERN x DIFFICULTY")
w("=" * 72)
w()

df7 = pd.read_csv("D:/Data/25_ACE/AG/AG-Research/results/exp07/summary.csv", encoding="utf-8")
df7["difficulty"] = df7["task_id"].str.split("_").str[-1]

for diff in diff_order:
    w(f"  --- {diff.upper()} ---")
    for pat in sorted(df7["pattern"].unique()):
        subset = df7[(df7["pattern"] == pat) & (df7["difficulty"] == diff)]["total_tokens"].dropna()
        if len(subset) > 0:
            w(format_ci(subset, f"    {pat:10s}: "))
    w()

# ============================================================
# 6. Key paper claims with confidence intervals
# ============================================================
w()
w("=" * 72)
w("6. KEY PAPER CLAIMS -- EVIDENCE SUMMARY")
w("=" * 72)
w()

# Claim: "Inverted-U" relationship
w("CLAIM: Inverted-U relationship between difficulty and multi-agent benefit")
w()
for pat in pat_order_07:
    if pat == "solo":
        continue
    w(f"  {pat}:")
    for diff in diff_order:
        solo_scores = sc[(sc["pattern"] == "solo") & (sc["difficulty"] == diff)]["overall"].dropna().values
        pat_scores = sc[(sc["pattern"] == pat) & (sc["difficulty"] == diff)]["overall"].dropna().values
        if len(solo_scores) > 0 and len(pat_scores) > 0:
            delta = np.mean(pat_scores) - np.mean(solo_scores)
            # Bootstrap CI for delta
            w(f"    {diff:6s}: delta(mean) = {delta:+.3f}  ({pat}={np.mean(pat_scores):.3f} - solo={np.mean(solo_scores):.3f})")
    w()

# Claim: debate3 largest quality drop
w("CLAIM: Debate-3 shows largest quality degradation")
w()
for pat in pat_order_07:
    if pat == "solo":
        continue
    all_pat = sc[sc["pattern"] == pat]["overall"].dropna().values
    all_solo = sc[sc["pattern"] == "solo"]["overall"].dropna().values
    delta = np.mean(all_pat) - np.mean(all_solo)
    w(f"  {pat:10s}: overall delta vs solo = {delta:+.3f}")

w()
w("CLAIM: Solo dominates in cost-efficiency across all difficulties")
w()
for diff in diff_order:
    w(f"  --- {diff.upper()} ---")
    for pat in pat_order_07:
        sub_scores = sc[(sc["pattern"] == pat) & (sc["difficulty"] == diff)]
        if len(sub_scores) > 0:
            mean_q = sub_scores["overall"].mean()
            mean_tok = sub_scores["total_tokens"].mean()
            efficiency = mean_q / (mean_tok / 1000) if mean_tok > 0 else 0
            w(f"    {pat:10s}: quality={mean_q:.2f}, tokens={mean_tok:.0f}, efficiency(q/ktok)={efficiency:.3f}")
    w()

w()
w("=" * 72)
w("END OF REPORT")
w("=" * 72)

# Write to file
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n>>> Saved to {OUT}")
