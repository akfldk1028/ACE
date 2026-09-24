from __future__ import annotations

import ast
from dataclasses import fields, replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from iclr2027.path_b_positive_intake_contract import (
    EXTERNAL_ROLE_APPROVAL_SCHEMA,
    PACKAGE_INDEX_SCHEMA,
    PersistedRecord,
    parse_persisted_record,
)


ROOT = Path(__file__).resolve().parents[1]
SCIENCE_PATH = ROOT / "iclr2027" / "path_b_positive_intake_science.py"
FROZEN_PATH = ROOT / "iclr2027" / "external_authority_acquisition.py"
ORACLE_PATH = ROOT / "iclr2027" / "obligation_oracle.py"

EXPECTED_TASK7_PROCESS_SHA = (
    "9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54"
)
EXPECTED_TASK5_PARENTS = (
    "2809048fa71d0f2458db13f7590c61f0f28674f2195c3d8690a45193df517299",
    "8d2f27d2fb9e6901d7bfed90407a25f8c714d23fe9d2f511a469494e272054ee",
    "8d98a17ee57b1a254d4f651d74b44b696ec022e3822daea1b8a3f25036060cc8",
)
EXPECTED_ROLES = (
    "legacy_search_impossibility_declaration",
    "one_thesis_contract",
    "new_upstream_scientific_snapshot",
    "independent_science_migration_review",
    "independent_provenance_migration_review",
    "independent_security_migration_review",
    "provenance_migration_receipt",
)
EXPECTED_REFERENCED_MEMBER_KINDS = (
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
)
EXPECTED_APPROVAL_DOMAINS = {
    "responsible_owner": "ACE-ICLR2027-PATH-B-RESPONSIBLE-OWNER-APPROVAL-V1\x00",
    "external_scientist": "ACE-ICLR2027-PATH-B-EXTERNAL-SCIENTIST-APPROVAL-V1\x00",
    "custodian": "ACE-ICLR2027-PATH-B-CUSTODIAN-APPROVAL-V1\x00",
    "artifact_pin": "ACE-ICLR2027-PATH-B-ARTIFACT-PIN-APPROVAL-V1\x00",
}
EXPECTED_CUSTODY_BYTE_COUNTS = (71_589, 63_630, 62_828, 90_780)
EXPECTED_TYPED_VIEW_FIELDS = {
    "ReferencedMemberView": (
        "member_kind",
        "member_identity",
        "file_byte_count",
        "file_sha256",
    ),
    "PinApprovalRefView": (
        "subject_role",
        "approval_member_identity",
        "approval_file_byte_count",
        "approval_file_sha256",
    ),
    "LegacyEvidenceView": ("member_identity", "record"),
    "CustodyObjectView": (
        "member_identity",
        "file_byte_count",
        "file_sha256",
    ),
    "ApprovalRecordView": (
        "approval_member_identity",
        "approval_file_byte_count",
        "approval_file_sha256",
        "approval_record",
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
    ),
}
EXPECTED_ROLE_AUTHORITY_FIELDS = (
    "actor_identity",
    "producer_package_identity",
    "signing_key_id",
    "signing_public_key_member_identity",
    "signing_public_key_byte_count",
    "signing_public_key_sha256",
    "detached_signature_member_identity",
    "detached_signature_byte_count",
    "detached_signature_sha256",
    "verifier_package_identity",
    "verifier_executable_member_identity",
    "verifier_executable_byte_count",
    "verifier_executable_sha256",
    "platform_signature_member_identity",
    "platform_signature_byte_count",
    "platform_signature_sha256",
    "rotation_member_identity",
    "rotation_byte_count",
    "rotation_sha256",
    "approval_member_identity",
    "approval_file_byte_count",
    "approval_sha256",
)
EXPECTED_CORE_TRIPLE_VIEW_FIELDS = (
    "role",
    "artifact_schema_version",
    "artifact_version",
    "artifact_logical_id",
    "envelope_logical_id",
    "pin_logical_id",
    "artifact_member_identity",
    "envelope_member_identity",
    "pin_member_identity",
    "artifact",
    "envelope",
    "pin",
    "predecessor_envelope_sha256s",
    "predecessor_pin_sha256s",
    "authority",
)
EXPECTED_PACKAGE_INDEX_METADATA_FIELDS = (
    "index_record",
    "index_version",
    "package_generation",
    "package_logical_id",
    "task7_process_spec_custody_ref_sha256",
    "task5_scientific_parent_custody_ref_sha256s",
    "core_roles",
    "referenced_members",
    "pin_approval_refs",
    "canonical_core_record_count",
    "artifact_count",
    "envelope_count",
    "pin_count",
    "review_count",
    "migration_receipt_pin_sha256",
    "responsible_owner_identity",
    "external_scientist_identity",
    "custodian_identities",
    "responsible_owner_approval_member_identity",
    "responsible_owner_approval_sha256",
    "external_scientist_approval_member_identity",
    "external_scientist_approval_sha256",
    "custodian_approval_member_identities",
    "custodian_approval_sha256s",
    "legacy_search_evidence",
    "task7_process_spec_custody",
    "task5_scientific_parent_custodies",
    "responsible_owner_approval",
    "external_scientist_approval",
    "custodian_approvals",
    "artifact_pin_approvals",
)
EXPECTED_ROLE_SCHEMAS = (
    "ace.iclr2027.legacy_search_impossibility_declaration.vnext",
    "ace.iclr2027.one_thesis_contract.vnext",
    "ace.iclr2027.new_upstream_scientific_snapshot.vnext",
    "ace.iclr2027.independent_migration_review.vnext",
    "ace.iclr2027.independent_migration_review.vnext",
    "ace.iclr2027.independent_migration_review.vnext",
    "ace.iclr2027.provenance_migration_receipt.vnext",
)
EXPECTED_ARTIFACT_SELF_HASH_FIELDS = (
    "declaration_sha256",
    "contract_sha256",
    "snapshot_sha256",
    "review_sha256",
    "review_sha256",
    "review_sha256",
    "receipt_sha256",
)
EXPECTED_THESIS_SCALARS = (
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
EXPECTED_POLICY_IDS = (
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
EXPECTED_ENDPOINT_HIERARCHY = (
    "e2_randomized_executed_bundle_primary",
    "e3_equal_information_oacs_vs_full_parity_raw_router_conditional_on_e2",
    "e4_fresh_downstream_frontier_conditional_on_e1_e2_e3",
    "e1_predictive_support_noncausal_nonprimary",
)
EXPECTED_KILL_CHAIN = (
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
EXPECTED_E3_PARENT_FIELDS = (
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
EXPECTED_E3_SHARED_FIELDS = (
    "costs",
    "admissibility",
    "examples",
    "split_fold",
    "learner_class_capacity",
    "tuning_optimization_opportunity",
    "action_space_tie_rule",
)


def _science():
    try:
        return importlib.import_module("iclr2027.path_b_positive_intake_science")
    except ModuleNotFoundError as error:
        raise AssertionError("positive-intake science module is absent") from error


def _digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


def _record(label: str, schema: str) -> PersistedRecord:
    if schema == "ace.iclr2027.legacy_search_impossibility_declaration.vnext":
        self_hash_field = "declaration_sha256"
    elif schema == "ace.iclr2027.one_thesis_contract.vnext":
        self_hash_field = "contract_sha256"
    elif schema == "ace.iclr2027.new_upstream_scientific_snapshot.vnext":
        self_hash_field = "snapshot_sha256"
    elif schema == "ace.iclr2027.independent_migration_review.vnext":
        self_hash_field = "review_sha256"
    elif schema == "ace.iclr2027.provenance_migration_receipt.vnext":
        self_hash_field = "receipt_sha256"
    elif schema == "ace.iclr2027.external_canonical_signature_envelope.vnext":
        self_hash_field = "envelope_sha256"
    elif schema == "ace.iclr2027.external_vnext_artifact_pin.vnext":
        self_hash_field = "pin_sha256"
    elif schema == "ace.iclr2027.path_b_positive_intake_package_index.v1":
        self_hash_field = "index_sha256"
    elif schema == "ace.iclr2027.legacy_search_evidence.vnext":
        self_hash_field = "evidence_sha256"
    else:
        raise AssertionError(f"unruled structural fixture schema: {schema}")
    return _structural_record(label, schema, self_hash_field)


def _authority(module, index: int):
    tag = f"role-{index}"
    return module.RoleAuthorityView(
        actor_identity=f"actor:{tag}",
        producer_package_identity=f"producer-package:{tag}",
        signing_key_id=f"key:{tag}",
        signing_public_key_member_identity=f"members/{tag}/key.pub",
        signing_public_key_byte_count=32,
        signing_public_key_sha256=_digest(f"key:{tag}"),
        detached_signature_member_identity=f"members/{tag}/artifact.sig",
        detached_signature_byte_count=64,
        detached_signature_sha256=_digest(f"signature:{tag}"),
        verifier_package_identity=f"verifier-package:{tag}",
        verifier_executable_member_identity=f"members/{tag}/verifier.bin",
        verifier_executable_byte_count=100 + index,
        verifier_executable_sha256=_digest(f"verifier:{tag}"),
        platform_signature_member_identity=f"members/{tag}/platform.sig",
        platform_signature_byte_count=64,
        platform_signature_sha256=_digest(f"platform:{tag}"),
        rotation_member_identity=f"members/{tag}/rotation.json",
        rotation_byte_count=200 + index,
        rotation_sha256=_digest(f"rotation:{tag}"),
        approval_member_identity=f"approvals/{tag}/pin.json",
        approval_file_byte_count=300 + index,
        approval_sha256=_digest(f"approval:{tag}"),
    )


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _structural_record(
    label: str, schema: str, self_hash_field: str
) -> PersistedRecord:
    payload = {
        "fixture": label,
        "schema_version": schema,
    }
    self_sha256 = sha256(_canonical_json(payload)).hexdigest()
    sealed = dict(payload)
    sealed[self_hash_field] = self_sha256
    raw = _canonical_json(sealed) + b"\n"
    return PersistedRecord(
        schema_version=schema,
        raw_bytes=raw,
        canonical_body=raw[:-1],
        file_sha256=sha256(raw).hexdigest(),
        self_sha256=self_sha256,
    )


def _fabricated_record(label: str, schema: str) -> PersistedRecord:
    raw = ('{"fixture":"' + label + '"}\n').encode("ascii")
    return PersistedRecord(
        schema_version=schema,
        raw_bytes=raw,
        canonical_body=raw[:-1],
        file_sha256=sha256(raw).hexdigest(),
        self_sha256=_digest("self:" + label),
    )


def _sealed_index_record(payload: dict[str, object]) -> PersistedRecord:
    sealed = dict(payload)
    sealed["index_sha256"] = sha256(_canonical_json(sealed)).hexdigest()
    return parse_persisted_record(_canonical_json(sealed) + b"\n", PACKAGE_INDEX_SCHEMA)


def _approval_view(
    module,
    tag: str,
    approval_role: str,
    approver_identity: str,
    subject_role: str,
    subject_logical_id: str,
    subject_file_sha256: str,
):
    signing_public_key_member_identity = f"approval-material/{tag}/key.pub"
    signing_public_key_sha256 = _digest(f"approval-key:{tag}")
    detached_signature_member_identity = f"approval-material/{tag}/record.sig"
    detached_signature_sha256 = _digest(f"approval-signature:{tag}")
    payload = {
        "schema_version": EXTERNAL_ROLE_APPROVAL_SCHEMA.schema_version,
        "approval_version": 1,
        "approval_role": approval_role,
        "approver_identity": approver_identity,
        "subject_role": subject_role,
        "subject_logical_id": subject_logical_id,
        "subject_file_sha256": subject_file_sha256,
        "decision": "approve",
        "approved_at_utc": "2026-08-30T00:00:00Z",
        "detached_message_domain": EXPECTED_APPROVAL_DOMAINS[approval_role],
        "signature_algorithm": "Ed25519",
        "signing_key_id": f"approval-key-id:{tag}",
        "signing_public_key_member_identity": signing_public_key_member_identity,
        "signing_public_key_byte_count": 32,
        "signing_public_key_sha256": signing_public_key_sha256,
        "detached_signature_member_identity": detached_signature_member_identity,
        "detached_signature_byte_count": 64,
        "detached_signature_sha256": detached_signature_sha256,
    }
    sealed = dict(payload)
    sealed["approval_sha256"] = sha256(_canonical_json(sealed)).hexdigest()
    record = parse_persisted_record(
        _canonical_json(sealed) + b"\n",
        EXTERNAL_ROLE_APPROVAL_SCHEMA,
    )
    return module.ApprovalRecordView(
        approval_member_identity=f"approvals/{tag}.json",
        approval_file_byte_count=len(record.raw_bytes),
        approval_file_sha256=record.file_sha256,
        approval_record=record,
        approval_version=1,
        approval_role=approval_role,
        approver_identity=approver_identity,
        subject_role=subject_role,
        subject_logical_id=subject_logical_id,
        subject_file_sha256=subject_file_sha256,
        decision="approve",
        approved_at_utc="2026-08-30T00:00:00Z",
        detached_message_domain=EXPECTED_APPROVAL_DOMAINS[approval_role],
        signature_algorithm="Ed25519",
        signing_key_id=f"approval-key-id:{tag}",
        signing_public_key_member_identity=signing_public_key_member_identity,
        signing_public_key_byte_count=32,
        signing_public_key_sha256=signing_public_key_sha256,
        detached_signature_member_identity=detached_signature_member_identity,
        detached_signature_byte_count=64,
        detached_signature_sha256=detached_signature_sha256,
    )


def _referenced_member_view(module, kind: str, identity: str, count: int, digest: str):
    return module.ReferencedMemberView(
        member_kind=kind,
        member_identity=identity,
        file_byte_count=count,
        file_sha256=digest,
    )


def _complete_referenced_inventory(module, metadata, triples):
    inventory = []
    for triple in triples:
        authority = triple.authority
        inventory.extend(
            (
                _referenced_member_view(
                    module,
                    "signing_public_key",
                    authority.signing_public_key_member_identity,
                    authority.signing_public_key_byte_count,
                    authority.signing_public_key_sha256,
                ),
                _referenced_member_view(
                    module,
                    "detached_signature",
                    authority.detached_signature_member_identity,
                    authority.detached_signature_byte_count,
                    authority.detached_signature_sha256,
                ),
                _referenced_member_view(
                    module,
                    "verifier_executable",
                    authority.verifier_executable_member_identity,
                    authority.verifier_executable_byte_count,
                    authority.verifier_executable_sha256,
                ),
                _referenced_member_view(
                    module,
                    "platform_signature",
                    authority.platform_signature_member_identity,
                    authority.platform_signature_byte_count,
                    authority.platform_signature_sha256,
                ),
                _referenced_member_view(
                    module,
                    "rotation",
                    authority.rotation_member_identity,
                    authority.rotation_byte_count,
                    authority.rotation_sha256,
                ),
            )
        )
    inventory.extend(
        _referenced_member_view(
            module,
            "legacy_search_evidence",
            evidence.member_identity,
            len(evidence.record.raw_bytes),
            evidence.record.file_sha256,
        )
        for evidence in metadata.legacy_search_evidence
    )
    approvals = (
        metadata.responsible_owner_approval,
        metadata.external_scientist_approval,
        *metadata.custodian_approvals,
        *metadata.artifact_pin_approvals,
    )
    approval_kinds = (
        "responsible_owner_approval",
        "external_scientist_approval",
        *("custodian_approval" for _ in metadata.custodian_approvals),
        *("pin_approval" for _ in metadata.artifact_pin_approvals),
    )
    inventory.extend(
        _referenced_member_view(
            module,
            kind,
            approval.approval_member_identity,
            approval.approval_file_byte_count,
            approval.approval_file_sha256,
        )
        for kind, approval in zip(approval_kinds, approvals, strict=True)
    )
    inventory.append(
        _referenced_member_view(
            module,
            "task7_process_spec_custody",
            metadata.task7_process_spec_custody.member_identity,
            metadata.task7_process_spec_custody.file_byte_count,
            metadata.task7_process_spec_custody.file_sha256,
        )
    )
    inventory.extend(
        _referenced_member_view(
            module,
            "task5_scientific_parent_custody",
            custody.member_identity,
            custody.file_byte_count,
            custody.file_sha256,
        )
        for custody in metadata.task5_scientific_parent_custodies
    )
    for approval in approvals:
        inventory.extend(
            (
                _referenced_member_view(
                    module,
                    "signing_public_key",
                    approval.signing_public_key_member_identity,
                    approval.signing_public_key_byte_count,
                    approval.signing_public_key_sha256,
                ),
                _referenced_member_view(
                    module,
                    "detached_signature",
                    approval.detached_signature_member_identity,
                    approval.detached_signature_byte_count,
                    approval.detached_signature_sha256,
                ),
            )
        )
    return tuple(inventory)


def _index_payload(metadata, triples) -> dict[str, object]:
    return {
        "schema_version": PACKAGE_INDEX_SCHEMA.schema_version,
        "index_version": metadata.index_version,
        "package_logical_id": metadata.package_logical_id,
        "package_generation": metadata.package_generation,
        "task7_process_spec_custody_ref": (
            metadata.task7_process_spec_custody_ref_sha256
        ),
        "task5_scientific_parent_custody_refs": list(
            metadata.task5_scientific_parent_custody_ref_sha256s
        ),
        "core_triples": [
            {
                "role": triple.role,
                "artifact_member_identity": triple.artifact_member_identity,
                "artifact_file_byte_count": len(triple.artifact.raw_bytes),
                "artifact_file_sha256": triple.artifact.file_sha256,
                "envelope_member_identity": triple.envelope_member_identity,
                "envelope_file_byte_count": len(triple.envelope.raw_bytes),
                "envelope_file_sha256": triple.envelope.file_sha256,
                "pin_member_identity": triple.pin_member_identity,
                "pin_file_byte_count": len(triple.pin.raw_bytes),
                "pin_file_sha256": triple.pin.file_sha256,
            }
            for triple in triples
        ],
        "referenced_members": [
            {
                "member_kind": member.member_kind,
                "member_identity": member.member_identity,
                "file_byte_count": member.file_byte_count,
                "file_sha256": member.file_sha256,
            }
            for member in metadata.referenced_members
        ],
        "pin_approval_refs": [
            {
                "subject_role": pin_ref.subject_role,
                "approval_member_identity": pin_ref.approval_member_identity,
                "approval_file_byte_count": pin_ref.approval_file_byte_count,
                "approval_file_sha256": pin_ref.approval_file_sha256,
            }
            for pin_ref in metadata.pin_approval_refs
        ],
        "canonical_core_record_count": metadata.canonical_core_record_count,
        "artifact_count": metadata.artifact_count,
        "envelope_count": metadata.envelope_count,
        "pin_count": metadata.pin_count,
        "review_count": metadata.review_count,
        "migration_receipt_pin_sha256": metadata.migration_receipt_pin_sha256,
    }


def _with_rebound_index(package, **updates):
    metadata = replace(package.package_index, **updates)
    record = _sealed_index_record(_index_payload(metadata, package.core_triples))
    return replace(
        package,
        package_index=replace(metadata, index_record=record),
    )


def _resealed_package(package, metadata=None, triples=None):
    observed_metadata = package.package_index if metadata is None else metadata
    observed_triples = package.core_triples if triples is None else tuple(triples)
    record = _sealed_index_record(_index_payload(observed_metadata, observed_triples))
    return replace(
        package,
        package_index=replace(observed_metadata, index_record=record),
        core_triples=observed_triples,
    )


def _resealed_approval_view(view, **updates):
    payload = json.loads(view.approval_record.canonical_body)
    payload.pop("approval_sha256")
    record_fields = {
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
    }
    payload.update(
        {key: value for key, value in updates.items() if key in record_fields}
    )
    sealed = dict(payload)
    sealed["approval_sha256"] = sha256(_canonical_json(sealed)).hexdigest()
    record = parse_persisted_record(
        _canonical_json(sealed) + b"\n",
        EXTERNAL_ROLE_APPROVAL_SCHEMA,
    )
    return replace(
        view,
        approval_record=record,
        approval_file_byte_count=len(record.raw_bytes),
        approval_file_sha256=record.file_sha256,
        **updates,
    )


def _approval_views(index):
    return (
        index.responsible_owner_approval,
        index.external_scientist_approval,
        *index.custodian_approvals,
        *index.artifact_pin_approvals,
    )


def _canonical_occurrence_census(package) -> tuple[str, ...]:
    index = package.package_index
    approvals = _approval_views(index)
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


def _package_with_cardinalities(custodian_count: int, evidence_count: int):
    module = _science()
    package = _package()
    index = package.package_index
    identities = tuple(
        f"custodian:formula:{position}" for position in range(custodian_count)
    )
    custodians = tuple(
        _approval_view(
            module,
            f"formula-custodian-{position}",
            "custodian",
            identity,
            EXPECTED_ROLES[0],
            package.core_triples[0].artifact_logical_id,
            package.core_triples[0].artifact.file_sha256,
        )
        for position, identity in enumerate(identities)
    )
    evidence = tuple(
        module.LegacyEvidenceView(
            member_identity=f"evidence/formula-{position}.json",
            record=_record(
                f"formula-evidence-{position}",
                "ace.iclr2027.legacy_search_evidence.vnext",
            ),
        )
        for position in range(evidence_count)
    )
    metadata = replace(
        index,
        custodian_identities=identities,
        custodian_approval_member_identities=tuple(
            approval.approval_member_identity for approval in custodians
        ),
        custodian_approval_sha256s=tuple(
            approval.approval_file_sha256 for approval in custodians
        ),
        custodian_approvals=custodians,
        legacy_search_evidence=evidence,
    )
    metadata = replace(
        metadata,
        referenced_members=_complete_referenced_inventory(
            module,
            metadata,
            package.core_triples,
        ),
    )
    return _resealed_package(package, metadata=metadata)


def _replace_approval_at(package, ordinal: int, **updates):
    module = _science()
    index = package.package_index
    approvals = _approval_views(index)
    updated = _resealed_approval_view(approvals[ordinal], **updates)
    triples = list(package.core_triples)

    if ordinal == 0:
        metadata = replace(
            index,
            responsible_owner_approval=updated,
            responsible_owner_approval_member_identity=(
                updated.approval_member_identity
            ),
            responsible_owner_approval_sha256=updated.approval_file_sha256,
        )
    elif ordinal == 1:
        metadata = replace(
            index,
            external_scientist_approval=updated,
            external_scientist_approval_member_identity=(
                updated.approval_member_identity
            ),
            external_scientist_approval_sha256=updated.approval_file_sha256,
        )
    elif ordinal < 2 + len(index.custodian_approvals):
        position = ordinal - 2
        custodians = list(index.custodian_approvals)
        custodians[position] = updated
        metadata = replace(
            index,
            custodian_approvals=tuple(custodians),
            custodian_approval_member_identities=tuple(
                approval.approval_member_identity for approval in custodians
            ),
            custodian_approval_sha256s=tuple(
                approval.approval_file_sha256 for approval in custodians
            ),
        )
    else:
        position = ordinal - 2 - len(index.custodian_approvals)
        pin_approvals = list(index.artifact_pin_approvals)
        pin_approvals[position] = updated
        pin_refs = list(index.pin_approval_refs)
        pin_refs[position] = module.PinApprovalRefView(
            subject_role=triples[position].role,
            approval_member_identity=updated.approval_member_identity,
            approval_file_byte_count=updated.approval_file_byte_count,
            approval_file_sha256=updated.approval_file_sha256,
        )
        triples[position] = replace(
            triples[position],
            authority=replace(
                triples[position].authority,
                approval_member_identity=updated.approval_member_identity,
                approval_file_byte_count=updated.approval_file_byte_count,
                approval_sha256=updated.approval_file_sha256,
            ),
        )
        metadata = replace(
            index,
            artifact_pin_approvals=tuple(pin_approvals),
            pin_approval_refs=tuple(pin_refs),
        )

    metadata = replace(
        metadata,
        referenced_members=_complete_referenced_inventory(
            module,
            metadata,
            tuple(triples),
        ),
    )
    return _resealed_package(
        package,
        metadata=metadata,
        triples=tuple(triples),
    )


def _package(core_record_factory=_record):
    module = _science()
    triples = []
    for index, (role, schema) in enumerate(
        zip(EXPECTED_ROLES, EXPECTED_ROLE_SCHEMAS, strict=True)
    ):
        predecessor_index = None if index == 0 else index - 1
        if index in (3, 4, 5):
            predecessor_index = 2
        if index == 6:
            predecessor_index = None
        predecessor_envelopes = (
            ()
            if predecessor_index is None
            else (triples[predecessor_index].envelope.self_sha256,)
        )
        predecessor_pins = (
            ()
            if predecessor_index is None
            else (triples[predecessor_index].pin.self_sha256,)
        )
        if index == 6:
            predecessor_envelopes = tuple(
                sorted(triples[item].envelope.self_sha256 for item in (3, 4, 5))
            )
            predecessor_pins = tuple(
                sorted(triples[item].pin.self_sha256 for item in (3, 4, 5))
            )
        triples.append(
            module.CoreTripleView(
                role=role,
                artifact_schema_version=schema,
                artifact_version=1,
                artifact_logical_id=f"artifact:{index}",
                envelope_logical_id=f"envelope:{index}",
                pin_logical_id=f"pin:{index}",
                artifact_member_identity=f"core/{index}/artifact.json",
                envelope_member_identity=f"core/{index}/envelope.json",
                pin_member_identity=f"core/{index}/pin.json",
                artifact=core_record_factory(f"artifact-{index}", schema),
                envelope=core_record_factory(
                    f"envelope-{index}",
                    "ace.iclr2027.external_canonical_signature_envelope.vnext",
                ),
                pin=core_record_factory(
                    f"pin-{index}", "ace.iclr2027.external_vnext_artifact_pin.vnext"
                ),
                predecessor_envelope_sha256s=predecessor_envelopes,
                predecessor_pin_sha256s=predecessor_pins,
                authority=_authority(module, index),
            )
        )
    responsible_owner_approval = _approval_view(
        module,
        "owner",
        "responsible_owner",
        "owner:external",
        EXPECTED_ROLES[0],
        triples[0].artifact_logical_id,
        triples[0].artifact.file_sha256,
    )
    external_scientist_approval = _approval_view(
        module,
        "scientist",
        "external_scientist",
        "scientist:external",
        EXPECTED_ROLES[1],
        triples[1].artifact_logical_id,
        triples[1].artifact.file_sha256,
    )
    custodian_identities = ("custodian:a", "custodian:b", "custodian:c")
    custodian_approvals = tuple(
        _approval_view(
            module,
            f"custodian-{index}",
            "custodian",
            identity,
            EXPECTED_ROLES[0],
            triples[0].artifact_logical_id,
            triples[0].artifact.file_sha256,
        )
        for index, identity in enumerate(custodian_identities)
    )
    artifact_pin_approvals = tuple(
        _approval_view(
            module,
            f"pin-{index}",
            "artifact_pin",
            f"pin-approver:{index}",
            triple.role,
            triple.pin_logical_id,
            triple.pin.file_sha256,
        )
        for index, triple in enumerate(triples)
    )
    triples = [
        replace(
            triple,
            authority=replace(
                triple.authority,
                approval_member_identity=approval.approval_member_identity,
                approval_file_byte_count=approval.approval_file_byte_count,
                approval_sha256=approval.approval_file_sha256,
            ),
        )
        for triple, approval in zip(triples, artifact_pin_approvals, strict=True)
    ]

    joins = tuple(
        module.ReceiptJoinView(
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
    index_record = _record(
        "package-index", "ace.iclr2027.path_b_positive_intake_package_index.v1"
    )
    legacy_search_evidence = (
        module.LegacyEvidenceView(
            member_identity="evidence/legacy-search.json",
            record=_record(
                "legacy-search-evidence",
                "ace.iclr2027.legacy_search_evidence.vnext",
            ),
        ),
    )
    task7_custody = module.CustodyObjectView(
        member_identity="custody/task7-process-spec.md",
        file_byte_count=EXPECTED_CUSTODY_BYTE_COUNTS[0],
        file_sha256=EXPECTED_TASK7_PROCESS_SHA,
    )
    task5_custodies = tuple(
        module.CustodyObjectView(
            member_identity=f"custody/task5-parent-{index}.md",
            file_byte_count=file_byte_count,
            file_sha256=file_sha256,
        )
        for index, (file_byte_count, file_sha256) in enumerate(
            zip(
                EXPECTED_CUSTODY_BYTE_COUNTS[1:],
                EXPECTED_TASK5_PARENTS,
                strict=True,
            )
        )
    )
    pin_approval_refs = tuple(
        module.PinApprovalRefView(
            subject_role=triple.role,
            approval_member_identity=approval.approval_member_identity,
            approval_file_byte_count=approval.approval_file_byte_count,
            approval_file_sha256=approval.approval_file_sha256,
        )
        for triple, approval in zip(triples, artifact_pin_approvals, strict=True)
    )
    metadata = module.PackageIndexMetadata(
        index_record=index_record,
        index_version=1,
        package_generation=1,
        package_logical_id="package:path-b:alpha",
        task7_process_spec_custody_ref_sha256=EXPECTED_TASK7_PROCESS_SHA,
        task5_scientific_parent_custody_ref_sha256s=EXPECTED_TASK5_PARENTS,
        core_roles=EXPECTED_ROLES,
        referenced_members=(),
        pin_approval_refs=pin_approval_refs,
        canonical_core_record_count=21,
        artifact_count=7,
        envelope_count=7,
        pin_count=7,
        review_count=3,
        migration_receipt_pin_sha256=triples[-1].pin.file_sha256,
        responsible_owner_identity="owner:external",
        external_scientist_identity="scientist:external",
        custodian_identities=custodian_identities,
        responsible_owner_approval_member_identity=(
            responsible_owner_approval.approval_member_identity
        ),
        responsible_owner_approval_sha256=(
            responsible_owner_approval.approval_file_sha256
        ),
        external_scientist_approval_member_identity=(
            external_scientist_approval.approval_member_identity
        ),
        external_scientist_approval_sha256=(
            external_scientist_approval.approval_file_sha256
        ),
        custodian_approval_member_identities=tuple(
            approval.approval_member_identity for approval in custodian_approvals
        ),
        custodian_approval_sha256s=tuple(
            approval.approval_file_sha256 for approval in custodian_approvals
        ),
        legacy_search_evidence=legacy_search_evidence,
        task7_process_spec_custody=task7_custody,
        task5_scientific_parent_custodies=task5_custodies,
        responsible_owner_approval=responsible_owner_approval,
        external_scientist_approval=external_scientist_approval,
        custodian_approvals=custodian_approvals,
        artifact_pin_approvals=artifact_pin_approvals,
    )
    metadata = replace(
        metadata,
        referenced_members=_complete_referenced_inventory(
            module,
            metadata,
            tuple(triples),
        ),
    )
    metadata = replace(
        metadata,
        index_record=_sealed_index_record(_index_payload(metadata, tuple(triples))),
    )
    scientific = module.ScientificContractView(
        legacy_continuity=False,
        legacy_equivalence=False,
        thesis_scalars=EXPECTED_THESIS_SCALARS,
        policy_ids=EXPECTED_POLICY_IDS,
        endpoint_hierarchy=EXPECTED_ENDPOINT_HIERARCHY,
        kill_chain=EXPECTED_KILL_CHAIN,
    )
    return module.SyntheticPackageView(
        package_index=metadata,
        core_triples=tuple(triples),
        scientific_contract=scientific,
        receipt_predecessor_join=joins,
    )


def _receipt_join_for_triple(module, triple):
    return module.ReceiptJoinView(
        role=triple.role,
        artifact_file_sha256=triple.artifact.file_sha256,
        artifact_sha256=triple.artifact.self_sha256,
        envelope_file_sha256=triple.envelope.file_sha256,
        envelope_sha256=triple.envelope.self_sha256,
        pin_file_sha256=triple.pin.file_sha256,
        pin_sha256=triple.pin.self_sha256,
    )


def _with_one_fabricated_core_record(package, index: int, field: str):
    module = _science()
    triples = list(package.core_triples)
    original = getattr(triples[index], field)
    fabricated = replace(
        _fabricated_record(f"isolated-{index}-{field}", original.schema_version),
        self_sha256=original.self_sha256,
    )
    triples[index] = replace(triples[index], **{field: fabricated})
    metadata = package.package_index
    if index == 6 and field == "pin":
        metadata = replace(
            metadata,
            migration_receipt_pin_sha256=fabricated.file_sha256,
        )
    joins = list(package.receipt_predecessor_join)
    if index < 6:
        joins[index] = _receipt_join_for_triple(module, triples[index])
    attacked = _resealed_package(
        replace(package, receipt_predecessor_join=tuple(joins)),
        metadata=metadata,
        triples=triples,
    )
    if field == "pin":
        approval_ordinal = 2 + len(metadata.custodian_approvals) + index
        attacked = _replace_approval_at(
            attacked,
            approval_ordinal,
            subject_file_sha256=fabricated.file_sha256,
        )
    return attacked


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"missing literal assignment: {name}")


def _science_ast_boundary_violations(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("syntax-error",)
    expected_imports = (
        "from dataclasses import dataclass",
        "from hashlib import sha256",
        "from json import loads",
        (
            "from iclr2027.path_b_positive_intake_contract import "
            "EXTERNAL_ROLE_APPROVAL_SCHEMA, IntakeContractError, "
            "PACKAGE_INDEX_SCHEMA, PersistedRecord, parse_persisted_record, "
            "parse_self_hashed_record"
        ),
    )
    observed_imports = tuple(
        ast.unparse(node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    allowed_calls = {
        "IntakeContractError",
        "PinApprovalRefView",
        "ReferencedMemberView",
        "ReceiptJoinView",
        "_canonical_global_occurrences",
        "_complete_referenced_inventory",
        "_expected_receipt_join",
        "_fail",
        "_referenced_member",
        "_record_self_hash_field",
        "_require_package_view",
        "_require_record",
        "_require_sha256",
        "_require_visible_ascii",
        "_sha256_text",
        "_validate_approval_record",
        "_validate_custody_object",
        "_validate_exact_dag",
        "_validate_global_occurrence_census",
        "_validate_index_and_core",
        "_validate_legacy_evidence",
        "_validate_package_index_record_binding",
        "_validate_pin_approval_ref",
        "_validate_referenced_member",
        "_validate_role_authority",
        "_visible_ascii",
        "all",
        "any",
        "bool",
        "dataclass",
        "len",
        "loads",
        "ord",
        "parse_persisted_record",
        "parse_self_hashed_record",
        "record.raw_bytes.count",
        "record.raw_bytes.endswith",
        "require_exact_tuple",
        "require_globally_distinct",
        "set",
        "sha256",
        "sha256(record.raw_bytes).hexdigest",
        "sorted",
        "tuple",
        "type",
        "zip",
    }
    expected_public_classes = (
        "ScientificContractView",
        "ReferencedMemberView",
        "PinApprovalRefView",
        "LegacyEvidenceView",
        "CustodyObjectView",
        "ApprovalRecordView",
        "RoleAuthorityView",
        "CoreTripleView",
        "ReceiptJoinView",
        "PackageIndexMetadata",
        "SyntheticPackageView",
    )
    expected_public_functions = (
        "require_exact_tuple",
        "require_globally_distinct",
        "validate_frozen_scientific_contract",
        "validate_global_role_separation",
    )
    violations: list[str] = []
    index_core_functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_index_and_core"
    ]
    core_loops = (
        [
            node
            for node in ast.walk(index_core_functions[0])
            if isinstance(node, ast.For)
            and ast.unparse(node.target) == "triple"
            and ast.unparse(node.iter) == "package.core_triples"
        ]
        if len(index_core_functions) == 1
        else []
    )
    expected_core_bindings = {
        (
            "_require_record(triple.artifact, triple.artifact_schema_version, "
            "'core_artifact', "
            "_record_self_hash_field(triple.artifact_schema_version))"
        ),
        (
            "_require_record(triple.envelope, _ENVELOPE_SCHEMA, "
            "'core_envelope', 'envelope_sha256')"
        ),
        "_require_record(triple.pin, _PIN_SCHEMA, 'core_pin', 'pin_sha256')",
    }
    observed_core_bindings = (
        {
            ast.unparse(node)
            for node in ast.walk(core_loops[0])
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "_require_record"
        }
        if len(core_loops) == 1
        else set()
    )
    if observed_core_bindings != expected_core_bindings:
        violations.append("core-record-binding-drift")
    if observed_imports != expected_imports:
        violations.append("import-drift")
    public_classes = tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    )
    public_functions = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    if public_classes != expected_public_classes:
        violations.append("public-class-drift")
    if public_functions != expected_public_functions:
        violations.append("public-function-drift")
    top_level_assignments = tuple(
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    )
    if top_level_assignments != (
        "_PACKAGE_INDEX_SCHEMA",
        "_ENVELOPE_SCHEMA",
        "_PIN_SCHEMA",
        "_TASK7_PROCESS_SPEC_SHA256",
        "_TASK7_PROCESS_SPEC_BYTE_COUNT",
        "_TASK5_SCIENTIFIC_PARENT_SHA256S",
        "_TASK5_SCIENTIFIC_PARENT_BYTE_COUNTS",
        "_FROZEN_ROLES",
        "_FROZEN_ROLE_SCHEMAS",
        "_FROZEN_THESIS_SCALARS",
        "_FROZEN_POLICY_IDS",
        "_FROZEN_ENDPOINT_HIERARCHY",
        "_FROZEN_KILL_CHAIN",
    ):
        violations.append("module-assignment-drift")
    trusted_names = {
        "EXTERNAL_ROLE_APPROVAL_SCHEMA",
        "IntakeContractError",
        "PACKAGE_INDEX_SCHEMA",
        "PersistedRecord",
        "dataclass",
        "loads",
        "parse_persisted_record",
        "parse_self_hashed_record",
        "sha256",
        *expected_public_classes,
        *expected_public_functions,
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func) not in allowed_calls:
            violations.append(f"operation-drift:{ast.unparse(node.func)}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            violations.append(f"dunder-attribute-drift:{node.attr}")
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id in trusted_names
        ):
            violations.append(f"trusted-name-rebound:{node.id}")
        if isinstance(node, ast.arg) and node.arg in trusted_names:
            violations.append(f"trusted-name-shadowed:{node.arg}")
    return tuple(violations)


class PositiveIntakeScienceTests(unittest.TestCase):
    def _assert_science_rejected(self, package) -> None:
        module = _science()
        with self.assertRaises(module.IntakeContractError):
            module.validate_frozen_scientific_contract(package)

    def _assert_separation_rejected(self, package) -> None:
        module = _science()
        with self.assertRaises(module.IntakeContractError):
            module.validate_global_role_separation(package)

    def test_valid_exact_contract_and_role_separation_are_observational_only(
        self,
    ) -> None:
        module = _science()
        package = _package()
        self.assertIsNone(module.validate_frozen_scientific_contract(package))
        self.assertIsNone(module.validate_global_role_separation(package))

    def test_each_of_fifteen_thesis_scalar_positions_is_exact(self) -> None:
        package = _package()
        for index, (name, value) in enumerate(EXPECTED_THESIS_SCALARS):
            attacked = list(EXPECTED_THESIS_SCALARS)
            attacked[index] = (name, value + "_drift")
            with self.subTest(index=index, name=name):
                self._assert_science_rejected(
                    replace(
                        package,
                        scientific_contract=replace(
                            package.scientific_contract,
                            thesis_scalars=tuple(attacked),
                        ),
                    )
                )

    def test_each_policy_endpoint_and_kill_clause_position_is_exact(self) -> None:
        package = _package()
        cases = (
            ("policy_ids", EXPECTED_POLICY_IDS),
            ("endpoint_hierarchy", EXPECTED_ENDPOINT_HIERARCHY),
            ("kill_chain", EXPECTED_KILL_CHAIN),
        )
        for field, expected in cases:
            for index, value in enumerate(expected):
                attacked = list(expected)
                attacked[index] = value + "_drift"
                with self.subTest(field=field, index=index):
                    self._assert_science_rejected(
                        replace(
                            package,
                            scientific_contract=replace(
                                package.scientific_contract,
                                **{field: tuple(attacked)},
                            ),
                        )
                    )

    def test_legacy_flags_architecture_jci_swap_pooling_and_rescue_are_rejected(
        self,
    ) -> None:
        package = _package()
        for field in ("legacy_continuity", "legacy_equivalence"):
            with self.subTest(field=field):
                self._assert_science_rejected(
                    replace(
                        package,
                        scientific_contract=replace(
                            package.scientific_contract, **{field: True}
                        ),
                    )
                )

        swapped_scalars = list(EXPECTED_THESIS_SCALARS)
        swapped_scalars[2] = (
            "architecture_domain_role",
            EXPECTED_THESIS_SCALARS[3][1],
        )
        swapped_scalars[3] = ("jci_domain_role", EXPECTED_THESIS_SCALARS[2][1])
        self._assert_science_rejected(
            replace(
                package,
                scientific_contract=replace(
                    package.scientific_contract,
                    thesis_scalars=tuple(swapped_scalars),
                ),
            )
        )

        pooled = list(EXPECTED_THESIS_SCALARS)
        pooled[6] = ("cross_domain_pooling", "allowed")
        self._assert_science_rejected(
            replace(
                package,
                scientific_contract=replace(
                    package.scientific_contract, thesis_scalars=tuple(pooled)
                ),
            )
        )

        rescue = list(EXPECTED_KILL_CHAIN)
        rescue[3] = "architecture_failure_is_rescued_by_jci_pooling"
        self._assert_science_rejected(
            replace(
                package,
                scientific_contract=replace(
                    package.scientific_contract, kill_chain=tuple(rescue)
                ),
            )
        )

        survivors = list(EXPECTED_KILL_CHAIN)
        survivors[4], survivors[9] = survivors[9], survivors[4]
        self._assert_science_rejected(
            replace(
                package,
                scientific_contract=replace(
                    package.scientific_contract, kill_chain=tuple(survivors)
                ),
            )
        )

    def test_each_task5_parent_and_task7_or_memory_ancestry_are_exact(self) -> None:
        package = _package()
        for index, parent in enumerate(EXPECTED_TASK5_PARENTS):
            attacked = list(EXPECTED_TASK5_PARENTS)
            attacked[index] = _digest(f"wrong-parent-{index}")
            with self.subTest(index=index, parent=parent):
                self._assert_science_rejected(
                    replace(
                        package,
                        package_index=replace(
                            package.package_index,
                            task5_scientific_parent_custody_ref_sha256s=tuple(attacked),
                        ),
                    )
                )
        for hostile_parent in (
            EXPECTED_TASK7_PROCESS_SHA,
            _digest("ICLR_2027_ARCHITECTURE_DOMAIN_MEMORY.md"),
        ):
            with self.subTest(hostile_parent=hostile_parent):
                self._assert_science_rejected(
                    replace(
                        package,
                        package_index=replace(
                            package.package_index,
                            task5_scientific_parent_custody_ref_sha256s=(
                                *EXPECTED_TASK5_PARENTS,
                                hostile_parent,
                            ),
                        ),
                    )
                )

    def test_each_role_position_and_all_versions_are_closed(self) -> None:
        package = _package()
        for index, role in enumerate(EXPECTED_ROLES):
            attacked_roles = list(EXPECTED_ROLES)
            attacked_roles[index] = role + "_drift"
            with self.subTest(source="index", index=index):
                self._assert_science_rejected(
                    replace(
                        package,
                        package_index=replace(
                            package.package_index, core_roles=tuple(attacked_roles)
                        ),
                    )
                )
            attacked_triples = list(package.core_triples)
            attacked_triples[index] = replace(
                attacked_triples[index], role=role + "_drift"
            )
            with self.subTest(source="triple", index=index):
                self._assert_science_rejected(
                    replace(package, core_triples=tuple(attacked_triples))
                )

            attacked_triples[index] = replace(
                package.core_triples[index], artifact_version=2
            )
            with self.subTest(source="version", index=index):
                self._assert_science_rejected(
                    replace(package, core_triples=tuple(attacked_triples))
                )

        self._assert_science_rejected(
            replace(
                package,
                package_index=replace(package.package_index, index_version=2),
            )
        )

    def test_exact_census_schema_and_task7_process_separation_are_required(
        self,
    ) -> None:
        package = _package()
        attacks = (
            replace(
                package,
                package_index=replace(
                    package.package_index, canonical_core_record_count=20
                ),
            ),
            replace(
                package,
                package_index=replace(package.package_index, review_count=4),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    task7_process_spec_custody_ref_sha256=_digest("task7-drift"),
                ),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    index_record=replace(
                        package.package_index.index_record,
                        schema_version="ace.iclr2027.unsupported_index.v2",
                    ),
                ),
            ),
            replace(package, core_triples=package.core_triples[:-1]),
        )
        for index, attacked in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_science_rejected(attacked)

    def test_exact_dag_and_six_predecessor_receipt_join_have_no_self_reference(
        self,
    ) -> None:
        package = _package()
        triples = list(package.core_triples)
        triples[1] = replace(triples[1], predecessor_envelope_sha256s=())
        self._assert_science_rejected(replace(package, core_triples=tuple(triples)))

        receipt = package.core_triples[-1]
        self_join = _science().ReceiptJoinView(
            role=receipt.role,
            artifact_file_sha256=receipt.artifact.file_sha256,
            artifact_sha256=receipt.artifact.self_sha256,
            envelope_file_sha256=receipt.envelope.file_sha256,
            envelope_sha256=receipt.envelope.self_sha256,
            pin_file_sha256=receipt.pin.file_sha256,
            pin_sha256=receipt.pin.self_sha256,
        )
        self._assert_science_rejected(
            replace(
                package,
                receipt_predecessor_join=(
                    *package.receipt_predecessor_join,
                    self_join,
                ),
            )
        )

        joins = list(package.receipt_predecessor_join)
        joins[0] = replace(joins[0], pin_sha256=receipt.pin.self_sha256)
        self._assert_science_rejected(
            replace(package, receipt_predecessor_join=tuple(joins))
        )

    def test_shared_producer_package_is_rejected_by_occurrence_cardinality(
        self,
    ) -> None:
        package = _package()
        triples = list(package.core_triples)
        triples[1] = replace(
            triples[1],
            authority=replace(
                triples[1].authority,
                producer_package_identity=triples[
                    0
                ].authority.producer_package_identity,
            ),
        )
        self._assert_separation_rejected(replace(package, core_triples=tuple(triples)))

    def test_owner_scientist_alias_and_approval_digest_reuse_are_rejected(self) -> None:
        package = _package()
        self._assert_separation_rejected(
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    external_scientist_identity=package.package_index.responsible_owner_identity,
                ),
            )
        )
        self._assert_separation_rejected(
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    external_scientist_approval_sha256=(
                        package.package_index.responsible_owner_approval_sha256
                    ),
                ),
            )
        )

    def test_cross_role_logical_ids_are_globally_distinct(self) -> None:
        package = _package()
        for field in (
            "artifact_logical_id",
            "envelope_logical_id",
            "pin_logical_id",
        ):
            triples = list(package.core_triples)
            triples[1] = replace(triples[1], **{field: getattr(triples[0], field)})
            with self.subTest(field=field):
                self._assert_separation_rejected(
                    replace(package, core_triples=tuple(triples))
                )

    def test_global_distinctness_spans_authority_dimensions_not_only_each_set(
        self,
    ) -> None:
        package = _package()
        triples = list(package.core_triples)
        triples[1] = replace(
            triples[1],
            authority=replace(
                triples[1].authority,
                signing_key_id=triples[0].authority.actor_identity,
            ),
        )
        self._assert_separation_rejected(replace(package, core_triples=tuple(triples)))

    def test_package_and_logical_authority_occurrences_share_one_global_census(
        self,
    ) -> None:
        package = _package()
        artifact_to_actor = list(package.core_triples)
        artifact_to_actor[0] = replace(
            artifact_to_actor[0],
            artifact_logical_id=package.core_triples[1].authority.actor_identity,
        )
        pin_to_owner_approval = list(package.core_triples)
        pin_to_owner_approval[0] = replace(
            pin_to_owner_approval[0],
            pin_logical_id=(
                package.package_index.responsible_owner_approval_member_identity
            ),
        )
        attacks = (
            replace(package, core_triples=tuple(artifact_to_actor)),
            replace(package, core_triples=tuple(pin_to_owner_approval)),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    package_logical_id=package.core_triples[0].authority.actor_identity,
                ),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    package_logical_id=package.core_triples[0].artifact_logical_id,
                ),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    package_logical_id=(
                        package.core_triples[0].authority.producer_package_identity
                    ),
                ),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    package_logical_id=(
                        package.package_index.responsible_owner_approval_sha256
                    ),
                ),
            ),
        )
        for index, attacked in enumerate(attacks):
            with self.subTest(index=index):
                self._assert_separation_rejected(attacked)

    def test_test_owned_contract_precedes_cross_source_ast_alignment(self) -> None:
        frozen_scalars = _literal_assignment(FROZEN_PATH, "_FROZEN_ONE_THESIS_SCALARS")
        frozen_policies = _literal_assignment(FROZEN_PATH, "_POLICY_IDS")
        frozen_endpoints = _literal_assignment(FROZEN_PATH, "_ENDPOINT_HIERARCHY")
        frozen_kills = _literal_assignment(FROZEN_PATH, "_KILL_CHAIN")
        frozen_roles = tuple(_literal_assignment(FROZEN_PATH, "_ROLE_DOMAINS").keys())
        oracle_parent = _literal_assignment(ORACLE_PATH, "_E3_PARENT_FIELDS")
        oracle_shared = _literal_assignment(ORACLE_PATH, "_E3_SHARED_FIELDS")

        self.assertEqual(frozen_scalars, EXPECTED_THESIS_SCALARS)
        self.assertEqual(frozen_policies, EXPECTED_POLICY_IDS)
        self.assertEqual(frozen_endpoints, EXPECTED_ENDPOINT_HIERARCHY)
        self.assertEqual(frozen_kills, EXPECTED_KILL_CHAIN)
        self.assertEqual(frozen_roles, EXPECTED_ROLES)
        self.assertEqual(oracle_parent, EXPECTED_E3_PARENT_FIELDS)
        self.assertEqual(oracle_shared, EXPECTED_E3_SHARED_FIELDS)

        _science()
        self.assertEqual(
            _literal_assignment(SCIENCE_PATH, "_FROZEN_THESIS_SCALARS"),
            EXPECTED_THESIS_SCALARS,
        )
        self.assertEqual(
            _literal_assignment(SCIENCE_PATH, "_FROZEN_POLICY_IDS"),
            EXPECTED_POLICY_IDS,
        )
        self.assertEqual(
            _literal_assignment(SCIENCE_PATH, "_FROZEN_ENDPOINT_HIERARCHY"),
            EXPECTED_ENDPOINT_HIERARCHY,
        )
        self.assertEqual(
            _literal_assignment(SCIENCE_PATH, "_FROZEN_KILL_CHAIN"),
            EXPECTED_KILL_CHAIN,
        )

    def test_module_ast_has_no_io_dynamic_authority_or_source_reads(self) -> None:
        _science()
        tree = ast.parse(SCIENCE_PATH.read_text(encoding="utf-8"))
        allowed_import_roots = {
            "dataclasses",
            "hashlib",
            "iclr2027",
            "json",
            "typing",
        }
        forbidden_calls = {
            "open",
            "compile",
            "eval",
            "exec",
            "getattr",
            "setattr",
            "delattr",
            "hasattr",
            "__import__",
        }
        forbidden_names = {
            "Path",
            "os",
            "subprocess",
            "socket",
            "pickle",
            "marshal",
            "shelve",
            "importlib",
        }
        observed_imports = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                observed_imports.update(name.split(".", 1)[0] for name in names)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, forbidden_calls)
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, forbidden_names)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(
                    node.attr,
                    {"read_text", "read_bytes", "write_text", "write_bytes"},
                )
        self.assertTrue(observed_imports <= allowed_import_roots)


class TaskSevenScienceAdversarialTests(unittest.TestCase):
    def test_complete_index_projection_has_exact_typed_public_surface(self) -> None:
        module = _science()
        for class_name, expected_fields in EXPECTED_TYPED_VIEW_FIELDS.items():
            with self.subTest(class_name=class_name):
                self.assertTrue(
                    hasattr(module, class_name),
                    f"missing typed view: {class_name}",
                )
                view_type = getattr(module, class_name, None)
                if view_type is not None:
                    self.assertEqual(
                        tuple(field.name for field in fields(view_type)),
                        expected_fields,
                    )
        for view_type, expected_fields in (
            (module.RoleAuthorityView, EXPECTED_ROLE_AUTHORITY_FIELDS),
            (module.CoreTripleView, EXPECTED_CORE_TRIPLE_VIEW_FIELDS),
            (module.PackageIndexMetadata, EXPECTED_PACKAGE_INDEX_METADATA_FIELDS),
        ):
            with self.subTest(class_name=view_type.__name__):
                self.assertEqual(
                    tuple(field.name for field in fields(view_type)),
                    expected_fields,
                )

    def _assert_science_rejected(self, package) -> None:
        module = _science()
        with self.assertRaises(module.IntakeContractError):
            module.validate_frozen_scientific_contract(package)

    def _assert_separation_rejected(self, package) -> None:
        module = _science()
        with self.assertRaises(module.IntakeContractError):
            module.validate_global_role_separation(package)

    def test_design_complete_section_7_3_inventory_is_accepted(self) -> None:
        module = _science()
        package = _package()
        for validator in (
            module.validate_frozen_scientific_contract,
            module.validate_global_role_separation,
        ):
            with self.subTest(validator=validator.__name__):
                self._assert_validator_accepts(validator, package)

    def test_every_omitted_index_projection_field_is_bound_to_the_typed_view(
        self,
    ) -> None:
        package = _package()
        base_payload = _index_payload(package.package_index, package.core_triples)
        attacks = []

        generation = json.loads(json.dumps(base_payload))
        generation["package_generation"] = 2
        attacks.append(("package_generation", generation))

        for field in (
            "artifact_member_identity",
            "envelope_member_identity",
            "pin_member_identity",
        ):
            payload = json.loads(json.dumps(base_payload))
            payload["core_triples"][0][field] = f"core/0/rebound-{field}.json"
            attacks.append((f"core:{field}", payload))

        referenced_count = json.loads(json.dumps(base_payload))
        referenced_count["referenced_members"][0]["file_byte_count"] += 1
        attacks.append(("referenced:file_byte_count", referenced_count))

        pin_count = json.loads(json.dumps(base_payload))
        pin_count["pin_approval_refs"][0]["approval_file_byte_count"] += 1
        pin_member_identity = pin_count["pin_approval_refs"][0][
            "approval_member_identity"
        ]
        matching_pin_member = next(
            item
            for item in pin_count["referenced_members"]
            if item["member_kind"] == "pin_approval"
            and item["member_identity"] == pin_member_identity
        )
        matching_pin_member["file_byte_count"] += 1
        attacks.append(("pin_ref:approval_file_byte_count", pin_count))

        for family, payload in attacks:
            attacked_record = _sealed_index_record(payload)
            attacked = replace(
                package,
                package_index=replace(
                    package.package_index,
                    index_record=attacked_record,
                ),
            )
            with self.subTest(family=family, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(family=family, validator="separation"):
                self._assert_separation_rejected(attacked)

    def test_complete_referenced_inventory_rejects_every_missing_or_extra_row(
        self,
    ) -> None:
        module = _science()
        package = _package()
        members = package.package_index.referenced_members
        for index, member in enumerate(members):
            if member.member_kind == "pin_approval":
                continue
            observed = members[:index] + members[index + 1 :]
            attacked = _resealed_package(
                package,
                metadata=replace(
                    package.package_index,
                    referenced_members=observed,
                ),
            )
            family = f"missing:{index}:{member.member_kind}"
            with self.subTest(family=family, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(family=family, validator="separation"):
                self._assert_separation_rejected(attacked)

        extra = module.ReferencedMemberView(
            member_kind="legacy_search_evidence",
            member_identity="evidence/unbound-extra.json",
            file_byte_count=17,
            file_sha256=_digest("unbound-extra-inventory"),
        )
        attacked = _resealed_package(
            package,
            metadata=replace(
                package.package_index,
                referenced_members=(*members, extra),
            ),
        )
        with self.subTest(family="extra", validator="science"):
            self._assert_science_rejected(attacked)
        with self.subTest(family="extra", validator="separation"):
            self._assert_separation_rejected(attacked)

        duplicate = replace(
            package.package_index,
            referenced_members=(*members, members[0]),
        )
        with self.subTest(family="duplicate_physical_row"):
            with self.assertRaises(module.IntakeContractError):
                _resealed_package(package, metadata=duplicate)

    def test_every_approval_record_view_field_and_raw_record_is_bound(self) -> None:
        package = _package()
        approval = package.package_index.responsible_owner_approval
        malformed_raw = b'{"not":"an-approval"}\n'
        malformed_record = PersistedRecord(
            schema_version=EXTERNAL_ROLE_APPROVAL_SCHEMA.schema_version,
            raw_bytes=malformed_raw,
            canonical_body=malformed_raw[:-1],
            file_sha256=sha256(malformed_raw).hexdigest(),
            self_sha256=_digest("malformed-approval-self"),
        )
        attacks = (
            ("approval_member_identity", "approvals/rebound-owner.json"),
            ("approval_file_byte_count", approval.approval_file_byte_count + 1),
            ("approval_file_sha256", approval.approval_record.self_sha256),
            ("approval_record", malformed_record),
            ("approval_version", 2),
            ("approval_role", "external_scientist"),
            ("approver_identity", "owner:rebound"),
            ("subject_role", EXPECTED_ROLES[2]),
            ("subject_logical_id", "subject:rebound"),
            ("subject_file_sha256", _digest("subject:rebound")),
            ("decision", "reject"),
            ("approved_at_utc", "2026-08-31T00:00:00Z"),
            (
                "detached_message_domain",
                EXPECTED_APPROVAL_DOMAINS["external_scientist"],
            ),
            ("signature_algorithm", "caller-minted"),
            ("signing_key_id", "approval-key-id:rebound"),
            (
                "signing_public_key_member_identity",
                "approval-material/rebound/key.pub",
            ),
            ("signing_public_key_byte_count", 33),
            ("signing_public_key_sha256", _digest("approval-key:rebound")),
            (
                "detached_signature_member_identity",
                "approval-material/rebound/record.sig",
            ),
            ("detached_signature_byte_count", 65),
            ("detached_signature_sha256", _digest("approval-signature:rebound")),
        )
        for field, value in attacks:
            attacked = replace(
                package,
                package_index=replace(
                    package.package_index,
                    responsible_owner_approval=replace(
                        approval,
                        **{field: value},
                    ),
                ),
            )
            with self.subTest(field=field, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(field=field, validator="separation"):
                self._assert_separation_rejected(attacked)

    def test_approval_record_censuses_are_exact_and_aligned(self) -> None:
        package = _package()
        index = package.package_index
        attacks = (
            (
                "missing_custodian_approval",
                replace(index, custodian_approvals=index.custodian_approvals[:-1]),
            ),
            (
                "reversed_custodian_approvals",
                replace(
                    index,
                    custodian_approvals=tuple(reversed(index.custodian_approvals)),
                ),
            ),
            (
                "extra_custodian_approval",
                replace(
                    index,
                    custodian_approvals=(
                        *index.custodian_approvals,
                        index.custodian_approvals[0],
                    ),
                ),
            ),
            (
                "missing_artifact_pin_approval",
                replace(
                    index,
                    artifact_pin_approvals=index.artifact_pin_approvals[:-1],
                ),
            ),
            (
                "reversed_artifact_pin_approvals",
                replace(
                    index,
                    artifact_pin_approvals=tuple(
                        reversed(index.artifact_pin_approvals)
                    ),
                ),
            ),
            (
                "extra_artifact_pin_approval",
                replace(
                    index,
                    artifact_pin_approvals=(
                        *index.artifact_pin_approvals,
                        index.artifact_pin_approvals[0],
                    ),
                ),
            ),
        )
        for family, attacked_index in attacks:
            attacked = replace(package, package_index=attacked_index)
            with self.subTest(family=family, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(family=family, validator="separation"):
                self._assert_separation_rejected(attacked)

    def test_legacy_evidence_is_nonempty_variable_and_exactly_bound(self) -> None:
        module = _science()
        package = _package()
        index = package.package_index
        original = index.legacy_search_evidence[0]
        attacks = (
            ("empty", ()),
            ("duplicate", (original, original)),
            (
                "member_identity",
                (replace(original, member_identity="evidence/rebound.json"),),
            ),
            (
                "record_file_hash",
                (
                    replace(
                        original,
                        record=replace(
                            original.record,
                            file_sha256=_digest("wrong-legacy-file-hash"),
                        ),
                    ),
                ),
            ),
        )
        for family, evidence in attacks:
            attacked = replace(
                package,
                package_index=replace(index, legacy_search_evidence=evidence),
            )
            with self.subTest(family=family, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(family=family, validator="separation"):
                self._assert_separation_rejected(attacked)

        second = module.LegacyEvidenceView(
            member_identity="evidence/legacy-search-2.json",
            record=_record(
                "legacy-search-evidence-2",
                "ace.iclr2027.legacy_search_evidence.vnext",
            ),
        )
        expanded = replace(
            index,
            legacy_search_evidence=(original, second),
        )
        expanded = replace(
            expanded,
            referenced_members=_complete_referenced_inventory(
                module,
                expanded,
                package.core_triples,
            ),
        )
        expanded_package = _resealed_package(package, metadata=expanded)
        for validator in (
            module.validate_frozen_scientific_contract,
            module.validate_global_role_separation,
        ):
            with self.subTest(family="two_evidence_positive", validator=validator):
                self._assert_validator_accepts(validator, expanded_package)

    def test_custody_objects_are_exactly_ordered_and_bound_to_index_refs(self) -> None:
        package = _package()
        index = package.package_index
        task7 = index.task7_process_spec_custody
        task5 = index.task5_scientific_parent_custodies
        attacks = (
            (
                "task7_identity",
                replace(
                    index,
                    task7_process_spec_custody=replace(
                        task7,
                        member_identity="custody/rebound-task7.md",
                    ),
                ),
            ),
            (
                "task7_count",
                replace(
                    index,
                    task7_process_spec_custody=replace(
                        task7,
                        file_byte_count=task7.file_byte_count + 1,
                    ),
                ),
            ),
            (
                "task7_hash",
                replace(
                    index,
                    task7_process_spec_custody=replace(
                        task7,
                        file_sha256=_digest("wrong-task7-custody"),
                    ),
                ),
            ),
            (
                "task5_count",
                replace(
                    index,
                    task5_scientific_parent_custodies=(
                        replace(task5[0], file_byte_count=task5[0].file_byte_count + 1),
                        *task5[1:],
                    ),
                ),
            ),
            (
                "task5_hash",
                replace(
                    index,
                    task5_scientific_parent_custodies=(
                        replace(task5[0], file_sha256=_digest("wrong-task5-custody")),
                        *task5[1:],
                    ),
                ),
            ),
            (
                "task5_reverse",
                replace(
                    index,
                    task5_scientific_parent_custodies=tuple(reversed(task5)),
                ),
            ),
            (
                "task5_missing",
                replace(index, task5_scientific_parent_custodies=task5[:-1]),
            ),
            (
                "task5_extra",
                replace(index, task5_scientific_parent_custodies=(*task5, task5[0])),
            ),
        )
        for family, attacked_index in attacks:
            attacked = replace(package, package_index=attacked_index)
            with self.subTest(family=family, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(family=family, validator="separation"):
                self._assert_separation_rejected(attacked)

    def test_core_authority_member_counts_are_bound_to_inventory_rows(self) -> None:
        package = _package()
        triple = package.core_triples[0]
        count_fields = (
            "signing_public_key_byte_count",
            "detached_signature_byte_count",
            "verifier_executable_byte_count",
            "platform_signature_byte_count",
            "rotation_byte_count",
            "approval_file_byte_count",
        )
        for field in count_fields:
            attacked_triple = replace(
                triple,
                authority=replace(
                    triple.authority,
                    **{field: getattr(triple.authority, field) + 1},
                ),
            )
            attacked = replace(
                package,
                core_triples=(attacked_triple, *package.core_triples[1:]),
            )
            with self.subTest(field=field, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(field=field, validator="separation"):
                self._assert_separation_rejected(attacked)

    def test_artifact_pin_approval_subject_joins_its_matching_core_pin(self) -> None:
        module = _science()
        package = _package()
        index = package.package_index
        wrong_subject = package.core_triples[1]
        attacked_approval = _resealed_approval_view(
            index.artifact_pin_approvals[0],
            subject_role=wrong_subject.role,
            subject_logical_id=wrong_subject.pin_logical_id,
            subject_file_sha256=wrong_subject.pin.file_sha256,
        )
        approvals = (
            attacked_approval,
            *index.artifact_pin_approvals[1:],
        )
        attacked_triple = replace(
            package.core_triples[0],
            authority=replace(
                package.core_triples[0].authority,
                approval_member_identity=attacked_approval.approval_member_identity,
                approval_file_byte_count=attacked_approval.approval_file_byte_count,
                approval_sha256=attacked_approval.approval_file_sha256,
            ),
        )
        triples = (attacked_triple, *package.core_triples[1:])
        pin_refs = (
            module.PinApprovalRefView(
                subject_role=attacked_triple.role,
                approval_member_identity=attacked_approval.approval_member_identity,
                approval_file_byte_count=attacked_approval.approval_file_byte_count,
                approval_file_sha256=attacked_approval.approval_file_sha256,
            ),
            *index.pin_approval_refs[1:],
        )
        metadata = replace(
            index,
            artifact_pin_approvals=approvals,
            pin_approval_refs=pin_refs,
        )
        metadata = replace(
            metadata,
            referenced_members=_complete_referenced_inventory(
                module,
                metadata,
                triples,
            ),
        )
        attacked = _resealed_package(
            package,
            metadata=metadata,
            triples=triples,
        )
        with self.subTest(validator="science"):
            self._assert_science_rejected(attacked)
        with self.subTest(validator="separation"):
            self._assert_separation_rejected(attacked)

    def test_non_pin_approval_subjects_have_no_invented_semantic_target(self) -> None:
        module = _science()
        package = _package()
        index = package.package_index
        owner = _resealed_approval_view(
            index.responsible_owner_approval,
            subject_role=EXPECTED_ROLES[4],
            subject_logical_id="owner-subject:independently-frozen",
            subject_file_sha256=_digest("owner-subject:independently-frozen"),
        )
        scientist = _resealed_approval_view(
            index.external_scientist_approval,
            subject_role=EXPECTED_ROLES[5],
            subject_logical_id="scientist-subject:independently-frozen",
            subject_file_sha256=_digest("scientist-subject:independently-frozen"),
        )
        custodians = tuple(
            _resealed_approval_view(
                approval,
                subject_role=EXPECTED_ROLES[(position + 1) % len(EXPECTED_ROLES)],
                subject_logical_id=f"custodian-subject:{position}",
                subject_file_sha256=_digest(f"custodian-subject:{position}"),
            )
            for position, approval in enumerate(index.custodian_approvals)
        )
        metadata = replace(
            index,
            responsible_owner_approval=owner,
            responsible_owner_approval_sha256=owner.approval_file_sha256,
            external_scientist_approval=scientist,
            external_scientist_approval_sha256=scientist.approval_file_sha256,
            custodian_approvals=custodians,
            custodian_approval_sha256s=tuple(
                approval.approval_file_sha256 for approval in custodians
            ),
        )
        metadata = replace(
            metadata,
            referenced_members=_complete_referenced_inventory(
                module,
                metadata,
                package.core_triples,
            ),
        )
        attacked = _resealed_package(package, metadata=metadata)
        for validator in (
            module.validate_frozen_scientific_contract,
            module.validate_global_role_separation,
        ):
            with self.subTest(validator=validator.__name__):
                self._assert_validator_accepts(validator, attacked)

    def test_package_generation_is_variable_positive_but_exactly_bound(self) -> None:
        module = _science()
        package = _package()
        coherent = _with_rebound_index(package, package_generation=2)
        for validator in (
            module.validate_frozen_scientific_contract,
            module.validate_global_role_separation,
        ):
            with self.subTest(family="coherent_positive", validator=validator):
                self._assert_validator_accepts(validator, coherent)

        mismatched = replace(
            package,
            package_index=replace(package.package_index, package_generation=2),
        )
        with self.subTest(family="view_only", validator="science"):
            self._assert_science_rejected(mismatched)
        with self.subTest(family="view_only", validator="separation"):
            self._assert_separation_rejected(mismatched)

    def test_index_projection_rejects_value_equal_untyped_rows(self) -> None:
        package = _package()
        index = package.package_index

        def untyped(value):
            return SimpleNamespace(
                **{field.name: getattr(value, field.name) for field in fields(value)}
            )

        attacks = []
        referenced = list(index.referenced_members)
        referenced[0] = untyped(referenced[0])
        attacks.append(replace(index, referenced_members=tuple(referenced)))

        pin_refs = list(index.pin_approval_refs)
        pin_refs[0] = untyped(pin_refs[0])
        attacks.append(replace(index, pin_approval_refs=tuple(pin_refs)))

        evidence = list(index.legacy_search_evidence)
        evidence[0] = untyped(evidence[0])
        attacks.append(replace(index, legacy_search_evidence=tuple(evidence)))
        attacks.append(
            replace(
                index,
                task7_process_spec_custody=untyped(index.task7_process_spec_custody),
            )
        )

        custodians = list(index.custodian_approvals)
        custodians[0] = untyped(custodians[0])
        attacks.append(replace(index, custodian_approvals=tuple(custodians)))

        pin_approvals = list(index.artifact_pin_approvals)
        pin_approvals[0] = untyped(pin_approvals[0])
        attacks.append(replace(index, artifact_pin_approvals=tuple(pin_approvals)))

        for attack_index, metadata in enumerate(attacks):
            attacked = _resealed_package(package, metadata=metadata)
            with self.subTest(attack=attack_index, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(attack=attack_index, validator="separation"):
                self._assert_separation_rejected(attacked)

    def _assert_validator_accepts(self, validator, package) -> None:
        module = _science()
        try:
            result = validator(package)
        except module.IntakeContractError as error:
            self.fail(f"valid aligned custodian census rejected: {error}")
        self.assertIsNone(result)

    def test_custodian_census_accepts_any_nonempty_aligned_cardinality(
        self,
    ) -> None:
        module = _science()
        package = _package()
        for count in (1, 2, 4):
            identities = tuple(f"custodian:aligned:{index}" for index in range(count))
            approvals = tuple(
                _approval_view(
                    module,
                    f"aligned-custodian-{index}",
                    "custodian",
                    identity,
                    EXPECTED_ROLES[0],
                    package.core_triples[0].artifact_logical_id,
                    package.core_triples[0].artifact.file_sha256,
                )
                for index, identity in enumerate(identities)
            )
            metadata = replace(
                package.package_index,
                custodian_identities=identities,
                custodian_approval_member_identities=tuple(
                    approval.approval_member_identity for approval in approvals
                ),
                custodian_approval_sha256s=tuple(
                    approval.approval_file_sha256 for approval in approvals
                ),
                custodian_approvals=approvals,
            )
            metadata = replace(
                metadata,
                referenced_members=_complete_referenced_inventory(
                    module,
                    metadata,
                    package.core_triples,
                ),
            )
            aligned = _resealed_package(package, metadata=metadata)
            with self.subTest(count=count, validator="science"):
                self._assert_validator_accepts(
                    module.validate_frozen_scientific_contract, aligned
                )
            with self.subTest(count=count, validator="separation"):
                self._assert_validator_accepts(
                    module.validate_global_role_separation, aligned
                )

    def test_custodian_census_rejects_empty_misaligned_and_malformed_values(
        self,
    ) -> None:
        package = _package()
        identities = ("custodian:aligned:0", "custodian:aligned:1")
        approval_members = (
            "approvals/custodian-aligned-0.json",
            "approvals/custodian-aligned-1.json",
        )
        approval_hashes = (
            _digest("approval:custodian:aligned:0"),
            _digest("approval:custodian:aligned:1"),
        )
        attacks = (
            ((), (), ()),
            (identities[:1], approval_members, approval_hashes),
            (identities, approval_members[:1], approval_hashes),
            (identities, approval_members, approval_hashes[:1]),
            (identities[:1], approval_members, (*approval_hashes, _digest("extra"))),
            (list(identities), approval_members, approval_hashes),
            ((identities[0], identities[0]), approval_members, approval_hashes),
            (identities, ("", approval_members[1]), approval_hashes),
            (identities, approval_members, ("not-a-sha256", approval_hashes[1])),
        )
        for index, (observed_ids, observed_members, observed_hashes) in enumerate(
            attacks
        ):
            attacked = replace(
                package,
                package_index=replace(
                    package.package_index,
                    custodian_identities=observed_ids,
                    custodian_approval_member_identities=observed_members,
                    custodian_approval_sha256s=observed_hashes,
                ),
            )
            with self.subTest(index=index):
                self._assert_separation_rejected(attacked)

    def test_every_scientific_scalar_list_position_and_ancestry_attack_rejects(
        self,
    ) -> None:
        package = _package()
        for index, (name, value) in enumerate(EXPECTED_THESIS_SCALARS):
            mutations = (
                (
                    *EXPECTED_THESIS_SCALARS[:index],
                    (name + "_drift", value),
                    *EXPECTED_THESIS_SCALARS[index + 1 :],
                ),
                (
                    *EXPECTED_THESIS_SCALARS[:index],
                    (name, value + "_drift"),
                    *EXPECTED_THESIS_SCALARS[index + 1 :],
                ),
                (
                    *EXPECTED_THESIS_SCALARS[:index],
                    *EXPECTED_THESIS_SCALARS[index + 1 :],
                ),
            )
            for kind, attacked in zip(
                ("name", "value", "delete"), mutations, strict=True
            ):
                with self.subTest(family="thesis_scalar", index=index, kind=kind):
                    self._assert_science_rejected(
                        replace(
                            package,
                            scientific_contract=replace(
                                package.scientific_contract,
                                thesis_scalars=attacked,
                            ),
                        )
                    )

        list_cases = (
            ("policy_ids", EXPECTED_POLICY_IDS),
            ("endpoint_hierarchy", EXPECTED_ENDPOINT_HIERARCHY),
            ("kill_chain", EXPECTED_KILL_CHAIN),
        )
        for field, expected in list_cases:
            for index, value in enumerate(expected):
                attacks = (
                    (*expected[:index], value + "_drift", *expected[index + 1 :]),
                    (*expected[:index], *expected[index + 1 :]),
                )
                for kind, attacked in zip(("value", "delete"), attacks, strict=True):
                    with self.subTest(family=field, index=index, kind=kind):
                        self._assert_science_rejected(
                            replace(
                                package,
                                scientific_contract=replace(
                                    package.scientific_contract,
                                    **{field: attacked},
                                ),
                            )
                        )
            reordered = (*expected[1:], expected[0])
            duplicated = (*expected[:-1], expected[0])
            for kind, attacked in (("reorder", reordered), ("duplicate", duplicated)):
                with self.subTest(family=field, kind=kind):
                    self._assert_science_rejected(
                        replace(
                            package,
                            scientific_contract=replace(
                                package.scientific_contract,
                                **{field: attacked},
                            ),
                        )
                    )

        hostile_parents = (
            EXPECTED_TASK7_PROCESS_SHA,
            _digest("ICLR_2027_ARCHITECTURE_DOMAIN_MEMORY.md"),
        )
        for index in range(3):
            for hostile in hostile_parents:
                parents = list(EXPECTED_TASK5_PARENTS)
                parents[index] = hostile
                with self.subTest(family="ancestry", index=index, hostile=hostile):
                    self._assert_science_rejected(
                        replace(
                            package,
                            package_index=replace(
                                package.package_index,
                                task5_scientific_parent_custody_ref_sha256s=tuple(
                                    parents
                                ),
                            ),
                        )
                    )

    def test_all_counts_versions_roles_and_dag_rows_reject_bool_self_reverse_cycles(
        self,
    ) -> None:
        package = _package()
        count_expectations = (
            ("canonical_core_record_count", 21),
            ("artifact_count", 7),
            ("envelope_count", 7),
            ("pin_count", 7),
            ("review_count", 3),
        )
        for field, expected in count_expectations:
            for value in (True, expected - 1, expected + 1):
                with self.subTest(family="count", field=field, value=value):
                    self._assert_science_rejected(
                        replace(
                            package,
                            package_index=replace(
                                package.package_index,
                                **{field: value},
                            ),
                        )
                    )

        for index in range(7):
            triples = list(package.core_triples)
            triples[index] = replace(
                triples[index],
                predecessor_envelope_sha256s=(triples[index].envelope.self_sha256,),
            )
            with self.subTest(family="dag_self", edge="envelope", index=index):
                self._assert_science_rejected(
                    replace(package, core_triples=tuple(triples))
                )

            triples = list(package.core_triples)
            triples[index] = replace(
                triples[index],
                predecessor_pin_sha256s=(triples[index].pin.self_sha256,),
            )
            with self.subTest(family="dag_self", edge="pin", index=index):
                self._assert_science_rejected(
                    replace(package, core_triples=tuple(triples))
                )

        triples = list(package.core_triples)
        triples[0] = replace(
            triples[0],
            predecessor_envelope_sha256s=(triples[1].envelope.self_sha256,),
            predecessor_pin_sha256s=(triples[1].pin.self_sha256,),
        )
        self._assert_science_rejected(replace(package, core_triples=tuple(triples)))

        duplicate_roles = list(package.core_triples)
        duplicate_roles[1] = replace(duplicate_roles[1], role=duplicate_roles[0].role)
        self._assert_science_rejected(
            replace(package, core_triples=tuple(duplicate_roles))
        )
        future_version = list(package.core_triples)
        future_version[2] = replace(future_version[2], artifact_version=2)
        self._assert_science_rejected(
            replace(package, core_triples=tuple(future_version))
        )

    def test_receipt_exact_six_predecessor_join_mutation_census_rejects(self) -> None:
        package = _package()
        join_fields = (
            "role",
            "artifact_file_sha256",
            "artifact_sha256",
            "envelope_file_sha256",
            "envelope_sha256",
            "pin_file_sha256",
            "pin_sha256",
        )
        for index, join in enumerate(package.receipt_predecessor_join):
            for field in join_fields:
                joins = list(package.receipt_predecessor_join)
                joins[index] = replace(join, **{field: getattr(join, field) + "_drift"})
                with self.subTest(index=index, field=field):
                    self._assert_science_rejected(
                        replace(package, receipt_predecessor_join=tuple(joins))
                    )
            omitted = (
                *package.receipt_predecessor_join[:index],
                *package.receipt_predecessor_join[index + 1 :],
            )
            with self.subTest(index=index, field="omitted"):
                self._assert_science_rejected(
                    replace(package, receipt_predecessor_join=omitted)
                )

        self._assert_science_rejected(
            replace(
                package,
                receipt_predecessor_join=tuple(
                    reversed(package.receipt_predecessor_join)
                ),
            )
        )
        receipt = package.core_triples[-1]
        self_join = _science().ReceiptJoinView(
            role=receipt.role,
            artifact_file_sha256=receipt.artifact.file_sha256,
            artifact_sha256=receipt.artifact.self_sha256,
            envelope_file_sha256=receipt.envelope.file_sha256,
            envelope_sha256=receipt.envelope.self_sha256,
            pin_file_sha256=receipt.pin.file_sha256,
            pin_sha256=receipt.pin.self_sha256,
        )
        self._assert_science_rejected(
            replace(
                package,
                receipt_predecessor_join=(
                    *package.receipt_predecessor_join,
                    self_join,
                ),
            )
        )

    def test_every_role_authority_rotation_and_index_occurrence_is_global(self) -> None:
        package = _package()
        authority_fields = (
            "actor_identity",
            "producer_package_identity",
            "signing_key_id",
            "signing_public_key_member_identity",
            "signing_public_key_sha256",
            "detached_signature_member_identity",
            "detached_signature_sha256",
            "verifier_package_identity",
            "verifier_executable_member_identity",
            "verifier_executable_sha256",
            "platform_signature_member_identity",
            "platform_signature_sha256",
            "rotation_member_identity",
            "rotation_sha256",
            "approval_member_identity",
            "approval_sha256",
        )
        collision = package.package_index.package_logical_id
        for triple_index in range(7):
            for field in authority_fields:
                triples = list(package.core_triples)
                triples[triple_index] = replace(
                    triples[triple_index],
                    authority=replace(
                        triples[triple_index].authority,
                        **{field: collision},
                    ),
                )
                with self.subTest(
                    family="authority_occurrence",
                    triple=triple_index,
                    field=field,
                ):
                    self._assert_separation_rejected(
                        replace(package, core_triples=tuple(triples))
                    )

            for field in (
                "artifact_logical_id",
                "envelope_logical_id",
                "pin_logical_id",
            ):
                triples = list(package.core_triples)
                triples[triple_index] = replace(
                    triples[triple_index],
                    **{field: collision},
                )
                with self.subTest(
                    family="logical_occurrence",
                    triple=triple_index,
                    field=field,
                ):
                    self._assert_separation_rejected(
                        replace(package, core_triples=tuple(triples))
                    )

        index_scalar_fields = (
            "responsible_owner_identity",
            "external_scientist_identity",
            "responsible_owner_approval_member_identity",
            "responsible_owner_approval_sha256",
            "external_scientist_approval_member_identity",
            "external_scientist_approval_sha256",
        )
        for field in index_scalar_fields:
            with self.subTest(family="index_occurrence", field=field):
                self._assert_separation_rejected(
                    replace(
                        package,
                        package_index=replace(
                            package.package_index,
                            **{field: collision},
                        ),
                    )
                )
        index_tuple_fields = (
            "custodian_identities",
            "custodian_approval_member_identities",
            "custodian_approval_sha256s",
        )
        for field in index_tuple_fields:
            values = getattr(package.package_index, field)
            for index in range(len(values)):
                attacked = list(values)
                attacked[index] = collision
                with self.subTest(family="index_occurrence", field=field, index=index):
                    self._assert_separation_rejected(
                        replace(
                            package,
                            package_index=replace(
                                package.package_index,
                                **{field: tuple(attacked)},
                            ),
                        )
                    )

    def test_canonical_occurrence_census_has_exact_variable_formula_and_mirrors(
        self,
    ) -> None:
        module = _science()
        for custodian_count, evidence_count in ((1, 1), (2, 1), (4, 1), (3, 2)):
            package = _package_with_cardinalities(
                custodian_count,
                evidence_count,
            )
            index = package.package_index
            approvals = _approval_views(index)
            occurrences = _canonical_occurrence_census(package)
            expected_count = 272 + 9 * custodian_count + 2 * evidence_count
            with self.subTest(
                family="formula",
                custodians=custodian_count,
                evidence=evidence_count,
            ):
                self.assertEqual(len(occurrences), expected_count)
                self.assertEqual(len(set(occurrences)), expected_count)

            self.assertEqual(
                tuple(
                    approval.approver_identity
                    for approval in approvals[: 2 + custodian_count]
                ),
                (
                    index.responsible_owner_identity,
                    index.external_scientist_identity,
                    *index.custodian_identities,
                ),
            )
            for triple, approval, pin_ref in zip(
                package.core_triples,
                index.artifact_pin_approvals,
                index.pin_approval_refs,
                strict=True,
            ):
                self.assertEqual(
                    (
                        approval.subject_role,
                        approval.subject_logical_id,
                        approval.subject_file_sha256,
                    ),
                    (triple.role, triple.pin_logical_id, triple.pin.file_sha256),
                )
                self.assertEqual(
                    (
                        pin_ref.approval_member_identity,
                        pin_ref.approval_file_byte_count,
                        pin_ref.approval_file_sha256,
                    ),
                    (
                        approval.approval_member_identity,
                        approval.approval_file_byte_count,
                        approval.approval_file_sha256,
                    ),
                )
            for validator in (
                module.validate_frozen_scientific_contract,
                module.validate_global_role_separation,
            ):
                with self.subTest(
                    family="mirror_positive",
                    custodians=custodian_count,
                    evidence=evidence_count,
                    validator=validator.__name__,
                ):
                    self._assert_validator_accepts(validator, package)

    def test_every_new_approval_authority_occurrence_is_globally_distinct(
        self,
    ) -> None:
        module = _science()
        package = _package()
        approvals = _approval_views(package.package_index)
        core_signing_key_id = package.core_triples[0].authority.signing_key_id

        for ordinal in range(len(approvals)):
            attacked = _replace_approval_at(
                package,
                ordinal,
                signing_key_id=core_signing_key_id,
            )
            for validator in (
                module.validate_frozen_scientific_contract,
                module.validate_global_role_separation,
            ):
                with self.subTest(
                    family="approval_signing_key_id",
                    ordinal=ordinal,
                    validator=validator.__name__,
                ):
                    with self.assertRaises(module.IntakeContractError):
                        validator(attacked)

        for ordinal, approval in enumerate(approvals):
            triples = list(package.core_triples)
            triples[0] = replace(
                triples[0],
                authority=replace(
                    triples[0].authority,
                    signing_key_id=approval.approval_record.self_sha256,
                ),
            )
            attacked = replace(package, core_triples=tuple(triples))
            for validator in (
                module.validate_frozen_scientific_contract,
                module.validate_global_role_separation,
            ):
                with self.subTest(
                    family="approval_self_digest",
                    ordinal=ordinal,
                    validator=validator.__name__,
                ):
                    with self.assertRaises(module.IntakeContractError):
                        validator(attacked)

        pin_offset = 2 + len(package.package_index.custodian_approvals)
        for position in range(len(package.package_index.artifact_pin_approvals)):
            attacked = _replace_approval_at(
                package,
                pin_offset + position,
                approver_identity=package.package_index.responsible_owner_identity,
            )
            for validator in (
                module.validate_frozen_scientific_contract,
                module.validate_global_role_separation,
            ):
                with self.subTest(
                    family="pin_approver_identity",
                    position=position,
                    validator=validator.__name__,
                ):
                    with self.assertRaises(module.IntakeContractError):
                        validator(attacked)

    def test_new_approval_occurrences_reject_cross_approval_and_dimension_aliases(
        self,
    ) -> None:
        module = _science()
        package = _package()
        index = package.package_index
        approvals = _approval_views(index)
        pin_offset = 2 + len(index.custodian_approvals)
        attacks = (
            _replace_approval_at(
                package,
                0,
                signing_key_id=approvals[1].signing_key_id,
            ),
            _replace_approval_at(
                package,
                0,
                signing_key_id=approvals[1].approval_record.self_sha256,
            ),
            _replace_approval_at(
                package,
                pin_offset,
                approver_identity=index.artifact_pin_approvals[1].approver_identity,
            ),
            _replace_approval_at(
                package,
                pin_offset,
                approver_identity=approvals[0].signing_key_id,
            ),
        )
        for attack_index, attacked in enumerate(attacks):
            for validator in (
                module.validate_frozen_scientific_contract,
                module.validate_global_role_separation,
            ):
                with self.subTest(
                    attack=attack_index,
                    validator=validator.__name__,
                ):
                    with self.assertRaises(module.IntakeContractError):
                        validator(attacked)

    def test_every_core_file_and_self_hash_occurrence_is_distinct(self) -> None:
        package = _package()
        coordinates = tuple(
            (triple_index, record_field, hash_field)
            for triple_index in range(7)
            for record_field in ("artifact", "envelope", "pin")
            for hash_field in ("file_sha256", "self_sha256")
        )
        first_coordinate = coordinates[0]
        first_record = getattr(
            package.core_triples[first_coordinate[0]], first_coordinate[1]
        )
        anchor = getattr(first_record, first_coordinate[2])
        alternate = package.core_triples[0].artifact.self_sha256
        for coordinate in coordinates:
            triple_index, record_field, hash_field = coordinate
            triples = list(package.core_triples)
            record = getattr(triples[triple_index], record_field)
            collision = alternate if coordinate == first_coordinate else anchor
            triples[triple_index] = replace(
                triples[triple_index],
                **{record_field: replace(record, **{hash_field: collision})},
            )
            with self.subTest(
                triple=triple_index,
                record=record_field,
                hash=hash_field,
            ):
                self._assert_science_rejected(
                    replace(package, core_triples=tuple(triples))
                )

    def test_view_leaf_types_custodian_cardinality_and_record_binding_reject(
        self,
    ) -> None:
        package = _package()
        triples = list(package.core_triples)
        triples[0] = replace(triples[0], artifact_logical_id="")
        empty_artifact_identity = replace(package, core_triples=tuple(triples))

        triples = list(package.core_triples)
        triples[0] = replace(
            triples[0],
            authority=replace(triples[0].authority, actor_identity=7),
        )
        integer_actor = replace(package, core_triples=tuple(triples))

        triples = list(package.core_triples)
        triples[0] = replace(
            triples[0],
            authority=replace(
                triples[0].authority,
                signing_public_key_sha256="not-a-sha256",
            ),
        )
        malformed_authority_hash = replace(package, core_triples=tuple(triples))

        triples = list(package.core_triples)
        triples[0] = replace(
            triples[0],
            authority=replace(triples[0].authority, rotation_member_identity=""),
        )
        empty_rotation_member = replace(package, core_triples=tuple(triples))

        separation_attacks = (
            replace(
                package,
                package_index=replace(package.package_index, package_logical_id=""),
            ),
            empty_artifact_identity,
            integer_actor,
            malformed_authority_hash,
            empty_rotation_member,
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    custodian_identities=(),
                    custodian_approval_member_identities=(),
                    custodian_approval_sha256s=(),
                ),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    custodian_approval_member_identities=("approval:custodian:a",),
                ),
            ),
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    responsible_owner_identity="",
                ),
            ),
        )
        for index, attacked in enumerate(separation_attacks):
            with self.subTest(family="view_leaf", index=index):
                self._assert_separation_rejected(attacked)

        record = package.package_index.index_record
        raw_without_lf = b"not-json"
        record_attacks = (
            replace(record, file_sha256=_digest("wrong-file-hash")),
            replace(record, canonical_body=b"evil"),
            replace(
                record,
                raw_bytes=raw_without_lf,
                canonical_body=raw_without_lf,
                file_sha256=sha256(raw_without_lf).hexdigest(),
            ),
        )
        for index, attacked_record in enumerate(record_attacks):
            with self.subTest(family="record_binding", index=index):
                self._assert_science_rejected(
                    replace(
                        package,
                        package_index=replace(
                            package.package_index,
                            index_record=attacked_record,
                        ),
                    ),
                )

    def test_package_index_record_is_bound_to_its_exact_parsed_metadata(
        self,
    ) -> None:
        package = _package()
        honest_unrelated_payload = _index_payload(
            package.package_index, package.core_triples
        )
        honest_unrelated_payload["package_logical_id"] = "package:path-b:unrelated"
        honest_unrelated = _sealed_index_record(honest_unrelated_payload)

        core_byte_count_drift_payload = _index_payload(
            package.package_index, package.core_triples
        )
        core_byte_count_drift_payload["core_triples"][0][
            "artifact_file_byte_count"
        ] += 1
        core_byte_count_drift = _sealed_index_record(core_byte_count_drift_payload)

        unrelated_raw = b'{"different":"payload"}\n'
        shaped_unrelated = PersistedRecord(
            schema_version=PACKAGE_INDEX_SCHEMA.schema_version,
            raw_bytes=unrelated_raw,
            canonical_body=unrelated_raw[:-1],
            file_sha256=sha256(unrelated_raw).hexdigest(),
            self_sha256="f" * 64,
        )
        shaped_self_hash = replace(
            package.package_index.index_record,
            self_sha256="f" * 64,
        )
        attacks = (
            ("honest_unrelated_exact_schema", honest_unrelated),
            ("core_byte_count_drift", core_byte_count_drift),
            ("unrelated_shape_only", shaped_unrelated),
            ("arbitrary_shaped_self_hash", shaped_self_hash),
        )
        for family, attacked_record in attacks:
            attacked = replace(
                package,
                package_index=replace(
                    package.package_index,
                    index_record=attacked_record,
                ),
            )
            with self.subTest(family=family, validator="science"):
                self._assert_science_rejected(attacked)
            with self.subTest(family=family, validator="separation"):
                self._assert_separation_rejected(attacked)

    def test_package_index_migration_receipt_pin_joins_the_receipt_triple(self) -> None:
        package = _package()
        self.assertTrue(
            hasattr(package.package_index, "migration_receipt_pin_sha256"),
            "package-index metadata omits the migration receipt pin join",
        )
        self._assert_science_rejected(
            replace(
                package,
                package_index=replace(
                    package.package_index,
                    migration_receipt_pin_sha256=_digest("unrelated-receipt-pin"),
                ),
            )
        )

    def test_every_core_record_is_structurally_parsed_and_self_hash_bound(
        self,
    ) -> None:
        module = _science()
        package = _package()
        for index, triple in enumerate(package.core_triples):
            coordinates = (
                (
                    "artifact",
                    EXPECTED_ROLE_SCHEMAS[index],
                    EXPECTED_ARTIFACT_SELF_HASH_FIELDS[index],
                ),
                (
                    "envelope",
                    "ace.iclr2027.external_canonical_signature_envelope.vnext",
                    "envelope_sha256",
                ),
                (
                    "pin",
                    "ace.iclr2027.external_vnext_artifact_pin.vnext",
                    "pin_sha256",
                ),
            )
            for field, expected_schema, self_hash_field in coordinates:
                label = f"core-{index}-{field}"
                valid = _structural_record(label, expected_schema, self_hash_field)

                wrong_schema = _structural_record(
                    label,
                    "ace.iclr2027.caller_minted.v1",
                    self_hash_field,
                )
                wrong_schema = replace(
                    wrong_schema,
                    schema_version=expected_schema,
                )
                wrong_self_field = _structural_record(
                    label,
                    expected_schema,
                    "caller_minted_sha256",
                )
                stale_payload = json.loads(valid.canonical_body)
                stale_payload["fixture"] = f"{label}-drift"
                stale_raw = _canonical_json(stale_payload) + b"\n"
                stale_self_hash = replace(
                    valid,
                    raw_bytes=stale_raw,
                    canonical_body=stale_raw[:-1],
                    file_sha256=sha256(stale_raw).hexdigest(),
                )
                attacks = (
                    (
                        "fabricated_unparsed",
                        _fabricated_record(label, expected_schema),
                    ),
                    ("wrong_raw_schema", wrong_schema),
                    ("wrong_self_hash_field", wrong_self_field),
                    ("body_drift_stale_self_hash", stale_self_hash),
                    ("object_self_hash_drift", replace(valid, self_sha256="f" * 64)),
                )
                for family, attacked_record in attacks:
                    with self.subTest(
                        index=index,
                        field=field,
                        family=family,
                    ):
                        with self.assertRaises(module.IntakeContractError):
                            module._require_record(
                                attacked_record,
                                expected_schema,
                                f"core_{index}_{field}",
                                self_hash_field,
                            )

        fabricated_package = _package(core_record_factory=_fabricated_record)
        with self.subTest(family="fabricated_package", validator="science"):
            self._assert_science_rejected(fabricated_package)
        with self.subTest(family="fabricated_package", validator="separation"):
            self._assert_separation_rejected(fabricated_package)

    def test_each_single_core_record_binding_is_publicly_enforced(self) -> None:
        package = _package()
        for index in range(7):
            for field in ("artifact", "envelope", "pin"):
                attacked = _with_one_fabricated_core_record(package, index, field)
                with self.subTest(index=index, field=field, validator="science"):
                    self._assert_science_rejected(attacked)
                with self.subTest(index=index, field=field, validator="separation"):
                    self._assert_separation_rejected(attacked)

    def test_science_ast_oracle_requires_all_three_core_binding_calls(self) -> None:
        source = SCIENCE_PATH.read_text(encoding="utf-8")
        anchors = (
            """        _require_record(
            triple.artifact,
            triple.artifact_schema_version,
            "core_artifact",
            _record_self_hash_field(triple.artifact_schema_version),
        )
""",
            """        _require_record(
            triple.envelope,
            _ENVELOPE_SCHEMA,
            "core_envelope",
            "envelope_sha256",
        )
""",
            """        _require_record(
            triple.pin,
            _PIN_SCHEMA,
            "core_pin",
            "pin_sha256",
        )
""",
        )
        for ordinal, anchor in enumerate(anchors):
            self.assertEqual(source.count(anchor), 1)
            mutant = source.replace(anchor, "", 1)
            with self.subTest(ordinal=ordinal):
                self.assertIn(
                    "core-record-binding-drift",
                    _science_ast_boundary_violations(mutant),
                )

    def test_science_ast_boundary_rejects_reviewed_capability_mutations(self) -> None:
        source = SCIENCE_PATH.read_text(encoding="utf-8")
        self.assertEqual(_science_ast_boundary_violations(source), ())
        mutations = (
            "import os",
            "from hashlib import md5",
            "open('ROOT_SENTINEL')",
            "def from_dict(value):\n    return value",
            "sha256 = open\nsha256(b'x')",
            "object.__subclasses__()",
            '_CAPABILITY = dataclass.__globals__["sys"].modules',
            (
                "from cryptography.hazmat.primitives.asymmetric.ed25519 "
                "import Ed25519PrivateKey\nEd25519PrivateKey.generate()"
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(
                    _science_ast_boundary_violations(f"{source}\n{mutation}\n")
                )


if __name__ == "__main__":
    unittest.main()
