"""Emit a zero-generation OACS backend audit from supplied local evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from iclr2027.oacs_backend_audit import (
    BackendAuditConfigV1,
    MetadataProbe,
    audit_backend,
    parse_canonical_config_bytes,
)


class EvidenceProbe:
    """In-memory evidence only; it never runs commands or contacts an account."""

    def __init__(self, evidence: dict[str, object]):
        if set(evidence) != {"version", "auth_mode", "quota_mode"}:
            raise ValueError("probe evidence has unexpected or missing fields")
        if any(type(value) is not str for value in evidence.values()):
            raise TypeError("probe evidence values must be exactly strings")
        self._evidence = evidence

    def version(self) -> str:
        return self._evidence["version"]  # type: ignore[return-value]

    def auth_mode(self) -> str:
        return self._evidence["auth_mode"]  # type: ignore[return-value]

    def quota_mode(self) -> str:
        return self._evidence["quota_mode"]  # type: ignore[return-value]


def _parse_canonical_evidence(payload: bytes) -> EvidenceProbe:
    try:
        text = payload.decode("utf-8")
        evidence = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("probe evidence must be UTF-8 JSON") from exc
    if type(evidence) is not dict:
        raise TypeError("probe evidence must be exactly a JSON object")
    probe = EvidenceProbe(evidence)
    expected = (
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    if payload != expected:
        raise ValueError("probe evidence JSON is not canonical")
    return probe


def _read_config(path: str) -> BackendAuditConfigV1:
    return parse_canonical_config_bytes(Path(path).read_bytes())


def _read_probe_evidence(path: str) -> MetadataProbe:
    return _parse_canonical_evidence(Path(path).read_bytes())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", required=True, help="canonical backend-audit configuration JSON"
    )
    parser.add_argument(
        "--probe-evidence",
        required=True,
        help="canonical, already-observed metadata JSON",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        audit = audit_backend(
            _read_config(args.config), _read_probe_evidence(args.probe_evidence)
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"backend audit input error: {exc}", file=sys.stderr)
        return 2
    payload = audit.canonical_bytes()
    stream = getattr(sys.stdout, "buffer", None)
    if stream is None:
        sys.stdout.write(payload.decode("utf-8"))
    else:
        stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
