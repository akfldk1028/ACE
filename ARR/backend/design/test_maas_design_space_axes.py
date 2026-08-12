"""건폐율 is a ceiling to choose under, not a target to reach.

Measured on PNU 4115011300106840001 before these bands existed: 86 of 128
delivered masses sat within one percent of the coverage cap, median exactly
1.000. Plan area was derived from floor area, so it was always maximal and
every proposal had the same silhouette envelope.
"""

from django.test import SimpleTestCase

from design.maas.design_space import (
    COVERAGE_BANDS,
    CoverageBand,
    coverage_band,
    coverage_band_ids,
    delivered_ground_take_band,
    delivered_void_band,
    VOID_BANDS,
    void_band,
    void_band_ids,
    plan_area_for_band,
)


CAPACITY_M2 = 499.938


class CoverageBandTests(SimpleTestCase):
    def test_the_bands_are_distinct_positions_not_neighbours(self):
        """Proposals a few percent of ground apart are the same proposal."""

        fractions = sorted(band.plan_fraction for band in COVERAGE_BANDS)

        self.assertGreaterEqual(len(fractions), 3)
        for lower, upper in zip(fractions, fractions[1:]):
            self.assertGreaterEqual(upper - lower, 0.1)

    def test_every_band_is_legal_by_construction(self):
        for band in COVERAGE_BANDS:
            self.assertGreater(band.plan_fraction, 0.0)
            self.assertLessEqual(band.plan_fraction, 1.0)
            self.assertLessEqual(
                plan_area_for_band(CAPACITY_M2, band),
                CAPACITY_M2 + 1e-9,
                band.band_id,
            )

    def test_filling_the_ground_is_one_band_among_several(self):
        full = [band for band in COVERAGE_BANDS if band.plan_fraction >= 1.0]

        self.assertEqual(1, len(full))
        self.assertLess(len(full), len(COVERAGE_BANDS))

    def test_a_band_asks_for_its_fraction_of_the_certified_capacity(self):
        self.assertAlmostEqual(
            CAPACITY_M2 * 0.45,
            plan_area_for_band(CAPACITY_M2, "dispersed_ground"),
            places=6,
        )

    def test_bands_resolve_by_id_and_reject_unknown_ones(self):
        for band_id in coverage_band_ids():
            self.assertIsInstance(coverage_band(band_id), CoverageBand)
        with self.assertRaises(KeyError):
            coverage_band("as_much_as_possible")

    def test_an_absent_capacity_yields_no_plate_rather_than_a_guess(self):
        for capacity in (0.0, -12.0, float("nan"), None, "wide"):
            self.assertEqual(
                0.0,
                plan_area_for_band(capacity, "held_ground"),
                capacity,
            )

    def test_band_ids_are_unique(self):
        self.assertEqual(len(COVERAGE_BANDS), len(set(coverage_band_ids())))


class DeliveredGroundTakeBandTests(SimpleTestCase):
    """A quota must count what was built, not what was asked for.

    The portfolio quota used to count BOOK base volume scopes - an authoring
    abstraction that does not survive into the form. Reading the delivered
    ground take back onto the same axis makes the quota spread over something
    an architect can see: a mass that asked to disperse and came out filling
    the ground counts as full ground, because that is what it is.
    """

    def test_a_ratio_lands_in_the_lowest_band_that_can_hold_it(self):
        self.assertEqual(
            "dispersed_ground",
            delivered_ground_take_band(0.40).band_id,
        )
        self.assertEqual("held_ground", delivered_ground_take_band(0.58).band_id)
        self.assertEqual("worked_ground", delivered_ground_take_band(0.80).band_id)
        self.assertEqual("full_ground", delivered_ground_take_band(0.95).band_id)

    def test_a_band_edge_belongs_to_its_own_band(self):
        for band in COVERAGE_BANDS:
            self.assertEqual(
                band.band_id,
                delivered_ground_take_band(band.plan_fraction).band_id,
                band.band_id,
            )

    def test_the_bands_actually_separate_the_delivered_spread(self):
        """The live medians must not collapse into one bucket."""

        measured = {"dispersed": 0.582, "held": 0.794, "worked": 0.804, "full": 1.000}
        landed = {
            name: delivered_ground_take_band(value).band_id
            for name, value in measured.items()
        }

        self.assertGreaterEqual(len(set(landed.values())), 3, landed)

    def test_filling_past_the_cap_is_still_full_ground(self):
        self.assertEqual("full_ground", delivered_ground_take_band(1.09).band_id)

    def test_an_unmeasured_take_does_not_crash_the_quota(self):
        for value in (None, "wide", float("nan"), -1.0):
            self.assertEqual(
                "dispersed_ground",
                delivered_ground_take_band(value).band_id,
                value,
            )


class VoidBandTests(SimpleTestCase):
    """Solid or void is the other axis, and it used to be pure loss.

    A court costs floor area and nothing scored it, so a scheme with one always
    lost to the same scheme without. A position cannot lose to another position.
    """

    def test_every_edge_is_a_figure_this_axis_can_name(self):
        """Pin the derivation, not the numbers.

        An arbitrary minimum gap was the earlier test and it asserted nothing
        about architecture - it only re-stated thresholds picked before any
        distribution was measured. Each edge is now the void ratio a named
        figure actually produces, computed from its geometry.
        """

        self.assertEqual(
            [0.09, 0.20, 0.333, 1.00],
            [band.void_ceiling for band in VOID_BANDS],
        )

    def test_a_ratio_lands_in_the_lowest_band_that_can_hold_it(self):
        self.assertEqual("solid_body", delivered_void_band(0.05).band_id)
        self.assertEqual("carved_body", delivered_void_band(0.19).band_id)
        self.assertEqual("open_figure", delivered_void_band(0.30).band_id)
        self.assertEqual("porous_field", delivered_void_band(0.42).band_id)

    def test_a_band_edge_belongs_to_its_own_band(self):
        for band in VOID_BANDS:
            self.assertEqual(
                band.band_id,
                delivered_void_band(band.void_ceiling).band_id,
                band.band_id,
            )

    def test_an_unmeasured_void_is_not_credited_with_one(self):
        """Fail closed toward solid: never award a court that was not measured."""

        for value in (None, "wide", float("nan"), -0.4, 0.0):
            self.assertEqual(
                "solid_body",
                delivered_void_band(value).band_id,
                value,
            )

    def test_band_ids_are_unique(self):
        self.assertEqual(len(VOID_BANDS), len(set(void_band_ids())))
        with self.assertRaises(KeyError):
            void_band("mostly_air")


class VoidBandsAreAnchoredOnFiguresTests(SimpleTestCase):
    """The edges are figures, computed - not thresholds picked before looking.

    Fitting them to one run's distribution was the alternative and is worse: a
    building would change position depending on what was generated beside it,
    and an axis an architect chooses along has to mean the same thing every run.
    """

    FIGURES = {
        "plain block": (0.000, "solid_body"),
        "court 30% of side": (0.090, "solid_body"),
        "notched block": (0.120, "carved_body"),
        "U slot": (0.167, "carved_body"),
        "two bars with a gap": (0.200, "carved_body"),
        "L with a quarter out": (0.250, "open_figure"),
        "H with two slots": (0.333, "open_figure"),
        "cross": (0.375, "porous_field"),
    }

    def test_each_figure_lands_in_the_band_named_after_it(self):
        for figure, (ratio, expected) in self.FIGURES.items():
            self.assertEqual(
                expected,
                delivered_void_band(ratio).band_id,
                f"{figure} at {ratio}",
            )

    def test_a_solid_block_is_solid_at_every_angle(self):
        """The measure this axis reads must not be moved by rotation alone.

        The axis-aligned ratio it replaced read a solid box as 0.351 void at 15
        degrees, 0.484 at 30 and 0.520 at 45 - it was measuring orientation.
        """

        from shapely import affinity
        from shapely.geometry import box

        solid = box(0.0, 0.0, 30.0, 20.0)
        for angle in (0, 15, 30, 37, 45):
            rotated = affinity.rotate(solid, angle)
            tightest = rotated.minimum_rotated_rectangle
            measured = max(0.0, 1.0 - rotated.area / tightest.area)

            self.assertAlmostEqual(0.0, measured, places=6, msg=f"{angle} deg")
            self.assertEqual("solid_body", delivered_void_band(measured).band_id)

    def test_a_courtyard_is_not_solid(self):
        from shapely.geometry import box

        block = box(0.0, 0.0, 30.0, 30.0)
        court = block.difference(box(7.5, 7.5, 22.5, 22.5))
        measured = 1.0 - court.area / court.minimum_rotated_rectangle.area

        self.assertNotEqual("solid_body", delivered_void_band(measured).band_id)
