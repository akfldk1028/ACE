### Task 6: Runner binding and stale-checkpoint rejection

**Files:**
- Modify: `run_exp08_architecture.py`
- Modify: `iclr2027/run_manifest.py`
- Modify: `tests/test_iclr2027_architecture_target_roster.py`
- Test: `tests/test_iclr2027_run_manifest.py`
- Test: `tests/test_iclr2027_dynamic_protocol.py`

**Interfaces:**
- Adds CLI: `--target-roster PATH` and `--target-roster-receipt PATH`.
- Adds exact v3 manifest keys: `target_roster_sha256`, `target_roster_receipt_sha256`, and `combined_dev_target_count`; legacy runs remain exact v2.
- Preserves all current model/backend/payment flags and does not launch a model during `--dry-run`.

V3 is valid only for `input_mode="frozen_private_binding"`, `split="dev"`,
and exact `combined_dev_target_count=64`. The two SHA fields equal the verified
receipt's `target_roster_sha256` and canonical `receipt_sha256`. V3 is rejected
with `--allow-unfrozen`, `split=test`, either missing sidecar argument, an
unverified/mutated sidecar, or a null/mismatched projection commitment.

`run_manifest_identity()` returns the v2 identity field closure for v2 and the
v3 closure including all three new fields for v3. Planned→executed projection
must preserve them. `_existing_compatible_manifest()` requires the existing
and proposed schema and entire schema-specific identity to match; any v2/v3
mix or roster/receipt/count drift requires a new checkpoint directory.

- [ ] **Step 1: Write RED runner tests**

```python
def test_dry_run_binds_verified_roster_without_model_call(self) -> None:
    code = runner.main([
        "--split", "dev", "--dry-run", "--checkpoint-dir", str(checkpoint),
        "--registry", str(registry), "--split-manifest", str(split_manifest),
        "--projection-identity", str(projection_identity),
        "--public-registry", str(public_registry),
        "--freeze-receipt", str(freeze_receipt),
        "--target-roster", str(roster),
        "--target-roster-receipt", str(receipt),
    ])
    self.assertEqual(code, 0)
    manifest = read_json(checkpoint / "run_manifest.json")
    self.assertEqual(manifest["combined_dev_target_count"], 64)

def test_checkpoint_resume_rejects_changed_roster_receipt(self) -> None:
    runner.main(first_dry_run_args)
    mutate_and_reseal_roster()
    with self.assertRaisesRegex(ValueError, "use a new --checkpoint-dir"):
        runner.main(first_dry_run_args)
```

Also test exact v2 no-sidecar validation/identity remains unchanged, exact v3
planned and executed validation, v3 rejection for public fixture/test split,
one-sided CLI arguments, v2 checkpoint reuse with v3 request, v3 checkpoint
reuse with v2 request, and preservation of all three fields across
planned→executed identity projection.

- [ ] **Step 2: Run RED with runner transaction tests**

Run: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol -v`

- [ ] **Step 3: Bind the verified receipt before checkpoint creation**

Parse both-or-neither arguments and verify them before `checkpoint_dir.mkdir`. When absent, emit the current exact v2 manifest byte-for-byte. When present, emit `ace.iclr2027.exp08_run_manifest.v3` with the three exact additional keys and include them in existing-manifest compatibility checks. Update `validate_run_manifest()` and `run_identity()` to accept exact v2 or exact v3 key closures without optional-field ambiguity. A dry run may write the plan/manifest but must make zero `ExperimentRunner` calls. Non-dry execution remains subject to existing authority/payment controls and is not invoked by this plan.

- [ ] **Step 4: Run GREEN and a fresh-root zero-call CLI dry run**

Use the Step-2 command, then run the CLI against reviewed fixture inputs and a fresh temporary checkpoint. Instrument `ExperimentRunner.run_single` to fail if called; expected call count is zero.

- [ ] **Step 5: Record checkpoint manifest bytes/hash and zero-call witness**

