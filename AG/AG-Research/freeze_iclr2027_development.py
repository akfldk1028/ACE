"""Freeze the validated ICLR 2027 development trajectory snapshot."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile
from typing import Sequence

from iclr2027.io import canonical_json
from iclr2027.trajectory_ingest import (
    build_development_snapshot_receipt,
    load_development_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--pilot-gate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _write_new_or_identical(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            if not path.is_file() or path.read_bytes() != content:
                raise ValueError("output collision: existing bytes are not identical")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = args.results.resolve()
    output = args.output.resolve()
    if output.is_relative_to(results):
        raise ValueError("snapshot output must be outside the source results directory")

    snapshot = load_development_snapshot(results, expected_count=450)
    receipt = build_development_snapshot_receipt(
        snapshot,
        results_dir=results,
        pilot_gate_path=args.pilot_gate,
    )
    _write_new_or_identical(
        output,
        (canonical_json(receipt) + "\n").encode("utf-8"),
    )
    print(f"snapshot_receipt={output}")
    print(f"transaction_count={len(snapshot.transactions)}")
    print(f"terminal_error_count={snapshot.terminal_error_count}")
    print(f"final_parse_complete_count={snapshot.final_parse_complete_count}")
    print(f"transaction_set_sha256={snapshot.transaction_set_sha256}")
    print(f"run_plan_sha256={snapshot.run_plan_sha256}")
    print(f"code_runtime_identity={snapshot.code_runtime_identity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
