"""
Human Evaluation Analysis
==========================
Analyzes filled human evaluation sheet against G-Eval answer key.
Computes Pearson, Spearman correlations and Cohen's weighted kappa.

Reads:
  results/exp02/human_eval_sheet.csv       (filled by human evaluator)
  results/exp02/human_eval_answer_key.csv  (G-Eval reference scores)

Output:
  results/exp02/human_eval_results.csv     (summary metrics)
  Console report with agreement statistics
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import csv
import statistics
from pathlib import Path

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results')
EXP02_DIR = RESULTS_DIR / 'exp02'

DIMENSIONS = ['accuracy', 'completeness', 'coherence', 'usefulness', 'overall']


def load_sheets():
    """Load human scores and answer key."""
    human_path = EXP02_DIR / 'human_eval_sheet.csv'
    key_path = EXP02_DIR / 'human_eval_answer_key.csv'

    human_scores = {}
    with open(human_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            sid = int(row['sample_id'])
            scores = {}
            valid = True
            for dim in DIMENSIONS:
                val = row.get(dim, '').strip()
                if not val:
                    valid = False
                    break
                scores[dim] = float(val)
            if valid:
                human_scores[sid] = scores

    answer_key = {}
    with open(key_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            sid = int(row['sample_id'])
            answer_key[sid] = {
                'pattern': row['pattern'],
                'task_id': row['task_id'],
                'task_category': row.get('task_category', ''),
                'geval_accuracy': float(row['geval_accuracy']),
                'geval_completeness': float(row['geval_completeness']),
                'geval_coherence': float(row['geval_coherence']),
                'geval_usefulness': float(row['geval_usefulness']),
                'geval_overall': float(row['geval_overall']),
            }

    print(f"[OK] Loaded {len(human_scores)} human scores, {len(answer_key)} answer key entries")
    return human_scores, answer_key


def compute_agreement(human_scores, answer_key):
    """Compute inter-rater agreement metrics."""
    from scipy import stats
    import numpy as np

    # Match by sample_id
    common_ids = set(human_scores.keys()) & set(answer_key.keys())
    print(f"[INFO] {len(common_ids)} matched samples")

    if len(common_ids) < 5:
        print("[ERROR] Too few matched samples for reliable statistics")
        return None

    results = {}
    for dim in DIMENSIONS:
        human_vals = [human_scores[sid][dim] for sid in sorted(common_ids)]
        geval_vals = [answer_key[sid][f'geval_{dim}'] for sid in sorted(common_ids)]

        # Basic stats
        mean_human = statistics.mean(human_vals)
        mean_geval = statistics.mean(geval_vals)
        mean_diff = mean_human - mean_geval

        # Correlations
        if len(set(human_vals)) < 2 or len(set(geval_vals)) < 2:
            results[dim] = {
                'pearson': 'N/A', 'spearman': 'N/A', 'kappa': 'N/A',
                'mean_human': f"{mean_human:.2f}", 'mean_geval': f"{mean_geval:.2f}",
                'mean_diff': f"{mean_diff:+.2f}", 'n': len(common_ids),
            }
            continue

        pearson_r, pearson_p = stats.pearsonr(human_vals, geval_vals)
        spearman_r, spearman_p = stats.spearmanr(human_vals, geval_vals)

        # Cohen's weighted kappa (quadratic)
        kappa = _weighted_kappa(human_vals, geval_vals)

        # Absolute agreement (within 1 point)
        within_1 = sum(1 for h, g in zip(human_vals, geval_vals) if abs(h - g) <= 1)
        agreement_pct = within_1 / len(common_ids) * 100

        results[dim] = {
            'pearson': f"{pearson_r:.3f}",
            'pearson_p': f"{pearson_p:.4f}",
            'spearman': f"{spearman_r:.3f}",
            'spearman_p': f"{spearman_p:.4f}",
            'kappa': f"{kappa:.3f}",
            'mean_human': f"{mean_human:.2f}",
            'mean_geval': f"{mean_geval:.2f}",
            'mean_diff': f"{mean_diff:+.2f}",
            'agreement_within_1': f"{agreement_pct:.1f}%",
            'n': len(common_ids),
        }

    return results


def _weighted_kappa(y1, y2):
    """Compute quadratic weighted kappa."""
    import numpy as np
    labels = sorted(set(y1) | set(y2))
    n_labels = len(labels)
    if n_labels < 2:
        return 0.0
    label_map = {l: i for i, l in enumerate(labels)}

    conf = np.zeros((n_labels, n_labels))
    for a, b in zip(y1, y2):
        conf[label_map[a]][label_map[b]] += 1

    n = len(y1)
    weights = np.zeros((n_labels, n_labels))
    for i in range(n_labels):
        for j in range(n_labels):
            weights[i][j] = (i - j) ** 2 / (n_labels - 1) ** 2

    hist1 = np.sum(conf, axis=1) / n
    hist2 = np.sum(conf, axis=0) / n
    expected = np.outer(hist1, hist2)

    observed = conf / n
    denom = np.sum(weights * expected)
    if denom == 0:
        return 0.0
    return 1 - np.sum(weights * observed) / denom


def main():
    human_scores, answer_key = load_sheets()

    if not human_scores:
        print("\n[WARN] No human scores found!")
        print("Please fill in the scores in:")
        print(f"  {EXP02_DIR / 'human_eval_sheet.csv'}")
        print("\nSee instructions in:")
        print(f"  {EXP02_DIR / 'human_eval_instructions.md'}")
        return

    results = compute_agreement(human_scores, answer_key)
    if not results:
        return

    # Print report
    print("\n" + "=" * 70)
    print("HUMAN vs G-EVAL AGREEMENT REPORT")
    print("=" * 70)
    print(f"{'Dimension':>15} {'Pearson':>8} {'Spearman':>9} {'Kappa':>7} "
          f"{'Human':>7} {'G-Eval':>7} {'Diff':>7} {'Agree±1':>8}")
    print("-" * 70)

    for dim in DIMENSIONS:
        r = results[dim]
        agree = r.get('agreement_within_1', 'N/A')
        print(f"{dim:>15} {r['pearson']:>8} {r['spearman']:>9} {r['kappa']:>7} "
              f"{r['mean_human']:>7} {r['mean_geval']:>7} {r['mean_diff']:>7} {agree:>8}")

    # Interpretation
    print("\n=== Interpretation ===")
    for dim in DIMENSIONS:
        r = results[dim]
        if r['pearson'] == 'N/A':
            continue
        p = float(r['pearson'])
        if p >= 0.8:
            strength = "strong"
        elif p >= 0.6:
            strength = "moderate"
        elif p >= 0.4:
            strength = "fair"
        else:
            strength = "weak"
        print(f"  {dim}: {strength} agreement (r={r['pearson']})")

    # Save results
    summary_path = EXP02_DIR / 'human_eval_results.csv'
    fields = ['dimension', 'pearson', 'pearson_p', 'spearman', 'spearman_p',
              'kappa', 'mean_human', 'mean_geval', 'mean_diff', 'agreement_within_1', 'n']
    with open(summary_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for dim in DIMENSIONS:
            writer.writerow({'dimension': dim, **results[dim]})
    print(f"\n[OK] Saved {summary_path}")

    print("\n[DONE] Human evaluation analysis complete.")


if __name__ == '__main__':
    main()
