"""Compute 6-model statistics for Opus integration."""
import pandas as pd
from scipy.stats import kruskal

files = {
    'Haiku': 'results/exp07/scores.csv',
    'GPT-4o-mini': 'results/exp07_gpt_4o_mini/scores.csv',
    'GPT-5.4': 'results/exp07_gpt_5_4/scores.csv',
    'Grok': 'results/exp07_grok_3_mini_fast/scores.csv',
    'Gemini': 'results/exp07_gemini_2_0_flash/scores.csv',
    'Opus': 'results/exp07_claude_opus_4_5_20251101/scores.csv',
}

all_dfs = []
for name, f in files.items():
    df = pd.read_csv(f)
    df['model'] = name
    df['difficulty'] = df['task_id'].apply(lambda x: x.split('_')[1])
    all_dfs.append(df)

combined = pd.concat(all_dfs, ignore_index=True)
print(f'Total scored runs: {len(combined)}')
print(f'Models: {combined["model"].nunique()}')
print()

# Solo dominance on easy
easy = combined[combined['difficulty'] == 'easy']
for model in ['Haiku', 'GPT-4o-mini', 'GPT-5.4', 'Grok', 'Gemini', 'Opus']:
    m = easy[easy['model'] == model]
    solo_mean = m[m['pattern'] == 'solo']['overall'].mean()
    best = m.groupby('pattern')['overall'].mean()
    best_pat = best.idxmax()
    print(f'{model:12} easy: solo={solo_mean:.2f}, best={best_pat}({best.max():.2f}), solo_best={best_pat == "solo"}')

print()

# 6-model mean table
for diff in ['easy', 'med', 'hard']:
    d = combined[combined['difficulty'] == diff]
    row = []
    for pat in ['solo', 'swm3', 'sel3', 'refl2', 'debate3']:
        row.append(f'{d[d["pattern"]==pat]["overall"].mean():.2f}')
    print(f'{diff:5} {" ".join(row)}')

print()

# Kruskal-Wallis
diff_groups = [combined[combined['difficulty'] == d]['overall'].values for d in ['easy', 'med', 'hard']]
pat_groups = [combined[combined['pattern'] == p]['overall'].values for p in ['solo', 'swm3', 'sel3', 'refl2', 'debate3']]
H_diff, p_diff = kruskal(*diff_groups)
H_pat, p_pat = kruskal(*pat_groups)
n = len(combined)
eta2_diff = (H_diff - 2) / (n - 3)
eta2_pat = (H_pat - 4) / (n - 5)
print(f'6-model K-W: difficulty H={H_diff:.2f}, p={p_diff:.2e}, eta2_H={eta2_diff:.3f}')
print(f'6-model K-W: pattern   H={H_pat:.2f}, p={p_pat:.2e}, eta2_H={eta2_pat:.3f}')
print(f'Ratio: {eta2_diff/eta2_pat:.1f}x')

# Refl2 vs Solo on medium/hard for Opus
print()
for diff in ['med', 'hard']:
    opus = combined[(combined['model'] == 'Opus') & (combined['difficulty'] == diff)]
    solo_v = opus[opus['pattern'] == 'solo']['overall'].values
    refl_v = opus[opus['pattern'] == 'refl2']['overall'].values
    delta = refl_v.mean() - solo_v.mean()
    print(f'Opus {diff}: solo={solo_v.mean():.2f}, refl2={refl_v.mean():.2f}, delta={delta:+.2f}')
