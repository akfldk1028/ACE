# MAAS GRL / Mass-Brain ON-OFF ablation

Updated: 2026-07-15

Read this before enabling GRL/Mass-Brain in routine MAAS generation or claiming
that relation memory improves the final 20-mass portfolio.

## Verdict

Current GRL/Mass-Brain does **not** improve the selected mass portfolio.
Keep routine generation OFF. Use it only as an explicit shadow-memory
experiment until a paired ablation proves a final-selection benefit.

This is not a claim that graph memory can never help. It is the measured result
of the current implementation, rollout and real-PNU benchmark.

## Fair benchmark contract

- PNU: `1168011800104170004`
- same site geometry and east-road context
- same program: neighborhood living
- same random seed and search/critic budgets
- same author cache and starting VLM score cache
- same baseline exact-compile path
- only `MAAS_MASS_BRAIN_ENABLED` differs

Runs:

- OFF: `maas-neighborhood-vlm-a2a-v104-fair-grl-off.json`
- ON: `maas-neighborhood-vlm-a2a-v105-fair-grl-on.json`
- machine-readable comparison:
  `maas-grl-ablation-v105-on-v104-off.json`

All artifacts are under
`docs/playwright/design-route-live-verify/`.

## Result

Both runs produced:

- selected: 19/20
- clean pool: 185
- capacity pool: 160
- visual-floor pool: 30
- language groups: folded 4, oblique 1, continuous 2, carved 4,
  cluster 2, stepped 3, bridge/interlock 3
- branched continuous field: missing
- automatic visual status: failed
- legal/parking projection: not run
- identical accepted-sequence names and order
- identical final review rows
- identical accepted-only PNG SHA-256:
  `730859f2986b815f008045d55e355bf10e68968c090e77e6c278f043fc84decb`

The ON run additionally performed 44-parent ingestion, generated 20
Mass-Brain proposals, exact-compiled 15 and VLM-evaluated 6. Rollout remained
`shadow/slots=0`; zero Mass-Brain candidates entered final selection. Approximate
wall time from process start to result write was 201 seconds OFF and 211 seconds
ON. Do not present those 20/15/6 shadow counts as a design-quality improvement.

## Coupling bug found and fixed

The first OFF probe, v103, returned only 15 masses. That was not a GRL benefit.
The feature flag accidentally disabled exact compilation of persisted accepted
and LLM-authored baseline seeds as well as Mass-Brain evidence compilation.
This removed normal baseline candidates and made the ablation invalid.

`program_massing/vlm_a2a.py` now keeps baseline persisted/authored exact
compilation unconditional. The stricter no-capacity-projection evidence pass is
isolated behind `mass_brain_enabled`. v104 is the corrected OFF run.

The relation-memory harness now defaults `MAAS_MASS_BRAIN_ENABLED` to `0`.
Enabling shadow evaluation requires an explicit environment value. The result
artifact also records Mass-Brain final-selection admission/effect for future
runs.

## Decision rule

Do not activate GRL/Mass-Brain selection slots based on connectivity, node
count, proposal count, compile count, or shadow VLM count. Require all of:

1. identical paired baseline/brain runs over multiple real parcels and programs;
2. non-zero brain candidates surviving geometry, capacity, legal and parking gates;
3. blinded VLM and architect preference improvement;
4. no loss of 20-card count, language coverage or morphology diversity;
5. measured improvement large enough to justify latency and model cost.

Until then, GRL may remain useful for provenance, audit, feedback storage and
offline research. It is not part of the routine generative quality path.

## Fundamental MASS work remains

This ablation does not solve the visual problem. The current board is still not
competition-grade, has no branched continuous field, and the supplied 69-page
BOOK corpus is not yet an active compiled language registry. The next work is
BOOK evidence -> typed operative graph -> real-PNU compile -> clean/capacity
gate -> VLM/architect evaluation, followed by legal/parking projection.
