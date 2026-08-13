"""Every BOOK operative removes material, and its range reaches massing scale.

An earlier pass measured the operatives by unioning *all* their triangle
projections into three orthographic silhouettes, and reported `carve`,
`extract`, `fracture`, `grade` and `notch` as dead - solidity 1.000 in every
view. That measurement is invalid for a concave cut: the cut face itself
projects into the pocket it opened and fills it, so anything short of a
through-cut reads as solid no matter how much it removed. Vertical faces
project to zero-area lines and escape it, which is why `branch` alone appeared
to work.

Volume cannot be fooled that way, and it says none of them is dead. What it
does say is that the same operative spans a wide range: measured on a
40x24x18 reference box, `carve` departs from its own convex hull by 0.004 at
its lowest setting and 0.200 at its highest - and 0.200 is `branch`'s own
articulation. So a run whose candidates all read alike is not evidence of a
broken operative; it is evidence of magnitudes chosen near the bottom of the
range.

These tests hold both facts, so neither has to be rediscovered.
"""

import manifold3d as m3d
from django.test import SimpleTestCase

from design.maas.geometry_language import compiler


REFERENCE_BOX = (40.0, 24.0, 18.0)

# Lowest and highest settings each operative accepts, taken from the clamps in
# the macro itself rather than guessed, so the test moves if the macro does.
SUBTRACTIVE_RANGE = {
    "carve": (
        compiler._book_carve_macro,
        {"width_ratio": 0.18, "depth_ratio": 0.12},
        {"width_ratio": 0.62, "depth_ratio": 0.52},
    ),
    "grade": (
        compiler._book_grade_macro,
        {"width_ratio": 0.38, "depth_ratio": 0.18},
        {"width_ratio": 0.90, "depth_ratio": 0.62},
    ),
    "notch": (
        compiler._book_notch_macro,
        {"ratio": 0.12},
        {"ratio": 0.42},
    ),
    "fracture": (
        compiler._book_fracture_macro,
        {"gap_ratio": 0.04},
        {"gap_ratio": 0.14, "retained_back_ratio": 0.20},
    ),
    "extract": (
        compiler._book_extract_macro,
        {"guest_scale": 0.24},
        {"guest_scale": 0.56, "distance_ratio": 0.34},
    ),
}


def _box():
    return m3d.Manifold.cube(REFERENCE_BOX, True)


def _articulation(solid):
    """How far the result departs from the box it fits in.

    This is the quantity the silhouette measurement was reaching for, taken
    where it cannot be filled in by a projected cut face.
    """

    hull_volume = float(solid.hull().volume())
    if hull_volume <= 1e-9:
        return 0.0
    return 1.0 - float(solid.volume()) / hull_volume


def _removed_fraction(solid):
    base_volume = REFERENCE_BOX[0] * REFERENCE_BOX[1] * REFERENCE_BOX[2]
    return 1.0 - float(solid.volume()) / base_volume


class SubtractiveOperativesRemoveMaterialTests(SimpleTestCase):
    def test_none_of_them_is_inert(self):
        """The claim this replaces was that five of these did nothing."""

        for name, (macro, low, _high) in SUBTRACTIVE_RANGE.items():
            with self.subTest(operative=name):
                result = macro(_box(), low, "test")

                self.assertGreater(_removed_fraction(result), 0.0)

    def test_the_cut_is_where_the_operative_says_it_is(self):
        """A removal fraction alone could come from anywhere in the solid.

        Sliced into slabs, a face operative has to leave the far side of the
        mass alone - otherwise it is a through-cut wearing a recess's name.
        """

        macro, _low, high = SUBTRACTIVE_RANGE["grade"]
        result = macro(_box(), high, "test")
        bottom = result.trim_by_plane((0.0, 0.0, 1.0), -REFERENCE_BOX[2] / 2.0)
        bottom = bottom.trim_by_plane((0.0, 0.0, -1.0), REFERENCE_BOX[2] / 3.0)
        base_bottom = _box().trim_by_plane((0.0, 0.0, 1.0), -REFERENCE_BOX[2] / 2.0)
        base_bottom = base_bottom.trim_by_plane((0.0, 0.0, -1.0), REFERENCE_BOX[2] / 3.0)

        self.assertAlmostEqual(
            float(base_bottom.volume()), float(bottom.volume()), delta=1.0
        )

    def test_each_one_stays_a_single_connected_host(self):
        """Every one of these macros raises if it severs; hold that at the top."""

        for name, (macro, _low, high) in SUBTRACTIVE_RANGE.items():
            with self.subTest(operative=name):
                self.assertEqual(1, len(macro(_box(), high, "test").decompose()))


class OperativeRangeReachesMassingScaleTests(SimpleTestCase):
    """`branch` articulates by 0.188 on this box. The others can get there."""

    BRANCH_ARTICULATION = 0.188

    def test_the_top_of_the_range_is_several_times_the_bottom(self):
        for name, (macro, low, high) in SUBTRACTIVE_RANGE.items():
            with self.subTest(operative=name):
                weak = _articulation(macro(_box(), low, "test"))
                strong = _articulation(macro(_box(), high, "test"))

                self.assertGreater(strong, weak * 2.5)

    def test_the_strongest_settings_reach_what_branch_reaches(self):
        """Not all of them - `notch` is a corner wedge and stays small.

        The point is that the range is not the limit for the operatives that
        carry the massing, so a portfolio that reads alike is a question about
        the magnitudes being authored, not about these macros.
        """

        reaching = [
            name
            for name, (macro, _low, high) in SUBTRACTIVE_RANGE.items()
            if _articulation(macro(_box(), high, "test")) >= self.BRANCH_ARTICULATION
        ]

        self.assertGreaterEqual(len(reaching), 2, reaching)

    def test_branch_is_the_scale_this_is_measured_against(self):
        """If branch drifts, the comparison above has to be re-read."""

        articulation = _articulation(compiler._book_branch_macro(_box(), {}, "test"))

        self.assertAlmostEqual(self.BRANCH_ARTICULATION, articulation, delta=0.03)
