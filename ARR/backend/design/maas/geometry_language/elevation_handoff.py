"""Hash-bound handoff from an executed GeometryProgram MASS to elevation work."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid
from typing import Any

from .executed_archive import (
    compile_executed_mass,
    executed_mass_manifest,
    materialize_executed_mass_passport,
    materialize_executed_mass_preview,
)


SCHEMA_VERSION = "arr.maas.elevation_handoff.v1"


def build_executed_mass_elevation_handoff(*, run_id: str, index: int) -> dict[str, Any]:
    """Validate one archived projected mesh and expose immutable elevation inputs.

    This packet does not claim that elevations were generated. It closes the
    identity/mesh boundary without promoting the capacity replay program to
    renderer-visible geometry authority.
    """

    compilation, artifact, row, _archive_path = compile_executed_mass(index, run_id)
    passport = materialize_executed_mass_passport(index, run_id)
    manifest = executed_mass_manifest(run_id)
    preview = materialize_executed_mass_preview(index, run_id).resolve()
    vlm = artifact.get("vlmAudit") if isinstance(artifact.get("vlmAudit"), dict) else {}
    identity = artifact.get("identity") if isinstance(artifact.get("identity"), dict) else {}
    projected_visual_mesh = (
        artifact.get("projectedVisualMesh")
        if isinstance(artifact.get("projectedVisualMesh"), dict)
        else {}
    )
    projected_visual_certificate = (
        artifact.get("projectedVisualCertificate")
        if isinstance(artifact.get("projectedVisualCertificate"), dict)
        else {}
    )
    geometry_hash = str(compilation.geometry_hash or identity.get("geometryHash") or "")
    program_hash = compilation.program.program_hash()
    handoff_id = hashlib.sha256(
        f"{run_id}|{index}|{program_hash}|{geometry_hash}".encode("utf-8")
    ).hexdigest()
    program_fit = vlm.get("program_fit_hard_pass")
    return {
        "schema_version": SCHEMA_VERSION,
        "handoff_id": f"elevation:{handoff_id[:24]}",
        "identity": {
            "run_id": str(run_id),
            "mass_index": int(index),
            "variant_id": str(row.get("variant_id") or f"maas_{int(index):02d}"),
            "pnu": str(manifest.get("pnu") or ""),
            "program_hash": program_hash,
            "geometry_hash": geometry_hash,
        },
        "authority": {
            "source": "validated_archived_projected_visual_mesh",
            "geometry_hash_replay_match": (
                geometry_hash
                == str(artifact.get("projectedVisualGeometryHash") or "")
                == str(identity.get("geometryHash") or "")
            ),
            "projected_visual_certificate_hard_pass": (
                projected_visual_certificate.get("hard_pass") is True
            ),
            "capacity_replay_program_visual_authority": False,
            "base_relative_parametric_geometry": False,
            "facade_may_not_modify_mass_geometry": True,
        },
        "geometry_program": compilation.program.to_dict(),
        "geometry_program_role": "capacity_replay_metadata_and_provenance",
        "projected_visual_certificate": projected_visual_certificate,
        "indexed_triangle_mesh": {
            "coordinate_space": str(
                projected_visual_mesh.get("coordinateSpace") or "local_model_m"
            ),
            "vertices": [list(vertex) for vertex in compilation.vertices],
            "triangles": [list(face) for face in compilation.triangles],
            "vertex_count": len(compilation.vertices),
            "triangle_count": len(compilation.triangles),
            "metrics": compilation.metrics,
        },
        "visual_evidence": {
            "actual_mass_preview_path": str(preview),
            "actual_mass_preview_sha256": hashlib.sha256(preview.read_bytes()).hexdigest(),
            "individual_vlm_evaluated": bool(vlm),
            "individual_vlm_model": str(vlm.get("model") or ""),
            "individual_vlm_response_id": str(vlm.get("response_id") or ""),
            "individual_vlm_program_fit_hard_pass": program_fit,
            "individual_vlm_actions": [str(value) for value in vlm.get("critic_actions") or ()],
            "vlm_image_inputs": vlm.get("vlm_image_inputs") or {},
        },
        "selection_state": {
            "mass_hard_gates_pass": bool((passport.get("executed_mass") or {}).get("hard_pass")),
            "individual_vlm_program_fit_pass": program_fit is True,
            "approved_for_final_elevation": bool(
                (passport.get("executed_mass") or {}).get("hard_pass")
                and program_fit is True
            ),
            "development_use_allowed": True,
        },
        "elevation_contract": {
            "required_views": ["front", "right", "back", "left", "axon", "top"],
            "required_conditions": [
                "camera_poses", "silhouette", "metric_depth", "surface_normals",
                "floor_guides", "facade_planes", "projection_manifest",
            ],
            "output_identity_fields": ["run_id", "program_hash", "geometry_hash", "handoff_id"],
            "status": "mesh_handoff_ready_condition_pack_adapter_pending",
            "next_adapter": "validated projected visual mesh -> multi-view elevation condition pack",
        },
        "research_memory": {
            "paper_map": "docs/ai-session-memory/maas-aesthetic-texturing/PAPERS.md",
            "implementation_memory": "docs/ai-session-memory/maas-aesthetic-texturing/IMPLEMENTATION_DECISIONS.md",
            "next_steps": "docs/ai-session-memory/maas-aesthetic-texturing/NEXT_STEPS.md",
        },
    }


def write_executed_mass_elevation_handoff(*, run_id: str, index: int, output_path: str | Path) -> Path:
    output = Path(output_path).resolve()
    payload = build_executed_mass_elevation_handoff(run_id=run_id, index=index)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(f"{output.suffix}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return output


__all__ = ["SCHEMA_VERSION", "build_executed_mass_elevation_handoff", "write_executed_mass_elevation_handoff"]
