# 25_ACE Portfolio — 6-Page Layout & Evidence Map

Updated: 2026-07-14  
Layout files: `1_1.jpg`–`1_6.jpg`  
Current MAAS checkpoint: `v58`

이 문서는 현재 포트폴리오 레이아웃에 들어간 다이어그램을 실제 프로젝트 구현과 연결하고, 각 텍스트 영역에 어떤 내용을 써야 하는지 기록한다. 현재 JPG 안의 영문 본문은 임시 문구이므로 사실 근거로 사용하지 않는다.

## Portfolio-wide narrative

> A typed address becomes a parcel key, the parcel key retrieves site and legal evidence, and specialized agents translate those constraints into executable massing alternatives. The system does not ask an LLM to declare compliance: deterministic legal, parking, capacity, and geometry gates remain binding while language and visual agents propose and critique design alternatives.

한국어 서사:

> 주소를 필지 식별자로 변환하고, 필지와 법규 근거를 검색한 뒤, 전문 에이전트가 제약조건을 실행 가능한 매스 대안으로 번역한다. LLM은 법규 통과를 판정하지 않으며, 법규·주차·용적·형상 검증은 결정론적 hard gate가 담당한다.

## Global factual baseline

### Legal graph snapshot used in the portfolio

- Maximum hierarchy: `LAW → JANG → JEOL → JO → HANG → HO → MOK`.
- Main relations: `CONTAINS`, `NEXT`, `CITES`.
- Portfolio graph snapshot: `31,126 nodes / 31,063 relationships / 58 regulations`.
- `HANG` nodes and `CONTAINS` relationship contexts use 3,072-dimensional embeddings.
- Search implementation includes exact, full-text, vector, relationship search, RRF/RNE-style expansion, and MMR diversity handling.
- The portfolio snapshot and the smaller ARR runtime snapshots must not be mixed in one metric sentence. When using `31,126 / 31,063`, explicitly call it the expanded portfolio graph snapshot.

### Current real-site MAAS checkpoint

- Artifact: `maas-neighborhood-vlm-a2a-v58-pnu-1168011800104170004-access-step-replenish`.
- PNU: `1168011800104170004`.
- Live VWorld parcel area: `264.13 m²`.
- Parcel dominant axis: approximately `28.99°`.
- Verified access: east frontage, shared length `14.01 m`.
- Estimated adjacent road-parcel width: `37.48 m`; contextual evidence only, not permit-final certification.
- Search: `4,356 raw → 2,834 clean → 2,594 capacity-pass`.
- VLM frontier: `30 parents + 27 critic children`.
- Live architect authoring: `29 candidates`, no deterministic fallback repair.
- Final research board: `20/20`, normalized FAR target `13/8`, zero near-duplicate pairs.
- Language groups: carved `5`, continuous `4`, stepped `3`, bridge/interlock `3`, folded `3`, cluster `2`.
- Status: `technical_pass`, `visual_status=review_required`.
- Real permit-law/parking projection: `not_run` in v58.
- Do not describe v58 as competition-grade, permit-approved, or final parking-approved.

### Canonical MAAS agent flow

```text
design_orchestrator
  → law_graph_agent
  → parking_agent
  → llm_architect_agent
  → massdsl_agent
  → maas_geometry_agent
  → grammar_critic_agent
  → review_agent
```

The three-agent fan-out icons in the current layout are a simplified collaboration symbol. They are not the exact current MAAS topology.

---

## Page 1 — Cover / Design Automation

Layout file: `1_1.jpg`

### Current visual layout

- Upper-left: main title.
- Center-left: subtitle, project type, category, and date.
- Upper-right: short project introduction.
- Lower half: urban hero image with a highlighted stepped building.

### Page role

Introduce the project as a complete address-to-massing system. The hero image is a vision image, not measured v58 evidence.

### Recommended text slots

- Main title: `ARCHITECTURAL DESIGN AUTOMATION`
- Subtitle: `From Address to Evidence-Backed Massing`
- Project type: `Personal Research & Development`
- Scope line: `Legal Knowledge Graph · Multi-Agent Design · Generative Massing`
- Date: `July 2026`

### Intro copy direction

Explain the full problem in one paragraph:

1. Architectural feasibility begins with a parcel, but the evidence is fragmented across address data, land information, legal clauses, parking rules, and geometry constraints.
2. This project connects those sources into a traceable design pipeline.
3. The result is not one opaque AI image but a reviewed set of executable massing alternatives with provenance.

### Evidence boundary

- The highlighted building can represent the design ambition or future architectural outcome.
- Do not call it the direct final output of v58 unless it is replaced with an actual generated and verified candidate.

---

## Page 2 — Legal Knowledge Graph

Layout file: `1_2.jpg`

### Current visual layout

- Left: large headline and system summary.
- Upper-middle: embedded legal node schema example.
- Lower-left: seven-level statute hierarchy.
- Middle: `CONTAINS`, `NEXT`, and `CITES` diagrams.
- Right: full Neo4j graph cluster visualization.
- Bottom: four numbered explanation blocks.

### Page role

Show why Korean architectural law is represented as a graph instead of a flat text archive.

### Recommended headline

`THE LAW IS A GRAPH`

Optional subhead:

`A seven-level statute structure turned into searchable design evidence.`

### Left summary content

- A typed address resolves to PNU and parcel context.
- The relevant legal context is retrieved from a Neo4j knowledge graph.
- Legal evidence is passed forward as structured constraints and source references.
- The graph informs the design process but does not itself generate geometry.

### Bottom caption mapping

1. `7-LEVEL STATUTE TREE`
   - `LAW → JANG → JEOL → JO → HANG → HO → MOK`.
   - Intermediate levels may be absent in some statutes.

2. `CONTAINS / NEXT / CITES`
   - `CONTAINS`: parent-child hierarchy and relationship-context embedding.
   - `NEXT`: same-level sequence traversal.
   - `CITES`: cross-law reference paths.

3. `HYBRID RETRIEVAL`
   - Exact, CJK full-text, vector, relationship-context, RRF/RNE, and MMR stages.

4. `CLUSTERED LEGAL FIELD`
   - The graph visualization exposes legal neighborhoods and cross-references rather than treating clauses as isolated documents.

### Evidence status

This page is directly grounded in the project schema and search implementation. It may be presented as an implemented system.

### Metric rule

If the page uses `31,126 nodes / 31,063 relationships`, label it as the expanded portfolio graph snapshot. Do not combine that number with the separate 18-law ARR runtime snapshot in the same caption.

---

## Page 3 — Parcel Intelligence & A2A Design Context

Layout file: `1_3.jpg`

### Current visual layout

- Left: large `A2A PROTOCOL` headline and introduction.
- Lower-left: user → host agent → specialist agents diagram.
- Upper-right: stacked GIS-layer diagram.
- Lower-middle: legal envelope cube over the site.
- Lower-right: supporting paragraph.

### Page role

Explain how a parcel becomes shared design context before mass generation.

### Recommended headline

`PARCEL INTELLIGENCE`

Optional secondary label:

`PNU · VWORLD · A2A CONTEXT`

### Active site inputs that may be claimed

- Typed address and PNU resolution.
- Live VWorld parcel boundary.
- Parcel area and local metric coordinate frame.
- Dominant parcel axis.
- Neighbor-road lookup and verified frontage segment.
- Zoning/land information used by the legal path.
- NGII/local elevation path where available.
- Map/aerial context used by the interface.

### GIS diagram qualification

The current generic layer stack also labels `Land cover`, `Hydrography`, `Geo Names`, and `Structure`. These are not all confirmed inputs to the current v58 author/compiler path.

Use one of these treatments:

- Rename the figure `EXTENSIBLE GEOSPATIAL CONTEXT` and visually emphasize only active layers; or
- Replace the generic stack with the actual v58 input set: parcel boundary, road frontage, parcel axis, zoning/legal context, elevation/datum, and map image.

### Agent diagram qualification

- A2A-compatible agents and agent cards are implemented.
- The exact MAAS flow is a staged handoff across seven domain agents plus the orchestrator.
- The current three-agent fan-out icon is acceptable only as a simplified symbol.
- Do not describe the current MAAS flow as an unrestricted full mesh.

### Legal envelope cube

The cube may represent deterministic site constraints such as BCR, FAR, height, setback, sunlight, and parking requirements. State that these values are solver inputs and hard gates, not LLM judgments.

---

## Page 4 — Graph-to-Massing Generation

Layout file: `1_4.jpg`

### Current visual layout

- Left: headline, summary, and simplified agent diagram.
- Upper-right: sixteen abstract mass-operation icons.
- Middle-right: explanatory paragraph.
- Lower-right: ten orange mass candidate thumbnails.

### Page role

Show how architectural language becomes executable geometry and a diverse candidate population.

### Recommended headline

`GRAPH TO MASSING`

Optional subhead:

`Typed design operations compiled inside a legal envelope.`

### Mass-operation diagram mapping

The abstract icons correctly represent the design-space/operator layer. They can be described through implemented verbs and principles such as:

- split and bridge,
- stack and shift,
- taper and stepback,
- carve, notch, courtyard, and atrium,
- fold and sloped roof,
- cluster and array,
- bend and continuous ribbon.

Do not describe the icons as sixteen fixed building templates. The project goal is typed, site-conditioned graph operations rather than named coordinate presets.

### Candidate thumbnail qualification

- The ten orange thumbnails are valid historical MAAS outputs.
- They predate the current v58 real-PNU board.
- Use the label `EARLY LEGAL-MASSING POPULATION` if retaining them.
- If the page is intended to show the current result, replace or supplement them with the v58 20-candidate board.

### Current generation evidence available for copy

- `4,356` raw candidates evaluated.
- `2,834` passed geometry cleanliness.
- `2,594` passed capacity filtering.
- `30` VLM parents and `27` critic children were reviewed.
- `20` final candidates survived with zero near duplicates.

### Required honesty statement

The current system is a clean mass-stage baseline. Several candidates remain conservative and rectilinear, and variable-width continuous roof fields remain an active representation goal.

---

## Page 5 — Downstream Design Development

Layout file: `1_5.jpg`

### Current visual layout

- Left: headline, summary, and simplified agent diagram.
- Upper-right: multiple facade/elevation alternatives.
- Center: selected mass axonometric.
- Middle-right: explanatory text.
- Lower-middle: a matrix of plan alternatives.
- Lower-middle/right: simplified final mass/section diagram.

### Page role

Present downstream modules that develop a selected mass into plan and facade studies.

### Recommended headline

`MASSING TO DESIGN DEVELOPMENT`

Optional subhead:

`Parallel plan, facade, and projection studies built from structured geometry.`

### Implemented modules represented on this page

- MAAS source volumes and source surfaces.
- AUA-derived floor-plan/packing experiments.
- Facade-plane extraction.
- Generated facade image and directional panel assets.
- Projection manifest and textured mesh/glTF export path.
- Cesium facade-wall material application in the VWorld design interface.

### Critical evidence boundary

These modules exist in the repository, but the current evidence does not prove that the exact v58 candidate automatically produced every plan and facade image shown on this page in one uninterrupted run.

Use this wording:

> The selected mass becomes a shared geometric base for parallel plan and facade studies.

Do not use this wording:

> v58 automatically completed the final floor plans and facade design.

### Facade qualification

- Generated facade imagery and per-direction facade panel assets exist.
- The exact number and provenance of the ten facade thumbnails must be stated only if their source run is identified.
- Do not imply permit-ready construction elevations.

### Plan qualification

- The plan grid may represent packing/design alternatives.
- Do not imply automatic BIM/IFC completion.
- Three.js/Cesium geometry is not automatically equivalent to a validated BIM/IFC model.

---

## Page 6 — Shared Memory, Runtime & Interface

Layout file: `1_6.jpg`

### Current visual layout

- Upper-left: agent/Neo4j query → Shared Memory Bus diagram.
- Lower-left: headline and short explanatory lines.
- Upper-right: two text blocks.
- Lower-right: actual application interface shown inside a device frame.

### Page role

Close the portfolio with the collaboration infrastructure and the user-facing system.

### Recommended headline

`SHARED MEMORY, LIVE INTERFACE`

Optional subhead:

`Evidence persists across agents, tools, and design review stages.`

### Implemented infrastructure that may be claimed

- `AG-light/server/agents/message_bus.py`: agent message bus.
- `AG-light/server/agents/shared_memory.py`: shared decisions, events, and persistent JSON memory.
- Send, broadcast, conversation log, decision store, and event publication endpoints.
- MCP tool mounting in the AG-light FastAPI server.
- MAAS agent folders, cards, contracts, rules, and versioned memory.
- Durable accepted-candidate archive and geometry-keyed VLM caches in the current research loop.

### Runtime qualification

The Shared Memory Bus is real collaboration infrastructure, but v58 does not route every internal operation through AG-light SharedMemory. The current real-site loop also uses direct Python orchestration, accepted graph archives, JSON artifacts, and atomic VLM caches.

Describe this diagram as:

> collaboration and persistence infrastructure

Do not describe it as:

> the exact step-by-step v58 runtime trace

### Interface image

The device-frame screenshot may be described as the actual user-facing design interface that connects address/PNU input, regulatory analysis, map context, and design results.

### Closing message

End on traceability rather than autonomous authorship:

> Every candidate remains connected to its parcel, legal evidence, authored graph, geometry compilation trace, and review status.

---

## Cross-page terminology

Use consistently:

- `Architectural Design Automation`
- `Parcel Intelligence`
- `Legal Knowledge Graph`
- `A2A Agent Handoff`
- `MassDSL / Component Graph`
- `Deterministic Hard Gates`
- `Source Geometry`
- `Visual Critic`
- `Durable Candidate Archive`
- `Design Development`

Avoid or qualify:

- `fully autonomous architect`
- `permit approved`
- `parking approved`
- `competition-grade final design`
- `all GIS layers are active inputs`
- `full-mesh MAAS runtime`
- `automatic BIM/IFC completion`
- `VLM decides legal compliance`
- `Neo4j generates the building geometry`

## Source references

- `docs/portfolio/NEO4J_GRAPH_SCHEMA.md`
- `docs/portfolio/PORTFOLIO_4PAGE_CAPTIONS.md`
- `docs/ai-session-memory/MAAS_MEMORY_INDEX.md`
- `docs/ai-session-memory/MAAS_VISUAL_FAILURE_HANDOFF_20260710.md`
- `docs/ai-session-memory/AGENT_FOLDER_STANDARD.md`
- `docs/ai-session-memory/MAAS_AGENT_FOLDER_BOUNDARIES.md`
- `ARR/backend/design/maas/HANDOFF.md`
- `ARR/backend/design/maas/program_massing/vlm_a2a.py`
- `AG-light/server/main.py`
- `AG-light/server/agents/message_bus.py`
- `AG-light/server/agents/shared_memory.py`

