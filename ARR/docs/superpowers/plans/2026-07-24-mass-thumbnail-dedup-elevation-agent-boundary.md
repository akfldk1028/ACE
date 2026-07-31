# MASS Thumbnail and Deduplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show one unique isometric MASS per bottom card and preserve the independent elevation-agent boundary.

**Architecture:** Materialize a deterministic isometric thumbnail from the immutable four-view MASS artifact, expose geometry identity on run rows, and deduplicate only the frontend MASS rail by geometry hash. Keep the execution timeline lossless and record future creative generation as an elevationAgent concern.

**Tech Stack:** Django, Pillow, React, TypeScript, Vitest, Django TestCase.

## Global Constraints

- One UnitBox remains the primitive authority.
- Do not alter GeometryProgram, compiled mesh, program hash or geometry hash.
- Bottom rail contains MASS thumbnails only.
- Do not hardcode an image-model name in MAAS geometry code.

---

### Task 1: Immutable single-MASS thumbnail

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/render.py`
- Modify: `ARR/backend/design/maas/single_execution/catalog.py`
- Modify: `ARR/backend/design/views.py`
- Modify: `ARR/backend/design/urls.py`
- Test: `ARR/backend/design/test_maas_single_execution.py`

**Interfaces:**
- Produces: `materialize_isometric_thumbnail(preview_path: str | Path) -> Path`
- Produces: `GET /design/maas/single-executions/<execution_id>/thumbnail/`
- Produces run fields: `geometry_hash`, `thumbnail_url`

- [ ] Add a failing API test asserting a 200 PNG thumbnail smaller than the
      900x680 composite and asserting run identity fields.
- [ ] Run the focused Django test and confirm the thumbnail route is 404.
- [ ] Add atomic Pillow cropping of the isometric panel and the immutable
      endpoint; add `geometry_hash` and `thumbnail_url` to `_run_row`.
- [ ] Rerun the focused Django test and confirm it passes.

### Task 2: Unique geometry cards

**Files:**
- Modify: `ARR/frontend/src/design/lib/language-system-types.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/archive-selection-policy.ts`
- Test: `ARR/frontend/test/unit/design/archive-selection-policy.test.ts`

**Interfaces:**
- Consumes: `ExecutedMassRun.geometry_hash?: string`
- Consumes: `ExecutedMassRun.thumbnail_url?: string`
- Produces: newest-first `RecentMassCard[]` unique by non-empty geometry hash

- [ ] Add a failing Vitest case with two runs sharing one geometry hash.
- [ ] Confirm the test reports two cards and the old `/preview/` URL.
- [ ] Deduplicate after newest-first sorting and use `/thumbnail/` for
      single-execution cards; match selection by geometry hash.
- [ ] Rerun the archive policy test and TypeScript type-check.

### Task 3: Agent boundary memory and browser proof

**Files:**
- Modify: `docs/ai-session-memory/maas-mass-flow/06_ELEVATION_HANDOFF.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/02_CURRENT_STATE.md`
- Create: `ARR/backend/agents/elevationAgent/DOMAIN_CONTRACT.md`

**Interfaces:**
- Records the replaceable creative image-provider boundary without making a
  provider call.

- [ ] Document deterministic projection versus future creative elevation
      generation and the cross-view/mesh consistency gate.
- [ ] Run backend MASS tests, frontend focused tests and type-check.
- [ ] Open `/design/language`, verify unique single-MASS thumbnails, click two
      cards, verify graph/right evidence changes, and save a screenshot.
