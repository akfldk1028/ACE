"""Fixed, sealed runner for the estimand-specific receipt study.

The trusted-process boundary is deliberately narrow: this standalone Python
process uses an audit-hook execution seal before any scientific computation and
does not load unreviewed network clients.  The seal blocks Python-level socket,
DNS, bind/listen, subprocess, and shell escape events.  It is not an OS sandbox
against hostile native extensions or another privileged process.  Output
identity safety is limited to held Windows directory handles, final-path and
file-ID revalidation, and exclusive new-file writes in that trusted process.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import numpy
import scipy

from iclr2027.estimand_receipt_evaluators import CONFIGURATIONS
from iclr2027.estimand_receipt_generator import generate_clean_benchmark
from iclr2027.estimand_receipt_simulation import (
    SCHEMA_VERSION,
    build_evaluator_profile,
    finalize_metrics,
    registered_scenarios,
    simulate_batch,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent
SCIENTIFIC_FILENAMES = (
    "design.json",
    "environment.json",
    "benchmark.json",
    "metrics.jsonl",
    "receipt.json",
)
REVIEWED_SOURCE_FILES = (
    "run_estimand_receipt_study.py",
    "iclr2027/__init__.py",
    "iclr2027/io.py",
    "iclr2027/estimand_receipt_simulation.py",
    "iclr2027/estimand_receipt_evaluators.py",
    "iclr2027/estimand_receipt_generator.py",
    "iclr2027/estimand_receipt_faults.py",
    "iclr2027/estimand_receipt_theory.py",
    "iclr2027/estimand_receipts.py",
)
_PROTECTED_OUTPUT_ROOTS = ("data", "results", "models")
_DISALLOWED_NETWORK_CLIENTS = frozenset(
    (
        "aiohttp",
        "boto3",
        "ftplib",
        "httpx",
        "paramiko",
        "requests",
        "telnetlib",
        "urllib3",
        "websockets",
    )
)
_TRANSPORT_MODULE_AUDIT = frozenset(
    (
        "socket",
        "ssl",
        "asyncio",
        "urllib",
        "urllib.request",
        "http",
        "http.client",
        "subprocess",
    )
)
_NETWORK_AUDIT_EVENTS = frozenset(
    (
        "socket.__new__",
        "socket.bind",
        "socket.connect",
        "socket.connect_ex",
        "socket.getaddrinfo",
        "socket.gethostbyaddr",
        "socket.gethostbyname",
        "socket.listen",
        "subprocess.Popen",
        "os.posix_spawn",
        "os.spawn",
        "os.system",
    )
)
_PROHIBITED_METADATA_KEYS = frozenset(
    (
        "timestamp",
        "createdat",
        "updatedat",
        "modifiedat",
        "startedat",
        "finishedat",
        "completedat",
        "host",
        "hostname",
        "machine",
        "computer",
        "pid",
        "processid",
        "process",
        "nonce",
        "runnonce",
        "executionnonce",
        "temp",
        "tmp",
        "temporary",
        "tempdir",
        "tmpdir",
        "tempfile",
        "templocation",
        "path",
        "filepath",
        "directory",
        "dirname",
        "location",
    )
)
_SEAL_INSTALLED = False


@dataclass(frozen=True, init=False)
class RunConfiguration:
    """A dry-only configuration minted by the module-level parser."""

    mode: str
    replication_start: int
    replication_end_exclusive: int
    replication_count: int
    output_dir: Path
    execution_index: int | None

    def __init__(self, *arguments: object, **keywords: object) -> None:
        del arguments, keywords
        raise TypeError("RunConfiguration is created only by parse_args")

    @classmethod
    def _dry(
        cls,
        *,
        output_dir: Path,
    ) -> RunConfiguration:
        value = object.__new__(cls)
        object.__setattr__(value, "mode", "dry")
        object.__setattr__(value, "replication_start", 0)
        object.__setattr__(value, "replication_end_exclusive", 20)
        object.__setattr__(value, "replication_count", 20)
        object.__setattr__(value, "output_dir", output_dir)
        object.__setattr__(value, "execution_index", None)
        return value

    @property
    def replications(self) -> int:
        """Compatibility alias for the fixed interval count."""

        return self.replication_count


def _argument_error(parser: argparse.ArgumentParser, message: str) -> NoReturn:
    parser.error(message)
    raise AssertionError("argparse.error must exit")


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--registered", action="store_true")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--execution-index", type=int)
    parser.add_argument("--confirm-registered-simulation", action="store_true")
    return parser


def _dry_configuration(
    parser: argparse.ArgumentParser, namespace: argparse.Namespace
) -> RunConfiguration:
    if namespace.dry_run:
        if namespace.execution_index is not None:
            _argument_error(parser, "--execution-index is registered-only")
        if namespace.confirm_registered_simulation:
            _argument_error(parser, "confirmation is registered-only")
        return RunConfiguration._dry(output_dir=namespace.output_dir)
    _argument_error(parser, "registered execution is available only through main")


def _validate_registered_cli(
    parser: argparse.ArgumentParser, namespace: argparse.Namespace
) -> None:
    if not namespace.confirm_registered_simulation:
        _argument_error(parser, "--confirm-registered-simulation is required")
    if namespace.execution_index not in (1, 2):
        _argument_error(parser, "--execution-index must be 1 or 2")


def parse_args(
    arguments: tuple[str, ...] | list[str] | None = None,
) -> RunConfiguration:
    """Parse only dry configurations for module-level/testable helpers."""

    parser = _argument_parser()
    return _dry_configuration(parser, parser.parse_args(arguments))


def _validate_run_configuration(config: object) -> RunConfiguration:
    if type(config) is not RunConfiguration:
        raise ValueError("dry configuration")
    if (
        type(config.replication_start) is not int
        or type(config.replication_end_exclusive) is not int
        or type(config.replication_count) is not int
        or config.replication_start != 0
        or config.replication_end_exclusive - config.replication_start
        != config.replication_count
    ):
        raise ValueError("replication interval")
    if (
        config.mode != "dry"
        or config.replication_count != 20
        or config.execution_index is not None
    ):
        raise ValueError("registered configuration is CLI-only")
    if not isinstance(config.output_dir, Path):
        raise ValueError("output directory")
    return config


def _is_link_or_reparse(path: Path) -> bool:
    """Return whether an existing path could redirect output traversal."""

    if path.is_symlink():
        return True
    try:
        attributes = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, FileNotFoundError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _unresolved_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _has_link_or_reparse_ancestor(path: Path) -> bool:
    current = path
    while True:
        if _is_link_or_reparse(current):
            return True
        if current.parent == current:
            return False
        current = current.parent


def validate_output_directory(path: Path) -> Path:
    """Reject output reuse, redirected traversal, and protected destinations."""

    candidate = _unresolved_absolute(path)
    repository = REPOSITORY_ROOT.resolve()
    for name in _PROTECTED_OUTPUT_ROOTS:
        protected = repository / name
        try:
            candidate.relative_to(protected)
        except ValueError:
            continue
        raise ValueError("protected output directory")
    if _is_link_or_reparse(candidate) or _has_link_or_reparse_ancestor(candidate):
        raise ValueError("link or reparse output traversal")
    if candidate.exists():
        raise ValueError("existing output directory")
    return candidate


def _network_capability_present() -> bool:
    """Audit disallowed third-party network clients before installing the seal."""

    return any(name in sys.modules for name in _DISALLOWED_NETWORK_CLIENTS)


def _execution_audit_hook(event: str, arguments: tuple[object, ...]) -> None:
    del arguments
    if event in _NETWORK_AUDIT_EVENTS:
        raise RuntimeError("network capability is forbidden by execution seal")


def install_execution_seal() -> None:
    """Install the process-wide Python audit boundary before scientific compute."""

    global _SEAL_INSTALLED
    if _SEAL_INSTALLED:
        return
    try:
        sys.addaudithook(_execution_audit_hook)
    except Exception as error:  # pragma: no cover - runtime capability failure
        raise RuntimeError("network execution seal unavailable") from error
    _SEAL_INSTALLED = True


def require_no_network_capability() -> None:
    """Fail closed for client imports, then seal standard-library transports."""

    if _network_capability_present():
        raise RuntimeError("network capability is forbidden")
    # This explicit audit retains visibility of every standard transport module
    # already loaded by scientific dependencies; the audit hook seals each one.
    _ = tuple(name for name in _TRANSPORT_MODULE_AUDIT if name in sys.modules)
    install_execution_seal()


def _normalized_metadata_key(key: str) -> str:
    return "".join(character for character in key.lower() if character.isalnum())


def _reject_execution_metadata(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("scientific payload key")
            if _normalized_metadata_key(key) in _PROHIBITED_METADATA_KEYS:
                raise ValueError("prohibited execution metadata")
            _reject_execution_metadata(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _reject_execution_metadata(child)


def canonical_json_bytes(value: object) -> bytes:
    """Encode JSON canonically without execution-local metadata."""

    _reject_execution_metadata(value)
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def validate_scientific_payload(filename: str, payload: bytes) -> None:
    if filename not in SCIENTIFIC_FILENAMES:
        raise ValueError("scientific filename")
    if not payload.endswith(b"\n") or b"\r" in payload:
        raise ValueError("canonical scientific payload")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("scientific payload encoding") from error
    if filename == "metrics.jsonl":
        body = text[:-1]
        if not body:
            raise ValueError("metrics payload")
        rows = body.split("\n")
        if any(not row for row in rows):
            raise ValueError("blank JSONL row")
        for row in rows:
            if (
                canonical_json_bytes(json.loads(row)).decode("utf-8").rstrip("\n")
                != row
            ):
                raise ValueError("canonical scientific payload")
    elif canonical_json_bytes(json.loads(text)).decode("utf-8") != text:
        raise ValueError("canonical scientific payload")


def _source_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative_name in REVIEWED_SOURCE_FILES:
        source = REPOSITORY_ROOT / relative_name
        if (
            not source.is_file()
            or _is_link_or_reparse(source)
            or _has_link_or_reparse_ancestor(source)
        ):
            raise ValueError("missing source hashes")
        hashes[relative_name] = hashlib.sha256(source.read_bytes()).hexdigest()
    return hashes


def _validate_replication_interval(
    *,
    mode: str,
    replication_start: int,
    replication_end_exclusive: int,
    replication_count: int,
) -> None:
    if (
        type(replication_start) is not int
        or type(replication_end_exclusive) is not int
        or type(replication_count) is not int
        or replication_start != 0
        or replication_end_exclusive - replication_start != replication_count
    ):
        raise ValueError("replication interval")
    required = {"dry": 20, "registered": 2000}.get(mode)
    if required is None or replication_count != required:
        raise ValueError("replication interval")


def receipt_self_hash(receipt: dict[str, object]) -> str:
    payload = {key: value for key, value in receipt.items() if key != "self_sha256"}
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def build_receipt(
    *,
    mode: str,
    replication_start: int,
    replication_end_exclusive: int,
    replication_count: int,
    source_hashes: dict[str, str],
    evaluator_profile_bytes: bytes,
    scenario_ids: tuple[str, ...],
    scientific_payloads: dict[str, bytes],
) -> dict[str, object]:
    """Build a receipt over the exact sources, interval, and scientific bytes."""

    _validate_replication_interval(
        mode=mode,
        replication_start=replication_start,
        replication_end_exclusive=replication_end_exclusive,
        replication_count=replication_count,
    )
    if mode != "dry":
        raise ValueError("registered receipt is CLI-only")
    expected_sources = _source_hashes()
    if type(source_hashes) is not dict or source_hashes != expected_sources:
        raise ValueError("missing source hashes")
    if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("scenario census")
    expected_files = set(SCIENTIFIC_FILENAMES) - {"receipt.json"}
    if set(scientific_payloads) != expected_files:
        raise ValueError("scientific files")
    for filename, payload in scientific_payloads.items():
        validate_scientific_payload(filename, payload)
    receipt: dict[str, object] = {
        "schema_version": "estimand-receipt-study-receipt/v2",
        "mode": mode,
        "replication_start": replication_start,
        "replication_end_exclusive": replication_end_exclusive,
        "replication_count": replication_count,
        "confirmatory": mode == "registered",
        "source_sha256": dict(sorted(source_hashes.items())),
        "evaluator_profile_sha256": hashlib.sha256(evaluator_profile_bytes).hexdigest(),
        "evaluator_profile_bytes_sha256": hashlib.sha256(
            evaluator_profile_bytes
        ).hexdigest(),
        "scenario_count": len(scenario_ids),
        "scenario_order_sha256": hashlib.sha256(
            canonical_json_bytes(list(scenario_ids))
        ).hexdigest(),
        "scientific_files": {
            filename: hashlib.sha256(scientific_payloads[filename]).hexdigest()
            for filename in sorted(scientific_payloads)
        },
    }
    receipt["self_sha256"] = receipt_self_hash(receipt)
    return receipt


def _design_payload(
    *,
    mode: str,
    replication_start: int,
    replication_end_exclusive: int,
    replication_count: int,
    scenario_values: tuple[object, ...],
) -> dict[str, object]:
    _validate_replication_interval(
        mode=mode,
        replication_start=replication_start,
        replication_end_exclusive=replication_end_exclusive,
        replication_count=replication_count,
    )
    if mode != "dry":
        raise ValueError("registered design is CLI-only")
    return {
        "schema_version": "estimand-receipt-study-design/v2",
        "simulation_schema_version": SCHEMA_VERSION,
        "mode": mode,
        "replication_start": replication_start,
        "replication_end_exclusive": replication_end_exclusive,
        "replication_count": replication_count,
        "confirmatory": mode == "registered",
        "scenario_census": [scenario.to_dict() for scenario in scenario_values],
        "configuration_order": list(CONFIGURATIONS),
    }


def _environment_payload() -> dict[str, object]:
    return {
        "schema_version": "estimand-receipt-study-environment/v2",
        "python_implementation": sys.implementation.name,
        "python_version": list(sys.version_info[:3]),
        "numpy_version": numpy.__version__,
        "scipy_version": scipy.__version__,
        "network_execution_seal": "python-audit-hook",
    }


def _benchmark_payload() -> dict[str, object]:
    benchmark = generate_clean_benchmark()
    ledger = [row.to_dict() for row in benchmark.ledger]
    artifacts = [row.to_dict() for row in benchmark.artifacts]
    return {
        "schema_version": "estimand-receipt-study-benchmark/v1",
        "benchmark_schema_version": benchmark.schema_version,
        "study_id": benchmark.study_id,
        "trust_root": benchmark.trust_root.to_dict(),
        "ledger_sha256": hashlib.sha256(canonical_json_bytes(ledger)).hexdigest(),
        "artifacts_sha256": hashlib.sha256(canonical_json_bytes(artifacts)).hexdigest(),
        "ledger_count": len(ledger),
        "artifact_count": len(artifacts),
    }


def _metrics_payload(
    scenario_values: tuple[object, ...],
    replication_start: int,
    replication_end_exclusive: int,
    evaluator_profile: object,
) -> bytes:
    replication_count = replication_end_exclusive - replication_start
    if replication_start != 0 or replication_count != 20:
        raise ValueError("registered metrics are CLI-only")
    rows: list[dict[str, object]] = []
    for scenario in scenario_values:
        batch = simulate_batch(
            scenario,
            replication_start,
            replication_count,
            evaluator_profile=evaluator_profile,
        )
        rows.extend(metric.to_dict() for metric in finalize_metrics((batch,)))
    payload = b"".join(canonical_json_bytes(row) for row in rows)
    validate_scientific_payload("metrics.jsonl", payload)
    return payload


def build_scientific_payloads(config: object) -> dict[str, bytes]:
    """Compute the exact aggregate-only payload after sealing its config/state."""

    checked = _validate_run_configuration(config)
    require_no_network_capability()
    scenarios = registered_scenarios()
    evaluator_profile = build_evaluator_profile()
    profile_text = evaluator_profile.canonical_bytes.decode("utf-8")
    payloads = {
        "design.json": canonical_json_bytes(
            _design_payload(
                mode=checked.mode,
                replication_start=checked.replication_start,
                replication_end_exclusive=checked.replication_end_exclusive,
                replication_count=checked.replication_count,
                scenario_values=scenarios,
            )
        ),
        "environment.json": canonical_json_bytes(_environment_payload()),
        "benchmark.json": canonical_json_bytes(_benchmark_payload()),
        "metrics.jsonl": _metrics_payload(
            scenarios,
            checked.replication_start,
            checked.replication_end_exclusive,
            evaluator_profile,
        ),
    }
    receipt = build_receipt(
        mode=checked.mode,
        replication_start=checked.replication_start,
        replication_end_exclusive=checked.replication_end_exclusive,
        replication_count=checked.replication_count,
        source_hashes=_source_hashes(),
        evaluator_profile_bytes=evaluator_profile.canonical_bytes,
        scenario_ids=tuple(scenario.scenario_id for scenario in scenarios),
        scientific_payloads=payloads,
    )
    receipt["evaluator_profile_canonical_json"] = profile_text
    receipt["self_sha256"] = receipt_self_hash(receipt)
    receipt_bytes = canonical_json_bytes(receipt)
    validate_scientific_payload("receipt.json", receipt_bytes)
    return {**payloads, "receipt.json": receipt_bytes}


@dataclass(frozen=True)
class _DirectoryIdentity:
    volume_serial: int
    file_index: int
    final_path: str


class _ByHandleFileInformation(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", ctypes.c_uint32),
        ("ftCreationTimeLow", ctypes.c_uint32),
        ("ftCreationTimeHigh", ctypes.c_uint32),
        ("ftLastAccessTimeLow", ctypes.c_uint32),
        ("ftLastAccessTimeHigh", ctypes.c_uint32),
        ("ftLastWriteTimeLow", ctypes.c_uint32),
        ("ftLastWriteTimeHigh", ctypes.c_uint32),
        ("dwVolumeSerialNumber", ctypes.c_uint32),
        ("nFileSizeHigh", ctypes.c_uint32),
        ("nFileSizeLow", ctypes.c_uint32),
        ("nNumberOfLinks", ctypes.c_uint32),
        ("nFileIndexHigh", ctypes.c_uint32),
        ("nFileIndexLow", ctypes.c_uint32),
    ]


_FILE_READ_ATTRIBUTES = 0x0080
_FILE_SHARE_READ = 0x0001
_FILE_SHARE_WRITE = 0x0002
_OPEN_EXISTING = 3
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


def _normalized_windows_path(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(os.path.normpath(value))


@dataclass
class _HeldDirectory:
    path: Path
    handle: int
    identity: _DirectoryIdentity
    closed: bool = False

    def close(self) -> None:
        if not self.closed:
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(self.handle)
            self.closed = True

    def revalidate(self) -> None:
        if self.closed or _is_link_or_reparse(self.path):
            raise ValueError("output identity changed")
        fresh = _open_held_directory(self.path)
        try:
            if fresh.identity != self.identity:
                raise ValueError("output identity changed")
        finally:
            fresh.close()


def _open_held_directory(path: Path) -> _HeldDirectory:
    if os.name != "nt":
        raise RuntimeError("Windows secure output handling is required")
    if _is_link_or_reparse(path):
        raise ValueError("link or reparse output traversal")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    )
    create_file.restype = ctypes.c_void_p
    handle = create_file(
        os.fspath(path),
        _FILE_READ_ATTRIBUTES,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle in (None, _INVALID_HANDLE_VALUE):
        raise OSError(ctypes.get_last_error(), "CreateFileW directory handle")
    information = _ByHandleFileInformation()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        kernel32.CloseHandle(handle)
        raise OSError(ctypes.get_last_error(), "GetFileInformationByHandle")
    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    if length == 0 or length >= len(buffer):
        kernel32.CloseHandle(handle)
        raise OSError(ctypes.get_last_error(), "GetFinalPathNameByHandleW")
    expected = _normalized_windows_path(os.path.abspath(os.fspath(path)))
    final_path = _normalized_windows_path(buffer.value)
    if (
        final_path != expected
        or information.dwFileAttributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        kernel32.CloseHandle(handle)
        raise ValueError("output identity changed")
    return _HeldDirectory(
        path=path,
        handle=int(handle),
        identity=_DirectoryIdentity(
            volume_serial=int(information.dwVolumeSerialNumber),
            file_index=(int(information.nFileIndexHigh) << 32)
            | int(information.nFileIndexLow),
            final_path=final_path,
        ),
    )


@dataclass
class FreshOutputRoot:
    path: Path
    parent: _HeldDirectory
    root: _HeldDirectory
    closed: bool = False

    def revalidate(self) -> None:
        self.parent.revalidate()
        self.root.revalidate()

    def write_new(self, filename: str, payload: bytes) -> None:
        if filename not in (*SCIENTIFIC_FILENAMES, "execution-local.json"):
            raise ValueError("output filename")
        self.revalidate()
        destination = self.path / filename
        if _is_link_or_reparse(destination):
            raise ValueError("output identity changed")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        descriptor = os.open(destination, flags, 0o600)
        try:
            self.revalidate()
            written = 0
            while written < len(payload):
                written += os.write(descriptor, payload[written:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self.revalidate()
        if _is_link_or_reparse(destination) or not destination.is_file():
            raise ValueError("output identity changed")

    def abort(self) -> None:
        """Remove only this newly-created, fixed-name incomplete root if safe."""

        try:
            self.revalidate()
            allowed = set(SCIENTIFIC_FILENAMES) | {"execution-local.json"}
            children = tuple(self.path.iterdir())
            if any(
                child.name not in allowed or _is_link_or_reparse(child)
                for child in children
            ):
                return
            for child in children:
                child.unlink()
            self.revalidate()
            self.path.rmdir()
        finally:
            self.close()

    def close(self) -> None:
        if not self.closed:
            self.root.close()
            self.parent.close()
            self.closed = True


def _remove_empty_created_root(path: Path) -> None:
    if _is_link_or_reparse(path):
        return
    try:
        if not any(path.iterdir()):
            path.rmdir()
    except OSError:
        return


def create_fresh_output_root(path: Path) -> FreshOutputRoot:
    """Exclusively create, hold, and identity-bind a new Windows output root."""

    candidate = validate_output_directory(path)
    parent = _open_held_directory(candidate.parent)
    created = False
    root: _HeldDirectory | None = None
    try:
        parent.revalidate()
        os.mkdir(candidate, mode=0o700)
        created = True
        root = _open_held_directory(candidate)
        parent.revalidate()
        root.revalidate()
        return FreshOutputRoot(candidate, parent, root)
    except Exception:
        if root is not None:
            root.close()
        if created:
            _remove_empty_created_root(candidate)
        parent.close()
        raise


def _write_output(config: object, payloads: dict[str, bytes]) -> None:
    checked = _validate_run_configuration(config)
    output = create_fresh_output_root(checked.output_dir)
    completed = False
    try:
        for filename in SCIENTIFIC_FILENAMES:
            payload = payloads[filename]
            validate_scientific_payload(filename, payload)
            output.write_new(filename, payload)
        execution_local = {
            "schema_version": "estimand-receipt-study-execution-local/v1",
            "mode": checked.mode,
            "replication_start": checked.replication_start,
            "replication_end_exclusive": checked.replication_end_exclusive,
            "replication_count": checked.replication_count,
            "execution_index": checked.execution_index,
        }
        output.write_new("execution-local.json", canonical_json_bytes(execution_local))
        output.revalidate()
        completed = True
    finally:
        if completed:
            output.close()
        else:
            output.abort()


def execute(config: object) -> int:
    """The sole compute/write entry point; validates authorization before work."""

    checked = _validate_run_configuration(config)
    require_no_network_capability()
    payloads = build_scientific_payloads(checked)
    _write_output(checked, payloads)
    return 0


def main(arguments: tuple[str, ...] | list[str] | None = None) -> int:
    """Run the closed CLI; confirmed registered execution exists only here."""

    parser = _argument_parser()
    namespace = parser.parse_args(arguments)
    if namespace.dry_run:
        return execute(_dry_configuration(parser, namespace))
    _validate_registered_cli(parser, namespace)
    validate_output_directory(namespace.output_dir)

    # This state and the registered execution closure are intentionally local to
    # the CLI invocation.  Module-level helpers are dry-only and cannot accept
    # this state or a registered configuration.
    cli_authorization = object()

    def execute_confirmed_registered() -> int:
        if cli_authorization is None:  # pragma: no cover - closure invariant
            raise RuntimeError("registered CLI authorization unavailable")
        replication_start = 0
        replication_end_exclusive = 2000
        replication_count = replication_end_exclusive - replication_start
        require_no_network_capability()
        scenarios = registered_scenarios()
        evaluator_profile = build_evaluator_profile()
        profile_text = evaluator_profile.canonical_bytes.decode("utf-8")
        payloads = {
            "design.json": canonical_json_bytes(
                {
                    "schema_version": "estimand-receipt-study-design/v2",
                    "simulation_schema_version": SCHEMA_VERSION,
                    "mode": "registered",
                    "replication_start": replication_start,
                    "replication_end_exclusive": replication_end_exclusive,
                    "replication_count": replication_count,
                    "confirmatory": True,
                    "scenario_census": [scenario.to_dict() for scenario in scenarios],
                    "configuration_order": list(CONFIGURATIONS),
                }
            ),
            "environment.json": canonical_json_bytes(_environment_payload()),
            "benchmark.json": canonical_json_bytes(_benchmark_payload()),
        }
        metric_rows: list[dict[str, object]] = []
        for scenario in scenarios:
            batch = simulate_batch(
                scenario,
                replication_start,
                replication_count,
                evaluator_profile=evaluator_profile,
            )
            metric_rows.extend(
                metric.to_dict() for metric in finalize_metrics((batch,))
            )
        payloads["metrics.jsonl"] = b"".join(
            canonical_json_bytes(row) for row in metric_rows
        )
        validate_scientific_payload("metrics.jsonl", payloads["metrics.jsonl"])
        receipt: dict[str, object] = {
            "schema_version": "estimand-receipt-study-receipt/v2",
            "mode": "registered",
            "replication_start": replication_start,
            "replication_end_exclusive": replication_end_exclusive,
            "replication_count": replication_count,
            "confirmatory": True,
            "source_sha256": dict(sorted(_source_hashes().items())),
            "evaluator_profile_sha256": hashlib.sha256(
                evaluator_profile.canonical_bytes
            ).hexdigest(),
            "evaluator_profile_bytes_sha256": hashlib.sha256(
                evaluator_profile.canonical_bytes
            ).hexdigest(),
            "scenario_count": len(scenarios),
            "scenario_order_sha256": hashlib.sha256(
                canonical_json_bytes([scenario.scenario_id for scenario in scenarios])
            ).hexdigest(),
            "scientific_files": {
                filename: hashlib.sha256(payloads[filename]).hexdigest()
                for filename in sorted(payloads)
            },
            "evaluator_profile_canonical_json": profile_text,
        }
        receipt["self_sha256"] = receipt_self_hash(receipt)
        payloads["receipt.json"] = canonical_json_bytes(receipt)
        validate_scientific_payload("receipt.json", payloads["receipt.json"])
        output = create_fresh_output_root(namespace.output_dir)
        completed = False
        try:
            for filename in SCIENTIFIC_FILENAMES:
                output.write_new(filename, payloads[filename])
            output.write_new(
                "execution-local.json",
                canonical_json_bytes(
                    {
                        "schema_version": "estimand-receipt-study-execution-local/v1",
                        "mode": "registered",
                        "replication_start": replication_start,
                        "replication_end_exclusive": replication_end_exclusive,
                        "replication_count": replication_count,
                        "execution_index": namespace.execution_index,
                    }
                ),
            )
            output.revalidate()
            completed = True
        finally:
            if completed:
                output.close()
            else:
                output.abort()
        return 0

    return execute_confirmed_registered()


if __name__ == "__main__":
    raise SystemExit(main())
