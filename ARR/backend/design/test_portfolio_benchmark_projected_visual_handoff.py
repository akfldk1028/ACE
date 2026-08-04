"""Regression coverage for projected visual render handoff atomicity."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from design.maas.book_language import portfolio_benchmark


class ProjectedVisualHandoffTest(SimpleTestCase):
    @staticmethod
    def _artifact(triangles):
        return {
            "authority": "certified_projected_visual_mesh",
            "projectedVisualMesh": {"triangles": triangles},
        }

    @staticmethod
    def _triangle():
        return {
            "role": "main:skin:000",
            "vertices_m": [
                [0.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
                [0.0, 1.0, 1.0],
            ],
        }

    def test_empty_projected_authority_raises_before_surface_mutation(self):
        props = {
            "source_surfaces": [{"role": "source:skin:000"}],
            "final_semantic_anchor": {"existing": True},
        }
        before = deepcopy(props)

        with self.assertRaises(
            portfolio_benchmark.ProjectedVisualHandoffError,
        ) as captured:
            portfolio_benchmark._atomically_replace_projected_visual_surfaces(
                props,
                self._artifact([]),
                visual_origin=SimpleNamespace(x=10.0, y=20.0),
                candidate_height=12.0,
            )

        self.assertEqual(props, before)
        self.assertEqual(
            captured.exception.evidence,
            {
                "failure_code": "projected_visual_handoff_invalid",
                "reason": "empty_triangles",
                "triangle_count": 0,
            },
        )

    def test_malformed_projected_triangle_raises_before_surface_mutation(self):
        props = {"source_surfaces": [{"role": "source:skin:000"}]}
        before = deepcopy(props["source_surfaces"])
        malformed = self._triangle()
        malformed["vertices_m"] = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]]

        with self.assertRaises(
            portfolio_benchmark.ProjectedVisualHandoffError,
        ) as captured:
            portfolio_benchmark._atomically_replace_projected_visual_surfaces(
                props,
                self._artifact([malformed]),
                visual_origin=SimpleNamespace(x=10.0, y=20.0),
                candidate_height=12.0,
            )

        self.assertEqual(props["source_surfaces"], before)
        self.assertEqual(
            captured.exception.evidence,
            {
                "failure_code": "projected_visual_handoff_invalid",
                "reason": "invalid_triangle_vertices",
                "triangle_count": 1,
                "triangle_index": 0,
            },
        )

    def test_invalid_artifact_shapes_raise_typed_handoff_errors(self):
        for label, artifact, reason in (
            ("nonmapping", [self._triangle()], "invalid_artifact"),
            ("nonmapping_mesh", {"projectedVisualMesh": []}, "invalid_projected_visual_mesh"),
            ("nonlist_triangles", self._artifact({}), "invalid_triangle_payload"),
        ):
            with self.subTest(label=label):
                props = {"source_surfaces": [{"role": "source:skin:000"}]}
                before = deepcopy(props)

                with self.assertRaises(
                    portfolio_benchmark.ProjectedVisualHandoffError,
                ) as captured:
                    portfolio_benchmark._atomically_replace_projected_visual_surfaces(
                        props,
                        artifact,
                        visual_origin=SimpleNamespace(x=10.0, y=20.0),
                        candidate_height=12.0,
                    )

                self.assertEqual(props, before)
                self.assertEqual(
                    captured.exception.evidence["failure_code"],
                    "projected_visual_handoff_invalid",
                )
                self.assertEqual(captured.exception.evidence["reason"], reason)

    def test_nonfinite_or_non_numeric_coordinates_raise_before_mutation(self):
        for label, coordinate in (
            ("bool", True),
            ("string", "1.0"),
            ("nan", float("nan")),
            ("infinity", float("inf")),
        ):
            with self.subTest(label=label):
                props = {"source_surfaces": [{"role": "source:skin:000"}]}
                before = deepcopy(props)
                malformed = self._triangle()
                malformed["vertices_m"][0][0] = coordinate

                with self.assertRaises(
                    portfolio_benchmark.ProjectedVisualHandoffError,
                ) as captured:
                    portfolio_benchmark._atomically_replace_projected_visual_surfaces(
                        props,
                        self._artifact([malformed]),
                        visual_origin=SimpleNamespace(x=10.0, y=20.0),
                        candidate_height=12.0,
                    )

                self.assertEqual(props, before)
                self.assertEqual(
                    captured.exception.evidence,
                    {
                        "failure_code": "projected_visual_handoff_invalid",
                        "reason": "invalid_triangle_vertices",
                        "triangle_count": 1,
                        "triangle_index": 0,
                    },
                )

    def test_invalid_second_triangle_preserves_original_surfaces(self):
        props = {"source_surfaces": [{"role": "source:skin:000"}]}
        before = deepcopy(props)
        malformed = self._triangle()
        malformed["vertices_m"][2] = [0.0, 1.0]

        with self.assertRaises(
            portfolio_benchmark.ProjectedVisualHandoffError,
        ):
            portfolio_benchmark._atomically_replace_projected_visual_surfaces(
                props,
                self._artifact([self._triangle(), malformed]),
                visual_origin=SimpleNamespace(x=10.0, y=20.0),
                candidate_height=12.0,
            )

        self.assertEqual(props, before)

    def test_valid_projected_triangles_replace_source_surfaces_atomically(self):
        props = {"source_surfaces": [{"role": "source:skin:000"}]}

        portfolio_benchmark._atomically_replace_projected_visual_surfaces(
            props,
            self._artifact([self._triangle()]),
            visual_origin=SimpleNamespace(x=10.0, y=20.0),
            candidate_height=12.0,
        )

        self.assertEqual(
            props["source_surfaces"],
            [{
                "role": "main:skin:000",
                "vertices_m": [
                    [0.0, 0.0, 0.0],
                    [2.0, 0.0, 0.0],
                    [0.0, 1.0, 1.0],
                ],
                "vertices_world_m": [
                    [10.0, 20.0, 0.0],
                    [12.0, 20.0, 0.0],
                    [10.0, 21.0, 12.0],
                ],
            }],
        )

    def test_production_handoff_staging_is_nonmutating_until_commit(self):
        props = {
            "source_surfaces": [{"role": "source:skin:000"}],
            "final_semantic_anchor": {"existing": True},
        }
        before = deepcopy(props)

        staged = portfolio_benchmark._stage_projected_visual_handoff(
            self._artifact([self._triangle()]),
            final_semantic_anchor={"expected_semantic_context": {"zone": "A"}},
            visual_origin=SimpleNamespace(x=10.0, y=20.0),
            candidate_height=12.0,
        )

        self.assertEqual(props, before)
        props.update(staged)
        self.assertEqual(
            props["final_semantic_anchor"],
            {"expected_semantic_context": {"zone": "A"}},
        )
        self.assertEqual(
            props["source_surfaces"][0]["vertices_world_m"],
            [[10.0, 20.0, 0.0], [12.0, 20.0, 0.0], [10.0, 21.0, 12.0]],
        )

    def test_present_falsy_artifacts_fail_closed_before_commit_or_render(self):
        for label, artifact in (
            ("empty_mapping", {}),
            ("empty_list", []),
            ("empty_string", ""),
            ("none", None),
        ):
            with self.subTest(label=label):
                props = {
                    "source_surfaces": [{"role": "source:skin:000"}],
                    "final_semantic_anchor": {"existing": True},
                }
                before = deepcopy(props)
                renderer = Mock()

                with self.assertRaises(
                    portfolio_benchmark.ProjectedVisualHandoffError,
                ):
                    staged = portfolio_benchmark._stage_projected_visual_handoff(
                        artifact,
                        final_semantic_anchor={"expected_semantic_context": {}},
                        visual_origin=SimpleNamespace(x=10.0, y=20.0),
                        candidate_height=12.0,
                        authority_present=True,
                    )
                    props.update(staged)
                    renderer()

                self.assertEqual(props, before)
                renderer.assert_not_called()

    def test_absent_projected_authority_preserves_legacy_staging(self):
        staged = portfolio_benchmark._stage_projected_visual_handoff(
            portfolio_benchmark._PROJECTED_VISUAL_ARTIFACT_ABSENT,
            final_semantic_anchor={"expected_semantic_context": {}},
            visual_origin=SimpleNamespace(x=10.0, y=20.0),
            candidate_height=12.0,
            authority_present=False,
        )

        self.assertEqual(
            staged,
            {"final_semantic_anchor": {"expected_semantic_context": {}}},
        )

    def test_persistence_rebinds_canonical_v2_certificate_before_commit(self):
        from design.maas.geometry_language.projected_visual_contract import (
            AUTHORED_COORDINATE_SPACE,
            FINAL_AUTHORITY_CERTIFICATION_MODE,
            FINAL_CERTIFICATE_SCHEMA,
            FINAL_MESH_SCHEMA,
        )

        canonical_certificate = {
            "schema_version": FINAL_CERTIFICATE_SCHEMA,
            "status": "certified",
            "hard_pass": True,
            "certification_mode": FINAL_AUTHORITY_CERTIFICATION_MODE,
            "projected_surface_coordinate_frame": AUTHORED_COORDINATE_SPACE,
            "visual_hash": "canonical-v2-visual-hash",
        }
        artifact = {
            "projectedVisualMesh": {
                "schemaVersion": FINAL_MESH_SCHEMA,
                "coordinateSpace": AUTHORED_COORDINATE_SPACE,
                "triangles": [self._triangle()],
            },
            "projectedVisualCertificate": deepcopy(canonical_certificate),
            "projectedVisualGeometryHash": "canonical-v2-visual-hash",
        }
        stale_certificate = {
            **canonical_certificate,
            "schema_version": "arr.maas.floorwise_visual_projection.v1",
            "visual_hash": "stale-v1-visual-hash",
        }
        props = {
            "floorwise_visual_projection": stale_certificate,
            "geometry_artifact": {"stale": True},
        }
        staged = {"source_surfaces": [self._triangle()]}
        anchor = {
            "expected_semantic_context": {"program": "neighborhood"},
            "expected_semantic_projection_hash": "semantic-hash",
            "expected_semantic_audit_payload_hash": "audit-hash",
            "expected_section_geometry_binding_hash": "section-hash",
        }
        validated = SimpleNamespace(visual_hash="canonical-v2-visual-hash")
        certified = SimpleNamespace(
            payload=lambda: deepcopy(artifact),
            feature_binding=lambda: {
                "geometry_artifact": deepcopy(artifact),
                "floorwise_visual_projection": deepcopy(
                    canonical_certificate
                ),
                "source_surfaces": [self._triangle()],
                "final_semantic_anchor": deepcopy(anchor),
                "certified_mass_artifact_core_hash": "core-hash",
            },
            validated_visual=validated,
        )

        with patch.object(
            portfolio_benchmark.CertifiedMassArtifact,
            "issue",
            side_effect=AssertionError("canonical artifact must not be regenerated"),
        ), patch.object(
            portfolio_benchmark.CertifiedMassArtifact,
            "load",
            return_value=certified,
        ):
            selected_artifact = (
                portfolio_benchmark._projected_visual_handoff_artifact(
                    SimpleNamespace(
                        metadata={
                            "floorwise_visual_projection": stale_certificate,
                        }
                    ),
                    existing_artifact=artifact,
                )
            )
        self.assertEqual(selected_artifact, artifact)

        with patch.object(
            portfolio_benchmark.CertifiedMassArtifact,
            "load",
            return_value=certified,
        ) as loader:
            result = portfolio_benchmark._persist_projected_visual_authority(
                props,
                geometry_artifact=artifact,
                staged_handoff=staged,
                final_semantic_anchor=anchor,
            )

        self.assertIs(result, validated)
        self.assertEqual(
            props["floorwise_visual_projection"],
            canonical_certificate,
        )
        self.assertEqual(props["geometry_artifact"], artifact)
        loader.assert_called_once_with(
            artifact,
            authority_context=anchor,
        )

        for label, mutate in (
            (
                "stale_v1",
                lambda value: value["projectedVisualCertificate"].update(
                    schema_version="arr.maas.floorwise_visual_projection.v1"
                ),
            ),
            (
                "tampered_hash",
                lambda value: value.update(
                    projectedVisualGeometryHash="tampered-visual-hash"
                ),
            ),
        ):
            with self.subTest(label=label):
                invalid_artifact = deepcopy(artifact)
                mutate(invalid_artifact)
                before = deepcopy(props)
                with self.assertRaises(ValueError):
                    portfolio_benchmark._persist_projected_visual_authority(
                        props,
                        geometry_artifact=invalid_artifact,
                        staged_handoff=staged,
                        final_semantic_anchor=anchor,
                    )
                self.assertEqual(props, before)

    def test_selected_candidate_handoff_loads_embedded_canonical_artifact(self):
        artifact = {"projectedVisualMesh": {"triangles": [self._triangle()]}}
        anchor = {"expected_semantic_projection_hash": "semantic-hash"}
        feature = {
            "type": "Feature",
            "properties": {
                "geometry_artifact": artifact,
                "final_semantic_anchor": anchor,
            },
        }
        certified = SimpleNamespace(payload=lambda: deepcopy(artifact))

        with patch.object(
            portfolio_benchmark.CertifiedMassArtifact,
            "load",
            return_value=certified,
        ) as loader:
            result = portfolio_benchmark._projected_visual_handoff_artifact(
                feature,
            )

        self.assertEqual(result, artifact)
        loader.assert_called_once_with(artifact, authority_context=anchor)

        with self.assertRaises(ValueError):
            portfolio_benchmark._projected_visual_handoff_artifact(
                {"type": "Feature", "properties": {}},
            )

        with patch.object(
            portfolio_benchmark.CertifiedMassArtifact,
            "load",
            side_effect=ValueError("tampered certified artifact"),
        ), self.assertRaisesRegex(ValueError, "tampered certified artifact"):
            portfolio_benchmark._projected_visual_handoff_artifact(feature)

    def test_r63_selected_repaired_persistence_binds_certified_semantic_gate(self):
        gate = {
            "schema_version": "arr.maas.final_semantic_projection.v1",
            "status": "verified",
            "hard_pass": True,
            "semantic_projection_hash": "r63-semantic-projection-hash",
            "failures": [],
        }
        feature = {
            "type": "Feature",
            "properties": {
                "variant_id": "r63-repaired-selected",
                "semantic_projection_hard_gate": deepcopy(gate),
            },
        }

        resolved = (
            portfolio_benchmark._selected_semantic_projection_hard_gate(
                feature,
                candidate_id="r63-repaired-selected",
            )
        )

        self.assertEqual(resolved, gate)
        self.assertIsNot(resolved, feature["properties"]["semantic_projection_hard_gate"])

        for label, invalid_feature, reason in (
            (
                "missing",
                {"type": "Feature", "properties": {"variant_id": "missing"}},
                "selected_semantic_projection_hard_gate_missing",
            ),
            (
                "failed",
                {
                    "type": "Feature",
                    "properties": {
                        "variant_id": "failed",
                        "semantic_projection_hard_gate": {
                            **gate,
                            "hard_pass": False,
                            "failures": ["statutory_context_mismatch"],
                        },
                    },
                },
                "selected_semantic_projection_hard_gate_failed",
            ),
        ):
            with self.subTest(label=label), self.assertRaises(
                portfolio_benchmark.SelectedSemanticProjectionHardGateError,
            ) as captured:
                portfolio_benchmark._selected_semantic_projection_hard_gate(
                    invalid_feature,
                    candidate_id=f"r63-{label}",
                )
            self.assertEqual(captured.exception.evidence["reason"], reason)
            self.assertEqual(
                captured.exception.evidence["candidate_id"],
                f"r63-{label}",
            )
