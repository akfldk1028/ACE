from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.geometry_language.projected_visual_contract import (
    exact_triangle_payload_hash,
    serialize_certified_projected_visual,
    validate_projected_visual_artifact,
)
from design.maas.geometry_language.source_bridge import (
    source_surface_payload_hash,
)
from design.maas.program_massing.semantic_carriers import (
    rebind_semantic_projection_capacity,
    semantic_audit_context_hash,
)
from design.maas.source_geometry.ir import SourceSurface


class ProjectedVisualCapacityProvenanceTest(SimpleTestCase):
    def _fixture(self):
        surface = SourceSurface(
            role="final_surface",
            volume_role="main",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 1.0)),
            operator="union",
            semantic_patch_id="final:0",
        )
        surface_hash = source_surface_payload_hash((surface,))
        evidence = rebind_semantic_projection_capacity(
            {
                "program_id": "gymnasium",
                "final_program_hash": "program-hash",
                "final_geometry_hash": "geometry-hash",
                "final_surface_payload_hash": surface_hash,
                "floor_capacity_plan_hash": "floor-plan",
                "pnu": "1168011800104170004",
                "site_context_hash": "law-site-hash",
                "capacity_alternative_id": "balanced",
                "achieved_capacity_band": "balanced",
                "source_role_scaffold_hash": "scaffold-hash",
                "program_contract_hash": "contract-hash",
                "projection_method": "test_projection",
                "carriers": [{"carrier_id": "carrier-1"}],
            },
            achieved_capacity_band="balanced",
            capacity_measurement_hash="new-capacity-hash",
        )
        archived_evidence = rebind_semantic_projection_capacity(
            evidence,
            achieved_capacity_band="balanced",
            capacity_measurement_hash="archived-capacity-hash",
        )
        context = {
            "floor_capacity_plan_hash": "floor-plan",
            "pnu": "1168011800104170004",
            "site_context_hash": "law-site-hash",
            "capacity_alternative_id": "balanced",
            "achieved_capacity_band": "balanced",
            "capacity_measurement_hash": "archived-capacity-hash",
            "program_id": "gymnasium",
        }
        audit = {
            "schema_version": "arr.maas.final_semantic_projection_audit.v1",
            "audit_scope": "full_identity",
            "status": "verified",
            "hard_pass": True,
            "semantic_projection_hash": archived_evidence[
                "semantic_projection_hash"
            ],
            "accepted_carrier_count": 1,
            "accepted_carriers": [{"carrier_id": "carrier-1"}],
            "failures": [],
            "audited_context": context,
            "audited_context_hash": semantic_audit_context_hash(context),
        }
        source = SimpleNamespace(
            footprint=box(0.0, 0.0, 2.0, 2.0),
            surfaces=(surface,),
            metadata={
                "geometry_authority": "authored_projected_surface_payload",
                "program_semantic_carrier_evidence": evidence,
                "geometry_program_bridge_evidence": {
                    "program_hash": "program-hash",
                    "geometry_hash": "geometry-hash",
                    "surface_payload_hash": surface_hash,
                },
                "final_program_hash": "program-hash",
                "final_geometry_hash": "geometry-hash",
                "final_surface_payload_hash": surface_hash,
                "candidate_floor_context": {
                    "floor_count": 4,
                    "height_m": 14.0,
                },
            },
        )
        return source, audit

    @staticmethod
    def _semantic_audit(source, *, building_type, expected_context):
        del building_type
        evidence = source.metadata["program_semantic_carrier_evidence"]
        failures = []
        if expected_context.get("site_context_hash") != "law-site-hash":
            failures.append("site_context_hash_mismatch")
        if (
            expected_context.get("capacity_measurement_hash")
            != evidence["capacity_measurement_hash"]
        ):
            failures.append("capacity_measurement_hash_mismatch")
        return {
            "schema_version": "arr.maas.final_semantic_projection_audit.v1",
            "audit_scope": "full_identity",
            "status": "verified" if not failures else "rejected",
            "hard_pass": not failures,
            "semantic_projection_hash": evidence["semantic_projection_hash"],
            "accepted_carrier_count": 1,
            "accepted_carriers": (
                [{"carrier_id": "carrier-1"}] if not failures else []
            ),
            "failures": failures,
            "audited_context": dict(expected_context),
            "audited_context_hash": semantic_audit_context_hash(
                expected_context
            ),
        }

    def test_updated_capacity_diagnostic_preserves_final_visual_authority(self):
        source, audit = self._fixture()

        with patch(
            "design.maas.program_massing.semantic_carriers."
            "audit_source_semantic_projection",
            side_effect=self._semantic_audit,
        ):
            artifact = serialize_certified_projected_visual(
                source,
                final_semantic_audit=audit,
            )

        self.assertEqual(
            artifact["semanticProjectionHash"],
            audit["semantic_projection_hash"],
        )
        self.assertEqual(
            artifact["capacityMeasurementProvenance"],
            {
                "identity_authority": False,
                "status": "diagnostic_drift",
                "audited_capacity_measurement_hash": "archived-capacity-hash",
                "current_capacity_measurement_hash": "new-capacity-hash",
            },
        )

    def test_four_floor_visual_payload_uses_one_physical_metric_frame(self):
        source, audit = self._fixture()

        with patch(
            "design.maas.program_massing.semantic_carriers."
            "audit_source_semantic_projection",
            side_effect=self._semantic_audit,
        ):
            artifact = serialize_certified_projected_visual(
                source,
                final_semantic_audit=audit,
            )

        mesh = artifact["projectedVisualMesh"]
        certificate = artifact["projectedVisualCertificate"]
        z_values = [
            float(vertex[2])
            for triangle in mesh["triangles"]
            for vertex in triangle["vertices_m"]
        ]
        self.assertEqual(max(z_values) - min(z_values), 14.0)
        self.assertEqual(
            mesh["schemaVersion"],
            "arr.maas.projected_visual_mesh.v2",
        )
        self.assertEqual(
            certificate["schema_version"],
            "arr.maas.floorwise_visual_projection.v2",
        )
        self.assertEqual(
            mesh["coordinateSpace"],
            "source_footprint_centroid_local_xyz_m",
        )
        self.assertEqual(
            certificate["projected_surface_coordinate_frame"],
            mesh["coordinateSpace"],
        )
        self.assertEqual(certificate["physical_height_m"], 14.0)
        self.assertEqual(
            certificate["normalized_source_surface_payload_hash"],
            source.metadata["final_surface_payload_hash"],
        )
        self.assertEqual(
            artifact["projectedVisualPayloadHash"],
            exact_triangle_payload_hash(mesh["triangles"]),
        )
        self.assertNotEqual(
            artifact["finalSurfacePayloadHash"],
            source.metadata["final_surface_payload_hash"],
        )

        stale = deepcopy(artifact)
        stale["projectedVisualMesh"].update({
            "schemaVersion": "arr.maas.projected_visual_mesh.v1",
            "coordinateSpace": (
                "source_footprint_centroid_local_xy_normalized_z"
            ),
        })
        stale["projectedVisualCertificate"].update({
            "schema_version": "arr.maas.floorwise_visual_projection.v1",
            "projected_surface_coordinate_frame": (
                "source_footprint_centroid_local_xy_normalized_z"
            ),
        })
        with self.assertRaisesRegex(
            ValueError,
            "selected floorwise visual projection is not certified",
        ):
            validate_projected_visual_artifact(stale)

    def test_late_archived_semantic_comparison_classifies_capacity_only_drift(self):
        source, audit = self._fixture()
        audit["semantic_projection_hash"] = source.metadata[
            "program_semantic_carrier_evidence"
        ]["semantic_projection_hash"]

        with patch(
            "design.maas.program_massing.semantic_carriers."
            "audit_source_semantic_projection",
            side_effect=self._semantic_audit,
        ):
            artifact = serialize_certified_projected_visual(
                source,
                final_semantic_audit=audit,
            )

        self.assertEqual(
            artifact["capacityMeasurementProvenance"]["status"],
            "diagnostic_drift",
        )
        self.assertEqual(
            artifact["finalSurfacePayloadHash"],
            source.metadata["final_surface_payload_hash"],
        )

    def test_unreconstructable_old_capacity_hash_is_diagnostic_only(self):
        source, audit = self._fixture()
        audit["semantic_projection_hash"] = (
            "unreconstructable-old-capacity-derived-hash"
        )

        with patch(
            "design.maas.program_massing.semantic_carriers."
            "audit_source_semantic_projection",
            side_effect=self._semantic_audit,
        ):
            artifact = serialize_certified_projected_visual(
                source,
                final_semantic_audit=audit,
            )

        self.assertEqual(
            artifact["capacityMeasurementProvenance"]["status"],
            "diagnostic_drift",
        )
        self.assertEqual(
            artifact["semanticProjectionHash"],
            "unreconstructable-old-capacity-derived-hash",
        )

    def test_changed_exact_surface_hash_remains_rejected(self):
        source, audit = self._fixture()
        source.metadata["final_surface_payload_hash"] = "tampered-surface-hash"

        with patch(
            "design.maas.program_massing.semantic_carriers."
            "audit_source_semantic_projection",
            side_effect=self._semantic_audit,
        ), self.assertRaisesRegex(ValueError, "identity audit failed"):
            serialize_certified_projected_visual(
                source,
                final_semantic_audit=audit,
            )

    def test_changed_statutory_context_certificate_remains_rejected(self):
        source, audit = self._fixture()
        tampered = deepcopy(audit)
        tampered["audited_context"]["site_context_hash"] = "other-law-site"
        tampered["audited_context_hash"] = semantic_audit_context_hash(
            tampered["audited_context"]
        )

        with patch(
            "design.maas.program_massing.semantic_carriers."
            "audit_source_semantic_projection",
            side_effect=self._semantic_audit,
        ), self.assertRaisesRegex(ValueError, "site_context_hash_mismatch"):
            serialize_certified_projected_visual(
                source,
                final_semantic_audit=tampered,
            )
