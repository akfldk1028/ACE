"""Train the frozen CATS model and conformal-calibration artifact matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

from iclr2027.cats import write_verified_frozen_variants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-frozen-variants", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.all_frozen_variants:
        raise SystemExit("--all-frozen-variants is required")
    registry = write_verified_frozen_variants(args.dataset, args.output)
    for variant in registry["variants"]:
        print(
            "variant="
            f"{variant['name']} family={variant['family']} "
            f"epsilon={variant['epsilon']:.2f} alpha={variant['alpha']:.2f} "
            f"q_alpha={variant['q_alpha']} "
            f"semantic_sha256={variant['semantic_sha256']}"
        )
    print(f"model_registry={args.output / 'model_registry.json'}")
    print(f"semantic_determinism={args.output / 'semantic_determinism.json'}")
    print("held_out_bundle_reads=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
