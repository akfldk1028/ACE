"""Canonical, tamper-evident receipts for ICLR 2027 artifacts."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any

from .secure_files import AuthenticatedTree, read_authenticated_file


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_RECEIPT_FIELDS = frozenset(
    {
        "artifact_sha256",
        "bindings",
        "file_set_sha256",
        "files",
        "row_census",
        "row_census_sha256",
        "schema_version",
    }
)
_WINDOWS_RESERVED_COMPONENTS = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
        "COM¹",
        "COM²",
        "COM³",
        "LPT¹",
        "LPT²",
        "LPT³",
    }
)
_WINDOWS_INVALID_COMPONENT_CHARACTERS = frozenset('<>:"|?*')


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    return _sha256_bytes(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
    )


def _canonical_relative_path(path: object, *, verification: bool = False) -> str:
    if not isinstance(path, str) or not path:
        raise ValueError("relative path required")
    normalized = path.replace("\\", "/")
    posix_path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(path)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError("path outside root" if verification else "relative path required")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path outside root" if verification else "relative path required")
    if any(_is_nonportable_windows_component(part) for part in parts):
        raise ValueError("non-portable artifact path")
    return "/".join(parts)


def _is_nonportable_windows_component(component: str) -> bool:
    if component.endswith((".", " ")):
        return True
    if any(
        character in _WINDOWS_INVALID_COMPONENT_CHARACTERS or ord(character) < 32
        for character in component
    ):
        return True
    return component.split(".", 1)[0].upper() in _WINDOWS_RESERVED_COMPONENTS


def _require_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")
    return value


def _canonical_bindings(bindings: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(bindings, Mapping):
        raise ValueError("bindings must be a mapping")
    canonical: dict[str, str] = {}
    for name, digest in bindings.items():
        if not isinstance(name, str) or not name:
            raise ValueError("binding names must be non-empty strings")
        if name in canonical:
            raise ValueError("duplicate binding name")
        canonical[name] = _require_sha256(digest, field="binding")
    return dict(sorted(canonical.items()))


def _canonical_row_census(row_census: Mapping[str, int]) -> dict[str, int]:
    if not isinstance(row_census, Mapping):
        raise ValueError("row census must be a mapping")
    canonical: dict[str, int] = {}
    for name, count in row_census.items():
        if not isinstance(name, str) or not name:
            raise ValueError("row census keys must be non-empty strings")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("row census values must be non-negative integers")
        canonical[name] = count
    return dict(sorted(canonical.items()))


def _canonical_file_hashes(
    files: Mapping[str, str], *, verification: bool = False
) -> dict[str, str]:
    if not isinstance(files, Mapping):
        raise ValueError("files must be a mapping")
    canonical: dict[str, str] = {}
    for path, digest in files.items():
        normalized_path = _canonical_relative_path(path, verification=verification)
        if normalized_path in canonical:
            raise ValueError("duplicate artifact path")
        canonical[normalized_path] = _require_sha256(digest, field="artifact hash")
    return dict(sorted(canonical.items()))


def canonical_file_set_hash(files: Mapping[str, str]) -> str:
    """Hash a sorted mapping of canonical relative artifact paths to SHA-256s."""
    return _canonical_hash(_canonical_file_hashes(files))


def canonical_row_census_hash(row_census: Mapping[str, int]) -> str:
    """Hash a sorted row-census mapping."""
    return _canonical_hash(_canonical_row_census(row_census))


def _receipt_payload(
    *,
    schema_version: str,
    files: dict[str, str],
    file_set_sha256: str,
    row_census: dict[str, int],
    row_census_sha256: str,
    bindings: dict[str, str],
) -> dict[str, object]:
    return {
        "bindings": bindings,
        "file_set_sha256": file_set_sha256,
        "files": files,
        "row_census": row_census,
        "row_census_sha256": row_census_sha256,
        "schema_version": schema_version,
    }


def canonical_artifact_receipt(
    *,
    schema_version: str,
    files: Mapping[str, str | Path],
    row_census: Mapping[str, int],
    bindings: Mapping[str, str],
) -> dict[str, Any]:
    """Create a canonical receipt from on-disk artifact bytes and metadata."""
    if not isinstance(schema_version, str) or not schema_version:
        raise ValueError("schema version must be a non-empty string")
    if not isinstance(files, Mapping):
        raise ValueError("files must be a mapping")

    file_hashes: dict[str, str] = {}
    for relative_path, file_path in files.items():
        normalized_path = _canonical_relative_path(relative_path)
        if normalized_path in file_hashes:
            raise ValueError("duplicate artifact path")
        artifact_path = Path(file_path)
        artifact = read_authenticated_file(
            artifact_path,
            label=f"artifact {normalized_path}",
        )
        file_hashes[normalized_path] = _sha256_bytes(artifact)

    canonical_files = dict(sorted(file_hashes.items()))
    canonical_census = _canonical_row_census(row_census)
    canonical_bindings = _canonical_bindings(bindings)
    file_set_sha256 = canonical_file_set_hash(canonical_files)
    row_census_sha256 = canonical_row_census_hash(canonical_census)
    payload = _receipt_payload(
        schema_version=schema_version,
        files=canonical_files,
        file_set_sha256=file_set_sha256,
        row_census=canonical_census,
        row_census_sha256=row_census_sha256,
        bindings=canonical_bindings,
    )
    return {**payload, "artifact_sha256": _canonical_hash(payload)}


def _validated_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_FIELDS:
        raise ValueError("receipt fields mismatch")
    schema_version = receipt["schema_version"]
    if not isinstance(schema_version, str) or not schema_version:
        raise ValueError("schema version must be a non-empty string")
    files = _canonical_file_hashes(receipt["files"], verification=True)
    row_census = _canonical_row_census(receipt["row_census"])
    bindings = _canonical_bindings(receipt["bindings"])
    file_set_sha256 = _require_sha256(receipt["file_set_sha256"], field="file-set hash")
    row_census_sha256 = _require_sha256(
        receipt["row_census_sha256"], field="row census hash"
    )
    artifact_sha256 = _require_sha256(receipt["artifact_sha256"], field="artifact hash")
    return {
        "schema_version": schema_version,
        "files": files,
        "file_set_sha256": file_set_sha256,
        "row_census": row_census,
        "row_census_sha256": row_census_sha256,
        "bindings": bindings,
        "artifact_sha256": artifact_sha256,
    }


def _verified_receipt_metadata(receipt: Mapping[str, object]) -> dict[str, object]:
    canonical_receipt = _validated_receipt(receipt)
    files = canonical_receipt["files"]
    row_census = canonical_receipt["row_census"]
    if not isinstance(files, dict) or not isinstance(row_census, dict):
        raise ValueError("receipt fields mismatch")
    if canonical_file_set_hash(files) != canonical_receipt["file_set_sha256"]:
        raise ValueError("file-set hash mismatch")
    if canonical_row_census_hash(row_census) != canonical_receipt["row_census_sha256"]:
        raise ValueError("row census hash mismatch")
    payload = _receipt_payload(
        schema_version=canonical_receipt["schema_version"],
        files=files,
        file_set_sha256=canonical_receipt["file_set_sha256"],
        row_census=row_census,
        row_census_sha256=canonical_receipt["row_census_sha256"],
        bindings=canonical_receipt["bindings"],
    )
    if _canonical_hash(payload) != canonical_receipt["artifact_sha256"]:
        raise ValueError("artifact hash mismatch")
    return canonical_receipt


def verify_artifact_receipt_bytes(
    receipt: Mapping[str, object],
    *,
    files: Mapping[str, bytes],
) -> None:
    """Validate a receipt against the exact authenticated bytes a caller consumes."""

    canonical_receipt = _verified_receipt_metadata(receipt)
    expected_files = canonical_receipt["files"]
    if not isinstance(expected_files, dict) or not isinstance(files, Mapping):
        raise ValueError("receipt fields mismatch")
    supplied: dict[str, bytes] = {}
    for relative_path, artifact in files.items():
        normalized = _canonical_relative_path(relative_path, verification=True)
        if normalized in supplied:
            raise ValueError("duplicate artifact path")
        if not isinstance(artifact, bytes):
            raise ValueError("artifact bytes required")
        supplied[normalized] = artifact
    if set(supplied) != set(expected_files):
        raise ValueError("artifact file set mismatch")
    for relative_path, expected_hash in expected_files.items():
        if _sha256_bytes(supplied[relative_path]) != expected_hash:
            raise ValueError("artifact hash mismatch")


def verify_artifact_receipt(receipt: Mapping[str, object], *, root: str | Path) -> None:
    """Validate a receipt's metadata and every named file beneath ``root``."""

    canonical_receipt = _verified_receipt_metadata(receipt)
    files = canonical_receipt["files"]
    if not isinstance(files, dict):
        raise ValueError("receipt fields mismatch")

    artifacts: dict[str, bytes] = {}
    with AuthenticatedTree(Path(root), label="artifact root") as tree:
        for relative_path in files:
            artifacts[relative_path] = tree.read_bytes(
                relative_path,
                label=f"artifact {relative_path}",
            )
    verify_artifact_receipt_bytes(canonical_receipt, files=artifacts)
