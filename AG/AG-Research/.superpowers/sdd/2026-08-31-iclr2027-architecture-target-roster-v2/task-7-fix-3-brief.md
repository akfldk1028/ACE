# Task 7 Fix Round 3 brief: mechanical formatter closure

## Root cause and authority

Task 7 gates 1–4 pass. Gate 5 is the first plan gate to check all roster
integration files with Ruff format 0.11.5. It exposed pre-existing format debt
in unchanged `dataset.py` and `precall_design_lock.py`, plus the builder and two
Task-7 changed files. This round authorizes a mechanical Ruff format only; no
semantic source edit is authorized.

## Pre-format normalized-AST pins

- builder: `31dd03836bcab2d528dfcf63410b61114016f1c0bc78d2e31c5a9a92778271f8`
- architecture roster: `1088fde21291ddac17a816d1e2d1559af7872a1761f7fd4aaffa94743db14270`
- dataset: `77f90a56256712073bbe7c90c3b3305ea2a244a9e99032f4b2c47b2abb4f868e`
- pre-call design lock:
  `81d93df63c762eab1d9e1cafb633749347c86af212bb124bb49cbdc449c9f1d8`
- focused test:
  `4b84c93e6555b9d48c3c948a120d022e7f832d38d85ade0628b948e66d37dfb5`

All five are UTF-8/LF with zero CR bytes.

## Allowed mechanical action

Run exactly once:

```text
C:\Python313\python.exe -E -B -m ruff format iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
```

`run_manifest.py` and `run_exp08_architecture.py` are already formatted and
must remain byte-identical. Do not use `apply_patch` or make any other source
edit in this round.

Immediately recompute all seven raw and normalized-AST hashes. Each of the five
listed AST hashes must match exactly; the two already formatted files must
match raw pins. Any mismatch is a blocker and no tests may be claimed.

Historical Task-4/5 raw pins for dataset/pre-call are superseded only by this
formatter event; their AST pins and behavior remain binding. Do not rewrite
historical reports. Append the exact before/after raw pins and unchanged AST
evidence to `task-7-report.md`.

## Ordered gates after AST parity

Run and stop on the first failure:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterMutationClosureTests -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_dataset tests.test_iclr2027_freeze_v2 tests.test_iclr2027_precall_design_lock tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol tests.test_iclr2027_architecture_obligations -v
C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
C:\Python313\python.exe -E -B -m ruff format --check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
```

Required final evidence remains 4,524 attempted / 0 accepted, 240 set
invariants, one release invariant, 51/51 focused, and 174/174 combined. No git,
network, model/non-dry run, credentials, protected data, candidate freeze,
subagents, or extra file edits.
