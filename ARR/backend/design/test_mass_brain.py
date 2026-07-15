from __future__ import annotations

from unittest.mock import Mock, patch

import httpx
from django.test import SimpleTestCase
from shapely.geometry import box, mapping

from design.maas.mass_brain import _parameter_schema_for_verb, record_proposal_feedback, record_shadow_outcomes, request_shadow_variants, sync_book_language_corpus
from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.mass_brain_relation_profile import relation_profile_from_feature
from design.maas.historical_memory import build_historical_envelope
from design.maas.preference.reference_corpus import ReferenceItem
from design.maas.morphology_operators import MorphologyVariant


def _variant(name: str, second: str, third: str) -> MorphologyVariant:
    return MorphologyVariant(
        operator=name,
        footprint=box(0, 0, 20, 20),
        verb_sequence=(
            {"verb": "base", "params": {}},
            {"verb": second, "params": {"factor": 0.7}},
            {"verb": third, "params": {"ratio": 0.3}},
        ),
    )


def _response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


class MassBrainBridgeTest(SimpleTestCase):
    @patch("design.maas.mass_brain.config.mass_brain_client")
    def test_book_corpus_sync_preserves_page_and_principle_counts(self, client):
        client.post.return_value = _response({
            "corpusId": "architect-book-69",
            "pageCount": 69,
            "baseOperativeCount": 30,
            "principleCount": 59,
        })

        result = sync_book_language_corpus()

        self.assertEqual(result["status"], "synced")
        payload = client.post.call_args.kwargs["json"]
        self.assertEqual(payload["page_count"], 69)
        self.assertEqual(payload["base_operative_count"], 30)
        self.assertEqual(len(payload["principles"]), 59)
        self.assertEqual(len(payload["case_studies"]), 10)
    def test_historical_memory_uses_sparse_evidence_edges(self):
        envelope = build_historical_envelope(
            references=[
                ReferenceItem(source="local", source_id="one", title="Courtyard housing", tags=("courtyard",)),
                ReferenceItem(source="local", source_id="two", title="Atrium school", tags=("atrium",)),
                ReferenceItem(source="local", source_id="three", title="Bridge offices", tags=("bridge",)),
            ],
            design_results=[],
        )
        self.assertEqual(len(envelope["contract"]["features"]), 3)
        self.assertEqual(len(envelope["contract"]["circuits"]), 1)
        self.assertEqual(envelope["projectKey"], "arr-global-precedents")

    @patch("design.maas.mass_brain.config.mass_brain_client")
    def test_shadow_bridge_ingests_sources_and_compiles_only_executable_lane(self, client):
        client.post.side_effect = [
            _response({"projectKey": "pnu-test"}),
            _response({
                "assistantStatus": "disabled",
                "proposals": [
                    {
                        "proposalId": "proposal:one",
                        "lane": "executable",
                        "componentGraph": {
                            "name": "hybrid",
                            "label": "Court ribbon hybrid",
                            "nodes": [
                                {"nodeId": "root", "role": "root", "parentId": None, "optional": False, "operation": {"verb": "base", "params": {}}},
                                {"nodeId": "primary_1_bar", "role": "primary", "parentId": "root", "optional": False, "operation": {"verb": "bar", "params": {"factor": 0.7}}},
                                {"nodeId": "void_2_courtyard", "role": "void", "parentId": "primary_1_bar", "optional": False, "operation": {"verb": "courtyard", "params": {"ratio": 0.22}}},
                            ],
                        },
                        "sourceNodeIds": ["feature:a", "feature:b"],
                        "evidenceIds": [],
                        "scoreBreakdown": {"novelty": 0.8, "evidence": 0.5},
                    },
                    {"proposalId": "proposal:experiment", "lane": "experimental", "operatorRecipe": {"compilerStatus": "unregistered"}},
                ],
            }),
        ]

        def interpret(base, sequence):
            return MorphologyVariant(sequence.name, base, verb_sequence=tuple(sequence.to_list()))

        batch = request_shadow_variants(
            base_footprint=box(0, 0, 20, 20),
            source_variants=[_variant("court", "bar", "courtyard"), _variant("bridge", "split", "diagonal_connect")],
            project_key="pnu-test",
            interpret=interpret,
            parking_options={"mass_brain": {"enabled": True, "count": 2}},
            program_type="neighborhood_living",
        )
        self.assertEqual(batch.artifact["status"], "shadow_generated")
        self.assertEqual(batch.artifact["compiled_count"], 1)
        self.assertEqual(batch.artifact["experimental_count"], 1)
        self.assertEqual(len(batch.variants), 1)
        self.assertTrue(batch.variants[0].operator.startswith("mass_brain_shadow_"))
        ingest_payload = client.post.call_args_list[0].kwargs["json"]
        self.assertEqual(ingest_payload["contract"]["schemaVersion"], "grl/v1")
        self.assertGreaterEqual(len(ingest_payload["contract"]["features"]), 2)
        first_payload = next(iter(ingest_payload["domainPayloads"].values()))
        self.assertIn(first_payload["relationProfile"]["formalStrategy"], {"carve", "bridge", "bend", "cluster"})
        self.assertEqual(first_payload["context"]["programType"], "neighborhood_living")
        self.assertEqual(first_payload["context"]["siteAspectBucket"], "balanced")
        primary = first_payload["componentGraph"]["nodes"][1]
        self.assertEqual(primary["role"], "primary")
        self.assertIn("parameterSchema", primary)
        self.assertIn("constraints", primary)
        self.assertIn("relation", primary)

    def test_flat_sequence_first_design_operation_is_the_primary_language(self):
        sequence = VerbSequence(
            "court_primary",
            "Court primary",
            (
                VerbCall("base", {}),
                VerbCall("courtyard", {"ratio": 0.25}),
                VerbCall("grade", {"side": "north", "depth_ratio": 0.2}),
            ),
        )
        graph = graph_from_sequence(sequence)
        self.assertEqual(graph.nodes[1].role, "primary")
        self.assertEqual(graph.nodes[1].operation.verb, "courtyard")
        self.assertEqual(graph.nodes[2].role, "support")

    def test_exported_schema_preserves_verified_legacy_parent_values(self):
        schema = _parameter_schema_for_verb(
            "courtyard",
            {"upper_ratio": 0.96, "width_ratio": 0.34, "open_side": "southwest"},
        )
        self.assertIn("width_ratio", schema["allowedParameters"])
        self.assertEqual(schema["numericBounds"]["upper_ratio"]["maximum"], 0.96)
        self.assertIn("southwest", schema["categoricalValues"]["open_side"])

    @patch("design.maas.mass_brain.config.mass_brain_client")
    def test_service_failure_is_fail_open(self, client):
        client.post.side_effect = httpx.ConnectError("offline")
        batch = request_shadow_variants(
            base_footprint=box(0, 0, 20, 20),
            source_variants=[_variant("court", "bar", "courtyard"), _variant("bridge", "split", "diagonal_connect")],
            project_key="pnu-test",
            interpret=lambda base, sequence: None,
            parking_options={"mass_brain": {"enabled": True}},
        )
        self.assertEqual(batch.variants, ())
        self.assertEqual(batch.artifact["status"], "unavailable_fail_open")

    @patch("design.maas.mass_brain.config.mass_brain_client")
    def test_outcome_reporting_never_promotes_shadow_candidate(self, client):
        client.post.return_value = _response({"hardPass": True})
        proposal = {"proposalId": "proposal:one", "scoreBreakdown": {"novelty": 0.8, "evidence": 0.5}}
        feature = {
            "type": "Feature",
            "geometry": mapping(box(0, 0, 1, 1)),
            "properties": {
                "parking_precheck": {"layout": {"status": "pass"}},
                "design_quality": {"score": 0.7},
                "source_signature": {"verb_profile": ["base", "step_envelope"], "surface_count": 24},
                "orderliness_evidence": {"main_mass_area_ratio": 0.84, "small_fragment_count": 0},
                "visual_diversity_evidence": {"volume_count": 3},
            },
        }
        result = record_shadow_outcomes(
            project_key="pnu-test",
            proposals_by_operator={"mass_brain_shadow_one": proposal},
            features_by_operator={"mass_brain_shadow_one": feature},
        )
        self.assertEqual(result, {"recorded_count": 1, "failed_count": 0})
        payload = client.post.call_args.kwargs["json"]
        self.assertTrue(payload["parkingPassed"])
        self.assertTrue(payload["geometryPassed"])
        self.assertTrue(payload["details"]["shadow"])
        self.assertTrue(payload["details"]["cleanMassPassed"])
        self.assertEqual(payload["details"]["relationProfile"]["formalStrategy"], "step")
        self.assertEqual(payload["details"]["relationProfile"]["primaryEnvelopeRetention"], 0.84)
        self.assertEqual(relation_profile_from_feature(feature)["surfaceCount"], 24)

    @patch("design.maas.mass_brain.config.mass_brain_client")
    def test_feedback_forwarding_is_idempotency_keyed_and_fail_open(self, client):
        client.post.return_value = _response({"userReward": 1.0})
        result = record_proposal_feedback(
            project_key="pnu-test",
            proposal_id="proposal:one",
            feedback_id="revision:one",
            decision="accepted",
            rating=5,
        )
        self.assertEqual(result["status"], "recorded")
        payload = client.post.call_args.kwargs["json"]
        self.assertEqual(payload["feedbackId"], "revision:one")

        client.post.side_effect = httpx.ConnectError("offline")
        result = record_proposal_feedback(
            project_key="pnu-test",
            proposal_id="proposal:one",
            feedback_id="revision:one",
            decision="accepted",
        )
        self.assertEqual(result["status"], "unavailable_fail_open")
