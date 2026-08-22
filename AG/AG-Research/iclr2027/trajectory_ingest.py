"""Read-only validation and freezing of the Exp08 development snapshot."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .artifact_receipts import canonical_artifact_receipt
from .exp08 import load_validated_transactions
from .io import sha256_json
from .pilot_gate import PILOT_PATTERNS, transaction_set_receipt
from .run_manifest import validate_run_manifest
from .secure_files import read_authenticated_file
from .study_contract import StudyContract


DEVELOPMENT_SNAPSHOT_SCHEMA = "ace.iclr2027.development_snapshot_receipt.v1"
DEVELOPMENT_SNAPSHOT_SOURCES_SCHEMA = (
    "ace.iclr2027.development_snapshot_sources.v1"
)
EXPECTED_TRANSACTION_SET_SHA256 = (
    "3e7e9c0edd5fc8b1f2cc77f69da6dca9e381018d117a2cf3e8e6a4e94459de74"
)
EXPECTED_RUN_PLAN_SHA256 = (
    "7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9"
)
EXPECTED_CODE_RUNTIME_IDENTITY = (
    "179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7"
    "-deps-48d730d98a916537"
)

_PLAN_IDENTITY_FIELDS = (
    "case_id",
    "pattern",
    "repeat",
    "model",
    "public_case_sha256",
    "prompt_sha256",
    "code_commit",
)
_PLAN_FIELDS = frozenset((*_PLAN_IDENTITY_FIELDS, "resume_key"))
_MESSAGE_FIELDS = ("index", "source", "content", "tokens_in", "tokens_out")


@dataclass(frozen=True)
class DevelopmentSnapshot:
    transactions: tuple[Mapping[str, Any], ...]
    transaction_set_sha256: str
    run_plan_sha256: str
    run_plan_identity_sha256: str
    code_runtime_identity: str
    completed_checkpoint_count: int
    terminal_error_count: int
    parsed_state_count: int
    parse_complete_count: int
    final_parse_complete_count: int
    message_hashes: Mapping[str, tuple[str, ...]]


def _read_json(path: Path, label: str) -> Any:
    try:
        artifact = read_authenticated_file(path, label=label)
        return json.loads(artifact.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not readable canonical JSON") from exc


def _sha256_file(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(read_authenticated_file(path, label=label)).hexdigest()
    except OSError as exc:
        raise ValueError(f"{label} is not readable") from exc


def _validated_run_plan(
    payload: Any,
    *,
    expected_count: int,
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    if not isinstance(payload, list) or len(payload) != expected_count:
        raise ValueError("run plan does not have the exact expected census")
    identities: list[Mapping[str, Any]] = []
    resume_keys: list[str] = []
    for row in payload:
        if not isinstance(row, Mapping) or set(row) != _PLAN_FIELDS:
            raise ValueError("run plan identity fields are not exact")
        identity = {field: row[field] for field in _PLAN_IDENTITY_FIELDS}
        resume_key = row["resume_key"]
        if not isinstance(resume_key, str) or sha256_json(identity) != resume_key:
            raise ValueError("run plan resume identity is invalid")
        identities.append(identity)
        resume_keys.append(resume_key)
    if len(set(resume_keys)) != expected_count:
        raise ValueError("run plan resume identities are not unique")
    return tuple(identities), tuple(resume_keys)


def _ordered_agent_message_hashes(
    transaction: Mapping[str, Any],
) -> tuple[str, ...]:
    turns = transaction["raw"]["result"]["turns"]
    return tuple(
        sha256_json({field: turn[field] for field in _MESSAGE_FIELDS})
        for turn in turns
        if str(turn["source"]).lower() != "user"
    )


def load_development_snapshot(
    results_dir: str | Path,
    *,
    expected_count: int = 450,
) -> DevelopmentSnapshot:
    """Validate and load the exact frozen development transaction snapshot."""

    if type(expected_count) is not int or expected_count <= 0:
        raise ValueError("expected_count must be a positive native integer")
    results = Path(results_dir)
    if not results.is_dir():
        raise ValueError("results directory does not exist")

    manifest = validate_run_manifest(
        _read_json(results / "run_manifest.json", "run manifest")
    )
    if (
        manifest["split"] != "dev"
        or manifest["input_mode"] != "frozen_private_binding"
        or manifest["patterns"] != list(PILOT_PATTERNS)
        or manifest["repeats"] != 3
        or manifest["planned_run_count"] != expected_count
        or manifest["executed"] is not True
    ):
        raise ValueError("run manifest is not the exact executed development plan")
    if manifest["expected_case_count"] != manifest["case_count"]:
        raise ValueError("run manifest does not bind the full development case set")
    if manifest["code_commit"] != EXPECTED_CODE_RUNTIME_IDENTITY:
        raise ValueError("code/runtime identity does not match the frozen v12 commitment")

    run_plan_path = results / "run_plan.json"
    run_plan_sha256 = _sha256_file(run_plan_path, "run plan")
    if run_plan_sha256 != EXPECTED_RUN_PLAN_SHA256:
        raise ValueError("run-plan SHA-256 does not match the frozen v12 commitment")
    plan_identities, plan_keys = _validated_run_plan(
        _read_json(run_plan_path, "run plan"), expected_count=expected_count
    )
    plan_identity_sha256 = sha256_json(plan_identities)
    if manifest["plan_sha256"] != plan_identity_sha256:
        raise ValueError("run manifest and run-plan identities do not match")
    case_ids = {str(identity["case_id"]) for identity in plan_identities}
    plan_composition = {
        (
            str(identity["case_id"]),
            str(identity["pattern"]),
            int(identity["repeat"]),
        )
        for identity in plan_identities
    }
    expected_composition = {
        (case_id, pattern, repeat)
        for case_id in case_ids
        for pattern in manifest["patterns"]
        for repeat in range(manifest["repeats"])
    }
    if (
        len(case_ids) != manifest["case_count"]
        or plan_composition != expected_composition
        or any(
            identity["model"] != manifest["model"]
            or identity["code_commit"] != manifest["code_commit"]
            for identity in plan_identities
        )
    ):
        raise ValueError("run manifest and run-plan composition do not match")

    transaction_set_sha256, transaction_count = transaction_set_receipt(results)
    if transaction_count != expected_count:
        raise ValueError("transaction set does not have the exact expected census")
    if transaction_set_sha256 != EXPECTED_TRANSACTION_SET_SHA256:
        raise ValueError(
            "transaction-set SHA-256 does not match the frozen v12 commitment"
        )

    transactions = load_validated_transactions(results)
    transaction_keys = tuple(
        str(transaction["resume_identity_sha256"])
        for transaction in transactions
    )
    if len(transactions) != expected_count or set(transaction_keys) != set(plan_keys):
        raise ValueError("transaction and run-plan key censuses are not exactly equal")

    completed_count = sum(
        transaction["checkpoint"]["status"] == "completed"
        for transaction in transactions
    )
    terminal_error_count = sum(
        transaction["checkpoint"]["status"] == "error"
        for transaction in transactions
    )
    if completed_count != expected_count or terminal_error_count != 0:
        raise ValueError("development snapshot has incomplete or terminal-error runs")

    parsed_state_count = sum(len(transaction["parsed"]) for transaction in transactions)
    parse_complete_count = sum(
        row["parse_complete"] is True
        for transaction in transactions
        for row in transaction["parsed"]
    )
    final_parse_complete_count = sum(
        bool(transaction["parsed"])
        and transaction["parsed"][-1]["parse_complete"] is True
        for transaction in transactions
    )
    if final_parse_complete_count != expected_count:
        raise ValueError("not every completed transaction has a final parse-complete state")
    expected_execution = {
        "completed_runs": completed_count + terminal_error_count,
        "error_runs": terminal_error_count,
        "parsed_states": parsed_state_count,
        "skipped_runs": expected_count - completed_count - terminal_error_count,
        "successful_parses": parse_complete_count,
    }
    if manifest["execution"] != expected_execution:
        raise ValueError("run manifest execution census does not match transactions")

    message_hashes = {
        str(transaction["resume_identity_sha256"]): _ordered_agent_message_hashes(
            transaction
        )
        for transaction in transactions
    }
    if any(
        len(message_hashes[str(transaction["resume_identity_sha256"])])
        != len(transaction["parsed"])
        for transaction in transactions
    ):
        raise ValueError("agent-message and parsed-state censuses do not match")

    return DevelopmentSnapshot(
        transactions=transactions,
        transaction_set_sha256=transaction_set_sha256,
        run_plan_sha256=run_plan_sha256,
        run_plan_identity_sha256=plan_identity_sha256,
        code_runtime_identity=str(manifest["code_commit"]),
        completed_checkpoint_count=completed_count,
        terminal_error_count=terminal_error_count,
        parsed_state_count=parsed_state_count,
        parse_complete_count=parse_complete_count,
        final_parse_complete_count=final_parse_complete_count,
        message_hashes=MappingProxyType(message_hashes),
    )


def _validate_negative_pilot_gate(path: Path) -> Mapping[str, Any]:
    gate = _read_json(path, "pilot gate")
    checks = gate.get("checks") if isinstance(gate, Mapping) else None
    if (
        not isinstance(gate, Mapping)
        or gate.get("passed") is not False
        or not isinstance(checks, Mapping)
        or checks.get("pilot_complete") is not True
        or checks.get("transaction_set_bound") is not True
        or checks.get("no_terminal_run_errors") is not True
        or checks.get("all_final_states_parse_complete") is not True
    ):
        raise ValueError("pilot gate is not the bound completed negative v12 gate")
    return gate


def build_development_snapshot_receipt(
    snapshot: DevelopmentSnapshot,
    *,
    results_dir: str | Path,
    pilot_gate_path: str | Path,
) -> dict[str, Any]:
    """Build a canonical receipt binding snapshot bytes, censuses, and messages."""

    results = Path(results_dir)
    pilot_gate = Path(pilot_gate_path)
    if pilot_gate.resolve() != (results / "pilot_gate.json").resolve():
        raise ValueError("pilot gate must be the gate inside the results directory")
    _validate_negative_pilot_gate(pilot_gate)

    message_hashes = {
        key: list(hashes) for key, hashes in sorted(snapshot.message_hashes.items())
    }
    row_census = {
        "agent_messages": sum(len(hashes) for hashes in message_hashes.values()),
        "completed_checkpoints": snapshot.completed_checkpoint_count,
        "final_parse_complete_states": snapshot.final_parse_complete_count,
        "parse_complete_states": snapshot.parse_complete_count,
        "parsed_states": snapshot.parsed_state_count,
        "terminal_errors": snapshot.terminal_error_count,
        "transactions": len(snapshot.transactions),
    }
    source_files = {
        "pilot_gate.json": pilot_gate,
        "run_manifest.json": results / "run_manifest.json",
        "run_plan.json": results / "run_plan.json",
        **{
            f"run_transactions/{key}.json": results / "run_transactions" / f"{key}.json"
            for key in sorted(message_hashes)
        },
    }
    bindings = {
        "code_runtime_identity_sha256": sha256_json(snapshot.code_runtime_identity),
        "message_hashes_sha256": sha256_json(message_hashes),
        "run_plan_identity_sha256": snapshot.run_plan_identity_sha256,
        "run_plan_sha256": snapshot.run_plan_sha256,
        "study_contract_sha256": sha256_json(asdict(StudyContract.primary())),
        "transaction_set_sha256": snapshot.transaction_set_sha256,
    }
    sources_receipt = canonical_artifact_receipt(
        schema_version=DEVELOPMENT_SNAPSHOT_SOURCES_SCHEMA,
        files=source_files,
        row_census=row_census,
        bindings=bindings,
    )
    payload: dict[str, Any] = {
        "code_runtime_identity": snapshot.code_runtime_identity,
        "completed_checkpoint_count": snapshot.completed_checkpoint_count,
        "final_parse_complete_count": snapshot.final_parse_complete_count,
        "message_hashes": message_hashes,
        "parse_complete_count": snapshot.parse_complete_count,
        "parsed_state_count": snapshot.parsed_state_count,
        "pilot_gate_passed": False,
        "run_plan_identity_sha256": snapshot.run_plan_identity_sha256,
        "run_plan_sha256": snapshot.run_plan_sha256,
        "schema_version": DEVELOPMENT_SNAPSHOT_SCHEMA,
        "source_artifact_receipt": sources_receipt,
        "study_contract": asdict(StudyContract.primary()),
        "terminal_error_count": snapshot.terminal_error_count,
        "transaction_count": len(snapshot.transactions),
        "transaction_set_sha256": snapshot.transaction_set_sha256,
    }
    return {**payload, "receipt_sha256": sha256_json(payload)}


__all__ = (
    "DEVELOPMENT_SNAPSHOT_SCHEMA",
    "DevelopmentSnapshot",
    "build_development_snapshot_receipt",
    "load_development_snapshot",
)
