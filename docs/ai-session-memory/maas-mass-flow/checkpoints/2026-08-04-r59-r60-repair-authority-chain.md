# r59-r60 repaired authority-chain checkpoint

## r59

- Design-diagnostic repaired candidates reached second downstream evaluation.
- Run crashed with `missing_candidate_floor_context`.
- Fix: copy only the parent's certified candidate floor/capacity context through
  the canonical resolver. Shared-floor and geometry measurements remain newly
  evaluated from repaired geometry. Missing or tampered context hard-fails.

## r60

- Full run completed without crash.
- Initial funnel: 62 evaluated, 16 compiled, 12 clean, 8 program passed.
- Initial downstream: 5 canonical, 4 combined hard pass.
- Final VLM: 4 scored, 0 initial hard pass.
- Repair: 4 mutated, 4 materialized, 3 clean, 2 design-diagnostic releases.
- Second downstream: 2 input, 0 legal/retention pass.
- Final selection: 0/5.

Both released candidates failed because repaired geometry had not received a
complete authored legal projection certificate/bridge chain. Program and
geometry hashes existed, but chain-specific projection, surface/proxy,
semantic, PNU, legal-floor-field, and floor-plan bindings were absent.

## Fix

- Repaired geometry now uses the same canonical authored legal projection
  authority issuance path as normal candidates.
- All hashes are recomputed from repaired geometry.
- Stale parent geometry certificates are removed rather than copied.
- Identical immutable certificate content is published to source metadata,
  bridge, and feature.
- `authored_projected_surface_payload` is set only after issuance succeeds.
- Issuance failure remains a typed hard failure.

## Verification

- Certified floor context survives second downstream: pass.
- Missing/tampered floor context hard-fails: pass.
- Repaired authority passes second downstream identity validation: pass.
- Stale bridge and tampered certificate hard-fail: pass.

No r61 full run has been executed.
