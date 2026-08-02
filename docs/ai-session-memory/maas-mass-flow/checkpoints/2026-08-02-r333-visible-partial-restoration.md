# r333 Visible Partial Restoration - 2026-08-02 KST

## Result

The first restored progressive target-3 run that produces a non-empty official
MASS board is:

```text
run: book-program-portfolios-r333-visible-partial-target3
PNU: 1168011800104170004
program: neighborhood
elapsed: 285.3 seconds
status: completed_with_failed_gate
selection pool: 1
selected/rendered: 1/3
selected scopes: 1/3
publishable: false
```

Official PNG:
`docs/playwright/design-route-live-verify/book-program-portfolios-r333-visible-partial-target3/maas-book-neighborhood-3.png`

Witness PNG:
`docs/playwright/design-route-live-verify/book-program-portfolios-r333-visible-partial-target3/maas-book-neighborhood-3-witness.png`

The visible candidate is still a low bar/step/notch form. It is evidence that
the supply-selection-render path is visible again, not evidence of restored
competition-grade diversity.

## Code Restored Before r333

- Progressive target-3 caps expensive exact compilation at 24 parent seeds.
- Shared-floor hard-pass reserve is now passed to progressive generation, so
  candidate generation can stop when sufficient downstream reserve exists.
- LLM-authored final ASTs no longer replay unchanged through every outer BOOK
  principle. One LLM AST receives one representative outer schedule; the
  deterministic BOOK lane keeps its broad principle exploration.
- Bounded legal pose/aspect reflow runs before CSG and preserves authored holes
  and concavities through a homogeneous affine transform.
- CSG refinement was reduced from 56 iterations to 8.
- Exact publication selection remains fail-closed, while a maximum hard-pass
  partial subset can render as an incomplete preview.
- Progressive target-3 count requirements are reachable: legacy 10-operation,
  10-language and six-scope checks are capped by the requested portfolio size.
- Incomplete progressive preview may render a final-GFA soft failure, but an
  exact 3/3 portfolio still requires hard final-mesh certification.

Focused integration tests after restoration:

```text
41 passed, 214 deselected
source/progressive focused Django tests: 16/16 pass
```

## Run Progression

- r331 was manually stopped at 638 seconds while still in candidate generation.
  This proved compile-limit alone did not remove repeated unchanged LLM AST
  evaluation.
- The repeated outer BOOK schedule was removed for final LLM ASTs.
- r332 reached final gate in 116.6 seconds with one selected candidate, then
  correctly raised `candidate_actual_gfa_stop_not_certified` because actual GFA
  was `242.357 m2` against target `265.858 m2` and the fourth floor was empty.
- r333 preserved that failure as nonpublishable preview evidence and completed
  without an exception in 285.3 seconds.

## Remaining Blocker

The visible pipeline is restored, but candidate supply is only one and the form
is still bar/step dominated. Most LLM ASTs fail one of:

- `whole_solid_affine_fit_infeasible`;
- authored silhouette distance after legal projection;
- tiny face/edge after replay;
- site coverage;
- final actual-GFA target reachability.

Do not return to repeated full runs. Next development must make legal fitting a
typed repair feedback loop for the LLM and derive/retain meaningful BaseVolume
scope from the authored UnitBox/Matrix4 AST. Then target-3 must reach three
certified, mesh-cluster-distinct candidates before target-10 or target-20.
