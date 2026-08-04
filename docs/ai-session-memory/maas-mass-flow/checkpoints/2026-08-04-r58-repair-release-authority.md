# r58 repair release authority checkpoint

## Observed funnel

- Initial final VLM: 4 input, 4 scored, 0 hard pass.
- Typed repairs: 4 mutated, 4 materialized, 4 clean.
- Repaired program release: 0.
- Final selection: 0/5.

## Exact blocker

Three twist-family repaired candidates passed volume, floor, coherence, and
program-form authority with scores 0.808-0.816. They were removed only because
`spatial_hard_pass` was false. Spatial/coherence are non-statutory design
evidence and were incorrectly reused as pre-final-VLM materialization release
authority.

## Fix

- Repaired candidates retain volume, floor, program-form, structural, legal,
  containment, clean, capacity, and parking hard gates.
- Spatial/coherence-only failures are retained as diagnostic evidence and sent
  to final VLM for competition-quality judgment and typed revision.
- Volume, floor, and program-form rule-budget failures remain hard rejected.
- No scoring threshold, law, capacity, parking, or initial candidate gate was
  loosened.

## Verification

- Spatial-only repaired candidate release: pass.
- Canonical floorwise projection remains authoritative: pass.
- Volume/floor/program-form failures remain rejected: pass.

No r59 full run has been executed yet.
