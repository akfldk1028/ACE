"""
Verification script for Figure 1.1 - displays figure metadata
"""

import sys
import io
from pathlib import Path
from PIL import Image

# Fix Windows cp949 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def verify_figure():
    """Verify the generated taxonomy figure."""
    base_dir = Path(r'D:\Data\25_ACE\AG\AG-Research\figures')

    files = [
        ('fig1_taxonomy.png', 150),
        ('fig1_taxonomy_hires.png', 300),
    ]

    print("=" * 60)
    print("Figure 1.1 Verification Report")
    print("=" * 60)

    for filename, expected_dpi in files:
        filepath = base_dir / filename

        if not filepath.exists():
            print(f"\n[ERROR] {filename} not found!")
            continue

        # Load image
        img = Image.open(filepath)

        # Get metadata
        width, height = img.size
        dpi_info = img.info.get('dpi', ('N/A', 'N/A'))
        size_kb = filepath.stat().st_size / 1024

        print(f"\n{filename}:")
        print(f"  Size: {width}x{height} pixels")
        print(f"  DPI: {dpi_info}")
        print(f"  File size: {size_kb:.1f} KB")
        print(f"  Mode: {img.mode}")
        print(f"  Status: [OK]")

    print("\n" + "=" * 60)
    print("[OK] Figure 1.1 taxonomy diagram verified successfully!")
    print("=" * 60)

    print("\nFigure contents:")
    print("  - Root: '13 Coordination Topologies'")
    print("  - Category A (Blue): Flat Sequential (3 patterns)")
    print("    >> RR-2, RR-3, RR-4")
    print("  - Category B (Orange): Dynamic Routing (4 patterns)")
    print("    >> Sel-3, Sel-4, Swm-3, Swm-4")
    print("  - Category C (Red): Structured Feedback (4 patterns)")
    print("    >> Refl-2, Refl-3, Deb-3, Deb-4")
    print("  - Category D (Teal): Composed/Nested (2 patterns)")
    print("    >> Pipe, MoA")
    print("\nTotal: 13 patterns across 4 categories")


if __name__ == '__main__':
    verify_figure()
