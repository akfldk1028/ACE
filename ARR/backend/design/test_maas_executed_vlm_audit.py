from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.geometry_language.executed_vlm_audit import _compact_audit_record
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.geometry_language.execution_evidence import vlm_evidence
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
