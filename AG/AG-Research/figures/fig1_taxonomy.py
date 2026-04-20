"""
Figure 1: Representative Topology Diagrams for 6 Multi-Agent Coordination Patterns.

2x3 grid showing agent communication patterns with circular nodes and directed arrows.
Output: figures/fig1_taxonomy.png, figures/fig1_taxonomy.pdf
"""

import sys
import io
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Circle
from pathlib import Path
import numpy as np

# --- Category color scheme ---
COLORS = {
    'A':       '#4C78A8',  # Blue   - Chain
    'B1':      '#F58518',  # Orange - Centralized Star
    'B2':      '#EECA3B',  # Dark gold - Decentralized Mesh
    'C_refl':  '#E45756',  # Red    - Reflection
    'C_debate':'#B07AA1',  # Purple - Debate
    'D':       '#72B7B2',  # Teal   - Pipeline
}

NODE_RADIUS = 0.35
NODE_LW = 3.5          # border linewidth
ARROW_LW = 3.0         # arrow linewidth
ARROW_SHRINK = 18       # shrink from node edge (points)
TITLE_SIZE = 16
LABEL_SIZE = 14
ANNOT_SIZE = 11


def _circle(ax, cx, cy, label, color, radius=NODE_RADIUS, fontsize=LABEL_SIZE):
    """Draw an agent node: white-filled circle with thick colored border."""
    circ = Circle(
        (cx, cy), radius,
        facecolor='white', edgecolor=color, linewidth=NODE_LW, zorder=5
    )
    ax.add_patch(circ)
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color=color, zorder=6)
    return (cx, cy)


def _arrow(ax, start, end, color, style='solid', lw=ARROW_LW,
           shrinkA=ARROW_SHRINK, shrinkB=ARROW_SHRINK,
           connectionstyle='arc3,rad=0', arrowstyle='-|>',
           mutation_scale=18):
    """Draw a directed arrow between two (x,y) points."""
    arrow = FancyArrowPatch(
        start, end,
        arrowstyle=arrowstyle,
        mutation_scale=mutation_scale,
        color=color, linewidth=lw, linestyle=style,
        shrinkA=shrinkA, shrinkB=shrinkB,
        connectionstyle=connectionstyle,
        zorder=3
    )
    ax.add_patch(arrow)
    return arrow


def _label_arrow(ax, x, y, text, color, fontsize=ANNOT_SIZE):
    """Place a small annotation near an arrow."""
    ax.text(x, y, text, ha='center', va='center',
            fontsize=fontsize, fontstyle='italic', color=color, zorder=7,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='none', alpha=0.85))


def _setup_ax(ax, title):
    """Configure a subplot axes."""
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=TITLE_SIZE, fontweight='bold', pad=12)


# ============================================================
# Panel (a): Chain  RR-3
# ============================================================
def draw_sequential(ax):
    _setup_ax(ax, '(a) Chain (A)')
    color = COLORS['A']

    # Three agents on a circle of radius 0.65
    R = 0.65
    angles = [90, 210, 330]  # top, bottom-left, bottom-right
    positions = []
    labels = ['$A_1$', '$A_2$', '$A_3$']

    for i, ang in enumerate(angles):
        rad = math.radians(ang)
        cx, cy = R * math.cos(rad), R * math.sin(rad)
        _circle(ax, cx, cy, labels[i], color)
        positions.append((cx, cy))

    # Curved arrows: A1 -> A2 -> A3 -> A1
    for i in range(3):
        j = (i + 1) % 3
        _arrow(ax, positions[i], positions[j], color, style='solid',
               connectionstyle='arc3,rad=0.25')


# ============================================================
# Panel (b): Centralized Star  Sel-3
# ============================================================
def draw_star(ax):
    _setup_ax(ax, '(b) Centralized Star (B1)')
    color = COLORS['B1']

    # Coordinator in center
    center = _circle(ax, 0, 0, 'Coord', color, fontsize=12)

    # 3 specialists around it
    R = 0.80
    angles = [90, 210, 330]
    labels = ['$S_1$', '$S_2$', '$S_3$']
    positions = []
    for i, ang in enumerate(angles):
        rad = math.radians(ang)
        cx, cy = R * math.cos(rad), R * math.sin(rad)
        _circle(ax, cx, cy, labels[i], color)
        positions.append((cx, cy))

    # Bidirectional: coordinator <-> each specialist (dashed = dynamic routing)
    for pos in positions:
        _arrow(ax, center, pos, color, style='dashed',
               connectionstyle='arc3,rad=0.12')
        _arrow(ax, pos, center, color, style='dashed',
               connectionstyle='arc3,rad=0.12')


# ============================================================
# Panel (c): Decentralized Mesh  Swm-3
# ============================================================
def draw_mesh(ax):
    _setup_ax(ax, '(c) Decentralized Mesh (B2)')
    color = COLORS['B2']
    # Darken the gold for better readability on white
    edge_color = '#C9A820'

    R = 0.65
    angles = [90, 210, 330]
    labels = ['$A_1$', '$A_2$', '$A_3$']
    positions = []
    for i, ang in enumerate(angles):
        rad = math.radians(ang)
        cx, cy = R * math.cos(rad), R * math.sin(rad)
        _circle(ax, cx, cy, labels[i], edge_color)
        positions.append((cx, cy))

    # Fully connected: every pair, both directions (dashed = dynamic)
    for i in range(3):
        for j in range(3):
            if i != j:
                _arrow(ax, positions[i], positions[j], edge_color,
                       style='dashed', connectionstyle='arc3,rad=0.2')


# ============================================================
# Panel (d): Reflection  Refl-2
# ============================================================
def draw_reflection(ax):
    _setup_ax(ax, '(d) Reflection (C)')
    color = COLORS['C_refl']

    gen_pos = _circle(ax, -0.55, 0, 'Gen', color)
    crit_pos = _circle(ax, 0.55, 0, 'Critic', color, fontsize=12)

    # Gen -> Critic (top arc) with "draft" label
    _arrow(ax, gen_pos, crit_pos, color, style='solid',
           connectionstyle='arc3,rad=0.35')
    _label_arrow(ax, 0, 0.45, 'draft', color)

    # Critic -> Gen (bottom arc) with "revise" label
    _arrow(ax, crit_pos, gen_pos, color, style='solid',
           connectionstyle='arc3,rad=0.35')
    _label_arrow(ax, 0, -0.45, 'revise', color)

    # "approve" exit arrow from Critic going right
    _arrow(ax, (0.55 + NODE_RADIUS + 0.02, 0), (1.15, 0), color,
           style='solid', shrinkA=0, shrinkB=0,
           arrowstyle='-|>', mutation_scale=16)
    _label_arrow(ax, 1.05, 0.20, 'done', color)


# ============================================================
# Panel (e): Debate  Deb-3
# ============================================================
def draw_debate(ax):
    _setup_ax(ax, '(e) Debate (C)')
    color = COLORS['C_debate']

    # Moderator on top, two debaters at bottom
    mod_pos = _circle(ax, 0, 0.55, 'Mod', color, fontsize=12)
    d1_pos = _circle(ax, -0.6, -0.45, '$D_1$', color)
    d2_pos = _circle(ax, 0.6, -0.45, '$D_2$', color)

    # D1 -> Mod, D2 -> Mod (arguments go up)
    _arrow(ax, d1_pos, mod_pos, color, style='solid',
           connectionstyle='arc3,rad=0.15')
    _arrow(ax, d2_pos, mod_pos, color, style='solid',
           connectionstyle='arc3,rad=-0.15')

    # Mod -> D1, Mod -> D2 (questions / prompts go down, dashed)
    _arrow(ax, mod_pos, d1_pos, color, style='dashed',
           connectionstyle='arc3,rad=0.15')
    _arrow(ax, mod_pos, d2_pos, color, style='dashed',
           connectionstyle='arc3,rad=-0.15')

    # D1 <-> D2 (cross-debate, dotted)
    _arrow(ax, d1_pos, d2_pos, color, style=(0, (2, 3)),
           connectionstyle='arc3,rad=0.2')
    _arrow(ax, d2_pos, d1_pos, color, style=(0, (2, 3)),
           connectionstyle='arc3,rad=0.2')

    # Labels
    _label_arrow(ax, -0.55, 0.15, 'argue', color)
    _label_arrow(ax, 0.55, 0.15, 'argue', color)
    _label_arrow(ax, 0, -0.6, 'rebut', color)


# ============================================================
# Panel (f): Pipeline  Pipe
# ============================================================
def draw_pipeline(ax):
    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.0, 1.0)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('(f) Pipeline (D)', fontsize=TITLE_SIZE, fontweight='bold', pad=12)

    color = COLORS['D']

    # 5 agents in a horizontal line
    xs = np.linspace(-1.35, 1.35, 5)
    y = 0
    labels = ['$A_1$', '$A_2$', '$A_3$', '$A_4$', '$A_5$']
    positions = []
    for i, x in enumerate(xs):
        _circle(ax, x, y, labels[i], color, radius=0.28, fontsize=12)
        positions.append((x, y))

    # Linear arrows: A1 -> A2 -> ... -> A5
    for i in range(4):
        _arrow(ax, positions[i], positions[i+1], color, style='solid',
               shrinkA=14, shrinkB=14)

    # Stage labels below each node
    stages = ['stage 1', 'stage 2', 'stage 3', 'stage 4', 'stage 5']
    for i, x in enumerate(xs):
        ax.text(x, y - 0.48, stages[i], ha='center', va='center',
                fontsize=10, color='#666666', zorder=6)


# ============================================================
# Main figure
# ============================================================
def generate_figure():
    fig, axes = plt.subplots(2, 3, figsize=(16, 11))
    fig.patch.set_facecolor('white')

    draw_sequential(axes[0, 0])
    draw_star(axes[0, 1])
    draw_mesh(axes[0, 2])
    draw_reflection(axes[1, 0])
    draw_debate(axes[1, 1])
    draw_pipeline(axes[1, 2])

    # Legend at the bottom
    legend_handles = [
        mpatches.Patch(facecolor='white', edgecolor=COLORS['A'], linewidth=3,
                       label='A: Sequential'),
        mpatches.Patch(facecolor='white', edgecolor=COLORS['B1'], linewidth=3,
                       label='B1: Centralized'),
        mpatches.Patch(facecolor='white', edgecolor='#C9A820', linewidth=3,
                       label='B2: Decentralized'),
        mpatches.Patch(facecolor='white', edgecolor=COLORS['C_refl'], linewidth=3,
                       label='C: Reflection'),
        mpatches.Patch(facecolor='white', edgecolor=COLORS['C_debate'], linewidth=3,
                       label='C: Debate'),
        mpatches.Patch(facecolor='white', edgecolor=COLORS['D'], linewidth=3,
                       label='D: Pipeline'),
    ]

    # Arrow style legend items
    from matplotlib.lines import Line2D
    line_handles = [
        Line2D([0], [0], color='#555555', linewidth=2.5, linestyle='solid',
               label='Fixed routing'),
        Line2D([0], [0], color='#555555', linewidth=2.5, linestyle='dashed',
               label='Dynamic routing'),
    ]

    all_handles = legend_handles + line_handles
    fig.legend(handles=all_handles, loc='lower center',
               ncol=4, fontsize=12, frameon=True,
               fancybox=True, edgecolor='#CCCCCC',
               bbox_to_anchor=(0.5, -0.01))

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Save
    out_dir = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
    out_dir.mkdir(parents=True, exist_ok=True)

    for ext in ('png', 'pdf'):
        path = out_dir / f'fig1_taxonomy.{ext}'
        fig.savefig(path, dpi=300, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        print(f'[OK] Saved {path}')

    plt.close(fig)


if __name__ == '__main__':
    generate_figure()
    print('\n[OK] Taxonomy topology diagrams generated.')
