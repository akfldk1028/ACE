"""Build leakage-safe CATS prefix artifacts from the frozen development snapshot."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from iclr2027.artifact_receipts import (
    canonical_artifact_receipt,
    verify_artifact_receipt,
)
from iclr2027.dataset import CASE_MANIFEST_SCHEMA, GOLD_RECORD_SCHEMA, SPLIT_MANIFEST_SCHEMA
from iclr2027.io import canonical_json, sha256_json, write_json_atomic, write_jsonl_atomic
from iclr2027.projection import ProjectionIdentity, verify_private_case_binding
from iclr2027.release import PROJECTION_IDENTITY_SCHEMA
from iclr2027.schema import (
    ArchitectureEvidencePacket,
    ArchitectureGoldRecord,
    ArchitecturePublicCase,
    PrivateCaseBinding,
)
from iclr2027.secure_files import read_authenticated_file
from iclr2027.study_contract import StudyContract
from iclr2027.trajectory_features import (
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    DatasetManifest,
    PrefixRuntimeFeature,
    PrivatePrefixLabel,
    TrajectoryGroupAssignment,
    assign_site_groups,
    fit_text_distance,
    private_prefix_labels,
    runtime_features,
    trajectory_id_from_resume_key,
)
from iclr2027.trajectory_ingest import (
    DEVELOPMENT_SNAPSHOT_SCHEMA,
    DevelopmentSnapshot,
    build_development_snapshot_receipt,
    load_development_snapshot,
)
from iclr2027.usage_ledger import build_usage_ledger


DATASET_MANIFEST_SCHEMA = "ace.iclr2027.cats_dataset_manifest.v1"
RUNTIME_FEATURE_SCHEMA = "ace.iclr2027.cats_prefix_runtime_feature.v1"
PRIVATE_LABEL_SCHEMA = "ace.iclr2027.cats_private_prefix_label.v1"
GROUP_ASSIGNMENT_SCHEMA = "ace.iclr2027.cats_group_assignments.v1"
DATASET_ARTIFACT_RECEIPT_SCHEMA = "ace.iclr2027.cats_dataset_artifacts.v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_PROJECTION_SECRET_HEX = re.compile(r"[0-9a-f]{64,}\Z")


@dataclass(frozen=True)
class _DevelopmentCase:
    public_case: ArchitecturePublicCase
    packet: ArchitectureEvidencePacket
    gold: ArchitectureGoldRecord


def _has_held_out_marker(path: Path) -> bool:
    return any(
        part.lower() == "test"
        or part.lower().startswith(("test.", "test-", "ood.", "ood-"))
        for part in path.parts
    )


def _assert_development_only_paths(paths: Sequence[Path] | None) -> None:
    if paths is None:
        return
    for path in paths:
        if _has_held_out_marker(Path(path)):
            raise PermissionError("held-out access is locked")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(
        read_authenticated_file(path, label=f"development artifact {path.name}")
    ).hexdigest()


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        artifact = read_authenticated_file(path, label=label)
        payload = json.loads(artifact.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    return payload


def _load_projection_identity(path: Path) -> ProjectionIdentity:
    payload = _read_json_object(path, "projection identity sidecar")
    if set(payload) != {"schema_version", "secret_hex"}:
        raise ValueError("projection identity sidecar fields are not exact")
    if payload.get("schema_version") != PROJECTION_IDENTITY_SCHEMA:
        raise ValueError("unsupported projection identity sidecar schema")
    secret_hex = payload.get("secret_hex")
    if not isinstance(secret_hex, str) or not _PROJECTION_SECRET_HEX.fullmatch(
        secret_hex
    ):
        raise ValueError("projection secret must be lowercase hex for at least 32 bytes")
    if len(secret_hex) % 2:
        raise ValueError("projection secret hex must contain complete bytes")
    return ProjectionIdentity(bytes.fromhex(secret_hex))


def _read_jsonl_objects(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        artifact = read_authenticated_file(path, label=label)
        lines = artifact.decode("utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"{label} is not readable JSON Lines") from error
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{label} row {line_number} is not JSON") from error
        if not isinstance(row, dict):
            raise ValueError(f"{label} row {line_number} must be an object")
        rows.append(row)
    return rows


def _safe_development_path(root: Path, relative_path: object) -> Path:
    raw = str(relative_path or "")
    candidate_path = Path(raw)
    _assert_development_only_paths((candidate_path,))
    if (
        not raw
        or candidate_path.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate_path.parts)
    ):
        raise ValueError("development artifact path must be relative")
    absolute_root = root.absolute()
    absolute = (root / candidate_path).absolute()
    try:
        absolute.relative_to(absolute_root)
    except ValueError as error:
        raise ValueError("development artifact path escapes its root") from error
    return root / candidate_path


def _verify_snapshot(
    snapshot_path: Path,
    *,
    results: Path,
) -> tuple[DevelopmentSnapshot, dict[str, Any]]:
    receipt = _read_json_object(snapshot_path, "development snapshot receipt")
    if receipt.get("schema_version") != DEVELOPMENT_SNAPSHOT_SCHEMA:
        raise ValueError("unsupported development snapshot receipt schema")
    receipt_sha256 = receipt.get("receipt_sha256")
    if not isinstance(receipt_sha256, str) or not _SHA256.fullmatch(receipt_sha256):
        raise ValueError("development snapshot receipt hash is invalid")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if sha256_json(body) != receipt_sha256:
        raise ValueError("development snapshot receipt self-hash mismatch")
    source_receipt = receipt.get("source_artifact_receipt")
    if not isinstance(source_receipt, Mapping):
        raise ValueError("development snapshot source receipt is missing")
    verify_artifact_receipt(source_receipt, root=results)
    snapshot = load_development_snapshot(results, expected_count=450)
    rebuilt = build_development_snapshot_receipt(
        snapshot,
        results_dir=results,
        pilot_gate_path=results / "pilot_gate.json",
    )
    if canonical_json(rebuilt) != canonical_json(receipt):
        raise ValueError("development snapshot receipt does not match loaded snapshot")
    if sha256_json(receipt.get("study_contract")) != sha256_json(
        asdict(StudyContract.primary())
    ):
        raise ValueError("snapshot study contract does not match the method lock")
    return snapshot, receipt


def _validated_bundle_rows(
    *,
    split_manifest_path: Path,
    split_manifest: Mapping[str, Any],
    key: str,
    identity,
) -> tuple[_DevelopmentCase, ...]:
    bundles = split_manifest.get("bundles")
    if not isinstance(bundles, Mapping):
        raise ValueError("split manifest has no bundle metadata")
    entry = bundles.get(key)
    if not isinstance(entry, Mapping):
        raise ValueError(f"split manifest is missing {key}")
    manifest_path = _safe_development_path(
        split_manifest_path.parent, entry.get("manifest_path")
    )
    if _sha256_file(manifest_path) != entry.get("manifest_sha256"):
        raise ValueError(f"case manifest hash mismatch: {key}")
    manifest = _read_json_object(manifest_path, f"case manifest {key}")
    expected_split, condition = key.split(".", maxsplit=1)
    if (
        manifest.get("schema_version") != CASE_MANIFEST_SCHEMA
        or manifest.get("split") != expected_split
        or manifest.get("condition") != condition
        or manifest.get("identity_commitment") != identity.commitment
        or manifest.get("registry_version") != split_manifest.get("registry_version")
        or manifest.get("registry_core_sha256")
        != split_manifest.get("registry_core_sha256")
    ):
        raise ValueError(f"case manifest metadata mismatch: {key}")
    case_count = manifest.get("case_count")
    if type(case_count) is not int or case_count <= 0 or entry.get("case_count") != case_count:
        raise ValueError(f"case count mismatch: {key}")
    expected_ids = manifest.get("case_ids")
    if (
        not isinstance(expected_ids, list)
        or len(expected_ids) != case_count
        or len(set(expected_ids)) != case_count
    ):
        raise ValueError(f"case ID cardinality mismatch: {key}")
    files = manifest.get("files")
    if not isinstance(files, Mapping) or set(files) != {"public", "internal", "gold"}:
        raise ValueError(f"case files missing: {key}")
    expected_schemas = {
        "public": ArchitecturePublicCase.SCHEMA_VERSION,
        "internal": PrivateCaseBinding.SCHEMA_VERSION,
        "gold": GOLD_RECORD_SCHEMA,
    }
    rows_by_side: dict[str, list[dict[str, Any]]] = {}
    for side in ("public", "internal", "gold"):
        file_entry = files[side]
        if (
            not isinstance(file_entry, Mapping)
            or file_entry.get("schema_version") != expected_schemas[side]
            or file_entry.get("record_count") != case_count
        ):
            raise ValueError(f"{side} file metadata mismatch: {key}")
        data_path = _safe_development_path(manifest_path.parent, file_entry.get("path"))
        if _sha256_file(data_path) != file_entry.get("sha256"):
            raise ValueError(f"{side} file hash mismatch: {key}")
        rows = _read_jsonl_objects(data_path, f"{side} file {key}")
        if len(rows) != case_count:
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
    if (
        [case.case_id for case in public_cases] != expected_ids
        or [binding.public_case_id for binding in bindings] != expected_ids
        or [gold.case_id for gold in gold_records] != expected_ids
    ):
        raise ValueError(f"case bundle ordering mismatch: {key}")
    cases: list[_DevelopmentCase] = []
    for public_case, binding, gold in zip(
        public_cases, bindings, gold_records, strict=True
    ):
        packet = verify_private_case_binding(public_case, binding, gold, identity)
        if packet.condition != condition:
            raise ValueError(f"private condition mismatch: {key}")
        cases.append(_DevelopmentCase(public_case, packet, gold))
    return tuple(cases)


def _load_development_cases(
    split_manifest_path: Path,
    projection_identity_path: Path,
) -> tuple[tuple[_DevelopmentCase, ...], str, str]:
    identity = _load_projection_identity(projection_identity_path)
    split_manifest = _read_json_object(split_manifest_path, "split manifest")
    if split_manifest.get("schema_version") != SPLIT_MANIFEST_SCHEMA:
        raise ValueError("unsupported split manifest schema")
    if split_manifest.get("identity_commitment") != identity.commitment:
        raise ValueError("split manifest identity commitment mismatch")
    bundles = split_manifest.get("bundles")
    if not isinstance(bundles, Mapping) or not {
        "dev.native",
        "dev.challenged",
    }.issubset(bundles):
        raise ValueError("split manifest does not bind both development bundles")
    cases = tuple(
        case
        for key in ("dev.native", "dev.challenged")
        for case in _validated_bundle_rows(
            split_manifest_path=split_manifest_path,
            split_manifest=split_manifest,
            key=key,
            identity=identity,
        )
    )
    if len(cases) != 30 or len({case.public_case.case_id for case in cases}) != 30:
        raise ValueError("development case census must contain exactly 30 unique cases")
    if len({case.public_case.site_ref for case in cases}) != 5:
        raise ValueError("development case census must contain exactly five sites")
    return cases, identity.commitment, _sha256_file(split_manifest_path)


def _agent_turns(transaction: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    raw = transaction.get("raw")
    raw = raw if isinstance(raw, Mapping) else {}
    result = raw.get("result")
    result = result if isinstance(result, Mapping) else {}
    turns = result.get("turns")
    if isinstance(turns, (str, bytes)) or not isinstance(turns, Sequence):
        raise ValueError("development transaction turns are invalid")
    return tuple(
        turn
        for turn in turns
        if isinstance(turn, Mapping) and str(turn.get("source") or "").lower() != "user"
    )


def _artifact_entry(path: Path, *, schema_version: str, record_count: int) -> dict[str, Any]:
    return {
        "record_count": record_count,
        "schema_version": schema_version,
        "sha256": _sha256_file(path),
    }


def build_dataset(
    *,
    case_paths: Sequence[Path] | None = None,
    method_lock: StudyContract | None = None,
    snapshot: Path | None = None,
    results: Path | None = None,
    split_manifest: Path | None = None,
    projection_identity: Path | None = None,
    epsilon: float | None = None,
    output: Path | None = None,
) -> DatasetManifest:
    """Build separated runtime, label, and group artifacts from development only."""

    _assert_development_only_paths(case_paths)
    contract = StudyContract.primary()
    if method_lock != contract:
        raise ValueError("method lock must equal the frozen primary StudyContract")
    required_paths = {
        "snapshot": snapshot,
        "results": results,
        "split_manifest": split_manifest,
        "projection_identity": projection_identity,
        "output": output,
    }
    if any(path is None for path in required_paths.values()):
        raise ValueError("all development dataset paths are required")
    snapshot_path = Path(snapshot)  # type: ignore[arg-type]
    results_path = Path(results)  # type: ignore[arg-type]
    split_manifest_path = Path(split_manifest)  # type: ignore[arg-type]
    projection_identity_path = Path(projection_identity)  # type: ignore[arg-type]
    output_path = Path(output)  # type: ignore[arg-type]
    _assert_development_only_paths(
        (snapshot_path, results_path, split_manifest_path, projection_identity_path)
    )
    if (
        isinstance(epsilon, bool)
        or not isinstance(epsilon, (int, float))
        or float(epsilon) != contract.epsilon
    ):
        raise ValueError("epsilon must equal the frozen primary StudyContract")

    development_snapshot, snapshot_receipt = _verify_snapshot(
        snapshot_path, results=results_path
    )
    development_cases, identity_commitment, split_manifest_sha256 = (
        _load_development_cases(split_manifest_path, projection_identity_path)
    )
    case_by_id = {case.public_case.case_id: case for case in development_cases}
    site_assignments = assign_site_groups(
        tuple(case.public_case for case in development_cases), seed=contract.group_seed
    )
    site_assignment_by_ref = {
        assignment.site_ref: assignment for assignment in site_assignments
    }

    transaction_records: list[
        tuple[
            Mapping[str, Any],
            _DevelopmentCase,
            str,
            TrajectoryGroupAssignment,
            tuple[Mapping[str, Any], ...],
        ]
    ] = []
    for transaction in development_snapshot.transactions:
        raw = transaction["raw"]
        case_id = str(raw["case_id"])
        case = case_by_id.get(case_id)
        if case is None:
            raise ValueError("snapshot transaction is not a development case")
        trajectory_id = trajectory_id_from_resume_key(
            str(transaction["resume_identity_sha256"])
        )
        assignment = site_assignment_by_ref[case.public_case.site_ref]
        agent_turns = _agent_turns(transaction)
        parsed = transaction["parsed"]
        scores = transaction["scores"]
        if len(agent_turns) != len(parsed) or len(parsed) != len(scores):
            raise ValueError("transaction prefix censuses are not aligned")
        result = raw["result"]
        trajectory_assignment = TrajectoryGroupAssignment(
            trajectory_id=trajectory_id,
            group_id=assignment.group_id,
            partition=assignment.partition,
            site_ref=assignment.site_ref,
            case_id=case.public_case.case_id,
            condition=case.packet.condition,
            mutation_family=case.gold.mutation_family,
            repeat=int(raw["repeat"]),
            final_turn_count=len(parsed),
            final_tokens=int(result["total_tokens"]),
        )
        transaction_records.append(
            (transaction, case, trajectory_id, trajectory_assignment, agent_turns)
        )
    if len(transaction_records) != 450 or len(
        {record[2] for record in transaction_records}
    ) != 450:
        raise ValueError("snapshot must assign exactly 450 unique trajectories")

    train_records = tuple(
        record for record in transaction_records if record[3].partition == "train"
    )
    train_texts = tuple(
        str(turn.get("content") or "")
        for record in train_records
        for turn in record[4]
    )
    fitted = fit_text_distance(train_texts)

    runtime_rows: list[PrefixRuntimeFeature] = []
    private_labels: list[PrivatePrefixLabel] = []
    trajectory_assignments: list[TrajectoryGroupAssignment] = []
    partition_by_trajectory: dict[str, str] = {}
    for transaction, _case, trajectory_id, assignment, agent_turns in transaction_records:
        raw = transaction["raw"]
        result = raw["result"]
        parsed = transaction["parsed"]
        qualities = tuple(float(score["quality"]) for score in transaction["scores"])
        private_labels.extend(
            private_prefix_labels(trajectory_id, qualities, epsilon=float(epsilon))
        )
        for turn_index in range(1, len(parsed) + 1):
            runtime_rows.append(
                runtime_features(
                    {
                        "agent_count": result["agent_count"],
                        "parsed": parsed,
                        "pattern": raw["pattern"],
                        "pattern_category": result["pattern_category"],
                        "prefix_turn_index": turn_index,
                        "trajectory_id": trajectory_id,
                        "turns": agent_turns,
                    },
                    fitted=fitted,
                )
            )
        trajectory_assignments.append(assignment)
        partition_by_trajectory[trajectory_id] = assignment.partition

    runtime_rows.sort(key=lambda row: row.row_id)
    private_labels.sort(key=lambda row: row.row_id)
    trajectory_assignments.sort(key=lambda row: row.trajectory_id)
    runtime_ids = [row.row_id for row in runtime_rows]
    label_ids = [row.row_id for row in private_labels]
    if runtime_ids != label_ids or len(runtime_ids) != len(set(runtime_ids)):
        raise ValueError("runtime and private row-ID censuses are not one-to-one")

    runtime_path = output_path / "runtime" / "runtime_features.jsonl"
    private_label_path = output_path / "private" / "private_labels.jsonl"
    assignment_path = output_path / "private" / "group_assignments.json"
    manifest_path = output_path / "feature_manifest.json"
    usage_events_path = output_path / "usage" / "usage_events.jsonl"
    claim_availability_path = output_path / "usage" / "claim_availability.json"
    write_jsonl_atomic(runtime_path, runtime_rows)
    write_jsonl_atomic(private_label_path, private_labels)
    write_json_atomic(
        assignment_path,
        {
            "assignments": trajectory_assignments,
            "schema_version": GROUP_ASSIGNMENT_SCHEMA,
        },
    )
    usage_ledger = build_usage_ledger(
        development_snapshot.transactions,
        trajectory_ids={
            str(transaction["resume_identity_sha256"]): trajectory_id
            for transaction, _case, trajectory_id, _assignment, _agent_turns in transaction_records
        },
    )
    write_jsonl_atomic(usage_events_path, usage_ledger.events)
    usage_event_counts = Counter(
        f"{event.event_kind}.{event.attempt_status}" for event in usage_ledger.events
    )
    write_json_atomic(
        claim_availability_path,
        {
            **usage_ledger.availability.to_dict(),
            "event_counts": dict(sorted(usage_event_counts.items())),
            "usage_events_sha256": _sha256_file(usage_events_path),
        },
    )

    site_partition_counts = Counter(row.partition for row in site_assignments)
    trajectory_partition_counts = Counter(
        row.partition for row in trajectory_assignments
    )
    prefix_partition_counts = Counter(
        partition_by_trajectory[row.trajectory_id] for row in runtime_rows
    )
    artifacts = {
        "private/group_assignments.json": _artifact_entry(
            assignment_path,
            schema_version=GROUP_ASSIGNMENT_SCHEMA,
            record_count=len(trajectory_assignments),
        ),
        "private/private_labels.jsonl": _artifact_entry(
            private_label_path,
            schema_version=PRIVATE_LABEL_SCHEMA,
            record_count=len(private_labels),
        ),
        "runtime/runtime_features.jsonl": _artifact_entry(
            runtime_path,
            schema_version=RUNTIME_FEATURE_SCHEMA,
            record_count=len(runtime_rows),
        ),
    }
    snapshot_receipt_file_sha256 = _sha256_file(snapshot_path)
    study_contract_sha256 = sha256_json(asdict(contract))
    artifact_receipt = canonical_artifact_receipt(
        schema_version=DATASET_ARTIFACT_RECEIPT_SCHEMA,
        files={
            "private/group_assignments.json": assignment_path,
            "private/private_labels.jsonl": private_label_path,
            "runtime/runtime_features.jsonl": runtime_path,
        },
        row_census={
            "assignments": len(trajectory_assignments),
            "prefixes": len(runtime_rows),
            "private_labels": len(private_labels),
            "runtime_features": len(runtime_rows),
            "sites": len(site_assignments),
            "trajectories": len(trajectory_assignments),
        },
        bindings={
            "projection_identity_commitment": identity_commitment,
            "snapshot_receipt_sha256": snapshot_receipt_file_sha256,
            "split_manifest_sha256": split_manifest_sha256,
            "study_contract_sha256": study_contract_sha256,
            "transaction_set_sha256": development_snapshot.transaction_set_sha256,
            "vocabulary_sha256": fitted.vocabulary_sha256,
        },
    )
    manifest = DatasetManifest(
        schema_version=DATASET_MANIFEST_SCHEMA,
        snapshot_receipt_sha256=snapshot_receipt_file_sha256,
        transaction_set_sha256=development_snapshot.transaction_set_sha256,
        split_manifest_sha256=split_manifest_sha256,
        projection_identity_commitment=identity_commitment,
        study_contract_sha256=study_contract_sha256,
        epsilon=float(epsilon),
        trajectory_count=len(trajectory_assignments),
        prefix_count=len(runtime_rows),
        site_partition_counts=dict(sorted(site_partition_counts.items())),
        trajectory_partition_counts=dict(
            sorted(trajectory_partition_counts.items())
        ),
        prefix_partition_counts=dict(sorted(prefix_partition_counts.items())),
        runtime_schema=PrefixRuntimeFeature.field_names(),
        private_label_schema=PrivatePrefixLabel.field_names(),
        assignment_schema=TrajectoryGroupAssignment.field_names(),
        numeric_features=NUMERIC_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
        model_features=MODEL_FEATURES,
        transformer={
            "class": "TfidfVectorizer",
            "fit_partition": "train",
            "fit_prefix_count": len(train_texts),
            "fit_site_count": site_partition_counts["train"],
            "fit_trajectory_count": len(train_records),
            "parameters": {
                "lowercase": True,
                "min_df": 1,
                "ngram_range": [1, 2],
                "norm": "l2",
            },
            "vocabulary_sha256": fitted.vocabulary_sha256,
            "vocabulary_size": len(fitted.vocabulary),
        },
        access_policy={
            "allowed_split": "dev",
            "held_out_bundle_reads": 0,
            "resolved_bundle_keys": ["dev.challenged", "dev.native"],
        },
        artifact_receipt=artifact_receipt,
        artifacts=artifacts,
    )
    write_json_atomic(manifest_path, manifest)
    if snapshot_receipt.get("transaction_count") != manifest.trajectory_count:
        raise ValueError("snapshot and dataset trajectory censuses differ")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--projection-identity", type=Path, required=True)
    parser.add_argument("--epsilon", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build_dataset(
        snapshot=args.snapshot,
        results=args.results,
        split_manifest=args.split_manifest,
        projection_identity=args.projection_identity,
        epsilon=args.epsilon,
        output=args.output,
        method_lock=StudyContract.primary(),
    )
    print(f"dataset_manifest={args.output / 'feature_manifest.json'}")
    print(
        "site_partition_counts="
        + canonical_json(dict(manifest.site_partition_counts))
    )
    print(f"trajectory_count={manifest.trajectory_count}")
    print(
        "trajectory_partition_counts="
        + canonical_json(dict(manifest.trajectory_partition_counts))
    )
    print(f"prefix_count={manifest.prefix_count}")
    print(f"vocabulary_sha256={manifest.transformer['vocabulary_sha256']}")
    print("held_out_bundle_reads=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
