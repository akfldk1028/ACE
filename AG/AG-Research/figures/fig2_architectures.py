"""
Figure 2: Pattern Architecture Diagrams
========================================
Shows message flow topology for each of the 5 pattern categories:
  A: Flat Sequential (Chain) - linear round-robin
  B1: Centralized Routing (Star) - LLM selector picks next agent
  B2: Decentralized Handoff (Mesh) - agents self-route via tool calls
  C: Structured Feedback - reflection loops and debate cycles
  D: Composed/Nested - pipeline stages and MoA layers

Output: figures/fig2_architectures.png
"""

import sys
import io

# Fix Windows cp949 encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

# Category colors (same as fig1)
COLORS = {
    'A': '#4C78A8',   # Blue
    'B1': '#F58518',  # Orange
    'B2': '#EECA3B',  # Yellow
    'C': '#E45756',   # Red
    'D': '#72B7B2',   # Teal
}

LIGHT_COLORS = {
    'A': '#D4E4F4',
    'B1': '#FDE5CC',
    'B2': '#FFF8CC',
    'C': '#F8D4D4',
    'D': '#D8EDEB',
}


def draw_agent_node(ax, x, y, label, color, size=0.35, fontsize=9, bold=False):
    """Draw a circular agent node."""
    circle = plt.Circle(
        (x, y), size,
        facecolor='white',
        edgecolor=color,
        linewidth=2.5,
        zorder=3
    )
    ax.add_patch(circle)
    ax.text(
        x, y, label,
        ha='center', va='center',
        fontsize=fontsize,
        fontweight='bold' if bold else 'normal',
        color=color,
        zorder=4
    )


def draw_controller_node(ax, x, y, label, color, width=0.8, height=0.5):
    """Draw a rectangular controller/coordinator node."""
    box = FancyBboxPatch(
        (x - width/2, y - height/2),
        width, height,
        boxstyle="round,pad=0.06",
        facecolor=color,
        edgecolor=color,
        alpha=0.2,
        linewidth=2.5,
        zorder=2
    )
    ax.add_patch(box)
    # Border
    border = FancyBboxPatch(
        (x - width/2, y - height/2),
        width, height,
        boxstyle="round,pad=0.06",
        facecolor='none',
        edgecolor=color,
        linewidth=2.5,
        zorder=3
    )
    ax.add_patch(border)
    ax.text(
        x, y, label,
        ha='center', va='center',
        fontsize=9,
        fontweight='bold',
        color=color,
        zorder=4
    )


def draw_arrow(ax, x1, y1, x2, y2, color='#555555', style='->', lw=1.8, curved=False):
    """Draw a directed arrow between two points."""
    rad = 0.2 if curved else 0
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        color=color,
        linewidth=lw,
        mutation_scale=15,
        zorder=1,
        connectionstyle=f"arc3,rad={rad}"
    )
    ax.add_patch(arrow)


def draw_bidirectional_arrow(ax, x1, y1, x2, y2, color='#555555', lw=1.8, rad=0.15):
    """Draw a bidirectional curved arrow."""
    arrow1 = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle='->',
        color=color,
        linewidth=lw,
        mutation_scale=15,
        zorder=1,
        connectionstyle=f"arc3,rad={rad}"
    )
    ax.add_patch(arrow1)
    arrow2 = FancyArrowPatch(
        (x2, y2), (x1, y1),
        arrowstyle='->',
        color=color,
        linewidth=lw,
        mutation_scale=15,
        zorder=1,
        connectionstyle=f"arc3,rad={rad}"
    )
    ax.add_patch(arrow2)


def draw_category_a(ax):
    """Flat Sequential: A1 -> A2 -> A3 -> A4"""
    color = COLORS['A']
    ax.set_title('A: Flat Sequential', fontsize=13, fontweight='bold',
                 color=color, pad=12)

    # Agents in a horizontal line
    agents = ['A1', 'A2', 'A3', 'A4']
    positions = [(1.0, 2.5), (2.5, 2.5), (4.0, 2.5), (5.5, 2.5)]

    for (x, y), label in zip(positions, agents):
        draw_agent_node(ax, x, y, label, color)

    # Arrows between agents
    for i in range(len(positions) - 1):
        x1, y1 = positions[i]
        x2, y2 = positions[i + 1]
        draw_arrow(ax, x1 + 0.38, y1, x2 - 0.38, y2, color=color)

    # Task input arrow
    ax.annotate('', xy=(0.62, 2.5), xytext=(0.0, 2.5),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.text(0.0, 2.82, 'Task', fontsize=8, color='#666666', ha='left')

    # Output arrow
    ax.annotate('', xy=(6.5, 2.5), xytext=(5.88, 2.5),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.text(6.5, 2.82, 'Result', fontsize=8, color='#666666', ha='right')

    # Annotation: round-robin cycling
    ax.annotate(
        'Round-Robin\ncycling',
        xy=(3.25, 2.0),
        fontsize=8,
        color='#888888',
        ha='center',
        style='italic'
    )

    # Dotted return arrow (cycling)
    cycle_arrow = FancyArrowPatch(
        (5.2, 2.1), (1.3, 2.1),
        arrowstyle='->',
        color=color,
        linewidth=1.2,
        linestyle='dashed',
        alpha=0.5,
        mutation_scale=12,
        zorder=1,
        connectionstyle="arc3,rad=-0.3"
    )
    ax.add_patch(cycle_arrow)

    ax.set_xlim(-0.5, 7.0)
    ax.set_ylim(1.0, 3.5)


def draw_category_b1(ax):
    """B1: Centralized Routing (Star) - LLM Selector picks next agent."""
    color = COLORS['B1']
    ax.set_title('B1: Centralized Routing (Star)', fontsize=12, fontweight='bold',
                 color=color, pad=12)

    # Controller (LLM Selector) at center-top
    draw_controller_node(ax, 3.25, 3.0, 'LLM\nSelector', color)

    # Agents in a row below
    agents = ['A1', 'A2', 'A3']
    positions = [(1.3, 1.3), (3.25, 1.3), (5.2, 1.3)]

    for (x, y), label in zip(positions, agents):
        draw_agent_node(ax, x, y, label, color, size=0.32)

    # Arrows from controller to each agent (fan-out)
    for x, y in positions:
        draw_arrow(ax, 3.25, 2.65, x, y + 0.35, color=color, style='->')

    # Return arrows (dashed)
    for x, y in positions:
        ret = FancyArrowPatch(
            (x, y + 0.35), (3.25, 2.65),
            arrowstyle='->', color=color, linewidth=0.8,
            linestyle='dashed', alpha=0.4, mutation_scale=10,
            zorder=0, connectionstyle="arc3,rad=0.15"
        )
        ax.add_patch(ret)

    ax.text(3.25, 0.65, 'Host LLM decides\nnext speaker', fontsize=8,
            color='#888888', ha='center', style='italic')

    ax.set_xlim(-0.2, 6.5)
    ax.set_ylim(0.3, 3.8)


def draw_category_b2(ax):
    """B2: Decentralized Handoff (Mesh) - agents self-route via Handoff tools."""
    color = COLORS['B2']
    ax.set_title('B2: Decentralized Handoff (Mesh)', fontsize=12, fontweight='bold',
                 color=color, pad=12)

    # Agents in a triangle (no central controller)
    agent_positions = [
        (2.0, 1.3, 'A1'),
        (4.5, 1.3, 'A2'),
        (3.25, 3.0, 'Triage'),
    ]

    for x, y, label in agent_positions:
        draw_agent_node(ax, x, y, label, color, size=0.35)

    # Mesh arrows (bidirectional between all pairs)
    pairs = [(0, 1), (1, 2), (2, 0)]
    for i, j in pairs:
        x1, y1, _ = agent_positions[i]
        x2, y2, _ = agent_positions[j]
        dx, dy = x2 - x1, y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        dx, dy = dx/dist, dy/dist
        draw_arrow(ax, x1 + dx * 0.38, y1 + dy * 0.38,
                   x2 - dx * 0.38, y2 - dy * 0.38,
                   color=color, curved=True)

    ax.text(3.25, 0.55, 'Agents route via\nHandoff() tool calls', fontsize=8,
            color='#888888', ha='center', style='italic')

    ax.set_xlim(-0.2, 6.5)
    ax.set_ylim(0.2, 3.8)


def draw_category_c(ax):
    """Structured Feedback: Reflection loop and Debate cycle."""
    color = COLORS['C']
    ax.set_title('C: Structured Feedback', fontsize=13, fontweight='bold',
                 color=color, pad=12)

    # Left side: Reflection (2 agents with feedback loop)
    ax.text(1.5, 3.5, 'Reflection', fontsize=10, fontweight='bold',
            color=color, ha='center', alpha=0.7)

    draw_agent_node(ax, 1.0, 2.5, 'Gen', color, size=0.32)
    draw_agent_node(ax, 2.2, 2.5, 'Critic', color, size=0.32)

    # Forward arrow
    draw_arrow(ax, 1.35, 2.5, 1.85, 2.5, color=color)
    # Feedback arrow (curved below)
    feedback = FancyArrowPatch(
        (1.88, 2.2), (1.32, 2.2),
        arrowstyle='->',
        color=color,
        linewidth=1.5,
        mutation_scale=12,
        zorder=1,
        connectionstyle="arc3,rad=-0.4"
    )
    ax.add_patch(feedback)
    ax.text(1.6, 1.75, 'feedback', fontsize=7, color='#888888',
            ha='center', style='italic')

    # Separator line
    ax.axvline(x=3.1, color='#DDDDDD', linewidth=1, linestyle='--')

    # Right side: Debate (3 agents in a triangle)
    ax.text(4.8, 3.5, 'Debate', fontsize=10, fontweight='bold',
            color=color, ha='center', alpha=0.7)

    debate_positions = [
        (4.0, 2.0, 'D1'),
        (5.6, 2.0, 'D2'),
        (4.8, 3.0, 'D3'),
    ]

    for x, y, label in debate_positions:
        draw_agent_node(ax, x, y, label, color, size=0.32)

    # Debate arrows (bidirectional triangle)
    pairs = [(0, 1), (1, 2), (2, 0)]
    for i, j in pairs:
        x1, y1, _ = debate_positions[i]
        x2, y2, _ = debate_positions[j]
        # Direction from i to j
        dx, dy = x2 - x1, y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        dx, dy = dx/dist, dy/dist
        draw_arrow(
            ax,
            x1 + dx * 0.35, y1 + dy * 0.35,
            x2 - dx * 0.35, y2 - dy * 0.35,
            color=color,
            curved=True
        )

    ax.text(4.8, 1.35, 'round-robin\nexchange', fontsize=7, color='#888888',
            ha='center', style='italic')

    ax.set_xlim(-0.2, 6.5)
    ax.set_ylim(1.0, 3.9)


def draw_category_d(ax):
    """Composed/Nested: Pipeline and MoA."""
    color = COLORS['D']
    ax.set_title('D: Composed/Nested', fontsize=13, fontweight='bold',
                 color=color, pad=12)

    # Top: Pipeline (sequential stages, each is a mini-team)
    ax.text(3.25, 3.7, 'Pipeline', fontsize=10, fontweight='bold',
            color=color, ha='center', alpha=0.7)

    # Stage boxes
    stages = [
        (1.0, 3.0, 'Stage 1'),
        (3.25, 3.0, 'Stage 2'),
        (5.5, 3.0, 'Stage 3'),
    ]
    for x, y, label in stages:
        box = FancyBboxPatch(
            (x - 0.6, y - 0.25), 1.2, 0.5,
            boxstyle="round,pad=0.05",
            facecolor=LIGHT_COLORS['D'],
            edgecolor=color,
            linewidth=2,
            zorder=2
        )
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=9,
                fontweight='bold', color=color, zorder=3)

    # Arrows between stages
    draw_arrow(ax, 1.65, 3.0, 2.62, 3.0, color=color)
    draw_arrow(ax, 3.9, 3.0, 4.87, 3.0, color=color)

    # Separator
    ax.axhline(y=2.15, color='#DDDDDD', linewidth=1, linestyle='--')

    # Bottom: MoA (Mixture of Agents - parallel layer then aggregator)
    ax.text(3.25, 1.9, 'MoA (Mixture-of-Agents)', fontsize=10, fontweight='bold',
            color=color, ha='center', alpha=0.7)

    # Parallel layer
    parallel_agents = [
        (1.0, 1.1, 'P1'),
        (2.5, 1.1, 'P2'),
        (4.0, 1.1, 'P3'),
    ]
    for x, y, label in parallel_agents:
        draw_agent_node(ax, x, y, label, color, size=0.30)

    # Aggregator
    draw_controller_node(ax, 5.8, 1.1, 'Agg', color, width=0.7, height=0.45)

    # Arrows from parallel to aggregator
    for x, y, _ in parallel_agents:
        draw_arrow(ax, x + 0.33, y, 5.42, 1.1, color=color)

    ax.text(2.5, 0.5, 'independent\ngeneration', fontsize=7, color='#888888',
            ha='center', style='italic')
    ax.text(5.8, 0.5, 'aggregate', fontsize=7, color='#888888',
            ha='center', style='italic')

    ax.set_xlim(-0.3, 6.8)
    ax.set_ylim(0.2, 4.0)


def generate_architecture_figure():
    """Generate the complete architecture diagram with 5 subplots (2x3 grid)."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), dpi=150)

    # Remove all axis decorations
    for ax in axes.flat:
        ax.set_aspect('equal')
        ax.axis('off')

    # Draw each category
    draw_category_a(axes[0, 0])
    draw_category_b1(axes[0, 1])
    draw_category_b2(axes[0, 2])
    draw_category_c(axes[1, 0])
    draw_category_d(axes[1, 1])
    # Hide unused 6th subplot
    axes[1, 2].set_visible(False)

    # Overall title
    fig.suptitle(
        'Figure 2: Message Flow Architectures for Each Pattern Category',
        fontsize=14,
        fontweight='bold',
        color='#333333',
        y=0.98
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])

    # Save
    output_dir = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / 'fig2_architectures.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Figure saved to: {output_path}")

    output_path_hires = output_dir / 'fig2_architectures_hires.png'
    plt.savefig(output_path_hires, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] High-res version (300 DPI) saved to: {output_path_hires}")

    plt.close()


if __name__ == '__main__':
    generate_architecture_figure()
    print("\n[OK] Architecture diagram generation complete!")
