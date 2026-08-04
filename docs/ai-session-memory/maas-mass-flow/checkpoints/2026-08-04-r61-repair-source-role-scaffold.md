# r61 repaired source-role scaffold checkpoint

## r61 result

- Initial final VLM: 4 scored, 0 hard pass.
- Repair: 4 mutated, 3 materialized.
- Authority issuance: 0 success, 3 failure.
- Selection: 0/5.

Issuance correctly rejected incomplete repaired authority before downstream.
Failures were missing required program relations and empty carrier projections,
including active/public ground roles and program-specific entry/service roles.

## Root cause

Repair built the complete canonical source-role scaffold on `base_source`, but
authority issuance recomputed semantic relations from the post-materialization
dominant-only source. This discarded required support relations before carrier
issuance.

## Fix

- Bind every program-required source relation through canonical identity
  Matrix4 nodes reachable from the repaired AST root.
- Preserve repaired geometry hash while binding semantic identity.
- Pass canonical `base_source` through authority issuance.
- Missing, duplicate, stale, ambiguous, or unreachable roles remain hard
  failures.
- Carrier projection must be nonempty for every required relation.

## Verification

Focused repair scaffold-to-authority issuance test passed. No r62 full run has
been executed yet.
