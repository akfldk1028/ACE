# MAAS Generator Paper Alignment Audit

Updated: 2026-07-08

Purpose: record whether the current MAAS generator is following the referenced
paper methods before adding second-stage preference distillation. This is the
first target: the generator must be methodologically sound before VLM/human
preference reranking is meaningful.

## Reference Method Baseline

The current local method is a clean-room ARR implementation inspired by these
paper directions, not a literal clone of any paper code:

- EvoMass / typology-oriented computational design optimization:
  - building massing typologies are generated for early-stage
    performance-based design exploration,
  - typology-first fixed workflows are replaced by typology-oriented
    optimization and exploration,
  - performance/legal evaluation must remain outside visual preference.
- CAADRIA 2025 urban massing extension:
  - massing generation should include both block variation and layout/context
    variation,
  - additive and subtractive generation are explicitly useful because they
    produce different typological families,
  - grid/cubical-only generation narrows the solution space.
- CAADRIA 2024 formal variation:
  - orthogonal/cubical optimization geometry is acceptable as an early-stage
    abstraction,
  - but it must be followed by volume-based and boundary-based formal
    variation, otherwise results stay coarse and repetitive.

## Current Code Mapping

| Paper Requirement | Local Code | Status |
|---|---|---|
| Typology/massing family generation | `design.maas.llm_proposals`, `grammar`, `source_geometry` | Partial pass |
| Additive/subtractive family split | `GENERATOR_MODE_BY_FAMILY`, `REQUIRED_COVERAGE_FAMILIES` | Pass as evidence taxonomy |
| Explicit geometry compiler | `source_geometry/compiler.py` | Pass |
| Legal/performance hard validation | `legal_envelope.py`, `repair_design`, `failed_constraint_metrics` | Pass for FAR/BCR/height envelope |
| Optimization/search loop | `legal_mesh_optimizer.py` ranking and balanced selection | Partial pass |
| Formal variation after cubical forms | `MassingGenome`, `formal_principles`, source volumes | Partial pass |
| Performance simulation beyond law | daylight/solar/user-intent objective | Missing or too weak |
| Layout variation | block placement/layout exploration | Missing for current parcel-scale output |
| Preference/user survey loop | second distillation plan | Not first-stage; planned after generator audit |

## Verdict

The generator is directionally correct but not yet paper-complete.

What is correct:

- LLM proposes architectural language and MassDSL; it does not decide law.
- MassDSL is compiled to inspectable source geometry.
- The legal solver repairs/rejects candidates deterministically.
- Additive, subtractive, hybrid, and sectional families are represented.
- Final review selection caps repeated stair/stepback outputs.

What is still insufficient:

- The objective function is still mostly FAR/BCR/diversity/orderliness. EvoMass
  style exploration should expose more explicit performance objectives and
  tradeoffs.
- Formal variation exists, but it is not yet a separate first-class optimizer
  stage with before/after deltas for volume-based and boundary-based changes.
- The LLM loop creates a broad candidate pool, but the optimizer still repairs
  too much geometry after the fact. Strong research output needs source geometry
  that survives legal repair with low `repair_delta`.
- The current 20-card PNG sheet is an evidence sheet, not proof that the
  generator is architecturally mature.
- Mass-stage parking pass is not permit-final parking approval.

## Correct Direction From Here

1. Keep law and parking as hard gates.
2. Make the first generator target paper alignment, not visual preference:
   typology generation -> explicit source geometry -> formal variation ->
   performance/legal evaluation -> optimization history.
3. Add a generator audit verifier that checks:
   - additive/subtractive/hybrid/sectional coverage,
   - formal-principle coverage,
   - low legal repair delta,
   - non-stepback cap,
   - objective vector attached to every candidate,
   - generation lineage from LLM/grammar to geometry to legal selection.
4. Only after this passes, add second-stage preference distillation:
   VLM/human pairwise preference reranking inside the already legal and
   methodologically valid candidate pool.

## Code Tasks

- Add `paper_alignment_evidence` to each candidate with:
  - `typology_generator`,
  - `generator_mode`,
  - `formal_variation_stage`,
  - `objective_vector`,
  - `legal_repair_delta`,
  - `selection_reason`.
- Add a verifier for `paper_alignment_evidence`.
- Treat formal variation as a separate source-geometry transform stage, not
  only as metadata.
- Keep the second distillation module separate under `design/maas/preference/`
  so it cannot hide first-stage generator weaknesses.
