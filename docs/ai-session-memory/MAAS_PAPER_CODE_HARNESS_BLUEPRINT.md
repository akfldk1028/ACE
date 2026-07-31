# MAAS Paper-Code-Harness Blueprint

Date: 2026-07-07

Purpose: stop treating mass diversity as a visual role-count problem. The MAAS loop must show a traceable chain:

`paper method -> clean-room code pattern -> ARR MassDSL/source geometry -> legal envelope repair -> JSON/PNG verifier evidence`.

Current canonical handoff: `docs/ai-session-memory/MAAS_MEMORY_INDEX.md`.

## Reference Methods

| Reference | Local code reviewed | Method to reuse | ARR implementation target | Harness evidence |
| --- | --- | --- | --- | --- |
| AIDL 2025 | `clone/aidl/AIDL/structure.py`, `clone/aidl/AIDL/solver.py` | High-level DSL objects are separate from the constraint solver. Hierarchical semantic parts are first-class. | `VerbSequence` and `SourceMass` expose primary/secondary architectural language, source volumes, rule evidence, and solver provenance. | `source_signature.primary_language`, `secondary_language`, `composition_rule`, `sourceGeometryUsed`, `legalPass`. |
| CAD-Assistant | `clone/CAD-Assistant/cad_assistant/core.py`, `clone/CAD-Assistant/cad_assistant/openai_planner.py` | Plan/action/execute/observe/revise loop, with image/observation feedback. | MAAS LLM loop proposes language; compiler executes; legal/PNG/JSON verifier observes; next loop revises failures. | `llm_proposal_loop`, prompt hash, compiled variants, final PNG and JSON verifier. |
| Design for Descent / d4descent | `clone/d4descent/scripts/optimize_shc.py`, `clone/d4descent/scripts/optimize_prompts.py` | Grammar/objective/optimizer separation and artifact logging. | Mass grammar is not the legal solver; legal pass is an objective/gate; artifacts are saved as latest JSON/PNG. | `verify-maas-20-alt-json.cjs`, `verify-maas-png.py`, parking verifier. |
| EvoMass 2024 | `clone/evo-mass/EvoMass/` if cloned later; paper method currently used from notes | Population diversity, island coverage, performance selection. | Keep additive/subtractive/hybrid/sectional islands, but add pairwise language composition. | island coverage, mass-language diversity, language-pair diversity. |

## Current Architectural Contract

Legal rules are hard constraints and must not be delegated to the LLM:

- FAR, BCR, height, parking, and geometry clipping stay in the legal optimizer and parking verifier.
- LLM chooses architectural language and authored parameters.
- Compiler uses rule priors only as explicit, counted priors.
- Hidden compiler defaults are not acceptable as "agent judgment".

Mass language must be represented as:

- `primary_language`: main massing logic, e.g. courtyard, split bridge, overlap slabs.
- `secondary_language`: modifying language, e.g. terrace ribbon, diagonal connector, roof cap, court liner.
- `composition_rule`: readable pair such as `split_bridge+terrace_ribbon`.
- `composition_layer_roles`: source-volume roles that physically express the secondary language.
- `repair_delta`: legal/parking repair trace, owned by legal optimizer.

## New Harness Gates

The JSON verifier must fail when final 20 candidates only look diverse by labels:

- primary/secondary language evidence must exist for most final candidates.
- composition-layer evidence must exist for enough candidates to prove actual geometry composition.
- language-pair diversity must be broader than isolated family diversity.
- irregular helper fragments must be capped.
- legacy fallback, two-tier stacks, legal failure, parking failure, high default/rule-prior dependence remain failures.

## Implementation Notes

Current clean-room adaptation already performed:

- `SourceMass.signature()` now exports primary/secondary language, secondary family, composition rule, and composition layer roles.
- `legal_mesh_optimizer._visual_diversity_evidence()` mirrors this information for final JSON review.
- `verify-maas-20-alt-json.cjs` adds gates for primary/secondary evidence, composition-layer evidence, language-pair diversity, and irregular-fragment caps.
- `compiler._family_from_mass_language()` now accepts common architectural aliases so LLM language names do not collapse to generic.
- `compiler._compose_secondary_language()` preserves secondary-language evidence for richer source geometry instead of dropping it too early.
- `source_geometry/compiler.py` now emits polygonal, curvilinear, and freeform source primitive roles for selected families.
- `legal_mesh_optimizer.py` now attaches `repair_delta` and source-volume repair retention evidence.
- Presentation artifact: `docs/maas-logic-diagram-20260707.pptx`.
- Critic artifact: `docs/playwright/design-route-live-verify/maas-critic-revision-latest.json`.

Latest verified metrics:

- JSON verifier: pass.
- PNG verifier: pass.
- parking verifier: pass.
- `legalPass`: 20/20.
- `sourceGeometryUsed`: 20/20.
- `parkingCountSatisfied`: 20/20.
- `parkingMassStagePass`: 20/20.
- `primarySecondaryEvidence`: 19.
- `compositionalLayerEvidence`: 16.
- `languagePairDiversity`: 19.
- `compositionLayerRoleDiversity`: 16.
- `sourcePrimitiveEvidence`: 6.
- `sourcePrimitiveRoleDiversity`: 10.
- `repairDeltaEvidence`: 20.
- `severeRepairDelta`: 0.
- `severeSourceVolumeRepair`: 0.
- `irregularFragmentMasses`: 3.

Current visual limitation:

- The latest PNG is substantially better than the repeated stepback state.
- The output is still mostly rectilinear bar/box source decomposition.
- Non-rectilinear primitive evidence exists, but it is concentrated in diagonal, branch, bend, and overlap families.
- Next primitive work should expand polygonal, curvilinear, or freeform mass sources to more families only if the legal/parking hard gates remain intact.

Remaining research-grade work:

- Move more compiler ratios from code into `rule_priors.py` with citations/rationale.
- Add a real critic revision loop that reads verifier failures and asks for corrected language pairs.
- Extend primitives beyond rectilinear source decompositions to polygonal/curvilinear shells when legal envelope and parking allow it.
