# Current Verified State — r194

Generated 2026-07-21 KST.

## Honest outcome

- Current-source run: `book-program-portfolios-r194-final-triangular-court`.
- Result: `15/20 · FAIL`; run state is `completed_with_failed_gate` at
  `final_gate_and_render`.
- Downstream site/legal/parking preflight passes for all 15 selected candidates.
- Final failures: `selected_count_below_20`,
  `available_book_principle_kind_missing_from_portfolio`, and
  `repeated_roof_archetype_above_30_percent`.
- r182 remains the latest numeric 20/20 baseline and was not VLM-approved.
- Do not promote r192 or r193: both were measured experiments and their changes
  were removed from production source.

## Geometry/search findings

- Default outcome memory is now run-local. r194's graph is 13.599 MB; accidental
  loading of the 469 MB shared PNU graph is no longer the default.
- Final plan families: articulated 7, curved/complex 7, quadrilateral 1.
  No triangular/non-quadrilateral plan candidate survived into final supply.
- Ground strategies: court threshold 1, entry notch 9, lifted threshold 5.
- Roofs: curved 2, oblique 1, prismatic 1, stepped 5, voided 5, sawtooth 1.
- Chassis: attached 3, bent 1, carved 4, leaning 1, lifted 4, terraced 2.
- The selector now preserves plan-family coverage when supply exists. It cannot
  select a triangle that candidate generation/GATE did not supply.
- Courtyard/split ground semantics are classified from existing evaluated
  chassis and program relations. Upstream BOOK solids are not rebound or
  unioned after the fact.
- Local research code `clone/d4descent` was inspected at its optimizer and
  rewrite/cleanup implementations. Its useful transferable pattern is staged
  discrete structure rewrites + continuous parameter optimization + periodic
  cleanup. MAAS currently has the discrete program/GATE loop but does not yet
  implement a differentiable continuous optimizer; do not claim paper parity.

## Render integrity

- The diagnostic renderer now uses a depth buffer instead of painter ordering.
- Direct review of r191-r194 boards shows no previous false floating-fragment
  artifact. Exact mesh connectivity and raster appearance agree on this point.
- This is not a substitute for manifold, self-intersection and multi-view GATEs.

## Paid VLM truth

- Exactly three new paid board calls were made in this loop: r191, r193, r194.
  No bulk image sweep was performed.
- r194 response:
  `resp_0c1db4c3d006705b006a5f770e85448199a522e34ada21b68d`.
- Model: `gpt-5.4-mini`; cache hit false; board submitted true.
- Verdict: FAIL; 9 visible families; dominant family share 0.40.
- Reasons: family resemblance, repeated footprint, repeated roof, weak program
  language and too few candidates.
- Requested next families: courtyard, split bridge, bent linear mass, cross
  mass, terrace and carve void.
- The paid board critic is a visual/program critic, never legal authority.

## Frontend and causal graph

- URL: `http://127.0.0.1:5175/design/language`.
- Playwright verification passes with one Full Graph.
- r194 exposes 15 executed MASS nodes and 15 loaded archive images.
- Clicking a MASS activates 40 related nodes and 38 causal edges; Selected MASS
  Path remains one graph and one exact result node.
- Five retrieved ArchDaily reference nodes and four exact agent-memory nodes are
  visible. Active VLM reference count is zero for r194, which accurately means
  the post-run board critic did not consume those individual reference images.
- BOOK scan image requests and DOM nodes are both zero. BOOK contributes typed
  geometry language, not raster evidence.
- Console errors and page errors are zero.

## Site/legal boundary

- PNU `1168011800104170004`; parcel area 264.126 m².
- BCR 60%, FAR 250%, adjacent setback 0.5 m, landscaping minimum 15%.
- Generation host 102.931 m²; requested 15 m / 5 floors.
- This remains a massing preflight, not approval-grade permit verification.

## Elevation boundary

- MASS-to-elevation indexed-mesh handoff exists, but final elevation generation
  remains blocked on a passing MASS and the mesh-to-condition-pack adapter.
- Elevation must derive metric depth, normals, silhouettes and facade planes
  from the accepted GeometryProgram mesh, face by face.

## Evidence

- `docs/playwright/design-route-live-verify/book-program-portfolios-r194-final-triangular-court/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r194-final-triangular-court/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r194-final-triangular-court/maas-paid-portfolio-vlm-audit.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r194-final-triangular-court/maas-geometry-mutation-outcome-graph.json`
- `docs/playwright/design-route-live-verify/frontend-live/r194-interaction/verify.json`
- `docs/playwright/design-route-live-verify/frontend-live/r194-interaction/full-graph.png`
