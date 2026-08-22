from __future__ import annotations

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_evaluation_contract import (
    StageDecision,
)
from design.maas.book_language.portfolio_evaluation_ledger import (
    PortfolioEvaluationLedger,
)


class PortfolioEvaluationLedgerTests(SimpleTestCase):
    def test_twenty_candidates_survive_with_stable_identity_and_no_truncation(self):
        ledger = PortfolioEvaluationLedger(
            run_id="legal-run-20",
            pnu="1168011800104170004",
            target_count=20,
        )
        for index in range(20):
            candidate_id = f"maas_{index + 1:02d}"
            ledger.begin_candidate(
                candidate_id=candidate_id,
                program_hash=f"program-{index}",
                geometry_hash=f"geometry-{index}",
                preview_path=f"renders/{candidate_id}.png",
                lineage={"book_principle_id": f"book:{index}"},
            )
            ledger.record_stage(
                candidate_id,
                StageDecision("geometry", "pass"),
            )
            ledger.finalize_candidate(candidate_id)

        evidence = ledger.evidence()

        self.assertEqual(evidence["record_count"], 20)
        self.assertFalse(evidence["records_truncated"])
        self.assertEqual(evidence["records"][0]["candidate_id"], "maas_01")
        self.assertEqual(
            evidence["records"][-1]["geometry_hash"],
            "geometry-19",
        )

    def test_failed_candidate_retains_ordered_reasons_and_missing_preview(self):
        ledger = PortfolioEvaluationLedger(
            run_id="failed-run",
            pnu="1168011800104170004",
            target_count=1,
        )
        ledger.begin_candidate(
            candidate_id="maas_fail",
            program_hash="program-fail",
            geometry_hash="geometry-fail",
        )
        ledger.record_stage(
            "maas_fail",
            StageDecision(
                "law",
                "fail",
                reasons=("height_limit", "setback_intrusion"),
                evidence={"height_m": 52.0, "limit_m": 50.0},
            ),
        )
        ledger.finalize_candidate("maas_fail")

        record = ledger.evidence()["records"][0]

        self.assertEqual(record["overall_status"], "failed")
        self.assertEqual(
            record["terminal_reasons"],
            ["height_limit", "setback_intrusion"],
        )
        self.assertEqual(record["preview_path"], "")

    def test_stage_update_replaces_only_that_candidate_stage(self):
        ledger = PortfolioEvaluationLedger("retry-run", "pnu", 1)
        ledger.begin_candidate(
            candidate_id="maas_retry",
            program_hash="program-retry",
            geometry_hash="geometry-retry",
        )
        ledger.record_stage(
            "maas_retry",
            StageDecision("parking", "fail", reasons=("shortfall",)),
        )
        ledger.record_stage(
            "maas_retry",
            StageDecision("parking", "pass", evidence={"spaces": 3}),
        )
        ledger.finalize_candidate("maas_retry")

        record = ledger.evidence()["records"][0]

        self.assertEqual(record["stages"]["parking"]["status"], "pass")
        self.assertEqual(record["stages"]["parking"]["evidence"], {"spaces": 3})

    def test_candidate_identity_cannot_be_rebound(self):
        ledger = PortfolioEvaluationLedger("identity-run", "pnu", 1)
        ledger.begin_candidate(
            candidate_id="maas_01",
            program_hash="program-a",
            geometry_hash="geometry-a",
        )

        with self.assertRaisesRegex(ValueError, "candidate identity rebinding"):
            ledger.begin_candidate(
                candidate_id="maas_01",
                program_hash="program-b",
                geometry_hash="geometry-a",
            )

    def test_explicit_record_limit_reports_truncation(self):
        ledger = PortfolioEvaluationLedger(
            "bounded-run",
            "pnu",
            target_count=3,
            record_limit=2,
        )
        for index in range(3):
            candidate_id = f"maas_{index}"
            ledger.begin_candidate(
                candidate_id=candidate_id,
                program_hash=f"program-{index}",
                geometry_hash=f"geometry-{index}",
            )
            ledger.finalize_candidate(candidate_id)

        evidence = ledger.evidence()

        self.assertEqual(evidence["record_count"], 3)
        self.assertEqual(len(evidence["records"]), 2)
        self.assertTrue(evidence["records_truncated"])
