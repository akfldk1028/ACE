from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language.mass_passport_bridge import (
    _bind_candidate_finalization_to_passport,
    _resolved_capacity_evidence,
    selected_candidate_execution_passport,
)
from design.maas.book_language.portfolio_benchmark import (
    _synchronize_finalization_publish_authority,
)
from design.maas.geometry_language.executed_archive import (
    _archived_capacity_evidence,
    materialize_executed_mass_passport,
)


class Task5BFinalizationAuthorityTest(SimpleTestCase):
    def _valid_evidence(self):
        certificate = {
            "hard_pass": True,
            "program_hash": "program-hash",
            "final_geometry_hash": "geometry-hash",
            "visual_hash": "visual-hash",
            "legal_floor_field_hash": "floor-field-hash",
            "candidate_actual_gfa_stop_hash": "gfa-stop-hash",
        }
        return {
            "schema_version": (
                "arr.maas.candidate_final_mesh_floor_finalization.v1"
            ),
            "status": "certified",
            "hard_pass": True,
            "candidate_actual_gfa_stop_certificate": certificate,
            "measured_identity": {
                "program_hash": "program-hash",
                "final_geometry_hash": "geometry-hash",
                "visual_hash": "visual-hash",
            },
            "legal_floor_field_hash": "floor-field-hash",
            "candidate_actual_gfa_stop_hash": "gfa-stop-hash",
        }

    def _expected_identity(self):
        return {
            "program_hash": "program-hash",
            "final_geometry_hash": "geometry-hash",
            "visual_hash": "visual-hash",
        }

    def _passport(self):
        return {
            "program_hash": "program-hash",
            "visual_hash": "visual-hash",
            "stages": [],
        }

    def test_strict_finalization_rejects_missing_none_and_non_mapping(self):
        for evidence in (None, "not-a-mapping"):
            with self.subTest(evidence=evidence):
                with self.assertRaisesRegex(
                    ValueError,
                    "candidate_finalization_evidence_missing_or_invalid",
                ):
                    _bind_candidate_finalization_to_passport(
                        self._passport(),
                        evidence,
                        expected_identity=self._expected_identity(),
                    )

    def test_strict_finalization_rejects_malformed_and_failed_mapping(self):
        malformed = {"schema_version": "wrong"}
        failed = self._valid_evidence()
        failed.update({"status": "failed", "hard_pass": False})
        for evidence in (malformed, failed):
            with self.subTest(evidence=evidence):
                with self.assertRaisesRegex(
                    ValueError,
                    "candidate_finalization_evidence_invalid_or_failed",
                ):
                    _bind_candidate_finalization_to_passport(
                        self._passport(),
                        evidence,
                        expected_identity=self._expected_identity(),
                    )

    def test_valid_finalization_evidence_binds_strict_passport(self):
        passport = _bind_candidate_finalization_to_passport(
            self._passport(),
            self._valid_evidence(),
            expected_identity=self._expected_identity(),
        )

        self.assertEqual(passport["final_legal_geometry_hash"], "geometry-hash")
        self.assertEqual(passport["legal_floor_field_hash"], "floor-field-hash")
        self.assertEqual(
            passport["candidate_actual_gfa_stop_hash"],
            "gfa-stop-hash",
        )

    def test_v2_binds_requested_target_and_verified_actual_capacity(self):
        evidence = self._valid_evidence()
        evidence.update({
            "schema_version": (
                "arr.maas.candidate_final_mesh_floor_finalization.v2"
            ),
            "candidate_target_gfa_m2": 300.0,
            "requested_candidate_target_gfa_m2": 315.0,
            "achieved_gfa_m2": 300.0,
            "candidate_feasible_maximum_gfa_m2": 400.0,
            "candidate_minimum_capacity_utilization": 0.7,
            "achieved_capacity_utilization": 0.75,
            "capacity_contract_mode": (
                "accepted_actual_gfa_minimum_band"
            ),
            "candidate_capacity_resolution_hard_pass": True,
        })
        evidence["candidate_actual_gfa_stop_certificate"].update({
            "target_gfa_m2": 300.0,
            "achieved_gfa_m2": 300.0,
        })

        passport = _bind_candidate_finalization_to_passport(
            self._passport(),
            evidence,
            expected_identity=self._expected_identity(),
        )

        self.assertEqual(passport["candidate_target_gfa_m2"], 300.0)
        self.assertEqual(
            passport["requested_candidate_target_gfa_m2"],
            315.0,
        )
        self.assertEqual(
            passport["achieved_capacity_utilization"],
            0.75,
        )

        for key, value in (
            ("achieved_capacity_utilization", 0.69),
            ("candidate_minimum_capacity_utilization", 0.8),
        ):
            tampered = deepcopy(evidence)
            tampered[key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(
                    ValueError,
                    "candidate_finalization_capacity_contract_mismatch",
                ):
                    _bind_candidate_finalization_to_passport(
                        self._passport(),
                        tampered,
                        expected_identity=self._expected_identity(),
                    )

    def test_relaxed_missing_finalization_is_explicit_and_typed(self):
        diagnostic_passport = self._passport()
        diagnostic_passport["stages"] = [{
            "id": "selector",
            "status": "passed",
            "evidence": {"selected": True, "hard_pass": True},
        }]
        passport = _bind_candidate_finalization_to_passport(
            diagnostic_passport,
            None,
            allow_relaxed_finalization=True,
            expected_identity=self._expected_identity(),
        )

        stage = passport["stages"][-1]
        self.assertEqual(stage["id"], "candidate_finalization_fallback")
        self.assertFalse(stage["required_for_final"])
        self.assertEqual(
            stage["evidence"]["reason"],
            "candidate_finalization_evidence_missing_or_invalid",
        )
        self.assertFalse(passport["hard_pass"])
        self.assertFalse(passport["final_hard_pass"])
        self.assertFalse(passport["publishable"])
        self.assertEqual(passport["status"], "diagnostic_non_publishable")
        selector = next(
            stage for stage in passport["stages"] if stage["id"] == "selector"
        )
        self.assertEqual(selector["status"], "failed")
        self.assertFalse(selector["evidence"]["selected"])
        self.assertFalse(selector["evidence"]["hard_pass"])

    def test_strict_rejects_empty_or_partial_certificate_and_identity(self):
        cases = {
            "empty_certificate": (
                "candidate_actual_gfa_stop_certificate",
                {},
            ),
            "empty_identity": ("measured_identity", {}),
            "partial_certificate": (
                "candidate_actual_gfa_stop_certificate",
                {"hard_pass": True, "program_hash": "program-hash"},
            ),
            "partial_identity": (
                "measured_identity",
                {"program_hash": "program-hash"},
            ),
        }
        for label, (field, value) in cases.items():
            evidence = self._valid_evidence()
            evidence[field] = value
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, "missing_required_field"):
                    _bind_candidate_finalization_to_passport(
                        self._passport(),
                        evidence,
                        expected_identity=self._expected_identity(),
                    )

    def test_strict_rejects_every_required_hash_absence_and_mismatch(self):
        locations = (
            ("payload", "legal_floor_field_hash"),
            ("payload", "candidate_actual_gfa_stop_hash"),
            ("identity", "program_hash"),
            ("identity", "final_geometry_hash"),
            ("identity", "visual_hash"),
            ("certificate", "program_hash"),
            ("certificate", "final_geometry_hash"),
            ("certificate", "visual_hash"),
            ("certificate", "legal_floor_field_hash"),
            ("certificate", "candidate_actual_gfa_stop_hash"),
        )
        for location, key in locations:
            for value, reason in (
                ("", "missing_required_field"),
                ("mismatch", "identity_mismatch"),
            ):
                evidence = self._valid_evidence()
                target = (
                    evidence
                    if location == "payload"
                    else evidence["measured_identity"]
                    if location == "identity"
                    else evidence["candidate_actual_gfa_stop_certificate"]
                )
                target[key] = value
                with self.subTest(location=location, key=key, value=value):
                    with self.assertRaisesRegex(ValueError, reason):
                        _bind_candidate_finalization_to_passport(
                            self._passport(),
                            evidence,
                            expected_identity=self._expected_identity(),
                        )

    def test_relaxed_invalid_failed_and_mismatched_are_non_publishable(self):
        malformed = {"schema_version": "wrong"}
        failed = self._valid_evidence()
        failed.update({"status": "failed", "hard_pass": False})
        mismatched = self._valid_evidence()
        mismatched["measured_identity"]["final_geometry_hash"] = "stale"
        for evidence in (malformed, failed, mismatched):
            with self.subTest(evidence=evidence):
                passport = _bind_candidate_finalization_to_passport(
                    {**self._passport(), "hard_pass": True, "final_hard_pass": True},
                    evidence,
                    allow_relaxed_finalization=True,
                    expected_identity=self._expected_identity(),
                )
                self.assertFalse(passport["hard_pass"])
                self.assertFalse(passport["final_hard_pass"])
                self.assertFalse(passport["publishable"])
                self.assertEqual(
                    passport["status"],
                    "diagnostic_non_publishable",
                )
                self.assertTrue(
                    passport["stages"][-1]["evidence"]["reason"].startswith(
                        "candidate_finalization_"
                    )
                )

    @patch(
        "design.maas.book_language.mass_passport_bridge.build_mass_execution_passport"
    )
    def test_selected_candidate_production_rejects_artifact_final_hash_mismatch(
        self,
        build_passport,
    ):
        build_passport.return_value = self._passport()
        evidence = self._valid_evidence()

        with self.assertRaisesRegex(ValueError, "identity_mismatch"):
            selected_candidate_execution_passport(
                compilation={
                    "certified_compilation": SimpleNamespace(
                        geometry_hash="visual-hash"
                    ),
                    "combined_hard_pass": True,
                },
                downstream_row={},
                source_metadata={},
                program_evidence={},
                descriptor={},
                pnu="test-pnu",
                candidate_finalization_evidence=evidence,
                expected_finalization_identity={
                    **self._expected_identity(),
                    "final_geometry_hash": "artifact-final-hash",
                },
            )

    def test_env_relaxed_production_seam_forces_all_publish_authorities_false(self):
        passport = {
            "status": "diagnostic_non_publishable",
            "publishable": False,
            "candidate_finalization_hard_pass": False,
            "stages": [{
                "id": "candidate_finalization_fallback",
                "evidence": {
                    "reason": "candidate_finalization_identity_mismatch:visual_hash"
                },
            }],
        }
        artifact = {"hardGates": {"combinedHardPass": True}}
        downstream_row = {"combined_hard_pass": True}
        final_row = {"combined_hard_pass": True}

        evidence = _synchronize_finalization_publish_authority(
            passport=passport,
            artifact=artifact,
            downstream_row=downstream_row,
            final_row=final_row,
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertEqual(
            evidence["reason"],
            "candidate_finalization_identity_mismatch:visual_hash",
        )
        self.assertFalse(artifact["hardGates"]["combinedHardPass"])
        self.assertFalse(downstream_row["combined_hard_pass"])
        self.assertFalse(final_row["combined_hard_pass"])
        self.assertEqual(
            artifact["hardGates"]["candidateFinalization"],
            downstream_row["candidate_finalization_hard_gate"],
        )
        self.assertEqual(
            final_row["candidate_finalization_hard_gate"],
            evidence,
        )

    def test_strict_valid_production_seam_preserves_true_authorities(self):
        passport = {
            "status": "in_progress",
            "candidate_finalization_hard_pass": True,
        }
        artifact = {"hardGates": {"combinedHardPass": True}}
        downstream_row = {"combined_hard_pass": True}
        final_row = {"combined_hard_pass": True}

        evidence = _synchronize_finalization_publish_authority(
            passport=passport,
            artifact=artifact,
            downstream_row=downstream_row,
            final_row=final_row,
        )

        self.assertTrue(evidence["hard_pass"])
        self.assertTrue(artifact["hardGates"]["combinedHardPass"])
        self.assertTrue(downstream_row["combined_hard_pass"])
        self.assertTrue(final_row["combined_hard_pass"])


class Task5BArchiveCapacityAuthorityTest(SimpleTestCase):
    def _projection(self):
        return {
            "alternative_id": "balanced_yield",
            "target_utilization": 0.80,
            "target_hard_pass": True,
            "selectable_capacity_alternative_id": "balanced_yield",
            "selectable_capacity_target_utilization": 0.80,
            "selectable_capacity_hard_pass": True,
            "feasible_minimum_utilization": 0.70,
        }

    def _contract(self):
        return {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": "floor-contract-hash",
            "hard_pass": True,
        }

    def _passport_capacity(self, measurement):
        return _resolved_capacity_evidence(
            capacity_projection=self._projection(),
            capacity_measurement=measurement,
            shared_floor_contract=self._contract(),
            descriptor={"capacity_target_hard_pass": True},
        )

    def _archive_capacity(self, measurement, contract=None):
        return _archived_capacity_evidence({
            "capacityAlternative": self._projection(),
            "executionPassport": {
                "stages": [{
                    "id": "capacity",
                    "evidence": {
                        "measurement": deepcopy(measurement),
                        "shared_floor_contract": deepcopy(
                            self._contract() if contract is None else contract
                        ),
                    },
                }],
            },
        })

    def test_stale_selectable_true_fails_both_final_capacity_authorities(self):
        measurement = {
            "feasible_capacity_utilization": 0.60,
            "hard_pass": True,
        }

        passport = self._passport_capacity(measurement)
        archive = self._archive_capacity(measurement)

        for evidence in (passport, archive):
            with self.subTest(authority=evidence):
                self.assertFalse(evidence["resolved_capacity_hard_pass"])
                self.assertFalse(evidence["hard_pass"])
                self.assertEqual(
                    evidence["resolved_capacity_failure_reasons"],
                    ["achieved_capacity_below_required_threshold"],
                )
                self.assertEqual(
                    evidence["resolved_capacity_minimum_utilization"],
                    0.70,
                )

    def test_valid_final_measurement_passes_both_capacity_authorities(self):
        measurement = {
            "feasible_capacity_utilization": 0.82,
            "hard_pass": True,
        }

        passport = self._passport_capacity(measurement)
        archive = self._archive_capacity(measurement)

        for evidence in (passport, archive):
            with self.subTest(authority=evidence):
                self.assertTrue(evidence["resolved_capacity_hard_pass"])
                self.assertTrue(evidence["hard_pass"])
                self.assertEqual(evidence["resolved_capacity_failure_reasons"], [])
                self.assertEqual(
                    evidence["resolved_capacity_target_utilization"],
                    0.80,
                )
                self.assertEqual(evidence["achieved_capacity_utilization"], 0.82)

    def test_shared_floor_contract_failure_agrees_between_passport_and_archive(self):
        measurement = {
            "feasible_capacity_utilization": 0.82,
            "hard_pass": True,
        }
        cases = (
            ({}, "shared_floor_contract_missing_or_invalid"),
            ({**self._contract(), "hard_pass": False}, "shared_floor_contract_failed"),
        )
        for contract, reason in cases:
            with self.subTest(contract=contract):
                passport = _resolved_capacity_evidence(
                    capacity_projection=self._projection(),
                    capacity_measurement=measurement,
                    shared_floor_contract=contract,
                    descriptor={"capacity_target_hard_pass": True},
                )
                archive = self._archive_capacity(measurement, contract)
                for evidence in (passport, archive):
                    self.assertFalse(evidence["hard_pass"])
                    self.assertFalse(evidence["shared_floor_contract_hard_pass"])
                    self.assertIn(
                        reason,
                        evidence["shared_floor_contract_failure_reasons"],
                    )

    def test_materialize_archive_production_persists_shared_floor_failure(self):
        measurement = {
            "feasible_capacity_utilization": 0.82,
            "hard_pass": True,
        }
        artifact = {
            "capacityAlternative": self._projection(),
            "executionPassport": {
                "stages": [{
                    "id": "capacity",
                    "evidence": {
                        "measurement": measurement,
                        "shared_floor_contract": {},
                    },
                }],
            },
            "hardGates": {},
        }
        compilation = SimpleNamespace(program=SimpleNamespace(metadata={}))
        with TemporaryDirectory() as temporary:
            sidecar = Path(temporary) / "passport.json"

            def write_passport(_compilation, _preview, **kwargs):
                sidecar.write_text(
                    json.dumps({
                        "capacity": kwargs["downstream_evidence"]["capacity"]
                    }),
                    encoding="utf-8",
                )
                return sidecar

            with (
                patch(
                    "design.maas.geometry_language.executed_archive.archived_compilation",
                    return_value=(compilation, artifact, {}, Path(temporary) / "archive.json"),
                ),
                patch(
                    "design.maas.geometry_language.executed_archive.materialize_executed_mass_preview",
                    return_value=Path(temporary) / "preview.png",
                ),
                patch(
                    "design.maas.geometry_language.executed_archive.executed_mass_manifest",
                    return_value={"pnu": "test-pnu"},
                ),
                patch(
                    "design.maas.geometry_language.executed_archive.write_mass_execution_passport",
                    side_effect=write_passport,
                ),
                patch(
                    "design.maas.geometry_language.executed_archive._retrieved_reference_records",
                    return_value=[],
                ),
                patch(
                    "design.maas.geometry_language.executed_archive._reference_corpus_summary",
                    return_value={},
                ),
                patch(
                    "design.maas.geometry_language.executed_archive._manifest_row",
                    return_value={},
                ),
            ):
                passport = materialize_executed_mass_passport(1, "test-run")

        self.assertFalse(passport["capacity"]["hard_pass"])
        self.assertIn(
            "shared_floor_contract_missing_or_invalid",
            passport["capacity"]["shared_floor_contract_failure_reasons"],
        )
