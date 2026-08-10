"""Regression contract for bounded MASS diagnostic progress reporting."""

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_benchmark import (
    apply_diagnostic_summary_policy,
)


class MaasDiagnosticProgressTests(SimpleTestCase):
    def test_progress_is_separate_from_canonical_completion(self):
        summary = {
            "programs": [{
                "selected_count": 3,
                "counts": {
                    "evaluated": 5,
                    "compiled": 4,
                    "final_hard_pass_selection_pool_count": 4,
                    "selection_trace": {
                        "portfolio_contract_solver_count": 3,
                        "portfolio_contract_solver_target_reached": True,
                    },
                },
            }],
        }

        apply_diagnostic_summary_policy(summary, target=3)

        self.assertEqual(
            summary["programs"][0]["mass_progress"],
            {
                "schema_version": "arr.maas.mass_progress.v1",
                "evaluated_count": 5,
                "compiled_count": 4,
                "individual_hard_pass_count": 4,
                "compatible_selected_count": 3,
                "diagnostic_target_count": 3,
                "diagnostic_target_reached": True,
                "canonical_target_count": 20,
                "canonical_complete": False,
            },
        )
