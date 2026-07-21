# Current Verified State — r188 causal shard + paid portfolio VLM

Generated 2026-07-21 KST.

## Honest outcome

- Newest replayable run: `book-program-portfolios-r188-map-elites-compatibility-reserve`.
- Result: `16/20 · FAIL`; numeric portfolio status fails, while downstream
  site/legal/parking status passes for all 16 selected candidates.
- Six Base Model scopes and four capacity alternatives are present.
- Selected phenotypes: curved 1, oblique 1, prismatic 1, stepped 5, voided 5,
  winged 3. This is still dominated by stepped/voided bar-box lineages.
- r182 remains the latest `20/20` numeric baseline. Do not relabel r188 as
  complete and do not relabel r182 as VLM-approved.

## Search and memory architecture

- r185 failed because the shared PNU graph was 462.37 MB with 79,725 nodes,
  228,527 edges and 64,135 observations; parsing it retained several GB of
  Python objects.
- r186 isolated the run graph but was stopped on projected memory growth.
- r187 introduced a run-local causal graph and MAP-Elites archive. It completed
  15/20 in 4,651 seconds and reduced the graph to about 62.9 MB.
- r188 keeps two elites per `Base scope × solid phenotype × capacity ALT` cell,
  protects BOOK/plan/genotype anchors and performs streaming compaction. It
  completed 16/20 in 4,292 seconds with roughly 1.1 GB steady working set and a
  47.2 MB graph. QD retained 125 candidates across 58 occupied cells.
- One elite per cell was too aggressive; two elites preserved more compatibility
  reserve but still did not produce a 20-member compatible portfolio.

## Paid VLM truth

- One paid post-render portfolio call was made for the exact r188 board using
  `gpt-5.4-mini`. It is cached by image/prompt/model/candidate hashes.
- Response ID: `resp_08693458daaa8786006a5f2bf259ac81999b54dd75f54c2742`.
- Verdict: FAIL; 8 visible families, dominant family share 0.50.
- Failures: family resemblance, repeated footprint, repeated roof, weak program
  language and too few candidates.
- Requested next typed families: courtyard, split bridge, L/U mass, carve void,
  lift, notch, terrace and cross mass.
- The critic did not independently label the obvious floating fragments in
  MASS 07 `pack · inflate`; human PNG review did. VLM is evidence, not geometry
  authority. Add raster/mesh fragmentation checks before claiming clean mass.

## Frontend and graph verification

- `/design/language` shows one graph and a 94-run chronological archive.
- Selecting r188 shows 16 actual generated MASS PNGs; BOOK raster count is 0.
- The selected causal path has 39 active edges and includes geometry, program,
  compiler, gates, render, selector and unique executed MASS stages.
- The run-local memory path is visible as:
  `Compiled Geometry → Geometry Portfolio → VLM Portfolio Critic → Outcome`.
- Header shows `PAID FAIL VLM`; footer shows
  `PORTFOLIO VLM FAIL · gpt-5.4-mini`.
- Browser verification: one Full Graph, paid VLM node 1, console errors 0,
  page errors 0.

## Site/legal facts

- PNU `1168011800104170004`; parcel area 264.126 m².
- BCR 60%, FAR 250%, adjacent setback 0.5 m, landscaping minimum 15%.
- Parcel-derived generation host 102.931 m²; height-dependent sunlight field
  materialized; requested mass 15 m / 5 floors.
- Feasible height-field floor area 418.167 m². The 660.315 m² statutory FAR
  ceiling is not falsely assumed reachable.
- This remains a massing preflight, not permit approval. Parking uses a reviewed
  structured local seed and still needs current official ordinance review.

## Evidence

- `docs/playwright/design-route-live-verify/book-program-portfolios-r188-map-elites-compatibility-reserve/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r188-map-elites-compatibility-reserve/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r188-map-elites-compatibility-reserve/maas-paid-portfolio-vlm-audit.json`
- `docs/playwright/design-route-live-verify/r185-chronological-mass-archive/verify-chronological-archive.json`
- `docs/playwright/design-route-live-verify/r185-chronological-mass-archive/r188-paid-vlm-full-graph.png`
- `docs/playwright/design-route-live-verify/r185-chronological-mass-archive/r188-paid-vlm-node-focus.png`

## Multi-agent boundary

`ARR/backend/agents` remains shared control-plane/memory. Independent agents
are sibling repositories modeled structurally after `elevationAgent`; future
`massAgent` owns its identity/private memory but wraps the canonical
`ARR/backend/design/maas` AST/compiler. Handoffs remain bound to run ID, program
hash, geometry hash, PNU, artifact URL, gate state and VLM state.

## Individual reference VLM audit (2026-07-21)

- Exactly three paid candidate calls were made for r188 MASS 01, 07 and 10 with
  `gpt-5.4-mini`. Each call submitted the actual archived MASS PNG first and
  only reference images that passed the cached massing-image suitability gate.
- MASS 01: response `resp_0ccae7434c758fbb006a5f409268fc8198ba164fb064a1f751`,
  visual mean 0.5525, program fit FAIL.
- MASS 07: response `resp_0989a33a1a0c0c87006a5f409b80f0819abf3ab50506127b52`,
  visual mean 0.3675, program fit FAIL; `too_fragmented`,
  `weak_primary_mass`, `weak_form_continuity`.
- MASS 10: response `resp_0dd0c7b57b42df04006a5f40a458d48199bbba83b48dd4b418`,
  visual mean 0.6388, program fit FAIL; best of the three but its public
  void/active-edge relation is insufficient.
- MASS 01/07 used one actual reference image; MASS 10 used two. Interior and
  obscured retrievals were rejected and never received active VLM edges.
- Browser verification for MASS 07: one local reference image, one active
  `visual_reference_input` edge, `LIVE SCORED`, response ID and critic actions,
  zero remote images, zero console/page errors.
- r188 remains 16/20 FAIL. VLM evidence cannot override any hard gate.

## Elevation preparation

- Research memory exists in `docs/ai-session-memory/maas-aesthetic-texturing/`.
- MASS 10 recompiled to its exact archived hash and exported as an indexed-mesh
  handoff with 82 vertices and 160 triangles.
- It is not approved for final elevation because its individual VLM program-fit
  gate failed. Development/prototyping use is explicitly separated.
- The missing adapter is GeometryProgram indexed mesh -> metric depth, normals,
  silhouettes, facade planes and projection condition pack.
