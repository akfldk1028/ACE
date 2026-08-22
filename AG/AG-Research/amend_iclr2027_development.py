"""Apply the preregistered ICLR 2027 development-site amendment."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from iclr2027.development_amendment import (
    PROTOCOL_MAX_PARCEL_AREA_M2,
    amend_development_registry,
)
from iclr2027.io import write_json_atomic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--archived-registry", type=Path, required=True)
    parser.add_argument("--candidate-source", type=Path, required=True)
    parser.add_argument("--expected-archived-registry-sha256", required=True)
    parser.add_argument("--expected-candidate-source-sha256", required=True)
    parser.add_argument(
        "--max-parcel-area-m2",
        type=float,
        default=PROTOCOL_MAX_PARCEL_AREA_M2,
    )
    parser.add_argument("--expected-promoted-count", type=int, default=3)
    parser.add_argument("--declared-date", default="2026-08-19")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    amended = amend_development_registry(
        args.registry,
        args.archived_registry,
        args.candidate_source,
        expected_archived_registry_sha256=(
            args.expected_archived_registry_sha256
        ),
        expected_candidate_source_sha256=args.expected_candidate_source_sha256,
        output_registry_path=args.output,
        max_parcel_area_m2=args.max_parcel_area_m2,
        expected_promoted_count=args.expected_promoted_count,
        declared_date=args.declared_date,
    )
    write_json_atomic(args.output, amended)
    sites = amended["sites"]
    amendment = amended["selection"]["development_amendment"]
    development_count = sum(site.get("split") == "dev" for site in sites)
    test_count = sum(site.get("split") == "test" for site in sites)
    print(
        f"promoted_sites={len(amendment['promoted_pnus'])} "
        f"development_sites={development_count} test_sites={test_count} "
        f"registry_version={amended['version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
