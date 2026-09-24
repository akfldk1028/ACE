"""Pure Generation-0 canonical-byte contracts for Path-B positive intake."""

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re


MAX_RECORD_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_SAFE_INTEGER = (1 << 53) - 1


class IntakeContractError(ValueError):
    """Raised when untrusted persisted bytes fail the closed contract."""


@dataclass(frozen=True, slots=True)
class ClosedSchema:
    schema_version: str
    version_field: str
    self_hash_field: str
    fields: frozenset[str]
    integer_fields: frozenset[str]
    boolean_fields: frozenset[str]
    array_fields: frozenset[str]
    object_fields: frozenset[str]
    identity_fields: frozenset[str]
    sha256_fields: frozenset[str]


@dataclass(frozen=True, slots=True)
class PersistedRecord:
    schema_version: str
    raw_bytes: bytes
    canonical_body: bytes
    file_sha256: str
    self_sha256: str


SealedRecord = PersistedRecord


_LOCATOR_FIELDS = frozenset(
    {
        "schema_version",
        "locator_version",
        "locator_logical_id",
        "package_logical_id",
        "package_generation",
        "predecessor_locator_sha256",
        "trust_policy_sha256",
        "immutable_store_identity",
        "immutable_object_identity",
        "immutable_object_version",
        "package_root_physical_identity",
        "package_index_member_identity",
        "package_index_file_byte_count",
        "package_index_file_sha256",
        "task7_process_spec_custody_ref_sha256",
        "task5_scientific_parent_custody_ref_sha256s",
        "member_manifest_sha256",
        "pin_approval_manifest_sha256",
        "rotation_current_head_sha256",
        "verifier_challenge_sha256",
        "created_at_utc",
        "expires_at_utc",
        "locator_sha256",
    }
)

LOCATOR_SCHEMA = ClosedSchema(
    schema_version="ace.iclr2027.path_b_positive_intake_locator.v1",
    version_field="locator_version",
    self_hash_field="locator_sha256",
    fields=_LOCATOR_FIELDS,
    integer_fields=frozenset(
        {
            "locator_version",
            "package_generation",
            "package_index_file_byte_count",
        }
    ),
    boolean_fields=frozenset(),
    array_fields=frozenset({"task5_scientific_parent_custody_ref_sha256s"}),
    object_fields=frozenset(),
    identity_fields=frozenset(
        {
            "locator_logical_id",
            "package_logical_id",
            "immutable_store_identity",
            "immutable_object_identity",
            "immutable_object_version",
            "package_root_physical_identity",
            "package_index_member_identity",
            "created_at_utc",
            "expires_at_utc",
        }
    ),
    sha256_fields=frozenset(
        {
            "predecessor_locator_sha256",
            "trust_policy_sha256",
            "package_index_file_sha256",
            "task7_process_spec_custody_ref_sha256",
            "member_manifest_sha256",
            "pin_approval_manifest_sha256",
            "rotation_current_head_sha256",
            "verifier_challenge_sha256",
            "locator_sha256",
        }
    ),
)


_INDEX_FIELDS = frozenset(
    {
        "schema_version",
        "index_version",
        "package_logical_id",
        "package_generation",
        "task7_process_spec_custody_ref",
        "task5_scientific_parent_custody_refs",
        "core_triples",
        "referenced_members",
        "pin_approval_refs",
        "canonical_core_record_count",
        "artifact_count",
        "envelope_count",
        "pin_count",
        "review_count",
        "migration_receipt_pin_sha256",
        "index_sha256",
    }
)

PACKAGE_INDEX_SCHEMA = ClosedSchema(
    schema_version="ace.iclr2027.path_b_positive_intake_package_index.v1",
    version_field="index_version",
    self_hash_field="index_sha256",
    fields=_INDEX_FIELDS,
    integer_fields=frozenset(
        {
            "index_version",
            "package_generation",
            "canonical_core_record_count",
            "artifact_count",
            "envelope_count",
            "pin_count",
            "review_count",
        }
    ),
    boolean_fields=frozenset(),
    array_fields=frozenset(
        {
            "task5_scientific_parent_custody_refs",
            "core_triples",
            "referenced_members",
            "pin_approval_refs",
        }
    ),
    object_fields=frozenset(),
    identity_fields=frozenset(
        {
            "package_logical_id",
            "task7_process_spec_custody_ref",
        }
    ),
    sha256_fields=frozenset(
        {
            "migration_receipt_pin_sha256",
            "index_sha256",
        }
    ),
)


_APPROVAL_FIELDS = frozenset(
    {
        "schema_version",
        "approval_version",
        "approval_role",
        "approver_identity",
        "subject_role",
        "subject_logical_id",
        "subject_file_sha256",
        "decision",
        "approved_at_utc",
        "detached_message_domain",
        "signature_algorithm",
        "signing_key_id",
        "signing_public_key_member_identity",
        "signing_public_key_byte_count",
        "signing_public_key_sha256",
        "detached_signature_member_identity",
        "detached_signature_byte_count",
        "detached_signature_sha256",
        "approval_sha256",
    }
)

EXTERNAL_ROLE_APPROVAL_SCHEMA = ClosedSchema(
    schema_version="ace.iclr2027.path_b_external_role_approval.v1",
    version_field="approval_version",
    self_hash_field="approval_sha256",
    fields=_APPROVAL_FIELDS,
    integer_fields=frozenset(
        {
            "approval_version",
            "signing_public_key_byte_count",
            "detached_signature_byte_count",
        }
    ),
    boolean_fields=frozenset(),
    array_fields=frozenset(),
    object_fields=frozenset(),
    identity_fields=frozenset(
        {
            "approval_role",
            "approver_identity",
            "subject_role",
            "subject_logical_id",
            "decision",
            "approved_at_utc",
            "signature_algorithm",
            "signing_key_id",
            "signing_public_key_member_identity",
            "detached_signature_member_identity",
        }
    ),
    sha256_fields=frozenset(
        {
            "subject_file_sha256",
            "signing_public_key_sha256",
            "detached_signature_sha256",
            "approval_sha256",
        }
    ),
)


_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "result_version",
        "input_refs",
        "input_counts",
        "stage_counters",
        "status",
        "reason_codes",
        "task6_vnext_commission_eligible",
        "source_access_authorized",
        "simulation_authorized",
        "paid_run_authorized",
        "official_result_eligible",
        "empirical_status",
        "result_sha256",
    }
)

RESULT_SCHEMA = ClosedSchema(
    schema_version="ace.iclr2027.path_b_positive_intake_result.v1",
    version_field="result_version",
    self_hash_field="result_sha256",
    fields=_RESULT_FIELDS,
    integer_fields=frozenset({"result_version"}),
    boolean_fields=frozenset(
        {
            "task6_vnext_commission_eligible",
            "source_access_authorized",
            "simulation_authorized",
            "paid_run_authorized",
            "official_result_eligible",
        }
    ),
    array_fields=frozenset({"reason_codes"}),
    object_fields=frozenset({"input_refs", "input_counts", "stage_counters"}),
    identity_fields=frozenset({"status", "empirical_status"}),
    sha256_fields=frozenset({"result_sha256"}),
)


PathBPositiveIntakeLocatorV1 = LOCATOR_SCHEMA
PathBPositiveIntakePackageIndexV1 = PACKAGE_INDEX_SCHEMA
PathBExternalRoleApprovalV1 = EXTERNAL_ROLE_APPROVAL_SCHEMA
PathBPositiveIntakeResultV1 = RESULT_SCHEMA


_CORE_TRIPLE_FIELDS = frozenset(
    {
        "role",
        "artifact_member_identity",
        "artifact_file_byte_count",
        "artifact_file_sha256",
        "envelope_member_identity",
        "envelope_file_byte_count",
        "envelope_file_sha256",
        "pin_member_identity",
        "pin_file_byte_count",
        "pin_file_sha256",
    }
)
_CORE_TRIPLE_IDENTITIES = frozenset(
    {
        "role",
        "artifact_member_identity",
        "envelope_member_identity",
        "pin_member_identity",
    }
)
_CORE_TRIPLE_COUNTS = frozenset(
    {
        "artifact_file_byte_count",
        "envelope_file_byte_count",
        "pin_file_byte_count",
    }
)
_CORE_TRIPLE_HASHES = frozenset(
    {
        "artifact_file_sha256",
        "envelope_file_sha256",
        "pin_file_sha256",
    }
)
_REFERENCED_MEMBER_FIELDS = frozenset(
    {"member_kind", "member_identity", "file_byte_count", "file_sha256"}
)
_REFERENCED_MEMBER_IDENTITIES = frozenset({"member_kind", "member_identity"})
_REFERENCED_MEMBER_COUNTS = frozenset({"file_byte_count"})
_REFERENCED_MEMBER_HASHES = frozenset({"file_sha256"})
_PIN_APPROVAL_REF_FIELDS = frozenset(
    {
        "subject_role",
        "approval_member_identity",
        "approval_file_byte_count",
        "approval_file_sha256",
    }
)
_PIN_APPROVAL_REF_IDENTITIES = frozenset({"subject_role", "approval_member_identity"})
_PIN_APPROVAL_REF_COUNTS = frozenset({"approval_file_byte_count"})
_PIN_APPROVAL_REF_HASHES = frozenset({"approval_file_sha256"})

_APPROVAL_DOMAINS = {
    "responsible_owner": "ACE-ICLR2027-PATH-B-RESPONSIBLE-OWNER-APPROVAL-V1\x00",
    "external_scientist": "ACE-ICLR2027-PATH-B-EXTERNAL-SCIENTIST-APPROVAL-V1\x00",
    "custodian": "ACE-ICLR2027-PATH-B-CUSTODIAN-APPROVAL-V1\x00",
    "artifact_pin": "ACE-ICLR2027-PATH-B-ARTIFACT-PIN-APPROVAL-V1\x00",
    "locator_pin": "ACE-ICLR2027-PATH-B-LOCATOR-PIN-APPROVAL-V1\x00",
}
_CORE_ROLES = (
    "legacy_search_impossibility_declaration",
    "one_thesis_contract",
    "new_upstream_scientific_snapshot",
    "independent_science_migration_review",
    "independent_provenance_migration_review",
    "independent_security_migration_review",
    "provenance_migration_receipt",
)
_REFERENCED_MEMBER_KINDS = frozenset(
    {
        "signing_public_key",
        "detached_signature",
        "verifier_executable",
        "platform_signature",
        "rotation",
        "legacy_search_evidence",
        "responsible_owner_approval",
        "external_scientist_approval",
        "custodian_approval",
        "pin_approval",
        "task7_process_spec_custody",
        "task5_scientific_parent_custody",
    }
)
_APPROVAL_SUBJECT_ROLES = frozenset((*_CORE_ROLES, "path_b_positive_intake_locator"))

_UTC_PATTERN = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$"
)
_WINDOWS_DEVICE_STEMS = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
_SHORT_NAME_ALIAS = re.compile(r"~[1-9][0-9]*(?:[.]|$)", re.IGNORECASE)

_RESULT_REASON_FAMILIES = frozenset(
    {
        "approval_authentication_failed",
        "canonical_file_encoding_failed",
        "core_record_census_mismatch",
        "cryptographic_signature_failed",
        "external_root_missing",
        "filesystem_identity_failed",
        "immutable_member_census_mismatch",
        "locator_authentication_failed",
        "package_index_binding_failed",
        "process_spec_custody_failed",
        "producer_reviewer_authority_overlap",
        "replay_or_freshness_failed",
        "scientific_contract_drift",
        "task5_parent_custody_failed",
        "verifier_package_or_rotation_failed",
    }
)


def _fail(reason: str) -> None:
    raise IntakeContractError(reason)


def _parse_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail("canonical_file_encoding_failed")
        result[key] = value
    return result


def _parse_integer(token: str) -> int:
    value = int(token)
    if abs(value) > MAX_SAFE_INTEGER:
        _fail("canonical_file_encoding_failed")
    if value == 0 and token.startswith("-"):
        _fail("canonical_file_encoding_failed")
    return value


def _parse_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        _fail("canonical_file_encoding_failed")
    if value == 0.0 and token.startswith("-"):
        _fail("canonical_file_encoding_failed")
    return value


def _reject_nonfinite(_token: str) -> object:
    _fail("canonical_file_encoding_failed")


def _canonical_json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return text.encode("utf-8")
    except (TypeError, UnicodeError, ValueError) as error:
        raise IntakeContractError("canonical_file_encoding_failed") from error


def _visible_ascii(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and all(0x21 <= ord(character) <= 0x7E for character in value)
    )


def _sha256_text(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_utc(value: object) -> bool:
    if type(value) is not str:
        return False
    matched = _UTC_PATTERN.fullmatch(value)
    if matched is None:
        return False
    year = int(matched.group("year"))
    month = int(matched.group("month"))
    day = int(matched.group("day"))
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_in_month = (
        31,
        29 if leap else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    )
    return day <= days_in_month[month - 1]


def _safe_relative_member_identity(value: object) -> bool:
    if not _visible_ascii(value):
        return False
    if (
        value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(character in value for character in '<>"|?*')
    ):
        return False
    segments = value.split("/")
    if any(
        not segment or segment in {".", ".."} or segment.endswith((".", " "))
        for segment in segments
    ):
        return False
    for segment in segments:
        stem = segment.partition(".")[0]
        stem = stem.upper()
        if stem in _WINDOWS_DEVICE_STEMS or _SHORT_NAME_ALIAS.search(segment):
            return False
    return True


def _require_unique_occurrences(
    values: list[str],
    *,
    casefold: bool = False,
) -> None:
    compared = [value.casefold() for value in values] if casefold else values
    if len(compared) != len(set(compared)):
        _fail("canonical_file_encoding_failed")


def _validate_tree(value: object, depth: int = 1) -> None:
    if depth > MAX_JSON_DEPTH:
        _fail("canonical_file_encoding_failed")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail("canonical_file_encoding_failed")
            _validate_tree(item, depth + 1)
        return
    if type(value) is list:
        for item in value:
            _validate_tree(item, depth + 1)
        return
    if type(value) is str or type(value) is bool:
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_INTEGER:
            _fail("canonical_file_encoding_failed")
        return
    if type(value) is float:
        if not math.isfinite(value) or (value == 0.0 and math.copysign(1.0, value) < 0):
            _fail("canonical_file_encoding_failed")
        return
    _fail("canonical_file_encoding_failed")


def _require_integer(value: object) -> None:
    if type(value) is not int or value < 0 or value > MAX_SAFE_INTEGER:
        _fail("canonical_file_encoding_failed")


def _require_positive_integer(value: object) -> None:
    if type(value) is not int or value <= 0 or value > MAX_SAFE_INTEGER:
        _fail("canonical_file_encoding_failed")


def _require_exact_item(
    value: object,
    fields: frozenset[str],
    identity_fields: frozenset[str],
    count_fields: frozenset[str],
    sha256_fields: frozenset[str],
) -> None:
    if type(value) is not dict or frozenset(value) != fields:
        _fail("canonical_file_encoding_failed")
    for field in identity_fields:
        if not _visible_ascii(value[field]):
            _fail("canonical_file_encoding_failed")
    for field in count_fields:
        _require_positive_integer(value[field])
    for field in sha256_fields:
        if not _sha256_text(value[field]):
            _fail("canonical_file_encoding_failed")


def _require_string_map(value: object) -> None:
    if type(value) is not dict:
        _fail("canonical_file_encoding_failed")
    for key, item in value.items():
        if not _visible_ascii(key) or not _visible_ascii(item):
            _fail("canonical_file_encoding_failed")


def _require_counter_map(value: object) -> None:
    if type(value) is not dict:
        _fail("canonical_file_encoding_failed")
    for key, item in value.items():
        if not _visible_ascii(key):
            _fail("canonical_file_encoding_failed")
        _require_integer(item)


def _validate_index(payload: dict[str, object]) -> None:
    parents = payload["task5_scientific_parent_custody_refs"]
    if type(parents) is not list or len(parents) != 3:
        _fail("canonical_file_encoding_failed")
    if any(not _visible_ascii(item) for item in parents):
        _fail("canonical_file_encoding_failed")
    if len(parents) != len(set(parents)):
        _fail("canonical_file_encoding_failed")

    for field, expected in (
        ("canonical_core_record_count", 21),
        ("artifact_count", 7),
        ("envelope_count", 7),
        ("pin_count", 7),
        ("review_count", 3),
    ):
        if payload[field] != expected:
            _fail("canonical_file_encoding_failed")
    _require_positive_integer(payload["package_generation"])

    core_triples = payload["core_triples"]
    if type(core_triples) is not list or len(core_triples) != 7:
        _fail("canonical_file_encoding_failed")
    for item in core_triples:
        _require_exact_item(
            item,
            _CORE_TRIPLE_FIELDS,
            _CORE_TRIPLE_IDENTITIES,
            _CORE_TRIPLE_COUNTS,
            _CORE_TRIPLE_HASHES,
        )
        for field in (
            "artifact_member_identity",
            "envelope_member_identity",
            "pin_member_identity",
        ):
            if not _safe_relative_member_identity(item[field]):
                _fail("canonical_file_encoding_failed")
    if tuple(item["role"] for item in core_triples) != _CORE_ROLES:
        _fail("canonical_file_encoding_failed")

    referenced_members = payload["referenced_members"]
    if type(referenced_members) is not list or not referenced_members:
        _fail("canonical_file_encoding_failed")
    for item in referenced_members:
        _require_exact_item(
            item,
            _REFERENCED_MEMBER_FIELDS,
            _REFERENCED_MEMBER_IDENTITIES,
            _REFERENCED_MEMBER_COUNTS,
            _REFERENCED_MEMBER_HASHES,
        )
        if not _safe_relative_member_identity(item["member_identity"]):
            _fail("canonical_file_encoding_failed")
        if item["member_kind"] not in _REFERENCED_MEMBER_KINDS:
            _fail("canonical_file_encoding_failed")

    pin_approval_refs = payload["pin_approval_refs"]
    if type(pin_approval_refs) is not list or len(pin_approval_refs) != 7:
        _fail("canonical_file_encoding_failed")
    for item in pin_approval_refs:
        _require_exact_item(
            item,
            _PIN_APPROVAL_REF_FIELDS,
            _PIN_APPROVAL_REF_IDENTITIES,
            _PIN_APPROVAL_REF_COUNTS,
            _PIN_APPROVAL_REF_HASHES,
        )
        if item["subject_role"] not in _CORE_ROLES:
            _fail("canonical_file_encoding_failed")
        if not _safe_relative_member_identity(item["approval_member_identity"]):
            _fail("canonical_file_encoding_failed")

    if tuple(item["subject_role"] for item in pin_approval_refs) != _CORE_ROLES:
        _fail("canonical_file_encoding_failed")

    core_member_identities = [
        value
        for item in core_triples
        for value in (
            item["artifact_member_identity"],
            item["envelope_member_identity"],
            item["pin_member_identity"],
        )
    ]
    referenced_member_identities = [
        item["member_identity"] for item in referenced_members
    ]
    _require_unique_occurrences(core_member_identities, casefold=True)
    _require_unique_occurrences(referenced_member_identities, casefold=True)
    _require_unique_occurrences(
        core_member_identities + referenced_member_identities,
        casefold=True,
    )

    core_member_hashes = [
        value
        for item in core_triples
        for value in (
            item["artifact_file_sha256"],
            item["envelope_file_sha256"],
            item["pin_file_sha256"],
        )
    ]
    referenced_member_hashes = [item["file_sha256"] for item in referenced_members]
    _require_unique_occurrences(core_member_hashes)
    _require_unique_occurrences(referenced_member_hashes)
    _require_unique_occurrences(core_member_hashes + referenced_member_hashes)

    pin_approval_members = [
        (
            item["member_identity"],
            item["file_byte_count"],
            item["file_sha256"],
        )
        for item in referenced_members
        if item["member_kind"] == "pin_approval"
    ]
    pin_approval_references = [
        (
            item["approval_member_identity"],
            item["approval_file_byte_count"],
            item["approval_file_sha256"],
        )
        for item in pin_approval_refs
    ]
    if (
        len(pin_approval_members) != 7
        or len(pin_approval_references) != len(set(pin_approval_references))
        or any(
            pin_approval_members.count(reference) != 1
            for reference in pin_approval_references
        )
        or any(
            pin_approval_references.count(member) != 1
            for member in pin_approval_members
        )
    ):
        _fail("canonical_file_encoding_failed")


def _validate_approval(payload: dict[str, object]) -> None:
    role = payload["approval_role"]
    if type(role) is not str or role not in _APPROVAL_DOMAINS:
        _fail("canonical_file_encoding_failed")
    if payload["subject_role"] not in _APPROVAL_SUBJECT_ROLES:
        _fail("canonical_file_encoding_failed")
    if (
        role == "locator_pin"
        and payload["subject_role"] != "path_b_positive_intake_locator"
    ):
        _fail("canonical_file_encoding_failed")
    if role == "artifact_pin" and payload["subject_role"] not in _CORE_ROLES:
        _fail("canonical_file_encoding_failed")
    if payload["decision"] != "approve":
        _fail("canonical_file_encoding_failed")
    if payload["detached_message_domain"] != _APPROVAL_DOMAINS[role]:
        _fail("canonical_file_encoding_failed")
    if payload["signature_algorithm"] != "Ed25519":
        _fail("canonical_file_encoding_failed")
    if payload["signing_public_key_byte_count"] != 32:
        _fail("canonical_file_encoding_failed")
    if payload["detached_signature_byte_count"] != 64:
        _fail("canonical_file_encoding_failed")
    if not _canonical_utc(payload["approved_at_utc"]):
        _fail("canonical_file_encoding_failed")
    for field in (
        "signing_public_key_member_identity",
        "detached_signature_member_identity",
    ):
        if not _safe_relative_member_identity(payload[field]):
            _fail("canonical_file_encoding_failed")


def _validate_result(payload: dict[str, object]) -> None:
    _require_string_map(payload["input_refs"])
    _require_counter_map(payload["input_counts"])
    _require_counter_map(payload["stage_counters"])
    if payload["input_refs"] or payload["input_counts"] or payload["stage_counters"]:
        _fail("canonical_file_encoding_failed")
    reasons = payload["reason_codes"]
    if type(reasons) is not list:
        _fail("canonical_file_encoding_failed")
    if any(not _visible_ascii(reason) for reason in reasons):
        _fail("canonical_file_encoding_failed")
    if any(reason not in _RESULT_REASON_FAMILIES for reason in reasons):
        _fail("canonical_file_encoding_failed")
    if len(reasons) != len(set(reasons)):
        _fail("canonical_file_encoding_failed")
    if reasons != sorted(reasons, key=lambda reason: reason.encode("ascii")):
        _fail("canonical_file_encoding_failed")

    if payload["status"] != "no_go":
        _fail("canonical_file_encoding_failed")
    if payload["empirical_status"] != "no_go_needs_context":
        _fail("canonical_file_encoding_failed")
    for field in (
        "task6_vnext_commission_eligible",
        "source_access_authorized",
        "simulation_authorized",
        "paid_run_authorized",
        "official_result_eligible",
    ):
        if payload[field] is not False:
            _fail("canonical_file_encoding_failed")


def _validate_schema_values(payload: dict[str, object], schema: ClosedSchema) -> None:
    if frozenset(payload) != schema.fields:
        _fail("canonical_file_encoding_failed")
    if payload["schema_version"] != schema.schema_version:
        _fail("canonical_file_encoding_failed")
    if (
        type(payload[schema.version_field]) is not int
        or payload[schema.version_field] != 1
    ):
        _fail("canonical_file_encoding_failed")

    for field in schema.integer_fields:
        _require_integer(payload[field])
    for field in schema.boolean_fields:
        if type(payload[field]) is not bool:
            _fail("canonical_file_encoding_failed")
    for field in schema.array_fields:
        if type(payload[field]) is not list:
            _fail("canonical_file_encoding_failed")
    for field in schema.object_fields:
        if type(payload[field]) is not dict:
            _fail("canonical_file_encoding_failed")
    for field in schema.identity_fields:
        if not _visible_ascii(payload[field]):
            _fail("canonical_file_encoding_failed")
    for field in schema.sha256_fields:
        if not _sha256_text(payload[field]):
            _fail("canonical_file_encoding_failed")

    if schema is LOCATOR_SCHEMA:
        parents = payload["task5_scientific_parent_custody_ref_sha256s"]
        if type(parents) is not list or len(parents) != 3:
            _fail("canonical_file_encoding_failed")
        if any(not _sha256_text(item) for item in parents):
            _fail("canonical_file_encoding_failed")
        _require_unique_occurrences(parents)
        _require_positive_integer(payload["package_generation"])
        _require_positive_integer(payload["package_index_file_byte_count"])
        if not _safe_relative_member_identity(payload["package_index_member_identity"]):
            _fail("canonical_file_encoding_failed")
        created = payload["created_at_utc"]
        expires = payload["expires_at_utc"]
        if not _canonical_utc(created) or not _canonical_utc(expires):
            _fail("canonical_file_encoding_failed")
        if created >= expires:
            _fail("canonical_file_encoding_failed")
    elif schema is PACKAGE_INDEX_SCHEMA:
        _validate_index(payload)
    elif schema is EXTERNAL_ROLE_APPROVAL_SCHEMA:
        _validate_approval(payload)
    elif schema is RESULT_SCHEMA:
        _validate_result(payload)


def _decode_canonical_record(raw: bytes) -> tuple[bytes, dict[str, object]]:
    if type(raw) is not bytes:
        _fail("canonical_file_encoding_failed")
    if not raw or len(raw) > MAX_RECORD_BYTES:
        _fail("canonical_file_encoding_failed")
    if raw.startswith(b"\xef\xbb\xbf"):
        _fail("canonical_file_encoding_failed")
    if raw.count(b"\n") != 1 or raw[-1:] != b"\n" or b"\r" in raw:
        _fail("canonical_file_encoding_failed")

    canonical_body = raw[:-1]
    try:
        text = canonical_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise IntakeContractError("canonical_file_encoding_failed") from error
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_parse_pairs,
            parse_constant=_reject_nonfinite,
            parse_int=_parse_integer,
            parse_float=_parse_float,
        )
    except IntakeContractError:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError, TypeError) as error:
        raise IntakeContractError("canonical_file_encoding_failed") from error

    if type(payload) is not dict:
        _fail("canonical_file_encoding_failed")
    _validate_tree(payload)
    if _canonical_json(payload) != canonical_body:
        _fail("canonical_file_encoding_failed")
    return canonical_body, payload


def parse_persisted_record(raw: bytes, schema: ClosedSchema) -> PersistedRecord:
    """Parse one exact canonical LF-terminated record without performing I/O."""

    if type(schema) is not ClosedSchema:
        _fail("canonical_file_encoding_failed")
    if not (
        schema is LOCATOR_SCHEMA
        or schema is PACKAGE_INDEX_SCHEMA
        or schema is EXTERNAL_ROLE_APPROVAL_SCHEMA
        or schema is RESULT_SCHEMA
    ):
        _fail("canonical_file_encoding_failed")
    canonical_body, payload = _decode_canonical_record(raw)
    _validate_schema_values(payload, schema)

    self_hash_body = dict(payload)
    observed_self_hash = self_hash_body.pop(schema.self_hash_field)
    expected_self_hash = sha256(_canonical_json(self_hash_body)).hexdigest()
    if observed_self_hash != expected_self_hash:
        _fail("canonical_file_encoding_failed")

    return PersistedRecord(
        schema_version=schema.schema_version,
        raw_bytes=raw,
        canonical_body=canonical_body,
        file_sha256=sha256(raw).hexdigest(),
        self_sha256=expected_self_hash,
    )


def parse_self_hashed_record(
    raw: bytes,
    expected_schema_version: str,
    self_hash_field: str,
) -> PersistedRecord:
    """Parse structural canonical bytes without claiming semantic authority."""

    if not _visible_ascii(expected_schema_version) or not _visible_ascii(
        self_hash_field
    ):
        _fail("canonical_file_encoding_failed")
    canonical_body, payload = _decode_canonical_record(raw)
    try:
        observed_schema_version = payload["schema_version"]
    except KeyError as error:
        raise IntakeContractError("canonical_file_encoding_failed") from error
    if observed_schema_version != expected_schema_version:
        _fail("canonical_file_encoding_failed")
    self_hash_body = dict(payload)
    try:
        observed_self_hash = self_hash_body.pop(self_hash_field)
    except KeyError as error:
        raise IntakeContractError("canonical_file_encoding_failed") from error
    if not _sha256_text(observed_self_hash):
        _fail("canonical_file_encoding_failed")
    expected_self_hash = sha256(_canonical_json(self_hash_body)).hexdigest()
    if observed_self_hash != expected_self_hash:
        _fail("canonical_file_encoding_failed")
    return PersistedRecord(
        schema_version=expected_schema_version,
        raw_bytes=raw,
        canonical_body=canonical_body,
        file_sha256=sha256(raw).hexdigest(),
        self_sha256=expected_self_hash,
    )
