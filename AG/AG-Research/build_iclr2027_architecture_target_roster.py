"""Build one verified, offline ICLR 2027 architecture roster release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from dataclasses import fields
from pathlib import Path
from typing import Mapping, Sequence

from iclr2027.architecture_target_roster import (
    AdmissionBindingV1,
    BlindOverlapCheckV1,
    FreezeReceiptV2,
    IndependentReviewV1,
    LegacyBindingsV1,
    SourceCaptureV1,
    TargetRosterError,
    _canonical_set_sha256,
    canonical_sha256,
    verify_admission_inputs,
)
from iclr2027.io import write_json_atomic


_JSON_INPUTS = frozenset(
    {
        "legacy_bindings.json",
        "target_roster.json",
        "site_locators.json",
        "target_specs.json",
        "source_captures.json",
        "geometry_receipts.json",
        "blind_overlap_check.json",
        "independent_review.json",
    }
)
_SOURCE_OBJECTS = "source_objects"
_MOVEFILE_WRITE_THROUGH = 0x8
_ERROR_FILE_EXISTS = 80
_ERROR_ALREADY_EXISTS = 183


def _fail(code: str) -> None:
    raise TargetRosterError(code)


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _is_regular_file(path: Path) -> bool:
    if _is_reparse_point(path):
        return False
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode)


def _is_directory(path: Path) -> bool:
    return not _is_reparse_point(path) and stat.S_ISDIR(path.lstat().st_mode)


def _require_absolute_directory(path: Path, code: str) -> Path:
    if not path.is_absolute() or not path.exists() or not _is_directory(path):
        _fail(code)
    return path.resolve(strict=True)


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _read_json(path: Path) -> object:
    if not _is_regular_file(path):
        _fail("input_layout")

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError("duplicate_json_key")
            parsed[key] = value
        return parsed

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        _fail("input_json")


def _validate_input_layout(input_root: Path) -> Path:
    root = _require_absolute_directory(input_root, "input_root")
    entries = {entry.name: entry for entry in root.iterdir()}
    if set(entries) != _JSON_INPUTS | {_SOURCE_OBJECTS}:
        _fail("input_layout")
    for name in _JSON_INPUTS:
        if not _is_regular_file(entries[name]):
            _fail("input_layout")
    if not _is_directory(entries[_SOURCE_OBJECTS]):
        _fail("input_layout")
    for entry in entries[_SOURCE_OBJECTS].iterdir():
        if not _is_regular_file(entry):
            _fail("input_layout")
    return root


def _load_verified_inputs(
    input_root: Path,
) -> tuple[
    dict[str, object], AdmissionBindingV1, LegacyBindingsV1, IndependentReviewV1
]:
    root = _validate_input_layout(input_root)
    payloads = {name: _read_json(root / name) for name in _JSON_INPUTS}
    captures = payloads["source_captures.json"]
    if type(captures) is not list:
        _fail("source_capture_set_type")
    raw_bytes_by_source_id: dict[str, bytes] = {}
    expected_source_names: set[str] = set()
    for row in captures:
        if not isinstance(row, Mapping):
            _fail("source_capture_type")
        capture = SourceCaptureV1.from_dict(row)
        expected_source_names.add(f"{capture.sha256}.bin")
        source_path = root / _SOURCE_OBJECTS / f"{capture.sha256}.bin"
        if not _contains(
            (root / _SOURCE_OBJECTS).resolve(strict=True),
            source_path.resolve(strict=False),
        ):
            _fail("input_layout")
        if not _is_regular_file(source_path):
            _fail("source_capture_missing_or_changed")
        try:
            raw_bytes_by_source_id[capture.source_id] = source_path.read_bytes()
        except OSError:
            _fail("source_capture_missing_or_changed")
        raw_bytes = raw_bytes_by_source_id[capture.source_id]
        if (
            len(raw_bytes) != capture.byte_length
            or hashlib.sha256(raw_bytes).hexdigest() != capture.sha256
        ):
            _fail("source_capture_missing_or_changed")
    actual_source_names = {entry.name for entry in (root / _SOURCE_OBJECTS).iterdir()}
    if actual_source_names != expected_source_names:
        _fail("input_layout")
    roster = payloads["target_roster.json"]
    locators = payloads["site_locators.json"]
    target_specs = payloads["target_specs.json"]
    geometry_receipts = payloads["geometry_receipts.json"]
    blind_check = payloads["blind_overlap_check.json"]
    if not isinstance(blind_check, Mapping):
        _fail("blinded_membership_check")
    blind = BlindOverlapCheckV1.from_dict(blind_check)
    if (
        not isinstance(roster, Mapping)
        or type(locators) is not list
        or type(target_specs) is not list
        or type(geometry_receipts) is not list
    ):
        _fail("input_json")
    binding = verify_admission_inputs(
        roster=roster,
        target_specs=target_specs,
        locators=locators,
        source_captures=captures,
        raw_bytes_by_source_id=raw_bytes_by_source_id,
        geometry_receipts=geometry_receipts,
        blind_check=blind_check,
        protected_roster_commitment=blind.protected_roster_commitment,
    )
    legacy_raw = payloads["legacy_bindings.json"]
    review_raw = payloads["independent_review.json"]
    if not isinstance(legacy_raw, Mapping) or not isinstance(review_raw, Mapping):
        _fail("input_json")
    legacy = LegacyBindingsV1.from_dict(legacy_raw)
    review = IndependentReviewV1.from_dict(review_raw)
    admission_hash = canonical_sha256(
        {field.name: getattr(binding, field.name) for field in fields(binding)}
    )
    if (
        legacy.projection_identity_commitment
        != roster["projection_identity_commitment"]
        or review.reviewed_target_roster_sha256 != binding.target_roster_sha256
        or review.reviewed_admission_binding_sha256 != admission_hash
    ):
        _fail("release_binding")
    return payloads, binding, legacy, review


def _as_dict(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _make_receipt(
    payloads: Mapping[str, object],
    binding: AdmissionBindingV1,
    legacy: LegacyBindingsV1,
    review: IndependentReviewV1,
) -> FreezeReceiptV2:
    roster = payloads["target_roster.json"]
    if not isinstance(roster, Mapping):
        _fail("input_json")
    receipt: dict[str, object] = {
        "schema_version": "ace.iclr2027.architecture_freeze_receipt.v2",
        "registry_version": legacy.registry_version,
        "registry_core_sha256": legacy.registry_core_sha256,
        "projection_identity_commitment": legacy.projection_identity_commitment,
        "split_manifest_sha256": legacy.split_manifest_sha256,
        "public_registry_sha256": legacy.public_registry_sha256,
        "public_case_set_sha256": legacy.public_case_set_sha256,
        "site_locator_set_sha256": binding.locator_set_sha256,
        "public_site_set_sha256": _canonical_set_sha256(roster["sites"]),
        "public_target_set_sha256": _canonical_set_sha256(roster["targets"]),
        "source_capture_set_sha256": binding.source_capture_set_sha256,
        "target_spec_set_sha256": binding.target_spec_set_sha256,
        "geometry_receipt_set_sha256": binding.geometry_receipt_set_sha256,
        "target_roster_sha256": binding.target_roster_sha256,
        "new_site_count": 3,
        "new_target_count": 34,
        "allocation": (12, 11, 11),
        "combined_dev_site_count": 8,
        "combined_dev_target_count": 64,
        "blind_overlap_check_sha256": binding.blind_overlap_check_sha256,
        "independent_review_sha256": review.review_sha256,
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = canonical_sha256(
        receipt, omit=frozenset({"receipt_sha256"})
    )
    return FreezeReceiptV2.from_dict(receipt)


def _cleanup_temporary(temporary_root: Path, output_parent: Path) -> None:
    resolved_temporary = temporary_root.resolve(strict=False)
    if (
        resolved_temporary.parent != output_parent
        or not resolved_temporary.name.startswith(".")
    ):
        _fail("temporary_cleanup")
    if temporary_root.exists():
        shutil.rmtree(temporary_root)


def _windows_move_file_ex_w(
    source: str, destination: str, flags: int
) -> tuple[bool, int]:
    """Call MoveFileExW without granting replacement permission."""

    import ctypes

    move_file_ex_w = ctypes.WinDLL("kernel32", use_last_error=True).MoveFileExW
    move_file_ex_w.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
    move_file_ex_w.restype = ctypes.c_bool
    succeeded = bool(move_file_ex_w(source, destination, flags))
    return succeeded, int(ctypes.get_last_error())


def _publish_fresh_directory(temporary_root: Path, output_root: Path) -> None:
    """Durably publish a staging directory without replacing any destination."""

    if os.name != "nt":
        _fail("publication_unsupported")
    try:
        succeeded, error_code = _windows_move_file_ex_w(
            str(temporary_root), str(output_root), _MOVEFILE_WRITE_THROUGH
        )
    except (ImportError, OSError):
        _fail("publication_failed")
    if succeeded:
        return
    if (
        error_code in (_ERROR_FILE_EXISTS, _ERROR_ALREADY_EXISTS)
        or output_root.exists()
    ):
        _fail("publication_destination_exists")
    _fail("publication_failed")


def build_frozen_roster(input_root: Path, output_root: Path) -> FreezeReceiptV2:
    """Validate a complete offline intake and atomically publish one fresh release."""

    requested_output = Path(output_root)
    if (
        not requested_output.is_absolute()
        or requested_output.exists()
        or _is_reparse_point(requested_output)
    ):
        _fail("output_root")
    output_parent = _require_absolute_directory(requested_output.parent, "output_root")
    resolved_output = output_parent / requested_output.name
    resolved_input = _validate_input_layout(Path(input_root))
    if _contains(resolved_input, resolved_output) or _contains(
        resolved_output, resolved_input
    ):
        _fail("root_containment")
    payloads, binding, legacy, review = _load_verified_inputs(resolved_input)
    receipt = _make_receipt(payloads, binding, legacy, review)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{resolved_output.name}.", dir=output_parent)
    )
    try:
        public_root = temporary_root / "public"
        private_root = temporary_root / "private"
        write_json_atomic(
            public_root / "architecture_target_roster.json",
            payloads["target_roster.json"],
        )
        write_json_atomic(
            public_root / "architecture_freeze_receipt.v2.json", _as_dict(receipt)
        )
        for source_name, release_name in (
            ("site_locators.json", "site_locators.json"),
            ("target_specs.json", "target_specs.json"),
            ("source_captures.json", "source_captures.json"),
            ("geometry_receipts.json", "geometry_receipts.json"),
            ("blind_overlap_check.json", "blind_overlap_check.json"),
            ("independent_review.json", "independent_review.json"),
        ):
            write_json_atomic(private_root / release_name, payloads[source_name])
        _publish_fresh_directory(temporary_root, resolved_output)
    except BaseException:
        _cleanup_temporary(temporary_root, output_parent)
        raise
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    receipt = build_frozen_roster(args.input_root, args.output_root)
    print(f"receipt_sha256={receipt.receipt_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
