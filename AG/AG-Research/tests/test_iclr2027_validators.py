from __future__ import annotations

import unittest
import json
from pathlib import Path


ARR_ROOT = Path(__file__).parents[1] / "data" / "iclr2027" / "arr"
CANDIDATE_FLOOR = ARR_ROOT / "test-03" / "maas-book-programs-summary.json"
ICLR_ROOT = Path(__file__).parents[1] / "data" / "iclr2027"


class StageAwareValidatorTests(unittest.TestCase):
    def _candidate_floor_packet(self):
        from iclr2027.arr_adapter import packet_from_arr_artifacts

        return packet_from_arr_artifacts(
            CANDIDATE_FLOOR,
            pnu="1165011100200390001",
            program="gymnasium",
            case_id="test-03-gymnasium-native",
        )[0]

    def test_candidate_floor_context_is_continue_with_typed_missing_evidence(self) -> None:
        from iclr2027.validators import gold_from_validation, validate_evidence_packet

        packet = self._candidate_floor_packet()
        result = validate_evidence_packet(packet)
        gold = gold_from_validation(packet, mutation_family="")

        self.assertEqual(result.expected_decision, "CONTINUE")
        self.assertEqual(result.blocking_issue_codes, ())
        self.assertEqual(
            result.missing_evidence_codes,
            ("candidate_floor_context.typed_ledger_missing",),
        )
        self.assertEqual(gold.expected_decision, "CONTINUE")
        self.assertEqual(gold.blocking_issue_codes, ())
        self.assertEqual(gold.missing_evidence_codes, result.missing_evidence_codes)

    def test_candidate_floor_continue_is_terminally_admissible_only_with_exact_missing_code(self) -> None:
        from iclr2027.schema import ArchitectureReviewState
        from iclr2027.validators import validate_terminal_admissibility

        packet = self._candidate_floor_packet()
        state = ArchitectureReviewState(
            checked_domains=("program",),
            blocking_issue_codes=(),
            missing_evidence_codes=(
                "candidate_floor_context.typed_ledger_missing",
            ),
            evidence_ids=("evidence:portfolio_attempt",),
            recommended_decision="CONTINUE",
            confidence=0.8,
        )
        self.assertTrue(validate_terminal_admissibility(packet, state).admissible)

        with self.assertRaisesRegex(ValueError, "unknown missing_evidence_codes"):
            ArchitectureReviewState(
                checked_domains=("program",),
                blocking_issue_codes=(),
                missing_evidence_codes=("candidate_floor_context.wrong",),
                evidence_ids=("evidence:portfolio_attempt",),
                recommended_decision="CONTINUE",
                confidence=0.8,
            )

    def test_attempt_hash_challenge_is_stage_aware_identity_reject(self) -> None:
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        packet = self._candidate_floor_packet()
        payload = packet.to_dict()
        payload["attempt_hash"] = "0" * 64
        challenged = ArchitectureEvidencePacket.from_dict(payload)

        result = validate_evidence_packet(challenged)
        self.assertEqual(result.expected_decision, "STOP_REJECT")
        self.assertEqual(
            result.blocking_issue_codes,
            ("identity.attempt_hash_mismatch",),
        )
        self.assertEqual(
            result.missing_evidence_codes,
            ("candidate_floor_context.typed_ledger_missing",),
        )

    def test_rehashed_stage_manifest_cannot_fabricate_route_or_preflight_evidence(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.io import sha256_json
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        cases = (
            (
                "test-03",
                "1165011100200390001",
                "neighborhood",
                lambda stage: stage.update(terminal_failure_count=35),
            ),
            (
                "dev-467-law-restored",
                "1168011800104670003",
                "neighborhood",
                lambda stage: stage.update(excluded_count=0),
            ),
            (
                "test-04",
                "1162010300201040003",
                "neighborhood",
                lambda stage: stage.update(routing_input_count=0),
            ),
            (
                "dev-467-law-restored",
                "1168011800104670003",
                "gymnasium",
                lambda stage: stage.update(dimensional_context_status="adapted"),
            ),
            (
                "test-03",
                "1165011100200390001",
                "gymnasium",
                lambda stage: stage.update(program_routing_input_count=1),
            ),
        )
        for directory, pnu, program, mutate in cases:
            with self.subTest(directory=directory, program=program):
                packet, _ = packet_from_arr_artifacts(
                    ARR_ROOT / directory / "maas-book-programs-summary.json",
                    pnu=pnu,
                    program=program,
                    case_id=f"{directory}-{program}-native",
                )
                payload = packet.to_dict()
                manifest = payload["evidence"][0]["evidence"]
                mutate(manifest["stage_evidence"])
                payload["attempt_hash"] = sha256_json(manifest)
                tampered = ArchitectureEvidencePacket.from_dict(payload)

                self.assertIn(
                    "evidence.portfolio_attempt_incomplete",
                    validate_evidence_packet(tampered).blocking_issue_codes,
                )

    def test_rehashed_attempt_manifests_reject_unknown_claim_fields(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.io import sha256_json
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        cases = (
            (
                "dev-417-law-restored",
                "1168011800104170004",
                "gymnasium",
                lambda manifest: manifest["candidates"][0].update(
                    fabricated_claim=True
                ),
            ),
            (
                "test-03",
                "1165011100200390001",
                "neighborhood",
                lambda manifest: manifest["mass_progress"].update(
                    fabricated_claim=True
                ),
            ),
            (
                "dev-467-law-restored",
                "1168011800104670003",
                "gymnasium",
                lambda manifest: manifest["downstream_hard_gate"].update(
                    fabricated_claim=True
                ),
            ),
            (
                "test-03",
                "1165011100200390001",
                "gymnasium",
                lambda manifest: manifest["stage_evidence"].update(
                    fabricated_claim=True
                ),
            ),
        )
        for directory, pnu, program, mutate in cases:
            with self.subTest(directory=directory, program=program):
                packet, _ = packet_from_arr_artifacts(
                    ARR_ROOT / directory / "maas-book-programs-summary.json",
                    pnu=pnu,
                    program=program,
                    case_id=f"{directory}-{program}-native",
                )
                payload = packet.to_dict()
                manifest = payload["evidence"][0]["evidence"]
                mutate(manifest)
                payload["attempt_hash"] = sha256_json(manifest)
                tampered = ArchitectureEvidencePacket.from_dict(payload)

                self.assertIn(
                    "evidence.portfolio_attempt_incomplete",
                    validate_evidence_packet(tampered).blocking_issue_codes,
                )

    def test_rehashed_attempt_manifests_reject_bool_and_float_counts(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.io import sha256_json
        from iclr2027.schema import ArchitectureEvidencePacket
        from iclr2027.validators import validate_evidence_packet

        cases = (
            (
                "dev-417-law-restored",
                "1168011800104170004",
                "gymnasium",
                lambda manifest: manifest["portfolio_completion"].update(
                    selected_count=False
                ),
            ),
            (
                "test-03",
                "1165011100200390001",
                "neighborhood",
                lambda manifest: manifest["stage_evidence"].update(
                    terminal_failure_count=36.0
                ),
            ),
            (
                "dev-467-law-restored",
                "1168011800104670003",
                "neighborhood",
                lambda manifest: manifest["stage_evidence"].update(
                    retained_count=False
                ),
            ),
            (
                "test-04",
                "1162010300201040003",
                "neighborhood",
                lambda manifest: manifest["stage_evidence"].update(
                    canonical_hard_pass_count=False
                ),
            ),
            (
                "dev-467-law-restored",
                "1168011800104670003",
                "gymnasium",
                lambda manifest: manifest["stage_evidence"].update(
                    effective_floor_count=False
                ),
            ),
            (
                "test-03",
                "1165011100200390001",
                "gymnasium",
                lambda manifest: manifest["stage_evidence"].update(
                    program_routing_input_count=False
                ),
            ),
        )
        for directory, pnu, program, mutate in cases:
            with self.subTest(directory=directory, program=program):
                packet, _ = packet_from_arr_artifacts(
                    ARR_ROOT / directory / "maas-book-programs-summary.json",
                    pnu=pnu,
                    program=program,
                    case_id=f"{directory}-{program}-native",
                )
                payload = packet.to_dict()
                manifest = payload["evidence"][0]["evidence"]
                mutate(manifest)
                payload["attempt_hash"] = sha256_json(manifest)
                tampered = ArchitectureEvidencePacket.from_dict(payload)
                self.assertIn(
                    "evidence.portfolio_attempt_incomplete",
                    validate_evidence_packet(tampered).blocking_issue_codes,
                )

    def test_public_and_private_terminal_validation_match_for_all_development_cases(
        self,
    ) -> None:
        from iclr2027.schema import (
            ArchitectureGoldRecord,
            ArchitecturePublicCase,
            ArchitectureReviewState,
            PrivateCaseBinding,
        )
        from iclr2027.validators import (
            validate_evidence_packet,
            validate_terminal_admissibility,
        )

        split_manifest = json.loads(
            (ICLR_ROOT / "split_manifest.json").read_text(encoding="utf-8")
        )
        seen = 0
        for condition in ("native", "challenged"):
            key = f"dev.{condition}"
            entry = split_manifest["bundles"][key]
            manifest_path = ICLR_ROOT / entry["manifest_path"]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            rows = {}
            for side in ("public", "internal", "gold"):
                path = manifest_path.parent / manifest["files"][side]["path"]
                rows[side] = [
                    json.loads(line)
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            for public_row, internal_row, gold_row in zip(
                rows["public"], rows["internal"], rows["gold"], strict=True
            ):
                public_case = ArchitecturePublicCase.from_dict(public_row)
                packet = PrivateCaseBinding.from_dict(internal_row).packet
                gold = ArchitectureGoldRecord.from_dict(gold_row)
                required_domains = tuple(
                    sorted(
                        {
                            str(item.get("domain"))
                            for item in public_case.evidence
                            if item.get("domain")
                            in {"site", "law", "parking", "program", "geometry"}
                        }
                    )
                )
                state = ArchitectureReviewState(
                    checked_domains=required_domains,
                    blocking_issue_codes=gold.blocking_issue_codes,
                    missing_evidence_codes=gold.missing_evidence_codes,
                    evidence_ids=gold.required_evidence_ids,
                    recommended_decision=gold.expected_decision,
                    confidence=1.0,
                )

                private_validation = validate_evidence_packet(packet)
                public_validation = validate_evidence_packet(public_case)
                self.assertEqual(
                    public_validation.expected_decision,
                    private_validation.expected_decision,
                )
                self.assertEqual(
                    public_validation.blocking_issue_codes,
                    private_validation.blocking_issue_codes,
                )
                self.assertEqual(
                    public_validation.missing_evidence_codes,
                    private_validation.missing_evidence_codes,
                )
                self.assertEqual(
                    validate_terminal_admissibility(public_case, state),
                    validate_terminal_admissibility(packet, state),
                )
                seen += 1
        self.assertEqual(seen, 30)


if __name__ == "__main__":
    unittest.main()
