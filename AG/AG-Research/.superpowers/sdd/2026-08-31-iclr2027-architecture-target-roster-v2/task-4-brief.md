### Task 4: Dataset sidecar integration without legacy drift

**Files:**
- Modify: `iclr2027/architecture_target_roster.py`
- Modify: `iclr2027/dataset.py`
- Modify: `tests/test_iclr2027_architecture_target_roster.py`
- Test: `tests/test_iclr2027_dataset.py`
- Test: `tests/test_iclr2027_freeze_v2.py`

**Interfaces:**
- Consumes: `verify_frozen_target_roster(roster_path, receipt_path, *, projection_identity_commitment) -> FreezeReceiptV2`.
- Produces: `verified_development_target_count(*, target_roster_path: Path | None, target_roster_receipt_path: Path | None, projection_identity_commitment: str) -> int | None`; both-or-neither is mandatory.
- Preserves: `build_native_cases`, `build_challenged_cases`, `build_cases`, `write_case_bundle`, split manifests, and legacy registry arithmetic remain unchanged. The standalone adapter does not claim that the 34 target specs have already been materialized as public cases.

`verify_frozen_target_roster()` reads each exact canonical JSON object from a
regular, non-reparse file; parses `TargetRosterV1` and `FreezeReceiptV2`; and
requires the caller's projection commitment, `receipt.target_roster_sha256 ==
roster.roster_sha256`, and recomputed canonical hashes of the public `sites`
and `targets` arrays. It returns the receipt only after all checks pass. It
does not need or read private locator/source/spec/review artifacts.

- [ ] **Step 1: Freeze pre-change legacy identities and write RED sidecar tests**

Capture byte length/SHA-256 for the existing registry, split manifest, public registry, freeze receipt, and four bundle manifests. Add tests proving no-sidecar outputs remain byte-identical and a verified sidecar reports combined development target count 64 without changing the legacy 30-case bundle count, `PROGRAM_ORDER`, or registry arithmetic.

Also mutate roster content/self-hash, receipt self-hash, projection commitment,
public-site-set hash, public-target-set hash, either missing path, symlink or
reparse input where safely constructible, and noncanonical/trailing bytes;
every mutation must fail before returning a count.

- [ ] **Step 2: Run RED plus the existing focused classes**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterDatasetIntegrationTests tests.test_iclr2027_dataset tests.test_iclr2027_freeze_v2 -v`

- [ ] **Step 3: Implement the minimal optional adapter**

Keep `registry_expected_bundle_counts()` and all case-build entry points unchanged. Add a separate helper:

```python
def verified_development_target_count(
    *, target_roster_path: Path | None, target_roster_receipt_path: Path | None,
    projection_identity_commitment: str,
) -> int | None:
    if (target_roster_path is None) != (target_roster_receipt_path is None):
        raise ValueError("target roster and receipt must be supplied together")
    if target_roster_path is None:
        return None
    receipt = verify_frozen_target_roster(
        target_roster_path,
        target_roster_receipt_path,
        projection_identity_commitment=projection_identity_commitment,
    )
    return receipt.combined_dev_target_count
```

Bind roster/receipt hashes in only the new development manifest extension. Do not reinterpret old site×program case bundles or write new public cases until separately materialized target artifacts exist.

- [ ] **Step 4: Run GREEN and compare every legacy pin**

Use the Step-2 command. Expected: all pass and every pre-change legacy hash matches.

- [ ] **Step 5: Record no-drift evidence and changed-file pins**

