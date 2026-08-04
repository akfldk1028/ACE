# r57 typed repair and causal feedback checkpoint

## Fixed failure loss

- Source replacement now records a typed reason for every `None` branch.
- Final repair materialization and program failures become failed
  `StageOutcome` records while legacy counters remain available.
- Initial and prior-cycle repair failures, failed stage outcomes, and final VLM
  critic/edit context are bounded, deduplicated, stripped of coordinates, and
  merged into the next cycle's existing authored-authority LLM feedback.
- Feedback is refreshed before every replenishment cycle instead of once per
  run.

## r57 evidence

- Initial final VLM: 4 input, 4 scored, 0 provider failures.
- Repair mutation: 4/4.
- Source materialized: 4/4, improved from r56 3/4.
- Clean/reprojected: 3/4, improved from r56 2/4.
- Program hard pass: 0/3.
- Every replenishment cycle consumed 12 authored/typed feedback records and
  executed an LLM author request.
- Cycle 4 produced one legal/program/downstream candidate and scored it with
  final VLM; cycle 5 produced another legal/program candidate.
- Final selection remains 0/5. Do not claim MASS completion.

## Newly exposed program failures

- One candidate failed program and program-form gates with body/public
  threshold rule budget failures.
- Two candidates had aggregate program score 0.808 and passed program-form,
  but failed a previously hidden program component.
- Program evidence now exposes volume, floor, coherence, and spatial hard-pass
  booleans plus component failure reasons without changing thresholds.

## Typed edit recovery

Cycle 4's `new_courtyard` edit targeted a semantic projection wrapper that was
unreachable from the repaired AST root. Compiler-safe mutation now resolves a
unique wrapper to the canonical reachable authored root, preserves resolution
evidence, and hard-fails missing or ambiguous mappings.

## Focused tests

- Typed source replacement reason: pass.
- Repair materialization StageOutcome: pass.
- Cycle N failure to cycle N+1 coordinate-free author feedback: pass.
- Hidden coherence/spatial component evidence: pass.
- Semantic projection target resolution and ambiguous rejection: pass.

## Next run criterion

The next full run must show whether reachable typed edits and explicit program
component feedback increase repaired/replenished program hard passes. If it
does not, inspect the first explicit component reason; do not lower law,
capacity, parking, or competition thresholds.
