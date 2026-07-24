# Current Verified State — r211-r216 multi-MASS archive with elevations

Generated 2026-07-24 KST.

## 2026-07-24 r227 UnitBox/BOOK fresh batch and MASS-bound elevation ALT

- `r227-unitbox-book-clean-01..10` are ten fresh synthesis executions, not
  portfolio replay. Every program descends from one normalized `1/1 UnitBox`;
  affine states use explicit 4x4 matrices and topology-changing BOOK operations
  remain recursive Solid-to-Solid nodes.
- The ten program hashes and ten geometry hashes are unique both within r227
  and against the pre-existing single-execution archive. The generated form
  families are curved bar, open courtyard, radial cross, stepped setback,
  tapered/leaning, diagonal cut, face attachment, profiled span, split bridge
  and nested offset.
- MASS generation itself is deterministic compiler execution. It does not
  silently call a VLM or image model. This separation is intentional:
  generation -> compiler/GATE/render -> deterministic elevation condition pack
  -> optional image proposal -> optional bounded MASS VLM critic.
- All ten executions produced their exact MASS PNG plus six deterministic
  front/right/back/left/top/axon projections. The projection cameras derive
  orthonormal bases and 4x4 view matrices from semantic direction/up vectors;
  pasted decimal camera bases are forbidden.
- The second-stage elevation image batch made exactly ten paid HTTP attempts,
  zero retries and at most one attempt per MASS. `gpt-image-2` quality review:
  6 passed, 3 `needs_review`, 1 failed. Passed post-pilot outputs use an API edit
  mask plus deterministic post-composite silhouette lock; generated pixels
  cannot change the MASS exterior.
- MASS 03 failed honestly because the provider rejected the unsupported
  `input_fidelity` parameter. It was not retried. MASS 01/02 are retained but
  inactive as pre-lock pilots, and MASS 05 remains `needs_review` because its
  top view reads as facade grid rather than roof evidence.
- The same single graph now traces `result:mass -> elevation:mesh_handoff ->
  elevation:condition_pack -> elevation:image_agent -> elevation:proposal`.
  Inactive/failed proposal edges remain at activation 0. The bottom rail remains
  MASS-only; technical elevations and ALT 01 are children of the selected MASS
  in the graph/right evidence panel.
- Browser verification passed after restarting a stale Django process:
  MASS 10 ALT endpoint returned `200 image/png` (498,051 bytes); the UI loaded
  its 900x680 MASS, six 720x720 technical views and one 1024x1024 ALT. Clicking
  MASS 09 changed both the MASS and proposal URLs to execution 09. There were
  zero failed browser responses, console errors or Vite overlays.
- One separate bounded paid MASS critic was run only for MASS 10 with one
  ArchDaily reference and zero retries. `gpt-5.4-mini` response
  `resp_0988715f6043f7e1006a6322e0f02081988bc3e6cb32764034` used the exact MASS
  PNG plus Seattle Central Library / OMA + LMN. It returned `live_scored` but
  hard-failed program fit: coherent silhouette, but weak public threshold,
  program relation and meaningful void. Usage was 21,902 tokens.
- Law/parking specialist calls are present, but r227 has `PNU_UNRESOLVED`, no
  parcel placement matrix, no site/capacity proof and no approval-grade parking
  result. Therefore law, parking, selector and final status remain
  `needs_evidence`. These are architectural form studies, not code-compliant or
  phenomenon-design-complete buildings.

Evidence:

- `docs/playwright/design-route-live-verify/r227-unitbox-book-clean-contact-sheet.png`
- `docs/playwright/design-route-live-verify/r227-elevation-proposals-05-10.png`
- `docs/playwright/design-route-live-verify/r227-frontend-final.png`
- `docs/playwright/design-route-live-verify/r227-frontend-mass09.png`
- `docs/playwright/design-route-live-verify/r227-frontend-vlm-live.png`
- `docs/ai-session-memory/maas-service-cache/single-executions/r227-unitbox-book-clean.batch.json`

## 2026-07-24 r222 fresh synthesis versus exact replay

- r219 was an exact r160 AST replay, not a newly synthesized design. Equal
  geometry hashes were correct compiler behavior; the UI/action label was
  wrong.
- Execution provenance is now explicit and lossless:
  `execution_mode=exact_replay` records source run/index, while
  `execution_mode=fresh_synthesis` means an independently authored AST.
- Current reviewed fresh MASS:
  `single-execution:r222-fresh-book-offset-courtyard`.
  Program hash `6c784f4f...16590`; geometry hash `31250e53...5c439`.
- A clean `/design/language` load now selects r222 by default. Selection
  prioritizes the newest replayable `fresh_synthesis` over an older site-bound
  portfolio, while a newer exact replay does not take over the "new design"
  slot. The bottom 16-card rail is historical evidence; only r222 was newly
  synthesized in this correction cycle.
- Executed operators are `box`, `scale`, `book_base_volume`,
  `nested_related` (BOOK Offset lowering), `notch`, `cantilever`,
  `split_wing`, `join_related`.
- The archive adapter resolves `book_scope=1/1`,
  `book_orientation=long_axis`,
  `book_principle_id=book:operative:offset`. The frontend full graph therefore
  connects the real BOOK node to the selected execution rather than showing
  an untyped or invented path.
- Browser status: r222 appears in the chronological timeline and 15-item MASS
  rail, displays `NEW SYNTHESIS`, loads its generated MASS/elevation images,
  and emits zero console errors.
- Truthful limit: r222 is geometry-ready but site-unresolved and
  `needs_evidence`; it is not yet a parcel-, FAR-, parking- or VLM-approved
  final design.

## 2026-07-24 r219 render/site-context regression correction

- The “flipped, generic object” regression was presentation and replay
  context, not a changed geometry hash. Positive isometric pitch combined with
  inverted screen Y projected higher Z downward; face-centroid painter ordering
  also let rear faces overwrite concave/crossing envelopes.
- `geometry_language/render.py` now uses `-28°` isometric pitch and the shared
  per-pixel depth rasterizer. Higher architectural points project upward.
- Legacy portfolio rows that retained only `card_index` now recover their exact
  card crop from the immutable board. r160 MASS 01 is materializable again with
  its recorded parcel/access-line presentation.
- HTTP and CLI replay now share `single_execution/replay.py`, preserving
  evaluated source-stage evidence.
- PNU alone is not placement proof. Single runs are `site_bound` only with PNU,
  parcel geometry and an explicit local-to-parcel 4x4 matrix. PNU-only replays
  are `source_gate_only` and cannot replace the default site-bound portfolio.
- The frontend defaults to the newest site-bound portfolio (`r196` currently)
  and its bottom rail contains its 15 architectural MASS cards. Diagnostic
  executions remain in the lossless timeline.
- Fresh `r219-site-evidence-upright-render` preserves r160 MASS 01 geometry hash
  `8ff66faf...d702`. Geometry, source site gate, law, parking, program fit,
  Neo4j and specialist collaboration passed. Capacity failed because the
  legacy artifact has no `capacityAlternative`; VLM was not run. Truthful
  status: `in_progress`, not accepted.
- Browser: HTTP 200, 15 portfolio cards, 0 broken images, 0 console/page
  errors, no Vite overlay.

## r218c BOOK-to-agent full-flow audit and stage synchronization

- Replayed selected MASS 01 from
  `book-program-portfolios-r160-single-program-relation-live-neighborhood`
  through the canonical one-MASS execution boundary as
  `r218c-flow-stage-sync-audit`.
- The persisted program has exactly one `1/1 UnitBox`, two `matrix4` nodes,
  three active BOOK projection nodes (`fracture`) and one active use/program
  projection node. Program and geometry hashes match across the execution
  manifest, passport, specialist handoffs and elevation condition pack.
- Geometry is one closed, watertight, manifold component with 40 vertices and
  80 triangles. Geometry GATE has zero issues and elevationAgent generated all
  six front/right/back/left/top/axon condition views.
- Fixed a causal-graph split found by this audit: law, parking and selector
  specialists were executing while their canonical flow nodes remained
  `not_evaluated`. Materialized specialist statuses now project back onto the
  same `flow:law`, `flow:parking` and `flow:selector` nodes. `needs_evidence`
  and `failed` activate their actual evidence path without becoming PASS.
- Live Neo4j and the law-domain service were reached. PNU remains unresolved,
  so law, parking, review and selector correctly remain `needs_evidence`.
- One bounded paid VLM call used one reference and zero retries. Model
  `gpt-5.4-mini`, response
  `resp_026194fa2be23e18006a62dfdb37a0819b99d8ab64c1ae261f`, rejected the MASS
  for a blank front, weak public threshold/void, program mismatch and
  fragmented continuity. The exact-byte r218c replay reused that result with
  `cache_hit=true`; it did not spend a second live call.
- Browser verification shows 13 unique geometry cards despite r218b/r218c
  sharing a geometry hash. Selecting r218c exposes BOOK, program, legal-agent,
  selector, render and elevation nodes in one graph; all images load and the
  VLM cache-hit failure remains visible.
- MASS-focused backend regression is 223/223 and TypeScript passes. Repository
  full test remains red: frontend ran 415 tests with 71 existing failures in
  ChatBox/SearchInput/Terminal/useInstallationSetup; backend discovered 770
  tests and showed multiple existing failures before the long audit process
  was stopped. Do not call the repository engineering-full-test green.

Browser evidence:

- `docs/playwright/design-route-live-verify/r218c-full-flow-stage-sync.png`
- `docs/playwright/design-route-live-verify/r218c-selected-causal-flow-stage-sync.png`

## r217 unique single-MASS thumbnail rail

- The bottom rail no longer displays the 900x680 four-view composite inside
  each card. Every single-execution card requests an immutable 436x286
  isometric-only `/thumbnail/` derived from the exact compiled MASS render.
- Single-execution run rows now expose `geometry_hash` and `thumbnail_url`.
  The rail sorts newest first and collapses identical non-empty geometry hashes
  to one representative card. The lossless execution timeline is unchanged.
- Live browser verification reduced 24 recent execution cards to 11 unique
  geometry cards. Every card contained exactly one loaded image, every source
  used `/thumbnail/`, broken images were zero, and no Vite overlay existed.
- Clicking the third unique card selected r214 and changed all six right-side
  elevation images to the r214 execution ID.
- The separate `ARR/backend/agents/elevationAgent` now records the future
  creative provider boundary: immutable MASS input, replaceable image model,
  prompt/input/output provenance and cross-view/mesh consistency gates.

Browser evidence:

- `docs/playwright/design-route-live-verify/r217-unique-single-mass-thumbnail-rail.png`

## r211-r216 distinct MASS generation and clickable archive

- Six independent geometry programs were executed: radial fan, stepped
  setback, tapered tower, diagonal slice, swept curved bar and twisted tower.
- Every program has exactly one primitive `1/1 UnitBox`; one or two explicit
  `matrix4` nodes derive the working volume before pattern, macro, modifier,
  cutting or Boolean operations. The six geometry hashes are distinct.
- Every result is geometry-ready, watertight/manifold, has zero Geometry GATE
  issues, and generated six deterministic elevation views from the exact
  indexed mesh: front, right, back, left, top and axon.
- `/design/language` now builds the bottom MASS-only rail from replayable
  single-execution runs rather than only `archive.masses` from the selected
  run. The latest 24 MASS results remain visible while one run is selected.
- Clicking r214 in browser verification moved the selected rail card, loaded
  the r214 diagonal-slice graph, and changed all six right-sidebar elevation
  URLs to r214. The page had zero broken images and no Vite error overlay.
- Final acceptance remains honestly `needs_evidence`: these diagnostic runs
  have `PNU_UNRESOLVED`, no site capacity/parking approval and no paid VLM
  critic. Geometry and elevation generation are proven; regulatory/design
  acceptance is not.

Browser evidence:

- `docs/playwright/design-route-live-verify/r216-six-distinct-mass-archive-frontend.png`
- `docs/playwright/design-route-live-verify/r215-multi-mass-elevation-archive-frontend.png`
- `docs/playwright/design-route-live-verify/r214-selected-mass-six-elevations-visible.png`

## r207 genuinely new MASS generation

- This is not an archived shape replay. A new eight-node program named
  `r207_fresh_notched_taper_cantilever` was authored and executed under
  `single-execution:r207-fresh-unitbox-notched-taper-cantilever`.
- One primitive `1/1 UnitBox` is reused by four 4x4 matrices to produce a
  notched podium, tapered vertical core and 12-degree rotated cantilever.
  Recursive `difference`, `taper` and three-input `union` compose the result.
- Freshness audit found no prior program-hash or geometry-hash collision.
  Program hash is `009ea38b...620c6`; geometry hash is
  `867fe51f...470e`.
- The actual new mesh is one closed, watertight, manifold component with
  outward normals, 200 triangles, volume `1070.793163` and bounds
  `18 x 12 x 14.5`. Geometry GATE passed with zero issues.
- `/design/language` lists r207 first in the chronological archive. Browser
  selection shows the new four-view PNG, four executed matrix glyphs, one
  causal graph, zero BOOK rasters and no error overlay.
- Final passport is still `needs_evidence`: no PNU/capacity/parking acceptance
  or VLM critic was supplied. Elevation remains three unevaluated continuation
  nodes; this run proves fresh geometry generation, not full design acceptance.

## r206 one UnitBox + two affine matrices + elevation trace

- `/design/language` now exposes one `1/1 UnitBox` Base Model and five BOOK
  derived-volume states. It renders one graph and zero BOOK raster images.
- The 18 executable reference programs lower every Box through an explicit
  UnitBox. r206 evaluates `UnitBox -> scale[5,5,16] -> lean(x += 0.2z)` and
  preserves the prior geometry hash.
- The r206 MASS is geometry-ready, watertight, manifold and one component.
  Browser proof shows the generated four-view PNG, three matrix glyphs in the
  full graph (identity + scale + lean), and two executed matrices in the
  selected path.
- Final status is still `needs_evidence`: the diagnostic has no PNU/capacity/
  parking/VLM evidence. This is not a legal or design-quality acceptance.
- Elevation continuation is visible as three pending nodes. No condition pack
  or elevation PNG exists because `elevationAgent` is not yet a mesh consumer.
- Verification: relevant backend 248/248, frontend feature tests 7/7,
  TypeScript and the standalone Vite web build pass. Full frontend remains
  336/407 with 71 legacy failures outside the MASS graph feature. The aggregate
  Electron packaging command remains red because `frontend/build/icon.ico` is
  absent after the web, main and preload bundles finish.

## r203 current-code browser execution (live law pending)

- Restarted the Vite-owned Django `:18000` process because it was running with
  `--noreload` and initially emitted an obsolete passport without specialist
  evidence. The repeated browser button execution now uses current source.
- Browser-created execution `mass-20260722T060646699517Z` is geometry-ready in
  1.899 s: one component, 108 triangles, watertight/manifold, zero geometry
  GATE issues, program hash `b1a77c19c816f324d2abf0eabf1e613e96b5d0e693ae2e4ab749ad6fb4f19472`
  and geometry hash `285a685cc961ecbd03249ad4a74805a67980597052bfbf9dfa94c6a067fbb26a`.
- The same passport/full graph contains six specialist nodes, five completed
  handoff edges and one bounded law-source attempt. The browser produced a new
  chronological run, loaded the generated MASS PNG, requested zero BOOK
  rasters, and recorded zero console/page/HTTP errors.
- Final status is `needs_evidence`: Neo4j `:7687` and law-domain-agents `:8011`
  are not listening, the built-in diagnostic shape has no PNU, and VLM is
  `not_evaluated`. No paid request was spent on this non-acceptable diagnostic.
- The MASS-focused regression group is green: backend 227/227, frontend 6/6,
  TypeScript and Django checks pass. Repository-wide engineering remains red:
  backend `design` ran 754 tests with 19 failures and 2 errors in 825.052 s;
  frontend ran 406 tests with 334 pass, 71 fail and 1 skipped. A post-suite VLM
  audit `NameError` fix passes its focused 17/17 regression.

## r201 multi-agent acceptance wiring (offline verified, live law pending)

- `execute_single_mass` now creates one immutable identity from execution ID,
  program hash, geometry hash and PNU, then runs geometry, law graph, parking,
  review and selector specialists in order.
- The existing MASS passport and activation graph now persist agent evidence,
  five handoffs, the bounded :8011 law search attempt and resolved Neo4j article
  IDs. No second graph or BOOK raster lane was added.
- A disconnected Neo4j or law-domain service yields `needs_evidence`. Geometry
  compilation and the four-view PNG remain available for diagnosis, but final
  acceptance is blocked.
- VLM program resolution now reads nested `metadata.program_projection` before
  family/generic fallback. The limit is three references with program, similar
  and counterfactual roles plus exact local-image SHA-256 deduplication.
- Verified offline: backend collaboration/single-execution/reference focused
  tests 18/18; frontend specialist sidebar 3/3; TypeScript type-check PASS.
- Materialized diagnostic execution `r201-offline-agent-path-verified`:
  geometry-ready, zero geometry GATE issues, 1.887 s in-process total,
  specialist handoffs 5/5 visible, final `needs_evidence` because 7687 and 8011
  were not listening. Browser verification found all six specialist columns,
  five rendered handoff edges, one selector-decision edge and zero console/page
  errors.
- Live Neo4j/:8011 and one bounded paid VLM run have not yet been executed for
  this new contract. Therefore current new-contract status is
  `needs_evidence`, not accepted.

## Historical bounded paid single-MASS acceptance (r200, pre-r201 contract)

- Immutable execution `mass-20260722T040843366927Z` replays r196 MASS 04.
  Program hash `e98802e47b7570b63719cd7ed58eb54b066deefce262e75510b43d6914d32f30`;
  geometry hash `1f59803258b651435af06b97883d483c5d79c494026e1eb6b2437b5853ad9436`.
- Geometry is one watertight/manifold component, 96 triangles. Base, BOOK,
  recursive geometry, program, site, capacity, law, parking, program fit,
  compiler, geometry GATE, render and selector all passed before VLM.
- Paid VLM used the generated four-view PNG plus exactly two massing references:
  `8 House / BIG` and `BIG Releases First Photographs of The Vancouver House and
  Telus Sky in Canada`. The endpoint has zero retries and a hard ceiling of
  three HTTP attempts including cold reference audits; one candidate call is
  confirmed live (`cache_hit=false`).
- `gpt-5.4-mini` response
  `resp_09c96346deac86f1006a604298bb9081988820c96f5ca84354` returned program-fit
  PASS. Final passport: `status=accepted`, `full_flow_complete=true`,
  `final_hard_pass=true`. Recorded usage is 26,250 input + 1,569 output = 27,819
  tokens. This exposes the next cost issue: prompt/graph context size, not image count.
- Browser verification on `/design/language`: one graph, 258 rendered nodes,
  141 active edges, two image-backed VLM reference nodes, one image-backed final
  MASS node, no Vite overlay. The sidebar exposes the bounded paid action and
  recorded 27,819-token usage.

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

## One-MASS frontend integration and full-test truth (r199)

- `/design/language` now executes the selected archived MASS through
  `POST /design/maas/single-executions/`, appends the result to the same
  chronological run timeline, and reloads the same Full Graph with exactly one
  executed MASS node, its actual four-view PNG and its execution passport.
- This is not a second graph or a BOOK-image graph. BOOK remains typed language
  authority; generated MASS PNGs are the visual result. Reference/VLM images
  enter only when they were actual model inputs.
- Browser r199 passed: HTTP 200, one graph, original 15/15 MASS PNGs loaded,
  new run `single-execution:mass-20260722T004049081375Z`, one generated MASS,
  one loaded gallery PNG, one passport, 129 related/active selected-path edges,
  zero BOOK raster requests, zero console errors and zero page errors.
- The replayed passport preserves evaluated r196 downstream evidence: site,
  capacity, law, parking, program fit, compiler, geometry GATE, render and
  selector passed. Geometry is one watertight/manifold component with 40
  triangles. VLM remains `not_evaluated`, so `full_flow_complete=false` and
  `final_hard_pass=false`; no paid request was made in this verification.
- Mandatory full test was actually run. Frontend build and TypeScript passed;
  focused MASS UI/API tests passed 3/3; backend focused tests passed 26/26;
  Django check passed; browser E2E passed. The repository-wide suites are not
  green: backend `design` ran 742 tests with 22 failures and 2 errors, while
  frontend Vitest ran 403 tests with 331 passed, 71 failed and 1 pending.
  Therefore the honest overall engineering full-test state is **FAIL**, not
  complete. See `07_FULL_TEST_CONTRACT.md` and `04_VALIDATION_GAPS.md`.

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

- `docs/ai-session-memory/maas-service-cache/single-executions/mass-20260722T040843366927Z/mass.png`
- `docs/ai-session-memory/maas-service-cache/single-executions/mass-20260722T040843366927Z/mass.png.passport.json`
- `docs/playwright/design-route-live-verify/r200-bounded-single-mass-vlm-selected-path-1920.png`
- `docs/playwright/design-route-live-verify/r200-bounded-single-mass-vlm-vlm-path-1920.png`

- `docs/playwright/design-route-live-verify/book-program-portfolios-r196-streaming-qd-one-cycle/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r196-streaming-qd-one-cycle/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r196-streaming-qd-one-cycle/maas-geometry-mutation-outcome-graph.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r197-full-seven-page-vlm-memory/maas-run-state.json`
- `docs/playwright/design-route-live-verify/frontend-live/r196-after-r197-resource-guard/verify.json`
- `docs/playwright/design-route-live-verify/frontend-live/r196-after-r197-resource-guard/full-graph.png`
- `docs/ai-session-memory/maas-service-cache/single-executions/r196-mass-01-fast/execution.json`
- `docs/ai-session-memory/maas-service-cache/single-executions/r196-mass-01-fast/mass.png`
- `docs/ai-session-memory/maas-service-cache/single-executions/r196-mass-01-fast/mass.png.passport.json`
- `docs/ai-session-memory/maas-service-cache/single-executions/mass-20260722T004049081375Z/execution.json`
- `docs/playwright/design-route-live-verify/frontend-live/single-execution-full-test-r199/verify.json`
- `docs/playwright/design-route-live-verify/frontend-live/single-execution-full-test-r199/single-execution-full-graph.png`
