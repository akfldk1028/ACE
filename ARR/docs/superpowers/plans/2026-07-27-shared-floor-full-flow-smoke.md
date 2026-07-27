# Shared Floor Full-Flow MASS Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject sculptural solids as buildings and execute one identity-bound, low-cost architectural MASS smoke flow.

**Architecture:** Add an independent shared-floor contract between legal generation and all downstream consumers. Preserve mesh section voids, materialize per-floor occupied/legal plates, and require that contract for capacity, parking, product acceptance and elevation.

**Tech Stack:** Python 3, Django tests, Shapely, existing GeometryProgram compiler, existing BOOK/downstream/elevation modules.

## Global Constraints

- Preserve all unrelated dirty work and commit exact files only.
- No paid call before every deterministic hard gate passes.
- Smoke mode permits one paid MASS VLM request and zero GPT Image requests.
- PNU, program hash, geometry hash and floor-contract hash must remain exact.

---

### Task 1: Preserve section voids

**Files:**
- Modify: `backend/design/maas/geometry_language/source_bridge.py`
- Test: `backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Consumes: polygonized mesh-section faces.
- Produces: `_mesh_section_polygon(...)` geometry with nested courtyard/annular voids preserved.

- [ ] Add a failing annular-section regression proving the center remains empty.
- [ ] Run only that test and confirm the current union fills the hole.
- [ ] Filter polygonized hole-filler faces before union.
- [ ] Re-run the regression and nearby source-bridge tests.

### Task 2: Add shared floor contract

**Files:**
- Create: `backend/design/maas/shared_floor_contract.py`
- Create: `backend/design/test_maas_shared_floor_contract.py`

**Interfaces:**
- Consumes: `SourceMass`, `LegalGenerationContext`, site polygon, height, floor count and immutable identity fields.
- Produces: `materialize_shared_floor_contract(...) -> dict[str, Any]`.

- [ ] Add a failing test where a 1 m annular plate is rejected and a five-storey 20 m x 16 m stack passes.
- [ ] Confirm failure because the contract API is absent.
- [ ] Implement per-floor legal/occupied intersections, clear-depth core, support ratio, totals and deterministic hash.
- [ ] Re-run the new test module.

### Task 3: Make capacity and downstream gates consume the contract

**Files:**
- Modify: `backend/design/maas/book_language/capacity_contract.py`
- Modify: `backend/design/maas/book_language/downstream_hard_gate.py`
- Test: `backend/design/test_maas_shared_floor_contract.py`

**Interfaces:**
- Consumes: `shared_floor_contract`.
- Produces: capacity measurement, FAR and parking facility area carrying the same contract hash.

- [ ] Add failing assertions that capacity and parking use contract totals rather than SourceVolume midpoint estimates.
- [ ] Pass/materialize the contract in downstream candidate evaluation.
- [ ] Reject a candidate when its floor contract fails.
- [ ] Run shared-floor, capacity-alternative and focused downstream tests.

### Task 4: Gate single execution and elevation

**Files:**
- Modify: `backend/design/maas/single_execution/pipeline.py`
- Modify: `backend/design/maas/agents/elevation_agent/runtime.py`
- Test: `backend/design/test_maas_single_execution.py`
- Test: `backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: accepted shared-floor evidence in `downstream_evidence`.
- Produces: no product acceptance/elevation before the shared-floor hard pass; exact contract-derived floor guides afterward.

- [ ] Add failing tests for missing/failed contract and exact guide equality.
- [ ] Move elevation behind the downstream acceptance predicate.
- [ ] Pass exact plate heights into the elevation condition pack.
- [ ] Run focused single-execution and elevation tests.

### Task 5: Add bounded one-MASS smoke orchestration

**Files:**
- Create: `backend/design/maas/full_flow_smoke.py`
- Create: `backend/design/management/commands/execute_maas_full_flow_smoke.py`
- Create: `backend/design/test_maas_full_flow_smoke.py`

**Interfaces:**
- Consumes: PNU, program slug, output root, optional one-call LLM author and one-call MASS VLM adapters.
- Produces: one immutable single execution with site/law/capacity/parking/floor/VLM/selector evidence.

- [ ] Add a failing adapter-based flow test proving only one VLM candidate is submitted after deterministic hard pass.
- [ ] Compose existing PNU context, legal generation, candidate generation, shared-floor/downstream gates and single execution.
- [ ] Fail closed when no candidate has a passing shared-floor contract.
- [ ] Run the smoke test with local adapters.

### Task 6: Runtime and frontend verification

**Files:**
- Modify only if runtime evidence exposes a focused bug.
- Update: `docs/ai-session-memory/maas-mass-flow/02_CURRENT_STATE.md`
- Update: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: generated smoke execution.
- Produces: verifiable archive result visible at `/design/language`.

- [ ] Run the local smoke with PNU `1168011800104170004`.
- [ ] Inspect the generated MASS PNG directly and verify floor count/FAR/parking evidence.
- [ ] If local gates pass and credentials are available, execute exactly one MASS VLM request.
- [ ] Start/verify backend and frontend, select the exact run at port 5178, and check images, stages, console and requests.
- [ ] Run all focused backend/frontend tests, update memory, commit exact changes and push.
