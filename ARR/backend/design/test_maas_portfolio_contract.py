from django.test import SimpleTestCase

from design.maas.book_language.portfolio_contract import (
    MINIMUM_PORTFOLIO_ALTERNATIVES,
    evaluate_portfolio_completion,
    resolve_portfolio_requirement,
)
from design.maas.book_language.authorship_policy import (
    bounded_live_llm_synthesis_requests,
)


class MaasPortfolioContractTests(SimpleTestCase):
    def test_live_llm_authorship_is_one_bounded_typed_ast_request(self):
        requests = bounded_live_llm_synthesis_requests(
            "neighborhood living",
            source_seed_names=("seed_a", "seed_b"),
            target_count=10,
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["source_seed"], "seed_a")
        self.assertTrue(requests[0]["live_llm_author"])
        self.assertTrue(requests[0]["llm_author_only"])
        self.assertFalse(requests[0]["live_vlm_revision"])
        self.assertEqual(requests[0]["llm_author_count"], 10)

    def test_smoke_reduces_cost_not_alternative_design_minimum(self):
        requirement = resolve_portfolio_requirement(
            smoke_mode=True,
            base_volume_scope_count=6,
        )

        self.assertEqual(MINIMUM_PORTFOLIO_ALTERNATIVES, 10)
        self.assertEqual(requirement.minimum_count, 10)
        self.assertEqual(requirement.selection_target, 10)
        self.assertEqual(requirement.required_scope_count, 6)

        evidence = evaluate_portfolio_completion(
            requirement,
            selected_count=1,
            selected_scope_count=1,
            runtime_live_vlm=False,
            exact_vlm_hard_pass_count=0,
            require_llm_authored_ast=False,
            llm_authored_selected_count=0,
            portfolio_vlm_audit={"status": "not_requested", "hard_pass": False},
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn("selected_count_below_minimum_10", evidence["failures"])
        self.assertIn("base_volume_scope_count_below_6", evidence["failures"])

    def test_live_completion_requires_exact_vlm_for_every_published_mass(self):
        requirement = resolve_portfolio_requirement(
            smoke_mode=True,
            base_volume_scope_count=6,
        )

        evidence = evaluate_portfolio_completion(
            requirement,
            selected_count=10,
            selected_scope_count=6,
            runtime_live_vlm=True,
            exact_vlm_hard_pass_count=9,
            require_llm_authored_ast=True,
            llm_authored_selected_count=1,
            portfolio_vlm_audit={"status": "pass", "hard_pass": True},
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "exact_post_book_vlm_hard_pass_count_below_selected_count",
            evidence["failures"],
        )

    def test_skipped_portfolio_vlm_is_never_visual_approval(self):
        requirement = resolve_portfolio_requirement(
            smoke_mode=True,
            base_volume_scope_count=6,
        )

        evidence = evaluate_portfolio_completion(
            requirement,
            selected_count=10,
            selected_scope_count=6,
            runtime_live_vlm=True,
            exact_vlm_hard_pass_count=10,
            require_llm_authored_ast=True,
            llm_authored_selected_count=1,
            portfolio_vlm_audit={
                "status": "skipped_cost_bounded_smoke",
                "evaluated": False,
                "hard_pass": True,
            },
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn("portfolio_vlm_audit_not_evaluated", evidence["failures"])

    def test_full_flow_requires_a_selected_llm_authored_ast(self):
        requirement = resolve_portfolio_requirement(
            smoke_mode=False,
            base_volume_scope_count=6,
        )

        self.assertEqual(requirement.selection_target, 20)
        evidence = evaluate_portfolio_completion(
            requirement,
            selected_count=20,
            selected_scope_count=6,
            runtime_live_vlm=True,
            exact_vlm_hard_pass_count=20,
            require_llm_authored_ast=True,
            llm_authored_selected_count=0,
            portfolio_vlm_audit={"status": "pass", "evaluated": True, "hard_pass": True},
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn("selected_llm_authored_ast_missing", evidence["failures"])
