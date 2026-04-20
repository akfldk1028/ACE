"""Regenerate Figure 5: Token Savings from Adaptive ΔU Termination (from paper Table 34 data)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Data from paper_draft.md Table 29 (adaptive λ=0.1 vs baseline)
patterns = ['rr3', 'sel3', 'sel4', 'swm3', 'swm4', 'refl2', 'debate3', 'pipe']
categories = ['A', 'B1', 'B1', 'B2', 'B2', 'C', 'C', 'D']
turn_delta = [19, 27, 26, -15, -65, 92, 5, 1]
token_delta = [32, 63, 47, 205, -70, 258, 8, 11]

cat_colors = {
    'A': '#4C78A8',
    'B1': '#F58518',
    'B2': '#EECA3B',
    'C': '#E45756',
    'D': '#72B7B2',
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

x = np.arange(len(patterns))
bar_colors = [cat_colors[c] for c in categories]

# (a) Turn reduction
bars1 = ax1.bar(x, turn_delta, color=bar_colors, edgecolor='#333', linewidth=0.5)
ax1.axhline(y=0, color='black', linewidth=0.8)
ax1.set_xticks(x)
ax1.set_xticklabels(patterns, fontsize=9)
ax1.set_ylabel('Turn Change (%)', fontsize=10)
ax1.set_title('(a) Average Turn Reduction vs Baseline', fontsize=10, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

for i, (bar, val) in enumerate(zip(bars1, turn_delta)):
    y_pos = val + (3 if val >= 0 else -8)
    ax1.text(bar.get_x() + bar.get_width()/2., y_pos, f'{val:+d}%',
             ha='center', va='bottom' if val >= 0 else 'top', fontsize=8, fontweight='bold')

# (b) Token savings
bars2 = ax2.bar(x, token_delta, color=bar_colors, edgecolor='#333', linewidth=0.5)
ax2.axhline(y=0, color='black', linewidth=0.8)
ax2.set_xticks(x)
ax2.set_xticklabels(patterns, fontsize=9)
ax2.set_ylabel('Token Change (%)', fontsize=10)
ax2.set_title('(b) Average Token Cost Savings vs Baseline', fontsize=10, fontweight='bold')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

for i, (bar, val) in enumerate(zip(bars2, token_delta)):
    y_pos = val + (8 if val >= 0 else -15)
    ax2.text(bar.get_x() + bar.get_width()/2., y_pos, f'{val:+d}%',
             ha='center', va='bottom' if val >= 0 else 'top', fontsize=8, fontweight='bold')

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=cat_colors[c], label=f'Cat {c}') for c in ['A', 'B1', 'B2', 'C', 'D']]
ax2.legend(handles=legend_elements, fontsize=8, loc='upper right')

plt.tight_layout()
out = 'D:/Data/25_ACE/AG/AG-Research/figures/fig_exp05_savings_by_pattern.png'
plt.savefig(out, dpi=300, bbox_inches='tight')
plt.savefig(out.replace('.png', '.pdf'), bbox_inches='tight')
print(f'[OK] Saved {out}')
