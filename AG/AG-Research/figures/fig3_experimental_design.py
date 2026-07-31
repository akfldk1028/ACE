"""
Figure 3: Experimental Design Overview
=======================================
Shows the 5 experiments, their inputs/outputs, and data flow between them.

Experiment flow:
  exp01 (Pattern Efficiency) → feeds data to → exp02, exp03, exp04
  exp02 (Termination Quality) → per-turn quality scores
  exp03 (Convergence Detection) → convergence analysis from exp01 data
  exp04 (Error Attribution) → error analysis from exp01+exp02 data
  exp05 (Adaptive Termination) → uses findings from exp01-04

Output: figures/fig3_experimental_design.png
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

# Experiment colors
EXP_COLORS = {
    '01': '#4C78A8',  # Blue
    '02': '#F58518',  # Orange
    '03': '#E45756',  # Red
    '04': '#54A24B',  # Green
    '05': '#B279A2',  # Purple
}


def draw_exp_box(ax, x, y, exp_id, title, subtitle, runs, width=2.8, height=1.2):
    """Draw an experiment box."""
    color = EXP_COLORS[exp_id]

    # Main box
    box = FancyBboxPatch(
        (x - width/2, y - height/2),
        width, height,
        boxstyle="round,pad=0.1",
        facecolor='white',
        edgecolor=color,
        linewidth=2.5,
        zorder=3
    )
    ax.add_patch(box)

    # Experiment ID badge
    badge_w, badge_h = 0.7, 0.35
    badge = FancyBboxPatch(
        (x - width/2 + 0.1, y + height/2 - badge_h - 0.05),
        badge_w, badge_h,
        boxstyle="round,pad=0.03",
        facecolor=color,
        edgecolor=color,
        linewidth=1,
        zorder=4
    )
    ax.add_patch(badge)
    ax.text(
        x - width/2 + 0.1 + badge_w/2,
        y + height/2 - badge_h/2 - 0.05,
        f'E{exp_id}',
        ha='center', va='center',
        fontsize=9, fontweight='bold',
        color='white', zorder=5
    )

    # Title
    ax.text(
        x, y + 0.15,
        title,
        ha='center', va='center',
        fontsize=11, fontweight='bold',
        color='#333333', zorder=4
    )

    # Subtitle
    ax.text(
        x, y - 0.12,
        subtitle,
        ha='center', va='center',
        fontsize=8, color='#666666',
        zorder=4
    )

    # Runs count
    ax.text(
        x, y - 0.35,
        f'{runs} runs',
        ha='center', va='center',
        fontsize=8, fontweight='bold',
        color=color, alpha=0.7,
        zorder=4
    )


def draw_data_arrow(ax, x1, y1, x2, y2, label='', color='#999999', curved=False):
    """Draw a data flow arrow with optional label."""
    rad = 0.15 if curved else 0
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle='-|>',
        color=color,
        linewidth=1.5,
        mutation_scale=15,
        zorder=1,
        connectionstyle=f"arc3,rad={rad}"
    )
    ax.add_patch(arrow)

    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(
            mid_x, mid_y + 0.15,
            label,
            ha='center', va='center',
            fontsize=7, color='#888888',
            style='italic',
            zorder=2,
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                      edgecolor='none', alpha=0.8)
        )


def generate_experimental_design():
    """Generate the experimental design overview figure."""
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    ax.set_xlim(-1, 17)
    ax.set_ylim(-0.5, 9)
    ax.axis('off')

    # === Top row: Input ===
    # Task Suite box
    task_box = FancyBboxPatch(
        (6.0, 7.5), 4.0, 0.8,
        boxstyle="round,pad=0.08",
        facecolor='#F5F5F5',
        edgecolor='#333333',
        linewidth=2,
        zorder=3
    )
    ax.add_patch(task_box)
    ax.text(8.0, 7.9, '25 Tasks x 9 Domains', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#333333', zorder=4)
    ax.text(8.0, 7.6, 'science / CS / history / philosophy / law / gaming / eng / biz / med',
            ha='center', va='center', fontsize=8, color='#666666', zorder=4)

    # 13 Patterns box
    patterns_box = FancyBboxPatch(
        (6.0, 6.3), 4.0, 0.8,
        boxstyle="round,pad=0.08",
        facecolor='#F5F5F5',
        edgecolor='#333333',
        linewidth=2,
        zorder=3
    )
    ax.add_patch(patterns_box)
    ax.text(8.0, 6.7, '8 Representative Patterns', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#333333', zorder=4)
    ax.text(8.0, 6.4, 'A(1) + B1(2) + B2(2) + C(2) + D(1) topologies',
            ha='center', va='center', fontsize=8, color='#666666', zorder=4)

    # === Main experiments ===
    # exp01 - Center, primary
    draw_exp_box(ax, 8.0, 4.5, '01', 'Pattern Efficiency',
                 'duration, tokens, turns per pattern', '200')

    # Arrow from inputs to exp01
    draw_data_arrow(ax, 8.0, 6.3, 8.0, 5.15, color='#333333')
    draw_data_arrow(ax, 8.0, 7.5, 8.0, 7.15, color='#333333')

    # exp02 - Left
    draw_exp_box(ax, 3.0, 2.2, '02', 'Termination Quality',
                 'per-turn G-Eval scoring', '100')

    # exp03 - Center-left
    draw_exp_box(ax, 8.0, 2.2, '03', 'Convergence Detection',
                 'KS-test claim stability', 'analysis')

    # exp04 - Right
    draw_exp_box(ax, 13.0, 2.2, '04', 'Error Attribution',
                 '8 error types per pattern', 'analysis')

    # Arrows from exp01 to exp02/03/04
    draw_data_arrow(ax, 6.5, 4.2, 4.5, 2.9, 'run data', EXP_COLORS['01'], curved=True)
    draw_data_arrow(ax, 8.0, 3.85, 8.0, 2.85, 'messages', EXP_COLORS['01'])
    draw_data_arrow(ax, 9.5, 4.2, 11.5, 2.9, 'errors', EXP_COLORS['01'], curved=True)

    # exp05 - Bottom center
    draw_exp_box(ax, 8.0, 0.2, '05', 'Adaptive Termination',
                 '\u0394U(t) = \u0394Q(t) \u2212 \u03bb\u00b7\u0394C(t) \u2192 0', '200')

    # Arrows from exp02/03/04 to exp05
    draw_data_arrow(ax, 3.0, 1.55, 6.5, 0.5, 'quality scores',
                    EXP_COLORS['02'], curved=True)
    draw_data_arrow(ax, 8.0, 1.55, 8.0, 0.85, 'convergence',
                    EXP_COLORS['03'])
    draw_data_arrow(ax, 13.0, 1.55, 9.5, 0.5, 'error patterns',
                    EXP_COLORS['04'], curved=True)

    # === Output annotations on the right ===
    outputs = [
        (15.5, 4.5, 'Tables 1-3', 'Efficiency comparison\nacross topologies', EXP_COLORS['01']),
        (15.5, 3.2, 'Figures 4-6', 'Token/turn distributions\nper category', EXP_COLORS['01']),
        (0.5, 2.2, 'Figure 7', 'Quality curves\n& regret detection', EXP_COLORS['02']),
        (15.5, 2.2, 'Table 7', 'Error taxonomy\ncorrelation', EXP_COLORS['04']),
        (15.5, 0.2, 'Figure 9', 'Pareto frontiers\noptimal lambda', EXP_COLORS['05']),
    ]

    for x, y, title, desc, color in outputs:
        ax.text(x, y + 0.15, title, fontsize=9, fontweight='bold',
                color=color, ha='center', va='center')
        ax.text(x, y - 0.15, desc, fontsize=7, color='#888888',
                ha='center', va='center', style='italic')

    # === Legend: Total runs ===
    legend_box = FancyBboxPatch(
        (0.0, 7.5), 3.5, 1.2,
        boxstyle="round,pad=0.1",
        facecolor='#FAFAFA',
        edgecolor='#CCCCCC',
        linewidth=1,
        zorder=2
    )
    ax.add_patch(legend_box)
    ax.text(1.75, 8.3, 'Total Experiment Budget', ha='center', va='center',
            fontsize=10, fontweight='bold', color='#333333', zorder=3)
    ax.text(1.75, 7.95, '500 LLM calls (v2)', ha='center', va='center',
            fontsize=9, color='#666666', zorder=3)
    ax.text(1.75, 7.65, '200 + 100 + 0 + 0 + 200', ha='center', va='center',
            fontsize=8, color='#999999', zorder=3)

    # Title
    ax.text(8.0, 8.7,
            'Figure 3: Experimental Design - Five Interconnected Experiments',
            ha='center', va='center',
            fontsize=14, fontweight='bold', color='#333333')

    plt.tight_layout()

    # Save
    output_dir = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
    output_path = output_dir / 'fig3_experimental_design.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Figure saved to: {output_path}")

    output_path_hires = output_dir / 'fig3_experimental_design_hires.png'
    plt.savefig(output_path_hires, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] High-res (300 DPI) saved to: {output_path_hires}")

    plt.close()


if __name__ == '__main__':
    generate_experimental_design()
    print("\n[OK] Experimental design diagram complete!")
