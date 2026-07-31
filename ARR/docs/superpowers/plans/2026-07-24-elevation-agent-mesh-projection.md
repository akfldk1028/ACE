# MASS Elevation Agent Mesh Projection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate six deterministic, hash-bound elevation views from every geometry-ready single MASS and expose them in the existing execution passport graph and frontend.

**Architecture:** A focused Python elevationAgent consumes `CompilationResult`, projects the indexed mesh, writes a condition pack and six PNGs, then returns a typed bundle. The single-MASS pipeline orchestrates it, while passport and frontend remain evidence consumers.

**Tech Stack:** Python 3, Pillow, NumPy, Django tests, React/TypeScript, Vitest.

## Global Constraints

- One `1/1 UnitBox` is the box primitive authority; derived boxes use Matrix4.
- Elevation geometry must match the compiled MASS `program_hash` and `geometry_hash`.
- Elevation output may not modify MASS geometry.
- Exactly one unified graph is used in `/design/language`.
- Unevaluated or missing evidence never counts as passed.

---

### Task 1: Elevation projection runtime

**Files:**
- Create: `ARR/backend/agents/elevationAgent/__init__.py`
- Create: `ARR/backend/design/maas/agents/elevation_agent/contract.py`
- Create: `ARR/backend/design/maas/agents/elevation_agent/projection.py`
- Create: `ARR/backend/design/maas/agents/elevation_agent/runtime.py`
- Keep `ARR/backend/agents/elevationAgent` as the separate shared-agent
  identity/private-memory repository; do not make ARR deployment depend on its
  unpinned nested Git worktree.
- Test: `ARR/backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: `generate_elevation_bundle(compilation, output_root, execution_id)`
- Produces: `ElevationBundle.to_dict()` with six view artifacts and condition evidence.

- [ ] Write a failing test that compiles a box and asserts six missing views.
- [ ] Run `python manage.py test design.test_maas_elevation_agent`.
- [ ] Implement typed contracts, orthographic triangle projection, SHA-bound files, and atomic manifest persistence.
- [ ] Run the test and confirm all artifacts and identities pass.

### Task 2: Single-execution and passport integration

**Files:**
- Modify: `ARR/backend/design/maas/single_execution/pipeline.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_persistence.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_passport.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_activation.py`
- Test: `ARR/backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: generated elevation manifest dictionary.
- Produces: active `elevation:mesh_handoff → elevation:condition_pack → elevation:result` passport path.

- [ ] Write a failing integration test asserting a geometry-ready execution has generated elevation nodes and PNG evidence.
- [ ] Run the focused test and confirm pending nodes cause failure.
- [ ] Invoke elevationAgent after the geometry render and pass evidence into passport persistence.
- [ ] Build active graph nodes only from materialized matching artifacts.
- [ ] Run focused and single-execution regression tests.

### Task 3: Frontend evidence

**Files:**
- Modify: `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/book-language-flow.css`
- Test: `ARR/frontend/test/unit/design/ExecutedMassEvidence.test.tsx`

**Interfaces:**
- Consumes: passport elevation result node evidence with `preview_url` and `views`.
- Produces: graph thumbnail and right-sidebar elevation view strip for the selected MASS.

- [ ] Write a failing component test for elevation result thumbnails.
- [ ] Run the focused Vitest file and confirm failure.
- [ ] Treat elevation result nodes as image-backed and render their six-view evidence in the existing sidebar.
- [ ] Run focused Vitest and TypeScript checks.

### Task 4: End-to-end proof and memory

**Files:**
- Modify: `docs/ai-session-memory/maas-mass-flow/02_CURRENT_STATE.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`
- Create: `docs/playwright/design-route-live-verify/r208-*/`

**Interfaces:**
- Consumes: one new multi-Matrix UnitBox program.
- Produces: execution bundle, MASS PNG, six elevation PNGs, passport, browser screenshot, and recorded hashes.

- [ ] Run all relevant backend and frontend test suites.
- [ ] Execute one new MASS and confirm UnitBox count `1`, Matrix4 count `>=1`, geometry GATE pass, and elevation view count `6`.
- [ ] Verify `/design/language` automatically selects the new run and shows the active elevation path.
- [ ] Update memory with exact statuses and artifact paths.
- [ ] Commit only scoped files and push branch `DK-BB`.
