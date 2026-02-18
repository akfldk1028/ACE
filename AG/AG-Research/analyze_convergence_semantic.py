"""
Experiment 03: Semantic Convergence Analysis (Embedding-based)
==============================================================
Upgrades Jaccard n-gram convergence to sentence-transformer embeddings.
Uses cosine similarity on all-MiniLM-L6-v2 (384d) embeddings for
meaningful semantic convergence detection.

Reads:  results/exp01/raw.json (200 runs, 8 patterns)
Output: results/exp03/convergence_semantic.csv        (per-run detail)
        results/exp03/convergence_summary_semantic.csv (pattern summary)
        results/exp03/convergence_jaccard_vs_embed.csv (method comparison)
        figures/fig_convergence_semantic.png           (3-panel figure)

Sensitivity analysis: theta = 0.80, 0.85, 0.90
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import csv
import re
import statistics
from pathlib import Path
from collections import defaultdict

import numpy as np

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results')
FIGURES_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
EXP01_DIR = RESULTS_DIR / 'exp01'
EXP03_DIR = RESULTS_DIR / 'exp03'
EXP03_DIR.mkdir(exist_ok=True)

CATEGORY_MAP = {
    'rr2': 'A', 'rr3': 'A', 'rr4': 'A',
    'sel3': 'B1', 'sel4': 'B1',
    'swm3': 'B2', 'swm4': 'B2',
    'refl2': 'C', 'refl3': 'C', 'debate3': 'C', 'debate4': 'C',
    'pipe': 'D', 'moa': 'D',
}

PATTERN_ORDER = ['rr3', 'sel3', 'sel4', 'swm3', 'swm4', 'refl2', 'debate3', 'pipe']
THRESHOLDS = [0.80, 0.85, 0.90]
DEFAULT_THETA = 0.85


def load_model():
    """Load sentence-transformers model."""
    print("[INFO] Loading sentence-transformers model...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("[OK] Model loaded (all-MiniLM-L6-v2, 384d)")
    return model


def cosine_sim(a, b):
    """Cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0


def get_ngrams(text, n=3):
    """Extract word n-grams (for Jaccard comparison)."""
    text = re.sub(r'\s+', ' ', text.lower().strip())
    words = text.split()
    if len(words) < n:
        return set(tuple(words,))
    return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))


def jaccard_similarity(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def analyze_run(run, model, theta=DEFAULT_THETA):
    """Analyze semantic convergence for a single run.

    Returns dict with convergence metrics, or None if insufficient turns.
    """
    turns = run.get('turns', [])
    agent_turns = [t for t in turns if t.get('source', '') != 'user' and t.get('content')]

    if len(agent_turns) < 2:
        return None

    # Collect texts
    texts = [t['content'] for t in agent_turns]

    # Encode all at once (batch for efficiency)
    embeddings = model.encode(texts, show_progress_bar=False)

    # Pairwise cosine similarity between consecutive turns
    sims = []
    for i in range(1, len(embeddings)):
        cos = cosine_sim(embeddings[i-1], embeddings[i])
        # Also compute Jaccard for comparison
        jac = jaccard_similarity(get_ngrams(texts[i-1]), get_ngrams(texts[i]))
        sims.append({
            'turn': i + 1,
            'cosine': cos,
            'jaccard': jac,
        })

    if not sims:
        return None

    # Detect convergence: first turn where cosine >= theta for 2 consecutive pairs
    converged_at = None
    for i in range(len(sims)):
        if sims[i]['cosine'] >= theta:
            if i + 1 < len(sims) and sims[i+1]['cosine'] >= theta:
                converged_at = sims[i]['turn']
                break
            elif i == len(sims) - 1:
                converged_at = sims[i]['turn']

    # Metrics
    cos_values = [s['cosine'] for s in sims]
    jac_values = [s['jaccard'] for s in sims]

    return {
        'pattern': run['pattern'],
        'category': CATEGORY_MAP.get(run['pattern'], '?'),
        'task_id': run['task_id'],
        'agent_turns': len(agent_turns),
        'comparisons': len(sims),
        'converged': converged_at is not None,
        'converged_at': converged_at,
        'final_cosine': cos_values[-1],
        'max_cosine': max(cos_values),
        'mean_cosine': statistics.mean(cos_values),
        'trend_cosine': cos_values[-1] - cos_values[0] if len(cos_values) >= 2 else 0,
        'final_jaccard': jac_values[-1],
        'mean_jaccard': statistics.mean(jac_values),
        'similarities': sims,
    }


def sensitivity_analysis(results, thresholds=THRESHOLDS):
    """Run convergence detection at multiple thresholds."""
    rows = []
    for theta in thresholds:
        by_pattern = defaultdict(list)
        for r in results:
            by_pattern[r['pattern']].append(r)

        for p in PATTERN_ORDER:
            if p not in by_pattern:
                continue
            runs = by_pattern[p]
            # Re-check convergence at this threshold
            conv_count = 0
            for r in runs:
                sims = r['similarities']
                converged = False
                for i in range(len(sims)):
                    if sims[i]['cosine'] >= theta:
                        if i + 1 < len(sims) and sims[i+1]['cosine'] >= theta:
                            converged = True
                            break
                        elif i == len(sims) - 1:
                            converged = True
                if converged:
                    conv_count += 1

            rows.append({
                'theta': theta,
                'pattern': p,
                'category': CATEGORY_MAP.get(p, '?'),
                'n_runs': len(runs),
                'convergence_rate': conv_count / len(runs) * 100,
            })
    return rows


def load_raw_data():
    """Load raw JSON data from exp01."""
    for fname in ['raw.json', 'raw_A_B1_B2_C_D.json']:
        path = EXP01_DIR / fname
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[OK] Loaded {len(data)} runs from {fname}")
            return data
    return []


def save_csv(path, rows, fieldnames):
    """Save list of dicts to CSV."""
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Saved {path}")


def generate_figure(results, sensitivity_rows):
    """Generate 3-panel convergence figure."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        colors = {
            'A': '#4C78A8', 'B1': '#F58518', 'B2': '#EECA3B',
            'C': '#E45756', 'D': '#72B7B2'
        }

        fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

        by_pattern = defaultdict(list)
        for r in results:
            by_pattern[r['pattern']].append(r)

        # Panel (a): Semantic convergence curves (mean cosine sim per turn index)
        ax = axes[0]
        for p in PATTERN_ORDER:
            if p not in by_pattern:
                continue
            runs = by_pattern[p]
            cat = CATEGORY_MAP.get(p, 'A')
            # Collect cosine by turn index
            turn_sims = defaultdict(list)
            for r in runs:
                for s in r['similarities']:
                    turn_sims[s['turn']].append(s['cosine'])
            if not turn_sims:
                continue
            turns_sorted = sorted(turn_sims.keys())
            means = [statistics.mean(turn_sims[t]) for t in turns_sorted]
            ax.plot(turns_sorted, means, marker='o', markersize=3, label=p,
                    color=colors.get(cat, '#999'), linewidth=1.5)

        ax.axhline(y=DEFAULT_THETA, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
        ax.text(ax.get_xlim()[0] + 0.2, DEFAULT_THETA + 0.01, f'θ={DEFAULT_THETA}', fontsize=8, color='gray')
        ax.set_xlabel('Turn Index')
        ax.set_ylabel('Cosine Similarity')
        ax.set_title('(a) Semantic Convergence Curves')
        ax.legend(fontsize=7, ncol=2, loc='lower right')
        ax.set_ylim(0, 1.05)

        # Panel (b): Jaccard vs Embedding comparison (mean per pattern)
        ax = axes[1]
        jac_means = []
        cos_means = []
        bar_colors = []
        for p in PATTERN_ORDER:
            if p in by_pattern:
                runs = by_pattern[p]
                jac_means.append(statistics.mean(r['mean_jaccard'] for r in runs))
                cos_means.append(statistics.mean(r['mean_cosine'] for r in runs))
                bar_colors.append(colors.get(CATEGORY_MAP.get(p, 'A'), '#999'))
            else:
                jac_means.append(0)
                cos_means.append(0)
                bar_colors.append('#999')

        x = np.arange(len(PATTERN_ORDER))
        width = 0.35
        ax.bar(x - width/2, jac_means, width, label='Jaccard (n-gram)', alpha=0.6, color=bar_colors)
        ax.bar(x + width/2, cos_means, width, label='Cosine (embedding)', alpha=0.9, color=bar_colors)
        ax.set_xticks(x)
        ax.set_xticklabels(PATTERN_ORDER, rotation=45)
        ax.set_ylabel('Mean Similarity')
        ax.set_title('(b) Jaccard vs Embedding Similarity')
        ax.legend(fontsize=8)

        # Panel (c): Convergence rate at different thresholds
        ax = axes[2]
        theta_groups = defaultdict(dict)
        for row in sensitivity_rows:
            theta_groups[row['theta']][row['pattern']] = row['convergence_rate']

        x = np.arange(len(PATTERN_ORDER))
        width = 0.25
        for i, theta in enumerate(THRESHOLDS):
            rates = [theta_groups.get(theta, {}).get(p, 0) for p in PATTERN_ORDER]
            ax.bar(x + (i - 1) * width, rates, width, label=f'θ={theta}', alpha=0.7 + i * 0.1)

        ax.set_xticks(x)
        ax.set_xticklabels(PATTERN_ORDER, rotation=45)
        ax.set_ylabel('Convergence Rate (%)')
        ax.set_title('(c) Sensitivity Analysis')
        ax.legend(fontsize=8)
        ax.set_ylim(0, 105)

        plt.suptitle('Experiment 03: Semantic Convergence Analysis (Sentence-BERT Embeddings)',
                      fontsize=13, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.93])

        fig_path = FIGURES_DIR / 'fig_convergence_semantic.png'
        plt.savefig(fig_path, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"[OK] Saved {fig_path}")
        plt.close()
    except Exception as e:
        print(f"[WARN] Figure generation failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    data = load_raw_data()
    if not data:
        print("[ERROR] No raw data found")
        return

    model = load_model()

    # Filter out errored runs
    valid_data = [r for r in data if not r.get('error')]
    print(f"[INFO] Processing {len(valid_data)} valid runs...")

    # Analyze each run
    results = []
    for i, run in enumerate(valid_data):
        r = analyze_run(run, model, theta=DEFAULT_THETA)
        if r:
            results.append(r)
        if (i + 1) % 25 == 0:
            print(f"  [{i+1}/{len(valid_data)}] processed")

    print(f"[OK] Analyzed {len(results)} runs with embeddings")

    # === Save detailed per-run CSV ===
    detail_fields = [
        'pattern', 'category', 'task_id', 'agent_turns', 'comparisons',
        'converged', 'converged_at', 'final_cosine', 'max_cosine', 'mean_cosine',
        'trend_cosine', 'final_jaccard', 'mean_jaccard',
    ]
    detail_rows = [{k: v for k, v in r.items() if k != 'similarities'} for r in results]
    save_csv(EXP03_DIR / 'convergence_semantic.csv', detail_rows, detail_fields)

    # === Summary by pattern ===
    by_pattern = defaultdict(list)
    for r in results:
        by_pattern[r['pattern']].append(r)

    print("\n=== Semantic Convergence Summary (θ=0.85) ===")
    print(f"{'Pattern':<10} {'Cat':<4} {'N':>4} {'Conv%':>6} {'MeanCos':>8} {'FinalCos':>9} "
          f"{'ConvTurn':>9} {'Trend':>7} {'MeanJac':>8}")
    print("-" * 78)

    summary_rows = []
    for p in PATTERN_ORDER:
        if p not in by_pattern:
            continue
        runs = by_pattern[p]
        n = len(runs)
        conv_count = sum(1 for r in runs if r['converged'])
        conv_pct = conv_count / n * 100
        mean_cos = statistics.mean(r['mean_cosine'] for r in runs)
        final_cos = statistics.mean(r['final_cosine'] for r in runs)
        mean_jac = statistics.mean(r['mean_jaccard'] for r in runs)
        conv_turns = [r['converged_at'] for r in runs if r['converged_at'] is not None]
        avg_conv_turn = statistics.mean(conv_turns) if conv_turns else None
        trend = statistics.mean(r['trend_cosine'] for r in runs)
        cat = CATEGORY_MAP.get(p, '?')
        conv_turn_str = f"{avg_conv_turn:.1f}" if avg_conv_turn else "N/A"

        print(f"{p:<10} {cat:<4} {n:>4} {conv_pct:>5.1f}% {mean_cos:>8.3f} {final_cos:>9.3f} "
              f"{conv_turn_str:>9} {trend:>+7.3f} {mean_jac:>8.3f}")

        summary_rows.append({
            'pattern': p, 'category': cat, 'n_runs': n,
            'convergence_rate_pct': f"{conv_pct:.1f}",
            'mean_cosine': f"{mean_cos:.3f}",
            'final_cosine': f"{final_cos:.3f}",
            'avg_convergence_turn': conv_turn_str,
            'trend_cosine': f"{trend:+.3f}",
            'mean_jaccard': f"{mean_jac:.3f}",
        })

    save_csv(EXP03_DIR / 'convergence_summary_semantic.csv', summary_rows,
             list(summary_rows[0].keys()))

    # === Jaccard vs Embedding comparison CSV ===
    compare_rows = []
    for p in PATTERN_ORDER:
        if p not in by_pattern:
            continue
        runs = by_pattern[p]
        compare_rows.append({
            'pattern': p,
            'category': CATEGORY_MAP.get(p, '?'),
            'mean_jaccard': f"{statistics.mean(r['mean_jaccard'] for r in runs):.3f}",
            'mean_cosine': f"{statistics.mean(r['mean_cosine'] for r in runs):.3f}",
            'jaccard_conv_rate': f"{sum(1 for r in runs if r['mean_jaccard'] >= 0.25) / len(runs) * 100:.1f}",
            'cosine_conv_rate_080': '',  # filled by sensitivity
            'cosine_conv_rate_085': '',
            'cosine_conv_rate_090': '',
        })

    # === Sensitivity analysis ===
    print("\n=== Sensitivity Analysis ===")
    sensitivity_rows = sensitivity_analysis(results)

    for row in sensitivity_rows:
        print(f"  θ={row['theta']:.2f}  {row['pattern']:<10} conv={row['convergence_rate']:>5.1f}%")

    # Fill comparison table
    for srow in sensitivity_rows:
        for crow in compare_rows:
            if crow['pattern'] == srow['pattern']:
                crow[f"cosine_conv_rate_0{int(srow['theta']*100)}"] = f"{srow['convergence_rate']:.1f}"

    save_csv(EXP03_DIR / 'convergence_jaccard_vs_embed.csv', compare_rows,
             list(compare_rows[0].keys()))

    # Save sensitivity detail
    sens_fields = ['theta', 'pattern', 'category', 'n_runs', 'convergence_rate']
    save_csv(EXP03_DIR / 'convergence_sensitivity.csv',
             [{k: v for k, v in r.items()} for r in sensitivity_rows], sens_fields)

    # === Category summary ===
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r['category']].append(r)

    print("\n=== By Category ===")
    for cat in ['A', 'B1', 'B2', 'C', 'D']:
        if cat not in by_cat:
            continue
        runs = by_cat[cat]
        conv_pct = sum(1 for r in runs if r['converged']) / len(runs) * 100
        mean_cos = statistics.mean(r['mean_cosine'] for r in runs)
        mean_jac = statistics.mean(r['mean_jaccard'] for r in runs)
        print(f"  {cat}: {len(runs)} runs, conv={conv_pct:.1f}%, "
              f"cosine={mean_cos:.3f}, jaccard={mean_jac:.3f}")

    # === Generate figure ===
    generate_figure(results, sensitivity_rows)

    print("\n[DONE] Semantic convergence analysis complete.")


if __name__ == '__main__':
    main()
