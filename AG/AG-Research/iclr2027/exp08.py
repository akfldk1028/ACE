"""Leakage-safe planning primitives for the Exp08 architecture pilot."""

from __future__ import annotations

import json
import hashlib
import math
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Sequence
from types import SimpleNamespace

from config import PATTERNS_ALL

from .io import (
    canonical_json,
    sha256_json,
    write_csv_atomic,
    write_json_atomic,
    write_jsonl_atomic,
)
from .architecture_metrics import score_prefix, score_prefix_breakdown
from .review_state import TurnRecord, accumulate_prefix_states
from .protocol import validate_pilot_protocol
from .schema import (
    ArchitectureEvidencePacket,
    ArchitectureGoldRecord,
    ArchitecturePublicCase,
    ArchitectureReviewState,
)
from .secure_files import AuthenticatedTree, read_authenticated_file
from .pilot_gate import (
    ALLOWED_CASE_STAGES,
    PILOT_SCORING_PROVENANCE_SCHEMA,
    PILOT_SUMMARY_V2_SCHEMA,
    PilotScoringProvenance,
    PilotSummary,
    transaction_set_receipt,
)
from .prompts import (
    ARCH_REVIEW_DECISION_RULES,
    ARCH_REVIEW_EVIDENCE_POLICY,
    ARCH_REVIEW_RESPONSE_ORDER,
    ARCH_REVIEW_STATE_BLOCK,
)


@dataclass(frozen=True)
class RunPlan:
    case_id: str
    pattern: str
    repeat: int
    model: str
    public_case_sha256: str
    prompt_sha256: str
    code_commit: str
    prompt: str
    resume_key: str

    @property
    def resume_identity(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "pattern": self.pattern,
            "repeat": self.repeat,
            "model": self.model,
            "public_case_sha256": self.public_case_sha256,
            "prompt_sha256": self.prompt_sha256,
            "code_commit": self.code_commit,
        }

    def to_dict(self, *, include_prompt: bool = False) -> dict[str, Any]:
        payload = {**self.resume_identity, "resume_key": self.resume_key}
        if include_prompt:
            payload["prompt"] = self.prompt
        return payload


def render_case_prompt(public_case: ArchitecturePublicCase) -> str:
    """Render an already-validated public case; never redact private packets here."""

    if not isinstance(public_case, ArchitecturePublicCase):
        raise TypeError("prompt input must be an ArchitecturePublicCase")
    prompt_packet = public_case.to_dict()
    prompt_packet.pop("case_id")
    evidence_ids = sorted(
        str(item.get("evidence_id"))
        for item in public_case.evidence
        if item.get("evidence_id")
    )
    attempt_hash_matches: bool | None = None
    if public_case.subject_kind == "portfolio_attempt":
        attempt_record = next(
            (
                item
                for item in public_case.evidence
                if item.get("evidence_id") == "evidence:portfolio_attempt"
            ),
            None,
        )
        attempt_manifest = (
            attempt_record.get("evidence")
            if isinstance(attempt_record, Mapping)
            else None
        )
        attempt_hash_matches = bool(
            isinstance(attempt_manifest, Mapping)
            and public_case.attempt_hash == sha256_json(dict(attempt_manifest))
        )
    decision_facts = {
        "available_evidence_ids": evidence_ids,
        "portfolio_attempt_hash_matches": attempt_hash_matches,
        "subject_kind": public_case.subject_kind,
        "attempt_stage": public_case.attempt_stage,
    }
    return (
        "Review this architecture evidence packet. Cite supplied evidence IDs, "
        "report missing evidence, and emit the required ARCH_REVIEW_STATE block. "
        "Do not assume facts outside the packet.\n\nEVIDENCE_PACKET\n"
        + canonical_json(prompt_packet)
        + "\nEND_EVIDENCE_PACKET\n\nDECISION_FACTS\n"
        + canonical_json(decision_facts)
        + "\nEND_DECISION_FACTS\n\n"
        + ARCH_REVIEW_RESPONSE_ORDER
        + "\nYour response must include exactly one complete block in this exact form:\n"
        + ARCH_REVIEW_STATE_BLOCK
        + "\n"
        + ARCH_REVIEW_DECISION_RULES
        + "\n"
        + ARCH_REVIEW_EVIDENCE_POLICY
        + "\nReplace the example values using only supplied evidence. If your system "
        "prompt requests a topology termination signal, append it only after the "
        "complete fenced block. A signal before or without a parse-valid block is invalid."
    )


def build_run_plan(
    cases: Sequence[Mapping[str, Any] | ArchitecturePublicCase],
    *,
    patterns: Sequence[str],
    repeats: int,
    model: str,
    code_commit: str,
) -> tuple[RunPlan, ...]:
    """Build deterministic run identities for case × topology × repeat."""

    if repeats <= 0:
        raise ValueError("repeats must be positive")
    if not model.strip():
        raise ValueError("model must be nonempty")
    unknown_patterns = set(patterns) - set(PATTERNS_ALL)
    if unknown_patterns:
        raise ValueError(f"unknown patterns: {sorted(unknown_patterns)}")
    public_cases = [
        case
        if isinstance(case, ArchitecturePublicCase)
        else ArchitecturePublicCase.from_dict(case)
        for case in cases
    ]
    public_cases.sort(key=lambda case: case.case_id)
    if len({case.case_id for case in public_cases}) != len(public_cases):
        raise ValueError("duplicate case_id in run plan")

    plans: list[RunPlan] = []
    for pattern in patterns:
        for public_case in public_cases:
            public_case_sha = sha256_json(public_case.to_dict())
            prompt = render_case_prompt(public_case)
            prompt_sha = sha256_json(prompt)
            for repeat in range(repeats):
                identity = {
                    "case_id": public_case.case_id,
                    "pattern": pattern,
                    "repeat": repeat,
                    "model": model,
                    "public_case_sha256": public_case_sha,
                    "prompt_sha256": prompt_sha,
                    "code_commit": code_commit,
                }
                plans.append(
                    RunPlan(
                        **identity,
                        prompt=prompt,
                        resume_key=sha256_json(identity),
                    )
                )
    return tuple(plans)


@dataclass(frozen=True)
class ExecutionSummary:
    completed_runs: int
    skipped_runs: int
    error_runs: int
    parsed_states: int
    successful_parses: int


def _completed_resume_keys(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(payload, Mapping)
            and payload.get("resume_key")
            and payload.get("status") == "completed"
        ):
            keys.add(str(payload["resume_key"]))
    return keys


_SCORE_FIELDS = (
    "resume_key",
    "case_id",
    "pattern",
    "repeat",
    "turn_index",
    "issue_f1",
    "evidence_f1",
    "domain_coverage",
    "verdict_score",
    "quality",
)

_SCORE_IDENTITY_FIELDS = (
    "resume_key",
    "case_id",
    "pattern",
    "repeat",
    "turn_index",
)

_BREAKDOWN_FIELDS = (
    *_SCORE_IDENTITY_FIELDS,
    "subject_stage",
    "decision_score",
    "blocking_issue_f1",
    "missing_evidence_f1",
)

RUN_TRANSACTION_SCHEMA = "ace.iclr2027.run_transaction.v1"
_RESUME_IDENTITY_FIELDS = (
    "case_id",
    "pattern",
    "repeat",
    "model",
    "public_case_sha256",
    "prompt_sha256",
    "code_commit",
)
_TRANSACTION_KEYS = {
    "schema_version",
    "resume_identity_sha256",
    "raw",
    "parsed",
    "scores",
    "score_breakdowns",
    "errors",
    "checkpoint",
}
_RAW_KEYS = frozenset({*_RESUME_IDENTITY_FIELDS, "resume_key", "result"})
_CHECKPOINT_KEYS = frozenset({"resume_key", "status"})
_PARSED_FIELDS = frozenset(
    {
        *_SCORE_IDENTITY_FIELDS,
        "source",
        "parse_complete",
        "parse_error_codes",
        "state",
    }
)
_ERROR_FIELDS = frozenset(
    {
        *_RESUME_IDENTITY_FIELDS,
        "resume_key",
        "attempt",
        "error",
    }
)
_STATE_FIELDS = frozenset(
    {
        "checked_domains",
        "blocking_issue_codes",
        "missing_evidence_codes",
        "evidence_ids",
        "recommended_decision",
        "confidence",
    }
)
_RUN_RESULT_FIELDS = frozenset(
    {
        "experiment_id",
        "task_id",
        "pattern",
        "repeat_index",
        "pattern_category",
        "agent_count",
        "stop_reason",
        "duration_sec",
        "total_tokens_in",
        "total_tokens_out",
        "total_tokens",
        "turn_count",
        "agent_turn_count",
        "terminated_by",
        "turns",
        "error",
        "quality_score",
        "converged_at",
        "stage_results",
    }
)
_TURN_FIELDS = frozenset(
    {"index", "source", "content", "timestamp", "tokens_in", "tokens_out"}
)
_LOWER_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_CASE_ID = re.compile(r"^case:[0-9a-f]{64}$")


def _require_exact_row_keys(
    row: Any,
    expected: frozenset[str],
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(row, Mapping) or set(row) != expected:
        raise ValueError(f"{label} must contain exact keys")
    return row


def _validate_outer_resume_identity(raw: Mapping[str, Any], identity: str) -> None:
    if not _LOWER_SHA256.fullmatch(identity):
        raise ValueError("run transaction identity mismatch")
    case_id = raw.get("case_id")
    if not isinstance(case_id, str) or not _PUBLIC_CASE_ID.fullmatch(case_id):
        raise ValueError("run transaction case identity is invalid")
    if raw.get("pattern") not in PATTERNS_ALL:
        raise ValueError("run transaction pattern is invalid")
    if type(raw.get("repeat")) is not int or raw["repeat"] < 0:
        raise ValueError("run transaction repeat is invalid")
    for field in ("model", "code_commit"):
        if not isinstance(raw.get(field), str) or not str(raw[field]).strip():
            raise ValueError(f"run transaction {field} is invalid")
    for field in ("public_case_sha256", "prompt_sha256"):
        value = raw.get(field)
        if not isinstance(value, str) or not _LOWER_SHA256.fullmatch(value):
            raise ValueError(f"run transaction {field} is invalid")


def _validate_nested_identity(
    row: Mapping[str, Any],
    raw: Mapping[str, Any],
    *,
    include_turn: bool,
) -> tuple[str, str, int, int] | None:
    if type(row.get("repeat")) is not int:
        raise ValueError("nested transaction repeat must be an integer")
    for field in ("resume_key", "case_id", "pattern", "repeat"):
        if row.get(field) != raw.get(field):
            raise ValueError("nested transaction identity mismatch")
    if not include_turn:
        return None
    turn_index = row.get("turn_index")
    if type(turn_index) is not int or turn_index < 0:
        raise ValueError("nested transaction turn index is invalid")
    return (
        str(row["resume_key"]),
        str(row["case_id"]),
        int(row["repeat"]),
        turn_index,
    )


def _validate_unit_metric(value: Any, label: str) -> None:
    if (
        type(value) not in {int, float}
        or not math.isfinite(float(value))
        or not 0.0 <= float(value) <= 1.0
    ):
        raise ValueError(f"{label} must be finite within [0, 1]")


def _validate_optional_string(value: Any, label: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{label} must be a nonempty string or null")


def _validate_raw_result(
    value: Any,
    raw: Mapping[str, Any],
) -> tuple[tuple[int, str], ...]:
    result = _require_exact_row_keys(value, _RUN_RESULT_FIELDS, "raw result")
    if type(result.get("repeat_index")) is not int:
        raise ValueError("raw result repeat_index must be an integer")
    if (
        result.get("task_id") != raw.get("case_id")
        or result.get("pattern") != raw.get("pattern")
        or result.get("repeat_index") != raw.get("repeat")
    ):
        raise ValueError("raw result identity mismatch")
    for field in ("experiment_id", "pattern_category"):
        if not isinstance(result.get(field), str) or not str(result[field]).strip():
            raise ValueError(f"raw result {field} is invalid")
    if type(result.get("agent_count")) is not int or result["agent_count"] < 0:
        raise ValueError("raw result agent_count is invalid")
    for field in ("stop_reason", "terminated_by"):
        _validate_optional_string(result.get(field), f"raw result {field}")
    duration = result.get("duration_sec")
    if (
        type(duration) not in {int, float}
        or not math.isfinite(float(duration))
        or duration < 0
    ):
        raise ValueError("raw result duration_sec is invalid")
    for field in (
        "total_tokens_in",
        "total_tokens_out",
        "total_tokens",
        "turn_count",
        "agent_turn_count",
    ):
        if type(result.get(field)) is not int or result[field] < 0:
            raise ValueError(f"raw result {field} is invalid")
    if result["total_tokens"] != (
        result["total_tokens_in"] + result["total_tokens_out"]
    ):
        raise ValueError("raw result token cardinality mismatch")
    quality_score = result.get("quality_score")
    if quality_score is not None and (
        type(quality_score) not in {int, float}
        or not math.isfinite(float(quality_score))
    ):
        raise ValueError("raw result quality_score is invalid")
    converged_at = result.get("converged_at")
    if converged_at is not None and (type(converged_at) is not int or converged_at < 0):
        raise ValueError("raw result converged_at is invalid")
    if result.get("stage_results") is not None and not isinstance(
        result["stage_results"], list
    ):
        raise ValueError("raw result stage_results is invalid")
    turns = result.get("turns")
    if not isinstance(turns, list):
        raise ValueError("raw result turns must be a list")
    turn_refs: list[tuple[int, str]] = []
    prior_index = -1
    for item in turns:
        turn = _require_exact_row_keys(item, _TURN_FIELDS, "raw result turn")
        index = turn.get("index")
        if type(index) is not int or index < 0 or index <= prior_index:
            raise ValueError("raw result turn indices must be strictly increasing")
        prior_index = index
        source = turn.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("raw result turn source is invalid")
        for field in ("content", "timestamp"):
            if not isinstance(turn.get(field), str):
                raise ValueError(f"raw result turn {field} is invalid")
        for field in ("tokens_in", "tokens_out"):
            if type(turn.get(field)) is not int or turn[field] < 0:
                raise ValueError(f"raw result turn {field} is invalid")
        if source.lower() != "user":
            turn_refs.append((index, source))
    if result["turn_count"] != len(turns):
        raise ValueError("raw result turn cardinality mismatch")
    if result["agent_turn_count"] != len(turn_refs):
        raise ValueError("raw result agent turn cardinality mismatch")
    return tuple(turn_refs)


def _validate_persisted_rows(
    payload: Mapping[str, Any],
    raw: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
) -> None:
    parsed_ids: list[tuple[str, str, int, int]] = []
    parsed_turn_refs: list[tuple[int, str]] = []
    for item in payload["parsed"]:
        row = _require_exact_row_keys(item, _PARSED_FIELDS, "parsed row")
        identity = _validate_nested_identity(row, raw, include_turn=True)
        assert identity is not None
        parsed_ids.append(identity)
        if not isinstance(row.get("source"), str) or not str(row["source"]).strip():
            raise ValueError("parsed row source is invalid")
        parsed_turn_refs.append((int(row["turn_index"]), str(row["source"])))
        if type(row.get("parse_complete")) is not bool:
            raise ValueError("parsed row parse_complete must be boolean")
        errors = row.get("parse_error_codes")
        if not isinstance(errors, list) or any(
            not isinstance(code, str) or not code for code in errors
        ):
            raise ValueError("parsed row parse_error_codes are invalid")
        state = _require_exact_row_keys(row.get("state"), _STATE_FIELDS, "review state")
        if ArchitectureReviewState.from_dict(state).to_dict() != dict(state):
            raise ValueError("parsed review state is not canonical")

    score_ids: list[tuple[str, str, int, int]] = []
    for item in payload["scores"]:
        row = _require_exact_row_keys(item, frozenset(_SCORE_FIELDS), "score row")
        identity = _validate_nested_identity(row, raw, include_turn=True)
        assert identity is not None
        score_ids.append(identity)
        for field in (
            "issue_f1",
            "evidence_f1",
            "domain_coverage",
            "verdict_score",
            "quality",
        ):
            _validate_unit_metric(row.get(field), f"score row {field}")

    breakdown_ids: list[tuple[str, str, int, int]] = []
    for item in payload["score_breakdowns"]:
        row = _require_exact_row_keys(
            item,
            frozenset(_BREAKDOWN_FIELDS),
            "score breakdown row",
        )
        identity = _validate_nested_identity(row, raw, include_turn=True)
        assert identity is not None
        breakdown_ids.append(identity)
        if row.get("subject_stage") not in ALLOWED_CASE_STAGES:
            raise ValueError("score breakdown subject_stage is invalid")
        for field in (
            "decision_score",
            "blocking_issue_f1",
            "missing_evidence_f1",
        ):
            _validate_unit_metric(row.get(field), f"score breakdown {field}")

    if (
        parsed_ids != score_ids
        or parsed_ids != breakdown_ids
        or len(parsed_ids) != len(set(parsed_ids))
    ):
        raise ValueError("transaction turn ledgers must have exact matching identities")

    attempts: list[int] = []
    for item in payload["errors"]:
        row = _require_exact_row_keys(item, _ERROR_FIELDS, "error row")
        _validate_nested_identity(row, raw, include_turn=False)
        for field in ("model", "public_case_sha256", "prompt_sha256", "code_commit"):
            if row.get(field) != raw.get(field):
                raise ValueError("nested transaction identity mismatch")
        attempt = row.get("attempt")
        if type(attempt) is not int or attempt <= 0:
            raise ValueError("transaction error attempt is invalid")
        if not isinstance(row.get("error"), str) or not str(row["error"]).strip():
            raise ValueError("transaction error message is invalid")
        attempts.append(attempt)
    if attempts != list(range(1, len(attempts) + 1)):
        raise ValueError("transaction error attempts must be contiguous from one")

    result = raw.get("result")
    raw_agent_turns = _validate_raw_result(result, raw)
    if tuple(parsed_turn_refs) != raw_agent_turns:
        raise ValueError("transaction turn ledgers do not match raw agent turns")
    final_error = result.get("error")
    status = checkpoint.get("status")
    if status == "completed":
        if final_error not in {None, ""}:
            raise ValueError("completed transaction cannot contain a final error")
    else:
        if not isinstance(final_error, str) or not final_error.strip():
            raise ValueError("error transaction requires a final error")
        if not payload["errors"] or payload["errors"][-1]["error"] != final_error:
            raise ValueError("error transaction must bind its final error")


def _validate_transaction(
    payload: Any,
    *,
    expected_resume_key: str | None = None,
) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("run transaction must be an object")
    if payload.get("schema_version") != RUN_TRANSACTION_SCHEMA:
        raise ValueError("unsupported run transaction schema")
    if set(payload) != _TRANSACTION_KEYS:
        raise ValueError("run transaction must contain exact v1 keys")
    identity = str(payload.get("resume_identity_sha256") or "")
    raw = payload.get("raw")
    checkpoint = payload.get("checkpoint")
    if not isinstance(raw, Mapping) or not isinstance(checkpoint, Mapping):
        raise ValueError("run transaction raw and checkpoint must be objects")
    raw_key = str(raw.get("resume_key") or "")
    checkpoint_key = str(checkpoint.get("resume_key") or "")
    if (
        len(identity) != 64
        or identity != raw_key
        or identity != checkpoint_key
        or (expected_resume_key is not None and identity != expected_resume_key)
    ):
        raise ValueError("run transaction identity mismatch")
    canonical_identity = {field: raw.get(field) for field in _RESUME_IDENTITY_FIELDS}
    if sha256_json(canonical_identity) != identity:
        raise ValueError("canonical transaction identity mismatch")
    _require_exact_row_keys(raw, _RAW_KEYS, "raw transaction")
    _validate_outer_resume_identity(raw, identity)
    _require_exact_row_keys(checkpoint, _CHECKPOINT_KEYS, "checkpoint")
    if checkpoint.get("status") not in {"completed", "error"}:
        raise ValueError("run transaction checkpoint status is invalid")
    for key in ("parsed", "scores", "score_breakdowns", "errors"):
        if not isinstance(payload.get(key), list):
            raise ValueError(f"run transaction {key} must be a list")
    _validate_persisted_rows(payload, raw, checkpoint)
    return payload


def _score_identities(rows: Sequence[Mapping[str, Any]]) -> list[tuple[str, ...]]:
    return sorted(
        tuple(str(row.get(field, "")) for field in _SCORE_IDENTITY_FIELDS)
        for row in rows
    )


def load_validated_transactions(
    output_dir: Path,
) -> tuple[Mapping[str, Any], ...]:
    """Read and validate per-run transactions without materializing ledgers."""

    rows: list[Mapping[str, Any]] = []
    with AuthenticatedTree(output_dir, label="run output root") as tree:
        output_entries = tree.list_directory(None, label="run output root")
        transaction_entry = next(
            (entry for entry in output_entries if entry.name == "run_transactions"),
            None,
        )
        if transaction_entry is not None and transaction_entry.is_directory:
            paths = tuple(
                entry
                for entry in tree.list_directory(
                    "run_transactions",
                    label="run transaction directory",
                )
                if not entry.is_directory and entry.name.endswith(".json")
            )
            for path in paths:
                artifact = tree.read_bytes(
                    Path("run_transactions") / path.name,
                    label=f"run transaction {path.name}",
                )
                payload = json.loads(artifact.decode("utf-8"))
                rows.append(
                    _validate_transaction(
                        payload,
                        expected_resume_key=Path(path.name).stem,
                    )
                )
    return tuple(rows)


def _materialize_transactions(output_dir: Path) -> list[Mapping[str, Any]]:
    """Atomically rebuild all derived ledgers from per-run transactions."""

    transactions = list(load_validated_transactions(output_dir))

    raw_rows = [transaction["raw"] for transaction in transactions]
    parsed_rows = [
        row for transaction in transactions for row in transaction.get("parsed", ())
    ]
    score_rows = [
        row for transaction in transactions for row in transaction.get("scores", ())
    ]
    breakdown_rows = [
        row
        for transaction in transactions
        for row in transaction.get("score_breakdowns", ())
    ]
    if _score_identities(score_rows) != _score_identities(breakdown_rows):
        raise ValueError("score and breakdown ledgers must have matching identities")
    error_rows: list[Mapping[str, Any]] = []
    for transaction in transactions:
        errors = transaction.get("errors")
        if isinstance(errors, list):
            error_rows.extend(row for row in errors if isinstance(row, Mapping))
    checkpoints = [transaction["checkpoint"] for transaction in transactions]
    write_jsonl_atomic(output_dir / "raw_trajectories.jsonl", raw_rows)
    write_jsonl_atomic(output_dir / "parsed_turn_states.jsonl", parsed_rows)
    write_csv_atomic(
        output_dir / "turn_scores.csv",
        score_rows,
        fieldnames=_SCORE_FIELDS,
    )
    write_csv_atomic(
        output_dir / "turn_score_breakdown.csv",
        breakdown_rows,
        fieldnames=_BREAKDOWN_FIELDS,
    )
    write_jsonl_atomic(output_dir / "errors_retries.jsonl", error_rows)
    write_jsonl_atomic(output_dir / "checkpoint.jsonl", checkpoints)
    return transactions


async def execute_run_plans(
    *,
    plans: Sequence[RunPlan],
    packets_by_case: Mapping[str, ArchitectureEvidencePacket],
    gold_by_case: Mapping[str, ArchitectureGoldRecord],
    output_dir: Path,
    team_builder: Callable[[str, str, tuple[str, ...]], Any],
    run_single: Callable[..., Awaitable[Any]],
    max_attempts: int = 3,
    enforce_pilot_protocol: bool = False,
) -> ExecutionSummary:
    """Execute pending plans with atomic recovery and bounded retries."""

    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.jsonl"
    _materialize_transactions(output_dir)
    done = _completed_resume_keys(checkpoint_path)
    completed = 0
    skipped = 0
    error_runs = 0
    parsed_states = 0
    successful_parses = 0

    for plan in plans:
        if plan.resume_key in done:
            skipped += 1
            continue
        packet = packets_by_case.get(plan.case_id)
        gold = gold_by_case.get(plan.case_id)
        if packet is None or gold is None:
            raise ValueError(f"packet/gold record missing for case: {plan.case_id}")
        transaction_path = output_dir / "run_transactions" / f"{plan.resume_key}.json"
        prior_errors: list[Mapping[str, Any]] = []
        if transaction_path.is_file():
            transaction = _validate_transaction(
                json.loads(transaction_path.read_text(encoding="utf-8")),
                expected_resume_key=plan.resume_key,
            )
            checkpoint = transaction.get("checkpoint")
            if (
                isinstance(checkpoint, Mapping)
                and checkpoint.get("status") == "completed"
            ):
                _materialize_transactions(output_dir)
                parsed_states += len(transaction["parsed"])
                successful_parses += sum(
                    row.get("parse_complete") is True for row in transaction["parsed"]
                )
                completed += 1
                continue
            prior = transaction.get("errors")
            if isinstance(prior, list):
                prior_errors.extend(row for row in prior if isinstance(row, Mapping))

        result = None
        errors = list(prior_errors)
        for local_attempt in range(1, max_attempts + 1):
            allowed_evidence_ids = tuple(
                sorted(str(item["evidence_id"]) for item in packet.evidence)
            )
            team = team_builder(
                plan.pattern,
                plan.model,
                allowed_evidence_ids,
            )
            try:
                result = await run_single(
                    team=team,
                    task_text=plan.prompt,
                    experiment_id="exp08_architecture",
                    task_id=plan.case_id,
                    pattern=plan.pattern,
                    repeat_index=plan.repeat,
                    turn_content_limit=None,
                    substantive_turns_only=True,
                )
            finally:
                if hasattr(team, "reset"):
                    try:
                        await team.reset()
                    except Exception:
                        pass
            if enforce_pilot_protocol and not result.error:
                protocol_errors = validate_pilot_protocol(
                    pattern=plan.pattern,
                    turns=result.turns,
                    packet=packet,
                    terminated_by=result.terminated_by,
                )
                if protocol_errors:
                    result.error = ";".join(protocol_errors)
            if not result.error:
                break
            errors.append(
                {
                    **plan.to_dict(),
                    "attempt": len(prior_errors) + local_attempt,
                    "error": result.error,
                }
            )
        if result is None:
            raise RuntimeError("run attempt loop produced no result")

        agent_turns = [
            turn for turn in result.turns if str(turn.source).lower() != "user"
        ]
        prefixes = accumulate_prefix_states(
            tuple(
                TurnRecord(author=str(turn.source), content=str(turn.content))
                for turn in agent_turns
            ),
            packet,
        )
        parsed_rows: list[dict[str, Any]] = []
        score_rows: list[dict[str, Any]] = []
        breakdown_rows: list[dict[str, Any]] = []
        for turn, prefix in zip(agent_turns, prefixes):
            score_identity = {
                "resume_key": plan.resume_key,
                "case_id": plan.case_id,
                "pattern": plan.pattern,
                "repeat": plan.repeat,
                "turn_index": int(turn.index),
            }
            parsed_rows.append(
                {
                    **score_identity,
                    "source": str(turn.source),
                    "parse_complete": prefix.parse_complete,
                    "parse_error_codes": list(prefix.parse_error_codes),
                    "state": prefix.state.to_dict(),
                }
            )
            score_rows.append(
                {
                    **score_identity,
                    **asdict(score_prefix(prefix, gold, packet)),
                }
            )
            breakdown_rows.append(
                {
                    **score_identity,
                    **score_prefix_breakdown(prefix, gold, packet),
                }
            )
        final_error = result.error
        persisted_result = asdict(result)
        persisted_result["task_id"] = plan.case_id
        transaction = {
            "schema_version": RUN_TRANSACTION_SCHEMA,
            "resume_identity_sha256": plan.resume_key,
            "raw": {
                **plan.to_dict(),
                "result": persisted_result,
            },
            "parsed": parsed_rows,
            "scores": score_rows,
            "score_breakdowns": breakdown_rows,
            "errors": errors,
            "checkpoint": {
                "resume_key": plan.resume_key,
                "status": "error" if final_error else "completed",
            },
        }
        _validate_transaction(transaction, expected_resume_key=plan.resume_key)
        write_json_atomic(transaction_path, transaction)
        _materialize_transactions(output_dir)
        parsed_states += len(transaction["parsed"])
        successful_parses += sum(
            row.get("parse_complete") is True for row in transaction["parsed"]
        )
        error_runs += int(bool(final_error))
        if not final_error:
            done.add(plan.resume_key)
        completed += 1
    return ExecutionSummary(
        completed_runs=completed,
        skipped_runs=skipped,
        error_runs=error_runs,
        parsed_states=parsed_states,
        successful_parses=successful_parses,
    )


def _jsonl_rows(path: Path) -> list[Mapping[str, Any]]:
    if not path.is_file():
        return []
    rows: list[Mapping[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, Mapping):
            rows.append(payload)
    return rows


def _final_run_key(identity: Mapping[str, Any]) -> str:
    return sha256_json(
        {
            "case_id": identity.get("case_id"),
            "pattern": identity.get("pattern"),
            "repeat": identity.get("repeat"),
        }
    )


def _sorted_final_run_keys(keys: Sequence[str]) -> list[str]:
    return sorted(keys, key=lambda value: value.encode("utf-8"))


def summarize_pilot(
    *,
    output_dir: Path,
    plans: Sequence[RunPlan],
    packets_by_case: Mapping[str, ArchitectureEvidencePacket],
    gold_by_case: Mapping[str, ArchitectureGoldRecord],
    estimated_completion_date: date,
    estimated_total_cost_usd: float | None,
) -> PilotSummary:
    """Summarize persisted artifacts for the independent pilot gate."""

    transactions = _materialize_transactions(output_dir)
    planned_final_run_keys = [_final_run_key(plan.resume_identity) for plan in plans]
    if len(planned_final_run_keys) != len(set(planned_final_run_keys)):
        raise ValueError("pilot summary has a duplicate final-run key")
    transaction_final_run_keys = [
        _final_run_key(transaction["raw"]) for transaction in transactions
    ]
    if len(transaction_final_run_keys) != len(set(transaction_final_run_keys)):
        raise ValueError("pilot summary has a duplicate final-run key")
    planned_final_run_key_set = set(planned_final_run_keys)
    transaction_final_run_key_set = set(transaction_final_run_keys)
    if planned_final_run_key_set - transaction_final_run_key_set:
        raise ValueError("pilot summary has a missing final-run key")
    if transaction_final_run_key_set - planned_final_run_key_set:
        raise ValueError("pilot summary has an unexpected final-run key")
    case_ids = {plan.case_id for plan in plans}
    relevant_gold = [gold_by_case[case_id] for case_id in sorted(case_ids)]
    plan_keys = {plan.resume_key for plan in plans}
    transaction_keys = {
        str(transaction["raw"]["resume_key"]) for transaction in transactions
    }
    if transaction_keys != plan_keys or len(transactions) != len(plan_keys):
        raise ValueError("pilot summary requires the exact transaction set")
    relevant_transactions = [
        transaction
        for transaction in transactions
        if str(transaction["raw"].get("resume_key")) in plan_keys
    ]
    parsed = [
        row for transaction in relevant_transactions for row in transaction["parsed"]
    ]
    transaction_hash, transaction_count = transaction_set_receipt(output_dir)
    final_rows: list[tuple[str, Any, Any, Mapping[str, Any]]] = []
    protocol_valid_runs = 0
    for transaction in relevant_transactions:
        parsed_rows = transaction["parsed"]
        score_rows = transaction["scores"]
        breakdown_rows = transaction["score_breakdowns"]
        raw = transaction["raw"]
        result = raw["result"]
        case_id = str(raw["case_id"])
        packet = packets_by_case.get(case_id)
        if packet is None:
            raise ValueError(f"packet missing for summarized case: {case_id}")
        gold = gold_by_case.get(case_id)
        if gold is None:
            raise ValueError(f"gold record missing for summarized case: {case_id}")
        agent_turn_rows = tuple(
            turn for turn in result["turns"] if str(turn["source"]).lower() != "user"
        )
        prefixes = accumulate_prefix_states(
            tuple(
                TurnRecord(
                    author=str(turn["source"]),
                    content=str(turn["content"]),
                )
                for turn in agent_turn_rows
            ),
            packet,
        )
        if not (
            len(prefixes) == len(parsed_rows) == len(score_rows) == len(breakdown_rows)
        ):
            raise ValueError("persisted ledger semantic mismatch: row count")
        recomputed_rows: list[tuple[Any, Any, Mapping[str, Any]]] = []
        for turn, prefix, parsed_row, score_row, breakdown_row in zip(
            agent_turn_rows,
            prefixes,
            parsed_rows,
            score_rows,
            breakdown_rows,
        ):
            recomputed_score = score_prefix(prefix, gold, packet)
            recomputed_breakdown = score_prefix_breakdown(prefix, gold, packet)
            if (
                parsed_row["source"] != str(turn["source"])
                or parsed_row["parse_complete"] is not prefix.parse_complete
                or parsed_row["parse_error_codes"] != list(prefix.parse_error_codes)
                or parsed_row["state"] != prefix.state.to_dict()
            ):
                raise ValueError("persisted parsed-state semantic mismatch")
            persisted_score = {
                field: score_row[field]
                for field in (
                    "issue_f1",
                    "evidence_f1",
                    "domain_coverage",
                    "verdict_score",
                    "quality",
                )
            }
            if persisted_score != asdict(recomputed_score):
                raise ValueError("persisted score semantic mismatch")
            persisted_breakdown = {
                field: breakdown_row[field]
                for field in (
                    "subject_stage",
                    "decision_score",
                    "blocking_issue_f1",
                    "missing_evidence_f1",
                )
            }
            if persisted_breakdown != recomputed_breakdown:
                raise ValueError("persisted breakdown semantic mismatch")
            recomputed_rows.append((prefix, recomputed_score, recomputed_breakdown))
        if recomputed_rows:
            final_rows.append((_final_run_key(raw), *recomputed_rows[-1]))
        turns = tuple(
            SimpleNamespace(
                source=str(turn["source"]),
                content=str(turn["content"]),
            )
            for turn in result["turns"]
        )
        protocol_errors = validate_pilot_protocol(
            pattern=str(raw["pattern"]),
            turns=turns,
            packet=packet,
            terminated_by=result.get("terminated_by"),
        )
        if (
            transaction["checkpoint"]["status"] == "completed"
            and not result.get("error")
            and not protocol_errors
        ):
            protocol_valid_runs += 1
    final_run_keys = [key for key, _prefix, _score, _breakdown in final_rows]
    if len(final_run_keys) != len(set(final_run_keys)):
        raise ValueError("pilot summary has a duplicate final-run key")
    final_run_key_set = set(final_run_keys)
    if planned_final_run_key_set - final_run_key_set:
        raise ValueError("pilot summary has a missing final-run key")
    if final_run_key_set - planned_final_run_key_set:
        raise ValueError("pilot summary has an unexpected final-run key")
    sorted_final_run_keys = _sorted_final_run_keys(final_run_keys)
    final_run_key_set_sha256 = sha256_json(sorted_final_run_keys)
    scoring_provenance = PilotScoringProvenance(
        schema_version=PILOT_SCORING_PROVENANCE_SCHEMA,
        scorer_sha256=hashlib.sha256(
            read_authenticated_file(
                Path(__file__).with_name("architecture_metrics.py"),
                label="architecture metrics scorer",
            )
        ).hexdigest(),
        final_run_key_set_sha256=final_run_key_set_sha256,
        final_run_key_count=len(final_run_keys),
        unique_final_run_key_count=len(final_run_key_set),
        missing_final_run_key_count=0,
        duplicate_final_run_key_count=0,
        reference_join_count=len(final_rows),
        common_denominator=len(final_rows),
        numerator_key_set_binding_sha256=sha256_json(
            {
                "blocking": final_run_key_set_sha256,
                "decision": final_run_key_set_sha256,
                "missing_evidence": final_run_key_set_sha256,
                "verdict": final_run_key_set_sha256,
            }
        ),
    )
    return PilotSummary(
        planned_runs=len(plans),
        completed_runs=sum(
            transaction["checkpoint"]["status"] == "completed"
            for transaction in relevant_transactions
        ),
        parsed_states=len(parsed),
        successful_parses=sum(row.get("parse_complete") is True for row in parsed),
        final_runs=len(final_rows),
        successful_final_parses=sum(
            prefix.parse_complete for _key, prefix, _score, _breakdown in final_rows
        ),
        correct_final_decisions=sum(
            prefix.parse_complete and breakdown["decision_score"] == 1.0
            for _key, prefix, _score, breakdown in final_rows
        ),
        correct_final_verdicts=sum(
            prefix.parse_complete and score.verdict_score == 1.0
            for _key, prefix, score, _breakdown in final_rows
        ),
        correct_final_blocking=sum(
            prefix.parse_complete and breakdown["blocking_issue_f1"] == 1.0
            for _key, prefix, _score, breakdown in final_rows
        ),
        correct_final_missing_evidence=sum(
            prefix.parse_complete and breakdown["missing_evidence_f1"] == 1.0
            for _key, prefix, _score, breakdown in final_rows
        ),
        protocol_valid_runs=protocol_valid_runs,
        run_errors=sum(
            transaction["checkpoint"]["status"] == "error"
            for transaction in relevant_transactions
        ),
        retried_runs=sum(
            bool(transaction["errors"]) for transaction in relevant_transactions
        ),
        safe_cases=sum(
            record.expected_decision == "STOP_ACCEPT" for record in relevant_gold
        ),
        unsafe_cases=sum(
            record.expected_decision == "STOP_REJECT" for record in relevant_gold
        ),
        continue_cases=sum(
            record.expected_decision == "CONTINUE" for record in relevant_gold
        ),
        fault_families=tuple(
            sorted(
                {
                    record.mutation_family
                    for record in relevant_gold
                    if record.mutation_family
                }
            )
        ),
        estimated_completion_date=estimated_completion_date,
        estimated_total_cost_usd=estimated_total_cost_usd,
        transaction_set_sha256=(
            transaction_hash if transaction_count == len(relevant_transactions) else ""
        ),
        schema_version=PILOT_SUMMARY_V2_SCHEMA,
        scoring_provenance=scoring_provenance,
    )
