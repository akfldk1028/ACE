"""The axes must mean the same thing on every parcel.

A pipeline that reaches a good portfolio by being tuned to one site is worth
nothing: the next address arrives with a different area, a different 건폐율, a
different orientation and a different shape. So the two axes an architect
chooses along are defined as dimensionless quantities over the parcel's own
certified numbers, and this file holds them to that.

Ground take is a fraction of the 건폐율 capacity the run certifies, so it scales
with whatever the law allows on that parcel. Void is the open share of the
mass's own tightest rectangle, so it is invariant to size and to rotation.
Neither reads a parcel identifier, an area, or a zoning constant.
"""

from django.test import SimpleTestCase
from shapely import affinity
from shapely.geometry import box

from design.maas.design_space import (
    COVERAGE_BANDS,
    VOID_BANDS,
    capacities_under_band,
    delivered_ground_take_band,
    delivered_void_band,
    plan_area_for_band,
)


def _void(geometry):
    tightest = geometry.minimum_rotated_rectangle
    return max(0.0, 1.0 - geometry.area / tightest.area)


class GroundTakeIsSiteIndependentTests(SimpleTestCase):
    # Three parcels that share nothing: a tight urban lot at 60 percent, the
    # Uijeongbu parcel's 20 percent, and a large site at 40.
    PARCELS = (
        ("tight urban 60%", 330.0, 60.0),
        ("uijeongbu 20%", 2499.691, 20.0),
        ("large site 40%", 18000.0, 40.0),
    )

    def test_a_band_asks_for_the_same_share_of_whatever_the_law_allows(self):
        for name, area, bcr_pct in self.PARCELS:
            capacity = area * bcr_pct / 100.0
            for band in COVERAGE_BANDS:
                self.assertAlmostEqual(
                    band.plan_fraction,
                    plan_area_for_band(capacity, band) / capacity,
                    places=9,
                    msg=f"{name} / {band.band_id}",
                )

    def test_the_delivered_band_reads_a_ratio_not_an_area(self):
        """The same proposition on a small and a huge parcel is one position."""

        for name, area, bcr_pct in self.PARCELS:
            capacity = area * bcr_pct / 100.0
            for band in COVERAGE_BANDS:
                delivered = capacity * band.plan_fraction
                self.assertEqual(
                    band.band_id,
                    delivered_ground_take_band(delivered / capacity).band_id,
                    f"{name} / {band.band_id}",
                )

    def test_bounding_the_stack_scales_with_the_parcel(self):
        for name, area, bcr_pct in self.PARCELS:
            capacity = area * bcr_pct / 100.0
            bounded = capacities_under_band(
                [capacity] * 5,
                ground_capacity_m2=capacity,
                band="dispersed_ground",
            )
            for plate in bounded:
                self.assertAlmostEqual(0.45, plate / capacity, places=9, msg=name)


class VoidIsSiteIndependentTests(SimpleTestCase):
    FIGURES = {
        "plain block": box(0.0, 0.0, 30.0, 20.0),
        "L with a quarter out": box(0.0, 0.0, 30.0, 30.0).difference(
            box(15.0, 15.0, 30.0, 30.0)
        ),
        "courtyard": box(0.0, 0.0, 30.0, 30.0).difference(
            box(7.5, 7.5, 22.5, 22.5)
        ),
        "H with two slots": box(0.0, 0.0, 30.0, 30.0)
        .difference(box(10.0, 15.0, 20.0, 30.0))
        .difference(box(10.0, 0.0, 20.0, 15.0)),
    }

    def test_scale_does_not_move_a_figure_off_its_position(self):
        """A 3 m pavilion and a 300 m block of the same figure are one position."""

        for name, figure in self.FIGURES.items():
            baseline = delivered_void_band(_void(figure)).band_id
            for factor in (0.1, 0.5, 3.0, 10.0):
                scaled = affinity.scale(figure, factor, factor, origin=(0, 0))
                self.assertEqual(
                    baseline,
                    delivered_void_band(_void(scaled)).band_id,
                    f"{name} x{factor}",
                )

    def test_orientation_does_not_move_a_figure_off_its_position(self):
        """How the parcel happens to sit on the grid is not an architectural fact."""

        for name, figure in self.FIGURES.items():
            baseline = delivered_void_band(_void(figure)).band_id
            for angle in (7, 15, 30, 37, 45, 63, 90):
                rotated = affinity.rotate(figure, angle)
                self.assertEqual(
                    baseline,
                    delivered_void_band(_void(rotated)).band_id,
                    f"{name} @{angle}deg",
                )

    def test_translation_does_not_move_a_figure_off_its_position(self):
        """UTM coordinates are large; the measure must not notice where it sits."""

        for name, figure in self.FIGURES.items():
            baseline = delivered_void_band(_void(figure)).band_id
            moved = affinity.translate(figure, 312_000.0, 4_140_000.0)

            self.assertEqual(
                baseline,
                delivered_void_band(_void(moved)).band_id,
                name,
            )

    def test_a_solid_figure_stays_solid_under_every_transform(self):
        solid = box(0.0, 0.0, 30.0, 20.0)
        for angle in (0, 15, 30, 37, 45):
            for factor in (0.2, 1.0, 8.0):
                shape = affinity.scale(
                    affinity.rotate(solid, angle), factor, factor
                )
                self.assertEqual(
                    "solid_body",
                    delivered_void_band(_void(shape)).band_id,
                    f"{angle}deg x{factor}",
                )


class TheAxesCarryNoParcelConstantsTests(SimpleTestCase):
    def test_every_band_edge_is_a_dimensionless_share(self):
        """Nothing here is an area, a length, or a zoning number."""

        for band in COVERAGE_BANDS:
            self.assertGreater(band.plan_fraction, 0.0)
            self.assertLessEqual(band.plan_fraction, 1.0)
        for band in VOID_BANDS:
            self.assertGreaterEqual(band.void_ceiling, 0.0)
            self.assertLessEqual(band.void_ceiling, 1.0)

    def test_an_absent_capacity_yields_no_plate_on_any_parcel(self):
        for capacity in (0.0, -1.0, float("nan"), None):
            self.assertEqual(
                0.0, plan_area_for_band(capacity, "dispersed_ground"), capacity
            )
