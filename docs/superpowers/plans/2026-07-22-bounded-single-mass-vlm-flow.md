# Bounded Single-MASS VLM Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one selected MASS reach a truthful, bounded paid VLM decision in the same immutable archive and Full Graph.

**Architecture:** Keep deterministic geometry execution network-free. Add focused repository, replay, and VLM review services under `design.maas.single_execution`; Django views only translate HTTP, and the frontend reloads the same archive contract after review.

**Tech Stack:** Python 3/Django, existing GeometryProgram compiler and OpenAI Responses REST adapter, React/TypeScript/Vitest, Playwright.

## Global Constraints

- Exactly one selected MASS per action.
- At most two reference images and four total live HTTP attempts including retries.
- Cache before live requests; no portfolio loop.
- `not_evaluated` and explicit VLM failure are never acceptance.
- Execution bundles are immutable and existing IDs are never overwritten.
- BOOK remains typed language authority, not result image evidence.

---

### Task 1: Correct final acceptance semantics

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/execution_evidence.py`
- Test: `ARR/backend/design/test_maas_extended_csg_contract.py`

**Interfaces:**
- Consumes: passport stage rows.
- Produces: `passport_state(stages)` with truthful `full_flow_complete` and `final_hard_pass`.

- [ ] Add tests where a live-scored VLM with `hard_pass=false`, a provider error, and a positive cache-hit result produce reject, reject, and accept respectively.
- [ ] Run the three tests and verify the first two fail against current code.
- [ ] Implement `vlm_hard_pass = status in {cache_hit, live_scored, passed} and evidence.hard_pass is True and evidence.program_fit_hard_pass is not False` and require it for acceptance.
- [ ] Run the focused passport tests and commit.

### Task 2: Make run persistence immutable and move replay out of views

**Files:**
- Create: `ARR/backend/design/maas/single_execution/repository.py`
- Create: `ARR/backend/design/maas/single_execution/replay.py`
- Modify: `ARR/backend/design/maas/single_execution/pipeline.py`
- Modify: `ARR/backend/design/maas/single_execution/__init__.py`
- Modify: `ARR/backend/design/views.py`
- Test: `ARR/backend/design/test_maas_single_execution.py`

**Interfaces:**
- Produces: `allocate_execution_id(root, requested_label='') -> str`, `resolve_replay_source(root, run_id, index) -> ReplaySource`.
- `execute_single_mass(..., allow_existing=False)` raises `FileExistsError` before writing an existing bundle.

- [ ] Add a failing test proving two writes to one ID cannot replace program/manifest/PNG.
- [ ] Add a failing HTTP test proving client `execution_id` cannot control the server directory.
- [ ] Implement exclusive server-generated IDs and source resolution in the two focused modules.
- [ ] Reduce `maas_single_execution` to request validation plus service calls.
- [ ] Run all single-execution tests and commit.

### Task 3: Bound and observe VLM transport

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/vlm_adapter.py`
- Modify: `ARR/backend/design/maas/preference/vlm_scorer.py`
- Modify: `ARR/backend/design/maas/geometry_language/execution_evidence.py`
- Test: `ARR/backend/design/test_maas_geometry_language.py`
- Test: `ARR/backend/design/test_maas_executed_vlm_audit.py`

**Interfaces:**
- `retrieve_geometry_reference_matches(..., limit=N)` returns no more than `N`.
- Candidate/reference results expose `api_usage`, `prompt_contract_version`, `candidate/program/geometry hashes`, and `live_request_count`.

- [ ] Add failing tests for exact `limit=1`, repository-absolute cache root, and retained API usage.
- [ ] Change geometry cache default to `workspace_root()/docs/...`.
- [ ] Add `detail='low'` to reference audit and `detail='high'` to the candidate image.
- [ ] Preserve Responses `usage` and exact evidence binding fields through `vlm_evidence`.
- [ ] Run focused VLM/cache tests and commit.

### Task 4: Add one-run bounded VLM review service and API

**Files:**
- Create: `ARR/backend/design/maas/single_execution/vlm_review.py`
- Modify: `ARR/backend/design/maas/single_execution/contracts.py`
- Modify: `ARR/backend/design/maas/single_execution/__init__.py`
- Modify: `ARR/backend/design/views.py`
- Modify: `ARR/backend/design/urls.py`
- Test: `ARR/backend/design/test_maas_single_execution.py`

**Interfaces:**
- Produces: `review_single_execution_with_vlm(root, run_id, reference_limit=2, max_live_requests=4, model=None) -> SingleMassVlmReviewResult`.
- Endpoint: `POST /design/maas/single-executions/<execution_id>/vlm-review/` with only `reference_limit` and optional model.

- [ ] Add failing endpoint tests for non-single run rejection, reference bound, exact passport enrichment, and negative VLM remaining rejected.
- [ ] Compile the persisted program and verify program/geometry/PNG hashes before calling VLM.
- [ ] Run reference retrieval and candidate scoring under the four-attempt budget; atomically enrich the same passport and update manifest.
- [ ] Return public URLs and cost evidence without absolute filesystem paths.
- [ ] Run all single-execution and VLM tests and commit.

### Task 5: Connect bounded VLM to the same frontend graph

**Files:**
- Modify: `ARR/frontend/src/design/lib/language-system-types.ts`
- Modify: `ARR/frontend/src/design/lib/api-client.ts`
- Create: `ARR/frontend/src/design/components/book-language-flow/useSingleMassExecution.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/book-language-flow.css`
- Test: `ARR/frontend/test/unit/design/maas-single-execution-api.test.ts`
- Test: `ARR/frontend/test/unit/design/ExecutedMassEvidence.test.tsx`

**Interfaces:**
- Produces `reviewSingleMassWithVlm(archiveRunId, options)` and a hook that owns execute/review state and aborts stale requests.

- [ ] Add failing tests for a visible `RUN BOUNDED VLM · 1 MASS · MAX 2 REFERENCES` action and same-run reload.
- [ ] Implement API types/client and extract execution/review state from the 1,031-line component.
- [ ] Clear stale passport/outcome state immediately on run change.
- [ ] Reload the reviewed single run and render only actual submitted VLM reference nodes.
- [ ] Run focused Vitest and TypeScript, then commit.

### Task 6: One paid run and full verification

**Files:**
- Modify: `docs/playwright/design-route-live-verify/verify-maas-single-graph.cjs`
- Modify: `docs/ai-session-memory/maas-mass-flow/02_CURRENT_STATE.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/04_VALIDATION_GAPS.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

- [ ] Verify `OPENAI_API_KEY` presence without printing it and inspect exact cache hits for the chosen MASS/reference hashes.
- [ ] Run one live VLM review with `reference_limit=2`, `MAAS_LIVE_VLM_MAX_REQUESTS=4`, and retries disabled.
- [ ] Verify response ID, model, submitted image hashes, usage, live/cache counts, VLM verdict and final passport state.
- [ ] Run backend focused tests, backend full `design`, frontend build/full/type-check, Django check, live HTTP and browser E2E.
- [ ] Directly inspect the final PNG and graph screenshot.
- [ ] Record both passes and remaining unrelated failures honestly in memory JSON/Markdown.
- [ ] Commit only task files, push `DK-BB`, and verify local/remote hashes match.
