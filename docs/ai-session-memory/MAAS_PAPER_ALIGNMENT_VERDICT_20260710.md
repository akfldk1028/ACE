# MAAS Paper Alignment Verdict - 2026-07-10

This file records the current gap between ARR MAAS code and the papers the user
expects it to follow. It is intentionally strict: verifier pass is not the same
as paper-complete implementation.

## Current Verdict

Overall status: `paper_inspired_partial_implementation`.

The latest MAAS run is verified as a legal/VLM preference massing pipeline, but
it is not yet a literal implementation of EvoMass, DDADesign, Archi-Agents, or
MASS.

Latest verified run facts:

- JSON verifier: pass.
- PNG verifier: pass.
- Legal pass: 20/20.
- Parking mass-stage pass: 20/20.
- Parking permit-final pass: 0/20.
- LLM raw candidates: 120.
- LLM compiled variants: 90.
- VLM top-k attempted/scored: 40/40.
- Final VLM-scored candidates: 16/20.
- Final direct OpenAI LLM candidates: 18/20.

## Paper-by-Paper Audit

### EvoMass / typology-oriented optimization

Paper target:

- Typology-oriented design exploration.
- Optimization-based exploration, not just sorting.
- Performance-related building massing typologies.
- Case studies with daylighting, solar exposure, subjective design intent, and
  design survey/user insight.

ARR current implementation:

- Has typology families, quota/island-like balanced selection, diversity
  metrics, legal envelope hard gates, and early massing performance proxies.
- Has `performance_proxy_evidence` with daylight perimeter, solar access, view
  openness, and mass distribution balance proxies.
- Has final island/family/language diversity guards.

Mismatch:

- No true SSIEA/evolutionary population loop with mutation/crossover,
  generation-by-generation replacement, Pareto/frontier tracking, or designer
  exploration UI.
- Environmental performance is proxy-only, not Radiance/Honeybee/daylight/solar
  simulation.
- Current island logic is quota/replacement selection, not evolutionary
  optimization.

Verdict: `partial`, not paper-complete.

Next required implementation:

- Add `design.maas.evolution/` with:
  - island populations;
  - mutation/crossover over MassDSL sequences;
  - objective vector legal/FAR/BCR/orderliness/diversity/performance/VLM;
  - generation trace;
  - non-dominated or ranked survivor selection;
  - response artifact `evolution_trace`.

### DDADesign / daylight-driven diffusion design

Paper target:

- Generate many massing models.
- Select/refine a massing model.
- Use daylight-driven strategy and daylight maps.
- Use LoRA/diffusion/ControlNet for facade/design generation constrained by
  massing contours.

ARR current implementation:

- Generates legal massing candidates.
- Uses VLM preference scoring on candidate PNGs.
- Has aesthetic/facade modules separate from legal massing.
- Has early daylight/solar proxies.

Mismatch:

- No trained daylight map model.
- No LoRA.
- No Stable Diffusion/ControlNet massing-to-design generation in the MAAS legal
  loop.
- VLM scoring is ranking/evaluation, not diffusion generation.

Verdict: `weak_partial`, not DDADesign implementation.

Next required implementation:

- Keep DDADesign claim limited to "inspired by massing-to-image evaluation".
- If implementing seriously, add separate `design.maas.daylight_diffusion/`
  adapter and do not mix it into legal hard gates.

### Archi-Agents

Paper target:

- Specialized agents with vector knowledge/BIM context.
- Iterative Chatchain-style collaboration.
- Generate and refine BIM models by integrating spatial, cost, and performance
  metrics.

ARR current implementation:

- Has agent folders with `agent.py`, `agent.yaml`, `SOUL.md`, `RULES.md`,
  `memory/MEMORY.md`.
- Has law, parking, LLM architect, MassDSL, geometry, grammar critic,
  preference, review, orchestrator roles.
- Has `agent_revision_trace`.

Mismatch:

- Current `agent_revision_trace.revision_type` is
  `selection_revision_not_geometry_mutation`.
- Agents mostly annotate/review/select. They do not yet run a closed loop:
  critic -> MassDSL mutation -> geometry compile -> law/parking recheck ->
  re-rank.
- No IFC/Revit/BIM refinement pipeline.

Verdict: `partial`, not Archi-Agents complete.

Next required implementation:

- Add `design.maas.agents/orchestrator/revision_loop.py`:
  - grammar/review critic emits mutation request;
  - llm_architect/massdsl agent generates revised sequence;
  - geometry agent compiles source geometry;
  - law/parking agents recheck;
  - accepted revisions re-enter candidate pool;
  - artifact changes to `revision_type=critic_to_geometry_mutation`.

### MASS / multi-agent system search

Paper target:

- Optimize prompts and agent/workflow topologies.
- Search over multi-agent systems or sample from an agentic supernet.
- Use environment feedback to optimize system distribution/operators.

ARR current implementation:

- Has fixed agent roles and fixed orchestrator flow.
- Has VLM/user feedback that can influence LLM generation prompt.
- Has explicit agent folders.

Mismatch:

- No prompt/topology search.
- No agentic supernet.
- No controller sampling different agent graphs per task.
- No environment-feedback optimization of agent operators.

Verdict: `not_implemented` for MASS proper.

Next required implementation:

- Either stop claiming MASS paper alignment, or add a separate
  `design.maas.agent_search/` module:
  - graph/topology candidates;
  - prompt variants;
  - evaluator using verifier/VLM/legal metrics;
  - search trace and selected topology artifact.

## What Is Actually Solid Now

- Legal envelope remains hard-gated.
- Parking mass-stage remains hard-gated.
- VLM is now real for top-40 preference scoring.
- Final set preserves VLM/direct-LLM/diversity metrics.
- LLM batch cache makes iteration practical.
- Module boundaries are now clearer:
  - `preference.loop`: VLM/reference scoring;
  - `selection.preference_guards`: final curation;
  - `llm_proposals`: LLM population generation/cache;
  - `legal_mesh_optimizer`: endpoint orchestration/legal geometry.

## Immediate Next Build Target

Priority should be Archi-Agents + EvoMass, not more verifier patching:

1. Implement critic-to-geometry mutation loop.
2. Implement EvoMass-like island evolution trace.
3. Keep DDADesign/diffusion separate unless a real daylight/diffusion pipeline
   is added.
4. Do not call the system paper-complete until the response contains:
   - `evolution_trace`;
   - `agent_revision_trace.revision_type=critic_to_geometry_mutation`;
   - real performance simulation or explicitly named proxy status;
   - optional `agent_search_trace` only if MASS is actually implemented.

## 2026-07-10 Implementation Update

The first paper-critical loop has been added and verified.

Implemented:

- `design.maas.evolution.island_loop`
  - creates first-generation MassDSL island mutation/crossover children;
  - uses LLM/grammar MassDSL sequences as seeds;
  - emits `arr.maas.evolution_trace.v1`;
  - hands generated children back into the existing legal repair, parking, VLM,
    and selection pipeline.
- `agent_revision_trace`
  - now reports `revision_type=critic_to_geometry_mutation` when evolved
    geometry children are accepted into the legal candidate pool.
- `source_geometry.compiler`
  - recognizes critic-section evolution overrides;
  - normalizes family-specific formal principles so source evidence does not
    collapse into one repeated generic tower language.
- final selection
  - sees the legal candidate pool before final balancing;
  - restores island, family, and formal-principle diversity at the end without
    bypassing legal or parking gates.

Latest verified run:

- JSON verifier: pass.
- PNG verifier: pass.
- Legal pass: 20/20.
- Parking mass-stage pass: 20/20.
- Parking permit-final pass: 0/20.
- LLM compiled variants: 90.
- Evolved MassDSL variants accepted for legal pipeline: 45.
- `agent_revision_trace.revision_type`: `critic_to_geometry_mutation`.
- `evolution_trace.paper_alignment_status`:
  `evomass_inspired_first_generation_not_full_ssiea`.
- Final VLM-scored candidates: 16/20.
- Final direct OpenAI LLM candidates: 18/20.
- Unique families: 15.
- Formal principle diversity: 6.
- Island coverage:
  - additive: 4;
  - subtractive: 6;
  - hybrid: 5;
  - sectional: 4.
- Source primitive role diversity: 4.

Remaining strict gap:

- This is now more than selection-only revision, but it is still not full
  EvoMass/SSIEA. The next paper gap is multi-generation population evolution
  with objective-vector history, survivor selection, and Pareto/frontier trace.

## 2026-07-10 Re-Review Correction

The earlier "latest verified run: pass" should not be treated as stable after
the subsequent stricter final-selection/taxonomy edits.

Latest re-review outcome:

- Compile: pass.
- `design.test_maas_preference` + `design.test_maas_selection_policy`: 30/30
  pass.
- PNG verifier: pass.
- JSON verifier: fail, but only on final-set balance metrics.
- Current failing JSON metrics:
  - `uniqueFamilies=14` where verifier requires at least 15;
  - `sameHeightMaxCount=13` where verifier allows at most 12.
- Current passing key metrics:
  - legal pass 20/20;
  - parking mass-stage pass 20/20;
  - two-tier masses 0;
  - role-pattern max repeat 2;
  - mass-language max repeat 2;
  - formal-principle diversity 6;
  - additive/subtractive/hybrid/sectional island coverage 5/6/5/4;
  - `agent_revision_trace.revision_type=critic_to_geometry_mutation`;
  - evolved legal-pool children 45;
  - selected evolved children 2.

Important implementation correction made during re-review:

- `agent_revision_trace.revision_type` must not be based only on generated
  evolution children. It now also records evolved legal-pool and selected-final
  survival counts.
- `terrace_link` was incorrectly collapsed into `folded_section`; it is now
  represented as `terraced_ribbon_section` so terrace ribbon is not lost as a
  formal architectural language.

Next repair target:

- Do not add more isolated verifier patches.
- The final 20-card selector needs a single constraint-satisfaction pass that
  solves family count, height histogram, language repeat, formal diversity,
  role-pattern repeat, and island quota together.

## 2026-07-10 gpt-5.6-luna VLM Guard Repair

Follow-up result after the re-review failure above:

- Switched MAAS generation and preference VLM defaults to `gpt-5.6-luna`.
- Direct OpenAI Responses API smoke test for `gpt-5.6-luna`: HTTP 200.
- Added `MAAS_DISABLE_PARKING_NEO4J=1` so rendering can use reviewed local
  structured parking seed rules when Neo4j routing is unavailable.
- Fixed the post-selection VLM guard:
  - `final_vlm_preference_minimum` had been replacing balanced candidates after
    `final_balanced_selection`;
  - `recover_final_vlm_review_metrics` now uses projection scoring and a final
    height-bucket repair after VLM/direct-LLM guards.
- Added semantic family/language normalization for composite massing:
  `reflected_pair`, `tapered_tower`, `branch_fin`, `courtyard_atrium`,
  `notched_void`, and `branch_atrium`.

Latest artifacts:

- `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`.
- `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`.

Latest verification:

- JSON verifier: pass.
- PNG verifier: pass.
- `legalPass=20/20`.
- `parkingCountSatisfied=20/20`.
- `parkingMassStagePass=20/20`.
- `legacyFallback=0`.
- `uniqueFamilies=15`.
- `massLanguageDiversity=15`.
- `rolePatternMaxCount=2`.
- `sameHeightMaxCount=12`.
- Island coverage additive/subtractive/hybrid/sectional: `4/6/6/4`.
- `formalPrincipleDiversity=8`.
- `architectureGradePass=20/20`.
