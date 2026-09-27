"""The master_plan_agent seat accepts a MasterPlanagent layout hand-off and fails closed."""
from __future__ import annotations

from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.agents.master_plan_agent.handoff import (
    evidence_from_masterplan_layout,
    identity_reasons,
    is_masterplan_layout,
)
from design.maas.agents.orchestrator.execution_collaboration import (
    build_default_execution_executors,
    run_execution_collaboration,
)
from design.maas.agents.shared.types import ExecutionIdentity
from design.maas.masterplan.geometry import digest

PNU = "1168010100106770000"


def identity(pnu: str = PNU) -> ExecutionIdentity:
    return ExecutionIdentity(execution_id="mass-01", program_hash="p", geometry_hash="g",
                             floor_capacity_plan_hash="f", pnu=pnu)


def layout(*, pnu: str = PNU, status: str = "resolved", hard_pass: bool = True, handoff_status: str = "passed",
           blocking: list[str] | None = None) -> dict:
    features = [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                 "properties": {"layer": "parking_stall", "level": -1, "stall_id": "B1-P001"}}]
    request = {"pnu": pnu, "site": {"type": "Polygon", "coordinates": [[[0, 0], [9, 0], [9, 9], [0, 0]]]}}
    return {
        "schema_version": "masterplan.layout.v1", "pnu": pnu, "status": status, "features": features,
        "metric_request": request, "metric_features": features, "blocking": list(blocking or []),
        "metrics": {"required_parking_stalls": 12, "provided_parking_stalls": 12, "parking_strategy": "basement",
                    "basement_levels": 1, "site_area_m2": 2880.0},
        "validation": {"geometry_status": "passed", "checks": [{"id": "parking_count", "status": "passed"}],
                       "pending_reviews": ["vehicle_swept_path_review"]},
        "handoff": {"source_agent": "masterplanagent", "target_agent": "massagent", "pnu": pnu,
                    "input_hash": digest(request), "geometry_hash": digest(features),
                    "metric_geometry_hash": digest(features), "status": handoff_status,
                    "evaluated": True, "hard_pass": hard_pass, "scope": "serialized geometry"},
    }


class MasterPlanHandoffTests(SimpleTestCase):
    def test_matching_hard_pass_layout_is_passed_evidence_with_its_metrics(self):
        evidence = evidence_from_masterplan_layout(identity(), layout())
        self.assertEqual(evidence.agent, "master_plan_agent")
        self.assertEqual(evidence.status, "passed")
        self.assertEqual(evidence.evidence["identity_reasons"], [])
        self.assertEqual(evidence.evidence["metrics"]["provided_parking_stalls"], 12)
        self.assertEqual(evidence.evidence["pending_reviews"], ["vehicle_swept_path_review"])
        self.assertEqual(evidence.evidence["handoff"]["geometry_hash"], layout()["handoff"]["geometry_hash"])

    def test_layout_for_another_parcel_fails_closed(self):
        evidence = evidence_from_masterplan_layout(identity("4115011300106840001"), layout())
        self.assertEqual(evidence.status, "failed")
        self.assertIn("pnu mismatch", evidence.evidence["identity_reasons"][0])

    def test_tampered_features_fail_the_hash_binding(self):
        tampered = layout()
        tampered["features"][0]["properties"]["stall_id"] = "B1-P999"
        reasons = identity_reasons(identity(), tampered)
        self.assertTrue(any("geometry hash" in r for r in reasons), reasons)
        self.assertEqual(evidence_from_masterplan_layout(identity(), tampered).status, "failed")

    def test_unresolved_layout_is_needs_evidence_with_its_reasons(self):
        pending = layout(status="needs_evidence", hard_pass=False, handoff_status="needs_evidence",
                         blocking=["overlay street_height: raster only"])
        evidence = evidence_from_masterplan_layout(identity(), pending)
        self.assertEqual(evidence.status, "needs_evidence")
        self.assertEqual(evidence.evidence["blocking"], ["overlay street_height: raster only"])

    def test_unevaluated_handoff_fails(self):
        raw = layout()
        raw["handoff"]["evaluated"] = False
        self.assertEqual(evidence_from_masterplan_layout(identity(), raw).status, "failed")

    def test_specialist_chain_takes_the_layout_in_the_master_plan_seat(self):
        compilation = SimpleNamespace(status="compiled", geometry_hash="g", metrics={})
        executors = build_default_execution_executors(
            compilation=compilation, geometry_gate_issues=[],
            downstream_evidence={"masterplan": layout(), "law": {}},
            program_metadata={"building_type": "업무시설"},
        )
        executors["law_graph_agent"] = lambda ident, acc: __import__(
            "design.maas.agents.shared.types", fromlist=["AgentEvidence"]).AgentEvidence(
            evidence_id="evidence:law_graph_agent", agent="law_graph_agent", status="passed", summary="stub", identity=ident)
        trace = run_execution_collaboration(identity(), executors=executors)
        seat = next(row for row in trace.evidence if row.agent == "master_plan_agent")
        self.assertEqual(seat.status, "passed")
        self.assertEqual(seat.evidence["source"], "masterplanagent")
        self.assertEqual(trace.final_status, "accepted")

    def test_chain_without_a_layout_keeps_the_legacy_parking_path(self):
        compilation = SimpleNamespace(status="compiled", geometry_hash="g", metrics={})
        executors = build_default_execution_executors(
            compilation=compilation, geometry_gate_issues=[],
            downstream_evidence={"parking": {"status": "failed", "evaluated": True, "hard_pass": False}},
            program_metadata={},
        )
        seat = executors["master_plan_agent"](identity(), ())
        self.assertEqual(seat.status, "failed")
        self.assertNotIn("source", seat.evidence)

    def test_is_masterplan_layout_requires_schema_and_handoff(self):
        self.assertTrue(is_masterplan_layout(layout()))
        self.assertFalse(is_masterplan_layout({"schema_version": "masterplan.layout.v0"}))
        self.assertFalse(is_masterplan_layout({"status": "passed", "hard_pass": True}))
