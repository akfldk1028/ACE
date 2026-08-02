# r182 Restoration Code Review - 2026-08-02 KST

## User Direction

Restore the working r182 MASS supply/selection/render path first, clean existing
code while modifying it, and only then develop more ellipse, plate, triangle,
axis, void and interlocking language through LLM-authored typed ASTs. Do not
keep adding bypasses. Elevation remains later work.

## Verified Baseline

`book-program-portfolios-r182-seven-page-closure-pass` is the last verified
numeric baseline on PNU `1168011800104170004`:

- selected/rendered `20/20`;
- legal/geometry-retention/parking combined hard pass `20/20`;
- 20 seed families, 13 geometry families, 9 chassis families;
- 8 roof/section families, 6 solid phenotypes, 6 BaseVolume scopes;
- 14 BOOK operations and zero near-duplicate pairs;
- no portfolio VLM request, so it is not VLM-approved evidence.

Board:
`docs/playwright/design-route-live-verify/book-program-portfolios-r182-seven-page-closure-pass/maas-book-neighborhood-20.png`

Board SHA-256:
`D749D91F75F700954DA709CC4644E2E64EE5DD0809640F5CC5B0CAD897758BAB`

The r182 board is a restoration baseline, not the final visual target. It still
contains too many box/bar/step forms and too few elliptical plates, triangular
plates, arcs, lifted fields and interlocking continuous systems.

## Root Causes Confirmed by Sequential Review

1. Current uncommitted exact-cardinality MILP returns `selected=[]` when a
   complete target portfolio is infeasible. A viable partial hard-pass pool is
   discarded, final board VLM is skipped, and the official renderer emits a
   header-only PNG.
2. Current uncommitted floor fitting removed committed `e60e60b` legal reflow
   fallback. Every floor uses one fixed pose and rejects the complete authored
   seed when one legal section cannot fit. This biases survival toward centered
   bar/prismatic/stepped forms.
3. Current legal CSG fitting can perform 12 containment probes plus 56 Shapely
   intersection refinements per floor, followed by visual projection, profiled
   clipping, loft fallback and replay compilation. This is the direct CPU
   source of the approximately 19-minute target-3 runs.
4. Progressive target-3 declares compile limit 24 but the pipeline never
   consumes it. Up to 31 authored seeds continue into expensive exact work.
5. Candidate early stop is forced to zero and replenishment reruns the complete
   generation/legal pipeline. The 18-minute reserve cutoff explains the
   observed 18-19 minute termination.
6. Target-3 final completion still requires ten BOOK operations, which is
   impossible for a three-candidate portfolio.
7. Capacity alternatives became advisory in selection, removing the r182
   capacity-spread pressure.

The strongest candidate-yield regressions are uncommitted. Commit `67cc101`
introduced the earliest committed floorwise projection cost; `e60e60b` later
restored yield with bounded pose/aspect reflow, which the current dirty tree
then removed.

## Required Restoration Order

1. Preserve publication fail-closed exact selection, but retain and render the
   maximum legal/parking/VLM hard-pass partial subset as `incomplete_preview`.
2. Keep official completion/publish failure until target count, scope,
   diversity and VLM requirements all pass.
3. Enforce progressive `compile_limit` before expensive BOOK/floorwise work.
4. Stop candidate generation once the requested hard-pass reserve is met; do
   not set early stop to zero.
5. Reintroduce bounded legal pose/aspect reflow before CSG fallback, preserving
   authored silhouette and never inventing step morphology.
6. Bound CSG refinement and cache exact results by program hash, legal floor
   plan hash and capacity target. Replenishment must reuse these artifacts.
7. Make count-dependent completion requirements reachable, for example BOOK
   operation minimum cannot exceed the selection target.
8. Re-run target-3. Only after `3/3` and visible PNG are restored proceed to
   target-10 and target-20.
9. Develop competition-grade diversity through LLM-authored UnitBox/Matrix4 +
   typed BOOK/CSG AST, with low-probability ellipse, triangle and plate seeds.
   Do not add named-building recipes or hardcoded completed forms.

## Non-Negotiable Architecture

`canonical UnitBox -> Matrix4 BaseVolume -> LLM GeometryProgram/AST -> BOOK and
typed CSG -> principal-frame legal placement/floor fit -> parking -> exact VLM
-> selector -> render`

Law remains hard. VLM remains mandatory for visual acceptance. Partial boards
are evidence, never publishable acceptance. MASS comes before elevation.
