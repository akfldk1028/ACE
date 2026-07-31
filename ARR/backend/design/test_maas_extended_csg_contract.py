"""Focused contracts for the BOOK authority bundle and extended-CSG system."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
import numpy as np
from PIL import Image

from design.maas.book_language.catalog import EXPECTED_LAYER_COUNTS, load_book_language_catalog
from design.maas.book_language.source_bundle import SOURCE_SPECS, load_book_source_bundle
from design.maas.geometry_language import (
    GeometryProgramBuilder,
    apply_book_projection_to_geometry_program,
    architectural_shape_programs,
    base_seed_programs,
    build_mass_execution_passport,
    build_mass_execution_agent_context,
    compile_geometry_program,
    enrich_mass_execution_passport,
    passport_path_for_preview,
    project_program_requirements,
    render_compilation_preview,
    write_mass_execution_passport,
)
from design.maas.program_massing import (
    book_sentence_variants,
    compose_program_with_book_operations,
    program_seed_sequences,
)
from design.maas.geometry_language.system_contract import build_extended_csg_contract
from design.maas.geometry_language.compiler import CompilationResult
from design.maas.geometry_language.executed_archive import materialize_executed_mass_preview
from design.maas.geometry_language import render as geometry_render


class MaasExtendedCsgContractTest(SimpleTestCase):
    def test_isometric_camera_projects_higher_mass_points_upward_on_screen(self):
        vertices = np.asarray(((2.0, 3.0, 0.0), (2.0, 3.0, 10.0)))
        projected, _depth, _rotated = geometry_render._project(
            vertices,
            yaw=35.0,
            pitch=geometry_render._ISOMETRIC_PITCH_DEGREES,
        )

        # Screen Y negates projected Y. Therefore a higher architectural point
        # must have greater projected Y to appear visually higher, not inverted.
        self.assertGreater(projected[1, 1], projected[0, 1])

    def test_archived_preview_recovers_the_card_crop_from_legacy_card_index_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "legacy-run"
            run.mkdir()
            archive_path = run / "maas-book-exact-geometry-artifacts.json"
            archive_path.write_text("{}", encoding="utf-8")
            board = Image.new("RGB", (768, 400), "blue")
            for x in range(384, 768):
                for y in range(72, 332):
                    board.putpixel((x, y), (220, 90, 30))
            board.save(run / "maas-book-neighborhood-20.png")
            record = {
                "geometry_artifact": {
                    "identity": {"geometryHash": "abc123"},
                },
            }
            row = {
                "archive_render_evidence": {
                    "card_index": 2,
                    "hard_pass": True,
                },
            }

            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ), patch(
                "design.maas.geometry_language.executed_archive.executed_mass_record",
                return_value=(record, row, archive_path),
            ):
                preview = materialize_executed_mass_preview(1, "legacy-run")

            with Image.open(preview) as cropped:
                self.assertEqual(cropped.size, (384, 260))
                self.assertEqual(cropped.getpixel((200, 100)), (220, 90, 30))

    def test_compilation_preview_uses_per_pixel_depth_for_crossing_mass_faces(self):
        builder = GeometryProgramBuilder("crossing_depth_faces")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 1, "depth": 1, "height": 1},
        )
        compilation = CompilationResult(
            program=builder.build(root),
            status="compiled",
            vertices=(
                (0, 0, 10),
                (10, 0, 0),
                (0, 10, 0),
                (0, 0, 0),
                (10, 0, 12),
                (0, 10, 5),
            ),
            triangles=((0, 1, 2), (3, 4, 5)),
            metrics={"triangle_count": 2},
            geometry_hash="a" * 64,
        )

        with TemporaryDirectory() as directory:
            preview = render_compilation_preview(
                compilation,
                Path(directory) / "crossing.png",
            )
            with Image.open(preview) as image:
                colors = image.convert("RGB").crop((20, 350, 430, 640)).getcolors(
                    maxcolors=100_000,
                )

        mass_colors = {
            color
            for _count, color in colors or ()
            if color[0] > 60
            and color[0] > color[1] * 1.2
            and color[1] > color[2] * 1.2
        }
        self.assertGreaterEqual(len(mass_colors), 2)

    def test_all_four_supplied_book_documents_are_required_authorities(self):
        bundle = load_book_source_bundle()
        self.assertEqual(bundle["document_count"], 4)
        self.assertEqual(
            {item["filename"] for item in bundle["documents"]},
            {filename for _, filename, _ in SOURCE_SPECS},
        )
        self.assertTrue(all(item["line_count"] > 0 for item in bundle["documents"]))

        catalog = load_book_language_catalog()
        self.assertEqual(catalog["entry_count"], 134)
        self.assertEqual(catalog["layer_counts"], EXPECTED_LAYER_COUNTS)
        self.assertEqual(catalog["source_bundle_document_count"], 4)

    def test_extended_csg_contract_contains_eighteen_real_gated_programs(self):
        contract = build_extended_csg_contract()
        self.assertEqual(contract["shape_count"], 18)
        self.assertTrue(all(row["compile_status"] == "compiled" for row in contract["shapes"]))
        self.assertTrue(all(row["gate_pass"] for row in contract["shapes"]))
        self.assertEqual(len({row["geometry_hash"] for row in contract["shapes"]}), 18)
        self.assertTrue(all(row["minimum_program"].startswith("mass ") for row in contract["shapes"]))
        self.assertEqual(contract["graph"]["stage_order"][0], "base_model")

    def test_structural_hash_ignores_node_names_but_edit_hash_preserves_them(self):
        first = GeometryProgramBuilder("first")
        base_a = first.add("primitive", "box", parameters={"width": 8, "depth": 3, "height": 3})
        moved_a = first.add("transform", "translate", inputs=(base_a,), parameters={"vector": [2, 0, 0]})
        program_a = first.build(moved_a)

        second = GeometryProgramBuilder("second")
        base_b = second.add("primitive", "box", node_id="source", parameters={"width": 8, "depth": 3, "height": 3})
        moved_b = second.add("transform", "translate", node_id="result", inputs=(base_b,), parameters={"vector": [2, 0, 0]})
        program_b = second.build(moved_b)

        self.assertNotEqual(program_a.program_hash(), program_b.program_hash())
        self.assertEqual(program_a.canonical_structure_hash(), program_b.canonical_structure_hash())
        self.assertEqual(
            compile_geometry_program(program_a).geometry_hash,
            compile_geometry_program(program_b).geometry_hash,
        )

    def test_geometry_phenotype_preview_is_a_compiled_hash_addressed_png(self):
        response = self.client.get("/design/maas/geometry-shapes/10/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(len(response["X-Geometry-Hash"]), 64)
        self.assertIn("immutable", response["Cache-Control"])

    def test_every_rendered_mass_receives_a_truthful_execution_passport(self):
        compilation = compile_geometry_program(architectural_shape_programs()[0])
        pre_render = build_mass_execution_passport(compilation)
        self.assertFalse(pre_render["truth_policy"]["internal_neuron_claim"])
        self.assertEqual(
            next(stage for stage in pre_render["stages"] if stage["id"] == "parking")["status"],
            "not_evaluated",
        )
        self.assertFalse(any(node["kind"] == "vlm_concept_score" for node in pre_render["activation_graph"]["nodes"]))

        with TemporaryDirectory() as directory:
            preview = render_compilation_preview(compilation, Path(directory) / "mass.png")
            sidecar = passport_path_for_preview(preview)
            self.assertTrue(sidecar.is_file())
            materialized = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(
                next(stage for stage in materialized["stages"] if stage["id"] == "render")["status"],
                "passed",
            )
            self.assertEqual(materialized["geometry_hash"], compilation.geometry_hash)
            self.assertEqual(
                materialized["agent_context"]["schema_version"],
                "arr.maas.mass_execution_agent_context.v1",
            )
            self.assertTrue(materialized["agent_context"]["active_nodes"])

    def test_geometry_phenotype_passport_endpoint_exposes_actual_trace(self):
        response = self.client.get("/design/maas/geometry-shapes/10/passport/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schema_version"], "arr.maas.mass_execution_passport.v1")
        self.assertTrue(payload["truth_policy"]["causal_program_trace"])
        self.assertGreater(len(payload["activation_graph"]["nodes"]), 10)
        self.assertEqual(payload["activation_graph"]["result_node_ids"], ["result:mass"])
        self.assertTrue(payload["activation_graph"]["root_node_ids"])
        self.assertEqual(
            payload["activation_graph"]["query_contract"]["default_query"],
            "active_ancestors_of_result:mass",
        )
        self.assertEqual(
            payload["activation_graph"]["query_contract"]["visualization_policy"],
            "render one selected MASS induced subgraph; never create parallel authority graphs",
        )
        self.assertEqual(
            next(stage for stage in payload["stages"] if stage["id"] == "render")["status"],
            "passed",
        )

    def test_downstream_law_parking_and_vlm_evidence_activate_only_real_nodes(self):
        compilation = compile_geometry_program(architectural_shape_programs()[4])
        initial = build_mass_execution_passport(compilation)
        enriched = enrich_mass_execution_passport(
            initial,
            downstream_evidence={
                "law": {"evaluated": True, "hard_pass": True, "far_pct": 199.5},
                "parking": {"evaluated": True, "hard_pass": False, "required_spaces": 12, "provided_spaces": 9},
            },
            vlm_result={
                "cache_hit": True,
                "model": "recorded-test-model",
                "concept_scores": {"courtyard_legibility": 0.84},
                "geometry_edits": [],
                "vlm_image_inputs": {
                    "schema_version": "arr.maas.vlm_image_inputs.v1",
                    "references": [{
                        "input_id": "reference:archdaily-test",
                        "role": "reference_image",
                        "source_id": "archdaily-test",
                        "title": "Test architecture reference",
                        "image_url": "https://example.com/reference.jpg",
                        "selection_role": "typology",
                        "matched_tags": ["courtyard"],
                        "used_by_vlm": True,
                    }],
                    "reference_count": 1,
                },
            },
        )
        statuses = {stage["id"]: stage["status"] for stage in enriched["stages"]}
        self.assertEqual(statuses["law"], "passed")
        self.assertEqual(statuses["parking"], "failed")
        self.assertEqual(statuses["vlm"], "cache_hit")
        concept = next(node for node in enriched["activation_graph"]["nodes"] if node["id"] == "vlm:concept:courtyard_legibility")
        self.assertEqual(concept["activation"], 0.84)
        reference = next(
            node for node in enriched["activation_graph"]["nodes"]
            if node["kind"] == "vlm_reference_image"
        )
        self.assertEqual(reference["source_id"], "archdaily-test")
        self.assertTrue(any(
            edge["source"] == reference["id"]
            and edge["target"] == "flow:vlm"
            and edge["relation"] == "visual_reference_input"
            for edge in enriched["activation_graph"]["edges"]
        ))
        context = build_mass_execution_agent_context(enriched)
        self.assertEqual(context["vlm_reference_images"][0]["source_id"], "archdaily-test")
        self.assertEqual(context["vlm_reference_images"][0]["matched_tags"], ["courtyard"])
        self.assertFalse(enriched["full_flow_complete"])

    def test_agent_context_reads_the_same_causal_graph_without_claiming_neurons(self):
        compilation = compile_geometry_program(architectural_shape_programs()[11])
        passport = build_mass_execution_passport(compilation)
        context = build_mass_execution_agent_context(passport)
        self.assertEqual(context["schema_version"], "arr.maas.mass_execution_agent_context.v1")
        self.assertIn("parking", context["pending_required_stages"])
        self.assertTrue(context["editable_ast_nodes"])
        self.assertTrue(all(item["node_id"] in compilation.program.node_map for item in context["editable_ast_nodes"]))
        self.assertIn("hidden-neuron", " ".join(context["agent_rules"]))
        research = context["research_method_context"]
        self.assertEqual(research["schema_version"], "arr.maas.executable_paper_method_context.v1")
        source_status = {
            row["source_id"]: row["runtime_status"]
            for row in research["sources"]
        }
        self.assertEqual(source_status["szalinski_siggraph_2020"], "adaptation_active")
        self.assertEqual(
            source_status["cadfusion_2025"],
            "registered_not_active_for_this_mass",
        )

    def test_rerender_does_not_erase_recorded_vlm_evidence(self):
        compilation = compile_geometry_program(architectural_shape_programs()[4])
        with TemporaryDirectory() as directory:
            preview = render_compilation_preview(compilation, Path(directory) / "courtyard.png")
            write_mass_execution_passport(
                compilation,
                preview,
                vlm_result={
                    "cache_hit": True,
                    "model": "recorded-test-model",
                    "response_id": "response-test",
                    "concept_scores": {"void_publicness": 0.88},
                    "geometry_edits": [],
                },
            )
            render_compilation_preview(compilation, preview)
            materialized = json.loads(passport_path_for_preview(preview).read_text(encoding="utf-8"))
            vlm = next(stage for stage in materialized["stages"] if stage["id"] == "vlm")
            self.assertEqual(vlm["status"], "cache_hit")
            self.assertEqual(vlm["evidence"]["concept_scores"]["void_publicness"], 0.88)

    def test_program_connectivity_guard_joins_real_surfaces_after_book_array(self):
        sequence = compose_program_with_book_operations(
            program_seed_sequences("neighborhood living")[0],
            book_sentence_variants(("taper", "array"), count=1)[0],
            base_volume_label="3/8",
            orientation="long_axis",
        )
        book_program = apply_book_projection_to_geometry_program(
            base_seed_programs()[1],
            sequence,
        )
        projected = project_program_requirements(
            book_program,
            building_type="neighborhood living",
            access_side="south",
        )
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled")
        self.assertEqual(compilation.metrics["component_count"], 1)
        self.assertIn("related_array", {node.operator for node in projected.nodes})
        self.assertIn("join_related", {node.operator for node in projected.nodes})
