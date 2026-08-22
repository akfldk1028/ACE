"""Blind, directly observed branch outcomes for the E2 primary endpoint.

Cost and the continuous interaction are later E2 secondary analyses.  E3 is a
later equal-information consumer; this module records measurements and makes
no E2, E3, safety, power, or policy claim.  Repeats remain nested observations.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, fields
import hashlib
import inspect
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import subprocess
import sys
import tempfile
import types
from typing import Any, Protocol, runtime_checkable


BRANCH_OUTCOME_SCHEMA = "ace.iclr2027.branch_outcome.v1"
TREATMENT_KINDS = ("stop", "solo_synthesis", "capability_packet")
CALL_CLASS_ORDER = ("agent", "selector", "router", "verifier", "synthesis")

_RECEIPT_SCHEMA = "ace.iclr2027.branch_outcome_receipt.v1"
_IMPLEMENTATION_SCHEMA = "ace.iclr2027.evaluation_implementation_spec.v1"
_REFERENCE_SCHEMA = "ace.iclr2027.blind_evaluator_reference.v1"
_WORKER_REQUEST_SCHEMA = "ace.iclr2027.blind_worker_request.v1"
_WORKER_RESPONSE_SCHEMA = "ace.iclr2027.blind_worker_response.v1"
_PHASE4A_EVALUATOR_MODULE = "iclr2027.obligation_outcomes"
_PHASE4A_EVALUATOR_QUALNAME = "_Phase4ASyntheticBlindEvaluator"
_PHASE4A_EVALUATOR_PATH = "iclr2027/obligation_outcomes.py"
_PHASE4A_EVALUATOR_CONTRACT = "b" * 64
_EVALUATOR_CONSTRUCTOR = "zero_arg_stateless"
_WORKER_TIMEOUT_SECONDS = 30.0
_WORKER_KILL_WAIT_SECONDS = 5.0
_MAX_OUTPUT_BYTES = 16 * 1024 * 1024
_MAX_REFERENCE_BYTES = 4 * 1024 * 1024
_MAX_REQUEST_BYTES = 50 * 1024 * 1024
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_WORKER_ERRORS = frozenset(
    {"contract_error", "evaluation_error", "protocol_error", "worker_internal_error"}
)

if os.name == "nt":
    _OUT_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _OUT_NTDLL = ctypes.WinDLL("ntdll")
    _OUT_INVALID_HANDLE = wintypes.HANDLE(-1).value
    _OUT_FILE_READ_DATA = 0x0001
    _OUT_FILE_WRITE_DATA = 0x0002
    _OUT_FILE_LIST_DIRECTORY = 0x0001
    _OUT_FILE_ADD_FILE = 0x0002
    _OUT_FILE_READ_ATTRIBUTES = 0x0080
    _OUT_DELETE = 0x00010000
    _OUT_SYNCHRONIZE = 0x00100000
    _OUT_SHARE_READ_WRITE = 0x00000001 | 0x00000002
    _OUT_SHARE_ALL = _OUT_SHARE_READ_WRITE | 0x00000004
    _OUT_OPEN_EXISTING = 3
    _OUT_FILE_ATTRIBUTE_NORMAL = 0x00000080
    _OUT_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _OUT_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _OUT_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _OUT_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _OUT_FILE_OPEN = 1
    _OUT_FILE_CREATE = 2
    _OUT_FILE_DIRECTORY_FILE = 0x00000001
    _OUT_FILE_NON_DIRECTORY_FILE = 0x00000040
    _OUT_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    _OUT_FILE_OPEN_REPARSE_POINT = 0x00200000
    _OUT_OBJ_CASE_INSENSITIVE = 0x00000040
    _OUT_FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
    _OUT_FILE_STANDARD_INFO_CLASS = 1
    _OUT_FILE_RENAME_INFO_CLASS = 3
    _OUT_FILE_DISPOSITION_INFO_CLASS = 4

    class _OutUnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )

    class _OutObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(_OutUnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )

    class _OutIoStatusValue(ctypes.Union):
        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))

    class _OutIoStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (("value", _OutIoStatusValue), ("Information", ctypes.c_size_t))

    class _OutFileAttributeTagInfo(ctypes.Structure):
        _fields_ = (("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD))

    class _OutFileStandardInfo(ctypes.Structure):
        _fields_ = (
            ("AllocationSize", ctypes.c_longlong),
            ("EndOfFile", ctypes.c_longlong),
            ("NumberOfLinks", wintypes.DWORD),
            ("DeletePending", wintypes.BOOLEAN),
            ("Directory", wintypes.BOOLEAN),
        )

    class _OutFileDispositionInfo(ctypes.Structure):
        _fields_ = (("DeleteFile", wintypes.BOOLEAN),)

    _OUT_KERNEL32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    _OUT_KERNEL32.CreateFileW.restype = wintypes.HANDLE
    _OUT_KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _OUT_KERNEL32.CloseHandle.restype = wintypes.BOOL
    _OUT_KERNEL32.GetFileInformationByHandleEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _OUT_KERNEL32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    _OUT_KERNEL32.GetFinalPathNameByHandleW.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    _OUT_KERNEL32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    _OUT_KERNEL32.ReadFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    _OUT_KERNEL32.ReadFile.restype = wintypes.BOOL
    _OUT_KERNEL32.WriteFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    _OUT_KERNEL32.WriteFile.restype = wintypes.BOOL
    _OUT_KERNEL32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    _OUT_KERNEL32.FlushFileBuffers.restype = wintypes.BOOL
    _OUT_KERNEL32.SetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _OUT_KERNEL32.SetFileInformationByHandle.restype = wintypes.BOOL
    _OUT_NTDLL.NtCreateFile.argtypes = (
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(_OutObjectAttributes),
        ctypes.POINTER(_OutIoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
    )
    _OUT_NTDLL.NtCreateFile.restype = wintypes.LONG
    _OUT_NTDLL.NtSetInformationFile.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_OutIoStatusBlock),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
    )
    _OUT_NTDLL.NtSetInformationFile.restype = wintypes.LONG
    _OUT_NTDLL.RtlNtStatusToDosError.argtypes = (wintypes.LONG,)
    _OUT_NTDLL.RtlNtStatusToDosError.restype = wintypes.ULONG
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_PREFIX = re.compile(r"prefix:[0-9a-f]{64}\Z")
_SLOT = re.compile(r"slot:[0-9a-f]{64}\Z")
_PACKET = re.compile(r"packet:[0-9a-f]{64}\Z")
_ASK_ACTIONS = frozenset(
    {"ASK_LAW", "ASK_PARKING", "ASK_PROGRAM", "ASK_GEOMETRY"}
)
_REFERENCE_KEYS = frozenset(
    {
        "schema_version",
        "assessment_criteria",
        "hidden_assessment_target",
        "content_sha256",
    }
)
_REFERENCE_FORBIDDEN_KEYS = frozenset(
    {
        "action",
        "actual_packet_id",
        "alignment",
        "arm",
        "branch_id",
        "call_count",
        "case_id",
        "cost",
        "latency",
        "opaque_slot_id",
        "packet_id",
        "policy",
        "repeat",
        "repeat_index",
        "seed",
        "site_id",
        "token",
        "tokens",
        "treatment",
        "treatment_kind",
        "usage",
    }
)


class BranchOutcomeContractError(ValueError):
    """Raised when a native value violates the frozen outcome contract."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _exact_dict(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise TypeError(f"{label} must be an exact dict")
    if any(type(key) is not str for key in value):
        raise BranchOutcomeContractError(f"{label} keys must be strings")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise BranchOutcomeContractError(f"{label} must contain exact keys")


def _exact_text(value: Any, field: str, *, forbid_separators: bool = False) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be a native string")
    if not value or value != value.strip():
        raise BranchOutcomeContractError(f"{field} must be nonempty and exact")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise BranchOutcomeContractError(f"{field} must not contain controls")
    if forbid_separators and ("/" in value or "\\" in value):
        raise BranchOutcomeContractError(f"{field} must not contain separators")
    return value


def _enum(value: Any, allowed: tuple[str, ...] | frozenset[str], field: str) -> str:
    result = _exact_text(value, field)
    if result not in allowed:
        raise BranchOutcomeContractError(f"unsupported {field}")
    return result


def _hash(value: Any, field: str) -> str:
    result = _exact_text(value, field)
    if _SHA.fullmatch(result) is None:
        raise BranchOutcomeContractError(f"{field} must be lowercase SHA-256")
    return result


def _optional_hash(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _hash(value, field)


def _prefixed(value: Any, pattern: re.Pattern[str], field: str) -> str:
    result = _exact_text(value, field)
    if pattern.fullmatch(result) is None:
        raise BranchOutcomeContractError(f"invalid {field}")
    return result


def _native_int(value: Any, field: str, *, minimum: int, maximum: int | None = None) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be a native integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise BranchOutcomeContractError(f"{field} is outside its allowed range")
    return value


def _native_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a native boolean")
    return value


def _native_float(
    value: Any,
    field: str,
    *,
    minimum: float,
    maximum: float | None = None,
) -> float:
    if type(value) is not float:
        raise TypeError(f"{field} must be a native float")
    if not math.isfinite(value):
        raise BranchOutcomeContractError(f"{field} must be finite")
    if value < minimum or (maximum is not None and value > maximum):
        raise BranchOutcomeContractError(f"{field} is outside its allowed range")
    return 0.0 if value == 0.0 else value


def _exact_tuple(value: Any, field: str) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    return value


def _json_array(value: Any, field: str) -> list[Any]:
    if type(value) is not list:
        raise TypeError(f"{field} must be an exact list")
    return value


class _PersistedRecord:
    __slots__ = ()

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    def canonical_json(self) -> str:
        return _canonical_bytes(self.to_dict()).decode("utf-8")

    def sha256(self) -> str:
        return _sha256_bytes(self.canonical_json().encode("utf-8"))


@dataclass(frozen=True, slots=True)
class BranchTreatmentKey(_PersistedRecord):
    site_id: str
    case_id: str
    prefix_id: str
    treatment_kind: str
    opaque_slot_id: str | None
    evaluator_action: str
    actual_packet_id: str | None
    repeat_index: int
    seed: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "site_id", _exact_text(self.site_id, "site_id", forbid_separators=True))
        object.__setattr__(self, "case_id", _exact_text(self.case_id, "case_id", forbid_separators=True))
        object.__setattr__(self, "prefix_id", _prefixed(self.prefix_id, _PREFIX, "prefix_id"))
        treatment = _enum(self.treatment_kind, TREATMENT_KINDS, "treatment_kind")
        object.__setattr__(self, "treatment_kind", treatment)
        object.__setattr__(self, "repeat_index", _native_int(self.repeat_index, "repeat_index", minimum=0))
        object.__setattr__(self, "seed", _native_int(self.seed, "seed", minimum=0, maximum=2**63 - 1))
        if treatment == "capability_packet":
            object.__setattr__(self, "opaque_slot_id", _prefixed(self.opaque_slot_id, _SLOT, "opaque_slot_id"))
            object.__setattr__(self, "evaluator_action", _enum(self.evaluator_action, _ASK_ACTIONS, "evaluator_action"))
            object.__setattr__(self, "actual_packet_id", _prefixed(self.actual_packet_id, _PACKET, "actual_packet_id"))
        else:
            if self.opaque_slot_id is not None or self.actual_packet_id is not None:
                raise BranchOutcomeContractError("non-packet treatments cannot bind slot or packet")
            expected = "STOP" if treatment == "stop" else "SOLO_SYNTHESIS"
            action = _exact_text(self.evaluator_action, "evaluator_action")
            object.__setattr__(self, "evaluator_action", action)
            if action != expected:
                raise BranchOutcomeContractError("treatment and evaluator_action disagree")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BranchTreatmentKey:
        data = _exact_dict(payload, "branch treatment key")
        _exact_keys(data, {field.name for field in fields(cls)}, "branch treatment key")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class ObligationClosureOutcome(_PersistedRecord):
    obligation_id: str
    pre_synthesis_closed: bool
    post_synthesis_closed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "obligation_id", _exact_text(self.obligation_id, "obligation_id"))
        object.__setattr__(self, "pre_synthesis_closed", _native_bool(self.pre_synthesis_closed, "pre_synthesis_closed"))
        object.__setattr__(self, "post_synthesis_closed", _native_bool(self.post_synthesis_closed, "post_synthesis_closed"))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ObligationClosureOutcome:
        data = _exact_dict(payload, "obligation closure")
        _exact_keys(data, {field.name for field in fields(cls)}, "obligation closure")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class BlindOutcomeScores(_PersistedRecord):
    pre_synthesis_closure_quality: float
    blind_terminal_closure_quality: float
    blocking_issue_f1: float
    missing_evidence_f1: float
    decision_accuracy: float
    exact_issue_agreement: bool
    unsafe_stop: bool

    def __post_init__(self) -> None:
        for field_name in (
            "pre_synthesis_closure_quality",
            "blind_terminal_closure_quality",
            "blocking_issue_f1",
            "missing_evidence_f1",
            "decision_accuracy",
        ):
            object.__setattr__(self, field_name, _native_float(getattr(self, field_name), field_name, minimum=0.0, maximum=1.0))
        object.__setattr__(self, "exact_issue_agreement", _native_bool(self.exact_issue_agreement, "exact_issue_agreement"))
        object.__setattr__(self, "unsafe_stop", _native_bool(self.unsafe_stop, "unsafe_stop"))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BlindOutcomeScores:
        data = _exact_dict(payload, "blind outcome scores")
        _exact_keys(data, {field.name for field in fields(cls)}, "blind outcome scores")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class CallClassUsage(_PersistedRecord):
    call_class: str
    call_count: int
    failed_retry_count: int
    processed_tokens: int
    latency_seconds: float
    frozen_list_price_cost: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "call_class", _enum(self.call_class, CALL_CLASS_ORDER, "call_class"))
        object.__setattr__(self, "call_count", _native_int(self.call_count, "call_count", minimum=0))
        object.__setattr__(self, "failed_retry_count", _native_int(self.failed_retry_count, "failed_retry_count", minimum=0))
        object.__setattr__(self, "processed_tokens", _native_int(self.processed_tokens, "processed_tokens", minimum=0))
        object.__setattr__(self, "latency_seconds", _native_float(self.latency_seconds, "latency_seconds", minimum=0.0))
        object.__setattr__(self, "frozen_list_price_cost", _native_float(self.frozen_list_price_cost, "frozen_list_price_cost", minimum=0.0))
        if self.failed_retry_count > self.call_count:
            raise BranchOutcomeContractError("failed retries cannot exceed calls")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CallClassUsage:
        data = _exact_dict(payload, "call-class usage")
        _exact_keys(data, {field.name for field in fields(cls)}, "call-class usage")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class CompleteUsageSummary(_PersistedRecord):
    by_call_class: tuple[CallClassUsage, ...]
    usage_ledger_sha256: str

    def __post_init__(self) -> None:
        rows = _exact_tuple(self.by_call_class, "by_call_class")
        if any(type(row) is not CallClassUsage for row in rows):
            raise TypeError("by_call_class must contain exact CallClassUsage rows")
        if tuple(row.call_class for row in rows) != CALL_CLASS_ORDER:
            raise BranchOutcomeContractError("usage rows must contain five ordered call classes")
        object.__setattr__(self, "by_call_class", rows)
        object.__setattr__(self, "usage_ledger_sha256", _hash(self.usage_ledger_sha256, "usage_ledger_sha256"))

    def _totals(self) -> dict[str, int | float]:
        return {
            "call_count": sum(row.call_count for row in self.by_call_class),
            "failed_retry_count": sum(row.failed_retry_count for row in self.by_call_class),
            "processed_tokens": sum(row.processed_tokens for row in self.by_call_class),
            "latency_seconds": math.fsum(row.latency_seconds for row in self.by_call_class),
            "frozen_list_price_cost": math.fsum(row.frozen_list_price_cost for row in self.by_call_class),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CompleteUsageSummary:
        data = _exact_dict(payload, "complete usage summary")
        _exact_keys(data, {"by_call_class", "usage_ledger_sha256", "totals"}, "complete usage summary")
        raw_rows = _json_array(data["by_call_class"], "by_call_class")
        result = cls(tuple(CallClassUsage.from_dict(row) for row in raw_rows), data["usage_ledger_sha256"])
        totals = _exact_dict(data["totals"], "usage totals")
        _exact_keys(totals, set(result._totals()), "usage totals")
        validated_totals = {
            "call_count": _native_int(totals["call_count"], "total call_count", minimum=0),
            "failed_retry_count": _native_int(totals["failed_retry_count"], "total failed_retry_count", minimum=0),
            "processed_tokens": _native_int(totals["processed_tokens"], "total processed_tokens", minimum=0),
            "latency_seconds": _native_float(totals["latency_seconds"], "total latency_seconds", minimum=0.0),
            "frozen_list_price_cost": _native_float(totals["frozen_list_price_cost"], "total frozen_list_price_cost", minimum=0.0),
        }
        if validated_totals != result._totals():
            raise BranchOutcomeContractError("caller-authored usage totals disagree")
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "by_call_class": [row.to_dict() for row in self.by_call_class],
            "usage_ledger_sha256": self.usage_ledger_sha256,
            "totals": self._totals(),
        }


@dataclass(frozen=True, slots=True)
class OutcomeProvenance(_PersistedRecord):
    source_receipt_sha256: str
    branch_transaction_sha256: str
    public_case_sha256: str
    public_state_sha256: str
    prefix_input_sha256: str
    pre_synthesis_output_sha256: str
    terminal_output_sha256: str
    usage_ledger_sha256: str
    evaluator_contract_sha256: str
    evaluator_reference_sha256: str
    catalog_sha256: str | None
    crossover_plan_sha256: str | None
    execution_binding_sha256: str | None
    actual_packet_manifest_sha256: str | None
    assignment_receipt_sha256: str
    evaluation_implementation_spec_sha256: str

    def __post_init__(self) -> None:
        nullable = {
            "catalog_sha256",
            "crossover_plan_sha256",
            "execution_binding_sha256",
            "actual_packet_manifest_sha256",
        }
        for field in fields(self):
            value = getattr(self, field.name)
            validated = _optional_hash(value, field.name) if field.name in nullable else _hash(value, field.name)
            object.__setattr__(self, field.name, validated)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> OutcomeProvenance:
        data = _exact_dict(payload, "outcome provenance")
        _exact_keys(data, {field.name for field in fields(cls)}, "outcome provenance")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


def _logical_path(value: Any, field: str) -> str:
    result = _exact_text(value, field)
    if "\\" in result or result.startswith("/") or re.match(r"^[A-Za-z]:", result):
        raise BranchOutcomeContractError(f"{field} must be repository-relative POSIX")
    parts = result.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise BranchOutcomeContractError(f"{field} has an unsafe component")
    if str(PurePosixPath(result)) != result:
        raise BranchOutcomeContractError(f"{field} is not canonical")
    return result


@dataclass(frozen=True, slots=True, init=False)
class EvaluationImplementationSpec(_PersistedRecord):
    relative_path: str
    external_file_sha256: str
    schema_version: str
    evaluator_module: str
    evaluator_qualname: str
    evaluator_logical_path: str
    evaluator_source_sha256: str
    evaluator_contract_sha256: str
    evaluator_constructor: str
    source_closure_sha256: str
    implementation_sha256s: tuple[tuple[str, str], ...]
    spec_sha256: str

    def __new__(cls) -> EvaluationImplementationSpec:
        raise TypeError("implementation specs are source-created; use only _for_test in Phase 4A tests")

    @classmethod
    def _for_test(
        cls,
        *,
        relative_path: str,
        external_file_sha256: str,
        implementation_sha256s: tuple[tuple[str, str], ...],
    ) -> EvaluationImplementationSpec:
        """Construct a conspicuously non-production synthetic specification."""

        obj = object.__new__(cls)
        relative = _logical_path(relative_path, "relative_path")
        external = _hash(external_file_sha256, "external_file_sha256")
        raw_rows = _exact_tuple(implementation_sha256s, "implementation_sha256s")
        if not raw_rows:
            raise BranchOutcomeContractError("implementation closure must be nonempty")
        rows: list[tuple[str, str]] = []
        for raw in raw_rows:
            pair = _exact_tuple(raw, "implementation member")
            if len(pair) != 2:
                raise BranchOutcomeContractError("implementation member must be a path/hash pair")
            rows.append((_logical_path(pair[0], "implementation path"), _hash(pair[1], "implementation hash")))
        expected_order = sorted(rows, key=lambda row: row[0].encode("utf-8"))
        paths = [row[0] for row in rows]
        if rows != expected_order or len(paths) != len(set(paths)) or len({path.casefold() for path in paths}) != len(paths):
            raise BranchOutcomeContractError("implementation paths must be unique byte-sorted without case collisions")
        frozen_rows = tuple(rows)
        member_map = dict(frozen_rows)
        if _PHASE4A_EVALUATOR_PATH not in member_map:
            raise BranchOutcomeContractError(
                "synthetic implementation closure must bind the exact evaluator source"
            )
        evaluator_source = member_map[_PHASE4A_EVALUATOR_PATH]
        source_closure = _sha256_json([list(row) for row in frozen_rows])
        spec_content = {
            "schema_version": _IMPLEMENTATION_SCHEMA,
            "evaluator_module": _PHASE4A_EVALUATOR_MODULE,
            "evaluator_qualname": _PHASE4A_EVALUATOR_QUALNAME,
            "evaluator_logical_path": _PHASE4A_EVALUATOR_PATH,
            "evaluator_source_sha256": evaluator_source,
            "evaluator_contract_sha256": _PHASE4A_EVALUATOR_CONTRACT,
            "evaluator_constructor": _EVALUATOR_CONSTRUCTOR,
            "source_closure_sha256": source_closure,
            "implementation_sha256s": [list(row) for row in frozen_rows],
        }
        object.__setattr__(obj, "relative_path", relative)
        object.__setattr__(obj, "external_file_sha256", external)
        object.__setattr__(obj, "schema_version", _IMPLEMENTATION_SCHEMA)
        object.__setattr__(obj, "evaluator_module", _PHASE4A_EVALUATOR_MODULE)
        object.__setattr__(obj, "evaluator_qualname", _PHASE4A_EVALUATOR_QUALNAME)
        object.__setattr__(obj, "evaluator_logical_path", _PHASE4A_EVALUATOR_PATH)
        object.__setattr__(obj, "evaluator_source_sha256", evaluator_source)
        object.__setattr__(obj, "evaluator_contract_sha256", _PHASE4A_EVALUATOR_CONTRACT)
        object.__setattr__(obj, "evaluator_constructor", _EVALUATOR_CONSTRUCTOR)
        object.__setattr__(obj, "source_closure_sha256", source_closure)
        object.__setattr__(obj, "implementation_sha256s", frozen_rows)
        object.__setattr__(obj, "spec_sha256", _sha256_json(spec_content))
        return obj

    @property
    def test_only(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "external_file_sha256": self.external_file_sha256,
            "schema_version": self.schema_version,
            "evaluator_module": self.evaluator_module,
            "evaluator_qualname": self.evaluator_qualname,
            "evaluator_logical_path": self.evaluator_logical_path,
            "evaluator_source_sha256": self.evaluator_source_sha256,
            "evaluator_contract_sha256": self.evaluator_contract_sha256,
            "evaluator_constructor": self.evaluator_constructor,
            "source_closure_sha256": self.source_closure_sha256,
            "implementation_sha256s": [list(row) for row in self.implementation_sha256s],
            "spec_sha256": self.spec_sha256,
        }


@dataclass(frozen=True, slots=True)
class BlindEvaluation:
    obligation_closures: tuple[ObligationClosureOutcome, ...]
    scores: BlindOutcomeScores

    def __post_init__(self) -> None:
        closures = _exact_tuple(self.obligation_closures, "obligation_closures")
        if any(type(row) is not ObligationClosureOutcome for row in closures):
            raise TypeError("obligation_closures must contain exact records")
        ids = tuple(row.obligation_id for row in closures)
        if ids != tuple(sorted(ids, key=lambda value: value.encode("utf-8"))) or len(ids) != len(set(ids)):
            raise BranchOutcomeContractError("obligation closures must be unique and canonical")
        if type(self.scores) is not BlindOutcomeScores:
            raise TypeError("scores must be exact BlindOutcomeScores")
        object.__setattr__(self, "obligation_closures", closures)


@runtime_checkable
class BlindBranchEvaluator(Protocol):
    @property
    def contract_sha256(self) -> str: ...

    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> BlindEvaluation: ...


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BranchOutcomeContractError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise BranchOutcomeContractError(f"nonfinite JSON number is forbidden: {value}")


def _validate_json_tree(value: Any) -> None:
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise BranchOutcomeContractError("JSON numbers must be finite")
        return
    if type(value) is list:
        for nested in value:
            _validate_json_tree(nested)
        return
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise BranchOutcomeContractError("JSON object keys must be strings")
        for nested in value.values():
            _validate_json_tree(nested)
        return
    raise BranchOutcomeContractError("JSON contains a non-native value")


def _decode_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    if type(raw) is not bytes:
        raise TypeError(f"{label} must be exact bytes")
    try:
        decoded = raw.decode("utf-8", errors="strict")
        value = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise BranchOutcomeContractError(f"invalid {label} JSON") from error
    result = _exact_dict(value, label)
    _validate_json_tree(result)
    return result


def _assert_reference_safe(value: Any) -> None:
    if type(value) is dict:
        for key, nested in value.items():
            if key.casefold() in _REFERENCE_FORBIDDEN_KEYS:
                raise BranchOutcomeContractError("evaluator reference contains forbidden metadata")
            _assert_reference_safe(nested)
    elif type(value) is list:
        for nested in value:
            _assert_reference_safe(nested)


def _validate_reference(raw: bytes) -> None:
    value = _decode_json_bytes(raw, "evaluator reference")
    _exact_keys(value, set(_REFERENCE_KEYS), "evaluator reference")
    if value["schema_version"] != _REFERENCE_SCHEMA:
        raise BranchOutcomeContractError("unsupported evaluator-reference schema")
    _assert_reference_safe(value["assessment_criteria"])
    _assert_reference_safe(value["hidden_assessment_target"])
    content = {key: value[key] for key in ("schema_version", "assessment_criteria", "hidden_assessment_target")}
    if _hash(value["content_sha256"], "content_sha256") != _sha256_json(content):
        raise BranchOutcomeContractError("evaluator-reference content hash mismatch")
    if _canonical_bytes(value) != raw:
        raise BranchOutcomeContractError("evaluator-reference bytes are noncanonical")


def _validate_packet_provenance(key: BranchTreatmentKey, provenance: OutcomeProvenance) -> None:
    values = (
        provenance.catalog_sha256,
        provenance.crossover_plan_sha256,
        provenance.execution_binding_sha256,
        provenance.actual_packet_manifest_sha256,
    )
    if key.treatment_kind == "capability_packet":
        if any(value is None for value in values):
            raise BranchOutcomeContractError("packet treatment requires all packet provenance")
    elif any(value is not None for value in values):
        raise BranchOutcomeContractError("non-packet treatment forbids packet provenance")


@dataclass(frozen=True, slots=True)
class BranchEvaluationSource:
    key: BranchTreatmentKey
    pre_synthesis_output: bytes
    terminal_output: bytes
    evaluator_reference: bytes
    usage: CompleteUsageSummary
    provenance: OutcomeProvenance
    implementation_spec: EvaluationImplementationSpec

    def __post_init__(self) -> None:
        if type(self.key) is not BranchTreatmentKey:
            raise TypeError("key must be an exact BranchTreatmentKey")
        for field_name in ("pre_synthesis_output", "terminal_output", "evaluator_reference"):
            if type(getattr(self, field_name)) is not bytes:
                raise TypeError(f"{field_name} must be exact bytes")
        if type(self.usage) is not CompleteUsageSummary:
            raise TypeError("usage must be exact CompleteUsageSummary")
        if type(self.provenance) is not OutcomeProvenance:
            raise TypeError("provenance must be exact OutcomeProvenance")
        if type(self.implementation_spec) is not EvaluationImplementationSpec:
            raise TypeError("implementation_spec must be exact EvaluationImplementationSpec")
        if _sha256_bytes(self.pre_synthesis_output) != self.provenance.pre_synthesis_output_sha256:
            raise BranchOutcomeContractError("pre-synthesis output hash mismatch")
        if _sha256_bytes(self.terminal_output) != self.provenance.terminal_output_sha256:
            raise BranchOutcomeContractError("terminal output hash mismatch")
        if _sha256_bytes(self.evaluator_reference) != self.provenance.evaluator_reference_sha256:
            raise BranchOutcomeContractError("evaluator-reference byte hash mismatch")
        _validate_reference(self.evaluator_reference)
        if self.usage.usage_ledger_sha256 != self.provenance.usage_ledger_sha256:
            raise BranchOutcomeContractError("usage ledger binding mismatch")
        if self.implementation_spec.spec_sha256 != self.provenance.evaluation_implementation_spec_sha256:
            raise BranchOutcomeContractError("implementation specification binding mismatch")
        _validate_packet_provenance(self.key, self.provenance)
        if self.key.treatment_kind == "stop" and self.pre_synthesis_output != self.terminal_output:
            raise BranchOutcomeContractError("STOP requires byte-identical stages")


def _outcome_content(
    schema_version: str,
    key: BranchTreatmentKey,
    obligation_closures: tuple[ObligationClosureOutcome, ...],
    scores: BlindOutcomeScores,
    usage: CompleteUsageSummary,
    provenance: OutcomeProvenance,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "key": key.to_dict(),
        "obligation_closures": [row.to_dict() for row in obligation_closures],
        "scores": scores.to_dict(),
        "usage": usage.to_dict(),
        "provenance": provenance.to_dict(),
    }


@dataclass(frozen=True, slots=True)
class BranchOutcome(_PersistedRecord):
    schema_version: str
    key: BranchTreatmentKey
    obligation_closures: tuple[ObligationClosureOutcome, ...]
    scores: BlindOutcomeScores
    usage: CompleteUsageSummary
    provenance: OutcomeProvenance
    outcome_id: str

    def __post_init__(self) -> None:
        schema = _exact_text(self.schema_version, "schema_version")
        object.__setattr__(self, "schema_version", schema)
        if schema != BRANCH_OUTCOME_SCHEMA:
            raise BranchOutcomeContractError("unsupported branch outcome schema")
        if type(self.key) is not BranchTreatmentKey:
            raise TypeError("key must be exact BranchTreatmentKey")
        evaluation = BlindEvaluation(self.obligation_closures, self.scores)
        object.__setattr__(self, "obligation_closures", evaluation.obligation_closures)
        if type(self.usage) is not CompleteUsageSummary:
            raise TypeError("usage must be exact CompleteUsageSummary")
        if type(self.provenance) is not OutcomeProvenance:
            raise TypeError("provenance must be exact OutcomeProvenance")
        if self.usage.usage_ledger_sha256 != self.provenance.usage_ledger_sha256:
            raise BranchOutcomeContractError("outcome usage binding mismatch")
        _validate_packet_provenance(self.key, self.provenance)
        if self.scores.unsafe_stop and self.key.treatment_kind != "stop":
            raise BranchOutcomeContractError("unsafe_stop is descriptive and STOP-only")
        expected = "outcome:" + _sha256_json(_outcome_content(self.schema_version, self.key, self.obligation_closures, self.scores, self.usage, self.provenance))
        if _prefixed(self.outcome_id, re.compile(r"outcome:[0-9a-f]{64}\Z"), "outcome_id") != expected:
            raise BranchOutcomeContractError("stale outcome_id")

    @classmethod
    def _create(
        cls,
        key: BranchTreatmentKey,
        evaluation: BlindEvaluation,
        usage: CompleteUsageSummary,
        provenance: OutcomeProvenance,
    ) -> BranchOutcome:
        content = _outcome_content(BRANCH_OUTCOME_SCHEMA, key, evaluation.obligation_closures, evaluation.scores, usage, provenance)
        return cls(BRANCH_OUTCOME_SCHEMA, key, evaluation.obligation_closures, evaluation.scores, usage, provenance, "outcome:" + _sha256_json(content))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BranchOutcome:
        data = _exact_dict(payload, "branch outcome")
        _exact_keys(data, {field.name for field in fields(cls)}, "branch outcome")
        closures = _json_array(data["obligation_closures"], "obligation_closures")
        return cls(
            schema_version=data["schema_version"],
            key=BranchTreatmentKey.from_dict(data["key"]),
            obligation_closures=tuple(ObligationClosureOutcome.from_dict(row) for row in closures),
            scores=BlindOutcomeScores.from_dict(data["scores"]),
            usage=CompleteUsageSummary.from_dict(data["usage"]),
            provenance=OutcomeProvenance.from_dict(data["provenance"]),
            outcome_id=data["outcome_id"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {**_outcome_content(self.schema_version, self.key, self.obligation_closures, self.scores, self.usage, self.provenance), "outcome_id": self.outcome_id}


def _branch_sort_key(key: BranchTreatmentKey) -> tuple[Any, ...]:
    return (
        key.site_id,
        key.case_id,
        key.prefix_id,
        key.treatment_kind,
        key.opaque_slot_id or "",
        key.actual_packet_id or "",
        key.repeat_index,
        key.seed,
    )


def validate_branch_outcome_table(outcomes: tuple[BranchOutcome, ...]) -> None:
    rows = _exact_tuple(outcomes, "outcomes")
    if not rows:
        raise BranchOutcomeContractError("outcome table must be nonempty")
    if any(type(row) is not BranchOutcome for row in rows):
        raise TypeError("outcomes must contain exact BranchOutcome rows")
    if tuple(_branch_sort_key(row.key) for row in rows) != tuple(sorted((_branch_sort_key(row.key) for row in rows))):
        raise BranchOutcomeContractError("outcome table is not in canonical branch order")
    if len({row.outcome_id for row in rows}) != len(rows):
        raise BranchOutcomeContractError("duplicate outcome_id")
    full_keys = tuple(_branch_sort_key(row.key) for row in rows)
    if len(set(full_keys)) != len(rows):
        raise BranchOutcomeContractError("duplicate full branch key")
    shared_names = (
        "public_case_sha256",
        "public_state_sha256",
        "prefix_input_sha256",
        "evaluator_contract_sha256",
        "evaluator_reference_sha256",
        "assignment_receipt_sha256",
        "evaluation_implementation_spec_sha256",
    )
    groups: dict[tuple[str, str, str], list[BranchOutcome]] = {}
    for row in rows:
        groups.setdefault((row.key.site_id, row.key.case_id, row.key.prefix_id), []).append(row)
    for group in groups.values():
        for name in shared_names:
            if len({getattr(row.provenance, name) for row in group}) != 1:
                raise BranchOutcomeContractError(f"assessment-target {name} mismatch")


class _Phase4ASyntheticBlindEvaluator:
    """The sole reviewed synthetic Phase 4A measurement instrument."""

    __slots__ = ()

    @property
    def contract_sha256(self) -> str:
        return _PHASE4A_EVALUATOR_CONTRACT

    def evaluate(
        self,
        *,
        pre_synthesis_output: bytes,
        terminal_output: bytes,
        evaluator_reference: bytes,
    ) -> BlindEvaluation:
        if not all(
            type(value) is bytes
            for value in (
                pre_synthesis_output,
                terminal_output,
                evaluator_reference,
            )
        ):
            raise BranchOutcomeContractError("synthetic evaluator accepts exact bytes only")
        if terminal_output == b"raise:synthetic-evaluation-error":
            raise RuntimeError("synthetic evaluation failure")
        if not evaluator_reference:
            raise BranchOutcomeContractError("synthetic evaluator requires a reference")
        stopped = pre_synthesis_output == terminal_output
        return BlindEvaluation(
            (
                ObligationClosureOutcome("obligation:a", True, True),
                ObligationClosureOutcome("obligation:b", False, not stopped),
            ),
            BlindOutcomeScores(
                0.5,
                0.5 if stopped else 1.0,
                2.0 / 3.0,
                1.0,
                1.0,
                True,
                stopped,
            ),
        )


_FORBIDDEN_EVALUATOR_NAMES = frozenset(
    {
        "__builtins__",
        "__import__",
        "_exit",
        "callback",
        "cached_outcome",
        "chdir",
        "compile",
        "ctypes",
        "environ",
        "eval",
        "exec",
        "fileno",
        "getcwd",
        "getenv",
        "globals",
        "import_module",
        "locals",
        "open",
        "pathlib",
        "policy",
        "popen",
        "read_bytes",
        "socket",
        "subprocess",
        "treatment",
        "usage",
    }
)
_ALLOWED_EVALUATOR_RECORDS = frozenset(
    {
        BlindEvaluation,
        ObligationClosureOutcome,
        BlindOutcomeScores,
        BranchOutcomeContractError,
    }
)


def _audit_evaluator_function(
    function: types.FunctionType,
    seen: set[int],
) -> None:
    if type(function) is not types.FunctionType:
        raise BranchOutcomeContractError("evaluator methods must be pure Python functions")
    if id(function) in seen:
        return
    seen.add(id(function))
    if function.__closure__ or function.__code__.co_freevars:
        raise BranchOutcomeContractError("evaluator code cannot capture closures")
    if function.__defaults__ not in (None, ()) or function.__kwdefaults__ not in (
        None,
        {},
    ):
        raise BranchOutcomeContractError("evaluator code cannot carry defaults")
    names = set(function.__code__.co_names)
    if names.intersection(_FORBIDDEN_EVALUATOR_NAMES) or any(
        name.startswith("__") for name in names
    ):
        raise BranchOutcomeContractError("evaluator references a forbidden capability")
    for name in names:
        if name not in function.__globals__:
            continue
        value = function.__globals__[name]
        if value is None or type(value) in {str, bytes, bool, int, float}:
            continue
        if type(value) is tuple and all(
            item is None or type(item) in {str, bytes, bool, int, float}
            for item in value
        ):
            continue
        if any(value is allowed for allowed in _ALLOWED_EVALUATOR_RECORDS):
            continue
        if type(value) is types.FunctionType and value.__module__ == function.__module__:
            _audit_evaluator_function(value, seen)
            continue
        raise BranchOutcomeContractError("evaluator references mutable or ambient globals")


def _audit_evaluator_class(evaluator_class: type[Any]) -> None:
    if type(evaluator_class) is not type:
        raise TypeError("evaluator class must have exact type metaclass")
    for name in (
        "__new__",
        "__init__",
        "__getattribute__",
        "__getattr__",
        "__setattr__",
        "__delattr__",
        "__reduce__",
        "__reduce_ex__",
        "__getstate__",
        "__setstate__",
    ):
        if name in evaluator_class.__dict__:
            raise BranchOutcomeContractError("evaluator has custom allocation or state hooks")
    if (
        evaluator_class.__dict__.get("__slots__") != ()
        or evaluator_class.__dictoffset__ != 0
    ):
        raise BranchOutcomeContractError("evaluator must be stateless and slotted")
    descriptor = evaluator_class.__dict__.get("contract_sha256")
    if type(descriptor) is not property or type(descriptor.fget) is not types.FunctionType:
        raise BranchOutcomeContractError("evaluator contract must be an exact property")
    method = evaluator_class.__dict__.get("evaluate")
    if type(method) is not types.FunctionType:
        raise BranchOutcomeContractError("evaluator evaluate must be a pure Python method")
    _audit_evaluator_function(descriptor.fget, set())
    _audit_evaluator_function(method, set())
    signature = inspect.signature(method)
    parameters = tuple(signature.parameters.values())
    if tuple(parameter.name for parameter in parameters) != (
        "self",
        "pre_synthesis_output",
        "terminal_output",
        "evaluator_reference",
    ):
        raise BranchOutcomeContractError("evaluator signature has wrong parameters")
    if parameters[0].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD or any(
        parameter.kind is not inspect.Parameter.KEYWORD_ONLY
        for parameter in parameters[1:]
    ):
        raise BranchOutcomeContractError(
            "evaluator exposes more than three keyword-only payloads"
        )


def _audit_evaluator_class_for_test(evaluator_class: type[Any]) -> None:
    """Exercise the static auditor without launching caller-selected code."""

    _audit_evaluator_class(evaluator_class)
    if evaluator_class is not _Phase4ASyntheticBlindEvaluator:
        raise BranchOutcomeContractError("only the exact Phase 4A fixture is executable")


def _validate_evaluator(
    evaluator: BlindBranchEvaluator,
    implementation_spec: EvaluationImplementationSpec,
) -> None:
    if type(evaluator) is not _Phase4ASyntheticBlindEvaluator:
        raise BranchOutcomeContractError("caller-selected evaluator identity is forbidden")
    if type(implementation_spec) is not EvaluationImplementationSpec:
        raise TypeError("implementation_spec must be exact")
    expected = (
        _PHASE4A_EVALUATOR_MODULE,
        _PHASE4A_EVALUATOR_QUALNAME,
        _PHASE4A_EVALUATOR_PATH,
        _PHASE4A_EVALUATOR_CONTRACT,
        _EVALUATOR_CONSTRUCTOR,
    )
    observed = (
        implementation_spec.evaluator_module,
        implementation_spec.evaluator_qualname,
        implementation_spec.evaluator_logical_path,
        implementation_spec.evaluator_contract_sha256,
        implementation_spec.evaluator_constructor,
    )
    if observed != expected:
        raise BranchOutcomeContractError("synthetic evaluator identity binding mismatch")
    _audit_evaluator_class(type(evaluator))
    source_path = Path(__file__).resolve(strict=True)
    if _sha256_bytes(source_path.read_bytes()) != implementation_spec.evaluator_source_sha256:
        raise BranchOutcomeContractError("evaluator source digest mismatch")


def _wire_evaluation(evaluation: BlindEvaluation) -> dict[str, Any]:
    if type(evaluation) is not BlindEvaluation:
        raise BranchOutcomeContractError("evaluator returned a foreign result")
    return {
        "obligation_closures": [row.to_dict() for row in evaluation.obligation_closures],
        "scores": evaluation.scores.to_dict(),
    }


def _evaluation_from_wire(value: Any) -> BlindEvaluation:
    payload = _exact_dict(value, "worker evaluation")
    _exact_keys(payload, {"obligation_closures", "scores"}, "worker evaluation")
    raw_closures = _json_array(payload["obligation_closures"], "obligation_closures")
    return BlindEvaluation(
        tuple(ObligationClosureOutcome.from_dict(row) for row in raw_closures),
        BlindOutcomeScores.from_dict(payload["scores"]),
    )


def _frame_payload(payload: dict[str, Any], *, maximum: int) -> bytes:
    body = _canonical_bytes(payload)
    if len(body) > maximum:
        raise BranchOutcomeContractError("worker payload exceeds its size limit")
    return len(body).to_bytes(8, "big") + body


def _parse_frame(raw: bytes, *, maximum: int, label: str) -> dict[str, Any]:
    if type(raw) is not bytes:
        raise TypeError(f"{label} frame must be exact bytes")
    if len(raw) < 8:
        raise BranchOutcomeContractError(f"{label} frame ended before its length")
    size = int.from_bytes(raw[:8], "big")
    if size > maximum or len(raw) != 8 + size:
        raise BranchOutcomeContractError(f"{label} frame length mismatch")
    body = raw[8:]
    payload = _decode_json_bytes(body, label)
    if _canonical_bytes(payload) != body:
        raise BranchOutcomeContractError(f"{label} frame is noncanonical")
    return payload


def _strict_b64_decode(value: Any, field: str, maximum: int) -> bytes:
    text = _exact_text(value, field)
    try:
        decoded = base64.b64decode(text, validate=True)
    except (ValueError, TypeError) as error:
        raise BranchOutcomeContractError(f"{field} is not strict base64") from error
    if len(decoded) > maximum or base64.b64encode(decoded).decode("ascii") != text:
        raise BranchOutcomeContractError(f"{field} is noncanonical or oversized")
    return decoded


def _request_frame(source: BranchEvaluationSource) -> tuple[bytes, str]:
    if len(source.pre_synthesis_output) > _MAX_OUTPUT_BYTES or len(
        source.terminal_output
    ) > _MAX_OUTPUT_BYTES:
        raise BranchOutcomeContractError("worker output payload is oversized")
    if len(source.evaluator_reference) > _MAX_REFERENCE_BYTES:
        raise BranchOutcomeContractError("worker reference payload is oversized")
    nonce = secrets.token_bytes(32).hex()
    unsigned = {
        "schema_version": _WORKER_REQUEST_SCHEMA,
        "nonce": nonce,
        "evaluator_contract_sha256": source.provenance.evaluator_contract_sha256,
        "pre_synthesis_output_b64": base64.b64encode(
            source.pre_synthesis_output
        ).decode("ascii"),
        "terminal_output_b64": base64.b64encode(source.terminal_output).decode(
            "ascii"
        ),
        "evaluator_reference_b64": base64.b64encode(
            source.evaluator_reference
        ).decode("ascii"),
    }
    return _frame_payload(
        {**unsigned, "request_sha256": _sha256_json(unsigned)},
        maximum=_MAX_REQUEST_BYTES,
    ), nonce


def _response_frame(
    *,
    nonce: str,
    contract: str,
    worker_pid: int,
    ok: bool,
    evaluation: BlindEvaluation | None,
    error: str | None,
) -> bytes:
    unsigned = {
        "schema_version": _WORKER_RESPONSE_SCHEMA,
        "nonce": nonce,
        "evaluator_contract_sha256": contract,
        "worker_pid": worker_pid,
        "ok": ok,
        "evaluation": None if evaluation is None else _wire_evaluation(evaluation),
        "error": error,
    }
    return _frame_payload(
        {**unsigned, "response_sha256": _sha256_json(unsigned)},
        maximum=_MAX_RESPONSE_BYTES,
    )


def _blind_worker_main(evaluator_qualname: str, evaluator_source_sha256: str) -> None:
    """Run inside the fixed isolated worker; communicate only framed bytes."""

    del evaluator_source_sha256
    request = _parse_frame(
        sys.stdin.buffer.read(_MAX_REQUEST_BYTES + 9),
        maximum=_MAX_REQUEST_BYTES,
        label="worker request",
    )
    _exact_keys(
        request,
        {
            "schema_version",
            "nonce",
            "evaluator_contract_sha256",
            "pre_synthesis_output_b64",
            "terminal_output_b64",
            "evaluator_reference_b64",
            "request_sha256",
        },
        "worker request",
    )
    if request["schema_version"] != _WORKER_REQUEST_SCHEMA:
        raise BranchOutcomeContractError("worker request schema mismatch")
    nonce = _hash(request["nonce"], "worker nonce")
    contract = _hash(
        request["evaluator_contract_sha256"], "worker evaluator contract"
    )
    unsigned = {key: value for key, value in request.items() if key != "request_sha256"}
    if _hash(request["request_sha256"], "request_sha256") != _sha256_json(unsigned):
        raise BranchOutcomeContractError("worker request self-hash mismatch")
    pre = _strict_b64_decode(
        request["pre_synthesis_output_b64"],
        "pre_synthesis_output_b64",
        _MAX_OUTPUT_BYTES,
    )
    terminal = _strict_b64_decode(
        request["terminal_output_b64"],
        "terminal_output_b64",
        _MAX_OUTPUT_BYTES,
    )
    reference = _strict_b64_decode(
        request["evaluator_reference_b64"],
        "evaluator_reference_b64",
        _MAX_REFERENCE_BYTES,
    )
    try:
        evaluator_class = globals()[evaluator_qualname]
        evaluator = evaluator_class()
        if evaluator.contract_sha256 != contract:
            raise BranchOutcomeContractError("worker evaluator contract mismatch")
        evaluation = evaluator.evaluate(
            pre_synthesis_output=pre,
            terminal_output=terminal,
            evaluator_reference=reference,
        )
        response = _response_frame(
            nonce=nonce,
            contract=contract,
            worker_pid=os.getpid(),
            ok=True,
            evaluation=evaluation,
            error=None,
        )
    except BranchOutcomeContractError:
        response = _response_frame(
            nonce=nonce,
            contract=contract,
            worker_pid=os.getpid(),
            ok=False,
            evaluation=None,
            error="contract_error",
        )
    except BaseException:
        response = _response_frame(
            nonce=nonce,
            contract=contract,
            worker_pid=os.getpid(),
            ok=False,
            evaluation=None,
            error="evaluation_error",
        )
    sys.stdout.buffer.write(response)
    sys.stdout.buffer.flush()


_BLIND_WORKER_BOOTSTRAP = r'''
import hashlib
import os
import sys
import types

project_root, module_name, evaluator_qualname, expected_sha = sys.argv[1:5]
source_path = os.path.realpath(os.path.join(project_root, *module_name.split(".")) + ".py")
expected_path = os.path.realpath(os.path.join(project_root, "iclr2027", "obligation_outcomes.py"))
if source_path != expected_path:
    raise SystemExit(71)
stdlib_roots = tuple(
    os.path.realpath(path)
    for path in (
        os.path.dirname(os.__file__),
        os.path.join(sys.base_prefix, "DLLs"),
        os.path.join(sys.base_prefix, "Lib"),
    )
)
state = {"sealed": False}

def audit(event, args):
    if event == "open":
        target = args[0]
        if isinstance(target, int):
            return
        resolved = os.path.realpath(os.fsdecode(target))
        if state["sealed"] or not (
            resolved == source_path
            or any(resolved == root or resolved.startswith(root + os.sep) for root in stdlib_roots)
        ):
            raise PermissionError("worker file access denied")
    if state["sealed"] and (
        event == "import"
        or event.startswith("socket.")
        or event.startswith("subprocess.")
        or event in {"compile", "exec", "os.system", "os.spawn", "ctypes.dlopen"}
    ):
        raise PermissionError("worker capability denied")

sys.addaudithook(audit)
with open(source_path, "rb") as source_handle:
    source_bytes = source_handle.read()
if hashlib.sha256(source_bytes).hexdigest() != expected_sha:
    raise SystemExit(72)
os.environ.clear()
package = types.ModuleType("iclr2027")
package.__path__ = [os.path.join(project_root, "iclr2027")]
package.__package__ = "iclr2027"
sys.modules["iclr2027"] = package
module = types.ModuleType(module_name)
module.__file__ = source_path
module.__package__ = "iclr2027"
sys.modules[module_name] = module
exec(compile(source_bytes, source_path, "exec"), module.__dict__)
state["sealed"] = True
module._blind_worker_main(evaluator_qualname, expected_sha)
'''.strip()


def _worker_environment() -> dict[str, str]:
    result = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if name in os.environ:
                result[name] = os.environ[name]
    return result


def _terminate_and_reap_worker(
    process: Any, *, wait_seconds: float
) -> BaseException | None:
    cleanup_error: BaseException | None = None
    try:
        process.terminate()
    except BaseException as error:
        cleanup_error = error
    try:
        process.wait(timeout=wait_seconds)
        return cleanup_error
    except subprocess.TimeoutExpired:
        pass
    except BaseException as error:
        if cleanup_error is None:
            cleanup_error = error
    try:
        process.kill()
    except BaseException as error:
        if cleanup_error is None:
            cleanup_error = error
    try:
        process.wait()
    except BaseException as error:
        if cleanup_error is None:
            cleanup_error = error
    return cleanup_error


def _run_blind_worker(
    source: BranchEvaluationSource,
    *,
    popen_factory: Any,
    timeout_seconds: float,
    kill_wait_seconds: float,
    request_capture: list[bytes] | None,
    response_mutator: Any | None,
    bootstrap_source_for_test: str | None = None,
    _trusted_bootstrap_source: str = _BLIND_WORKER_BOOTSTRAP,
    _trusted_bootstrap_sha256: str = "00e19b82e8713b0cef68d5edbfc824575321bd1b4fbf2cf00471225d2ccd6749",
) -> tuple[BlindEvaluation, int]:
    bootstrap_source = (
        _trusted_bootstrap_source
        if bootstrap_source_for_test is None
        else bootstrap_source_for_test
    )
    if (
        type(bootstrap_source) is not str
        or _sha256_bytes(bootstrap_source.encode("utf-8"))
        != _trusted_bootstrap_sha256
    ):
        raise BranchOutcomeContractError("blind worker bootstrap digest mismatch")
    request, nonce = _request_frame(source)
    if request_capture is not None:
        request_capture.append(request)
    specification = source.implementation_spec
    project_root = str(Path(__file__).resolve(strict=True).parents[1])
    argv = [
        str(Path(sys.executable).resolve(strict=True)),
        "-I",
        "-S",
        "-B",
        "-c",
        bootstrap_source,
        project_root,
        specification.evaluator_module,
        specification.evaluator_qualname,
        specification.evaluator_source_sha256,
    ]
    kwargs: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "close_fds": True,
        "env": _worker_environment(),
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    with tempfile.TemporaryDirectory() as working_directory:
        kwargs["cwd"] = working_directory
        process = popen_factory(argv, **kwargs)
        try:
            stdout, stderr = process.communicate(
                input=request,
                timeout=timeout_seconds,
            )
        except BaseException as error:
            cleanup_error = _terminate_and_reap_worker(
                process, wait_seconds=kill_wait_seconds
            )
            if cleanup_error is not None:
                error.add_note(
                    "blind worker cleanup also failed: "
                    f"{type(cleanup_error).__name__}"
                )
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            message = (
                "blind worker timed out"
                if isinstance(error, subprocess.TimeoutExpired)
                else "blind worker communication failed"
            )
            raise BranchOutcomeContractError(message) from error
    if process.returncode != 0:
        raise BranchOutcomeContractError("blind worker exited abnormally")
    if stderr:
        raise BranchOutcomeContractError("blind worker emitted stderr")
    if response_mutator is not None:
        stdout = response_mutator(stdout)
    response = _parse_frame(
        stdout,
        maximum=_MAX_RESPONSE_BYTES,
        label="worker response",
    )
    _exact_keys(
        response,
        {
            "schema_version",
            "nonce",
            "evaluator_contract_sha256",
            "worker_pid",
            "ok",
            "evaluation",
            "error",
            "response_sha256",
        },
        "worker response",
    )
    if response["schema_version"] != _WORKER_RESPONSE_SCHEMA:
        raise BranchOutcomeContractError("worker response schema mismatch")
    response_nonce = _hash(response["nonce"], "response nonce")
    response_contract = _hash(
        response["evaluator_contract_sha256"], "response contract"
    )
    worker_pid = _native_int(
        response["worker_pid"], "worker_pid", minimum=1
    )
    ok = _native_bool(response["ok"], "worker ok")
    response_hash = _hash(response["response_sha256"], "response_sha256")
    unsigned = {
        key: value for key, value in response.items() if key != "response_sha256"
    }
    if response_hash != _sha256_json(unsigned):
        raise BranchOutcomeContractError("worker response self-hash mismatch")
    if response_nonce != nonce or response_contract != source.provenance.evaluator_contract_sha256:
        raise BranchOutcomeContractError("worker response nonce/contract mismatch")
    if worker_pid != process.pid:
        raise BranchOutcomeContractError("worker response PID mismatch")
    if ok:
        if response["error"] is not None or response["evaluation"] is None:
            raise BranchOutcomeContractError("successful worker response has wrong union")
        return _evaluation_from_wire(response["evaluation"]), worker_pid
    if response["evaluation"] is not None or response["error"] not in _WORKER_ERRORS:
        raise BranchOutcomeContractError("failed worker response has wrong union")
    raise BranchOutcomeContractError(f"blind worker failed: {response['error']}")


def _run_blind_worker_for_test(
    source: BranchEvaluationSource,
    *,
    popen_factory: Any = subprocess.Popen,
    timeout_seconds: float = _WORKER_TIMEOUT_SECONDS,
    kill_wait_seconds: float = _WORKER_KILL_WAIT_SECONDS,
    request_capture: list[bytes] | None = None,
    response_mutator: Any | None = None,
    bootstrap_source_for_test: str | None = None,
) -> tuple[BlindEvaluation, int]:
    if type(source) is not BranchEvaluationSource:
        raise TypeError("source must be exact BranchEvaluationSource")
    if request_capture is not None and type(request_capture) is not list:
        raise TypeError("request_capture must be an exact list or None")
    if response_mutator is not None and not callable(response_mutator):
        raise TypeError("response_mutator must be callable or None")
    if bootstrap_source_for_test is not None and type(bootstrap_source_for_test) is not str:
        raise TypeError("bootstrap_source_for_test must be an exact string or None")
    return _run_blind_worker(
        source,
        popen_factory=popen_factory,
        timeout_seconds=timeout_seconds,
        kill_wait_seconds=kill_wait_seconds,
        request_capture=request_capture,
        response_mutator=response_mutator,
        bootstrap_source_for_test=bootstrap_source_for_test,
    )


def _join_blind_evaluation_for_test(source: BranchEvaluationSource, evaluation: BlindEvaluation) -> BranchOutcome:
    if type(source) is not BranchEvaluationSource:
        raise TypeError("source must be exact BranchEvaluationSource")
    if type(evaluation) is not BlindEvaluation:
        raise TypeError("evaluation must be exact BlindEvaluation")
    return BranchOutcome._create(source.key, BlindEvaluation(evaluation.obligation_closures, evaluation.scores), source.usage, source.provenance)


def evaluate_branch_source(source: BranchEvaluationSource, evaluator: BlindBranchEvaluator) -> BranchOutcome:
    if type(source) is not BranchEvaluationSource:
        raise TypeError("source must be an exact BranchEvaluationSource")
    _validate_evaluator(evaluator, source.implementation_spec)
    if (
        source.implementation_spec.evaluator_contract_sha256
        != source.provenance.evaluator_contract_sha256
    ):
        raise BranchOutcomeContractError("evaluator contract binding mismatch")
    evaluation, _process_id = _run_blind_worker(
        source,
        popen_factory=subprocess.Popen,
        timeout_seconds=_WORKER_TIMEOUT_SECONDS,
        kill_wait_seconds=_WORKER_KILL_WAIT_SECONDS,
        request_capture=None,
        response_mutator=None,
    )
    return _join_blind_evaluation_for_test(source, evaluation)


def _receipt_content(
    schema_version: str,
    outcomes_relative_path: str,
    source_receipt_sha256s: tuple[str, ...],
    branch_transaction_sha256s: tuple[str, ...],
    outcome_sha256s: tuple[str, ...],
    rows_sha256: str,
    outcomes_file_sha256: str,
    row_count: int,
    evaluator_contract_sha256: str,
    evaluator_reference_sha256s: tuple[str, ...],
    implementation_sha256s: tuple[tuple[str, str], ...],
    evaluation_implementation_spec_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "outcomes_relative_path": outcomes_relative_path,
        "source_receipt_sha256s": list(source_receipt_sha256s),
        "branch_transaction_sha256s": list(branch_transaction_sha256s),
        "outcome_sha256s": list(outcome_sha256s),
        "rows_sha256": rows_sha256,
        "outcomes_file_sha256": outcomes_file_sha256,
        "row_count": row_count,
        "evaluator_contract_sha256": evaluator_contract_sha256,
        "evaluator_reference_sha256s": list(evaluator_reference_sha256s),
        "implementation_sha256s": [list(row) for row in implementation_sha256s],
        "evaluation_implementation_spec_sha256": evaluation_implementation_spec_sha256,
    }


@dataclass(frozen=True, slots=True)
class BranchOutcomeReceipt(_PersistedRecord):
    schema_version: str
    outcomes_relative_path: str
    source_receipt_sha256s: tuple[str, ...]
    branch_transaction_sha256s: tuple[str, ...]
    outcome_sha256s: tuple[str, ...]
    rows_sha256: str
    outcomes_file_sha256: str
    row_count: int
    evaluator_contract_sha256: str
    evaluator_reference_sha256s: tuple[str, ...]
    implementation_sha256s: tuple[tuple[str, str], ...]
    evaluation_implementation_spec_sha256: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        schema = _exact_text(self.schema_version, "schema_version")
        object.__setattr__(self, "schema_version", schema)
        if schema != _RECEIPT_SCHEMA:
            raise BranchOutcomeContractError("unsupported receipt schema")
        output_path = _exact_text(self.outcomes_relative_path, "outcomes_relative_path")
        object.__setattr__(self, "outcomes_relative_path", output_path)
        if output_path != "branch_outcomes.jsonl":
            raise BranchOutcomeContractError("outcomes path must be fixed")
        object.__setattr__(self, "row_count", _native_int(self.row_count, "row_count", minimum=1))
        source_hashes = _exact_tuple(self.source_receipt_sha256s, "source_receipt_sha256s")
        for value in source_hashes:
            _hash(value, "source_receipt_sha256")
        if not source_hashes or source_hashes != tuple(sorted(set(source_hashes))):
            raise BranchOutcomeContractError("source receipt hashes must be a nonempty sorted set")
        ordered_names = (
            "branch_transaction_sha256s",
            "outcome_sha256s",
            "evaluator_reference_sha256s",
        )
        for name in ordered_names:
            values = _exact_tuple(getattr(self, name), name)
            for value in values:
                _hash(value, name)
            if len(values) != self.row_count:
                raise BranchOutcomeContractError(f"{name} census mismatch")
        for name in ("rows_sha256", "outcomes_file_sha256", "evaluator_contract_sha256", "evaluation_implementation_spec_sha256"):
            object.__setattr__(self, name, _hash(getattr(self, name), name))
        if self.rows_sha256 != self.outcomes_file_sha256:
            raise BranchOutcomeContractError("row and file hashes must bind the same bytes")
        members = _exact_tuple(self.implementation_sha256s, "implementation_sha256s")
        normalized: list[tuple[str, str]] = []
        for member in members:
            pair = _exact_tuple(member, "implementation member")
            if len(pair) != 2:
                raise BranchOutcomeContractError("implementation member shape mismatch")
            normalized.append((_logical_path(pair[0], "implementation path"), _hash(pair[1], "implementation hash")))
        if tuple(normalized) != tuple(sorted(normalized, key=lambda row: row[0].encode("utf-8"))) or len({row[0].casefold() for row in normalized}) != len(normalized):
            raise BranchOutcomeContractError("receipt implementation closure is noncanonical")
        object.__setattr__(self, "implementation_sha256s", tuple(normalized))
        expected = _sha256_json(_receipt_content(
            self.schema_version, self.outcomes_relative_path, source_hashes,
            self.branch_transaction_sha256s, self.outcome_sha256s,
            self.rows_sha256, self.outcomes_file_sha256, self.row_count,
            self.evaluator_contract_sha256, self.evaluator_reference_sha256s,
            self.implementation_sha256s, self.evaluation_implementation_spec_sha256,
        ))
        if _hash(self.receipt_sha256, "receipt_sha256") != expected:
            raise BranchOutcomeContractError("stale receipt self-hash")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BranchOutcomeReceipt:
        """Validate internal consistency only; this does not authenticate a receipt."""

        data = _exact_dict(payload, "branch outcome receipt")
        _exact_keys(data, {field.name for field in fields(cls)}, "branch outcome receipt")
        tuple_names = (
            "source_receipt_sha256s", "branch_transaction_sha256s", "outcome_sha256s",
            "evaluator_reference_sha256s", "implementation_sha256s",
        )
        converted = dict(data)
        for name in tuple_names:
            raw = _json_array(data[name], name)
            converted[name] = tuple(tuple(item) if name == "implementation_sha256s" and type(item) is list else item for item in raw)
        return cls(**converted)

    def to_dict(self) -> dict[str, Any]:
        return {**_receipt_content(
            self.schema_version, self.outcomes_relative_path, self.source_receipt_sha256s,
            self.branch_transaction_sha256s, self.outcome_sha256s, self.rows_sha256,
            self.outcomes_file_sha256, self.row_count, self.evaluator_contract_sha256,
            self.evaluator_reference_sha256s, self.implementation_sha256s,
            self.evaluation_implementation_spec_sha256,
        ), "receipt_sha256": self.receipt_sha256}


def _rows_bytes(outcomes: tuple[BranchOutcome, ...]) -> bytes:
    return b"".join(row.canonical_json().encode("utf-8") + b"\n" for row in outcomes)


def _validate_receipt_against_outcomes(
    outcomes: tuple[BranchOutcome, ...], receipt: BranchOutcomeReceipt
) -> None:
    validate_branch_outcome_table(outcomes)
    rows = _rows_bytes(outcomes)
    expected_values = {
        "source_receipt_sha256s": tuple(
            sorted({row.provenance.source_receipt_sha256 for row in outcomes})
        ),
        "branch_transaction_sha256s": tuple(
            row.provenance.branch_transaction_sha256 for row in outcomes
        ),
        "outcome_sha256s": tuple(row.sha256() for row in outcomes),
        "rows_sha256": _sha256_bytes(rows),
        "outcomes_file_sha256": _sha256_bytes(rows),
        "row_count": len(outcomes),
        "evaluator_reference_sha256s": tuple(
            row.provenance.evaluator_reference_sha256 for row in outcomes
        ),
    }
    if any(getattr(receipt, name) != value for name, value in expected_values.items()):
        raise BranchOutcomeContractError("receipt does not bind the supplied outcome table")
    if {row.provenance.evaluator_contract_sha256 for row in outcomes} != {
        receipt.evaluator_contract_sha256
    }:
        raise BranchOutcomeContractError("receipt evaluator contract mismatch")
    if {row.provenance.evaluation_implementation_spec_sha256 for row in outcomes} != {
        receipt.evaluation_implementation_spec_sha256
    }:
        raise BranchOutcomeContractError("receipt implementation specification mismatch")


def build_branch_outcome_receipt(
    outcomes: tuple[BranchOutcome, ...],
    *,
    implementation_spec: EvaluationImplementationSpec,
) -> BranchOutcomeReceipt:
    if type(implementation_spec) is not EvaluationImplementationSpec:
        raise TypeError("implementation_spec must be exact EvaluationImplementationSpec")
    validate_branch_outcome_table(outcomes)
    if any(row.provenance.evaluation_implementation_spec_sha256 != implementation_spec.spec_sha256 for row in outcomes):
        raise BranchOutcomeContractError("outcome implementation specification mismatch")
    contracts = {row.provenance.evaluator_contract_sha256 for row in outcomes}
    if len(contracts) != 1:
        raise BranchOutcomeContractError("all outcomes must share one evaluator contract")
    rows = _rows_bytes(outcomes)
    content = _receipt_content(
        _RECEIPT_SCHEMA,
        "branch_outcomes.jsonl",
        tuple(sorted({row.provenance.source_receipt_sha256 for row in outcomes})),
        tuple(row.provenance.branch_transaction_sha256 for row in outcomes),
        tuple(row.sha256() for row in outcomes),
        _sha256_bytes(rows),
        _sha256_bytes(rows),
        len(outcomes),
        next(iter(contracts)),
        tuple(row.provenance.evaluator_reference_sha256 for row in outcomes),
        implementation_spec.implementation_sha256s,
        implementation_spec.spec_sha256,
    )
    return BranchOutcomeReceipt(
        schema_version=content["schema_version"],
        outcomes_relative_path=content["outcomes_relative_path"],
        source_receipt_sha256s=tuple(content["source_receipt_sha256s"]),
        branch_transaction_sha256s=tuple(content["branch_transaction_sha256s"]),
        outcome_sha256s=tuple(content["outcome_sha256s"]),
        rows_sha256=content["rows_sha256"],
        outcomes_file_sha256=content["outcomes_file_sha256"],
        row_count=content["row_count"],
        evaluator_contract_sha256=content["evaluator_contract_sha256"],
        evaluator_reference_sha256s=tuple(content["evaluator_reference_sha256s"]),
        implementation_sha256s=tuple(
            tuple(row) for row in content["implementation_sha256s"]
        ),
        evaluation_implementation_spec_sha256=content[
            "evaluation_implementation_spec_sha256"
        ],
        receipt_sha256=_sha256_json(content),
    )


def verify_branch_outcomes_from_source(
    outcomes: tuple[BranchOutcome, ...],
    receipt: BranchOutcomeReceipt,
    *,
    sources: tuple[BranchEvaluationSource, ...],
    evaluator: BlindBranchEvaluator,
) -> None:
    rows = _exact_tuple(outcomes, "outcomes")
    if any(type(row) is not BranchOutcome for row in rows):
        raise TypeError("outcomes must contain exact BranchOutcome rows")
    source_rows = _exact_tuple(sources, "sources")
    if type(receipt) is not BranchOutcomeReceipt:
        raise TypeError("receipt must be exact BranchOutcomeReceipt")
    if len(rows) != len(source_rows) or not source_rows:
        raise BranchOutcomeContractError("source/outcome roster census mismatch")
    if any(type(source) is not BranchEvaluationSource for source in source_rows):
        raise TypeError("sources must contain exact BranchEvaluationSource records")
    if tuple(_branch_sort_key(source.key) for source in source_rows) != tuple(sorted(_branch_sort_key(source.key) for source in source_rows)):
        raise BranchOutcomeContractError("sources are not in canonical branch order")
    specification = source_rows[0].implementation_spec
    if any(source.implementation_spec != specification for source in source_rows):
        raise BranchOutcomeContractError("sources do not share one implementation specification")
    source_groups: dict[tuple[str, str, str], list[BranchEvaluationSource]] = {}
    for source in source_rows:
        source_groups.setdefault(
            (source.key.site_id, source.key.case_id, source.key.prefix_id), []
        ).append(source)
    shared_names = (
        "public_case_sha256",
        "public_state_sha256",
        "prefix_input_sha256",
        "evaluator_contract_sha256",
        "evaluator_reference_sha256",
        "assignment_receipt_sha256",
        "evaluation_implementation_spec_sha256",
    )
    for group in source_groups.values():
        if len({source.evaluator_reference for source in group}) != 1:
            raise BranchOutcomeContractError(
                "assessment-target evaluator reference bytes mismatch"
            )
        for name in shared_names:
            if len({getattr(source.provenance, name) for source in group}) != 1:
                raise BranchOutcomeContractError(
                    f"assessment-target source {name} mismatch"
                )
    expected = tuple(evaluate_branch_source(source, evaluator) for source in source_rows)
    if tuple(row.canonical_json() for row in rows) != tuple(row.canonical_json() for row in expected):
        raise BranchOutcomeContractError("source replay outcome mismatch")
    expected_receipt = build_branch_outcome_receipt(expected, implementation_spec=specification)
    if receipt.canonical_json() != expected_receipt.canonical_json():
        raise BranchOutcomeContractError("source replay receipt mismatch")


def _parse_outcome_jsonl_bytes_for_test(raw: bytes) -> tuple[BranchOutcome, ...]:
    if type(raw) is not bytes:
        raise TypeError("JSONL must be exact bytes")
    raw.decode("utf-8", errors="strict")
    if not raw or not raw.endswith(b"\n") or b"\r" in raw or b"\n\n" in raw:
        raise BranchOutcomeContractError("JSONL requires one canonical LF-terminated object per row")
    lines = raw[:-1].split(b"\n")
    outcomes: list[BranchOutcome] = []
    for line in lines:
        payload = _decode_json_bytes(line, "outcome row")
        if _canonical_bytes(payload) != line:
            raise BranchOutcomeContractError("outcome row is noncanonical")
        outcomes.append(BranchOutcome.from_dict(payload))
    result = tuple(outcomes)
    validate_branch_outcome_table(result)
    return result


def _parse_receipt_bytes_for_test(raw: bytes) -> BranchOutcomeReceipt:
    payload = _decode_json_bytes(raw, "receipt")
    if _canonical_bytes(payload) != raw:
        raise BranchOutcomeContractError("receipt bytes are noncanonical")
    return BranchOutcomeReceipt.from_dict(payload)


_TABLE_NAME = "branch_outcomes.jsonl"
_PUBLICATION_RECEIPT_NAME = "branch_outcomes.receipt.json"
_PUBLICATION_LOCK_NAME = ".branch_outcomes.lock"
_QUARANTINE_NAME = ".branch_outcomes.quarantine"
_LOCK_SCHEMA = "ace.iclr2027.branch_outcome_lock.v1"
_QUARANTINE_SCHEMA = "ace.iclr2027.branch_outcome_quarantine.v1"


def _publication_phase_hook_for_test(_phase: str) -> None:
    """Private deterministic fault-injection boundary; production supplies no hook."""


@dataclass(slots=True)
class _PublicationLeaf:
    name: str
    handle: Any
    size: int
    sha256: str


def _self_hashed_marker(content: dict[str, Any], hash_name: str) -> bytes:
    return _canonical_bytes({**content, hash_name: _sha256_bytes(_canonical_bytes(content))})


def _posix_publication_supported() -> bool:
    required = {os.open, os.rename, os.stat, os.unlink}
    return required <= os.supports_dir_fd and os.stat in os.supports_follow_symlinks


class _PublicationCapability:
    """Retained directory capability used by the synthetic Phase 4A publisher."""

    def __init__(self, output_dir: Path) -> None:
        if not isinstance(output_dir, Path):
            raise TypeError("test output directory must be a Path")
        self.output_dir = Path(os.path.abspath(output_dir))
        self.parent_dir = self.output_dir.parent
        if self.output_dir == self.parent_dir:
            raise BranchOutcomeContractError("output directory cannot be a filesystem root")
        self.parent_handle: Any = None
        self.output_handle: Any = None
        self._leaves: dict[str, _PublicationLeaf] = {}

    def __enter__(self) -> _PublicationCapability:
        if os.name == "nt":
            self.parent_handle = self._win_open_absolute_directory(self.parent_dir)
            try:
                self._win_validate(
                    self.parent_handle, expected=self.parent_dir, directory=True
                )
                self.output_handle = self._win_open_relative(
                    self.parent_handle,
                    self.output_dir.name,
                    directory=True,
                    create=False,
                    access=_OUT_FILE_LIST_DIRECTORY
                    | _OUT_FILE_READ_ATTRIBUTES
                    | _OUT_SYNCHRONIZE,
                    share=_OUT_SHARE_READ_WRITE,
                )
                self._win_validate(
                    self.output_handle, expected=self.output_dir, directory=True
                )
            except BaseException:
                self._win_close(self.output_handle)
                self._win_close(self.parent_handle)
                self.output_handle = self.parent_handle = None
                raise
        else:
            if not _posix_publication_supported():
                raise BranchOutcomeContractError(
                    "platform lacks handle-relative publication support"
                )
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
            self.parent_handle = os.open(self.parent_dir, flags)
            try:
                self.output_handle = os.open(
                    self.output_dir.name, flags, dir_fd=self.parent_handle
                )
                self._posix_validate(
                    self.parent_handle, expected=self.parent_dir, directory=True
                )
                self._posix_validate(
                    self.output_handle, expected=self.output_dir, directory=True
                )
            except BaseException:
                if self.output_handle is not None:
                    os.close(self.output_handle)
                os.close(self.parent_handle)
                self.output_handle = self.parent_handle = None
                raise
        self.ensure_current()
        return self

    def __exit__(self, *_exc: object) -> None:
        for leaf in tuple(self._leaves.values()):
            try:
                self.cleanup_leaf(leaf)
            except BaseException:
                pass
        if os.name == "nt":
            self._win_close(self.output_handle)
            self._win_close(self.parent_handle)
        else:
            if self.output_handle is not None:
                os.close(self.output_handle)
            if self.parent_handle is not None:
                os.close(self.parent_handle)
        self.output_handle = self.parent_handle = None

    def ensure_current(self) -> None:
        if self.parent_handle is None or self.output_handle is None:
            raise RuntimeError("publication capability is closed")
        if os.name == "nt":
            self._win_validate(
                self.parent_handle, expected=self.parent_dir, directory=True
            )
            self._win_validate(
                self.output_handle, expected=self.output_dir, directory=True
            )
        else:
            self._posix_validate(
                self.parent_handle, expected=self.parent_dir, directory=True
            )
            self._posix_validate(
                self.output_handle, expected=self.output_dir, directory=True
            )

    def create_leaf(
        self, final_name: str, payload: bytes, *, write_phase: str | None
    ) -> _PublicationLeaf:
        if write_phase is not None:
            _publication_phase_hook_for_test(write_phase)
        self.ensure_current()
        for _attempt in range(32):
            name = f".{final_name}.{secrets.token_hex(16)}.tmp"
            try:
                if os.name == "nt":
                    handle = self._win_open_relative(
                        self.output_handle,
                        name,
                        directory=False,
                        create=True,
                        access=_OUT_FILE_WRITE_DATA
                        | _OUT_FILE_READ_ATTRIBUTES
                        | _OUT_DELETE
                        | _OUT_SYNCHRONIZE,
                        share=_OUT_SHARE_ALL,
                    )
                else:
                    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
                    handle = os.open(name, flags, 0o600, dir_fd=self.output_handle)
            except FileExistsError:
                continue
            leaf = _PublicationLeaf(name, handle, len(payload), _sha256_bytes(payload))
            self._leaves[name] = leaf
            try:
                if os.name == "nt":
                    self._win_write(handle, payload)
                else:
                    view = memoryview(payload)
                    while view:
                        written = os.write(handle, view)
                        if written <= 0:
                            raise OSError("temporary write made no progress")
                        view = view[written:]
                if write_phase is not None:
                    _publication_phase_hook_for_test(
                        write_phase.replace("write", "fsync")
                    )
                if os.name == "nt":
                    if not _OUT_KERNEL32.FlushFileBuffers(handle):
                        raise OSError(ctypes.get_last_error(), "temporary fsync failed")
                else:
                    os.fsync(handle)
                self.validate_leaf(leaf)
                return leaf
            except BaseException:
                try:
                    self.cleanup_leaf(leaf)
                finally:
                    raise
        raise FileExistsError("cannot allocate a unique publication temporary")

    def create_fixed_leaf(self, name: str, payload: bytes) -> _PublicationLeaf:
        self.ensure_current()
        if os.name == "nt":
            handle = self._win_open_relative(
                self.output_handle,
                name,
                directory=False,
                create=True,
                access=_OUT_FILE_WRITE_DATA
                | _OUT_FILE_READ_ATTRIBUTES
                | _OUT_DELETE
                | _OUT_SYNCHRONIZE,
                share=_OUT_SHARE_READ_WRITE,
            )
        else:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            handle = os.open(name, flags, 0o600, dir_fd=self.output_handle)
        leaf = _PublicationLeaf(name, handle, len(payload), _sha256_bytes(payload))
        self._leaves[name] = leaf
        try:
            if os.name == "nt":
                self._win_write(handle, payload)
                if not _OUT_KERNEL32.FlushFileBuffers(handle):
                    raise OSError(ctypes.get_last_error(), "fixed-leaf fsync failed")
            else:
                view = memoryview(payload)
                while view:
                    count = os.write(handle, view)
                    if count <= 0:
                        raise OSError("fixed-leaf write made no progress")
                    view = view[count:]
                os.fsync(handle)
            self.validate_leaf(leaf)
            return leaf
        except BaseException:
            try:
                self.cleanup_leaf(leaf)
            finally:
                raise

    def validate_leaf(self, leaf: _PublicationLeaf) -> None:
        if leaf.handle is None:
            raise BranchOutcomeContractError("publication leaf handle is closed")
        if os.name == "nt":
            self._win_validate(
                leaf.handle,
                expected=self.output_dir / leaf.name,
                directory=False,
            )
            raw = self._win_read_fresh(leaf.name)
        else:
            observed = os.fstat(leaf.handle)
            try:
                named = os.stat(
                    leaf.name, dir_fd=self.output_handle, follow_symlinks=False
                )
            except FileNotFoundError as error:
                raise BranchOutcomeContractError("publication leaf identity changed") from error
            if (
                not stat.S_ISREG(observed.st_mode)
                or observed.st_nlink != 1
                or (observed.st_dev, observed.st_ino) != (named.st_dev, named.st_ino)
            ):
                raise BranchOutcomeContractError("publication leaf identity changed")
            raw = self._read_optional(leaf.name)
            if raw is None:
                raise BranchOutcomeContractError("publication leaf disappeared")
        if len(raw) != leaf.size or _sha256_bytes(raw) != leaf.sha256:
            raise BranchOutcomeContractError("publication leaf bytes changed")

    def replace(
        self, leaf: _PublicationLeaf, final_name: str, *, phase: str | None
    ) -> None:
        if phase is not None:
            _publication_phase_hook_for_test(phase)
        self.ensure_current()
        self.validate_leaf(leaf)
        if os.name == "nt":
            self._win_rename(leaf.handle, final_name)
            self._win_validate(
                leaf.handle, expected=self.output_dir / final_name, directory=False
            )
            self._win_close(leaf.handle)
        else:
            identity = os.fstat(leaf.handle)
            os.replace(
                leaf.name,
                final_name,
                src_dir_fd=self.output_handle,
                dst_dir_fd=self.output_handle,
            )
            named = os.stat(
                final_name, dir_fd=self.output_handle, follow_symlinks=False
            )
            if (identity.st_dev, identity.st_ino) != (named.st_dev, named.st_ino):
                raise BranchOutcomeContractError(
                    "publication replacement identity changed"
                )
            os.close(leaf.handle)
        leaf.handle = None
        self._leaves.pop(leaf.name, None)

    def read_optional(self, name: str) -> bytes | None:
        self.ensure_current()
        return self._read_optional(name)

    def _read_optional(self, name: str) -> bytes | None:
        if os.name == "nt":
            try:
                return self._win_read_fresh(name)
            except FileNotFoundError:
                return None
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            handle = os.open(name, flags, dir_fd=self.output_handle)
        except FileNotFoundError:
            return None
        try:
            observed = os.fstat(handle)
            if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
                raise BranchOutcomeContractError("publication member has invalid identity")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(handle, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(handle)

    def delete_name(self, name: str) -> None:
        self.ensure_current()
        if os.name == "nt":
            try:
                handle = self._win_open_relative(
                    self.output_handle,
                    name,
                    directory=False,
                    create=False,
                    access=_OUT_FILE_READ_ATTRIBUTES | _OUT_DELETE | _OUT_SYNCHRONIZE,
                    share=_OUT_SHARE_ALL,
                )
            except FileNotFoundError:
                return
            try:
                self._win_validate(handle, expected=self.output_dir / name, directory=False)
                self._win_delete(handle)
            finally:
                self._win_close(handle)
        else:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            try:
                handle = os.open(name, flags, dir_fd=self.output_handle)
            except FileNotFoundError:
                return
            try:
                observed = os.fstat(handle)
                named = os.stat(
                    name, dir_fd=self.output_handle, follow_symlinks=False
                )
                if (
                    not stat.S_ISREG(observed.st_mode)
                    or observed.st_nlink != 1
                    or (observed.st_dev, observed.st_ino)
                    != (named.st_dev, named.st_ino)
                ):
                    raise BranchOutcomeContractError(
                        "publication deletion identity changed"
                    )
                os.unlink(name, dir_fd=self.output_handle)
            finally:
                os.close(handle)

    def cleanup_leaf(self, leaf: _PublicationLeaf) -> None:
        if leaf.name not in self._leaves:
            return
        try:
            if leaf.handle is None:
                return
            try:
                self.validate_leaf(leaf)
            except BaseException:
                if os.name == "nt":
                    self._win_close(leaf.handle)
                else:
                    os.close(leaf.handle)
                leaf.handle = None
                raise
            if os.name == "nt":
                self._win_delete(leaf.handle)
                self._win_close(leaf.handle)
            else:
                os.unlink(leaf.name, dir_fd=self.output_handle)
                os.close(leaf.handle)
            leaf.handle = None
        finally:
            self._leaves.pop(leaf.name, None)

    def abandon_leaf_handle(self, leaf: _PublicationLeaf) -> None:
        """Close an owned handle after cleanup failure without touching its name."""

        if leaf.handle is None:
            return
        if os.name == "nt":
            self._win_close(leaf.handle)
        else:
            os.close(leaf.handle)
        leaf.handle = None
        self._leaves.pop(leaf.name, None)

    def fsync_directory(self) -> None:
        _publication_phase_hook_for_test("directory-fsync")
        self.ensure_current()
        if os.name == "nt":
            if not _OUT_KERNEL32.FlushFileBuffers(self.output_handle):
                error = ctypes.get_last_error()
                if error not in {1, 5, 87}:
                    raise OSError(error, "directory fsync failed")
        else:
            os.fsync(self.output_handle)

    if os.name == "nt":

        @staticmethod
        def _win_open_absolute_directory(path: Path) -> Any:
            handle = _OUT_KERNEL32.CreateFileW(
                str(path),
                _OUT_FILE_LIST_DIRECTORY | _OUT_FILE_READ_ATTRIBUTES | _OUT_SYNCHRONIZE,
                _OUT_SHARE_READ_WRITE,
                None,
                _OUT_OPEN_EXISTING,
                _OUT_FILE_FLAG_BACKUP_SEMANTICS | _OUT_FILE_FLAG_OPEN_REPARSE_POINT,
                None,
            )
            if handle == _OUT_INVALID_HANDLE:
                raise BranchOutcomeContractError(
                    f"publication directory cannot be opened ({ctypes.get_last_error()})"
                )
            return handle

        @staticmethod
        def _win_open_relative(
            parent: Any,
            name: str,
            *,
            directory: bool,
            create: bool,
            access: int,
            share: int,
        ) -> Any:
            name_buffer = ctypes.create_unicode_buffer(name)
            length = len(name.encode("utf-16-le"))
            unicode_name = _OutUnicodeString(
                length, length + 2, ctypes.cast(name_buffer, wintypes.LPWSTR)
            )
            attributes = _OutObjectAttributes(
                ctypes.sizeof(_OutObjectAttributes),
                parent,
                ctypes.pointer(unicode_name),
                _OUT_OBJ_CASE_INSENSITIVE,
                None,
                None,
            )
            io_status = _OutIoStatusBlock()
            handle = wintypes.HANDLE()
            options = (
                (_OUT_FILE_DIRECTORY_FILE if directory else _OUT_FILE_NON_DIRECTORY_FILE)
                | _OUT_FILE_SYNCHRONOUS_IO_NONALERT
                | _OUT_FILE_OPEN_REPARSE_POINT
            )
            status = _OUT_NTDLL.NtCreateFile(
                ctypes.byref(handle),
                access,
                ctypes.byref(attributes),
                ctypes.byref(io_status),
                None,
                _OUT_FILE_ATTRIBUTE_DIRECTORY if directory else _OUT_FILE_ATTRIBUTE_NORMAL,
                share,
                _OUT_FILE_CREATE if create else _OUT_FILE_OPEN,
                options,
                None,
                0,
            )
            if status < 0:
                error = int(_OUT_NTDLL.RtlNtStatusToDosError(status))
                if error in {2, 3}:
                    raise FileNotFoundError(error, "publication member is missing", name)
                if create and error in {80, 183}:
                    raise FileExistsError(error, "publication member exists", name)
                raise OSError(error, "relative publication operation failed", name)
            return handle

        @staticmethod
        def _win_final_path(handle: Any) -> Path:
            size = _OUT_KERNEL32.GetFinalPathNameByHandleW(handle, None, 0, 0)
            if not size:
                raise BranchOutcomeContractError("publication path cannot be authenticated")
            buffer = ctypes.create_unicode_buffer(size + 1)
            result = _OUT_KERNEL32.GetFinalPathNameByHandleW(
                handle, buffer, len(buffer), 0
            )
            if not result or result >= len(buffer):
                raise BranchOutcomeContractError("publication path cannot be authenticated")
            value = buffer.value
            if value.startswith("\\\\?\\"):
                value = value[4:]
            return Path(os.path.abspath(value))

        @classmethod
        def _win_validate(cls, handle: Any, *, expected: Path, directory: bool) -> None:
            tag = _OutFileAttributeTagInfo()
            if not _OUT_KERNEL32.GetFileInformationByHandleEx(
                handle,
                _OUT_FILE_ATTRIBUTE_TAG_INFO_CLASS,
                ctypes.byref(tag),
                ctypes.sizeof(tag),
            ):
                raise BranchOutcomeContractError("publication attributes cannot be authenticated")
            if tag.FileAttributes & _OUT_FILE_ATTRIBUTE_REPARSE_POINT or tag.ReparseTag:
                raise BranchOutcomeContractError("publication reparse point rejected")
            info = _OutFileStandardInfo()
            if not _OUT_KERNEL32.GetFileInformationByHandleEx(
                handle,
                _OUT_FILE_STANDARD_INFO_CLASS,
                ctypes.byref(info),
                ctypes.sizeof(info),
            ):
                raise BranchOutcomeContractError("publication type cannot be authenticated")
            if bool(info.Directory) is not directory or info.DeletePending:
                raise BranchOutcomeContractError("publication identity changed")
            if not directory and info.NumberOfLinks != 1:
                raise BranchOutcomeContractError("publication leaf link count is not one")
            actual = os.path.normcase(str(cls._win_final_path(handle)))
            wanted = os.path.normcase(str(Path(os.path.abspath(expected))))
            if actual != wanted:
                raise BranchOutcomeContractError("publication path identity changed")

        @staticmethod
        def _win_write(handle: Any, payload: bytes) -> None:
            offset = 0
            while offset < len(payload):
                chunk = payload[offset : offset + 1024 * 1024]
                buffer = ctypes.create_string_buffer(chunk)
                written = wintypes.DWORD()
                if not _OUT_KERNEL32.WriteFile(
                    handle, buffer, len(chunk), ctypes.byref(written), None
                ):
                    raise OSError(ctypes.get_last_error(), "temporary write failed")
                if written.value <= 0:
                    raise OSError("temporary write made no progress")
                offset += written.value

        def _win_read_fresh(self, name: str) -> bytes:
            handle = self._win_open_relative(
                self.output_handle,
                name,
                directory=False,
                create=False,
                access=_OUT_FILE_READ_DATA | _OUT_FILE_READ_ATTRIBUTES | _OUT_SYNCHRONIZE,
                share=_OUT_SHARE_ALL,
            )
            try:
                self._win_validate(handle, expected=self.output_dir / name, directory=False)
                chunks: list[bytes] = []
                while True:
                    buffer = ctypes.create_string_buffer(1024 * 1024)
                    read = wintypes.DWORD()
                    if not _OUT_KERNEL32.ReadFile(
                        handle, buffer, len(buffer), ctypes.byref(read), None
                    ):
                        raise OSError(ctypes.get_last_error(), "publication read failed")
                    if read.value == 0:
                        return b"".join(chunks)
                    chunks.append(buffer.raw[: read.value])
            finally:
                self._win_close(handle)

        def _win_rename(self, handle: Any, final_name: str) -> None:
            encoded = final_name.encode("utf-16-le")
            offset = 20
            payload = ctypes.create_string_buffer(offset + len(encoded))
            ctypes.c_ubyte.from_buffer(payload, 0).value = 1
            output_value = getattr(self.output_handle, "value", self.output_handle)
            ctypes.c_void_p.from_buffer(payload, 8).value = output_value
            wintypes.DWORD.from_buffer(payload, 16).value = len(encoded)
            ctypes.memmove(ctypes.addressof(payload) + offset, encoded, len(encoded))
            status_block = _OutIoStatusBlock()
            status = _OUT_NTDLL.NtSetInformationFile(
                handle,
                ctypes.byref(status_block),
                ctypes.byref(payload),
                len(payload),
                10,
            )
            if status < 0:
                error = int(_OUT_NTDLL.RtlNtStatusToDosError(status))
                raise OSError(error, "atomic publication replacement failed")

        @staticmethod
        def _win_delete(handle: Any) -> None:
            disposition = _OutFileDispositionInfo(True)
            if not _OUT_KERNEL32.SetFileInformationByHandle(
                handle,
                _OUT_FILE_DISPOSITION_INFO_CLASS,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            ):
                raise OSError(ctypes.get_last_error(), "publication deletion failed")

        @staticmethod
        def _win_close(handle: Any) -> None:
            if handle is not None:
                _OUT_KERNEL32.CloseHandle(handle)

    else:

        def _posix_validate(self, handle: int, *, expected: Path, directory: bool) -> None:
            observed = os.fstat(handle)
            correct = stat.S_ISDIR(observed.st_mode) if directory else stat.S_ISREG(observed.st_mode)
            if not correct or (not directory and observed.st_nlink != 1):
                raise BranchOutcomeContractError("publication member has invalid identity")
            if directory and expected == self.parent_dir:
                named = os.stat(expected, follow_symlinks=False)
            elif directory:
                named = os.stat(
                    expected.name, dir_fd=self.parent_handle, follow_symlinks=False
                )
            else:
                named = os.stat(
                    expected.name, dir_fd=self.output_handle, follow_symlinks=False
                )
            if (observed.st_dev, observed.st_ino) != (named.st_dev, named.st_ino):
                raise BranchOutcomeContractError("publication path identity changed")


def _publish_pair_for_test(
    outcomes: tuple[BranchOutcome, ...],
    receipt: BranchOutcomeReceipt,
    output_dir: Path,
) -> None:
    """Failure-atomic inert-byte publication for temporary Phase 4A tests only."""

    if type(receipt) is not BranchOutcomeReceipt:
        raise TypeError("receipt must be exact BranchOutcomeReceipt")
    _validate_receipt_against_outcomes(outcomes, receipt)
    table_bytes = _rows_bytes(outcomes)
    receipt_bytes = receipt.canonical_json().encode("utf-8")
    with _PublicationCapability(output_dir) as capability:
        if capability.read_optional(_QUARANTINE_NAME) is not None:
            raise BranchOutcomeContractError("publication directory is quarantined")
        lock_content = {
            "schema_version": _LOCK_SCHEMA,
            "pid": os.getpid(),
            "nonce": secrets.token_hex(32),
        }
        lock = capability.create_fixed_leaf(
            _PUBLICATION_LOCK_NAME,
            _self_hashed_marker(lock_content, "lock_sha256"),
        )
        _publication_phase_hook_for_test("lock")
        table_temp: _PublicationLeaf | None = None
        receipt_temp: _PublicationLeaf | None = None
        replacement_started = False
        prior: tuple[bytes, bytes] | None = None
        failure: BaseException | None = None
        quarantine_reason: str | None = None
        try:
            prior_table = capability.read_optional(_TABLE_NAME)
            prior_receipt = capability.read_optional(_PUBLICATION_RECEIPT_NAME)
            if (prior_table is None) != (prior_receipt is None):
                raise BranchOutcomeContractError("prior pair is incomplete")
            if prior_table is not None:
                assert prior_receipt is not None
                parsed_rows = _parse_outcome_jsonl_bytes_for_test(prior_table)
                parsed_receipt = _parse_receipt_bytes_for_test(prior_receipt)
                _validate_receipt_against_outcomes(parsed_rows, parsed_receipt)
                prior = (prior_table, prior_receipt)
            table_temp = capability.create_leaf(
                _TABLE_NAME, table_bytes, write_phase="table-temp-write"
            )
            receipt_temp = capability.create_leaf(
                _PUBLICATION_RECEIPT_NAME,
                receipt_bytes,
                write_phase="receipt-temp-write",
            )
            replacement_started = True
            capability.replace(table_temp, _TABLE_NAME, phase="table-replace")
            table_temp = None
            capability.replace(
                receipt_temp,
                _PUBLICATION_RECEIPT_NAME,
                phase="receipt-replace",
            )
            receipt_temp = None
            capability.fsync_directory()
            _publication_phase_hook_for_test("verify-reopen")
            if (
                capability.read_optional(_TABLE_NAME) != table_bytes
                or capability.read_optional(_PUBLICATION_RECEIPT_NAME) != receipt_bytes
            ):
                raise BranchOutcomeContractError("published pair changed before verification")
        except BaseException as error:
            failure = error
            if replacement_started:
                try:
                    _restore_published_pair(capability, prior)
                except BaseException:
                    quarantine_reason = "restore_failed"
            try:
                _publication_phase_hook_for_test("cleanup")
                if table_temp is not None:
                    capability.cleanup_leaf(table_temp)
                if receipt_temp is not None:
                    capability.cleanup_leaf(receipt_temp)
            except BaseException as cleanup_error:
                if quarantine_reason is None:
                    quarantine_reason = (
                        "identity_changed"
                        if isinstance(cleanup_error, BranchOutcomeContractError)
                        else "cleanup_failed"
                    )
            if quarantine_reason is None and isinstance(error, BranchOutcomeContractError):
                if "identity" in str(error) or "link count" in str(error):
                    quarantine_reason = "identity_changed"
            if quarantine_reason is not None:
                _write_quarantine(capability, quarantine_reason)
        finally:
            try:
                _publication_phase_hook_for_test("unlock")
                capability.cleanup_leaf(lock)
            except BaseException as unlock_error:
                capability.abandon_leaf_handle(lock)
                if quarantine_reason is None:
                    quarantine_reason = "cleanup_failed"
                    _write_quarantine(capability, quarantine_reason)
                if failure is None:
                    failure = unlock_error
        if failure is not None:
            raise failure


def _restore_published_pair(
    capability: _PublicationCapability, prior: tuple[bytes, bytes] | None
) -> None:
    values: tuple[tuple[str, bytes | None, str], ...] = (
        (_TABLE_NAME, None if prior is None else prior[0], "rollback-table"),
        (
            _PUBLICATION_RECEIPT_NAME,
            None if prior is None else prior[1],
            "rollback-receipt",
        ),
    )
    for name, payload, phase in values:
        last_error: BaseException | None = None
        for _attempt in range(3):
            try:
                _publication_phase_hook_for_test(phase)
                if payload is None:
                    capability.delete_name(name)
                else:
                    temporary = capability.create_leaf(
                        name, payload, write_phase=None
                    )
                    capability.replace(temporary, name, phase=None)
                last_error = None
                break
            except BaseException as error:
                last_error = error
        if last_error is not None:
            raise last_error
    capability.fsync_directory()


def _write_quarantine(capability: _PublicationCapability, reason_code: str) -> None:
    content = {
        "schema_version": _QUARANTINE_SCHEMA,
        "state": "recovery_required",
        "reason_code": reason_code,
    }
    marker = capability.create_fixed_leaf(
        _QUARANTINE_NAME,
        _self_hashed_marker(content, "quarantine_sha256"),
    )
    if os.name == "nt":
        capability._win_close(marker.handle)
    else:
        os.close(marker.handle)
    marker.handle = None
    capability._leaves.pop(marker.name, None)
    capability.fsync_directory()


def _verify_pair_against_expected_for_test(
    outcomes: tuple[BranchOutcome, ...],
    receipt: BranchOutcomeReceipt,
    output_dir: Path,
) -> None:
    expected_table = _rows_bytes(outcomes)
    expected_receipt = receipt.canonical_json().encode("utf-8")
    with _PublicationCapability(output_dir) as capability:
        if capability.read_optional(_QUARANTINE_NAME) is not None:
            raise BranchOutcomeContractError("publication directory is quarantined")
        if capability.read_optional(_PUBLICATION_LOCK_NAME) is not None:
            raise BranchOutcomeContractError("publication directory is locked")
        table_bytes = capability.read_optional(_TABLE_NAME)
        receipt_bytes = capability.read_optional(_PUBLICATION_RECEIPT_NAME)
        if table_bytes != expected_table:
            raise BranchOutcomeContractError("published table differs from external expectation")
        if receipt_bytes != expected_receipt:
            raise BranchOutcomeContractError("published receipt differs from external expectation")
        assert table_bytes is not None and receipt_bytes is not None
        parsed_rows = _parse_outcome_jsonl_bytes_for_test(table_bytes)
        parsed_receipt = _parse_receipt_bytes_for_test(receipt_bytes)
        _validate_receipt_against_outcomes(parsed_rows, parsed_receipt)
        if parsed_rows != outcomes or parsed_receipt != receipt:
            raise BranchOutcomeContractError("published pair semantic mismatch")


__all__ = (
    "BRANCH_OUTCOME_SCHEMA",
    "CALL_CLASS_ORDER",
    "TREATMENT_KINDS",
    "BranchOutcomeContractError",
    "BranchTreatmentKey",
    "ObligationClosureOutcome",
    "BlindOutcomeScores",
    "CallClassUsage",
    "CompleteUsageSummary",
    "OutcomeProvenance",
    "EvaluationImplementationSpec",
    "BranchOutcome",
    "BranchOutcomeReceipt",
    "BlindEvaluation",
    "BlindBranchEvaluator",
    "BranchEvaluationSource",
    "evaluate_branch_source",
    "build_branch_outcome_receipt",
    "verify_branch_outcomes_from_source",
    "validate_branch_outcome_table",
)
