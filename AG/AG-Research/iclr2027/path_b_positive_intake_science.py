"""Pure scientific equality and relationship checks for Generation-0 intake.

The views in this module contain only already-parsed, in-memory observations.
They cannot locate, open, authenticate, or promote an external package.
"""

from dataclasses import dataclass
from hashlib import sha256
from json import loads

from iclr2027.path_b_positive_intake_contract import (
    EXTERNAL_ROLE_APPROVAL_SCHEMA,
    IntakeContractError,
    PACKAGE_INDEX_SCHEMA,
    PersistedRecord,
    parse_persisted_record,
    parse_self_hashed_record,
)


_PACKAGE_INDEX_SCHEMA = "ace.iclr2027.path_b_positive_intake_package_index.v1"
_ENVELOPE_SCHEMA = "ace.iclr2027.external_canonical_signature_envelope.vnext"
_PIN_SCHEMA = "ace.iclr2027.external_vnext_artifact_pin.vnext"
_TASK7_PROCESS_SPEC_SHA256 = (
    "9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54"
)
_TASK7_PROCESS_SPEC_BYTE_COUNT = 71_589
_TASK5_SCIENTIFIC_PARENT_SHA256S = (
    "2809048fa71d0f2458db13f7590c61f0f28674f2195c3d8690a45193df517299",
    "8d2f27d2fb9e6901d7bfed90407a25f8c714d23fe9d2f511a469494e272054ee",
    "8d98a17ee57b1a254d4f651d74b44b696ec022e3822daea1b8a3f25036060cc8",
)
_TASK5_SCIENTIFIC_PARENT_BYTE_COUNTS = (63_630, 62_828, 90_780)
_FROZEN_ROLES = (
    "legacy_search_impossibility_declaration",
    "one_thesis_contract",
    "new_upstream_scientific_snapshot",
    "independent_science_migration_review",
    "independent_provenance_migration_review",
    "independent_security_migration_review",
    "provenance_migration_receipt",
)
_FROZEN_ROLE_SCHEMAS = (
    "ace.iclr2027.legacy_search_impossibility_declaration.vnext",
    "ace.iclr2027.one_thesis_contract.vnext",
    "ace.iclr2027.new_upstream_scientific_snapshot.vnext",
    "ace.iclr2027.independent_migration_review.vnext",
    "ace.iclr2027.independent_migration_review.vnext",
    "ace.iclr2027.independent_migration_review.vnext",
    "ace.iclr2027.provenance_migration_receipt.vnext",
)
_FROZEN_THESIS_SCALARS = (
    ("thesis_id", "residual_obligation_x_actually_executed_complete_bundle"),
    (
        "treatment_definition",
        "residual_obligation_status_x_actually_executed_complete_bundle",
    ),
    ("architecture_domain_role", "flagship_primary_domain"),
    ("jci_domain_role", "independent_e2_e3_replication_no_pooling"),
    (
        "architecture_ontology_clause",
        "architecture_site_cluster_flagship_residual_obligation_x_actually_executed_complete_bundle",
    ),
    (
        "jci_ontology_clause",
        "jci_project_cluster_independent_e2_e3_resource_obligation_replication_no_pooling",
    ),
    ("cross_domain_pooling", "forbidden"),
    ("cats_role", "negative_motivation_and_baseline_only"),
    ("e1_role", "predictive_noncausal_nonprimary_support"),
    ("e2_role", "randomized_executed_complete_bundle_primary_mechanism"),
    (
        "e2_primary_endpoint",
        "blind_terminal_obligation_closure_quality_present_high_minus_low_minus_absent_high_minus_low",
    ),
    ("e3_role", "equal_information_policy_consequence_conditional_on_e2"),
    ("e3_primary_comparator", "full_parity_raw_router"),
    (
        "retrospective_oracle_role",
        "post_outcome_descriptive_upper_bound_separate_not_deployable",
    ),
    ("e4_role", "fresh_downstream_deployable_frontier_after_e1_e2_e3"),
)
_FROZEN_POLICY_IDS = (
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
_FROZEN_ENDPOINT_HIERARCHY = (
    "e2_randomized_executed_bundle_primary",
    "e3_equal_information_oacs_vs_full_parity_raw_router_conditional_on_e2",
    "e4_fresh_downstream_frontier_conditional_on_e1_e2_e3",
    "e1_predictive_support_noncausal_nonprimary",
)
_FROZEN_KILL_CHAIN = (
    "e1_failure_removes_predictive_support_and_blocks_e1_dependent_e4_without_rescuing_e2",
    "architecture_e2_nonpositive_nonestimable_unsupported_or_noncompliant_kills_causal_mechanism_and_iclr_main_oacs_thesis",
    "architecture_e3_null_or_parity_invalid_after_positive_e2_kills_oacs_method_and_iclr_main_claim",
    "architecture_failure_never_reclassified_as_jci_only_main_claim_and_no_cross_ontology_pooling_or_rescue",
    "only_narrower_jci_descriptive_and_randomized_executed_bundle_effect_reporting_may_remain_after_architecture_main_claim_kill",
    "architecture_main_claim_kill_forbids_flagship_replication_cross_domain_mechanism_main_and_oacs_main_survival",
    "jci_e2_nonpositive_nonestimable_unsupported_or_noncompliant_kills_causal_mechanism_and_iclr_main_oacs_thesis",
    "jci_e3_null_or_parity_invalid_after_positive_e2_kills_oacs_method_and_iclr_main_claim",
    "jci_failure_never_reclassified_as_generalization_only_and_no_cross_ontology_pooling_or_rescue",
    "only_narrower_architecture_descriptive_and_executed_bundle_effect_reporting_may_remain",
    "e1_e2_e3_pass_e4_failure_kills_deployable_frontier_claim",
)


@dataclass(frozen=True, slots=True)
class ScientificContractView:
    legacy_continuity: bool
    legacy_equivalence: bool
    thesis_scalars: tuple[tuple[str, str], ...]
    policy_ids: tuple[str, ...]
    endpoint_hierarchy: tuple[str, ...]
    kill_chain: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReferencedMemberView:
    member_kind: str
    member_identity: str
    file_byte_count: int
    file_sha256: str


@dataclass(frozen=True, slots=True)
class PinApprovalRefView:
    subject_role: str
    approval_member_identity: str
    approval_file_byte_count: int
    approval_file_sha256: str


@dataclass(frozen=True, slots=True)
class LegacyEvidenceView:
    member_identity: str
    record: PersistedRecord


@dataclass(frozen=True, slots=True)
class CustodyObjectView:
    member_identity: str
    file_byte_count: int
    file_sha256: str


@dataclass(frozen=True, slots=True)
class ApprovalRecordView:
    approval_member_identity: str
    approval_file_byte_count: int
    approval_file_sha256: str
    approval_record: PersistedRecord
    approval_version: int
    approval_role: str
    approver_identity: str
    subject_role: str
    subject_logical_id: str
    subject_file_sha256: str
    decision: str
    approved_at_utc: str
    detached_message_domain: str
    signature_algorithm: str
    signing_key_id: str
    signing_public_key_member_identity: str
    signing_public_key_byte_count: int
    signing_public_key_sha256: str
    detached_signature_member_identity: str
    detached_signature_byte_count: int
    detached_signature_sha256: str


@dataclass(frozen=True, slots=True)
class RoleAuthorityView:
    actor_identity: str
    producer_package_identity: str
    signing_key_id: str
    signing_public_key_member_identity: str
    signing_public_key_byte_count: int
    signing_public_key_sha256: str
    detached_signature_member_identity: str
    detached_signature_byte_count: int
    detached_signature_sha256: str
    verifier_package_identity: str
    verifier_executable_member_identity: str
    verifier_executable_byte_count: int
    verifier_executable_sha256: str
    platform_signature_member_identity: str
    platform_signature_byte_count: int
    platform_signature_sha256: str
    rotation_member_identity: str
    rotation_byte_count: int
    rotation_sha256: str
    approval_member_identity: str
    approval_file_byte_count: int
    approval_sha256: str


@dataclass(frozen=True, slots=True)
class CoreTripleView:
    role: str
    artifact_schema_version: str
    artifact_version: int
    artifact_logical_id: str
    envelope_logical_id: str
    pin_logical_id: str
    artifact_member_identity: str
    envelope_member_identity: str
    pin_member_identity: str
    artifact: PersistedRecord
    envelope: PersistedRecord
    pin: PersistedRecord
    predecessor_envelope_sha256s: tuple[str, ...]
    predecessor_pin_sha256s: tuple[str, ...]
    authority: RoleAuthorityView


@dataclass(frozen=True, slots=True)
class ReceiptJoinView:
    role: str
    artifact_file_sha256: str
    artifact_sha256: str
    envelope_file_sha256: str
    envelope_sha256: str
    pin_file_sha256: str
    pin_sha256: str


@dataclass(frozen=True, slots=True)
class PackageIndexMetadata:
    index_record: PersistedRecord
    index_version: int
    package_generation: int
    package_logical_id: str
    task7_process_spec_custody_ref_sha256: str
    task5_scientific_parent_custody_ref_sha256s: tuple[str, ...]
    core_roles: tuple[str, ...]
    referenced_members: tuple[ReferencedMemberView, ...]
    pin_approval_refs: tuple[PinApprovalRefView, ...]
    canonical_core_record_count: int
    artifact_count: int
    envelope_count: int
    pin_count: int
    review_count: int
    migration_receipt_pin_sha256: str
    responsible_owner_identity: str
    external_scientist_identity: str
    custodian_identities: tuple[str, ...]
    responsible_owner_approval_member_identity: str
    responsible_owner_approval_sha256: str
    external_scientist_approval_member_identity: str
    external_scientist_approval_sha256: str
    custodian_approval_member_identities: tuple[str, ...]
    custodian_approval_sha256s: tuple[str, ...]
    legacy_search_evidence: tuple[LegacyEvidenceView, ...]
    task7_process_spec_custody: CustodyObjectView
    task5_scientific_parent_custodies: tuple[CustodyObjectView, ...]
    responsible_owner_approval: ApprovalRecordView
    external_scientist_approval: ApprovalRecordView
    custodian_approvals: tuple[ApprovalRecordView, ...]
    artifact_pin_approvals: tuple[ApprovalRecordView, ...]


@dataclass(frozen=True, slots=True)
class SyntheticPackageView:
    package_index: PackageIndexMetadata
    core_triples: tuple[CoreTripleView, ...]
    scientific_contract: ScientificContractView
    receipt_predecessor_join: tuple[ReceiptJoinView, ...]


def _fail(reason: str) -> None:
    raise IntakeContractError(reason)


def require_exact_tuple(
    name: str,
    observed: tuple[object, ...],
    expected: tuple[object, ...],
) -> None:
    if type(observed) is not tuple or observed != expected:
        _fail(f"{name}_drift")


def require_globally_distinct(name: str, occurrences: tuple[str, ...]) -> None:
    if type(occurrences) is not tuple:
        _fail(f"{name}_overlap")
    if any(type(value) is not str for value in occurrences):
        _fail(f"{name}_overlap")
    if len(occurrences) != len(set(occurrences)):
        _fail(f"{name}_overlap")


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


def _require_visible_ascii(name: str, values: tuple[object, ...]) -> None:
    if any(not _visible_ascii(value) for value in values):
        _fail(f"{name}_drift")


def _require_sha256(name: str, values: tuple[object, ...]) -> None:
    if any(not _sha256_text(value) for value in values):
        _fail(f"{name}_drift")


def _require_package_view(package: SyntheticPackageView) -> None:
    if type(package) is not SyntheticPackageView:
        _fail("synthetic_package_view_drift")
    if type(package.package_index) is not PackageIndexMetadata:
        _fail("package_index_metadata_drift")
    if type(package.scientific_contract) is not ScientificContractView:
        _fail("scientific_contract_view_drift")
    if type(package.core_triples) is not tuple or any(
        type(triple) is not CoreTripleView for triple in package.core_triples
    ):
        _fail("core_triple_view_drift")
    if type(package.receipt_predecessor_join) is not tuple or any(
        type(join) is not ReceiptJoinView for join in package.receipt_predecessor_join
    ):
        _fail("receipt_predecessor_join_drift")


def _record_self_hash_field(schema: str) -> str:
    if schema == "ace.iclr2027.legacy_search_impossibility_declaration.vnext":
        return "declaration_sha256"
    if schema == "ace.iclr2027.one_thesis_contract.vnext":
        return "contract_sha256"
    if schema == "ace.iclr2027.new_upstream_scientific_snapshot.vnext":
        return "snapshot_sha256"
    if schema == "ace.iclr2027.independent_migration_review.vnext":
        return "review_sha256"
    if schema == "ace.iclr2027.provenance_migration_receipt.vnext":
        return "receipt_sha256"
    if schema == _ENVELOPE_SCHEMA:
        return "envelope_sha256"
    if schema == _PIN_SCHEMA:
        return "pin_sha256"
    _fail("core_record_schema_drift")


def _require_record(
    record: PersistedRecord,
    schema: str,
    name: str,
    self_hash_field: str | None = None,
) -> None:
    if type(record) is not PersistedRecord or record.schema_version != schema:
        _fail(f"{name}_schema_drift")
    if (
        type(record.raw_bytes) is not bytes
        or not record.raw_bytes
        or record.raw_bytes.count(b"\n") != 1
        or not record.raw_bytes.endswith(b"\n")
        or b"\r" in record.raw_bytes
        or type(record.canonical_body) is not bytes
        or record.canonical_body != record.raw_bytes[:-1]
        or record.file_sha256 != sha256(record.raw_bytes).hexdigest()
        or not _sha256_text(record.self_sha256)
    ):
        _fail(f"{name}_byte_binding_drift")
    if self_hash_field is not None:
        parsed = parse_self_hashed_record(
            record.raw_bytes,
            schema,
            self_hash_field,
        )
        if parsed != record:
            _fail(f"{name}_byte_binding_drift")


def _validate_role_authority(authority: RoleAuthorityView) -> None:
    _require_visible_ascii(
        "role_authority_identity",
        (
            authority.actor_identity,
            authority.producer_package_identity,
            authority.signing_key_id,
            authority.signing_public_key_member_identity,
            authority.detached_signature_member_identity,
            authority.verifier_package_identity,
            authority.verifier_executable_member_identity,
            authority.platform_signature_member_identity,
            authority.rotation_member_identity,
            authority.approval_member_identity,
        ),
    )
    _require_sha256(
        "role_authority_sha256",
        (
            authority.signing_public_key_sha256,
            authority.detached_signature_sha256,
            authority.verifier_executable_sha256,
            authority.platform_signature_sha256,
            authority.rotation_sha256,
            authority.approval_sha256,
        ),
    )
    member_counts = (
        authority.signing_public_key_byte_count,
        authority.detached_signature_byte_count,
        authority.verifier_executable_byte_count,
        authority.platform_signature_byte_count,
        authority.rotation_byte_count,
        authority.approval_file_byte_count,
    )
    if any(type(value) is not int or value <= 0 for value in member_counts):
        _fail("role_authority_byte_count_drift")
    if member_counts[:2] != (32, 64):
        _fail("role_authority_signature_byte_count_drift")


def _validate_referenced_member(member: ReferencedMemberView) -> None:
    if type(member) is not ReferencedMemberView:
        _fail("referenced_member_view_drift")
    _require_visible_ascii(
        "referenced_member_identity",
        (member.member_kind, member.member_identity),
    )
    if type(member.file_byte_count) is not int or member.file_byte_count <= 0:
        _fail("referenced_member_byte_count_drift")
    _require_sha256("referenced_member_sha256", (member.file_sha256,))


def _validate_pin_approval_ref(pin_ref: PinApprovalRefView) -> None:
    if type(pin_ref) is not PinApprovalRefView:
        _fail("pin_approval_ref_view_drift")
    _require_visible_ascii(
        "pin_approval_ref_identity",
        (pin_ref.subject_role, pin_ref.approval_member_identity),
    )
    if (
        type(pin_ref.approval_file_byte_count) is not int
        or pin_ref.approval_file_byte_count <= 0
    ):
        _fail("pin_approval_ref_byte_count_drift")
    _require_sha256(
        "pin_approval_ref_sha256",
        (pin_ref.approval_file_sha256,),
    )


def _validate_legacy_evidence(evidence: LegacyEvidenceView) -> None:
    if type(evidence) is not LegacyEvidenceView:
        _fail("legacy_evidence_view_drift")
    _require_visible_ascii(
        "legacy_evidence_identity",
        (evidence.member_identity,),
    )
    if type(evidence.record) is not PersistedRecord or not _visible_ascii(
        evidence.record.schema_version
    ):
        _fail("legacy_evidence_schema_drift")
    _require_record(
        evidence.record,
        evidence.record.schema_version,
        "legacy_evidence",
    )


def _validate_custody_object(custody: CustodyObjectView, name: str) -> None:
    if type(custody) is not CustodyObjectView:
        _fail(f"{name}_view_drift")
    _require_visible_ascii(f"{name}_identity", (custody.member_identity,))
    if type(custody.file_byte_count) is not int or custody.file_byte_count <= 0:
        _fail(f"{name}_byte_count_drift")
    _require_sha256(f"{name}_sha256", (custody.file_sha256,))


def _validate_approval_record(
    approval: ApprovalRecordView,
    expected_role: str,
    expected_approver_identity: str | None,
    expected_pin_subject: tuple[str, str, str] | None,
) -> None:
    if type(approval) is not ApprovalRecordView:
        _fail("approval_record_view_drift")
    _require_visible_ascii(
        "approval_record_identity",
        (
            approval.approval_member_identity,
            approval.approval_role,
            approval.approver_identity,
            approval.subject_role,
            approval.subject_logical_id,
            approval.decision,
            approval.approved_at_utc,
            approval.signature_algorithm,
            approval.signing_key_id,
            approval.signing_public_key_member_identity,
            approval.detached_signature_member_identity,
        ),
    )
    if (
        type(approval.approval_file_byte_count) is not int
        or approval.approval_file_byte_count <= 0
        or type(approval.signing_public_key_byte_count) is not int
        or type(approval.detached_signature_byte_count) is not int
    ):
        _fail("approval_record_byte_count_drift")
    _require_sha256(
        "approval_record_sha256",
        (
            approval.approval_file_sha256,
            approval.subject_file_sha256,
            approval.signing_public_key_sha256,
            approval.detached_signature_sha256,
        ),
    )
    _require_record(
        approval.approval_record,
        EXTERNAL_ROLE_APPROVAL_SCHEMA.schema_version,
        "approval_record",
    )
    reparsed_record = parse_persisted_record(
        approval.approval_record.raw_bytes,
        EXTERNAL_ROLE_APPROVAL_SCHEMA,
    )
    if reparsed_record != approval.approval_record:
        _fail("approval_record_byte_binding_drift")
    payload = loads(approval.approval_record.canonical_body)
    payload_projection = (
        payload["approval_version"],
        payload["approval_role"],
        payload["approver_identity"],
        payload["subject_role"],
        payload["subject_logical_id"],
        payload["subject_file_sha256"],
        payload["decision"],
        payload["approved_at_utc"],
        payload["detached_message_domain"],
        payload["signature_algorithm"],
        payload["signing_key_id"],
        payload["signing_public_key_member_identity"],
        payload["signing_public_key_byte_count"],
        payload["signing_public_key_sha256"],
        payload["detached_signature_member_identity"],
        payload["detached_signature_byte_count"],
        payload["detached_signature_sha256"],
    )
    view_projection = (
        approval.approval_version,
        approval.approval_role,
        approval.approver_identity,
        approval.subject_role,
        approval.subject_logical_id,
        approval.subject_file_sha256,
        approval.decision,
        approval.approved_at_utc,
        approval.detached_message_domain,
        approval.signature_algorithm,
        approval.signing_key_id,
        approval.signing_public_key_member_identity,
        approval.signing_public_key_byte_count,
        approval.signing_public_key_sha256,
        approval.detached_signature_member_identity,
        approval.detached_signature_byte_count,
        approval.detached_signature_sha256,
    )
    if payload_projection != view_projection:
        _fail("approval_record_metadata_binding_drift")
    if (
        approval.approval_file_byte_count != len(approval.approval_record.raw_bytes)
        or approval.approval_file_sha256 != approval.approval_record.file_sha256
    ):
        _fail("approval_record_file_binding_drift")
    if approval.approval_role != expected_role:
        _fail("approval_role_census_drift")
    if (
        expected_approver_identity is not None
        and approval.approver_identity != expected_approver_identity
    ):
        _fail("approval_approver_join_drift")
    if expected_pin_subject is not None:
        observed_pin_subject = (
            approval.subject_role,
            approval.subject_logical_id,
            approval.subject_file_sha256,
        )
        if observed_pin_subject != expected_pin_subject:
            _fail("artifact_pin_approval_subject_join_drift")


def _referenced_member(
    member_kind: str,
    member_identity: str,
    file_byte_count: int,
    file_sha256: str,
) -> ReferencedMemberView:
    return ReferencedMemberView(
        member_kind=member_kind,
        member_identity=member_identity,
        file_byte_count=file_byte_count,
        file_sha256=file_sha256,
    )


def _complete_referenced_inventory(
    package: SyntheticPackageView,
) -> tuple[ReferencedMemberView, ...]:
    index = package.package_index
    inventory = tuple(
        member
        for triple in package.core_triples
        for member in (
            _referenced_member(
                "signing_public_key",
                triple.authority.signing_public_key_member_identity,
                triple.authority.signing_public_key_byte_count,
                triple.authority.signing_public_key_sha256,
            ),
            _referenced_member(
                "detached_signature",
                triple.authority.detached_signature_member_identity,
                triple.authority.detached_signature_byte_count,
                triple.authority.detached_signature_sha256,
            ),
            _referenced_member(
                "verifier_executable",
                triple.authority.verifier_executable_member_identity,
                triple.authority.verifier_executable_byte_count,
                triple.authority.verifier_executable_sha256,
            ),
            _referenced_member(
                "platform_signature",
                triple.authority.platform_signature_member_identity,
                triple.authority.platform_signature_byte_count,
                triple.authority.platform_signature_sha256,
            ),
            _referenced_member(
                "rotation",
                triple.authority.rotation_member_identity,
                triple.authority.rotation_byte_count,
                triple.authority.rotation_sha256,
            ),
        )
    )
    inventory += tuple(
        _referenced_member(
            "legacy_search_evidence",
            evidence.member_identity,
            len(evidence.record.raw_bytes),
            evidence.record.file_sha256,
        )
        for evidence in index.legacy_search_evidence
    )
    approvals = (
        index.responsible_owner_approval,
        index.external_scientist_approval,
        *index.custodian_approvals,
        *index.artifact_pin_approvals,
    )
    approval_kinds = (
        "responsible_owner_approval",
        "external_scientist_approval",
        *("custodian_approval" for _ in index.custodian_approvals),
        *("pin_approval" for _ in index.artifact_pin_approvals),
    )
    inventory += tuple(
        _referenced_member(
            member_kind,
            approval.approval_member_identity,
            approval.approval_file_byte_count,
            approval.approval_file_sha256,
        )
        for member_kind, approval in zip(approval_kinds, approvals)
    )
    inventory += (
        _referenced_member(
            "task7_process_spec_custody",
            index.task7_process_spec_custody.member_identity,
            index.task7_process_spec_custody.file_byte_count,
            index.task7_process_spec_custody.file_sha256,
        ),
        *(
            _referenced_member(
                "task5_scientific_parent_custody",
                custody.member_identity,
                custody.file_byte_count,
                custody.file_sha256,
            )
            for custody in index.task5_scientific_parent_custodies
        ),
    )
    inventory += tuple(
        member
        for approval in approvals
        for member in (
            _referenced_member(
                "signing_public_key",
                approval.signing_public_key_member_identity,
                approval.signing_public_key_byte_count,
                approval.signing_public_key_sha256,
            ),
            _referenced_member(
                "detached_signature",
                approval.detached_signature_member_identity,
                approval.detached_signature_byte_count,
                approval.detached_signature_sha256,
            ),
        )
    )
    return inventory


def _validate_package_index_record_binding(package: SyntheticPackageView) -> None:
    index = package.package_index
    reparsed_record = parse_persisted_record(
        index.index_record.raw_bytes,
        PACKAGE_INDEX_SCHEMA,
    )
    if reparsed_record != index.index_record:
        _fail("package_index_byte_binding_drift")
    payload = loads(index.index_record.canonical_body)

    payload_projection = (
        payload["index_version"],
        payload["package_logical_id"],
        payload["package_generation"],
        payload["task7_process_spec_custody_ref"],
        tuple(payload["task5_scientific_parent_custody_refs"]),
        tuple(item["role"] for item in payload["core_triples"]),
        payload["canonical_core_record_count"],
        payload["artifact_count"],
        payload["envelope_count"],
        payload["pin_count"],
        payload["review_count"],
        payload["migration_receipt_pin_sha256"],
    )
    metadata_projection = (
        index.index_version,
        index.package_logical_id,
        index.package_generation,
        index.task7_process_spec_custody_ref_sha256,
        index.task5_scientific_parent_custody_ref_sha256s,
        index.core_roles,
        index.canonical_core_record_count,
        index.artifact_count,
        index.envelope_count,
        index.pin_count,
        index.review_count,
        index.migration_receipt_pin_sha256,
    )
    if payload_projection != metadata_projection:
        _fail("package_index_metadata_binding_drift")

    payload_core_files = tuple(
        (
            item["role"],
            item["artifact_member_identity"],
            item["artifact_file_byte_count"],
            item["artifact_file_sha256"],
            item["envelope_member_identity"],
            item["envelope_file_byte_count"],
            item["envelope_file_sha256"],
            item["pin_member_identity"],
            item["pin_file_byte_count"],
            item["pin_file_sha256"],
        )
        for item in payload["core_triples"]
    )
    view_core_files = tuple(
        (
            triple.role,
            triple.artifact_member_identity,
            len(triple.artifact.raw_bytes),
            triple.artifact.file_sha256,
            triple.envelope_member_identity,
            len(triple.envelope.raw_bytes),
            triple.envelope.file_sha256,
            triple.pin_member_identity,
            len(triple.pin.raw_bytes),
            triple.pin.file_sha256,
        )
        for triple in package.core_triples
    )
    if payload_core_files != view_core_files:
        _fail("package_index_core_file_binding_drift")

    payload_referenced_members = tuple(
        (
            item["member_kind"],
            item["member_identity"],
            item["file_byte_count"],
            item["file_sha256"],
        )
        for item in payload["referenced_members"]
    )
    view_referenced_members = tuple(
        (
            member.member_kind,
            member.member_identity,
            member.file_byte_count,
            member.file_sha256,
        )
        for member in index.referenced_members
    )
    if payload_referenced_members != view_referenced_members:
        _fail("package_index_referenced_member_binding_drift")

    payload_pin_approvals = tuple(
        (
            item["subject_role"],
            item["approval_member_identity"],
            item["approval_file_byte_count"],
            item["approval_file_sha256"],
        )
        for item in payload["pin_approval_refs"]
    )
    view_pin_approvals = tuple(
        (
            pin_ref.subject_role,
            pin_ref.approval_member_identity,
            pin_ref.approval_file_byte_count,
            pin_ref.approval_file_sha256,
        )
        for pin_ref in index.pin_approval_refs
    )
    if payload_pin_approvals != view_pin_approvals:
        _fail("package_index_pin_approval_binding_drift")


def _validate_index_and_core(package: SyntheticPackageView) -> None:
    index = package.package_index
    _require_record(index.index_record, _PACKAGE_INDEX_SCHEMA, "package_index")
    if type(index.index_version) is not int or index.index_version != 1:
        _fail("package_index_version_drift")
    if type(index.package_generation) is not int or index.package_generation <= 0:
        _fail("package_generation_drift")
    if (
        type(index.custodian_identities) is not tuple
        or type(index.custodian_approval_member_identities) is not tuple
        or type(index.custodian_approval_sha256s) is not tuple
        or type(index.custodian_approvals) is not tuple
        or not index.custodian_identities
        or len(index.custodian_identities)
        != len(index.custodian_approval_member_identities)
        or len(index.custodian_identities) != len(index.custodian_approval_sha256s)
        or len(index.custodian_identities) != len(index.custodian_approvals)
    ):
        _fail("custodian_approval_census_drift")
    if (
        type(index.referenced_members) is not tuple
        or type(index.pin_approval_refs) is not tuple
        or type(index.legacy_search_evidence) is not tuple
        or type(index.task5_scientific_parent_custodies) is not tuple
        or type(index.artifact_pin_approvals) is not tuple
        or not index.legacy_search_evidence
        or len(index.task5_scientific_parent_custodies) != 3
        or len(index.artifact_pin_approvals) != 7
    ):
        _fail("package_index_typed_census_drift")
    for member in index.referenced_members:
        _validate_referenced_member(member)
    for pin_ref in index.pin_approval_refs:
        _validate_pin_approval_ref(pin_ref)
    for evidence in index.legacy_search_evidence:
        _validate_legacy_evidence(evidence)
    _validate_custody_object(
        index.task7_process_spec_custody,
        "task7_process_spec_custody",
    )
    for custody in index.task5_scientific_parent_custodies:
        _validate_custody_object(custody, "task5_scientific_parent_custody")
    _require_visible_ascii(
        "package_index_identity",
        (
            index.package_logical_id,
            index.responsible_owner_identity,
            index.external_scientist_identity,
            index.responsible_owner_approval_member_identity,
            index.external_scientist_approval_member_identity,
            *index.custodian_identities,
            *index.custodian_approval_member_identities,
        ),
    )
    _require_sha256(
        "package_index_approval_sha256",
        (
            index.migration_receipt_pin_sha256,
            index.responsible_owner_approval_sha256,
            index.external_scientist_approval_sha256,
            *index.custodian_approval_sha256s,
        ),
    )
    if index.task7_process_spec_custody_ref_sha256 != _TASK7_PROCESS_SPEC_SHA256:
        _fail("task7_process_spec_custody_drift")
    require_exact_tuple(
        "task5_scientific_parent_custody",
        index.task5_scientific_parent_custody_ref_sha256s,
        _TASK5_SCIENTIFIC_PARENT_SHA256S,
    )
    if (
        index.task7_process_spec_custody.file_byte_count
        != _TASK7_PROCESS_SPEC_BYTE_COUNT
        or index.task7_process_spec_custody.file_sha256
        != index.task7_process_spec_custody_ref_sha256
        or tuple(
            custody.file_byte_count
            for custody in index.task5_scientific_parent_custodies
        )
        != _TASK5_SCIENTIFIC_PARENT_BYTE_COUNTS
        or tuple(
            custody.file_sha256 for custody in index.task5_scientific_parent_custodies
        )
        != index.task5_scientific_parent_custody_ref_sha256s
    ):
        _fail("scientific_parent_custody_binding_drift")
    require_exact_tuple("core_role_census", index.core_roles, _FROZEN_ROLES)
    expected_counts = (21, 7, 7, 7, 3)
    observed_counts = (
        index.canonical_core_record_count,
        index.artifact_count,
        index.envelope_count,
        index.pin_count,
        index.review_count,
    )
    if any(type(value) is not int for value in observed_counts):
        _fail("core_record_census_drift")
    require_exact_tuple("core_record_census", observed_counts, expected_counts)
    if len(package.core_triples) != 7:
        _fail("core_triple_census_drift")
    if index.migration_receipt_pin_sha256 != package.core_triples[-1].pin.file_sha256:
        _fail("migration_receipt_pin_join_drift")

    roles = tuple(triple.role for triple in package.core_triples)
    schemas = tuple(triple.artifact_schema_version for triple in package.core_triples)
    require_exact_tuple("core_triple_roles", roles, _FROZEN_ROLES)
    require_exact_tuple("core_artifact_schemas", schemas, _FROZEN_ROLE_SCHEMAS)
    for triple in package.core_triples:
        if type(triple.artifact_version) is not int or triple.artifact_version != 1:
            _fail("core_artifact_version_drift")
        if type(triple.authority) is not RoleAuthorityView:
            _fail("role_authority_view_drift")
        _require_visible_ascii(
            "core_logical_identity",
            (
                triple.artifact_logical_id,
                triple.envelope_logical_id,
                triple.pin_logical_id,
                triple.artifact_member_identity,
                triple.envelope_member_identity,
                triple.pin_member_identity,
            ),
        )
        _validate_role_authority(triple.authority)
        _require_record(
            triple.artifact,
            triple.artifact_schema_version,
            "core_artifact",
            _record_self_hash_field(triple.artifact_schema_version),
        )
        _require_record(
            triple.envelope,
            _ENVELOPE_SCHEMA,
            "core_envelope",
            "envelope_sha256",
        )
        _require_record(
            triple.pin,
            _PIN_SCHEMA,
            "core_pin",
            "pin_sha256",
        )

    _validate_approval_record(
        index.responsible_owner_approval,
        "responsible_owner",
        index.responsible_owner_identity,
        None,
    )
    _validate_approval_record(
        index.external_scientist_approval,
        "external_scientist",
        index.external_scientist_identity,
        None,
    )
    for identity, approval in zip(
        index.custodian_identities,
        index.custodian_approvals,
    ):
        _validate_approval_record(approval, "custodian", identity, None)
    for triple, approval in zip(
        package.core_triples,
        index.artifact_pin_approvals,
    ):
        _validate_approval_record(
            approval,
            "artifact_pin",
            None,
            (triple.role, triple.pin_logical_id, triple.pin.file_sha256),
        )

    if (
        index.responsible_owner_approval_member_identity
        != index.responsible_owner_approval.approval_member_identity
        or index.responsible_owner_approval_sha256
        != index.responsible_owner_approval.approval_file_sha256
        or index.external_scientist_approval_member_identity
        != index.external_scientist_approval.approval_member_identity
        or index.external_scientist_approval_sha256
        != index.external_scientist_approval.approval_file_sha256
        or index.custodian_approval_member_identities
        != tuple(
            approval.approval_member_identity for approval in index.custodian_approvals
        )
        or index.custodian_approval_sha256s
        != tuple(
            approval.approval_file_sha256 for approval in index.custodian_approvals
        )
    ):
        _fail("external_role_approval_join_drift")
    expected_pin_refs = tuple(
        PinApprovalRefView(
            subject_role=triple.role,
            approval_member_identity=approval.approval_member_identity,
            approval_file_byte_count=approval.approval_file_byte_count,
            approval_file_sha256=approval.approval_file_sha256,
        )
        for triple, approval in zip(
            package.core_triples,
            index.artifact_pin_approvals,
        )
    )
    require_exact_tuple(
        "artifact_pin_approval_ref_census",
        index.pin_approval_refs,
        expected_pin_refs,
    )
    for triple, approval in zip(
        package.core_triples,
        index.artifact_pin_approvals,
    ):
        authority = triple.authority
        if (
            authority.approval_member_identity != approval.approval_member_identity
            or authority.approval_file_byte_count != approval.approval_file_byte_count
            or authority.approval_sha256 != approval.approval_file_sha256
        ):
            _fail("core_authority_approval_join_drift")
    require_exact_tuple(
        "complete_referenced_inventory",
        index.referenced_members,
        _complete_referenced_inventory(package),
    )
    _validate_package_index_record_binding(package)
    _validate_global_occurrence_census(package)


def _canonical_global_occurrences(
    package: SyntheticPackageView,
) -> tuple[str, ...]:
    index = package.package_index
    approvals = (
        index.responsible_owner_approval,
        index.external_scientist_approval,
        *index.custodian_approvals,
        *index.artifact_pin_approvals,
    )
    return (
        index.package_logical_id,
        *(
            value
            for triple in package.core_triples
            for value in (
                triple.artifact_logical_id,
                triple.envelope_logical_id,
                triple.pin_logical_id,
            )
        ),
        *(
            value
            for triple in package.core_triples
            for value in (
                triple.artifact_member_identity,
                triple.artifact.file_sha256,
                triple.envelope_member_identity,
                triple.envelope.file_sha256,
                triple.pin_member_identity,
                triple.pin.file_sha256,
            )
        ),
        *(
            value
            for member in index.referenced_members
            for value in (member.member_identity, member.file_sha256)
        ),
        *(
            value
            for triple in package.core_triples
            for value in (
                triple.authority.actor_identity,
                triple.authority.producer_package_identity,
                triple.authority.verifier_package_identity,
                triple.authority.signing_key_id,
            )
        ),
        index.responsible_owner_identity,
        index.external_scientist_identity,
        *index.custodian_identities,
        *(approval.signing_key_id for approval in approvals),
        *(approval.approver_identity for approval in index.artifact_pin_approvals),
        *(
            record.self_sha256
            for triple in package.core_triples
            for record in (triple.artifact, triple.envelope, triple.pin)
        ),
        *(approval.approval_record.self_sha256 for approval in approvals),
    )


def _validate_global_occurrence_census(package: SyntheticPackageView) -> None:
    require_globally_distinct(
        "global_role_occurrence",
        _canonical_global_occurrences(package),
    )


def _expected_receipt_join(
    triples: tuple[CoreTripleView, ...],
) -> tuple[ReceiptJoinView, ...]:
    return tuple(
        ReceiptJoinView(
            role=triple.role,
            artifact_file_sha256=triple.artifact.file_sha256,
            artifact_sha256=triple.artifact.self_sha256,
            envelope_file_sha256=triple.envelope.file_sha256,
            envelope_sha256=triple.envelope.self_sha256,
            pin_file_sha256=triple.pin.file_sha256,
            pin_sha256=triple.pin.self_sha256,
        )
        for triple in triples[:6]
    )


def _validate_exact_dag(package: SyntheticPackageView) -> None:
    triples = package.core_triples
    expected_envelope_predecessors = (
        (),
        (triples[0].envelope.self_sha256,),
        (triples[1].envelope.self_sha256,),
        (triples[2].envelope.self_sha256,),
        (triples[2].envelope.self_sha256,),
        (triples[2].envelope.self_sha256,),
        tuple(sorted(triples[index].envelope.self_sha256 for index in (3, 4, 5))),
    )
    expected_pin_predecessors = (
        (),
        (triples[0].pin.self_sha256,),
        (triples[1].pin.self_sha256,),
        (triples[2].pin.self_sha256,),
        (triples[2].pin.self_sha256,),
        (triples[2].pin.self_sha256,),
        tuple(sorted(triples[index].pin.self_sha256 for index in (3, 4, 5))),
    )
    observed_envelope_predecessors = tuple(
        triple.predecessor_envelope_sha256s for triple in triples
    )
    observed_pin_predecessors = tuple(
        triple.predecessor_pin_sha256s for triple in triples
    )
    require_exact_tuple(
        "envelope_predecessor_dag",
        observed_envelope_predecessors,
        expected_envelope_predecessors,
    )
    require_exact_tuple(
        "pin_predecessor_dag",
        observed_pin_predecessors,
        expected_pin_predecessors,
    )
    require_exact_tuple(
        "receipt_six_predecessor_join",
        package.receipt_predecessor_join,
        _expected_receipt_join(triples),
    )


def validate_frozen_scientific_contract(package: SyntheticPackageView) -> None:
    """Require the frozen science, ancestry, census, and seven-role DAG exactly."""

    _require_package_view(package)
    _validate_index_and_core(package)
    science = package.scientific_contract
    if science.legacy_continuity is not False:
        _fail("legacy_continuity_drift")
    if science.legacy_equivalence is not False:
        _fail("legacy_equivalence_drift")
    require_exact_tuple(
        "thesis_scalars", science.thesis_scalars, _FROZEN_THESIS_SCALARS
    )
    require_exact_tuple("policy_ids", science.policy_ids, _FROZEN_POLICY_IDS)
    require_exact_tuple(
        "endpoint_hierarchy",
        science.endpoint_hierarchy,
        _FROZEN_ENDPOINT_HIERARCHY,
    )
    require_exact_tuple("kill_chain", science.kill_chain, _FROZEN_KILL_CHAIN)
    _validate_exact_dag(package)
    return None


def validate_global_role_separation(package: SyntheticPackageView) -> None:
    """Reject reuse across logical IDs and all authority-role occurrences."""

    _require_package_view(package)
    _validate_index_and_core(package)
    return None
