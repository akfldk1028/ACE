from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date

from iclr2027.pilot_gate import PilotSummary, evaluate_pilot


class PilotDecisionCensusTests(unittest.TestCase):
    def _summary(self) -> PilotSummary:
        return PilotSummary(
            planned_runs=450,
            completed_runs=450,
            parsed_states=450,
            successful_parses=450,
            final_runs=450,
            successful_final_parses=450,
            correct_final_decisions=450,
            correct_final_verdicts=450,
            correct_final_blocking=450,
            correct_final_missing_evidence=450,
            protocol_valid_runs=450,
            run_errors=0,
            retried_runs=0,
            safe_cases=7,
            unsafe_cases=21,
            continue_cases=2,
            fault_families=(
                "identity_hash",
                "law_projection",
                "parking_shortage",
                "program_capacity",
                "geometry_compile",
            ),
            estimated_completion_date=date(2026, 8, 30),
            estimated_total_cost_usd=1.0,
            transaction_set_sha256="d" * 64,
            stage_case_counts={"execution": 30},
        )

    def _manifest(self) -> dict[str, object]:
        return {
            "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
            "input_mode": "frozen_private_binding",
            "split": "dev",
            "patterns": ["rr3", "sel3", "swm3", "refl3", "debate3"],
            "repeats": 3,
            "model": "fixture-model",
            "code_commit": "fixture-commit",
            "case_count": 30,
            "expected_case_count": 30,
            "planned_run_count": 450,
            "stage_case_counts": {"execution": 30},
            "decision_case_counts": {
                "STOP_ACCEPT": 7,
                "STOP_REJECT": 21,
                "CONTINUE": 2,
            },
            "input_hashes": {
                f"input:{index:064x}": f"{index:064x}"
                for index in range(1, 7)
            },
            "identity_commitment": "a" * 64,
            "registry_core_sha256": "b" * 64,
            "split_manifest_sha256": "c" * 64,
            "plan_sha256": "d" * 64,
            "executed": True,
            "execution": {
                "completed_runs": 450,
                "skipped_runs": 0,
                "error_runs": 0,
                "parsed_states": 450,
                "successful_parses": 450,
            },
            "estimated_cost_per_run_usd": 1.0 / 450,
            "estimated_total_cost_usd": 1.0,
            "estimated_completion_date": "2026-08-30",
        }

    def test_full_pilot_requires_exact_three_way_decision_census(self) -> None:
        result = evaluate_pilot(
            self._summary(),
            run_manifest=self._manifest(),
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=450,
        )

        self.assertTrue(result.checks["all_cases_labeled"])
        self.assertTrue(result.checks["all_decision_classes_present"])
        self.assertTrue(result.checks["decision_census_consistent"])
        self.assertTrue(result.passed)

    def test_missing_continue_or_manifest_mismatch_fails_closed(self) -> None:
        no_continue = replace(
            self._summary(),
            unsafe_cases=23,
            continue_cases=0,
        )
        no_continue_result = evaluate_pilot(
            no_continue,
            run_manifest={
                **self._manifest(),
                "decision_case_counts": {
                    "STOP_ACCEPT": 7,
                    "STOP_REJECT": 23,
                    "CONTINUE": 0,
                },
            },
        )
        mismatch = evaluate_pilot(
            self._summary(),
            run_manifest={
                **self._manifest(),
                "decision_case_counts": {
                    "STOP_ACCEPT": 8,
                    "STOP_REJECT": 20,
                    "CONTINUE": 2,
                },
            },
        )

        self.assertFalse(no_continue_result.checks["all_decision_classes_present"])
        self.assertFalse(mismatch.checks["decision_census_consistent"])


if __name__ == "__main__":
    unittest.main()
