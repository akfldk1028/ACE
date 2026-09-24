# Task 6 Fix Round 1 re-review package

Re-review the single Important finding recorded in `task-6-review.md` against
the current files and the appended Fix Round 1 section in `task-6-report.md`.

Read-only scope:

- `run_exp08_architecture.py`
- `tests/test_iclr2027_architecture_target_roster.py`
- `iclr2027/run_manifest.py` only for no-drift confirmation

Required checks:

1. Reproduce or inspect the original valid-sidecar plus manifest-invalid
   `private-model` case. It must raise and leave the fresh checkpoint path
   absent.
2. Confirm `checkpoint_dir.mkdir()` is after `validate_run_manifest()` and
   `_existing_compatible_manifest()`, and immediately before the first write.
3. Confirm existing checkpoint compatibility/resume semantics were not broken.
4. Run the focused 9-test runner class and, if safe, the exact 36-test Task-6
   command. No non-dry/model/network path.
5. Recompute raw/AST pins and check the report. Confirm `run_manifest.py` is
   unchanged.

Do not edit files, use git/network/credentials/subagents, access
held-out/test/OOD content, or run a model. Return ADDRESSED/PASS or ranked new
findings with exact file/line evidence.
