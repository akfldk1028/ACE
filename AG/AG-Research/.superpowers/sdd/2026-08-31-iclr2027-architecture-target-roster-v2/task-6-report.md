# Task 6 report — runner v3 binding and stale-checkpoint rejection

## Result

Implemented receipt-bound Exp08 runner manifests without changing legacy
no-sidecar behavior.

- `run_exp08_architecture.py` now accepts `--target-roster PATH` and
  `--target-roster-receipt PATH` as a both-or-neither pair.
- A supplied pair is permitted only for frozen private development runs. The
  public roster and canonical v2 receipt are verified against the loaded
  private projection commitment before `checkpoint_dir.mkdir()`.
- A verified pair produces exact
  `ace.iclr2027.exp08_run_manifest.v3`; an absent pair continues to produce
  exact `ace.iclr2027.exp08_run_manifest.v2`.
- V3 adds exactly `target_roster_sha256`,
  `target_roster_receipt_sha256`, and `combined_dev_target_count`. The receipt
  supplies all three values, and the combined count is exactly 64. Legacy
  `case_count` and `expected_case_count` remain 30.
- `validate_run_manifest()` selects an exact schema-specific planned/executed
  key closure. `run_manifest_identity()` returns the unchanged v2 closure or
  the v3 closure containing all three receipt fields.
- Existing-manifest compatibility now requires equal schemas and compares the
  complete schema-specific identity. V2/v3 mixing and roster, receipt, or
  combined-count drift all require a new checkpoint directory.
- Dry runs stop before the execution/payment branch and do not call
  `ExperimentRunner.run_single`.

## TDD: RED and GREEN

The production change that each test protects was named before implementation:
missing CLI binding, optional-field ambiguity, unverified sidecars creating a
checkpoint, stale receipt reuse, v2/v3 mixing, loss of v3 fields during the
planned-to-executed projection, and a model call during a dry run.

The first RED invocation found a test-fixture setup error (the sidecar helper's
parent directory did not exist). I corrected only that fixture and reran RED.
The corrected exact command was:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol -v
```

Corrected RED failed at the intended missing-feature boundary: every new
sidecar/v3 runner path stopped in `argparse` because `--target-roster` and
`--target-roster-receipt` did not exist. The exact legacy v2 pin and all 27
pre-existing run-manifest/dynamic-protocol regression tests passed.

After the minimal implementation and the independent three-field checkpoint
drift test, the same exact GREEN command passed all 35 tests. The final fresh
post-format invocation again passed all 35 tests in 33.097 seconds.

Coverage added in `TargetRosterRunnerTests` proves:

- exact v2 bytes, schema, identity closure, case count, and absence of v3 keys;
- exact v3 planned and executed validation and identity preservation;
- receipt-derived roster SHA, canonical receipt SHA, and combined count 64;
- rejection of public-fixture mode, test split, one-sided CLI arguments, null
  projection commitment, mismatched projection commitment, missing/extra v3
  keys, invalid count, and unverified mutated bytes;
- all pre-checkpoint failure cases leave the checkpoint path absent;
- valid but resealed roster/receipt drift cannot reuse a v3 checkpoint;
- each of the three v3 identity fields independently invalidates a stale
  checkpoint;
- v2 checkpoint plus v3 proposal and v3 checkpoint plus v2 proposal both fail;
- a dry run makes exactly zero `ExperimentRunner.run_single` calls.

## Exact v2 no-drift pin

Before production edits, a real frozen-private development dry run with
`--code-commit legacy-pin` recorded:

| Property | Pin |
| --- | --- |
| Exit | `0` |
| Manifest schema | `ace.iclr2027.exp08_run_manifest.v2` |
| Manifest bytes | `1702` |
| Manifest SHA-256 | `200fcaf552f83d528b3955143af8d02dbca366a455566171c9aafe241e4cc310` |
| `case_count` | `30` |
| `planned_run_count` | `450` |

The post-implementation test recreates those exact bytes and hash. The v2
identity field order remains:

```text
schema_version, input_mode, split, patterns, repeats, model, code_commit,
case_count, expected_case_count, planned_run_count, stage_case_counts,
decision_case_counts, input_hashes, identity_commitment,
registry_core_sha256, split_manifest_sha256, plan_sha256
```

No-sidecar validation continues to reject any additional v3 key, so v2 has no
optional-field ambiguity.

## Fresh-root v3 and zero-call witness

A fresh temporary checkpoint used a sidecar produced by the reviewed roster
builder and bound to the repository's frozen projection. The command invoked
only `--dry-run`; `ExperimentRunner.run_single` was instrumented to raise if
called.

| Property | Witness |
| --- | --- |
| Exit | `0` |
| `ExperimentRunner.run_single` calls | `0` |
| Manifest schema | `ace.iclr2027.exp08_run_manifest.v3` |
| Manifest bytes | `1937` |
| Manifest SHA-256 | `229000e1607479b9757f1414603aba5954f2471f1e9cc6d000216c5ecba34f05` |
| `case_count` / `expected_case_count` | `30` / `30` |
| `combined_dev_target_count` | `64` |
| `target_roster_sha256` | `71fd440fd66ba14d0488181af1f48fa8d0e602fe6c628625860aecb26b7e26af` |
| `target_roster_receipt_sha256` | `a2435dcab085b5ee9b3ee762a8bb56413e4df70eea44793bee728a4523196884` |

The v3 identity is the unchanged 17-field v2 identity followed by:

```text
target_roster_sha256, target_roster_receipt_sha256,
combined_dev_target_count
```

The planned-to-executed validation witness preserved the complete 20-field
identity exactly.

## Verification

- Exact Task-6 command: 35 tests passed.
- Full target-roster plus legacy runner regression command:
  `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_runner_v2 -v`
  — 54 tests passed.
- `C:\Python313\python.exe -E -B -m ruff check iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py`
  — `All checks passed!`.
- `C:\Python313\python.exe -E -B -m ruff format --check iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py`
  — all three files formatted.

Final file pins (normalized AST is
`sha256(ast.dump(tree, include_attributes=False))`):

| File | Bytes | Raw SHA-256 | Normalized AST SHA-256 |
| --- | ---: | --- | --- |
| `iclr2027/run_manifest.py` | 13429 | `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8` | `a73ffa8a00b4d65eb1cd137c560c9bf5e6b581218f0af4c06005c20751cb9c52` |
| `run_exp08_architecture.py` | 26319 | `91b3a7e10e25372a29e83c1c5e8d1067534c293f9458999dcb2a5aa4c5fde0f6` | `4911e199daa21f97ba08bc4c37a7e1435dd68f1047e1cec0e1f1eddce15f3c01` |
| `tests/test_iclr2027_architecture_target_roster.py` | 66447 | `3038b3e79c77de0df61a841ff1762922b97965878abf3b403beb2b45179473ab` | `4ef18170ec3e0832e83a80390679d15ffb3b68ff44bbde5beae5c8fc74f77c2d` |

## Concerns and boundaries

No product blocker remains. No network access, held-out data access, actual
model call, git operation, or paid run occurred. The requested Task-6 command
and both manual pin witnesses were dry-only.

Process note: the optional broad `tests.test_iclr2027_runner_v2` regression
suite enters existing non-dry code paths under its established test doubles.
Those checks made no `ExperimentRunner`/model/network call, but the suite was
broader than the brief's required dry-only Task-6 command. No manual or real
non-dry execution was performed.

## Fix Round 1 — fail before checkpoint creation

### Independent-review finding and repair

The review finding reproduced against the Task-6 implementation:
`checkpoint_dir.mkdir()` ran after plan construction but before
`validate_run_manifest()` and `_existing_compatible_manifest()`. Consequently,
a verified sidecar combined with manifest-invalid `--model private-model`
raised the privacy-validation error but left an empty fresh checkpoint
directory.

The repair is deliberately limited to the write boundary. The runner now:

1. constructs and validates the complete v2/v3 manifest;
2. reads and validates any existing checkpoint manifest and checks the full
   schema-specific identity;
3. resolves planned/executed resume state;
4. creates `checkpoint_dir` immediately before the first
   `write_json_atomic()` call.

No manifest schema, identity field, compatibility rule, sidecar verification,
or write payload changed.

### Fix Round 1 RED / GREEN

Added
`test_manifest_invalid_model_fails_before_checkpoint_creation`. It builds valid
reviewed sidecars, requests a fresh checkpoint with `--model private-model`,
asserts the existing privacy-validation exception, and asserts that the fresh
checkpoint path remains absent.

The first class run showed that the validator's exact existing message was
`run manifest contains private or path-like content`; the test expectation was
corrected without touching production. The focused corrected RED command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests.test_manifest_invalid_model_fails_before_checkpoint_creation -v
```

failed only at the intended contract assertion:

```text
AssertionError: True is not false
```

After moving the single `mkdir` call, the complete runner class passed 9/9.
This includes every existing sidecar-specific pre-checkpoint case: one-sided
arguments, public-fixture mode, test split, projection mismatch, noncanonical
or mutated sidecar bytes, plus the new manifest-invalid model case. Each fresh
checkpoint path remains absent on failure.

### Fix Round 1 gates

The gates were run sequentially in the brief's order, stopping would have
occurred on the first failure:

1. `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests -v`
   — 9 tests passed.
2. `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterRunnerTests tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol -v`
   — 36 tests passed.
3. `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_runner_v2 -v`
   — 55 tests passed.
4. `C:\Python313\python.exe -E -B -m ruff check iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py`
   — `All checks passed!`.
5. `C:\Python313\python.exe -E -B -m ruff format --check iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py`
   — all three files already formatted.

### Recomputed manifest and no-call pins

A fresh dry-only witness recreated both schemas with
`ExperimentRunner.run_single` instrumented to raise on any call. Both commands
exited 0 and the combined call count was exactly 0.

| Manifest | Bytes | SHA-256 | Schema | Legacy cases | Combined targets |
| --- | ---: | --- | --- | ---: | ---: |
| V2 no sidecar | 1702 | `200fcaf552f83d528b3955143af8d02dbca366a455566171c9aafe241e4cc310` | `ace.iclr2027.exp08_run_manifest.v2` | 30 | absent |
| V3 reviewed sidecar | 1937 | `229000e1607479b9757f1414603aba5954f2471f1e9cc6d000216c5ecba34f05` | `ace.iclr2027.exp08_run_manifest.v3` | 30 | 64 |

Thus the exact v2 legacy bytes and the Task-6 v3 bytes are unchanged by the
write-order repair.

### Fix Round 1 final source pins

Normalized AST is `sha256(ast.dump(tree, include_attributes=False))`.
`iclr2027/run_manifest.py` was not edited in this round and its raw/AST pins
remain exact.

| File | Bytes | Raw SHA-256 | Normalized AST SHA-256 |
| --- | ---: | --- | --- |
| `iclr2027/run_manifest.py` | 13429 | `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8` | `a73ffa8a00b4d65eb1cd137c560c9bf5e6b581218f0af4c06005c20751cb9c52` |
| `run_exp08_architecture.py` | 26319 | `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6` | `2c8e14b62f65259e0ce552d2c7e41f5e79c4d27c55a5a3f4ccb6ffc6438832ad` |
| `tests/test_iclr2027_architecture_target_roster.py` | 67079 | `ccd44597febff2bf3a1e94beaf973a938c074837d0cb125a805140138999a9aa` | `96c89f6026aef352dcf29bb3b8c3a6a51f7ed5cad5c4eaaa2af94bec3cfc85e4` |

### Fix Round 1 boundaries and concerns

No product concern remains. No network, held-out/test/OOD data, git operation,
subagent, actual model call, paid run, or manual non-dry run occurred. The only
execution-path coverage was the brief-mandated existing regression gate, whose
non-dry branches use established test doubles; the manual pin witness was
dry-only and recorded zero `run_single` calls.
