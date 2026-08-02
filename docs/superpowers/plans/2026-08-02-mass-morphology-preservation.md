# MASS Morphology Preservation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep intentional stepped MASSes while preventing diagnostic legal fallback from converting non-stepped authored GeometryPrograms into selectable stepped floor unions.

**Architecture:** The authored GeometryProgram remains the morphology authority. Diagnostic target sizing may relax selection completeness and tiny-geometry diagnostics, but it may not disable authored-to-legal identity preservation. Elevation and frontend work are explicitly out of scope.

**Tech Stack:** Python, Django `SimpleTestCase`, Shapely, ARR MAAS GeometryProgram pipeline.

## Global Constraints

- Preserve canonical `1/1 UnitBox` and derived `1/2`, `3/8`, `1/4`, `1/8`, `1/16` lineage.
- Keep intentional `book_grade`, `setback`, `stack`, `stepped_mass`, and `terrace` programs valid.
- Do not run the target-20 portfolio in this checkpoint.
- Do not modify elevationAgent or frontend elevation presentation.

---

### Task 1: Make authored morphology protection non-bypassable

**Files:**
- Create: `ARR/backend/design/test_maas_diagnostic_morphology_policy.py`
- Modify: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`

**Interfaces:**
- Consumes: `run_book_program_portfolios(...)` and `_authored_projection_identity_evidence(...)`.
- Produces: diagnostic runs that never enable visible-step fallback and identity evidence that always rejects unrequested step collapse.

- [x] **Step 1: Write failing tests for environment injection and identity bypass**
- [x] **Step 2: Run the focused test module and confirm both failures**
- [x] **Step 3: Remove diagnostic environment injection and make the compatibility argument non-bypassable**
- [x] **Step 4: Run the focused module and existing authored-projection tests**
- [x] **Step 5: Record the checkpoint in MAAS session memory**

### Task 2: Audit rare-form scheduling after morphology preservation

**Files:**
- Review: `ARR/backend/design/maas/creative_family_registry.py`
- Review: `ARR/backend/design/maas/book_language/competition_breadth_scheduler.py`
- Review: `ARR/backend/design/maas/book_language/portfolio_selection.py`

**Interfaces:**
- Consumes: UnitBox-derived family supply and final certified morphology evidence.
- Produces: a separate follow-up design for mostly rectilinear BaseVolume outcomes with bounded triangular, elliptical/disc, oblique, and interlocking outcomes.

- [x] **Step 1: Measure configured supply proportions without generating a portfolio**
- [x] **Step 2: Compare configured proportions with the latest r318 final-mesh classifications**
- [x] **Step 3: Define the next TDD checkpoint without changing selector law gates**
