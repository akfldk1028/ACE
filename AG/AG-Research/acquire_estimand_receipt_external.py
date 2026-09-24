"""Acquire the pinned AgentTelemetry source without executing upstream code."""

from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import urllib.error
import urllib.request

from iclr2027.estimand_receipt_external import (
    ExternalSourceReceipt,
    EXPECTED_LICENSE_BYTES,
    EXPECTED_LICENSE_SHA256,
    EXPECTED_SOURCE_BYTES,
    EXPECTED_SOURCE_SHA256,
    LICENSE_URL,
    SOURCE_COMMIT,
    SOURCE_URL,
    validate_raw_source_identity,
)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise urllib.error.HTTPError(req.full_url, code, "redirects are prohibited", headers, fp)


def _download_exact(url: str) -> bytes:
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "estimand-receipt-intake/1"})
    with opener.open(request, timeout=30) as response:
        if response.geturl() != url:
            raise ValueError("redirects are prohibited")
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir: Path = args.output_dir
    try:
        os.mkdir(output_dir)
    except FileExistsError as error:
        raise SystemExit("output directory must not already exist") from error

    try:
        source = _download_exact(SOURCE_URL)
        license_bytes = _download_exact(LICENSE_URL)
        validate_raw_source_identity(
            source, license_bytes,
            expected_source_bytes=EXPECTED_SOURCE_BYTES,
            expected_source_sha256=EXPECTED_SOURCE_SHA256,
            expected_license_bytes=EXPECTED_LICENSE_BYTES,
            expected_license_sha256=EXPECTED_LICENSE_SHA256,
        )
        receipt = ExternalSourceReceipt.from_bytes(
            source, license_bytes, url=SOURCE_URL, commit_sha=SOURCE_COMMIT,
            retrieved_on=date.today(),
        )
        (output_dir / "traces_v1.jsonl").open("xb").write(source)
        (output_dir / "LICENSE").open("xb").write(license_bytes)
        (output_dir / "external_source_receipt.json").open("xb").write(receipt.canonical_json_bytes())
    except Exception:
        # The exclusively-created directory is deliberately retained as an
        # inadmissible intake marker; no alternate data source is attempted.
        raise

    print(
        f"frozen AgentTelemetry: {receipt.source_rows} rows, {receipt.license_spdx}, "
        f"source_sha256={receipt.source_sha256}, license_sha256={receipt.license_sha256}, "
        f"canonical_rows_sha256={receipt.canonical_rows_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
