"""
Multi-Model Cross-Validation for G-Eval Scoring
=================================================
Scores samples using multiple LLM evaluators:
  1. Claude Haiku 4.5 (via claude CLI subprocess)
  2. Grok (xAI API)
  3. Gemini (Google API)

Claude Sonnet (primary) + GPT-4o-mini + GPT-5.4 already done.
This adds 3 more for 6-model consensus.

Usage: python cross_validate_multi_model.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import json
import csv
import os
import re
import random
import subprocess
import statistics
import time
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp02')
random.seed(42)

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

DIMENSIONS = ['accuracy', 'completeness', 'coherence', 'usefulness', 'overall']


def load_data():
    with open(RESULTS_DIR / 'raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    scores = []
    with open(RESULTS_DIR / 'scores.csv', 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for k in DIMENSIONS:
                row[k] = float(row[k])
            row['turn_index'] = int(row['turn_index'])
            scores.append(row)
    return raw_data, scores


def load_tasks():
    task_path = Path(r'D:\Data\25_ACE\AG\AG-Research\task_suite.json')
    with open(task_path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    return {t['id']: t for t in tasks}


def get_cumulative_text(run, up_to_turn):
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
    """Select 40 stratified samples (same as original for comparability)."""
    run_lookup = {(r['pattern'], r['task_id']): r for r in raw_data}
    by_pattern = defaultdict(list)
    for s in scores:
        by_pattern[s['pattern']].append(s)
    selected = []
    per_pattern = n // len(by_pattern)
    for pattern, pattern_scores in by_pattern.items():
        sorted_scores = sorted(pattern_scores, key=lambda x: x['overall'])
        if len(sorted_scores) <= per_pattern:
            chosen = sorted_scores
        else:
            step = len(sorted_scores) / per_pattern
            indices = [int(i * step) for i in range(per_pattern)]
            chosen = [sorted_scores[i] for i in indices]
        selected.extend(chosen)
    random.shuffle(selected)
    return selected[:n], run_lookup


def parse_scores(text):
    json_match = re.search(r'\{[^}]+\}', text)
    if json_match:
        scores = json.loads(json_match.group())
        return {d: max(1, min(5, int(scores.get(d, 3)))) for d in DIMENSIONS}
    return None


def score_with_claude_haiku(prompt):
    """Score using Claude Haiku via CLI subprocess (minimal mode)."""
    try:
        result = subprocess.run(
            [
                'claude', '-p', prompt,
                '--model', 'claude-haiku-4-5-20251001',
                '--output-format', 'text',
                '--system-prompt', 'You are a scoring assistant. Return only JSON.',
                '--setting-sources', '',
                '--tools', '',
                '--no-session-persistence',
            ],
            capture_output=True, text=True, timeout=120, encoding='utf-8'
        )
        if result.returncode == 0:
            return parse_scores(result.stdout)
        else:
            print(f"    Haiku stderr: {result.stderr[:100]}")
    except Exception as e:
        print(f"    Haiku error: {e}")
    return None


def score_with_opus(prompt):
    """Score using Claude Opus via CLI subprocess."""
    try:
        result = subprocess.run(
            [
                'claude', '-p', prompt,
                '--model', 'claude-opus-4-5-20251101',
                '--output-format', 'text',
                '--system-prompt', 'You are a scoring assistant. Return only JSON.',
                '--setting-sources', '',
                '--tools', '',
                '--no-session-persistence',
            ],
            capture_output=True, text=True, timeout=180, encoding='utf-8'
        )
        if result.returncode == 0:
            return parse_scores(result.stdout)
        else:
            print(f"    Opus stderr: {result.stderr[:100]}")
    except Exception as e:
        print(f"    Opus error: {e}")
    return None


def score_with_grok(prompt, api_key):
    """Score using Grok via xAI API (OpenAI-compatible) with retry."""
    import httpx
    for attempt in range(3):
        try:
            response = httpx.post(
                'https://api.x.ai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': 'grok-3-mini-fast',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0,
                    'max_tokens': 100,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            text = response.json()['choices'][0]['message']['content'].strip()
            return parse_scores(text)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"    Grok 429, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"    Grok error: {e}")
            return None
        except Exception as e:
            print(f"    Grok error: {e}")
            return None
    return None


def score_with_gemini(prompt, api_key):
    """Score using Gemini via Google AI API with retry."""
    import httpx
    for attempt in range(3):
        try:
            response = httpx.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}',
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {'temperature': 0, 'maxOutputTokens': 100},
                },
                timeout=30.0,
            )
            response.raise_for_status()
            text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            return parse_scores(text)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"    Gemini 429, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"    Gemini error: {e}")
            return None
        except Exception as e:
            print(f"    Gemini error: {e}")
            return None
    return None


def score_with_llama(prompt, api_key):
    """Score using Llama 3.3 70B via Groq API (OpenAI-compatible)."""
    import httpx
    for attempt in range(3):
        try:
            response = httpx.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0,
                    'max_tokens': 100,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            text = response.json()['choices'][0]['message']['content'].strip()
            return parse_scores(text)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"    Llama 429, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"    Llama error: {e}")
            return None
        except Exception as e:
            print(f"    Llama error: {e}")
            return None
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['haiku', 'grok', 'gemini', 'opus', 'llama'], required=True,
                        help='Which model to run (one at a time)')
    args = parser.parse_args()

    xai_key = os.environ.get('XAI_API_KEY', '')
    gemini_key = os.environ.get('GOOGLE_GEMINI_API_KEY', '')
    groq_key = os.environ.get('GROQ_API_KEY', '')

    models_to_run = []
    if args.model == 'haiku':
        models_to_run.append(('haiku', lambda p: score_with_claude_haiku(p)))
    elif args.model == 'grok':
        if not xai_key:
            print("ERROR: XAI_API_KEY not set"); return
        models_to_run.append(('grok', lambda p: score_with_grok(p, xai_key)))
    elif args.model == 'gemini':
        if not gemini_key:
            print("ERROR: GOOGLE_GEMINI_API_KEY not set"); return
        models_to_run.append(('gemini', lambda p: score_with_gemini(p, gemini_key)))
    elif args.model == 'opus':
        models_to_run.append(('opus', lambda p: score_with_opus(p)))
    elif args.model == 'llama':
        if not groq_key:
            print("ERROR: GROQ_API_KEY not set"); return
        models_to_run.append(('llama', lambda p: score_with_llama(p, groq_key)))

    print(f"Running model: {args.model}")

    raw_data, scores = load_data()
    tasks = load_tasks()
    samples, run_lookup = select_samples(raw_data, scores, n=100)
    print(f"Selected {len(samples)} samples")

    for model_name, score_fn in models_to_run:
        print(f"\n{'='*50}")
        print(f"  Scoring with: {model_name}")
        print(f"{'='*50}")

        pairs = []
        errors = 0

        for i, sample in enumerate(samples):
            run_key = (sample['pattern'], sample['task_id'])
            run = run_lookup.get(run_key)
            if not run:
                errors += 1
                continue

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
                task=task_text, rubric=rubric,
                turn_index=sample['turn_index'],
                cumulative_text=cumulative[:3000],
            )

            if i > 0:
                time.sleep(2)  # rate limit padding

            try:
                model_scores = score_fn(prompt)
                if model_scores:
                    pair = {
                        'pattern': sample['pattern'],
                        'task_id': sample['task_id'],
                        'turn_index': sample['turn_index'],
                    }
                    for dim in DIMENSIONS:
                        pair[f'claude_{dim}'] = sample[dim]
                        pair[f'{model_name}_{dim}'] = model_scores[dim]
                    pairs.append(pair)
                    print(f"  [{i+1}/{len(samples)}] {sample['pattern']}/{sample['task_id']}: "
                          f"Claude={sample['overall']:.0f} {model_name}={model_scores['overall']}")
                else:
                    errors += 1
                    print(f"  [{i+1}] Parse error")
            except Exception as e:
                errors += 1
                print(f"  [{i+1}] Error: {e}")

        print(f"\n[OK] {model_name}: {len(pairs)} scored, {errors} errors")

        if not pairs:
            continue

        # Save pairs
        pair_fields = list(pairs[0].keys())
        path = RESULTS_DIR / f'cross_validation_{model_name}.csv'
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=pair_fields)
            writer.writeheader()
            writer.writerows(pairs)

        # Compute correlations
        from scipy import stats
        from sklearn.metrics import cohen_kappa_score

        print(f"\n  === {model_name} Cross-Validation ===")
        for dim in DIMENSIONS:
            claude = [p[f'claude_{dim}'] for p in pairs]
            model = [p[f'{model_name}_{dim}'] for p in pairs]

            if len(set(claude)) < 2 or len(set(model)) < 2:
                print(f"    {dim}: insufficient variance")
                continue

            r, _ = stats.pearsonr(claude, model)
            rho, _ = stats.spearmanr(claude, model)
            kw = cohen_kappa_score(claude, model, weights='quadratic')

            print(f"    {dim:>15}: r={r:.3f} ρ={rho:.3f} κ_w={kw:.3f} "
                  f"(Claude={statistics.mean(claude):.2f} {model_name}={statistics.mean(model):.2f} "
                  f"Δ={statistics.mean(claude)-statistics.mean(model):+.2f})")

        print(f"  Saved: {path}")


if __name__ == '__main__':
    main()
