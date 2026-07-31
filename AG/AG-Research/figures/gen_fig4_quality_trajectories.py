"""Regenerate Figure 4: Quality Trajectories by Topology (from paper Table 19 data)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Data from paper_draft.md Table 19
data = {
    'rr3':     {'cat': 'A: Flat Sequential', 'scores': [3.9, 4.2, 4.5, 4.1, 4.1, 4.1], 'opt': 3},
    'sel3':    {'cat': 'B1: Centralized Routing', 'scores': [3.8, 3.5, 2.7, 4.0, 4.0], 'opt': 4},
    'swm3':    {'cat': 'B2: Decentralized Handoff', 'scores': [4.2, 3.0, 2.0], 'opt': 1},
    'refl2':   {'cat': 'C: Structured Feedback', 'scores': [3.9, 4.8, 4.0, 4.0], 'opt': 2},
    'debate3': {'cat': 'C: Structured Feedback', 'scores': [3.8, 3.4, 3.3, 3.3], 'opt': 1},
}

colors = {
    'rr3': '#4C78A8',
    'sel3': '#F58518',
    'swm3': '#EECA3B',
    'refl2': '#E45756',
    'debate3': '#72B7B2',
}

fig, axes = plt.subplots(1, 5, figsize=(14, 3.2), sharey=True)

for i, (pattern, info) in enumerate(data.items()):
    ax = axes[i]
    turns = list(range(1, len(info['scores']) + 1))
    scores = info['scores']

    ax.plot(turns, scores, 'o-', color=colors[pattern], linewidth=2, markersize=6, label=f'Mean Q(t)')
    ax.axvline(x=info['opt'], color='red', linestyle='--', alpha=0.6, linewidth=1.5)
    ax.plot(info['opt'], scores[info['opt']-1], '*', color='red', markersize=14, zorder=5,
            label=f'Optimal stop (t={info["opt"]})')

    ax.set_title(f'{pattern}', fontsize=10, fontweight='bold')
    ax.set_xlabel('Agent Turn', fontsize=9)
    if i == 0:
        ax.set_ylabel('Quality Score Q(t)', fontsize=9)
    ax.set_ylim(1.5, 5.2)
    ax.set_xticks(turns)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=6.5, loc='lower left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.suptitle('Quality Trajectories: G-Eval Score per Agent Turn', fontsize=12, fontweight='bold', y=1.02)
plt.tight_layout()

out = 'D:/Data/25_ACE/AG/AG-Research/figures/fig5_quality_trajectories.png'
plt.savefig(out, dpi=300, bbox_inches='tight')
plt.savefig(out.replace('.png', '.pdf'), bbox_inches='tight')
print(f'[OK] Saved {out}')
