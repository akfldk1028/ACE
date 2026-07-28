"""Canonical transport contract for Task 1 certified projected visual meshes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from typing import Any


MESH_SCHEMA = "arr.maas.projected_visual_mesh.v1"
CERTIFICATE_SCHEMA = "arr.maas.floorwise_visual_projection.v1"
COORDINATE_SPACE = "capacity_source_centroid_local_xy_normalized_z"
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


def serialize_certified_projected_visual(source: Any) -> dict[str, Any]:
    """Serialize exact triangle records while retaining Task 1 visual identity."""

    metadata = (
        source.metadata
        if isinstance(getattr(source, "metadata", None), dict)
        else {}
    )
    certificate = metadata.get("floorwise_visual_projection")
    if not isinstance(certificate, dict):
        return {}
    if certificate.get("status") == "not_applicable_no_authored_mesh":
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
    if coordinate_space != COORDINATE_SPACE:
        raise ValueError("unsupported projected visual coordinate frame")
    payload_hash = exact_triangle_payload_hash(triangles)
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


def declares_projected_visual_binding(artifact: dict[str, Any]) -> bool:
    """Return true for complete bindings and for downgrade/tamper markers."""

    return (
        any(field in artifact for field in PROJECTED_FIELDS)
        or artifact.get("authority") == PROJECTED_AUTHORITY
        or artifact.get("geometryProgramRole") == CAPACITY_PROGRAM_ROLE
    )


def validate_projected_visual_artifact(
    artifact: dict[str, Any],
) -> ValidatedProjectedVisual | None:
    """Validate and hydrate one complete binding; only true legacy returns None."""

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
        or mesh.get("coordinateSpace") != COORDINATE_SPACE
        or certificate.get("projected_surface_coordinate_frame")
        != COORDINATE_SPACE
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

    normalized: list[dict[str, Any]] = []
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for triangle in triangle_payload:
        record, exact_vertices = _validated_triangle_record(triangle)
        base_index = len(vertices)
        vertices.extend(exact_vertices)
        triangles.append((base_index, base_index + 1, base_index + 2))
        normalized.append(record)

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
        coordinate_space=COORDINATE_SPACE,
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


def _validate_certificate_status(certificate: dict[str, Any]) -> None:
    if (
        certificate.get("schema_version") != CERTIFICATE_SCHEMA
        or certificate.get("status") != "certified"
        or certificate.get("hard_pass") is not True
    ):
        raise ValueError("selected floorwise visual projection is not certified")


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


__all__ = [
    "CAPACITY_PROGRAM_ROLE",
    "COORDINATE_SPACE",
    "PROJECTED_AUTHORITY",
    "ValidatedProjectedVisual",
    "declares_projected_visual_binding",
    "exact_triangle_payload_hash",
    "serialize_certified_projected_visual",
    "validate_projected_visual_artifact",
]
