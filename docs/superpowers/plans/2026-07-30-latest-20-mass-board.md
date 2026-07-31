# Latest 20 MASS Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate one zero-paid 5x4 PNG board from twenty unique cached LLM-authored GeometryPrograms.

**Architecture:** Add a cache-pool reader with a deterministic program-hash
dedupe contract, expose it as an explicit `cache_pool` author mode on the
existing creative portfolio command, and reuse existing compilation, render,
archive, and board persistence. This phase remains explicitly pre-legal.

**Tech Stack:** Python 3, Django management commands, Pillow, MAAS GeometryProgram compiler.

## Global Constraints

- Use only accepted `arr.maas.geometry_llm_author_cache.v3` exact programs.
- Never select a named recipe or silently fall back to fixtures.
- Use canonical `1/1 UnitBox` normalization.
- Make zero paid provider requests.
- Persist `PRE-LEGAL / NOT EVALUATED`; do not claim law or parking acceptance.
- Produce exactly twenty unique program and geometry identities.

---

### Task 1: Accepted LLM cache-pool reader

**Files:**
- Modify: `ARR/backend/design/maas/creative_program_author.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`

**Interfaces:**
- Produces: `authored_programs_from_cache_pool(cache_root: Path, expected_count: int) -> tuple[CreativeAuthoredProgram, ...]`

- [ ] Write a failing test with accepted, rejected, duplicate, and malformed cache files.
- [ ] Run the focused test and verify failure because the reader does not exist.
- [ ] Implement deterministic file ordering, schema/status validation, exact-program parsing, and program-hash dedupe.
- [ ] Run the focused test and verify the requested unique programs are returned without recipes.

### Task 2: Explicit cache-pool command mode

**Files:**
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`

**Interfaces:**
- Consumes: `authored_programs_from_cache_pool`
- Produces: CLI options `--author-mode cache_pool` and `--author-cache-root`

- [ ] Write a failing command test requesting two cached programs with no API key.
- [ ] Run the focused test and verify the mode is rejected before implementation.
- [ ] Add the explicit mode and required directory argument with no fallback.
- [ ] Run the focused test and verify two candidate JSONs and one board are written with paid counts zero.

### Task 3: Twenty-card review board

**Files:**
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`

**Interfaces:**
- Produces: a 5-column board for exactly twenty items and explicit pre-legal labels.

- [ ] Write a failing board-layout test for twenty items.
- [ ] Run the focused test and verify the current 10-column board fails.
- [ ] Make the board column count resolve to five for a twenty-candidate run and prefix its labels with `PRE-LEGAL`.
- [ ] Run the focused test and existing command tests.

### Task 4: Generate and verify the real latest board

**Files:**
- Create: `docs/mass/maas-latest-20-cache-pool-20260730/`
- Modify: `docs/ai-session-memory/MAAS_LAWFUL_DIVERSE_LLM_PILOT_20260730.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: accepted local author cache directory and PNU `1168011800104170004`
- Produces: `maas-creative-board.png`, twenty renders, identities, and updated recovery memory.

- [ ] Run the cache-pool command with `count=20` and no VLM pilot.
- [ ] Verify candidate count, unique program hashes, unique geometry hashes, PNG dimensions, and paid request counts.
- [ ] Inspect the generated board directly.
- [ ] Update memory with artifact paths, hashes, exact status, and the remaining legal-evaluation requirement.
- [ ] Run focused tests, Python compilation, JSON parsing, and `git diff --check`.

