"""Fail-closed, current-state-only Gate 0 inventory."""

from __future__ import annotations

from collections.abc import Mapping
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import date
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
from types import MappingProxyType
from typing import Any

from . import gate0_sources
from .gate0_sources import Gate0RawSourcePaths, _Gate0ValidatedSourcePaths
from .io import canonical_json
from .secure_files import AuthenticatedTree


GATE0_SCHEMA = "ace.iclr2027.obligation_gate0.v1"
GATE0_PUBLICATION_RECEIPT_SCHEMA = (
    "ace.iclr2027.obligation_gate0_publication_receipt.v1"
)
RESERVED_V1_STATUS_VALUES = frozenset({"collection_prerequisites_met"})

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TRANSACTION_NAME = re.compile(r"^run_transactions/[0-9a-f]{64}\.json$")
_INPUT_HASH_KEY = re.compile(r"^input:([0-9a-f]{64})$")
_RAW_PNU = re.compile(r"(?<!\d)\d{19}(?!\d)")
_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_PATTERNS = ("rr3", "sel3", "swm3", "refl3", "debate3")
_ACTIONS = (
    "STOP",
    "SOLO_SYNTHESIS",
    "ASK_LAW",
    "ASK_PARKING",
    "ASK_PROGRAM",
    "ASK_GEOMETRY",
)
_DATASET_FILES = (
    "private/group_assignments.json",
    "private/private_labels.jsonl",
    "runtime/runtime_features.jsonl",
)
_DATASET_BINDINGS = (
    "projection_identity_commitment",
    "snapshot_receipt_sha256",
    "split_manifest_sha256",
    "study_contract_sha256",
    "transaction_set_sha256",
    "vocabulary_sha256",
)
_ARTIFACT_RECEIPT_KEYS = (
    "artifact_sha256",
    "bindings",
    "file_set_sha256",
    "files",
    "row_census",
    "row_census_sha256",
    "schema_version",
)
_SNAPSHOT_BINDINGS = (
    "code_runtime_identity_sha256",
    "message_hashes_sha256",
    "run_plan_identity_sha256",
    "run_plan_sha256",
    "study_contract_sha256",
    "transaction_set_sha256",
)
_SNAPSHOT_ROW_CENSUS_KEYS = (
    "agent_messages",
    "completed_checkpoints",
    "final_parse_complete_states",
    "parse_complete_states",
    "parsed_states",
    "terminal_errors",
    "transactions",
)
_ROW_CENSUS_KEYS = (
    "assignments",
    "prefixes",
    "private_labels",
    "runtime_features",
    "sites",
    "trajectories",
)
_SOURCE_FILE_KEYS = (
    "snapshot_receipt",
    "snapshot_transaction_member_set",
    "pilot_gate",
    "pilot_run_manifest",
    "pilot_run_plan",
    "dataset_manifest",
    "dataset_manifest_member_bindings",
    "development_gate",
)
_ACCESS_AUDIT_KEYS = (
    "held_out_bundle_reads",
    "model_calls",
    "model_refits",
    "transformer_refits",
    "controller_runs",
    "transaction_body_reads",
    "private_group_assignment_reads",
    "private_label_reads",
    "runtime_feature_reads",
    "future_projection_reads",
)

_INVENTORY_NAME = "stage0_inventory.json"
_RECEIPT_NAME = "stage0_inventory.receipt.json"


def _publication_phase_hook(_phase: str) -> None:
    """Testing observer invoked immediately before each publication operation."""


@dataclass(slots=True)
class _PublicationTemp:
    name: str
    handle: Any = None


if os.name == "nt":
    _PUB_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _PUB_NTDLL = ctypes.WinDLL("ntdll")
    _PUB_INVALID_HANDLE = wintypes.HANDLE(-1).value

    _PUB_FILE_READ_DATA = 0x0001
    _PUB_FILE_WRITE_DATA = 0x0002
    _PUB_FILE_LIST_DIRECTORY = 0x0001
    _PUB_FILE_ADD_SUBDIRECTORY = 0x0004
    _PUB_FILE_READ_ATTRIBUTES = 0x0080
    _PUB_DELETE = 0x00010000
    _PUB_SYNCHRONIZE = 0x00100000
    _PUB_SHARE_ALL = 0x00000001 | 0x00000002 | 0x00000004
    _PUB_OPEN_EXISTING = 3
    _PUB_FILE_ATTRIBUTE_NORMAL = 0x00000080
    _PUB_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _PUB_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _PUB_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _PUB_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _PUB_FILE_OPEN = 1
    _PUB_FILE_CREATE = 2
    _PUB_FILE_DIRECTORY_FILE = 0x00000001
    _PUB_FILE_NON_DIRECTORY_FILE = 0x00000040
    _PUB_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    _PUB_FILE_OPEN_REPARSE_POINT = 0x00200000
    _PUB_OBJ_CASE_INSENSITIVE = 0x00000040
    _PUB_FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
    _PUB_FILE_STANDARD_INFO_CLASS = 1
    _PUB_FILE_RENAME_INFO_CLASS = 3
    _PUB_FILE_DISPOSITION_INFO_CLASS = 4

    class _PubUnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )

    class _PubObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(_PubUnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )

    class _PubIoStatusValue(ctypes.Union):
        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))

    class _PubIoStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (("value", _PubIoStatusValue), ("Information", ctypes.c_size_t))

    class _PubFileAttributeTagInfo(ctypes.Structure):
        _fields_ = (("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD))

    class _PubFileStandardInfo(ctypes.Structure):
        _fields_ = (
            ("AllocationSize", ctypes.c_longlong),
            ("EndOfFile", ctypes.c_longlong),
            ("NumberOfLinks", wintypes.DWORD),
            ("DeletePending", wintypes.BOOLEAN),
            ("Directory", wintypes.BOOLEAN),
        )

    class _PubFileDispositionInfo(ctypes.Structure):
        _fields_ = (("DeleteFile", wintypes.BOOLEAN),)

    _PUB_KERNEL32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    _PUB_KERNEL32.CreateFileW.restype = wintypes.HANDLE
    _PUB_KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _PUB_KERNEL32.CloseHandle.restype = wintypes.BOOL
    _PUB_KERNEL32.GetFileInformationByHandleEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _PUB_KERNEL32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    _PUB_KERNEL32.ReadFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    _PUB_KERNEL32.ReadFile.restype = wintypes.BOOL
    _PUB_KERNEL32.WriteFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    _PUB_KERNEL32.WriteFile.restype = wintypes.BOOL
    _PUB_KERNEL32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    _PUB_KERNEL32.FlushFileBuffers.restype = wintypes.BOOL
    _PUB_KERNEL32.SetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _PUB_KERNEL32.SetFileInformationByHandle.restype = wintypes.BOOL
    _PUB_NTDLL.NtCreateFile.argtypes = (
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(_PubObjectAttributes),
        ctypes.POINTER(_PubIoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
    )
    _PUB_NTDLL.NtCreateFile.restype = wintypes.LONG
    _PUB_NTDLL.NtSetInformationFile.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_PubIoStatusBlock),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
    )
    _PUB_NTDLL.NtSetInformationFile.restype = wintypes.LONG
    _PUB_NTDLL.RtlNtStatusToDosError.argtypes = (wintypes.LONG,)
    _PUB_NTDLL.RtlNtStatusToDosError.restype = wintypes.ULONG
_INVENTORY_KEYS = (
    "schema_version",
    "status",
    "acceptance_passed",
    "blockers",
    "access_audit",
    "source_files",
    "development_inventory",
    "branch_coverage",
    "split_readiness",
    "mechanism_readiness",
    "execution_readiness",
    "baseline_readiness",
    "historical_reference",
    "call_budget",
    "receipt_sha256",
)
_PUBLICATION_KEYS = (
    "schema_version",
    "inventory_relative_path",
    "inventory_file_sha256",
    "inventory_self_sha256",
    "source_files_sha256",
    "receipt_sha256",
)
_BLOCKERS = (
    "baseline_executable_specs_unavailable",
    "capability_audit_outcomes_unavailable",
    "capability_packet_separability_unavailable",
    "common_synthesis_isolation_unproven",
    "execution_isolation_precall_spec_unavailable",
    "insufficient_disjoint_sites",
    "minimum_primary_units_not_met",
    "opaque_executor_view_unproven",
    "primary_unit_family_strata_unverified",
    "residual_labels_unavailable",
    "safe_partition_projection_unavailable",
    "standardized_oacs_branches_missing",
)

_RUN_IDENTITY_FIELDS = (
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
_PLANNED_MANIFEST_KEYS = (*_RUN_IDENTITY_FIELDS, "executed")
_EXECUTED_MANIFEST_KEYS = (
    *_PLANNED_MANIFEST_KEYS,
    "execution",
    "estimated_cost_per_run_usd",
    "estimated_total_cost_usd",
    "estimated_completion_date",
)
_EXECUTION_KEYS = (
    "completed_runs",
    "skipped_runs",
    "error_runs",
    "parsed_states",
    "successful_parses",
)
_PLAN_ROW_KEYS = (
    "case_id",
    "pattern",
    "repeat",
    "model",
    "public_case_sha256",
    "prompt_sha256",
    "code_commit",
    "resume_key",
)
_ALLOWED_STAGES = frozenset(
    {
        "execution",
        "selection",
        "materialization",
        "preflight",
        "candidate_floor_context",
    }
)
_DECISIONS = frozenset({"CONTINUE", "STOP_ACCEPT", "STOP_REJECT"})
_SHA256_VALUE_FIELDS = frozenset(
    {
        "identity_commitment",
        "registry_core_sha256",
        "split_manifest_sha256",
        "plan_sha256",
    }
)
_FORBIDDEN_PRIVACY_TOKENS = frozenset(
    {"unknown", "condition", "private", "pnu", "gold", "path", "secret", "internal"}
)


class Gate0Status(str, Enum):
    DATA_COLLECTION_REQUIRED = "data_collection_required"
    DESIGN_INFEASIBLE = "design_infeasible"


@dataclass(frozen=True, slots=True)
class _AuthenticatedCensus:
    site_count: int
    case_count: int
    patterns: tuple[str, ...]
    repeats: int
    historical_runs: int
    prefix_count: int


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _self_hash(payload: Mapping[str, Any]) -> str:
    return _sha256_bytes(canonical_json(payload).encode("utf-8"))


def _require_sha256(value: Any, label: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a nonempty native string")
    return value


def _positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive native integer")
    return value


def _nonnegative_int(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative native integer")
    return value


def _nonnegative_number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return float(value)


def _exact_dict(value: Any, keys: tuple[str, ...], label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ValueError(f"{label} must be a native JSON object")
    if set(value) != set(keys):
        raise ValueError(f"{label} keys are invalid")
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _canonical_json_value(data: bytes, label: str) -> Any:
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{label} is not strict JSON") from error
    try:
        expected = (canonical_json(value) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} is not canonical JSON") from error
    if data != expected:
        raise ValueError(f"{label} canonical bytes mismatch")
    return value


def _canonical_object(data: bytes, label: str) -> dict[str, Any]:
    value = _canonical_json_value(data, label)
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return value


def _canonical_list(data: bytes, label: str) -> list[Any]:
    value = _canonical_json_value(data, label)
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON list")
    return value


def _privacy_tokens(value: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z]+", value)}


def _audit_manifest_privacy(value: Any, *, path: tuple[str, ...] = ()) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("run manifest keys must be strings")
            if _privacy_tokens(key) & _FORBIDDEN_PRIVACY_TOKENS:
                raise ValueError("run manifest contains a forbidden privacy token")
            _audit_manifest_privacy(item, path=(*path, key))
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _audit_manifest_privacy(item, path=(*path, str(index)))
        return
    if type(value) is not str:
        return
    if path == ("input_mode",) and value == "frozen_private_binding":
        return
    if _SHA256.fullmatch(value) is not None and (
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


def _validate_count_map(
    value: Any,
    *,
    allowed: frozenset[str],
    case_count: int,
    label: str,
    allow_empty: bool = False,
) -> dict[str, int]:
    if type(value) is not dict or (not value and not allow_empty):
        raise ValueError(f"{label} must be a native object")
    if any(type(key) is not str for key in value) or set(value) - allowed:
        raise ValueError(f"{label} keys are invalid")
    for key, count in value.items():
        _positive_int(count, f"{label}.{key}")
    if value and sum(value.values()) != case_count:
        raise ValueError(f"{label} must sum to case_count")
    return dict(sorted(value.items()))


def _validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    _audit_manifest_privacy(manifest)
    executed = manifest.get("executed")
    if type(executed) is not bool:
        raise ValueError("executed must be a native boolean")
    _exact_dict(
        manifest,
        _EXECUTED_MANIFEST_KEYS if executed else _PLANNED_MANIFEST_KEYS,
        "run manifest",
    )
    if manifest["schema_version"] != "ace.iclr2027.exp08_run_manifest.v2":
        raise ValueError("unsupported run manifest schema")
    input_mode = manifest["input_mode"]
    if type(input_mode) is not str or input_mode not in {
        "frozen_private_binding",
        "public_fixture",
    }:
        raise ValueError("unsupported run manifest input_mode")
    if type(manifest["split"]) is not str or manifest["split"] not in {"dev", "test"}:
        raise ValueError("run manifest split must be dev or test")
    patterns = manifest["patterns"]
    if (
        type(patterns) is not list
        or tuple(patterns) != _PATTERNS
        or any(type(pattern) is not str for pattern in patterns)
        or len(set(patterns)) != len(patterns)
    ):
        raise ValueError("run manifest patterns contradict Gate0 v1")
    repeats = _positive_int(manifest["repeats"], "repeats")
    model = _require_nonempty_string(manifest["model"], "model")
    code_commit = _require_nonempty_string(manifest["code_commit"], "code_commit")
    case_count = _positive_int(manifest["case_count"], "case_count")
    expected_case_count = _positive_int(
        manifest["expected_case_count"], "expected_case_count"
    )
    planned_run_count = _positive_int(
        manifest["planned_run_count"], "planned_run_count"
    )
    if case_count > expected_case_count:
        raise ValueError("case_count exceeds expected_case_count")
    if planned_run_count != case_count * len(patterns) * repeats:
        raise ValueError("planned_run_count does not match plan composition")
    _validate_count_map(
        manifest["stage_case_counts"],
        allowed=_ALLOWED_STAGES,
        case_count=case_count,
        label="stage_case_counts",
    )
    decision_counts = _validate_count_map(
        manifest["decision_case_counts"],
        allowed=_DECISIONS,
        case_count=case_count,
        label="decision_case_counts",
        allow_empty=input_mode == "public_fixture",
    )
    if input_mode == "public_fixture" and decision_counts:
        raise ValueError("public_fixture decision census must be empty")
    input_hashes = manifest["input_hashes"]
    expected_hash_count = 2 if input_mode == "public_fixture" else 6
    if type(input_hashes) is not dict or len(input_hashes) != expected_hash_count:
        raise ValueError("input_hashes cardinality is invalid")
    for key, digest in input_hashes.items():
        if type(key) is not str or type(digest) is not str:
            raise ValueError("input_hashes must contain native strings")
        match = _INPUT_HASH_KEY.fullmatch(key)
        if match is None or match.group(1) != digest:
            raise ValueError("input_hashes must be neutral self-bindings")
    _require_sha256(manifest["plan_sha256"], "plan_sha256")
    commitments = (
        "identity_commitment",
        "registry_core_sha256",
        "split_manifest_sha256",
    )
    if input_mode == "public_fixture":
        if any(manifest[field] is not None for field in commitments):
            raise ValueError("public_fixture commitments must be null")
    else:
        for field in commitments:
            _require_sha256(manifest[field], field)
    if executed:
        execution = _exact_dict(manifest["execution"], _EXECUTION_KEYS, "execution")
        completed = _nonnegative_int(execution["completed_runs"], "completed_runs")
        skipped = _nonnegative_int(execution["skipped_runs"], "skipped_runs")
        errors = _nonnegative_int(execution["error_runs"], "error_runs")
        parsed = _nonnegative_int(execution["parsed_states"], "parsed_states")
        successful = _nonnegative_int(
            execution["successful_parses"], "successful_parses"
        )
        if completed + skipped != planned_run_count:
            raise ValueError("execution run counts do not cover plan")
        if errors > completed or successful > parsed:
            raise ValueError("execution counts are inconsistent")
        per_run = _nonnegative_number(
            manifest["estimated_cost_per_run_usd"], "estimated_cost_per_run_usd"
        )
        total = _nonnegative_number(
            manifest["estimated_total_cost_usd"], "estimated_total_cost_usd"
        )
        if not math.isclose(
            total,
            per_run * planned_run_count,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("estimated total cost does not match plan")
        completion = manifest["estimated_completion_date"]
        if type(completion) is not str or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", completion
        ) is None:
            raise ValueError("estimated_completion_date must be an ISO date")
        try:
            date.fromisoformat(completion)
        except ValueError as error:
            raise ValueError("estimated_completion_date must be an ISO date") from error
    if (
        case_count != 30
        or repeats != 3
        or planned_run_count != 450
    ):
        raise ValueError("authenticated manifest census contradicts Gate0 v1")
    return {
        "case_count": case_count,
        "patterns": tuple(patterns),
        "repeats": repeats,
        "model": model,
        "code_commit": code_commit,
        "planned_run_count": planned_run_count,
        "plan_sha256": manifest["plan_sha256"],
    }


def _validate_run_plan(
    plan: list[Any],
    *,
    manifest: Mapping[str, Any],
    transaction_names: tuple[str, ...],
) -> None:
    if len(plan) != manifest["planned_run_count"]:
        raise ValueError("run plan length mismatch")
    case_to_public: dict[str, str] = {}
    public_to_case: dict[str, str] = {}
    case_to_prompt: dict[str, str] = {}
    resume_keys: set[str] = set()
    cells: set[tuple[str, str, int]] = set()
    for index, raw_row in enumerate(plan):
        row = _exact_dict(raw_row, _PLAN_ROW_KEYS, f"run plan row {index}")
        case_id = _require_nonempty_string(row["case_id"], "case_id")
        pattern = _require_nonempty_string(row["pattern"], "pattern")
        if pattern not in manifest["patterns"]:
            raise ValueError("run plan pattern is not in manifest")
        repeat = row["repeat"]
        if type(repeat) is not int or repeat not in range(manifest["repeats"]):
            raise ValueError("run plan repeat is invalid")
        model = _require_nonempty_string(row["model"], "row model")
        code_commit = _require_nonempty_string(row["code_commit"], "row code_commit")
        if model != manifest["model"] or code_commit != manifest["code_commit"]:
            raise ValueError("run plan model/code identity mismatch")
        public_case_sha256 = _require_sha256(
            row["public_case_sha256"], "public_case_sha256"
        )
        prompt_sha256 = _require_sha256(row["prompt_sha256"], "prompt_sha256")
        resume_key = _require_sha256(row["resume_key"], "resume_key")
        identity = {
            "case_id": case_id,
            "pattern": pattern,
            "repeat": repeat,
            "model": model,
            "public_case_sha256": public_case_sha256,
            "prompt_sha256": prompt_sha256,
            "code_commit": code_commit,
        }
        if resume_key != _self_hash(identity):
            raise ValueError("run plan resume identity mismatch")
        prior_public = case_to_public.setdefault(case_id, public_case_sha256)
        if prior_public != public_case_sha256:
            raise ValueError("public-case digest changed within case")
        prior_case = public_to_case.setdefault(public_case_sha256, case_id)
        if prior_case != case_id:
            raise ValueError("public-case digest aliases two cases")
        prior_prompt = case_to_prompt.setdefault(case_id, prompt_sha256)
        if prior_prompt != prompt_sha256:
            raise ValueError("prompt digest changed within case")
        if resume_key in resume_keys:
            raise ValueError("duplicate run plan resume key")
        resume_keys.add(resume_key)
        cell = (case_id, pattern, repeat)
        if cell in cells:
            raise ValueError("duplicate run plan Cartesian cell")
        cells.add(cell)
    if len(case_to_public) != manifest["case_count"] or len(public_to_case) != len(
        case_to_public
    ):
        raise ValueError("run plan case/public digest bijection mismatch")
    expected_cells = {
        (case_id, pattern, repeat)
        for case_id in case_to_public
        for pattern in manifest["patterns"]
        for repeat in range(manifest["repeats"])
    }
    if cells != expected_cells:
        raise ValueError("run plan Cartesian product mismatch")
    expected_transactions = tuple(
        sorted(f"run_transactions/{resume_key}.json" for resume_key in resume_keys)
    )
    if transaction_names != expected_transactions:
        raise ValueError("snapshot transaction-name set does not match run plan")


def _validate_dataset_artifact(dataset: dict[str, Any]) -> dict[str, Any]:
    artifact = dataset.get("artifact_receipt")
    artifact = _exact_dict(
        artifact,
        (
            "artifact_sha256",
            "bindings",
            "file_set_sha256",
            "files",
            "row_census",
            "row_census_sha256",
            "schema_version",
        ),
        "dataset artifact receipt",
    )
    if artifact["schema_version"] != "ace.iclr2027.cats_dataset_artifacts.v1":
        raise ValueError("unsupported dataset artifact receipt schema")
    files = _exact_dict(artifact["files"], _DATASET_FILES, "dataset files")
    if tuple(files) != _DATASET_FILES:
        raise ValueError("dataset file map is not byte-sorted")
    for name in _DATASET_FILES:
        _require_sha256(files[name], f"dataset file {name}")
    bindings = _exact_dict(
        artifact["bindings"], _DATASET_BINDINGS, "dataset bindings"
    )
    if tuple(bindings) != _DATASET_BINDINGS:
        raise ValueError("dataset bindings are not byte-sorted")
    for name in _DATASET_BINDINGS:
        _require_sha256(bindings[name], f"dataset binding {name}")
    row_census = _exact_dict(
        artifact["row_census"], _ROW_CENSUS_KEYS, "dataset row census"
    )
    if tuple(row_census) != _ROW_CENSUS_KEYS:
        raise ValueError("dataset row census is not byte-sorted")
    for name in _ROW_CENSUS_KEYS:
        _positive_int(row_census[name], f"row_census.{name}")
    file_set_sha256 = _require_sha256(
        artifact["file_set_sha256"], "file_set_sha256"
    )
    row_census_sha256 = _require_sha256(
        artifact["row_census_sha256"], "row_census_sha256"
    )
    artifact_sha256 = _require_sha256(
        artifact["artifact_sha256"], "artifact_sha256"
    )
    if file_set_sha256 != _self_hash(files):
        raise ValueError("dataset file-set hash mismatch")
    if row_census_sha256 != _self_hash(row_census):
        raise ValueError("dataset row-census hash mismatch")
    artifact_payload = {
        "bindings": bindings,
        "file_set_sha256": file_set_sha256,
        "files": files,
        "row_census": row_census,
        "row_census_sha256": row_census_sha256,
        "schema_version": artifact["schema_version"],
    }
    if artifact_sha256 != _self_hash(artifact_payload):
        raise ValueError("dataset artifact hash mismatch")
    expected_census = {
        "assignments": 450,
        "prefixes": 1524,
        "private_labels": 1524,
        "runtime_features": 1524,
        "sites": 5,
        "trajectories": 450,
    }
    if not _native_equal(row_census, expected_census):
        raise ValueError("dataset row census contradicts Gate0 v1")
    return {
        "file_set_sha256": file_set_sha256,
        "row_census": dict(row_census),
    }


def _immutable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _immutable(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_immutable(item) for item in value)
    return value


def _mutable(value: Any) -> Any:
    if isinstance(value, Gate0Status):
        return value.value
    if isinstance(value, Mapping):
        return {key: _mutable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_mutable(item) for item in value]
    return value


def _native_equal(actual: Any, expected: Any) -> bool:
    if type(expected) is dict:
        return (
            type(actual) is dict
            and set(actual) == set(expected)
            and all(_native_equal(actual[key], expected[key]) for key in expected)
        )
    if type(expected) is list:
        return (
            type(actual) is list
            and len(actual) == len(expected)
            and all(
                _native_equal(actual_item, expected_item)
                for actual_item, expected_item in zip(actual, expected, strict=True)
            )
        )
    if type(actual) is not type(expected):
        return False
    if type(actual) is float and not math.isfinite(actual):
        return False
    return actual == expected


def _access_audit() -> dict[str, int]:
    return {key: 0 for key in _ACCESS_AUDIT_KEYS}


def _derived_components(
    source_files: Mapping[str, str], census: _AuthenticatedCensus
) -> dict[str, Any]:
    required_sites = 8
    required_units = 64
    unit_multiplier = 64
    return {
        "schema_version": GATE0_SCHEMA,
        "status": Gate0Status.DATA_COLLECTION_REQUIRED.value,
        "acceptance_passed": False,
        "blockers": list(_BLOCKERS),
        "access_audit": _access_audit(),
        "source_files": dict(source_files),
        "development_inventory": {
            "full_frozen_development": {
                "site_count": census.site_count,
                "case_count": census.case_count,
                "receipt_declared_historical_runs": census.historical_runs,
                "historical_patterns": list(census.patterns),
                "repeats_per_case_pattern": census.repeats,
                "receipt_declared_prefix_count": census.prefix_count,
            },
            "preserved_development_gate": {
                "safe_projection_available": False,
                "site_count": None,
                "case_count": None,
                "trajectories": None,
                "prefix_count": None,
                "prefix_depth_counts": None,
                "state": "safe_projection_not_declared_in_v1",
            },
            "inferential_unit": "site_case",
            "prefixes_are_independent": False,
            "repeated_trajectories_are_independent": False,
        },
        "branch_coverage": {
            "required_actions": list(_ACTIONS),
            "direct_terminal_cells": {action: 0 for action in _ACTIONS},
            "identical_post_action_synthesis": False,
            "transition_stitching_permitted": False,
            "historical_topologies_are_oacs_actions": False,
        },
        "split_readiness": {
            "required_capability_audit_sites": 3,
            "required_focal_sites": 5,
            "required_disjoint_sites": required_sites,
            "required_primary_units": required_units,
            "required_units_per_site": 8,
            "required_units_per_family_per_site": 2,
            "available_sites": census.site_count,
            "available_cases": census.case_count,
            "site_gap": required_sites - census.site_count,
            "minimum_primary_unit_gap": required_units - census.case_count,
            "verified_eligible_primary_units": None,
            "verified_primary_unit_gap": None,
            "primary_unit_stratification_verified": False,
            "safe_partition_projection_available": False,
            "disjoint_positive_gate_a_possible": False,
            "current_corpus_use": "negative_oriented_smoke_only",
        },
        "mechanism_readiness": {
            "residual_label_receipt_state": "not_declared_in_v1",
            "capability_audit_outcome_receipt_state": "not_declared_in_v1",
            "precall_execution_isolation_spec_state": "not_declared_in_v1",
            "baseline_executable_spec_state": "not_declared_in_v1",
            "residual_label_receipt_available": False,
            "blind_label_metrics_available": False,
            "capability_audit_outcome_receipt_available": False,
            "capability_matrix_frozen_on_disjoint_sites": False,
            "packet_separability_evidenced": False,
            "required_label_thresholds": {
                "macro_f1": 0.8,
                "family_recall": 0.7,
                "ece_max": 0.1,
            },
            "required_packet_thresholds": {
                "unique_best_families_min": 3,
                "posterior_min": 0.8,
                "single_packet_best_max": 0.7,
                "rank_correlation_min": 0.7,
                "stable_advantage_signs": True,
            },
            "status": "not_measured",
        },
        "execution_readiness": {
            "complete_packet_tool_swap_receipt_available": False,
            "precall_execution_isolation_spec_available": False,
            "postrun_branch_conformance_receipts_available": False,
            "opaque_executor_view_proven": False,
            "common_synthesis_isolation_proven": False,
            "reuse_1728_eligible": False,
            "default_future_base_call_budget": 216 * unit_multiplier,
            "collection_status": "data_collection_required",
        },
        "baseline_readiness": {
            name: "specification_missing"
            for name in (
                "cost_aware_routing",
                "rirs",
                "vmao",
                "verimap",
                "equal_information_raw_router",
                "separated_router_stopper",
                "all_specialists",
                "solo",
            )
        },
        "historical_reference": {"fixed_topologies": "historical_reference_only"},
        "call_budget": {
            "gate0_model_calls": 0,
            "current_authorized_calls": 0,
            "factored_terminal_records_per_unit": 16,
            "factored_terminal_records_for_64_units": 16 * unit_multiplier,
            "factored_base_calls_per_unit": 27,
            "factored_base_calls_for_64_units": 27 * unit_multiplier,
            "factorial_terminal_records_per_unit": 144,
            "factorial_terminal_records_for_64_units": 144 * unit_multiplier,
            "factorial_base_calls_per_unit": 216,
            "factorial_base_calls_for_64_units": 216 * unit_multiplier,
            "current_future_plan": "factorial_13824_base_calls",
            "historical_visible_agent_tokens_usable_as_complete_cost": False,
        },
    }


def _validate_source_files(value: Any) -> dict[str, str]:
    result = _exact_dict(value, _SOURCE_FILE_KEYS, "source_files")
    return {key: _require_sha256(result[key], f"source_files.{key}") for key in _SOURCE_FILE_KEYS}


def _census_from_inventory(data: dict[str, Any]) -> _AuthenticatedCensus:
    try:
        full = data["development_inventory"]["full_frozen_development"]
        patterns = full["historical_patterns"]
        if type(patterns) is not list or any(type(item) is not str for item in patterns):
            raise ValueError("inventory historical patterns are invalid")
        census = _AuthenticatedCensus(
            site_count=_positive_int(full["site_count"], "inventory site_count"),
            case_count=_positive_int(full["case_count"], "inventory case_count"),
            patterns=tuple(patterns),
            repeats=_positive_int(full["repeats_per_case_pattern"], "inventory repeats"),
            historical_runs=_positive_int(
                full["receipt_declared_historical_runs"], "inventory historical runs"
            ),
            prefix_count=_positive_int(
                full["receipt_declared_prefix_count"], "inventory prefix count"
            ),
        )
    except (KeyError, TypeError) as error:
        raise ValueError("inventory development census is invalid") from error
    if census != _AuthenticatedCensus(5, 30, _PATTERNS, 3, 450, 1524):
        raise ValueError("inventory census contradicts Gate0 v1")
    return census


def _validate_inventory_payload(payload: Any) -> dict[str, Any]:
    data = _exact_dict(payload, _INVENTORY_KEYS, "Gate0 inventory")
    if data["schema_version"] != GATE0_SCHEMA:
        raise ValueError("unsupported Gate0 inventory schema")
    if data["status"] in RESERVED_V1_STATUS_VALUES:
        raise ValueError("reserved Gate0 status is unavailable in v1")
    if data["status"] != Gate0Status.DATA_COLLECTION_REQUIRED.value:
        raise ValueError("current Gate0 v1 status is invalid")
    if type(data["acceptance_passed"]) is not bool or data["acceptance_passed"]:
        raise ValueError("v1 acceptance must be native false")
    source_files = _validate_source_files(data["source_files"])
    census = _census_from_inventory(data)
    expected = _derived_components(source_files, census)
    for key, expected_value in expected.items():
        if not _native_equal(data[key], expected_value):
            raise ValueError(f"Gate0 inventory derived field mismatch: {key}")
    receipt_sha256 = _require_sha256(data["receipt_sha256"], "inventory receipt_sha256")
    if receipt_sha256 != _self_hash(
        {key: value for key, value in data.items() if key != "receipt_sha256"}
    ):
        raise ValueError("Gate0 inventory self-hash mismatch")
    return data


@dataclass(frozen=True, slots=True)
class Gate0Inventory:
    schema_version: str
    status: Gate0Status
    acceptance_passed: bool
    blockers: tuple[str, ...]
    access_audit: Mapping[str, int]
    source_files: Mapping[str, str]
    development_inventory: Mapping[str, object]
    branch_coverage: Mapping[str, object]
    split_readiness: Mapping[str, object]
    mechanism_readiness: Mapping[str, object]
    execution_readiness: Mapping[str, object]
    baseline_readiness: Mapping[str, str]
    historical_reference: Mapping[str, str]
    call_budget: Mapping[str, int | bool | str]
    receipt_sha256: str

    def __post_init__(self) -> None:
        if type(self.status) is not Gate0Status:
            raise TypeError("status must be an exact Gate0Status")
        payload = self.to_dict()
        _validate_inventory_payload(payload)
        for field in (
            "access_audit",
            "source_files",
            "development_inventory",
            "branch_coverage",
            "split_readiness",
            "mechanism_readiness",
            "execution_readiness",
            "baseline_readiness",
            "historical_reference",
            "call_budget",
        ):
            object.__setattr__(self, field, _immutable(getattr(self, field)))
        object.__setattr__(self, "blockers", tuple(self.blockers))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value if isinstance(self.status, Gate0Status) else self.status,
            "acceptance_passed": self.acceptance_passed,
            "blockers": _mutable(self.blockers),
            "access_audit": _mutable(self.access_audit),
            "source_files": _mutable(self.source_files),
            "development_inventory": _mutable(self.development_inventory),
            "branch_coverage": _mutable(self.branch_coverage),
            "split_readiness": _mutable(self.split_readiness),
            "mechanism_readiness": _mutable(self.mechanism_readiness),
            "execution_readiness": _mutable(self.execution_readiness),
            "baseline_readiness": _mutable(self.baseline_readiness),
            "historical_reference": _mutable(self.historical_reference),
            "call_budget": _mutable(self.call_budget),
            "receipt_sha256": self.receipt_sha256,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Gate0Inventory:
        data = _validate_inventory_payload(payload)
        return cls(
            schema_version=data["schema_version"],
            status=Gate0Status(data["status"]),
            acceptance_passed=data["acceptance_passed"],
            blockers=tuple(data["blockers"]),
            access_audit=data["access_audit"],
            source_files=data["source_files"],
            development_inventory=data["development_inventory"],
            branch_coverage=data["branch_coverage"],
            split_readiness=data["split_readiness"],
            mechanism_readiness=data["mechanism_readiness"],
            execution_readiness=data["execution_readiness"],
            baseline_readiness=data["baseline_readiness"],
            historical_reference=data["historical_reference"],
            call_budget=data["call_budget"],
            receipt_sha256=data["receipt_sha256"],
        )


def _validate_publication_payload(payload: Any) -> dict[str, Any]:
    data = _exact_dict(payload, _PUBLICATION_KEYS, "Gate0 publication receipt")
    if data["schema_version"] != GATE0_PUBLICATION_RECEIPT_SCHEMA:
        raise ValueError("unsupported Gate0 publication receipt schema")
    if data["inventory_relative_path"] != "stage0_inventory.json":
        raise ValueError("publication receipt inventory path is invalid")
    for key in (
        "inventory_file_sha256",
        "inventory_self_sha256",
        "source_files_sha256",
        "receipt_sha256",
    ):
        _require_sha256(data[key], key)
    expected = _self_hash(
        {key: value for key, value in data.items() if key != "receipt_sha256"}
    )
    if data["receipt_sha256"] != expected:
        raise ValueError("publication receipt self-hash mismatch")
    return data


@dataclass(frozen=True, slots=True)
class Gate0PublicationReceipt:
    schema_version: str
    inventory_relative_path: str
    inventory_file_sha256: str
    inventory_self_sha256: str
    source_files_sha256: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        _validate_publication_payload(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "inventory_relative_path": self.inventory_relative_path,
            "inventory_file_sha256": self.inventory_file_sha256,
            "inventory_self_sha256": self.inventory_self_sha256,
            "source_files_sha256": self.source_files_sha256,
            "receipt_sha256": self.receipt_sha256,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Gate0PublicationReceipt:
        data = _validate_publication_payload(payload)
        return cls(**data)


def _read_top_sources(validated: _Gate0ValidatedSourcePaths) -> dict[str, bytes]:
    specs = gate0_sources.GATE0_TOP_SOURCES
    paths = (
        validated.snapshot_receipt,
        validated.pilot_gate,
        validated.dataset_manifest,
        validated.development_gate,
    )
    results: dict[str, bytes] = {}
    with AuthenticatedTree(_SOURCE_ROOT, label="Gate0 source root") as tree:
        for spec, path in zip(specs, paths, strict=True):
            data = tree.read_bytes(str(path), label=f"Gate0 {spec.logical_name}")
            if _sha256_bytes(data) != spec.sha256:
                raise ValueError(f"Gate0 {spec.logical_name} hash mismatch")
            results[spec.logical_name] = data
    return results


def _snapshot_sources(snapshot: dict[str, Any]) -> tuple[dict[str, str], tuple[str, ...]]:
    if snapshot.get("schema_version") != "ace.iclr2027.development_snapshot_receipt.v1":
        raise ValueError("unsupported snapshot receipt schema")
    receipt_sha256 = _require_sha256(
        snapshot.get("receipt_sha256"), "snapshot receipt_sha256"
    )
    if receipt_sha256 != _self_hash(
        {key: value for key, value in snapshot.items() if key != "receipt_sha256"}
    ):
        raise ValueError("snapshot receipt self-hash mismatch")
    receipt = _exact_dict(
        snapshot.get("source_artifact_receipt"),
        _ARTIFACT_RECEIPT_KEYS,
        "snapshot source artifact receipt",
    )
    if receipt["schema_version"] != "ace.iclr2027.development_snapshot_sources.v1":
        raise ValueError("unsupported snapshot source artifact receipt schema")
    files = receipt["files"]
    if type(files) is not dict or any(type(name) is not str for name in files):
        raise ValueError("snapshot source file map is invalid")
    if tuple(files) != tuple(sorted(files)):
        raise ValueError("snapshot source file map is not byte-sorted")
    normalized = {
        name: _require_sha256(digest, f"snapshot digest {name}")
        for name, digest in files.items()
    }
    bindings = _exact_dict(
        receipt["bindings"], _SNAPSHOT_BINDINGS, "snapshot source bindings"
    )
    if tuple(bindings) != _SNAPSHOT_BINDINGS:
        raise ValueError("snapshot source bindings are not byte-sorted")
    for name in _SNAPSHOT_BINDINGS:
        _require_sha256(bindings[name], f"snapshot source binding {name}")
    row_census = _exact_dict(
        receipt["row_census"],
        _SNAPSHOT_ROW_CENSUS_KEYS,
        "snapshot source row census",
    )
    if tuple(row_census) != _SNAPSHOT_ROW_CENSUS_KEYS:
        raise ValueError("snapshot source row census is not byte-sorted")
    for name in _SNAPSHOT_ROW_CENSUS_KEYS:
        _nonnegative_int(row_census[name], f"snapshot source row_census.{name}")
    file_set_sha256 = _require_sha256(
        receipt["file_set_sha256"], "snapshot source file_set_sha256"
    )
    row_census_sha256 = _require_sha256(
        receipt["row_census_sha256"], "snapshot source row_census_sha256"
    )
    artifact_sha256 = _require_sha256(
        receipt["artifact_sha256"], "snapshot source artifact_sha256"
    )
    if file_set_sha256 != _self_hash(normalized):
        raise ValueError("snapshot source file-set hash mismatch")
    if row_census_sha256 != _self_hash(row_census):
        raise ValueError("snapshot source row-census hash mismatch")
    artifact_payload = {
        "bindings": bindings,
        "file_set_sha256": file_set_sha256,
        "files": normalized,
        "row_census": row_census,
        "row_census_sha256": row_census_sha256,
        "schema_version": receipt["schema_version"],
    }
    if artifact_sha256 != _self_hash(artifact_payload):
        raise ValueError("snapshot source artifact hash mismatch")
    required = {"pilot_gate.json", "run_manifest.json", "run_plan.json"}
    transaction_names = tuple(sorted(set(normalized) - required))
    if (
        set(normalized) != required | set(transaction_names)
        or len(transaction_names) != 450
        or any(_TRANSACTION_NAME.fullmatch(name) is None for name in transaction_names)
    ):
        raise ValueError("snapshot declared member set is invalid")
    return normalized, transaction_names


def _read_snapshot_bound_pilot_files(
    snapshot_files: Mapping[str, str],
) -> tuple[bytes, bytes]:
    pilot_spec = gate0_sources.GATE0_TOP_SOURCES[1]
    root = _SOURCE_ROOT / Path(pilot_spec.relative_path).parent
    with AuthenticatedTree(root, label="Gate0 snapshot-bound pilot root") as tree:
        manifest = tree.read_bytes("run_manifest.json", label="Gate0 run manifest")
        plan = tree.read_bytes("run_plan.json", label="Gate0 run plan")
    if (
        _sha256_bytes(manifest) != snapshot_files["run_manifest.json"]
        or _sha256_bytes(plan) != snapshot_files["run_plan.json"]
    ):
        raise ValueError("snapshot-bound pilot member hash mismatch")
    return manifest, plan


def build_gate0_inventory(*, sources: Gate0RawSourcePaths) -> Gate0Inventory:
    """Build the current conservative inventory from authenticated metadata only."""

    validated = gate0_sources.validate_gate0_raw_source_paths(sources)
    top = _read_top_sources(validated)
    snapshot = _canonical_object(top["snapshot_receipt"], "snapshot receipt")
    dataset = _canonical_object(top["dataset_manifest"], "dataset manifest")
    _canonical_object(top["pilot_gate"], "pilot gate")
    _canonical_object(top["development_gate"], "development gate")
    snapshot_files, transaction_names = _snapshot_sources(snapshot)
    if snapshot_files["pilot_gate.json"] != gate0_sources.GATE0_TOP_SOURCES[1].sha256:
        raise ValueError("snapshot parent pilot gate binding mismatch")
    manifest_bytes, plan_bytes = _read_snapshot_bound_pilot_files(snapshot_files)
    manifest = _validate_manifest(_canonical_object(manifest_bytes, "run manifest"))
    plan = _canonical_list(plan_bytes, "run plan")
    _validate_run_plan(plan, manifest=manifest, transaction_names=transaction_names)
    artifact = _validate_dataset_artifact(dataset)
    row_census = artifact["row_census"]
    if not (
        row_census["trajectories"]
        == len(plan)
        == manifest["planned_run_count"]
        == len(transaction_names)
        and row_census["assignments"] == len(plan)
        and row_census["private_labels"]
        == row_census["runtime_features"]
        == row_census["prefixes"]
    ):
        raise ValueError("authenticated source census cross-check mismatch")
    source_map = {
        "snapshot_receipt": gate0_sources.GATE0_TOP_SOURCES[0].sha256,
        "snapshot_transaction_member_set": _self_hash(list(transaction_names)),
        "pilot_gate": gate0_sources.GATE0_TOP_SOURCES[1].sha256,
        "pilot_run_manifest": snapshot_files["run_manifest.json"],
        "pilot_run_plan": snapshot_files["run_plan.json"],
        "dataset_manifest": gate0_sources.GATE0_TOP_SOURCES[2].sha256,
        "dataset_manifest_member_bindings": artifact["file_set_sha256"],
        "development_gate": gate0_sources.GATE0_TOP_SOURCES[3].sha256,
    }
    census = _AuthenticatedCensus(
        site_count=row_census["sites"],
        case_count=manifest["case_count"],
        patterns=manifest["patterns"],
        repeats=manifest["repeats"],
        historical_runs=len(plan),
        prefix_count=row_census["prefixes"],
    )
    payload = _derived_components(source_map, census)
    payload["receipt_sha256"] = _self_hash(payload)
    return Gate0Inventory.from_dict(payload)


def gate0_inventory_file_bytes(inventory: Gate0Inventory) -> bytes:
    if type(inventory) is not Gate0Inventory:
        raise TypeError("inventory must be an exact Gate0Inventory")
    return (canonical_json(inventory.to_dict()) + "\n").encode("utf-8")


def gate0_publication_receipt_file_bytes(receipt: Gate0PublicationReceipt) -> bytes:
    if type(receipt) is not Gate0PublicationReceipt:
        raise TypeError("receipt must be an exact Gate0PublicationReceipt")
    return (canonical_json(receipt.to_dict()) + "\n").encode("utf-8")


def _posix_publication_capabilities_available(
    *,
    dir_fd_support: set[object],
    fd_support: set[object],
    follow_symlinks_support: set[object],
) -> bool:
    required_dir_fd = {os.mkdir, os.open, os.rename, os.stat, os.unlink}
    return (
        required_dir_fd <= dir_fd_support
        and os.listdir in fd_support
        and os.stat in follow_symlinks_support
    )


class _PublicationDirectory:
    """One retained, authenticated output-directory publication capability."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(os.path.abspath(output_dir))
        self.parent_dir = self.output_dir.parent
        if self.output_dir == self.parent_dir:
            raise ValueError("Gate0 output directory cannot be a filesystem root")
        self._parent_tree: AuthenticatedTree | None = None
        self._parent_handle: Any = None
        self._output_handle: Any = None
        self._temporaries: dict[str, _PublicationTemp] = {}

    def __enter__(self) -> _PublicationDirectory:
        if os.name == "nt":
            self._parent_handle = self._win_open_directory(self.parent_dir)
            try:
                self._win_validate_handle(
                    self._parent_handle,
                    expected=self.parent_dir,
                    directory=True,
                    detached=False,
                )
                try:
                    self._output_handle = self._win_open_relative(
                        self._parent_handle,
                        self.output_dir.name,
                        directory=True,
                        create=False,
                        access=_PUB_FILE_LIST_DIRECTORY
                        | _PUB_FILE_READ_ATTRIBUTES
                        | _PUB_SYNCHRONIZE,
                    )
                except FileNotFoundError:
                    _publication_phase_hook("create_output_directory")
                    self._ensure_parent_current()
                    self._output_handle = self._win_open_relative(
                        self._parent_handle,
                        self.output_dir.name,
                        directory=True,
                        create=True,
                        access=_PUB_FILE_LIST_DIRECTORY
                        | _PUB_FILE_READ_ATTRIBUTES
                        | _PUB_SYNCHRONIZE,
                    )
                self._win_validate_handle(
                    self._output_handle,
                    expected=self.output_dir,
                    directory=True,
                    detached=False,
                )
            except BaseException:
                self._win_close(self._output_handle)
                self._output_handle = None
                self._win_close(self._parent_handle)
                self._parent_handle = None
                raise
        else:
            if not _posix_publication_capabilities_available(
                dir_fd_support=os.supports_dir_fd,
                fd_support=os.supports_fd,
                follow_symlinks_support=os.supports_follow_symlinks,
            ):
                raise ValueError("platform lacks handle-relative publication support")
            self._parent_tree = AuthenticatedTree(
                self.parent_dir, label="Gate0 publication parent"
            )
            self._parent_tree.__enter__()
            try:
                self._parent_handle = self._parent_tree._root_handle
                flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
                try:
                    self._output_handle = os.open(
                        self.output_dir.name, flags, dir_fd=self._parent_handle
                    )
                except FileNotFoundError:
                    _publication_phase_hook("create_output_directory")
                    self._ensure_parent_current()
                    os.mkdir(self.output_dir.name, 0o700, dir_fd=self._parent_handle)
                    self._output_handle = os.open(
                        self.output_dir.name, flags, dir_fd=self._parent_handle
                    )
                self._posix_validate_handle(
                    self._output_handle,
                    expected=self.output_dir,
                    directory=True,
                    detached=False,
                )
            except BaseException:
                if self._output_handle is not None:
                    os.close(self._output_handle)
                    self._output_handle = None
                self._parent_tree.__exit__()
                self._parent_tree = None
                self._parent_handle = None
                raise
        try:
            self.ensure_current()
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *_exc: object) -> None:
        for temporary in tuple(self._temporaries.values()):
            self.cleanup_temp(temporary)
        if os.name == "nt":
            self._win_close(self._output_handle)
            self._win_close(self._parent_handle)
        else:
            if self._output_handle is not None:
                os.close(self._output_handle)
            if self._parent_tree is not None:
                self._parent_tree.__exit__()
        self._output_handle = None
        self._parent_handle = None
        self._parent_tree = None

    def ensure_current(self) -> None:
        if self._parent_handle is None or self._output_handle is None:
            raise RuntimeError("Gate0 publication capability is not open")
        self._ensure_parent_current()
        if os.name == "nt":
            self._win_validate_handle(
                self._output_handle,
                expected=self.output_dir,
                directory=True,
                detached=False,
            )
        else:
            self._posix_validate_handle(
                self._output_handle,
                expected=self.output_dir,
                directory=True,
                detached=False,
            )

    def _ensure_parent_current(self) -> None:
        if self._parent_handle is None:
            raise RuntimeError("Gate0 publication parent capability is not open")
        if os.name == "nt":
            self._win_validate_handle(
                self._parent_handle,
                expected=self.parent_dir,
                directory=True,
                detached=False,
            )
        else:
            assert self._parent_tree is not None
            self._parent_tree._validate_handle(
                self._parent_handle,
                expected=self.parent_dir,
                directory=True,
                label="Gate0 publication parent",
            )

    def read_existing_pair(self) -> tuple[bytes, bytes] | None:
        inventory = self._read_optional(_INVENTORY_NAME)
        receipt = self._read_optional(_RECEIPT_NAME)
        if (inventory is None) != (receipt is None):
            raise ValueError("existing Gate0 publication pair is incomplete")
        if inventory is None:
            return None
        assert receipt is not None
        _verify_gate0_pair_bytes(
            inventory,
            receipt,
            expected_receipt_file_sha256=_sha256_bytes(receipt),
        )
        return inventory, receipt

    def write_temp(
        self,
        final_name: str,
        data: bytes,
        *,
        phase: str | None,
        detached: bool = False,
    ) -> _PublicationTemp:
        self._before_operation(phase, detached=detached)
        for _attempt in range(32):
            name = f".{final_name}.{secrets.token_hex(16)}.tmp"
            if os.name == "nt":
                try:
                    handle = self._win_open_relative(
                        self._output_handle,
                        name,
                        directory=False,
                        create=True,
                        access=_PUB_FILE_WRITE_DATA
                        | _PUB_FILE_READ_ATTRIBUTES
                        | _PUB_DELETE
                        | _PUB_SYNCHRONIZE,
                    )
                except FileExistsError:
                    continue
                temporary = _PublicationTemp(name, handle)
                self._temporaries[name] = temporary
                try:
                    self._win_validate_handle(
                        handle,
                        expected=self.output_dir / name,
                        directory=False,
                        detached=detached,
                    )
                    self._win_write(handle, data)
                except BaseException:
                    self.cleanup_temp(temporary)
                    raise
                return temporary
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                handle = os.open(name, flags, 0o600, dir_fd=self._output_handle)
            except FileExistsError:
                continue
            temporary = _PublicationTemp(name, handle)
            self._temporaries[name] = temporary
            try:
                view = memoryview(data)
                while view:
                    written = os.write(handle, view)
                    if written <= 0:
                        raise OSError("Gate0 temporary write made no progress")
                    view = view[written:]
                os.fsync(handle)
            except BaseException:
                os.close(handle)
                temporary.handle = None
                self.cleanup_temp(temporary)
                raise
            return temporary
        raise FileExistsError("cannot allocate a unique Gate0 temporary name")

    def replace(
        self,
        temporary: _PublicationTemp,
        final_name: str,
        *,
        phase: str | None,
        detached: bool = False,
    ) -> None:
        self._before_operation(phase, detached=detached)
        if os.name == "nt":
            handle = temporary.handle
            if handle is None:
                raise RuntimeError("Gate0 temporary handle is closed")
            try:
                self._win_validate_handle(
                    handle,
                    expected=self.output_dir / temporary.name,
                    directory=False,
                    detached=detached,
                )
                self._win_rename(handle, final_name)
                self._win_close(handle)
                temporary.handle = None
            except BaseException:
                raise
        else:
            handle = temporary.handle
            if type(handle) is not int:
                raise RuntimeError("Gate0 temporary handle is closed")
            self._posix_validate_handle(
                handle,
                expected=self.output_dir / temporary.name,
                directory=False,
                detached=detached,
            )
            os.replace(
                temporary.name,
                final_name,
                src_dir_fd=self._output_handle,
                dst_dir_fd=self._output_handle,
            )
            os.fsync(self._output_handle)
            os.close(handle)
            temporary.handle = None
        self._temporaries.pop(temporary.name, None)

    def read_bytes(self, name: str, *, phase: str) -> bytes:
        self._before_operation(phase, detached=False)
        result = self._read_optional(name)
        if result is None:
            raise ValueError(f"Gate0 publication member {name} is missing")
        return result

    def restore_pair(self, prior: tuple[bytes, bytes] | None) -> None:
        _publication_phase_hook("rollback")
        if prior is None:
            try:
                self._delete_relative(_RECEIPT_NAME, detached=True)
                self._delete_relative(_INVENTORY_NAME, detached=True)
            except BaseException:
                self._quarantine_pair()
                raise
            return
        try:
            inventory_temp = self.write_temp(
                _INVENTORY_NAME, prior[0], phase=None, detached=True
            )
            receipt_temp = self.write_temp(
                _RECEIPT_NAME, prior[1], phase=None, detached=True
            )
            self.replace(
                inventory_temp, _INVENTORY_NAME, phase=None, detached=True
            )
            self.replace(receipt_temp, _RECEIPT_NAME, phase=None, detached=True)
        except BaseException:
            self._quarantine_pair()
            raise

    def _quarantine_pair(self) -> None:
        first_error: BaseException | None = None
        for _attempt in range(2):
            for name in (_RECEIPT_NAME, _INVENTORY_NAME):
                try:
                    self._delete_relative(name, detached=True)
                except BaseException as error:
                    if first_error is None:
                        first_error = error
        remaining = tuple(
            name
            for name in (_RECEIPT_NAME, _INVENTORY_NAME)
            if self._read_optional(name, detached=True) is not None
        )
        if remaining:
            raise OSError(f"Gate0 publication quarantine failed: {remaining}") from first_error

    def cleanup_temp(self, temporary: _PublicationTemp) -> None:
        if temporary.name not in self._temporaries:
            return
        try:
            if os.name == "nt":
                first_error: BaseException | None = None
                if temporary.handle is not None:
                    try:
                        self._win_delete_handle(temporary.handle)
                    except BaseException as error:
                        first_error = error
                    finally:
                        self._win_close(temporary.handle)
                        temporary.handle = None
                try:
                    self._delete_relative(temporary.name, detached=True)
                except BaseException as error:
                    if first_error is None:
                        first_error = error
                if first_error is not None:
                    raise first_error
                return
            first_error = None
            if temporary.handle is not None:
                try:
                    owned = os.fstat(temporary.handle)
                    for candidate in os.listdir(self._output_handle):
                        try:
                            observed = os.stat(
                                candidate,
                                dir_fd=self._output_handle,
                                follow_symlinks=False,
                            )
                        except FileNotFoundError:
                            continue
                        if (observed.st_dev, observed.st_ino) == (
                            owned.st_dev,
                            owned.st_ino,
                        ):
                            try:
                                os.unlink(candidate, dir_fd=self._output_handle)
                            except FileNotFoundError:
                                pass
                except BaseException as error:
                    first_error = error
                finally:
                    os.close(temporary.handle)
                    temporary.handle = None
            try:
                self._delete_relative(temporary.name, detached=True)
            except BaseException as error:
                if first_error is None:
                    first_error = error
            if first_error is not None:
                raise first_error
        finally:
            self._temporaries.pop(temporary.name, None)

    def _before_operation(self, phase: str | None, *, detached: bool) -> None:
        if phase is not None:
            _publication_phase_hook(phase)
        if not detached:
            self.ensure_current()

    def _read_optional(self, name: str, *, detached: bool = False) -> bytes | None:
        if os.name == "nt":
            try:
                handle = self._win_open_relative(
                    self._output_handle,
                    name,
                    directory=False,
                    create=False,
                    access=_PUB_FILE_READ_DATA
                    | _PUB_FILE_READ_ATTRIBUTES
                    | _PUB_SYNCHRONIZE,
                )
            except FileNotFoundError:
                return None
            try:
                self._win_validate_handle(
                    handle,
                    expected=self.output_dir / name,
                    directory=False,
                    detached=detached,
                )
                return self._win_read(handle)
            finally:
                self._win_close(handle)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            handle = os.open(name, flags, dir_fd=self._output_handle)
        except FileNotFoundError:
            return None
        try:
            self._posix_validate_handle(
                handle,
                expected=self.output_dir / name,
                directory=False,
                detached=detached,
            )
            chunks: list[bytes] = []
            while True:
                chunk = os.read(handle, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(handle)

    def _delete_relative(self, name: str, *, detached: bool) -> None:
        if os.name == "nt":
            try:
                handle = self._win_open_relative(
                    self._output_handle,
                    name,
                    directory=False,
                    create=False,
                    access=_PUB_FILE_READ_ATTRIBUTES | _PUB_DELETE | _PUB_SYNCHRONIZE,
                )
            except FileNotFoundError:
                return
            try:
                self._win_validate_handle(
                    handle,
                    expected=self.output_dir / name,
                    directory=False,
                    detached=detached,
                )
                self._win_delete_handle(handle)
            finally:
                self._win_close(handle)
            return
        try:
            os.unlink(name, dir_fd=self._output_handle)
            os.fsync(self._output_handle)
        except FileNotFoundError:
            pass

    if os.name == "nt":

        @staticmethod
        def _win_open_directory(path: Path) -> Any:
            handle = _PUB_KERNEL32.CreateFileW(
                str(path),
                _PUB_FILE_LIST_DIRECTORY
                | _PUB_FILE_ADD_SUBDIRECTORY
                | _PUB_FILE_READ_ATTRIBUTES
                | _PUB_SYNCHRONIZE,
                _PUB_SHARE_ALL,
                None,
                _PUB_OPEN_EXISTING,
                _PUB_FILE_FLAG_BACKUP_SEMANTICS | _PUB_FILE_FLAG_OPEN_REPARSE_POINT,
                None,
            )
            if handle == _PUB_INVALID_HANDLE:
                error = ctypes.get_last_error()
                raise ValueError(f"Gate0 publication parent cannot be opened ({error})")
            return handle

        @staticmethod
        def _win_open_relative(
            parent: Any,
            name: str,
            *,
            directory: bool,
            create: bool,
            access: int,
        ) -> Any:
            buffer = ctypes.create_unicode_buffer(name)
            encoded_length = len(name.encode("utf-16-le"))
            unicode_name = _PubUnicodeString(
                encoded_length,
                encoded_length + 2,
                ctypes.cast(buffer, wintypes.LPWSTR),
            )
            attributes = _PubObjectAttributes(
                ctypes.sizeof(_PubObjectAttributes),
                parent,
                ctypes.pointer(unicode_name),
                _PUB_OBJ_CASE_INSENSITIVE,
                None,
                None,
            )
            io_status = _PubIoStatusBlock()
            handle = wintypes.HANDLE()
            options = (
                (_PUB_FILE_DIRECTORY_FILE if directory else _PUB_FILE_NON_DIRECTORY_FILE)
                | _PUB_FILE_SYNCHRONOUS_IO_NONALERT
                | _PUB_FILE_OPEN_REPARSE_POINT
            )
            status = _PUB_NTDLL.NtCreateFile(
                ctypes.byref(handle),
                access,
                ctypes.byref(attributes),
                ctypes.byref(io_status),
                None,
                _PUB_FILE_ATTRIBUTE_DIRECTORY if directory else _PUB_FILE_ATTRIBUTE_NORMAL,
                _PUB_SHARE_ALL,
                _PUB_FILE_CREATE if create else _PUB_FILE_OPEN,
                options,
                None,
                0,
            )
            if status < 0:
                error = int(_PUB_NTDLL.RtlNtStatusToDosError(status))
                if error in {2, 3}:
                    raise FileNotFoundError(error, "relative publication member is missing", name)
                if create and error in {80, 183}:
                    raise FileExistsError(error, "relative publication member exists", name)
                raise OSError(error, "relative Gate0 publication operation failed", name)
            return handle

        @staticmethod
        def _win_validate_handle(
            handle: Any,
            *,
            expected: Path,
            directory: bool,
            detached: bool,
        ) -> None:
            tag = _PubFileAttributeTagInfo()
            if not _PUB_KERNEL32.GetFileInformationByHandleEx(
                handle,
                _PUB_FILE_ATTRIBUTE_TAG_INFO_CLASS,
                ctypes.byref(tag),
                ctypes.sizeof(tag),
            ):
                raise ValueError("Gate0 publication attributes cannot be authenticated")
            if tag.FileAttributes & _PUB_FILE_ATTRIBUTE_REPARSE_POINT or tag.ReparseTag:
                raise ValueError("Gate0 publication contains a reparse point")
            standard = _PubFileStandardInfo()
            if not _PUB_KERNEL32.GetFileInformationByHandleEx(
                handle,
                _PUB_FILE_STANDARD_INFO_CLASS,
                ctypes.byref(standard),
                ctypes.sizeof(standard),
            ):
                raise ValueError("Gate0 publication type cannot be authenticated")
            if bool(standard.Directory) is not directory or standard.DeletePending:
                raise ValueError("Gate0 publication member has an invalid type")
            if not directory and standard.NumberOfLinks != 1:
                raise ValueError("Gate0 publication file link count must be exactly one")
            if not detached:
                AuthenticatedTree._validate_handle(
                    handle,
                    expected=expected,
                    directory=directory,
                    label="Gate0 publication",
                )

        @staticmethod
        def _win_write(handle: Any, data: bytes) -> None:
            offset = 0
            while offset < len(data):
                chunk = data[offset : offset + 1024 * 1024]
                buffer = ctypes.create_string_buffer(chunk)
                written = wintypes.DWORD()
                if not _PUB_KERNEL32.WriteFile(
                    handle,
                    buffer,
                    len(chunk),
                    ctypes.byref(written),
                    None,
                ):
                    raise OSError(ctypes.get_last_error(), "Gate0 temporary write failed")
                if written.value <= 0:
                    raise OSError("Gate0 temporary write made no progress")
                offset += written.value
            if not _PUB_KERNEL32.FlushFileBuffers(handle):
                raise OSError(ctypes.get_last_error(), "Gate0 temporary fsync failed")

        @staticmethod
        def _win_read(handle: Any) -> bytes:
            chunks: list[bytes] = []
            while True:
                buffer = ctypes.create_string_buffer(1024 * 1024)
                count = wintypes.DWORD()
                if not _PUB_KERNEL32.ReadFile(
                    handle,
                    buffer,
                    len(buffer),
                    ctypes.byref(count),
                    None,
                ):
                    raise OSError(ctypes.get_last_error(), "Gate0 publication read failed")
                if count.value == 0:
                    return b"".join(chunks)
                chunks.append(buffer.raw[: count.value])

        def _win_rename(self, handle: Any, final_name: str) -> None:
            encoded = final_name.encode("utf-16-le")
            file_name_offset = 20
            payload = ctypes.create_string_buffer(file_name_offset + len(encoded))
            ctypes.c_ubyte.from_buffer(payload, 0).value = 1
            output_handle_value = getattr(
                self._output_handle, "value", self._output_handle
            )
            ctypes.c_void_p.from_buffer(payload, 8).value = output_handle_value
            wintypes.DWORD.from_buffer(payload, 16).value = len(encoded)
            ctypes.memmove(ctypes.addressof(payload) + file_name_offset, encoded, len(encoded))
            io_status = _PubIoStatusBlock()
            status = _PUB_NTDLL.NtSetInformationFile(
                handle,
                ctypes.byref(io_status),
                ctypes.byref(payload),
                len(payload),
                10,
            )
            if status < 0:
                error = int(_PUB_NTDLL.RtlNtStatusToDosError(status))
                raise OSError(error, "Gate0 atomic replacement failed")

        @staticmethod
        def _win_delete_handle(handle: Any) -> None:
            disposition = _PubFileDispositionInfo(True)
            if not _PUB_KERNEL32.SetFileInformationByHandle(
                handle,
                _PUB_FILE_DISPOSITION_INFO_CLASS,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            ):
                raise OSError(ctypes.get_last_error(), "Gate0 relative deletion failed")

        @staticmethod
        def _win_close(handle: Any) -> None:
            if handle is not None:
                _PUB_KERNEL32.CloseHandle(handle)

    else:

        def _posix_validate_handle(
            self,
            handle: int,
            *,
            expected: Path,
            directory: bool,
            detached: bool,
        ) -> None:
            observed = os.fstat(handle)
            correct_type = (
                stat.S_ISDIR(observed.st_mode)
                if directory
                else stat.S_ISREG(observed.st_mode)
            )
            if not correct_type or (not directory and observed.st_nlink != 1):
                raise ValueError("Gate0 publication member has an invalid type")
            if not detached:
                assert self._parent_tree is not None
                self._parent_tree._validate_handle(
                    handle,
                    expected=expected,
                    directory=directory,
                    label="Gate0 publication",
                )


def _gate0_publication_material(inventory: Gate0Inventory) -> tuple[bytes, bytes]:
    if type(inventory) is not Gate0Inventory:
        raise TypeError("inventory must be an exact Gate0Inventory")
    inventory_bytes = gate0_inventory_file_bytes(inventory)
    receipt_payload = {
        "schema_version": GATE0_PUBLICATION_RECEIPT_SCHEMA,
        "inventory_relative_path": "stage0_inventory.json",
        "inventory_file_sha256": _sha256_bytes(inventory_bytes),
        "inventory_self_sha256": inventory.receipt_sha256,
        "source_files_sha256": _self_hash(inventory.source_files),
    }
    receipt_payload["receipt_sha256"] = _self_hash(receipt_payload)
    receipt = Gate0PublicationReceipt.from_dict(receipt_payload)
    receipt_bytes = gate0_publication_receipt_file_bytes(receipt)
    _verify_gate0_pair_bytes(
        inventory_bytes,
        receipt_bytes,
        expected_receipt_file_sha256=_sha256_bytes(receipt_bytes),
    )
    return inventory_bytes, receipt_bytes


def gate0_expected_publication_receipt_file_sha256(inventory: Gate0Inventory) -> str:
    """Return the trusted receipt-file digest derived before publication."""

    _inventory_bytes, receipt_bytes = _gate0_publication_material(inventory)
    return _sha256_bytes(receipt_bytes)


def publish_gate0_inventory(inventory: Gate0Inventory, *, output_dir: Path) -> Path:
    """Publish a receipt-last pair; the returned path is location-only."""

    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a Path")
    receipt_path = output_dir / _RECEIPT_NAME
    inventory_bytes, receipt_bytes = _gate0_publication_material(inventory)
    with _PublicationDirectory(output_dir) as directory:
        prior = directory.read_existing_pair()
        inventory_temp: _PublicationTemp | None = None
        receipt_temp: _PublicationTemp | None = None
        publication_started = False
        try:
            inventory_temp = directory.write_temp(
                _INVENTORY_NAME,
                inventory_bytes,
                phase="write_inventory_temp",
            )
            receipt_temp = directory.write_temp(
                _RECEIPT_NAME,
                receipt_bytes,
                phase="write_receipt_temp",
            )
            publication_started = True
            directory.replace(
                inventory_temp,
                _INVENTORY_NAME,
                phase="replace_inventory",
            )
            inventory_temp = None
            directory.replace(
                receipt_temp,
                _RECEIPT_NAME,
                phase="replace_receipt",
            )
            receipt_temp = None
            verified_inventory = directory.read_bytes(
                _INVENTORY_NAME, phase="verify_inventory"
            )
            verified_receipt = directory.read_bytes(
                _RECEIPT_NAME, phase="verify_receipt"
            )
            _verify_gate0_pair_bytes(
                verified_inventory,
                verified_receipt,
                expected_receipt_file_sha256=_sha256_bytes(receipt_bytes),
            )
            directory.ensure_current()
        except BaseException as publication_error:
            if publication_started:
                try:
                    directory.restore_pair(prior)
                except BaseException as rollback_error:
                    raise publication_error from rollback_error
            raise
        finally:
            if inventory_temp is not None:
                directory.cleanup_temp(inventory_temp)
            if receipt_temp is not None:
                directory.cleanup_temp(receipt_temp)
    return receipt_path


def _verify_gate0_pair_bytes(
    inventory_bytes: bytes,
    receipt_bytes: bytes,
    *,
    expected_receipt_file_sha256: str,
) -> Gate0Inventory:
    _require_sha256(expected_receipt_file_sha256, "expected receipt file SHA-256")
    if _sha256_bytes(receipt_bytes) != expected_receipt_file_sha256:
        raise ValueError("publication receipt file hash mismatch")
    receipt = Gate0PublicationReceipt.from_dict(
        _canonical_object(receipt_bytes, "publication receipt")
    )
    if receipt.inventory_file_sha256 != _sha256_bytes(inventory_bytes):
        raise ValueError("inventory file hash mismatch")
    inventory = Gate0Inventory.from_dict(_canonical_object(inventory_bytes, "inventory"))
    if receipt.inventory_self_sha256 != inventory.receipt_sha256:
        raise ValueError("inventory self-hash binding mismatch")
    if receipt.source_files_sha256 != _self_hash(inventory.source_files):
        raise ValueError("source map hash mismatch")
    return inventory


def verify_gate0_publication(
    inventory_path: str | Path,
    receipt_path: str | Path,
    *,
    expected_receipt_file_sha256: str,
) -> Gate0Inventory:
    inventory_path = Path(inventory_path)
    receipt_path = Path(receipt_path)
    if (
        inventory_path.name != _INVENTORY_NAME
        or receipt_path.name != _RECEIPT_NAME
        or inventory_path.parent != receipt_path.parent
    ):
        raise ValueError("Gate0 publication paths are invalid")
    with AuthenticatedTree(
        inventory_path.parent, label="Gate0 publication directory"
    ) as tree:
        inventory_bytes = tree.read_bytes(
            _INVENTORY_NAME, label="Gate0 inventory"
        )
        receipt_bytes = tree.read_bytes(
            _RECEIPT_NAME, label="Gate0 publication receipt"
        )
    return _verify_gate0_pair_bytes(
        inventory_bytes,
        receipt_bytes,
        expected_receipt_file_sha256=expected_receipt_file_sha256,
    )


__all__ = (
    "GATE0_PUBLICATION_RECEIPT_SCHEMA",
    "GATE0_SCHEMA",
    "RESERVED_V1_STATUS_VALUES",
    "Gate0Inventory",
    "Gate0PublicationReceipt",
    "Gate0Status",
    "build_gate0_inventory",
    "gate0_expected_publication_receipt_file_sha256",
    "gate0_inventory_file_bytes",
    "gate0_publication_receipt_file_bytes",
    "publish_gate0_inventory",
    "verify_gate0_publication",
)
