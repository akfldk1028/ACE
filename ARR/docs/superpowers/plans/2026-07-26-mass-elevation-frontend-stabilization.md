# MASS–Elevation Frontend Stabilization Implementation Plan

> **Design:** `docs/superpowers/specs/2026-07-25-mass-elevation-frontend-stabilization-design.md`

**Goal:** Keep legacy and current MASS runs navigable, preserve evidence truth, improve laptop-width layout, and restore the configured Electron packaging asset.

**Architecture:** Harden the evidence component at the legacy-data boundary, contain unexpected evidence-render failures with a small local React boundary, and adjust only the existing flow toolbar/workspace CSS. Reuse the existing Eigent logo source for packaging instead of introducing new branding.

**Tech Stack:** React 18, TypeScript, Vitest, Testing Library, Vite, Electron Builder, Playwright/agent-browser.

---

## Task 1: Lock the legacy-passport regression

**Files:**

- Modify: `frontend/test/unit/design/ExecutedMassEvidence.test.tsx`
- Modify: `frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`

1. Add a test that renders a non-single legacy run with `agent_collaboration: {}`.
2. Run the focused test and confirm the current implementation throws.
3. Make nested identity access fully optional.
4. Run the focused test and confirm it passes.

## Task 2: Contain evidence-panel failures

**Files:**

- Create: `frontend/src/design/components/book-language-flow/EvidencePanelBoundary.tsx`
- Create: `frontend/test/unit/design/EvidencePanelBoundary.test.tsx`
- Modify: `frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `frontend/src/design/components/book-language-flow/book-language-flow.css`

1. Add a failing test with a child that throws.
2. Implement a local error boundary with an accessible evidence-unavailable fallback.
3. Wrap only `ExecutedMassEvidence`, keyed by run and MASS so selection resets the boundary.
4. Style the fallback within the evidence column.

## Task 3: Preserve accurate six-view semantics

**Files:**

- Modify: `frontend/test/unit/design/ExecutedMassEvidence.test.tsx`

1. Replace the obsolete `ELEVATION AGENT` expectation with `6-VIEW GEOMETRY VERIFICATION`.
2. Keep image-count and preview-URL assertions.
3. Run all focused design tests.

## Task 4: Stabilize laptop-width layout

**Files:**

- Modify: `frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `frontend/src/design/components/book-language-flow/book-language-flow.css`

1. Give the selected run label a full-value title and stable truncation container.
2. Add a laptop breakpoint that wraps metadata groups, prevents vertical identifier wrapping, and narrows the evidence column safely.
3. Preserve the existing small-screen single-column breakpoint.
4. Verify at 1920×1080, 1366×768, and a compact viewport.

## Task 5: Restore packaging icon resolution

**Files:**

- Create or restore: `frontend/build/icon.ico`
- Modify only if required: `frontend/electron-builder.json`

1. Inspect repository history and existing Eigent logo assets.
2. Produce the required multi-size ICO from the existing square logo source without altering its design.
3. Run the Windows packaging command and confirm it proceeds beyond icon resolution.

## Task 6: Full verification and delivery

**Files:**

- Modify only files listed above plus verification artifacts if intentionally retained.

1. Run `npx vitest run test/unit/design`.
2. Run `npm run type-check`.
3. Run `vite build --mode web`.
4. Run the applicable Electron Builder Windows packaging check.
5. In a real browser, verify `r230-03-radial-cross` and `book-program-portfolios-r182-seven-page-closure-pass`, image loading, console errors, and responsive layout.
6. Review the diff against the approved scope.
7. Commit only the MASS–elevation stabilization files and push `master` to its configured upstream.
