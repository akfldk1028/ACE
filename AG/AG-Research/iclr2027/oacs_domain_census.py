"""Outcome-free, rights-bound domain census contracts for the MAS/OACS gate."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


_SCHEMA = "oacs-domain-census/v1"
_DOMAINS = {"architecture", "jci"}
_PARTITIONS = {"audit", "focal"}
_RIGHTS_STATUSES = {"unrestricted", "permission_granted"}
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_PROTECTED_RE = re.compile(
    r"pnu|path|project|gold|outcome|mutation|expected|decision|evaluator|feedback",
    re.IGNORECASE,
)
_ROOT_KEYS = {"schema", "units", "source_manifest_sha256"}
_UNIT_KEYS = {
    "domain",
    "cluster_id",
    "unit_id",
    "partition",
    "obligation_families",
    "public_packet_sha256",
    "evaluator_commitment_sha256",
    "source_rights_status",
    "blind_overlap_sha256",
}


class DomainCensusError(ValueError):
    """Raised when an outcome-free domain census violates its contract."""


def _require_hash(value: object, field: str) -> None:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise DomainCensusError(f"{field} must be a lowercase SHA-256")


def _require_opaque(value: object, field: str) -> None:
    if type(value) is not str or not value:
        raise DomainCensusError(f"{field} must be nonempty opaque text")
    if _PROTECTED_RE.search(value) or any(character in value for character in "/\\:"):
        raise DomainCensusError(f"{field} contains a protected channel or identifier")
    if _OPAQUE_RE.fullmatch(value) is None:
        raise DomainCensusError(f"{field} must be an opaque identifier")


def _unit_order_key(unit: "DomainUnitV1") -> tuple[bytes, bytes, bytes]:
    return (
        unit.domain.encode("utf-8"),
        unit.cluster_id.encode("utf-8"),
        unit.unit_id.encode("utf-8"),
    )


@dataclass(frozen=True)
class DomainUnitV1:
    domain: str
    cluster_id: str
    unit_id: str
    partition: str
    obligation_families: tuple[str, ...]
    public_packet_sha256: str
    evaluator_commitment_sha256: str
    source_rights_status: str
    blind_overlap_sha256: str

    def __post_init__(self) -> None:
        if type(self.domain) is not str or self.domain not in _DOMAINS:
            raise DomainCensusError("domain is not a closed enum")
        _require_opaque(self.cluster_id, "cluster_id")
        _require_opaque(self.unit_id, "unit_id")
        if type(self.partition) is not str or self.partition not in _PARTITIONS:
            raise DomainCensusError("partition is not a closed enum")
        if type(self.obligation_families) is not tuple:
            raise DomainCensusError("obligation_families must be a tuple")
        if not self.obligation_families:
            raise DomainCensusError("obligation_families must be nonempty")
        for family in self.obligation_families:
            _require_opaque(family, "obligation family")
        family_order = tuple(
            sorted(self.obligation_families, key=lambda value: value.encode("utf-8"))
        )
        if self.obligation_families != family_order:
            raise DomainCensusError("obligation_families must be byte-sorted")
        if len(set(self.obligation_families)) != len(self.obligation_families):
            raise DomainCensusError("obligation_families must be unique")
        _require_hash(self.public_packet_sha256, "public_packet_sha256")
        _require_hash(self.evaluator_commitment_sha256, "evaluator_commitment_sha256")
        if (
            type(self.source_rights_status) is not str
            or self.source_rights_status not in _RIGHTS_STATUSES
        ):
            raise DomainCensusError(
                "source_rights_status is not an accepted rights status"
            )
        _require_hash(self.blind_overlap_sha256, "blind_overlap_sha256")


@dataclass(frozen=True)
class DomainCensusV1:
    schema: str
    units: tuple[DomainUnitV1, ...]
    source_manifest_sha256: str

    def __post_init__(self) -> None:
        if type(self.schema) is not str or self.schema != _SCHEMA:
            raise DomainCensusError("schema is not the closed domain census schema")
        if type(self.units) is not tuple:
            raise DomainCensusError("units must be a tuple")
        if not self.units:
            raise DomainCensusError("units must be nonempty")
        if any(type(unit) is not DomainUnitV1 for unit in self.units):
            raise DomainCensusError("units must contain DomainUnitV1 values")
        pairs = [(unit.domain, unit.cluster_id, unit.unit_id) for unit in self.units]
        if len(set(pairs)) != len(pairs):
            raise DomainCensusError("cluster/unit pairs must be unique")
        if tuple(sorted(self.units, key=_unit_order_key)) != self.units:
            raise DomainCensusError("units must be byte-sorted")
        partitions_by_cluster: dict[tuple[str, str], set[str]] = {}
        for unit in self.units:
            partitions_by_cluster.setdefault((unit.domain, unit.cluster_id), set()).add(
                unit.partition
            )
        if any(len(partitions) != 1 for partitions in partitions_by_cluster.values()):
            raise DomainCensusError("audit and focal clusters must be disjoint")
        _require_hash(self.source_manifest_sha256, "source_manifest_sha256")

    @property
    def cluster_count(self) -> int:
        return len({(unit.domain, unit.cluster_id) for unit in self.units})


def _require_domain_census(census: object, domain: str) -> DomainCensusV1:
    if type(census) is not DomainCensusV1:
        raise DomainCensusError("census must be DomainCensusV1")
    if any(unit.domain != domain for unit in census.units):
        raise DomainCensusError(f"{domain} census must not pool domains")
    return census


def validate_architecture_census(census: DomainCensusV1) -> DomainCensusV1:
    """Validate the independent Architecture census without pooling any domain."""

    census = _require_domain_census(census, "architecture")
    audit = tuple(unit for unit in census.units if unit.partition == "audit")
    focal = tuple(unit for unit in census.units if unit.partition == "focal")
    audit_clusters = {unit.cluster_id for unit in audit}
    focal_clusters = {unit.cluster_id for unit in focal}
    if (
        len(audit_clusters) != 3
        or len(audit) < 24
        or len(focal_clusters) != 5
        or len(focal) < 40
    ):
        raise DomainCensusError(
            "architecture census requires 3 audit clusters/24 units and 5 focal clusters/40 units"
        )
    families = {family for unit in census.units for family in unit.obligation_families}
    if len(families) < 5:
        raise DomainCensusError("architecture census requires five obligation families")
    return census


def validate_jci_census(census: DomainCensusV1) -> DomainCensusV1:
    """Validate the independent JCI replication census without pooling domains."""

    census = _require_domain_census(census, "jci")
    clusters = {unit.cluster_id for unit in census.units}
    if len(clusters) < 8 or len(census.units) < 80:
        raise DomainCensusError(
            "jci census requires at least 8 repositories and 80 prefixes"
        )
    resource_units = tuple(
        unit for unit in census.units if "resource" in unit.obligation_families
    )
    if (
        len(resource_units) < 20
        or len({unit.cluster_id for unit in resource_units}) < 3
    ):
        raise DomainCensusError(
            "jci resource obligation requires 20 prefixes across three repositories"
        )
    return census


def _unit_payload(unit: DomainUnitV1) -> dict[str, Any]:
    return {
        "domain": unit.domain,
        "cluster_id": unit.cluster_id,
        "unit_id": unit.unit_id,
        "partition": unit.partition,
        "obligation_families": list(unit.obligation_families),
        "public_packet_sha256": unit.public_packet_sha256,
        "evaluator_commitment_sha256": unit.evaluator_commitment_sha256,
        "source_rights_status": unit.source_rights_status,
        "blind_overlap_sha256": unit.blind_overlap_sha256,
    }


def _census_payload(census: DomainCensusV1) -> dict[str, Any]:
    if type(census) is not DomainCensusV1:
        raise DomainCensusError("census must be DomainCensusV1")
    return {
        "schema": census.schema,
        "units": [_unit_payload(unit) for unit in census.units],
        "source_manifest_sha256": census.source_manifest_sha256,
    }


def domain_census_bytes(census: DomainCensusV1) -> bytes:
    """Return canonical UTF-8 JSON with sorted keys and exactly one final LF."""

    try:
        raw = json.dumps(
            _census_payload(census),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise DomainCensusError("census cannot be encoded as UTF-8 JSON") from exc
    return raw + b"\n"


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise DomainCensusError("duplicate JSON key")
        payload[key] = value
    return payload


def _parse_unit(value: object) -> DomainUnitV1:
    if type(value) is not dict or set(value) != _UNIT_KEYS:
        raise DomainCensusError("row keys do not match closed schema")
    families = value["obligation_families"]
    if type(families) is not list:
        raise DomainCensusError("obligation_families must be a JSON array")
    return DomainUnitV1(
        domain=value["domain"],
        cluster_id=value["cluster_id"],
        unit_id=value["unit_id"],
        partition=value["partition"],
        obligation_families=tuple(families),
        public_packet_sha256=value["public_packet_sha256"],
        evaluator_commitment_sha256=value["evaluator_commitment_sha256"],
        source_rights_status=value["source_rights_status"],
        blind_overlap_sha256=value["blind_overlap_sha256"],
    )


def verify_domain_census_bytes(raw: bytes) -> DomainCensusV1:
    """Parse a census only when its bytes are the unique canonical representation."""

    if type(raw) is not bytes:
        raise DomainCensusError("raw census must be bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                DomainCensusError(f"invalid JSON constant: {value}")
            ),
        )
    except DomainCensusError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise DomainCensusError("invalid census JSON") from exc
    if type(payload) is not dict or set(payload) != _ROOT_KEYS:
        raise DomainCensusError("root keys do not match closed schema")
    if type(payload["units"]) is not list:
        raise DomainCensusError("units must be a JSON array")
    census = DomainCensusV1(
        schema=payload["schema"],
        units=tuple(_parse_unit(unit) for unit in payload["units"]),
        source_manifest_sha256=payload["source_manifest_sha256"],
    )
    if raw != domain_census_bytes(census):
        raise DomainCensusError("census bytes are not canonical JSON")
    return census


__all__ = [
    "DomainCensusError",
    "DomainCensusV1",
    "DomainUnitV1",
    "domain_census_bytes",
    "validate_architecture_census",
    "validate_jci_census",
    "verify_domain_census_bytes",
]
