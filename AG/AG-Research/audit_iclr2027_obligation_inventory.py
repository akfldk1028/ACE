"""Write the fixed current-state Gate 0 inventory publication pair."""

from __future__ import annotations

import argparse
from pathlib import Path

from iclr2027.gate0_sources import GATE0_TOP_SOURCES, Gate0RawSourcePaths
from iclr2027.obligation_inventory import (
    build_gate0_inventory,
    gate0_expected_publication_receipt_file_sha256,
    publish_gate0_inventory,
    verify_gate0_publication,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("source",), required=True)
    args = parser.parse_args(argv)
    del args
    raw = Gate0RawSourcePaths(*(spec.relative_path for spec in GATE0_TOP_SOURCES))
    inventory = build_gate0_inventory(sources=raw)
    expected_receipt_file_sha256 = gate0_expected_publication_receipt_file_sha256(
        inventory
    )
    root = Path(__file__).resolve().parent
    output = root / "results/exp10_obligation"
    receipt_path = publish_gate0_inventory(inventory, output_dir=output)
    verified = verify_gate0_publication(
        output / "stage0_inventory.json",
        receipt_path,
        expected_receipt_file_sha256=expected_receipt_file_sha256,
    )
    print(verified.status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
