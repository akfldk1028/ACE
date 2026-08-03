# MASS flow authority repair, Tasks 1-5

Date: 2026-08-03 KST

## Objective

Restore a truthful, diverse MASS pipeline before elevation work. The target flow remains:

`UnitBox -> Matrix4 BaseVolume -> LLM GeometryProgram/AST -> BOOK/typed CSG -> principal-frame placement -> floorwise legal/GFA/parking -> exact render/VLM -> typed AST revision -> diverse exact selection -> MASS`

No named-building recipes or complete-form hardcoding were introduced.

## Completed repairs

1. Exact VLM base identity and descendant release
   - Replaced coarse parent-key collapse with fingerprint/hash identity.
   - Preserved multiple exact hard-pass bases and failed ambiguous descendants closed.

2. Typed terminal materialization failures
   - Added one bounded terminal reason per failed materialization invocation.
   - Kept affine/deficit events separate from terminal failures.

3. Visual authority
   - Removed automatic legal-floor loft/prism replay as final visual authority.
   - Authored Matrix4 projection and authored profiled legal clip remain authoritative.
   - Intentional authored stepped AST remains valid; accidental floor replay convergence does not.

4. Atomic projected visual handoff
   - Present malformed or empty authority fails closed before mutation/render.
   - Valid projected surfaces replace prior surfaces atomically.
   - Focused tests: 9 passed.
   - Residual test gap: the full `run_book_program_portfolios` render boundary is too coupled for a bounded entrypoint test; production ordering was independently reviewed.

5. Capacity and finalization authority
   - `combined_hard_pass` now includes resolved capacity in addition to legal, geometry retention, parking, and semantic projection.
   - Full and smoke portfolios use the same final downstream cardinality/all-pass gate.
   - Final rows persist resolved capacity and semantic evidence, not only a boolean.
   - Strict finalization rejects missing, empty, partial, failed, or identity-mismatched evidence.
   - Final geometry identity is established before binding; self-comparison and post-bind overwrite were removed.
   - Relaxed finalization is explicitly diagnostic and non-publishable across passport, artifact, downstream row, and final row.
   - Archive and passport share resolved capacity semantics, including the shared-floor contract.
   - Focused tests: Task 5A 6 passed; Task 5B 14 passed.

6. Count semantics
   - Added `legal_fit_failure_count_unit=deficit_reason_event`.
   - Added `terminal_materialization_failure_count_unit=failed_materialization_invocation`.
   - Added invocation and terminal totals with sum invariants.
   - A real `_program_pool` test covers one failed evaluation followed by one successful evaluation.
   - Focused tests: 4 passed.

## Newly confirmed Task 6 input

The capacity geometry retry body is production-dead under the current policy:

`geometry_retry_bypassed = bool(retry_required)` and the body requires `retry_required and not geometry_retry_bypassed`.

Do not hide this with a test-only seam. Task 6 must decide explicitly whether to keep diagnostic-only behavior or enable a bounded, real retry policy. This decision belongs with target-aware VLM/repair supply because it directly controls how many exact candidates survive to final review.

## Validation discipline

Only focused tests were run during Tasks 1-5. No broad suite, VLM call, full MASS run, or PNG claim has been made yet. The next full evidence point is one bounded target-3 run followed by exact report and PNG inspection.
