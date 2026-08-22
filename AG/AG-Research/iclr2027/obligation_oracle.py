"""Synthetic, zero-call Task 5 Phase-A E2/E3 contracts.

Nothing in this module authenticates or opens a Phase-B source.  The records
are deliberately inert algebra fixtures with strict canonical serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import math
from typing import Any, ClassVar


_SCHEMA_DOMAIN = "ace.iclr2027.synthetic_task5_phase_a.v2"
_SCHEMA_PREFIX = _SCHEMA_DOMAIN + "."
_HEX = frozenset("0123456789abcdef")
_OPAQUE_KINDS = frozenset({"slot", "packet", "assignment", "control"})
_TREATMENTS = frozenset({"stop", "solo_synthesis", "capability_packet"})
_MEASURE_KINDS = frozenset({"frozen_stratum", "predeclared_continuous_secondary"})
_ALIGNMENT_ROLES = frozenset({"high", "low", "residual_absent_control"})
_EFFECT_STRATA = frozenset(
    {"matched_residual_present", "matched_residual_absent", "not_applicable"}
)
_SUPPORT_STATUSES = frozenset({"adequate", "weak", "empty"})
_COMPLIANCE_STATUSES = frozenset(
    {"verified", "noncompliant", "attrited_predeclared"}
)
_AUXILIARY_CONTROL_KINDS = frozenset(
    {"global_bundle_strength", "uniform_random_admissible"}
)
_READINESS_STATUSES = frozenset(
    {
        "supported",
        "unsupported_official_interface",
        "unsupported_missing_dependency",
        "inapplicable_predeclared_amendment",
    }
)
_READINESS_REASONS = frozenset(
    {
        "ready_verified",
        "official_interface_absent",
        "official_interface_incompatible",
        "dependency_unavailable",
        "license_or_access_blocked",
        "domain_inapplicable",
        "faithfulness_failed",
    }
)
_BASELINE_IDS = (
    "agentprune",
    "agora",
    "always_all_specialists",
    "automix",
    "bicsrouter",
    "conformal_thinking",
    "cost_aware_protocol_routing",
    "difficulty_confidence",
    "fixed_topology",
    "gptswarm",
    "graphplanner",
    "masrouter",
    "matched_compute_self_agent_scaling",
    "random_admissible_action",
    "rirs_talk_to_right_specialists",
    "routellm",
    "self_resource_allocation",
    "separated_router_stopper",
    "solo",
    "verimap",
    "vmao",
    "zooter_adaptation",
)
_INTERNAL_BASELINES = frozenset(
    {
        "always_all_specialists",
        "difficulty_confidence",
        "fixed_topology",
        "random_admissible_action",
        "separated_router_stopper",
        "solo",
    }
)
_E3_PARENT_SCHEMA = _SCHEMA_DOMAIN + ".e3_source_parent"
_E3_PROJECTION_SCHEMA = _SCHEMA_DOMAIN + ".e3_projection_spec"
_E3_PARENT_FIELDS = (
    "site_ref",
    "case_ref",
    "prefix_ref",
    "raw_transcript_prefix",
    "numeric_residual_serialization",
    "complete_capability_table",
    "opaque_packet_binding_cards",
    "costs",
    "admissibility",
    "examples",
    "split_fold",
    "learner_class_capacity",
    "tuning_optimization_opportunity",
    "target_action_roster",
    "action_space_tie_rule",
)
_E3_SHARED_FIELDS = (
    "costs",
    "admissibility",
    "examples",
    "split_fold",
    "learner_class_capacity",
    "tuning_optimization_opportunity",
    "action_space_tie_rule",
)
_E3_TIE_RULE = "max_blind_direct_value_then_roster_order"


class NeedsContextError(RuntimeError):
    """Raised before any Phase-B path construction or I/O."""


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("value is not strict canonical JSON") from error


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_value(value: object) -> str:
    return _sha_bytes(_canonical(value).encode("utf-8"))


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("JSON object has duplicate or non-string key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _loads_strict(raw: str) -> object:
    if type(raw) is not str or raw.startswith("\ufeff"):
        raise ValueError("raw JSON must be exact UTF-8 text without BOM")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("invalid strict JSON") from error
    if _has_negative_signed_zero(value):
        raise ValueError("JSON contains negative signed zero")
    if raw != _canonical(value):
        raise ValueError("JSON is not canonical")
    return value


def _has_negative_signed_zero(value: object) -> bool:
    if type(value) is float:
        return value == 0.0 and math.copysign(1.0, value) < 0.0
    if type(value) is list:
        return any(_has_negative_signed_zero(item) for item in value)
    if type(value) is dict:
        return any(_has_negative_signed_zero(item) for item in value.values())
    return False


def _normal_zero(value: object) -> object:
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("numeric value must be finite")
        return 0.0 if value == 0.0 else value
    if type(value) is tuple:
        return tuple(_normal_zero(item) for item in value)
    return value


def _require_str(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise TypeError(f"{name} must be a nonempty exact str")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{name} contains a control character")
    return value


def _require_identifier(value: object, name: str) -> str:
    text = _require_str(value, name)
    if "/" in text or "\\" in text or text in {".", ".."}:
        raise ValueError(f"{name} is not an opaque identifier")
    return text


def _require_opaque_id(value: object, name: str) -> str:
    identifier = _require_str(value, name)
    if (
        len(identifier) != 67
        or not identifier.startswith("o5_")
        or any(char not in _HEX for char in identifier[3:])
    ):
        raise ValueError(f"{name} must be a registry-derived opaque ID")
    return identifier


def _require_hash(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in _HEX for char in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


def _optional_hash(value: object, name: str) -> None:
    if value is not None:
        _require_hash(value, name)


def _require_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise TypeError(f"{name} must be a native int >= {minimum}")
    return value


def _require_float(
    value: object,
    name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    positive: bool = False,
) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise TypeError(f"{name} must be a native finite float")
    if positive and value <= 0.0:
        raise ValueError(f"{name} must be positive")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} is below its minimum")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} is above its maximum")
    return value


def _require_hash_tuple(value: object, name: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple or (nonempty and not value):
        raise TypeError(f"{name} must be an exact tuple")
    for item in value:
        _require_hash(item, name)
    if tuple(sorted(value, key=lambda item: item.encode("ascii"))) != value:
        raise ValueError(f"{name} must be byte sorted")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must be unique")
    return value


def _plain(value: object) -> object:
    if isinstance(value, _Record):
        return value.to_dict()
    if type(value) is bytes:
        try:
            return value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError("bytes field is not UTF-8") from error
    if type(value) is tuple:
        return [_plain(item) for item in value]
    if value is None or type(value) in {str, bool, int, float}:
        return value
    raise TypeError("record contains a noncanonical native value")


class _Record:
    __slots__ = ()

    SCHEMA: ClassVar[str]
    HASH_FIELD: ClassVar[str]
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset()
    BYTES_FIELDS: ClassVar[frozenset[str]] = frozenset()
    RECORD_FIELDS: ClassVar[dict[str, type[_Record]]] = {}
    RECORD_TUPLE_FIELDS: ClassVar[dict[str, type[_Record]]] = {}

    def __post_init__(self) -> None:
        for field in fields(self):
            if field.name != self.HASH_FIELD:
                object.__setattr__(self, field.name, _normal_zero(getattr(self, field.name)))
        if self.synthetic_only is not True:  # type: ignore[attr-defined]
            raise ValueError("record must be synthetic_only=True")
        self._validate()
        observed = getattr(self, self.HASH_FIELD)
        _require_hash(observed, self.HASH_FIELD)
        unsigned = self.to_dict()
        unsigned.pop(self.HASH_FIELD)
        if observed != _sha_value(unsigned):
            raise ValueError("record self-hash mismatch")

    def _validate(self) -> None:
        return None

    @classmethod
    def create(cls, **values: object) -> Any:
        names = tuple(field.name for field in fields(cls))
        allowed = set(names) - {"synthetic_only", cls.HASH_FIELD}
        if set(values) != allowed:
            raise ValueError(f"{cls.__name__}.create has missing or extra fields")
        normalized = {name: _normal_zero(value) for name, value in values.items()}
        normalized["synthetic_only"] = True
        unsigned: dict[str, object] = {}
        if "schema_version" not in names:
            unsigned["schema_version"] = cls.SCHEMA
        unsigned.update({name: _plain(normalized[name]) for name in names if name != cls.HASH_FIELD})
        normalized[cls.HASH_FIELD] = _sha_value(unsigned)
        return cls(**normalized)

    @classmethod
    def from_dict(cls, value: object) -> Any:
        if type(value) is not dict or any(type(key) is not str for key in value):
            raise TypeError("record must be an exact dict with string keys")
        names = tuple(field.name for field in fields(cls))
        expected = set(names)
        if "schema_version" not in names:
            expected.add("schema_version")
        if set(value) != expected:
            raise ValueError("record has missing or extra keys")
        if "schema_version" not in names and value["schema_version"] != cls.SCHEMA:
            raise ValueError("record schema mismatch")
        converted: dict[str, object] = {}
        for name in names:
            item = value[name]
            if name in cls.BYTES_FIELDS:
                if type(item) is not str:
                    raise TypeError(f"{name} must serialize as exact str")
                converted[name] = item.encode("utf-8")
            elif name in cls.RECORD_FIELDS:
                converted[name] = cls.RECORD_FIELDS[name].from_dict(item)
            elif name in cls.RECORD_TUPLE_FIELDS:
                if type(item) is not list:
                    raise TypeError(f"{name} must serialize as exact list")
                converted[name] = tuple(
                    cls.RECORD_TUPLE_FIELDS[name].from_dict(child) for child in item
                )
            elif name in cls.TUPLE_FIELDS:
                if type(item) is not list:
                    raise TypeError(f"{name} must serialize as exact list")
                converted[name] = tuple(item)
            else:
                converted[name] = item
        return cls(**converted)

    @classmethod
    def from_json(cls, raw: str | bytes) -> Any:
        if type(raw) is bytes:
            try:
                text = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise ValueError("raw JSON is not UTF-8") from error
        elif type(raw) is str:
            text = raw
        else:
            raise TypeError("raw JSON must be exact str or bytes")
        return cls.from_dict(_loads_strict(text))

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {}
        names = tuple(field.name for field in fields(self))
        if "schema_version" not in names:
            result["schema_version"] = self.SCHEMA
        for field in fields(self):
            result[field.name] = _plain(getattr(self, field.name))
        return result

    def canonical_json(self) -> str:
        return _canonical(self.to_dict())


def _validate_collection(
    value: object,
    expected_type: type[_Record],
    hash_name: str,
    name: str,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be an exact tuple")
    for row in value:
        if type(row) is not expected_type:
            raise TypeError(f"{name} contains a foreign record")
    hashes = tuple(getattr(row, hash_name) for row in value)
    if hashes != tuple(sorted(hashes, key=lambda item: item.encode("ascii"))):
        raise ValueError(f"{name} is not canonical")
    if len(hashes) != len(set(hashes)):
        raise ValueError(f"{name} contains a duplicate")


@dataclass(frozen=True, slots=True)
class SyntheticOpaqueIdentityRegistryV2(_Record):
    derivation_seed_sha256: str
    entries: tuple[tuple[str, int, str], ...]
    packet_manifest_bindings: tuple[tuple[str, str], ...]
    synthetic_only: bool
    registry_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticOpaqueIdentityRegistryV2.v2"
    HASH_FIELD = "registry_sha256"
    TUPLE_FIELDS = frozenset({"entries", "packet_manifest_bindings"})

    @classmethod
    def from_dict(cls, value: object) -> Any:
        if type(value) is not dict:
            raise TypeError("registry must be an exact dict")
        converted = dict(value)
        for name, length in (("entries", 3), ("packet_manifest_bindings", 2)):
            rows = converted.get(name)
            if type(rows) is not list:
                raise TypeError(f"{name} must serialize as an exact list")
            if any(type(row) is not list or len(row) != length for row in rows):
                raise TypeError(f"{name} rows must serialize as exact lists")
            converted[name] = [tuple(row) for row in rows]
        return _Record.from_dict.__func__(cls, converted)

    def _validate(self) -> None:
        _require_hash(self.derivation_seed_sha256, "derivation_seed_sha256")
        if type(self.entries) is not tuple or not self.entries:
            raise TypeError("entries must be a nonempty exact tuple")
        previous: tuple[bytes, int] | None = None
        seen_pairs: set[tuple[str, int]] = set()
        seen_ids: set[str] = set()
        for entry in self.entries:
            if type(entry) is not tuple or len(entry) != 3:
                raise TypeError("registry entries must be exact triples")
            kind, ordinal, opaque_id = entry
            if type(kind) is not str or kind not in _OPAQUE_KINDS:
                raise ValueError("registry entry has invalid kind")
            _require_int(ordinal, "registry ordinal")
            _require_opaque_id(opaque_id, "registry opaque ID")
            expected = "o5_" + _sha_value(
                [_SCHEMA_DOMAIN, self.derivation_seed_sha256, kind, ordinal]
            )
            if opaque_id != expected:
                raise ValueError("registry opaque ID is not derived from its entry")
            order = (kind.encode("ascii"), ordinal)
            if previous is not None and order <= previous:
                raise ValueError("registry entries are not byte sorted and unique")
            previous = order
            if (kind, ordinal) in seen_pairs or opaque_id in seen_ids:
                raise ValueError("registry entries are not one-to-one")
            seen_pairs.add((kind, ordinal))
            seen_ids.add(opaque_id)
        if type(self.packet_manifest_bindings) is not tuple:
            raise TypeError("packet_manifest_bindings must be an exact tuple")
        previous_packet: bytes | None = None
        bindings: dict[str, str] = {}
        manifests: set[str] = set()
        for binding in self.packet_manifest_bindings:
            if type(binding) is not tuple or len(binding) != 2:
                raise TypeError("packet manifest bindings must be exact pairs")
            packet_id, manifest = binding
            _require_opaque_id(packet_id, "packet_id")
            _require_hash(manifest, "complete_bundle_manifest_sha256")
            encoded = packet_id.encode("ascii")
            if previous_packet is not None and encoded <= previous_packet:
                raise ValueError("packet manifest bindings are not byte sorted and unique")
            previous_packet = encoded
            if packet_id in bindings or manifest in manifests:
                raise ValueError("packet manifest bindings are not one-to-one")
            bindings[packet_id] = manifest
            manifests.add(manifest)
        packet_entries = {opaque_id for kind, _, opaque_id in self.entries if kind == "packet"}
        if set(bindings) != packet_entries:
            raise ValueError("packet manifest bindings do not close registry packets")

    def resolve(self, kind: str, opaque_id: str) -> int:
        if type(kind) is not str or kind not in _OPAQUE_KINDS:
            raise ValueError("registry resolution has invalid kind")
        _require_opaque_id(opaque_id, "opaque_id")
        for entry_kind, ordinal, entry_id in self.entries:
            if entry_kind == kind and entry_id == opaque_id:
                return ordinal
        raise ValueError("opaque ID is stale, foreign, or wrong-kind")

    def packet_manifest(self, packet_id: str) -> str:
        self.resolve("packet", packet_id)
        for bound_packet, manifest in self.packet_manifest_bindings:
            if bound_packet == packet_id:
                return manifest
        raise ValueError("packet has no manifest binding")


def _require_repeat_seed_cells(value: object, name: str) -> tuple[tuple[int, int], ...]:
    if type(value) is not tuple or not value:
        raise TypeError(f"{name} must be a nonempty exact tuple")
    previous: tuple[int, int] | None = None
    for cell in value:
        if type(cell) is not tuple or len(cell) != 2:
            raise TypeError(f"{name} entries must be exact pairs")
        repeat_index, seed = cell
        _require_int(repeat_index, "repeat_index")
        _require_int(seed, "seed")
        if previous is not None and cell <= previous:
            raise ValueError(f"{name} must be lexicographically sorted and unique")
        previous = cell
    return value


def _target_action_roster_digest(
    site_ref: str,
    case_ref: str,
    prefix_ref: str,
    packet_ids: tuple[str, ...],
    repeat_seed_cells: tuple[tuple[int, int], ...],
) -> str:
    return _sha_value(
        [
            site_ref,
            case_ref,
            prefix_ref,
            list(packet_ids),
            [list(cell) for cell in repeat_seed_cells],
        ]
    )


@dataclass(frozen=True, slots=True)
class AuxiliaryControlPlanV2(_Record):
    control_ref: str
    control_kind: str
    focal_pair_key_sha256: str
    site_ref: str
    case_ref: str
    prefix_ref: str
    target_action_roster_sha256: str
    packet_ids: tuple[str, ...]
    repeat_seed_cells: tuple[tuple[int, int], ...]
    assignment_record_sha256s: tuple[str, ...]
    assignment_reference_multiplicities: tuple[int, ...]
    selection_probability_spec_sha256: str
    support_cell_sha256: str
    synthetic_only: bool
    plan_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "AuxiliaryControlPlanV2.v2"
    HASH_FIELD = "plan_sha256"
    TUPLE_FIELDS = frozenset(
        {"packet_ids", "repeat_seed_cells", "assignment_record_sha256s", "assignment_reference_multiplicities"}
    )

    @classmethod
    def from_dict(cls, value: object) -> Any:
        if type(value) is not dict:
            raise TypeError("auxiliary plan must be an exact dict")
        converted = dict(value)
        cells = converted.get("repeat_seed_cells")
        if type(cells) is not list or any(type(cell) is not list or len(cell) != 2 for cell in cells):
            raise TypeError("repeat_seed_cells must serialize as exact pairs")
        converted["repeat_seed_cells"] = [tuple(cell) for cell in cells]
        return _Record.from_dict.__func__(cls, converted)

    def _validate(self) -> None:
        _require_opaque_id(self.control_ref, "control_ref")
        if self.control_kind not in _AUXILIARY_CONTROL_KINDS:
            raise ValueError("invalid auxiliary control_kind")
        for name in ("focal_pair_key_sha256", "target_action_roster_sha256", "selection_probability_spec_sha256", "support_cell_sha256"):
            _require_hash(getattr(self, name), name)
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        if type(self.packet_ids) is not tuple or not self.packet_ids:
            raise TypeError("packet_ids must be a nonempty exact tuple")
        for packet_id in self.packet_ids:
            _require_opaque_id(packet_id, "packet_ids")
        if tuple(sorted(self.packet_ids, key=lambda item: item.encode("ascii"))) != self.packet_ids or len(set(self.packet_ids)) != len(self.packet_ids):
            raise ValueError("packet_ids must be byte sorted and unique")
        _require_repeat_seed_cells(self.repeat_seed_cells, "repeat_seed_cells")
        _require_hash_tuple(self.assignment_record_sha256s, "assignment_record_sha256s", nonempty=True)
        if type(self.assignment_reference_multiplicities) is not tuple or len(self.assignment_reference_multiplicities) != len(self.assignment_record_sha256s):
            raise TypeError("assignment_reference_multiplicities must align with assignments")
        for multiplicity in self.assignment_reference_multiplicities:
            _require_int(multiplicity, "assignment reference multiplicity", minimum=1)


@dataclass(frozen=True, slots=True)
class AuxiliaryControlConformanceV2(_Record):
    control_plan_sha256: str
    assignment_record_sha256s: tuple[str, ...]
    execution_record_sha256s: tuple[str, ...]
    terminal_record_sha256s: tuple[str, ...]
    compliance_status: str
    synthetic_only: bool
    conformance_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "AuxiliaryControlConformanceV2.v2"
    HASH_FIELD = "conformance_sha256"
    TUPLE_FIELDS = frozenset({"assignment_record_sha256s", "execution_record_sha256s", "terminal_record_sha256s"})

    def _validate(self) -> None:
        _require_hash(self.control_plan_sha256, "control_plan_sha256")
        for name in ("assignment_record_sha256s", "execution_record_sha256s", "terminal_record_sha256s"):
            _require_hash_tuple(getattr(self, name), name, nonempty=True)
        if not (len(self.assignment_record_sha256s) == len(self.execution_record_sha256s) == len(self.terminal_record_sha256s)):
            raise ValueError("auxiliary conformance joins must align")
        if self.compliance_status not in _COMPLIANCE_STATUSES:
            raise ValueError("invalid auxiliary compliance_status")


@dataclass(frozen=True, slots=True)
class SyntheticE1ActionRosterV2(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    packet_ids: tuple[str, ...]
    repeat_seed_cells: tuple[tuple[int, int], ...]
    common_synthesis_spec_sha256: str
    opaque_identity_registry_sha256: str
    synthetic_only: bool
    roster_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticE1ActionRosterV2.v2"
    HASH_FIELD = "roster_sha256"
    TUPLE_FIELDS = frozenset({"packet_ids", "repeat_seed_cells"})

    @classmethod
    def from_dict(cls, value: object) -> Any:
        if type(value) is not dict:
            raise TypeError("action roster must be an exact dict")
        converted = dict(value)
        cells = converted.get("repeat_seed_cells")
        if type(cells) is not list or any(type(cell) is not list or len(cell) != 2 for cell in cells):
            raise TypeError("repeat_seed_cells must serialize as exact pairs")
        converted["repeat_seed_cells"] = [tuple(cell) for cell in cells]
        return _Record.from_dict.__func__(cls, converted)

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        if type(self.packet_ids) is not tuple or not self.packet_ids:
            raise TypeError("packet_ids must be a nonempty exact tuple")
        for packet_id in self.packet_ids:
            _require_opaque_id(packet_id, "packet_ids")
        if tuple(sorted(self.packet_ids, key=lambda item: item.encode("ascii"))) != self.packet_ids or len(set(self.packet_ids)) != len(self.packet_ids):
            raise ValueError("packet_ids must be byte sorted and unique")
        _require_repeat_seed_cells(self.repeat_seed_cells, "repeat_seed_cells")
        _require_hash(self.common_synthesis_spec_sha256, "common_synthesis_spec_sha256")
        _require_hash(self.opaque_identity_registry_sha256, "opaque_identity_registry_sha256")


@dataclass(frozen=True, slots=True)
class SyntheticSoloExecutionConformanceV2(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    repeat_index: int
    seed: int
    common_synthesis_spec_sha256: str
    pre_call_execution_isolation_receipt_sha256: str
    post_run_execution_usage_conformance_receipt_sha256: str
    usage_ledger_sha256: str
    compliance_status: str
    synthetic_only: bool
    record_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticSoloExecutionConformanceV2.v2"
    HASH_FIELD = "record_sha256"

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        _require_int(self.repeat_index, "repeat_index")
        _require_int(self.seed, "seed")
        for name in ("common_synthesis_spec_sha256", "pre_call_execution_isolation_receipt_sha256", "post_run_execution_usage_conformance_receipt_sha256", "usage_ledger_sha256"):
            _require_hash(getattr(self, name), name)
        if self.compliance_status not in _COMPLIANCE_STATUSES:
            raise ValueError("invalid solo compliance_status")


@dataclass(frozen=True, slots=True)
class SyntheticTerminalBranch(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    treatment_kind: str
    opaque_slot_id: str | None
    actual_packet_id: str | None
    repeat_index: int
    seed: int
    blind_terminal_quality: float
    complete_processed_tokens: int
    latency_seconds: float
    list_price_cost: float
    execution_conformance_sha256: str
    direct_terminal_sha256: str
    synthetic_only: bool
    record_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticTerminalBranch.v2"
    HASH_FIELD = "record_sha256"

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        if self.treatment_kind not in _TREATMENTS:
            raise ValueError("invalid treatment_kind")
        packet = self.treatment_kind == "capability_packet"
        if packet:
            _require_identifier(self.opaque_slot_id, "opaque_slot_id")
            _require_identifier(self.actual_packet_id, "actual_packet_id")
        elif self.opaque_slot_id is not None or self.actual_packet_id is not None:
            raise ValueError("non-packet treatment must have null packet identity")
        _require_int(self.repeat_index, "repeat_index")
        _require_int(self.seed, "seed")
        _require_float(self.blind_terminal_quality, "blind_terminal_quality", minimum=0.0, maximum=1.0)
        _require_int(self.complete_processed_tokens, "complete_processed_tokens")
        _require_float(self.latency_seconds, "latency_seconds", minimum=0.0)
        _require_float(self.list_price_cost, "list_price_cost", minimum=0.0)
        _require_hash(self.execution_conformance_sha256, "execution_conformance_sha256")
        _require_hash(self.direct_terminal_sha256, "direct_terminal_sha256")


@dataclass(frozen=True, slots=True)
class SyntheticAssignmentCrossoverRecord(_Record):
    assignment_ref: str
    site_ref: str
    case_ref: str
    prefix_ref: str
    repeat_index: int
    seed: int
    assigned_opaque_slot_id: str
    assigned_actual_packet_id: str
    assigned_complete_bundle_manifest_sha256: str
    assignment_probability: float
    assignment_probability_spec_sha256: str
    randomization_nonce_sha256: str
    cyclic_crossover_plan_sha256: str
    complete_packet_roster_sha256: str
    immutable_target_roster_sha256: str
    synthetic_only: bool
    record_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticAssignmentCrossoverRecord.v2"
    HASH_FIELD = "record_sha256"

    def _validate(self) -> None:
        for name in (
            "assignment_ref", "site_ref", "case_ref", "prefix_ref",
            "assigned_opaque_slot_id", "assigned_actual_packet_id",
        ):
            _require_identifier(getattr(self, name), name)
        _require_int(self.repeat_index, "repeat_index")
        _require_int(self.seed, "seed")
        _require_float(self.assignment_probability, "assignment_probability", positive=True, maximum=1.0)
        for name in (
            "assigned_complete_bundle_manifest_sha256",
            "assignment_probability_spec_sha256", "randomization_nonce_sha256",
            "cyclic_crossover_plan_sha256", "complete_packet_roster_sha256",
            "immutable_target_roster_sha256",
        ):
            _require_hash(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class SyntheticPairAssignmentClosure(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    high_assignment_record_sha256s: tuple[str, ...]
    low_assignment_record_sha256s: tuple[str, ...]
    cyclic_crossover_plan_sha256: str
    complete_packet_roster_sha256: str
    immutable_target_roster_sha256: str
    assignment_probability_spec_sha256: str
    synthetic_only: bool
    closure_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticPairAssignmentClosure.v2"
    HASH_FIELD = "closure_sha256"
    TUPLE_FIELDS = frozenset({"high_assignment_record_sha256s", "low_assignment_record_sha256s"})

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        _require_hash_tuple(self.high_assignment_record_sha256s, "high assignments", nonempty=True)
        _require_hash_tuple(self.low_assignment_record_sha256s, "low assignments", nonempty=True)
        for name in (
            "cyclic_crossover_plan_sha256", "complete_packet_roster_sha256",
            "immutable_target_roster_sha256", "assignment_probability_spec_sha256",
        ):
            _require_hash(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class FrozenResidualCapabilityBinding(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    opaque_packet_id: str
    complete_bundle_manifest_sha256: str
    obligation_ontology_sha256: str
    residual_obligation_snapshot_sha256: str
    residual_source_receipt_sha256: str
    capability_matrix_sha256: str
    capability_matrix_source_receipt_sha256: str
    alignment_rule_sha256: str
    alignment_measure_kind: str
    capability_dimension_sha256: str
    obligation_relation_sha256: str
    alignment_role: str
    effect_modifier_stratum: str
    support_cell_sha256: str
    pair_set_sha256: str
    synthetic_only: bool
    binding_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "FrozenResidualCapabilityBinding.v2"
    HASH_FIELD = "binding_sha256"

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref", "opaque_packet_id"):
            _require_identifier(getattr(self, name), name)
        for name in (
            "complete_bundle_manifest_sha256", "obligation_ontology_sha256",
            "residual_obligation_snapshot_sha256", "residual_source_receipt_sha256",
            "capability_matrix_sha256", "capability_matrix_source_receipt_sha256",
            "alignment_rule_sha256", "capability_dimension_sha256",
            "obligation_relation_sha256", "support_cell_sha256", "pair_set_sha256",
        ):
            _require_hash(getattr(self, name), name)
        if self.alignment_measure_kind not in _MEASURE_KINDS:
            raise ValueError("invalid alignment_measure_kind")
        if self.alignment_role not in _ALIGNMENT_ROLES:
            raise ValueError("invalid alignment_role")
        if self.effect_modifier_stratum not in _EFFECT_STRATA:
            raise ValueError("invalid effect_modifier_stratum")


@dataclass(frozen=True, slots=True)
class SyntheticSupportBalanceRecord(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    support_cell_sha256: str
    target_census: int
    cost_balance_sha256: str
    complete_token_balance_sha256: str
    information_exposure_balance_sha256: str
    prompt_profile_length_balance_sha256: str
    tool_access_count_balance_sha256: str
    synthesis_path_balance_sha256: str
    admissibility_balance_sha256: str
    global_bundle_strength_control_sha256: str | None
    uniform_random_control_sha256: str | None
    residual_absent_control_selection_spec_sha256: str
    support_status: str
    synthetic_only: bool
    record_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticSupportBalanceRecord.v2"
    HASH_FIELD = "record_sha256"

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        _require_int(self.target_census, "target_census")
        for name in (
            "support_cell_sha256", "cost_balance_sha256", "complete_token_balance_sha256",
            "information_exposure_balance_sha256", "prompt_profile_length_balance_sha256",
            "tool_access_count_balance_sha256", "synthesis_path_balance_sha256",
            "admissibility_balance_sha256", "residual_absent_control_selection_spec_sha256",
        ):
            _require_hash(getattr(self, name), name)
        _optional_hash(self.global_bundle_strength_control_sha256, "global_bundle_strength_control_sha256")
        _optional_hash(self.uniform_random_control_sha256, "uniform_random_control_sha256")
        if self.support_status not in _SUPPORT_STATUSES:
            raise ValueError("invalid support_status")


@dataclass(frozen=True, slots=True)
class SyntheticExecutionConformanceRecord(_Record):
    assignment_ref: str
    site_ref: str
    case_ref: str
    prefix_ref: str
    repeat_index: int
    seed: int
    assigned_opaque_slot_id: str
    assigned_actual_packet_id: str
    actual_opaque_slot_id: str
    actual_packet_id: str
    actual_complete_bundle_manifest_sha256: str
    pre_call_execution_isolation_receipt_sha256: str
    post_run_execution_usage_conformance_receipt_sha256: str
    usage_ledger_sha256: str
    compliance_status: str
    synthetic_only: bool
    record_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticExecutionConformanceRecord.v2"
    HASH_FIELD = "record_sha256"

    def _validate(self) -> None:
        for name in (
            "assignment_ref", "site_ref", "case_ref", "prefix_ref",
            "assigned_opaque_slot_id", "assigned_actual_packet_id",
            "actual_opaque_slot_id", "actual_packet_id",
        ):
            _require_identifier(getattr(self, name), name)
        _require_int(self.repeat_index, "repeat_index")
        _require_int(self.seed, "seed")
        for name in (
            "actual_complete_bundle_manifest_sha256",
            "pre_call_execution_isolation_receipt_sha256",
            "post_run_execution_usage_conformance_receipt_sha256",
            "usage_ledger_sha256",
        ):
            _require_hash(getattr(self, name), name)
        if self.compliance_status not in _COMPLIANCE_STATUSES:
            raise ValueError("invalid compliance_status")


@dataclass(frozen=True, slots=True)
class FrozenE2Pair(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    high_packet_id: str
    high_complete_bundle_manifest_sha256: str
    high_residual_capability_binding_sha256: str
    low_packet_id: str
    low_complete_bundle_manifest_sha256: str
    low_residual_capability_binding_sha256: str
    pair_assignment_closure_sha256: str
    balance_support_record_sha256: str
    evaluator_reference_sha256: str
    pair_set_sha256: str
    synthetic_only: bool
    pair_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "FrozenE2Pair.v2"
    HASH_FIELD = "pair_sha256"

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref", "high_packet_id", "low_packet_id"):
            _require_identifier(getattr(self, name), name)
        if self.high_packet_id == self.low_packet_id:
            raise ValueError("focal packet identities must differ")
        for name in (
            "high_complete_bundle_manifest_sha256", "high_residual_capability_binding_sha256",
            "low_complete_bundle_manifest_sha256", "low_residual_capability_binding_sha256",
            "pair_assignment_closure_sha256", "balance_support_record_sha256",
            "evaluator_reference_sha256", "pair_set_sha256",
        ):
            _require_hash(getattr(self, name), name)


def _focal_key(pair: FrozenE2Pair) -> str:
    return _sha_value(
        [
            pair.site_ref, pair.case_ref, pair.prefix_ref,
            pair.high_packet_id, pair.high_complete_bundle_manifest_sha256,
            pair.low_packet_id, pair.low_complete_bundle_manifest_sha256,
            pair.evaluator_reference_sha256, pair.pair_set_sha256,
        ]
    )


@dataclass(frozen=True, slots=True)
class SyntheticResidualAbsentControlPair(_Record):
    control_ref: str
    focal_pair_key_sha256: str
    site_ref: str
    case_ref: str
    prefix_ref: str
    high_packet_id: str
    high_complete_bundle_manifest_sha256: str
    high_residual_capability_binding_sha256: str
    low_packet_id: str
    low_complete_bundle_manifest_sha256: str
    low_residual_capability_binding_sha256: str
    pair_assignment_closure_sha256: str
    balance_support_record_sha256: str
    evaluator_reference_sha256: str
    pair_set_sha256: str
    matching_weight: float
    residual_absent_control_selection_spec_sha256: str
    synthetic_only: bool
    control_pair_key_sha256: str
    control_pair_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticResidualAbsentControlPair.v2"
    HASH_FIELD = "control_pair_sha256"

    def _validate(self) -> None:
        for name in (
            "control_ref", "site_ref", "case_ref", "prefix_ref",
            "high_packet_id", "low_packet_id",
        ):
            _require_identifier(getattr(self, name), name)
        for name in (
            "focal_pair_key_sha256", "high_complete_bundle_manifest_sha256",
            "high_residual_capability_binding_sha256", "low_complete_bundle_manifest_sha256",
            "low_residual_capability_binding_sha256", "pair_assignment_closure_sha256",
            "balance_support_record_sha256", "evaluator_reference_sha256",
            "pair_set_sha256", "residual_absent_control_selection_spec_sha256",
            "control_pair_key_sha256",
        ):
            _require_hash(getattr(self, name), name)
        _require_float(self.matching_weight, "matching_weight", positive=True)
        key_fields = tuple(field.name for field in fields(self))
        through_weight = key_fields[: key_fields.index("matching_weight") + 1]
        expected = _sha_value({name: _plain(getattr(self, name)) for name in through_weight})
        if self.control_pair_key_sha256 != expected:
            raise ValueError("control_pair_key_sha256 mismatch")


@dataclass(frozen=True, slots=True)
class SyntheticResidualAbsentControlRoster(_Record):
    focal_pair_key_sha256: str
    support_cell_sha256: str
    pair_set_sha256: str
    control_pair_key_sha256s: tuple[str, ...]
    matching_weights: tuple[float, ...]
    selection_spec_sha256: str
    synthetic_only: bool
    roster_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticResidualAbsentControlRoster.v2"
    HASH_FIELD = "roster_sha256"
    TUPLE_FIELDS = frozenset({"control_pair_key_sha256s", "matching_weights"})

    def _validate(self) -> None:
        for name in ("focal_pair_key_sha256", "support_cell_sha256", "pair_set_sha256", "selection_spec_sha256"):
            _require_hash(getattr(self, name), name)
        _require_hash_tuple(self.control_pair_key_sha256s, "control_pair_key_sha256s", nonempty=True)
        if type(self.matching_weights) is not tuple or len(self.matching_weights) != len(self.control_pair_key_sha256s):
            raise TypeError("matching_weights must align with control keys")
        for weight in self.matching_weights:
            _require_float(weight, "matching_weight", positive=True)
        if math.fsum(self.matching_weights) != 1.0:
            raise ValueError("matching_weights must sum exactly to 1.0")


@dataclass(frozen=True, slots=True)
class E2MechanismContract(_Record):
    opaque_identity_registry: SyntheticOpaqueIdentityRegistryV2
    e1_action_rosters: tuple[SyntheticE1ActionRosterV2, ...]
    solo_execution_records: tuple[SyntheticSoloExecutionConformanceV2, ...]
    auxiliary_control_plans: tuple[AuxiliaryControlPlanV2, ...]
    auxiliary_control_conformances: tuple[AuxiliaryControlConformanceV2, ...]
    bindings: tuple[FrozenResidualCapabilityBinding, ...]
    assignments: tuple[SyntheticAssignmentCrossoverRecord, ...]
    pair_assignment_closures: tuple[SyntheticPairAssignmentClosure, ...]
    support_balance_records: tuple[SyntheticSupportBalanceRecord, ...]
    execution_records: tuple[SyntheticExecutionConformanceRecord, ...]
    terminal_branches: tuple[SyntheticTerminalBranch, ...]
    pairs: tuple[FrozenE2Pair, ...]
    residual_absent_control_pairs: tuple[SyntheticResidualAbsentControlPair, ...]
    residual_absent_control_rosters: tuple[SyntheticResidualAbsentControlRoster, ...]
    blind_outcome_schema_sha256: str
    common_synthesis_spec_sha256: str
    analysis_code_sha256: str
    synthetic_only: bool
    contract_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "E2MechanismContract.v2"
    HASH_FIELD = "contract_sha256"

    def _validate(self) -> None:
        if type(self.opaque_identity_registry) is not SyntheticOpaqueIdentityRegistryV2:
            raise TypeError("opaque_identity_registry has foreign type")
        specifications = (
            (self.e1_action_rosters, SyntheticE1ActionRosterV2, "roster_sha256", "e1_action_rosters"),
            (self.solo_execution_records, SyntheticSoloExecutionConformanceV2, "record_sha256", "solo_execution_records"),
            (self.auxiliary_control_plans, AuxiliaryControlPlanV2, "plan_sha256", "auxiliary_control_plans"),
            (self.auxiliary_control_conformances, AuxiliaryControlConformanceV2, "conformance_sha256", "auxiliary_control_conformances"),
            (self.bindings, FrozenResidualCapabilityBinding, "binding_sha256", "bindings"),
            (self.assignments, SyntheticAssignmentCrossoverRecord, "record_sha256", "assignments"),
            (self.pair_assignment_closures, SyntheticPairAssignmentClosure, "closure_sha256", "pair_assignment_closures"),
            (self.support_balance_records, SyntheticSupportBalanceRecord, "record_sha256", "support_balance_records"),
            (self.execution_records, SyntheticExecutionConformanceRecord, "record_sha256", "execution_records"),
            (self.terminal_branches, SyntheticTerminalBranch, "record_sha256", "terminal_branches"),
            (self.pairs, FrozenE2Pair, "pair_sha256", "pairs"),
            (self.residual_absent_control_pairs, SyntheticResidualAbsentControlPair, "control_pair_sha256", "residual_absent_control_pairs"),
            (self.residual_absent_control_rosters, SyntheticResidualAbsentControlRoster, "roster_sha256", "residual_absent_control_rosters"),
        )
        for value, cls, hash_name, name in specifications:
            _validate_collection(value, cls, hash_name, name)
        for name in ("blind_outcome_schema_sha256", "common_synthesis_spec_sha256", "analysis_code_sha256"):
            _require_hash(getattr(self, name), name)
        registry = self.opaque_identity_registry
        roster_targets: set[tuple[str, str, str]] = set()
        for row in self.e1_action_rosters:
            target = (row.site_ref, row.case_ref, row.prefix_ref)
            if target in roster_targets:
                raise ValueError("E1 action roster target does not resolve once")
            roster_targets.add(target)
            if row.common_synthesis_spec_sha256 != self.common_synthesis_spec_sha256:
                raise ValueError("E1 action roster synthesis specification mismatch")
            if row.opaque_identity_registry_sha256 != registry.registry_sha256:
                raise ValueError("action roster registry mismatch")
            for packet_id in row.packet_ids:
                registry.resolve("packet", packet_id)
        for row in self.auxiliary_control_plans:
            registry.resolve("control", row.control_ref)
            for packet_id in row.packet_ids:
                registry.resolve("packet", packet_id)
        for row in self.bindings:
            if registry.packet_manifest(row.opaque_packet_id) != row.complete_bundle_manifest_sha256:
                raise ValueError("binding packet manifest disagrees with registry")
        for row in self.assignments:
            registry.resolve("assignment", row.assignment_ref)
            registry.resolve("slot", row.assigned_opaque_slot_id)
            if registry.packet_manifest(row.assigned_actual_packet_id) != row.assigned_complete_bundle_manifest_sha256:
                raise ValueError("assignment packet manifest disagrees with registry")
        for row in self.execution_records:
            registry.resolve("assignment", row.assignment_ref)
            registry.resolve("slot", row.assigned_opaque_slot_id)
            registry.resolve("slot", row.actual_opaque_slot_id)
            registry.resolve("packet", row.assigned_actual_packet_id)
            registry.resolve("packet", row.actual_packet_id)
            if registry.packet_manifest(row.actual_packet_id) != row.actual_complete_bundle_manifest_sha256:
                raise ValueError("execution packet manifest disagrees with registry")
        for row in self.terminal_branches:
            if row.treatment_kind == "capability_packet":
                registry.resolve("slot", row.opaque_slot_id)
                registry.resolve("packet", row.actual_packet_id)
        for row in self.pairs:
            if (
                registry.packet_manifest(row.high_packet_id)
                != row.high_complete_bundle_manifest_sha256
                or registry.packet_manifest(row.low_packet_id)
                != row.low_complete_bundle_manifest_sha256
            ):
                raise ValueError("focal packet manifest disagrees with registry")
        for row in self.residual_absent_control_pairs:
            registry.resolve("control", row.control_ref)
            if (
                registry.packet_manifest(row.high_packet_id)
                != row.high_complete_bundle_manifest_sha256
                or registry.packet_manifest(row.low_packet_id)
                != row.low_complete_bundle_manifest_sha256
            ):
                raise ValueError("control packet manifest disagrees with registry")


@dataclass(frozen=True, slots=True)
class E2SyntheticSummary(_Record):
    status: str
    site_clustered_primary_contrast: float | None
    secondary_cost_adjusted_utility: float | None
    secondary_continuous_alignment_cost_interaction: float | None
    site_count: int
    case_count: int
    row_count: int
    support_census_sha256: str
    synthetic_only: bool
    summary_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "E2SyntheticSummary.v2"
    HASH_FIELD = "summary_sha256"

    def _validate(self) -> None:
        if self.status not in {"synthetic_complete", "non_estimable_support"}:
            raise ValueError("invalid E2 summary status")
        values = (
            self.site_clustered_primary_contrast,
            self.secondary_cost_adjusted_utility,
            self.secondary_continuous_alignment_cost_interaction,
        )
        if self.status == "non_estimable_support":
            if values != (None, None, None):
                raise ValueError("non-estimable E2 numerics must be None")
        else:
            _require_float(values[0], "primary contrast")
            if values[1:] != (None, None):
                raise ValueError("Phase-A secondary E2 numerics must be None")
        _require_int(self.site_count, "site_count")
        _require_int(self.case_count, "case_count")
        _require_int(self.row_count, "row_count")
        _require_hash(self.support_census_sha256, "support_census_sha256")


@dataclass(frozen=True, slots=True)
class SyntheticE3TargetActionAuthorityV2(_Record):
    site_ref: str
    case_ref: str
    prefix_ref: str
    packet_slot_bindings: tuple[tuple[str, str, str], ...]
    opaque_identity_registry_sha256: str
    synthetic_only: bool
    authority_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticE3TargetActionAuthorityV2.v2"
    HASH_FIELD = "authority_sha256"
    TUPLE_FIELDS = frozenset({"packet_slot_bindings"})

    @classmethod
    def from_dict(cls, value: object) -> Any:
        if type(value) is not dict:
            raise TypeError("E3 target action authority must be an exact dict")
        converted = dict(value)
        rows = converted.get("packet_slot_bindings")
        if type(rows) is not list or any(type(row) is not list or len(row) != 3 for row in rows):
            raise TypeError("packet_slot_bindings must serialize as exact triples")
        converted["packet_slot_bindings"] = [tuple(row) for row in rows]
        return _Record.from_dict.__func__(cls, converted)

    def _validate(self) -> None:
        for name in ("site_ref", "case_ref", "prefix_ref"):
            _require_identifier(getattr(self, name), name)
        _require_hash(self.opaque_identity_registry_sha256, "opaque_identity_registry_sha256")
        if type(self.packet_slot_bindings) is not tuple or not self.packet_slot_bindings:
            raise TypeError("packet_slot_bindings must be a nonempty exact tuple")
        previous: tuple[bytes, bytes] | None = None
        slots: set[str] = set()
        packets: set[str] = set()
        for row in self.packet_slot_bindings:
            if type(row) is not tuple or len(row) != 3:
                raise TypeError("packet_slot_bindings rows must be exact triples")
            slot_id, packet_id, manifest = row
            _require_opaque_id(slot_id, "opaque_slot_id")
            _require_opaque_id(packet_id, "opaque_packet_id")
            _require_hash(manifest, "complete_bundle_manifest_sha256")
            order = (slot_id.encode("ascii"), packet_id.encode("ascii"))
            if previous is not None and order <= previous:
                raise ValueError("packet_slot_bindings must be byte sorted and unique")
            if slot_id in slots or packet_id in packets:
                raise ValueError("packet_slot_bindings must be one-to-one")
            previous = order
            slots.add(slot_id)
            packets.add(packet_id)


@dataclass(frozen=True, slots=True)
class SyntheticParityReplayBundle(_Record):
    source_parent_bytes: bytes
    oacs_input_bytes: bytes
    raw_router_input_bytes: bytes
    oacs_projection_spec_bytes: bytes
    raw_router_projection_spec_bytes: bytes
    information_equivalence_map_bytes: bytes
    target_action_roster_bytes: bytes
    shared_training_opportunity_bytes: bytes
    oacs_pre_outcome_decision_bytes: bytes
    raw_router_pre_outcome_decision_bytes: bytes
    synthetic_only: bool
    bundle_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticParityReplayBundle.v2"
    HASH_FIELD = "bundle_sha256"
    BYTES_FIELDS = frozenset(
        {
            "source_parent_bytes", "oacs_input_bytes", "raw_router_input_bytes",
            "oacs_projection_spec_bytes", "raw_router_projection_spec_bytes",
            "information_equivalence_map_bytes", "target_action_roster_bytes",
            "shared_training_opportunity_bytes", "oacs_pre_outcome_decision_bytes",
            "raw_router_pre_outcome_decision_bytes",
        }
    )

    def _validate(self) -> None:
        _validate_parity_bundle(self)


@dataclass(frozen=True, slots=True)
class PairedInformationParityReceipt(_Record):
    schema_version: str
    source_parent_receipt_sha256: str
    oacs_input_bytes_sha256: str
    raw_router_input_bytes_sha256: str
    oacs_projection_spec_sha256: str
    raw_router_projection_spec_sha256: str
    information_equivalence_map_sha256: str
    target_action_roster_sha256: str
    costs_sha256: str
    admissibility_sha256: str
    examples_sha256: str
    split_fold_sha256: str
    learner_class_capacity_sha256: str
    tuning_optimization_opportunity_sha256: str
    action_space_tie_rule_sha256: str
    oacs_pre_outcome_decisions_sha256: str
    raw_router_pre_outcome_decisions_sha256: str
    pair_sha256: str
    synthetic_only: bool
    receipt_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "PairedInformationParityReceipt.v2"
    HASH_FIELD = "receipt_sha256"

    def _validate(self) -> None:
        if self.schema_version != self.SCHEMA:
            raise ValueError("parity receipt schema mismatch")
        for field in fields(self):
            if field.name.endswith("_sha256"):
                _require_hash(getattr(self, field.name), field.name)


@dataclass(frozen=True, slots=True)
class MandatoryBaselineRosterEntry(_Record):
    baseline_id: str
    official_source_spec_sha256: str | None
    version_sha256: str
    synthetic_only: bool
    entry_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "MandatoryBaselineRosterEntry.v2"
    HASH_FIELD = "entry_sha256"

    def _validate(self) -> None:
        if self.baseline_id not in _BASELINE_IDS:
            raise ValueError("baseline_id is not mandatory")
        _require_hash(self.version_sha256, "version_sha256")
        if self.baseline_id in _INTERNAL_BASELINES:
            if self.official_source_spec_sha256 is not None:
                raise ValueError("internal control must not claim official source")
        else:
            _require_hash(self.official_source_spec_sha256, "official_source_spec_sha256")


@dataclass(frozen=True, slots=True)
class MandatoryBaselineRoster(_Record):
    entries: tuple[MandatoryBaselineRosterEntry, ...]
    synthetic_only: bool
    roster_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "MandatoryBaselineRoster.v2"
    HASH_FIELD = "roster_sha256"

    def _validate(self) -> None:
        if type(self.entries) is not tuple or any(type(row) is not MandatoryBaselineRosterEntry for row in self.entries):
            raise TypeError("entries must be exact baseline records")
        if tuple(row.baseline_id for row in self.entries) != _BASELINE_IDS:
            raise ValueError("mandatory baseline roster is incomplete or noncanonical")
        entries = {row.baseline_id: row for row in self.entries}
        allocation = entries["self_resource_allocation"]
        scaling = entries["matched_compute_self_agent_scaling"]
        if (
            allocation.official_source_spec_sha256 == scaling.official_source_spec_sha256
            or allocation.version_sha256 == scaling.version_sha256
        ):
            raise ValueError("resource allocation and self-agent scaling commitments must be distinct")


@dataclass(frozen=True, slots=True)
class BaselinePreOutcomeReadinessAuthority(_Record):
    baseline_id: str
    version_sha256: str
    status: str
    reason_code: str
    official_source_spec_sha256: str | None
    executed_method_id: str | None
    adapter_code_sha256: str | None
    dependency_environment_lock_sha256: str | None
    parity_projection_sha256: str | None
    synthetic_faithfulness_test_receipt_sha256: str | None
    reviewer_decision_sha256: str
    pre_outcome_amendment_sha256: str | None
    synthetic_only: bool
    status_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "BaselinePreOutcomeReadinessAuthority.v2"
    HASH_FIELD = "status_sha256"

    def _validate(self) -> None:
        if self.baseline_id not in _BASELINE_IDS:
            raise ValueError("readiness baseline is not mandatory")
        if self.status not in _READINESS_STATUSES:
            raise ValueError("invalid readiness status")
        _require_hash(self.version_sha256, "version_sha256")
        if self.reason_code not in _READINESS_REASONS:
            raise ValueError("invalid readiness reason")
        if self.executed_method_id is not None:
            _require_identifier(self.executed_method_id, "executed_method_id")
        for name in (
            "official_source_spec_sha256", "adapter_code_sha256",
            "dependency_environment_lock_sha256", "parity_projection_sha256",
            "synthetic_faithfulness_test_receipt_sha256", "pre_outcome_amendment_sha256",
        ):
            _optional_hash(getattr(self, name), name)
        _require_hash(self.reviewer_decision_sha256, "reviewer_decision_sha256")
        if self.status == "supported":
            if self.reason_code != "ready_verified" or self.pre_outcome_amendment_sha256 is not None:
                raise ValueError("supported readiness has wrong reason/amendment")
            if self.executed_method_id != self.baseline_id:
                raise ValueError("supported readiness must execute under baseline_id")
            for name in (
                "adapter_code_sha256", "dependency_environment_lock_sha256",
                "parity_projection_sha256", "synthetic_faithfulness_test_receipt_sha256",
            ):
                _require_hash(getattr(self, name), name)
        elif self.status.startswith("unsupported_"):
            allowed = (
                {"official_interface_absent", "official_interface_incompatible", "faithfulness_failed"}
                if self.status == "unsupported_official_interface"
                else {"dependency_unavailable", "license_or_access_blocked"}
            )
            if self.reason_code not in allowed:
                raise ValueError("unsupported readiness has wrong-status reason")
            if self.executed_method_id is not None:
                raise ValueError("unsupported readiness cannot have executed identity")
            if any(
                getattr(self, name) is not None
                for name in (
                    "adapter_code_sha256", "parity_projection_sha256",
                    "synthetic_faithfulness_test_receipt_sha256",
                    "pre_outcome_amendment_sha256",
                )
            ):
                raise ValueError("unsupported readiness has forbidden artifacts")
            _require_hash(self.dependency_environment_lock_sha256, "dependency_environment_lock_sha256")
        else:
            if self.reason_code != "domain_inapplicable":
                raise ValueError("inapplicable readiness needs domain_inapplicable")
            for name in (
                "adapter_code_sha256", "dependency_environment_lock_sha256",
                "parity_projection_sha256", "synthetic_faithfulness_test_receipt_sha256",
                "pre_outcome_amendment_sha256",
            ):
                _require_hash(getattr(self, name), name)
            expected = "adaptation:" + _sha_value(
                [self.baseline_id, self.pre_outcome_amendment_sha256]
            )
            if self.executed_method_id != expected:
                raise ValueError("adapted readiness has wrong executed identity")


@dataclass(frozen=True, slots=True)
class BaselineDecisionRunConformanceReceipt(_Record):
    baseline_id: str
    executed_method_id: str
    readiness_status_sha256: str
    input_action_roster_sha256: str
    baseline_input_bytes: bytes
    baseline_input_bytes_sha256: str
    baseline_projection_spec_bytes: bytes
    baseline_projection_spec_bytes_sha256: str
    pre_outcome_decision_bytes: bytes
    pre_outcome_decision_bytes_sha256: str
    adapter_environment_sha256: str
    decision_timing_sha256: str
    no_outcome_access_receipt_sha256: str
    synthetic_only: bool
    receipt_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "BaselineDecisionRunConformanceReceipt.v2"
    HASH_FIELD = "receipt_sha256"
    BYTES_FIELDS = frozenset(
        {"baseline_input_bytes", "baseline_projection_spec_bytes", "pre_outcome_decision_bytes"}
    )

    def _validate(self) -> None:
        if self.baseline_id not in _BASELINE_IDS:
            raise ValueError("conformance baseline is not mandatory")
        _require_identifier(self.executed_method_id, "executed_method_id")
        for name in (
            "readiness_status_sha256", "input_action_roster_sha256",
            "baseline_input_bytes_sha256", "baseline_projection_spec_bytes_sha256",
            "pre_outcome_decision_bytes_sha256",
            "adapter_environment_sha256", "decision_timing_sha256",
            "no_outcome_access_receipt_sha256",
        ):
            _require_hash(getattr(self, name), name)
        baseline_input = _canonical_bytes_value(
            self.baseline_input_bytes, "baseline_input_bytes"
        )
        if type(baseline_input) is not dict or not baseline_input:
            raise TypeError("baseline input must be a nonempty exact object")
        projection_spec = _canonical_bytes_value(
            self.baseline_projection_spec_bytes, "baseline_projection_spec_bytes"
        )
        _validate_projection_spec(projection_spec, require_full=False)
        decision = _canonical_bytes_value(
            self.pre_outcome_decision_bytes, "pre_outcome_decision_bytes"
        )
        if type(decision) is not dict or set(decision) != {"action"}:
            raise ValueError("baseline decision must have one action")
        _validate_action(decision["action"])
        if self.baseline_input_bytes_sha256 != _sha_bytes(self.baseline_input_bytes):
            raise ValueError("baseline input byte hash mismatch")
        if self.baseline_projection_spec_bytes_sha256 != _sha_bytes(
            self.baseline_projection_spec_bytes
        ):
            raise ValueError("baseline projection byte hash mismatch")
        if self.pre_outcome_decision_bytes_sha256 != _sha_bytes(
            self.pre_outcome_decision_bytes
        ):
            raise ValueError("baseline decision byte hash mismatch")


@dataclass(frozen=True, slots=True)
class SyntheticRetrospectiveOracleEvaluationV2(_Record):
    target_action_authority_sha256: str
    direct_action_value_table_bytes: bytes
    oracle_decision_bytes: bytes
    action_space_tie_rule_sha256: str
    admissibility_sha256: str
    synthetic_only: bool
    evaluation_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "SyntheticRetrospectiveOracleEvaluationV2.v2"
    HASH_FIELD = "evaluation_sha256"
    BYTES_FIELDS = frozenset({"direct_action_value_table_bytes", "oracle_decision_bytes"})

    def _validate(self) -> None:
        for name in (
            "target_action_authority_sha256", "action_space_tie_rule_sha256",
            "admissibility_sha256",
        ):
            _require_hash(getattr(self, name), name)
        table = _canonical_bytes_value(
            self.direct_action_value_table_bytes, "direct_action_value_table_bytes"
        )
        if type(table) is not list or not table:
            raise TypeError("direct action value table must be a nonempty array")
        action_hashes: set[str] = set()
        for row in table:
            if type(row) is not dict or set(row) != {"action", "blind_direct_value"}:
                raise ValueError("direct action value row has wrong keys")
            _validate_action(row["action"])
            _require_float(row["blind_direct_value"], "blind_direct_value")
            action_hash = _sha_value(row["action"])
            if action_hash in action_hashes:
                raise ValueError("direct action value table contains duplicate action")
            action_hashes.add(action_hash)
        decision = _canonical_bytes_value(self.oracle_decision_bytes, "oracle_decision_bytes")
        if type(decision) is not dict or set(decision) != {"action"}:
            raise ValueError("oracle decision must have one action")
        _validate_action(decision["action"])


@dataclass(frozen=True, slots=True)
class E3ComparatorContract(_Record):
    parity_receipt: PairedInformationParityReceipt
    parity_replay_bundle: SyntheticParityReplayBundle
    opaque_identity_registry: SyntheticOpaqueIdentityRegistryV2
    target_action_authority: SyntheticE3TargetActionAuthorityV2
    shared_e1_action_roster: SyntheticE1ActionRosterV2
    mandatory_roster: MandatoryBaselineRoster
    baseline_pre_outcome_readiness: tuple[BaselinePreOutcomeReadinessAuthority, ...]
    baseline_decision_conformance: tuple[BaselineDecisionRunConformanceReceipt, ...]
    retrospective_oracle_evaluation: SyntheticRetrospectiveOracleEvaluationV2
    analysis_code_sha256: str
    synthetic_only: bool
    contract_sha256: str

    SCHEMA = _SCHEMA_PREFIX + "E3ComparatorContract.v2"
    HASH_FIELD = "contract_sha256"

    def _validate(self) -> None:
        _validate_e3_contract(self)


E2MechanismContract.RECORD_FIELDS = {
    "opaque_identity_registry": SyntheticOpaqueIdentityRegistryV2,
}
E2MechanismContract.RECORD_TUPLE_FIELDS = {
    "e1_action_rosters": SyntheticE1ActionRosterV2,
    "solo_execution_records": SyntheticSoloExecutionConformanceV2,
    "auxiliary_control_plans": AuxiliaryControlPlanV2,
    "auxiliary_control_conformances": AuxiliaryControlConformanceV2,
    "bindings": FrozenResidualCapabilityBinding,
    "assignments": SyntheticAssignmentCrossoverRecord,
    "pair_assignment_closures": SyntheticPairAssignmentClosure,
    "support_balance_records": SyntheticSupportBalanceRecord,
    "execution_records": SyntheticExecutionConformanceRecord,
    "terminal_branches": SyntheticTerminalBranch,
    "pairs": FrozenE2Pair,
    "residual_absent_control_pairs": SyntheticResidualAbsentControlPair,
    "residual_absent_control_rosters": SyntheticResidualAbsentControlRoster,
}
MandatoryBaselineRoster.RECORD_TUPLE_FIELDS = {"entries": MandatoryBaselineRosterEntry}
E3ComparatorContract.RECORD_FIELDS = {
    "parity_receipt": PairedInformationParityReceipt,
    "parity_replay_bundle": SyntheticParityReplayBundle,
    "opaque_identity_registry": SyntheticOpaqueIdentityRegistryV2,
    "target_action_authority": SyntheticE3TargetActionAuthorityV2,
    "shared_e1_action_roster": SyntheticE1ActionRosterV2,
    "mandatory_roster": MandatoryBaselineRoster,
    "retrospective_oracle_evaluation": SyntheticRetrospectiveOracleEvaluationV2,
}
E3ComparatorContract.RECORD_TUPLE_FIELDS = {
    "baseline_pre_outcome_readiness": BaselinePreOutcomeReadinessAuthority,
    "baseline_decision_conformance": BaselineDecisionRunConformanceReceipt,
}


def _canonical_bytes_value(raw: object, name: str) -> object:
    if type(raw) is not bytes:
        raise TypeError(f"{name} must be exact bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(f"{name} is not UTF-8") from error
    return _loads_strict(text)


def validate_direct_terminal_branches(
    branches: tuple[SyntheticTerminalBranch, ...],
) -> None:
    _validate_collection(branches, SyntheticTerminalBranch, "record_sha256", "branches")
    keys: set[tuple[object, ...]] = set()
    for row in branches:
        key = (
            row.site_ref, row.case_ref, row.prefix_ref, row.treatment_kind,
            row.opaque_slot_id, row.actual_packet_id, row.repeat_index, row.seed,
        )
        if key in keys:
            raise ValueError("duplicate direct terminal branch")
        keys.add(key)


def _none_summary(contract: E2MechanismContract) -> E2SyntheticSummary:
    sites = {row.site_ref for row in contract.pairs}
    cases = {(row.site_ref, row.case_ref) for row in contract.pairs}
    census = {
        "focal_pairs": [row.pair_sha256 for row in contract.pairs],
        "controls": [row.control_pair_sha256 for row in contract.residual_absent_control_pairs],
        "rosters": [row.roster_sha256 for row in contract.residual_absent_control_rosters],
    }
    return E2SyntheticSummary.create(
        status="non_estimable_support",
        site_clustered_primary_contrast=None,
        secondary_cost_adjusted_utility=None,
        secondary_continuous_alignment_cost_interaction=None,
        site_count=len(sites),
        case_count=len(cases),
        row_count=len(contract.terminal_branches),
        support_census_sha256=_sha_value(census),
    )


_BINDING_SHARED = (
    "site_ref", "case_ref", "prefix_ref", "obligation_ontology_sha256",
    "residual_obligation_snapshot_sha256", "residual_source_receipt_sha256",
    "capability_matrix_sha256", "capability_matrix_source_receipt_sha256",
    "alignment_rule_sha256", "alignment_measure_kind", "capability_dimension_sha256",
    "obligation_relation_sha256", "effect_modifier_stratum", "support_cell_sha256",
    "pair_set_sha256", "synthetic_only",
)


def _validate_synthetic_e2(contract: E2MechanismContract) -> E2SyntheticSummary:
    if type(contract) is not E2MechanismContract:
        raise TypeError("contract must be exact E2MechanismContract")
    try:
        validate_direct_terminal_branches(contract.terminal_branches)
        bindings = {row.binding_sha256: row for row in contract.bindings}
        assignments = {row.record_sha256: row for row in contract.assignments}
        if len({row.assignment_ref for row in contract.assignments}) != len(contract.assignments):
            raise ValueError("assignment_ref must resolve exactly once")
        closures = {row.closure_sha256: row for row in contract.pair_assignment_closures}
        supports = {row.record_sha256: row for row in contract.support_balance_records}
        controls = {row.control_pair_key_sha256: row for row in contract.residual_absent_control_pairs}
        rosters_by_focal: dict[str, list[SyntheticResidualAbsentControlRoster]] = {}
        for roster in contract.residual_absent_control_rosters:
            rosters_by_focal.setdefault(roster.focal_pair_key_sha256, []).append(roster)
        executions_by_ref: dict[str, list[SyntheticExecutionConformanceRecord]] = {}
        for row in contract.execution_records:
            executions_by_ref.setdefault(row.assignment_ref, []).append(row)
        branches = contract.terminal_branches
        action_rosters_by_target: dict[tuple[str, str, str], SyntheticE1ActionRosterV2] = {}
        for action_roster in contract.e1_action_rosters:
            if action_roster.common_synthesis_spec_sha256 != contract.common_synthesis_spec_sha256:
                raise ValueError("E1 action roster synthesis specification mismatch")
            target = (action_roster.site_ref, action_roster.case_ref, action_roster.prefix_ref)
            if target in action_rosters_by_target:
                raise ValueError("E1 action roster target does not resolve once")
            action_rosters_by_target[target] = action_roster
        plans_by_focal_kind: dict[tuple[str, str], list[AuxiliaryControlPlanV2]] = {}
        for plan in contract.auxiliary_control_plans:
            plans_by_focal_kind.setdefault((plan.focal_pair_key_sha256, plan.control_kind), []).append(plan)
        conformances_by_plan: dict[str, list[AuxiliaryControlConformanceV2]] = {}
        for conformance in contract.auxiliary_control_conformances:
            conformances_by_plan.setdefault(conformance.control_plan_sha256, []).append(conformance)
        reached_bindings: set[str] = set()
        reached_assignments: set[str] = set()
        reached_closures: set[str] = set()
        reached_supports: set[str] = set()
        reached_executions: set[str] = set()
        reached_branches: set[str] = set()
        reached_controls: set[str] = set()
        reached_rosters: set[str] = set()
        reached_auxiliary_plans: set[str] = set()
        reached_auxiliary_conformances: set[str] = set()
        reached_action_rosters: set[str] = set()
        reached_solo_records: set[str] = set()
        expected_reference_census: dict[tuple[str, str, str], int] = {}
        realized_reference_census: dict[tuple[str, str, str], int] = {}
        reference_owners: dict[str, str] = {}

        def count_reference(
            assignment: SyntheticAssignmentCrossoverRecord,
            execution: SyntheticExecutionConformanceRecord,
            terminal: SyntheticTerminalBranch,
            focal_owner: str,
            *,
            expected: int,
            realized: int,
        ) -> None:
            key = (assignment.record_sha256, execution.record_sha256, terminal.record_sha256)
            expected_reference_census[key] = expected_reference_census.get(key, 0) + expected
            realized_reference_census[key] = realized_reference_census.get(key, 0) + realized
            for record_hash in key:
                owner = reference_owners.setdefault(record_hash, focal_owner)
                if owner != focal_owner:
                    raise ValueError("reference leg serves a second focal pair")

        def resolve_effect(
            row: FrozenE2Pair | SyntheticResidualAbsentControlPair,
            high_binding: FrozenResidualCapabilityBinding,
            low_binding: FrozenResidualCapabilityBinding,
            required_cells: set[tuple[int, int]] | None = None,
            focal_owner: str | None = None,
        ) -> tuple[float, set[tuple[int, int]]]:
            closure = closures[row.pair_assignment_closure_sha256]
            reached_closures.add(closure.closure_sha256)
            if (closure.site_ref, closure.case_ref, closure.prefix_ref) != (
                row.site_ref, row.case_ref, row.prefix_ref
            ):
                raise ValueError("assignment closure target mismatch")
            high_rows = [assignments[key] for key in closure.high_assignment_record_sha256s]
            low_rows = [assignments[key] for key in closure.low_assignment_record_sha256s]
            high_cells = {(item.repeat_index, item.seed) for item in high_rows}
            low_cells = {(item.repeat_index, item.seed) for item in low_rows}
            if len(high_cells) != len(high_rows) or len(low_cells) != len(low_rows) or high_cells != low_cells:
                raise ValueError("assignment repeat cells do not close")
            if required_cells is not None and high_cells != required_cells:
                raise ValueError("control repeat cells differ from focal")
            high_by_cell = {(item.repeat_index, item.seed): item for item in high_rows}
            low_by_cell = {(item.repeat_index, item.seed): item for item in low_rows}
            quality_diffs: list[float] = []
            for cell in sorted(high_cells):
                terminal: dict[str, SyntheticTerminalBranch] = {}
                for arm, assignment, packet_id, manifest in (
                    ("high", high_by_cell[cell], row.high_packet_id, row.high_complete_bundle_manifest_sha256),
                    ("low", low_by_cell[cell], row.low_packet_id, row.low_complete_bundle_manifest_sha256),
                ):
                    reached_assignments.add(assignment.record_sha256)
                    if (
                        (assignment.site_ref, assignment.case_ref, assignment.prefix_ref)
                        != (row.site_ref, row.case_ref, row.prefix_ref)
                        or assignment.assigned_actual_packet_id != packet_id
                        or assignment.assigned_complete_bundle_manifest_sha256 != manifest
                        or assignment.cyclic_crossover_plan_sha256 != closure.cyclic_crossover_plan_sha256
                        or assignment.complete_packet_roster_sha256 != closure.complete_packet_roster_sha256
                        or assignment.immutable_target_roster_sha256 != closure.immutable_target_roster_sha256
                        or assignment.assignment_probability_spec_sha256 != closure.assignment_probability_spec_sha256
                    ):
                        raise ValueError("assignment does not match pair closure")
                    execution_rows = executions_by_ref.get(assignment.assignment_ref, [])
                    if len(execution_rows) != 1:
                        raise ValueError("execution does not resolve exactly once")
                    execution = execution_rows[0]
                    reached_executions.add(execution.record_sha256)
                    if (
                        execution.compliance_status != "verified"
                        or (execution.site_ref, execution.case_ref, execution.prefix_ref, execution.repeat_index, execution.seed)
                        != (assignment.site_ref, assignment.case_ref, assignment.prefix_ref, assignment.repeat_index, assignment.seed)
                        or execution.assigned_opaque_slot_id != assignment.assigned_opaque_slot_id
                        or execution.assigned_actual_packet_id != packet_id
                        or execution.actual_opaque_slot_id != assignment.assigned_opaque_slot_id
                        or execution.actual_packet_id != packet_id
                        or execution.actual_complete_bundle_manifest_sha256 != manifest
                    ):
                        raise ValueError("execution is not assignment compliant")
                    candidates = [
                        branch
                        for branch in branches
                        if (
                            branch.site_ref, branch.case_ref, branch.prefix_ref,
                            branch.repeat_index, branch.seed, branch.treatment_kind,
                            branch.opaque_slot_id, branch.actual_packet_id,
                        )
                        == (
                            assignment.site_ref, assignment.case_ref, assignment.prefix_ref,
                            assignment.repeat_index, assignment.seed, "capability_packet",
                            assignment.assigned_opaque_slot_id, packet_id,
                        )
                    ]
                    if len(candidates) != 1:
                        raise ValueError("terminal branch does not resolve exactly once")
                    branch = candidates[0]
                    if branch.execution_conformance_sha256 != execution.post_run_execution_usage_conformance_receipt_sha256:
                        raise ValueError("terminal conformance mismatch")
                    reached_branches.add(branch.record_sha256)
                    count_reference(
                        assignment, execution, branch,
                        focal_owner or (
                            _focal_key(row)
                            if type(row) is FrozenE2Pair
                            else row.focal_pair_key_sha256
                        ),
                        expected=1, realized=1,
                    )
                    terminal[arm] = branch
                quality_diff = terminal["high"].blind_terminal_quality - terminal["low"].blind_terminal_quality
                quality_diffs.append(quality_diff)
            return math.fsum(quality_diffs) / len(quality_diffs), high_cells

        primary_by_site_case_target: dict[
            str, dict[str, dict[str, list[float]]]
        ] = {}
        census_rows: list[object] = []
        focal_keys = tuple(_focal_key(pair) for pair in contract.pairs)
        if len(focal_keys) != len(set(focal_keys)):
            raise ValueError("focal pair key must resolve exactly once")
        for pair in contract.pairs:
            high_binding = bindings[pair.high_residual_capability_binding_sha256]
            low_binding = bindings[pair.low_residual_capability_binding_sha256]
            reached_bindings.update({high_binding.binding_sha256, low_binding.binding_sha256})
            if any(getattr(high_binding, name) != getattr(low_binding, name) for name in _BINDING_SHARED):
                raise ValueError("focal binding parents differ")
            if (
                (high_binding.site_ref, high_binding.case_ref, high_binding.prefix_ref)
                != (pair.site_ref, pair.case_ref, pair.prefix_ref)
                or (low_binding.site_ref, low_binding.case_ref, low_binding.prefix_ref)
                != (pair.site_ref, pair.case_ref, pair.prefix_ref)
                or high_binding.alignment_role != "high"
                or low_binding.alignment_role != "low"
                or high_binding.effect_modifier_stratum != "matched_residual_present"
                or high_binding.opaque_packet_id != pair.high_packet_id
                or low_binding.opaque_packet_id != pair.low_packet_id
                or high_binding.complete_bundle_manifest_sha256 != pair.high_complete_bundle_manifest_sha256
                or low_binding.complete_bundle_manifest_sha256 != pair.low_complete_bundle_manifest_sha256
                or high_binding.pair_set_sha256 != pair.pair_set_sha256
            ):
                raise ValueError("focal binding orientation mismatch")
            support = supports[pair.balance_support_record_sha256]
            reached_supports.add(support.record_sha256)
            if (
                (support.site_ref, support.case_ref, support.prefix_ref)
                != (pair.site_ref, pair.case_ref, pair.prefix_ref)
                or support.support_status != "adequate"
                or support.support_cell_sha256 != high_binding.support_cell_sha256
            ):
                raise ValueError("focal support is not adequate")
            focal_d, focal_cells = resolve_effect(pair, high_binding, low_binding)
            focal_key = _focal_key(pair)
            roster_rows = rosters_by_focal.get(focal_key, [])
            if len(roster_rows) != 1:
                raise ValueError("focal control roster does not resolve once")
            roster = roster_rows[0]
            reached_rosters.add(roster.roster_sha256)
            if (
                roster.support_cell_sha256 != support.support_cell_sha256
                or roster.pair_set_sha256 != pair.pair_set_sha256
                or roster.selection_spec_sha256 != support.residual_absent_control_selection_spec_sha256
            ):
                raise ValueError("control roster does not match focal support")
            control_diffs: list[float] = []
            control_census: list[object] = []
            focal_control_parents = (
                high_binding.obligation_ontology_sha256,
                high_binding.capability_matrix_sha256,
                high_binding.capability_matrix_source_receipt_sha256,
                high_binding.alignment_rule_sha256,
                high_binding.alignment_measure_kind,
                high_binding.capability_dimension_sha256,
                high_binding.obligation_relation_sha256,
            )
            for key, weight in zip(roster.control_pair_key_sha256s, roster.matching_weights, strict=True):
                control = controls[key]
                reached_controls.add(control.control_pair_sha256)
                if control.matching_weight != weight:
                    raise ValueError("roster/control weight mismatch")
                if (
                    control.focal_pair_key_sha256 != focal_key
                    or control.site_ref != pair.site_ref
                    or (control.case_ref, control.prefix_ref) == (pair.case_ref, pair.prefix_ref)
                    or control.high_packet_id != pair.high_packet_id
                    or control.low_packet_id != pair.low_packet_id
                    or control.high_complete_bundle_manifest_sha256 != pair.high_complete_bundle_manifest_sha256
                    or control.low_complete_bundle_manifest_sha256 != pair.low_complete_bundle_manifest_sha256
                    or control.evaluator_reference_sha256 != pair.evaluator_reference_sha256
                    or control.pair_set_sha256 != pair.pair_set_sha256
                    or control.residual_absent_control_selection_spec_sha256 != roster.selection_spec_sha256
                ):
                    raise ValueError("residual-absent control target mismatch")
                control_support = supports[control.balance_support_record_sha256]
                reached_supports.add(control_support.record_sha256)
                if (
                    (control_support.site_ref, control_support.case_ref, control_support.prefix_ref)
                    != (control.site_ref, control.case_ref, control.prefix_ref)
                    or control_support.support_status != "adequate"
                    or control_support.global_bundle_strength_control_sha256 is not None
                    or control_support.uniform_random_control_sha256 is not None
                    or control_support.residual_absent_control_selection_spec_sha256 != roster.selection_spec_sha256
                ):
                    raise ValueError("control support is not adequate")
                control_high = bindings[control.high_residual_capability_binding_sha256]
                control_low = bindings[control.low_residual_capability_binding_sha256]
                reached_bindings.update({control_high.binding_sha256, control_low.binding_sha256})
                if any(getattr(control_high, name) != getattr(control_low, name) for name in _BINDING_SHARED):
                    raise ValueError("control binding parents differ")
                control_parents = (
                    control_high.obligation_ontology_sha256,
                    control_high.capability_matrix_sha256,
                    control_high.capability_matrix_source_receipt_sha256,
                    control_high.alignment_rule_sha256,
                    control_high.alignment_measure_kind,
                    control_high.capability_dimension_sha256,
                    control_high.obligation_relation_sha256,
                )
                if (
                    (control_high.site_ref, control_high.case_ref, control_high.prefix_ref)
                    != (control.site_ref, control.case_ref, control.prefix_ref)
                    or (control_low.site_ref, control_low.case_ref, control_low.prefix_ref)
                    != (control.site_ref, control.case_ref, control.prefix_ref)
                    or control_parents != focal_control_parents
                    or control_high.alignment_role != "residual_absent_control"
                    or control_low.alignment_role != "residual_absent_control"
                    or control_high.effect_modifier_stratum != "matched_residual_absent"
                    or control_high.opaque_packet_id != control.high_packet_id
                    or control_low.opaque_packet_id != control.low_packet_id
                    or control_high.complete_bundle_manifest_sha256 != control.high_complete_bundle_manifest_sha256
                    or control_low.complete_bundle_manifest_sha256 != control.low_complete_bundle_manifest_sha256
                    or control_support.support_cell_sha256 != control_high.support_cell_sha256
                ):
                    raise ValueError("control binding orientation mismatch")
                c_d, _ = resolve_effect(control, control_high, control_low, focal_cells)
                control_diffs.append(weight * c_d)
                control_census.append([control.control_pair_key_sha256, weight])

            for kind in _AUXILIARY_CONTROL_KINDS:
                plan_rows = plans_by_focal_kind.get((focal_key, kind), [])
                if len(plan_rows) != 1:
                    raise ValueError("focal auxiliary plan does not resolve once")
                plan = plan_rows[0]
                conformance_rows = conformances_by_plan.get(plan.plan_sha256, [])
                if len(conformance_rows) != 1 or conformance_rows[0].compliance_status != "verified":
                    raise ValueError("auxiliary conformance does not resolve once and verified")
                conformance = conformance_rows[0]
                reached_auxiliary_plans.add(plan.plan_sha256)
                reached_auxiliary_conformances.add(conformance.conformance_sha256)
                target = (plan.site_ref, plan.case_ref, plan.prefix_ref)
                expected_plan_roster = _target_action_roster_digest(
                    plan.site_ref, plan.case_ref, plan.prefix_ref,
                    plan.packet_ids, plan.repeat_seed_cells,
                )
                if plan.target_action_roster_sha256 != expected_plan_roster:
                    raise ValueError("auxiliary plan target roster digest mismatch")
                e1_roster = action_rosters_by_target.get(target)
                if kind == "global_bundle_strength":
                    planned_control = [
                        row for row in contract.residual_absent_control_pairs
                        if row.focal_pair_key_sha256 == focal_key
                        and (row.site_ref, row.case_ref, row.prefix_ref) == (plan.site_ref, plan.case_ref, plan.prefix_ref)
                        and row.control_ref == plan.control_ref
                    ]
                    if len(planned_control) != 1:
                        raise ValueError("global control target does not resolve")
                    global_control = planned_control[0]
                    global_support = supports[global_control.balance_support_record_sha256]
                    expected_assignments = tuple(sorted(
                        closures[global_control.pair_assignment_closure_sha256].high_assignment_record_sha256s
                        + closures[global_control.pair_assignment_closure_sha256].low_assignment_record_sha256s
                    ))
                    if (
                        plan.packet_ids != tuple(sorted((pair.high_packet_id, pair.low_packet_id)))
                        or plan.repeat_seed_cells != tuple(sorted(focal_cells))
                        or plan.support_cell_sha256 != global_support.support_cell_sha256
                        or plan.selection_probability_spec_sha256 != global_support.residual_absent_control_selection_spec_sha256
                        or plan.assignment_record_sha256s != expected_assignments
                        or support.global_bundle_strength_control_sha256 != conformance.conformance_sha256
                    ):
                        raise ValueError("global control plan disagrees with focal authority")
                else:
                    if e1_roster is None:
                        raise ValueError("uniform control requires a same-target E1 roster")
                    if (
                        plan.packet_ids != e1_roster.packet_ids
                        or plan.repeat_seed_cells != e1_roster.repeat_seed_cells
                    ):
                        raise ValueError("uniform control menu does not equal same-target E1 roster")
                    if (
                        (plan.site_ref, plan.case_ref, plan.prefix_ref) != (pair.site_ref, pair.case_ref, pair.prefix_ref)
                        or plan.repeat_seed_cells != tuple(sorted(focal_cells))
                        or plan.support_cell_sha256 != support.support_cell_sha256
                        or support.uniform_random_control_sha256 != conformance.conformance_sha256
                    ):
                        raise ValueError("uniform control plan disagrees with focal authority")
                    selected = [assignments[key] for key in plan.assignment_record_sha256s]
                    if len(selected) != len(focal_cells) or {(row.repeat_index, row.seed) for row in selected} != focal_cells:
                        raise ValueError("uniform control cells do not close")
                    if any(
                        row.assignment_probability != 1.0 / len(plan.packet_ids)
                        or row.assignment_probability_spec_sha256 != plan.selection_probability_spec_sha256
                        or (row.site_ref, row.case_ref, row.prefix_ref)
                        != (plan.site_ref, plan.case_ref, plan.prefix_ref)
                        or row.assigned_actual_packet_id not in plan.packet_ids
                        for row in selected
                    ):
                        raise ValueError("uniform control probability is not exact")
                if conformance.assignment_record_sha256s != plan.assignment_record_sha256s:
                    raise ValueError("conformance selected an unplanned assignment")
                expected_executions: list[str] = []
                expected_terminals: list[str] = []
                for assignment_hash, multiplicity in zip(plan.assignment_record_sha256s, plan.assignment_reference_multiplicities, strict=True):
                    assignment = assignments[assignment_hash]
                    if assignment.immutable_target_roster_sha256 == expected_plan_roster:
                        pass
                    elif (
                        e1_roster is not None
                        and assignment.immutable_target_roster_sha256 == e1_roster.roster_sha256
                        and assignment.assigned_actual_packet_id in e1_roster.packet_ids
                        and (assignment.repeat_index, assignment.seed)
                        in e1_roster.repeat_seed_cells
                    ):
                        pass
                    else:
                        raise ValueError("auxiliary assignment owner is neither plan-only nor exact E1 roster")
                    execution_rows = executions_by_ref.get(assignment.assignment_ref, [])
                    if len(execution_rows) != 1:
                        raise ValueError("auxiliary assignment execution is not unique")
                    execution = execution_rows[0]
                    terminal_rows = [
                        row for row in branches
                        if (
                            row.site_ref, row.case_ref, row.prefix_ref,
                            row.repeat_index, row.seed, row.treatment_kind,
                            row.opaque_slot_id, row.actual_packet_id,
                            row.execution_conformance_sha256,
                        ) == (
                            assignment.site_ref, assignment.case_ref, assignment.prefix_ref,
                            assignment.repeat_index, assignment.seed, "capability_packet",
                            assignment.assigned_opaque_slot_id, assignment.assigned_actual_packet_id,
                            execution.post_run_execution_usage_conformance_receipt_sha256,
                        )
                    ]
                    if len(terminal_rows) != 1:
                        raise ValueError("auxiliary assignment terminal is not unique")
                    terminal = terminal_rows[0]
                    if (
                        execution.compliance_status != "verified"
                        or (execution.site_ref, execution.case_ref, execution.prefix_ref, execution.repeat_index, execution.seed)
                        != (assignment.site_ref, assignment.case_ref, assignment.prefix_ref, assignment.repeat_index, assignment.seed)
                        or execution.assigned_opaque_slot_id != assignment.assigned_opaque_slot_id
                        or execution.assigned_actual_packet_id != assignment.assigned_actual_packet_id
                        or execution.actual_opaque_slot_id != assignment.assigned_opaque_slot_id
                        or execution.actual_packet_id != assignment.assigned_actual_packet_id
                        or execution.actual_complete_bundle_manifest_sha256 != assignment.assigned_complete_bundle_manifest_sha256
                    ):
                        raise ValueError("auxiliary conformance join is not exact")
                    expected_executions.append(execution.record_sha256)
                    expected_terminals.append(terminal.record_sha256)
                    reached_assignments.add(assignment_hash)
                    reached_executions.add(execution.record_sha256)
                    reached_branches.add(terminal.record_sha256)
                    count_reference(
                        assignment, execution, terminal, focal_key,
                        expected=multiplicity, realized=1,
                    )
                if (
                    conformance.execution_record_sha256s != tuple(sorted(expected_executions))
                    or conformance.terminal_record_sha256s != tuple(sorted(expected_terminals))
                ):
                    raise ValueError("auxiliary conformance tuples are not exact joins")
            primary = focal_d - math.fsum(control_diffs)
            primary_by_site_case_target.setdefault(pair.site_ref, {}).setdefault(
                pair.case_ref, {}
            ).setdefault(pair.prefix_ref, []).append(primary)
            census_rows.append(
                [pair.site_ref, pair.case_ref, pair.prefix_ref, focal_key, control_census]
            )

        e1_rosters_by_hash = {
            row.roster_sha256: row for row in contract.e1_action_rosters
        }
        for roster in contract.e1_action_rosters:
            target = (roster.site_ref, roster.case_ref, roster.prefix_ref)
            reached_action_rosters.add(roster.roster_sha256)
            for repeat_index, seed in roster.repeat_seed_cells:
                solo_rows = [
                    row for row in contract.solo_execution_records
                    if (row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed)
                    == (*target, repeat_index, seed)
                ]
                solo_terminals = [
                    row for row in branches
                    if (row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed,
                        row.treatment_kind, row.opaque_slot_id, row.actual_packet_id)
                    == (*target, repeat_index, seed, "solo_synthesis", None, None)
                ]
                if (
                    len(solo_rows) != 1
                    or len(solo_terminals) != 1
                    or solo_rows[0].common_synthesis_spec_sha256
                    != roster.common_synthesis_spec_sha256
                    or solo_rows[0].compliance_status != "verified"
                    or solo_terminals[0].execution_conformance_sha256
                    != solo_rows[0].record_sha256
                ):
                    raise ValueError("E1 SOLO closure does not resolve exactly once and verified")
                reached_solo_records.add(solo_rows[0].record_sha256)
                reached_branches.add(solo_terminals[0].record_sha256)
            for packet_id in roster.packet_ids:
                for repeat_index, seed in roster.repeat_seed_cells:
                    owned_rows = [
                        row for row in assignments.values()
                        if (row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed,
                            row.assigned_actual_packet_id, row.immutable_target_roster_sha256)
                        == (*target, repeat_index, seed, packet_id, roster.roster_sha256)
                    ]
                    if len(owned_rows) != 1:
                        raise ValueError("E1 packet assignment ownership does not resolve exactly once")
                    assignment = owned_rows[0]
                    execution_rows = executions_by_ref.get(assignment.assignment_ref, [])
                    terminal_rows = [
                        row for row in branches
                        if (row.site_ref, row.case_ref, row.prefix_ref, row.repeat_index, row.seed,
                            row.treatment_kind, row.opaque_slot_id, row.actual_packet_id)
                        == (*target, repeat_index, seed, "capability_packet",
                            assignment.assigned_opaque_slot_id, packet_id)
                    ]
                    if (
                        len(execution_rows) != 1
                        or len(terminal_rows) != 1
                        or execution_rows[0].compliance_status != "verified"
                        or (execution_rows[0].site_ref, execution_rows[0].case_ref,
                            execution_rows[0].prefix_ref, execution_rows[0].repeat_index,
                            execution_rows[0].seed)
                        != (*target, repeat_index, seed)
                        or execution_rows[0].assigned_opaque_slot_id
                        != assignment.assigned_opaque_slot_id
                        or execution_rows[0].assigned_actual_packet_id != packet_id
                        or execution_rows[0].actual_opaque_slot_id
                        != assignment.assigned_opaque_slot_id
                        or execution_rows[0].actual_packet_id != packet_id
                        or execution_rows[0].actual_complete_bundle_manifest_sha256
                        != assignment.assigned_complete_bundle_manifest_sha256
                        or terminal_rows[0].execution_conformance_sha256
                        != execution_rows[0].post_run_execution_usage_conformance_receipt_sha256
                    ):
                        raise ValueError("E1 packet closure does not resolve exactly once and verified")
                    owner = reference_owners.get(assignment.record_sha256)
                    if owner is None and contract.pairs:
                        raise ValueError("E1 packet assignment is not owned by a focal pair")
                    reached_assignments.add(assignment.record_sha256)
                    reached_executions.add(execution_rows[0].record_sha256)
                    reached_branches.add(terminal_rows[0].record_sha256)
                    if owner is not None:
                        count_reference(
                            assignment, execution_rows[0], terminal_rows[0], owner,
                            expected=1, realized=1,
                        )
        for assignment in assignments.values():
            roster = e1_rosters_by_hash.get(assignment.immutable_target_roster_sha256)
            if roster is not None and assignment.record_sha256 not in reached_assignments:
                raise ValueError("E1 roster-owned assignment is extra or has foreign target/cell")

        if reached_bindings != set(bindings):
            raise ValueError("unreachable binding")
        if reached_assignments != set(assignments):
            raise ValueError("unreachable assignment")
        if reached_closures != set(closures):
            raise ValueError("unreachable closure")
        if reached_supports != set(supports):
            raise ValueError("unreachable support")
        if reached_executions != {row.record_sha256 for row in contract.execution_records}:
            raise ValueError("unreachable execution")
        if reached_controls != {row.control_pair_sha256 for row in contract.residual_absent_control_pairs}:
            raise ValueError("unreachable control")
        if reached_rosters != {row.roster_sha256 for row in contract.residual_absent_control_rosters}:
            raise ValueError("unreachable control roster")
        if reached_auxiliary_plans != {row.plan_sha256 for row in contract.auxiliary_control_plans}:
            raise ValueError("unreachable auxiliary plan")
        if reached_auxiliary_conformances != {row.conformance_sha256 for row in contract.auxiliary_control_conformances}:
            raise ValueError("unreachable auxiliary conformance")
        if reached_action_rosters != {row.roster_sha256 for row in contract.e1_action_rosters}:
            raise ValueError("unreachable E1 action roster")
        if reached_solo_records != {row.record_sha256 for row in contract.solo_execution_records}:
            raise ValueError("unreachable SOLO conformance")
        if expected_reference_census != realized_reference_census:
            raise ValueError("reference census does not match realized joins")
        if {row.record_sha256 for row in contract.terminal_branches} != reached_branches:
            raise ValueError("unreachable terminal")
        if not contract.pairs:
            return _none_summary(contract)

        def aggregate(
            values: dict[str, dict[str, dict[str, list[float]]]],
        ) -> float:
            site_values = []
            for site in sorted(values):
                case_values = []
                for _, targets in sorted(values[site].items()):
                    target_values = [
                        math.fsum(pair_values) / len(pair_values)
                        for _, pair_values in sorted(targets.items())
                    ]
                    case_values.append(math.fsum(target_values) / len(target_values))
                site_values.append(math.fsum(case_values) / len(case_values))
            return math.fsum(site_values) / len(site_values)

        return E2SyntheticSummary.create(
            status="synthetic_complete",
            site_clustered_primary_contrast=aggregate(primary_by_site_case_target),
            secondary_cost_adjusted_utility=None,
            secondary_continuous_alignment_cost_interaction=None,
            site_count=len(primary_by_site_case_target),
            case_count=sum(
                len(value) for value in primary_by_site_case_target.values()
            ),
            row_count=len(contract.terminal_branches),
            support_census_sha256=_sha_value(sorted(census_rows)),
        )
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(str(error)) from error


def evaluate_synthetic_e2(contract: E2MechanismContract) -> E2SyntheticSummary:
    """Fail closed publicly while the private validator retains failure reasons."""
    if type(contract) is not E2MechanismContract:
        raise TypeError("contract must be exact E2MechanismContract")
    try:
        return _validate_synthetic_e2(contract)
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError):
        return _none_summary(contract)


def _validate_action(value: object) -> None:
    if type(value) is not dict or "action_kind" not in value:
        raise ValueError("action must be an exact typed object")
    if value["action_kind"] in {"stop", "solo"}:
        if set(value) != {"action_kind"}:
            raise ValueError("reserved action has extra identity")
        return
    if value["action_kind"] != "capability_packet" or set(value) != {
        "action_kind", "opaque_packet_id", "opaque_slot_id"
    }:
        raise ValueError("capability action has wrong schema")
    _require_opaque_id(value["opaque_packet_id"], "opaque_packet_id")
    _require_opaque_id(value["opaque_slot_id"], "opaque_slot_id")


def _validate_action_roster(value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list or len(value) < 3:
        raise ValueError("target action roster must contain stop, solo, and packets")
    if value[0] != {"action_kind": "stop"} or value[1] != {"action_kind": "solo"}:
        raise ValueError("target action roster has wrong reserved-action order")
    hashes: set[str] = set()
    slots: set[str] = set()
    packets: set[str] = set()
    result: list[dict[str, object]] = []
    for index, action in enumerate(value):
        _validate_action(action)
        if index >= 2:
            if action["action_kind"] != "capability_packet":
                raise ValueError("nonpacket action appears after reserved actions")
            slot_id = action["opaque_slot_id"]
            packet_id = action["opaque_packet_id"]
            if slot_id in slots or packet_id in packets:
                raise ValueError("capability actions are not one-to-one")
            slots.add(slot_id)
            packets.add(packet_id)
        action_hash = _sha_value(action)
        if action_hash in hashes:
            raise ValueError("target action roster contains duplicate action")
        hashes.add(action_hash)
        result.append(action)
    return tuple(result)


def _validate_projection_spec(value: object, *, require_full: bool) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"schema_version", "field_map"}:
        raise ValueError("projection spec must be an exact object")
    if value["schema_version"] != _E3_PROJECTION_SCHEMA:
        raise ValueError("projection spec schema mismatch")
    mapping = value["field_map"]
    if type(mapping) is not dict or not mapping:
        raise ValueError("projection field_map must be nonempty")
    if any(type(left) is not str or not left for left in mapping):
        raise TypeError("projected field names must be nonempty strings")
    sources = tuple(mapping.values())
    if any(type(source) is not str or source not in _E3_PARENT_FIELDS for source in sources):
        raise ValueError("projection selects an unknown parent field")
    if len(set(sources)) != len(sources):
        raise ValueError("projection cannot duplicate parent information")
    if require_full and set(sources) != set(_E3_PARENT_FIELDS):
        raise ValueError("parity projection must be a bijection over all parent fields")
    return mapping


def _projection(parent: dict[str, object], mapping: dict[str, str]) -> dict[str, object]:
    return {output_name: parent[parent_name] for output_name, parent_name in mapping.items()}


def _validate_parent(parent: object) -> dict[str, object]:
    if type(parent) is not dict or set(parent) != {"schema_version", *_E3_PARENT_FIELDS}:
        raise ValueError("E3 source parent has missing or extra fields")
    if parent["schema_version"] != _E3_PARENT_SCHEMA:
        raise ValueError("E3 source parent schema mismatch")
    for name in ("site_ref", "case_ref", "prefix_ref"):
        _require_identifier(parent[name], name)

    transcript = parent["raw_transcript_prefix"]
    if type(transcript) is not list or not transcript:
        raise TypeError("raw_transcript_prefix must be a nonempty array")
    for message in transcript:
        if type(message) is not dict or set(message) != {"role", "token_ids"}:
            raise ValueError("transcript message has wrong keys")
        if message["role"] not in {"system", "user", "assistant", "tool"}:
            raise ValueError("transcript role is invalid")
        token_ids = message["token_ids"]
        if type(token_ids) is not list or not token_ids:
            raise TypeError("token_ids must be a nonempty array")
        for token_id in token_ids:
            _require_int(token_id, "token_id")

    residual = parent["numeric_residual_serialization"]
    if type(residual) is not dict or set(residual) != {"obligation", "capability", "alignment"}:
        raise ValueError("numeric residual serialization has wrong keys")
    dimensions: list[int] = []
    for name in ("obligation", "capability", "alignment"):
        vector = residual[name]
        if type(vector) is not list or not vector:
            raise TypeError("numeric residual vectors must be nonempty arrays")
        for item in vector:
            _require_float(item, name)
        dimensions.append(len(vector))
    if len(set(dimensions)) != 1:
        raise ValueError("numeric residual vectors have unequal dimensions")
    dimension = dimensions[0]

    actions = _validate_action_roster(parent["target_action_roster"])
    action_hashes = tuple(_sha_value(action) for action in actions)
    packet_actions = actions[2:]
    capability_table = parent["complete_capability_table"]
    if type(capability_table) is not list or len(capability_table) != len(packet_actions):
        raise ValueError("complete capability table cardinality mismatch")
    for row, action in zip(capability_table, packet_actions, strict=True):
        if type(row) is not dict or set(row) != {
            "opaque_slot_id", "opaque_packet_id", "complete_bundle_manifest_sha256",
            "capability_vector",
        }:
            raise ValueError("capability-table row has wrong keys")
        if (
            row["opaque_slot_id"] != action["opaque_slot_id"]
            or row["opaque_packet_id"] != action["opaque_packet_id"]
        ):
            raise ValueError("capability table does not follow target roster")
        _require_hash(row["complete_bundle_manifest_sha256"], "complete_bundle_manifest_sha256")
        vector = row["capability_vector"]
        if type(vector) is not list or len(vector) != dimension:
            raise ValueError("capability vector dimension mismatch")
        for item in vector:
            _require_float(item, "capability_vector")

    cards = parent["opaque_packet_binding_cards"]
    if type(cards) is not list or len(cards) != len(packet_actions):
        raise ValueError("opaque binding card cardinality mismatch")
    for card, action in zip(cards, packet_actions, strict=True):
        if type(card) is not dict or set(card) != {"opaque_packet_id", "binding_sha256"}:
            raise ValueError("opaque binding card has wrong keys")
        if card["opaque_packet_id"] != action["opaque_packet_id"]:
            raise ValueError("opaque binding card packet mismatch")
        _require_hash(card["binding_sha256"], "binding_sha256")

    costs = parent["costs"]
    if type(costs) is not list or len(costs) != len(actions):
        raise ValueError("cost roster cardinality mismatch")
    for cost, action_hash in zip(costs, action_hashes, strict=True):
        if type(cost) is not dict or set(cost) != {
            "action_sha256", "processed_tokens", "latency_seconds", "list_price_cost"
        }:
            raise ValueError("cost row has wrong keys")
        if cost["action_sha256"] != action_hash:
            raise ValueError("cost row action mismatch")
        _require_int(cost["processed_tokens"], "processed_tokens")
        _require_float(cost["latency_seconds"], "latency_seconds", minimum=0.0)
        _require_float(cost["list_price_cost"], "list_price_cost", minimum=0.0)

    admissibility = parent["admissibility"]
    if type(admissibility) is not dict or set(admissibility) != {"admissible_action_sha256s"}:
        raise ValueError("admissibility has wrong keys")
    admissible = admissibility["admissible_action_sha256s"]
    if type(admissible) is not list or not admissible:
        raise TypeError("admissible action list must be nonempty")
    for action_hash in admissible:
        _require_hash(action_hash, "admissible_action_sha256")
    expected_admissible = [value for value in action_hashes if value in set(admissible)]
    if admissible != expected_admissible or len(admissible) != len(set(admissible)):
        raise ValueError("admissible actions must be a unique roster-ordered subset")

    examples = parent["examples"]
    if type(examples) is not list or not examples:
        raise TypeError("examples must be a nonempty array")
    encoded_examples: list[bytes] = []
    for example in examples:
        if type(example) is not dict or set(example) != {"input_sha256", "action_sha256"}:
            raise ValueError("example has wrong keys")
        _require_hash(example["input_sha256"], "input_sha256")
        _require_hash(example["action_sha256"], "action_sha256")
        if example["action_sha256"] not in admissible:
            raise ValueError("example action is inadmissible")
        encoded_examples.append(_canonical(example).encode("utf-8"))
    if encoded_examples != sorted(encoded_examples) or len(encoded_examples) != len(set(encoded_examples)):
        raise ValueError("examples must be byte sorted and unique")

    split = parent["split_fold"]
    if type(split) is not dict or set(split) != {
        "held_out_site_ref", "training_site_refs", "manifest_sha256"
    }:
        raise ValueError("split_fold has wrong keys")
    if split["held_out_site_ref"] != parent["site_ref"]:
        raise ValueError("held-out site does not equal target site")
    training_sites = split["training_site_refs"]
    if type(training_sites) is not list or not training_sites:
        raise TypeError("training_site_refs must be nonempty")
    for site in training_sites:
        _require_identifier(site, "training_site_ref")
    if (
        training_sites != sorted(training_sites, key=lambda item: item.encode("utf-8"))
        or len(training_sites) != len(set(training_sites))
        or parent["site_ref"] in training_sites
    ):
        raise ValueError("training sites are not a disjoint byte-sorted set")
    _require_hash(split["manifest_sha256"], "manifest_sha256")

    learner = parent["learner_class_capacity"]
    if type(learner) is not dict or set(learner) != {
        "learner_class_sha256", "parameter_budget", "context_token_budget", "tool_policy_sha256"
    }:
        raise ValueError("learner_class_capacity has wrong keys")
    _require_hash(learner["learner_class_sha256"], "learner_class_sha256")
    _require_int(learner["parameter_budget"], "parameter_budget", minimum=1)
    _require_int(learner["context_token_budget"], "context_token_budget", minimum=1)
    _require_hash(learner["tool_policy_sha256"], "tool_policy_sha256")

    tuning = parent["tuning_optimization_opportunity"]
    if type(tuning) is not dict or set(tuning) != {
        "objective_sha256", "trial_budget", "seeds", "early_stop_rule_sha256"
    }:
        raise ValueError("tuning opportunity has wrong keys")
    _require_hash(tuning["objective_sha256"], "objective_sha256")
    _require_int(tuning["trial_budget"], "trial_budget", minimum=1)
    seeds = tuning["seeds"]
    if type(seeds) is not list or not seeds:
        raise TypeError("tuning seeds must be nonempty")
    for seed in seeds:
        _require_int(seed, "tuning seed")
    if seeds != sorted(seeds) or len(seeds) != len(set(seeds)):
        raise ValueError("tuning seeds must be sorted and unique")
    _require_hash(tuning["early_stop_rule_sha256"], "early_stop_rule_sha256")

    tie = parent["action_space_tie_rule"]
    if type(tie) is not dict or set(tie) != {"rule_sha256", "ordered_action_sha256s"}:
        raise ValueError("action-space tie rule has wrong keys")
    if tie["rule_sha256"] != _sha_value(_E3_TIE_RULE):
        raise ValueError("action-space tie rule digest mismatch")
    if tie["ordered_action_sha256s"] != list(action_hashes):
        raise ValueError("tie-rule action order mismatch")
    return {
        "parent": parent,
        "actions": actions,
        "action_hashes": action_hashes,
        "admissible_action_sha256s": tuple(admissible),
    }


def _validate_decision(
    value: object,
    actions: tuple[dict[str, object], ...],
    admissible_action_sha256s: tuple[str, ...],
    name: str,
) -> None:
    if type(value) is not dict or set(value) != {"action"}:
        raise ValueError(f"{name} must be an exact one-action object")
    _validate_action(value["action"])
    if value["action"] not in actions or _sha_value(value["action"]) not in admissible_action_sha256s:
        raise ValueError(f"{name} selects a foreign or inadmissible action")


def _validate_parity_bundle(bundle: SyntheticParityReplayBundle) -> dict[str, object]:
    if type(bundle) is not SyntheticParityReplayBundle:
        raise TypeError("bundle must be exact SyntheticParityReplayBundle")
    parsed = {
        name: _canonical_bytes_value(getattr(bundle, name), name)
        for name in bundle.BYTES_FIELDS
    }
    parent_result = _validate_parent(parsed["source_parent_bytes"])
    parent = parent_result["parent"]
    actions = parent_result["actions"]
    admissible = parent_result["admissible_action_sha256s"]
    if parsed["target_action_roster_bytes"] != list(actions):
        raise ValueError("target action roster bytes do not equal parent roster")
    training = parsed["shared_training_opportunity_bytes"]
    if type(training) is not dict or set(training) != set(_E3_SHARED_FIELDS):
        raise ValueError("shared training opportunity has wrong keys")
    if any(training[name] != parent[name] for name in _E3_SHARED_FIELDS):
        raise ValueError("shared training opportunity differs from parent")
    oacs_map = _validate_projection_spec(parsed["oacs_projection_spec_bytes"], require_full=True)
    raw_map = _validate_projection_spec(parsed["raw_router_projection_spec_bytes"], require_full=True)
    if parsed["oacs_input_bytes"] != _projection(parent, oacs_map):
        raise ValueError("OACS projected input replay mismatch")
    if parsed["raw_router_input_bytes"] != _projection(parent, raw_map):
        raise ValueError("raw-router projected input replay mismatch")
    oacs_inverse = {source: output for output, source in oacs_map.items()}
    raw_inverse = {source: output for output, source in raw_map.items()}
    expected_equivalence = [
        {
            "parent_field": source,
            "oacs_field": oacs_inverse[source],
            "raw_router_field": raw_inverse[source],
        }
        for source in _E3_PARENT_FIELDS
    ]
    if parsed["information_equivalence_map_bytes"] != expected_equivalence:
        raise ValueError("information equivalence map is not complete and derived")
    _validate_decision(
        parsed["oacs_pre_outcome_decision_bytes"], actions, admissible, "OACS decision"
    )
    _validate_decision(
        parsed["raw_router_pre_outcome_decision_bytes"], actions, admissible,
        "raw-router decision",
    )
    return {**parent_result, "training": training}


def validate_paired_information_parity(
    receipt: PairedInformationParityReceipt,
    replay_bundle: SyntheticParityReplayBundle,
) -> None:
    if type(receipt) is not PairedInformationParityReceipt:
        raise TypeError("receipt must be exact PairedInformationParityReceipt")
    result = _validate_parity_bundle(replay_bundle)
    training = result["training"]
    actual = {
        "source_parent_receipt_sha256": _sha_bytes(replay_bundle.source_parent_bytes),
        "oacs_input_bytes_sha256": _sha_bytes(replay_bundle.oacs_input_bytes),
        "raw_router_input_bytes_sha256": _sha_bytes(replay_bundle.raw_router_input_bytes),
        "oacs_projection_spec_sha256": _sha_bytes(replay_bundle.oacs_projection_spec_bytes),
        "raw_router_projection_spec_sha256": _sha_bytes(replay_bundle.raw_router_projection_spec_bytes),
        "information_equivalence_map_sha256": _sha_bytes(
            replay_bundle.information_equivalence_map_bytes
        ),
        "target_action_roster_sha256": _sha_bytes(replay_bundle.target_action_roster_bytes),
    }
    for key in _E3_SHARED_FIELDS:
        actual[f"{key}_sha256"] = _sha_value(training[key])
    actual["oacs_pre_outcome_decisions_sha256"] = _sha_bytes(
        replay_bundle.oacs_pre_outcome_decision_bytes
    )
    actual["raw_router_pre_outcome_decisions_sha256"] = _sha_bytes(
        replay_bundle.raw_router_pre_outcome_decision_bytes
    )
    for key, value in actual.items():
        if getattr(receipt, key) != value:
            raise ValueError(f"parity receipt mismatch: {key}")
    if receipt.pair_sha256 != _sha_value(actual):
        raise ValueError("parity pair hash mismatch")


def validate_baseline_pre_outcome_readiness(
    roster: MandatoryBaselineRoster,
    readiness: tuple[BaselinePreOutcomeReadinessAuthority, ...],
) -> None:
    if type(roster) is not MandatoryBaselineRoster or type(readiness) is not tuple:
        raise TypeError("baseline readiness inputs have foreign type")
    if any(type(row) is not BaselinePreOutcomeReadinessAuthority for row in readiness):
        raise TypeError("readiness contains foreign row")
    if tuple(row.baseline_id for row in readiness) != _BASELINE_IDS:
        raise ValueError("readiness must have one canonical row per baseline")
    entries = {row.baseline_id: row for row in roster.entries}
    for row in readiness:
        entry = entries[row.baseline_id]
        if (
            row.official_source_spec_sha256 != entry.official_source_spec_sha256
            or row.version_sha256 != entry.version_sha256
        ):
            raise ValueError("readiness source/version does not match roster")


def validate_baseline_decision_run_conformance(
    roster: MandatoryBaselineRoster,
    readiness: tuple[BaselinePreOutcomeReadinessAuthority, ...],
    conformance: tuple[BaselineDecisionRunConformanceReceipt, ...],
) -> None:
    validate_baseline_pre_outcome_readiness(roster, readiness)
    if type(conformance) is not tuple or any(type(row) is not BaselineDecisionRunConformanceReceipt for row in conformance):
        raise TypeError("conformance must be an exact tuple of exact rows")
    ids = tuple(row.baseline_id for row in conformance)
    if ids != tuple(sorted(ids, key=lambda item: item.encode("utf-8"))) or len(ids) != len(set(ids)):
        raise ValueError("conformance rows must be unique and byte sorted")
    required = {
        row.baseline_id
        for row in readiness
        if row.status in {"supported", "inapplicable_predeclared_amendment"}
    }
    if set(ids) != required:
        raise ValueError("conformance cardinality does not match readiness")
    readiness_by_id = {row.baseline_id: row for row in readiness}
    for row in conformance:
        ready = readiness_by_id[row.baseline_id]
        if row.executed_method_id != ready.executed_method_id:
            raise ValueError("conformance executed identity does not match readiness")
        if row.readiness_status_sha256 != ready.status_sha256:
            raise ValueError("conformance does not bind exact readiness")


def _reconstructed_actions(
    registry: SyntheticOpaqueIdentityRegistryV2,
    authority: SyntheticE3TargetActionAuthorityV2,
    shared_roster: SyntheticE1ActionRosterV2,
) -> tuple[dict[str, object], ...]:
    if type(registry) is not SyntheticOpaqueIdentityRegistryV2:
        raise TypeError("E3 registry has foreign type")
    if type(authority) is not SyntheticE3TargetActionAuthorityV2:
        raise TypeError("E3 target authority has foreign type")
    if type(shared_roster) is not SyntheticE1ActionRosterV2:
        raise TypeError("shared E1 action roster has foreign type")
    if (
        authority.opaque_identity_registry_sha256 != registry.registry_sha256
        or shared_roster.opaque_identity_registry_sha256 != registry.registry_sha256
    ):
        raise ValueError("E3 authorities do not bind nested registry")
    authority_target = (authority.site_ref, authority.case_ref, authority.prefix_ref)
    roster_target = (shared_roster.site_ref, shared_roster.case_ref, shared_roster.prefix_ref)
    if authority_target != roster_target:
        raise ValueError("E3 target authority and shared roster target differ")
    packet_ids = tuple(packet for _, packet, _ in authority.packet_slot_bindings)
    if packet_ids != shared_roster.packet_ids:
        raise ValueError("E3 target packet menu differs from shared E1 menu")
    actions: list[dict[str, object]] = [
        {"action_kind": "stop"},
        {"action_kind": "solo"},
    ]
    for slot_id, packet_id, manifest in authority.packet_slot_bindings:
        registry.resolve("slot", slot_id)
        registry.resolve("packet", packet_id)
        if registry.packet_manifest(packet_id) != manifest:
            raise ValueError("E3 target packet manifest differs from registry")
        actions.append(
            {
                "action_kind": "capability_packet",
                "opaque_packet_id": packet_id,
                "opaque_slot_id": slot_id,
            }
        )
    return tuple(actions)


def _validate_e3_contract(contract: E3ComparatorContract) -> None:
    for name, expected_type in (
        ("parity_receipt", PairedInformationParityReceipt),
        ("parity_replay_bundle", SyntheticParityReplayBundle),
        ("opaque_identity_registry", SyntheticOpaqueIdentityRegistryV2),
        ("target_action_authority", SyntheticE3TargetActionAuthorityV2),
        ("shared_e1_action_roster", SyntheticE1ActionRosterV2),
        ("mandatory_roster", MandatoryBaselineRoster),
        ("retrospective_oracle_evaluation", SyntheticRetrospectiveOracleEvaluationV2),
    ):
        if type(getattr(contract, name)) is not expected_type:
            raise TypeError(f"{name} has foreign type")
    _require_hash(contract.analysis_code_sha256, "analysis_code_sha256")
    actions = _reconstructed_actions(
        contract.opaque_identity_registry,
        contract.target_action_authority,
        contract.shared_e1_action_roster,
    )
    validate_paired_information_parity(contract.parity_receipt, contract.parity_replay_bundle)
    parity = _validate_parity_bundle(contract.parity_replay_bundle)
    parent = parity["parent"]
    if tuple(parent[name] for name in ("site_ref", "case_ref", "prefix_ref")) != (
        contract.target_action_authority.site_ref,
        contract.target_action_authority.case_ref,
        contract.target_action_authority.prefix_ref,
    ):
        raise ValueError("E3 source parent target differs from typed authority")
    if parity["actions"] != actions:
        raise ValueError("E3 source parent action roster differs from typed authority")
    for row, binding in zip(
        parent["complete_capability_table"],
        contract.target_action_authority.packet_slot_bindings,
        strict=True,
    ):
        if (
            row["opaque_slot_id"], row["opaque_packet_id"],
            row["complete_bundle_manifest_sha256"],
        ) != binding:
            raise ValueError("E3 capability table differs from typed target binding")

    validate_baseline_pre_outcome_readiness(
        contract.mandatory_roster, contract.baseline_pre_outcome_readiness
    )
    validate_baseline_decision_run_conformance(
        contract.mandatory_roster,
        contract.baseline_pre_outcome_readiness,
        contract.baseline_decision_conformance,
    )
    readiness = {row.baseline_id: row for row in contract.baseline_pre_outcome_readiness}
    roster_sha = _sha_bytes(contract.parity_replay_bundle.target_action_roster_bytes)
    admissible = parity["admissible_action_sha256s"]
    for row in contract.baseline_decision_conformance:
        ready = readiness[row.baseline_id]
        if row.input_action_roster_sha256 != roster_sha:
            raise ValueError("baseline conformance action roster drift")
        projection_spec = _canonical_bytes_value(
            row.baseline_projection_spec_bytes, "baseline_projection_spec_bytes"
        )
        mapping = _validate_projection_spec(projection_spec, require_full=False)
        if row.baseline_projection_spec_bytes_sha256 != ready.parity_projection_sha256:
            raise ValueError("baseline projection does not bind readiness")
        baseline_input = _canonical_bytes_value(row.baseline_input_bytes, "baseline_input_bytes")
        if baseline_input != _projection(parent, mapping):
            raise ValueError("baseline input replay mismatch")
        decision = _canonical_bytes_value(
            row.pre_outcome_decision_bytes, "pre_outcome_decision_bytes"
        )
        _validate_decision(decision, actions, admissible, "baseline decision")
        expected_environment = _sha_value(
            [
                ready.status_sha256,
                ready.version_sha256,
                ready.adapter_code_sha256,
                ready.dependency_environment_lock_sha256,
                ready.parity_projection_sha256,
                ready.executed_method_id,
            ]
        )
        if row.adapter_environment_sha256 != expected_environment:
            raise ValueError("baseline adapter/environment receipt mismatch")

    oracle = contract.retrospective_oracle_evaluation
    if oracle.target_action_authority_sha256 != contract.target_action_authority.authority_sha256:
        raise ValueError("retrospective oracle target authority mismatch")
    if oracle.action_space_tie_rule_sha256 != contract.parity_receipt.action_space_tie_rule_sha256:
        raise ValueError("retrospective oracle tie rule mismatch")
    if oracle.admissibility_sha256 != contract.parity_receipt.admissibility_sha256:
        raise ValueError("retrospective oracle admissibility mismatch")
    if oracle.admissibility_sha256 != _sha_value(parent["admissibility"]):
        raise ValueError("retrospective oracle does not bind parent admissibility")
    table = _canonical_bytes_value(
        oracle.direct_action_value_table_bytes, "direct_action_value_table_bytes"
    )
    if len(table) != len(actions):
        raise ValueError("retrospective oracle table is incomplete")
    values: dict[str, float] = {}
    for row, action in zip(table, actions, strict=True):
        if row["action"] != action:
            raise ValueError("retrospective oracle table action/order mismatch")
        values[_sha_value(action)] = row["blind_direct_value"]
    maximum = max(values[action_hash] for action_hash in admissible)
    expected_hash = next(
        action_hash for action_hash in parity["action_hashes"]
        if action_hash in admissible and values[action_hash] == maximum
    )
    oracle_decision = _canonical_bytes_value(oracle.oracle_decision_bytes, "oracle_decision_bytes")
    _validate_decision(oracle_decision, actions, admissible, "retrospective oracle decision")
    if _sha_value(oracle_decision["action"]) != expected_hash:
        raise ValueError("retrospective oracle decision is not admissible-only argmax/tie")


def require_phase_b_authority(*_args: object, **_kwargs: object) -> None:
    raise NeedsContextError("NEEDS_CONTEXT")


__all__ = (
    "NeedsContextError",
    "SyntheticOpaqueIdentityRegistryV2",
    "AuxiliaryControlPlanV2",
    "AuxiliaryControlConformanceV2",
    "SyntheticE1ActionRosterV2",
    "SyntheticSoloExecutionConformanceV2",
    "SyntheticE3TargetActionAuthorityV2",
    "SyntheticRetrospectiveOracleEvaluationV2",
    "SyntheticTerminalBranch",
    "SyntheticAssignmentCrossoverRecord",
    "SyntheticPairAssignmentClosure",
    "FrozenResidualCapabilityBinding",
    "SyntheticSupportBalanceRecord",
    "SyntheticExecutionConformanceRecord",
    "FrozenE2Pair",
    "SyntheticResidualAbsentControlPair",
    "SyntheticResidualAbsentControlRoster",
    "E2MechanismContract",
    "E2SyntheticSummary",
    "SyntheticParityReplayBundle",
    "PairedInformationParityReceipt",
    "MandatoryBaselineRosterEntry",
    "MandatoryBaselineRoster",
    "BaselinePreOutcomeReadinessAuthority",
    "BaselineDecisionRunConformanceReceipt",
    "E3ComparatorContract",
    "validate_direct_terminal_branches",
    "evaluate_synthetic_e2",
    "validate_paired_information_parity",
    "validate_baseline_pre_outcome_readiness",
    "validate_baseline_decision_run_conformance",
    "require_phase_b_authority",
)
