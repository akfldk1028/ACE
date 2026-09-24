# Task 7 Fix Round 2 brief

## Evidence

Fix Round 1 reached 4,524 attempted / 0 accepted, 240 set invariants, and one
release invariant. Ordered gate 1 still failed on two wrong rejection surfaces.

1. A valid resealed SHA-256 happened to contain 19 consecutive decimal digits,
   so recursive protected-value scanning rejected the hash as a raw PNU before
   the intended `target_order` error.
2. The missing-target-source attack changed one occurrence of a source that is
   intentionally shared by two evidence families. The old source therefore
   remained in the spec union while it was removed from the public union,
   triggering `target_source_public_binding` before the intended missing-source
   boundary.

## Allowed writes

- `iclr2027/architecture_target_roster.py`
- `tests/test_iclr2027_architecture_target_roster.py`
- append Fix Round 2 evidence to `task-7-report.md`

Do not edit builder or any other production/test/design/plan/ledger/candidate
artifact. No git, network, model/non-dry run, credentials, protected data,
subagents, or candidate freeze.

## TDD and minimal changes

1. Preserve a focused RED proving the known target-order witness is rejected as
   `protected_identifier` only because its valid 64-hex self-hash contains a
   coincidental 19-digit substring.
2. In recursive public protected-value scanning, do not apply raw-PNU substring
   detection to a string that is exactly a valid lowercase 64-hex digest. Keep
   every key/token/URI/path check and raw PNU rejection for non-digest strings.
   The exact typed hash fields remain validated by their owning parsers.
3. Correct only the missing-target-source attack: replace the chosen source in
   every evidence-family list in that target spec and in the public source
   union, reseal, and prove it reaches `source_capture_reference_missing`.
   Do not weaken or reorder production binding checks for this fixture issue.
4. Run the two focused witnesses GREEN, then the exact mutation class.

## Ordered gates

Run and stop on the first failure:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterMutationClosureTests -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_dataset tests.test_iclr2027_freeze_v2 tests.test_iclr2027_precall_design_lock tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol tests.test_iclr2027_architecture_obligations -v
C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
C:\Python313\python.exe -E -B -m ruff format --check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
```

Final mutation output must remain explicit: 4,524 attempted, 0 accepted, 240
set invariants, one release invariant. Rehash all changed files, prove builder
and unrelated production unchanged, and append RED/GREEN/gate evidence.
