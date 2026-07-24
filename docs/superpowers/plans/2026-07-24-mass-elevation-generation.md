# MASS + Elevation Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate ten genuinely distinct fresh MASS executions, bind one deterministic elevation condition pack and at most one paid image-generated facade proposal to each MASS, and verify every mapping in the single `/design/language` graph.

**Architecture:** A new bounded batch orchestrator will compose the existing normalized synthesis, BOOK projection, program projection, compiler/GATE, single-execution persistence and elevationAgent modules without adding logic to `portfolio_benchmark.py`. The existing provider-neutral aesthetic adapter is reused behind an elevation-specific bridge so image generation occurs only after a hash-bound MASS and condition pack exist. Frontend evidence reads proposal artifacts from the selected MASS passport; it never mixes proposals between executions.

**Tech Stack:** Python 3.13, Django, Pillow, existing recursive Geometry DSL/compiler, OpenAI Python SDK 1.109.1, React/TypeScript/Vitest, Playwright.

## Global Constraints

- Every MASS begins with one `1/1 UnitBox`; affine variation is represented by Matrix4.
- Geometry dimensions come from normalized seed/host parameter space, never parcel/world-coordinate literals.
- Ten accepted MASSes must have ten distinct program hashes and ten distinct geometry hashes.
- Geometry GATE and elevation condition-pack generation occur before any paid image request.
- Paid image generation is limited to one request per accepted MASS and ten requests total.
- No automatic paid retry.
- Image generation may change facade materials, openings, rhythm and presentation only; it may not change the MASS silhouette, height, roofline, courtyard, bridge, setback or cantilever.
- MASS generation does not claim VLM use. Image-provider execution and optional VLM evidence remain separately identified.
- Portfolio scoring and portfolio VLM are out of scope.
- Existing unrelated workspace changes and archives must not be staged.

---

### Task 1: Freeze the ten-MASS generation contract

**Files:**
- Create: `ARR/backend/design/maas/fresh_batch.py`
- Test: `ARR/backend/design/test_maas_fresh_batch.py`

**Interfaces:**
- Produces: `FreshMassSpec`, `fresh_mass_specs()`, `author_fresh_mass_candidates(spec, *, building_type, variation_offset)`.
- Consumes: `synthesize_architectural_programs`, `compose_program_with_book_operations`, `book_sentence_variants`, `apply_book_projection_to_geometry_program`, `project_program_requirements`.

- [ ] **Step 1: Write the failing specification test**

```python
def test_fresh_mass_specs_cover_ten_distinct_architectural_relations(self):
    specs = fresh_mass_specs()
    self.assertEqual(len(specs), 10)
    self.assertEqual(len({item.family for item in specs}), 10)
    self.assertEqual(len({item.book_verbs for item in specs}), 10)
    self.assertTrue(all(item.scope_label == "1/1" for item in specs))
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python manage.py test design.test_maas_fresh_batch.FreshMassBatchTests.test_fresh_mass_specs_cover_ten_distinct_architectural_relations -v 2`

Expected: FAIL because `design.maas.fresh_batch` does not exist.

- [ ] **Step 3: Add the minimal typed specification**

Implement ten grammar-level families: curved bar, courtyard, radial/cross, stepped setback, tapered/leaning tower, diagonal cut, attached volume, profiled span, split bridge and nested offset. Store intent/operator/BOOK choices only; do not store geometry dimensions.

- [ ] **Step 4: Verify GREEN**

Run the exact test from Step 2.

Expected: PASS.

---

### Task 2: Add bounded unique batch execution

**Files:**
- Modify: `ARR/backend/design/maas/fresh_batch.py`
- Create: `ARR/backend/design/management/commands/generate_maas_fresh_batch.py`
- Modify: `ARR/backend/design/test_maas_fresh_batch.py`

**Interfaces:**
- Produces: `generate_fresh_mass_batch(output_root, batch_id, building_type, count=10, image_provider=None) -> dict`.
- Persists: `<output_root>/<execution-id>/...` through `execute_single_mass`.
- Persists batch evidence: `<output_root>/<batch-id>.batch.json`.

- [ ] **Step 1: Write failing tests for uniqueness and paid-call ceiling**

```python
def test_batch_accepts_ten_unique_geometry_hashes_before_image_generation(self):
    result = generate_fresh_mass_batch(self.root, "batch-test", "neighborhood living", count=10)
    self.assertEqual(result["accepted_count"], 10)
    self.assertEqual(len(set(result["program_hashes"])), 10)
    self.assertEqual(len(set(result["geometry_hashes"])), 10)
    self.assertEqual(result["paid_image_request_count"], 0)
```

Also assert every execution mode is `fresh_synthesis`, every accepted passport has `geometry_gate=passed`, and rejected duplicate/GATE-failed candidates never enter the archive.

- [ ] **Step 2: Run the batch test and verify RED**

Run: `python manage.py test design.test_maas_fresh_batch.FreshMassBatchTests.test_batch_accepts_ten_unique_geometry_hashes_before_image_generation -v 2`

Expected: FAIL because the orchestrator function is missing.

- [ ] **Step 3: Implement bounded author/compile/replenish**

For each spec, derive the variation cursor from `sha256(batch_id + spec.id)` and try a bounded sequence of candidate programs. Apply BOOK and use projection, compile and GATE locally, reject duplicate program/geometry hashes, then call `execute_single_mass(..., execution_mode="fresh_synthesis")` only for accepted programs. Stop with an explicit incomplete manifest when ten valid candidates cannot be found; never copy an old AST.

- [ ] **Step 4: Add the management command**

Command:

```powershell
python manage.py generate_maas_fresh_batch `
  --batch-id r223-mass-elevation `
  --count 10 `
  --building-type "neighborhood living"
```

The default command performs no image request. `--image-provider gpt-image` is an explicit later stage.

- [ ] **Step 5: Verify GREEN and regression**

Run:

```powershell
python manage.py test design.test_maas_fresh_batch design.test_maas_single_execution -v 1
```

Expected: all tests PASS.

---

### Task 3: Bridge elevationAgent to the existing aesthetic provider

**Files:**
- Create: `ARR/backend/design/maas/agents/elevation_agent/facade_strategy.py`
- Create: `ARR/backend/design/maas/agents/elevation_agent/image_proposal.py`
- Modify: `ARR/backend/design/maas/agents/elevation_agent/__init__.py`
- Modify: `ARR/backend/design/maas/agents/elevation_agent/runtime.py`
- Modify: `ARR/backend/design/maas/aesthetic/adapters/openai_image.py`
- Modify: `ARR/backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Produces: `select_facade_strategy(program, compilation) -> dict`.
- Produces: `generate_elevation_image_proposal(bundle, mass_preview, *, adapter, strategy) -> dict`.
- Reuses: `RenderedReference`, `AestheticProvider`, `OpenAIImageAdapter`.

- [ ] **Step 1: Write failing strategy and provider-binding tests**

Assert that facade strategy is derived from measured aspect/height/operator path, uses no world coordinates, differs across representative MASS families, and that a fake provider receives the selected MASS preview plus matching execution/program/geometry hashes exactly once.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python manage.py test design.test_maas_elevation_agent -v 2
```

Expected: FAIL because facade strategy and image proposal interfaces do not exist.

- [ ] **Step 3: Implement facade strategy**

Return one primary system per MASS from a bounded material vocabulary: high-performance glass, deep mineral reveals, vertical fins, horizontal shading, perforated metal, terracotta, exposed concrete or hybrid. The selection is a deterministic function of geometry metrics, facade aspect ratios and executed operators; material selection never mutates geometry.

- [ ] **Step 4: Implement provider-neutral proposal generation**

Build a reference record from the exact `mass.png` and elevation bundle. Include the six deterministic views, condition-pack path, hash identity, immutable-geometry prompt and material strategy. Invoke the injected adapter once. Write `elevation/proposals/alt-01/proposal.json`; hash any generated PNG and expose `/design/maas/single-executions/<id>/elevation-proposals/alt-01/`.

- [ ] **Step 5: Correct OpenAI adapter evidence**

Use the configured image-edit model through `client.images.edit` with the selected MASS reference. Record provider, model, size, prompt hash, input image SHA-256, output SHA-256, request ID when supplied by the API and usage when supplied. Never fabricate a response ID or usage. Keep retries at zero.

- [ ] **Step 6: Verify GREEN**

Run the command from Step 2.

Expected: all elevation tests PASS without making a real provider request.

---

### Task 4: Persist image proposal in the MASS passport and graph

**Files:**
- Modify: `ARR/backend/design/maas/single_execution/pipeline.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_activation.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_passport.py`
- Modify: `ARR/backend/design/views.py`
- Modify: `ARR/backend/design/urls.py`
- Modify: `ARR/backend/design/test_maas_single_execution.py`

**Interfaces:**
- Extends: `execute_single_mass(..., elevation_image_adapter=None)`.
- Serves: `GET /design/maas/single-executions/<id>/elevation-proposals/alt-01/`.
- Graph path: `result:mass -> elevation:mesh_handoff -> elevation:condition_pack -> elevation:image_agent -> elevation:proposal`.

- [ ] **Step 1: Write failing persistence/API/graph tests**

Inject a fake adapter and assert one image call, matching hashes in passport evidence, proposal API HTTP 200, and active causal edges from the selected MASS to the proposal. Assert the no-adapter path remains `not_evaluated` and performs zero calls.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python manage.py test design.test_maas_single_execution -v 2
```

Expected: FAIL because no proposal endpoint or graph node exists.

- [ ] **Step 3: Implement pipeline and graph integration**

Run image generation after deterministic elevation bundle creation and before passport creation. Store failed provider calls truthfully as `failed` or `not_configured`; do not mark them passed. Add graph nodes only from persisted evidence.

- [ ] **Step 4: Implement immutable image serving**

Resolve the proposal artifact inside the selected execution directory, reject traversal, and return immutable PNG headers.

- [ ] **Step 5: Verify GREEN**

Run the command from Step 2.

Expected: all tests PASS.

---

### Task 5: Render MASS-specific proposal evidence in the frontend

**Files:**
- Modify: `ARR/frontend/src/design/lib/language-system-types.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/LanguageNetworkCanvas.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/book-language-flow.css`
- Create: `ARR/frontend/src/design/components/book-language-flow/elevation-proposal.test.ts`

**Interfaces:**
- Reads: `passport.elevation_evidence.image_proposal`.
- Displays: technical six-view evidence and one `ALT 01` proposal for the selected MASS only.

- [ ] **Step 1: Write failing evidence-mapping tests**

Assert that proposal extraction rejects a geometry-hash mismatch and accepts an artifact whose execution/program/geometry hashes match the selected MASS.

- [ ] **Step 2: Verify RED**

Run:

```powershell
npx vitest run src/design/components/book-language-flow/elevation-proposal.test.ts
```

Expected: FAIL because the extractor does not exist.

- [ ] **Step 3: Implement typed extraction and UI**

Add a focused helper that binds proposal to selected MASS identity. Render the image, strategy, model and status below deterministic views. Add `ELEVATION IMAGE AGENT` and `ELEVATION ALT` graph labels without creating a second graph.

- [ ] **Step 4: Verify GREEN and type safety**

Run:

```powershell
npx vitest run src/design/components/book-language-flow/elevation-proposal.test.ts
npm run type-check
```

Expected: both commands PASS.

---

### Task 6: Generate ten MASSes, then make at most ten paid image requests

**Files:**
- Generate: `docs/ai-session-memory/maas-service-cache/single-executions/r223-*`
- Generate: `docs/ai-session-memory/maas-service-cache/single-executions/r223-mass-elevation.batch.json`

**Interfaces:**
- Uses: `generate_maas_fresh_batch`.
- Provider: existing `OpenAIImageAdapter`.

- [ ] **Step 1: Run local MASS-only generation**

Run:

```powershell
python manage.py generate_maas_fresh_batch `
  --batch-id r223-mass-elevation `
  --count 10 `
  --building-type "neighborhood living"
```

Expected: ten accepted, ten unique program hashes, ten unique geometry hashes, zero paid requests.

- [ ] **Step 2: Inspect all ten MASS PNGs**

Create a contact sheet for inspection only. Reject and regenerate any fragmented, inverted, toy-like or perceptually duplicate MASS before paid calls.

- [ ] **Step 3: Run the explicit image stage**

Run:

```powershell
python manage.py generate_maas_fresh_batch `
  --batch-id r223-mass-elevation `
  --resume `
  --image-provider gpt-image `
  --image-limit 10
```

Expected: no more than ten provider requests and no retry. A missing API key or provider error is recorded, not hidden.

- [ ] **Step 4: Inspect each generated ALT**

Compare every ALT against its source `mass.png` and deterministic views. Record `needs_review` when silhouette preservation is uncertain; never claim law/site/VLM approval from an image.

---

### Task 7: Browser verification, memory and delivery

**Files:**
- Modify: `docs/playwright/design-route-live-verify/verify-maas-single-graph.cjs`
- Generate: `docs/playwright/design-route-live-verify/r223-mass-elevation-frontend.png`
- Modify: `docs/ai-session-memory/maas-mass-flow/02_CURRENT_STATE.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/04_VALIDATION_GAPS.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`
- Modify: `ARR/backend/agents/elevationAgent/memory/MEMORY.md`

- [ ] **Step 1: Verify backend and frontend suites**

Run:

```powershell
python manage.py test design.test_maas_fresh_batch design.test_maas_elevation_agent design.test_maas_single_execution -v 1
npx vitest run src/design/components/book-language-flow/archive-selection-policy.test.ts src/design/components/book-language-flow/execution-mode.test.ts src/design/components/book-language-flow/elevation-proposal.test.ts
npm run type-check
```

Expected: zero failures.

- [ ] **Step 2: Verify the live browser**

Open `http://127.0.0.1:5175/design/language`. Confirm the latest ten MASS cards load, click all ten, verify the right panel shows the matching technical elevation and ALT only, confirm the selected graph path reaches image agent/proposal, and collect console/page errors.

- [ ] **Step 3: Update durable memory**

Record actual generated IDs/hashes, paid request count, model, failures and truthful remaining gaps. Do not claim VLM when only the image model ran.

- [ ] **Step 4: Review, commit and push exact paths**

Run `git diff --check` on scoped files, inspect staged paths, commit only this feature, push branch `DK-BB`, and preserve unrelated working-tree content.
