# Multi-Agent Legal-to-Design Workflow

Updated: 2026-06-23

## Decision From Professor Discussion

The target is not a single-agent tool call. The target is an AutoGen/A2A-style
collaborative workflow where specialized agents review, challenge, and request
deterministic repairs from each other across the full path:

```text
law graph / legal basis
-> datum and site interpretation
-> parking law and parking feasibility
-> MAAS legal mass generation
-> design optimization and graph-driven edits
-> visual/BIM/export evidence
-> final review
```

Agents may reason, debate, route, and request deterministic tools. They must not
invent legal values, mutate mass geometry directly, or declare compliance without
evidence.

## Existing Assets To Reuse

Do not rebuild the agent stack from scratch.

- `AG/` and `AG/autogen_a2a_kit/`: older AutoGen/A2A experiments, team patterns,
  A2A demos, and orchestration references.
- `AG-light/server/agents/`: compact MessageBus, SharedMemory, and collaborative
  agent utilities.
- `AG-light/server/mcp_tools/tools.py`: current MCP entrypoint with
  `arr_maas_evidence` and `arr_maas_review`.
- `ARR/backend/design/maas/agents/`: deterministic local MAAS reviewer contracts
  and A2UI output. This is a contract seed, not true live orchestration yet.
- `ARR/backend/agents/`: Django A2A/worker-agent app. Useful reference, but it
  should not become the source of truth for `/design` geometry.
- `ARR/backend/graph_db/`: Neo4j services, provenance tracking, and graph
  algorithms. Use this for law/evidence/decision relationships, not raw geometry.
- `ARR/backend/law/`: law Graph DB ingestion/search/A2A domain-agent assets.

## Ownership Boundary

Keep the boundaries strict:

```text
ARR backend
  deterministic legal calculators, MAAS geometry, parking validator,
  evidence bundle builder, artifacts, IFC/glTF export

AG-light
  live multi-agent orchestration, MessageBus/SharedMemory, MCP tool wrappers,
  AutoGen-like debate/review workflow

Neo4j / graph_db
  law articles, domain relationships, durable provenance, final/important
  agent decisions, evidence relationships, candidate lineage

gateway
  thin external tool entrypoint; do not put domain logic here
```

## Required Agent Roles

Initial AutoGen-style team:

- `orchestrator_agent`: decomposes user request and coordinates the workflow.
- `law_graph_agent`: queries Neo4j/law search for legal basis and citations.
- `datum_agent`: checks Article 119 datum, road level, adjacent-lot level, and
  Article 86 average plane evidence.
- `parking_agent`: checks Parking Lot Act / Enforcement Decree / Enforcement
  Rule / local ordinance requirements and parking layout feasibility.
- `maas_geometry_agent`: converts edits or graph gestures into MAAS grammar
  operations, then calls ARR deterministic generation/repair tools.
- `design_optimizer_agent`: compares FAR/BCR/usefulness/daylight/design
  objectives and proposes deterministic regeneration requests.
- `visual_qa_agent`: compares API geometry, section/plan artifacts, VWorld
  headed-browser evidence, and BIM/export artifacts.
- `review_agent`: final judge. It returns `pass`, `fail`, or `needs_evidence`
  only from the evidence bundle and reviewer outputs.

## Tool Contract Needed In AG-light

Add these MCP/tool wrappers around ARR endpoints and local graph services:

```text
arr_design_site_context(pnu_or_address)
arr_design_auto_constraints(pnu, site_polygon, building_type)
arr_maas_generate_variants(site_context, constraints, options)
arr_maas_evidence(job_id, design_id)
arr_maas_validate_candidate(job_id, design_id)
arr_parking_requirements(pnu, building_type, floor_area, uses)
arr_parking_layout_check(candidate_geometry, parking_requirements)
arr_maas_apply_operation(job_id, design_id, operation)
arr_visual_evidence(job_id, design_id)
arr_ifc_export(job_id, design_id)
```

The existing `arr_maas_evidence` and `arr_maas_review` are first-pass tools; they
currently fetch/summarize ARR evidence and do not yet run a true multi-agent
review.

## Frontend Visibility Requirement

Agent collaboration must be visible in the design UI, not hidden in server logs.
Reference the existing `AG-frontend/src` implementation:

- `features/playground/LiveAgentFlow.tsx`: connects live execution state to an
  agent graph and message detail panel.
- `features/team-builder/agentflow/AgentFlow.tsx`: React Flow visualization for
  sequential, selector, handoff, debate, and reflection patterns.
- `features/team-builder/agentflow/AgentNode.tsx`: per-agent active state and
  last-message display.
- `features/playground/executionStore.ts`: normalized turn stream
  (`source`, `content`, `timestamp`, `messageType`, token metadata).
- `features/history/components/MessageBubble.tsx`: type-specific rendering for
  text, handoff, tool call, tool result, and chunks.

The `/design` page should include an agent collaboration panel, not only a final
AI answer. Minimum UI:

- team graph:
  `User -> Orchestrator -> Law Graph -> Datum -> Parking -> MAAS Geometry -> Design Optimizer -> Visual QA -> Review`
- active-agent highlight while a run is executing,
- handoff arrows and tool-call/tool-result badges,
- chronological message timeline,
- node click filters messages for that agent,
- decision/evidence summary separated from raw dialogue,
- offline/empty state when AG-light is not running.

Initial design event contract:

```text
agent_message(source, target?, content, timestamp, run_id, metadata?)
handoff(source, target, reason, timestamp, run_id)
tool_call(source, tool, args_summary, timestamp, run_id)
tool_result(source, tool, status, summary, evidence_refs?, timestamp, run_id)
decision(source, status, summary, evidence_refs?, timestamp, run_id)
repair_request(source, target_agent, operation, reason, timestamp, run_id)
```

Frontend implementation direction:

```text
ARR/frontend/src/design/components/AgentCollaborationPanel.tsx
ARR/frontend/src/design/hooks/use-design-agent-events.ts
ARR/frontend/src/design/lib/agent-events.ts
```

The panel should reuse the AG-frontend interaction model, but keep ARR's design
frontend ownership and styling local. Do not import the AG-frontend app directly
unless the projects are intentionally merged later.

## 2026-06-23 ARR `/design` AG-frontend AgentFlow Port

The user explicitly clarified that the multi-agent UI should reuse the existing
AG/AG-frontend work instead of being newly invented. Current implementation
decision:

- `AG/` contains the heavier AutoGen Studio original and A2A experiments.
- `AG-frontend/src/features/team-builder/agentflow/` is the cleaner port of
  AutoGen Studio `AgentFlow` and is the correct reference for ARR.
- ARR must not import the AG-frontend app directly. ARR owns `/design`, so the
  AG-frontend interaction model is adapted into ARR-local modules.

Current ARR-local files:

```text
ARR/frontend/src/design/components/ag-light-flow/AGLightFlow.tsx
ARR/frontend/src/design/components/ag-light-flow/AGLightFlowToolbar.tsx
ARR/frontend/src/design/components/ag-light-flow/layout-generator.ts
ARR/frontend/src/design/components/ag-light-flow/agentnode.tsx
ARR/frontend/src/design/components/ag-light-flow/edge.tsx
ARR/frontend/src/design/components/ag-light-flow/types.ts
ARR/frontend/src/design/components/ag-light-flow/agents/
```

Module boundary:

- `AGLightFlow.tsx`: React Flow provider/rendering, fullscreen state, viewport.
- `AGLightFlowToolbar.tsx`: AG-frontend-style toolbar controls.
- `layout-generator.ts`: ARR-specific selector/handoff graph generation from
  current `/design` evidence reviews/messages and JSON_MODULES agent modules.
- `agentnode.tsx` and `edge.tsx`: existing ARR React Flow node/edge components,
  reused and extended with compact/last-message rendering.
- `agents/*`: one folder per visible JSON_MODULES participant, with shared
  adapter code isolated under `agents/shared`.

Current JSON/team source of truth:

```text
JSON_MODULES/registry.json
  maas_legal_design -> teams/041_MAAS_Legal_Design_Team.json

JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json
  SelectorGroupChat:
    law_graph_agent
    parking_agent
    maas_geometry_agent
    review_agent
```

ARR must not create a second local JSON source for this team. The visible
React Flow graph reads the team participants from `JSON_MODULES/teams/041...`
through `agents/shared/team-config.ts`.

Current ARR visible graph semantics:

```text
User
-> design_orchestrator (Selector/Handoff UI hub)
-> law_graph_agent / parking_agent / maas_geometry_agent / review_agent
-> design_orchestrator report edges
```

`design_orchestrator` is an ARR UI hub representing the SelectorGroupChat
router. It is intentionally not a separate participant in `041_MAAS...json`.

Runtime evidence mapping:

```text
law_graph_agent      <- ARR review/message agent id: law_agent
parking_agent        <- ARR review/message agent id: parking_agent
maas_geometry_agent  <- ARR review/message agent ids: sunlight_agent + datum_agent
review_agent         <- ARR review/message agent id: design_critic
```

This is still AG-light visualization plus deterministic ARR evidence review,
not full AutoGen runtime orchestration. The visible panel now shows:

- JSON_MODULES agent ids in the nodes:
  `law_graph_agent`, `parking_agent`, `maas_geometry_agent`, `review_agent`,
- readable Korean labels: law, parking, mass/datum, final review,
- live bus-derived last messages in the nodes,
- request/report edge labels,
- fullscreen graph mode,
- panel compact mode for the narrow right sidebar.

Verification artifacts:

```text
docs/playwright/design-route-live-verify/ag-light/verify-current-ag-light.cjs
docs/playwright/design-route-live-verify/ag-light/verify-current-ag-light-fullscreen.cjs
docs/playwright/design-route-live-verify/ag-light/ag-light-current-result.json
docs/playwright/design-route-live-verify/ag-light/ag-light-current-fullscreen-result.json
docs/playwright/design-route-live-verify/ag-light/ag-light-json-modules-agent-flow.json
```

Known dev-server note: on WSL-mounted `D:\Data\25_ACE`, Vite HMR sometimes keeps
old `ag-light-flow` modules. If DOM still shows old node text like
`orchestrator / Routes review outcomes`, or if node text omits JSON ids like
`law_graph_agent`, restart `ARR/frontend` dev server on `127.0.0.1:5174` before
judging screenshots.

Latest verified screenshot after the JSON_MODULES wiring:

```text
docs/playwright/design-route-live-verify/ag-light/ag-light-json-modules-agent-flow-1782185181473.png
```

Follow-up review/fix:

- User clarified that the requirement is React Flow visibly present in the
  actual `/design` route, not only a hidden or tiny side visualization.
- `/design` right collaboration workspace width was increased and the panel now
  labels the graph as `AG-light React Flow`.
- `AGLightFlow` default panel height was increased so the graph reads as a
  real workspace, with fullscreen still available.
- React Flow node rendering was fixed by giving nodes stable dimensions.
- React Flow's internal edge DOM proved unstable in the embedded `/design`
  workspace even when `AGLightFlow` state contained 9 edges. ARR now renders the
  visible graph lines through `EdgeOverlay.tsx`, which reads the same
  React Flow node/edge state plus viewport transform. This preserves draggable
  nodes, pan, zoom, fullscreen, and a reliable visual flow.
- Latest Playwright result verified on `/design`:
  - `reactFlowNodes: 6`
  - `reactFlowEdges: 9`
  - `edgePaths: 9`
  - visible JSON agents:
    `law_graph_agent`, `parking_agent`, `maas_geometry_agent`, `review_agent`

Latest verified `/design` screenshot:

```text
docs/playwright/design-route-live-verify/ag-light/design-route-react-flow-1782186313839.png
docs/playwright/design-route-live-verify/ag-light/design-route-react-flow-result.json
```

## 2026-06-23 Default Flow, Direct Agent Commands, And CLI Smoke Test

The current `/design` right-side AI collaboration panel must show the AG-light
flow even before a PNU or candidate is selected. The default state is not a
blank placeholder anymore.

Current ARR frontend modules:

```text
ARR/frontend/src/design/DesignPage.tsx
  owns the left controls, Cesium/main canvas, and collapsible right AI panel.

ARR/frontend/src/design/components/DefaultAgentFlowPanel.tsx
  empty/default workspace before PNU or candidate selection;
  renders the JSON_MODULES-derived AG-light React Flow plus direct command UI.

ARR/frontend/src/design/components/InteractiveDesignPanel.tsx
  candidate/evidence-aware workspace after a design candidate is selected;
  reads AG-light health/log and sends direct agent commands with job/design
  metadata.

ARR/frontend/src/design/components/DirectAgentChatPanel.tsx
  reusable agent-specific command panel. Selecting a React Flow agent node
  changes this command target.

ARR/frontend/src/design/components/ag-light-flow/AGLightFlow.tsx
  React Flow provider/render shell, draggable nodes, pan/zoom, fullscreen,
  test attributes: data-node-count and data-edge-count.

ARR/frontend/src/design/components/ag-light-flow/EdgeOverlay.tsx
  visible edge renderer. It draws the agent handoff/report lines from the same
  node/edge state because embedded React Flow internal edge DOM was unreliable.

ARR/frontend/src/design/components/ag-light-flow/agents/
  one folder per visible JSON_MODULES agent:
    law-graph-agent/
    parking-agent/
    maas-geometry-agent/
    review-agent/
    shared/
```

Current interaction rules:

- `/design` default state renders `User -> design_orchestrator -> agents` before
  PNU input.
- Nodes are draggable and the graph supports pan/zoom controls.
- Selecting an agent node updates `DirectAgentChatPanel` target.
- Direct agent commands are sent to AG-light `/bus/send`.
- The right AI collaboration sidebar can collapse/expand.
- PNU/candidate mode is bus-log driven: AG-light messages are reflected in
  nodes/edges, but full automatic AutoGen-style reasoning orchestration is not
  implemented yet. The current verified layer is a bus-level collaborative
  workflow plus ARR deterministic evidence review.

Current AG-light/ARR/Graph DB boundary:

```text
ARR frontend/backend
  /design UI, deterministic site/legal/parking/MAAS evidence and candidate data

AG-light
  live MessageBus runtime used by direct commands and agent-to-agent smoke tests

JSON_MODULES
  team/agent source of truth:
  JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json

Neo4j Graph DB
  law/evidence/provenance graph; not a raw chat transcript store

AG and AG-frontend
  reference implementations only; do not create another runtime repo from them
  unless the architecture is intentionally changed.
```

CLI added for repeatable agent-to-agent verification:

```text
ARR/backend/design/scripts/ag_light_agent_flow_cli.py
```

CLI behavior:

```text
user
-> design_orchestrator
-> law_graph_agent
-> parking_agent
-> maas_geometry_agent
-> review_agent
-> design_orchestrator
```

It reads `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`, verifies the
required agent ids exist, sends directed messages to `http://127.0.0.1:8200`,
then reads `/bus/log` by `run_id` and reports success rate.

Latest smoke result:

```text
python3 ARR/backend/design/scripts/ag_light_agent_flow_cli.py \
  --runs 5 \
  --json-output docs/playwright/design-route-live-verify/ag-light/ag-light-agent-flow-cli-result.json

runs: 5
success: 5
success_rate: 100.0%
failures: 0
```

Latest default `/design` Playwright check after the edge overlay fix and
visual cleanup:

```text
data-node-count: 6
data-edge-count: 5
visible overlay edge paths: 5
direct agent command panel: visible
parking_agent node click changes DirectAgentChatPanel target: true
```

The visual graph was intentionally simplified after user review. Do not restore
the previous hub-and-spoke return-edge layout unless explicitly requested.

Current visible edge sequence:

```text
user
-> design_orchestrator
-> law_graph_agent
-> parking_agent
-> maas_geometry_agent
-> review_agent
```

Default edge labels are hidden (`showLabels: false`) to reduce clutter. The
toolbar can still re-enable labels.

Verification artifact:

```text
docs/playwright/design-route-live-verify/ag-light/design-clean-react-flow-result.json
```

Note: on 2026-06-23 Playwright high-level screenshot APIs repeatedly timed out
after font loading / element stability on the full `/design` page, likely due to
the heavy map/WebGL layer. DOM verification succeeded and older PNGs remain in
the same folder, but the latest cleaned-flow verification is recorded as JSON.

## What Goes Into Graph DB

Do not store every agent-to-agent chat message in Neo4j.

Raw dialogue is high-volume and mostly operational. Keep raw transcripts in the
MessageBus log, SharedMemory event stream, file artifacts, or a relational/log
store. Graph DB is for durable, queryable reasoning provenance.

Store only summarized or decision-grade objects in Graph DB:

- `AgentReview`: final structured review from one agent for one evidence bundle.
- `EvidenceArtifact`: references to section PNG, VWorld screenshot, JSON bundle,
  IFC/glTF, law result, or parking layout artifact.
- `Decision`: final or intermediate decision that changes workflow state.
- `CandidateLineage`: seed/operator/repair history for a MAAS candidate.
- `RejectedConstraint`: hard rule that blocked a candidate.
- `RequestedRepair`: deterministic repair/regeneration request made by an agent.

Do not store:

- every token/message in a debate,
- transient reasoning text,
- repeated progress chatter,
- full GeoJSON/IFC/glTF payloads.

Instead, store a graph node that points to the durable artifact/log location and
contains a compact summary, hash, status, and source agent.

## Parking Law Must Enter Graph DB

Parking cannot be only a hard-coded calculator. It needs both layers:

This is the first implementation sequence for the multi-agent workflow. Do not
start by making a parking agent invent rules from prompts or by hard-coding only
frontend labels. The order is:

```text
Parking Lot Act JSON/API source
-> Neo4j law graph load
-> article/table relationship verification
-> parking domain/search coverage
-> deterministic ARR parking validator
-> AG-light parking_agent wrapper
-> /design evidence and agent-flow UI
```

1. **Graph DB legal basis**
   - Add/verify Parking Lot Act (`주차장법`), Enforcement Decree
     (`주차장법 시행령`), Enforcement Rule (`주차장법 시행규칙`), and local
     parking ordinances where available.
   - Required refs include:
     - Parking Lot Act Article 19 (`부설주차장의 설치`)
     - Enforcement Decree Article 6 and attached Table 1
     (`부설주차장의 설치대상 시설물 종류 및 설치기준`)
     - Enforcement Rule Article 11 (`부설주차장의 구조ㆍ설비기준`)
   - The graph should store law/article/table refs, amendment/provenance, and
     local ordinance override relationships.
   - Existing source files to start from:
     - `ARR/backend/law/data/api/주차장법_법률.json`
     - `ARR/backend/law/data/api/주차장법_시행령.json`
     - `ARR/backend/law/data/api/주차장법_시행규칙.json`
   - Existing pipeline reference:
     - `ARR/backend/law/STEP/README.md`
     - `ARR/backend/law/STEP/step2_json_to_neo4j.py`
     - `ARR/backend/law/STEP/step3_add_hang_embeddings.py`
     - `ARR/backend/law/STEP/step4_initialize_domains.py`
     - `ARR/backend/law/relationship_embedding/`

2. **Deterministic parking validator**
   - Compute required parking count by use and floor area.
   - Apply local ordinance override when applicable.
   - Check stall dimensions, aisle widths, small-lot exceptions, ramp/access,
     and whether the generated mass/site can actually host the parking.
   - Output structured evidence into `arr.maas.evidence.v0`.

Unknown parking evidence is not pass. If parking law refs or layout feasibility
are missing, final status must be `needs_evidence`.

3. **Parking-aware mass generation**
   - Parking must be a mass-generation constraint, not only a post-generation
     checklist. Many Korean small/medium lots have 1F massing, piloti voids,
     core placement, and ramp feasibility determined by parking.
   - Final required parking count is only known after the candidate has a
     program and floor/use areas. The graph gives the rule; MAAS candidate
     geometry/program gives the metric.
   - Required feedback loop:

```text
PNU/site/context
-> local ordinance and national law rule lookup
-> candidate mass + floor/use area schedule
-> required parking count calculation
-> parking envelope and layout feasibility check
-> repair request if infeasible
-> regenerated candidate with updated parking strategy
```

   - Candidate schema needs a `parking_strategy` field, at minimum:
     - `none`
     - `ground_surface`
     - `piloti_ground`
     - `basement`
     - `semi_basement`
     - `mechanical`
     - `mixed`
   - Piloti parking is not just "empty first floor". The checker must reason
     about:
     - 1F void/covered parking envelope,
     - column grid and usable bay width,
     - vehicle entry width and driveway location,
     - stall size, aisle width, turning radius, and ramp need,
     - pedestrian entrance and vehicle-path separation,
     - accessible parking stall and barrier-free route to entrance/elevator,
     - core placement and lost 1F usable area.
   - Parking layout failure should emit deterministic `RequestedRepair` items,
     for example:
     - increase 1F piloti clear width,
     - move core away from parking aisle,
     - reduce footprint or change podium split,
     - add basement or semi-basement parking,
     - switch to mechanical parking where legally/design-wise acceptable.
   - The parking agent should not mutate geometry directly. It reports evidence,
     infeasible constraints, and repair requests; `maas_geometry_agent` applies
     deterministic operations.
   - Implemented first schema hook:
     - `ARR/backend/design/maas/parking_strategy.py`
     - `legal_mesh_optimizer.py` attaches `parking_strategy`,
       `parking_strategy_candidates`, and `parking_precheck` to each generated
       candidate and `properties.maas_model`.
     - `evidence.py` exposes these fields under `candidate` and
       `mobility.parking`, while keeping final parking status as
       `needs_evidence`.
   - Current strategy hook is a deterministic planning precheck only. It does
     not compute statutory required count, does not pack actual stalls, and does
     not declare layout feasibility.
   - Tests run:
     - `py_compile design/maas/parking_strategy.py design/maas/legal_mesh_optimizer.py design/maas/evidence.py`
     - `manage.py test design.test_maas_export.MaasLegalVariantsTest.test_generates_repaired_legal_diverse_variants design.test_maas_export.MaasEvidenceBundleEndpointTest.test_endpoint_returns_canonical_evidence_bundle`
   - Literature/code review:
     - `docs/ai-session-memory/PARKING_LAYOUT_ALGORITHM_REVIEW.md`
     - `docs/ai-session-memory/parking-layout-clones/transnetlab-parking-lot-design`
     - 2021 grid/MIP paper is treated as foundational baseline only.
     - Primary exact-solver reference is Thomas/Rambha 2025 branch-and-cut code
       and paper; direct import is not recommended because it is CPLEX/global
       config research code, but the `x0/x90/y/z` variable structure and
       connectivity cuts should inform ARR's future solver contract.

### Parking Law Graph Status 2026-06-11

First graph load is complete against Windows Neo4j from WSL using:

```bash
cd /mnt/d/Data/25_ACE/ARR/backend
.venv/bin/python law/scripts/json_to_neo4j.py --json law/data/api/주차장법_법률.json --output law/scripts/neo4j --uri bolt://172.27.80.1:7687 --password ""
.venv/bin/python law/scripts/json_to_neo4j.py --json law/data/api/주차장법_시행령.json --output law/scripts/neo4j --uri bolt://172.27.80.1:7687 --password ""
.venv/bin/python law/scripts/json_to_neo4j.py --json law/data/api/주차장법_시행규칙.json --output law/scripts/neo4j --uri bolt://172.27.80.1:7687 --password ""
.venv/bin/python law/scripts/add_parking_law_semantics.py --uri bolt://172.27.80.1:7687 --password ""
```

Loaded root LAW nodes:

- `주차장법(법률)`
- `주차장법(시행령)`
- `주차장법(시행규칙)`

Verified key nodes and relationships:

- `주차장법(법률)::제5장::제19조`
  `DELEGATES_TO`
  `주차장법(시행령)::제6조`
- `주차장법(시행령)::제6조`
  `DETAILED_BY`
  `주차장법(시행규칙)::제11조`
- `주차장법(시행령)::제6조::1`
  `HAS_APPENDIX`
  `주차장법(시행령)::별표1`
- `parking_regulation` Domain exists with 198 linked nodes.

Added/updated scripts:

- `ARR/backend/law/scripts/json_to_neo4j.py`
  - preserves API-style law roots as `법명(법률/시행령/시행규칙)`;
  - writes type-specific backup files such as `주차장법_시행령_neo4j.json`;
  - stores `law_type`, `law_category`, `base_law_name`, and `agent_id` on unit
    nodes.
- `ARR/backend/law/scripts/add_parking_law_semantics.py`
  - adds parking domain and durable semantic relationships.
- `ARR/backend/law/scripts/add_parking_appendix_rules.py`
  - loader only; reads structured legal rule artifacts from
    `ARR/backend/law/data/structured/parking_appendix_rules.json`;
  - creates unique constraints for `APPENDIX.full_id`,
    `ParkingRequirementRule.rule_id`, and `AccessibleParkingFacilityRule.rule_id`;
  - attaches rule nodes to existing `APPENDIX` nodes and `Domain` with the same
    graph style as the existing law system.
- `ARR/backend/law/scripts/add_parking_ordinance_rules.py`
  - loader only; reads reviewed local ordinance artifacts from
    `ARR/backend/law/data/structured/seoul_parking_ordinance_rules.json`;
  - creates `LocalOrdinance` and `LocalParkingRequirementRule` nodes;
  - connects local rules to national `ParkingRequirementRule` nodes via
    `OVERRIDES`.
- `ARR/backend/law/scripts/verify_parking_law_graph.py`
  - verifies roots, semantic chains, appendix links, domain coverage, unique rule
    ids, parking table values, external delegated housing rule metadata, and
    accessible parking geometry/access/surface/marking values.
  - checks law interpretation details: Parking Enforcement Decree Appendix 1 note
    6 rounding is not `ceil`; graph rows must use
    `appendix_note_6_half_up_total_under_one_zero`.
- `ARR/backend/law/scripts/check_parking_counts.py`
  - verifies actual parking-count outcomes from Graph DB rules across multiple
    PNU jurisdictions and use/area boundary cases.
  - applies local ordinance override by PNU prefix first, then national fallback.
  - current cases cover Gangnam/Songpa/Yongsan and Busan PNU prefixes, 99/100/101/150,
    149/150/225, single-house 50/51/199/200, warehouse 399/400/4200/10000,
    other building 15000, spectator capacity 149/150, accessible parking
    2-4 percent ranges, and row 5 external housing-rule delegation.

Current important gap:

- The existing law.go.kr downloader parses `조문단위` only. It does not yet parse
  the actual attached table body for `주차장법 시행령 [별표 1]`.
- Official appendix PDFs were downloaded as evidence:
  - `docs/legal-sources/parking_law_enforcement_decree_appendix1.pdf`
  - `docs/legal-sources/accessibility_rule_appendix1.pdf`
- Extracted official PDF text is stored next to the PDFs:
  - `docs/legal-sources/parking_law_enforcement_decree_appendix1.txt`
  - `docs/legal-sources/accessibility_rule_appendix1.txt`
- `APPENDIX {full_id: '주차장법(시행령)::별표1'}` is now
  `content_status = structured_seed_loaded` and has 11
  `ParkingRequirementRule` children.
- `APPENDIX {full_id: '장애인ㆍ노인ㆍ임산부 등의 편의증진 보장에 관한 법률(시행규칙)::별표1'}`
  is now `content_status = structured_seed_loaded` and has 4
  `AccessibleParkingFacilityRule` children.
- 서울특별시 조례 is loaded as a local override layer:
  - source text:
    `docs/legal-sources/seoul_parking_ordinance_appendix2.txt`
  - structured artifact:
    `ARR/backend/law/data/structured/seoul_parking_ordinance_rules.json`
  - `LocalOrdinance {ordinance_id: "seoul_parking_ordinance", pnu_prefix: "11"}`
  - 14 `LocalParkingRequirementRule` nodes and 14 `OVERRIDES` relationships
  - examples:
    - 위락시설: national `100㎡/대`, Seoul `67㎡/대`
    - row 2 broad facilities: national `150㎡/대`, Seoul `100㎡/대`
    - 근린생활/숙박: national `200㎡/대`, Seoul `134㎡/대`
    - 창고시설: national `400㎡/대`, Seoul `267㎡/대`
    - 그 밖의 건축물: national `300㎡/대`, Seoul `200㎡/대`
- Latest verification after Seoul ordinance load:
  - `verify_parking_law_graph.py`: `45/45 passed`
  - `check_parking_counts.py`: `23/23 parking cases passed`
- The current rows are calculation-oriented structured artifact data backed by
  official PDFs and extracted text. Do not put these legal values directly in
  loader code. A future OCR/HWP parser should regenerate or confirm the JSON
  artifact before marking it as fully machine-parsed.
- Important interpretation correction from review:
  - Parking appendix rows 1, 2, 3, 4, 6, 7, 8, 9, 10, 11 must not use plain
    `ceil(...)`. Use the appendix note 6 rule: fractional part 0.5 or more counts
    as 1, but if the whole facility's calculated total is under 1 space then it
    counts as 0. Row 5 is excluded and delegates to
    `주택건설기준 등에 관한 규정 제27조제1항`.
  - Accessible parking slope `1/50` is stored as `recommended`, because the
    source text says `할 수 있다` and the appendix note treats such clauses as
    recommendations. No height difference and slip-resistant flat finish remain
    mandatory.
- Do not compute final legal parking count from prompts. Query
  `ParkingRequirementRule`, `AccessibleParkingFacilityRule`, the source
  `APPENDIX`, and local ordinance overrides.
- PNU-level count needs local ordinance coverage. If a PNU starts with `11`, use
  Seoul local rules before national rules. If no matching local ordinance is
  loaded, use national fallback and mark local ordinance coverage as incomplete.
- Row 5 housing/officetel remains delegated to
  `주택건설기준 등에 관한 규정 제27조제1항`. Seoul household/unit minimums are
  stored, but final apartment/officetel counts need that external rule too.
- 서울특별시 조례 별표 2 did not show a single disabled-parking ratio value.
  Keep accessible parking count as the national delegated range `2~4%` until the
  exact local disabled-parking provision is separately sourced and loaded.

Accessible parking update:

- Loaded into Neo4j:
  - `장애인ㆍ노인ㆍ임산부 등의 편의증진 보장에 관한 법률(법률)`
  - `장애인ㆍ노인ㆍ임산부 등의 편의증진 보장에 관한 법률(시행령)`
  - `장애인ㆍ노인ㆍ임산부 등의 편의증진 보장에 관한 법률(시행규칙)`
- Added `accessible_parking_regulation` Domain.
- Verified legal minimum disabled stall size from `주차장법 시행규칙 제3조제1항제2호`:
  - `width_m = 3.3`
  - `length_m = 5.0`
  - Keep any `3.5m x 5.0m` value as a separate project/BF/design recommendation,
    not as the statutory minimum, unless a newer source explicitly changes it.
- Added accessible parking semantic relations:
  - `주차장법(시행규칙)::제3조`
    `DEFINES_STALL_DIMENSION`
    `주차장법(시행규칙)::제3조::1::제2호`
  - `주차장법(시행규칙)::제4조::1::제8호`
    `HAS_THRESHOLD`
    `제8호::가목` for 20-50 spaces -> at least 1 accessible space
  - `주차장법(시행규칙)::제4조::1::제8호`
    `HAS_RATIO_RANGE`
    `제8호::나목` for 50+ spaces -> 2-4 percent by local ordinance
  - `편의증진법 제8조 -> 시행령 제4조 -> 시행규칙 제2조`
  - `편의증진법 시행규칙 제2조제1항 -> APPENDIX 별표1`
- `편의증진법 시행규칙 [별표 1]` now has structured accessible parking rows for:
  - stall geometry: 3.3m x 5.0m; parallel 2.0m x 6.0m;
  - access route: 1.2m minimum effective width, no height difference, separated
    from vehicle path;
  - surface: no height difference, slope at or below 1/50, slip-resistant finish;
  - markings/signage: 1.3m x 1.5m floor mark, 0.5m x 0.58m stall-line mark,
    0.7m x 0.6m sign, 1.5m install height.
- Verification script:
  `ARR/backend/law/scripts/verify_parking_law_graph.py`
  passed `45/45` against `bolt://172.27.80.1:7687`.
- Parking count scenario script:
  `ARR/backend/law/scripts/check_parking_counts.py`
  passed `23/23` against `bolt://172.27.80.1:7687`.
- Important product limitation:
  PNU alone does not determine parking count. The calculator needs jurisdiction,
  facility/use classification, and the metric required by the selected row
  (facility area, holes, bays, capacity, household/unit data, etc.). Current PNU
  handling extracts jurisdiction code only. Seoul metropolitan ordinance is
  loaded for PNU prefix `11`; other local ordinances and the exact accessible
  parking percentage remain incomplete until sourced.

Appendix structured artifact:

- `ARR/backend/law/data/structured/parking_appendix_rules.json`
  - source of truth for the currently structured parking appendix rows;
  - source metadata points to official law.go.kr URLs, PDF paths, TXT paths, and
    effective dates;
  - `source_parse_status = official_pdf_text_extracted_manual_review`.

## Folder Direction

Do not move everything immediately. Add a thin orchestration layer first.

Recommended next structure:

```text
AG-light/server/agents/
  roles/
    law_graph_agent.py
    datum_agent.py
    parking_agent.py
    maas_geometry_agent.py
    design_optimizer_agent.py
    visual_qa_agent.py
    review_agent.py
  workflows/
    legal_design_optimization.py
    parking_review.py
    graph_edit_to_mass.py
  contracts/
    messages.py
    evidence_refs.py

AG-light/server/mcp_tools/
  maas_tools.py
  parking_tools.py
  design_tools.py

ARR/backend/design/maas/
  evidence/
  validators/
    geometry.py
    law.py
    parking.py
    program.py
    visual.py
  export/
    ifc.py
    gltf.py
```

Keep `ARR/backend/design/maas/agents/` as deterministic local reviewer contracts
unless/until the live AG-light workflow supersedes it.

## Workflow Gate

A candidate is reviewable only when all these blocks exist:

- legal Graph DB citations,
- datum evidence,
- parking requirement and parking layout evidence,
- MAAS geometry/floor plates/volume evidence,
- section/plan/VWorld visual evidence,
- summarized agent review trace, with raw dialogue stored outside the graph,
- final decision with unresolved failures and missing evidence listed.

If any hard block is missing, the correct result is `needs_evidence`.

## Parking Design Rule Memory

This section is the current project memory for parking. Re-read this before
touching MAAS parking, law graph parking, or parking agent work.

### Separate The Problems

Do not collapse parking into one scalar.

1. Required count:
   - Source: Graph DB law/ordinance rules.
   - Inputs: PNU jurisdiction, building/facility use, candidate floor/use area
     schedule, and special metrics such as holes, bays, spectator capacity, or
     household/unit data.
   - Output: required standard count plus accessible parking requirement/status.
2. Layout feasibility:
   - Source: MAAS geometry, site polygon, road/frontage geometry, core/column
     obstructions, ramp/entrance conditions, and statutory layout dimensions.
   - Output: pass/fail/needs_evidence plus repair requests.
3. Design repair:
   - Source: parking agent evidence.
   - Actor: `maas_geometry_agent`, not the law graph agent.
   - Output: revised mass/footprint/core/parking strategy.

### Small Attached-Parking Exceptions

For small Korean attached parking, do not assume every stall needs a full
internal 6m aisle module.

- Parking Lot Act Enforcement Rule Article 11(5) matters for small attached
  self-parking lots.
- For total attached self-parking spaces of 8 or fewer:
  - lane width base can be 2.5m, but aisle adjacent to parking stalls still
    depends on parking type;
  - if the site touches a road under 12m with no sidewalk/roadway separation,
    the road may be counted as a driving aisle for stall placement;
  - when using that road-as-aisle exception, the aisle width is counted including
    the road: 6m for perpendicular parking, 4m for parallel parking;
  - road inclusion reaches the centerline, or the opposite road boundary if
    there is no centerline.
- For a sidewalk/roadway separated road of 12m or more:
  - if total spaces are 5 or fewer and parking use is not obstructed, the road
    can be used as the aisle for perpendicular stall placement.
- For 5 or fewer stalls:
  - tandem/serial placement is allowed up to 2 stalls deep from the aisle.
- Entrance width:
  - normal minimum is 3.0m;
  - dead-end road cases may be 2.5m if the local authority recognizes no traffic
    obstruction.
- These are not automatic compliance. They require actual road geometry,
  centerline/opposite-boundary data, sidewalk condition, and local authority
  traffic-obstruction review.

### Code Hook Added

- `ARR/backend/design/maas/parking_layout.py`
  - `evaluate_small_attached_parking_relief(...)` records:
    - road-as-aisle options,
    - tandem parking possibility,
    - entrance-width rule,
    - explicit limitations.
- `ARR/backend/design/maas/parking_strategy.py`
  - `parking_precheck.small_attached_parking_relief` is attached to every MAAS
    candidate.
- Current limitation:
  - this hook is evidence/planning metadata only until Graph DB required count
    is wired into `parking_precheck.required_count`;
  - once required count is known, the same relief logic must be re-evaluated
    with that exact count.

### Test Expectations

Run both layers when changing parking:

```bash
cd /mnt/d/Data/25_ACE/ARR/backend
.venv/bin/python manage.py test design.test_maas_export.MaasLegalVariantsTest.test_generates_repaired_legal_diverse_variants design.test_maas_export.MaasLegalVariantsTest.test_small_attached_parking_relief_tracks_road_aisle_and_tandem_exceptions design.test_maas_export.MaasLegalVariantsTest.test_small_attached_parking_relief_blocks_exceptions_when_space_count_is_too_high design.test_maas_export.MaasEvidenceBundleEndpointTest.test_endpoint_returns_canonical_evidence_bundle
.venv/bin/python law/scripts/check_parking_counts.py --uri bolt://172.27.80.1:7687 --password ""
.venv/bin/python law/scripts/check_parking_to_maas_layout.py --uri bolt://172.27.80.1:7687 --password ""
```

Expected behavior:

- Seoul PNU prefix `11` uses Seoul ordinance overrides.
- Non-Seoul PNUs currently fall back to national rules unless local ordinance is
  loaded.
- PNU alone is insufficient: program/use area is required.
- Small-site layout feasibility must consider:
  - internal parking envelope,
  - road-as-aisle exceptions,
  - tandem/serial parking,
  - accessible stall/route,
  - core/column/ramp conflicts.

### Integration Test Status 2026-06-11

Added:

- `ARR/backend/law/scripts/check_parking_to_maas_layout.py`
- `ARR/backend/law/data/structured/parking_layout_rules.json`
- `ARR/backend/law/scripts/add_parking_layout_rules.py`

This script verifies:

```text
Graph DB rule selection
-> required parking count
-> accessible count status
-> MAAS parking strategy
-> parking_precheck.layout_candidate
-> stall polygon coordinates
```

Current tested cases:

- Gangnam single-house 1-space case:
  - Seoul ordinance row 4;
  - road-as-aisle single-row placement;
  - 1 coordinate stall generated.
- Gangnam row 2 two-space small attached case:
  - Seoul ordinance row 2;
  - road-as-aisle placement;
  - 2 coordinate stalls generated.
- Songpa warehouse 16-space case:
  - Seoul ordinance row 8;
  - accessible count still `needs_local_ordinance_ratio`;
  - internal double-loaded 90-degree placement;
  - 16 coordinate stalls generated.
- Busan warehouse national fallback 0-space case:
  - national rule fallback;
  - layout pressure is zero;
  - `required_parking_spaces=0` must still be treated as a real value.
- Gangnam apartment/officetel delegated rule case:
  - Seoul ordinance row 5;
  - stops before layout with `needs_external_rule`.

Latest results:

- `check_parking_to_maas_layout.py`: `5/5 graph-to-maas layout cases passed`.
- `check_parking_counts.py`: `23/23 parking cases passed`.
- `verify_parking_law_graph.py`: `49/49 passed`.
- MAAS/Django focused parking tests: `7/7 OK`.

Graph DB parking layout rules now loaded:

- `ParkingLayoutRule` count: 7.
- Source article: `주차장법(시행규칙)::제11조`.
- Key structured rules:
  - `parking_layout_rule_attached_self_parking_under_8`
  - `parking_layout_rule_small_attached_lane_width`
  - `parking_layout_rule_road_as_aisle_undivided_under_12m`
  - `parking_layout_rule_road_as_aisle_sidewalk_12m_perpendicular_under_5`
  - `parking_layout_rule_tandem_under_5`
  - `parking_layout_rule_attached_entrance_width`
  - `parking_layout_rule_no_obstacle_between_road_and_stall`
- The rules are connected by:
  - `(:JO {full_id: '주차장법(시행규칙)::제11조'})-[:HAS_LAYOUT_RULE]->(:ParkingLayoutRule)`
  - `(:ParkingLayoutRule)-[:DERIVED_FROM]->(source law unit)`
  - `(:ParkingLayoutRule)-[:BELONGS_TO_DOMAIN]->(:Domain {domain_id: 'parking_regulation'})`

Bug fixed during test:

- `parking_strategy.py` previously used an `or` chain for required parking
  count, so `required_parking_spaces = 0` was treated as missing.
- It now uses first-non-`None` semantics, so zero-space legal fallback cases are
  preserved.

## Next Session Handoff 2026-06-11

The parking/legal foundation is now good enough to move to multi-agent
collaboration. Do not redo the parking-law loading work unless verification
fails.

### Current Stable Modules

- Graph DB law/parking loaders:
  - `ARR/backend/law/scripts/add_parking_appendix_rules.py`
  - `ARR/backend/law/scripts/add_parking_ordinance_rules.py`
  - `ARR/backend/law/scripts/add_parking_layout_rules.py`
- Graph DB validation:
  - `ARR/backend/law/scripts/verify_parking_law_graph.py`
  - `ARR/backend/law/scripts/check_parking_counts.py`
  - `ARR/backend/law/scripts/check_parking_to_maas_layout.py`
- MAAS parking code:
  - `ARR/backend/design/maas/parking_layout.py`
  - `ARR/backend/design/maas/parking_strategy.py`
  - `ARR/backend/design/maas/evidence.py`
- Algorithm/literature memory:
  - `docs/ai-session-memory/PARKING_LAYOUT_ALGORITHM_REVIEW.md`
  - local clone:
    `docs/ai-session-memory/parking-layout-clones/transnetlab-parking-lot-design`

### Maintenance Notes

- Keep law interpretation data out of hardcoded service logic where possible.
  Structured legal facts belong in JSON seed files and Graph DB loader scripts.
- Keep deterministic geometry logic in `ARR/backend/design/maas/parking_layout.py`.
- Keep strategy selection and MAAS property attachment in
  `ARR/backend/design/maas/parking_strategy.py`.
- Do not claim legal compliance from `layout_candidate`; it is a deterministic
  first candidate, not the final MIP/grid solver.
- Preserve zero values. Do not use `a or b` for legal quantities where `0` is a
  valid result.

### Next Priority: Multi-Agent Collaboration Layer

Use the existing general `AG` implementation as the primary reference. Do not
invent a new multi-agent runtime from scratch.

Important existing implementation:

- `D:/Data/25_ACE/AG`
  - AutoGen Studio launcher:
    - `AG/start_autogen.py`
    - `AG/start_with_key.ps1`
  - AutoGen Studio team/gallery scripts:
    - `AG/create_pipeline_team.py`
    - `AG/add_a2a_to_gallery11.py`
    - `AG/add_a2a_wrappers_to_gallery11.py`
    - `AG/add_a2a_agents_to_gallery11.py`
  - Existing AutoGen-style team pattern:
    - `SelectorGroupChat`
    - `RoundRobinGroupChat`
    - staged agents such as `insights_agent`, `deep_research_agent`,
      `spec_writer_agent`, `planner_agent`, `coder_agent`,
      `qa_reviewer_agent`, `qa_fixer_agent`
  - Existing A2A wrapper style:
    - tools are Python code strings using JSON-RPC `message/send`;
    - agent calls are routed to local ports.
  - Existing law-domain agent implementation:
    - `AG/agent/law-domain-agents/`
    - includes `law_orchestrator.py`, `domain_agent_factory.py`,
      `domain_manager.py`, `law_search_engine.py`, `graph_algorithms.py`,
      `server.py`, `a2a_executor.py`.
- `JSON_MODULES`
  - modular team/agent/pattern definitions used by the general AG ecosystem.
  - relevant team files:
    - `JSON_MODULES/teams/033_Auto-Claude A2A Protocol Team.json`
    - `JSON_MODULES/teams/036_Auto-Claude + A2A Full Team.json`
    - `JSON_MODULES/teams/037_Auto-Claude Sequential Pipeline.json`
    - `JSON_MODULES/teams/038_Land_Regulation_Analysis_Team.json`
    - `JSON_MODULES/teams/039_Land_Swarm_Analysis_Team.json`
    - `JSON_MODULES/teams/040_Land_Light_Team.json`
- `AG-light`
  - use as a slim integration surface only:
    - `AG-light/server/main.py`
    - `AG-light/server/agents/message_bus.py`
    - `AG-light/server/agents/shared_memory.py`
    - `AG-light/server/mcp_tools/tools.py`
  - It already has a Message Bus, SharedMemory, and MCP tools, but the richer
    AutoGen/A2A team implementation lives in general `AG`.

Therefore the next MAAS legal-design collaboration should be implemented as an
AutoGen/A2A-style team in the general `AG`/`JSON_MODULES` style first, then
optionally exposed through AG-light tools/bus if needed.

Do not put raw agent dialogue in the law Graph DB. Runtime conversation belongs
to AutoGen/AG message history or logs. Graph DB should store legal sources and
structured artifacts only.

Recommended first workflow:

```text
law_graph_agent
-> parking_agent
-> maas_geometry_agent
-> design_optimizer_agent
-> review_agent
```

Agent responsibilities:

- `law_graph_agent`
  - reads PNU/use/floor-area inputs;
  - queries Graph DB parking requirement and layout rules;
  - emits `EvidenceArtifact` objects with law refs and selected rules.
- `parking_agent`
  - computes required parking count from Graph DB results;
  - calls MAAS parking layout candidate generation;
  - emits `RejectedConstraint` or `RequestedRepair` when capacity/layout fails.
- `maas_geometry_agent`
  - applies geometry repairs only;
  - examples: reserve piloti void, move core, reduce/split footprint, add
    basement/semi-basement, switch mechanical.
- `design_optimizer_agent`
  - regenerates candidate variants using repair requests as constraints.
- `review_agent`
  - summarizes pass/fail/needs_evidence and creates the final decision object.

Graph DB persistence rule:

- Store durable outputs:
  - `AgentReview`
  - `EvidenceArtifact`
  - `Decision`
  - `CandidateLineage`
  - `RejectedConstraint`
  - `RequestedRepair`
- Do not store raw agent chat as first-class legal truth.
- Raw dialogue can be logged outside Graph DB or attached as debug artifacts if
  needed, but Graph DB should prefer structured decisions and citations.

### Frontend Next Step

Use `D:/Data/25_ACE/AG-frontend/src` as reference for showing agent-to-agent
conversation and progress. The ARR frontend should expose:

- agent timeline,
- current agent status,
- evidence artifacts,
- requested repairs,
- candidate lineage,
- final decision state.

The frontend should not merely show chat. It should show why the candidate
changed and which legal/design constraint caused the change.

### Solver Next Step After Multi-Agent Skeleton

After the AG-light workflow can call parking tools end-to-end, implement the
real optimization solver:

```text
ParkingGridInput
-> grid rasterization
-> x0/x90/y/z variables
-> driveway connectivity constraints
-> OR-Tools or python-mip backend
-> ParkingGridSolution
```

Use the 2025 `transnetlab/parking-lot-design` clone as architecture reference,
not as direct imported code.

### Implementation Started 2026-06-11

Started the actual AG/AG-light connection work. This is no longer just a plan.

Added AG-light MCP tools in:

- `AG-light/server/mcp_tools/tools.py`

Tool count changed from 22 to 26. New tools:

- `arr_parking_graph_verify`
  - runs ARR `law/scripts/verify_parking_law_graph.py`;
  - expected latest result: `49/49 passed`.
- `arr_parking_count_check`
  - runs ARR `law/scripts/check_parking_counts.py`;
  - expected latest result: `23/23 parking cases passed`.
- `arr_parking_to_maas_layout_check`
  - runs ARR `law/scripts/check_parking_to_maas_layout.py`;
  - expected latest result: `5/5 graph-to-maas layout cases passed`.
- `arr_maas_parking_layout_candidate`
  - calls ARR `design.maas.parking_layout.generate_parking_layout_candidate`;
  - returns stall polygon coordinates for deterministic first parking candidate.

AG-light tool implementation notes:

- Uses `ARR_BACKEND_DIR`, default `/mnt/d/Data/25_ACE/ARR/backend`.
- Uses `ARR_PYTHON`, default `/mnt/d/Data/25_ACE/ARR/backend/.venv/bin/python`.
- Uses Neo4j defaults:
  - `bolt://172.27.80.1:7687`
  - user `neo4j`
  - password from `NEO4J_PASSWORD`
- This keeps AG-light as a slim adapter surface. The legal/MAAS logic remains in
  ARR.

Added general AG/JSON_MODULES team:

- `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`
- registered in `JSON_MODULES/registry.json` as `maas_legal_design`.

Team type:

- `autogen_agentchat.teams.SelectorGroupChat`

Agents:

- `law_graph_agent`
  - verifies/cites parking law Graph DB.
- `parking_agent`
  - runs parking count checks and GraphDB-to-MAAS layout checks.
- `maas_geometry_agent`
  - converts parking/legal failures into MAAS geometry repair operations.
- `review_agent`
  - emits structured EvidenceArtifact/RejectedConstraint/RequestedRepair/
    Decision summaries and terminates.

Validation run:

```bash
cd /mnt/d/Data/25_ACE
python -m json.tool JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json
python JSON_MODULES/validate_json.py
cd /mnt/d/Data/25_ACE/AG-light
server/.venv/bin/python -m py_compile server/mcp_tools/tools.py server/main.py
cd /mnt/d/Data/25_ACE/AG-light/server
.venv/bin/python - <<'PY'
import asyncio
from mcp_tools import tools
async def main():
    print(await tools.arr_maas_parking_layout_candidate(
        required_spaces=2,
        envelope_width_m=5,
        envelope_depth_m=10,
        road_width_m=6,
        has_sidewalk_separation=False,
        timeout=30,
    ))
    print(await tools.arr_parking_to_maas_layout_check(timeout=120))
asyncio.run(main())
PY
```

Latest validation results:

- `JSON_MODULES/validate_json.py`: `102 PASS, 0 FAIL`.
- AG-light py_compile: passed.
- AG-light import test from `AG-light/server`: passed.
- `arr_maas_parking_layout_candidate`: returned `status=pass`,
  `placement_mode=road_as_aisle_single_row`, `provided_spaces=2`.
- `arr_parking_to_maas_layout_check`: returned `5/5 graph-to-maas layout cases
  passed`.

Remaining next step:

- Wire this team into the existing general `AG` AutoGen Studio/gallery import
  path if needed, following the style of `AG/create_pipeline_team.py` and
  `AG/add_a2a_to_gallery11.py`.
- Then expose the agent timeline/evidence/repair state in the frontend.

### Commit Scope 2026-06-11

Commit/push is important. Do not use broad `git add .` because the repository
has many unrelated dirty/untracked files. Stage only the legal parking and
AG-light/JSON_MODULES integration files.

Expected commit contents:

- ARR parking law/Graph DB:
  - `ARR/backend/law/data/structured/parking_appendix_rules.json`
  - `ARR/backend/law/data/structured/seoul_parking_ordinance_rules.json`
  - `ARR/backend/law/data/structured/parking_layout_rules.json`
  - `ARR/backend/law/scripts/add_parking_appendix_rules.py`
  - `ARR/backend/law/scripts/add_parking_ordinance_rules.py`
  - `ARR/backend/law/scripts/add_parking_layout_rules.py`
  - `ARR/backend/law/scripts/check_parking_counts.py`
  - `ARR/backend/law/scripts/check_parking_to_maas_layout.py`
  - `ARR/backend/law/scripts/verify_parking_law_graph.py`
- ARR MAAS parking:
  - `ARR/backend/design/maas/parking_layout.py`
  - `ARR/backend/design/maas/parking_strategy.py`
  - `ARR/backend/design/maas/evidence.py`
  - `ARR/backend/design/test_maas_export.py`
- Official/legal/research evidence:
  - `docs/legal-sources/`
  - `docs/ai-session-memory/PARKING_LAYOUT_ALGORITHM_REVIEW.md`
  - `docs/ai-session-memory/parking-layout-clones/transnetlab-parking-lot-design/`
  - `docs/ai-session-memory/MULTI_AGENT_LEGAL_DESIGN_WORKFLOW.md`
- AG/AG-light integration:
  - `AG-light/server/mcp_tools/tools.py`
  - `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`
  - `JSON_MODULES/registry.json`
  - `JSON_MODULES/validation_report.json`

Latest pre-commit verification:

- `verify_parking_law_graph.py`: `49/49 passed`
- `check_parking_counts.py`: `23/23 parking cases passed`
- `check_parking_to_maas_layout.py`: `5/5 graph-to-maas layout cases passed`
- MAAS focused Django tests: `7/7 OK`
- `JSON_MODULES/validate_json.py`: `102 PASS, 0 FAIL`
- AG-light MCP import and direct parking tool calls: passed
