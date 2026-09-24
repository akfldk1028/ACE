"""Build deterministic, leakage-separated architecture research datasets."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .architecture_target_roster import verify_frozen_target_roster
from .arr_adapter import packet_from_arr_artifacts
from .faults import CHALLENGE_FAMILY_CENSUS, FAULT_REGISTRY, assign_fault_families
from .io import sha256_json, write_json_atomic, write_jsonl_atomic
from .projection import (
    ProjectionIdentity,
    bind_private_case,
    project_gold_record,
    project_public_case,
    verify_private_case_binding,
)
from .schema import (
    ArchitectureEvidencePacket,
    ArchitectureGoldRecord,
    ArchitecturePublicCase,
    PrivateCaseBinding,
)
from .validators import gold_from_validation


PROGRAM_ORDER = ("neighborhood", "gymnasium", "cultural")
BUNDLE_KEYS = frozenset(
    {"dev.native", "dev.challenged", "test.native", "test.challenged"}
)
LEGACY_EXPECTED_BUNDLE_COUNTS = {
    "dev.native": 6,
    "dev.challenged": 6,
    "test.native": 15,
    "test.challenged": 15,
}
CASE_MANIFEST_SCHEMA = "ace.iclr2027.case_manifest.v2"
SPLIT_MANIFEST_SCHEMA = "ace.iclr2027.split_manifest.v2"
GOLD_RECORD_SCHEMA = "ace.iclr2027.gold_record.v1"
_REGISTRY_MUTABLE_FREEZE_FIELDS = {
    "frozen",
    "split_manifest_sha256",
    "freeze_receipt_sha256",
}


def registry_expected_bundle_counts(registry: Mapping[str, Any]) -> dict[str, int]:
    """Load strict protocol counts, with compatibility for legacy registries."""

    if "expected_bundle_counts" not in registry:
        return dict(LEGACY_EXPECTED_BUNDLE_COUNTS)
    raw = registry["expected_bundle_counts"]
    if not isinstance(raw, Mapping) or set(raw) != BUNDLE_KEYS:
        raise ValueError("expected_bundle_counts must contain exactly four bundle keys")
    counts: dict[str, int] = {}
    for key in sorted(BUNDLE_KEYS):
        value = raw[key]
        if type(value) is not int or value <= 0:
            raise ValueError("expected bundle counts must be positive integers")
        counts[key] = value
    for split in ("dev", "test"):
        if counts[f"{split}.native"] != counts[f"{split}.challenged"]:
            raise ValueError("native and challenged bundle counts must match")
    sites = registry.get("sites")
    if not isinstance(sites, list) or any(
        not isinstance(site, Mapping) for site in sites
    ):
        raise ValueError("site registry has no valid sites list")
    for split in ("dev", "test"):
        site_count = sum(site.get("split") == split for site in sites)
        if counts[f"{split}.native"] != site_count * len(PROGRAM_ORDER):
            raise ValueError(
                f"expected {split} bundle count does not match site count times three"
            )
    return counts


def verified_development_target_count(
    *,
    target_roster_path: Path | None,
    target_roster_receipt_path: Path | None,
    projection_identity_commitment: str,
) -> int | None:
    """Return receipt-bound typed-target count without changing legacy cases."""

    if (target_roster_path is None) != (target_roster_receipt_path is None):
        raise ValueError("target roster and receipt must be supplied together")
    if target_roster_path is None:
        return None
    receipt = verify_frozen_target_roster(
        target_roster_path,
        target_roster_receipt_path,
        projection_identity_commitment=projection_identity_commitment,
    )
    return receipt.combined_dev_target_count


@dataclass(frozen=True)
class CaseBuildResult:
    split: str
    condition: str
    registry_version: str
    packets: tuple[ArchitectureEvidencePacket, ...]
    gold_records: tuple[ArchitectureGoldRecord, ...]
    source_artifacts: tuple["SourceArtifact", ...] = ()
    registry_core_sha256: str = ""
    expected_bundle_counts: Mapping[str, int] = field(
        default_factory=lambda: dict(LEGACY_EXPECTED_BUNDLE_COUNTS)
    )


@dataclass(frozen=True)
class SourceArtifact:
    path: Path
    sha256: str


def _load_registry(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("site registry root must be an object")
    if payload.get("schema_version") != "ace.iclr2027.site_registry.v1":
        raise ValueError("unsupported site registry schema")
    if not str(payload.get("version") or "").strip():
        raise ValueError("site registry version must be nonempty")
    registry_expected_bundle_counts(payload)
    return payload


def registry_core_sha256(registry: Mapping[str, Any]) -> str:
    """Hash immutable registry content while excluding freeze receipt fields."""

    core = {
        str(key): value
        for key, value in registry.items()
        if str(key) not in _REGISTRY_MUTABLE_FREEZE_FIELDS
    }
    return sha256_json(core)


def _artifact_path(registry_path: Path, raw_path: Any) -> Path:
    path = Path(str(raw_path or ""))
    if not path.is_absolute():
        path = registry_path.parent / path
    return path.resolve()


def _manifest_artifact_path(path: Path, *, manifest_directory: Path) -> str:
    try:
        rendered = os.path.relpath(path.resolve(), manifest_directory.resolve())
    except ValueError:
        rendered = str(path.resolve())
    return rendered.replace("\\", "/")


def build_native_cases(registry_path: Path, *, split: str) -> CaseBuildResult:
    """Convert all registered native ARR artifacts for one split."""

    if split not in {"dev", "test"}:
        raise ValueError("split must be dev or test")
    registry = _load_registry(registry_path)
    expected_bundle_counts = registry_expected_bundle_counts(registry)
    sites = registry.get("sites")
    if not isinstance(sites, list):
        raise ValueError("site registry has no sites list")

    packets: list[ArchitectureEvidencePacket] = []
    gold_records: list[ArchitectureGoldRecord] = []
    sources: dict[Path, SourceArtifact] = {}
    selected_sites = sorted(
        (
            site
            for site in sites
            if isinstance(site, Mapping) and site.get("split") == split
        ),
        key=lambda site: str(site.get("pnu") or ""),
    )
    if not selected_sites:
        raise ValueError(f"site registry has no sites for split={split}")

    for site in selected_sites:
        pnu = str(site.get("pnu") or "")
        artifacts = site.get("artifacts")
        if not isinstance(artifacts, Mapping) or not artifacts:
            raise ValueError(f"site {pnu} has no program artifacts")
        for program in PROGRAM_ORDER:
            if program not in artifacts:
                continue
            summary_path = _artifact_path(registry_path, artifacts[program])
            if not summary_path.is_file():
                raise ValueError(f"ARR artifact does not exist: {summary_path}")
            case_id = f"{split}-{pnu}-{program}-native"
            packet, gold = packet_from_arr_artifacts(
                summary_path,
                pnu=pnu,
                program=program,
                case_id=case_id,
            )
            source_sha256 = _sha256_file(summary_path)
            if packet.source_artifact_sha256 != source_sha256:
                raise ValueError("packet source artifact hash mismatch")
            sources[summary_path] = SourceArtifact(summary_path, source_sha256)
            packets.append(packet)
            gold_records.append(gold)

    if not packets:
        raise ValueError(f"no native cases built for split={split}")
    return CaseBuildResult(
        split=split,
        condition="native",
        registry_version=str(registry["version"]),
        packets=tuple(packets),
        gold_records=tuple(gold_records),
        source_artifacts=tuple(
            sources[path] for path in sorted(sources, key=lambda item: str(item))
        ),
        registry_core_sha256=registry_core_sha256(registry),
        expected_bundle_counts=expected_bundle_counts,
    )


def build_challenged_cases(registry_path: Path, *, split: str) -> CaseBuildResult:
    """Build one independently validated challenged case per native case."""

    return _challenge_native_result(build_native_cases(registry_path, split=split))


def _challenge_native_result(native: CaseBuildResult) -> CaseBuildResult:
    """Apply only faults valid for each subject's evidence stage."""

    execution_packets = tuple(
        packet for packet in native.packets if packet.subject_kind == "execution"
    )
    expected_native_count = native.expected_bundle_counts.get(f"{native.split}.native")
    complete_development = (
        native.split == "dev"
        and expected_native_count is not None
        and len(native.packets) == expected_native_count
    )
    if complete_development and len(execution_packets) != len(CHALLENGE_FAMILY_CENSUS):
        raise ValueError(
            f"a complete development challenge requires exactly "
            f"{len(CHALLENGE_FAMILY_CENSUS)} "
            "execution packets"
        )
    assignment = assign_fault_families(packet.case_id for packet in execution_packets)
    if complete_development and sorted(assignment.values()) != sorted(
        CHALLENGE_FAMILY_CENSUS
    ):
        raise ValueError(
            "complete development challenge must assign every registered family once"
        )
    packets: list[ArchitectureEvidencePacket] = []
    gold_records: list[ArchitectureGoldRecord] = []
    for packet in native.packets:
        if packet.subject_kind == "execution":
            family = assignment[packet.case_id]
            challenged = FAULT_REGISTRY[family](packet)
        else:
            family = "portfolio_attempt_hash"
            payload = packet.to_dict()
            payload["condition"] = "challenged"
            if str(payload["case_id"]).endswith("-native"):
                payload["case_id"] = (
                    str(payload["case_id"])[: -len("-native")] + "-challenged"
                )
            payload["attempt_hash"] = "0" * 64
            challenged = ArchitectureEvidencePacket.from_dict(payload)
        packets.append(challenged)
        gold_records.append(gold_from_validation(challenged, mutation_family=family))
    return CaseBuildResult(
        split=native.split,
        condition="challenged",
        registry_version=native.registry_version,
        packets=tuple(packets),
        gold_records=tuple(gold_records),
        source_artifacts=native.source_artifacts,
        registry_core_sha256=native.registry_core_sha256,
        expected_bundle_counts=dict(native.expected_bundle_counts),
    )


def build_cases(
    registry_path: Path,
    *,
    split: str,
    condition: str,
) -> CaseBuildResult:
    if condition == "native":
        return build_native_cases(registry_path, split=split)
    if condition == "challenged":
        return build_challenged_cases(registry_path, split=split)
    raise ValueError("condition must be native or challenged")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_positive_count(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} case count must be a positive integer")
    return value


def write_case_bundle(
    result: CaseBuildResult,
    *,
    output_dir: Path,
    projection_identity: ProjectionIdentity,
) -> dict[str, Any]:
    """Atomically write a public/internal/gold v2 bundle and hash manifest."""

    if len(result.packets) != len(result.gold_records):
        raise ValueError("internal packet and gold cardinality mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", result.registry_core_sha256):
        raise ValueError("case result requires a canonical registry core hash")

    public_cases: list[ArchitecturePublicCase] = []
    bindings: list[PrivateCaseBinding] = []
    public_gold: list[ArchitectureGoldRecord] = []
    for packet, internal_gold in zip(result.packets, result.gold_records):
        public_case = project_public_case(packet, projection_identity)
        gold_record = project_gold_record(
            internal_gold,
            packet,
            projection_identity,
        )
        binding = bind_private_case(
            public_case,
            packet,
            gold_record,
            projection_identity,
        )
        public_cases.append(public_case)
        bindings.append(binding)
        public_gold.append(gold_record)

    case_ids = [case.case_id for case in public_cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate public case identity")
    if [binding.public_case_id for binding in bindings] != case_ids:
        raise ValueError("public and internal binding ordering mismatch")
    if [record.case_id for record in public_gold] != case_ids:
        raise ValueError("public and gold case ordering mismatch")

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{result.split}.{result.condition}"
    public_path = output_dir / f"{stem}.public.jsonl"
    internal_path = output_dir / f"{stem}.internal.jsonl"
    gold_path = output_dir / f"{stem}.gold.jsonl"
    manifest_path = output_dir / f"{stem}.manifest.json"
    write_jsonl_atomic(public_path, (case.to_dict() for case in public_cases))
    write_jsonl_atomic(internal_path, (binding.to_dict() for binding in bindings))
    write_jsonl_atomic(gold_path, (record.to_dict() for record in public_gold))

    file_specs = {
        "public": (public_path, ArchitecturePublicCase.SCHEMA_VERSION),
        "internal": (internal_path, PrivateCaseBinding.SCHEMA_VERSION),
        "gold": (gold_path, GOLD_RECORD_SCHEMA),
    }
    manifest: dict[str, Any] = {
        "schema_version": CASE_MANIFEST_SCHEMA,
        "registry_version": result.registry_version,
        "registry_core_sha256": result.registry_core_sha256,
        "identity_commitment": projection_identity.commitment,
        "split": result.split,
        "condition": result.condition,
        "case_count": len(case_ids),
        "case_ids": case_ids,
        "sources": [
            {
                "source_id": f"source:{source.sha256}",
                "sha256": source.sha256,
            }
            for source in result.source_artifacts
        ],
        "files": {
            side: {
                "path": path.name,
                "schema_version": schema_version,
                "record_count": len(case_ids),
                "sha256": _sha256_file(path),
            }
            for side, (path, schema_version) in file_specs.items()
        },
    }
    write_json_atomic(manifest_path, manifest)
    return manifest


def update_split_manifest(
    bundle_manifest: Mapping[str, Any],
    *,
    bundle_manifest_path: Path,
    split_manifest_path: Path,
) -> dict[str, Any]:
    """Atomically bind one case bundle into the four-way split manifest."""

    if bundle_manifest.get("schema_version") != CASE_MANIFEST_SCHEMA:
        raise ValueError("unsupported case bundle manifest")
    key = f"{bundle_manifest.get('split')}.{bundle_manifest.get('condition')}"
    if key not in BUNDLE_KEYS:
        raise ValueError(f"unsupported case bundle key: {key}")
    bundle_case_count = _strict_positive_count(
        bundle_manifest.get("case_count"), "bundle manifest"
    )
    if split_manifest_path.is_file():
        payload = json.loads(split_manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("split manifest must be an object")
        if payload.get("schema_version") != SPLIT_MANIFEST_SCHEMA:
            raise ValueError("unsupported split manifest schema")
    else:
        payload = {
            "schema_version": SPLIT_MANIFEST_SCHEMA,
            "registry_version": bundle_manifest.get("registry_version"),
            "registry_core_sha256": bundle_manifest.get("registry_core_sha256"),
            "identity_commitment": bundle_manifest.get("identity_commitment"),
            "bundles": {},
        }
    if payload.get("registry_version") != bundle_manifest.get("registry_version"):
        raise ValueError("split manifest registry version mismatch")
    if payload.get("registry_core_sha256") != bundle_manifest.get(
        "registry_core_sha256"
    ):
        raise ValueError("split manifest registry core mismatch")
    if payload.get("identity_commitment") != bundle_manifest.get("identity_commitment"):
        raise ValueError("split manifest identity commitment mismatch")
    relative_path = os.path.relpath(
        bundle_manifest_path.resolve(),
        split_manifest_path.parent.resolve(),
    ).replace("\\", "/")
    payload.setdefault("bundles", {})[key] = {
        "manifest_path": relative_path,
        "manifest_sha256": _sha256_file(bundle_manifest_path),
        "case_count": bundle_case_count,
    }
    payload["bundles"] = dict(sorted(payload["bundles"].items()))
    write_json_atomic(split_manifest_path, payload)
    return payload


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    return payload


def _read_jsonl_objects(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{label} row {line_number} must be an object")
        rows.append(row)
    return rows


def _registry_artifact_hashes(
    registry: Mapping[str, Any],
    *,
    registry_path: Path,
) -> dict[tuple[str, str], str]:
    sites = registry.get("sites")
    if not isinstance(sites, list):
        raise ValueError("site registry has no sites list")
    hashes: dict[tuple[str, str], str] = {}
    for site in sites:
        if not isinstance(site, Mapping):
            raise ValueError("site registry entries must be objects")
        pnu = str(site.get("pnu") or "")
        split = str(site.get("split") or "")
        if not re.fullmatch(r"[0-9]{19}", pnu) or split not in {"dev", "test"}:
            raise ValueError("site registry identity or split is invalid")
        artifacts = site.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ValueError(f"site {pnu} has no program artifacts")
        for program, raw_path in artifacts.items():
            key = (pnu, str(program))
            if key in hashes:
                raise ValueError("duplicate registry site/program membership")
            path = _artifact_path(registry_path, raw_path)
            if not path.is_file():
                raise ValueError("registry artifact does not exist")
            hashes[key] = _sha256_file(path)
    return hashes


def _verify_split_manifest(
    registry: Mapping[str, Any],
    split_manifest_path: Path,
    *,
    registry_path: Path,
    projection_identity: ProjectionIdentity,
) -> dict[str, Any]:
    split_manifest = _read_json_object(split_manifest_path, "split manifest")
    if split_manifest.get("schema_version") != SPLIT_MANIFEST_SCHEMA:
        raise ValueError("unsupported split manifest schema")
    if split_manifest.get("registry_version") != registry.get("version"):
        raise ValueError("split manifest registry version mismatch")
    core_hash = registry_core_sha256(registry)
    if split_manifest.get("registry_core_sha256") != core_hash:
        raise ValueError("split manifest registry core mismatch")
    if split_manifest.get("identity_commitment") != projection_identity.commitment:
        raise ValueError("split manifest identity commitment mismatch")
    bundles = split_manifest.get("bundles")
    if not isinstance(bundles, Mapping):
        raise ValueError("split manifest has no bundles")
    expected_bundle_counts = registry_expected_bundle_counts(registry)
    if set(bundles) != BUNDLE_KEYS:
        raise ValueError("split manifest does not contain all four research bundles")
    registry_hashes = _registry_artifact_hashes(
        registry,
        registry_path=registry_path,
    )
    all_public_ids: set[str] = set()
    for key, expected_count in expected_bundle_counts.items():
        entry = bundles[key]
        if not isinstance(entry, Mapping):
            raise ValueError(f"invalid split bundle entry: {key}")
        manifest_path = (
            split_manifest_path.parent / str(entry.get("manifest_path") or "")
        ).resolve()
        if _sha256_file(manifest_path) != entry.get("manifest_sha256"):
            raise ValueError(f"case manifest hash mismatch: {key}")
        manifest = _read_json_object(manifest_path, f"case manifest {key}")
        expected_split, expected_condition = key.split(".", maxsplit=1)
        if (
            manifest.get("schema_version") != CASE_MANIFEST_SCHEMA
            or manifest.get("registry_version") != registry.get("version")
            or manifest.get("split") != expected_split
            or manifest.get("condition") != expected_condition
        ):
            raise ValueError(f"case manifest metadata mismatch: {key}")
        if manifest.get("registry_core_sha256") != core_hash:
            raise ValueError(f"case manifest registry core mismatch: {key}")
        if manifest.get("identity_commitment") != projection_identity.commitment:
            raise ValueError(f"case manifest identity commitment mismatch: {key}")
        if (
            _strict_positive_count(manifest.get("case_count"), "bundle manifest")
            != expected_count
        ):
            raise ValueError(f"case count mismatch: {key}")
        if (
            _strict_positive_count(entry.get("case_count"), "split manifest entry")
            != expected_count
        ):
            raise ValueError(f"split entry case count mismatch: {key}")
        expected_ids = list(manifest.get("case_ids") or ())
        if (
            len(expected_ids) != expected_count
            or len(set(expected_ids)) != expected_count
        ):
            raise ValueError(f"case ID cardinality mismatch: {key}")
        sources = manifest.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"source artifacts missing: {key}")
        source_hashes: set[str] = set()
        for source in sources:
            if not isinstance(source, Mapping):
                raise ValueError(f"source artifact entry invalid: {key}")
            if set(source) != {"source_id", "sha256"}:
                raise ValueError(f"source artifact entry has forbidden fields: {key}")
            source_id = str(source.get("source_id") or "").strip()
            expected_source_hash = str(source.get("sha256") or "").strip()
            if (
                not re.fullmatch(r"[0-9a-f]{64}", expected_source_hash)
                or source_id != f"source:{expected_source_hash}"
            ):
                raise ValueError(f"source artifact identity mismatch: {key}")
            if expected_source_hash in source_hashes:
                raise ValueError(f"duplicate source artifact identity: {key}")
            source_hashes.add(expected_source_hash)
        files = manifest.get("files")
        if not isinstance(files, Mapping) or set(files) != {
            "public",
            "internal",
            "gold",
        }:
            raise ValueError(f"case files missing: {key}")
        expected_schemas = {
            "public": ArchitecturePublicCase.SCHEMA_VERSION,
            "internal": PrivateCaseBinding.SCHEMA_VERSION,
            "gold": GOLD_RECORD_SCHEMA,
        }
        rows_by_side: dict[str, list[dict[str, Any]]] = {}
        for side in ("public", "internal", "gold"):
            file_entry = files.get(side)
            if not isinstance(file_entry, Mapping):
                raise ValueError(f"{side} file entry missing: {key}")
            if file_entry.get("schema_version") != expected_schemas[side]:
                raise ValueError(f"{side} file schema mismatch: {key}")
            if (
                _strict_positive_count(file_entry.get("record_count"), f"{side} file")
                != expected_count
            ):
                raise ValueError(f"{side} record count mismatch: {key}")
            data_path = manifest_path.parent / str(file_entry.get("path") or "")
            if _sha256_file(data_path) != file_entry.get("sha256"):
                raise ValueError(f"{side} hash mismatch: {key}")
            rows = _read_jsonl_objects(data_path, f"{side} file")
            if len(rows) != expected_count:
                raise ValueError(f"{side} record count mismatch: {key}")
            rows_by_side[side] = rows

        public_cases = tuple(
            ArchitecturePublicCase.from_dict(row) for row in rows_by_side["public"]
        )
        bindings = tuple(
            PrivateCaseBinding.from_dict(row) for row in rows_by_side["internal"]
        )
        gold_records = tuple(
            ArchitectureGoldRecord.from_dict(row) for row in rows_by_side["gold"]
        )
        if [case.case_id for case in public_cases] != expected_ids:
            raise ValueError(f"public case ID order mismatch: {key}")
        if [binding.public_case_id for binding in bindings] != expected_ids:
            raise ValueError(f"internal case ID order mismatch: {key}")
        if [record.case_id for record in gold_records] != expected_ids:
            raise ValueError(f"gold case ID order mismatch: {key}")
        if all_public_ids.intersection(expected_ids):
            raise ValueError("public case IDs must be unique across all bundles")
        all_public_ids.update(expected_ids)

        bound_source_hashes: set[str] = set()
        for public_case, binding, gold_record in zip(
            public_cases, bindings, gold_records
        ):
            packet = verify_private_case_binding(
                public_case,
                binding,
                gold_record,
                projection_identity,
            )
            if packet.condition != expected_condition:
                raise ValueError(f"private condition mismatch: {key}")
            registry_source_hash = registry_hashes.get((packet.pnu, packet.program))
            if registry_source_hash is None:
                raise ValueError(f"private packet is not a registry member: {key}")
            if packet.source_artifact_sha256 != registry_source_hash:
                raise ValueError(f"private packet source hash mismatch: {key}")
            bound_source_hashes.add(registry_source_hash)
        if bound_source_hashes != source_hashes:
            raise ValueError(f"case manifest source set mismatch: {key}")
    return split_manifest


def freeze_site_registry(
    registry_path: Path,
    *,
    split_manifest_path: Path,
    projection_identity: ProjectionIdentity,
    public_registry_path: Path,
    freeze_receipt_path: Path,
) -> dict[str, Any]:
    """Freeze a registry only after all expected bundle hashes validate."""

    registry = _read_json_object(registry_path, "site registry")
    split_manifest = _verify_split_manifest(
        registry,
        split_manifest_path,
        registry_path=registry_path,
        projection_identity=projection_identity,
    )
    from .release import (
        FREEZE_RECEIPT_SCHEMA,
        audit_public_metadata,
        build_public_registry_projection,
    )

    public_registry = build_public_registry_projection(
        registry,
        projection_identity,
        registry_core_hash=registry_core_sha256(registry),
    )
    write_json_atomic(public_registry_path, public_registry)
    case_ids = sorted(
        case_id
        for entry in split_manifest["bundles"].values()
        for case_id in _read_json_object(
            (
                split_manifest_path.parent / str(entry.get("manifest_path") or "")
            ).resolve(),
            "case manifest",
        )["case_ids"]
    )
    receipt = {
        "schema_version": FREEZE_RECEIPT_SCHEMA,
        "registry_version": registry.get("version"),
        "registry_core_sha256": registry_core_sha256(registry),
        "identity_commitment": projection_identity.commitment,
        "split_manifest_sha256": _sha256_file(split_manifest_path),
        "public_registry_sha256": _sha256_file(public_registry_path),
        "public_case_set_sha256": sha256_json(case_ids),
    }
    audit_public_metadata(receipt, "freeze_receipt")
    write_json_atomic(freeze_receipt_path, receipt)
    registry["frozen"] = True
    registry["split_manifest_sha256"] = _sha256_file(split_manifest_path)
    registry["freeze_receipt_sha256"] = _sha256_file(freeze_receipt_path)
    write_json_atomic(registry_path, registry)
    return registry


def verify_frozen_registry(
    registry_path: Path,
    *,
    split_manifest_path: Path,
    projection_identity: ProjectionIdentity,
    public_registry_path: Path,
    freeze_receipt_path: Path,
) -> dict[str, Any]:
    """Fail closed if the frozen registry or any bound case artifact changed."""

    registry = _read_json_object(registry_path, "site registry")
    if registry.get("frozen") is not True:
        raise ValueError("site registry is not frozen")
    receipt = _read_json_object(freeze_receipt_path, "freeze receipt")
    from .release import (
        FREEZE_RECEIPT_SCHEMA,
        build_public_registry_projection,
    )

    receipt_keys = {
        "schema_version",
        "registry_version",
        "registry_core_sha256",
        "identity_commitment",
        "split_manifest_sha256",
        "public_registry_sha256",
        "public_case_set_sha256",
    }
    if (
        set(receipt) != receipt_keys
        or receipt.get("schema_version") != FREEZE_RECEIPT_SCHEMA
    ):
        raise ValueError("unsupported freeze receipt schema")
    core_hash = registry_core_sha256(registry)
    if receipt.get("registry_core_sha256") != core_hash:
        raise ValueError("frozen registry core mismatch")
    if receipt.get("identity_commitment") != projection_identity.commitment:
        raise ValueError("frozen identity commitment mismatch")
    if _sha256_file(freeze_receipt_path) != registry.get("freeze_receipt_sha256"):
        raise ValueError("freeze receipt hash mismatch")
    expected_hash = str(registry.get("split_manifest_sha256") or "")
    if (
        _sha256_file(split_manifest_path) != expected_hash
        or receipt.get("split_manifest_sha256") != expected_hash
    ):
        raise ValueError("split manifest hash mismatch")
    if _sha256_file(public_registry_path) != receipt.get("public_registry_sha256"):
        raise ValueError("public registry hash mismatch")
    expected_public_registry = build_public_registry_projection(
        registry,
        projection_identity,
        registry_core_hash=core_hash,
    )
    if (
        _read_json_object(public_registry_path, "public registry")
        != expected_public_registry
    ):
        raise ValueError("public registry projection mismatch")
    split_manifest = _verify_split_manifest(
        registry,
        split_manifest_path,
        registry_path=registry_path,
        projection_identity=projection_identity,
    )
    case_ids = sorted(
        case_id
        for entry in split_manifest["bundles"].values()
        for case_id in _read_json_object(
            (
                split_manifest_path.parent / str(entry.get("manifest_path") or "")
            ).resolve(),
            "case manifest",
        )["case_ids"]
    )
    if receipt.get("public_case_set_sha256") != sha256_json(case_ids):
        raise ValueError("public case set hash mismatch")
    return split_manifest
