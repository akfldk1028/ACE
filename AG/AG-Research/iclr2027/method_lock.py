"""Fail-closed, source-bound method-lock candidate for ICLR 2027."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

from .io import canonical_json, sha256_json
from .pilot_gate import (
    _load_run_manifest,
    _load_summary,
    evaluate_pilot,
    transaction_set_receipt,
)
from .policy_replay import (
    EXPECTED_INPUT_SHA256,
    REPLAY_IMPLEMENTATION_FILES,
    safe_input_file,
)
from .secure_files import AuthenticatedTree, read_authenticated_file
from .study_contract import StudyContract


METHOD_LOCK_SCHEMA = "ace.iclr2027.method_lock_candidate.v1"
REAL_SCOPE = "real_development_method_lock"
SYNTHETIC_SCOPE = "synthetic_logic_only"
EXECUTION_MEMORY_CONTINUATION_SCHEMA = (
    "ace.iclr2027.execution_memory_continuation.v1"
)

EXPECTED_SOURCE_SHA256 = {
    "dataset_manifest": "7afe02f50c7b179c659b19042413d45d6940fa68444831359177e422262136a1",
    "design_receipt": "c86ce17e923d3a6988ed93d14c55f0ef7271b3a88eb94a44b88bf686ceee9da5",
    "development_gate": "e4f64639991b617955b4e2f2821a46205e0d7dd5f9b79aef4fd883b729c565b5",
    "model_registry": "c30e5abd4b82ac652ae684376251b8b0bd836f28ebe84e8c815180f16ab702d8",
    "pilot_gate": "d534eeb379e4fbe8793ff986fa2e583eca7b6783d561f968a606be0139b945a6",
    "snapshot_receipt": "63556ffe60f0cfbbc7f5bea4f2d75e4bbafa67566a3bd9a8f61d22ad298b5a4d",
}
EXPECTED_DESIGN_DOCUMENT = "2026-08-19-iclr2027-option-b-design.md"
EXPECTED_DESIGN_DOCUMENT_BYTES = 11_885
EXPECTED_DESIGN_DOCUMENT_SHA256 = (
    "95f54cbd8ec5ea0700d967b9128d568690fcb118eda588dff35917e007f532a1"
)
EXPECTED_EXECUTION_MEMORY_BASELINE_SHA256 = (
    "66166704b54d2e4b7f23e4107dcd0b254ee786c1218fd47a4e3bf91a4dd086e5"
)
EXPECTED_EXECUTION_MEMORY_NAME = "ICLR_2027_EXECUTION_MEMORY_2026-08-19.md"
EXPECTED_PILOT_FAILED_CHECKS = (
    "final_blocking_at_least_95pct",
    "final_decision_at_least_95pct",
    "final_verdict_at_least_95pct",
    "retry_rate_below_5pct",
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CANDIDATE_FIELDS = frozenset(
    {
        "access_audit",
        "blockers",
        "dataset",
        "dependency_receipts",
        "design_receipt",
        "development_gate",
        "execution_memory",
        "held_out_access_allowed",
        "implementation_closure",
        "models",
        "pilot_gate",
        "receipt_sha256",
        "replay",
        "schema_version",
        "scientific_identity",
        "scope",
        "source_files",
        "status",
        "study_contract",
        "usage_claims",
    }
)
_REAL_ADDITIONAL_IMPLEMENTATION_FILES = (
    "build_exp09_dataset.py",
    "freeze_iclr2027_development.py",
    "freeze_iclr2027_method.py",
    "iclr2027/method_lock.py",
    "iclr2027/secure_files.py",
    "train_exp09_cats.py",
)


@dataclass(frozen=True)
class MethodLockAuthorization:
    """Result of a positive logical lock check, without opening any case data."""

    logical_method_lock_positive: bool
    real_data_access: bool
    scope: str


@dataclass(frozen=True)
class _SourcePaths:
    design_receipt: Path
    design_document: Path
    snapshot: Path
    pilot_gate: Path
    dataset: Path
    models: Path
    replay: Path
    project_root: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(
        read_authenticated_file(path, label=f"SHA-256 input {path.name}")
    ).hexdigest()


def _require_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _read_json(path: Path, *, label: str, canonical: bool) -> dict[str, Any]:
    artifact = read_authenticated_file(path, label=label)
    try:
        value = json.loads(artifact.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    if canonical and artifact != (canonical_json(value) + "\n").encode("utf-8"):
        raise ValueError(f"{label} is not canonical JSON")
    return value


def _expected_real_paths() -> dict[str, Path]:
    project = _expected_implementation_root()
    workspace = project.parents[1]
    return {
        "design_receipt": workspace
        / "docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.receipt.json",
        "snapshot": project
        / "results/exp09_cats/development_snapshot/snapshot_receipt.json",
        "pilot_gate": project
        / "results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json",
        "dataset": project / "results/exp09_cats/dataset/feature_manifest.json",
        "models": project / "results/exp09_cats/models/model_registry.json",
        "replay": project
        / "results/exp09_cats/replay/development/development_gate.json",
    }


def _expected_implementation_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _decode_json_object(artifact: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(artifact.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _same_lexical_path(left: str | Path, right: str | Path) -> bool:
    return os.path.normcase(os.path.abspath(os.fspath(left))) == os.path.normcase(
        os.path.abspath(os.fspath(right))
    )


def _materialize_authenticated_file(
    tree: AuthenticatedTree,
    relative: str | Path,
    destination_root: Path,
    *,
    label: str,
    expected_sha256: str | None = None,
) -> bytes:
    artifact = tree.read_bytes(relative, label=label)
    if expected_sha256 is not None and hashlib.sha256(artifact).hexdigest() != expected_sha256:
        raise ValueError(f"{label} SHA-256 mismatch")
    destination = destination_root / Path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(artifact)
    return artifact


@contextmanager
def _prepare_source_paths(
    *,
    design_receipt: str | Path,
    snapshot: str | Path,
    pilot_gate: str | Path,
    dataset: str | Path,
    models: str | Path,
    replay: str | Path,
) -> Any:
    supplied = {
        "design_receipt": Path(design_receipt),
        "snapshot": Path(snapshot),
        "pilot_gate": Path(pilot_gate),
        "dataset": Path(dataset),
        "models": Path(models),
        "replay": Path(replay),
    }
    expected = _expected_real_paths()
    resolved: dict[str, Path] = {}
    for name, raw_path in supplied.items():
        if not _same_lexical_path(raw_path, expected[name]):
            raise ValueError(f"{name.replace('_', ' ')} is not the frozen source path")
        resolved[name] = expected[name]

    real_project = _expected_implementation_root()
    with tempfile.TemporaryDirectory(prefix="ace-method-lock-authenticated-") as temporary:
        snapshot_root = Path(temporary)
        project = snapshot_root / "project"
        workspace = snapshot_root / "workspace"
        design_destination = workspace / "docs/superpowers/specs"
        snapshot_destination = project / "results/exp09_cats/development_snapshot"
        pilot_destination = (
            project / "results/exp08_architecture/pilot_full_v12_clean_recovery"
        )
        dataset_destination = project / "results/exp09_cats/dataset"
        model_destination = project / "results/exp09_cats/models"
        replay_destination = project / "results/exp09_cats/replay/development"

        with ExitStack() as stack:
            design_tree = stack.enter_context(
                AuthenticatedTree(
                    resolved["design_receipt"].parent,
                    label="design source root",
                )
            )
            snapshot_tree = stack.enter_context(
                AuthenticatedTree(resolved["snapshot"].parent, label="snapshot root")
            )
            pilot_tree = stack.enter_context(
                AuthenticatedTree(
                    resolved["pilot_gate"].parent,
                    label="development transaction root",
                )
            )
            dataset_tree = stack.enter_context(
                AuthenticatedTree(resolved["dataset"].parent, label="dataset root")
            )
            model_tree = stack.enter_context(
                AuthenticatedTree(resolved["models"].parent, label="model root")
            )
            replay_tree = stack.enter_context(
                AuthenticatedTree(resolved["replay"].parent, label="replay root")
            )
            implementation_tree = stack.enter_context(
                AuthenticatedTree(real_project, label="implementation root")
            )

            design_bytes = _materialize_authenticated_file(
                design_tree,
                resolved["design_receipt"].name,
                design_destination,
                label="design receipt",
                expected_sha256=EXPECTED_SOURCE_SHA256["design_receipt"],
            )
            design_payload = _decode_json_object(design_bytes, label="design receipt")
            document_name = design_payload.get("document")
            if document_name != EXPECTED_DESIGN_DOCUMENT:
                raise ValueError("design receipt document filename mismatch")
            _materialize_authenticated_file(
                design_tree,
                document_name,
                design_destination,
                label="design document",
                expected_sha256=EXPECTED_DESIGN_DOCUMENT_SHA256,
            )

            snapshot_bytes = _materialize_authenticated_file(
                snapshot_tree,
                resolved["snapshot"].name,
                snapshot_destination,
                label="development snapshot receipt",
                expected_sha256=EXPECTED_SOURCE_SHA256["snapshot_receipt"],
            )
            snapshot_payload = _decode_json_object(
                snapshot_bytes, label="development snapshot receipt"
            )
            source_receipt = snapshot_payload.get("source_artifact_receipt")
            source_files = (
                source_receipt.get("files")
                if isinstance(source_receipt, Mapping)
                else None
            )
            if not isinstance(source_files, Mapping):
                raise ValueError("development snapshot source file receipt is missing")
            fixed_pilot_files = {"pilot_gate.json", "run_manifest.json", "run_plan.json"}
            transaction_files = set(source_files) - fixed_pilot_files
            if (
                len(source_files) != 453
                or len(transaction_files) != 450
                or any(
                    re.fullmatch(r"run_transactions/[0-9a-f]{64}\.json", str(name))
                    is None
                    for name in transaction_files
                )
                or any(
                    not isinstance(digest, str) or _SHA256.fullmatch(digest) is None
                    for digest in source_files.values()
                )
            ):
                raise ValueError("development snapshot source file set is invalid")
            for name, digest in sorted(source_files.items()):
                _materialize_authenticated_file(
                    pilot_tree,
                    str(name),
                    pilot_destination,
                    label=f"development source {name}",
                    expected_sha256=str(digest),
                )
            _materialize_authenticated_file(
                pilot_tree,
                "pilot_summary.json",
                pilot_destination,
                label="pilot summary",
            )

            dataset_bytes = _materialize_authenticated_file(
                dataset_tree,
                resolved["dataset"].name,
                dataset_destination,
                label="dataset manifest",
                expected_sha256=EXPECTED_SOURCE_SHA256["dataset_manifest"],
            )
            dataset_payload = _decode_json_object(dataset_bytes, label="dataset manifest")
            artifact_receipt = dataset_payload.get("artifact_receipt")
            dataset_files = (
                artifact_receipt.get("files")
                if isinstance(artifact_receipt, Mapping)
                else None
            )
            expected_dataset_files = {
                "private/group_assignments.json",
                "private/private_labels.jsonl",
                "runtime/runtime_features.jsonl",
            }
            if not isinstance(dataset_files, Mapping) or set(dataset_files) != expected_dataset_files:
                raise ValueError("dataset artifact file set mismatch")
            for name, digest in sorted(dataset_files.items()):
                _materialize_authenticated_file(
                    dataset_tree,
                    str(name),
                    dataset_destination,
                    label=f"dataset source {name}",
                    expected_sha256=str(digest),
                )
            for name, digest_key in (
                ("usage/claim_availability.json", "claim_availability.json"),
                ("usage/usage_events.jsonl", "usage_events.jsonl"),
            ):
                _materialize_authenticated_file(
                    dataset_tree,
                    name,
                    dataset_destination,
                    label=f"dataset source {name}",
                    expected_sha256=EXPECTED_INPUT_SHA256[digest_key],
                )

            registry_bytes = _materialize_authenticated_file(
                model_tree,
                resolved["models"].name,
                model_destination,
                label="model registry",
                expected_sha256=EXPECTED_SOURCE_SHA256["model_registry"],
            )
            registry = _decode_json_object(registry_bytes, label="model registry")
            variants = registry.get("variants")
            expected_variant_names = {
                "cats-primary",
                "cats-logistic",
                "cats-epsilon-0p01",
                "cats-epsilon-0p05",
                "cats-alpha-0p05",
                "cats-alpha-0p20",
            }
            if (
                not isinstance(variants, Sequence)
                or isinstance(variants, (str, bytes))
                or len(variants) != 6
                or {
                    str(variant.get("name"))
                    for variant in variants
                    if isinstance(variant, Mapping)
                }
                != expected_variant_names
                or any(
                    not isinstance(variant, Mapping)
                    or variant.get("path") != variant.get("name")
                    for variant in variants
                )
            ):
                raise ValueError("model registry variant paths mismatch")
            _materialize_authenticated_file(
                model_tree,
                "registry.json",
                model_destination,
                label="model registry alias",
                expected_sha256=EXPECTED_SOURCE_SHA256["model_registry"],
            )
            _materialize_authenticated_file(
                model_tree,
                "semantic_determinism.json",
                model_destination,
                label="semantic determinism receipt",
                expected_sha256=EXPECTED_INPUT_SHA256["semantic_determinism.json"],
            )
            model_hash_keys = {
                "classifier.joblib": "classifier_sha256",
                "manifest.json": "manifest_sha256",
                "predictions.jsonl": "predictions_sha256",
                "transformer.joblib": "transformer_sha256",
            }
            for variant in variants:
                assert isinstance(variant, Mapping)
                variant_path = str(variant["path"])
                for filename, digest_key in model_hash_keys.items():
                    digest = variant.get(digest_key)
                    _require_sha256(digest, label=f"model {variant_path} {filename}")
                    _materialize_authenticated_file(
                        model_tree,
                        f"{variant_path}/{filename}",
                        model_destination,
                        label=f"model artifact {variant_path}/{filename}",
                        expected_sha256=str(digest),
                    )

            gate_bytes = _materialize_authenticated_file(
                replay_tree,
                resolved["replay"].name,
                replay_destination,
                label="development gate",
                expected_sha256=EXPECTED_SOURCE_SHA256["development_gate"],
            )
            gate_payload = _decode_json_object(gate_bytes, label="development gate")
            rows_digest = _require_sha256(
                gate_payload.get("replay_rows_sha256"), label="replay rows hash"
            )
            _materialize_authenticated_file(
                replay_tree,
                "replay_rows.jsonl",
                replay_destination,
                label="replay rows",
                expected_sha256=rows_digest,
            )

            implementation_files = set(REPLAY_IMPLEMENTATION_FILES) | set(
                _REAL_ADDITIONAL_IMPLEMENTATION_FILES
            )
            for name in sorted(implementation_files):
                _materialize_authenticated_file(
                    implementation_tree,
                    name,
                    project,
                    label=f"implementation {name}",
                )

            paths = _SourcePaths(
                design_receipt=design_destination / resolved["design_receipt"].name,
                design_document=design_destination / EXPECTED_DESIGN_DOCUMENT,
                snapshot=snapshot_destination / resolved["snapshot"].name,
                pilot_gate=pilot_destination / resolved["pilot_gate"].name,
                dataset=dataset_destination / resolved["dataset"].name,
                models=model_destination / resolved["models"].name,
                replay=replay_destination / resolved["replay"].name,
                project_root=project,
            )
            observed = _observed_top_source_hashes(paths)
            for name, expected_hash in EXPECTED_SOURCE_SHA256.items():
                if observed[name] != expected_hash:
                    raise ValueError(f"{name.replace('_', ' ')} SHA-256 mismatch")
            yield paths


def _observed_top_source_hashes(paths: _SourcePaths) -> dict[str, str]:
    return {
        "dataset_manifest": _sha256_file(paths.dataset),
        "design_document": _sha256_file(paths.design_document),
        "design_receipt": _sha256_file(paths.design_receipt),
        "development_gate": _sha256_file(paths.replay),
        "model_registry": _sha256_file(paths.models),
        "pilot_gate": _sha256_file(paths.pilot_gate),
        "snapshot_receipt": _sha256_file(paths.snapshot),
    }


def _validate_design_receipt(paths: _SourcePaths) -> dict[str, Any]:
    receipt = _read_json(paths.design_receipt, label="design receipt", canonical=False)
    expected_fields = {
        "document",
        "document_bytes",
        "document_sha256",
        "effective_date",
        "schema_version",
        "status",
        "timing_disclosure",
    }
    if set(receipt) != expected_fields:
        raise ValueError("design receipt fields mismatch")
    if (
        receipt["schema_version"] != "ace.iclr2027.design_receipt.v1"
        or receipt["status"] != "approved_prospective_amendment"
        or receipt["effective_date"] != "2026-08-19"
        or receipt["document"] != EXPECTED_DESIGN_DOCUMENT
        or receipt["document_bytes"] != EXPECTED_DESIGN_DOCUMENT_BYTES
        or receipt["document_sha256"] != EXPECTED_DESIGN_DOCUMENT_SHA256
        or not isinstance(receipt["timing_disclosure"], str)
        or not receipt["timing_disclosure"]
    ):
        raise ValueError("design receipt prospective-amendment binding mismatch")
    document_bytes = read_authenticated_file(paths.design_document, label="design document")
    if (
        len(document_bytes) != receipt["document_bytes"]
        or hashlib.sha256(document_bytes).hexdigest() != receipt["document_sha256"]
    ):
        raise ValueError("design document bytes mismatch")
    return {
        **receipt,
        "receipt_file_sha256": _sha256_file(paths.design_receipt),
    }


def _validate_pilot_gate(paths: _SourcePaths) -> dict[str, Any]:
    root = paths.pilot_gate.parent
    for filename in ("pilot_summary.json", "run_manifest.json"):
        safe_input_file(root / filename, label=f"pilot source {filename}")
    if not (root / "run_transactions").is_dir():
        raise ValueError("pilot transaction directory is missing from authenticated snapshot")
    transaction_hash, transaction_count = transaction_set_receipt(root)
    recomputed = evaluate_pilot(
        _load_summary(root),
        run_manifest=_load_run_manifest(root),
        observed_transaction_set_sha256=transaction_hash,
        observed_transaction_count=transaction_count,
    ).to_dict()
    persisted = _read_json(paths.pilot_gate, label="pilot gate", canonical=True)
    if persisted != recomputed:
        raise ValueError("pilot gate differs from source recomputation")
    checks = persisted.get("checks")
    if not isinstance(checks, Mapping) or any(type(value) is not bool for value in checks.values()):
        raise ValueError("pilot gate check schema mismatch")
    failures = tuple(sorted(name for name, value in checks.items() if not value))
    if persisted.get("passed") is not all(checks.values()):
        raise ValueError("pilot gate pass state is inconsistent")
    if failures != EXPECTED_PILOT_FAILED_CHECKS:
        raise ValueError("pilot gate failed-check set mismatch")
    return persisted


def _development_failures(gate: Mapping[str, Any]) -> list[str]:
    checks = gate.get("checks")
    if not isinstance(checks, Mapping):
        raise ValueError("development gate checks are missing")
    failed: list[str] = []
    for name, raw_check in checks.items():
        if not isinstance(name, str) or not isinstance(raw_check, Mapping):
            raise ValueError("development gate check schema mismatch")
        passed = raw_check.get("passed")
        if type(passed) is not bool:
            raise ValueError("development gate check pass value is invalid")
        if not passed:
            failed.append(name)
    failures = sorted(failed)
    if gate.get("failures") != failures or gate.get("passed") is not (not failures):
        raise ValueError("development gate pass state is inconsistent")
    return failures


def _pilot_summary(gate: Mapping[str, Any], *, file_sha256: str) -> dict[str, Any]:
    checks = gate.get("checks")
    if not isinstance(checks, Mapping) or any(type(value) is not bool for value in checks.values()):
        raise ValueError("pilot gate check schema mismatch")
    failures = sorted(name for name, value in checks.items() if not value)
    passed = gate.get("passed")
    if type(passed) is not bool or passed is not all(checks.values()):
        raise ValueError("pilot gate pass state is inconsistent")
    return {
        "checks": dict(checks),
        "failed_checks": failures,
        "file_sha256": _require_sha256(file_sha256, label="pilot gate file hash"),
        "metrics": {
            key: value for key, value in gate.items() if key not in {"checks", "passed"}
        },
        "passed": passed,
    }


def _development_summary(
    gate: Mapping[str, Any], *, file_sha256: str
) -> dict[str, Any]:
    failures = _development_failures(gate)
    return {
        "checks": dict(gate["checks"]),
        "failed_checks": failures,
        "file_sha256": _require_sha256(
            file_sha256, label="development gate file hash"
        ),
        "passed": gate["passed"],
        "receipt_sha256": _require_sha256(
            gate.get("receipt_sha256"), label="development gate receipt hash"
        ),
    }


def _real_execution_memory_binding() -> dict[str, str]:
    return {
        "baseline_sha256": EXPECTED_EXECUTION_MEMORY_BASELINE_SHA256,
        "continuation_schema": EXECUTION_MEMORY_CONTINUATION_SCHEMA,
        "path": EXPECTED_EXECUTION_MEMORY_NAME,
    }


def _implementation_closure(
    gate: Mapping[str, Any], *, project_root: Path
) -> dict[str, str]:
    replay_implementation = gate.get("replay_implementation")
    if not isinstance(replay_implementation, Mapping):
        raise ValueError("replay implementation closure is missing")
    closure = {
        str(name): _require_sha256(digest, label="replay implementation hash")
        for name, digest in replay_implementation.items()
    }
    for name in _REAL_ADDITIONAL_IMPLEMENTATION_FILES:
        path = safe_input_file(project_root / name, label=f"implementation {name}")
        closure[name] = _sha256_file(path)
    return dict(sorted(closure.items()))


def _model_summary(
    *, registry: Mapping[str, Any], gate: Mapping[str, Any], model_root: Path
) -> dict[str, Any]:
    variants = registry.get("variants")
    if not isinstance(variants, Sequence) or isinstance(variants, (str, bytes)):
        raise ValueError("model registry variants are invalid")
    semantic_path = safe_input_file(
        model_root / "semantic_determinism.json",
        label="model semantic determinism receipt",
    )
    semantic = _read_json(
        semantic_path, label="model semantic determinism receipt", canonical=True
    )
    semantic_variants = semantic.get("variants")
    if not isinstance(semantic_variants, Sequence) or len(semantic_variants) != 6:
        raise ValueError("model semantic variant census mismatch")
    comparisons = [
        value
        for variant in semantic_variants
        for value in (
            variant.get("matching", {}).values()
            if isinstance(variant, Mapping)
            and isinstance(variant.get("matching"), Mapping)
            else ()
        )
    ]
    if len(comparisons) != 48 or any(value is not True for value in comparisons):
        raise ValueError("model semantic determinism comparison mismatch")
    source_hashes = gate.get("source_hashes")
    if not isinstance(source_hashes, Mapping):
        raise ValueError("development gate source hashes are missing")
    artifact_count = sum(
        name.startswith("models/")
        and name.count("/") == 2
        and name.rsplit("/", 1)[1]
        in {"classifier.joblib", "manifest.json", "predictions.jsonl", "transformer.joblib"}
        for name in source_hashes
    )
    if registry.get("variant_count") != 6 or len(variants) != 6 or artifact_count != 24:
        raise ValueError("model variant/artifact census mismatch")
    compact_variants = [
        {
            key: variant[key]
            for key in (
                "alpha",
                "classifier_sha256",
                "epsilon",
                "family",
                "manifest_sha256",
                "name",
                "predictions_sha256",
                "q_alpha",
                "semantic_sha256",
                "transformer_sha256",
            )
        }
        for variant in variants
    ]
    return {
        "artifact_count": artifact_count,
        "semantic_comparisons_passed": sum(value is True for value in comparisons),
        "semantic_comparisons_total": len(comparisons),
        "semantic_determinism_file_sha256": _sha256_file(semantic_path),
        "variant_count": len(variants),
        "variants": compact_variants,
    }


def _dataset_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    receipt = manifest.get("artifact_receipt")
    transformer = manifest.get("transformer")
    if not isinstance(receipt, Mapping) or not isinstance(transformer, Mapping):
        raise ValueError("dataset receipt/transformer binding is missing")
    files = receipt.get("files")
    if not isinstance(files, Mapping) or len(files) != 3:
        raise ValueError("dataset artifact file census mismatch")
    return {
        "artifact_files": len(files),
        "prefix_partition_counts": manifest["prefix_partition_counts"],
        "row_census": receipt["row_census"],
        "site_partition_counts": manifest["site_partition_counts"],
        "trajectory_partition_counts": manifest["trajectory_partition_counts"],
        "vocabulary_sha256": transformer["vocabulary_sha256"],
        "vocabulary_size": transformer["vocabulary_size"],
    }


def _usage_claims(dataset_root: Path, gate: Mapping[str, Any]) -> dict[str, Any]:
    claim_path = safe_input_file(
        dataset_root / "usage/claim_availability.json",
        label="usage claim availability",
    )
    claim = _read_json(claim_path, label="usage claim availability", canonical=True)
    gate_claims = gate.get("usage_claims")
    if not isinstance(gate_claims, Mapping):
        raise ValueError("development gate usage claims are missing")
    for key in (
        "invoice_grade_cost",
        "reasons",
        "total_compute",
        "visible_agent_token_boundary",
        "visible_agent_tokens",
    ):
        if claim.get(key) != gate_claims.get(key):
            raise ValueError("usage claim binding mismatch")
    return {
        **dict(gate_claims),
        "event_counts": claim.get("event_counts"),
        "usage_events_sha256": claim.get("usage_events_sha256"),
    }


def _critical_replay_module_paths() -> dict[str, str]:
    modules: dict[str, str] = {"config": "config.py"}
    for relative in REPLAY_IMPLEMENTATION_FILES:
        path = Path(relative)
        if not relative.startswith("iclr2027/") or path.suffix != ".py":
            continue
        module = "iclr2027" if path.name == "__init__.py" else ".".join(path.with_suffix("").parts)
        modules[module] = relative
    return dict(sorted(modules.items()))


def _canonical_ordered_paths(
    values: Sequence[str | Path], *, strict: bool
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        resolved = Path(raw).resolve(strict=strict)
        if not resolved.is_absolute():
            raise ValueError("trusted import path must be absolute")
        text = os.path.normpath(str(resolved))
        key = os.path.normcase(text)
        if key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _trusted_replay_dependency_paths() -> list[str]:
    roots: list[Path] = []
    for name in ("joblib", "numpy", "pandas", "scipy", "sklearn", "threadpoolctl"):
        module = importlib.import_module(name)
        origin_value = getattr(module, "__file__", None)
        if not isinstance(origin_value, str):
            raise ValueError(f"trusted replay dependency {name} has no file origin")
        origin = Path(origin_value).resolve(strict=True)
        site_root = next(
            (
                parent
                for parent in origin.parents
                if parent.name in {"site-packages", "dist-packages"}
            ),
            origin.parent,
        )
        roots.append(site_root)
    ordered = sorted(roots, key=lambda value: os.path.normcase(str(value)))
    return _canonical_ordered_paths(ordered, strict=True)


def _verify_replay_from_authenticated_snapshot(paths: _SourcePaths) -> dict[str, Any]:
    """Run the unchanged Task 6 verifier inside the authenticated source mirror."""

    script = """
import importlib
import json
import os
from pathlib import Path
import sys

def canonical_ordered_paths(values, *, strict):
    result = []
    seen = set()
    for raw in values:
        resolved = Path(raw).resolve(strict=strict)
        if not resolved.is_absolute():
            raise RuntimeError("trusted import path must be absolute")
        text = os.path.normpath(str(resolved))
        key = os.path.normcase(text)
        if key not in seen:
            seen.add(key)
            result.append(text)
    return result

isolated_runtime_roots = canonical_ordered_paths(sys.path, strict=False)
project_root = canonical_ordered_paths([sys.argv[1]], strict=True)[0]
dependency_paths = canonical_ordered_paths(json.loads(sys.argv[6]), strict=True)
critical_modules = json.loads(sys.argv[7])
if not isinstance(critical_modules, dict) or critical_modules.get("config") != "config.py":
    raise RuntimeError("authenticated replay config module is missing")
allowed_sys_path = canonical_ordered_paths(
    [project_root, *isolated_runtime_roots, *dependency_paths], strict=False
)
sys.path[:] = allowed_sys_path
sys.dont_write_bytecode = True

config_module = importlib.import_module("config")
config_origin = getattr(config_module, "__file__", None)
if not isinstance(config_origin, str):
    raise RuntimeError("critical module has no file origin: config")
module_origins = {"config": str(Path(config_origin).resolve(strict=True))}
import_sequence = ["config"]
sys.path[:] = allowed_sys_path
if sys.path != allowed_sys_path:
    raise RuntimeError("authenticated replay sys.path normalization failed")
after_config_normalization = list(sys.path)

for module_name in critical_modules:
    if module_name == "config":
        continue
    module = importlib.import_module(module_name)
    origin = getattr(module, "__file__", None)
    if not isinstance(origin, str):
        raise RuntimeError(f"critical module has no file origin: {module_name}")
    module_origins[module_name] = str(Path(origin).resolve(strict=True))
    import_sequence.append(module_name)
if sys.path != allowed_sys_path:
    raise RuntimeError("authenticated replay sys.path changed before replay")
before_replay = list(sys.path)
canonical_json = sys.modules["iclr2027.io"].canonical_json
verify_replay_outputs = sys.modules["iclr2027.policy_replay"].verify_replay_outputs
gate = verify_replay_outputs(
    sys.argv[2],
    snapshot=sys.argv[3],
    dataset=sys.argv[4],
    models=sys.argv[5],
)
if sys.path != allowed_sys_path:
    raise RuntimeError("authenticated replay sys.path changed after replay")
after_replay = list(sys.path)
sys.stdout.write(canonical_json({
    "gate": gate,
    "import_sequence": import_sequence,
    "module_origins": module_origins,
    "sys_path_attestation": {
        "after_config_normalization": after_config_normalization,
        "after_replay": after_replay,
        "allowed": allowed_sys_path,
        "before_replay": before_replay,
        "isolated_runtime_roots": isolated_runtime_roots,
    },
}))
"""
    critical_modules = _critical_replay_module_paths()
    dependency_paths = _trusted_replay_dependency_paths()
    environment = {
        key: os.environ[key]
        for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "TMPDIR")
        if key in os.environ
    }
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            script,
            str(paths.project_root),
            str(paths.replay.parent),
            str(paths.snapshot),
            str(paths.dataset.parent),
            str(paths.models.parent),
            canonical_json(dependency_paths),
            canonical_json(critical_modules),
        ],
        cwd=paths.project_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        suffix = detail[-1] if detail else "unknown verifier error"
        raise ValueError(f"authenticated Task 6 reconstruction failed: {suffix}")
    attestation = _decode_json_object(
        completed.stdout.encode("utf-8"), label="verified reconstruction"
    )
    if set(attestation) != {
        "gate",
        "import_sequence",
        "module_origins",
        "sys_path_attestation",
    }:
        raise ValueError("authenticated Task 6 attestation fields mismatch")
    gate = attestation["gate"]
    import_sequence = attestation["import_sequence"]
    origins = attestation["module_origins"]
    path_attestation = attestation["sys_path_attestation"]
    if (
        not isinstance(gate, Mapping)
        or not isinstance(import_sequence, list)
        or not isinstance(origins, Mapping)
        or not isinstance(path_attestation, Mapping)
    ):
        raise ValueError("authenticated Task 6 attestation schema mismatch")
    if import_sequence != list(critical_modules):
        raise ValueError("authenticated Task 6 import sequence mismatch")
    if set(origins) != set(critical_modules):
        raise ValueError("authenticated Task 6 module-origin census mismatch")
    for module, relative in critical_modules.items():
        expected = paths.project_root / relative
        observed = origins[module]
        if not isinstance(observed, str) or not _same_lexical_path(observed, expected):
            raise ValueError(f"authenticated Task 6 module origin mismatch: {module}")
    if set(path_attestation) != {
        "after_config_normalization",
        "after_replay",
        "allowed",
        "before_replay",
        "isolated_runtime_roots",
    }:
        raise ValueError("authenticated Task 6 sys.path attestation fields mismatch")
    runtime_roots = path_attestation["isolated_runtime_roots"]
    if not isinstance(runtime_roots, list) or not runtime_roots:
        raise ValueError("authenticated Task 6 runtime-root attestation mismatch")
    if any(not isinstance(value, str) for value in runtime_roots):
        raise ValueError("authenticated Task 6 runtime-root attestation mismatch")
    canonical_runtime = _canonical_ordered_paths(runtime_roots, strict=False)
    if canonical_runtime != runtime_roots:
        raise ValueError("authenticated Task 6 runtime-root attestation mismatch")
    expected_allowed = _canonical_ordered_paths(
        [paths.project_root, *canonical_runtime, *dependency_paths], strict=False
    )
    if path_attestation["allowed"] != expected_allowed:
        raise ValueError("authenticated Task 6 sys.path allowlist mismatch")
    for checkpoint in (
        "after_config_normalization",
        "before_replay",
        "after_replay",
    ):
        if path_attestation[checkpoint] != expected_allowed:
            raise ValueError(f"authenticated Task 6 sys.path {checkpoint} mismatch")
    persisted_gate = read_authenticated_file(paths.replay, label="persisted development gate")
    reconstructed_gate = (canonical_json(gate) + "\n").encode("utf-8")
    if reconstructed_gate != persisted_gate:
        raise ValueError("persisted development gate differs from child reconstruction")
    return dict(gate)


def _source_closure(paths: _SourcePaths) -> dict[str, object]:
    design = _validate_design_receipt(paths)
    pilot = _validate_pilot_gate(paths)
    verified_gate = _verify_replay_from_authenticated_snapshot(paths)
    snapshot = _read_json(paths.snapshot, label="snapshot receipt", canonical=True)
    dataset = _read_json(paths.dataset, label="dataset manifest", canonical=True)
    registry = _read_json(paths.models, label="model registry", canonical=True)
    project = paths.project_root
    source_hashes = verified_gate.get("source_hashes")
    source_receipts = verified_gate.get("source_receipts")
    if not isinstance(source_hashes, Mapping) or not isinstance(source_receipts, Mapping):
        raise ValueError("development gate dependency closure is missing")
    access_audit = verified_gate.get("access_audit")
    if not isinstance(access_audit, Mapping) or dict(access_audit) != {
        "authorized_partition": "development_gate",
        "held_out_bundle_reads": 0,
        "llm_calls": 0,
        "model_refits": 0,
        "transformer_refits": 0,
    }:
        raise ValueError("development access audit mismatch")
    replay_summary = {
        "bootstrap": verified_gate["bootstrap"],
        "lexical_collision": verified_gate["policy_contrasts"][
            "lexical_du_vs_max_cap"
        ],
        "policy_parameters": verified_gate["policy_parameters"],
        "policy_registry": verified_gate["policy_registry"],
        "receipt_sha256": verified_gate["receipt_sha256"],
        "replay_rows_sha256": verified_gate["replay_rows_sha256"],
        "row_census": verified_gate["row_census"],
        "source_hashes": dict(source_hashes),
        "state_conformal": verified_gate["state_conformal_derivation"],
    }
    return {
        "scope": REAL_SCOPE,
        "design_receipt": design,
        "scientific_identity": {
            "code_runtime_identity": snapshot["code_runtime_identity"],
            "run_plan_sha256": snapshot["run_plan_sha256"],
            "transaction_set_sha256": snapshot["transaction_set_sha256"],
        },
        "study_contract": asdict(StudyContract.primary()),
        "source_files": _observed_top_source_hashes(paths),
        "dependency_receipts": dict(source_receipts),
        "dataset": _dataset_summary(dataset),
        "models": _model_summary(
            registry=registry, gate=verified_gate, model_root=paths.models.parent
        ),
        "replay": replay_summary,
        "implementation_closure": _implementation_closure(
            verified_gate, project_root=project
        ),
        "execution_memory": _real_execution_memory_binding(),
        "usage_claims": _usage_claims(paths.dataset.parent, verified_gate),
        "access_audit": {
            "commits": 0,
            "held_out_bundle_reads": 0,
            "llm_calls": 0,
            "model_refits": 0,
            "transformer_refits": 0,
        },
        "_pilot_gate": pilot,
        "_development_gate": verified_gate,
    }


def build_method_lock(
    closure: Mapping[str, object],
    *,
    pilot_gate: Mapping[str, Any],
    development_gate: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic candidate; this function does not authenticate it."""

    if not isinstance(closure, Mapping):
        raise ValueError("method-lock closure must be a mapping")
    required = _CANDIDATE_FIELDS - {
        "blockers",
        "development_gate",
        "held_out_access_allowed",
        "pilot_gate",
        "receipt_sha256",
        "schema_version",
        "status",
    }
    if set(closure) != required:
        raise ValueError("method-lock closure fields mismatch")
    source_files = closure.get("source_files")
    if not isinstance(source_files, Mapping):
        raise ValueError("source file closure is missing")
    pilot_hash = source_files.get("pilot_gate")
    development_hash = source_files.get("development_gate")
    pilot_summary = _pilot_summary(pilot_gate, file_sha256=pilot_hash)
    development_summary = _development_summary(
        development_gate, file_sha256=development_hash
    )
    blockers = sorted(
        name
        for name, passed in (
            ("pilot_gate_failed", pilot_summary["passed"]),
            ("development_gate_failed", development_summary["passed"]),
        )
        if not passed
    )
    logical_positive = not blockers
    held_out_access_allowed = logical_positive and closure["scope"] == REAL_SCOPE
    payload = {
        "schema_version": METHOD_LOCK_SCHEMA,
        **{key: closure[key] for key in sorted(required)},
        "pilot_gate": pilot_summary,
        "development_gate": development_summary,
        "blockers": blockers,
        "held_out_access_allowed": held_out_access_allowed,
        "status": (
            "positive"
            if held_out_access_allowed
            else "logical_positive"
            if logical_positive
            else "blocked"
        ),
    }
    candidate = {**payload, "receipt_sha256": sha256_json(payload)}
    _validate_candidate(candidate)
    return candidate


def build_method_lock_from_sources(
    *,
    design_receipt: str | Path,
    snapshot: str | Path,
    pilot_gate: str | Path,
    dataset: str | Path,
    models: str | Path,
    replay: str | Path,
) -> dict[str, Any]:
    """Recompute every declared development dependency and build the candidate."""

    with _prepare_source_paths(
        design_receipt=design_receipt,
        snapshot=snapshot,
        pilot_gate=pilot_gate,
        dataset=dataset,
        models=models,
        replay=replay,
    ) as paths:
        closure = _source_closure(paths)
        pilot = closure.pop("_pilot_gate")
        development = closure.pop("_development_gate")
        assert isinstance(pilot, Mapping)
        assert isinstance(development, Mapping)
        return build_method_lock(
            closure,
            pilot_gate=pilot,
            development_gate=development,
        )


def candidate_file_bytes(candidate: Mapping[str, Any]) -> bytes:
    """Return the sole canonical on-disk encoding for a candidate."""

    _validate_candidate(candidate)
    return (canonical_json(candidate) + "\n").encode("utf-8")


def _validate_gate_summary(
    summary: object, *, development: bool
) -> tuple[bool, list[str]]:
    expected = {"checks", "failed_checks", "file_sha256", "passed"}
    expected.add("receipt_sha256" if development else "metrics")
    if not isinstance(summary, Mapping) or set(summary) != expected:
        raise ValueError("candidate gate summary fields mismatch")
    checks = summary["checks"]
    if not isinstance(checks, Mapping):
        raise ValueError("candidate gate checks are invalid")
    if development:
        failures = []
        for name, check in checks.items():
            if not isinstance(name, str) or not isinstance(check, Mapping):
                raise ValueError("candidate development check schema mismatch")
            passed = check.get("passed")
            if type(passed) is not bool:
                raise ValueError("candidate development check pass value is invalid")
            if not passed:
                failures.append(name)
        _require_sha256(summary["receipt_sha256"], label="gate receipt hash")
    else:
        if any(type(value) is not bool for value in checks.values()):
            raise ValueError("candidate pilot check pass value is invalid")
        failures = [name for name, value in checks.items() if not value]
        if not isinstance(summary["metrics"], Mapping):
            raise ValueError("candidate pilot metrics are invalid")
    failures = sorted(failures)
    if summary["failed_checks"] != failures:
        raise ValueError("candidate failed check derivation mismatch")
    passed = summary["passed"]
    if type(passed) is not bool or passed is not (not failures):
        raise ValueError("candidate gate pass state mismatch")
    _require_sha256(summary["file_sha256"], label="candidate gate file hash")
    return passed, failures


def _validate_candidate(candidate: Mapping[str, Any]) -> None:
    if not isinstance(candidate, Mapping) or set(candidate) != _CANDIDATE_FIELDS:
        raise ValueError("candidate fields mismatch")
    if candidate["schema_version"] != METHOD_LOCK_SCHEMA:
        raise ValueError("candidate schema mismatch")
    if candidate["scope"] not in {REAL_SCOPE, SYNTHETIC_SCOPE}:
        raise ValueError("candidate scope mismatch")
    for field in (
        "access_audit",
        "dataset",
        "dependency_receipts",
        "design_receipt",
        "execution_memory",
        "implementation_closure",
        "models",
        "replay",
        "scientific_identity",
        "source_files",
        "study_contract",
        "usage_claims",
    ):
        if not isinstance(candidate[field], Mapping):
            raise ValueError(f"candidate {field.replace('_', ' ')} is missing")
    receipt = _require_sha256(candidate["receipt_sha256"], label="candidate self hash")
    payload = {key: value for key, value in candidate.items() if key != "receipt_sha256"}
    if sha256_json(payload) != receipt:
        raise ValueError("candidate self hash mismatch")
    pilot_passed, _ = _validate_gate_summary(
        candidate["pilot_gate"], development=False
    )
    development_passed, _ = _validate_gate_summary(
        candidate["development_gate"], development=True
    )
    expected_blockers = sorted(
        name
        for name, passed in (
            ("pilot_gate_failed", pilot_passed),
            ("development_gate_failed", development_passed),
        )
        if not passed
    )
    if candidate["blockers"] != expected_blockers:
        raise ValueError("candidate blocker derivation mismatch")
    logical_positive = not expected_blockers
    expected_allowed = logical_positive and candidate["scope"] == REAL_SCOPE
    allowed = candidate["held_out_access_allowed"]
    if type(allowed) is not bool or allowed is not expected_allowed:
        raise ValueError("candidate access decision mismatch")
    expected_status = (
        "positive" if allowed else "logical_positive" if logical_positive else "blocked"
    )
    if candidate["status"] != expected_status:
        raise ValueError("candidate status mismatch")
    audit = candidate["access_audit"]
    if (
        audit.get("held_out_bundle_reads") != 0
        or audit.get("llm_calls") != 0
        or audit.get("model_refits") != 0
        or audit.get("transformer_refits") != 0
    ):
        raise ValueError("candidate access audit mismatch")
    if candidate["scope"] == REAL_SCOPE and audit.get("commits") != 0:
        raise ValueError("candidate commit audit mismatch")


def _candidate_file_hash(candidate: Mapping[str, Any]) -> str:
    return hashlib.sha256(candidate_file_bytes(candidate)).hexdigest()


def render_execution_memory_continuation(candidate: Mapping[str, Any]) -> bytes:
    """Render the exact append-only Task 1-7 execution-memory continuation."""

    _validate_candidate(candidate)
    if candidate["scope"] != REAL_SCOPE:
        raise ValueError("only the real candidate has an execution-memory report")
    source_files = candidate["source_files"]
    replay = candidate["replay"]
    source_hashes = replay["source_hashes"]
    models = candidate["models"]
    dataset = candidate["dataset"]
    usage = candidate["usage_claims"]
    development = candidate["development_gate"]
    pilot = candidate["pilot_gate"]
    collision = replay["lexical_collision"]
    state = replay["state_conformal"]
    candidate_hash = _candidate_file_hash(candidate)
    lines = [
        "",
        "## 2026-08-20 Task 1-7 development continuation and method-lock denial",
        "",
        "This append-only continuation supersedes the earlier pre-CATS status statements without rewriting them.",
        "",
        "### Frozen scientific identity",
        "",
        f"- Transaction set SHA-256: `{candidate['scientific_identity']['transaction_set_sha256']}`.",
        f"- Run-plan SHA-256: `{candidate['scientific_identity']['run_plan_sha256']}`.",
        f"- Code/runtime identity: `{candidate['scientific_identity']['code_runtime_identity']}`.",
        "",
        "### Task 1-6 receipt and artifact closure",
        "",
    ]
    top_paths = {
        "dataset_manifest": "results/exp09_cats/dataset/feature_manifest.json",
        "design_document": f"../../docs/superpowers/specs/{EXPECTED_DESIGN_DOCUMENT}",
        "design_receipt": "../../docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.receipt.json",
        "development_gate": "results/exp09_cats/replay/development/development_gate.json",
        "model_registry": "results/exp09_cats/models/model_registry.json",
        "pilot_gate": "results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json",
        "snapshot_receipt": "results/exp09_cats/development_snapshot/snapshot_receipt.json",
    }
    for name in sorted(top_paths):
        lines.append(f"- `{top_paths[name]}` SHA-256 `{source_files[name]}`.")
    for name, digest in sorted(source_hashes.items()):
        lines.append(f"- `{name}` SHA-256 `{digest}`.")
    lines.extend(
        [
            "",
            "### Development censuses and fitted artifacts",
            "",
            f"- Site split: `{canonical_json(dataset['site_partition_counts'])}`; trajectory split: `{canonical_json(dataset['trajectory_partition_counts'])}`; prefix split: `{canonical_json(dataset['prefix_partition_counts'])}`.",
            f"- Dataset row census: `{canonical_json(dataset['row_census'])}`; vocabulary size `{dataset['vocabulary_size']}` with SHA-256 `{dataset['vocabulary_sha256']}`.",
            f"- Usage event census: `{canonical_json(usage['event_counts'])}`; usage-events SHA-256 `{usage['usage_events_sha256']}`.",
            f"- Model census: `{models['variant_count']}` variants and `{models['artifact_count']}/24` bound scientific artifacts; semantic determinism `{models['semantic_comparisons_passed']}/{models['semantic_comparisons_total']}` comparisons true.",
        ]
    )
    for variant in models["variants"]:
        lines.append(
            f"- `{variant['name']}` family `{variant['family']}`, epsilon `{variant['epsilon']}`, alpha `{variant['alpha']}`, q `{variant['q_alpha']}`, semantic SHA-256 `{variant['semantic_sha256']}`."
        )
    lines.extend(
        [
            f"- Replay census: `{canonical_json(replay['row_census'])}`; replay rows SHA-256 `{replay['replay_rows_sha256']}`.",
            f"- State-conformal calibration uses `{state['source_partition']}` rows, q `{state['q_alpha']}`, and `adapted_after_development_outcomes={str(state['adapted_after_development_outcomes']).lower()}`.",
            f"- The legacy lexical comparator is algorithmically distinct, but its stop vector collides with max-cap on `{collision['matching_stop_turns']}/{collision['trajectory_count']}` trajectories; collision-vector SHA-256 `{collision['collision_vector_sha256']}`. No independent empirical contrast is claimed.",
            "",
            "### Gates, usage boundary, and access decision",
            "",
        ]
    )
    for name, check in development["checks"].items():
        lines.append(
            f"- Development check `{name}`: passed `{str(check['passed']).lower()}`, observed `{check['observed']}`, operator `{check['operator']}`, threshold `{check['threshold']}`."
        )
    lines.extend(
        [
            f"- Development gate result: passed `{str(development['passed']).lower()}`; failed checks `{canonical_json(development['failed_checks'])}`.",
            f"- Pilot gate result: passed `{str(pilot['passed']).lower()}`; failed checks derived from false values `{canonical_json(pilot['failed_checks'])}`.",
            f"- Usage claim boundary: `{usage['visible_agent_token_boundary']}` Visible-agent tokens are available, while invoice-grade cost is `{str(usage['invoice_grade_cost']).lower()}` and total-compute claims are `{str(usage['total_compute']).lower()}` for reasons `{canonical_json(usage['reasons'])}`. These limitations are not monetary or total-compute savings claims.",
            f"- Method-lock candidate `results/exp09_cats/method_lock_candidate.json` file SHA-256 `{candidate_hash}`; canonical self-hash `{candidate['receipt_sha256']}`; blockers `{canonical_json(candidate['blockers'])}`.",
            "- `held_out_access_allowed=false`.",
            "- Access audit: zero restricted-bundle reads, zero additional LLM calls, zero model or transformer refits, and zero commits for Tasks 1-7.",
            "- No held-out or OOD work may proceed. The failed pilot and development gates remain binding; no retuning or reinterpretation is authorized.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _baseline_memory_path() -> Path:
    workspace = Path(__file__).resolve().parents[3]
    return workspace / (
        ".superpowers/sdd/2026-08-19-iclr2027-development-snapshot-cats-gate/"
        "baselines/task-7/ICLR_2027_EXECUTION_MEMORY_2026-08-19.md"
    )


def _authoritative_memory_path() -> Path:
    return Path(__file__).resolve().parents[1] / EXPECTED_EXECUTION_MEMORY_NAME


def _verify_execution_memory(candidate: Mapping[str, Any], path: str | Path) -> None:
    binding = candidate["execution_memory"]
    if binding != _real_execution_memory_binding():
        raise ValueError("execution memory binding mismatch")
    authoritative = _authoritative_memory_path()
    if not _same_lexical_path(path, authoritative):
        raise ValueError("authoritative execution memory path mismatch")
    baseline_bytes = read_authenticated_file(
        _baseline_memory_path(), label="execution memory baseline"
    )
    if hashlib.sha256(baseline_bytes).hexdigest() != EXPECTED_EXECUTION_MEMORY_BASELINE_SHA256:
        raise ValueError("execution memory baseline SHA-256 mismatch")
    memory_bytes = read_authenticated_file(
        authoritative, label="authoritative execution memory"
    )
    expected = baseline_bytes + render_execution_memory_continuation(candidate)
    if memory_bytes != expected:
        raise ValueError("execution memory is stale or mismatched")


def _early_source_comparison(
    candidate: Mapping[str, Any],
    *,
    paths: _SourcePaths,
) -> None:
    observed = _observed_top_source_hashes(paths)
    if candidate["source_files"] != observed:
        raise ValueError("candidate source-file closure mismatch")
    pilot = _validate_pilot_gate(paths)
    persisted_gate = _read_json(paths.replay, label="development gate", canonical=True)
    if candidate["pilot_gate"] != _pilot_summary(
        pilot, file_sha256=observed["pilot_gate"]
    ):
        raise ValueError("candidate pilot gate closure mismatch")
    if candidate["development_gate"] != _development_summary(
        persisted_gate, file_sha256=observed["development_gate"]
    ):
        raise ValueError("candidate development gate closure mismatch")
    if candidate["implementation_closure"] != _implementation_closure(
        persisted_gate, project_root=paths.project_root
    ):
        raise ValueError("candidate implementation closure mismatch")


def verify_method_lock_candidate(
    candidate: str | Path,
    *,
    design_receipt: str | Path | None = None,
    snapshot: str | Path | None = None,
    pilot_gate: str | Path | None = None,
    dataset: str | Path | None = None,
    models: str | Path | None = None,
    replay: str | Path | None = None,
    execution_memory: str | Path | None = None,
    expected_candidate_file_sha256: str | None = None,
) -> dict[str, Any]:
    """Authenticate a candidate from complete sources or an external file digest."""

    source_values = (design_receipt, snapshot, pilot_gate, dataset, models, replay)
    source_mode = all(value is not None for value in source_values)
    partial_source_mode = any(value is not None for value in source_values)
    digest_mode = expected_candidate_file_sha256 is not None
    if partial_source_mode and not source_mode:
        raise ValueError("source verification requires all six frozen inputs")
    if source_mode == digest_mode:
        raise ValueError("select exactly one trusted method-lock verification mode")
    if digest_mode:
        _require_sha256(
            expected_candidate_file_sha256, label="trusted candidate file hash"
        )

    candidate_path = Path(candidate)
    candidate_artifact = read_authenticated_file(
        candidate_path, label="method-lock candidate"
    )
    value = _decode_json_object(candidate_artifact, label="method-lock candidate")
    if candidate_artifact != (canonical_json(value) + "\n").encode("utf-8"):
        raise ValueError("method-lock candidate is not canonical JSON")
    _validate_candidate(value)
    if digest_mode:
        if hashlib.sha256(candidate_artifact).hexdigest() != expected_candidate_file_sha256:
            raise ValueError("trusted candidate file SHA-256 mismatch")
        if value["scope"] == REAL_SCOPE:
            if execution_memory is None:
                raise ValueError("authoritative execution memory is required")
            _verify_execution_memory(value, execution_memory)
        elif execution_memory is not None:
            raise ValueError("non-real candidates do not bind authoritative execution memory")
        return value

    if execution_memory is None:
        raise ValueError("authoritative execution memory is required")
    _verify_execution_memory(value, execution_memory)

    assert design_receipt is not None
    assert snapshot is not None
    assert pilot_gate is not None
    assert dataset is not None
    assert models is not None
    assert replay is not None
    assert execution_memory is not None
    with _prepare_source_paths(
        design_receipt=design_receipt,
        snapshot=snapshot,
        pilot_gate=pilot_gate,
        dataset=dataset,
        models=models,
        replay=replay,
    ) as paths:
        _early_source_comparison(value, paths=paths)
        closure = _source_closure(paths)
        verified_pilot = closure.pop("_pilot_gate")
        verified_development = closure.pop("_development_gate")
        assert isinstance(verified_pilot, Mapping)
        assert isinstance(verified_development, Mapping)
        expected = build_method_lock(
            closure,
            pilot_gate=verified_pilot,
            development_gate=verified_development,
        )
        if candidate_artifact != candidate_file_bytes(expected):
            raise ValueError("candidate differs from source reconstruction")
    return value


def require_positive_method_lock(
    candidate: str | Path,
    *,
    design_receipt: str | Path | None = None,
    snapshot: str | Path | None = None,
    pilot_gate: str | Path | None = None,
    dataset: str | Path | None = None,
    models: str | Path | None = None,
    replay: str | Path | None = None,
    execution_memory: str | Path | None = None,
    expected_candidate_file_sha256: str | None = None,
) -> MethodLockAuthorization:
    """Independently authenticate, then require a genuinely positive lock."""

    verified = verify_method_lock_candidate(
        candidate,
        design_receipt=design_receipt,
        snapshot=snapshot,
        pilot_gate=pilot_gate,
        dataset=dataset,
        models=models,
        replay=replay,
        execution_memory=execution_memory,
        expected_candidate_file_sha256=expected_candidate_file_sha256,
    )
    if verified["scope"] != REAL_SCOPE:
        raise PermissionError("non-real synthetic scope cannot authorize access")
    if (
        verified["held_out_access_allowed"] is not True
        or verified["blockers"]
        or verified["pilot_gate"]["passed"] is not True
        or verified["development_gate"]["passed"] is not True
    ):
        raise PermissionError("positive method lock is required")
    return MethodLockAuthorization(
        logical_method_lock_positive=True,
        real_data_access=True,
        scope=REAL_SCOPE,
    )


def validate_logical_method_lock(candidate: Mapping[str, Any]) -> bool:
    """Validate a synthetic fixture's logic without granting any data access."""

    _validate_candidate(candidate)
    if candidate["scope"] != SYNTHETIC_SCOPE:
        raise ValueError("logical fixture validation requires synthetic scope")
    return bool(
        not candidate["blockers"]
        and candidate["pilot_gate"]["passed"] is True
        and candidate["development_gate"]["passed"] is True
        and candidate["held_out_access_allowed"] is False
        and candidate["status"] == "logical_positive"
    )


__all__ = (
    "EXECUTION_MEMORY_CONTINUATION_SCHEMA",
    "METHOD_LOCK_SCHEMA",
    "MethodLockAuthorization",
    "REAL_SCOPE",
    "SYNTHETIC_SCOPE",
    "build_method_lock",
    "build_method_lock_from_sources",
    "candidate_file_bytes",
    "render_execution_memory_continuation",
    "require_positive_method_lock",
    "validate_logical_method_lock",
    "verify_method_lock_candidate",
)
