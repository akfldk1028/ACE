# r78-r80 Replenishment Ledger and Context - 2026-08-05 KST

## Goal

Recover lawful, competition-grade, genuinely diverse MASS target-five supply without relaxing statutory law, parking, capacity, program, VLM, or diversity thresholds.

## Run progression

- **r78:** `1/5` selected in `444.9s`. Replenishment repeatedly attempted the same causal work instead of skipping completed attempts.
- **`ce5d748`**: carried reviewed-parent state across replenishment cycles.
- **`8a85cc6` + `0f0a7ee`**: introduced and completed the replenishment-attempt ledger and its persisted evidence.
- **r79:** crashed during cycle 3 with `FinalMeshFloorEvidenceError`; no final PNG was produced.
- **`d2b603e`**: isolated per-candidate/per-cycle context so one failed floor-evidence path could not contaminate later work.
- **`c8c7643`**: stabilized causal identity used by replenishment records and ledger matching.
- **r80:** `1/5` selected in `180.05s`; completed without the r79 crash.

## r80 evidence

- PNG: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r80\maas-book-neighborhood-5.png`
- Ledger: `28` attempts, `12` unique identities, `16` repeated attempts, `0` skips.
- Cause: duplicate causal records remained distinct in the ledger input, so membership checks did not suppress repeated work.
- Retained final hard-pass supply: `1`.
- New final-VLM candidates: `0`.
- Replenishment author: `0/20`.
- Selected result: measured `stepped`, operation `shift`.

## Pending work and blockers

- A set-dedupe patch for causal ledger inputs is under review with commit pending. It is not live-verified and must not be reported as fixing r80.
- Verify nonzero ledger skips and reduced repeated attempts in the next live run.
- Preserve complete provider rejection diagnostics through replenishment, rather than collapsing them into generic no-author/no-candidate outcomes.
- Emit typed raw profiled-mesh failure codes, including failing node/operator and kernel, surface, or floor-evidence cause.
- Restore lawful authored and final-VLM supply to the existing target-five contract with no threshold relaxation.

## Exact next steps

1. Review and commit the set-dedupe patch without changing ledger identity authority.
2. Run one fresh live target-five and verify repeated causal inputs increment ledger skips before provider work.
3. Audit every provider rejection from request through persisted replenishment evidence and final routing.
4. Add typed profiled-mesh raw diagnostic codes at the materialization/floor-evidence boundary.
5. Continue only through the existing canonical program, statutory law, parking, exact final-VLM, and diversity gates; do not relax thresholds.

