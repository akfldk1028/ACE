# r62 neighborhood repaired source-role binding checkpoint

## r62 result

- Initial final VLM: 4 scored, 0 hard pass.
- Repair mutation/geometry change: 4/4.
- Source-role binding: 0/4.
- Materialization, issuance, second downstream, repaired final VLM: 0.
- Selection: 0/5.

All repairs failed with generic `source_role_scaffold_binding_failed` before
the fix.

## Root cause

Neighborhood relation binding selected `primary_program_mass` from the largest
post-BOOK component. After carve/offset operations the canonical primary bar
was not always the largest component, so required source relations disappeared.

## Fix

- Neighborhood required relations derive from canonical semantic roles rather
  than post-operation volume ranking.
- Exact required/missing/available relation evidence is preserved in typed
  repair failures.
- Canonical source-role binding retains all required relations without changing
  repaired geometry hashes.

## Verification

The focused r62 neighborhood regression covers all four observed repaired
sequence families and passes. No r63 full run has been executed yet.
