"""No-authority CLI for the Generation-0 Path-B positive-intake contract."""

from __future__ import annotations

import argparse
import json
import sys

from iclr2027 import path_b_positive_intake as intake


_ARGUMENT_ERROR = b"error: invalid arguments\n"


class _ClosedArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        sys.stderr.buffer.write(_ARGUMENT_ERROR)
        raise SystemExit(2)


def _fixed_formatter(prog: str) -> argparse.HelpFormatter:
    return argparse.HelpFormatter(prog, width=80)


def _parser() -> argparse.ArgumentParser:
    parser = _ClosedArgumentParser(
        prog="validate_iclr2027_path_b_positive_intake.py",
        description="Report Generation-0 Path-B positive-intake no-go status.",
        formatter_class=_fixed_formatter,
        allow_abbrev=False,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--current-status", action="store_true")
    group.add_argument("--list-negative-fixtures", action="store_true")
    return parser


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="strict", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="strict", newline="\n")
    parser = _parser()
    arguments = sys.argv[1:]
    if arguments not in (
        ["--current-status"],
        ["--list-negative-fixtures"],
        ["--help"],
        ["-h"],
    ):
        parser.error("")
    args = parser.parse_args(arguments)
    if args.current_status:
        output = intake.current_status().to_json()
    else:
        output = _canonical_json(
            [item.to_dict() for item in intake.negative_fixture_registry()]
        )
    sys.stdout.buffer.write(output.encode("ascii") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
