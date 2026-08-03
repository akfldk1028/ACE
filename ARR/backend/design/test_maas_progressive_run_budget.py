from django.test import SimpleTestCase

from design.maas.book_language.run_budget import (
    MassRunBudget,
    progressive_mass_run_budget,
    replenishment_allowed_by_deadline,
)
from design.maas.book_language.authorship_policy import (
    bounded_live_llm_synthesis_requests,
    bounded_llm_author_batch_count,
    live_llm_authored_program_target,
)
from design.maas.book_language.candidate_generation import (
    _principles_for_seed,
)
from design.maas.book_language.portfolio_contract import (
    evaluate_portfolio_completion,
    resolve_progressive_portfolio_requirement,
)
from design.maas.book_language.portfolio_benchmark import (
    _allow_incomplete_preview_finalization,
    _allow_partial_portfolio_preview,
    _portfolio_count_requirements,
)
from design.management.commands.benchmark_maas_book_program_portfolios import (
    Command as BenchmarkCommand,
)


class ProgressiveMassRunBudgetTests(SimpleTestCase):
    def test_progressive_run_renders_partial_hard_pass_portfolio(self):
        self.assertTrue(_allow_partial_portfolio_preview(
            diagnostic_target=None,
            progressive_target=3,
        ))
        self.assertFalse(_allow_partial_portfolio_preview(
            diagnostic_target=None,
            progressive_target=None,
        ))

    def test_target_three_count_requirements_are_reachable(self):
        self.assertEqual(
            _portfolio_count_requirements(
                selection_target=3,
                required_scope_target=3,
                available_principle_kind_count=4,
            ),
            {
                "book_operation_count": 3,
                "visual_language_count": 3,
                "base_volume_scope_count": 3,
                "principle_kind_count": 3,
            },
        )

    def test_llm_authored_ast_is_not_replayed_for_every_outer_book_principle(self):
        principles = tuple(
            (index, {"principle_id": f"book:{index}"})
            for index in range(6)
        )

        self.assertEqual(
            _principles_for_seed(
                principles,
                seed_index=2,
                llm_authored_seed=True,
            ),
            (principles[2],),
        )
        self.assertEqual(
            _principles_for_seed(
                principles,
                seed_index=2,
                llm_authored_seed=False,
            ),
            principles,
        )

    def test_incomplete_progressive_candidate_renders_but_complete_gate_stays_strict(self):
        self.assertTrue(_allow_incomplete_preview_finalization(
            diagnostic_target=None,
            smoke_mode=False,
            progressive_target=3,
            selected_count=1,
            selection_target=3,
            explicitly_relaxed=False,
        ))
        self.assertFalse(_allow_incomplete_preview_finalization(
            diagnostic_target=None,
            smoke_mode=False,
            progressive_target=3,
            selected_count=3,
            selection_target=3,
            explicitly_relaxed=False,
        ))

    def test_exact_progressive_budgets(self):
        target_three = progressive_mass_run_budget(3)

        self.assertEqual(target_three.author_batch_count, 2)
        self.assertEqual(target_three.base_parent_review_budget, 3)
        self.assertEqual(target_three.exact_acceptance_opportunities, 9)
        self.assertEqual(target_three.portfolio_board_reserve, 1)
        self.assertEqual(target_three.total_provider_request_limit, 16)

    def test_target_five_budget_is_bounded_and_partitioned(self):
        target_three = progressive_mass_run_budget(3)
        target_five = progressive_mass_run_budget(5)
        target_ten = progressive_mass_run_budget(10)

        self.assertEqual(
            (target_five.raw_target, target_five.compile_limit,
             target_five.timeout_seconds),
            (52, 60, 60 * 60),
        )
        self.assertEqual(target_five.initial_compile_limit, 48)
        self.assertEqual(target_five.replenishment_compile_reserve, 12)
        self.assertEqual(
            target_five.provider_request_quotas,
            {
                "author_initial": 3,
                "author_replenishment": 1,
                "base_candidate": 7,
                "exact_candidate": 15,
                "portfolio_board": 1,
                "reference_audit": 0,
                "retry": 0,
            },
        )
        self.assertEqual(target_five.total_provider_request_limit, 27)
        self.assertEqual(target_five.live_vlm_request_limit, 23)
        self.assertLess(
            target_three.total_provider_request_limit,
            target_five.total_provider_request_limit,
        )
        self.assertLessEqual(
            target_five.total_provider_request_limit,
            target_ten.total_provider_request_limit,
        )

    def test_non_progressive_target_is_rejected(self):
        with self.assertRaisesMessage(
            ValueError,
            "progressive MASS target must be one of 3, 5, 10, or 20",
        ):
            progressive_mass_run_budget(4)

    def test_cluster_limit_is_uniform_not_a_named_form_quota(self):
        self.assertEqual(progressive_mass_run_budget(3).cluster_maximum, 1)
        self.assertEqual(progressive_mass_run_budget(10).cluster_maximum, 3)
        self.assertEqual(progressive_mass_run_budget(20).cluster_maximum, 5)

    def test_live_llm_supply_uses_progressive_raw_budget(self):
        self.assertEqual(live_llm_authored_program_target(3), 36)
        self.assertEqual(live_llm_authored_program_target(5), 52)
        self.assertEqual(live_llm_authored_program_target(10), 90)
        self.assertEqual(live_llm_authored_program_target(20), 160)

    def test_legacy_diagnostic_target_keeps_bounded_behavior(self):
        self.assertEqual(live_llm_authored_program_target(4), 4)
        self.assertEqual(live_llm_authored_program_target(30), 12)

    def test_progressive_supply_is_split_into_bounded_author_batches(self):
        target_three = bounded_live_llm_synthesis_requests(
            "neighborhood_living",
            source_seed_names=("seed-a",),
            target_count=3,
        )
        target_twenty = bounded_live_llm_synthesis_requests(
            "neighborhood_living",
            source_seed_names=("seed-a",),
            target_count=20,
        )

        self.assertEqual(
            [request["llm_author_count"] for request in target_three],
            [24, 12],
        )
        self.assertEqual(len(target_twenty), 7)
        self.assertEqual(
            sum(request["llm_author_count"] for request in target_twenty),
            160,
        )

    def test_provider_author_batch_cannot_reintroduce_the_twelve_cap(self):
        self.assertEqual(bounded_llm_author_batch_count(36), 24)
        self.assertEqual(bounded_llm_author_batch_count(12), 12)

    def test_progressive_requirement_is_a_complete_reduced_portfolio(self):
        requirement = resolve_progressive_portfolio_requirement(
            target_count=3,
            base_volume_scope_count=6,
        )

        self.assertEqual(requirement.minimum_count, 3)
        self.assertEqual(requirement.selection_target, 3)
        self.assertEqual(requirement.required_scope_count, 3)
        self.assertFalse(requirement.smoke_mode)

    def test_target_five_requirement_is_complete(self):
        requirement = resolve_progressive_portfolio_requirement(
            target_count=5,
            base_volume_scope_count=8,
        )

        self.assertEqual(requirement.minimum_count, 5)
        self.assertEqual(requirement.selection_target, 5)
        self.assertEqual(requirement.required_scope_count, 5)
        self.assertFalse(requirement.smoke_mode)

    def test_progressive_cli_accepts_all_first_class_targets(self):
        parser = BenchmarkCommand().create_parser("manage.py", "benchmark")
        action = next(
            item
            for item in parser._actions
            if item.dest == "progressive_target"
        )

        self.assertEqual(tuple(action.choices), (3, 5, 10, 20))
        self.assertIn("3, 5, 10, or 20", action.help)

    def test_every_progressive_selection_must_be_llm_authored(self):
        requirement = resolve_progressive_portfolio_requirement(
            target_count=3,
            base_volume_scope_count=3,
        )
        completion = evaluate_portfolio_completion(
            requirement,
            selected_count=3,
            selected_scope_count=3,
            runtime_live_vlm=True,
            exact_vlm_hard_pass_count=3,
            require_llm_authored_ast=True,
            llm_authored_selected_count=2,
            portfolio_vlm_audit={"evaluated": True, "hard_pass": True},
        )

        self.assertIn(
            "selected_llm_authored_ast_count_below_selected_count",
            completion["failures"],
        )

    def test_target_three_total_provider_limit_includes_author_batches(self):
        budget = progressive_mass_run_budget(3)

        self.assertEqual(budget.author_batch_count, 2)
        self.assertEqual(budget.portfolio_board_reserve, 1)
        self.assertEqual(
            budget.provider_request_quotas,
            {
                "author_initial": 2,
                "author_replenishment": 1,
                "base_candidate": 3,
                "exact_candidate": 9,
                "portfolio_board": 1,
                "reference_audit": 0,
                "retry": 0,
            },
        )
        self.assertEqual(budget.total_provider_request_limit, 16)

    def test_base_parent_budget_is_bounded_by_configured_top_k(self):
        budget = MassRunBudget(
            target_count=3,
            raw_target=36,
            compile_limit=24,
            timeout_seconds=45 * 60,
            configured_base_top_k=2,
        )

        self.assertEqual(budget.base_parent_review_budget, 2)

    def test_target_ten_and_twenty_provider_contracts(self):
        target_ten = progressive_mass_run_budget(10)
        target_twenty = progressive_mass_run_budget(20)

        self.assertEqual(
            (
                target_ten.author_batch_count,
                target_ten.base_parent_review_budget,
                target_ten.exact_acceptance_opportunities,
                target_ten.portfolio_board_reserve,
                target_ten.total_provider_request_limit,
            ),
            (4, 8, 30, 1, 44),
        )
        self.assertEqual(
            (
                target_twenty.author_batch_count,
                target_twenty.base_parent_review_budget,
                target_twenty.exact_acceptance_opportunities,
                target_twenty.portfolio_board_reserve,
                target_twenty.total_provider_request_limit,
            ),
            (7, 8, 60, 1, 77),
        )

    def test_replenishment_needs_sixty_percent_runtime_reserve(self):
        self.assertTrue(replenishment_allowed_by_deadline(
            started_at=0.0,
            timeout_seconds=2700,
            now=1000.0,
        ))
        self.assertFalse(replenishment_allowed_by_deadline(
            started_at=0.0,
            timeout_seconds=2700,
            now=1200.0,
        ))
