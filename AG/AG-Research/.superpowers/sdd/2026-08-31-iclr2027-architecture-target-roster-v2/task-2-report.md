# Task 2 report — private source, locator, geometry, target-spec, and blind-overlap closure

## Scope and identity

- Task identity: `2026-08-31-iclr2027-architecture-target-roster-v2 / Task 2`
- Modified implementation: `iclr2027/architecture_target_roster.py`
- Modified tests: `tests/test_iclr2027_architecture_target_roster.py`
- Commit status: none (no add, commit, stash, reset, or clean performed)
- No network/model calls, held-out/OOD reads, or protected-roster content were used.

## TDD evidence

Admission tests were added before the Task 2 implementation. The required RED command produced the expected missing-validator import failure against Task 1 code:

```text
$ C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v
test_iclr2027_architecture_target_roster (unittest.loader._FailedTest.test_iclr2027_architecture_target_roster) ... ERROR

======================================================================
ERROR: test_iclr2027_architecture_target_roster (unittest.loader._FailedTest.test_iclr2027_architecture_target_roster)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_iclr2027_architecture_target_roster
Traceback (most recent call last):
  File "C:\Python313\Lib\unittest\loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
  File "D:\Data\25_ACE\AG\AG-Research\tests\test_iclr2027_architecture_target_roster.py", line 8, in <module>
    from iclr2027.architecture_target_roster import (
    ...<4 lines>...
    )
ImportError: cannot import name 'verify_admission_inputs' from 'iclr2027.architecture_target_roster' (D:\Data\25_ACE\AG\AG-Research\iclr2027\architecture_target_roster.py)

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

This is the expected pre-implementation failure: the admission validator did not yet exist.

## GREEN verification

```text
$ C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v
test_evidence_fields_and_conditions_cannot_inflate_targets (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_evidence_fields_and_conditions_cannot_inflate_targets) ... ok
test_exact_12_11_11_roster_is_accepted (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_exact_12_11_11_roster_is_accepted) ... ok
test_exact_public_rows_accept_source_ids_and_reject_legacy_fields (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_exact_public_rows_accept_source_ids_and_reject_legacy_fields) ... ok
test_public_records_reject_protected_values_recursively (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_public_records_reject_protected_values_recursively) ... ok
test_blind_check_binds_exact_locator_and_protected_roster_commitments (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_blind_check_binds_exact_locator_and_protected_roster_commitments) ... ok
test_every_target_has_all_five_bound_families (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_every_target_has_all_five_bound_families) ... ok
test_project_cluster_and_parcel_overlap_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_project_cluster_and_parcel_overlap_are_rejected) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.027s

OK
```

```text
$ C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
All checks passed!
```

## Implemented closure

- Added exact-key immutable records and `from_dict()` parsers for source captures, site locators, target specifications, geometry receipts, and blind-overlap checks.
- Added set validators, raw-byte length/SHA-256 recomputation, exact source-reference closure, unique normalized identities, target/public-hash matching, one hard-pass receipt per public target, and duplicate PNU/parcel/project-cluster rejection.
- Added the keyword-only admission validator, returning `AdmissionBindingV1` with exactly six hash fields. It retains no raw bytes, PNUs, URIs, or protected-roster content.
- The blind check is exact-key/self-hashed; it requires no overlap, three checked sites, and equality to the current locator-set and protected-roster commitments.

## Synthetic-fixture pins

The following deterministic hashes were generated from the in-test synthetic fixture only; they are not a claim that any real candidate is admitted.

```text
target_roster_sha256=2cc7a02d062ee9f9ab0f556d52d9184e220859094aff0b89326b546cb2e9dd55
locator_set_sha256=aaf04680733be042ec519bd8a1b1e881359aed24211c0f0edf4579f52ef471dd
source_capture_set_sha256=44fdc7721e6b61ab7ce42f48b5600d9850f6edf41f9bf389a3b1aec1b158ae2b
target_spec_set_sha256=611bdfca901a602365aaa6c9904f3bc4a8c7dc64910da22492aa9f85d597a6f2
geometry_receipt_set_sha256=f53abafcb9224d0f33c8607c787741bea89b05b534ff56b2dbf52cedc658eab3
blind_overlap_check_sha256=843b3533da1ee2aa11b0b415b3be734b6bec92e3994db912e96f179a912bfcbf
```

## Blocker census

- `target_source_coverage_incomplete`: a target does not bind all five required evidence families.
- `blinded_membership_check`: malformed/self-hash-invalid blind record, wrong locator/protected-roster binding, positive overlap, or count other than three.
- `site_or_project_cluster_overlap`: duplicate internal site ID, PNU, parcel geometry SHA-256, or project cluster ID.
- Additional closure blockers are emitted for source-byte mismatch, missing source references, public/private target mismatch, receipt mismatch/closure, and duplicate normalized identities.

## Self-review and concerns

- Reviewed exact closed-key sets, canonical record/set hash binding, source-byte recomputation, and the public/private boundary. `git diff --check` returned exit 0; the two requested test classes and Ruff were rerun successfully after implementation.
- The RED result is an import-time missing-interface error rather than an assertion failure, because Task 1 did not export the required admission API. It directly identifies the specified missing validator.
- No candidate admission is asserted. The pins above belong solely to synthetic test data.

## Fix Round 1/5 — RED evidence

The regression tests were written before this fix.  The exact RED command was:

```text
$ C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v
test_blind_check_binds_exact_locator_and_protected_roster_commitments (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_blind_check_binds_exact_locator_and_protected_roster_commitments) ... ok
test_every_target_has_all_five_bound_families (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_every_target_has_all_five_bound_families) ... ok
test_exact_three_locator_and_thirty_four_target_closures_are_required (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_exact_three_locator_and_thirty_four_target_closures_are_required) ... ok
test_geometry_receipt_set_requires_hard_pass (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_geometry_receipt_set_requires_hard_pass) ... FAIL
test_identity_aliases_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_identity_aliases_are_rejected) ... FAIL (12 subtests: site, law, parking, program, geometry, evidence, condition, native, challenged, repeat, prefix, treatment)
test_locator_source_reference_and_order_are_closed (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_locator_source_reference_and_order_are_closed) ... ok
test_non_json_self_hash_fields_raise_stable_blockers (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_non_json_self_hash_fields_raise_stable_blockers) ... ERROR
test_pnu_requires_ascii_digits (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_pnu_requires_ascii_digits) ... FAIL
test_private_schema_versions_are_exact (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_private_schema_versions_are_exact) ... FAIL
test_project_cluster_and_parcel_overlap_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_project_cluster_and_parcel_overlap_are_rejected) ... ok
test_raw_byte_length_and_hash_mismatch_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_raw_byte_length_and_hash_mismatch_are_rejected) ... ok
test_train_locator_is_rejected_even_with_resealed_blind_record (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_train_locator_is_rejected_even_with_resealed_blind_record) ... FAIL
test_valid_admission_returns_only_six_non_sensitive_hashes (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_valid_admission_returns_only_six_non_sensitive_hashes) ... ok

ERROR: TargetSpecV1.from_dict(spec) raised raw TypeError: Object of type object is not JSON serializable at canonical_sha256() instead of TargetRosterError.
FAIL: geometry_receipt_hard_pass — TargetRosterError not raised.
FAIL: normalized_subject_identity — TargetRosterError not raised for each of the 12 alias witnesses.
FAIL: locator_pnu — TargetRosterError not raised for Arabic-Indic 19-digit witness.
FAIL: source_capture_schema — TargetRosterError not raised for non-exact schema literal.
FAIL: locator_split — TargetRosterError not raised after `train` locator plus resealed blind record.

----------------------------------------------------------------------
Ran 13 tests in 0.120s

FAILED (failures=16, errors=1)
```

## Fix Round 1/5 — implementation

- Site locators now require `split == "dev"` before blind-record binding is considered.
- PNUs use ASCII-only `[0-9]{19}` matching.
- Private parsers require these exact schema literals: `ace.iclr2027.architecture_source_capture.v1`, `ace.iclr2027.architecture_site_locator.v1`, `ace.iclr2027.architecture_target_spec.v1`, `ace.iclr2027.architecture_geometry_receipt.v1`, and `ace.iclr2027.architecture_blind_overlap_check.v1`.
- Normalized subject identities reject all specified evidence/condition/repeat/treatment alias categories while retaining existing uniqueness closure.
- Geometry-receipt set validation rejects any non-`True` hard-pass record directly.
- Target-spec, geometry-receipt, and blind self-hash serialization convert non-JSON `TypeError`/`ValueError` failures to their stable `TargetRosterError` blocker codes.
- Admission tests now include a valid six-hash/no-sensitive-retention binding, exact schema/split/PNU/alias witnesses, byte pins, source closure/order, exact 3/34 closure, geometry hard pass, blind binding, and malformed self-hash witnesses.

## Fix Round 1/5 — GREEN evidence

```text
$ C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v
test_evidence_fields_and_conditions_cannot_inflate_targets (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_evidence_fields_and_conditions_cannot_inflate_targets) ... ok
test_exact_12_11_11_roster_is_accepted (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_exact_12_11_11_roster_is_accepted) ... ok
test_exact_public_rows_accept_source_ids_and_reject_legacy_fields (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_exact_public_rows_accept_source_ids_and_reject_legacy_fields) ... ok
test_public_records_reject_protected_values_recursively (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_public_records_reject_protected_values_recursively) ... ok
test_blind_check_binds_exact_locator_and_protected_roster_commitments (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_blind_check_binds_exact_locator_and_protected_roster_commitments) ... ok
test_every_target_has_all_five_bound_families (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_every_target_has_all_five_bound_families) ... ok
test_exact_three_locator_and_thirty_four_target_closures_are_required (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_exact_three_locator_and_thirty_four_target_closures_are_required) ... ok
test_geometry_receipt_set_requires_hard_pass (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_geometry_receipt_set_requires_hard_pass) ... ok
test_identity_aliases_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_identity_aliases_are_rejected) ... ok
test_locator_source_reference_and_order_are_closed (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_locator_source_reference_and_order_are_closed) ... ok
test_non_json_self_hash_fields_raise_stable_blockers (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_non_json_self_hash_fields_raise_stable_blockers) ... ok
test_pnu_requires_ascii_digits (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_pnu_requires_ascii_digits) ... ok
test_private_schema_versions_are_exact (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_private_schema_versions_are_exact) ... ok
test_project_cluster_and_parcel_overlap_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_project_cluster_and_parcel_overlap_are_rejected) ... ok
test_raw_byte_length_and_hash_mismatch_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_raw_byte_length_and_hash_mismatch_are_rejected) ... ok
test_train_locator_is_rejected_even_with_resealed_blind_record (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_train_locator_is_rejected_even_with_resealed_blind_record) ... ok
test_valid_admission_returns_only_six_non_sensitive_hashes (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_valid_admission_returns_only_six_non_sensitive_hashes) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.075s

OK

$ C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
All checks passed!
```

## Fix Round 1/5 — final synthetic-fixture pins

```text
target_roster_sha256=8f755115bd47009ddd94e0a9ee81861e0c0a89a94569a5accad0b3db8640482f
locator_set_sha256=76cef062f4b801931111c800eaa73ecef27b6abaa6a366c0ac20545eba6e33ee
source_capture_set_sha256=fcb004e752b5e82f4508720c5c1be00eda9b9151859a2ac81e12690997b2ecf8
target_spec_set_sha256=0794d96e2c5c64e6b85590fd9f35a88078e68bde37ede3b1c751b040b7586bd5
geometry_receipt_set_sha256=af637c8727e1ba0b46249de3971bd8aa5e835e77d43a4435992d7ecdbde8a592
blind_overlap_check_sha256=6848636aa8c62e9f90f407bd84338b66a1567215c993cff4d035430743b677f4
```

No candidate admission is claimed; these hashes are deterministic synthetic-fixture pins.

## Fix Round 1/5 — final re-verification

After expanding the exact-schema witness to cover all five private parsers, the final fresh verification was:

```text
$ C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v
test_evidence_fields_and_conditions_cannot_inflate_targets (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_evidence_fields_and_conditions_cannot_inflate_targets) ... ok
test_exact_12_11_11_roster_is_accepted (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_exact_12_11_11_roster_is_accepted) ... ok
test_exact_public_rows_accept_source_ids_and_reject_legacy_fields (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_exact_public_rows_accept_source_ids_and_reject_legacy_fields) ... ok
test_public_records_reject_protected_values_recursively (tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests.test_public_records_reject_protected_values_recursively) ... ok
test_blind_check_binds_exact_locator_and_protected_roster_commitments (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_blind_check_binds_exact_locator_and_protected_roster_commitments) ... ok
test_every_target_has_all_five_bound_families (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_every_target_has_all_five_bound_families) ... ok
test_exact_three_locator_and_thirty_four_target_closures_are_required (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_exact_three_locator_and_thirty_four_target_closures_are_required) ... ok
test_geometry_receipt_set_requires_hard_pass (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_geometry_receipt_set_requires_hard_pass) ... ok
test_identity_aliases_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_identity_aliases_are_rejected) ... ok
test_locator_source_reference_and_order_are_closed (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_locator_source_reference_and_order_are_closed) ... ok
test_non_json_self_hash_fields_raise_stable_blockers (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_non_json_self_hash_fields_raise_stable_blockers) ... ok
test_pnu_requires_ascii_digits (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_pnu_requires_ascii_digits) ... ok
test_private_schema_versions_are_exact (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_private_schema_versions_are_exact) ... ok
test_project_cluster_and_parcel_overlap_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_project_cluster_and_parcel_overlap_are_rejected) ... ok
test_raw_byte_length_and_hash_mismatch_are_rejected (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_raw_byte_length_and_hash_mismatch_are_rejected) ... ok
test_train_locator_is_rejected_even_with_resealed_blind_record (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_train_locator_is_rejected_even_with_resealed_blind_record) ... ok
test_valid_admission_returns_only_six_non_sensitive_hashes (tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests.test_valid_admission_returns_only_six_non_sensitive_hashes) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.070s

OK

$ C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py tests/test_iclr2027_architecture_target_roster.py
All checks passed!
```
