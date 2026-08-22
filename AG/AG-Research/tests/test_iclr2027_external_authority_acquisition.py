"""Contract tests for the synthetic-only Task 7 Path-B validator.

All scientific literals and expected outcomes in this file are test-owned.
They deliberately do not import production constants to form their oracle.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import iclr2027.external_authority_acquisition as acquisition
from iclr2027.external_authority_acquisition import (
    ExternalAuthorityAcquisitionError,
    NeedsContextError,
    negative_fixture_registry,
    require_authenticated_external_authority_acquisition,
    validate_synthetic_external_authority_acquisition,
)
from iclr2027.external_authority_acquisition import (
    _CustodianSearchRowVNext,
    _CustodyEvidenceRowVNext,
    _ExternalAuthorityAcquisitionResult,
    _ExternalCanonicalSignatureEnvelopeVNext,
    _ExternalVNextArtifactPinVNext,
    _IndependentMigrationReviewVNext,
    _LegacySearchImpossibilityDeclarationVNext,
    _NegativeFixtureSpec,
    _NewUpstreamScientificSnapshotVNext,
    _ObjectVersionSearchRowVNext,
    _OneThesisContractVNext,
    _ProvenanceMigrationReceiptVNext,
    _StoreSearchRowVNext,
    _SyntheticPathBDagInput,
    _validate_synthetic_path_b_metadata,
)


BRIEF_SHA = "9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54"
SCIENCE_REVIEW_SHA = "a42811069e45a34ba1cb70ffc90f6e5253e53954042e263356efffa424e67146"
SECURITY_REVIEW_SHA = "987c9e316e2c428fe2c0a6effc685ef0f46841ec72e6f462e3fae6194335b571"
LEGACY_SHA = "e774381bbde93a9540821a6375ccbee55ec724d801e91b10efab2bcdc91083b6"
FORBIDDEN_MEMORY_SHAS = (
    "a10f565562d83ec2c0e44e43baa13f0b01fa9922e5f72506ad6d824738a463c2",
    "ef42347d74bc3f319036dfc91e84c85934291726d51778d388edbab32736d158",
)
TASK5_ANALYSIS_SHA = "2809048fa71d0f2458db13f7590c61f0f28674f2195c3d8690a45193df517299"
TASK5_BRIEF_SHA = "8d2f27d2fb9e6901d7bfed90407a25f8c714d23fe9d2f511a469494e272054ee"
TASK5_REVIEW_SHA = "8d98a17ee57b1a254d4f651d74b44b696ec022e3822daea1b8a3f25036060cc8"


def _ast_policy_violations(source: str) -> tuple[str, ...]:
    """Return test-owned static-policy violations for a Python source string."""

    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    violations: set[str] = set()
    forbidden_roots = {
        "cryptography",
        "http",
        "importlib",
        "io",
        "model",
        "nacl",
        "os",
        "pathlib",
        "requests",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
    }
    forbidden_builtins = {"__import__", "compile", "eval", "exec", "open"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = alias.name
                root = alias.name.split(".")[0]
                if root in forbidden_roots or "task6" in alias.name.lower():
                    violations.add(f"import:{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{module}.{alias.name}"
            root = module.split(".")[0]
            if root in forbidden_roots or "task6" in module.lower():
                violations.add(f"import-from:{module}")

    def resolved_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = resolved_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        if isinstance(node, ast.Call):
            function_name = resolved_name(node.func)
            if function_name in {"getattr", "builtins.getattr"} and len(node.args) >= 2:
                attribute = node.args[1]
                if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str):
                    base = resolved_name(node.args[0])
                    return f"{base}.{attribute.value}" if base else attribute.value
            return resolved_name(node.func)
        return ""

    assignments = tuple(node for node in ast.walk(tree) if isinstance(node, ast.Assign))
    for _ in range(len(assignments) + 1):
        changed = False
        for node in assignments:
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            resolved = resolved_name(node.value)
            if resolved and aliases.get(node.targets[0].id) != resolved:
                aliases[node.targets[0].id] = resolved
                changed = True
        if not changed:
            break

    forbidden_qualified = forbidden_builtins | {
        f"{namespace}.{name}"
        for namespace in ("builtins", "__builtins__")
        for name in forbidden_builtins
    }
    forbidden_namespaces = {"builtins", "__builtins__"}
    forbidden_reflection = {
        "globals",
        "locals",
        "vars",
        "builtins.globals",
        "builtins.locals",
        "builtins.vars",
        "__builtins__.globals",
        "__builtins__.locals",
        "__builtins__.vars",
    }
    for reference in ast.walk(tree):
        if isinstance(reference, ast.Name) and not isinstance(reference.ctx, ast.Load):
            continue
        if not isinstance(reference, (ast.Name, ast.Attribute, ast.Call)):
            continue
        name = resolved_name(reference)
        root = name.split(".")[0]
        if (
            name in forbidden_qualified
            or name in forbidden_reflection
            or name in forbidden_namespaces
            or root in forbidden_roots
        ):
            violations.add(f"reference:{name}")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = resolved_name(node.func)
        root = name.split(".")[0]
        if name in forbidden_qualified or root in forbidden_roots:
            violations.add(f"call:{name}")
        if name in {
            "builtins.__import__",
            "__builtins__.__import__",
            "importlib.import_module",
            "importlib.__import__",
        }:
            violations.add(f"dynamic-import:{name}")
        if name in {"__import__", "builtins.__import__", "__builtins__.__import__"} and node.args:
            target = node.args[0]
            if isinstance(target, ast.Constant) and isinstance(target.value, str):
                if "task6" in target.value.lower():
                    violations.add(f"task6-dynamic-import:{target.value}")
    return tuple(sorted(violations))


def _ast_policy_violations_for_target(source: str, target: str) -> tuple[str, ...]:
    """Apply the generic policy plus one exact reviewed import form sequence."""

    expected = {
        "production": (
            ("from", "__future__", 0, (("annotations", None),)),
            ("from", "dataclasses", 0, (("dataclass", None), ("fields", None))),
            ("from", "datetime", 0, (("datetime", None),)),
            ("import", (("hashlib", None),)),
            ("import", (("json", None),)),
            ("import", (("math", None),)),
            ("import", (("re", None),)),
            ("from", "typing", 0, (("Any", None), ("ClassVar", None))),
        ),
        "cli": (
            ("from", "__future__", 0, (("annotations", None),)),
            ("import", (("argparse", None),)),
            (
                "from",
                "iclr2027",
                0,
                (("external_authority_acquisition", "acquisition"),),
            ),
        ),
    }
    violations = set(_ast_policy_violations(source))
    if target not in expected:
        violations.add(f"unknown-import-policy:{target}")
        return tuple(sorted(violations))
    tree = ast.parse(source)
    actual: list[tuple[object, ...]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            actual.append(("import", tuple((alias.name, alias.asname) for alias in node.names)))
        elif isinstance(node, ast.ImportFrom):
            actual.append(
                (
                    "from",
                    node.module or "",
                    node.level,
                    tuple((alias.name, alias.asname) for alias in node.names),
                )
            )
    if tuple(actual) != expected[target]:
        violations.add(f"exact-import-allowlist:{target}")
    return tuple(sorted(violations))

POLICY_IDS = (
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

ENDPOINT_HIERARCHY = (
    "e2_randomized_executed_bundle_primary",
    "e3_equal_information_oacs_vs_full_parity_raw_router_conditional_on_e2",
    "e4_fresh_downstream_frontier_conditional_on_e1_e2_e3",
    "e1_predictive_support_noncausal_nonprimary",
)

KILL_CHAIN = (
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

REASON_IDS = (
    "actual_architecture_jci_rosters_missing",
    "external_launcher_root_capability_missing",
    "external_migration_receipt_missing",
    "external_one_thesis_contract_missing",
    "external_path_b_owner_signature_missing",
    "external_reviews_missing",
    "external_signatures_missing",
    "external_snapshot_missing",
    "legacy_search_declaration_missing",
    "operation_rate_manifest_missing",
    "paid_run_authorization_missing",
    "simulation_freeze_missing",
    "task6_vnext_authority_missing",
    "task6_vnext_implementation_missing",
    "task6_vnext_reviews_missing",
)

FIXTURE_IDS = (
    "migration_architecture_failure_downgraded_to_domain_local_only",
    "migration_architecture_failure_retains_jci_only_main_claim",
    "migration_architecture_survivor_boundary_swapped_or_omitted",
    "migration_cats_contribution_upgrade",
    "migration_claims_e774_continuity",
    "migration_contains_task6_or_task7_dependency",
    "migration_declaration_e774_missing_or_wrong",
    "migration_derived_from_a10",
    "migration_domain_pooling_or_jci_role_drift",
    "migration_endpoint_or_kill_chain_drift",
    "migration_incomplete_search_or_owner",
    "migration_jci_failure_downgraded_to_generalization_only",
    "migration_mixed_schema",
    "migration_ontology_kill_clause_swapped_or_omitted",
    "migration_oracle_policy_upgrade",
    "migration_review_independence_caller_authored",
    "migration_review_missing_foreign_or_swapped_role_domain",
    "migration_review_owner_or_producer_signed",
    "migration_review_self_file_cycle",
    "migration_review_shared_key_or_package",
    "migration_task6_plan_before_vnext_review",
    "migration_thesis_role_drift",
    "migration_unreviewed",
    "migration_workspace_signing",
    "paid_run_from_intake_checklist",
    "synthetic_fixture_upgraded_to_real",
)

FIXTURE_OUTCOMES = {
    "migration_architecture_failure_downgraded_to_domain_local_only": ("scientific_kill_chain", "reject_exact_architecture_main_claim_kill"),
    "migration_architecture_failure_retains_jci_only_main_claim": ("scientific_kill_chain", "reject_no_reclassification_or_rescue"),
    "migration_architecture_survivor_boundary_swapped_or_omitted": ("scientific_kill_chain", "reject_exact_ordered_kill_chain"),
    "migration_cats_contribution_upgrade": ("scientific_role", "reject_exact_cats_role"),
    "migration_claims_e774_continuity": ("provenance_scope", "reject_declaration_only_legacy_target"),
    "migration_contains_task6_or_task7_dependency": ("acyclicity", "reject_dependency_insertion_or_reverse_cycle"),
    "migration_declaration_e774_missing_or_wrong": ("provenance_scope", "reject_legacy_search_declaration"),
    "migration_derived_from_a10": ("provenance_scope", "reject_downstream_memory_derivation"),
    "migration_domain_pooling_or_jci_role_drift": ("scientific_role", "reject_exact_domain_contract"),
    "migration_endpoint_or_kill_chain_drift": ("scientific_kill_chain", "reject_exact_ordered_arrays"),
    "migration_incomplete_search_or_owner": ("search_closure", "reject_incomplete_signed_declaration"),
    "migration_jci_failure_downgraded_to_generalization_only": ("scientific_kill_chain", "reject_exact_jci_kill"),
    "migration_mixed_schema": ("schema", "reject_version_mixing"),
    "migration_ontology_kill_clause_swapped_or_omitted": ("scientific_kill_chain", "reject_ontology_specific_contract"),
    "migration_oracle_policy_upgrade": ("scientific_role", "reject_exact_separate_oracle_role"),
    "migration_review_independence_caller_authored": ("review_independence", "reject_caller_boolean_as_evidence"),
    "migration_review_missing_foreign_or_swapped_role_domain": ("review_independence", "reject_before_migration_receipt"),
    "migration_review_owner_or_producer_signed": ("review_independence", "reject_role_key_or_package_overlap"),
    "migration_review_self_file_cycle": ("acyclicity", "reject_review_schema_or_reverse_cycle"),
    "migration_review_shared_key_or_package": ("review_independence", "reject_pairwise_distinct_reviewer_authority"),
    "migration_task6_plan_before_vnext_review": ("chronology", "reject_premature_task6_vnext"),
    "migration_thesis_role_drift": ("scientific_role", "reject_exact_one_thesis_contract"),
    "migration_unreviewed": ("review_independence", "no_go"),
    "migration_workspace_signing": ("trust_boundary", "reject_workspace_signing"),
    "paid_run_from_intake_checklist": ("paid_boundary", "no_go"),
    "synthetic_fixture_upgraded_to_real": ("synthetic_boundary", "reject_synthetic_to_real_upgrade"),
}

FIXTURE_DESCRIPTIONS = {
    "migration_architecture_failure_downgraded_to_domain_local_only": "Architecture E2 or E3 failure is downgraded to a domain-local issue",
    "migration_architecture_failure_retains_jci_only_main_claim": "Architecture failure retains a JCI-only ICLR-main claim",
    "migration_architecture_survivor_boundary_swapped_or_omitted": "Architecture and JCI survivor boundaries are swapped or omitted",
    "migration_cats_contribution_upgrade": "CATS is promoted from baseline-only motivation",
    "migration_claims_e774_continuity": "Migration asserts e774 continuity or equivalence",
    "migration_contains_task6_or_task7_dependency": "Upstream migration inserts a Task6 or Task7 dependency",
    "migration_declaration_e774_missing_or_wrong": "Declaration omits or changes the searched e774 digest",
    "migration_derived_from_a10": "Migration derives from a downstream current-memory snapshot",
    "migration_domain_pooling_or_jci_role_drift": "JCI is pooled with Architecture or changes role",
    "migration_endpoint_or_kill_chain_drift": "Endpoint hierarchy or kill chain changes",
    "migration_incomplete_search_or_owner": "Search census or responsible owner approval is incomplete",
    "migration_jci_failure_downgraded_to_generalization_only": "JCI failure is downgraded while keeping the main claim",
    "migration_mixed_schema": "A v1 or v3 object is mixed into a vNext position",
    "migration_ontology_kill_clause_swapped_or_omitted": "Ontology-specific kill clauses are swapped or omitted",
    "migration_oracle_policy_upgrade": "Retrospective oracle is promoted into the deployable roster",
    "migration_review_independence_caller_authored": "Caller boolean is used as independence evidence",
    "migration_review_missing_foreign_or_swapped_role_domain": "Review is missing, foreign, or uses a swapped role domain",
    "migration_review_owner_or_producer_signed": "Migration owner or producer signs a review",
    "migration_review_self_file_cycle": "Review or receipt introduces a self-file reverse cycle",
    "migration_review_shared_key_or_package": "Reviewers share a key or verifier package",
    "migration_task6_plan_before_vnext_review": "Task6 vNext planning occurs before required reviews",
    "migration_thesis_role_drift": "One-thesis treatment or flagship role changes",
    "migration_unreviewed": "One or more migration reviews are absent or nonapproved",
    "migration_workspace_signing": "Workspace key or signature is treated as external authority",
    "paid_run_from_intake_checklist": "An intake checklist is upgraded to paid-run authorization",
    "synthetic_fixture_upgraded_to_real": "Synthetic fixture is upgraded to real authority",
}

EXPECTED_REGISTRY_SHA = "5fde31fdf101249618ee66c359283990aa3363d9d7e22c389c2470403d52bb28"
EXPECTED_RESULT_SHA = "35a185b9455dc1def3c84a3ede34943785ac6b935e4810db3c62482289e06bfb"
EXPECTED_RESULT_JSON = (
    '{"authority_mode":"synthetic","binding_brief_sha256":"9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54",'
    '"data_read_count":0,"external_artifact_count":0,"external_review_count":0,"external_signature_count":0,"model_call_count":0,'
    '"negative_fixture_registry_sha256":"5fde31fdf101249618ee66c359283990aa3363d9d7e22c389c2470403d52bb28",'
    '"official_result_eligible":false,"paid_call_count":0,"rate_read_count":0,"reason_codes":["actual_architecture_jci_rosters_missing",'
    '"external_launcher_root_capability_missing","external_migration_receipt_missing","external_one_thesis_contract_missing",'
    '"external_path_b_owner_signature_missing","external_reviews_missing","external_signatures_missing","external_snapshot_missing",'
    '"legacy_search_declaration_missing","operation_rate_manifest_missing","paid_run_authorization_missing","simulation_freeze_missing",'
    '"task6_vnext_authority_missing","task6_vnext_implementation_missing","task6_vnext_reviews_missing"],"result_read_count":0,'
    '"result_sha256":"35a185b9455dc1def3c84a3ede34943785ac6b935e4810db3c62482289e06bfb",'
    '"schema_version":"ace.iclr2027.external_authority_acquisition_result.v1",'
    '"science_review_sha256":"a42811069e45a34ba1cb70ffc90f6e5253e53954042e263356efffa424e67146",'
    '"security_review_sha256":"987c9e316e2c428fe2c0a6effc685ef0f46841ec72e6f462e3fae6194335b571",'
    '"selected_path":"path_b_user_approved_but_not_externally_authenticated","simulation_draw_count":0,"source_read_count":0,'
    '"status":"no_go","synthetic_only":true,"task6_vnext_authority_count":0,"task6_vnext_implementation_count":0,"tool_call_count":0}'
)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)


def _sha(value: object) -> str:
    if isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = _canonical(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _seal(payload: dict[str, object], self_key: str) -> dict[str, object]:
    sealed = dict(payload)
    sealed[self_key] = _sha(payload)
    return sealed


def _file_sha(payload: dict[str, object]) -> str:
    return _sha(payload)


def _file_len(payload: dict[str, object]) -> int:
    return len(_canonical(payload).encode("utf-8"))


def _custodian_row_dict() -> dict[str, object]:
    return _seal(
        {
            "custodian_id": "custodian-0",
            "custodian_role": "legacy-record-custodian",
            "contacted_at_utc": "2026-08-20T00:00:01Z",
            "completed_at_utc": "2026-08-20T00:00:07Z",
            "searched_store_ids": ["store-0"],
            "searched_object_version_keys": ["object-version-0"],
            "search_method": "exhaustive_immutable_version_search",
            "search_result": "exact_raw_bytes_not_found",
            "approval_member_identity": "member:custodian-approval-0",
            "approval_file_sha256": "1" * 64,
        },
        "row_sha256",
    )


def _store_row_dict() -> dict[str, object]:
    return _seal(
        {
            "store_id": "store-0",
            "owner_custodian_id": "custodian-0",
            "store_kind": "immutable_object_store",
            "immutable_store_identity": "immutable-store-0",
            "store_version": "store-version-0",
            "searched_at_utc": "2026-08-20T00:00:02Z",
            "search_scope": "all_known_namespaces_and_versions",
            "all_known_namespaces_examined": True,
            "evidence_member_identities": ["member:evidence-0"],
            "search_result": "exact_raw_bytes_not_found",
        },
        "row_sha256",
    )


def _object_row_dict() -> dict[str, object]:
    return _seal(
        {
            "object_version_key": "object-version-0",
            "store_id": "store-0",
            "immutable_object_identity": "immutable-object-0",
            "immutable_object_version": "immutable-object-version-0",
            "examined_at_utc": "2026-08-20T00:00:03Z",
            "raw_object_available": False,
            "candidate_file_count": 0,
            "candidate_file_sha256s": [],
            "evidence_member_identities": ["member:evidence-0"],
            "search_result": "exact_raw_bytes_not_found",
        },
        "row_sha256",
    )


def _evidence_row_dict() -> dict[str, object]:
    return _seal(
        {
            "evidence_index": 0,
            "occurred_at_utc": "2026-08-20T00:00:04Z",
            "custodian_identity": "custodian-0",
            "immutable_store_identity": "immutable-store-0",
            "immutable_object_identity": "immutable-object-0",
            "immutable_object_version": "immutable-object-version-0",
            "evidence_member_identity": "member:evidence-0",
            "evidence_file_sha256": "2" * 64,
            "evidence_file_byte_count": 10,
        },
        "row_sha256",
    )


def _declaration_dict() -> dict[str, object]:
    return _seal(
        {
            "schema_version": "ace.iclr2027.legacy_search_impossibility_declaration.vnext",
            "declaration_version": 1,
            "declaration_logical_id": "legacy-search-declaration-0",
            "legacy_snapshot_logical_id": "legacy-upstream-memory-snapshot",
            "expected_legacy_raw_sha256": LEGACY_SHA,
            "search_opened_at_utc": "2026-08-20T00:00:00Z",
            "search_closed_at_utc": "2026-08-20T00:00:08Z",
            "known_custodian_ids": ["custodian-0"],
            "known_store_ids": ["store-0"],
            "known_object_version_keys": ["object-version-0"],
            "custodian_search_rows": [_custodian_row_dict()],
            "store_search_rows": [_store_row_dict()],
            "object_version_search_rows": [_object_row_dict()],
            "custody_evidence_rows": [_evidence_row_dict()],
            "unsearched_custodian_ids": [],
            "unsearched_store_ids": [],
            "unsearched_object_version_keys": [],
            "legacy_recovery_status": "exhaustive_search_completed_exact_raw_bytes_not_recovered",
            "legacy_continuity": False,
            "legacy_equivalence": False,
            "responsible_migration_owner_identity": "external-migration-owner",
            "responsible_owner_approval_member_identity": "member:owner-approval",
            "responsible_owner_approval_sha256": "3" * 64,
            "custodian_approval_member_sha256s": ["1" * 64],
        },
        "declaration_sha256",
    )


def _thesis_dict() -> dict[str, object]:
    return _seal(
        {
            "schema_version": "ace.iclr2027.one_thesis_contract.vnext",
            "contract_version": 1,
            "contract_logical_id": "one-thesis-contract-0",
            "allowed_upstream_authority_sha256s": sorted(
                [TASK5_BRIEF_SHA, TASK5_ANALYSIS_SHA, TASK5_REVIEW_SHA]
            ),
            "task5_brief_sha256": TASK5_BRIEF_SHA,
            "task5_analysis_plan_sha256": TASK5_ANALYSIS_SHA,
            "task5_review_sha256": TASK5_REVIEW_SHA,
            "external_scientist_identity": "external-domain-scientist",
            "external_scientist_approval_member_identity": "member:scientist-approval",
            "external_scientist_approval_sha256": "4" * 64,
            "legacy_continuity": False,
            "legacy_equivalence": False,
            "thesis_id": "residual_obligation_x_actually_executed_complete_bundle",
            "treatment_definition": "residual_obligation_status_x_actually_executed_complete_bundle",
            "architecture_domain_role": "flagship_primary_domain",
            "jci_domain_role": "independent_e2_e3_replication_no_pooling",
            "architecture_ontology_clause": "architecture_site_cluster_flagship_residual_obligation_x_actually_executed_complete_bundle",
            "jci_ontology_clause": "jci_project_cluster_independent_e2_e3_resource_obligation_replication_no_pooling",
            "cross_domain_pooling": "forbidden",
            "cats_role": "negative_motivation_and_baseline_only",
            "e1_role": "predictive_noncausal_nonprimary_support",
            "e2_role": "randomized_executed_complete_bundle_primary_mechanism",
            "e2_primary_endpoint": "blind_terminal_obligation_closure_quality_present_high_minus_low_minus_absent_high_minus_low",
            "e3_role": "equal_information_policy_consequence_conditional_on_e2",
            "e3_primary_comparator": "full_parity_raw_router",
            "e3_mandatory_policy_ids": list(POLICY_IDS),
            "retrospective_oracle_role": "post_outcome_descriptive_upper_bound_separate_not_deployable",
            "e4_role": "fresh_downstream_deployable_frontier_after_e1_e2_e3",
            "endpoint_hierarchy": list(ENDPOINT_HIERARCHY),
            "kill_chain": list(KILL_CHAIN),
        },
        "contract_sha256",
    )


def _snapshot_dict(declaration: dict[str, object], thesis: dict[str, object]) -> dict[str, object]:
    return _seal(
        {
            "schema_version": "ace.iclr2027.new_upstream_scientific_snapshot.vnext",
            "snapshot_version": 1,
            "snapshot_logical_id": "new-upstream-snapshot-0",
            "migration_kind": "explicit_non_continuity_migration",
            "legacy_search_declaration_file_sha256": _file_sha(declaration),
            "legacy_search_declaration_sha256": declaration["declaration_sha256"],
            "one_thesis_contract_file_sha256": _file_sha(thesis),
            "one_thesis_contract_sha256": thesis["contract_sha256"],
            "allowed_upstream_authority_sha256s": sorted(
                [TASK5_BRIEF_SHA, TASK5_ANALYSIS_SHA, TASK5_REVIEW_SHA]
            ),
            "external_scientist_approval_sha256": "4" * 64,
            "legacy_continuity": False,
            "legacy_equivalence": False,
        },
        "snapshot_sha256",
    )


REVIEW_ROLES = (
    "independent_provenance_migration_review",
    "independent_science_migration_review",
    "independent_security_migration_review",
)


def _review_dict(
    role: str,
    declaration: dict[str, object],
    thesis: dict[str, object],
    snapshot: dict[str, object],
    *,
    reviewer_identity: str | None = None,
) -> dict[str, object]:
    return _seal(
        {
            "schema_version": "ace.iclr2027.independent_migration_review.vnext",
            "review_role": role,
            "reviewed_declaration_file_sha256": _file_sha(declaration),
            "reviewed_declaration_sha256": declaration["declaration_sha256"],
            "reviewed_one_thesis_contract_file_sha256": _file_sha(thesis),
            "reviewed_one_thesis_contract_sha256": thesis["contract_sha256"],
            "reviewed_snapshot_file_sha256": _file_sha(snapshot),
            "reviewed_snapshot_sha256": snapshot["snapshot_sha256"],
            "reviewer_identity": reviewer_identity or f"reviewer:{role}",
            "reviewer_independent": True,
            "reviewed_at_utc": "2026-08-20T00:00:09Z",
            "critical_count": 0,
            "important_count": 0,
            "minor_count": 0,
            "verdict": "approved",
        },
        "review_sha256",
    )


ROLE_DOMAINS = {
    "legacy_search_impossibility_declaration": "ACE-ICLR2027-LEGACY-SEARCH-IMPOSSIBILITY-VNEXT\x00",
    "one_thesis_contract": "ACE-ICLR2027-ONE-THESIS-CONTRACT-VNEXT\x00",
    "new_upstream_scientific_snapshot": "ACE-ICLR2027-NEW-UPSTREAM-SCIENTIFIC-SNAPSHOT-VNEXT\x00",
    "independent_science_migration_review": "ACE-ICLR2027-INDEPENDENT-SCIENCE-MIGRATION-REVIEW-VNEXT\x00",
    "independent_provenance_migration_review": "ACE-ICLR2027-INDEPENDENT-PROVENANCE-MIGRATION-REVIEW-VNEXT\x00",
    "independent_security_migration_review": "ACE-ICLR2027-INDEPENDENT-SECURITY-MIGRATION-REVIEW-VNEXT\x00",
    "provenance_migration_receipt": "ACE-ICLR2027-PROVENANCE-MIGRATION-RECEIPT-VNEXT\x00",
}

TERMINATED_ROLE_DOMAINS = dict(ROLE_DOMAINS)


def _reseed(payload: dict[str, object], self_key: str, updates: dict[str, object] | None) -> dict[str, object]:
    changed = {key: value for key, value in payload.items() if key != self_key}
    if updates:
        changed.update(updates)
    return _seal(changed, self_key)


def _load_record(cls: type, payload: dict[str, object], loader: str) -> object:
    if loader == "from_dict":
        return cls.from_dict(payload)
    if loader == "from_json":
        return cls.from_json(_canonical(payload))
    raise AssertionError(f"unexpected loader: {loader}")


def _envelope_dict(
    *,
    artifact_role: str,
    artifact: dict[str, object],
    artifact_schema_version: str,
    logical_id: str,
    predecessors: list[str],
) -> dict[str, object]:
    marker = _sha(artifact_role)[:12]
    return _seal(
        {
            "schema_version": "ace.iclr2027.external_canonical_signature_envelope.vnext",
            "envelope_version": 1,
            "artifact_role": artifact_role,
            "artifact_schema_version": artifact_schema_version,
            "artifact_logical_id": logical_id,
            "artifact_file_byte_count": _file_len(artifact),
            "artifact_file_sha256": _file_sha(artifact),
            "detached_message_domain": ROLE_DOMAINS[artifact_role],
            "signature_algorithm": "ed25519",
            "signing_key_id": f"key:{marker}",
            "signing_public_key_member_identity": f"member:key:{marker}",
            "signing_public_key_byte_count": 32,
            "signing_public_key_sha256": marker.ljust(64, "a"),
            "detached_signature_member_identity": f"member:signature:{marker}",
            "detached_signature_byte_count": 64,
            "detached_signature_sha256": marker.ljust(64, "b"),
            "external_verifier_package_identity": f"package:{marker}",
            "external_verifier_package_version": f"version:{marker}",
            "external_verifier_executable_sha256": marker.ljust(64, "c"),
            "rotation_provenance_member_identity": f"member:rotation:{marker}",
            "rotation_provenance_sha256": marker.ljust(64, "d"),
            "predecessor_envelope_sha256s": predecessors,
        },
        "envelope_sha256",
    )


def _pin_dict(
    *,
    artifact_role: str,
    artifact: dict[str, object],
    envelope: dict[str, object],
    predecessors: list[str],
) -> dict[str, object]:
    marker = _sha(artifact_role)[:12]
    return _seal(
        {
            "schema_version": "ace.iclr2027.external_vnext_artifact_pin.vnext",
            "pin_version": 1,
            "artifact_role": artifact_role,
            "expected_artifact_file_byte_count": _file_len(artifact),
            "expected_artifact_file_sha256": _file_sha(artifact),
            "expected_signature_envelope_file_byte_count": _file_len(envelope),
            "expected_signature_envelope_file_sha256": _file_sha(envelope),
            "external_verifier_package_identity": envelope["external_verifier_package_identity"],
            "external_verifier_package_version": envelope["external_verifier_package_version"],
            "external_verifier_executable_member_identity": f"member:executable:{marker}",
            "external_verifier_executable_sha256": envelope["external_verifier_executable_sha256"],
            "external_platform_signature_member_identity": f"member:platform-signature:{marker}",
            "external_platform_signature_sha256": marker.ljust(64, "e"),
            "signing_key_id": envelope["signing_key_id"],
            "signing_public_key_member_identity": envelope["signing_public_key_member_identity"],
            "signing_public_key_byte_count": 32,
            "signing_public_key_sha256": envelope["signing_public_key_sha256"],
            "detached_signature_member_identity": envelope["detached_signature_member_identity"],
            "detached_signature_byte_count": 64,
            "detached_signature_sha256": envelope["detached_signature_sha256"],
            "detached_message_domain": envelope["detached_message_domain"],
            "rotation_provenance_member_identity": envelope["rotation_provenance_member_identity"],
            "rotation_provenance_sha256": envelope["rotation_provenance_sha256"],
            "predecessor_artifact_pin_sha256s": predecessors,
        },
        "pin_sha256",
    )


def _raw_artifact_triple(
    payload: dict[str, object],
    role: str,
    logical_id: str,
    env_predecessors: list[str],
    pin_predecessors: list[str],
    *,
    envelope_updates: dict[str, object] | None = None,
    pin_updates: dict[str, object] | None = None,
) -> tuple[dict[str, object], str, dict[str, object], str, dict[str, object], str]:
    envelope_dict = _envelope_dict(
        artifact_role=role,
        artifact=payload,
        artifact_schema_version=payload["schema_version"],
        logical_id=logical_id,
        predecessors=env_predecessors,
    )
    envelope_dict = _reseed(envelope_dict, "envelope_sha256", envelope_updates)
    pin_dict = _pin_dict(
        artifact_role=role,
        artifact=payload,
        envelope=envelope_dict,
        predecessors=pin_predecessors,
    )
    pin_dict = _reseed(pin_dict, "pin_sha256", pin_updates)
    return payload, _file_sha(payload), envelope_dict, _file_sha(envelope_dict), pin_dict, _file_sha(pin_dict)


def _raw_dag(
    *,
    reviewer_identity_overrides: dict[str, str] | None = None,
    artifact_updates: dict[str, dict[str, object]] | None = None,
    envelope_updates: dict[str, dict[str, object]] | None = None,
    pin_updates: dict[str, dict[str, object]] | None = None,
    declaration_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    artifact_updates = artifact_updates or {}
    envelope_updates = envelope_updates or {}
    pin_updates = pin_updates or {}
    declaration_dict = declaration_payload or _declaration_dict()
    declaration_dict = _reseed(
        declaration_dict,
        "declaration_sha256",
        artifact_updates.get("legacy_search_impossibility_declaration"),
    )
    thesis_dict = _reseed(
        _thesis_dict(),
        "contract_sha256",
        artifact_updates.get("one_thesis_contract"),
    )
    snapshot_dict = _snapshot_dict(declaration_dict, thesis_dict)
    snapshot_dict = _reseed(
        snapshot_dict,
        "snapshot_sha256",
        artifact_updates.get("new_upstream_scientific_snapshot"),
    )
    declaration = _raw_artifact_triple(
        declaration_dict,
        "legacy_search_impossibility_declaration",
        declaration_dict["declaration_logical_id"],
        [],
        [],
        envelope_updates=envelope_updates.get("legacy_search_impossibility_declaration"),
        pin_updates=pin_updates.get("legacy_search_impossibility_declaration"),
    )
    thesis = _raw_artifact_triple(
        thesis_dict,
        "one_thesis_contract",
        thesis_dict["contract_logical_id"],
        [declaration[2]["envelope_sha256"]],
        [declaration[4]["pin_sha256"]],
        envelope_updates=envelope_updates.get("one_thesis_contract"),
        pin_updates=pin_updates.get("one_thesis_contract"),
    )
    snapshot = _raw_artifact_triple(
        snapshot_dict,
        "new_upstream_scientific_snapshot",
        snapshot_dict["snapshot_logical_id"],
        [thesis[2]["envelope_sha256"]],
        [thesis[4]["pin_sha256"]],
        envelope_updates=envelope_updates.get("new_upstream_scientific_snapshot"),
        pin_updates=pin_updates.get("new_upstream_scientific_snapshot"),
    )
    reviews = []
    review_dicts = []
    for role in REVIEW_ROLES:
        review_dict = _review_dict(
            role,
            declaration_dict,
            thesis_dict,
            snapshot_dict,
            reviewer_identity=(reviewer_identity_overrides or {}).get(role),
        )
        review_dict = _reseed(review_dict, "review_sha256", artifact_updates.get(role))
        review_dicts.append(review_dict)
        reviews.append(
            _raw_artifact_triple(
                review_dict,
                role,
                f"review:{role}",
                [snapshot[2]["envelope_sha256"]],
                [snapshot[4]["pin_sha256"]],
                envelope_updates=envelope_updates.get(role),
                pin_updates=pin_updates.get(role),
            )
        )
    receipt_payload = {
        "schema_version": "ace.iclr2027.provenance_migration_receipt.vnext",
        "migration_version": 1,
        "migration_logical_id": "migration-receipt-0",
        "legacy_search_declaration_file_sha256": declaration[1],
        "legacy_search_declaration_sha256": declaration[0]["declaration_sha256"],
        "legacy_search_declaration_signature_envelope_file_sha256": declaration[3],
        "legacy_search_declaration_signature_envelope_sha256": declaration[2]["envelope_sha256"],
        "legacy_search_declaration_pin_file_sha256": declaration[5],
        "legacy_search_declaration_pin_sha256": declaration[4]["pin_sha256"],
        "one_thesis_contract_file_sha256": thesis[1],
        "one_thesis_contract_sha256": thesis[0]["contract_sha256"],
        "one_thesis_contract_signature_envelope_file_sha256": thesis[3],
        "one_thesis_contract_signature_envelope_sha256": thesis[2]["envelope_sha256"],
        "one_thesis_contract_pin_file_sha256": thesis[5],
        "one_thesis_contract_pin_sha256": thesis[4]["pin_sha256"],
        "new_snapshot_file_sha256": snapshot[1],
        "new_snapshot_sha256": snapshot[0]["snapshot_sha256"],
        "new_snapshot_signature_envelope_file_sha256": snapshot[3],
        "new_snapshot_signature_envelope_sha256": snapshot[2]["envelope_sha256"],
        "new_snapshot_pin_file_sha256": snapshot[5],
        "new_snapshot_pin_sha256": snapshot[4]["pin_sha256"],
    }
    reviews_by_role = {review[0]["review_role"]: review for review in reviews}
    for label, role in (
        ("science", "independent_science_migration_review"),
        ("provenance", "independent_provenance_migration_review"),
        ("security", "independent_security_migration_review"),
    ):
        review = reviews_by_role[role]
        receipt_payload.update(
            {
                f"independent_{label}_review_file_sha256": review[1],
                f"independent_{label}_review_sha256": review[0]["review_sha256"],
                f"independent_{label}_review_signature_envelope_file_sha256": review[3],
                f"independent_{label}_review_signature_envelope_sha256": review[2]["envelope_sha256"],
                f"independent_{label}_review_pin_file_sha256": review[5],
                f"independent_{label}_review_pin_sha256": review[4]["pin_sha256"],
            }
        )
    receipt_payload.update(
        {
            "legacy_continuity": False,
            "legacy_equivalence": False,
            "migration_status": "reviewed_non_continuity_snapshot_ready_for_task6_vnext_authority",
        }
    )
    receipt_dict = _seal(receipt_payload, "receipt_sha256")
    receipt_dict = _reseed(
        receipt_dict,
        "receipt_sha256",
        artifact_updates.get("provenance_migration_receipt"),
    )
    receipt = _raw_artifact_triple(
        receipt_dict,
        "provenance_migration_receipt",
        receipt_dict["migration_logical_id"],
        sorted(review[2]["envelope_sha256"] for review in reviews),
        sorted(review[4]["pin_sha256"] for review in reviews),
        envelope_updates=envelope_updates.get("provenance_migration_receipt"),
        pin_updates=pin_updates.get("provenance_migration_receipt"),
    )
    return {
        "declaration": declaration,
        "thesis": thesis,
        "snapshot": snapshot,
        "reviews": tuple(reviews),
        "receipt": receipt,
    }


def _raw_triple_by_role(raw_dag: dict[str, object], role: str) -> tuple[object, ...]:
    if role == "legacy_search_impossibility_declaration":
        return raw_dag["declaration"]
    if role == "one_thesis_contract":
        return raw_dag["thesis"]
    if role == "new_upstream_scientific_snapshot":
        return raw_dag["snapshot"]
    if role == "provenance_migration_receipt":
        return raw_dag["receipt"]
    for review in raw_dag["reviews"]:
        if review[0]["review_role"] == role:
            return review
    raise AssertionError(f"unknown raw role: {role}")


def _artifact_type_for_role(role: str) -> type:
    if role == "legacy_search_impossibility_declaration":
        return _LegacySearchImpossibilityDeclarationVNext
    if role == "one_thesis_contract":
        return _OneThesisContractVNext
    if role == "new_upstream_scientific_snapshot":
        return _NewUpstreamScientificSnapshotVNext
    if role == "provenance_migration_receipt":
        return _ProvenanceMigrationReceiptVNext
    if role in REVIEW_ROLES:
        return _IndependentMigrationReviewVNext
    raise AssertionError(f"unknown artifact role: {role}")


def _parse_raw_triple(raw_triple: tuple[object, ...], role: str, loader: str) -> tuple[object, ...]:
    return (
        _load_record(_artifact_type_for_role(role), raw_triple[0], loader),
        raw_triple[1],
        _load_record(_ExternalCanonicalSignatureEnvelopeVNext, raw_triple[2], loader),
        raw_triple[3],
        _load_record(_ExternalVNextArtifactPinVNext, raw_triple[4], loader),
        raw_triple[5],
    )


def _typed_dag_from_raw(raw_dag: dict[str, object], loader: str) -> _SyntheticPathBDagInput:
    declaration = _parse_raw_triple(
        raw_dag["declaration"],
        "legacy_search_impossibility_declaration",
        loader,
    )
    thesis = _parse_raw_triple(raw_dag["thesis"], "one_thesis_contract", loader)
    snapshot = _parse_raw_triple(
        raw_dag["snapshot"],
        "new_upstream_scientific_snapshot",
        loader,
    )
    reviews = tuple(
        _parse_raw_triple(review, review[0]["review_role"], loader)
        for review in raw_dag["reviews"]
    )
    receipt = _parse_raw_triple(
        raw_dag["receipt"],
        "provenance_migration_receipt",
        loader,
    )
    return _SyntheticPathBDagInput.from_components(
        declaration=declaration,
        thesis=thesis,
        snapshot=snapshot,
        reviews=reviews,
        receipt=receipt,
    )


def _valid_dag(*, loader: str = "from_dict", **kwargs: object) -> _SyntheticPathBDagInput:
    return _typed_dag_from_raw(_raw_dag(**kwargs), loader)


def _two_store_declaration_dict(*, swap_evidence: bool = False, swap_search: bool = False) -> dict[str, object]:
    custodians: list[dict[str, object]] = []
    stores: list[dict[str, object]] = []
    objects: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    approvals: list[str] = []
    for index in range(2):
        searched_index = 1 - index if swap_search else index
        approval = str(index + 1) * 64
        approvals.append(approval)
        custodians.append(
            _seal(
                {
                    "custodian_id": f"custodian-{index}",
                    "custodian_role": "legacy-record-custodian",
                    "contacted_at_utc": f"2026-08-20T00:00:0{index + 1}Z",
                    "completed_at_utc": "2026-08-20T00:00:07Z",
                    "searched_store_ids": [f"store-{searched_index}"],
                    "searched_object_version_keys": [f"object-version-{searched_index}"],
                    "search_method": "exhaustive_immutable_version_search",
                    "search_result": "exact_raw_bytes_not_found",
                    "approval_member_identity": f"member:custodian-approval-{index}",
                    "approval_file_sha256": approval,
                },
                "row_sha256",
            )
        )
        evidence_index = 1 - index if swap_evidence else index
        stores.append(
            _seal(
                {
                    "store_id": f"store-{index}",
                    "owner_custodian_id": f"custodian-{index}",
                    "store_kind": "immutable_object_store",
                    "immutable_store_identity": f"immutable-store-{index}",
                    "store_version": f"store-version-{index}",
                    "searched_at_utc": f"2026-08-20T00:00:0{index + 2}Z",
                    "search_scope": "all_known_namespaces_and_versions",
                    "all_known_namespaces_examined": True,
                    "evidence_member_identities": [f"member:evidence-{evidence_index}"],
                    "search_result": "exact_raw_bytes_not_found",
                },
                "row_sha256",
            )
        )
        objects.append(
            _seal(
                {
                    "object_version_key": f"object-version-{index}",
                    "store_id": f"store-{index}",
                    "immutable_object_identity": f"immutable-object-{index}",
                    "immutable_object_version": f"immutable-object-version-{index}",
                    "examined_at_utc": f"2026-08-20T00:00:0{index + 3}Z",
                    "raw_object_available": False,
                    "candidate_file_count": 0,
                    "candidate_file_sha256s": [],
                    "evidence_member_identities": [f"member:evidence-{evidence_index}"],
                    "search_result": "exact_raw_bytes_not_found",
                },
                "row_sha256",
            )
        )
        evidence.append(
            _seal(
                {
                    "evidence_index": index,
                    "occurred_at_utc": f"2026-08-20T00:00:0{index + 5}Z",
                    "custodian_identity": f"custodian-{index}",
                    "immutable_store_identity": f"immutable-store-{index}",
                    "immutable_object_identity": f"immutable-object-{index}",
                    "immutable_object_version": f"immutable-object-version-{index}",
                    "evidence_member_identity": f"member:evidence-{index}",
                    "evidence_file_sha256": str(index + 3) * 64,
                    "evidence_file_byte_count": 10 + index,
                },
                "row_sha256",
            )
        )
    payload = _declaration_dict()
    payload.update(
        {
            "known_custodian_ids": ["custodian-0", "custodian-1"],
            "known_store_ids": ["store-0", "store-1"],
            "known_object_version_keys": ["object-version-0", "object-version-1"],
            "custodian_search_rows": custodians,
            "store_search_rows": stores,
            "object_version_search_rows": objects,
            "custody_evidence_rows": evidence,
            "custodian_approval_member_sha256s": sorted(approvals),
        }
    )
    return _reseed(payload, "declaration_sha256", None)


class PublicContractLoaderTests(unittest.TestCase):
    def test_exact_public_contract_exports(self) -> None:
        self.assertEqual(
            acquisition.__all__,
            (
                "ExternalAuthorityAcquisitionError",
                "NeedsContextError",
                "negative_fixture_registry",
                "validate_synthetic_external_authority_acquisition",
                "require_authenticated_external_authority_acquisition",
            ),
        )
        self.assertTrue(issubclass(NeedsContextError, ExternalAuthorityAcquisitionError))


class CanonicalRecordTests(unittest.TestCase):
    def test_envelope_exact_keys_canonical_json_and_hand_derived_hash(self) -> None:
        artifact = _thesis_dict()
        payload = _envelope_dict(
            artifact_role="one_thesis_contract",
            artifact=artifact,
            artifact_schema_version=artifact["schema_version"],
            logical_id=artifact["contract_logical_id"],
            predecessors=["0" * 64],
        )
        record = _ExternalCanonicalSignatureEnvelopeVNext.from_dict(payload)
        self.assertEqual(tuple(record.to_dict()), tuple(payload))
        self.assertEqual(record.to_dict(), payload)
        self.assertEqual(record.to_json(), _canonical(payload))
        self.assertEqual(record.envelope_sha256, _sha({k: v for k, v in payload.items() if k != "envelope_sha256"}))
        self.assertEqual(
            _ExternalCanonicalSignatureEnvelopeVNext.from_json(record.to_json()),
            record,
        )

    def test_pin_requires_exact_lengths_and_distinct_member_identities(self) -> None:
        artifact = _thesis_dict()
        envelope = _envelope_dict(
            artifact_role="one_thesis_contract",
            artifact=artifact,
            artifact_schema_version=artifact["schema_version"],
            logical_id=artifact["contract_logical_id"],
            predecessors=["0" * 64],
        )
        pin = _pin_dict(
            artifact_role="one_thesis_contract",
            artifact=artifact,
            envelope=envelope,
            predecessors=["1" * 64],
        )
        self.assertEqual(_ExternalVNextArtifactPinVNext.from_dict(pin).to_dict(), pin)
        for key, value in (("signing_public_key_byte_count", 31), ("detached_signature_byte_count", 63)):
            changed = dict(pin)
            changed[key] = value
            changed["pin_sha256"] = _sha({k: v for k, v in changed.items() if k != "pin_sha256"})
            with self.assertRaises(ExternalAuthorityAcquisitionError):
                _ExternalVNextArtifactPinVNext.from_dict(changed)
        alias = dict(pin)
        alias["detached_signature_member_identity"] = alias["signing_public_key_member_identity"]
        alias["pin_sha256"] = _sha({k: v for k, v in alias.items() if k != "pin_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _ExternalVNextArtifactPinVNext.from_dict(alias)

    def test_strict_json_rejects_ambiguous_or_noncanonical_inputs(self) -> None:
        payload = _thesis_dict()
        cls = _OneThesisContractVNext
        canonical = _canonical(payload)
        bad_json = (
            " " + canonical,
            canonical + "\n",
            "\ufeff" + canonical,
            canonical.replace('"contract_version":1', '"contract_version":-0.0'),
            canonical.replace('"contract_version":1', '"contract_version":NaN'),
            canonical.replace('"contract_version":1', '"contract_version":1,"contract_version":1'),
        )
        for text in bad_json:
            with self.subTest(text=text[:40]):
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    cls.from_json(text)
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            cls.from_json(b"{}")
        nested_tuple = dict(payload)
        nested_tuple["endpoint_hierarchy"] = tuple(ENDPOINT_HIERARCHY)
        nested_tuple["contract_sha256"] = _sha({k: v for k, v in nested_tuple.items() if k != "contract_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            cls.from_dict(nested_tuple)

    def test_exact_dict_shape_type_and_self_hash_fail_closed(self) -> None:
        payload = _thesis_dict()
        variants = []
        missing = dict(payload)
        missing.pop("cats_role")
        variants.append(missing)
        extra = dict(payload)
        extra["foreign"] = "value"
        variants.append(extra)
        non_string = dict(payload)
        non_string[1] = non_string.pop("contract_version")
        variants.append(non_string)
        bool_as_int = dict(payload)
        bool_as_int["contract_version"] = True
        variants.append(bool_as_int)
        stale = dict(payload)
        stale["contract_sha256"] = "0" * 64
        variants.append(stale)
        for variant in variants:
            with self.subTest(keys=tuple(variant)):
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _OneThesisContractVNext.from_dict(variant)

    def test_all_internal_records_are_frozen_slotted_sealed_and_roundtrip(self) -> None:
        dag = _valid_dag()
        records = [
            dag.declaration[0],
            *dag.declaration[0].custodian_search_rows,
            *dag.declaration[0].store_search_rows,
            *dag.declaration[0].object_version_search_rows,
            *dag.declaration[0].custody_evidence_rows,
            dag.thesis[0],
            dag.snapshot[0],
            *(item[0] for item in dag.reviews),
            dag.receipt[0],
            dag.declaration[2],
            dag.declaration[4],
        ]
        for record in records:
            with self.subTest(record=type(record).__name__):
                self.assertTrue(dataclasses.is_dataclass(record))
                self.assertFalse(hasattr(record, "__dict__"))
                with self.assertRaises((AttributeError, dataclasses.FrozenInstanceError)):
                    setattr(record, next(iter(record.to_dict())), "changed")
                self.assertEqual(type(record).from_dict(record.to_dict()), record)
                self.assertEqual(type(record).from_json(record.to_json()), record)
                with self.assertRaises(TypeError):
                    type(record)()
                bypass = object.__new__(type(record))
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    bypass.to_dict()
        with self.assertRaises(TypeError):
            class _ForbiddenSubclass(_OneThesisContractVNext):
                pass

    def test_dag_fixture_and_result_records_block_direct_object_new_and_subclass_bypasses(self) -> None:
        for record in (
            negative_fixture_registry()[0],
            validate_synthetic_external_authority_acquisition(),
        ):
            with self.subTest(record_type=type(record).__name__):
                with self.assertRaises(TypeError):
                    type(record)()
                bypass = object.__new__(type(record))
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    bypass.to_dict()
                with self.assertRaises(TypeError):
                    type(f"Forbidden{type(record).__name__}", (type(record),), {})

        with self.assertRaises(TypeError):
            _SyntheticPathBDagInput()
        incomplete_dag = object.__new__(_SyntheticPathBDagInput)
        try:
            _validate_synthetic_path_b_metadata(incomplete_dag)
        except Exception as error:  # noqa: BLE001 - assertion proves the exact boundary type.
            self.assertIs(type(error), ExternalAuthorityAcquisitionError)
        else:
            self.fail("incomplete DAG bypass was accepted")
        with self.assertRaises(TypeError):
            type("ForbiddenSyntheticPathBDagInput", (_SyntheticPathBDagInput,), {})


class ScientificContractTests(unittest.TestCase):
    def test_exact_one_thesis_literals_and_22_policy_roster(self) -> None:
        record = _OneThesisContractVNext.from_dict(_thesis_dict())
        self.assertEqual(record.e3_mandatory_policy_ids, POLICY_IDS)
        self.assertEqual(record.endpoint_hierarchy, ENDPOINT_HIERARCHY)
        self.assertEqual(record.kill_chain, KILL_CHAIN)
        self.assertEqual(record.architecture_domain_role, "flagship_primary_domain")
        self.assertEqual(record.jci_domain_role, "independent_e2_e3_replication_no_pooling")
        self.assertEqual(record.cross_domain_pooling, "forbidden")

    def test_fully_rehashed_scientific_semantic_drifts_reject(self) -> None:
        changes = {
            "thesis_id": "resource_routing_only",
            "architecture_domain_role": "secondary_domain",
            "jci_domain_role": "pooled_replication",
            "cats_role": "causal_contribution",
            "e1_role": "causal_primary",
            "e2_role": "observational_mechanism",
            "e3_primary_comparator": "retrospective_oracle",
            "retrospective_oracle_role": "deployable_primary",
            "e4_role": "same_data_frontier",
        }
        for key, value in changes.items():
            changed = dict(_thesis_dict())
            changed[key] = value
            changed["contract_sha256"] = _sha({k: v for k, v in changed.items() if k != "contract_sha256"})
            with self.subTest(key=key):
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _OneThesisContractVNext.from_json(_canonical(changed))
        changed = dict(_thesis_dict())
        changed["e3_mandatory_policy_ids"] = list(POLICY_IDS[:-1])
        changed["contract_sha256"] = _sha({k: v for k, v in changed.items() if k != "contract_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _OneThesisContractVNext.from_dict(changed)
        changed = dict(_thesis_dict())
        changed["kill_chain"] = list(KILL_CHAIN[:-1])
        changed["contract_sha256"] = _sha({k: v for k, v in changed.items() if k != "contract_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _OneThesisContractVNext.from_dict(changed)

    def test_coordinated_mutable_production_constant_substitution_cannot_change_contract(self) -> None:
        drift = dict(_thesis_dict())
        drift["cats_role"] = "causal_contribution"
        drift["contract_sha256"] = _sha({k: v for k, v in drift.items() if k != "contract_sha256"})
        prior = acquisition._ONE_THESIS_SCALARS
        acquisition._ONE_THESIS_SCALARS = {**prior, "cats_role": "causal_contribution"}
        try:
            with self.assertRaises(ExternalAuthorityAcquisitionError):
                _OneThesisContractVNext.from_dict(drift)
        finally:
            acquisition._ONE_THESIS_SCALARS = prior

    def test_fully_rehashed_task6_namespace_in_free_text_is_not_upstream_authority(self) -> None:
        changed = dict(_thesis_dict())
        changed["external_scientist_identity"] = "task6-vnext-workspace-owner"
        changed["contract_sha256"] = _sha({k: v for k, v in changed.items() if k != "contract_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _OneThesisContractVNext.from_dict(changed)


class ProvenanceDagTests(unittest.TestCase):
    def test_stage_specific_helpers_prove_root_is_reached_only_for_root_attacks(self) -> None:
        self.assertTrue(
            hasattr(type(self), "_assert_leaf_rejects"),
            "leaf/parser rejection helper is missing",
        )
        self.assertTrue(
            hasattr(type(self), "_assert_root_rejects"),
            "root-only rejection helper is missing",
        )
        root_calls = 0
        original_validator = globals()["_validate_synthetic_path_b_metadata"]

        def counted_validator(value: _SyntheticPathBDagInput) -> None:
            nonlocal root_calls
            root_calls += 1
            original_validator(value)

        globals()["_validate_synthetic_path_b_metadata"] = counted_validator
        try:
            self._assert_leaf_rejects(
                leaf_role="independent_science_migration_review",
                leaf_component="artifact",
                artifact_updates={
                    "independent_science_migration_review": {
                        "reviewer_identity": f"hostile:{LEGACY_SHA}"
                    }
                },
            )
            self.assertEqual(root_calls, 0)
            self._assert_root_rejects(
                envelope_updates={
                    role: {"external_verifier_package_version": "shared-review-version"}
                    for role in REVIEW_ROLES
                }
            )
            self.assertEqual(root_calls, 2)
        finally:
            globals()["_validate_synthetic_path_b_metadata"] = original_validator

    def _assert_leaf_rejects(
        self,
        *,
        leaf_role: str,
        leaf_component: str,
        **kwargs: object,
    ) -> None:
        component_index_and_type = {
            "artifact": (0, _artifact_type_for_role(leaf_role)),
            "envelope": (2, _ExternalCanonicalSignatureEnvelopeVNext),
            "pin": (4, _ExternalVNextArtifactPinVNext),
        }
        if leaf_component not in component_index_and_type:
            raise AssertionError(f"unknown leaf component: {leaf_component}")
        component_index, record_type = component_index_and_type[leaf_component]
        for loader in ("from_dict", "from_json"):
            with self.subTest(loader=loader, leaf_role=leaf_role, leaf_component=leaf_component):
                raw_dag = _raw_dag(**kwargs)
                self.assertEqual(len(raw_dag["reviews"]), 3)
                self.assertEqual(len(raw_dag["receipt"]), 6)
                raw_leaf = _raw_triple_by_role(raw_dag, leaf_role)[component_index]
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _load_record(record_type, raw_leaf, loader)
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _typed_dag_from_raw(raw_dag, loader)

    def _assert_root_rejects(self, **kwargs: object) -> None:
        for loader in ("from_dict", "from_json"):
            with self.subTest(loader=loader, mutation=kwargs):
                raw_dag = _raw_dag(**kwargs)
                dag = _typed_dag_from_raw(raw_dag, loader)
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _validate_synthetic_path_b_metadata(dag)

    def test_every_role_domain_has_exact_terminal_nul_in_dict_and_json(self) -> None:
        artifact = _thesis_dict()
        for role, domain in TERMINATED_ROLE_DOMAINS.items():
            envelope = _envelope_dict(
                artifact_role=role,
                artifact=artifact,
                artifact_schema_version={
                    "legacy_search_impossibility_declaration": "ace.iclr2027.legacy_search_impossibility_declaration.vnext",
                    "one_thesis_contract": "ace.iclr2027.one_thesis_contract.vnext",
                    "new_upstream_scientific_snapshot": "ace.iclr2027.new_upstream_scientific_snapshot.vnext",
                    "independent_science_migration_review": "ace.iclr2027.independent_migration_review.vnext",
                    "independent_provenance_migration_review": "ace.iclr2027.independent_migration_review.vnext",
                    "independent_security_migration_review": "ace.iclr2027.independent_migration_review.vnext",
                    "provenance_migration_receipt": "ace.iclr2027.provenance_migration_receipt.vnext",
                }[role],
                logical_id=f"logical:{role}",
                predecessors=[],
            )
            envelope = _reseed(
                envelope,
                "envelope_sha256",
                {"detached_message_domain": domain},
            )
            pin = _pin_dict(
                artifact_role=role,
                artifact=artifact,
                envelope=envelope,
                predecessors=[],
            )
            for loader in ("from_dict", "from_json"):
                with self.subTest(role=role, loader=loader):
                    envelope_record = _load_record(
                        _ExternalCanonicalSignatureEnvelopeVNext,
                        envelope,
                        loader,
                    )
                    pin_record = _load_record(_ExternalVNextArtifactPinVNext, pin, loader)
                    self.assertEqual(envelope_record.detached_message_domain, domain)
                    self.assertEqual(pin_record.detached_message_domain, domain)
                    self.assertIn("\\u0000", envelope_record.to_json())
                    self.assertIn("\\u0000", pin_record.to_json())

    def test_full_dag_rejects_forbidden_tokens_in_every_envelope_and_pin(self) -> None:
        forbidden = FORBIDDEN_MEMORY_SHAS + (LEGACY_SHA, "task6", "task7")
        for role in ROLE_DOMAINS:
            for token in forbidden:
                self._assert_leaf_rejects(
                    leaf_role=role,
                    leaf_component="envelope",
                    envelope_updates={
                        role: {"external_verifier_package_version": f"version:{role}:{token}"}
                    }
                )
                pin_field = (
                    "external_platform_signature_sha256"
                    if len(token) == 64
                    else "external_platform_signature_member_identity"
                )
                self._assert_leaf_rejects(
                    leaf_role=role,
                    leaf_component="pin",
                    pin_updates={role: {pin_field: token}},
                )

    def test_full_dag_and_leaf_parsers_enforce_field_aware_forbidden_scope(self) -> None:
        artifact_attacks = (
            ("legacy_search_impossibility_declaration", "responsible_migration_owner_identity"),
            ("one_thesis_contract", "external_scientist_identity"),
            ("new_upstream_scientific_snapshot", "snapshot_logical_id"),
            ("independent_science_migration_review", "reviewer_identity"),
            ("independent_provenance_migration_review", "reviewer_identity"),
            ("independent_security_migration_review", "reviewer_identity"),
            ("provenance_migration_receipt", "migration_logical_id"),
        )
        for role, field in artifact_attacks:
            tokens = FORBIDDEN_MEMORY_SHAS + (LEGACY_SHA, "task6", "task7")
            for token in tokens:
                self._assert_leaf_rejects(
                    leaf_role=role,
                    leaf_component="artifact",
                    artifact_updates={role: {field: f"hostile:{token}"}}
                )
        # These are the only two field-aware exceptions in a valid full DAG.
        dag = _valid_dag()
        self.assertEqual(dag.declaration[0].expected_legacy_raw_sha256, LEGACY_SHA)
        self.assertEqual(
            dag.receipt[0].migration_status,
            "reviewed_non_continuity_snapshot_ready_for_task6_vnext_authority",
        )
        self.assertIsNone(_validate_synthetic_path_b_metadata(dag))

    def test_full_dag_reviewer_authority_dimensions_are_distinct_and_nonoverlapping(self) -> None:
        shared_dimensions = (
            ("envelope", "external_verifier_package_version", "shared-version"),
            ("envelope", "signing_public_key_member_identity", "member:shared-review-key"),
            ("envelope", "detached_signature_sha256", "6" * 64),
            ("envelope", "rotation_provenance_sha256", "7" * 64),
            ("pin", "external_verifier_executable_member_identity", "member:shared-review-executable"),
            ("pin", "external_platform_signature_sha256", "8" * 64),
        )
        for location, field, value in shared_dimensions:
            updates = {role: {field: value} for role in REVIEW_ROLES}
            self._assert_root_rejects(
                envelope_updates=updates if location == "envelope" else {},
                pin_updates=updates if location == "pin" else {},
            )

        producer_marker = _sha("legacy_search_impossibility_declaration")[:12]
        producer_overlaps = (
            ("envelope", "external_verifier_package_version", f"version:{producer_marker}"),
            ("envelope", "signing_public_key_member_identity", f"member:key:{producer_marker}"),
            ("envelope", "detached_signature_sha256", producer_marker.ljust(64, "b")),
            ("envelope", "rotation_provenance_sha256", producer_marker.ljust(64, "d")),
            ("pin", "external_verifier_executable_member_identity", f"member:executable:{producer_marker}"),
            ("pin", "external_platform_signature_sha256", producer_marker.ljust(64, "e")),
        )
        science_role = "independent_science_migration_review"
        for location, field, value in producer_overlaps:
            updates = {science_role: {field: value}}
            self._assert_root_rejects(
                envelope_updates=updates if location == "envelope" else {},
                pin_updates=updates if location == "pin" else {},
            )
        self._assert_root_rejects(
            envelope_updates={
                science_role: {"external_verifier_package_version": f"key:{producer_marker}"}
            }
        )
        self._assert_root_rejects(
            reviewer_identity_overrides={science_role: "external-domain-scientist"}
        )

    def test_full_dag_rejects_cross_swapped_store_object_and_custodian_search_bijections(self) -> None:
        self._assert_leaf_rejects(
            leaf_role="legacy_search_impossibility_declaration",
            leaf_component="artifact",
            declaration_payload=_two_store_declaration_dict(swap_evidence=True)
        )
        self._assert_leaf_rejects(
            leaf_role="legacy_search_impossibility_declaration",
            leaf_component="artifact",
            declaration_payload=_two_store_declaration_dict(swap_search=True)
        )

    def test_complete_synthetic_dag_relational_validation_returns_none(self) -> None:
        self.assertIsNone(_validate_synthetic_path_b_metadata(_valid_dag()))

    def test_declaration_search_closure_and_e774_scope_are_fail_closed(self) -> None:
        changes = (
            ("expected_legacy_raw_sha256", "0" * 64),
            ("legacy_continuity", True),
            ("legacy_equivalence", True),
            ("unsearched_store_ids", ["store-0"]),
            ("known_custodian_ids", ["foreign-custodian"]),
            ("legacy_recovery_status", "recovered"),
        )
        for key, value in changes:
            changed = dict(_declaration_dict())
            changed[key] = value
            changed["declaration_sha256"] = _sha({k: v for k, v in changed.items() if k != "declaration_sha256"})
            with self.subTest(key=key):
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _LegacySearchImpossibilityDeclarationVNext.from_dict(changed)

    def test_search_rows_reject_fully_rehashed_native_time_and_census_drifts(self) -> None:
        changed = dict(_object_row_dict())
        changed["raw_object_available"] = True
        changed["row_sha256"] = _sha({k: v for k, v in changed.items() if k != "row_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _ObjectVersionSearchRowVNext.from_dict(changed)
        changed = dict(_store_row_dict())
        changed["all_known_namespaces_examined"] = 1
        changed["row_sha256"] = _sha({k: v for k, v in changed.items() if k != "row_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _StoreSearchRowVNext.from_dict(changed)
        changed = dict(_custodian_row_dict())
        changed["completed_at_utc"] = "2026-08-19T23:59:59Z"
        changed["row_sha256"] = _sha({k: v for k, v in changed.items() if k != "row_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _CustodianSearchRowVNext.from_dict(changed)
        changed = dict(_evidence_row_dict())
        changed["evidence_index"] = True
        changed["row_sha256"] = _sha({k: v for k, v in changed.items() if k != "row_sha256"})
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _CustodyEvidenceRowVNext.from_dict(changed)

    def test_declaration_rejects_fully_rehashed_foreign_evidence_physical_joins(self) -> None:
        declaration = dict(_declaration_dict())
        evidence = dict(declaration["custody_evidence_rows"][0])
        evidence["immutable_object_identity"] = "foreign-object"
        evidence["row_sha256"] = _sha({k: v for k, v in evidence.items() if k != "row_sha256"})
        declaration["custody_evidence_rows"] = [evidence]
        declaration["declaration_sha256"] = _sha(
            {k: v for k, v in declaration.items() if k != "declaration_sha256"}
        )
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _LegacySearchImpossibilityDeclarationVNext.from_dict(declaration)

    def test_snapshot_and_review_reject_foreign_or_downstream_joins(self) -> None:
        declaration = _declaration_dict()
        thesis = _thesis_dict()
        snapshot = _snapshot_dict(declaration, thesis)
        for digest in FORBIDDEN_MEMORY_SHAS:
            changed = dict(snapshot)
            changed["one_thesis_contract_file_sha256"] = digest
            changed["snapshot_sha256"] = _sha({k: v for k, v in changed.items() if k != "snapshot_sha256"})
            with self.assertRaises(ExternalAuthorityAcquisitionError):
                _NewUpstreamScientificSnapshotVNext.from_dict(changed)
            with self.assertRaises(ExternalAuthorityAcquisitionError):
                _NewUpstreamScientificSnapshotVNext.from_json(_canonical(changed))
        review = _review_dict(REVIEW_ROLES[0], declaration, thesis, snapshot)
        for digest in FORBIDDEN_MEMORY_SHAS:
            changed = dict(review)
            changed["reviewed_snapshot_file_sha256"] = digest
            changed["review_sha256"] = _sha({k: v for k, v in changed.items() if k != "review_sha256"})
            with self.assertRaises(ExternalAuthorityAcquisitionError):
                _IndependentMigrationReviewVNext.from_dict(changed)
            with self.assertRaises(ExternalAuthorityAcquisitionError):
                _IndependentMigrationReviewVNext.from_json(_canonical(changed))

    def test_dag_rejects_review_role_domain_key_package_and_join_attacks(self) -> None:
        dag = _valid_dag()
        review = dag.reviews[0]
        envelope_dict = review[2].to_dict()
        envelope_dict["artifact_role"] = "independent_science_migration_review"
        envelope_dict["detached_message_domain"] = ROLE_DOMAINS["independent_science_migration_review"]
        envelope_dict["envelope_sha256"] = _sha({k: v for k, v in envelope_dict.items() if k != "envelope_sha256"})
        hostile_envelope = _ExternalCanonicalSignatureEnvelopeVNext.from_dict(envelope_dict)
        hostile_review = (review[0], review[1], hostile_envelope, _file_sha(envelope_dict), review[4], review[5])
        changed_reviews = (hostile_review,) + dag.reviews[1:]
        hostile_dag = _SyntheticPathBDagInput.from_components(
            declaration=dag.declaration,
            thesis=dag.thesis,
            snapshot=dag.snapshot,
            reviews=changed_reviews,
            receipt=dag.receipt,
        )
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _validate_synthetic_path_b_metadata(hostile_dag)

    def test_dag_rejects_foreign_lookalikes_before_property_access(self) -> None:
        class Hostile:
            accesses = 0

            def __getattribute__(self, name: str) -> object:
                type(self).accesses += 1
                raise AssertionError(name)

        dag = _valid_dag()
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _SyntheticPathBDagInput.from_components(
                declaration=(Hostile(),) + dag.declaration[1:],
                thesis=dag.thesis,
                snapshot=dag.snapshot,
                reviews=dag.reviews,
                receipt=dag.receipt,
            )
        self.assertEqual(Hostile.accesses, 0)

    def test_dag_rejects_fully_rehashed_migration_owner_as_reviewer(self) -> None:
        dag = _valid_dag(
            reviewer_identity_overrides={
                "independent_science_migration_review": "external-migration-owner"
            }
        )
        with self.assertRaises(ExternalAuthorityAcquisitionError):
            _validate_synthetic_path_b_metadata(dag)


class RegistryAndResultTests(unittest.TestCase):
    def test_negative_registry_exact_order_mapping_metadata_and_hashes(self) -> None:
        registry = negative_fixture_registry()
        self.assertIsInstance(registry, tuple)
        self.assertEqual(tuple(item.fixture_id for item in registry), FIXTURE_IDS)
        self.assertEqual(tuple(item.fixture_id for item in registry), tuple(sorted(FIXTURE_IDS, key=lambda x: x.encode("utf-8"))))
        for item in registry:
            category, outcome = FIXTURE_OUTCOMES[item.fixture_id]
            self.assertEqual(item.category, category)
            self.assertEqual(item.required_outcome, outcome)
            self.assertEqual(item.mutation_description, FIXTURE_DESCRIPTIONS[item.fixture_id])
            self.assertEqual(_NegativeFixtureSpec.from_dict(item.to_dict()), item)
            self.assertFalse(hasattr(item, "__dict__"))
        self.assertEqual(len({item.fixture_sha256 for item in registry}), 26)
        expected_rows = []
        for fixture_id in FIXTURE_IDS:
            category, outcome = FIXTURE_OUTCOMES[fixture_id]
            unsealed = {
                "schema_version": "ace.iclr2027.external_authority_negative_fixture.v1",
                "fixture_id": fixture_id,
                "category": category,
                "mutation_description": FIXTURE_DESCRIPTIONS[fixture_id],
                "required_outcome": outcome,
            }
            expected_rows.append(_seal(unsealed, "fixture_sha256"))
        self.assertEqual([item.to_dict() for item in registry], expected_rows)
        self.assertEqual(_sha(expected_rows), EXPECTED_REGISTRY_SHA)
        with self.assertRaises(TypeError):
            registry[0] = registry[1]

    def test_current_result_exact_no_go_and_test_owned_canonical_self_hash(self) -> None:
        result = validate_synthetic_external_authority_acquisition()
        self.assertIsInstance(result, _ExternalAuthorityAcquisitionResult)
        expected_without_hash = {
            "schema_version": "ace.iclr2027.external_authority_acquisition_result.v1",
            "binding_brief_sha256": BRIEF_SHA,
            "science_review_sha256": SCIENCE_REVIEW_SHA,
            "security_review_sha256": SECURITY_REVIEW_SHA,
            "selected_path": "path_b_user_approved_but_not_externally_authenticated",
            "authority_mode": "synthetic",
            "status": "no_go",
            "reason_codes": list(REASON_IDS),
            "negative_fixture_registry_sha256": EXPECTED_REGISTRY_SHA,
            "external_artifact_count": 0,
            "external_signature_count": 0,
            "external_review_count": 0,
            "task6_vnext_authority_count": 0,
            "task6_vnext_implementation_count": 0,
            "source_read_count": 0,
            "data_read_count": 0,
            "result_read_count": 0,
            "rate_read_count": 0,
            "simulation_draw_count": 0,
            "model_call_count": 0,
            "tool_call_count": 0,
            "paid_call_count": 0,
            "official_result_eligible": False,
            "synthetic_only": True,
        }
        expected = _seal(expected_without_hash, "result_sha256")
        self.assertEqual(result.to_dict(), expected)
        self.assertEqual(result.to_json(), EXPECTED_RESULT_JSON)
        self.assertEqual(_canonical(expected), EXPECTED_RESULT_JSON)
        self.assertEqual(result.result_sha256, EXPECTED_RESULT_SHA)
        self.assertEqual(_sha(expected_without_hash), EXPECTED_RESULT_SHA)
        self.assertEqual(_ExternalAuthorityAcquisitionResult.from_json(result.to_json()), result)

    def test_fully_rehashed_authenticated_pass_official_and_counter_upgrades_reject(self) -> None:
        baseline = validate_synthetic_external_authority_acquisition().to_dict()
        changes = (
            {"authority_mode": "authenticated", "status": "pass", "official_result_eligible": True, "synthetic_only": False},
            {"selected_path": "path_a_legacy_recovery"},
            {"reason_codes": []},
            {"model_call_count": 1},
            {"external_artifact_count": 7},
            {"binding_brief_sha256": "f" * 64},
        )
        for mutation in changes:
            changed = dict(baseline)
            changed.update(mutation)
            changed["result_sha256"] = _sha({k: v for k, v in changed.items() if k != "result_sha256"})
            with self.subTest(mutation=mutation):
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _ExternalAuthorityAcquisitionResult.from_dict(changed)
                with self.assertRaises(ExternalAuthorityAcquisitionError):
                    _ExternalAuthorityAcquisitionResult.from_json(_canonical(changed))

    def test_authenticated_entrypoint_rejects_before_any_property_or_protocol_access(self) -> None:
        class Hostile:
            accesses = 0

            def _trip(self) -> object:
                type(self).accesses += 1
                raise AssertionError("observer accessed")

            def __getattribute__(self, name: str) -> object:
                del name
                return object.__getattribute__(self, "_trip")()

            def __iter__(self) -> object:
                return object.__getattribute__(self, "_trip")()

            def __bool__(self) -> object:
                return object.__getattribute__(self, "_trip")()

            def __repr__(self) -> object:
                return object.__getattribute__(self, "_trip")()

            def __fspath__(self) -> object:
                return object.__getattribute__(self, "_trip")()

        with self.assertRaisesRegex(NeedsContextError, "^NEEDS_CONTEXT$"):
            require_authenticated_external_authority_acquisition(Hostile())
        self.assertEqual(Hostile.accesses, 0)


class CliAndStaticBoundaryTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    CLI = ROOT / "validate_iclr2027_external_authority_acquisition.py"

    def _run(self, option: str) -> subprocess.CompletedProcess[str]:
        self.assertIn(option, ("--help", "--current-status", "--list-negative-fixtures"))
        return subprocess.run(
            [sys.executable, "-B", "validate_iclr2027_external_authority_acquisition.py", option],
            cwd=self.ROOT,
            shell=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_status_and_fixture_cli_are_fixed_canonical_and_deterministic(self) -> None:
        help_run = self._run("--help")
        self.assertEqual(help_run.returncode, 0)
        self.assertIn("--current-status", help_run.stdout)
        first = self._run("--current-status")
        second = self._run("--current-status")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stderr, "")
        self.assertEqual(first.stdout, second.stdout)
        self.assertTrue(first.stdout.endswith("\n"))
        self.assertFalse(first.stdout.endswith("\n\n"))
        self.assertEqual(json.loads(first.stdout), validate_synthetic_external_authority_acquisition().to_dict())
        fixtures = self._run("--list-negative-fixtures")
        self.assertEqual(fixtures.returncode, 0)
        self.assertEqual(fixtures.stderr, "")
        self.assertEqual(json.loads(fixtures.stdout), [item.to_dict() for item in negative_fixture_registry()])

    def test_unknown_source_path_key_signature_and_output_options_fail(self) -> None:
        for option in ("--source", "--path", "--key", "--signature", "--output", "--rate"):
            completed = subprocess.run(
                [sys.executable, "-B", str(self.CLI), option, "sentinel"],
                cwd=self.ROOT,
                shell=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            with self.subTest(option=option):
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")

    def test_production_ast_has_no_io_crypto_process_domain_or_task6_imports(self) -> None:
        paths = (
            ("production", self.ROOT / "iclr2027" / "external_authority_acquisition.py"),
            ("cli", self.CLI),
        )
        for target, path in paths:
            with self.subTest(path=path.name):
                self.assertEqual(
                    _ast_policy_violations_for_target(path.read_text(encoding="utf-8"), target),
                    (),
                )

    def test_ast_policy_rejects_dynamic_and_attribute_call_mutations_for_both_targets(self) -> None:
        self.assertIn(
            "_ast_policy_violations",
            globals(),
            "mutation-sensitive AST policy helper is missing",
        )
        mutations = (
            "open('x')",
            "__import__('safe_module')",
            "eval('1 + 1')",
            "exec('value = 1')",
            "compile('1 + 1', 'fixture', 'eval')",
            "import importlib\nimportlib.import_module('safe_module')",
            "from importlib import import_module as load\nload('safe_module')",
            "from pathlib import Path\nPath('x').read_text()",
            "import os\nos.remove('x')",
            "import socket\nsocket.socket().connect(('127.0.0.1', 1))",
            "import subprocess\nsubprocess.run(['echo', 'x'])",
            "from cryptography.hazmat.primitives.asymmetric import ed25519\ned25519.Ed25519PrivateKey.generate()",
            "__import__('iclr2027.task6_vnext')",
        )
        for source in mutations:
            with self.subTest(source=source):
                self.assertTrue(_ast_policy_violations(source))
        for path in (self.ROOT / "iclr2027" / "external_authority_acquisition.py", self.CLI):
            with self.subTest(path=path.name):
                self.assertEqual(_ast_policy_violations(path.read_text(encoding="utf-8")), ())

    def test_ast_policy_rejects_builtins_assignment_and_getattr_evasions(self) -> None:
        mutations = (
            "import builtins\nbuiltins.open('x')",
            "import builtins\nbuiltins.eval('1 + 1')",
            "import builtins\nbuiltins.exec('value = 1')",
            "import builtins\nbuiltins.compile('1', 'fixture', 'eval')",
            "import builtins\nbuiltins.__import__('safe_module')",
            "from builtins import open as f\nf('x')",
            "from builtins import eval as f\nf('1 + 1')",
            "from builtins import exec as f\nf('value = 1')",
            "from builtins import compile as f\nf('1', 'fixture', 'eval')",
            "from builtins import __import__ as f\nf('safe_module')",
            "f = open\nf('x')",
            "f = eval\nf('1 + 1')",
            "f = exec\nf('value = 1')",
            "f = compile\nf('1', 'fixture', 'eval')",
            "f = __import__\nf('safe_module')",
            "import builtins\nf = builtins.open\nf('x')",
            "import importlib\nload = importlib.import_module\nload('safe_module')",
            "getattr(__builtins__, 'open')('x')",
            "getattr(__builtins__, 'eval')('1 + 1')",
            "getattr(__builtins__, 'exec')('value = 1')",
            "getattr(__builtins__, 'compile')('1', 'fixture', 'eval')",
            "getattr(__builtins__, '__import__')('safe_module')",
            "import builtins\ngetattr(builtins, 'open')('x')",
            "import builtins\ngetattr(builtins, '__import__')('safe_module')",
            "getattr(__builtins__, '__import__')('iclr2027.task6_vnext')",
        )
        for source in mutations:
            with self.subTest(source=source):
                self.assertTrue(_ast_policy_violations(source))

    def test_ast_policy_rejects_every_alias_target_shape_in_both_real_sources(self) -> None:
        mutations = (
            "first = second = open\nfirst('x')",
            "first = second = __import__\nsecond('safe_module')",
            "import builtins\nfirst = second = builtins.open\nfirst('x')",
            "first = second = __builtins__.__import__\nfirst('safe_module')",
            "from builtins import open as source\nfirst = second = source\nsecond('x')",
            "from builtins import __import__ as source\nfirst = second = source\nfirst('safe_module')",
            "import builtins\nvalue: object = builtins.open\nvalue('x')",
            "value: object = __builtins__.__import__\nvalue('safe_module')",
            "value: object = getattr(__builtins__, 'compile')\nvalue('1', 'fixture', 'eval')",
            "if (value := eval):\n    value('1 + 1')",
            "first, second = open, exec\nfirst('x')",
            "[first, second] = [compile, __import__]\nsecond('safe_module')",
            "first, *rest = (open, eval)\nfirst('x')",
            "(first, (second, third)) = (open, (eval, exec))\nthird('value = 1')",
            "import builtins\nsource = builtins.open\nfirst = source\nsecond = first\nsecond('x')",
            "source = getattr(__builtins__, '__import__')\nfirst = source\nsecond = first\nsecond('iclr2027.task6_vnext')",
        )
        real_sources = (
            ("production", self.ROOT / "iclr2027" / "external_authority_acquisition.py"),
            ("cli", self.CLI),
        )
        for target, path in real_sources:
            base_source = path.read_text(encoding="utf-8")
            for mutation in mutations:
                with self.subTest(target=target, mutation=mutation):
                    self.assertTrue(_ast_policy_violations(f"{base_source}\n{mutation}\n"))

    def test_ast_policy_rejects_forbidden_references_in_every_ast_context(self) -> None:
        mutations = (
            "def invoke(fn=open):\n    return fn",
            "import builtins\ndef invoke(*, fn=builtins.eval):\n    return fn",
            "def invoke(fn=__builtins__.__import__):\n    return fn",
            "def invoke(fn=getattr(__builtins__, 'compile')):\n    return fn",
            "(lambda fn=exec: fn)",
            "(lambda fn=open: fn)",
            "def expose():\n    return open",
            "import builtins\ndef expose():\n    return builtins.eval",
            "def expose():\n    return getattr(__builtins__, '__import__')",
            "def expose():\n    yield exec",
            "def expose():\n    yield from (compile,)",
            "for fn in (open,):\n    pass",
            "import builtins\nfor fn in (builtins.open,):\n    pass",
            "[fn for fn in (eval,)]",
            "(fn for fn in (__import__,))",
            "{fn for fn in (compile,)}",
            "@open\ndef decorated():\n    pass",
            "import builtins\n@builtins.eval\ndef decorated():\n    pass",
            "class Derived(open):\n    pass",
            "class Derived(metaclass=eval):\n    pass",
            "setattr(holder, 'fn', open)",
            "setattr(holder, 'fn', getattr(__builtins__, '__import__'))",
            "holder.append(compile)",
            "holder.update(fn=exec)",
            "register(open)",
            "globals()['open']",
            "locals()['eval']",
            "vars(__builtins__)['__import__']",
            "__builtins__.__import__('iclr2027.task6_vnext')",
        )
        real_sources = (
            ("production", self.ROOT / "iclr2027" / "external_authority_acquisition.py"),
            ("cli", self.CLI),
        )
        for target, path in real_sources:
            base_source = path.read_text(encoding="utf-8")
            for mutation in mutations:
                with self.subTest(target=target, mutation=mutation):
                    violations = _ast_policy_violations(f"{base_source}\n{mutation}\n")
                    self.assertTrue(violations)
                    if "task6_vnext" in mutation:
                        self.assertIn(
                            "task6-dynamic-import:iclr2027.task6_vnext",
                            violations,
                        )

    def test_ast_policy_rejects_module_registry_and_reflective_import_roots(self) -> None:
        mutations = (
            "import sys\nsys.modules['builtins'].__dict__['open']('x')",
            "import inspect\ninspect.getmodule(object)",
            "import gc\ngc.get_objects()",
            "import pickle\npickle.loads(b'x')",
            "import marshal\nmarshal.loads(b'x')",
            "import types\ntypes.FunctionType(code, globals())",
        )
        real_sources = (
            ("production", self.ROOT / "iclr2027" / "external_authority_acquisition.py"),
            ("cli", self.CLI),
        )
        for target, path in real_sources:
            base_source = path.read_text(encoding="utf-8")
            for mutation in mutations:
                with self.subTest(target=target, mutation=mutation):
                    self.assertTrue(
                        _ast_policy_violations_for_target(
                            f"{base_source}\n{mutation}\n",
                            target,
                        )
                    )

    def test_exact_per_file_import_allowlists_reject_every_form_drift(self) -> None:
        self.assertIn(
            "_ast_policy_violations_for_target",
            globals(),
            "exact per-file import allowlist helper is missing",
        )
        production = (self.ROOT / "iclr2027" / "external_authority_acquisition.py").read_text(
            encoding="utf-8"
        )
        cli = self.CLI.read_text(encoding="utf-8")
        self.assertEqual(_ast_policy_violations_for_target(production, "production"), ())
        self.assertEqual(_ast_policy_violations_for_target(cli, "cli"), ())
        extra_imports = (
            "import sys",
            "import inspect",
            "import gc",
            "import pickle",
            "import marshal",
            "import types",
            "from sys import modules",
        )
        for target, source in (("production", production), ("cli", cli)):
            for statement in extra_imports:
                with self.subTest(target=target, statement=statement):
                    self.assertTrue(
                        _ast_policy_violations_for_target(
                            f"{source}\n{statement}\n",
                            target,
                        )
                    )
        form_drifts = (
            ("production-alias", production.replace("import hashlib\n", "import hashlib as h\n", 1), "production"),
            (
                "production-from-form",
                production.replace("import hashlib\n", "from hashlib import sha256\n", 1),
                "production",
            ),
            (
                "production-member-order",
                production.replace(
                    "from dataclasses import dataclass, fields",
                    "from dataclasses import fields, dataclass",
                    1,
                ),
                "production",
            ),
            ("production-missing", production.replace("import math\n", "", 1), "production"),
            ("cli-alias", cli.replace("import argparse\n", "import argparse as args\n", 1), "cli"),
            (
                "cli-root-form",
                cli.replace(
                    "from iclr2027 import external_authority_acquisition as acquisition",
                    "import iclr2027.external_authority_acquisition as acquisition",
                    1,
                ),
                "cli",
            ),
            (
                "cli-missing",
                cli.replace("from __future__ import annotations\n", "", 1),
                "cli",
            ),
        )
        for label, source, target in form_drifts:
            with self.subTest(label=label):
                self.assertTrue(_ast_policy_violations_for_target(source, target))


if __name__ == "__main__":
    unittest.main()
