# r9 PNU2 gymnasium selected-0 forensic audit

Date: 2026-07-29  
Mode: read-only systematic debugging; no benchmark replay and no code edits

## Verdict

PNU2's gymnasium result is not a diversity-selector collapse and is not a
parking or Neo4j-law rejection. Candidate supply is lost before any of those
stages.

The first persisted loss is:

`sequence_compiled -> directed_geometry_materialization`

Both the initial pass and bounded-parent replenishment evaluate 36 candidates.
All 72 sequences compile, and all 72 return `None` from
`_materialize_directed_geometry`. Consequently every later count is zero.

PNU2 also has a genuine program/site infeasibility:

- generation host: 429.700 m2
- reported host axes: 85.423 m x 6.215 m
- estimated clear-span capacity: 5.718 m
- compact-training-hall minimum clear span: 6.000 m
- dimensional status: `infeasible`
- reason: `legal_generation_site_cannot_fit_minimum_program_span`

The live law-derived floor sections are more restrictive than the dimensional
context indicates. Their measured minimum rotated rectangle is approximately
76.957 m x 3.204 m (aspect 24.02), versus 12.865 m x 8.009 m (aspect 1.61) for
the successful PNU1 gym.

There is also a control-flow/provenance bug. The infeasible dimensional
context is treated as advisory, then the fallback restores the 18 m / 3-floor
catalog values and derives a 9 m / 3-floor occupiable-floor plan. The run
therefore spends 72 materialization attempts and ends with generic portfolio
deficits instead of reporting authoritative program/site infeasibility.

Without lowering the 6 m program span requirement or a legal gate, the
pipeline cannot honestly produce three gymnasium masses on this PNU2 legal
field.

## Evidence sources

- PNU2:
  `docs/playwright/design-route-live-verify/r9-pnu2-target3-neo4j-20260729/20260728T231424666714Z-01-pnu-1168011800104670003`
- PNU1:
  `docs/playwright/design-route-live-verify/r9-pnu1-target3-neo4j-20260729/20260728T230824304909Z-01-pnu-1168011800104170004`
- Candidate materializer:
  `ARR/backend/design/maas/book_language/candidate_generation.py`
- Dimensional resolver:
  `ARR/backend/design/maas/book_language/candidate_analysis.py`
- Benchmark fallback:
  `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Legal-field selector:
  `ARR/backend/design/maas/geometry_language/legal_field_affine_placement.py`

## Stage ledger

### PNU2 gymnasium

| Stage | Initial | Replenishment | Combined consequence |
|---|---:|---:|---:|
| Universal recursive seed supply | 164 | 128 | 292 |
| Budgeted candidates evaluated | 36 | 36 | 72 |
| BOOK/source sequences compiled | 36 | 36 | 72 |
| Sequence compile failures | 0 | 0 | 0 |
| Directed geometry materialized | 0 | 0 | 0 |
| Directed materialization failures | 36 | 36 | 72 |
| Root compiled | 0 | 0 | 0 |
| Projection materialized | 0 | 0 | 0 |
| Clean mass | 0 | 0 | 0 |
| Program hard pass | 0 | 0 | 0 |
| Capacity + floor hard pass | 0 | 0 | 0 |
| Shared-floor evaluated/pass | 0/0 | no input | 0/0 |
| Preselection legal pass | 0 | 0 | 0 |
| Geometry-retention pass | 0 | 0 | 0 |
| Parking hard pass | 0 | 0 | 0 |
| Combined preselection pass | 0 | 0 | 0 |
| Morphology/MAP-Elites input | 0 | no input | 0 |
| MAP-Elites occupied cells | 0 | no input | 0 |
| Final hard-pass selection pool | 0 | 0 | 0 |
| Selected | 0 | 0 | 0 |

The summary's final failure labels such as
`selected_count_below_target_3`, base-scope shortages, capacity-band balance,
stepped/ground-strategy shortages, and smoke target failure are downstream
consequences. They are not causal rejection reasons.

The outcome graph independently records 72 gym observations at
`geometry_gate_stage=directed_geometry_materialization`, every one with
`directed_geometry_materialization_failed`. It records no PNU2 gym
`program_gate`, legal, parking, or selected observation.

### Successful PNU1 gymnasium

Initial pass:

- evaluated 36
- sequence compiled 36
- directed materialized / root compiled / clean: 17 / 17 / 17
- program hard pass: 15
- capacity-target and floor hard pass: 14
- shared-floor input/pass: 12 / 12
- preselection legal/retention/parking/combined: 12 / 12 / 12 / 12
- morphology/MAP-Elites input and retained: 12 / 12
- occupied MAP-Elites cells: 8

Replenishment:

- evaluated 36
- sequence compiled 36
- directed materialized / root compiled / clean: 22 / 22 / 21
- program hard pass: 14
- preselection legal/retention/parking/combined: 12 / 12 / 12 / 12

Final:

- combined hard-pass pool: 24
- selected: 3

PNU1's two initial program failures occur only after materialization:
one `gym_clear_span_below_program_minimum` and one compound architectural
body-rule repetition/budget failure. These are not seen in PNU2 because PNU2
never reaches the program gate.

## Same-program control

The two outcome graphs contain exactly the same set of 72 authored
`program_hash` values for gymnasium.

- PNU2: all 72 hashes fail directed materialization.
- PNU1: 39 of those same hashes materialize; 33 fail materialization.

This rules out missing universal-form-bank diversity or different authored
seed supply as the PNU2-wide cause. At least 39 known-materializable authored
programs are lost only when bound to PNU2's site/legal context.

The persisted schema does not record which internal `return None` branch in
`_materialize_directed_geometry` fired. Therefore the exact sub-branch cannot
be claimed from these artifacts. The bounded inference is that the loss is
inside the site-bound authored-compilation/legal-field lane, with the extreme
legal-section geometry and genuine clear-span infeasibility as the
site-specific discriminator. It is not valid to name parking, program form,
capacity selection, morphology, or diversity as the cause.

## PNU1 versus PNU2 geometry

| Measurement | PNU1 gym success | PNU2 gym failure |
|---|---:|---:|
| Generation-site area | 102.931 m2 | 429.700 m2 |
| Generation host short axis | 8.009 m | 6.215 m |
| Estimated clear span | 7.368 m | 5.718 m |
| Dimensional result | adapted compact hall | infeasible |
| Effective pre-authoring height/floors | 5.894 m / 2 | fallback 18 m / 3 |
| Legal floor-section area | 102.931 m2 | 185.850 m2 |
| Legal-section MRR | 12.865 x 8.009 m | 76.957 x 3.204 m |
| Legal-section aspect | 1.61 | 24.02 |
| Legal-section vertices | 5 | 158 |
| Target per floor | 56.612 m2 | 102.217 m2 |
| Target/section ratio | 0.55 | 0.55 |

The failure is geometric rather than an area-total shortage. PNU2 has more
area, but it is a very narrow legal ribbon. Aggregate area alone is therefore
not a valid gym feasibility proxy.

## Source-level control-flow finding

`_program_dimensional_context` correctly returns `infeasible` when no gym
subtype meets minimum span. In the benchmark:

1. the status is copied into a diagnostic-only advisory;
2. the disabled early-exit block (`if False`) never emits a program-infeasible
   result;
3. the fallback uses `effective_height_m or catalog_height` and
   `effective_floors or catalog_floors`;
4. the context is overwritten with the fallback height/floor values;
5. candidate generation proceeds into exact site-bound materialization.

This explains the contradictory PNU2 record: `status=infeasible` and
`selected_subtype=none`, but `effective_height_m=18` and
`effective_floors=3`.

## Minimal PNU-general correction

No acceptance gate should be lowered.

1. Make program dimensional feasibility consume the actual law-derived
   floor-section field, including the narrowest occupied section, rather than
   only the ground generation polygon.
2. Resolve subtype, height, floor count, and floor-capacity plan as one
   convergent pre-authoring contract. Do not overwrite an infeasible context
   with catalog defaults.
3. When no legal section field can meet any program subtype's dimensional
   minimum, stop that program lane with an explicit
   `program_site_infeasible` result. Do not describe zero supply as a
   morphology/diversity failure.
4. Add a structured materialization result/failure enum for at least:
   payload/edit, BOOK/program projection, semantic scaffold, authored
   compilation, affine screening, exact legal CSG, source bridge, and hash or
   semantic certificate. This changes observability, not gate strength.

If product requirements demand three results for every PNU regardless of
program fit, that is a different policy decision: choose a different feasible
program/subtype or clearly label speculative envelope studies. It cannot be
implemented honestly by widening affine search or weakening span,
containment, capacity, or parking gates.
