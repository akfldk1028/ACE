"""Exact validation and stable identity projection for Exp08 run manifests."""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from datetime import date
from typing import Any

from config import PATTERNS_ALL

from .pilot_gate import ALLOWED_CASE_STAGES


RUN_MANIFEST_SCHEMA = "ace.iclr2027.exp08_run_manifest.v2"
RUN_MANIFEST_V3_SCHEMA = "ace.iclr2027.exp08_run_manifest.v3"
RUN_IDENTITY_FIELDS = (
    "schema_version",
    "input_mode",
    "split",
    "patterns",
    "repeats",
    "model",
    "code_commit",
    "case_count",
    "expected_case_count",
    "planned_run_count",
    "stage_case_counts",
    "decision_case_counts",
    "input_hashes",
    "identity_commitment",
    "registry_core_sha256",
    "split_manifest_sha256",
    "plan_sha256",
)
RUN_V3_IDENTITY_FIELDS = (
    *RUN_IDENTITY_FIELDS,
    "target_roster_sha256",
    "target_roster_receipt_sha256",
    "combined_dev_target_count",
)

_V2_PLANNED_FIELDS = frozenset((*RUN_IDENTITY_FIELDS, "executed"))
_V2_EXECUTED_FIELDS = frozenset(
    (
        *_V2_PLANNED_FIELDS,
        "execution",
        "estimated_cost_per_run_usd",
        "estimated_total_cost_usd",
        "estimated_completion_date",
    )
)
_V3_PLANNED_FIELDS = frozenset((*RUN_V3_IDENTITY_FIELDS, "executed"))
_V3_EXECUTED_FIELDS = frozenset(
    (
        *_V3_PLANNED_FIELDS,
        "execution",
        "estimated_cost_per_run_usd",
        "estimated_total_cost_usd",
        "estimated_completion_date",
    )
)
_EXECUTION_FIELDS = frozenset(
    {
        "completed_runs",
        "skipped_runs",
        "error_runs",
        "parsed_states",
        "successful_parses",
    }
)
_INPUT_MODES = frozenset({"frozen_private_binding", "public_fixture"})
_DECISIONS = frozenset({"CONTINUE", "STOP_ACCEPT", "STOP_REJECT"})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_INPUT_HASH_KEY = re.compile(r"^input:([0-9a-f]{64})$")
_RAW_PNU = re.compile(r"(?<!\d)\d{19}(?!\d)")
_SHA256_VALUE_FIELDS = frozenset(
    {
        "identity_commitment",
        "registry_core_sha256",
        "split_manifest_sha256",
        "plan_sha256",
        "target_roster_sha256",
        "target_roster_receipt_sha256",
    }
)
_FORBIDDEN_PRIVACY_TOKENS = frozenset(
    {"unknown", "condition", "private", "pnu", "gold", "path", "secret", "internal"}
)


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: frozenset[str],
    label: str,
) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} keys are not exact")


def _privacy_tokens(value: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z]+", value)}


def _audit_privacy(value: Any, *, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("run manifest keys must be strings")
            if _privacy_tokens(key) & _FORBIDDEN_PRIVACY_TOKENS:
                raise ValueError("run manifest contains a forbidden privacy token")
            _audit_privacy(item, path=(*path, key))
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _audit_privacy(item, path=(*path, str(index)))
        return
    if not isinstance(value, str):
        return
    if path == ("input_mode",) and value == "frozen_private_binding":
        return
    if _HEX64.fullmatch(value) is not None and (
        (len(path) == 1 and path[0] in _SHA256_VALUE_FIELDS)
        or (len(path) == 2 and path[0] == "input_hashes")
    ):
        return
    if (
        _RAW_PNU.search(value)
        or "/" in value
        or "\\" in value
        or _privacy_tokens(value) & _FORBIDDEN_PRIVACY_TOKENS
    ):
        raise ValueError("run manifest contains private or path-like content")


def _native_positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive native integer")
    return value


def _native_nonnegative_int(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative native integer")
    return value


def _nonnegative_number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return float(value)


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _validate_patterns(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("patterns must be a nonempty list")
    if any(not isinstance(pattern, str) for pattern in value):
        raise ValueError("patterns must contain strings")
    if len(set(value)) != len(value):
        raise ValueError("patterns must be unique")
    if set(value) - set(PATTERNS_ALL):
        raise ValueError("patterns contain an unknown topology")
    return value


def _validate_census(
    value: Any,
    *,
    allowed: frozenset[str],
    case_count: int,
    label: str,
    allow_empty: bool = False,
) -> dict[str, int]:
    if type(value) is not dict or (not value and not allow_empty):
        raise ValueError(f"{label} must be a nonempty object")
    if set(value) - allowed:
        raise ValueError(f"{label} contains an unsupported key")
    for key, count in value.items():
        _native_positive_int(count, f"{label}.{key}")
    if value and sum(value.values()) != case_count:
        raise ValueError(f"{label} must sum to case_count")
    return value


def _validate_input_hashes(value: Any, *, expected_count: int) -> dict[str, str]:
    if type(value) is not dict or len(value) != expected_count:
        raise ValueError("input_hashes cardinality is invalid")
    for key, digest in value.items():
        if not isinstance(key, str) or not isinstance(digest, str):
            raise ValueError("input_hashes must contain strings")
        match = _INPUT_HASH_KEY.fullmatch(key)
        if match is None or match.group(1) != digest:
            raise ValueError("input_hashes must use neutral self-binding keys")
    return value


def _validate_execution(value: Any, *, planned_run_count: int) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("execution metadata must be an object")
    _require_exact_keys(value, _EXECUTION_FIELDS, "execution metadata")
    completed = _native_nonnegative_int(value["completed_runs"], "completed_runs")
    skipped = _native_nonnegative_int(value["skipped_runs"], "skipped_runs")
    errors = _native_nonnegative_int(value["error_runs"], "error_runs")
    parsed = _native_nonnegative_int(value["parsed_states"], "parsed_states")
    successful = _native_nonnegative_int(
        value["successful_parses"],
        "successful_parses",
    )
    if completed + skipped != planned_run_count:
        raise ValueError("execution run counts do not cover the plan")
    if errors > completed:
        raise ValueError("error_runs exceeds completed_runs")
    if successful > parsed:
        raise ValueError("successful_parses exceeds parsed_states")


def validate_run_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an exact v2 or v3 manifest and return an unaliased copy."""

    if not isinstance(payload, Mapping):
        raise ValueError("run manifest must be an object")
    _audit_privacy(payload)
    executed = payload.get("executed")
    if type(executed) is not bool:
        raise ValueError("executed must be a native boolean")
    schema = payload.get("schema_version")
    if schema == RUN_MANIFEST_SCHEMA:
        planned_fields = _V2_PLANNED_FIELDS
        executed_fields = _V2_EXECUTED_FIELDS
    elif schema == RUN_MANIFEST_V3_SCHEMA:
        planned_fields = _V3_PLANNED_FIELDS
        executed_fields = _V3_EXECUTED_FIELDS
    else:
        raise ValueError("unsupported run manifest schema")
    _require_exact_keys(
        payload,
        executed_fields if executed else planned_fields,
        "run manifest",
    )
    input_mode = payload["input_mode"]
    if not isinstance(input_mode, str) or input_mode not in _INPUT_MODES:
        raise ValueError("unsupported run manifest input_mode")
    split = payload["split"]
    if not isinstance(split, str) or split not in {"dev", "test"}:
        raise ValueError("run manifest split must be dev or test")
    patterns = _validate_patterns(payload["patterns"])
    repeats = _native_positive_int(payload["repeats"], "repeats")
    _nonempty_string(payload["model"], "model")
    _nonempty_string(payload["code_commit"], "code_commit")
    case_count = _native_positive_int(payload["case_count"], "case_count")
    expected_case_count = _native_positive_int(
        payload["expected_case_count"],
        "expected_case_count",
    )
    planned_run_count = _native_positive_int(
        payload["planned_run_count"],
        "planned_run_count",
    )
    if case_count > expected_case_count:
        raise ValueError("case_count exceeds expected_case_count")
    if planned_run_count != case_count * len(patterns) * repeats:
        raise ValueError("planned_run_count does not match plan composition")
    _validate_census(
        payload["stage_case_counts"],
        allowed=ALLOWED_CASE_STAGES,
        case_count=case_count,
        label="stage_case_counts",
    )
    _validate_census(
        payload["decision_case_counts"],
        allowed=_DECISIONS,
        case_count=case_count,
        label="decision_case_counts",
        allow_empty=input_mode == "public_fixture",
    )
    if input_mode == "public_fixture" and payload["decision_case_counts"]:
        raise ValueError("public_fixture must not contain a decision census")
    _validate_input_hashes(
        payload["input_hashes"],
        expected_count=2 if input_mode == "public_fixture" else 6,
    )
    _sha256(payload["plan_sha256"], "plan_sha256")
    commitment_fields = (
        "identity_commitment",
        "registry_core_sha256",
        "split_manifest_sha256",
    )
    if input_mode == "public_fixture":
        if any(payload[field] is not None for field in commitment_fields):
            raise ValueError("public_fixture commitments must be null")
    else:
        for field in commitment_fields:
            _sha256(payload[field], field)
    if schema == RUN_MANIFEST_V3_SCHEMA:
        if input_mode != "frozen_private_binding" or split != "dev":
            raise ValueError("v3 run manifest requires frozen private dev input")
        _sha256(payload["target_roster_sha256"], "target_roster_sha256")
        _sha256(
            payload["target_roster_receipt_sha256"],
            "target_roster_receipt_sha256",
        )
        combined_count = _native_positive_int(
            payload["combined_dev_target_count"],
            "combined_dev_target_count",
        )
        if combined_count != 64:
            raise ValueError("combined_dev_target_count must be exactly 64")
    if executed:
        _validate_execution(payload["execution"], planned_run_count=planned_run_count)
        per_run = _nonnegative_number(
            payload["estimated_cost_per_run_usd"],
            "estimated_cost_per_run_usd",
        )
        total = _nonnegative_number(
            payload["estimated_total_cost_usd"],
            "estimated_total_cost_usd",
        )
        if not math.isclose(
            total,
            per_run * planned_run_count,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("estimated total cost does not match the plan")
        completion = payload["estimated_completion_date"]
        if not isinstance(completion, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", completion
        ):
            raise ValueError("estimated_completion_date must be an ISO date")
        try:
            date.fromisoformat(completion)
        except ValueError as exc:
            raise ValueError("estimated_completion_date must be an ISO date") from exc

    canonical = copy.deepcopy(dict(payload))
    for field in ("stage_case_counts", "decision_case_counts", "input_hashes"):
        canonical[field] = dict(sorted(canonical[field].items()))
    if executed:
        canonical["execution"] = {
            field: canonical["execution"][field] for field in sorted(_EXECUTION_FIELDS)
        }
    return canonical


def run_manifest_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact stable identity shared by planned and executed manifests."""

    validated = validate_run_manifest(payload)
    return {
        field: copy.deepcopy(validated[field])
        for field in (
            RUN_V3_IDENTITY_FIELDS
            if validated["schema_version"] == RUN_MANIFEST_V3_SCHEMA
            else RUN_IDENTITY_FIELDS
        )
    }


__all__ = (
    "RUN_IDENTITY_FIELDS",
    "RUN_MANIFEST_SCHEMA",
    "RUN_MANIFEST_V3_SCHEMA",
    "RUN_V3_IDENTITY_FIELDS",
    "run_manifest_identity",
    "validate_run_manifest",
)
