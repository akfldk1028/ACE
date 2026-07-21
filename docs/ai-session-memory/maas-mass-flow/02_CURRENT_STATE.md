# Current Verified State — r196 completed, r197 resource-guarded

Generated 2026-07-22 KST.

## One-MASS deploy fast path

- `design.maas.single_execution.execute_single_mass` is now the canonical
  request-time boundary. It reuses the only GeometryProgram compiler, geometry
  GATE, four-view renderer and execution passport; it does not run portfolio
  search.
- Public API: `POST /design/maas/single-executions/`; the response provides
  preview, passport and manifest URLs. CLI: `execute_maas_single_mass` accepts
  a built-in shape, a JSON AST, or an exact archived run/index.
- Actual r196 MASS 01 replay: geometry hash
  `1d15bdc91ac3544502d5c3677d1b527c11d69e189cfe9bef2713a40ccb314c94`,
  one connected component, 40 triangles, geometry GATE pass, 38.426 ms local
  pipeline time. Live HTTP POST repeated the same AST in 41.087 ms.
- The generated causal passport has 14 stages, 23 nodes, 28 edges and 15
  active edges terminating at one `result:mass`. Law, parking, VLM and selector
  remain honestly `not_evaluated`; therefore the MASS is `geometry_ready` while
  full-flow status remains `in_progress`.
- Direct review of the new four-view PNG found one coherent connected solid,
  not the previous painter-order fragment artifact. Its leaning/cut silhouette
  is inherited from the exact r196 program; this single replay does not make
  the overall r196 portfolio visually accepted.

## Honest outcome

- Latest completed run: `book-program-portfolios-r196-streaming-qd-one-cycle`.
- Result: `15/20 · FAIL`; downstream site/legal/parking preflight passes.
- Failures: selected count below 20, one available BOOK principle kind missing,
  and repeated roof archetype above 30 percent.
- Duration 1093.214 seconds; run-local graph 13.002 MB.
- r194 is the latest paid board audit: FAIL, 9 visible families, dominant share
  0.40, response `resp_0c1db4c3d006705b006a5f770e85448199a522e34ada21b68d`.
- r195 was stopped during initial candidate generation and r197 during cycle 2
  after free physical memory fell below 1 GB. Both are state-only failures with
  no final MASS/PNG. r197 retained the cycle-1 checkpoint of 15 selected.
- r182 remains the latest numeric 20/20 baseline and was not VLM-approved.

## Memory/search correction

- Candidate generation now uses a streaming MAP-Elites archive owned by
  `quality_diversity_archive.py` instead of waiting for 384 heavy candidates.
- r196 measured peak candidate count 193, 197 compactions and 1116 released
  candidates. Process memory stabilized near 600–740 MB instead of r195's
  early 791 MB spike. The retained source now batches compaction at a bounded
  `max_archive_size + 24` margin to reduce compaction overhead.
- GeometryProgram, graph notes and graph snapshot are immutable candidate
  evidence and are shared between SourceMass and Feature instead of deep-copied.
- No geometry/legal/parking/capacity/silhouette threshold was relaxed.
- Full seven-page closure could not be completed while other workstation apps
  left only 0.26 GB free. Continue only when the machine has a stable memory
  reserve; do not terminate user applications automatically.

## Geometry/search findings

- r196 final supply: 90 capacity-target hard passes from a raw pool of 145;
  MILP maximum remains 15 for that one-page run.
- Selected plans: articulated 7, curved/complex 7, quadrilateral 1. Ground:
  court threshold 1, entry notch 9, lifted threshold 5.
- Eight form-bank pages contain 13 typed triangular-profile programs, but the
  old program projection often changed their measured plan via split/notch.
- Current source now chooses footprint-preserving `lift` for triangular,
  trapezoidal and kite profiles when topology permits. Unit compilation passes,
  but this change has not yet completed a full benchmark run; do not claim a
  generated triangular portfolio result yet.
- Selection diagnostics now records plan-family supply and selected counts at
  the exact capacity-target hard-pass universe.

## VLM feedback boundary

- Exactly three paid board calls were made in the r191-r194 loop; no new paid
  call was spent on the visually similar r196 board.
- Post-run paid audit descriptors now pass through the same typed feedback
  mapper as live candidates. Candidate actions become exact geometry-family and
  chassis counts before entering the graph; free-form prose never becomes an
  operator.
- r194 graph memory was copied into r197's run-owned transfer graph. Historical
  r194 evidence was not modified. The transfer was resource-safe but did not
  improve cycle 1 beyond 15 candidates.

## Render and frontend verification

- Direct r196 PNG review: no painter-order floating fragments; all 15 are
  visible, but the board remains too box/step dominated for acceptance.
- URL: `http://127.0.0.1:5175/design/language`.
- After r197 failed, the frontend correctly leaves r197 as a 0-MASS state-only
  timeline entry and selects r196 as the latest replayable portfolio.
- Browser pass: one graph; 15 executed nodes and 15 loaded images; 42 related
  nodes and 40 active edges after MASS click; 5 retrieved ArchDaily nodes;
  6 exact memory nodes; 0 active VLM references for r196; 0 BOOK rasters; 0 JS
  or page errors; one Selected MASS Path result.
- The r196 header/footer truthfully say VLM not evaluated/no claim.

## Site/legal/elevation boundary

- PNU `1168011800104170004`; parcel 264.126 m²; BCR 60%; FAR 250%; adjacent
  setback 0.5 m; landscaping minimum 15%; generation host 102.931 m².
- This is massing preflight, not approval-grade permit verification.
- Elevation indexed-mesh handoff exists, but final elevation remains blocked on
  an accepted MASS and the mesh-to-condition-pack adapter.

## Research alignment

- `clone/d4descent` optimizer/rewrite/cleanup code was inspected. MAAS uses the
  staged discrete rewrite/selection/cleanup principle but does not implement
  equivalent differentiable continuous optimization; do not claim paper parity.

## Evidence

- `docs/playwright/design-route-live-verify/book-program-portfolios-r196-streaming-qd-one-cycle/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r196-streaming-qd-one-cycle/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r196-streaming-qd-one-cycle/maas-geometry-mutation-outcome-graph.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r197-full-seven-page-vlm-memory/maas-run-state.json`
- `docs/playwright/design-route-live-verify/frontend-live/r196-after-r197-resource-guard/verify.json`
- `docs/playwright/design-route-live-verify/frontend-live/r196-after-r197-resource-guard/full-graph.png`
- `docs/ai-session-memory/maas-service-cache/single-executions/r196-mass-01-fast/execution.json`
- `docs/ai-session-memory/maas-service-cache/single-executions/r196-mass-01-fast/mass.png`
- `docs/ai-session-memory/maas-service-cache/single-executions/r196-mass-01-fast/mass.png.passport.json`
