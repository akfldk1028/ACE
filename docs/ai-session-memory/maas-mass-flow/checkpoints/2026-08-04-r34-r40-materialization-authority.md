# MAAS MASS Flow Checkpoint: r34-r40 Materialization Authority

Date: 2026-08-04

Status: authoritative chronological checkpoint for the r34-r40 debugging
sequence. Run facts and commit IDs below are verified facts supplied for this
checkpoint. Current fixes and next-run items are explicitly distinguished.

## Project invariants

- The LLM authors the full typed BOOK graph.
- Matrix4 owns principal placement.
- Typed CSG owns the nonlinear geometry graph.
- Statutory law is hard authority.
- Final VLM is hard authority for genuine provider program-fit and provider
  blocking verdicts. Competition score floors and locally derived diagnostics
  remain ranking and repair objectives.
- Facade development happens later and is not MASS geometry authority.
- Capacity and portfolio-composition objectives do not replace statutory law
  or parking authority.
- The exact authored and certified geometry remains render, VLM, floor,
  capacity, law, witness, and archive authority.
- No convex hull, synthetic capacity plate, largest-polygon substitution,
  loft, prism, or other fallback may replace the exact certified geometry.

## Commit chronology

Verified commits:

- `bf00162`: dynamic replenishment.
- `38185f7`: stale cache quota.
- `9362224`: canonical program authority and cycle sizing.
- `58ebab4`: development counter.
- `8cd0f9c`: separate logical author and repair budgets.

The exact association of each commit with an individual r34-r40 run is not
restated beyond the supplied descriptions.

## r34-r36 debugging foundation

Verified fixes represented by the commit sequence above:

- Replenishment became dynamic rather than consuming one undifferentiated
  generation budget.
- Stale cache usage stopped consuming or misreporting live quota authority.
- Canonical program authority was carried through materialization, and cycle
  sizing was separated from run-global exact budget accounting.
- Development counting was corrected.
- Logical author calls and repair calls received separate budget accounting.

Pending:

- Exact per-run r34, r35, and r36 funnel counts and PNG paths were not supplied
  for this checkpoint.

## r37

Verified funnel:

- Legal archive records: 11.
- Initial program hard passes: 2.
- BASE VLM approved: 2.
- Released parent count: 1.
- Descendants: 2.
- Routed to final VLM: 1.
- Final VLM hard passes: 0.
- Selected: 0.

Verified root cause and correction:

- Target-deficit-aware sizing computed a fair per-cycle exact compile limit.
- `_run_replenishment_cycle_with_compile_authority` overwrote that value with
  run-global remaining budget.
- The regression shape computed `4` but delivered `18` to the cycle.
- The fix changed overwrite semantics to cap semantics: preserve `4` when the
  global remainder is `18`, but cap `24` to `18`.
- Global usage accounting, exhaustion authority, and later-cycle reservation
  remain separate from the cycle allocation.

PNG:

- Pending: no r37 PNG path was supplied.

## r38

Verified result:

- Selection reached 1 candidate.
- The run then crashed at witness generation.

Verified PNG:

- `D:/Data/25_ACE/docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r38/maas-book-neighborhood-5.png`

Interpretation:

- The funnel reached nonempty selection, so the terminal failure was witness
  handling rather than an empty final selection pool.

## r39

Verified funnel:

- Attempts: 42.
- Materialized: 13.
- Clean: 11.
- Program hard passes: 3.
- BASE VLM approved: 2.
- Released parent count: 1.
- Descendants: 2.
- Routed to final VLM: 1.
- Final VLM hard passes: 0.
- Typed repair materialized: 1.
- Typed repair clean: 1.
- Typed repair program hard passes: 0.
- Selected: 0.
- Legal-fit failures caused by rounding: 6.

Verified diagnosis:

- The typed repair path successfully produced materialized and clean geometry,
  but program authority rejected that repaired result before selection.
- Six legal-fit failures were precision/rounding failures rather than evidence
  that a synthetic replacement geometry was required.

PNG:

- Pending: no r39 PNG path was supplied.

## r40

Verified funnel:

- `target_exceeds`: 0.
- `floor_affine` terminal failures: 1.
- Attempts: 34.
- Materialized: 9.
- Authored visual authority records: 13.
- Clean: 1.
- Program hard passes: 0.
- Selected: 0.

Verified diagnosis:

- Target-exceeds rejection was no longer the active terminal cause.
- One floor-affine terminal failure remained.
- Materialization and authored visual authority were nonempty, but the funnel
  collapsed from clean 1 to program 0 before selection.

PNG:

- Pending: no r40 PNG path was supplied.

## Current uncommitted fixes

The following are present as current uncommitted fixes and are not yet verified
by an r41 run:

- Bounded final-VLM typed-edit completion.
- Certified witness filtering.
- Precision tolerance of `0.0005 m2`.
- Removal of the pre-CSG affine prerequisite.
- Aggregate MultiPolygon floor-union preservation.

Authority intent of the MultiPolygon correction:

- Preserve all disjoint exact floor components as one aggregate certified
  floor union.
- Preserve total floor area rather than selecting only one component.
- Keep program hash, geometry hash, materialization evidence, law input,
  capacity measurement, witness, render, and VLM tied to the same aggregate
  geometry.
- Do not introduce convex-hull, largest-component, plate, loft, prism, or
  synthetic fallback authority.

## Known remaining issues

- The current uncommitted fixes require an r41 run.
- The complete r41 funnel and PNG must be inspected after the run.
- Failed author-call observability is incomplete.
- Generic `book_projection` failures need more specific subreasons.
- It remains pending whether r41 reaches nonempty clean, program, final-VLM,
  and selected counts under the corrected aggregate floor authority.

## Next test-first and run step

Verified next step:

1. Run r41 with the current uncommitted fixes.
2. Inspect the full attempts -> materialized -> authored visual authority ->
   clean -> program -> BASE -> parent -> descendants -> routed -> final VLM ->
   typed repair -> selected funnel.
3. Inspect the r41 PNG and certified witness output.
4. Add failed author-call observability test-first.
5. Add generic `book_projection` subreason reporting test-first.

The aggregate MultiPolygon floor-union preservation must remain covered by a
production-shaped regression proving aggregate area and identity preservation,
deterministic component ordering, and absence of synthetic fallback.

