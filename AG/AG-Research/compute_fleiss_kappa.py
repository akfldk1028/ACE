"""
5-Model Cross-Validation Consensus: Fleiss' κ + Pairwise Cohen's κ_w
=====================================================================
Computes inter-rater agreement across 6 LLM evaluators:
  1. Claude Sonnet (G-Eval, primary scorer)
  2. GPT-4o-mini (cross-validation, 40 samples)  — reported separately
  3. GPT-5.4 (cross-validation, 100 samples)
  4. Haiku 4.5 (cross-validation, 100 samples)
  5. Grok 3 Mini (cross-validation, 100 samples)
  6. Gemini 2.0 Flash (cross-validation, 100 samples)

On overlapping samples (100 for 5-rater, 40 for 6-rater), computes:
  - Per-model Cohen's quadratic weighted κ vs Claude
  - 5-rater Fleiss' κ (5 categories)
  - Krippendorff's α (ordinal)

Output: results/exp02/five_model_consensus.csv
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import csv
import numpy as np
from pathlib import Path

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp02')
DIMENSIONS = ['accuracy', 'completeness', 'coherence', 'usefulness', 'overall']

# Model configs: (filename, column_prefix_for_cross_validator)
MODELS = {
    'GPT-4o-mini': ('cross_validation.csv', 'gpt'),
    'GPT-5.4': ('cross_validation_gpt54.csv', 'gpt'),
    'Haiku': ('cross_validation_haiku.csv', 'haiku'),
    'Grok': ('cross_validation_grok.csv', 'grok'),
    'Gemini': ('cross_validation_gemini.csv', 'gemini'),
}

# 5-rater set (N=100 overlap: Claude + GPT-5.4 + Haiku + Grok + Gemini)
# GPT-4o-mini (N=40) reported separately
FIVE_RATER_MODELS = ['GPT-5.4', 'Haiku', 'Grok', 'Gemini']


def load_cross_validation(filename, model_prefix):
    """Load cross-validation CSV, return dict keyed by (pattern, task_id, turn_index)."""
    data = {}
    path = RESULTS_DIR / filename
    with open(path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            key = (row['pattern'], row['task_id'], int(row['turn_index']))
            data[key] = {
                'claude': {d: int(float(row[f'claude_{d}'])) for d in DIMENSIONS},
                'model': {d: int(float(row[f'{model_prefix}_{d}'])) for d in DIMENSIONS},
            }
    return data


def cohens_weighted_kappa(y1, y2, weights='quadratic'):
    """Compute Cohen's weighted kappa."""
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(y1, y2, weights=weights)


def fleiss_kappa(ratings_matrix):
    """Compute Fleiss' kappa from a subjects × categories matrix.

    ratings_matrix[i][j] = number of raters who assigned category j to subject i
    """
    N, k = ratings_matrix.shape
    n = ratings_matrix.sum(axis=1)[0]  # number of raters per subject

    # Proportion of assignments to each category
    p_j = ratings_matrix.sum(axis=0) / (N * n)

    # Per-subject agreement
    P_i = (ratings_matrix ** 2).sum(axis=1) - n
    P_i = P_i / (n * (n - 1))

    P_bar = P_i.mean()
    P_e = (p_j ** 2).sum()

    if P_e == 1.0:
        return 1.0

    kappa = (P_bar - P_e) / (1 - P_e)
    return kappa


def krippendorff_alpha_ordinal(data_matrix):
    """Compute Krippendorff's alpha for ordinal data.

    data_matrix: raters × subjects, with NaN for missing
    """
    n_raters, n_subjects = data_matrix.shape

    # Observed disagreement
    pairs = []
    for j in range(n_subjects):
        values = data_matrix[:, j]
        valid = values[~np.isnan(values)]
        if len(valid) < 2:
            continue
        for a in range(len(valid)):
            for b in range(a + 1, len(valid)):
                pairs.append((valid[a], valid[b]))

    if not pairs:
        return 0.0

    pairs = np.array(pairs)
    Do = np.mean((pairs[:, 0] - pairs[:, 1]) ** 2)

    # Expected disagreement (full pairwise)
    all_values = data_matrix[~np.isnan(data_matrix)]
    n_total = len(all_values)
    De = 0.0
    count = 0
    for i in range(n_total):
        for j in range(i + 1, n_total):
            De += (all_values[i] - all_values[j]) ** 2
            count += 1
    De = De / count if count > 0 else 0

    if De == 0:
        return 1.0

    return 1 - Do / De


def main():
    # Load all cross-validation results
    all_data = {}
    for model_name, (filename, prefix) in MODELS.items():
        all_data[model_name] = load_cross_validation(filename, prefix)
        print(f"  Loaded {model_name}: {len(all_data[model_name])} samples")

    # ================================================================
    # Part A: Per-model pairwise κ_w vs Claude (overall dimension)
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Part A: Per-Model Pairwise Agreement (vs Claude)")
    print(f"{'='*60}\n")

    pairwise_results = {}
    for model_name in MODELS:
        data = all_data[model_name]
        n = len(data)
        keys = sorted(data.keys())

        for dim in DIMENSIONS:
            claude_scores = [data[k]['claude'][dim] for k in keys]
            model_scores = [data[k]['model'][dim] for k in keys]

            kw = cohens_weighted_kappa(claude_scores, model_scores)
            r = np.corrcoef(claude_scores, model_scores)[0, 1]
            from scipy.stats import spearmanr
            rho, _ = spearmanr(claude_scores, model_scores)
            delta = np.mean(claude_scores) - np.mean(model_scores)

            if model_name not in pairwise_results:
                pairwise_results[model_name] = {}
            pairwise_results[model_name][dim] = {
                'n': n, 'kw': kw, 'r': r, 'rho': rho, 'delta': delta,
                'mean_claude': np.mean(claude_scores),
                'mean_model': np.mean(model_scores),
            }

        ov = pairwise_results[model_name]['overall']
        print(f"  {model_name:15s} (N={ov['n']:3d}): κ_w={ov['kw']:.3f}  r={ov['r']:.3f}  ρ={ov['rho']:.3f}  Δ={ov['delta']:+.2f}")

    # ================================================================
    # Part B: 5-rater Fleiss' κ (Claude + GPT-5.4 + Haiku + Grok, N=100)
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Part B: 5-Rater Consensus (Claude + GPT-5.4 + Haiku + Grok)")
    print(f"{'='*60}\n")

    # Find overlapping keys across 3 N=100 models
    overlap_keys = None
    for model_name in FIVE_RATER_MODELS:
        keys = set(all_data[model_name].keys())
        if overlap_keys is None:
            overlap_keys = keys
        else:
            overlap_keys = overlap_keys & keys
    overlap_keys = sorted(overlap_keys)
    n_overlap = len(overlap_keys)
    print(f"  Overlapping samples (5-rater): {n_overlap}")

    five_rater_results = {}
    for dim in DIMENSIONS:
        # Extract scores: Claude + 4 cross-validators
        claude_scores = [all_data['GPT-5.4'][k]['claude'][dim] for k in overlap_keys]
        gpt54_scores = [all_data['GPT-5.4'][k]['model'][dim] for k in overlap_keys]
        haiku_scores = [all_data['Haiku'][k]['model'][dim] for k in overlap_keys]
        grok_scores = [all_data['Grok'][k]['model'][dim] for k in overlap_keys]
        gemini_scores = [all_data['Gemini'][k]['model'][dim] for k in overlap_keys]

        all_rater_scores = [claude_scores, gpt54_scores, haiku_scores, grok_scores, gemini_scores]

        # Fleiss' κ (5 raters, 5 categories: scores 1-5)
        ratings = np.zeros((n_overlap, 5))
        for i in range(n_overlap):
            for rater in all_rater_scores:
                ratings[i, rater[i] - 1] += 1
        fk = fleiss_kappa(ratings)

        # Krippendorff's α
        data_matrix = np.array(all_rater_scores, dtype=float)
        ka = krippendorff_alpha_ordinal(data_matrix)

        # Mean per rater
        means = {
            'Claude': np.mean(claude_scores),
            'GPT-5.4': np.mean(gpt54_scores),
            'Haiku': np.mean(haiku_scores),
            'Grok': np.mean(grok_scores),
            'Gemini': np.mean(gemini_scores),
        }

        five_rater_results[dim] = {
            'fleiss_kappa': fk,
            'krippendorff_alpha': ka,
            'means': means,
        }

        print(f"  {dim:>15}: Fleiss' κ = {fk:.3f}  Krippendorff's α = {ka:.3f}")
        print(f"    Means: Claude={means['Claude']:.2f}  5.4={means['GPT-5.4']:.2f}  "
              f"Haiku={means['Haiku']:.2f}  Grok={means['Grok']:.2f}  Gemini={means['Gemini']:.2f}")

    # ================================================================
    # Save results
    # ================================================================
    out_path = RESULTS_DIR / 'five_model_consensus.csv'
    fields = ['dimension', 'fleiss_kappa_5rater', 'krippendorff_alpha_5rater',
              'mean_claude', 'mean_gpt54', 'mean_haiku', 'mean_grok', 'mean_gemini']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for dim in DIMENSIONS:
            r = five_rater_results[dim]
            writer.writerow({
                'dimension': dim,
                'fleiss_kappa_5rater': f"{r['fleiss_kappa']:.3f}",
                'krippendorff_alpha_5rater': f"{r['krippendorff_alpha']:.3f}",
                'mean_claude': f"{r['means']['Claude']:.2f}",
                'mean_gpt54': f"{r['means']['GPT-5.4']:.2f}",
                'mean_haiku': f"{r['means']['Haiku']:.2f}",
                'mean_grok': f"{r['means']['Grok']:.2f}",
                'mean_gemini': f"{r['means']['Gemini']:.2f}",
            })
    print(f"\n[OK] Saved {out_path}")

    # Paper-ready summary
    ov = five_rater_results['overall']
    print(f"\n{'='*60}")
    print(f"PAPER-READY SUMMARY")
    print(f"{'='*60}")
    print(f"\nPer-model overall κ_w (vs Claude):")
    for m in MODELS:
        r = pairwise_results[m]['overall']
        print(f"  {m:15s} (N={r['n']:3d}): κ_w={r['kw']:.3f}  r={r['r']:.3f}  ρ={r['rho']:.3f}  Δ={r['delta']:+.2f}")
    print(f"\n5-rater Fleiss' κ (Claude + GPT-5.4 + Haiku + Grok, N={n_overlap}):")
    print(f"  Fleiss' κ (overall) = {ov['fleiss_kappa']:.3f}")
    print(f"  Krippendorff's α (overall) = {ov['krippendorff_alpha']:.3f}")

    # κ_w range across all 5 cross-validators
    all_kw = [pairwise_results[m]['overall']['kw'] for m in MODELS]
    kw_100 = [pairwise_results[m]['overall']['kw'] for m in FIVE_RATER_MODELS]
    print(f"  κ_w range (3 N=100 models): {min(kw_100):.3f}--{max(kw_100):.3f}")
    print(f"  κ_w range (all 5 models): {min(all_kw):.3f}--{max(all_kw):.3f}")
    agreement = 'Moderate' if np.mean(kw_100) >= 0.40 else 'Fair-to-moderate'
    print(f"  → {agreement} agreement across 5 models from 4 providers")


if __name__ == '__main__':
    main()
