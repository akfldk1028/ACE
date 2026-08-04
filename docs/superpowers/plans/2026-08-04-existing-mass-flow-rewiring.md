# Existing MASS Flow Rewiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconnect existing MASS modules so broad lawful and visually diverse live candidates survive generation cycles and reach final VLM and selection.

**Architecture:** Preserve all existing authorities and archives. Correct the two-phase ordering, broaden only development-parent release, retain bounded live QD candidates across cycles, and feed selector exclusions through the existing author-feedback channel.

**Tech Stack:** Django/Python, Shapely geometry, existing MAAS GeometryProgram/BOOK/QD/VLM modules, Django tests and pytest.

## Global Constraints

- Do not weaken statutory law, containment, structure, parking or final-VLM gates.
- Do not promote detached `LegalMassArchive` records into live candidates.
- Do not create a parallel archive, queue or agent.
- Keep BASE generation, replenishment and selection responsibilities in their existing modules.
- Use test-first RED/GREEN for every behavior change.
- Do not run a paid live target-5 benchmark until Tasks 1-4 and the deterministic integration test pass.

---

### Task 1: Restore two-phase replenishment ordering

**Files:**
- Modify: `ARR/backend/design/maas/book_language/portfolio_replenishment.py`
- Test: `ARR/backend/design/test_replenishment_two_phase_order.py`

**Interfaces:**
- Consumes: existing `_program_pool(..., base_review_callback=...)` contract.
- Produces: replenishment evidence proving BASE review occurs before descendant generation.

- [ ] Write a failing test with a recording callback that asserts event order equals `base_generated, base_reviewed, descendant_generated`.
- [ ] Run the focused test and confirm current replenishment records descendant generation before review or omits the callback.
- [ ] Pass the existing BASE review callback into replenishment generation and consume its returned two-phase VLM evidence instead of auditing after descendants exist.
- [ ] Run the focused test and existing replenishment tests.
- [ ] Commit only Task 1 files.

### Task 2: Preserve certified development parents for BOOK expansion

**Files:**
- Modify: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Test: `ARR/backend/design/test_development_parent_release.py`

**Interfaces:**
- Consumes: reviewed BASE evidence containing exact fingerprints, response identity and `development_review_eligible`.
- Produces: exact reviewed-parent registry entries with separate `development_release` and `selection_eligible` authority.

- [ ] Write failing tests proving a certified development-reviewed BASE enters descendant generation while an unreviewed, hash-conflicted or structurally invalid BASE remains rejected.
- [ ] Run the focused tests and capture the expected rejection of the valid development parent.
- [ ] Modify the existing reviewed registry predicate without changing final selection eligibility.
- [ ] Run focused lineage and BASE-review tests.
- [ ] Commit only Task 2 files.

### Task 3: Carry the existing live QD reserve across cycles

**Files:**
- Modify: `ARR/backend/design/maas/book_language/portfolio_replenishment.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `ARR/backend/design/test_replenishment_live_qd_reserve.py`

**Interfaces:**
- Consumes: live program-passing candidates returned by the current cycle and prior reserve.
- Produces: a bounded deduplicated reserve using existing candidate fingerprints and MAP-Elites descriptors.

- [ ] Write a failing two-cycle test where a lawful non-selected candidate from cycle 1 is still available for downstream/final review in cycle 2.
- [ ] Assert detached legal archive dictionaries cannot enter the reserve.
- [ ] Add reserve input/output fields to the existing replenishment result and carry them in benchmark state.
- [ ] Bound/deduplicate with existing QD functions; do not duplicate descriptor logic.
- [ ] Run focused QD, replenishment and portfolio tests.
- [ ] Commit only Task 3 hunks; preserve unrelated dirty changes.

### Task 4: Feed selector exclusions into existing author feedback

**Files:**
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `ARR/backend/design/test_selector_replenishment_feedback.py`

**Interfaces:**
- Consumes: existing `selection_trace` and `selection_capacity_diagnostics`.
- Produces: bounded coordinate-free causal feedback for the next synthesis request.

- [ ] Write a failing test proving `silhouette_near_duplicate` and missing descriptor cells appear in the next author request while coordinates and mesh payloads do not.
- [ ] Compute diagnostics immediately after selection and add them to `prior_cycle_causal_evidence`.
- [ ] Reuse `_bounded_replenishment_causal_feedback` sanitization and deduplication.
- [ ] Recompute family deficits from selected and excluded candidates after selection.
- [ ] Run focused feedback and portfolio tests.
- [ ] Commit only Task 4 hunks; preserve unrelated dirty changes.

### Task 5: Deterministic flow loop and live validation

**Files:**
- Create: `ARR/backend/design/test_mass_flow_rewiring_integration.py`
- Update: `docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-04-existing-flow-rewiring-result.md`

**Interfaces:**
- Consumes: Tasks 1-4 contracts.
- Produces: stage-by-stage funnel evidence and one live target-5 artifact set.

- [ ] Write a deterministic multi-cycle test with stepped, curved/oblique and voided families; assert all three reach adjudication and selector feedback changes the next request.
- [ ] Run focused tests from Tasks 1-5 together.
- [ ] Run one live LLM+VLM target-5 benchmark into a new revision directory.
- [ ] Inspect the final PNG and summary for selected count, law/parking/final-VLM authority and phenotype/body/section diversity.
- [ ] Record exact counts, failures, runtime, PNG path and commits in memory.
- [ ] Commit only the result checkpoint and explicitly related code/tests.

