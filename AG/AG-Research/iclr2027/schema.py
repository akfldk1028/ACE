"""Typed schemas for architecture termination experiments."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Mapping, Sequence

from .io import assert_public_gold_separation, sha256_json


ProgramId = Literal["neighborhood", "gymnasium", "cultural"]
Condition = Literal["native", "challenged"]
SubjectKind = Literal["execution", "portfolio_attempt"]
ReviewDecision = Literal["CONTINUE", "STOP_ACCEPT", "STOP_REJECT"]
AttemptStage = Literal[
    "selection", "materialization", "preflight", "candidate_floor_context"
]
MaterializationRoute = Literal[
    "all_invocations_failed",
    "capacity_admission_empty",
    "program_routing_empty",
]

_PROGRAMS = {"neighborhood", "gymnasium", "cultural"}
_CONDITIONS = {"native", "challenged"}
_SUBJECT_KINDS = {"execution", "portfolio_attempt"}
_TERMINAL_DECISIONS = {"STOP_ACCEPT", "STOP_REJECT"}
_REVIEW_DECISIONS = {"CONTINUE", *_TERMINAL_DECISIONS}
_ATTEMPT_STAGES = {
    "selection",
    "materialization",
    "preflight",
    "candidate_floor_context",
}
_MATERIALIZATION_ROUTES = {
    "all_invocations_failed",
    "capacity_admission_empty",
    "program_routing_empty",
}
_DOMAINS = {"site", "law", "parking", "program", "geometry"}
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_SHA256_LOWER = re.compile(r"^[0-9a-f]{64}$")
_PNU = re.compile(r"^[0-9]{19}$")
_RAW_PNU = re.compile(r"(?<!\d)\d{19}(?!\d)")
_PUBLIC_CASE_ID = re.compile(r"^case:[0-9a-f]{64}$")
_PUBLIC_SITE_ID = re.compile(r"^site:[0-9a-f]{64}$")
_ATTEMPT_ID = re.compile(r"^attempt:[0-9a-f]{64}$")

PUBLIC_CASE_SCHEMA_VERSION = "ace.iclr2027.public_case.v1"
PRIVATE_CASE_BINDING_SCHEMA_VERSION = "ace.iclr2027.private_case_binding.v1"

_PUBLIC_CASE_KEYS = frozenset(
    {
        "schema_version",
        "case_id",
        "site_ref",
        "program",
        "execution_id",
        "program_hash",
        "geometry_hash",
        "evidence",
        "subject_kind",
        "source_artifact_sha256",
        "attempt_id",
        "attempt_hash",
        "attempt_stage",
        "route_kind",
    }
)
_PRIVATE_CASE_BINDING_KEYS = frozenset(
    {
        "schema_version",
        "public_case_id",
        "public_case_sha256",
        "internal_packet_sha256",
        "gold_record_sha256",
        "packet",
    }
)
_FORBIDDEN_RELEASE_KEYS = {
    "pnu",
    "condition",
    "expected_decision",
    "mutation_family",
    "gold_record",
}


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be nonempty")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field} must be a sequence of strings")
    result = tuple(str(item).strip() for item in value)
    if any(not item for item in result):
        raise ValueError(f"{field} contains an empty value")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    return result


def _contains_raw_pnu(value: str) -> bool:
    """Distinguish raw cadastral tokens from approved opaque/hash identities."""

    if (
        _PUBLIC_CASE_ID.fullmatch(value)
        or _PUBLIC_SITE_ID.fullmatch(value)
        or _SHA256.fullmatch(value)
        or _ATTEMPT_ID.fullmatch(value)
    ):
        return False
    return _RAW_PNU.search(value) is not None


def _assert_public_release_safe(value: Any, path: str = "public_case") -> None:
    """Reject private identifiers and labels from a public-case payload."""

    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            lowered = key.lower()
            if lowered in _FORBIDDEN_RELEASE_KEYS or lowered.startswith("gold_"):
                raise ValueError(f"forbidden public field at {path}.{key}")
            if lowered == "case_id" and path != "public_case":
                raise ValueError(f"nested case_id is forbidden at {path}.{key}")
            if _contains_raw_pnu(key):
                raise ValueError(f"raw PNU is forbidden at {path}.{key}")
            _assert_public_release_safe(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _assert_public_release_safe(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if _contains_raw_pnu(value):
            raise ValueError(f"raw PNU is forbidden at {path}")
    elif isinstance(value, int) and not isinstance(value, bool):
        if _PNU.fullmatch(str(value)):
            raise ValueError(f"raw PNU is forbidden at {path}")


def _require_exact_keys(
    payload: Mapping[str, Any],
    expected: frozenset[str],
    label: str,
) -> None:
    keys = set(payload)
    if keys != expected or any(not isinstance(key, str) for key in payload):
        missing = sorted(expected - keys)
        extra = sorted(str(key) for key in keys - expected)
        raise ValueError(
            f"{label} must contain exact keys; missing={missing}, extra={extra}"
        )


class FrozenDict(Mapping[str, Any]):
    """Small recursively immutable mapping used inside frozen packets."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = dict(data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return FrozenDict({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class ArchitectureEvidencePacket:
    case_id: str
    pnu: str
    program: ProgramId
    condition: Condition
    execution_id: str | None
    program_hash: str | None
    geometry_hash: str | None
    evidence: tuple[Mapping[str, Any], ...]
    subject_kind: SubjectKind = "execution"
    source_artifact_sha256: str | None = None
    attempt_id: str | None = None
    attempt_hash: str | None = None
    attempt_stage: AttemptStage | None = None
    route_kind: MaterializationRoute | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence",
            tuple(_freeze(item) for item in self.evidence),
        )
        _required_text(self.case_id, "case_id")
        if not _PNU.fullmatch(self.pnu):
            raise ValueError("pnu must contain exactly 19 digits")
        if self.program not in _PROGRAMS:
            raise ValueError(f"unsupported program: {self.program}")
        if self.condition not in _CONDITIONS:
            raise ValueError(f"unsupported condition: {self.condition}")
        if self.subject_kind not in _SUBJECT_KINDS:
            raise ValueError(f"unsupported subject_kind: {self.subject_kind}")
        if self.source_artifact_sha256 is not None and not _SHA256.fullmatch(
            self.source_artifact_sha256
        ):
            raise ValueError("source_artifact_sha256 must be a 64-character SHA-256")
        if self.subject_kind == "execution":
            _required_text(self.execution_id, "execution_id")
            if not isinstance(self.program_hash, str) or not _SHA256.fullmatch(
                self.program_hash
            ):
                raise ValueError("program_hash must be a 64-character SHA-256")
            if not isinstance(self.geometry_hash, str) or not _SHA256.fullmatch(
                self.geometry_hash
            ):
                raise ValueError("geometry_hash must be a 64-character SHA-256")
            if self.attempt_id is not None or self.attempt_hash is not None:
                raise ValueError("execution subject must not contain attempt identity")
            if self.attempt_stage is not None:
                raise ValueError("execution subject must not contain attempt_stage")
            if self.route_kind is not None:
                raise ValueError("execution subject must not contain route_kind")
        else:
            if any(
                value is not None
                for value in (self.execution_id, self.program_hash, self.geometry_hash)
            ):
                raise ValueError(
                    "portfolio_attempt subject must not contain execution identity"
                )
            if not isinstance(self.attempt_id, str) or not re.fullmatch(
                r"attempt:[0-9a-f]{64}", self.attempt_id
            ):
                raise ValueError("attempt_id must be an opaque artifact-bound identity")
            if not isinstance(self.attempt_hash, str) or not _SHA256.fullmatch(
                self.attempt_hash
            ):
                raise ValueError("attempt_hash must be a 64-character SHA-256")
            if not isinstance(self.source_artifact_sha256, str):
                raise ValueError(
                    "source_artifact_sha256 is required for portfolio_attempt"
                )
            if self.attempt_stage not in _ATTEMPT_STAGES:
                raise ValueError("portfolio_attempt requires a supported attempt_stage")
            if self.attempt_stage == "materialization":
                if self.route_kind not in _MATERIALIZATION_ROUTES:
                    raise ValueError(
                        "materialization portfolio_attempt requires a supported route_kind"
                    )
            elif self.route_kind is not None:
                raise ValueError(
                    "route_kind is only valid for materialization attempts"
                )
        if not self.evidence:
            raise ValueError("evidence must not be empty")
        evidence_ids = [
            _required_text(item.get("evidence_id"), "evidence_id")
            for item in self.evidence
        ]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate evidence_id")
        assert_public_gold_separation(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ArchitectureEvidencePacket":
        evidence = payload.get("evidence")
        if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
            raise ValueError("evidence must be a sequence")
        return cls(
            case_id=str(payload.get("case_id") or ""),
            pnu=str(payload.get("pnu") or ""),
            program=str(payload.get("program") or ""),  # type: ignore[arg-type]
            condition=str(payload.get("condition") or ""),  # type: ignore[arg-type]
            execution_id=_optional_text(payload.get("execution_id")),
            program_hash=_optional_text(payload.get("program_hash")),
            geometry_hash=_optional_text(payload.get("geometry_hash")),
            evidence=tuple(dict(item) for item in evidence),
            subject_kind=str(payload.get("subject_kind") or "execution"),  # type: ignore[arg-type]
            source_artifact_sha256=_optional_text(
                payload.get("source_artifact_sha256")
            ),
            attempt_id=_optional_text(payload.get("attempt_id")),
            attempt_hash=_optional_text(payload.get("attempt_hash")),
            attempt_stage=_optional_text(payload.get("attempt_stage")),  # type: ignore[arg-type]
            route_kind=_optional_text(payload.get("route_kind")),  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "pnu": self.pnu,
            "program": self.program,
            "condition": self.condition,
            "execution_id": self.execution_id,
            "program_hash": self.program_hash,
            "geometry_hash": self.geometry_hash,
            "evidence": _thaw(self.evidence),
            "subject_kind": self.subject_kind,
            "source_artifact_sha256": self.source_artifact_sha256,
            "attempt_id": self.attempt_id,
            "attempt_hash": self.attempt_hash,
            "attempt_stage": self.attempt_stage,
            "route_kind": self.route_kind,
        }


@dataclass(frozen=True)
class ArchitecturePublicCase:
    """Strict PNU-free projection supplied to agents and public consumers."""

    SCHEMA_VERSION: ClassVar[str] = PUBLIC_CASE_SCHEMA_VERSION

    case_id: str
    site_ref: str
    program: ProgramId
    execution_id: str | None
    program_hash: str | None
    geometry_hash: str | None
    evidence: tuple[Mapping[str, Any], ...]
    subject_kind: SubjectKind = "execution"
    source_artifact_sha256: str | None = None
    attempt_id: str | None = None
    attempt_hash: str | None = None
    attempt_stage: AttemptStage | None = None
    route_kind: MaterializationRoute | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence",
            tuple(_freeze(item) for item in self.evidence),
        )
        if not _PUBLIC_CASE_ID.fullmatch(self.case_id):
            raise ValueError("public case_id must be a full opaque case identity")
        if not _PUBLIC_SITE_ID.fullmatch(self.site_ref):
            raise ValueError("site_ref must be a full opaque site identity")
        if self.program not in _PROGRAMS:
            raise ValueError(f"unsupported program: {self.program}")
        if self.subject_kind not in _SUBJECT_KINDS:
            raise ValueError(f"unsupported subject_kind: {self.subject_kind}")
        if self.source_artifact_sha256 is not None and not _SHA256.fullmatch(
            self.source_artifact_sha256
        ):
            raise ValueError("source_artifact_sha256 must be a 64-character SHA-256")
        if self.subject_kind == "execution":
            _required_text(self.execution_id, "execution_id")
            if not isinstance(self.program_hash, str) or not _SHA256.fullmatch(
                self.program_hash
            ):
                raise ValueError("program_hash must be a 64-character SHA-256")
            if not isinstance(self.geometry_hash, str) or not _SHA256.fullmatch(
                self.geometry_hash
            ):
                raise ValueError("geometry_hash must be a 64-character SHA-256")
            if self.attempt_id is not None or self.attempt_hash is not None:
                raise ValueError("execution subject must not contain attempt identity")
            if self.attempt_stage is not None:
                raise ValueError("execution subject must not contain attempt_stage")
            if self.route_kind is not None:
                raise ValueError("execution subject must not contain route_kind")
        else:
            if any(
                value is not None
                for value in (self.execution_id, self.program_hash, self.geometry_hash)
            ):
                raise ValueError(
                    "portfolio_attempt subject must not contain execution identity"
                )
            if not isinstance(self.attempt_id, str) or not _ATTEMPT_ID.fullmatch(
                self.attempt_id
            ):
                raise ValueError("attempt_id must be an opaque artifact-bound identity")
            if not isinstance(self.attempt_hash, str) or not _SHA256.fullmatch(
                self.attempt_hash
            ):
                raise ValueError("attempt_hash must be a 64-character SHA-256")
            if not isinstance(self.source_artifact_sha256, str):
                raise ValueError(
                    "source_artifact_sha256 is required for portfolio_attempt"
                )
            if self.attempt_stage not in _ATTEMPT_STAGES:
                raise ValueError("portfolio_attempt requires a supported attempt_stage")
            if self.attempt_stage == "materialization":
                if self.route_kind not in _MATERIALIZATION_ROUTES:
                    raise ValueError(
                        "materialization portfolio_attempt requires a supported route_kind"
                    )
            elif self.route_kind is not None:
                raise ValueError(
                    "route_kind is only valid for materialization attempts"
                )
        if not self.evidence:
            raise ValueError("evidence must not be empty")
        evidence_ids = [
            _required_text(item.get("evidence_id"), "evidence_id")
            for item in self.evidence
        ]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate evidence_id")
        _assert_public_release_safe(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ArchitecturePublicCase":
        _require_exact_keys(payload, _PUBLIC_CASE_KEYS, "public case")
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError("unsupported public case schema")
        evidence = payload.get("evidence")
        if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
            raise ValueError("evidence must be a sequence")
        if any(not isinstance(item, Mapping) for item in evidence):
            raise ValueError("evidence items must be objects")
        return cls(
            case_id=str(payload.get("case_id") or ""),
            site_ref=str(payload.get("site_ref") or ""),
            program=str(payload.get("program") or ""),  # type: ignore[arg-type]
            execution_id=_optional_text(payload.get("execution_id")),
            program_hash=_optional_text(payload.get("program_hash")),
            geometry_hash=_optional_text(payload.get("geometry_hash")),
            evidence=tuple(dict(item) for item in evidence),
            subject_kind=str(payload.get("subject_kind") or ""),  # type: ignore[arg-type]
            source_artifact_sha256=_optional_text(
                payload.get("source_artifact_sha256")
            ),
            attempt_id=_optional_text(payload.get("attempt_id")),
            attempt_hash=_optional_text(payload.get("attempt_hash")),
            attempt_stage=_optional_text(payload.get("attempt_stage")),  # type: ignore[arg-type]
            route_kind=_optional_text(payload.get("route_kind")),  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "case_id": self.case_id,
            "site_ref": self.site_ref,
            "program": self.program,
            "execution_id": self.execution_id,
            "program_hash": self.program_hash,
            "geometry_hash": self.geometry_hash,
            "evidence": _thaw(self.evidence),
            "subject_kind": self.subject_kind,
            "source_artifact_sha256": self.source_artifact_sha256,
            "attempt_id": self.attempt_id,
            "attempt_hash": self.attempt_hash,
            "attempt_stage": self.attempt_stage,
            "route_kind": self.route_kind,
        }


@dataclass(frozen=True)
class ArchitectureGoldRecord:
    case_id: str
    expected_decision: ReviewDecision
    blocking_issue_codes: tuple[str, ...]
    missing_evidence_codes: tuple[str, ...]
    required_evidence_ids: tuple[str, ...]
    mutation_family: str

    def __post_init__(self) -> None:
        _required_text(self.case_id, "case_id")
        if self.expected_decision not in _REVIEW_DECISIONS:
            raise ValueError("unsupported expected_decision")
        if self.expected_decision == "STOP_REJECT" and not self.blocking_issue_codes:
            raise ValueError("STOP_REJECT requires a blocking issue")
        if self.expected_decision == "CONTINUE" and (
            self.blocking_issue_codes or not self.missing_evidence_codes
        ):
            raise ValueError("CONTINUE requires missing evidence and no blocking issue")
        if self.expected_decision == "STOP_ACCEPT" and (
            self.blocking_issue_codes or self.missing_evidence_codes
        ):
            raise ValueError("STOP_ACCEPT cannot contain blocking or missing evidence")
        if not self.required_evidence_ids:
            raise ValueError("required_evidence_ids must not be empty")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ArchitectureGoldRecord":
        return cls(
            case_id=str(payload.get("case_id") or ""),
            expected_decision=str(payload.get("expected_decision") or ""),  # type: ignore[arg-type]
            blocking_issue_codes=_string_tuple(
                payload.get("blocking_issue_codes", ()),
                "blocking_issue_codes",
            ),
            missing_evidence_codes=_string_tuple(
                payload.get("missing_evidence_codes", ()),
                "missing_evidence_codes",
            ),
            required_evidence_ids=_string_tuple(
                payload.get("required_evidence_ids", ()),
                "required_evidence_ids",
            ),
            mutation_family=str(payload.get("mutation_family") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "expected_decision": self.expected_decision,
            "blocking_issue_codes": list(self.blocking_issue_codes),
            "missing_evidence_codes": list(self.missing_evidence_codes),
            "required_evidence_ids": list(self.required_evidence_ids),
            "mutation_family": self.mutation_family,
        }


@dataclass(frozen=True)
class PrivateCaseBinding:
    """Private envelope binding one public projection to packet and gold hashes."""

    SCHEMA_VERSION: ClassVar[str] = PRIVATE_CASE_BINDING_SCHEMA_VERSION

    public_case_id: str
    public_case_sha256: str
    internal_packet_sha256: str
    gold_record_sha256: str
    packet: ArchitectureEvidencePacket

    def __post_init__(self) -> None:
        if not _PUBLIC_CASE_ID.fullmatch(self.public_case_id):
            raise ValueError("public_case_id must be a full opaque case identity")
        for field_name in (
            "public_case_sha256",
            "internal_packet_sha256",
            "gold_record_sha256",
        ):
            value = getattr(self, field_name)
            if not _SHA256_LOWER.fullmatch(value):
                raise ValueError(f"{field_name} must be a lowercase SHA-256")
        if sha256_json(self.packet.to_dict()) != self.internal_packet_sha256:
            raise ValueError("internal packet canonical hash mismatch")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PrivateCaseBinding":
        _require_exact_keys(payload, _PRIVATE_CASE_BINDING_KEYS, "private case binding")
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError("unsupported private case binding schema")
        packet = payload.get("packet")
        if not isinstance(packet, Mapping):
            raise ValueError("private case binding packet must be an object")
        return cls(
            public_case_id=str(payload.get("public_case_id") or ""),
            public_case_sha256=str(payload.get("public_case_sha256") or ""),
            internal_packet_sha256=str(payload.get("internal_packet_sha256") or ""),
            gold_record_sha256=str(payload.get("gold_record_sha256") or ""),
            packet=ArchitectureEvidencePacket.from_dict(packet),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "public_case_id": self.public_case_id,
            "public_case_sha256": self.public_case_sha256,
            "internal_packet_sha256": self.internal_packet_sha256,
            "gold_record_sha256": self.gold_record_sha256,
            "packet": self.packet.to_dict(),
        }


@dataclass(frozen=True)
class ArchitectureReviewState:
    checked_domains: tuple[str, ...]
    blocking_issue_codes: tuple[str, ...]
    missing_evidence_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    recommended_decision: ReviewDecision
    confidence: float

    ALLOWED_MISSING_EVIDENCE_CODES = frozenset(
        {
            "law.required_evidence_missing",
            "parking.required_evidence_missing",
            "candidate_floor_context.typed_ledger_missing",
        }
    )
    ALLOWED_BLOCKING_ISSUE_CODES = frozenset(
        {
            "identity.attempt_hash_mismatch",
            "evidence.portfolio_attempt_incomplete",
            "selection.no_admitted_candidate",
            "materialization.no_candidate_reached_ledger",
            "preflight.program_site_infeasible",
            "site.boundary_failed",
            "geometry.compilation_failed",
            "identity.hash_mismatch",
            "law.projection_failed",
            "parking.supply_shortage",
            "program.capacity_failed",
        }
    )

    def __post_init__(self) -> None:
        unknown_domains = set(self.checked_domains) - _DOMAINS
        if unknown_domains:
            raise ValueError(f"unknown checked_domains: {sorted(unknown_domains)}")
        unknown_missing_codes = (
            set(self.missing_evidence_codes) - self.ALLOWED_MISSING_EVIDENCE_CODES
        )
        if unknown_missing_codes:
            raise ValueError(
                f"unknown missing_evidence_codes: {sorted(unknown_missing_codes)}"
            )
        unknown_blocking_codes = (
            set(self.blocking_issue_codes) - self.ALLOWED_BLOCKING_ISSUE_CODES
        )
        if unknown_blocking_codes:
            raise ValueError(
                f"unknown blocking_issue_codes: {sorted(unknown_blocking_codes)}"
            )
        if self.recommended_decision not in _REVIEW_DECISIONS:
            raise ValueError("unsupported recommended_decision")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0, 1]")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ArchitectureReviewState":
        return cls(
            checked_domains=_string_tuple(
                payload.get("checked_domains", ()), "checked_domains"
            ),
            blocking_issue_codes=_string_tuple(
                payload.get("blocking_issue_codes", ()),
                "blocking_issue_codes",
            ),
            missing_evidence_codes=_string_tuple(
                payload.get("missing_evidence_codes", ()),
                "missing_evidence_codes",
            ),
            evidence_ids=_string_tuple(payload.get("evidence_ids", ()), "evidence_ids"),
            recommended_decision=str(payload.get("recommended_decision") or ""),  # type: ignore[arg-type]
            confidence=float(payload.get("confidence", 0.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "checked_domains": list(self.checked_domains),
            "blocking_issue_codes": list(self.blocking_issue_codes),
            "missing_evidence_codes": list(self.missing_evidence_codes),
            "evidence_ids": list(self.evidence_ids),
            "recommended_decision": self.recommended_decision,
            "confidence": self.confidence,
        }
