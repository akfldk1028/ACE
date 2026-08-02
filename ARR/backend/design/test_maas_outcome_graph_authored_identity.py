from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.geometry_language import base_seed_programs
from design.maas.geometry_language.floorwise_visual_projection import (
    projected_surface_visual_hash,
)
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.source_geometry.ir import SourceSurface


class OutcomeGraphAuthoredIdentityTests(SimpleTestCase):
    def _source_and_candidate(self):
        authored = base_seed_programs()[0]
        projected = base_seed_programs()[1]
        authored_payload = authored.to_dict()
        authored_payload["metadata"] = {
            **authored_payload["metadata"],
            "pre_book_program_hash": "reusable-pre-book-hash",
        }
        source = SimpleNamespace(metadata={
            "authored_geometry_program": authored_payload,
            "geometry_program": projected.to_dict(),
            "geometry_program_bridge_evidence": {
                "upstream_authored_program_hash": authored.program_hash(),
                "program_hash": projected.program_hash(),
                "geometry_hash": "final-geometry",
                "source_seed": "identity-seed",
                "operator_path": ["base", "notch"],
            },
            "program_book_projection_evidence": {
                "scope": {"base_volume_label": "1/2"},
            },
        }, surfaces=())
        candidate = SimpleNamespace(
            source=source,
            sequence=SimpleNamespace(name="identity-seed__book_notch"),
            principle_id="book:operative:notch",
        )
        return authored, projected, source, candidate

    def test_success_candidate_preserves_authored_and_projected_identities(self):
        authored, projected, _source, candidate = (
            self._source_and_candidate()
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        graph.observe_candidates(
            program_slug="neighborhood",
            candidates=(candidate,),
            downstream_report={"rows": [{
                "legal_projection": {
                    "hard_pass": True,
                    "geometry_retention_pass": True,
                },
                "parking_hard_gate": {"hard_pass": True},
                "combined_hard_pass": True,
            }]},
        )

        observation = graph.observations[-1]
        self.assertEqual(
            observation["program_hash"],
            "reusable-pre-book-hash",
        )
        self.assertEqual(
            observation["authored_program_hash"],
            authored.program_hash(),
        )
        self.assertEqual(
            observation["authored_book_program_hash"],
            authored.program_hash(),
        )
        self.assertEqual(
            observation["projected_program_hash"],
            projected.program_hash(),
        )
        authored_node = next(
            node for node in graph.nodes.values()
            if node["kind"] == "geometry_program"
        )
        projected_node = next(
            node for node in graph.nodes.values()
            if node["kind"] == "projected_geometry_program"
        )
        self.assertEqual(
            authored_node["attributes"]["name"],
            authored.name,
        )
        self.assertEqual(
            projected_node["attributes"]["typed_ast"]["root_id"],
            projected.root_id,
        )
        self.assertTrue(any(
            edge["kind"] == "book_projected_to"
            for edge in graph.edges.values()
        ))
        preferred = graph.preferred_book_principle_ids(
            source_seed="identity-seed",
            program_hash="reusable-pre-book-hash",
            fallback=("book:fallback",),
        )
        self.assertEqual(preferred[0], "book:operative:notch")

    def test_program_evaluation_uses_same_authored_source_identity(self):
        authored, projected, source, _candidate = (
            self._source_and_candidate()
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        graph.observe_program_evaluation(
            program_slug="neighborhood",
            source=source,
            sequence_name="identity-seed__book_notch",
            principle_id="book:operative:notch",
            spatial={},
            failed_gates=(),
        )

        observation = graph.observations[-1]
        self.assertEqual(
            observation["program_hash"],
            "reusable-pre-book-hash",
        )
        self.assertEqual(
            observation["authored_book_program_hash"],
            authored.program_hash(),
        )
        self.assertEqual(
            observation["projected_program_hash"],
            projected.program_hash(),
        )

    def test_final_vlm_keeps_authored_node_and_reviews_final_ast(self):
        authored, projected, _source, candidate = (
            self._source_and_candidate()
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        graph.observe_final_book_vlm_audit(
            program_slug="neighborhood",
            candidate=candidate,
            audit={
                "hard_pass": True,
                "reviewed_exact_post_book_geometry": True,
                "response_id": "identity-review",
            },
        )

        observation = graph.observations[-1]
        self.assertEqual(
            observation["program_hash"],
            "reusable-pre-book-hash",
        )
        self.assertEqual(
            observation["authored_book_program_hash"],
            authored.program_hash(),
        )
        self.assertEqual(
            observation["projected_program_hash"],
            projected.program_hash(),
        )
        authored_node = next(
            node for node in graph.nodes.values()
            if node["kind"] == "geometry_program"
        )
        projected_node = next(
            node for node in graph.nodes.values()
            if node["kind"] == "projected_geometry_program"
        )
        self.assertEqual(
            authored_node["attributes"]["name"],
            authored.name,
        )
        self.assertEqual(
            projected_node["attributes"]["typed_ast"]["root_id"],
            projected.root_id,
        )

    def test_geometry_failure_uses_same_three_identities(self):
        authored, projected, source, _candidate = (
            self._source_and_candidate()
        )
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        graph.observe_geometry_gate_failure(
            program_slug="neighborhood",
            source_seed="identity-seed",
            program=projected,
            principle_id="book:operative:notch",
            book_scope="1/2",
            stage="capacity_replay",
            failure_reasons=("tiny_edge",),
            source=source,
        )

        observation = graph.observations[-1]
        self.assertEqual(
            observation["program_hash"],
            "reusable-pre-book-hash",
        )
        self.assertEqual(
            observation["authored_book_program_hash"],
            authored.program_hash(),
        )
        self.assertEqual(
            observation["projected_program_hash"],
            projected.program_hash(),
        )

    def test_render_observation_uses_same_three_identities(self):
        authored, projected, source, candidate = (
            self._source_and_candidate()
        )
        surface = SourceSurface(
            role="visual",
            volume_role="primary",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=(
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
            ),
        )
        visual_hash = projected_surface_visual_hash((surface,))
        source.surfaces = (surface,)
        source.metadata["floorwise_visual_projection"] = {
            "schema_version": "arr.maas.floorwise_visual_projection.v1",
            "status": "certified",
            "hard_pass": True,
            "visual_hash": visual_hash,
            "projected_surface_count": 1,
        }
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        graph.observe_portfolio_render(
            program_slug="neighborhood",
            candidates=(candidate,),
            board_path=Path("board.png"),
            render_evidence=({
                "card_index": 1,
                "projected_visual_geometry_hash": visual_hash,
                "hard_pass": True,
            },),
        )

        observation = graph.observations[-1]
        self.assertEqual(
            observation["program_hash"],
            "reusable-pre-book-hash",
        )
        self.assertEqual(
            observation["authored_book_program_hash"],
            authored.program_hash(),
        )
        self.assertEqual(
            observation["projected_program_hash"],
            projected.program_hash(),
        )
