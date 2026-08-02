from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.design_memory.reference_events import (
    EVENT_SCHEMA_VERSION,
    build_reference_review_events,
    human_pairwise_choice_event,
    mutable_event,
)
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.geometry_language.executed_archive import (
    _retrieved_reference_records,
)
from design.management.commands.generate_maas_creative_100 import (
    _run_bounded_vlm_pilot,
    _select_morphology_medoids,
)
from design.maas.preference.pairwise_store import (
    PairwisePreference,
    append_pairwise_label,
    load_pairwise_labels,
)
from design.maas.preference.vlm_scorer import (
    _bind_submitted_reference_identity,
    _reference_image_inputs,
)


def _reference(index: int) -> dict:
    return {
        "source_id": f"reference-{index}",
        "title": f"Reference {index}",
        "local_path": f"/reference-corpus/reference-{index}.jpg",
        "sha256": f"{index:064x}",
        "source_url": f"https://example.test/projects/{index}",
        "reference_collection": "licensed-test-corpus",
        "rights": "test-only",
        "provenance": {"collector": "unit-test"},
        "retrieval_order": index,
    }


class DesignReferenceEventTests(SimpleTestCase):
    def test_five_retrieved_two_submitted_are_immutable_and_hash_linked(self):
        retrieved = [_reference(index) for index in range(1, 6)]
        submitted = [
            {
                **retrieved[index],
                "input_order": index + 1,
                "used_by_vlm": True,
            }
            for index in range(2)
        ]
        result = {
            "model": "test-vlm",
            "response_id": "response-17",
            "concept_scores": {"gesture_clarity": 0.8},
            "critic_actions": ["strengthen_void"],
            "geometry_edits": [{
                "operation": "update_parameters",
                "target_node_id": "root",
                "parameters": {"width": 8.0},
            }],
            "vlm_image_inputs": {"references": submitted},
        }

        events = build_reference_review_events(
            retrieved_references=retrieved,
            vlm_result=result,
            program_hash="program-hash",
            geometry_hash="geometry-hash",
            require_exact_truth_policy=True,
        )

        self.assertTrue(all(isinstance(event, MappingProxyType) for event in events))
        self.assertEqual(
            [event["event_type"] for event in events].count("reference_retrieved"),
            5,
        )
        submissions = [
            event for event in events
            if event["event_type"] == "reference_submitted_to_vlm"
        ]
        self.assertEqual(len(submissions), 2)
        self.assertEqual(sum(bool(event["used_by_vlm"]) for event in events), 2)
        self.assertTrue(all(
            event["schema_version"] == EVENT_SCHEMA_VERSION
            and event["response_id"] == "response-17"
            and event["program_hash"] == "program-hash"
            and event["geometry_hash"] == "geometry-hash"
            and event["sha256"]
            and event["input_order"] in (1, 2)
            and (event["local_path"] or event["image_uri"])
            for event in submissions
        ))
        with self.assertRaises(TypeError):
            events[0]["event_type"] = "tampered"
        json.dumps([mutable_event(event) for event in events])

    def test_exact_truth_policy_rejects_wrong_retrieval_or_submission_count(self):
        with self.assertRaisesRegex(ValueError, "exactly five"):
            build_reference_review_events(
                retrieved_references=[_reference(1)],
                vlm_result={"response_id": "r", "vlm_image_inputs": {"references": []}},
                program_hash="p",
                geometry_hash="g",
                require_exact_truth_policy=True,
            )

    def test_pairwise_choice_links_people_candidates_reason_and_geometry(self):
        label = PairwisePreference(
            preferred_candidate_id="creative-002",
            rejected_candidate_id="creative-001",
            reviewer_id="professor",
            session_id="jury-7",
            reason="clearer large-span section",
            preferred_geometry_hash="geometry-2",
            rejected_geometry_hash="geometry-1",
        )

        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "pairwise.jsonl"
            append_pairwise_label(path, label)
            persisted = load_pairwise_labels(path)[0]
        event = human_pairwise_choice_event(**{
            key: persisted[key]
            for key in label.to_event_fields()
        })

        self.assertEqual(event["event_type"], "human_pairwise_choice")
        self.assertEqual(event["reviewer_id"], "professor")
        self.assertEqual(event["session_id"], "jury-7")
        self.assertEqual(event["preferred_candidate_id"], "creative-002")
        self.assertEqual(event["rejected_candidate_id"], "creative-001")
        self.assertEqual(event["preferred_geometry_hash"], "geometry-2")
        self.assertEqual(event["rejected_geometry_hash"], "geometry-1")
        self.assertEqual(event["reason"], "clearer large-span section")

    def test_portable_graph_keeps_reference_metadata_but_not_image_bytes(self):
        retrieved = [_reference(index) for index in range(1, 6)]
        result = {
            "model": "test-vlm",
            "response_id": "response-graph",
            "concept_scores": {},
            "critic_actions": [],
            "geometry_edits": [],
            "vlm_image_inputs": {
                "references": [
                    {**retrieved[0], "input_order": 1, "used_by_vlm": True},
                    {**retrieved[1], "input_order": 2, "used_by_vlm": True},
                ],
            },
        }
        events = build_reference_review_events(
            retrieved_references=retrieved,
            vlm_result=result,
            program_hash="program-graph",
            geometry_hash="geometry-graph",
            require_exact_truth_policy=True,
        )
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "design-memory.json"
            graph = GeometryOutcomeGraph(path, "pnu")
            graph.observe_design_memory_events(events)
            payload = graph.save()
            persisted = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload, persisted)
        reference = next(
            node for node in persisted["nodes"]
            if node["kind"] == "reference"
            and node["identity"] == "reference-1"
        )
        self.assertEqual(reference["attributes"]["rights"], "test-only")
        self.assertEqual(
            reference["attributes"]["provenance"],
            {"collector": "unit-test"},
        )
        self.assertEqual(reference["attributes"]["sha256"], f"{1:064x}")
        self.assertNotIn("image_bytes", json.dumps(persisted))

    def test_morphology_medoid_selects_one_representative_per_family(self):
        def candidate(candidate_id: str, family: str, axis: float) -> dict:
            descriptor = {
                "axis_ratios": [axis, 0.5, 0.5],
                "z_slice_occupancies": [0.5] * 8,
                "floor_area_profile": [0.125] * 8,
                "convexity": 0.5,
                "void_fraction": 0.1,
                "normal_bins": [1 / 12] * 12,
                "radial_bins": [0.125] * 8,
                "silhouette_front": [0.5] * 16,
                "silhouette_side": [0.5] * 16,
                "silhouette_isometric": [0.5] * 16,
                "component_count": 1,
                "contact_topology": "single",
            }
            return {
                "candidate_id": candidate_id,
                "family": family,
                "morphology_evidence": {"descriptor": descriptor},
            }

        selected = _select_morphology_medoids([
            candidate("a-edge", "family-a", 0.1),
            candidate("a-medoid", "family-a", 0.5),
            candidate("a-other", "family-a", 0.6),
            candidate("b-only", "family-b", 0.7),
        ])

        self.assertEqual(
            [item["candidate_id"] for item in selected],
            ["a-medoid", "b-only"],
        )
        self.assertLessEqual(len(selected), 15)

    def test_reference_inputs_are_low_detail_and_bind_exact_review_identity(self):
        with TemporaryDirectory() as temporary:
            matches = []
            for index in range(1, 6):
                path = Path(temporary) / f"reference-{index}.jpg"
                path.write_bytes(f"reference-{index}".encode())
                matches.append({
                    **_reference(index),
                    "local_path": str(path),
                })
            content, records = _reference_image_inputs(matches, limit=2)

        image_parts = [
            part for part in content if part["type"] == "input_image"
        ]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(part["detail"] == "low" for part in image_parts))
        bound = _bind_submitted_reference_identity(
            records,
            response_id="response-bound",
            program_hash="program-bound",
            geometry_hash="geometry-bound",
        )
        self.assertTrue(all(
            record["response_id"] == "response-bound"
            and record["program_hash"] == "program-bound"
            and record["geometry_hash"] == "geometry-bound"
            for record in bound
        ))

    def test_executed_archive_reference_record_keeps_digest_and_provenance(self):
        builder = GeometryProgramBuilder("archive-reference")
        root_id = builder.add(
            "primitive",
            "box",
            parameters={"width": 4, "depth": 3, "height": 2},
        )
        program = builder.build(root_id)
        with TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            image_path = (
                workspace / "docs" / "ai-session-memory"
                / "reference-corpus" / "archdaily" / "reference.jpg"
            )
            image_path.parent.mkdir(parents=True)
            image_path.write_bytes(b"archived-reference")
            match = {
                **_reference(1),
                "local_path": str(image_path),
                "provenance": "curated import",
            }
            with patch(
                "design.maas.geometry_language.executed_archive."
                "retrieve_geometry_reference_matches",
                return_value=[match],
            ), patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=workspace,
            ):
                records = _retrieved_reference_records(program)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["local_path"], str(image_path))
        self.assertEqual(len(records[0]["sha256"]), 64)
        self.assertEqual(records[0]["rights"], "test-only")
        self.assertEqual(
            records[0]["provenance"],
            {"note": "curated import"},
        )

    def test_bounded_pilot_caps_families_references_and_uses_low_detail(self):
        builder = GeometryProgramBuilder("pilot-program")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 4, "depth": 3, "height": 2},
        )
        program_payload = builder.build(root).to_dict()

        def candidate(index: int) -> dict:
            axis = 0.1 + index / 100
            descriptor = {
                "axis_ratios": [axis, 0.5, 0.5],
                "z_slice_occupancies": [0.5] * 8,
                "floor_area_profile": [0.125] * 8,
                "convexity": 0.5,
                "void_fraction": 0.1,
                "normal_bins": [1 / 12] * 12,
                "radial_bins": [0.125] * 8,
                "silhouette_front": [0.5] * 16,
                "silhouette_side": [0.5] * 16,
                "silhouette_isometric": [0.5] * 16,
                "component_count": 1,
                "contact_topology": "single",
            }
            return {
                "candidate_id": f"candidate-{index:02d}",
                "family": f"family-{index:02d}",
                "program_hash": f"program-{index:02d}",
                "geometry_hash": f"geometry-{index:02d}",
                "geometry_program": program_payload,
                "render_png": f"renders/candidate-{index:02d}.png",
                "morphology_evidence": {"descriptor": descriptor},
            }

        candidates = [candidate(index) for index in range(18)]
        calls = []

        def fake_score(**kwargs):
            calls.append(kwargs)
            submitted = [
                {
                    **reference,
                    "input_order": order,
                    "used_by_vlm": True,
                }
                for order, reference in enumerate(
                    kwargs["reference_matches"][:2],
                    start=1,
                )
            ]
            return {
                "model": "mock-vlm",
                "response_id": f"response-{len(calls)}",
                "concept_scores": {},
                "critic_actions": [],
                "geometry_edits": [],
                "vlm_image_inputs": {"references": submitted},
            }

        references = [_reference(index) for index in range(1, 6)]
        with TemporaryDirectory() as temporary, patch(
            "design.management.commands.generate_maas_creative_100."
            "retrieve_geometry_reference_matches",
            return_value=references,
        ), patch(
            "design.management.commands.generate_maas_creative_100."
            "score_candidate_with_openai_vlm",
            side_effect=fake_score,
        ):
            result = _run_bounded_vlm_pilot(
                candidates,
                run_directory=Path(temporary),
                model="mock-vlm",
            )

        self.assertEqual(result["request_count"], 15)
        self.assertEqual(len(calls), 15)
        self.assertTrue(all(
            call["image_detail"] == "low"
            and len(call["reference_matches"]) <= 3
            for call in calls
        ))
