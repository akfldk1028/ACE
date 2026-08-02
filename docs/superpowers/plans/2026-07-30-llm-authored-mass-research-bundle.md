# LLM-Authored MASS Research Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove required family-recipe selection from the production creative MASS path and persist a complete elevation-research folder for every compiled MASS.

**Architecture:** The portfolio builder accepts authored `GeometryProgram` objects through a source-neutral contract, compiles and gates them, then classifies morphology after geometry exists. The command exposes explicit payload, live-LLM, and fixture modes. A separate artifact writer creates hash-bound program, transform, mesh, OBJ/CSV, six-view, and elevation-research files without creating a second geometry authority.

**Tech Stack:** Python 3, Django management commands/tests, existing typed GeometryProgram compiler and OpenAI author adapter, Pillow elevation projection, JSON/CSV/OBJ.

## Global Constraints

- One canonical `1/1 UnitBox`; named completed-form recipes are not production authoring authority.
- Paid provider calls require explicit `llm` author mode and credentials.
- Compiler/gates own geometry truth; the LLM owns typed intent only.
- Family classification happens after compilation and cannot invoke builders.
- Every research artifact is bound to run, candidate, program, geometry, and PNU identity.
- Research bundles remain pre-legal and set `geometry_mutation_allowed=false`.
- Preserve existing candidate JSON/render/frontend compatibility paths.

---

### Task 1: Record the architecture and memory checkpoint

**Files:**
- Create: `docs/superpowers/specs/2026-07-30-llm-authored-mass-research-bundle-design.md`
- Create: `docs/superpowers/plans/2026-07-30-llm-authored-mass-research-bundle.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/06_ELEVATION_HANDOFF.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`

- [x] Write the approved recipe-demotion, author-source, post-hoc family, and MASS-folder decisions.
- [x] Parse `current-checkpoint.json` to prove the machine-readable memory remains valid JSON.

### Task 2: Add the recipe-independent authored-program path

**Files:**
- Create: `ARR/backend/design/maas/creative_program_author.py`
- Create: `ARR/backend/design/test_maas_creative_program_author.py`
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`

**Interfaces:**
- Produces: `CreativeAuthoredProgram(program, author_evidence)`.
- Produces: `authored_programs_from_payload(payload, expected_count)`.
- Produces: `posthoc_family_label(program, compilation, descriptor)`.
- Consumes: `build_creative_floor_portfolio(..., authored_programs=...)`.

- [x] Write a test injecting arbitrary typed programs while patching the recipe registry to raise if called.
- [x] Run the test and verify it fails because the authored-program parameter does not exist.
- [x] Implement the source-neutral dataclass, payload adapter, authored scheduling, and post-hoc classifier.
- [x] Run the focused author and portfolio tests and verify they pass.

### Task 3: Expose explicit author modes in the command

**Files:**
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Modify: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`

**Interfaces:**
- `--author-mode payload --author-payload <json>`
- `--author-mode llm [--author-model <model>]`
- `--author-mode recipe_fixture`

- [x] Write tests for payload mode and for missing LLM credentials failing without recipe fallback.
- [x] Run both tests and verify the expected failures.
- [x] Load structured payloads with the existing compiler-validating adapter; call the live author only in explicit `llm` mode; retain fixture mode for compatibility.
- [x] Run command tests and verify author source evidence is persisted.

### Task 4: Persist one complete MASS research folder

**Files:**
- Create: `ARR/backend/design/maas/creative_research_bundle.py`
- Create: `ARR/backend/design/test_maas_creative_research_bundle.py`
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`

**Interfaces:**
- Produces: `write_creative_mass_research_bundle(candidate, run_directory, run_id, pnu) -> dict`.
- Consumes: exact candidate GeometryProgram, Matrix4 trace, indexed mesh, storey evidence, and identity hashes.

- [x] Write a failing test for the exact MASS folder tree and identity manifest.
- [x] Add failing assertions that OBJ/CSV counts match the indexed mesh.
- [x] Add failing assertions for six views, camera Matrix4, stable face IDs, normals, floor guides, and facade planes.
- [x] Implement atomic JSON/CSV/OBJ writes and reuse deterministic elevation projection for views.
- [x] Link mass directory, manifest, and research handoff from candidate and portfolio records.
- [x] Run focused bundle and command tests.

### Task 5: Verify and checkpoint

**Files:**
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`

- [x] Run focused author, portfolio, command, compiler, and elevation projection tests.
- [x] Generate a small payload-authored archive and audit every relative path and SHA-256.
- [x] Parse the portfolio, candidate, mass manifest, research handoff, and current checkpoint JSON files.
- [x] Record exact pass/fail counts and any unrelated repository regressions without overstating full-suite status.
