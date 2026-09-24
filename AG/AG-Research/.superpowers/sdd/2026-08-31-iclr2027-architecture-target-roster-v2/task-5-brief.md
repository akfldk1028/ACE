### Task 5: Pre-call inventory verification that cannot authorize execution

**Files:**
- Modify: `iclr2027/precall_design_lock.py`
- Modify: `tests/test_iclr2027_architecture_target_roster.py`
- Test: `tests/test_iclr2027_precall_design_lock.py`

**Interfaces:**
- Produces: `VerifiedArchitectureInventoryV2.from_dict()` and `verify_architecture_inventory_receipt(roster_path: Path, receipt_path: Path, *, projection_identity_commitment: str) -> VerifiedArchitectureInventoryV2`.
- Preserves: authenticated authority functions continue raising `NeedsContextError` exactly.

The view schema is `ace.iclr2027.verified_architecture_inventory.v2`. Its
`target_roster_sha256` is the verified receipt's roster self-hash and its
`freeze_receipt_sha256` is the verified receipt's canonical `receipt_sha256`
(not a second path read). `view_sha256` is the canonical self-hash with only
that field omitted. Parsing requires exact fields/types, site count 8, target
count 64, and lowercase projection/hash bindings.

- [ ] **Step 1: Write RED tests for receipt-derived counts and authority preservation**

```python
def test_precall_counts_are_derived_from_receipt(self) -> None:
    view = verify_architecture_inventory_receipt(roster, receipt, projection_identity_commitment=IDENTITY)
    self.assertEqual((view.site_count, view.target_unit_count), (8, 64))

def test_roster_does_not_upgrade_authenticated_authority(self) -> None:
    with self.assertRaisesRegex(NeedsContextError, "authenticated launcher capability is absent"):
        require_authenticated_pre_call_authority()
```

- [ ] **Step 2: Run RED and existing pre-call tests**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterPreCallTests tests.test_iclr2027_precall_design_lock -v`

- [ ] **Step 3: Add the immutable verification view**

The view contains only `schema_version`, `site_count=8`, `target_unit_count=64`, `target_roster_sha256`, `freeze_receipt_sha256`, `projection_identity_commitment`, and `view_sha256`. It is an inventory fact, not an authority receipt, candidate selection, gate result, or official eligibility flag.

- [ ] **Step 4: Run GREEN and re-run exact synthetic/authenticated no-go assertions**

Use the Step-2 command. Expected: all pass.

- [ ] **Step 5: Record normalized AST before/after and prove only the new inventory path changed**

