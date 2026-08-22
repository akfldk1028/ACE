"""Deterministically promote invalidated v1 test sites into development."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from .io import sha256_json


REGISTRY_SCHEMA = "ace.iclr2027.site_registry.v1"
CANDIDATE_SOURCE_SCHEMA = "ace.iclr2027.candidate_source.v1"
AMENDMENT_SCHEMA = "ace.iclr2027.development_amendment.v1"
AMENDMENT_RULE = "all_v1_test_sites_passing_v2_nonoutcome_eligibility.v1"
PROTOCOL_MAX_PARCEL_AREA_M2 = 30_000.0
EXPECTED_BUNDLE_COUNTS = {
    "dev.native": 15,
    "dev.challenged": 15,
    "test.native": 15,
    "test.challenged": 15,
}

_PNU = re.compile(r"^[0-9]{19}$")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return copy.deepcopy(dict(value))


def _selection(registry: Mapping[str, Any], label: str) -> dict[str, Any]:
    return _object(registry.get("selection"), f"{label} selection")


def _required_sha256(value: str, label: str) -> str:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{label} must be a 64-character SHA-256")
    return value.lower()


def _pnu_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _PNU.fullmatch(value):
        raise ValueError(f"{label} must contain exactly 19 digits")
    return value


def _index_by_pnu(
    records: Any,
    *,
    label: str,
) -> dict[str, dict[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise ValueError(f"{label} must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for raw in records:
        record = _object(raw, f"{label} entry")
        pnu = _pnu_value(record.get("pnu"), f"{label} PNU")
        if pnu in indexed:
            raise ValueError(f"duplicate {label} PNU")
        indexed[pnu] = record
    return indexed


def _selected_pnus(selection: Mapping[str, Any], label: str) -> tuple[str, ...]:
    raw = selection.get("selected_pnus")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{label} selected_pnus must be a list")
    pnus = tuple(_pnu_value(value, f"{label} selected PNU") for value in raw)
    if len(pnus) != len(set(pnus)):
        raise ValueError(f"duplicate {label} selected PNU")
    return pnus


def _site_identity(site: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): copy.deepcopy(value)
        for key, value in site.items()
        if key != "artifacts"
    }


def _eligibility_failure(
    candidate: Mapping[str, Any],
    *,
    max_parcel_area_m2: float,
) -> str | None:
    if candidate.get("boundary_available") is not True:
        return "boundary_unavailable"
    if candidate.get("law_available") is not True:
        return "law_unavailable"
    if candidate.get("parking_available") is not True:
        return "parking_unavailable"
    try:
        area = float(candidate.get("parcel_area_m2"))
    except (TypeError, ValueError) as exc:
        raise ValueError("candidate parcel area must be numeric") from exc
    if area <= 0:
        raise ValueError("candidate parcel area must be positive")
    if area > max_parcel_area_m2:
        return "parcel_area_out_of_scope"
    return None


def _source_test_order(
    archived_sites: Mapping[str, Mapping[str, Any]],
    archived_selection: Mapping[str, Any],
) -> tuple[str, ...]:
    selected = _selected_pnus(archived_selection, "archived registry")
    archived_test = {
        pnu for pnu, site in archived_sites.items() if site.get("split") == "test"
    }
    if set(selected) != archived_test:
        raise ValueError("archived selected_pnus do not match archived test sites")
    return selected


def _current_test_order(
    current_sites: Mapping[str, Mapping[str, Any]],
    current_selection: Mapping[str, Any],
) -> tuple[str, ...]:
    selected = _selected_pnus(current_selection, "current registry")
    current_test = {
        pnu for pnu, site in current_sites.items() if site.get("split") == "test"
    }
    if set(selected) != current_test:
        raise ValueError("current selected_pnus do not match final v2 test sites")
    return selected


def _promotion_inventory(
    source_order: Sequence[str],
    archived_sites: Mapping[str, Mapping[str, Any]],
    candidates: Mapping[str, Mapping[str, Any]],
    *,
    max_parcel_area_m2: float,
) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    promoted: list[tuple[int, str]] = []
    excluded: list[tuple[int, str]] = []
    for rank, pnu in enumerate(source_order, start=1):
        candidate = candidates.get(pnu)
        if candidate is None:
            raise ValueError("archived test site is missing from candidate source")
        source_area = float(archived_sites[pnu].get("parcel_area_m2") or 0.0)
        candidate_area = float(candidate.get("parcel_area_m2") or 0.0)
        if source_area <= 0 or source_area != candidate_area:
            raise ValueError("archived and candidate parcel areas do not match")
        failure = _eligibility_failure(
            candidate,
            max_parcel_area_m2=max_parcel_area_m2,
        )
        if failure is None:
            promoted.append((rank, pnu))
        else:
            excluded.append((rank, failure))
    return promoted, excluded


def _amendment_record(
    *,
    base_registry_version: str,
    archived_registry_version: str,
    source_registry_path: str,
    source_registry_sha256: str,
    candidate_source_sha256: str,
    declared_date: str,
    max_parcel_area_m2: float,
    promoted: Sequence[tuple[int, str]],
    excluded: Sequence[tuple[int, str]],
    development_pnus: Sequence[str],
    expected_promoted_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": AMENDMENT_SCHEMA,
        "rule_id": AMENDMENT_RULE,
        "declared_date": declared_date,
        "base_registry_version": base_registry_version,
        "source_registry_path": source_registry_path,
        "source_registry_sha256": source_registry_sha256,
        "source_registry_version": archived_registry_version,
        "candidate_source_sha256": candidate_source_sha256,
        "selection_fields": [
            "archived_registry.sites[].split",
            "candidate_source.candidates[].parcel_area_m2",
            "candidate_source.candidates[].boundary_available",
            "candidate_source.candidates[].law_available",
            "candidate_source.candidates[].parking_available",
        ],
        "max_parcel_area_m2": float(max_parcel_area_m2),
        "include_all_matches": True,
        "expected_promoted_count": expected_promoted_count,
        "promoted_source_ranks": [rank for rank, _ in promoted],
        "promoted_pnus": [pnu for _, pnu in promoted],
        "promoted_pnus_sha256": sha256_json(sorted(pnu for _, pnu in promoted)),
        "development_pnus_sha256": sha256_json(sorted(development_pnus)),
        "excluded_source_ranks": [rank for rank, _ in excluded],
        "excluded": [
            {"source_rank": rank, "reason": reason} for rank, reason in excluded
        ],
        "excluded_reason_counts": dict(
            sorted(Counter(reason for _, reason in excluded).items())
        ),
    }


def _version(
    *,
    base_selection: Mapping[str, Any],
    base_registry_version: str,
    amendment: Mapping[str, Any],
    sites: Sequence[Mapping[str, Any]],
    declared_date: str,
) -> str:
    identity = {
        "schema_version": REGISTRY_SCHEMA,
        "protocol_revision": 2,
        "base_registry_version": base_registry_version,
        "base_selection": base_selection,
        "development_amendment": amendment,
        "expected_bundle_counts": EXPECTED_BUNDLE_COUNTS,
        "sites": [_site_identity(site) for site in sites],
    }
    compact_date = declared_date.replace("-", "")
    return f"selection-{compact_date}-{sha256_json(identity)[:12]}"


def derive_development_amendment(
    current_registry: Mapping[str, Any],
    archived_registry: Mapping[str, Any],
    candidate_source: Mapping[str, Any],
    *,
    source_registry_path: str,
    source_registry_sha256: str,
    candidate_source_sha256: str,
    max_parcel_area_m2: float = PROTOCOL_MAX_PARCEL_AREA_M2,
    expected_promoted_count: int = 3,
    declared_date: str = "2026-08-19",
) -> dict[str, Any]:
    """Return a protocol-amended registry without mutating any input."""

    current = _object(current_registry, "current registry")
    archived = _object(archived_registry, "archived registry")
    candidate_payload = _object(candidate_source, "candidate source")
    if current.get("schema_version") != REGISTRY_SCHEMA:
        raise ValueError("unsupported current registry schema")
    if archived.get("schema_version") != REGISTRY_SCHEMA:
        raise ValueError("unsupported archived registry schema")
    if candidate_payload.get("schema_version") != CANDIDATE_SOURCE_SCHEMA:
        raise ValueError("unsupported candidate source schema")
    if current.get("frozen") is True:
        raise ValueError("current registry is frozen")
    if (
        type(max_parcel_area_m2) not in {int, float}
        or float(max_parcel_area_m2) != PROTOCOL_MAX_PARCEL_AREA_M2
    ):
        raise ValueError("protocol max_parcel_area_m2 must equal 30000.0")
    max_parcel_area_m2 = PROTOCOL_MAX_PARCEL_AREA_M2
    if expected_promoted_count <= 0:
        raise ValueError("expected_promoted_count must be positive")
    date.fromisoformat(declared_date)
    source_registry_sha256 = _required_sha256(
        source_registry_sha256, "source_registry_sha256"
    )
    candidate_source_sha256 = _required_sha256(
        candidate_source_sha256, "candidate_source_sha256"
    )
    source_registry_path = str(source_registry_path).replace("\\", "/").strip()
    if not source_registry_path:
        raise ValueError("source_registry_path must be nonempty")

    current_selection = _selection(current, "current registry")
    archived_selection = _selection(archived, "archived registry")
    if (
        str(current_selection.get("candidate_source_sha256") or "").lower()
        != candidate_source_sha256
        or str(archived_selection.get("candidate_source_sha256") or "").lower()
        != candidate_source_sha256
    ):
        raise ValueError("candidate source hash is not bound by both registries")

    current_sites = _index_by_pnu(current.get("sites"), label="current site")
    archived_sites = _index_by_pnu(archived.get("sites"), label="archived site")
    candidates = _index_by_pnu(
        candidate_payload.get("candidates"), label="candidate"
    )
    if any(site.get("split") not in {"dev", "test"} for site in current_sites.values()):
        raise ValueError("current site has unsupported split")
    source_order = _source_test_order(archived_sites, archived_selection)
    test_order = _current_test_order(current_sites, current_selection)
    promoted, excluded = _promotion_inventory(
        source_order,
        archived_sites,
        candidates,
        max_parcel_area_m2=max_parcel_area_m2,
    )
    if len(promoted) != expected_promoted_count:
        raise ValueError(
            f"expected {expected_promoted_count} eligible promotions, found {len(promoted)}"
        )
    promoted_pnus = tuple(pnu for _, pnu in promoted)
    current_test_pnus = set(test_order)
    if current_test_pnus.intersection(promoted_pnus):
        raise ValueError("development promotion overlaps final v2 test")

    existing = current_selection.get("development_amendment")
    current_dev_pnus = {
        pnu for pnu, site in current_sites.items() if site.get("split") == "dev"
    }
    promoted_set = set(promoted_pnus)
    if existing is None and current_dev_pnus.intersection(promoted_set):
        raise ValueError("development promotion overlaps current development sites")
    base_dev_pnus = current_dev_pnus - promoted_set
    expected_dev_site_count = EXPECTED_BUNDLE_COUNTS["dev.native"] // 3
    if len(base_dev_pnus) + len(promoted) != expected_dev_site_count:
        raise ValueError(
            f"expected {expected_dev_site_count} development sites after amendment"
        )
    if len(test_order) != EXPECTED_BUNDLE_COUNTS["test.native"] // 3:
        raise ValueError("expected 5 final v2 test sites")

    base_registry_version = (
        str(existing.get("base_registry_version") or "")
        if isinstance(existing, Mapping)
        else str(current.get("version") or "")
    )
    if not base_registry_version:
        raise ValueError("base registry version must be nonempty")
    archived_registry_version = str(archived.get("version") or "").strip()
    if not archived_registry_version:
        raise ValueError("archived registry version must be nonempty")
    development_pnus = tuple(sorted((*base_dev_pnus, *promoted_pnus)))
    amendment = _amendment_record(
        base_registry_version=base_registry_version,
        archived_registry_version=archived_registry_version,
        source_registry_path=source_registry_path,
        source_registry_sha256=source_registry_sha256,
        candidate_source_sha256=candidate_source_sha256,
        declared_date=declared_date,
        max_parcel_area_m2=max_parcel_area_m2,
        promoted=promoted,
        excluded=excluded,
        development_pnus=development_pnus,
        expected_promoted_count=expected_promoted_count,
    )

    promoted_sites: list[dict[str, Any]] = []
    for rank, pnu in promoted:
        site = copy.deepcopy(archived_sites[pnu])
        site["split"] = "dev"
        site["artifacts"] = {}
        site["development_origin"] = {
            "kind": "promoted_invalidated_v1_test",
            "source_registry_version": archived_registry_version,
            "source_selection_rank": rank,
        }
        promoted_sites.append(site)
    base_dev_sites = [copy.deepcopy(current_sites[pnu]) for pnu in sorted(base_dev_pnus)]
    test_sites = [copy.deepcopy(current_sites[pnu]) for pnu in test_order]
    ordered_sites = [*base_dev_sites, *promoted_sites, *test_sites]
    base_selection = copy.deepcopy(current_selection)
    base_selection.pop("development_amendment", None)
    expected_version = _version(
        base_selection=base_selection,
        base_registry_version=base_registry_version,
        amendment=amendment,
        sites=ordered_sites,
        declared_date=declared_date,
    )

    if existing is not None:
        expected_by_pnu = {site["pnu"]: site for site in promoted_sites}
        existing_promotions = promoted_set.intersection(current_dev_pnus)
        valid = (
            isinstance(existing, Mapping)
            and dict(existing) == amendment
            and existing_promotions == promoted_set
            and current.get("protocol_revision") == 2
            and current.get("expected_bundle_counts") == EXPECTED_BUNDLE_COUNTS
            and current.get("version") == expected_version
        )
        if valid:
            for pnu, expected_site in expected_by_pnu.items():
                actual_identity = _site_identity(current_sites[pnu])
                if actual_identity != _site_identity(expected_site):
                    valid = False
                    break
        if not valid:
            raise ValueError("existing development amendment does not match protocol")
        return current

    output = copy.deepcopy(current)
    output["protocol_revision"] = 2
    output["expected_bundle_counts"] = copy.deepcopy(EXPECTED_BUNDLE_COUNTS)
    output["sites"] = ordered_sites
    output_selection = copy.deepcopy(base_selection)
    output_selection["development_amendment"] = amendment
    output["selection"] = output_selection
    output["version"] = expected_version
    return output


def amend_development_registry(
    registry_path: Path,
    archived_registry_path: Path,
    candidate_source_path: Path,
    *,
    expected_archived_registry_sha256: str,
    expected_candidate_source_sha256: str,
    output_registry_path: Path | None = None,
    max_parcel_area_m2: float = PROTOCOL_MAX_PARCEL_AREA_M2,
    expected_promoted_count: int = 3,
    declared_date: str = "2026-08-19",
) -> dict[str, Any]:
    """Load, hash-bind, and derive an amended registry without writing it."""

    output_registry_path = (
        registry_path if output_registry_path is None else output_registry_path
    )

    for path, label in (
        (registry_path, "current registry"),
        (archived_registry_path, "archived registry"),
        (candidate_source_path, "candidate source"),
    ):
        if not path.is_file():
            raise ValueError(f"{label} must be a file")
    output_resolved = output_registry_path.resolve()
    if output_resolved in {
        archived_registry_path.resolve(),
        candidate_source_path.resolve(),
    }:
        raise ValueError("output registry collides with an immutable source")
    expected_archive = _required_sha256(
        expected_archived_registry_sha256,
        "expected_archived_registry_sha256",
    )
    expected_candidate = _required_sha256(
        expected_candidate_source_sha256,
        "expected_candidate_source_sha256",
    )
    archive_bytes = archived_registry_path.read_bytes()
    candidate_bytes = candidate_source_path.read_bytes()
    actual_archive = hashlib.sha256(archive_bytes).hexdigest()
    actual_candidate = hashlib.sha256(candidate_bytes).hexdigest()
    if actual_archive != expected_archive:
        raise ValueError("archived registry SHA-256 mismatch")
    if actual_candidate != expected_candidate:
        raise ValueError("candidate source SHA-256 mismatch")
    current = json.loads(registry_path.read_text(encoding="utf-8"))
    archived = json.loads(archive_bytes.decode("utf-8"))
    candidate_source = json.loads(candidate_bytes.decode("utf-8"))
    try:
        source_label = os.path.relpath(
            archived_registry_path.resolve(), output_registry_path.parent.resolve()
        ).replace("\\", "/")
    except ValueError as exc:
        raise ValueError("archived registry needs an output-relative path") from exc
    return derive_development_amendment(
        current,
        archived,
        candidate_source,
        source_registry_path=source_label,
        source_registry_sha256=actual_archive,
        candidate_source_sha256=actual_candidate,
        max_parcel_area_m2=max_parcel_area_m2,
        expected_promoted_count=expected_promoted_count,
        declared_date=declared_date,
    )
