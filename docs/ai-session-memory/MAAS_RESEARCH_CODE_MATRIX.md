# MAAS Research-Code Matrix

Updated: 2026-07-01

Purpose: keep the MAAS loop honest. A paper is not "implemented" until its
methodological requirement is mapped to code, evidence, and a failing/passing
verification artifact.

## Current Status

- Latest output:
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- Current verification pass:
  - 20 candidates generated.
  - 20/20 legal pass.
  - 20/20 source geometry used.
  - 20/20 parking required-count satisfied.
  - legacy fallback 0.
  - JSON verifier pass.
  - PNG freshness/color verifier pass.
  - agent-authored evidence 19.
  - legal-envelope solver anchor 1.
  - `llmAuthoringGap` 0.
  - unique shape count 20.
  - unique family count 15.
  - unique section profile count 15.
- Remaining methodological gap:
  - no true live LLM/tool feedback loop.
  - no population optimization + clustering/medoid loop.
  - current pass uses a static clone/MAAS agent proposal artifact plus deterministic legal validation.

## Paper/Method Requirements vs Code

| Source | Requirement | Current Code | Gap | Verification |
| --- | --- | --- | --- | --- |
| AIDL 2025, "A Solver-Aided Hierarchical Language for LLM-Driven CAD Design" | LLM emits hierarchical DSL; solver handles spatial constraints. | `clone/MAAS/outputs/arr_agent_proposals/maas_arr_massdsl_proposals.v1.json`; `ARR/backend/design/maas/grammar/agent_proposals.py`; `source_geometry/compiler.py`; legal repair in `legal_mesh_optimizer.py`. | Current proposal is static artifact, not live LLM planning. MassDSL is still mostly flat sequence, not hierarchical component graph. | JSON must show `parameter_source=clone_maas_agent_arch_language` or true `llm_arch_language_proposal`; legal metrics pass after clip/reject. |
| CAD-Assistant 2025 | Tool-augmented VLLM executes CAD actions, observes geometry state, revises. | Agent review contracts exist in `ARR/backend/design/maas/agents/*`; preferred-operator API can test individual proposals. | No automatic proposal-execute-visual-critic-revise loop. | A loop artifact should show attempt N, rendered PNG, critic finding, revised MassDSL, legal result. |
| CAD-HLLM / hierarchical executable CAD generation | Decompose CAD generation into structured command planning. | `VerbSequence` and MassDSL calls exist. | No planner hierarchy: site strategy -> typology -> component volumes -> parameters. | Proposal schema should include hierarchy levels, not only `calls[]`. |
| EvoMass / FOAR 2024 | Typology-oriented massing exploration with performance-based optimization. | Legal envelope scoring, design quality scoring, diversity scoring. | No real population search; many values still fixture/heuristic. | Need population log with generated candidates, objective scores, legal rejects, selected cluster representatives. |
| CAADRIA 2025 performance-based urban massing optimization | Massing variation + layout variation + optimization, not fixed presets. | Parking/layout and legal massing are both evaluated. | They are not jointly optimized; parking is mostly post-filter/repair. | Need objective vector including legal, parking, environment/performance, and diversity cluster medoids. |
| CAADRIA 2026 generative pre-design framework | Early-stage framing and exploration, not only output generation. | `goal.md`, agent evidence, and A2UI review surface document the design process. | No explicit problem-framing state updated by agent feedback. | Need session artifact: design goals, constraints, rejected hypotheses, revised exploration direction. |

## 2026-07-01 Section Diversity Fix

- Fix location: `ARR/backend/design/maas/legal_mesh_optimizer.py`.
- Problem: section profile extraction returned early on generic `split`, `cave`, or `puncture`, so later architectural verbs were hidden.
- Change:
  - `diagonal_connect`, `terrace_link`, and `sloped_roof_mass` now have precedence over generic split/cut verbs.
  - agent-authored `offset`, `reflect`, and `array` verbs now produce explicit section kinds:
    `offset_twin_bar`, `reflected_court_pair`, `array_cluster`.
- Verification:
  - `node docs/playwright/design-route-live-verify/verify-maas-20-alt-json.cjs docs/playwright/design-route-live-verify/maas-20-alt-latest.json`: pass.
  - `python3 docs/playwright/design-route-live-verify/verify-maas-png.py docs/playwright/design-route-live-verify/maas-20-alt-latest.png`: pass.
  - `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export.MaasLegalVariantsTest.test_grammar_sequences_generate_composite_variants design.test_maas_export.MaasLegalVariantsTest.test_source_signature_contributes_to_candidate_distance design.test_maas_export.MaasLegalVariantsTest.test_massdsl_agent_contract_compiles_from_candidate_evidence -v 1`: pass.

## 2026-07-01 LLM Loop Implementation

- Implemented an OpenAI Responses API + Structured Outputs MassDSL proposal loop.
- New schema: `arr.maas.llm_massdsl_batch.v1`.
- Required artifact fields:
  - prompt hash
  - model/provider/API metadata
  - language palette count
  - combination rule count
  - raw candidate count
  - compiled sequence/variant counts
- Runtime contract:
  - LLM proposes architecture language and MassDSL candidates.
  - ARR source compiler materializes geometry.
  - ARR legal solver validates, clips, or rejects.
  - Deterministic presets remain fallback/test fixtures, not proof of LLM architectural judgment.
- Verification hardening:
  - `verify-maas-20-alt-json.cjs` now requires LLM-authored final evidence, loop schema, prompt hash, 120 raw candidates, and at least 80 compiled LLM variants.
  - Weak LLM candidates with FAR < 20% or BCR < 8% are limited in the final review set.
- Local tests:
  - LLM structured batch contract compiles 120 structured candidates.
  - LLM sequence compiles to ARR source geometry with `parameter_source=llm_arch_language_proposal`.
  - Existing MassDSL agent contract still identifies deterministic sequence authoring gaps.
- Live render status:
  - Strict JSON schema errors were fixed.
  - Actual OpenAI call reached the API but failed with `insufficient_quota` / HTTP 429.
  - Therefore the new LLM verifier is intentionally not passing yet; the blocker is OpenAI account quota/billing, not static code fallback.

## Next Implementation Loop

1. Final selection must prefer legal agent-authored candidates from the full
   legal candidate pool, not only those that survived earlier deterministic
   selectors.
2. Legal envelope anchors must be marked as `legal_envelope_solver`, not as
   missing LLM authoring.
3. Deterministic grammar candidates may remain as fallback/test fixtures only;
   default 20-card evidence should be mostly agent/optimizer provenance.
4. Add a real loop artifact:
   `proposal -> compile -> legal repair -> render evidence -> critic -> revise`.

## 2026-07-07 Literature-First Reset

Latest user correction:

- The newest PNG improved legal/diversity counters but some masses read as
  irregular fragments.
- "Mixed architectural language" should not mean adding arbitrary helper pieces.
  It should mean a legible composition such as:
  `primary_language + secondary_language + legal repair trace`.
- Verifier-driven volume-count increases are not enough. They can accidentally
  create chaotic massing that is worse architecturally.

Research interpretation:

| Method family | What to extract | What not to do | Code/verifier consequence |
| --- | --- | --- | --- |
| Shape grammar / procedural grammar | Rule hierarchy, primary mass + modifying rule, readable derivation trace. | Add random fragments only to increase role count. | `VerbSequence` / source compiler must expose `primary_language`, `secondary_language`, and grammar action trace. |
| Graph grammar / example-based procedural modeling | Reusable composition patterns and adjacency/topology relations. | Treat each family as an isolated label. | Add topology roles and composition layer evidence; later build pattern library from good examples. |
| AIDL / CAD-HLLM / solver-aided CAD | LLM proposes high-level DSL; solver checks constraints. | Let LLM decide legal compliance or hide compiler defaults as "AI judgment." | LLM schema must require explicit language hierarchy and authored params; legal solver remains hard gate. |
| EvoMass / SSIEA | Population/island diversity plus performance selection. | Manually insert fixed numeric presets and call it evolution. | Keep island quotas, but add clustering/medoid and critic-revision artifact. |
| Constraint-aware optimization/diffusion | Projection/repair into feasible set with trace. | Generate illegal mass then visually decorate it as legal. | Repair trace and legal clipping remain required; reject severe repair candidates. |

Immediate next review task:

1. Re-read local literature notes in `ARR/backend/design/research/06_LITERATURE/`
   and `docs/260506/research/`.
2. For each cited paper, record:
   - actual methodological claim,
   - whether ARR currently implements it,
   - which module owns the implementation,
   - what verifier/PNG evidence would prove it.
3. Only after that, continue code changes around compositional mass language.

New implementation target after review:

- Replace single `mass_language` as the only design descriptor with:
  - `primary_language`
  - `secondary_language`
  - `composition_rule`
  - `composition_layer_roles`
  - `repair_delta`
- Add verifier gates for:
  - compositional secondary-language evidence,
  - irregular-fragment cap,
  - repeated height/role/footprint pattern cap,
  - legal/parking pass preservation.

## 2026-07-07 Paper-Code-Harness Implementation

Added memory blueprint:

- `docs/ai-session-memory/MAAS_PAPER_CODE_HARNESS_BLUEPRINT.md`

Clean-room code mapping now implemented:

| Claim | Code owner | Verifier owner |
| --- | --- | --- |
| AIDL-like high-level language is separate from legal solver. | `ARR/backend/design/maas/source_geometry/ir.py`, `compiler.py` | `verify-maas-20-alt-json.cjs`: legal pass plus source geometry evidence. |
| CAD-Assistant-like observe/revise loop has structured evidence. | `llm_proposals.py`, render JSON artifact | prompt hash, LLM loop counts, final PNG/JSON. |
| d4descent-like grammar/objective separation is enforced. | MassDSL/source geometry compiler versus legal optimizer | `sourceGeometryUsed`, `legacyFallback=0`, legal/parking verifiers. |
| EvoMass-like diversity is not only family count. | `primary_language`, `secondary_language`, `composition_rule`, `composition_layer_roles` | new primary/secondary, composition layer, and language pair gates. |

Important correction:

- Volume-role diversity alone is not architectural diversity.
- Random fragments are now capped by verifier role-pattern checks.
- Secondary language must leave a physical source-volume role, not just a note.

## 2026-07-07 Current Status Correction

Canonical current handoff:

- `docs/ai-session-memory/MAAS_MEMORY_INDEX.md`

The previous "static artifact" gap is no longer the current live state for the
latest 20-card harness. The latest run used the LLM proposal loop and passed the
composition verifier gates. Older notes remain historical context.

| Method claim | Current status | Evidence | Still missing |
| --- | --- | --- | --- |
| LLM language -> MassDSL/source geometry -> legal solver separation | implemented | `primary_language`, `secondary_language`, `composition_rule`, source geometry, legal pass | deeper hierarchical component graph |
| Composition is more than family count | implemented | `primarySecondaryEvidence=19`, `compositionalLayerEvidence=18`, `languagePairDiversity=17` | richer non-rectilinear primitives |
| Legal/parking are hard gates | implemented | `legalPass=20/20`, `parkingCountSatisfied=20/20`, `parkingMassStagePass=20/20` | permit-final parking still requires review statuses |
| EvoMass-style population diversity | partial | island coverage and language-pair diversity gates | clustering/medoid selection and objective-vector artifact |
| CAD-Assistant-style critic revision | partial | prompt hash, loop artifact, PNG/JSON verifier | automatic critic -> revised prompt/sequence loop |
| Constraint-aware projection evidence | partial | legal repair/clipping and source geometry evidence | explicit `repair_delta` and severe-repair penalty |

Next code must not add more families only to raise counters. It should add
primitive expressivity and traceability: polygonal/curvilinear/freeform source
primitives, `repair_delta`, and critic-revision artifacts.

## Source Links

- AIDL 2025: https://arxiv.org/abs/2502.09819
- CAD-Assistant ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/papers/Mallis_CAD-Assistant_Tool-Augmented_VLLMs_as_Generic_CAD_Task_Solvers_ICCV_2025_paper.pdf
- CAADRIA 2025 massing optimization: https://papers.cumincad.org/data/works/att/caadria2025_359.pdf
- CAADRIA 2026 pre-design framework: https://papers.cumincad.org/data/works/att/caadria2026_18.pdf
- EvoMass FOAR 2024: https://journal.hep.com.cn/foar/EN/10.1016/j.foar.2024.06.001

## 2026-07-02 Implementation Update

- Reference repos cloned for audit, not direct legal geometry truth:
  - `clone/aidl` from https://github.com/deGravity/aidl
  - `clone/CAD-Assistant` from https://github.com/dimitrismallis/CAD-Assistant
- ARR code change:
  - `source_signature.parameter_provenance` records whether MassDSL values came
    from LLM/agent/deterministic sequence or ARR compiler defaults.
  - `source_signature.parameter_default_count` is used to penalize/reject LLM
    candidates that depend too much on hidden compiler ratios.
  - LLM structured schema now requires `typology`, so generated candidates must
    state an architectural family instead of only a call sequence.
  - Final 20 selection now applies typology quotas and caps
    `stepback_tower`/`terrace_link`/`taper`/`grade` dominant candidates at 3.
  - `visual_diversity_evidence.stepback_dominant` is exposed for PNG/JSON
    audits.
- Interpretation:
  - This still is not full AIDL/CAD-Assistant/EvoMass.
  - It is a concrete step toward those papers: high-level architectural intent
    and parameters are explicit, legal validation remains deterministic, and
    selection is measured by visual/topological family instead of score alone.
