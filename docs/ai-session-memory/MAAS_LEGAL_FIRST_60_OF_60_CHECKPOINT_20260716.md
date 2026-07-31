# MAAS legal-first 60/60 checkpoint (2026-07-16)

This checkpoint supersedes the legal-retention result at the end of
`MAAS_BOOK_EXECUTABLE_LANGUAGE_CHECKPOINT_20260715.md`. The older run selected
on the parcel first and clipped afterward, so geometry retention passed 0/60.

## What changed

The BOOK/program portfolio loop now materializes one reusable
`LegalGenerationContext` before candidate generation. The context contains the
horizontal buildable footprint, the height-dependent sunlight ring, regulation
limits and typed evidence. Candidate generation and downstream evaluation share
that exact context.

The active graph order is now:

`live PNU parcel -> legal generation context -> program role graph -> p.3 scope -> BOOK operators -> bounded parameter probe -> optional legal field fit -> program/clean gate -> legal/retention/parking preselection -> diverse portfolio selector -> same-source hard-gate replay`

Key implementation details:

- The compiler starts from the 102.931 m2 legal buildable footprint rather than
  the full 264.126 m2 parcel.
- Each BOOK sentence executes three schema-bounded parameter probes. These are
  typed operator parameters, not labels or parcel-coordinate templates.
- The third probe can use the sunlight-safe section at two thirds of requested
  program height as a second legal base host.
- If a portfolio still lacks 20 alternatives or one of the six p.3 scopes, one
  deterministic normalized parent-graph mutation is evaluated as bounded
  replenishment.
- The difficult gym `1/16` candidate uses a whole-graph
  `bounded_uniform_scale_translate` legal-field modifier. Volumes and renderer
  surfaces receive the same transform before program and hard-gate selection.
  The selected candidate retains 0.9249 volume and weighted plan IoU. Two other
  `1/16` candidates remain rejected at 0.7914 and 0.7935; no retention threshold
  was relaxed.
- The summary records hard-gate counts by p.3 scope and generation-host mode,
  plus legal-generation provenance on selected rows.
- Clean mass remains `visible volume <= 5`. The default effective-surface budget
  and profiled-surface exception are unchanged; no disconnected fragment lane
  was added.

## Latest live PNU result

PNU: `1168011800104170004`. VWorld boundary, zoning/regulation, road frontage,
neighbors, sunlight and local structured parking rules were live/materialized.
No synthetic parcel fallback was used. Neo4j is not required for this diagnostic.

- Neighborhood living: 20/20, 18 distinct BOOK principles, 18 measured visual
  languages, all six p.3 scopes.
- Gymnasium: 20/20, 14 distinct BOOK principles, 18 measured visual languages,
  all six p.3 scopes. Six roof/section families survive: ridge, ridge plus
  daylight monitor, carved-entry ridge, folded, sawtooth/daylight monitor and
  stepped section.
- Cultural/museum: 20/20, 16 distinct BOOK principles, 18 measured visual
  languages, all six p.3 scopes.

Same accepted source hard gates:

- legal metrics: 60/60
- geometry retention: 60/60
- parking: 60/60
- combined legal + retention + parking: 60/60
- mean volume retention: neighborhood 0.9038, gym 0.9288, cultural 0.8546
- minimum selected volume retention: 0.8018

Cross-program mean silhouette distance is 0.4556 for neighborhood/gym, 0.4270
for neighborhood/cultural and 0.4807 for gym/cultural. Minimum pairwise values
are 0.2204, 0.2329 and 0.2534. These are descriptor evidence, not an
architecture-grade verdict.

## Honest visual verdict

Overall status remains **FAIL** even though BOOK/program numeric status and the
downstream hard constraints pass. Direct original-resolution PNG inspection
still detects program-internal chassis repetition:

- Neighborhood has more branch/ribbon/split variation, but elongated bars and
  folded/terrace cascades repeat.
- Gym roof/section geometry is real and more varied, but most alternatives still
  begin from the same low rectangular long-span hall chassis.
- Cultural alternatives preserve court/bridge/split/carve relations, but low
  gallery boxes and stepped bars dominate.

Therefore `architecture_grade_claim_allowed` remains false. The two KakaoTalk
reference masses and the broader extended-CSG/Geometry-DSL target are not yet
visually matched by these program portfolios. The compiler has the recursive
language capacity, but the program generator/selector still needs stronger
chassis archetypes and reference-conditioned graph edits.

VLM was not used as a direct geometry generator in this run. The current VLM
role remains critic/reranker/typed graph-edit director. No live OpenAI request
was made with the API key pasted into chat; that key must be treated as exposed
and rotated. Mass-Brain/GRL remains a shadow lane because the prior fair
v104/v105 ablation did not change final accepted geometry.

## Evidence

- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-cultural-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-60-summary.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-visual-review.json`

## Next work

1. Add explicit program chassis nodes, not only roof/section nodes: neighborhood
   court/street/ribbon/corner typologies, gym fan/paired-hall/arched-bar/offset
   service-court typologies, and museum courtyard/bridge/atrium/ramp/cluster
   typologies.
2. Add stronger pose-invariant chassis clustering and reserve representatives
   per chassis before BOOK-operation diversity is counted.
3. Feed reference-image VLM analysis into typed chassis/section/void graph edits,
   then prove the edit changes compiled geometry and final selection.
4. Keep the legal-first context and 60/60 hard constraints fixed while improving
   visual diversity. Do not restore post-selection clipping or weaken retention.
5. Re-run the three PNG boards and update visual review only after direct
   original-resolution inspection.
