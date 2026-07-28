# Floorwise Legal Visual MASS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce at least ten law-checked architectural MASS alternatives whose board, VLM, archive replay, and elevation share one certified projected visual mesh.

**Architecture:** Keep floor plates as capacity/legal authority and project the complete authored indexed mesh through the same floor Matrix4 field. Bind both products with a fail-closed certificate and route all visual consumers to its geometry hash.

**Tech Stack:** Python 3.13, Django tests, Shapely, existing GeometryProgram compiler/Matrix4 helpers, SciPy MILP, Matplotlib/MAAS preview pipeline.

## Global Constraints

- Preserve BaseVolume → BOOK → LLM GeometryProgram/AST provenance.
- Use Matrix4 transforms; do not introduce named completed-building templates.
- Legal/BCR/FAR/parking consume the floor capacity stack.
- Board/VLM/archive/elevation consume one certified projected visual mesh.
- Never accept an empty visual mesh for a source that had an authored profiled mesh.
- Keep hard silhouette distance at `0.10`.
- Deterministic target is at least 10 selected alternatives before paid calls.
- Basement parking without verifier-issued ramp geometry remains fail-closed.
- Do not stage unrelated dirty worktree files.

---

### Task 1: Project and certify the authored visual mesh

**Files:**
- Create: `ARR/backend/design/maas/geometry_language/floorwise_visual_projection.py`
- Modify: `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Test: `ARR/backend/design/test_maas_shared_floor_contract.py`

**Interfaces:**
- Consumes: `SourceMass`, `legal_sections`, materialized floor `matrix4` rows.
- Produces: `project_floorwise_visual_mesh(source, legal_sections, floor_matrices, capacity_plates) -> FloorwiseVisualProjection`.

- [ ] **Step 1: Write failing projection tests**

Add tests that assert identical proxy volumes with centered versus shifted
authored triangle meshes yield non-empty certified surfaces, different visual
hashes, silhouette distance above `0.10`, and unchanged total capacity GFA.
Add an out-of-envelope fixture that returns a failed certificate rather than
empty-success surfaces.

- [ ] **Step 2: Verify RED**

Run:
`C:\Python313\python.exe manage.py test design.test_maas_shared_floor_contract.SharedFloorContractTests.test_floorwise_visual_projection_preserves_authored_mesh design.test_maas_shared_floor_contract.SharedFloorContractTests.test_floorwise_visual_projection_rejects_legal_escape -v 2`

Expected: FAIL because `floorwise_visual_projection` and certified surfaces do
not exist.

- [ ] **Step 3: Implement the minimal projector**

Create immutable `FloorwiseVisualProjection` and
`FloorwiseVisualProjectionCertificate` records. Convert local triangle
vertices to world coordinates, interpolate adjacent 4×4 matrices by normalized
Z, transform vertices, rebuild surfaces, compute a stable visual hash, and
validate finite/non-degenerate triangles plus legal floor-center and boundary
samples.

- [ ] **Step 4: Bind projection into materialization**

After capacity plates and matrices are finalized,
`materialize_floorwise_legal_source` calls the projector. If the input had a
complete authored profiled mesh and certification fails, return `None`.
Otherwise store certified surfaces and certificate metadata. Proxy-only legacy
fixtures remain supported and explicitly record `not_applicable_no_authored_mesh`.

- [ ] **Step 5: Verify GREEN**

Run the two focused tests, then:
`C:\Python313\python.exe manage.py test design.test_maas_shared_floor_contract -v 1`

Expected: all pass.

### Task 2: Route archive replay and elevation to the certified visual mesh

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/executed_archive.py`
- Modify: `ARR/backend/design/maas/geometry_language/elevation_handoff.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `ARR/backend/design/test_maas_export.py`
- Test: `ARR/backend/design/test_maas_flow_regressions.py`

**Interfaces:**
- Consumes: certificate and projected triangle payload from Task 1.
- Produces: canonical `projectedVisualMesh`, `projectedVisualGeometryHash`, and elevation condition packs bound to that hash.

- [ ] **Step 1: Write failing identity test**

Add a selected-artifact fixture with a certified projected mesh. Assert the
board artifact, executed archive replay, and elevation handoff all expose the
same projected visual hash and do not declare the floor-box replay program the
visual authority.

- [ ] **Step 2: Verify RED**

Run the focused export/flow tests and confirm hash fields are missing or point
to the floorwise box compilation.

- [ ] **Step 3: Serialize and replay the projected mesh**

Persist the exact triangle payload and certificate in the artifact.
`compile_executed_mass` validates the payload hash before returning it as visual
geometry. `elevation_handoff` uses the same validated vertices/triangles and
hash. Keep the floorwise GeometryProgram as capacity replay metadata.

- [ ] **Step 4: Verify GREEN**

Run:
`C:\Python313\python.exe manage.py test design.test_maas_export design.test_maas_flow_regressions -v 1`

Expected: all pass.

### Task 3: Close selection and performance regressions

**Files:**
- Modify: `ARR/backend/design/maas/book_language/portfolio_selection.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `ARR/backend/design/test_maas_book_language.py`
- Test: `ARR/backend/design/test_maas_portfolio_contract.py`

**Interfaces:**
- Consumes: certified visual signatures from Task 1.
- Produces: one shared compatibility analysis reused by selector, solver, and diagnostics.

- [ ] **Step 1: Write failing reuse/cardinality tests**

Add a 54-candidate fixture proving compatibility is measured once per unordered
pair, MILP maximizes cardinality before coverage, and diagnostics report the
same matrix used for selection.

- [ ] **Step 2: Verify RED**

Run focused tests and confirm repeated pair evaluation or mismatched selection
diagnostics.

- [ ] **Step 3: Implement shared compatibility analysis**

Introduce a bounded analysis record containing fingerprints, silhouette keys,
pairwise compatibility and nearest distances. Pass it to the exact/MILP/beam
selection and diagnostics instead of recomputing. Retain all hard thresholds
and caps.

- [ ] **Step 4: Verify GREEN**

Run:
`C:\Python313\python.exe manage.py test design.test_maas_book_language design.test_maas_portfolio_contract -v 1`

Expected: all pass.

### Task 4: Deterministic, paid, and frontend end-to-end verification

**Files:**
- Modify: `ARR/backend/design/maas/agents/maas_geometry_agent/memory/MEMORY.md`
- Artifacts: `docs/playwright/design-route-live-verify/book-program-portfolios-*`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: accepted ten-card PNG, bounded paid evidence, live route screenshot, memory record.

- [ ] **Step 1: Run deterministic benchmark**

Run smoke with one bounded replenishment cycle. Require selected count `>=10`,
scope coverage target, legal/parking pass for every selected item, certified
visual mesh for every selected item, and zero admitted near-duplicate pairs.

- [ ] **Step 2: Review PNG**

Open the board at original resolution. Reject it if cards are still generic
terraced boxes, materials are falsely shown at MASS stage, or plan/section
differences are not visually legible.

- [ ] **Step 3: Run bounded paid author/critic pass**

Use one live LLM author request and bounded VLM requests with zero retries.
Never weaken deterministic completeness or mark skipped VLM as pass.

- [ ] **Step 4: Verify live frontend**

Open `http://localhost:5178/design/language`, check console errors, select the
accepted MASS, verify elevation/facade handoff uses its projected visual hash,
and save a screenshot.

- [ ] **Step 5: Final tests and memory**

Run the scoped MAAS suite, compile checks, diff checks, update `MEMORY.md` with
root causes and exact run evidence, then stage only task files, commit, and push
`DK-BB`.

