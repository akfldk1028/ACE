"""Generate hybrid termination results chart (6 patterns, all categories)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json
import statistics
from pathlib import Path

RESULTS_DIR = Path(r'D:\Data\25_ACE\AG\AG-Research\results\exp05')

PATTERNS = ['swm4', 'rr3', 'refl2', 'debate3', 'sel3', 'pipe']
LABELS = ['Swm-4', 'RR-3', 'Refl-2', 'Debate-3', 'Sel-3', 'Pipe']
CATEGORIES = ['A', 'A', 'B', 'B', 'C', 'D']


def load_data():
    hybrid = json.loads((RESULTS_DIR / 'hybrid_results.json').read_text(encoding='utf-8'))
    hybrid_ok = [r for r in hybrid if not r.get('error')]

    # Load baseline
    for fname in ['raw.json', 'checkpoint.json']:
        path = RESULTS_DIR / fname
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            baseline = [r for r in data
                        if r.get('experiment_id', '').endswith('_baseline')
                        and r.get('pattern') in PATTERNS
                        and not r.get('error')]
            break
    else:
        baseline = []

    return hybrid_ok, baseline


def main():
    hybrid_ok, baseline = load_data()
    n = len(PATTERNS)

    fig, axes = plt.subplots(1, 3, figsize=(18, 4.5))
    colors = {'keyword_hybrid': '#4C78A8', 'adaptive_hybrid': '#E45756', 'max_messages': '#999999'}

    # Build x-labels with category
    xlabels = [f'{LABELS[i]}\n(Cat {CATEGORIES[i]})' for i in range(n)]

    # (a) Termination type breakdown
    ax = axes[0]
    legend_added = set()
    for i, pattern in enumerate(PATTERNS):
        runs = [r for r in hybrid_ok if r['pattern'] == pattern]
        total = len(runs)
        if total == 0:
            continue

        kw = sum(1 for r in runs if r.get('terminated_by') == 'keyword_hybrid') / total * 100
        ad = sum(1 for r in runs if r.get('terminated_by') == 'adaptive_hybrid') / total * 100
        mx = sum(1 for r in runs if r.get('terminated_by') == 'max_messages') / total * 100

        bottom = 0
        for label, val, color in [('Keyword', kw, colors['keyword_hybrid']),
                                   ('Adaptive (\u0394U)', ad, colors['adaptive_hybrid']),
                                   ('Max msgs', mx, colors['max_messages'])]:
            if val > 0:
                show_label = label if label not in legend_added else ''
                ax.bar(i, val, bottom=bottom, color=color, label=show_label, width=0.6)
                if val >= 8:
                    ax.text(i, bottom + val/2, f'{val:.0f}%', ha='center', va='center',
                            fontsize=8, fontweight='bold', color='white')
                bottom += val
                legend_added.add(label)

    ax.set_xticks(range(n))
    ax.set_xticklabels(xlabels, fontsize=8)
    ax.set_ylabel('Termination Type (%)', fontsize=10)
    ax.set_ylim(0, 105)
    ax.legend(fontsize=8, loc='upper right')
    ax.set_title('(a) Who Terminates?', fontsize=10, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # (b) Token comparison: baseline vs hybrid
    ax = axes[1]
    x = np.arange(n)
    width = 0.35

    for i, pattern in enumerate(PATTERNS):
        h_runs = [r for r in hybrid_ok if r['pattern'] == pattern]
        b_runs = [r for r in baseline if r['pattern'] == pattern]

        h_mean = statistics.mean([r['total_tokens'] for r in h_runs]) if h_runs else 0
        b_mean = statistics.mean([r['total_tokens'] for r in b_runs]) if b_runs else 0
        h_std = statistics.stdev([r['total_tokens'] for r in h_runs]) if len(h_runs) > 1 else 0
        b_std = statistics.stdev([r['total_tokens'] for r in b_runs]) if len(b_runs) > 1 else 0

        ax.bar(i - width/2, b_mean/1000, width, yerr=b_std/1000, color='#D3D3D3',
               edgecolor='#888', label='Baseline' if i == 0 else '', capsize=2)
        ax.bar(i + width/2, h_mean/1000, width, yerr=h_std/1000, color='#F4A261',
               edgecolor='#E76F51', label='Hybrid' if i == 0 else '', capsize=2)

        if b_mean > 0:
            savings = (1 - h_mean / b_mean) * 100
            y_pos = max(h_mean, b_mean) / 1000 + max(h_std, b_std) / 1000 + 0.3
            ax.text(i, y_pos, f'{savings:+.0f}%',
                    ha='center', fontsize=8, fontweight='bold',
                    color='#E76F51' if savings > 0 else '#888')

    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, fontsize=8)
    ax.set_ylabel('Total Tokens (\u00d710\u00b3)', fontsize=10)
    ax.legend(fontsize=8)
    ax.set_title('(b) Token Savings', fontsize=10, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # (c) Turn count comparison
    ax = axes[2]
    for i, pattern in enumerate(PATTERNS):
        h_runs = [r for r in hybrid_ok if r['pattern'] == pattern]
        b_runs = [r for r in baseline if r['pattern'] == pattern]

        h_turns = [r['turn_count'] for r in h_runs] if h_runs else [0]
        b_turns = [r['turn_count'] for r in b_runs] if b_runs else [0]

        ax.bar(i - width/2, statistics.mean(b_turns), width, color='#D3D3D3',
               edgecolor='#888', label='Baseline' if i == 0 else '')
        ax.bar(i + width/2, statistics.mean(h_turns), width, color='#F4A261',
               edgecolor='#E76F51', label='Hybrid' if i == 0 else '')

    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, fontsize=8)
    ax.set_ylabel('Mean Turns', fontsize=10)
    ax.legend(fontsize=8)
    ax.set_title('(c) Turn Reduction', fontsize=10, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    out_dir = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
    plt.savefig(out_dir / 'fig_hybrid_validation.png', dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / 'fig_hybrid_validation.pdf', bbox_inches='tight')
    print('[OK] Saved fig_hybrid_validation.png + .pdf (6 patterns)')


if __name__ == '__main__':
    main()
