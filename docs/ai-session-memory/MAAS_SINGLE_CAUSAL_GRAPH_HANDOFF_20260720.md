# MAAS single causal graph handoff — 2026-07-20

This file is the first read for the next AI session working on
`http://127.0.0.1:5175/design/language` or the BOOK/MASS/VLM generation loop.

## Non-negotiable system definition

MAAS is an Extended CSG-based Procedural Architectural Massing Language. It is
not a gallery of BOOK page images, not a mesh-editing toy, and not a visual
diagram disconnected from execution.

The authority chain for one candidate is:

`Base Solid → BOOK typed rule → recursive Geometry AST → program projection → compiler → geometry/site/capacity/law/parking/program GATEs → generated four-view MASS PNG → actually executed VLM inputs and scores → Selector → final MASS`.

Every MASS has one machine-readable execution passport. The frontend is only a
projection of that graph. Agents, the API and the UI must read the same node and
edge payload; a second authority graph must not be invented for presentation.

## Single graph rule

- Storage unit: `arr.maas.mass_execution_passport.v1`.
- Graph unit: `arr.maas.mass_activation_graph.v1`.
- Stable identity: `graph_id = mass-execution:<program_hash>` and stable node
  IDs within that program hash.
- Root query: `root_node_ids`.
- Result query: `result_node_ids = ["result:mass"]`.
- Default UI/Agent query: active ancestors of `result:mass`.
- Edge direction is cause to effect.
- An active edge has `activation > 0`.
- Pending/failed evidence stays present with activation 0. It is never painted
  as pass and never silently removed from the stored graph.
- The UI renders one selected MASS induced subgraph. Selecting another MASS
  changes the subgraph; it does not open another parallel graph.

Backend implementation:

- `ARR/backend/design/maas/geometry_language/execution_passport.py`
- `ARR/backend/design/maas/geometry_language/execution_activation.py`
- `ARR/backend/design/maas/geometry_language/execution_agent_context.py`
- `ARR/backend/design/maas/book_language/mass_passport_bridge.py`
- `/design/maas/executed-masses/`
- `/design/maas/executed-masses/<index>/passport/`

`GeometryOutcomeGraph` remains the cross-run outcome/memory store and can mirror
to Neo4j. The per-MASS passport is the exact execution subgraph. Computational
geometry remains in the Geometry Compiler/kernel; the graph stores typed
program, provenance, measurements, decisions and artifacts.

## BOOK authority and image policy

The four supplied BOOK extraction documents under `docs/260506/BOOK` are the
language authority. BOOK terms such as Base Volume 1/1, 3/8, 1/2, 1/4, 1/8,
1/16, Taper, Inflate, Nest, Bend, Shift and their combinations compile into
typed AST nodes.

BOOK raster scans are not MASS evidence and must not appear in
`/design/language`. Page IDs may remain as textual provenance. The frontend no
longer requests `/design/maas/book-assets/*`.

VLM images follow a different rule: only the generated candidate image and
reference images actually submitted to a recorded VLM request may become image
nodes. Retrieved-but-unused references do not activate. A run with no VLM call
shows `NOT EVALUATED`, zero reference nodes and activation-0 VLM edges.

## Frontend checkpoint r178

`BookLanguageFlow.tsx` is now one screen and one graph:

- no BOOK/catalog/geometry/lineage graph tabs;
- central single causal graph for the selected executed MASS;
- right sidebar contains the actual archived MASS PNG, BOOK rule ID, Base
  Volume scope, FAR/capacity alternative, gate/VLM/selector state, hashes and
  exact DSL;
- bottom strip contains actual executed MASS candidates; clicking a thumbnail
  reloads that candidate's passport;
- no nested `MassExecutionGraph`, no FULL FLOW duplicate, no BOOK scan card;
- inactive VLM edges are not traversed as selected causal paths.

Files:

- `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- `ARR/frontend/src/design/components/book-language-flow/LanguageNetworkCanvas.tsx`
- `ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- `ARR/frontend/src/design/components/book-language-flow/book-language-flow.css`

Browser evidence:

- `docs/playwright/design-route-live-verify/r178-single-causal-language-graph/single-causal-language-graph.png`
- `docs/playwright/design-route-live-verify/r178-single-causal-language-graph/verify-language-graph.json`

Verified: HTTP 200, meaningful content, exactly one causal graph, zero legacy
mini graphs, actual MASS sidebar present, MASS 01→02 click changes passport,
one result node, one VLM node, zero BOOK raster DOM elements, zero BOOK asset
requests, zero console/page errors. Frontend `tsc --noEmit` passes.

## Selection and visual-coherence status

r176 was 12/20 and r177 was 14/20. Both are failures even though every selected
candidate passed compiler/geometry/program/legal/parking gates and all four
capacity alternatives were present. r177's only portfolio failure was
`selected_count_below_20`.

r177 revealed that a 512-width beam result was being treated like a maximum
compatible subset. This is not a sound proof. The final 60-candidate set is now
solved as a binary MILP:

- one binary variable per candidate;
- incompatible silhouette pairs: `x_i + x_j <= 1`;
- typed operation/seed/section/roof/chassis/capacity/concept/phenotype caps;
- required Base Volume, capacity, principle-kind, frontage and ground-strategy
  coverage;
- objective: maximum candidate count, then measured score as a tiny tie-break.

Implementation:

- `ARR/backend/design/maas/book_language/portfolio_constraint_solver.py`
- `ARR/backend/design/maas/book_language/portfolio_selection.py`

The MILP does not weaken a geometry, legal, parking, capacity or silhouette
gate. If the optimum is below 20, the problem is candidate-language supply and
must be fixed before selection. Do not fill blank cards with failed or duplicate
MASSes.

r178 completed `15/20 · fail`. MILP proved 15 under the supplied constraints,
so it improved the approximate r177 set by one but did not fill the board.
Trace: raw 351, capacity-target hard pass 60, unique final solver pool 60,
MILP count 15, all four capacity alternatives present, and the only portfolio
failure is `selected_count_below_20`. It made zero paid VLM requests.

The proof exposed a modeling error: nominal capacity-band quotas were encoded
as hard maxima summing to 20. Supply was MAX 1 / BRIEF 5 / BALANCED 19 /
RESERVE 30, but pairwise silhouette conflicts allowed only two BRIEF cards.
The unused BRIEF quota could not be absorbed by another already hard-passing
band. Capacity alternatives are scenarios, not morphology families. r179
therefore requires every available band at least once but treats the nominal
distribution as a preference. Every candidate's own achieved-versus-target
capacity check remains a hard gate. r179 is running at
`book-program-portfolios-r179-language-only-capacity-coverage-milp-pass` and
must be treated as pending until final JSON and PNG exist.

## Honest visual boundary

Watertight/manifold/component-count pass does not prove competition-level
architectural coherence. r176/r177 boards include candidates that are valid
solids but still read as over-carved, overly faceted or accumulated effects.
Do not call them final. Preserve the existing scale-free polygon-quality,
spatial-connectivity and body-rule-budget gates. Add a new hard condition only
from a measured, normalized failure pattern; do not tune arbitrary dimensions
against one screenshot.

Directly inspect the final 20-card board. A later VLM visual pass must be
explicitly enabled and cost-bounded. Never claim VLM recognition from a
non-live run.

## Research-method provenance

Per-MASS Agent context now declares which research adaptation was actually
active rather than merely listing papers. The local source registry is
`ARR/backend/design/maas/preference/paper_sources.py`; current method layers
include ShapeAssembly-style typed part programs, Szalinski-style program
recovery/canonicalization, CADFusion/CADTalk semantic program conditioning,
CADLoop-style skill-grounded iteration and EvoMass-style performance-oriented
evolution. Active/inactive status is stored in
`research_method_context` for each MASS. A paper citation is not execution
evidence unless its runtime components were used for that candidate.

## Next-session order

1. Read this file and `maas-language-visual-memory-current.json`.
2. Inspect the completed r178 summary and board; never infer completion from a
   running directory.
3. If MILP optimum is 20, verify every archived passport/hash/gate and rerun the
   browser check against the 20-candidate archive.
4. If optimum is below 20, use solver conflict/cap diagnostics to expand the
   upstream typed Geometry Program supply. Do not relax silhouette or clean
   mass gates.
5. Judge the actual PNGs for architectural coherence. VLM can be enabled only
   with explicit credentials/opt-in and a bounded request budget.
6. Update this handoff and the machine-readable current JSON with the completed
   run ID, exact counts, failures and evidence paths.

## r179 FULL GRAPH restoration + ArchDaily/VLM truth (2026-07-20 23:55 KST)

The BOOK graph was not deleted. The frontend now uses one `LanguageNetworkCanvas`
with two query modes over the same stable IDs:

- `FULL GRAPH`: complete visible BOOK design space plus the selected MASS runtime
  trace, actual render, reference retrieval, VLM/selector state, exact outcome
  memory slice and all archived MASS result PNG nodes;
- `SELECTED MASS PATH`: the compact execution passport for one MASS.

FULL contains Base Model 6, Orientation 3, Operation Family 3, Cardinality 6,
BOOK Operative 30, Combination/Aggregation/Variation nodes and 15 actual r179
MASS results. Selecting MASS 01 activates exactly one BOOK semantic route and
its observed AST/program/compiler/site/FAR/law/parking/render/selector route.
It does not traverse every combinatorial ancestor. One canvas remains mounted;
there is no second graph component and no BOOK raster request.

ArchDaily evidence is now typed rather than hidden:

- local corpus authority: 13 collections / 313 projects / 375 images;
- selected MASS query: explicit program/use + geometry family + intent tags;
- five deterministic relevant images are shown as image nodes;
- retrieved-but-not-submitted images use pending/dashed edges;
- only images recorded in `vlm_reference_image` passport nodes may use active
  `visual_reference_input` edges;
- r179 Live VLM is OFF, so current truth is 5 retrieved / 0 used and VLM
  `not_evaluated`; no paid request was made;
- all displayed images use the allow-listed local
  `/design/maas/reference-assets/...` route, not direct remote loading.

The selected MASS also queries `GeometryOutcomeGraph` by exact geometry hash.
MASS 01 currently returns a real three-node/two-edge lineage slice. The UI
re-reads archive and outcome endpoints every three seconds and switches to a
new completed run automatically. This is near-live file/API synchronization,
not a claim that hidden model neurons or an unfinished in-process observation
are streamed before the runner checkpoints its graph.

r179 completed `15/20 · fail` with zero paid VLM calls. Do not describe the
portfolio or its visual quality as complete. The capacity-band correction did
not raise the MILP result above r178; candidate-language supply/compatibility
still needs correction without relaxing geometry/legal/parking/capacity gates.

Verification:

- `docs/playwright/design-route-live-verify/r179-full-graph-ui/verify-full-graph.json`
- `docs/playwright/design-route-live-verify/r179-full-graph-ui/full-graph-with-mass-results.png`
- `docs/playwright/design-route-live-verify/r179-full-graph-ui/full-graph-archdaily-vlm-nodes.png`
- browser: HTTP 200, graph count 1, Base 6, Operatives 30, executed MASS 15,
  ArchDaily retrieved 5, active VLM references 0, exact Agent Memory nodes 3,
  BOOK raster requests 0, console/page errors 0;
- frontend `tsc --noEmit` passed;
- backend extended-CSG focused tests passed 10/10.

## r182 actual Geometry-page closure + one-graph verification (2026-07-21)

The replenishment defect was real: prior parent cycles changed legacy role
sequences while replaying the same fixed Geometry Program payloads. The form
bank is now paged by actual recursive AST payload in
`geometry_language/universal_form_bank.py`. Page 0 retains the 64 bounded
synthesis programs plus 18 core examples; pages 1-7 each author 64 new bounded
programs and record `form_bank_variation_page` in program metadata and every
selected MASS execution passport. Page 0 and page 1 payload overlap is zero.

Non-live runs may traverse seven bounded pages; a live-VLM run retains its
configured/default one-cycle budget. This is a cost boundary, not a quality
gate relaxation. r182 made zero paid VLM calls.

The candidate-availability diagnostic was also unified. Selector, capacity
diagnostic and benchmark now use the same deduplicated, capacity-target
hard-pass universe. A BOOK principle or FAR band existing only among rejected
candidates is no longer reported as available. This fixed r181's false
aggregation failure without inventing a selected aggregation.

r182 completed `20/20 · pass` after page 7:

- selected counts by replenishment page: 16, 18, 18, 19, 19, 19, 20;
- accumulated selection-pool counts: 419, 459, 476, 488, 493, 498, 499;
- exact capacity-target pass universe: 177;
- MILP selected 20 and reached target under unchanged silhouette, clean mass,
  program, legal, parking and capacity gates;
- six Base Volume scopes, fourteen BOOK principles, all four principle depths
  present (13 base operative / 2 combination / 1 aggregation / 4 case study);
- capacity alternatives: 11 spatial reserve / 5 balanced / 3 brief / 1 maximum;
- solid phenotypes: 3 curved / 1 oblique / 5 prismatic / 5 stepped / 5 voided /
  1 winged; thirteen recursive geometry families;
- 20 visual languages, zero near-duplicate pairs, downstream 20/20, and twenty
  visible archive cards.

Direct PNG review is required even after numeric pass. MASS 17 is recorded as
one connected, non-degenerate solid, but its layered pinch silhouette can read
as floating from the archive camera. Do not call the board competition-final
or VLM-approved on the strength of the numeric pass.

Evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios-r182-seven-page-closure-pass/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r182-seven-page-closure-pass/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/r182-single-graph-ui-final-images/full-graph.png`
- `docs/playwright/design-route-live-verify/r182-single-graph-ui-final-images/archdaily-vlm-reference-nodes.png`
- `docs/playwright/design-route-live-verify/r182-single-graph-ui-final-images/verify.json`

Browser verification: HTTP 200; one graph; Base 6; Operatives 30; actual MASS
20; gallery images loaded 20/20; selected evidence image loaded; ArchDaily 5
retrieved / 0 used; exact memory nodes 6; selected MASS click activates 43
related nodes and 41 edges; BOOK raster request/DOM count 0; console/page errors
0; selected-path graph/result count 1/1. The sidebar now says
`COMPLETE · VLM NOT EVALUATED` instead of the misleading `IN PROGRESS` while
still making no VLM acceptance claim.

Current inspection URL: `http://127.0.0.1:5175/design/language`.
