# MASS–Elevation Frontend Stabilization Design

**Date:** 2026-07-25
**Scope:** `frontend/src/design/components/book-language-flow` and Electron packaging assets/config only

## Context

The current MASS–elevation route renders the latest `r230` execution correctly, including the compiler MASS image, creative elevation alternate where available, and six deterministic geometry views. A legacy `r182` timeline selection, however, crashes the whole application because its passport contains `agent_collaboration: {}` without an `identity` object. The same screen is also cramped around 1366 px, one focused design test still expects an obsolete elevation-agent label, and the Electron package build is blocked by missing icon files.

The UI must continue to distinguish deterministic six-view geometry verification from creative elevation output. It must not imply that the eight MASS records without generated elevation proposals are complete.

## Chosen Approach

Apply a focused production-stabilization pass instead of either a one-line hotfix or a broad frontend rewrite.

1. Harden legacy passport handling and add a regression test for an empty collaboration object.
2. Isolate evidence-panel rendering failures so a malformed historical record cannot white-screen the entire route.
3. Keep the accurate `6-VIEW GEOMETRY VERIFICATION` wording and update the stale test.
4. Improve the toolbar and workspace layout at laptop widths without changing the desktop information architecture.
5. Restore Electron packaging icons by reusing an existing repository visual source; do not invent a new brand asset.
6. Verify both the current `r230` path and the previously crashing `r182` path in a real browser.

## Data Contract and Error Handling

Execution identity resolution will treat every nested legacy field as optional. A `single-execution:` run id remains the preferred identity source; otherwise the UI reads `passport.agent_collaboration.identity.execution_id` only when the complete path exists.

`ExecutedMassEvidence` remains responsible for evidence presentation. It will receive a local React error boundary at its integration point. The fallback will identify the affected evidence panel and keep timeline navigation and the rest of the MASS route available. This is a last-resort guard, not a substitute for validating known fields.

## Testing Strategy

Tests are written or updated before implementation:

- A passport with `agent_collaboration: {}` renders without throwing.
- The evidence heading asserts `6-VIEW GEOMETRY VERIFICATION`.
- The local error boundary renders a contained fallback when its child throws.
- Existing focused design tests remain green.

After implementation:

- run the focused design Vitest suite;
- run TypeScript type checking;
- run the web production build;
- run the Electron packaging command far enough to prove icon resolution;
- use browser automation to select both `r230-03-radial-cross` and `book-program-portfolios-r182-seven-page-closure-pass`;
- check for a nonblank route, expected evidence content, image load failures, and console errors at desktop and 1366 px widths.

The unrelated legacy ChatBox, SearchInput, Terminal, and installation-setup failures are recorded but excluded from this change.

## Responsive Behavior

At wide desktop widths, the existing two-column workspace remains unchanged. At laptop widths, metadata groups may wrap into stable rows, long run identifiers are truncated with a discoverable full value, and the evidence column is allowed to narrow without collapsing labels into vertical text. At small widths, the existing single-column breakpoint remains authoritative.

## Packaging Assets

The repository is searched for an existing square project logo or icon. If found, it is used to produce the Windows `.ico` required by `electron-builder`; macOS configuration is aligned only when a valid existing source supports it. If no suitable source exists, the build config is changed only where the packager accepts a verified fallback—no placeholder branding is silently introduced.

## Non-Goals

- Generating missing creative elevations for the other eight MASS records
- Claiming VLM, facade, section, or mesh-consistency approval that has not occurred
- Refactoring the full `BookLanguageFlow` component or virtualizing the complete timeline
- Fixing the 71 unrelated legacy frontend test failures
- Changing MASS generation, elevation-agent, or backend memory behavior

## Completion Criteria

The work is complete when the previously crashing legacy run can be selected without losing the page, the current run still displays correct evidence semantics, laptop-width layout is readable, focused tests and type checking pass, browser verification has no route-breaking console error, and packaging no longer fails because the configured icon is absent.
