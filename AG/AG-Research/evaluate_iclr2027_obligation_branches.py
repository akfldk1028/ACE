"""Offline blind branch evaluation entry point (Phase 4A boundary only)."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate directly observed terminal obligation branches. "
            "Phase 4A exposes help only; source mode requires a later reviewed trust root."
        )
    )
    parser.add_argument("--mode", required=True, choices=("source",))
    parser.add_argument("--source-receipt", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _build_parser().parse_args(argv)
    # Deliberately before Path construction, stat, enumeration, or output creation.
    raise SystemExit("NEEDS_CONTEXT")


if __name__ == "__main__":
    raise SystemExit(main())
