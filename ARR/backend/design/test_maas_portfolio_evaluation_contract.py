from __future__ import annotations

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_evaluation_contract import (
    CandidateEvaluation,
    StageDecision,
    classify_candidate_evaluation,
)


DETERMINISTIC_STAGES = (
    "geometry",
    "law",
    "capacity",
    "parking",
    "program",
)


def passing_decisions() -> dict[str, StageDecision]:
    decisions = {
        stage: StageDecision(stage=stage, status="pass")
        for stage in DETERMINISTIC_STAGES
    }
    decisions["vlm"] = StageDecision(
        stage="vlm",
        status="not_evaluated",
    )
    decisions["selection"] = StageDecision(
        stage="selection",
        status="not_evaluated",
    )
    return decisions


class PortfolioEvaluationContractTests(SimpleTestCase):
    def test_deterministic_pass_is_legal_when_vlm_is_not_evaluated(self):
        self.assertEqual(
            classify_candidate_evaluation(
                passing_decisions(),
                selected=False,
                integrity_failures=(),
            ),
            "legal_pass",
        )

    def test_any_deterministic_failure_is_failed_with_ordered_reasons(self):
        decisions = passing_decisions()
        decisions["parking"] = StageDecision(
            stage="parking",
            status="fail",
            reasons=("parking_count_shortfall", "turning_path_unverified"),
        )
        evaluation = CandidateEvaluation(
            candidate_id="maas_02",
            program_hash="program-02",
            geometry_hash="geometry-02",
            stages=decisions,
        )

        evidence = evaluation.evidence()

        self.assertEqual(evidence["overall_status"], "failed")
        self.assertEqual(
            evidence["terminal_reasons"],
            ["parking_count_shortfall", "turning_path_unverified"],
        )

    def test_missing_required_stage_fails_closed_to_not_evaluated(self):
        self.assertEqual(
            classify_candidate_evaluation(
                {"geometry": StageDecision("geometry", "pass")},
                selected=True,
                integrity_failures=(),
            ),
            "not_evaluated",
        )

    def test_integrity_failure_prevents_legal_or_selected_claim(self):
        evaluation = CandidateEvaluation(
            candidate_id="maas_03",
            program_hash="program-03",
            geometry_hash="geometry-03",
            stages=passing_decisions(),
            selected=True,
            integrity_failures=("geometry_hash_mismatch",),
        )

        evidence = evaluation.evidence()

        self.assertEqual(evidence["overall_status"], "failed")
        self.assertEqual(
            evidence["terminal_reasons"],
            ["geometry_hash_mismatch"],
        )

    def test_stage_decision_rejects_unknown_status_and_stage(self):
        with self.assertRaisesRegex(ValueError, "unknown evaluation stage"):
            StageDecision("facade", "pass")
        with self.assertRaisesRegex(ValueError, "unknown evaluation status"):
            StageDecision("law", "maybe")
