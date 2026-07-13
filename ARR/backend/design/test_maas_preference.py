"""Tests for MAAS second-stage preference distillation."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from design.maas.preference.candidate_crops import crop_candidate_images
from design.maas.llm_proposals import _prompt, _stable_hash
from design.maas.preference import build_preference_distillation, build_vlm_generation_feedback, rerank_candidates
from design.maas.preference.harness import export_generation_feedback, run_preference_harness
from design.maas.preference.pairwise_store import PairwisePreference, append_pairwise_label, load_pairwise_labels, pairwise_win_counts
from design.maas.preference.quality_audit import audit_preference_output
from design.maas.preference.reference_corpus import (
    ReferenceItem,
    archdaily_api_collection_dir,
    load_reference_tree,
    match_reference_context,
    write_reference_items,
)
from design.maas.preference.loop import (
    PreferenceLoopCallbacks,
    apply_preference_loop,
    preference_loop_config,
    preference_vlm_scored,
)
from design.maas.selection.preference_guards import (
    PreferenceGuardCallbacks,
    clean_mass_failures,
    enforce_final_vlm_preference_minimum,
)
from design.maas.legal_mesh_optimizer import (
    _architectural_order_gate,
    _design_review_quality_key,
    _formal_principle,
    _has_review_source_geometry,
    _is_direct_openai_llm_candidate,
    _is_plain_capacity_anchor,
    _is_reviewable_architectural_mass,
    _research_mass_language,
    _source_family,
)
from design.maas.selection import final_mass_stage_parking_pass
from design.maas.evolution.critic_loop import run_critic_geometry_loop
from design.maas.grammar.component_graph import MassComponentGraph, MassComponentNode, graph_from_sequence
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.morphology_operators import MorphologyVariant
from design.maas.source_geometry.coherence import evaluate_source_volume_coherence
from design.maas.source_geometry.compiler import compile_component_graph_to_source_mass, compile_sequence_to_source_mass
from design.maas.source_geometry.ir import SourceVolume
from shapely.geometry import box


class MaasPreferenceDistillationTest(TestCase):
    def test_component_graph_makes_mass_hierarchy_explicit(self):
        sequence = VerbSequence("graph", "graph", (
            VerbCall("base", {}),
            VerbCall("bar", {"factor": 0.72}),
            VerbCall("courtyard", {"ratio": 0.22}),
            VerbCall("bridge", {"axis": "x"}),
        ))
        graph = graph_from_sequence(sequence)

        self.assertEqual(graph.validate(), [])
        self.assertEqual([node.role for node in graph.nodes], ["root", "primary", "void", "connector"])
        self.assertEqual(graph.nodes[2].parent_id, graph.nodes[1].node_id)
        self.assertEqual(graph.to_dict()["schema_version"], "arr.maas.component_graph.v1")

    def test_coherence_objective_rejects_redundant_overlapping_solids(self):
        footprint = box(0, 0, 10, 10)
        volumes = tuple(
            SourceVolume(f"secondary_helper_{index}", footprint, 0.0, 1.0, "overlap")
            for index in range(4)
        )

        evidence = evaluate_source_volume_coherence(volumes)

        self.assertFalse(evidence["hard_pass"])
        self.assertGreater(evidence["redundant_overlap_pair_count"], 1)
        self.assertLess(evidence["score"], 0.62)

    def test_graph_parent_relation_changes_compiled_geometry(self):
        root = MassComponentNode("root", "root", VerbCall("base", {}))
        primary = MassComponentNode(
            "primary_bar", "primary", VerbCall("bar", {"axis": "x", "factor": 0.52}), "root"
        )
        notch_on_primary = MassComponentNode(
            "void_notch", "void", VerbCall("notch", {"corner": "+x+y", "ratio": 0.28}), "primary_bar"
        )
        notch_on_root = MassComponentNode(
            "void_notch", "void", VerbCall("notch", {"corner": "+x+y", "ratio": 0.28}), "root"
        )
        child_graph = MassComponentGraph("child", "child", (root, primary, notch_on_primary))
        root_graph = MassComponentGraph("root_target", "root target", (root, primary, notch_on_root))

        child_mass = compile_component_graph_to_source_mass(box(0, 0, 20, 12), child_graph)
        root_mass = compile_component_graph_to_source_mass(box(0, 0, 20, 12), root_graph)

        self.assertIsNotNone(child_mass)
        self.assertIsNotNone(root_mass)
        self.assertNotAlmostEqual(child_mass.footprint.area, root_mass.footprint.area)
        self.assertNotEqual(child_mass.metadata["family"], root_mass.metadata["family"])

    def test_executable_family_prevents_false_folded_principle_collapse(self):
        sequence = VerbSequence(
            "llm_branch_declared_folded",
            "branch",
            (VerbCall("base", {}), VerbCall("branch", {"angle": 34.0, "trunk_ratio": 0.3, "arm_ratio": 0.2})),
            ("formal_principle=folded_section",),
        )

        mass = compile_sequence_to_source_mass(box(0, 0, 20, 12), sequence)

        self.assertIsNotNone(mass)
        self.assertEqual(mass.metadata["family"], "branch")
        self.assertEqual(mass.metadata["formal_principle"], "torqued_stack")

    def _feature(self, variant_id="maas_01", family="courtyard", score=0.7):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [127.0, 37.0],
                    [127.0001, 37.0],
                    [127.0001, 37.0001],
                    [127.0, 37.0001],
                    [127.0, 37.0],
                ]],
            },
            "properties": {
                "variant_id": variant_id,
                "mass_shape": f"llm_{family}",
                "operator_family": family,
                "far": 35.0,
                "bcr": 25.0,
                "height": 8.4,
                "far_utilization": 0.72,
                "bcr_utilization": 0.45,
                "diversity_score": 0.5,
                "geometry_resolution": {"status": "source_geometry_used"},
                "mass_volumes": [
                    {
                        "bottom_height": 0.0,
                        "top_height": 2.8,
                        "role": "base",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.0, 37.0],
                                [127.0001, 37.0],
                                [127.0001, 37.0001],
                                [127.0, 37.0001],
                                [127.0, 37.0],
                            ]],
                        },
                    },
                    {
                        "bottom_height": 2.8,
                        "top_height": 5.6,
                        "role": "body",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.00002, 37.00001],
                                [127.0001, 37.00001],
                                [127.00009, 37.00009],
                                [127.00002, 37.00009],
                                [127.00002, 37.00001],
                            ]],
                        },
                    },
                    {
                        "bottom_height": 5.6,
                        "top_height": 8.4,
                        "role": "top",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.00003, 37.00002],
                                [127.00009, 37.00002],
                                [127.00008, 37.00008],
                                [127.00003, 37.00008],
                                [127.00003, 37.00002],
                            ]],
                        },
                    },
                ],
                "source_signature": {
                    "family": family,
                    "formal_principle": "carved_atrium" if family == "courtyard" else "split_bridge_connector",
                    "primary_language": family,
                    "secondary_language": "void",
                    "surface_count": 24,
                    "volume_count": 4,
                    "rule_evidence": {"generator_mode": "subtractive"},
                },
                "visual_diversity_evidence": {
                    "mass_language": family,
                    "volume_count": 4,
                    "hole_count": 1 if family == "courtyard" else 0,
                },
                "orderliness_evidence": {
                    "schema_version": "arr.maas.orderliness.v1",
                    "orderliness_score": score,
                    "main_mass_area_ratio": 0.55,
                },
                "architectural_ambition_evidence": {
                    "schema_version": "arr.maas.architectural_ambition.v1",
                    "architecture_grade_pass": True,
                    "formal_principle": "carved_atrium" if family == "courtyard" else "split_bridge_connector",
                    "dominant_gesture": "void-defined mass",
                    "silhouette_strength": 0.78,
                    "sectional_diagram_clarity": 0.75,
                },
                "repair_delta": {
                    "schema_version": "arr.maas.repair_delta.v1",
                    "area_retention": 0.94,
                    "scope": "legal_footprint",
                },
                "parking_precheck": {
                    "layout_candidate": {
                        "status": "needs_mechanical_parking_review",
                        "mass_stage_parking": {"status": "pass"},
                    }
                },
            },
        }

    def _loop_callbacks(self):
        return PreferenceLoopCallbacks(
            design_review_quality_key=_design_review_quality_key,
            final_mass_stage_parking_pass=final_mass_stage_parking_pass,
            has_review_source_geometry=_has_review_source_geometry,
            is_plain_capacity_anchor=_is_plain_capacity_anchor,
            is_reviewable_architectural_mass=_is_reviewable_architectural_mass,
            source_family=_source_family,
        )

    def _guard_callbacks(self):
        return PreferenceGuardCallbacks(
            architectural_order_gate=_architectural_order_gate,
            design_review_quality_key=_design_review_quality_key,
            final_mass_stage_parking_pass=final_mass_stage_parking_pass,
            formal_principle=_formal_principle,
            has_review_source_geometry=_has_review_source_geometry,
            is_direct_openai_llm_candidate=_is_direct_openai_llm_candidate,
            is_plain_capacity_anchor=_is_plain_capacity_anchor,
            is_reviewable_architectural_mass=_is_reviewable_architectural_mass,
            preference_vlm_scored=preference_vlm_scored,
            research_mass_language=_research_mass_language,
            source_family=_source_family,
        )

    def test_build_preference_distillation_preserves_hard_gates(self):
        evidence = build_preference_distillation(self._feature())

        self.assertEqual(evidence["schema_version"], "arr.maas.preference_distill.v1")
        self.assertEqual(evidence["mode"], "vlm_ready_geometry_proxy")
        self.assertTrue(evidence["hard_gates"]["legal_gate_preserved"])
        self.assertTrue(evidence["hard_gates"]["parking_mass_stage_gate_preserved"])
        self.assertEqual(len(evidence["concept_scores"]), 6)

    def test_same_run_critic_loop_mutates_rescores_and_accepts_improvement(self):
        parent = self._feature(variant_id="parent")
        parent["properties"]["mass_shape"] = "llm_parent"
        parent["properties"]["maas_verb_sequence"] = [
            {"verb": "base", "params": {}},
            {"verb": "overlap", "params": {"slab_ratio": 0.4}},
            {"verb": "terrace_link", "params": {"upper_ratio": 0.8}},
            {"verb": "shift", "params": {"distance_ratio": 0.1}},
        ]
        parent["properties"]["preference_distillation"] = {
            "mode": "vlm_scored",
            "vlm_status": "scored",
            "critic_actions": ["too_fragmented"],
        }
        parent["properties"]["critic_test_score"] = 1

        def interpret(_base, sequence):
            return MorphologyVariant(
                operator=sequence.name,
                footprint=box(0, 0, 10, 10),
                notes=sequence.notes,
                verb_sequence=tuple(sequence.to_list()),
            )

        def evaluate(variant):
            return {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "mass_shape": variant.operator,
                    "critic_test_score": 0,
                    "maas_verb_sequence": list(variant.verb_sequence),
                },
            }

        def rescore(children):
            for child in children:
                child["properties"]["critic_test_score"] = 2

        result = run_critic_geometry_loop(
            base_footprint=box(0, 0, 10, 10),
            scored_features=[parent],
            interpret=interpret,
            evaluate=evaluate,
            rescore=rescore,
            quality_key=lambda feature: (float(feature["properties"].get("critic_test_score") or 0),),
            max_generations=1,
        )

        self.assertEqual(len(result.accepted), 1)
        self.assertEqual(result.trace["accepted_child_count"], 1)
        self.assertEqual(result.trace["status"], "accepted_revisions")
        self.assertEqual(
            result.accepted[0]["properties"]["critic_revision_evidence"]["critic_actions"],
            ["too_fragmented"],
        )

    def test_clean_mass_gate_rejects_surface_and_volume_fragmentation(self):
        feature = self._feature()
        feature["properties"]["architectural_ambition_evidence"]["implemented_volume_roles"] = [
            "primary", "secondary", "support",
        ]
        feature["properties"]["source_signature"]["surface_count"] = 37
        feature["properties"]["mass_volumes"] *= 2

        passed, issues = _architectural_order_gate(feature)
        failures = clean_mass_failures(feature)

        self.assertFalse(passed)
        self.assertIn("over_complex_source_surfaces", issues)
        self.assertIn("too_many_visible_volumes", issues)
        self.assertEqual(failures["surface_over"], 1)
        self.assertEqual(failures["volume_over"], 1)

    def test_clean_mass_quality_key_beats_vlm_scored_fragmented_mass(self):
        clean = self._feature(variant_id="clean")
        noisy = self._feature(variant_id="noisy")
        for feature in (clean, noisy):
            feature["properties"]["architectural_ambition_evidence"]["implemented_volume_roles"] = [
                "primary", "secondary", "support",
            ]
        noisy["properties"]["source_signature"]["surface_count"] = 68
        noisy["properties"]["mass_volumes"] *= 2
        noisy["properties"]["preference_distillation"] = {
            "mode": "vlm_scored", "vlm_status": "scored", "aggregate_score": 0.99,
        }

        self.assertGreater(_design_review_quality_key(clean), _design_review_quality_key(noisy))

    def test_reference_matching_uses_architectural_tags(self):
        feature = self._feature(family="courtyard")
        refs = [
            ReferenceItem(source="hf", source_id="1", title="Courtyard atrium building", tags=("courtyard", "atrium")),
            ReferenceItem(source="hf", source_id="2", title="highway bridge", tags=("infrastructure",)),
        ]

        matches = match_reference_context(feature, refs)

        self.assertEqual(matches[0]["source_id"], "1")
        self.assertIn("courtyard", matches[0]["matched_tags"])

    def test_reference_signal_changes_precedent_score(self):
        feature = self._feature(family="courtyard")
        without_refs = build_preference_distillation(feature)
        with_refs = build_preference_distillation(feature, reference_matches=[
            {
                "source": "archdaily_api",
                "source_id": "archdaily_1",
                "title": "Courtyard precedent",
                "score": 2,
                "local_path": "reference.jpg",
            }
        ])

        self.assertGreater(
            with_refs["concept_scores"]["precedent_resonance"],
            without_refs["concept_scores"]["precedent_resonance"],
        )
        self.assertGreater(with_refs["distilled_preference_score"], without_refs["distilled_preference_score"])
        self.assertEqual(with_refs["reference_signal"]["matched_reference_count"], 1)

    def test_pairwise_wins_adjust_reranking(self):
        first = self._feature("maas_01", "courtyard", 0.7)
        second = self._feature("maas_02", "split", 0.7)
        first["properties"]["preference_distillation"] = build_preference_distillation(first)
        second["properties"]["preference_distillation"] = build_preference_distillation(second)

        ranked = rerank_candidates([first, second], pairwise_wins={"maas_02": 3}, diversity_reserve=0)

        self.assertEqual(ranked[0]["properties"]["variant_id"], "maas_02")
        self.assertEqual(ranked[0]["properties"]["preference_rerank"]["rank"], 1)

    def test_preference_loop_scores_top_k_and_changes_quality_key(self):
        first = self._feature("maas_01", "courtyard", 0.7)
        second = self._feature("maas_02", "split", 0.7)

        def fake_scorer(**kwargs):
            feature = kwargs["feature"]
            variant_id = feature["properties"]["variant_id"]
            high = variant_id == "maas_02"
            score = 0.95 if high else 0.45
            return {
                "schema_version": "arr.maas.vlm_concept_scores.v1",
                "model": "fake-vlm",
                "concept_scores": {
                    "gesture_clarity": score,
                    "hierarchy": score,
                    "non_stair_silhouette": score,
                    "void_publicness": score,
                    "repair_integrity": score,
                    "precedent_resonance": score,
                },
            }

        artifact = apply_preference_loop(
            [first, second],
            config={
                "enabled": True,
                "require_vlm": True,
                "top_k": 2,
                "parallel_workers": 2,
                "model": "fake-vlm",
                "reference_root": "",
            },
            callbacks=self._loop_callbacks(),
            scorer=fake_scorer,
        )

        self.assertEqual(artifact["vlm_scored_count"], 2)
        self.assertEqual(artifact["parallel_workers"], 2)
        self.assertTrue(preference_vlm_scored(second))
        self.assertGreater(_design_review_quality_key(second), _design_review_quality_key(first))
        self.assertEqual(second["properties"]["preference_distillation"]["mode"], "vlm_scored")

    def test_final_vlm_preference_minimum_replaces_proxy_candidate(self):
        proxy = self._feature("maas_01", "courtyard", 0.7)
        scored = self._feature("maas_02", "split", 0.7)
        proxy["properties"]["mass_shape"] = "proxy_courtyard"
        scored["properties"]["mass_shape"] = "vlm_split"
        scored["properties"]["orderliness_evidence"]["orderliness_score"] = 0.92
        scored["properties"]["architectural_ambition_evidence"]["implemented_volume_roles"] = ["base", "body", "top"]
        scored["properties"]["preference_distillation"] = build_preference_distillation(
            scored,
            vlm_model="fake-vlm",
            vlm_scores={
                "gesture_clarity": 0.9,
                "hierarchy": 0.9,
                "non_stair_silhouette": 0.9,
                "void_publicness": 0.9,
                "repair_integrity": 0.9,
                "precedent_resonance": 0.9,
            },
            vlm_status="scored",
        )

        selected = enforce_final_vlm_preference_minimum(
            [proxy],
            source_pool=[proxy, scored],
            final_limit=1,
            min_count=1,
            callbacks=self._guard_callbacks(),
        )

        self.assertEqual(selected[0]["properties"]["mass_shape"], "vlm_split")
        self.assertTrue(preference_vlm_scored(selected[0]))

    def test_preference_loop_require_vlm_rejects_silent_proxy(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                apply_preference_loop(
                    [self._feature()],
                    config={
                        "enabled": True,
                        "require_vlm": True,
                        "top_k": 1,
                        "model": "fake-vlm",
                        "reference_root": "",
                    },
                    callbacks=self._loop_callbacks(),
                    scorer=None,
                )

    def test_preference_loop_config_defaults_to_top_40(self):
        config = preference_loop_config({"maas_preference_loop": {"enabled": True, "require_vlm": True}})

        self.assertTrue(config["enabled"])
        self.assertEqual(config["top_k"], 40)
        self.assertEqual(config["parallel_workers"], 4)
        self.assertEqual(config["min_final_vlm_scored"], 16)

    def test_harness_merges_reference_and_preference_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            reference_root = root / "reference-corpus"
            refs_path = reference_root / "huggingface" / "metadata.jsonl"
            write_reference_items(refs_path, [
                ReferenceItem(source="hf", source_id="1", title="Courtyard architecture", tags=("courtyard", "atrium")),
            ])
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")

            summary = run_preference_harness(
                input_json=input_json,
                output_json=output_json,
                reference_root=reference_root,
                use_vlm=False,
            )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            props = output["response"]["feature_collection"]["features"][0]["properties"]

        self.assertEqual(summary["reference_count"], 1)
        self.assertEqual(props["preference_distillation"]["schema_version"], "arr.maas.preference_distill.v1")
        self.assertEqual(props["preference_distillation"]["reference_matches"][0]["source_id"], "1")
        self.assertEqual(props["paper_alignment_evidence"]["schema_version"], "arr.maas.paper_alignment.v1")

    def test_harness_loads_structured_archdaily_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            reference_root = root / "reference-corpus"
            collection_dir = archdaily_api_collection_dir(
                reference_root,
                start_path="/projects/categories/houses",
                collection_name="houses_smoke",
            )
            write_reference_items(collection_dir / "metadata.jsonl", [
                ReferenceItem(
                    source="archdaily_api",
                    source_id="archdaily_1",
                    title="Courtyard house precedent",
                    local_path=str(collection_dir / "images" / "archdaily_1.jpg"),
                    tags=("courtyard", "house"),
                ),
            ])
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")

            summary = run_preference_harness(
                input_json=input_json,
                output_json=output_json,
                reference_root=reference_root,
                use_vlm=False,
            )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            matches = output["response"]["feature_collection"]["features"][0]["properties"]["preference_distillation"]["reference_matches"]
            audit = output["response"]["preference_quality_audit"]
            reference_count = len(load_reference_tree(reference_root))

        self.assertEqual(reference_count, 1)
        self.assertEqual(summary["reference_count"], 1)
        self.assertEqual(matches[0]["source"], "archdaily_api")
        self.assertEqual(audit["schema_version"], "arr.maas.preference_quality_audit.v1")

    def test_pairwise_jsonl_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.jsonl"
            append_pairwise_label(path, PairwisePreference(
                preferred_candidate_id="maas_02",
                rejected_candidate_id="maas_01",
                reviewer_id="professor",
            ))
            labels = load_pairwise_labels(path)

        self.assertEqual(len(labels), 1)
        self.assertEqual(pairwise_win_counts(labels, reviewer_id="professor"), {"maas_02": 1})

    def test_harness_records_vlm_failure_as_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            image_path = root / "candidate.png"
            image_path.write_bytes(b"not-a-real-png")
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")
            with patch("design.maas.preference.harness.score_candidate_with_openai_vlm", side_effect=Exception("boom")):
                run_preference_harness(
                    input_json=input_json,
                    output_json=output_json,
                    image_path=image_path,
                    reference_root=root / "reference-corpus",
                    use_vlm=True,
                )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            evidence = output["response"]["feature_collection"]["features"][0]["properties"]["preference_distillation"]

        self.assertEqual(evidence["mode"], "geometry_proxy_fallback")
        self.assertEqual(evidence["vlm_status"], "failed")

    def test_harness_sends_candidate_crop_to_vlm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            image_path = root / "sheet.png"
            crop_dir = root / "crops"
            from PIL import Image

            Image.new("RGB", (900, 420), "#ffffff").save(image_path)
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature("maas_01"), self._feature("maas_02", "split")],
                    }
                }
            }), encoding="utf-8")
            seen_paths = []

            def fake_vlm(**kwargs):
                seen_paths.append(Path(kwargs["image_path"]).name)
                return {
                    "schema_version": "arr.maas.vlm_concept_scores.v1",
                    "model": "fake-vlm",
                    "concept_scores": {
                        "gesture_clarity": 0.8,
                        "hierarchy": 0.8,
                        "non_stair_silhouette": 0.8,
                        "void_publicness": 0.8,
                        "repair_integrity": 0.8,
                        "precedent_resonance": 0.8,
                    },
                }

            with patch("design.maas.preference.harness.score_candidate_with_openai_vlm", side_effect=fake_vlm):
                run_preference_harness(
                    input_json=input_json,
                    output_json=output_json,
                    image_path=image_path,
                    reference_root=root / "reference-corpus",
                    use_vlm=True,
                    candidate_crop_dir=crop_dir,
                )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            by_id = {
                feature["properties"]["variant_id"]: feature["properties"]["preference_distillation"]
                for feature in output["response"]["feature_collection"]["features"]
            }

        self.assertEqual(seen_paths, ["maas_01.png", "maas_02.png"])
        self.assertEqual(by_id["maas_01"]["mode"], "vlm_scored")
        self.assertIn("maas_01.png", by_id["maas_01"]["image_uri"])

    def test_vlm_generation_feedback_extracts_next_generation_brief(self):
        top = self._feature("maas_01", "diagonal_connect", 0.9)
        bottom = self._feature("maas_02", "legal_layered", 0.6)
        top["properties"]["preference_distillation"] = build_preference_distillation(
            top,
            vlm_model="fake-vlm",
            vlm_scores={
                "gesture_clarity": 0.9,
                "hierarchy": 0.85,
                "non_stair_silhouette": 0.85,
                "void_publicness": 0.8,
                "repair_integrity": 0.9,
                "precedent_resonance": 0.9,
            },
            vlm_status="scored",
        )
        bottom["properties"]["mass_shape"] = "legal_layered_max"
        bottom["properties"]["preference_distillation"] = build_preference_distillation(
            bottom,
            vlm_model="fake-vlm",
            vlm_scores={
                "gesture_clarity": 0.6,
                "hierarchy": 0.6,
                "non_stair_silhouette": 0.3,
                "void_publicness": 0.2,
                "repair_integrity": 0.8,
                "precedent_resonance": 0.4,
            },
            vlm_status="scored",
        )
        payload = {
            "feature_collection": {"features": [top, bottom]},
            "preference_quality_audit": {"top_reference_delta_saturated_count": 2, "reference_delta_unique_count": 1},
        }

        feedback = build_vlm_generation_feedback(payload, top_n=1, bottom_n=1)

        self.assertEqual(feedback["schema_version"], "arr.maas.vlm_generation_feedback.v1")
        self.assertIn("diagonal", feedback["must_use"])
        self.assertIn("legal_layered_max", feedback["avoid"])
        self.assertIn("formal_principle_targets", feedback)

    def test_harness_requires_real_vlm_for_feedback_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")

            with self.assertRaises(RuntimeError):
                run_preference_harness(
                    input_json=input_json,
                    output_json=output_json,
                    reference_root=root / "reference-corpus",
                    use_vlm=False,
                    require_vlm_feedback=True,
                )

    def test_feedback_only_exports_without_rewriting_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            feedback_json = root / "feedback.json"
            feature = self._feature("maas_01", "diagonal_connect", 0.9)
            feature["properties"]["preference_distillation"] = build_preference_distillation(
                feature,
                vlm_model="fake-vlm",
                vlm_scores={
                    "gesture_clarity": 0.9,
                    "hierarchy": 0.85,
                    "non_stair_silhouette": 0.85,
                    "void_publicness": 0.8,
                    "repair_integrity": 0.9,
                    "precedent_resonance": 0.9,
                },
                vlm_status="scored",
            )
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [feature],
                    }
                }
            }), encoding="utf-8")

            feedback = export_generation_feedback(
                input_json=input_json,
                feedback_json=feedback_json,
                require_vlm_feedback=True,
            )
            after = json.loads(input_json.read_text(encoding="utf-8"))
            feedback_exists = feedback_json.exists()

        self.assertEqual(feedback["vlm_scored_count"], 1)
        self.assertTrue(feedback_exists)
        self.assertEqual(
            after["response"]["feature_collection"]["features"][0]["properties"]["preference_distillation"]["mode"],
            "vlm_scored",
        )

    def test_generation_feedback_changes_llm_prompt_hash(self):
        site_context = {"building_type": "공동주택", "site_area_m2": 100.0, "limits": {"far": 200}}
        feedback = {
            "schema_version": "arr.maas.vlm_generation_feedback.v1",
            "must_use": ["diagonal", "undercut"],
            "avoid": ["legal_layered_max"],
            "quota": {"diagonal_or_split_bridge": 4},
            "formal_principle_targets": ["undercut_tapered_tower"],
        }

        base_hash = _stable_hash(_prompt(site_context, 3, batch_index=1))
        feedback_hash = _stable_hash(_prompt(site_context, 3, batch_index=1, generation_feedback=feedback))

        self.assertNotEqual(base_hash, feedback_hash)

    def test_preference_quality_audit_flags_missing_reference_signal(self):
        feature = self._feature()
        feature["properties"]["preference_distillation"] = build_preference_distillation(feature)
        payload = {"feature_collection": {"features": [feature for _ in range(10)]}}

        audit = audit_preference_output(payload)

        self.assertEqual(audit["status"], "fail")
        self.assertIn("top_reference_coverage_too_low", audit["failures"])
