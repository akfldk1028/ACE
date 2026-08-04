from __future__ import annotations

import inspect
import os
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import portfolio_benchmark
from design.maas.book_language import portfolio_replenishment
from design.maas.book_language.run_budget import progressive_mass_run_budget


class DynamicReplenishmentBudgetTests(SimpleTestCase):
    def test_replenishment_author_limit_scales_with_target_under_safety_cap(self):
        self.assertEqual(
            progressive_mass_run_budget(5).replenishment_author_request_limit,
            5,
        )
        self.assertEqual(
            progressive_mass_run_budget(20).replenishment_author_request_limit,
            8,
        )

    def test_live_cycle_cap_defaults_to_run_budget_and_env_only_lowers_it(self):
        parameters = inspect.signature(
            portfolio_replenishment.replenishment_cycle_budget_for_run
        ).parameters
        self.assertIn("run_budget_limit", parameters)

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MAAS_BOOK_REPLENISHMENT_CYCLES", None)
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(
                    live_vlm=True,
                    run_budget_limit=5,
                ),
                5,
            )
        with patch.dict(
            os.environ,
            {"MAAS_BOOK_REPLENISHMENT_CYCLES": "2"},
            clear=False,
        ):
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(
                    live_vlm=True,
                    run_budget_limit=5,
                ),
                2,
            )
        with patch.dict(
            os.environ,
            {"MAAS_BOOK_REPLENISHMENT_CYCLES": "7"},
            clear=False,
        ):
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(
                    live_vlm=True,
                    run_budget_limit=5,
                ),
                5,
            )

    def test_replenishment_uses_one_deterministic_author_request_per_cycle(self):
        parameters = inspect.signature(
            portfolio_benchmark._deficit_directed_replenishment_inputs
        ).parameters
        self.assertIn("cycle_index", parameters)

        requests = [
            {"source_seed": "seed-a"},
            {"source_seed": "seed-b"},
            {"source_seed": "seed-c"},
        ]
        selected_seeds = []
        for cycle_index in range(1, 5):
            result = portfolio_benchmark._deficit_directed_replenishment_inputs(
                requests,
                legal_fit_repair_feedback=[],
                capacity_authoring_deficits=[],
                family_supply_deficits={},
                progressive_target=5,
                cycle_index=cycle_index,
                exact_compile_remaining=17,
            )
            self.assertEqual(len(result["synthesis_requests"]), 1)
            selected_seeds.append(
                result["synthesis_requests"][0]["source_seed"]
            )

        self.assertEqual(
            selected_seeds,
            ["seed-a", "seed-b", "seed-c", "seed-a"],
        )

    def test_cycle_preflight_rechecks_target_exact_author_and_runtime(self):
        preflight = getattr(
            portfolio_benchmark,
            "_replenishment_cycle_preflight_stop_reason",
            None,
        )
        self.assertIsNotNone(preflight)

        common = {
            "selected_count": 1,
            "selected_scope_count": 1,
            "target_count": 5,
            "required_scope_count": 5,
        }
        self.assertEqual(
            preflight(
                **common,
                exact_compile_remaining=0,
                author_replenishment_remaining=3,
                runtime_reserve_available=True,
            ),
            "cumulative_exact_compile_budget_exhausted",
        )
        self.assertEqual(
            preflight(
                **common,
                exact_compile_remaining=17,
                author_replenishment_remaining=0,
                runtime_reserve_available=True,
            ),
            "replenishment_author_quota_exhausted",
        )
        self.assertEqual(
            preflight(
                **common,
                exact_compile_remaining=17,
                author_replenishment_remaining=3,
                runtime_reserve_available=False,
            ),
            "runtime_reserve_exhausted",
        )
        self.assertEqual(
            preflight(
                selected_count=5,
                selected_scope_count=5,
                target_count=5,
                required_scope_count=5,
                exact_compile_remaining=0,
                author_replenishment_remaining=0,
                runtime_reserve_available=False,
            ),
            "target_and_scope_coverage_reached",
        )
        self.assertEqual(
            preflight(
                **common,
                exact_compile_remaining=17,
                author_replenishment_remaining=3,
                runtime_reserve_available=True,
            ),
            "",
        )

    def test_target_completion_precedes_author_budget_failure(self):
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=5,
                selected_scope_count=5,
                target_count=5,
                required_scope_count=5,
                cycles_run=1,
                cycle_budget=5,
                author_budget_failure={
                    "code": "request_quota_exhausted",
                    "quota": "author_replenishment",
                    "author_stage": "replenishment",
                },
            ),
            "target_and_scope_coverage_reached",
        )
