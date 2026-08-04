# MASS flow checkpoint: r69-r70 selection supply architecture

Date: 2026-08-04 (Asia/Seoul)

## Goal

Produce five law-compliant, competition-grade, visibly distinct MASS alternatives. Elevation work remains out of scope. Stair-step massing is one valid language, not the only output phenotype.

## Runs

### r69

- Result: `1/5`
- Runtime: about 315 seconds
- Final PNG: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r69/maas-book-neighborhood-5.png`
- The first source-role binder fix executed: repaired source materialization increased from `0` in r68 to `1`.
- The benchmark caller did not pass successful-author accounting, so empty author responses still consumed the legacy `5/5` quota.
- Final-VLM candidate count increased from four to five, but only one hard-passed.

### r70

- Result: `1/5`
- Runtime: about 349 seconds
- Final PNG: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r70/maas-book-neighborhood-5.png`
- Selected mass changed from r69 `shift` at FAR `113/126%` to `expand` at FAR `88/126%`.
- Replenishment stopped on `cycle_budget_exhausted`, not legacy author quota. The caller wiring therefore executed.
- Reconstructed successful authored supply count: `0 -> 0 -> 1 -> 1 -> 2` over five cycles.
- Final-VLM supply reached six candidates across four nominal LLM families.
- Two candidates hard-passed final VLM, but silhouette distance was `0.0929`, below the distinctness minimum `0.1`; only one was retained.
- Every final-VLM candidate was classified as `stepped`. Effective phenotype diversity remained one.
- Typed repairs improved to `3 source-role bound / 3 materialized`, but none reached a second final VLM because canonical reprojection or reachable-origin authority still failed.

## Confirmed architecture bottleneck

The limiting factor is no longer one statutory gate or quota arithmetic. The pipeline couples these concerns inside each replenishment cycle:

1. authored/materialized supply production;
2. strict downstream and final-VLM adjudication;
3. portfolio diversity selection.

This produces too few selectable candidates and feeds selector rejection back to authoring too late. Numerical family labels increased, but all candidates collapsed to one stepped phenotype.

## Required direction

Use a bounded legal-reservoir-first flow:

1. Collect exact, clean, directly statutory-law/parking-passing candidates before paid final VLM.
2. Deduplicate by canonical program and geometry identity.
3. Index candidates by measured phenotype, BOOK graph, scope, ground strategy, roof/chassis, and void strategy.
4. Select a target-scaled diverse batch from missing descriptor cells.
5. Run final VLM and typed repair on the batch.
6. Revalidate law, parking, capacity, and semantic authority after repair.
7. Feed selector exclusions such as `silhouette_near_duplicate` directly into the next reservoir supply request.

Statutory law, parking, capacity, and post-repair legal validation must not be weakened. The purpose is to move diversity selection earlier, where enough legal supply exists, not to promote failed candidates.

## Code state

- `0621f10 fix: preserve repaired mass supply through selection`
- `1ec3026 fix: preserve repaired semantic authority`
- Focused regressions passed: three caller-quota tests and four semantic-authority tests.
- The r70 caller-quota wiring in `design/maas/book_language/portfolio_benchmark.py` remains uncommitted because that file contained substantial pre-existing dirty changes; do not stage the whole file as an isolated quota commit.

