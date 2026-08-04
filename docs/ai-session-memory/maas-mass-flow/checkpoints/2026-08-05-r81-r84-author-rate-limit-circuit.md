# r81-r84 Author Rate-Limit Circuit - 2026-08-05 KST

## Goal

Preserve lawful target-five MASS generation while preventing repeated paid author calls during provider rate limits. Statutory, parking, capacity, program, VLM, and diversity thresholds remain unchanged.

## Run progression

- **r81:** selected `1/5` in approximately `178s`; replenishment ledger recorded `3` skips. Typed provider diagnostics proved all `5/5` author attempts failed with HTTP `429`.
- **r82:** confirmed every replenishment cycle reached HTTP `429` before any JSON author response was available.
- **r83:** made `3` author calls and deferred `2`; fallback cooldowns of `2s` and `4s` expired during the same invocation, allowing repeated provider calls.
- **r84:** invocation-scoped no-header circuit began with `29` cached programs, made exactly `1` author call that returned HTTP `429`, and deferred the remaining `4` author opportunities. Carried geometry continued through the pipeline.

## r84 evidence

- Total paid provider requests: `2`.
- Runtime: `169.863s`.
- Selected: `1/5`.
- PNG: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r84\maas-book-neighborhood-5.png`
- The circuit bounded author transport failures without suppressing cached/carried geometry processing.

## Commit and working-tree boundary

- **`9344bb8`**: deduplicated causal replenishment identities so completed causal work can be skipped reliably.
- Typed provider diagnostics and the invocation-scoped cooldown/circuit working tree pass `51` focused tests and completed live r84.
- That work remains **uncommitted** because clean `HEAD` lacks existing dirty prerequisite dependencies including `MaasRevisionEvent` and `AGGREGATION_VERBS`; staging whole files would be unsafe.
- Do not claim the typed diagnostics/circuit as clean-HEAD or committed behavior until the dependency stack is isolated and committed safely.

## Exact next steps

1. Resolve and commit the prerequisite dirty dependency stack safely, preserving unrelated work and avoiding whole-file staging.
2. Isolate and commit the typed provider diagnostics and invocation-scoped rate-limit circuit only after those prerequisites exist on clean `HEAD`.
3. When the author provider is available, rerun one live target-five and verify author JSON responses, bounded paid calls, ledger skips, and downstream candidate growth.
4. Independently add typed profiled-mesh raw-code evidence at the materialization boundary, including failing node/operator and kernel, surface, or floor cause.
5. Do not relax law, parking, capacity, program, VLM, morphology, or diversity thresholds.

