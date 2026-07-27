# Law-Derived Floor Capacity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make live PNU law and program constraints, rather than a catalog fixture, own MASS floor count and per-floor capacity from authoring through elevation.

**Architecture:** Add one pure floor-capacity planner before geometry authoring. The existing UnitBox/BOOK compiler, shared-floor gate, parking gate, VLM loop, replay, and elevation modules consume the same content-addressed plan without acquiring new planning responsibilities.

**Tech Stack:** Python 3, Django tests, Shapely, Manifold geometry compiler, React/TypeScript/Vitest, Vite browser verification

## Global Constraints

- Preserve one `1/1 UnitBox` primitive authority and homogeneous 4x4 affine provenance.
- Keep Boolean and nonlinear geometry as typed CSG/modifier operations.
- Do not relax BCR, FAR, height, shared-floor, parking, retention, program, or VLM gates.
- Use realized shared-floor geometry as final FAR and parking authority.
- Use at most one new LLM author call and one final VLM call per live smoke iteration.
- Preserve unrelated dirty-worktree changes and stage only MASS flow files.

---

### Task 1: Pure law-derived floor capacity planner

**Files:**
- Create: `backend/design/maas/book_language/floor_capacity_plan.py`
- Create: `backend/design/test_maas_floor_capacity_plan.py`

**Interfaces:**
- Consumes: `LegalGenerationContext`, site-local `Polygon`, building type, target utilization, optional clear-span dimensional context
- Produces: `derive_program_floor_capacity_plan(...) -> dict[str, Any]` with exact sections, selected floor count, height, per-floor targets, status, and `floor_capacity_plan_hash`

- [ ] **Step 1: Write failing planner tests**

Add literal fixtures proving:

- a five-floor hint cannot override a seven- or eight-floor law-derived result;
- legal height clamps the program profile range before measuring capacity;
- shrinking upper legal sections change the selected count and target allocation;
- every target is nonnegative, no greater than its section, and the sum stays under FAR;
- unreachable profile minima return explicit `infeasible`;
- clear-span mode preserves separate mass height and occupiable levels.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python manage.py test design.test_maas_floor_capacity_plan -v 2
```

Expected: import failure for the missing planner module.

- [ ] **Step 3: Implement the pure planner**

Implement:

```python
def derive_program_floor_capacity_plan(
    context: LegalGenerationContext,
    *,
    site_local_utm: Polygon,
    building_type: str,
    target_utilization: float,
    brief_height_cap_m: float | None = None,
    dimensional_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ...
```

For ordinary programs, sample every allowed profile floor at the envelope's
typical floor height, calculate the maximum allowed profile-stack capacity,
and discard terminal sections below the shared occupiable area or clear-depth
minimum before anchoring the target to that maximum. Select the smallest count that can carry
the full feasible capacity—not merely the target GFA—so the unused utilization
share remains available for courts, voids, terraces, and circulation. Allocate
the target proportionally to exact legal floor capacity so the same reserve
ratio remains on every selected plate. Serialize section geometry in the
site-local frame and hash the canonical plan payload.

For clear-span dimensional contexts, preserve the adapted clear height and
explicit occupiable count without converting clear height into ordinary storeys.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```powershell
python manage.py test design.test_maas_floor_capacity_plan -v 2
```

Expected: all planner tests pass.

### Task 2: Make the planner authoritative in BOOK portfolio generation

**Files:**
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `backend/design/maas/book_language/capacity_contract.py`
- Modify: `backend/design/maas/book_language/program_catalog.py`
- Modify: `backend/design/test_maas_book_language.py`
- Modify: `backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Consumes: Task 1 `floor_capacity_plan`
- Produces: one authoritative `height`, `floors`, legal section list, and plan hash passed to candidate generation and capacity alternatives

- [ ] **Step 1: Write failing integration tests**

Assert that a neighborhood portfolio fixture carrying the legacy five-floor
hint uses the planner-selected count, and that `build_feasible_capacity_contract`
copies the exact plan identity and sections rather than resampling a separate
floor authority.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python manage.py test design.test_maas_book_language design.test_maas_geometry_language -v 1
```

Expected: new assertions fail because the catalog still owns five floors and
the capacity contract has no plan identity.

- [ ] **Step 3: Integrate the planner**

Move capacity-policy resolution before candidate authoring, derive the floor
plan after the live legal context exists, and replace local catalog
`height/floors` authority with plan values. Retain catalog numbers only as
explicit historical hints and never as legal truth. Allow
`build_feasible_capacity_contract(..., floor_capacity_plan=plan)` to reuse the
same exact areas and hash.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Task 2 command and require zero failures.

### Task 3: Preserve one plan identity through exact geometry and elevation

**Files:**
- Modify: `backend/design/maas/geometry_language/source_bridge.py`
- Modify: `backend/design/maas/shared_floor_contract.py`
- Modify: `backend/design/maas/agents/elevation_agent/runtime.py`
- Modify: `backend/design/maas/single_execution/pipeline.py`
- Modify: `backend/design/maas/single_execution/replay.py`
- Modify: `backend/design/test_maas_shared_floor_contract.py`
- Modify: `backend/design/test_maas_single_execution.py`

**Interfaces:**
- Consumes: Task 2 plan and exact selected GeometryProgram
- Produces: floorwise matrix stack, shared-floor contract, replay, and elevation evidence all carrying one `floor_capacity_plan_hash`

- [ ] **Step 1: Write failing identity tests**

Assert that floorwise matrix metadata, shared-floor totals, law/parking replay,
and elevation handoff all expose the same nonempty plan hash and selected floor
count.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python manage.py test design.test_maas_shared_floor_contract design.test_maas_single_execution -v 1
```

- [ ] **Step 3: Thread immutable plan evidence through existing boundaries**

Add only serialization and validation at each boundary. Do not let downstream
modules recalculate the selected floor count. Reject a mismatched or missing
hash when a plan-aware execution claims full-flow completion.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Task 3 command and require zero failures.

### Task 4: Advance VLM selection by typed architectural evidence

**Files:**
- Modify: `backend/design/maas/book_language/vlm_review.py`
- Modify: `backend/design/maas/geometry_language/outcome_graph.py`
- Modify: `backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Consumes: hard-pass candidates, exact prior failure hashes, deterministic morphology/program evidence
- Produces: one non-repeated shortlist candidate favoring a public void/threshold and explicit program/section control

- [ ] **Step 1: Write a failing shortlist test**

Build hard-pass candidates where a higher generic capacity-pack score competes
with a frontage-aligned notch/court candidate. Assert that after prior exact
failures the architectural candidate wins without changing any gate threshold.

- [ ] **Step 2: Run the test and verify RED**

Run the exact new test in `design.test_maas_geometry_language`.

- [ ] **Step 3: Add the smallest deterministic tie-break**

Rank only already hard-passed candidates. Use existing evidence for public
void, frontage threshold, program controller, section controller, and
too-box-like risk; do not encode a finished shape or program-specific parcel
coordinates.

- [ ] **Step 4: Run the focused test and regressions**

Require the new test and existing prior-failure filter tests to pass.

### Task 5: Serialize and display honest product evidence

**Files:**
- Modify: `backend/design/maas/geometry_language/executed_archive.py`
- Modify: `backend/design/maas/single_execution/catalog.py`
- Modify: `frontend/src/design/lib/language-system-types.ts`
- Modify: `frontend/src/design/components/book-language-flow/archive-selection-policy.ts`
- Modify: `frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `frontend/src/design/components/book-language-flow/LanguageNetworkCanvas.tsx`
- Modify: focused backend and frontend tests beside those modules

**Interfaces:**
- Consumes: exact execution passport and plan-aware matrix evidence
- Produces: current-run selection and honest status for floors, GFA, FAR, BCR, parking, hashes, VLM, agent collaboration, and elevation

- [ ] **Step 1: Write failing serializer/UI tests**

Assert:

- a current plan-aware run outranks a stale pre-contract accepted run;
- `in_progress` with unevaluated VLM never renders `COMPLETE`;
- selected floor count, height, GFA, FAR, BCR, parking, plan hash, and elevation
  state are visible;
- floor-position 4x4 matrices include provenance.

- [ ] **Step 2: Run backend and frontend focused tests and verify RED**

Use Django focused tests and:

```powershell
npm test -- --run
```

with the exact changed Vitest files.

- [ ] **Step 3: Extend serializers and UI**

Copy existing evidence; do not recompute legal metrics in React. Show authored
BOOK principle and final legal floorwise projection as separate authorities.
Rename any GET-only timeline action from replay to select.

- [ ] **Step 4: Run focused tests and verify GREEN**

Require zero failures and no React console warnings.

### Task 6: Bounded live loop, exact replay, elevation, and publish

**Files:**
- Update: `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- Create: `docs/ai-session-memory/maas-mass-flow/09_2026-07-27_LAW_DERIVED_FLOOR_LOOP.md`

**Interfaces:**
- Consumes: all previous tasks
- Produces: one exact accepted MASS, one bounded elevation proposal, browser proof, memory, commit, and pushed branch

- [ ] **Step 1: Run backend and frontend regressions**

Run the focused MASS suites, UnitBox matrix suite, TypeScript build, and all
changed Vitest suites. Stop on any failure.

- [ ] **Step 2: Run one bounded live MASS iteration**

Reuse the controlled outcome graph so r252-r254 failed hashes are excluded.
Allow at most one new LLM author request and one final VLM request. Do not
generate an elevation unless an exact candidate passes every MASS gate.

- [ ] **Step 3: Replay the selected exact MASS**

Run `execute_maas_single_mass` and assert program hash, geometry hash, plan hash,
floor count, legal/FAR/BCR, and parking identities match the selected archive.

- [ ] **Step 4: Generate one bounded elevation proposal**

Use the frozen selected MASS as the only reference. Verify the elevation
proposal preserves silhouette, height, floor count, setbacks, and identity.

- [ ] **Step 5: Verify `/design/language` on port 5178**

Select the newest run, inspect visible evidence, capture a full screenshot, and
require zero console/request errors.

- [ ] **Step 6: Update memory and publish**

Record exact successes and failures, paid request counts, hashes, PNG paths,
test counts, and remaining gaps. Stage only reviewed MASS-flow files, run
`git diff --cached --check`, commit, and push
`codex/shared-floor-full-flow-smoke`.
