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
