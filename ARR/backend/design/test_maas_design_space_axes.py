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
