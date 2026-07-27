"""Contracts for the architect-supplied BOOK language registry."""

import os
from collections import Counter
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.book_language import audited_book_language_registry, book_base_verbs, build_book_language_registry
from design.maas.book_language import candidate_analysis, portfolio_benchmark, portfolio_feedback
from design.maas.book_language import portfolio_selection, vlm_review
from design.maas.book_language import final_vlm_cycle, portfolio_replenishment
from design.maas.book_language import lineage as book_lineage
from design.maas.book_language.corpus_audit import audit_book_corpus
from design.maas.geometry_language import base_seed_program, compile_geometry_program
from design.maas.grammar.vocab import BOOK_BASE_VERBS, SUPPORTED_VERBS
from design.maas.preference.vlm_scorer import _normalize_vlm_result
from design.maas.preference import vlm_scorer
from design.maas.preference.loop import _vlm_cache_key
from design.maas.program_massing import program_seed_sequences
from design.maas.source_geometry import compile_sequence_to_source_mass


class MaasBookLanguageRegistryTest(SimpleTestCase):
    def test_lineage_gate_keeps_descendant_when_viable_base_was_evicted_by_qd(self):
        def candidate(parent_key: str, stage: str, target_pass: bool):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "book_generation_lineage": {
                    "parent_key": parent_key,
                    "stage": stage,
                },
                "geometry_program": {
                    "metadata": {"family": "agent_notch"},
                },
                "capacity_alternative_projection": {
                    "target_hard_pass": target_pass,
                },
            }))

        retained_descendant = candidate(
            "base-evicted-after-program-pass",
            "combination",
            True,
        )
        rejected_descendant = candidate(
            "base-never-program-valid",
            "combination",
            True,
        )

        retained, evidence = book_lineage.gate_descendants_by_base(
            [retained_descendant, rejected_descendant],
            known_viable_base_keys={"base-evicted-after-program-pass"},
        )

        self.assertEqual(retained, [retained_descendant])
        self.assertEqual(evidence["retained_via_known_base_count"], 1)
        self.assertEqual(evidence["capacity_target_pass_input_count"], 2)
        self.assertEqual(evidence["capacity_target_pass_retained_count"], 1)

    def test_capacity_portfolio_quotas_balance_four_bands_and_absorb_rare_supply(self):
        def candidate(alternative_id: str):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {
                    "alternative_id": alternative_id,
                },
            }))

        balanced_supply = [
            candidate(alternative_id)
            for alternative_id in (
                "spatial_reserve", "balanced_yield", "brief_target", "maximum_feasible",
            )
            for _index in range(20)
        ]
        self.assertEqual(
            portfolio_selection._capacity_portfolio_quotas(
                balanced_supply,
                target=20,
            ),
            {
                "maximum_feasible": 5,
                "brief_target": 5,
                "balanced_yield": 5,
                "spatial_reserve": 5,
            },
        )

        rare_maximum_supply = [
            *[candidate("maximum_feasible") for _index in range(3)],
            *[candidate("brief_target") for _index in range(9)],
            *[candidate("balanced_yield") for _index in range(20)],
            *[candidate("spatial_reserve") for _index in range(20)],
        ]
        self.assertEqual(
            portfolio_selection._capacity_portfolio_quotas(
                rare_maximum_supply,
                target=20,
            ),
            {
                "maximum_feasible": 3,
                "brief_target": 6,
                "balanced_yield": 6,
                "spatial_reserve": 5,
            },
        )

    def test_bounded_solver_recovers_twenty_set_from_large_greedy_trap(self):
        count = 31
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=2.0 if index == 0 else 1.0 - index * 0.001,
                cap_keys=(f"candidate:{index}",),
                coverage_tags=(("required:maximum",) if index == 20 else ()),
            )
            for index in range(count)
        ]
        compatibility = [[True for _right in range(count)] for _left in range(count)]
        for index in range(1, 21):
            compatibility[0][index] = False
            compatibility[index][0] = False

        selected = portfolio_selection.solve_bounded_compatible_subset(
            facts,
            compatibility,
            target_count=20,
            maximum_key_counts={f"candidate:{index}": 1 for index in range(count)},
            required_coverage_tags=("required:maximum",),
            beam_width=128,
        )

        self.assertEqual(len(selected), 20)
        self.assertNotIn(0, selected)
        self.assertIn(20, selected)

    def test_milp_solver_proves_maximum_set_under_caps_and_coverage(self):
        count = 31
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=2.0 if index == 0 else 1.0 - index * 0.001,
                cap_keys=(f"candidate:{index}", f"band:{index % 4}"),
                coverage_tags=(("required:maximum",) if index == 20 else ()),
            )
            for index in range(count)
        ]
        compatibility = [[True for _right in range(count)] for _left in range(count)]
        for index in range(1, 21):
            compatibility[0][index] = False
            compatibility[index][0] = False
        maximum_counts = {
            **{f"candidate:{index}": 1 for index in range(count)},
            **{f"band:{index}": 6 for index in range(4)},
        }

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            compatibility,
            target_count=20,
            maximum_key_counts=maximum_counts,
            required_coverage_tags=("required:maximum",),
        )

        self.assertEqual(len(selected), 20)
        self.assertNotIn(0, selected)
        self.assertIn(20, selected)

    def test_joint_scope_anchors_include_rare_capacity_band_before_greedy_selection(self):
        scopes = ("1/1", "1/2", "1/4", "1/8", "1/16", "3/8")
        alternatives = (
            "spatial_reserve", "balanced_yield", "brief_target",
            "maximum_feasible", "spatial_reserve", "balanced_yield",
        )
        principle_kinds = (
            "base_operative", "combination", "aggregation",
            "base_operative", "combination", "aggregation",
        )
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                scope=scope,
                alternative=alternatives[index],
                principle_kind=principle_kinds[index],
                operation=f"operation_{index}",
                score=1.0 - index * 0.01,
                seed=f"seed_{index}",
                section=f"section_{index}",
                roof=f"roof_{index}",
                chassis=f"chassis_{index}",
                phenotype=f"phenotype_{index}",
            )
            for index, scope in enumerate(scopes)
        ]
        with (
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_capacity_alternative_key", side_effect=lambda item: item.alternative),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
                "wedge_like": False,
                "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
        ):
            anchors = portfolio_selection._scope_coverage_anchors(
                candidates,
                seed_family_cap=2,
                section_family_cap=6,
                roof_archetype_caps={candidate.roof: 2 for candidate in candidates},
                chassis_family_caps={candidate.chassis: 2 for candidate in candidates},
                phenotype_cap=6,
                wedge_like_cap=2,
                pyramidal_like_cap=2,
                required_principle_kinds=("base_operative", "combination", "aggregation"),
                required_capacity_alternatives=(
                    "spatial_reserve", "balanced_yield", "brief_target", "maximum_feasible",
                ),
            )

        self.assertEqual({candidate.scope for candidate in anchors}, set(scopes))
        self.assertIn("maximum_feasible", {candidate.alternative for candidate in anchors})

    def test_final_ast_controller_resolves_stale_snapshot_missing_concept(self):
        source = SimpleNamespace(metadata={
            "geometry_program": {
                "metadata": {"base_seed": "bar"},
                "nodes": [
                    {
                        "id": "book03_book_split",
                        "operator": "book_split",
                        "parameters": {"access_side": "west"},
                    },
                ],
            },
            "program_context": {"site_access_side_in_program_frame": "west"},
            "geometry_graph_snapshot": {
                "design_concept_graph": {
                    "concept_nodes": [
                        {
                            "concept_id": "concept:public_threshold",
                            "missing_controller": True,
                        },
                    ],
                },
            },
        })
        candidate = SimpleNamespace(source=source)
        with (
            patch.object(candidate_analysis, "_architectural_articulation_metrics", return_value={"rules": []}),
            patch.object(candidate_analysis, "_roof_archetype", return_value="recursive:winged"),
        ):
            descriptor = candidate_analysis._design_concept_descriptor(candidate)

        self.assertEqual(descriptor["missing_required_concepts"], [])
        self.assertEqual(
            descriptor["resolved_snapshot_concepts_from_final_ast"],
            ["concept:public_threshold"],
        )
        self.assertEqual(descriptor["threshold_controller_node_ids"], ["book03_book_split"])
        self.assertTrue(descriptor["frontage_aligned"])

    def test_replenishment_cycle_budget_is_bounded(self):
        with patch.dict(os.environ, {"MAAS_BOOK_REPLENISHMENT_CYCLES": ""}):
            self.assertEqual(portfolio_replenishment.replenishment_cycle_budget(), 1)
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(live_vlm=True),
                1,
            )
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(live_vlm=False),
                7,
            )
        with patch.dict(os.environ, {"MAAS_BOOK_REPLENISHMENT_CYCLES": "0"}):
            self.assertEqual(portfolio_replenishment.replenishment_cycle_budget(), 1)
        with patch.dict(os.environ, {"MAAS_BOOK_REPLENISHMENT_CYCLES": "9"}):
            self.assertEqual(portfolio_replenishment.replenishment_cycle_budget(), 8)

    def test_live_vlm_http_request_budget_is_a_process_wide_hard_cap(self):
        with (
            patch.dict(os.environ, {"MAAS_LIVE_VLM_MAX_REQUESTS": "2"}),
            patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0),
        ):
            self.assertEqual(vlm_scorer._consume_live_vlm_request_budget(), 1)
            self.assertEqual(vlm_scorer._consume_live_vlm_request_budget(), 2)
            with self.assertRaisesRegex(
                vlm_scorer.VlmScoringError,
                "live_vlm_request_budget_exhausted:2/2",
            ):
                vlm_scorer._consume_live_vlm_request_budget()

    def test_replenishment_does_not_stop_on_intermediate_zero_pool_growth(self):
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=9,
                selected_scope_count=6,
                target_count=20,
                required_scope_count=6,
                cycles_run=2,
                cycle_budget=3,
            ),
            "",
        )
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=9,
                selected_scope_count=6,
                target_count=20,
                required_scope_count=6,
                cycles_run=3,
                cycle_budget=3,
            ),
            "cycle_budget_exhausted",
        )

    def test_final_vlm_cycle_accumulates_only_exact_hard_passes(self):
        retained = SimpleNamespace(key="retained")
        candidate = SimpleNamespace(key="new")
        repaired = SimpleNamespace(key="repaired")
        with (
            patch.object(final_vlm_cycle, "_bounded_visual_selection_pool", side_effect=lambda items: list(items)),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                side_effect=[
                    ([candidate], {"hard_pass_count": 1, "audit_records": []}),
                    ([repaired], {"hard_pass_count": 1, "audit_records": []}),
                ],
            ),
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([repaired], {"repaired_candidate_count": 1}),
            ),
            patch.object(
                final_vlm_cycle,
                "evaluate_accepted_sources_downstream",
                return_value={"rows": [{"combined_hard_pass": True}]},
            ),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [candidate],
                retained_hard_passes=[retained],
                building_type="program",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="test",
                generation_site=object(),
                height=12.0,
                floors=4,
                generation_context=object(),
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                base_capacity_contract={},
                downstream_context={},
                hard_gate_summary=lambda report, pool: {"candidate_count": len(pool)},
                completion_status="complete",
                no_repair_status="no_repair",
            )

        self.assertEqual(result.selection_pool, [retained, candidate, repaired])
        self.assertEqual(result.final_vlm_gate["hard_pass_count"], 3)
        self.assertTrue(result.repair_evidence["same_run_causal_loop_closed"])

    def test_final_vlm_cycle_routes_only_capacity_target_passes_to_paid_review(self):
        target_pass = SimpleNamespace(
            key="target-pass",
            source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {"target_hard_pass": True},
            }),
        )
        target_miss = SimpleNamespace(
            key="target-miss",
            source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {"target_hard_pass": False},
            }),
        )
        reviewed_inputs = []

        def audit(items, **_kwargs):
            reviewed_inputs.append(list(items))
            return list(items), {"hard_pass_count": len(items), "audit_records": []}

        with (
            patch.object(
                final_vlm_cycle,
                "_bounded_visual_selection_pool",
                side_effect=lambda items: list(items),
            ),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                side_effect=audit,
            ),
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([], {"repaired_candidate_count": 0}),
            ),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [target_miss, target_pass],
                retained_hard_passes=[],
                building_type="program",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="test",
                generation_site=object(),
                height=12.0,
                floors=4,
                generation_context=None,
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                base_capacity_contract={},
                downstream_context={},
                hard_gate_summary=lambda report, pool: {
                    "candidate_count": len(pool)
                },
                completion_status="complete",
                no_repair_status="no_repair",
            )

        self.assertEqual(reviewed_inputs, [[target_pass]])
        self.assertEqual(result.selection_pool, [target_pass])
        self.assertEqual(
            result.initial_vlm_gate["capacity_target_routing"][
                "rejected_before_paid_vlm_count"
            ],
            1,
        )

    def test_final_vlm_cycle_skips_paid_review_when_all_measured_candidates_miss_target(self):
        target_miss = SimpleNamespace(
            key="target-miss",
            source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {"target_hard_pass": False},
            }),
        )

        with (
            patch.object(
                final_vlm_cycle,
                "_bounded_visual_selection_pool",
                side_effect=lambda items: list(items),
            ),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
            ) as paid_review,
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
            ) as repair,
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [target_miss],
                retained_hard_passes=[],
                building_type="program",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="test",
                generation_site=object(),
                height=12.0,
                floors=4,
                generation_context=None,
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                base_capacity_contract={},
                downstream_context={},
                hard_gate_summary=lambda report, pool: {
                    "candidate_count": len(pool)
                },
                completion_status="complete",
                no_repair_status="no_repair",
            )

        paid_review.assert_not_called()
        repair.assert_not_called()
        self.assertEqual(result.selection_pool, [])
        self.assertEqual(
            result.initial_vlm_gate["status"],
            "no_capacity_target_hard_pass_candidates",
        )
        self.assertEqual(
            result.final_vlm_gate["status"],
            "no_capacity_target_hard_pass_candidates",
        )

    def test_replenishment_vlm_reviews_only_new_candidates(self):
        retained = [SimpleNamespace(key="prior-pass")]
        new = [SimpleNamespace(key="new-candidate")]
        with patch.object(
            portfolio_benchmark,
            "_bounded_visual_selection_pool",
            side_effect=lambda items: list(items),
        ):
            kept, review_pool = portfolio_benchmark._partition_replenishment_vlm_candidates(
                retained,
                new,
            )

        self.assertEqual([item.key for item in kept], ["prior-pass"])
        self.assertEqual([item.key for item in review_pool], ["new-candidate"])
        self.assertNotIn(retained[0], review_pool)

    def test_individual_vlm_cache_key_is_program_and_review_stage_scoped(self):
        geometry = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]],
        }
        neighborhood = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "program_context": {"program_id": "neighborhood_living"},
                "site_access_context": {"side": "west"},
                "portfolio_diversity_context": {"book_review_stage": "final_book"},
            },
        }
        gymnasium = {
            **neighborhood,
            "properties": {
                **neighborhood["properties"],
                "program_context": {"program_id": "gymnasium"},
            },
        }
        base_review = {
            **neighborhood,
            "properties": {
                **neighborhood["properties"],
                "portfolio_diversity_context": {
                    "book_review_stage": "book_base_operative",
                },
            },
        }

        neighborhood_key = _vlm_cache_key(neighborhood, [], "test-model")
        self.assertNotEqual(neighborhood_key, _vlm_cache_key(gymnasium, [], "test-model"))
        self.assertNotEqual(neighborhood_key, _vlm_cache_key(base_review, [], "test-model"))

    def test_base_vlm_reviews_exact_parents_of_diverse_descendants_first(self):
        def candidate(name, stage, parent_key, score):
            return SimpleNamespace(
                key=name,
                score=score,
                sequence=SimpleNamespace(name=name),
                source=SimpleNamespace(metadata={
                    "book_generation_lineage": {
                        "stage": stage,
                        "parent_key": parent_key,
                    },
                }),
            )

        base_1 = candidate("base-1", "base", "parent-1", 0.99)
        base_2 = candidate("base-2", "base", "parent-2", 0.80)
        base_3 = candidate("base-3", "base", "parent-3", 0.70)
        descendant_2 = candidate("descendant-2", "combination", "parent-2", 0.95)
        descendant_3 = candidate("descendant-3", "aggregation", "parent-3", 0.90)
        with patch.object(
            vlm_review,
            "_final_book_vlm_shortlist",
            side_effect=lambda items, target, **_kwargs: list(items)[:target],
        ):
            shortlist, evidence = vlm_review._book_base_parent_shortlist(
                [base_1, base_2, base_3, descendant_2, descendant_3],
                target=3,
                visual_directive={},
            )

        self.assertEqual([item.key for item in shortlist], ["base-2", "base-3", "base-1"])
        self.assertEqual(evidence["requested_exact_parent_count"], 2)
        self.assertTrue(evidence["descendant_first_parent_resolution"])

    def test_base_vlm_replenishment_quota_does_not_oversample_capped_family(self):
        def candidate(name, family, score):
            return SimpleNamespace(
                key=name,
                family=family,
                chassis=f"chassis-{family}",
                score=score,
                source=SimpleNamespace(metadata={
                    "book_generation_lineage": {
                        "stage": "base",
                        "parent_key": f"parent-{name}",
                    },
                }),
            )

        candidates = [
            *[candidate(f"repeat-{index}", "repeated", 1.0 - index * 0.01) for index in range(5)],
            candidate("lift", "lift", 0.80),
            candidate("notch", "notch", 0.79),
            candidate("split", "split_bridge", 0.78),
        ]
        with (
            patch.object(vlm_review, "_final_book_vlm_shortlist", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(vlm_review, "_form_bank_lane", return_value="bounded_synthesis"),
        ):
            shortlist, evidence = vlm_review._book_base_parent_shortlist(
                candidates,
                target=4,
                visual_directive={"max_geometry_family_counts": {"repeated": 1}},
            )

        self.assertEqual(sum(item.family == "repeated" for item in shortlist), 1)
        self.assertEqual({item.family for item in shortlist}, {
            "repeated", "lift", "notch", "split_bridge",
        })
        self.assertGreater(evidence["review_cap_skip_counts"]["geometry:repeated"], 0)
        self.assertTrue(evidence["review_caps_are_supply_quotas_not_quality_relaxations"])

    def test_base_vlm_shortlist_reserves_one_review_per_chassis_before_score_fill(self):
        def candidate(name, chassis, score):
            return SimpleNamespace(
                key=name,
                family="shared-agent-family",
                chassis=chassis,
                score=score,
                source=SimpleNamespace(metadata={
                    "book_generation_lineage": {
                        "stage": "base",
                        "parent_key": f"parent-{name}",
                    },
                }),
            )

        candidates = [
            *[candidate(f"repeat-{index}", "repeated", 1.0 - index * 0.01) for index in range(5)],
            candidate("court", "courtyard", 0.70),
            candidate("split", "split-wing", 0.69),
            candidate("cross", "distributed-cross", 0.68),
        ]
        with (
            patch.object(vlm_review, "_final_book_vlm_shortlist", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(vlm_review, "_form_bank_lane", return_value="bounded_synthesis"),
        ):
            shortlist, evidence = vlm_review._book_base_parent_shortlist(
                candidates,
                target=4,
                visual_directive={},
            )

        self.assertEqual({item.chassis for item in shortlist}, {
            "repeated", "courtyard", "split-wing", "distributed-cross",
        })
        self.assertEqual(evidence["chassis_family_anchor_count"], 4)

    def test_default_outcome_graph_is_pnu_scoped_not_output_directory_scoped(self):
        with TemporaryDirectory() as temporary_dir, patch.dict(
            os.environ,
            {"MAAS_OUTCOME_GRAPH_DIR": temporary_dir},
        ):
            first = portfolio_benchmark.default_outcome_graph_path("11680/parcel:004")
            second = portfolio_benchmark.default_outcome_graph_path("11680/parcel:004")
            other = portfolio_benchmark.default_outcome_graph_path("11680/parcel:005")

        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertEqual(first.parent, Path(temporary_dir).resolve())
        self.assertNotIn("/", first.name)
        self.assertNotIn(":", first.name)

    def test_final_vlm_shortlist_reserves_review_bandwidth_for_typed_llm_author_lane(self):
        procedural = [
            SimpleNamespace(
                key=f"procedural-{index}",
                score=1.0 - index * 0.001,
                authored=False,
                family=f"agent_family_{index % 8}",
                scope=("1/1", "1/2", "1/4", "1/8")[index % 4],
                phenotype=("prismatic", "stepped", "voided")[index % 3],
                principle_kind="base_operative",
            )
            for index in range(100)
        ]
        authored = [
            SimpleNamespace(
                key=f"authored-{index}",
                score=0.7 - index * 0.001,
                authored=True,
                family=f"llm_family_{index % 5}",
                scope=("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")[index % 6],
                phenotype=("curved", "oblique", "winged", "voided")[index % 4],
                principle_kind="combination",
            )
            for index in range(20)
        ]
        pool = [*procedural, *authored]
        with (
            patch.object(vlm_review, "_llm_authored_candidate", side_effect=lambda item: item.authored),
            patch.object(vlm_review, "_form_bank_lane", return_value=""),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(vlm_review, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
            }),
            patch.object(vlm_review, "_select", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
        ):
            shortlist = portfolio_benchmark._final_book_vlm_shortlist(
                pool,
                target=64,
                visual_directive={},
            )

        self.assertEqual(len(shortlist), 64)
        self.assertGreaterEqual(sum(item.authored for item in shortlist), 16)

    def test_final_vlm_shortlist_reviews_each_available_executable_core_family(self):
        synthesized = [
            SimpleNamespace(
                key=f"synthesized-{index}",
                score=1.0 - index * 0.001,
                lane="bounded_synthesis",
                family=f"agent_family_{index % 12}",
                scope=("1/1", "1/2", "1/4", "1/8")[index % 4],
                phenotype=("prismatic", "stepped", "voided")[index % 3],
                principle_kind="base_operative",
            )
            for index in range(120)
        ]
        core = [
            SimpleNamespace(
                key=f"core-{family}-{variant}",
                score=0.65 - family * 0.002 - variant * 0.001,
                lane="executable_core_language",
                family=f"core_family_{family}",
                scope=("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")[variant % 6],
                phenotype=("winged", "voided", "curved")[variant % 3],
                principle_kind="combination",
            )
            for family in range(18)
            for variant in range(2)
        ]
        pool = [*synthesized, *core]
        with (
            patch.object(vlm_review, "_llm_authored_candidate", return_value=False),
            patch.object(vlm_review, "_form_bank_lane", side_effect=lambda item: item.lane),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(vlm_review, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
            }),
            patch.object(vlm_review, "_select", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
        ):
            shortlist = vlm_review._final_book_vlm_shortlist(
                pool,
                target=64,
                visual_directive={},
            )

        reviewed_core_families = {
            item.family for item in shortlist
            if item.lane == "executable_core_language"
        }
        self.assertEqual(len(shortlist), 64)
        self.assertEqual(reviewed_core_families, {f"core_family_{index}" for index in range(18)})
        self.assertGreaterEqual(
            sum(item.lane == "executable_core_language" for item in shortlist),
            36,
        )

    def test_final_vlm_recovers_transient_call_failure_and_reports_it(self):
        site = Polygon(((0, 0), (20, 0), (20, 16), (0, 16)))
        sequence = program_seed_sequences("neighborhood_living")[0]
        source = compile_sequence_to_source_mass(site, sequence)
        self.assertIsNotNone(source)
        assert source is not None
        program = base_seed_program("slab")
        source = replace(source, metadata={
            **source.metadata,
            "geometry_program": program.to_dict(),
            "source_capacity_measurement": {
                "utilization_ratio": 0.8,
                "total_floor_area_m2": 240.0,
            },
            "capacity_alternative_projection": {
                "requested_capacity_alternative_id": "brief_target",
                "requested_target_utilization": 0.90,
                "selectable_capacity_alternative_id": "balanced",
                "selectable_capacity_target_utilization": 0.80,
                "selectable_capacity_hard_pass": True,
            },
            "shared_floor_contract": {
                "schema_version": "arr.maas.shared_floor_contract.v1",
                "floor_contract_hash": "floor-contract-test",
                "floor_capacity_plan_hash": "floor-plan-test",
                "target_floor_areas_m2": [80.0, 80.0, 80.0],
                "totals": {"requested_floors": 3, "total_floor_area_m2": 240.0},
                "hard_pass": True,
            },
        })
        candidate = portfolio_benchmark._Candidate(
            "book:operative:test",
            "base_operative",
            "test",
            sequence,
            source,
            {"type": "Feature", "geometry": None, "properties": {}},
            0.8,
        )
        attempts = 0
        reviewed_features = []

        def flaky_scorer(**kwargs):
            nonlocal attempts
            attempts += 1
            reviewed_features.append(kwargs["feature"])
            if attempts == 1:
                raise TimeoutError("transient unit-test timeout")
            return {
                "concept_scores": {},
                "critic_actions": [],
                "geometry_edits": [],
                "response_id": "recovered-response",
                "model": "test-vlm",
            }

        with (
            TemporaryDirectory() as temporary_dir,
            patch.object(vlm_review, "_audited_final_book_references", return_value=([], {
                "hard_pass": True,
                "accepted": [],
            })),
            patch.object(vlm_review, "_solid_morphology_metrics", return_value={
                "phenotype": "prismatic",
                "pyramidal_like": False,
            }),
            patch.object(vlm_review, "_final_book_vlm_hard_pass", return_value=(True, [])),
            patch.dict(os.environ, {"MAAS_FINAL_BOOK_VLM_RECOVERY_WORKERS": "1"}),
        ):
            accepted, evidence = vlm_review._audit_final_book_geometry_with_vlm(
                [candidate],
                building_type="neighborhood_living",
                output_dir=Path(temporary_dir),
                visual_directive={},
                scorer=flaky_scorer,
                shortlist_override=[candidate],
            )

        self.assertEqual(attempts, 2)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(evidence["initial_call_failure_count"], 1)
        self.assertEqual(evidence["recovered_call_failure_count"], 1)
        self.assertEqual(evidence["unrecovered_call_failure_count"], 0)
        self.assertEqual(evidence["call_failure_records"], [])
        capacity_context = reviewed_features[-1]["properties"]["capacity_review_context"]
        self.assertEqual(
            capacity_context["capacity_alternative"][
                "selectable_capacity_alternative_id"
            ],
            "balanced",
        )
        self.assertEqual(
            capacity_context["target_floor_areas_m2"],
            [80.0, 80.0, 80.0],
        )
        self.assertEqual(
            accepted[0].source.metadata["final_book_vlm_audit"][
                "capacity_review_context"
            ]["floor_contract_hash"],
            "floor-contract-test",
        )

    def test_final_vlm_rejects_legacy_candidate_before_provider_call(self):
        legacy = SimpleNamespace(
            source=SimpleNamespace(metadata={}),
            feature={"type": "Feature", "properties": {}},
            sequence=SimpleNamespace(name="legacy-program-sequence"),
            score=0.9,
        )

        def scorer_must_not_run(**_kwargs):
            raise AssertionError("legacy geometry must not reach the exact-AST VLM")

        with TemporaryDirectory() as temporary_dir:
            accepted, evidence = vlm_review._audit_final_book_geometry_with_vlm(
                [legacy],
                building_type="neighborhood_living",
                output_dir=Path(temporary_dir),
                visual_directive={},
                scorer=scorer_must_not_run,
                shortlist_override=[legacy],
            )

        self.assertEqual(accepted, [])
        self.assertEqual(evidence["input_count"], 1)
        self.assertEqual(evidence["exact_geometry_program_input_count"], 0)
        self.assertEqual(evidence["invalid_geometry_program_rejected_count"], 1)
        self.assertEqual(evidence["initial_call_failure_count"], 0)

    def test_final_vlm_typed_edit_keeps_book_ast_and_reprojects_legal_floor_stack(self):
        site = Polygon(((0, 0), (42, 0), (42, 30), (0, 30)))
        sequence = program_seed_sequences("gymnasium")[0]
        source = compile_sequence_to_source_mass(site, sequence)
        self.assertIsNotNone(source)
        assert source is not None
        parent_program = base_seed_program("slab")
        parent_capacity_alternative = {
            "schema_version": "arr.maas.capacity_alternative_projection.v1",
            "alternative_id": "maximum_feasible",
            "target_utilization": 0.98,
            "target_floor_area_m2": 3704.4,
        }
        base_capacity_contract = {
            "schema_version": "arr.maas.feasible_base_capacity.v1",
            "minimum_utilization": 0.70,
            "target_utilization": 0.90,
            "feasible_maximum_floor_area_m2": 3780.0,
            "generation_site_area_m2": float(site.area),
            "requested_floors": 3,
        }
        source = replace(source, metadata={
            **source.metadata,
            "geometry_program": parent_program.to_dict(),
            "geometry_program_bridge_evidence": {"legal_fit_strength": 0.0},
            "legal_generation_context_evidence": {},
            "capacity_alternative_projection": parent_capacity_alternative,
            "floorwise_legal_matrix_stack": {
                "status": "materialized",
                "target_plan_coverage": 0.74,
            },
        })
        candidate = portfolio_benchmark._Candidate(
            "test-principle",
            "base_operative",
            "expand",
            sequence,
            source,
            {"type": "Feature", "properties": {}},
            0.8,
        )
        audit_gate = {"audit_records": [{
            "source_sequence": sequence.name,
            "hard_pass": False,
            "response_id": "critic-exact-1",
            "geometry_edits": [{
                "operation": "set_parameter",
                "target_node_id": "seed_slab",
                "parameter_name": "vector",
                "vector_value": [2.65, 1.25, 0.34],
            }],
        }]}

        def materialize(_base_source, repaired_program, **_kwargs):
            return replace(source, metadata={
                **source.metadata,
                "geometry_program": repaired_program.to_dict(),
            })

        def attach_evidence(feature, **_kwargs):
            feature.setdefault("properties", {})["program_spatial_evidence"] = {
                "architectural_score": 0.82,
            }
            return {"hard_pass": True, "program_fit_score": 0.84}

        with (
            patch.object(vlm_review, "compile_sequence_to_source_mass", return_value=source),
            patch.object(vlm_review, "replace_source_dominant_with_geometry_program", side_effect=materialize),
            patch.object(vlm_review, "_clean_mass_gate", return_value=(True, {"failure_reasons": []})),
            patch.object(vlm_review, "_inside_site", return_value=True),
            patch.object(vlm_review, "source_feature", return_value={"type": "Feature", "properties": {}}),
            patch.object(vlm_review, "attach_program_massing_evidence", side_effect=attach_evidence),
            patch.object(vlm_review, "_program_form_gate", return_value={"hard_pass": True}),
            patch.object(vlm_review, "measure_source_capacity", return_value={
                "schema_version": "arr.maas.source_capacity_measurement.v1",
                "feasible_capacity_utilization": 0.99,
            }),
            patch.object(
                vlm_review,
                "materialize_floorwise_legal_source",
                side_effect=lambda repaired_source, **_kwargs: repaired_source,
            ) as floorwise_reprojection,
            patch.object(
                vlm_review,
                "_materialize_repaired_floor_contract",
                return_value={"hard_pass": True, "failure_reasons": []},
            ),
            patch.object(vlm_review, "generation_site_at_height", return_value=site),
        ):
            repaired, counts = portfolio_benchmark._repair_exact_post_book_candidates_from_vlm(
                [candidate],
                audit_gate,
                generation_site=site,
                building_type="gymnasium",
                height=18.0,
                floors=3,
                generation_context=SimpleNamespace(),
                program_dimensional_context={},
                site_boundary_source="unit_test",
                site_access_context={},
                site_access_geometry=None,
                base_capacity_contract=base_capacity_contract,
                capacity_site=site,
            )

        self.assertEqual(len(repaired), 1)
        self.assertEqual(counts["geometry_changed_count"], 1)
        self.assertEqual(counts["repaired_candidate_count"], 1)
        self.assertEqual(counts["floorwise_legal_reprojection_count"], 1)
        self.assertEqual(floorwise_reprojection.call_count, 1)
        self.assertEqual(
            floorwise_reprojection.call_args.kwargs["target_plan_coverage"],
            0.74,
        )
        self.assertFalse(counts["book_reprojection_applied"])
        repaired_program = repaired[0].source.metadata["geometry_program"]
        self.assertEqual(
            repaired_program["metadata"]["final_vlm_repair"]["parent_program_hash"],
            parent_program.program_hash(),
        )
        self.assertNotEqual(
            compile_geometry_program(parent_program).geometry_hash,
            compile_geometry_program(type(parent_program).from_dict(repaired_program)).geometry_hash,
        )
        repaired_capacity = repaired[0].source.metadata["capacity_alternative_projection"]
        self.assertEqual(repaired_capacity["alternative_id"], "maximum_feasible")
        self.assertEqual(repaired_capacity["target_utilization"], 0.98)
        self.assertTrue(repaired_capacity["target_hard_pass"])

    def test_exact_post_book_repair_reserves_bandwidth_for_typed_llm_ast(self):
        candidates = []
        records = {}
        for index in range(12):
            authored = index >= 8
            name = f"candidate-{index}"
            program_metadata = {
                "family": f"{'llm' if authored else 'agent'}_{index}",
                **({"author_provider": "openai_llm_geometry_author"} if authored else {}),
            }
            candidates.append(SimpleNamespace(
                sequence=SimpleNamespace(name=name),
                source=SimpleNamespace(metadata={
                    "geometry_program": {"metadata": program_metadata},
                }),
                score=1.0 - index * 0.01,
            ))
            records[name] = {
                "failures": ["final_book_unresolved_public_threshold_relation"],
                "concept_scores": {
                    "gesture_clarity": 0.78,
                    "hierarchy": 0.76,
                    "repair_integrity": 0.82,
                    "program_appropriateness": 0.7,
                    "void_publicness": 0.62,
                    "section_program_fit": 0.66,
                },
            }

        selected = portfolio_benchmark._exact_post_book_repair_shortlist(
            candidates,
            records,
            repair_budget=6,
        )

        self.assertEqual(len(selected), 6)
        self.assertEqual(
            sum(portfolio_benchmark._llm_authored_candidate(candidate) for candidate in selected),
            4,
        )

    def test_vlm_normalization_rejects_arbitrary_tier_before_archive(self):
        scores = {
            "gesture_clarity": 0.82,
            "hierarchy": 0.84,
            "non_stair_silhouette": 0.22,
            "void_publicness": 0.76,
            "repair_integrity": 0.86,
            "precedent_resonance": 0.72,
            "program_appropriateness": 0.80,
            "section_program_fit": 0.66,
        }
        unresolved = _normalize_vlm_result({
            "concept_scores": scores,
            "program_fit_hard_pass": True,
            "critic_actions": ["preserve_dominant_gesture"],
        }, model="test-vlm", response_id="unresolved")
        intentional = _normalize_vlm_result({
            "concept_scores": scores,
            "program_fit_hard_pass": True,
            "critic_actions": ["good_step_mass"],
        }, model="test-vlm", response_id="intentional")

        self.assertFalse(unresolved["program_fit_hard_pass"])
        self.assertIn("weak_form_continuity", unresolved["critic_actions"])
        self.assertTrue(intentional["program_fit_hard_pass"])

    def test_final_book_vlm_gate_rejects_fragmentation_and_arbitrary_tiers(self):
        accepted, accepted_failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.82,
            },
            "critic_actions": ["good_step_mass", "preserve_dominant_gesture"],
        })
        fragmented, fragmented_failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {"non_stair_silhouette": 0.71},
            "critic_actions": ["too_fragmented", "weak_form_continuity"],
        })
        tiered, tiered_failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {"non_stair_silhouette": 0.41},
            "critic_actions": [],
        })

        self.assertTrue(accepted)
        self.assertEqual(accepted_failures, [])
        self.assertFalse(fragmented)
        self.assertIn("final_book_vlm_too_fragmented", fragmented_failures)
        self.assertIn("final_book_vlm_weak_form_continuity", fragmented_failures)
        self.assertFalse(tiered)
        self.assertIn("final_book_arbitrary_tier_silhouette", tiered_failures)

    def test_base_book_vlm_gate_preserves_developable_parent_for_descendants(self):
        result = {
            "program_fit_hard_pass": False,
            "concept_scores": {
                "gesture_clarity": 0.66,
                "hierarchy": 0.64,
                "repair_integrity": 0.74,
                "program_appropriateness": 0.55,
                "non_stair_silhouette": 0.44,
            },
            "critic_actions": [
                "too_box_like", "weak_form_continuity", "wrong_program_typology",
            ],
        }

        base_pass, base_failures = portfolio_benchmark._final_book_vlm_hard_pass(
            result,
            review_stage="book_base_operative",
        )
        final_pass, final_failures = portfolio_benchmark._final_book_vlm_hard_pass(result)

        self.assertTrue(base_pass)
        self.assertEqual(base_failures, [])
        self.assertFalse(final_pass)
        self.assertIn("final_book_program_fit_failed", final_failures)
        self.assertIn("final_book_vlm_too_box_like", final_failures)
        self.assertIn("final_book_vlm_wrong_program_typology", final_failures)

    def test_book_vlm_base_capacity_floor_scales_with_exact_book_scope(self):
        base_policy = vlm_review.book_vlm_stage_policy("book_base_operative")
        final_policy = vlm_review.book_vlm_stage_policy("final_book")

        self.assertEqual(base_policy.minimum_feasible_capacity_utilization, 0.40)
        self.assertEqual(final_policy.minimum_feasible_capacity_utilization, 0.40)
        self.assertEqual(base_policy.capacity_normalization, "book_scope_fraction")
        self.assertEqual(final_policy.capacity_normalization, "none")

        candidate = SimpleNamespace(source=SimpleNamespace(metadata={
            "program_book_projection_evidence": {
                "scope": {"base_volume_label": "1/16"},
            },
        }))
        self.assertAlmostEqual(
            vlm_review._book_stage_capacity_floor(candidate, "book_base_operative"),
            0.025,
        )
        self.assertAlmostEqual(
            vlm_review._book_stage_capacity_floor(candidate, "final_book"),
            0.40,
        )

        result = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.82,
            },
            "critic_actions": ["preserve_dominant_gesture"],
        }
        viable, viable_failures = vlm_review._final_book_vlm_hard_pass(
            result,
            candidate_capacity={"feasible_capacity_utilization": 0.45},
            minimum_capacity_utilization=final_policy.minimum_feasible_capacity_utilization,
        )
        undersized, undersized_failures = vlm_review._final_book_vlm_hard_pass(
            result,
            candidate_capacity={"feasible_capacity_utilization": 0.39},
            minimum_capacity_utilization=final_policy.minimum_feasible_capacity_utilization,
        )

        self.assertTrue(viable)
        self.assertEqual(viable_failures, [])
        self.assertFalse(undersized)
        self.assertIn("book_stage_feasible_capacity_below_competition_floor", undersized_failures)

    def test_final_book_vlm_gate_requires_massing_legible_reference_images(self):
        hard_pass, failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.82,
            },
            "critic_actions": ["preserve_dominant_gesture"],
            "reference_massing_gate": {
                "hard_pass": False,
                "minimum_program_specific_images": 3,
                "massing_suitable_program_image_count": 2,
            },
        })

        self.assertFalse(hard_pass)
        self.assertIn("final_book_reference_massing_suitability_failed", failures)

    def test_final_book_vlm_gate_requires_program_relation_for_pyramidal_mass(self):
        base_result = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.72,
                "void_publicness": 0.40,
                "section_program_fit": 0.48,
            },
            "critic_actions": ["good_step_mass"],
        }

        hard_pass, failures = portfolio_benchmark._final_book_vlm_hard_pass(
            base_result,
            candidate_morphology={"pyramidal_like": True, "section_phenotype": "none"},
            candidate_design_concept={"frontage_aligned": False},
        )
        resolved_result = {
            **base_result,
            "concept_scores": {
                **base_result["concept_scores"],
                "section_program_fit": 0.78,
            },
        }
        resolved, resolved_failures = portfolio_benchmark._final_book_vlm_hard_pass(
            resolved_result,
            candidate_morphology={"pyramidal_like": True, "section_phenotype": "stepped"},
            candidate_design_concept={"frontage_aligned": False},
        )

        self.assertFalse(hard_pass)
        self.assertIn("final_book_unresolved_pyramidal_program_relation", failures)
        self.assertTrue(resolved)
        self.assertEqual(resolved_failures, [])

    def test_final_book_vlm_gate_does_not_accept_unresolved_access_side_void_request(self):
        result = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.84,
                "hierarchy": 0.78,
                "repair_integrity": 0.82,
                "program_appropriateness": 0.72,
                "non_stair_silhouette": 0.70,
                "void_publicness": 0.34,
            },
            "critic_actions": ["needs_carved_void", "preserve_dominant_gesture"],
        }

        hard_pass, failures = portfolio_benchmark._final_book_vlm_hard_pass(
            result,
            candidate_morphology={"pyramidal_like": False, "section_phenotype": "none"},
            candidate_design_concept={
                "target_access_side_in_program_frame": "west",
                "frontage_aligned": False,
            },
        )

        self.assertFalse(hard_pass)
        self.assertIn("final_book_unresolved_public_threshold_relation", failures)

    def test_portfolio_joint_anchor_preserves_all_available_book_language_depths(self):
        scopes = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")
        kinds = ("base_operative", "base_operative", "combination", "base_operative", "aggregation", "base_operative")
        candidates = [
            SimpleNamespace(
                scope=scope,
                principle_kind=kind,
                operation=f"op_{index}",
                score=1.0 - index * 0.01,
                seed=f"seed_{index}",
                section=f"section_{index % 2}",
                roof=f"roof_{index % 3}",
                chassis=f"chassis_{index % 2}",
                phenotype="oblique" if index else "curved",
            )
            for index, (scope, kind) in enumerate(zip(scopes, kinds))
        ]
        with (
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {"phenotype": item.phenotype}),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
        ):
            anchors = portfolio_benchmark._scope_coverage_anchors(
                candidates,
                seed_family_cap=2,
                section_family_cap=4,
                roof_archetype_caps={f"roof_{index}": 4 for index in range(3)},
                chassis_family_caps={f"chassis_{index}": 4 for index in range(2)},
                phenotype_cap=5,
                wedge_like_cap=2,
                pyramidal_like_cap=2,
                required_phenotypes=("curved", "oblique"),
                required_principle_kinds=("base_operative", "combination", "aggregation"),
            )

        self.assertEqual({item.scope for item in anchors}, set(scopes))
        self.assertEqual(
            {item.principle_kind for item in anchors},
            {"base_operative", "combination", "aggregation"},
        )

    def test_selector_enforces_measured_pyramidal_cap_after_anchor_stage(self):
        scopes = ["1/1", "3/8", "1/2", "1/4", "1/8", "1/16"]
        candidates = []
        for index, scope in enumerate(scopes):
            for pyramidal in (True, False):
                candidates.append(SimpleNamespace(
                    key=f"{scope}:{pyramidal}",
                    scope=scope,
                    principle_kind="base_operative",
                    operation=f"operation_{index}_{int(pyramidal)}",
                    score=1.0 if pyramidal else 0.8,
                    seed=f"seed_{index}_{int(pyramidal)}",
                    section=f"section_{index}_{int(pyramidal)}",
                    roof=f"roof_{index}_{int(pyramidal)}",
                    chassis=f"chassis_{index}_{int(pyramidal)}",
                    phenotype="stepped" if pyramidal else f"non_step_{index}",
                    pyramidal=pyramidal,
                ))
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
                "wedge_like": False,
                "pyramidal_like": item.pyramidal,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge",
                "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_geometry_program_family", return_value=""),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_benchmark._select(
                candidates,
                target=10,
                visual_directive={"max_pyramidal_like_count": 2},
            )

        self.assertEqual(sum(item.pyramidal for item in selected), 2)
        self.assertLess(len(selected), 10)

    def test_selector_consumes_next_run_geometry_family_supply_cap(self):
        scopes = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")
        candidates = []
        for index, scope in enumerate(scopes):
            for family, score in (("repeated_family", 1.0), (f"alternate_{index}", 0.8)):
                candidates.append(SimpleNamespace(
                    key=f"{scope}:{family}", scope=scope,
                    principle_kind="base_operative", operation=f"op_{index}_{family}",
                    score=score, seed=f"seed_{index}_{family}",
                    section=f"section_{index}_{family}", roof=f"roof_{index}_{family}",
                    chassis=f"chassis_{index}_{family}", phenotype="prismatic",
                    family=family,
                ))
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=6,
                visual_directive={"max_geometry_family_counts": {"repeated_family": 1}},
                selection_trace=trace,
            )

        self.assertEqual(sum(item.family == "repeated_family" for item in selected), 1)
        self.assertEqual(trace["memory_geometry_family_caps"], {"repeated_family": 1})

    def test_selector_reserves_a_slot_for_missing_chassis_only_after_hard_pass_pool(self):
        candidates = [
            SimpleNamespace(
                key=name, scope="1/1", principle_kind="base_operative",
                operation=f"op_{name}", score=score, seed=f"seed_{name}",
                section=f"section_{name}", roof=f"roof_{name}",
                chassis=chassis, phenotype="prismatic", family=f"family_{name}",
            )
            for name, score, chassis in (
                ("common_a", 1.0, "recursive_chassis:courtyard"),
                ("common_b", 0.9, "recursive_chassis:courtyard"),
                ("radial", 0.2, "recursive_chassis:radial_wings"),
            )
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=2,
                visual_directive={
                    "required_chassis_families": ["recursive_chassis:radial_wings"],
                },
                selection_trace=trace,
            )

        self.assertIn("recursive_chassis:radial_wings", {item.chassis for item in selected})
        self.assertEqual(trace["after_chassis_anchor_count"], 2)

    def test_selector_treats_memory_chassis_cap_as_priority_when_it_would_leave_empty_cards(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}", scope="1/1",
                principle_kind="base_operative", operation=f"op_{index}",
                score=1.0 - index * 0.1, seed=f"seed_{index}",
                section=f"section_{index}", roof=f"roof_{index}",
                chassis="recursive_chassis:courtyard",
                phenotype=f"phenotype_{index}", family=f"family_{index}",
            )
            for index in range(3)
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": f"ground_{item.key}", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=3,
                visual_directive={
                    "max_chassis_family_counts": {"recursive_chassis:courtyard": 1},
                },
                selection_trace=trace,
            )

        self.assertEqual(len(selected), 3)
        self.assertEqual(trace["memory_cap_primary_selection_count"], 1)
        self.assertEqual(trace["memory_cap_fallback_added_count"], 2)

    def test_selector_rejects_measured_capacity_target_miss_before_diversity_scoring(self):
        candidates = [
            SimpleNamespace(
                key=name,
                scope="1/1",
                principle_kind="base_operative",
                operation=f"op_{name}",
                score=score,
                seed=f"seed_{name}",
                section=f"section_{name}",
                roof=f"roof_{name}",
                chassis=f"chassis_{name}",
                phenotype="prismatic",
                family=f"family_{name}",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": "maximum_feasible",
                        "target_hard_pass": capacity_pass,
                    },
                }),
            )
            for name, score, capacity_pass in (
                ("high_score_miss", 1.0, False),
                ("measured_pass", 0.6, True),
            )
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=1,
                selection_trace=trace,
            )

        self.assertEqual([candidate.key for candidate in selected], ["measured_pass"])
        self.assertEqual(trace["capacity_target_gate_measured_count"], 2)
        self.assertEqual(trace["capacity_target_gate_pass_count"], 1)
        self.assertEqual(trace["capacity_target_gate_rejected_count"], 1)

    def test_milp_capacity_bands_require_coverage_without_blocking_absorption(self):
        alternatives = (
            ["maximum_feasible"]
            + ["brief_target"] * 5
            + ["balanced_yield"] * 19
            + ["spatial_reserve"] * 30
        )
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                scope="1/1",
                principle_kind=("combination" if index == 1 else "base_operative"),
                operation=f"operation_{index % 12}",
                score=1.0 - index * 0.001,
                seed=f"seed_{index}",
                section=f"section_{index}",
                roof=f"roof_{index}",
                chassis=f"chassis_{index}",
                phenotype=f"phenotype_{index}",
                family=f"family_{index}",
                alternative=alternative,
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": alternative,
                        "target_hard_pass": True,
                    },
                }),
            )
            for index, alternative in enumerate(alternatives)
        ]
        trace = {}

        def silhouette(left, right):
            if left is right:
                return 1.0
            if left.alternative == right.alternative == "brief_target":
                return 0.0
            return 1.0

        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", side_effect=silhouette),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=20,
                selection_trace=trace,
            )

        selected_bands = Counter(item.alternative for item in selected)
        self.assertEqual(len(selected), 20)
        self.assertEqual(set(selected_bands), {
            "maximum_feasible", "brief_target", "balanced_yield", "spatial_reserve",
        })
        self.assertEqual(selected_bands["brief_target"], 1)
        self.assertEqual(
            trace["milp_capacity_band_policy"],
            "all_available_bands_required_once; nominal quotas are soft preferences",
        )

    def test_bounded_visual_pool_preserves_rare_capacity_pass_before_common_score(self):
        candidates = [
            SimpleNamespace(
                key=name,
                score=score,
                scope="1/1",
                family="shared_family",
                roof="shared_roof",
                seed="shared_seed",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": alternative_id,
                        "target_hard_pass": True,
                    },
                }),
            )
            for name, score, alternative_id in (
                ("common_reserve", 1.0, "spatial_reserve"),
                ("rare_maximum", 0.7, "maximum_feasible"),
            )
        ]
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
        ):
            retained = portfolio_selection._bounded_visual_selection_pool(
                candidates,
                per_family_scope=1,
                per_seed_scope=1,
            )

        self.assertEqual([candidate.key for candidate in retained], ["rare_maximum"])

    def test_selection_diagnostics_excludes_capacity_target_misses_like_selector(self):
        def candidate(key: str, hard_pass: bool):
            return SimpleNamespace(
                key=key,
                score=1.0,
                operation=key,
                principle_kind="base_operative",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": "balanced_yield",
                        "target_hard_pass": hard_pass,
                    },
                }),
            )

        selected = candidate("selected", True)
        valid_remaining = candidate("valid_remaining", True)
        target_miss = candidate("target_miss", False)
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.key),
            patch.object(portfolio_selection, "_section_family", return_value="section"),
            patch.object(portfolio_selection, "_roof_archetype", return_value="roof"),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.key),
            patch.object(portfolio_selection, "_plan_family", side_effect=lambda item: (
                "triangular" if item.key == "valid_remaining" else "quadrilateral"
            )),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_solid_morphology_metrics", return_value={
                "phenotype": "prismatic", "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge",
                "concept_key": item.key,
                "frontage_aligned": True,
            }),
        ):
            diagnostics = portfolio_selection._selection_capacity_diagnostics(
                [selected, valid_remaining, target_miss],
                [selected],
                target=20,
            )

        self.assertEqual(diagnostics["capacity_target_measured_count"], 3)
        self.assertEqual(diagnostics["capacity_target_pass_count"], 2)
        self.assertEqual(diagnostics["capacity_target_rejected_count"], 1)
        self.assertEqual(diagnostics["selection_universe_count"], 2)
        self.assertEqual(diagnostics["remaining_candidate_count"], 1)
        self.assertEqual(
            diagnostics["plan_family_supply_counts"],
            {"quadrilateral": 1, "triangular": 1},
        )

    def test_portfolio_feedback_resolves_replace_votes_to_exact_ast_family(self):
        rows = [{"variant_id": f"maas_{index:02}"} for index in range(1, 5)]
        candidates = [SimpleNamespace(family="profiled", chassis="courtyard") for _ in rows]
        audit = {
            "candidate_actions": [
                {"candidate_id": "maas_01", "decision": "keep"},
                {"candidate_id": "maas_02", "decision": "replace"},
                {"candidate_id": "maas_03", "decision": "replace"},
                {"candidate_id": "maas_04", "decision": "replace"},
            ],
        }
        with (
            patch.object(
                portfolio_feedback,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                portfolio_feedback,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
        ):
            enriched = portfolio_feedback.enrich_portfolio_vlm_feedback(
                audit, rows=rows, candidates=candidates,
            )

        self.assertEqual(
            enriched["geometry_family_action_counts"]["profiled"],
            {"keep": 1, "replace": 3},
        )
        self.assertEqual(enriched["overrepresented_geometry_families"], ["profiled"])
        self.assertEqual(
            enriched["chassis_family_action_counts"]["courtyard"],
            {"keep": 1, "replace": 3},
        )
        self.assertEqual(enriched["overrepresented_chassis_families"], ["courtyard"])

    def test_portfolio_feedback_marks_two_replaced_chassis_as_repeated(self):
        rows = [{"variant_id": "maas_01"}, {"variant_id": "maas_02"}]
        candidates = [SimpleNamespace(family="curve", chassis="curved_bar") for _ in rows]
        audit = {"candidate_actions": [
            {"candidate_id": "maas_01", "decision": "replace"},
            {"candidate_id": "maas_02", "decision": "replace"},
        ]}
        with (
            patch.object(portfolio_feedback, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_feedback, "_chassis_family", side_effect=lambda item: item.chassis),
        ):
            enriched = portfolio_feedback.enrich_portfolio_vlm_feedback(
                audit, rows=rows, candidates=candidates,
            )

        self.assertEqual(enriched["overrepresented_chassis_families"], ["curved_bar"])

    def test_post_run_descriptor_feedback_matches_live_candidate_feedback(self):
        enriched = portfolio_feedback.enrich_portfolio_vlm_feedback_from_descriptors(
            {"hard_pass": False, "candidate_actions": [
                {"candidate_id": "maas_01", "decision": "replace"},
                {"candidate_id": "maas_02", "decision": "replace"},
            ]},
            candidate_descriptors=[
                {"candidate_id": "maas_01", "geometry_family": "agent_notch", "chassis_family": "carved_monolith"},
                {"candidate_id": "maas_02", "geometry_family": "agent_notch", "chassis_family": "carved_monolith"},
            ],
        )

        self.assertEqual(enriched["overrepresented_geometry_families"], ["agent_notch"])
        self.assertEqual(enriched["overrepresented_chassis_families"], ["carved_monolith"])

    def test_portfolio_feedback_marks_missing_core_chassis_as_review_anchors(self):
        rows = [{"variant_id": "maas_01"}]
        candidates = [SimpleNamespace(family="curve", chassis="recursive_chassis:curved_bar")]
        with (
            patch.object(portfolio_feedback, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_feedback, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_feedback, "core_chassis_families", return_value=("curved_bar", "radial_wings")),
        ):
            failed = portfolio_feedback.enrich_portfolio_vlm_feedback(
                {"hard_pass": False, "candidate_actions": []},
                rows=rows,
                candidates=candidates,
            )
            passed = portfolio_feedback.enrich_portfolio_vlm_feedback(
                {"hard_pass": True, "candidate_actions": []},
                rows=rows,
                candidates=candidates,
            )

        self.assertEqual(
            failed["underrepresented_chassis_families"],
            ["recursive_chassis:radial_wings"],
        )
        self.assertEqual(passed["underrepresented_chassis_families"], [])

    def test_chassis_caps_apply_only_to_the_named_family(self):
        caps = portfolio_selection._chassis_caps(
            {"courtyard", "split_wing"},
            target=20,
            directive={"max_chassis_family_counts": {"courtyard": 1}},
        )

        self.assertEqual(caps["courtyard"], 1)
        self.assertEqual(caps["split_wing"], 12)

    def test_rebalance_one_for_two_recovers_valid_portfolio_without_relaxing_caps(self):
        def item(name, scope, score):
            return SimpleNamespace(
                name=name,
                scope=scope,
                principle_kind="base_operative",
                operation=f"op_{name}",
                score=score,
                seed=f"seed_{name}",
                section=f"section_{name}",
                roof=f"roof_{name}",
                chassis=f"chassis_{name}",
            )

        a = item("a", "1/1", 0.90)
        b = item("b", "1/2", 0.80)
        c = item("c", "1/1", 0.88)
        d = item("d", "1/1", 0.86)

        def silhouette(left, right):
            return 0.05 if {left.name, right.name} in ({"a", "c"}, {"a", "d"}) else 1.0

        with (
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda value: value.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda value: value.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda value: value.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda value: value.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda value: value.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", return_value={
                "phenotype": "prismatic", "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", side_effect=silhouette),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda value: {
                "ground_strategy": "direct_edge",
                "concept_key": value.name,
                "frontage_aligned": False,
            }),
        ):
            result = portfolio_benchmark._rebalance_measured_morphologies(
                [a, b],
                [a, b, c, d],
                target=3,
                visual_directive={},
            )

        self.assertEqual({value.name for value in result}, {"b", "c", "d"})

    def test_clean_mass_gate_rejects_two_large_disconnected_mesh_components(self):
        source = SimpleNamespace(
            volumes=(object(),),
            metadata={
                "geometry_program_bridge_evidence": {"program_hash": "recursive"},
                "geometry_program_compilation": {"metrics": {
                    "component_count": 2,
                    "minimum_component_volume_ratio": 0.5,
                }},
            },
            signature=lambda: {
                "surface_count": 20,
                "effective_surface_count": 12,
                "continuous_surface_evidence": {"hard_pass": True},
            },
        )

        hard_pass, evidence = portfolio_benchmark._clean_mass_gate(source)

        self.assertFalse(hard_pass)
        self.assertIn("disconnected_mesh_component_count", evidence["failure_reasons"])
        self.assertEqual(evidence["mesh_component_count"], 2)

    def test_clean_mass_gate_treats_law_derived_floor_bands_as_one_building(self):
        source = SimpleNamespace(
            volumes=tuple(object() for _ in range(6)),
            metadata={
                "geometry_program_bridge_evidence": {"program_hash": "recursive"},
                "geometry_program_compilation": {"metrics": {
                    "component_count": 1,
                    "minimum_component_volume_ratio": 1.0,
                }},
                "floorwise_legal_matrix_stack": {
                    "status": "materialized",
                    "floor_count": 6,
                },
            },
            signature=lambda: {
                "surface_count": 24,
                "effective_surface_count": 12,
                "continuous_surface_evidence": {"hard_pass": False},
            },
        )

        hard_pass, evidence = portfolio_benchmark._clean_mass_gate(source)

        self.assertTrue(hard_pass, evidence)
        self.assertNotIn("visible_volume_count", evidence["failure_reasons"])
        self.assertEqual(evidence["floor_band_count"], 6)
        self.assertEqual(evidence["visible_component_count"], 1)

    def test_registry_reconciles_all_pages_and_principle_groups(self):
        registry = build_book_language_registry()

        self.assertEqual(registry["page_count"], 69)
        self.assertEqual(registry["base_volume_count"], 6)
        self.assertEqual([item["label"] for item in registry["base_volumes"]], [
            "1/1 Base Volume", "3/8 Base Volume", "1/2 Base Volume",
            "1/4 Base Volume", "1/8 Base Volume", "1/16 Base Volume",
        ])
        self.assertEqual(len(registry["pages"]), 69)
        self.assertEqual(registry["base_operative_count"], 30)
        self.assertEqual(registry["combination_count"], 20)
        self.assertEqual(registry["aggregation_recipe_count"], 9)
        self.assertEqual(registry["case_study_count"], 10)
        self.assertEqual(registry["executable_principle_count"], 69)
        self.assertEqual(registry["operative_page_variation_count"], 11)
        self.assertEqual(registry["operative_orientation_count"], 3)
        self.assertEqual([page["page"] for page in registry["pages"]], list(range(1, 70)))
        self.assertTrue(all(page["sha256"] for page in registry["pages"]))
        self.assertEqual(len(registry["taxonomy"]["operations"]["add"]["single"]), 3)
        self.assertEqual(len(registry["taxonomy"]["operations"]["add"]["multiple"]), 4)
        self.assertEqual(len(registry["taxonomy"]["operations"]["displace"]["single"]), 4)
        self.assertEqual(len(registry["taxonomy"]["operations"]["displace"]["multiple"]), 7)
        self.assertEqual(len(registry["taxonomy"]["operations"]["subtract"]["single"]), 8)
        self.assertEqual(len(registry["taxonomy"]["operations"]["subtract"]["multiple"]), 4)
        self.assertEqual(len(registry["pages"][2]["principle_ids"]), 6)

    def test_disk_corpus_matches_typed_registry_and_ocr_provenance(self):
        audit = audit_book_corpus()

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(audit["scan_page_count"], 69)
        self.assertEqual(audit["ocr_page_count"], 69)
        self.assertEqual(audit["registry_page_count"], 69)
        self.assertEqual(audit["principle_count"], 69)
        self.assertEqual(
            audit["unreferenced_source_pages"],
            [1, 2, 4, 5, 13, 25, 38, 49, 59],
        )

    def test_taxonomy_continuation_pages_are_not_mislabeled_as_operatives(self):
        pages = {item["page"]: item for item in build_book_language_registry()["pages"]}

        self.assertEqual(pages[13]["section"], "operative_index")
        self.assertEqual(pages[25]["section"], "operative_index")
        self.assertEqual(pages[12]["section"], "base_operative")
        self.assertEqual(pages[14]["section"], "base_operative")
        self.assertEqual(pages[26]["section"], "base_operative")

    def test_every_base_operative_preserves_book_procedure_and_variation_semantics(self):
        base = [item for item in build_book_language_registry()["principles"] if item["kind"] == "base_operative"]

        self.assertEqual(len(base), 30)
        self.assertTrue(all(len(item["semantics"]["procedure"]) == 3 for item in base))
        self.assertTrue(all(item["semantics"]["variation_parameters"] for item in base))
        self.assertTrue(all(item["semantics"]["base_volume_fractions"] == ["1/1", "3/8", "1/2", "1/4", "1/8", "1/16"] for item in base))
        self.assertTrue(all(item["source_diagram_contract"]["procedure_step_count"] == 3 for item in base))
        self.assertTrue(all(item["source_diagram_contract"]["variation_count"] == 11 for item in base))
        self.assertTrue(all(item["source_diagram_contract"]["orientations"] == ["long_axis", "short_axis", "vertical"] for item in base))
        self.assertEqual(next(item for item in base if item["label"] == "bend")["semantics"]["output_topology"], "single_bent_volume")
        self.assertEqual(next(item for item in base if item["label"] == "merge")["semantics"]["output_topology"], "single_fused_volume")

    def test_case_studies_preserve_the_books_combined_operations(self):
        cases = {item["page_refs"][0]: item for item in build_book_language_registry()["case_studies"]}

        self.assertEqual(cases[60]["verbs"], ["carve", "offset"])
        self.assertEqual(cases[61]["verbs"], ["embed", "branch"])
        self.assertEqual(cases[63]["verbs"], ["expand", "nest"])
        self.assertEqual(cases[69]["verbs"], ["overlap", "rotate"])
        self.assertEqual(cases[60]["implementation_elements"], [
            "Offset Program", "Perimeter Services", "Punctured Openings",
        ])
        self.assertEqual(cases[69]["implementation_elements"], [
            "Rotated Volumes", "Stacked Utility and Circulation Cores", "Plinth and Street Facade",
        ])
        self.assertTrue(all(item["generation_stage"] == "case_study" for item in cases.values()))

    def test_book_aggregation_display_and_execution_orders_are_both_preserved(self):
        aggregations = [item for item in build_book_language_registry()["principles"] if item["kind"] == "aggregation"]
        reflect_expand = next(item for item in aggregations if item["label"].startswith("reflect"))

        self.assertEqual(reflect_expand["verbs"], ["reflect", "expand"])
        self.assertEqual(reflect_expand["execution_verbs"], ["expand", "reflect"])

    def test_page_count_and_executable_taxonomy_are_independently_accounted(self):
        registry = build_book_language_registry()
        principles = registry["principles"]

        self.assertEqual(len([item for item in principles if item["kind"] == "base_operative"]), 30)
        self.assertEqual(len([item for item in principles if item["kind"] == "combination"]), 20)
        self.assertEqual(len([item for item in principles if item["kind"] == "aggregation"]), 9)
        self.assertEqual(len([item for item in principles if item["kind"] == "case_study"]), 10)
        self.assertEqual(len(registry["case_studies"]), 10)
        self.assertEqual(registry["executable_principle_count"], len(principles))

    def test_compile_evidence_is_required_for_active_status(self):
        principle_id = "book:operative:expand"
        typed = build_book_language_registry()["principles"]
        active = build_book_language_registry({
            principle_id: {"compile_passed": True, "hard_pass": True, "geometry_delta": 0.12},
        })["principles"]

        self.assertEqual(next(item for item in typed if item["principle_id"] == principle_id)["status"], "typed")
        self.assertEqual(next(item for item in active if item["principle_id"] == principle_id)["status"], "active")

    def test_base_operative_vocabulary_is_exact(self):
        self.assertEqual(len(book_base_verbs()), 30)
        self.assertIn("inflate", book_base_verbs())
        self.assertIn("rotate", book_base_verbs())
        self.assertIn("puncture", book_base_verbs())
        self.assertEqual(BOOK_BASE_VERBS, set(book_base_verbs()))
        self.assertTrue(BOOK_BASE_VERBS.issubset(SUPPORTED_VERBS))

    def test_every_base_operative_has_multi_site_compile_evidence(self):
        registry = audited_book_language_registry()
        base = [item for item in registry["principles"] if item["kind"] == "base_operative"]

        self.assertEqual(len(base), 30)
        self.assertTrue(all(item["compile_evidence"]["compile_pass_count"] == 4 for item in base))
        self.assertTrue(all(item["status"] == "active" for item in base))
        self.assertTrue(all(item["compile_evidence"]["clean_pass_count"] == 4 for item in base))

    def test_all_book_operations_combinations_aggregations_and_cases_have_clean_execution_evidence(self):
        registry = audited_book_language_registry()

        self.assertEqual(len(registry["principles"]), 69)
        self.assertTrue(all(item["status"] == "active" for item in registry["principles"]))
        self.assertTrue(all(item["compile_evidence"]["clean_pass_count"] == 4 for item in registry["principles"]))
