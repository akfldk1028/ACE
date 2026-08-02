# Target3 Diagnostic Anchor Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reserve typed prism, oblique, and stepped GeometryProgram/BOOK probes before exhaustive target3 diagnostic enumeration while shrinking `candidate_generation.py`.

**Architecture:** A focused `diagnostic_anchor_scheduler.py` will own canonical preservation controls, typed anchor discovery, fixed BOOK principle selection, and 1/1 scope policy. `candidate_generation.py` will retain the exact legal/capacity pipeline and call the scheduler through thin functions only.

**Tech Stack:** Python dataclasses, existing GeometryProgram/VerbSequence ASTs, Django TestCase.

## Global Constraints

- Never hardcode a program hash, PNU, parcel coordinate, or final phenotype.
- Anchors are typed supply intentions; final measured mesh morphology remains authoritative.
- Preserve the unchanged exact legal, capacity, parking, hash, and morphology gates.
- Keep target20 competition scheduling unchanged.

---

### Task 1: Scheduler contract and extraction

**Files:**
- Create: `ARR/backend/design/maas/book_language/diagnostic_anchor_scheduler.py`
- Modify: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Test: `ARR/backend/design/test_maas_diagnostic_anchor_scheduler.py`

**Interfaces:**
- Produces: `schedule_diagnostic_anchor_parents(parent_seeds) -> tuple[VerbSequence, ...]`
- Produces: `diagnostic_anchor_principles(seed, principle_by_id, default) -> tuple`
- Produces: `diagnostic_anchor_scope(seed, default_label, default_orientation) -> tuple[str, str]`
- Consumes: existing geometry payload notes, BOOK registry principles, and canonical base-seed programs.

- [x] **Step 1: Write failing tests**

Assert that the scheduler emits prism, oblique, and stepped anchors first; binds fixed typed BOOK principles and 1/1 scope; does not hardcode hashes/PNU; and preserves all non-anchor parents exactly once.

- [x] **Step 2: Verify RED**

Run: `python manage.py test design.test_maas_diagnostic_anchor_scheduler -v 2`

Expected: import failure because `diagnostic_anchor_scheduler` does not exist.

- [x] **Step 3: Implement minimal scheduler and thin integration**

Move the existing preservation-control construction out of `candidate_generation.py`, add typed operator classification, and call scheduler policy at parent/principle/scope boundaries.

- [x] **Step 4: Verify GREEN and regressions**

Run the focused scheduler tests, relevant BOOK-language tests, and target3 smoke.

- [x] **Step 5: Report**

Report target3 output, measured anchor supply, and `git diff --numstat` proving `candidate_generation.py` shrank.

## Result

- Focused verification: 7 tests passed; scoped `py_compile` and
  `git diff --check` passed.
- `candidate_generation.py` shrank from 4605 to 4515 lines during this task.
- Fresh PNU smoke:
  `docs/mass/mass-pnu3-target3-anchors-final-20260730-003705`.
- Typed prismatic and stepped anchors hard-passed; the initial exact pool grew
  to three with one ordinary measured-oblique candidate.
- Product verdict remains fail, but the solver facts did not collapse: the
  five candidates were measured as three prismatic, one oblique and one
  stepped, with distinct volume and surface keys. All ten exact certified
  silhouette distances were below the target3 `0.16` minimum
  (`0.027592..0.133717`), leaving a compatibility graph with no edge and
  maximum cardinality one. Continue by generating larger certified
  top/front/side separation; do not weaken diversity gates.
