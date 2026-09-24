"""Strict, non-executing intake utilities for the AgentTelemetry public source."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
from typing import Any, Mapping


SOURCE_URL = (
    "https://raw.githubusercontent.com/Krishnachaitanyakc/AgentTelemetry/"
    "8ba0ae753d51cc2837f4ef2fa450e103c3be904a/src/agenttelemetry_inspect/data/traces_v1.jsonl"
)
LICENSE_URL = (
    "https://raw.githubusercontent.com/Krishnachaitanyakc/AgentTelemetry/"
    "8ba0ae753d51cc2837f4ef2fa450e103c3be904a/LICENSE"
)
REPOSITORY = "Krishnachaitanyakc/AgentTelemetry"
SOURCE_COMMIT = "8ba0ae753d51cc2837f4ef2fa450e103c3be904a"
SOURCE_PATH = "src/agenttelemetry_inspect/data/traces_v1.jsonl"
SCHEMA_VERSION = "external-source-receipt/v1"
EXPECTED_SOURCE_BYTES = 612561
EXPECTED_SOURCE_SHA256 = (
    "99a3e63f5a7a2eb25f5c1fd9ea62f80181f44e2d5a0d1096877c18f4cbd7cb49"
)
EXPECTED_LICENSE_BYTES = 11239
EXPECTED_LICENSE_SHA256 = (
    "87e71eab2d4ec25ebe384daf6436a9c8afb54a26bc7f22bcc0642075d64bda10"
)
_RECEIPT_FIELDS = (
    "schema_version",
    "repository",
    "source_commit",
    "source_path",
    "source_sha256",
    "source_bytes",
    "source_rows",
    "canonical_rows_sha256",
    "license_spdx",
    "license_sha256",
    "retrieved_on",
)
_ROOT_KEYS = frozenset(("id", "input", "metadata", "target"))
_METADATA_KEYS = frozenset(
    (
        "condition",
        "framework",
        "fault_type",
        "is_control",
        "task",
        "n_spans",
        "oracle_detected",
        "oracle_false_fires",
        "ground_truth_events",
        "run_error",
        "harness",
    )
)
_HARNESS_KEYS = frozenset(
    ("seed", "rate", "max_iterations", "persona", "dataset_version")
)


def _canonical_json_line(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_non_finite_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON constant: {token}")


def _is_exact(value: Any, value_type: type[Any]) -> bool:
    return type(value) is value_type


def _validate_row_schema(row: Mapping[str, Any]) -> None:
    if set(row) != _ROOT_KEYS:
        raise ValueError("source row has unexpected root schema")
    if not all(_is_exact(row[key], str) for key in ("id", "input", "target")):
        raise ValueError("id, input, and target must be strings")
    metadata = row["metadata"]
    if not _is_exact(metadata, dict) or set(metadata) != _METADATA_KEYS:
        raise ValueError("source row has unexpected metadata schema")
    if not all(
        _is_exact(metadata[key], str)
        for key in ("condition", "framework", "fault_type", "task")
    ):
        raise ValueError("metadata string fields have wrong types")
    if not all(
        _is_exact(metadata[key], bool) for key in ("is_control", "oracle_detected")
    ):
        raise ValueError("metadata boolean fields have wrong types")
    if not all(
        _is_exact(metadata[key], int) for key in ("n_spans", "ground_truth_events")
    ):
        raise ValueError("metadata integer fields have wrong types")
    if not _is_exact(metadata["oracle_false_fires"], list) or not all(
        _is_exact(item, str) for item in metadata["oracle_false_fires"]
    ):
        raise ValueError("metadata oracle_false_fires must be a list of strings")
    if metadata["run_error"] is not None and not _is_exact(metadata["run_error"], str):
        raise ValueError("metadata run_error must be a string or null")
    harness = metadata["harness"]
    if not _is_exact(harness, dict) or set(harness) != _HARNESS_KEYS:
        raise ValueError("metadata harness has unexpected schema")
    if not all(_is_exact(harness[key], int) for key in ("seed", "max_iterations")):
        raise ValueError("metadata harness integer fields have wrong types")
    if not _is_exact(harness["rate"], float):
        raise ValueError("metadata harness rate must be a float")
    if not all(_is_exact(harness[key], str) for key in ("persona", "dataset_version")):
        raise ValueError("metadata harness string fields have wrong types")


def load_agenttelemetry_rows(source: bytes) -> tuple[Mapping[str, Any], ...]:
    """Parse precisely 170 UTF-8/LF canonical JSON object records."""
    if not isinstance(source, bytes):
        raise ValueError("source must be bytes")
    if source.startswith(b"\xef\xbb\xbf"):
        raise ValueError("source must not have a UTF-8 BOM")
    if b"\r" in source or not source.endswith(b"\n"):
        raise ValueError("source must use LF line endings and end with LF")
    try:
        text = source.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise ValueError("source must be strict UTF-8") from error

    lines = text.splitlines()
    if len(lines) != 170 or any(not line for line in lines):
        raise ValueError("source must contain exactly 170 nonempty JSONL rows")

    rows: list[Mapping[str, Any]] = []
    identities: set[str] = set()
    for line in lines:
        try:
            row = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_non_finite_constant,
            )
        except (json.JSONDecodeError, ValueError) as error:
            raise ValueError("source contains invalid JSON") from error
        if not isinstance(row, dict):
            raise ValueError("each source row must be a JSON object")
        _validate_row_schema(row)
        if row["id"] in identities:
            raise ValueError("source contains duplicate row identities")
        identities.add(row["id"])
        rows.append(row)
    return tuple(rows)


def validate_raw_source_identity(
    source: bytes,
    license_bytes: bytes,
    *,
    expected_source_bytes: int,
    expected_source_sha256: str,
    expected_license_bytes: int,
    expected_license_sha256: str,
) -> None:
    """Fail closed when the immutable raw source or license bytes drift."""
    source_sha256 = hashlib.sha256(source).hexdigest()
    license_sha256 = hashlib.sha256(license_bytes).hexdigest()
    if len(source) != expected_source_bytes or source_sha256 != expected_source_sha256:
        raise ValueError("source raw-byte identity does not match the pinned revision")
    if (
        len(license_bytes) != expected_license_bytes
        or license_sha256 != expected_license_sha256
    ):
        raise ValueError("license raw-byte identity does not match the pinned revision")


def _validate_apache_license(license_bytes: bytes) -> None:
    if not isinstance(license_bytes, bytes):
        raise ValueError("license must be bytes")
    try:
        license_text = license_bytes.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise ValueError("license must be strict UTF-8") from error
    has_license_url = (
        "http://www.apache.org/licenses/" in license_text
        or "https://www.apache.org/licenses/" in license_text
    )
    if not (
        "Apache License" in license_text
        and "Version 2.0" in license_text
        and has_license_url
    ):
        raise ValueError("license is not the Apache-2.0 license text")


@dataclass(frozen=True)
class ExternalSourceReceipt:
    schema_version: str
    repository: str
    source_commit: str
    source_path: str
    source_sha256: str
    source_bytes: int
    source_rows: int
    canonical_rows_sha256: str
    license_spdx: str
    license_sha256: str
    retrieved_on: str

    @classmethod
    def from_bytes(
        cls,
        source: bytes,
        license_bytes: bytes,
        *,
        url: str,
        commit_sha: str,
        retrieved_on: date,
    ) -> "ExternalSourceReceipt":
        if url != SOURCE_URL:
            raise ValueError(
                "source URL must be the exact immutable AgentTelemetry URL"
            )
        if commit_sha != SOURCE_COMMIT:
            raise ValueError("source commit must be the exact pinned 40-hex commit")
        if not isinstance(retrieved_on, date):
            raise ValueError("retrieved_on must be a date")
        validate_raw_source_identity(
            source,
            license_bytes,
            expected_source_bytes=EXPECTED_SOURCE_BYTES,
            expected_source_sha256=EXPECTED_SOURCE_SHA256,
            expected_license_bytes=EXPECTED_LICENSE_BYTES,
            expected_license_sha256=EXPECTED_LICENSE_SHA256,
        )
        rows = load_agenttelemetry_rows(source)
        _validate_apache_license(license_bytes)
        return cls(
            schema_version=SCHEMA_VERSION,
            repository=REPOSITORY,
            source_commit=SOURCE_COMMIT,
            source_path=SOURCE_PATH,
            source_sha256=hashlib.sha256(source).hexdigest(),
            source_bytes=len(source),
            source_rows=len(rows),
            canonical_rows_sha256=hashlib.sha256(
                b"".join(_canonical_json_line(row) + b"\n" for row in rows)
            ).hexdigest(),
            license_spdx="Apache-2.0",
            license_sha256=hashlib.sha256(license_bytes).hexdigest(),
            retrieved_on=retrieved_on.isoformat(),
        )

    def canonical_json_bytes(self) -> bytes:
        payload = asdict(self)
        if tuple(payload) != _RECEIPT_FIELDS:
            raise ValueError("receipt has unexpected fields")
        return (
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            + b"\n"
        )
