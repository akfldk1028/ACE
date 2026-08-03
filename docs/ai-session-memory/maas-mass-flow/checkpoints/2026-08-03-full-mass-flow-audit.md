# Full MASS Flow Audit - 2026-08-03 KST

## Scope

This audit stops patch-by-patch work and reviews the complete MASS path before
another implementation or full run:

```text
BaseVolume / UnitBox / Matrix4
-> deterministic and LLM GeometryProgram/AST seeds
-> BOOK projection and parameter variants
-> compile to SourceMass
-> floorwise legal materialization and typed CSG
-> clean/program/capacity gates
-> lineage and QD archive
-> base VLM
-> legal/GFA/parking downstream gate
-> final exact VLM and typed repair
-> exact portfolio selection
-> final mesh/GFA certification
-> PNG render and portfolio VLM
```

No code was modified during this audit. The findings compare the r182 working
baseline with r334.

## Required Architecture

The intended authority chain remains:

```text
canonical UnitBox
-> Matrix4 BaseVolume, usually near-cubic with low-frequency alternate shapes
-> LLM-authored typed GeometryProgram/AST
-> BOOK typed operations and CSG
-> principal-frame site placement
-> polygon/CSG legal containment by floor
-> actual floor/GFA/parking measurement
-> exact rendered geometry VLM
-> typed AST revision
-> diverse exact selection
```

Matrix4 controls coordinate systems and placement. It does not replace BOOK
boolean, nonlinear, or macro geometry. Law remains hard. VLM judges visual
quality only after exact legal geometry exists. Elevation remains out of scope.

## r182 Versus r334

### r182 working baseline

```text
selected: 20
visible cards: 20
BOOK operations: 14
visual languages: 20
BaseVolume scopes: 6
capacity alternatives: 4
near duplicates: 0
selection raw pool late in run: 499
capacity-pass selection universe: 177
replenishment cycles: 7
```

Typical r182 cycle:

```text
evaluated: about 1,300-1,700
compiled/materialized: about 1,300-1,400
program passed: about 700
lineage retained: about 660-700
```

r182 did not include mandatory final VLM, so it is the geometric diversity and
lawful-supply baseline, not the complete current acceptance contract.

### r334 current flow

```text
LLM parent seeds evaluated: 24
sequence compile succeeded: 24
directed geometry materialized: 9
program hard-pass: 7
post-lineage retained: 4
downstream legal/parking preselection: 3
final exact VLM hard-pass: 1
selection pool: 1
selected/rendered: 1/3
replenishment pool growth: 0
```

The largest absolute loss is directed materialization: `24 -> 9`. The final
cardinality loss is final exact VLM: `3 -> 1`. Between them, lineage identity
collisions incorrectly remove valid supply.

## Critical Findings

### P0-1: Base VLM hard-pass candidates overwrite each other by coarse parent key

`vlm_review.py` converts approved candidates to a dictionary keyed only by
`book_generation_lineage.parent_key`. Distinct BaseVolume/BOOK/LLM exact bases
can share that coarse key, so later candidates overwrite earlier candidates.

r334 evidence:

```text
base VLM hard-pass records: 2
approved base dictionary entries: 1
```

The exact candidate identity must be at least parent lineage plus stable base
review fingerprint, authored program hash, or exact geometry hash. A coarse
lineage name is not a unique geometry identity.

Relevant code:

```text
backend/design/maas/book_language/vlm_review.py:1336
backend/design/maas/book_language/vlm_review.py:1439
backend/design/maas/book_language/vlm_review.py:1482
backend/design/maas/book_language/vlm_review.py:1533
```

### P0-2: Descendants are deleted by key membership, not quality

After the overwrite, descendants survive only when their coarse `parent_key`
is present in the already-collapsed reviewed dictionary. r334 removed all three
descendants even though the base audit had two hard-pass records.

```text
descendant input: 3
descendant released: 0
```

This is an identity projection bug, not a VLM rejection. Descendants must bind
to an exact reviewed base fingerprint. Persisted reviewed bases must release new
descendants without another paid base review.

Relevant code:

```text
backend/design/maas/book_language/vlm_review.py:1457
backend/design/maas/book_language/vlm_review.py:1484
backend/design/maas/book_language/vlm_review.py:1515
backend/design/maas/book_language/portfolio_replenishment.py:433
```

### P0-3: Legal fallback replaces authored MASS with floor-plate stairs

The normal source-bridge path projects the authored exact mesh through floor
Matrix4 transforms. If that fails, the code successively:

```text
clips the profiled mesh
-> lofts legal floor sections
-> rebuilds prisms from floor unions/capacity volumes
-> recompiles that replacement GeometryProgram
-> certifies visible_step_fallback=True
```

The final two fallbacks no longer preserve the authored curved, voided,
cantilevered, elliptical, or oblique mesh. They elevate law-derived floor plates
to visible geometry authority. This directly explains convergence toward the
same stepped/terraced silhouette.

Lawful floor sections may remain capacity authority, but a plate loft/replay
must not silently become the design/render authority. If exact authored visual
projection fails, return typed repair evidence to the LLM/VLM AST loop.

Relevant code:

```text
backend/design/maas/geometry_language/source_bridge.py:700
backend/design/maas/geometry_language/source_bridge.py:714
backend/design/maas/geometry_language/source_bridge.py:752
backend/design/maas/geometry_language/source_bridge.py:788
backend/design/maas/geometry_language/source_bridge.py:814
backend/design/maas/geometry_language/source_bridge.py:865
```

### P0-4: Empty projected artifact can erase valid render surfaces

`portfolio_benchmark.py` first places SourceMass surfaces in the render feature.
If `projected_visual_artifact` is any truthy dictionary, it then clears those
surfaces before iterating projected triangles. A truthy artifact with an empty
triangle list leaves `source_surfaces=[]`, even when exact compilation and the
original SourceMass surfaces are valid.

The renderer receives feature surfaces, not the exact compilation mesh. The
mass-pixel visibility gate runs only after PNG generation, so a blank card is
written first and diagnosed later.

Required behavior:

```text
nonempty certified projected triangles -> replace render surfaces
empty projected triangles -> hard failure or preserve exact certified source
never clear valid surfaces before replacement payload is validated
```

Relevant code:

```text
backend/design/maas/book_language/portfolio_benchmark.py:2337
backend/design/maas/book_language/portfolio_benchmark.py:2467
backend/design/maas/book_language/portfolio_benchmark.py:2531
backend/design/maas/book_language/portfolio_benchmark.py:2573
backend/design/maas/book_language/portfolio_benchmark.py:2861
backend/design/maas/book_language/portfolio_benchmark.py:2928
```

## High-Severity Supply Findings

### P1-1: Directed materialization hides 15 different failures behind one reason

r334 sequence compilation actually succeeded for all 24 evaluated LLM parents.
Only nine survived `_materialize_directed_geometry()`. The public `compiled=9`
counter is misnamed because it increments after materialization, not after
sequence compilation.

```text
sequence_compiled: 24
directed_geometry_materialized: 9
directed_geometry_materialization_failed: 15
```

The generic failure combines BOOK projection, legal section, source compile,
floorwise materialization, authored identity, replay serialization, replay
compile, final identity, and semantic carrier failures. Typed failure evidence
is required before changing any threshold.

Relevant code:

```text
backend/design/maas/book_language/candidate_generation.py:1211
backend/design/maas/book_language/candidate_generation.py:1279
backend/design/maas/book_language/candidate_generation.py:1298
backend/design/maas/book_language/candidate_generation.py:1313
backend/design/maas/book_language/candidate_generation.py:1351
backend/design/maas/book_language/candidate_generation.py:1543
backend/design/maas/book_language/candidate_generation.py:1668
backend/design/maas/book_language/candidate_generation.py:2422
backend/design/maas/book_language/candidate_generation.py:2530
```

### P1-2: Source bridge returns undifferentiated `None` at every authority boundary

`materialize_floorwise_legal_source()` merges all failures into `None`:

```text
missing source floor section
target allocation failure
axis-scale failure
floor affine fit failure
containment failure
visual projection failure
loft/replay compile failure
authority hash failure
final visual/capacity section mismatch
```

The caller therefore cannot distinguish an AST needing a smaller span from a
numeric replay bug or a geometry-authority collapse. It cannot produce useful
typed LLM repair instructions.

### P1-3: Final exact VLM is accepted-only and becomes the authoritative pool

After downstream legal/parking hard-pass, the final VLM function evaluates a
bounded shortlist and returns only VLM hard-pass candidates. The benchmark then
replaces the entire selection pool with that accepted list.

r334:

```text
final VLM input: 3
final VLM hard-pass: 1
selection pool after VLM: 1
```

Unreviewed candidates must not publish, but target cardinality requires enough
review supply and bounded typed repair. A target-3 run cannot be expected to
produce three final passes from exactly three reviews when ordinary visual
rejection is allowed. The review/repair reserve must be derived from target and
observed pass rate, while keeping final publication fail-closed.

Relevant code:

```text
backend/design/maas/book_language/portfolio_benchmark.py:1728
backend/design/maas/book_language/portfolio_benchmark.py:1752
backend/design/maas/book_language/portfolio_benchmark.py:1854
backend/design/maas/book_language/portfolio_benchmark.py:1889
backend/design/maas/book_language/vlm_review.py:930
backend/design/maas/book_language/vlm_review.py:967
backend/design/maas/book_language/vlm_review.py:1114
backend/design/maas/book_language/vlm_review.py:1300
```

### P1-4: Exclusion state removes new descendants, not only duplicate paid reviews

Replenishment passes cumulative reviewed parent keys/fingerprints into the next
base gate. The gate filters the mixed base/descendant pool before persisted
audit reuse. New descendants of an already-reviewed base can disappear before
the cached base decision releases them.

Reviewed, approved, rejected, and paid-review-excluded identities must be
separate sets. Exclusion should apply only to fresh paid base-review requests,
not to descendant generation or persisted-audit release.

## Legal, GFA, Capacity, and Parking Findings

### P1-5: Capacity selection uses two inconsistent authorities

Candidate helpers may trust stale `selectable_capacity_hard_pass` or legacy
`target_hard_pass`, while archive band resolution recomputes a stricter feasible
band from measured utilization. A candidate can pass the selection boolean but
have no resolved capacity alternative.

The same resolved measured-capacity evidence must drive generation counters,
archive descriptors, downstream hard-pass, and final selection.

Relevant code:

```text
backend/design/maas/book_language/candidate_analysis.py:74
backend/design/maas/book_language/candidate_analysis.py:131
backend/design/maas/book_language/candidate_analysis.py:147
backend/design/maas/book_language/mass_passport_bridge.py:394
backend/design/maas/book_language/mass_passport_bridge.py:461
```

### P1-6: Missing final-mesh floor finalization evidence is not fail-closed

The passport bridge returns the existing passport unchanged when finalization
evidence is absent. Invalid present evidence can fail, but completely missing
evidence may survive. Program, final geometry, visual hash, actual GFA stop,
floor count, and target GFA must all be present and bound for publishable MASS.

Relevant code:

```text
backend/design/maas/book_language/mass_passport_bridge.py:156
backend/design/maas/book_language/mass_passport_bridge.py:164
backend/design/maas/book_language/mass_passport_bridge.py:198
```

### P1-7: Visual legal authority and GFA authority are distinct but incompletely joined

The exact visual projection proves visual mesh/legal binding. Capacity plates
remain GFA authority. Candidate analysis verifies exact surface and legal hash
binding but does not remeasure target GFA or partial-floor area from the visible
mesh. Finalization must join these authorities explicitly without treating the
visual certificate itself as a GFA certificate.

### P1-8: Parking is copied into the passport, not recomputed there

The reviewed passport bridge copies `downstream_row.parking_hard_gate`. Parking
losses therefore occur in the external downstream evaluator/combined-hard-pass
filter. The next implementation review must preserve this authority boundary
and add explicit parking attrition counters; it must not infer parking success
from legal or capacity evidence.

## Counter and Observability Defects

The following names currently mislead debugging:

```text
compiled = materialized, not sequence compiled
legal_fit_failure_count = affine miss events, including fallback successes
program_passed_by_* = post-lineage retained candidates
agent_mutated_seed_count = filtered pool minus a fixed base count
universal_form_bank size = theoretical bank, not executed supply
qd_stream_candidates_released = archive event count, not QD output cardinality
```

Every stage must report exact input, pass, fail, and failure reason counts under
stable names. Counters must reconcile arithmetically across stage boundaries.

## Performance Findings

The slow path repeats expensive work:

```text
mesh section reconstruction per floor and again for final verification
multiple containment bisections per floor
clip -> loft -> replay compile sequential fallbacks
full triangle SourceSurface recreation
repeated whole-mesh host containment searches
final VLM on supply already collapsed below target
```

Do not optimize by weakening hard gates. Remove replacement-geometry fallbacks,
cache exact section measurements by geometry/floor identity, stop impossible
candidates with typed reasons, and avoid paid VLM unless enough legal candidates
exist to meet the requested target with repair reserve.

## Corrected Flow

```text
1. Generate exact BaseVolume/LLM/BOOK genotype identities.
2. Compile once and record sequence-compile evidence.
3. Materialize legal geometry with typed result, never anonymous None.
4. Preserve authored visual authority; law plate is containment/GFA authority.
5. If authored projection fails, return typed AST repair instead of plate replay.
6. Run clean/program/capacity gates from one measured authority.
7. QD archive exact identities before review, preserving scopes and morphology.
8. Base VLM indexes exact base fingerprint, not coarse parent key.
9. Release descendants by exact reviewed-base fingerprint.
10. Run legal/GFA/parking combined hard gate with reconciled counters.
11. Review a target-aware final VLM reserve and apply bounded typed repair.
12. Keep only exact VLM hard-pass candidates for publication.
13. Require target cardinality before publish; partial board remains diagnostic.
14. Bind final program, geometry, visual, floor/GFA, legal, and parking hashes.
15. Render only a nonempty certified triangle payload.
16. Run final portfolio VLM with its reserved request.
```

## Implementation Order

No full run should occur between every small edit. Implement and test in this
order:

```text
1. Fix exact base identity maps and descendant release in vlm_review.py.
2. Add typed materialization result/failure evidence across candidate_generation.py and source_bridge.py.
3. Remove floor-plate loft/replay as automatic final visual authority.
4. Fix empty projected artifact surface overwrite before renderer.
5. Unify measured capacity/finalization authority and add parking attrition evidence.
6. Reconcile all stage counters.
7. Add target-aware VLM/replenishment reserve without accepting unreviewed candidates.
8. Run focused tests.
9. Run one target-3 end-to-end test with live VLM and a five-minute ceiling.
10. Accept the result only if three distinct visible legal MASSes render.
```

The first target is not twenty. It is three exact, visibly distinct, lawful
MASSes with no hidden plate-replay replacement and complete VLM evidence.

