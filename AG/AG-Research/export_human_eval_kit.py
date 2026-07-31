"""
Human Evaluation Kit Exporter
==============================
Exports stratified sample from exp02 for human evaluation.

Sampling strategy:
  - 30 total samples
  - 10 high quality (overall >= 4.5), 10 mid (3.0-4.0), 10 low (<= 2.5)
  - Min 4 samples per pattern (5 patterns: rr3, sel3, swm3, refl2, debate3)

Output:
  results/exp02/human_eval_sheet.csv         (blank scores for evaluator)
  results/exp02/human_eval_answer_key.csv    (G-Eval scores for comparison)
  results/exp02/human_eval_instructions.md   (evaluation guide)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import csv
import random
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results')
EXP02_DIR = RESULTS_DIR / 'exp02'

random.seed(42)  # Reproducible sampling


def load_data():
    """Load exp02 raw data and scores."""
    raw_path = EXP02_DIR / 'raw.json'
    scores_path = EXP02_DIR / 'scores.csv'

    with open(raw_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    scores = []
    with open(scores_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['overall'] = float(row['overall'])
            row['accuracy'] = float(row['accuracy'])
            row['completeness'] = float(row['completeness'])
            row['coherence'] = float(row['coherence'])
            row['usefulness'] = float(row['usefulness'])
            row['turn_index'] = int(row['turn_index'])
            scores.append(row)

    print(f"[OK] Loaded {len(raw_data)} runs, {len(scores)} turn scores")
    return raw_data, scores


def get_cumulative_text(run, up_to_turn):
    """Build cumulative text for a run up to a given substantive turn index."""
    cumulative = ""
    substantive_idx = 0
    for turn in run.get('turns', []):
        if turn.get('source') == 'user':
            continue
        content = str(turn.get('content', ''))
        # Skip handoff/metadata turns
        if any(ind in content for ind in ['FunctionCall(', 'FunctionExecutionResult(', 'Transferred to ', 'transfer_to_']):
            continue
        if len(content.strip()) < 20:
            continue
        substantive_idx += 1
        cumulative += f"\n[{turn['source']}]: {content}\n"
        if substantive_idx >= up_to_turn:
            break
    return cumulative.strip()


def get_task_text(run):
    """Extract the user's task prompt from the run."""
    for turn in run.get('turns', []):
        if turn.get('source') == 'user':
            return turn.get('content', '')
    return ''


def stratified_sample(raw_data, scores):
    """Sample 30 items: 10 high, 10 mid, 10 low with pattern coverage."""
    # Build lookup: (pattern, task_id, turn_index) -> score row
    score_lookup = {}
    for s in scores:
        key = (s['pattern'], s['task_id'], s['turn_index'])
        score_lookup[key] = s

    # Build run lookup: (pattern, task_id) -> run data
    run_lookup = {}
    for r in raw_data:
        run_lookup[(r['pattern'], r['task_id'])] = r

    # For sampling, use the FINAL turn of each (pattern, task_id) run
    # This gives us one representative score per run
    final_scores = {}
    for s in scores:
        key = (s['pattern'], s['task_id'])
        if key not in final_scores or s['turn_index'] > final_scores[key]['turn_index']:
            final_scores[key] = s

    items = list(final_scores.values())

    # Categorize
    high = [i for i in items if i['overall'] >= 4.5]
    mid = [i for i in items if 3.0 <= i['overall'] <= 4.0]
    low = [i for i in items if i['overall'] <= 2.5]

    print(f"[INFO] Score distribution: high({len(high)}) mid({len(mid)}) low({len(low)})")

    # If not enough in a bucket, expand thresholds
    if len(low) < 10:
        low = [i for i in items if i['overall'] <= 3.0]
        print(f"[INFO] Expanded low threshold to <=3.0: {len(low)} items")
    if len(mid) < 10:
        mid = [i for i in items if 3.0 < i['overall'] < 4.5]
        print(f"[INFO] Expanded mid range to (3.0, 4.5): {len(mid)} items")

    def ensure_pattern_coverage(pool, n_target, min_per_pattern=2):
        """Select from pool ensuring pattern coverage."""
        patterns = list(set(i['pattern'] for i in pool))
        selected = []
        by_pattern = defaultdict(list)
        for i in pool:
            by_pattern[i['pattern']].append(i)

        # First pass: take min_per_pattern from each pattern
        for p in patterns:
            available = by_pattern[p]
            take = min(min_per_pattern, len(available))
            chosen = random.sample(available, take)
            selected.extend(chosen)

        # Remove already selected
        selected_keys = set((s['pattern'], s['task_id']) for s in selected)
        remaining = [i for i in pool if (i['pattern'], i['task_id']) not in selected_keys]

        # Fill rest randomly
        still_need = n_target - len(selected)
        if still_need > 0 and remaining:
            extra = random.sample(remaining, min(still_need, len(remaining)))
            selected.extend(extra)

        return selected[:n_target]

    sampled_high = ensure_pattern_coverage(high, 10)
    sampled_mid = ensure_pattern_coverage(mid, 10)
    sampled_low = ensure_pattern_coverage(low, 10)

    all_sampled = sampled_high + sampled_mid + sampled_low
    random.shuffle(all_sampled)

    # Build final items with text
    final_items = []
    for idx, s in enumerate(all_sampled):
        run_key = (s['pattern'], s['task_id'])
        run = run_lookup.get(run_key)
        if not run:
            continue

        task_text = get_task_text(run)
        response_text = get_cumulative_text(run, s['turn_index'])

        # Truncate for human readability
        if len(response_text) > 2000:
            response_text = response_text[:1800] + "\n\n[... truncated for evaluation ...]"

        final_items.append({
            'sample_id': idx + 1,
            'pattern': s['pattern'],
            'task_id': s['task_id'],
            'task_category': s.get('task_category', ''),
            'turn_index': s['turn_index'],
            'task_prompt': task_text,
            'agent_response': response_text,
            # G-Eval scores (for answer key)
            'geval_accuracy': s['accuracy'],
            'geval_completeness': s['completeness'],
            'geval_coherence': s['coherence'],
            'geval_usefulness': s['usefulness'],
            'geval_overall': s['overall'],
        })

    return final_items


def export_sheet(items):
    """Export blank evaluation sheet (no G-Eval scores)."""
    path = EXP02_DIR / 'human_eval_sheet.csv'
    fields = [
        'sample_id', 'task_prompt', 'agent_response',
        'accuracy', 'completeness', 'coherence', 'usefulness', 'overall',
        'comments',
    ]
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow({
                'sample_id': item['sample_id'],
                'task_prompt': item['task_prompt'],
                'agent_response': item['agent_response'],
                'accuracy': '',
                'completeness': '',
                'coherence': '',
                'usefulness': '',
                'overall': '',
                'comments': '',
            })
    print(f"[OK] Saved {path} ({len(items)} samples)")


def export_answer_key(items):
    """Export answer key with G-Eval scores."""
    path = EXP02_DIR / 'human_eval_answer_key.csv'
    fields = [
        'sample_id', 'pattern', 'task_id', 'task_category', 'turn_index',
        'geval_accuracy', 'geval_completeness', 'geval_coherence',
        'geval_usefulness', 'geval_overall',
    ]
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow({k: item[k] for k in fields})
    print(f"[OK] Saved {path}")


def export_instructions():
    """Export evaluation instructions."""
    path = EXP02_DIR / 'human_eval_instructions.md'
    text = """# Human Evaluation Instructions

## Overview
You are evaluating 30 samples of multi-agent conversation outputs.
Each sample contains a **task prompt** and the **agents' cumulative response**.

## Rating Scale (1-5)
For each sample, rate on 5 dimensions:

| Score | Meaning |
|-------|---------|
| 5 | Excellent - comprehensive, accurate, well-structured |
| 4 | Good - mostly complete with minor gaps |
| 3 | Adequate - covers basics but misses important aspects |
| 2 | Poor - significant errors or omissions |
| 1 | Very Poor - fundamentally wrong or irrelevant |

## Dimensions
1. **Accuracy**: Are the facts and claims correct?
2. **Completeness**: Does the response thoroughly address all parts of the task?
3. **Coherence**: Is the response logically organized and consistent?
4. **Usefulness**: Does the response provide practical, actionable value?
5. **Overall**: Holistic quality considering all factors above.

## Procedure
1. Read the **task prompt** carefully.
2. Read the **agent response** in full.
3. Assign integer scores (1-5) for each dimension.
4. Optionally add brief comments in the **comments** column.
5. Do NOT look at the answer key until you have finished all 30 samples.

## Important Notes
- Rate based on the response content alone, not on formatting or language.
- If the response is in Korean or mixed language, evaluate content quality equally.
- Some responses may be truncated - evaluate what is present.
- Samples are randomized - do not assume any ordering by quality.

## Time Estimate
~30-45 minutes (1-1.5 min per sample)

## After Completion
Save the filled CSV and run:
```bash
C:/Python313/python analyze_human_eval.py
```
This will compute inter-rater agreement metrics (Pearson, Spearman, Cohen's kappa).
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"[OK] Saved {path}")


def main():
    raw_data, scores = load_data()
    items = stratified_sample(raw_data, scores)

    print(f"\n[INFO] Final sample: {len(items)} items")
    pattern_counts = defaultdict(int)
    for i in items:
        pattern_counts[i['pattern']] += 1
    for p, c in sorted(pattern_counts.items()):
        print(f"  {p}: {c} samples")

    export_sheet(items)
    export_answer_key(items)
    export_instructions()

    print("\n[DONE] Human evaluation kit exported.")


if __name__ == '__main__':
    main()
