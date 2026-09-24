### Task 2: Private source, locator, geometry, and blind-overlap closure

**Files:**
- Modify: `iclr2027/architecture_target_roster.py`
- Modify: `tests/test_iclr2027_architecture_target_roster.py`

**Interfaces:**
- Consumes: Task-1 canonical hashing and exact-record conventions.
- Produces: `SourceCaptureV1.from_dict()`, `SiteLocatorV1.from_dict()`, `TargetSpecV1.from_dict()`, `BlindOverlapCheckV1.from_dict()`, `GeometryReceiptV1.from_dict()`.
- Produces: `verify_source_capture_set(rows, raw_bytes_by_source_id)`, `verify_site_locator_set(rows)`, `verify_target_spec_set(rows, roster)`, `verify_geometry_receipt_set(rows)`, `verify_blind_overlap_check(row, *, locator_set_sha256, protected_roster_commitment)` and keyword-only `verify_admission_inputs(...) -> AdmissionBindingV1`.

Exact private records are:

```python
SOURCE_CAPTURE_KEYS = {
    "schema_version", "source_id", "publisher", "canonical_uri",
    "retrieved_at", "effective_at", "media_type", "byte_length", "sha256",
    "etag", "last_modified", "license", "redistribution_status",
}
SITE_LOCATOR_KEYS = {
    "schema_version", "internal_site_id", "pnu", "split", "area_bin",
    "parcel_geometry_sha256", "project_cluster_id", "source_capture_ids",
}
TARGET_SPEC_KEYS = {
    "schema_version", "target_ref", "normalized_subject_identity",
    "evidence_family_sources", "geometry_receipt_sha256", "target_spec_sha256",
}
GEOMETRY_RECEIPT_KEYS = {
    "schema_version", "target_ref", "input_geometry_sha256",
    "materializer_code_sha256", "output_geometry_sha256",
    "compile_log_sha256", "hard_pass", "receipt_sha256",
}
BLIND_KEYS = {
    "schema_version", "locator_set_sha256", "protected_roster_commitment",
    "overlap_found", "checked_site_count", "audit_sha256", "record_sha256",
}
```

`AdmissionBindingV1` contains only the six canonical set/record hashes:
`target_roster_sha256`, `locator_set_sha256`, `source_capture_set_sha256`,
`target_spec_set_sha256`, `geometry_receipt_set_sha256`, and
`blind_overlap_check_sha256`.

- [ ] **Step 1: Add failing eligibility and blind-check tests**

```python
def test_every_target_has_all_five_bound_families(self) -> None:
    inputs = make_admission_inputs()
    del inputs["target_specs"][0]["evidence_family_sources"]["parking"]
    with self.assertRaisesRegex(TargetRosterError, "target_source_coverage_incomplete"):
        verify_admission_inputs(**inputs)

def test_blind_check_binds_exact_locator_and_protected_roster_commitments(self) -> None:
    inputs = make_admission_inputs()
    inputs["blind_check"]["locator_set_sha256"] = "0" * 64
    with self.assertRaisesRegex(TargetRosterError, "blinded_membership_check"):
        verify_admission_inputs(**inputs)

def test_project_cluster_and_parcel_overlap_are_rejected(self) -> None:
    inputs = make_admission_inputs()
    inputs["locators"][1]["project_cluster_id"] = inputs["locators"][0]["project_cluster_id"]
    with self.assertRaisesRegex(TargetRosterError, "site_or_project_cluster_overlap"):
        verify_admission_inputs(**inputs)
```

- [ ] **Step 2: Run RED and confirm the missing validators**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v`

- [ ] **Step 3: Implement closed sets and stable blocker codes**

`verify_admission_inputs()` must recompute file length/hash from captured bytes, require `redistribution_status` and `license` to be explicit, require nonempty geometry compile receipts for every target, reject duplicate PNU/parcel hash/project cluster, and validate a blind record shaped exactly as:

```python
BLIND_KEYS = {
    "schema_version", "locator_set_sha256", "protected_roster_commitment",
    "overlap_found", "checked_site_count", "audit_sha256", "record_sha256",
}
```

The checker output must have `overlap_found is False`, `checked_site_count == 3`, and hashes bound to the current locator set and a nonempty protected-roster commitment. It must not expose protected rows.

`verify_admission_inputs()` has the exact keyword-only inputs `roster`,
`target_specs`, `locators`, `source_captures`, `raw_bytes_by_source_id`,
`geometry_receipts`, `blind_check`, and `protected_roster_commitment`. It
requires one target spec and one hard-pass geometry receipt per public target,
matches public/private target-spec hashes, requires unique normalized subject
identities, proves every referenced source ID exists, and returns the six-hash
`AdmissionBindingV1` without retaining raw bytes, PNUs, URIs, or protected
roster content.

- [ ] **Step 4: Run the admission tests and both Task-1/2 classes**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterSchemaTests tests.test_iclr2027_architecture_target_roster.TargetRosterAdmissionTests -v`

Expected: exit 0.

- [ ] **Step 5: Record pins and blocker census; do not claim any candidate admitted yet**

