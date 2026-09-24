# MASS Continuous Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore continuous non-staircase MASS production, persist versioned run memory, and resume C53-B01 through the publishable twenty-member gate.

**Architecture:** Repair the shared fixed-pose legal CSG fitter before spending another provider request. Add an append-only version snapshot boundary around the existing run-state and numbered memory system, then resume the persisted C53 request, package its response through the existing trusted manifest importer, and run the unchanged production gates.

**Tech Stack:** Python 3.13, Django tests, Shapely, manifold3d, Codex CLI OAuth, existing MAAS BOOK/geometry pipeline.

## Global Constraints

- One canonical UnitBox and one authored global Matrix4 per LLM AST.
- One fixed-pose site Matrix4; no coded pose/aspect ladder and no per-floor recentering.
- Continuous authored visual mesh; law floor plates are analysis/GFA authority only.
- Capacity utilization is at least 0.70.
- No deterministic geometry fallback, rejected-AST hand repair, gate relaxation, or premature canonical count.
- Preserve existing dirty-worktree changes.

---

### Task 1: Fixed-pose legal CSG recovery

**Files:**
- Modify: `ARR/backend/design/test_maas_source_bridge_legal_reflow.py`
- Modify: `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Modify: `ARR/backend/design/test_task7a_floorwise_csg_target_fit.py` only where an old assertion no longer represents the approved continuous-flow contract

**Interfaces:**
- Consumes: `_matrix_fit_polygon_to_host(source, host, target_area, target_center, allow_legal_csg_projection, allow_pose_reflow, fit_evidence)`.
- Produces: the maximum sampled legal intersection at a fixed pose, exact target recovery when reachable, and bounded evidence for non-monotonic intersections.

- [ ] Add a real concave-host regression asserting target-area recovery without changing pose.
- [ ] Run the focused test and confirm the existing 5.97964 m2 result fails against the hand-derived 6.0 m2 target.
- [ ] Make the smallest sampling/bracketing correction that retains the best sampled lower and refines around every target crossing.
- [ ] Run source-bridge, Task7A, Matrix4, identity, and agent-authorship tests.
- [ ] Align obsolete test fixtures with the complete production certificate shape; do not change production behavior to satisfy partial mocks.

### Task 2: Append-only version memory

**Files:**
- Create: `ARR/backend/design/maas/agents/maas_geometry_agent/version_memory.py`
- Create: `ARR/backend/design/test_maas_version_memory.py`
- Modify: `ARR/backend/design/maas/geometry_language/run_state.py`

**Interfaces:**
- Produces: `write_version_snapshot(output_dir: Path, *, version_id: str, parent_version_id: str, stage: str, payload: dict) -> Path`.
- Snapshot path: `<output_dir>/memory/<version_id>.json`; an existing version may only be rewritten when its content is byte-identical.
- Run state records `version_memory_path` and `parent_version_id` without credentials.

- [ ] Write tests for append-only creation, conflicting rewrite rejection, hash recording, and bounded credential-free payloads.
- [ ] Run the tests and confirm failure because the interface does not exist.
- [ ] Implement atomic snapshots and bind them to run-state lifecycle transitions.
- [ ] Run version-memory and run-state regression tests.

### Task 3: Resume and preserve C53-B01 author supply

**Files:**
- Create: `ARR/.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v31-c53-b01/resume_c53_b01.py`
- Reuse: `provider-prompt.txt`, `provider-output-schema.json`, `exact-oauth-request.json`, `eligible-path-scan.json`
- Reuse: `package_static_codex_mass_v11.py` and `agent_authored_supply.py`

**Interfaces:**
- Produces immutable `provider-response.json`, `provider-attempt-result-v2.json`, trusted manifest, admission JSON, and a version snapshot with SHA-256 identities.

- [ ] Add a dry-run test proving all four shared counts are exactly twenty and all artifact hashes match the persisted request.
- [ ] Implement resume logic that refuses an altered request and saves raw output before parsing.
- [ ] Invoke exactly one OAuth batch retry.
- [ ] Parse and compile all returned programs; package only a complete valid batch.
- [ ] If the provider is unavailable, preserve typed failure evidence and stop without fake candidates.

### Task 4: Production gates and deficit replenishment

**Files:**
- Reuse: `benchmark_maas_book_program_portfolios.py`
- Reuse: `portfolio_benchmark.py`
- Add only targeted regression tests if a production stage exposes a new general bug.

**Interfaces:**
- Consumes the trusted C53 manifest/admission contract.
- Produces sequential per-candidate law, capacity, semantic, parking, mesh, identity, VLM, and diversity evidence.

- [ ] Verify live PNU, regulation, sunlight, parking graph, law graph, and VLM prerequisites before paid work.
- [ ] Run the twenty-program production flow and persist every rejection by version.
- [ ] Replenish only typed deficits through fresh LLM-authored programs.
- [ ] Do not freeze a stepped, identity-collapsed, detached-semantic, illegal, or sub-0.70 candidate.

### Task 5: Publishable twenty and visual inspection

**Files:**
- Reuse: production summary, archive boards, and publishable-20 manifest paths in the selected output version directory.
- Modify numbered MASS current state/failure ledger only after evidence exists.

**Interfaces:**
- Produces a passing `maas-book-programs-summary.json`, publishable-20 manifest, exact twenty-member board PNG, and final version snapshot.

- [ ] Run the independent publishable-20 audit.
- [ ] Verify twenty exact LLM-authored rows, twenty final VLM passes, all law/parking/mesh hashes, and complete pair certificates.
- [ ] Inspect the combined PNG for staircase repetition and visible family collapse.
- [ ] Update `08_FAILURE_LEDGER.md`, `09_CURRENT_STATE.md`, and manifest timestamp with measured results only.
- [ ] Run the complete affected regression suite and report exact pass/fail counts.
