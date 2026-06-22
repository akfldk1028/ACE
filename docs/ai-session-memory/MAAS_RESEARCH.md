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
