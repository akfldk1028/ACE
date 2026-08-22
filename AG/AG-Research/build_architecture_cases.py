"""Build architecture-domain ICLR 2027 evidence cases from frozen ARR artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from iclr2027.dataset import (
    build_cases,
    freeze_site_registry,
    registry_expected_bundle_counts,
    update_split_manifest,
    verify_frozen_registry,
    write_case_bundle,
)
from iclr2027.release import load_projection_identity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/iclr2027/site_registry.json"),
        help="frozen site registry JSON",
    )
    parser.add_argument("--split", choices=("dev", "test"))
    parser.add_argument(
        "--condition",
        choices=("native", "challenged"),
        default="native",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/iclr2027/cases"),
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="allow fixture/smoke bundles smaller than the frozen research split",
    )
    parser.add_argument("--split-manifest", type=Path)
    parser.add_argument(
        "--projection-identity",
        type=Path,
        default=Path("data/iclr2027/projection_identity.private.json"),
        help="private caller-supplied projection identity sidecar",
    )
    parser.add_argument(
        "--public-registry",
        type=Path,
        default=Path("data/iclr2027/site_registry.public.json"),
    )
    parser.add_argument(
        "--freeze-receipt",
        type=Path,
        default=Path("data/iclr2027/freeze_receipt.json"),
    )
    parser.add_argument("--freeze-registry", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    split_manifest_path = (
        args.split_manifest
        if args.split_manifest is not None
        else args.registry.parent / "split_manifest.json"
    )
    projection_identity = load_projection_identity(args.projection_identity)
    if args.audit_only:
        manifest = verify_frozen_registry(
            args.registry,
            split_manifest_path=split_manifest_path,
            projection_identity=projection_identity,
            public_registry_path=args.public_registry,
            freeze_receipt_path=args.freeze_receipt,
        )
        print(f"verified_bundles={len(manifest['bundles'])}")
        return 0
    if args.split is None:
        raise ValueError("--split is required unless --audit-only is used")
    registry_payload = json.loads(args.registry.read_text(encoding="utf-8"))
    if registry_payload.get("frozen") is True:
        raise ValueError(
            "site registry is frozen; create a new registry version before rebuilding cases"
        )
    result = build_cases(
        args.registry,
        split=args.split,
        condition=args.condition,
    )
    expected_count = registry_expected_bundle_counts(registry_payload)[
        f"{args.split}.{args.condition}"
    ]
    if not args.allow_partial and len(result.packets) != expected_count:
        raise ValueError(
            f"expected {expected_count} cases for split={args.split}, "
            f"built {len(result.packets)}; use --allow-partial only for tests/smoke runs"
        )
    manifest = write_case_bundle(
        result,
        output_dir=args.output_dir,
        projection_identity=projection_identity,
    )
    bundle_manifest_path = (
        args.output_dir / f"{args.split}.{args.condition}.manifest.json"
    )
    update_split_manifest(
        manifest,
        bundle_manifest_path=bundle_manifest_path,
        split_manifest_path=split_manifest_path,
    )
    if args.freeze_registry:
        freeze_site_registry(
            args.registry,
            split_manifest_path=split_manifest_path,
            projection_identity=projection_identity,
            public_registry_path=args.public_registry,
            freeze_receipt_path=args.freeze_receipt,
        )
    print(
        f"built {manifest['case_count']} {args.condition} cases "
        f"for split={args.split} in {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
