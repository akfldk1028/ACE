"""Freeze the source-recomputed ICLR 2027 method-lock candidate."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile
from typing import Sequence

from iclr2027.io import canonical_json
from iclr2027.method_lock import (
    build_method_lock_from_sources,
    candidate_file_bytes,
)
from iclr2027.secure_files import read_authenticated_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-receipt", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--pilot-gate", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _is_reparse_or_link(path: Path) -> bool:
    try:
        item_stat = os.lstat(path)
    except OSError:
        return False
    attributes = getattr(item_stat, "st_file_attributes", 0)
    return bool(path.is_symlink() or attributes & 0x400)


def _safe_output(path: Path) -> Path:
    absolute = path.absolute()
    for component in reversed((absolute, *absolute.parents)):
        if os.path.lexists(component) and _is_reparse_or_link(component):
            raise ValueError("method-lock output contains a symlink or reparse point")
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = parent.resolve(strict=True)
    if path.name != "method_lock_candidate.json":
        raise ValueError("method-lock output filename mismatch")
    return resolved_parent / path.name


def _write_new_or_identical(path: Path, content: bytes) -> None:
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
            if (
                not path.is_file()
                or read_authenticated_file(path, label="existing method-lock output")
                != content
            ):
                raise ValueError("output collision: existing bytes are not identical")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    candidate = build_method_lock_from_sources(
        design_receipt=args.design_receipt,
        snapshot=args.snapshot,
        pilot_gate=args.pilot_gate,
        dataset=args.dataset,
        models=args.models,
        replay=args.replay,
    )
    output = _safe_output(args.output)
    _write_new_or_identical(output, candidate_file_bytes(candidate))
    print(
        canonical_json(
            {
                "blockers": candidate["blockers"],
                "held_out_access_allowed": candidate["held_out_access_allowed"],
                "output": str(output),
                "receipt_sha256": candidate["receipt_sha256"],
                "schema_version": candidate["schema_version"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
