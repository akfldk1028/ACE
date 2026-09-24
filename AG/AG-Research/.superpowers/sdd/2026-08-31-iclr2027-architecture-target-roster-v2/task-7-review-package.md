# Task 7 focused blocker review package

## Purpose

Independently review the Task 7 mutation matrix and establish root causes
before any production fix.

Read:

- `task-7-brief.md`
- `task-7-report.md`
- `tests/test_iclr2027_architecture_target_roster.py`
- the production/builder surfaces invoked by the accepted attacks

## Read-only constraints

Do not edit files, use git/network/credentials/subagents, inspect
held-out/test/OOD data, create candidate artifacts, or run a model/non-dry
experiment. Temporary synthetic fixtures are permitted.

## Required independent reproduction

Run the focused `TargetRosterMutationClosureTests` or smaller literal witnesses
and verify the exact census claim:

- attempted attacks: 4,140
- accepted attacks: 5
- canonical-set permutation invariants: 240
- exact-eight release census invariant: 1

Reproduce and trace these five reported accepted channels:

1. rebalanced cross-site target pairing;
2. public target `source_ids` containing `geometry`;
3. public target `source_ids` containing `repeat-01`;
4. public target `source_ids` containing `alias-01`;
5. swapping evidence-family source assignments without changing the public
   source union.

Also reproduce source-object omission escaping as raw `FileNotFoundError`
instead of stable `TargetRosterError`.

For each case, identify the first parser/validator/builder boundary that should
own rejection, trace why current logic accepts or leaks it, compare with a
nearby working validation pattern, and classify Critical/Important/Minor. Check
that every expectation is independent and no hash collision/harness ordering
artifact remains. Check the 240 pure top-level private-set permutations are
correct invariants while public/nested order mutations remain attacks.

Return a root-cause report with exact file/line references and recommended
minimal behavioral boundaries. Do not implement fixes.
