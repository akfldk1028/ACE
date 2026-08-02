# MAAS Lawful Diverse LLM Pilot - Active Recovery Memory

Updated: 2026-07-30 19:45 KST

## 2026-08-01 subagent continuation checkpoint (required_macro_operators_any)

- Root cause confirmed in code: `synthesis_requests_from_program_profile()` was
  forwarding only `required_macro_operators_all` from geometry contract, so
  contracts using `required_macro_operators_any` were never enforced during
  recursive program synthesis.
- Fix applied:
  - `ARR/backend/design/maas/geometry_language/synthesis.py`
    now reads `required_macro_operators_any` from request/profile contracts.
  - Candidate synthesis enforces “at least one of required_any” by injecting a
    compatible required operator when missing.
  - `synthesis_requests_from_program_profile("neighborhood living"/"cultural")`
    now carries that required_any list forward.
  - Added regression test:
    `test_profile_required_macro_operators_any_are_enforced_in_synthesis`
    in `ARR/backend/design/test_maas_geometry_language.py`.
- Quick validation run:
  - `python backend/manage.py test design.test_maas_geometry_language.MaasGeometryLanguageTest.test_profile_required_macro_operators_any_are_enforced_in_synthesis`
  - `python backend/manage.py test design.test_maas_geometry_language.MaasGeometryLanguageTest.test_program_profile_infers_capabilities_without_section_templates design.test_maas_geometry_language.MaasGeometryLanguageTest.test_frontend_early_typologies_are_typed_executable_chassis_priors`
  both passed in this session.

## 2026-07-31 MASS target-20 smoke continuity checkpoint (r19xx)

Direct user-requested execution was re-run with diagnostic target 20 on real
PNU (neighborhood, recursive-only):

```bash
cd ARR\\backend
$env:MAAS_ALLOW_TINY_GEOMETRY_GATES='true'
python manage.py benchmark_maas_book_program_portfolios --diagnostic-target 20 --smoke --program neighborhood --recursive-only --output-dir tmp_mass_check/subagent-run-20smoke
```

Observed result:

- Runtime: ~27 minutes
- Status: `completed_with_failed_gate` (non-fatal; diagnostic-only path)
- `selected_mass_count`: 5
- `program_passed_count`: 37
- `selection_target`: 10 (smoke)
- `minimum_count` requirement: 10
- `selected_scope_count`: 3 / `required_scope_count`: 6
- Failure reasons persisted in `maas-book-programs-summary.json`:
  - `selected_count_below_minimum_10`
  - `base_volume_scope_count_below_6`
  - `diagnostic_only_not_portfolio_acceptance`
- Evidence outputs present:
  - `tmp_mass_check/subagent-run-20smoke/maas-book-neighborhood-20-smoke.png`
  - `tmp_mass_check/subagent-run-20smoke/maas-book-programs-summary.json`
  - `tmp_mass_check/subagent-run-20smoke/maas-run-state.json`
  - `tmp_mass_check/subagent-run-20smoke/maas-geometry-mutation-outcome-graph.json`

Speed decomposition from this run:

- Candidate-generation and replenishment are the bottleneck; `final_gate` appeared only
  after the multi-minute generation loop.
- Throughput in the run hovered around ~15–20 evaluated candidates/min initially,
  then flattened under tighter compile/geometry gate pressure as compile count
  saturated before final selection.
- The failure is not random runtime flake; run-state shows repeated progress to
  128 evaluated candidates (first run), then completion with low final scope coverage.
- Most wall-clock is deterministic geometry/legal projection and hard-gate filtering,
  not startup / I/O.

A second attempt with explicit budget scaling was started to test whether widening
diagnostic budget helps selection feasibility:

```bash
$env:MAAS_DIAGNOSTIC_BUDGET_SCALE='3'
```

That attempt reached >20 minutes in `phase=candidate_generation` with
`selected_mass_count=0`, `evaluated_count=~552`, `compiled_count=227`,
`program_passed_count=173`, then was terminated to avoid unbounded wall-clock.

This confirms that budget scaling alone does not solve the 6-scope minimum bottleneck
in the current diagnostic target-20 path.

Immediate non-breaking next step:

- In diagnostic-only mode, compute required scope minima from available scope supply
  (`min(6, available_scope_count)`) or temporarily set scope minima to 0 when raw
  scope coverage is insufficient for a witness board.
- Keep all law/capacity/parking and authored-identity hard gates untouched; adjust
  only witness/selection policy and rendering policy in diagnostic mode.
- Add a dedicated diagnostic witness board (including reject tags) for non-contract
  states so visual review can run while contract remains strict.

## Read this first

This is the active recovery authority for the interrupted creative MASS
session. It overrides any interpretation that production generation should
select one of fifteen named recipes, satisfy named-family quotas, or stop at a
pre-legal payload test.

## User intent, stated precisely

Generate a portfolio of materially different architectural solutions while
obeying the real site's law, capacity, floor, and parking constraints.

Triangular/faceted forms, oblique crystals, thin or interlocking discs,
long-span structures, and stepped masses are examples of forms that the shared
geometry language can express. They are possible solutions, not required
families, quotas, or checklist items. Stepped mass is neither forbidden nor
preferred. It is one possible solution like every other form. A portfolio that
collapses into stepped or otherwise near-identical variants is a diversity
failure.

Each candidate must resolve to one connected, watertight, manifold MASS.
Across the portfolio, candidates must be materially different in morphology,
space, silhouette, and architectural organization.

## MASS preview continuity note - 2026-07-31

- `run_book_program_portfolios()` diagnostic probe now accepts
  `diagnostic_target=20` (in addition to `1/2/3`) so a full 20-item preview
  run can be requested for diversity checks without changing the core production
  target contract.
- CLI and verify paths were aligned to that same target set:
  - `benchmark_maas_book_program_portfolios --diagnostic-target` now allows `1,2,3,20`.
  - `verify_single_authority_mass_pnus` allows `1,2,3,20` for command parsing,
    command construction, and result validation.
- In diagnostic mode, portfolio fallback now keeps the best available compatible
  set (including partial cardinality) instead of returning an empty pool when
  exact target cardinality is impossible.
- Quick continuity check used:
  `cd ARR\\backend && python manage.py test design.test_maas_mass_product_evidence.MaasMassProductEvidenceTest.test_diagnostic_target_is_strictly_bounded_and_never_completes_portfolio --verbosity 1`

## Production authoring authority

- The sole seed authority is the canonical `1/1 UnitBox` / BaseVolume.
- Matrix4 and generic typed operations such as clip, circularize, array, CSG,
  bridge, loft, sweep, bend, and related modifiers form one shared geometry
  language.
- The live LLM authors typed `GeometryProgram` ASTs directly from that language.
- Production generation must not ask the LLM to choose a recipe or family ID.
- Existing fifteen-family recipes remain only compiler/operator fixtures and
  regression witnesses. They prove that the language can express those
  constructions; they are not a production generator.
- Family or morphology labels may be attached only after compilation for
  analysis, filtering, and collapse detection.

## Lawful execution order

Use real PNU `1168011800104170004` unless the user explicitly changes the site.

```text
PNU and cited law evidence
-> deterministic site/legal envelope and floor-capacity alternatives
-> parking requirements and precheck
-> live LLM-authored GeometryProgram candidates
-> compiler and connected/watertight/manifold gates
-> legal floor projection, containment, BCR/FAR/height/GFA and parking gates
-> exact final-solid renders
-> mandatory image-backed VLM review
-> typed repair only when explicitly budgeted
-> selector and immutable accepted evidence
```

Law, parking, geometry, and numeric solvers own hard-pass authority. VLM judges
the rendered architectural result, diversity, coherence, program fit, and
visible failure modes; it cannot override a failed legal or geometry gate.

A non-stepped authored solution may not be silently rewritten into generic
stepped floor prisms during legal projection. Preservation failure must reject
the candidate or request a typed repair.

### Latest floorwise projection correction - 2026-07-31 16:20 KST

Applied in the massing pipeline:

- The legal projection branch now treats `floorwise_source_to_geometry_program`
  as **intentional-step-only**.
- For non-stepped authored `GeometryProgram`s, if
  `select_legal_field_affine_projection` fails, the candidate is rejected
  immediately instead of being re-synthesized as floorwise unioned slabs.
- This is to prevent the visible stair-step collapse that was seen in
  `r183-outcome-hardpass-22.png`, while preserving an explicit stepped path for
  programs that include intentional operators (`setback`, `stepped_mass`, or
  `terrace`).
- The same principle is now encoded as acceptance logic; a candidate can still
  pass only when it preserves authored mass identity through exact legal projection,
  or gets rejected and repaired.

## VLM and cost contract

- VLM review is mandatory for any final accepted claim.
- The VLM must receive the exact final legal geometry image and matching
  program/geometry/legal identity hashes.
- Retrieval is not VLM review. A reference is `used_by_vlm=true` only when its
  exact image was submitted.
- The first live pilot has a hard ceiling of 20 paid provider requests in
  total, including LLM authoring, VLM reviews, and any explicitly approved
  repair.
- Prefer one structured LLM batch author request for the candidate set.
- Use cache first, disable automatic retries, record every response ID and
  usage, and stop when the ceiling is reached.
- Do not spend the unused budget merely to reach 20. Twenty is a ceiling, not a
  quota.

## Current truthful state at interruption

- The generic UnitBox operators and fifteen regression recipe witnesses exist.
- Recipe-independent authored-program ingestion and research-bundle persistence
  are implemented.
- The last verified author mode was `payload`, not live LLM.
- Current paid author request count is 0.
- Current paid VLM request count is 0.
- The current creative-100 command is explicitly pre-legal and records
  `legal_review=not_evaluated`; it cannot by itself satisfy this pilot.
- No live, lawful, VLM-reviewed diverse-20 result exists yet.

### 2026-07-31 selection continuity checkpoint

- The 20-candidate diagnostic selection path had a hard block: fallback logic
  relaxed contract fields (distinct/copy caps) but still reused the compatibility
  matrix and key caps built from the strict contract, so `target=20` frequently
  stayed at 0/low cardinality.
- Patch applied in `portfolio_selection._select`:
  - `build_compatibility_analysis` now uses target-aware silhouette distance.
  - Joint payload and compatibility matrix are now built through helpers that
    accept an explicit active contract.
  - In `allow_diagnostic_fallback`, the second solve pass rebuilds payload,
    compatibility, and key caps from a relaxed contract (target 20 specific):
    exact/minimum capacity-band quotas disabled, diversity minimums reduced, and
    pair-distance loosened.
  - This keeps strict 20-card production contract unchanged, while the diagnostic
    fallback can still return a usable wide set when strict contract is
    over-constrained.

### 2026-07-31 subagent handoff: diagnostic preview contract hardening

- Confirmed and fixed `portfolio_selection._select` NameError risk:
  `portfolio_contract_preview_recovered_count` referenced `joint_selected`
  before assignment. It now uses `len(joint_indices)` consistently.
- The target-20 diagnostic fallback path now has a third preview branch when
  both strict and relaxed exact contracts return empty:
  - `diagnostic_preview_contract` is built from the relaxed contract.
  - strict scope/copy/pair constraints are removed for witness recovery.
  - `solve_maximum_compatible_subset(..., required_coverage_tags=())` can return
    a partial or full 20-card witness without changing the strict production
    contract.
- Added regression test:
  `test_target_20_diagnostic_preview_contract_retrieves_maximum_cardinality`
  in `ARR/backend/design/test_maas_book_language.py`.
- Verification command run:
  `cd ARR/backend && python manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_target_20_diagnostic_preview_contract_retrieves_maximum_cardinality`
  passed with status OK.

### 2026-07-31 smoke-mode continuity checkpoint

- Fixed a behavior where `--diagnostic-target` implicitly turned on `--smoke` in
  `benchmark_maas_book_program_portfolios`.
- `smoke_mode` now depends only on explicit `--smoke`; setting
  `--diagnostic-target 20` can now run with full 20-candidate diagnostic
  behavior.
- `verify_single_authority_mass_pnus` continues to build benchmark commands with
  explicit diagnostic target and leaves smoke off unless no target is provided.


Do not describe the current state as product completion. The active work is to
join the already-existing law/parking execution authority to recipe-independent
live LLM authorship, then run a bounded image-backed VLM pilot.

## Acceptance and failure rules

The pilot succeeds only when:

- production authoring uses no recipe/family selection;
- candidates come from one canonical UnitBox/BaseVolume language;
- every surviving candidate passes exact geometry and real-PNU legal/parking
  hard gates;
- the surviving portfolio is materially diverse rather than parameter noise;
- no one morphology, including stepped mass, becomes the universal result;
- the VLM actually reviews the exact final legal visual evidence;
- all identities, response IDs, request counts, costs, and artifacts are
  persisted without overclaiming unreviewed candidates.

The pilot fails if named-form coverage is treated as a quota, if all solutions
collapse into a repeated form, if legal projection destroys authored identity,
if law/parking remain `not_evaluated`, or if VLM review is skipped.

## Live recovery checkpoint — 2026-07-30 17:47 KST

This section supersedes the earlier interruption counters above.

- A live LLM author cache contains two recipe-independent typed ASTs from one
  structured response: `llm_translate_courtyard` and `llm_bend_lift`.
- The LLM author response ID is
  `resp_0db697c82d12db73006a6b03796ff4819896c14aece38c38d0`.
- The runtime now keeps `llm_author_only` supply separate from the deterministic
  universal form bank and does not overlay a BOOK recipe on an LLM-authored
  body.
- Floorwise legal materialization now permits legal underfill and rejects only
  overfill. Capacity/yield remains measured and may remain an advisory miss;
  maximum legal capacity is not a statutory minimum.
- Direct-LLM projection evidence is accepted when the final exact legal bridge
  is materialized. A missing BOOK selector node is not grounds to reject an
  authored AST that was intentionally not overwritten by a recipe.
- The achieved-capacity semantic identity now names
  `below_feasible_minimum` without treating it as a capacity hard pass. This
  prevents a blank-label hash mismatch while preserving the yield warning.
- For the real PNU, one `llm_bend_lift` candidate passed exact compile, program
  gate, shared-floor contract, live PNU law, geometry retention, semantic
  binding, and parking. Its achieved GFA was about `145.14 m²` against the
  `299.089 m²` target and `332.322 m²` feasible maximum, so it remained a
  low-yield diagnostic candidate.
- The exact final legal four-view image was submitted to the live VLM once in
  run `docs/mass/maas-lawful-live-llm-vlm-20260730-26`.
- Final VLM response:
  `resp_0ca5f26a6e44d870006a6b0f6c5978819bb9bb98644a4f8682`.
- The VLM rejected the candidate for low hierarchy/program appropriateness,
  failed program fit, unresolved public threshold, and a weak entrance
  sequence. Critic actions included `too_box_like` and `needs_carved_void`.
- Direct image inspection confirmed the user's warned failure: the authored
  `bend/lift` relation collapsed during legal execution into a generic
  stepped/tiered/pyramidal stack. This candidate is rejected evidence, not a
  MASS candidate to present as accepted.
- The `llm_translate_courtyard` sibling still fails directed legal
  materialization before law/VLM.
- No candidate from this recovery is accepted yet. Do not render or report the
  run-26 stepped form as a successful alternative.

### Highest-priority next fix

The final legal projection must preserve a continuous non-stepped authored
solid as a continuous exact manifold. Per-floor occupancy/GFA evidence may be
derived by slicing that solid, but the renderer/VLM geometry authority must not
be rebuilt as visibly separated or terraced floor prisms. If an authored form
cannot be legally projected without identity collapse, reject it and request a
typed AST repair; never silently replace it.

After this is fixed locally, rerun the two cached LLM ASTs through exact
compile/law/parking. Spend another paid VLM call only on a visibly
identity-preserved legal result.

### Paid-call accounting caution

The run-26 exact candidate VLM call is confirmed as one new paid request.
Earlier interrupted attempts include cached, rejected, and possibly attempted
author/VLM requests whose exact total was not persisted by the old process
contract. Treat the previously estimated cumulative upper bound plus run-26 as
the safety authority and remain below the original ceiling of 20. Do not infer
that an empty author-cache directory proves no HTTP attempt; external-author
errors with zero valid programs currently lose their status from candidate
notes and need explicit request-level diagnostics.

## Exact replay and actual ArchDaily VLM checkpoint - 2026-07-30 18:35 KST

This section is the newest recovery authority and supersedes the older
`current truthful state` counters above.

### Non-negotiable product intent

- Diversity is the goal under law. A stepped candidate may appear as one
  solution, but a stepped-only portfolio is a product failure.
- Triangle, disc, interlocking plate, long-span, courtyard, bent bar, and other
  morphologies are optional outcomes of the shared language, never quotas.
- Every production candidate starts from the one BaseVolume / `1/1 UnitBox`.
  The LLM authors a typed `GeometryProgram` from generic operators. Production
  may not select a named family or recipe.
- Final candidates must be connected, watertight, manifold, legal for the real
  PNU, capacity-valid, floor-valid, parking-valid, and reviewed by VLM using
  the exact final legal render.
- Legal projection must preserve the authored form. If filling capacity turns
  a prismatic/bent form into an unrequested stepped or pyramidal stack, reject
  it; never count it as a successful repair.

### Local zero-cost candidate evidence

Cached AST replay and deterministic gates used zero new provider requests.
The relevant results were:

- `cut_corner + courtyard`: authored legal identity and parking passed, but
  the U-shaped arms violated the 2.4 m shared-floor clear-depth minimum.
- `bent_bar + notch`: initial exact GFA was about `221.269 m2`, below the
  `232.625 m2` minimum. A deterministic capacity refit approached the target,
  but the legal projection became an unrequested stepped/pyramidal fallback
  and failed identity preservation.
- `twist + notch`: exact GFA was about `201.596 m2`; it also needed mechanical
  parking review and looked like a stepped/pyramidal cake stack.
- `scale + carve_void`: exact final GFA was about `136.847 m2`, so it failed
  capacity despite a valid repaired numeric mesh.
- `setback + courtyard`: degenerate stepped/pyramidal morphology; rejected.

Do not weaken clear-depth, capacity, legal identity, manifold, or parking gates
to increase the count.

### One new paid VLM call with actual ArchDaily images

Exactly one new candidate-VLM request was made for this checkpoint. Automatic
retries were disabled and the local request budget was hard-set to one.

- Result:
  `docs/mass/maas-lawful-explicit-replay-20260730-51/vlm-actual-critique.json`
- Candidate render:
  `docs/mass/maas-lawful-explicit-replay-20260730-51/exact-final-legal-mass.png`
- VLM response:
  `resp_0b63d731f9506d4c006a6b209cb140819895df2ad5c9b94dc7`
- Candidate image SHA-256:
  `849d67992ededcf3c10d1c64df046d0ba52672090f02ac53aef3413e2b1b2acf`
- Program hash:
  `0ebe6cb5ba3b0da641cf04fd0ad967da548608ebe107a5b51e38d1c61fce4972`
- Geometry hash:
  `ee6f2fca747a4d397d320d74bd2c7471463f19b091eb2080cb5e1275dce79e37`
- Paid budget evidence:
  `limit=1`, `request_count=1`, `remaining_count=0`,
  `candidate_vlm=1`, `total_tokens=9109`.

The exact submitted reference images were:

1. `archdaily_876220`, Dongyuan Qianxun Community Center / Scenic
   Architecture Office, role `similar`, SHA-256
   `994f85d2001d1becbed7c5793d5f1ed0030e494541672fa116e1f4eef315110a`.
2. `archdaily_945744`, Cube Gallery / CLOU Architects, role
   `counterfactual`, SHA-256
   `5ebb6d41564266dc7f5d5b1238869bde6ccf4bb856f82502035796e0f4035939`.

Both reference records say `used_by_vlm=true` and carry the same response,
program, and geometry identity as the candidate.

The VLM rejected the candidate with `program_fit_hard_pass=false`. Its critic
actions were `needs_clean_anchor`, `needs_carved_void`,
`weak_form_continuity`, `too_box_like`, and `wrong_program_typology`. The
visible bent bar was coherent as one mass, but too sealed and terraced, lacked
a convincing west/public threshold, and did not form an active
neighborhood-commercial base. This is rejected diagnostic evidence, not an
accepted MASS.

### Cost and next-action guard

Recent recovery authoring used seven bounded text-author requests before these
zero-cost replays; older historical totals remain imperfectly persisted. This
checkpoint adds exactly one VLM request. Do not infer that the cumulative
historical total is eight.

Make no further paid call until a locally verified candidate passes exact
geometry, PNU law, capacity, shared-floor, authored-identity, and parking
gates and has a visibly non-collapsed final render. The next author/replay
target should be a compact, high-yield, non-stepped AST with a legible west
public threshold and useful carved void.

For a named cached AST replay, use:

```text
MAAS_GEOMETRY_AUTHOR_REPLAY_CACHE_PATH=<author-cache.json>
MAAS_GEOMETRY_AUTHOR_REPLAY_PROGRAM_NAME=<exact cached program name>
```

The final-book VLM cache is:

```text
ARR/backend/docs/ai-session-memory/reference-corpus/final-book-vlm-cache/eadec4a73ddd7d770f2761eaf15617bff2394b14c52e0b7e7fdd6ba1515f4324.json
```

## Latest 20 visible MASS supply checkpoint - 2026-07-30 19:45 KST

The earlier two-image result was not evidence that millions of alternatives
had failed. Runs 37-65 were bounded diagnostic replays with
`diagnostic_target=1|2`, one parent page, one cache program selected by name,
and no rejected-candidate render persistence. Across those runs only 30
candidate evaluations occurred.

The candidate-supply and visibility path now has an explicit zero-paid
`cache_pool` author mode:

- it reads only accepted `arr.maas.geometry_llm_author_cache.v3` records;
- it parses exact `compiled_programs`;
- it normalizes every program to one canonical `1/1 UnitBox` authority;
- it rejects disconnected, non-watertight, non-manifold, no-UnitBox, malformed,
  rejected-cache, duplicate-program, and duplicate-geometry entries;
- it never falls back to named recipes;
- it writes individual renders, research bundles, and a 5x4 board for twenty.

The verified artifact is:

```text
docs/mass/maas-latest-20-cache-pool-20260730/maas-creative-board.png
```

Board SHA-256:

```text
de1fda0be3e415edc40a8f784b642edfd83d3060be199eea8d3c93cf65b27d6d
```

Verified evidence:

- candidate count: 20
- unique program hashes: 20
- unique geometry hashes: 20
- connected/watertight/manifold: 20/20 for all three
- distinct operator signatures: 19
- board layout: 5 columns x 4 rows, 1500x1000 PNG
- paid author requests: 0
- paid VLM requests: 0
- legal status: `not_evaluated` for all 20

Post-hoc morphology counts are
`compact-low=7`, `compact-mid=5`, `linear-low=4`, `bridge-mid=1`,
`bridge-low=1`, `curved-low=1`, and `curved-tall=1`. These labels are analysis
only and did not select recipes.

This board solves the immediate supply/visibility failure, not the lawful
acceptance goal. It is a truthful pre-legal choice pool. The next phase must
route these exact identities through the existing real-PNU law, capacity,
shared-floor, parking, authored-projection, and bounded image-backed VLM
gates. Rejected candidates must remain visible with their failure status.

Implementation authority:

```text
ARR/backend/design/maas/creative_program_author.py
ARR/backend/design/management/commands/generate_maas_creative_100.py
docs/superpowers/specs/2026-07-30-latest-20-mass-board-design.md
docs/superpowers/plans/2026-07-30-latest-20-mass-board.md
```

## Active competition-grade pivot - 2026-07-30 after 20-board review

The user directly reviewed the 5x4 board and ruled that hash/operator
uniqueness is not enough. The target is now a competition-grade portfolio:
twenty architectural strategies for the same real parcel, not twenty
normalized sculptures.

Non-negotiable interpretation for the next session:

- Every comparison board must visibly use the same PNU
  `1168011800104170004`, the same parcel frame, road/access orientation, and
  legal buildable field. A PNU string stored in JSON is not proof that the
  geometry was generated or projected on that parcel.
- The canonical source remains one `1/1 UnitBox` BaseVolume. The next language
  layer must let the LLM derive generic architectural planes and spatial
  relations: extract/section a face or plane, thicken it into a usable plate,
  transform/fold/tilt it, intersect or join plates/discs, carve voids, and
  express slab, wall, roof, bridge, support, and cantilever roles. These are
  typed capabilities, not named architect or building recipes.
- SANAA-, OMA-, Qatar National Library-, and Qatar National Museum-like work
  are range tests for light plate fields, continuous floor-wall-roof sections,
  relational organization, and interlocking disc/plane systems. Never imitate
  a named work and never enforce a named family quota.
- A cube BaseVolume plus affine transforms alone cannot create discs, curved
  sections, or topology changes. Generic `section/circularize/loft/shell-
  thicken/boolean` capabilities must remain available as derived operations
  over the one BaseVolume authority.
- Thin disconnected sculpture, decorative plates, or solids with no usable
  occupied floors are not architectural MASS candidates. Before paid review,
  exact geometry must prove connected/watertight/manifold construction,
  usable floor plates, clear height/depth, vertical circulation feasibility,
  program-area capacity, and non-token spatial volume.
- The zero-paid 20-board run intentionally omitted `--vlm-pilot`; it has no
  visual-quality authority. The existing pilot is opt-in and selects coarse
  morphology-family medoids, which is insufficient for the new spatial goal.
- Paid text LLM authoring is optional because the active AI can author typed
  AST payloads. Paid VLM is mandatory for any visually accepted/final
  candidate. Spend it only after deterministic geometry, parcel, law,
  capacity, floor, parking, and authored-identity gates, but do not skip it.
- Each VLM request must include the exact final legal render and actual local
  ArchDaily reference images. The critic must judge spatialization, occupied
  space, slab/wall/void/threshold/circulation legibility, generic box/step
  repetition, program fit, and reference use rather than silhouette alone.
- Rejected candidates remain visible on the same board with exact failure
  labels. Never present a pre-legal candidate as competition-grade.
- Cost remains bounded: free deterministic gates first, then a small explicit
  VLM shortlist. No automatic retries and no silent paid calls.

Current root cause:

The cache-pool board compiled canonical normalized programs and assigned
prelegal floor targets, but did not place or legally project them on the real
parcel. Diversity selection emphasized hashes, operator signatures, and
coarse post-hoc morphology, so compact box-like solids dominated. The opt-in
VLM stage was not requested. This explains both weak competition character
and the zero VLM count.

Next design task:

Specify one exact-parcel, spatially inhabitable 20-candidate pipeline with a
generic plane-to-thickened-space layer, deterministic spatial-capacity gates,
preserved reject renders, and a bounded image-backed VLM shortlist. Do not
implement until that design is reviewed and approved.

## Paid same-parcel creative-range VLM audit - 2026-07-31 KST

This checkpoint records the user's latest correction and one deliberately
bounded paid visual test in the existing `D:\Data\25_ACE` checkout. No folder
was copied from the spatial-mass worktree.

### Exact product intent

- Keep ordinary lawful BaseVolume-derived masses available. Do not force every
  result to be exotic, curved, long-span, stepped, SANAA-like, or OMA-like.
- The same open language must also be capable of a few competition-grade
  relational candidates using plate, surface, slab, wall, roof, void,
  intersection, overlap, continuous section, and circulation relationships.
- Qatar National Library, Seattle Central Library, SANAA, OMA, and Qatar
  National Museum are capability-range references only. They are never named
  recipes, copies, mandatory families, or portfolio quotas.
- A disc or ellipse with no usable occupied volume is not a MASS. Advanced
  geometry must carry plausible floors, clear height/depth, program area,
  circulation, public threshold, and connected spatial volume.
- A stepped mass remains one valid option. A board dominated by box, gable, or
  code-minimum step variants is a diversity failure even when hashes and
  post-hoc family labels differ.
- Law remains deterministic authority. Use the same PNU, parcel, road/access
  edge, legal field, BCR/FAR/height, capacity, parking, geometry-retention, and
  authored-identity gates before any visual acceptance.

### Existing board audited

The audited board is:

```text
docs/playwright/design-route-live-verify/
book-program-portfolios-r181-bounded-geometry-page-loop-pass/
maas-book-neighborhood-20.png
```

It visibly contains 19 candidates for PNU `1168011800104170004` and one
`NO DISTINCT HARD-PASS CANDIDATE` slot. The existing run records 19/19 legal,
parking, geometry-retention, and combined hard passes, but the final portfolio
status is fail because it reached only 19/20. Direct review shows that the
board is still dominated by compact boxes, gables, and stepped solids. This is
the precise visual-collapse problem; the board is not accepted as a
competition-grade portfolio.

Board SHA-256:

```text
7aad78eed2b2d7e156397a1fb7d8b4d2a642f544cb706d08e14d148468a8bd4d
```

### Exactly one new paid VLM request

One `gpt-5.4-mini` candidate-VLM request was made with automatic retries
disabled and both live/provider budgets hard-set to one.

- Audit:
  `docs/playwright/design-route-live-verify/book-program-portfolios-r181-bounded-geometry-page-loop-pass/maas-paid-creative-range-vlm-audit-20260731.json`
- Response ID:
  `resp_0d8419abad9b8221006a6bf98cfb98819a9d64690019da4454`
- Paid request evidence:
  `limit=1`, `request_count=1`, `remaining_count=0`,
  `candidate_vlm=1`
- Usage:
  `input_tokens=13214`, `output_tokens=461`, `total_tokens=13675`
- Candidate image detail: `high`
- Reference count: `2`; both exact local files have
  `used_by_vlm=true`
- Retry count: `0`

Actual ArchDaily inputs:

1. `archdaily_0006`, Qatar National Library / OMA,
   SHA-256
   `ffaea1357ea01ac45cb07c2564dad4edc617521b0ef9e3dfb02cdee701d714e1`.
2. `archdaily_0001`, Seattle Central Library / OMA + LMN,
   SHA-256
   `8433714f6a2f7518efb4b465d044faf884238923202b1914c7d4043641049210`.

The critic returned `program_fit_hard_pass=false` and low scores for
`gesture_clarity=0.33`, `hierarchy=0.28`, `void_publicness=0.12`,
`precedent_resonance=0.21`, `program_appropriateness=0.18`, and
`section_program_fit=0.16`. Actions included `too_box_like`,
`needs_carved_void`, `weak_primary_mass`, `needs_clean_anchor`,
`too_fragmented`, `wrong_program_typology`, and
`weak_form_continuity`. It found high visible repair integrity (`0.93`) but no
meaningful public ground void, active threshold, or relational occupied
section.

### Audit limitation that must not be hidden

The paid request used the existing per-candidate scorer because it is the
available path that submits actual local reference images in the same HTTP
request. Its fixed prompt calls the first image a four-view candidate, while
the supplied image is a 19-candidate portfolio board. The response therefore
described a representative compact block rather than reliably enumerating all
19 siblings. Treat the call as valid evidence that the VLM received and
compared the exact board and references, and as confirmation of the visible
box/void/section deficit. Do not treat it as a complete per-card portfolio
ranking, and do not spend a second request to correct it. Before the next paid
portfolio audit, the board-specific scorer must accept reference image inputs
and bind board/run identity explicitly.

### Next generation directive

Spend zero additional paid requests now. Generate and hard-gate candidates
locally on the same parcel. Keep the normal BaseVolume/solid lanes, but open
generic relational operations as optional outcomes:

```text
BaseVolume
-> section/host face/derived surface
-> thicken into inhabitable slab, wall, roof, or shell
-> transform/fold/tilt/loft/sweep/circularize
-> intersect/join/bridge/carve while preserving one connected manifold
-> prove occupied floor schedule, clear height/depth, circulation and capacity
-> preserve authored identity through real-PNU law and parking projection
-> retain both passes and rejects with exact reasons
-> build one same-site 20-card PNG
-> shortlist only deterministic survivors for bounded VLM
```

Do not require a named morphology count. Diversity selection must measure
spatial relations and architectural organization, not merely operator,
program, geometry hashes, roof labels, or silhouette labels.

## Zero-paid Matrix4 relational MASS PNG checkpoint - 2026-07-31 KST

The user approved the integrated board-scorer approach with a cheaper visual
review contract: generate and hard-gate twenty locally, then submit at most
three survivors as one contact-sheet request rather than three separate VLM
calls.

The BaseVolume affine contract is now executable and tested:

```text
one normalized 1/1 UnitBox
-> explicit persisted homogeneous Matrix4
-> evaluated block/slab/bar/tower BaseVolume
-> optional topology-changing operations
```

The prior `scale` shorthand for affine base seeds now persists as an explicit
`matrix4` node. This does not claim Matrix4 can create discs, shells, voids, or
intersections. Those remain typed operations after the evaluated BaseVolume.

Implementation commit:

```text
3583047 feat(maas): render Matrix4 relational MASS shortlist
```

Zero-paid artifacts:

```text
docs/playwright/design-route-live-verify/maas-relational-shortlist-r1/
```

- Twenty-card PNG: `maas-same-site-20.png`
- Twenty-card SHA-256:
  `532ed5ee3b1c315af37cacbc7f2032cd5208cfa43acdf3cee0092f5cbaa5312e`
- Three-card PNG: `maas-vlm-shortlist-3.png`
- Three-card SHA-256:
  `921e9d95e5db13a4054a2ab0358a60e937c2baa30a4e7e6475899e5b0c7d729a`
- Machine manifest: `manifest.json`
- Exact GeometryProgram JSON count: `20`
- Compiled count: `20/20`
- Connected component count: `1` for every compiled candidate
- Paid provider requests: `0`
- Shortlist IDs: `mass-19`, `mass-17`, `mass-15`

The visible portfolio contains ordinary solids, bent and swept bars, L/U/cross
plans, courtyard, bridge, step, taper, loft, and one interlocking elliptic
plate system. The continuous-section probe remains visible as `mass-20`, but
it was removed from the paid shortlist because its current narrow strip does
not yet prove adequate occupiable depth. This is the intended behavior:
relational capability is open, not automatically accepted.

The board-specific scorer now accepts exact reference images in the same
request, binds board/reference SHA-256 and response identity, carries candidate
program/geometry hashes, distinguishes a three-card contact sheet from a
single four-view candidate, and supports `expected_candidate_count=3`.
The focused transport and paid-budget tests pass without a network call. The
scorer, global paid-provider guard, and focused tests are committed in the
actual nested ARR repository as:

```text
cbf267d fix(maas): bind references to bounded portfolio VLM
```

The final caller wiring in the already-dirty `portfolio_benchmark.py` working
file was not committed because that file contains more than 1,600 lines of
pre-existing unrelated edits. The scorer itself is committed and callable.

Current truth: these PNGs are normalized geometry-language previews, not
same-parcel legal acceptance. They explicitly say law, capacity, and parking
are not evaluated. The next deterministic step is to project the twenty exact
GeometryProgram identities onto the real PNU buildable field, compute occupied
floor/capacity/clear-depth/circulation evidence, preserve authored identity,
and retain all rejects. Spend one VLM request only if three exact survivors
remain; otherwise spend zero.

## Real-PNU full run r183 and bounded VLM checkpoint - 2026-07-31 KST

The proper command was executed for the real parcel and neighborhood program:

```text
python manage.py benchmark_maas_book_program_portfolios \
  --pnu 1168011800104170004 \
  --program neighborhood \
  --publishable-20 \
  --output-dir .../book-program-portfolios-r183-proper-full-pnu
```

VWorld parcel, land-use, price, adjacent parcel, road, ordinance, sunlight,
setback, parking, floor, capacity and final geometry stages were entered.
Candidate generation itself used zero paid requests. The bounded seven-page
replenishment produced 22 individually observed `combined_hard_pass=true`
candidates.

This is not a successful twenty-MASS portfolio. The final fail-closed solver
selected zero candidates, the exact artifact archive has zero records, and the
official `maas-book-neighborhood-20.png` contains `0/20 floor-verified masses`.
The run failed the publishable contract because the 22-candidate supply could
not satisfy pairwise compatibility, exact capacity-band counts, scope and
body/roof/chassis/plan diversity quotas, shared legal-floor-field selection
identity, and target-20 certification together. Never present the 22 outcome
observations as selected, publishable, or newly law-recertified candidates.

The prior r182 run crashed when one legal floor band contained no replayable
footprint. The exact message
`floorwise volume has no replayable footprint` is now converted to rejection
of that one candidate only; every other `ValueError` still propagates. Focused
TDD is 2/2 passing. In r183 the same bad input occurred four times and all four
were isolated while the run continued through page seven.

The outcome graph retains 22 final floorwise typed ASTs. Its compact AST omits
the fixed `FLOORWISE_CAPACITY_REPLAY_TRANSPORT_CONTRACT`. Restoring that
contract gives 22/22 matching projected program hashes, 22/22 compiled mesh
gate passes, and 14 numeric tiny-edge repairs. The outcome `geometry_hash` is
`final_floorwise_visual_geometry_hash`, while the replay compiler hash is a
mesh hash; these are different hash roles and must not be compared directly.

Exact-program replay evidence:

```text
docs/playwright/design-route-live-verify/
book-program-portfolios-r183-proper-full-pnu/
outcome-hardpass-floorwise-renders/
```

- 22-card PNG: `r183-outcome-hardpass-22.png`
- PNG SHA-256:
  `22cba4da0ac860df1640910bb1f8576ddcd378c6aacd32c9e17969013ff9105e`
- Replay manifest: `r183-outcome-hardpass-render-manifest.json`
- Candidate count: 22
- Projected program hash match: 22/22
- Standalone compilation gate: 22/22
- Numeric transport repair attempted: 14/22
- Source-run selection status: not selected
- Legal and parking recertification during replay: not performed

Why this board looks stepped:

- In this run the exact replay artifact is a **floorwise transport artifact** (`execution_contract_restored_from: design.maas.geometry_language.ast.FLOORWISE_CAPACITY_REPLAY_TRANSPORT_CONTRACT`).
- `candidate_generation.py` follows the legacy fallback branch because `legal_field_selection` is `None`, so `materialize_floorwise_legal_source()` then `floorwise_source_to_geometry_program()` is used.
- `floorwise_source_to_geometry_program()` serializes each legalized floor band as:
  `extruded_polygon -> translate(bottom_fraction * height) -> union`.
- Therefore the final mesh is intentionally a stepped union of flat floor plates, not a single continuous authored volume.
- This is consistent with current code and is not automatically a crash; it should be treated as a **lawful-but-not-desirable visual form** for this board unless the upstream program is proven to preserve non-stepped authored identity.

Hard rule for next recovery:

- If a candidate cannot be preserved as a continuous authored legal solid, it should be rejected (or explicitly resubmitted for repair), not silently accepted as a stepped fallback for final selection.

A three-card visual shortlist was submitted to `gpt-5.4-mini` once at low
detail with the actual Qatar National Library and Seattle Central Library
ArchDaily image files. The paid-provider guard recorded exactly one
`portfolio_vlm` request and no retry:

```text
response_id = resp_0d9bfd302c642410006a6c211eb378819a828fe1576cba6d9f
```

The VLM rejected all three candidates. It found three visible variants but one
dominant bar/box chassis with minor subtraction, weak program-specific
section/threshold language, and family resemblance. It requested courtyard or
attached-volume relations, lifted/cantilevered plates, split bridges, radial
fans, cross masses, terraces and profiled halls as next-run typed anchors.

Identity limitation: the paid request occurred before the omitted execution
contract was restored. Its input board and the exact-program replay board have
four-view dHash distance `0.0013020833333333333`, so the visual conclusion is
useful as a near-identical-board diagnostic, but the response is not exact
program-hash-bound and cannot certify law, parking, selection or acceptance.
No second paid request was made. Read:

```text
maas-paid-3-survivor-vlm-audit-20260731.json
maas-paid-3-survivor-vlm-audit-20260731-identity-note.json
```

Current physical-evidence boundary: the full pipeline proves occupied
floorwise polygons, floor support, clear-depth checks, GFA/FAR/BCR and parking
calculations for candidates that reach the corresponding gates. It does not
yet physically prove a constructed vertical core, egress route or room-level
program packing. Do not describe those as solved.

The 22-to-zero selection is intended fail-closed behavior, not a MILP solver
crash. All 231 candidate pairs were evaluated; 181 pairs failed the composite
gestalt threshold and the proven maximum compatible subset size was four.
The achieved capacity-band supply was only `5/2/1/6` plus eight unclassified,
while the publishable contract requires exact `5/5/5/5` and all twenty
classified. Scope supply was `5/2/4/5/4/2`, which also cannot satisfy three to
four examples in every one of six scopes.

One classification bug was exposed but is not the whole blocker. The final
floorwise transport AST contains mainly floor plates, translations and a
union, so reading semantic design concept and chassis from that transport AST
collapsed all 22 to `direct_edge` and `recursive_chassis:unclassified`. The
authored semantic AST is still preserved in the outcome graph. The smallest
safe code boundary is to make only design-concept and chassis classification
read the validated authored semantic payload; morphology, plan and visual
distance must continue to read the final certified mesh. Do not weaken the
solver, pair threshold or publishable contract. Even after that metadata fix,
replenishment must receive achieved-band, scope and novelty deficits or the
twenty-candidate portfolio will remain impossible.

Next action: repair supply and selection semantics so at least twenty
compatible candidates can be certified without loosening law or disguising
bar/step repetition. Keep ordinary BaseVolume outcomes, but make plate, slab,
wall, void, bridge, courtyard and intersection relations survive legal
projection as genuinely different occupied architectures.

## 2026-08-02 MASS morphology-preservation checkpoint

Scope for this checkpoint is MASS only. ElevationAgent, facade imagery and
frontend elevation presentation are deferred.

Baseline commits created before the new fix:

- `0dc31b7 chore(maas): checkpoint recent mass pipeline work`
- `f41e304 chore(repo): exclude nested elevation agent checkout`

Confirmed root cause:

- `run_book_program_portfolios(..., diagnostic_target=...)` automatically set
  `MAAS_ALLOW_VISIBLE_STEP_FALLBACK=1`.
- `_materialize_directed_geometry()` converted that environment setting into
  `enforce_morphology_preservation=False` when affine legal placement failed.
- Floorwise replay transport could therefore replace a non-stepped authored
  body with translated floor extrusions and still enter diagnostic flow.
- The authored silhouette threshold was `0.85`, while existing contract tests
  require distance `0.41` to fail and `0.3577` to remain admissible.

Implemented bounded correction:

- Diagnostic target sizing no longer injects
  `MAAS_ALLOW_VISIBLE_STEP_FALLBACK`.
- Authored-to-legal morphology preservation is non-bypassable for final MASS
  identity. The old compatibility argument cannot disable the gate.
- A projected `visible_step_fallback=true` is rejected for non-step authorship
  even if the old environment variable is externally set.
- Intentional step operators remain admissible:
  `book_grade`, `setback`, `stack`, `stepped_mass`, `terrace`.
- Maximum authored/projected intrinsic silhouette distance is `0.40`.

TDD evidence:

- New RED run: 2/2 tests failed for the expected automatic environment
  injection and morphology-bypass reasons.
- GREEN focused run: 6/6 passed, covering diagnostic environment isolation,
  non-bypassable identity, unrequested step rejection, intentional step
  acceptance, void morphology retention and per-candidate unreplayable-floor
  rejection.
- Test module added:
  `ARR/backend/design/test_maas_diagnostic_morphology_policy.py`.

Known separate stale-test conflict, not changed here:

- `test_other_floorwise_replay_value_error_still_aborts` expects `None`, while
  its name and production policy say non-whitelisted `ValueError` must
  propagate. Resolve that contract separately rather than weakening this fix.

Honest boundary:

- No target-20 portfolio was regenerated.
- No claim is made yet that final certified supply is diverse.
- Next checkpoint audits the actual scheduling ratio between ordinary
  rectilinear UnitBox-derived MASSes and bounded triangular, elliptical/disc,
  oblique and interlocking outcomes without loosening law, capacity or parking.

### 2026-08-02 read-only supply scheduling audit

- `generate_maas_creative_100` and the real-PNU BOOK benchmark use different
  supply paths. The former uses `balanced_family_schedule()`; the latter uses
  `universal_form_program_pages()` plus `staged_principle_schedule()`.
- Creative-100 currently balances all fifteen named diagnostic families almost
  equally. For 100 records it schedules each ordinary family 7 times and each
  of triangular shard, oblique crystal, thin-disc cluster, interlocking discs
  and long-span bridge 6 times. The five special families therefore occupy
  30%, which is higher than the intended low-rate capability sampling.
- Real-PNU page zero currently has 82 parents. It has no
  `triangular_shard`, `thin_disc_cluster`, `interlocking_tilted_discs` or
  equivalent canonical UnitBox-derived low-rate parent.
- `universal_form_bank_contract()` advertises triangular and oval profiled
  prism capabilities, but `universal_form_programs()` rejects every synthesis
  record whose sole primitive is not exactly canonical `box(1,1,1)`.
  Consequently those advertised profiled-prism seeds do not enter the actual
  PNU candidate supply.
- This filtering is correct for singular BaseVolume authority. The required
  correction is not a second triangle/ellipse primitive authority; it is a
  small number of canonical UnitBox programs that derive triangular/oblique
  shape through typed `clip` and elliptical/disc shape through typed
  `circularize`, then continue through BOOK operations and legal projection.
- r318 selected 5 diagnostic candidates: all five are `base_operative`; three
  final bodies are stepped, one voided and one prismatic. Combination,
  aggregation and case-study selected counts are all zero. All five chassis
  classifications are `recursive_chassis:unclassified`.

Next bounded implementation target:

- Add four canonical UnitBox-derived low-rate capability parents to the actual
  universal form bank page zero: triangular clip, oblique clip, elliptical
  circularize and interlocking circularized plates.
- Four parents among the current 82 gives approximately 4.7% special parent
  supply before hard gates. This is a capability range, not a final portfolio
  quota and not a named-building recipe.
- Test canonical UnitBox lineage, operator presence, deterministic hashes,
  compile/manifold evidence and bounded parent percentage before running any
  portfolio.

### 2026-08-02 low-rate UnitBox capability supply implemented

Implemented in the actual real-PNU parent source rather than only the separate
creative-100 gallery:

- `rare_unitbox_capability_programs()` adds exactly four generic page-zero
  parents:
  - `unitbox_triangular_clip`
  - `unitbox_oblique_clip`
  - `unitbox_elliptical_volume`
  - `unitbox_interlocking_elliptical_volumes`
- Every program contains exactly one primitive authority:
  `box(width=1, depth=1, height=1)`.
- Proportion and placement use Matrix4. Topology change uses typed `clip`,
  `circularize`, `matrix_array` and `union` operations.
- No named architect/building metadata, parcel coordinates or final-family
  selector quota was added.
- Universal form-bank page zero increases from 82 to 86 parents. Special
  capability supply is exactly `4/86 = 4.651%` before BOOK, legal, capacity,
  parking and VLM gates.

TDD and compile evidence:

- Initial RED: focused module failed because
  `rare_unitbox_capability_programs` did not exist.
- First GREEN attempt exposed a test-contract error: compiler connectivity is
  `component_count == 1`, not a nonexistent `connected` metric. Production
  programs had already compiled; the test was corrected to the real metric.
- Focused capability plus existing strict UnitBox operator suite: 12/12 pass.
- All four programs compile with `component_count=1`, `watertight=true`,
  `manifold=true`, deterministic distinct program hashes and required typed
  operators.

Remaining boundary:

- This proves real form-bank parent admission and compiler validity only.
- It does not prove survival through five-floor authoritative plates, exact
  PNU legal projection, FAR, parking, final selection or VLM.
- The next small checkpoint should run these four identities through the cheap
  BOOK screen and deterministic legal/floor preflight without running the full
  target-20 portfolio.

## 2026-07-31 target-20 diagnostic continuity checkpoint (r318)

- Command family:
  - `python manage.py benchmark_maas_book_program_portfolios --pnu 1168011800104170004 --program neighborhood --output-dir .../book-program-portfolios-r318-neighborhood-target20-smoke-fix --diagnostic-target 20 --smoke`
  - same command without `--smoke` in `.../r318-neighborhood-target20`
- Environment for both runs:  
  `MAAS_BOOK_SMOKE_REPLENISHMENT_CYCLES=2`, `MAAS_BOOK_REPLENISHMENT_CYCLES=2`,
  `MAAS_BOOK_NONLIVE_REPLENISHMENT_CYCLES=2`,
  `MAAS_ALLOW_VISIBLE_STEP_FALLBACK=1`,
  `MAAS_ALLOW_TINY_GEOMETRY_GATES=1`,
  `MAAS_RELAX_BOOK_FINALIZATION_GATE=1`.

Observed completion states:

- both runs: `selected_count=5`
- smoke run: `selection_target=10` and `portfolio_requirement.minimum_count=10`
- non-smoke run: `selection_target=20` and `minimum_count=10`
- both: `selected_scope_count=4` vs `required_scope_count=6`
- both: `status=completed_with_failed_gate`
- both: portfolio failures include `selected_count_below_minimum_10`,
  `base_volume_scope_count_below_6`, `diagnostic_only_not_portfolio_acceptance`.

Evidence files:

- `.../book-program-portfolios-r318-neighborhood-target20-smoke-fix/maas-run-state.json`
- `.../book-program-portfolios-r318-neighborhood-target20/maas-run-state.json`
- `.../r318-neighborhood-target20-smoke-fix/maas-book-neighborhood-20-smoke.png`

Root-cause hypothesis for repeated “4-scope only”:

1. `resolve_portfolio_requirement` still enforces `required_scope_count=6` for
   the real base scopes, and diagnostic completion checks keep this minimum in both
   smoke and non-smoke 20-target runs.
2. `_select` diagnostic fallback for `target>=20` still sets
   `base_scope_minimum_each=1`, so the solver still requires at least one candidate
   in every configured base scope before a 20-card contract can be satisfied.
3. Selection supply after gates reached `selection_pool_count=95` with `evaluated_count=128`,
   so this is not generator starvation; it is selection-policy feasibility.

Recommended next step (non-breaking, diagnostic-only):

- In diagnostic/fallback path, compute required scope minima from available scope
  supply (`min(6, available_scope_count)`) or set scope minima to 0 for target20
  diagnostic when insufficient raw scope coverage exists.
- Keep law/capacity/parking hard gates untouched; only adjust selection/diagnostic
  witness policy.
- Consider adding an explicit “diagnostic witness board” path that renders top-20
  non-rejected candidates with reject reasons when strict portfolio gate is not met,
  so visual review can continue while preserving strict contract boundaries.

### 2026-07-31 2차 조치 - staircase fallback 하드 스탑 적용

- 적용 파일: `ARR/backend/design/maas/book_language/candidate_generation.py`
- 변경 핵심:
  - `legal_field_selection is None` fallback 경로에서
    `_authored_projection_identity_evidence(..., enforce_morphology_preservation=...)`
    를 고정 `False`에서 `not _allow_visible_step_fallback()`로 변경.
  - 기본은 `False`(fallback 허용 아님)로 동작하여 비의도적 계단형 재구성을 차단.
  - 사용자가 명시적으로 `MAAS_ALLOW_VISIBLE_STEP_FALLBACK=1/true/yes/on`을
    주지 않는 한, 비계단형 저자 형상을 계단형으로 변형해 통과시키지 않음.
- 검증:
  - `python -m py_compile backend/design/maas/book_language/candidate_generation.py`
    통과.
  - 해당 모듈만의 단독 pytest는 현재 세션에서 Django 설정 미설정으로 불가
    (`DJANGO_SETTINGS_MODULE` 필요).
- 즉시 후속 확인:
  - 동일 조건 재생성에서 `r183-outcome-hardpass-22`와 같은 렌더가 계단형이면,
    해당 후보의 `authored_projection_identity`에서 `status`, `failure_reasons`,
    `visual_certificate.visible_step_fallback`를 우선 점검.
  - `visible_step_fallback=true`이며 authored가 비계단형이면 현재 설정 오차 또는
    이전 코드 경로 잔존 가능성이므로 즉시 폴백 경로 단일 추적이 필요.
