# Cheap Three-Candidate Portfolio VLM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce same-site MASS PNG evidence and replace the incorrect single-candidate board audit with a one-request, three-candidate portfolio VLM contract.

**Architecture:** Normalize affine BaseVolumes as one UnitBox followed by an explicit Matrix4, then apply topology-changing operators downstream. Run deterministic geometry/site/program/law/parking gates before selecting at most three visually separated survivors. Submit one three-card PNG and at most two exact local reference images to the board-specific scorer in one paid request with no retry.

**Tech Stack:** Python 3, Django tests, Pillow, existing MAAS GeometryProgram/compiler, OpenAI Responses API transport mocked in tests.

## Global Constraints

- Work only in `D:\Data\25_ACE`; do not copy another worktree or project folder.
- The sole mathematical root is one normalized `1/1 UnitBox`.
- Persist affine BaseVolume derivation as an explicit homogeneous 4x4 matrix.
- Matrix4 does not replace topology-changing typed operators.
- Named precedents are capability-range evidence, never recipes or quotas.
- Generate twenty candidates with zero provider calls before any VLM shortlist.
- VLM shortlist size is at most three candidates in one PNG and one HTTP request.
- Use at most two reference images at low detail, `gpt-5.4-mini`, and zero retries.
- If fewer than three deterministic survivors exist, spend zero paid requests.
- JSON is machine authority; PNG is mandatory user-facing evidence.

---

### Task 1: Board-Specific Reference Image Contract

**Files:**
- Create: `ARR/backend/design/test_maas_portfolio_vlm_references.py`
- Modify: `ARR/backend/design/maas/preference/vlm_scorer.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`

**Interfaces:**
- Consumes: existing `_reference_image_inputs(reference_matches, limit)` and paid-provider request guard.
- Produces: `score_portfolio_board_with_openai_vlm(..., reference_matches=None, image_detail="high", program_hashes=None, geometry_hashes=None)` with `vlm_image_inputs`.

- [ ] **Step 1: Write the failing transport test**

Create a 3-card PNG and two local reference PNGs. Mock
`urllib.request.urlopen`, capture the JSON request body, and assert content
contains exactly three `input_image` records in this order: board, reference
one, reference two. Assert the prompt contains
`three separate candidate cards` and does not contain
`four-view candidate`.

- [ ] **Step 2: Run the transport test and verify RED**

Run:

```powershell
python manage.py test design.test_maas_portfolio_vlm_references.PortfolioVlmReferenceTests.test_board_request_submits_two_exact_references_once --verbosity 2
```

Expected: FAIL because `score_portfolio_board_with_openai_vlm` does not accept
`reference_matches`.

- [ ] **Step 3: Add identity and cache RED tests**

Assert the result contains board/reference local paths, SHA-256 values,
`used_by_vlm=true`, response ID, and candidate program/geometry hashes. Run a
second zero-network cache-key unit test that changes one reference SHA-256 and
asserts a different key.

- [ ] **Step 4: Implement the smallest board scorer change**

Add reference/image-detail/identity parameters. Reuse
`_reference_image_inputs`, bind submitted identities with
`_bind_submitted_reference_identity`, include exact reference identities in
the cache key, and persist:

```python
result["vlm_image_inputs"] = {
    "schema_version": "arr.maas.portfolio_vlm_image_inputs.v1",
    "board": {...},
    "references": submitted_references,
    "reference_count": len(submitted_references),
    "candidate_program_hashes": [...],
    "candidate_geometry_hashes": [...],
}
result["api_usage"] = dict(response_data.get("usage") or {})
```

Update the prompt to say the first image is one contact sheet containing three
separate candidate cards and require one decision per candidate ID.

- [ ] **Step 5: Pass audited references from portfolio generation**

Deduplicate already-retrieved candidate `reference_matches` by exact local
image SHA/source identity. Pass at most two into the board scorer. Do not
perform separate reference-audit HTTP calls.

- [ ] **Step 6: Run focused tests and commit**

Run:

```powershell
python manage.py test design.test_maas_portfolio_vlm_references design.test_maas_paid_provider_budget --verbosity 1
```

Commit only the three task files with:

```powershell
git commit -m "fix(maas): bind references to portfolio VLM board"
```

### Task 2: Explicit Matrix4 BaseVolume Authority

**Files:**
- Create: `ARR/backend/design/test_maas_basevolume_matrix_contract.py`
- Modify: `ARR/backend/design/maas/geometry_language/base_seeds.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_passport.py`

**Interfaces:**
- Consumes: `scale_matrix4`, `matrix4_to_lists`, GeometryNode `matrix4`.
- Produces: `base_seed_program(seed_id)` programs with one `unit_box` primitive and one explicit Matrix4 affine BaseVolume node for block/slab/bar/tower.

- [ ] **Step 1: Write the failing Matrix4 test**

For `block`, `slab`, `bar`, and `tower`, assert:

```python
program = base_seed_program(seed_id)
assert [n.operator for n in program.nodes].count("box") == 1
assert [n.operator for n in program.nodes].count("matrix4") == 1
assert program.nodes[-1].parameters["matrix4"][3] == [0.0, 0.0, 0.0, 1.0]
```

Also compile each program and assert connected/watertight/manifold output.

- [ ] **Step 2: Run the Matrix4 test and verify RED**

Run:

```powershell
python manage.py test design.test_maas_basevolume_matrix_contract.BaseVolumeMatrixContractTests.test_affine_seeds_persist_explicit_matrix4 --verbosity 2
```

Expected: FAIL because current AST stores the `scale` shorthand.

- [ ] **Step 3: Implement explicit Matrix4 normalization**

Import `scale_matrix4` and `matrix4_to_lists`. Replace only the persisted
affine seed node with:

```python
GeometryNode(
    f"seed_{spec.seed_id}",
    "transform",
    "matrix4",
    inputs=("unit_box",),
    parameters={"matrix4": matrix4_to_lists(scale_matrix4(spec.normalized_scale))},
)
```

Record `canonical_root=1/1 UnitBox` and
`basevolume_affine_authority=explicit_matrix4` in program metadata/passport.

- [ ] **Step 4: Quarantine the second primitive authority**

Add a failing test that `profiled_prism` is not returned by
`base_seed_programs()` as an independent base primitive. Preserve its profile
catalog as downstream derived-topology input; do not delete geometry
capability.

- [ ] **Step 5: Run focused compiler/BaseVolume tests and commit**

Run:

```powershell
python manage.py test design.test_maas_basevolume_matrix_contract design.test_maas_geometry_language --verbosity 1
```

Commit only task files with:

```powershell
git commit -m "fix(maas): make BaseVolume Matrix4 authority explicit"
```

### Task 3: Free Three-MASS Visual Checkpoint

**Files:**
- Create: `ARR/backend/design/maas/geometry_language/relational_mass_preview.py`
- Create: `ARR/backend/design/test_maas_relational_mass_preview.py`
- Create runtime artifacts under: `docs/playwright/design-route-live-verify/maas-relational-shortlist-r1/`

**Interfaces:**
- Consumes: explicit Matrix4 BaseVolumes and existing compiler/render helpers.
- Produces: `render_relational_mass_preview(output_dir, pnu) -> dict` with candidate JSON, individual PNGs, `maas-same-site-20.png`, and `maas-vlm-shortlist-3.png`.

- [ ] **Step 1: Write failing preview tests**

Assert the preview builder returns twenty slots on PNU
`1168011800104170004`, selects at most three deterministic geometry survivors,
and produces no paid-provider calls. Assert every compiled survivor is
connected, watertight, and manifold.

- [ ] **Step 2: Run preview tests and verify RED**

Run:

```powershell
python manage.py test design.test_maas_relational_mass_preview --verbosity 2
```

Expected: FAIL because the preview module does not exist.

- [ ] **Step 3: Implement bounded candidate programs**

Build a deterministic zero-paid pool containing ordinary affine solids plus
optional relational programs using only current typed operators. Each program
starts from explicit Matrix4 BaseVolume and uses combinations such as
`courtyard`, `carve_void`, `circularize`, `profile_sweep_3d`, `matrix_array`,
`bridge`, `attach`, `cantilever`, `section_surface`, `loft_surface`,
`host_face_surface`, and `shell_thicken` when supported by the active compiler.
Unsupported programs are retained as rejected slots with exact compiler
reasons.

- [ ] **Step 4: Add deterministic spatial prechecks**

For every survivor record component count, watertightness, manifoldness,
volume, occupied floor estimate, clear-height/depth proxy, and geometry hash.
Do not label law/parking pass unless the existing exact PNU services actually
return matching identity evidence.

- [ ] **Step 5: Render mandatory PNGs**

Render a 5x4 board with same parcel/access frame and per-slot status. Render a
3-card shortlist board with candidate IDs, measured geometry facts, and
`VLM NOT YET SPENT`. Reject slots remain visible.

- [ ] **Step 6: Run preview tests and generate artifacts**

Run:

```powershell
python manage.py test design.test_maas_relational_mass_preview --verbosity 1
python manage.py shell -c "from design.maas.geometry_language.relational_mass_preview import render_relational_mass_preview; print(render_relational_mass_preview('../../docs/playwright/design-route-live-verify/maas-relational-shortlist-r1', '1168011800104170004'))"
```

- [ ] **Step 7: Inspect both PNGs and commit**

Open the generated PNGs, verify nonblank unique masses and truthful labels,
then commit the module/tests only. Runtime PNG/JSON artifacts remain available
for user review and may be committed separately after approval.

### Task 4: Final Verification and Memory

**Files:**
- Modify: `docs/ai-session-memory/MAAS_LAWFUL_DIVERSE_LLM_PILOT_20260730.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: focused test output and generated artifact hashes.
- Produces: next-session recovery truth.

- [ ] **Step 1: Run focused verification**

Run all new tests plus paid-provider budget tests and `python manage.py check`.

- [ ] **Step 2: Verify artifacts**

Parse every JSON, open every PNG, recompute SHA-256 values, verify paid request
count remains unchanged, and run `git diff --check` on task files.

- [ ] **Step 3: Update memory truthfully**

Record BaseVolume Matrix4 behavior, board scorer reference support, exact free
preview status, artifact paths/hashes, rejected reasons, and whether exact
law/parking evidence was or was not evaluated.

- [ ] **Step 4: Commit focused memory changes**

Stage only the three memory files and generated audit manifest. Do not stage
unrelated dirty workspace files.
