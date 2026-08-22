from __future__ import annotations

import unittest
import tempfile
from pathlib import Path


class ResearchSchemaTests(unittest.TestCase):
    def _imports(self):
        try:
            from iclr2027.io import canonical_json, sha256_json
            from iclr2027.schema import ArchitectureEvidencePacket, ArchitectureReviewState
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"schema modules are missing: {exc}")
        return canonical_json, sha256_json, ArchitectureEvidencePacket, ArchitectureReviewState

    def _packet_payload(self) -> dict[str, object]:
        return {
            "case_id": "dev-417-neighborhood-native",
            "pnu": "1168011800104170004",
            "program": "neighborhood",
            "condition": "native",
            "execution_id": "single-execution:dev-417",
            "program_hash": "a" * 64,
            "geometry_hash": "b" * 64,
            "evidence": [
                {"evidence_id": "evidence:geometry", "status": "passed"},
                {"evidence_id": "evidence:law", "status": "passed"},
            ],
        }

    def _attempt_payload(self) -> dict[str, object]:
        return {
            "case_id": "dev-417-gymnasium-native",
            "pnu": "1168011800104170004",
            "program": "gymnasium",
            "condition": "native",
            "subject_kind": "portfolio_attempt",
            "execution_id": None,
            "program_hash": None,
            "geometry_hash": None,
            "source_artifact_sha256": "c" * 64,
            "attempt_id": "attempt:" + "e" * 64,
            "attempt_hash": "d" * 64,
            "attempt_stage": "selection",
            "route_kind": None,
            "evidence": [
                {
                    "evidence_id": "evidence:portfolio_attempt",
                    "domain": "program",
                    "status": "failed",
                    "evidence": {"selected_count": 0},
                }
            ],
        }

    def test_canonical_json_is_independent_of_mapping_insertion_order(self) -> None:
        canonical_json, sha256_json, _, _ = self._imports()

        left = {"b": 2, "a": 1}
        right = {"a": 1, "b": 2}

        self.assertEqual(canonical_json(left), '{"a":1,"b":2}')
        self.assertEqual(sha256_json(left), sha256_json(right))

    def test_packet_round_trip_preserves_hash_stable_payload(self) -> None:
        _, sha256_json, ArchitectureEvidencePacket, _ = self._imports()

        packet = ArchitectureEvidencePacket.from_dict(self._packet_payload())
        restored = ArchitectureEvidencePacket.from_dict(packet.to_dict())

        self.assertEqual(restored, packet)
        self.assertEqual(sha256_json(restored), sha256_json(packet))

    def test_portfolio_attempt_round_trip_requires_attempt_identity_and_null_execution_trio(self) -> None:
        _, _, ArchitectureEvidencePacket, _ = self._imports()

        packet = ArchitectureEvidencePacket.from_dict(self._attempt_payload())

        self.assertEqual(packet.subject_kind, "portfolio_attempt")
        self.assertIsNone(packet.execution_id)
        self.assertIsNone(packet.program_hash)
        self.assertIsNone(packet.geometry_hash)
        self.assertEqual(packet.attempt_stage, "selection")
        self.assertIsNone(packet.route_kind)
        self.assertEqual(
            ArchitectureEvidencePacket.from_dict(packet.to_dict()),
            packet,
        )

        mixed = self._attempt_payload()
        mixed["execution_id"] = "fabricated-execution"
        with self.assertRaisesRegex(ValueError, "portfolio_attempt.*execution"):
            ArchitectureEvidencePacket.from_dict(mixed)

        missing_attempt_hash = self._attempt_payload()
        missing_attempt_hash["attempt_hash"] = None
        with self.assertRaisesRegex(ValueError, "attempt_hash"):
            ArchitectureEvidencePacket.from_dict(missing_attempt_hash)

    def test_execution_subject_still_requires_complete_execution_identity(self) -> None:
        _, _, ArchitectureEvidencePacket, _ = self._imports()
        payload = self._packet_payload()
        payload["subject_kind"] = "execution"
        payload["geometry_hash"] = None

        with self.assertRaisesRegex(ValueError, "geometry_hash"):
            ArchitectureEvidencePacket.from_dict(payload)

    def test_subject_kind_discriminates_stage_and_materialization_route(self) -> None:
        _, _, ArchitectureEvidencePacket, _ = self._imports()

        execution = self._packet_payload()
        execution["attempt_stage"] = "selection"
        with self.assertRaisesRegex(ValueError, "execution.*attempt_stage"):
            ArchitectureEvidencePacket.from_dict(execution)

        missing_stage = self._attempt_payload()
        missing_stage.pop("attempt_stage")
        with self.assertRaisesRegex(ValueError, "attempt_stage"):
            ArchitectureEvidencePacket.from_dict(missing_stage)

        materialization = self._attempt_payload()
        materialization["attempt_stage"] = "materialization"
        with self.assertRaisesRegex(ValueError, "route_kind"):
            ArchitectureEvidencePacket.from_dict(materialization)

        selection_with_route = self._attempt_payload()
        selection_with_route["route_kind"] = "capacity_admission_empty"
        with self.assertRaisesRegex(ValueError, "route_kind"):
            ArchitectureEvidencePacket.from_dict(selection_with_route)

        for route_kind in (
            "all_invocations_failed",
            "capacity_admission_empty",
            "program_routing_empty",
        ):
            payload = self._attempt_payload()
            payload["attempt_stage"] = "materialization"
            payload["route_kind"] = route_kind
            self.assertEqual(
                ArchitectureEvidencePacket.from_dict(payload).route_kind,
                route_kind,
            )

    def test_packet_nested_evidence_is_immutable(self) -> None:
        _, sha256_json, ArchitectureEvidencePacket, _ = self._imports()
        payload = self._packet_payload()
        payload["evidence"] = [
            {
                "evidence_id": "evidence:law",
                "status": "passed",
                "details": {"hard_pass": True},
            }
        ]
        packet = ArchitectureEvidencePacket.from_dict(payload)
        before = sha256_json(packet)

        with self.assertRaises(TypeError):
            packet.evidence[0]["status"] = "failed"  # type: ignore[index]
        with self.assertRaises(TypeError):
            packet.evidence[0]["details"]["hard_pass"] = False  # type: ignore[index]

        self.assertEqual(sha256_json(packet), before)

    def test_packet_rejects_non_pnu_identifier(self) -> None:
        _, _, ArchitectureEvidencePacket, _ = self._imports()
        payload = self._packet_payload()
        payload["pnu"] = "not-a-pnu"

        with self.assertRaisesRegex(ValueError, "19 digits"):
            ArchitectureEvidencePacket.from_dict(payload)

    def test_packet_rejects_duplicate_evidence_ids(self) -> None:
        _, _, ArchitectureEvidencePacket, _ = self._imports()
        payload = self._packet_payload()
        payload["evidence"] = [
            {"evidence_id": "evidence:law", "status": "passed"},
            {"evidence_id": "evidence:law", "status": "failed"},
        ]

        with self.assertRaisesRegex(ValueError, "duplicate evidence_id"):
            ArchitectureEvidencePacket.from_dict(payload)

    def test_packet_rejects_nested_gold_or_mutation_fields(self) -> None:
        _, _, ArchitectureEvidencePacket, _ = self._imports()
        payload = self._packet_payload()
        payload["evidence"] = [
            {
                "evidence_id": "evidence:law",
                "status": "failed",
                "details": {"mutation_family": "law_projection"},
            }
        ]

        with self.assertRaisesRegex(ValueError, "forbidden public field"):
            ArchitectureEvidencePacket.from_dict(payload)

    def test_review_state_rejects_unknown_decision(self) -> None:
        _, _, _, ArchitectureReviewState = self._imports()

        with self.assertRaisesRegex(ValueError, "recommended_decision"):
            ArchitectureReviewState.from_dict(
                {
                    "checked_domains": ["law"],
                    "blocking_issue_codes": [],
                    "missing_evidence_codes": [],
                    "evidence_ids": ["evidence:law"],
                    "recommended_decision": "MAYBE",
                    "confidence": 0.5,
                }
            )

    def test_review_state_rejects_confidence_outside_unit_interval(self) -> None:
        _, _, _, ArchitectureReviewState = self._imports()

        with self.assertRaisesRegex(ValueError, "confidence"):
            ArchitectureReviewState.from_dict(
                {
                    "checked_domains": ["law"],
                    "blocking_issue_codes": [],
                    "missing_evidence_codes": [],
                    "evidence_ids": ["evidence:law"],
                    "recommended_decision": "CONTINUE",
                    "confidence": 1.2,
                }
            )

    def test_gold_record_round_trip_is_separate_from_public_packet(self) -> None:
        try:
            from iclr2027.schema import ArchitectureGoldRecord
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"gold schema is missing: {exc}")

        record = ArchitectureGoldRecord.from_dict(
            {
                "case_id": "dev-417-neighborhood-challenged",
                "expected_decision": "STOP_REJECT",
                "blocking_issue_codes": ["parking.supply_shortage"],
                "missing_evidence_codes": [],
                "required_evidence_ids": ["evidence:parking"],
                "mutation_family": "parking_shortage",
            }
        )

        self.assertEqual(
            ArchitectureGoldRecord.from_dict(record.to_dict()),
            record,
        )

    def test_gold_continue_requires_missing_evidence_separate_from_blockers(self) -> None:
        from iclr2027.schema import ArchitectureGoldRecord

        record = ArchitectureGoldRecord.from_dict(
            {
                "case_id": "test-03-gymnasium-native",
                "expected_decision": "CONTINUE",
                "blocking_issue_codes": [],
                "missing_evidence_codes": [
                    "candidate_floor_context.typed_ledger_missing"
                ],
                "required_evidence_ids": ["evidence:portfolio_attempt"],
                "mutation_family": "",
            }
        )
        self.assertEqual(record.expected_decision, "CONTINUE")
        self.assertEqual(
            ArchitectureGoldRecord.from_dict(record.to_dict()),
            record,
        )

        invalid = record.to_dict()
        invalid["blocking_issue_codes"] = ["program.capacity_failed"]
        with self.assertRaisesRegex(ValueError, "CONTINUE"):
            ArchitectureGoldRecord.from_dict(invalid)

    def test_atomic_writers_emit_canonical_json_and_jsonl(self) -> None:
        try:
            from iclr2027.io import write_json_atomic, write_jsonl_atomic
        except ImportError as exc:
            self.fail(f"atomic writers are missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = root / "nested" / "record.json"
            jsonl_path = root / "nested" / "records.jsonl"

            write_json_atomic(json_path, {"b": 2, "a": 1})
            write_jsonl_atomic(jsonl_path, [{"z": 3}, {"a": 1}])

            self.assertEqual(json_path.read_text(encoding="utf-8"), '{"a":1,"b":2}\n')
            self.assertEqual(
                jsonl_path.read_text(encoding="utf-8"),
                '{"z":3}\n{"a":1}\n',
            )

    def test_public_gold_separation_rejects_gold_keys_at_any_depth(self) -> None:
        try:
            from iclr2027.io import assert_public_gold_separation
        except ImportError as exc:
            self.fail(f"public/gold audit is missing: {exc}")

        with self.assertRaisesRegex(ValueError, "forbidden public field"):
            assert_public_gold_separation(
                {"evidence": [{"details": {"gold_issue_codes": ["law.failed"]}}]}
            )


if __name__ == "__main__":
    unittest.main()
