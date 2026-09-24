from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


TARGET_ROSTER_SCHEMA = "ace.iclr2027.architecture_target_roster.v1"
ALLOCATION = (12, 11, 11)
EVIDENCE_FAMILIES = ("geometry", "law", "parking", "program", "site")

_ROOT_KEYS = frozenset(
    {
        "schema_version",
        "roster_version",
        "projection_identity_commitment",
        "split",
        "site_count",
        "target_count",
        "allocation",
        "sites",
        "targets",
        "roster_sha256",
    }
)
_SITE_KEYS = frozenset({"site_ref", "area_bin"})
_TARGET_KEYS = frozenset(
    {
        "target_ref",
        "site_ref",
        "program",
        "subject_kind",
        "attempt_stage",
        "route_kind",
        "target_spec_sha256",
        "source_ids",
    }
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_PROTECTED_TOKEN_RE = re.compile(
    r"(?:address|challenged|condition|decision|expected|gold|internal|mutation|"
    r"native|outcome|path|pnu|private|secret|uri|url)",
    re.IGNORECASE,
)
_RAW_PNU_RE = re.compile(r"(?<![0-9])[0-9]{19}(?![0-9])")
_URI_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
_WINDOWS_PATH_RE = re.compile(r"^[a-z]:[\\/]", re.IGNORECASE)
_IDENTITY_ALIAS_RE = re.compile(
    r"(?:^|[^a-z0-9])(?:alias|site|law|parking|program|geometry|evidence|condition|"
    r"native|challenged|repeat|prefix|treatment)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)

SOURCE_CAPTURE_SCHEMA = "ace.iclr2027.architecture_source_capture.v1"
SITE_LOCATOR_SCHEMA = "ace.iclr2027.architecture_site_locator.v1"
TARGET_SPEC_SCHEMA = "ace.iclr2027.architecture_target_spec.v1"
GEOMETRY_RECEIPT_SCHEMA = "ace.iclr2027.architecture_geometry_receipt.v1"
BLIND_OVERLAP_CHECK_SCHEMA = "ace.iclr2027.architecture_blind_overlap_check.v1"
LEGACY_BINDINGS_SCHEMA = "ace.iclr2027.architecture_legacy_bindings.v1"
INDEPENDENT_REVIEW_SCHEMA = "ace.iclr2027.architecture_independent_review.v1"
FREEZE_RECEIPT_SCHEMA = "ace.iclr2027.architecture_freeze_receipt.v2"

SOURCE_CAPTURE_KEYS = frozenset(
    {
        "schema_version",
        "source_id",
        "publisher",
        "canonical_uri",
        "retrieved_at",
        "effective_at",
        "media_type",
        "byte_length",
        "sha256",
        "etag",
        "last_modified",
        "license",
        "redistribution_status",
        "evidence_families",
    }
)
SITE_LOCATOR_KEYS = frozenset(
    {
        "schema_version",
        "internal_site_id",
        "pnu",
        "split",
        "area_bin",
        "parcel_geometry_sha256",
        "project_cluster_id",
        "source_capture_ids",
    }
)
TARGET_SPEC_KEYS = frozenset(
    {
        "schema_version",
        "target_ref",
        "normalized_subject_identity",
        "evidence_family_sources",
        "geometry_receipt_sha256",
        "target_spec_sha256",
    }
)
GEOMETRY_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "target_ref",
        "input_geometry_sha256",
        "materializer_code_sha256",
        "output_geometry_sha256",
        "compile_log_sha256",
        "hard_pass",
        "receipt_sha256",
    }
)
BLIND_KEYS = frozenset(
    {
        "schema_version",
        "locator_set_sha256",
        "protected_roster_commitment",
        "overlap_found",
        "checked_site_count",
        "audit_sha256",
        "record_sha256",
    }
)
LEGACY_BINDINGS_KEYS = frozenset(
    {
        "schema_version",
        "registry_version",
        "registry_core_sha256",
        "projection_identity_commitment",
        "split_manifest_sha256",
        "public_registry_sha256",
        "public_case_set_sha256",
        "existing_dev_site_count",
        "existing_dev_target_count",
    }
)
INDEPENDENT_REVIEW_KEYS = frozenset(
    {
        "schema_version",
        "reviewed_target_roster_sha256",
        "reviewed_admission_binding_sha256",
        "status",
        "reviewer_identity_commitment",
        "review_sha256",
    }
)
FREEZE_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "registry_version",
        "registry_core_sha256",
        "projection_identity_commitment",
        "split_manifest_sha256",
        "public_registry_sha256",
        "public_case_set_sha256",
        "site_locator_set_sha256",
        "public_site_set_sha256",
        "public_target_set_sha256",
        "source_capture_set_sha256",
        "target_spec_set_sha256",
        "geometry_receipt_set_sha256",
        "target_roster_sha256",
        "new_site_count",
        "new_target_count",
        "allocation",
        "combined_dev_site_count",
        "combined_dev_target_count",
        "blind_overlap_check_sha256",
        "independent_review_sha256",
        "receipt_sha256",
    }
)


class TargetRosterError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceCaptureV1:
    schema_version: str
    source_id: str
    publisher: str
    canonical_uri: str
    retrieved_at: str
    effective_at: str
    media_type: str
    byte_length: int
    sha256: str
    etag: str
    last_modified: str
    license: str
    redistribution_status: str
    evidence_families: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> SourceCaptureV1:
        return _parse_source_capture(value)


@dataclass(frozen=True, slots=True)
class SiteLocatorV1:
    schema_version: str
    internal_site_id: str
    pnu: str
    split: str
    area_bin: str
    parcel_geometry_sha256: str
    project_cluster_id: str
    source_capture_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> SiteLocatorV1:
        return _parse_site_locator(value)


@dataclass(frozen=True, slots=True)
class TargetSpecV1:
    schema_version: str
    target_ref: str
    normalized_subject_identity: str
    evidence_family_sources: Mapping[str, tuple[str, ...]]
    geometry_receipt_sha256: str
    target_spec_sha256: str

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> TargetSpecV1:
        return _parse_target_spec(value)


@dataclass(frozen=True, slots=True)
class GeometryReceiptV1:
    schema_version: str
    target_ref: str
    input_geometry_sha256: str
    materializer_code_sha256: str
    output_geometry_sha256: str
    compile_log_sha256: str
    hard_pass: bool
    receipt_sha256: str

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> GeometryReceiptV1:
        return _parse_geometry_receipt(value)


@dataclass(frozen=True, slots=True)
class BlindOverlapCheckV1:
    schema_version: str
    locator_set_sha256: str
    protected_roster_commitment: str
    overlap_found: bool
    checked_site_count: int
    audit_sha256: str
    record_sha256: str

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> BlindOverlapCheckV1:
        return _parse_blind_overlap_check(value)


@dataclass(frozen=True, slots=True)
class AdmissionBindingV1:
    target_roster_sha256: str
    locator_set_sha256: str
    source_capture_set_sha256: str
    target_spec_set_sha256: str
    geometry_receipt_set_sha256: str
    blind_overlap_check_sha256: str


@dataclass(frozen=True, slots=True)
class LegacyBindingsV1:
    schema_version: str
    registry_version: str
    registry_core_sha256: str
    projection_identity_commitment: str
    split_manifest_sha256: str
    public_registry_sha256: str
    public_case_set_sha256: str
    existing_dev_site_count: int
    existing_dev_target_count: int

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> LegacyBindingsV1:
        return _parse_legacy_bindings(value)


@dataclass(frozen=True, slots=True)
class IndependentReviewV1:
    schema_version: str
    reviewed_target_roster_sha256: str
    reviewed_admission_binding_sha256: str
    status: str
    reviewer_identity_commitment: str
    review_sha256: str

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> IndependentReviewV1:
        return _parse_independent_review(value)


@dataclass(frozen=True, slots=True)
class FreezeReceiptV2:
    schema_version: str
    registry_version: str
    registry_core_sha256: str
    projection_identity_commitment: str
    split_manifest_sha256: str
    public_registry_sha256: str
    public_case_set_sha256: str
    site_locator_set_sha256: str
    public_site_set_sha256: str
    public_target_set_sha256: str
    source_capture_set_sha256: str
    target_spec_set_sha256: str
    geometry_receipt_set_sha256: str
    target_roster_sha256: str
    new_site_count: int
    new_target_count: int
    allocation: tuple[int, int, int]
    combined_dev_site_count: int
    combined_dev_target_count: int
    blind_overlap_check_sha256: str
    independent_review_sha256: str
    receipt_sha256: str

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> FreezeReceiptV2:
        return _parse_freeze_receipt(value)


def canonical_sha256(
    value: Mapping[str, object], *, omit: frozenset[str] = frozenset()
) -> str:
    payload = {key: item for key, item in value.items() if key not in omit}
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class TargetRosterV1:
    schema_version: str
    roster_version: str
    projection_identity_commitment: str
    split: str
    site_count: int
    target_count: int
    allocation: tuple[int, ...]
    sites: tuple[Mapping[str, object], ...]
    targets: tuple[Mapping[str, object], ...]
    roster_sha256: str

    @classmethod
    def from_dict(cls, roster: Mapping[str, object]) -> TargetRosterV1:
        return _parse_roster(roster)


def verify_target_roster(roster: Mapping[str, object]) -> TargetRosterV1:
    return TargetRosterV1.from_dict(roster)


def _is_regular_nonreparse_file(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISREG(metadata.st_mode) and not bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _read_canonical_json_object(path: Path, *, label: str) -> dict[str, object]:
    requested = Path(path)
    if not _is_regular_nonreparse_file(requested):
        _error(f"{label}_file")
    try:
        before = requested.lstat()
        with requested.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            attributes = getattr(opened, "st_file_attributes", 0)
            if not stat.S_ISREG(opened.st_mode) or attributes & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
            ):
                _error(f"{label}_file")
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                _error(f"{label}_file")
            raw = handle.read()
        after = requested.lstat()
    except OSError:
        _error(f"{label}_file")
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ):
        _error(f"{label}_file")

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError("duplicate_json_key")
            parsed[key] = value
        return parsed

    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
        if type(payload) is not dict:
            _error(f"{label}_json")
        canonical = (
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        _error(f"{label}_json")
    if raw != canonical:
        _error(f"{label}_canonical_json")
    return payload


def verify_frozen_target_roster(
    roster_path: Path,
    receipt_path: Path,
    *,
    projection_identity_commitment: str,
) -> FreezeReceiptV2:
    """Verify the public roster/receipt sidecar without materializing cases."""

    roster = verify_target_roster(
        _read_canonical_json_object(Path(roster_path), label="target_roster")
    )
    receipt = FreezeReceiptV2.from_dict(
        _read_canonical_json_object(Path(receipt_path), label="freeze_receipt")
    )
    if not _is_hash(projection_identity_commitment) or (
        roster.projection_identity_commitment != projection_identity_commitment
        or receipt.projection_identity_commitment != projection_identity_commitment
    ):
        _error("projection_identity_commitment")
    if receipt.target_roster_sha256 != roster.roster_sha256:
        _error("frozen_target_roster_binding")
    if receipt.public_site_set_sha256 != _canonical_set_sha256(roster.sites):
        _error("public_site_set_sha256")
    if receipt.public_target_set_sha256 != _canonical_set_sha256(roster.targets):
        _error("public_target_set_sha256")
    return receipt


def _error(code: str) -> None:
    raise TargetRosterError(code)


def _is_hash(value: object) -> bool:
    return type(value) is str and _HASH_RE.fullmatch(value) is not None


def _require_keys(value: Mapping[str, object], keys: frozenset[str], code: str) -> None:
    if set(value) != keys:
        _error(code)


def _require_string(value: object, code: str) -> str:
    if type(value) is not str:
        _error(code)
    return value


def _require_sequence(value: object, code: str) -> Sequence[object]:
    if type(value) not in (list, tuple):
        _error(code)
    return value  # type: ignore[return-value]


def _reject_protected(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str or _PROTECTED_TOKEN_RE.search(key):
                _error("protected_identifier")
            _reject_protected(item)
    elif type(value) in (list, tuple):
        for item in value:
            _reject_protected(item)
    elif type(value) is str:
        if (
            _PROTECTED_TOKEN_RE.search(value)
            or (_RAW_PNU_RE.search(value) and not _is_hash(value))
            or _URI_RE.search(value)
            or _WINDOWS_PATH_RE.search(value)
            or value.startswith(("/", "\\", "~"))
            or "/" in value
            or "\\" in value
        ):
            _error("protected_identifier")


def _parse_site(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _error("site_row_type")
    _require_keys(value, _SITE_KEYS, "site_keys")
    site_ref = _require_string(value["site_ref"], "site_ref_type")
    if not site_ref:
        _error("site_ref_empty")
    area_bin = _require_string(value["area_bin"], "area_bin_type")
    if not area_bin:
        _error("area_bin_empty")
    return {"site_ref": site_ref, "area_bin": area_bin}


def _parse_target(value: object, site_refs: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _error("target_row_type")
    _require_keys(value, _TARGET_KEYS, "target_keys")
    target_ref = _require_string(value["target_ref"], "target_ref_type")
    site_ref = _require_string(value["site_ref"], "target_site_ref_type")
    if not target_ref or site_ref not in site_refs:
        _error("target_ref_or_site")
    for field in ("program", "subject_kind", "attempt_stage", "route_kind"):
        if not _require_string(value[field], f"{field}_type"):
            _error(f"{field}_empty")
    if not _is_hash(value["target_spec_sha256"]):
        _error("target_spec_sha256")
    source_ids = _require_sequence(value["source_ids"], "source_ids_type")
    if not source_ids or any(type(item) is not str or not item for item in source_ids):
        _error("source_ids")
    if len(source_ids) != len(set(source_ids)) or list(source_ids) != sorted(
        source_ids, key=lambda item: item.encode("utf-8")
    ):
        _error("source_ids")
    if any(_IDENTITY_ALIAS_RE.search(item) for item in source_ids):
        _error("protected_identifier")
    return {
        "target_ref": target_ref,
        "site_ref": site_ref,
        "program": value["program"],
        "subject_kind": value["subject_kind"],
        "attempt_stage": value["attempt_stage"],
        "route_kind": value["route_kind"],
        "target_spec_sha256": value["target_spec_sha256"],
        "source_ids": tuple(source_ids),
    }


def _require_nonempty_string(value: object, code: str) -> str:
    text = _require_string(value, code)
    if not text:
        _error(code)
    return text


def _require_hash(value: object, code: str) -> str:
    if not _is_hash(value):
        _error(code)
    return value


def _parse_legacy_bindings(value: Mapping[str, object]) -> LegacyBindingsV1:
    if not isinstance(value, Mapping):
        _error("legacy_bindings")
    _require_keys(value, LEGACY_BINDINGS_KEYS, "legacy_bindings")
    schema_version = _require_schema(
        value["schema_version"], LEGACY_BINDINGS_SCHEMA, "legacy_bindings"
    )
    registry_version = _require_nonempty_string(
        value["registry_version"], "legacy_bindings"
    )
    hash_fields = (
        "registry_core_sha256",
        "projection_identity_commitment",
        "split_manifest_sha256",
        "public_registry_sha256",
        "public_case_set_sha256",
    )
    for field in hash_fields:
        _require_hash(value[field], "legacy_bindings")
    if (
        type(value["existing_dev_site_count"]) is not int
        or value["existing_dev_site_count"] != 5
        or type(value["existing_dev_target_count"]) is not int
        or value["existing_dev_target_count"] != 30
    ):
        _error("legacy_bindings")
    return LegacyBindingsV1(
        schema_version=schema_version,
        registry_version=registry_version,
        registry_core_sha256=value["registry_core_sha256"],
        projection_identity_commitment=value["projection_identity_commitment"],
        split_manifest_sha256=value["split_manifest_sha256"],
        public_registry_sha256=value["public_registry_sha256"],
        public_case_set_sha256=value["public_case_set_sha256"],
        existing_dev_site_count=5,
        existing_dev_target_count=30,
    )


def _parse_independent_review(value: Mapping[str, object]) -> IndependentReviewV1:
    if not isinstance(value, Mapping):
        _error("independent_review")
    _require_keys(value, INDEPENDENT_REVIEW_KEYS, "independent_review")
    schema_version = _require_schema(
        value["schema_version"], INDEPENDENT_REVIEW_SCHEMA, "independent_review"
    )
    for field in (
        "reviewed_target_roster_sha256",
        "reviewed_admission_binding_sha256",
        "reviewer_identity_commitment",
        "review_sha256",
    ):
        _require_hash(value[field], "independent_review")
    if value["status"] != "approved":
        _error("independent_review")
    if (
        _canonical_record_sha256(
            value, omit=frozenset({"review_sha256"}), code="independent_review"
        )
        != value["review_sha256"]
    ):
        _error("independent_review")
    return IndependentReviewV1(
        schema_version=schema_version,
        reviewed_target_roster_sha256=value["reviewed_target_roster_sha256"],
        reviewed_admission_binding_sha256=value["reviewed_admission_binding_sha256"],
        status="approved",
        reviewer_identity_commitment=value["reviewer_identity_commitment"],
        review_sha256=value["review_sha256"],
    )


def _parse_freeze_receipt(value: Mapping[str, object]) -> FreezeReceiptV2:
    if not isinstance(value, Mapping):
        _error("freeze_receipt")
    _require_keys(value, FREEZE_RECEIPT_KEYS, "freeze_receipt")
    schema_version = _require_schema(
        value["schema_version"], FREEZE_RECEIPT_SCHEMA, "freeze_receipt"
    )
    registry_version = _require_nonempty_string(
        value["registry_version"], "freeze_receipt"
    )
    for field in (
        "registry_core_sha256",
        "projection_identity_commitment",
        "split_manifest_sha256",
        "public_registry_sha256",
        "public_case_set_sha256",
        "site_locator_set_sha256",
        "public_site_set_sha256",
        "public_target_set_sha256",
        "source_capture_set_sha256",
        "target_spec_set_sha256",
        "geometry_receipt_set_sha256",
        "target_roster_sha256",
        "blind_overlap_check_sha256",
        "independent_review_sha256",
        "receipt_sha256",
    ):
        _require_hash(value[field], "freeze_receipt")
    allocation = _require_sequence(value["allocation"], "freeze_receipt")
    if (
        tuple(allocation) != ALLOCATION
        or any(type(item) is not int for item in allocation)
        or type(value["new_site_count"]) is not int
        or value["new_site_count"] != 3
        or type(value["new_target_count"]) is not int
        or value["new_target_count"] != 34
        or type(value["combined_dev_site_count"]) is not int
        or value["combined_dev_site_count"] != 8
        or type(value["combined_dev_target_count"]) is not int
        or value["combined_dev_target_count"] != 64
    ):
        _error("freeze_receipt")
    if (
        _canonical_record_sha256(
            value, omit=frozenset({"receipt_sha256"}), code="freeze_receipt"
        )
        != value["receipt_sha256"]
    ):
        _error("freeze_receipt")
    return FreezeReceiptV2(
        schema_version=schema_version,
        registry_version=registry_version,
        registry_core_sha256=value["registry_core_sha256"],
        projection_identity_commitment=value["projection_identity_commitment"],
        split_manifest_sha256=value["split_manifest_sha256"],
        public_registry_sha256=value["public_registry_sha256"],
        public_case_set_sha256=value["public_case_set_sha256"],
        site_locator_set_sha256=value["site_locator_set_sha256"],
        public_site_set_sha256=value["public_site_set_sha256"],
        public_target_set_sha256=value["public_target_set_sha256"],
        source_capture_set_sha256=value["source_capture_set_sha256"],
        target_spec_set_sha256=value["target_spec_set_sha256"],
        geometry_receipt_set_sha256=value["geometry_receipt_set_sha256"],
        target_roster_sha256=value["target_roster_sha256"],
        new_site_count=3,
        new_target_count=34,
        allocation=ALLOCATION,
        combined_dev_site_count=8,
        combined_dev_target_count=64,
        blind_overlap_check_sha256=value["blind_overlap_check_sha256"],
        independent_review_sha256=value["independent_review_sha256"],
        receipt_sha256=value["receipt_sha256"],
    )


def _require_schema(value: object, expected: str, code: str) -> str:
    schema_version = _require_nonempty_string(value, code)
    if schema_version != expected:
        _error(code)
    return schema_version


def _canonical_record_sha256(
    value: Mapping[str, object], *, omit: frozenset[str], code: str
) -> str:
    try:
        return canonical_sha256(value, omit=omit)
    except (TypeError, ValueError):
        _error(code)


def _parse_source_ids(value: object, code: str) -> tuple[str, ...]:
    source_ids = _require_sequence(value, code)
    if not source_ids or any(type(item) is not str or not item for item in source_ids):
        _error(code)
    if len(source_ids) != len(set(source_ids)) or list(source_ids) != sorted(
        source_ids, key=lambda item: item.encode("utf-8")
    ):
        _error(code)
    return tuple(source_ids)  # type: ignore[arg-type]


def _parse_source_capture(value: Mapping[str, object]) -> SourceCaptureV1:
    if not isinstance(value, Mapping):
        _error("source_capture_type")
    _require_keys(value, SOURCE_CAPTURE_KEYS, "source_capture_keys")
    if type(value["byte_length"]) is not int or value["byte_length"] < 0:
        _error("source_capture_byte_length")
    evidence_families = _parse_source_ids(
        value["evidence_families"], "source_evidence_families"
    )
    if not set(evidence_families).issubset(EVIDENCE_FAMILIES):
        _error("source_evidence_families")
    return SourceCaptureV1(
        schema_version=_require_schema(
            value["schema_version"], SOURCE_CAPTURE_SCHEMA, "source_capture_schema"
        ),
        source_id=_require_nonempty_string(value["source_id"], "source_id"),
        publisher=_require_nonempty_string(value["publisher"], "source_publisher"),
        canonical_uri=_require_nonempty_string(
            value["canonical_uri"], "source_canonical_uri"
        ),
        retrieved_at=_require_nonempty_string(
            value["retrieved_at"], "source_retrieved_at"
        ),
        effective_at=_require_nonempty_string(
            value["effective_at"], "source_effective_at"
        ),
        media_type=_require_nonempty_string(value["media_type"], "source_media_type"),
        byte_length=value["byte_length"],
        sha256=_require_hash(value["sha256"], "source_sha256"),
        etag=_require_string(value["etag"], "source_etag"),
        last_modified=_require_string(value["last_modified"], "source_last_modified"),
        license=_require_nonempty_string(value["license"], "source_license"),
        redistribution_status=_require_nonempty_string(
            value["redistribution_status"], "source_redistribution_status"
        ),
        evidence_families=evidence_families,
    )


def verify_source_capture_set(
    rows: Sequence[Mapping[str, object]], raw_bytes_by_source_id: Mapping[str, bytes]
) -> tuple[SourceCaptureV1, ...]:
    raw_rows = _require_sequence(rows, "source_capture_set_type")
    parsed = tuple(SourceCaptureV1.from_dict(row) for row in raw_rows)
    source_ids = tuple(row.source_id for row in parsed)
    if len(source_ids) != len(set(source_ids)):
        _error("source_capture_id_duplicate")
    if set(raw_bytes_by_source_id) != set(source_ids):
        _error("source_capture_bytes_closure")
    for row in parsed:
        raw = raw_bytes_by_source_id[row.source_id]
        if type(raw) is not bytes:
            _error("source_capture_raw_bytes")
        if len(raw) != row.byte_length or hashlib.sha256(raw).hexdigest() != row.sha256:
            _error("source_capture_bytes_mismatch")
    return parsed


def _parse_site_locator(value: Mapping[str, object]) -> SiteLocatorV1:
    if not isinstance(value, Mapping):
        _error("site_locator_type")
    _require_keys(value, SITE_LOCATOR_KEYS, "site_locator_keys")
    pnu = _require_nonempty_string(value["pnu"], "locator_pnu")
    if _RAW_PNU_RE.fullmatch(pnu) is None:
        _error("locator_pnu")
    return SiteLocatorV1(
        schema_version=_require_schema(
            value["schema_version"], SITE_LOCATOR_SCHEMA, "site_locator_schema"
        ),
        internal_site_id=_require_nonempty_string(
            value["internal_site_id"], "locator_internal_site_id"
        ),
        pnu=pnu,
        split=_require_schema(value["split"], "dev", "locator_split"),
        area_bin=_require_nonempty_string(value["area_bin"], "locator_area_bin"),
        parcel_geometry_sha256=_require_hash(
            value["parcel_geometry_sha256"], "locator_parcel_geometry_sha256"
        ),
        project_cluster_id=_require_nonempty_string(
            value["project_cluster_id"], "locator_project_cluster_id"
        ),
        source_capture_ids=_parse_source_ids(
            value["source_capture_ids"], "locator_source_capture_ids"
        ),
    )


def verify_site_locator_set(
    rows: Sequence[Mapping[str, object]],
) -> tuple[SiteLocatorV1, ...]:
    raw_rows = _require_sequence(rows, "site_locator_set_type")
    parsed = tuple(SiteLocatorV1.from_dict(row) for row in raw_rows)
    if len(parsed) != 3:
        _error("site_locator_count")
    for values in (
        tuple(row.internal_site_id for row in parsed),
        tuple(row.pnu for row in parsed),
        tuple(row.parcel_geometry_sha256 for row in parsed),
        tuple(row.project_cluster_id for row in parsed),
    ):
        if len(values) != len(set(values)):
            _error("site_or_project_cluster_overlap")
    return parsed


def _parse_target_spec(value: Mapping[str, object]) -> TargetSpecV1:
    if not isinstance(value, Mapping):
        _error("target_spec_type")
    _require_keys(value, TARGET_SPEC_KEYS, "target_spec_keys")
    raw_families = value["evidence_family_sources"]
    if not isinstance(raw_families, Mapping) or set(raw_families) != set(
        EVIDENCE_FAMILIES
    ):
        _error("target_source_coverage_incomplete")
    evidence_family_sources = {
        family: _parse_source_ids(
            raw_families[family], "target_source_coverage_incomplete"
        )
        for family in EVIDENCE_FAMILIES
    }
    target_spec_sha256 = _require_hash(
        value["target_spec_sha256"], "target_spec_sha256"
    )
    if (
        _canonical_record_sha256(
            value, omit=frozenset({"target_spec_sha256"}), code="target_spec_sha256"
        )
        != target_spec_sha256
    ):
        _error("target_spec_sha256")
    normalized_subject_identity = _require_nonempty_string(
        value["normalized_subject_identity"], "normalized_subject_identity"
    )
    if _IDENTITY_ALIAS_RE.search(normalized_subject_identity):
        _error("normalized_subject_identity")
    return TargetSpecV1(
        schema_version=_require_schema(
            value["schema_version"], TARGET_SPEC_SCHEMA, "target_spec_schema"
        ),
        target_ref=_require_nonempty_string(
            value["target_ref"], "target_spec_target_ref"
        ),
        normalized_subject_identity=normalized_subject_identity,
        evidence_family_sources=evidence_family_sources,
        geometry_receipt_sha256=_require_hash(
            value["geometry_receipt_sha256"], "geometry_receipt_sha256"
        ),
        target_spec_sha256=target_spec_sha256,
    )


def verify_target_spec_set(
    rows: Sequence[Mapping[str, object]], roster: TargetRosterV1
) -> tuple[TargetSpecV1, ...]:
    raw_rows = _require_sequence(rows, "target_spec_set_type")
    parsed = tuple(TargetSpecV1.from_dict(row) for row in raw_rows)
    target_refs = tuple(row.target_ref for row in parsed)
    identities = tuple(row.normalized_subject_identity for row in parsed)
    if len(target_refs) != len(set(target_refs)):
        _error("target_spec_target_ref_duplicate")
    if len(identities) != len(set(identities)):
        _error("normalized_subject_identity_duplicate")
    public_targets = {target["target_ref"]: target for target in roster.targets}
    if set(target_refs) != set(public_targets):
        _error("target_spec_target_closure")
    for row in parsed:
        if (
            public_targets[row.target_ref]["target_spec_sha256"]
            != row.target_spec_sha256
        ):
            _error("target_spec_public_binding")
    return parsed


def _parse_geometry_receipt(value: Mapping[str, object]) -> GeometryReceiptV1:
    if not isinstance(value, Mapping):
        _error("geometry_receipt_type")
    _require_keys(value, GEOMETRY_RECEIPT_KEYS, "geometry_receipt_keys")
    receipt_sha256 = _require_hash(value["receipt_sha256"], "geometry_receipt_sha256")
    if (
        _canonical_record_sha256(
            value, omit=frozenset({"receipt_sha256"}), code="geometry_receipt_sha256"
        )
        != receipt_sha256
    ):
        _error("geometry_receipt_sha256")
    if type(value["hard_pass"]) is not bool:
        _error("geometry_receipt_hard_pass")
    return GeometryReceiptV1(
        schema_version=_require_schema(
            value["schema_version"], GEOMETRY_RECEIPT_SCHEMA, "geometry_receipt_schema"
        ),
        target_ref=_require_nonempty_string(
            value["target_ref"], "geometry_receipt_target_ref"
        ),
        input_geometry_sha256=_require_hash(
            value["input_geometry_sha256"], "input_geometry_sha256"
        ),
        materializer_code_sha256=_require_hash(
            value["materializer_code_sha256"], "materializer_code_sha256"
        ),
        output_geometry_sha256=_require_hash(
            value["output_geometry_sha256"], "output_geometry_sha256"
        ),
        compile_log_sha256=_require_hash(
            value["compile_log_sha256"], "compile_log_sha256"
        ),
        hard_pass=value["hard_pass"],
        receipt_sha256=receipt_sha256,
    )


def verify_geometry_receipt_set(
    rows: Sequence[Mapping[str, object]],
) -> tuple[GeometryReceiptV1, ...]:
    raw_rows = _require_sequence(rows, "geometry_receipt_set_type")
    parsed = tuple(GeometryReceiptV1.from_dict(row) for row in raw_rows)
    target_refs = tuple(row.target_ref for row in parsed)
    if len(target_refs) != len(set(target_refs)):
        _error("geometry_receipt_target_ref_duplicate")
    if any(not row.hard_pass for row in parsed):
        _error("geometry_receipt_hard_pass")
    return parsed


def _parse_blind_overlap_check(value: Mapping[str, object]) -> BlindOverlapCheckV1:
    if not isinstance(value, Mapping):
        _error("blinded_membership_check")
    _require_keys(value, BLIND_KEYS, "blinded_membership_check")
    if (
        type(value["overlap_found"]) is not bool
        or type(value["checked_site_count"]) is not int
    ):
        _error("blinded_membership_check")
    record_sha256 = _require_hash(value["record_sha256"], "blinded_membership_check")
    if (
        _canonical_record_sha256(
            value, omit=frozenset({"record_sha256"}), code="blinded_membership_check"
        )
        != record_sha256
    ):
        _error("blinded_membership_check")
    return BlindOverlapCheckV1(
        schema_version=_require_schema(
            value["schema_version"],
            BLIND_OVERLAP_CHECK_SCHEMA,
            "blinded_membership_check",
        ),
        locator_set_sha256=_require_hash(
            value["locator_set_sha256"], "blinded_membership_check"
        ),
        protected_roster_commitment=_require_hash(
            value["protected_roster_commitment"], "blinded_membership_check"
        ),
        overlap_found=value["overlap_found"],
        checked_site_count=value["checked_site_count"],
        audit_sha256=_require_hash(value["audit_sha256"], "blinded_membership_check"),
        record_sha256=record_sha256,
    )


def verify_blind_overlap_check(
    row: Mapping[str, object],
    *,
    locator_set_sha256: str,
    protected_roster_commitment: str,
) -> BlindOverlapCheckV1:
    parsed = BlindOverlapCheckV1.from_dict(row)
    if (
        parsed.locator_set_sha256 != locator_set_sha256
        or parsed.protected_roster_commitment != protected_roster_commitment
        or not protected_roster_commitment
        or parsed.overlap_found is not False
        or parsed.checked_site_count != 3
    ):
        _error("blinded_membership_check")
    return parsed


def _canonical_set_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    encoded_rows = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return hashlib.sha256(
        ("[" + ",".join(sorted(encoded_rows)) + "]").encode("utf-8")
    ).hexdigest()


def verify_admission_inputs(
    *,
    roster: Mapping[str, object],
    target_specs: Sequence[Mapping[str, object]],
    locators: Sequence[Mapping[str, object]],
    source_captures: Sequence[Mapping[str, object]],
    raw_bytes_by_source_id: Mapping[str, bytes],
    geometry_receipts: Sequence[Mapping[str, object]],
    blind_check: Mapping[str, object],
    protected_roster_commitment: str,
) -> AdmissionBindingV1:
    parsed_roster = verify_target_roster(roster)
    parsed_captures = verify_source_capture_set(source_captures, raw_bytes_by_source_id)
    parsed_locators = verify_site_locator_set(locators)
    parsed_specs = verify_target_spec_set(target_specs, parsed_roster)
    parsed_receipts = verify_geometry_receipt_set(geometry_receipts)
    source_ids = {row.source_id for row in parsed_captures}
    referenced_source_ids = {
        source_id
        for locator in parsed_locators
        for source_id in locator.source_capture_ids
    }
    public_targets = {target["target_ref"]: target for target in parsed_roster.targets}
    receipts_by_target = {receipt.target_ref: receipt for receipt in parsed_receipts}
    if set(receipts_by_target) != set(public_targets):
        _error("geometry_receipt_target_closure")
    for spec in parsed_specs:
        evidence_source_ids = {
            source_id
            for family_source_ids in spec.evidence_family_sources.values()
            for source_id in family_source_ids
        }
        referenced_source_ids.update(evidence_source_ids)
        if evidence_source_ids != set(public_targets[spec.target_ref]["source_ids"]):
            _error("target_source_public_binding")
        receipt = receipts_by_target[spec.target_ref]
        if (
            receipt.receipt_sha256 != spec.geometry_receipt_sha256
            or not receipt.hard_pass
        ):
            _error("geometry_receipt_binding")
    if not referenced_source_ids.issubset(source_ids):
        _error("source_capture_reference_missing")
    captures_by_source_id = {row.source_id: row for row in parsed_captures}
    for locator in parsed_locators:
        if any(
            "site" not in captures_by_source_id[source_id].evidence_families
            for source_id in locator.source_capture_ids
        ):
            _error("locator_source_family_mapping")
    for spec in parsed_specs:
        for family, family_source_ids in spec.evidence_family_sources.items():
            if any(
                family not in captures_by_source_id[source_id].evidence_families
                for source_id in family_source_ids
            ):
                _error("evidence_family_source_mapping")
    if {locator.area_bin for locator in parsed_locators} != {
        site["area_bin"] for site in parsed_roster.sites
    }:
        _error("site_locator_area_bin_binding")
    locator_set_sha256 = _canonical_set_sha256(locators)
    parsed_blind = verify_blind_overlap_check(
        blind_check,
        locator_set_sha256=locator_set_sha256,
        protected_roster_commitment=protected_roster_commitment,
    )
    return AdmissionBindingV1(
        target_roster_sha256=parsed_roster.roster_sha256,
        locator_set_sha256=locator_set_sha256,
        source_capture_set_sha256=_canonical_set_sha256(source_captures),
        target_spec_set_sha256=_canonical_set_sha256(target_specs),
        geometry_receipt_set_sha256=_canonical_set_sha256(geometry_receipts),
        blind_overlap_check_sha256=parsed_blind.record_sha256,
    )


def _parse_roster(roster: Mapping[str, object]) -> TargetRosterV1:
    if not isinstance(roster, Mapping):
        _error("roster_type")
    _reject_protected(roster)
    _require_keys(roster, _ROOT_KEYS, "roster_keys")
    if (
        type(roster["schema_version"]) is not str
        or roster["schema_version"] != TARGET_ROSTER_SCHEMA
    ):
        _error("schema_version")
    roster_version = _require_string(roster["roster_version"], "roster_version_type")
    if not roster_version:
        _error("roster_version_empty")
    if not _is_hash(roster["projection_identity_commitment"]):
        _error("projection_identity_commitment")
    if type(roster["split"]) is not str or roster["split"] != "dev":
        _error("split")
    if type(roster["site_count"]) is not int or roster["site_count"] != 3:
        _error("site_count")
    if type(roster["target_count"]) is not int or roster["target_count"] != 34:
        _error("target_count")
    allocation_raw = _require_sequence(roster["allocation"], "allocation_type")
    if tuple(allocation_raw) != ALLOCATION or any(
        type(item) is not int for item in allocation_raw
    ):
        _error("allocation")
    sites_raw = _require_sequence(roster["sites"], "sites_type")
    targets_raw = _require_sequence(roster["targets"], "targets_type")
    if len(sites_raw) != 3 or len(targets_raw) != 34:
        _error("roster_counts")
    sites = tuple(_parse_site(site) for site in sites_raw)
    site_refs = tuple(site["site_ref"] for site in sites)
    if len(site_refs) != len(set(site_refs)) or list(site_refs) != sorted(
        site_refs, key=lambda item: item.encode("utf-8")
    ):
        _error("site_order")
    targets = tuple(
        _parse_target(target, frozenset(site_refs)) for target in targets_raw
    )
    target_refs = tuple(target["target_ref"] for target in targets)
    target_hashes = tuple(target["target_spec_sha256"] for target in targets)
    if len(target_refs) != len(set(target_refs)):
        _error("target_ref_duplicate")
    if len(target_hashes) != len(set(target_hashes)):
        _error("target_spec_duplicate_or_mutated")
    if list(target_refs) != sorted(target_refs, key=lambda item: item.encode("utf-8")):
        _error("target_order")
    expected_pairings = tuple(
        (f"{site_ref}-target-{target_index:02d}", site_ref)
        for site_ref, count in zip(site_refs, ALLOCATION, strict=True)
        for target_index in range(count)
    )
    actual_pairings = tuple(
        (target["target_ref"], target["site_ref"]) for target in targets
    )
    if actual_pairings != expected_pairings:
        _error("target_site_pairing")
    counts = tuple(
        sum(target["site_ref"] == site_ref for target in targets)
        for site_ref in site_refs
    )
    if counts != ALLOCATION:
        _error("allocation_by_site")
    if not _is_hash(roster["roster_sha256"]):
        _error("roster_sha256")
    if (
        canonical_sha256(roster, omit=frozenset({"roster_sha256"}))
        != roster["roster_sha256"]
    ):
        _error("roster_sha256")
    return TargetRosterV1(
        schema_version=TARGET_ROSTER_SCHEMA,
        roster_version=roster_version,
        projection_identity_commitment=roster["projection_identity_commitment"],
        split="dev",
        site_count=3,
        target_count=34,
        allocation=ALLOCATION,
        sites=sites,
        targets=targets,
        roster_sha256=roster["roster_sha256"],
    )
