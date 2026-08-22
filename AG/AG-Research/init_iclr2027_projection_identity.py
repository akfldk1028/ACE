"""Initialize the private opaque-identity sidecar used by ICLR 2027 bundles."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from iclr2027.release import create_projection_identity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/iclr2027/projection_identity.private.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    identity = create_projection_identity(args.output)
    print(f"path={args.output}")
    print(f"identity_commitment={identity.commitment}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
