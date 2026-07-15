# MAAS Paper-Code Deep Audit

Date: 2026-07-09

Purpose: compare the current MAAS implementation against the actual paper
methods instead of treating internal diversity/legal verifier pass as research
completion.

Canonical audit command:

```bash
node docs/playwright/design-route-live-verify/audit-maas-paper-alignment.cjs \
  docs/playwright/design-route-live-verify/maas-20-alt-latest.json
```

Latest audit verdict:

```text
paper_inspired_not_paper_complete
```

## Current Verified Facts

- Latest internal JSON verifier: pass.
- Latest PNG verifier: pass.
- Candidate count: 20.
- Legal pass: 20/20.
- Parking mass-stage pass: 20/20.
- LLM proposal loop: compiled.
- Raw LLM candidate population: 128.
- Compiled variants: 120.
- Final family diversity: 15.
- Formal principle diversity: 7.
- Latest 20-card preference mode: `vlm_ready_geometry_proxy`, not
  `vlm_scored`.

## Repeated Review Passes

Second review pass, 2026-07-09:

- Existing internal verifier and PNG verifier still pass.
- Paper audit still returns `paper_inspired_not_paper_complete`.
- VLM code path is real:
  candidate crop image is sent first, and up to 3 matched reference images are
  appended to the OpenAI Responses request.
- Current latest generated JSON is not itself VLM-scored:
  `maas-20-alt-latest.json` has `vlm_ready_geometry_proxy` and
  `vlm_status=not_requested` for all 20 candidates.
- The VLM-scored artifact exists separately:
  `maas-20-alt-vlm-feedback-run-latest.json` has `reference_count=152`,
  `use_vlm=true`, `vlm_model=gpt-4.1-mini`, and 20/20 `vlm_status=scored`.
- Reference corpus exists but is uneven:
  152 total references, 144 ArchDaily API and 8 seeded iconic precedents;
  many API references are apartment/house/project pages, so a better massing
  quality filter is still needed.
- Agent folders and review flow exist:
  latest JSON contains 8 `agent_trace` / `agent_reviews` records.
- Agent gap:
  latest JSON does not contain a critic-to-generator revision trace, so
  Archi-Agents-style collaboration is partial, not complete.
- Population selection gap:
  `_kmedoid_representatives` exists and is used in the selector, but previous
  JSON did not record which final candidates survived as medoid
  representatives.

Code changes from second review pass:

- `docs/playwright/design-route-live-verify/audit-maas-paper-alignment.cjs`
  now reads `selection_debug.legal_pool_source_families`, `agent_trace`, and
  `agent_reviews`.
- `ARR/backend/design/maas/legal_mesh_optimizer.py` now appends
  `selection_trace` events when candidates are selected by the k-medoid
  representative stage.
- Future generated JSON should expose:
  `selection_debug.final_selection_trace_evidence` and
  `selection_debug.final_kmedoid_representatives`.

Next required verification after a new full generation:

1. Run internal JSON/PNG/parking verifiers.
2. Run `audit-maas-paper-alignment.cjs`.
3. Run the VLM harness again on the newly generated PNG/JSON.
4. Confirm the latest JSON or paired preference artifact is `vlm_scored`, not
   only `vlm_ready_geometry_proxy`.
5. Check whether medoid trace survives final replacement:
   `final_kmedoid_representatives > 0`.

## Paper-Driven Code Fix 1: EvoMass/SSIEA Objective Axis

Issue:

- EvoMass/SSIEA-style massing optimization is not just "many forms."
- The cited direction is performance-based exploration: daylighting, solar
  radiation, and other environmental/design objectives must appear as part of
  candidate evaluation.
- Before this fix, ARR's `paper_alignment_evidence.objective_vector` was mostly
  FAR/BCR/diversity/orderliness.

Implemented:

- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - Added `_early_massing_performance_proxy(feature)`.
  - It computes fast massing-level proxies from source volumes:
    - `daylight_perimeter_proxy`
    - `south_solar_access_proxy`
    - `view_openness_proxy`
    - `mass_distribution_balance`
    - `aggregate_performance_proxy`
  - `paper_alignment_evidence.objective_vector` now includes these proxy
    objectives for future generated candidates.
  - `_design_review_quality_key(feature)` now uses
    `aggregate_performance_proxy`, so the proxy affects selection/ranking and is
    not only audit decoration.

Important limitation:

- This is not Radiance, UDI, solar-radiation, glare, or energy simulation.
- It is an explicit early-stage performance proxy so the optimization artifact
  no longer pretends FAR/BCR/orderliness are enough for EvoMass alignment.

Verification:

- `python -m py_compile design/maas/legal_mesh_optimizer.py`: pass.
- Smoke call on an existing candidate returned measured proxy evidence.
- Selection key smoke showed `aggregate_performance_proxy=0.4336` in the review
  quality tuple.

Next step:

- Later replace or augment proxy values with real Radiance/Honeybee/solar
  simulation when the performance backend is available.

## Paper-Driven Code Fix 2: Archi-Agents Revision Evidence

Issue:

- The agent folders/contracts existed, and `agent_reviews` were emitted, but the
  JSON did not record how agent critique changed the final candidate set.
- That is too weak for Archi-Agents-style collaboration; it looks like a report,
  not a workflow.

Implemented:

- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - Added `_build_agent_revision_trace(...)`.
  - The response now emits `agent_revision_trace`.
  - Each selected candidate receives `agent_revision_evidence`.
  - The trace records applied agent rules from law, parking, grammar critic,
    preference distiller, and geometry agents.
  - It also records excluded order-failure counts, selected family/formal
    distributions, selected average performance proxy, and candidate-level
    revision decisions.
- `docs/playwright/design-route-live-verify/audit-maas-paper-alignment.cjs`
  - Now checks `agent_revision_trace`.
  - Now counts candidate-level `agent_revision_evidence`.

Important limitation:

- This is explicitly `selection_revision_not_geometry_mutation`.
- It proves agent critique affects final candidate selection. It does not yet
  prove a full critic-to-generator loop that regenerates new MassDSL geometry
  after critique.

Verification:

- `python -m py_compile design/maas/legal_mesh_optimizer.py`: pass.
- Smoke call on an existing JSON produced
  `arr.maas.agent_revision_trace.v1`, 8 agent reviews, 20 candidate revisions,
  and `selected_average_performance_proxy=0.4813`.

## Modularization Correction

Issue:

- `legal_mesh_optimizer.py` was accumulating paper/objective/agent evidence
  code directly inside an already oversized optimizer file.
- That made the paper implementation harder to audit and increased the risk of
  hidden coupling.

Implemented:

- Moved early performance objectives to:
  - `ARR/backend/design/maas/performance_objectives.py`
- Moved paper-alignment evidence and preference attachment to:
  - `ARR/backend/design/maas/paper_alignment.py`
- Moved agent revision trace assembly to:
  - `ARR/backend/design/maas/agent_revision.py`
- `legal_mesh_optimizer.py` now imports and calls these modules instead of
  owning their implementation.

Verification:

- `py_compile` passed for all four modules.
- Smoke call verified:
  - `aggregate_performance_proxy=0.4336`
  - paper objective vector includes daylight/solar/view/balance keys
  - `agent_revision_trace.v1` returns 20 candidate revisions.

Next modularization target:

- Extract final selection/ranking policy from `legal_mesh_optimizer.py` into a
  dedicated `selection_policy.py` or `selection/` package. The optimizer is still
  too large even after this correction.

## Selection Policy Modularization Pass 1

Implemented:

- Added `ARR/backend/design/maas/selection_policy.py`.
- Moved the final review-set refinement guards out of `legal_mesh_optimizer.py`:
  - minimum direct LLM-authored candidates,
  - dominant-height reduction,
  - repeated role-pattern reduction,
  - language/family diversity repair.
- `legal_mesh_optimizer.py` now calls `refine_final_review_set(...)` with a
  `FinalReviewRefinementCallbacks` contract instead of owning that policy block.

Verification:

- `py_compile` passed for `legal_mesh_optimizer.py` and `selection_policy.py`.
- Smoke call on existing latest JSON returned:
  - `count=20`
  - `families=15`
  - `languages=15`
  - first variant remained `maas_01`.
- `legal_mesh_optimizer.py` reduced from 7,971 lines to 7,730 lines.

Remaining modularization:

- `_final_design_balanced_selection` is still too large and should be split next.
- `_select_diverse_features` should move after the callback contract stabilizes.
- `selection_debug` can remain in optimizer until selection extraction is
  complete.

## Selection Policy Modularization Pass 2

Implemented:

- Moved review-set constraint helpers into `selection_policy.py`:
  - `final_mass_stage_parking_pass`
  - `layout_status`
  - `source_reviewable`
  - `unresolved_llm_authoring`
  - `visible_tier_count`
  - `review_set_geometry_ok`
  - `review_set_constraints_ok`
- `legal_mesh_optimizer.py` now keeps thin wrappers only where the large
  `_final_design_balanced_selection` function still needs local state.

Verification:

- `py_compile` passed for `legal_mesh_optimizer.py` and `selection_policy.py`.
- Smoke call on existing latest JSON returned:
  - `count=20`
  - `families=15`
  - `languages=15`
- `legal_mesh_optimizer.py` reduced again to 7,676 lines.

Next safe extraction:

- Split the island quota block from `_final_design_balanced_selection`.
- Do not move the whole function at once unless a fuller callback contract is
  introduced first.

## Selection Policy Review After Pass 2

Review result:

- The modularization direction is correct: selection-only helpers now live in
  `selection_policy.py`, and optimizer coupling is lower.
- The logic is not "complete" or theoretically perfect. It is still a heuristic
  review-sheet policy, not a formal optimizer.

Bug found and fixed:

- `refine_final_review_set([], ...)` raised `ValueError` because the height
  guard called `max()` on an empty `Counter`.
- Added an empty-selected guard.

Policy cleanup:

- Added `FinalReviewRefinementPolicy` so the main thresholds are named instead
  of anonymous values:
  - minimum direct LLM candidates,
  - max dominant height count,
  - max role-pattern repeat,
  - max language repeat,
  - minimum language/family diversity,
  - max parameter-default ratio.
- `review_set_constraints_ok` now receives `max_language_repeat` explicitly.

Verification:

- Empty input smoke returns `[]`.
- Existing latest JSON smoke still returns:
  - `count=20`
  - `families=15`
  - `languages=15`
- `py_compile` and paper audit passed.

Remaining limitation:

- Large parts of `_final_design_balanced_selection` still contain many policy
  thresholds and recovery stages. The next real improvement is not claiming
  perfection; it is extracting the island quota/recovery block with named policy
  objects and adding focused unit tests for pathological candidate pools.

## Selection Policy Modularization Pass 3

Implemented:

- Moved pure island/formal helper logic into `selection_policy.py`:
  - island quota counts,
  - duplicate role-pattern counts,
  - island candidate scoring key,
  - formal-principle counts,
  - vertical-strategy counts,
  - formal diversity candidate key.
- Added callback contracts:
  - `IslandQuotaCallbacks`
  - `FormalDiversityCallbacks`
- Removed duplicate replacement helper by using one `relaxed_review_replace`
  implementation for formal diversity and later recovery stages.

Verification:

- `py_compile` passed.
- Existing latest JSON smoke remains:
  - `count=20`
  - `families=15`
  - `languages=15`
- Paper audit passed.
- `legal_mesh_optimizer.py` reduced to 7,647 lines.

Remaining:

- The mutation loops for island quota/recovery still live in
  `_final_design_balanced_selection` because they mutate `result` and rely on
  `replace_result`/`rebuild_seen_state`.
- Next extraction should move those loops behind a small state object rather
  than passing many loose callbacks.

## Selection State Refactor Review

Committed baseline comparison:

- In `HEAD`, `_final_design_balanced_selection` owned local mutable state:
  `result`, `seen_ids`, `seen_shapes`, and direct append/replace bookkeeping.
- Current code moves that bookkeeping into `selection_policy.SelectionState`.
- `legal_mesh_optimizer.py` still reads aliases such as `result` and
  `seen_ids`, but append/replace/rebuild behavior is now centralized.

Implemented:

- Added `SelectionState` to `selection_policy.py`.
- Connected `_final_design_balanced_selection` to `SelectionState`.
- Replaced manual add/rebuild/replace bookkeeping with:
  - `selection_state.append_seen(...)`
  - `selection_state.rebuild()`
  - `selection_state.replace_if_valid(...)`

Review result:

- This is a real modularization step, not just moving comments or adding an
  unused abstraction.
- One leftover manual state update in `force_add_reviewable` was found and
  replaced with `selection_state.append_seen(...)`.

Verification:

- `py_compile` passed.
- Direct `_final_design_balanced_selection` smoke returned:
  - 20 candidates,
  - 15 families,
  - 15 research languages.
- Paper audit passed.

Remaining:

- `SelectionState` does not yet own all replacement methods; later loops still
  mutate `result[index]` directly followed by `rebuild_seen_state()`.
- Next pass should move `relaxed_review_replace` into `SelectionState` or a
  state-aware helper before extracting island/recovery mutation loops.

## Selection State Refactor Pass 2

Implemented:

- Added state-level replacement helpers:
  - `SelectionState.replace_relaxed(...)`
  - `SelectionState.replace_unchecked(...)`
- Replaced direct `result[index] = candidate` flows in:
  - formal/recovery relaxed replacement,
  - forced recovery replacement,
  - LLM coverage-repair promotion.
- Verified that all selection-result index assignment now lives in
  `selection_policy.SelectionState`; the remaining optimizer calls are wrapper
  calls or non-selection dict updates.

Verification:

- `py_compile` passed.
- Direct `_final_design_balanced_selection` smoke remains:
  - 20 candidates,
  - 15 families,
  - 15 research languages.
- Paper audit passed.

Architecture review:

- `legal_mesh_optimizer.py` is still too large at about 7.6k lines.
- Proper next package split should be role-based, not arbitrary:
  - `selection/` for review-set selection and state,
  - `orchestration/` for `generate_legal_mass_variants`,
  - `section_materialization/` for section profile source volumes,
  - `parking_repair/` for repair candidate generation,
  - `feature_factory/` for GeoJSON feature construction.
- Do not keep growing a flat `selection_policy.py` forever; once selection
  extraction stabilizes, move it to a `selection/` package.

## Paper-by-Paper Verdict

| Paper/method | Current status | Evidence | Gap |
| --- | --- | --- | --- |
| EvoMass FOAR 2024 | partial | population exists: 128 raw / 120 compiled; final family diversity 15; code now adds daylight/solar/view/balance proxies to future objective vectors and ranking | still proxy-only; no Radiance/Honeybee/solar simulation or user-survey objective |
| CAADRIA 2025 urban massing | partial | 20/20 mass-stage parking pass | massing and parking/layout are gated, not jointly optimized as a layout+massing workflow |
| AIDL / CAD-HLLM / solver-aided CAD | implemented_partial | LLM loop compiled; composition/formal evidence exists for all final 20 | MassDSL remains mostly flat call sequence, not a true hierarchical component graph |
| Archi-Agents | implemented_partial for future runs | agent folders/contracts exist; code now emits `agent_revision_trace` and candidate `agent_revision_evidence` | revision is selection-level, not geometry mutation/regeneration after critique |
| MASS multi-agent system search 2025 | not implemented | prompt hash exists | no prompt/topology search artifact; fixed orchestration |
| DDADesign / diffusion massing-to-design | weak | reference-backed VLM module exists | latest 20-card JSON is not re-scored VLM preference; no trained diffusion/ControlNet massing prior |
| Constraint-aware diffusion/projection | partial | repair delta/source-volume repair evidence is good for final 20 | deterministic repair exists, but no differentiable or sampling-time constraint projection |

## Important Correction

The current system is not "paper-complete."

It is a hybrid engineering pipeline:

1. LLM proposes MassDSL language and parameters.
2. ARR source geometry compiler materializes source volumes.
3. Deterministic legal/parking gates repair or reject.
4. Internal verifiers check legal, source geometry, diversity, repair, and PNG
   evidence.
5. VLM/reference preference can score or feed back into the next generation,
   but the latest 20-card JSON is currently proxy preference evidence unless a
   VLM harness is run again after generation.

## Next Research-Grade Work

Do not add more labels or families just to raise counters.

Priority fixes:

1. Upgrade `agent_revision_trace` from selection revision to geometry mutation:
   critic -> MassDSL revision -> compiler -> legal/parking projection -> rerank.
2. Replace EvoMass proxy objective axes with stronger simulation or calibrated
   environmental metrics:
   daylight/solar/view/user-preference.
3. Add medoid/cluster representative selection over geometry descriptors,
   not only quota replacement and repeat caps.
4. Add current-generation VLM scoring after every full PNG generation when
   claiming VLM-backed preference.
5. Keep legal/parking hard gates unchanged.

## Selection Package Split Pass 1

Implemented:

- Created a real `design.maas.selection` package instead of continuing to grow
  one flat policy file:
  - `selection/types.py` for callback contracts and feature type aliases,
  - `selection/state.py` for `SelectionState`,
  - `selection/constraints.py` for parking/layout/review-set gates,
  - `selection/quota.py` for quota and diversity scoring helpers,
  - `selection/refinement.py` for final 20-card refinement,
  - `selection/__init__.py` for public exports.
- Replaced the optimizer import with `from design.maas.selection import ...`.
- Kept `selection_policy.py` as a compatibility shim so older imports do not
  break while the optimizer is being split.

Verification:

- `py_compile` passed for the optimizer, compatibility shim, new selection
  package files, and the paper/performance/agent evidence modules.
- Direct `_final_design_balanced_selection` smoke on
  `maas-20-alt-latest.json` remains:
  - 20 candidates,
  - 15 source families,
  - 15 research mass languages.
- Paper-alignment audit still exits successfully.
- File-size check after split:
  - `legal_mesh_optimizer.py`: 7,609 lines,
  - `selection_policy.py`: 58-line compatibility shim,
  - `selection/` package files: small focused modules, currently 63-270 lines
    each.

Important limitation:

- The smoke output still reports parking statuses as
  `needs_drive_connectivity_review` and `needs_mechanical_parking_review`.
  Therefore this is mass-stage parking feasibility evidence, not a final
  permit-grade parking approval. Do not present it as final legal/parking
  completion.

Next loop:

- Move the remaining large `_final_design_balanced_selection` orchestration
  loops into the `selection/` package step by step.
- Add focused selection tests before changing the scoring semantics:
  duplicate-heavy pools, weak-LLM-heavy pools, height-crowded pools, empty
  pools, and parking-failing pools.

## Selection Regression Tests Pass 1

Implemented:

- Added `ARR/backend/design/test_maas_selection_policy.py`.
- Covered the first small but important regression set:
  - compatibility shim exports the same `SelectionState` as
    `design.maas.selection`,
  - empty `refine_final_review_set(...)` returns `[]`,
  - `SelectionState.replace_relaxed(...)` rejects duplicate shape replacement,
  - `SelectionState.replace_relaxed(...)` rejects parking `fail` replacement.

Verification:

- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 4/4 tests.
- `py_compile` passed again for the optimizer, selection package, compatibility
  shim, and the new test file.

Next loop:

- Add tests for language crowding, source-family crowding, and weak LLM reject
  limits before moving the larger island/formal/recovery loops out of
  `_final_design_balanced_selection`.

## Selection Regression Tests Pass 2

Implemented:

- Extended `ARR/backend/design/test_maas_selection_policy.py` from 4 tests to
  9 tests.
- Added direct coverage for:
  - language crowding rejection,
  - source-family crowding rejection,
  - weak LLM `reject_final_review` over-limit rejection,
  - final metric snapshot family/language/island counts,
  - final structural quota rejection when language repetition remains too high.

Modularization:

- Added `selection/final_metrics.py`.
- Added `FinalMetricCallbacks`.
- Moved final review-set metric calculations out of
  `_final_design_balanced_selection` into the selection package:
  - `final_metric_snapshot(...)`,
  - `unique_family_count_after(...)`,
  - `final_metrics_ok_after(...)`,
  - `final_hard_quotas_ok_after(...)`,
  - `final_structural_quotas_ok_after(...)`.
- The optimizer now keeps small wrapper functions around these package helpers
  because the surrounding selection loop still lives in the optimizer.

Verification:

- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 9/9 tests.
- `py_compile` passed.
- Direct `_final_design_balanced_selection` smoke remains:
  - 20 candidates,
  - 15 source families,
  - 15 research languages,
  - 20 unique shapes.
- Paper audit still exits successfully with verdict
  `paper_inspired_not_paper_complete`.
- `legal_mesh_optimizer.py` line count moved from 7,609 to 7,572.

Remaining:

- The optimizer still owns the actual island/formal/recovery orchestration
  loops. Next extraction should move one complete loop block, not just another
  scoring helper.

## Selection Island Refinement Extraction Pass 1

Implemented:

- Added `selection/island_refinement.py`.
- Moved the first complete island quota refinement loop out of
  `_final_design_balanced_selection`:
  - additive/subtractive/hybrid/sectional quota balancing,
  - duplicate role-pattern replacement,
  - candidate ranking through `IslandQuotaCallbacks`.
- Extended `IslandQuotaCallbacks` with `formal_principle` because the existing
  replacement key protected torqued-stack formal language.
- Removed the corresponding island helper aliases from the optimizer import.
- Added a direct test that verifies island refinement can replace an over-generic
  result item with a missing additive candidate.

Verification:

- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 10/10 tests.
- `py_compile` passed.
- Direct `_final_design_balanced_selection` smoke remains:
  - 20 candidates,
  - 15 source families,
  - 15 research languages,
  - 20 unique shapes.
- Paper audit still exits successfully with verdict
  `paper_inspired_not_paper_complete`.
- `legal_mesh_optimizer.py` line count moved from 7,572 to 7,487.

Paper/code alignment note:

- This pass makes the EvoMass/SSIEA-inspired typology-island balancing explicit
  and testable.
- It does **not** implement real EvoMass behavior yet: no evolutionary
  population operators, no k-medoid representative trace, and no environmental
  performance objective simulation. The audit gap remains valid.

Next loop:

- Move the formal-principle / vertical-strategy over-representation loop into
  `selection/formal_refinement.py`.
- After that, the next research-grade change should be a real selection trace
  artifact or k-medoid representative evidence, because the paper audit still
  reports `finalKmedoidRepresentatives: 0` and `finalSelectionTraceEvidence: 0`.

## Selection Formal Refinement Extraction Pass 1

Implemented:

- Added `selection/formal_refinement.py`.
- Moved the formal-principle / vertical-strategy over-representation loop out
  of `_final_design_balanced_selection`.
- Added `enforce_formal_diversity_replacements(...)`.
- Extended `FormalDiversityCallbacks` with `stair_like_risk` so the extracted
  replacement choice preserves the previous high-stair-risk preference order.
- Added a direct unit test proving an over-repeated formal principle can be
  replaced by a different formal language candidate.

Verification:

- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 11/11 tests.
- `py_compile` passed.
- Direct `_final_design_balanced_selection` smoke remains:
  - 20 candidates,
  - 15 source families,
  - 15 research languages,
  - 20 unique shapes.
- Paper audit still exits successfully with verdict
  `paper_inspired_not_paper_complete`.
- `legal_mesh_optimizer.py` line count moved from 7,487 to 7,427.

Paper/code alignment note:

- This pass makes architectural formal-language balancing explicit and
  testable. It supports the review-sheet goal of not showing the same massing
  language repeatedly.
- It still does not close the paper gaps around:
  - hierarchical MassDSL/component graph,
  - critic-to-generator geometry mutation,
  - k-medoid representative trace,
  - real performance objectives.

Next loop:

- Extract the repair/height/formal-target recovery block after the first formal
  refinement pass.
- Then add a `selection_trace` artifact so paper audit can stop reporting
  `finalSelectionTraceEvidence: 0`.

## Selection Initial Recovery Extraction Pass 1

Implemented:

- Added `selection/recovery_refinement.py`.
- Added `RecoveryRefinementCallbacks`.
- Extracted a larger recovery block from `_final_design_balanced_selection`:
  - severe repair-retention replacement,
  - dominant height replacement,
  - missing/over-repeated target formal principle replacement.
- Reused exported `height_bucket(...)` from the recovery module for later
  optimizer cleanup code.
- Added a unit test proving a severe repair-loss result item can be replaced by
  a higher-retention candidate.

Verification:

- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 12/12 tests.
- `py_compile` passed.
- Direct `_final_design_balanced_selection` smoke remains:
  - 20 candidates,
  - 15 source families,
  - 15 research languages,
  - 20 unique shapes.
- Paper audit still exits successfully with verdict
  `paper_inspired_not_paper_complete`.
- `legal_mesh_optimizer.py` line count moved from 7,427 to 7,306 in this pass.

Important process correction:

- Previous loop only reduced the optimizer by about 60 lines, which was too
  small for the actual problem. This pass intentionally extracted a larger
  behavior block. Continue extracting whole behavior stages rather than only
  helper functions.

Next loop:

- Extract the next cleanup/recovery stage around:
  - clean replacement pool,
  - signature proposal priority,
  - replaceable final indexes,
  - repeat cap candidate checks.
- Then add `selection_trace` / k-medoid representative evidence so the audit
  can begin closing the EvoMass paper gap instead of only clarifying code
  structure.

## Final Balanced Selection Extraction Pass 1

Process correction:

- The previous incremental extraction was still too conservative. The optimizer
  remained over 7k lines and the user correctly flagged that as unacceptable.
- This pass moved the whole `_final_design_balanced_selection` orchestration out
  of `legal_mesh_optimizer.py` instead of extracting another small helper.

Implemented:

- Added `selection/final_balanced.py`.
- Added `BalancedSelectionDeps`.
- Moved the full balanced-selection orchestration body into
  `final_design_balanced_selection(...)`.
- Replaced optimizer implementation with a thin dependency wrapper.
- Exported `BalancedSelectionDeps` and `final_design_balanced_selection` through
  `design.maas.selection`.

Verification:

- `py_compile` passed.
- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 12/12 tests.
- Direct `_final_design_balanced_selection` smoke remains:
  - 20 candidates,
  - 15 source families,
  - 15 research languages,
  - 20 unique shapes.
- Paper audit still exits successfully with verdict
  `paper_inspired_not_paper_complete`.

Size impact:

- `legal_mesh_optimizer.py` moved from 7,306 lines to 5,481 lines.
- New `selection/final_balanced.py` is 1,992 lines.

Important limitation:

- This is a real module-boundary correction, not a research-method correction.
- The huge selection logic is now in the selection package, but
  `selection/final_balanced.py` is itself too large. Next work should split that
  file by selection stages.
- Paper audit gaps remain:
  - no k-medoid representative trace,
  - no selection trace artifact,
  - no true EvoMass evolutionary optimization,
  - no critic-to-generator geometry mutation.

Next loop:

- Split `selection/final_balanced.py` into stage modules:
  - seed/authoring coverage,
  - quota/island/formal recovery,
  - cleanup/replacement pools,
  - final hard quota repair.
- Add `selection_trace` evidence while splitting so the paper audit can begin
  closing `finalSelectionTraceEvidence: 0`.

## Post-Extraction Review And Trace Pass

Reviewed:

- The large move was structurally correct: `legal_mesh_optimizer.py` is now a
  wrapper around `selection.final_design_balanced_selection(...)` for final
  review selection.
- The next oversized file is `selection/final_balanced.py`, currently about
  2k lines. That file must be split by stage; otherwise the complexity simply
  moved folders.
- The paper audit gap around selection evidence was valid for the cached JSON:
  `maas-20-alt-latest.json` has no `selection_trace` entries because it was
  generated before this trace pass.

Implemented:

- Added `attach_final_selection_trace(...)` in `selection/final_balanced.py`.
- Every selected final candidate now receives:
  - `schema_version: arr.maas.selection_trace.v1`,
  - `stage: final_balanced_selection`,
  - rank,
  - final limit,
  - source family,
  - research mass language,
  - quota group,
  - final family/language/group counts,
  - mass-stage parking pass evidence.

Verification:

- `py_compile` passed.
- `python manage.py test design.test_maas_selection_policy --verbosity 2`
  passed 12/12 tests.
- `verify-maas-png.py` passed:
  - PNG size 2200x1400,
  - fresh relative to JSON,
  - nonblank mass/site pixels.
- `verify-maas-20-alt-json.cjs` passed and reports:
  - 20/20 legal pass,
  - 20 unique shapes,
  - 15 unique families,
  - 20/20 parking count satisfied,
  - 20/20 parking mass-stage pass,
  - 0/20 parking permit pass,
  - 0 low-orderliness masses,
  - 0 severe repair candidates,
  - 15 mass languages,
  - max mass language repeat 2,
  - island coverage additive 4 / subtractive 4 / hybrid 6 / sectional 5.
- Direct Python smoke after the trace change reports:
  - 20 candidates,
  - 15 families,
  - 15 languages,
  - 20 candidates with `selection_trace`,
  - 20 `final_balanced_selection` trace events.

Paper/code alignment note:

- This improves traceability for the EvoMass/selection-evidence audit, but it
  is not k-medoid evidence. Do not claim k-medoid representative selection from
  this trace.
- Cached `maas-20-alt-latest.json` still audits as
  `paper_inspired_not_paper_complete` until a full generation refresh writes
  the new trace into JSON.
- Actual current mass quality from verifier is decent for a review sheet, but
  parking remains mass-stage only, not permit-final approval.

Next loop:

- Regenerate the MAAS JSON/PNG through the backend route when the dev server is
  available so `selection_debug.final_selection_trace_evidence` reflects the
  new trace.
- Split `selection/final_balanced.py` into stage modules and preserve the new
  trace behavior.

## Review-Board Anchor Policy And Paper Alignment Check

Reviewed after the final-selection extraction:

- `legal_mesh_optimizer.py` is down to 5,481 lines, but the responsibility is
  not fully cleaned up because `selection/final_balanced.py` is still about 2k
  lines.
- `py_compile`, `design.test_maas_selection_policy`, PNG verification, and JSON
  verification pass.
- The current PNG is better than the early stair-heavy versions but is not yet
  presentation-grade architectural massing.

Paper alignment judgment:

- EvoMass/SSIEA: partially aligned. The system has typology diversity,
  objective proxies, island quotas, and selection evidence, but not true
  steady-state island evolution with simulation feedback.
- DDADesign: partially aligned. The system has massing candidates and
  VLM-ready/proxy preference evidence, but the latest 20-card JSON is not
  actually `vlm_scored`.
- Subtractive massing literature: directionally aligned for the
  additive/subtractive/hybrid language split. The remaining weakness is that too
  much cleanup happens in final selection instead of upstream source geometry
  generation.

Implemented correction:

- `legal_layered_max` is treated as internal law/envelope evidence, not a
  preferred review-board mass.
- In `selection/final_balanced.py`, generic review backfill now suppresses that
  anchor when enough authored/reviewable candidates exist.
- The final emergency fallback can still use the anchor only when the
  non-anchor reviewable pool is insufficient.

Verification nuance:

- A direct smoke against cached `maas-20-alt-latest.json` still reports one
  `legal_layered_max`, because that JSON contains only the already selected 20
  candidates. There is no larger non-anchor pool available in that smoke.
- Judge this policy only after a full backend generation rerun that uses the
  full candidate pool and rewrites JSON/PNG.

Next loop:

- Regenerate through the backend route, not just re-render stale JSON.
- Then compare the new PNG and paper audit.
- Continue splitting `selection/final_balanced.py` by stage. The right end
  state is: upstream grammar/source-geometry/VLM creates design intent, final
  selection curates evidence instead of rescuing weak geometry.

## VLM Top-40 Pre-Selection Implementation

Implemented:

- Added `parking_options.maas_preference_loop` support in
  `generate_legal_mass_variants`.
- The loop runs before final balanced selection, after parking mass-stage
  evidence is available.
- It chooses the full-pool top-k reviewable/legal/parking-stage candidates;
  default `top_k` is 40.
- `require_vlm=true` creates temporary candidate preview PNGs and sends them
  through the OpenAI VLM scorer. A failure raises; it does not downgrade into a
  fake VLM claim.
- Tests can inject a fake scorer to avoid network calls.
- `_design_review_quality_key` now gives `vlm_scored` candidates and
  `distilled_preference_score` explicit priority.
- `attach_paper_alignment_and_preference_evidence` now preserves existing VLM
  preference evidence instead of overwriting it with geometry proxy evidence.
- `render-maas-20-alt.cjs` exposes:
  - `MAAS_PREFERENCE_LOOP_ENABLED`,
  - `MAAS_PREFERENCE_LOOP_REQUIRE_VLM`,
  - `MAAS_PREFERENCE_LOOP_TOP_K`,
  - `MAAS_PREFERENCE_VLM_MODEL`,
  - `MAAS_PREFERENCE_REFERENCE_ROOT`.

Verification:

- `py_compile` passed for MAAS optimizer, paper alignment, selection, and
  preference modules.
- Django tests passed:
  - `design.test_maas_preference`,
  - `design.test_maas_selection_policy`,
  - 29/29 total.
- `node --check render-maas-20-alt.cjs` passed.
- Existing stale `maas-20-alt-latest.json` verifier still passes.

Important limitation:

- The existing `maas-20-alt-latest.json/png` were not regenerated by this pass.
  Therefore the current paper audit still sees `vlm_ready_geometry_proxy` and
  reports `paper_inspired_not_paper_complete`.
- The implementation proof is the test suite plus code path. The visual proof
  requires a full backend regeneration with:

```bash
MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1 \
MAAS_PREFERENCE_LOOP_TOP_K=40 \
MAAS_PREFERENCE_VLM_MODEL="${MAAS_PREFERENCE_VLM_MODEL:-gpt-4.1-mini}" \
node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs
```

Expected post-regeneration checks:

- final candidates include `preference_distillation.mode = "vlm_scored"`;
- `selection_debug.final_vlm_scored_count` is nonzero and should target at
  least 16/20;
- `legal_layered_max` should disappear when the full non-anchor pool is
  sufficient;
- paper audit DDADesign/VLM check should move from weak to partial.

## VLM Regeneration Result

Actual regeneration completed:

- Proof run with LLM off:
  - `MAAS_LLM_LOOP_REQUIRED=0`,
  - `MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1`,
  - `MAAS_PREFERENCE_LOOP_TOP_K=8`,
  - completed in about 97s,
  - proved the VLM scorer path with 8 scored candidates,
  - failed the normal JSON verifier because LLM population evidence was
    intentionally absent.
- Final verified run:
  - `MAAS_LLM_LOOP_REQUIRED=1`,
  - `MAAS_LLM_TARGET_COUNT=120`,
  - `MAAS_LLM_COMPILE_LIMIT=90`,
  - `MAAS_PREFERENCE_LOOP_REQUIRE_VLM=1`,
  - `MAAS_PREFERENCE_LOOP_TOP_K=8`,
  - completed in 927,457ms.

Final run verification:

- `verify-maas-20-alt-json.cjs`: pass.
- `verify-maas-png.py`: pass.
- `legalPass`: 20/20.
- `parkingMassStagePass`: 20/20.
- `parkingPermitPass`: 0/20; not permit-final.
- `uniqueFamilies`: 16.
- `massLanguageDiversity`: 16.
- `llmRawCandidates`: 121.
- `llmCompiledVariants`: 90.
- `finalDirectOpenAILlm`: 18.
- `legal_layered_max`: 0.
- Preference loop:
  - `candidate_pool_count`: 155,
  - `attempted_count`: 8,
  - `vlm_scored_count`: 8,
  - `final_vlm_scored_count`: 7,
  - model: `gpt-4.1-mini`.
- Paper audit:
  - EvoMass: partial,
  - DDADesign/VLM: partial,
  - overall still `paper_inspired_not_paper_complete`.

Visual judgment:

- The new PNG is materially better than the earlier legal-anchor/stair-heavy
  versions: no `legal_layered_max`, stronger family diversity, fewer repeated
  role patterns.
- It is still not final competition-grade massing. Several candidates are still
  low/flat or repair-like, and VLM only affects 7/20 because top-k had to be
  reduced for runtime.

Next technical bottleneck:

- Top-40 VLM scoring is too slow in the current sequential backend path.
- Before claiming top-40 preference distillation, implement parallel/batched
  scoring or a two-stage proxy shortlist, then require
  `final_vlm_scored_count >= 16`.

## Top-40 VLM + Cache Verification

Implemented after the above bottleneck:

- VLM preference loop is now parallelized with
  `maas_preference_loop.parallel_workers`.
- LLM population generation now supports:
  - `batch_workers`,
  - `cache_path`,
  - `MAAS_LLM_BATCH_CACHE_PATH`,
  - payload-level forwarding from `render-maas-20-alt.cjs`.
- The first successful full LLM run wrote:
  `docs/ai-session-memory/maas-cache/latest-llm-batch.json`.
- Subsequent runs cache-hit the LLM population and still compile the 120
  MassDSL sequences, so the VLM/selection loop can be tested without waiting
  for a new 120-candidate LLM generation every time.
- Final review guards now run after balanced selection:
  - preserve at least 16 image-backed VLM-scored candidates;
  - preserve at least 18 direct OpenAI LLM-authored candidates;
  - recover height diversity, formal-principle diversity, family diversity, and
    mass-language diversity.

Latest verified output:

- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`

Verifier result:

- `verify-maas-20-alt-json.cjs`: pass.
- `verify-maas-png.py`: pass.
- `legalPass`: 20/20.
- `parkingMassStagePass`: 20/20.
- `parkingPermitPass`: 0/20; still not permit-final.
- `preference_loop.attempted_count`: 40.
- `preference_loop.vlm_scored_count`: 40.
- `selection_debug.final_vlm_scored_count`: 16.
- `finalDirectOpenAILlm`: 18.
- `uniqueFamilies`: 15.
- `massLanguageDiversity`: 15.
- `sameHeightMaxCount`: 12.
- `formalPrincipleDiversity`: 6.
- `finalCoverageRepairLlm`: 0.
- `llm_proposal_loop.cache.hit`: true on the final verification loop.

Current paper-alignment status:

- Better than the prior `top_k=8` proof: DDADesign/VLM-style second-stage
  visual preference now affects most of the final sheet rather than only a
  handful of candidates.
- Still not paper-complete:
  - EvoMass is still only approximated by quota/island-style selection and
    proxy objective scoring, not a true SSIEA island evolution loop.
  - Archi-Agents still mostly revises selection, not full critic-to-geometry
    mutation.
  - VLM scoring is a preference/reranking stage over generated massing PNGs,
    not diffusion/control generation.
  - Performance objectives are early massing proxies, not Honeybee/Radiance or
    validated simulation.

## Modularization Checkpoint

Refactor completed after top-40 VLM verification:

- Moved VLM preference scoring internals from
  `design.maas.legal_mesh_optimizer` to:
  `design.maas.preference.loop`.
- Moved final VLM/direct-LLM/diversity preservation guards to:
  `design.maas.selection.preference_guards`.
- `legal_mesh_optimizer.py` remains the legal endpoint orchestrator, but now
  calls preference/review modules via explicit callback bundles.
- The module boundary is intentional:
  - preference module cannot decide law or parking;
  - selection guard module cannot generate geometry;
  - legal optimizer remains responsible for legal envelope compilation and
    hard-gate orchestration.

Verification after modularization:

- `py_compile`: pass for the changed MAAS modules.
- Django tests:
  - `design.test_maas_preference`,
  - `design.test_maas_selection_policy`,
  - 30/30 pass.
- Cache-hit render completed and regenerated latest JSON/PNG.
- `verify-maas-20-alt-json.cjs`: pass.
- `verify-maas-png.py`: pass.
- Final metrics retained:
  - VLM top-40 scored 40/40;
  - final VLM-scored 16/20;
  - final direct OpenAI LLM 18/20;
  - legal pass 20/20;
  - parking mass-stage pass 20/20;
  - permit-final parking pass still 0/20.
