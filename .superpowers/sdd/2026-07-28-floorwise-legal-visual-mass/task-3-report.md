# Task 3 - bounded MASS feature materialization and shared selection analysis

## Result

- Main BOOK candidate generation now stores `source_surface_summary` instead
  of copying every renderer triangle into every candidate feature.
- `materialize_source_feature_surfaces()` reconstructs the legacy eager
  payload exactly and idempotently. Preview/repair paths remain eager; the
  bounded final VLM shortlist and selected board materialize on demand.
- Semantic/program evidence reads the summary when the triangle payload has
  not been materialized, so eager and lazy candidates receive the same gates.
- Visual silhouette reuse now caches compact Shapely view unions and pair
  distances. Cache values hold weak source references, verify object identity
  against Python id reuse, and never retain the giant triangle serialization.
- One bounded `CompatibilityAnalysis` is shared by anchors, greedy selection,
  exact search, MILP/beam search, rebalance, replenishment, and diagnostics.
  Its pair records also use identity-checked weak candidate references, so
  dropped candidates and their `SourceMass` meshes remain collectible. The
  `0.10` compatibility threshold and solver target cardinalities are unchanged.

## TDD evidence

RED was observed before implementation:

- summary-only feature test: unexpected `surface_materialization` argument;
- compact cache test: instrumentation API absent;
- shared analysis test: builder absent.

Focused GREEN:

- new lazy/eager parity, weak-cache GC, and 54-candidate unordered-pair tests:
  3/3;
- selector tests: 6/6;
- final VLM tests: 8/8;
- selection diagnostics: 1/1;
- silhouette tests: 3/3;
- source-surface tests: 7/7;
- compatibility and Candidate GC tests: 2/2;
- MILP tests: 3/3;
- rebalance and joint-anchor tests: 2/2;
- portfolio contract: 5/5;
- flow regressions: 19/19.

The requested four-module aggregate command was started once, but its shell
timed out while the Python child continued orphaned; a duplicate invocation
was stopped and the remaining orphan later exited without recoverable stdout.
It was not rerun as another aggregate job. The affected paths were instead
verified with the focused groups above.

## Performance and identity checks

- The 54-candidate analysis evaluates exactly `54 * 53 / 2 = 1,431`
  unordered pairs; reversed matrix access is cache-only.
- Weak-cache tests prove both source objects and real `_Candidate` instances
  can be garbage-collected after analysis.
- A four-source parity probe compared six compact distances with the legacy
  key implementation. Maximum floating-point delta was
  `5.551115123125783e-17`.
- A representative compiled feature measured 82,062 bytes eager versus
  55,114 bytes summary-only; the saving grows with recursive profiled-surface
  count because the summary is constant-size.

No paid VLM call and no long portfolio benchmark was run.

## Review Fix Round 1 - cardinality-first bounded fallback

### Root cause

The bounded no-MILP fallback ranked retained beam states by required coverage
before cardinality and filtered its terminal choice to any coverage-feasible
state. A single required-tag candidate incompatible with every other candidate
could therefore replace a mutually compatible ten-card set.

### RED evidence

Command:

```powershell
C:\Python313\python.exe manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_bounded_fallback_prefers_cardinality_before_isolated_required_coverage -v 2
```

Observed exit code `1`: the fallback returned `(0,)`, the isolated required
coverage witness, instead of the compatible ten-card set `(1, ..., 10)`.

### Fix

- Candidate visitation now considers pairwise conflict count before rare
  required coverage and score.
- Beam state rank is cardinality first, required coverage second, and score
  third.
- The terminal choice compares all retained compatible/cap-valid states
  instead of filtering to a smaller coverage-feasible state.
- The supplied compatibility matrix, typed caps, target, and shared `0.10`
  compatibility threshold are unchanged.
- Selector trace fields remain truthful: a missing/no-result MILP still
  records `milp_global_solver_used=False`, while bounded solver count and
  replacement evidence report the actual fallback result.

### GREEN evidence

Focused regression:

```powershell
C:\Python313\python.exe manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_bounded_fallback_prefers_cardinality_before_isolated_required_coverage -v 2
```

Observed: `Ran 1 test ... OK`, exit code `0`.

Focused exact/bounded/MILP/selector group:

```powershell
C:\Python313\python.exe manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_exact_solver_prefers_cardinality_when_full_coverage_is_infeasible design.test_maas_book_language.MaasBookLanguageRegistryTest.test_bounded_solver_recovers_twenty_set_from_large_greedy_trap design.test_maas_book_language.MaasBookLanguageRegistryTest.test_bounded_fallback_prefers_cardinality_before_isolated_required_coverage design.test_maas_book_language.MaasBookLanguageRegistryTest.test_milp_solver_proves_maximum_set_under_caps_and_coverage design.test_maas_book_language.MaasBookLanguageRegistryTest.test_milp_solver_falls_back_to_cardinality_when_joint_coverage_is_infeasible design.test_maas_book_language.MaasBookLanguageRegistryTest.test_milp_capacity_bands_require_coverage_without_blocking_absorption -v 2
```

Observed: `Ran 6 tests ... OK`, exit code `0`.

Relevant full module:

```powershell
C:\Python313\python.exe manage.py test design.test_maas_book_language -v 1
```

Observed: `Found 66 test(s)`, `Ran 66 tests ... OK`, exit code `0`.

Static verification:

```powershell
C:\Python313\python.exe -m py_compile ARR/backend/design/maas/book_language/portfolio_constraint_solver.py ARR/backend/design/test_maas_book_language.py
git diff --check -- ARR/backend/design/maas/book_language/portfolio_constraint_solver.py ARR/backend/design/test_maas_book_language.py
```

Observed: both exited `0`; diff check emitted only working-copy LF-to-CRLF
notices.

### Files and remaining minor gap

- Modified `portfolio_constraint_solver.py` and
  `test_maas_book_language.py`; no legal optimizer or export test file was
  touched.
- The reviewer-requested `summary_only` through final board/artifact Task 2
  hash integration was not added in this constrained solver round. The final
  board/artifact assembly remains embedded in the monolithic portfolio
  benchmark, so a truthful focused integration would require either a large
  full-benchmark fixture or production extraction/refactoring unrelated to the
  fallback fix. Existing Task 2 real-render identity and Task 3 summary/eager
  parity tests remain the adjacent boundary coverage.
- After the recorded `66/66` module pass, a concurrent agent added
  `test_shared_compatibility_analysis_single_flights_same_pair` and its imports
  to the shared dirty test file. A fresh run then found 67 tests and failed
  only that new unrelated concurrency regression (`call_count 8`, expected
  `1`); the six solver/selector tests still passed `6/6`. Per parent
  coordination, that concurrent hunk is preserved in the worktree and excluded
  exactly from this commit.
