# Task 7 brief: deterministic mutation closure

## Objective

Add an independent, exhaustive deterministic mutation matrix for the complete
architecture target-roster admission/freeze/verification surface. The matrix
must accept exactly zero mutations. This task does not authorize a candidate
freeze or any model execution.

## Allowed writes

- `tests/test_iclr2027_architecture_target_roster.py`
- `.superpowers/sdd/2026-08-31-iclr2027-architecture-target-roster-v2/task-7-report.md`

Do not edit production code, the design, the plan, the public paper, any
candidate acquisition package, any existing frozen release, or the background
diagnostic. Do not use git, the network, credentials, held-out/test/OOD data,
model outcomes, or subagents. Do not start a model run.

## Incoming implementation pins

- `iclr2027/architecture_target_roster.py`: 40,429 bytes,
  `2d873d179e537406273ba7be18855a1edd477fca0b2a7bd58ebc5a7500acc11d`
- `build_iclr2027_architecture_target_roster.py`: 12,515 bytes,
  `7e8e39e58083f60cc27603b708ebbeac52dcfb4d6df0c3d0cef7f15b57d3f86b`
- `iclr2027/dataset.py`: 31,859 bytes,
  `b3469093d68e11b7f96266e1f2b5259e7aee279aedafcb121e470e36fa31b99e`
- `iclr2027/precall_design_lock.py`: 44,855 bytes,
  `9ea5ddeed9294e904f030f99b79a0162c5d96b6ce39f248fa3b4c1894579a714`
- `iclr2027/run_manifest.py`: 13,429 bytes,
  `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8`
- `run_exp08_architecture.py`: 26,319 bytes,
  `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6`
- focused test before Task 7: 67,079 bytes,
  `ccd44597febff2bf3a1e94beaf973a938c074837d0cb125a805140138999a9aa`

These two values supersede the earlier Task-6 pre-review pins. They are the
exact Task-6 Fix Round 1 values accepted by independent re-review; this is an
authorized baseline correction, not unreviewed drift.

Rehash every incoming production file before and after the task. Any drift is a
blocker.

## TDD protocol

1. Add a RED witness that demonstrates at least one real uncovered mutation or
   missing mutation census assertion. Record the exact failing command and
   failure.
2. Add the minimal independent test-owned mutation machinery. Do not copy
   production field constants, call production canonicalizers to derive
   expected bytes, or accept a mutation merely because another parser rejects
   it for an unrelated reason.
3. Rerun the focused mutation class, then the complete focused test file.

## Required mutation families

Use valid independently constructed synthetic fixtures only. Generate and
count a distinct attack for every applicable item below:

1. Public roster root: every root field, site-row field, target-row field,
   list order, allocation/order position, duplicate site/target pairing,
   cross-site reference, and self-hash.
2. Public leakage: prohibited key and prohibited normalized string-value
   channels at root, site, target, and nested source-list positions, covering
   PNU/address/URI/path, condition/outcome/gold/mutation, evidence-family and
   repeat/alias tokens.
3. Source captures: every row field, source bytes, length/hash,
   license/redistribution/effective-date, order, omission, duplication, and
   source closure.
4. Site locators: every row field, exact `split=dev`, ASCII PNU, parcel/site
   uniqueness, ordering, omission, duplication, and schema.
5. Target specifications: every row field, normalized subject identity,
   program/kind/stage/route, evidence-family source mapping, source reference,
   target hash, ordering, omission, duplication, and 12/11/11 allocation.
6. Geometry receipts: every row field, target reference, compiler/artifact
   commitments, geometry hash, exact `hard_pass=true`, ordering, omission, and
   duplication.
7. Blind-overlap check: every field, locator-set binding, protected-roster
   commitment, reviewer commitment, zero-overlap decision, self-hash, and
   wrong caller/binding.
8. Independent review: every field, roster/admission binding, status/reviewer,
   reviewed count/allocation, self-hash, and wrong pairing.
9. Freeze receipt v2: every one of the exact 22 fields, public/private file
   hash binding, counts 3/34 and combined 8/64, allocation 12/11/11,
   projection commitment, independent-review pin, order/extra/missing fields,
   and receipt self-hash.
10. Builder/release surface: exact eight inputs, source-object closure, exact
    eight outputs, path/type substitution, omission/extra object, stale release
    pairing, and mutation after capture where the existing public test APIs can
    exercise these without a real candidate package.
11. Cross-layer attacks: reseal a mutated lower layer and prove the next layer
    rejects it; independently mutate each runner-v3 binding field and prove a
    stale checkpoint cannot be reused.

The test must report an explicit total attempted-mutation count and an explicit
accepted count. Final accepted count must be exactly `0`. Preserve distinct
row identities in the test oracle so duplication/omission cannot collapse into
an indistinguishable label.

## Required gates

Run in order and stop on the first failure:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster -v
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster tests.test_iclr2027_dataset tests.test_iclr2027_freeze_v2 tests.test_iclr2027_precall_design_lock tests.test_iclr2027_run_manifest tests.test_iclr2027_dynamic_protocol tests.test_iclr2027_architecture_obligations -v
C:\Python313\python.exe -E -B -m ruff check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
C:\Python313\python.exe -E -B -m ruff format --check iclr2027/architecture_target_roster.py build_iclr2027_architecture_target_roster.py iclr2027/dataset.py iclr2027/precall_design_lock.py iclr2027/run_manifest.py run_exp08_architecture.py tests/test_iclr2027_architecture_target_roster.py
```

Do not autoformat production. If only the allowed test file fails the format
gate, report and stop; the controller will authorize formatting separately.

## Scientific boundary and report

This test task may prove validator closure only. It must not claim that Guro,
Seoul Innovation Park, or Airport-dong supplies 12/11/11 eligible subjects.
No real candidate is admitted unless a separate source audit proves all 34
distinct physical/programmatic target subjects plus license, geometry, blind
overlap, and independent-review receipts.

Record the RED/GREEN evidence, per-family mutation counts, exact accepted count,
all gate results/times, final file pins, production no-drift pins, and any
concerns in `task-7-report.md`. State explicitly that no model/network/candidate
freeze occurred.
