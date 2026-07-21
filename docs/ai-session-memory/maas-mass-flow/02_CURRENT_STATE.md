# Current Verified State — r182 + chronological archive

Generated 2026-07-21 KST.

## What is working

- Portfolio status: `20/20 · pass` for PNU `1168011800104170004`, program
  `근린생활시설`.
- Actual Geometry Program replenishment pages authored new AST payloads. The
  selected counts were `16, 18, 18, 19, 19, 19, 20`; page 7 supplied the last
  compatible MASS.
- Six Base Volume scopes, fourteen BOOK principles, four principle depths and
  four capacity alternatives are present.
- Capacity distribution: reserve 11, balanced 5, brief 3, maximum 1.
- Solid phenotypes: curved 3, oblique 1, prismatic 5, stepped 5, voided 5,
  winged 1. Visual-language count 20; near-duplicate pairs 0.
- Downstream site/legal/parking combined hard pass: 20/20.
- Browser: one graph, 20 executed MASS nodes, 20/20 gallery images loaded,
  selected sidebar image loaded, Base 6, Operatives 30, BOOK raster 0,
  console/page errors 0.
- `/design/language` now exposes one causal graph plus a chronological execution
  timeline and a MASS-only archive. It discovers 91 historical runs, places the
  newest run at the left, and keeps failed runs visible instead of silently
  falling back to an older success.
- Selecting r184 truthfully shows `0 MASS · NO FINAL`; selecting r182 replays 20
  actual generated MASS images and unique run-bound node IDs. BOOK scans are
  language provenance only and never appear as generated MASS evidence.
- Program/use controllers and BOOK operators now have separate authority.
  `book_split` cannot impersonate a public-space, access, legal or program
  controller merely because its name is Split.
- `ARR/backend/agents` is the shared multi-agent control plane. Independent
  agents are sibling repositories such as `elevationAgent` and the future
  `massAgent`; shared memory/contracts live at the parent, while private agent
  history stays inside each sibling.

## What is not yet proven

- The board is numerically valid but not visually competition-final. MASS 17 is
  one connected, non-degenerate solid yet its layered pinch silhouette reads as
  floating from the archive camera. Several masses remain compact/prismatic.
- Live VLM was not run for r182. A bounded r184 review later used exactly 24
  paid calls against actual generated MASS renders and small relevant reference
  sets, but selected 0/20. r184 is therefore preserved as a failed run, not
  presented as a finished portfolio.
- Deterministic r185 was stopped after 2,739.4 seconds when system free physical
  memory fell below 1 GB. It produced no final geometry archive or MASS PNG and
  therefore cannot support a visual-quality claim. The frontend preserves it as
  `aborted_memory_pressure · 0 MASS · NO FINAL` instead of hiding it.
- The legal flow used live PNU zoning and the actual parcel-derived buildable
  host, but it is a massing preflight, not an approval-grade code check.
- Parking used the reviewed local structured seed; Neo4j legal enrichment was
  not requested. The selected rule source still requires authoritative permit
  review.

## Site/legal facts used by r182

- PNU: `1168011800104170004`; jurisdiction code `11680`.
- Original parcel area: 264.126 m².
- Zone: 제2종일반주거지역.
- BCR limit: 60%; FAR limit: 250%.
- Adjacent setback: 0.5 m; landscaping minimum: 15%.
- Parcel-derived horizontal buildable/generation host: 102.931 m².
- Sunlight field: materialized and height-dependent.
- Requested massing: 15 m / 5 floors.
- Feasible maximum floor area from the height field: 418.167 m²; the statutory
  FAR ceiling 660.315 m² was not falsely assumed reachable.
- Parking example for MASS 01: required 2, provided 2, piloti-ground strategy.

`parcel_coordinates_used=false` in the program dimensional context means the
universal language did not memorize absolute parcel coordinates as a template.
The compiler still received the actual parcel-derived buildable polygon and its
oriented dimensions. Keep this distinction explicit.

## Evidence

- `docs/playwright/design-route-live-verify/book-program-portfolios-r182-seven-page-closure-pass/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r182-seven-page-closure-pass/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/r182-single-graph-ui-final-images/verify.json`
- `docs/playwright/design-route-live-verify/r182-single-graph-ui-final-images/full-graph.png`
- `docs/playwright/design-route-live-verify/r185-chronological-mass-archive/verify-chronological-archive.json`
- `docs/playwright/design-route-live-verify/r185-chronological-mass-archive/chronological-mass-archive.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r185-program-controller-archive-preflight/maas-run-state.json`

## Multi-agent boundary

- Shared parent contract: `ARR/backend/agents/SHARED_AGENT_ARCHITECTURE.md`
- Shared parent memory: `ARR/backend/agents/memory/MEMORY.md`
- Agent template reference: `ARR/backend/agents/elevationAgent`
- MASS domain engine: `ARR/backend/design/maas`
- Future independent MASS agent: `ARR/backend/agents/massAgent`

Copy the `elevationAgent` repository structure for a new agent, but never copy
its identity, private memory or example history. Cross-agent handoffs must be
bound to `run_id`, `program_hash`, `geometry_hash`, PNU, artifact URLs and gate
states so every downstream decision is replayable.
