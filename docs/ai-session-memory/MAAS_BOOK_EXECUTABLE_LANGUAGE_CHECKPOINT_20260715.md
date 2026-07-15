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
