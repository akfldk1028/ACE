# Task 6 review package

## Scope

Review the Task 6 implementation against:

- `task-6-brief.md`
- `task-6-report.md`
- `docs/superpowers/specs/2026-08-31-iclr2027-architecture-target-roster-v2-design.md`
- `docs/superpowers/plans/2026-08-31-iclr2027-architecture-target-roster-v2.md`

Review only these implementation surfaces:

- `iclr2027/run_manifest.py`
- `run_exp08_architecture.py`
- `tests/test_iclr2027_architecture_target_roster.py`
- regression-only `tests/test_iclr2027_run_manifest.py`
- regression-only `tests/test_iclr2027_dynamic_protocol.py`

Do not edit files, run a real/non-dry experiment, use the network, inspect
credentials, inspect held-out/test/OOD data, or create a checkpoint outside a
temporary directory.

## Required independent checks

1. No-sidecar execution remains exact schema v2 and exact legacy manifest
   identity/bytes. V2 must reject every v3-only key.
2. Sidecars are both-or-neither and allowed only for frozen private `dev`.
3. Both public roster and canonical receipt are verified, their projection
   commitment is bound to the frozen repository projection, and all failure
   paths occur before `checkpoint_dir.mkdir()`.
4. V3 adds exactly `target_roster_sha256`,
   `target_roster_receipt_sha256`, and `combined_dev_target_count=64`; it must
   not relabel `case_count=30` as 64.
5. Planned-to-executed validation preserves the complete v3 identity.
6. V2/v3 mixing and independent drift of each v3 identity field require a
   fresh checkpoint.
7. The dry-only witness calls `ExperimentRunner.run_single` exactly zero
   times. Do not execute a real model path.
8. Tests independently derive expected values rather than importing the same
   production constants or parser logic under test.
9. Recompute final raw and normalized-AST pins and compare with the report.
10. Run the exact 35-test Task-6 command and the specified Ruff checks if safe.

## Claimed implementation pins

- `iclr2027/run_manifest.py`: 13,429 bytes,
  `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8`
- `run_exp08_architecture.py`: 26,319 bytes,
  `91b3a7e10e25372a29e83c1c5e8d1067534c293f9458999dcb2a5aa4c5fde0f6`
- `tests/test_iclr2027_architecture_target_roster.py`: 66,447 bytes,
  `3038b3e79c77de0df61a841ff1762922b97965878abf3b403beb2b45179473ab`

## Output

Write no file. Return findings ranked Critical/Important/Minor with exact file
and line references. If there are no findings, state PASS and list the fresh
commands/results and recomputed pins. Treat evidence drift, optional-field
ambiguity, false materialization of 64 cases, or any possible non-dry call as
Important or Critical as appropriate.
