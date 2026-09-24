# MAAS Memory and BaseVolume Axis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the independent base-form, Matrix4, BOOK fraction, orientation, and operation axes while making the current MAAS contract reliably loadable by AI agents.

**Architecture:** A numbered memory bundle with a machine-readable manifest replaces the mixed 700-line authority file. The geometry author contract exposes UnitBox-derived form capabilities separately from the unchanged BOOK p.3 fraction grammar, and the existing production selector remains the rejection authority.

**Tech Stack:** Python, Django tests, typed GeometryProgram AST, manifold3d, JSON/Markdown contracts.

## Global Constraints

- No deterministic MASS morphology templates or fallback.
- Exactly one canonical UnitBox and one global homogeneous Matrix4 per authored candidate.
- BOOK p.3 fractions remain `1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`.
- The LLM owns form selection and typed parameters; code only compiles and validates.
- No canonical run before exact production fit and utilization `>=0.70` preflight.

---

### Task 1: Modular memory contract

**Files:**
- Create: `backend/design/maas/agents/maas_geometry_agent/memory/manifest.json`
- Create: numbered Markdown modules under the same directory
- Modify: `backend/design/maas/agents/maas_geometry_agent/memory/MEMORY.md`
- Test: `backend/design/test_maas_geometry_memory_contract.py`

**Interfaces:**
- Consumes: current `MEMORY.md` authority and run history.
- Produces: deterministic read order plus focused current contracts.

- [ ] Write a failing test that loads `manifest.json`, requires every ordered module, and checks the causal lineage and prefreeze gate phrases.
- [ ] Run the test and confirm failure because the manifest is absent.
- [ ] Create the manifest/modules, preserve legacy text under `history/`, and reduce `MEMORY.md` to the mandatory loader and first rule.
- [ ] Run the memory contract test and confirm pass.

### Task 2: Independent base-form author axis

**Files:**
- Modify: `backend/design/maas/geometry_language/base_seeds.py`
- Modify: `backend/design/maas/geometry_language/mutation.py`
- Modify: `backend/design/maas/geometry_language/llm_adapter.py`
- Modify only if required by the typed capability: `backend/design/maas/geometry_language/ast.py`, `compiler.py`
- Test: `backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Consumes: one canonical UnitBox.
- Produces: LLM-selectable prismatic, elliptical, and simplex/tetrahedral form capabilities before the global Matrix4 and BOOK scope.

- [ ] Write failing tests for author-schema exposure, prompt ordering, and executable UnitBox-derived ellipse/simplex programs.
- [ ] Run only those tests and confirm the missing author capability failures.
- [ ] Add the minimal typed capability contracts without generating any candidate morphology table.
- [ ] Run the focused tests and existing UnitBox/affine normalization tests.

### Task 3: Cross-axis offer and prefreeze regression

**Files:**
- Modify: `backend/design/maas/geometry_language/llm_adapter.py`
- Test: `backend/design/test_maas_geometry_language.py`
- Test: `.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/test_static_packager_v11.py`

**Interfaces:**
- Consumes: base-form capability, exact BOOK path offer, normalized legal/capacity context.
- Produces: explicit independent-axis prompt evidence and fail-closed prefreeze evidence.

- [ ] Write failing tests proving the prompt does not collapse base form into fraction and compiler-only evidence cannot claim legal preflight.
- [ ] Run the focused tests and confirm failure.
- [ ] Add the minimal prompt/evidence contract fields and validation.
- [ ] Run focused and authorship suites.

### Task 4: Production regression and new MASS

**Files:**
- No morphology generator files.
- Produce only direct LLM-authored candidate evidence after Tasks 1-3 pass.

**Interfaces:**
- Consumes: corrected memory/harness and live legal/capacity contract.
- Produces: one candidate result at a time, then the exact twenty-candidate portfolio.

- [ ] Run geometry-language, floorwise legal, authored projection identity, and static authorship suites.
- [ ] Author one fresh AST with a corrected bounded offer.
- [ ] Run exact production prefreeze; discard unchanged on null fit or utilization below `0.70`.
- [ ] Canonical-validate exactly once only after prefreeze pass.
- [ ] Repeat sequentially until twenty independently authored hard-pass candidates exist, then render and inspect the combined PNG and frontend graph.

