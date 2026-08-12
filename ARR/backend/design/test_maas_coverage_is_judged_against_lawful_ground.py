"""Site coverage has to be judged against the ground the law allows.

Measured on PNU 4115011300106840001: parcel 2499.691 m2, 건폐율 20 percent, so
the legal footprint cap is 499.938 m2 - while the setback host section the ratio
was divided by is 1922.226 m2. The highest ratio any lawful building can reach
there is 0.26, and COVERAGE_RANGES["cultural"] starts at 0.24 with the pass
threshold at 0.55. That made roughly 87 percent of the legal footprint the
minimum a mass had to fill before it could pass the program gate.

Filling the 건폐율 was therefore not one proposal among several. It was a pass
condition, which is why every delivered mass had the same silhouette envelope.
"""

from django.test import SimpleTestCase
from shapely.geometry import box, mapping

from design.maas.program_massing.spatial_evaluation import (
    attach_program_spatial_evidence,
)


PARCEL_M2 = 2499.691
HOST_SECTION_M2 = 1922.226
LAWFUL_GROUND_M2 = 499.938


def _feature(footprint_m2, *, lawful_capacity=LAWFUL_GROUND_M2):
    side = footprint_m2 ** 0.5
    properties = {
        "benchmark_site_area_m2": HOST_SECTION_M2,
        "mass_volumes": [{
            "role": "gallery",
            "bottom_height": 0.0,
            "top_height": 6.0,
            "geometry": mapping(box(0.0, 0.0, side, side)),
        }],
    }
    if lawful_capacity is not None:
        properties["base_capacity_contract"] = {
            "legal_floor_field": {
                "bcr_footprint_capacity_m2": lawful_capacity,
            },
        }
    return {"type": "Feature", "properties": properties,
            "geometry": mapping(box(0.0, 0.0, side, side))}


def _coverage(footprint_m2, **kwargs):
    evidence = attach_program_spatial_evidence(
        _feature(footprint_m2, **kwargs),
        building_type="cultural",
        site_area_m2=HOST_SECTION_M2,
    )
    return evidence


class CoverageIsJudgedAgainstLawfulGroundTests(SimpleTestCase):
    def test_the_denominator_is_the_ground_the_law_allows(self):
        evidence = _coverage(LAWFUL_GROUND_M2)

        self.assertAlmostEqual(
            LAWFUL_GROUND_M2,
            float(evidence["coverage_denominator_m2"]),
            places=2,
        )
        self.assertAlmostEqual(1.0, float(evidence["site_coverage_ratio"]), places=2)

    def test_taking_all_the_law_allows_is_not_penalised(self):
        """The coverage hard gate owns the ceiling; this gate must not re-judge it."""

        evidence = _coverage(LAWFUL_GROUND_M2)

        self.assertGreaterEqual(float(evidence["site_coverage_score"]), 0.55)

    def test_holding_the_ground_passes_the_program_gate(self):
        """A scheme on 45% of its legal footprint is a proposal, not a failure."""

        evidence = _coverage(LAWFUL_GROUND_M2 * 0.45)

        self.assertAlmostEqual(0.45, float(evidence["site_coverage_ratio"]), places=2)
        self.assertGreaterEqual(float(evidence["site_coverage_score"]), 0.55)

    def test_the_whole_lawful_range_survives_the_gate(self):
        for fraction in (0.45, 0.65, 0.85, 1.00):
            evidence = _coverage(LAWFUL_GROUND_M2 * fraction)
            self.assertGreaterEqual(
                float(evidence["site_coverage_score"]),
                0.55,
                f"ground take {fraction}",
            )

    def test_a_sliver_is_still_refused(self):
        """The lower end stays a program judgement - this is not a loosening."""

        evidence = _coverage(LAWFUL_GROUND_M2 * 0.05)

        self.assertLess(float(evidence["site_coverage_score"]), 0.55)

    def test_without_a_capacity_contract_nothing_changes(self):
        """No certified capacity means no invented ceiling."""

        evidence = _coverage(LAWFUL_GROUND_M2, lawful_capacity=None)

        self.assertEqual(0.0, float(evidence["lawful_ground_capacity_m2"]))
        self.assertAlmostEqual(
            HOST_SECTION_M2,
            float(evidence["coverage_denominator_m2"]),
            places=2,
        )
        self.assertAlmostEqual(
            LAWFUL_GROUND_M2 / HOST_SECTION_M2,
            float(evidence["site_coverage_ratio"]),
            places=2,
        )

    def test_the_measurement_says_which_ground_it_used(self):
        self.assertIn(
            "lawful_ground",
            str(_coverage(LAWFUL_GROUND_M2)["coverage_measurement_mode"]),
        )
        self.assertNotIn(
            "lawful_ground",
            str(
                _coverage(LAWFUL_GROUND_M2, lawful_capacity=None)[
                    "coverage_measurement_mode"
                ]
            ),
        )
