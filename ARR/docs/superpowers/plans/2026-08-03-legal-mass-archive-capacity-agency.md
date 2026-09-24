# Legal MASS Archive and Capacity Agency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve and render every valid legal MASS before capacity/program scoring, then let typed agents and VLM revise and select without weakening statutory gates.

**Architecture:** Split deterministic legal admissibility from design-policy evaluation. Introduce an immutable legal-candidate archive between exact legal projection and capacity/VLM selection, treat utilization and per-floor target deltas as typed measurements rather than archive deletion gates, and execute BASE certification before descendant identity binding.

**Tech Stack:** Python 3.13, Django management commands/tests, Shapely polygon/CSG, typed GeometryProgram AST, OpenAI LLM/VLM adapters, Pillow board renderer.

## Global Constraints

- Parcel, height, setback, BCR, FAR upper limits, exact geometry authority, and statutory parking remain fail-closed.
- `0.70`, `0.90`, and per-floor target areas cannot delete an otherwise legal MASS from the legal archive.
- Capacity revisions must be generic typed GeometryProgram descendants, recompiled and recertified through the full legal pipeline.
- No named-form hardcoding and no floorwise prism/loft visual fallback.
- BASE must be compiler-clean, contained, and exact-hash registered before descendant `parent_geometry_hash` binding.
- VLM cannot waive law; it reviews only renderable exact geometry.
- MASS only; elevation remains out of scope.

---

### Task 1: Separate Legal Admissibility From Capacity Objectives

**Files:**
- Modify: `backend/design/maas/book_language/candidate_floor_authority.py`
- Modify: `backend/design/maas/book_language/capacity_contract.py`
- Modify: `backend/design/maas/book_language/candidate_generation.py`
- Test: `backend/design/test_legal_mass_capacity_authority.py`

**Interfaces:**
- Consumes: exact `shared_floor_contract` and source capacity measurement.
- Produces: `legal_hard_pass`, `capacity_objective_status`, `revision_recommended`, and diagnostic per-floor deltas without changing existing statutory evidence.

- [ ] **Step 1: Write failing authority tests**

Create tests proving a contained, measurable candidate at utilization `0.668` remains legal/archive-eligible while reporting a capacity objective miss; a `0.6998` candidate is not erased; per-floor target deltas do not change legal admissibility; malformed or outside-legal geometry remains rejected.

- [ ] **Step 2: Run the authority tests and verify RED**

Run: `python manage.py test design.test_legal_mass_capacity_authority --verbosity 1`

Expected: failures show the current capacity/shared-floor hard-pass value controls candidate retention.

- [ ] **Step 3: Implement typed policy separation**

Add a pure evaluator returning:

```python
{
    "legal_hard_pass": bool,
    "shared_floor_measured": bool,
    "feasible_capacity_utilization": float,
    "capacity_objective_status": "below" | "within" | "above" | "unavailable",
    "per_floor_target_deltas_m2": list[float],
    "revision_recommended": bool,
}
```

Use legal containment/topology/upper-limit failures for `legal_hard_pass`. Keep capacity thresholds and floor targets in the objective fields. Candidate generation must stop using capacity-objective failure as the condition that deletes a legal candidate.

- [ ] **Step 4: Run the authority tests and verify GREEN**

Run: `python manage.py test design.test_legal_mass_capacity_authority --verbosity 1`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git add backend/design/maas/book_language/candidate_floor_authority.py backend/design/maas/book_language/capacity_contract.py backend/design/maas/book_language/candidate_generation.py backend/design/test_legal_mass_capacity_authority.py
git commit -m "fix: separate legal mass from capacity objectives"
```

### Task 2: Materialize an Immutable Legal MASS Archive

**Files:**
- Create: `backend/design/maas/book_language/legal_mass_archive.py`
- Modify: `backend/design/maas/book_language/candidate_generation.py`
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `backend/design/test_legal_mass_archive.py`

**Interfaces:**
- Consumes: compiler-clean, contained, authored-surface-certified candidates plus Task 1 policy evidence.
- Produces: `LegalMassArchiveRecord` dictionaries and `legal_mass_archive` run evidence retained independently of final selection.

- [ ] **Step 1: Write failing archive tests**

Test that legal candidates with capacity misses enter the archive, illegal/unbound candidates do not, descendants create new records without overwriting parents, and archive records retain geometry/program hashes, surfaces, capacity evidence, scope, family, and lineage.

- [ ] **Step 2: Run archive tests and verify RED**

Run: `python manage.py test design.test_legal_mass_archive --verbosity 1`

Expected: archive module/evidence is absent.

- [ ] **Step 3: Implement the archive boundary**

Create pure record validation/deduplication keyed by exact geometry hash. Insert archive admission after authored legal projection, compilation, containment, and surface authority checks, but before capacity objective filtering and VLM. Persist bounded archive evidence in portfolio counts and summary JSON.

- [ ] **Step 4: Run archive tests and verify GREEN**

Run: `python manage.py test design.test_legal_mass_archive --verbosity 1`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 2**

```powershell
git add backend/design/maas/book_language/legal_mass_archive.py backend/design/maas/book_language/candidate_generation.py backend/design/maas/book_language/portfolio_benchmark.py backend/design/test_legal_mass_archive.py
git commit -m "feat: preserve legal mass archive"
```

### Task 3: Enforce BASE-Then-Descendant Production

**Files:**
- Modify: `backend/design/maas/book_language/candidate_generation.py`
- Test: `backend/design/test_r340_base_vlm_transport.py`
- Test: `backend/design/test_legal_mass_archive.py`

**Interfaces:**
- Consumes: selected exact-key schedules and Task 2 archive registry.
- Produces: two-phase lineage execution and exact `parent_geometry_hash` binding.

- [ ] **Step 1: Write a failing live-order regression**

Test the production loop rather than only helper functions. The selected descendant must cause its BASE to materialize, certify, archive, and register first. The descendant must then carry the BASE post-BOOK geometry hash. Missing/conflicting base hashes remain unbound and fail closed.

- [ ] **Step 2: Run the lineage regression and verify RED**

Run: `python -m unittest design.test_r340_base_vlm_transport -v`

Expected: production-order assertion fails because descendant metadata is currently attached before registry population.

- [ ] **Step 3: Implement explicit two-phase scheduling**

Partition each LLM lineage schedule into BASE work then descendant work. Do not rely on incidental principle iteration order. Register only compiler-clean, contained, archived BASE geometry hashes; bind descendants only in phase two.

- [ ] **Step 4: Run lineage and archive tests and verify GREEN**

Run: `python -m unittest design.test_r340_base_vlm_transport -v`

Run: `python manage.py test design.test_legal_mass_archive --verbosity 1`

Expected: both pass.

- [ ] **Step 5: Commit Task 3**

```powershell
git add backend/design/maas/book_language/candidate_generation.py backend/design/test_r340_base_vlm_transport.py backend/design/test_legal_mass_archive.py
git commit -m "fix: certify base before descendant binding"
```

### Task 4: Render Legal Archive Independently of Selection

**Files:**
- Create: `backend/design/maas/book_language/legal_mass_archive_board.py`
- Modify: `backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `backend/design/test_legal_mass_archive_board.py`

**Interfaces:**
- Consumes: Task 2 archive records and exact source surfaces.
- Produces: `maas-book-<program>-<target>-legal-archive.png` plus manifest path/hash and visible-card evidence.

- [ ] **Step 1: Write failing board tests**

Test a `0/5` final selection with three archived legal masses. The legal archive board must contain three visible mass cards with utilization, capacity status, parking status, VLM status, and non-selection reason. The selected board may remain empty.

- [ ] **Step 2: Run board tests and verify RED**

Run: `python manage.py test design.test_legal_mass_archive_board --verbosity 1`

Expected: archive board artifact is absent.

- [ ] **Step 3: Implement archive board and manifest**

Render exact archived source surfaces through the existing MASS renderer. Do not synthesize silhouettes from capacity plates. Persist card count, visible mass pixel ratio, PNG path/hash, and archive record identities in summary JSON.

- [ ] **Step 4: Run board tests and verify GREEN**

Run: `python manage.py test design.test_legal_mass_archive_board --verbosity 1`

Expected: all tests pass and the temporary PNG has nonzero visible mass pixels.

- [ ] **Step 5: Commit Task 4**

```powershell
git add backend/design/maas/book_language/legal_mass_archive_board.py backend/design/management/commands/benchmark_maas_book_program_portfolios.py backend/design/maas/book_language/portfolio_benchmark.py backend/design/test_legal_mass_archive_board.py
git commit -m "feat: render legal mass archive board"
```

### Task 5: Full MASS Regression and Target-5 Evidence

**Files:**
- Modify: `docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-03-legal-archive-target5-result.md`

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: focused regression evidence, one target-5 live run, archive PNG, selected PNG, and checkpoint record.

- [ ] **Step 1: Run focused regressions**

```powershell
python manage.py test design.test_legal_mass_capacity_authority design.test_legal_mass_archive design.test_legal_mass_archive_board design.test_task7b_authored_projection_identity design.test_r339_llm_book_lineage_release design.test_task7c_authored_visual_authority --verbosity 1
python -m unittest design.test_r340_base_vlm_transport -v
```

Expected: all pass.

- [ ] **Step 2: Run target-5 once**

```powershell
python manage.py benchmark_maas_book_program_portfolios --program neighborhood --recursive-only --progressive-target 5 --live-llm-author --live-vlm --output-dir "D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5" --verbosity 1
```

- [ ] **Step 3: Inspect both PNG artifacts and summary evidence**

Confirm that any nonempty legal archive produces visible cards even when final selection is below five. Record legal archive count, capacity objective bands, BASE/descendant VLM counts, selected count, law/parking status, and both absolute PNG paths.

- [ ] **Step 4: Write and commit the checkpoint**

```powershell
git add docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-03-legal-archive-target5-result.md
git commit -m "docs: record legal archive target5 result"
```
