### Task 3: Offline builder and freeze receipt v2

**Files:**
- Create: `build_iclr2027_architecture_target_roster.py`
- Modify: `iclr2027/architecture_target_roster.py`
- Modify: `tests/test_iclr2027_architecture_target_roster.py`

**Interfaces:**
- Consumes: `verify_admission_inputs()` and Task-1 record constructors.
- Produces: `LegacyBindingsV1.from_dict()`, `IndependentReviewV1.from_dict()`, and `FreezeReceiptV2.from_dict()`.
- Produces: `build_frozen_roster(input_root: Path, output_root: Path) -> FreezeReceiptV2`.
- CLI: `python -E -B build_iclr2027_architecture_target_roster.py --input-root D:\acquisition\architecture-roster-v2-input --output-root D:\acquisition\architecture-roster-v2-release-01`.

The input root contains exactly these regular files plus the source-object
directory; unexpected files, links, reparse points, and directories fail:

```text
legacy_bindings.json
target_roster.json
site_locators.json
target_specs.json
source_captures.json
geometry_receipts.json
blind_overlap_check.json
independent_review.json
source_objects/<capture-sha256>.bin
```

`LegacyBindingsV1` has exact fields `{schema_version, registry_version,
registry_core_sha256, projection_identity_commitment, split_manifest_sha256,
public_registry_sha256, public_case_set_sha256, existing_dev_site_count,
existing_dev_target_count}` with schema
`ace.iclr2027.architecture_legacy_bindings.v1` and exact counts `5/30`.

`IndependentReviewV1` has exact fields `{schema_version,
reviewed_target_roster_sha256, reviewed_admission_binding_sha256, status,
reviewer_identity_commitment, review_sha256}` with schema
`ace.iclr2027.architecture_independent_review.v1`, status `approved`, current
roster/admission hashes, lowercase reviewer commitment, and canonical
self-hash.

`FreezeReceiptV2` has exact fields `{schema_version, registry_version,
registry_core_sha256, projection_identity_commitment, split_manifest_sha256,
public_registry_sha256, public_case_set_sha256, site_locator_set_sha256,
public_site_set_sha256, public_target_set_sha256, source_capture_set_sha256,
target_spec_set_sha256, geometry_receipt_set_sha256, target_roster_sha256,
new_site_count, new_target_count, allocation, combined_dev_site_count,
combined_dev_target_count, blind_overlap_check_sha256,
independent_review_sha256, receipt_sha256}` and schema
`ace.iclr2027.architecture_freeze_receipt.v2`.

The successful release contains exactly:

```text
public/architecture_target_roster.json
public/architecture_freeze_receipt.v2.json
private/site_locators.json
private/target_specs.json
private/source_captures.json
private/geometry_receipts.json
private/blind_overlap_check.json
private/independent_review.json
```

- [ ] **Step 1: Write failing builder transaction tests**

```python
def test_builder_writes_only_to_fresh_output_and_emits_exact_receipt(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        input_root = write_complete_inputs(Path(tmp) / "input")
        output_root = Path(tmp) / "output"
        receipt = build_frozen_roster(input_root, output_root)
        self.assertEqual((receipt.new_site_count, receipt.new_target_count), (3, 34))
        self.assertEqual((receipt.combined_dev_site_count, receipt.combined_dev_target_count), (8, 64))
        self.assertEqual(receipt.allocation, (12, 11, 11))

def test_builder_leaves_no_partial_release_on_failure(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        input_root = write_complete_inputs(Path(tmp) / "input", corrupt_source=True)
        output_root = Path(tmp) / "output"
        with self.assertRaisesRegex(TargetRosterError, "source_capture_missing_or_changed"):
            build_frozen_roster(input_root, output_root)
        self.assertFalse(output_root.exists())
```

- [ ] **Step 2: Run RED**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterBuilderTests -v`

- [ ] **Step 3: Implement an offline, fresh-root transaction**

The builder reads only exact named JSON/byte inputs under `input_root`, verifies them before opening a sibling temporary output directory, emits canonical LF/final-LF JSON through the existing atomic writer, fsyncs/renames the complete release, and rejects a pre-existing `output_root`. It contains no HTTP, browser, subprocess, model-client, environment-secret, protected-roster discovery, or retry logic.

The v2 receipt contains the exact spec fields plus `receipt_sha256`; recompute the self-hash with only that field omitted. `independent_review_sha256` and `blind_overlap_check_sha256` are required input bindings, never self-issued by the builder.

- [ ] **Step 4: Run GREEN, CLI help, and static forbidden-capability scan**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterBuilderTests -v`

Run: `C:\Python313\python.exe -E -B build_iclr2027_architecture_target_roster.py --help`

Run: `rg -n "requests|urllib|httpx|Claude|OpenAI|subprocess|heldout|test_registry|os\.environ" build_iclr2027_architecture_target_roster.py iclr2027/architecture_target_roster.py`

Expected: tests/help exit 0; capability scan has no executable acquisition/model/protected-roster path.

- [ ] **Step 5: Record exact builder AST and raw-file hashes in the report**

