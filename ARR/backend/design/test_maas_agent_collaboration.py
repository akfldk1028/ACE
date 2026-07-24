from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.agents.orchestrator.execution_collaboration import (
    ExecutionCollaborationError,
    run_execution_collaboration,
)
from design.maas.agents.law_graph_agent.evidence import (
    _bounded_law_domain_search,
    collect_law_agent_evidence,
)
from design.maas.agents.shared.types import AgentEvidence, ExecutionIdentity
from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.single_execution import execute_single_mass


class ExecutionCollaborationContractTests(SimpleTestCase):
    def _identity(self) -> ExecutionIdentity:
        return ExecutionIdentity(
            execution_id="mass-contract-01",
            program_hash="program-hash-01",
            geometry_hash="geometry-hash-01",
            pnu="1168011800104170004",
        )

    def _executor(self, agent: str, status: str = "passed"):
        def execute(identity, accumulated):
            return AgentEvidence(
                evidence_id=f"evidence:{agent}",
                agent=agent,
                status=status,
                summary=f"{agent} {status}",
                identity=identity,
                evidence={"upstream_count": len(accumulated)},
            )

        return execute

    def test_exact_mass_identity_traverses_specialists_in_order(self):
        identity = self._identity()
        trace = run_execution_collaboration(
            identity,
            executors={
                "maas_geometry_agent": self._executor("maas_geometry_agent"),
                "law_graph_agent": self._executor("law_graph_agent"),
                "parking_agent": self._executor("parking_agent"),
                "review_agent": self._executor("review_agent"),
            },
        )

        self.assertEqual(
            [row.agent for row in trace.evidence],
            [
                "maas_geometry_agent",
                "law_graph_agent",
                "parking_agent",
                "review_agent",
                "selector",
            ],
        )
        self.assertEqual(
            [(row.source_agent, row.target_agent) for row in trace.handoffs],
            [
                ("design_orchestrator", "maas_geometry_agent"),
                ("maas_geometry_agent", "law_graph_agent"),
                ("law_graph_agent", "parking_agent"),
                ("parking_agent", "review_agent"),
                ("review_agent", "selector"),
            ],
        )
        self.assertTrue(all(row.identity == identity for row in trace.evidence))
        self.assertTrue(all(row.identity == identity for row in trace.handoffs))
        self.assertEqual(trace.final_status, "accepted")

    def test_missing_law_evidence_blocks_acceptance_but_keeps_trace(self):
        identity = self._identity()
        trace = run_execution_collaboration(
            identity,
            executors={
                "maas_geometry_agent": self._executor("maas_geometry_agent"),
                "law_graph_agent": self._executor("law_graph_agent", "needs_evidence"),
                "parking_agent": self._executor("parking_agent"),
                "review_agent": self._executor("review_agent"),
            },
        )

        self.assertEqual(trace.final_status, "needs_evidence")
        self.assertEqual(trace.evidence[-1].agent, "selector")
        self.assertEqual(trace.evidence[-1].status, "needs_evidence")
        self.assertEqual(len(trace.handoffs), 5)

    def test_hash_mismatch_fails_closed(self):
        identity = self._identity()

        def corrupt_geometry(bound_identity, accumulated):
            return AgentEvidence(
                evidence_id="evidence:bad-geometry",
                agent="maas_geometry_agent",
                status="passed",
                summary="wrong MASS",
                identity=replace(bound_identity, geometry_hash="another-geometry"),
                evidence={},
            )

        with self.assertRaisesMessage(ExecutionCollaborationError, "identity mismatch"):
            run_execution_collaboration(
                identity,
                executors={
                    "maas_geometry_agent": corrupt_geometry,
                    "law_graph_agent": self._executor("law_graph_agent"),
                    "parking_agent": self._executor("parking_agent"),
                    "review_agent": self._executor("review_agent"),
                },
            )

    def test_law_agent_records_graph_and_search_provenance(self):
        identity = self._identity()
        evidence = collect_law_agent_evidence(
            identity,
            {
                "law": {"evaluated": True, "hard_pass": True},
                "building_type": "neighborhood_living",
            },
            graph_loader=lambda: {
                "graph_status": {"attempted": True, "available": True},
                "articles": [{"id": "article:84", "law_name": "건축법"}],
            },
            searcher=lambda query, limit: {
                "attempted": True,
                "available": True,
                "query": query,
                "results": [{"hang_id": "hang:parking", "law_name": "주차장법"}],
            },
        )

        self.assertEqual(evidence.status, "passed")
        self.assertEqual(evidence.identity, identity)
        self.assertTrue(evidence.evidence["neo4j"]["available"])
        self.assertTrue(evidence.evidence["law_search"]["available"])
        self.assertEqual(evidence.evidence["article_ids"], ["article:84"])
        self.assertEqual(evidence.evidence["search_result_ids"], ["hang:parking"])

    def test_law_agent_marks_unavailable_graph_as_needs_evidence(self):
        evidence = collect_law_agent_evidence(
            self._identity(),
            {"law": {"evaluated": True, "hard_pass": True}},
            graph_loader=lambda: {
                "graph_status": {
                    "attempted": True,
                    "available": False,
                    "reason": "neo4j_unavailable",
                },
                "articles": [],
            },
            searcher=lambda query, limit: {
                "attempted": True,
                "available": False,
                "error_category": "law_service_unavailable",
                "results": [],
            },
        )

        self.assertEqual(evidence.status, "needs_evidence")
        self.assertIn("neo4j_unavailable", evidence.evidence["missing_evidence"])
        self.assertIn("law_search_unavailable", evidence.evidence["missing_evidence"])

    @patch("land.config.law_client")
    def test_law_domain_search_allows_bounded_cold_start(self, law_client):
        response = law_client.post.return_value
        response.json.return_value = {"results": [{"hang_id": "hang:parking"}]}

        with patch.object(sys, "argv", ["manage.py"]):
            result = _bounded_law_domain_search("parking", 3)

        timeout = law_client.post.call_args.kwargs["timeout"]
        self.assertGreaterEqual(timeout.read, 5.0)
        self.assertLessEqual(timeout.read, 8.0)
        self.assertTrue(result["available"])

    def test_single_mass_passport_and_full_graph_persist_agent_handoffs(self):
        builder = GeometryProgramBuilder("agent_collaboration_mass")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 12, "depth": 8, "height": 5},
            semantic_role="base_seed",
        )
        program = builder.build(
            root,
            family="agent_collaboration_test",
            program_projection_applied=True,
            program_projection={"program_id": "neighborhood_living"},
        )
        downstream = {
            stage_id: {"evaluated": True, "hard_pass": True, "selected": stage_id == "selector"}
            for stage_id in ("site", "capacity", "law", "parking", "program_fit", "selector")
        }
        downstream["site"]["pnu"] = self._identity().pnu
        vlm = {
            "model": "fixture-vlm",
            "program_fit_hard_pass": True,
            "hard_pass": True,
            "concept_scores": {"gesture_clarity": 0.8},
        }

        def factory(agent, status="passed"):
            def execute(identity, accumulated):
                return AgentEvidence(
                    evidence_id=f"evidence:{agent}",
                    agent=agent,
                    status=status,
                    summary=f"{agent} {status}",
                    identity=identity,
                    evidence={"article_ids": ["article:84"]} if agent == "law_graph_agent" else {},
                )

            return execute

        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                program,
                output_root=directory,
                execution_id="agent-passport",
                downstream_evidence=downstream,
                vlm_result=vlm,
                collaboration_executors={
                    "maas_geometry_agent": factory("maas_geometry_agent"),
                    "law_graph_agent": factory("law_graph_agent"),
                    "parking_agent": factory("parking_agent"),
                    "review_agent": factory("review_agent"),
                },
            )

            passport = result.passport
            identity = passport["agent_collaboration"]["identity"]
            self.assertEqual(identity["execution_id"], "agent-passport")
            self.assertEqual(identity["program_hash"], result.program_hash)
            self.assertEqual(identity["geometry_hash"], result.geometry_hash)
            self.assertEqual(passport["status"], "accepted")
            self.assertTrue(Path(result.preview_path).is_file())
            graph = passport["activation_graph"]
            node_ids = {node["id"] for node in graph["nodes"]}
            self.assertIn("agent:law_graph_agent", node_ids)
            self.assertIn("law:article:84", node_ids)
            selector_node = next(
                node for node in graph["nodes"] if node["id"] == "agent:selector"
            )
            self.assertEqual(selector_node["status"], "accepted")
            self.assertEqual(selector_node["activation"], 1.0)
            handoff_edges = [edge for edge in graph["edges"] if edge["relation"] == "agent_handoff"]
            self.assertEqual(len(handoff_edges), 5)
            self.assertTrue(all(edge["activation"] == 1.0 for edge in handoff_edges))
