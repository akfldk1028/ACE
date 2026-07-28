"""Tests for ARR-local MAAS OpenSCAD export."""

import json
import os
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from shapely.geometry import Polygon, box
from unittest.mock import patch

from design.maas import export_mass_geojson_to_scad, generate_legal_mass_variants, mass_geojson_to_scad
from design.maas.aesthetic import build_aesthetic_image_job, build_aesthetic_pipeline_result, validate_aesthetic_job
from design.maas.aesthetic.contracts import ProviderResult
from design.maas.aesthetic.projection_assets import attach_facade_panel_assets
from design.maas.aesthetic.projection_bake import attach_baked_projection_assets
from design.maas.aesthetic.projection_export import attach_textured_mesh_assets
from design.maas.aesthetic.renderers import MultiViewReferencePackRenderer, ReferencePngRenderer
from design.maas.grammar import generate_grammar_variants, load_term_ontology, resolve_intent_to_sequence
from design.maas.legal_mesh_optimizer import (
    _compact_visual_volumes,
    _feature_distance,
    _final_design_balanced_selection,
    _operator_family,
    _apply_piloti_parking_void,
    _promote_legal_floor_stack_source_geometry,
    _preserve_visible_section_connector,
    _upper_typology_is_viable,
)
from design.maas.final_floorwise_legal import revalidate_final_floorwise_feature
from design.maas.legal_envelope import allowed_footprint_at_height, build_legal_envelope
from design.maas.llm_proposals import (
    LLM_BATCH_SCHEMA_VERSION,
    LLM_PARAMETER_SOURCE,
    generate_llm_massdsl_batch,
)
from design.maas.morphology_operators import generate_morphology_variants
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.grammar.verb_sequence import VerbSequence, call
from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.interactive.revision import apply_graph_operations, infer_graph_operations
from design.maas.interactive.reference_intent import interpret_reference_intent_with_openai_vlm
from design.maas.interactive.revision_evaluation import evaluate_reference_revision
from design.maas.interactive.revision_learning import build_revision_learning_profile
from design.maas.parking_layout import (
    _drive_entrance_access,
    _solve_grid_parking_layout,
    evaluate_small_attached_parking_relief,
    generate_parking_layout_candidate,
)
from design.maas.parking_requirements import resolve_candidate_parking_requirement
from design.maas.parking_strategy import infer_parking_strategy
from design.maas.research_backends import inspect_maas_clone_backend, run_maas_clone_reference_baseline
from design.maas.training import build_examples_from_design_results, build_sft_examples, evidence_to_review_example, export_sft_seed
from design.models import DesignResult, OptimizationJob
from design.services.site_geometry import geojson_to_polygon, wgs84_to_utm


class MaasScadExportServiceTest(TestCase):
    def _base_feature(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [127.0000, 37.0000],
                    [127.0005, 37.0000],
                    [127.0005, 37.0004],
                    [127.0000, 37.0004],
                    [127.0000, 37.0000],
                ]],
            },
            "properties": {
                "height": 18.0,
                "num_floors": 6,
                "floor_height": 3.0,
                "far": 180.0,
                "bcr": 45.0,
                "mass_shape": "additive",
            },
        }

    def test_exports_single_mass_to_scad(self):
        result = export_mass_geojson_to_scad(self._base_feature(), name="test mass")

        self.assertEqual(result["mode"], "maas_scad_export")
        self.assertEqual(result["name"], "test_mass")
        self.assertIn("linear_extrude(height=18.0000)", result["scad_text"])
        self.assertIn("polygon(points=", result["scad_text"])
        self.assertFalse(result["metadata"]["has_stepback"])

    def test_exports_stepback_as_two_extrusions(self):
        feature = self._base_feature()
        feature["properties"]["lower_height"] = 9.0
        feature["properties"]["upper_geometry"] = {
            "type": "Polygon",
            "coordinates": [[
                [127.0001, 37.0001],
                [127.0004, 37.0001],
                [127.0004, 37.0003],
                [127.0001, 37.0003],
                [127.0001, 37.0001],
            ]],
        }

        export = mass_geojson_to_scad(feature, name="stepback")

        self.assertEqual(export.metadata["has_stepback"], True)
        self.assertIn("lower mass / podium", export.scad_text)
        self.assertIn("upper mass / stepback", export.scad_text)
        self.assertEqual(export.scad_text.count("linear_extrude(height=9.0000)"), 2)


class MaasScadExportEndpointTest(TestCase):
    def test_endpoint_requires_mass_geojson(self):
        response = self.client.post(
            "/design/maas/export-scad/",
            data={},
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 400)

    def test_endpoint_returns_scad_text(self):
        response = self.client.post(
            "/design/maas/export-scad/",
            data={
                "name": "candidate 01",
                "mass_geojson": {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [127.0000, 37.0000],
                            [127.0004, 37.0000],
                            [127.0004, 37.0004],
                            [127.0000, 37.0004],
                            [127.0000, 37.0000],
                        ]],
                    },
                    "properties": {"height": 15.0, "far": 150.0, "bcr": 40.0},
                },
            },
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "candidate_01")
        self.assertIn("union() {", data["scad_text"])
        self.assertEqual(data["metadata"]["height"], 15.0)


class MaasEvidenceBundleEndpointTest(TestCase):
    def _feature(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [127.0000, 37.0000],
                    [127.0004, 37.0000],
                    [127.0004, 37.0004],
                    [127.0000, 37.0004],
                    [127.0000, 37.0000],
                ]],
            },
            "properties": {
                "algorithm": "maas_legal_envelope",
                "variant_id": "maas_01",
                "mass_shape": "legal_layered_max",
                "maas_concept": "legal capacity anchor",
                "height": 17.5,
                "num_floors": 5,
                "floor_height": 3.5,
                "footprint_area": 102.93,
                "floor_area": 361.28,
                "bcr": 38.97,
                "far": 136.78,
                "min_setback": 0.7,
                "open_pct": 61.03,
                "maas_score": 0.75,
                "floor_plates": [
                    {"floor": 1, "area_m2": 102.93},
                    {"floor": 5, "area_m2": 28.96},
                ],
                "mass_volumes": [],
            },
        }

    def _job(self):
        return OptimizationJob.objects.create(
            pnu="1168011800104170004",
            address="",
            site_polygon={
                "type": "Polygon",
                "coordinates": [[
                    [127.0000, 37.0000],
                    [127.0010, 37.0000],
                    [127.0010, 37.0010],
                    [127.0000, 37.0010],
                    [127.0000, 37.0000],
                ]],
            },
            site_area_m2=264.1,
            job_spec={"options": {"building_type": "공동주택", "algorithm": "maas_legal_envelope"}},
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 200, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 35, "unit": "m"},
                {"name": "setback", "type": "Constraint", "Requirement": "Greater than", "val": 0.5, "unit": "m"},
            ],
            status="complete",
        )

    def test_endpoint_returns_canonical_evidence_bundle(self):
        job = self._job()
        DesignResult.objects.create(
            job=job,
            generation=0,
            design_id=900000,
            inputs=[],
            outputs={"objectives": [361.28, 61.03]},
            ranking=1.0,
            is_feasible=True,
            is_pareto_optimal=True,
            mass_geojson=self._feature(),
        )

        response = self.client.get(
            f"/design/jobs/{job.id}/results/900000/evidence/",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["schema_version"], "arr.maas.evidence.v0")
        for key in (
            "project", "site", "candidate", "geometry", "legal", "program",
            "mobility", "life_safety", "environment", "checks", "issues",
            "validators", "assets", "provenance", "agent_reviews", "final_decision",
        ):
            self.assertIn(key, data)
        self.assertEqual(data["site"]["pnu"], "1168011800104170004")
        self.assertEqual(data["candidate"]["intended_use"]["building_type"], "공동주택")
        self.assertIn("parking_strategy", data["candidate"])
        self.assertIn("precheck", data["mobility"]["parking"])
        self.assertIn("small_attached_parking_relief", data["mobility"]["parking"]["precheck"])
        self.assertEqual(data["geometry"]["geometry_metrics"]["height_m"], 17.5)
        statuses = {check["key"]: check["status"] for check in data["checks"]}
        self.assertEqual(statuses["bulk_and_density.bcr"], "pass")
        self.assertEqual(statuses["bulk_and_density.far"], "pass")
        self.assertEqual(statuses["bulk_and_density.height"], "pass")
        self.assertEqual(statuses["parking_loading_and_mobility.parking_required_count"], "needs_evidence")
        self.assertEqual(data["final_decision"]["status"], "needs_evidence")
        self.assertIn("parking_loading_and_mobility.parking_required_count", data["final_decision"]["missing_evidence"])

    def test_evidence_preserves_zero_metrics_without_fallback(self):
        job = self._job()
        feature = self._feature()
        feature["properties"]["min_setback"] = 0.0
        feature["properties"]["maas_score"] = 0.0
        feature["properties"]["maas_model"] = {
            "legal_metrics": {
                "min_setback": 99.0,
            }
        }
        DesignResult.objects.create(
            job=job,
            generation=0,
            design_id=900001,
            inputs=[],
            outputs={},
            ranking=1.0,
            is_feasible=True,
            is_pareto_optimal=True,
            mass_geojson=feature,
        )

        response = self.client.get(
            f"/design/jobs/{job.id}/results/900001/evidence/",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["candidate"]["score"], 0.0)
        self.assertEqual(data["geometry"]["geometry_metrics"]["min_setback_m"], 0.0)
        statuses = {check["key"]: check["status"] for check in data["checks"]}
        self.assertEqual(statuses["building_line_and_setbacks.adjacent_setback"], "fail")

    def test_missing_pnu_is_not_replaced_with_placeholder(self):
        job = self._job()
        job.pnu = ""
        job.save(update_fields=["pnu"])
        DesignResult.objects.create(
            job=job,
            generation=0,
            design_id=900002,
            inputs=[],
            outputs={},
            ranking=1.0,
            is_feasible=True,
            is_pareto_optimal=True,
            mass_geojson=self._feature(),
        )

        response = self.client.get(
            f"/design/jobs/{job.id}/results/900002/evidence/",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["site"]["pnu"])
        statuses = {check["key"]: check["status"] for check in data["checks"]}
        self.assertEqual(statuses["site_rights_and_cadastre.pnu_identity"], "needs_evidence")
        self.assertIn("site_rights_and_cadastre.pnu_identity", data["final_decision"]["missing_evidence"])
        self.assertIn("issue:site:missing-pnu", {issue["id"] for issue in data["issues"]})

    def test_evidence_merges_law_graph_projection_without_changing_status(self):
        job = self._job()
        DesignResult.objects.create(
            job=job,
            generation=0,
            design_id=900003,
            inputs=[],
            outputs={},
            ranking=1.0,
            is_feasible=True,
            is_pareto_optimal=True,
            mass_geojson=self._feature(),
        )

        projection = {
            "graph_status": {"available": True, "resolved_count": 1, "missing_count": 0},
            "articles": [
                {
                    "ref_id": "건축법_제60조",
                    "full_id": "건축법(법률)::제6장::제60조",
                    "law_name": "건축법",
                    "number": "60조",
                    "title": "건축물의 높이 제한",
                    "source": "neo4j",
                }
            ],
            "refs_by_check": {
                "bulk_and_density.height": ["law:건축법(법률)::제6장::제60조"],
            },
            "provenance_entities": [
                {
                    "id": "law:건축법(법률)::제6장::제60조",
                    "type": "LawArticle",
                    "title": "건축물의 높이 제한",
                }
            ],
            "provenance_relations": [
                {
                    "type": "wasDerivedFrom",
                    "entity": "law:건축법(법률)::제6장::제60조",
                    "source": "neo4j:law_graph",
                }
            ],
        }

        with patch("design.maas.evidence.build_law_provenance_projection", return_value=projection):
            response = self.client.get(
                f"/design/jobs/{job.id}/results/900003/evidence/",
                HTTP_HOST="127.0.0.1",
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["final_decision"]["status"], "needs_evidence")
        self.assertEqual(data["legal"]["graph_projection"]["available"], True)
        self.assertEqual(data["legal"]["law_articles"][0]["title"], "건축물의 높이 제한")
        checks = {check["key"]: check for check in data["checks"]}
        height_check = checks["bulk_and_density.height"]
        self.assertIn("law:건축법(법률)::제6장::제60조", height_check["basis"]["law_articles"])
        self.assertIn("law:건축법(법률)::제6장::제60조", height_check["evidence_refs"])
        self.assertIn(
            "law:건축법(법률)::제6장::제60조",
            {entity["id"] for entity in data["provenance"]["entities"]},
        )


class MaasLegalVariantsTest(TestCase):
    def _floorwise_probe_feature(self):
        lower = {
            "type": "Polygon",
            "coordinates": [[
                [127.00020, 37.00020],
                [127.00045, 37.00020],
                [127.00045, 37.00080],
                [127.00020, 37.00080],
                [127.00020, 37.00020],
            ]],
        }
        upper = {
            "type": "Polygon",
            "coordinates": [[
                [127.00050, 37.00020],
                [127.00085, 37.00020],
                [127.00085, 37.00080],
                [127.00050, 37.00080],
                [127.00050, 37.00020],
            ]],
        }
        volumes = [
            {
                "bottom_height": 0.0,
                "top_height": 3.0,
                "geometry": lower,
                "role": "lower_probe",
            },
            {
                "bottom_height": 3.0,
                "top_height": 6.0,
                "geometry": upper,
                "role": "upper_probe",
            },
        ]
        return {
            "type": "Feature",
            "geometry": lower,
            "properties": {
                "height": 6.0,
                "num_floors": 2,
                "floor_height": 3.0,
                "mass_shape": "probe_two_band",
                "mass_volumes": volumes,
                "maas_model": {"volumes": volumes, "floor_plates": []},
                "source_signature": {
                    "family": "probe",
                    "component_graph": {"stale": True},
                    "coherence_evidence": {"hard_pass": True, "score": 0.99},
                    "source_volume_roles": ["lower_probe", "upper_probe"],
                    "parameter_default_ratio": 0.2,
                },
            },
        }

    def _floorwise_probe_envelope(self):
        return build_legal_envelope(
            site_utm=wgs84_to_utm(geojson_to_polygon(self._site())),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 100, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 500, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 20, "unit": "m"},
            ],
            building_type="怨듬룞二쇳깮",
            sunlight_envelope=None,
        )

    def test_floorwise_sections_do_not_mix_next_band_at_shared_height(self):
        feature = self._floorwise_probe_feature()
        lower = wgs84_to_utm(geojson_to_polygon(feature["properties"]["mass_volumes"][0]["geometry"]))
        upper = wgs84_to_utm(geojson_to_polygon(feature["properties"]["mass_volumes"][1]["geometry"]))

        result = revalidate_final_floorwise_feature(
            feature,
            envelope=self._floorwise_probe_envelope(),
            sunlight_envelope=None,
            building_type="怨듬룞二쇳깮",
        )

        self.assertIsNotNone(result.feature)
        plates = result.feature["properties"]["floor_plates"]
        self.assertEqual(len(plates), 2)
        first = wgs84_to_utm(geojson_to_polygon(plates[0]["geometry"]))
        second = wgs84_to_utm(geojson_to_polygon(plates[1]["geometry"]))
        self.assertLessEqual(first.intersection(upper).area, 0.05)
        self.assertLessEqual(second.intersection(lower).area, 0.05)

    def test_partial_explicit_plates_cannot_hide_canonical_upper_band(self):
        feature = self._floorwise_probe_feature()
        feature["properties"]["floor_plates"] = [{
            "floor": 1,
            "top_height": 3.0,
            "area": 1.0,
            "geometry": feature["geometry"],
        }]
        feature["properties"]["maas_model"]["floor_plates"] = feature["properties"]["floor_plates"]

        result = revalidate_final_floorwise_feature(
            feature,
            envelope=self._floorwise_probe_envelope(),
            sunlight_envelope=None,
            building_type="怨듬룞二쇳깮",
        )

        self.assertIsNotNone(result.feature)
        props = result.feature["properties"]
        self.assertEqual(len(props["floor_plates"]), 2)
        self.assertEqual(
            props["floorwise_legal_evidence"]["source"],
            "derived_mass_volume_sections_incomplete_explicit_plates",
        )
        signature = props["source_signature"]
        self.assertNotIn("component_graph", signature)
        self.assertEqual(signature["coherence_evidence"]["status"], "measured")
        self.assertNotEqual(signature["coherence_evidence"]["score"], 0.99)
        self.assertEqual(signature["source_volume_roles"], ["floorwise_legal_mass"])

    def test_piloti_subtraction_keeps_canonical_geometry_and_evidence_synchronized(self):
        feature = self._floorwise_probe_feature()
        props = feature["properties"]
        props["parking_strategy"] = "piloti_ground"
        props["parking_precheck"] = {
            "layout_candidate": {"stalls": [{"id": "stall-1"}]},
        }
        props["source_volumes"] = list(props["mass_volumes"])
        props["floorwise_legal_evidence"] = {
            "status": "pass",
            "checked_mass_volume_count": 2,
        }

        _apply_piloti_parking_void(feature)

        self.assertIn("parking_piloti_void", props)
        self.assertEqual(props["mass_volumes"], props["source_volumes"])
        self.assertEqual(props["mass_volumes"], props["maas_model"]["volumes"])
        self.assertEqual(props["mass_volumes"], props["maas_model"]["source_volumes"])
        self.assertIn(
            "piloti_parking_void",
            props["floorwise_legal_evidence"]["post_validation_subtractions"],
        )

    def test_bounded_component_graph_revision_preserves_ids_and_clamps_parameter(self):
        graph = graph_from_sequence(VerbSequence(
            name="agent_revision_probe",
            label="revision probe",
            calls=(call("base", proportion="site"), call("bar", axis="x", factor=0.50)),
        ))
        node_id = graph.nodes[1].node_id

        revised, diff = apply_graph_operations(graph, [{
            "type": "scale_parameter",
            "node_id": node_id,
            "parameter": "factor",
            "factor": 4.0,
        }])

        self.assertEqual(revised.nodes[1].node_id, node_id)
        self.assertEqual(revised.nodes[1].operation.params["factor"], 0.90)
        self.assertEqual(diff[0]["before"], 0.50)
        self.assertEqual(diff[0]["after"], 0.90)
        self.assertEqual(revised.validate(), [])

        with self.assertRaisesRegex(ValueError, "root component cannot be revised directly"):
            apply_graph_operations(graph, [{
                "type": "set_parameter",
                "node_id": graph.nodes[0].node_id,
                "parameter": "factor",
                "value": 0.5,
            }])

    def test_conversation_translates_height_instruction_to_stable_node_edit(self):
        graph = graph_from_sequence(VerbSequence(
            name="agent_conversation_probe",
            label="conversation probe",
            calls=(
                call("base", proportion="site"),
                call("lift", upper_ratio=0.72, lower_floor_fraction=0.40),
            ),
        ))

        instruction = "\uc0c1\ubd80 \ub9e4\uc2a4\ub97c \uc870\uae08 \ub354 \ub0ae\ucdb0\uc918"
        operations = infer_graph_operations(graph, instruction)

        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0]["node_id"], graph.nodes[1].node_id)
        self.assertEqual(operations[0]["parameter"], "upper_ratio")
        self.assertLess(operations[0]["factor"], 1.0)

    def test_reference_vlm_translates_image_principle_to_bounded_graph_operation(self):
        graph = graph_from_sequence(VerbSequence(
            name="reference_intent_probe",
            label="reference intent probe",
            calls=(
                call("base", proportion="site"),
                call("lift", upper_ratio=0.72, lower_floor_fraction=0.40),
            ),
        ))
        response = {
            "id": "resp_reference_probe",
            "output_text": json.dumps({
                "reference_principles": ["low horizontal upper mass"],
                "operations": [{
                    "type": "scale_parameter",
                    "node_id": graph.nodes[1].node_id,
                    "parameter": "upper_ratio",
                    "factor": 0.86,
                    "value": None,
                    "reason": "Transfer the reference's lower horizontal emphasis.",
                }],
                "confidence": 0.84,
                "warnings": [],
            }),
        }

        intent = interpret_reference_intent_with_openai_vlm(
            graph=graph,
            references=[{"data_url": "data:image/png;base64,AA==", "title": "client precedent"}],
            instruction="이 이미지의 수평적인 비례를 반영해줘",
            model="fake-reference-vlm",
            response_override=response,
        )

        self.assertEqual(intent["schema_version"], "arr.maas.reference_intent.v1")
        self.assertEqual(intent["operations"][0]["node_id"], graph.nodes[1].node_id)
        self.assertEqual(intent["operations"][0]["inference_source"], "openai_reference_vlm_v1")
        self.assertEqual(intent["reference_principles"], ["low horizontal upper mass"])

    def test_reference_revision_evaluation_requires_measured_improvement(self):
        before = {
            "model": "fake-vlm", "response_id": "before", "cache_hit": True,
            "concept_scores": {
                "gesture_clarity": 0.70, "hierarchy": 0.70, "non_stair_silhouette": 0.70,
                "void_publicness": 0.50, "repair_integrity": 0.75, "precedent_resonance": 0.52,
            },
        }
        after = {
            "model": "fake-vlm", "response_id": "after", "cache_hit": False,
            "concept_scores": {
                "gesture_clarity": 0.74, "hierarchy": 0.73, "non_stair_silhouette": 0.72,
                "void_publicness": 0.51, "repair_integrity": 0.76, "precedent_resonance": 0.61,
            },
        }
        scorer = patch("design.maas.interactive.revision_evaluation.openai_preview_preference_scorer")
        with scorer as factory:
            factory.return_value.side_effect = [before, after]
            result = evaluate_reference_revision(
                before_feature={"type": "Feature"},
                after_feature={"type": "Feature"},
                references=[{"data_url": "data:image/png;base64,AA=="}],
                intent_confidence=0.82,
                model="fake-vlm",
            )

        self.assertTrue(result["improvement_gate_pass"])
        self.assertEqual(result["reference_adherence_delta"], 0.09)
        self.assertEqual(result["cache_hit_count"], 1)
        self.assertEqual(result["vlm_call_count"], 1)

    def test_conversational_revision_endpoint_returns_graph_diff_and_history(self):
        footprint = {
            "type": "Polygon",
            "coordinates": [[[127.0, 37.0], [127.0005, 37.0], [127.0005, 37.0004], [127.0, 37.0004], [127.0, 37.0]]],
        }
        graph = graph_from_sequence(VerbSequence(
            name="agent_revision_endpoint",
            label="revision endpoint",
            calls=(call("base", proportion="site"), call("bar", axis="x", factor=0.50)),
        ))
        feature = {
            "type": "Feature",
            "geometry": footprint,
            "properties": {
                "height": 8.4,
                "num_floors": 3,
                "floor_height": 2.8,
                "far": 60.0,
                "bcr": 30.0,
                "building_type": "공동주택",
                "source_signature": {"component_graph": graph.to_dict()},
                "maas_model": {"volumes": [], "legal_metrics": {}},
            },
        }
        response = self.client.post(
            "/design/maas/revision/",
            data={
                "accepted_feature": feature,
                "site_polygon": footprint,
                "project_key": "test-reference-project",
                "building_type": "공동주택",
                "instruction": "상부 바를 더 길게",
                "graph_operations": [{
                    "type": "scale_parameter",
                    "node_id": graph.nodes[1].node_id,
                    "parameter": "factor",
                    "factor": 1.25,
                }],
                "references": [{"id": "ref-01", "uri": "client-upload://ref-01"}],
            },
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["schema_version"], "arr.maas.conversational_revision.v1")
        self.assertEqual(data["graph_diff"][0]["node_id"], graph.nodes[1].node_id)
        self.assertEqual(data["reference_evidence"]["status"], "provided_with_explicit_operations")
        self.assertEqual(len(data["revision_history"]), 1)
        self.assertIn("coherence_pass", data["validation"])
        self.assertTrue(data["revision_event_id"])

        feedback = self.client.post(
            f"/design/maas/revision/{data['revision_event_id']}/feedback/",
            data={"decision": "accepted", "rating": 4.5, "note": "direction is useful"},
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(feedback.status_code, 200, feedback.content)
        self.assertEqual(feedback.json()["decision"], "accepted")
        profile = build_revision_learning_profile("test-reference-project")
        self.assertEqual(profile["feedback_event_count"], 1)
        self.assertTrue(profile["preferred_operation_patterns"])

        reference_intent = {
            "schema_version": "arr.maas.reference_intent.v1",
            "provider": "openai",
            "model": "fake-reference-vlm",
            "response_id": "resp_api_probe",
            "reference_principles": ["stronger horizontal bar"],
            "operations": [{
                "type": "scale_parameter",
                "node_id": graph.nodes[1].node_id,
                "parameter": "factor",
                "factor": 1.10,
                "inference_source": "openai_reference_vlm_v1",
            }],
            "operation_rationales": ["Transfer the horizontal proportion."],
            "confidence": 0.82,
            "warnings": [],
        }
        revision_evaluation = {
            "schema_version": "arr.maas.revision_evaluation.v1",
            "status": "improved",
            "improvement_gate_pass": True,
            "reference_adherence_delta": 0.08,
            "mass_quality_delta": 0.03,
            "failures": [],
        }
        with patch(
            "design.maas.interactive.revision.interpret_reference_intent_with_openai_vlm",
            return_value=reference_intent,
        ) as reference_vlm, patch(
            "design.maas.interactive.revision.evaluate_reference_revision",
            return_value=revision_evaluation,
        ) as revision_evaluator, patch(
            "design.maas.interactive.revision.final_mass_stage_parking_pass",
            return_value=True,
        ), patch(
            "design.maas.interactive.revision._architectural_order_gate",
            return_value=(True, []),
        ):
            vlm_response = self.client.post(
                "/design/maas/revision/",
                data={
                    "accepted_feature": feature,
                    "site_polygon": footprint,
                    "building_type": "공동주택",
                    "instruction": "이 레퍼런스의 수평 비례를 반영해줘",
                    "references": [{"data_url": "data:image/png;base64,AA=="}],
                },
                content_type="application/json",
                HTTP_HOST="127.0.0.1",
            )

        self.assertEqual(vlm_response.status_code, 200, vlm_response.content)
        vlm_data = vlm_response.json()
        self.assertEqual(vlm_data["intent_translation"]["source"], "openai_reference_vlm_v1")
        self.assertEqual(vlm_data["reference_evidence"]["status"], "vlm_interpreted")
        self.assertEqual(vlm_data["reference_evidence"]["intent"]["response_id"], "resp_api_probe")
        self.assertTrue(vlm_data["revision_evaluation"]["improvement_gate_pass"])
        reference_vlm.assert_called_once()
        revision_evaluator.assert_called_once()

    def test_final_balanced_selection_accepts_empty_preselection(self):
        self.assertEqual(_final_design_balanced_selection([], final_limit=20), [])

    def _site(self):
        return {
            "type": "Polygon",
            "coordinates": [[
                [127.0000, 37.0000],
                [127.0010, 37.0000],
                [127.0010, 37.0010],
                [127.0000, 37.0010],
                [127.0000, 37.0000],
            ]],
        }

    def _mass(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [127.0002, 37.0002],
                    [127.0008, 37.0002],
                    [127.0008, 37.0008],
                    [127.0002, 37.0008],
                    [127.0002, 37.0002],
                ]],
            },
            "properties": {"height": 28.0, "num_floors": 10, "floor_height": 2.8},
        }

    def _constraints(self):
        return [
            {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "%"},
            {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
            {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 35, "unit": "m"},
        ]

    def _sunlight_envelope(self, height=10.0):
        return {
            "slanted_polygons": [{
                "corners": [
                    [127.0000, 37.0000, height],
                    [127.0010, 37.0000, height],
                    [127.0010, 37.0010, height],
                    [127.0000, 37.0010, height],
                ],
            }],
        }

    def test_generates_repaired_legal_diverse_variants(self):
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=self._constraints(),
            building_type="공동주택",
            max_variants=4,
        )

        self.assertEqual(result["mode"], "maas_legal_variants")
        self.assertEqual(result["algorithm"], "maas_legal_envelope")
        self.assertEqual(result["seed_library"]["legacy_algorithms"], "demoted_to_seed_sources")
        self.assertEqual(result["seed_library"]["capacity_source"], "legal_envelope")
        self.assertEqual(result["seed_library"]["grammar_sequences"], "enabled_as_composite_maas_seeds")
        self.assertGreater(result["count"], 0)
        self.assertLessEqual(result["count"], 4)
        for feature in result["feature_collection"]["features"]:
            props = feature["properties"]
            self.assertEqual(props["algorithm"], "maas_legal_envelope")
            self.assertLessEqual(props["bcr"], 50.1)
            self.assertLessEqual(props["far"], 250.1)
            self.assertLessEqual(props["height"], 35.1)
            self.assertIn("maas_score", props)
            self.assertIn("far_utilization", props)
            self.assertIn("bcr_utilization", props)
            self.assertIn(props["parking_strategy"], {
                "none",
                "ground_surface",
                "piloti_ground",
                "basement",
                "semi_basement",
                "mechanical",
                "mixed",
            })
            self.assertEqual(props["parking_precheck"]["schema_version"], "arr.maas.parking_strategy.v0")
            self.assertEqual(props["parking_precheck"]["status"], "has_layout_candidate")
            self.assertEqual(
                props["parking_precheck"]["layout_candidate"]["legal_count_status"],
                "unresolved_visual_layout_only",
            )
            self.assertIn("small_attached_parking_relief", props["parking_precheck"])
            self.assertEqual(props["maas_model"]["parking_strategy"], props["parking_strategy"])

    def test_typology_first_generator_produces_architectural_families(self):
        base = wgs84_to_utm(Polygon([
            (127.00000, 37.00000),
            (127.00100, 37.00010),
            (127.00086, 37.00100),
            (127.00008, 37.00088),
            (127.00000, 37.00000),
        ]))

        variants = generate_morphology_variants(base)
        operators = {variant.operator for variant in variants}

        self.assertIn("split_bridge_x", operators)
        self.assertIn("courtyard_void", operators)
        self.assertIn("interlock_cross_diagonal", operators)
        self.assertIn("terrace_link_north", operators)
        self.assertIn("sloped_roof_mass", operators)

    def test_tiny_upper_mass_is_not_valid_typology(self):
        lower = wgs84_to_utm(Polygon([
            (127.00000, 37.00000),
            (127.00100, 37.00000),
            (127.00100, 37.00100),
            (127.00000, 37.00100),
            (127.00000, 37.00000),
        ]))
        tiny_upper = lower.centroid.buffer(1.0)

        self.assertFalse(_upper_typology_is_viable(lower, tiny_upper))

    def test_legal_layered_visual_volumes_preserve_sunlight_steps(self):
        floor_plates = []
        for floor, size in enumerate([1.0, 1.0, 0.82, 0.62, 0.42], start=1):
            floor_plates.append({
                "floor": floor,
                "top_height": floor * 2.8,
                "area": round(size * 100.0, 2),
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0, 37.0],
                        [127.0 + size * 0.001, 37.0],
                        [127.0 + size * 0.001, 37.0 + size * 0.001],
                        [127.0, 37.0 + size * 0.001],
                        [127.0, 37.0],
                    ]],
                },
            })

        volumes = _compact_visual_volumes(floor_plates, "legal_layered_max")

        self.assertLessEqual(len(volumes), 4)
        self.assertGreaterEqual(len(volumes), 2)
        self.assertEqual(volumes[0]["bottom_height"], 0.0)
        self.assertEqual(volumes[-1]["top_height"], floor_plates[-1]["top_height"])

    def test_legal_layered_anchor_has_graph_and_measured_coherence(self):
        footprint = {
            "type": "Polygon",
            "coordinates": [[[127.0, 37.0], [127.0005, 37.0], [127.0005, 37.0004], [127.0, 37.0004], [127.0, 37.0]]],
        }
        feature = {"type": "Feature", "geometry": footprint, "properties": {
            "height": 18.0,
            "mass_shape": "legal_layered_max",
            "mass_volumes": [
            {"bottom_height": 0.0, "top_height": 6.0, "geometry": footprint},
            {"bottom_height": 6.0, "top_height": 12.0, "geometry": footprint},
            {"bottom_height": 12.0, "top_height": 18.0, "geometry": footprint},
            ],
        }}

        _promote_legal_floor_stack_source_geometry(feature)

        signature = feature["properties"]["source_signature"]
        self.assertEqual(signature["component_graph"]["validation_errors"], [])
        self.assertTrue(signature["coherence_evidence"]["hard_pass"])
        self.assertEqual(signature["coherence_evidence"]["volume_count"], 3)

    def test_grammar_operator_family_maps_to_typology_family(self):
        self.assertEqual(_operator_family("grammar_cave_inset_puncture"), "void_notch")
        self.assertEqual(_operator_family("grammar_diagonal_step_connector"), "diagonal_connect")
        self.assertEqual(_operator_family("grammar_terrace_ribbon_stepback"), "terrace_link")
        self.assertEqual(_operator_family("grammar_sloped_roof_envelope"), "sloped_roof")

    def test_typology_selection_filters_fail_and_repair_even_when_under_limit(self):
        def feature(shape: str, *, status: str = "needs_mechanical_parking_review", score: float = 0.5):
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0000, 37.0000],
                        [127.0003, 37.0000],
                        [127.0003, 37.0003],
                        [127.0000, 37.0003],
                        [127.0000, 37.0000],
                    ]],
                },
                "properties": {
                    "mass_shape": shape,
                    "height": 18.0,
                    "design_quality_score": score,
                    "diversity_score": score,
                    "maas_score": score,
                    "parking_precheck": {
                        "layout_candidate": {"status": status},
                    },
                },
            }

        selected = _final_design_balanced_selection(
            [
                feature("legal_layered_max", score=0.7),
                feature("parking_repair_shrink", status="needs_drive_connectivity_review", score=0.9),
                feature("branch_y_wide", status="fail", score=0.8),
                feature("grammar_sloped_roof_envelope", score=0.6),
            ],
            final_limit=20,
        )
        shapes = [item["properties"]["mass_shape"] for item in selected]

        self.assertIn("legal_layered_max", shapes)
        self.assertIn("grammar_sloped_roof_envelope", shapes)
        self.assertNotIn("parking_repair_shrink", shapes)
        self.assertNotIn("branch_y_wide", shapes)

    def test_source_signature_contributes_to_candidate_distance(self):
        def feature(family: str, verbs: list[str], upper_ratio: float):
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0000, 37.0000],
                        [127.0003, 37.0000],
                        [127.0003, 37.0003],
                        [127.0000, 37.0003],
                        [127.0000, 37.0000],
                    ]],
                },
                "properties": {
                    "mass_shape": f"grammar_{family}",
                    "bcr": 40.0,
                    "far": 120.0,
                    "height": 12.0,
                    "shape_signature": {"compactness": 16.0},
                    "shape_signature_3d": {"volume_count": 2, "floor_plate_count": 4},
                    "source_signature": {
                        "family": family,
                        "volume_count": 2,
                        "upper_to_ground_ratio": upper_ratio,
                        "area_profile_m2": [100.0, 70.0],
                        "verb_profile": verbs,
                    },
                    "maas_verb_sequence": [{"verb": verb, "params": {}} for verb in ["base", *verbs]],
                },
            }

        same_family = _feature_distance(
            feature("terrace_link", ["lift", "terrace_link"], 0.68),
            feature("terrace_link", ["lift", "terrace_link"], 0.68),
        )
        different_family = _feature_distance(
            feature("terrace_link", ["lift", "terrace_link"], 0.68),
            feature("diagonal_connect", ["lift", "diagonal_connect"], 0.52),
        )

        self.assertGreater(different_family, same_family)

    def test_small_attached_parking_relief_tracks_road_aisle_and_tandem_exceptions(self):
        relief = evaluate_small_attached_parking_relief(
            required_spaces=5,
            road_context={
                "road_width_m": 6.0,
                "has_sidewalk_separation": False,
                "is_dead_end_road": True,
            },
        )

        self.assertEqual(relief["status"], "evaluated")
        self.assertTrue(relief["road_as_aisle_options"][0]["available"])
        self.assertFalse(relief["road_as_aisle_options"][1]["available"])
        self.assertTrue(relief["tandem_parking"]["available"])
        self.assertEqual(relief["tandem_parking"]["max_depth_from_aisle"], 2)
        self.assertEqual(relief["entrance_width"]["min_width_m"], 3.0)
        self.assertEqual(relief["entrance_width"]["dead_end_road_approval_min_width_m"], 2.5)

    def test_small_attached_parking_relief_blocks_exceptions_when_space_count_is_too_high(self):
        relief = evaluate_small_attached_parking_relief(
            required_spaces=9,
            road_context={
                "road_width_m": 6.0,
                "has_sidewalk_separation": False,
            },
        )

        self.assertFalse(relief["road_as_aisle_options"][0]["available"])
        self.assertFalse(relief["tandem_parking"]["available"])

    def test_parking_layout_candidate_places_small_tandem_stalls_with_road_as_aisle(self):
        layout = generate_parking_layout_candidate(
            box(0, 0, 12.5, 10),
            required_spaces=5,
            accessible_spaces=1,
            road_context={
                "road_width_m": 6.0,
                "has_sidewalk_separation": False,
            },
        )

        self.assertEqual(layout["status"], "pass")
        self.assertEqual(layout["placement_mode"], "road_as_aisle_tandem")
        self.assertEqual(layout["provided_spaces"], 5)
        self.assertEqual(layout["provided_accessible_spaces"], 1)
        self.assertEqual(layout["stalls"][0]["type"], "accessible")
        self.assertIn("polygon", layout["stalls"][0])
        self.assertEqual(
            layout["authority_review_check"]["status"],
            "prechecked_needs_external_evidence",
        )
        self.assertTrue(layout["authority_review_check"]["checks"]["tandem_depth_count_ok"])
        self.assertIn(
            "authority_no_traffic_obstruction_confirmation",
            layout["authority_review_check"]["external_evidence_needed"],
        )

    def test_parking_layout_candidate_places_internal_double_loaded_stalls(self):
        layout = generate_parking_layout_candidate(
            box(0, 0, 16, 16),
            required_spaces=8,
            accessible_spaces=0,
            strategy="piloti_ground",
        )

        self.assertEqual(layout["status"], "pass")
        self.assertEqual(layout["placement_mode"], "internal_double_loaded_90")
        self.assertEqual(layout["provided_spaces"], 8)
        self.assertEqual(layout["unmet_spaces"], 0)

    def test_parking_layout_candidate_draws_small_single_row_review_stalls(self):
        layout = generate_parking_layout_candidate(
            box(0, 0, 14, 5.5),
            required_spaces=5,
            accessible_spaces=1,
            strategy="ground_surface",
        )

        self.assertEqual(layout["status"], "needs_aisle_review")
        self.assertEqual(layout["placement_mode"], "single_row_aisle_review")
        self.assertEqual(layout["provided_spaces"], 5)
        self.assertEqual(layout["provided_accessible_spaces"], 1)
        self.assertEqual(layout["unmet_spaces"], 0)

    def test_parking_layout_grid_solver_places_connected_drive_cells(self):
        layout = _solve_grid_parking_layout(
            box(0, 0, 14, 11.5),
            required_spaces=3,
            accessible_spaces=0,
            strategy="piloti_ground",
            road_context={"sharedEdge": [[0, 11.5], [14, 11.5]]},
        )

        self.assertEqual(layout["status"], "pass")
        self.assertEqual(layout["placement_mode"], "grid_connected_90")
        self.assertEqual(layout["provided_spaces"], 3)
        self.assertEqual(layout["unmet_spaces"], 0)
        self.assertEqual(layout["adjacency"]["status"], "row_contiguous")
        self.assertEqual(layout["adjacency"]["gap_pairs"], 0)
        self.assertEqual(layout["column_clearance"]["status"], "deferred_structural_review")
        self.assertEqual(layout["drive_aisle_clearance"]["status"], "pass")
        self.assertEqual(layout["turning_clearance"]["status"], "v1_pass")
        self.assertEqual(layout["turning_clearance"]["method"], "stall_frontage_and_entrance_connector_v1")
        self.assertEqual(layout["turning_clearance"]["frontage_connected_stalls"], 3)
        self.assertEqual(layout["turning_clearance"]["frontage_total_stalls"], 3)
        self.assertTrue(layout["turning_clearance"]["entrance_connected"])
        self.assertIn("grid_solver", layout)
        self.assertGreaterEqual(layout["grid_solver"]["candidate_stalls"], 3)
        self.assertEqual(len(layout["grid_solver"]["drive_cells"]), 3)
        self.assertTrue(layout["grid_solver"]["drive_components_connected"])
        self.assertTrue(layout["grid_solver"]["entrance_connected"])
        self.assertEqual(layout["grid_solver"]["entrance_connection_method"], "road_frontage_geometry")

    def test_parking_layout_grid_solver_flags_disconnected_entrance_edge(self):
        layout = _solve_grid_parking_layout(
            box(0, 0, 14, 11.5),
            required_spaces=3,
            accessible_spaces=0,
            strategy="piloti_ground",
            road_context={"sharedEdge": [[0, 20], [14, 20]]},
        )

        self.assertEqual(layout["status"], "needs_drive_connectivity_review")
        self.assertEqual(layout["provided_spaces"], 3)
        self.assertFalse(layout["grid_solver"]["entrance_connected"])
        self.assertEqual(layout["grid_solver"]["entrance_connection_method"], "road_frontage_geometry")
        self.assertGreater(layout["grid_solver"]["entrance_min_distance_m"], 0)
        self.assertEqual(layout["turning_clearance"]["status"], "needs_swept_path_review")
        self.assertEqual(layout["turning_clearance"]["frontage_connected_stalls"], 3)
        self.assertFalse(layout["turning_clearance"]["entrance_connected"])

    def test_parking_layout_grid_solver_records_site_connector_turning_v1(self):
        layout = _solve_grid_parking_layout(
            box(0, 0, 14, 11.5),
            drive_polygon=box(0, 0, 14, 17),
            required_spaces=3,
            accessible_spaces=0,
            strategy="piloti_ground",
            road_context={"sharedEdge": [[0, 17], [14, 17]]},
        )

        self.assertEqual(layout["status"], "pass")
        self.assertEqual(layout["grid_solver"]["entrance_connection_type"], "site_connector_v1")
        self.assertEqual(layout["grid_solver"]["entrance_connector_width_m"], 3.0)
        self.assertEqual(layout["turning_clearance"]["status"], "v1_pass")
        self.assertEqual(layout["turning_clearance"]["method"], "stall_frontage_and_entrance_connector_v1")
        self.assertEqual(layout["turning_clearance"]["frontage_connected_stalls"], 3)
        self.assertTrue(layout["turning_clearance"]["entrance_connected"])
        self.assertEqual(layout["turning_clearance"]["entrance_connection_type"], "site_connector_v1")

    def test_parking_drive_entrance_allows_site_connector_inside_drive_area(self):
        access = _drive_entrance_access(
            [box(2, 2, 4, 4)],
            box(0, 0, 10, 10),
            road_context={"sharedEdge": [[10, 2], [10, 4]]},
        )

        self.assertTrue(access["connected"])
        self.assertEqual(access["connection_type"], "site_connector_v1")
        self.assertEqual(access["connector_length_m"], 6.0)
        self.assertEqual(access["connector_width_m"], 3.0)

    def test_parking_drive_entrance_rejects_connector_without_min_width(self):
        access = _drive_entrance_access(
            [box(2, 2.8, 4, 3.2)],
            box(0, 2.6, 10, 3.4),
            road_context={"sharedEdge": [[10, 2.8], [10, 3.2]]},
        )

        self.assertFalse(access["connected"])
        self.assertEqual(access["connection_type"], "none")

    def test_parking_drive_entrance_rejects_connector_outside_drive_area(self):
        access = _drive_entrance_access(
            [box(2, 2, 4, 4)],
            box(0, 0, 10, 10),
            road_context={"sharedEdge": [[12, 2], [12, 4]]},
        )

        self.assertFalse(access["connected"])
        self.assertEqual(access["connection_type"], "none")

    def test_parking_layout_grid_solver_prefers_accessible_drive_edge(self):
        layout = _solve_grid_parking_layout(
            box(0, 0, 70, 11.5),
            required_spaces=2,
            accessible_spaces=0,
            strategy="ground_surface",
            road_context={"sharedEdge": [[0, 0], [70, 0]]},
        )

        self.assertEqual(layout["status"], "pass")
        self.assertEqual(layout["adjacency"]["status"], "row_contiguous")
        self.assertTrue(layout["grid_solver"]["entrance_connected"])
        self.assertEqual(layout["grid_solver"]["entrance_min_distance_m"], 0.0)

    def test_parking_layout_grid_solver_prefers_adjacent_small_stalls(self):
        layout = _solve_grid_parking_layout(
            box(0, 0, 70, 11.5),
            required_spaces=2,
            accessible_spaces=0,
            strategy="ground_surface",
            road_context={"sharedEdge": [[0, 11.5], [70, 11.5]]},
        )

        self.assertEqual(layout["provided_spaces"], 2)
        first = Polygon(layout["stalls"][0]["polygon"])
        second = Polygon(layout["stalls"][1]["polygon"])
        self.assertLessEqual(first.distance(second), 0.05)
        self.assertEqual(layout["adjacency"]["status"], "row_contiguous")
        self.assertTrue(layout["adjacency"]["contiguous_ok"])
        self.assertEqual(layout["layout_formula"]["schema_version"], "arr.maas.parking_formula.v1")
        self.assertEqual(layout["layout_formula"]["module"]["double_loaded_90_depth_m"], 16.0)
        self.assertEqual(layout["column_clearance"]["status"], "not_applicable")
        self.assertEqual(layout["drive_aisle_clearance"]["status"], "pass")
        self.assertEqual(layout["turning_clearance"]["status"], "v1_pass")

    def test_parking_layout_grid_solver_fails_when_accessible_stall_is_missing(self):
        layout = _solve_grid_parking_layout(
            box(0, 0, 2.6, 11.5),
            required_spaces=1,
            accessible_spaces=1,
            strategy="ground_surface",
            road_context={"sharedEdge": [[0, 11.5], [2.6, 11.5]]},
        )

        self.assertEqual(layout["status"], "fail")
        self.assertEqual(layout["provided_spaces"], 1)
        self.assertEqual(layout["provided_accessible_spaces"], 0)
        self.assertEqual(layout["unmet_spaces"], 0)
        self.assertEqual(layout["unmet_accessible_spaces"], 1)
        self.assertEqual(layout["reason"], "grid_solver_insufficient_accessible_stall_candidates")

    def test_parking_strategy_keeps_searching_after_aisle_review_candidate(self):
        strategy = infer_parking_strategy(
            {
                "footprint_area": 80.0,
                "floor_area": 160.0,
                "num_floors": 2,
                "bcr": 50.0,
                "required_parking_spaces": 2,
                "parking_road_context": {
                    "sharedEdge": [[0, 17], [14, 17]],
                },
            },
            site_area_m2=238.0,
            building_type="다가구주택",
            footprint_utm=box(0, 0, 14, 5.5),
            site_utm=box(0, 0, 14, 17),
        )

        self.assertEqual(strategy["selected_strategy"], "piloti_ground")
        self.assertEqual(strategy["layout_candidate"]["status"], "pass")
        self.assertEqual(strategy["layout_candidate"]["turning_clearance"]["frontage_connected_stalls"], 2)

    def test_parking_strategy_attaches_layout_candidate_when_required_count_exists(self):
        strategy = infer_parking_strategy(
            {
                "footprint_area": 125.0,
                "floor_area": 250.0,
                "num_floors": 2,
                "bcr": 50.0,
                "required_parking_spaces": 5,
                "required_accessible_parking_spaces": 1,
                "parking_road_context": {
                    "road_width_m": 6.0,
                    "has_sidewalk_separation": False,
                },
            },
            site_area_m2=250.0,
            building_type="다가구주택",
            footprint_utm=box(0, 0, 12.5, 10),
            site_utm=box(0, 0, 20, 12.5),
        )

        self.assertEqual(strategy["status"], "has_layout_candidate")
        self.assertEqual(strategy["layout_candidate"]["status"], "pass")
        self.assertEqual(strategy["layout_candidate"]["provided_spaces"], 5)
        self.assertIn("parking_envelope_wgs84", strategy)
        self.assertIn("polygon_wgs84", strategy["layout_candidate"]["stalls"][0])
        self.assertEqual(len(strategy["layout_candidate"]["stalls"][0]["polygon_wgs84"][0]), 2)

    def test_mechanical_parking_unlocks_high_far_mass_stage_without_final_pass(self):
        strategy = infer_parking_strategy(
            {
                "footprint_area": 180.0,
                "floor_area": 660.0,
                "num_floors": 7,
                "bcr": 68.0,
                "required_parking_spaces": 7,
            },
            site_area_m2=264.0,
            building_type="공동주택",
            footprint_utm=box(0, 0, 13.5, 13.5),
            site_utm=box(0, 0, 16, 16),
        )

        layout = strategy["layout_candidate"]
        self.assertEqual(strategy["selected_strategy"], "mechanical")
        self.assertEqual(layout["status"], "needs_mechanical_parking_review")
        self.assertEqual(layout["provided_spaces"], 7)
        self.assertEqual(layout["mass_stage_parking"]["status"], "pass")
        self.assertTrue(layout["mass_stage_parking"]["authority_review_required"])
        self.assertIn("mechanical_parking_equipment_type", layout["authority_review_check"]["external_evidence_needed"])
        self.assertEqual(layout["stalls"], [])

    def test_basement_parking_needs_ramp_evidence_before_final_pass(self):
        layout = generate_parking_layout_candidate(
            box(0, 0, 16, 16),
            required_spaces=2,
            strategy="basement",
            road_context={"sharedEdge": [[0, 0], [16, 0]]},
        )

        self.assertEqual(layout["provided_spaces"], 2)
        self.assertEqual(layout["status"], "needs_basement_ramp_review")
        self.assertIn(
            "basement_ramp_slope_width_and_turning_geometry",
            layout["authority_review_check"]["external_evidence_needed"],
        )

    def test_parking_requirement_local_seed_rules_compute_neighborhood_use(self):
        rules = {
            "national": {
                "parking_appendix1_row_03": {
                    "rule_id": "parking_appendix1_row_03",
                    "row_no": "3",
                    "spaces_per": 200.0,
                    "rounding_rule": "appendix_note_6_half_up_total_under_one_zero",
                }
            },
            "local": [
                {
                    "rule_id": "seoul_parking_appendix2_row_03",
                    "base_rule_id": "parking_appendix1_row_03",
                    "pnu_prefix": "11",
                    "row_no": "3",
                    "spaces_per": 134.0,
                    "rounding_rule": "ordinance_note_6_half_up_total_under_one_zero",
                }
            ],
        }
        requirement = resolve_candidate_parking_requirement(
            pnu="1168011800104170004",
            building_type="근린생활시설",
            facility_area_m2=264.0,
            rules=rules,
        )

        self.assertEqual(requirement["status"], "computed")
        self.assertEqual(requirement["selected_rule_id"], "seoul_parking_appendix2_row_03")
        self.assertEqual(requirement["required_spaces"], 2)
        self.assertEqual(requirement["accessible"]["accessible_min"], 0)

    def test_parking_requirement_maps_multifamily_house_to_unit_schedule_rule(self):
        requirement = resolve_candidate_parking_requirement(
            pnu="1168011800104170004",
            building_type="다가구주택",
            facility_area_m2=300.0,
            options={
                "housing_unit_schedule": [
                    {
                        "unit_type": "50m2",
                        "exclusive_area_m2": 50.0,
                        "count": 4,
                    },
                ],
            },
        )

        self.assertEqual(requirement["status"], "computed")
        self.assertEqual(
            requirement["base_rule_id"],
            "parking_appendix1_row_05",
        )
        self.assertEqual(requirement["required_spaces"], 4)
        self.assertEqual(
            requirement["unit_schedule"]["units"][0]["count"],
            4,
        )

    def test_grammar_sequences_generate_composite_variants(self):
        variants = generate_grammar_variants(box(0, 0, 30, 20))

        self.assertGreaterEqual(len(variants), 6)
        operators = {variant.operator for variant in variants}
        self.assertIn("grammar_courtyard_lift_taper", operators)
        self.assertIn("grammar_podium_tower_offset", operators)
        self.assertIn("grammar_sunlight_multi_step", operators)
        self.assertIn("grammar_diagonal_step_connector", operators)
        self.assertIn("grammar_terrace_ribbon_stepback", operators)
        self.assertIn("grammar_sloped_roof_envelope", operators)
        for variant in variants:
            self.assertTrue(variant.operator.startswith(("grammar_", "agent_")))
            self.assertGreaterEqual(len(variant.verb_sequence), 2)
            self.assertEqual(variant.verb_sequence[0]["verb"], "base")
            self.assertEqual(variant.source_geometry_status, "compiled")
            self.assertIsNotNone(variant.source_signature)
            self.assertGreaterEqual(variant.source_signature["volume_count"], 1)
            self.assertGreaterEqual(variant.source_signature["surface_count"], 1)
            self.assertGreaterEqual(len(variant.source_verb_trace), 2)
            self.assertGreaterEqual(len(variant.source_volumes), 1)
            self.assertGreaterEqual(len(variant.source_surfaces), 1)

        source_rich = {
            variant.operator: variant
            for variant in variants
            if variant.upper_footprint is not None
        }
        self.assertIn("grammar_cave_inset_puncture", source_rich)
        self.assertIn("grammar_interlock_step_taper", source_rich)
        self.assertGreaterEqual(len(source_rich), 8)

    def test_design_section_operators_create_upper_mass_hints(self):
        from design.maas.morphology_operators import generate_morphology_variants

        variants = generate_morphology_variants(box(0, 0, 30, 20))
        by_operator = {variant.operator: variant for variant in variants}

        for operator in (
            "diagonal_connect_step_x",
            "diagonal_connect_step_y",
            "terrace_link_north",
            "sloped_roof_mass",
        ):
            self.assertIn(operator, by_operator)
            variant = by_operator[operator]
            self.assertIsNotNone(variant.upper_footprint)
            self.assertLess(variant.upper_footprint.area, variant.footprint.area)
            self.assertGreaterEqual(len(variant.verb_sequence), 2)
            self.assertEqual(variant.verb_sequence[0]["verb"], "base")

    def test_maas_sequence_metrics_follow_reference_eval_contract(self):
        from design.maas.design_quality import ordered_lcs, sequence_metrics, token_f1, verb_set_jaccard

        pred = [
            {"verb": "base", "params": {}},
            {"verb": "courtyard", "params": {}},
            {"verb": "lift", "params": {}},
            {"verb": "taper", "params": {}},
        ]
        gold = [
            {"verb": "base", "params": {}},
            {"verb": "courtyard", "params": {}},
            {"verb": "taper", "params": {}},
        ]

        self.assertEqual(ordered_lcs(pred, gold), 2)
        self.assertAlmostEqual(verb_set_jaccard(pred, gold), 2 / 3, places=4)
        self.assertAlmostEqual(token_f1(pred, gold), 0.8, places=4)
        metrics = sequence_metrics(pred, gold)
        self.assertEqual(metrics["parsimony"], 3)
        self.assertTrue(metrics["has_plan_operation"])
        self.assertTrue(metrics["has_section_operation"])
        self.assertEqual(metrics["reference_comparison"]["ordered_lcs"], 2)

    def test_d4descent_clone_backend_is_connected_as_research_optimizer(self):
        from design.maas.research_backends import d4descent_design_evidence

        evidence = d4descent_design_evidence(enable_import=False)

        self.assertEqual(evidence["name"], "d4descent")
        self.assertEqual(evidence["source"], "clone/d4descent")
        self.assertTrue(evidence["backend"]["exists"])
        self.assertEqual(evidence["backend"]["interfaces"]["optimizer"], "d4descent.optimizer.optimize")
        self.assertEqual(evidence["absorbed_pattern"]["rewrite"], "ARR grammar/morphology operators")

    def test_maas_clone_bridge_compiles_reference_sequence(self):
        backend = inspect_maas_clone_backend(enable_import=False)

        self.assertEqual(backend["name"], "MAAS")
        self.assertEqual(backend["source"], "clone/MAAS")
        self.assertTrue(backend["exists"])
        self.assertEqual(backend["interfaces"]["compiler"], "maas.grammar.compiler.compile_sequence")

        baseline = run_maas_clone_reference_baseline(enable_import=True)
        self.assertEqual(baseline["status"], "compiled")
        self.assertEqual(baseline["scad_compile_status"], "compiled")
        self.assertTrue(baseline["scad_contains"]["cube"])
        self.assertEqual(baseline["metric_summary"]["token_f1"], 1.0)
        self.assertEqual(baseline["metric_summary"]["ordered_lcs"], 2)
        self.assertIn("missing_artifacts", baseline)
        self.assertEqual(baseline["case_gold_source"]["status"], "available")
        self.assertEqual(baseline["case_baseline"]["status"], "compiled")
        self.assertEqual(baseline["case_baseline"]["case_count"], 10)
        self.assertEqual(baseline["case_baseline"]["compiled_case_count"], 10)
        self.assertIn("stack", baseline["case_baseline"]["unique_gold_verbs"])
        self.assertIn("rotate_part", baseline["case_baseline"]["unique_gold_verbs"])

    def test_maas_algorithm_benchmark_command_writes_latest_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = StringIO()
            call_command(
                "benchmark_maas_algorithms",
                "--out-dir",
                tmp,
                "--operators",
                "grammar_diagonal_step_connector",
                "--max-variants",
                "3",
                stdout=out,
            )

            latest = os.path.join(tmp, "latest.json")
            self.assertTrue(os.path.exists(latest))
            with open(latest, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["mode"], "maas_algorithm_benchmark")
            self.assertEqual(data["parking_mode"], "disabled")
            self.assertEqual(data["source"]["legal_truth"], "ARR deterministic legal repair/evaluation")
            original = data["source"]["original_maas_baseline"]
            self.assertEqual(original["source"], "clone/MAAS")
            self.assertEqual(original["status"], "compiled")
            self.assertEqual(original["scad_compile_status"], "compiled")
            self.assertEqual(original["case_baseline"]["case_count"], 10)
            self.assertEqual(original["case_baseline"]["compiled_case_count"], 10)
            self.assertIn("cave", data["aggregate"]["original_maas_reference_verbs"])
            self.assertIn("stack", data["aggregate"]["original_maas_reference_verbs"])
            self.assertIn("embed", data["aggregate"]["original_maas_reference_verbs"])
            self.assertIn("branch", data["aggregate"]["original_maas_reference_verbs"])
            self.assertIn("overlap", data["aggregate"]["original_maas_reference_verbs"])
            self.assertIn("rotate_part", data["aggregate"]["original_maas_reference_verbs"])
            self.assertEqual(data["aggregate"]["original_maas_baseline_status"], "compiled")
            self.assertEqual(data["aggregate"]["original_maas_case_baseline_status"], "compiled")
            self.assertEqual(data["aggregate"]["original_maas_case_count"], 10)
            self.assertEqual(data["aggregate"]["original_maas_compiled_case_count"], 10)
            self.assertGreaterEqual(data["aggregate"]["scenario_count"], 2)
            self.assertEqual(data["aggregate"]["successful_scenarios"], data["aggregate"]["scenario_count"])
            self.assertEqual(data["aggregate"]["parking_evidence_feature_count"], 0)
            self.assertIsNone(data["aggregate"]["parking_pass_rate"])
            self.assertEqual(data["aggregate"]["preferred_survival_rate"], 1.0)
            self.assertGreaterEqual(data["aggregate"]["legal_pass_rate"], 0.99)
            self.assertGreaterEqual(data["aggregate"]["unique_mass_shape_count"], 3)
            self.assertGreaterEqual(data["aggregate"]["unique_concept_count"], 3)
            self.assertGreaterEqual(data["aggregate"]["unique_verb_count"], 3)
            self.assertGreaterEqual(data["aggregate"]["average_unique_shapes_per_scenario"], 3.0)
            self.assertGreaterEqual(data["aggregate"]["section_connector_feature_count"], 1)
            self.assertGreaterEqual(data["aggregate"]["section_connector_scenario_count"], 1)
            self.assertGreaterEqual(data["aggregate"]["section_connector_shape_count"], 1)
            self.assertIn("mass_shape_histogram", data["aggregate"])
            self.assertFalse(any(
                feature.get("parking_evidence_enabled")
                for scenario in data["scenarios"]
                for feature in scenario.get("features", [])
            ))
            self.assertTrue(all(
                scenario.get("unique_mass_shape_count", 0) >= 3
                for scenario in data["scenarios"]
                if scenario.get("status") == "ok"
            ))
            self.assertTrue(any(
                scenario.get("preferred_operator") == "grammar_diagonal_step_connector"
                and scenario.get("preferred_top")
                for scenario in data["scenarios"]
            ))

    def test_generated_variants_include_design_quality_and_d4descent_evidence(self):
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
            ],
            building_type="공동주택",
            max_variants=4,
            preferred_operator="grammar_diagonal_step_connector",
        )

        top = result["feature_collection"]["features"][0]["properties"]
        quality = top["design_quality"]
        self.assertEqual(quality["source"], "arr.maas.design_quality.v1")
        self.assertIn("sequence_metrics", quality)
        self.assertGreaterEqual(quality["score"], 0.0)
        self.assertLessEqual(quality["score"], 1.0)
        self.assertEqual(quality["optimizer_backend"]["name"], "d4descent")
        self.assertIn(quality["optimizer_backend"]["status"], {"imported", "import_failed", "available_not_imported", "missing"})
        self.assertEqual(top["maas_model"]["design_quality"]["score"], quality["score"])

    def test_sunlight_cap_and_bcr_fill_are_prioritized(self):
        constraints = [
            {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
            {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
            {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
        ]

        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=constraints,
            building_type="공동주택",
            max_variants=5,
            sunlight_envelope=self._sunlight_envelope(height=10.0),
        )

        self.assertGreater(result["count"], 0)
        features = result["feature_collection"]["features"]
        for feature in features:
            props = feature["properties"]
            self.assertLessEqual(props["height"], 10.1)
            self.assertLessEqual(props["bcr"], 60.1)
            self.assertLessEqual(props["far"], 250.1)
        top = features[0]["properties"]
        self.assertIn(top["mass_shape"], {"legal_layered_max", "legal_buildable_max", "bcr_fill_light", "bcr_fill_mid", "bcr_fill_strong"})
        self.assertGreaterEqual(top["bcr"], 45.0)

    def test_final_candidates_carry_floorwise_law_evidence_before_ranking(self):
        constraints = [
            {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
            {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
            {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
        ]
        sunlight_envelope = self._sunlight_envelope(height=10.0)
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=constraints,
            building_type="怨듬룞二쇳깮",
            max_variants=5,
            sunlight_envelope=sunlight_envelope,
        )
        envelope = build_legal_envelope(
            site_utm=wgs84_to_utm(geojson_to_polygon(self._site())),
            constraints=constraints,
            building_type="怨듬룞二쇳깮",
            sunlight_envelope=sunlight_envelope,
        )

        features = result["feature_collection"]["features"]
        if not features:
            self.assertEqual(result.get("generation_status"), "infeasible")
            self.assertTrue(result.get("infeasible_reason"))
            self.assertTrue(all(rejection.get("reason") for rejection in result.get("rejected", [])))
            return

        for feature in features:
            props = feature["properties"]
            plates = props.get("floor_plates") or []
            evidence = props.get("floorwise_legal_evidence") or {}
            volumes = props.get("mass_volumes") or []
            self.assertGreater(len(plates), 0, props.get("mass_shape"))
            self.assertEqual(evidence.get("status"), "pass", props.get("mass_shape"))
            self.assertEqual(evidence.get("checked_floor_count"), len(plates))
            self.assertEqual(evidence.get("checked_mass_volume_count"), len(volumes))
            self.assertLessEqual(props["height"], 10.1)
            for plate in plates:
                allowed = allowed_footprint_at_height(
                    envelope,
                    float(plate["top_height"]),
                    sunlight_envelope,
                )
                self.assertIsNotNone(allowed)
                occupied = wgs84_to_utm(geojson_to_polygon(plate["geometry"]))
                self.assertLessEqual(occupied.difference(allowed).area, 0.05)

    def test_feasible_three_floor_candidate_records_floorwise_pass_evidence(self):
        constraints = [
            {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
            {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
            {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
        ]
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=constraints,
            building_type="怨듬룞二쇳깮",
            max_variants=1,
            preferred_operator="legal_layered_max",
            sunlight_envelope=self._sunlight_envelope(height=10.0),
        )

        self.assertEqual(result["count"], 1)
        props = result["feature_collection"]["features"][0]["properties"]
        self.assertEqual(
            [plate["top_height"] for plate in props["floor_plates"]],
            [3.0, 6.0, 9.0],
        )
        evidence = props.get("floorwise_legal_evidence") or {}
        self.assertEqual(evidence.get("status"), "pass")
        self.assertEqual(evidence.get("checked_floor_count"), 3)
        self.assertEqual(props["source_volumes"], props["mass_volumes"])
        self.assertEqual(props["maas_model"]["source_volumes"], props["mass_volumes"])
        self.assertNotIn("source_surfaces", props)
        self.assertNotIn("section_source_surfaces", props)
        self.assertEqual(
            props["geometry_resolution"]["status"],
            "floorwise_legal_revalidated",
        )

    def test_floorwise_repair_rejects_candidate_below_existing_far_policy(self):
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
            ],
            building_type="怨듬룞二쇳깮",
            max_variants=1,
            preferred_operator="legal_layered_max",
            sunlight_envelope=self._sunlight_envelope(height=10.0),
            parking_options={"min_far_utilization": 0.95},
        )

        self.assertEqual(result["generation_status"], "infeasible")
        self.assertEqual(result["count"], 0)
        underfill = [
            rejection
            for rejection in result["rejected"]
            if rejection.get("reason") == "underused_floorwise_legal_far_capacity"
        ]
        self.assertGreater(len(underfill), 0)
        self.assertTrue(all(item["measured_far_utilization"] < 0.95 for item in underfill))

    def test_buildable_max_variant_can_outgrow_small_source_mass(self):
        mass = self._mass()
        mass["geometry"]["coordinates"] = [[
            [127.00045, 37.00045],
            [127.00055, 37.00045],
            [127.00055, 37.00055],
            [127.00045, 37.00055],
            [127.00045, 37.00045],
        ]]

        result = generate_legal_mass_variants(
            mass_geojson=mass,
            site_polygon_geojson=self._site(),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
                {"name": "building_line_setback", "type": "Constraint", "Requirement": "Greater than", "val": 0.5, "unit": "m"},
            ],
            building_type="공동주택",
            max_variants=5,
        )

        top = result["feature_collection"]["features"][0]["properties"]
        self.assertEqual(top["mass_shape"], "legal_layered_max")
        self.assertIn("maas_model", top)
        self.assertEqual(top["maas_model"]["operator"], top["mass_shape"])
        self.assertGreater(len(top["maas_model"]["volumes"]), 0)
        self.assertIn("floor_plates", top)
        self.assertGreater(len(top["floor_plates"]), 0)
        min_plate_area = min(24.0, top["floor_plates"][0]["area"] * 0.25)
        for plate in top["floor_plates"]:
            self.assertGreaterEqual(plate["area"], min_plate_area)
        self.assertEqual(top["maas_model"]["floor_plates"], top["floor_plates"])
        self.assertIn("floor_groups", top["maas_model"])
        self.assertGreater(len(top["maas_model"]["floor_groups"]), 0)
        first_group = top["maas_model"]["floor_groups"][0]
        self.assertEqual(first_group["program_packing"]["constraint_source"], "maas_legal_envelope")
        self.assertEqual(first_group["program_packing"]["algorithm"], "circle_grid_packing")
        self.assertEqual(first_group["program_packing"]["best_floor_plan"]["type"], "FeatureCollection")
        self.assertGreater(first_group["program_packing"]["preview_summary"]["room_count"], 0)
        self.assertLessEqual(top["bcr"], 60.1)
        self.assertLessEqual(top["far"], 250.1)
        self.assertGreater(top["bcr"], 1.0)

    def test_variant_selection_preserves_capacity_and_shape_diversity(self):
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
            ],
            building_type="공동주택",
            max_variants=6,
            sunlight_envelope={
                "slanted_polygons": [{
                    "corners": [
                        [127.0000, 37.0000, 10.0],
                        [127.0010, 37.0000, 14.0],
                        [127.0010, 37.0010, 30.0],
                        [127.0000, 37.0010, 24.0],
                    ],
                }],
            },
        )

        features = result["feature_collection"]["features"]
        shapes = {f["properties"]["mass_shape"].replace("_layered", "") for f in features}
        self.assertGreaterEqual(len(features), 6)
        self.assertGreaterEqual(len(shapes), 5)
        for feature in features:
            props = feature["properties"]
            self.assertLessEqual(props["bcr"], 60.1)
            self.assertLessEqual(props["far"], 250.1)
            self.assertLessEqual(props["height"], 50.1)
            self.assertIn("shape_signature_3d", props)
            self.assertIn("candidate_diversity", props)
            self.assertIn(props["candidate_diversity"]["class"], {"plan_diverse", "section_diverse", "near_duplicate"})
            if props["mass_shape"].startswith("grammar_"):
                self.assertEqual(props["source_geometry_status"], "compiled")
                self.assertIn("source_signature", props["maas_model"])
                self.assertIn("source_verb_trace", props["maas_model"])
        self.assertTrue(any("floor_plates" in f["properties"] for f in features))
        diversity_classes = {f["properties"]["candidate_diversity"]["class"] for f in features}
        self.assertTrue({"plan_diverse", "section_diverse"} & diversity_classes)
        connector_verbs = {"diagonal_connect", "terrace_link", "sloped_roof_mass"}
        connector_features = [
            f for f in features
            if connector_verbs & {
                item.get("verb")
                for item in f["properties"].get("maas_verb_sequence", [])
                if isinstance(item, dict)
            }
        ]
        self.assertTrue(connector_features)

    def test_source_geometry_records_default_provenance_for_arch_language_verbs(self):
        base = box(0, 0, 42, 32)
        verbs = [
            "notch",
            "cave",
            "courtyard",
            "split",
            "bar",
            "branch",
            "pinch",
            "bend",
            "embed",
            "extrude",
            "nest",
            "stack",
            "offset",
            "array",
            "reflect",
            "interlock",
            "overlap",
            "taper",
            "grade",
            "shift",
            "inset",
            "expand",
        ]

        for verb in verbs:
            sequence = VerbSequence(
                name=f"llm_default_probe_{verb}",
                label=verb,
                calls=(call("base", proportion="site"), call(verb)),
            )
            source = compile_sequence_to_source_mass(base, sequence)

            self.assertIsNotNone(source, verb)
            signature = source.signature()
            self.assertGreater(signature["parameter_default_count"], 0, verb)
            self.assertTrue(signature["parameter_provenance"], verb)

    def test_formal_principle_generates_architecture_grade_tapered_tower(self):
        sequence = VerbSequence(
            name="llm_architecture_probe_undercut",
            label="undercut tapered tower",
            calls=(
                call("base", proportion="site"),
                call("taper", x_ratio=0.62, y_ratio=0.58, lower_floor_fraction=0.40),
            ),
            notes=(
                "formal_principle=undercut_tapered_tower",
                "dominant_gesture=undercut podium with tapered upper mass",
                "reference_basis=Vancouver House/BIG-like undercut/taper principle",
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 42, 30), sequence)

        self.assertIsNotNone(source)
        signature = source.signature()
        ambition = signature["architectural_ambition_evidence"]
        roles = {volume.role for volume in source.volumes}
        self.assertEqual(ambition["formal_principle"], "undercut_tapered_tower")
        self.assertTrue(ambition["architecture_grade_pass"])
        self.assertTrue(any("undercut" in role for role in roles))
        self.assertTrue(any("tower" in role for role in roles))
        self.assertGreaterEqual(len(source.volumes), 3)

    def test_formal_principle_generates_stacked_platform_roles(self):
        sequence = VerbSequence(
            name="llm_architecture_probe_stack",
            label="shifted platform stack",
            calls=(
                call("base", proportion="site"),
                call("shift", distance_ratio=0.18, lower_floor_fraction=0.44),
            ),
            notes=(
                "formal_principle=stacked_shifted_platforms",
                "dominant_gesture=OMA/Seattle Library-like shifted platform diagram",
                "reference_basis=stacked platform and diagrammatic section principle",
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 42, 30), sequence)

        self.assertIsNotNone(source)
        signature = source.signature()
        ambition = signature["architectural_ambition_evidence"]
        roles = {volume.role for volume in source.volumes}
        self.assertEqual(ambition["formal_principle"], "stacked_shifted_platforms")
        self.assertTrue(ambition["architecture_grade_pass"])
        self.assertGreaterEqual(sum(role.startswith("primary_shifted_platform_") for role in roles), 3)
        self.assertTrue(source.signature()["coherence_evidence"]["hard_pass"])

    def test_array_cluster_preserves_podium_scale_and_clean_coherence(self):
        base = box(0, 0, 42, 30)
        source = compile_sequence_to_source_mass(
            base,
            VerbSequence(
                name="grammar_clean_program_box_cluster",
                label="clean program box cluster",
                calls=(
                    call("base", proportion="site"),
                    call("array", n=2, unit_scale=0.46, spacing_ratio=0.26),
                ),
                notes=("primary_language=clean_program_box_cluster",),
            ),
        )

        self.assertIsNotNone(source)
        signature = source.signature()
        self.assertGreaterEqual(source.footprint.area / base.area, 0.95)
        self.assertEqual(signature["volume_count"], 3)
        self.assertTrue(signature["coherence_evidence"]["hard_pass"])
        self.assertEqual(signature["coherence_evidence"]["small_fragment_count"], 0)

    def test_massing_genome_prioritizes_family_over_taper_tokens(self):
        cases = [
            (
                "grammar_courtyard_lift_taper__sweep_court_open",
                (call("base", proportion="site"), call("courtyard", ratio=0.20), call("taper", x_ratio=0.92)),
                "carved_atrium",
            ),
            (
                "grammar_diagonal_step_connector__sweep_taper_sharp",
                (call("base", proportion="site"), call("diagonal_connect", axis="x"), call("taper", x_ratio=0.82)),
                "split_bridge_connector",
            ),
            (
                "grammar_sloped_roof_envelope__sweep_taper_sharp",
                (call("base", proportion="site"), call("sloped_roof_mass", x_ratio=0.70), call("taper", x_ratio=0.88)),
                "folded_section",
            ),
            (
                "grammar_interlock_step_taper__sweep_interlock_thick",
                (call("base", proportion="site"), call("interlock", angle=28.0), call("taper", x_ratio=0.70)),
                "torqued_stack",
            ),
            (
                "grammar_overlap_shift_terrace__sweep_lift_low",
                (call("base", proportion="site"), call("overlap", axis="x"), call("lift", upper_ratio=0.72)),
                "stacked_shifted_platforms",
            ),
        ]

        for name, calls, expected_principle in cases:
            with self.subTest(name=name):
                sequence = VerbSequence(name=name, label=name, calls=calls)
                source = compile_sequence_to_source_mass(box(0, 0, 42, 30), sequence)

                self.assertIsNotNone(source)
                genome = source.signature()["massing_genome"]
                self.assertEqual(genome["schema_version"], "arr.maas.massing_genome.v1")
                self.assertEqual(genome["formal_principle"], expected_principle)
                self.assertNotEqual(genome["formal_principle"], "undercut_tapered_tower")
                self.assertEqual(genome["inference_source"], "family_priority")

    def test_massing_genome_exports_layered_attribution_circuit(self):
        sequence = VerbSequence(
            name="grammar_diagonal_step_connector__sweep_taper_sharp",
            label="diagonal connector with taper token",
            calls=(
                call("base", proportion="site"),
                call("diagonal_connect", axis="x"),
                call("taper", x_ratio=0.82),
            ),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 42, 30), sequence)

        self.assertIsNotNone(source)
        circuit = source.signature()["massing_genome_circuit"]
        self.assertEqual(circuit["schema_version"], "arr.maas.genome_attribution_circuit.v1")
        self.assertEqual(circuit["graph_type"], "layered_attribution_flow")
        node_layers = {node["layer"] for node in circuit["nodes"]}
        self.assertTrue({"source", "concept", "strategy", "critic", "agent_action"}.issubset(node_layers))
        edge_kinds = {edge["kind"] for edge in circuit["edges"]}
        self.assertIn("evidence_to_concept", edge_kinds)
        self.assertIn("critic_to_action_gate", edge_kinds)
        self.assertTrue(any(node["id"] == "concept.formal_principle" for node in circuit["nodes"]))

    def test_formal_compiler_records_genome_strategy_specific_roles(self):
        cases = [
            (
                "grammar_interlock_step_taper__sweep_interlock_thick",
                (call("base", proportion="site"), call("interlock", angle=28.0), call("taper", x_ratio=0.70)),
                "torqued_stack",
                "rotated_stack",
                "_torqued_plate_",
            ),
            (
                "grammar_sloped_roof_envelope__sweep_taper_sharp",
                (call("base", proportion="site"), call("sloped_roof_mass", x_ratio=0.70), call("taper", x_ratio=0.88)),
                "folded_section",
                "folded_planes",
                "_folded_",
            ),
            (
                "grammar_overlap_shift_terrace__sweep_lift_low",
                (call("base", proportion="site"), call("overlap", axis="x"), call("lift", upper_ratio=0.72)),
                "stacked_shifted_platforms",
                "shifted_platforms",
                "_shifted_platform_",
            ),
        ]

        for name, calls, expected_principle, expected_strategy, expected_role_prefix in cases:
            with self.subTest(name=name):
                source = compile_sequence_to_source_mass(
                    box(0, 0, 42, 30),
                    VerbSequence(name=name, label=name, calls=calls),
                )

                self.assertIsNotNone(source)
                signature = source.signature()
                genome = signature["massing_genome"]
                ambition = signature["architectural_ambition_evidence"]
                roles = {volume.role for volume in source.volumes}
                self.assertEqual(genome["formal_principle"], expected_principle)
                self.assertEqual(genome["vertical_strategy"], expected_strategy)
                self.assertEqual(ambition["formal_principle"], expected_principle)
                self.assertEqual(ambition["vertical_strategy"], expected_strategy)
                self.assertEqual(ambition["genome_strategy_evidence"]["vertical_strategy"], expected_strategy)
                self.assertTrue(signature["primary_language"])
                self.assertTrue(signature["secondary_language"])
                self.assertGreater(signature["source_primitive_count"], 0)
                self.assertTrue(any(expected_role_prefix in role for role in roles))

    def test_final_selection_keeps_stepback_and_weak_llm_caps_after_replacement(self):
        def feature(shape: str, family: str, *, score: float, quality: str = "reviewable") -> dict:
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0002, 37.0002],
                        [127.0008, 37.0002],
                        [127.0008, 37.0008],
                        [127.0002, 37.0008],
                        [127.0002, 37.0002],
                    ]],
                },
                "properties": {
                    "mass_shape": shape,
                    "height": 24.0,
                    "far": 120.0,
                    "bcr": 35.0,
                    "maas_score": score,
                    "design_quality_score": score,
                    "diversity_score": score,
                    "source_geometry_status": "compiled",
                    "geometry_resolution": {"status": "source_geometry_used"},
                    "source_signature": {
                        "family": family,
                        "volume_count": 2,
                        "surface_count": 8,
                        "parameter_default_count": 0,
                        "architectural_ambition_evidence": {
                            "schema_version": "arr.maas.architectural_ambition.v1",
                            "formal_principle": "stacked_shifted_platforms",
                            "dominant_gesture": f"{family} review mass",
                            "has_formal_principle": True,
                            "has_dominant_gesture": True,
                            "implemented_volume_roles": [
                                "primary_shifted_platform_0",
                                "primary_shifted_platform_1",
                                "secondary_vertical_datum_core",
                            ],
                            "silhouette_strength": 0.82,
                            "sectional_diagram_clarity": 0.82,
                            "podium_or_ground_relationship": True,
                            "architecture_grade_pass": True,
                        },
                    },
                    "architectural_ambition_evidence": {
                        "schema_version": "arr.maas.architectural_ambition.v1",
                        "formal_principle": "stacked_shifted_platforms",
                        "dominant_gesture": f"{family} review mass",
                        "has_formal_principle": True,
                        "has_dominant_gesture": True,
                        "implemented_volume_roles": [
                            "primary_shifted_platform_0",
                            "primary_shifted_platform_1",
                            "secondary_vertical_datum_core",
                        ],
                        "silhouette_strength": 0.82,
                        "sectional_diagram_clarity": 0.82,
                        "podium_or_ground_relationship": True,
                        "architecture_grade_pass": True,
                    },
                    "orderliness_evidence": {
                        "schema_version": "arr.maas.orderliness.v1",
                        "status": "measured",
                        "dominant_axis": "balanced",
                        "main_role": "primary_mass",
                        "main_mass_area_ratio": 0.45,
                        "aligned_role_ratio": 0.85,
                        "small_fragment_count": 0,
                        "fragment_role_count": 0,
                        "role_hierarchy_depth": 2,
                        "unclear_language_mix": False,
                        "orderliness_score": 0.82,
                    },
                    "mass_volumes": [
                        {"bottom_height": 0.0, "top_height": 12.0, "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.0002, 37.0002],
                                [127.0008, 37.0002],
                                [127.0008, 37.0008],
                                [127.0002, 37.0008],
                                [127.0002, 37.0002],
                            ]],
                        }},
                        {"bottom_height": 12.0, "top_height": 24.0, "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.00025, 37.00025],
                                [127.00075, 37.00025],
                                [127.00075, 37.00075],
                                [127.00025, 37.00075],
                                [127.00025, 37.00025],
                            ]],
                        }},
                        {"bottom_height": 18.0, "top_height": 24.0, "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.0003, 37.0003],
                                [127.0007, 37.0003],
                                [127.0007, 37.0007],
                                [127.0003, 37.0007],
                                [127.0003, 37.0003],
                            ]],
                        }},
                    ],
                    "parking_precheck": {
                        "layout_candidate": {"status": "pass", "provided_spaces": 6, "required_spaces": 4},
                    },
                    "llm_candidate_quality": {"status": quality},
                },
            }

        selected = [feature("legal_layered_max", "legal_layered", score=1.0)]
        for index, family in enumerate(["stepback_tower", "terrace_link", "grade", "taper", "stepback_tower"]):
            selected.append(feature(f"llm_step_{index}", family, score=0.95 - index * 0.01))
        for index, family in enumerate(["courtyard", "split", "slender_bar", "branch", "array_cluster", "interlock"]):
            selected.append(feature(f"llm_good_{index}", family, score=0.80 - index * 0.01))
        selected.append(feature("llm_weak_review", "overlap", score=0.99, quality="reject_final_review"))
        for index, family in enumerate([
            "overlap",
            "bend",
            "embed",
            "extrude",
            "nest",
            "reflected_pair",
            "pinch",
            "sloped_roof",
            "diagonal_connect",
            "offset",
        ]):
            selected.append(feature(f"grammar_{family}_{index}", family, score=0.70 - index * 0.01))

        result = _final_design_balanced_selection(selected, final_limit=20)
        families = [item["properties"]["source_signature"]["family"] for item in result]
        weak_llm = [
            item for item in result
            if item["properties"]["llm_candidate_quality"]["status"] == "reject_final_review"
        ]

        self.assertLessEqual(sum(family in {"stepback_tower", "terrace_link", "grade", "taper"} for family in families), 3)
        self.assertLessEqual(len(weak_llm), 1)
        self.assertGreaterEqual(sum(item["properties"]["mass_shape"].startswith("llm_") for item in result), 4)

    def test_final_selection_limits_repeated_formal_principle_when_alternatives_exist(self):
        def feature(
            shape: str,
            family: str,
            formal_principle: str,
            vertical_strategy: str,
            *,
            score: float,
        ) -> dict:
            ambition = {
                "schema_version": "arr.maas.architectural_ambition.v1",
                "formal_principle": formal_principle,
                "dominant_gesture": f"{formal_principle} review mass",
                "has_formal_principle": True,
                "has_dominant_gesture": True,
                "implemented_volume_roles": [
                    f"primary_{formal_principle}_0",
                    f"primary_{formal_principle}_1",
                    f"secondary_{formal_principle}_datum",
                ],
                "massing_genome_schema_version": "arr.maas.massing_genome.v1",
                "genome_strategy_evidence": {
                    "vertical_strategy": vertical_strategy,
                    "stair_like_risk": "low",
                },
                "vertical_strategy": vertical_strategy,
                "stair_like_risk": "low",
                "silhouette_strength": 0.86,
                "sectional_diagram_clarity": 0.86,
                "podium_or_ground_relationship": True,
                "architecture_grade_pass": True,
            }
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0002, 37.0002],
                        [127.0008, 37.0002],
                        [127.0008, 37.0008],
                        [127.0002, 37.0008],
                        [127.0002, 37.0002],
                    ]],
                },
                "properties": {
                    "mass_shape": shape,
                    "height": 24.0,
                    "far": 120.0,
                    "bcr": 35.0,
                    "maas_score": score,
                    "design_quality_score": score,
                    "diversity_score": score,
                    "source_geometry_status": "compiled",
                    "geometry_resolution": {"status": "source_geometry_used"},
                    "source_signature": {
                        "family": family,
                        "volume_count": 3,
                        "surface_count": 12,
                        "parameter_default_count": 0,
                        "massing_genome": {
                            "schema_version": "arr.maas.massing_genome.v1",
                            "formal_principle": formal_principle,
                            "vertical_strategy": vertical_strategy,
                            "stair_like_risk": "low",
                        },
                        "architectural_ambition_evidence": ambition,
                    },
                    "architectural_ambition_evidence": ambition,
                    "orderliness_evidence": {
                        "schema_version": "arr.maas.orderliness.v1",
                        "status": "measured",
                        "dominant_axis": "balanced",
                        "main_role": "primary_mass",
                        "main_mass_area_ratio": 0.50,
                        "aligned_role_ratio": 0.88,
                        "small_fragment_count": 0,
                        "fragment_role_count": 0,
                        "role_hierarchy_depth": 2,
                        "unclear_language_mix": False,
                        "orderliness_score": 0.86,
                    },
                    "mass_volumes": [
                        {"bottom_height": 0.0, "top_height": 8.0, "geometry": {"type": "Polygon", "coordinates": [[[127.0002, 37.0002], [127.0008, 37.0002], [127.0008, 37.0008], [127.0002, 37.0008], [127.0002, 37.0002]]]}},
                        {"bottom_height": 8.0, "top_height": 16.0, "geometry": {"type": "Polygon", "coordinates": [[[127.00025, 37.00025], [127.00075, 37.00025], [127.00075, 37.00075], [127.00025, 37.00075], [127.00025, 37.00025]]]}},
                        {"bottom_height": 16.0, "top_height": 24.0, "geometry": {"type": "Polygon", "coordinates": [[[127.0003, 37.0003], [127.0007, 37.0003], [127.0007, 37.0007], [127.0003, 37.0007], [127.0003, 37.0003]]]}},
                    ],
                    "parking_precheck": {
                        "layout_candidate": {"status": "pass", "provided_spaces": 6, "required_spaces": 4},
                    },
                    "llm_candidate_quality": {"status": "reviewable"},
                },
            }

        repeated_families = [
            "courtyard",
            "split",
            "slender_bar",
            "branch",
            "array_cluster",
            "interlock",
            "overlap",
            "bend",
            "embed",
            "extrude",
        ]
        alternatives = [
            ("void_notch", "carved_monolith", "central_void"),
            ("nest", "carved_monolith", "nested_void"),
            ("reflected_pair", "stacked_shifted_platforms", "shifted_platforms"),
            ("pinch", "torqued_stack", "rotated_stack"),
            ("diagonal_connect", "split_bridge_connector", "split_bridge"),
            ("sloped_roof", "folded_section", "folded_planes"),
            ("offset", "stacked_shifted_platforms", "shifted_platforms"),
            ("terrace_link", "folded_section", "folded_planes"),
            ("grade", "folded_section", "folded_planes"),
            ("taper", "slender_podium_tower", "podium_tower"),
            ("courtyard", "carved_atrium", "atrium_cut"),
            ("split", "split_bridge_connector", "split_bridge"),
            ("slender_bar", "slender_podium_tower", "podium_tower"),
            ("branch", "torqued_stack", "rotated_stack"),
            ("array_cluster", "stacked_shifted_platforms", "shifted_platforms"),
            ("interlock", "torqued_stack", "rotated_stack"),
            ("overlap", "stacked_shifted_platforms", "shifted_platforms"),
        ]
        selected = [
            feature(
                f"llm_repeated_{index}",
                family,
                "undercut_tapered_tower",
                "undercut_taper",
                score=0.99 - index * 0.01,
            )
            for index, family in enumerate(repeated_families)
        ]
        selected.extend(
            feature(
                f"llm_alt_{index}",
                family,
                formal_principle,
                strategy,
                score=0.70 - index * 0.01,
            )
            for index, (family, formal_principle, strategy) in enumerate(alternatives)
        )

        result = _final_design_balanced_selection(selected, final_limit=20)
        principles = [
            item["properties"]["architectural_ambition_evidence"]["formal_principle"]
            for item in result
        ]
        strategies = [
            item["properties"]["architectural_ambition_evidence"]["vertical_strategy"]
            for item in result
        ]

        self.assertEqual(len(result), 20)
        self.assertLessEqual(principles.count("undercut_tapered_tower"), 5)
        self.assertLessEqual(strategies.count("undercut_taper"), 5)
        self.assertGreaterEqual(len(set(principles)), 5)

    def test_section_connector_preservation_does_not_override_parking_gate(self):
        def feature(shape: str, *, provided: int, score: float) -> dict:
            return {
                "type": "Feature",
                "properties": {
                    "mass_shape": shape,
                    "maas_score": score,
                    "parking_precheck": {
                        "required_count": {"required_spaces": 3},
                        "layout_candidate": {
                            "status": "pass" if provided >= 3 else "fail",
                            "required_spaces": 3,
                            "provided_spaces": provided,
                            "unmet_spaces": max(0, 3 - provided),
                        },
                    },
                },
            }

        visible_pass = [
            feature("legal_layered_max", provided=3, score=0.9),
            feature("court_open_east", provided=3, score=0.8),
        ]
        weak_connector = feature("grammar_diagonal_step_connector_layered", provided=1, score=0.7)

        selected = _preserve_visible_section_connector(
            [*visible_pass, weak_connector],
            final_limit=2,
        )

        self.assertEqual(
            [item["properties"]["mass_shape"] for item in selected[:2]],
            ["legal_layered_max", "court_open_east"],
        )

    def test_preferred_design_operator_survives_selection(self):
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
            ],
            building_type="공동주택",
            max_variants=4,
            preferred_operator="grammar_terrace_ribbon_stepback",
        )

        features = result["feature_collection"]["features"]
        self.assertGreater(len(features), 0)
        top = features[0]["properties"]
        self.assertEqual(top["mass_shape"], "grammar_terrace_ribbon_stepback")
        self.assertEqual(top["maas_concept"], "연속테라스 스텝백")
        self.assertIn("maas_model", top)
        self.assertGreaterEqual(len(top["maas_model"]["volumes"]), 2)
        self.assertIn("terrace_link", [item["verb"] for item in top["maas_verb_sequence"]])
        self.assertLessEqual(top["bcr"], 60.1)
        self.assertLessEqual(top["far"], 250.1)

    def test_layered_stack_uses_floor_by_floor_envelope(self):
        """층별 허용 footprint를 잘라 사선 높이 여유를 FAR로 활용한다."""
        envelope = {
            "slanted_polygons": [{
                "corners": [
                    [127.0000, 37.0000, 10.0],
                    [127.0010, 37.0000, 10.0],
                    [127.0010, 37.0010, 30.0],
                    [127.0000, 37.0010, 30.0],
                ],
            }],
        }
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=self._site(),
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 60, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 250, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
            ],
            building_type="공동주택",
            max_variants=5,
            sunlight_envelope=envelope,
        )

        top = result["feature_collection"]["features"][0]["properties"]
        self.assertEqual(top["mass_shape"], "legal_layered_max")
        self.assertTrue(result["constraints"]["has_floor_plate_stack"])
        self.assertGreater(top["height"], 10.0)
        self.assertLessEqual(top["far"], 250.1)
        self.assertLessEqual(top["bcr"], 60.1)
        self.assertGreater(len(top["floor_plates"]), 3)
        areas = [p["area"] for p in top["floor_plates"]]
        self.assertLess(areas[-1], areas[0])
        min_plate_area = min(24.0, areas[0] * 0.25)
        for area in areas:
            self.assertGreaterEqual(area, min_plate_area)

    def test_edge_specific_setback_geometry_avoids_global_road_buffer(self):
        """도로 setback은 도로 edge에만 적용하고 반대편 인접 edge 용량은 보존한다."""
        site = self._site()
        # bottom road edge만 8m 후퇴, 나머지는 buildable_area 0.5m 기반.
        setback_geometries = {
            "buildable_area": {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.000005, 37.000005],
                        [127.000995, 37.000005],
                        [127.000995, 37.000995],
                        [127.000005, 37.000995],
                        [127.000005, 37.000005],
                    ]],
                },
                "distance_m": 0.5,
                "label": "edge-specific buildable",
            },
            "road_setback": {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [127.0000, 37.000072],
                        [127.0010, 37.000072],
                    ],
                },
                "distance_m": 8.0,
                "label": "bottom road only",
            },
        }
        result = generate_legal_mass_variants(
            mass_geojson=self._mass(),
            site_polygon_geojson=site,
            constraints=[
                {"name": "bcr", "type": "Constraint", "Requirement": "Less than", "val": 80, "unit": "%"},
                {"name": "far", "type": "Constraint", "Requirement": "Less than", "val": 400, "unit": "%"},
                {"name": "height", "type": "Constraint", "Requirement": "Less than", "val": 50, "unit": "m"},
                {"name": "setback", "type": "Constraint", "Requirement": "Greater than", "val": 0.5, "unit": "m"},
            ],
            building_type="공동주택",
            max_variants=3,
            setback_geometries=setback_geometries,
        )

        top = result["feature_collection"]["features"][0]["properties"]
        self.assertEqual(top["mass_shape"], "legal_layered_max")
        self.assertGreater(top["bcr"], 50.0)
        self.assertLess(top["bcr"], 80.1)

    def test_interactive_operation_endpoint_returns_synced_metrics(self):
        response = self.client.post(
            "/design/interactive/operation/",
            data={
                "mass_geojson": self._mass(),
                "site_polygon": self._site(),
                "constraints": self._constraints(),
                "building_type": "공동주택",
                "operation": {"type": "push_pull_height", "delta_floors": 1},
            },
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "interactive_operation")
        props = data["feature"]["properties"]
        self.assertLessEqual(props["bcr"], 50.1)
        self.assertLessEqual(props["far"], 250.1)
        self.assertLessEqual(props["height"], 35.1)
        self.assertEqual(data["normalized_operation"]["type"], "push_pull_face")
        self.assertIn("operation_history", props)
        self.assertGreaterEqual(len(data["agent_reviews"]), 4)
        self.assertEqual(data["a2ui_messages"][0]["version"], "v0.9")
        self.assertIn("createSurface", data["a2ui_messages"][0])

    def test_interactive_offset_edge_returns_agent_reviewed_legal_mass(self):
        response = self.client.post(
            "/design/interactive/operation/",
            data={
                "mass_geojson": self._mass(),
                "site_polygon": self._site(),
                "constraints": self._constraints(),
                "building_type": "공동주택",
                "operation": {
                    "type": "offset_edge",
                    "target": {"kind": "side", "edge_index": 1},
                    "delta_m": 2.0,
                },
            },
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        props = data["feature"]["properties"]
        self.assertEqual(data["normalized_operation"]["type"], "offset_edge")
        self.assertEqual(data["normalized_operation"]["target"]["edge_index"], 1)
        self.assertEqual(props["mass_shape"], "interactive_seed_repaired")
        self.assertLessEqual(props["bcr"], 50.1)
        self.assertLessEqual(props["far"], 250.1)
        self.assertIn("operation_history", props)
        self.assertTrue(any(r["agent"] == "law_graph_agent" for r in data["agent_reviews"]))
        self.assertEqual(data["a2ui_messages"][1]["updateComponents"]["surfaceId"], "maas-agent-review")

    def test_maas_agent_registry_exposes_flow_cards(self):
        from design.maas.agents import build_agent_cards, build_agent_registry
        from design.maas.agents.orchestrator.flow import FLOW_AGENT_SEQUENCE, FLOW_STEPS

        registry = build_agent_registry()
        self.assertEqual(list(FLOW_AGENT_SEQUENCE), [
            "design_orchestrator",
            "law_graph_agent",
            "parking_agent",
            "massdsl_agent",
            "maas_geometry_agent",
            "grammar_critic_agent",
            "review_agent",
        ])
        self.assertTrue(all(agent_id in registry for agent_id in FLOW_AGENT_SEQUENCE))
        cards = build_agent_cards()
        self.assertEqual([card["name"] for card in cards], list(FLOW_AGENT_SEQUENCE))
        self.assertEqual(FLOW_STEPS[1][0], "design_orchestrator")
        self.assertEqual(FLOW_STEPS[1][1], "law_graph_agent")
        self.assertTrue(any(step[1] == "massdsl_agent" for step in FLOW_STEPS))
        self.assertTrue(any(step[1] == "grammar_critic_agent" for step in FLOW_STEPS))
        self.assertTrue(all("skills" in card and "capabilities" in card for card in cards))

    def test_overheight_source_does_not_inflate_legal_seed_floors(self):
        mass = self._mass()
        mass["properties"] = {"height": 280.0, "num_floors": 100, "floor_height": 2.8}

        result = generate_legal_mass_variants(
            mass_geojson=mass,
            site_polygon_geojson=self._site(),
            constraints=self._constraints(),
            building_type="공동주택",
            max_variants=3,
        )

        # 35m / 2.8m = 12 floors. The source may be illegal, but the seed budget
        # reported by MAAS must remain the legal height-derived seed.
        self.assertEqual(result["constraints"]["max_seed_floors"], 12)
        for feature in result["feature_collection"]["features"]:
            self.assertLessEqual(feature["properties"]["height"], 35.1)

    def test_endpoint_returns_feature_collection(self):
        response = self.client.post(
            "/design/maas/legal-variants/",
            data={
                "mass_geojson": self._mass(),
                "site_polygon": self._site(),
                "constraints": self._constraints(),
                "building_type": "공동주택",
                "max_variants": 3,
            },
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "maas_legal_variants")
        self.assertEqual(data["feature_collection"]["type"], "FeatureCollection")
        self.assertLessEqual(data["count"], 3)
        self.assertGreaterEqual(len(data["agent_reviews"]), 6)
        self.assertTrue(any(review["agent"] == "massdsl_agent" for review in data["agent_reviews"]))
        self.assertTrue(any(review["agent"] == "grammar_critic_agent" for review in data["agent_reviews"]))
        self.assertEqual(data["a2ui_messages"][0]["version"], "v0.9")
        self.assertIn("massdsl_proposals", data)
        self.assertIn("grammar_reviews", data)
        first_props = data["feature_collection"]["features"][0]["properties"]
        self.assertIn("massdsl_proposal", first_props)
        self.assertIn("grammar_review", first_props)
        self.assertIn("validation_status", first_props["massdsl_proposal"])
        self.assertIn("status", first_props["grammar_review"])

    def test_massdsl_agent_contract_compiles_from_candidate_evidence(self):
        from design.maas.agents.grammar_critic_agent import build_grammar_review
        from design.maas.agents.massdsl_agent import build_massdsl_proposal

        feature = {
            "type": "Feature",
            "properties": {
                "variant_id": "maas_01",
                "mass_shape": "grammar_diagonal_step_connector",
                "maas_verb_sequence": [
                    {"verb": "base", "params": {}},
                    {"verb": "lift", "params": {"upper_ratio": 0.78}},
                    {"verb": "diagonal_connect", "params": {"axis": "x"}},
                ],
                "source_geometry_status": "compiled",
                "source_signature": {
                    "family": "diagonal_connect",
                    "volume_count": 2,
                    "surface_count": 8,
                    "verb_profile": ["lift", "diagonal_connect"],
                },
                "source_surfaces": [
                    {"role": "source_roof_upper", "surface_type": "roof_polygon", "vertex_count": 4},
                ],
                "geometry_resolution": {
                    "status": "source_geometry_used",
                    "source": "massdsl_proposal_source_geometry",
                    "legal_action": "repaired_and_clipped_to_legal_envelope",
                },
                "visual_diversity_evidence": {
                    "visual_family": "diagonal_connect",
                    "volume_count": 2,
                    "hole_count": 0,
                    "stepback_like": False,
                },
                "parking_precheck": {
                    "layout_candidate": {"status": "pass", "provided_spaces": 3},
                },
            },
        }

        proposal = build_massdsl_proposal(
            feature,
            operation_type="maas_legal_variants",
            constraints={"far_limit": 250, "bcr_limit": 60, "height_limit": 35},
        )
        review = build_grammar_review(feature)

        self.assertEqual(proposal["schema_version"], "arr.maas.massdsl.proposal.v1")
        self.assertEqual(proposal["proposal_source"], "deterministic_agent_contract")
        self.assertEqual(proposal["validation_status"], "valid")
        self.assertIn("design_parameters", proposal)
        self.assertEqual(proposal["design_parameters"]["family"], "diagonal_connect")
        self.assertEqual(
            proposal["design_parameters"]["parameter_source"],
            "deterministic_sequence_library",
        )
        self.assertTrue(proposal["design_parameters"]["requires_llm_authoring"])
        self.assertIn("authoring_gap", proposal["design_parameters"])
        self.assertIn("fallback_rank", proposal)
        self.assertEqual(proposal["source_refs"]["source_geometry_status"], "compiled")
        self.assertEqual(proposal["source_refs"]["source_surface_count"], 1)
        self.assertEqual(review["schema_version"], "arr.maas.grammar_review.v1")
        self.assertEqual(review["status"], "pass")
        self.assertTrue(review["has_section_language"])
        self.assertTrue(review["has_source_surface_contract"])
        self.assertEqual(review["geometry_resolution"]["status"], "source_geometry_used")
        self.assertEqual(review["visual_diversity_evidence"]["visual_family"], "diagonal_connect")

    def test_llm_massdsl_batch_contract_compiles_structured_population(self):
        response = self._llm_batch_response()

        batch = generate_llm_massdsl_batch(
            site_context={"site_area_m2": 264.1, "limits": {"far": 250, "bcr": 60, "height": 50}},
            target_count=120,
            model="test-model",
            response_override=response,
        )

        self.assertEqual(batch.artifact["schema_version"], LLM_BATCH_SCHEMA_VERSION)
        self.assertEqual(batch.artifact["provider"], "openai")
        self.assertGreaterEqual(batch.artifact["raw_candidate_count"], 120)
        self.assertGreaterEqual(batch.artifact["compiled_sequence_count"], 120)
        self.assertGreaterEqual(len(batch.sequences), 120)
        self.assertTrue(batch.sequences[0].name.startswith("llm_"))
        self.assertIn(f"parameter_source={LLM_PARAMETER_SOURCE}", batch.sequences[0].notes)
        self.assertFalse(batch.sequences[0].validate())

    def _llm_batch_response(self):
        def candidate(index):
            patterns = [
                [
                    {"verb": "base", "params": {"proportion": "site"}},
                    {"verb": "array", "params": {"n": 3, "axis": "x", "spacing_ratio": 0.18, "unit_scale": 0.34, "lower_floor_fraction": 0.34}},
                    {"verb": "terrace_link", "params": {"side": "north", "upper_ratio": 0.78, "width_ratio": 0.46, "depth_ratio": 0.18, "lower_floor_fraction": 0.38}},
                ],
                [
                    {"verb": "base", "params": {"proportion": "site"}},
                    {"verb": "split", "params": {"axis": "y", "gap_ratio": 0.24, "bridge_ratio": 0.22, "upper_ratio": 0.78, "lower_floor_fraction": 0.40}},
                    {"verb": "diagonal_connect", "params": {"axis": "x", "upper_ratio": 0.72, "distance_ratio": 0.10, "angle": 28.0, "lower_floor_fraction": 0.38}},
                ],
                [
                    {"verb": "base", "params": {"proportion": "site"}},
                    {"verb": "bar", "params": {"axis": "x", "factor": 0.42, "shift": 0.04, "upper_ratio": 0.82, "lower_floor_fraction": 0.44}},
                    {"verb": "offset", "params": {"axis": "y", "distance_ratio": 0.24, "other_scale": 0.72, "upper_ratio": 0.78, "lower_floor_fraction": 0.38}},
                ],
                [
                    {"verb": "base", "params": {"proportion": "site"}},
                    {"verb": "branch", "params": {"angle": 42.0, "trunk_ratio": 0.26, "arm_ratio": 0.2, "upper_ratio": 0.78, "lower_floor_fraction": 0.42}},
                    {"verb": "taper", "params": {"x_ratio": 0.72, "y_ratio": 0.78, "lower_floor_fraction": 0.42}},
                ],
            ]
            return {
                "name": f"proposal_{index:03d}",
                "label": f"LLM proposal {index:03d}",
                "typology": ["array_cluster", "split_bridge", "offset_bar", "branch_taper"][index % 4],
                "architectural_language": "clustered connector massing",
                "intent_tags": ["cluster", "connector", "legal_solver_validated"],
                "calls": patterns[index % len(patterns)],
                "rationale": "Test proposal keeps authored MassDSL parameters separate from legal validation.",
            }

        return {
            "language_palette": [f"language_{i}" for i in range(30)],
            "combination_rules": [f"rule_{i}" for i in range(10)],
            "candidates": [candidate(i) for i in range(120)],
        }

    def test_llm_sequence_compiles_to_source_variant_with_llm_provenance(self):
        from design.maas.grammar.legal_interpreter import interpret_sequence

        batch = generate_llm_massdsl_batch(
            site_context={"site_area_m2": 264.1, "limits": {"far": 250, "bcr": 60, "height": 50}},
            target_count=120,
            model="test-model",
            response_override=self._llm_batch_response(),
        )

        variant = interpret_sequence(wgs84_to_utm(Polygon(self._site()["coordinates"][0])), batch.sequences[0])

        self.assertIsNotNone(variant)
        self.assertTrue(variant.operator.startswith("llm_"))
        self.assertEqual(
            variant.research_basis["parameter_source"],
            LLM_PARAMETER_SOURCE,
        )
        self.assertFalse(variant.research_basis["requires_llm_authoring"])
        self.assertEqual(variant.research_basis["optimization_mode"], "llm_arch_language_proposal")


class MaasIntentTrainingContractTest(TestCase):
    def _job(self, *, algorithm="maas_legal_envelope"):
        return OptimizationJob.objects.create(
            pnu="1168011800104170004",
            address="",
            site_polygon={
                "type": "Polygon",
                "coordinates": [[
                    [127.0000, 37.0000],
                    [127.0010, 37.0000],
                    [127.0010, 37.0010],
                    [127.0000, 37.0010],
                    [127.0000, 37.0000],
                ]],
            },
            site_area_m2=264.1,
            job_spec={"options": {"building_type": "공동주택", "algorithm": algorithm}},
            constraints=[],
            status="complete",
        )

    def _design(self, job, design_id, *, algorithm="maas_legal_envelope"):
        return DesignResult.objects.create(
            job=job,
            generation=0,
            design_id=design_id,
            inputs=[],
            outputs={},
            ranking=1.0,
            is_feasible=True,
            is_pareto_optimal=True,
            mass_geojson={
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0000, 37.0000],
                        [127.0004, 37.0000],
                        [127.0004, 37.0004],
                        [127.0000, 37.0004],
                        [127.0000, 37.0000],
                    ]],
                },
                "properties": {"algorithm": algorithm, "height": 15.0},
            },
        )

    def test_korean_architectural_intent_resolves_to_maas_sequence_not_geometry(self):
        result = resolve_intent_to_sequence("북측 일조 때문에 상부를 계단식으로 후퇴시켜줘")

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["policy"]["llm_must_not_emit_raw_geometry"])
        self.assertEqual(result["policy"]["geometry_source_of_truth"], "ARR/backend/design/maas")
        top = result["proposals"][0]
        self.assertEqual(top["sequence"], "grammar_sunlight_multi_step")
        self.assertEqual(top["maas_sequence"][0]["verb"], "base")
        self.assertNotIn("coordinates", json.dumps(top, ensure_ascii=False))
        self.assertIn("sunlight", top["constraints"]["must_validate"])

    def test_term_ontology_contains_architecture_terms_for_sequence_mapping(self):
        ontology = load_term_ontology()
        terms = {term["id"]: term for term in ontology["terms"]}

        self.assertIn("sunlight_step", terms)
        self.assertIn("podium_tower", terms)
        self.assertIn("split_bridge", terms)
        self.assertIn("diagonal_connect", terms)
        self.assertIn("terrace_link", terms)
        self.assertIn("sloped_roof_mass", terms)
        self.assertIn("step_envelope", terms["sunlight_step"]["verbs"])
        self.assertIn("split", terms["split_bridge"]["verbs"])
        self.assertIn("diagonal_connect", terms["diagonal_connect"]["verbs"])

    def test_seed_sft_examples_train_intent_to_sequence_contract(self):
        examples = build_sft_examples()
        sunlight_examples = [
            example for example in examples
            if example["sequence"] == "grammar_sunlight_multi_step"
        ]

        self.assertGreaterEqual(len(sunlight_examples), 2)
        assistant = json.loads(sunlight_examples[0]["messages"][2]["content"])
        self.assertEqual(assistant["maas_sequence"][0]["verb"], "base")
        self.assertEqual(
            assistant["constraints"]["geometry_source_of_truth"],
            "ARR/backend/design/maas",
        )
        self.assertIn("sunlight", assistant["constraints"]["must_validate"])

    def test_sft_seed_export_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = export_sft_seed(os.path.join(tmp, "maas_intent_sft_seed.jsonl"))
            lines = path.read_text(encoding="utf-8").splitlines()

        self.assertGreater(len(lines), 10)
        first = json.loads(lines[0])
        self.assertEqual(first["source"], "arr.maas.sequence_library.v0")
        self.assertEqual(first["messages"][0]["role"], "system")

    def test_evidence_review_training_keeps_missing_evidence_visible(self):
        evidence = {
            "schema_version": "arr.maas.evidence.v0",
            "bundle_id": "maas-evidence:test-job:maas_01",
            "candidate": {
                "candidate_id": "maas_01",
                "mass_shape": "legal_layered_max",
                "maas_concept": "legal capacity anchor",
            },
            "geometry": {
                "geometry_metrics": {"height_m": 17.5, "far": 136.78},
                "verb_sequence": [{"verb": "base", "params": {"source": "legal_buildable"}}],
            },
            "checks": [
                {"key": "bulk_and_density.height", "status": "pass"},
                {"key": "parking_loading_and_mobility.parking_required_count", "status": "needs_evidence"},
            ],
            "final_decision": {
                "status": "needs_evidence",
                "missing_evidence": ["parking_loading_and_mobility.parking_required_count"],
            },
        }

        example = evidence_to_review_example(evidence)
        answer = json.loads(example["messages"][2]["content"])

        self.assertEqual(answer["review_status"], "needs_evidence")
        self.assertTrue(answer["must_not_claim_legal_pass"])
        self.assertIn("maas_review", answer["recommended_tools"])

    def test_management_command_exports_seed_without_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            call_command("export_maas_training_data", out_dir=tmp, skip_db=True, verbosity=0)
            path = os.path.join(tmp, "maas_intent_sft_seed.jsonl")

            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                row = json.loads(f.readline())

        self.assertEqual(row["source"], "arr.maas.sequence_library.v0")

    def test_evidence_review_export_filters_non_maas_design_results(self):
        non_maas_job = self._job(algorithm="additive")
        self._design(non_maas_job, 910001, algorithm="additive")
        maas_job = self._job(algorithm="maas_legal_envelope")
        self._design(maas_job, 910002, algorithm="maas_legal_envelope")

        examples = build_examples_from_design_results(limit=10)

        self.assertEqual(len(examples), 1)
        prompt = json.loads(examples[0]["messages"][1]["content"])
        self.assertEqual(prompt["candidate"]["candidate_id"], "910002")

    def test_evidence_review_export_allows_zero_limit(self):
        maas_job = self._job(algorithm="maas_legal_envelope")
        self._design(maas_job, 910003, algorithm="maas_legal_envelope")

        self.assertEqual(build_examples_from_design_results(limit=0), [])


class MaasAestheticImageJobTest(TestCase):
    def _evidence(self):
        return {
            "schema_version": "arr.maas.evidence.v0",
            "bundle_id": "maas-evidence:test-job:maas_01",
            "candidate": {
                "candidate_id": "maas_01",
                "mass_shape": "legal_layered_max",
                "intended_use": {"building_type": "공동주택"},
            },
            "geometry": {
                "mass_geojson": {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [127.0000, 37.0000],
                            [127.0004, 37.0000],
                            [127.0004, 37.0003],
                            [127.0000, 37.0003],
                            [127.0000, 37.0000],
                        ]],
                    },
                    "properties": {},
                },
                "floor_plates": [{"floor": 1, "area_m2": 120.0}],
                "mass_volumes": [{
                    "name": "main",
                    "bottom_height": 0.0,
                    "top_height": 21.0,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [127.0000, 37.0000],
                            [127.0004, 37.0000],
                            [127.0004, 37.0003],
                            [127.0000, 37.0003],
                            [127.0000, 37.0000],
                        ]],
                    },
                }],
                "geometry_metrics": {
                    "height_m": 21.0,
                    "num_floors": 7,
                    "shape_signature_3d": {
                        "volume_count": 1,
                        "floor_plate_count": 7,
                        "height_bands": [21.0],
                    },
                },
            },
            "program": {"building_type": "공동주택"},
        }

    def test_aesthetic_image_job_locks_legal_mass_geometry(self):
        job = build_aesthetic_image_job(self._evidence(), provider="gpt-image", style="brick residential facade")

        self.assertEqual(job["schema_version"], "arr.maas.aesthetic_image_job.v0")
        self.assertEqual(job["source_bundle_id"], "maas-evidence:test-job:maas_01")
        self.assertEqual(job["candidate_id"], "maas_01")
        self.assertEqual(job["mode"], "reference_image_to_image")
        self.assertEqual(job["evidence_policy"]["legal_status_effect"], "none")
        self.assertIn("mass_geojson", job["evidence_policy"]["must_not_change"])
        self.assertTrue(job["prompt"]["constraints"]["lock_silhouette"])
        self.assertEqual(job["prompt"]["constraints"]["lock_height_m"], 21.0)
        self.assertEqual(job["prompt"]["constraints"]["lock_num_floors"], 7)
        self.assertIn("brick residential facade", job["prompt"]["prompt"])
        self.assertEqual(job["reference_render"]["geometry_lock"]["mass_geojson_ref"], "geometry.mass_geojson")
        self.assertEqual(job["reference_render"]["geometry_lock"]["shape_signature_3d"]["floor_plate_count"], 7)
        self.assertEqual(job["locked_geometry"]["geometry_metrics"]["height_m"], 21.0)
        self.assertEqual(job["locked_geometry"]["mass_geojson"]["geometry"]["type"], "Polygon")

        validation = validate_aesthetic_job(job)
        self.assertEqual(validation["status"], "pass")
        self.assertEqual(validation["issues"], [])

    def test_aesthetic_validator_rejects_unanchored_jobs(self):
        job = build_aesthetic_image_job(self._evidence())
        job["source_bundle_id"] = None
        job["prompt"]["constraints"]["lock_silhouette"] = False
        job["evidence_policy"]["legal_status_effect"] = "changes_geometry"

        validation = validate_aesthetic_job(job)

        self.assertEqual(validation["status"], "fail")
        codes = {issue["code"] for issue in validation["issues"]}
        self.assertIn("missing_source_bundle", codes)
        self.assertIn("silhouette_not_locked", codes)
        self.assertIn("legal_status_mutation", codes)

    def test_aesthetic_pipeline_renders_reference_png_and_preserves_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_aesthetic_pipeline_result(
                self._evidence(),
                provider="placeholder",
                renderer=ReferencePngRenderer(tmp),
                attach_to_evidence=True,
            )

            self.assertEqual(result["status"], "needs_provider")
            self.assertEqual(result["job_validation"]["status"], "pass")
            self.assertEqual(result["provider_validation"]["status"], "pass")
            self.assertEqual(result["provider_result"]["status"], "needs_provider")
            self.assertTrue(result["reference"]["uri"].endswith(".png"))
            self.assertIn("sha256", result["reference"]["metadata"])
            self.assertEqual(result["evidence"]["assets"]["aesthetic"][0]["legal_status_effect"], "none")

    def test_multi_view_reference_pack_carries_scene_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_aesthetic_pipeline_result(
                self._evidence(),
                provider="placeholder",
                renderer=MultiViewReferencePackRenderer(tmp),
                attach_to_evidence=True,
            )

            self.assertEqual(result["status"], "needs_provider")
            self.assertTrue(result["reference"]["uri"].endswith(".multi-view.png"))
            metadata = result["reference"]["metadata"]
            self.assertEqual(metadata["reference_type"], "multi_view_pack")
            self.assertEqual(metadata["views"], ["front", "right", "back", "left", "axon", "top"])
            self.assertEqual(metadata["scene_graph"]["schema_version"], "arr.maas.scene_graph.v0")
            self.assertEqual(metadata["condition_pack"]["schema_version"], "arr.maas.condition_pack.v0")
            self.assertTrue(os.path.exists(metadata["condition_pack"]["scene_graph"]["uri"]))
            self.assertTrue(os.path.exists(metadata["condition_pack"]["camera_poses"]["uri"]))
            self.assertTrue(os.path.exists(metadata["condition_pack"]["facade_planes"]["uri"]))
            self.assertTrue(os.path.exists(metadata["condition_pack"]["projection_manifest"]["uri"]))
            self.assertTrue(os.path.exists(metadata["condition_pack"]["views"]["front"]["silhouette"]["uri"]))
            self.assertTrue(os.path.exists(metadata["condition_pack"]["views"]["front"]["depth"]["uri"]))
            self.assertTrue(os.path.exists(metadata["condition_pack"]["views"]["front"]["floor_guides"]["uri"]))
            with open(metadata["condition_pack"]["projection_manifest"]["uri"], encoding="utf-8") as f:
                projection = json.load(f)
            self.assertEqual(projection["schema_version"], "arr.maas.projection_manifest.v0")
            self.assertGreaterEqual(len(projection["surfaces"]), 4)
            first_surface = projection["surfaces"][0]
            self.assertEqual(len(first_surface["vertices_m"]), 4)
            self.assertEqual(len(first_surface["uv"]), 4)
            for uv in first_surface["uv"]:
                self.assertGreaterEqual(uv[0], 0)
                self.assertLessEqual(uv[0], 1)
                self.assertGreaterEqual(uv[1], 0)
                self.assertLessEqual(uv[1], 1)
            self.assertGreater(first_surface["uv"][1][0], first_surface["uv"][0][0])
            self.assertLess(first_surface["uv"][2][1], first_surface["uv"][1][1])
            self.assertIn(first_surface["view"], {"front", "right", "back", "left"})
            node_types = {node["type"] for node in metadata["scene_graph"]["nodes"]}
            self.assertIn("BuildingMass", node_types)
            self.assertIn("Facade", node_types)

    def test_projection_assets_crop_panels_and_bake_texture_atlas(self):
        with tempfile.TemporaryDirectory() as tmp:
            renderer = MultiViewReferencePackRenderer(tmp)
            reference = renderer.render(build_aesthetic_image_job(self._evidence()))
            generated = os.path.join(tmp, "generated.png")
            from PIL import Image, ImageDraw
            image = Image.new("RGB", (1536, 1536), "#f8fafc")
            draw = ImageDraw.Draw(image)
            for color, box in [
                ("#b45309", (19, 19, 505, 758)),
                ("#8a6f55", (524, 19, 1010, 758)),
                ("#4b5563", (1029, 19, 1515, 758)),
                ("#6b5b45", (19, 777, 505, 1516)),
            ]:
                draw.rectangle(box, fill=color)
            image.save(generated)
            provider = ProviderResult(
                provider="test",
                status="complete",
                assets=[{
                    "asset_id": "asset:test:generated",
                    "uri": generated,
                    "media_type": "image/png",
                    "source_bundle_id": "maas-evidence:test-job:maas_01",
                    "candidate_id": "maas_01",
                    "legal_status_effect": "none",
                    "role": "generated_facade_image",
                }],
            )

            with_panels = attach_facade_panel_assets(provider, reference.metadata)
            baked = attach_baked_projection_assets(with_panels, reference.metadata, atlas_size=768)
            textured = attach_textured_mesh_assets(baked)

            roles = [asset["role"] for asset in textured.assets]
            self.assertIn("facade_panel_image", roles)
            self.assertIn("baked_texture_atlas", roles)
            self.assertIn("texture_bake_manifest", roles)
            self.assertIn("textured_mesh_manifest", roles)
            self.assertIn("textured_gltf", roles)
            self.assertEqual(textured.metadata["texture_bake"]["mode"], "deterministic_panel_atlas_bake")
            self.assertEqual(textured.metadata["textured_mesh"]["mode"], "baked_texture_mesh")
            atlas = next(asset for asset in textured.assets if asset["role"] == "baked_texture_atlas")
            manifest = next(asset for asset in textured.assets if asset["role"] == "texture_bake_manifest")
            mesh_manifest = next(asset for asset in textured.assets if asset["role"] == "textured_mesh_manifest")
            gltf_asset = next(asset for asset in textured.assets if asset["role"] == "textured_gltf")
            self.assertTrue(os.path.exists(atlas["uri"]))
            self.assertTrue(os.path.exists(manifest["uri"]))
            self.assertTrue(os.path.exists(mesh_manifest["uri"]))
            self.assertTrue(os.path.exists(gltf_asset["uri"]))
            with open(manifest["uri"], encoding="utf-8") as f:
                bake = json.load(f)
            self.assertEqual(bake["schema_version"], "arr.maas.texture_bake.v0")
            self.assertGreater(bake["surface_count"], 0)
            self.assertEqual(bake["legal_status_effect"], "none")
            with open(mesh_manifest["uri"], encoding="utf-8") as f:
                mesh = json.load(f)
            self.assertEqual(mesh["schema_version"], "arr.maas.textured_mesh.v0")
            self.assertEqual(mesh["legal_status_effect"], "none")
            self.assertGreater(len(mesh["mesh"]["positions_m"]), 0)
            self.assertGreater(len(mesh["mesh"]["indices"]), 0)
            self.assertGreater(len(mesh["mesh"]["surface_ranges"]), 0)
            with open(gltf_asset["uri"], encoding="utf-8") as f:
                gltf = json.load(f)
            self.assertEqual(gltf["asset"]["version"], "2.0")
            self.assertEqual(gltf["images"][0]["uri"], "baked_texture_atlas.png")
            self.assertGreater(gltf["accessors"][2]["count"], 0)

    def test_openai_and_nano_banana_adapters_are_safe_without_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            renderer = ReferencePngRenderer(tmp)
            env = {
                key: value
                for key, value in os.environ.items()
                if key not in {
                    "OPENAI_API_KEY",
                    "GEMINI_API_KEY",
                    "GOOGLE_API_KEY",
                    "NANO_BANANA_ENDPOINT",
                    "NANO_BANANA_API_KEY",
                }
            }
            with patch.dict(os.environ, env, clear=True):
                for provider in ("gpt-image", "nano-banana"):
                    result = build_aesthetic_pipeline_result(
                        self._evidence(),
                        provider=provider,
                        renderer=renderer,
                    )
                    self.assertEqual(result["status"], "needs_provider")
                    self.assertIn(result["provider_result"]["status"], {"not_configured", "needs_provider"})
                    self.assertEqual(result["provider_validation"]["status"], "pass")

    def test_aesthetic_endpoint_builds_reference_png_from_evidence(self):
        job = OptimizationJob.objects.create(
            pnu="1168011800104170004",
            address="",
            site_polygon={
                "type": "Polygon",
                "coordinates": [[
                    [127.0000, 37.0000],
                    [127.0010, 37.0000],
                    [127.0010, 37.0010],
                    [127.0000, 37.0010],
                    [127.0000, 37.0000],
                ]],
            },
            site_area_m2=264.1,
            job_spec={"options": {"building_type": "공동주택", "algorithm": "maas_legal_envelope"}},
            constraints=[],
            status="complete",
        )
        DesignResult.objects.create(
            job=job,
            generation=0,
            design_id=900010,
            inputs=[],
            outputs={},
            ranking=1.0,
            is_feasible=True,
            is_pareto_optimal=True,
            mass_geojson={
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [127.0000, 37.0000],
                        [127.0004, 37.0000],
                        [127.0004, 37.0003],
                        [127.0000, 37.0003],
                        [127.0000, 37.0000],
                    ]],
                },
                "properties": {
                    "algorithm": "maas_legal_envelope",
                    "variant_id": "maas_01",
                    "mass_shape": "legal_layered_max",
                    "height": 16.8,
                    "num_floors": 6,
                    "bcr": 39.0,
                    "far": 175.5,
                    "floor_area": 463.0,
                },
            },
        )

        response = self.client.post(
            f"/design/jobs/{job.id}/results/900010/aesthetic/",
            data={"provider": "placeholder", "style": "brick residential facade"},
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "needs_provider")
        self.assertEqual(data["job"]["evidence_policy"]["legal_status_effect"], "none")
        self.assertEqual(data["reference"]["media_type"], "image/png")
        self.assertTrue(data["reference"]["url"].startswith("/design/maas/aesthetic-assets/references/"))
        self.assertEqual(data["reference"]["metadata"]["reference_type"], "multi_view_pack")
        self.assertEqual(data["reference"]["metadata"]["scene_graph"]["schema_version"], "arr.maas.scene_graph.v0")
        pack = data["reference"]["metadata"]["condition_pack"]
        self.assertEqual(pack["schema_version"], "arr.maas.condition_pack.v0")
        self.assertTrue(pack["scene_graph"]["url"].startswith("/design/maas/aesthetic-assets/references/"))
        self.assertTrue(pack["projection_manifest"]["url"].startswith("/design/maas/aesthetic-assets/references/"))
        self.assertTrue(pack["views"]["front"]["silhouette"]["url"].endswith("/silhouette/front.png"))
        self.assertTrue(pack["views"]["front"]["depth"]["url"].endswith("/depth/front.png"))
        self.assertTrue(pack["views"]["front"]["floor_guides"]["url"].endswith("/floor_guides/front.png"))
        self.assertEqual(data["provider_result"]["provider"], "placeholder")
        self.assertEqual(data["evidence"]["assets"]["aesthetic"][0]["legal_status_effect"], "none")
