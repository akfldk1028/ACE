# MAAS Research Direction

Updated: 2026-06-08

## Blunt Verdict

The right direction is not "let an LLM/agent invent mass geometry."

The robust path is:

```text
legal envelope / cadastral datum / setbacks
-> procedural mass grammar
-> constraint solver / repair
-> evolutionary or multi-objective search for diversity/performance
-> deterministic validators
-> agent explanations and orchestration
-> real-browser VWorld visual confirmation
```

Agents should coordinate, critique, explain, and select. They should not be the source of geometric truth.

## Research Signals

### Procedural Building Grammars

Use shape grammars / procedural rules as the editable mass-generation language.

Important source:

- Mueller, Wonka, Haegler, Ulmer, Van Gool, "Procedural Modeling of Buildings", SIGGRAPH 2006.
- Key idea to borrow: hierarchical/context-sensitive rules generate building mass/shell variations, while keeping geometry editable and reproducible.

ARR implication:

- MAAS `verb_sequence` should become a real grammar, not just labels.
- Operators such as `base`, `taper`, `notch`, `split`, `court`, `terrace`, `podium`, `tower` should compile to explicit floor plates/volumes.

### Constraints Inside Procedural Modeling

Do not generate first and validate later only. Constraints must be part of the generation loop.

Important source:

- Whiting, Ochsendorf, Durand, "Procedural Modeling of Structurally-Sound Masonry Buildings", SIGGRAPH Asia 2009.
- Key idea to borrow: procedural parameters are automatically adjusted by optimization so generated forms satisfy hard feasibility constraints.

ARR implication:

- The legal envelope and datum basis must constrain generation before ranking.
- Repair is still needed, but a candidate that repeatedly needs severe repair should be penalized or rejected.

### Layout / Program Synthesis

Massing alone is not enough. A mass is weak if floor plates cannot host a plausible program/core/circulation.

Important source:

- Merrell, Schkufza, Koltun, "Computer-Generated Residential Building Layouts", SIGGRAPH Asia 2010.
- Key idea to borrow: high-level architectural requirements become programs; stochastic optimization realizes them into floor plans.

ARR implication:

- Current `program_packing.status = ok` is only a first pass.
- Need minimum core, corridor, egress, vertical shaft, and usable depth checks by building type.
- A floor plate below program viability should be rejected, not merely hidden.

### Diversity-Preserving Optimization

Do not return 18 nearly identical legal boxes.

Important source:

- EvoMass / SSIEA building massing research.
- Key idea to borrow: island-based / steady-state evolutionary search preserves diverse typologies while improving performance.

ARR implication:

- Keep `legal_layered_max` as capacity anchor.
- Use legacy 10 algorithms and grammar operators as seed/diversity sources only.
- Rank by legal validity first, then capacity, program viability, daylight/sunlight, and typological diversity.

### Example-Based / Graph Grammar Generation

For richer forms, learn/extract reusable graph grammar patterns from examples rather than hand-writing endless templates.

Important source:

- Merrell, "Example-Based Procedural Modeling Using Graph Grammars", SIGGRAPH 2023.

ARR implication:

- Later phase: collect good mass examples as graph primitives and extract reusable patterns.
- Do not do this before legal envelope and validator gates are reliable.

### Generative Design Workflow

Architecture workflows need explicit objectives, constraints, and human review, not black-box generation.

Important source:

- Autodesk Project Discover, generative design for architectural space planning.

ARR implication:

- UI should expose objective tradeoffs and hard constraint status.
- Each candidate must carry a review trail: legal basis, repair actions, rejected constraints, datum source, and visual verification state.

### Multi-Agent Role

Multi-agent systems are useful, but only around deterministic tools.

Research signal:

- Multi-agent architecture/search papers show that topology, roles, and verification matter, but they do not replace domain validators.

ARR implication:

Recommended agents:

- Geometry Agent: checks polygon validity, floor plate stack, volume consistency.
- Law Agent: checks BCR/FAR/height/setback/sunlight/daylight/datum basis.
- Program Agent: checks core/corridor/room packing viability.
- Optimization Agent: checks diversity and objective tradeoffs.
- Visual QA Agent: compares API geometry, section PNG, and VWorld view.
- Review Agent: rejects any candidate without complete evidence.

## Current Repo Integration Status

The project already has several agent / orchestration surfaces:

- Root `AG/` / Auto-Claude documents AutoGen Studio, A2A agents, CLI orchestration, and SharedMemory.
- `AG-light/` is a compact legal-agent platform: Cloudflare Worker, FastAPI MCP tools, MessageBus, SharedMemory, Claude agent definitions, team JSON, and pattern JSON.
- ARR has an `agents` Django app with A2A-style agent cards, JSON-RPC chat endpoints, worker agents, and Neo4j integration.
- ARR also has a `graph_db/` package with Neo4j provenance tracking for Decision/Evidence/Artifact relationships.
- `cli/design-regulation-check/` is the current strongest deterministic verification harness for datum/envelope/section/VWorld-related gates.
- Hermes gateway currently exposes ARR backend tools.

But MAAS is not yet wired into that stack.

Current MAAS `agents/` are deterministic local review contracts, not live AutoGen/Hermes/AG-light/A2A workers. They attach JSON review cards for geometry/law/optimization/review to the MAAS response, and emit A2UI messages for the frontend. This is a good interface seed, but it is not true multi-agent orchestration yet.

2026-06-11 professor discussion update:

- The intended product direction is explicitly AutoGen/A2A-like collaboration:
  agents must talk to each other, challenge evidence, and request deterministic
  repair/regeneration, not merely call one MCP tool.
- Existing AutoGen/A2A assets should be reused where practical, especially
  `AG/`, `AG-light/server/agents/`, MessageBus, SharedMemory, team/pattern JSON,
  and AG-light MCP tools.
- Do not move raw geometry truth into the agent layer. Live agents coordinate
  around ARR deterministic tools and the MAAS evidence bundle.
- Do not use Graph DB as a raw chat transcript store. Store durable review
  summaries, decisions, evidence refs, rejected constraints, repair requests,
  and candidate lineage. Raw debate logs can live in MessageBus/SharedMemory/log
  artifacts and be referenced by hash/path if needed.
- Parking is now a first-priority legal/design blocker. The Parking Lot Act,
  Enforcement Decree/Table 1, Enforcement Rule, and relevant local ordinances
  must be represented in the law Graph DB while ARR implements deterministic
  parking requirement/layout validators.

The missing bridge is an ARR/Hermes tool layer for massing:

- `generate_maas_variants`: call `site-boundary -> auto-constraints -> jobs -> run -> results`.
- `validate_mass_candidate`: validate one candidate against legal metrics, floor plates, program feasibility, and datum basis.
- `render_mass_evidence`: produce API-derived section/plan artifacts.
- `vworld_visual_check`: confirm real-browser Cesium/VWorld placement.
- `maas_review`: run parallel reviewer agents over the same evidence bundle and return a final PASS/FAIL.
- `parking_requirements`: compute required parking count with law/article refs.
- `parking_layout_check`: validate stall/aisle/ramp/access feasibility for the
  selected candidate.

Do not let reviewer agents invent or mutate geometry directly. They may request deterministic repair/regeneration, but the source of truth remains the legal envelope generator, validators, and visual evidence.

Graph DB should not become the geometry engine for massing. Keep exact mass geometry in Postgres JSON/PostGIS-style artifacts, GeoJSON, section images, and deterministic validator outputs. Use Neo4j for relationships and provenance:

- PNU -> zoning/parcel/datum/legal-basis nodes.
- MAAS job -> candidate -> floor plates / mass volumes / rendered evidence artifacts.
- candidate -> applied constraints -> violated/repaired/rejected rules.
- agent review -> evidence -> final decision.
- candidate lineage from seed/operator/grammar step to final selected result.

This lets agents ask "why did this mass pass/fail?" or "which law/evidence caused rejection?" without moving computational geometry into the graph database.

## Implementation Priority

1. Make legal envelope generation deterministic and testable for more PNU cases.
2. Replace pragmatic floor-area threshold with building-type/program-aware minimum plate rules.
3. Add Parking Lot Act graph ingestion/projection and deterministic parking
   requirement/layout validators.
4. Add mass-aware daylight: selected mass wall/window candidates -> perpendicular distance rays -> pass/fail section.
5. Add true VWorld visual gate in a real browser environment, not headless WebGL.
6. Promote `maas_verb_sequence` into a real grammar compiler with typed operators and inverse traceability.
7. Add true AutoGen/A2A-style agent review only after the above validators
   produce structured evidence.

## Non-Negotiable Standard

A MAAS candidate is not "correct" unless these all agree:

- API legal metrics.
- Datum source and basis.
- Floor plate/volume geometry.
- Program/core feasibility.
- Parking requirement and layout feasibility.
- Section PNG.
- VWorld/Cesium placement in a real browser.
- Summarized agent review trace with no unresolved hard failures.

## 2026-06-26 MAAS 20-Alternative PNG Evidence

Latest mass-diversity evidence for real PNU `1168011800104170004` was regenerated after restarting the ARR backend on `127.0.0.1:18000`.

- Command/script: `node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`
- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- HTML: `docs/playwright/design-route-live-verify/maas-20-alt-latest.html`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- Result count: 20 alternatives.
- Unique `mass_shape` names: 17.
- Section-profile alternatives: 6.
  - Rank 9: `diagonal_connect_step_x_layered` / `diagonal_connector`
  - Rank 10: `terrace_link_north_layered` / `terrace_ribbon`
  - Rank 11: `sloped_roof_mass_layered` / `sloped_roof`
  - Rank 12: `grammar_diagonal_step_connector_layered` / `diagonal_connector`
  - Rank 15: `grammar_sloped_roof_envelope_layered` / `sloped_roof`
  - Rank 17: `grammar_terrace_ribbon_stepback_layered` / `terrace_ribbon`

Interpretation:

- The generator is no longer producing only identical legal boxes. The PNG now shows plan variation plus visible pink section overlays for sloped roof, diagonal connector, and terrace ribbon concepts.
- It is still not final design quality. Several top and bottom candidates share similar high-FAR stepped envelopes, so the selector should add a stronger family-level diversity gate.
- Parking remains the hard blocker for this PNU/building type. The latest 20-alt PNG has no green parking-pass candidates; high-FAR design variants mostly fail required/provided parking. Do not present these as approved masses.
- Next loop should keep legal/section diversity while explicitly optimizing for parking-feasible candidates, not merely ranking high FAR/BCR outputs.

## 2026-06-26 Late Loop: Design-Family Balance / Parking Floating Fix

User correctly rejected the previous PNG as not competition/design quality:

- Too many candidates were still legal stepback boxes.
- Pink `diagonal_connector`, `terrace_ribbon`, and `sloped_roof` read as visual overlays, not true mass geometry.
- Parking lines in the live Cesium view could read as floating because exact stall outlines had both ground-clamped lines and elevated duplicate visible lines.

Changes made:

- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - Added final design-balanced selection for the 20-card review set.
  - The selector now keeps at most a compact parking signal, then reserves family representatives before backfill.
  - For `max_variants >= 8`, the early K-medoid branch now preserves plan-diverse families: `interlock`, `overlap`, `split`, `branch`, `pinch`, `courtyard`, `void_notch`, and `slender_bar`.
  - Duplicate `mass_shape` entries are avoided until there are no unique shapes left to fill the sheet.
- `ARR/frontend/src/design/lib/cesium/mass-entities.ts`
  - Removed elevated duplicate parking stall visible-lines from the default view.
  - Parking guide lines are ground-clamped.
  - Parking labels are lowered close to ground level.
- `docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`
  - Section profile drawing was toned down so it reads less like arbitrary pink markup: diagonal connector is a width-bearing connector face, terrace ribbons are tighter edge bands, and sloped roof is closer to the top mass.

Latest regenerated evidence:

- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- PNU: `1168011800104170004`
- Candidate count: 20
- Unique `mass_shape` count: 19
- Section-profile candidates: 6
- Parking pass count: 0
- Generation time: about 138 seconds
- Visible families now include `interlock_cross_diagonal`, `overlap_slabs_y`, `split_bridge_y`, `branch_y_wide`, `pinch_waist_x`, `courtyard_void`, `slender_bar_south`, and the section-design grammar candidates.

Remaining hard truth:

- This is better review evidence, but it is still not paper-grade architectural massing.
- `sloped_roof`, `terrace_ribbon`, and `diagonal_connector` are still section/render evidence layered over conservative legal floor plates. They are not yet true non-orthogonal mesh solids in the source geometry.
- The actual PNU/common-housing run still has `parkingPass=0`, so no candidate should be called permit-ready or final.
- Next real improvement is not another overlay pass. It should create source geometry for sloped/diagonal/terrace solids and optimize against parking feasibility at generation time.

## 2026-06-27 PNG Review Loop: Render Tricks Are Not Enough

User asked to keep reviewing the PNG visually, not just quote metrics. Latest
loop regenerated `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
after changing `render-maas-20-alt.cjs` so section-profile candidates materialize
their rendered volume rings instead of only drawing pink overlays.

Latest visual/stat result:

- PNU: `1168011800104170004`
- Candidate count: 20
- Unique `mass_shape`: 19
- Section-profile candidates: 6
- Parking pass: 0
- Generation time: about 120 seconds

Visual judgment:

- Plan-family diversity is now visible: interlock, overlap, split, branch,
  pinch, courtyard, slender bar, legal layered, and section grammar candidates
  all appear in the sheet.
- The section-profile rendering is still not good enough for competition-grade
  architectural massing. `diagonal_connector` still reads partly like a marker
  on a stepped box, and `sloped_roof` still reads like a roof plane placed on
  top rather than a true source solid.
- Do not spend more time trying to make this pass by PNG overlay/render tricks.
  The next real fix belongs in backend geometry generation: create actual
  source volumes/solids for sloped, diagonal, and terrace/ribbon forms, then
  validate those against legal envelope and parking feasibility.

## 2026-06-27 Backend Section Source Volumes

User asked to do the backend geometry step, not just keep adjusting PNG. First
backend implementation is now in `ARR/backend/design/maas/legal_mesh_optimizer.py`.

What changed:

- Section profile intent is materialized into `properties.mass_volumes` and
  `properties.maas_model.volumes`.
- Legal accounting still uses conservative `floor_plates`; generated section
  volumes are clipped inside their legal floor-plate bands.
- New metadata:
  - `properties.section_profile_materialized.status =
    materialized_inside_legal_floor_plates`
  - volume roles include `section_source_sloped_roof`,
    `section_source_terrace_ribbon`, `section_source_diagonal_connector`, and
    `section_source_diagonal_connector_bridge`.
- Diagonal connector variants now append a real bridge volume inside the union
  of legal floor-plate bands instead of relying on a pink line overlay.
- `render-maas-20-alt.cjs` no longer fabricates section geometry in the PNG.
  It draws backend `mass_volumes`; connector bridge volumes get a darker orange
  source-volume style so they are visible without a fake overlay.

Latest PNU evidence:

- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- PNU: `1168011800104170004`
- Candidate count: 20
- Unique `mass_shape`: 19
- Section materialized candidates: 6
- Diagonal bridge source-volume candidates: 2
- Parking pass: 0
- Generation time: about 116 seconds

Visual judgment after opening the PNG:

- This is a real backend source-volume improvement: the JSON now carries
  materialized section volumes, not only `section_profile` labels.
- It still does not reach competition-grade design quality. The output is a
  conservative stepped/shifted solid approximation inside legal plates, not a
  true freeform/non-orthogonal mesh optimizer.
- Next required step is a proper 3D solid/mesh path for sloped faces and
  connector surfaces, plus parking-feasible generation. Do not claim this is
  final MAAS paper-quality massing.

## 2026-06-28 Backend Section Source Surfaces

Loop goal: keep reviewing the PNG and move from source volumes to explicit
source surfaces so sloped/terrace/diagonal intent reads as geometry, not labels.

Changes:

- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - Adds `section_source_surfaces` to `properties` and `maas_model`.
  - Surface records use `vertices_wgs84_h`, `role`, `kind`, and
    `surface_type`.
  - Generated roles:
    - `section_surface_sloped_roof_plane`
    - `section_surface_terrace_band_1..3`
    - `section_surface_diagonal_connector_deck`
- `docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`
  - Draws backend-provided `section_source_surfaces`.
  - No frontend-only section geometry fabrication is needed for the PNG.

Latest real-PNU evidence:

- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- PNU: `1168011800104170004`
- Candidate count: 20
- Unique `mass_shape`: 19
- Section materialized candidates: 6
- Surface candidates: 6
- Surface count: 10
- Parking pass: 0
- Generation time: about 138 seconds

Visual judgment after opening PNG:

- This loop is a visible improvement. `sloped_roof`, `terrace_ribbon`, and
  `diagonal_connector` now read as backend source surfaces in the PNG rather
  than pink overlay strokes.
- Still not final competition-grade design. The geometry remains conservative
  and coarse, but the evidence path is now correctly backend-driven:
  floor plates -> materialized source volumes -> source surfaces -> PNG.
- Next loop should either improve the actual shape grammar operators for more
  architectural massing quality or start parking-feasible generation; do not
  regress back to display-only overlays.
