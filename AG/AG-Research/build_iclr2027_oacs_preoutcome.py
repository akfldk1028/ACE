"""Build one synthetic or governed MAS/OACS pre-outcome package exactly once."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from contextlib import contextmanager
import os
from pathlib import Path
import stat
import sys
from typing import Any, Iterator, NamedTuple

from iclr2027.oacs_preflight import (
    OacsPreflightInputsV1,
    PreflightError,
    evaluate_preflight,
    preflight_receipt_bytes,
    verify_preflight_receipt_bytes,
)
from iclr2027.oacs_preflight_v2 import (
    OacsPreflightInputsV2,
    evaluate_preflight_v2,
    preflight_receipt_v2_bytes,
    verify_preflight_receipt_v2_bytes,
)
from iclr2027.secure_files import AuthenticatedTree, read_authenticated_file

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    from iclr2027 import secure_files as _secure_files

    class _AclSizeInformation(ctypes.Structure):
        _fields_ = (
            ("AceCount", wintypes.DWORD),
            ("AclBytesInUse", wintypes.DWORD),
            ("AclBytesFree", wintypes.DWORD),
        )

    class _AceHeader(ctypes.Structure):
        _fields_ = (
            ("AceType", ctypes.c_ubyte),
            ("AceFlags", ctypes.c_ubyte),
            ("AceSize", wintypes.WORD),
        )

    class _AclHeader(ctypes.Structure):
        _fields_ = (
            ("AclRevision", ctypes.c_ubyte),
            ("Sbz1", ctypes.c_ubyte),
            ("AclSize", wintypes.WORD),
            ("AceCount", wintypes.WORD),
            ("Sbz2", wintypes.WORD),
        )

    class _Luid(ctypes.Structure):
        _fields_ = (("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG))

    class _LuidAndAttributes(ctypes.Structure):
        _fields_ = (("Luid", _Luid), ("Attributes", wintypes.DWORD))

    class _PrivilegeSet(ctypes.Structure):
        _fields_ = (
            ("PrivilegeCount", wintypes.DWORD),
            ("Control", wintypes.DWORD),
            ("Privilege", _LuidAndAttributes * 1),
        )

    class _SidAndAttributes(ctypes.Structure):
        _fields_ = (("Sid", wintypes.LPVOID), ("Attributes", wintypes.DWORD))

    class _TokenUser(ctypes.Structure):
        _fields_ = (("User", _SidAndAttributes),)


_OWNER_RIGHTS_DENY_MASK = 0x00000006 | 0x00040000 | 0x00080000
_WORLD_DENY_MASK = 0x00000006
_OWNER_ALLOW_MASK = 0x000000E9 | 0x00010000 | 0x00020000 | 0x00100000
_FILE_OWNER_RIGHTS_DENY_MASK = 0x00040000 | 0x00080000
_FILE_OWNER_ALLOW_MASK = 0x00000089 | 0x00010000 | 0x00020000 | 0x00100000


PACKAGE_MEMBERS = {
    "governing_design": "governing-design.md",
    "claim_ledger": "claim-ledger.json",
    "review_package": "review-package.json",
    "review_problem_novelty": "reviews/problem_novelty.json",
    "review_causal_statistics": "reviews/causal_statistics.json",
    "review_experiment_reproducibility": "reviews/experiment_reproducibility.json",
    "review_adversarial_falsifier": "reviews/adversarial_falsifier.json",
    "architecture_census": "architecture-census.json",
    "jci_census": "jci-census.json",
    "study_contract": "study-contract.json",
    "backend_audit": "backend-audit.json",
    "approval_trust_root": "approval-trust-root.json",
    "architecture_power_plan": "architecture-power-plan.json",
    "jci_power_plan": "jci-power-plan.json",
    "receipt": "preflight-receipt.json",
}
_REVIEW_KEYS = (
    "review_problem_novelty",
    "review_causal_statistics",
    "review_experiment_reproducibility",
    "review_adversarial_falsifier",
)
_INPUT_KEYS = tuple(
    key for key in PACKAGE_MEMBERS if key not in {"receipt", "approval_trust_root"}
)


class PreflightCliError(ValueError):
    """Raised for a deterministic command-line or package-path rejection."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PreflightCliError(message)


class _WindowsPublicationTransaction:
    def __init__(self) -> None:
        self._ktm: Any = None
        self._set_current: Any = None
        self._get_current: Any = None
        self.handle: Any = None
        self._active = False

    @staticmethod
    def _value(handle: Any) -> int:
        value = handle if isinstance(handle, int) else getattr(handle, "value", None)
        return 0 if value is None else int(value)

    def __enter__(self) -> _WindowsPublicationTransaction:
        if os.name != "nt":
            raise PreflightCliError(
                "Windows transactional publication proof is unavailable"
            )
        try:
            self._ktm = ctypes.WinDLL("KtmW32", use_last_error=True)
            create_transaction = self._ktm.CreateTransaction
            create_transaction.argtypes = (
                wintypes.LPVOID,
                wintypes.LPVOID,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.LPCWSTR,
            )
            create_transaction.restype = wintypes.HANDLE
            self._ktm.CommitTransaction.argtypes = (wintypes.HANDLE,)
            self._ktm.CommitTransaction.restype = wintypes.BOOL
            self._ktm.RollbackTransaction.argtypes = (wintypes.HANDLE,)
            self._ktm.RollbackTransaction.restype = wintypes.BOOL
            self._set_current = _secure_files._ntdll.RtlSetCurrentTransaction
            self._set_current.argtypes = (wintypes.HANDLE,)
            self._set_current.restype = ctypes.c_ubyte
            self._get_current = _secure_files._ntdll.RtlGetCurrentTransaction
            self._get_current.argtypes = ()
            self._get_current.restype = wintypes.HANDLE
        except (AttributeError, OSError) as exc:
            raise PreflightCliError(
                "Windows transactional publication APIs are unavailable"
            ) from exc
        if self._value(self._get_current()) != 0:
            raise PreflightCliError(
                "an ambient Windows transaction already exists on this thread"
            )
        self.handle = create_transaction(
            None,
            None,
            0,
            0,
            0,
            0,
            "MAS/OACS exact preflight publication",
        )
        invalid = ctypes.c_void_p(-1).value
        if self._value(self.handle) in (0, invalid):
            error = ctypes.get_last_error()
            raise PreflightCliError(
                f"Windows publication transaction cannot be created ({error})"
            )
        if not self._set_current(self.handle):
            error = ctypes.get_last_error()
            _close_handle(self.handle)
            self.handle = None
            raise PreflightCliError(
                f"Windows publication transaction cannot become ambient ({error})"
            )
        self._active = True
        return self

    def commit(self) -> None:
        if (
            not self._active
            or self.handle is None
            or self._value(self._get_current()) != self._value(self.handle)
        ):
            raise PreflightCliError(
                "Windows publication transaction lost its ambient authority"
            )
        if not self._set_current(None):
            error = ctypes.get_last_error()
            raise PreflightCliError(
                f"Windows publication transaction cannot be detached ({error})"
            )
        if not self._ktm.CommitTransaction(self.handle):
            error = ctypes.get_last_error()
            raise PreflightCliError(
                f"Windows publication transaction cannot commit ({error})"
            )
        self._active = False

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        del exc_type, exc_value, traceback
        rollback_error: int | None = None
        if self.handle is not None and self._active:
            if self._value(self._get_current()) == self._value(self.handle):
                if not self._set_current(None):
                    rollback_error = ctypes.get_last_error()
            if not self._ktm.RollbackTransaction(self.handle):
                rollback_error = ctypes.get_last_error()
        if self.handle is not None:
            _close_handle(self.handle)
        self.handle = None
        self._active = False
        if rollback_error is not None:
            raise PreflightCliError(
                f"Windows publication transaction cannot roll back ({rollback_error})"
            )


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--preflight-version",
        choices=("v1", "v2"),
        default="v1",
    )
    parser.add_argument("--governing-design", required=True)
    parser.add_argument("--governing-design-sha256", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--review-package", required=True)
    parser.add_argument("--review-problem-novelty", required=True)
    parser.add_argument("--review-causal-statistics", required=True)
    parser.add_argument("--review-experiment-reproducibility", required=True)
    parser.add_argument("--review-adversarial-falsifier", required=True)
    parser.add_argument("--architecture-census", required=True)
    parser.add_argument("--jci-census", required=True)
    parser.add_argument("--study-contract", required=True)
    parser.add_argument("--backend-audit", required=True)
    parser.add_argument("--approval-trust-root")
    parser.add_argument("--approval-trust-root-sha256")
    parser.add_argument("--architecture-power-plan", required=True)
    parser.add_argument("--jci-power-plan", required=True)
    parser.add_argument("--output-root", required=True)
    return parser


def _reject_duplicate_options(arguments: Sequence[str]) -> None:
    seen: set[str] = set()
    for token in arguments:
        if not token.startswith("--"):
            continue
        option = token.split("=", 1)[0]
        if option in seen:
            raise PreflightCliError(f"duplicate option rejected: {option}")
        seen.add(option)


def _canonical_absolute_path(value: object, *, label: str) -> Path:
    if type(value) is not str or not value:
        raise PreflightCliError(f"{label} must be an explicit absolute path")
    path = Path(value)
    if not path.is_absolute():
        raise PreflightCliError(f"{label} must be an explicit absolute path")
    canonical = os.path.abspath(os.path.normpath(value))
    if value != canonical:
        raise PreflightCliError(
            f"{label} must be a canonical absolute path without aliases"
        )
    return path


def _read_declared_inputs(
    namespace: argparse.Namespace,
) -> tuple[OacsPreflightInputsV1 | OacsPreflightInputsV2, dict[str, bytes]]:
    declared: dict[str, Path] = {}
    for key in _INPUT_KEYS:
        option_value = getattr(namespace, key)
        declared[key] = _canonical_absolute_path(option_value, label=key)
    if namespace.approval_trust_root is not None:
        declared["approval_trust_root"] = _canonical_absolute_path(
            namespace.approval_trust_root,
            label="approval_trust_root",
        )
    identities = [
        os.path.normcase(os.path.normpath(str(path))) for path in declared.values()
    ]
    if len(set(identities)) != len(identities):
        raise PreflightCliError("duplicate input path rejected")
    raw = {
        key: read_authenticated_file(path, label=key) for key, path in declared.items()
    }
    input_type = (
        OacsPreflightInputsV2
        if namespace.preflight_version == "v2"
        else OacsPreflightInputsV1
    )
    inputs = input_type(
        governing_design_bytes=raw["governing_design"],
        expected_governing_design_sha256=namespace.governing_design_sha256,
        claim_ledger_bytes=raw["claim_ledger"],
        review_package_bytes=raw["review_package"],
        locked_review_bytes=tuple(raw[key] for key in _REVIEW_KEYS),
        architecture_census_bytes=raw["architecture_census"],
        jci_census_bytes=raw["jci_census"],
        study_contract_bytes=raw["study_contract"],
        backend_audit_bytes=raw["backend_audit"],
        approval_trust_root_bytes=raw.get("approval_trust_root"),
        expected_approval_trust_root_sha256=(namespace.approval_trust_root_sha256),
        architecture_power_plan_bytes=raw["architecture_power_plan"],
        jci_power_plan_bytes=raw["jci_power_plan"],
    )
    return inputs, raw


@contextmanager
def _new_output_parent(
    value: object,
) -> Iterator[tuple[Path, AuthenticatedTree]]:
    output = _canonical_absolute_path(value, label="output_root")
    if not output.name.endswith("-final"):
        raise PreflightCliError("output_root must end in -final")
    if os.path.lexists(output):
        raise PreflightCliError("output_root already exists")
    if not os.path.lexists(output.parent):
        raise PreflightCliError("output_root parent does not exist")
    with AuthenticatedTree(output.parent, label="output_root parent") as parent:
        if os.path.lexists(output):
            raise PreflightCliError("output_root already exists")
        yield output, parent


def _close_handle(handle: Any) -> None:
    AuthenticatedTree._close(handle)


def _windows_well_known_sid(kind: int) -> Any:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    create_sid = advapi32.CreateWellKnownSid
    create_sid.argtypes = (
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.DWORD),
    )
    create_sid.restype = wintypes.BOOL
    length = wintypes.DWORD(68)
    sid = ctypes.create_string_buffer(length.value)
    if not create_sid(kind, None, sid, ctypes.byref(length)):
        raise PreflightCliError("Windows security SID cannot be constructed")
    return sid


def _windows_acl(entries: tuple[tuple[bool, int, Any], ...]) -> Any:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    get_length_sid = advapi32.GetLengthSid
    get_length_sid.argtypes = (wintypes.LPVOID,)
    get_length_sid.restype = wintypes.DWORD
    initialize_acl = advapi32.InitializeAcl
    initialize_acl.argtypes = (wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD)
    initialize_acl.restype = wintypes.BOOL
    add_denied = advapi32.AddAccessDeniedAceEx
    add_denied.argtypes = (
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
    )
    add_denied.restype = wintypes.BOOL
    add_allowed = advapi32.AddAccessAllowedAceEx
    add_allowed.argtypes = add_denied.argtypes
    add_allowed.restype = wintypes.BOOL
    length = 8 + sum(8 + get_length_sid(sid) for _, _, sid in entries)
    acl = ctypes.create_string_buffer(length)
    if not initialize_acl(acl, length, 2):
        raise PreflightCliError("Windows package DACL cannot be initialized")
    for denied, mask, sid in entries:
        add = add_denied if denied else add_allowed
        if not add(acl, 2, 0, mask, sid):
            raise PreflightCliError("Windows package ACE cannot be added")
    return acl


def _windows_current_user_sid() -> Any:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    open_token = advapi32.OpenProcessToken
    open_token.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    open_token.restype = wintypes.BOOL
    get_token_information = advapi32.GetTokenInformation
    get_token_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    get_token_information.restype = wintypes.BOOL
    get_length_sid = advapi32.GetLengthSid
    get_length_sid.argtypes = (wintypes.LPVOID,)
    get_length_sid.restype = wintypes.DWORD
    copy_sid = advapi32.CopySid
    copy_sid.argtypes = (wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID)
    copy_sid.restype = wintypes.BOOL
    get_current_process = _secure_files._kernel32.GetCurrentProcess
    get_current_process.argtypes = ()
    get_current_process.restype = wintypes.HANDLE
    token = wintypes.HANDLE()
    if not open_token(get_current_process(), 0x0008, ctypes.byref(token)):
        raise PreflightCliError("current Windows user SID cannot be queried")
    try:
        length = wintypes.DWORD()
        get_token_information(token, 1, None, 0, ctypes.byref(length))
        if length.value == 0:
            raise PreflightCliError("current Windows user SID size is unavailable")
        information = ctypes.create_string_buffer(length.value)
        if not get_token_information(
            token,
            1,
            information,
            length,
            ctypes.byref(length),
        ):
            raise PreflightCliError("current Windows user SID is unavailable")
        source = ctypes.cast(information, ctypes.POINTER(_TokenUser)).contents.User.Sid
        sid_length = get_length_sid(source)
        result = ctypes.create_string_buffer(sid_length)
        if not copy_sid(sid_length, result, source):
            raise PreflightCliError("current Windows user SID cannot be copied")
        return result
    finally:
        _close_handle(token)


def _require_safe_windows_privileges() -> None:
    if os.name != "nt":
        raise PreflightCliError(
            "Windows publication security proof is unavailable on this platform"
        )
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    open_token = advapi32.OpenProcessToken
    open_token.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    open_token.restype = wintypes.BOOL
    open_thread_token = advapi32.OpenThreadToken
    open_thread_token.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.BOOL,
        ctypes.POINTER(wintypes.HANDLE),
    )
    open_thread_token.restype = wintypes.BOOL
    lookup_privilege = advapi32.LookupPrivilegeValueW
    lookup_privilege.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.POINTER(_Luid),
    )
    lookup_privilege.restype = wintypes.BOOL
    privilege_check = advapi32.PrivilegeCheck
    privilege_check.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_PrivilegeSet),
        ctypes.POINTER(wintypes.BOOL),
    )
    privilege_check.restype = wintypes.BOOL
    get_current_process = _secure_files._kernel32.GetCurrentProcess
    get_current_process.argtypes = ()
    get_current_process.restype = wintypes.HANDLE
    get_current_thread = _secure_files._kernel32.GetCurrentThread
    get_current_thread.argtypes = ()
    get_current_thread.restype = wintypes.HANDLE
    tokens: list[tuple[str, Any]] = []
    thread_token = wintypes.HANDLE()
    if open_thread_token(
        get_current_thread(),
        0x0008,
        True,
        ctypes.byref(thread_token),
    ):
        tokens.append(("effective thread", thread_token))
    elif ctypes.get_last_error() != 1008:
        raise PreflightCliError("effective Windows thread token cannot be queried")
    process_token = wintypes.HANDLE()
    if not open_token(get_current_process(), 0x0008, ctypes.byref(process_token)):
        for _, token in reversed(tokens):
            _close_handle(token)
        raise PreflightCliError("current Windows process token cannot be queried")
    tokens.append(("process", process_token))
    try:
        for token_label, token in tokens:
            for name in ("SeTakeOwnershipPrivilege", "SeRestorePrivilege"):
                luid = _Luid()
                if not lookup_privilege(None, name, ctypes.byref(luid)):
                    raise PreflightCliError(
                        f"Windows privilege {name} cannot be resolved"
                    )
                required = _PrivilegeSet(
                    1,
                    1,
                    (_LuidAndAttributes(luid, 0x00000002),),
                )
                enabled = wintypes.BOOL()
                if not privilege_check(
                    token, ctypes.byref(required), ctypes.byref(enabled)
                ):
                    raise PreflightCliError(
                        f"Windows privilege {name} cannot be checked"
                    )
                if enabled:
                    raise PreflightCliError(
                        f"enabled {name} on {token_label} token defeats the "
                        "publication security proof"
                    )
    finally:
        for _, token in reversed(tokens):
            _close_handle(token)


def _create_relative(
    parent_handle: Any,
    name: str,
    *,
    expected: Path,
    directory: bool,
) -> Any:
    if os.name == "nt":
        encoded = name.encode("utf-16-le")
        buffer = ctypes.create_unicode_buffer(name)
        unicode_name = _secure_files._UnicodeString(
            len(encoded),
            len(encoded) + 2,
            ctypes.cast(buffer, wintypes.LPWSTR),
        )
        attributes = _secure_files._ObjectAttributes(
            ctypes.sizeof(_secure_files._ObjectAttributes),
            parent_handle,
            ctypes.pointer(unicode_name),
            _secure_files._OBJ_CASE_INSENSITIVE,
            None,
            None,
        )
        io_status = _secure_files._IoStatusBlock()
        handle = wintypes.HANDLE()
        desired = 0x0001 | 0x0080 | 0x00020000 | 0x00100000
        if directory:
            desired |= 0x00040000 | 0x00080000
        else:
            desired |= 0x0002 | 0x00040000 | 0x00080000
        options = (
            (_secure_files._FILE_DIRECTORY_FILE if directory else 0x00000040)
            | _secure_files._FILE_SYNCHRONOUS_IO_NONALERT
            | _secure_files._FILE_FLAG_OPEN_REPARSE_POINT
        )
        status = _secure_files._ntdll.NtCreateFile(
            ctypes.byref(handle),
            desired,
            ctypes.byref(attributes),
            ctypes.byref(io_status),
            None,
            0 if directory else 0x00000080,
            _secure_files._FILE_SHARE_READ,
            2,
            options,
            None,
            0,
        )
        if status < 0:
            error = _secure_files._ntdll.RtlNtStatusToDosError(status)
            raise PreflightCliError(
                f"new package path cannot be created exclusively ({error})"
            )
        try:
            AuthenticatedTree._validate_handle(
                handle,
                expected=expected,
                directory=directory,
                label="new package path",
            )
        except BaseException:
            _close_handle(handle)
            raise
        return handle

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    if directory:
        os.mkdir(name, 0o700, dir_fd=parent_handle)
        flags |= getattr(os, "O_DIRECTORY", 0)
    else:
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    handle = os.open(name, flags, 0o600, dir_fd=parent_handle)
    try:
        observed = os.fstat(handle)
        valid_type = (
            stat.S_ISDIR(observed.st_mode)
            if directory
            else stat.S_ISREG(observed.st_mode)
        )
        if not valid_type or (not directory and observed.st_nlink != 1):
            raise PreflightCliError("new package path has an invalid native type")
    except BaseException:
        _close_handle(handle)
        raise
    return handle


def _open_retained_relative(
    parent_handle: Any,
    name: str,
    *,
    expected: Path,
    directory: bool,
    bridge_write_share: bool = False,
) -> Any:
    if os.name != "nt":
        raise PreflightCliError(
            "Windows retained publication proof is unavailable on this platform"
        )
    encoded = name.encode("utf-16-le")
    buffer = ctypes.create_unicode_buffer(name)
    unicode_name = _secure_files._UnicodeString(
        len(encoded),
        len(encoded) + 2,
        ctypes.cast(buffer, wintypes.LPWSTR),
    )
    attributes = _secure_files._ObjectAttributes(
        ctypes.sizeof(_secure_files._ObjectAttributes),
        parent_handle,
        ctypes.pointer(unicode_name),
        _secure_files._OBJ_CASE_INSENSITIVE,
        None,
        None,
    )
    io_status = _secure_files._IoStatusBlock()
    handle = wintypes.HANDLE()
    desired = 0x0001 | 0x0080 | 0x00020000 | 0x00100000
    share = _secure_files._FILE_SHARE_READ
    if bridge_write_share:
        share |= 0x00000002
    options = (
        (_secure_files._FILE_DIRECTORY_FILE if directory else 0x00000040)
        | _secure_files._FILE_SYNCHRONOUS_IO_NONALERT
        | _secure_files._FILE_FLAG_OPEN_REPARSE_POINT
    )
    status = _secure_files._ntdll.NtCreateFile(
        ctypes.byref(handle),
        desired,
        ctypes.byref(attributes),
        ctypes.byref(io_status),
        None,
        0,
        share,
        1,
        options,
        None,
        0,
    )
    if status < 0:
        error = _secure_files._ntdll.RtlNtStatusToDosError(status)
        raise PreflightCliError(f"committed package path cannot be retained ({error})")
    try:
        AuthenticatedTree._validate_handle(
            handle,
            expected=expected,
            directory=directory,
            label="committed package path",
        )
    except BaseException:
        _close_handle(handle)
        raise
    return handle


def _write_retained_handle(handle: Any, raw: bytes) -> None:
    if os.name == "nt":
        write_file = _secure_files._kernel32.WriteFile
        write_file.argtypes = (
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        )
        write_file.restype = wintypes.BOOL
        flush_file = _secure_files._kernel32.FlushFileBuffers
        flush_file.argtypes = (wintypes.HANDLE,)
        flush_file.restype = wintypes.BOOL
        position = 0
        while position < len(raw):
            chunk = raw[position : position + 1024 * 1024]
            buffer = ctypes.create_string_buffer(chunk)
            count = wintypes.DWORD()
            if not write_file(
                handle,
                buffer,
                len(chunk),
                ctypes.byref(count),
                None,
            ):
                raise OSError("new package member write failed")
            if count.value <= 0:
                raise OSError("short package write")
            position += count.value
        if not flush_file(handle):
            raise OSError("new package member flush failed")
        return

    position = 0
    while position < len(raw):
        written = os.write(handle, raw[position:])
        if written <= 0:
            raise OSError("short package write")
        position += written
    os.fsync(handle)


def _seal_directory_namespace(handle: Any) -> None:
    if os.name != "nt":
        return
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    set_security = advapi32.SetSecurityInfo
    set_security.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
    )
    set_security.restype = wintypes.DWORD
    owner = _windows_current_user_sid()
    owner_rights = _windows_well_known_sid(71)
    world = _windows_well_known_sid(1)
    sealed_acl = _windows_acl(
        (
            (True, _OWNER_RIGHTS_DENY_MASK, owner_rights),
            (True, _WORLD_DENY_MASK, world),
            (False, _OWNER_ALLOW_MASK, owner),
        )
    )
    result = set_security(
        handle,
        1,
        0x00000001 | 0x00000004 | 0x80000000,
        owner,
        None,
        sealed_acl,
        None,
    )
    if result != 0:
        raise PreflightCliError(f"new package namespace cannot be sealed ({result})")


def _seal_file_access(handle: Any) -> None:
    if os.name != "nt":
        return
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    set_security = advapi32.SetSecurityInfo
    set_security.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
    )
    set_security.restype = wintypes.DWORD
    owner = _windows_current_user_sid()
    owner_rights = _windows_well_known_sid(71)
    dacl = _windows_acl(
        (
            (True, _FILE_OWNER_RIGHTS_DENY_MASK, owner_rights),
            (False, _FILE_OWNER_ALLOW_MASK, owner),
        )
    )
    result = set_security(
        handle,
        1,
        0x00000001 | 0x00000004 | 0x80000000,
        owner,
        None,
        dacl,
        None,
    )
    if result != 0:
        raise PreflightCliError(f"new package member ACL cannot be sealed ({result})")


def _require_exact_protected_acl(
    handle: Any,
    *,
    label: str,
    directory: bool,
) -> None:
    seal_name = "namespace seal" if directory else "member seal"
    if os.name != "nt":
        raise PreflightCliError(
            f"package {seal_name} cannot be authenticated on this platform"
        )
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    get_security = advapi32.GetSecurityInfo
    get_security.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPVOID),
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPVOID),
    )
    get_security.restype = wintypes.DWORD
    get_descriptor_control = advapi32.GetSecurityDescriptorControl
    get_descriptor_control.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    )
    get_descriptor_control.restype = wintypes.BOOL
    get_acl_information = advapi32.GetAclInformation
    get_acl_information.argtypes = (
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.c_int,
    )
    get_acl_information.restype = wintypes.BOOL
    get_ace = advapi32.GetAce
    get_ace.argtypes = (
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
    )
    get_ace.restype = wintypes.BOOL
    get_length_sid = advapi32.GetLengthSid
    get_length_sid.argtypes = (wintypes.LPVOID,)
    get_length_sid.restype = wintypes.DWORD
    equal_sid = advapi32.EqualSid
    equal_sid.argtypes = (wintypes.LPVOID, wintypes.LPVOID)
    equal_sid.restype = wintypes.BOOL
    local_free = _secure_files._kernel32.LocalFree
    local_free.argtypes = (wintypes.HLOCAL,)
    local_free.restype = wintypes.HLOCAL

    owner = wintypes.LPVOID()
    dacl = wintypes.LPVOID()
    descriptor = wintypes.LPVOID()
    result = get_security(
        handle,
        1,
        0x00000001 | 0x00000004,
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result != 0 or not owner or not dacl or not descriptor:
        raise PreflightCliError(f"{label} {seal_name} is absent")
    try:
        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if not get_descriptor_control(
            descriptor,
            ctypes.byref(control),
            ctypes.byref(revision),
        ) or not (control.value & 0x1000):
            raise PreflightCliError(f"{label} {seal_name} is not protected")
        acl_header = ctypes.cast(dacl, ctypes.POINTER(_AclHeader)).contents
        information = _AclSizeInformation()
        if not get_acl_information(
            dacl,
            ctypes.byref(information),
            ctypes.sizeof(information),
            2,
        ):
            raise PreflightCliError(f"{label} {seal_name} cannot be measured")
        owner_rights = _windows_well_known_sid(71)
        current_user = _windows_current_user_sid()
        if not equal_sid(owner, current_user):
            raise PreflightCliError(f"{label} {seal_name} owner is not exact")
        expected_aces = (
            (
                (1, _OWNER_RIGHTS_DENY_MASK, owner_rights),
                (1, _WORLD_DENY_MASK, _windows_well_known_sid(1)),
                (0, _OWNER_ALLOW_MASK, current_user),
            )
            if directory
            else (
                (1, _FILE_OWNER_RIGHTS_DENY_MASK, owner_rights),
                (0, _FILE_OWNER_ALLOW_MASK, current_user),
            )
        )
        expected_size = 8 + sum(8 + get_length_sid(sid) for _, _, sid in expected_aces)
        if (
            acl_header.AclRevision != 2
            or information.AceCount != len(expected_aces)
            or information.AclBytesInUse != expected_size
        ):
            raise PreflightCliError(f"{label} {seal_name} is not exact")
        for index, (ace_type, expected_mask, expected_sid) in enumerate(expected_aces):
            ace = wintypes.LPVOID()
            if not get_ace(dacl, index, ctypes.byref(ace)):
                raise PreflightCliError(f"{label} {seal_name} ACE is unreadable")
            header = ctypes.cast(ace, ctypes.POINTER(_AceHeader)).contents
            mask = wintypes.DWORD.from_address(ace.value + 4).value
            sid = wintypes.LPVOID(ace.value + 8)
            if (
                header.AceType != ace_type
                or header.AceFlags != 0
                or header.AceSize != 8 + get_length_sid(expected_sid)
                or mask != expected_mask
                or not equal_sid(sid, expected_sid)
            ):
                raise PreflightCliError(f"{label} {seal_name} ACE order is not exact")
    finally:
        local_free(descriptor)


def _require_directory_namespace_sealed(handle: Any, *, label: str) -> None:
    _require_exact_protected_acl(handle, label=label, directory=True)


def _require_file_access_sealed(handle: Any, *, label: str) -> None:
    _require_exact_protected_acl(handle, label=label, directory=False)


def _read_retained_handle(handle: Any, *, label: str) -> bytes:
    if os.name == "nt":
        set_pointer = _secure_files._kernel32.SetFilePointerEx
        set_pointer.argtypes = (
            wintypes.HANDLE,
            ctypes.c_longlong,
            ctypes.POINTER(ctypes.c_longlong),
            wintypes.DWORD,
        )
        set_pointer.restype = wintypes.BOOL
        if not set_pointer(handle, 0, None, 0):
            raise PreflightCliError(f"{label} retained handle cannot be rewound")
        return AuthenticatedTree._read_handle(handle, label=label)
    os.lseek(handle, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(handle, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _list_retained_directory(
    handle: Any,
    *,
    label: str,
) -> tuple[tuple[str, bool], ...]:
    return AuthenticatedTree._list_handle(handle, label=label)


class _CreatedPackage(NamedTuple):
    root_handle: Any
    review_handle: Any
    file_handles: dict[str, Any]
    expected: dict[str, bytes]


def _verify_created_package(package: _CreatedPackage) -> None:
    expected_top, expected_reviews = _expected_member_sets(package.expected)
    if (
        set(
            _list_retained_directory(
                package.root_handle,
                label="new output package",
            )
        )
        != expected_top
    ):
        raise PreflightCliError("new output package member set drifted")
    if (
        set(
            _list_retained_directory(
                package.review_handle,
                label="new output reviews",
            )
        )
        != expected_reviews
    ):
        raise PreflightCliError("new output review member set drifted")
    for relative in sorted(package.expected, key=lambda item: item.encode("utf-8")):
        if (
            _read_retained_handle(package.file_handles[relative], label=relative)
            != package.expected[relative]
        ):
            raise PreflightCliError("new output package failed exact read-back")


def _require_created_package_sealed(package: _CreatedPackage) -> None:
    _require_directory_namespace_sealed(
        package.review_handle,
        label="new output reviews",
    )
    _require_directory_namespace_sealed(
        package.root_handle,
        label="new output package",
    )
    for relative in sorted(package.expected, key=lambda item: item.encode("utf-8")):
        _require_file_access_sealed(
            package.file_handles[relative],
            label=relative,
        )


def _expected_member_sets(
    expected: dict[str, bytes],
) -> tuple[set[tuple[str, bool]], set[tuple[str, bool]]]:
    top = {
        (Path(relative).parts[0], Path(relative).parts[0] == "reviews")
        for relative in expected
    }
    reviews = {
        (Path(relative).name, False)
        for relative in expected
        if Path(relative).parts[0] == "reviews"
    }
    return top, reviews


@contextmanager
def _write_package_once(
    output: Path,
    parent: AuthenticatedTree,
    raw_inputs: dict[str, bytes],
    receipt_bytes: bytes,
) -> Iterator[_CreatedPackage]:
    expected: dict[str, bytes] = {
        PACKAGE_MEMBERS[key]: raw for key, raw in raw_inputs.items()
    }
    expected[PACKAGE_MEMBERS["receipt"]] = receipt_bytes
    retained: list[Any] = []
    try:
        with _WindowsPublicationTransaction() as transaction:
            transacted: list[Any] = []
            transacted_files: dict[str, Any] = {}
            try:
                root_handle = _create_relative(
                    parent._root_handle,
                    output.name,
                    expected=output,
                    directory=True,
                )
                transacted.append(root_handle)
                review_handle = _create_relative(
                    root_handle,
                    "reviews",
                    expected=output / "reviews",
                    directory=True,
                )
                transacted.append(review_handle)
                for relative in sorted(
                    expected,
                    key=lambda item: item.encode("utf-8"),
                ):
                    path = Path(relative)
                    owner = review_handle if path.parts[0] == "reviews" else root_handle
                    handle = _create_relative(
                        owner,
                        path.name,
                        expected=output / path,
                        directory=False,
                    )
                    transacted.append(handle)
                    transacted_files[relative] = handle
                    _write_retained_handle(handle, expected[relative])
                for handle in transacted_files.values():
                    _seal_file_access(handle)
                _seal_directory_namespace(review_handle)
                _seal_directory_namespace(root_handle)
                transacted_package = _CreatedPackage(
                    root_handle=root_handle,
                    review_handle=review_handle,
                    file_handles=transacted_files,
                    expected=expected,
                )
                _verify_created_package(transacted_package)
                _require_created_package_sealed(transacted_package)
                transaction.commit()

                retained_root = _open_retained_relative(
                    parent._root_handle,
                    output.name,
                    expected=output,
                    directory=True,
                )
                retained.append(retained_root)
                retained_reviews = _open_retained_relative(
                    retained_root,
                    "reviews",
                    expected=output / "reviews",
                    directory=True,
                )
                retained.append(retained_reviews)
                retained_files: dict[str, Any] = {}
                for relative in sorted(
                    expected,
                    key=lambda item: item.encode("utf-8"),
                ):
                    path = Path(relative)
                    owner = (
                        retained_reviews
                        if path.parts[0] == "reviews"
                        else retained_root
                    )
                    handle = _open_retained_relative(
                        owner,
                        path.name,
                        expected=output / path,
                        directory=False,
                        bridge_write_share=True,
                    )
                    retained.append(handle)
                    retained_files[relative] = handle
            finally:
                for handle in reversed(transacted):
                    _close_handle(handle)

            package = _CreatedPackage(
                root_handle=retained_root,
                review_handle=retained_reviews,
                file_handles=retained_files,
                expected=expected,
            )
            _verify_created_package(package)
            _require_created_package_sealed(package)
            yield package
    finally:
        for handle in reversed(retained):
            _close_handle(handle)


def _package_top_level(*, approval_present: bool) -> set[tuple[str, bool]]:
    keys = set(_INPUT_KEYS) | {"receipt"}
    if approval_present:
        keys.add("approval_trust_root")
    return {
        (
            Path(PACKAGE_MEMBERS[key]).parts[0],
            Path(PACKAGE_MEMBERS[key]).parts[0] == "reviews",
        )
        for key in keys
    }


@contextmanager
def read_package_inputs(
    root_value: object,
    *,
    expected_governing_design_sha256: str,
    expected_approval_trust_root_sha256: str | None,
    preflight_version: str = "v1",
) -> Iterator[
    tuple[OacsPreflightInputsV1 | OacsPreflightInputsV2, bytes, _CreatedPackage]
]:
    """Read an exact built package through one authenticated retained root."""

    if preflight_version not in ("v1", "v2"):
        raise PreflightCliError("preflight_version is not supported")
    root = _canonical_absolute_path(root_value, label="input_root")
    if not root.name.endswith("-final"):
        raise PreflightCliError("input_root must end in -final")
    with AuthenticatedTree(root.parent, label="input_root parent") as parent_tree:
        with _WindowsPublicationTransaction():
            transaction_probe = _open_retained_relative(
                parent_tree._root_handle,
                root.name,
                expected=root,
                directory=True,
            )
            _close_handle(transaction_probe)
        retained: list[Any] = []
        try:
            root_handle = _open_retained_relative(
                parent_tree._root_handle,
                root.name,
                expected=root,
                directory=True,
            )
            retained.append(root_handle)
            review_handle = _open_retained_relative(
                root_handle,
                "reviews",
                expected=root / "reviews",
                directory=True,
            )
            retained.append(review_handle)
            with AuthenticatedTree(root, label="input_root") as tree:
                top_entries = tree.list_directory(None, label="input_root")
                top_names = {entry.name for entry in top_entries}
                approval_present = (
                    Path(PACKAGE_MEMBERS["approval_trust_root"]).name in top_names
                )
                if {
                    (entry.name, entry.is_directory) for entry in top_entries
                } != _package_top_level(approval_present=approval_present):
                    raise PreflightCliError(
                        "input_root has missing or extra package members"
                    )
                review_entries = tree.list_directory("reviews", label="input reviews")
                expected_reviews = {
                    (Path(PACKAGE_MEMBERS[key]).name, False) for key in _REVIEW_KEYS
                }
                if {
                    (entry.name, entry.is_directory) for entry in review_entries
                } != expected_reviews:
                    raise PreflightCliError("input review member set is not exact")
                keys = list(_INPUT_KEYS)
                if approval_present:
                    keys.append("approval_trust_root")
                file_handles: dict[str, Any] = {}
                for key in [*keys, "receipt"]:
                    relative_name = PACKAGE_MEMBERS[key]
                    relative = Path(relative_name)
                    owner = (
                        review_handle if relative.parts[0] == "reviews" else root_handle
                    )
                    handle = _open_retained_relative(
                        owner,
                        relative.name,
                        expected=root / relative,
                        directory=False,
                    )
                    retained.append(handle)
                    file_handles[relative_name] = handle
                receipt_raw = _read_retained_handle(
                    file_handles[PACKAGE_MEMBERS["receipt"]],
                    label="receipt",
                )
                if preflight_version == "v2":
                    verify_preflight_receipt_v2_bytes(receipt_raw)
                else:
                    verify_preflight_receipt_bytes(receipt_raw)
                raw = {
                    key: _read_retained_handle(
                        file_handles[PACKAGE_MEMBERS[key]],
                        label=key,
                    )
                    for key in keys
                }
                input_type = (
                    OacsPreflightInputsV2
                    if preflight_version == "v2"
                    else OacsPreflightInputsV1
                )
                inputs = input_type(
                    governing_design_bytes=raw["governing_design"],
                    expected_governing_design_sha256=(expected_governing_design_sha256),
                    claim_ledger_bytes=raw["claim_ledger"],
                    review_package_bytes=raw["review_package"],
                    locked_review_bytes=tuple(raw[key] for key in _REVIEW_KEYS),
                    architecture_census_bytes=raw["architecture_census"],
                    jci_census_bytes=raw["jci_census"],
                    study_contract_bytes=raw["study_contract"],
                    backend_audit_bytes=raw["backend_audit"],
                    approval_trust_root_bytes=raw.get("approval_trust_root"),
                    expected_approval_trust_root_sha256=(
                        expected_approval_trust_root_sha256
                    ),
                    architecture_power_plan_bytes=raw["architecture_power_plan"],
                    jci_power_plan_bytes=raw["jci_power_plan"],
                )
                expected = {PACKAGE_MEMBERS[key]: value for key, value in raw.items()}
                expected[PACKAGE_MEMBERS["receipt"]] = receipt_raw
                package = _CreatedPackage(
                    root_handle=root_handle,
                    review_handle=review_handle,
                    file_handles=file_handles,
                    expected=expected,
                )
                _verify_created_package(package)
                _require_created_package_sealed(package)
                yield inputs, receipt_raw, package
        finally:
            for handle in reversed(retained):
                _close_handle(handle)


def _write_stdout(raw: bytes) -> None:
    stream: Any = sys.stdout
    binary = getattr(stream, "buffer", None)
    if binary is not None:
        binary.write(raw)
        binary.flush()
    else:
        stream.write(raw.decode("utf-8"))
        stream.flush()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        _reject_duplicate_options(arguments)
        namespace = _parser().parse_args(arguments)
        _require_safe_windows_privileges()
        with _new_output_parent(namespace.output_root) as (output, parent):
            inputs, raw_inputs = _read_declared_inputs(namespace)
            if namespace.preflight_version == "v2":
                receipt_raw = preflight_receipt_v2_bytes(evaluate_preflight_v2(inputs))
            else:
                receipt_raw = preflight_receipt_bytes(evaluate_preflight(inputs))
            with _write_package_once(
                output,
                parent,
                raw_inputs,
                receipt_raw,
            ) as package:
                _verify_created_package(package)
                _require_created_package_sealed(package)
                _write_stdout(receipt_raw)
    except (OSError, PreflightCliError, PreflightError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
