"""
Figure 1.1: Taxonomy of 13 Multi-Agent Coordination Patterns

Generates a tree-layout diagram showing 5 categories of coordination topologies:
- A: Flat Sequential / Chain (RR-2, RR-3, RR-4)
- B1: Centralized Routing / Star (Sel-3, Sel-4)
- B2: Decentralized Handoff / Mesh (Swm-3, Swm-4)
- C: Structured Feedback (Refl-2, Refl-3, Debate-3, Debate-4)
- D: Composed/Nested (Pipe, MoA)

Output: figures/fig1_taxonomy.png
"""

import sys
import io

# Fix Windows cp949 encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

# Category colors (publication-quality palette)
COLORS = {
    'A': '#4C78A8',   # Blue - Flat Sequential (Chain)
    'B1': '#F58518',  # Orange - Centralized Routing (Star)
    'B2': '#EECA3B',  # Yellow - Decentralized Handoff (Mesh)
    'C': '#E45756',   # Red - Structured Feedback
    'D': '#72B7B2',   # Teal - Composed/Nested
}

# Topology icons (using ASCII-safe symbols)
ICONS = {
    'A': '>>',       # Linear chain
    'B1': '*',       # Hub-and-spoke (star)
    'B2': '#',       # Mesh/peer-to-peer
    'C': 'O',        # Loop/cycle
    'D': '=',        # Layers
}

# Pattern definitions
PATTERNS = {
    'A': {
        'title': 'Flat Sequential\n(Chain)',
        'patterns': [
            ('RR-2', 2),
            ('RR-3', 3),
            ('RR-4', 4),
        ]
    },
    'B1': {
        'title': 'Centralized\nRouting (Star)',
        'patterns': [
            ('Sel-3', 3),
            ('Sel-4', 4),
        ]
    },
    'B2': {
        'title': 'Decentralized\nHandoff (Mesh)',
        'patterns': [
            ('Swm-3', 3),
            ('Swm-4', 4),
        ]
    },
    'C': {
        'title': 'Structured\nFeedback',
        'patterns': [
            ('Refl-2', 2),
            ('Refl-3', 3),
            ('Debate-3', 3),
            ('Debate-4', 4),
        ]
    },
    'D': {
        'title': 'Composed/\nNested',
        'patterns': [
            ('Pipe', '2+'),
            ('MoA', '3+'),
        ]
    },
}


def draw_pattern_box(ax, x, y, name, agent_count, category, width=1.0, height=0.5):
    """Draw a single pattern box with name, agent count, and icon."""
    color = COLORS[category]
    icon = ICONS[category]

    # Main box with rounded corners
    box = FancyBboxPatch(
        (x - width/2, y - height/2),
        width,
        height,
        boxstyle="round,pad=0.05",
        edgecolor=color,
        facecolor='white',
        linewidth=2.5,
        zorder=3
    )
    ax.add_patch(box)

    # Pattern name (bold)
    ax.text(
        x, y + 0.08,
        name,
        ha='center',
        va='center',
        fontsize=11,
        fontweight='bold',
        color=color,
        zorder=4
    )

    # Agent count (small text)
    ax.text(
        x, y - 0.08,
        f'{agent_count} agents',
        ha='center',
        va='center',
        fontsize=8,
        color='#666666',
        zorder=4
    )

    # Topology icon (top-right corner)
    ax.text(
        x + width/2 - 0.12,
        y + height/2 - 0.12,
        icon,
        ha='center',
        va='center',
        fontsize=10,
        color=color,
        alpha=0.5,
        zorder=4
    )


def draw_category_box(ax, x, y, title, category, width=1.2, height=0.6):
    """Draw a category box (larger, filled background)."""
    color = COLORS[category]

    # Category box with filled background
    box = FancyBboxPatch(
        (x - width/2, y - height/2),
        width,
        height,
        boxstyle="round,pad=0.08",
        edgecolor=color,
        facecolor=color,
        alpha=0.15,
        linewidth=2.5,
        zorder=2
    )
    ax.add_patch(box)

    # Category title
    ax.text(
        x, y,
        title,
        ha='center',
        va='center',
        fontsize=12,
        fontweight='bold',
        color=color,
        zorder=4
    )


def draw_arrow(ax, x1, y1, x2, y2, color='#333333', style='->'):
    """Draw a connecting arrow."""
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle=style,
        color=color,
        linewidth=1.5,
        alpha=0.6,
        zorder=1,
        connectionstyle="arc3,rad=0"
    )
    ax.add_patch(arrow)


def generate_taxonomy_figure():
    """Generate the complete taxonomy diagram."""
    # Create figure
    fig, ax = plt.subplots(figsize=(20, 6), dpi=150)
    ax.set_xlim(-1, 21)
    ax.set_ylim(-1, 6)
    ax.axis('off')
    ax.set_aspect('equal')

    # Root node
    root_x, root_y = 10, 5
    root_box = FancyBboxPatch(
        (root_x - 1.8, root_y - 0.35),
        3.6,
        0.7,
        boxstyle="round,pad=0.1",
        edgecolor='#333333',
        facecolor='#F5F5F5',
        linewidth=3,
        zorder=3
    )
    ax.add_patch(root_box)
    ax.text(
        root_x, root_y,
        '13 Coordination Topologies',
        ha='center',
        va='center',
        fontsize=14,
        fontweight='bold',
        color='#333333',
        zorder=4
    )

    # Category positions (y=3.2 for all 5 categories)
    category_y = 3.2
    category_positions = {
        'A': 2.0,
        'B1': 5.5,
        'B2': 9.0,
        'C': 13.0,
        'D': 17.5,
    }

    # Draw categories
    for cat_id, x_pos in category_positions.items():
        cat_data = PATTERNS[cat_id]
        draw_category_box(ax, x_pos, category_y, cat_data['title'], cat_id, height=0.7)
        draw_arrow(ax, root_x, root_y - 0.35, x_pos, category_y + 0.35, color=COLORS[cat_id])

    # Pattern positions (bottom layer, y=1.0) — data-driven
    pattern_y = 1.0
    for cat_id, center_x in category_positions.items():
        cat_patterns = PATTERNS[cat_id]['patterns']
        spacing = 1.3
        start_x = center_x - (len(cat_patterns) - 1) * spacing / 2
        for i, (name, count) in enumerate(cat_patterns):
            x = start_x + i * spacing
            draw_pattern_box(ax, x, pattern_y, name, count, cat_id)
            draw_arrow(ax, center_x, category_y - 0.35, x, pattern_y + 0.25, color=COLORS[cat_id])

    # Legend (topology icons)
    legend_y = 0.2
    legend_items = [
        ('>>', 'Chain', COLORS['A']),
        ('*', 'Star', COLORS['B1']),
        ('#', 'Mesh', COLORS['B2']),
        ('O', 'Feedback', COLORS['C']),
        ('=', 'Nested', COLORS['D']),
    ]

    legend_x = 1.5
    for i, (icon, label, color) in enumerate(legend_items):
        x = legend_x + i * 3.2
        ax.text(x, legend_y, icon, fontsize=12, color=color, ha='left', va='center')
        ax.text(x + 0.4, legend_y, label, fontsize=9, color='#666666', ha='left', va='center')

    # Title annotation
    ax.text(
        10, -0.5,
        'Figure 1.1: Taxonomy of Multi-Agent Coordination Patterns',
        ha='center',
        va='center',
        fontsize=10,
        color='#666666',
        style='italic'
    )

    # Tight layout
    plt.tight_layout()

    # Save
    output_dir = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'fig1_taxonomy.png'

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none'
    )
    print(f"[OK] Figure saved to: {output_path}")

    # Also save as high-res for publication
    output_path_hires = output_dir / 'fig1_taxonomy_hires.png'
    plt.savefig(
        output_path_hires,
        dpi=300,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none'
    )
    print(f"[OK] High-res version (300 DPI) saved to: {output_path_hires}")

    plt.close()


if __name__ == '__main__':
    generate_taxonomy_figure()
    print("\n[OK] Taxonomy diagram generation complete!")
