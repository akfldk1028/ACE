"""Deterministic, PNU-free public projections for architecture cases."""

from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from .io import sha256_json
from .schema import (
    ArchitectureEvidencePacket,
    ArchitectureGoldRecord,
    ArchitecturePublicCase,
    PrivateCaseBinding,
)


_PNU = re.compile(r"^[0-9]{19}$")
_RAW_PNU = re.compile(r"(?<!\d)\d{19}(?!\d)")
_PRIVATE_EXACT_KEYS = {
    "case_id",
    "condition",
    "expected_decision",
    "mutation_family",
    "gold_record",
}
_SITE_DOMAIN = b"ace.iclr2027.public.site.v1\0"
_CASE_DOMAIN = b"ace.iclr2027.public.case.v1\0"
_COMMITMENT_DOMAIN = b"ace.iclr2027.projection.secret.v1\0"


@dataclass(frozen=True)
class ProjectionIdentity:
    """Caller-supplied secret namespace for stable opaque public identities."""

    secret: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.secret) is not bytes:
            raise TypeError("projection secret must be a 32-byte or longer bytes value")
        if len(self.secret) < 32:
            raise ValueError("projection secret must be a 32-byte or longer bytes value")

    @property
    def commitment(self) -> str:
        return hashlib.sha256(_COMMITMENT_DOMAIN + self.secret).hexdigest()

    def site_ref(self, pnu: str) -> str:
        if not isinstance(pnu, str) or not _PNU.fullmatch(pnu):
            raise ValueError("site identity input must contain exactly 19 digits")
        digest = hmac.new(
            self.secret,
            _SITE_DOMAIN + pnu.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        return f"site:{digest}"

    def case_id(self, internal_case_id: str) -> str:
        if not isinstance(internal_case_id, str) or not internal_case_id.strip():
            raise ValueError("internal case identity must be nonempty")
        digest = hmac.new(
            self.secret,
            _CASE_DOMAIN + internal_case_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"case:{digest}"


def _project_text(
    value: str,
    *,
    identity: ProjectionIdentity,
    internal_case_id: str,
    public_case_id: str,
) -> str:
    if value == internal_case_id:
        return public_case_id
    return _RAW_PNU.sub(
        lambda match: identity.site_ref(match.group()),
        value,
    )


def _project_nested(
    value: Any,
    *,
    identity: ProjectionIdentity,
    internal_case_id: str,
    public_case_id: str,
) -> Any:
    if isinstance(value, Mapping):
        projected: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            lowered = key.lower()
            if lowered in _PRIVATE_EXACT_KEYS or lowered.startswith("gold_"):
                continue
            public_key = "site_ref" if lowered == "pnu" else _project_text(
                key,
                identity=identity,
                internal_case_id=internal_case_id,
                public_case_id=public_case_id,
            )
            if public_key in projected:
                raise ValueError(f"public projection key collision: {public_key}")
            projected[public_key] = _project_nested(
                item,
                identity=identity,
                internal_case_id=internal_case_id,
                public_case_id=public_case_id,
            )
        return projected
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [
            _project_nested(
                item,
                identity=identity,
                internal_case_id=internal_case_id,
                public_case_id=public_case_id,
            )
            for item in value
        ]
    if isinstance(value, str):
        return _project_text(
            value,
            identity=identity,
            internal_case_id=internal_case_id,
            public_case_id=public_case_id,
        )
    if isinstance(value, int) and not isinstance(value, bool):
        text = str(value)
        if _PNU.fullmatch(text):
            return identity.site_ref(text)
    return value


def project_public_case(
    packet: ArchitectureEvidencePacket,
    identity: ProjectionIdentity,
) -> ArchitecturePublicCase:
    """Project one internal packet into its strict agent-visible representation."""

    if not isinstance(packet, ArchitectureEvidencePacket):
        raise TypeError("packet must be an ArchitectureEvidencePacket")
    if not isinstance(identity, ProjectionIdentity):
        raise TypeError("identity must be a ProjectionIdentity")
    public_case_id = identity.case_id(packet.case_id)
    evidence = _project_nested(
        packet.evidence,
        identity=identity,
        internal_case_id=packet.case_id,
        public_case_id=public_case_id,
    )
    if not isinstance(evidence, list) or any(
        not isinstance(item, Mapping) for item in evidence
    ):
        raise ValueError("projected evidence must remain a sequence of objects")
    execution_id = _project_nested(
        packet.execution_id,
        identity=identity,
        internal_case_id=packet.case_id,
        public_case_id=public_case_id,
    )
    return ArchitecturePublicCase(
        case_id=public_case_id,
        site_ref=identity.site_ref(packet.pnu),
        program=packet.program,
        execution_id=execution_id,
        program_hash=packet.program_hash,
        geometry_hash=packet.geometry_hash,
        evidence=tuple(dict(item) for item in evidence),
        subject_kind=packet.subject_kind,
        source_artifact_sha256=packet.source_artifact_sha256,
        attempt_id=packet.attempt_id,
        attempt_hash=packet.attempt_hash,
        attempt_stage=packet.attempt_stage,
        route_kind=packet.route_kind,
    )


def project_gold_record(
    gold_record: ArchitectureGoldRecord,
    packet: ArchitectureEvidencePacket,
    identity: ProjectionIdentity,
) -> ArchitectureGoldRecord:
    """Replace the internal gold key with the same opaque public case identity."""

    if gold_record.case_id != packet.case_id:
        raise ValueError("internal packet and gold case IDs do not match")
    return replace(gold_record, case_id=identity.case_id(packet.case_id))


def bind_private_case(
    public_case: ArchitecturePublicCase,
    packet: ArchitectureEvidencePacket,
    gold_record: ArchitectureGoldRecord,
    identity: ProjectionIdentity,
) -> PrivateCaseBinding:
    """Create a canonical three-way binding after checking the projection."""

    if public_case.case_id != gold_record.case_id:
        raise ValueError("public and gold case IDs do not match")
    if project_public_case(packet, identity) != public_case:
        raise ValueError("public case is not the canonical packet projection")
    return PrivateCaseBinding(
        public_case_id=public_case.case_id,
        public_case_sha256=sha256_json(public_case.to_dict()),
        internal_packet_sha256=sha256_json(packet.to_dict()),
        gold_record_sha256=sha256_json(gold_record.to_dict()),
        packet=packet,
    )


def verify_private_case_binding(
    public_case: ArchitecturePublicCase,
    binding: PrivateCaseBinding,
    gold_record: ArchitectureGoldRecord,
    identity: ProjectionIdentity,
) -> ArchitectureEvidencePacket:
    """Fail closed unless a persisted public/internal/gold triplet is exact."""

    if binding.public_case_id != public_case.case_id:
        raise ValueError("public case identity mismatch")
    if not hmac.compare_digest(
        binding.public_case_sha256,
        sha256_json(public_case.to_dict()),
    ):
        raise ValueError("public case canonical hash mismatch")
    if public_case.case_id != gold_record.case_id:
        raise ValueError("public and gold case IDs do not match")
    if not hmac.compare_digest(
        binding.gold_record_sha256,
        sha256_json(gold_record.to_dict()),
    ):
        raise ValueError("gold record canonical hash mismatch")
    if project_public_case(binding.packet, identity) != public_case:
        raise ValueError("public case is not the canonical packet projection")
    return binding.packet


__all__ = [
    "ProjectionIdentity",
    "bind_private_case",
    "project_gold_record",
    "project_public_case",
    "verify_private_case_binding",
]
