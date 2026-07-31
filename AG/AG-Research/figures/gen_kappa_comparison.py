"""Generate 6-model κ_w comparison chart + bias spectrum."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Data from cross-validation results (overall dimension, actual computed)
models = ['GPT-4o-mini\n(N=40)', 'GPT-5.4\n(N=100)', 'Haiku 4.5\n(N=100)',
          'Grok 3 Mini\n(N=100)', 'Gemini Flash\n(N=100)', 'Opus 4.6\n(N=100)']
providers = ['OpenAI', 'OpenAI', 'Anthropic', 'xAI', 'Google', 'Anthropic']
kappa_w = [0.244, 0.415, 0.425, 0.449, 0.359, 0.507]
delta = [-0.93, +0.69, +0.91, -0.60, -0.82, +0.57]
pearson_r = [0.434, 0.540, 0.662, 0.628, 0.569, 0.632]

# Colors by provider
provider_colors = {
    'OpenAI': '#74b9ff',
    'Anthropic': '#a29bfe',
    'xAI': '#fd79a8',
    'Google': '#55efc4',
}
bar_colors = [provider_colors[p] for p in providers]
edge_colors = ['#2d3436'] * 6

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.5), gridspec_kw={'width_ratios': [3.5, 2]})

# ---- Left: κ_w bar chart ----
x = np.arange(len(models))
bars = ax1.bar(x, kappa_w, 0.6, color=bar_colors, edgecolor=edge_colors, linewidth=0.8)

# Threshold lines
ax1.axhline(y=0.40, color='#2D6A4F', linestyle='--', alpha=0.7, linewidth=1)
ax1.text(5.55, 0.405, 'Moderate', fontsize=8, color='#2D6A4F', fontstyle='italic')
ax1.axhline(y=0.20, color='#999', linestyle=':', alpha=0.5, linewidth=0.8)
ax1.text(5.55, 0.205, 'Fair', fontsize=8, color='#999', fontstyle='italic')

# Value labels
for bar in bars:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
             f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8.5, fontweight='bold')

ax1.set_ylabel("Cohen's Weighted $\\kappa_w$ (Overall)", fontsize=10)
ax1.set_xticks(x)
ax1.set_xticklabels(models, fontsize=8.5)
ax1.set_ylim(0, 0.60)
ax1.set_title('(a) Cross-Model Agreement (6 Models, 4 Providers)', fontsize=10, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# ---- Right: Bias direction spectrum ----
# Sort by delta for visual clarity
order = np.argsort(delta)
sorted_models = [models[i].replace('\n', ' ') for i in order]
sorted_delta = [delta[i] for i in order]
sorted_colors = [bar_colors[i] for i in order]

y = np.arange(len(sorted_models))
bars2 = ax2.barh(y, sorted_delta, 0.5, color=sorted_colors, edgecolor=edge_colors, linewidth=0.8)

ax2.axvline(x=0, color='black', linewidth=0.8)

# Annotate values
for i, (bar, val) in enumerate(zip(bars2, sorted_delta)):
    offset = 0.05 if val >= 0 else -0.05
    ha = 'left' if val >= 0 else 'right'
    ax2.text(val + offset, i, f'{val:+.2f}', ha=ha, va='center', fontsize=8.5, fontweight='bold')

# Zone labels
ax2.text(-1.1, -0.7, '← Lenient', fontsize=8, color='#636e72', fontstyle='italic')
ax2.text(0.65, -0.7, 'Strict →', fontsize=8, color='#636e72', fontstyle='italic')

ax2.set_yticks(y)
ax2.set_yticklabels(sorted_models, fontsize=8.5)
ax2.set_xlabel('$\\Delta$ (Claude $-$ Cross-Validator)', fontsize=10)
ax2.set_title('(b) Bias Direction Across Models', fontsize=10, fontweight='bold')
ax2.set_xlim(-1.3, 1.3)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('D:/Data/25_ACE/AG/AG-Research/figures/fig_kappa_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig('D:/Data/25_ACE/AG/AG-Research/figures/fig_kappa_comparison.pdf', bbox_inches='tight')
print('[OK] Saved fig_kappa_comparison.png + .pdf')
