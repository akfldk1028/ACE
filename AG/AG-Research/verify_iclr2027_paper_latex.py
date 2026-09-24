"""Command-line entry point for the fixed Task-11 paper verifier."""

import sys

from iclr2027.paper_latex_verification import (
    PaperLatexVerificationError,
    PaperStaticReceipt,
    verify_static_paper_latex,
)


def main(argv: list[str] | None = None) -> int:
    """Verify the fixed paper root under the exact no-argument contract."""

    arguments = sys.argv[1:] if argv is None else argv
    if arguments == ["--help"]:
        sys.stdout.buffer.write(b"usage: verify_iclr2027_paper_latex.py [--help]\n")
        return 0
    if arguments:
        sys.stderr.buffer.write(
            (
                '{"reason_code":"invalid_cli_argument",'
                '"schema_version":"ace.iclr2027.paper_latex_static_error.v1",'
                '"status":"error"}\n'
            ).encode("utf-8")
        )
        return 2
    try:
        receipt: PaperStaticReceipt = verify_static_paper_latex()
    except PaperLatexVerificationError as error:
        sys.stderr.buffer.write(
            (
                f'{{"reason_code":"{error.reason_code}",'
                '"schema_version":"ace.iclr2027.paper_latex_static_error.v1",'
                '"status":"error"}\n'
            ).encode("utf-8")
        )
        return 1
    sys.stdout.buffer.write((receipt.canonical_json() + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
