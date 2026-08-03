# r334 Bounded Center and VLM Budget - 2026-08-03 KST

## Objective

Restore a diverse, lawful MASS supply before elevation work. The pipeline
remains UnitBox/Matrix4 BaseVolume -> LLM GeometryProgram/AST -> BOOK/typed CSG
-> legal/floor/GFA/parking -> exact render/VLM -> typed revision -> selection.
No completed building form or named-building recipe is hardcoded.

## Root-Cause Correction

`materialize_floorwise_legal_source()` already routed failed whole-solid affine
selection into floorwise Matrix4/CSG materialization. The earlier assumption
that candidates were immediately discarded before CSG was incorrect.

The bounded reflow did, however, keep every ratio/angle probe fixed at
`legal.centroid`. For a concave legal polygon whose centroid falls in a void,
all probes returned no affine candidate. `_matrix_fit_polygon_to_host()` now
keeps the requested center first and probes `host.representative_point()` only
when needed. Exact containment remains mandatory; GFA, identity, clean-mesh,
parking, and VLM gates are unchanged.

Regression coverage:

```text
test_bounded_center_reflow_handles_concave_legal_centroid_void
test_bounded_aspect_reflow_preserves_silhouette_before_csg
```

## r334 Result

```text
run: book-program-portfolios-r334-bounded-center-target3
PNU: 1168011800104170004
program: neighborhood
elapsed: 241.5 seconds
status: completed_with_failed_gate
selection pool: 1
selected/rendered: 1/3
selected scopes: 1/3
publishable: false
```

Official PNG:
`docs/playwright/design-route-live-verify/book-program-portfolios-r334-bounded-center-target3/maas-book-neighborhood-3.png`

Direct PNG review: one low stepped/notched bar remains visible; the other
portfolio slots report `NO DISTINCT HARD-PASS CANDIDATE`. This is not a
competition-grade result.

Compared with r333, logged whole-solid affine deficits fell from 51 to 38 and
authored identity collapses fell from 11 to 7. The center correction therefore
removed a real attrition source, but it did not increase final portfolio supply.

## VLM Findings

The progressive run did request live VLM internally. Its persisted completion
evidence reports:

```text
runtime_live_vlm: true
exact_vlm_hard_pass_count: 1
portfolio_vlm_audit_status: call_failed
portfolio_vlm_error: paid_provider_request_budget_exhausted:6/6
```

The lifecycle decorator recorded `live_vlm_requested: false` because it wrote
run state before the command converted `--progressive-target` into live LLM/VLM
options. Run-state tracking now treats any progressive target as an implied
live-VLM request.

The target-3 provider budget was `2 author batches + 4 VLM requests = 6`, which
left no request for the mandatory final portfolio audit. `MassRunBudget` now
declares one `portfolio_vlm_request_reserve`, making the target-3 ceiling 7.
This changes request accounting only; it does not weaken a visual gate.

## Focused Verification

```text
4 tests passed
- target-3 provider budget reserves final portfolio VLM
- progressive run-state records implied live VLM
- concave legal center reflow
- existing aspect/hole-preservation reflow
```

## Remaining Blocker and Next Step

Do not run another full target-3 immediately. r334 still logged:

```text
38 principal-frame legal-fit deficits
7 authored projection identity collapses
3 projection replay compilation failures
8 LLM-authored final hard-gate failures
```

`LegalFitDeficit` currently tells the next LLM only target/legal floor areas and
the generic reason `whole_solid_affine_fit_infeasible`. It does not identify the
failed stage, source section/aspect, legal centroid coverage, retained area, or
visual replay mismatch. The next change must add typed materialization failure
evidence and feed one bounded repair cycle. Preserve silhouette identity checks;
do not solve supply by accepting legal projection collapse or padding the board.

