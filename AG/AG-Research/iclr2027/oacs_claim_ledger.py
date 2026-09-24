"""Canonical claim ledger contract for the MAS/OACS pre-outcome gate."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


CLAIM_STATUSES = (
    "executed",
    "frozen_diagnostic",
    "prospective",
    "blocked",
    "unsupported",
    "not_assessable",
)
CLAIM_TYPES = (
    "problem",
    "causal_mechanism",
    "policy_consequence",
    "domain_scope",
    "measurement",
    "limitation",
)
SEVERITIES = ("critical", "important", "minor")

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_TYPES = {
    "problem",
    "causal_mechanism",
    "policy_consequence",
    "domain_scope",
    "limitation",
}
_RECORD_KEYS = {
    "claim_id",
    "exact_span",
    "claim_type",
    "status",
    "evidence_sha256",
    "falsifier",
    "severity_if_wrong",
}
_ROOT_KEYS = {"design_sha256", "records"}


class ClaimLedgerError(ValueError):
    """Raised when a claim ledger violates its closed contract."""


def _require_hash(value: object, field: str) -> None:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise ClaimLedgerError(f"{field} must be a lowercase SHA-256")


def _require_nonempty_text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise ClaimLedgerError(f"{field} must be nonempty")


@dataclass(frozen=True)
class ClaimRecordV1:
    claim_id: str
    exact_span: str
    claim_type: str
    status: str
    evidence_sha256: tuple[str, ...]
    falsifier: str
    severity_if_wrong: str

    def __post_init__(self) -> None:
        if type(self.claim_id) is not str or not self.claim_id.startswith("claim:"):
            raise ClaimLedgerError("claim IDs must use the claim: prefix")
        if self.claim_id != self.claim_id.lower():
            raise ClaimLedgerError("claim IDs must be lowercase")
        _require_nonempty_text(self.exact_span, "exact_span")
        if self.claim_type not in CLAIM_TYPES:
            raise ClaimLedgerError("claim_type is not a closed enum")
        if self.status not in CLAIM_STATUSES:
            raise ClaimLedgerError("status is not a closed enum")
        if type(self.evidence_sha256) is not tuple:
            raise ClaimLedgerError("evidence_sha256 must be a tuple")
        for evidence_hash in self.evidence_sha256:
            _require_hash(evidence_hash, "evidence_sha256 entry")
        if tuple(sorted(self.evidence_sha256)) != self.evidence_sha256:
            raise ClaimLedgerError("evidence hashes must be byte-sorted")
        if len(set(self.evidence_sha256)) != len(self.evidence_sha256):
            raise ClaimLedgerError("evidence hashes must be unique")
        _require_nonempty_text(self.falsifier, "falsifier")
        if self.severity_if_wrong not in SEVERITIES:
            raise ClaimLedgerError("severity_if_wrong is not a closed enum")
        outcome_status = self.status in {"executed", "frozen_diagnostic"}
        if outcome_status and not self.evidence_sha256:
            raise ClaimLedgerError("executed claim evidence is required")
        if not outcome_status and self.evidence_sha256:
            raise ClaimLedgerError("prospective claim may not carry outcome evidence")


@dataclass(frozen=True)
class ClaimLedgerV1:
    design_sha256: str
    records: tuple[ClaimRecordV1, ...]

    def __post_init__(self) -> None:
        _require_hash(self.design_sha256, "design_sha256")
        if type(self.records) is not tuple:
            raise ClaimLedgerError("records must be a tuple")
        if any(not isinstance(record, ClaimRecordV1) for record in self.records):
            raise ClaimLedgerError("records must contain ClaimRecordV1 values")
        ids = [record.claim_id for record in self.records]
        if len(set(ids)) != len(ids):
            raise ClaimLedgerError("claim IDs must be unique")
        byte_sorted_ids = sorted(ids, key=lambda value: value.encode("utf-8"))
        if ids != byte_sorted_ids:
            raise ClaimLedgerError("claim IDs must be byte-sorted")
        present_types = {record.claim_type for record in self.records}
        missing = _REQUIRED_TYPES - present_types
        if missing:
            raise ClaimLedgerError("ledger missing required claim types")


def _record_payload(record: ClaimRecordV1) -> dict[str, Any]:
    return {
        "claim_id": record.claim_id,
        "exact_span": record.exact_span,
        "claim_type": record.claim_type,
        "status": record.status,
        "evidence_sha256": list(record.evidence_sha256),
        "falsifier": record.falsifier,
        "severity_if_wrong": record.severity_if_wrong,
    }


def _ledger_payload(ledger: ClaimLedgerV1) -> dict[str, Any]:
    if not isinstance(ledger, ClaimLedgerV1):
        raise ClaimLedgerError("ledger must be ClaimLedgerV1")
    return {
        "design_sha256": ledger.design_sha256,
        "records": [_record_payload(record) for record in ledger.records],
    }


def claim_ledger_bytes(ledger: ClaimLedgerV1) -> bytes:
    """Return the one-LF canonical UTF-8 JSON representation of ``ledger``."""

    try:
        raw = json.dumps(
            _ledger_payload(ledger),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (UnicodeError, TypeError, ValueError) as exc:
        raise ClaimLedgerError("ledger cannot be encoded as UTF-8 JSON") from exc
    return raw + b"\n"


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ClaimLedgerError("duplicate JSON key")
        value[key] = item
    return value


def _parse_record(value: object) -> ClaimRecordV1:
    if type(value) is not dict:
        raise ClaimLedgerError("record must be a JSON object")
    if set(value) != _RECORD_KEYS:
        raise ClaimLedgerError("row keys do not match closed schema")
    evidence = value["evidence_sha256"]
    if type(evidence) is not list:
        raise ClaimLedgerError("evidence_sha256 must be a JSON array")
    return ClaimRecordV1(
        claim_id=value["claim_id"],
        exact_span=value["exact_span"],
        claim_type=value["claim_type"],
        status=value["status"],
        evidence_sha256=tuple(evidence),
        falsifier=value["falsifier"],
        severity_if_wrong=value["severity_if_wrong"],
    )


def verify_claim_ledger_bytes(raw: bytes) -> ClaimLedgerV1:
    """Parse and verify canonical ledger bytes, rejecting any byte mutation."""

    if type(raw) is not bytes:
        raise ClaimLedgerError("raw ledger must be bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ClaimLedgerError(f"invalid JSON constant: {value}")
            ),
        )
    except ClaimLedgerError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ClaimLedgerError("invalid ledger JSON") from exc
    if type(payload) is not dict or set(payload) != _ROOT_KEYS:
        raise ClaimLedgerError("root keys do not match closed schema")
    records = payload["records"]
    if type(records) is not list:
        raise ClaimLedgerError("records must be a JSON array")
    ledger = ClaimLedgerV1(
        design_sha256=payload["design_sha256"],
        records=tuple(_parse_record(record) for record in records),
    )
    if raw != claim_ledger_bytes(ledger):
        raise ClaimLedgerError("ledger bytes are not canonical JSON")
    return ledger


__all__ = [
    "CLAIM_STATUSES",
    "CLAIM_TYPES",
    "SEVERITIES",
    "ClaimLedgerError",
    "ClaimLedgerV1",
    "ClaimRecordV1",
    "claim_ledger_bytes",
    "verify_claim_ledger_bytes",
]
