"""건축면적 is the union of the plates, and legal certification has to say so.

Every check in `evaluate_legal_capacity_authority` reads one plate at a time -
its legal geometry, its retention, its vertical support. 건축면적 is not a
per-plate quantity: 건축법 시행령 제119조 제1항 제2호 defines it as the horizontal
projection of the *building*, which is the union of the plates.

Laterally offset plates each pass their own check while their union does not.
On PNU 4115011300106840001 that let a mass measured 1.04x over the coverage
capacity certify with `legal_hard_pass: True`, and 6 of 96 certified plate
sets projected past the cap.
"""

from copy import deepcopy

from django.test import SimpleTestCase

from design.maas.book_language.capacity_contract import (
    evaluate_legal_capacity_authority,
)


def _rectangle(min_x, min_y, max_x, max_y):
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_x, min_y],
            [max_x, min_y],
            [max_x, max_y],
            [min_x, max_y],
            [min_x, min_y],
        ]],
    }


# 1,000 m2 parcel at 50% 건폐율 - the contract's own product, 500 m2.
PARCEL_AREA_M2 = 1000.0
BCR_LIMIT_PCT = 50.0
COVERAGE_CAPACITY_M2 = 500.0
LEGAL_GEOMETRY = _rectangle(0.0, 0.0, 60.0, 60.0)


class LegalAuthorityMeasuresThePlateUnionTests(SimpleTestCase):
    def _contract(self):
        return {
            "schema_version": "arr.maas.feasible_base_capacity.v1",
            "parcel_area_m2": PARCEL_AREA_M2,
            "bcr_limit_pct": BCR_LIMIT_PCT,
            "target_utilization": 0.8,
            "minimum_utilization": 0.3,
            "target_floor_areas_m2": [400.0, 400.0],
        }

    def _shared_floor_contract(self, occupied_geometries):
        return {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "hard_pass": True,
            "failure_reasons": [],
            "plates": [
                {
                    "floor": index + 1,
                    "legal_geometry_utm": deepcopy(LEGAL_GEOMETRY),
                    "occupied_geometry_utm": deepcopy(geometry),
                    "gross_area_m2": 400.0,
                    "legal_retention_ratio": 1.0,
                    "support_ratio": 1.0,
                    "hard_pass": True,
                    "failure_reasons": [],
                }
                for index, geometry in enumerate(occupied_geometries)
            ],
        }

    def _measurement(self):
        return {
            "schema_version": "arr.maas.source_capacity_measurement.v1",
            "feasible_capacity_utilization": 0.6,
        }

    def _authority(self, occupied_geometries):
        return evaluate_legal_capacity_authority(
            self._shared_floor_contract(occupied_geometries),
            self._measurement(),
            self._contract(),
        )

    def test_stacked_plates_within_the_capacity_still_certify(self):
        """20 x 20 twice, one above the other: the union is 400 m2."""

        authority = self._authority([
            _rectangle(0.0, 0.0, 20.0, 20.0),
            _rectangle(0.0, 0.0, 20.0, 20.0),
        ])

        coverage = authority["plate_projection_coverage"]
        self.assertEqual("measured", coverage["status"])
        self.assertAlmostEqual(400.0, coverage["projected_area_m2"], places=3)
        self.assertFalse(coverage["exceeds_capacity"])
        self.assertTrue(authority["legal_hard_pass"])

    def test_offset_plates_under_the_cap_each_but_over_it_together(self):
        """The failure this pins: 400 + 400 sharing 100, projecting 700."""

        authority = self._authority([
            _rectangle(0.0, 0.0, 20.0, 20.0),
            _rectangle(15.0, 0.0, 35.0, 20.0),
        ])

        coverage = authority["plate_projection_coverage"]
        self.assertAlmostEqual(700.0, coverage["projected_area_m2"], places=3)
        self.assertEqual(
            COVERAGE_CAPACITY_M2,
            coverage["coverage_capacity_m2"],
        )
        self.assertTrue(coverage["exceeds_capacity"])
        self.assertFalse(authority["legal_hard_pass"])
        self.assertIn(
            "coverage_projection_exceeds_capacity",
            authority["plate_recertification_failure_reasons"],
        )

    def test_no_single_plate_carries_the_whole_breach(self):
        """Both plates sit under the cap; only the union does not."""

        authority = self._authority([
            _rectangle(0.0, 0.0, 20.0, 20.0),
            _rectangle(15.0, 0.0, 35.0, 20.0),
        ])

        self.assertTrue(authority["plate_projection_coverage"]["exceeds_capacity"])
        for record in authority["plate_recertification_failures"]:
            self.assertNotIn(
                "coverage_projection_exceeds_capacity",
                record.get("reasons") or (),
            )

    def test_a_contract_declaring_no_capacity_reports_rather_than_passing(self):
        contract = self._contract()
        contract["bcr_limit_pct"] = 0.0
        authority = evaluate_legal_capacity_authority(
            self._shared_floor_contract([
                _rectangle(0.0, 0.0, 20.0, 20.0),
                _rectangle(15.0, 0.0, 35.0, 20.0),
            ]),
            self._measurement(),
            contract,
        )

        coverage = authority["plate_projection_coverage"]
        self.assertEqual("unmeasurable", coverage["status"])
        self.assertNotIn("exceeds_capacity", coverage)
