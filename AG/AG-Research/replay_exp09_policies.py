"""Replay the frozen Task 6 policy registry on the development gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from iclr2027.io import canonical_json
from iclr2027.policy_replay import run_development_replay


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay the frozen Exp09 policies without model traffic."
    )
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    gate = run_development_replay(
        snapshot=args.snapshot,
        dataset=args.dataset,
        models=args.models,
        partition=args.partition,
        output=args.output,
    )
    print(
        canonical_json(
            {
                "failures": gate["failures"],
                "passed": gate["passed"],
                "receipt_sha256": gate["receipt_sha256"],
                "replay_rows_sha256": gate["replay_rows_sha256"],
                "row_census": gate["row_census"],
                "schema_version": gate["schema_version"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
