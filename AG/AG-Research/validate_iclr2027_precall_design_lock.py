"""Help/current-fixture CLI for the synthetic Task 6 pre-call lock."""

from __future__ import annotations

import argparse

from iclr2027.precall_design_lock import _canonical_fixture_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the synthetic-only Task 6 pre-call design-lock fixture. "
            "Authenticated/source modes require separately delivered context."
        )
    )
    parser.add_argument("--current-fixture", action="store_true")
    parser.add_argument("--authenticated", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--inventory")
    parser.add_argument("--data")
    parser.add_argument("--rates")
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    protected = (
        arguments.authenticated
        or arguments.source is not None
        or arguments.inventory is not None
        or arguments.data is not None
        or arguments.rates is not None
        or arguments.output is not None
    )
    if protected:
        raise SystemExit("NEEDS_CONTEXT: authenticated source authority is unavailable")
    if arguments.current_fixture:
        print(_canonical_fixture_json())
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
