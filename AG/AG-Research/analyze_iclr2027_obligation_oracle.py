"""Help-only Task 5 Phase-A CLI; source mode is not authorized."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("--inventory", "--source", "--data", "--output"):
        parser.add_argument(flag)
    arguments = parser.parse_args(argv)
    if any(value is not None for value in vars(arguments).values()):
        raise SystemExit("NEEDS_CONTEXT")
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
