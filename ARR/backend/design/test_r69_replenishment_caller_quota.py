from django.test import SimpleTestCase

from design.maas.book_language import portfolio_benchmark
from design.maas.book_language.portfolio_replenishment import (
    replenishment_stop_reason,
)


class R69ReplenishmentCallerQuotaTests(SimpleTestCase):
    def test_author_budget_state_keeps_success_and_attempt_budgets_distinct(self):
        budget_state = getattr(
            portfolio_benchmark,
            "_replenishment_author_budget_state",
            None,
        )
        self.assertIsNotNone(budget_state)

        state = budget_state(
            {
                "remaining_count": 20,
                "quota_limits": {"author_replenishment": 5},
                "quota_remaining_counts": {"author_replenishment": 0},
            },
            successful_author_count=2,
        )

        self.assertEqual(state, {
            "author_replenishment_remaining": 0,
            "successful_author_count": 2,
            "successful_author_limit": 5,
            "provider_attempts_remaining": 20,
        })

    def test_only_materialized_authored_supply_consumes_success_quota(self):
        success_increment = getattr(
            portfolio_benchmark,
            "_materialized_authored_supply_success",
            None,
        )
        self.assertIsNotNone(success_increment)

        cycle_evidence = (
            {
                "llm_author_request_executed": False,
                "geometry_program_llm_author_stage_counts": {},
            },
            {
                "llm_author_request_executed": True,
                "geometry_program_llm_author_stage_counts": {
                    "directed_geometry_materialized": 1,
                },
            },
            {
                "llm_author_request_executed": True,
                "geometry_program_llm_author_stage_counts": {
                    "directed_geometry_materialized": 1,
                },
            },
            {
                "llm_author_request_executed": False,
                "geometry_program_llm_author_stage_counts": {},
            },
            {
                "llm_author_request_executed": True,
                "geometry_program_llm_author_stage_counts": {
                    "directed_geometry_materialized": 0,
                },
            },
        )

        successful_author_count = 0
        cumulative_counts = []
        for evidence in cycle_evidence:
            successful_author_count += success_increment(evidence)
            cumulative_counts.append(successful_author_count)

        self.assertEqual(cumulative_counts, [0, 1, 2, 2, 2])

    def test_empty_results_bypass_legacy_success_quota_until_provider_budget_ends(self):
        common = {
            "selected_count": 1,
            "selected_scope_count": 1,
            "target_count": 5,
            "required_scope_count": 5,
            "exact_compile_remaining": 8,
            "author_replenishment_remaining": 0,
            "successful_author_count": 2,
            "successful_author_limit": 5,
            "runtime_reserve_available": True,
        }

        self.assertEqual(
            portfolio_benchmark._replenishment_cycle_preflight_stop_reason(
                **common,
                provider_attempts_remaining=1,
            ),
            "",
        )
        self.assertEqual(
            portfolio_benchmark._replenishment_cycle_preflight_stop_reason(
                **common,
                provider_attempts_remaining=0,
            ),
            "replenishment_provider_attempt_budget_exhausted",
        )
        self.assertEqual(
            replenishment_stop_reason(
                selected_count=1,
                selected_scope_count=1,
                target_count=5,
                required_scope_count=5,
                cycles_run=4,
                cycle_budget=8,
                exact_compile_remaining=8,
                author_replenishment_remaining=0,
                successful_author_count=2,
                successful_author_limit=5,
                provider_attempts_remaining=1,
            ),
            "",
        )
        self.assertEqual(
            replenishment_stop_reason(
                selected_count=1,
                selected_scope_count=1,
                target_count=5,
                required_scope_count=5,
                cycles_run=5,
                cycle_budget=8,
                exact_compile_remaining=8,
                author_replenishment_remaining=0,
                successful_author_count=2,
                successful_author_limit=5,
                provider_attempts_remaining=0,
            ),
            "replenishment_provider_attempt_budget_exhausted",
        )
