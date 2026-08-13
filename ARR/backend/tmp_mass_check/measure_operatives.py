"""Measure what each BOOK operative actually removes, by volume.

The previous pass measured the three orthographic silhouettes as a union of all
triangle projections. That is invalid for a concave cut: the cut face itself
projects into the pocket it opened and fills it, so anything short of a
through-cut reads as solid. Five operatives were wrongly called dead that way.

Volume cannot be fooled by that. Each operative is applied to the same reference
solid and reported on:

  removed          - fraction of the base volume the operative took away
  bbox_change      - did it change the outer extents (a through-cut usually does)
  slab_profile     - removed fraction in thin slabs up the height, so a cut that
                     is real but local shows where it lives
  convexity_drop   - 1 - volume/convex_hull_volume, the actual articulation: how
                     far the result departs from the box it fits in
  parts            - connected components; an operative that severs is a bug

Run: python tmp_mass_check/measure_operatives.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

import manifold3d as m3d  # noqa: E402

from design.maas.geometry_language import compiler  # noqa: E402


BASE_SIZE = (40.0, 24.0, 18.0)
SLABS = 6


def _base():
    return m3d.Manifold.cube(BASE_SIZE, True)


def _slab(solid, low, high):
    cut = solid.trim_by_plane((0.0, 0.0, -1.0), -high)
    if cut.is_empty():
        return 0.0
    cut = cut.trim_by_plane((0.0, 0.0, 1.0), low)
    return 0.0 if cut.is_empty() else float(cut.volume())


def _convexity_drop(solid):
    hull = solid.hull()
    hull_volume = float(hull.volume())
    if hull_volume <= 1e-9:
        return 0.0
    return 1.0 - float(solid.volume()) / hull_volume


def measure(name, macro, params):
    base = _base()
    try:
        result = macro(base, params, "measure")
    except Exception as error:  # the operative refused these params
        return {"name": name, "error": f"{type(error).__name__}: {error}"}

    base_volume = float(base.volume())
    minz, maxz = -BASE_SIZE[2] / 2.0, BASE_SIZE[2] / 2.0
    step = (maxz - minz) / SLABS
    profile = []
    for index in range(SLABS):
        low = minz + index * step
        high = low + step
        base_slab = _slab(base, low, high)
        cut_slab = _slab(result, low, high)
        profile.append(0.0 if base_slab <= 1e-9 else 1.0 - cut_slab / base_slab)

    bb_base = base.bounding_box()
    bb_result = result.bounding_box()
    bbox_change = max(abs(a - b) for a, b in zip(bb_base, bb_result))

    return {
        "name": name,
        "removed": 1.0 - float(result.volume()) / base_volume,
        "bbox_change": bbox_change,
        "profile": profile,
        "convexity_drop": _convexity_drop(result),
        "base_convexity_drop": _convexity_drop(base),
        "parts": len(result.decompose()),
    }


OPERATIVES = [
    ("branch", compiler._book_branch_macro, {}),
    ("terminal_split", compiler._book_terminal_split_macro, {}),
    ("carve", compiler._book_carve_macro, {}),
    ("fracture", compiler._book_fracture_macro, {}),
    ("grade", compiler._book_grade_macro, {}),
    ("notch", compiler._book_notch_macro, {}),
    ("extract", compiler._book_extract_macro, {}),
    ("lift_related", compiler._book_lift_related_macro, {}),
    ("lodge", compiler._book_lodge_macro, {}),
    ("rotate", compiler._book_rotate_macro, {}),
]


def main():
    print(f"base {BASE_SIZE}  slabs bottom -> top\n")
    header = f"{'operative':<16}{'removed':>9}{'convex':>9}{'bbox':>8}{'parts':>6}  slab profile"
    print(header)
    print("-" * len(header) + "-" * 30)
    for name, macro, params in OPERATIVES:
        row = measure(name, macro, params)
        if "error" in row:
            print(f"{name:<16}  {row['error']}")
            continue
        profile = " ".join(f"{value:5.2f}" for value in row["profile"])
        print(
            f"{row['name']:<16}"
            f"{row['removed']:>8.1%}"
            f"{row['convexity_drop']:>9.3f}"
            f"{row['bbox_change']:>8.2f}"
            f"{row['parts']:>6}"
            f"  {profile}"
        )


if __name__ == "__main__":
    main()
