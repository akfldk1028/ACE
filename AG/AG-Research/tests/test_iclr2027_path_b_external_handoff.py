from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HANDOFF = REPO_ROOT / "docs" / "paper" / "iclr2027_oacs" / "path_b_external_handoff.md"
PRODUCTION = REPO_ROOT / "iclr2027" / "external_authority_acquisition.py"
BEGIN_CONTRACT = "<!-- BEGIN PATH_B_HANDOFF_CONTRACT_V1 -->"
END_CONTRACT = "<!-- END PATH_B_HANDOFF_CONTRACT_V1 -->"

TASK7_PROCESS_SPEC = {
    "byte_count": 71589,
    "external_custody_required": True,
    "role": "process_authority_only_not_scientific_parent",
    "sha256": "9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54",
    "transport_candidate_path": "D:/Data/25_ACE/AG/.superpowers/sdd/2026-08-20-obligation-aware-coordination/task-7-external-authority-acquisition-brief.md",
}
TASK5_INPUTS = (
    {
        "role": "identification_and_analysis_plan",
        "transport_candidate_path": "D:/Data/25_ACE/AG/.superpowers/sdd/2026-08-20-obligation-aware-coordination/task-5-identification-and-analysis-plan.md",
        "byte_count": 63630,
        "sha256": "2809048fa71d0f2458db13f7590c61f0f28674f2195c3d8690a45193df517299",
    },
    {
        "role": "scientific_brief",
        "transport_candidate_path": "D:/Data/25_ACE/AG/.superpowers/sdd/2026-08-20-obligation-aware-coordination/task-5-brief.md",
        "byte_count": 62828,
        "sha256": "8d2f27d2fb9e6901d7bfed90407a25f8c714d23fe9d2f511a469494e272054ee",
    },
    {
        "role": "scientific_review",
        "transport_candidate_path": "D:/Data/25_ACE/AG/.superpowers/sdd/2026-08-20-obligation-aware-coordination/task-5-brief-review.md",
        "byte_count": 90780,
        "sha256": "8d98a17ee57b1a254d4f651d74b44b696ec022e3822daea1b8a3f25036060cc8",
    },
)
LEGACY_TARGET = "e774381bbde93a9540821a6375ccbee55ec724d801e91b10efab2bcdc91083b6"

WRAPPER_SCHEMAS = {
    "artifact_pin": "ace.iclr2027.external_vnext_artifact_pin.vnext",
    "signature_envelope": "ace.iclr2027.external_canonical_signature_envelope.vnext",
}
LOCATOR_VOCABULARY = {
    "future_path_b_positive_intake_locator": "absent_until_separately_approved",
    "task5_scientific_parent_custody_ref": "required_before_scientific_authorship",
    "task7_process_spec_custody_ref": "required_before_step_1",
}
REVIEWER_ENVELOPE_DIMENSIONS = (
    "signing_key_id",
    "signing_public_key_member_identity",
    "signing_public_key_sha256",
    "detached_signature_member_identity",
    "detached_signature_sha256",
    "external_verifier_package_identity",
    "external_verifier_package_version",
    "external_verifier_executable_sha256",
    "rotation_provenance_member_identity",
    "rotation_provenance_sha256",
)
REVIEWER_PIN_DIMENSIONS = (
    "external_verifier_executable_member_identity",
    "external_platform_signature_member_identity",
    "external_platform_signature_sha256",
)
ROLE_SEPARATION_CONTRACT = {
    "approval_digest_fields": [
        "responsible_owner_approval_sha256",
        "external_scientist_approval_sha256",
        "custodian_search_rows[*].approval_file_sha256",
    ],
    "approval_member_identity_fields": [
        "responsible_owner_approval_member_identity",
        "external_scientist_approval_member_identity",
        "custodian_search_rows[*].approval_member_identity",
    ],
    "nonreviewer_producer_identities": [
        "responsible_migration_owner_identity",
        "external_scientist_identity",
    ],
    "producer_roles": [
        "declaration_producer",
        "thesis_producer",
        "snapshot_producer",
        "migration_receipt_producer",
        "responsible_migration_owner",
    ],
    "reviewer_envelope_dimensions": list(REVIEWER_ENVELOPE_DIMENSIONS),
    "reviewer_pin_dimensions": list(REVIEWER_PIN_DIMENSIONS),
    "reviewer_record_dimensions": ["reviewer_identity"],
}
CONTRACT_KEYS = {
    "canonical_record_count",
    "dag_predecessors",
    "legacy_search_target_sha256",
    "locator_vocabulary",
    "non_authoritative",
    "process_specification",
    "receipt_joins_predecessor_roles",
    "role_domains",
    "role_schemas",
    "role_separation",
    "schema_version",
    "task5_scientific_contract_mirror",
    "task5_transport_candidates",
    "wrapper_schemas",
}
EXPECTED_DIGEST_COUNTS = Counter(
    {
        TASK7_PROCESS_SPEC["sha256"]: 2,
        TASK5_INPUTS[0]["sha256"]: 2,
        TASK5_INPUTS[1]["sha256"]: 2,
        TASK5_INPUTS[2]["sha256"]: 2,
        LEGACY_TARGET: 1,
    }
)

ROLE_SCHEMAS = {
    "legacy_search_impossibility_declaration": "ace.iclr2027.legacy_search_impossibility_declaration.vnext",
    "one_thesis_contract": "ace.iclr2027.one_thesis_contract.vnext",
    "new_upstream_scientific_snapshot": "ace.iclr2027.new_upstream_scientific_snapshot.vnext",
    "independent_science_migration_review": "ace.iclr2027.independent_migration_review.vnext",
    "independent_provenance_migration_review": "ace.iclr2027.independent_migration_review.vnext",
    "independent_security_migration_review": "ace.iclr2027.independent_migration_review.vnext",
    "provenance_migration_receipt": "ace.iclr2027.provenance_migration_receipt.vnext",
}
ROLE_DOMAINS = {
    "legacy_search_impossibility_declaration": "ACE-ICLR2027-LEGACY-SEARCH-IMPOSSIBILITY-VNEXT\x00",
    "one_thesis_contract": "ACE-ICLR2027-ONE-THESIS-CONTRACT-VNEXT\x00",
    "new_upstream_scientific_snapshot": "ACE-ICLR2027-NEW-UPSTREAM-SCIENTIFIC-SNAPSHOT-VNEXT\x00",
    "independent_science_migration_review": "ACE-ICLR2027-INDEPENDENT-SCIENCE-MIGRATION-REVIEW-VNEXT\x00",
    "independent_provenance_migration_review": "ACE-ICLR2027-INDEPENDENT-PROVENANCE-MIGRATION-REVIEW-VNEXT\x00",
    "independent_security_migration_review": "ACE-ICLR2027-INDEPENDENT-SECURITY-MIGRATION-REVIEW-VNEXT\x00",
    "provenance_migration_receipt": "ACE-ICLR2027-PROVENANCE-MIGRATION-RECEIPT-VNEXT\x00",
}
DAG_PREDECESSORS = {
    "legacy_search_impossibility_declaration": (),
    "one_thesis_contract": ("legacy_search_impossibility_declaration",),
    "new_upstream_scientific_snapshot": ("one_thesis_contract",),
    "independent_science_migration_review": ("new_upstream_scientific_snapshot",),
    "independent_provenance_migration_review": ("new_upstream_scientific_snapshot",),
    "independent_security_migration_review": ("new_upstream_scientific_snapshot",),
    "provenance_migration_receipt": (
        "independent_provenance_migration_review",
        "independent_science_migration_review",
        "independent_security_migration_review",
    ),
}
PREDECESSOR_ARTIFACT_ROLES = (
    "legacy_search_impossibility_declaration",
    "one_thesis_contract",
    "new_upstream_scientific_snapshot",
    "independent_science_migration_review",
    "independent_provenance_migration_review",
    "independent_security_migration_review",
)

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
ONE_THESIS_SCALARS = (
    ("thesis_id", "residual_obligation_x_actually_executed_complete_bundle"),
    ("treatment_definition", "residual_obligation_status_x_actually_executed_complete_bundle"),
    ("architecture_domain_role", "flagship_primary_domain"),
    ("jci_domain_role", "independent_e2_e3_replication_no_pooling"),
    ("architecture_ontology_clause", "architecture_site_cluster_flagship_residual_obligation_x_actually_executed_complete_bundle"),
    ("jci_ontology_clause", "jci_project_cluster_independent_e2_e3_resource_obligation_replication_no_pooling"),
    ("cross_domain_pooling", "forbidden"),
    ("cats_role", "negative_motivation_and_baseline_only"),
    ("e1_role", "predictive_noncausal_nonprimary_support"),
    ("e2_role", "randomized_executed_complete_bundle_primary_mechanism"),
    ("e2_primary_endpoint", "blind_terminal_obligation_closure_quality_present_high_minus_low_minus_absent_high_minus_low"),
    ("e3_role", "equal_information_policy_consequence_conditional_on_e2"),
    ("e3_primary_comparator", "full_parity_raw_router"),
    ("retrospective_oracle_role", "post_outcome_descriptive_upper_bound_separate_not_deployable"),
    ("e4_role", "fresh_downstream_deployable_frontier_after_e1_e2_e3"),
)


def _literal_assignments(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, object] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            result[target.id] = ast.literal_eval(node.value)
        except (TypeError, ValueError):
            continue
    return result


def _class_annotated_fields(path: Path) -> dict[str, tuple[str, ...]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        result[node.name] = tuple(
            item.target.id
            for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        )
    return result


class PathBExternalHandoffTests(unittest.TestCase):
    def _read(self) -> tuple[bytes, str]:
        self.assertTrue(HANDOFF.is_file(), f"missing handoff: {HANDOFF}")
        raw = HANDOFF.read_bytes()
        return raw, raw.decode("utf-8")

    @staticmethod
    def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def _contract(self, text: str) -> dict[str, object]:
        self.assertEqual(text.count(BEGIN_CONTRACT), 1)
        self.assertEqual(text.count(END_CONTRACT), 1)
        body = text.split(BEGIN_CONTRACT, 1)[1].split(END_CONTRACT, 1)[0].strip()
        self.assertTrue(body.startswith("```json\n"))
        self.assertTrue(body.endswith("\n```"))
        return json.loads(
            body[len("```json\n") : -len("\n```")],
            object_pairs_hook=self._reject_duplicate_keys,
        )

    def _assert_closed_contract(self, contract: dict[str, object]) -> None:
        self.assertEqual(set(contract), CONTRACT_KEYS)
        self.assertEqual(
            set(contract["process_specification"]),
            {"byte_count", "external_custody_required", "role", "sha256", "transport_candidate_path"},
        )
        self.assertEqual(set(contract["task5_scientific_contract_mirror"]), {
            "endpoint_hierarchy", "kill_chain", "policy_ids", "scalars"
        })
        self.assertEqual(contract["wrapper_schemas"], WRAPPER_SCHEMAS)
        self.assertEqual(contract["role_separation"], ROLE_SEPARATION_CONTRACT)
        for row in contract["task5_transport_candidates"]:
            self.assertEqual(set(row), {"byte_count", "role", "sha256", "transport_candidate_path"})

    def test_handoff_is_ascii_lf_only_and_non_authoritative(self) -> None:
        raw, text = self._read()
        self.assertTrue(text.isascii())
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"\n"))
        for banner in (
            "INTAKE_ONLY",
            "MINTS_NO_AUTHORITY",
            "NOT_TASK6_VNEXT",
            "NO_SIMULATION_OR_PAID_AUTHORIZATION",
        ):
            self.assertEqual(text.count(banner), 1, banner)
        self.assertIn("This workspace cannot sign, approve, authenticate, or mint PASS", text)
        self.assertIn("status remains `NO-GO`/`NEEDS_CONTEXT`", text)

    def test_machine_contract_binds_process_spec_task5_bytes_and_legacy_target(self) -> None:
        _, text = self._read()
        contract = self._contract(text)
        self.assertEqual(contract["process_specification"], TASK7_PROCESS_SPEC)
        self.assertEqual(tuple(contract["task5_transport_candidates"]), TASK5_INPUTS)
        self.assertEqual(contract["legacy_search_target_sha256"], LEGACY_TARGET)
        self.assertEqual(text.count(LEGACY_TARGET), 1)
        self.assertIn("transport candidates only", text)
        self.assertIn("STOP before scientific authorship", text)
        self.assertIn("sender-side transport hint, never a locator or trust root", text)
        self.assertIn("STOP before Step 1", text)
        for item in (TASK7_PROCESS_SPEC, *TASK5_INPUTS):
            raw = Path(item["transport_candidate_path"]).read_bytes()
            self.assertEqual(len(raw), item["byte_count"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])

    def test_machine_contract_has_closed_keys_rejects_duplicates_and_whitelists_digests(self) -> None:
        _, text = self._read()
        contract = self._contract(text)
        self._assert_closed_contract(contract)
        self.assertEqual(contract["schema_version"], "ace.iclr2027.path_b_external_handoff_contract.v1")
        self.assertIs(contract["non_authoritative"], True)
        self.assertEqual(contract["locator_vocabulary"], LOCATOR_VOCABULARY)
        duplicated = text.replace(
            '  "canonical_record_count": 21,',
            '  "canonical_record_count": 20,\n  "canonical_record_count": 21,',
            1,
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self._contract(duplicated)
        extra = dict(contract)
        extra["unexpected"] = True
        with self.assertRaises(AssertionError):
            self._assert_closed_contract(extra)
        observed = Counter(re.findall(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", text))
        self.assertEqual(observed, EXPECTED_DIGEST_COUNTS)

    def test_machine_contract_exactly_matches_test_owned_and_production_role_maps(self) -> None:
        _, text = self._read()
        contract = self._contract(text)
        self.assertEqual(contract["role_schemas"], ROLE_SCHEMAS)
        self.assertEqual(contract["role_domains"], ROLE_DOMAINS)
        self.assertEqual(
            {key: tuple(value) for key, value in contract["dag_predecessors"].items()},
            DAG_PREDECESSORS,
        )
        self.assertEqual(len(contract["role_schemas"]), 7)
        self.assertEqual(len(set(contract["role_schemas"])), 7)
        production = _literal_assignments(PRODUCTION)
        self.assertEqual(production["_ROLE_SCHEMAS"], ROLE_SCHEMAS)
        self.assertEqual(production["_ROLE_DOMAINS"], ROLE_DOMAINS)
        self.assertEqual(production["envelope_dimensions"], REVIEWER_ENVELOPE_DIMENSIONS)
        self.assertEqual(production["pin_dimensions"], REVIEWER_PIN_DIMENSIONS)
        fields = _class_annotated_fields(PRODUCTION)
        self.assertIn("responsible_owner_approval_member_identity", fields["_LegacySearchImpossibilityDeclarationVNext"])
        self.assertIn("responsible_owner_approval_sha256", fields["_LegacySearchImpossibilityDeclarationVNext"])
        self.assertIn("external_scientist_approval_member_identity", fields["_OneThesisContractVNext"])
        self.assertIn("external_scientist_approval_sha256", fields["_OneThesisContractVNext"])
        self.assertIn("approval_member_identity", fields["_CustodianSearchRowVNext"])
        self.assertIn("approval_file_sha256", fields["_CustodianSearchRowVNext"])
        self.assertIn("reviewer_identity", fields["_IndependentMigrationReviewVNext"])
        all_fields = {name for values in fields.values() for name in values}
        self.assertNotIn("custodian_approval_member_identity", all_fields)
        self.assertNotIn("custodian_approval_file_sha256", all_fields)

    def test_domain_prefixes_end_in_one_nul_and_json_uses_unicode_escape(self) -> None:
        _, text = self._read()
        contract = self._contract(text)
        for domain in contract["role_domains"].values():
            self.assertTrue(domain.endswith("\x00"))
            self.assertNotIn("\x00", domain[:-1])
        contract_raw = text.split(BEGIN_CONTRACT, 1)[1].split(END_CONTRACT, 1)[0]
        self.assertEqual(contract_raw.count("\\u0000"), 7)
        self.assertIn("exactly one terminal byte `0x00`", text)
        self.assertIn("canonical JSON serializes that code point as `\\u0000`", text)

    def test_scientific_contract_mirror_is_exact_and_matches_frozen_production(self) -> None:
        _, text = self._read()
        mirror = self._contract(text)["task5_scientific_contract_mirror"]
        self.assertEqual(tuple(tuple(item) for item in mirror["scalars"]), ONE_THESIS_SCALARS)
        self.assertEqual(tuple(mirror["policy_ids"]), POLICY_IDS)
        self.assertEqual(tuple(mirror["endpoint_hierarchy"]), ENDPOINT_HIERARCHY)
        self.assertEqual(tuple(mirror["kill_chain"]), KILL_CHAIN)
        self.assertEqual(len(set(mirror["policy_ids"])), 22)
        self.assertEqual(len(mirror["endpoint_hierarchy"]), 4)
        self.assertEqual(len(mirror["kill_chain"]), 11)
        production = _literal_assignments(PRODUCTION)
        self.assertEqual(production["_POLICY_IDS"], POLICY_IDS)
        self.assertEqual(production["_ENDPOINT_HIERARCHY"], ENDPOINT_HIERARCHY)
        self.assertEqual(production["_KILL_CHAIN"], KILL_CHAIN)
        self.assertEqual(production["_FROZEN_ONE_THESIS_SCALARS"], ONE_THESIS_SCALARS)
        self.assertIn("mirror is transport guidance, not scientific authority", text)

    def test_receipt_joins_only_six_predecessor_triples_without_self_cycle(self) -> None:
        _, text = self._read()
        contract = self._contract(text)
        self.assertEqual(tuple(contract["receipt_joins_predecessor_roles"]), PREDECESSOR_ARTIFACT_ROLES)
        self.assertNotIn("provenance_migration_receipt", contract["receipt_joins_predecessor_roles"])
        self.assertEqual(contract["canonical_record_count"], 21)
        self.assertIn("six predecessor artifacts", text)
        self.assertIn("complete the seventh triple", text)
        self.assertIn("contains no self-file, self-envelope, or self-pin join", text)
        self.assertNotIn("all seven artifacts, their seven envelopes, and their seven pins", text)
        self.assertIn("byte-sorted three review envelopes", text)
        self.assertIn("byte-sorted three review pins", text)

    def test_external_action_order_defers_locator_until_locator_contract_exists(self) -> None:
        _, text = self._read()
        required_steps = (
            "1. External owner selects explicit Path B non-continuity migration",
            "2. Custodians complete and approve the exhaustive legacy search",
            "3. External scientist authors and approves the one-thesis contract",
            "4. External producer closes and signs the new upstream snapshot",
            "5. Three independent reviewers separately review and sign",
            "6. Migration authority signs the receipt; its external pin is independently approved",
            "7. Retain the completed package under immutable external custody",
            "8. Separately design, approve, and freeze the external-rooted locator",
            "9. Only then commission a separate Task 6 vNext authority",
        )
        for step in required_steps:
            self.assertIn(step, text)
        positions = [text.index(step) for step in required_steps]
        self.assertEqual(positions, sorted(positions))

    def test_role_separation_canonical_bytes_and_nonclaims_are_complete(self) -> None:
        _, text = self._read()
        for phrase in (
            "artifact -> signature envelope -> separately approved external pin",
            "producer and migration-owner keys, public keys, verifier package identities and versions, executables, platform signatures, signature members, and rotation chains must not overlap any reviewer dimension",
            "external-verifier executable member identities and hashes",
            "responsible-owner, external-scientist, and every custodian approval member identity and SHA-256",
            "external scientist is an artifact producer and cannot be a migration reviewer",
            "producer, migration-owner, and reviewer key/package identity overlaps are forbidden across all such roles",
            "global reviewer-authority union is reviewer record + envelope + pin dimensions",
            "separately approved repo-external package member",
            "cannot be supplied or overridden by any artifact, envelope, review, receipt, caller, or workspace",
            "creates no pin-owner identity",
            "globally pairwise distinct",
            "UTF-8 without BOM",
            "object keys byte-sorted",
            "compact separators",
            "exactly one final LF",
            "No source or data access",
            "No zero-call simulation",
            "No paid execution",
            "No empirical or submission claim",
            "No workspace-generated key, signature, approval, or trust root",
            "does not itself prove sample sufficiency, source correctness, model readiness",
            "simulation validity, feasibility, cost, safety, generalization, empirical",
            "effect, paper acceptance, or submission readiness",
        ):
            self.assertIn(phrase, text)
        for locator_term in LOCATOR_VOCABULARY:
            self.assertIn(f"`{locator_term}`", text)

    def test_safe_status_commands_and_current_blockers_remain_visible(self) -> None:
        _, text = self._read()
        for command in (
            "python -B validate_iclr2027_external_authority_acquisition.py --current-status",
            "python -B validate_iclr2027_external_authority_acquisition.py --list-negative-fixtures",
            "python -B validate_iclr2027_precall_design_lock.py --current-fixture",
        ):
            self.assertIn(command, text)
        for blocker in (
            "actual_architecture_jci_rosters_missing",
            "external_migration_receipt_missing",
            "external_reviews_missing",
            "external_signatures_missing",
            "external_snapshot_missing",
            "legacy_search_declaration_missing",
            "task6_vnext_authority_missing",
            "simulation_freeze_missing",
            "paid_run_authorization_missing",
        ):
            self.assertIn(f"`{blocker}`", text)


if __name__ == "__main__":
    unittest.main()
