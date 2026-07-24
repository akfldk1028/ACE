"""Provider-neutral generation of one facade proposal for one locked MASS."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any
import uuid

from design.maas.aesthetic.contracts import AestheticProvider, RenderedReference


def generate_elevation_image_proposal(
    bundle: dict[str, Any],
    mass_preview: str | Path,
    *,
    adapter: AestheticProvider,
    strategy: dict[str, Any],
) -> dict[str, Any]:
    """Call the injected provider exactly once and persist ALT 01 evidence."""

    if str(bundle.get("status") or "") != "generated":
        raise ValueError("image proposal requires a generated elevation bundle")
    identity = {
        "execution_id": str(bundle.get("execution_id") or ""),
        "program_hash": str(bundle.get("program_hash") or ""),
        "geometry_hash": str(bundle.get("geometry_hash") or ""),
    }
    if not all(identity.values()):
        raise ValueError("image proposal requires complete execution identity")
    preview = Path(mass_preview).resolve()
    if not preview.is_file():
        raise ValueError(f"MASS preview does not exist: {preview}")
    elevation_root = Path(str(bundle.get("output_directory") or "")).resolve()
    proposal_root = elevation_root / "proposals" / "alt-01"
    proposal_root.mkdir(parents=True, exist_ok=True)
    manifest_path = proposal_root / "proposal.json"
    input_sha256 = _sha256(preview)
    views = [
        {
            "view": str(row.get("view") or ""),
            "path": str(row.get("path") or ""),
            "sha256": str(row.get("sha256") or ""),
        }
        for row in bundle.get("views") or ()
        if isinstance(row, dict)
    ]
    job = {
        "schema_version": "arr.elevation_agent.image_job.v1",
        "source_bundle_id": identity["execution_id"],
        "candidate_id": identity["geometry_hash"],
        "identity": identity,
        "strategy": strategy,
        "locked_evidence": {
            "mass_preview_sha256": input_sha256,
            "condition_pack_path": str(bundle.get("condition_pack_path") or ""),
            "views": views,
        },
        "prompt": {
            "prompt": (
                f"Facade system: {strategy.get('primary_system')}. "
                f"Rhythm: {strategy.get('rhythm')}. "
                f"Opening logic: {strategy.get('opening_logic')}. "
                "Apply facade materials and openings to the exact supplied MASS. "
                "The MASS geometry, silhouette, roofline, setbacks, voids, bridges, "
                "cantilevers, proportions and camera panel layout are immutable."
            ),
            "negative_prompt": (
                "changed silhouette, changed mass, extra volume, removed volume, "
                "changed roofline, changed height, floating fragments, warped site"
            ),
        },
    }
    reference = RenderedReference(
        asset_id=f"asset:maas:{identity['execution_id']}:locked-preview",
        uri=str(preview),
        metadata={
            "reference_type": "locked_mass_sheet",
            "identity": identity,
            "sha256": input_sha256,
            "condition_pack_path": str(bundle.get("condition_pack_path") or ""),
            "views": views,
            "geometry_mutation_allowed": False,
        },
    )

    provider_result = adapter.generate(job, reference)
    payload: dict[str, Any] = {
        "schema_version": "arr.elevation_agent.image_proposal.v1",
        "status": str(provider_result.status or "failed"),
        "identity": identity,
        "strategy": strategy,
        "provider": str(provider_result.provider or getattr(adapter, "name", "")),
        "provider_metadata": dict(provider_result.metadata or {}),
        "issues": list(provider_result.issues or ()),
        "input_reference": {
            "path": str(preview),
            "sha256": input_sha256,
        },
        "condition_pack_path": str(bundle.get("condition_pack_path") or ""),
        "view_count": len(views),
        "request_count": 1,
        "retry_count": 0,
        "manifest_path": str(manifest_path),
        "artifact": {},
    }
    asset = next(
        (row for row in provider_result.assets or () if isinstance(row, dict)),
        None,
    )
    if provider_result.status == "complete" and asset:
        asset_uri = str(asset.get("uri") or "")
        source = Path(asset_uri).resolve()
        if source.is_file():
            artifact_path = proposal_root / "proposal.png"
            if source != artifact_path:
                shutil.copy2(source, artifact_path)
            payload["artifact"] = {
                "asset_id": str(asset.get("asset_id") or ""),
                "path": str(artifact_path),
                "sha256": _sha256(artifact_path),
                "media_type": str(asset.get("media_type") or "image/png"),
                "preview_url": (
                    "/design/maas/single-executions/"
                    f"{identity['execution_id']}/elevation-proposals/alt-01/"
                ),
            }
        else:
            payload["artifact"] = {
                "asset_id": str(asset.get("asset_id") or ""),
                "uri": asset_uri,
                "sha256": "",
                "media_type": str(asset.get("media_type") or "image/png"),
                "preview_url": "",
            }
    _write_json_atomic(manifest_path, payload)
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(f"{path.suffix}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


__all__ = ["generate_elevation_image_proposal"]
