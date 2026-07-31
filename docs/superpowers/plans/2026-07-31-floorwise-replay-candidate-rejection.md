# Floorwise Replay Candidate Rejection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent one floorwise replay footprint degeneracy from aborting a same-PNU portfolio run while preserving strict geometry, GFA, and structural-error contracts.

**Architecture:** Keep the exact replay serializer strict and convert only its known `floorwise volume has no replayable footprint` candidate error into `_materialize_directed_geometry(...) -> None`. The existing `_program_pool` rejection counter and `continue` path then discard that candidate without changing any floor band or hiding unrelated invariant failures.

**Tech Stack:** Python 3.13, Django `SimpleTestCase`, `unittest.mock.patch`, Shapely, existing MAAS GeometryProgram/SourceMass pipeline.

## Global Constraints

- Work only in `D:\Data\25_ACE`; do not create another project copy or worktree.
- `ARR/backend/design/test_maas_mass_stage.py` is a pre-existing untracked
  user file. Do not stage it or add task-owned tests to it.
- Do not modify `floorwise_source_to_geometry_program` to skip or delete invalid floor volumes.
- Catch only the exact message `floorwise volume has no replayable footprint`.
- Every other `ValueError` must continue to propagate.
- A rejected candidate must return `None` and reuse the existing `_program_pool` fail-closed path.
- Re-run the proper PNU `1168011800104170004` portfolio with zero paid provider calls before VLM.
- Allow one bounded three-card VLM request only when at least three deterministic final survivors exist.

---

### Task 1: Candidate-Level Replay Rejection

**Files:**
- Create: `ARR/backend/design/test_maas_floorwise_candidate_rejection.py`
- Modify: `ARR/backend/design/maas/book_language/candidate_generation.py:1251-1255`

**Interfaces:**
- Consumes: `floorwise_source_to_geometry_program(source, height_m, name) -> GeometryProgram`
- Produces: `_materialize_directed_geometry(...) -> SourceMass | None`, returning `None` only for the exact unreplayable-footprint candidate error.

- [ ] **Step 1: Add the regression tests**

Add a self-contained test module owned by this task. Build a real `SourceMass`
with gymnasium roles and trusted component-graph provenance, the `slab`
program from `base_seed_program("slab")`, candidate height `16.0`, four
floors, a four-floor `box(-15.0, -10.0, 15.0, 10.0)` legal field, and a
`geometry_program_directive=real-slab` sequence. This mirrors the canonical
real-slab fallback boundary without importing from either pre-existing
untracked test module.

Patch `select_legal_field_affine_projection` to return `None`,
`_authored_projection_identity_evidence` to return `{"hard_pass": True}`, and
`floorwise_source_to_geometry_program` to raise:

```python
ValueError("floorwise volume has no replayable footprint")
```

Assert `_materialize_directed_geometry(...)` returns `None`.

Add a companion test with:

```python
ValueError("source has no materialized floorwise legal matrix stack")
```

Assert that error still propagates with `self.assertRaisesMessage`.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python manage.py test `
  design.test_maas_floorwise_candidate_rejection.FloorwiseCandidateReplayRejectionTests.test_unreplayable_floor_volume_is_rejected_as_one_candidate `
  design.test_maas_floorwise_candidate_rejection.FloorwiseCandidateReplayRejectionTests.test_other_floorwise_replay_value_error_still_aborts `
  --verbosity 2
```

Expected: the first test errors with
`floorwise volume has no replayable footprint`; the second already propagates.

- [ ] **Step 3: Implement the narrow candidate boundary**

Wrap only the fallback call at `candidate_generation.py:1251-1255`:

```python
try:
    execution_program = floorwise_source_to_geometry_program(
        materialized,
        height_m=candidate_height_m,
        name=f"{authored_program.name}__final_legal_projection",
    )
except ValueError as exc:
    if str(exc) != "floorwise volume has no replayable footprint":
        raise
    logger.info(
        "Rejecting authored projection replay serialization: %s",
        exc,
    )
    return None
```

Do not catch `TypeError`, do not catch at replenishment scope, and do not
modify the source volumes.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the two tests from Step 2. Expected: `2/2 PASS`.

Run:

```powershell
python manage.py test `
  design.test_maas_capacity_replay_numeric_transport `
  design.test_maas_mass_stage.MaasStageHardContractTests.test_real_slab_uses_final_floorwise_program_as_geometry_authority `
  design.test_maas_shared_floor_contract `
  --verbosity 1
```

Expected: zero failures.

- [ ] **Step 5: Inspect and commit only the two task files**

Run:

```powershell
git diff --check -- `
  backend/design/test_maas_floorwise_candidate_rejection.py `
  backend/design/maas/book_language/candidate_generation.py
git diff --stat -- `
  backend/design/test_maas_floorwise_candidate_rejection.py `
  backend/design/maas/book_language/candidate_generation.py
```

Because both files contain pre-existing user changes, stage only the exact
new test and exception-boundary hunks. Commit:

```powershell
git commit -m "fix(maas): reject unreplayable floor candidate"
```

### Task 2: Proper Same-PNU Full Verification

**Files:**
- Create runtime artifacts under:
  `docs/playwright/design-route-live-verify/book-program-portfolios-r183-proper-full-pnu/`
- Modify after verification:
  `docs/ai-session-memory/MAAS_LAWFUL_DIVERSE_LLM_PILOT_20260730.md`
  `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
  `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: fixed current `benchmark_maas_book_program_portfolios` command.
- Produces: exact run state, summary JSON, geometry artifacts JSON, same-PNU portfolio PNG, optional three-card VLM audit, and truthful recovery memory.

- [ ] **Step 1: Re-run the zero-paid proper portfolio**

From `ARR/backend`, run:

```powershell
python manage.py benchmark_maas_book_program_portfolios `
  --pnu 1168011800104170004 `
  --program neighborhood `
  --publishable-20 `
  --output-dir D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-r183-proper-full-pnu
```

Do not pass `--live-vlm` or `--live-llm-author`.

- [ ] **Step 2: Verify the exact full-run evidence**

Parse every generated JSON and assert:

- PNU equals `1168011800104170004`.
- Site boundary source equals `vworld_live_pnu`.
- Every selected row binds the final program hash, geometry hash, legal floor
  field hash, actual GFA stop certificate, law result, parking result, and
  shared-floor contract.
- Selected count and hard-pass count are reported exactly; do not claim 20 if
  the bounded search produces fewer.
- Paid-provider request count is zero.

- [ ] **Step 3: Inspect the portfolio PNG**

Open the final neighborhood board and confirm that every reported selected
candidate has visible mass. Record repeated step/box dominance as failure
evidence rather than relabeling it as diversity.

- [ ] **Step 4: Run one three-card VLM audit only if eligible**

If at least three selected candidates pass deterministic law, parking,
shared-floor, geometry, and final-GFA gates, render one three-card board from
three materially separated survivors. Submit exactly one request using
`gpt-5.4-mini`, at most two local precedent references at low detail, and zero
retries. If fewer than three qualify, spend zero.

- [ ] **Step 5: Run final code verification**

From `ARR/backend`, run:

```powershell
python manage.py test `
  design.test_maas_mass_stage `
  design.test_maas_capacity_replay_numeric_transport `
  design.test_maas_shared_floor_contract `
  design.test_maas_portfolio_vlm_references `
  design.test_maas_paid_provider_budget `
  --verbosity 1
python manage.py check
```

Read the complete output and report exact pass/failure counts.

- [ ] **Step 6: Update and commit memory**

Record the r182 failure, the narrow fix, r183 selected/hard-pass counts,
artifact paths and hashes, paid-call count, VLM result or skip reason, and the
remaining physical core/egress/room-packing limitation. Stage and commit only
the three memory files.
