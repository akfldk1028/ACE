from __future__ import annotations

import json
import unittest


def block(payload: dict) -> str:
    return "ARCH_REVIEW_STATE\n```json\n" + json.dumps(payload) + "\n```"


def valid_payload(**overrides: object) -> dict:
    payload: dict[str, object] = {
        "checked_domains": ["geometry", "law", "parking", "program"],
        "blocking_issue_codes": [],
        "missing_evidence_codes": [],
        "evidence_ids": [
            "evidence:geometry_agent",
            "evidence:law_graph_agent",
            "evidence:parking_agent",
            "evidence:program_agent",
            "evidence:review_agent",
        ],
        "recommended_decision": "STOP_ACCEPT",
        "confidence": 0.9,
    }
    payload.update(overrides)
    return payload


class ReviewStateParserTests(unittest.TestCase):
    def test_valid_fenced_json_is_complete(self) -> None:
        try:
            from iclr2027.review_state import parse_review_state
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"review state parser is missing: {exc}")

        result = parse_review_state("검토 완료\n" + block(valid_payload()))

        self.assertTrue(result.complete)
        self.assertEqual(result.state.recommended_decision, "STOP_ACCEPT")
        self.assertEqual(result.error_codes, ())

    def test_multiple_blocks_return_last_valid_block(self) -> None:
        from iclr2027.review_state import parse_review_state

        first = block(
            valid_payload(
                recommended_decision="CONTINUE",
                missing_evidence_codes=["parking.required_evidence_missing"],
                confidence=0.4,
            )
        )
        second = block(
            valid_payload(
                recommended_decision="STOP_REJECT",
                blocking_issue_codes=["parking.supply_shortage"],
                confidence=0.8,
            )
        )
        malformed = "ARCH_REVIEW_STATE\n```json\n{bad json}\n```"

        result = parse_review_state("\n".join((first, second, malformed)))

        self.assertTrue(result.complete)
        self.assertEqual(result.state.recommended_decision, "STOP_REJECT")
        self.assertEqual(result.block_count, 3)

    def test_malformed_out_of_range_duplicate_and_handoff_fail_closed(self) -> None:
        from iclr2027.review_state import parse_review_state

        samples = (
            "ARCH_REVIEW_STATE\n```json\n{bad json}\n```",
            block(valid_payload(confidence=1.2)),
            block(valid_payload(blocking_issue_codes=["x", "x"])),
            "I hand this to the structural reviewer.",
        )
        for sample in samples:
            with self.subTest(sample=sample[:30]):
                result = parse_review_state(sample)
                self.assertFalse(result.complete)
                self.assertEqual(result.state.recommended_decision, "CONTINUE")
                self.assertEqual(result.state.confidence, 0.0)
                self.assertTrue(result.error_codes)

    def test_unknown_evidence_is_retained_for_precision_but_cannot_stop(self) -> None:
        from iclr2027.review_state import parse_review_state

        result = parse_review_state(
            block(valid_payload(evidence_ids=["evidence:invented_agent"]))
        )

        self.assertFalse(result.complete)
        self.assertEqual(result.state.recommended_decision, "CONTINUE")
        self.assertEqual(result.state.evidence_ids, ("evidence:invented_agent",))
        self.assertIn("unknown_evidence_id", result.error_codes)

    def test_evidence_identifier_cannot_be_used_as_a_missing_issue_code(self) -> None:
        from iclr2027.review_state import parse_review_state

        result = parse_review_state(
            block(
                valid_payload(
                    missing_evidence_codes=["evidence:parking_agent"],
                    recommended_decision="CONTINUE",
                )
            )
        )

        self.assertFalse(result.complete)
        self.assertIn("invalid_state", result.error_codes)

    def test_portfolio_attempt_evidence_is_a_known_typed_record(self) -> None:
        from iclr2027.review_state import parse_review_state

        result = parse_review_state(
            block(
                valid_payload(
                    checked_domains=["program"],
                    blocking_issue_codes=["selection.no_admitted_candidate"],
                    evidence_ids=["evidence:portfolio_attempt"],
                    recommended_decision="STOP_REJECT",
                )
            )
        )

        self.assertTrue(result.complete)
        self.assertEqual(result.error_codes, ())
        self.assertEqual(result.state.evidence_ids, ("evidence:portfolio_attempt",))

    def test_packet_local_evidence_ids_reject_a_cross_case_known_id(self) -> None:
        from iclr2027.review_state import parse_review_state

        result = parse_review_state(
            block(valid_payload(evidence_ids=["evidence:portfolio_attempt"])),
            known_evidence_ids={"evidence:site_agent"},
        )

        self.assertFalse(result.complete)
        self.assertIn("unknown_evidence_id", result.error_codes)

    def test_fake_gold_field_invalidates_the_block(self) -> None:
        from iclr2027.review_state import parse_review_state

        payload = valid_payload(expected_decision="STOP_ACCEPT")
        result = parse_review_state(block(payload))

        self.assertFalse(result.complete)
        self.assertEqual(result.state.recommended_decision, "CONTINUE")
        self.assertIn("unexpected_field", result.error_codes)

    def test_unlabeled_exact_json_with_terminate_remains_fail_closed(self) -> None:
        from iclr2027.review_state import parse_review_state

        model_output = "```json\n" + json.dumps(valid_payload()) + "\n```\nTERMINATE"
        result = parse_review_state(model_output)

        self.assertFalse(result.complete)
        self.assertEqual(result.state.recommended_decision, "CONTINUE")
        self.assertEqual(result.error_codes, ("missing_state_block",))

    def test_self_tagged_leading_json_is_complete_without_external_marker(self) -> None:
        from iclr2027.review_state import parse_review_state

        payload = {"state_schema": "ARCH_REVIEW_STATE", **valid_payload()}
        model_output = "```json\n" + json.dumps(payload) + "\n```"
        result = parse_review_state(model_output)

        self.assertTrue(result.complete)
        self.assertEqual(result.state.recommended_decision, "STOP_ACCEPT")
        self.assertEqual(result.error_codes, ())

    def test_self_tagged_json_is_rejected_after_leading_prose(self) -> None:
        from iclr2027.review_state import parse_review_state

        payload = {"state_schema": "ARCH_REVIEW_STATE", **valid_payload()}
        model_output = "analysis first\n```json\n" + json.dumps(payload) + "\n```"
        result = parse_review_state(model_output)

        self.assertFalse(result.complete)
        self.assertEqual(result.error_codes, ("missing_state_block",))

    def test_decision_and_issue_lists_must_be_semantically_consistent(self) -> None:
        from iclr2027.review_state import parse_review_state

        inconsistent = (
            valid_payload(
                recommended_decision="STOP_ACCEPT",
                missing_evidence_codes=["parking.required_evidence_missing"],
            ),
            valid_payload(
                recommended_decision="STOP_ACCEPT",
                blocking_issue_codes=["parking.supply_shortage"],
            ),
            valid_payload(
                recommended_decision="STOP_REJECT",
                blocking_issue_codes=[],
            ),
            valid_payload(
                recommended_decision="CONTINUE",
                missing_evidence_codes=[],
            ),
            valid_payload(
                recommended_decision="CONTINUE",
                blocking_issue_codes=["parking.supply_shortage"],
                missing_evidence_codes=["parking.required_evidence_missing"],
            ),
        )
        for payload in inconsistent:
            with self.subTest(decision=payload["recommended_decision"]):
                result = parse_review_state(block(payload))
                self.assertFalse(result.complete)
                self.assertEqual(result.state.recommended_decision, "CONTINUE")
                self.assertIn("invalid_state", result.error_codes)


if __name__ == "__main__":
    unittest.main()
