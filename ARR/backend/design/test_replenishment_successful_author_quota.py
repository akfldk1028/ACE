from django.test import SimpleTestCase

from design.maas.book_language.portfolio_replenishment import (
    replenishment_stop_reason,
)


class ReplenishmentSuccessfulAuthorQuotaTests(SimpleTestCase):
    def test_empty_author_results_do_not_exhaust_success_quota_before_valid_result(self):
        materialized_results = (0, 0, 1)
        successful_author_count = 0
        reasons = []

        for cycle_index, materialized_count in enumerate(
            materialized_results,
            start=1,
        ):
            successful_author_count += int(materialized_count > 0)
            reasons.append(replenishment_stop_reason(
                selected_count=1,
                selected_scope_count=1,
                target_count=5,
                required_scope_count=5,
                cycles_run=cycle_index,
                cycle_budget=5,
                exact_compile_remaining=8,
                author_replenishment_remaining=0,
                successful_author_count=successful_author_count,
                successful_author_limit=1,
                provider_attempts_remaining=3 - cycle_index,
            ))

        self.assertEqual(
            reasons,
            ["", "", "replenishment_author_quota_exhausted"],
        )

    def test_empty_results_remain_bounded_by_provider_and_cycle_budgets(self):
        provider_stop = replenishment_stop_reason(
            selected_count=1,
            selected_scope_count=1,
            target_count=5,
            required_scope_count=5,
            cycles_run=2,
            cycle_budget=5,
            exact_compile_remaining=8,
            author_replenishment_remaining=0,
            successful_author_count=0,
            successful_author_limit=1,
            provider_attempts_remaining=0,
        )
        cycle_stop = replenishment_stop_reason(
            selected_count=1,
            selected_scope_count=1,
            target_count=5,
            required_scope_count=5,
            cycles_run=5,
            cycle_budget=5,
            exact_compile_remaining=8,
            author_replenishment_remaining=0,
            successful_author_count=0,
            successful_author_limit=1,
            provider_attempts_remaining=2,
        )

        self.assertEqual(
            provider_stop,
            "replenishment_provider_attempt_budget_exhausted",
        )
        self.assertEqual(cycle_stop, "cycle_budget_exhausted")
