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
