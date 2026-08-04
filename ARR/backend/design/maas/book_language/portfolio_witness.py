"""Failure evidence for strict MASS portfolios without false publication."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable


def _certified_witness_visual_authority(
    feature: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    properties = (
        feature.get("properties")
        if isinstance(feature, dict)
        and isinstance(feature.get("properties"), dict)
        else {}
    )
    surfaces = properties.get("source_surfaces")
    surfaces = surfaces if isinstance(surfaces, list) else []
    certified_surfaces = [item for item in surfaces if isinstance(item, dict)]
    profiled_surfaces = [
        item for item in certified_surfaces
        if str(item.get("surface_type") or "").startswith("profiled_")
    ]
    certificate = properties.get("floorwise_visual_projection")
    if not isinstance(certificate, dict):
        model = properties.get("maas_model")
        model = model if isinstance(model, dict) else {}
        certificate = model.get("floorwise_visual_projection")
    certificate = certificate if isinstance(certificate, dict) else {}
    artifact = properties.get("geometry_artifact")
    artifact = artifact if isinstance(artifact, dict) else {}
    visual_hash = str(certificate.get("visual_hash") or "")
    artifact_hash = str(artifact.get("projectedVisualGeometryHash") or "")
    artifact_hash_matches = bool(
        artifact_hash and visual_hash and artifact_hash == visual_hash
    )
    authority = {
        "schema_version": str(certificate.get("schema_version") or ""),
        "status": str(certificate.get("status") or ""),
        "hard_pass": certificate.get("hard_pass") is True,
        "visual_hash_present": bool(visual_hash),
        "projected_surface_count": int(
            certificate.get("projected_surface_count") or 0
        ),
        "source_surface_count": len(certified_surfaces),
        "profiled_surface_count": len(profiled_surfaces),
        "artifact_hash_matches": artifact_hash_matches,
    }
    hard_pass = bool(
        authority["schema_version"]
        == "arr.maas.floorwise_visual_projection.v1"
        and authority["status"] == "certified"
        and authority["hard_pass"]
        and authority["visual_hash_present"]
        and authority["projected_surface_count"]
        == authority["source_surface_count"]
        and authority["profiled_surface_count"] > 0
        and (not artifact or artifact_hash_matches)
    )
    return hard_pass, authority


def persist_portfolio_witness(
    output_dir: Path,
    *,
    program_slug: str,
    target_count: int,
    selected_count: int,
    records: Iterable[dict[str, Any]],
    features: Iterable[dict[str, Any]],
    failure_histogram: dict[str, int],
    renderer: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Persist a clearly non-publishable board when strict selection fails."""

    if int(selected_count) >= int(target_count):
        return {
            "schema_version": "arr.maas.portfolio_witness.v1",
            "status": "not_required",
            "publishable": False,
            "target_count": int(target_count),
            "selected_count": int(selected_count),
        }

    normalized_records = [deepcopy(record) for record in records]
    candidate_features = [deepcopy(feature) for feature in features]
    normalized_features: list[dict[str, Any]] = []
    feature_exclusions: list[dict[str, Any]] = []
    for index, feature in enumerate(candidate_features):
        properties = feature.setdefault("properties", {})
        record = (
            normalized_records[index]
            if index < len(normalized_records)
            else {}
        )
        properties["portfolio_witness"] = {
            "candidate_id": str(record.get("candidate_id") or ""),
            "publishable": False,
            "status": str(record.get("status") or "diagnostic"),
            "failure_reasons": list(record.get("failure_reasons") or ()),
        }
        certified, authority = _certified_witness_visual_authority(feature)
        if certified:
            normalized_features.append(feature)
            continue
        exclusion = {
            "candidate_id": str(record.get("candidate_id") or ""),
            "feature_index": index,
            "reason": "witness_feature_uncertified_authored_visual",
            "authority": authority,
        }
        feature_exclusions.append(exclusion)
        if index < len(normalized_records):
            normalized_records[index]["witness_feature_exclusion"] = deepcopy(
                exclusion
            )

    directory = Path(output_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    board = directory / f"maas-book-{program_slug}-{int(target_count)}-witness.png"
    manifest = directory / f"maas-book-{program_slug}-{int(target_count)}-witness.json"
    if renderer is None and normalized_features:
        from design.maas.program_massing.benchmark import render_archive_sheet

        renderer = render_archive_sheet
    if normalized_features:
        assert renderer is not None
        renderer(
            normalized_features,
            board,
            title=(
                f"MAAS {program_slug} - {len(normalized_features)} WITNESSES - "
                f"NOT SELECTED / NOT PUBLISHABLE"
            ),
        )
    evidence = {
        "schema_version": "arr.maas.portfolio_witness.v1",
        "status": "failed_portfolio_witness",
        "publishable": False,
        "target_count": int(target_count),
        "selected_count": int(selected_count),
        "candidate_count": len(normalized_records),
        "rendered_candidate_count": len(normalized_features),
        "excluded_feature_count": len(feature_exclusions),
        "feature_exclusions": feature_exclusions,
        "failure_histogram": {
            str(key): int(value)
            for key, value in sorted(failure_histogram.items())
        },
        "records": normalized_records,
        "board_path": str(board) if normalized_features else "",
        "board_sha256": (
            sha256(board.read_bytes()).hexdigest()
            if normalized_features
            else ""
        ),
        "manifest_path": str(manifest),
    }
    manifest.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return evidence


__all__ = ["persist_portfolio_witness"]
