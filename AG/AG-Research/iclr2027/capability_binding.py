"""Opaque capability catalogs and evaluator-only Latin crossover bindings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
import re
from typing import Any

from .io import canonical_json as _canonical_json
from .io import sha256_json
from .obligation_contract import CoordinationAction


_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_SLOT_PATTERN = re.compile(r"slot:[0-9a-f]{64}\Z")
_SPECIALIST_ACTIONS = frozenset(
    {
        CoordinationAction.ASK_LAW.value,
        CoordinationAction.ASK_PARKING.value,
        CoordinationAction.ASK_PROGRAM.value,
        CoordinationAction.ASK_GEOMETRY.value,
    }
)
_PROFILE_CONTENT_KEYS = frozenset({"obligation_advantages", "incremental_cost"})
_PROFILE_KEYS = _PROFILE_CONTENT_KEYS | {"profile_id"}
_SLOT_KEYS = frozenset({"slot_id", "profile"})
_CATALOG_KEYS = frozenset(
    {
        "catalog_nonce",
        "obligation_catalog_sha256",
        "capability_audit_sha256",
        "slots",
    }
)
_PACKET_CONTENT_KEYS = frozenset(
    {
        "action",
        "prompt_sha256",
        "tool_manifest_sha256",
        "permission_manifest_sha256",
        "evidence_scope_sha256",
        "budget_contract_sha256",
        "output_schema_sha256",
        "model_runtime_sha256",
        "container_sha256",
    }
)
_PACKET_KEYS = _PACKET_CONTENT_KEYS | {"packet_id"}
_ASSIGNMENT_KEYS = frozenset({"slot_id", "packet"})
_BINDING_KEYS = frozenset({"catalog_sha256", "assignments"})
_REFERENCE_KEYS = frozenset({"slot_id", "profile_id", "packet_id"})
_PLAN_KEYS = frozenset(
    {
        "plan_id",
        "catalog_sha256",
        "obligation_catalog_sha256",
        "capability_audit_sha256",
        "crossover_seed_sha256",
        "aligned_reference",
        "aligned_arm_index",
        "arms",
    }
)


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    return value


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return value


def _require_exact_keys(
    payload: Mapping[str, Any],
    expected: frozenset[str],
    field_name: str,
) -> None:
    if any(not isinstance(key, str) for key in payload) or set(payload) != expected:
        missing = sorted(expected - set(payload))
        extra = sorted(str(key) for key in set(payload) - expected)
        raise ValueError(
            f"{field_name} must contain exact keys; missing={missing}, extra={extra}"
        )


def _sha256(value: Any, field_name: str) -> str:
    result = _required_text(value, field_name)
    if _SHA256_PATTERN.fullmatch(result) is None:
        raise ValueError(f"{field_name} must be an exact lowercase SHA-256")
    return result


def _prefixed_sha256(value: Any, prefix: str, field_name: str) -> str:
    result = _required_text(value, field_name)
    if not result.startswith(prefix) or _SHA256_PATTERN.fullmatch(
        result[len(prefix) :]
    ) is None:
        raise ValueError(f"{field_name} must be {prefix} plus a lowercase SHA-256")
    return result


def _finite_number(
    value: Any,
    field_name: str,
    *,
    minimum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    if minimum is not None and result < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return 0.0 if result == 0.0 else result


def _sequence(value: Any, field_name: str) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence")
    return tuple(value)


def _native_index(value: Any, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be a native integer")
    if not 0 <= value < 4:
        raise ValueError(f"{field_name} must be within [0, 3]")
    return value


def _obligation_id(value: Any) -> str:
    result = _required_text(value, "obligation_id")
    if result in {action.value for action in CoordinationAction}:
        raise ValueError("obligation_id cannot be a canonical execution action")
    return result


class _CanonicalContract:
    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def sha256(self) -> str:
        return sha256_json(self.to_dict())


@dataclass(frozen=True)
class CapabilityProfile(_CanonicalContract):
    obligation_advantages: tuple[tuple[str, float], ...]
    incremental_cost: float
    _profile_id: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        raw_advantages = _sequence(
            self.obligation_advantages, "obligation_advantages"
        )
        normalized: list[tuple[str, float]] = []
        for raw_pair in raw_advantages:
            pair = _sequence(raw_pair, "obligation advantage")
            if len(pair) != 2:
                raise ValueError(
                    "each obligation advantage must contain an ID and advantage"
                )
            normalized.append(
                (
                    _obligation_id(pair[0]),
                    _finite_number(pair[1], "obligation advantage"),
                )
            )
        normalized.sort(key=lambda pair: pair[0])
        ids = tuple(obligation_id for obligation_id, _ in normalized)
        if len(ids) != len(set(ids)):
            raise ValueError("obligation advantage IDs must be unique")
        object.__setattr__(self, "obligation_advantages", tuple(normalized))
        object.__setattr__(
            self,
            "incremental_cost",
            _finite_number(
                self.incremental_cost,
                "incremental_cost",
                minimum=0.0,
            ),
        )

    @property
    def profile_id(self) -> str:
        if self._profile_id is None:
            raise ValueError("profile_id is available only in a bound catalog")
        return self._profile_id

    def _content_dict(self) -> dict[str, Any]:
        return {
            "obligation_advantages": [
                [obligation_id, advantage]
                for obligation_id, advantage in self.obligation_advantages
            ],
            "incremental_cost": self.incremental_cost,
        }

    def _bound(self, catalog_nonce: str) -> "CapabilityProfile":
        bound = CapabilityProfile(
            self.obligation_advantages,
            self.incremental_cost,
        )
        object.__setattr__(
            bound,
            "_profile_id",
            "profile:"
            + sha256_json(
                {
                    "catalog_nonce": catalog_nonce,
                    "profile": bound._content_dict(),
                }
            ),
        )
        return bound

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        catalog_nonce: str | None = None,
    ) -> "CapabilityProfile":
        data = _require_mapping(payload, "capability profile")
        expected_keys = (
            _PROFILE_CONTENT_KEYS if catalog_nonce is None else _PROFILE_KEYS
        )
        _require_exact_keys(data, expected_keys, "capability profile")
        profile = cls(
            obligation_advantages=data["obligation_advantages"],
            incremental_cost=data["incremental_cost"],
        )
        if catalog_nonce is None:
            return profile
        bound = profile._bound(_sha256(catalog_nonce, "catalog_nonce"))
        supplied_id = _prefixed_sha256(
            data["profile_id"], "profile:", "profile_id"
        )
        if supplied_id != bound.profile_id:
            raise ValueError("stale profile_id")
        return bound

    def to_dict(self) -> dict[str, Any]:
        result = self._content_dict()
        if self._profile_id is not None:
            result = {"profile_id": self._profile_id, **result}
        return result


def _profile_sort_key(profile: CapabilityProfile) -> str:
    return _canonical_json(profile._content_dict())


@dataclass(frozen=True)
class OpaqueActionSlot(_CanonicalContract):
    slot_id: str
    profile: CapabilityProfile

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "slot_id",
            _prefixed_sha256(self.slot_id, "slot:", "slot_id"),
        )
        if type(self.profile) is not CapabilityProfile:
            raise TypeError("profile must be an exact CapabilityProfile")
        if self.profile._profile_id is None:
            raise ValueError("slot profile must be bound to a catalog nonce")

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        catalog_nonce: str,
        slot_index: int,
    ) -> "OpaqueActionSlot":
        data = _require_mapping(payload, "opaque action slot")
        _require_exact_keys(data, _SLOT_KEYS, "opaque action slot")
        nonce = _sha256(catalog_nonce, "catalog_nonce")
        index = _native_index(slot_index, "slot_index")
        supplied_slot_id = _prefixed_sha256(data["slot_id"], "slot:", "slot_id")
        expected_slot_id = "slot:" + sha256_json(
            {"catalog_nonce": nonce, "slot_index": index}
        )
        if supplied_slot_id != expected_slot_id:
            raise ValueError("stale slot_id")
        return cls(
            slot_id=supplied_slot_id,
            profile=CapabilityProfile.from_dict(
                _require_mapping(data["profile"], "capability profile"),
                catalog_nonce=nonce,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"slot_id": self.slot_id, "profile": self.profile.to_dict()}


@dataclass(frozen=True)
class ControllerCapabilityCatalog(_CanonicalContract):
    catalog_nonce: str
    obligation_catalog_sha256: str
    capability_audit_sha256: str
    slots: tuple[OpaqueActionSlot, ...]

    def __post_init__(self) -> None:
        nonce = _sha256(self.catalog_nonce, "catalog_nonce")
        object.__setattr__(self, "catalog_nonce", nonce)
        object.__setattr__(
            self,
            "obligation_catalog_sha256",
            _sha256(self.obligation_catalog_sha256, "obligation_catalog_sha256"),
        )
        object.__setattr__(
            self,
            "capability_audit_sha256",
            _sha256(self.capability_audit_sha256, "capability_audit_sha256"),
        )
        slots = _sequence(self.slots, "slots")
        if len(slots) != 4:
            raise ValueError("catalog must contain exactly four slots")
        if any(type(slot) is not OpaqueActionSlot for slot in slots):
            raise TypeError("slots must contain exact OpaqueActionSlot values")
        if len({slot.slot_id for slot in slots}) != 4:
            raise ValueError("catalog slot IDs must be unique")
        profile_ids = tuple(slot.profile.profile_id for slot in slots)
        if len(set(profile_ids)) != 4:
            raise ValueError("catalog profile IDs must be unique")
        sort_keys = tuple(_profile_sort_key(slot.profile) for slot in slots)
        if sort_keys != tuple(sorted(sort_keys)):
            raise ValueError("catalog profiles must be in canonical order")
        for index, slot in enumerate(slots):
            expected_slot_id = "slot:" + sha256_json(
                {"catalog_nonce": nonce, "slot_index": index}
            )
            if slot.slot_id != expected_slot_id:
                raise ValueError("slot_id does not match catalog nonce and index")
            expected_profile_id = "profile:" + sha256_json(
                {
                    "catalog_nonce": nonce,
                    "profile": slot.profile._content_dict(),
                }
            )
            if slot.profile.profile_id != expected_profile_id:
                raise ValueError("profile_id does not match catalog nonce and content")
        object.__setattr__(self, "slots", slots)

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any]
    ) -> "ControllerCapabilityCatalog":
        data = _require_mapping(payload, "controller capability catalog")
        _require_exact_keys(data, _CATALOG_KEYS, "controller capability catalog")
        nonce = _sha256(data["catalog_nonce"], "catalog_nonce")
        raw_slots = _sequence(data["slots"], "slots")
        return cls(
            catalog_nonce=nonce,
            obligation_catalog_sha256=data["obligation_catalog_sha256"],
            capability_audit_sha256=data["capability_audit_sha256"],
            slots=tuple(
                OpaqueActionSlot.from_dict(
                    _require_mapping(slot, "opaque action slot"),
                    catalog_nonce=nonce,
                    slot_index=index,
                )
                for index, slot in enumerate(raw_slots)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_nonce": self.catalog_nonce,
            "obligation_catalog_sha256": self.obligation_catalog_sha256,
            "capability_audit_sha256": self.capability_audit_sha256,
            "slots": [slot.to_dict() for slot in self.slots],
        }


@dataclass(frozen=True)
class CapabilityPacketManifest(_CanonicalContract):
    action: str
    prompt_sha256: str
    tool_manifest_sha256: str
    permission_manifest_sha256: str
    evidence_scope_sha256: str
    budget_contract_sha256: str
    output_schema_sha256: str
    model_runtime_sha256: str
    container_sha256: str

    def __post_init__(self) -> None:
        action = self.action
        if isinstance(action, CoordinationAction):
            action = action.value
        if not isinstance(action, str):
            raise TypeError("action must be a string or CoordinationAction")
        if action not in _SPECIALIST_ACTIONS:
            raise ValueError("action must be one of the four specialist ASK actions")
        object.__setattr__(self, "action", action)
        for field_name in (
            "prompt_sha256",
            "tool_manifest_sha256",
            "permission_manifest_sha256",
            "evidence_scope_sha256",
            "budget_contract_sha256",
            "output_schema_sha256",
            "model_runtime_sha256",
            "container_sha256",
        ):
            object.__setattr__(
                self,
                field_name,
                _sha256(getattr(self, field_name), field_name),
            )

    def _manifest_dict(self) -> dict[str, str]:
        return {
            "action": self.action,
            "prompt_sha256": self.prompt_sha256,
            "tool_manifest_sha256": self.tool_manifest_sha256,
            "permission_manifest_sha256": self.permission_manifest_sha256,
            "evidence_scope_sha256": self.evidence_scope_sha256,
            "budget_contract_sha256": self.budget_contract_sha256,
            "output_schema_sha256": self.output_schema_sha256,
            "model_runtime_sha256": self.model_runtime_sha256,
            "container_sha256": self.container_sha256,
        }

    @property
    def packet_id(self) -> str:
        return "packet:" + sha256_json(self._manifest_dict())

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any]
    ) -> "CapabilityPacketManifest":
        data = _require_mapping(payload, "capability packet manifest")
        _require_exact_keys(data, _PACKET_KEYS, "capability packet manifest")
        packet = cls(**{key: data[key] for key in _PACKET_CONTENT_KEYS})
        supplied_id = _prefixed_sha256(
            data["packet_id"], "packet:", "packet_id"
        )
        if supplied_id != packet.packet_id:
            raise ValueError("stale packet_id")
        return packet

    def to_dict(self) -> dict[str, Any]:
        return {"packet_id": self.packet_id, **self._manifest_dict()}


@dataclass(frozen=True)
class ExecutionCapabilityBinding(_CanonicalContract):
    catalog_sha256: str
    assignments: tuple[tuple[str, CapabilityPacketManifest], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "catalog_sha256",
            _sha256(self.catalog_sha256, "catalog_sha256"),
        )
        raw_assignments = _sequence(self.assignments, "assignments")
        if len(raw_assignments) != 4:
            raise ValueError("binding must contain exactly four assignments")
        assignments: list[tuple[str, CapabilityPacketManifest]] = []
        for raw_assignment in raw_assignments:
            assignment = _sequence(raw_assignment, "assignment")
            if len(assignment) != 2:
                raise ValueError("each assignment must contain slot_id and packet")
            slot_id = _prefixed_sha256(assignment[0], "slot:", "slot_id")
            packet = assignment[1]
            if type(packet) is not CapabilityPacketManifest:
                raise TypeError("assignment packet must be an exact manifest")
            assignments.append((slot_id, packet))
        assignments.sort(key=lambda assignment: assignment[0])
        slot_ids = tuple(slot_id for slot_id, _ in assignments)
        packets = tuple(packet for _, packet in assignments)
        if len(set(slot_ids)) != 4:
            raise ValueError("binding slot IDs must be unique")
        if len({packet.packet_id for packet in packets}) != 4:
            raise ValueError("binding packets must be unique")
        if {packet.action for packet in packets} != _SPECIALIST_ACTIONS:
            raise ValueError("binding must contain each specialist action exactly once")
        object.__setattr__(self, "assignments", tuple(assignments))

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any]
    ) -> "ExecutionCapabilityBinding":
        data = _require_mapping(payload, "execution capability binding")
        _require_exact_keys(data, _BINDING_KEYS, "execution capability binding")
        raw_assignments = _sequence(data["assignments"], "assignments")
        assignments: list[tuple[str, CapabilityPacketManifest]] = []
        for raw_assignment in raw_assignments:
            assignment = _require_mapping(raw_assignment, "assignment")
            _require_exact_keys(assignment, _ASSIGNMENT_KEYS, "assignment")
            assignments.append(
                (
                    assignment["slot_id"],
                    CapabilityPacketManifest.from_dict(
                        _require_mapping(assignment["packet"], "packet manifest")
                    ),
                )
            )
        return cls(data["catalog_sha256"], tuple(assignments))

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_sha256": self.catalog_sha256,
            "assignments": [
                {"slot_id": slot_id, "packet": packet.to_dict()}
                for slot_id, packet in self.assignments
            ],
        }


def _plan_content(
    catalog_sha256: str,
    obligation_catalog_sha256: str,
    capability_audit_sha256: str,
    crossover_seed_sha256: str,
    aligned_reference: tuple[tuple[str, str, str], ...],
    aligned_arm_index: int,
    arms: tuple[ExecutionCapabilityBinding, ...],
) -> dict[str, Any]:
    return {
        "catalog_sha256": catalog_sha256,
        "obligation_catalog_sha256": obligation_catalog_sha256,
        "capability_audit_sha256": capability_audit_sha256,
        "crossover_seed_sha256": crossover_seed_sha256,
        "aligned_reference": [
            {
                "slot_id": slot_id,
                "profile_id": profile_id,
                "packet_id": packet_id,
            }
            for slot_id, profile_id, packet_id in aligned_reference
        ],
        "aligned_arm_index": aligned_arm_index,
        "arms": [arm.to_dict() for arm in arms],
    }


def _seed_shifts(seed: str) -> tuple[int, ...]:
    direction = 1 if int(seed[0], 16) % 2 == 0 else -1
    shifts = tuple((direction * index) % 4 for index in range(4))
    rotation = int(seed[1], 16) % 4
    return shifts[rotation:] + shifts[:rotation]


@dataclass(frozen=True)
class CapabilityCrossoverPlan(_CanonicalContract):
    plan_id: str
    catalog_sha256: str
    obligation_catalog_sha256: str
    capability_audit_sha256: str
    crossover_seed_sha256: str
    aligned_reference: tuple[tuple[str, str, str], ...]
    aligned_arm_index: int
    arms: tuple[ExecutionCapabilityBinding, ...]

    def __post_init__(self) -> None:
        plan_id = _prefixed_sha256(self.plan_id, "plan:", "plan_id")
        catalog_hash = _sha256(self.catalog_sha256, "catalog_sha256")
        ontology_hash = _sha256(
            self.obligation_catalog_sha256, "obligation_catalog_sha256"
        )
        audit_hash = _sha256(
            self.capability_audit_sha256, "capability_audit_sha256"
        )
        seed = _sha256(self.crossover_seed_sha256, "crossover_seed_sha256")
        aligned_arm_index = _native_index(
            self.aligned_arm_index, "aligned_arm_index"
        )
        raw_reference = _sequence(self.aligned_reference, "aligned_reference")
        if len(raw_reference) != 4:
            raise ValueError("aligned_reference must contain exactly four entries")
        aligned_reference: list[tuple[str, str, str]] = []
        for raw_entry in raw_reference:
            entry = _sequence(raw_entry, "aligned reference entry")
            if len(entry) != 3:
                raise ValueError(
                    "aligned reference entries must contain slot, profile, and packet IDs"
                )
            aligned_reference.append(
                (
                    _prefixed_sha256(entry[0], "slot:", "slot_id"),
                    _prefixed_sha256(entry[1], "profile:", "profile_id"),
                    _prefixed_sha256(entry[2], "packet:", "packet_id"),
                )
            )
        reference = tuple(aligned_reference)
        if len({entry[0] for entry in reference}) != 4:
            raise ValueError("aligned reference slot IDs must be unique")
        if len({entry[1] for entry in reference}) != 4:
            raise ValueError("aligned reference profile IDs must be unique")
        if len({entry[2] for entry in reference}) != 4:
            raise ValueError("aligned reference packet IDs must be unique")
        arms = _sequence(self.arms, "arms")
        if len(arms) != 4:
            raise ValueError("crossover plan must contain exactly four arms")
        if any(type(arm) is not ExecutionCapabilityBinding for arm in arms):
            raise TypeError("arms must contain exact execution bindings")
        if any(arm.catalog_sha256 != catalog_hash for arm in arms):
            raise ValueError("every arm must bind the plan catalog hash")
        if len({arm.sha256() for arm in arms}) != 4:
            raise ValueError("crossover arms must be unique")
        reference_slots = {entry[0] for entry in reference}
        reference_packets = {entry[2] for entry in reference}
        for arm in arms:
            if {slot_id for slot_id, _ in arm.assignments} != reference_slots:
                raise ValueError("every arm must bind the aligned reference slots")
            if {
                packet.packet_id for _, packet in arm.assignments
            } != reference_packets:
                raise ValueError("every arm must bind the aligned reference packets")
        ordered_shifts = _seed_shifts(seed)
        expected_aligned_index = ordered_shifts.index(0)
        if aligned_arm_index != expected_aligned_index:
            raise ValueError("aligned_arm_index is inconsistent with crossover seed")
        for arm_index, (arm, shift) in enumerate(zip(arms, ordered_shifts, strict=True)):
            observed_assignment = {
                slot_id: packet.packet_id for slot_id, packet in arm.assignments
            }
            expected_assignment = {
                entry[0]: reference[(index + shift) % 4][2]
                for index, entry in enumerate(reference)
            }
            if observed_assignment != expected_assignment:
                raise ValueError(
                    f"arm {arm_index} order is inconsistent with crossover seed"
                )
        expected_plan_id = "plan:" + sha256_json(
            _plan_content(
                catalog_hash,
                ontology_hash,
                audit_hash,
                seed,
                reference,
                aligned_arm_index,
                arms,
            )
        )
        if plan_id != expected_plan_id:
            raise ValueError("plan_id does not match the plan content")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "catalog_sha256", catalog_hash)
        object.__setattr__(self, "obligation_catalog_sha256", ontology_hash)
        object.__setattr__(self, "capability_audit_sha256", audit_hash)
        object.__setattr__(self, "crossover_seed_sha256", seed)
        object.__setattr__(self, "aligned_reference", reference)
        object.__setattr__(self, "aligned_arm_index", aligned_arm_index)
        object.__setattr__(self, "arms", arms)

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any]
    ) -> "CapabilityCrossoverPlan":
        data = _require_mapping(payload, "capability crossover plan")
        _require_exact_keys(data, _PLAN_KEYS, "capability crossover plan")
        raw_reference = _sequence(data["aligned_reference"], "aligned_reference")
        reference: list[tuple[str, str, str]] = []
        for raw_entry in raw_reference:
            entry = _require_mapping(raw_entry, "aligned reference entry")
            _require_exact_keys(entry, _REFERENCE_KEYS, "aligned reference entry")
            reference.append(
                (entry["slot_id"], entry["profile_id"], entry["packet_id"])
            )
        raw_arms = _sequence(data["arms"], "arms")
        return cls(
            plan_id=data["plan_id"],
            catalog_sha256=data["catalog_sha256"],
            obligation_catalog_sha256=data["obligation_catalog_sha256"],
            capability_audit_sha256=data["capability_audit_sha256"],
            crossover_seed_sha256=data["crossover_seed_sha256"],
            aligned_reference=tuple(reference),
            aligned_arm_index=data["aligned_arm_index"],
            arms=tuple(
                ExecutionCapabilityBinding.from_dict(
                    _require_mapping(arm, "execution capability binding")
                )
                for arm in raw_arms
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            **_plan_content(
                self.catalog_sha256,
                self.obligation_catalog_sha256,
                self.capability_audit_sha256,
                self.crossover_seed_sha256,
                self.aligned_reference,
                self.aligned_arm_index,
                self.arms,
            ),
        }


def build_controller_catalog(
    profiles_in_canonical_order: Sequence[CapabilityProfile],
    catalog_nonce: str,
    obligation_catalog_sha256: str,
    capability_audit_sha256: str,
) -> ControllerCapabilityCatalog:
    """Build controller-visible opaque slots without execution information."""

    nonce = _sha256(catalog_nonce, "catalog_nonce")
    _sha256(obligation_catalog_sha256, "obligation_catalog_sha256")
    _sha256(capability_audit_sha256, "capability_audit_sha256")
    profiles = _sequence(profiles_in_canonical_order, "profiles_in_canonical_order")
    if len(profiles) != 4:
        raise ValueError("exactly four capability profiles are required")
    if any(type(profile) is not CapabilityProfile for profile in profiles):
        raise TypeError("profiles must contain exact CapabilityProfile values")
    sort_keys = tuple(_profile_sort_key(profile) for profile in profiles)
    if sort_keys != tuple(sorted(sort_keys)):
        raise ValueError("profiles_in_canonical_order is not canonically ordered")
    if len(set(sort_keys)) != 4:
        raise ValueError("capability profiles must be unique")
    slots = tuple(
        OpaqueActionSlot(
            "slot:" + sha256_json({"catalog_nonce": nonce, "slot_index": index}),
            profile._bound(nonce),
        )
        for index, profile in enumerate(profiles)
    )
    return ControllerCapabilityCatalog(
        nonce,
        obligation_catalog_sha256,
        capability_audit_sha256,
        slots,
    )


def assert_unique_catalog_nonces(
    catalogs: Sequence[ControllerCapabilityCatalog],
) -> None:
    """Reject nonce reuse; callers must supply never-reused cryptographic nonces."""

    values = _sequence(catalogs, "catalogs")
    if any(type(catalog) is not ControllerCapabilityCatalog for catalog in values):
        raise TypeError("catalogs must contain exact controller catalogs")
    nonces = tuple(catalog.catalog_nonce for catalog in values)
    if len(nonces) != len(set(nonces)):
        raise ValueError("catalog nonce reuse detected")


def _make_plan(
    catalog_sha256: str,
    obligation_catalog_sha256: str,
    capability_audit_sha256: str,
    crossover_seed_sha256: str,
    aligned_reference: tuple[tuple[str, str, str], ...],
    aligned_arm_index: int,
    arms: tuple[ExecutionCapabilityBinding, ...],
) -> CapabilityCrossoverPlan:
    plan_id = "plan:" + sha256_json(
        _plan_content(
            catalog_sha256,
            obligation_catalog_sha256,
            capability_audit_sha256,
            crossover_seed_sha256,
            aligned_reference,
            aligned_arm_index,
            arms,
        )
    )
    return CapabilityCrossoverPlan(
        plan_id,
        catalog_sha256,
        obligation_catalog_sha256,
        capability_audit_sha256,
        crossover_seed_sha256,
        aligned_reference,
        aligned_arm_index,
        arms,
    )


def build_crossover_plan(
    catalog: ControllerCapabilityCatalog,
    aligned_packets_in_profile_order: Sequence[CapabilityPacketManifest],
    crossover_seed_sha256: str,
) -> CapabilityCrossoverPlan:
    """Build the evaluator-only aligned arm and cyclic Latin crossover."""

    if type(catalog) is not ControllerCapabilityCatalog:
        raise TypeError("catalog must be an exact ControllerCapabilityCatalog")
    seed = _sha256(crossover_seed_sha256, "crossover_seed_sha256")
    packets = _sequence(
        aligned_packets_in_profile_order,
        "aligned_packets_in_profile_order",
    )
    if len(packets) != 4:
        raise ValueError("exactly four aligned packets are required")
    if any(type(packet) is not CapabilityPacketManifest for packet in packets):
        raise TypeError("packets must contain exact packet manifests")
    if len({packet.packet_id for packet in packets}) != 4:
        raise ValueError("aligned packets must be unique")
    if {packet.action for packet in packets} != _SPECIALIST_ACTIONS:
        raise ValueError("aligned packets must contain all specialist actions")

    ordered_shifts = _seed_shifts(seed)
    catalog_hash = catalog.sha256()
    aligned_reference = tuple(
        (slot.slot_id, slot.profile.profile_id, packet.packet_id)
        for slot, packet in zip(catalog.slots, packets, strict=True)
    )
    aligned_arm_index = ordered_shifts.index(0)
    arms = tuple(
        ExecutionCapabilityBinding(
            catalog_hash,
            tuple(
                (
                    slot.slot_id,
                    packets[(index + shift) % 4],
                )
                for index, slot in enumerate(catalog.slots)
            ),
        )
        for shift in ordered_shifts
    )
    plan = _make_plan(
        catalog_hash,
        catalog.obligation_catalog_sha256,
        catalog.capability_audit_sha256,
        seed,
        aligned_reference,
        aligned_arm_index,
        arms,
    )
    validate_crossover_plan(catalog, plan)
    return plan


def validate_crossover_plan(
    catalog: ControllerCapabilityCatalog,
    plan: CapabilityCrossoverPlan,
) -> None:
    """Authenticate a structurally valid plan against its exact catalog."""

    if type(catalog) is not ControllerCapabilityCatalog:
        raise TypeError("catalog must be an exact ControllerCapabilityCatalog")
    if type(plan) is not CapabilityCrossoverPlan:
        raise TypeError("plan must be an exact CapabilityCrossoverPlan")
    if plan.catalog_sha256 != catalog.sha256():
        raise ValueError("plan catalog hash does not match the supplied catalog")
    if plan.obligation_catalog_sha256 != catalog.obligation_catalog_sha256:
        raise ValueError("plan ontology hash does not match the supplied catalog")
    if plan.capability_audit_sha256 != catalog.capability_audit_sha256:
        raise ValueError(
            "plan capability-audit hash does not match the supplied catalog"
        )
    expected_reference = tuple(
        (slot.slot_id, slot.profile.profile_id) for slot in catalog.slots
    )
    observed_reference = tuple(
        (slot_id, profile_id)
        for slot_id, profile_id, _packet_id in plan.aligned_reference
    )
    if observed_reference != expected_reference:
        raise ValueError("plan catalog slot/profile reference does not match catalog")
    catalog_slots = {slot.slot_id for slot in catalog.slots}
    for arm in plan.arms:
        if {slot_id for slot_id, _packet in arm.assignments} != catalog_slots:
            raise ValueError("plan arm catalog slot set does not match catalog")


def relabel_crossover(
    catalog: ControllerCapabilityCatalog,
    plan: CapabilityCrossoverPlan,
    new_catalog_nonce: str,
) -> tuple[ControllerCapabilityCatalog, CapabilityCrossoverPlan]:
    """Relabel opaque slots while preserving every evaluator assignment."""

    if type(catalog) is not ControllerCapabilityCatalog:
        raise TypeError("catalog must be an exact ControllerCapabilityCatalog")
    if type(plan) is not CapabilityCrossoverPlan:
        raise TypeError("plan must be an exact CapabilityCrossoverPlan")
    validate_crossover_plan(catalog, plan)
    nonce = _sha256(new_catalog_nonce, "new_catalog_nonce")
    if nonce == catalog.catalog_nonce:
        raise ValueError("relabeling requires a new catalog nonce")
    new_catalog = build_controller_catalog(
        tuple(slot.profile for slot in catalog.slots),
        nonce,
        catalog.obligation_catalog_sha256,
        catalog.capability_audit_sha256,
    )
    renamed_slots = {
        old.slot_id: new.slot_id
        for old, new in zip(catalog.slots, new_catalog.slots, strict=True)
    }
    new_catalog_hash = new_catalog.sha256()
    new_arms = tuple(
        ExecutionCapabilityBinding(
            new_catalog_hash,
            tuple(
                (renamed_slots[slot_id], packet)
                for slot_id, packet in arm.assignments
            ),
        )
        for arm in plan.arms
    )
    new_reference = tuple(
        (new_slot.slot_id, new_slot.profile.profile_id, old_reference[2])
        for new_slot, old_reference in zip(
            new_catalog.slots,
            plan.aligned_reference,
            strict=True,
        )
    )
    new_plan = _make_plan(
        new_catalog_hash,
        new_catalog.obligation_catalog_sha256,
        new_catalog.capability_audit_sha256,
        plan.crossover_seed_sha256,
        new_reference,
        plan.aligned_arm_index,
        new_arms,
    )
    validate_crossover_plan(new_catalog, new_plan)
    return new_catalog, new_plan


def controller_catalog_bytes(catalog: ControllerCapabilityCatalog) -> bytes:
    """Return the complete and only controller-facing capability payload."""

    if type(catalog) is not ControllerCapabilityCatalog:
        raise TypeError("controller serialization accepts only an exact catalog")
    return catalog.canonical_json().encode("utf-8")


__all__ = (
    "CapabilityCrossoverPlan",
    "CapabilityPacketManifest",
    "CapabilityProfile",
    "ControllerCapabilityCatalog",
    "ExecutionCapabilityBinding",
    "OpaqueActionSlot",
    "assert_unique_catalog_nonces",
    "build_controller_catalog",
    "build_crossover_plan",
    "controller_catalog_bytes",
    "relabel_crossover",
    "validate_crossover_plan",
)
