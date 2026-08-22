"""Evidence-level fault mutations for challenged architecture cases."""

from __future__ import annotations

import hashlib
from typing import Callable, Iterable, Mapping

from .schema import ArchitectureEvidencePacket


FaultFn = Callable[[ArchitectureEvidencePacket], ArchitectureEvidencePacket]


def _challenged_payload(packet: ArchitectureEvidencePacket) -> dict:
    payload = packet.to_dict()
    payload["condition"] = "challenged"
    if payload["case_id"].endswith("-native"):
        payload["case_id"] = payload["case_id"][: -len("-native")] + "-challenged"
    return payload


def _evidence(payload: dict, evidence_id: str) -> dict:
    for item in payload["evidence"]:
        if item.get("evidence_id") == evidence_id:
            return item
    raise ValueError(f"required evidence is missing: {evidence_id}")


def mutate_identity_hash(packet: ArchitectureEvidencePacket) -> ArchitectureEvidencePacket:
    payload = _challenged_payload(packet)
    law = _evidence(payload, "evidence:law_graph_agent")
    law["identity"]["geometry_hash"] = "0" * 64
    return ArchitectureEvidencePacket.from_dict(payload)


def mutate_law_projection(packet: ArchitectureEvidencePacket) -> ArchitectureEvidencePacket:
    payload = _challenged_payload(packet)
    law = _evidence(payload, "evidence:law_graph_agent")
    projection = law["evidence"]["legal_projection"]
    projection["volume_retention"] = 0.5
    return ArchitectureEvidencePacket.from_dict(payload)


def mutate_parking_shortage(packet: ArchitectureEvidencePacket) -> ArchitectureEvidencePacket:
    payload = _challenged_payload(packet)
    parking = _evidence(payload, "evidence:parking_agent")["evidence"]
    required = max(int(parking.get("required_spaces") or 0), 1)
    parking["required_spaces"] = required
    parking["provided_spaces"] = required - 1
    return ArchitectureEvidencePacket.from_dict(payload)


def mutate_program_capacity(packet: ArchitectureEvidencePacket) -> ArchitectureEvidencePacket:
    payload = _challenged_payload(packet)
    program = _evidence(payload, "evidence:program_agent")["evidence"]
    target = float(program.get("candidate_target_gfa_m2") or 0.0)
    if target <= 0:
        raise ValueError("program target GFA is unavailable")
    program["achieved_gfa_m2"] = target * 0.5
    return ArchitectureEvidencePacket.from_dict(payload)


def mutate_geometry_compile(packet: ArchitectureEvidencePacket) -> ArchitectureEvidencePacket:
    payload = _challenged_payload(packet)
    geometry = _evidence(payload, "evidence:geometry_agent")["evidence"]
    geometry["candidate_floor_count"] = 0
    return ArchitectureEvidencePacket.from_dict(payload)


def _mutate_required_evidence_missing(
    packet: ArchitectureEvidencePacket,
    evidence_id: str,
) -> ArchitectureEvidencePacket:
    payload = _challenged_payload(packet)
    payload["evidence"] = [
        item
        for item in payload["evidence"]
        if item.get("evidence_id") != evidence_id
    ]
    return ArchitectureEvidencePacket.from_dict(payload)


def mutate_law_evidence_missing(
    packet: ArchitectureEvidencePacket,
) -> ArchitectureEvidencePacket:
    return _mutate_required_evidence_missing(packet, "evidence:law_graph_agent")


def mutate_parking_evidence_missing(
    packet: ArchitectureEvidencePacket,
) -> ArchitectureEvidencePacket:
    return _mutate_required_evidence_missing(packet, "evidence:parking_agent")


HARD_FAULT_FAMILIES = (
    "identity_hash",
    "law_projection",
    "parking_shortage",
    "program_capacity",
    "geometry_compile",
)
MISSING_EVIDENCE_FAULT_FAMILIES = (
    "law_evidence_missing",
    "parking_evidence_missing",
)
CHALLENGE_FAMILY_CENSUS = (
    *HARD_FAULT_FAMILIES,
    *MISSING_EVIDENCE_FAULT_FAMILIES,
)


FAULT_REGISTRY: Mapping[str, FaultFn] = {
    "identity_hash": mutate_identity_hash,
    "law_projection": mutate_law_projection,
    "parking_shortage": mutate_parking_shortage,
    "program_capacity": mutate_program_capacity,
    "geometry_compile": mutate_geometry_compile,
    "law_evidence_missing": mutate_law_evidence_missing,
    "parking_evidence_missing": mutate_parking_evidence_missing,
}


def assign_fault_families(case_ids: Iterable[str]) -> dict[str, str]:
    """Balance families after a deterministic hash ordering of case IDs."""

    unique = set(case_ids)
    ordered = sorted(
        unique,
        key=lambda case_id: hashlib.sha256(case_id.encode("utf-8")).hexdigest(),
    )
    families = tuple(FAULT_REGISTRY)
    return {
        case_id: families[index % len(families)]
        for index, case_id in enumerate(ordered)
    }
