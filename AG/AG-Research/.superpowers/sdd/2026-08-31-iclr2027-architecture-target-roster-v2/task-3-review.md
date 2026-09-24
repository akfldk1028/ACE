# Task 3 review — initial

Spec Compliance: FAIL. Task Quality: Needs fixes.

## Important

1. File fsync plus `os.replace` does not satisfy the brief's crash-durable
   publication requirement; staging/output parent directory entries are not
   durably flushed.
2. Freshness is checked before validation but final `os.replace` is not an
   explicit atomic no-replace publication primitive, leaving a destination
   creation race.
3. Transaction tests omit pre-existing-output preservation, nested roots,
   extra/link/reparse entries, invalid independent review before staging,
   publication failure cleanup, and an all-entry/type release census.

## Minor

- Expected filesystem races/permission failures can escape as raw `OSError`
  instead of stable `TargetRosterError` blockers.

The schema, validation order, exact eight inputs/outputs, review binding,
receipt construction, no-call capability closure, and corrupt-source rollback
were otherwise strong.
