"""Canonical isolated-review contracts for the MAS/OACS pre-outcome gate."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any

from iclr2027.oacs_claim_ledger import ClaimLedgerV1, claim_ledger_bytes


ROLES = (
    "problem_novelty",
    "causal_statistics",
    "experiment_reproducibility",
    "adversarial_falsifier",
)
VERDICTS = ("ACCEPT", "REVISE", "REJECT")
FINDING_SEVERITIES = ("C", "I", "M")
ICLR_GUIDELINES_URL = "https://iclr.cc/Conferences/2027/ReviewerGuidelines"
ICLR_QUESTIONS = (
    "What precise problem does the paper address?",
    "Is the approach motivated and situated in prior work?",
    "Are the claims correct and rigorously supported?",
    "Does the work contribute significant knowledge or value?",
)
FROZEN_PREAMBLE = (
    "Read only the listed frozen inputs. Do not inspect another review. State the\n"
    "paper's exact problem and contribution before judging it. Cite an exact claim\n"
    "ID and evidence hash for every decision-relevant finding. Answer the four ICLR\n"
    "questions. Give the strongest accept case, strongest reject case, an explicit\n"
    "falsifier, the smallest correction, and one of ACCEPT, REVISE, or REJECT. Do\n"
    "not infer completed results from prospective work and do not use a score from\n"
    "another reviewer."
)
ROLE_SUFFIXES = {
    "problem_novelty": "closest primary work, narrow novelty, significance.",
    "causal_statistics": (
        "units, treatment, randomization, estimand, interference, clustering, "
        "multiplicity, missingness, power."
    ),
    "experiment_reproducibility": (
        "rights, split, leakage, parity, execution binding, retry/cost accounting, "
        "reconstruction."
    ),
    "adversarial_falsifier": (
        "relabel, misbind, denominator, selective exclusion, post-hoc rescue, "
        "prospective-to-executed promotion."
    ),
}

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_FAILURE_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_ASSIGNMENT_KEYS = {
    "assignment_sha256",
    "claim_ledger_sha256",
    "iclr_guidelines_url",
    "iclr_questions",
    "prompt",
    "role",
    "source_sha256",
    "visible_inputs",
}
_PACKAGE_KEYS = {
    "assignments",
    "claim_ids",
    "claim_ledger_sha256",
    "package_sha256",
    "source_sha256",
}
_FINDING_KEYS = {
    "claim_id",
    "evidence_sha256",
    "failure_code",
    "falsifier_result",
    "resolved",
    "severity",
}
_REVIEW_KEYS = {"assignment_sha256", "findings", "review_sha256", "role", "verdict"}


class ReviewHarnessError(ValueError):
    """Raised when an isolated review contract is malformed or untrusted."""


def _require_hash(value: object, field: str) -> None:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise ReviewHarnessError(f"{field} must be a lowercase SHA-256")


def _require_nonempty_text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise ReviewHarnessError(f"{field} must be nonempty")


def _canonical_bytes(payload: object) -> bytes:
    try:
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, UnicodeError, ValueError) as exc:
        raise ReviewHarnessError("value cannot be encoded as UTF-8 JSON") from exc


def _hash_payload(payload: object) -> str:
    return sha256(_canonical_bytes(payload)).hexdigest()


def _require_sorted_hashes(value: object, field: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ReviewHarnessError(f"{field} must be a tuple")
    for item in value:
        _require_hash(item, f"{field} entry")
    if tuple(sorted(value)) != value or len(set(value)) != len(value):
        raise ReviewHarnessError(f"{field} must be sorted and unique")
    return value


def _visible_inputs(claim_ledger_sha256: str, source_sha256: tuple[str, ...]) -> str:
    return (
        f"claim_ledger_sha256={claim_ledger_sha256}\n"
        f"frozen_source_sha256={','.join(source_sha256)}"
    )


def _prompt(role: str) -> str:
    return FROZEN_PREAMBLE + "\n\n" + ROLE_SUFFIXES[role]


@dataclass(frozen=True)
class ReviewAssignmentV1:
    role: str
    claim_ledger_sha256: str
    source_sha256: tuple[str, ...]
    iclr_guidelines_url: str
    iclr_questions: tuple[str, ...]
    visible_inputs: str
    prompt: str
    assignment_sha256: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ReviewHarnessError("role is not a closed enum")
        _require_hash(self.claim_ledger_sha256, "claim_ledger_sha256")
        _require_sorted_hashes(self.source_sha256, "source_sha256")
        if self.iclr_guidelines_url != ICLR_GUIDELINES_URL:
            raise ReviewHarnessError("ICLR guidelines URL is not frozen")
        if self.iclr_questions != ICLR_QUESTIONS:
            raise ReviewHarnessError("ICLR questions are not frozen")
        if (
            self.visible_inputs
            != _visible_inputs(self.claim_ledger_sha256, self.source_sha256)
            or "review" in self.visible_inputs.lower()
        ):
            raise ReviewHarnessError("visible inputs violate role isolation")
        if self.prompt != _prompt(self.role):
            raise ReviewHarnessError("assignment prompt is not frozen")
        _require_hash(self.assignment_sha256, "assignment_sha256")
        if self.assignment_sha256 != _hash_payload(_assignment_body(self)):
            raise ReviewHarnessError("assignment self-hash does not match")


def _assignment_body(assignment: ReviewAssignmentV1) -> dict[str, Any]:
    return {
        "role": assignment.role,
        "claim_ledger_sha256": assignment.claim_ledger_sha256,
        "source_sha256": list(assignment.source_sha256),
        "iclr_guidelines_url": assignment.iclr_guidelines_url,
        "iclr_questions": list(assignment.iclr_questions),
        "visible_inputs": assignment.visible_inputs,
        "prompt": assignment.prompt,
    }


def _lock_assignment(
    role: str, claim_ledger_sha256: str, source_sha256: tuple[str, ...]
) -> ReviewAssignmentV1:
    body = {
        "role": role,
        "claim_ledger_sha256": claim_ledger_sha256,
        "source_sha256": list(source_sha256),
        "iclr_guidelines_url": ICLR_GUIDELINES_URL,
        "iclr_questions": list(ICLR_QUESTIONS),
        "visible_inputs": _visible_inputs(claim_ledger_sha256, source_sha256),
        "prompt": _prompt(role),
    }
    return ReviewAssignmentV1(
        role=role,
        claim_ledger_sha256=claim_ledger_sha256,
        source_sha256=source_sha256,
        iclr_guidelines_url=ICLR_GUIDELINES_URL,
        iclr_questions=ICLR_QUESTIONS,
        visible_inputs=body["visible_inputs"],
        prompt=body["prompt"],
        assignment_sha256=_hash_payload(body),
    )


@dataclass(frozen=True)
class FindingV1:
    failure_code: str
    severity: str
    claim_id: str
    evidence_sha256: str
    falsifier_result: str
    resolved: bool

    def __post_init__(self) -> None:
        if (
            type(self.failure_code) is not str
            or _FAILURE_CODE_RE.fullmatch(self.failure_code) is None
        ):
            raise ReviewHarnessError("failure_code is not a closed token")
        if self.severity not in FINDING_SEVERITIES:
            raise ReviewHarnessError("finding severity is not a closed enum")
        if (
            type(self.claim_id) is not str
            or not self.claim_id.startswith("claim:")
            or self.claim_id != self.claim_id.lower()
        ):
            raise ReviewHarnessError("claim IDs must use the lowercase claim: prefix")
        _require_hash(self.evidence_sha256, "evidence_sha256")
        _require_nonempty_text(self.falsifier_result, "falsifier_result")
        if type(self.resolved) is not bool:
            raise ReviewHarnessError("resolved must be a native boolean")


def _finding_payload(finding: FindingV1) -> dict[str, Any]:
    return {
        "failure_code": finding.failure_code,
        "severity": finding.severity,
        "claim_id": finding.claim_id,
        "evidence_sha256": finding.evidence_sha256,
        "falsifier_result": finding.falsifier_result,
        "resolved": finding.resolved,
    }


@dataclass(frozen=True)
class ReviewRecordV1:
    role: str
    assignment_sha256: str
    verdict: str
    findings: tuple[FindingV1, ...]
    review_sha256: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ReviewHarnessError("role is not a closed enum")
        _require_hash(self.assignment_sha256, "assignment_sha256")
        if self.verdict not in VERDICTS:
            raise ReviewHarnessError("verdict is not a closed enum")
        if type(self.findings) is not tuple or any(
            not isinstance(finding, FindingV1) for finding in self.findings
        ):
            raise ReviewHarnessError("findings must contain FindingV1 values")
        _require_hash(self.review_sha256, "review_sha256")
        if self.review_sha256 != _hash_payload(_review_body(self)):
            raise ReviewHarnessError("review self-hash does not match")


def _review_body(review: ReviewRecordV1) -> dict[str, Any]:
    return {
        "role": review.role,
        "assignment_sha256": review.assignment_sha256,
        "verdict": review.verdict,
        "findings": [_finding_payload(finding) for finding in review.findings],
    }


def lock_review_record(
    *, role: str, assignment_sha256: str, verdict: str, findings: tuple[FindingV1, ...]
) -> ReviewRecordV1:
    """Create a self-hashed review record without seeing any other review."""

    body = {
        "role": role,
        "assignment_sha256": assignment_sha256,
        "verdict": verdict,
        "findings": [_finding_payload(finding) for finding in findings],
    }
    return ReviewRecordV1(
        role=role,
        assignment_sha256=assignment_sha256,
        verdict=verdict,
        findings=findings,
        review_sha256=_hash_payload(body),
    )


@dataclass(frozen=True)
class ReviewPackageV1:
    claim_ledger_sha256: str
    source_sha256: tuple[str, ...]
    claim_ids: tuple[str, ...]
    assignments: tuple[ReviewAssignmentV1, ...]
    package_sha256: str

    def __post_init__(self) -> None:
        _require_hash(self.claim_ledger_sha256, "claim_ledger_sha256")
        _require_sorted_hashes(self.source_sha256, "source_sha256")
        if type(self.claim_ids) is not tuple:
            raise ReviewHarnessError("claim_ids must be a tuple")
        if (
            any(
                type(claim_id) is not str
                or not claim_id.startswith("claim:")
                or claim_id != claim_id.lower()
                for claim_id in self.claim_ids
            )
            or tuple(sorted(self.claim_ids, key=lambda item: item.encode("utf-8")))
            != self.claim_ids
            or len(set(self.claim_ids)) != len(self.claim_ids)
        ):
            raise ReviewHarnessError(
                "claim IDs must be unique lowercase byte-sorted values"
            )
        if type(self.assignments) is not tuple or any(
            not isinstance(assignment, ReviewAssignmentV1)
            for assignment in self.assignments
        ):
            raise ReviewHarnessError(
                "assignments must contain ReviewAssignmentV1 values"
            )
        if tuple(assignment.role for assignment in self.assignments) != ROLES:
            raise ReviewHarnessError("assignment role order is not frozen")
        if any(
            assignment.claim_ledger_sha256 != self.claim_ledger_sha256
            or assignment.source_sha256 != self.source_sha256
            for assignment in self.assignments
        ):
            raise ReviewHarnessError("assignment frozen inputs do not match package")
        _require_hash(self.package_sha256, "package_sha256")
        if self.package_sha256 != _hash_payload(_package_body(self)):
            raise ReviewHarnessError("package self-hash does not match")


def _package_body(package: ReviewPackageV1) -> dict[str, Any]:
    return {
        "claim_ledger_sha256": package.claim_ledger_sha256,
        "source_sha256": list(package.source_sha256),
        "claim_ids": list(package.claim_ids),
        "assignments": [
            {
                **_assignment_body(assignment),
                "assignment_sha256": assignment.assignment_sha256,
            }
            for assignment in package.assignments
        ],
    }


def build_review_package(
    ledger: ClaimLedgerV1, source_hashes: tuple[str, ...]
) -> ReviewPackageV1:
    """Freeze four isolated assignments from the claim ledger and source pins."""

    if not isinstance(ledger, ClaimLedgerV1):
        raise ReviewHarnessError("ledger must be ClaimLedgerV1")
    source_sha256 = _require_sorted_hashes(source_hashes, "source_hashes")
    ledger_evidence = {
        evidence_hash
        for record in ledger.records
        for evidence_hash in record.evidence_sha256
    }
    if not ledger_evidence.issubset(set(source_sha256)):
        raise ReviewHarnessError("frozen source hashes omit claim evidence")
    claim_ledger_sha256 = sha256(claim_ledger_bytes(ledger)).hexdigest()
    assignments = tuple(
        _lock_assignment(role, claim_ledger_sha256, source_sha256) for role in ROLES
    )
    claim_ids = tuple(record.claim_id for record in ledger.records)
    body = {
        "claim_ledger_sha256": claim_ledger_sha256,
        "source_sha256": list(source_sha256),
        "claim_ids": list(claim_ids),
        "assignments": [
            {
                **_assignment_body(assignment),
                "assignment_sha256": assignment.assignment_sha256,
            }
            for assignment in assignments
        ],
    }
    return ReviewPackageV1(
        claim_ledger_sha256=claim_ledger_sha256,
        source_sha256=source_sha256,
        claim_ids=claim_ids,
        assignments=assignments,
        package_sha256=_hash_payload(body),
    )


def _package_payload(package: ReviewPackageV1) -> dict[str, Any]:
    body = _package_body(package)
    return {**body, "package_sha256": package.package_sha256}


def review_package_bytes(package: ReviewPackageV1) -> bytes:
    if not isinstance(package, ReviewPackageV1):
        raise ReviewHarnessError("package must be ReviewPackageV1")
    return _canonical_bytes(_package_payload(package))


def locked_review_bytes(review: ReviewRecordV1) -> bytes:
    if not isinstance(review, ReviewRecordV1):
        raise ReviewHarnessError("review must be ReviewRecordV1")
    return _canonical_bytes(
        {**_review_body(review), "review_sha256": review.review_sha256}
    )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewHarnessError("duplicate JSON key")
        result[key] = value
    return result


def _load_json(raw: bytes, label: str) -> object:
    if type(raw) is not bytes:
        raise ReviewHarnessError(f"raw {label} must be bytes")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ReviewHarnessError(f"invalid JSON constant: {value}")
            ),
        )
    except ReviewHarnessError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ReviewHarnessError(f"invalid {label} JSON") from exc


def _parse_assignment(value: object) -> ReviewAssignmentV1:
    if type(value) is not dict or set(value) != _ASSIGNMENT_KEYS:
        raise ReviewHarnessError("assignment keys do not match closed schema")
    if (
        type(value["source_sha256"]) is not list
        or type(value["iclr_questions"]) is not list
    ):
        raise ReviewHarnessError("assignment arrays must be JSON arrays")
    return ReviewAssignmentV1(
        role=value["role"],
        claim_ledger_sha256=value["claim_ledger_sha256"],
        source_sha256=tuple(value["source_sha256"]),
        iclr_guidelines_url=value["iclr_guidelines_url"],
        iclr_questions=tuple(value["iclr_questions"]),
        visible_inputs=value["visible_inputs"],
        prompt=value["prompt"],
        assignment_sha256=value["assignment_sha256"],
    )


def _parse_finding(value: object) -> FindingV1:
    if type(value) is not dict or set(value) != _FINDING_KEYS:
        raise ReviewHarnessError("finding keys do not match closed schema")
    return FindingV1(
        failure_code=value["failure_code"],
        severity=value["severity"],
        claim_id=value["claim_id"],
        evidence_sha256=value["evidence_sha256"],
        falsifier_result=value["falsifier_result"],
        resolved=value["resolved"],
    )


def _parse_review(value: object) -> ReviewRecordV1:
    if type(value) is not dict or set(value) != _REVIEW_KEYS:
        raise ReviewHarnessError("review keys do not match closed schema")
    if type(value["findings"]) is not list:
        raise ReviewHarnessError("findings must be a JSON array")
    return ReviewRecordV1(
        role=value["role"],
        assignment_sha256=value["assignment_sha256"],
        verdict=value["verdict"],
        findings=tuple(_parse_finding(finding) for finding in value["findings"]),
        review_sha256=value["review_sha256"],
    )


def verify_review_package_bytes(raw: bytes) -> ReviewPackageV1:
    """Verify closed-schema, canonical package bytes and every assignment lock."""

    payload = _load_json(raw, "review package")
    if type(payload) is not dict or set(payload) != _PACKAGE_KEYS:
        raise ReviewHarnessError("package keys do not match closed schema")
    if (
        type(payload["source_sha256"]) is not list
        or type(payload["claim_ids"]) is not list
        or type(payload["assignments"]) is not list
    ):
        raise ReviewHarnessError("package arrays must be JSON arrays")
    package = ReviewPackageV1(
        claim_ledger_sha256=payload["claim_ledger_sha256"],
        source_sha256=tuple(payload["source_sha256"]),
        claim_ids=tuple(payload["claim_ids"]),
        assignments=tuple(_parse_assignment(item) for item in payload["assignments"]),
        package_sha256=payload["package_sha256"],
    )
    if raw != review_package_bytes(package):
        raise ReviewHarnessError("review package bytes are not canonical JSON")
    return package


def verify_locked_review_bytes(raw: bytes) -> ReviewRecordV1:
    """Verify closed-schema, canonical bytes for one self-locked review."""

    review = _parse_review(_load_json(raw, "locked review"))
    if raw != locked_review_bytes(review):
        raise ReviewHarnessError("locked review bytes are not canonical JSON")
    return review


def _verify_review_order(reviews: object) -> tuple[ReviewRecordV1, ...]:
    if type(reviews) is not tuple or any(
        not isinstance(review, ReviewRecordV1) for review in reviews
    ):
        raise ReviewHarnessError("reviews must contain ReviewRecordV1 values")
    if tuple(review.role for review in reviews) != ROLES:
        raise ReviewHarnessError("review role order is not frozen")
    return reviews


def verify_locked_reviews(
    package: ReviewPackageV1, reviews: tuple[ReviewRecordV1, ...]
) -> tuple[ReviewRecordV1, ...]:
    """Verify assignment locks and claim/evidence bindings before cross-reading."""

    if not isinstance(package, ReviewPackageV1):
        raise ReviewHarnessError("package must be ReviewPackageV1")
    reviews = _verify_review_order(reviews)
    assignment_hashes = {
        assignment.role: assignment.assignment_sha256
        for assignment in package.assignments
    }
    source_hashes = set(package.source_sha256)
    claim_ids = set(package.claim_ids)
    for review in reviews:
        if review.assignment_sha256 != assignment_hashes[review.role]:
            raise ReviewHarnessError("review assignment hash is stale or mismatched")
        for finding in review.findings:
            if finding.claim_id not in claim_ids:
                raise ReviewHarnessError("finding claim ID is not frozen")
            if finding.evidence_sha256 not in source_hashes:
                raise ReviewHarnessError("finding evidence hash is not frozen")
    return reviews


def adjudicate_review_union(
    package: ReviewPackageV1,
    reviews: tuple[ReviewRecordV1, ...],
    *,
    proposed_status: str,
) -> tuple[FindingV1, ...]:
    """Return the finding union; no scores, votes, or outcome evidence are inferred."""

    reviews = verify_locked_reviews(package, reviews)
    if proposed_status not in ("go", "hold"):
        raise ReviewHarnessError("proposed_status is not a closed enum")
    union: list[FindingV1] = []
    by_identity: dict[tuple[str, str, str], FindingV1] = {}
    for review in reviews:
        for finding in review.findings:
            identity = (
                finding.failure_code,
                finding.claim_id,
                finding.evidence_sha256,
            )
            existing = by_identity.get(identity)
            if existing is None:
                by_identity[identity] = finding
                union.append(finding)
            elif (
                existing.severity != finding.severity
                or existing.resolved != finding.resolved
                or existing.falsifier_result != finding.falsifier_result
            ):
                raise ReviewHarnessError("conflicting duplicate finding identity")
    if proposed_status == "go":
        for finding in union:
            if not finding.resolved and finding.severity in ("C", "I"):
                severity_name = "critical" if finding.severity == "C" else "important"
                raise ReviewHarnessError(
                    f"unresolved {severity_name} finding blocks go"
                )
    return tuple(union)


__all__ = [
    "FINDING_SEVERITIES",
    "FROZEN_PREAMBLE",
    "ICLR_GUIDELINES_URL",
    "ICLR_QUESTIONS",
    "ROLE_SUFFIXES",
    "ROLES",
    "VERDICTS",
    "FindingV1",
    "ReviewAssignmentV1",
    "ReviewHarnessError",
    "ReviewPackageV1",
    "ReviewRecordV1",
    "adjudicate_review_union",
    "build_review_package",
    "lock_review_record",
    "locked_review_bytes",
    "review_package_bytes",
    "verify_locked_review_bytes",
    "verify_locked_reviews",
    "verify_review_package_bytes",
]
