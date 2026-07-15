"""Program-conditioned MAAS massing contracts."""

import random
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.affinity import rotate, scale, translate
from shapely.geometry import Polygon, box, mapping

from design.maas.grammar import generate_grammar_variants
from design.maas.grammar.component_graph import (
    MassComponentGraph,
    MassComponentNode,
    graph_from_sequence,
    primary_operation_from_sequence,
)
from design.maas.llm_proposals import build_site_context
from design.maas.llm_proposals import LlmProposalBatch
from design.maas.llm_proposals import (
    LlmProposalError,
    _feedback_prompt_payload,
    _field_topology_counts,
    _language_group_counts,
    _missing_requested_language_groups,
    _normalise_params,
    _validate_requested_language_groups,
    _validate_requested_field_topologies,
)
from design.maas.agents.llm_architect_agent import LLMArchitectAgent
from design.maas.interactive.language_brain import propose_language_mutation
from design.maas.program_massing import creative_archive_sequences, creative_seed_sequences, program_archive_sequences, program_search_prior, program_seed_sequences, resolve_program_profile
from design.maas.program_massing.benchmark import run_creative_20_archive_benchmark, run_neighborhood_20_language_benchmark, run_program_massing_benchmark, run_site_adaptation_benchmark
from design.maas.program_massing.grl_contract import build_archive_grl_contract
from design.maas.program_massing.graph_archive import bounded_behavior_frontier, field_topology_coverage
from design.maas.program_massing.adaptive_loop import run_adaptive_neighborhood_vlm_a2a_loop
from design.maas.program_massing.geometry_safety import safe_unary_union
from design.maas.program_massing.language_quality import assess_language_geometry
from design.maas.program_massing.vlm_a2a import (
    _binding_box_rejection,
    _field_topology,
    _has_editable_control_field,
    _historical_author_target,
    _language_group,
    _retain_geometry_best,
    _same_source_geometry,
    _source_far_utilization,
    _source_geometry_fingerprint,
    _select_language_balanced_archive,
    generation_feedback_from_result,
)
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import (
    ProgramElite,
    _descriptor_distance,
    _extract_overrides,
    _feature,
    _mutated_graph_parameters,
    _with_overrides,
)
from design.maas.program_massing.morphology import intrinsic_shape_distance, intrinsic_silhouette_distance
from design.maas.program_massing.portfolio_solver import PortfolioCandidateFacts, solve_portfolio_beam
from design.maas.program_massing.capacity_projection import project_bend_capacity
from design.maas.program_massing.creative import attach_creative_mass_evidence
from design.maas.program_massing.spatial_evaluation import attach_program_spatial_evidence
from design.maas.preference.reference_paths import resolve_reference_image_path
from design.maas.preference.vlm_scorer import VLM_PROMPT_CONTRACT_VERSION, _normalize_vlm_result, _prompt_text, _response_schema
from design.maas.grammar.parameter_schema import PARAMETERS_BY_VERB
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.compiler import _array_units
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.source_geometry.parametric_curves import swept_variable_ribbon
from design.maas.agents.orchestrator.generative_loop import CriticDirective, GraphEditDirective, run_generative_a2a_loop
from design.maas.agents.llm_architect_agent.graph_revision import apply_critic_graph_edits
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence


class MaasProgramMassingTest(SimpleTestCase):
    def test_author_validator_counts_executable_field_topology_not_candidate_name(self):
        data = {"candidates": [{
            "name": "fake_branched_name",
            "calls": [
                {"verb": "base", "role": "root", "params": "{}"},
                {"verb": "branch", "role": "primary", "params": "{}"},
                {
                    "verb": "bend",
                    "role": "support",
                    "params": '{"field_topology":"branched"}',
                },
            ],
        }]}
        feedback = {"required_field_topologies": {"parallel": 1, "branched": 1}}

        self.assertEqual(_field_topology_counts(data), {"parallel": 0, "branched": 0})
        with self.assertRaises(LlmProposalError):
            _validate_requested_field_topologies(data, feedback)

    def test_invalid_serialized_volume_is_repaired_without_aborting_population(self):
        bowtie = Polygon(((0, 0), (10, 10), (0, 10), (10, 0), (0, 0)))
        feature = {
            "type": "Feature",
            "geometry": mapping(box(0, 0, 10, 10)),
            "properties": {
                "benchmark_site_area_m2": 100.0,
                "mass_volumes": [{
                    "role": "primary_mass",
                    "geometry": mapping(bowtie),
                    "bottom_height": 0.0,
                    "top_height": 9.0,
                }],
                "source_signature": {
                    "surface_count": 6,
                    "coherence_evidence": {"score": 0.8, "hard_pass": True},
                },
            },
        }

        spatial = attach_program_spatial_evidence(
            feature,
            building_type="제1종근린생활시설",
            site_area_m2=100.0,
        )
        creative = attach_creative_mass_evidence(feature, site_area_m2=100.0)

        self.assertIn("architectural_score", spatial)
        self.assertIn("creative_score", creative)

    def test_invalid_source_polygon_does_not_abort_morphology_archive(self):
        bowtie = Polygon(((0, 0), (10, 10), (0, 10), (10, 0), (0, 0)))
        invalid = SourceMass(
            "invalid",
            bowtie,
            volumes=(SourceVolume("primary", bowtie, 0.0, 1.0, "bend"),),
        )
        valid_footprint = box(0, 0, 10, 10)
        valid = SourceMass(
            "valid",
            valid_footprint,
            volumes=(SourceVolume("primary", valid_footprint, 0.0, 1.0, "bar"),),
        )

        distance = intrinsic_silhouette_distance(invalid, valid)
        volume_distance, plan_distance = intrinsic_shape_distance(invalid, valid)

        self.assertGreaterEqual(distance, 0.0)
        self.assertGreaterEqual(volume_distance, 0.0)
        self.assertGreaterEqual(plan_distance, 0.0)

    def test_invalid_source_polygon_does_not_abort_archive_descriptor(self):
        bowtie = Polygon(((0, 0), (10, 10), (0, 10), (10, 0), (0, 0)))
        valid = box(0, 0, 10, 10)
        sequence = VerbSequence(
            "descriptor_safety", "descriptor safety",
            (VerbCall("base", {}), VerbCall("bar", {"axis": "x", "factor": 0.5})),
        )

        def elite(name, footprint):
            source = SourceMass(
                name,
                footprint,
                volumes=(SourceVolume("primary", footprint, 0.0, 1.0, "bar"),),
            )
            return ProgramElite(sequence, source, {"properties": {
                "program_spatial_evidence": {
                    "dominant_component_ratio": 1.0,
                    "site_coverage_ratio": 0.5,
                    "height_level_count": 1,
                },
            }}, 0.8, 0)

        self.assertGreaterEqual(_descriptor_distance(elite("invalid", bowtie), elite("valid", valid)), 0.0)

    def test_generation_feedback_carries_branched_field_deficit(self):
        feedback = generation_feedback_from_result({
            "status": "technical_fail",
            "visual_status": "automatic_visual_floor_failed",
            "selected_count": 13,
            "missing_language_groups": {"continuous_field": 1},
            "selected_field_topology_coverage": {
                "missing": {"branched": 1},
            },
            "trace": [],
        })

        self.assertGreaterEqual(feedback["quota"]["continuous_or_bent"], 4)
        self.assertEqual(feedback["required_field_topologies"]["branched"], 2)
        self.assertEqual(
            feedback["reference_signal_diagnosis"]["missing_field_topologies"],
            {"branched": 1},
        )
        self.assertEqual(
            _feedback_prompt_payload(feedback)["required_field_topologies"]["branched"],
            2,
        )

    def test_generation_feedback_does_not_reauthor_selector_only_topology_deficit(self):
        feedback = generation_feedback_from_result({
            "status": "technical_fail",
            "visual_status": "automatic_visual_floor_failed",
            "selected_count": 18,
            "missing_language_groups": {"continuous_field": 1},
            "selected_field_topology_coverage": {"missing": {"branched": 1}},
            "authored_field_topology_coverage": {
                "counts": {"parallel": 5, "branched": 3},
                "missing": {},
                "hard_pass": True,
            },
            "trace": [],
        })

        self.assertEqual(feedback["required_field_topologies"]["parallel"], 0)
        self.assertEqual(feedback["required_field_topologies"]["branched"], 0)
        self.assertEqual(
            feedback["reference_signal_diagnosis"]["missing_selected_field_topologies"],
            {"branched": 1},
        )
        self.assertEqual(
            feedback["reference_signal_diagnosis"]["missing_authored_field_topologies"],
            {},
        )

    def test_generation_feedback_requests_executable_missing_language_groups(self):
        feedback = generation_feedback_from_result({
            "status": "technical_fail",
            "visual_status": "automatic_visual_floor_failed",
            "selected_count": 17,
            "missing_language_groups": {"folded_section": 1, "stepped_capacity": 1},
            "selected_field_topology_coverage": {"missing": {}},
            "trace": [],
        })

        self.assertEqual(feedback["required_language_groups"], {
            "folded_section": 1,
            "stepped_capacity": 1,
        })
        prompt_feedback = _feedback_prompt_payload(feedback)
        self.assertEqual(prompt_feedback["required_language_groups"], feedback["required_language_groups"])

    def test_author_language_coverage_uses_primary_graph_operation_not_label(self):
        data = {"candidates": [
            {
                "name": "fake_folded_section_label",
                "formal_principle": "carved_solid",
                "mass_language": "notched_void",
                "calls": [
                    {"role": "root", "verb": "base", "params": "{}"},
                    {"role": "primary", "verb": "notch", "params": "{}"},
                ],
            },
            {
                "name": "real_fold",
                "formal_principle": "folded_section",
                "mass_language": "sloped_roof",
                "calls": [
                    {"role": "root", "verb": "base", "params": "{}"},
                    {"role": "primary", "verb": "sloped_roof_mass", "params": "{}"},
                ],
            },
            {
                "name": "real_terrace",
                "formal_principle": "stepped_landform",
                "mass_language": "terrace_ribbon",
                "calls": [
                    {"role": "root", "verb": "base", "params": "{}"},
                    {"role": "primary", "verb": "terrace_link", "params": "{}"},
                ],
            },
        ]}
        feedback = {"required_language_groups": {"folded_section": 2, "stepped_capacity": 1}}

        self.assertEqual(_language_group_counts(data), {
            "carved_void": 1,
            "folded_section": 1,
            "stepped_capacity": 1,
        })
        self.assertEqual(_missing_requested_language_groups(data, feedback), {"folded_section": 1})
        with self.assertRaises(LlmProposalError):
            _validate_requested_language_groups(data, feedback)

    def test_adaptive_loop_reauthors_from_honest_language_deficit(self):
        failed = {
            "status": "technical_fail",
            "visual_status": "automatic_visual_floor_failed",
            "selected_count": 17,
            "missing_language_groups": {"folded_section": 1, "stepped_capacity": 1},
            "selected_field_topology_coverage": {"missing": {}},
            "trace": [],
        }
        passed = {
            "status": "technical_pass",
            "visual_status": "review_required",
            "selected_count": 20,
            "missing_language_groups": {},
        }
        with TemporaryDirectory() as temporary, patch(
            "design.maas.program_massing.adaptive_loop.run_neighborhood_vlm_a2a_loop",
            side_effect=[failed, passed],
        ) as runner:
            root = Path(temporary)
            result = run_adaptive_neighborhood_vlm_a2a_loop(
                output_json=root / "board.json",
                output_png=root / "board.png",
                max_rounds=3,
            )

        self.assertEqual(runner.call_count, 2)
        second = runner.call_args_list[1].kwargs
        self.assertEqual(second["generation_feedback"]["required_language_groups"], {
            "folded_section": 1,
            "stepped_capacity": 1,
        })
        self.assertEqual(second["generation_feedback"]["required_field_topologies"]["branched"], 1)
        self.assertIn(root / "board.json", second["accepted_seed_result_paths"])
        self.assertEqual(result["adaptive_replenishment"]["status"], "visual_floor_reached")
        self.assertEqual(result["adaptive_replenishment"]["completed_rounds"], 2)

    def test_adaptive_loop_returns_best_round_when_later_round_regresses(self):
        better = {
            "status": "technical_fail",
            "visual_status": "automatic_visual_floor_failed",
            "selected_count": 18,
            "capacity_target_met_count": 10,
            "geometric_language_count": 7,
            "missing_language_groups": {},
            "selected_field_topology_coverage": {"missing": {}},
            "rows": [{"vlm_design_score": 0.74}],
            "trace": [],
        }
        regressed = {
            "status": "technical_fail",
            "visual_status": "automatic_visual_floor_failed",
            "selected_count": 17,
            "capacity_target_met_count": 9,
            "geometric_language_count": 6,
            "missing_language_groups": {"cluster_field": 1},
            "selected_field_topology_coverage": {"missing": {}},
            "rows": [{"vlm_design_score": 0.76}],
            "trace": [],
        }
        with TemporaryDirectory() as temporary, patch(
            "design.maas.program_massing.adaptive_loop.run_neighborhood_vlm_a2a_loop",
            side_effect=[better, regressed],
        ):
            root = Path(temporary)
            result = run_adaptive_neighborhood_vlm_a2a_loop(
                output_json=root / "board.json",
                output_png=root / "board.png",
                max_rounds=2,
            )

        self.assertEqual(result["selected_count"], 18)
        self.assertEqual(result["adaptive_replenishment"]["best_round"], 1)
        self.assertEqual(result["adaptive_replenishment"]["last_round"], 2)
        self.assertTrue(result["adaptive_replenishment"]["monotonic_best_so_far"])

    def test_box_critic_is_not_overridden_by_family_label_alone(self):
        box_feature = {"properties": {
            "program_spatial_evidence": {"spatial_role_projection": {
                "profiled_roof_present": False,
                "non_rectilinear_component_count": 0,
                "envelope_void_ratio": 0.06,
            }},
            "source_signature": {"continuous_surface_evidence": {"hard_pass": False}},
            "preference_distillation": {
                "concept_scores": {"form_coherence": 0.78, "visual_quality": 0.72},
                "critic_actions": ["too_box_like"],
            },
        }}
        profiled_feature = {"properties": {
            **box_feature["properties"],
            "source_signature": {"continuous_surface_evidence": {"hard_pass": True}},
        }}

        self.assertTrue(_binding_box_rejection(box_feature, {"too_box_like"}))
        self.assertFalse(_binding_box_rejection(profiled_feature, {"too_box_like"}))

    def test_stepped_language_requires_real_sectional_progression(self):
        footprint = box(0, 0, 20, 10)
        flat_stack = SourceMass(
            "flat_stack",
            footprint,
            volumes=(
                SourceVolume("lower", footprint, 0.0, 0.34, "stack"),
                SourceVolume("middle", footprint, 0.34, 0.67, "stack"),
                SourceVolume("upper", footprint, 0.67, 1.0, "stack"),
            ),
        )
        stepped_stack = SourceMass(
            "stepped_stack",
            footprint,
            volumes=(
                SourceVolume("lower", footprint, 0.0, 0.34, "stack"),
                SourceVolume("middle", box(2, 0, 20, 10), 0.34, 0.67, "stack"),
                SourceVolume("upper", box(5, 0, 20, 10), 0.67, 1.0, "stack"),
            ),
        )
        feature = {"properties": {
            "source_signature": {"coherence_evidence": {
                "hard_pass": True,
                "small_fragment_count": 0,
                "redundant_overlap_pair_count": 0,
                "collision_energy": 0.0,
            }},
            "program_spatial_evidence": {"spatial_role_projection": {}},
        }}

        flat = assess_language_geometry(flat_stack, feature, "stepped_capacity")
        stepped = assess_language_geometry(stepped_stack, feature, "stepped_capacity")

        self.assertFalse(flat["geometry_pass"])
        self.assertFalse(flat["sectional_progression"])
        self.assertTrue(stepped["geometry_pass"])
        self.assertTrue(stepped["sectional_progression"])

    def test_cluster_language_rejects_uniform_detached_lego_array(self):
        equal_boxes = tuple(
            SourceVolume(f"cell_{index}", translate(box(0, 0, 4, 4), xoff=index * 6), 0.0, 1.0, "array")
            for index in range(3)
        )
        footprint = safe_unary_union([volume.footprint for volume in equal_boxes])
        source = SourceMass("uniform_array", footprint, volumes=equal_boxes)
        feature = {"properties": {
            "source_signature": {"coherence_evidence": {
                "hard_pass": True,
                "small_fragment_count": 0,
                "redundant_overlap_pair_count": 0,
                "collision_energy": 0.0,
            }},
            "program_spatial_evidence": {"spatial_role_projection": {}},
        }}

        evidence = assess_language_geometry(source, feature, "cluster_field")

        self.assertFalse(evidence["geometry_pass"])
        self.assertEqual(evidence["normalized_component_area_spread"], 0.0)

    def test_array_grammar_materializes_authored_component_hierarchy(self):
        units = _array_units(
            box(0, 0, 24, 18),
            "x",
            3,
            0.22,
            0.42,
            hierarchy_ratio=0.24,
            stagger_ratio=0.14,
        )
        areas = [float(unit.area) for unit in units]
        normalized_spread = (max(areas) - min(areas)) / (sum(areas) / len(areas))

        self.assertEqual(len(units), 3)
        self.assertGreaterEqual(normalized_spread, 0.08)
        self.assertLess(units[0].centroid.y, units[1].centroid.y)

    def test_llm_array_parameters_are_persisted_within_typed_bounds(self):
        params = _normalise_params("array", {
            "axis": "y",
            "n": 4,
            "spacing_ratio": 0.22,
            "unit_scale": 0.78,
            "hierarchy_ratio": 0.64,
            "stagger_ratio": 0.31,
            "lower_floor_fraction": 0.42,
        })

        self.assertEqual(params["unit_scale"], 0.70)
        self.assertEqual(params["hierarchy_ratio"], 0.36)
        self.assertEqual(params["stagger_ratio"], 0.28)

    def test_critic_archive_preserves_parent_when_distinct_child_is_worse(self):
        sequence = VerbSequence(
            "critic_archive_parent",
            "critic archive parent",
            (VerbCall("base", {}), VerbCall("bar", {"axis": "x", "factor": 0.5})),
        )
        parent_footprint = box(0, 0, 12, 8)
        child_footprint = box(0, 0, 9, 8)
        parent = ProgramElite(
            sequence,
            SourceMass(
                "parent",
                parent_footprint,
                volumes=(SourceVolume("parent", parent_footprint, 0.0, 1.0, "bar"),),
            ),
            {"properties": {}},
            0.82,
            0,
        )
        child = ProgramElite(
            replace(sequence, name="critic_archive_child"),
            SourceMass(
                "child",
                child_footprint,
                volumes=(SourceVolume("child", child_footprint, 0.0, 1.0, "bar"),),
            ),
            {"properties": {}},
            0.61,
            1,
        )
        archive: dict[str, ProgramElite] = {}

        _retain_geometry_best(archive, parent)
        _retain_geometry_best(archive, child)

        self.assertEqual(len(archive), 2)
        self.assertIn(parent, archive.values())
        self.assertIn(child, archive.values())

    def test_portfolio_beam_escapes_greedy_one_blocks_two_failure(self):
        facts = [
            PortfolioCandidateFacts(0.99, "a", "p0", "t0"),
            PortfolioCandidateFacts(0.82, "a", "p1", "t1"),
            PortfolioCandidateFacts(0.81, "b", "p2", "t2"),
            PortfolioCandidateFacts(0.80, "c", "p3", "t3"),
        ]
        compatibility = [[True] * 4 for _ in range(4)]
        for other in (1, 2):
            compatibility[0][other] = False
            compatibility[other][0] = False

        selected = solve_portfolio_beam(
            facts,
            compatibility,
            target_count=3,
            minimum_groups={"a": 1, "b": 1, "c": 1},
        )

        self.assertEqual(set(selected), {1, 2, 3})

    def test_portfolio_beam_reserves_editable_surface_genotypes(self):
        facts = [
            PortfolioCandidateFacts(0.99, "folded_section", "folded", "box_a"),
            PortfolioCandidateFacts(0.98, "folded_section", "folded", "box_b"),
            PortfolioCandidateFacts(0.87, "folded_section", "folded", "loft_a", editable_field=True),
            PortfolioCandidateFacts(0.86, "continuous_field", "ribbon", "ribbon_a", editable_field=True),
        ]
        compatibility = [[True] * 4 for _ in range(4)]

        selected = solve_portfolio_beam(
            facts,
            compatibility,
            target_count=3,
            minimum_groups={"folded_section": 1, "continuous_field": 1},
            minimum_editable_field_count=2,
        )

        self.assertEqual(len(selected), 3)
        self.assertGreaterEqual(sum(facts[index].editable_field for index in selected), 2)

    def test_vlm_structural_edit_contract_rejects_invented_verbs(self):
        verb_schema = _response_schema()["properties"]["graph_edits"]["items"]["properties"]["verb"]

        self.assertIn("bend", verb_schema["enum"])
        self.assertIn("sloped_roof_mass", verb_schema["enum"])
        self.assertNotIn("void_link", verb_schema["enum"])
        self.assertIn("graph_edit", VLM_PROMPT_CONTRACT_VERSION)

    def test_vlm_prompt_exposes_source_graph_primary_instead_of_empty_root(self):
        graph = MassComponentGraph(
            "critic_graph",
            "Critic graph",
            (
                MassComponentNode("root", "root", VerbCall("base", {})),
                MassComponentNode(
                    "primary_ribbon",
                    "primary",
                    VerbCall("bend", {"factor": 0.14}),
                    parent_id="root",
                ),
            ),
        )
        feature = {"properties": {"source_signature": {"component_graph": graph.to_dict()}}}

        prompt = _prompt_text(feature, [])

        self.assertIn('"primary_node_id": "primary_ribbon"', prompt)
        self.assertIn('"node_id": "primary_ribbon"', prompt)
        self.assertIn("Never target the base/root node", prompt)

    def test_historical_author_cache_keeps_its_original_population_contract(self):
        with TemporaryDirectory() as tmp:
            cache = Path(tmp) / "historical.json"
            cache.write_text(
                __import__("json").dumps({
                    "target_count": 3,
                    "data": {"candidates": [{}, {}, {}, {}]},
                }),
                encoding="utf-8",
            )

            target = _historical_author_target(cache, fallback=32)

        self.assertEqual(target, 3)

    def test_vlm_can_mutate_existing_bend_control_point_as_typed_graph_edit(self):
        controls = [[0.04, 0.25], [0.32, 0.62], [0.68, 0.38], [0.96, 0.72]]
        graph = MassComponentGraph(
            "bend_graph",
            "Bend graph",
            (
                MassComponentNode("root", "root", VerbCall("base", {})),
                MassComponentNode(
                    "primary_bend",
                    "primary",
                    VerbCall("bend", {"control_points": controls}),
                    parent_id="root",
                ),
            ),
        )
        directive = CriticDirective(graph_edits=(GraphEditDirective(
            operation="set_control_point",
            target_node_id="primary_bend",
            control_point_index=1,
            control_point_u=0.40,
            control_point_v=0.78,
        ),))

        revised = apply_critic_graph_edits(graph.to_sequence(), directive)

        self.assertEqual(len(revised), 1)
        revised_graph = graph_from_sequence(revised[0])
        revised_controls = revised_graph.nodes[1].operation.params["control_points"]
        self.assertEqual(revised_controls[1], [0.4, 0.78])
        self.assertIn("control_points", PARAMETERS_BY_VERB["bend"])
        operation_schema = _response_schema()["properties"]["graph_edits"]["items"]["properties"]["operation"]
        self.assertIn("set_control_point", operation_schema["enum"])

    def test_agent_section_controls_compile_to_distinct_site_loft_and_vlm_can_edit_them(self):
        ridge_controls = [[0.03, 0.28], [0.28, 0.58], [0.50, 0.88], [0.72, 0.56], [0.97, 0.24]]
        valley_controls = [[0.03, 0.82], [0.28, 0.52], [0.50, 0.20], [0.72, 0.55], [0.97, 0.84]]

        def compile_profile(name, controls):
            sequence = VerbSequence(
                name,
                name,
                (
                    VerbCall("base", {}),
                    VerbCall("sloped_roof_mass", {
                        "axis": "x",
                        "upper_ratio": 0.90,
                        "x_ratio": 0.82,
                        "y_ratio": 0.78,
                        "lower_floor_fraction": 0.42,
                        "field_samples": 7,
                        "longitudinal_wave": 0.12,
                        "twist": 0.16,
                        "control_points": controls,
                    }),
                ),
                notes=("formal_principle=folded_section",),
            )
            return sequence, compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)

        ridge_sequence, ridge = compile_profile("llm_sloped_roof_ridge", ridge_controls)
        _, valley = compile_profile("llm_sloped_roof_valley", valley_controls)

        self.assertIsNotNone(ridge)
        self.assertIsNotNone(valley)
        evidence = ridge.signature()["continuous_surface_evidence"]
        self.assertEqual(evidence["representation"], "agent_section_loft_quad_mesh")
        self.assertLessEqual(evidence["surface_count"], 48)
        self.assertEqual(evidence["section_field"]["authored_station_count"], 7)
        self.assertEqual(evidence["section_field"]["review_lod_station_count"], 5)
        self.assertEqual(evidence["section_field"]["section_interpolation"], "smooth")
        self.assertEqual(evidence["section_field"]["compiled_section_point_count"], 7)
        self.assertGreaterEqual(evidence["section_field"]["section_height_range"], 0.18)
        self.assertLessEqual(evidence["section_field"]["max_normalized_segment_slope"], 4.5)
        ridge_roof = [surface for surface in ridge.surfaces if surface.surface_type == "profiled_section_loft_roof"]
        valley_roof = [surface for surface in valley.surfaces if surface.surface_type == "profiled_section_loft_roof"]
        self.assertTrue(ridge_roof)
        self.assertNotEqual(ridge_roof[0].vertices_m, valley_roof[0].vertices_m)
        self.assertGreaterEqual(len({round(vertex[2], 3) for surface in ridge_roof for vertex in surface.vertices_m}), 4)
        ridge_feature = _feature(
            ridge, ridge_sequence, building_type="neighborhood living", height=18, floors=5, site_area=2400
        )
        self.assertTrue(assess_language_geometry(ridge, ridge_feature, "folded_section")["geometry_pass"])
        spatial = attach_program_spatial_evidence(
            ridge_feature, building_type="neighborhood living", site_area_m2=2400
        )
        self.assertTrue(spatial["agent_section_loft"])
        self.assertGreaterEqual(spatial["hierarchy_score"], 0.5)

        graph = graph_from_sequence(ridge_sequence)
        primary_id = graph.nodes[1].node_id
        directive = CriticDirective(graph_edits=(GraphEditDirective(
            operation="set_control_point",
            target_node_id=primary_id,
            control_point_index=2,
            control_point_u=0.50,
            control_point_v=0.68,
        ),))
        revised = apply_critic_graph_edits(ridge_sequence, directive)
        self.assertEqual(len(revised), 1)
        self.assertEqual(graph_from_sequence(revised[0]).nodes[1].operation.params["control_points"][2], [0.5, 0.68])
        self.assertIn("control_points", PARAMETERS_BY_VERB["sloped_roof_mass"])

    def test_program_search_mutates_section_control_field_not_only_scalar_ratios(self):
        controls = [[0.04, 0.24], [0.27, 0.63], [0.52, 0.38], [0.76, 0.72], [0.96, 0.49]]
        seed = VerbSequence(
            "agent_section_genotype",
            "agent section genotype",
            (
                VerbCall("base", {}),
                VerbCall("sloped_roof_mass", {
                    "axis": "x",
                    "x_ratio": 0.72,
                    "y_ratio": 0.58,
                    "upper_ratio": 0.86,
                    "lower_floor_fraction": 0.28,
                    "field_samples": 7,
                    "longitudinal_wave": 0.08,
                    "twist": -0.06,
                    "control_points": controls,
                }),
            ),
            notes=("formal_principle=folded_section",),
        )

        parent = _extract_overrides(seed)
        overrides = _mutated_graph_parameters(seed, parent, random.Random(417))
        child = _with_overrides(seed, overrides, generation=1, index=0)
        child_controls = child.calls[1].params["control_points"]

        self.assertNotEqual(child_controls, controls)
        self.assertEqual(len(child_controls), len(controls))
        self.assertTrue(all(
            float(right[0]) - float(left[0]) >= 0.035
            for left, right in zip(child_controls, child_controls[1:])
        ))
        extracted_child = _extract_overrides(child)
        self.assertIn("call_1__control_point_2_v", extracted_child)
        self.assertAlmostEqual(
            extracted_child["call_1__control_point_2_v"],
            float(child_controls[2][1]),
        )
        parent_source = compile_sequence_to_source_mass(box(0, 0, 24, 18), seed)
        child_source = compile_sequence_to_source_mass(box(0, 0, 24, 18), child)
        self.assertIsNotNone(parent_source)
        self.assertIsNotNone(child_source)
        self.assertNotEqual(
            parent_source.signature()["continuous_surface_evidence"]["section_field"]["control_points"],
            child_source.signature()["continuous_surface_evidence"]["section_field"]["control_points"],
        )

    def test_capacity_projection_preserves_authored_curve_and_changes_only_occupiable_section(self):
        controls = [[0.04, 0.25], [0.32, 0.62], [0.68, 0.38], [0.96, 0.72]]
        sequence = VerbSequence(
            "thin_curve",
            "Thin curve",
            (
                VerbCall("base", {}),
                VerbCall("bend", {
                    "lane_count": 2,
                    "lane_width_ratio": 0.08,
                    "vertical_overlap": 0.18,
                    "curvature": 0.12,
                    "control_points": controls,
                }),
            ),
        )

        projected = project_bend_capacity(
            sequence,
            observed_utilization=0.42,
            target_utilization=0.90,
        )

        self.assertIsNotNone(projected)
        primary = primary_operation_from_sequence(projected)
        self.assertEqual(primary.params["control_points"], controls)
        self.assertEqual(primary.params["curvature"], 0.12)
        self.assertEqual(primary.params["lane_count"], 3)
        self.assertGreater(primary.params["lane_width_ratio"], 0.08)
        self.assertGreater(primary.params["vertical_overlap"], 0.18)
        self.assertTrue(any("capacity_projection=observed_far_feedback" in note for note in projected.notes))

    def test_vlm_drops_control_point_edit_when_target_has_no_editable_curve(self):
        feature = {
            "properties": {
                "source_signature": {
                    "component_graph": {
                        "nodes": [{
                            "node_id": "primary_box",
                            "role": "primary",
                            "operation": {"verb": "bar", "params": {}},
                        }],
                    },
                },
            },
        }
        payload = {
            "concept_scores": {},
            "graph_edits": [{
                "operation": "set_control_point",
                "target_node_id": "primary_box",
                "control_point_index": 1,
                "control_point_u": 0.4,
                "control_point_v": 0.7,
            }],
        }

        normalized = _normalize_vlm_result(payload, model="test", response_id="r", feature=feature)

        self.assertEqual(normalized["graph_edits"], [])

    def test_editable_control_field_requires_real_bend_control_points(self):
        sequence = VerbSequence(
            "editable_bend",
            "Editable bend",
            (
                VerbCall("base", {}),
                VerbCall("bend", {"control_points": [
                    [0.04, 0.25], [0.32, 0.62], [0.68, 0.38], [0.96, 0.72],
                ]}),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 30, 18), sequence)
        feature = _feature(source, sequence, building_type="test", height=12, floors=3, site_area=540)
        elite = ProgramElite(sequence, source, feature, 0.8, 0)

        self.assertTrue(_has_editable_control_field(elite))

    def test_review_dedup_preserves_editable_genotype_for_same_geometry(self):
        controls = [[0.04, 0.25], [0.32, 0.62], [0.68, 0.38], [0.96, 0.72]]
        editable = VerbSequence(
            "editable",
            "Editable",
            (VerbCall("base", {}), VerbCall("bend", {"control_points": controls})),
        )
        frozen = VerbSequence(
            "frozen",
            "Frozen",
            (VerbCall("base", {}), VerbCall("bend", {})),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 30, 18), editable)
        feature = _feature(source, editable, building_type="test", height=12, floors=3, site_area=540)
        editable_elite = ProgramElite(editable, source, feature, 0.7, 0)
        frozen_elite = ProgramElite(frozen, source, feature, 0.9, 0)

        selected = _select_language_balanced_archive(
            [frozen_elite, editable_elite],
            target_count=1,
            minimum_distance=0.0,
            minimum_groups={},
            minimum_editable_field_count=1,
        )

        self.assertEqual(selected[0].sequence.name, "editable")

    def test_profiled_surface_silhouette_is_translation_invariant(self):
        footprint = box(0, 0, 20, 10)
        volume = SourceVolume("profiled_main", footprint, 0.0, 1.0, "bend")
        surface = SourceSurface(
            "profiled_roof",
            "profiled_main",
            "bend",
            "profiled_roof",
            ((0.0, 0.0, 0.2), (20.0, 0.0, 0.2), (20.0, 10.0, 1.0), (0.0, 10.0, 0.6)),
        )
        source = SourceMass("profile", footprint, volumes=(volume,), surfaces=(surface,))
        moved = SourceMass(
            "profile_moved",
            translate(footprint, xoff=312000.0, yoff=4150000.0),
            volumes=(replace(volume, footprint=translate(volume.footprint, xoff=312000.0, yoff=4150000.0)),),
            surfaces=(surface,),
        )

        self.assertLess(intrinsic_silhouette_distance(source, moved), 0.001)

    def test_archive_fingerprint_keeps_distinct_profiled_surfaces_with_same_proxy_volume(self):
        footprint = box(0, 0, 20, 10)
        volume = SourceVolume("profiled_main", footprint, 0.0, 1.0, "bend")

        def candidate(name: str, heights: tuple[float, float, float, float], score: float) -> ProgramElite:
            surface = SourceSurface(
                f"{name}_roof",
                "profiled_main",
                "bend",
                "profiled_roof",
                (
                    (0.0, 0.0, heights[0]),
                    (20.0, 0.0, heights[1]),
                    (20.0, 10.0, heights[2]),
                    (0.0, 10.0, heights[3]),
                ),
            )
            source = SourceMass(name, footprint, volumes=(volume,), surfaces=(surface,))
            sequence = VerbSequence(name, name, (VerbCall("base", {}), VerbCall("bend", {})))
            feature = _feature(
                source,
                sequence,
                building_type="제1종근린생활시설",
                height=12.0,
                floors=3,
                site_area=float(footprint.area),
            )
            feature["properties"]["program_spatial_evidence"] = {
                "dominant_component_ratio": 1.0,
                "site_coverage_ratio": 1.0,
                "height_level_count": 2,
            }
            return ProgramElite(sequence, source, feature, score, 0)

        low_fold = candidate("low_fold", (0.2, 0.2, 0.6, 0.6), 0.9)
        diagonal_fold = candidate("diagonal_fold", (0.1, 0.9, 1.0, 0.2), 0.8)

        self.assertEqual(low_fold.source.source_volume_signatures(), diagonal_fold.source.source_volume_signatures())
        self.assertGreater(intrinsic_silhouette_distance(low_fold.source, diagonal_fold.source), 0.1)
        self.assertNotEqual(
            _source_geometry_fingerprint(low_fold.source),
            _source_geometry_fingerprint(diagonal_fold.source),
        )

    def test_vlm_graph_edit_supports_typed_categorical_parameter(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        graph = MassComponentGraph(
            "editable_court",
            "editable court",
            (
                MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored),
                MassComponentNode(
                    "court_primary",
                    "primary",
                    VerbCall("courtyard", {
                        "ratio": 0.28,
                        "open_side": "closed",
                        "upper_ratio": 0.82,
                        "lower_floor_fraction": 0.38,
                    }),
                    "root",
                    constraints=authored,
                ),
            ),
        )
        directive = CriticDirective(graph_edits=(GraphEditDirective(
            operation="set_parameter",
            target_node_id="court_primary",
            parameter_name="open_side",
            string_value="south",
        ),))

        revised = apply_critic_graph_edits(graph.to_sequence(), directive)

        self.assertEqual(len(revised), 1)
        self.assertEqual(
            graph_from_sequence(revised[0]).nodes[1].operation.params["open_side"],
            "south",
        )

    def test_vlm_topology_edit_requires_explicit_followup_parameter(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        graph = MassComponentGraph(
            "editable_offset",
            "editable offset",
            (
                MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored),
                MassComponentNode(
                    "offset_primary",
                    "primary",
                    VerbCall("offset", {
                        "axis": "x",
                        "distance_ratio": 0.2,
                        "other_scale": 0.6,
                        "upper_ratio": 0.78,
                        "lower_floor_fraction": 0.38,
                    }),
                    "root",
                    constraints=authored,
                ),
            ),
        )
        empty_replace = CriticDirective(graph_edits=(GraphEditDirective(
            operation="replace_operation",
            target_node_id="offset_primary",
            verb="bend",
        ),))
        parameterized_replace = CriticDirective(graph_edits=(
            GraphEditDirective(
                operation="replace_operation",
                target_node_id="offset_primary",
                verb="bend",
            ),
            GraphEditDirective(
                operation="set_parameter",
                target_node_id="offset_primary",
                parameter_name="angle",
                numeric_value=24.0,
            ),
        ))

        self.assertEqual(apply_critic_graph_edits(graph.to_sequence(), empty_replace), ())
        revised = apply_critic_graph_edits(graph.to_sequence(), parameterized_replace)
        self.assertEqual(len(revised), 1)
        primary = graph_from_sequence(revised[0]).nodes[1]
        self.assertEqual(primary.operation.verb, "bend")
        self.assertEqual(primary.operation.params["angle"], 24.0)

    def test_vlm_graph_edit_rejects_wrong_verb_parameter_and_applies_canonical_one(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        graph = MassComponentGraph(
            "editable_offset",
            "editable offset",
            (
                MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored),
                MassComponentNode(
                    "offset_primary",
                    "primary",
                    VerbCall("offset", {"axis": "x", "distance_ratio": 0.2, "other_scale": 0.6}),
                    "root",
                    constraints=authored,
                ),
            ),
        )
        wrong = CriticDirective(graph_edits=(GraphEditDirective(
            operation="set_parameter",
            target_node_id="offset_primary",
            parameter_name="x_ratio",
            numeric_value=0.4,
        ),))
        valid = CriticDirective(graph_edits=(GraphEditDirective(
            operation="set_parameter",
            target_node_id="offset_primary",
            parameter_name="distance_ratio",
            numeric_value=0.08,
        ),))

        self.assertEqual(apply_critic_graph_edits(graph.to_sequence(), wrong), ())
        revised = apply_critic_graph_edits(graph.to_sequence(), valid)
        self.assertEqual(len(revised), 1)
        self.assertEqual(
            graph_from_sequence(revised[0]).nodes[1].operation.params["distance_ratio"],
            0.08,
        )

    def test_same_source_geometry_includes_profiled_surface_vertices(self):
        sequence = VerbSequence(
            "surface_identity",
            "surface identity",
            (VerbCall("base", {}), VerbCall("bend", {"height_mid_ratio": 0.7})),
        )
        first = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)
        second = compile_sequence_to_source_mass(
            box(0, 0, 60, 40),
            VerbSequence(
                "surface_changed",
                "surface changed",
                (VerbCall("base", {}), VerbCall("bend", {"height_mid_ratio": 0.98})),
            ),
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertFalse(_same_source_geometry(first, second))
        self.assertGreater(intrinsic_silhouette_distance(first, second), 0.01)

    def test_reference_path_resolver_recovers_historical_docs_relative_path(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "docs" / "references" / "precedent.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"reference")

            resolved = resolve_reference_image_path(
                "../../docs/references/precedent.jpg",
                root=root,
            )

            self.assertEqual(resolved, image.resolve())

    def test_graph_native_contract_rejects_multiple_primary_nodes(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        graph = MassComponentGraph(
            "invalid_two_primary",
            "invalid two primary",
            (
                MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored),
                MassComponentNode(
                    "array_primary", "primary", VerbCall("array", {"n": 3}),
                    "root", constraints=authored,
                ),
                MassComponentNode(
                    "court_primary", "primary", VerbCall("courtyard", {"ratio": 0.3}),
                    "array_primary", constraints=authored, relation="deform",
                ),
            ),
        )

        self.assertIn(
            "graph-native component graph requires exactly one primary node",
            graph.validate(),
        )

    def test_graph_native_language_uses_primary_role_not_flat_call_position(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        graph = MassComponentGraph(
            "branched_role_order",
            "branched role order",
            (
                MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored),
                MassComponentNode(
                    "branch_support", "support", VerbCall("branch", {"count": 2}),
                    "root", constraints=authored,
                ),
                MassComponentNode(
                    "bend_primary", "primary",
                    VerbCall("bend", {"field_topology": "branched", "lane_count": 3}),
                    "root", constraints=authored,
                ),
            ),
        )
        sequence = graph.to_sequence()
        footprint = box(0, 0, 30, 20)
        source = SourceMass(
            sequence.name,
            footprint,
            volumes=(SourceVolume("primary", footprint, 0.0, 1.0, "bend"),),
        )
        elite = ProgramElite(
            sequence,
            source,
            {"properties": {"normalized_far_utilization": 0.8}},
            0.8,
            0,
        )

        self.assertEqual(primary_operation_from_sequence(sequence).verb, "bend")
        self.assertEqual(_language_group(elite), "continuous_field")
        self.assertEqual(_field_topology(elite), "branched")

    def test_graph_native_compiler_uses_primary_family_over_support_label(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        graph = MassComponentGraph(
            "llm_branched_bend_offset_twin_bar",
            "primary bend with optional offset support",
            (
                MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored),
                MassComponentNode(
                    "bend_primary", "primary",
                    VerbCall("bend", {
                        "angle": 24.0,
                        "factor": 0.8,
                        "upper_ratio": 0.82,
                        "lower_floor_fraction": 0.36,
                        "field_topology": "branched",
                        "lane_count": 3,
                        "lane_width_ratio": 0.16,
                    }),
                    "root", constraints=authored,
                ),
                MassComponentNode(
                    "offset_support", "support",
                    VerbCall("offset", {
                        "axis": "x", "distance_ratio": 0.2,
                        "other_scale": 0.72, "upper_ratio": 0.8,
                        "lower_floor_fraction": 0.36,
                    }),
                    "bend_primary", constraints=authored,
                ),
            ),
        )

        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), graph.to_sequence())

        self.assertIsNotNone(source)
        self.assertEqual(source.signature()["formal_principle"], "continuous_ribbon_field")
        self.assertEqual(len(source.volumes), 1)
        self.assertTrue(all("branched_ribbon" in volume.role for volume in source.volumes))
        feature = _feature(
            source, graph.to_sequence(),
            building_type="neighborhood living", height=15.0, floors=5, site_area=2400.0,
        )
        attach_program_massing_evidence(feature, building_type="neighborhood living")
        spatial = feature["properties"]["program_spatial_evidence"]
        self.assertTrue(spatial["single_solid_profiled_field"])
        self.assertEqual(spatial["profiled_design_patch_count"], 3)
        self.assertLess(spatial["dominant_component_ratio"], 1.0)
        self.assertGreaterEqual(spatial["hierarchy_score"], 0.5)

    def test_ribbon_width_contract_allows_capacity_search_to_thicken_field(self):
        def compile_width(width):
            return compile_sequence_to_source_mass(
                box(0, 0, 60, 40),
                VerbSequence(
                    f"width_{width}", f"width {width}",
                    (VerbCall("base", {}), VerbCall("bend", {
                        "angle": 18.0,
                        "factor": 0.8,
                        "upper_ratio": 0.82,
                        "lower_floor_fraction": 0.36,
                        "field_topology": "branched",
                        "lane_count": 3,
                        "lane_width_ratio": width,
                    })),
                ),
            )

        narrow = compile_width(0.09)
        wide = compile_width(0.16)

        self.assertIsNotNone(narrow)
        self.assertIsNotNone(wide)
        narrow_area = sum(float(volume.footprint.area) for volume in narrow.volumes)
        wide_area = sum(float(volume.footprint.area) for volume in wide.volumes)
        self.assertGreater(wide_area, narrow_area * 1.25)

    def test_graph_native_search_override_updates_executable_graph_envelope(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "offset_primary",
            "primary",
            VerbCall("offset", {
                "axis": "x",
                "distance_ratio": 0.27,
                "other_scale": 0.62,
                "upper_ratio": 0.78,
                "lower_floor_fraction": 0.38,
            }),
            "root",
            constraints=authored,
        )
        graph = MassComponentGraph("search_graph", "search graph", (root, primary))
        seed = graph.to_sequence()

        child = _with_overrides(seed, {"call_1__distance_ratio": 0.05}, 0, 1)

        self.assertEqual(child.calls[1].params["distance_ratio"], 0.05)
        self.assertEqual(
            graph_from_sequence(child).nodes[1].operation.params["distance_ratio"],
            0.05,
        )
        base = compile_sequence_to_source_mass(box(0, 0, 60, 40), seed)
        changed = compile_sequence_to_source_mass(box(0, 0, 60, 40), child)
        self.assertIsNotNone(base)
        self.assertIsNotNone(changed)
        self.assertNotEqual(base.source_volume_signatures(), changed.source_volume_signatures())

    def test_variable_width_sweep_materializes_tapered_continuous_mass(self):
        sweep = swept_variable_ribbon(
            ((1.0, 5.0), (5.0, 5.0), (9.0, 5.0)),
            half_widths=(0.8, 2.4, 0.8),
            clip=box(0, 0, 10, 10),
        )

        self.assertIsNotNone(sweep)
        self.assertTrue(sweep.is_valid)
        middle_depth = sweep.intersection(box(4.5, 0, 5.5, 10)).area
        end_depth = sweep.intersection(box(1.0, 0, 2.0, 10)).area
        self.assertGreater(middle_depth, end_depth * 1.5)

    def test_behavior_frontier_keeps_multiple_elites_without_all_pair_pool(self):
        sequence = VerbSequence(
            "frontier_bar",
            "frontier bar",
            (VerbCall("base", {}), VerbCall("bar", {"axis": "x", "factor": 0.5})),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)
        population = [
            ProgramElite(sequence, source, {"properties": {}}, score / 10.0, 0)
            for score in range(10)
        ]

        frontier = bounded_behavior_frontier(population, per_cell=3, minimum_count=0)

        self.assertEqual(len(frontier), 3)
        self.assertEqual([item.score for item in frontier], [0.9, 0.8, 0.7])

    def test_field_topology_coverage_requires_geometry_not_pose_variants(self):
        parallel = VerbSequence(
            "parallel", "parallel", (VerbCall("base", {}), VerbCall("bend", {"field_topology": "parallel"})),
        )
        branched = VerbSequence(
            "branched", "branched", (VerbCall("base", {}), VerbCall("bend", {"field_topology": "branched"})),
        )

        self.assertFalse(field_topology_coverage((parallel,))["hard_pass"])
        self.assertTrue(field_topology_coverage((parallel, branched))["hard_pass"])

    def test_grl_archive_contract_exposes_pose_invariant_duplicate_relation(self):
        contract = build_archive_grl_contract(
            dataset_id="maas:test",
            title="test archive",
            source_path="result.json",
            site={"pnu": "test-pnu", "area_m2": 2400},
            candidates=[
                {
                    "variant_id": "candidate_a",
                    "formal_principle": "carved_atrium",
                    "language_group": "carved_void",
                    "vlm_design_score": 0.8,
                    "normalized_far_utilization": 0.9,
                    "volume_count": 2,
                    "surface_count": 12,
                },
                {
                    "variant_id": "candidate_b",
                    "formal_principle": "carved_atrium",
                    "language_group": "carved_void",
                    "vlm_design_score": 0.75,
                    "normalized_far_utilization": 0.92,
                    "volume_count": 2,
                    "surface_count": 12,
                },
            ],
            morphology_relations=[{"left": 0, "right": 1, "distance": 0.04}],
        )

        self.assertEqual(contract["schemaVersion"], "grl/v1")
        self.assertEqual(contract["relations"][0]["type"], "intrinsic_geometry_duplicate")
        ids = [
            item["id"]
            for key in ("features", "evidence", "circuits", "relations")
            for item in contract[key]
        ]
        self.assertEqual(len(ids), len(set(ids)))

    def test_archive_descriptor_treats_rotated_or_mirrored_mass_as_same_language(self):
        sequence = VerbSequence(
            "orientation_invariant_court",
            "orientation invariant court",
            (
                VerbCall("base", {}),
                VerbCall("bar", {"axis": "x", "factor": 0.58}),
                VerbCall("courtyard", {"inner_scale": 0.42}),
                VerbCall("lift", {"ratio": 0.18}),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)
        self.assertIsNotNone(source)

        def elite(compiled, name):
            named = replace(compiled, name=name)
            feature = _feature(
                named,
                sequence,
                building_type="neighborhood living",
                height=18.0,
                floors=5,
                site_area=2400.0,
            )
            attach_program_massing_evidence(feature, building_type="neighborhood living")
            return ProgramElite(sequence, named, feature, 0.9, 0)

        center = source.footprint.centroid
        rotated = replace(
            source,
            footprint=rotate(source.footprint, 90, origin=center),
            upper_footprint=(
                rotate(source.upper_footprint, 90, origin=center)
                if source.upper_footprint is not None
                else None
            ),
            volumes=tuple(
                replace(volume, footprint=rotate(volume.footprint, 90, origin=center))
                for volume in source.volumes
            ),
        )
        mirrored = replace(
            source,
            footprint=scale(source.footprint, xfact=-1, yfact=1, origin=center),
            upper_footprint=(
                scale(source.upper_footprint, xfact=-1, yfact=1, origin=center)
                if source.upper_footprint is not None
                else None
            ),
            volumes=tuple(
                replace(volume, footprint=scale(volume.footprint, xfact=-1, yfact=1, origin=center))
                for volume in source.volumes
            ),
        )

        original_elite = elite(source, "original")
        self.assertLess(_descriptor_distance(original_elite, elite(rotated, "rotated")), 0.08)
        self.assertLess(_descriptor_distance(original_elite, elite(mirrored, "mirrored")), 0.08)
        self.assertLess(intrinsic_silhouette_distance(source, rotated), 0.02)
        self.assertLess(intrinsic_silhouette_distance(source, mirrored), 0.02)

    def test_default_continuous_ribbon_is_an_occupiable_capacity_mass(self):
        sequence = VerbSequence(
            "llm_capacity_ribbon",
            "occupiable layered ribbon",
            (
                VerbCall("base", {}),
                VerbCall("bend", {"lane_count": 3, "vertical_overlap": 0.22, "curvature": 0.10}),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)

        self.assertIsNotNone(source)
        utilization = _source_far_utilization(
            source,
            site_area=2400.0,
            floors=5,
            far_limit_ratio=3.0,
        )
        self.assertGreaterEqual(utilization, 0.70)
        field = source.signature()["architectural_ambition_evidence"]["site_design_field"]
        self.assertGreaterEqual(field["vertical_band_height"], 0.80)
        self.assertTrue(field["variable_width"])
        self.assertEqual(field["width_profile_source"], "formal_rule_prior")

    def test_agent_authored_branched_ribbon_compiles_as_one_field_with_two_arms(self):
        sequence = VerbSequence(
            "llm_branched_ribbon",
            "one grounded field divides into two upper public arms",
            (
                VerbCall("base", {}),
                VerbCall("bend", {
                    "lane_count": 3,
                    "field_topology": "branched",
                    "branch_point_ratio": 0.38,
                    "lane_width_ratio": 0.10,
                    "width_start_ratio": 0.92,
                    "width_mid_ratio": 1.28,
                    "width_end_ratio": 0.68,
                    "width_wave": 0.12,
                    "height_start_ratio": 0.48,
                    "height_mid_ratio": 0.96,
                    "height_end_ratio": 0.62,
                    "height_wave": 0.14,
                    "vertical_overlap": 0.24,
                    "curvature": 0.12,
                }),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)

        self.assertIsNotNone(source)
        roles = {volume.role for volume in source.volumes}
        self.assertIn("primary_branched_ribbon_trunk", roles)
        self.assertIn("primary_branched_ribbon_arm_0", roles)
        self.assertIn("primary_branched_ribbon_arm_1", roles)
        field = source.signature()["architectural_ambition_evidence"]["site_design_field"]
        self.assertEqual(field["field_topology"], "branched")
        self.assertEqual(field["width_profile_source"], "agent_authored")
        self.assertEqual(field["height_profile_source"], "agent_authored")
        self.assertEqual(field["branch_point_ratio"], 0.38)
        self.assertTrue(source.signature()["coherence_evidence"]["hard_pass"])
        surface = source.signature()["continuous_surface_evidence"]
        self.assertEqual(surface["status"], "materialized")
        self.assertEqual(surface["profiled_volume_count"], 3)
        self.assertEqual(surface["representation"], "agent_field_quad_strips")

    def test_generative_a2a_loop_recompiles_typed_graph_edit(self):
        initial = VerbSequence(
            "agent_authored_initial",
            "agent authored initial",
            (VerbCall("base", {"proportion": "site"}), VerbCall("bar", {"axis": "x", "factor": 0.50})),
        )
        compiled_factors = []

        def compile_candidate(sequence):
            compiled_factors.append(float(sequence.calls[1].params["factor"]))
            return {"type": "Feature", "geometry": None, "properties": {"variant_id": sequence.name, "factor": compiled_factors[-1]}}

        def critic(feature):
            if feature["properties"]["factor"] >= 0.70:
                return CriticDirective(provider="test-vlm")
            return CriticDirective(
                actions=("weak_primary_mass",),
                graph_edits=(GraphEditDirective(
                    operation="set_parameter",
                    target_node_id="primary_1_bar",
                    parameter_name="factor",
                    numeric_value=0.72,
                    rationale="strengthen the primary street mass",
                ),),
                provider="test-vlm",
            )

        result = run_generative_a2a_loop(
            context={"building_type": "근린생활시설"},
            target_count=1,
            author_population=lambda context: (initial,),
            compile_candidate=compile_candidate,
            hard_gate=lambda feature: True,
            critic_agent=critic,
            revise_graph=apply_critic_graph_edits,
            quality_key=lambda feature: (feature["properties"]["factor"],),
            select_archive=lambda features, count: sorted(features, key=lambda feature: feature["properties"]["factor"], reverse=True)[:count],
            max_generations=3,
        )
        self.assertEqual(result.trace["status"], "completed")
        self.assertEqual(compiled_factors, [0.5, 0.72])
        self.assertEqual(result.archive[0]["properties"]["factor"], 0.72)

    def test_gym_long_span_hall_materializes_a_real_ridge(self):
        sequence = next(item for item in program_seed_sequences("체육관") if "long_span_hall" in item.name)
        source = compile_sequence_to_source_mass(box(0, 0, 60, 40), sequence)
        self.assertIsNotNone(source)
        roofs = [
            surface for surface in source.surfaces
            if surface.surface_type == "profiled_formal_roof" and "main_long_span_hall" in surface.role
        ]
        self.assertEqual(len(roofs), 1)
        self.assertGreaterEqual(len(roofs[0].vertices_m), 6)
        self.assertGreaterEqual(len({round(vertex[2], 4) for vertex in roofs[0].vertices_m}), 2)
        self.assertTrue(source.signature()["continuous_surface_evidence"]["hard_pass"])

    def test_building_use_aliases_resolve_to_distinct_profiles(self):
        self.assertEqual(resolve_program_profile("공동주택")["id"], "housing")
        self.assertEqual(resolve_program_profile("근린생활시설 카페")["id"], "cafe")
        self.assertEqual(resolve_program_profile("학교 체육관")["id"], "gymnasium")

    def test_program_seed_graphs_are_distinct_and_compilable(self):
        fingerprints = {}
        for building_type in ("공동주택", "카페", "체육관"):
            sequences = program_seed_sequences(building_type)
            self.assertGreaterEqual(len(sequences), 2)
            self.assertTrue(all(not sequence.validate() for sequence in sequences))
            fingerprints[building_type] = {tuple(call.verb for call in sequence.calls) for sequence in sequences}
            variants = generate_grammar_variants(box(0, 0, 60, 40), building_type=building_type)
            names = {variant.operator for variant in variants}
            self.assertTrue({sequence.name for sequence in sequences}.issubset(names))
        self.assertEqual(len({tuple(sorted(value)) for value in fingerprints.values()}), 3)

    def test_housing_legal_pool_receives_twenty_program_sequences(self):
        sequences = program_archive_sequences(box(0, 0, 60, 40), "housing", target_count=20)
        self.assertEqual(len(sequences), 20)
        self.assertGreaterEqual(len({item.name.split("__search_", 1)[0] for item in sequences}), 12)
        self.assertTrue(all(not item.validate() for item in sequences))

    def test_llm_site_context_contains_program_design_intent(self):
        context = build_site_context(
            site_area_m2=2400,
            building_type="체육관",
            limits={"far": 200, "bcr": 60, "height": 30, "max_seed_floors": 6},
            max_variants=20,
        )
        self.assertEqual(context["program_massing"]["profile_id"], "gymnasium")
        self.assertIn("long-span", context["program_massing"]["design_intent"])
        self.assertEqual(context["program_massing"]["search_prior"]["max_component_nodes"], 3)
        self.assertIn("hall_span_ratio", context["program_massing"]["search_prior"]["archive_descriptors"])

    def test_llm_site_context_exposes_geometry_to_language_agent(self):
        site = rotate(box(0, 0, 80, 30), 27, origin="centroid")
        context = build_site_context(
            site_area_m2=site.area,
            building_type="cafe",
            limits={"far": 200, "bcr": 60, "height": 24, "max_seed_floors": 5},
            max_variants=20,
            site_polygon=site,
            access_context={"frontage": "southwest"},
        )
        intelligence = context["site_geometry_intelligence"]
        self.assertEqual(intelligence["status"], "available")
        self.assertAlmostEqual(abs(intelligence["dominant_axis_world_degrees"]), 27.0, delta=0.1)
        self.assertAlmostEqual(intelligence["oriented_aspect_ratio"], 80 / 30, delta=0.01)
        self.assertEqual(intelligence["access_context"]["frontage"], "southwest")

        concave = Polygon([(0, 0), (60, 0), (60, 20), (25, 20), (25, 50), (0, 50)])
        concave_context = build_site_context(
            site_area_m2=concave.area,
            building_type="cafe",
            limits={},
            max_variants=20,
            site_polygon=concave,
        )
        self.assertTrue(concave_context["site_geometry_intelligence"]["is_concave"])
        self.assertTrue(any("concavity" in item for item in concave_context["site_geometry_intelligence"]["design_directives"]))

    def test_llm_architect_agent_owns_live_population_operation(self):
        context = {
            "site_geometry_intelligence": {"status": "available"},
        }
        with patch(
            "design.maas.llm_proposals.generate_llm_massdsl_batch",
            return_value=LlmProposalBatch(artifact={"status": "generated"}, sequences=()),
        ):
            batch = LLMArchitectAgent().propose_population(
                site_context=context,
                target_count=1,
                response_override={},
            )
        self.assertEqual(batch.artifact["owning_agent"], "llm_architect_agent")
        self.assertEqual(batch.artifact["agent_operation"], "architectural_language_population_proposal")
        self.assertEqual(batch.artifact["site_geometry_status"], "available")

    def test_robotics_transfer_prior_is_program_specific_and_keeps_hard_gate_order(self):
        housing = program_search_prior("housing")
        gym = program_search_prior("gymnasium")
        self.assertNotEqual(housing["archive_descriptors"], gym["archive_descriptors"])
        self.assertEqual(gym["hard_constraint_order"][:3], ["grammar_validity", "law", "parking"])
        self.assertIn("robogrammar_2020", gym["source_ids"])

    def test_cross_program_benchmark_passes_quantitative_separation(self):
        with TemporaryDirectory() as temporary:
            result = run_program_massing_benchmark(
                output_json=Path(temporary) / "benchmark.json",
                output_png=Path(temporary) / "benchmark.png",
            )
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertEqual(result["distinct_profile_fingerprint_count"], 2)
        self.assertGreaterEqual(result["mean_program_fit"], 0.75)
        self.assertGreaterEqual(result["case_count"], 5)
        self.assertGreaterEqual(sum(item["evaluated_count"] for item in result["search_reports"].values()), 200)
        self.assertGreater(sum(item["rejected_count"] for item in result["search_reports"].values()), 0)
        self.assertGreaterEqual(min(item["architectural_score"] for item in result["rows"]), 0.88)
        self.assertLessEqual(max(item["surface_count"] for item in result["rows"]), 28)
        self.assertLessEqual(max(item["volume_count"] for item in result["rows"]), 4)

    def test_creative_archive_precedes_program_and_legal_projection(self):
        with TemporaryDirectory() as temporary:
            result = run_creative_20_archive_benchmark(
                output_json=Path(temporary) / "creative-20.json",
                output_png=Path(temporary) / "creative-20.png",
            )
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertFalse(result["program_conditioned"])
        self.assertFalse(result["legal_parking_checked"])
        self.assertEqual(result["selected_count"], 20)
        self.assertGreaterEqual(result["topology_count"], 12)
        self.assertGreaterEqual(result["geometric_language_count"], 14)
        self.assertGreaterEqual(result["sculptural_geometry_count"], 8)
        self.assertGreaterEqual(result["minimum_creative_score"], 0.75)
        self.assertTrue(all(item["hard_pass"] for item in result["rows"]))

    def test_neighborhood_archive_has_twenty_grounded_clean_languages(self):
        with TemporaryDirectory() as temporary:
            result = run_neighborhood_20_language_benchmark(
                output_json=Path(temporary) / "neighborhood-20.json",
                output_png=Path(temporary) / "neighborhood-20.png",
            )
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertEqual(result["selected_count"], 20)
        self.assertGreaterEqual(result["topology_count"], 10)
        self.assertGreaterEqual(result["formal_principle_count"], 6)
        self.assertLessEqual(result["near_duplicate_pair_count"], 2)
        self.assertTrue(all(row["grounded"] and row["hard_pass"] for row in result["rows"]))
        self.assertLessEqual(max(row["surface_count"] for row in result["rows"]), 28)

    def test_creative_seeds_have_neutral_names(self):
        seeds = creative_seed_sequences()
        self.assertGreaterEqual(len(seeds), 20)
        self.assertTrue(all(item.name.startswith("creative_") for item in seeds))
        self.assertTrue(all("housing" not in item.name for item in seeds))

    def test_site_adaptation_benchmark_uses_real_parcel_frames(self):
        with TemporaryDirectory() as temporary:
            result = run_site_adaptation_benchmark(
                output_json=Path(temporary) / "site-adaptation.json",
                output_png=Path(temporary) / "site-adaptation.png",
            )
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertEqual(result["site_count"], 3)
        self.assertEqual(result["language_count"], 4)
        self.assertTrue(all(row["within_site"] for row in result["rows"]))

    def test_experimental_creative_archive_is_quarantined_from_live_pool(self):
        sequences = creative_archive_sequences(box(0, 0, 60, 40), target_count=20)
        self.assertEqual(len(sequences), 20)
        self.assertGreaterEqual(len({item.name.split("__search_", 1)[0] for item in sequences}), 12)
        variants = generate_grammar_variants(box(0, 0, 60, 40), building_type="카페")
        operators = [item.operator for item in variants]
        self.assertFalse(any(item.startswith("creative_") for item in operators))
        self.assertTrue(any(item.startswith("program_cafe_") for item in operators))
        with patch.dict("os.environ", {"MAAS_ENABLE_EXPERIMENTAL_CREATIVE_ARCHIVE": "1"}):
            experimental = generate_grammar_variants(box(0, 0, 60, 40), building_type="移댄럹")
        self.assertTrue(experimental[0].operator.startswith("creative_"))

    def test_reference_language_brain_changes_topology_and_avoids_repetition(self):
        intent = {
            "reference_principles": ["flowing ribbon with a curved court and continuous roof"],
            "operation_rationales": ["embracing landscape roof"],
        }
        first = propose_language_mutation(reference_intent=intent, current_language="creative_court_bar")
        self.assertIsNotNone(first)
        self.assertEqual(first.sequence.name, "creative_ribbon_campus")
        second = propose_language_mutation(
            reference_intent=intent,
            current_language="creative_court_bar",
            used_languages=("creative_ribbon_campus",),
        )
        self.assertIsNotNone(second)
        self.assertEqual(second.sequence.name, "creative_arc_court")
        self.assertNotEqual(first.diversity_group, "cluster")

    def test_reference_language_brain_keeps_lego_as_one_bounded_family(self):
        intent = {"reference_principles": ["interlocking lego modular blocks arranged as a village cluster"]}
        first = propose_language_mutation(reference_intent=intent)
        self.assertEqual(first.sequence.name, "creative_voxel_cascade")
        second = propose_language_mutation(reference_intent=intent, used_languages=(first.sequence.name,))
        self.assertEqual(second.sequence.name, "creative_cluster_village")
