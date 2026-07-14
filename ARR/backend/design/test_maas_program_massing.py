"""Program-conditioned MAAS massing contracts."""

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.affinity import rotate, scale
from shapely.geometry import Polygon, box

from design.maas.grammar import generate_grammar_variants
from design.maas.llm_proposals import build_site_context
from design.maas.llm_proposals import LlmProposalBatch
from design.maas.agents.llm_architect_agent import LLMArchitectAgent
from design.maas.interactive.language_brain import propose_language_mutation
from design.maas.program_massing import creative_archive_sequences, creative_seed_sequences, program_archive_sequences, program_search_prior, program_seed_sequences, resolve_program_profile
from design.maas.program_massing.benchmark import run_creative_20_archive_benchmark, run_neighborhood_20_language_benchmark, run_program_massing_benchmark, run_site_adaptation_benchmark
from design.maas.program_massing.grl_contract import build_archive_grl_contract
from design.maas.program_massing.graph_archive import bounded_behavior_frontier, field_topology_coverage
from design.maas.program_massing.vlm_a2a import _source_far_utilization
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import ProgramElite, _descriptor_distance, _feature
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.parametric_curves import swept_variable_ribbon
from design.maas.agents.orchestrator.generative_loop import CriticDirective, GraphEditDirective, run_generative_a2a_loop
from design.maas.agents.llm_architect_agent.graph_revision import apply_critic_graph_edits
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence


class MaasProgramMassingTest(SimpleTestCase):
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
