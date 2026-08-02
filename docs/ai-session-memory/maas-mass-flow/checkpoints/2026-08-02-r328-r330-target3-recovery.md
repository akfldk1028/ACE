# r328-r330 Progressive Target-3 Recovery - 2026-08-02 KST

## Fixed Runtime Exceptions

- r328 stopped after about 1132 seconds because `portfolio_started_at` had
  been inserted in `_certified_projected_visual_artifact` instead of
  `run_book_program_portfolios`.
- r329 stopped after about 1127 seconds because the new witness path called
  `_Candidate.program_hash()`, but `_Candidate` is an analysis dataclass and
  has no such method.
- Both faults now have focused regression coverage. The focused suite passed:
  `38 passed, 214 deselected`.

## r330 Exact Run

```text
PNU: 1168011800104170004
program: neighborhood
command: python manage.py benchmark_maas_book_program_portfolios
  --pnu 1168011800104170004
  --program neighborhood
  --progressive-target 3
  --output-dir .../book-program-portfolios-r330-progressive-target3-witness-fixed
elapsed: 1136.9 seconds
```

## Result

- run state: `completed_with_failed_gate`
- selection pool: `2`
- selected: `0/3`
- required/selected scopes: `3/0`
- final exact portfolio VLM: not evaluated because no strict portfolio of 3
  reached that stage
- official board is intentionally empty
- nonpublishable witness board contains two rejected masses

Witness files:

```text
docs/playwright/design-route-live-verify/
  book-program-portfolios-r330-progressive-target3-witness-fixed/
    maas-book-neighborhood-3-witness.png
    maas-book-neighborhood-3-witness.json
```

Witness SHA-256:
`483157aaa8b6f4276cef1b0ae574c48785b33801f6baa1d79f302a76a00d93a9`

The two witness forms are still low bar/step variants and are not the target
competition-grade diversity.

## Measured Bottleneck

The roughly 19-minute latency is not primarily provider latency. Cached LLM
authorship produced 31 active seeds, but the benchmark repeatedly recompiles
the same ASTs across capacity alternatives and legal floor sections. The main
loss reasons observed in logs are:

- `whole_solid_affine_fit_infeasible`
- `tiny_edge` after capacity replay
- `unrequested_legal_step_collapse`
- `unrequested_visible_step_fallback`
- role/site coverage failures

The legal floor field itself is feasible: four usable floors with legal
section capacities approximately `102.931, 102.931, 74.989, 51.471 m2` and
feasible total `332.322 m2`. The defect is in preserving an authored solid
while fitting those nonuniform legal sections, not in a lack of statutory
capacity.

## Hard Next Step

Do not rerun the same full target-3 benchmark. First split the deployment path:

1. Persist compiled/legal candidate artifacts by `(program_hash,
   floor_capacity_plan_hash, capacity_target)`.
2. Reuse those artifacts for selector, final VLM, and renderer refreshes.
3. Replace repeated whole-solid affine attempts with typed floorwise legal-fit
   repair that preserves the authored silhouette and never invents steps.
4. Run target-3 again only after a focused cache test proves a selection/render
   refresh does not regenerate all candidates.

This remains an agent pipeline:
LLM Architect -> MASS Geometry -> Law/Legal Fit -> Parking -> VLM Critic ->
Selector -> exact VLM gate -> render. Elevation remains out of scope.
