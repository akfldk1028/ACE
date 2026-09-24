# Task 7 final independent review package

Read-only review of final Task 7 validator closure and formatter event.

Review:

- binding design and plan amendments;
- `task-7-report.md` and prior `task-7-review.md`;
- `iclr2027/architecture_target_roster.py`;
- `build_iclr2027_architecture_target_roster.py`;
- `tests/test_iclr2027_architecture_target_roster.py`;
- dataset/pre-call/manifest/runner only for raw/AST and integration no-drift.

Do not edit files, use git/network/credentials/subagents, inspect
held-out/test/OOD data, create candidate artifacts, or run a model/non-dry
experiment.

Required independent checks:

1. Recompute the mutation census and prove 4,524 distinct labelled attacks,
   accepted 0, 240 correctly classified top-level private-set invariants, and
   one exact-eight release invariant. Ensure row identities do not collapse.
2. Verify exact site-scoped `<site_ref>-target-NN` binding and cross-site swap
   rejection without relying only on aggregate counts.
3. Verify exact SourceCaptureV1 `evidence_families`, membership checks for all
   target families and locator site sources, and rejection of the original
   law/geometry swap.
4. Verify public source IDs reject evidence-family/repeat/alias channels while
   remaining opaque, and that exact 64-hex digests are exempt only from raw-PNU
   substring scanning—not from typed hash or other protected checks.
5. Verify omitted source objects return stable TargetRosterError and reparse
   protections remain intact.
6. Verify all 207 two-element nested-order attacks are actually enumerated and
   rejected, while the 240 top-level set permutations remain valid invariants.
7. Audit the test oracle for same-code derivation, wrong-surface expectations,
   swallowed exceptions, accepted-count collapse, or mutable shared fixtures.
8. Recompute all seven final raw pins and the five binding AST pins; confirm
   formatter AST parity and manifest/runner raw no-drift.
9. Run the exact mutation class, full target-roster module, combined seven-module
   suite, Ruff check, and Ruff format check if safe.
10. Confirm no actual candidate was frozen and no result/model data can enter
    validator authority.

Return PASS or ranked Critical/Important/Minor findings with exact file/line
evidence and fresh command results. Do not write a review file.
