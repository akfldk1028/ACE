# Language Legal MASS Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show all evaluated MASS candidates together in the existing `/design/language` graph and gallery with fail-closed law, capacity, parking, program, VLM, and selection evidence.

**Architecture:** A backend contract classifies persisted stage evidence, a bounded ledger retains both accepted and rejected candidates, and a read-only catalog exposes the records. Focused React adapter, filter, badge, evidence, and portfolio-view modules consume the manifest; `BookLanguageFlow.tsx` only coordinates fetching and selection.

**Tech Stack:** Python 3.13, Django, JSON evidence contracts, React, TypeScript, Vitest, Testing Library, `LanguageNetworkCanvas`, browser verification.

## Global Constraints

- Reuse `/design/language`; do not add another route.
- Never infer legal PASS from a render, family, score, or frontend logic.
- Missing/invalid evidence is `not_evaluated`; hash-integrity failure is `fail`.
- Preserve rejected candidates and ordered terminal reasons.
- Keep VLM separate from deterministic legal status.
- Render a target-20 run on one screen without pagination.
- Never substitute another MASS image when preview evidence is absent.
- Do not weaken any geometry, law, capacity, parking, program, VLM, morphology, or selection gate.
- Keep classification and presentation outside the already-large `BookLanguageFlow.tsx`.

## File ownership

- `portfolio_evaluation_contract.py`: statuses, candidate contract, classifier.
- `portfolio_evaluation_ledger.py`: bounded run-local decision storage.
- `portfolio_evaluation_catalog.py`: persisted-run validation and API payload.
- `mass-portfolio-types.ts`: frontend DTOs only.
- `mass-portfolio-adapter.ts`: pure manifest-to-card/graph conversion.
- `MassPortfolioFilters.tsx`: overall and per-stage filters.
- `MassStatusBadge.tsx`: accessible status label.
- `MassPortfolioEvidence.tsx`: selected-card evidence.
- `MassPortfolioView.tsx`: portfolio graph and all-card gallery composition.
- `BookLanguageFlow.tsx`: fetch, selected key, and view mounting only.

---

### Task 1: Fail-closed evaluation contract

**Files:**
- Create: `backend/design/maas/book_language/portfolio_evaluation_contract.py`
- Test: `backend/design/test_maas_portfolio_evaluation_contract.py`

**Interfaces:**
- Produces `StageDecision`, `CandidateEvaluation`, and `classify_candidate_evaluation(stage_decisions, *, selected, integrity_failures) -> str`.
- Stage values are `pass | fail | not_evaluated`; overall values are `selected | legal_pass | failed | not_evaluated`.

- [ ] Write tests proving five deterministic PASS stages produce `legal_pass` even when VLM is not evaluated, any deterministic failure produces `failed`, a missing stage produces `not_evaluated`, and a hash mismatch produces `failed`.
- [ ] Run `python manage.py test design.test_maas_portfolio_evaluation_contract -v 2`; expect missing-module RED.
- [ ] Implement frozen dataclasses, exact seven-stage validation, ordered reason normalization, and the pure classifier.
- [ ] Re-run the focused test; expect PASS.
- [ ] Commit only the contract and test with `git commit -m "feat: add fail-closed mass evaluation contract"`.

Core assertion:

```python
assert classify_candidate_evaluation(
    deterministic_pass_with_vlm_not_evaluated,
    selected=False,
    integrity_failures=(),
) == "legal_pass"
```

### Task 2: Bounded evaluation ledger

**Files:**
- Create: `backend/design/maas/book_language/portfolio_evaluation_ledger.py`
- Test: `backend/design/test_maas_portfolio_evaluation_ledger.py`

**Interfaces:**
- Consumes Task 1 decisions.
- Produces `PortfolioEvaluationLedger.begin_candidate(...)`, `.record_stage(...)`, `.finalize_candidate(...)`, and `.evidence()`.

- [ ] Write tests for twenty retained records, ordered reasons, repeated stage updates, rejected-record persistence, preview absence, candidate/hash rebinding rejection, and explicit truncation evidence.
- [ ] Run `python manage.py test design.test_maas_portfolio_evaluation_ledger -v 2`; expect RED.
- [ ] Implement a candidate-ID keyed ledger that deep-copies evidence, rejects identity rebinding, and emits `arr.maas.portfolio_evaluation_ledger.v1`.
- [ ] Run Task 1 and Task 2 tests together; expect PASS.
- [ ] Commit only the ledger and test with `git commit -m "feat: persist full mass evaluation ledger"`.

Expected evidence shape:

```python
{
    "schema_version": "arr.maas.portfolio_evaluation_ledger.v1",
    "target_count": 20,
    "records": [{"candidate_id": "maas_01", "overall_status": "failed", "stages": {}}],
    "records_truncated": False,
}
```

### Task 3: Existing BOOK gate wiring

**Files:**
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Test: `backend/design/test_maas_portfolio_evaluation_wiring.py`

**Interfaces:**
- Consumes Task 2 ledger.
- Produces result key `portfolio_evaluation` and artifact `maas-portfolio-evaluation.json`.

- [ ] Write a test fixture with one deterministic pass, one geometry failure, one parking failure, and one unreviewed candidate; assert all survive with exact terminal reasons and existing gate return values remain unchanged.
- [ ] Run `python manage.py test design.test_maas_portfolio_evaluation_wiring -v 2`; expect absent-ledger RED.
- [ ] Instantiate one ledger per program run and add recording calls only at existing compile, law, capacity, parking, program, VLM, and selection boundaries. Never recalculate a decision.
- [ ] Finalize every attempted candidate and atomically write the ledger artifact.
- [ ] Run the wiring test plus `design.test_legal_mass_archive` and `design.test_maas_paid_provider_budget`; expect PASS and unchanged gate counts.
- [ ] Commit task files only with `git commit -m "feat: record complete BOOK candidate decisions"`.

### Task 4: Read-only evaluation catalog and API

**Files:**
- Create: `backend/design/maas/portfolio_evaluation_catalog.py`
- Modify: `backend/design/views.py`
- Modify: `backend/design/urls.py`
- Test: `backend/design/test_maas_portfolio_evaluation_api.py`

**Interfaces:**
- Produces `GET /api/design/maas/portfolio-evaluations/?run_id=<id>` with schema `arr.maas.portfolio_evaluation_manifest.v1`.

- [ ] Write tests for explicit/latest run selection, path traversal rejection, missing run, invalid schema, hash mismatch downgrade, failed-record retention, and missing preview.
- [ ] Run `python manage.py test design.test_maas_portfolio_evaluation_api -v 2`; expect RED.
- [ ] Implement root-bounded path resolution, v1 validation, integrity downgrade, evidence URLs, and a thin Django view.
- [ ] Run the new API test plus existing creative catalog/API tests; expect PASS.
- [ ] Commit task files only with `git commit -m "feat: expose mass portfolio evaluation manifest"`.

API record invariant:

```python
assert record["preview_url"] == "" if not record["renderable"] else record["preview_url"].startswith("/api/design/")
```

### Task 5: Frontend types, adapter, API, and filters

**Files:**
- Create: `frontend/src/design/components/book-language-flow/mass-portfolio-types.ts`
- Create: `frontend/src/design/components/book-language-flow/mass-portfolio-adapter.ts`
- Create: `frontend/src/design/components/book-language-flow/MassPortfolioFilters.tsx`
- Modify: `frontend/src/design/lib/api-client.ts`
- Test: `frontend/test/unit/design/mass-portfolio-adapter.test.ts`
- Test: `frontend/test/unit/design/MassPortfolioFilters.test.tsx`

**Interfaces:**
- Produces `adaptMassPortfolio(manifest)` returning cards, graph nodes/edges, stage order, and counts.
- Produces `filterMassPortfolioCards(cards, filters)` and `getMassPortfolioEvaluation(signal?, runId?)`.

- [ ] Write tests proving twenty records survive adaptation, failure branches retain reasons, pre-legal values stay not-evaluated, filters select exact classes/stages, and missing previews remain missing.
- [ ] Run `npm test -- --run test/unit/design/mass-portfolio-adapter.test.ts test/unit/design/MassPortfolioFilters.test.tsx`; expect RED.
- [ ] Implement discriminated TypeScript types, a pure adapter, pure filter function, and the typed fetch call. Unknown statuses normalize to `not_evaluated`.
- [ ] Re-run focused tests; expect PASS.
- [ ] Commit task files only with `git commit -m "feat: adapt typed legal mass portfolio evidence"`.

### Task 6: Modular graph/gallery/evidence UI

**Files:**
- Create: `frontend/src/design/components/book-language-flow/MassStatusBadge.tsx`
- Create: `frontend/src/design/components/book-language-flow/MassPortfolioEvidence.tsx`
- Create: `frontend/src/design/components/book-language-flow/MassPortfolioView.tsx`
- Create: `frontend/src/design/components/book-language-flow/mass-portfolio.css`
- Modify: `frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Test: `frontend/test/unit/design/MassPortfolioView.test.tsx`
- Test: `frontend/test/unit/design/BookLanguageFlow.test.tsx`

**Interfaces:**
- Produces `MassPortfolioView({ portfolio, selectedKey, onSelect })`.

- [ ] Write tests rendering a 20-record fixture: twenty buttons are present together, status is textual, terminal reason is visible, missing preview shows `NO RENDERABLE MASS`, card selection updates evidence, and graph selection shares the stable key.
- [ ] Run the two focused component tests; expect missing-component RED.
- [ ] Implement badge-only, evidence-only, and composition-only components. Use a five-column desktop grid for exactly four rows at target 20; responsive widths may reduce columns without hiding cards.
- [ ] Modify `BookLanguageFlow` only to fetch the manifest, hold the selected key, mount `MassPortfolioView`, and rename `CREATIVE 100` to `MASS PORTFOLIO`.
- [ ] Run focused tests plus `LanguageNetworkCanvas` and legacy creative filter tests; expect PASS.
- [ ] Commit task files only with `git commit -m "feat: show all legal mass decisions in language graph"`.

### Task 7: Full verification and one combined PNG

**Files:**
- Modify: `backend/design/maas/README.md`
- Create: `docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-05-language-legal-mass-portfolio.md`
- Create: new run-scoped evidence under `docs/playwright/design-route-live-verify/`.

- [ ] Run Tasks 1-4 backend tests plus legal archive, portfolio contract, paid-provider-budget, and creative portfolio suites; require PASS.
- [ ] Run Tasks 5-6 frontend tests, `npm run typecheck`, and existing design unit tests; require PASS.
- [ ] Materialize a bounded zero-paid PNU `1168011800104170004` evaluation. Persist deterministic decisions and leave VLM honestly `not_evaluated`.
- [ ] Start backend/frontend and open `/design/language`; select `MASS PORTFOLIO`.
- [ ] Verify 20 cards appear together, ALL/PASS/FAIL/NOT EVALUATED filters work, one pass and one fail select the correct graph branch/evidence, and there are no broken images or error overlays.
- [ ] Capture and directly inspect one full-page PNG containing the graph/evidence region and all twenty cards.
- [ ] Record PNG dimensions/hash, nonblank-card count, run ID, stage counts, and legal status counts in the checkpoint.
- [ ] Commit only task-owned files. Preserve unrelated dirty work and record any overlapping file that cannot be safely committed.
