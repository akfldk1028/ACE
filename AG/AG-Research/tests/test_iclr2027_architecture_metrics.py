from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"


def block(payload: dict) -> str:
    return "ARCH_REVIEW_STATE\n```json\n" + json.dumps(payload) + "\n```"


class ArchitectureMetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.faults import mutate_parking_shortage
        from iclr2027.validators import gold_from_validation

        native, _ = packet_from_arr_artifacts(
            FIXTURE,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="dev-417-neighborhood-native",
        )
        cls.packet = mutate_parking_shortage(native)
        cls.gold = gold_from_validation(cls.packet, mutation_family="parking_shortage")

    def test_hand_calculated_components_penalize_unknown_citation_and_incomplete_parse(self) -> None:
        try:
            from iclr2027.architecture_metrics import score_prefix
            from iclr2027.review_state import PrefixReviewState
            from iclr2027.schema import ArchitectureReviewState
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"architecture metric modules are missing: {exc}")

        state = ArchitectureReviewState(
            checked_domains=("law", "parking", "program"),
            blocking_issue_codes=("parking.supply_shortage",),
            missing_evidence_codes=(),
            evidence_ids=(
                "evidence:geometry_agent",
                "evidence:law_graph_agent",
                "evidence:parking_agent",
                "evidence:program_agent",
                "evidence:invented_agent",
            ),
            recommended_decision="STOP_REJECT",
            confidence=0.9,
        )
        prefix = PrefixReviewState(
            turn_index=2,
            state=state,
            parse_complete=False,
            parse_error_codes=("unknown_evidence_id",),
        )

        score = score_prefix(prefix, self.gold, self.packet)

        self.assertAlmostEqual(score.issue_f1, 1.0)
        self.assertAlmostEqual(score.evidence_f1, 8.0 / 11.0)
        self.assertAlmostEqual(score.domain_coverage, 0.6)
        self.assertAlmostEqual(score.verdict_score, 0.0)
        self.assertAlmostEqual(score.quality, 0.30 + 2.0 / 11.0 + 0.12)

    def test_verdict_credit_requires_terminal_admissibility(self) -> None:
        from iclr2027.architecture_metrics import score_prefix
        from iclr2027.review_state import PrefixReviewState
        from iclr2027.schema import ArchitectureReviewState

        state = ArchitectureReviewState(
            checked_domains=(),
            blocking_issue_codes=("parking.supply_shortage",),
            missing_evidence_codes=(),
            evidence_ids=(),
            recommended_decision="STOP_REJECT",
            confidence=0.99,
        )
        prefix = PrefixReviewState(0, state, True, ())

        score = score_prefix(prefix, self.gold, self.packet)

        self.assertEqual(score.verdict_score, 0.0)

    def test_blocking_and_missing_evidence_scores_are_reported_separately(self) -> None:
        from iclr2027.architecture_metrics import score_prefix, score_prefix_breakdown
        from iclr2027.review_state import PrefixReviewState
        from iclr2027.schema import ArchitectureReviewState

        state = ArchitectureReviewState(
            checked_domains=("site", "geometry", "law", "parking", "program"),
            blocking_issue_codes=("parking.supply_shortage",),
            missing_evidence_codes=("law.required_evidence_missing",),
            evidence_ids=tuple(self.gold.required_evidence_ids),
            recommended_decision="STOP_REJECT",
            confidence=0.9,
        )
        prefix = PrefixReviewState(0, state, True, ())

        score = score_prefix(prefix, self.gold, self.packet)
        breakdown = score_prefix_breakdown(prefix, self.gold, self.packet)

        self.assertAlmostEqual(score.issue_f1, 1.0)
        self.assertEqual(score.verdict_score, 0.0)
        self.assertEqual(breakdown["subject_stage"], "execution")
        self.assertEqual(breakdown["decision_score"], 1.0)
        self.assertEqual(breakdown["blocking_issue_f1"], 1.0)
        self.assertEqual(breakdown["missing_evidence_f1"], 0.0)

    def test_continue_gold_scores_missing_evidence_and_stage_independently(self) -> None:
        from iclr2027.architecture_metrics import score_prefix_breakdown
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.review_state import PrefixReviewState
        from iclr2027.schema import ArchitectureReviewState

        packet, gold = packet_from_arr_artifacts(
            Path(__file__).parents[1]
            / "data"
            / "iclr2027"
            / "arr"
            / "test-03"
            / "maas-book-programs-summary.json",
            pnu="1165011100200390001",
            program="gymnasium",
            case_id="test-03-gymnasium-native",
        )
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

        breakdown = score_prefix_breakdown(
            PrefixReviewState(0, state, True, ()), gold, packet
        )

        self.assertEqual(breakdown["subject_stage"], "candidate_floor_context")
        self.assertEqual(breakdown["decision_score"], 1.0)
        self.assertEqual(breakdown["blocking_issue_f1"], 1.0)
        self.assertEqual(breakdown["missing_evidence_f1"], 1.0)

    def test_accumulation_unions_valid_evidence_and_fails_closed_on_bad_turn(self) -> None:
        from iclr2027.review_state import TurnRecord, accumulate_prefix_states

        turn1 = TurnRecord(
            author="law",
            content=block(
                {
                    "checked_domains": ["law"],
                    "blocking_issue_codes": [],
                    "missing_evidence_codes": [],
                    "evidence_ids": ["evidence:law_graph_agent"],
                    "recommended_decision": "CONTINUE",
                    "confidence": 0.5,
                }
            ),
        )
        turn2 = TurnRecord(
            author="parking",
            content=block(
                {
                    "checked_domains": ["parking"],
                    "blocking_issue_codes": ["parking.supply_shortage"],
                    "missing_evidence_codes": [],
                    "evidence_ids": ["evidence:parking_agent"],
                    "recommended_decision": "STOP_REJECT",
                    "confidence": 0.9,
                }
            ),
        )
        turn3 = TurnRecord(author="handoff", content="please continue")

        prefixes = accumulate_prefix_states((turn1, turn2, turn3), self.packet)

        self.assertEqual(len(prefixes), 3)
        self.assertEqual(prefixes[1].state.checked_domains, ("law", "parking"))
        self.assertEqual(
            prefixes[1].state.blocking_issue_codes,
            ("parking.supply_shortage",),
        )
        self.assertEqual(prefixes[1].state.recommended_decision, "STOP_REJECT")
        self.assertTrue(prefixes[1].parse_complete)
        self.assertFalse(prefixes[2].parse_complete)
        self.assertEqual(prefixes[2].state.recommended_decision, "CONTINUE")


if __name__ == "__main__":
    unittest.main()
