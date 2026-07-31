# Radial MASS and Roof-Safe Architectural Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a connected common-hub radial MASS, produce a roof-safe architectural render from one paid image call, and show that render in the selected-MASS frontend without contaminating the MASS-only archive.

**Architecture:** A focused fresh-family contract authors and validates the radial phenotype before the normal compiler/GATE pipeline. A separate image panel-role contract protects the top view and records deterministic roof-guard evidence after the provider response. The existing passport and single causal graph remain authoritative; the frontend only presents identity-matched render evidence already stored in that passport.

**Tech Stack:** Python 3, Django tests, Pillow, recursive MAAS Geometry AST, manifold3d compiler, TypeScript, React, Vitest, Vite, Playwright browser verification.

## Global Constraints

- Every produced solid starts from the single normalized `1/1 UnitBox` authority and 4x4 affine transforms.
- BOOK is executable geometry language, not image evidence.
- No parcel/world-coordinate constants are introduced into the MASS program.
- The paid image adapter is called exactly once per requested MASS and never retries.
- Existing r227 artifacts are immutable.
- The bottom frontend gallery remains MASS-only.
- Render, elevation, VLM and legal evidence must match the selected execution, program and geometry hashes.
- One causal graph is retained; no parallel render or facade graph is added.
- Render output is design evidence, not geometry or legal authority.

---

### Task 1: Common-Hub Radial Family Contract

**Files:**
- Create: `ARR/backend/design/maas/fresh_family_contracts.py`
- Modify: `ARR/backend/design/maas/fresh_batch.py`
- Test: `ARR/backend/design/test_maas_fresh_batch.py`

**Interfaces:**
- Consumes: `FreshMassSpec`, deterministic `variation_offset`, `GeometryProgramBuilder`, `compile_geometry_program`.
- Produces: `build_family_contract_program(spec, variation_offset) -> GeometryProgram | None`.
- Produces: `family_phenotype_issues(program, spec) -> tuple[str, ...]`.
- `generate_fresh_mass_batch` invokes the focused author before general synthesis and rejects candidates whose phenotype issues are non-empty.

- [ ] **Step 1: Write the failing radial AST contract test**

```python
def test_radial_family_contract_uses_one_unitbox_common_hub_and_radial_array(self):
    spec = next(item for item in fresh_mass_specs() if item.spec_id == "radial-cross")
    program = build_family_contract_program(spec, variation_offset=317)
    self.assertIsNotNone(program)
    operators = [node.operator for node in program.topological_nodes()]
    self.assertEqual(operators.count("box"), 1)
    self.assertIn("radial_array", operators)
    self.assertIn("union", operators)
    self.assertNotIn("bend", operators)
    self.assertEqual(family_phenotype_issues(program, spec), ())
```

- [ ] **Step 2: Run the focused test and verify RED**

Run from `ARR/backend`:

```powershell
python manage.py test design.test_maas_fresh_batch.FreshMassBatchTests.test_radial_family_contract_uses_one_unitbox_common_hub_and_radial_array -v 2
```

Expected: import failure because `fresh_family_contracts` does not exist.

- [ ] **Step 3: Implement the minimal relative radial author**

Create a program with:

```python
wing = builder.add(
    "primitive",
    "box",
    parameters={"width": wing_length, "depth": wing_depth, "height": height},
    semantic_role="wing",
)
aligned = builder.add(
    "transform",
    "translate",
    inputs=(wing,),
    parameters={"vector": [0.0, -wing_depth / 2.0, 0.0]},
)
wings = builder.add(
    "pattern",
    "radial_array",
    inputs=(aligned,),
    parameters={
        "count": wing_count,
        "total_angle_degrees": 360.0 * (wing_count - 1) / wing_count,
        "pivot": [0.0, 0.0, 0.0],
    },
    semantic_role="wing",
)
hub = builder.add(
    "primitive",
    "box",
    parameters={"width": hub_size, "depth": hub_size, "height": height},
    semantic_role="hub",
)
centered_hub = builder.add(
    "transform",
    "translate",
    inputs=(hub,),
    parameters={"vector": [-hub_size / 2.0, -hub_size / 2.0, 0.0]},
)
root = builder.add(
    "boolean",
    "union",
    inputs=(centered_hub, wings),
    semantic_role="main",
)
```

All values are normalized ratios derived deterministically from
`variation_offset`; the builder rewrites every authored box to transforms of
one UnitBox. Metadata records `book_recursive_projection.ordered_verbs` as
`["rotate", "merge"]` and identifies `radial_array + common hub union` as the
core lowering.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Write the failing compiled phenotype test**

```python
def test_radial_family_contract_compiles_as_one_connected_manifold(self):
    spec = next(item for item in fresh_mass_specs() if item.spec_id == "radial-cross")
    program = build_family_contract_program(spec, variation_offset=319)
    compilation = compile_geometry_program(program)
    self.assertEqual(compilation.status, "compiled")
    self.assertEqual(compilation.metrics["component_count"], 1)
    self.assertTrue(compilation.metrics["watertight"])
    self.assertTrue(compilation.metrics["manifold"])
```

- [ ] **Step 6: Verify RED, add compiled checks to the phenotype validator, and verify GREEN**

Run the focused test. It must initially fail on the missing compiled phenotype
evidence, then pass after `family_phenotype_issues` checks the radial node/hub
topology and the ordinary compilation GATE checks connected, watertight,
manifold geometry.

- [ ] **Step 7: Integrate the contract into bounded fresh generation**

For `radial-cross`, author the focused candidate for each bounded cycle. For
all other specs, retain the existing synthesis and BOOK projection path.
Apply the same archive program/geometry hash checks and the same
`execute_single_mass` pipeline to both paths. Never relabel a rejected generic
candidate as radial.

- [ ] **Step 8: Run fresh-batch regression tests**

```powershell
python manage.py test design.test_maas_fresh_batch -v 2
```

Expected: all tests pass and ten accepted geometries remain unique.

- [ ] **Step 9: Commit the radial contract**

```powershell
git add ARR/backend/design/maas/fresh_family_contracts.py ARR/backend/design/maas/fresh_batch.py ARR/backend/design/test_maas_fresh_batch.py
git commit -m "fix(maas): enforce common-hub radial mass phenotype"
```

---

### Task 2: Top-Panel Roof Semantic Guard

**Files:**
- Create: `ARR/backend/design/maas/agents/elevation_agent/panel_roles.py`
- Modify: `ARR/backend/design/maas/agents/elevation_agent/image_proposal.py`
- Modify: `ARR/backend/design/maas/aesthetic/adapters/openai_image.py`
- Test: `ARR/backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Produces: `locked_sheet_panel_roles() -> tuple[dict[str, object], ...]`.
- Produces: `roof_mass_mask(reference_path, panel_roles) -> Image.Image`.
- Produces: `apply_roof_semantic_guard(generated_path, locked_path, mass_mask_path, panel_roles) -> dict[str, object]`.
- `generate_elevation_image_proposal` stores panel roles and presentation kind.
- `OpenAIImageAdapter.generate` records `roof_semantic_guard` metadata after one provider response.

- [ ] **Step 1: Write the failing panel-role mask test**

```python
def test_roof_role_mask_selects_only_bottom_left_top_panel_mass_pixels(self):
    mask = roof_mass_mask(reference_path, locked_sheet_panel_roles())
    self.assertEqual(mask.getpixel((25, 75)), 255)
    self.assertEqual(mask.getpixel((75, 75)), 0)
    self.assertEqual(mask.getpixel((25, 25)), 0)
```

Use a 100×100 synthetic four-panel sheet with orange MASS pixels in every
quadrant. Expected initial failure: module/function missing.

- [ ] **Step 2: Implement explicit normalized panel roles**

Use normalized sheet regions:

```python
(
    {"role": "isometric", "bounds": [0.0, 0.0, 0.5, 0.5], "surface": "facade_and_roof"},
    {"role": "opposite",  "bounds": [0.5, 0.0, 1.0, 0.5], "surface": "facade_and_roof"},
    {"role": "top",       "bounds": [0.0, 0.5, 0.5, 1.0], "surface": "roof_only"},
    {"role": "front",     "bounds": [0.5, 0.5, 1.0, 1.0], "surface": "facade"},
)
```

The mask intersects the `top` region with the existing color-derived MASS
mask. It does not use parcel or world coordinates.

- [ ] **Step 3: Verify the panel-role mask test passes**

```powershell
python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTest.test_roof_role_mask_selects_only_bottom_left_top_panel_mass_pixels -v 2
```

- [ ] **Step 4: Write the failing synthetic facade-grid suppression test**

Create a provider-like top panel containing alternating dark/light vertical
and horizontal grid lines. Assert:

```python
evidence = apply_roof_semantic_guard(...)
self.assertEqual(evidence["status"], "applied")
self.assertGreater(evidence["changed_pixel_count"], 0)
self.assertLess(evidence["after_grid_score"], evidence["before_grid_score"])
self.assertEqual(outside_top_pixels_after, outside_top_pixels_before)
```

- [ ] **Step 5: Implement the deterministic guard and verify GREEN**

Within only the top MASS mask:

1. measure horizontal/vertical adjacent-pixel high-frequency score;
2. create a low-frequency roof surface with Pillow Gaussian blur;
3. blend it into the provider result only where the roof mask is active;
4. reapply the original mask boundary;
5. record before/after score, changed pixels and status.

Pixels outside the top MASS mask are byte-for-byte unchanged by this guard.

- [ ] **Step 6: Extend the one-call image job and manifest**

Set:

```python
"presentation": {
    "kind": "architectural_render_sheet",
    "authority": "generated_design_proposal",
    "panel_roles": list(locked_sheet_panel_roles()),
}
```

The prompt explicitly says the top role is `roof_only`, with no windows,
mullions, balconies, rails or facade bays. Persist the adapter's
`roof_semantic_guard` metadata into the proposal. Keep `request_count == 1`
and `retry_count == 0`.

- [ ] **Step 7: Run all elevation-agent tests**

```powershell
python manage.py test design.test_maas_elevation_agent -v 2
```

Expected: all tests pass.

- [ ] **Step 8: Commit the roof semantic contract**

```powershell
git add ARR/backend/design/maas/agents/elevation_agent/panel_roles.py ARR/backend/design/maas/agents/elevation_agent/image_proposal.py ARR/backend/design/maas/aesthetic/adapters/openai_image.py ARR/backend/design/test_maas_elevation_agent.py
git commit -m "fix(maas): keep generated top panels roof semantic"
```

---

### Task 3: Identity-Bound Architectural Render Evidence in Frontend

**Files:**
- Modify: `ARR/frontend/src/design/components/book-language-flow/elevation-proposal.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/elevation-proposal.test.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/book-language-flow.css`

**Interfaces:**
- Extends: `ElevationProposalEvidence` with `presentationKind`,
  `authority`, `requestCount`, `retryCount`, `roofGuardStatus`, and
  `roofGuardChangedPixels`.
- Preserves: `extractElevationProposal(passport, selected)` strict
  execution/program/geometry identity filtering.
- The result gallery continues to consume only `mass.previewUrl`.

- [ ] **Step 1: Write the failing frontend extraction test**

Extend the proposal fixture with:

```typescript
presentation: {
  kind: 'architectural_render_sheet',
  authority: 'generated_design_proposal',
},
request_count: 1,
retry_count: 0,
provider_metadata: {
  model: 'gpt-image-test',
  roof_semantic_guard: {
    status: 'applied',
    changed_pixel_count: 42,
  },
},
```

Assert those values are returned while the copied-geometry rejection remains
`null`.

- [ ] **Step 2: Run the focused Vitest and verify RED**

```powershell
npx vitest run src/design/components/book-language-flow/elevation-proposal.test.ts
```

Expected: missing properties in the extracted evidence.

- [ ] **Step 3: Extend the pure extractor and verify GREEN**

Read only serializable values from the identity-matched proposal. Invalid
preview URLs or mismatched hashes continue returning `null`.

- [ ] **Step 4: Change the selected-MASS evidence hierarchy**

Render in this order:

1. `ACTUAL COMPILER MASS`;
2. `ARCHITECTURAL RENDER AGENT · RENDER ALT 01`;
3. `6-VIEW GEOMETRY VERIFICATION`.

The render card includes `GENERATED DESIGN PROPOSAL · NOT GEOMETRY / LEGAL
AUTHORITY`, provider/model, request/retry counts, roof-guard status and artifact
hash. The six views are styled as compact technical evidence rather than the
primary visual.

- [ ] **Step 5: Preserve the MASS-only archive and style the render as a primary visual**

Do not change `geometry-result-gallery img src={mass.previewUrl}`. Give the
architectural render card a larger image area, neutral background and compact
monochrome metadata. Do not add decorative colors.

- [ ] **Step 6: Run frontend tests and type checking**

```powershell
npm test -- --run src/design/components/book-language-flow/elevation-proposal.test.ts src/design/components/book-language-flow/archive-selection-policy.test.ts
npm run type-check
```

Expected: tests and TypeScript pass.

- [ ] **Step 7: Commit the frontend render presentation**

```powershell
git add ARR/frontend/src/design/components/book-language-flow/elevation-proposal.ts ARR/frontend/src/design/components/book-language-flow/elevation-proposal.test.ts ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx ARR/frontend/src/design/components/book-language-flow/book-language-flow.css
git commit -m "feat(maas): present identity-bound architectural render alt"
```

---

### Task 4: Generate, Inspect and Verify a New Proof Run

**Files:**
- Generated: `docs/ai-session-memory/maas-service-cache/single-executions/r228-*/`
- Generated: `docs/playwright/design-route-live-verify/r228-*.png`
- Modify: `docs/ai-session-memory/README.md`
- Modify: `docs/ai-session-memory/maas-agent-flow-memory.md`

**Interfaces:**
- Consumes the normal `generate_maas_fresh_batch` and explicit elevation
  proposal command paths.
- Produces a new archive-unique MASS03 radial execution and MASS05 tapered
  execution, one bounded render proposal for each requested proof MASS, and
  browser screenshots.

- [ ] **Step 1: Run the full backend regression set**

```powershell
python manage.py test design.test_maas_geometry_language design.test_maas_fresh_batch design.test_maas_elevation_agent -v 2
python manage.py check
```

Expected: all tests and Django check pass.

- [ ] **Step 2: Generate a fresh ten-MASS batch**

```powershell
python manage.py generate_maas_fresh_batch --batch-id r228-radial-roof-render --count 10 --building-type "generic architectural form study"
```

Expected: `accepted_count == 10`, unique program/geometry hashes, and
`paid_image_request_count == 0` before the explicit render stage.

- [ ] **Step 3: Inspect MASS03 before spending**

Open the new MASS03 `mass.png` and verify:

- at least three plan directions;
- a visible common hub;
- no floating components;
- no one-sided bent fan;
- upright, parcel-neutral architectural massing.

If this fails, stop before any paid image call.

- [ ] **Step 4: Run bounded architectural render generation**

Use the existing explicit batch proposal command/API only for MASS03 and
MASS05. Maximum: two total paid image requests, zero retries.

- [ ] **Step 5: Inspect generated images**

Verify:

- the output reads as architectural rendering, not orange elevation drawing;
- top panel reads as roof material without facade grid;
- silhouette, camera panels and MASS identity remain locked;
- the proposal manifest records provider/model/request and roof-guard evidence.

- [ ] **Step 6: Verify the browser using the connected dev server**

At `http://127.0.0.1:5175/design/language`:

- MASS-only thumbnails remain in the bottom gallery;
- selecting MASS03 shows its common-hub MASS, matching render and six views;
- selecting MASS05 changes all three identities together;
- the render card is primary and labelled `RENDER ALT 01`;
- the full graph contains the existing render proposal node, not a new graph;
- no broken images, console errors or Vite overlay.

- [ ] **Step 7: Update durable memory**

Record:

- the corrected causal flow;
- the radial common-hub invariant;
- the roof-only top-panel invariant;
- frontend hierarchy and MASS-only gallery invariant;
- exact generated execution IDs and artifact paths;
- paid request count and any honest `needs_review` result.

- [ ] **Step 8: Run final verification**

```powershell
git diff --check
python manage.py test design.test_maas_geometry_language design.test_maas_fresh_batch design.test_maas_elevation_agent -v 2
npm test -- --run src/design/components/book-language-flow/elevation-proposal.test.ts src/design/components/book-language-flow/archive-selection-policy.test.ts
npm run type-check
```

Expected: all commands pass.

- [ ] **Step 9: Commit and push only intentional files**

Review the dirty worktree, preserve the user's unrelated staged files, commit
the memory updates and selected verification evidence with exact paths, then:

```powershell
git push origin DK-BB
```

