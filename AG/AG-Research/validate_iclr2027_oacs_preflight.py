"""Read-only validation of one frozen MAS/OACS preflight package."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys

from build_iclr2027_oacs_preoutcome import (
    PreflightCliError,
    _require_created_package_sealed,
    _require_safe_windows_privileges,
    _reject_duplicate_options,
    _verify_created_package,
    _write_stdout,
    read_package_inputs,
)
from iclr2027.oacs_preflight import (
    PreflightError,
    validate_preflight_receipt_bytes,
)
from iclr2027.oacs_preflight_v2 import validate_preflight_receipt_v2_bytes


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PreflightCliError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--preflight-version",
        choices=("v1", "v2"),
        default="v1",
    )
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--governing-design-sha256", required=True)
    parser.add_argument("--approval-trust-root-sha256")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        _reject_duplicate_options(arguments)
        namespace = _parser().parse_args(arguments)
        _require_safe_windows_privileges()
        with read_package_inputs(
            namespace.input_root,
            expected_governing_design_sha256=namespace.governing_design_sha256,
            expected_approval_trust_root_sha256=(namespace.approval_trust_root_sha256),
            preflight_version=namespace.preflight_version,
        ) as (inputs, receipt_raw, package):
            if namespace.preflight_version == "v2":
                validate_preflight_receipt_v2_bytes(receipt_raw, inputs)
            else:
                validate_preflight_receipt_bytes(receipt_raw, inputs)
            _verify_created_package(package)
            _require_created_package_sealed(package)
            _write_stdout(receipt_raw)
    except (OSError, PreflightCliError, PreflightError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
