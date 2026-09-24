# Task 5 report — verified pre-call inventory view

## Scope and result

Added `VerifiedArchitectureInventoryV2` and
`verify_architecture_inventory_receipt()` to
`iclr2027/precall_design_lock.py`, plus receipt-derived inventory and authority
boundary coverage in `tests/test_iclr2027_architecture_target_roster.py`.

The view is an immutable, self-hashing inventory fact with exactly these
serialized fields:

`schema_version`, `site_count`, `target_unit_count`, `target_roster_sha256`,
`freeze_receipt_sha256`, `projection_identity_commitment`, and `view_sha256`.

It requires the exact v2 schema, native integer counts of 8 and 64, and
lowercase SHA-256 values for each binding. `view_sha256` is computed from the
canonical object with only `view_sha256` omitted.

The receipt adapter delegates its only path access to the existing
`verify_frozen_target_roster()` public-sidecar verifier. It derives
`target_roster_sha256` from the verified receipt binding and
`freeze_receipt_sha256` from that same verified receipt's canonical
`receipt_sha256`; it performs no second receipt-path read. It exposes no
candidate, gate, eligibility, status, or execution-authority field.

## RED / GREEN

- RED command:
  `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterDatasetIntegrationTests tests.test_iclr2027_precall_design_lock -v`
  failed only at `test_precall_counts_are_derived_from_receipt`: the requested
  verifier was absent. The authenticated no-upgrade assertion and the 61
  existing checks passed.
- GREEN command: the same command passed all 62 checks. It verifies the
  receipt-derived `(site_count, target_unit_count) == (8, 64)`, the exact view
  field schema and `from_dict()` round-trip, and the required authenticated
  `NeedsContextError` text.
- Full relevant regression command:
  `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_precall_design_lock`
  passed all 90 tests.
- Ruff:
  `C:\Python313\python.exe -E -B -m ruff check iclr2027/precall_design_lock.py tests/test_iclr2027_architecture_target_roster.py`
  passed (`All checks passed!`).

## Authority preservation

- `validate_authenticated_pre_call_design_lock()` normalized AST: unchanged.
- `require_authenticated_pre_call_authority()` normalized AST: unchanged; it
  still raises `NeedsContextError("NEEDS_CONTEXT: authenticated launcher capability is absent")`.
- `__all__`, `_CURRENT_REASONS`, `_CURRENT_FACT_SHA256`, `_CURRENT_LOCK_SHA256`,
  and `_CURRENT_GATE_AUTHORITY_SHA256S` normalized AST assignments: unchanged.
- The synthetic fixture closure and existing no-go behavior were not edited;
  the complete pre-call regression module passed.

## Normalized AST and raw pins

Baseline bytes below are reconstructed solely by deleting the exact Task 5
imports/class/function and the two Task 5 test methods from the final bytes.
Normalized AST is `sha256(ast.dump(tree, include_attributes=False))`.

| File | Raw before | Raw after | AST before | AST after |
| --- | --- | --- | --- | --- |
| `iclr2027/precall_design_lock.py` | `7d850554905062d7abc4bb81d899aebca1f0218cf1b3bc8bc11d65126f843b8b` | `0e8c761c1f13a97d02d564e0ee16a2fb8bb213b6b773ac638d8bed66cb8e6a6e` | `c364d0cb952fb12088a03b51a7314ad937411c422cb0ec12dad98a6b1b14093e` | `b8fa55866f1bd9683c7b05dd7c86aeccae870f1d12ddc7e305594aa566bc1762` |
| `tests/test_iclr2027_architecture_target_roster.py` | `8d609ea6995db88fab4d94917a6506cb502523f9dfddc372c7a75176463adc45` | `3140fa21bf548e5fc7cbbd6ddae3745b9536aeb182b0f0ff7e01560442212b33` | `32e0670e03ba6398e6e9c5d51d38bf53ac0e19a2971624b7ef0c7e5ec4ed54b5` | `5cff1109283d210c2484432a22c411d97115827d1e18f9e84fb746136c11ea89` |

The only added top-level production nodes are
`VerifiedArchitectureInventoryV2` and
`verify_architecture_inventory_receipt`; no existing top-level function or
class AST changed. The test change is limited to two new methods and their
imports.

## Concerns

None outstanding. The forwarding annotations use `typing.Any`, preserving the
frozen prohibition on `pathlib` imports and `Path` AST names; runtime path
handling remains wholly in the already verified public-sidecar verifier.

## Round 1/5 review repair

The forwarding annotations now use runtime-valid `typing.Any`; no `Path` or
`pathlib` name/import was added. The existing public-sidecar verifier remains
the sole owner of path validation.

### RED

After adding the focused type-hint and independent binding tests, this command:

`C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterDatasetIntegrationTests tests.test_iclr2027_precall_design_lock -v`

failed exactly at `test_precall_inventory_adapter_annotations_resolve` with
`NameError: name 'Path' is not defined` from `typing.get_type_hints()`. The
remaining 63 tests, including the independent receipt-binding/hash test and
the authenticated authority boundary, passed.

### GREEN

Replacing both forwarding annotations with `Any` made the same focused command
pass all 64 tests. The new tests prove:

- `get_type_hints()` resolves both forwarding arguments to `typing.Any` with no
  `NameError`.
- the schema is exactly `ace.iclr2027.verified_architecture_inventory.v2`;
  counts remain 8/64; and the exact seven-field closure contains no authority,
  status, eligibility, candidate, or gate fields;
- roster and freeze hashes equal the independently verified `FreezeReceiptV2`
  bindings; the projection commitment equals the caller and receipt commitment;
  and a wrong caller commitment is rejected;
- an independently assembled canonical JSON object containing exactly the six
  non-`view_sha256` fields hashes to `view.view_sha256`.

Final verification:

- `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_precall_design_lock` — 92 tests passed.
- `C:\Python313\python.exe -E -B -m ruff check iclr2027/precall_design_lock.py tests/test_iclr2027_architecture_target_roster.py` — `All checks passed!`.

### Final pins

Normalized AST is `sha256(ast.dump(tree, include_attributes=False))`.

| File | Raw SHA-256 | Normalized AST SHA-256 |
| --- | --- | --- |
| `iclr2027/precall_design_lock.py` | `9ea5ddeed9294e904f030f99b79a0162c5d96b6ce39f248fa3b4c1894579a714` | `81d93df63c762eab1d9e1cafb633749347c86af212bb124bb49cbdc449c9f1d8` |
| `tests/test_iclr2027_architecture_target_roster.py` | `4f65c3a747993e8b45391da9b3de6c52633fded4e3ae68e980f41fec96c42757` | `7fd34781e88e01b8e065ff198a181dbdab720a45815222322ca05692c8847639` |

The frozen pre-call AST guard confirms no `Path` AST name, and the existing
pre-call suite continues to prove the authenticated `NeedsContextError` and
synthetic no-go continuity are unchanged.
