"""Fixed-argument CLI for the synthetic Task 7 acquisition status."""

from __future__ import annotations

import argparse

from iclr2027 import external_authority_acquisition as acquisition


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report synthetic-only external-authority acquisition status."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--current-status", action="store_true")
    group.add_argument("--list-negative-fixtures", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.current_status:
        print(acquisition.validate_synthetic_external_authority_acquisition().to_json())
    else:
        values = [item.to_dict() for item in acquisition.negative_fixture_registry()]
        print(acquisition._canonical_json(values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
