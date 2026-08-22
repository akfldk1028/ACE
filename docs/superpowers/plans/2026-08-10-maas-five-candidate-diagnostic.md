# MAAS Five-Candidate Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the unmodified MAAS production gates on five distinct persisted OAuth-authored inputs and emit one honest five-card PNG without paid provider calls.

**Architecture:** Add `5` to the existing diagnostic-target boundary only. Reuse the generic bounded diagnostic budget and the existing selector, legal, program, parking, mesh, diversity, and renderer implementation; then execute the immutable C89 manifest through that path.

**Tech Stack:** Django management command, Python, Shapely/GEOS, Manifold3D, NumPy, persisted Codex/OAuth GeometryProgram manifests.

## Global Constraints

- Do not call paid LLM or VLM providers.
- Do not run target 20 and crop its output.
- Do not change morphology, law, GFA, parking, identity, duplicate, stepped, wedge, or selection thresholds.
- Preserve the C89 manifest and admission bytes unchanged.
- A partial result remains diagnostic failure evidence and must not be reported as five successful candidates.

---

### Task 1: Admit bounded diagnostic target 5

**Files:**
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `ARR/backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Test: `ARR/backend/design/test_maas_mass_product_evidence.py`
- Test: `ARR/backend/design/test_maas_book_language.py`

**Interfaces:**
- Consumes: `diagnostic_generation_budget(target: int | None)` and the Django command parser.
- Produces: target 5 accepted with all six BOOK `scope_labels`, `evaluation_cap=60`, `candidate_cap=20`, and `replenishment_cycle_cap=1`.

- [ ] **Step 1: Write failing target-5 budget and CLI parser tests**

```python
budget = diagnostic_generation_budget(5)
self.assertEqual(len(budget["scope_labels"]), 6)
self.assertEqual(budget["evaluation_cap"], 60)
self.assertEqual(budget["candidate_cap"], 20)

options = Command().create_parser("manage.py", command_name).parse_args([
    "--diagnostic-target", "5",
])
self.assertEqual(options.diagnostic_target, 5)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python ARR/backend/manage.py test design.test_maas_mass_product_evidence.MaasMassProductEvidenceTest design.test_maas_book_language.MaasBookLanguageRegistryTest --verbosity 1`

Expected: the target-5 budget raises `ValueError` and the parser rejects `5`.

- [ ] **Step 3: Add 5 to the shared diagnostic options and CLI choices**

```python
DIAGNOSTIC_TARGET_OPTIONS = (1, 2, 3, 5, 20)

parser.add_argument(
    "--diagnostic-target",
    type=int,
    choices=(1, 2, 3, 5, 20),
    default=None,
)
```

Update the two validation messages to list `1, 2, 3, 5, or 20`.

- [ ] **Step 4: Re-run the focused tests and verify GREEN**

Run the same Django test command. Expected: `OK` with zero failures.

### Task 2: Execute and inspect C105

**Files:**
- Read: `ARR/.superpowers/sdd/2026-08-05-llm-authored-diverse-legal-mass/tmp-v31-c53-b01/codex-mass-manifest-c89-v11-balanced36.json`
- Read: matching `-admission.json`
- Generate: `docs/playwright/design-route-live-verify/legal-mass-v31-c105-c89-diverse5/`
- Modify: `ARR/backend/design/maas/agents/maas_geometry_agent/memory/09_CURRENT_STATE.md`

**Interfaces:**
- Consumes: C89 session ID, request ID, manifest SHA-256, and all 36 admitted program hashes.
- Produces: a diagnostic run state, evaluation JSON, exact geometry artifacts, and `maas-book-neighborhood-5.png`.

- [ ] **Step 1: Verify manifest SHA-256 and admission count**

Run `Get-FileHash -Algorithm SHA256` and compare it with `ca70b84a603d53c1c4458fbaa5aa1b30010651333ba6e1d28929af7d7bec2b3c`; verify 36 admitted hashes.

- [ ] **Step 2: Run one target-5 diagnostic**

Run `benchmark_maas_book_program_portfolios` with PNU `1168011800104170004`, program `neighborhood`, diagnostic target `5`, and the exact C89 admission arguments. Do not pass `--live-llm-author` or `--live-vlm`.

- [ ] **Step 3: Verify machine evidence**

Require selected, compiled, and program-passed counts sufficient for five; verify each selected candidate's law/program/parking hard pass, unique program/geometry hashes, measured diversity facts, and PNG existence. If selected count is below five, stop and report the typed deficits.

- [ ] **Step 4: Inspect the combined PNG**

Open the PNG at original resolution. Report visible repetition, stepped count, wedge count, and whether the five forms are materially distinct; do not infer visual success from labels.

- [ ] **Step 5: Record C105 evidence**

Append exact counts, duration, hashes, metrics, and PNG path to `09_CURRENT_STATE.md`. Keep publishable target-20 status separate from five-candidate diagnostic evidence.
