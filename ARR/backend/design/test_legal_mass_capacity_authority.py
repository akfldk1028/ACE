from copy import deepcopy
from dataclasses import dataclass
from inspect import signature
from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.book_language.capacity_contract import (
    evaluate_legal_capacity_authority,
)


@dataclass(frozen=True)
class _CandidateSource:
    metadata: dict


class LegalMassCapacityAuthorityTests(SimpleTestCase):
    def _shared_floor_contract(self, *, failure_reasons=()):
        legal_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [0.0, 0.0],
                [20.0, 0.0],
                [20.0, 20.0],
                [0.0, 20.0],
                [0.0, 0.0],
            ]],
        }
        occupied_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [0.0, 0.0],
                [20.0, 0.0],
                [20.0, 16.7],
                [0.0, 16.7],
                [0.0, 0.0],
            ]],
        }
        return {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "hard_pass": not failure_reasons,
            "failure_reasons": list(failure_reasons),
            "plates": [
                {
                    "floor": floor,
                    "legal_geometry_utm": deepcopy(legal_geometry),
                    "occupied_geometry_utm": deepcopy(occupied_geometry),
                    "gross_area_m2": 334.0,
                    "legal_retention_ratio": 1.0,
                    "support_ratio": 1.0,
                    "hard_pass": not failure_reasons,
                    "failure_reasons": list(failure_reasons),
                }
                for floor in (1, 2)
            ],
        }

    def _capacity_measurement(self, utilization):
        return {
            "schema_version": "arr.maas.source_capacity_measurement.v1",
            "feasible_capacity_utilization": utilization,
        }

    def _capacity_contract(self, *, targets=(350.0, 350.0)):
        return {
            "minimum_utilization": 0.70,
            "target_utilization": 0.80,
            "target_floor_areas_m2": list(targets),
        }

    def test_capacity_miss_remains_legal_and_recommends_revision(self):
        authority = evaluate_legal_capacity_authority(
            self._shared_floor_contract(
                failure_reasons=("insufficient_floor_area",),
            ),
            self._capacity_measurement(0.668),
            self._capacity_contract(),
        )

        self.assertTrue(authority["legal_hard_pass"])
        self.assertTrue(authority["shared_floor_measured"])
        self.assertEqual(authority["feasible_capacity_utilization"], 0.668)
        self.assertEqual(authority["capacity_objective_status"], "below")
        self.assertEqual(authority["per_floor_target_deltas_m2"], [-16.0, -16.0])
        self.assertTrue(authority["revision_recommended"])

    def test_near_threshold_capacity_candidate_is_not_erased(self):
        authority = evaluate_legal_capacity_authority(
            self._shared_floor_contract(
                failure_reasons=("insufficient_floor_area",),
            ),
            self._capacity_measurement(0.6998),
            self._capacity_contract(),
        )

        self.assertTrue(authority["legal_hard_pass"])
        self.assertEqual(authority["capacity_objective_status"], "below")
        self.assertTrue(authority["revision_recommended"])

    def test_floor_target_deltas_are_diagnostic_not_legal_gates(self):
        authority = evaluate_legal_capacity_authority(
            self._shared_floor_contract(
                failure_reasons=("insufficient_floor_area",),
            ),
            self._capacity_measurement(0.75),
            self._capacity_contract(targets=(320.0, 400.0)),
        )

        self.assertTrue(authority["legal_hard_pass"])
        self.assertEqual(authority["per_floor_target_deltas_m2"], [14.0, -66.0])
        self.assertEqual(authority["capacity_objective_status"], "within")

    def test_malformed_or_illegal_floor_evidence_remains_rejected(self):
        malformed_capacity_miss = self._shared_floor_contract(
            failure_reasons=("insufficient_floor_area",),
        )
        malformed_capacity_miss["plates"][0].pop("occupied_geometry_utm")
        for shared_floor_contract in (
            None,
            malformed_capacity_miss,
            self._shared_floor_contract(
                failure_reasons=("floor_outside_legal_envelope",),
            ),
            self._shared_floor_contract(
                failure_reasons=("invalid_floor_topology",),
            ),
        ):
            with self.subTest(shared_floor_contract=shared_floor_contract):
                authority = evaluate_legal_capacity_authority(
                    shared_floor_contract,
                    self._capacity_measurement(0.80),
                    self._capacity_contract(),
                )

                self.assertFalse(authority["legal_hard_pass"])

    def test_coordinate_grid_containment_residue_is_recertified(self):
        contract = self._shared_floor_contract()
        long_edge_m = 100000.0
        grid_residue_m = 0.5e-6
        legal = {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [long_edge_m, 0.0],
                             [long_edge_m, 10.0], [0.0, 10.0], [0.0, 0.0]]],
        }
        occupied = {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [long_edge_m + grid_residue_m, 0.0],
                             [long_edge_m + grid_residue_m, 10.0],
                             [0.0, 10.0], [0.0, 0.0]]],
        }
        plate = contract["plates"][0]
        plate["legal_geometry_utm"] = legal
        plate["occupied_geometry_utm"] = occupied
        plate["gross_area_m2"] = (long_edge_m + grid_residue_m) * 10.0

        result = evaluate_legal_capacity_authority(
            contract,
            self._capacity_measurement(0.9),
            self._capacity_contract(),
        )

        self.assertTrue(result["legal_hard_pass"])
        self.assertEqual(result["plate_recertification_failures"], [])

    def test_material_outside_geometry_retains_distance_and_area_evidence(self):
        contract = self._shared_floor_contract()
        plate = contract["plates"][0]
        plate["occupied_geometry_utm"] = {
            "type": "Polygon",
            "coordinates": [[[19.0, 0.0], [21.0, 0.0], [21.0, 10.0],
                             [19.0, 10.0], [19.0, 0.0]]],
        }
        plate["gross_area_m2"] = 20.0

        result = evaluate_legal_capacity_authority(
            contract,
            self._capacity_measurement(0.9),
            self._capacity_contract(),
        )

        failure = result["plate_recertification_failures"][0]
        self.assertIn("occupied_outside_legal_geometry", failure["reasons"])
        self.assertAlmostEqual(
            failure["measured_values"]["occupied_outside_legal_area_m2"],
            10.0,
        )
        self.assertEqual(
            failure["measured_values"].get("occupied_outside_legal_distance_m"),
            1.0,
        )
        self.assertEqual(
            failure["thresholds"].get("constructive_coordinate_grid_m"),
            1e-6,
        )

    def test_vertical_support_failure_is_unchanged_by_containment_alignment(self):
        contract = self._shared_floor_contract()
        plate = contract["plates"][1]
        plate["support_ratio"] = 0.19

        result = evaluate_legal_capacity_authority(
            contract,
            self._capacity_measurement(0.9),
            self._capacity_contract(),
        )

        self.assertFalse(result["legal_hard_pass"])
        self.assertIn(
            "vertical_support_below_threshold",
            result["plate_recertification_failures"][0]["reasons"],
        )

    def test_plate_recertification_emits_typed_failure_reasons(self):
        def invalid_polygon():
            return {
                "type": "Polygon",
                "coordinates": [[
                    [0.0, 0.0],
                    [20.0, 20.0],
                    [0.0, 20.0],
                    [20.0, 0.0],
                    [0.0, 0.0],
                ]],
            }

        def mutate(case):
            contract = self._shared_floor_contract()
            plate = contract["plates"][case.get("plate_index", 0)]
            if case["reason"] == "malformed_plate":
                contract["plates"][0] = None
            elif case["reason"] == "invalid_legal_polygon":
                plate["legal_geometry_utm"] = invalid_polygon()
            elif case["reason"] == "invalid_occupied_polygon":
                plate["occupied_geometry_utm"] = invalid_polygon()
            elif case["reason"] == "occupied_area_mismatch":
                plate["gross_area_m2"] = 330.0
            elif case["reason"] == "occupied_outside_legal_geometry":
                plate["occupied_geometry_utm"] = {
                    "type": "Polygon",
                    "coordinates": [[
                        [19.0, 0.0], [21.0, 0.0], [21.0, 10.0],
                        [19.0, 10.0], [19.0, 0.0],
                    ]],
                }
                plate["gross_area_m2"] = 20.0
            elif case["reason"] == "legal_retention_below_threshold":
                plate["legal_retention_ratio"] = 0.79
            elif case["reason"] == "vertical_support_below_threshold":
                plate["support_ratio"] = 0.19
            elif case["reason"] == "declared_plate_status_mismatch":
                plate["hard_pass"] = False
            return contract

        cases = (
            {"reason": "malformed_plate"},
            {"reason": "invalid_legal_polygon"},
            {"reason": "invalid_occupied_polygon"},
            {"reason": "occupied_area_mismatch"},
            {"reason": "occupied_outside_legal_geometry"},
            {"reason": "legal_retention_below_threshold"},
            {"reason": "vertical_support_below_threshold", "plate_index": 1},
            {"reason": "declared_plate_status_mismatch"},
        )

        for case in cases:
            with self.subTest(reason=case["reason"]):
                authority = evaluate_legal_capacity_authority(
                    mutate(case),
                    self._capacity_measurement(0.80),
                    self._capacity_contract(),
                )
                records = authority.get("plate_recertification_failures")

                self.assertIsNotNone(records)
                self.assertFalse(authority["legal_hard_pass"])
                self.assertIn(
                    case["reason"],
                    {
                        reason
                        for record in records
                        for reason in record["reasons"]
                    },
                )
                record = next(
                    record
                    for record in records
                    if case["reason"] in record["reasons"]
                )
                self.assertIn("floor_index", record)
                self.assertIn("measured_values", record)
                self.assertIn("thresholds", record)
                self.assertIn("threshold_sources", record)

    def test_candidate_generation_retains_and_annotates_legal_capacity_misses(self):
        from design.maas.book_language.candidate_generation import (
            _retain_candidate_with_legal_capacity_authority,
        )

        for utilization in (0.668, 0.6998):
            with self.subTest(utilization=utilization):
                candidate = _retain_candidate_with_legal_capacity_authority(
                    _CandidateSource(metadata={"candidate": "original"}),
                    self._shared_floor_contract(
                        failure_reasons=("insufficient_floor_area",),
                    ),
                    self._capacity_measurement(utilization),
                    self._capacity_contract(),
                )

                self.assertIsNotNone(candidate)
                self.assertEqual(candidate.metadata["candidate"], "original")
                self.assertTrue(candidate.metadata["legal_hard_pass"])
                self.assertEqual(
                    candidate.metadata["feasible_capacity_utilization"],
                    utilization,
                )
                self.assertEqual(
                    candidate.metadata["capacity_objective_status"],
                    "below",
                )
                self.assertTrue(candidate.metadata["revision_recommended"])

    def test_retained_candidate_carries_final_capacity_evidence_downstream(self):
        from design.maas.book_language.candidate_generation import (
            _retain_candidate_with_legal_capacity_authority,
        )

        measurement = self._capacity_measurement(0.80)
        projection = {
            "alternative_id": "spatial_reserve",
            "hard_pass": True,
        }

        candidate = _retain_candidate_with_legal_capacity_authority(
            _CandidateSource(metadata={"candidate": "measured"}),
            self._shared_floor_contract(),
            measurement,
            self._capacity_contract(),
            capacity_projection=projection,
        )

        self.assertEqual(
            candidate.metadata["source_capacity_measurement"],
            measurement,
        )
        self.assertEqual(
            candidate.metadata["capacity_alternative_projection"],
            projection,
        )

    def test_candidate_generation_rejects_illegal_floor_evidence(self):
        from design.maas.book_language.candidate_generation import (
            _retain_candidate_with_legal_capacity_authority,
        )

        candidate = _retain_candidate_with_legal_capacity_authority(
            _CandidateSource(metadata={}),
            self._shared_floor_contract(
                failure_reasons=("floor_outside_legal_envelope",),
            ),
            self._capacity_measurement(0.80),
            self._capacity_contract(),
        )

        self.assertIsNone(candidate)

    def test_plate_recertification_evidence_survives_terminal_artifact(self):
        from design.maas.book_language import candidate_generation

        contract = self._shared_floor_contract()
        plate = contract["plates"][0]
        plate["occupied_geometry_utm"] = {
            "type": "Polygon",
            "coordinates": [[[19.0, 0.0], [21.0, 0.0], [21.0, 10.0],
                             [19.0, 10.0], [19.0, 0.0]]],
        }
        plate["gross_area_m2"] = 20.0
        rejection_evidence = []
        candidate = candidate_generation._retain_candidate_with_legal_capacity_authority(
            _CandidateSource(metadata={}),
            shared_floor_contract=contract,
            capacity_measurement=self._capacity_measurement(0.9),
            capacity_contract=self._capacity_contract(),
            rejection_evidence_sink=rejection_evidence,
        )
        self.assertIsNone(candidate)

        report_records = []
        candidate_generation._record_projection_authority_failure(
            authority_evidence=rejection_evidence[0],
            report_records=report_records,
            outcome_graph=None,
            program_slug="neighborhood",
            source_seed="test_seed",
            program={},
            principle_id="book:operative:test",
            book_scope="1/1",
            legal_floor_field_hash="test_floor_field",
            scope_counts={},
            geometry_stages={},
            llm_authored_failure_counts={},
        )

        evidence = report_records[0]["evidence"]
        failures = evidence.get("plate_recertification_failures")
        self.assertIsNotNone(failures)
        self.assertEqual(
            failures[0]["measured_values"]["occupied_outside_legal_distance_m"],
            1.0,
        )
        certificate_failures = report_records[0][
            "terminal_certificate_evidence"
        ].get("plate_recertification_failures")
        self.assertIsNotNone(certificate_failures)
        self.assertEqual(
            certificate_failures[0]["measured_values"][
                "occupied_outside_legal_area_m2"
            ],
            10.0,
        )

    def test_rejected_authority_records_terminal_projection_failure(self):
        from design.maas.book_language import candidate_generation

        rejection_evidence = []
        self.assertIn(
            "rejection_evidence_sink",
            signature(
                candidate_generation._retain_candidate_with_legal_capacity_authority
            ).parameters,
        )
        candidate = candidate_generation._retain_candidate_with_legal_capacity_authority(
            _CandidateSource(metadata={}),
            self._shared_floor_contract(
                failure_reasons=("floor_outside_legal_envelope",),
            ),
            self._capacity_measurement(0.80),
            self._capacity_contract(),
            rejection_evidence_sink=rejection_evidence,
        )
        recorder = getattr(
            candidate_generation,
            "_record_projection_authority_failure",
            None,
        )

        self.assertIsNone(candidate)
        self.assertIsNotNone(recorder)
        self.assertEqual(len(rejection_evidence), 1)
        terminal_records = []
        scope_counts = {"projection_failed": 0}
        geometry_stages = {
            "projection_failed": 0,
            "projection_authority_failed": 0,
        }
        llm_failure_counts = {}
        program = SimpleNamespace(
            metadata={"family": "llm_twist_carve_void"},
            program_hash=lambda: "r45-program-hash",
            to_dict=lambda: {
                "name": "r45-program",
                "metadata": {"family": "llm_twist_carve_void"},
            },
        )

        recorder(
            authority_evidence=rejection_evidence[0],
            report_records=terminal_records,
            outcome_graph=None,
            program_slug="neighborhood",
            source_seed="r45-seed",
            program=program,
            principle_id="book:operative:twist",
            book_scope="1/2",
            legal_floor_field_hash="legal-field-hash",
            scope_counts=scope_counts,
            geometry_stages=geometry_stages,
            llm_authored_failure_counts=llm_failure_counts,
        )

        record = terminal_records[0]
        self.assertEqual(record["stage"], "projection_authority")
        self.assertEqual(
            record["evidence"]["failure_reason"],
            "legal_capacity_authority_rejected",
        )
        self.assertEqual(
            record["evidence"]["certificate_causes"],
            ["floor_outside_legal_envelope"],
        )
        witness = record["evidence"]["failure_witness"]
        self.assertFalse(witness["legal_hard_pass"])
        self.assertTrue(witness["shared_floor_measured"])
        self.assertEqual(
            witness["feasible_capacity_utilization"],
            0.8,
        )
        self.assertEqual(scope_counts["projection_failed"], 1)
        self.assertEqual(geometry_stages["projection_failed"], 1)
        self.assertEqual(
            geometry_stages["projection_authority_failed"],
            1,
        )
        self.assertEqual(
            llm_failure_counts["legal_capacity_authority_rejected"],
            1,
        )
