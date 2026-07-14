# MAAS Visual Failure Handoff - 2026-07-10

Read this before making more MAAS code changes.

## Current Human Verdict

The latest MAAS JSON/PNG verifier passes, but the massing is still visually bad.
Do not treat the current verifier pass as "problem solved".

User-visible problem:

- The PNG looks like broken orange fragments rather than clean architectural
  massing.
- Many cards lost the earlier readable stepped/rectangular mass anchors.
- Some candidates are over-composed with ribbons, fins, small plates, and
  cross/evolution pieces.
- The result has label diversity, but not enough clean architectural order.

Latest artifacts inspected:

- `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`

Latest machine verifier status:

- JSON verifier: pass.
- PNG freshness/color verifier: pass.
- `legalPass=20/20`.
- `parkingCountSatisfied=20/20`.
- `parkingMassStagePass=20/20`.
- `uniqueFamilies=15`.
- `massLanguageDiversity=15`.
- `rolePatternMaxCount=2`.
- `sameHeightMaxCount=12`.
- Island coverage additive/subtractive/hybrid/sectional: `4/6/6/4`.

Important: those metrics are necessary but not sufficient. They did not catch
visual mass failure.

## Model / Codex Context

- Current OpenAI/Codex direction from the user: use the better 5.6-class model
  path where available.
- Project defaults were changed to `gpt-5.6-luna`:
  - `ARR/backend/design/maas/llm_proposals.py`
  - `ARR/backend/design/maas/preference/vlm_scorer.py`
  - `docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`
- Direct API smoke test for `gpt-5.6-luna` returned HTTP 200 in this session.
- Do not invent unavailable model IDs. Preserve explicit official/verified
  model IDs only.
- If a future session discusses OpenAI/Codex model availability, verify against
  official OpenAI docs or a direct API smoke test.

## VLM Is Real, But Not Enough

VLM was actually used in the latest run:

- `response.preference_loop.status=scored`
- `response.preference_loop.require_vlm=true`
- `response.preference_loop.top_k=40`
- `response.preference_loop.attempted_count=40`
- `response.preference_loop.vlm_scored_count=40`
- `response.preference_loop.model=gpt-5.6-luna`
- final 20 includes 16 candidates with
  `preference_distillation.mode=vlm_scored`,
  `vlm_status=scored`, and `vlm_model=gpt-5.6-luna`.

But current VLM role is only:

1. crop candidate PNGs;
2. score/rerank generated candidates;
3. help preserve top candidates.

Current VLM role is not:

- generating new geometry;
- mutating MassDSL after a bad visual critique;
- rejecting the whole population before final selection;
- guaranteeing competition-grade massing.

Therefore, if the source candidate pool is visually weak, VLM can only choose
among weak options. Next work must connect VLM/critic feedback back to geometry
generation or add stricter pre-VLM clean-mass gates.

## Current Bad Visual Signals From JSON

Latest inspected final 20 contained too many high-complexity candidates:

- `maas_01`: `surface_count=76`, `vols=7`,
  `branch_atrium`, shape `llm_b3_5_branch_taper_atrium_tower_085`.
- `maas_02`: `surface_count=68`, `vols=6`,
  `diagonal_connector`, evolved overlap/offset section.
- `maas_04`: `surface_count=58`, `vols=6`,
  `overlap_slabs`, evolved terrace link.
- `maas_09`: `surface_count=57`, `vols=6`,
  `overlap_slabs`.
- `maas_11`: `surface_count=58`, `small_fragment_count=2`,
  `tapered_tower`.
- `maas_14`: `surface_count=65`, `small_fragment_count=2`,
  `tapered_tower`.
- `maas_17`: `surface_count=72`, `vols=7`,
  `bend_ribbon` crossover.

Conclusion:

- `source_signature.surface_count` in the 50-70+ range correlates with noisy,
  over-fragmented cards.
- `visible volumes >= 6` often reads as too many pieces in the small review
  PNG.
- Evolution/crossover variants are passing counters but often look messy.
- Current `orderliness_score` is too forgiving. It can be high while the PNG
  still looks visually chaotic.

## Do Not Repeat

- Do not keep adding taxonomy labels just to pass `uniqueFamilies`.
- Do not treat `src surfaces` as proof of richer architecture.
- Do not let `surface_count=60+` survive unless the PNG is visibly clean.
- Do not let VLM top-k preservation override clean-mass readability.
- Do not call the result competition-grade just because JSON verifier passes.
- Do not erase legal/parking gates; law and mass-stage parking are still hard
  constraints.

## Next Correct Implementation Direction

Fix the generator/selector before more paper or presentation work.

Priority 1: add a hard clean-mass prefilter before final VLM rerank.

Suggested policy:

- reject or heavily penalize final candidates with `surface_count > 48`;
- reject or heavily penalize final candidates with `visible_volume_count > 5`;
- reject candidates with `small_fragment_count > 1`;
- require at least one strong base/primary/support hierarchy;
- require clean silhouette without many small coplanar fins;
- preserve legal pass and parking mass-stage pass.

Priority 2: restore clean anchor quotas.

Final 20 should include a minimum number of visually stable anchors:

- clean rectangular/slab anchor;
- clean step/terrace anchor;
- clean podium/tower or slender bar anchor;
- clean courtyard/void anchor;
- clean diagonal/bridge or sectional anchor.

These anchors are not fallback failures. They are necessary visual controls so
the sheet does not become all noisy experimental fragments.

Priority 3: restrict evolution/crossover.

- Crossover and evolved parameter children should be admitted only if they pass
  stricter visual simplicity thresholds.
- Evolution must not mean more pieces. It should improve a dominant gesture.
- Cap final evolved/crossover candidates unless they clearly outperform clean
  anchors visually.

Priority 4: connect VLM critique to geometry mutation.

Current VLM is a reranker. The next research-grade loop should be:

1. generate candidate;
2. render crop;
3. VLM returns structured critique:
   `too_fragmented`, `weak_primary_mass`, `needs_clean_anchor`,
   `too_many_surface_pieces`, `good_void`, `good_step_mass`;
4. convert critique to MassDSL/source-geometry mutation;
5. rerun law/parking gates;
6. rerender and re-evaluate.

## Practical First Patch For Next Session

Start with deterministic visual cleanup, not another model change.

## Files To Inspect First

Do not start by changing model names. Inspect these files in this order.

### 1. `ARR/backend/design/maas/legal_mesh_optimizer.py`

Why:

- It owns the high-level MAAS candidate pipeline and final evidence attachment.
- It defines the current visual/orderliness gates that are too forgiving.
- It defines semantic normalization that can hide visual failure behind better
  labels.

Primary functions/sections to inspect:

- `_architectural_order_gate`
  - Current problem: lets visually noisy candidates through if they have enough
    formal/evidence labels.
  - It currently allows high `surface_count` and high `visible_volume_count`
    candidates too easily.
- `_design_review_quality_key`
  - Current problem: VLM/preference/LLM authorship can outrank clean mass
    readability.
  - Needs stronger negative terms for high `surface_count`, 6-7 visible
    volumes, small fragments, and over-composed evolution/crossover names.
- `_orderliness_evidence`
  - Current problem: scores can be high even when PNG looks fragmented.
  - Needs a visual-fragment penalty based on surface count and coplanar/helper
    pieces, not only polygon area ratios.
- `_source_family`, `_research_diversity_descriptor`, `_research_mass_language`
  - Current problem: useful for taxonomy, but can make broken forms look
    diverse on paper.
  - Do not add more taxonomy labels unless they improve visual gating or
    source geometry.
- `_attach_visual_diversity_evidence`
  - Confirm that canonical family/language changes are mirrored into
    `source_signature.rule_evidence.research_diversity_descriptor`.

First patch target:

- Add/strengthen clean-mass gate:
  - `surface_count > 48` should be a severe issue for final review.
  - `visible_volume_count > 5` should be a severe issue for final review.
  - `small_fragment_count > 1` should be a severe issue.
  - Evolution/crossover candidates with high surface count should be heavily
    penalized or rejected from final 20.

### 2. `ARR/backend/design/maas/selection/final_balanced.py`

Why:

- It chooses the public final 20 review cards.
- It currently balances counters well, but still allows visually noisy cards.

Primary functions/sections to inspect:

- `final_design_balanced_selection`
  - Current problem: final selection solves family/language/island metrics but
    not visual cleanliness.
- `attach_final_selection_trace`
  - Useful to confirm whether noisy candidates enter during final balancing.
- Any block using:
  - `height_bucket`
  - `_research_mass_language`
  - `_research_quota_group`
  - `_source_family`
  - `_design_review_quality_key`

First patch target:

- Add a final clean candidate predicate before backfill and replacement pools:
  - legal and parking pass are still required;
  - source geometry required;
  - reject high surface/volume/noisy evolution candidates unless they are needed
    as last fallback.
- Add clean anchor quotas before exotic variety:
  - at least one simple slab/rectangular anchor;
  - at least one clean stepped/terrace anchor;
  - at least one clean podium/tower or slender-bar anchor;
  - at least one clean courtyard/void anchor;
  - at least one clean sectional/bridge anchor.

### 3. `ARR/backend/design/maas/selection/preference_guards.py`

Why:

- It runs after balanced selection and can undo visual balance to preserve VLM
  or direct LLM minimums.
- This already caused a failure once: VLM guard replaced balanced cards.

Primary functions/sections to inspect:

- `enforce_final_vlm_preference_minimum`
  - Current problem: VLM-scored candidates can still be visually poor.
- `enforce_final_direct_llm_minimum`
  - Current problem: direct LLM minimum may preserve generated but ugly forms.
- `recover_final_vlm_review_metrics`
  - Current problem: projection score mostly tracks verifier metrics, not PNG
    cleanliness.
- `metric_score`
  - Add clean-mass penalties here so post-VLM repair cannot reintroduce visual
    clutter.

First patch target:

- Add clean-mass projection failures:
  - `surface_over`
  - `volume_over`
  - `small_fragment_over`
  - `evolved_crossover_over`
- Keep VLM active, but only among candidates that pass clean-mass threshold.

### 4. `ARR/backend/design/maas/source_geometry/compiler.py`

Why:

- This is where the geometry actually becomes many pieces.
- The visual failure is not only selection. The compiler creates over-fragmented
  source volumes for some families.

Primary functions/sections to inspect:

- `_family_plan_volumes`
  - Current problem families:
    - `branch`
    - `overlap`
    - `bend`
    - `pinch`
    - `extrude`
    - `nest`
  - Many of these create 5-7 source volumes and 50-70+ source surfaces.
- `_compose_secondary_language`
  - Current problem: secondary language adds another piece even when the primary
    already has enough massing articulation.
  - Should cap added secondary pieces when source volume count is already high.
- `_source_surfaces`
  - It exposes `surface_count`; useful for measuring failure but should not be
    gamed by adding surfaces.
- `_layout_volumes`
  - Check if formal-principle route produces cleaner 3-5 volume alternatives
    than family-plan route.

First patch target:

- For final-review candidates, prefer 3-5 source volumes.
- Collapse excess helper volumes for `branch`, `overlap`, and `bend` into one
  dominant primary + one secondary + one void/core piece.
- Do not let `__evo_cross_` variants add more geometry layers unless they pass
  clean-mass gate.

### 5. `ARR/backend/design/maas/evolution/island_loop.py`

Why:

- Several ugly cards are evolved/crossover variants.
- Evolution currently increases formal variation, but often increases clutter.

Primary functions/sections to inspect:

- parameter mutation creation for `__evo_param_`
- critic-section mutation creation for `__evo_critic_section`
- crossover creation for `__evo_cross_`

First patch target:

- Add a simplicity objective or penalty before evolved variants enter the legal
  candidate pool.
- Do not allow evolution to increase piece count indefinitely.
- Treat crossover as experimental: final set should cap it unless VLM and
  clean-mass gates both agree.

### 6. `ARR/backend/design/maas/preference/loop.py`

Why:

- This confirms VLM is actually scoring crops, but it is not enough.
- Future improvement should route VLM critique back into generation.

Primary functions/sections to inspect:

- `apply_preference_loop`
- candidate preview PNG/crop scoring path
- VLM result attachment under `preference_distillation`

First patch target:

- Do not merely increase `top_k`.
- Add structured VLM critique fields if implementing feedback:
  - `too_fragmented`
  - `weak_primary_mass`
  - `needs_clean_anchor`
  - `too_many_surface_pieces`
  - `good_void`
  - `good_step_mass`
- Feed those fields into MassDSL/source-geometry mutation only after law and
  parking remain hard gates.

## Suspicious Latest Cards

Use these as regression examples when inspecting PNG/JSON:

- `maas_01`
  - `surface_count=76`, `vols=7`, `branch_atrium`
  - visually over-fragmented.
- `maas_02`
  - `surface_count=68`, `vols=6`, evolved diagonal/overlap/offset section
  - too many source surfaces for a clean section mass.
- `maas_04`
  - `surface_count=58`, `vols=6`, evolved overlap/terrace
  - noisy slab/ribbon composition.
- `maas_09`
  - `surface_count=57`, `vols=6`, overlap slab terrace
  - repeated over-composed language.
- `maas_11`
  - `surface_count=58`, `small_fragment_count=2`, tapered tower
  - fragmented despite high enough verifier score.
- `maas_14`
  - `surface_count=65`, `small_fragment_count=2`, tapered tower
  - same visual failure class as `maas_11`.
- `maas_17`
  - `surface_count=72`, `vols=7`, bend-ribbon crossover
  - crossover clutter; should be capped or cleaned.

## Concrete Next-Session Plan

1. Read this file and inspect the latest PNG manually.
2. Run the diagnostic command below and identify all candidates with:
   - `surface_count > 48`;
   - `vols > 5`;
   - `small_fragment_count > 1`;
   - shape containing `__evo_cross_`.
3. Patch `legal_mesh_optimizer.py` clean-mass gate and quality key.
4. Patch `preference_guards.py` so VLM preservation cannot reintroduce noisy
   candidates.
5. Patch `final_balanced.py` only after the two guard layers are fixed.
6. Regenerate PNG/JSON with `gpt-5.6-luna` and VLM enabled.
7. Verify:
   - JSON verifier pass;
   - PNG verifier pass;
   - manual PNG review: at least several clean, readable anchor masses.

## Likely Files

- `ARR/backend/design/maas/legal_mesh_optimizer.py`
  - `_architectural_order_gate`
  - `_design_review_quality_key`
  - source family/language normalization only if it affects visual gate evidence
- `ARR/backend/design/maas/selection/final_balanced.py`
  - final clean-mass constraint before backfill
- `ARR/backend/design/maas/selection/preference_guards.py`
  - VLM guard must respect clean-mass projection score
- `ARR/backend/design/maas/source_geometry/compiler.py`
  - reduce noisy multi-piece source volumes for `branch`, `overlap`, `bend`,
    `tapered_tower`, and crossover-derived variants

Fast diagnostic command:

```bash
node - <<'NODE'
const d=require('./docs/playwright/design-route-live-verify/maas-20-alt-latest.json');
const f=d.response.feature_collection.features;
for (const [i,x] of f.entries()) {
  const p=x.properties||{}, s=p.source_signature||{}, r=s.rule_evidence||{}, rd=r.research_diversity_descriptor||{}, o=p.orderliness_evidence||{};
  console.log(`${String(i+1).padStart(2,'0')} ${p.variant_id} surf=${s.surface_count} vols=${(p.mass_volumes||[]).length} fam=${s.family||p.operator_family} lang=${rd.mass_language||r.mass_language} h=${p.height} order=${o.orderliness_score} main=${o.main_mass_area_ratio} small=${o.small_fragment_count} shape=${p.mass_shape}`);
}
NODE
```

Expected next visual target:

- fewer `surface_count > 50` cards;
- fewer 6-7 volume cards;
- at least several clean, readable simple masses;
- less orange fragment clutter;
- legal and parking mass-stage still pass;
- VLM remains enabled, but only after clean-mass candidate filtering.

## 2026-07-10 Implemented Follow-up

- Same-run two-generation `VLM critic -> MassDSL mutation -> compile ->
  legal/parking/clean gate -> VLM rescore` is implemented.
- VLM input is now a four-view pack (isometric/opposite/front/top), not a
  single silhouette.
- Compiler prunes secondary liner/core/cap helpers when their 3D occupancy is
  already mostly covered by a primary mass.
- Clean anchors now include restrained bar/stack, courtyard, and podium/tower
  mutations; clean two-volume anchors are explicitly valid.
- The initial `surface_count <= 48` emergency gate reduced the failure class.
  After a successful measured run (avg 26.1, max 48), the competition-review
  gate was tightened to `surface_count <= 36`; final review volumes remain
  capped at 4.
- Latest measured pre-tightening run: JSON/PNG pass, legal 20/20, parking
  mass-stage 20/20, 3 accepted critic geometry revisions, volume histogram
  `2:3, 3:8, 4:9`.
- This is still paper-inspired, not paper-complete. Do not claim diffusion
  fine-tuning or MASS topology search exists.

### Final restarted-server proof

- The backend was restarted after the 36-surface policy change; do not use the
  earlier no-reload run as proof.
- Latest final JSON/PNG verifiers: pass/pass.
- Legal: 20/20; parking mass-stage: 20/20.
- Surface count: average 25.55, maximum 35, `over36=0`.
- Visible volumes: maximum 4; histogram `2:1, 3:9, 4:10`.
- Four-view VLM-scored final cards: 15/20.
- Same-run critic: 44 evaluated mutations, 5 accepted revisions (11.36%).
- No human pairwise preference JSONL exists yet. Fine-tuning is therefore not
  evidence-ready; collect architect labels across held-out sites before LoRA,
  DPO/MDPO, or reward-model training.

## 2026-07-11 Root Architecture Replacement

- Added `arr.maas.component_graph.v1`: every mass now has explicit
  root/primary/support/void/connector nodes, parent-child edges, optional-node
  semantics, validation, and a flat `VerbSequence` compatibility adapter.
- Source geometry compiler now treats the component graph as the genotype and
  exports it in every source signature.
- Added generator-independent `arr.maas.mass_coherence.v1` objective measuring
  3D redundant overlap, collision energy, hierarchy, fragments, volume budget,
  and plan connectivity.
- Coherence, legal repair retention, law, and parking are final hard gates;
  final guards/backfill cannot reinsert a failed candidate.
- VLM critic mutation now removes optional graph nodes or strengthens the
  primary graph node, instead of editing a specific card/shape by name.
- Added constrained cross-generation archive evidence to the critic loop.
- Verifier composition evidence now uses component graph edges rather than
  rewarding extra helper volumes.

Final restarted-server proof:

- JSON/PNG verifier: pass/pass.
- component graph valid: 20/20.
- coherence hard pass: 20/20; average 0.9203.
- legal repair retention pass: 20/20; minimum 1.0 in latest final set.
- legal/parking mass-stage: 20/20.
- surface average 23.5, maximum 34; visible-volume maximum 4.
- critic accepted geometry revisions: 19; constrained archive: 58.
- tests: 35 passed.

Remaining honest research gaps are not mass-by-mass fixes: editable B-Rep
semantics, joint program/circulation/daylight simulation, MASS prompt/topology
search, trained diffusion prior, and architect-labeled preference data.

## 2026-07-11 graph-native + exact-selection checkpoint

- The compiler now executes `MassComponentGraph` parent topology; the flat
  sequence path is only a compatibility adapter. Changing a node parent changes
  compiled geometry and is regression-tested.
- Final review selection now uses SciPy/HiGHS 0-1 MILP after legal, parking,
  architectural-order, coherence, and compiler-default gates.
- Never append the previous heuristic tail after an exact projection. This bug
  once returned 30 cards after the MILP correctly selected 20.
- The verifier now fails unless `final_integer_projection.status` is
  `optimal`/`feasible`; heuristic fallback cannot masquerade as success.
- Latest proof after a real server restart: 20 cards, projection `optimal`, 3
  policy attempts, graph valid 20/20, coherence hard-pass 20/20, VLM-scored
  13/20, max surface count 36, max small fragments 0.
- Important operational lesson: the old `--noreload` Django process must be
  restarted after selector/compiler edits. Two expensive runs used stale code
  before this was detected from the old Cartesian attempt trace.
- Visual judgment remains stricter than verifier pass: the set is materially
  cleaner, but some folded/sloped-roof cards still have overlapping linework.
  Do not call this fully competition-grade yet; next work should improve those
  family-specific graph primitives without weakening legal/parking/coherence.

## 2026-07-11 ArchDaily pairwise-diversity continuation

- Added 54 ArchDaily JSON API project references under
  `archdaily/api/massing_diversity_20260711`; the loaded corpus increased from
  152 to 206 references.
- Added `selection/visual_similarity.py`. It combines executable family,
  mass-language, role topology, surface/volume/height, VLM concept vector, and
  ArchDaily API reference overlap.
- The exact MILP now receives pairwise mutual-exclusion constraints and records
  conflict count/threshold. One verified run solved `optimal` at threshold
  0.86 with 178 conflict pairs, coherence 20/20, max surfaces 34, and max small
  fragments 1.
- Direct PNG review still found near-identical split-bridge and sloped-roof
  cards, so a stronger same-language + same-role + near-identical-geometry
  hard conflict and language-cap profiles were added.
- Strong language cap 2 proved infeasible for some clean eligible pools. The
  current code tries cap 2 first, then cap 3 with 0.92/0.96 similarity safety
  profiles. The final validation request exceeded the 1200-second HTTP limit,
  so this newest policy is NOT yet accepted as verified.
- Do not use the current `maas-20-alt-latest.json` as a success checkpoint: it
  is an earlier infeasible fallback artifact. Re-run with a durable/background
  job or cached VLM evidence, then require exact optimal/feasible + coherence
  20/20 + direct PNG review.

## 2026-07-11 cost-controlled VLM policy

- Default generation and VLM model changed from preview `gpt-5.6-luna` to
  `gpt-5.4-mini`. GPT-5.5 exists but is unnecessary flagship spend for this
  well-defined structured architecture QA task.
- Added persistent VLM cache keyed by model + exact geometry/volumes + top
  reference images. Cache hit/miss counts are emitted by the preference loop.
- Added a mandatory final VLM completion pass: when VLM is required, all final
  20 cards must be image-scored or the request raises. The JSON verifier now
  requires `final_vlm_completion.final_vlm_scored_count == 20`.
- Provenance/role-string quotas were reduced to meaningful floors because they
  were forcing fragmented role labels. Visual quality remains governed by
  graph/coherence, clean-mass, pairwise conflict, and 20/20 final VLM gates.

## 2026-07-12 static review corrections

- Fixed a semantic bug: final VLM completion alone was too late to influence
  MILP selection. In required-VLM mode, only genuinely `vlm_scored` candidates
  may now enter the exact integer pool.
- Geometry-equivalent duplicates now score exactly 1.0, so late relaxed
  similarity profiles cannot accidentally permit a declared hard duplicate.
- Parallel persistent-cache writes now use UUID temporary names; same-key
  concurrent evaluations cannot collide on a PID-only temp file.
- Relevant selection/preference test suites: 39/39 pass.
- Full paid generation was intentionally not run during this review. Remaining
  runtime question: whether the stratified 30-candidate VLM pool always has
  enough family/island capacity for a feasible exact 20-card solution.

## 2026-07-12 service latency architecture

- Full generation/VLM is not a synchronous product request. It remains an
  offline refresh workload and must never be hidden behind heuristic fallback.
- Added durable verified cache (`design.maas.service_cache`). A result is
  publishable only when it has 20 cards, exact projection optimal/feasible,
  final VLM 20/20, and coherence 20/20.
- `POST /design/maas/legal-variants/` with `service_mode: "cached"` returns a
  verified cache hit immediately or an explicit 404 `cache_miss`; it never
  starts the expensive generation path.
- `service_mode: "refresh"` may be used by a worker and atomically publishes
  only verified output. Unverified/fallback output returns conflict and is not
  cached.
- Offline worker command:
  `python manage.py refresh_maas_service_cache <payload.json>`.
- Service/preference/selection tests: 41/41 pass. No verified production cache
  has been published yet; the latest paid run was intentionally terminated
  when the synchronous service-latency flaw was recognized.

## 2026-07-12 root geometry and clean-pool correction

- Found a direct generator cause of the 6--7 fragment legal anchor: when the
  legal floor area changed, `_compact_visual_volumes` emitted every floor as a
  separate visible volume. Legal floor plates remain the accounting source of
  truth, but the review mass is now compressed to at most four bands chosen
  from the strongest relative step changes.
- The legal layered anchor now receives the same measured
  `component_graph` and `coherence_evidence` as grammar-generated candidates;
  it no longer bypasses or fails the clean exact pool because evidence is
  missing.
- Non-LLM runs no longer request impossible direct-LLM MILP quotas. Added
  strict pairwise profiles where provenance/family/island quotas become soft
  before visual similarity is relaxed.
- Evolution was expanded from 64 to a bounded 96 children, round-robin 24 per
  additive/hybrid/sectional/subtractive island. This exposes later seed
  typologies instead of repeatedly selecting the first sixteen from each
  island.
- Latest no-cost deterministic proof (`MAAS_LLM_LOOP_REQUIRED=0`, preference
  VLM off): 20 candidates, exact MILP `optimal`, clean pool 72, similarity
  threshold 0.90, language cap 3, 102 conflict pairs, component graph 20/20,
  coherence 20/20, visible/source volume maximum 4, surface maximum 35, small
  fragment maximum 0. Relevant tests: 48/48 pass.
- Direct PNG review is materially more varied (extruded fin, reflected court,
  nested stack and connectors now survive), but three terrace-language cards
  remain. Do not call the deterministic sheet perfect competition-grade work;
  final publication still requires cached 20/20 VLM review and an architect
  preference pass. The deterministic run proves the root geometry/selection
  path, not trained architectural taste.

## 2026-07-12 visible-language cap correction

- The exact selector previously capped broad research language. This grouped
  visually different notch/twin-bar/terrace masses under
  `bar_notch_terrace`, while failing to directly cap the repeated synthesis
  users actually see on the card.
- Added `_projection_visual_language`: integer projection now uses the
  materialized `section_profile_materialized.kind` (falling back to section
  profile/research language). Research language remains intact as provenance.
- Added bounded clean grammar anchors for podium bar, courtyard block, twin
  wing and shifted slab. These are real short component programs, not renamed
  cards, and therefore still face compiler, legal, parking, order and
  coherence gates.
- Latest no-cost full run: exact `optimal` at similarity 0.90 and visible
  language cap 2 (previously cap 2 was infeasible and cap 3 was required),
  clean pool 74, graph/coherence 20/20, maximum visible volumes 4, maximum
  surfaces 35, maximum small fragments 1. The final sheet has no visible
  synthesis kind more than twice. Tests remain 48/48.

## Next required language: disciplined box aggregation

- The clean-mass correction must not collapse the design space into only
  monolith/cut/terrace/bridge types. The user explicitly wants BIG/OMA-like
  aggregate massing: several rectangular volumes attached, shifted, stacked
  or crossed into one readable composition.
- Do not implement this as random Lego scatter. Required genotype is one
  dominant rectangular mass, one or two subordinate boxes, and an explicit
  support/overlap/core relationship; maximum four visible volumes and the
  existing legal, parking, component-graph and coherence hard gates remain.
- Recover clean variants of these languages: shifted box stack, interlocking
  bars, cantilevered box over podium, clustered program blocks, and crossed
  slabs. Their silhouette/plan topology must be materially distinct, and the
  final visible-language cap still applies.
- Current evidence shows why this is missing: `torqued_stack` and
  `stacked_shifted_platforms` candidates are generated, but many fail
  coherence/order due redundant overlap, excessive surfaces or weak main-box
  hierarchy. Fix the compiler/graph construction for those families rather
  than weakening the gates.

## Required product contract: conversational reference-conditioned editing

- This must become a stateful multi-agent design system, not a one-shot sheet
  generator. A client or architect must be able to attach reference images,
  select a candidate, and request revisions in conversation (for example:
  cantilever the upper box, keep the courtyard, reduce height, follow this
  precedent's hierarchy, or preserve parking).
- VLM/reference retrieval supplies visual intent and critique; it does not
  directly mutate geometry. A design-intent agent translates conversation and
  reference evidence into typed component-graph operations; a geometry agent
  applies them; legal/parking agents re-run hard constraints; a visual critic
  compares the render with the requested intent; an orchestrator retains the
  accepted/rejected revision history.
- The editable state is `MassComponentGraph`, with stable component IDs,
  parent/support relations and parameter provenance. Never regenerate an
  unrelated mass when the user asks to edit one component. Every turn retains
  the previous accepted graph and emits a graph diff plus legal, parking,
  coherence and visual evidence.
- Reference images may guide hierarchy, proportion, silhouette, void and
  aggregation, but must not be copied as geometry. Store reference provenance
  and use reference-conditioned scoring together with explicit user
  constraints.
- Interactive turns use cached reference embeddings and bounded graph
  mutations. Expensive corpus refresh/fine-tuning stays offline; a small edit
  must not synchronously regenerate the full population or hide a heuristic
  fallback.

## 2026-07-12 box-aggregation compiler checkpoint

- Corrected the actual formal-principle compiler, not only downstream family
  helpers. `torqued_stack` is now three vertically ordered attached plates;
  `stacked_shifted_platforms` is three shifted boxes; `array_cluster` is a
  common shallow podium with two supported program boxes.
- Removed full-height helper/core overlaps that made the same box occupy the
  same space repeatedly. Direct compiler probes changed as follows:
  interlock coherence 0.058/fail -> 1.0/pass; overlap 0.0/fail -> 1.0/pass;
  array cluster 0.0/fail with three fragments -> 1.0/pass with zero fragments.
- Latest full no-cost run after this correction: exact projection `optimal` at
  similarity 0.90 and visible-language cap 2; clean exact pool increased from
  74 to 95; coherence 20/20; maximum visible volume 4; maximum surface count
  35; maximum small fragments 0. `array_cluster`, two bend ribbons and two
  pinched/stacked box compositions now survive the final sheet.
- The box language is now present but still needs reference-conditioned/user
  editing controls described above. Do not conflate this generator checkpoint
  with completion of the stateful conversational revision API.

## 2026-07-12 mass-scale correction

- Full-sheet review exposed an under-scaled `array_cluster` at BCR 3.01% and
  FAR 5.61%. Root cause: the `array` verb replaced the canonical footprint
  with the union of its miniature cells before the formal podium/box compiler
  ran.
- The array verb now preserves the authored footprint as the common podium
  datum while retaining layout units only for upper program-box placement.
  Rule priors now use 2--3 substantial boxes (`unit_scale` 0.36--0.58) rather
  than 3--5 scattered miniature cells.
- Added final review mass-scale hard gates: BCR must be at least 8% and FAR at
  least 12%. This is a review-sheet gate and does not modify legal accounting.
- Latest no-cost full run: exact MILP `optimal`, clean pool 100, similarity
  0.90, visible-language cap 2, coherence 20/20, maximum volumes 4, maximum
  surfaces 35, maximum small fragments 0. Final-set minimum BCR is 10.16% and
  minimum FAR is 15.87%. Two readable `array_cluster` alternatives survive at
  BCR 35.98/37.55% and FAR 59.0/47.81%. Relevant tests: 49/49 pass.

## 2026-07-12 folded-roof cleanup

- The noisy roof image was partly real geometry and partly a verification
  renderer bug: a synthetic roof polygon plus two ribs was drawn over already
  materialized source volumes. The duplicate overlay is removed.
- `folded_section` now compiles as a common full plinth plus low/high roof
  boxes meeting at one datum, instead of two near-full-plan polygons crossing
  each other. Direct result: 3 volumes, coherence 1.0, redundant overlaps 0,
  small fragments 0, source surfaces reduced from 22 to 15 in the probe.
- Latest no-cost full run remains exact `optimal`, clean pool 106, similarity
  0.90, visible-language cap 2, coherence 20/20, minimum BCR 10.16%, minimum
  FAR 17.7%, and small fragments maximum 0. Both selected roof candidates have
  coherence 1.0 and 17 surfaces after legal materialization.
- Direct PNG review confirms the crossed synthetic roof/rib clutter is gone.
  The next correction is within-language near-duplication for the two bend
  ribbons; same-language plan/aspect hard-duplicate tolerances were tightened
  from 0.05 to 0.10 rather than lowering the global diversity gate.

## 2026-07-12 post-selection and bend-duplicate correction

- Found and blocked a dangerous contract violation: evidence attachment could
  re-materialize section geometry after the exact MILP had evaluated pairwise
  conflicts. Final source volumes are now immutable during evidence
  attachment, and a geometry fingerprint invariant raises if any post-selection
  evidence step mutates them.
- Projection visual language is now canonicalized from source family before
  optional profile/research labels. This prevents candidates from appearing as
  different languages to MILP and both becoming `bend_ribbon` only at render
  time.
- With preference/VLM disabled, the former bend pair scored about 0.8945 before
  concept evidence and 0.9945 after evidence. Same-language isometric hard
  duplicate detection now tolerates aspect variation up to 0.25 while retaining
  the normalized centroid/plan-tail gate. A shifted-plan regression remains
  explicitly protected.
- Latest full no-cost proof: exact `optimal`, clean pool 106, similarity 0.90,
  visible-language cap 2, conflict pairs 178, coherence 20/20, minimum BCR
  10.16%, minimum FAR 17.7%, maximum small fragments 0. The near-identical bend
  pair was replaced by materially different alternatives: BCR 16.48/FAR 21.98
  versus BCR 28.6/FAR 36.67. Tests: 50/50 pass.

## 2026-07-12 final audit, multi-site and VLM publication

- Static/final audit added exception traceback logging and confirmed the exact
  set no longer receives a heuristic tail. Evidence attachment cannot mutate
  final mass volumes because of the geometry fingerprint invariant.
- Multi-site regression on PNU `1168011800104670003` exposed two independent
  empty-provisional-set crashes: recovery height balancing and VLM metric
  recovery both called `max()` on an empty set. The heuristic selector and
  preference guard now treat empty provisional results as a valid handoff to
  the downstream full legal-pool exact projection. Regression suite: 51/51.
- That Dogok parcel remains honestly infeasible for both apartment and
  neighborhood-use probes: 376 legal candidates were generated, but mass-stage
  parking hard-pass count was 0. Parking was not weakened. API output now adds
  `generation_status=infeasible` and the explicit reason
  `no_candidate_passed_mass_stage_parking_hard_constraint` instead of silently
  presenting count 0 as a successful design sheet.
- Final required-VLM run on PNU `1168011800104170004` used
  `gpt-5.4-mini`: preselection VLM 40/40 (14 cache hits, 26 misses, 0 failures),
  final completion 20/20 (19/19 attempted cache hits plus the already-scored
  anchor), reference corpus 206, exact projection `optimal`, graph/coherence
  20/20, minimum BCR 10.16%, minimum FAR 19.04%, maximum volumes 4, maximum
  surfaces 35, maximum small fragments 0. Direct PNG review was completed.
- The verified service result was published atomically. A cache-root bug was
  caught immediately: `parents[5]` escaped the workspace to `D:/Data/docs`.
  It is corrected to `parents[4]`, and the verified cache now lives at
  `docs/ai-session-memory/maas-service-cache/761684a245036ed17b583c6cff62552a3c03dc37d3c04d3ce91eb6b99eb00ae4.json`.
  `load_verified_result` confirms the cached 20-card result is valid.

## 2026-07-13 stateful conversational mass revision

- Added `POST /design/maas/revision/` with schema
  `arr.maas.conversational_revision.v1`. It edits the accepted candidate's
  stable component graph and recompiles only that graph; it never regenerates
  the 376-candidate population for a local client/architect instruction.
- Supported bounded mutations are `set_parameter`, `scale_parameter`, and
  removal of an optional leaf. Root edits are forbidden, parameter values are
  clamped, and every attempted revision reruns legal metrics, mass-stage
  parking, component coherence, and architectural-order hard gates.
- A rejected revision returns the previously accepted feature unchanged plus
  the rejected candidate, failures, graph diff, and revision history.
- Deterministic Korean/English intent translation now covers lower/raise,
  widen/narrow, cantilever projection, and courtyard expansion. Explicit graph
  operations remain available for agent-authored edits.
- Real verification used the latest `maas_01`: Korean instruction "상부 매스를
  조금 더 낮춰줘" edited stable node `connector_1_terrace_link`, changing
  `upper_ratio` 0.74 -> 0.6512. Legal, parking, coherence, and architectural
  order all passed; the revision was accepted without population regeneration.
- Reference uploads are currently preserved as provenance with status
  `provided_not_vlm_scored`. Do not claim that image content is already parsed
  into graph mutations: reference-conditioned VLM intent extraction is the
  next separate integration. The existing VLM still scores/reranks generated
  mass images and is not a geometry mutator.
- Regression bundle after implementation: 50/50 passed.

## 2026-07-13 reference-image VLM revision completed

- The earlier provenance-only limitation above is superseded. Added the
  modular adapter `design/maas/interactive/reference_intent.py`.
- When `/design/maas/revision/` receives reference images without explicit
  graph operations, `gpt-5.4-mini` now reads up to three images and returns
  strict structured output: transferable massing principles, one-to-three
  bounded stable-node operations, rationales, confidence, and warnings.
- The VLM is an intent proposer, not an unconstrained geometry writer. Node IDs
  are enumerated from the accepted component graph; only approved parameters
  and operation types are accepted. The deterministic compiler then rebuilds
  the one graph and legal, parking, coherence, and architectural-order hard
  gates accept or reject it. No silent text fallback occurs when a supplied
  reference cannot be interpreted.
- Real non-mock proof used ArchDaily corpus image `archdaily_1028344.jpg` and
  latest `maas_01`. The VLM extracted a lighter horizontal connector principle
  and proposed `connector_1_terrace_link.width_ratio * 0.92`, producing
  0.78 -> 0.7176. The revision was accepted with all four hard gates passing;
  end-to-end latency was 6.55 seconds.
- Local image reads are restricted to approved workspace `docs` and backend
  `media` roots, images are capped at 10 MB, and base64 data is not echoed into
  response history. Explicit graph operations with references remain supported
  and are labeled separately from actual VLM interpretation.
- Updated regression bundle: 51/51 passed.

## 2026-07-13 quantitative reference revision and continual calibration

- A reference edit is no longer accepted merely because law/parking/coherence/
  order pass. `interactive/revision_evaluation.py` renders the unchanged and
  revised mass with the same fixed four views, scores both against the same
  references, and requires: intent confidence >= 0.60, precedent-resonance
  delta >= +0.01, and weighted visible-mass-quality delta >= -0.02.
- Intent and before/after VLM calls are cached by model, graph/geometry,
  instruction, references, and project learning profile. Identical materialized
  geometry intentionally reuses the same score rather than spending again.
- Multi-operation VLM proposals are also tried as independent alternatives
  after a combined proposal fails. Only an alternative that passes structural
  and quantitative improvement gates may replace the accepted graph.
- Added persistent `MaasRevisionEvent` plus migration `design.0002`. Every API
  attempt records graph diff, hard-gate evidence, quantitative deltas, VLM
  provenance, and gate decision. `POST /design/maas/revision/<id>/feedback/`
  records architect/client accepted/rejected/undo and optional 1--5 rating.
- `revision_learning.py` aggregates project-scoped feedback into preferred and
  avoided operation/direction patterns. That soft profile is injected into the
  next reference VLM prompt and included in the intent cache key. It cannot
  override legal or parking hard gates.
- When `job_id` is supplied, site polygon and constraints are loaded from the
  stored `OptimizationJob`, rather than trusting a client copy. Optional
  `design_id` loads the stored accepted mass.
- Real proof on latest `maas_01` with ArchDaily `archdaily_1028344.jpg`: the
  proposed edit improved precedent resonance by +0.06 but reduced weighted
  mass quality by -0.1174. The server therefore rejected it and retained the
  previous feature even though all four structural hard gates passed. A repeat
  used the intent and two visual-score cache hits, took 3.13 seconds, and made
  zero new evaluation VLM calls. This is correct negative evidence, not a
  successful design revision.
- The two independent parameter alternatives materialized to the same visual
  geometry after legal clipping and therefore reused the same cached score.
  Do not count graph-parameter changes without a visual geometry change as
  architectural progress.
- Database migration applied; Django check clean; regression bundle 52/52.

## 2026-07-13 program-conditioned massing and precedent expansion

- Added modular `ARR/backend/design/maas/program_massing/` versioned profiles,
  MassDSL seeds, scoring, benchmark rendering, and research search priors.
- Housing, cafe, gymnasium, office, cultural, and retail now receive different
  intent, floor/volume ranges, preferred families, and seeds. Housing/cafe/gym
  also receive distinct MAP-Elites descriptors and graph-mutation policies.
- RoboGrammar transfer is bounded to valid component-graph expansion, bounded
  depth/node count, and heuristic pruning. The official MIT implementation is
  in `clone/RoboGrammar`; ARR does not claim to run its robot simulator. GLSO
  is a recorded future grammar-valid latent proposal space, not a trained VAE.
- Hard constraint order remains grammar validity -> law -> parking -> clean
  mass -> program fit. Program scoring cannot rescue an illegal mass.
- Fixed the housing seed itself instead of weakening its gate: removing the
  fragmenting post-courtyard lift changed coherence 0.620 -> 0.793 and three
  plan components -> one, with 26 surfaces and four visible volumes.
- Same-site six-seed benchmark passes: overall mean program fit 0.9813;
  housing 0.944, cafe 1.0, gymnasium 1.0; three distinct fingerprints. Review
  `docs/playwright/design-route-live-verify/maas-program-massing-benchmark-latest.png`
  and its matching JSON. This seed benchmark alone is not competition-grade
  proof for every final selected candidate.
- Added 36 cafe/restaurant and 36 sports-architecture ArchDaily precedents.
  Rebuilt the stale DB index to 12 collection manifests, 274 unique references,
  and 338 images. New crawls now refresh `archdaily/DB_MANIFEST.json`. Keep the
  corpus as internal precedent/VLM evidence with provenance, not redistribution.
- Verification: program/preference 30/30 passed; program + selection +
  evolution + preference + cache 51/51 passed. An unsliced full export suite
  was stopped after one minute with no output; do not record it as pass/fail.

## 2026-07-13 program visual correction loop (supersedes seed-only benchmark)

- Direct human review rejected the first program PNG: program labels differed,
  but all uses still passed through the same generic family box decomposer.
- Added versioned `program_massing/data/component_assemblies.v1.json`. Program
  components, normalized bounds, height bands, families, and mutation limits
  live in data, not Python coordinate conditionals or per-site metre values.
- The source compiler now materializes role-bearing assemblies for program
  seeds: housing living bars/court/core or bridge; cafe public room/service/
  threshold/terrace/roof; gym main long-span hall/service spine/entry canopy/
  daylight monitor. All remain clipped to the supplied legal footprint.
- Added geometry-based `program_spatial_evidence`: required role coverage,
  dominant component ratio, site coverage, height/section hierarchy, and source
  coherence. Program fit can no longer pass from family/floor counters alone.
- Added a deterministic bounded generate-evaluate-select loop. Current proof
  evaluates 312 geometry candidates (three uses, two grammars, four generations,
  twelve offspring plus parent), rejects 69 failed candidates, and retains six
  elites. It does not force a mutated child when the parent remains better.
- Latest artifact paths remain
  `maas-program-massing-benchmark-latest.{json,png}`. Latest result: pass,
  mean program fit 0.9922, minimum architectural spatial score 0.975, all six
  hard pass. Benchmark now fails if it evaluates fewer than 300, rejects zero,
  or any elite architectural score is below 0.88.
- Fixed alpha flattening in the review sheet; transparent previews no longer
  render against black. Direct review finds materially clearer use separation
  than the rejected first sheet, but this mass diagram is not a claim of a
  finished facade/competition presentation.
- Regression after integration: 52/52 passed; `git diff --check` passed.

## 2026-07-13 housing 20-mass archive development

- Expanded housing from two to six data-defined component topologies: open
  court bars, shifted parallel bars, terraced cluster, gateway court, podium
  twins, and diagonal court. Normalized rotations are supported and clipped to
  the legal footprint; rotation and coordinate mutation ranges remain in JSON.
- Added diversity-archive selection. It de-duplicates materialized geometry,
  preserves at least one hard-pass representative of every topology, caps each
  topology, and fills the remaining slots using architectural quality plus
  descriptor distance (dominant ratio, coverage, height levels, surfaces).
- Latest proof searched 510 source geometries, rejected 59, and selected 20
  hard-pass housing masses across all six topologies. Mean spatial architectural
  score 0.976, minimum 0.917. Evidence:
  `docs/playwright/design-route-live-verify/maas-housing-20-program-archive-latest.{json,png}`.
- This is not a disconnected demo: `program_archive_sequences()` now supplies
  exactly 20 program sequences to `generate_grammar_variants()` before generic
  agent/library candidates. Direct probe produced 129 total grammar variants,
  20 program variants, and coverage of all six housing topologies.
- Direct PNG review finds a material improvement over the earlier fragmented
  20-sheet: clear courts, gateways, staggered bars, podium/twin masses, and one
  diagonal family. Variants inside a topology remain related by design, but no
  single topology may erase the others solely through a higher proxy score.
- Regression after service-pool integration: 54/54 passed. `git diff --check`
  passed apart from a Windows LF/CRLF advisory on `legal_interpreter.py`.

## 2026-07-13 creative primitive and 10-topology correction

- Direct review correctly found the six-topology sheet still converged toward
  wide low masses plus upper boxes. The underlying limitation was the assembly
  compiler's axis-aligned rectangular bounds, not a lack of scoring weights.
- `component_assemblies.v1.json` and its compiler now support normalized
  arbitrary polygon plates, bounded vertex mutation, and rotation in addition
  to rectangles. These remain data-defined, footprint-relative, and clipped;
  they are not per-site Python coordinates.
- Housing now has ten hard-pass topologies: court bar, shifted bar, terraced
  cluster, gateway court, podium twins, diagonal court, sky-bridge court,
  pinwheel court, polygonal cantilever stack, and polygonal zigzag terraces.
- Archive selection is constrained to exactly two elites per topology for the
  20-sheet. Latest loop evaluated 850, rejected 111 (including one initially
  selected spatial-score failure), and retained 20. Ten of ten topologies are
  present; mean architectural spatial score 0.9687, minimum 0.914.
- Latest evidence overwrites
  `maas-housing-20-program-archive-latest.{json,png}`. Direct review confirms
  materially wider plan/section language: pinwheel, elevated bridge,
  cantilever, diagonal, and zigzag plates coexist with necessary clean anchors.
- Real service-pool probe: 129 grammar variants, exactly 20 program variants,
  exactly ten program topologies, two each. Regression remains 54/54; diff
  check passed with only the existing LF/CRLF advisory.
- Do not claim surface/section development is finished: the new polygonal
  source volumes are richer, but facade systems, curved shells, ramps, and
  structural span validation remain later layers.

## 2026-07-13 reference-led creative pre-legal archive and card board

- User references `docs/images.jpg` and `docs/images (1).jpg` exposed the next
  gap: flowing ribbon-campus plates and interlocking voxel terraces cannot be
  learned by scoring axis-aligned housing boxes harder.
- The intended stage order is now explicit: creative source exploration ->
  clean/coherence filter -> program adaptation -> legal/parking projection.
  This does not weaken production law/parking gates; the creative board labels
  them `source archive; legal/parking not run` rather than claiming a pass.
- Assembly data/compiler now support normalized buffered path primitives with
  mutable control vertices and width, in addition to polygons/rotated boxes.
  Added ribbon-campus and voxel-cascade languages. The reference images are
  principle sources only; geometry is not copied.
- Latest creative-source loop evaluated 1,020 candidates, rejected 112, and
  retained 20 across 12 topology/language families. Mean spatial score 0.9741,
  minimum 0.929. A curved path is currently extruded as a mass volume; this is
  not yet a continuous anticlastic roof-shell implementation.
- Restored the requested review format using the existing browserless 20-card
  renderer: single isometric, site boundary, mass language, source surfaces,
  BCR, and explicit pending law/parking status. Evidence:
  `docs/playwright/design-route-live-verify/maas-creative-20-card-latest.json`
  and `maas-creative-20-card-latest.png`; four-view companion is
  `maas-creative-20-four-view-latest.png`.
- Regression remains 54/54. The current topology records still reuse housing-
  prefixed role names internally; do not interpret that naming as a requirement
  that creative exploration remain housing-only. A future cleanup should move
  reusable creative languages into their own neutral profile before program
  adaptation.

## 2026-07-13 fresh full-flow PNG audit

- Ran a fresh synchronous end-to-end generation for PNU
  `1168011800104170004`: boundary, legal constraints, 120 LLM MassDSL
  candidates, compilation, legal/parking/evolution/exact projection, final VLM
  completion, HTML and PNG. API generation took 318.010 seconds; total render
  command took 373.4 seconds. This confirms full refresh must remain an async or
  precomputed job, while conversational single-graph revision stays interactive.
- Fresh JSON verifier, parking verifier, and PNG verifier all pass. Key result:
  exact projection optimal; 20/20 legal, parking mass-stage, graph/coherence,
  architecture-grade, and final VLM; 120 raw/compiled LLM sequences; 18 unique
  families; 16 mass languages; max visible volumes 4; no small fragments.
- Generated the ordinary evidence PNG at
  `docs/playwright/design-route-live-verify/maas-20-alt-latest.png` and a new
  uncluttered four-view sheet at
  `docs/playwright/design-route-live-verify/maas-20-alt-clean-mass-latest.png`.
- Direct visual review still rejects the claim that all 20 are competition
  grade. `maas_10`, `maas_13`, `maas_15`, and `maas_17` read as over-crossed or
  bridge-fragment compositions; several other cards are too low/flat. The
  selector admits VLM preference scores as low as 0.534--0.561 for diversity
  coverage, while some visually questionable candidates retain high order
  proxy scores. JSON pass is therefore not final visual acceptance.
- Next correction must add a final-sheet visual quality floor and/or replace
  low-preference diversity-fill cards from the clean legal pool without
  weakening family/language diversity, law, parking, or exact-selection
  constraints. The clean four-view contact sheet should be the human audit
  artifact for this correction.

## 2026-07-13 program-neutral creative-first pipeline correction

- The prior board was labelled creative but its archive selection still used
  housing program-fit and housing role coverage. That mismatch is now removed.
- The operational order is now: program-neutral creative archive -> optional
  building-use projection -> legal/parking hard projection -> final selection
  and VLM rerank. `generate_grammar_variants()` inserts the 20 creative source
  candidates first, then the requested use-specific seeds, then the generic
  proposal/library pool.
- Added `creative.py` with neutral `creative_*` sequences and independent form
  evidence. Its hard gate measures volume count 2..5, effective surface count
  <=48, small fragments <=1, plan components <=3, hierarchy, dominance,
  coverage, and source coherence. It does not score housing roles, target
  floors, law, or parking.
- Reusable assembly roles are neutralized at compile time (`creative_*`); the
  underlying versioned component data is reused rather than duplicated.
- Buffered ribbon paths retain their raw tessellated surface count (64 in the
  baseline) but use a separately reported logical/effective surface count for
  the clean-mass gate. This prevents curve tessellation from being mistaken for
  fragmented massing while keeping raw complexity auditable.
- Latest independent search: 1,020 evaluated, 20 selected, 12 topology
  languages, mean creative score 0.962, minimum 0.878, no benchmark failures.
  Live cafe grammar-pool probe: 131 total, first 20 creative candidates across
  all 12 topologies, then two cafe-specific program seeds.
- Latest evidence was regenerated at
  `docs/playwright/design-route-live-verify/maas-creative-20-card-latest.{json,png}`.
  Law and parking remain explicitly unrun on this source archive.
- Direct PNG audit remains honest: this is materially broader and no longer
  housing-conditioned, but many candidates are still rectilinear. The ribbon
  primitive is a buffered-path extrusion, not a continuously warped roof shell;
  do not call the whole sheet competition-grade yet.
- Regression: 56/56 selected MAAS tests pass. `git diff --check` reports no
  whitespace errors; the dirty worktree and CRLF advisories were preserved.

## 2026-07-13 closed-loop reference-to-geometry correction

- The missing link was confirmed: `SourceSurface` already existed, but ribbon
  assemblies were flattened to constant-height `SourceVolume` boxes and both
  VLM preview and the card renderer read only `mass_volumes`. Reference agents
  therefore could not reward the geometry they were supposed to inspect.
- Path assemblies now author explicit 3D profiled roof strips, bank facades,
  and end caps from centerline, width, and per-control-point roof heights.
  Feature payloads carry `source_surfaces` plus world vertices; VLM preview and
  the 20-card renderer draw these surfaces and suppress the duplicate flat
  ribbon box.
- The voxel/cascade language now has five connected interlocking volumes. The
  coherence gate was corrected from `<=4` to `<=5`, matching the clean-mass
  contract (`visible_volume_count > 5` is still rejected). Five-block clusters
  are not treated as fragmentation when connected and small-fragment-free.
- Added eight non-LEGO language families: bridge canyon, ring stack, fan
  plates, arc court, cluster village, folded spine, cross cantilever, and
  terrace bowl. The creative archive now has 20 distinct topology names, so
  the 20-card board no longer fills slots by duplicating 12 families.
- Latest loop evaluated 1,700 candidates and selected 20 distinct languages;
  creative mean/minimum were 0.9553/0.891, benchmark status pass. The board
  is regenerated at `docs/playwright/design-route-live-verify/maas-creative-20-card-latest.{json,png}`.
- Direct review shows actual profiled ribbons and interlocking voxel/cantilever
  forms, but some anchors remain rectilinear. This is not a claim of universal
  competition-grade design or continuous shell topology yet; the loop now has
  the geometry evidence needed to continue improving rather than scoring flat
  proxy boxes.
- Regression after the change: 58/58 selected MAAS tests pass.

## 2026-07-13 final code/PNG audit

- Re-audited the regenerated JSON and PNG: 20/20 features, 20 unique mass
  shapes, all `hard_pass=true`, volume counts 3..5, fragments 0, and no
  effective surface gate breach. The board visibly includes profiled arc/ribbon
  roofs, folded spine, bridge canyon, ring stack, voxel cascade, fan plates,
  cluster village, and cantilever families.
- Found and fixed a real service-path issue: legal candidates can carry only
  local `vertices_m` in `MorphologyVariant.source_surfaces`, while the new
  renderer initially expected benchmark-only `vertices_world_m`. Both the card
  renderer and VLM preview now derive world vertices from feature centroid and
  height as a fallback. Direct fallback preview was verified with a ribbon.
- Correct PNG rerender reports 20 cards at 2200x1400. Full selected MAAS suite
  remains 58/58; whitespace check has no errors beyond existing CRLF notices.

## 2026-07-13 stale legal-artifact audit

- User-provided `maas-20-alt-latest.png` is the older 12:45 legal artifact,
  generated before the 20-language creative archive and profiled surface
  renderer. Its JSON has no `creative_mass_evidence`; do not compare it as the
  current creative board.
- Fixed a real final-path consistency bug: the architectural order policy
  allowed five visible volumes but `selection/preference_guards.py` still
  counted `len(volumes)-4` as fragmentation. The guard now rejects only more
  than five and its contract test is updated. Targeted tests pass 52/52.
- Reference images remain examples of desired breadth, not templates to clone.

## 2026-07-13 profiled surfaces, 20-language archive, and language brain

- Root cause found: `SourceSurface` supported arbitrary 3D vertices, but path
  assemblies emitted constant-height `SourceVolume` boxes and both the card
  renderer and VLM preview ignored source surfaces. VLM therefore could not see
  the intended roof geometry.
- Ribbon/path components now carry authored roof profiles. The compiler builds
  explicit left/right banks, profiled roof strips, side quads, and end quads.
  Search features attach world-space surface vertices; the 5x4 card renderer
  and four-view VLM preview render these surfaces and suppress the flat ribbon
  proxy volume.
- The LEGO precedent is one bounded family, not the generator default. Voxel
  cascade now uses five connected/interlocking volumes and distinct terrace
  levels. Coherence now follows the stated clean-mass gate `volume_count <= 5`
  rather than the erroneous old global limit of four.
- Creative data now contains 20 distinct topology/language seeds. Added arc
  court, folded spine, bridge canyon, fan plates, ring stack, cluster village,
  cross cantilever, and terrace bowl. Archive selection is required to retain
  all 20, so no topology is duplicated merely to fill the board.
- Latest loop evaluated 1,700 geometries, rejected 114, selected 20/20 distinct
  languages, mean creative score 0.9633, minimum 0.934. Latest evidence remains
  `docs/playwright/design-route-live-verify/maas-creative-20-card-latest.{json,png}`.
- Added `interactive/language_brain.py`. It maps transferable reference
  principles to a program-neutral topology replacement, exposes alternatives
  and matched signals, and penalizes previously used topology names. Flowing
  roof intent can replace a court graph with ribbon campus; the next similar
  revision moves to arc court rather than repeating ribbon. LEGO intent is
  bounded to voxel/cluster choices, not propagated to the whole archive.
- `apply_conversational_graph_revision()` now performs this topology mutation
  before compilation when reference VLM evidence is strong. The resulting
  geometry is accepted only if the existing coherence, law, parking,
  architectural-order, and VLM before/after improvement gates pass; otherwise
  the previously accepted graph remains.
- This is the requested first architecture-agent brain layer: reference VLM ->
  transferable principle -> topology/graph mutation -> geometry -> critics ->
  persistent revision history. It is not a claim that a fine-tuned foundation
  model or unrestricted graph synthesis has been trained.
- Regression: 58/58 selected MAAS tests pass; `git diff --check` has no
  whitespace errors beyond preserved CRLF advisories.

## 2026-07-13 formal-graph generator correction

This supersedes the earlier "20 distinct topology/language seeds" claim.

- Direct code audit found that `creative_seed_sequences()` copied
  `program_seed_sequences("housing")`, renamed `program_housing_*` to
  `creative_*`, then mutated fixed component coordinates. Twenty names were not
  evidence of twenty architectural languages and caused the repeated box/LEGO
  appearance.
- Creative seeds now come from the program-neutral MassDSL operation library:
  courtyard/cave/notch, split/bridge, bend/branch/interlock, terrace/shift,
  folded-roof and section graphs. Housing component assemblies are no longer
  the default creative population.
- Search mutation edits bounded numeric parameters on every operation call,
  instead of injecting only `component_*` coordinates into the last call.
- Archive distance now includes plan symmetric difference, compactness, aspect,
  height bands and volume count. The benchmark reports
  `geometric_language_count`; renamed labels alone cannot pass diversity.
- Latest full loop evaluated 1,700, rejected 717 and selected 20: 13 formal
  graph families, 16 measured geometry-language clusters, mean score 0.881,
  minimum 0.753. Evidence is
  `docs/playwright/design-route-live-verify/maas-creative-20-card-latest.{json,png}`.
- Stable conversational language names now bind to formal MassDSL graphs rather
  than old component templates. Reference mutation regression passes 2/2.
- Honest visual verdict: bend/branch/bridge/courtyard candidates are materially
  more distinct, but many later cards remain podium/stack-like. This is not yet
  competition-grade. Next target is a global organizing-rule evaluator
  (continuous circulation/roof field, void hierarchy, sectional continuity),
  followed by validated VLM-proposed topology—not more named templates.

## 2026-07-13 single-view box-bias correction

- The four-view VLM contact sheet was incorrectly reused as the primary human
  20-up board. That made comparison with the older single-isometric artifact
  confusing. Human review now uses a 5x4, one-isometric-view-per-candidate PNG;
  VLM evaluation still retains isometric/opposite/front/top evidence.
- The comparable board exposes the remaining failure clearly: only 4/20
  candidates belong to strict authored sculptural families; 16/20 remain
  rectilinear extrusion/stack candidates.
- A first vertex-count metric falsely reported 16 sculptural candidates because
  clipped rectangles acquire extra vertices. It was immediately removed.
  `sculptural_geometry` now requires bend/branch/folded/terrace family geometry
  or explicit profiled surfaces.
- The creative benchmark now intentionally FAILS with
  `sculptural_geometry_count_below_8_box_bias` (4 sculptural, 16 rectilinear).
  Do not weaken this gate or claim the mass generator is complete.
- Root cause is below selection: many named operations in `source_geometry/compiler.py`
  reduce to `_rect_piece` plus vertical extrusion. Next work must add real
  continuous-ribbon, folded-surface, carved-monolith and non-box interlock
  primitives, then make at least 8/20 survive the existing clean-mass gate.

## 2026-07-13 old-vs-creative direct visual correction

- Direct comparison of the user's
  `docs/maas-20-alt-latest - 복사본 (6).png` against
  `docs/maas-creative-20-card-latest.png` showed the old legal board is
  architecturally better. It preserves recognizable terrace-ribbon, bend,
  sloped-roof, pinched-waist, branch, void and diagonal-connector wholes. The
  creative board decomposed most candidates into arbitrary rectangular pieces.
- Therefore the experimental creative archive is quarantined from the live
  `generate_grammar_variants()` path by default. It only enters when
  `MAAS_ENABLE_EXPERIMENTAL_CREATIVE_ARCHIVE=1`. Agent proposals and the proven
  data-backed grammar sweeps now precede program component seeds.
- Backend was restarted and the real PNU legal flow was regenerated with no GPT
  or preference-VLM calls. New evidence is
  `docs/playwright/design-route-live-verify/maas-20-alt-latest.{json,png}`;
  20 candidates returned in 235,367 ms.
- Visual recovery succeeded: ribbon, roof, bend, pinched waist, split bridge,
  diagonal connector, cluster and embedded void are present again. Remaining
  failures are explicit near-duplicate pairs 1/3, 5/10, 8/16, 11/15 and 18/19,
  plus underscaled candidate 14. Do not call this complete.
- Quarantine regression passes 1/1. The experimental graph composer remains a
  research path until its own strict box-bias benchmark passes visually.
- Verification nuance: the recovered real-PNU run deliberately used
  `MAAS_LLM_LOOP_REQUIRED=0` and no preference VLM to avoid model cost. PNG
  verification and parking mass-stage verification pass. The strict full JSON
  verifier fails only its expected LLM/VLM completion/evidence requirements;
  do not label this no-model artifact as a completed VLM run.

## 2026-07-13 polygon-quality gate and honest representation limit

- The system is not "paper-complete" and the current output is not the limit.
  A clean polygon gate is necessary geometry hygiene, not the fundamental
  competition-grade generator.
- Added `source_geometry/polygon_quality.py` and integrated it into compiler
  cleanup and coherence v2. Evidence is scale-independent and records validity,
  exterior vertex count, holes, minimum edge ratio, short-edge count, minimum
  rotated width ratio, and compactness.
- Invalid/self-intersecting plans are repaired conservatively; topology-
  preserving simplification removes clipping debris only when it retains at
  least 97% of area. Hairline slivers, repeated short-edge/spike debris, invalid
  plans, and plans with more than 96 exterior vertices now fail source
  coherence rather than reaching the selector as acceptable masses.
- Polygon/selection/preference/evolution regression is 49/49. A separate
  broader command including the expensive program archive benchmark exceeded
  four minutes and did not produce a final result; do not report that broader
  suite as passed for this patch.
- Fundamental next layer: replace `_rect_piece + extrusion` as the dominant
  representation with graph-native continuous primitives: centerline/width/
  height fields for ribbons, curved or folded roof fields, carved-monolith
  solid/void operators, and explicit connection/section continuity. VLM must
  evaluate rendered multi-view geometry and return typed failure signals to
  those generator parameters. Reranking boxes cannot create this geometry.
- Preserve the stronger recovered legal baseline while this research generator
  remains behind its red box-bias benchmark. Never claim polygon cleanliness is
  equivalent to architectural quality or continuous shell generation.

## 2026-07-13 graph-native continuous surface implementation

- Implemented the first fundamental representation change rather than another
  selector weight. Formal MassDSL graphs now materialize explicit non-flat 3D
  roof and facade surfaces for `folded_section`, `terraced_ribbon_section`,
  `torqued_stack`, and the new `continuous_ribbon_field` principle.
- Corrected the semantic collapse `bend -> torqued_stack`. Bend graphs now map
  to `continuous_ribbon_field`: three connected, footprint-relative buffered
  centerline ribbons with coupled longitudinal/transverse height fields. The
  coordinates are normalized formal rules, not parcel-specific templates.
- The conservative `SourceVolume` proxy remains the FAR/BCR/legal solid, while
  `SourceSurface` is the authored review/VLM envelope. Flat proxy roofs for
  profiled roles are suppressed by the existing VLM renderer, so it now sees
  the actual varying-height field.
- Added `continuous_surface_evidence` to the source signature. Raw tessellated
  `surface_count` is preserved, while `effective_surface_count` records logical
  complexity for profiled surfaces. Legal order gates now use the effective
  count; they no longer force correct meshes to delete facade faces.
- Direct 109-variant grammar probe: 33 candidates materialize profiled formal
  surfaces across four principles. Maximum raw surface count is 49, maximum
  effective count is 18, and none exceed the legal order limit of 36.
- Targeted polygon/selection/preference/evolution regression is 51/51. Two
  isolated legacy export tests still fail their pre-existing
  `inference_source == family_priority` assertion for four non-bend cases; do
  not attribute those failures to the new surface geometry or claim the entire
  repository suite passes.
- Visual probes are
  `docs/playwright/design-route-live-verify/continuous-surface-probe/`.
  The change produces connected non-flat ribbons and folded fields, but they
  remain piecewise-linear early-massing surfaces, not smooth NURBS/subdivision
  shells, structural form-finding, or a claim of universal competition grade.

## 2026-07-13 six-board visual loop and paper-critical VLM correction

- Ran six successive 20-mass creative boards and directly inspected every PNG;
  do not use numeric pass alone as acceptance. Artifacts are
  `maas-creative-20-continuous-latest.png` and `v2` through `v6` beside it.
- Board 1 exposed label-driven prefill and repeated interlock/terrace forms.
  Board 2 used geometry-distance greedy selection: 20 measured languages and
  zero near-duplicate pairs, but only 7/20 sculptural, so it failed.
- Boards 3--5 added an explicit sculptural quota and reached 8 then 12/20, but
  direct PNG review rejected them: several cross-compositions were only named
  sculptural, and repeated bend/terrace fields still dominated.
- Removed family-name sculptural scoring. A candidate now counts only when
  actual `continuous_surface_evidence.hard_pass` and a profiled roof exist for
  continuous-ribbon, folded-section, or terraced-ribbon principles.
- Added a formal-principle cap of four. Board 6 then selected 20, 17 topology
  labels, 20 measured geometry clusters, zero near-duplicate pairs, but only
  8/20 real profiled sculptural candidates. Benchmark correctly fails
  `sculptural_geometry_count_below_12_competition_target`. Direct PNG review
  agrees: the generator pool, not only the selector, lacks enough distinct
  continuous/formal geometry operators.
- Paper/code audit found the CAD-Assistant-style observe/critic/revise loop was
  present but its VLM vocabulary could not say `too_box_like`,
  `weak_form_continuity`, `needs_profiled_surface`, or `needs_carved_void`.
  These typed actions are now in the VLM schema and compile to bounded MassDSL
  topology mutations: continuous ribbon field, folded field, or carved atrium,
  followed by the existing legal/parking/review revalidation.
- The mutation parameters inherit parent numeric intent where possible and vary
  by critic generation; they are not parcel-specific coordinates. Regression
  proving `too_box_like -> bend -> continuous_ribbon_field` and the wider
  polygon/selection/preference/evolution set passes 52/52.
- Remaining fundamental task: add more independent graph-native formal
  operators (smooth loft/subdivision ribbon, carved shell/atrium surface,
  cantilever/fan field, bridge/canyon continuity) and let actual VLM actions
  populate/evaluate those cells. More quotas cannot manufacture missing design
  languages. Keep board 6 red until at least 12/20 actual profiled principles
  pass direct PNG review, not only the counter.

## 2026-07-13 site-aware agent flow and boards v7-v9

- Full runtime audit found the documented multi-agent flow overstated runtime
  ownership: `DesignOrchestratorAgent` routes/reviews only, and the live OpenAI
  population was called directly from `legal_mesh_optimizer.py`. The live call
  now goes through `LLMArchitectAgent.propose_population`; its artifact records
  `owning_agent=llm_architect_agent` and the site-geometry status. The broader
  orchestrator is still not a stateful bidirectional execution engine.
- The LLM previously received only area, use, FAR/BCR and height. It now receives
  `site_geometry_intelligence`: dominant world axis, oriented aspect/size,
  compactness, convexity/concavity, boundary vertices, access context and typed
  design directives. The source compiler uses the same dominant-axis local
  frame and restores volumes/surfaces to world coordinates.
- Added a clean-silhouette hard gate using exterior-only normalized perimeter
  compactness. This rejects connected starburst/interlock debris while retaining
  courtyards; novelty selection can no longer rescue those candidates merely
  because they are different.
- Folded-section seeds were silently absent because their formal compiler filled
  100% of the parcel and failed coverage. Folded bases/roof planes are now
  authored inside an inset plinth. This restored a third true non-flat family.
- Board v7: 20 geometry languages and zero duplicates, but 8/20 actual profiled
  geometry; direct PNG rejected fragmentary cards 4/5/9/10.
- Board v8: silhouette gate removed the worst starbursts, but still 8/20 and
  visually weak branch/podium cards; direct PNG rejected completion.
- Board v9: benchmark passes with 20/20 selected, 14 topology labels, 20 measured
  geometry languages, 12/20 real profiled candidates, 0 near duplicates. Direct
  PNG is materially cleaner, but repeated folded/ribbon families and weak cards
  6/12 mean this is not a claim of universal competition-grade design.
- Multi-site evidence `maas-site-adaptation-v2.{json,png}` compiles four languages
  across rotated-long, trapezoid and concave-L parcels: 12/12 compile, all source
  volumes inside the parcel, and distinct site-frame angles 29, 5.553 and 0
  degrees. This proves geometry-frame adaptation, not full road/context-aware
  architectural reasoning.
- Paper verdict after reading EvoMass and CAADRIA 2024 primary sources: topology,
  population search, graph-native formal surfaces and critic-to-geometry revision
  are partial matches. A general second-phase Volume-Based/Boundary-Based formal
  variation optimizer, real daylight/solar simulation, and a stateful multi-agent
  negotiation loop are still missing. VLM remains critic/reranker plus typed
  mutation trigger, not a learned geometry generator.

## 2026-07-13 capacity/program split and PNG-corrected program loop

- Root live-ALT bug: `legal_mesh_optimizer.py` used `_research_review_floors`
  to collapse agent/LLM candidates to 2--4 floor maquettes, while the selector
  could omit `legal_layered_max`. Capacity alternatives therefore displayed
  low-FAR fragments even when the legal envelope supported a full mass.
- Live projection now chooses the highest legal floor count under FAR/height,
  pins the legal anchor, and rejects under-capacity candidates before expensive
  3D/graph/parking/VLM work. This is a pipeline correction, not per-card XYZ
  hardcoding.
- FAR utilization is brief-dependent, never a global 70% rule. Small
  neighborhood-living/residential/commercial feasibility defaults to
  `capacity-first` (0.70); gymnasium/museum/cultural/civic programs default to
  `design-led` (0.20). Explicit `capacity-first`, `balanced`, `design-led`, or
  `min_far_utilization` in `massing_brief` overrides the default.
- Default visual benchmark is now neighborhood living + gymnasium, not housing.
  Artifact v1 exposed generic box masses. Compiler audit found the gym's
  `main_long_span_hall` role was excluded from `folded_section` surfaces, so the
  semantic roof label rendered as a flat box. It now materializes a six-vertex
  ridge and varying-height roof/facades.
- PNG v3 deliberately tested a continuous neighborhood street ribbon. Numeric
  fit was 0.971, but direct visual review rejected it as tangled/over-composed.
  The seed was removed and program search now hard-rejects more than 4 volumes
  or 28 raw source surfaces. Do not restore the ribbon because its score passed.
- Current accepted artifact is
  `docs/playwright/design-route-live-verify/maas-program-neighborhood-gym-v4.png`
  with JSON beside it: 5 program elites, mean fit 0.972/0.980, max 23 surfaces,
  max 3 volumes. It is cleaner and the gym roof is genuinely non-flat, but the
  neighborhood masses remain early typology studies, not BIG/OMA competition
  grade. Keep that distinction explicit.
- Targeted regression after the correction: 43/43 program/polygon/selection/
  evolution tests, plus 17/17 capacity-policy/selection tests. Full repository
  suite was not run.
# 2026-07-13 site-conditioned graph loop (IN PROGRESS, not solved)

- User correctly rejected a patch that merely replaced one fixed ribbon coordinate template with another. Do not restore fixed `minx + width * ratio` path arrays and do not call them agent design.
- Current target flow: `site geometry intelligence -> editable mass graph/design field -> compiler -> legal/parking projection -> multi-view PNG/VLM -> explicit graph edit -> recompile`.
- New research material is local:
  - `clone/shapecraft` at commit `2a09177` (official NeurIPS 2025 code).
  - `clone/papers-2026/Proc3D_2601.12234.pdf` and extracted `.txt`.
  - `clone/papers-2026/3D-Layout-R1_2603.22279.pdf` and extracted `.txt`.
  - `clone/papers-2026/WACV2025_3D_Synthesis_Architectural_Design.pdf` and extracted `.txt`.
- Important transferable mechanisms:
  - ShapeCraft: component DAG + bounding-volume generation, multiple rendered sampling paths, VLM evaluation, best verified iteration.
  - Proc3D: compact editable graph; localized node-parameter edits instead of regenerating an opaque mesh.
  - 3D-Layout-R1: explicit intermediate scene-graph edits with format/IoU/collision rewards; direct final-coordinate prediction is weaker.
- `source_geometry/design_fields.py` now maps graph-authored parameters to actual parcel cross-sections. It must remain coordinate-template-free. This is currently under test.
- `continuous_ribbon_field` now consumes that site design field. It is not accepted until tests pass and a newly rendered PNG is directly inspected.
- The first test after the rejected ribbon-template patch failed `sculptural_geometry_count_below_12_competition_target`; never hide or relabel that failure.
- Parking performance root cause found: small-lot exact grid selection allowed 90C5 exhaustive combinations. It is now capped at 5,000 combinations and falls through to bounded selection; measured request time fell from about 46 seconds to about 1 second.
- Neo4j being off was not the cause of the visual failure. Graph DB is the law/relationship authority; request-time deterministic rules may use a versioned local snapshot.
- `legal_mesh_optimizer.py` is still far too large (~6.8k lines). Capacity, candidate-pool, trace and parking budget were extracted, but candidate generation, parking projection, and preference/final selection still need large stage extraction. Do not claim refactoring is complete.
## 2026-07-13 Mass-Brain integration audit (useful memory, unsafe generator as-is)

The independent service at `D:/Data/Mass-Brain` was read through its complete
`docs/memory` handoff and its ARR bridge/recombination implementation.  It is a
useful long-term append-only store for graph lineage, compile/legal/parking/VLM
outcomes, and explicit architect feedback.  It does **not** currently solve the
neighborhood-living 20-mass visual problem and must remain shadow-only.

Concrete blockers found in code:

- Its 774-feature bootstrap contains zero historical executable
  `componentGraph` records; precedent images/metrics can be retrieved but cannot
  yet be recombined into executable architectural languages.
- `src/recombine.ts` splices structurally distant nodes by chaining them to the
  last node without spatial/program compatibility, which can recreate the LEGO
  fragment failure.
- Numeric jitter clamps every numeric parameter to `12`; valid architectural
  angles above 12 degrees are therefore silently destroyed.
- `src/llm-assistant.ts` rejects any assistant edit whose role/verb signature
  changes, so it can tune parameters but cannot author a new topology.
- Learned reward is verb-signature based and is not yet conditioned on parcel,
  access, program, scale, or building type.
- ARR `_unique_sequences()` deduplicates only the verb sequence, losing distinct
  parameterizations before Mass-Brain ingestion.

Recommended use/order:

1. Finish the ARR neighborhood-living 20-language graph/render/gate loop first.
2. Store typed graph mutations and their context/outcomes in Mass-Brain.
3. Add context-aware compatibility and parameter schemas before recombination.
4. Run a fixed blind baseline-vs-brain PNG benchmark; do not promote based only
   on counters, VLM scores, or the existing shadow promotion statistics.

Do not describe Mass-Brain as a creativity model or as proof of aesthetic
improvement.  Neo4j is unrelated to this visual bottleneck; SQLite/GRL memory is
also not a substitute for a geometry-producing graph mutation loop.
## 2026-07-13 neighborhood 20-language loop v1/v2 (NUMERIC PASS, VISUAL REJECT)

Artifacts:

- `docs/playwright/design-route-live-verify/maas-neighborhood-20-v1.png/.json`
- `docs/playwright/design-route-live-verify/maas-neighborhood-20-v2.png/.json`

Both runs selected 20 candidates with 14 topology labels, 6 formal principles,
raw surface count <= 28, volume count <= 4, grounded program roles, and no
duplicates under the then-current numeric threshold.  Neither run is accepted.

Direct PNG verdict:

- most candidates still share a low full-site podium plus one small upper box;
- nominal terrace/fold/step principles compile to the same visual language;
- the two curved/bent candidates read as clipped objects, not convincing usable
  neighborhood-living architecture;
- v2's height-integrated 3D distance improved selection ordering but could not
  create diversity absent from the candidate pool.

Root-cause update: selector repair alone is exhausted.  The language-author
stage must produce topology-changing typed graph mutations from site/program,
reference/book memory, and VLM critic evidence.  The current four program seeds
plus parameter-only mutation cannot reach the objective.  Do not lower visual
thresholds or add more coordinate templates to fill 20 cards.

## 2026-07-13 real author + VLM A2A v4-v6 (TECHNICAL PASS, VISUAL FAIL)

Artifacts:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v4.png/.json`
- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v5.png/.json`
- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v6.png/.json`
- reusable author response: `maas-neighborhood-author-v4-cache.json`

What is now real:

- `program_massing/vlm_a2a.py` calls `LLMArchitectAgent.propose_population()`
  before local search. gpt-5.4-mini authored 27 executable MassDSL graphs.
- The correct 274-item reference corpus is matched and every shortlist image is
  scored by the real VLM. Typed graph edits are compiled and re-rendered.
- A normalized capacity gate now computes occupied union area per level rather
  than rewarding a visual label. Neighborhood living uses the program/site
  capacity policy before VLM selection.
- The Korean capacity aliases in `capacity_policy.py` were repaired; the prior
  mojibake silently selected the generic policy.

Critical findings:

- v4 took 772 seconds because one author batch failed and sub-batch recovery
  ran. It produced 27 graphs (5 timeout coverage repairs), 2,904 evaluated
  variants, 615 clean variants, and 20 final cards. Direct PNG: visual reject.
- Authoring was not the bottleneck: zero authored sequences were schema-rejected
  and verbs included bend/split/courtyard/interlock/overlap. The compiler and
  gates collapsed this variety.
- The raw-surface 28 gate systematically rejected profiled ribbons: one bend
  had 38 raw surfaces but only 24 effective surfaces and four legal solids.
  The corrected contract is raw <= 48, effective <= 28, volumes <= 4.
- v5 admitted continuous geometry but also admitted tangled torqued examples.
  Worse, a VLM 0.3667 candidate survived because the final selector still used
  the old program-only `ProgramElite.score`.
- v6 uses a 24-item VLM shortlist, a 0.55 automatic VLM floor, dual-objective
  rescoring, and a normalized FAR floor. Counts: clean pool 782, capacity pool
  587, VLM parents 24, VLM children 17, visual-floor pool 19, selected 20.
  Correct status is `automatic_visual_floor_failed`; do not call it solved.
- v6 is cleaner than v5 and removes the worst low-VLM torqued cards, but direct
  review still sees excessive plinth/upper-box language and only a few credible
  continuous ribbons. It is not competition-grade.

Next mandatory loop:

1. Do not lower the 0.55 VLM floor or fill the twentieth card with a failure.
2. Add compiler-level 3D silhouette/section descriptors that distinguish a
   coherent continuous field from transparent crossed plates; plan coherence
   alone currently misses this visual failure.
3. Feed the v6 bottom-card graph edits back to a new author population; do not
   reuse only parameter mutation.
4. Project the visual-floor archive onto real PNU law/parking. Require legal,
   parking, program, and capacity hard pass, then rank by VLM design quality.
5. Measure topology/geometry retention across legal projection. If repair turns
   a good source into a box or drops below FAR policy, return to the graph author.
6. Add a wall-clock/call budget to author recovery. Service requests must use a
   cached author pool and bounded asynchronous shortlist, not the 772-second
   research loop.

## 2026-07-14 graph-semantics, honest visual-floor, and v29 checkpoint

This is the latest checkpoint. The mass problem is **not complete** and the
current output is **not competition grade**.

Implemented correctness fixes:

- `program_massing/vlm_a2a.py` and `preference/loop.py` now use surface-aware
  VLM cache schema v2. A compiler change that alters visible profiled surfaces
  cannot reuse a stale box-image score.
- `source_geometry/design_fields.py`, `formal_principles.py`, and `compiler.py`
  now materialize an occupiable continuous ribbon field without adding the old
  rectangular box on top. The default ribbon reaches the neighborhood
  capacity gate and remains polygon-quality hard-pass.
- `source_geometry/graph_materializer.py` no longer emits every cumulative
  terminal state as an overlapping solid. It emits section bands/deltas.
- A confirmed graph-semantics defect was fixed: the live author correctly put
  `courtyard` in a root-sibling node with `relation=subtract`, but the
  materializer only inspected descendants of the primary. The v24 source
  signature therefore said `subtractive_node_ids=[]` and compiled a hole-free
  box. Subtractive deltas are now applied to the primary regardless of sibling
  placement.
- Root-sibling support states are not copied in parcel coordinates. Their
  normalized mutation is affine-rebased into the primary mass frame before it
  becomes a sectional layer. This is generic graph interpretation, not a
  named typology or fixed parcel-coordinate template.
- The final JSON now records `visual_floor_rejection_counts`, rejection
  samples, and `final_selection_audit`. Do not diagnose a low selected count
  from the selector alone.
- The visual floor no longer treats three rectangular height levels as a
  non-box language. A rectilinear envelope needs a real profiled surface,
  non-rectilinear exterior, or VLM `good_void` plus a substantial measured
  void. `too_box_like` is binding without direct geometry evidence.

Live author and loop evidence:

- Fresh live `gpt-5.4-mini` author cache:
  `maas-neighborhood-author-v21-fresh-graph-cache.json`.
  It contains 32 graph candidates, completed in about 43 seconds, with zero
  OpenAI batch errors and zero deterministic coverage repair. It is not a
  fallback-authored population.
- v24 before sibling subtraction: 3,124 evaluated, 1,363 clean, 995 capacity,
  21 VLM parents, 26 VLM children, only 3 selected. Rejection audit: 14 below
  VLM design floor, 9 box-like without geometry evidence, 4 fragmented. Three
  of six visual-floor survivors were duplicate ribbon descriptors.
- v27 after sibling subtraction: 7 selected and capacity target 5/7; carved,
  stepped, and folded counts increased. Direct PNG review rejected the numeric
  improvement because cards 2--5 were still visually rectangular box stacks.
- v29 after support rebasing and the stricter rectilinear gate: only 2 selected.
  One is a valid continuous ribbon; the second courtyard still reads too much
  like an assembled block despite `good_void`. This is an honest failed author
  population, not a reason to relax the floor.
- Latest full artifacts:
  `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v29-rebased-support.png`
  and `.json`.
- Latest raw graph board:
  `docs/playwright/design-route-live-verify/maas-graph-author-v28-rebased-support-probe.png`.
- v29 counts: 3,124 evaluated, 1,275 clean, 995 capacity, 21 parents, 21
  children, 2 selected, 2 capacity-target met. Language groups are continuous
  1 and carved 1. Status is `automatic_visual_floor_failed`.
- The primary v29 PNG was subsequently corrected to remain a 20-card human
  review board: 2 cards are green `ACCEPT`, 18 are red `REJECT`, and each red
  card displays its gate reason. The two-card view now lives only at
  `maas-neighborhood-vlm-a2a-v29-rebased-support-accepted-only.png`. Never
  hide generated stepped/folded candidates merely because the current critic
  rejected them; generation and evaluation failures must remain distinguishable.

Program and hard-gate verification:

- Cross-program benchmark passed with 6 cases, neighborhood mean fit 0.9605,
  gymnasium mean fit 0.98, and two distinct program geometry fingerprints.
  Artifact: `maas-program-cross-v28.png/.json`. The gym correctly differs as a
  long-span hall/service-entry composition, but the board is program-branch
  evidence, not a competition-quality claim.
- 34/34 graph/preference regressions pass, including root-sibling void and
  support rebasing.
- Seven targeted legal/parking regressions pass: repaired legal variants,
  <=8-space attached/tandem road-aisle relief, >8 exception blocking, small
  tandem layout, mechanical mass-stage parking, neighborhood local seed rule,
  and proof that a section connector cannot override the parking gate.
- Neo4j was not required for those deterministic hard-gate tests. Turning the
  graph DB off is not the cause of the visual mass failure. Neo4j remains
  useful for cited law provenance/memory, not for inventing geometry.

Current diagnosis and mandatory next order:

1. Do not fine-tune the VLM yet. The corpus is active and large; the latest
   failure is still author graph expressiveness plus graph-to-silhouette
   materialization. A better critic cannot generate an unavailable operator.
2. Generate one fresh bounded author population using the v29 exact rejection
   counts. Do not reuse v21 and claim a new result. Require independent
   silhouette operators: open court/canyon, branched field, folded shell,
   terraced landform, split bridge, and continuous ribbon.
3. Add multi-view exterior-silhouette/section descriptors. Closed rectangular
   courtyard holes and several stacked rectangles must not satisfy diversity
   merely through volume/height counts or transparent isometric rendering.
4. Feed critic edits into topology-level graph replacement, not only parameter
   edits. Preserve graph IDs and verify that edited operations materially alter
   source surfaces/volumes.
5. Inspect every raw and final PNG. Never relax the 0.20 duplicate distance or
   fill to 20 with known failures.
6. Only after 20 source masses survive direct review, project them through a
   real PNU legal/parking run and measure topology/geometry retention. Legal,
   parking, capacity, and clean-mass checks remain hard.

Mass-Brain remains useful as append-only graph/evaluation/feedback memory, but
it does not fix this checkpoint by itself. Keep it shadow-only until its graph
mutation contract can express and verify the missing topology changes.

## 2026-07-13 reference-first A2A v7/v8 and bridge compiler correction

This is the newest checkpoint. Read it before assuming that more ArchDaily
images or VLM fine-tuning is the immediate fix.

What the live run actually saw:

- `preference/reference_language_distiller.py` now reads reference images
  before graph authoring, not only after geometry exists. The v2 artifact is
  `docs/playwright/design-route-live-verify/maas-reference-language-neighborhood-v2.json`.
- That artifact used 10 real image-backed references including gymnasium,
  sports/cultural, restaurant, club and civic projects. It distilled eight
  coordinate-free graph recipes: continuous field, carved void, bridge/
  interlock, folded section, cluster field, two stepped-capacity languages and
  one hybrid civic language.
- Candidate scoring still sends up to three real reference images beside each
  candidate render. Therefore the current failure is not evidence that the VLM
  or ArchDaily corpus was inactive.
- No fine-tuning is justified yet. The strongest observed bottlenecks are typed
  graph preservation, graph-to-geometry compiler semantics, missing surface
  operators and final archive diversity. Fine-tuning a critic cannot create a
  geometry family the compiler cannot represent.

v7 artifact and verdict:

- `maas-neighborhood-vlm-a2a-v7.png/.json` took about 700 seconds.
- 27 authored graphs, 793 clean variants, 693 capacity-pass variants, 24 VLM
  parents, 15 children, 22 above the VLM floor, 20 selected.
- Direct PNG review: stepped/capacity forms returned, but bridge/interlock was
  absent and ribbons/plinth boxes repeated. Status correctly remained
  `automatic_visual_floor_failed`.

Root bridge defect and correction:

- The author did generate several split/diagonal/interlock graphs. They were
  lost before final selection because `split_bridge_connector` compiled as two
  wings plus a site-wide diagonal box plus a full-depth core. The redundant
  overlaps/collision and compact-monolith polygon test killed the bridge family.
- `source_geometry/formal_principles.py` now compiles the principle as two
  separated inhabited wings plus one short, graph/site-ratio connector.
- `source_geometry/compiler.py` no longer adds a second site-wide connector
  when split/diagonal/interlock is already materialized, and the legacy split
  path uses the same two-wing/short-bridge semantics.
- `source_geometry/coherence.py` recognizes bridge/ribbon/connector/spine roles
  as intentional linear elements for tortuosity only. Hairline width, overlap,
  fragments, collision, polygon validity and solid count remain hard gates.
- Probe artifact:
  `docs/playwright/design-route-live-verify/split-bridge-compiler-probe-v8b.png`.
  The main authored split bridge and coverage split both changed from coherence
  failure to 3 volumes, 15 raw surfaces, zero redundant overlap and coherence
  score 1.0.

v8 full-loop artifact and honest visual verdict:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v8.png/.json`
  is the current full-loop evidence. Runtime was 675.5 seconds with the author
  and reference-distillation caches reused; candidate images and VLM graph
  revision were recomputed.
- Counts: 2,904 evaluated; 1,002 clean; 884 capacity-pass; 24 VLM parents; 18
  VLM children; 22 visual-floor candidates; 20 selected.
- Language groups: continuous 3, carved 5, bridge/interlock 3, folded 3,
  stepped-capacity 4, cluster 1, calm anchor 1. Bridge/canyon is visibly present
  in cards 6, 7 and 18; stepped/capacity hierarchy is visible around cards
  8--12 and 19.
- v8 is **not accepted**. Direct review found near copies 1/2, 3/5, 6/7,
  10/12 and 11/19, plus remaining `large base + small upper box` cards. The
  automatic status correctly remained `automatic_visual_floor_failed` because
  cluster coverage was short.

Post-v8 code corrections not yet validated by another expensive full run:

- The final selector used to relax geometry distance from 0.16 to 0.099 and
  allowed two variants of one topology; this explains why visually duplicated
  cards filled the 20 count. Relaxed fill is removed. Final distance is 0.20,
  and a second variant of one graph requires at least 0.28 3D distance.
- The result now records `geometric_language_count` and explicit
  `near_duplicate_pairs`; visual review status cannot pass with a near duplicate
  or fewer than 18 measured geometry languages.
- Reference v2 requested only one cluster language while final selection
  required two. Distillation schema v3 now requests 10 recipes, including two
  cluster-field, two stepped-capacity and two hybrid-civic recipes. Default
  future cache is `maas-reference-language-neighborhood-v3.json`.
- The v3 distillation call was executed successfully against 12 real images.
  The artifact contains 10 validated recipes, including `Loose Cluster Commons`
  (`array, shift, nest`) and `Terraced Cluster Porch`
  (`array, offset, terrace_link`). This proves the new reference contract, not
  the resulting geometry quality.
- Do not reuse the v2 author cache to claim v3 geometry was tested. The next
  research run must use a newly authored v3 population and strict selection.
  It is acceptable and honest for that run to return fewer than 20 rather than
  force duplicates.

Regression state after these changes:

- 35/35 targeted polygon/preference plus gym-ridge tests pass.
- A new regression asserts a split bridge is exactly two wings + one connector,
  zero redundant overlap, coherence hard-pass.
- The larger 51-test group has one intentionally unresolved baseline failure:
  `sculptural_geometry_count_below_12_competition_target`. Never lower or hide
  it. A gym ridge regression found during the run was fixed by ensuring a
  semantic `main_long_span_hall` roof profile reaches `folded_section` surfaces.

Next mandatory order:

1. Use the completed v3 image distillation to create a new author population
   with a bounded call/wall-clock budget; do not pay for repeated authoring on
   ordinary requests.
2. Run strict final selection without relaxed duplicate fill. Inspect the PNG.
3. If fewer than 20 survive, feed the exact missing groups and duplicate pairs
   back to the architect agent for one bounded regeneration batch.
4. Continue adding genuinely independent graph-native surface/solid operators;
   do not solve missing diversity with labels, coordinates or selector quotas.
5. Only after the source 20 pass direct visual review, project them through real
   PNU legal/parking and measure geometry retention. Law/parking remain hard.

### 2026-07-13 v8 FAR audit and stratified ArchDaily retrieval v4

- Direct v8 capacity audit: mean normalized FAR utilization 0.7332, minimum
  0.5542, maximum 1.0. Counts were 11/20 >= 0.70, 6/20 >= 0.80 and only 2/20
  >= 0.90. Therefore v8 is not a full-FAR creative archive.
- The reason was policy/ranking, not lack of feasible geometry: the 2,400 m2
  neighborhood test used the large-site balanced minimum 0.55, and final VLM
  ranking had no capacity target term.
- `capacity_policy.py` now exposes a separate `target_far_utilization`:
  capacity-first 0.90, balanced 0.75, design-led 0.55. The minimum hard gate
  remains separate. Do not apply capacity-first globally to museums, gyms or
  other design-led briefs.
- The neighborhood VLM research loop now explicitly uses capacity-first, keeps
  minimum 0.70, ranks capacity fit toward target 0.90 after hard gates, and
  requires at least 8/20 final cards to reach target before visual status can
  become reviewable. This code is tested but has not yet produced a new full
  PNG; v8 remains the last complete board.
- ArchDaily DB was not small: `DB_MANIFEST.json` reports 12 collections, 274
  unique projects and 338 local images. v3 retrieval nevertheless chose 6/12
  images from `sports_architecture`; the failure was retrieval concentration.
- Reference distillation schema v4 uses collection-stratified sampling with a
  two-image cap and priority for `iconic_precedents` and
  `massing_diversity_20260711`. Actual v4 sampling covered 11 collections and
  included `8 House / BIG`, `Hangzhou Prism / OMA`, sports, cultural, cafe,
  apartments, houses, housing, office and current-project references.
- Actual artifact:
  `docs/playwright/design-route-live-verify/maas-reference-language-neighborhood-v4.json`.
  It distilled 10 recipes, including two genuinely separate cluster briefs:
  `porous settlement field` (`array, offset, courtyard`) and
  `courtyard weave field` (`branch, nest, courtyard`).
- Next full run must use v4 plus a newly authored population. Do not reuse v7
  author cache and do not claim v4 improved geometry until its PNG is inspected.

## 2026-07-14 durable quality archive / repeatability correction (v49-v53)

Current best full-loop evidence:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v53-full-frontier-repeatability-contract.json`
- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v53-full-frontier-repeatability-contract.png`
- Status: `technical_pass`, `visual_status=review_required`; 20/20 accepted,
  20 measured geometry languages, zero near-duplicate pairs.
- Capacity-first portfolio: 9/20 reach normalized FAR utilization 0.90; required
  count is 8. Final groups are bridge 2, stepped 3, continuous 4, carved 6,
  cluster 2, calm 1 and folded 2.
- Archive evolution contract also passes: 14 persisted + 6 fresh, maximum
  persisted 16 and minimum fresh 4. Authored selection is 13/20.
- v49 independently passed the same 20/20, capacity and duplicate gates with a
  30-parent frontier. v50 (20-parent frontier) returned 19; v52 returned 20 but
  only 7/8 capacity. Therefore `review_pool_count=30` is the current quality
  setting. A 20-parent quick mode must not claim equivalent reliability.

Fundamental bugs fixed, not parcel-coordinate patches:

- Component-graph verbs now have executable general semantics for separated
  arrays, split bodies + connector and interlocking bodies. Cumulative graph
  states no longer become overlapping solids or fill intended field gaps.
- Language-specific geometry gates reject labels without direct geometric
  evidence: continuous, folded, stepped, bridge/interlock, carved and cluster.
- The quota loop now fills actual deficits. It previously added every minimum
  again after persisted/authored reservation, causing early language groups to
  overtake the board.
- Durable accepted memory and mutation-parent frontier are separate. All exact
  accepted graphs are cache-revalidated and remain eligible for the final
  stability archive even when they are not selected as mutation parents.
- Final selection reserves fresh candidates first, then authored/language/FAR
  deficits, then fills remaining cells from accepted memory. One weak author
  batch can no longer erase the good archive, and accepted memory can no longer
  freeze every presentation slot.
- Capacity rebalance now preserves language minima/maxima, descriptor distance,
  topology/principle caps, authored minimum, persisted maximum and fresh
  minimum. v51 exposed and v52 fixed a hidden fresh 4 -> 3 policy violation.
- VLM cache schema is identity-independent for equivalent executable geometry;
  repeated `llm_accepted_seed_` prefixes are normalized. Each completed paid
  VLM evaluation is now written immediately with an atomic temp-file replace,
  so a later timeout cannot discard prior completed scores.
- Final carved maximum is 6, not because distance was relaxed, but because the
  label contains distinct courtyard/atrium/notch/embed/monolith principles.
  Descriptor distance remains 0.20 and per-principle maximum remains 4.

Regression and visual verdict:

- `python manage.py test design.test_maas_preference --verbosity 1` passes
  42/42 after the final code change; `py_compile` also passes.
- Direct v53 PNG review: fragmentation/collision regression is gone and the
  sheet contains readable ribbon, split/bridge, stepped, courtyard, cluster and
  folded alternatives. It is a stable clean mass-stage baseline.
- Do **not** call this architecture-competition grade. Too many cards remain
  conservative rectilinear podium/bar/box compositions; the compiler still
  lacks a strong continuous curved sheet/roof language comparable to the user
  reference. `review_required` means human review, not aesthetic completion.
- `legal_projection_status` is still `not_run` in this neighborhood research
  loop. Capacity is enforced, but real PNU law/parking projection and geometry
  retention must run later as separate hard gates. Neo4j being off did not
  cause the mass-language problem and is not needed for this isolated benchmark.

Next mandatory work:

1. Keep v53 (or a later passing archive) as the immediate service response;
   replenish missing/weak cells asynchronously instead of running a 5-6 minute
   full VLM loop inside every request.
2. Move beyond the stable rectilinear baseline by adding graph-native curved
   sheet, variable-width ribbon and continuous roof/section operators with the
   same direct geometry gates. Do not add named coordinate templates.
3. Add a blind human/reference comparison metric for silhouette continuity,
   spatial consequence of voids and non-box curvature. VLM remains critic and
   graph-edit author; it is not itself the geometry compiler.
4. Run cross-program neighborhood/gym/cafe or museum benchmarks using their own
   capacity policies. Never force neighborhood 0.90 FAR onto design-led briefs.
5. Only after source-mass visual review, run real PNU legal/parking projection
   and reject excessive geometry loss; law/parking remain hard constraints.

## 2026-07-14 real-PNU site adaptation and curved-field target

Verified site path:

- Project PNU is `1168011800104170004`. A live VWorld parcel lookup returned
  the matching polygon; WGS84 was transformed to UTM 52N and translated to a
  local metric frame. Measured site area is 264.13 m2.
- `scripts/run_neighborhood_vlm_a2a.py` now accepts `--pnu`,
  `--site-boundary-from` and `--far-limit-ratio`. The real metric polygon is
  passed into the graph author site context, compiler, FAR calculation and
  result provenance. The cache fallback is accepted only when its stored PNU
  matches the requested PNU.
- `source_geometry/design_fields.py` derives its frame from the parcel minimum
  rotated rectangle. Ribbon cross-sections follow the parcel long axis instead
  of global X/Y coordinates. Evidence records the coordinate frame and world
  angle. This is a general site rule, not a coordinate template for this PNU.
- A separate archive adaptation probe compiled the v53 accepted graphs on the
  real parcel: 20/20 compiled, 20/20 passed parcel containment and 16/20 reached
  normalized FAR utilization 0.90 at FAR 250%. Evidence is
  `maas-pnu-1168011800104170004-v53-adaptation.json/.png`.
- Parcel containment now records both buffered predicate and outside area.
  The only tolerance is 2 mm plus a capped 0.0005--0.005 m2 GEOS Boolean-area
  tolerance; it cannot hide a meaningful setback or parcel breach. The former
  strict `covers` check falsely rejected 17 candidates for at most 0.00035 m2
  of clipping dust.

Honest visual interpretation:

- The adaptation PNG proves site fit, orientation and capacity transfer. It
  does not prove that the agent authored new forms for the site, and it is not
  a legal/parking projection. A fresh PNU-conditioned Author -> compiler ->
  hard gate -> VLM loop is the next required evidence.
- `docs/images.jpg` is a language target, not a building to copy. The useful
  principles are parallel/branching curved bars, variable-width tapered ends,
  layered continuous roof sheets, deliberate landscape courts and one coherent
  field responding to the parcel/landscape axes.
- Current `swept_ribbon` and Catmull-Rom paths can express curved centerlines,
  but width is effectively constant and roofs are still assembled from bounded
  profiled surfaces. Therefore the current compiler cannot yet reproduce the
  reference's variable-width multi-body roof continuity at competition quality.
- Required representation work is graph-native: variable-width sweep,
  tapered/branched lane field, rail-to-rail roof loft, field-spacing/courtyard
  gate and a site medial/access/landscape flow field. VLM edits must mutate
  these typed parameters; adding named coordinate recipes is prohibited.

Service/runtime boundary:

- PNU is sufficient to retrieve and condition on the parcel. Neo4j is not
  required for VWorld geometry or the isolated mass loop.
- Keep a verified site archive as the immediate response and improve it in an
  offline replenishment job. The existing cache refresh command supports
  offline atomic publication, but a durable queue with crash-safe job state is
  not yet implemented and must not be claimed complete.

### Real-PNU full-loop correction chain (v54-v58)

Current real-site checkpoint:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v58-pnu-1168011800104170004-access-step-replenish.json`
- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v58-pnu-1168011800104170004-access-step-replenish.png`
- `docs/playwright/design-route-live-verify/maas-pnu-1168011800104170004-site-adaptation-latest.json/.png`
- v58 status is `technical_pass`, `visual_status=review_required`: 20/20,
  normalized FAR target 13/8, zero near duplicates. Groups are carved 5,
  continuous 4, stepped 3, bridge/interlock 3, folded 3 and cluster 2.
- Search/VLM counts: 4,356 raw evaluated, 2,834 clean, 2,594 capacity-pass,
  30 VLM parents and 27 critic children. The live author produced 29 candidates
  with no OpenAI batch errors or deterministic fallback repair.

Why v54-v57 are not the final checkpoint:

- v54 used the real parcel but an incorrect temporary `south` access fact and
  returned only 19. v55 restored 20 but still lacked parcel/access visual
  evidence and failed its folded-section quota. Never cite either as full PNU
  site intelligence.
- v56 corrected the author to the actual east frontage and drew the green
  parcel outline for VLM. It passed, but did not yet show which parcel edge was
  the road frontage.
- v57 added the thick blue primary-access segment and made parcel/access
  geometry part of VLM cache identity. It honestly failed with only two
  stepped-capacity candidates. v58 fed that exact deficit to a new east-access
  author batch and passed without relaxing any quota.

Actual site/access evidence:

- Live VWorld parcel area is 264.13 m2; dominant axis is about 28.99 degrees.
- Live neighboring-road lookup found one east frontage, shared length 14.01 m,
  estimated road-parcel width 37.48 m. The width is contextual evidence, not a
  permit-final road-width certification.
- Author prompts receive descriptive access facts, not coordinates. The
  compiler receives the local metric polygon. VLM previews show the parcel as
  a thin green polygon and verified frontage as a thick blue segment.
- VLM cache schema now includes component graph, volumes, surfaces, parcel
  geometry, access context, access geometry and reference IDs. Scores cannot
  leak across a different site or road edge.

Direct visual verdict:

- v58 is more trustworthy than v53 as project-site evidence and preserves
  ribbon, stepped, clustered, bridge, folded and carved alternatives on the
  real parcel. It no longer hides site fit behind isolated orange masses.
- It is still not competition-grade or comparable to `docs/images.jpg`.
  Several cards remain conservative rectilinear bars/podiums, and the current
  ribbon has a curved centerline but not a true variable-width multi-building
  roof sheet. Do not convert `review_required` into aesthetic completion.
- Legal/parking projection remains `not_run` in v58. FAR capacity and real
  parcel containment pass, but permit law, parking layout and post-projection
  language retention remain the next hard stage.
## 2026-07-14 rotation-equivalent language correction and GRL audit (in progress)

User-visible failure after real-PNU v58:

- Several cards express the same architectural language with only a rotated or
  reflected placement. The v58 JSON reported `near_duplicate_pairs=[]`, but
  direct PNG review correctly rejected that claim.
- Root cause is now identified in
  `program_massing/search.py::_descriptor_distance`: it compared layered
  volumes and plan symmetric difference in absolute site coordinates. Rotating
  the same mass therefore increased distance and incorrectly rewarded it as a
  new language. This is an algorithm defect before it is a VLM-data problem.

Implementation now present but not yet certified by a new full PNU board:

- New modular policy module:
  `ARR/backend/design/maas/program_massing/morphology.py`.
- It centers each layered source mass, aligns its minimum-rotated-rectangle
  major axis, normalizes uniform scale, and compares all planar rotation and
  reflection symmetries while retaining plan proportion, void placement and
  vertical band structure.
- `_descriptor_distance` uses this intrinsic morphology channel. If compiled
  geometry is equivalent, different LLM labels/principle prose cannot rescue
  the duplicate. Site/access response stays a separate evaluation channel and
  is not counted as a new formal language.
- Regression tests cover a 90-degree rotation and reflection of the same
  compiled mass.

GRL decision:

- `D:/Data/25_ACE/GRL/GRL` is a portable evidence/circuit/relation contract
  viewer. It is not a generator, optimizer, graph database or learned geometry
  model, so attaching it alone cannot improve form.
- A replaceable adapter is now isolated in
  `program_massing/grl_contract.py`. Each full loop writes a sibling
  `*-grl.json` contract tracing site -> formal principle -> executable selected
  mass and records pose-invariant morphology-neighbor/duplicate relations.
- The selector/hard gate improves the archive; GRL makes the decision
  inspectable. Do not move generation logic into GRL.

Relevant 2026 research checked against the code:

- Proc3D (arXiv:2601.12234): compact editable procedural graph and localized
  parameter editing. It supports keeping MassDSL/component graphs compact and
  executable; it does not supply architectural quality automatically.
- 3D-Layout-R1 (arXiv:2603.22279): structured scene-graph edits plus geometric
  IoU/collision reward. It supports graph-edit traces with deterministic
  geometry rewards rather than prose-only critic output.
- 3DCodeBench (arXiv:2606.01057): VLM procedural code generation still needs
  execution feedback and pairwise human preference; disconnected/floating
  geometry remains common. It supports the existing compile/gate/render/critic
  loop and shows why VLM reranking alone is insufficient.
- SimWorlds (arXiv:2607.01766): planner/coder/reviewer with a deterministic
  verifier and runtime-state inspection. It supports modular agent roles and
  executable stage gates, not one monolithic prompt.

Required next verification after any session interruption:

1. Finish `design.test_maas_program_massing` and the focused morphology/GRL
   tests; do not claim pass until the command exits successfully.
2. Run the same real PNU `1168011800104170004`, same target 20 and same v58
   author/VLM caches as a v59 comparison. New paid calls are not required for
   unchanged executable geometry.
3. Compare v58 versus v59 on selected count, capacity target, language-group
   histogram, intrinsic duplicate count, geometric-language count, VLM score,
   and direct side-by-side PNG judgment.
4. If strict pose-invariant novelty leaves fewer than 20 valid cards, report
   the honest deficit and author genuinely new graphs. Never relax the metric
   merely to refill the sheet.
5. This patch only fixes false diversity. Competition-grade variable-width
   sweeps, branched/tapered ribbon fields and continuous roof loft remain the
   next representation-level generator work.

## 2026-07-14 pose-invariant v59 and editable field representation v61-v65

Same-PNU v59 result (do not overwrite with the earlier plan):

- Artifact: `maas-neighborhood-vlm-a2a-v59-pnu-1168011800104170004-pose-invariant-grl.json/.png`
  plus sibling `-grl.json`.
- Strict rotation/reflection-invariant selection returned an honest 18/20,
  `technical_fail` and `automatic_visual_floor_failed`; it did not refill the
  board with pose variants. Raw/clean/capacity pools were 3,872 / 2,283 /
  2,071. Capacity target was 12. Final groups were carved 6, continuous 1,
  folded 3, bridge 3, cluster 2 and stepped 3.
- Final `near_duplicate_pairs=[]` and `morphology_repeat_pairs=[]`. Re-auditing
  v58 with the new metric found five repeated pairs that the old world-axis
  metric missed: one intrinsic geometry duplicate plus four same-principle or
  same-topology repeats.
- Direct PNG review: v59 removes false rotated/reflected diversity, but the
  remaining slots are filled mostly by conservative bar/court/box languages.
  Quality did not become competition-grade. This proves the metric correction,
  not design completion.

Modular implementation boundaries:

- `program_massing/morphology.py`: replaceable intrinsic D4 pose-invariant
  morphology metric and novelty policy.
- `program_massing/graph_archive.py`: bounded multi-elite frontier and authored
  field-topology coverage audit. This avoids all-pairs work on 2,000+ legal
  candidates while retaining several elites per behavior cell.
- `program_massing/grl_contract.py`: GRL evidence/lineage adapter only.
- `source_geometry/parametric_curves.py`: variable-width sweep primitive.
- `source_geometry/design_fields.py`: parcel-frame path, width, branch and
  height fields; it contains no PNU coordinate recipe.
- `source_geometry/formal_principles.py`: graph field -> legal proxy volumes
  and serializable surface-field specs.
- `compiler.py`: consumes the field specs as quad-strip roof/facade surfaces;
  legal/FAR proxy volumes remain separate. A future NURBS/neural field backend
  can replace this materializer without changing selection or law stages.
- `scripts/render_ribbon_topology_probe.py`: reproducible real-PNU
  representation benchmark. It is not a production seed library.

Representation loop and honest visual verdict:

- v61 first branched topology: clean 3-volume trunk + two arms, but FAR was
  only 0.31-0.36.
- v62 made the field capacity-bearing without box refill: branched FAR rose to
  0.65-0.74, but equal-height extrusions looked like curved walls.
- v63 connected branched roles to the existing profiled surface path; still
  relied on a non-planar polygon roof.
- v64 exposed agent-authored width and height profiles, but renderer
  triangulation produced jagged/tent-like roofs.
- v65 replaced that representation with path-aligned variable-width
  quad-strips. Artifact:
  `maas-pnu-1168011800104170004-v65-quad-strip-field-probe.json/.png`.
  Six of six variants compile, pass containment/coherence, parallel FAR is 1.0
  and branched FAR is 0.6459-0.7435. Direct PNG review confirms smoother roof
  strips and real plan/section change, but it is still a six-form
  representation test, not an ArchDaily/competition-grade 20-board.

Fresh-author audit in progress at handoff time:

- v66 author cache contains 29 live `gpt-5.4-mini` candidates. Three contain a
  bend call. Only one explicitly authored the full width/height field contract
  and it selected `parallel`; two legacy-shaped bend calls normalize to the
  parallel default. No authored `branched` candidate exists in that population.
- The prompt now requires at least one parallel and one branched field, and the
  separate `field_topology_coverage` gate makes a missing topology an honest
  visual-floor failure. This is a population diversity constraint, not a
  coordinate or precedent-outline hardcode.
- If v66/v67 contains no branched field, run a new author batch; do not claim
  the compiler capability proves the agent used it and do not weaken the gate.

Completed v66 result:

- `maas-neighborhood-vlm-a2a-v66-pnu-1168011800104170004-fresh-field-contract.json/.png`
  is `technical_fail`, `automatic_visual_floor_failed`, 18/20. It evaluated
  3,784 raw / 2,662 clean / 2,478 capacity candidates, reviewed 24 VLM parents
  and 27 critic children, and met FAR target on 12/8.
- Final geometry has 18 languages and no pose-invariant repeat pairs, but is
  short one continuous field and one stepped-capacity candidate. Thirteen of
  18 selected candidates are live-authored.
- Direct PNG review still rejects the board: one clear profiled field appears
  at card 4, while most cards remain conservative rectilinear courts, bars and
  stepbacks. Removal of duplicates exposed the generator's language deficit;
  it did not create quality by itself.
- The live author took about 200 seconds, returned 29/29 compiled graphs, no
  OpenAI batch error and no deterministic repair. Do not rerun this author
  payload synchronously in a service request.

Current-code cached-author v67 result:

- `maas-neighborhood-vlm-a2a-v67-pnu-1168011800104170004-current-field-audit.json/.png`
  recompiles the same v66 author population with the quad-strip field
  representation. Author cache lookup took 2 ms.
- Result remains `technical_fail` / `automatic_visual_floor_failed`: 19/20,
  FAR target 12/8, 19 geometric languages, no near/intrinsic duplicate pairs.
  It is short one continuous field and one stepped candidate.
- Authored topology audit is explicit: parallel 3, branched 0, hard fail.
  Post-run selected-sequence audit is parallel 1, branched 0, also hard fail.
  v67 started before the selected-coverage result field was added, so its JSON
  has no selected audit object; the same public audit function produced these
  counts immediately afterward and future runs persist both author and final
  coverage.
- Direct PNG review: the continuous field at card 10 has a smoother profiled
  roof than v66, but the board remains overwhelmingly rectilinear. This is a
  renderer/representation improvement, not a generator-quality completion.
- Do not spend another full author call merely to refill a counter. The next
  author batch must explicitly close the branched and stepped deficits, and
  the final archive must retain both parallel and branched topologies.

Verification known at this checkpoint:

- Six focused tests pass: variable-width sweep, bounded behavior frontier,
  GRL duplicate relation, rotation/reflection invariance, default capacity
  ribbon and agent-authored branched quad-strip field.
- Separate field-topology coverage tests also pass.
- The full `design.test_maas_program_massing` module previously exceeded the
  244-second command window; do not convert that timeout into a full-suite pass.

## 2026-07-14 v68-v74 clean-selector and unioned branched-field correction

Read this section before rerunning the current full PNU loop.

Verified failure chain:

- v68 had a surface-aware three-view metric but 16/20 technical failures and
  visually repeated boxes.
- v69 fixed graph-envelope search mutation, graph-native primary cardinality,
  Windows/WSL reference paths and VLM graph-edit validation. It selected 15
  but still contained three duplicate pairs.
- v70 separated descriptor and silhouette hard gates. It honestly returned
  13/20 with zero duplicate pairs.
- v71/v73 exposed invalid Shapely polygons at multiple scoring boundaries.
  `program_massing/geometry_safety.py` is now the shared repair/union boundary;
  do not reintroduce raw population-wide `unary_union` calls.
- v73b selected 17/20 with zero near/morphology/silhouette repeats, but final
  topology coverage was parallel 1 / branched 0. Direct PNG review remained
  box-heavy.

Root causes fixed after v73b:

1. Graph-native semantics were still partly positional. A shared
   `primary_operation_from_sequence()` now resolves the component whose graph
   role is `primary`; selectors and descriptor semantics no longer assume
   `calls[1]`.
2. More importantly, the compiler allowed filename/`mass_language` hints such
   as `offset_twin_bar` to override an explicit primary `bend`. A graph-native
   primary operation now determines the executable source family. Prose and
   support operations remain provenance/secondary intent.
3. The parameter schema allowed a larger ribbon width than the author and
   design-field boundaries. `lane_width_ratio` now has one shared 0.045-0.22
   typed contract, allowing capacity search to produce occupiable 8-10 m bars
   on the real small parcel without coordinate templates.
4. A branched continuous field used to serialize trunk plus two arms as three
   overlapping legal solids. Widening them triggered collision gates and read
   as LEGO fragments. The legal/FAR proxy is now one unioned branched solid;
   editable trunk/arm roof and facade quad strips remain separate VLM/render
   surface patches.
5. The formal compiler's unconditional three-volume minimum discarded this
   clean solid and silently restored the legacy two-box bend fallback. A
   continuous field may now have one legal solid when profiled surface specs
   are present.
6. Program spatial evaluation previously treated every single solid as
   dominant ratio 1.0 and hierarchy 0. A narrowly scoped exception now uses
   executable profiled patch count for hierarchy/dominance only when the
   continuous-surface hard evidence passes. Ordinary single boxes receive no
   exception.

Minimal same-PNU audit before the full run:

- The three live-authored branched-bend repair seeds originally produced zero
  accepted mutations out of 132.
- After the source-family/union/spatial fixes, 64 clean program candidates
  survive, 21 reach normalized FAR utilization >= 0.70, maximum utilization is
  0.7708, and every survivor is `continuous_field / branched` with one visible
  legal volume and coherence 1.0.

Latest full artifact:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v74-primary-unioned-branch.json`
- sibling `.png`, `-accepted-only.png`, `-grl.json`, and VLM score cache.
- Real PNU `1168011800104170004`, VWorld live 264.13 m2 parcel and east road.
- Raw / clean / capacity pools: 3,784 / 2,411 / 1,944.
- VLM parents 23, critic children 17, selected 17/20.
- Final groups: continuous 2, carved 6, stepped 2, bridge 3, cluster 2,
  folded 1, calm 1. Missing quotas: folded 1 and stepped 1.
- Capacity target met by 10 selected candidates. Parallel 1 / branched 1 final
  topology coverage passes. Near, intrinsic-morphology and silhouette repeat
  pairs are all empty.
- The selected branched candidate has one legal volume, 44 profiled surfaces,
  FAR utilization 0.8165 and VLM design score 0.6883.
- The author cache was a real `gpt-5.4-mini` cache hit (3 ms); reference corpus
  count remains 274. Geometry-changed candidates were keyed separately in the
  VLM cache.

Honest direct PNG verdict:

- Card 2 is materially improved: a single joined branching/curved mass, not
  three overlapping blocks. The parallel profiled field and several terrace/
  bridge candidates remain legible.
- Roughly half the board is still conservative rectilinear court, bar, box or
  stepback language. The folded candidate is weak. This is not ArchDaily/BIG/
  competition-grade completion and the 17/20 status must stay red.
- The offline loop took about 1,100 seconds. It is an archive-improvement batch
  job, not a synchronous service path. Production should consume a verified
  graph archive and perform bounded site adaptation/legal projection.
- `legal_projection_status` is still `not_run`. Neo4j being off did not cause
  the geometry failures; the PNU/VWorld/source-geometry path works without it.

Next work, without weakening gates:

1. Generate a targeted live replenishment for genuinely distinct folded roof
   and stepped landform graphs using v74 feedback; do not refill with rotations
   or another court box.
2. Add stage timing and descriptor/silhouette memoization. The full loop grows
   slower as the clean archive grows.
3. Run the resulting accepted graph archive through the deterministic service
   legal/FAR/parking path and measure geometry retention. Do not infer legal or
   parking pass from the offline board.
4. Continue direct PNG review. Counts, VLM pass and zero duplicates remain
   necessary but insufficient for a competition-grade claim.

## 2026-07-14 v75-v79 adaptive replenishment, strict language evidence, and hierarchical cluster grammar

Read this section first. It supersedes v74 as the current implementation and
failure diagnosis, but it does not claim completion.

What was implemented:

1. `program_massing/adaptive_loop.py` now runs bounded author -> compile -> VLM
   -> selector replenishment rounds. It carries accepted executable graphs,
   author populations and geometry-keyed VLM caches forward. It never pads a
   board with rejected or duplicate candidates.
2. `generation_feedback_from_result()` separates an authored topology deficit
   from a selector-retention deficit. A prior author archive that already has
   parallel and branched fields is not forced to reauthor them every round.
3. Missing language groups are classified from the executable primary graph
   operation, not filename or language label. A focused author repair batch is
   requested only for the measured deficit.
4. Search cost is explicit through `search_generations` and
   `offspring_per_seed`. Focused 1x3 runs take roughly 3-4 minutes with an
   author-cache hit instead of the earlier 27-minute full-population search.
5. `too_box_like` is binding unless the compiled geometry contains a profiled
   surface or critic-confirmed strong void. A family label no longer rescues
   arbitrary cuboids.
6. `stepped_capacity` now requires actual centroid shift or plate-area change.
   Three coincident slabs are not a stepped language.
7. `carved_void` is rejected when VLM says `needs_carved_void` without also
   confirming `good_void`. Bounding-envelope whitespace alone is insufficient.
8. `cluster_field` now requires shared open-space ratio, local adjacency and
   component-area hierarchy. Three or four equal detached boxes fail.
9. MassDSL `array` gained typed `hierarchy_ratio` and `stagger_ratio`. The
   author controls them and the compiler derives unequal, staggered members
   from parcel dimensions. This is a reusable procedural grammar, not a named
   building or parcel-coordinate template. Numeric author values are persisted
   within the shared typed bounds instead of being silently clamped only at
   render time.
10. Adaptive orchestration is monotonic best-so-far. v79 round 1 produced
    18/20, while round 2 regressed to 17/20. The coordinator now compares round
    quality and returns the better artifact rather than blindly returning the
    last round.

Verified artifact chain on live PNU `1168011800104170004`:

- v75d (`maas-neighborhood-vlm-a2a-v75d-focused-continuous-cluster`): 20/20,
  seven language groups, parallel 1 / branched 1, no measured duplicates,
  capacity target 12. This was before the stricter box/language evidence and
  therefore is not the current quality truth.
- v76 (`...v76-binding-box-critic`): 20/20, capacity target 10. It rejected
  three box-like candidates but the direct PNG still contained many
  conservative rectilinear masses.
- v77 round 2 (`...v77-strict-language-evidence-r2`): honest 17/20. Uniform
  array clusters and weak carved candidates were removed. This failure proved
  that the compiler, not reference-data quantity, was collapsing authored
  cluster intent.
- v78 (`...v78-hierarchical-cluster`): the same cached graphs recompiled with
  the new array grammar; cluster survival improved from 0 to 1 and total from
  17 to 18 without a new OpenAI author call.
- v79 round 1 (`...v79-authored-spatial-cluster`): current stricter best,
  honest 18/20. Final groups are continuous 2, bridge 2, carved 5, cluster 2,
  folded 3, stepped 3 and calm 1. Language minima are complete; two additional
  intrinsically distinct visual-floor candidates are still missing. Round 2
  regressed to 17 and exposed the best-so-far orchestration bug now fixed.

Direct PNG verdict:

- Continuous fields, bridge/interlock, folded roofs, terraces and two spatial
  clusters are all present. The cluster fields are no longer equal-size array
  copies.
- The board is cleaner and semantically more honest, but several court,
  carved and stepped candidates remain conservative rectilinear compositions.
  It is not yet ArchDaily/BIG/OMA or competition-grade.
- Do not weaken intrinsic distance or visual gates merely to reach 20. The
  missing work is more expressive executable graph/surface representation and
  stronger candidate generation, not counter repair.

Reference-data conclusion:

- The local corpus currently contains 12 collections, 274 unique records and
  338 images across housing, cultural, commercial, office and sports domains.
- Blindly crawling more ArchDaily images is not the current priority. First
  improve typed reference-to-graph mutation and compiler expressivity. Add
  data only when a measured language/usage gap is identified, then curate it
  by formal principle rather than raw image count.

Non-negotiable remaining work:

1. Keep v79 round 1 as the best strict checkpoint and run future rounds through
   the monotonic coordinator.
2. Add stronger graph-native non-rectilinear sectional/roof/ground operations;
   do not simulate them with more boxes or filename labels.
3. Add a portfolio-level architectural ambition audit independent of language
   quotas, then compare it with direct PNG review.
4. Project the accepted executable graphs through deterministic law, FAR and
   parking and measure geometry retention. Offline `legal_projection_status`
   is still `not_run`; no legal or parking pass may be inferred here.
5. Serve verified archive results immediately and run costly author/VLM
   replenishment asynchronously. A fresh focused round is about 7-8 minutes;
   this is not a synchronous request path.

## 2026-07-15 v80-v86 closed-loop graph-mutation audit

Read this section before treating v79 as the latest checkpoint. The mass loop
is materially more capable, but it is still not competition-grade and it did
not run deterministic legal/parking projection.

Root causes fixed in code:

1. The VLM prompt looked for `props.component_graph`, while the executable
   graph is stored at `props.source_signature.component_graph`. The critic was
   therefore often shown an empty graph and targeted an invented `root` node.
   The prompt now exposes the real editable node ids and primary node id, and
   forbids structural edits against `root`.
2. Reference retrieval previously reinforced the candidate's current language.
   It now keeps two similar precedents and reserves one image-backed
   counterfactual formal principle. This is a generic retrieval policy, not a
   named-building template.
3. VLM graph revision is no longer limited to scalar tuning. A typed
   `set_control_point` edit can move one existing bend control point within
   bounded normalized coordinates while preserving path order. The canonical
   parameter schema, orchestration directive and graph revision all share the
   same contract.
4. Geometry-fingerprint dedup previously discarded an editable bend genotype
   when a frozen scalar candidate rendered similarly. Review-parent selection
   now reserves executable control-field candidates and prefers mutation
   capacity when geometry is otherwise identical.
5. A paid fresh author run could be aborted by an older cache because the old
   population was revalidated against the new target count. Historical caches
   are now validated against their own persisted population contract.
6. Critic replacement is non-destructive and final portfolio search uses a
   constraint-aware beam solver. A worse child cannot erase a distinct good
   parent merely because it was reviewed, and greedy early choices no longer
   trivially block a better compatible portfolio.

Real-PNU loop evidence for `1168011800104170004`:

- v80 non-destructive critic archive: honest 18/20.
- v81 constraint portfolio solver: still 18/20; the solver alone did not create
  missing morphology.
- v82 structural reference graph edits: 17/20. Structural edits executed, but
  the empty/wrong graph target defect was exposed.
- v83 counterfactual/node-aware prompt: 16/20. Eight of nineteen rescored
  children improved, but stricter admission reduced the final board.
- v84 fresh graph author: 15/20 despite 64 authored graphs. More candidates did
  not solve the representation/capacity interaction.
- **v85 control-point critic is the current best evidence**: honest 19/20,
  capacity target 10 (minimum 8), all seven language groups present, and zero
  intrinsic silhouette repeats. Artifact:
  `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v85-control-point-critic-accepted-only.png`.
- v86 editable-genotype archive also returned 19/20 and increased the review
  frontier from 21 to 23, but lost one cluster quota and was not visually
  better. Keep v85 as best-so-far.

Direct PNG verdict:

- v85 is cleaner than the earlier box-pile regressions and includes a credible
  continuous ribbon plus stepped, folded, carved, bridge and cluster families.
- Several candidates are still conservative boxes/steps and one thin
  interlock is visually weak. This is not yet ArchDaily/BIG/OMA or
  competition-grade massing.
- The system emitted `set_control_point` edits, but no accepted improved child
  yet proves that a VLM curve mutation survives compile, capacity and spatial
  gates. Do not describe the typed edit contract itself as a solved visual
  feedback loop.

Current bottleneck and next bounded work:

1. Make control-point review eligibility explicit: only request
   `set_control_point` for an existing bend node that already has 4-6 controls,
   then measure accepted-child improvement rather than operation count.
2. Optimize continuous-field width and sectional height against the target FAR
   before hard-gate evaluation. Current authored ribbons are frequently too
   thin/low-capacity; weakening the gate or refilling with boxes is forbidden.
3. Generate one more intrinsically distinct capacity-bearing cluster/field to
   close 19 -> 20. Do not duplicate or rotate an existing language.
4. After an honest 20/20 mass board, run deterministic law/FAR/parking
   projection and report geometry retention. v80-v86 are mass-stage only.

Data/model conclusion: the local corpus already has 274 references and 338
images. Blind crawling or fine-tuning is not justified by this failure. The
measured issue is executable representation, mutation admission and
capacity-aware search. VLM is active as image critic and typed graph reviser;
it is not a free-form mesh generator. Neo4j was not required for this offline
loop.
