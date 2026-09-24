# Task 7 Fix Round 1 brief

## Root causes

Independent review reproduced the 4,140/5 mutation result and raw filesystem
escape. The binding design and plan now contain the controller-approved
pre-freeze contract refinement.

1. Public targets can be rebalanced across sites because only membership and
   counts are checked.
2. Evidence-family assignments are flattened to a source union because source
   captures have no private family declaration.
3. Public source IDs do not reject evidence-family/repeat/alias tokens.
4. `_is_regular_file()` performs an unprotected second `lstat()` and leaks
   `FileNotFoundError`.
5. The matrix uses singleton nested source lists and does not enumerate nested
   order attacks.

## Allowed writes

- `iclr2027/architecture_target_roster.py`
- `build_iclr2027_architecture_target_roster.py`
- `tests/test_iclr2027_architecture_target_roster.py`
- append Fix Round 1 evidence to `task-7-report.md`

Do not edit other production/tests, design/plan/ledger, candidate artifacts, or
the background diagnostic. No git, network, credentials, held-out/test/OOD
data, subagents, candidate freeze, model call, or non-dry experiment.

## TDD sequence

Before production edits, add and run separate minimal RED witnesses for:

1. swapping one target between site 00 and 01 while preserving 12/11/11;
2. swapping `law` and `geometry` sources after resealing spec/roster;
3. each public source-ID token `geometry`, `repeat-01`, and `alias-01`;
4. omitted captured source object returning stable
   `source_capture_missing_or_changed`, not raw `FileNotFoundError`;
5. public target, target-spec family, and locator two-element nested-list
   reordering.

Record exact RED command/results. Every expectation must be independently
constructed and exercise real code.

## Minimal production contract

### Target/site binding

For each byte-ordinal site `i`, require the exact target refs
`<site_ref>-target-00` through `<site_ref>-target-(allocation[i]-1)`, zero
padded to two digits, bound to that same `site_ref` and in global byte order.
Reject any mismatch with stable code `target_site_pairing`. Do not infer the
site from counts alone.

### Private evidence-family binding

Refine the not-yet-released `SourceCaptureV1` exact record with one required
field `evidence_families`. It is a nonempty, unique, UTF-8 byte-ordinal list or
tuple whose values are a subset of exactly `site`, `law`, `parking`, `program`,
and `geometry`.

- Target fixtures use opaque public IDs such as `source-0000`; no public source
  ID embeds target/site/family/repeat/alias meaning.
- Each target-family assignment must reference a capture whose
  `evidence_families` contains that family, else
  `evidence_family_source_mapping`.
- Every locator source must declare `site`, else
  `locator_source_family_mapping`.
- A capture may legitimately declare more than one family. Independent review
  remains responsible for the factual correctness of declarations; the
  validator owns exact membership binding.

Do not change the source-capture schema-version literal: this is an explicit
pre-freeze v1 contract correction and no real release exists. Update every
synthetic fixture and exact-key test accordingly.

### Public source-ID grammar

At the public target parser boundary, reject any source ID matching the existing
normalized identity alias/evidence-family grammar. Preserve ordinary opaque
IDs. Do not add broad tokens to the global protected-key regex because public
schema keys such as `program` are legitimate.

### Stable filesystem boundary

Make `_is_regular_file()` return `False` for `OSError` from its `lstat()` path,
so `_load_verified_inputs()` emits `source_capture_missing_or_changed`. Keep
the existing reparse-point rejection. Do not add retry behavior.

### Nested-order closure

Add distinct two-element order attacks for each of 34 public target
`source_ids`, each of 34x5 target-spec family lists, and each of three locator
source lists. These are attacks, unlike the 240 top-level private set
permutations, which remain separately asserted invariants. Preserve distinct
labels and report the updated attempted count.

## Ordered verification

After individual GREEN witnesses, run and stop on first failure:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterMutationClosureTests -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_dataset tests.test_iclr2027_freeze_v2 tests.test_iclr2027_precall_design_lock tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol tests.test_iclr2027_architecture_obligations -v
C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
C:\Python313\python.exe -E -B -m ruff format --check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
```

The mutation result must report explicit per-family totals, accepted `0`, 240
set invariants, and one release invariant. Rehash all incoming/outgoing files,
prove unrelated production pins unchanged, and append RED/GREEN/root-cause/gate
evidence to the report.
