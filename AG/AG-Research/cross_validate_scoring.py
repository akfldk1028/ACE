"""
LLM Cross-Validation for G-Eval Scoring
=========================================
Re-scores a subset of exp02 turns using a different LLM (GPT-4o)
to validate the Claude-based G-Eval scores.

Requires: OPENAI_API_KEY environment variable

Sampling: 40 turns stratified across 5 patterns and score ranges
Uses the IDENTICAL scoring prompt from scorer.py for fair comparison.

Output:
  results/exp02/cross_validation.csv          (paired scores)
  results/exp02/cross_validation_summary.csv  (correlation metrics)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import csv
import os
import re
import random
import statistics
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results')
EXP02_DIR = RESULTS_DIR / 'exp02'

random.seed(42)

# Identical prompt from exp02_termination_quality/scorer.py
SCORING_PROMPT = """You are evaluating a multi-agent conversation output.

## Task
{task}

## Evaluation Rubric
{rubric}

## Cumulative Response (up to turn {turn_index})
{cumulative_text}

## Instructions
Rate the cumulative response on these 5 dimensions (1-5 scale each):
1. **Accuracy**: Correctness of facts and claims
2. **Completeness**: How thoroughly the task is addressed
3. **Coherence**: Logical flow and consistency
4. **Usefulness**: Practical value of the answer
5. **Overall**: Overall quality considering all factors

Return ONLY a JSON object with exactly these keys:
{{"accuracy": N, "completeness": N, "coherence": N, "usefulness": N, "overall": N}}

where N is an integer from 1 to 5.
"""


def load_data():
    """Load exp02 raw runs and scores."""
    with open(EXP02_DIR / 'raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    scores = []
    with open(EXP02_DIR / 'scores.csv', 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for k in ['accuracy', 'completeness', 'coherence', 'usefulness', 'overall']:
                row[k] = float(row[k])
            row['turn_index'] = int(row['turn_index'])
            scores.append(row)

    return raw_data, scores


def load_tasks():
    """Load task suite for rubric lookup."""
    task_path = Path(r'D:\Data\25_ACE\AG\AG-Research\task_suite.json')
    with open(task_path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    return {t['id']: t for t in tasks}


def get_cumulative_text(run, up_to_turn):
    """Build cumulative text up to given substantive turn index."""
    cumulative = ""
    substantive_idx = 0
    for turn in run.get('turns', []):
        if turn.get('source') == 'user':
            continue
        content = str(turn.get('content', ''))
        if any(ind in content for ind in ['FunctionCall(', 'FunctionExecutionResult(', 'Transferred to ', 'transfer_to_']):
            continue
        if len(content.strip()) < 20:
            continue
        substantive_idx += 1
        cumulative += f"\n[{turn['source']}]: {content}\n"
        if substantive_idx >= up_to_turn:
            break
    return cumulative.strip()


def select_samples(raw_data, scores, n=40):
    """Select 40 stratified samples (8 per pattern)."""
    run_lookup = {(r['pattern'], r['task_id']): r for r in raw_data}

    by_pattern = defaultdict(list)
    for s in scores:
        by_pattern[s['pattern']].append(s)

    selected = []
    per_pattern = n // len(by_pattern)  # 8 per pattern

    for pattern, pattern_scores in by_pattern.items():
        # Stratify within pattern by score range
        sorted_scores = sorted(pattern_scores, key=lambda x: x['overall'])
        # Take evenly spaced samples
        if len(sorted_scores) <= per_pattern:
            chosen = sorted_scores
        else:
            step = len(sorted_scores) / per_pattern
            indices = [int(i * step) for i in range(per_pattern)]
            chosen = [sorted_scores[i] for i in indices]
        selected.extend(chosen)

    random.shuffle(selected)
    return selected[:n], run_lookup


def score_with_openai(prompt, api_key):
    """Score using OpenAI GPT-4o API."""
    import httpx

    response = httpx.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'gpt-4o-mini',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0,
            'max_tokens': 100,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    text = response.json()['choices'][0]['message']['content'].strip()

    # Extract JSON
    json_match = re.search(r'\{[^}]+\}', text)
    if json_match:
        scores = json.loads(json_match.group())
        return {
            'accuracy': max(1, min(5, int(scores.get('accuracy', 3)))),
            'completeness': max(1, min(5, int(scores.get('completeness', 3)))),
            'coherence': max(1, min(5, int(scores.get('coherence', 3)))),
            'usefulness': max(1, min(5, int(scores.get('usefulness', 3)))),
            'overall': max(1, min(5, int(scores.get('overall', 3)))),
        }
    return None


def compute_correlations(pairs):
    """Compute Pearson, Spearman correlations and Cohen's weighted kappa."""
    from scipy import stats

    dimensions = ['accuracy', 'completeness', 'coherence', 'usefulness', 'overall']
    results = {}

    for dim in dimensions:
        claude_scores = [p[f'claude_{dim}'] for p in pairs]
        gpt_scores = [p[f'gpt_{dim}'] for p in pairs]

        if len(set(claude_scores)) < 2 or len(set(gpt_scores)) < 2:
            results[dim] = {'pearson': 'N/A', 'spearman': 'N/A', 'kappa': 'N/A'}
            continue

        pearson_r, pearson_p = stats.pearsonr(claude_scores, gpt_scores)
        spearman_r, spearman_p = stats.spearmanr(claude_scores, gpt_scores)

        # Cohen's weighted kappa
        try:
            from sklearn.metrics import cohen_kappa_score
            kappa = cohen_kappa_score(claude_scores, gpt_scores, weights='quadratic')
        except ImportError:
            # Manual weighted kappa fallback
            kappa = _weighted_kappa(claude_scores, gpt_scores)

        results[dim] = {
            'pearson': f"{pearson_r:.3f}",
            'pearson_p': f"{pearson_p:.4f}",
            'spearman': f"{spearman_r:.3f}",
            'spearman_p': f"{spearman_p:.4f}",
            'kappa': f"{kappa:.3f}",
            'mean_claude': f"{statistics.mean(claude_scores):.2f}",
            'mean_gpt': f"{statistics.mean(gpt_scores):.2f}",
            'mean_diff': f"{statistics.mean(claude_scores) - statistics.mean(gpt_scores):+.2f}",
        }

    return results


def _weighted_kappa(y1, y2):
    """Compute quadratic weighted kappa (fallback if sklearn unavailable)."""
    import numpy as np
    labels = sorted(set(y1) | set(y2))
    n_labels = len(labels)
    label_map = {l: i for i, l in enumerate(labels)}

    # Confusion matrix
    conf = np.zeros((n_labels, n_labels))
    for a, b in zip(y1, y2):
        conf[label_map[a]][label_map[b]] += 1

    n = len(y1)
    # Weight matrix (quadratic)
    weights = np.zeros((n_labels, n_labels))
    for i in range(n_labels):
        for j in range(n_labels):
            weights[i][j] = (i - j) ** 2 / (n_labels - 1) ** 2

    # Expected
    hist1 = np.sum(conf, axis=1) / n
    hist2 = np.sum(conf, axis=0) / n
    expected = np.outer(hist1, hist2)

    observed = conf / n
    return 1 - np.sum(weights * observed) / np.sum(weights * expected)


def main():
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set.")
        print("Set it with: set OPENAI_API_KEY=sk-...")
        print("\nGenerating sample selection only (dry run)...")
        dry_run = True
    else:
        dry_run = False

    raw_data, scores = load_data()
    tasks = load_tasks()
    samples, run_lookup = select_samples(raw_data, scores, n=40)

    print(f"[OK] Selected {len(samples)} samples for cross-validation")
    pattern_counts = defaultdict(int)
    for s in samples:
        pattern_counts[s['pattern']] += 1
    for p, c in sorted(pattern_counts.items()):
        print(f"  {p}: {c} samples")

    if dry_run:
        # Save sample selection for review
        path = EXP02_DIR / 'cross_validation_samples.csv'
        fields = ['pattern', 'task_id', 'turn_index', 'overall']
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for s in samples:
                writer.writerow({k: s[k] for k in fields})
        print(f"[OK] Saved sample selection to {path}")
        print("\n[INFO] Set OPENAI_API_KEY and re-run for full cross-validation.")
        return

    # Score each sample with GPT-4o
    pairs = []
    errors = 0
    for i, sample in enumerate(samples):
        run_key = (sample['pattern'], sample['task_id'])
        run = run_lookup.get(run_key)
        if not run:
            errors += 1
            continue

        # Find task metadata
        task_meta = tasks.get(sample['task_id'], {})
        task_text = task_meta.get('task', '')
        if not task_text:
            for t in run.get('turns', []):
                if t.get('source') == 'user':
                    task_text = t.get('content', '')
                    break

        rubric = task_meta.get('eval_rubric', 'General quality')
        cumulative = get_cumulative_text(run, sample['turn_index'])

        prompt = SCORING_PROMPT.format(
            task=task_text,
            rubric=rubric,
            turn_index=sample['turn_index'],
            cumulative_text=cumulative[:3000],
        )

        try:
            gpt_scores = score_with_openai(prompt, api_key)
            if gpt_scores:
                pair = {
                    'pattern': sample['pattern'],
                    'task_id': sample['task_id'],
                    'turn_index': sample['turn_index'],
                }
                for dim in ['accuracy', 'completeness', 'coherence', 'usefulness', 'overall']:
                    pair[f'claude_{dim}'] = sample[dim]
                    pair[f'gpt_{dim}'] = gpt_scores[dim]
                pairs.append(pair)
                print(f"  [{i+1}/{len(samples)}] {sample['pattern']}/{sample['task_id']}: "
                      f"Claude={sample['overall']:.0f} GPT={gpt_scores['overall']}")
            else:
                errors += 1
                print(f"  [{i+1}] Parse error")
        except Exception as e:
            errors += 1
            print(f"  [{i+1}] API error: {e}")

    print(f"\n[OK] Scored {len(pairs)} samples ({errors} errors)")

    # Save paired scores
    if not pairs:
        print("[ERROR] No valid pairs to analyze")
        return

    pair_fields = list(pairs[0].keys())
    path = EXP02_DIR / 'cross_validation.csv'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=pair_fields)
        writer.writeheader()
        writer.writerows(pairs)
    print(f"[OK] Saved {path}")

    # Compute correlations
    print("\n=== Cross-Validation Results ===")
    corr = compute_correlations(pairs)
    for dim, metrics in corr.items():
        print(f"  {dim:>15}: Pearson={metrics['pearson']} Spearman={metrics['spearman']} "
              f"Kappa={metrics['kappa']} (Claude={metrics['mean_claude']} GPT={metrics['mean_gpt']} "
              f"diff={metrics['mean_diff']})")

    # Save summary
    summary_path = EXP02_DIR / 'cross_validation_summary.csv'
    summary_fields = ['dimension', 'pearson', 'pearson_p', 'spearman', 'spearman_p',
                      'kappa', 'mean_claude', 'mean_gpt', 'mean_diff']
    with open(summary_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        for dim, metrics in corr.items():
            writer.writerow({'dimension': dim, **metrics})
    print(f"[OK] Saved {summary_path}")

    print("\n[DONE] Cross-validation complete.")


if __name__ == '__main__':
    main()
