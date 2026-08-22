"""Private identity loading and public-release helpers for ICLR artifacts."""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from .projection import ProjectionIdentity
from .io import canonical_json, sha256_json, write_json_atomic, write_jsonl_atomic
from .schema import ArchitecturePublicCase


PROJECTION_IDENTITY_SCHEMA = "ace.iclr2027.projection_identity.private.v1"
PUBLIC_SITE_REGISTRY_SCHEMA = "ace.iclr2027.public_site_registry.v1"
FREEZE_RECEIPT_SCHEMA = "ace.iclr2027.freeze_receipt.v1"
PUBLIC_RELEASE_MANIFEST_SCHEMA = "ace.iclr2027.public_release_manifest.v1"
_SECRET_HEX = re.compile(r"^[0-9a-f]{64,}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SITE_REF = re.compile(r"^site:[0-9a-f]{64}$")
_REGISTRY_VERSION = re.compile(r"^selection-[0-9]{8}-[0-9a-f]{12}$")
_RAW_19_DIGITS = re.compile(r"(?<![0-9])[0-9]{19}(?![0-9])")
_IDENTITY_KEYS = frozenset({"schema_version", "secret_hex"})
_AREA_BINS = frozenset({"small", "medium", "large"})
_PUBLIC_REGISTRY_KEYS = frozenset(
    {
        "schema_version",
        "registry_version",
        "registry_core_sha256",
        "identity_commitment",
        "sites",
    }
)
_PUBLIC_SITE_KEYS = frozenset({"site_ref", "split", "area_bin"})
_RELEASE_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "registry_version",
        "registry_core_sha256",
        "identity_commitment",
        "public_case_set_sha256",
        "files",
    }
)
_RELEASE_FILE_KEYS = frozenset({"path", "record_count", "sha256"})
_RELEASE_PATHS = {
    "dev": "dev.public.jsonl",
    "test": "test.public.jsonl",
    "sites": "site_registry.public.json",
}
_FORBIDDEN_METADATA_KEYS = {
    "pnu",
    "condition",
    "expected_decision",
    "mutation_family",
    "gold_record",
    "secret",
    "secret_hex",
    "private",
    "internal",
    "internal_id",
    "internal_case_id",
}
_FORBIDDEN_METADATA_TOKENS = frozenset(
    {"pnu", "condition", "gold", "private", "path", "secret", "internal"}
)
_FORBIDDEN_METADATA_VALUES = frozenset({"native", "challenged"})


def _exact_keys(payload: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if set(payload) != expected:
        missing = sorted(expected - set(payload))
        extra = sorted(str(key) for key in set(payload) - expected)
        raise ValueError(
            f"{label} must contain exact keys; missing={missing}, extra={extra}"
        )


def audit_public_metadata(value: Any, path: str = "public_metadata") -> None:
    """Recursively reject private identifiers, raw cadastral tokens, and paths."""

    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            if not isinstance(raw_key, str):
                raise ValueError(f"public metadata key must be text at {path}")
            lowered = raw_key.lower()
            key_tokens = frozenset(re.findall(r"[a-z0-9]+", lowered))
            if (
                lowered in _FORBIDDEN_METADATA_KEYS
                or lowered.startswith("gold_")
                or lowered.startswith("private_")
                or lowered.startswith("internal_")
                or lowered.endswith("_path")
                or lowered.endswith("_pnu")
                or (
                    lowered != "path"
                    and bool(key_tokens & _FORBIDDEN_METADATA_TOKENS)
                )
            ):
                raise ValueError(f"forbidden public metadata key at {path}.{raw_key}")
            if _RAW_19_DIGITS.search(raw_key):
                raise ValueError(f"raw 19-digit identifier at {path}.{raw_key}")
            audit_public_metadata(item, f"{path}.{raw_key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            audit_public_metadata(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if _RAW_19_DIGITS.search(value):
            raise ValueError(f"raw 19-digit identifier at {path}")
        if "/" in value or "\\" in value or re.match(r"^[A-Za-z]:", value):
            raise ValueError(f"filesystem path is forbidden at {path}")
        value_tokens = frozenset(re.findall(r"[a-z0-9]+", value.lower()))
        forbidden_value_tokens = _FORBIDDEN_METADATA_TOKENS - {"pnu", "path"}
        if (
            value.lower() in _FORBIDDEN_METADATA_VALUES
            or bool(value_tokens & forbidden_value_tokens)
        ):
            raise ValueError(f"forbidden public metadata value at {path}")


def validate_public_registry_projection(payload: Mapping[str, Any]) -> None:
    _exact_keys(payload, _PUBLIC_REGISTRY_KEYS, "public site registry")
    if payload.get("schema_version") != PUBLIC_SITE_REGISTRY_SCHEMA:
        raise ValueError("unsupported public site registry schema")
    version = payload.get("registry_version")
    if not isinstance(version, str) or not _REGISTRY_VERSION.fullmatch(version):
        raise ValueError("public registry version is invalid")
    for field in ("registry_core_sha256", "identity_commitment"):
        value = payload.get(field)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError(f"public registry {field} is invalid")
    sites = payload.get("sites")
    if not isinstance(sites, list) or not sites:
        raise ValueError("public registry sites must be a nonempty list")
    site_refs: list[str] = []
    for site in sites:
        if not isinstance(site, Mapping):
            raise ValueError("public registry site must be an object")
        _exact_keys(site, _PUBLIC_SITE_KEYS, "public registry site")
        site_ref = site.get("site_ref")
        if not isinstance(site_ref, str) or not _SITE_REF.fullmatch(site_ref):
            raise ValueError("public registry site_ref is invalid")
        if site.get("split") not in {"dev", "test"}:
            raise ValueError("public registry split is invalid")
        if site.get("area_bin") not in _AREA_BINS:
            raise ValueError("public registry area_bin is invalid")
        site_refs.append(site_ref)
    if site_refs != sorted(site_refs) or len(site_refs) != len(set(site_refs)):
        raise ValueError("public registry sites must have unique canonical order")
    audit_public_metadata(payload, "public_registry")


def validate_public_release_manifest(payload: Mapping[str, Any]) -> None:
    _exact_keys(payload, _RELEASE_MANIFEST_KEYS, "public release manifest")
    if payload.get("schema_version") != PUBLIC_RELEASE_MANIFEST_SCHEMA:
        raise ValueError("unsupported public release manifest schema")
    version = payload.get("registry_version")
    if not isinstance(version, str) or not _REGISTRY_VERSION.fullmatch(version):
        raise ValueError("public release registry version is invalid")
    for field in (
        "registry_core_sha256",
        "identity_commitment",
        "public_case_set_sha256",
    ):
        value = payload.get(field)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError(f"public release {field} is invalid")
    files = payload.get("files")
    if not isinstance(files, Mapping) or set(files) != set(_RELEASE_PATHS):
        raise ValueError("public release files must match the exact allowlist")
    for key, expected_path in _RELEASE_PATHS.items():
        entry = files[key]
        if not isinstance(entry, Mapping):
            raise ValueError("public release file entry must be an object")
        _exact_keys(entry, _RELEASE_FILE_KEYS, "public release file")
        if entry.get("path") != expected_path:
            raise ValueError("public release path is not allowlisted")
        count = entry.get("record_count")
        if type(count) is not int or count <= 0:
            raise ValueError("public release record_count must be positive")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("public release file hash is invalid")
    audit_public_metadata(payload, "release_manifest")


def load_projection_identity(path: Path) -> ProjectionIdentity:
    """Load a caller-supplied high-entropy secret from a private JSON sidecar."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("projection identity sidecar must be an object")
    _exact_keys(payload, _IDENTITY_KEYS, "projection identity sidecar")
    if payload.get("schema_version") != PROJECTION_IDENTITY_SCHEMA:
        raise ValueError("unsupported projection identity sidecar schema")
    secret_hex = payload.get("secret_hex")
    if not isinstance(secret_hex, str) or not _SECRET_HEX.fullmatch(secret_hex):
        raise ValueError("projection secret must be lowercase hex for at least 32 bytes")
    if len(secret_hex) % 2:
        raise ValueError("projection secret hex must contain complete bytes")
    return ProjectionIdentity(bytes.fromhex(secret_hex))


def create_projection_identity(
    path: Path,
    *,
    secret_factory: Callable[[int], bytes] = secrets.token_bytes,
) -> ProjectionIdentity:
    """Create one private sidecar atomically without following or replacing targets."""

    if os.path.lexists(path):
        raise FileExistsError(f"projection identity already exists: {path}")
    secret = secret_factory(32)
    if type(secret) is not bytes or len(secret) != 32:
        raise ValueError("projection secret factory must return exactly 32 bytes")
    identity = ProjectionIdentity(secret)
    payload = {
        "schema_version": PROJECTION_IDENTITY_SCHEMA,
        "secret_hex": secret.hex(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as exc:
            raise FileExistsError(
                f"projection identity already exists: {path}"
            ) from exc
    finally:
        temporary_path.unlink(missing_ok=True)
    return identity


def build_public_registry_projection(
    registry: Mapping[str, Any],
    identity: ProjectionIdentity,
    *,
    registry_core_hash: str,
) -> dict[str, Any]:
    """Return the exact PNU-free registry view committed by a freeze receipt."""

    version = registry.get("version")
    if not isinstance(version, str) or not _REGISTRY_VERSION.fullmatch(version):
        raise ValueError("public registry version is invalid")
    if not isinstance(registry_core_hash, str) or not _SHA256.fullmatch(
        registry_core_hash
    ):
        raise ValueError("public registry core hash is invalid")
    sites = registry.get("sites")
    if not isinstance(sites, list):
        raise ValueError("site registry has no sites list")
    public_sites: list[dict[str, str]] = []
    for site in sites:
        if not isinstance(site, Mapping):
            raise ValueError("site registry entries must be objects")
        split = str(site.get("split") or "")
        area_bin = str(site.get("area_bin") or "")
        if split not in {"dev", "test"}:
            raise ValueError("public registry site metadata is invalid")
        if area_bin not in _AREA_BINS:
            raise ValueError("public registry area_bin is invalid")
        public_sites.append(
            {
                "site_ref": identity.site_ref(str(site.get("pnu") or "")),
                "split": split,
                "area_bin": area_bin,
            }
        )
    public_sites.sort(key=lambda site: site["site_ref"])
    if len({site["site_ref"] for site in public_sites}) != len(public_sites):
        raise ValueError("duplicate public site identity")
    payload = {
        "schema_version": PUBLIC_SITE_REGISTRY_SCHEMA,
        "registry_version": version,
        "registry_core_sha256": registry_core_hash,
        "identity_commitment": identity.commitment,
        "sites": public_sites,
    }
    validate_public_registry_projection(payload)
    return payload


def _sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON artifact must be an object")
    return payload


def write_public_release(
    *,
    registry_path: Path,
    split_manifest_path: Path,
    projection_identity: ProjectionIdentity,
    public_registry_path: Path,
    freeze_receipt_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Export only allowlisted public cases and the PNU-free site projection."""

    from .dataset import verify_frozen_registry

    release_names = {
        "dev.public.jsonl",
        "test.public.jsonl",
        "site_registry.public.json",
        "release_manifest.json",
    }
    if output_dir.exists():
        unexpected = sorted(
            child.name for child in output_dir.iterdir() if child.name not in release_names
        )
        if unexpected:
            raise ValueError(
                f"public release allowlist rejects existing entries: {unexpected}"
            )

    split_manifest = verify_frozen_registry(
        registry_path,
        split_manifest_path=split_manifest_path,
        projection_identity=projection_identity,
        public_registry_path=public_registry_path,
        freeze_receipt_path=freeze_receipt_path,
    )
    by_split: dict[str, list[ArchitecturePublicCase]] = {"dev": [], "test": []}
    for key, entry in split_manifest["bundles"].items():
        split, _condition = key.split(".", maxsplit=1)
        manifest_path = (
            split_manifest_path.parent / str(entry["manifest_path"])
        ).resolve()
        case_manifest = _read_json_object(manifest_path)
        public_entry = case_manifest["files"]["public"]
        public_path = manifest_path.parent / str(public_entry["path"])
        for line in public_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, Mapping):
                    raise ValueError("public case row must be an object")
                by_split[split].append(ArchitecturePublicCase.from_dict(row))

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files: dict[str, dict[str, Any]] = {}
    for split in ("dev", "test"):
        cases = sorted(by_split[split], key=lambda case: case.case_id)
        if len({case.case_id for case in cases}) != len(cases):
            raise ValueError("duplicate public case in release")
        path = output_dir / f"{split}.public.jsonl"
        write_jsonl_atomic(path, (case.to_dict() for case in cases))
        output_files[split] = {
            "path": path.name,
            "record_count": len(cases),
            "sha256": _sha256_file(path),
        }

    public_registry = _read_json_object(public_registry_path)
    validate_public_registry_projection(public_registry)
    registry_output = output_dir / "site_registry.public.json"
    write_json_atomic(registry_output, public_registry)
    output_files["sites"] = {
        "path": registry_output.name,
        "record_count": len(public_registry["sites"]),
        "sha256": _sha256_file(registry_output),
    }
    manifest = {
        "schema_version": PUBLIC_RELEASE_MANIFEST_SCHEMA,
        "registry_version": public_registry["registry_version"],
        "registry_core_sha256": public_registry["registry_core_sha256"],
        "identity_commitment": projection_identity.commitment,
        "public_case_set_sha256": sha256_json(
            sorted(case.case_id for cases in by_split.values() for case in cases)
        ),
        "files": output_files,
    }
    validate_public_release_manifest(manifest)
    write_json_atomic(output_dir / "release_manifest.json", manifest)
    return manifest


__all__ = [
    "FREEZE_RECEIPT_SCHEMA",
    "PROJECTION_IDENTITY_SCHEMA",
    "PUBLIC_RELEASE_MANIFEST_SCHEMA",
    "PUBLIC_SITE_REGISTRY_SCHEMA",
    "build_public_registry_projection",
    "create_projection_identity",
    "audit_public_metadata",
    "load_projection_identity",
    "write_public_release",
    "validate_public_registry_projection",
    "validate_public_release_manifest",
]
