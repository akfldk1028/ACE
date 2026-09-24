# Task 7 report: deterministic mutation closure

## Final status

`COMPLETE_VALIDATOR_CLOSURE`. After three documented fix rounds, the expanded
matrix attempted 4,524 attacks and accepted exactly zero; 240 top-level private
set permutations and the exact-eight release census passed as explicit
invariants. The complete target-roster module passed 51/51, the prescribed
combined suite passed 174/174, and Ruff lint/format gates passed. No real
candidate was admitted; the candidate gate remains a separate source and
geometry decision.

The initial run below is preserved as RED history: it accepted five of 4,140
attacks and leaked one raw `FileNotFoundError`, then stopped before later gates.

## Episode A: superseded preflight stop

The first preflight stopped because `run_exp08_architecture.py` and the focused
test differed from the original brief pins. The controller subsequently ruled
that both values were the exact Task-6 Fix Round 1 pins accepted by independent
re-review and updated the brief. This episode is preserved as historical
preflight evidence; it is not final drift:

- runner: 26,319 bytes,
  `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6`
- focused test baseline: 67,079 bytes,
  `ccd44597febff2bf3a1e94beaf973a938c074837d0cb125a805140138999a9aa`

The resumed fresh preflight matched every corrected incoming pin.

## TDD evidence

### RED

Exact command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterMutationClosureTests -v
```

Result: exit `1`, elapsed `1.925s`, one test/one failure. The exact witness was:

```text
AssertionError ... mutation census is missing all eleven required families
```

This proved the required mutation census was absent before machinery was
implemented.

### Focused implementation run

The same exact command was rerun after independently implementing all eleven
families. A first diagnostic run identified two synthetic self-hash/PNU
collisions and one callback that wrote a roster before mutating it. Those
test-harness defects were corrected without production edits. The corrected
run produced:

```text
MUTATION_ATTEMPTED=4140
MUTATION_ACCEPTED=5
SET_PERMUTATION_INVARIANTS=240
RELEASE_SURFACE_INVARIANTS=1
```

Result: exit `1`, elapsed `26.318s`, one test/one failure. All 240 pure
permutations of the top-level private canonical sets passed separately as
semantic invariants, following the controller's binding-design clarification.
The builder's exact-eight-file release census invariant also passed.

## Mutation census

| Family | Attempted | Accepted |
| --- | ---: | ---: |
| Public roster | 435 | 1 |
| Public leakage | 14 | 3 |
| Source captures | 2,770 | 0 |
| Site locators | 36 | 0 |
| Target specifications | 460 | 1 |
| Geometry receipts | 340 | 0 |
| Blind-overlap check | 10 | 0 |
| Independent review | 10 | 0 |
| Freeze receipt v2 | 30 | 0 |
| Builder/release surface | 26 | 0 accepted; 1 wrong-surface exception |
| Cross-layer attacks | 9 | 0 |
| **Total** | **4,140** | **5** |

Distinct row identities are embedded in every row/field, omission, and
duplication label; row deletion and duplication cannot collapse to the same
oracle label.

## Accepted attacks

1. `public_roster:cross-site-rebalanced-pairing`
2. `public_leakage:source-list:evidence-family`
3. `public_leakage:source-list:repeat`
4. `public_leakage:source-list:alias`
5. `target_specifications:evidence-family-source-swap`

The wrong-surface attack was
`builder_release_surface:source-object:omit`: omission of a captured source
object raised raw `FileNotFoundError` from the builder path instead of the
expected stable `TargetRosterError` rejection.

## Gate results

| Ordered gate | Result | Time |
| --- | --- | ---: |
| Focused mutation class (TDD prerequisite) | **FAIL**: 5 accepted, 1 wrong-surface exception | 26.318s |
| Complete focused test file | not run; stopped at focused GREEN failure | n/a |
| Required gate 1: focused file | not run | n/a |
| Required gate 2: combined tests | not run | n/a |
| Required gate 3: Ruff check | not run | n/a |
| Required gate 4: Ruff format check | not run | n/a |

## Final pins and production no-drift evidence

Production files matched their corrected incoming pins after the failed
focused run:

| File | Final bytes | Final SHA-256 | Result |
| --- | ---: | --- | --- |
| `iclr2027/architecture_target_roster.py` | 40,429 | `2d873d179e537406273ba7be18855a1edd477fca0b2a7bd58ebc5a7500acc11d` | no drift |
| `build_iclr2027_architecture_target_roster.py` | 12,515 | `7e8e39e58083f60cc27603b708ebbeac52dcfb4d6df0c3d0cef7f15b57d3f86b` | no drift |
| `iclr2027/dataset.py` | 31,859 | `b3469093d68e11b7f96266e1f2b5259e7aee279aedafcb121e470e36fa31b99e` | no drift |
| `iclr2027/precall_design_lock.py` | 44,855 | `9ea5ddeed9294e904f030f99b79a0162c5d96b6ce39f248fa3b4c1894579a714` | no drift |
| `iclr2027/run_manifest.py` | 13,429 | `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8` | no drift |
| `run_exp08_architecture.py` | 26,319 | `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6` | no drift |
| `tests/test_iclr2027_architecture_target_roster.py` | 135,396 | `b5a7ee10f9017fdc4759f5d24987d1cae0874b520df8eeb99c50d71c610fc752` | allowed Task-7 write |

## Scientific and operational boundary

No model execution, model call, network access, credential access, candidate
acquisition, candidate freeze, held-out/test/OOD-data access, git operation, or
subagent use occurred. No production file was edited. This task does not prove
that Guro, Seoul Innovation Park, or Airport-dong supplies 12/11/11 eligible
subjects and does not admit any real candidate. The result proves that the
current validator surface is not mutation-closed under the Task-7 contract.

## Concerns and next authorization needed

Production changes were outside Task 7's allowed writes. A separately reviewed
fix task is required for the five accepted channels and the raw
`FileNotFoundError` escape before this matrix can reach GREEN and the ordered
gates can run.

---

## Fix Round 1 evidence (2026-09-01)

### Status

`STOPPED_ORDERED_GATE_1`. The reviewed production fixes made every mutation
reject (`4,524 attempted / 0 accepted`), but the first ordered gate found two
test-oracle attacks rejected by a different surface than intended. The brief
requires stopping at the first ordered failure, so no broader gate was run and
the oracle defects were not changed in this round.

### Incoming pins

| File | Incoming bytes | Incoming SHA-256 |
| --- | ---: | --- |
| `iclr2027/architecture_target_roster.py` | 40,429 | `2d873d179e537406273ba7be18855a1edd477fca0b2a7bd58ebc5a7500acc11d` |
| `build_iclr2027_architecture_target_roster.py` | 12,515 | `7e8e39e58083f60cc27603b708ebbeac52dcfb4d6df0c3d0cef7f15b57d3f86b` |
| `tests/test_iclr2027_architecture_target_roster.py` | 135,396 | `b5a7ee10f9017fdc4759f5d24987d1cae0874b520df8eeb99c50d71c610fc752` |
| `task-7-report.md` | 5,775 | `8caec845d620daceb41f7c9464263f98cdb4934db905a0ed2b24358d271ab8d2` |

All unrelated production pins matched the Task-7 final pins before edits.

### Separate RED witnesses

Each command used
`C:\Python313\python.exe -E -B -m unittest <fully-qualified-test> -v`.

| Witness | RED result | Time |
| --- | --- | ---: |
| Rebalanced cross-site pairing | FAIL: expected `target_site_pairing`, no exception | 2.474s |
| Resealed law/geometry source swap | FAIL: expected `evidence_family_source_mapping`, no exception | 1.978s |
| Public `geometry`/`repeat-01`/`alias-01` source IDs | FAIL: three subtests, no exceptions | 1.937s |
| Omitted captured source object | FAIL: raw `FileNotFoundError` escaped stable boundary | 2.063s |
| 207 distinct nested-order attacks | FAIL: all 207 census labels absent | 2.191s |

The omitted-source witness was first observed as a unittest error, then
rewritten before production changes to fail explicitly on any non-stable
exception. The recorded RED above is the corrected assertion failure.

### Minimal production changes

- Public target refs are now bound byte-ordinally to their site and exact
  zero-padded allocation position, with `target_site_pairing` on mismatch.
- Source captures require exact `evidence_families`; admission verifies every
  target-family declaration and every locator's `site` declaration.
- Synthetic source IDs are opaque and the public parser rejects the reviewed
  alias/evidence/repeat grammar without broadening protected schema keys.
- Builder `_is_regular_file()` now returns `False` on `OSError` from `lstat()`,
  preserving the stable `source_capture_missing_or_changed` boundary.
- The matrix adds all 34 public-target, 170 target-family, and three locator
  nested-order attacks while retaining 173 captures and 240 top-level
  canonical-set permutation invariants.

### Individual GREEN evidence

| Witness | Result | Time |
| --- | --- | ---: |
| Rebalanced cross-site pairing | PASS | 2.039s |
| Resealed family-source swap | PASS | 2.122s |
| Public semantic source-ID tokens | PASS | 2.004s |
| Stable omitted-source error | PASS | 3.329s |
| 207 nested-order attacks | PASS | 2.076s |

### Ordered gate 1

Exact command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterMutationClosureTests -v
```

Result: exit `1`, elapsed `26.214s`:

```text
MUTATION_ATTEMPTED=4524
MUTATION_ACCEPTED=0
SET_PERMUTATION_INVARIANTS=240
RELEASE_SURFACE_INVARIANTS=1
```

Per-family attempted counts:

| Family | Attempted | Accepted |
| --- | ---: | ---: |
| Public roster | 469 | 0 |
| Public leakage | 14 | 0 |
| Source captures | 2,946 | 0 |
| Site locators | 39 | 0 |
| Target specifications | 631 | 0 |
| Geometry receipts | 340 | 0 |
| Blind-overlap check | 10 | 0 |
| Independent review | 10 | 0 |
| Freeze receipt v2 | 30 | 0 |
| Builder/release surface | 26 | 0 |
| Cross-layer attacks | 9 | 0 |
| **Total** | **4,524** | **0** |

The gate failed its independent-surface assertion for exactly two attacks:

1. `public_roster:target-order:10:11` expected `target_order`, but that
   deterministic reseal produced a self-hash containing a PNU-shaped digit
   channel and hit `protected_identifier` first.
2. `target_specifications:source-reference:missing` expected
   `source_capture_reference_missing`, but the refined multi-family fixture
   reuses captures across two families; replacing only one family reference
   changed the public source union and hit `target_source_public_binding`
   first.

Both are test-oracle construction issues. They do not change the explicit
accepted count of zero, but the matrix correctly refuses to count rejection by
an unrelated surface as closure.

### Remaining ordered gates

| Gate | Result |
| --- | --- |
| Complete target-roster test file | not run; stopped at gate 1 |
| Combined focused suite | not run |
| Ruff check | not run |
| Ruff format check | not run |

### Outgoing pins at stop

| File | Outgoing bytes | Outgoing SHA-256 | Status |
| --- | ---: | --- | --- |
| `iclr2027/architecture_target_roster.py` | 41,930 | `e06d403e936006f906b8cc3b7fb694560d446ae4dc8e28d8095a2bf86ab30b5b` | allowed Fix Round 1 write |
| `build_iclr2027_architecture_target_roster.py` | 12,614 | `fcb51fc049bfe2bcdd89024df19bd893c2acf95342b2b4da27623e6fba0189ca` | allowed Fix Round 1 write |
| `tests/test_iclr2027_architecture_target_roster.py` | 143,947 | `b2f65a402e5e5c61ba79c279b734b8b5a31594027112ca5e32e23294fa4c04e1` | allowed Fix Round 1 write |
| `iclr2027/dataset.py` | 31,859 | `b3469093d68e11b7f96266e1f2b5259e7aee279aedafcb121e470e36fa31b99e` | unchanged |
| `iclr2027/precall_design_lock.py` | 44,855 | `9ea5ddeed9294e904f030f99b79a0162c5d96b6ce39f248fa3b4c1894579a714` | unchanged |
| `iclr2027/run_manifest.py` | 13,429 | `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8` | unchanged |
| `run_exp08_architecture.py` | 26,319 | `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6` | unchanged |

### Boundary statement

No network, credentials, held-out/test/OOD data, model call, non-dry
experiment, candidate acquisition, candidate freeze, git operation, subagent,
or protected-data access occurred. No candidate is admitted, and this stopped
round makes no 12/11/11 empirical eligibility claim.

---

## Fix Round 2 evidence (2026-09-01)

### Status

`STOPPED_FORMAT_GATE`. Both wrong-surface oracle cases from Fix Round 1 were
closed, the full mutation matrix reached GREEN at `4,524 / 0`, both test gates
and Ruff lint passed, and the final ordered format-check gate failed. No files
were formatted after the failure.

### Incoming pins

| File | Incoming bytes | Incoming SHA-256 |
| --- | ---: | --- |
| `iclr2027/architecture_target_roster.py` | 41,930 | `e06d403e936006f906b8cc3b7fb694560d446ae4dc8e28d8095a2bf86ab30b5b` |
| `build_iclr2027_architecture_target_roster.py` | 12,614 | `fcb51fc049bfe2bcdd89024df19bd893c2acf95342b2b4da27623e6fba0189ca` |
| `tests/test_iclr2027_architecture_target_roster.py` | 143,947 | `b2f65a402e5e5c61ba79c279b734b8b5a31594027112ca5e32e23294fa4c04e1` |
| `task-7-report.md` | 12,010 | `df7afa2c893d952d7ae3166cfd73eed5edf49ae117c51253d9801f6b277a7dbc` |

All builder and unrelated-production pins matched Fix Round 1 before changes.

### RED and minimal correction

Exact RED command:

```text
C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterFixRound1RedTests.test_valid_self_hash_is_not_scanned_as_raw_pnu -v
```

Result: exit `1`, elapsed `2.750s`. The witness independently confirmed that
the known target-order reseal was exact lowercase 64-hex and contained a
boundary-delimited 19-digit substring. The validator returned
`protected_identifier`, not the intended `target_order`.

The production change exempts only an exact valid lowercase 64-hex digest from
raw-PNU substring scanning. It retains every key/token/URI/path check and raw
PNU rejection for non-digest strings. Typed hash fields remain checked by their
own parsers.

The shared-source missing attack was corrected only in test code: the chosen
source is replaced in every evidence-family list that shares it and in the
public source union before spec/roster resealing. No production binding order
or rule was weakened.

### Focused GREEN witnesses

| Witness | Result | Time |
| --- | --- | ---: |
| Exact-digest PNU false-positive | PASS | 2.154s |
| Shared-source missing closure | PASS as `source_capture_reference_missing` | 2.208s |

### Ordered gates

| Gate | Result | Time |
| --- | --- | ---: |
| Mutation class | PASS, 1/1 | 24.687s |
| Complete target-roster file | PASS, 51/51 | 59.291s |
| Combined focused suite | PASS, 174/174 | 69.233s |
| Ruff check | PASS, all checks | 0.672s |
| Ruff format check | **FAIL**, five files would reformat | 0.119s |

The mutation gate printed exactly:

```text
MUTATION_ATTEMPTED=4524
MUTATION_ACCEPTED=0
SET_PERMUTATION_INVARIANTS=240
RELEASE_SURFACE_INVARIANTS=1
```

Per-family counts remained unchanged from Fix Round 1: public roster 469,
public leakage 14, source captures 2,946, site locators 39, target
specifications 631, geometry receipts 340, blind-overlap 10, independent review
10, freeze receipt 30, builder/release 26, and cross-layer 9.

The exact final gate output was:

```text
Would reformat: build_iclr2027_architecture_target_roster.py
Would reformat: iclr2027\architecture_target_roster.py
Would reformat: iclr2027\dataset.py
Would reformat: iclr2027\precall_design_lock.py
Would reformat: tests\test_iclr2027_architecture_target_roster.py
5 files would be reformatted, 2 files already formatted
```

Builder, dataset, and pre-call design lock were unchanged and outside Fix Round
2 write authority. The round stopped without formatting any file.

### Outgoing pins at stop

| File | Outgoing bytes | Outgoing SHA-256 | Status |
| --- | ---: | --- | --- |
| `iclr2027/architecture_target_roster.py` | 41,956 | `e6e6463c9908ae5e20fe9b5f8ec76f28a235102827ed47e5125a6bc1bc90bde6` | allowed Fix Round 2 write |
| `tests/test_iclr2027_architecture_target_roster.py` | 145,173 | `54fed725611f538f3d3fa55b653c6cb51175da34aa00bac1f99a38aeaef3c4de` | allowed Fix Round 2 write |
| `build_iclr2027_architecture_target_roster.py` | 12,614 | `fcb51fc049bfe2bcdd89024df19bd893c2acf95342b2b4da27623e6fba0189ca` | unchanged |
| `iclr2027/dataset.py` | 31,859 | `b3469093d68e11b7f96266e1f2b5259e7aee279aedafcb121e470e36fa31b99e` | unchanged |
| `iclr2027/precall_design_lock.py` | 44,855 | `9ea5ddeed9294e904f030f99b79a0162c5d96b6ce39f248fa3b4c1894579a714` | unchanged |
| `iclr2027/run_manifest.py` | 13,429 | `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8` | unchanged |
| `run_exp08_architecture.py` | 26,319 | `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6` | unchanged |

### Boundary statement

No git, network, credentials, protected data, model/non-dry run, candidate
acquisition, candidate freeze, or subagent use occurred. This test closure does
not admit a candidate or establish 12/11/11 real-world eligibility.
## Fix Round 3: mechanical formatter closure

The final Task-7 format gate was the first plan gate to include unchanged
`dataset.py` and `precall_design_lock.py`. Ruff 0.11.5 reported five files as
unformatted. The controller authorized exactly one mechanical formatter run
over the seven-file gate surface. It reported `5 files reformatted, 2 files
left unchanged`.

All five reformatted files were UTF-8/LF with zero CR bytes before and after.
Their normalized AST hashes were recomputed immediately after formatting and
again after all gates; every value remained exactly unchanged:

| File | Binding normalized-AST SHA-256 |
| --- | --- |
| `build_iclr2027_architecture_target_roster.py` | `31dd03836bcab2d528dfcf63410b61114016f1c0bc78d2e31c5a9a92778271f8` |
| `iclr2027/architecture_target_roster.py` | `1088fde21291ddac17a816d1e2d1559af7872a1761f7fd4aaffa94743db14270` |
| `iclr2027/dataset.py` | `77f90a56256712073bbe7c90c3b3305ea2a244a9e99032f4b2c47b2abb4f868e` |
| `iclr2027/precall_design_lock.py` | `81d93df63c762eab1d9e1cafb633749347c86af212bb124bb49cbdc449c9f1d8` |
| `tests/test_iclr2027_architecture_target_roster.py` | `4b84c93e6555b9d48c3c948a120d022e7f832d38d85ade0628b948e66d37dfb5` |

The already formatted manifest and runner remained byte-identical. Historical
Task-4/5 raw pins for dataset/pre-call are superseded by this formatter event;
their AST identities and tested behavior remain unchanged.

Final raw pins are:

| File | SHA-256 |
| --- | --- |
| `iclr2027/architecture_target_roster.py` | `3b047354809f2cc913d886f8be7a92255fcfa2734ee4b535be56091fd73de199` |
| `build_iclr2027_architecture_target_roster.py` | `6eb7c596ee1a550e4006fa26f70635d09b1926481e39fbc62842593a2f6df09c` |
| `iclr2027/dataset.py` | `bba010219a56d2f2cae12d0722ba1fc7d8c7c80cdecc3561edd4083f1d4191ef` |
| `iclr2027/precall_design_lock.py` | `eeb65c6248acf6abe4bcf3c42aa4eee45cd08a23d631afd76dcfadd384ffcebf` |
| `iclr2027/run_manifest.py` | `bb19aca2c790910157da50872c23282224cbe541bcec997f798d4aad154d0fa8` |
| `run_exp08_architecture.py` | `b84502d44c711764de621a54624398903607bbad76add3b7389f415b2e2711e6` |
| `tests/test_iclr2027_architecture_target_roster.py` | `e802355eb75a6e349d3b7b9ab92a0f0582aec76acb3a88397cb46a5f7b20d31f` |

Post-format ordered gates all passed:

1. Mutation class: 1/1 in 25.979 seconds; 4,524 attempted, 0 accepted,
   240 canonical-set invariants, one release invariant.
2. Complete target-roster module: 51/51 in 53.230 seconds of unittest time.
3. Prescribed combined seven-module suite: 174/174 in 60.842 seconds of
   unittest time.
4. Ruff check: `All checks passed!`.
5. Ruff format check: `7 files already formatted`.

No model/non-dry execution, network/credential/protected-data access,
candidate freeze, git action, or extra formatter run occurred.
