# Task 6 Fix Round 1 brief

## Finding

Independent review found one Important defect. `run_exp08_architecture.py`
creates `checkpoint_dir` before `validate_run_manifest()` and compatibility
checking. A verified sidecar paired with a manifest-invalid model value raises
but leaves an empty checkpoint directory. This violates the fail-before-write
contract.

## Allowed writes

- `run_exp08_architecture.py`
- `tests/test_iclr2027_architecture_target_roster.py`
- append a clearly labelled Fix Round 1 section to `task-6-report.md`

Do not modify `iclr2027/run_manifest.py`, other production/tests, design/plan,
candidate data, or the diagnostic. No git, network, held-out/test/OOD access,
subagent, model execution, or non-dry manual run.

## Required TDD fix

1. Add a focused RED regression using valid verified sidecars and a
   manifest-invalid `--model private-model`. Assert the exception and that the
   fresh checkpoint path does not exist.
2. Move checkpoint creation until after both `validate_run_manifest()` and
   `_existing_compatible_manifest()` complete. Preserve existing checkpoint
   compatibility behavior. Create the directory immediately before the first
   write only after all pre-write validation succeeds.
3. Prove every existing sidecar-specific pre-checkpoint failure remains clean.

## Gates

Run and stop on the first failure:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_runner_v2 -v
C:\Python313\python.exe -E -B -m ruff check iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
C:\Python313\python.exe -E -B -m ruff format --check iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
```

Recompute the three Task-6 pins and normalized AST pins. Reconfirm the exact
v2 legacy pin and a dry v3 zero-`run_single` witness. Append RED/GREEN evidence,
gate results, pins, and no-call/no-network statement to the report.
