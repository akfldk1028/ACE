from __future__ import annotations

import inspect
import os
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import portfolio_benchmark
from design.maas.book_language import portfolio_replenishment
from design.maas.book_language.run_budget import progressive_mass_run_budget


class DynamicReplenishmentBudgetTests(SimpleTestCase):
    def test_compile_authority_preserves_fair_cycle_limit_below_global_remaining(self):
        observed_limits = []

        def run_cycle(*, cycle_index, exact_compile_limit, **_kwargs):
            observed_limits.append((cycle_index, exact_compile_limit))
            return exact_compile_limit

        fair_limit = portfolio_benchmark._run_replenishment_cycle_with_compile_authority(
            run_cycle,
            exact_compile_remaining=18,
            compile_stop_sink={},
            cycle_index=2,
            exact_compile_limit=4,
        )
        globally_capped_limit = (
            portfolio_benchmark._run_replenishment_cycle_with_compile_authority(
                run_cycle,
                exact_compile_remaining=18,
                compile_stop_sink={},
                cycle_index=3,
                exact_compile_limit=24,
            )
        )

        self.assertEqual(fair_limit, 4)
        self.assertEqual(globally_capped_limit, 18)
        self.assertEqual(observed_limits, [(2, 4), (3, 18)])

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
                cycle_budget=5,
                exact_compile_remaining=17,
                author_replenishment_remaining=5,
                selected_count=1,
                selected_scope_count=1,
                target_count=5,
                required_scope_count=5,
            )
            self.assertEqual(len(result["synthesis_requests"]), 1)
            selected_seeds.append(
                result["synthesis_requests"][0]["source_seed"]
            )

        self.assertEqual(
            selected_seeds,
            ["seed-a", "seed-b", "seed-c", "seed-a"],
        )

    def test_cycle_batch_is_bounded_by_target_deficit_and_fair_exact_share(self):
        book_graph_context = {
            "schema_version": "arr.maas.book_graph_supply.v1",
            "hard_gate_effect": "none_diagnostic_only",
            "principle_id_counts": {"base-01": 1},
        }
        family_feedback = {"missing_chassis": ["split_wing"]}
        result = portfolio_benchmark._deficit_directed_replenishment_inputs(
            [{
                "source_seed": "seed-b",
                "candidate_count": 24,
                "llm_author_count": 24,
                "llm_author_batch_index": 1,
                "llm_author_batch_count": 3,
                "llm_author_variation_offset": 24,
                "book_graph_supply": book_graph_context,
                "book_graph_vocabulary": {"principles": ["base-01", "comb-01"]},
                "instruction": "retain canonical program authority",
            }],
            legal_fit_repair_feedback=[{"failure": "legal"}],
            capacity_authoring_deficits=[{"gfa_deficit_m2": 12.0}],
            family_supply_deficits=family_feedback,
            progressive_target=5,
            selected_count=1,
            selected_scope_count=1,
            target_count=5,
            required_scope_count=5,
            cycle_index=2,
            cycle_budget=5,
            exact_compile_remaining=17,
            author_replenishment_remaining=4,
        )

        self.assertEqual(result["exact_compile_limit"], 5)
        self.assertEqual(len(result["synthesis_requests"]), 1)
        request = result["synthesis_requests"][0]
        self.assertEqual(request["candidate_count"], 4)
        self.assertEqual(request["llm_author_count"], 4)
        self.assertEqual(request["llm_author_batch_index"], 1)
        self.assertEqual(request["llm_author_batch_count"], 3)
        self.assertEqual(request["llm_author_variation_offset"], 24)
        self.assertEqual(request["book_graph_supply"], book_graph_context)
        self.assertEqual(
            request["book_graph_vocabulary"],
            {"principles": ["base-01", "comb-01"]},
        )
        self.assertEqual(request["family_supply_deficits"], family_feedback)
        self.assertIn("retain canonical program authority", request["instruction"])
        self.assertEqual(request["legal_fit_repair_feedback"], [{"failure": "legal"}])

    def test_scope_deficit_drives_batch_when_count_target_is_met(self):
        result = portfolio_benchmark._deficit_directed_replenishment_inputs(
            [{"candidate_count": 24, "llm_author_count": 24}],
            legal_fit_repair_feedback=[],
            capacity_authoring_deficits=[],
            family_supply_deficits={},
            progressive_target=5,
            selected_count=5,
            selected_scope_count=2,
            target_count=5,
            required_scope_count=5,
            cycle_index=1,
            cycle_budget=3,
            exact_compile_remaining=9,
            author_replenishment_remaining=3,
        )

        self.assertEqual(result["exact_compile_limit"], 3)
        self.assertEqual(result["synthesis_requests"][0]["candidate_count"], 3)
        self.assertEqual(result["synthesis_requests"][0]["llm_author_count"], 3)

    def test_last_viable_cycle_may_use_exact_remainder_but_batch_stays_demand_bounded(self):
        result = portfolio_benchmark._deficit_directed_replenishment_inputs(
            [{"candidate_count": 24, "llm_author_count": 24}],
            legal_fit_repair_feedback=[],
            capacity_authoring_deficits=[],
            family_supply_deficits={},
            progressive_target=5,
            selected_count=1,
            selected_scope_count=1,
            target_count=5,
            required_scope_count=5,
            cycle_index=5,
            cycle_budget=5,
            exact_compile_remaining=17,
            author_replenishment_remaining=1,
        )

        self.assertEqual(result["exact_compile_limit"], 17)
        self.assertEqual(result["synthesis_requests"][0]["candidate_count"], 4)
        self.assertEqual(result["synthesis_requests"][0]["llm_author_count"], 4)

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

    def test_authoritative_author_remainder_overrides_historical_failure(self):
        historical_failure = {
            "code": "request_quota_exhausted",
            "quota": "author_replenishment",
            "author_stage": "replenishment",
        }
        common = {
            "selected_count": 1,
            "selected_scope_count": 1,
            "target_count": 5,
            "required_scope_count": 5,
            "cycles_run": 1,
            "cycle_budget": 5,
            "exact_compile_remaining": 17,
            "author_budget_failure": historical_failure,
        }

        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                **common,
                author_replenishment_remaining=5,
            ),
            "",
        )
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                **common,
                author_replenishment_remaining=0,
            ),
            "replenishment_author_quota_exhausted",
        )
