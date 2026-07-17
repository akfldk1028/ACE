# MAAS BOOK executable-language checkpoint — 2026-07-15

## Why this checkpoint exists

The Mass-Brain activation UI incorrectly placed seven coarse
`formalStrategy` buckets (`preserve/carve/step/bend/bridge/cluster/fold`) under
`02 PRINCIPLE`. Those buckets are search/grouping labels, not the architectural
principles in the architect-supplied BOOK. `69 pages` was also a provenance
count marked pending, not proof that 69 pages were active in generation.

## Direct source-page verification

The original scans, not OCR alone, establish this hierarchy:

1. **Operations**
   - Add: single 3, multiple 4
   - Displace: single 4, multiple 7
   - Subtract: single 8, multiple 4
   - Total base operatives: 30
2. **Combinations**: 20 repeated/mixed two-operation sentences.
3. **Aggregations**: Reflect, Pack, Stack, Array and Join applied to operations;
   the supplied pages contain nine explicit recipes.
4. **Case studies**: real projects use compound operations, not a single label.

The case-study pages were visually checked and must retain these compound
languages:

- 60 Poli House: `Carve + Offset`
- 61 Villa 1: `Embed + Branch`
- 62 Casa para un Carpintero: `Embed + Overlap`
- 63 House N: `Expand + Nest`
- 64 House in Minamimachi 2: `Overlap + Expand`
- 65 Nursing Home: `Bend + Shift`
- 66 Leimondo Nursery School: `Embed + Taper`
- 67 Gouveia Law Courts: `Lift + Carve`
- 68 Carabanchel Housing: `Lift + Extrude`
- 69 Ironbank: `Overlap + Rotate`

Do not collapse those examples to `offset`, `branch`, `overlap`, etc.

## Implemented contract

- `book_language/registry.py` is the canonical page/principle taxonomy.
- Every one of the 69 pages retains page number, checksum, OCR, section and
  principle references.
- Page records, executable principles and case evidence are different object
  types even when their counts happen to resemble one another.
- Principle states are `typed`, `compile_tested`, or `active`. Only compiler
  evidence with non-zero 2.5D geometry delta and clean-mass pass may be active.
- All 30 BOOK base verbs are first-class members of the executable vocabulary.
- Missing operations are implemented through normalized, parcel-derived
  kernels in `source_geometry/operative_kernels.py`; no named precedent or raw
  parcel coordinates are encoded.

## Honest verification state

The canonical four-site audit now compiles and clean-gates all 30 base
operations on rectangular, narrow, trapezoid and concave sites. Promotion is
evidence-derived, not a manually edited count:

- `expand` is a real sectional expansion: compact ground plate to full upper
  plate. The former outward-scale-then-clip no-op is gone.
- polygon cleanup can no longer simplify across a concave parcel corner and
  enlarge the permitted envelope. This fixed the `extrude` containment leak.
- `extract` and `puncture` retain legible polygonal voids while remaining under
  the clean surface budget.
- `merge` is one fused body; its input units are not duplicated as extra review
  solids, avoiding the Lego-fragment regression.

This 30/30 result proves base-operator compiler coverage only. It does **not**
prove 20-combination generation quality, program fit, law/FAR/parking retention,
VLM preference quality or competition-grade visual design.

## UI correction completed

`02 PRINCIPLE` must render the BOOK hierarchy:

`Operations -> Combinations -> Aggregations -> Case-study compound languages`

The seven formalStrategy buckets remain only as a separate search filter. The
API/UI now reconcile 69 pages, 30 base operations, 20 combinations, nine
aggregation recipes and ten case-study evidence records. Runtime browser
verification shows metrics `69 / 30 / 20 / 9 / 30 / 0`, all 30 real operative
labels, all ten compound case labels, no Vite overlay and no console errors.

Presentation/runtime evidence:

- `docs/mass-brain-book-principles-30-active-20260715.png`
- `http://127.0.0.1:5210/`

The Playwright fixture previously reused `architect-book-69` and could
overwrite the live corpus when a dev server was reused. It now writes
`architect-book-69-test` and opens `?corpus=architect-book-69-test`; production
continues to default to the canonical ID.

Mass-Brain verification passes typecheck, 13 core tests, build, dist smoke,
debug build, browser smoke and `npm audit` with zero reported vulnerabilities.

## Next implementation order

1. Generate and select 20 candidates from the full BOOK graph distribution;
   prove measured plan/section/volume distance rather than label diversity.
2. Run the same 20-candidate contract for neighborhood living, gym and cultural
   programs, then inspect all PNGs.
3. Project the accepted creative sources through the same-run legal/FAR/parking
   hard gates and measure geometry retention.
4. Profile/async-bound the current neighborhood 20-language search. Its full
   benchmark exceeds the present 240-second test limit; it must not become a
   synchronous request path.
5. Keep Mass-Brain shadow-only until a controlled ON/OFF run changes final
   accepted geometry and improves blind visual preference without gate loss.

## 2026-07-15 full-grammar and live-program correction (latest; supersedes older counts above)

The BOOK evidence is now represented as six p.3 relative base volumes (`1/1`,
`3/8`, `1/2`, `1/4`, `1/8`, `1/16`), 30 base operations, 20 combinations,
nine aggregations and ten case studies. Each base operation has diagram-derived
input/output topology, a three-stage procedure, orientation modes and bounded
variation axes in `book_language/semantics.py`.

The four-site audit now executes all 59 operation/combination/aggregation
principles, not only the 30 base verbs. All 59 pass measured non-zero 2.5D
delta, parcel containment, <=5 volumes and <=48 effective surfaces. Aggregation
display order and execution order are separate: BOOK `Reflect | Expand` is
compiled as `Base -> Expand -> Reflect`.

Mass-Brain runtime now shows `69 pages / 6 base volumes / 30 base operations /
20 combinations / 9 aggregations / 59 active / 0 pending` on one complete
taxonomy board. Verified screenshot:

- `docs/mass-brain-book-full-grammar-20260715.png`

This is compiler coverage, not design completion. A bounded live-VWorld PNU
benchmark applies all 59 sentences to neighborhood, gym and cultural program
anchors and selects by pose-invariant top/front/side silhouette distance.
Latest honest one-probe result after relational-body preservation:

- neighborhood living: 16/20, 13 distinct BOOK principles, 13 visual languages — fail.
- gymnasium: 16/20, 8 distinct BOOK principles, 12 visual languages — fail.
- cultural: 20/20, 20 distinct BOOK principles, 19 visual languages — numerical
  pass, but direct PNG review remains conservative/box-like and not competition-grade.

The three-program run evaluates 531 program/principle combinations in about 95
seconds. Increasing seed probes from one to two took about 216 seconds and
returned the same 16/16/20 counts, so it was reverted. Do not repeat blind
search expansion. The program projection formerly erased every relational
secondary result by retaining only one largest projected volume. It now retains
up to two for multi-volume operations within the <=5-volume global budget while
preserving service/entry/public program roles. A regression test proves
`Expand -> Reflect` retains two primary bodies plus gym service and entry roles.

Evidence paths:

- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-cultural-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-summary.json`

Critical remaining BOOK gap: the six p.3 volumes are real corpus records but
are not yet materialized as a selected sub-volume inside the program dominant
mass. The current operation still receives the dominant component as a whole.
Next implementation must add typed graph scope:

`program dominant -> BOOK base-volume scope -> orientation -> operation -> variation`

It must define add/displace/subtract composition against the host and prove all
six scopes create real geometry deltas without weakening parcel, program or
clean gates. Do not claim the BOOK is fully active in generation until this
scope node exists. Law/FAR/parking remains `not_run` in this diagnostic.

## 2026-07-15 p.3 scope and neighborhood 20/20 correction (latest; supersedes the gap above)

The p.3 relative-volume gap above is now implemented. `select_book_scope`
materializes all six fractions (`1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`)
in a principal-axis frame, supports long-axis, short-axis and vertical scope,
clips safely to oblique/concave hosts, and records a typed projection graph:

`program dominant -> select_book_scope -> ordered BOOK operations`

All four neighborhood-living seeds now enter the same data-backed program
assembly/projection path. The assemblies are normalized role graphs with
bounded coordinate/height/rotation mutation, not parcel coordinates or named
precedent copies. Targeted scope/program regressions: 8 tests pass.

Latest live VWorld PNU `1168011800104170004` result:

- neighborhood living: 20/20, 20 BOOK principles, 20 visual-language keys,
  all six p.3 scopes, zero near-duplicate silhouette pairs.
- gymnasium: 13/20, eight BOOK principles, 11 visual-language keys, five of
  six scopes; `1/16` has zero program-hard-pass candidates.
- cultural: 20/20, 20 BOOK principles, 20 visual-language keys, all six scopes.

Overall status remains **fail** because gym is 13/20. Direct PNG review also
shows strong family resemblance and conservative box/terrace relatives; this
is not competition-grade completion. Law/FAR/parking is still not run in this
diagnostic. Next work: diagnose gym spatial-hard-gate failures and expand the
long-span hall section/roof graph, then project accepted sources through the
same-run legal/FAR/parking hard gates.

Latest evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-cultural-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-summary.json`

The active Codex session began repeatedly returning `{"detail":"Bad Request"}`
after very large context/image/tool traffic. Mass-Brain port 5210 and VWorld
both returned HTTP 200, so treat this as session transport instability, not a
MAAS runtime failure. Continue in a fresh session from this checkpoint.

## 2026-07-15 gym section graph, 60/60 numeric pass, and legal-retention audit (latest; supersedes the 13/20 state above)

The gym shortfall has been measured by hard-gate and scope, then corrected by
geometry rather than threshold relaxation. The benchmark summary now records
`role_coverage`, `dominant_ratio`, `site_coverage`, `hierarchy`, and
`coherence` failures for every p.3 scope, including exclusive failures,
failure signatures, and metric distributions. On the latest gym population,
233 clean candidates yield 64 program-hard-pass candidates. Total failed-gate
incidence is role coverage 77, dominant ratio 53, site coverage 26, hierarchy
1, and coherence 109. The difficult `1/16` scope now has two hard-pass
candidates; among its 31 clean candidates, remaining failures are primarily
coherence 25 and role coverage 19, followed by dominant ratio 4. No program
hard-gate threshold was loosened.

Gym section and roof language is now a bounded typed graph. Nodes include
`long_span_hall`, `ridge_roof`, `folded_roof`, `sawtooth_roof`,
`stepped_section`, `service_spine`, `carved_entry`, `entry_canopy`, and
`daylight_monitor`; edges use `input`, `deform`, `attach`, `subtract`, and
`monitor`. BOOK operations mutate normalized graph controls and the compiler
materializes planar roof strips, facades, and subtractive entry evidence on the
actual parcel-derived footprint. Six data-backed gym assemblies cover ridge,
ridge plus monitor, folded service hall, sawtooth daylight hall, stepped
section, and carved-entry ridge hall. No PNU coordinate or completed-building
template is embedded.

Latest live VWorld PNU `1168011800104170004` BOOK/program diagnostic:

- neighborhood living: 20/20, 18 distinct BOOK principles, 13 measured visual
  languages, all six scopes, zero near-duplicate silhouette pairs.
- gymnasium: 20/20, 15 distinct BOOK principles, 16 measured visual languages,
  all six scopes, zero near-duplicate silhouette pairs. Six roof/section
  families are selected; the largest seed and section-family shares are both
  0.25, with 17 distinct section-control signatures. Mean clean complexity is
  3.75 visible volumes and 19.70 effective surfaces.
- cultural: 20/20, 12 distinct BOOK principles, 17 measured visual languages,
  all six scopes, zero near-duplicate silhouette pairs.

The clean-mass contract remains `visible volume <= 5` and
`effective surface <= 48`. Projection evidence must be materialized; a seed
fallback cannot enter the accepted portfolio. Selection explicitly anchors all
six scopes, limits seed/section-family repetition, and retains the silhouette
distance gate.

Cross-program geometry descriptors are now included in the summary. Mean
cross-program silhouette distance is 0.4579 for neighborhood/gym, 0.4507 for
neighborhood/cultural, and 0.4803 for gym/cultural. Roof/section-family Jaccard
distance is 1.0, 0.8333, and 1.0 respectively. These numbers prove program
language separation only at the diagnostic descriptor level; they do not
override visual review.

Direct inspection of the three original-resolution 20-mass boards and the
combined 60-mass board remains **fail**. Neighborhood still repeats elongated
bars and folded terrace cascades. Gym roof/section variation is materially
better, but a low rectangular long-span hall chassis repeats. Cultural still
repeats low stepped gallery bars and compact stacked boxes. Therefore
`architecture_grade_claim_allowed` is false and the 60-mass set is not yet
competition-grade.

The exact accepted source objects are now sent to a same-run legal/FAR/parking
hard-gate evaluator; geometry is not regenerated. Live PNU evidence is
`제2종일반주거지역`, BCR 60%, FAR 250%, adjacent setback 0.5 m,
landscaping 15%, one road frontage, four neighboring parcels, and a
materialized sunlight envelope. The local structured parking rules are used
when Neo4j enrichment is not requested, so this diagnostic remains runnable
with Neo4j off and uses no synthetic site fallback.

Post-projection legal metrics pass 60/60, but this is not a successful design
result: legal clipping destroys too much of every accepted source. Geometry
retention passes 0/60 at the unchanged requirements of volume retention >=
0.80 and weighted plan IoU >= 0.75. Mean retained volume is 0.5648 for
neighborhood, 0.5456 for gym, and 0.5117 for cultural. Parking passes 18/20,
18/20, and 20/20; the four failures require driveway-connectivity review.
Combined legal + retention + parking pass is therefore 0/60. Overall benchmark
status remains **fail**, even though the BOOK/program numeric counter is
60/60.

Latest evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-cultural-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-60-summary.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-visual-review.json`

Regression verification on this state: 23 BOOK/scope/Mass-Brain tests and six
targeted program-massing tests pass. JSON parsing and Python byte-compilation
also pass.

Next work must generate inside the legal/sunlight/parking envelope before
portfolio selection, not rely on destructive post-selection clipping. Add the
driveway/access graph as a typed mutation input, then improve gym chassis,
neighborhood spatial typology, and cultural gallery typology under stronger
visual-family clustering. VLM remains a critic/reranker and typed graph-edit
director; it is not a direct geometry generator. Mass-Brain/GRL remains a
shadow lane until final accepted geometry improvement is proved.

## 2026-07-16 recursive solid integration and 60/60 correction (latest; supersedes the visual/retention failure above)

The Extended Geometry Language is now the dominant-source authoring path for
this diagnostic. Five normalized seed priors (`block`, `slab`, `bar`, `tower`,
`profiled_prism`) feed bounded recursive AST synthesis. The first four are
scaled forms of the same unit Box; they are search priors, not extra kernel
primitives or completed building templates. Program profiles or a typed VLM
directive provide intent tags and role-graph lineages. They do not provide
parcel coordinates or finished mass recipes.

The executable path is now:

`program role graph -> normalized base seed -> bounded recursive operators -> BOOK p.3 scope -> BOOK principle -> compiled manifold -> program/clean gate -> same-source legal/FAR/parking gate -> selector -> outcome graph`

The portable outcome graph stores genotype, BOOK principle, scope, program
failures, legal retention and selection observations. It can optionally mirror
to Neo4j, but the PNU benchmark remains runnable with Neo4j off. Graph memory
reorders already typed fit strengths and BOOK neighborhoods; it cannot author
or relabel geometry by itself.

The default profile inference now searches up to 12 candidates per role
lineage and always includes a topology-preserving `calm_prismatic` control.
This prevents profiles containing only cut/setback preferences from collapsing
the whole population into wedge or terrace relatives. For the reviewed PNU,
each program uses two role lineages with 24 bounded candidates each. These are
`base_seeds + intent_tags + maximum_operator_depth` requests, not hard-coded
completed forms.

Latest live VWorld PNU `1168011800104170004` recursive run (`r32`):

- neighborhood: 20/20, 19 BOOK operations, 13 visual-language keys, six
  scopes, zero near-duplicate pairs; phenotype distribution curved 1,
  oblique 2, prismatic 2, stepped 5, voided 5, winged 5.
- gymnasium: 20/20, 18 BOOK operations, 11 visual-language keys, six scopes,
  zero near-duplicate pairs; curved 4, oblique 1, prismatic 5, stepped 2,
  voided 4, winged 4. Three degenerate sheet-like candidates were rejected
  before final selection.
- cultural: 20/20, 17 BOOK operations, 17 visual-language keys, six scopes,
  zero near-duplicate pairs; curved 3, oblique 3, prismatic 2, stepped 4,
  voided 5, winged 3.

All 60 exact accepted source objects pass the same-run legal, FAR, parking and
geometry-retention hard gates. Mean retained volume is 0.8892 neighborhood,
0.9036 gym and 0.9321 cultural; the minimum selected retention is 0.8004. No
threshold was loosened. The clean contract remains visible volumes <=5 and
effective surfaces <=48, with an additional rejection for disconnected
components below 8% of total volume and measured degenerate sheet/spike forms.

Direct inspection of all three full-resolution PNGs records
`procedural_mass_diversity_pass`: the previous box-only, gable-only and
terrace/wedge collapse is no longer present. Gym is the longest-plan program
(mean oriented aspect 2.1086), neighborhood mixes street/court/wing languages,
and cultural has the richest selected visual-language count (17). This is a
geometry-language and hard-constraint diagnostic pass, **not** proof of a
competition-ready building. `architecture_grade_claim_allowed` remains false
until site planning, circulation, structure, facade and performance are
evaluated.

Latest standard evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-neighborhood-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-cultural-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-60-summary.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios/maas-book-programs-visual-review.json`

The live OpenAI VLM was deliberately not called. A key pasted into chat is
compromised and was neither stored nor used; it must be revoked and replaced
through a secure environment variable. Stored typed VLM/session directives
were applied deterministically. VLM remains a critic, reranker and typed
graph-edit director rather than a direct mesh generator.

## 2026-07-16 ArchDaily + live-VLM + outcome-graph causal loop r33 (latest; supersedes r32 counts and visual verdict)

The three previously separate capabilities are now one executable causal
contract:

`program genotype -> automatic ArchDaily retrieval (similar + counterfactual) -> rendered candidate + editable geometry graph + prior outcome neighborhood -> VLM typed node edits -> semantic validation -> recompile -> geometry-hash change -> clean gate -> outcome graph observation -> next genotype query`

Automatic retrieval reads the local ArchDaily corpus (274 unique projects and
338 image files at this checkpoint) from intent tags, base seed, operator path
and building type. It does not retrieve parcel coordinates or copy a completed
building. The VLM receives up to five image-backed references, including a
counterfactual formal principle and explicit session references when present.

`GeometryOutcomeGraph.agent_neighborhood()` now supplies exact-genotype prior
successes, failed program/legal gates, fit strengths and BOOK principles to the
critic. `observe_vlm_loop()` records the critic model/response identity, typed
edits, reference IDs, parent/child program hashes, parent/child geometry hashes
and whether compiled geometry actually changed. Neo4j remains an optional
mirror; the portable graph is authoritative for this diagnostic. The standard
r33 graph contains 6,619 nodes, 18,953 edges and 6,113 observations.

The closed path is regression-tested with an injected VLM callback: an
ArchDaily-backed request proposes a typed taper node, the AST and compiled mesh
hashes both change, the child passes the clean gate, and the response/reference
and `vlm_revised_to` edge are queryable in graph memory. No synthetic score is
used in the PNU artifact. The real OpenAI VLM remains **not run** because the
only known key was pasted into chat and is compromised. Live execution now
requires both `MAAS_LIVE_GEOMETRY_VLM=1` and explicit
`MAAS_LIVE_VLM_CREDENTIAL_ROTATED=1` confirmation with a rotated key supplied
through the process environment. Never reuse or paste the old key.

p.3 scope and base shape remain separate axes. The six fractions (`1/1`,
`3/8`, `1/2`, `1/4`, `1/8`, `1/16`) clip the available starting extent. Five
semantic base priors (`block`, `slab`, `bar`, `tower`, `profiled_prism`) define
starting proportion/section. Block/slab/bar/tower are non-uniform transforms of
one unit Box and are deliberately distinct agent-readable seed nodes; a `1/16
slab` and `1/16 bar` therefore compile to different geometry.

The selector now solves scope and measured phenotype anchors jointly before
greedy novelty filling. This fixed a reproducibility failure in which a valid
hard-pass oblique gym candidate existed in the bounded pool but was discarded
after scope anchors. No threshold was relaxed and no oblique completed form was
hard-coded.

Latest real PNU `1168011800104170004` deterministic r33 run:

- neighborhood: 20/20, 20 BOOK principles, 16 measured visual languages, six
  scopes, zero near-duplicate pairs; curved 4, oblique 1, prismatic 6, stepped
  2, voided 5, winged 2.
- gymnasium: 20/20, 18 BOOK principles, 19 measured visual languages, six
  scopes, zero near-duplicate pairs; curved 1, oblique 2, prismatic 6, stepped
  4, voided 2, winged 5.
- cultural: 20/20, 19 BOOK principles, 16 measured visual languages, six
  scopes, zero near-duplicate pairs; curved 2, oblique 1, prismatic 6, stepped
  5, voided 3, winged 3.
- legal/FAR/geometry-retention/parking combined hard pass: 60/60. Mean volume
  retention is 0.9034, 0.9214 and 0.9181; selected minimum is 0.8026.
- live-VLM causal trace counts in this PNU artifact are all zero and the status
  explicitly says the opt-in was inactive. Do not attribute r33 geometric
  improvement to a live OpenAI call.

Direct inspection of the three r33 original-resolution PNGs gives a split
verdict. Procedural mass diversity passes and the earlier gable-only collapse
is gone, but architecture-grade and cross-program differentiation fail. Low
prismatic/chamfer/terrace relatives still recur between neighborhood and
cultural; their minimum cross-program silhouette distance is 0.0283. Gym has
long-span, winged, stepped, court and oblique bodies, but some bars still read
as generic clipped sheds. `architecture_grade_claim_allowed` remains false and
the overall summary is deliberately `fail` after applying the current visual
review fingerprint.

Stale visual reviews can no longer silently overwrite a new run. The review
must carry the exact selected-source/scope/phenotype fingerprint or it is
reported as ignored.

Verification on this state: 51 geometry/BOOK/scope/Mass-Brain tests and the
three targeted program-massing tests pass. The full PNU benchmark completed
twice during this correction (first exposing the missing gym oblique, then
passing numeric/hard constraints after the joint selector fix).

## 2026-07-16 unified opaque solid preview r34 (latest; supersedes r33 render/counts)

The apparent disappearance of the gym gable and the mixed solid/wireframe
portfolio were a renderer defect, not a missing section graph. The preview had
three geometry paths with incompatible material contracts:

- recursive kernel mesh faces used alpha 255;
- program-section gable/fold/sawtooth/step faces used alpha 150;
- ordinary `mass_volumes` prism sides/top used alpha 105/185.

Rear faces therefore showed through program-section and ordinary volume
candidates. `feature_preview_png()` now applies one depth-ordered, world-normal
shaded, alpha-255 material to all profiled surfaces and ordinary prism faces.
Typed patch and triangle edges remain in the graph/JSON and are no longer used
as a competing X-ray visual language. Direct inspection of the regenerated
60-board confirms that every candidate is rendered as an opaque solid. The gym
portfolio contains one measured `gable_ridge`, one `folded`, one
`barrel_vault`, and one `stepped` roof/section family; the gable is present and
readable.

Latest real VWorld PNU `1168011800104170004` r34 run, with the existing clean
and hard thresholds unchanged:

- neighborhood: 20/20, 19 BOOK principles, 14 visual languages, six scopes,
  zero near-duplicate pairs; curved 1, oblique 2, prismatic 6, stepped 4,
  voided 4, winged 3.
- gymnasium: 20/20, 18 BOOK principles, 16 visual languages, six scopes, zero
  near-duplicate pairs; curved 1, oblique 3, prismatic 6, stepped 2, voided 4,
  winged 4.
- cultural: 20/20, 20 BOOK principles, 15 visual languages, six scopes, zero
  near-duplicate pairs; curved 1, oblique 1, prismatic 5, stepped 5, voided 4,
  winged 4.
- combined legal/FAR/geometry-retention/parking hard pass: 60/60. Mean volume
  retention is 0.8931, 0.9253 and 0.9213; selected minimum is 0.8026.
- portable outcome graph: 8,570 nodes, 24,806 edges and 8,064 observations;
  Neo4j mirror disabled, portable graph available.
- live OpenAI VLM revision was not run for this fingerprint. Stored typed
  directives and outcome graph memory were active, but they are not evidence
  of a live model call.

The direct visual verdict remains **fail** for architecture-grade completion.
The unified renderer fixes the misleading representation, but low
box/chamfer/terrace relatives still recur between neighborhood and cultural.
Their mean/minimum cross-program silhouette distances are 0.3599/0.0707.
Gym is more program-distinct (long bars and authored roof sections), but clear
span structure, daylight, entry/service circulation and spectator section are
still unverified. The summary deliberately records numeric/hard-gate pass and
overall visual-design fail separately.

Verification on r34:

- renderer material + gym ridge + six gym section-family targeted tests: 3/3
  pass;
- actual VWorld PNU benchmark completed twice while closing both alpha paths;
- Django `design` full suite: 473 tests, 455 pass and 18 pre-existing contract
  failures. The failures include legacy legal selection expectations, genome
  role/name drift, creative-count expectation and a stale VLM contract-version
  assertion; do not call the repository full suite green;
- `land` app-label discovery timed out after 15 minutes, while explicit
  `ZoningMapperTest` passed 9/9;
- `law` has one import error (`agents.law` missing), and the three explicit
  parser tests cannot import `rest_framework` in this environment;
- `gemini`, `agents`, `core` and `graph_db` app labels discover zero tests;
  `agents` discovery also attempts an unnecessary Neo4j connection.

Latest evidence remains the three program PNGs, combined 60 PNG, summary JSON
and fingerprint-matched visual review JSON in
`docs/playwright/design-route-live-verify/book-program-portfolios/`.

## 2026-07-16 live ArchDaily/VLM control-lane and measured-section correction r38 (latest; supersedes r34 live status and counts)

The OpenAI live geometry critic was run with an environment-provided rotated
credential; no key value is stored in the repository or artifacts. The full
PNU run proves that actual image-backed ArchDaily references were supplied to
the VLM, not only text labels. Each response received up to five retrieved
`similar`/`counterfactual` images. The portable graph contains reference nodes
for ArchDaily IDs `0001`, `0002`, `0006`, `0007`, `0008` and API item
`1042923`, together with critic response IDs, typed edits, parent/child hashes
and `vlm_revised_to` edges.

Two causal defects were corrected without relaxing hard thresholds:

1. An explicit VLM/session `geometry_synthesis_request` previously replaced
   the program-profile inference lane. In the live gym run this erased the
   deterministic hard-pass oblique/winged control population. Profile control
   requests and VLM requests are now additive and are recorded as
   `program_profile_control+vlm_or_session_directive`. A regression test proves
   that a narrow VLM request cannot remove the profile lane's `split_wing` and
   `shear`/`slice` capabilities.
2. Visual morphology measured only `profiled_recursive_solid_mesh` faces.
   Executable legacy/program section graphs therefore appeared as generic
   prisms, while carved, multi-component or high-normal-count solids could be
   exempted from wedge/pyramid repetition. The classifier now reads compiled
   roof graph operators (`flat`, `gable`, `shed`, `folded`, `barrel`,
   `sawtooth`, `stepped`) and applies silhouette convergence tests without
   topology exemptions. The maximum phenotype count is also a final failure
   condition rather than a best-effort selector preference.

The gym `split_wing` macro also gained an optional normalized low ground
service spine while retaining its upper bridge. This reconnects long-span
wings as one occupiable program relation instead of disconnected Lego pieces.
The recursive mesh-to-source bridge now quantizes adjacent triangle-section
intersection endpoints before polygonization; this removes approximately
1e-12 endpoint drift that silently discarded lower/middle mesh bands and
collapsed source footprint coverage. No parcel coordinates or completed
building template were added.

Latest full live VWorld PNU `1168011800104170004` run (3,578.1 seconds):

- neighborhood: 20/20, 15 BOOK principles, 16 measured visual languages, six
  scopes, zero near-duplicate pairs; curved 3, oblique 1, prismatic 6,
  stepped 1, voided 6, winged 3; wedge 2, pyramid 2. Live VLM completed 65
  candidates with 15 compiled geometry revisions and at most five references.
- gymnasium: 20/20, 12 BOOK principles, 19 measured visual languages, six
  scopes, zero near-duplicate pairs; curved 3, oblique 6, prismatic 4,
  stepped 4, voided 2, winged 1; wedge 1, pyramid 2. Live VLM completed 68
  candidates with 14 compiled geometry revisions and at most five references.
- cultural: 20/20, 18 BOOK principles, 16 measured visual languages, six
  scopes, zero near-duplicate pairs; curved 2, oblique 1, prismatic 5,
  stepped 4, voided 4, winged 4; wedge 3, pyramid 2. Live VLM completed 68
  candidates with 15 compiled geometry revisions and at most five references.
- the exact 60 selected sources pass legal, FAR, geometry-retention and
  parking gates 60/60. Mean retained volume is 0.8427 neighborhood, 0.9377
  gym and 0.8701 cultural; minimum selected retention is 0.8026.
- the accumulated portable outcome graph now has 18,877 nodes, 55,186 edges
  and 16,903 observations. Across accumulated live critic observations it has
  659 unique `gpt-5.4-mini` response IDs, 1,983 typed geometry edits and 229
  records with `geometry_changed=true`. Neo4j remains disabled and is not
  required for this diagnostic.

Direct original-resolution review is deliberately split from the numeric
result. Gym is measurably program-distinct from both other programs: its
neighborhood/gym and gym/cultural mean silhouette distances are 0.4564 and
0.4823, with roof-section Jaccard distances 0.8 and 0.7778. Neighborhood and
cultural remain too similar: mean/minimum silhouette distance 0.3532/0.0732,
roof-section Jaccard distance 0.3636 and dominant-ratio delta 0.0015. Their
compact courtyard, chamfer and terrace families recur despite different BOOK
labels. The fingerprint-matched visual review therefore sets overall status
to **fail**, while `book_program_numeric_status` and
`downstream_hard_gate_status` remain **pass**. `architecture_grade_claim_allowed`
is false.

This run proves that ArchDaily images, the live VLM, typed graph mutations,
portable graph memory and downstream hard constraints all execute in one
pipeline. It does **not** prove that VLM caused a better final accepted
portfolio. The next correction must make the VLM review the final
BOOK-projected/legal-retained board (not only the pre-BOOK recursive program),
emit typed population feedback, and author genuinely different neighborhood
street/tenant/public-ground graphs versus cultural gallery/logistics/daylight
graphs. Do not address the remaining failure by weakening similarity or hard
constraint thresholds.

Verification on r38:

- geometry-language plus BOOK-language tests: 41/41 pass;
- geometry-language plus three targeted program projection tests: 33/33 pass;
- actual live PNU gym runs and the final three-program live run completed;
- direct inspection performed on all three original PNGs and the combined
  60-board. The earlier 473-test full-suite result remains 455 pass / 18 known
  failures; do not call the entire repository green without rerunning and
  resolving those unrelated contracts.

## 2026-07-17 program-conditioned VLM and recursive hall checkpoint r53 (latest; supersedes all earlier gym counts)

Overall status is **fail**. This section supersedes the earlier r38 gym 20/20
count. The older result proved that the components executed, but it did not
prove that the VLM reference lane was program-conditioned or that the selected
geometry was visually a credible gymnasium portfolio.

The root cause was traced rather than hidden by relaxing thresholds:

1. Gym references were being retrieved through generic form tags. The live
   reference set could therefore contain houses and libraries even though the
   requested program was a long-span sports hall. Reference contracts are now
   program-conditioned: gym uses the local ArchDaily sports-architecture
   corpus, cultural uses cultural architecture, and neighborhood uses
   cafe/mixed-use material. Each contract carries semantic invariants and a
   hard program-match requirement.
2. A clean compiled candidate could enter the archive even when the VLM said
   that it did not fit the program. Rejected candidates may now remain mutation
   parents, but cannot be final archive members. When live VLM is required,
   final selection accepts only candidates with a live program-fit review.
3. The geometry graph previously mixed body and roof-section appearance into
   one phenotype. It now records body phenotype, section phenotype, roof
   family, chassis family and plan family separately. Protected
   `program_section_invariant` nodes cannot be removed, replaced or rewired by
   a VLM edit; the critic may only wrap them with a valid typed operation.
4. The recursive language gained a normalized `profiled_hall` macro with
   ridge, shed, folded, sawtooth/daylight-monitor, stepped and barrel section
   families. It is applied after bounded body mutation, so the body program and
   long-span section remain independently legible. No parcel coordinates or
   finished-building templates were added.
5. Exact geometry-program/VLM evidence is cached by prompt contract, model,
   program hash, geometry hash, preview hash, program context and reference
   identities. Credentials are not persisted. The cache reduced a repeated
   live run from approximately 1,015 seconds to 357 seconds without replacing
   the live evidence contract.

Latest full live gym PNU `1168011800104170004` run, r53:

- selected: 12/20; numeric status **fail**;
- BOOK principles: 11; visual-language keys: 7; p.3 scopes: 6/6; reported
  near-duplicate pairs: 0;
- body phenotypes: curved 2, prismatic 1, stepped 1, voided 8; required oblique
  body phenotype is absent;
- roof/section families: arched 3, barrel 2, ridge 1, sawtooth 3, shed 3;
- chassis families: bar 9, block 1, slab 2; plan families: bar 11,
  intermediate 1;
- 46 candidates reached legal/geometry-retention hard pass; 39 passed the live
  VLM program review. The visual selector still retained only 12. Of the
  remaining pool, 22 were silhouette conflicts and 16 hit the chassis-family
  cap, proving that the current bottleneck is genuine form convergence rather
  than a shortage of clean or legal candidates;
- the live loop supplied up to five program-conditioned ArchDaily images per
  critic call, used 91 prior graph observations at most, and compiled 20
  geometry revisions;
- the same 12 accepted sources pass legal, FAR, geometry-retention and parking
  hard gates 12/12. Mean retained volume is 0.8864 and minimum retained volume
  is 0.8026. The parking ordinance calculation rounds the small tested floor
  areas to zero required spaces, while layout status remains
  `needs_swept_path_review`; this is not a full parking-layout approval.

Direct original-resolution PNG review remains **fail**. Most candidates now
read as long-span halls, but sawtooth/voided bar relatives repeat. Card 4 is a
triangular/tent-like false positive even though the live VLM scored program
appropriateness 0.82 and section fit 0.80. Its measured upper-area ratio
0.3102, horizontal ratio 0.8257, vertical ratio 0.0060, sloped ratio 0.1683
and 17 horizontal levels exposed the critic false positive. A third measured
tent-collapse condition was added after r53; current code would reject that
candidate, so r53 must not be re-labelled as a current 12-good-design result.
VLM judgment remains critic evidence, not a substitute for mesh-derived hard
gates.

Evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios-r53-live-capability-gym/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r53-live-capability-gym/maas-book-programs-summary.json`

The deterministic r52 capability preflight reached 20/20 with 18 BOOK
principles, 11 visual-language keys, all six scopes and downstream hard gates
20/20. It was intentionally run without live VLM and its PNG still contained
visually questionable triangular relatives. It is useful only as proof that
the compiler and selector have enough bounded capability; it is not final
evidence and must not replace r53.

Verification for this checkpoint:

- `design.test_maas_geometry_language`: 41/41 pass;
- BOOK scope/language plus Mass-Brain tests: 23/23 pass;
- the three requested program-massing projection/role tests: 3/3 pass;
- the latest measured tent-collapse regression passes after the post-r53
  correction.

Next work must preserve the hard thresholds and solve plan/body topology
diversity: produce real winged, lifted, bent and oblique long-span relations
that retain geometry after the legal envelope; calibrate the VLM against the
mesh false-positive cases; rerun live gym until 20 visually credible cases are
available; then rerun neighborhood and cultural together and expose the
reference -> contract -> critic -> typed edit -> child -> hard-gate causal
graph in the frontend. Do not claim competition-grade or commercialization
readiness before those steps pass direct PNG review.

## 2026-07-17 site-feasible recursive authority checkpoint r57 (latest; supersedes r53 gym geometry counts)

Overall status remains **fail**. This checkpoint fixes two causes of misleading
gym geometry, but it is not a competition-design result and it did not run a
new live VLM batch.

Root causes and corrections:

1. Program-body mutations and later BOOK mutations previously accumulated
   without one architectural rule budget. A candidate could therefore combine
   several independently valid effects into layered fins, bands and Lego-like
   masses. One provenance-aware articulation gate now counts body operations
   across both layers, limits the combined body rule count to two and rejects
   repeated structural families such as void+void, step+step, array+array or
   support+support. Roof/section invariants and p.3 scope projection are not
   miscounted as body decoration.
2. When the recursive geometry agent was requested, rejected recursive
   candidates could be replenished by legacy component seeds that never passed
   through the same AST authority. Recursive synthesis/mutation now makes the
   recursive geometry program the only possible final geometry authority;
   legacy program assemblies remain semantic role priors, not completed-form
   fallback templates.
3. The tested PNU has only 102.931 m2 of legal generation host with oriented
   axes 8.009 m x 12.865 m. The former benchmark still requested an 18 m tall,
   three-floor long-span gym, even though the estimated clear-span capacity is
   only 7.368 m. This physical mismatch caused repeated tent/pyramid false
   solutions. Program profiles now carry dimensional requirements. The
   benchmark either selects a feasible subtype or returns program-infeasible;
   it never fills the count with a fake gym. This parcel selects
   `compact_training_hall`, minimum clear span 6 m, effective height 5.894 m
   and two floors. No parcel coordinate or completed building form was encoded
   in the profile.
4. Recursive mesh z values are normalized 0..1. Morphology formerly read this
   as one metre while the render and legal feature used the requested building
   height. Morphology and program-form gates now use the same effective height
   scale, so clear span, solid height, surface normals and height/span ratio are
   evaluated in metres.

Latest deterministic VWorld PNU `1168011800104170004` gym run, r57:

- selected 20/20; 18 BOOK principles; 10 visual-language keys; six p.3 scopes;
  zero reported near-duplicate silhouette pairs;
- recursive geometry authority 20/20; 19 seed lineages and 11 recursive
  geometry families; chassis families bar 9, slab 8 and block 3;
- roof families: ridge 7, shed 4, folded 3, prismatic 2, curved 1, voided 1,
  sawtooth 1 and stepped 1;
- body phenotypes: curved 5, oblique 3, prismatic 3, stepped 1 and voided 8;
  section phenotypes still collapse to only oblique 18 and stepped 2;
- all selected candidates use at most two architectural body rules; mean
  visible volume count 2.15 and mean effective surface count 8.95;
- the same selected sources pass the downstream legal/FAR, geometry-retention
  and parking hard gates 20/20. Mean and minimum volume retention are both
  1.0. The local small-project parking calculation rounds each selected floor
  area below one required stall to zero; layout remains
  `needs_swept_path_review`, so this is not a detailed parking-layout approval.

Direct original-resolution PNG review remains **fail**. The former disconnected
toy fragments and church/tent population are substantially reduced, but the
board converges to low plates, shallow cuts, central holes and roof grooves.
All 20 selected candidates are classified as the same intermediate plan
family, and the two section phenotype families are not enough to communicate
twenty competition-level concepts. The result demonstrates physical and legal
feasibility, not architectural proposition quality.

The r57 directive provider is
`bounded_capability_preflight_not_final_vlm`; `live_geometry_vlm_revision` is
false. Existing program-conditioned ArchDaily/VLM evidence remains available,
but no claim may be made that a new VLM reviewed r57. The next loop must move
site response, public threshold/entry, service access, dominant hall and roof
daylight/structure into a higher-level typed **design-concept graph**, use the
VLM to critique the final BOOK-projected board, and mutate causal graph nodes
rather than merely request additional low-level operators. It must also expand
plan/chassis concept diversity without weakening clear-span, clean-mass or
legal hard gates.

Evidence:

- `docs/playwright/design-route-live-verify/book-program-portfolios-r57-scaled-morphology-gym/maas-book-gymnasium-20.png`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r57-scaled-morphology-gym/maas-book-programs-summary.json`
- `docs/playwright/design-route-live-verify/book-program-portfolios-r57-scaled-morphology-gym/maas-geometry-mutation-outcome-graph.json`

Verification for r57 code:

- `design.test_maas_geometry_language`: 46/46 pass;
- BOOK scope/language plus Mass-Brain tests: 23/23 pass;
- the three requested program-massing projection/role tests: 3/3 pass;
- live VWorld benchmark completed in 452.5 seconds;
- direct original PNG inspection performed; overall design status intentionally
  remains fail.
