"""Canonical transport contract for Task 1 certified projected visual meshes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from typing import Any

from .floorwise_visual_projection import (
    FLOORWISE_EXACT_AUTHORITY_CONTRACTS,
    FLOORWISE_EXACT_AUTHORITY_MODES,
    floorwise_authority_binding_hash,
)


MESH_SCHEMA = "arr.maas.projected_visual_mesh.v1"
CERTIFICATE_SCHEMA = "arr.maas.floorwise_visual_projection.v1"
COORDINATE_SPACE = "capacity_source_centroid_local_xy_normalized_z"
AUTHORED_COORDINATE_SPACE = (
    "source_footprint_centroid_local_xy_normalized_z"
)
FINAL_AUTHORITY_CERTIFICATION_MODE = (
    "final_floorwise_legal_geometry_authority"
)
PROJECTED_AUTHORITY = "certified_projected_visual_mesh"
CAPACITY_PROGRAM_ROLE = "capacity_replay_metadata_and_provenance"
PROJECTED_FIELDS = (
    "projectedVisualMesh",
    "projectedVisualCertificate",
    "projectedVisualGeometryHash",
    "projectedVisualPayloadHash",
)


@dataclass(frozen=True)
class ValidatedProjectedVisual:
    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]
    visual_hash: str
    exact_payload_hash: str
    coordinate_space: str
    certificate: dict[str, Any]


def serialize_certified_projected_visual(
    source: Any,
    *,
    final_semantic_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize exact triangle records while retaining Task 1 visual identity."""

    metadata = (
        source.metadata
        if isinstance(getattr(source, "metadata", None), dict)
        else {}
    )
    has_authored_profiled_surface = any(
        str(getattr(surface, "surface_type", "") or "").startswith("profiled_")
        for surface in tuple(getattr(source, "surfaces", ()) or ())
    )
    if (
        metadata.get("geometry_authority")
        == "final_floorwise_legal_geometry_program"
    ):
        return _serialize_final_floorwise_authority(
            source,
            metadata,
            final_semantic_audit=final_semantic_audit,
        )
    certificate = metadata.get("floorwise_visual_projection")
    if not isinstance(certificate, dict):
        if has_authored_profiled_surface:
            raise ValueError(
                "authored profiled visual source has no certified projection"
            )
        return {}
    if certificate.get("status") == "not_applicable_no_authored_mesh":
        if has_authored_profiled_surface:
            raise ValueError(
                "authored profiled visual source has no certified projection"
            )
        return {}
    _validate_certificate_status(certificate)

    triangles = [
        _surface_triangle_record(surface)
        for surface in tuple(getattr(source, "surfaces", ()) or ())
    ]
    expected_hash = str(certificate.get("visual_hash") or "")
    expected_count = int(certificate.get("projected_surface_count") or 0)
    if (
        not triangles
        or expected_count != len(triangles)
        or not expected_hash
        or _task1_visual_hash(triangles) != expected_hash
    ):
        raise ValueError(
            "certified projected visual mesh does not match its certificate"
        )
    coordinate_space = str(
        certificate.get("projected_surface_coordinate_frame") or ""
    )
    if coordinate_space != _certificate_coordinate_space(certificate):
        raise ValueError("unsupported projected visual coordinate frame")
    payload_hash = exact_triangle_payload_hash(triangles)
    if (
        certificate.get("certification_mode")
        == "authored_visual_legal_validation"
        and str(certificate.get("exact_surface_payload_hash") or "")
        != payload_hash
    ):
        raise ValueError(
            "certified authored visual exact payload hash mismatch"
        )
    _validate_floorwise_authority_binding(
        certificate,
        exact_payload_hash=payload_hash,
    )
    return {
        "authority": PROJECTED_AUTHORITY,
        "geometryProgramRole": CAPACITY_PROGRAM_ROLE,
        "projectedVisualMesh": {
            "schemaVersion": MESH_SCHEMA,
            "coordinateSpace": coordinate_space,
            "triangles": triangles,
            "vertexCount": len(triangles) * 3,
            "triangleCount": len(triangles),
        },
        "projectedVisualCertificate": deepcopy(certificate),
        "projectedVisualGeometryHash": expected_hash,
        "projectedVisualPayloadHash": payload_hash,
    }


def _serialize_final_floorwise_authority(
    source: Any,
    metadata: dict[str, Any],
    *,
    final_semantic_audit: dict[str, Any] | None,
) -> dict[str, Any]:
    """Serialize the exact Task 3 authority without a legacy visual sibling."""

    from design.maas.program_massing.semantic_carriers import (
        audit_source_semantic_projection,
        semantic_audit_context_hash,
    )
    from .source_bridge import source_surface_payload_hash

    semantic_evidence = metadata.get("program_semantic_carrier_evidence")
    semantic_evidence = (
        semantic_evidence
        if isinstance(semantic_evidence, dict)
        else {}
    )
    program_id = str(semantic_evidence.get("program_id") or "")
    external_audit = (
        final_semantic_audit
        if isinstance(final_semantic_audit, dict)
        else {}
    )
    external_context = external_audit.get("audited_context")
    external_context = (
        external_context if isinstance(external_context, dict) else {}
    )
    recomputed_audit = audit_source_semantic_projection(
        source,
        building_type=program_id,
        expected_context=external_context,
    )
    semantic_hash = str(
        semantic_evidence.get("semantic_projection_hash") or ""
    )
    bridge = metadata.get("geometry_program_bridge_evidence")
    bridge = bridge if isinstance(bridge, dict) else {}
    final_program_hash = str(bridge.get("program_hash") or "")
    final_geometry_hash = str(bridge.get("geometry_hash") or "")
    surfaces = tuple(getattr(source, "surfaces", ()) or ())
    actual_surface_hash = source_surface_payload_hash(surfaces)
    identity_ok = bool(
        external_audit.get("schema_version")
        == "arr.maas.final_semantic_projection_audit.v1"
        and external_audit.get("status") == "verified"
        and external_audit.get("hard_pass") is True
        and isinstance(external_audit.get("accepted_carriers"), list)
        and bool(external_audit.get("accepted_carriers"))
        and int(external_audit.get("accepted_carrier_count") or 0)
        == len(external_audit.get("accepted_carriers") or ())
        and str(external_audit.get("audited_context_hash") or "")
        == semantic_audit_context_hash(external_context)
        and recomputed_audit.get("hard_pass") is True
        and str(external_audit.get("semantic_projection_hash") or "")
        == semantic_hash
        and str(recomputed_audit.get("semantic_projection_hash") or "")
        == semantic_hash
        and str(recomputed_audit.get("audited_context_hash") or "")
        == str(external_audit.get("audited_context_hash") or "")
        and _canonical_payload_hash(recomputed_audit)
        == _canonical_payload_hash(external_audit)
        and semantic_hash
        and final_program_hash
        and final_geometry_hash
        and str(metadata.get("final_program_hash") or "")
        == final_program_hash
        and str(metadata.get("final_geometry_hash") or "")
        == final_geometry_hash
        and str(metadata.get("final_surface_payload_hash") or "")
        == actual_surface_hash
        and str(bridge.get("surface_payload_hash") or "")
        == actual_surface_hash
    )
    if not identity_ok:
        failures = sorted(set(
            list(recomputed_audit.get("failures") or ())
            + list(external_audit.get("failures") or ())
        ))
        raise ValueError(
            "final floorwise visual authority identity audit failed"
            + (f": {','.join(failures)}" if failures else "")
        )

    triangles = [_surface_triangle_record(surface) for surface in surfaces]
    if not triangles:
        raise ValueError(
            "final floorwise visual authority identity audit failed: "
            "empty_surface_payload"
        )
    payload_hash = exact_triangle_payload_hash(triangles)
    visual_hash = _task1_visual_hash(triangles)
    semantic_audit_payload_hash = _canonical_payload_hash(
        external_audit
    )
    origin = getattr(source, "footprint", None)
    origin = getattr(origin, "centroid", None)
    if origin is None:
        raise ValueError(
            "final floorwise visual authority identity audit failed: "
            "source_origin_missing"
        )
    certificate = {
        "schema_version": CERTIFICATE_SCHEMA,
        "status": "certified",
        "hard_pass": True,
        "certification_mode": FINAL_AUTHORITY_CERTIFICATION_MODE,
        "visual_hash": visual_hash,
        "projected_surface_count": len(triangles),
        "projected_surface_coordinate_frame": AUTHORED_COORDINATE_SPACE,
        "exact_surface_payload_hash": payload_hash,
        "final_program_hash": final_program_hash,
        "final_geometry_hash": final_geometry_hash,
        "final_surface_payload_hash": actual_surface_hash,
        "semantic_projection_hash": semantic_hash,
        "semantic_projection_audit_hard_pass": True,
        "semantic_audit_context_hash": str(
            external_audit.get("audited_context_hash") or ""
        ),
        "semantic_audit_payload_hash": semantic_audit_payload_hash,
        "source_footprint_centroid_utm": [
            float(origin.x),
            float(origin.y),
        ],
    }
    return {
        "authority": PROJECTED_AUTHORITY,
        "geometryProgramRole": CAPACITY_PROGRAM_ROLE,
        "projectedVisualMesh": {
            "schemaVersion": MESH_SCHEMA,
            "coordinateSpace": AUTHORED_COORDINATE_SPACE,
            "triangles": triangles,
            "vertexCount": len(triangles) * 3,
            "triangleCount": len(triangles),
        },
        "projectedVisualCertificate": certificate,
        "projectedVisualGeometryHash": visual_hash,
        "projectedVisualPayloadHash": payload_hash,
        "finalLegalGeometryHash": final_geometry_hash,
        "finalSurfacePayloadHash": actual_surface_hash,
        "semanticProjectionHash": semantic_hash,
        "semanticProjectionAudit": deepcopy(external_audit),
        "semanticProjectionAuditPayloadHash": (
            semantic_audit_payload_hash
        ),
    }


def declares_projected_visual_binding(artifact: dict[str, Any]) -> bool:
    """Return true for complete bindings and for downgrade/tamper markers."""

    return (
        any(field in artifact for field in PROJECTED_FIELDS)
        or artifact.get("authority") == PROJECTED_AUTHORITY
        or artifact.get("geometryProgramRole") == CAPACITY_PROGRAM_ROLE
    )


def validate_projected_visual_artifact(
    artifact: dict[str, Any],
    *,
    expected_semantic_context: dict[str, Any] | None = None,
    expected_semantic_projection_hash: str = "",
    expected_semantic_audit_payload_hash: str = "",
) -> ValidatedProjectedVisual | None:
    """Validate and hydrate one complete binding; only true legacy returns None.

    Final-authority artifacts require a semantic anchor supplied by their
    caller from evidence outside the artifact.  Legacy projected visuals keep
    their historical no-anchor validation path.
    """

    if not declares_projected_visual_binding(artifact):
        return None
    if (
        not all(field in artifact for field in PROJECTED_FIELDS)
        or artifact.get("authority") != PROJECTED_AUTHORITY
        or artifact.get("geometryProgramRole") != CAPACITY_PROGRAM_ROLE
    ):
        raise ValueError("incomplete projected visual archive binding")

    mesh = artifact.get("projectedVisualMesh")
    certificate = artifact.get("projectedVisualCertificate")
    if not isinstance(mesh, dict) or not isinstance(certificate, dict):
        raise ValueError("invalid projected visual archive binding")
    _validate_certificate_status(certificate)

    expected_visual_hash = str(artifact.get("projectedVisualGeometryHash") or "")
    expected_payload_hash = str(artifact.get("projectedVisualPayloadHash") or "")
    identity = artifact.get("identity")
    identity = identity if isinstance(identity, dict) else {}
    if (
        not expected_visual_hash
        or str(identity.get("geometryHash") or "") != expected_visual_hash
        or str(certificate.get("visual_hash") or "") != expected_visual_hash
    ):
        raise ValueError("invalid projected visual certificate identity")
    if (
        mesh.get("schemaVersion") != MESH_SCHEMA
        or mesh.get("coordinateSpace")
        != _certificate_coordinate_space(certificate)
        or certificate.get("projected_surface_coordinate_frame")
        != _certificate_coordinate_space(certificate)
    ):
        raise ValueError("invalid projected visual mesh coordinate contract")

    triangle_payload = mesh.get("triangles")
    if not isinstance(triangle_payload, list) or not triangle_payload:
        raise ValueError("invalid projected visual triangle payload")
    try:
        actual_payload_hash = exact_triangle_payload_hash(triangle_payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid projected visual triangle payload") from exc
    if not expected_payload_hash or actual_payload_hash != expected_payload_hash:
        raise ValueError(
            "projected visual exact payload hash mismatch: "
            f"expected={expected_payload_hash} actual={actual_payload_hash}"
        )
    if (
        certificate.get("certification_mode")
        in {
            "authored_visual_legal_validation",
            FINAL_AUTHORITY_CERTIFICATION_MODE,
        }
        and str(certificate.get("exact_surface_payload_hash") or "")
        != actual_payload_hash
    ):
        raise ValueError(
            "certified authored visual exact payload hash mismatch"
        )
    _validate_floorwise_authority_binding(
        certificate,
        exact_payload_hash=actual_payload_hash,
    )

    normalized: list[dict[str, Any]] = []
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for triangle in triangle_payload:
        record, exact_vertices = _validated_triangle_record(triangle)
        base_index = len(vertices)
        vertices.extend(exact_vertices)
        triangles.append((base_index, base_index + 1, base_index + 2))
        normalized.append(record)

    final_authority = (
        certificate.get("certification_mode")
        == FINAL_AUTHORITY_CERTIFICATION_MODE
    )
    if final_authority and (
        str(certificate.get("final_program_hash") or "")
        != str(identity.get("programHash") or "")
        or str(certificate.get("final_geometry_hash") or "")
        != str(artifact.get("finalLegalGeometryHash") or "")
        or str(identity.get("finalLegalGeometryHash") or "")
        != str(certificate.get("final_geometry_hash") or "")
        or str(certificate.get("final_surface_payload_hash") or "")
        != str(artifact.get("finalSurfacePayloadHash") or "")
        or str(certificate.get("semantic_projection_hash") or "")
        != str(artifact.get("semanticProjectionHash") or "")
        or str(certificate.get("semantic_audit_payload_hash") or "")
        != str(artifact.get("semanticProjectionAuditPayloadHash") or "")
        or not str(certificate.get("final_surface_payload_hash") or "")
        or not str(certificate.get("semantic_projection_hash") or "")
        or certificate.get("semantic_projection_audit_hard_pass") is not True
        or not isinstance(
            certificate.get("source_footprint_centroid_utm"),
            list,
        )
        or len(certificate.get("source_footprint_centroid_utm") or ())
        != 2
    ):
        raise ValueError("invalid final floorwise visual authority certificate")
    if final_authority:
        actual_final_geometry_hash = _final_authority_geometry_hash(
            normalized,
            certificate=certificate,
        )
        actual_surface_hash = _source_surface_payload_hash_from_triangles(
            normalized
        )
        audit = artifact.get("semanticProjectionAudit")
        audit = audit if isinstance(audit, dict) else {}
        if (
            not isinstance(expected_semantic_context, dict)
            or not expected_semantic_context
            or not str(expected_semantic_projection_hash or "")
            or not str(expected_semantic_audit_payload_hash or "")
        ):
            raise ValueError(
                "invalid final floorwise visual authority external semantic "
                "anchor"
            )
        expected_context_hash = _canonical_payload_hash(
            expected_semantic_context
        )
        if (
            str(audit.get("audited_context_hash") or "")
            != expected_context_hash
            or _canonical_payload_hash(
                audit.get("audited_context")
                if isinstance(audit.get("audited_context"), dict)
                else {}
            )
            != expected_context_hash
            or str(certificate.get("semantic_audit_context_hash") or "")
            != expected_context_hash
            or str(audit.get("semantic_projection_hash") or "")
            != str(expected_semantic_projection_hash)
            or str(certificate.get("semantic_projection_hash") or "")
            != str(expected_semantic_projection_hash)
            or str(artifact.get("semanticProjectionHash") or "")
            != str(expected_semantic_projection_hash)
            or _canonical_payload_hash(audit)
            != str(expected_semantic_audit_payload_hash)
            or str(certificate.get("semantic_audit_payload_hash") or "")
            != str(expected_semantic_audit_payload_hash)
            or str(
                artifact.get("semanticProjectionAuditPayloadHash") or ""
            )
            != str(expected_semantic_audit_payload_hash)
        ):
            raise ValueError(
                "invalid final floorwise visual authority external semantic "
                "anchor"
            )
        if (
            actual_final_geometry_hash
            != str(certificate.get("final_geometry_hash") or "")
            or actual_surface_hash
            != str(certificate.get("final_surface_payload_hash") or "")
            or audit.get("schema_version")
            != "arr.maas.final_semantic_projection_audit.v1"
            or audit.get("status") != "verified"
            or audit.get("hard_pass") is not True
            or str(audit.get("semantic_projection_hash") or "")
            != str(certificate.get("semantic_projection_hash") or "")
            or str(audit.get("audited_context_hash") or "")
            != str(certificate.get("semantic_audit_context_hash") or "")
            or _canonical_payload_hash(audit)
            != str(certificate.get("semantic_audit_payload_hash") or "")
        ):
            raise ValueError(
                "invalid final floorwise visual authority certificate"
            )
    actual_visual_hash = _task1_visual_hash(normalized)
    expected_triangle_count = int(certificate.get("projected_surface_count") or 0)
    if (
        actual_visual_hash != expected_visual_hash
        or expected_triangle_count != len(triangles)
        or int(mesh.get("triangleCount") or 0) != len(triangles)
        or int(mesh.get("vertexCount") or 0) != len(vertices)
    ):
        raise ValueError(
            "projected visual mesh hash mismatch: "
            f"expected={expected_visual_hash} actual={actual_visual_hash}"
        )
    return ValidatedProjectedVisual(
        vertices=tuple(vertices),
        triangles=tuple(triangles),
        visual_hash=expected_visual_hash,
        exact_payload_hash=expected_payload_hash,
        coordinate_space=str(mesh.get("coordinateSpace") or ""),
        certificate=deepcopy(certificate),
    )


def exact_triangle_payload_hash(triangles: list[dict[str, Any]]) -> str:
    """Hash exact JSON triangle records without Task 1's 8-decimal projection."""

    encoded = json.dumps(
        triangles,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_floorwise_authority_binding(
    certificate: dict[str, Any],
    *,
    exact_payload_hash: str,
) -> None:
    mode = str(certificate.get("certification_mode") or "")
    if mode not in FLOORWISE_EXACT_AUTHORITY_MODES:
        component_marker_fields = (
            "section_profile_hash",
            "capacity_volume_hash",
            "floor_capacity_plan_hash",
            "matrix4_stack_hash",
            "authority_binding_hash",
        )
        operation = str(
            certificate.get("visible_geometry_operation") or ""
        )
        task6_operations = {
            contract[0]
            for contract in FLOORWISE_EXACT_AUTHORITY_CONTRACTS.values()
        }
        strong_floorwise_evidence = bool(
            any(
                str(certificate.get(field) or "").strip()
                for field in component_marker_fields
            )
            or operation in task6_operations
            or certificate.get("visible_step_fallback") is True
        )
        if strong_floorwise_evidence:
            raise ValueError(
                "certified floorwise visual authority mode mismatch"
            )
        # Preserve established unrelated certificate lanes when they carry no
        # Task-6 evidence. Their independent exact/final checks remain active.
        if mode in {
            "floorwise_capacity_projection",
            "authored_visual_legal_validation",
            FINAL_AUTHORITY_CERTIFICATION_MODE,
        }:
            return
        authority_marker_fields = (
            *component_marker_fields,
            "exact_surface_payload_hash",
            "visible_geometry_operation",
            "visible_step_fallback",
        )
        if any(
            field in certificate
            for field in authority_marker_fields
        ):
            raise ValueError(
                "certified floorwise visual authority mode mismatch"
            )
        return
    expected_operation, expected_fallback = (
        FLOORWISE_EXACT_AUTHORITY_CONTRACTS[mode]
    )
    if (
        str(certificate.get("visible_geometry_operation") or "")
        != expected_operation
        or certificate.get("visible_step_fallback")
        is not expected_fallback
    ):
        raise ValueError(
            "certified floorwise visual authority mode mismatch"
        )
    certificate_exact_hash = str(
        certificate.get("exact_surface_payload_hash") or ""
    )
    if certificate_exact_hash != str(exact_payload_hash or ""):
        raise ValueError(
            "certified floorwise visual exact payload hash mismatch"
        )
    component_fields = (
        "section_profile_hash",
        "capacity_volume_hash",
        "floor_capacity_plan_hash",
        "matrix4_stack_hash",
        "authority_binding_hash",
    )
    if any(
        not str(certificate.get(field) or "").strip()
        for field in component_fields
    ):
        raise ValueError(
            "certified floorwise visual authority binding mismatch"
        )
    from .floorwise_visual_projection import (
        valid_floor_center_numeric_equivalence,
    )

    if not valid_floor_center_numeric_equivalence(certificate):
        raise ValueError(
            "certified floorwise visual numeric equivalence mismatch"
        )
    recomputed = floorwise_authority_binding_hash(
        section_profile_hash=str(certificate["section_profile_hash"]),
        capacity_volume_hash=str(certificate["capacity_volume_hash"]),
        floor_capacity_plan_hash=str(certificate["floor_capacity_plan_hash"]),
        matrix4_stack_hash=str(certificate["matrix4_stack_hash"]),
        exact_surface_payload_hash=certificate_exact_hash,
        certification_mode=mode,
        visible_geometry_operation=expected_operation,
        visible_step_fallback=bool(
            certificate.get("visible_step_fallback")
        ),
        authored_program_hash=str(
            certificate.get("authored_program_hash") or ""
        ),
        effective_height_m=float(
            certificate.get("effective_height_m") or 0.0
        ),
        verified_profiled_sloped_surface_area=float(
            certificate.get(
                "verified_profiled_sloped_surface_area"
            ) or 0.0
        ),
        verified_profiled_sloped_surface_ratio=float(
            certificate.get(
                "verified_profiled_sloped_surface_ratio"
            ) or 0.0
        ),
        verified_profiled_sloped_surface_hash=str(
            certificate.get(
                "verified_profiled_sloped_surface_hash"
            ) or ""
        ),
        section_numeric_epsilon_m=float(
            certificate.get("section_numeric_epsilon_m") or 0.0
        ),
        floor_center_numeric_equivalence_schema=str(
            certificate.get(
                "floor_center_numeric_equivalence_schema"
            ) or ""
        ),
        max_section_area_delta_m2=float(
            certificate.get("max_section_area_delta_m2") or 0.0
        ),
        max_section_symdiff_m2=float(
            certificate.get("max_section_symdiff_m2") or 0.0
        ),
        max_section_hausdorff_m=float(
            certificate.get("max_section_hausdorff_m") or 0.0
        ),
        max_section_area_bound_m2=float(
            certificate.get("max_section_area_bound_m2") or 0.0
        ),
        mesh_numeric_repair_schema=str(
            certificate.get("mesh_numeric_repair_schema") or ""
        ),
        mesh_cleanup_collapse_threshold_m=float(
            certificate.get("mesh_cleanup_collapse_threshold_m") or 0.0
        ),
        mesh_cleanup_max_physical_displacement_m=float(
            certificate.get(
                "mesh_cleanup_max_physical_displacement_m"
            ) or 0.0
        ),
        mesh_cleanup_raw_indexed_mesh_hash=str(
            certificate.get("mesh_cleanup_raw_indexed_mesh_hash") or ""
        ),
        mesh_cleanup_raw_gate_failure_codes=tuple(
            certificate.get("mesh_cleanup_raw_gate_failure_codes") or ()
        ),
        mesh_cleanup_clean_indexed_mesh_hash=str(
            certificate.get("mesh_cleanup_clean_indexed_mesh_hash") or ""
        ),
        mesh_cleanup_clean_gate_hard_pass=bool(
            certificate.get("mesh_cleanup_clean_gate_hard_pass")
        ),
    )
    if recomputed != str(certificate.get("authority_binding_hash") or ""):
        raise ValueError(
            "certified floorwise visual authority binding mismatch"
        )


def _validate_certificate_status(certificate: dict[str, Any]) -> None:
    if (
        certificate.get("schema_version") != CERTIFICATE_SCHEMA
        or certificate.get("status") != "certified"
        or certificate.get("hard_pass") is not True
    ):
        raise ValueError("selected floorwise visual projection is not certified")


def _certificate_coordinate_space(certificate: dict[str, Any]) -> str:
    mode = str(certificate.get("certification_mode") or "")
    return (
        AUTHORED_COORDINATE_SPACE
        if mode in {
            "authored_visual_legal_validation",
            FINAL_AUTHORITY_CERTIFICATION_MODE,
        }
        else COORDINATE_SPACE
    )


def _surface_triangle_record(surface: Any) -> dict[str, Any]:
    vertices = tuple(getattr(surface, "vertices_m", ()) or ())
    if len(vertices) != 3:
        raise ValueError("certified projected visual mesh must contain triangles")
    exact_vertices: list[list[float]] = []
    for vertex in vertices:
        if len(vertex) != 3:
            raise ValueError("certified projected visual mesh must contain triangles")
        values = [float(value) for value in vertex]
        if not all(isfinite(value) for value in values):
            raise ValueError("certified projected visual mesh must contain finite triangles")
        exact_vertices.append(values)
    surface_type = str(getattr(surface, "surface_type", "") or "")
    if not surface_type.startswith("profiled_"):
        raise ValueError("certified projected visual surface must be profiled")
    return {
        "role": str(getattr(surface, "role", "") or ""),
        "volume_role": str(getattr(surface, "volume_role", "") or ""),
        "verb": str(getattr(surface, "verb", "") or ""),
        "surface_type": surface_type,
        "vertices_m": exact_vertices,
        "operator": str(getattr(surface, "operator", "") or ""),
        "semantic_patch_id": str(
            getattr(surface, "semantic_patch_id", "") or ""
        ),
    }


def _validated_triangle_record(
    triangle: Any,
) -> tuple[dict[str, Any], list[tuple[float, float, float]]]:
    if not isinstance(triangle, dict):
        raise ValueError("invalid projected visual triangle payload")
    raw_vertices = triangle.get("vertices_m")
    if not isinstance(raw_vertices, list) or len(raw_vertices) != 3:
        raise ValueError("invalid projected visual triangle payload")
    exact_vertices: list[tuple[float, float, float]] = []
    for raw_vertex in raw_vertices:
        if (
            not isinstance(raw_vertex, list)
            or len(raw_vertex) != 3
            or any(isinstance(value, bool) for value in raw_vertex)
        ):
            raise ValueError("invalid projected visual triangle payload")
        try:
            vertex = tuple(float(value) for value in raw_vertex)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid projected visual triangle payload") from exc
        if not all(isfinite(value) for value in vertex):
            raise ValueError("invalid projected visual triangle payload")
        exact_vertices.append(vertex)
    surface_type = str(triangle.get("surface_type") or "")
    if not surface_type.startswith("profiled_"):
        raise ValueError("invalid projected visual surface type")
    record = {
        "role": str(triangle.get("role") or ""),
        "volume_role": str(triangle.get("volume_role") or ""),
        "verb": str(triangle.get("verb") or ""),
        "surface_type": surface_type,
        "vertices_m": [list(vertex) for vertex in exact_vertices],
        "operator": str(triangle.get("operator") or ""),
        "semantic_patch_id": str(triangle.get("semantic_patch_id") or ""),
    }
    return record, exact_vertices


def _task1_visual_hash(triangles: list[dict[str, Any]]) -> str:
    payload = [
        {
            "role": triangle["role"],
            "volume_role": triangle["volume_role"],
            "surface_type": triangle["surface_type"],
            "semantic_patch_id": triangle["semantic_patch_id"],
            "vertices": [
                [round(float(x), 8), round(float(y), 8), round(float(z), 8)]
                for x, y, z in triangle["vertices_m"]
            ],
        }
        for triangle in triangles
    ]
    return hashlib.sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _final_authority_geometry_hash(
    triangles: list[dict[str, Any]],
    *,
    certificate: dict[str, Any],
) -> str:
    """Recompute compiler mesh identity from exact centroid-local surfaces."""

    raw_origin = certificate.get("source_footprint_centroid_utm")
    if (
        not isinstance(raw_origin, list)
        or len(raw_origin) != 2
        or any(isinstance(value, bool) for value in raw_origin)
    ):
        raise ValueError("invalid final floorwise visual authority certificate")
    try:
        origin_x, origin_y = (float(value) for value in raw_origin)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "invalid final floorwise visual authority certificate"
        ) from exc
    if not all(isfinite(value) for value in (origin_x, origin_y)):
        raise ValueError("invalid final floorwise visual authority certificate")
    canonical = []
    for triangle in triangles:
        points = sorted(
            (
                round(float(vertex[0]) + origin_x, 5),
                round(float(vertex[1]) + origin_y, 5),
                round(float(vertex[2]), 5),
            )
            for vertex in triangle["vertices_m"]
        )
        canonical.append(points)
    canonical.sort()
    return hashlib.sha256(json.dumps(
        canonical,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def final_floorwise_visual_geometry_hash(source: Any) -> str:
    """Return the compiler-style identity of the exact final visual mesh."""

    surfaces = tuple(getattr(source, "surfaces", ()) or ())
    footprint = getattr(source, "footprint", None)
    origin = getattr(footprint, "centroid", None)
    if not surfaces or origin is None:
        raise ValueError("final floorwise visual source is incomplete")
    triangles = [
        _surface_triangle_record(surface)
        for surface in surfaces
    ]
    return _final_authority_geometry_hash(
        triangles,
        certificate={
            "source_footprint_centroid_utm": [
                float(origin.x),
                float(origin.y),
            ],
        },
    )


def _source_surface_payload_hash_from_triangles(
    triangles: list[dict[str, Any]],
) -> str:
    records = tuple(
        json.dumps(
            {
                "operator": triangle["operator"],
                "role": triangle["role"],
                "semantic_patch_id": triangle["semantic_patch_id"],
                "surface_type": triangle["surface_type"],
                "verb": triangle["verb"],
                "vertices_m": [
                    [float(x), float(y), float(z)]
                    for x, y, z in triangle["vertices_m"]
                ],
                "volume_role": triangle["volume_role"],
            },
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        for triangle in triangles
    )
    return hashlib.sha256(
        f"[{','.join(sorted(records))}]".encode("utf-8")
    ).hexdigest()


def _canonical_payload_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def semantic_audit_payload_hash(audit: dict[str, Any]) -> str:
    """Return the canonical hash used to externally anchor a semantic audit."""

    return _canonical_payload_hash(audit)


__all__ = [
    "AUTHORED_COORDINATE_SPACE",
    "CAPACITY_PROGRAM_ROLE",
    "COORDINATE_SPACE",
    "PROJECTED_AUTHORITY",
    "FINAL_AUTHORITY_CERTIFICATION_MODE",
    "ValidatedProjectedVisual",
    "declares_projected_visual_binding",
    "exact_triangle_payload_hash",
    "final_floorwise_visual_geometry_hash",
    "semantic_audit_payload_hash",
    "serialize_certified_projected_visual",
    "validate_projected_visual_artifact",
]
