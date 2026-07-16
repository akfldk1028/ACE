"""Regression contracts for the recursive solid geometry language."""

import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box

from design.maas.geometry_language import (
    GeometryEdit,
    GeometryOutcomeGraph,
    GeometryProgramBuilder,
    apply_book_projection_to_geometry_program,
    apply_geometry_edits,
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
    parse_geometry_dsl,
    program_cost,
    reference_language_programs,
    replace_source_dominant_with_geometry_program,
    retrieve_geometry_reference_matches,
    run_geometry_program_a2a_loop,
    score_geometry_program_with_openai_vlm,
    synthesize_architectural_programs,
    synthesis_requests_from_program_profile,
)
from design.maas.book_language.registry import build_book_language_registry
from design.maas.program_massing import (
    book_operation_variants,
    book_sentence_variants,
    compose_program_with_book_operations,
    program_seed_sequences,
)
from design.maas.preference.vlm_scorer import _prompt_text
from design.maas.source_geometry.compiler import compile_sequence_to_source_mass


class MaasGeometryLanguageTest(SimpleTestCase):
    def test_all_59_book_principles_mutate_the_recursive_manifold_ast(self):
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
        self.assertEqual(len(rows), 59)
        self.assertTrue(all(result.status == "compiled" for _program, result in rows))
        self.assertTrue(all(int(result.metrics["component_count"]) <= 5 for _program, result in rows))
        self.assertEqual(len({program.program_hash() for program, _result in rows}), 59)
        self.assertGreaterEqual(len({result.geometry_hash for _program, result in rows}), 58)
        self.assertTrue(all(
            program.metadata["book_recursive_projection"]["geometry_authority"] == "recursive_manifold_ast"
            for program, _result in rows
        ))

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
        self.assertNotIn("section_controls", str(requests))

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
                {"source": "archdaily_api", "source_id": "hall-3", "title": "Twisted bridge field", "local_path": str(root / "hall-3.jpg"), "tags": ["twist", "bridge", "field"]},
                {"source": "archdaily_api", "source_id": "hall-4", "title": "Folded daylight roof", "local_path": str(root / "hall-4.jpg"), "tags": ["folded", "section", "roof"]},
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

    def test_portfolio_agent_path_closes_reference_vlm_edit_and_memory_loop(self):
        from design.maas.book_language.portfolio_benchmark import _agent_mutated_seeds

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
            "design.maas.book_language.portfolio_benchmark.retrieve_geometry_reference_matches",
            return_value=[{
                "source": "archdaily_api", "source_id": "fixture-reference",
                "title": "Fixture hall", "image_url": "https://example.test/hall.jpg",
                "selection_role": "counterfactual", "matched_tags": ["folded"],
            }],
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

    def test_vlm_synthesis_request_is_additive_to_program_profile_control_lane(self):
        from design.maas.book_language.portfolio_benchmark import _agent_mutated_seeds

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
            {"program_profile_control", "vlm_or_session_directive"},
        )
        self.assertTrue(any("split_wing" in family for family in families))
        self.assertTrue(any("shear" in family or "slice" in family for family in families))

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

    def test_original_eighteen_are_not_misreported_as_one_identical_box_seed(self):
        primitive_signatures = {
            tuple((node.operator, repr(sorted(node.parameters.items()))) for node in program.nodes if node.kind == "primitive")
            for program in architectural_shape_programs()
        }
        self.assertGreater(len(primitive_signatures), 1)

    def test_vlm_receives_node_bound_graph_notes_and_scope_seed_distinction(self):
        program = base_seed_programs()[1]
        compilation = compile_geometry_program(program)
        notes = build_geometry_graph_notes(program, compilation)
        snapshot = build_geometry_graph_snapshot(program, compilation)
        self.assertEqual([note["node_id"] for note in notes], [node.id for node in program.topological_nodes()])
        self.assertTrue(all(note["note_is_non_executable"] for note in notes))
        self.assertEqual(snapshot["root_node_id"], program.root_id)
        self.assertEqual(len(snapshot["edges"]), len(program.topological_nodes()) - 1)
        self.assertEqual(snapshot["agent_edit_contract"]["target_selector"], "node_id")
        self.assertTrue(snapshot["agent_edit_contract"]["requires_recompile_and_rerender"])
        feature = {"properties": {
            "geometry_program": program.to_dict(),
            "geometry_graph_notes": notes,
            "geometry_graph_snapshot": snapshot,
            "base_seed_catalog": [program.metadata["base_seed"]],
        }}
        prompt = _prompt_text(feature, [])
        self.assertIn("geometry_graph_notes", prompt)
        self.assertIn("geometry_graph_snapshot", prompt)
        self.assertIn("site scope fraction from normalized base seed", prompt)
        self.assertIn("seed_slab", prompt)

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
            "leaning_tower", "slice", "cut_corner", "loft", "sweep", "split_wing", "twist",
        }.issubset(operators))
        expansions = {operation for result in compilations for row in result.trace for operation in row["macro_expansion"]}
        self.assertTrue({"difference", "shear"}.issubset(expansions))

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

    def test_llm_author_payload_becomes_valid_compilable_programs(self):
        programs = geometry_programs_from_author_payload({"programs": [
            {"name": "courtyard_author", "dsl": "mass base = box(12, 9, 5)\nmass result = courtyard(base, margin_ratio=0.28)", "rationale": "carved court"},
            {"name": "fan_author", "dsl": "mass bar = box(11, 2, 3)\nmass moved = move(bar, 0, -1, 0)\nmass result = radial_array(moved, count=5, total_angle_degrees=72)", "rationale": "radial field"},
        ]}, expected_count=2)
        self.assertEqual(len(programs), 2)
        self.assertEqual(len({program.program_hash() for program in programs}), 2)
        self.assertTrue(all(compile_geometry_program(program).status == "compiled" for program in programs))

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
