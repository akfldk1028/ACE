"""Regression contracts for the recursive solid geometry language."""

import os
import json
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from shapely.errors import GEOSException
from django.test import SimpleTestCase
from shapely.geometry import Polygon, box

from design.maas.geometry_language import source_bridge as source_bridge_module

from design.maas.geometry_language import (
    BOOK_KERNEL_PARAMETER_PROJECTIONS,
    BOOK_RELATION_INVARIANTS,
    GeometryEdit,
    GeometryOutcomeGraph,
    GeometryProgramBuilder,
    TYPOLOGY_PRIORS,
    apply_book_projection_to_geometry_program,
    apply_geometry_edits,
    apply_geometry_edits_compiler_safe,
    audit_reference_matches_for_massing,
    architectural_shape_programs,
    base_seed_programs,
    box_derived_base_seed_programs,
    build_geometry_graph_notes,
    build_geometry_graph_snapshot,
    compilation_gate,
    compile_geometry_program,
    compile_geometry_program_to_source_mass,
    geometry_equivalent,
    geometry_programs_from_author_payload,
    l_mass_difference_program,
    openai_vlm_geometry_critic,
    parse_geometry_dsl,
    program_cost,
    project_program_requirements,
    project_book_parameter,
    reference_language_programs,
    recursive_book_projection_evidence,
    replace_source_dominant_with_geometry_program,
    retrieve_geometry_reference_matches,
    run_geometry_program_a2a_loop,
    score_geometry_program_with_openai_vlm,
    synthesize_architectural_programs,
    synthesis_requests_from_program_profile,
)
from design.maas.geometry_language.mutation import (
    BOOLEAN_PARAMETERS,
    OPERATOR_PARAMETER_CONTRACTS,
)
from design.maas.geometry_language import llm_adapter as geometry_llm_adapter
from design.maas.geometry_language import synthesis as geometry_synthesis
from design.maas.geometry_language import vlm_adapter as geometry_vlm_adapter
from design.maas.book_language.registry import build_book_language_registry
from design.maas.book_language.corpus_contract import BASE_OPERATIVES
from design.maas.geometry_language.base_volume_audit import audit_book_base_volumes
from design.maas.geometry_language.base_volume_host_audit import audit_book_base_volumes_across_hosts
from design.maas.geometry_language.universal_form_bank import universal_form_programs
from design.maas.geometry_language.typology_audit import audit_typology_priors
from design.maas.geometry_language.operative_audit import audit_book_operatives
from design.maas.geometry_language.page_audit import audit_book_pages
from design.maas.geometry_language.book_lowering_contract import BOOK_OPERATIVE_LOWERING
from design.maas.language_system import build_language_system_manifest
from design.maas.book_language.downstream_hard_gate import LegalGenerationContext
from design.maas.book_language.capacity_contract import (
    build_feasible_capacity_contract,
    recursive_plan_coverage_floor,
)
from design.maas.book_language.portfolio_benchmark import (
    _architectural_articulation_metrics,
    _audited_final_book_references,
    _chassis_family,
    _design_concept_descriptor,
    _program_dimensional_context,
    _program_form_gate,
    _reference_language_author_context,
    _site_access_side_in_principal_frame,
    _solid_morphology_metrics,
)
from design.maas.book_language.lineage import staged_principle_schedule
from design.maas.book_language.variation_lattice import book_probe_scope
from design.maas.program_massing import (
    book_operation_variants,
    book_sentence_variants,
    book_variation_indices,
    compose_program_with_book_operations,
    program_reference_contract,
    program_seed_sequences,
)
from design.maas.preference.vlm_scorer import _normalize_vlm_result, _prompt_text
from design.maas.preference import loop as preference_loop
from design.maas.source_geometry.compiler import compile_sequence_to_source_mass


class MaasGeometryLanguageTest(SimpleTestCase):
    def test_book_stack_upper_ratio_controls_executable_setback_geometry(self):
        base = base_seed_programs()[2]
        seed = program_seed_sequences("neighborhood_living")[0]
        stack = book_sentence_variants(("stack",), count=1)[0][0]

        def projected(upper_ratio: float):
            call = replace(stack, params={
                **stack.params,
                "levels": 3,
                "upper_ratio": upper_ratio,
                "lower_floor_fraction": 0.30,
            })
            sequence = compose_program_with_book_operations(
                seed,
                (call,),
                base_volume_label="1/1",
                orientation="long_axis",
            )
            return apply_book_projection_to_geometry_program(base, sequence)

        broad_top = projected(0.72)
        narrow_top = projected(0.36)
        broad_node = next(node for node in broad_top.nodes if node.operator == "stepped_mass")
        narrow_node = next(node for node in narrow_top.nodes if node.operator == "stepped_mass")

        self.assertAlmostEqual(broad_node.parameters["setback_ratio"], 0.14)
        self.assertAlmostEqual(narrow_node.parameters["setback_ratio"], 0.32)
        self.assertNotEqual(broad_top.program_hash(), narrow_top.program_hash())
        self.assertNotEqual(
            compile_geometry_program(broad_top).geometry_hash,
            compile_geometry_program(narrow_top).geometry_hash,
        )

    def test_language_system_starts_with_book_base_models_and_explicit_edges(self):
        manifest = build_language_system_manifest()
        graph = manifest["exploration_graph"]

        self.assertEqual(manifest["schema_version"], "arr.maas.language_system.v3")
        self.assertEqual(graph["schema_version"], "arr.maas.book_exploration_graph.v1")
        self.assertEqual(graph["counts"]["base_model_count"], 1)
        self.assertEqual(graph["counts"]["derived_volume_count"], 5)
        self.assertEqual(graph["counts"]["operation_count"], 30)
        self.assertEqual(graph["counts"]["combination_count"], 20)
        self.assertEqual(graph["counts"]["aggregation_count"], 9)
        self.assertEqual(graph["counts"]["case_study_evidence_count"], 10)
        self.assertEqual(graph["counts"]["book_page_evidence_count"], 69)
        self.assertEqual(len(manifest["axes"]["base_volumes"]), 6)
        self.assertEqual(len(manifest["axes"]["base_seeds"]), 5)
        self.assertEqual(len(manifest["axes"]["chassis"]), 11)
        self.assertEqual(len(manifest["axes"]["principles"]), 69)
        self.assertEqual(len(manifest["axes"]["programs"]), 7)
        self.assertEqual(len(manifest["axes"]["capacity_alternatives"]), 4)
        self.assertEqual(manifest["counts"]["universal_form_programs"], 82)
        self.assertEqual(manifest["semantic_order"][:6], [
            "base_model", "derived_volume", "orientation", "operation_family", "cardinality", "book_operation",
        ])
        self.assertFalse(manifest["form_bank_contract"]["program_conditioned"])
        self.assertEqual(
            manifest["semantic_order"][8:11],
            ["program", "capacity_alternative", "hard_gates"],
        )
        self.assertEqual(
            manifest["form_bank_contract"]["vlm_role"],
            "post_program_typed_critic_and_repair",
        )
        self.assertTrue(manifest["compatibility_contract"]["exploration_graph_edges_are_authoritative"])
        self.assertTrue(graph["contracts"]["base_seed_and_chassis_are_detail_only"])
        node_by_id = {node["id"]: node for node in graph["nodes"]}
        self.assertTrue(all(node_by_id[node_id]["kind"] == "base_model" for node_id in graph["root_node_ids"]))
        self.assertFalse(any(
            edge["scope"] == "execution" and node_by_id[edge["source"]]["kind"] == "source_page"
            for edge in graph["edges"]
        ))

    def test_all_base_volume_choices_transfer_across_all_five_host_proportions(self):
        audit = audit_book_base_volumes_across_hosts()
        audit.pop("_compilations", None)

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(audit["compile_count"], 90)
        self.assertEqual(audit["exact_box_host_count"], 4)
        self.assertTrue(all(row["component_count"] == 1 for row in audit["rows"]))
        slab_whole = [
            row for row in audit["rows"]
            if row["base_seed"] == "slab" and row["base_volume"] == "1/1"
        ]
        self.assertEqual(len(slab_whole), 3)
        self.assertTrue(all(row["measured_host_fraction"] == 1.0 for row in slab_whole))

    def test_book_kernel_projection_uses_schema_bounds_not_inline_remaps(self):
        for (verb, source_parameter), contract in BOOK_KERNEL_PARAMETER_PROJECTIONS.items():
            source_low, source_high = contract.source_bounds
            target_low, target_high = contract.kernel_bounds
            self.assertEqual(
                project_book_parameter(verb, source_parameter, source_low),
                target_low,
            )
            self.assertEqual(
                project_book_parameter(verb, source_parameter, source_high),
                target_high,
            )
            midpoint = project_book_parameter(
                verb, source_parameter, (source_low + source_high) / 2.0
            )
            self.assertAlmostEqual(midpoint, (target_low + target_high) / 2.0)
            self.assertTrue(contract.measurement_basis.startswith("selected_live_solid"))

    def test_shift_relation_records_live_volume_projection_and_neutral_section(self):
        base = base_seed_programs()[2]
        seed = program_seed_sequences("gymnasium")[0]
        shift = book_operation_variants("shift", count=11)[7]
        sequence = compose_program_with_book_operations(
            seed,
            (shift,),
            base_volume_label="1/4",
            orientation="short_axis",
        )
        program = apply_book_projection_to_geometry_program(base, sequence)
        node = next(item for item in program.nodes if item.operator == "shift_related")

        self.assertEqual(
            node.parameters["distance_ratio"],
            project_book_parameter(
                "shift", "distance_ratio", shift.params["distance_ratio"]
            ),
        )
        self.assertEqual(
            node.parameters["split_ratio"],
            BOOK_RELATION_INVARIANTS[("shift", "split_ratio")].value,
        )
        evidence = program.metadata["book_recursive_projection"]["parameter_projection"]
        self.assertEqual(
            evidence["coordinate_system"],
            "selected_live_solid_normalized_bounds",
        )
        self.assertEqual(evidence["projections"][0]["measurement_basis"],
                         "selected_live_solid_axis_span")
        self.assertEqual(evidence["relation_invariants"][0]["kernel_parameter"],
                         "split_ratio")
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_book_kernel_macros_expose_every_executed_parameter_to_graph_editors(self):
        self.assertTrue({"axis", "gap_ratio", "unit_scale"}.issubset(
            OPERATOR_PARAMETER_CONTRACTS["merge_related"]
        ))
        self.assertTrue({"axis", "distance_ratio", "unit_scale", "outward_sign"}.issubset(
            OPERATOR_PARAMETER_CONTRACTS["offset_related"]
        ))
        self.assertTrue({"axis", "angle_degrees", "bar_ratio", "distance_ratio", "outward_sign"}.issubset(
            OPERATOR_PARAMETER_CONTRACTS["interlock_related"]
        ))
        self.assertTrue({"axis", "slab_ratio", "shift_ratio", "vertical_overlap", "outward_sign"}.issubset(
            OPERATOR_PARAMETER_CONTRACTS["overlap_related"]
        ))
        self.assertIn("spacing_ratio", OPERATOR_PARAMETER_CONTRACTS["puncture"])
        self.assertTrue({"layout", "connector_width_ratio"}.issubset(
            OPERATOR_PARAMETER_CONTRACTS["split_wing"]
        ))
        self.assertTrue({"podium_scale", "podium_height_ratio"}.issubset(
            OPERATOR_PARAMETER_CONTRACTS["stepped_mass"]
        ))

    def test_direct_author_contract_exposes_existing_plate_disc_operators(self):
        expected = {
            "matrix4": {"matrix4"},
            "circularize": {"segments"},
            "matrix_array": {"matrices", "require_connected"},
            "profile_sweep_3d": {"path", "require_connected"},
            "attach": {
                "host_face", "anchor", "guest_extent",
                "engagement", "rotation_degrees",
            },
            "bridge": {"height", "height_ratio", "width", "width_ratio"},
        }
        prompt = geometry_llm_adapter._author_prompt({
            "program": "neighborhood_living",
            "instruction": "author one executable spatial mass",
        }, 1)
        for operator, parameters in expected.items():
            self.assertIn(operator, prompt)
            self.assertTrue(
                parameters.issubset(OPERATOR_PARAMETER_CONTRACTS[operator])
            )
            self.assertIn(operator, geometry_vlm_adapter.OPERATOR_EFFECTS)
            self.assertIn(
                operator,
                geometry_llm_adapter._AUTHOR_BODY_RULE_FAMILIES,
            )

        self.assertIn("require_connected", BOOLEAN_PARAMETERS)
        self.assertEqual(
            geometry_llm_adapter._author_parameter_value_contract(
                "matrix4", "matrix4"
            )["type"],
            "structured_literal",
        )
        self.assertEqual(
            geometry_llm_adapter._author_parameter_value_contract(
                "matrix_array", "matrices"
            )["type"],
            "structured_literal",
        )

    def test_book_operations_do_not_translate_in_world_or_seed_units(self):
        base = base_seed_programs()[2]
        seed = program_seed_sequences("gymnasium")[0]
        for verb in (item.verb for item in BASE_OPERATIVES):
            call = book_operation_variants(verb, count=1)[0]
            sequence = compose_program_with_book_operations(
                seed,
                (call,),
                base_volume_label="1/4",
                orientation="long_axis",
            )
            program = apply_book_projection_to_geometry_program(base, sequence)
            book_nodes = [
                node for node in program.nodes
                if node.provenance.get("source") == "book_recursive_projection"
            ]
            self.assertNotIn("translate", {node.operator for node in book_nodes}, verb)
            projection = program.metadata["book_recursive_projection"]
            self.assertEqual(
                projection["outward_direction_source"],
                "oriented_p3_cell_volume_weighted_center",
            )

    def test_book_vlm_capacity_floor_is_stage_aware(self):
        from design.maas.book_language.vlm_review import _final_book_vlm_hard_pass

        result = {
            "program_fit_hard_pass": True,
            "critic_actions": [],
            "concept_scores": {
                "gesture_clarity": 0.9,
                "hierarchy": 0.9,
                "repair_integrity": 0.9,
                "program_appropriateness": 0.9,
                "non_stair_silhouette": 0.9,
            },
        }
        base_pass, _ = _final_book_vlm_hard_pass(
            result,
            candidate_capacity={"feasible_capacity_utilization": 0.46},
            minimum_capacity_utilization=0.40,
        )
        final_pass, failures = _final_book_vlm_hard_pass(
            result,
            candidate_capacity={"feasible_capacity_utilization": 0.54},
            minimum_capacity_utilization=0.55,
        )

        self.assertTrue(base_pass)
        self.assertFalse(final_pass)
        self.assertIn("book_stage_feasible_capacity_below_competition_floor", failures)

    def test_book_vlm_review_budgets_are_cost_bounded_by_default_and_ceiling(self):
        from design.maas.book_language.vlm_review import _book_vlm_review_budget

        with patch.dict(os.environ, {
            "MAAS_BOOK_BASE_VLM_TOP_K": "",
            "MAAS_FINAL_BOOK_VLM_TOP_K": "",
        }):
            self.assertEqual(_book_vlm_review_budget("book_base_operative"), 8)
            self.assertEqual(_book_vlm_review_budget("final_book"), 12)
        with patch.dict(os.environ, {
            "MAAS_BOOK_BASE_VLM_TOP_K": "40",
            "MAAS_FINAL_BOOK_VLM_TOP_K": "80",
        }):
            self.assertEqual(_book_vlm_review_budget("book_base_operative"), 32)
            self.assertEqual(_book_vlm_review_budget("final_book"), 48)
        with patch.dict(os.environ, {"MAAS_FINAL_BOOK_VLM_TOP_K": "1"}):
            self.assertEqual(_book_vlm_review_budget("final_book"), 1)
        with patch.dict(os.environ, {"MAAS_FINAL_BOOK_VLM_TOP_K": "999"}):
            self.assertEqual(_book_vlm_review_budget("final_book"), 48)

    def test_one_shot_final_vlm_reviews_selector_winner_not_alphabetic_family(self):
        from design.maas.book_language.vlm_review import _final_book_vlm_shortlist

        selector_winner = object()
        with patch(
            "design.maas.book_language.vlm_review._select",
            return_value=[selector_winner],
        ) as selector:
            result = _final_book_vlm_shortlist(
                [object(), object()],
                target=1,
                visual_directive={"test": True},
            )

        self.assertEqual(result, [selector_winner])
        selector.assert_called_once()

    def test_one_shot_final_vlm_does_not_drop_a_hard_gate_pool_when_portfolio_selector_is_empty(self):
        from design.maas.book_language.vlm_review import _final_book_vlm_shortlist

        lower = SimpleNamespace(score=0.72)
        higher = SimpleNamespace(score=0.91)
        with patch(
            "design.maas.book_language.vlm_review._select",
            return_value=[],
        ):
            result = _final_book_vlm_shortlist(
                [lower, higher],
                target=1,
                visual_directive={},
            )

        self.assertEqual(result, [higher])

    def test_one_shot_final_vlm_prefers_typed_public_program_candidate_over_box_like_pack(self):
        from design.maas.book_language import vlm_review

        generic = SimpleNamespace(key="generic", score=0.95)
        architectural = SimpleNamespace(key="architectural", score=0.82)

        def descriptor(candidate):
            if candidate is architectural:
                return {
                    "frontage_aligned": True,
                    "open_voids": [{"node_id": "court"}],
                    "frontage_notches": [{"node_id": "entry"}],
                    "program_controller_node_ids": ["program"],
                    "section_controller_node_ids": ["section"],
                    "missing_required_concepts": [],
                    "ground_strategy": "frontage_open_court",
                }
            return {
                "frontage_aligned": False,
                "open_voids": [],
                "frontage_notches": [],
                "program_controller_node_ids": [],
                "section_controller_node_ids": [],
                "missing_required_concepts": ["concept:public_threshold"],
                "ground_strategy": "direct_edge",
            }

        with (
            patch.object(vlm_review, "_select", return_value=[generic]),
            patch.object(
                vlm_review,
                "_design_concept_descriptor",
                side_effect=descriptor,
            ),
            patch.object(
                vlm_review,
                "_solid_morphology_metrics",
                side_effect=lambda candidate: {
                    "phenotype": (
                        "voided" if candidate is architectural else "prismatic"
                    ),
                    "pyramidal_like": False,
                    "wedge_like": False,
                },
            ),
        ):
            result = vlm_review._final_book_vlm_shortlist(
                [generic, architectural],
                target=1,
                visual_directive={},
            )

        self.assertEqual(result, [architectural])

    def test_one_shot_final_vlm_skips_exact_geometry_already_rejected_by_critic(self):
        from design.maas.book_language.vlm_review import (
            _exclude_prior_final_book_vlm_failures,
        )

        def candidate(geometry_hash: str):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "geometry_program_bridge_evidence": {
                    "geometry_hash": geometry_hash,
                },
            }))

        rejected = candidate("geometry-rejected")
        fresh = candidate("geometry-fresh")
        graph = SimpleNamespace(
            failed_final_book_geometry_hashes=lambda program_slug: (
                {"geometry-rejected"} if program_slug == "neighborhood" else set()
            ),
        )

        filtered, evidence = _exclude_prior_final_book_vlm_failures(
            [rejected, fresh],
            outcome_graph=graph,
            program_slug="neighborhood",
        )

        self.assertEqual(filtered, [fresh])
        self.assertEqual(evidence["prior_exact_failure_count"], 1)
        self.assertEqual(evidence["remaining_candidate_count"], 1)

    def test_base_stage_vlm_releases_only_descendants_of_approved_exact_parent(self):
        from design.maas.book_language.candidate_analysis import _Candidate
        from design.maas.book_language.vlm_review import audit_book_base_stage_with_vlm

        @dataclass(frozen=True)
        class FakeSource:
            metadata: dict

        def candidate(stage: str, parent_key: str, principle: str):
            return _Candidate(
                principle,
                "base_operative" if stage == "base" else "combination",
                principle,
                program_seed_sequences("neighborhood_living")[0],
                FakeSource({
                    "book_generation_lineage": {
                        "stage": stage,
                        "parent_key": parent_key,
                    },
                }),
                {"properties": {}},
                0.7,
            )

        approved_base = candidate("base", "parent-approved", "book:operative:bend")
        approved_child = candidate("combination", "parent-approved", "book:combination:bend+bend")
        rejected_base = candidate("base", "parent-rejected", "book:operative:split")
        rejected_child = candidate("combination", "parent-rejected", "book:combination:split+split")
        audited_base = replace(
            approved_base,
            source=replace(approved_base.source, metadata={
                **approved_base.source.metadata,
                "final_book_vlm_audit": {
                    "hard_pass": True,
                    "response_id": "base-response",
                },
            }),
        )
        with (
            patch(
                "design.maas.book_language.vlm_review._book_base_parent_shortlist",
                return_value=([approved_base, rejected_base], {
                    "descendant_first_parent_resolution": True,
                }),
            ),
            patch(
                "design.maas.book_language.vlm_review._audit_final_book_geometry_with_vlm",
                return_value=([audited_base], {
                    "hard_pass_count": 1,
                    "audit_records": [
                        {"parent_key": "parent-approved"},
                        {"parent_key": "parent-rejected"},
                    ],
                }),
            ),
        ):
            released, evidence = audit_book_base_stage_with_vlm(
                [approved_base, approved_child, rejected_base, rejected_child],
                building_type="neighborhood_living",
                output_dir=Path("unused"),
                visual_directive={},
            )

        self.assertEqual(len(released), 2)
        self.assertEqual(
            {item.source.metadata["book_generation_lineage"]["parent_key"] for item in released},
            {"parent-approved"},
        )
        base = next(item for item in released if item.principle_kind == "base_operative")
        child = next(item for item in released if item.principle_kind == "combination")
        self.assertEqual(base.source.metadata["base_book_vlm_audit"]["review_stage"], "book_base_operative")
        self.assertTrue(child.source.metadata["base_book_vlm_parent_audit"]["hard_pass"])
        self.assertEqual(evidence["rejected_descendant_count"], 1)
        self.assertEqual(
            set(evidence["reviewed_parent_keys"]),
            {"parent-approved", "parent-rejected"},
        )

    def test_base_stage_vlm_replenishment_skips_previously_reviewed_parent(self):
        from design.maas.book_language.candidate_analysis import _Candidate
        from design.maas.book_language.vlm_review import (
            _base_review_fingerprint,
            audit_book_base_stage_with_vlm,
        )

        @dataclass(frozen=True)
        class FakeSource:
            metadata: dict

        def candidate(parent_key: str, geometry_hash: str | None = None):
            return _Candidate(
                parent_key,
                "base_operative",
                "book:operative:bend",
                program_seed_sequences("neighborhood_living")[0],
                FakeSource({
                    "book_generation_lineage": {
                        "stage": "base",
                        "parent_key": parent_key,
                    },
                    "geometry_program_compilation": {
                        "geometry_hash": geometry_hash or f"geometry-{parent_key}",
                    },
                }),
                {"properties": {}},
                0.7,
            )

        first = candidate("parent-first-batch", "same-first-geometry")
        regenerated_first = candidate(
            "parent-first-batch-regenerated",
            "same-first-geometry",
        )
        second = candidate("parent-second-batch")
        evidence_fingerprint = _base_review_fingerprint(first)
        audited_second = replace(
            second,
            source=replace(second.source, metadata={
                **second.source.metadata,
                "final_book_vlm_audit": {
                    "hard_pass": True,
                    "response_id": "second-response",
                },
            }),
        )
        with (
            patch(
                "design.maas.book_language.vlm_review._book_base_parent_shortlist",
                return_value=([second], {"descendant_first_parent_resolution": True}),
            ),
            patch(
                "design.maas.book_language.vlm_review._audit_final_book_geometry_with_vlm",
                return_value=([audited_second], {
                    "hard_pass_count": 1,
                    "audit_records": [{"parent_key": "parent-second-batch"}],
                }),
            ) as audit,
        ):
            released, evidence = audit_book_base_stage_with_vlm(
                [regenerated_first, second],
                building_type="neighborhood_living",
                output_dir=Path("unused"),
                visual_directive={},
                # The regenerated lineage has a new name but the compiled
                # base is identical to the first batch.
                excluded_parent_fingerprints={
                    evidence_fingerprint
                },
            )

        reviewed_bases = audit.call_args.args[0]
        self.assertEqual([item.principle_id for item in reviewed_bases], ["parent-second-batch"])
        self.assertEqual([item.principle_id for item in released], ["parent-second-batch"])
        self.assertEqual(evidence["excluded_parent_count"], 0)
        self.assertEqual(evidence["excluded_parent_fingerprint_count"], 1)

    def test_base_parent_shortlist_reserves_required_and_core_before_descendants(self):
        from design.maas.book_language.candidate_analysis import _Candidate
        from design.maas.book_language.vlm_review import _book_base_parent_shortlist

        @dataclass(frozen=True)
        class FakeSource:
            metadata: dict

        def candidate(
            name: str,
            family: str,
            *,
            stage: str,
            lane: str,
            score: float,
        ):
            return _Candidate(
                name,
                "base_operative" if stage == "base" else "combination",
                "book:operative:bend",
                program_seed_sequences("neighborhood_living")[0],
                FakeSource({
                    "book_generation_lineage": {
                        "stage": stage,
                        "parent_key": name.split("-child", 1)[0],
                    },
                    "geometry_program_bridge_evidence": {"status": "materialized"},
                    "geometry_program": {
                        "metadata": {
                            "family": family,
                            "form_bank_lane": lane,
                        },
                    },
                }),
                {"properties": {}},
                score,
            )

        split = candidate(
            "split-parent", "split_bridge", stage="base",
            lane="executable_core_language", score=0.1,
        )
        court = candidate(
            "court-parent", "courtyard", stage="base",
            lane="executable_core_language", score=0.2,
        )
        agent_bases = [
            candidate(
                f"agent-{index}", "agent_profiled_hall", stage="base",
                lane="bounded_synthesis", score=0.9 - index * 0.01,
            )
            for index in range(5)
        ]
        descendants = [
            candidate(
                f"agent-{index}-child", "agent_profiled_hall", stage="combination",
                lane="bounded_synthesis", score=1.0 - index * 0.01,
            )
            for index in range(5)
        ]
        with patch(
            "design.maas.book_language.vlm_review._final_book_vlm_shortlist",
            side_effect=lambda pool, **kwargs: list(pool)[:kwargs["target"]],
        ):
            shortlist, evidence = _book_base_parent_shortlist(
                [split, court, *agent_bases, *descendants],
                target=4,
                visual_directive={
                    "required_geometry_program_families": ["split_bridge"],
                },
            )

        self.assertEqual(len(shortlist), 4)
        self.assertIn("split-parent", [item.principle_id for item in shortlist])
        self.assertIn("court-parent", [item.principle_id for item in shortlist])
        self.assertEqual(evidence["base_anchor_target"], 2)
        self.assertEqual(evidence["executable_core_family_anchor_count"], 2)
        self.assertEqual(
            evidence["review_order"],
            "required_family_then_rare_chassis_then_core_alphabet_then_descendant_parent_then_fallback",
        )

    def test_base_vlm_memory_is_stage_and_contract_scoped(self):
        from design.maas.book_language.vlm_review import (
            _base_review_fingerprint,
            _book_vlm_review_contract,
        )

        source = SimpleNamespace(metadata={
            "book_generation_lineage": {
                "stage": "base",
                "parent_key": "parent-memory",
            },
            "geometry_program_compilation": {"geometry_hash": "exact-base-solid"},
        })
        candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="neighborhood-seed__book_bend"),
            principle_id="book:operative:bend",
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="site-a")
        fingerprint = _base_review_fingerprint(candidate)
        contract = _book_vlm_review_contract("book_base_operative")
        graph.observe_base_book_vlm_audit(
            program_slug="neighborhood",
            candidate=candidate,
            base_review_fingerprint=fingerprint,
            review_contract_fingerprint=contract["fingerprint"],
            audit={
                "hard_pass": True,
                "status": "pass",
                "model": contract["model"],
                "prompt_contract_version": contract["prompt_contract_version"],
                "review_contract_fingerprint": contract["fingerprint"],
                "response_id": "base-memory-response",
                "review_stage": "book_base_operative",
            },
        )

        approved = graph.approved_base_book_vlm_audits(
            program_slug="neighborhood",
            base_review_fingerprints=[fingerprint],
            review_contract_fingerprint=contract["fingerprint"],
        )
        self.assertEqual(approved[fingerprint]["response_id"], "base-memory-response")
        self.assertEqual(
            [item["stage"] for item in graph.observations],
            ["book_base_vlm"],
        )
        self.assertEqual(graph.approved_base_book_vlm_audits(
            program_slug="gymnasium",
            base_review_fingerprints=[fingerprint],
            review_contract_fingerprint=contract["fingerprint"],
        ), {})
        self.assertEqual(graph.approved_base_book_vlm_audits(
            program_slug="neighborhood",
            base_review_fingerprints=[fingerprint],
            review_contract_fingerprint="changed-prompt-or-policy",
        ), {})

    def test_base_stage_reuses_exact_graph_approval_without_calling_vlm(self):
        from design.maas.book_language.candidate_analysis import _Candidate
        from design.maas.book_language.vlm_review import (
            _base_review_fingerprint,
            _book_vlm_review_contract,
            audit_book_base_stage_with_vlm,
        )

        @dataclass(frozen=True)
        class FakeSource:
            metadata: dict

        def candidate(stage: str, principle: str):
            return _Candidate(
                principle,
                "base_operative" if stage == "base" else "combination",
                principle,
                program_seed_sequences("neighborhood_living")[0],
                FakeSource({
                    "book_generation_lineage": {
                        "stage": stage,
                        "parent_key": "stable-parent",
                    },
                    "geometry_program_compilation": {
                        "geometry_hash": "stable-exact-base",
                    },
                }),
                {"properties": {}},
                0.7,
            )

        base = candidate("base", "book:operative:bend")
        child = candidate("combination", "book:combination:bend+bend")
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="site-a")
        contract = _book_vlm_review_contract("book_base_operative")
        graph.observe_base_book_vlm_audit(
            program_slug="neighborhood",
            candidate=base,
            base_review_fingerprint=_base_review_fingerprint(base),
            review_contract_fingerprint=contract["fingerprint"],
            audit={
                "hard_pass": True,
                "status": "pass",
                "model": contract["model"],
                "prompt_contract_version": contract["prompt_contract_version"],
                "review_contract_fingerprint": contract["fingerprint"],
                "response_id": "persisted-response",
                "review_stage": "book_base_operative",
                "concept_scores": {"gesture_clarity": 0.8},
            },
        )
        with patch(
            "design.maas.book_language.vlm_review._audit_final_book_geometry_with_vlm"
        ) as audit:
            released, evidence = audit_book_base_stage_with_vlm(
                [base, child],
                building_type="neighborhood_living",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=graph,
                program_slug="neighborhood",
            )

        audit.assert_not_called()
        self.assertEqual(len(released), 2)
        self.assertEqual(evidence["persisted_approved_base_count"], 1)
        self.assertEqual(evidence["fresh_base_input_count"], 0)
        released_base = next(item for item in released if item.principle_kind == "base_operative")
        released_child = next(item for item in released if item.principle_kind == "combination")
        self.assertTrue(released_base.source.metadata["base_book_vlm_audit"]["reused_from_outcome_graph"])
        self.assertTrue(released_child.source.metadata["base_book_vlm_parent_audit"]["reused_from_outcome_graph"])

    def test_legacy_base_response_is_removed_from_final_learning_and_promoted(self):
        from design.maas.book_language.vlm_review import _book_vlm_review_contract

        source = SimpleNamespace(metadata={
            "geometry_program": {
                "name": "legacy-base",
                "metadata": {"pre_book_program_hash": "authored", "family": "split_bridge"},
                "nodes": [],
                "root_id": "",
            },
            "geometry_program_bridge_evidence": {
                "program_hash": "projected",
                "geometry_hash": "legacy-base-solid",
                "source_seed": "neighborhood-seed",
            },
            "program_book_projection_evidence": {
                "scope": {"base_volume_label": "1/2"},
            },
        })
        candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="neighborhood-seed__book_split"),
            principle_id="book:operative:split",
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="site-a")
        graph.observe_final_book_vlm_audit(
            program_slug="neighborhood",
            candidate=candidate,
            audit={
                "hard_pass": True,
                "failures": [],
                "model": "fake-vlm",
                "response_id": "known-base-response",
                "critic_actions": ["good_void"],
                "concept_scores": {"gesture_clarity": 0.8},
                "reviewed_exact_post_book_geometry": True,
            },
        )
        contract = _book_vlm_review_contract("book_base_operative")
        result = graph.migrate_legacy_base_book_vlm_observations(
            program_slug="neighborhood",
            critic_response_ids=["known-base-response"],
            review_contract=contract,
        )

        self.assertEqual(result, {
            "matched": 1,
            "promoted_hard_pass": 1,
            "relabelled": 1,
        })
        self.assertFalse(any(item.get("stage") == "final_book_vlm" for item in graph.observations))
        base_observation = next(
            item for item in graph.observations if item.get("stage") == "book_base_vlm"
        )
        approved = graph.approved_base_book_vlm_audits(
            program_slug="neighborhood",
            base_review_fingerprints=[base_observation["base_review_fingerprint"]],
            review_contract_fingerprint=contract["fingerprint"],
        )
        self.assertEqual(
            approved[base_observation["base_review_fingerprint"]]["response_id"],
            "known-base-response",
        )

    def test_feasible_capacity_contract_integrates_floorwise_legal_field(self):
        envelope = SimpleNamespace(bcr_limit=60.0, far_limit=250.0)
        context = LegalGenerationContext(
            envelope=envelope,
            generation_site=box(0, 0, 20, 10),
            sunlight_ring=(),
            evidence={},
        )
        contract = build_feasible_capacity_contract(
            context,
            site_local_utm=box(0, 0, 25, 20),
            height_m=15.0,
            floors=5,
        )

        # The 500 m2 parcel permits 300 m2 at grade by BCR, but the actual
        # legal host is only 200 m2. Five legal sections therefore carry
        # 1,000 m2, below the statutory 1,250 m2 FAR ceiling.
        self.assertEqual(contract["height_field_capacity_m2"], 1000.0)
        self.assertEqual(contract["far_capacity_m2"], 1250.0)
        self.assertEqual(contract["feasible_maximum_floor_area_m2"], 1000.0)
        self.assertEqual(contract["target_floor_area_m2"], 880.0)
        self.assertEqual(contract["target_base_plan_area_m2"], 176.0)
        self.assertEqual(contract["target_base_plan_coverage"], 0.88)

    def test_feasible_capacity_contract_applies_ground_bcr_before_far(self):
        envelope = SimpleNamespace(bcr_limit=40.0, far_limit=300.0)
        context = LegalGenerationContext(
            envelope=envelope,
            generation_site=box(0, 0, 30, 20),
            sunlight_ring=(),
            evidence={},
        )
        contract = build_feasible_capacity_contract(
            context,
            site_local_utm=box(0, 0, 25, 20),
            height_m=9.0,
            floors=3,
        )

        self.assertEqual(contract["bcr_adjusted_floor_areas_m2"], [200.0, 600.0, 600.0])
        self.assertEqual(contract["height_field_capacity_m2"], 1400.0)
        self.assertEqual(contract["feasible_maximum_floor_area_m2"], 1400.0)

    def test_recursive_book_schedule_emits_base_parent_before_every_descendant(self):
        principles = tuple(build_book_language_registry()["principles"])
        schedule = staged_principle_schedule(principles, 5, count=12)

        self.assertEqual(len(schedule), 12)
        positions = {
            str(principle["principle_id"]): position
            for position, (_index, principle) in enumerate(schedule)
        }
        descendants = [
            principle for _index, principle in schedule
            if principle["generation_stage"] != "base"
        ]
        self.assertTrue(descendants)
        for principle in descendants:
            parent_id = str(principle["lineage_parent_principle_id"])
            self.assertIn(parent_id, positions)
            self.assertLess(positions[parent_id], positions[str(principle["principle_id"])])

    def test_book_registry_records_causal_generation_lineage_for_all_69_principles(self):
        principles = tuple(build_book_language_registry()["principles"])
        by_id = {str(item["principle_id"]): item for item in principles}

        self.assertEqual(len(principles), 69)
        self.assertEqual(
            {str(item["generation_stage"]) for item in principles},
            {"base", "combination", "aggregation", "case_study"},
        )
        for principle in principles:
            base_id = str(principle["lineage_base_operative_id"])
            self.assertIn(base_id, by_id)
            self.assertEqual(by_id[base_id]["generation_stage"], "base")
            if principle["generation_stage"] == "base":
                self.assertIsNone(principle["lineage_parent_principle_id"])
            else:
                self.assertEqual(principle["lineage_parent_principle_id"], base_id)

    def test_lineage_gate_reports_rejected_descendants_by_exact_geometry_family(self):
        from design.maas.book_language.lineage import gate_descendants_by_base

        def candidate(stage: str, parent_key: str, family: str):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "book_generation_lineage": {"stage": stage, "parent_key": parent_key},
                "geometry_program": {"metadata": {"family": family}},
            }))

        retained, evidence = gate_descendants_by_base([
            candidate("base", "court-parent", "courtyard"),
            candidate("combination", "court-parent", "courtyard"),
            candidate("combination", "missing-split-parent", "split_bridge"),
        ])

        self.assertEqual(len(retained), 2)
        self.assertEqual(
            evidence["by_geometry_family"]["split_bridge"],
            {
                "input_base_count": 0,
                "input_descendant_count": 1,
                "retained_base_count": 0,
                "retained_descendant_count": 0,
                "rejected_descendant_without_viable_base_count": 1,
            },
        )

    def test_program_observation_records_actual_combined_program_gate(self):
        graph = GeometryOutcomeGraph(Path("unused-outcome-graph.json"), "test")
        program = base_seed_programs()[0]
        source = SimpleNamespace(metadata={
            "geometry_program": program.to_dict(),
            "geometry_program_bridge_evidence": {
                "program_hash": program.program_hash(),
                "geometry_hash": "geometry-hash",
                "source_seed": "program_seed",
            },
            "program_book_projection_evidence": {
                "scope": {"base_volume_label": "1/1"},
            },
        })

        graph.observe_program_evaluation(
            program_slug="neighborhood",
            source=source,
            sequence_name="program_seed__book_test",
            principle_id="book:operative:shift",
            spatial={"role_coverage_score": 1.0},
            failed_gates=(),
            program_hard_pass=False,
            program_evidence={
                "volume_count": 6,
                "volume_fit": 0.16,
                "program_fit_score": 0.71,
            },
        )

        observation = graph.observations[-1]
        self.assertFalse(observation["program_hard_pass"])
        self.assertEqual(observation["failed_program_gates"], ["program_massing"])
        self.assertEqual(observation["program_massing_metrics"]["volume_count"], 6)

    def test_final_constraint_solver_escapes_greedy_compatibility_trap(self):
        from design.maas.book_language.portfolio_constraint_solver import (
            ConstraintCandidateFacts,
            solve_maximum_compatible_subset,
        )

        facts = [
            ConstraintCandidateFacts(0.99, ("family:dominant",), ("scope:1/1",)),
            ConstraintCandidateFacts(0.91, ("family:a",), ("scope:1/1",)),
            ConstraintCandidateFacts(0.90, ("family:b",), ("scope:1/2",)),
            ConstraintCandidateFacts(0.89, ("family:c",), ("scope:1/4",)),
        ]
        compatibility = [[True] * 4 for _ in range(4)]
        for other in (1, 2, 3):
            compatibility[0][other] = False
            compatibility[other][0] = False

        selected = solve_maximum_compatible_subset(
            facts,
            compatibility,
            target_count=3,
            maximum_key_counts={key: 1 for fact in facts for key in fact.cap_keys},
            required_coverage_tags=("scope:1/1", "scope:1/2", "scope:1/4"),
        )

        self.assertEqual(set(selected), {1, 2, 3})

    def test_chassis_family_uses_executable_topology_not_only_base_seed(self):
        def candidate(operator: str):
            program = parse_geometry_dsl(
                "mass base = box(2.2, 1.45, 0.28)\n"
                f"mass result = {operator}(base, "
                + (
                    "axis='x', gap_ratio=0.16, bridge=True, access_side='west')"
                    if operator == "split_wing"
                    else "axis='x', angle_degrees=28, subdivisions=4)"
                ),
                name=f"slab_{operator}",
            )
            program = replace(program, metadata={
                **program.metadata,
                "family": f"agent_{operator}",
                "base_seed": "slab",
            })
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "geometry_program_bridge_evidence": {"status": "materialized"},
                "geometry_program": program.to_dict(),
            }))

        self.assertEqual(
            _chassis_family(candidate("split_wing")),
            "recursive_chassis:split_wing",
        )
        self.assertEqual(
            _chassis_family(candidate("bend")),
            "recursive_chassis:bent_bar",
        )

    def test_executable_core_form_bank_has_typed_base_seed_and_chassis(self):
        core = [
            program for program in universal_form_programs()
            if program.metadata.get("form_bank_lane") == "executable_core_language"
        ]

        self.assertEqual(len(core), 18)
        self.assertNotIn("unknown", {program.metadata.get("base_seed") for program in core})
        self.assertNotIn("unclassified", {program.metadata.get("chassis") for program in core})
        by_family = {program.metadata["family"]: program.metadata for program in core}
        self.assertEqual(by_family["u_mass"]["chassis"], "u_court")
        self.assertEqual(by_family["overlapping_mass"]["chassis"], "overlapping_bars")
        self.assertEqual(by_family["split_bridge"]["base_seed"], "slab")
        self.assertEqual(by_family["swept_bar"]["chassis"], "curved_bar")

    def test_llm_author_schema_restricts_base_seed_to_program_profile_allow_list(self):
        schema = geometry_llm_adapter._author_schema(
            3,
            allowed_base_seeds=geometry_llm_adapter._allowed_author_base_seeds({
                "base_seeds": ["bar", "slab", "unknown", "bar"],
            }),
        )
        base_seed_schema = schema["properties"]["programs"]["items"]["properties"]["base_seed"]

        self.assertEqual(base_seed_schema["enum"], ["bar", "slab"])
        self.assertNotIn("tower", base_seed_schema["enum"])

    def test_llm_author_schema_encodes_node_arity_by_kind_and_operator(self):
        schema = geometry_llm_adapter._author_schema(2)
        node_schema = schema["properties"]["programs"]["items"]["properties"]["nodes"]["items"]
        variants = node_schema["anyOf"]

        union = next(
            item for item in variants
            if item["properties"]["kind"]["enum"] == ["boolean"]
            and "union" in item["properties"]["operator"]["enum"]
        )
        transform = next(
            item for item in variants
            if item["properties"]["kind"]["enum"] == ["transform"]
        )
        bridge = next(
            item for item in variants
            if item["properties"]["kind"]["enum"] == ["composition"]
            and item["properties"]["operator"]["enum"] == ["bridge"]
        )

        self.assertEqual(union["properties"]["inputs"]["minItems"], 2)
        self.assertEqual(transform["properties"]["inputs"]["minItems"], 1)
        self.assertEqual(transform["properties"]["inputs"]["maxItems"], 1)
        self.assertEqual(bridge["properties"]["inputs"]["minItems"], 2)
        self.assertEqual(bridge["properties"]["inputs"]["maxItems"], 2)

    def test_llm_author_schema_is_program_conditioned_without_completed_form_templates(self):
        neighborhood_context = {
            "program_context": program_reference_contract("neighborhood_living"),
        }
        gym_context = {
            "program_context": program_reference_contract("gymnasium"),
        }
        neighborhood_operators = geometry_llm_adapter._allowed_author_operators(neighborhood_context)
        gym_operators = geometry_llm_adapter._allowed_author_operators(gym_context)

        self.assertNotIn("profiled_hall", neighborhood_operators)
        self.assertNotIn("leaning_tower", neighborhood_operators)
        self.assertIn("courtyard", neighborhood_operators)
        self.assertIn("profiled_hall", gym_operators)
        self.assertNotIn("split_wing", gym_operators)
        self.assertIsNone(neighborhood_context["program_context"]["geometry_template"])

    def test_llm_author_prompt_uses_current_program_roles_not_generic_hall_roles(self):
        prompt = geometry_llm_adapter._author_prompt({
            "building_type": "neighborhood_living",
            "program_context": program_reference_contract("neighborhood_living"),
            "base_seeds": ["bar", "slab", "block"],
            "maximum_operator_depth": 2,
            "downstream_body_rule_reserve": 1,
        }, 4)

        self.assertIn("public_ground_edge", prompt)
        self.assertIn("street_access", prompt)
        self.assertIn("Never append a fake result", prompt)
        self.assertIn("allowed macro list", prompt)

    def test_llm_author_recognizes_program_invariant_roles_as_access_relations(self):
        context = {
            **program_reference_contract("neighborhood_living"),
            "site_access_side_in_program_frame": "west",
        }
        court = parse_geometry_dsl(
            "mass base = box(12, 8, 5)\n"
            "mass result = carve_void(base, margin_ratio=0.22, open_side='west')",
            name="program_void_role",
        )
        court = court.with_nodes(
            replace(node, semantic_role="void_or_terrace")
            if node.id == "result" else node
            for node in court.nodes
        )
        threshold = parse_geometry_dsl(
            "mass base = box(12, 8, 5)\n"
            "mass result = notch(base, side='west', ratio=0.2)",
            name="program_street_access_role",
        )
        threshold = threshold.with_nodes(
            replace(node, semantic_role="street_access")
            if node.id == "result" else node
            for node in threshold.nodes
        )

        self.assertTrue(geometry_llm_adapter._is_program_relation_node(court.node_map["result"]))
        self.assertTrue(geometry_llm_adapter._is_program_relation_node(threshold.node_map["result"]))
        self.assertEqual(geometry_llm_adapter._misaligned_access_relation(court, context), "")
        self.assertEqual(geometry_llm_adapter._misaligned_access_relation(threshold, context), "")

    def test_relational_wing_operators_prefer_longitudinal_base_seed(self):
        for operator in ("cross_mass", "split_wing", "bent_bar"):
            seed = geometry_synthesis._base_seed_for_operator(
                operator,
                ("block", "slab", "bar", "profiled_prism"),
                cursor=0,
                palette_size=4,
                intent_tags=("distributed_wings",),
            )
            self.assertEqual(seed, "bar", operator)
            self.assertNotIn("block", geometry_llm_adapter.SEMANTIC_MACRO_BASE_SEEDS[operator])

    def test_program_contract_rejects_open_court_after_repeated_plan_relation(self):
        context = {
            **program_reference_contract("neighborhood_living"),
            "site_access_side_in_program_frame": "west",
        }
        fragmented = parse_geometry_dsl(
            "mass base = box(2.8, 0.62, 0.48)\n"
            "mass body = cross_mass(base, angle_degrees=82)\n"
            "mass result = carve_void(body, margin_ratio=0.3, open_side='west')",
            name="fragmenting_cross_open_court",
        )
        coherent = parse_geometry_dsl(
            "mass base = box(2.8, 0.62, 0.48)\n"
            "mass body = cross_mass(base, angle_degrees=82)\n"
            "mass result = lift(body, rise_ratio=0.2, support_ratio=0.12, access_side='west')",
            name="coherent_cross_lift",
        )

        self.assertIn(
            "fragments_repeated_plan_use_lift_or_side_notch",
            geometry_llm_adapter._program_language_contract_issue(fragmented, context),
        )
        self.assertEqual(
            geometry_llm_adapter._program_language_contract_issue(coherent, context),
            "",
        )

    def test_neighborhood_recursive_fit_uses_legal_host_at_architectural_scale(self):
        self.assertEqual(recursive_plan_coverage_floor("neighborhood_living"), 0.0)
        self.assertEqual(recursive_plan_coverage_floor("gymnasium"), 0.0)
        self.assertEqual(
            recursive_plan_coverage_floor(
                "neighborhood_living",
                {"target_base_plan_area_m2": 120.0},
                host_area_m2=200.0,
            ),
            0.6,
        )

        host = Polygon(((0, 0), (30, 0), (30, 20), (0, 20)))
        source = compile_sequence_to_source_mass(
            host,
            program_seed_sequences("neighborhood_living")[0],
        )
        self.assertIsNotNone(source)
        assert source is not None
        program = parse_geometry_dsl(
            "mass base = box(2.8, 0.62, 0.48)\n"
            "mass body = bent_bar(base, axis='x', angle_degrees=32, subdivisions=4)\n"
            "mass result = notch(body, side='west', ratio=0.2)",
            name="architectural_scale_bent_bar",
        )
        composed = replace_source_dominant_with_geometry_program(
            source,
            program,
            containment_host=host,
            minimum_host_plan_coverage=0.58,
        )
        self.assertIsNotNone(composed)
        assert composed is not None
        integration = composed.metadata["program_role_integration_evidence"]
        self.assertEqual(integration["minimum_host_plan_coverage"], 0.58)
        self.assertGreaterEqual(
            integration["recursive_target_plan_area_m2"],
            round(host.area * 0.58, 4),
        )
        self.assertTrue(all(host.buffer(1e-7).covers(volume.footprint) for volume in composed.volumes))

    def test_program_geometry_contract_requires_access_relation_and_rejects_wrong_typology_macro(self):
        context = program_reference_contract("neighborhood_living")
        plain = parse_geometry_dsl("mass result = box(10, 8, 5)", name="plain_neighborhood")
        self.assertEqual(
            geometry_llm_adapter._misaligned_access_relation(plain, context),
            "program:missing_access_bound_relation",
        )
        hall = parse_geometry_dsl(
            "mass base = box(10, 8, 5)\n"
            "mass result = profiled_hall(base, section_family='ridge', span_axis='x')",
            name="wrong_neighborhood_hall",
        )
        self.assertIn(
            "not_allowed_for_program",
            geometry_llm_adapter._program_language_contract_issue(hall, context),
        )

    def test_llm_author_contract_matches_downstream_body_and_threshold_rule_budget(self):
        context = {
            **program_reference_contract("neighborhood_living"),
            "site_access_side_in_program_frame": "west",
            "author_maximum_body_rule_count": 2,
            "author_maximum_public_threshold_rule_count": 1,
        }
        overloaded = parse_geometry_dsl(
            "mass base = box(10, 8, 5)\n"
            "mass lifted = lift(base, rise_ratio=0.18, support_ratio=0.08)\n"
            "mass cut = cut_corner(lifted, corner='ne', ratio=0.2)\n"
            "mass court = courtyard(cut, margin_ratio=0.22, open_side='west')\n"
            "mass result = notch(court, side='west', ratio=0.18)",
            name="overloaded_author",
        )
        issue = geometry_llm_adapter._program_language_contract_issue(overloaded, context)
        self.assertIn("public_threshold_rule_budget=2", issue)

        valid = parse_geometry_dsl(
            "mass base = box(10, 8, 5)\n"
            "mass body = bend(base, axis='x', angle_degrees=24, subdivisions=4)\n"
            "mass result = notch(body, side='west', ratio=0.18)",
            name="bounded_author",
        )
        self.assertEqual(
            geometry_llm_adapter._program_language_contract_issue(valid, context),
            "",
        )

    def test_cross_layer_articulation_counts_openai_llm_authored_nodes(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 5)\n"
            "mass body = bend(base, axis='x', angle_degrees=24, subdivisions=4)\n"
            "mass result = notch(body, side='west', ratio=0.18)",
            name="llm_rule_evidence",
        )
        program = program.with_nodes(
            replace(node, provenance={"source": "openai_llm_geometry_author"})
            for node in program.nodes
        )
        source = compile_geometry_program_to_source_mass(program, box(0, 0, 30, 22))
        self.assertIsNotNone(source)
        metrics = _architectural_articulation_metrics(source)
        self.assertEqual(metrics["program_rule_count"], 1)
        self.assertEqual(metrics["public_threshold_rule_count"], 1)
        self.assertTrue(metrics["hard_pass"])

    def test_llm_author_rejects_tower_macro_applied_to_slab_seed(self):
        with self.assertRaisesRegex(
            Exception,
            "semantic_macro_leaning_tower_incompatible_with_slab_seed",
        ):
            geometry_programs_from_author_payload({"programs": [{
                "name": "mislabelled_slab_tower",
                "base_seed": "slab",
                "dsl": (
                    "mass seed = scale(box(1, 1, 1), vector=[2.2, 1.45, 0.28])\n"
                    "mass result = leaning_tower(seed, amount=0.18)"
                ),
                "intent_tags": ["oblique_slab"],
            }]}, expected_count=1)

    def test_llm_author_lowers_kind_and_parameter_type_from_operator_contract(self):
        def parameter(name, value_type, *, number=0.0, string="", boolean=False, vector=()):
            return {
                "name": name,
                "value_type": value_type,
                "numeric_value": number,
                "string_value": string,
                "boolean_value": boolean,
                "vector_value": list(vector),
                "structured_json": "null",
            }

        programs = geometry_programs_from_author_payload({"programs": [{
            "name": "contract_lowered",
            "base_seed": "block",
            "intent_tags": ["public_threshold"],
            "root_id": "court",
            "rationale": "compiler contract owns redundant type fields",
            "nodes": [
                {
                    "id": "seed", "kind": "primitive", "operator": "box", "inputs": [],
                    "parameters": [
                        parameter("width", "number", number=1.0),
                        parameter("depth", "number", number=1.0),
                        parameter("height", "number", number=1.0),
                    ],
                    "semantic_role": "base_seed",
                },
                {
                    "id": "result", "kind": "transform", "operator": "translate", "inputs": ["seed"],
                    "parameters": [
                        parameter("x", "number", number=0.0),
                        parameter("y", "number", number=0.0),
                        parameter("z", "string", number=0.0, string="literal"),
                    ],
                    "semantic_role": "site_fit",
                },
                {
                    "id": "court", "kind": "modifier", "operator": "courtyard", "inputs": ["result"],
                    "parameters": [
                        parameter("margin_ratio", "number", number=0.22),
                        parameter("open_side", "string", string="west"),
                    ],
                    "semantic_role": "public_void",
                },
            ],
        }]}, expected_count=1)

        program = programs[0]
        self.assertEqual(program.node_map["court"].kind, "macro")
        self.assertEqual(program.node_map["result"].parameters["z"], 0.0)
        self.assertEqual(len(program.metadata["contract_lowered_node_kind_corrections"]), 1)
        self.assertEqual(len(program.metadata["contract_lowered_parameter_type_corrections"]), 1)
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_llm_author_lowers_ambiguous_cut_operator_to_canonical_core_kind(self):
        def parameter(name, value_type, *, number=0.0, string=""):
            return {
                "name": name,
                "value_type": value_type,
                "numeric_value": number,
                "string_value": string,
                "boolean_value": False,
                "vector_value": [],
                "structured_json": "null",
            }

        program = geometry_programs_from_author_payload({"programs": [{
            "name": "canonical_cut_corner",
            "base_seed": "block",
            "intent_tags": ["oblique_body_cut"],
            "root_id": "result",
            "rationale": "body cut before any public relation",
            "nodes": [
                {
                    "id": "base", "kind": "primitive", "operator": "box", "inputs": [],
                    "parameters": [
                        parameter("width", "number", number=1.0),
                        parameter("depth", "number", number=1.0),
                        parameter("height", "number", number=1.0),
                    ],
                    "semantic_role": "base_seed",
                },
                {
                    "id": "result", "kind": "transform", "operator": "cut_corner", "inputs": ["base"],
                    "parameters": [
                        parameter("corner", "string", string="ne"),
                        parameter("ratio", "number", number=0.22),
                    ],
                    "semantic_role": "body_cut",
                },
            ],
        }]}, expected_count=1)[0]

        self.assertEqual(program.node_map["result"].kind, "modifier")
        self.assertEqual(
            program.metadata["contract_lowered_node_kind_corrections"][0]["contract_kind"],
            "modifier",
        )
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_llm_author_rejects_disconnected_solid_before_book_projection(self):
        with self.assertRaisesRegex(Exception, "disconnected_component_budget_exceeded"):
            geometry_programs_from_author_payload({"programs": [{
                "name": "disconnected_array",
                "base_seed": "block",
                "dsl": (
                    "mass seed = box(1, 1, 1)\n"
                    "mass result = linear_array(seed, count=2, vector=[3, 0, 0])"
                ),
                "intent_tags": ["invalid_disconnected_lego"],
            }]}, expected_count=1)

    def test_reference_image_vlm_gate_rejects_interior_before_mass_critic(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            matches = []
            for index in range(4):
                path = root / f"reference-{index}.jpg"
                path.write_bytes(b"fixture")
                matches.append({
                    "source": "archdaily_api",
                    "source_id": f"sports-{index}",
                    "title": f"Sports project {index}",
                    "local_path": str(path),
                    "program_match_tier": "preferred_collection",
                    "program_relevance_score": 8 - index,
                    "reference_contract": {"hard_pass": True},
                })
            audits = [
                {
                    "schema_version": "arr.maas.reference_image_massing_audit.v1",
                    "prompt_contract_version": "test",
                    "provider": "openai", "model": "test", "response_id": f"r-{index}",
                    "view_type": "interior" if index == 0 else "exterior_massing",
                    "whole_building_visible": index != 0,
                    "massing_legibility": 0.1 if index == 0 else 0.8,
                    "operation_clarity": 0.1 if index == 0 else 0.6 + index * 0.05,
                    "hard_pass": index != 0,
                    "failure_reasons": ["interior_only"] if index == 0 else [],
                    "visible_form_traits": [] if index == 0 else ["long_span"],
                    "cache_hit": False,
                }
                for index in range(4)
            ]
            with patch(
                "design.maas.geometry_language.vlm_adapter.audit_reference_image_for_massing",
                side_effect=audits,
            ):
                report = audit_reference_matches_for_massing(
                    matches,
                    building_type="gymnasium",
                    limit=5,
                )
        self.assertTrue(report["hard_pass"])
        self.assertEqual(report["massing_suitable_program_image_count"], 3)
        self.assertEqual(len(report["accepted"]), 3)
        self.assertEqual(report["rejected"][0]["source_id"], "sports-0")
        self.assertEqual(report["rejected"][0]["view_type"], "interior")

    def test_reference_image_vlm_gate_rejects_highrise_scale_for_neighborhood_program(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            matches = []
            audits = []
            for index in range(5):
                path = root / f"reference-{index}.jpg"
                path.write_bytes(b"fixture")
                matches.append({
                    "source": "archdaily_api",
                    "source_id": f"neighborhood-{index}",
                    "title": f"Neighborhood project {index}",
                    "local_path": str(path),
                    "program_match_tier": "preferred_collection",
                    "program_relevance_score": 8 - index,
                    "reference_contract": {"hard_pass": True},
                })
                audits.append({
                    "schema_version": "arr.maas.reference_image_massing_audit.v2",
                    "prompt_contract_version": "test",
                    "provider": "openai", "model": "test", "response_id": f"r-{index}",
                    "view_type": "exterior_massing",
                    "whole_building_visible": True,
                    "massing_legibility": 0.9,
                    "operation_clarity": 0.8,
                    "building_scale_typology": "highrise_tower" if index == 0 else "pavilion_lowrise",
                    "primary_building_typology": "office" if index == 0 else "retail_hospitality",
                    "typology_confidence": 0.92,
                    "hard_pass": True,
                    "failure_reasons": [],
                    "visible_form_traits": ["tower"] if index == 0 else ["courtyard"],
                    "cache_hit": False,
                })
            with patch(
                "design.maas.geometry_language.vlm_adapter.audit_reference_image_for_massing",
                side_effect=audits,
            ):
                report = audit_reference_matches_for_massing(
                    matches,
                    building_type="neighborhood_living",
                    limit=5,
                )

        self.assertTrue(report["hard_pass"])
        self.assertEqual(len(report["accepted"]), 4)
        rejected = next(item for item in report["rejected"] if item["source_id"] == "neighborhood-0")
        self.assertEqual(rejected["status"], "rejected_program_scale_mismatch")
        self.assertFalse(rejected["program_scale_compatible"])

    def test_final_book_reference_gate_expands_archive_search_without_relaxing_minimum(self):
        program = parse_geometry_dsl("mass result = box(10, 8, 6)")
        initial = [{"source_id": f"initial-{index}"} for index in range(10)]
        expanded = [{"source_id": f"expanded-{index}"} for index in range(24)]

        def retrieve(_program, *, building_type, limit):
            self.assertEqual(building_type, "neighborhood_living")
            return initial if limit == 10 else expanded

        def audit(matches, *, building_type, model, limit):
            accepted_count = 2 if len(matches) == 10 else 5
            accepted = [
                {
                    **matches[index],
                    "program_match_tier": "preferred_collection",
                }
                for index in range(accepted_count)
            ]
            return {
                "schema_version": "arr.maas.reference_massing_gate.v1",
                "input_image_count": len(matches),
                "massing_suitable_image_count": accepted_count,
                "massing_suitable_program_image_count": accepted_count,
                "hard_pass": accepted_count >= 3,
                "accepted": accepted,
                "rejected": [],
            }

        with patch(
            "design.maas.book_language.reference_context.retrieve_geometry_reference_matches",
            side_effect=retrieve,
        ), patch(
            "design.maas.book_language.reference_context.audit_reference_matches_for_massing",
            side_effect=audit,
        ):
            references, report = _audited_final_book_references(
                program,
                building_type="neighborhood_living",
            )

        self.assertEqual(len(references), 5)
        self.assertTrue(report["hard_pass"])
        self.assertTrue(report["adaptive_retrieval_attempted"])
        self.assertFalse(report["initial_retrieval"]["hard_pass"])
        self.assertEqual(report["expanded_retrieval_limit"], 24)
        self.assertTrue(report["hard_requirement_was_not_relaxed"])

    def test_reference_vlm_language_exposes_relations_without_geometry_template(self):
        context = _reference_language_author_context([{
            "source_id": "archdaily-gym-1",
            "title": "Verified Sports Hall",
            "program_match_tier": "preferred_collection",
            "massing_image_audit": {
                "building_scale_typology": "large_span_hall",
                "primary_building_typology": "sports",
                "visible_form_traits": ["folded daylight roof", "subordinate service spine"],
                "massing_legibility": 0.91,
                "operation_clarity": 0.87,
            },
        }], {
            "program_id": "gymnasium",
            "minimum_program_specific_images": 1,
            "massing_suitable_program_image_count": 1,
            "hard_pass": True,
        })

        self.assertEqual(context["status"], "verified")
        self.assertTrue(context["transfer_only_relations_and_operations"])
        self.assertFalse(context["copy_completed_form"])
        self.assertNotIn("local_path", context["references"][0])
        self.assertNotIn("image_url", context["references"][0])
        self.assertEqual(
            context["references"][0]["visible_form_traits"],
            ["folded daylight roof", "subordinate service spine"],
        )

    def test_final_vlm_cache_key_changes_with_prompt_contract(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 1], [0, 1], [0, 0]]]},
            "properties": {"mass_volumes": [], "source_surfaces": []},
        }
        with patch.object(preference_loop, "VLM_PROMPT_CONTRACT_VERSION", "contract-a"):
            first = preference_loop._vlm_cache_key(feature, [], "model")
        with patch.object(preference_loop, "VLM_PROMPT_CONTRACT_VERSION", "contract-b"):
            second = preference_loop._vlm_cache_key(feature, [], "model")
        self.assertNotEqual(first, second)

    def test_vlm_section_action_is_program_conditioned_but_explicit_hard_fail_is_never_ignored(self):
        payload = {
            "program_fit_hard_pass": False,
            "concept_scores": {
                "program_appropriateness": 0.8,
                "section_program_fit": 0.2,
            },
            "critic_actions": ["missing_program_section"],
        }
        neighborhood = _normalize_vlm_result(
            payload,
            model="fake",
            response_id="neighborhood",
            feature={"properties": {"program_context": {
                "program_id": "neighborhood_living",
                "semantic_invariants": [{"id": "neighborhood_active_edge"}],
            }}},
        )
        gym = _normalize_vlm_result(
            payload,
            model="fake",
            response_id="gym",
            feature={"properties": {"program_context": {
                "program_id": "gymnasium",
                "semantic_invariants": [{"id": "gym_roof_section"}],
            }}},
        )

        self.assertFalse(neighborhood["program_fit_hard_pass"])
        self.assertNotIn("missing_program_section", neighborhood["critic_actions"])
        self.assertFalse(neighborhood["explicit_program_section_required"])
        self.assertFalse(gym["program_fit_hard_pass"])
        self.assertIn("missing_program_section", gym["critic_actions"])
        self.assertTrue(gym["explicit_program_section_required"])

    def test_vlm_visual_fragment_action_cannot_contradict_a_hard_pass(self):
        payload = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.78,
                "repair_integrity": 0.74,
                "program_appropriateness": 0.80,
                "section_program_fit": 0.75,
            },
            "critic_actions": ["too_fragmented"],
        }
        result = _normalize_vlm_result(
            payload,
            model="fake",
            response_id="fragment",
            feature={"properties": {"program_context": {
                "program_id": "neighborhood_living",
                "semantic_invariants": [{"id": "neighborhood_active_edge"}],
            }}},
        )
        self.assertFalse(result["program_fit_hard_pass"])
        self.assertIn("too_fragmented", result["critic_actions"])

    def test_open_side_courtyard_is_a_distinct_clean_u_shaped_solid(self):
        closed = parse_geometry_dsl(
            'mass base = box(12, 9, 5)\nmass result = courtyard(base, margin_ratio=0.24, open_side="closed")',
            name="closed_court",
        )
        opened = parse_geometry_dsl(
            'mass base = box(12, 9, 5)\nmass result = courtyard(base, margin_ratio=0.24, open_side="east")',
            name="open_court",
        )
        closed_compilation = compile_geometry_program(closed)
        open_compilation = compile_geometry_program(opened)
        self.assertEqual(closed_compilation.status, "compiled")
        self.assertEqual(open_compilation.status, "compiled")
        self.assertNotEqual(closed_compilation.geometry_hash, open_compilation.geometry_hash)
        self.assertLess(open_compilation.metrics["volume"], closed_compilation.metrics["volume"])
        self.assertFalse(compilation_gate(open_compilation))

    def test_site_access_maps_to_normalized_program_principal_side(self):
        site = box(0, 0, 20, 10)
        east_edge = {"type": "LineString", "coordinates": [[20, 1], [20, 9]]}
        west_edge = {"type": "LineString", "coordinates": [[0, 1], [0, 9]]}
        south_edge = {"type": "LineString", "coordinates": [[2, 0], [18, 0]]}
        north_edge = {"type": "LineString", "coordinates": [[2, 10], [18, 10]]}
        long_positive = _site_access_side_in_principal_frame(site, east_edge)
        long_negative = _site_access_side_in_principal_frame(site, west_edge)
        short_negative = _site_access_side_in_principal_frame(site, south_edge)
        short_positive = _site_access_side_in_principal_frame(site, north_edge)
        self.assertEqual({long_positive, long_negative}, {"east", "west"})
        self.assertEqual({short_positive, short_negative}, {"north", "south"})

    def test_frontage_notch_is_typed_and_measured_as_access_aligned(self):
        program = parse_geometry_dsl(
            'mass base = box(12, 9, 5)\nmass result = notch(base, side="west", ratio=0.2, width_ratio=0.4, height_ratio=0.65)',
            name="frontage_notch",
        )
        compilation = compile_geometry_program(program)
        self.assertEqual(compilation.status, "compiled")
        context = {
            **program_reference_contract("gymnasium"),
            "site_access_context": {"primary_access_edge": "west"},
            "site_access_side_in_program_frame": "west",
        }
        snapshot = build_geometry_graph_snapshot(program, compilation, program_context=context)
        source = SimpleNamespace(metadata={
            "geometry_program": program.to_dict(),
            "program_context": context,
            "geometry_graph_snapshot": snapshot,
        })
        descriptor = _design_concept_descriptor(source)
        self.assertEqual(descriptor["ground_strategy"], "frontage_entry_notch")
        self.assertTrue(descriptor["frontage_aligned"])
        self.assertEqual(descriptor["frontage_aligned_controller_node_ids"], ["result"])

    def test_vlm_section_family_edit_regenerates_controls_and_geometry(self):
        program = parse_geometry_dsl(
            'mass base = box(12, 9, 5)\nmass result = profiled_hall(base, section_family="ridge", span_axis="x")',
            name="section_edit",
        )
        before = compile_geometry_program(program)
        mutation = apply_geometry_edits(program, [{
            "operation": "set_parameter",
            "target_node_id": "result",
            "parameter_name": "section_family",
            "string_value": "arched",
        }])
        self.assertEqual(mutation.status, "revised")
        self.assertIsNotNone(mutation.program)
        revised = mutation.program.node_map["result"]
        self.assertEqual(revised.parameters["section_family"], "barrel")
        self.assertGreater(len(revised.parameters["section_controls"]), 3)
        after = compile_geometry_program(mutation.program)
        self.assertEqual(after.status, "compiled")
        self.assertNotEqual(before.geometry_hash, after.geometry_hash)

    def test_direct_edge_graph_exposes_root_as_wrap_target_not_satisfied_controller(self):
        program = parse_geometry_dsl("mass result = box(12, 9, 5)", name="direct_edge")
        compilation = compile_geometry_program(program)
        context = {
            **program_reference_contract("gymnasium"),
            "site_access_context": {"primary_access_edge": "west"},
            "site_access_side_in_program_frame": "west",
        }
        snapshot = build_geometry_graph_snapshot(program, compilation, program_context=context)
        threshold = next(
            item for item in snapshot["design_concept_graph"]["concept_nodes"]
            if item["concept_id"] == "concept:public_threshold"
        )
        self.assertEqual(threshold["controller_node_ids"], [])
        self.assertEqual(threshold["available_wrap_target_node_ids"], ["result"])
        self.assertEqual(threshold["controller_mode"], "direct_edge_root_available_for_typed_add_node")
        self.assertEqual(threshold["frontage_alignment_status"], "direct_edge_unarticulated")
        self.assertTrue(threshold["missing_controller"])
        self.assertFalse(any(
            edge["relation"] == "controls_public_threshold"
            for edge in snapshot["design_concept_graph"]["causal_bindings"]
        ))
        self.assertTrue(any(
            edge["relation"] == "available_for_public_threshold_mutation"
            and edge["target_geometry_node_id"] == "result"
            for edge in snapshot["design_concept_graph"]["causal_bindings"]
        ))

    def test_design_graph_understands_program_role_names_not_only_generic_dominant_mass(self):
        base = parse_geometry_dsl("mass result = box(12, 9, 5)", name="role_probe")
        role_program = replace(base, nodes=(replace(
            base.nodes[0], semantic_role="dominant_hall",
        ),))
        compilation = compile_geometry_program(role_program)
        snapshot = build_geometry_graph_snapshot(
            role_program,
            compilation,
            program_context=program_reference_contract("gymnasium"),
        )
        dominant = next(
            item for item in snapshot["design_concept_graph"]["concept_nodes"]
            if item["concept_id"] == "concept:dominant_program_space"
        )
        self.assertEqual(dominant["controller_node_ids"], ["result"])

    def test_vlm_critic_receives_stable_balanced_portfolio_section_slot(self):
        base = parse_geometry_dsl("mass result = box(12, 9, 5)", name="slot_probe")
        program = replace(base, metadata={**base.metadata, "variation_index": 4})
        compilation = compile_geometry_program(program)
        critic = openai_vlm_geometry_critic(
            building_type="gymnasium",
            program_context={"program_id": "gymnasium"},
        )
        with patch(
            "design.maas.geometry_language.vlm_adapter.score_geometry_program_with_openai_vlm",
            return_value={"program_fit_hard_pass": True},
        ) as scorer:
            critic(program, compilation, Path("unused.png"))
        context = scorer.call_args.kwargs["program_context"]
        contract = context["portfolio_diversity_contract"]
        self.assertEqual(contract["preferred_section_family"], "stepped")
        self.assertEqual(
            contract["allowed_section_families"],
            ["ridge", "shed", "folded", "sawtooth", "stepped", "barrel"],
        )

    def test_design_concept_graph_binds_site_threshold_to_editable_court_node(self):
        program = parse_geometry_dsl(
            'mass base = box(12, 9, 5)\nmass result = courtyard(base, margin_ratio=0.24, open_side="east")',
            name="site_court",
        )
        compilation = compile_geometry_program(program)
        context = {
            **program_reference_contract("gymnasium"),
            "site_access_context": {"primary_access_edge": "east", "road_width_m": 6.0},
            "site_access_side_in_program_frame": "east",
            "program_dimensional_context": {
                "selected_subtype": "compact_training_hall",
                "minimum_clear_span_m": 6.0,
                "effective_height_m": 5.8,
                "maximum_height_to_clear_span_ratio": 1.1,
            },
        }
        snapshot = build_geometry_graph_snapshot(program, compilation, program_context=context)
        concept = snapshot["design_concept_graph"]
        threshold = next(
            item for item in concept["concept_nodes"]
            if item["concept_id"] == "concept:public_threshold"
        )
        self.assertEqual(threshold["target_open_side"], "east")
        self.assertEqual(threshold["controller_node_ids"], ["result"])
        self.assertFalse(threshold["missing_controller"])
        self.assertEqual(threshold["frontage_alignment_status"], "aligned")
        self.assertEqual(threshold["frontage_aligned_controller_node_ids"], ["result"])
        self.assertTrue(any(
            edge["relation"] == "controls_public_threshold"
            and edge["target_geometry_node_id"] == "result"
            for edge in concept["causal_bindings"]
        ))

        source = SimpleNamespace(metadata={
            "geometry_program": program.to_dict(),
            "program_context": context,
            "geometry_graph_snapshot": snapshot,
        })
        descriptor = _design_concept_descriptor(source)
        self.assertEqual(descriptor["ground_strategy"], "frontage_open_court")
        self.assertEqual(descriptor["frontage_aligned_controller_node_ids"], ["result"])
        self.assertTrue(descriptor["derived_from_final_recursive_ast"])

    def test_geometry_vlm_critic_cache_reuses_identical_render_evidence(self):
        program = parse_geometry_dsl("mass result = box(10, 8, 6)", name="cache_probe")
        compilation = compile_geometry_program(program)
        with TemporaryDirectory() as directory:
            preview = Path(directory) / "preview.png"
            preview.write_bytes(b"stable-render-evidence")
            cache_dir = Path(directory) / "cache"
            payload = {
                "concept_scores": {
                    "gesture_clarity": 0.8,
                    "hierarchy": 0.8,
                    "program_appropriateness": 0.8,
                    "section_program_fit": 0.8,
                },
                "program_fit_hard_pass": True,
                "critic_actions": [],
                "geometry_edits": [],
                "reference_assessments": [],
                "model": "test-vlm",
                "response_id": "test-response",
            }
            with patch.dict(os.environ, {"MAAS_GEOMETRY_VLM_CACHE_DIR": str(cache_dir)}), patch(
                "design.maas.geometry_language.vlm_adapter.score_candidate_with_openai_vlm",
                return_value=payload,
            ) as scorer:
                first = score_geometry_program_with_openai_vlm(
                    program,
                    compilation,
                    preview,
                    building_type="gymnasium",
                    program_context=program_reference_contract("gymnasium"),
                    outcome_memory_context={"observation_count": 1, "common_failed_gates": []},
                    model="test-vlm",
                )
                second = score_geometry_program_with_openai_vlm(
                    program,
                    compilation,
                    preview,
                    building_type="gymnasium",
                    program_context=program_reference_contract("gymnasium"),
                    outcome_memory_context={"observation_count": 1, "common_failed_gates": []},
                    model="test-vlm",
                )
                revised_memory = score_geometry_program_with_openai_vlm(
                    program,
                    compilation,
                    preview,
                    building_type="gymnasium",
                    program_context=program_reference_contract("gymnasium"),
                    outcome_memory_context={
                        "observation_count": 2,
                        "common_failed_gates": [{"gate": "role_coverage", "count": 1}],
                    },
                    model="test-vlm",
                )
            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            self.assertFalse(revised_memory["cache_hit"])
            self.assertEqual(scorer.call_count, 2)
            self.assertEqual(len(tuple(cache_dir.glob("*.json"))), 2)

    def test_gym_program_form_gate_rejects_cascade_without_hall_enclosure(self):
        pyramid = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": False,
            "horizontal_level_count": 10,
            "horizontal_surface_ratio": 0.912,
            "vertical_surface_ratio": 0.0124,
            "sloped_surface_ratio": 0.0756,
        }})
        sloped_pyramid = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": False,
            "horizontal_level_count": 4,
            "horizontal_surface_ratio": 0.6397,
            "vertical_surface_ratio": 0.0,
            "sloped_surface_ratio": 0.3603,
        }})
        sawtooth_hall = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": False,
            "horizontal_level_count": 6,
            "horizontal_surface_ratio": 0.41,
            "vertical_surface_ratio": 0.17,
            "sloped_surface_ratio": 0.42,
        }})
        measured_profiled_hall = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": False,
            "horizontal_level_count": 8,
            "horizontal_surface_ratio": 0.72,
            "vertical_surface_ratio": 0.02,
            "sloped_surface_ratio": 0.26,
            "oriented_plan_aspect_ratio": 2.4,
            "profiled_section_family": "sawtooth",
            "measured_profiled_hall": True,
        }})
        collapsed_profiled_tent = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": True,
            "collapsed_profiled_tent_like": True,
            "horizontal_level_count": 11,
            "horizontal_surface_ratio": 0.94,
            "vertical_surface_ratio": 0.0,
            "sloped_surface_ratio": 0.06,
            "oriented_plan_aspect_ratio": 1.6,
            "profiled_section_family": "barrel",
            "measured_profiled_hall": True,
        }})
        shallow_sloped_tent = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": True,
            "collapsed_profiled_tent_like": True,
            "horizontal_level_count": 16,
            "horizontal_surface_ratio": 0.85,
            "vertical_surface_ratio": 0.0,
            "sloped_surface_ratio": 0.15,
            "upper_area_ratio": 0.10,
            "oriented_plan_aspect_ratio": 2.4,
            "profiled_section_family": "folded",
            "measured_profiled_hall": True,
        }})
        broad_low_vertical_tent = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": True,
            "collapsed_profiled_tent_like": True,
            "horizontal_level_count": 17,
            "horizontal_surface_ratio": 0.826,
            "vertical_surface_ratio": 0.006,
            "sloped_surface_ratio": 0.168,
            "upper_area_ratio": 0.31,
            "oriented_plan_aspect_ratio": 2.35,
            "profiled_section_family": "barrel",
            "measured_profiled_hall": True,
        }})
        five_level_erased_enclosure = SimpleNamespace(metadata={"measured_solid_morphology": {
            "pyramidal_like": False,
            "collapsed_profiled_tent_like": False,
            "horizontal_level_count": 5,
            "horizontal_surface_ratio": 0.968,
            "vertical_surface_ratio": 0.0,
            "sloped_surface_ratio": 0.032,
            "upper_area_ratio": 0.056,
            "oriented_plan_aspect_ratio": 2.4,
            "profiled_section_family": "ridge",
            "measured_profiled_hall": True,
        }})
        rejected = _program_form_gate(pyramid, "gymnasium")
        rejected_sloped = _program_form_gate(sloped_pyramid, "gymnasium")
        accepted = _program_form_gate(sawtooth_hall, "gymnasium")
        accepted_profiled = _program_form_gate(measured_profiled_hall, "gymnasium")
        rejected_collapsed_tent = _program_form_gate(collapsed_profiled_tent, "gymnasium")
        rejected_shallow_tent = _program_form_gate(shallow_sloped_tent, "gymnasium")
        rejected_broad_tent = _program_form_gate(broad_low_vertical_tent, "gymnasium")
        rejected_erased_enclosure = _program_form_gate(five_level_erased_enclosure, "gymnasium")
        self.assertFalse(rejected["hard_pass"])
        self.assertFalse(rejected_sloped["hard_pass"])
        self.assertIn("gym_dominant_hall_erased_by_cascade_or_pyramid", rejected["failures"])
        self.assertTrue(accepted["hard_pass"])
        self.assertTrue(accepted_profiled["hard_pass"])
        self.assertFalse(rejected_collapsed_tent["hard_pass"])
        self.assertFalse(rejected_shallow_tent["hard_pass"])
        self.assertFalse(rejected_broad_tent["hard_pass"])
        self.assertFalse(rejected_erased_enclosure["hard_pass"])
        self.assertTrue(rejected_erased_enclosure["dominant_enclosure_erased"])

    def test_architectural_articulation_gate_rejects_cross_layer_effect_stacking(self):
        def node(node_id, operator, source, **provenance):
            return {
                "id": node_id,
                "operator": operator,
                "provenance": {"source": source, **provenance},
            }

        overloaded = SimpleNamespace(metadata={
            "measured_solid_morphology": {"pyramidal_like": False},
            "geometry_program": {"nodes": [
                {"id": "base", "operator": "box", "provenance": {"source": "seed"}},
                node("step", "stepped_mass", "procedural_geometry_synthesis_agent"),
                node("cantilever", "cantilever", "procedural_geometry_synthesis_agent"),
                node("scope", "clip_fraction", "book_recursive_projection", book_verb="select_book_scope", book_call_index=-1),
                node("book_stack", "stepped_mass", "book_recursive_projection", book_verb="stack", book_call_index=1),
                node("book_bend", "bend", "book_recursive_projection", book_verb="bend", book_call_index=2),
                node("section", "profiled_hall", "procedural_geometry_synthesis_agent"),
            ]},
        })
        metrics = _architectural_articulation_metrics(overloaded)
        gate = _program_form_gate(overloaded, "gymnasium")
        self.assertEqual(metrics["body_rule_count"], 4)
        self.assertEqual(metrics["program_rule_count"], 2)
        self.assertEqual(metrics["book_rule_count"], 2)
        self.assertEqual(metrics["duplicated_structural_families"], ["step"])
        self.assertNotIn("profiled_hall", [rule["operator"] for rule in metrics["rules"]])
        self.assertFalse(gate["hard_pass"])
        self.assertIn("architectural_body_rule_budget_exceeded", gate["failures"])
        self.assertIn("architectural_body_rule_family_repeated", gate["failures"])

    def test_architectural_articulation_gate_accepts_one_body_rule_plus_one_book_rule(self):
        coherent = SimpleNamespace(metadata={
            "measured_solid_morphology": {"pyramidal_like": False},
            "geometry_program": {"nodes": [
                {"id": "base", "operator": "box", "provenance": {"source": "seed"}},
                {
                    "id": "puncture",
                    "operator": "puncture",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
                {
                    "id": "scope",
                    "operator": "difference",
                    "provenance": {
                        "source": "book_recursive_projection",
                        "book_verb": "select_book_scope",
                        "book_call_index": -1,
                    },
                },
                {
                    "id": "expand",
                    "operator": "scale",
                    "provenance": {
                        "source": "book_recursive_projection",
                        "book_verb": "expand",
                        "book_call_index": 1,
                    },
                },
                {
                    "id": "section",
                    "operator": "profiled_hall",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
            ]},
        })
        metrics = _architectural_articulation_metrics(coherent)
        self.assertEqual(metrics["body_rule_count"], 2)
        self.assertTrue(metrics["hard_pass"])
        self.assertTrue(_program_form_gate(coherent, "gymnasium")["hard_pass"])

    def test_neighborhood_program_form_gate_allows_declared_two_step_book_sentence(self):
        accumulated = SimpleNamespace(metadata={
            "measured_solid_morphology": {"pyramidal_like": False},
            "geometry_program": {"nodes": [
                {"id": "base", "operator": "box", "provenance": {"source": "seed"}},
                {
                    "id": "body", "operator": "bend",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
                {
                    "id": "book_stack", "operator": "stepped_mass",
                    "provenance": {
                        "source": "book_recursive_projection",
                        "book_verb": "stack", "book_call_index": 1,
                    },
                },
                {
                    "id": "book_branch", "operator": "radial_array",
                    "provenance": {
                        "source": "book_recursive_projection",
                        "book_verb": "branch", "book_call_index": 2,
                    },
                },
            ]},
        })
        gate = _program_form_gate(accumulated, "neighborhood_living")
        self.assertTrue(gate["hard_pass"])
        self.assertEqual(gate["architectural_articulation"]["book_rule_count"], 2)

    def test_architectural_articulation_accepts_two_distinct_program_rule_families(self):
        composed = SimpleNamespace(metadata={
            "measured_solid_morphology": {"pyramidal_like": False},
            "geometry_program": {"nodes": [
                {"id": "base", "operator": "box", "provenance": {"source": "seed"}},
                {
                    "id": "bend", "operator": "bend",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
                {
                    "id": "setback", "operator": "setback",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
            ]},
        })
        repeated = SimpleNamespace(metadata={
            "geometry_program": {"nodes": [
                {
                    "id": "bend_a", "operator": "bend",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
                {
                    "id": "bend_b", "operator": "inflate",
                    "provenance": {"source": "critic_geometry_edit"},
                },
            ]},
        })

        composed_metrics = _architectural_articulation_metrics(composed)
        repeated_metrics = _architectural_articulation_metrics(repeated)
        self.assertEqual(composed_metrics["program_rule_count"], 2)
        self.assertEqual(composed_metrics["budget"]["program_body_rules"], 2)
        self.assertTrue(composed_metrics["hard_pass"])
        self.assertEqual(repeated_metrics["duplicated_program_families"], ["deformation"])
        self.assertIn("program_body_rule_family_repeated", repeated_metrics["budget_failures"])
        self.assertFalse(repeated_metrics["hard_pass"])

    def test_articulation_budget_respects_program_threshold_and_book_layers(self):
        layered = SimpleNamespace(metadata={
            "measured_solid_morphology": {"pyramidal_like": False},
            "geometry_program": {"nodes": [
                {"id": "base", "operator": "box", "provenance": {"source": "seed"}},
                {
                    "id": "lift", "operator": "lift", "parameters": {},
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
                {
                    "id": "entry", "operator": "courtyard", "parameters": {"open_side": "west"},
                    "provenance": {"source": "critic_geometry_edit"},
                },
                *[
                    {
                        "id": f"book_{index}", "operator": operator,
                        "provenance": {
                            "source": "book_recursive_projection",
                            "book_verb": verb,
                            "book_call_index": index,
                        },
                    }
                    for index, (operator, verb) in enumerate((
                        ("scale", "inflate"),
                        ("radial_array", "array"),
                        ("translate", "stack"),
                    ), start=1)
                ],
                {
                    "id": "section", "operator": "profiled_hall",
                    "provenance": {"source": "procedural_geometry_synthesis_agent"},
                },
            ]},
        })
        metrics = _architectural_articulation_metrics(layered)
        self.assertEqual(metrics["program_rule_count"], 1)
        self.assertEqual(metrics["public_threshold_rule_count"], 1)
        self.assertEqual(metrics["book_rule_count"], 3)
        self.assertEqual(metrics["body_rule_count"], 4)
        self.assertEqual(metrics["budget_failures"], [])
        self.assertTrue(metrics["hard_pass"])

        repeated_book = SimpleNamespace(metadata={
            "geometry_program": {"nodes": [
                {
                    "id": f"book_step_{index}", "operator": "stepped_mass",
                    "provenance": {
                        "source": "book_recursive_projection",
                        "book_verb": "stack",
                        "book_call_index": index,
                    },
                }
                for index in (1, 2)
            ]},
        })
        repeated = _architectural_articulation_metrics(repeated_book)
        self.assertEqual(repeated["duplicated_structural_families"], [])
        self.assertTrue(repeated["book_internal_repetition_is_authored_language"])
        self.assertTrue(repeated["hard_pass"])

    def test_gym_dimensional_context_adapts_height_or_reports_infeasible(self):
        compact = _program_dimensional_context(box(0, 0, 8, 15), "gymnasium", 18.0, 3)
        full = _program_dimensional_context(box(0, 0, 20, 30), "gymnasium", 18.0, 3)
        infeasible = _program_dimensional_context(box(0, 0, 5, 8), "gymnasium", 18.0, 3)
        self.assertEqual(compact["selected_subtype"], "compact_training_hall")
        self.assertEqual(compact["effective_height_m"], 5.888)
        self.assertEqual(compact["effective_floors"], 2)
        self.assertEqual(full["selected_subtype"], "long_span_sports_hall")
        self.assertEqual(full["effective_height_m"], 11.96)
        self.assertEqual(infeasible["status"], "infeasible")

    def test_gym_program_form_gate_enforces_measured_span_and_height_ratio(self):
        context = {
            "minimum_clear_span_m": 6.0,
            "maximum_height_to_clear_span_ratio": 1.10,
            "selected_subtype": "compact_training_hall",
        }
        valid = SimpleNamespace(
            footprint=box(0, 0, 8, 15),
            metadata={
                "program_dimensional_context": context,
                "measured_solid_morphology": {
                    "pyramidal_like": False,
                    "solid_height_m": 8.0,
                },
            },
        )
        too_tall = SimpleNamespace(
            footprint=box(0, 0, 5, 15),
            metadata={
                "program_dimensional_context": context,
                "measured_solid_morphology": {
                    "pyramidal_like": False,
                    "solid_height_m": 12.0,
                },
            },
        )
        self.assertTrue(_program_form_gate(valid, "gymnasium")["hard_pass"])
        rejected = _program_form_gate(too_tall, "gymnasium")
        self.assertFalse(rejected["hard_pass"])
        self.assertIn("gym_clear_span_below_program_minimum", rejected["failures"])
        self.assertIn("gym_height_to_clear_span_ratio_exceeded", rejected["failures"])

    def test_recursive_morphology_scales_normalized_z_by_effective_program_height(self):
        source = SimpleNamespace(
            footprint=box(0, 0, 8, 15),
            upper_footprint=box(0, 0, 8, 15),
            surfaces=(SimpleNamespace(
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 1.0)),
            ),),
            metadata={
                "program_dimensional_context": {"effective_height_m": 6.0},
                "geometry_program_compilation": {"metrics": {"component_count": 1, "genus": 0}},
                "geometry_program": {"nodes": []},
            },
        )
        metrics = _solid_morphology_metrics(source)
        self.assertEqual(metrics["solid_height_m"], 6.0)
        self.assertGreater(metrics["sloped_surface_ratio"], 0.9)

    def test_profiled_hall_macro_compiles_six_distinct_section_families(self):
        programs = synthesize_architectural_programs({
            "base_seeds": ["bar"],
            "intent_tags": ["profiled_span_section"],
            "candidate_count": 6,
            "maximum_operator_depth": 1,
        }, building_type="gymnasium")
        self.assertEqual(len(programs), 6)
        section_families = {
            str(program.node_map[program.root_id].parameters.get("section_family") or "")
            for program in programs
        }
        self.assertEqual(section_families, {"ridge", "shed", "folded", "sawtooth", "stepped", "barrel"})
        compilations = [compile_geometry_program(program) for program in programs]
        self.assertTrue(all(result.status == "compiled" for result in compilations))
        self.assertTrue(all(not compilation_gate(result) for result in compilations))
        self.assertEqual(len({result.geometry_hash for result in compilations}), 6)
        self.assertTrue(all(
            "normalized_section_profile" in {
                expansion
                for row in result.trace
                for expansion in row["macro_expansion"]
            }
            for result in compilations
        ))
        protected_snapshot = build_geometry_graph_snapshot(programs[0], compilations[0])
        self.assertEqual(
            protected_snapshot["agent_edit_contract"]["protected_geometry_node_ids"],
            [programs[0].root_id],
        )

    def test_profiled_hall_language_generates_twenty_four_distinct_bounded_variants(self):
        programs = synthesize_architectural_programs({
            "base_seeds": ["bar", "slab", "block"],
            "intent_tags": ["profiled_span_section"],
            "candidate_count": 24,
            "maximum_operator_depth": 1,
        }, building_type="gymnasium")
        self.assertEqual(len(programs), 24)
        self.assertEqual({
            node.parameters["section_family"]
            for program in programs
            for node in program.nodes
            if node.operator == "profiled_hall"
        }, {"ridge", "shed", "folded", "sawtooth", "stepped", "barrel"})
        self.assertEqual({
            node.parameters["section_variant_index"]
            for program in programs
            for node in program.nodes
            if node.operator == "profiled_hall"
        }, {0, 1, 2, 3})
        compilations = [compile_geometry_program(program) for program in programs]
        self.assertTrue(all(result.status == "compiled" for result in compilations))
        self.assertEqual(len({result.geometry_hash for result in compilations}), 24)

    def test_required_terminal_section_keeps_oversampled_body_mutations_program_fit(self):
        request = {
            "base_seeds": ["bar", "slab", "block"],
            "intent_tags": [
                "calm_prismatic", "carved_void", "continuous_curve",
                "oblique_section", "lifted_ground",
            ],
            "required_body_phenotypes": ["curved", "stepped", "voided", "oblique"],
            "required_terminal_operator": "profiled_hall",
            "candidate_count": 48,
            "maximum_operator_depth": 2,
        }
        programs = synthesize_architectural_programs(request, building_type="gymnasium")
        self.assertEqual(len(programs), 48)
        self.assertTrue(all(program.node_map[program.root_id].operator == "profiled_hall" for program in programs))
        self.assertTrue(all(program.metadata["required_terminal_operator"] == "profiled_hall" for program in programs))
        self.assertTrue(all("long_span" in program.metadata["intent_tags"] for program in programs))
        self.assertTrue(all("stepped_section" in program.metadata["intent_tags"] for program in programs))
        split_nodes = [
            node for program in programs for node in program.nodes
            if node.operator == "split_wing"
        ]
        self.assertTrue(split_nodes)
        self.assertTrue(all(node.parameters.get("ground_spine") for node in split_nodes))
        self.assertGreaterEqual(len({
            tuple(program.metadata["operator_path"][:-1])
            for program in programs
        }), 8)
        compilations = [compile_geometry_program(program) for program in programs]
        self.assertTrue(all(result.status == "compiled" for result in compilations))
        self.assertEqual(len({result.geometry_hash for result in compilations}), 48)
        continuation = synthesize_architectural_programs({
            **request,
            "candidate_count": 24,
            "variation_offset": 48,
        }, building_type="gymnasium")
        self.assertEqual(len(continuation), 24)
        self.assertFalse(
            {program.program_hash() for program in programs}
            & {program.program_hash() for program in continuation}
        )
        self.assertTrue(all(program.metadata["variation_offset"] == 48 for program in continuation))

    def test_vlm_cannot_replace_program_section_invariant_but_can_wrap_it(self):
        hall = synthesize_architectural_programs({
            "base_seeds": ["bar"],
            "intent_tags": ["profiled_span_section"],
            "candidate_count": 1,
            "maximum_operator_depth": 1,
        }, building_type="gymnasium")[0]
        protected_id = hall.root_id
        rejected = apply_geometry_edits(hall, [{
            "operation": "replace_operator",
            "target_node_id": protected_id,
            "operator": "courtyard",
        }])
        self.assertEqual(rejected.status, "no_valid_edit_applied")
        self.assertIn("protected_program_invariant", {issue.code for issue in rejected.issues})

        wrapped = apply_geometry_edits(hall, [
            {
                "operation": "add_node",
                "node_id": "critic_public_court",
                "node_kind": "macro",
                "operator": "courtyard",
                "input_ids": [protected_id],
                "semantic_role": "public_void",
            },
            {
                "operation": "set_parameter",
                "target_node_id": "critic_public_court",
                "parameter_name": "void_ratio",
                "numeric_value": 0.24,
            },
            {"operation": "set_root", "target_node_id": "critic_public_court"},
        ])
        self.assertEqual(wrapped.status, "revised")
        self.assertIsNotNone(wrapped.program)
        self.assertEqual(wrapped.program.root_id, "critic_public_court")
        self.assertEqual(wrapped.program.node_map["critic_public_court"].parameters["margin_ratio"], 0.24)
        self.assertNotIn("void_ratio", wrapped.program.node_map["critic_public_court"].parameters)
        self.assertEqual(compile_geometry_program(wrapped.program).status, "compiled")

    def test_book_body_mutation_is_inserted_before_program_section_invariant(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["bar"],
            "intent_tags": ["profiled_span_section"],
            "candidate_count": 1,
            "maximum_operator_depth": 1,
        }, building_type="gymnasium")[0]
        section_id = program.root_id
        seed = program_seed_sequences("gymnasium")[0]
        sequence = compose_program_with_book_operations(
            seed,
            (book_operation_variants("bend", count=1)[0],),
            base_volume_label="1/2",
            orientation="long_axis",
        )
        projected = apply_book_projection_to_geometry_program(program, sequence)
        self.assertEqual(projected.root_id, section_id)
        section = projected.node_map[section_id]
        self.assertTrue(section.inputs[0].startswith("book"))
        self.assertEqual(
            projected.metadata["book_recursive_projection"]["application_order"],
            "base_body_then_book_scope_and_operations_then_program_relation_suffix",
        )
        before = compile_geometry_program(program)
        after = compile_geometry_program(projected)
        self.assertEqual(after.status, "compiled")
        self.assertNotEqual(before.geometry_hash, after.geometry_hash)

    def test_book_body_mutation_is_inserted_before_public_threshold_suffix(self):
        body = parse_geometry_dsl(
            "mass base = box(12, 8, 5)\n"
            "mass result = courtyard(base, margin_ratio=0.24, open_side='east')",
            name="terminal_public_court",
        )
        body = body.with_nodes(
            replace(node, semantic_role="public_threshold")
            if node.id == "result" else node
            for node in body.nodes
        )
        seed = program_seed_sequences("neighborhood_living")[0]
        sequence = compose_program_with_book_operations(
            seed,
            (book_operation_variants("taper", count=1)[0],),
            base_volume_label="1/2",
            orientation="long_axis",
        )
        projected = apply_book_projection_to_geometry_program(body, sequence)

        self.assertEqual(projected.root_id, "result")
        self.assertTrue(projected.node_map["result"].inputs[0].startswith("book"))
        self.assertEqual(
            projected.metadata["book_recursive_projection"]["program_relation_suffix_node_ids"],
            ["result"],
        )
        self.assertEqual(compile_geometry_program(projected).status, "compiled")

    def test_book_lift_precedes_program_access_while_terminal_split_can_bind_it(self):
        body = parse_geometry_dsl(
            "mass base = box(2.8, 0.62, 0.48)\n"
            "mass result = notch(base, side='west', ratio=0.2)",
            name="west_access_body",
        )
        body = body.with_nodes(
            replace(
                node,
                semantic_role="street_access",
                provenance={"program_invariant": True},
            ) if node.id == "result" else node
            for node in body.nodes
        )
        seed = program_seed_sequences("neighborhood_living")[0]
        for verb in ("lift", "split"):
            sequence = compose_program_with_book_operations(
                seed,
                (book_operation_variants(verb, count=1)[0],),
                base_volume_label="1/1",
                orientation="long_axis",
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            book_node = next(
                node for node in projected.nodes
                if (node.provenance or {}).get("book_verb") == verb
                and node.operator in {"book_lift", "book_split"}
            )
            if verb == "lift":
                self.assertEqual(book_node.operator, "book_lift")
                self.assertNotIn("access_side", book_node.parameters)
                self.assertEqual(book_node.parameters["axis"], "x")
            else:
                self.assertEqual(book_node.operator, "book_split")
                self.assertEqual(book_node.parameters["access_side"], "west")
                self.assertNotIn("ground_spine", book_node.parameters)
                self.assertEqual(book_node.parameters["split_generation"], 0)
                self.assertGreaterEqual(book_node.parameters["terminal_ratio"], 0.28)
                self.assertLessEqual(book_node.parameters["terminal_ratio"], 0.76)
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)

    def test_book_repeated_split_recursively_divides_one_child_branch(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        calls = book_sentence_variants(("split", "split"), count=1)[0]
        self.assertEqual(calls[0].params["axis"], calls[1].params["axis"])
        sequence = compose_program_with_book_operations(
            seed, calls, base_volume_label="1/4", orientation="long_axis",
        )
        projected = apply_book_projection_to_geometry_program(body, sequence)
        split_nodes = [
            node for node in projected.nodes
            if (node.provenance or {}).get("book_verb") == "split"
        ]
        self.assertEqual(
            [node.parameters["split_generation"] for node in split_nodes],
            [0, 1],
        )
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled", compilation.issues)
        self.assertEqual(compilation.metrics["component_count"], 1)

    def test_book_twist_follows_the_selected_base_volume_orientation(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        twist = book_operation_variants("twist", count=1)[0]
        axes = {}
        hashes = set()
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (twist,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "twist"
            )
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            hashes.add(compilation.geometry_hash)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })
        self.assertEqual(len(hashes), 3)

    def test_book_carve_uses_face_orientation_and_both_page_parameters(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        carve = book_operation_variants("carve", count=1)[0]
        axes = {}
        hashes = set()
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (carve,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "carve"
            )
            self.assertEqual(node.operator, "book_carve")
            self.assertIn("width_ratio", node.parameters)
            self.assertIn("depth_ratio", node.parameters)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
            hashes.add(compilation.geometry_hash)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })
        self.assertEqual(len(hashes), 3)

    def test_book_compress_follows_base_volume_orientation(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        compress = book_operation_variants("compress", count=1)[0]
        vectors = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (compress,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "compress"
            )
            vectors[orientation] = node.parameters["vector"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertLess(vectors["long_axis"][0], 1.0)
        self.assertLess(vectors["short_axis"][1], 1.0)
        self.assertLess(vectors["vertical"][2], 1.0)

    def test_book_fracture_is_use_agnostic_and_follows_scope_orientation(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        fracture = book_operation_variants("fracture", count=1)[0]
        axes = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (fracture,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "fracture"
            )
            self.assertEqual(node.operator, "book_fracture")
            self.assertNotIn("access_side", node.parameters)
            self.assertNotIn("ground_spine", node.parameters)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })

    def test_book_grade_is_a_face_oriented_subtraction_not_generic_terrace(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        grade = book_operation_variants("grade", count=1)[0]
        axes = {}
        hashes = set()
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (grade,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "grade"
            )
            self.assertEqual(node.operator, "book_grade")
            self.assertEqual(node.parameters["levels"], 4)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
            hashes.add(compilation.geometry_hash)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })
        self.assertEqual(len(hashes), 3)

    def test_book_notch_uses_a_face_oriented_wedge_not_program_entry_box(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        notch = book_operation_variants("notch", count=1)[0]
        axes = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (notch,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "notch"
            )
            self.assertEqual(node.operator, "book_notch")
            self.assertNotIn("side", node.parameters)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })

    def test_book_pinch_uses_orientation_and_depth_profile(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        pinch = book_operation_variants("pinch", count=1)[0]
        axes = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (pinch,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "pinch"
            )
            self.assertIn("profile_power", node.parameters)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })

    def test_book_shear_uses_three_orientation_specific_cut_planes(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        shear = book_operation_variants("shear", count=1)[0]
        normals = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (shear,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "shear"
            )
            normals[orientation] = node.parameters["normal"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertNotEqual(normals["long_axis"], normals["short_axis"])
        self.assertNotEqual(normals["long_axis"], normals["vertical"])
        self.assertNotEqual(normals["short_axis"], normals["vertical"])

    def test_book_taper_follows_selected_base_volume_orientation(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        taper = book_operation_variants("taper", count=1)[0]
        axes = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (taper,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "taper"
            )
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })

    def test_book_embed_enters_the_selected_face_and_projects_insertion_depth(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        embed = book_operation_variants("embed", count=1)[0]
        axes = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (embed,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "embed"
            )
            self.assertIn("embedded_ratio", node.parameters)
            self.assertNotIn("distance_ratio", node.parameters)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })

    def test_book_extract_compiles_a_continuous_face_oriented_guest_path(self):
        body = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        extract = book_operation_variants("extract", count=1)[0]
        axes = {}
        for orientation in ("long_axis", "short_axis", "vertical"):
            sequence = compose_program_with_book_operations(
                seed,
                (extract,),
                base_volume_label="1/1",
                orientation=orientation,
            )
            projected = apply_book_projection_to_geometry_program(body, sequence)
            node = next(
                item for item in projected.nodes
                if (item.provenance or {}).get("book_verb") == "extract"
            )
            self.assertEqual(node.operator, "book_extract")
            self.assertIn("guest_scale", node.parameters)
            self.assertIn("distance_ratio", node.parameters)
            axes[orientation] = node.parameters["axis"]
            compilation = compile_geometry_program(projected)
            self.assertEqual(compilation.status, "compiled", compilation.issues)
            self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertEqual(axes, {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        })

    def test_llm_author_gate_detects_threshold_erased_by_later_body_transform(self):
        program = parse_geometry_dsl(
            "mass base = box(12, 8, 5)\n"
            "mass court = courtyard(base, margin_ratio=0.24, open_side='east')\n"
            "mass result = rotate(court, axis='z', angle_degrees=20)",
            name="nonterminal_threshold",
        )
        program = program.with_nodes(
            replace(node, semantic_role="public_threshold")
            if node.id == "court" else node
            for node in program.nodes
        )
        self.assertEqual(
            geometry_llm_adapter._nonterminal_program_relation(program),
            "court",
        )

    def test_linear_architectural_stack_is_canonicalized_before_core_compilation(self):
        program = parse_geometry_dsl(
            "mass base = box(12, 8, 6)\n"
            "mass court = courtyard(base, margin_ratio=0.24, open_side='east')\n"
            "mass body = setback(court, levels=3, setback_ratio=0.1, shift_per_level=[0.03, 0, 0.04])\n"
            "mass result = lift(body, rise_ratio=0.16, support_ratio=0.1)",
            name="misordered_architectural_stack",
        )
        program = program.with_nodes(
            replace(node, semantic_role={
                "court": "public_threshold",
                "body": "calm_upper_mass",
                "result": "public_entry",
            }.get(node.id, node.semantic_role))
            for node in program.nodes
        )
        canonical = geometry_llm_adapter._canonicalize_program_relation_suffix(program)

        self.assertEqual(canonical.node_map["body"].inputs, ("base",))
        self.assertEqual(canonical.node_map["court"].inputs, ("body",))
        self.assertEqual(canonical.node_map["result"].inputs, ("court",))
        self.assertEqual(geometry_llm_adapter._nonterminal_program_relation(canonical), "")
        self.assertTrue(canonical.metadata["architectural_relation_suffix_canonicalized"])
        compilation = compile_geometry_program(canonical)
        self.assertEqual(compilation.status, "compiled")
        self.assertFalse(compilation_gate(compilation, geometry_llm_adapter.AUTHOR_GEOMETRY_GATE_POLICY))

    def test_llm_author_gate_binds_public_relation_to_program_access_side(self):
        program = parse_geometry_dsl(
            "mass base = box(12, 8, 5)\n"
            "mass result = notch(base, corner='ne', width_ratio=0.22, depth_ratio=0.18)",
            name="unbound_public_threshold",
        )
        program = program.with_nodes(
            replace(node, semantic_role="public_threshold")
            if node.id == "result" else node
            for node in program.nodes
        )
        context = {"site_access_side_in_program_frame": "east"}
        self.assertEqual(
            geometry_llm_adapter._misaligned_access_relation(program, context),
            "result:side=missing:required=east",
        )
        bound = program.with_nodes(
            replace(node, parameters={**node.parameters, "side": "east"})
            if node.id == "result" else node
            for node in program.nodes
        )
        self.assertEqual(
            geometry_llm_adapter._misaligned_access_relation(bound, context),
            "",
        )

    def test_vlm_can_reparameterize_but_cannot_bypass_public_relation_invariant(self):
        program = parse_geometry_dsl(
            "mass base = box(12, 8, 5)\n"
            "mass result = courtyard(base, margin_ratio=0.24, open_side='east')",
            name="protected_public_threshold",
        )
        program = program.with_nodes(
            replace(
                node,
                semantic_role="public_threshold",
                provenance={"program_invariant": True, "program_invariant_kind": "access_relation"},
            )
            if node.id == "result" else node
            for node in program.nodes
        )
        adjusted = apply_geometry_edits(program, [{
            "operation": "set_parameter",
            "target_node_id": "result",
            "parameter_name": "open_side",
            "string_value": "west",
        }])
        self.assertEqual(adjusted.status, "revised")
        self.assertEqual(adjusted.program.node_map["result"].parameters["open_side"], "west")
        bypassed = apply_geometry_edits(program, [{
            "operation": "set_root",
            "target_node_id": "base",
        }])
        self.assertEqual(bypassed.status, "no_valid_edit_applied")
        self.assertIn("program_invariant_bypassed", {issue.code for issue in bypassed.issues})

    def test_book_projection_rejects_repeated_full_body_effect_but_keeps_local_scope(self):
        body = parse_geometry_dsl(
            "mass base = box(12, 3, 4)\n"
            "mass result = bent_bar(base, axis='x', angle_degrees=26, subdivisions=4)"
        )
        seed = program_seed_sequences("neighborhood_living")[0]
        bend = book_operation_variants("bend", count=1)[0]
        full = compose_program_with_book_operations(
            seed, (bend,), base_volume_label="1/1", orientation="long_axis",
        )
        with self.assertRaisesRegex(ValueError, "incompatible_book_effect_stack:bend"):
            apply_book_projection_to_geometry_program(body, full)

        local = compose_program_with_book_operations(
            seed, (bend,), base_volume_label="1/4", orientation="long_axis",
        )
        projected = apply_book_projection_to_geometry_program(body, local)
        result = compile_geometry_program(projected)
        self.assertEqual(result.status, "compiled", result.issues)
        self.assertNotEqual(result.geometry_hash, compile_geometry_program(body).geometry_hash)

    def test_program_reference_contract_resolves_exact_profile_ids(self):
        expected = {
            "gymnasium": "sports_architecture",
            "cultural": "cultural_architecture",
            "neighborhood_living": "cafes_restaurants",
        }
        for profile_id, primary_collection in expected.items():
            contract = program_reference_contract(profile_id)
            self.assertEqual(contract["program_id"], profile_id)
            self.assertIn(primary_collection, contract["preferred_collections"])
            self.assertGreaterEqual(contract["minimum_program_specific_images"], 3)
            self.assertTrue(contract["semantic_invariants"])
            self.assertTrue(contract["target_floor_range"])
            self.assertTrue(contract["target_volume_range"])
            self.assertIsNone(contract["geometry_template"])
            self.assertFalse(contract["parcel_coordinates_allowed"])
        self.assertIn(
            "office tower",
            program_reference_contract("neighborhood_living")["excluded_terms"],
        )

    def test_neighborhood_reference_retrieval_rejects_preferred_collection_tower_typology(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["bar"],
            "intent_tags": ["carved_void", "stepped_section"],
            "candidate_count": 1,
        }, building_type="neighborhood_living")[0]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cafe_dir = root / "cafes_restaurants"
            mixed_dir = root / "mixed_use"
            cafe_dir.mkdir()
            mixed_dir.mkdir()
            cafe_records = []
            for index in range(4):
                image = cafe_dir / f"cafe-{index}.jpg"
                image.touch()
                cafe_records.append({
                    "source": "archdaily_api",
                    "source_id": f"cafe-{index}",
                    "title": f"Neighborhood courtyard cafe {index}",
                    "local_path": str(image),
                    "tags": ["cafe", "courtyard", "terrace", "street edge"],
                })
            (cafe_dir / "metadata.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in cafe_records),
                encoding="utf-8",
            )
            tower_image = mixed_dir / "tower.jpg"
            tower_image.touch()
            (mixed_dir / "metadata.jsonl").write_text(
                json.dumps({
                    "source": "archdaily_api",
                    "source_id": "tower",
                    "title": "Tallest Office Tower",
                    "caption": "A 230 meter tall mixed use office tower",
                    "local_path": str(tower_image),
                    "tags": ["commercial", "mixed use", "office tower"],
                }) + "\n",
                encoding="utf-8",
            )
            matches = retrieve_geometry_reference_matches(
                program,
                building_type="neighborhood_living",
                reference_root=root,
                limit=5,
            )

        self.assertGreaterEqual(len(matches), 3)
        self.assertNotIn("tower", {item["source_id"] for item in matches})
        self.assertTrue(all(item["reference_contract"]["hard_pass"] for item in matches))

    def test_all_69_book_principles_mutate_the_recursive_manifold_ast(self):
        base = base_seed_programs()[1]
        seed = program_seed_sequences("gymnasium")[0]
        scopes = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")
        orientations = ("long_axis", "short_axis", "vertical")
        rows = []
        for index, principle in enumerate(build_book_language_registry()["principles"]):
            calls = book_sentence_variants(principle["execution_verbs"], count=1)[0]
            sequence = compose_program_with_book_operations(
                seed,
                calls,
                base_volume_label=scopes[index % len(scopes)],
                orientation=orientations[index % len(orientations)],
            )
            program = apply_book_projection_to_geometry_program(base, sequence)
            compilation = compile_geometry_program(program)
            rows.append((program, compilation))
        self.assertEqual(len(rows), 69)
        self.assertTrue(all(result.status == "compiled" for _program, result in rows))
        self.assertTrue(all(int(result.metrics["component_count"]) <= 5 for _program, result in rows))
        self.assertEqual(len({program.program_hash() for program, _result in rows}), 69)
        self.assertGreaterEqual(len({result.geometry_hash for _program, result in rows}), 68)
        self.assertTrue(all(
            program.metadata["book_recursive_projection"]["geometry_authority"] == "recursive_manifold_ast"
            for program, _result in rows
        ))

    def test_repeated_book_operatives_are_relational_not_identical_replays(self):
        for calls in book_sentence_variants(("bend", "bend"), count=3):
            first, second = calls
            self.assertNotEqual(first.params, second.params)
            self.assertEqual(first.params["axis"], second.params["axis"])
            if abs(float(first.params["angle"])) > 1e-9:
                self.assertGreater(float(first.params["angle"]) * float(second.params["angle"]), 0.0)
        first_split, second_split = book_sentence_variants(("split", "split"), count=1)[0]
        # BOOK p.40 recursively splits one child of the first fork; it does
        # not apply an orthogonal full-body cut.
        self.assertEqual(first_split.params["axis"], second_split.params["axis"])
        self.assertNotEqual(first_split.params, second_split.params)

    def test_book_variations_sample_the_complete_eleven_diagram_lattice(self):
        variants = book_operation_variants("bend", count=11)

        self.assertEqual(book_variation_indices(1), (5,))
        self.assertEqual(book_variation_indices(3), (0, 5, 10))
        self.assertEqual(book_variation_indices(11), tuple(range(11)))
        self.assertEqual(len(variants), 11)
        self.assertEqual(len({float(call.params["angle"]) for call in variants}), 11)
        self.assertGreater(len({(call.params["axis"], call.params["curvature"]) for call in variants}), 8)
        representative_scopes = [book_probe_scope(0, 0, index) for index in (0, 5, 10)]
        self.assertEqual({orientation for _scope, orientation in representative_scopes}, {
            "long_axis", "short_axis", "vertical",
        })
        recursive_probe_scopes = [
            book_probe_scope(0, base_index, 10, couple_variation=False)
            for base_index in range(18)
        ]
        self.assertEqual({scope for scope, _orientation in recursive_probe_scopes}, {
            "1/1", "3/8", "1/2", "1/4", "1/8", "1/16",
        })
        self.assertEqual({orientation for _scope, orientation in recursive_probe_scopes}, {
            "long_axis", "short_axis", "vertical",
        })

    def test_book_branch_expand_and_shift_survive_as_live_solid_relations(self):
        base = base_seed_programs()[2]
        seed = program_seed_sequences("gymnasium")[0]
        before = compile_geometry_program(base)
        before_bounds = before.metrics["bounds"]
        before_spans = [
            before_bounds[1][axis] - before_bounds[0][axis]
            for axis in range(3)
        ]
        expected_operators = {
            "branch": "book_branch",
            "expand": "boundary_expand",
            "shift": "shift_related",
        }
        results = {}
        for verb, expected_operator in expected_operators.items():
            sequence = compose_program_with_book_operations(
                seed,
                (book_operation_variants(verb, count=1)[0],),
                base_volume_label="1/1",
                orientation="long_axis",
            )
            program = apply_book_projection_to_geometry_program(base, sequence)
            self.assertIn(expected_operator, {node.operator for node in program.nodes})
            result = compile_geometry_program(program)
            self.assertEqual(result.status, "compiled")
            self.assertEqual(result.metrics["component_count"], 1)
            results[verb] = result
        branch_bounds = results["branch"].metrics["bounds"]
        expand_bounds = results["expand"].metrics["bounds"]
        shift_bounds = results["shift"].metrics["bounds"]
        self.assertGreater(branch_bounds[1][1] - branch_bounds[0][1], before_spans[1])
        self.assertGreater(expand_bounds[1][1] - expand_bounds[0][1], before_spans[1])
        self.assertGreater(shift_bounds[1][0] - shift_bounds[0][0], before_spans[0])

    def test_book_array_keeps_related_wings_and_capacity_in_source_bridge(self):
        base = base_seed_programs()[2]
        seed = program_seed_sequences("gymnasium")[0]
        calls = book_sentence_variants(("taper", "array"), count=1)[0]
        sequence = compose_program_with_book_operations(seed, calls)
        program = apply_book_projection_to_geometry_program(base, sequence)
        related = next(node for node in program.nodes if node.operator == "related_array")
        self.assertEqual(related.parameters["mode"], "array")
        compilation = compile_geometry_program(program)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)
        host = box(0, 0, 30, 20)
        source = compile_geometry_program_to_source_mass(
            program,
            host,
            target_plan_area=528.0,
        )
        self.assertIsNotNone(source)
        assert source is not None
        self.assertGreater(source.footprint.area, host.area * 0.65)

    def test_six_book_scopes_are_causal_geometry_not_metadata_labels(self):
        base = base_seed_programs()[2]
        seed = program_seed_sequences("gymnasium")[0]
        bend = book_operation_variants("bend", count=2)[1]
        programs = []
        compilations = []
        for scope in ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16"):
            sequence = compose_program_with_book_operations(
                seed, (bend,), base_volume_label=scope, orientation="long_axis",
            )
            program = apply_book_projection_to_geometry_program(base, sequence)
            programs.append(program)
            compilations.append(compile_geometry_program(program))
        self.assertTrue(all(result.status == "compiled" for result in compilations))
        self.assertEqual(len({program.program_hash() for program in programs}), 6)
        self.assertEqual(len({result.geometry_hash for result in compilations}), 6)
        self.assertEqual(
            {program.metadata["book_recursive_projection"]["scope_label"] for program in programs},
            {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"},
        )

    def test_book_p3_base_volumes_keep_exact_fraction_and_connected_topology(self):
        audit = audit_book_base_volumes()

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(len(audit["rows"]), 18)
        three_eighths = [row for row in audit["rows"] if row["label"] == "3/8"]
        self.assertTrue(all(row["topology"] == "connected_three_octant_l" for row in three_eighths))
        self.assertTrue(all(row["vertex_count"] > 8 for row in three_eighths))
        self.assertTrue(all(row["component_count"] == 1 for row in audit["rows"]))

    def test_all_thirty_book_operatives_keep_eleven_variations_in_three_orientations(self):
        audit = audit_book_operatives()

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(audit["compile_count"], 990)
        self.assertEqual(len(audit["rows"]), 30)
        self.assertTrue(all(row["unique_geometry_count"] == 33 for row in audit["rows"]))

    def test_all_sixty_nine_book_pages_have_source_and_recursive_execution_evidence(self):
        audit = audit_book_pages()
        audit.pop("_representative", None)

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(audit["page_count"], 69)
        self.assertEqual(audit["principle_count"], 69)
        self.assertEqual(audit["recursive_compile_count"], 2277)
        self.assertEqual(audit["base_volume_compile_count"], 18)
        self.assertEqual(audit["total_compile_count"], 2295)
        self.assertTrue(all(row["hard_pass"] for row in audit["pages"]))
        self.assertEqual(
            {row["validation_mode"] for row in audit["pages"]},
            {
                "source_and_taxonomy_evidence",
                "exact_base_volume_geometry",
                "recursive_principle_geometry",
            },
        )

    def test_repeated_inscribe_keeps_one_nested_open_side_from_page_39(self):
        for first, second in book_sentence_variants(("inscribe", "inscribe"), count=11):
            self.assertEqual(first.params["open_side"], second.params["open_side"])

    def test_every_book_operative_has_one_page_reviewed_lowering_contract(self):
        self.assertEqual(set(BOOK_OPERATIVE_LOWERING), {item.verb for item in BASE_OPERATIVES})

    def test_recursive_book_projection_evidence_has_one_mesh_authority(self):
        base = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        sequence = compose_program_with_book_operations(
            seed,
            (book_operation_variants("expand", count=1)[0],),
            base_volume_label="3/8",
            orientation="vertical",
        )
        projected = apply_book_projection_to_geometry_program(base, sequence)
        compilation = compile_geometry_program(projected)
        evidence = recursive_book_projection_evidence(projected, {
            "status": "materialized",
            "program_hash": projected.program_hash(),
            "geometry_hash": compilation.geometry_hash,
        })

        self.assertEqual(evidence["status"], "materialized")
        self.assertEqual(evidence["geometry_authority"], "recursive_manifold_ast")
        self.assertTrue(evidence["legacy_source_projection_bypassed"])
        self.assertEqual(evidence["scope"]["base_volume_label"], "3/8")
        self.assertEqual(evidence["scope"]["topology"], "connected_three_octant_l")
        self.assertEqual(evidence["authoritative_geometry_hash"], compilation.geometry_hash)
        self.assertEqual(
            len([
                node for node in evidence["projection_graph"]["nodes"]
                if node["solid_operator"] == "book_base_volume"
            ]),
            1,
        )

    def test_vertical_book_extrude_preserves_plan_and_changes_height(self):
        base = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        sequence = compose_program_with_book_operations(
            seed,
            (book_operation_variants("extrude", count=1)[0],),
            base_volume_label="1/1",
            orientation="vertical",
        )
        projected = apply_book_projection_to_geometry_program(base, sequence)
        before = compile_geometry_program(base)
        after = compile_geometry_program(projected)
        self.assertEqual(after.status, "compiled")
        before_bounds = before.metrics["bounds"]
        after_bounds = after.metrics["bounds"]
        self.assertEqual(before_bounds[0][:2], after_bounds[0][:2])
        self.assertEqual(before_bounds[1][:2], after_bounds[1][:2])
        self.assertGreater(after_bounds[1][2] - after_bounds[0][2], before_bounds[1][2] - before_bounds[0][2])

    def test_normalized_slice_ratio_retains_most_of_different_base_proportions(self):
        for width, depth, height in ((10.0, 6.0, 4.0), (18.0, 3.0, 3.5)):
            builder = GeometryProgramBuilder(f"normalized_slice_{width}")
            base = builder.add(
                "primitive", "box",
                parameters={"width": width, "depth": depth, "height": height},
            )
            sliced = builder.add(
                "modifier", "slice", inputs=(base,),
                parameters={
                    "normal": [0.7, 0.0, -1.0],
                    "offset_ratio": 0.12,
                    "keep_side": "positive",
                },
            )
            before = compile_geometry_program(builder.build(base))
            after = compile_geometry_program(builder.build(sliced))
            self.assertEqual(after.status, "compiled")
            retention = after.metrics["volume"] / before.metrics["volume"]
            self.assertGreater(retention, 0.80)
            self.assertLess(retention, 0.99)

    def test_synthesis_agent_builds_diverse_recursive_programs_from_normalized_bases(self):
        programs = synthesize_architectural_programs({
            "base_seeds": ["slab", "bar", "block"],
            "intent_tags": [
                "long_span", "continuous_curve", "oblique_section",
                "stepped_section", "carved_void", "lifted_ground",
            ],
            "candidate_count": 18,
            "maximum_operator_depth": 2,
        }, building_type="gymnasium")
        self.assertEqual(len(programs), 18)
        self.assertEqual(len({program.program_hash() for program in programs}), 18)
        self.assertGreaterEqual(len({tuple(program.metadata["operator_path"]) for program in programs}), 12)
        self.assertEqual({program.metadata["completed_building_template"] for program in programs}, {False})
        self.assertTrue(all(compile_geometry_program(program).status == "compiled" for program in programs))
        effect_family = {
            "bend": "deformation", "bent_bar": "deformation", "twist": "deformation",
            "inflate": "deformation", "pinch": "deformation", "taper": "deformation",
            "shear": "deformation", "setback": "step", "stepped_mass": "step",
            "terrace": "step", "courtyard": "void", "carve_void": "void",
            "notch": "void", "puncture": "void", "cut_corner": "void",
            "slice": "cut", "radial_array": "array", "cross_mass": "array",
            "split_wing": "array", "cantilever": "support", "lift": "support",
        }
        for program in programs:
            families = [
                effect_family[operator]
                for operator in program.metadata["operator_path"]
                if operator in effect_family
            ]
            self.assertEqual(len(families), len(set(families)))
        compatibility_programs = synthesize_architectural_programs({
            "base_seeds": ["profiled_prism", "bar", "slab"],
            "intent_tags": ["long_span", "oblique_section"],
            "candidate_count": 12,
            "maximum_operator_depth": 2,
        }, building_type="gymnasium")
        long_span_slice = next(
            program for program in compatibility_programs
            if program.metadata["operator_path"][0] == "slice"
        )
        self.assertIn(long_span_slice.metadata["base_seed"], {"bar", "slab"})

    def test_program_profile_infers_capabilities_without_section_templates(self):
        requests = synthesis_requests_from_program_profile(
            "gymnasium",
            source_seeds=("hall_a", "hall_b", "hall_c"),
        )
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(
            not item["inference_evidence"]["section_control_templates_used"]
            for item in requests
        ))
        self.assertTrue(all("long_span" in item["intent_tags"] for item in requests))
        self.assertTrue(all("bar" in item["base_seeds"] for item in requests))
        self.assertTrue(all(item["typology_priors"] == [
            "additive", "subtractive", "lshape", "freeform",
        ] for item in requests))
        self.assertTrue(all(item["required_access_bound_relation"] for item in requests))
        self.assertTrue(all(
            item["required_macro_operators_all"] == ["profiled_hall"]
            for item in requests
        ))
        self.assertTrue(all(
            "profiled_hall" in item["allowed_macro_operators"]
            for item in requests
        ))
        self.assertEqual([item["variation_offset"] for item in requests], [0, 18])
        self.assertEqual(
            {item["downstream_body_rule_reserve"] for item in requests},
            {1},
        )
        self.assertEqual(
            {tuple(item["legal_fit_strengths"]) for item in requests},
            {(0.0,)},
        )
        first_programs = synthesize_architectural_programs(requests[0], building_type="gymnasium")
        second_programs = synthesize_architectural_programs(requests[1], building_type="gymnasium")
        self.assertFalse(
            {program.program_hash() for program in first_programs}
            & {program.program_hash() for program in second_programs}
        )
        self.assertNotIn("section_controls", str(requests))

    def test_frontend_early_typologies_are_typed_executable_chassis_priors(self):
        self.assertEqual([prior.typology_id for prior in TYPOLOGY_PRIORS], [
            "additive", "subtractive", "grid", "lshape", "ushape", "cross",
            "courtyard", "tower_podium", "hshape", "radial", "freeform",
        ])
        request = {
            **synthesis_requests_from_program_profile(
                "neighborhood living",
                source_seeds=("lineage-a",),
                candidates_per_lineage=12,
            )[0],
            "site_access_side": "west",
        }
        programs = synthesize_architectural_programs(request, building_type="neighborhood living")
        authored_priors = {
            str(program.metadata.get("early_typology_prior") or "")
            for program in programs
        }
        self.assertTrue(set(request["typology_priors"]).issubset(authored_priors))
        self.assertTrue(all(compile_geometry_program(program).status == "compiled" for program in programs))
        grid = next(program for program in programs if program.metadata.get("early_typology_prior") == "grid")
        grid_result = compile_geometry_program(grid)
        self.assertIn("grid_mass", grid.metadata["operator_path"])
        self.assertEqual(grid_result.metrics["component_count"], 1)
        tower_podium = next(
            program for program in programs
            if program.metadata.get("early_typology_prior") == "tower_podium"
        )
        self.assertEqual(tower_podium.metadata["base_seed"], "tower")

    def test_all_eleven_canonical_typology_chassis_are_connected_and_distinct(self):
        audit = audit_typology_priors()

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(len(audit["rows"]), 11)
        self.assertEqual(len({row["geometry_hash"] for row in audit["rows"]}), 11)

    def test_source_bridge_rejects_detached_recursive_fragments(self):
        detached = parse_geometry_dsl(
            "mass base = box(4, 2, 2)\n"
            "mass result = linear_array(base, count=3, vector=[8, 0, 0])",
            name="detached_fragment_probe",
        )

        self.assertEqual(compile_geometry_program(detached).metrics["component_count"], 3)
        self.assertIsNone(
            compile_geometry_program_to_source_mass(detached, box(0, 0, 30, 20))
        )

    def test_repeated_book_bend_is_not_stacked_over_an_existing_cross_field(self):
        cross = next(
            program for program in architectural_shape_programs()
            if program.metadata.get("family") == "cross_mass"
        )
        sequence = compose_program_with_book_operations(
            program_seed_sequences("neighborhood living")[0],
            book_sentence_variants(("bend", "bend"), count=1)[0],
            base_volume_label="3/8",
        )

        with self.assertRaisesRegex(ValueError, "repeated_nonlinear_deformation"):
            apply_book_projection_to_geometry_program(cross, sequence)

    def test_split_chassis_rejects_book_relation_that_erases_public_gap(self):
        split = next(
            program for program in architectural_shape_programs()
            if program.metadata.get("family") == "split_bridge"
        )
        intersect = compose_program_with_book_operations(
            program_seed_sequences("neighborhood living")[0],
            (book_operation_variants("intersect", count=1)[0],),
            base_volume_label="1/2",
        )
        taper = compose_program_with_book_operations(
            program_seed_sequences("neighborhood living")[0],
            (book_operation_variants("taper", count=1)[0],),
            base_volume_label="1/2",
        )

        with self.assertRaisesRegex(
            ValueError,
            "incompatible_book_chassis_relation:split_wing:intersect",
        ):
            apply_book_projection_to_geometry_program(split, intersect)
        compatible = apply_book_projection_to_geometry_program(split, taper)
        evidence = compatible.metadata["book_recursive_projection"]["chassis_compatibility"]
        self.assertEqual(evidence["status"], "compatible")
        self.assertEqual(
            evidence["checked_relations"][0]["protected_relation"],
            "continuous_public_gap_between_two_legible_wings",
        )

    def test_split_gap_uses_one_shared_normalized_relation_contract(self):
        from design.maas.geometry_language import (
            SPLIT_WING_RELATION_CONTRACT,
            project_book_split_gap_ratio,
        )
        from design.maas.grammar.parameter_schema import PARAMETER_BOUNDS

        source_low, source_high = PARAMETER_BOUNDS["gap_ratio"]
        self.assertEqual(
            project_book_split_gap_ratio(source_low),
            SPLIT_WING_RELATION_CONTRACT.minimum_public_gap_ratio,
        )
        self.assertEqual(
            project_book_split_gap_ratio(source_high),
            SPLIT_WING_RELATION_CONTRACT.maximum_public_gap_ratio,
        )
        split = next(
            program for program in architectural_shape_programs()
            if program.metadata.get("family") == "split_bridge"
        )
        split_node = next(node for node in split.nodes if node.operator == "split_wing")
        self.assertEqual(
            split_node.parameters["gap_ratio"],
            SPLIT_WING_RELATION_CONTRACT.default_public_gap_ratio,
        )

    def test_program_profile_reserves_one_body_rule_for_book_projection(self):
        request = {
            **synthesis_requests_from_program_profile(
                "neighborhood living",
                source_seeds=("lineage-a",),
                candidates_per_lineage=24,
            )[0],
            "site_access_side": "west",
        }
        programs = synthesize_architectural_programs(
            request,
            building_type="neighborhood living",
        )
        body_operators = {
            "bend", "bent_bar", "twist", "inflate", "pinch", "taper",
            "shear", "setback", "stepped_mass", "terrace", "puncture",
            "cut_corner", "slice", "radial_array", "cross_mass", "grid_mass",
            "split_wing", "cantilever", "lift",
        }
        for program in programs:
            path = list(program.metadata["operator_path"])
            body_nodes = [
                node
                for node in program.topological_nodes()
                if node.operator in body_operators
                and not (
                    node.operator in {"lift", "split_wing"}
                    and str(node.parameters.get("access_side") or "closed") != "closed"
                )
            ]
            self.assertLessEqual(
                len(body_nodes),
                1,
                path,
            )
            self.assertLessEqual(
                sum(operator in {"courtyard", "carve_void", "notch"} for operator in path),
                1,
                path,
            )

    def test_program_profile_synthesis_materializes_required_access_relation_and_program_macro(self):
        for building_type in ("neighborhood living", "gymnasium", "cultural"):
            request = {
                **synthesis_requests_from_program_profile(
                    building_type,
                    source_seeds=("lineage-a",),
                    candidates_per_lineage=6,
                )[0],
                "site_access_side": "west",
            }
            programs = synthesize_architectural_programs(
                request,
                building_type=building_type,
            )
            self.assertEqual(len(programs), 6)
            allowed_macros = set(request["allowed_macro_operators"])
            for program in programs:
                nodes = program.topological_nodes()
                macros = {node.operator for node in nodes if node.kind == "macro"}
                self.assertTrue(macros.issubset(allowed_macros))
                access_nodes = [
                    node for node in nodes
                    if node.operator in {"courtyard", "carve_void", "notch", "lift", "split_wing"}
                ]
                self.assertTrue(access_nodes)
                self.assertTrue(any(
                    node.parameters.get("open_side") == "west"
                    or node.parameters.get("side") == "west"
                    or node.parameters.get("access_side") == "west"
                    for node in access_nodes
                ))
                if building_type == "gymnasium":
                    self.assertIn("profiled_hall", macros)
                self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_access_bound_lift_uses_one_connected_back_service_spine(self):
        programs = synthesize_architectural_programs({
            "base_seeds": ["slab"],
            "intent_tags": ["lifted_ground"],
            "candidate_count": 8,
            "maximum_operator_depth": 1,
            "allowed_macro_operators": ["lift"],
            "required_access_bound_relation": True,
            "site_access_side": "west",
        }, building_type="neighborhood living")
        lifted = next(
            program for program in programs
            if "lift" in program.metadata["operator_path"]
        )
        lift_node = next(node for node in lifted.nodes if node.operator == "lift")
        self.assertEqual(lift_node.parameters["access_side"], "west")
        compilation = compile_geometry_program(lifted)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertIn(
            "access_bound_service_spine",
            {item for row in compilation.trace for item in row["macro_expansion"]},
        )
        context = {
            **program_reference_contract("neighborhood_living"),
            "site_access_side_in_program_frame": "west",
            "site_access_context": {"primary_access_edge": "west", "road_width_m": 6.0},
        }
        self.assertEqual(
            geometry_llm_adapter._misaligned_access_relation(lifted, context),
            "",
        )
        snapshot = build_geometry_graph_snapshot(
            lifted,
            compilation,
            program_context=context,
        )
        source = SimpleNamespace(metadata={
            "geometry_program": lifted.to_dict(),
            "program_context": context,
            "geometry_graph_snapshot": snapshot,
        })
        descriptor = _design_concept_descriptor(source)
        self.assertEqual(descriptor["ground_strategy"], "frontage_lifted_threshold")
        self.assertEqual(
            descriptor["frontage_aligned_controller_node_ids"],
            [lift_node.id],
        )

    def test_program_profile_control_explores_its_executable_macro_contract(self):
        request = {
            **synthesis_requests_from_program_profile(
                "neighborhood living",
                source_seeds=("lineage-a",),
                candidates_per_lineage=24,
            )[0],
            "site_access_side": "west",
        }
        programs = synthesize_architectural_programs(
            request,
            building_type="neighborhood living",
        )
        explored = {
            node.operator
            for program in programs
            for node in program.nodes
        }

        # These are materially different plan/section languages from the
        # advertised program contract, not parameter variants of one notch.
        self.assertTrue({
            "cross_mass", "split_wing", "stepped_mass", "cut_corner",
            "bent_bar", "courtyard",
        }.issubset(explored), explored)

    def test_universal_form_bank_precedes_program_and_covers_every_chassis(self):
        from collections import Counter

        from design.maas.geometry_language.universal_form_bank import (
            universal_form_bank_contract,
            universal_form_programs,
        )

        contract = universal_form_bank_contract()
        programs = universal_form_programs()
        chassis = {
            str(program.metadata.get("early_typology_prior") or "")
            for program in programs
            if str(program.metadata.get("early_typology_prior") or "")
        }

        self.assertFalse(contract["program_conditioned"])
        self.assertEqual(contract["stage_order"][:5], (
            "base_seed", "chassis", "base_volume", "book_principle", "book_variation",
        ))
        self.assertEqual(contract["stage_order"][5:], (
            "program_projection", "capacity_alternative_projection", "hard_gates", "live_vlm",
        ))
        self.assertEqual(len(programs), 82)
        self.assertEqual(contract["synthesis_lane_program_count"], 64)
        self.assertEqual(contract["replenishment_page_size"], 64)
        self.assertEqual(
            contract["replenishment_rule"],
            "advance_low_discrepancy_geometry_program_page",
        )
        self.assertEqual(contract["executable_core_lane_program_count"], 18)
        self.assertEqual(contract["operator_sampling"], "balanced_unique_round_robin")
        self.assertTrue({
            "l_mass", "u_mass", "attached_volume", "overlapping_mass",
            "swept_bar", "split_bridge",
        }.issubset({str(program.metadata.get("family") or "") for program in programs}))
        self.assertEqual(
            chassis,
            {prior.typology_id for prior in TYPOLOGY_PRIORS},
        )
        self.assertTrue(all(not program.metadata["program_conditioned"] for program in programs))
        compilations = [compile_geometry_program(program) for program in programs]
        self.assertTrue(all(item.status == "compiled" for item in compilations))
        self.assertTrue(all(item.metrics["component_count"] == 1 for item in compilations))
        synthesis_family_counts = Counter(
            str(program.metadata.get("family") or "")
            for program in programs
            if program.metadata.get("form_bank_lane") == "bounded_synthesis"
        )
        self.assertEqual(sum(synthesis_family_counts.values()), 64)
        self.assertLessEqual(max(synthesis_family_counts.values()), 5)
        self.assertLessEqual(synthesis_family_counts["agent_profiled_hall"], 2)
        self.assertLessEqual(synthesis_family_counts["agent_split_wing"], 3)

    def test_universal_form_bank_replenishment_page_authors_new_geometry_programs(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        baseline = universal_form_programs(0)
        replenishment = universal_form_programs(1)
        baseline_hashes = {program.program_hash() for program in baseline}
        replenishment_hashes = {program.program_hash() for program in replenishment}

        self.assertEqual(len(baseline), 82)
        self.assertEqual(len(replenishment), 64)
        self.assertTrue(all(
            program.metadata.get("form_bank_variation_page") == 1
            for program in replenishment
        ))
        # A low-discrepancy boundary may land on one identical normalized
        # parameter tuple; the page must still contribute a genuinely new
        # population rather than replaying all 82 baseline payloads.
        self.assertGreaterEqual(len(replenishment_hashes - baseline_hashes), 63)

    def test_universal_relational_families_rotate_beyond_thin_bar_chassis(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        relational = [
            program for program in universal_form_programs()
            if set(program.metadata.get("operator_path") or ())
            & {"bent_bar", "split_wing", "cross_mass", "grid_mass"}
        ]
        seeds = {str(program.metadata.get("base_seed") or "") for program in relational}

        self.assertIn("bar", seeds)
        self.assertIn("slab", seeds)
        self.assertIn("profiled_prism", seeds)

    def test_default_dominant_form_supply_is_identical_before_program_projection(self):
        from design.maas.book_language.candidate_generation import _agent_mutated_seeds

        def payloads(building_type):
            seeds = _agent_mutated_seeds(building_type, mutations=None)
            return {
                note.split("=", 1)[1]
                for seed in seeds
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            }, {
                note.split("=", 1)[1]
                for seed in seeds
                for note in seed.notes
                if note.startswith("geometry_program_synthesis_request_source=")
            }

        neighborhood_payloads, neighborhood_sources = payloads("neighborhood living")
        gym_payloads, gym_sources = payloads("gymnasium")
        cultural_payloads, cultural_sources = payloads("cultural")

        self.assertEqual(neighborhood_payloads, gym_payloads)
        self.assertEqual(gym_payloads, cultural_payloads)
        self.assertEqual(len(gym_payloads), 82)
        self.assertEqual(neighborhood_sources, {"universal_form_bank_control"})
        self.assertEqual(gym_sources, {"universal_form_bank_control"})
        self.assertEqual(cultural_sources, {"universal_form_bank_control"})

    def test_replenishment_seed_supply_uses_requested_geometry_variation_page(self):
        from design.maas.book_language.candidate_generation import _agent_mutated_seeds

        def payloads(page: int):
            seeds = _agent_mutated_seeds(
                "neighborhood living",
                mutations=None,
                universal_variation_pages=(page,),
            )
            return ({
                note.split("=", 1)[1]
                for seed in seeds
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            }, {
                note.split("=", 1)[1]
                for seed in seeds
                for note in seed.notes
                if note.startswith("geometry_program_form_bank_page=")
            })

        baseline_payloads, baseline_pages = payloads(0)
        replenishment_payloads, replenishment_pages = payloads(1)

        self.assertEqual(len(baseline_payloads), 82)
        self.assertEqual(len(replenishment_payloads), 64)
        self.assertFalse(baseline_payloads & replenishment_payloads)
        self.assertEqual(baseline_pages, {"0"})
        self.assertEqual(replenishment_pages, {"1"})

    def test_post_book_program_projection_adds_relations_not_base_forms(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        base = universal_form_programs()[0]
        base_hash = base.program_hash()
        rows = {}
        for building_type in ("neighborhood living", "gymnasium", "cultural"):
            projected = project_program_requirements(
                base,
                building_type=building_type,
                access_side="south",
            )
            compilation = compile_geometry_program(projected)
            evidence = projected.metadata["program_projection"]
            threshold = projected.node_map[evidence["threshold_controller_node_id"]]
            rows[building_type] = projected

            self.assertEqual(evidence["pre_program_projection_hash"], base_hash)
            self.assertEqual(projected.metadata["program_projection_stage"], "post_book")
            self.assertTrue(evidence["universal_form_preserved"])
            self.assertFalse(evidence["base_or_book_authority"])
            self.assertEqual(threshold.provenance["source"], "post_book_program_projection")
            self.assertEqual(threshold.provenance["program_conditioning_stage"], "after_book")
            self.assertIn("south", threshold.parameters.values())
            self.assertEqual(compilation.status, "compiled")
            self.assertEqual(compilation.metrics["component_count"], 1)

        gym = rows["gymnasium"]
        hall = next(node for node in gym.nodes if (
            node.operator == "profiled_hall"
            and node.provenance.get("source") == "post_book_program_projection"
        ))
        self.assertEqual(hall.semantic_role, "program_section_invariant")
        self.assertFalse(any(
            node.operator == "profiled_hall"
            and node.provenance.get("source") == "post_book_program_projection"
            for node in rows["neighborhood living"].nodes
        ))

    def test_program_projection_resolves_access_and_section_concept_controllers(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        for building_type in ("neighborhood living", "gymnasium", "cultural"):
            projected = project_program_requirements(
                universal_form_programs()[0],
                building_type=building_type,
                access_side="east",
            )
            compilation = compile_geometry_program(projected)
            context = {
                **program_reference_contract(building_type),
                "site_access_context": {"primary_access_edge": "verified-edge"},
                "site_access_side_in_program_frame": "east",
            }
            graph = build_geometry_graph_snapshot(
                projected,
                compilation,
                program_context=context,
            )["design_concept_graph"]
            concepts = {
                item["concept_id"]: item
                for item in graph["concept_nodes"]
            }
            self.assertFalse(concepts["concept:public_threshold"]["missing_controller"])
            self.assertTrue(
                concepts["concept:public_threshold"]["frontage_aligned_controller_node_ids"]
            )
            if building_type == "gymnasium":
                self.assertFalse(
                    concepts["concept:structure_daylight_section"]["missing_controller"]
                )

    def test_program_projection_opens_existing_court_without_stacking_a_notch(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        court = next(
            program for program in universal_form_programs()
            if str(program.metadata.get("family") or "") == "agent_courtyard"
        )
        before_threshold_count = sum(
            node.operator in {"courtyard", "carve_void", "notch", "lift", "split_wing"}
            for node in court.nodes
        )
        projected = project_program_requirements(
            court,
            building_type="neighborhood living",
            access_side="west",
        )
        evidence = projected.metadata["program_projection"]
        threshold = projected.node_map[evidence["threshold_controller_node_id"]]

        self.assertEqual(evidence["threshold_status"], "rebound_existing_final_ast_controller")
        self.assertEqual(threshold.operator, "courtyard")
        self.assertEqual(threshold.parameters["open_side"], "west")
        self.assertGreaterEqual(threshold.parameters["margin_ratio"], 0.18)
        self.assertLessEqual(threshold.parameters["margin_ratio"], 0.24)
        self.assertEqual(
            sum(
                node.operator in {"courtyard", "carve_void", "notch", "lift", "split_wing"}
                for node in projected.nodes
            ),
            before_threshold_count,
        )
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)

    def test_neighborhood_projection_strengthens_existing_notch_from_program_contract(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        notched = next(
            program for program in universal_form_programs()
            if any(node.operator == "notch" for node in program.nodes)
        )
        projected = project_program_requirements(
            notched,
            building_type="neighborhood living",
            access_side="west",
        )
        evidence = projected.metadata["program_projection"]
        threshold = projected.node_map[evidence["threshold_controller_node_id"]]

        self.assertEqual(threshold.operator, "notch")
        self.assertEqual(threshold.parameters["side"], "west")
        self.assertGreaterEqual(threshold.parameters["ratio"], 0.28)
        self.assertGreaterEqual(threshold.parameters["width_ratio"], 0.38)
        self.assertGreaterEqual(threshold.parameters["height_ratio"], 0.58)
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)

    def test_neighborhood_projection_reuses_substantial_threshold_as_public_space(self):
        base = base_seed_programs()[0]
        base_hash = base.program_hash()
        projected = project_program_requirements(
            base,
            building_type="neighborhood living",
            access_side="west",
        )
        evidence = projected.metadata["program_projection"]
        public_space = projected.node_map[evidence["public_space_controller_node_id"]]
        threshold = projected.node_map[evidence["threshold_controller_node_id"]]

        self.assertEqual(
            evidence["public_space_status"],
            "reused_program_threshold_as_public_space",
        )
        self.assertIn(public_space.operator, {"courtyard", "carve_void", "lift", "split_wing"})
        self.assertEqual(public_space.semantic_role, "public_threshold")
        self.assertEqual(public_space.id, threshold.id)
        self.assertEqual(evidence["pre_program_projection_hash"], base_hash)
        self.assertTrue(evidence["universal_form_preserved"])
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)

    def test_program_projection_does_not_stack_split_wing_on_radial_or_lifted_twist(self):
        programs = {
            program.metadata.get("family"): program
            for program in architectural_shape_programs()
        }
        radial = project_program_requirements(
            programs["radial_fan"],
            building_type="neighborhood living",
            access_side="west",
        )
        twisted = project_program_requirements(
            programs["twisted_mass"],
            building_type="neighborhood living",
            access_side="west",
        )

        self.assertEqual(
            radial.metadata["program_projection"]["public_space_status"],
            "reused_substantial_frontage_cut_as_public_space",
        )
        self.assertEqual(
            twisted.metadata["program_projection"]["public_space_status"],
            "reused_program_threshold_as_public_space",
        )
        for projected in (radial, twisted):
            self.assertFalse(any(
                node.operator == "split_wing"
                and node.provenance.get("source") == "post_book_program_projection"
                for node in projected.nodes
            ))
            self.assertEqual(
                compile_geometry_program(projected).metrics["component_count"],
                1,
            )

    def test_book_split_never_impersonates_a_program_controller(self):
        from dataclasses import replace

        from design.maas.geometry_language.ast import GeometryNode
        from design.maas.geometry_language.base_seeds import base_seed_programs
        from design.maas.geometry_language.program_controller_contract import (
            is_materialized_program_controller,
        )

        base = base_seed_programs()[0]
        book_split = GeometryNode(
            id="book_probe_split",
            kind="macro",
            operator="book_split",
            inputs=(base.root_id,),
            parameters={
                "axis": "x",
                "gap_ratio": 0.16,
                "terminal_ratio": 0.54,
                "angle_degrees": 14.0,
                "outward_sign": 1.0,
                "branch_sign": 1.0,
                "split_generation": 0,
                "access_side": "west",
            },
            semantic_role="book_mutated_dominant",
            provenance={
                "source": "book_recursive_projection",
                "book_verb": "split",
                "normalized_parameters_only": True,
            },
        )
        book_program = replace(
            base,
            nodes=(*base.nodes, book_split),
            root_id=book_split.id,
        )
        projected = project_program_requirements(
            book_program,
            building_type="neighborhood living",
            access_side="west",
        )
        evidence = projected.metadata["program_projection"]
        controller = projected.node_map[evidence["threshold_controller_node_id"]]

        self.assertFalse(is_materialized_program_controller(book_split))
        self.assertNotEqual(controller.id, book_split.id)
        self.assertEqual(
            projected.node_map[book_split.id].provenance["source"],
            "book_recursive_projection",
        )
        self.assertEqual(controller.provenance["source"], "post_book_program_projection")
        self.assertEqual(compile_geometry_program(projected).status, "compiled")
        self.assertEqual(compile_geometry_program(projected).metrics["component_count"], 1)

    def test_program_projection_keeps_all_universal_forms_connected(self):
        from design.maas.geometry_language.universal_form_bank import universal_form_programs

        results = [
            compile_geometry_program(project_program_requirements(
                program,
                building_type=building_type,
                access_side="west",
            ))
            for building_type in ("neighborhood living", "gymnasium", "cultural")
            for program in universal_form_programs()
        ]
        self.assertTrue(all(result.status == "compiled" for result in results))
        self.assertTrue(all(result.metrics["component_count"] == 1 for result in results))

    def test_long_span_split_wing_has_normalized_ground_service_spine(self):
        programs = synthesize_architectural_programs({
            "base_seeds": ["bar", "slab", "block"],
            "intent_tags": ["long_span", "distributed_wings"],
            "candidate_count": 18,
            "maximum_operator_depth": 2,
        }, building_type="gymnasium")
        wing = next(
            program for program in programs
            if "split_wing" in program.metadata["operator_path"]
        )
        node = next(node for node in wing.nodes if node.operator == "split_wing")

        self.assertTrue(node.parameters["ground_spine"])
        self.assertGreaterEqual(node.parameters["ground_spine_width_ratio"], 0.30)
        compilation = compile_geometry_program(wing)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)

        host = box(0, 0, 60, 40)
        source = compile_geometry_program_to_source_mass(
            wing,
            host,
            target_plan_area=host.area * 0.58,
        )
        self.assertIsNotNone(source)
        assert source is not None
        self.assertTrue(all(host.covers(volume.footprint) for volume in source.volumes))
        self.assertGreater(source.footprint.area / host.area, 0.35)

    def test_source_bridge_does_not_let_legal_upper_frame_author_a_wedge_by_default(self):
        program = next(
            item for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "") == "block"
        )
        source = compile_geometry_program_to_source_mass(
            program,
            box(0, 0, 30, 20),
            upper_host=box(8, 5, 24, 17),
        )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(bridge["legal_fit_strength"], 0.0)
        self.assertEqual(bridge["legal_fit_mode"], "principal_frame_bounded")
        for surface in source.surfaces:
            if surface.surface_type != "profiled_recursive_solid_mesh":
                continue
            a, b, c = surface.vertices_m[:3]
            ux, uy, uz = (b[index] - a[index] for index in range(3))
            vx, vy, vz = (c[index] - a[index] for index in range(3))
            nx, ny, nz = (
                uy * vz - uz * vy,
                uz * vx - ux * vz,
                ux * vy - uy * vx,
            )
            magnitude = (nx * nx + ny * ny + nz * nz) ** 0.5
            if magnitude > 1e-9:
                self.assertTrue(
                    abs(nz / magnitude) <= 1e-6
                    or abs(nz / magnitude) >= 1.0 - 1e-6
                )

    def test_source_bridge_records_convex_hull_capacity_shortfall_without_erasing_language(self):
        bar = next(
            item for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "") == "bar"
        )
        host = box(0, 0, 30, 20)

        feasible = compile_geometry_program_to_source_mass(
            bar,
            host,
            minimum_plan_area=host.area * 0.50,
        )
        impossible = compile_geometry_program_to_source_mass(
            bar,
            host,
            minimum_plan_area=host.area * 0.95,
        )

        self.assertIsNotNone(feasible)
        self.assertIsNotNone(impossible)
        feasible_bridge = feasible.metadata["geometry_program_bridge_evidence"]
        impossible_bridge = impossible.metadata["geometry_program_bridge_evidence"]
        self.assertTrue(feasible_bridge["minimum_plan_area_target_satisfied"])
        self.assertFalse(impossible_bridge["minimum_plan_area_target_satisfied"])
        self.assertGreater(
            impossible_bridge["minimum_plan_area_shortfall_ratio"],
            0.0,
        )
        self.assertLess(
            impossible_bridge["achieved_mesh_plan_projection_area"],
            impossible_bridge["minimum_plan_area_target"],
        )

    def test_mesh_projection_geos_failure_is_a_conservative_candidate_failure(self):
        vertices = (
            (0.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (0.0, 3.0, 0.0),
            (4.0, 3.0, 0.0),
        )
        triangles = ((0, 1, 2), (1, 3, 2))

        with patch.object(
            source_bridge_module,
            "unary_union",
            side_effect=GEOSException("TopologyException: Ring edge missing"),
        ):
            area = source_bridge_module._mesh_plan_projection_area(vertices, triangles)

        # The full rectangle is 12 m2.  On repeated GEOS failure the bridge
        # reports one valid triangle (6 m2), never a fabricated larger area.
        self.assertEqual(area, 6.0)

    def test_outcome_graph_retrieves_successful_genotype_without_neo4j(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["slab"],
            "intent_tags": ["continuous_curve"],
            "candidate_count": 1,
        }, building_type="gymnasium")[0]
        source = compile_geometry_program_to_source_mass(
            program,
            Polygon(((0, 0), (24, 0), (24, 18), (0, 18))),
            upper_fit_strength=0.4,
        )
        self.assertIsNotNone(source)
        source.metadata["geometry_program_bridge_evidence"]["source_seed"] = "program_gym_folded_service_hall"
        candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="program_gym_folded_service_hall__book_probe"),
            principle_id="book:operative:bend",
        )
        report = {"rows": [{
            "combined_hard_pass": True,
            "legal_projection": {
                "hard_pass": True,
                "geometry_retention_pass": True,
                "volume_retention": 0.91,
                "geometry_failure_reasons": [],
            },
            "parking_hard_gate": {"hard_pass": True},
        }]}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "outcome-graph.json"
            graph = GeometryOutcomeGraph.load(path, pnu="test-pnu")
            graph.observe_candidates(
                program_slug="gymnasium",
                candidates=[candidate],
                downstream_report=report,
                selected=[candidate],
            )
            payload = graph.save()
            loaded = GeometryOutcomeGraph.load(path, pnu="test-pnu")
            strengths = loaded.preferred_strengths(
                source_seed="program_gym_folded_service_hall",
                program_hash=program.program_hash(),
                fallback=[0.0, 0.8],
            )
            loaded.begin_program_run("gymnasium")
        self.assertGreater(payload["node_count"], 0)
        self.assertGreater(payload["edge_count"], 0)
        self.assertEqual(strengths, (0.4,))
        self.assertFalse(any(item.get("selected") for item in loaded.observations))
        self.assertFalse(any(
            item["attributes"].get("selected")
            for item in loaded.nodes.values()
            if item["kind"] == "outcome"
        ))

    def test_selection_only_refresh_preserves_observed_downstream_gate_evidence(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["slab"],
            "intent_tags": ["continuous_curve"],
            "candidate_count": 1,
        }, building_type="gymnasium")[0]
        source = compile_geometry_program_to_source_mass(
            program,
            Polygon(((0, 0), (24, 0), (24, 18), (0, 18))),
            upper_fit_strength=0.4,
        )
        self.assertIsNotNone(source)
        source.metadata["geometry_program_bridge_evidence"]["source_seed"] = "selection-refresh-seed"
        candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="selection-refresh-seed__book_probe"),
            principle_id="book:operative:bend",
        )
        displaced_candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="selection-refresh-seed__book_probe"),
            principle_id="book:operative:expand",
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.observe_candidates(
            program_slug="gymnasium",
            candidates=[candidate, displaced_candidate],
            downstream_report={"rows": [
                {
                    "combined_hard_pass": True,
                    "legal_projection": {
                        "hard_pass": True,
                        "geometry_retention_pass": True,
                        "volume_retention": 0.91,
                        "geometry_failure_reasons": [],
                    },
                    "parking_hard_gate": {"hard_pass": True},
                },
                {
                    "combined_hard_pass": True,
                    "legal_projection": {
                        "hard_pass": True,
                        "geometry_retention_pass": True,
                        "volume_retention": 0.88,
                        "geometry_failure_reasons": [],
                    },
                    "parking_hard_gate": {"hard_pass": True},
                },
            ]},
            selected=[displaced_candidate],
        )

        graph.observe_candidates(
            program_slug="gymnasium",
            candidates=[candidate],
            downstream_report=None,
            selected=[candidate],
        )

        self.assertEqual(len(graph.observations), 2)
        observation = next(
            item
            for item in graph.observations
            if item["book_principle_id"] == "book:operative:bend"
        )
        displaced = next(
            item
            for item in graph.observations
            if item["book_principle_id"] == "book:operative:expand"
        )
        self.assertTrue(observation["selected"])
        self.assertTrue(observation["combined_hard_pass"])
        self.assertTrue(observation["legal_hard_pass"])
        self.assertTrue(observation["geometry_retention_pass"])
        self.assertEqual(observation["volume_retention"], 0.91)
        self.assertTrue(observation["parking_hard_pass"])
        self.assertFalse(displaced["selected"])
        self.assertTrue(displaced["combined_hard_pass"])
        self.assertEqual(displaced["volume_retention"], 0.88)
        outcome_nodes = {
            item["identity"]: item["attributes"]
            for item in graph.nodes.values()
            if item["kind"] == "outcome"
        }
        self.assertTrue(outcome_nodes[observation["id"]]["selected"])
        self.assertFalse(outcome_nodes[displaced["id"]]["selected"])

    def test_outcome_graph_explores_unseen_fit_then_exploits_lowest_success(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.observations = [{
            "source_seed": "hall",
            "program_hash": "program-hash",
            "legal_fit_strength": 0.0,
            "program_hard_pass": False,
            "combined_hard_pass": False,
            "volume_retention": 0.0,
        }]
        self.assertEqual(
            graph.preferred_strengths(
                source_seed="hall", program_hash="program-hash",
                fallback=[0.0, 0.4, 0.8], limit=2,
            ),
            (0.0, 0.4),
        )
        graph.observations[0].update({
            "program_hard_pass": True,
            "combined_hard_pass": True,
            "volume_retention": 0.93,
        })
        self.assertEqual(
            graph.preferred_strengths(
                source_seed="hall", program_hash="program-hash",
                fallback=[0.0, 0.4, 0.8], limit=2,
            ),
            (0.0,),
        )

    def test_outcome_graph_supplies_source_level_priors_to_new_llm_author(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.nodes = {
            "program-node": {
                "kind": "geometry_program",
                "identity": "program-hash",
                "attributes": {
                    "base_seed": "bar",
                    "operator_path": ["bend", "courtyard"],
                    "intent_tags": ["continuous_curve", "carved_void"],
                },
            }
        }
        graph.observations = [
            {
                "source_seed": "active-bar",
                "program_slug": "neighborhood_living",
                "program_hash": "program-hash",
                "program_hard_pass": True,
                "combined_hard_pass": True,
                "final_book_vlm_hard_pass": True,
                "reference_assessments": [{
                    "source_id": "archdaily-gym-1",
                    "program_relevance": 0.86,
                    "transferable_principle": "one dominant span with a carved public threshold",
                    "mismatch_warning": "",
                }],
            },
            {
                "source_seed": "active-bar",
                "program_slug": "neighborhood_living",
                "program_hash": "program-hash",
                "program_hard_pass": False,
                "failed_program_gates": ["coherence"],
                "failed_final_book_vlm_gates": ["final_book_vlm_too_fragmented"],
            },
            {
                "stage": "final_book_vlm",
                "source_seed": "active-bar",
                "program_slug": "neighborhood",
                "program_hash": "projected-program-hash",
                "final_book_vlm_hard_pass": False,
                "book_principle_id": "book:operative:split",
                "book_scope": "1/4",
                "critic_actions": ["too_fragmented"],
                "geometry_edits": [{
                    "operation": "set_parameter",
                    "target_node_id": "old-book-node",
                    "parameter_name": "gap_ratio",
                    "numeric_value": 0.18,
                }],
                "failed_final_book_vlm_gates": ["final_book_vlm_too_fragmented"],
            },
        ]
        context = graph.author_context(
            source_seed="active-bar",
            program_slug="neighborhood_living",
            program_aliases=("neighborhood",),
        )
        self.assertEqual(context["observation_count"], 3)
        self.assertEqual(context["program_aliases"], ["neighborhood", "neighborhood_living"])
        self.assertEqual(context["successful_genotype_priors"][0]["base_seed"], "bar")
        self.assertEqual(
            context["successful_genotype_priors"][0]["operator_path"],
            ["bend", "courtyard"],
        )
        self.assertEqual(context["common_authored_body_failures"][0]["gate"], "coherence")
        self.assertEqual(
            context["conditional_book_projection_failures"][0]["attribution"],
            "book_projection_context_not_global_author_failure",
        )
        repair = context["transferable_projection_repair_priors"][0]
        self.assertTrue(repair["node_ids_removed"])
        self.assertEqual(repair["edit_intents"][0]["parameter_name"], "gap_ratio")
        self.assertNotIn("target_node_id", repair["edit_intents"][0])
        reference_prior = context["reference_relation_priors"][0]
        self.assertEqual(reference_prior["provenance"], "image_grounded_reference_vlm_assessment")
        self.assertNotIn("coordinates", reference_prior)

    def test_outcome_graph_returns_board_level_repetition_to_next_author(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.observe_portfolio_vlm_audit(
            program_slug="gymnasium",
            candidate_geometry_hashes=("geometry-a", "geometry-b"),
            audit={
                "response_id": "portfolio-response",
                "model": "test-vlm",
                "hard_pass": False,
                "candidate_count": 20,
                "visible_family_count": 4,
                "dominant_family_share": 0.55,
                "failure_reasons": ["repeated_roof", "pyramid_dominated"],
                "repeated_family_groups": [{
                    "candidate_ids": ["maas_01", "maas_02"],
                    "shared_language": "stepped pyramidal roof",
                    "severity": "high",
                }],
                "required_next_relations": ["long span hall plus daylight monitor"],
                "required_geometry_families": ["split_bridge", "cross_mass"],
                "geometry_family_action_counts": {
                    "agent_profiled_hall": {"keep": 1, "replace": 4},
                },
                "overrepresented_geometry_families": ["agent_profiled_hall"],
                "chassis_family_action_counts": {
                    "recursive_chassis:courtyard": {"keep": 2, "replace": 2},
                },
                "overrepresented_chassis_families": [
                    "recursive_chassis:courtyard",
                ],
                "underrepresented_chassis_families": [
                    "recursive_chassis:radial_wings",
                    "recursive_chassis:twisted_tower",
                ],
            },
        )

        context = graph.author_context(source_seed="hall", program_slug="gymnasium")
        feedback = context["portfolio_visual_feedback"][0]
        self.assertEqual(feedback["visible_family_count"], 4)
        self.assertEqual(feedback["attribution"], "final_sibling_board_not_individual_candidate")
        self.assertEqual(
            feedback["required_next_relations"],
            ["long span hall plus daylight monitor"],
        )
        self.assertEqual(
            feedback["required_geometry_families"],
            ["split_bridge", "cross_mass"],
        )
        directive = graph.latest_portfolio_directive("gymnasium")
        self.assertEqual(directive["status"], "materialized")
        self.assertEqual(
            directive["required_geometry_program_families"],
            ["split_bridge", "cross_mass"],
        )
        self.assertEqual(
            directive["max_geometry_family_counts"],
            {"agent_profiled_hall": 1},
        )
        self.assertEqual(
            directive["max_chassis_family_counts"],
            {"recursive_chassis:courtyard": 2},
        )
        self.assertEqual(
            directive["required_chassis_families"],
            ["recursive_chassis:radial_wings", "recursive_chassis:twisted_tower"],
        )
        self.assertEqual(directive["max_chassis_family_count"], 0)
        self.assertEqual(
            graph.latest_portfolio_directive("cultural")["status"],
            "no_prior_portfolio_vlm",
        )
        graph.observe_portfolio_vlm_audit(
            program_slug="gymnasium",
            candidate_geometry_hashes=("geometry-c",),
            audit={
                "response_id": "later-portfolio-response",
                "hard_pass": False,
                "required_geometry_families": ["courtyard"],
            },
        )
        self.assertEqual(
            graph.latest_portfolio_directive("gymnasium")["required_geometry_program_families"],
            ["courtyard"],
        )
        self.assertEqual(
            graph.latest_portfolio_directive("gymnasium")["max_geometry_family_counts"],
            {"agent_profiled_hall": 1},
        )
        self.assertEqual(
            graph.latest_portfolio_directive("gymnasium")["max_chassis_family_counts"],
            {"recursive_chassis:courtyard": 2},
        )
        self.assertTrue(any(
            edge["kind"] == "reviewed_as_board_by" for edge in graph.edges.values()
        ))

    def test_outcome_graph_rederives_missing_chassis_for_older_board_observation(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.observe_portfolio_vlm_audit(
            program_slug="neighborhood",
            candidate_geometry_hashes=("geometry-a",),
            audit={
                "response_id": "old-board-response",
                "hard_pass": False,
                "chassis_family_action_counts": {
                    "recursive_chassis:courtyard": {"keep": 1, "replace": 0},
                },
            },
        )

        with patch(
            "design.maas.geometry_language.outcome_graph.core_chassis_families",
            return_value=("courtyard", "radial_wings"),
        ):
            directive = graph.latest_portfolio_directive("neighborhood")

        self.assertEqual(
            directive["required_chassis_families"],
            ["recursive_chassis:radial_wings"],
        )

    def test_outcome_graph_persists_pre_program_clean_failure_for_next_author(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        program = base_seed_programs()[1]
        graph.observe_geometry_gate_failure(
            program_slug="neighborhood",
            source_seed="active-bar",
            program=program,
            principle_id="book:aggregation:array:rotate",
            book_scope="1/4",
            stage="clean_mass",
            failure_reasons=("disconnected_mesh_component_count",),
        )

        context = graph.author_context(
            source_seed="active-bar",
            program_slug="neighborhood",
        )
        self.assertEqual(context["observation_count"], 1)
        self.assertEqual(
            context["common_authored_body_failures"][0],
            {"gate": "disconnected_mesh_component_count", "count": 1},
        )
        observation = graph.observations[0]
        self.assertEqual(observation["stage"], "geometry_gate")
        self.assertEqual(observation["geometry_gate_stage"], "clean_mass")
        self.assertFalse(observation["program_hard_pass"])

    def test_outcome_graph_retrieves_scope_balanced_book_neighborhood(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.observations = [
            {
                "source_seed": "hall", "program_hash": "hash",
                "book_principle_id": f"book:operative:{scope_index}",
                "book_scope": scope, "program_hard_pass": True,
                "combined_hard_pass": True, "volume_retention": 0.9,
            }
            for scope_index, scope in enumerate(("1/1", "3/8", "1/2", "1/4", "1/8", "1/16"))
        ]
        selected = graph.preferred_book_principle_ids(
            source_seed="hall", program_hash="hash",
            fallback=("book:aggregation:array:taper",), limit=6,
        )
        self.assertEqual(len(selected), 6)
        self.assertEqual(
            {next(item["book_scope"] for item in graph.observations if item["book_principle_id"] == principle) for principle in selected},
            {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"},
        )

    def test_archdaily_retrieval_is_image_backed_and_includes_counterfactual(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["bar"],
            "intent_tags": ["long_span", "continuous_curve", "carved_void"],
            "candidate_count": 1,
        }, building_type="gymnasium")[0]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            records = [
                {"source": "archdaily_api", "source_id": "hall-1", "title": "Long span sports hall", "local_path": str(root / "hall-1.jpg"), "tags": ["bar", "slender", "long_span"]},
                {"source": "archdaily_api", "source_id": "hall-2", "title": "Carved arena court", "local_path": str(root / "hall-2.jpg"), "tags": ["void", "carve", "court"]},
                {"source": "archdaily_api", "source_id": "hall-3", "title": "Sports bridge field", "local_path": str(root / "hall-3.jpg"), "tags": ["sports", "twist", "bridge", "field"]},
                {"source": "archdaily_api", "source_id": "hall-4", "title": "Gym folded daylight roof", "local_path": str(root / "hall-4.jpg"), "tags": ["gym", "folded", "section", "roof"]},
            ]
            for record in records:
                Path(record["local_path"]).touch()
            (root / "metadata.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            matches = retrieve_geometry_reference_matches(
                program,
                building_type="gymnasium",
                reference_root=root,
                limit=5,
            )
        self.assertGreaterEqual(len(matches), 3)
        self.assertTrue(all(item.get("local_path") or item.get("image_url") for item in matches))
        self.assertTrue(all(str(item.get("source") or "").startswith("archdaily") for item in matches[:3]))
        self.assertTrue(all(item["reference_contract"]["hard_pass"] for item in matches))
        self.assertTrue(all(item["program_id"] == "gymnasium" for item in matches))
        self.assertIn("counterfactual", {item.get("selection_role") for item in matches})

    def test_vlm_receives_outcome_memory_and_causal_reference_trace(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["slab"],
            "intent_tags": ["stepped_section"],
            "candidate_count": 1,
        }, building_type="gymnasium")[0]
        compilation = compile_geometry_program(program)
        memory = {
            "schema_version": "arr.maas.geometry_agent_neighborhood.v1",
            "observation_count": 4,
            "common_failed_gates": [{"gate": "coherence", "count": 2}],
        }
        references = [{
            "source": "archdaily_api", "source_id": "ref-1", "title": "Folded hall",
            "local_path": str(Path(__file__)), "selection_role": "counterfactual",
        }]
        captured = {}

        def fake_scorer(**kwargs):
            captured.update(kwargs)
            return {"score": 0.72, "geometry_edits": [], "model": "fake-vlm", "response_id": "resp-1"}

        with TemporaryDirectory() as directory, patch(
            "design.maas.geometry_language.vlm_adapter.score_candidate_with_openai_vlm",
            side_effect=fake_scorer,
        ), patch(
            "design.maas.geometry_language.vlm_adapter.audit_reference_image_for_massing",
            return_value={
                "schema_version": "arr.maas.reference_image_massing_audit.v1",
                "prompt_contract_version": "test", "provider": "openai", "model": "test",
                "response_id": "reference-audit", "view_type": "exterior_massing",
                "whole_building_visible": True, "massing_legibility": 0.9,
                "operation_clarity": 0.8, "hard_pass": True,
                "failure_reasons": [], "visible_form_traits": ["folded_roof"],
                "cache_hit": False,
            },
        ):
            result = score_geometry_program_with_openai_vlm(
                program,
                compilation,
                Path(directory) / "candidate.png",
                reference_matches=references,
                outcome_memory_context=memory,
            )
        self.assertEqual(
            captured["feature"]["properties"]["outcome_memory_context"]["observation_count"],
            4,
        )
        self.assertEqual(captured["reference_matches"][0]["source_id"], "ref-1")
        self.assertEqual(result["maas_causal_context"]["outcome_memory"]["observation_count"], 4)

    def test_vlm_revision_trace_is_persisted_and_retrievable_by_graph_agent(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.observe_vlm_loop(
            program_slug="gymnasium",
            source_seed="hall",
            trace={"generations": [{"records": [{
                "generation": 0,
                "program": "hall-program",
                "program_hash": "program-hash",
                "geometry_hash": "geometry-before",
                "status": "critic_reviewed",
                "critic_score": 0.78,
                "critic_model": "fake-vlm",
                "critic_response_id": "resp-graph-1",
                "critic_actions": ["needs_profiled_surface"],
                "geometry_edits": [{"operation": "set_parameter", "target_node_id": "roof"}],
                "mutation_status": "mutated",
                "revision_proof": {
                    "child_program_hash": "child-hash",
                    "child_geometry_hash": "geometry-after",
                    "geometry_changed": True,
                },
                "vlm_causal_context": {
                    "reference_matches": [{
                        "source": "archdaily_api", "source_id": "arch-ref-1",
                        "title": "Curved sports hall", "selection_role": "counterfactual",
                    }],
                    "outcome_memory": {"observation_count": 7},
                },
            }]}]},
        )
        memory = graph.agent_neighborhood(source_seed="hall", program_hash="program-hash")
        self.assertEqual(memory["observation_count"], 1)
        self.assertTrue(memory["recent_measured_outcomes"][0]["geometry_changed"])
        self.assertTrue(any(node["kind"] == "vlm_critic" for node in graph.nodes.values()))
        self.assertTrue(any(node["kind"] == "reference" for node in graph.nodes.values()))
        self.assertTrue(any(edge["kind"] == "vlm_revised_to" for edge in graph.edges.values()))
        child_source = SimpleNamespace(metadata={
            "geometry_program": {
                "name": "child",
                "metadata": {"pre_book_program_hash": "child-hash", "family": "profiled_hall"},
            },
            "geometry_program_bridge_evidence": {
                "program_hash": "projected-child",
                "geometry_hash": "final-child-geometry",
                "source_seed": "hall",
            },
            "program_book_projection_evidence": {"scope": {"base_volume_label": "1/2"}},
        })
        graph.observe_final_book_vlm_audit(
            program_slug="gymnasium",
            candidate=SimpleNamespace(
                source=child_source,
                sequence=SimpleNamespace(name="hall__book"),
                principle_id="book:operative:bend",
            ),
            audit={
                "hard_pass": False,
                "failures": ["final_book_vlm_wrong_program_typology"],
                "critic_actions": ["wrong_program_typology"],
                "reviewed_exact_post_book_geometry": True,
            },
        )
        causal_memory = graph.agent_neighborhood(source_seed="hall", program_hash="program-hash")
        self.assertEqual(causal_memory["descendant_program_hashes"], ["child-hash"])
        self.assertEqual(causal_memory["observation_count"], 2)
        self.assertEqual(causal_memory["recent_measured_outcomes"][0]["stage"], "final_book_vlm")
        self.assertEqual(causal_memory["common_failed_gates"], [])
        self.assertEqual(
            causal_memory["downstream_projection_failure_patterns"][0]["gate"],
            "final_book_vlm_wrong_program_typology",
        )
        self.assertEqual(
            causal_memory["downstream_projection_failure_patterns"][0]["attribution"],
            "book_projection_context_not_global_author_failure",
        )

    def test_final_book_vlm_audit_links_reference_projected_program_and_critic(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        projected_program = base_seed_programs()[1].to_dict()
        projected_program["metadata"] = {
            **projected_program["metadata"],
            "pre_book_program_hash": "authored-hash",
            "family": "bent_bar",
        }
        source = SimpleNamespace(metadata={
            "family": "bent_bar",
            "geometry_program": projected_program,
            "geometry_program_bridge_evidence": {
                "program_hash": "projected-hash",
                "geometry_hash": "solid-hash",
                "source_seed": "neighborhood-seed",
                "operator_path": ["base", "bend"],
            },
            "program_book_projection_evidence": {"scope": {"base_volume_label": "1/4"}},
        })
        candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="neighborhood-seed__book_bend"),
            principle_id="book-bend",
        )
        graph.observe_final_book_vlm_audit(
            program_slug="neighborhood",
            candidate=candidate,
            audit={
                "hard_pass": False,
                "failures": ["final_book_vlm_too_fragmented"],
                "model": "fake-vlm",
                "response_id": "final-response",
                "critic_actions": ["needs_clean_anchor"],
                "geometry_edits": [{"operation": "set_parameter", "target_node_id": "bend"}],
                "concept_scores": {"gesture_clarity": 0.4},
                "reviewed_exact_post_book_geometry": True,
                "reference_ids": ["arch-ref-final"],
                "reference_records": [{
                    "source_id": "arch-ref-final",
                    "source": "archdaily_api",
                    "title": "Bent retail precedent",
                    "program_id": "neighborhood",
                }],
            },
        )
        observation = next(item for item in graph.observations if item.get("stage") == "final_book_vlm")
        self.assertFalse(observation["final_book_vlm_hard_pass"])
        self.assertEqual(observation["projected_program_hash"], "projected-hash")
        self.assertEqual(
            graph.failed_final_book_geometry_hashes("neighborhood"),
            {"solid-hash"},
        )
        projected_node = next(
            node for node in graph.nodes.values()
            if node["kind"] == "projected_geometry_program"
        )
        self.assertEqual(
            projected_node["attributes"]["typed_ast"]["root_id"],
            projected_program["root_id"],
        )
        self.assertTrue(projected_node["attributes"]["typed_ast"]["nodes"])
        self.assertFalse(projected_node["attributes"]["typed_ast"]["contains_parcel_coordinates"])
        self.assertTrue(any(node["kind"] == "reference" for node in graph.nodes.values()))
        self.assertTrue(any(edge["kind"] == "reviewed_by" for edge in graph.edges.values()))
        self.assertTrue(any(edge["kind"] == "informed" for edge in graph.edges.values()))
        memory = graph.agent_neighborhood(
            source_seed="neighborhood-seed",
            program_hash="authored-hash",
        )
        self.assertEqual(memory["recent_measured_outcomes"][0]["stage"], "final_book_vlm")
        self.assertEqual(memory["common_failed_gates"], [])
        self.assertEqual(
            memory["downstream_projection_failure_patterns"][0]["gate"],
            "final_book_vlm_too_fragmented",
        )
        self.assertEqual(
            memory["suggested_projection_edits"][0]["geometry_edits"][0]["target_node_id"],
            "bend",
        )
        self.assertIn(
            "validate_recompile_rerender_all_hard_gates",
            memory["suggested_projection_edits"][0]["application_contract"],
        )
        fresh_memory = graph.agent_neighborhood(
            source_seed="new-neighborhood-seed",
            program_hash="fresh-authored-hash",
            program_slug="neighborhood",
        )
        self.assertEqual(fresh_memory["exact_genotype_observation_count"], 0)
        self.assertEqual(fresh_memory["program_level_observation_count"], 1)
        self.assertEqual(fresh_memory["observation_count"], 1)
        self.assertTrue(fresh_memory["program_level_relation_priors"][0]["node_ids_removed"])
        self.assertNotIn(
            "target_node_id",
            json.dumps(fresh_memory["program_level_relation_priors"], sort_keys=True),
        )
        self.assertEqual(
            graph.preferred_strengths(
                source_seed="neighborhood-seed",
                program_hash="authored-hash",
                fallback=(0.2, 0.6),
            ),
            (0.2, 0.6),
        )

    def test_portfolio_agent_path_closes_reference_vlm_edit_and_memory_loop(self):
        from design.maas.book_language.candidate_generation import _agent_mutated_seeds

        source_name = program_seed_sequences("gymnasium")[0].name
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        def fake_scorer(**kwargs):
            program = kwargs["feature"]["properties"]["geometry_program"]
            node_ids = {str(node.get("id")) for node in program.get("nodes") or []}
            if "critic_taper" in node_ids:
                edits = []
                score = 0.92
            else:
                edits = [
                    {"operation": "add_node", "node_id": "critic_taper", "node_kind": "modifier", "operator": "taper", "input_ids": [program["root_id"]]},
                    {"operation": "set_parameter", "target_node_id": "critic_taper", "parameter_name": "end_scale", "vector_value": [0.62, 0.78]},
                    {"operation": "set_parameter", "target_node_id": "critic_taper", "parameter_name": "subdivisions", "numeric_value": 3},
                    {"operation": "set_root", "target_node_id": "critic_taper"},
                ]
                score = 0.71
            return {
                "score": score,
                "concept_scores": {"gesture_clarity": score, "hierarchy": score},
                "critic_actions": ["needs_profiled_surface"],
                "geometry_edits": edits,
                "model": "fake-vlm",
                "response_id": f"resp-{len(node_ids)}-{int(score * 100)}",
            }

        with patch.dict(os.environ, {
            "MAAS_LIVE_GEOMETRY_VLM": "1",
            "MAAS_LIVE_VLM_CREDENTIAL_ROTATED": "1",
            "OPENAI_API_KEY": "test-only-not-sent",
        }), patch(
            "design.maas.geometry_language.vlm_adapter.score_candidate_with_openai_vlm",
            side_effect=fake_scorer,
        ), patch(
            "design.maas.book_language.candidate_generation.retrieve_geometry_reference_matches",
            return_value=[{
                "source": "archdaily_api", "source_id": "fixture-reference",
                "title": "Fixture hall", "image_url": "https://example.test/hall.jpg",
                "local_path": str(Path(__file__)),
                "selection_role": "counterfactual", "matched_tags": ["folded"],
            }],
        ), patch(
            "design.maas.book_language.candidate_generation._audited_final_book_references",
            return_value=([], {"status": "test_stub", "hard_pass": False}),
        ), patch(
            "design.maas.geometry_language.vlm_adapter.audit_reference_image_for_massing",
            return_value={
                "schema_version": "arr.maas.reference_image_massing_audit.v1",
                "prompt_contract_version": "test", "provider": "openai", "model": "test",
                "response_id": "reference-audit", "view_type": "exterior_massing",
                "whole_building_visible": True, "massing_legibility": 0.9,
                "operation_clarity": 0.8, "hard_pass": True,
                "failure_reasons": [], "visible_form_traits": ["folded_roof"],
                "cache_hit": False,
            },
        ):
            seeds = _agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[{
                    "source_seed": source_name,
                    "base_seeds": ["slab"],
                    "intent_tags": ["long_span", "stepped_section", "carved_void"],
                    "candidate_count": 1,
                    "live_vlm_revision": True,
                    "vlm_generations": 2,
                    "reference_limit": 5,
                    "legal_fit_strengths": [0.0],
                }],
                outcome_graph=graph,
            )
        generated = [seed for seed in seeds if any(note == "geometry_program_vlm_status=completed" for note in seed.notes)]
        self.assertEqual(len(generated), 1)
        self.assertIn(
            "geometry_program_synthesis_request_source=vlm_or_session_directive",
            generated[0].notes,
        )
        payload = next(note.split("=", 1)[1] for note in generated[0].notes if note.startswith("geometry_program_payload="))
        self.assertIn("critic_taper", payload)
        self.assertTrue(any(item.get("stage") == "vlm_critic" for item in graph.observations))
        self.assertTrue(any(item.get("reference_ids") for item in graph.observations))
        self.assertTrue(any(item.get("geometry_changed") for item in graph.observations))

    def test_live_program_pool_marks_typed_llm_author_as_active_geometry_source(self):
        from design.maas.book_language.candidate_generation import _agent_mutated_seeds

        source_name = program_seed_sequences("gymnasium")[0].name
        authored = replace(base_seed_programs()[1], metadata={
            **base_seed_programs()[1].metadata,
            "family": "llm_typed_slab",
            "author_provider": "openai_llm_geometry_author",
            "author_model": "test-model",
            "author_response_id": "author-response",
            "author_representation": "typed_json_ast",
        })
        archive_item = SimpleNamespace(
            program=authored,
            critic_score=0.82,
            generation=0,
            critic_payload={
                "model": "test-vlm",
                "response_id": "critic-response",
                "program_fit_hard_pass": True,
                "concept_scores": {
                    "program_appropriateness": 0.8,
                    "section_program_fit": 0.76,
                },
                "maas_causal_context": {"reference_matches": []},
            },
        )
        fake_loop = SimpleNamespace(
            archive=(archive_item,),
            trace={
                "status": "completed",
                "geometry_revision_count": 0,
                "unique_geometry_count": 1,
            },
        )
        with (
            patch.dict(os.environ, {
                "MAAS_LIVE_GEOMETRY_VLM": "1",
                "MAAS_LIVE_VLM_CREDENTIAL_ROTATED": "1",
                "OPENAI_API_KEY": "test-only-not-sent",
            }),
            patch(
                "design.maas.book_language.candidate_generation.author_geometry_programs_with_openai",
                return_value=(authored,),
            ),
            patch(
                "design.maas.book_language.candidate_generation.run_geometry_program_a2a_loop",
                return_value=fake_loop,
            ),
            patch(
                "design.maas.book_language.candidate_generation._audited_final_book_references",
                return_value=([], {"status": "test_stub", "hard_pass": False}),
            ),
        ):
            seeds = _agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[{
                    "source_seed": source_name,
                    "base_seeds": ["slab"],
                    "intent_tags": ["long_span"],
                    "candidate_count": 1,
                    "live_vlm_revision": True,
                    "live_llm_author": True,
                    "llm_author_count": 1,
                    "legal_fit_strengths": [0.0],
                }],
            )

        active = [
            seed for seed in seeds
            if "geometry_program_llm_author_active=True" in seed.notes
        ]
        self.assertEqual(len(active), 1)
        self.assertTrue(any(
            note.startswith("geometry_program_llm_author_status=completed:1")
            for note in active[0].notes
        ))
        payload = next(
            note.split("=", 1)[1]
            for note in active[0].notes
            if note.startswith("geometry_program_payload=")
        )
        self.assertEqual(
            json.loads(payload)["metadata"]["author_representation"],
            "typed_json_ast",
        )

    def test_llm_author_can_run_once_without_prebook_vlm(self):
        from design.maas.book_language.candidate_generation import _agent_mutated_seeds

        source_name = program_seed_sequences("gymnasium")[0].name
        authored = replace(base_seed_programs()[1], metadata={
            **base_seed_programs()[1].metadata,
            "family": "llm_one_shot_mass",
            "author_provider": "openai_llm_geometry_author",
            "author_model": "test-model",
            "author_response_id": "author-one-shot",
            "author_representation": "typed_json_ast",
        })
        with (
            patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "test-only-not-sent"},
                clear=False,
            ),
            patch(
                "design.maas.book_language.candidate_generation.author_geometry_programs_with_openai",
                return_value=(authored,),
            ) as author,
            patch(
                "design.maas.book_language.candidate_generation.run_geometry_program_a2a_loop",
            ) as prebook_vlm,
        ):
            seeds = _agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[{
                    "source_seed": source_name,
                    "base_seeds": ["slab"],
                    "intent_tags": ["five_floor", "public_threshold"],
                    "live_llm_author": True,
                    "live_vlm_revision": False,
                    "llm_author_count": 1,
                }],
            )

        author.assert_called_once()
        self.assertEqual(author.call_args.kwargs["target_count"], 1)
        prebook_vlm.assert_not_called()
        active = [
            seed for seed in seeds
            if "geometry_program_llm_author_active=True" in seed.notes
        ]
        self.assertEqual(len(active), 1)
        self.assertIn(
            "geometry_program_vlm_status=deferred_to_exact_post_book_final_solid",
            active[0].notes,
        )

    def test_prebook_vlm_rejection_quarantines_connected_llm_parent_without_selection_authority(self):
        from design.maas.book_language.candidate_generation import (
            _prebook_vlm_quarantined_llm_parents,
        )

        authored = replace(base_seed_programs()[1], metadata={
            **base_seed_programs()[1].metadata,
            "author_provider": "openai_llm_geometry_author",
            "author_model": "test-model",
            "author_response_id": "author-response",
        })
        rejected_trace = {
            "generations": [{
                "records": [{
                    "program_hash": authored.program_hash(),
                    "status": "critic_program_fit_rejected",
                    "critic_response_id": "critic-response",
                    "critic_actions": ["reduce_box_like_expression"],
                    "program_appropriateness": 0.34,
                    "section_program_fit": 0.41,
                }],
            }],
        }

        quarantined = _prebook_vlm_quarantined_llm_parents(
            (authored,),
            rejected_trace,
        )

        self.assertEqual(len(quarantined), 1)
        metadata = quarantined[0].metadata
        self.assertTrue(metadata["pre_book_vlm_quarantined"])
        self.assertFalse(metadata["vlm_program_fit_hard_pass"])
        self.assertEqual(
            metadata["pre_book_vlm_quarantine_selection_authority"],
            "none_until_exact_final_vlm_hard_pass",
        )
        self.assertEqual(
            metadata["pre_book_vlm_critic_actions"],
            ["reduce_box_like_expression"],
        )

        deterministic = base_seed_programs()[0]
        self.assertEqual(
            _prebook_vlm_quarantined_llm_parents(
                (deterministic,),
                {
                    "generations": [{
                        "records": [{
                            "program_hash": deterministic.program_hash(),
                            "status": "critic_program_fit_rejected",
                        }],
                    }],
                },
            ),
            (),
        )

    def test_vlm_synthesis_request_is_additive_to_universal_form_control_lane(self):
        from design.maas.book_language.candidate_generation import _agent_mutated_seeds

        source_name = program_seed_sequences("gymnasium")[0].name
        seeds = _agent_mutated_seeds(
            "gymnasium",
            mutations=None,
            synthesis_requests=[{
                "source_seed": source_name,
                "base_seeds": ["block"],
                "intent_tags": ["calm_prismatic"],
                "candidate_count": 1,
                "legal_fit_strengths": [0.0],
            }],
        )
        synthesized = [
            seed for seed in seeds
            if any(note.startswith("geometry_program_payload=") for note in seed.notes)
        ]
        sources = {
            note.split("=", 1)[1]
            for seed in synthesized
            for note in seed.notes
            if note.startswith("geometry_program_synthesis_request_source=")
        }
        payloads = [
            json.loads(next(
                note.split("=", 1)[1]
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            ))
            for seed in synthesized
        ]
        families = {str((payload.get("metadata") or {}).get("family") or "") for payload in payloads}
        self.assertEqual(
            sources,
            {"universal_form_bank_control", "vlm_or_session_directive"},
        )
        self.assertTrue(any("cross_mass" in family for family in families))
        self.assertTrue(any("grid_mass" in family for family in families))
        self.assertTrue(any("stepped_mass" in family for family in families))

    def test_visual_wedge_and_pyramid_flags_do_not_hide_complex_topology(self):
        from design.maas.book_language.portfolio_benchmark import _section_silhouette_flags

        wedge, pyramid = _section_silhouette_flags(
            sloped_surface_ratio=0.39,
            upper_area_ratio=0.33,
            horizontal_level_count=11,
            vertical_surface_ratio=0.18,
        )
        self.assertTrue(wedge)
        self.assertTrue(pyramid)

        wedge, pyramid = _section_silhouette_flags(
            sloped_surface_ratio=0.04,
            upper_area_ratio=0.06,
            horizontal_level_count=13,
            vertical_surface_ratio=0.22,
        )
        self.assertFalse(wedge)
        self.assertTrue(pyramid)

        wedge, pyramid = _section_silhouette_flags(
            sloped_surface_ratio=0.0,
            upper_area_ratio=0.64,
            horizontal_level_count=5,
            vertical_surface_ratio=0.23,
        )
        self.assertFalse(wedge)
        self.assertTrue(pyramid)

    def test_compiled_program_roof_graph_has_visible_phenotype(self):
        from design.maas.book_language.portfolio_benchmark import _program_section_phenotype

        self.assertEqual(_program_section_phenotype({"flat_roof"}), "prismatic")
        self.assertEqual(_program_section_phenotype({"barrel_roof"}), "curved")
        self.assertEqual(_program_section_phenotype({"ridge_roof"}), "oblique")
        self.assertEqual(_program_section_phenotype({"folded_roof"}), "oblique")
        self.assertEqual(_program_section_phenotype({"sawtooth_roof"}), "stepped")

    def test_scope_and_base_seed_are_separate_and_four_seeds_share_one_unit_box(self):
        box_seeds = box_derived_base_seed_programs()
        self.assertEqual(len(box_seeds), 4)
        for program in box_seeds:
            unit = program.node_map["unit_box"]
            self.assertEqual(unit.operator, "box")
            self.assertEqual(unit.parameters, {"width": 1.0, "depth": 1.0, "height": 1.0})
            self.assertTrue(program.metadata["site_scope_is_separate"])
        results = [compile_geometry_program(program) for program in base_seed_programs()]
        self.assertEqual(len(results), 5)
        self.assertTrue(all(result.status == "compiled" for result in results))
        self.assertEqual(len({result.geometry_hash for result in results}), 5)

    def test_site_fit_preserves_compact_slab_and_bar_plan_languages(self):
        host = box(0, 0, 60, 40)
        aspects = {}
        areas = {}
        for program in base_seed_programs():
            source = compile_geometry_program_to_source_mass(program, host)
            self.assertIsNotNone(source)
            assert source is not None
            seed_id = program.metadata["base_seed"]["seed_id"]
            rectangle = list(source.footprint.minimum_rotated_rectangle.exterior.coords)
            lengths = [
                ((rectangle[index + 1][0] - rectangle[index][0]) ** 2
                 + (rectangle[index + 1][1] - rectangle[index][1]) ** 2) ** 0.5
                for index in range(4)
            ]
            aspects[seed_id] = max(lengths) / max(min(lengths), 1e-9)
            areas[seed_id] = source.footprint.area

        # A host fit may respond to the parcel, but it must not normalize all
        # base seeds to the host's single aspect ratio.
        self.assertLess(aspects["block"], 1.35)
        self.assertGreater(aspects["slab"], aspects["block"] + 0.15)
        self.assertGreater(aspects["bar"], 2.5)
        self.assertGreater(aspects["bar"], aspects["slab"] + 1.0)
        self.assertGreater(areas["slab"], areas["block"] * 1.8)
        self.assertLess(areas["tower"], areas["block"] * 0.8)

    def test_original_eighteen_share_one_unitbox_authority_but_not_one_program(self):
        primitive_signatures = {
            tuple((node.operator, repr(sorted(node.parameters.items()))) for node in program.nodes if node.kind == "primitive")
            for program in architectural_shape_programs()
        }
        self.assertEqual(
            primitive_signatures,
            {(("box", "[('depth', 1.0), ('height', 1.0), ('width', 1.0)]"),)},
        )
        self.assertEqual(
            len({program.program_hash() for program in architectural_shape_programs()}),
            18,
        )

    def test_vlm_receives_node_bound_graph_notes_and_scope_seed_distinction(self):
        program = base_seed_programs()[1]
        compilation = compile_geometry_program(program)
        notes = build_geometry_graph_notes(program, compilation)
        contract = program_reference_contract("gymnasium")
        snapshot = build_geometry_graph_snapshot(
            program,
            compilation,
            program_context=contract,
            reference_matches=[{
                "source_id": "sports-hall-1",
                "title": "Long-span sports hall",
                "program_match_tier": "preferred_collection",
                "reference_collection": "sports_architecture",
            }],
        )
        self.assertEqual([note["node_id"] for note in notes], [node.id for node in program.topological_nodes()])
        self.assertTrue(all(note["note_is_non_executable"] for note in notes))
        self.assertEqual(snapshot["root_node_id"], program.root_id)
        self.assertEqual(len(snapshot["edges"]), len(program.topological_nodes()) - 1)
        self.assertEqual(snapshot["agent_edit_contract"]["target_selector"], "node_id")
        self.assertTrue(snapshot["agent_edit_contract"]["requires_recompile_and_rerender"])
        self.assertTrue(snapshot["agent_edit_contract"]["must_preserve_program_context_graph"])
        self.assertEqual(snapshot["program_context_graph"]["root_node_id"], "program:gymnasium")
        self.assertTrue(any(
            node["node_kind"] == "semantic_invariant"
            for node in snapshot["program_context_graph"]["nodes"]
        ))
        self.assertTrue(all(
            not node["editable"]
            for node in snapshot["program_context_graph"]["nodes"]
        ))
        feature = {"properties": {
            "geometry_program": program.to_dict(),
            "geometry_graph_notes": notes,
            "geometry_graph_snapshot": snapshot,
            "program_context": contract,
            "base_seed_catalog": [program.metadata["base_seed"]],
            "mass_execution_agent_context": {
                "schema_version": "arr.maas.mass_execution_agent_context.v1",
                "stage_status": {"geometry_gate": "passed", "parking": "not_evaluated"},
                "active_nodes": [{"id": "ast:seed_slab", "source_id": "seed_slab"}],
                "active_edges": [],
                "editable_ast_nodes": [{"node_id": "seed_slab", "operator": "scale"}],
                "failed_stages": [],
                "pending_required_stages": ["parking"],
            },
        }}
        prompt = _prompt_text(feature, [])
        self.assertIn("geometry_graph_notes", prompt)
        self.assertIn("geometry_graph_snapshot", prompt)
        self.assertIn("site scope fraction from normalized base seed", prompt)
        self.assertIn("seed_slab", prompt)
        self.assertIn("program_context is a hard semantic brief", prompt)
        self.assertIn("arbitrary cascading pyramid", prompt)
        self.assertIn("mass_execution_agent_context", prompt)
        self.assertIn('"parking": "not_evaluated"', prompt)
        self.assertIn('"node_id": "seed_slab"', prompt)

    def test_exact_post_book_vlm_uses_only_geometry_ast_node_namespace(self):
        program = base_seed_programs()[1]
        compilation = compile_geometry_program(program)
        feature = {"properties": {
            "geometry_only_critic_mode": True,
            "geometry_program": program.to_dict(),
            "geometry_graph_notes": build_geometry_graph_notes(program, compilation),
            "geometry_graph_snapshot": build_geometry_graph_snapshot(program, compilation),
            "source_signature": {
                "component_graph": {
                    "nodes": [{
                        "node_id": "legacy_primary_1_courtyard",
                        "role": "primary",
                        "operation": {"verb": "courtyard"},
                    }],
                },
            },
        }}

        prompt = _prompt_text(feature, [])

        self.assertIn("GEOMETRY-ONLY CRITIC MODE IS ACTIVE", prompt)
        self.assertIn("geometry_editable_nodes", prompt)
        self.assertIn(program.root_id, prompt)
        self.assertNotIn("legacy_primary_1_courtyard", prompt)
        self.assertIn("Return graph_edits=[]", prompt)

    def test_geometry_only_vlm_normalizer_drops_legacy_graph_namespace_and_keeps_ordered_new_node(self):
        program = base_seed_programs()[1]
        normalized = _normalize_vlm_result(
            {
                "program_fit_hard_pass": False,
                "concept_scores": {},
                "critic_actions": [],
                "graph_edits": [{
                    "operation": "replace_operation",
                    "target_node_id": "legacy_primary_1_courtyard",
                    "verb": "courtyard",
                }],
                "geometry_edits": [
                    {
                        "operation": "set_parameter",
                        "target_node_id": "legacy_primary_1_courtyard",
                        "parameter_name": "margin_ratio",
                        "numeric_value": 0.2,
                    },
                    {
                        "operation": "add_node",
                        "node_id": "critic_court",
                        "node_kind": "macro",
                        "operator": "courtyard",
                        "input_ids": [program.root_id],
                    },
                    {
                        "operation": "set_parameter",
                        "target_node_id": "critic_court",
                        "parameter_name": "margin_ratio",
                        "numeric_value": 0.2,
                    },
                    {
                        "operation": "set_parameter",
                        "target_node_id": "critic_court",
                        "parameter_name": "open_side",
                        "string_value": "west",
                    },
                    {
                        "operation": "set_root",
                        "target_node_id": "critic_court",
                    },
                ],
            },
            model="fake",
            response_id="geometry-namespace",
            feature={"properties": {
                "geometry_only_critic_mode": True,
                "geometry_program": program.to_dict(),
            }},
        )

        self.assertEqual(normalized["graph_edits"], [])
        self.assertEqual(
            [item["operation"] for item in normalized["geometry_edits"]],
            ["add_node", "set_parameter", "set_parameter", "set_root"],
        )
        mutation = apply_geometry_edits(program, normalized["geometry_edits"])
        self.assertEqual(mutation.status, "revised", mutation.issues)
        assert mutation.program is not None
        self.assertEqual(mutation.program.root_id, "critic_court")
        self.assertEqual(compile_geometry_program(mutation.program).status, "compiled")

    def test_geometry_only_vlm_enforces_program_macro_and_operator_parameter_contracts(self):
        program = base_seed_programs()[1]
        compilation = compile_geometry_program(program)
        context = program_reference_contract("neighborhood living")
        snapshot = build_geometry_graph_snapshot(
            program,
            compilation,
            program_context=context,
        )
        normalized = _normalize_vlm_result(
            {
                "program_fit_hard_pass": False,
                "concept_scores": {},
                "critic_actions": [],
                "geometry_edits": [
                    {
                        "operation": "add_node", "node_id": "wrong_hall",
                        "node_kind": "macro", "operator": "profiled_hall",
                        "input_ids": [program.root_id],
                    },
                    {
                        "operation": "set_parameter", "target_node_id": "wrong_hall",
                        "parameter_name": "section_family", "string_value": "folded",
                    },
                    {
                        "operation": "set_root", "target_node_id": "wrong_hall",
                    },
                    {
                        "operation": "add_node", "node_id": "orphan_step",
                        "node_kind": "macro", "operator": "stepped_mass",
                        "input_ids": [program.root_id],
                    },
                    {
                        "operation": "add_node", "node_id": "public_court",
                        "node_kind": "macro", "operator": "courtyard",
                        "input_ids": [program.root_id],
                    },
                    {
                        "operation": "set_parameter", "target_node_id": "public_court",
                        "parameter_name": "unsupported_decoration", "numeric_value": 0.4,
                    },
                    {
                        "operation": "set_parameter", "target_node_id": "public_court",
                        "parameter_name": "margin_ratio", "numeric_value": 0.22,
                    },
                    {
                        "operation": "set_parameter", "target_node_id": "public_court",
                        "parameter_name": "open_side", "string_value": "west",
                    },
                    {
                        "operation": "set_root", "target_node_id": "public_court",
                    },
                ],
            },
            model="fake",
            response_id="program-operator-contract",
            feature={"properties": {
                "geometry_only_critic_mode": True,
                "geometry_program": program.to_dict(),
                "geometry_graph_snapshot": snapshot,
                "program_context": context,
            }},
        )

        encoded = json.dumps(normalized["geometry_edits"])
        self.assertNotIn("profiled_hall", encoded)
        self.assertNotIn("wrong_hall", encoded)
        self.assertNotIn("orphan_step", encoded)
        self.assertNotIn("unsupported_decoration", encoded)
        self.assertEqual(
            [item["operation"] for item in normalized["geometry_edits"]],
            ["add_node", "set_parameter", "set_parameter", "set_root"],
        )
        mutation = apply_geometry_edits(program, normalized["geometry_edits"])
        self.assertEqual(mutation.status, "revised", mutation.issues)
        assert mutation.program is not None
        self.assertEqual(compile_geometry_program(mutation.program).status, "compiled")

    def test_geometry_only_vlm_recovers_root_for_one_unambiguous_unary_add_chain(self):
        program = base_seed_programs()[1]
        compilation = compile_geometry_program(program)
        context = program_reference_contract("neighborhood living")
        normalized = _normalize_vlm_result(
            {
                "program_fit_hard_pass": False,
                "concept_scores": {},
                "critic_actions": [],
                "geometry_edits": [
                    {
                        "operation": "add_node", "node_id": "public_court",
                        "node_kind": "macro", "operator": "courtyard",
                        "input_ids": [program.root_id],
                    },
                    {
                        "operation": "set_parameter", "target_node_id": "public_court",
                        "parameter_name": "margin_ratio", "numeric_value": 0.22,
                    },
                ],
            },
            model="fake",
            response_id="implicit-root",
            feature={"properties": {
                "geometry_only_critic_mode": True,
                "geometry_program": program.to_dict(),
                "geometry_graph_snapshot": build_geometry_graph_snapshot(
                    program, compilation, program_context=context,
                ),
                "program_context": context,
            }},
        )

        self.assertEqual(normalized["geometry_edits"][-1]["operation"], "set_root")
        self.assertEqual(normalized["geometry_edits"][-1]["target_node_id"], "public_court")
        mutation = apply_geometry_edits(program, normalized["geometry_edits"])
        self.assertEqual(mutation.status, "revised", mutation.issues)
        assert mutation.program is not None
        self.assertEqual(mutation.program.root_id, "public_court")

    def test_eighteen_architectural_families_compile_to_distinct_gated_solids(self):
        programs = architectural_shape_programs()
        self.assertEqual(len(programs), 18)
        compilations = [compile_geometry_program(program) for program in programs]

        self.assertTrue(all(result.status == "compiled" for result in compilations))
        self.assertTrue(all(not compilation_gate(result) for result in compilations))
        self.assertEqual(len({program.program_hash() for program in programs}), 18)
        self.assertEqual(len({result.geometry_hash for result in compilations}), 18)
        self.assertTrue(all(int(result.metrics["component_count"]) <= 5 for result in compilations))
        operators = {node.operator for program in programs for node in program.nodes}
        self.assertTrue({
            "bend", "radial_array", "courtyard", "notch", "setback", "tapered_tower",
            "leaning_tower", "slice", "cut_corner", "matrix4", "taper", "split_wing", "twist",
        }.issubset(operators))
        expansions = {operation for result in compilations for row in result.trace for operation in row["macro_expansion"]}
        self.assertTrue({"difference", "shear"}.issubset(expansions))

    def test_radial_and_twisted_chassis_leave_clean_budget_for_book_projection(self):
        from design.maas.source_geometry.coherence import evaluate_source_volume_coherence

        programs = {
            program.metadata.get("family"): program
            for program in architectural_shape_programs()
        }
        host = box(0, 0, 100, 70)
        for family in ("radial_fan", "twisted_mass"):
            for verb in ("notch", "shift", "bend", "inscribe"):
                sequence = compose_program_with_book_operations(
                    program_seed_sequences("neighborhood living")[0],
                    (book_operation_variants(verb, count=1)[0],),
                    base_volume_label="1/2",
                )
                projected = apply_book_projection_to_geometry_program(
                    programs[family], sequence,
                )
                source = compile_geometry_program_to_source_mass(projected, host)

                self.assertIsNotNone(source, (family, verb))
                assert source is not None
                self.assertLessEqual(
                    int(source.signature()["effective_surface_count"]),
                    48,
                    (family, verb),
                )
                self.assertTrue(
                    evaluate_source_volume_coherence(source.volumes)["hard_pass"],
                    (family, verb),
                )

    def test_compiler_reports_tiny_disconnected_component_ratio(self):
        builder = GeometryProgramBuilder("tiny_fragment_metric")
        main = builder.add("primitive", "box", parameters={"width": 10, "depth": 8, "height": 4})
        speck = builder.add("primitive", "box", parameters={"width": 0.5, "depth": 0.5, "height": 0.5})
        moved = builder.add("transform", "translate", inputs=(speck,), parameters={"vector": [12, 0, 0]})
        root = builder.add("boolean", "union", inputs=(main, moved))
        result = compile_geometry_program(builder.build(root))
        self.assertEqual(result.status, "compiled")
        self.assertEqual(result.metrics["component_count"], 2)
        self.assertLess(result.metrics["minimum_component_volume_ratio"], 0.01)

    def test_three_photo_languages_are_transferable_programs_not_coordinate_templates(self):
        references = reference_language_programs()
        self.assertEqual(len(references), 3)
        for program in references.values():
            result = compile_geometry_program(program)
            self.assertEqual(result.status, "compiled", result.issues)
            self.assertFalse(compilation_gate(result))
            self.assertNotIn("parcel", str(program.to_dict()).lower())
            self.assertNotIn("pnu", str(program.to_dict()).lower())

    def test_recursive_photo_languages_materialize_inside_oblique_source_host(self):
        host = Polygon(((0, 4), (35, 0), (44, 19), (29, 35), (3, 29)))
        for name, program in reference_language_programs().items():
            source = compile_geometry_program_to_source_mass(program, host)
            self.assertIsNotNone(source, name)
            assert source is not None
            self.assertLessEqual(len(source.volumes), 3)
            self.assertTrue(source.surfaces)
            self.assertTrue(all(host.covers(volume.footprint) for volume in source.volumes))
            self.assertLessEqual(int(source.signature()["effective_surface_count"]), 48)
            evidence = source.metadata["geometry_program_bridge_evidence"]
            compilation = compile_geometry_program(program)
            self.assertEqual(evidence["geometry_hash"], compilation.geometry_hash)
            self.assertEqual(evidence["surface_coordinate_frame"], "source_footprint_centroid_local")
            self.assertFalse(evidence["parcel_coordinates_in_program"])

    def test_recursive_bridge_exports_the_complete_compiler_mesh(self):
        program = synthesize_architectural_programs({
            "base_seeds": ["slab"],
            "intent_tags": ["continuous_curve"],
            "candidate_count": 1,
            "maximum_operator_depth": 1,
        }, building_type="gymnasium")[0]
        compilation = compile_geometry_program(program)
        self.assertGreater(len(compilation.triangles), 160)
        source = compile_geometry_program_to_source_mass(
            program,
            Polygon(((0, 0), (30, 0), (30, 20), (0, 20))),
        )
        self.assertIsNotNone(source)
        assert source is not None
        recursive_surfaces = tuple(
            surface for surface in source.surfaces
            if surface.surface_type == "profiled_recursive_solid_mesh"
        )
        self.assertEqual(len(recursive_surfaces), len(compilation.triangles))

    def test_recursive_primary_replaces_gym_hall_without_erasing_program_roles(self):
        host = Polygon(((0, 4), (35, 0), (44, 19), (29, 35), (3, 29)))
        seed = program_seed_sequences("gymnasium")[0]
        source = compile_sequence_to_source_mass(host, seed)
        self.assertIsNotNone(source)
        assert source is not None
        original_roles = {volume.role for volume in source.volumes}
        original_surface_signature = {
            tuple(tuple(round(value, 5) for value in vertex) for vertex in surface.vertices_m)
            for surface in source.surfaces
        }
        program = reference_language_programs()["amorepacific_carved_cantilever_cube"]
        composed = replace_source_dominant_with_geometry_program(
            source,
            program,
            containment_host=host,
        )
        self.assertIsNotNone(composed)
        assert composed is not None
        self.assertLessEqual(len(composed.volumes), 5)
        composed_roles = {volume.role for volume in composed.volumes} | {
            str(zone.get("role") or "")
            for zone in composed.metadata.get("program_space_zones") or ()
        }
        self.assertEqual(composed_roles, original_roles)
        self.assertEqual(
            composed.metadata["program_role_integration_evidence"]["mode"],
            "normalized_spatial_zones_inside_dominant_envelope",
        )
        integration = composed.metadata["program_role_integration_evidence"]
        self.assertGreaterEqual(
            integration["original_component_union_area_m2"],
            source.footprint.area,
        )
        self.assertLessEqual(
            integration["recursive_target_plan_area_m2"],
            host.area,
        )
        self.assertGreaterEqual(
            integration["recursive_target_plan_area_m2"],
            max(volume.footprint.area for volume in source.volumes),
        )
        self.assertTrue(all(host.buffer(1e-7).covers(volume.footprint) for volume in composed.volumes))
        self.assertLessEqual(int(composed.signature()["effective_surface_count"]), 48)
        self.assertEqual(
            composed.metadata["geometry_program_bridge_evidence"]["geometry_hash"],
            compile_geometry_program(program).geometry_hash,
        )
        composed_surface_signature = {
            tuple(tuple(round(value, 5) for value in vertex) for vertex in surface.vertices_m)
            for surface in composed.surfaces
        }
        self.assertNotEqual(original_surface_signature, composed_surface_signature)

    def test_l_mass_canonicalizer_prefers_short_union_but_recognizes_difference_equivalence(self):
        union_program = architectural_shape_programs()[2]
        difference_program = l_mass_difference_program()
        union_result = compile_geometry_program(union_program)
        difference_result = compile_geometry_program(difference_program)

        self.assertTrue(geometry_equivalent(union_result, difference_result))
        self.assertLess(program_cost(union_program, union_result).total, program_cost(difference_program, difference_result).total)

    def test_modifier_order_is_semantic_and_not_flattened(self):
        before = GeometryProgramBuilder("bend_after_carve")
        base = before.add("primitive", "box", parameters={"width": 14, "depth": 4, "height": 4})
        cutter = before.add("primitive", "box", parameters={"width": 4, "depth": 6, "height": 2})
        moved = before.add("transform", "translate", inputs=(cutter,), parameters={"vector": [5, -1, 2]})
        carved = before.add("boolean", "difference", inputs=(base, moved))
        bent_after = before.add("modifier", "bend", inputs=(carved,), parameters={"axis": "x", "angle_degrees": 38, "subdivisions": 4})

        after = GeometryProgramBuilder("carve_after_bend")
        base2 = after.add("primitive", "box", parameters={"width": 14, "depth": 4, "height": 4})
        bent = after.add("modifier", "bend", inputs=(base2,), parameters={"axis": "x", "angle_degrees": 38, "subdivisions": 4})
        cutter2 = after.add("primitive", "box", parameters={"width": 4, "depth": 6, "height": 2})
        moved2 = after.add("transform", "translate", inputs=(cutter2,), parameters={"vector": [5, -1, 2]})
        carved_after = after.add("boolean", "difference", inputs=(bent, moved2))

        first = compile_geometry_program(before.build(bent_after))
        second = compile_geometry_program(after.build(carved_after))
        self.assertEqual(first.status, "compiled")
        self.assertEqual(second.status, "compiled")
        self.assertFalse(geometry_equivalent(first, second))

    def test_text_dsl_reassignment_normalizes_to_acyclic_ssa_and_compiles(self):
        program = parse_geometry_dsl("""
            mass main = box(10, 8, 4)
            mass void = box(4, 4, 5)
            void = move(void, 0, 0, 0.5)
            mass courtyard = subtract(main, void)
            mass tower = box(3, 3, 10)
            tower = taper(tower, axis="z", endScale=[0.5, 0.5])
            tower = shear(tower, axis="x", amount=0.2)
            mass result = union(courtyard, tower)
        """)
        self.assertEqual(program.root_id, "result")
        self.assertIn("void__2", program.node_map)
        self.assertIn("tower__3", program.node_map)
        self.assertFalse([issue for issue in program.validate() if issue.severity == "error"])
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_text_dsl_lowers_recursive_solid_expressions_into_typed_ssa_nodes(self):
        program = parse_geometry_dsl(
            "mass result = difference("
            "bend(union(box(10, 3, 4), translate(box(3, 7, 4), vector=[3.5, 0, 0])), axis='x', angle_degrees=22, subdivisions=3), "
            "taper(translate(box(2, 2, 5), vector=[4, 0, 0]), axis='z', end_scale=[0.6, 0.6], subdivisions=3)"
            ")",
            name="recursive_expression",
        )

        self.assertEqual(program.root_id, "result")
        self.assertEqual(program.node_map["result"].operator, "difference")
        self.assertGreaterEqual(len(program.nodes), 9)
        self.assertEqual(program.topological_nodes()[-1].id, "result")
        self.assertFalse([issue for issue in program.validate() if issue.severity == "error"])
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_llm_author_accepts_nested_scale_seed_without_shape_fallback(self):
        programs = geometry_programs_from_author_payload({
            "programs": [{
                "name": "nested_slab",
                "base_seed": "slab",
                "dsl": (
                    "mass base = scale(box(1, 1, 1), vector=[2.2, 1.45, 0.28])\n"
                    "mass result = courtyard(base, margin_ratio=0.22, open_side='west')"
                ),
                "intent_tags": ["public_court"],
            }],
        }, expected_count=1)

        self.assertEqual(len(programs), 1)
        self.assertEqual(programs[0].metadata["base_seed"], "slab")
        self.assertEqual(programs[0].node_map["base"].inputs, ("base__input_1",))
        self.assertEqual(programs[0].node_map["base"].semantic_role, "base_seed")
        self.assertEqual(programs[0].metadata["operator_path"], ["courtyard"])
        self.assertEqual(compile_geometry_program(programs[0]).status, "compiled")

    def test_llm_author_typed_ast_payload_eliminates_embedded_dsl_literal_failures(self):
        def parameter(name, value_type, *, number=0.0, string="", boolean=False, vector=(), structured="null"):
            return {
                "name": name,
                "value_type": value_type,
                "numeric_value": number,
                "string_value": string,
                "boolean_value": boolean,
                "vector_value": list(vector),
                "structured_json": structured,
            }

        programs = geometry_programs_from_author_payload({"programs": [{
            "name": "typed_slab_court",
            "base_seed": "slab",
            "intent_tags": ["public_threshold"],
            "root_id": "result",
            "rationale": "one slab is carved into a street-facing court",
            "nodes": [
                {
                    "id": "unit",
                    "kind": "primitive",
                    "operator": "box",
                    "inputs": [],
                    "parameters": [
                        parameter("width", "number", number=1.0),
                        parameter("depth", "number", number=1.0),
                        parameter("height", "number", number=1.0),
                    ],
                    "semantic_role": "base_seed",
                },
                {
                    "id": "seed",
                    "kind": "transform",
                    "operator": "scale",
                    "inputs": ["unit"],
                    "parameters": [
                        parameter("vector", "vector", vector=(2.2, 1.45, 0.28)),
                    ],
                    "semantic_role": "base_seed",
                },
                {
                    "id": "result",
                    "kind": "macro",
                    "operator": "courtyard",
                    "inputs": ["seed"],
                    "parameters": [
                        parameter("margin_ratio", "number", number=0.24),
                        parameter("open_side", "string", string="west"),
                    ],
                    "semantic_role": "public_void",
                },
            ],
        }]}, expected_count=1)

        self.assertEqual(len(programs), 1)
        program = programs[0]
        self.assertEqual(program.metadata["author_representation"], "typed_json_ast")
        self.assertEqual(program.metadata["base_seed"], "slab")
        self.assertIn("mass result = courtyard(seed", program.metadata["canonical_dsl"])
        self.assertEqual(program.node_map["result"].parameters["open_side"], "west")
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_llm_author_canonicalizes_redundant_single_input_union_result(self):
        empty = lambda name, kind, operator, inputs: {
            "id": name,
            "kind": kind,
            "operator": operator,
            "inputs": inputs,
            "parameters": [],
            "semantic_role": "dominant_mass",
        }
        box_node = empty("body", "primitive", "box", [])
        box_node["parameters"] = [
            {
                "name": name,
                "value_type": "number",
                "numeric_value": value,
                "string_value": "",
                "boolean_value": False,
                "vector_value": [],
                "structured_json": "null",
            }
            for name, value in (("width", 1.0), ("depth", 1.0), ("height", 1.0))
        ]
        program = geometry_programs_from_author_payload({"programs": [{
            "name": "identity_union",
            "base_seed": "block",
            "intent_tags": [],
            "root_id": "result",
            "rationale": "",
            "nodes": [
                box_node,
                empty("result", "boolean", "union", ["body"]),
            ],
        }]}, expected_count=1)[0]

        self.assertEqual(program.root_id, "body")
        self.assertNotIn("result", program.node_map)
        self.assertEqual(
            program.metadata["canonicalized_identity_boolean_node_ids"],
            ["result"],
        )
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_llm_author_canonicalizes_wrong_kind_single_input_union_result(self):
        empty = lambda name, kind, operator, inputs: {
            "id": name,
            "kind": kind,
            "operator": operator,
            "inputs": inputs,
            "parameters": [],
            "semantic_role": "dominant_mass",
        }
        body = empty("body", "primitive", "box", [])
        body["parameters"] = [
            {
                "name": name,
                "value_type": "number",
                "numeric_value": value,
                "string_value": "",
                "boolean_value": False,
                "vector_value": [],
                "structured_json": "null",
            }
            for name, value in (("width", 1.0), ("depth", 1.0), ("height", 1.0))
        ]
        program = geometry_programs_from_author_payload({"programs": [{
            "name": "wrong_kind_identity_union",
            "base_seed": "block",
            "intent_tags": [],
            "root_id": "result",
            "rationale": "",
            "nodes": [body, empty("result", "composition", "union", ["body"])],
        }]}, expected_count=1)[0]

        self.assertEqual(program.root_id, "body")
        self.assertEqual(
            program.metadata["canonicalized_identity_boolean_node_ids"],
            ["result"],
        )

    def test_llm_author_rejects_bridge_with_duplicate_solid_inputs_before_compile(self):
        def node(node_id, kind, operator, inputs, parameters=()):
            return {
                "id": node_id,
                "kind": kind,
                "operator": operator,
                "inputs": list(inputs),
                "parameters": list(parameters),
                "semantic_role": "dominant_mass",
            }

        number = lambda name, value: {
            "name": name,
            "value_type": "number",
            "numeric_value": value,
            "string_value": "",
            "boolean_value": False,
            "vector_value": [],
            "structured_json": "null",
        }
        payload = {"programs": [{
            "name": "degenerate_bridge",
            "base_seed": "block",
            "intent_tags": [],
            "root_id": "result",
            "rationale": "",
            "nodes": [
                node("body", "primitive", "box", (), (
                    number("width", 1.0), number("depth", 1.0), number("height", 1.0),
                )),
                node("result", "composition", "bridge", ("body", "body")),
            ],
        }]}

        with self.assertRaisesRegex(
            geometry_llm_adapter.GeometryAuthorError,
            "composition inputs must reference distinct earlier solids",
        ):
            geometry_programs_from_author_payload(payload, expected_count=1)

    def test_typed_critic_edit_must_change_both_program_and_compiled_geometry(self):
        program = parse_geometry_dsl("mass result = box(10, 8, 6)")
        parent = compile_geometry_program(program)
        mutation = apply_geometry_edits(program, (
            GeometryEdit("add_node", node_id="critic_taper", node_kind="modifier", operator="taper", input_ids=(program.root_id,)),
            GeometryEdit("set_parameter", target_node_id="critic_taper", parameter_name="end_scale", vector_value=(0.48, 0.66)),
            GeometryEdit("set_parameter", target_node_id="critic_taper", parameter_name="subdivisions", numeric_value=3),
            GeometryEdit("set_root", target_node_id="critic_taper"),
        ))
        self.assertEqual(mutation.status, "revised", mutation.issues)
        child = compile_geometry_program(mutation.program)
        self.assertNotEqual(program.program_hash(), mutation.program.program_hash())
        self.assertNotEqual(parent.geometry_hash, child.geometry_hash)
        self.assertFalse(compilation_gate(child))

    def test_vlm_graph_contract_exposes_every_executable_operator_parameter_family(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass wing = split_wing(base, axis='x', gap_ratio=0.16, ground_spine=True)\n"
            "mass result = setback(wing, levels=3, setback_ratio=0.1, shift_per_level=[0.04, 0, 0])"
        )
        compilation = compile_geometry_program(program)
        snapshot = build_geometry_graph_snapshot(program, compilation)
        contracts = snapshot["agent_edit_contract"]["operator_parameter_contracts"]
        self.assertIn("gap_ratio", contracts["split_wing"])
        self.assertIn("ground_spine_width_ratio", contracts["split_wing"])
        self.assertIn("shift_per_level", contracts["setback"])
        self.assertIn("angle_degrees", contracts["bend"])
        self.assertIn("start_ratio", contracts["cantilever"])
        value_contracts = snapshot["agent_edit_contract"]["operator_parameter_value_contracts"]
        self.assertEqual(
            value_contracts["setback"]["shift_per_level"],
            {"type": "numeric_vector", "lengths": [3]},
        )
        self.assertEqual(
            value_contracts["cut_corner"]["corner"],
            {"type": "string", "enum": ["ne", "nw", "se", "sw"]},
        )
        self.assertEqual(
            value_contracts["split_wing"]["ground_spine"],
            {"type": "boolean"},
        )

    def test_typed_critic_boolean_edit_does_not_treat_false_as_truthy_string(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass result = split_wing(base, axis='x', gap_ratio=0.16, bridge=True, ground_spine=True)"
        )
        mutation = apply_geometry_edits(program, [
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "bridge",
                "boolean_value": False,
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "ground_spine",
                "boolean_value": False,
            },
        ])
        self.assertEqual(mutation.status, "revised", mutation.issues)
        self.assertIs(mutation.program.node_map["result"].parameters["bridge"], False)
        self.assertIs(mutation.program.node_map["result"].parameters["ground_spine"], False)

        legacy = apply_geometry_edits(program, [{
            "operation": "set_parameter",
            "target_node_id": "result",
            "parameter_name": "bridge",
            "string_value": "false",
        }])
        self.assertEqual(legacy.status, "revised", legacy.issues)
        self.assertIs(legacy.program.node_map["result"].parameters["bridge"], False)

        normalized = _normalize_vlm_result(
            {
                "program_fit_hard_pass": False,
                "concept_scores": {},
                "critic_actions": [],
                "geometry_edits": [{
                    "operation": "set_parameter",
                    "target_node_id": "result",
                    "parameter_name": "ground_spine",
                    "boolean_value": False,
                }],
            },
            model="fake",
            response_id="boolean-edit",
            feature={"properties": {}},
        )
        self.assertIs(normalized["geometry_edits"][0]["boolean_value"], False)

    def test_typed_critic_ignores_placeholder_vector_for_scalar_and_string_parameters(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass result = courtyard(base, margin_ratio=0.2, open_side='closed')"
        )
        mutation = apply_geometry_edits(program, [
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "margin_ratio",
                "numeric_value": 0.27,
                "vector_value": [0.0, 0.0, 0.0],
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "open_side",
                "string_value": "west",
                "vector_value": [0.0, 0.0, 0.0],
            },
        ])

        self.assertEqual(mutation.status, "revised", mutation.issues)
        self.assertEqual(mutation.program.node_map["result"].parameters["margin_ratio"], 0.27)
        self.assertEqual(mutation.program.node_map["result"].parameters["open_side"], "west")
        self.assertEqual(compile_geometry_program(mutation.program).status, "compiled")

    def test_compiler_safe_mutation_recovers_independent_valid_vlm_edit_group(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass leaned = shear(base, axis='x', direction='z', amount=0.12)\n"
            "mass result = notch(leaned, side='west', ratio=0.2)"
        )
        parent = compile_geometry_program(program)
        recovered = apply_geometry_edits_compiler_safe(program, [
            {
                "operation": "set_parameter",
                "target_node_id": "leaned",
                "parameter_name": "direction",
                "string_value": "x",
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "ratio",
                "numeric_value": 0.36,
            },
        ])

        self.assertEqual(recovered.recovery_mode, "atomic_group_recovery")
        self.assertEqual(recovered.mutation.status, "revised")
        self.assertEqual(recovered.compilation.status, "compiled")
        self.assertEqual(recovered.mutation.program.node_map["leaned"].parameters["direction"], "z")
        self.assertEqual(recovered.mutation.program.node_map["result"].parameters["ratio"], 0.36)
        self.assertNotEqual(parent.geometry_hash, recovered.compilation.geometry_hash)
        self.assertEqual(recovered.rejected_groups[0]["group"], "leaned")
        self.assertEqual(recovered.rejected_groups[0]["status"], "compile_rejected")

    def test_compiler_safe_mutation_rejects_semantic_node_not_connected_to_render_root(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass result = cantilever(base, start_ratio=0.58, vector=[0.18, 0, 0])"
        )
        parent = compile_geometry_program(program)
        recovered = apply_geometry_edits_compiler_safe(program, [
            {
                "operation": "add_node",
                "node_id": "public_court",
                "node_kind": "macro",
                "operator": "courtyard",
                "input_ids": ["result"],
                "semantic_role": "public_void",
            },
            {
                "operation": "set_parameter",
                "target_node_id": "public_court",
                "parameter_name": "margin_ratio",
                "numeric_value": 0.24,
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "start_ratio",
                "numeric_value": 0.49,
            },
        ])

        self.assertEqual(recovered.recovery_mode, "atomic_group_recovery")
        self.assertEqual(recovered.mutation.status, "revised")
        self.assertNotIn("public_court", recovered.mutation.program.node_map)
        self.assertEqual(recovered.mutation.program.node_map["result"].parameters["start_ratio"], 0.49)
        self.assertNotEqual(parent.geometry_hash, recovered.compilation.geometry_hash)
        rejected = {item["group"]: item for item in recovered.rejected_groups}
        self.assertEqual(rejected["public_court"]["status"], "invalid_revision")
        self.assertIn(
            "unreachable_node",
            {issue["code"] for issue in rejected["public_court"]["issues"]},
        )

    def test_typed_critic_rejects_compiler_noop_parameter_and_stale_replacement_parameters(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass result = cantilever(base, start_ratio=0.58, vector=[0.18, 0, 0])"
        )
        noop = apply_geometry_edits(program, [{
            "operation": "set_parameter",
            "target_node_id": "result",
            "parameter_name": "separation_ratio",
            "numeric_value": 0.28,
        }])
        self.assertEqual(noop.status, "no_valid_edit_applied")
        self.assertIn("unsupported_operator_parameter", {issue.code for issue in noop.issues})

        replacement = apply_geometry_edits(program, [
            {
                "operation": "replace_operator",
                "target_node_id": "result",
                "operator": "courtyard",
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "margin_ratio",
                "numeric_value": 0.24,
            },
        ])
        self.assertEqual(replacement.status, "revised", replacement.issues)
        revised = replacement.program.node_map["result"]
        self.assertEqual(revised.operator, "courtyard")
        self.assertEqual(revised.parameters, {"margin_ratio": 0.24})

    def test_typed_critic_can_replace_unary_modifier_with_unary_macro(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass result = taper(base, axis=\"z\", start_scale=[1, 1], end_scale=[0.72, 0.72], subdivisions=3)"
        )
        parent = compile_geometry_program(program)
        revised = apply_geometry_edits_compiler_safe(program, [
            {
                "operation": "replace_operator",
                "target_node_id": "result",
                # The live VLM record carried the old modifier kind. The
                # executable operator registry must infer macro here.
                "node_kind": "modifier",
                "operator": "stepped_mass",
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "direction",
                "string_value": "y",
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "levels",
                "numeric_value": 4,
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "setback_ratio",
                "numeric_value": 0.14,
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "podium_height_ratio",
                "numeric_value": 0.34,
            },
            {
                "operation": "set_parameter",
                "target_node_id": "result",
                "parameter_name": "podium_scale",
                "numeric_value": 0.92,
            },
        ])

        self.assertEqual(revised.mutation.status, "revised", revised.mutation.issues)
        node = revised.mutation.program.node_map["result"]
        self.assertEqual((node.kind, node.operator), ("macro", "stepped_mass"))
        self.assertEqual(node.parameters["levels"], 4)
        self.assertEqual(revised.compilation.status, "compiled")
        self.assertEqual(revised.compilation.metrics["component_count"], 1)
        self.assertNotEqual(parent.geometry_hash, revised.compilation.geometry_hash)

    def test_stepped_shift_parameter_changes_executable_geometry(self):
        centered = parse_geometry_dsl(
            "mass base = box(10, 8, 8)\n"
            "mass result = setback(base, levels=4, setback_ratio=0.12, shift_per_level=[0, 0, 0])"
        )
        shifted = parse_geometry_dsl(
            "mass base = box(10, 8, 8)\n"
            "mass result = setback(base, levels=4, setback_ratio=0.12, shift_per_level=[0.04, 0, 0])"
        )
        centered_result = compile_geometry_program(centered)
        shifted_result = compile_geometry_program(shifted)
        self.assertEqual(centered_result.status, "compiled")
        self.assertEqual(shifted_result.status, "compiled")
        self.assertNotEqual(centered_result.geometry_hash, shifted_result.geometry_hash)
        self.assertFalse(compilation_gate(shifted_result))

    def test_stepped_vertical_shift_retains_one_connected_solid(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 8)\n"
            "mass result = setback(base, levels=3, setback_ratio=0.14, shift_per_level=[0.03, 0, 0.05])"
        )
        result = compile_geometry_program(program)
        self.assertEqual(result.status, "compiled")
        self.assertEqual(result.metrics["component_count"], 1)
        self.assertFalse(compilation_gate(result, geometry_llm_adapter.AUTHOR_GEOMETRY_GATE_POLICY))

    def test_cantilever_rejects_vertical_vector_and_delegates_height_to_lift(self):
        program = parse_geometry_dsl(
            "mass base = box(10, 8, 6)\n"
            "mass result = cantilever(base, start_ratio=0.55, vector=[0.2, 0, 0.1])"
        )
        result = compile_geometry_program(program)
        self.assertEqual(result.status, "compile_failed")
        self.assertIn(
            "cantilever_requires_horizontal_vector",
            {issue.code for issue in result.issues},
        )

    def test_stepped_macro_preserves_upstream_void_in_recursive_solid(self):
        shallow = parse_geometry_dsl(
            "mass base = box(10, 8, 8)\n"
            "mass court = courtyard(base, margin_ratio=0.2, open_side='west')\n"
            "mass result = stepped_mass(court, levels=3, setback_ratio=0.1, direction='x')"
        )
        deep = parse_geometry_dsl(
            "mass base = box(10, 8, 8)\n"
            "mass court = courtyard(base, margin_ratio=0.32, open_side='west')\n"
            "mass result = stepped_mass(court, levels=3, setback_ratio=0.1, direction='x')"
        )
        shallow_result = compile_geometry_program(shallow)
        deep_result = compile_geometry_program(deep)

        self.assertEqual(shallow_result.status, "compiled", shallow_result.issues)
        self.assertEqual(deep_result.status, "compiled", deep_result.issues)
        self.assertNotEqual(shallow_result.geometry_hash, deep_result.geometry_hash)
        self.assertNotEqual(
            shallow_result.metrics["volume"],
            deep_result.metrics["volume"],
            "changing an upstream court must survive the downstream step modifier",
        )
        self.assertFalse(compilation_gate(shallow_result))
        self.assertFalse(compilation_gate(deep_result))

    def test_llm_author_payload_becomes_valid_compilable_programs(self):
        programs = geometry_programs_from_author_payload({"programs": [
            {"name": "courtyard_author", "dsl": "mass base = box(12, 9, 5)\nmass result = courtyard(base, margin_ratio=0.28)", "rationale": "carved court"},
            {"name": "fan_author", "dsl": "mass bar = box(11, 2, 3)\nmass moved = move(bar, 0, -1, 0)\nmass result = radial_array(moved, count=5, total_angle_degrees=72)", "rationale": "radial field"},
        ]}, expected_count=2)
        self.assertEqual(len(programs), 2)
        self.assertEqual(len({program.program_hash() for program in programs}), 2)
        self.assertEqual([program.metadata["base_seed"] for program in programs], ["block", "bar"])
        self.assertTrue(all(
            program.metadata["language_layer"] == "llm_authored_recursive_geometry"
            for program in programs
        ))
        self.assertTrue(all(program.metadata["author_batch_valid_count"] == 2 for program in programs))
        self.assertTrue(all(program.metadata["author_batch_rejected_count"] == 0 for program in programs))
        self.assertTrue(all(compile_geometry_program(program).status == "compiled" for program in programs))

    def test_llm_author_rejects_declared_base_seed_that_does_not_match_executable_dsl(self):
        with self.assertRaisesRegex(Exception, "declared_base_seed_slab_does_not_match_bar"):
            geometry_programs_from_author_payload({"programs": [{
                "name": "dishonest_seed",
                "base_seed": "slab",
                "intent_tags": ["long_span"],
                "dsl": "mass result = box(12, 2, 3)",
                "rationale": "mismatched declaration",
            }]}, expected_count=1)

    def test_llm_author_rejects_non_executable_typed_parameter_values(self):
        with self.assertRaisesRegex(Exception, "valid unique programs"):
            geometry_programs_from_author_payload({"programs": [{
                "name": "invalid_step_contract",
                "base_seed": "block",
                "intent_tags": ["stepped"],
                "dsl": (
                    "mass base = box(1, 1, 1)\n"
                    "mass result = setback(base, levels=4, direction='z', shift_per_level=0.06)"
                ),
                "rationale": "invalid scalar vector and vertical plan direction",
            }]}, expected_count=1)

    def test_closed_loop_recompiles_and_archives_vlm_ast_revision(self):
        original = parse_geometry_dsl("mass result = box(10, 8, 6)", name="author_box")

        def author(_context):
            return (original,)

        def critic(program, _compilation, _preview: Path):
            if program.root_id == "result":
                return {
                    "concept_scores": {"gesture_clarity": 0.35, "hierarchy": 0.55},
                    "critic_actions": ["too_box_like"],
                    "geometry_edits": [
                        {"operation": "add_node", "node_id": "critic_taper", "node_kind": "modifier", "operator": "taper", "input_ids": ["result"]},
                        {"operation": "set_parameter", "target_node_id": "critic_taper", "parameter_name": "end_scale", "vector_value": [0.48, 0.66]},
                        {"operation": "set_parameter", "target_node_id": "critic_taper", "parameter_name": "subdivisions", "numeric_value": 3},
                        {"operation": "set_root", "target_node_id": "critic_taper"},
                    ],
                }
            return {"concept_scores": {"gesture_clarity": 0.82, "hierarchy": 0.8}, "geometry_edits": []}

        with TemporaryDirectory() as directory:
            loop = run_geometry_program_a2a_loop(
                context={},
                target_count=2,
                author_programs=author,
                critic_program=critic,
                max_generations=2,
                preview_dir=directory,
                author_provider="deterministic_test",
                critic_provider="deterministic_test",
            )
        self.assertEqual(loop.trace["status"], "completed")
        self.assertEqual(loop.trace["geometry_revision_count"], 1)
        self.assertEqual(loop.trace["unique_geometry_count"], 2)
        self.assertFalse(loop.trace["vlm_geometry_critic_active"])
        self.assertTrue(loop.trace["critic_callback_active"])
        self.assertTrue(loop.trace["typed_ast_revision_active"])

    def test_program_rejected_vlm_parent_can_revise_but_cannot_enter_archive(self):
        original = parse_geometry_dsl("mass result = box(10, 8, 6)", name="wrong_program_parent")

        def critic(program, _compilation, _preview: Path):
            if program.root_id == "result":
                return {
                    "program_fit_hard_pass": False,
                    "concept_scores": {
                        "gesture_clarity": 0.8,
                        "hierarchy": 0.8,
                        "program_appropriateness": 0.2,
                        "section_program_fit": 0.2,
                    },
                    "critic_actions": ["wrong_program_typology", "missing_program_section"],
                    "geometry_edits": [
                        {"operation": "add_node", "node_id": "hall_taper", "node_kind": "modifier", "operator": "taper", "input_ids": ["result"]},
                        {"operation": "set_parameter", "target_node_id": "hall_taper", "parameter_name": "end_scale", "vector_value": [0.82, 0.92]},
                        {"operation": "set_parameter", "target_node_id": "hall_taper", "parameter_name": "subdivisions", "numeric_value": 3},
                        {"operation": "set_root", "target_node_id": "hall_taper"},
                    ],
                }
            return {
                "program_fit_hard_pass": True,
                "concept_scores": {
                    "gesture_clarity": 0.82,
                    "hierarchy": 0.8,
                    "program_appropriateness": 0.82,
                    "section_program_fit": 0.78,
                },
                "geometry_edits": [],
            }

        with TemporaryDirectory() as directory:
            loop = run_geometry_program_a2a_loop(
                context={"building_type": "gymnasium"},
                target_count=1,
                author_programs=lambda _context: (original,),
                critic_program=critic,
                max_generations=2,
                preview_dir=directory,
            )
        first = loop.trace["generations"][0]["records"][0]
        self.assertEqual(first["status"], "critic_program_fit_rejected")
        self.assertFalse(first["program_fit_hard_pass"])
        self.assertTrue(first["revision_proof"]["geometry_changed"])
        self.assertEqual(loop.trace["archive_count"], 1)
        self.assertTrue(all(candidate.program.root_id != "result" for candidate in loop.archive))
