# Ten-Alternative MASS Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:verification-before-completion. Execute sequentially because the portfolio contract changes the later generation and review budgets.

**Goal:** Produce at least ten distinct, floor-aware architectural MASS alternatives that each satisfy the same floor, law, FAR and parking contracts before paid VLM review and frontend publication.

**Architecture:** Separate portfolio completeness from smoke/cost controls in a pure contract module. Keep BaseVolume and BOOK/LLM AST authorship upstream, deterministic floor/law/FAR/parking gates in the middle, and bounded exact-solid VLM plus portfolio-board VLM downstream. A smoke run may reduce search/review effort, but it may never convert a one-candidate diagnostic into a completed alternative-design portfolio.

**Tech Stack:** Python 3, Django tests, Shapely, existing GeometryProgram/BOOK compiler, OpenAI LLM/VLM adapters, Vite/React frontend.

## Global Constraints

- Preserve unrelated dirty files and commit exact paths only.
- Minimum publishable portfolio size is 10; the historical full target remains 20.
- No paid call before deterministic floor, law, FAR and parking hard gates.
- Every published live-VLM candidate must carry an exact post-BOOK VLM hard pass.
- At least one publishable full-flow candidate must originate from an actual LLM-authored typed GeometryProgram/AST.
- Ground, piloti, basement/semi-basement, mechanical and mixed parking remain typed strategies; conceptual/review-required parking must not be reported as permit-final compliance.
- GPT Image is an elevation-only downstream step for the chosen MASS, not a MASS generator.

### Task 1: Extract the portfolio-completeness contract

**Files:**
- Create: `backend/design/maas/book_language/portfolio_contract.py`
- Create: `backend/design/test_maas_portfolio_contract.py`

- [ ] Add failing tests proving smoke still requires 10 alternatives and cannot treat a skipped VLM audit as approval.
- [ ] Add a pure requirement object with minimum 10, smoke target 10, full target 20 and all six BaseVolume scopes.
- [ ] Add fail-closed completion evidence for count, exact-solid VLM and LLM-authored AST requirements.
- [ ] Run the focused contract tests.

### Task 2: Remove the single-candidate smoke bypass

**Files:**
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Test: `backend/design/test_maas_portfolio_contract.py`

- [ ] Resolve selection and scope targets from the new contract.
- [ ] Let bounded replenishment run whenever the portfolio is below target, including smoke.
- [ ] Stop clearing ordinary portfolio failures in smoke mode.
- [ ] Record skipped board VLM as unevaluated and never as `hard_pass`.
- [ ] Rename board/output evidence so it reports the actual target.

### Task 3: Restore bounded LLM AST authorship

**Files:**
- Modify: `backend/design/maas/book_language/candidate_generation.py`
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Test: `backend/design/test_maas_geometry_language.py`
- Test: `backend/design/test_maas_portfolio_contract.py`

- [ ] Add an explicit bounded live-LLM-author option and default profile-derived synthesis requests.
- [ ] Keep authored ASTs additive to BaseVolume and universal controls.
- [ ] Prove an authored program is compiled, BOOK-projected and subjected to identical downstream gates.
- [ ] Fail a claimed full-flow completion when no selected LLM-authored AST exists.

### Task 4: Preserve legal parking alternatives

**Files:**
- Modify only if a failing regression identifies a gap in `backend/design/maas/book_language/parking_strategy.py`, `parking_layout.py` or `downstream_hard_gate.py`.
- Test: `backend/design/test_maas_export.py`

- [ ] Verify the current Seoul rule evidence computes the required count.
- [ ] Verify small self-parking/piloti, basement and mechanical-review strategies remain typed alternatives.
- [ ] Verify only physically laid out and legally accepted spaces count as hard-pass supply.
- [ ] Ensure parking strategy does not collapse the MASS portfolio to one form family.

### Task 5: Run bounded generation and paid review

**Evidence:**
- Write a fresh r274-or-later output directory under `docs/playwright/design-route-live-verify/`.

- [ ] Run deterministic generation first and inspect ten floor/law/FAR/parking-pass candidates.
- [ ] Run a bounded live LLM author and exact post-BOOK VLM review; do not run hundreds of calls.
- [ ] Require at least ten final alternatives or report the run as incomplete with exact rejection counts.
- [ ] Run one portfolio-board VLM audit and one chosen-MASS elevation flow.

### Task 6: Verify frontend, memory and publication

**Files:**
- Modify frontend only if live verification finds a data/render defect.
- Modify: `backend/design/maas/agents/maas_geometry_agent/memory/MEMORY.md`

- [ ] Run focused and broad backend regressions.
- [ ] Run frontend typecheck/tests.
- [ ] Verify `/design/language` on port 5178, broken images and browser console.
- [ ] Open the fresh portfolio PNG and selected MASS/elevation PNGs.
- [ ] Record exact flow, budgets, counts and remaining limitations in memory.
- [ ] Commit only task files and push `DK-BB`.
