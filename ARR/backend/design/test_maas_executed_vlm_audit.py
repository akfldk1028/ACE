from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.geometry_language.executed_vlm_audit import _compact_audit_record
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.geometry_language.execution_evidence import passport_state, stage, vlm_evidence
from design.maas.geometry_language.vlm_adapter import retrieve_geometry_reference_matches
from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.preference.reference_paths import reference_image_preview_url


class ExecutedMassVlmAuditTests(SimpleTestCase):
    def _audit(self):
        return {
            "model": "test-vlm",
            "response_id": "response-7",
            "program_fit_hard_pass": False,
            "concept_scores": {"gesture_clarity": 0.6, "hierarchy": 0.4},
            "critic_actions": ["too_fragmented"],
            "vlm_image_inputs": {
                "candidate": {
                    "sha256": "candidate-sha",
                    "used_by_vlm": True,
                },
                "references": [
                    {
                        "source_id": "archdaily_7",
                        "title": "Reference seven",
                        "sha256": "reference-sha",
                        "input_order": 1,
                        "used_by_vlm": True,
                    },
                    {
                        "source_id": "retrieved_only",
                        "used_by_vlm": False,
                    },
                ],
            },
        }

    def test_compact_record_derives_mean_without_inventing_pass(self):
        record = _compact_audit_record({"index": 7, "audit": self._audit()})
        self.assertEqual(record["critic_score"], 0.5)
        self.assertFalse(record["hard_pass"])

    def test_passport_vlm_evidence_exposes_failure_actions(self):
        evidence = vlm_evidence(self._audit())
        self.assertFalse(evidence["program_fit_hard_pass"])
        self.assertFalse(evidence["hard_pass"])
        self.assertEqual(evidence["critic_actions"], ["too_fragmented"])

    def test_completed_vlm_with_explicit_hard_failure_rejects_mass(self):
        stages = [
            stage(stage_id, stage_id, "passed")
            for stage_id in (
                "base_model", "recursive_geometry", "program", "site", "capacity",
                "law", "parking", "program_fit", "compiler", "geometry_gate",
                "render", "selector",
            )
        ]
        stages.append(stage(
            "vlm",
            "VLM critic",
            "live_scored",
            evidence={"hard_pass": False, "program_fit_hard_pass": False},
        ))

        state = passport_state(stages)

        self.assertTrue(state["full_flow_complete"])
        self.assertFalse(state["final_hard_pass"])
        self.assertEqual(state["status"], "rejected")

    def test_reference_limit_is_exact_even_when_explicit_matches_are_supplied(self):
        builder = GeometryProgramBuilder("bounded-reference-test")
        root = builder.add("primitive", "box", parameters={"width": 4, "depth": 3, "height": 2})
        program = builder.build(root)
        with TemporaryDirectory() as directory:
            reference_root = Path(directory)
            first = reference_root / "first.jpg"
            second = reference_root / "second.jpg"
            first.write_bytes(b"first")
            second.write_bytes(b"second")

            matches = retrieve_geometry_reference_matches(
                program,
                building_type="generic",
                explicit_matches=[
                    {"source": "test", "source_id": "first", "local_path": str(first)},
                    {"source": "test", "source_id": "second", "local_path": str(second)},
                ],
                reference_root=reference_root,
                limit=1,
            )

        self.assertEqual(len(matches), 1)

    def test_outcome_graph_connects_only_material_vlm_inputs(self):
        with TemporaryDirectory() as directory:
            graph = GeometryOutcomeGraph(Path(directory) / "graph.json", "pnu")
            graph.observe_executed_mass_vlm_audit(
                program_slug="neighborhood",
                source_seed="seed-7",
                program_hash="program-7",
                geometry_hash="geometry-7",
                preview_path="mass-07.png",
                audit=self._audit(),
            )
            reference_nodes = [
                node for node in graph.nodes.values()
                if node["kind"] == "reference"
            ]
            self.assertEqual([node["identity"] for node in reference_nodes], ["archdaily_7"])
            self.assertTrue(any(edge["kind"] == "visual_input_to" for edge in graph.edges.values()))
            observation = next(row for row in graph.observations if row["stage"] == "executed_mass_vlm")
            self.assertEqual(observation["critic_score"], 0.5)
            self.assertEqual(observation["reference_ids"], ["archdaily_7"])

    def test_local_reference_preview_is_same_origin(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "docs" / "ai-session-memory" / "reference-corpus" / "archdaily" / "reference.jpg"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"reference")
            self.assertEqual(
                reference_image_preview_url(str(path), root=root),
                "/design/maas/reference-assets/archdaily/reference.jpg",
            )
