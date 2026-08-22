from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"


class ChallengedCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        cls.packet, cls.native_gold = packet_from_arr_artifacts(
            FIXTURE,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="dev-417-neighborhood-native",
        )

    def test_native_packet_passes_independent_validators(self) -> None:
        try:
            from iclr2027.validators import validate_evidence_packet
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"validator module is missing: {exc}")

        result = validate_evidence_packet(self.packet)

        self.assertEqual(result.blocking_issue_codes, ())
        self.assertEqual(result.expected_decision, "STOP_ACCEPT")

    def test_each_fault_mutates_evidence_and_derives_typed_rejection(self) -> None:
        try:
            from iclr2027.faults import FAULT_REGISTRY
            from iclr2027.validators import gold_from_validation, validate_evidence_packet
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"fault or validator module is missing: {exc}")

        expected = {
            "identity_hash": "identity.hash_mismatch",
            "law_projection": "law.projection_failed",
            "parking_shortage": "parking.supply_shortage",
            "program_capacity": "program.capacity_failed",
            "geometry_compile": "geometry.compilation_failed",
        }
        for family, issue_code in expected.items():
            with self.subTest(family=family):
                challenged = FAULT_REGISTRY[family](self.packet)
                result = validate_evidence_packet(challenged)
                gold = gold_from_validation(challenged, mutation_family=family)

                self.assertEqual(result.blocking_issue_codes, (issue_code,))
                self.assertEqual(result.missing_evidence_codes, ())
                self.assertEqual(result.expected_decision, "STOP_REJECT")
                self.assertEqual(gold.expected_decision, "STOP_REJECT")
                self.assertIn(issue_code, gold.blocking_issue_codes)
                self.assertEqual(gold.mutation_family, family)
                self.assertNotIn("mutation_family", challenged.to_dict())
                self.assertNotIn(family, str(challenged.to_dict()))

    def test_missing_evidence_faults_derive_only_typed_continue_labels(self) -> None:
        from iclr2027.faults import FAULT_REGISTRY
        from iclr2027.validators import gold_from_validation, validate_evidence_packet

        expected = {
            "law_evidence_missing": (
                "evidence:law_graph_agent",
                "law.required_evidence_missing",
            ),
            "parking_evidence_missing": (
                "evidence:parking_agent",
                "parking.required_evidence_missing",
            ),
        }
        observed_missing_codes: set[str] = set()
        for family, (omitted_id, missing_code) in expected.items():
            with self.subTest(family=family):
                challenged = FAULT_REGISTRY[family](self.packet)
                result = validate_evidence_packet(challenged)
                gold = gold_from_validation(challenged, mutation_family=family)

                evidence_ids = {
                    str(item["evidence_id"]) for item in challenged.evidence
                }
                self.assertNotIn(omitted_id, evidence_ids)
                self.assertEqual(result.blocking_issue_codes, ())
                self.assertEqual(result.missing_evidence_codes, (missing_code,))
                self.assertEqual(result.expected_decision, "CONTINUE")
                self.assertEqual(gold.expected_decision, "CONTINUE")
                self.assertEqual(gold.missing_evidence_codes, (missing_code,))
                observed_missing_codes.update(result.missing_evidence_codes)

        self.assertEqual(
            observed_missing_codes,
            {
                "law.required_evidence_missing",
                "parking.required_evidence_missing",
            },
        )

    def test_present_failed_law_or_parking_evidence_remains_reject(self) -> None:
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        expected = {
            "evidence:law_graph_agent": "law.projection_failed",
            "evidence:parking_agent": "parking.supply_shortage",
        }
        for evidence_id, issue_code in expected.items():
            with self.subTest(evidence_id=evidence_id):
                payload = self.packet.to_dict()
                record = next(
                    item
                    for item in payload["evidence"]
                    if item["evidence_id"] == evidence_id
                )
                if evidence_id == "evidence:law_graph_agent":
                    record["evidence"]["legal_projection"][
                        "volume_retention"
                    ] = "malformed"
                else:
                    record["evidence"]["required_spaces"] = "malformed"
                malformed = ArchitectureEvidencePacket.from_dict(payload)

                result = validate_evidence_packet(malformed)
                self.assertEqual(result.expected_decision, "STOP_REJECT")
                self.assertIn(issue_code, result.blocking_issue_codes)
                self.assertEqual(result.missing_evidence_codes, ())

    def test_missing_domain_does_not_relax_other_identity_checks(self) -> None:
        from iclr2027.faults import FAULT_REGISTRY
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        cases = (
            (
                "law_evidence_missing",
                "evidence:site_agent",
                "geometry_hash",
                "law.required_evidence_missing",
            ),
            (
                "parking_evidence_missing",
                "evidence:law_graph_agent",
                "geometry_hash",
                "parking.required_evidence_missing",
            ),
        )
        for family, evidence_id, identity_field, missing_code in cases:
            with self.subTest(family=family):
                payload = FAULT_REGISTRY[family](self.packet).to_dict()
                record = next(
                    item
                    for item in payload["evidence"]
                    if item["evidence_id"] == evidence_id
                )
                container = (
                    record["evidence"]
                    if evidence_id == "evidence:site_agent"
                    else record["identity"]
                )
                container[identity_field] = "0" * 64
                tampered = ArchitectureEvidencePacket.from_dict(payload)

                result = validate_evidence_packet(tampered)
                self.assertEqual(result.expected_decision, "STOP_REJECT")
                self.assertEqual(
                    result.blocking_issue_codes,
                    ("identity.hash_mismatch",),
                )
                self.assertEqual(result.missing_evidence_codes, (missing_code,))

    def test_balanced_assignment_is_stable_and_covers_all_faults(self) -> None:
        try:
            from iclr2027.faults import FAULT_REGISTRY, assign_fault_families
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"fault module is missing: {exc}")

        case_ids = [f"dev-case-{index}" for index in range(12)]
        first = assign_fault_families(case_ids)
        second = assign_fault_families(list(reversed(case_ids)))

        self.assertEqual(first, second)
        self.assertEqual(set(first.values()), set(FAULT_REGISTRY))
        counts = [list(first.values()).count(family) for family in FAULT_REGISTRY]
        self.assertLessEqual(max(counts) - min(counts), 1)

    def test_seven_case_census_assigns_each_preregistered_family_once(self) -> None:
        from iclr2027.faults import (
            CHALLENGE_FAMILY_CENSUS,
            assign_fault_families,
        )

        case_ids = [f"dev-case-{index}" for index in range(7)]
        expected = {
            "dev-case-1": "identity_hash",
            "dev-case-2": "law_projection",
            "dev-case-3": "parking_shortage",
            "dev-case-5": "program_capacity",
            "dev-case-0": "geometry_compile",
            "dev-case-4": "law_evidence_missing",
            "dev-case-6": "parking_evidence_missing",
        }

        self.assertEqual(
            CHALLENGE_FAMILY_CENSUS,
            (
                "identity_hash",
                "law_projection",
                "parking_shortage",
                "program_capacity",
                "geometry_compile",
                "law_evidence_missing",
                "parking_evidence_missing",
            ),
        )
        self.assertEqual(assign_fault_families(case_ids), expected)
        self.assertEqual(
            assign_fault_families(list(reversed(case_ids))),
            expected,
        )
        self.assertEqual(set(expected.values()), set(CHALLENGE_FAMILY_CENSUS))

    def test_pilot_gate_still_requires_each_hard_family(self) -> None:
        from iclr2027.faults import (
            CHALLENGE_FAMILY_CENSUS,
            HARD_FAULT_FAMILIES,
        )
        from iclr2027.pilot_gate import PilotSummary, evaluate_pilot

        manifest = {
            "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
            "split": "dev",
            "patterns": ["rr3", "sel3", "swm3", "refl3", "debate3"],
            "repeats": 3,
            "expected_case_count": 30,
            "case_count": 30,
            "planned_run_count": 450,
            "stage_case_counts": {"execution": 30},
            "decision_case_counts": {
                "STOP_ACCEPT": 7,
                "STOP_REJECT": 21,
                "CONTINUE": 2,
            },
            "executed": True,
        }

        def summary(families: tuple[str, ...]) -> PilotSummary:
            return PilotSummary(
                planned_runs=450,
                completed_runs=450,
                parsed_states=900,
                successful_parses=900,
                final_runs=450,
                successful_final_parses=450,
                correct_final_decisions=450,
                correct_final_verdicts=450,
                correct_final_blocking=450,
                correct_final_missing_evidence=450,
                protocol_valid_runs=450,
                run_errors=0,
                safe_cases=7,
                unsafe_cases=21,
                continue_cases=2,
                fault_families=families,
                estimated_completion_date=date(2026, 9, 1),
                estimated_total_cost_usd=1.0,
                stage_case_counts={"execution": 30},
            )

        all_families = tuple(CHALLENGE_FAMILY_CENSUS)
        self.assertTrue(
            evaluate_pilot(
                summary(all_families),
                run_manifest=manifest,
            ).checks["all_fault_families"]
        )
        for hard_family in HARD_FAULT_FAMILIES:
            with self.subTest(hard_family=hard_family):
                without_hard = tuple(
                    family for family in all_families if family != hard_family
                )
                self.assertFalse(
                    evaluate_pilot(
                        summary(without_hard),
                        run_manifest=manifest,
                    ).checks["all_fault_families"]
                )

    def test_stop_accept_requires_all_packet_evidence_and_domains(self) -> None:
        from iclr2027.schema import ArchitectureReviewState
        from iclr2027.validators import validate_terminal_admissibility

        empty_claim = ArchitectureReviewState(
            checked_domains=(),
            blocking_issue_codes=(),
            missing_evidence_codes=(),
            evidence_ids=(),
            recommended_decision="STOP_ACCEPT",
            confidence=0.9,
        )
        rejected = validate_terminal_admissibility(self.packet, empty_claim)

        self.assertFalse(rejected.admissible)
        self.assertIn("required_evidence_not_cited", rejected.reasons)
        self.assertIn("required_domain_not_checked", rejected.reasons)

        complete_claim = ArchitectureReviewState(
            checked_domains=("site", "geometry", "law", "parking", "program"),
            blocking_issue_codes=(),
            missing_evidence_codes=(),
            evidence_ids=tuple(
                str(item["evidence_id"]) for item in self.packet.evidence
            ),
            recommended_decision="STOP_ACCEPT",
            confidence=0.9,
        )
        accepted = validate_terminal_admissibility(self.packet, complete_claim)

        self.assertTrue(accepted.admissible)

    def test_terminal_claim_rejects_invented_blocking_issue(self) -> None:
        from iclr2027.schema import ArchitectureReviewState
        from iclr2027.validators import validate_terminal_admissibility

        claim = ArchitectureReviewState(
            checked_domains=("site", "geometry", "law", "parking", "program"),
            blocking_issue_codes=("law.invented_failure",),
            missing_evidence_codes=(),
            evidence_ids=tuple(
                str(item["evidence_id"]) for item in self.packet.evidence
            ),
            recommended_decision="STOP_ACCEPT",
            confidence=0.9,
        )

        result = validate_terminal_admissibility(self.packet, claim)

        self.assertFalse(result.admissible)
        self.assertIn("blocking_issue_mismatch", result.reasons)


if __name__ == "__main__":
    unittest.main()
