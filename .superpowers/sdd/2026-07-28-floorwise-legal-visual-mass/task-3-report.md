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
