# MAAS r293 exact replay v6 — solid elevation rendering delta

Date: 2026-07-28

Read the full predecessor first:

`MAAS_R293_V5_AUTHORED_LEGAL_ELEVATION_CHECKPOINT_20260728.md`

This delta supersedes v5 only for elevation PNG rendering and latest replay
identity. The Base Model, BOOK/GeometryProgram AST, legal projection, parking
evidence and certified visual geometry are unchanged.

## User correction

The v5 elevation exposed the internal indexed triangle network and therefore
looked like a mesh. That presentation violated the intended product path:

`canonical UnitBox -> BaseVolume 1/1..1/16 -> BOOK operators -> LLM-authored
GeometryProgram/AST -> 4x4 transform graph + typed CSG/macro graph -> compiler
+ floor/law/FAR/parking -> render -> VLM typed review -> selected MASS ->
elevation`

The indexed triangle mesh is only a compiler/certificate transport. It is not
the design authority and must not appear as the final architectural language.

## Root cause

`ARR/backend/design/maas/agents/elevation_agent/projection.py` detected
adjacent faces by vertex index. Certified authored visual archives store three
fresh vertex indices per triangle, even where two triangles have identical
endpoint coordinates. Every triangle edge was therefore misclassified as a
boundary and drawn in black.

## Fix

- Keep the authoritative certified mesh and its hash unchanged.
- For render-only feature-edge detection, weld edge endpoints by quantized 3D
  coordinates at the existing 8-decimal contract precision.
- Suppress shared coplanar triangle diagonals.
- Preserve true silhouette, boundary and non-coplanar crease edges.
- Preserve the existing far-to-near painter order so rear edges remain
  occluded.

Regression test:

`test_elevation_render_hides_coplanar_triangulation_edges`

The test uses two coplanar triangles with duplicate endpoint indices. Before
the fix the center diagonal pixel was dark value 41 and the test failed. After
the fix the pixel remains face color and the test passes.

## Latest replay

`D:\Data\25_ACE\docs\ai-session-memory\maas-service-cache\single-executions\r293-selected-01-exact-replay-v6`

v6 replays through v5 to the original r293 archive.

Identity remains unchanged:

- program:
  `e7c1c15fff6f9151522ffe3ed47c40abfc7a3fb09be31035918782d9c5a021c8`
- certified authored visual geometry:
  `8440f0a1106d97a885f43ce8ade2ecdc4a684d4673dd271cac2c6b57f0b35045`
- floor-capacity plan:
  `9b82b925857b4561b54cde2dbc0b75f5c7dcb9baf4f8c0e3421217d6dd2126fc`

Physical bounds remain Z 0–14 m with guides 0/3.5/7/10.5/14 m.

## PNG evidence

- `D:\Data\25_ACE\docs\mass\r293-selected-01-mass-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-front-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-right-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-back-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-left-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-top-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-axon-v6.png`
- `D:\Data\25_ACE\docs\mass\r293-design-language-v6-selected-path-solid.png`

Original-resolution inspection passed for front and axon: both show solid
architectural faces and actual form edges without triangle wireframe.

The unversioned elevation PNG copies in `docs/mass` now point to v6.

## Verification

Backend focused single-execution suite: 43/43 passed.

Backend combined MASS suite: 418/418 passed.

Browser selected-path verification:

- v6 selected;
- 6-VIEW present;
- no hash/identity warning;
- `VLM NOT EVALUATED · NO CLAIM` remains visible.

## Still unresolved

- PNG floor guides are metadata only; projection currently draws a ground
  baseline, not explicit 3.5/7/10.5 m guide annotations.
- Parking source ordinance/appendix provenance and prior 1-versus-2 conflict
  remain unresolved.
- Portfolio diversity remains 5/6 Base Volume scopes and stepped 4/10.
- VLM is not evaluated, so v6 is geometry-ready, not final accepted.

## Cross-PNU diversity task started — 2026-07-28

The user requested that the remaining MASS work be split into small verified
steps, with this memory updated between steps:

1. Trace why FAR-filling stepped forms disappeared.
2. Select several real PNUs with cached legal evidence.
3. Freeze the distribution contract before changing code.
4. Add failing selector/supply tests.
5. Make the minimum code change.
6. Run short per-PNU probes before any long portfolio run.
7. Inspect PNG, legal, parking and diversity evidence per PNU.

First measured finding from r293:

- selection universe: 26 legally/geometry/parking eligible candidates;
- capacity target measured: 26;
- capacity target pass: 0;
- capacity target advisory miss: 26;
- selected FAR range: 35.936%–55.725%;
- mean selected FAR: 44.7971%;
- selected capacity labels mention spatial reserve, brief target and
  maximum-feasible, but measured candidates resolve below their requested
  target;
- current selector permits four copies of one roof archetype while the final
  audit rejects more than three;
- current selected scopes are 5/6 and omit `1/16`.

Therefore the missing FAR-filling stepped design is not only a board-ordering
problem. The investigation must distinguish:

- whether a high-yield stepped candidate exists before the 26-candidate final
  selection universe;
- whether stable all-floor legal-host intersection limits every candidate to
  low yield;
- whether capacity projection/measurement does not scale the authored
  BaseVolume to the requested band;
- whether the selector loses a valid high-yield candidate through
  silhouette/roof/phenotype caps.

No diversity or capacity policy has been changed yet.

### Step 1 complete: FAR-step supply root cause

The disappearance is upstream of final selection.

- r293 measured 1,533 compiled candidates and every one was below the feasible
  capacity floor.
- The 26-candidate final hard-pass/QD universe contained seven stepped
  candidates, but no FAR-target-passing candidate of any phenotype.
- Across 82 program/shared-floor candidates, maximum achieved feasible
  utilization was 0.5455.
- The selected maximum was 0.4429 / 55.725% FAR.
- Live legal floor plates were approximately
  102.931, 102.931, 74.989 and 51.471 m².
- Fitting the entire authored body to the all-floor stable intersection limits
  a constant four-floor stack to at most
  `4 × 51.471 / 332.322 = 0.6195`, below the minimum 0.70 band before voids or
  articulation are counted.

The code already builds a target-filled `floorwise_sibling` with one Matrix4
fit per legal floor. However, candidate generation copies only the sibling's
matrix/certificate metadata back to the visible authored source. Capacity/GFA
measurement still consumes the original low-occupancy volumes. The retry path
records 1,533 opportunities but is explicitly `diagnostic_only` and never
selects replacement geometry.

The selector cannot repair this:

- capacity score is advisory and excluded from the MASS design score;
- all 26 candidates tie as capacity misses;
- requested alternative labels are used as archive descriptors even when the
  measured/selectable alternative is empty;
- therefore the trace can mention maximum-feasible supply although no
  candidate attained even the minimum band.

Do not restore the old generic plan-refit path. It allows a numeric capacity
target to replace the BaseModel/BOOK design authority.

### Step 2 in progress: real-PNU sample

Strong locally cached legal/parking samples:

1. `1168011800104170004`
   - parcel 264.13 m²;
   - archived BCR 60 / FAR 250 / setback 0.5 / landscape 15;
   - multiple complete neighborhood-living results.
2. `1168011800104670003`
   - parcel 437.85 m²;
   - archived BCR 50 / FAR 300 / setback 0.5 / landscape 15;
   - latest complete neighborhood-living sample has computed two-space
     ground-surface parking evidence.

Conditional third sample:

3. `1168011800104230007`
   - parcel 343.76 m²;
   - BCR 50 / FAR 300;
   - one complete neighborhood-living job and parking candidates exist;
   - missing parcel land-analysis provenance means it must not yet be labelled
     `verified legal`.

Excluded from the strict comparison:

- `1168010100106770000`: parking needs an external rule and underground ramp
  evidence is heuristic.
- `1111011500100010001`: parking needs an external rule and cached versus job
  BCR/FAR constraints conflict.

Authority reminder:

- parcel boundary/numeric constraints: cached VWorld + archived job;
- law article linkage: Neo4j/law graph;
- required parking count: structured Seoul ordinance rule for the generated
  use/GFA;
- parking layout: solver evidence, not permit approval.

### Step 2 image and authority re-review

The user rejected option A and requested another sequential review before any
implementation. The PNG evidence supports that rejection.

- `r253-typed-repair-floorwise-probe.png` turns an authored U-shaped body into
  pinched/hourglass and wedge-like floor bands. It does not preserve the
  authored MASS well enough to become the production path.
- `stepped-capacity-probe-v2/...png` reaches capacity through a generic four
  plate staircase. It demonstrates capacity reachability, not design-language
  diversity.
- `r167.../maas-book-neighborhood-20.png` shows that FAR 111-142% and much
  broader silhouettes once coexisted, but its old pass labels do not prove the
  present one-authority legal/parking contract.
- r293 v6 preserves authored polygonal diversity but remains low-yield because
  it fits every floor to the smallest common legal host.

Two approaches are now explicitly excluded:

1. restoring the old generic plan-refit/capacity-pack retry;
2. rendering one authored mesh while pricing FAR and parking from a different
   hidden floorwise sibling.

The remaining design question is narrower: whether to express the lawful
floorwise adaptation as explicit nodes appended to the same executable
GeometryProgram (`slice authored solid by floor -> per-floor principal-frame
Matrix4 -> union`) so render, GFA/FAR, law, parking, selection and elevation
all consume one exact compiled result. No implementation has started.

### Step 3 authority decision recommended, awaiting user approval

Further code review rejects promoting the current floorwise implementation
unchanged:

- `project_floorwise_visual_mesh()` interpolates adjacent floor matrices
  continuously between floor-center breakpoints. This explains the pinched,
  sloped and hourglass side faces visible in the r253 probe.
- `floorwise_source_to_geometry_program()` serializes fitted legal polygons as
  new extruded plates. It replays capacity plates but no longer replays the
  authored BaseModel/BOOK solid as the executable root.

Recommended single-authority projection:

1. compile the authored BaseVolume + BOOK GeometryProgram;
2. intersect that exact root solid with one horizontal CSG band per floor;
3. apply one constant principal-frame Matrix4 to each isolated band;
4. intersect each transformed band with that floor's extruded legal polygon;
5. union the bands into one final GeometryProgram root;
6. compute GFA/FAR, law, parking, render/VLM, selection and elevation only
   from this exact final compiled solid.

There is no interpolation between floor matrices and no hidden area-only
sibling. Legal clipping may alter a candidate, so program retention,
silhouette distance and exact achieved capacity must be remeasured after the
clip. A candidate that misses a requested capacity band must not be labelled
as that band.

### Step 3A: BaseVolume vocabulary rechecked against BOOK p.3

The six BaseVolume scopes are source-faithful, not an arbitrary selector
bucket. Direct inspection of `docs/260506/BOOK/스캔_smallpdf_3.jpg` confirms:

`1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`.

These labels are volume fractions, not plan aspect ratios. Therefore `1/2`
must not be described as a `1:2` rectangular proportion.

The authority is still one normalized `1/1 UnitBox`. The other five are typed
occupancy/partition states derived from that UnitBox:

- `1/1`: whole cube;
- `3/8`: connected three-octant L;
- `1/2`: half cube;
- `1/4`: half-section bar;
- `1/8`: one octant;
- `1/16`: quarter-section bar.

The intended semantic order is:

`one UnitBox -> choose one of six BOOK BaseVolume scopes -> orientation /
host morphology -> BOOK single operation -> BOOK sequential combination /
aggregation / case-study composition -> LLM-authored typed GeometryProgram ->
compile -> floorwise legal CSG projection -> measure exact FAR/parking/law ->
render/VLM -> selection -> elevation`.

All six scopes in a ten-card board are a lineage-coverage requirement, not a
claim that six scopes alone provide visual diversity. Visual diversity remains
an independent measured constraint after final legal projection.

Terminology clarification requested by the user:

- The very first and sole primitive authority is always the normalized `1/1
  UnitBox`.
- A BOOK fraction (`1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`) is selected as
  a relative occupancy/topology state of that UnitBox.
- A wide plate, bar, tower or profiled prism is the subsequent host-morphology
  / base-seed Matrix4 state, not a seventh BaseVolume.
- Example: `1/1 scope + slab seed = wide full plate`; `1/2 scope + slab seed =
  half plate`; `1/4 scope + bar seed = local linear wing`.

The provenance order must therefore remain explicit:

`canonical 1/1 UnitBox -> BOOK fraction state -> orientation -> host
morphology/base seed -> chassis -> BOOK operations and compositions`.

Matrix authority clarification:

- There is exactly one initial primitive: the canonical normalized `1/1
  BaseVolume`, represented as one UnitBox.
- Every derived cell instance, scale, orientation, translation, rotation,
  shear and final principal-frame placement is represented by a homogeneous
  4x4 matrix.
- Rectangular fraction states such as `1/2`, `1/4`, `1/8` and `1/16` can be
  produced from the same UnitBox through Matrix4 scale/placement.
- The BOOK `3/8` L-state cannot be produced by one affine matrix because an
  affine transform cannot change topology. It is three Matrix4-derived
  UnitBox cells joined by a typed CSG union.
- Likewise carve, void, split, legal polygon intersection and other
  topology-changing/nonlinear BOOK operations remain explicit typed CSG or
  macro nodes. Their component placements still use Matrix4.

Canonical statement:

`one 1/1 UnitBox authority + Matrix4 transform graph + typed CSG/macro graph`.

The approved architecture is now formalized in:

`ARR/docs/superpowers/specs/2026-07-28-single-authority-basevolume-legal-mass-design.md`.

That spec supersedes the previous three-authority floorwise design. Its only
new selector decision awaiting final review is strict four-band balancing:
ten cards must distribute the four actually achieved capacity bands as
2/2/3/3 in some order, while still covering all six BaseVolume lineages.

## Implementation execution started

Implementation plan:

`ARR/docs/superpowers/plans/2026-07-28-single-authority-legal-mass.md`

Recovery ledger:

`.superpowers/sdd/2026-07-28-single-authority-legal-mass/progress.md`

Current declared language space is 21,039,480 theoretical paths:

`6 BaseVolume scopes x 3 orientations x 5 base seeds x 11 chassis x 69 BOOK
principles x 11 variations x 7 programs x 4 capacity alternatives`.

This space is not brute-forced. Bounded stratified/QD search must preserve the
axes while compile, law, achieved capacity, parking, silhouette and VLM gates
reduce supply. A long ten-card run is forbidden until a three-candidate probe
proves that the same final geometry hash is used for render, FAR, law and
parking.

Execution is split into five reviewed tasks. Task 1 now starts with explicit
Matrix4 host fitting and site-bound program export. No production
implementation result has been claimed yet.

### Task 1 RED checkpoint

The Task 1 implementer added and ran the focused tests. They fail for the
intended missing interfaces:

- `append_site_placement_matrix`;
- `inverse_matrix4`.

The failure is not a long portfolio/runtime failure. Minimal GREEN
implementation is now in progress. No Task 1 completion or success claim has
been made.

### Task 1 complete after reviewed fix rounds

Task 1 now provides:

- affine `inverse_matrix4`;
- `HostFitTransform`;
- explicit Matrix4 host fitting including target-area shrink and axis widening;
- a root `site_placement_matrix4` GeometryProgram node;
- site-bound SourceMass export without a second principal-frame fit.

Final focused module result: 213/213 passed. Measured corresponding-vertex
delta between the derived fit and recompiled placed program:

`1.9827908761303516e-08`.

Review fix round 1 replaced the noncanonical dimensional-box success fixture
and made vertex comparison preserve order and multiplicity. Fix round 2 made
the site-bound guard require exactly one primitive overall, and that sole
primitive must be the normalized UnitBox. A connected UnitBox-plus-cylinder
program is rejected by the new site-bound authority while the legacy bridge
retains its historical behavior.

Task 1 scoped re-review is approved with no remaining Critical/Important
findings. Task 2 starts next: constant-per-floor Matrix4 bands plus typed CSG
legal intersections on the same GeometryProgram.

### Task 2 pre-RED architecture correction

The first Task 2 sketch proposed new slab and legal-polygon primitives. That
would violate the user's approved sole-UnitBox authority and would be rejected
by Task 1's site-bound guard.

Corrected contract:

- each floor slab is another Matrix4 instance of the existing normalized
  UnitBox node;
- the irregular legal polygon is not a public primitive;
- it is an execution-only typed `legal_section_clip` CSG/macro consuming the
  transformed authored band with exterior/holes/Z-band parameters;
- the final projected program must still contain exactly one primitive node.

The correction was made before RED tests or production Task 2 edits.

### Task 2 complete after review

Task 2 now appends the legal floor stack to the same executable
GeometryProgram:

`existing UnitBox -> floor-band Matrix4 -> authored-root intersection ->
fixed floor Matrix4 -> typed legal_section_clip -> final union`.

Final evidence:

- focused tests: 4/4;
- exact primitive count: 1;
- achieved areas:
  `[97.78400004, 97.78400004, 71.23999997, 48.89800001]` m2;
- program hash:
  `5afa41acef467a37343c52f02060a1583f3be3cf83911e1e8c6d3033c34a8226`;
- geometry hash:
  `492a1543a4954bba854ded3be4e0e78ef7fa52507b768d11ce6735304e1b3fe8`;
- hard pass, contained, finite, manifold and watertight;
- no Matrix4 interpolation;
- no projected-surface sibling;
- Task 1 site-bound SourceMass export succeeds;
- `compilation_gate` reports no issues.

A load-bearing integration regression found sub-micrometre Boolean sliver
edges when a band cutter exactly shared the authored XY bounds. The band
cutter now expands outward by 0.1 mm in XY only. Because it remains
intersected with the authored root, it cannot add occupied geometry and it
does not alter Z boundaries.

Independent Task 2 review approved with no Critical/Important findings.
Deferred minors: rerun the combined geometry suite after the final cutter
padding during final scoped verification, and add/confirm a polygon-hole clip
case if a live legal section contains holes.

Task 3 now starts. It must replace the stable all-floor host and hidden sibling
path so candidate volumes, surfaces, FAR, law and parking all originate from
the Task 2 final projected program.

### Task 3 complete after critical review fixes

The selectable candidate path now executes:

`authored BOOK/program -> Task 1 site Matrix4 -> Task 2 floorwise legal
program -> exact site-bound SourceMass`.

The old selectable stable-all-floor intersection and diagnostic sibling copy
are removed. The r293-shaped deterministic fixture now measures:

- floor areas `[102.93099981, 102.93099981, 74.989, 51.47099999]` m2;
- total GFA `332.322` m2;
- FAR `125.879545%` on the fixture site;
- final program hash
  `5cb161825e010351135df2226262482efa16877e8e7843a869bebec5426e034d`;
- final geometry hash
  `8335633e29bfb327b1a87166fe11d24e3a57633058733bbf7eb58f2a35d73695`;
- projection failures `0`.

The first independent review found three authority defects, all fixed:

1. requested capacity shortfall no longer deletes a valid legal candidate; it
   is measured diagnostic evidence for Task 4 classification;
2. certified final export no longer truncates triangle surfaces, requires
   nonempty exact count equality, and binds a canonical exact SourceSurface
   SHA-256 that downstream recomputes from the actual payload;
3. every part of every certified floor band is retained instead of being
   cut by a global volume-record cap.

Regression evidence:

- 2050 compiler triangles export as 2050 surfaces;
- a forced 11/12 partial export rejects;
- two bands with two polygon parts retain four SourceVolumes;
- real compiled final source passes;
- empty or tampered surfaces fail closed;
- full focused Task 3 suite 147/147 passed.

Task 3 scoped re-review approved all three fixes with no new
Critical/Important findings.

The live target-three command remains blocked because the current management
command has no target-count option and `--smoke` runs at least ten. No long
probe was started. Task 5 must add the bounded interface before real PNU PNG
verification.

Task 4 starts next: only actually achieved capacity bands count, and ten-card
cardinality, all six scopes, 2/2/3/3 band balance, stepped 1-3, upper-band
stepped supply, roof/phenotype caps and silhouette incompatibilities are one
joint solver problem.

### Task 4 complete after review fixes

The target-ten selector is now one joint MILP. Deterministic passing evidence:

- selected count 10;
- scopes `2/2/2/2/1/1` across the six BOOK lineages;
- achieved capacity bands `3/3/2/2`;
- stepped count 1;
- upper-band stepped count 1;
- roof and solid phenotype counts `3/3/2/2`.

The first review found three gaps, all fixed:

1. achieved capacity is re-resolved from the current Task 3 measurement, not
   trusted from raw id/pass metadata;
2. every selected card must belong to exactly one of the four canonical
   achieved bands, so `2/2/2/2 + two blank` fails;
3. solver timeouts/nonoptimal diagnostics are not called proven infeasible or
   maximum cardinality. A row-valid exact-ten incumbent may be accepted;
   otherwise non-proven statuses remain explicit.

Final Task 4 evidence:

- full module 84/84 passed;
- review regression slice 6/6 passed;
- no post-joint cardinality-only fallback;
- scoped re-review approved with no new Critical/Important finding.

Task 5 starts next. It must first add a bounded diagnostic target of three
that is explicitly not a completed portfolio. Two strict cached PNUs are
probed separately. A target-ten run remains forbidden until the three-card
same-hash PNG/FAR/law/parking evidence passes.

### Task 1 GREEN checkpoint

Task 1 implemented explicit `HostFitTransform` Matrix4 placement, affine
inverse, root site-placement program export, and exact site-bound SourceMass
materialization with no second principal-frame fit.

Exact verification command:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_unitbox_matrix `
  design.test_maas_geometry_language -v 2
```

Result: `211/211` tests passed in `12.981s`. The appended matrix node ID was
`site_placement_matrix4`; recompiling the placed program produced a maximum
vertex delta of `1.9827908761303516e-08`, below the `1e-7` contract.

### Task 1 fix round 1/5

Review follow-up made the site-bound authority contract explicit:

- the success fixture is now visibly
  `1/1 UnitBox -> slab Matrix4 -> rotate -> site-placement Matrix4`;
- the new site-bound export rejects raw dimensional box authority before the
  compiler can normalize it, while the legacy direct bridge remains
  unchanged;
- vertex equivalence now requires equal tuple lengths and compares
  corresponding indices, preserving order and multiplicity.

TDD RED: the new noncanonical-authority regression failed because the
site-bound entry point returned `SourceMass(...)` instead of `None`.

Focused GREEN: `3/3` affected methods passed in `0.030s`.

Full verification:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_unitbox_matrix `
  design.test_maas_geometry_language -v 2
```

Result: `212/212` passed in `12.778s`. Matrix node ID remained
`site_placement_matrix4`; all `8` corresponding vertices matched with maximum
delta `1.9827908761303516e-08`. Scoped `git diff --check` exited `0`.

### Task 1 fix round 2/5

The site-bound UnitBox authority guard now counts all primitive nodes, requires
exactly one, and requires that sole primitive to be the normalized `1/1`
UnitBox. Transform and typed CSG nodes remain allowed.

TDD RED used a connected
`UnitBox-derived slab + translated cylinder + union + rotate + site Matrix4`
program. The site-bound exporter incorrectly returned `SourceMass(...)`
instead of `None`, while the legacy direct bridge remained valid.

Focused GREEN: `1/1` passed in `0.019s`.

Full command:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_unitbox_matrix `
  design.test_maas_geometry_language -v 2
```

Result: `213/213` passed in `12.760s`—the prior 212 plus the new focused
mixed-primitive regression. Scoped `git diff --check` exited `0`.

### Task 3 final projected GeometryProgram authority

Task 3 replaced the selectable stable-host/diagnostic-sibling path with one
physical authority:

`authored program -> BOOK/program projection -> site-placement Matrix4 ->
floorwise legal CSG projection -> exact site-bound SourceMass`.

The returned candidate volumes, surfaces, `geometry_program`, compilation
payload and geometry bridge all originate from that final projected program.
The source metadata authority is
`final_floorwise_legal_geometry_program`. Authored program/geometry hashes
remain only under upstream provenance. The selectable candidate path no
longer calls `materialize_floorwise_legal_source()`, and capacity retry
evidence cannot select replacement geometry.

TDD RED command:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_mass_stage `
  design.test_maas_shared_floor_contract `
  design.test_maas_book_language -v 2
```

Initial result: `144` tests ran in `6.445s`; the new authority regression
errored with missing `geometry_authority`, and the r293 regression measured
only `46.4525775669 m2`, below the old `205.884 m2` ceiling.

Final fresh verification used the same command and passed `142/142` tests in
`6.202s`. `compileall -q` on the six scoped Task 3 code/test files and scoped
`git diff --check` both exited `0`.

Deterministic r293-shaped fixture evidence:

- legal/target floor areas:
  `[102.931, 102.931, 74.989, 51.471] m2`;
- achieved final floor areas:
  `[102.93099981, 102.93099981, 74.989, 51.47099999] m2`;
- four authoritative SourceVolume bands total `332.322 m2`;
- deterministic compiler calls: `5` over `4` unique program states;
- achieved FAR on the r293 `264 m2` parcel basis: `125.879545%`;
- projection failures: `0`;
- final program hash:
  `5cb161825e010351135df2226262482efa16877e8e7843a869bebec5426e034d`;
- final geometry hash:
  `8335633e29bfb327b1a87166fe11d24e3a57633058733bbf7eb58f2a35d73695`.

Shared-floor measurement receives the final bridge hashes. Downstream GFA/FAR,
law, parking and render evidence now each records the final geometry hash.
Final-authority candidates fail closed when the program/projection/bridge/
compiled-render/shared-floor hashes disagree.

The requested live target-three/no-VLM BOOK probe was not started. Exact
blocker: `benchmark_maas_book_program_portfolios` exposes no target-count
argument. Its smallest `--smoke` mode explicitly runs a minimum 10-alternative
portfolio. Starting that command would violate the Task 3 target-three and
no-long-portfolio constraint. No ten-card run was attempted. A bounded
target-three CLI must be supplied before the live PNU probe can run.

### Task 3 fix round 1/5

Review follow-up removed the remaining requested-capacity selection gate and
made the final render payload independently verifiable.

Seven new regressions first reproduced all findings:

- valid final legal geometry was discarded solely for requested area miss;
- a synthetic 2050-triangle final compilation exported only 2048 surfaces;
- a patched 11/12 surface export was accepted;
- two polygon parts across two certified bands were truncated from four
  SourceVolumes to two;
- downstream positive evidence lacked a completeness/payload binding;
- altered and empty final surface payloads both passed.

All seven failed before production edits (`6` failures, `1` error, `0.678s`).

Certified final site-bound export now has this binding contract:

```text
nonempty surfaces
raw compiler triangles == exported surfaces == actual SourceMass surfaces
surface_export_complete == true
surface_payload_hash == SHA-256(canonical exact SourceSurface JSON payload)
```

The canonical payload includes every surface field and every unrounded vertex;
records are sorted before hashing. Downstream recomputes the hash from the
actual `SourceMass.surfaces` and fails closed for incomplete or altered
payloads. Certified floorwise sources bypass the legacy surface cap and retain
every polygon part in every legal floor band. The positive downstream fixture
is now a real compiled/projected site-bound source.

Requested and achieved floor areas now remain in
`capacity_projection_measurement` with diagnostic-only authority. A valid
shortfall remains available for Task 4 classification; the r293 fixture still
proves its own 99.5%-plus exact achievement.

Focused GREEN passed `7/7` in `0.697s`. The complete Task 3 command passed
`147/147` in `6.810s`. The large-payload test exported `2050/2050`; the
incomplete `11/12` patch returned no source; the multipart test retained all
four band/part SourceVolumes.

### Task 4 achieved capacity and joint ten-card solver

Task 4 made achieved capacity—not requested capacity intent—the archive and
portfolio authority. `_capacity_alternative_key()` now returns only a
nonempty measured `selectable_capacity_alternative_id` with
`selectable_capacity_hard_pass == True`; all requested-label fallback paths
return `""`. Requested alternatives remain separately searchable through
diagnostic counters.

The QD axis is now `achieved_capacity_band`, and blank capacity misses cannot
claim achieved-band anchor protection. Selection diagnostics, QD evidence and
benchmark metrics report achieved capacity bands separately from requested
alternatives.

The final target-ten selector now invokes one exact MILP over:

- exactly ten selections;
- all six BOOK scopes at least once;
- each of four achieved capacity bands two to three times;
- stepped count one to three;
- at least one stepped `brief_target` or `maximum_feasible`;
- roof archetype and solid phenotype maximum counts of three;
- existing pairwise silhouette incompatibilities.

An infeasible joint model returns no completed board. Its versioned
certificate serializes stable unsatisfied constraint names plus the maximum
cardinality achievable under incompatibility and upper-bound constraints.
The final selector has no cardinality-only or bounded-beam fallback.

TDD RED:

```text
python ARR/backend/manage.py test design.test_maas_book_language -v 2
Found 77 test(s).
1 requested-label assertion failure + 8 missing joint-API errors
Ran 77 tests in 1.715s
FAILED (failures=1, errors=8)
```

Fresh GREEN:

```text
Found 78 test(s).
Ran 78 tests in 1.796s
OK
```

`compileall -q` and scoped `git diff --check` both exited `0`; Git printed
only existing LF/CRLF warnings.

Deterministic feasible distribution:

```text
selected_count = 10
scope_counts = 1/1:2, 3/8:2, 1/2:2, 1/4:2, 1/8:1, 1/16:1
achieved_capacity_counts =
  spatial_reserve:3, balanced_yield:3,
  brief_target:2, maximum_feasible:2
stepped_count = 1
upper_band_stepped_count = 1
roof_counts = 3/3/2/2
solid_phenotype_counts = 3/3/2/2
```

The incompatible `4/2/2/2` capacity distribution returned `()` with:

```text
maximum_achievable_cardinality = 9
unsatisfied_constraints =
  selection_count:exact_10
  capacity_band:spatial_reserve:max_3
```

No portfolio benchmark or live VLM run was started.

### Task 4 fix round 1/5: canonical resolution, full partition, solver proof

Review regressions exposed three authority gaps:

1. a stale raw selectable ID/True flag could bypass final achieved
   measurement;
2. `2/2/2/2 + 2 blank` cards could satisfy the four named band rows;
3. time-limit/error incumbents were serialized as proven infeasibility and an
   unproven diagnostic incumbent was called a maximum.

TDD RED ran five tests in `0.004s` with `3` failures and `2` errors. A sixth,
audit-specific regression separately errored on the missing audit helper.

The achieved-band key now calls the Task 3
`resolve_capacity_band_evidence()` contract with current
`source_capacity_measurement`. The selectable-measurement marker is mandatory,
so requested-label fallback remains impossible. Canonical target, minimum and
achieved utilization all have to resolve hard-pass before a band key exists.

The joint MILP now has
`capacity_band:classified_exact_10`, whose coefficients cover only the four
canonical bands and whose bounds are exactly ten. The benchmark audit uses
the matching unfiltered partition rule. `2/2/2/2 + 2 blank` returns no board
and names that constraint. Its diagnostic maximum is optimally ten because
diagnostic search relaxes equality/lower requirements; the certificate keeps
the failed classified partition explicit.

Solver evidence now distinguishes proof states:

- a row-valid target incumbent is feasible even when score optimization hits
  a limit;
- only SciPy status `2` is `infeasible`;
- limit/unbounded/error/unknown becomes `solver_not_proven` with no maximum
  claim;
- diagnostic cardinality is called a maximum only for status `0` plus
  `success=True`;
- otherwise only an incumbent count and
  `maximum_cardinality_proven=False` are recorded.

Fix GREEN:

```text
focused review slice: 6/6 passed in 0.006s
full design.test_maas_book_language: 84/84 passed in 1.764s
compileall -q: exit 0
scoped git diff --check: exit 0
```

No performance issue was observed; the full module remained below two
seconds. No portfolio benchmark, live VLM, reset or commit was run.

## 2026-07-29 Task 5 live-probe checkpoint

Task 5 has implemented final-legal-geometry-hash propagation through mass
product evidence, the elevation runtime, and the single-execution pipeline.
Authored-program and capacity hashes remain upstream evidence only and cannot
substitute for the final projected geometry hash. The focused hash slice is
`4/4` GREEN.

The production selector remains exact-ten. A separate
`--diagnostic-target {1,2,3}` path is explicitly marked
`diagnostic_only=true` and cannot emit production pass/completion claims.
`ARR/backend/tools/verify_single_authority_mass_pnus.py` launches each PNU in
a fresh subprocess and output directory, strips OPENAI/VLM environment
variables, persists state, and terminates after 60 seconds without a state
update. The Task 5 regression was `83/83` GREEN before the later bounded
generation tests.

PNU 1 (`1168011800104170004`) live evidence so far:

- First probe output:
  `.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes/20260728T154532714336Z-01-pnu-1168011800104170004`.
- It stalled in candidate generation because target-three selection still
  scheduled roughly 1,968 evaluations with no inner progress callback.
- The diagnostic lattice is now bounded to scopes `1/1,3/8,1/2`, parent page
  `(0,)`, one BOOK probe, 36 evaluations and 12 released candidates. Inner
  counters persist `evaluated_count`, `compiled_count`,
  `program_passed_count`, and `candidate_cap`; focused budget tests are GREEN.
- The second probe completed that bounded initial generation in 7.638 seconds:
  `evaluated=36`, `compiled=8`, `program_passed=0`, `selection_pool=0`.
  It then stalled because replenishment called `_program_pool` without the
  diagnostic caps/progress callback. No PNG, FAR, law, parking, or final hash
  was produced.
- Replenishment now receives the same diagnostic lattice and
  evaluation/candidate caps, is limited to one cycle, and persists
  `phase=replenishment_generation`. The focused module is `9/9` GREEN.
- One PNU 1 re-probe using this replenishment fix is currently authorized.
  If it still yields zero candidates, do not run another blind loop: persist
  the hard-gate rejection histogram and representative failures, then repair
  the smallest deterministic bounded lattice under RED/GREEN tests.

Do not start PNU 2 or exact-ten production. PNU 2 is allowed only after PNU 1
produces real same-hash PNG/FAR/law/parking evidence and the PNG is manually
inspected. Exact-ten is allowed only after both PNU target-three probes pass.

### PNU 1 probe 3 result: bounded execution completed, acceptance failed

Output:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r3/20260728T155533271640Z-01-pnu-1168011800104170004`.

The replenishment cap fix removed the hang. All three program runs completed
in about one minute total and produced four PNG files, but these are empty
diagnostic boards showing `0/3 floor-verified masses`; they are not accepted
MASS PNG evidence. The combined summary is `diagnostic_only`, `final_count=0`,
`final_geometry_hashes=[]`, `final_geometry_hash_agreement=false`, empty FAR
and parking arrays. PNU 2 remains forbidden.

Exact first-pass counts and program-gate failures:

- neighborhood: evaluated 36, compiled 8, clean 6, program hard-pass 0;
  all six failed `dominant_ratio`, one also `site_coverage`.
- gymnasium: evaluated 36, compiled 23, clean 22, program hard-pass 0;
  all 22 failed `role_coverage+dominant_ratio`, three also failed the
  program-form relation.
- cultural: evaluated 36, compiled 11, clean 9, program hard-pass 0;
  all nine failed `role_coverage+dominant_ratio`, one also `site_coverage`.

Representative gym observation: the final projected solid had
`dominant_component_ratio=1.0`, `dominant_ratio_score=0.45`, and
`role_coverage_score=0.333`, despite its upstream source seed being
`program_gym_long_span_hall`. This indicates an authority/provenance break:
the Task 3 floorwise final solid is geometrically one connected legal product,
while the old program gate interprets its floor-band proxy roles as if they
were the authored program component hierarchy. In
`_materialize_final_legal_candidate`, materialized final metadata overwrites
upstream `program_space_zones` and replaces authored continuous-surface
hierarchy evidence with a generic one-patch record.

Current repair rule: do not lower program thresholds and do not accept stale
upstream geometry as final authority. Preserve the final program/geometry/
surface hashes and measured legal solid as sole geometry authority, but carry
hash-bound authored semantic-role and morphology provenance through the
projection certificate. Add tamper/spoof rejection and a RED regression for a
valid Task 3 projected program before rerunning PNU 1.

Independent audit:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-semantic-provenance-audit.md`.
It requires actual disjoint semantic carrier polygons projected into the
principal frame and vertical interval of the final floor-band proxies. The
dominant role owns the measurable remainder; carriers cannot add geometry.
Their canonical payload must bind the final program, final geometry, complete
surface payload, floor-capacity-plan, PNU/site context, and capacity
alternative hashes/IDs. Consumers recompute these bindings and fail closed on
stale zones, token-stuffed role names, overlap/area inflation, empty/outside
carriers, multipart loss, or cross-PNU replay. The physical
`geometric_dominant_component_ratio=1.0` remains honest; verified internal
program carriers may separately establish semantic dominance and role
coverage.

### Task 5 semantic projection review: REJECT, fix round 1 active

The first implementation passed its strengthened 8/8 tests, production
handoff fixture 1/1, and the three-module Task 5 regression 96/96 in 84.624
seconds. Those GREEN tests are not sufficient evidence. Independent review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-semantic-projection-review.md`
reproduced three Critical bypasses:

1. The evaluator compared the carrier envelope to a second context blob in
   the same SourceMass signature. Copying both blobs from another
   PNU/site/floor-plan/capacity context passed a self-consistent replay.
2. Three fabricated roles `fake_main_hall`, `fake_service`, and `fake_entry`
   passed build, audit, all 3 role hits, and the spatial hard gate because
   relation mapping trusted role-name substrings.
3. The production downstream combined hard pass did not rerun or require the
   semantic audit; missing/stale/tampered evidence could still pass
   law+geometry+parking.

Important gaps: an empty surface tuple could bind the canonical empty hash;
stale `program_space_zones` remained available to VLM consumers; and the
envelope bound the requested capacity alternative before the achieved
capacity measurement/band existed.

Fix round 1 is now RED. It must use independently derived downstream expected
PNU/site/floor-plan/current achieved-capacity identities, exact trusted
canonical component identities rather than role tokens, nonempty complete
surface export, achieved-capacity evidence hash, verified carriers only in
VLM context, and a mandatory downstream semantic hard gate. No PNU live probe
is permitted until re-review approves these findings.

### Task 5 semantic projection re-review round 1: REJECT

Fix round 1 resolved arbitrary fake-role strings, empty/incomplete surface
payloads, achieved-capacity identity, externally derived PNU context, and
mandatory downstream audit in the covered path. Fresh regressions were 99/99
GREEN. Re-review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-semantic-projection-re-review-round-1.md`
still rejected the implementation:

- Removing/downgrading the final-authority string made the in-scope semantic
  audit return `not_required/hard_pass=true`; an isolated downstream row then
  passed legal, parking, semantic, and combined gates.
- Generation bound the buildable generation polygon, while downstream hashed
  the original parcel polygon. A normal setback/height-safe candidate could
  be rejected despite being correct.
- Copying canonical component-graph metadata plus canonical-looking volume
  roles could pass without proving those component identities are reachable
  from the authored/final AST root.
- Legacy exact post-BOOK VLM repair still used the old
  `replace_source_dominant...`, `program_space_zones`, and floorwise sibling
  path instead of returning through the sole final materializer.

Fix round 2 is active. In-scope missing authority must fail closed; generation
and downstream must hash the same independently recomputed buildable site;
semantic component identity must be bound to reachable AST nodes/canonical
seed compilation; and legacy VLM repair must either rematerialize through the
same final Matrix4+floorwise legal program or explicitly return no selectable
candidate without stale zones. PNU probes remain forbidden.

### Task 5 PNU 1 probe r4: generation fixed, render contract failed

After round-2 approval, exactly one diagnostic target-three run started at
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r4/20260728T165427740951Z-01-pnu-1168011800104170004`.

The real PNU pipeline reached gymnasium 27 evaluated, 17 compiled, 12
program-passed, a 20-candidate selection pool, and transiently selected three.
The r3 `program_passed=0` semantic failure is resolved.

It then failed in final render serialization with
`ValueError: authored profiled visual source has no certified projection`.
The exact final floorwise-authority surfaces have `profiled_*` triangle types,
so `projected_visual_contract.py` routed them into the legacy authored-mesh
branch requiring `floorwise_visual_projection`. Task 3 intentionally removed
that sibling certificate because the final program/geometry/complete-surface
hashes are now sole authority.

The only emitted neighborhood PNG is an empty `0/3` title and is rejected.
There is no accepted gym/cultural/combined PNG, FAR, parking, or final hash
summary. Do not rerun yet.

Required fix: a separate final-floorwise-authority serialization branch may
emit the exact final surfaces only when program, geometry, complete surface
payload, semantic projection, and current context agree. Missing/tampered
evidence must fail. Existing legacy profiled sources without
`floorwise_visual_projection` must continue to fail.

### Task 5 r4 renderer coordinate-contract checkpoint

An initial read of `floorwise_source_to_geometry_program()` suggested metre Z,
but tracing the actual serialized object corrected that inference. The
candidate's exact final surfaces come from the site-bound UnitBox compilation:
the bridge localizes XY to `SourceMass.footprint.centroid` and preserves the
compiled normalized 0..1 Z. The separate downstream execution program expands
the floor stack to metre height. Therefore the portfolio renderer's centroid
addition and height multiplication are correct for this surface transport.

The final-floorwise-authority serializer must retain
`source_footprint_centroid_local_xy_normalized_z`; it must not localize or
scale the vertices a second time. RED tests must prove exact triangle
preservation and must reject missing/tampered final program, geometry,
complete-surface and semantic/current-context bindings. The legacy
authored-profile path remains fail-closed without its legacy certificate. No
additional live PNU run is authorized before focused and regression GREEN plus
independent review.

The initial final-authority implementation exposed a second identity trap
before any rerun. Legacy visual identity hashes typed surface records, while
the final legal geometry identity is the compiler's canonical triangle-mesh
hash; those algorithms are intentionally different. The final serializer now
must reconstruct world XY from the certified source centroid, recompute the
compiler mesh hash from all exact triangles, and compare it with the claimed
final geometry hash. It may not simply trust the claimed hash. The test fixture
must export the complete compiled mesh rather than two illustrative faces.

`preference/loop.py::_require_certified_authored_visual` also repeated the
legacy surface-hash equality check. Final-authority preview must instead
validate the complete projected artifact and require exact equality between
the feature surfaces and its triangle payload; legacy behavior remains
unchanged. Required proof is serializer -> portfolio artifact -> validator ->
`feature_preview_png`, including tamper rejection. No live PNU rerun yet.

### Task 5 r4 visual-authority independent review: REJECT, fix round 2

The first renderer fix reached a real preview and passed its happy-path and
legacy regressions, but independent review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r4-visual-authority-review.md`
rejected the artifact boundary:

1. `projectedVisualGeometryHash`/certificate `visual_hash` still carried the
   compiler final geometry hash, while visual transport and compiler/legal
   hashes are distinct identities. Portfolio/passport fields then aliased the
   visual value into `finalLegalGeometryHash`.
2. Post-serialization mutation of certificate `semantic_projection_hash` or
   `final_surface_payload_hash` was accepted because the validator checked
   only non-emptiness.
3. A fabricated external audit containing only `hard_pass`, a copied semantic
   hash and empty failures certified successfully; no full schema/current
   PNU-site-capacity envelope was required.
4. Moving only `feature.geometry` +100 m shifted rendered vertices while the
   artifact retained the original certified centroid.

Fix round 2 must preserve a distinct exact visual transport hash and compiler
`finalLegalGeometryHash`, independently validate both, recompute the final
SourceSurface payload at archive hydration, require a complete externally
derived semantic audit/current-context envelope, and bind/reject renderer
origin divergence. All four adversarial REDs are required before GREEN. No
PNU rerun.

### Task 5 r4 visual-authority fix round 2: GREEN, awaiting re-review

All four independent-review bypasses were reproduced as RED before production
edits, then fixed:

- `projectedVisualGeometryHash` is the exact typed-triangle visual transport
  identity; `finalLegalGeometryHash` is the separately recomputed compiler/
  legal mesh identity. Portfolio render evidence, rows and passports use the
  latter for final legal identity.
- Archive hydration recomputes the compiler mesh hash from every exact
  centroid-local triangle, reconstructs the SourceSurface payload hash, and
  binds the full semantic audit payload plus audited current
  PNU/site/floor-plan/capacity context.
- A minimal fabricated audit no longer certifies. Serialization requires a
  complete externally produced verified audit and requires its canonical
  payload to equal a fresh audit recomputed from that external context.
- Final-authority preview validates the complete artifact, exact feature/
  artifact triangle equality, and the feature centroid against the certified
  origin. A +100 m feature-only move fails closed.

Fresh verification:

- focused final authority/tamper: 2/2 GREEN;
- portfolio plus legacy visual authority: 20/20 GREEN;
- full relevant command
  `python manage.py test design.test_maas_mass_product_evidence design.test_maas_flow_regressions design.test_maas_single_execution design.test_maas_elevation_agent --verbosity 1`:
  140/140 GREEN in 84.473 s;
- compileall and scoped code/docs diff checks exit 0.

No PNU rerun, PNU2 or target-10 has occurred. Independent round-2 re-review is
active; PNU1 target-three may run only after approval.

### Task 5 r4 visual-authority re-review round 2: REJECT, fix round 3

The previous four bypasses are resolved, but re-review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r4-visual-authority-re-review-round-2.md`
found one remaining archive-boundary bypass. If an archived caller changes the
semantic audit PNU/context or semantic projection hash and then recomputes all
co-located context/audit/certificate/top-level hashes, the validator accepts
the self-consistent replacement. The 64-test mass+flow slice remained GREEN,
but hashes stored beside the payload cannot authenticate that payload against
the current job.

Fix round 3 must make final-authority artifact validation require an expected
semantic context/hash supplied independently by the caller. The live portfolio
caller must pass the downstream audit/current context it just recomputed.
Archive hydration must receive an external run/current-context anchor rather
than treating `artifact.semanticProjectionAudit` as its own expectation.
Direct final-artifact validation without that external anchor must fail
closed. Legacy visual artifacts remain compatible. No PNU rerun.

### Task 5 r4 visual-authority fix round 3: GREEN, awaiting re-review

The externally anchored validator is implemented. Final-authority validation
now requires caller-supplied `expected_semantic_context` and
`expected_semantic_projection_hash`; it refuses to use the artifact's own
semantic audit as its expectation. The live portfolio supplies the current
downstream semantic hard-gate context/hash, preview receives a sibling caller
anchor, and executed-archive hydration receives the separately loaded summary
row anchor. Direct final-artifact validation without an anchor fails closed;
legacy artifacts do not require this new final-only anchor.

The reviewer reproduction is now covered: changing archived PNU/context or
semantic hash and recomputing all co-located hashes is rejected while the
external anchor remains unchanged.

Fresh verification:

- focused final authority: 2/2 GREEN;
- portfolio plus legacy visual authority: 20/20 GREEN;
- full four-module regression: 140/140 GREEN in 84.831 s, command exit 0,
  including executed-archive flow and legacy archive replay.

No PNU rerun occurred. Independent round-3 re-review is active.

### Task 5 r4 visual-authority re-review round 3: REJECT, fix round 4

The external current-context and semantic-hash anchors work: no-anchor final
validation rejects, artifact-only PNU/semantic rewrite rejects, real archive
replay with its separate summary anchor passes, and a missing summary anchor
rejects. One carrier-payload bypass remains. Changing
`semanticProjectionAudit.accepted_carriers` to an impossible area/empty
polygon and recomputing only the artifact-local audit payload hash plus its
certificate/top-level copies still passes under the unchanged external
context/hash.

Fix round 4 adds the canonical full semantic audit payload hash as a third
caller-supplied anchor. Portfolio/preview derive it from the original
downstream audit; archive hydration derives it from the separately loaded
summary-row audit. Final validation compares the hydrated artifact audit
payload against that external expected hash. No PNU rerun.

### Task 5 r4 visual-authority fix round 4: GREEN and independently APPROVED

The full canonical downstream semantic-audit payload hash is now the third
required caller-owned anchor. Direct validation, live portfolio, preview, and
separate summary-row archive hydration all pass the original external audit
payload hash; final artifacts cannot supply their own expectation. Legacy
visual artifacts remain no-anchor compatible.

Fresh verification:

- focused final replay/preview: 1/1 GREEN in 0.059 s;
- mass+flow/archive: 64/64 GREEN in 0.754 s;
- full four-module: 140/140 GREEN in 85.857 s, exit 0;
- compileall and scoped diff checks exit 0.

Independent round-4 re-review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r4-visual-authority-re-review-round-4.md`
APPROVED. It freshly confirmed: base final artifact and original archive pass;
no-anchor final, carrier area `999999` plus empty polygon, PNU/context rewrite,
semantic-hash rewrite, artifact-only archive carrier replay, and missing
summary anchor all reject; legacy no-anchor passes. One nonblocking note is
that `_archive_render_evidence` has a legacy visual-hash fallback when no final
hash list is supplied, but the production final path supplies both lists.

No PNU rerun has occurred as of this checkpoint. PNU1 diagnostic target-three
is now authorized; PNU2 and target-ten remain gated on its accepted PNG/hash/
FAR/law/parking evidence.

### Task 5 PNU1 diagnostic target-three r5: render graph contract failed

Exactly one approved PNU1 run started at
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r5/20260728T173322638402Z-01-pnu-1168011800104170004`.
Gymnasium again reached 27 evaluated / 17 compiled / 12 program-passed, pool
20, and selected three with two of three scopes. Candidate generation and the
final visual-authority serializer therefore remained recovered.

The run then failed in `outcome_graph.observe_portfolio_render()` with
`projected visual render hash mismatch: certified=missing
rendered=b8835f8bcdf012c9a1ed2e55018e64772ce2c1f6646cf586e0a2ffa14cfa045d`.
The outcome graph still reads only
`source.metadata.floorwise_visual_projection`, which final authority
intentionally removes. The certified final visual certificate exists in the
new `feature.properties.geometry_artifact`, and render evidence carries both
visual transport and final legal hashes, but that graph consumer has not yet
been migrated.

This is a post-render-evidence graph contract error, not a return of the
candidate semantic/dominance failure. r5 emitted no accepted final result and
must not be counted as PNG/FAR/law/parking/hash evidence. Do not restore the
legacy sibling certificate. Add a final-authority outcome-graph branch that
uses the validated geometry artifact and preserves the dual identities. No
PNU2/target-ten or further PNU1 run before RED/GREEN and review.

### Task 5 r5 outcome-graph migration: GREEN and independently APPROVED

The exact r5 failure was reproduced before editing. The final-authority branch
now obtains the certificate from
`candidate.feature.properties.geometry_artifact`, validates it with the
external semantic anchors, compares rendered visual transport hash against
`projectedVisualGeometryHash`, and independently compares rendered final,
artifact final, and source bridge final hashes. It records visual and
final-legal identities separately. The legacy source-certificate branch is
unchanged; no stale sibling was restored.

Verification:

- focused exact outcome/dual-hash test: 1/1 GREEN in 0.075 s;
- mass+flow: 64/64 GREEN in 0.799 s;
- full four-module: 140/140 GREEN in 85.504 s, exit 0;
- compileall/scoped diff checks exit 0.

Independent review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r5-outcome-graph-migration-review.md`
APPROVED. Fresh attacks on artifact surface, missing anchor, rendered visual,
rendered final, and source bridge final all reject; final without a legacy
certificate succeeds; legacy behavior remains GREEN.

No PNU rerun has occurred after r5 as of this checkpoint. One PNU1
target-three r6 is now authorized; PNU2 and target-ten remain gated.

### Task 5 PNU1 diagnostic target-three r6: rendered-feature handoff failed

Exactly one r6 PNU1 run at
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r6/20260728T174004079223Z-01-pnu-1168011800104170004`
again reached gym 27 evaluated / 17 compiled / 12 program-passed, pool 20,
selected three, scopes two of three. It then repeated
`certified=missing rendered=b8835f...` in outcome graph.

The r5 final branch is correct for an artifact-bearing candidate, but the
production portfolio deep-copies each original `candidate.feature` into a
separate rendered `features` list and adds `geometry_artifact`/semantic anchors
only to those copies. `observe_portfolio_render()` was still called with the
original selected candidates, so it could not see the exact rendered feature.
The focused r5 test passed an artifact-bearing feature directly and missed this
handoff boundary.

Required correction: outcome observation must receive the exact rendered
feature list explicitly (or an equivalent immutable artifact bundle) and zip
it with selected candidates and render evidence. It must not mutate the
selected candidates or restore stale source metadata. Add a production-shaped
integration RED. r6 is failed evidence only; no accepted PNG/FAR/law/parking/
hash summary and no PNU2/target-ten/rerun yet.

The first explicit `render_features` implementation passed the equal-length
production-shaped path but independent review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r6-rendered-feature-boundary-review.md`
REJECTED its cardinality boundary. Python's three-way `zip()` silently emitted
zero observations for candidate/feature/evidence length mismatches, and an
explicit non-dict rendered feature could fall back to `candidate.feature`.
Required fix: materialize the three iterables, require exact cardinality,
require every explicitly supplied feature to be a dict, and permit legacy
candidate-feature fallback only when the entire `render_features` argument is
omitted. No PNU rerun.

### Task 5 r6 rendered-feature boundary fix: GREEN and independently APPROVED

Portfolio now passes the exact deep-copied rendered feature list explicitly to
outcome observation. The observer materializes candidate and render-evidence
iterables and requires exact cardinality in all modes. When rendered features
are explicitly supplied it also requires an equal count and dict type for
every item; only omission of the entire argument enables legacy
`candidate.feature` fallback.

Verification:

- focused production-shaped outcome test: 1/1 GREEN in 0.063 s;
- mass+flow: 64/64 GREEN in 0.810 s;
- full four-module: 140/140 GREEN in 85.538 s, exit 0;
- compileall/scoped diff checks exit 0.

Independent re-review
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r6-rendered-feature-boundary-re-review-round-2.md`
APPROVED. Both legacy mismatch directions, all three explicit mismatch
directions, and explicit `None` fail before observation with zero observation
delta; normal final, legacy fallback, and dual-hash tamper paths are correct.

No PNU rerun occurred after r6 as of this checkpoint. One PNU1 target-three r7
is authorized; PNU2 and target-ten remain gated.

### Task 5 PNU1 target-three r7: pipeline completed, overall gate failed

Checkpoint time: 2026-07-29T02:55:20+09:00.

Exactly one authorized PNU1 r7 run completed at
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r7/20260728T175027967070Z-01-pnu-1168011800104170004`.
The run did not throw, but its authoritative result is
`completed_with_failed_gate` / `diagnostic_only`, not an accepted MASS
product.

Program outcome:

- gymnasium: selected 3; downstream legal/geometry/parking/combined gates all
  3/3;
- neighborhood: selected 0;
- cultural: selected 0.

Gymnasium original PNG
`maas-book-gymnasium-3-smoke.png` was opened at original detail. It contains
three actual orange mass models rather than placeholder boxes: a folded/curved
form, carved parallel lifted bands, and a sawtooth/ribbed stepped form. The
three cards report FAR 51%, 38%, and 40% against the displayed 78% cap.
Only two distinct BOOK scopes are represented, so this is useful diagnostic
diversity but does not prove all-program or six-scope diversity.

The neighborhood and cultural programs reached preselection but failed the
final legal gate with `authored_mass_outside_legal_envelope`:

- neighborhood: one preselection candidate, scope 1/2, then legal 0/1;
- cultural: four preselection candidates, scopes 3/8 (three) and 1/2 (one),
  then legal 0/4.

This establishes the next debugging boundary: determine from exact polygons,
coordinate frames, difference areas, and hashes whether these are real illegal
solids or a host/principal-frame comparison defect. Do not relax containment
or diversity thresholds.

The combined archive carries one law-graph identity,
`bc2f5be63b8b9131f11f1ba8448f894d477650da1479d1902aab3a8973ac6b00`,
and three distinct compiler/legal final geometry hashes:

1. `1bf4227eb774834eaf81b9cf4c5039a127b41a89139b87833f018c2848d9bbf0`
2. `3a9cf6ea8cd58ef324fcf4ccc05ca06291c379e906818e44d5765540d1a765c7`
3. `e95a3a09f447d8762ea82027cd63d97def0bbbc9847ba275e91aac319917a2c9`

All three gym rows currently report parking required/provided 0/0 and
`needs_swept_path_review` while hard-pass is true. That conflicts with the
earlier working expectation of two required spaces and is under independent
audit; do not claim parking correctness yet.

No r7 image is copied into `docs/mass` as final because the overall target is
0/3/0 rather than 3/3/3. No PNU2 or target-ten is authorized. Two read-only
parallel audits are active: exact containment/frame evidence for neighborhood
and cultural, and independent gym PNG/hash/FAR/law/parking evidence review.

### Task 5 r7 independent gym evidence audit

Independent report
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r7-gym-accepted-evidence-audit.md`
verdict: the three gym cards are valid diagnostic-only MASS evidence, but they
are not a completed portfolio or Neo4j-complete legal/parking certification.

The original 1920 x 394 gym PNG SHA-256 is
`a468c8acb72de26da026ca6a6450d824b527583583dd77722bc9a7bb959656a1`.
Independent material-pixel ratios 0.04633 / 0.04707 / 0.04262 exactly reproduce
the persisted render evidence. Each card has a unique visual transport hash
and a unique final-legal hash, with row/artifact/render/outcome mappings
agreeing. The final-legal metrics are:

- card 1: GFA 135.459 m2, BCR 22.867%, FAR 51.286%, height 5.894 m;
- card 2: GFA 100.894 m2, BCR 15.588%, FAR 38.199%, height 5.894 m;
- card 3: GFA 104.646 m2, BCR 15.954%, FAR 39.620%, height 5.894 m.

All three report zero clipping, retention 1.0, and plan IoU 1.0. The current
gym floor-capacity authority is a two-floor clear-span plan; none reaches its
capacity target and none fills the FAR envelope.

Parking zero is internally consistent only with the current local seed rule
`seoul_parking_appendix2_row_10_other`: GFA / 200 m2 yields raw values below
one and note 6 rounds the total below one to zero. It is not authoritative
parking proof because graph status is `not_requested`, ordinance/appendix
source fields are null, and swept-path layout is unverified. The earlier
two-space expectation is not supported by r7 and may have assumed five floors,
larger GFA, or another use classification.

The combined `law_graph` value is a canonical hash of persisted legal context,
not an explicit Neo4j query result; no row has an explicit
`law_graph_evidence_hash`. The summary flag
`final_geometry_hash_agreement=false` is misleading because it compares
different candidates as if all should share one final hash; distinct candidate
hashes are correct and their per-row mappings agree.

Gym diversity is real at the operation and phenotype level but insufficient:
only scopes 1/1 and 1/2, two roof archetypes, repeated sawtooth, no upper-band
stepped candidate, same height, low FAR, and selected 3 versus full minimum 10.
Do not present r7 as completion.

### r7 containment actual-path RED and correction

The host/frame audit found all programs use the same local-UTM
`horizontal_buildable_envelope`; gym passes because its two legal floor
sections do not shrink, while neighborhood four-floor and cultural five-floor
sources fail only where upper sunlight sections shrink. Independent report
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r7-legal-envelope-preselection-forensics.md`
has SHA-256
`810d460856d81dd36f749483d5971668aa833329a6712016cb963dd2270a3649`.

An initial 5e-8 m probe against legacy
`_matrix_fit_polygon_to_host()` found a real tolerance mismatch, but code
tracing proved that selectable r7 candidates do not call that function. The
probe test and production change were reverted and must not be treated as r7
evidence.

The actual production path is:

`append_floorwise_legal_projection()`
`-> compile_site_bound_geometry_program_to_source_mass()`
`-> downstream _evaluate_candidate()`.

A deterministic r293-shaped four-floor reproduction with legal areas
102.931 / 102.931 / 74.989 / 51.471 m2 showed:

- the floorwise compiler certificate reports all sections contained;
- exported floors 1-3 have exact difference area zero;
- exported floor 4 has difference area
  `4.39189804524e-08 m2`, exact `covers=False`, but buffered
  `covers=True`;
- downstream epsilon is around `5e-11 m2`, so the same final source fails.

Actual-path TDD RED
`MaasStageHardContractTests.test_final_floorwise_program_exports_exact_contained_source_volumes`
failed on the floor-4 exact containment assertion.

The approved single-authority design excludes relaxing downstream or clipping
only a separate SourceVolume proxy. An initial inward CSG margin of `1e-7 m`
made the r293 exact-containment RED green, but a shrinking lower/lower/middle/
upper stack exposed approximately `1e-7 m` mesh edges below the compiler's
`1e-5 m` minimum. The floorwise certificate incorrectly passed before the
site-bound exporter rejected `tiny_edge`.

A second actual-path RED now requires a certified shrinking floor stack to
have an empty ordinary `compilation_gate()` result and a non-null site-bound
export. The corrected margin is derived from the shared gate policy:
`GeometryGatePolicy.minimum_edge_length * 2 = 2e-5 m`. Floorwise projection
also runs the ordinary compilation gate before issuing a hard-pass
certificate. The shrinking-stack export, r293 exact containment, and existing
0.005 m2 true-escape rejection are GREEN.

Certification and downstream still use the original unbuffered legal
polygons. The r293 four-floor total area loss is `0.00289014684362 m2`
(retained ratio `0.999991303173`), and every exported floor proxy has exact
difference area zero and `covers=True`.

This changes the final mesh itself, preserves one final geometry authority,
and does not lower a legal threshold. Full regression and independent review
remain required before one controlled PNU1 target-three rerun. No PNU2 or
target-ten.

Round-2 review confirms the 2e-5 inset itself: shrinking-stack minimum edge is
about `2.000000000013e-05 m`, ordinary gate clean, export succeeds, r293 exact
escape is zero, and 0.005 m2 escape still rejects. It found a separate
certificate/export policy mismatch: floorwise certification currently runs
the default geometry policy (`maximum_components=5`), while mandatory
site-bound export uses `GeometryGatePolicy(maximum_components=1)`. A canonical
UnitBox program producing two separated components can therefore be certified
hard-pass and then rejected by export. Required next RED/GREEN: reproduce this
counterexample and make certification use the exact export policy. Current
round-2 verdict is REJECT until that closes.

### Post-GREEN regression baseline and active reviews

Running floorwise legal program + shared-floor + mass-stage modules found 83
tests total with 8 failures and 1 error. The exact same 8+1 signature already
occurred before the actual-path legal CSG inset; after the inset the new
exact-containment test and all floorwise legal-program tests pass, with no new
failure. The pre-existing failures group around:

- `_materialize_directed_geometry()` returning `None` in older fixtures after
  Task 5 final semantic/context requirements;
- downstream combined-pass expectations built on older fixture authority;
- one `_program_pool()` fixture whose `generation_context` lacks the now
  required `generation_site`.

These are not silently accepted as harmless. A semantic/context reviewer is
triaging stale fixtures versus production bugs read-only. A second independent
reviewer is auditing the 1e-7 inward CSG correction, hash/surface authority,
area impact, holes/concavity, and real-escape behavior. A third law/parking
agent is auditing why r7 used a canonical law-context fallback and local
parking seed with Neo4j `not_requested`. No PNU rerun until all three report
and required regressions are GREEN.

Regression fixture implementer completed test-only repairs:

- nine repaired cases: 9/9 GREEN;
- floorwise/shared-floor/mass-stage: 84/84 GREEN in 5.600 s;
- Task 5 mass-product/single-execution/elevation evidence: 105/105 GREEN in
  85.450 s;
- no production gate or threshold changed.

It added one shared canonical gymnasium semantic fixture, supplied explicit
PNU/site/capacity identities to direct materialization tests, changed legacy
metric-only fixtures to assert semantic/combined fail-closed, used a real
generation context, and made the intentionally infeasible noncanonical
target-ten fixture assert joint-solver infeasibility. Independent task review
is active; do not count this task complete until review approves.

### r7 Neo4j law/parking runtime audit

Independent report
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r7-neo4j-law-parking-runtime-audit.md`
SHA-256:
`ccd6de9c2062aed332c4ec77ff979f43a819876f9f71a49ed443e31cdac2fca4`.

Findings:

- r7 numerical zoning came from the live hard path
  VWorld -> zoning mapper -> regulation calculator -> constraints. It was not
  synthetic, but it was not Neo4j-derived.
- r7's combined `law_graph` value is only a canonical persisted legal-context
  hash, not explicit graph-agent evidence.
- r7 parking options carried only road context. Neither
  `MAAS_ENABLE_PARKING_NEO4J=1` nor `use_neo4j` was supplied, so the loader
  intentionally used `local_structured_seed` with graph `not_requested`.
- Neo4j connectivity and data are healthy read-only: JO 4928, HANG 12069,
  ParkingRule 11, LocalParking 14; law seed 6/6; law-agent service health 200
  and evidence pass/search 3; parking validation 49/49 plus 23/23.
- Graph-backed parking still computes zero required spaces for the current
  gym GFA under Seoul other-building area/200 and the below-one rounding
  rule. Neo4j restores ordinance provenance; it does not turn this case into
  two spaces.
- The next run can opt into graph parking without code by setting
  `MAAS_ENABLE_PARKING_NEO4J=1`, leaving
  `MAAS_DISABLE_PARKING_NEO4J` unset, and using the configured credentials.
- BOOK portfolio has no current law-specialist evidence call or explicit
  `law_graph_evidence_hash` producer bound to PNU + program + capacity +
  final geometry. A parking flag alone cannot satisfy the approved law-graph
  identity contract. This wiring is a separate pre-PNU blocker.

### 2026-07-29 CSG component-policy GREEN checkpoint

The round-2 certificate/export mismatch now has an exact RED and minimal
GREEN. A connected canonical UnitBox-authored block intersected with a
connected concave legal polygon can split into two final components. Before
the fix, floorwise certification used the default
`maximum_components=5`, issued a hard-pass certificate, and the mandatory
site-bound exporter immediately returned `None` because it requires one
component.

`append_floorwise_legal_projection()` now runs its final pre-certificate gate
with the exact export policy:
`GeometryGatePolicy(maximum_components=1)`. The existing shared-policy
`2e-5 m` legal inset, ordinary compiler gates, exact unbuffered containment,
and 0.005 m2 true-escape rejection remain unchanged.

Root independently reran the complete floorwise module plus both actual-path
containment regressions: 8/8 GREEN in 1.63 s. Implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-csg-certificate-export-policy-report.md`.
Independent round-3 review is active; this is not yet authorization for a PNU
rerun.

Round-3 independent CSG review is now APPROVE. The reviewer reran 8/8 focused
tests in 1.66 s and independently confirmed: authored/placed inputs each have
one component; the connected concave legal polygon is valid; the split-output
counterexample is rejected before certification; certificate and mandatory
export use identical `GeometryGatePolicy` values with
`maximum_components=1`; the 2e-5 inset remains exactly twice the shared 1e-5
minimum edge; and exporter program/geometry hash checks remain intact. Report
SHA-256:
`89d1beb91658e1e8cc41e986de1997e0a04d3e903420509794b9b3c65ec513d8`.
CSG legal-solid blocker is closed.

The regression-fixture independent review rejected one test-evidence detail
despite all tests being green: the shared fixture reused fabricated non-hex
`"s"*64` and `"m"*64` site/capacity identities across different polygons and
outcomes. Product logic was not implicated. The fixture implementer is
replacing them with the production `semantic_site_context_hash()` of each
exact site and the honest pre-measurement
`pending_capacity_measurement` identity, with persisted-context assertions.
Current post-CSG integration baseline is 85/85 GREEN; Task 5 evidence baseline
is 105/105 GREEN. Fixture task remains unapproved until re-review.

Focused fixture re-review is now APPROVE. Fabricated identity constants are
gone; each site hash is production-derived from the exact PNU/program/polygon;
pre-measurement capacity uses the honest `pending_capacity_measurement`
sentinel; and a measured requested-shortfall is rebound to an empty achieved
band in both final context and semantic evidence. Reviewer ran 4/4 GREEN in
0.451 s and found no production-gate change. Review SHA-256:
`84fd6f806ebc0db7306c6aec52b9dd385791fcd793593dc3b7043e6990991439`.
Root's final post-rebind integration run is 85/85 GREEN in 5.600 s. Regression
fixture blocker is closed.

Sequential Task 5 law/parking identity wiring implementation is now active
under the written brief. It is TDD-only with injected/mocked external sources:
no PNU, live VLM, Neo4j mutation, or target-ten run. It must remove the
verifier fallback, batch expensive law sources once per program, bind full
evidence separately to each exact final MASS identity, persist the explicit
hash/payload, fail closed on missing evidence, and preserve VWorld/calculator
numeric authority.

### 2026-07-29 law/parking identity wiring GREEN checkpoint

The bounded TDD implementation is complete and pending independent review.
Implemented behavior:

- one graph projection and one bounded law-domain search snapshot per selected
  building-program portfolio;
- a separate full `AgentEvidence` payload and canonical hash for every final
  MASS identity using stable execution id, final legal program hash,
  non-sentinel floor-capacity-plan hash, PNU, and
  `finalLegalGeometryHash` (never projected visual hash);
- payload/hash/status/identity continuity validation with fail-closed selected
  row, passport selector, geometry artifact, program failure, verifier summary
  and process exit;
- no verifier hash fallback from `legal_context`;
- successful parking graph source recorded as `neo4j/available`, with honest
  local/unavailable states retained and propagated through candidate/row/
  passport/artifact;
- numeric VWorld/regulation-calculator `legal_projection` remains unchanged.

TDD and regressions recorded in
`task-5-law-graph-parking-identity-wiring-report.md`:
focused 8/8, consolidated 190/190 in 13.625 s, BOOK language 84/84, and
flow/elevation/law 75/75 in 76.400 s. No live PNU, VLM, or Neo4j mutation.
Independent read-only law identity review is active. Do not run PNU until it
approves.

Independent law identity review verdict is REJECT, report SHA-256
`645e2022d8d59d47ec7bc0cf9c9aab82c19399687bdc53fd705c0b5e8eafc301`.
Three verifier/persistence blockers were reproduced:

1. valid law evidence alone could make the runner exit 0 even when run,
   downstream, parking, and selected combined gates failed;
2. the final law-bound passport was not copied back into the selected summary
   row, leaving its nested passport stale and unverified against row/artifact
   copies;
3. `final_geometry_hash_agreement` incorrectly required every diverse MASS to
   share one global hash instead of checking continuity within each MASS.

The implementation repair is active with exact REDs. Diagnostic target-three
semantics remain distinct from production target-ten requirements: acceptance
must use requested diagnostic count plus per-selected-MASS legal/parking/
combined evidence and per-row final-hash continuity, not production-only
portfolio failures. Top row, final passport, and a compact artifact law
binding must all be present and equal. No PNU yet.

All three law-review blockers now have RED/GREEN fixes and await re-review:

- bounded-probe acceptance checks explicit failure statuses, requested
  diagnostic count, per-selected combined/parking evidence, downstream status,
  explicit law evidence, and final identity;
- final geometry agreement is per MASS across required row/render/final
  passport channels, so diverse candidates may have distinct hashes;
  elevation/archive are reported optional and enforced when present;
- the final law-bound passport replaces the selected-summary passport, and a
  compact `geometry_artifact_law_binding` persists exact identity + full
  payload + canonical hash; verifier requires equal valid top-row/passport/
  artifact copies and rejects missing/tampered carriers.

New adversarial focused tests are 14/14 GREEN. Final combined law/BOOK/
floorwise/shared-floor/MASS-stage/flow/elevation regression is 349/349 GREEN
in 93.060 s; py_compile and scoped diff-check pass. Updated report SHA-256:
`b73f387c2a0617a5d21c81ef702c29a87e998e7d70b281d943365975db62702e`.
Independent re-review is active. No PNU yet.

First law re-review repair closed the original copy/hash/bypass mechanics, but
the same reviewer issued a second REJECT (review SHA-256
`f07db21e1e029985425dcbdd822371d1ba1fe9524c4cd74d758da9f8f8c80a82`)
on three more diagnostic-runner markers: an explicit program `status=fail`,
a diagnostic-target result not marked `diagnostic_only`, and a selected
render with `hard_pass=false` could still pass. Exact isolated REDs failed
3/3 before the fix. The verifier now requires top and program diagnostic
markers/status plus every selected render hard pass. Expanded law suite is
17/17 GREEN; regression and another independent re-review remain pending.
No PNU.

Third focused law identity re-review is APPROVE. Review SHA-256:
`c85553abdb1041e09bbd5522d4df535997b39670a7300483cc88027a6e0fa18b`.
Independent isolated checks confirm only the complete diagnostic contract
passes; invalid top/program diagnostic markers, explicit program failure,
render hard-pass failure, cross-copy law tamper, and optional geometry mismatch
all reject. Fresh focused 18/18 and compact 166/166 are GREEN. This approval
permits one bounded PNU1 target-three probe, but is not live-PNU acceptance
evidence.

Next authorized command boundary:

- PNU `1168011800104170004` only;
- diagnostic target 3 only;
- `MAAS_ENABLE_PARKING_NEO4J=1`;
- `MAAS_DISABLE_PARKING_NEO4J` unset;
- live VLM/OpenAI disabled by the verifier;
- new r8 output root;
- no PNU2, target-ten, or `docs/mass` copy unless PNU1 produces 3/3/3 and
  passes original-resolution PNG, explicit law payload/hash, Neo4j parking
  provenance, per-MASS final-hash continuity, and all hard gates.

The next sequential implementation blocker is now specified in
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-law-graph-parking-identity-wiring-brief.md`.
It requires one bounded law source lookup per program, per-MASS evidence bound
to PNU + final program + capacity + final geometry, explicit persisted hashes,
positive Neo4j parking provenance, and removal of the verifier's legal-context
fallback. No PNU, PNU2, target-ten, or `docs/mass` copy yet.

## 2026-07-29 continuity checkpoint — PNU1 r8 target-three result

The law review approval authorized exactly one PNU1 target-three probe. Parking
Neo4j was explicitly enabled and preflight returned
`status=loaded, source=neo4j, graph_status=available`. The first direct-script
launch failed immediately with `ModuleNotFoundError: design`; it produced no
product result. The corrected module launch completed normally in about
1 minute 40 seconds, so r8 is not a hang:

`python -m tools.verify_single_authority_mass_pnus --pnu
1168011800104170004 --output-root
.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r8
--diagnostic-target 3 --inactivity-timeout-seconds 180`

Canonical r8 run directory:

`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r8/20260728T193417732224Z-01-pnu-1168011800104170004`

Parent evidence:

`.superpowers/sdd/2026-07-28-single-authority-legal-mass/artifacts/task5-pnu-probes-r8/combined-summary.json`

Result is intentionally **not accepted**. Top state is
`completed_with_failed_gate`, diagnostic status is `diagnostic_only`, and the
only bounded failure is `program_diagnostic_target_not_met`. Exact selected
counts are neighborhood 2/3, gymnasium 3/3, cultural 2/3 (seven total). All
seven selected products pass final legal geometry agreement, downstream legal,
parking, combined, render hard-pass, and explicit law identity continuity.
Every law hash and final legal geometry hash is explicit and unique. Parking
provenance is `neo4j/available`; neighborhood products require/provide 2/2
spaces and the remaining products require/provide 0/0. The portfolio FAR range
is approximately 38.199–96.456.

Original-resolution PNG inspection, not thumbnail-only inspection:

- neighborhood PNG contains two real cards plus three empty placeholders.
  Both selected forms are materially similar stepped/pyramidal stacks
  (`lift`, `skew`), so it does not meet the requested diversity bar.
- gymnasium PNG contains three materially different real masses: an
  expanded/folded plane, a carved/lifted U/band, and a ribbed/sawtooth mass.
- cultural PNG contains two real cards plus three empty placeholders. Both are
  materially similar stepped/pyramidal stacks with local notch/puncture
  variation, so it does not meet the requested diversity bar.

Selection diagnostics show a supply problem, not a downstream legal failure:

- neighborhood pool 4, selected 2; the two remaining candidates are excluded
  only by `pyramidal_like_cap`.
- gymnasium pool 20, selected 3; 16 unselected candidates remain otherwise
  eligible.
- cultural pool 5, selected 2; two remaining candidates are exclusively
  pyramidal-like and the third also hits concept/genotype/silhouette limits.

Do not lower the pyramidal cap, reinterpret these near-identical forms as
diverse, copy them to `docs/mass`, run PNU2, or run target-ten. The next task is
a bounded TDD generator/replenishment fix that creates genuinely distinct
non-pyramidal legal candidates for the shrinking neighborhood/cultural legal
contexts while preserving UnitBox 1/1 authority, Matrix4 transforms, typed
BOOK/CSG, exact capacity, and all law/parking/hash gates. Two independent
read-only reports are active:

- `task-5-r8-diversity-supply-forensics.md`
- `task-5-r8-selected-evidence-audit.md`

### Independent r8 selected-evidence audit

The evidence audit is complete and the final-product verdict is
**INVALID / REJECT**. Report SHA-256:
`33666240256442390F17FAAFDA268BF1D6E27F1C2B674EDF639FD6554038C751`.
The report is
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-selected-evidence-audit.md`.

Verified diagnostic positives:

- all seven program hashes, final legal geometry hashes, law hashes and visual
  hashes are unique;
- all row/gate/passport/artifact law copies and final geometry/render/surface
  identities are continuous;
- Neo4j law evidence is resolved 6/missing 0 plus three search results per
  program;
- authoritative parking join is neighborhood 2/2 using the `/134` rule and
  gym/cultural 0/0 using the `/200` rule. A null field in the selected display
  row is a UI/schema join gap, not loss of the stored identity chain.

New hard blocker discovered by the audit:

- cultural C1 and C2 have `shared_floor_contract_hard_pass=false` (usable
  floors 1/5 and 0/5), yet their legal projection and combined downstream rows
  incorrectly say hard pass. This is a real hard-gate aggregation defect, not
  a display issue.
- gym G1-G3 and cultural C1-C2 capacity passport stages fail; every r8 passport
  remains `in_progress`, final false. VLM, collaboration and elevation were not
  evaluated in this diagnostic run.

Original PNG SHA-256 values:

- neighborhood `abf6c5c26d5b5a2cf33c2072ddf259b3868b2dc3b493a235fced27496b6007b2`
- gymnasium `a468c8acb72de26da026ca6a6450d824b527583583dd77722bc9a7bb959656a1`
- cultural `1542056e5a8ffccbee2f53a28820b4d85a7493d06ac03123cc3b2a148a0ac970`
- combined `2db5cbe8df48e001a415cf346310376c7198f196aa0b6036284bfce069f74637`

Sequential repair order is now:

1. strict TDD so false/missing required shared-floor contract cannot become a
   legal/combined/selected/verifier pass;
2. then fix generation ordering so replenishment pages expose genuinely new
   early topology families rather than spending the diagnostic budget on the
   same first three families;
3. rerun PNU1 target three and inspect every exact PNG and evidence row.

`shared_floor_gate_impl` is the only active implementation agent. The diversity
forensics agent remains read-only.

### Independent r8 diversity-supply forensics

Forensics is complete. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-diversity-supply-forensics.md`.
SHA-256:
`A647E5C86B20D13268143C3BC3C2F989C39C2A4686F8B691B27A2F1D3D3DFF29`.

Root cause is generation ordering, not selector error and not simply too few
cycles. The target-three 36-evaluation loop is seed-major: it spends 12 BOOK
probes on each of only the first three universal form programs. Although each
replenishment page changes `variation_offset=page*64`,
`synthesis.py` currently chooses the early typology prior with
`requested_typology_priors[attempts]`, ignoring that offset. Pages 0 through 7
therefore all begin with the same `inflate(block)`, `carve_void(block)`,
`grid_mass(bar)` topology tranche; parameters drift, and some hashes repeat.
The exact shrinking legal stacks then turn the surviving full-host 4/5-floor
forms into pyramidal-like solids.

Minimal TDD after the shared-floor repair:

1. RED that page 1 must advance early topology while page 0 remains the
   approved additive/subtractive/grid baseline.
2. GREEN by rotating the prior deterministically with
   `(variation_offset + attempts) % prior_count`; with 11 priors and stride 64,
   page 1 begins radial, freeform/bent, additive.
3. A production-shaped frozen-r8-host RED/GREEN is mandatory: under unchanged
   36 evaluations/page and one replenishment, both neighborhood and cultural
   must supply at least three unique final hard passes and at least one
   measured `pyramidal_like=false` final solid after exact floorwise CSG.
4. If rotation alone cannot satisfy the final-geometry test, schedule one
   existing program-independent narrow bent/radial witness. Do not alter the
   pyramidal classifier/cap, floor targets, law gates, or UnitBox/Matrix4/BOOK
   authority.

The sequential implementation contract is frozen in
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-topology-diversity-brief.md`.
Do not start it until the shared-floor fail-open repair is green and reviewed.

### Shared-floor fail-open repair GREEN, review pending

Implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-shared-floor-gate-repair-report.md`.
SHA-256:
`37C670B66B8D2BDE366A8F9C6927221F587C664B6F8313F5FC062DB0BB3C02F0`.

One fail-closed helper now requires schema
`arr.maas.shared_floor_contract.v1`, non-empty `floor_contract_hash`, and
`hard_pass=true`. False, missing, malformed or hashless required contracts
reject downstream legal/combined, selected passport capacity, and bounded PNU
verifier acceptance. Production changes are limited to:

- `mass_passport_bridge.py`
- `downstream_hard_gate.py`
- `verify_single_authority_mass_pnus.py`

Agent regressions: exact adversarial 3/3, shared-floor/MASS/law 102/102,
passport/single-execution/MASS 172/172, BOOK 84/84, py_compile/diff-check
clean. Root independently reran the three exact false/missing boundary tests:
3/3 GREEN in 0.024 s. `shared_floor_gate_review` is now independently reviewing
the change; do not start topology implementation until APPROVE.

Independent shared-floor review is APPROVE. Review SHA-256:
`539D7ED6D3E75056C022398A3CC9DB3246D609B5FD834484E9B441AA5BC646B7`.
Positive and false/missing/hashless contracts were independently reproduced
across downstream, passport and verifier; fresh 3/3 and 102/102 are GREEN.
This closes the fail-open blocker and authorizes the sequential topology-
ordering implementation brief.

Topology-ordering TDD checkpoint: RED reproduced page 1 incorrectly starting
inflate/carve/grid. The minimal `synthesis.py` rotation
`(variation_offset + attempts) % prior_count` is now GREEN 1/1; page 0 is
unchanged and page 1's literal early triple is
radial-wings / bent-bar / primitive-block. No other production change yet.
The required frozen-r8 final legal CSG supply test is now the active blocker.

Frozen-host acceptance RED completed after rotation: 1 test failed in
23.578 s. Neighborhood page 0 produced one accepted candidate, page 1
produced zero; each evaluated exactly 36. Only one unique
shared-floor+capacity-hard-pass final identity survived and it was pyramidal
(`voided`). Therefore topology rotation is necessary but not sufficient. The
agent is now isolating the exact radial/bent loss boundary before using the
brief-authorized single existing narrow program-independent reserve.

### r8 topology reserve / fixture-fidelity checkpoint

Two bounded attempts to promote one existing program-independent SLAB bend
(`agent_bend`, then `agent_bent_bar`) into page 1 did not satisfy the frozen
final-solid test. Both remained zero-output on the affected neighborhood host,
so the experimental reserve promotion has been removed; no failed reserve is
left in production.

The remaining frozen-test RED is not yet trustworthy as a live-r8 equivalence
test. Its page-0 neighborhood diagnostics differ from the saved live r8 run:
the fixture reports compiled/clean/program-pass 7/7/1 (and lineage retains
zero), whereas live r8 reports 8/6/2 (and lineage retains one). The mismatch
was traced to incomplete run inputs in the hand-frozen harness, including a
synthetic PNU suffix and empty access context. The harness now uses exact PNU
`1168011800104170004` and the saved east-access/west-program-frame relation;
the forensics agent is completing the final equivalence check. Do not run r9,
PNU2, target ten, or copy PNGs to `docs/mass` until this test either faithfully
reproduces r8 and turns GREEN or produces a precise boundary-exhausted REJECT.

The exact-equivalence audit is now closed as **BOUNDARY EXHAUSTED / REJECT**.
Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-topology-diversity-report.md`.
SHA-256:
`7A3A5446D76AE55FCDDD98AEF5BB7A642C1B9B6762BD94BD586819C6C6A2A29C`.

After restoring the exact PNU, saved east-access/west-program-frame relation,
road width, legal sections, targets and dimensional contexts, the current
production path still drifts from the saved r8 artifact at directed geometry
materialization. Final frozen evidence: page 0 accepts zero; rotated page 1
accepts two unique shared-floor+capacity-hard-pass hashes, but both remain
measured pyramidal; radial and bend materialize zero. The focused harness was
removed after evidence capture because it is intentionally RED. Both allowed
existing-SLAB reserve trials were removed. Only the deterministic page-offset
rotation remains in production, with its focused unit test GREEN 1/1.

Therefore the next step is a new geometry/program-projection design brief:
radial/bent source graphs must intrinsically survive host fit, public/program
projection and floorwise legal CSG as one connected, adequately covered solid.
Do not add another scheduling exception and do not change legal, capacity,
morphology, selector or floor-target gates. Two read-only agents now audit
(a) viable normalized final-solid topology supply and (b) the exact
CSG/morphology loss boundary before a single implementation author is chosen.

### r8 CSG / morphology-loss audit

Read-only audit report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-csg-morphology-loss-audit.md`.
SHA-256:
`9C908597B27D199AA57485A89173FD4B65CABAF219BB973ADE245A102598F986`.

The saved r8 radial/bent absence and the post-rotation loss are different:

- saved r8 never evaluated radial/bent at all: seed-major 12 evaluations per
  genotype exhaust the 36 cap on synthesis indices 0..2;
- executable core bent/radial are indices 64/65, first reachable at
  evaluations 769/781, and page > 0 omits the core lane;
- after rotation, bounded radial/bend each compile as one component and return
  a host fit, but the combined BOOK -> program projection -> floorwise CSG ->
  semantic/export transaction collapses 12 -> 0 behind one undifferentiated
  `None`;
- core bent/radial also compile as one component and host-fit successfully,
  but exact r8 final-floorwise survival is not yet proven.

The audit also confirms the user's objection about floor areas. Current
`append_floorwise_legal_projection` independently applies a principal-frame
Matrix4 to every occupied floor band to hit proportional target floor areas,
then clips to the legal section. This makes neighborhood top/ground
`0.50005` and cultural `0.43756`; with 4/5 levels both are pyramidal by
construction. Those target values are capacity/law evidence, not a plan or
MASS authoring language at this design stage.

The next brief must therefore preserve:

- exact legal sections as hard maximum CSG clips;
- the unchanged aggregate capacity/FAR minimum and measured final GFA;
- per-floor target values and hash as provenance/advisory evidence;
- the authored placed UnitBox/Matrix4/BOOK solid as the geometry being clipped.

It must remove per-floor target-area Matrix4 resynthesis from geometry
authority, then expose both bounded synthesis and the already-declared
executable core lane within the same bounded diagnostic budget. No capacity
minimum, legal gate, morphology classifier, selector cap or floor target value
may be reduced.

The independent final-solid supply architecture agrees. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r8-final-solid-form-supply-architecture.md`.
SHA-256:
`0FC1D75CB091D12B041EE4985E64CACD1DEEB05B41464E2A92C60B1778F55807`.
It directly probed ten core families on the frozen host: lane exposure alone
still produced old-projection top/ground ratios `0.1675..0.4034`, so the
floorwise authority repair must precede scheduling. It then specifies page-0
slots 0..2 unchanged, bounded/core round-robin after slot 2, and diagonal
genotype x BOOK traversal so the unchanged 36 cap sees 36 distinct genotypes
before second probes.

The sequential implementation plan is:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-authored-solid-implementation-plan.md`.
Implement floorwise authored-solid preservation and aggregate identity/capacity
regressions first; review them; then implement two-lane breadth scheduling;
finally require exact frozen neighborhood+cultural GREEN before PNU1 r9.

Floorwise implementation RED is captured: two focused tests fail on the old
code because changing only advisory targets can make projection uncertifiable,
and a bent/offset authored section is changed by per-floor target matrices.

Read-only pre-review found two additional critical boundaries that the direct
projector RED alone does not cover:

1. `_materialize_directed_geometry` currently derives the one site-placement
   scale and minimum plan area from `max(target_floor_areas_m2)`. The
   production-shaped path must also be invariant to advisory per-floor vector
   changes; any retained global scale must be explicitly aggregate-capacity
   steering, not a per-floor maximum.
2. Advisory targets and plan hash currently sit in reachable executable node
   parameters. Because `program_hash()` includes them, identical final meshes
   can receive different final program hashes and masquerade as diversity.
   Advisory values/hash must live in certificate/metadata provenance only;
   identical executable geometry must have identical final program and
   geometry hashes.

Further review gates after this first GREEN: recompute/validate the shared-floor
seal rather than trusting an asserted hard pass; require measured final-solid
utilization for every capacity band; equate measured shared-floor GFA with
legal/FAR/parking area; preserve complete source export; reject missing upper
bands/disconnected unions; and bind every downstream consumer to the final
compiler hash.

### r9 authored-solid steps 1-2 implementation GREEN, review pending

Implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-authored-solid-implementation-report.md`.
SHA-256:
`C18D564599F97067EB98C1504FC3C6C42DF504F41AC5294C0AD33D9D9C0795F9`.

Implemented:

- final geometry is authored root -> horizontal band -> exact legal prism
  intersection -> union; no per-floor target-area scale;
- per-floor targets and plan hash are metadata/certificate only and absent
  from reachable executable nodes;
- the only placement size steering is one global
  `sum(target_floor_areas)/floor_count` aggregate plan target;
- same-total `(600,200)` and `(400,400)` production materializations have
  identical final program hash, geometry hash, volumes and surfaces;
- capacity-band resolution requires finite measured final-solid utilization,
  a finite positive program-specific minimum, and the exact requested or
  selectable target; neighborhood 0.70 and cultural 0.40 remain unchanged;
  missing/NaN minimum fails closed.

Agent verification: focused 94/94, related 311/311, py_compile and targeted
diff-check GREEN. Root independently reran the focused floorwise/shared-floor/
MASS product suite: 94/94 GREEN in 1.866 s. Independent
`authored_solid_review` is active. Do not start form-bank/scheduling changes
until APPROVE.

Independent fast review is **APPROVE**. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-authored-solid-review.md`.
SHA-256:
`7B866CEB2A0154E4D63FF32138C1CDDF6519CCBAC97B7EDD29B186940CE3CB9F`.
Seven exact methods passed. A 17-node reachable final DAG contained no
`target_floor_areas`, `floor_capacity_plan_hash` or advisory label; same-total
materialization identity, bent/offset preservation, neighborhood 0.70,
cultural 0.40 and missing/NaN fail-closed were independently reproduced.
This approves implementation-plan steps 1-2 only. It is not PNU, render,
law/elevation or diversity approval. Steps 3-4 (two-lane supply and diagonal
genotype x BOOK traversal) may now begin.

### r9 breadth-supply steps 3-4 GREEN; frozen step 5 RED

Implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-breadth-supply-implementation-report.md`.
SHA-256:
`61C1B2D9828C62E4050DA79C788F588DC4DEC777FFC4EE543252CA5A46F08C2E`.

Implemented and verified:

- page 0 preserves inflate/carve/grid slots 0..2, then round-robins bounded
  synthesis with executable core; page 0 is 82 unique (64+18), page 1 is 64
  new bounded records with no fixed-core replay;
- the executable MASS control bank filters every program that is not exactly
  one canonical `box(1,1,1)` UnitBox primitive, fills missing records from
  deterministic reserve lattice offsets, and deduplicates hashes; all page0
  and page1 records now satisfy the UnitBox authority;
- diagnostic cap 36 overrides candidate-cap early stopping and evaluates one
  lineage-safe base BOOK probe for 36 distinct genotype hashes before any
  second probe; first36 includes 16 core records and 36 unique parent keys;
  non-diagnostic scheduling remains unchanged.

Focused 6/6, geometry+MASS 230/230, pycompile/diff-check GREEN.

Exact frozen r8 authority test:
`ARR/backend/design/test_maas_r9_frozen_acceptance.py`.
It uses saved PNU1 legal polygons, targets/hashes, dimensions, west program
access/east road relation, 60/250 BCR/FAR, page0+one replenish, 36/page, no
network/Neo4j/VLM. Final result remains RED:

- neighborhood: page0 36/31 compiled/26 clean/0 program pass; page1
  36/32/25/1; one eligible unique winged identity, still pyramidal;
- cultural: page0 36/31/24/5; page1 36/31/21/6; four eligible unique
  identities, but all four pyramidal (stepped/stepped/curved/stepped).

Thus nominal supply and UnitBox authority are fixed. Remaining boundaries are
(a) neighborhood program gate semantics after 51 clean solids and (b) final
top/ground morphology despite authored-solid clipping. Two read-only agents
are isolating those independently. No live r9 is authorized.

### r9 neighborhood program-gate root cause isolated

Read-only report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-neighborhood-program-gate-forensics.md`.
SHA-256:
`FF0535C1CD872BB4C0C83BEBA0EB2C7850E8195240CDBDAA28D6F8266E04B6F1`.

Exact frozen reproduction:

- page 0: 36 evaluated / 31 compiled / 26 clean / 0 program pass;
- page 1: 36 / 32 / 25 / 1;
- every one of the 50 clean failures includes `dominant_ratio`; hierarchy and
  coherence do not fail;
- the single pass is `agent_shear`, utilization 0.7136.

The failure is not a missing form family. Verified semantic carriers are
rebound after capacity measurement. When no capacity band is achieved,
`achieved_capacity_band=""`; the spatial carrier audit treats that honest
capacity miss as `achieved_capacity_band_mismatch`, clears all carriers, and
therefore measures one undifferentiated dominant solid at ratio 1.0/score
0.21. The shear is the only record whose measured utilization resolves
`spatial_reserve`, so it retains seven carriers and passes.

Required TDD boundary: spatial semantic-carrier geometry verification and
downstream capacity identity are separate fail-closed audits. A below-capacity
candidate may retain verified spatial carriers for program-relation scoring,
while downstream capacity must remain false. Tampered program/geometry/
surface/carrier evidence must still fail. Do not permit a blank band, lower a
threshold, or relabel a miss as achieved. This correction alone cannot meet
neighborhood target 3 because page 0 remains below 0.70 and page 1 has only
one capacity-valid candidate; aggregate placement/capacity supply remains a
separate geometry issue.

### r9 non-pyramidal preliminary exact measurements

Frozen final eligible section vectors are:

- neighborhood shear: `[72.974654, 72.687779, 52.948037, 37.484229]`,
  top/ground proxy ratio 0.5137, GFA 236.095 versus required 232.625;
- cultural eligible records have top/ground proxy ratios 0.3205, 0.4732,
  0.4668 and 0.4448.

Before legal clipping, the same authored solids have top/ground ratios
0.9882 (neighborhood) and 1.0304..1.1391 (three independently measured
cultural records). After exact legal clipping they collapse to approximately
the legal host ratios: 0.5001 neighborhood and 0.4376 cultural. Thus authored
BOOK/Matrix4 z-profiles are not intrinsically pyramidal. The current single
placement is fitted to the ground host; upper legal corridors shrink and
migrate away from it, so clipping removes the authored upper mass. The active
read-only agent is testing a principled common/upper-corridor placement
witness. No placement fix or live r9 is yet authorized.

Final read-only report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-nonpyramidal-final-forensics.md`.
SHA-256:
`FA843199B7C8A4D4E44D4812B180A5B196C983B59D342B08311C923716FE87F5`.

Bounded placement witnesses were both REJECT:

- translation-only while retaining full authored XY containment in the ground
  host reaches at best neighborhood ratio 0.5450 / GFA 241.743 and cultural
  ratio 0.5973 / GFA 205.414;
- one normalized-z legal-corridor Matrix4 shear reaches at best neighborhood
  0.5450 and cultural 0.6586, still below the unchanged 0.68 measured
  silhouette boundary.

Therefore a centroid translation or one shear patch is not sufficient. The
next RED must generate a bounded set of whole-legal-section-field affine
alternatives (orientation/flip, anisotropic scale, normalized-z shear) for the
existing canonical BAR/SLAB/shear authored programs. Alternatives are accepted
only after the actual final CSG passes connectedness, capacity, exact
containment and program/geometry/surface identity; the unchanged morphology
classifier must then witness at least one non-pyramidal final solid. Do not
change the PNU fixture, template, capacity target, law gate or classifier.

### r9 spatial/capacity audit separation implemented; review pending

Implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-spatial-capacity-audit-separation-implementation.md`.
SHA-256:
`A9AD71B1F5CD7E2D6807D3E35DE111D4A6FB2AA55DA5C0083E3FE1B7CB43AAB0`.

`spatial_evaluation` now uses a geometry-only semantic-carrier audit over the
exact final program/geometry/surface, reachable scaffold, carrier hash,
floor-band containment/disjointness and required relations. The existing
`audit_source_semantic_projection` remains the full downstream audit and still
requires the floor plan, PNU/site context, requested alternative, achieved
capacity band and capacity-measurement hash.

Evidence:

- new TDD 2/2 GREEN;
- MASS product 31/31 GREEN;
- focused downstream/capacity 6/6 GREEN;
- root independently reran the two new tests plus final-hash and measured
  capacity regressions: 4/4 GREEN in 0.053 s;
- frozen r9 ran once in 41.765 s: neighborhood program pass improved from
  page0/page1 `0/1` to `21/20`, and released candidate supply from 1 to 24;
  capacity-eligible remains exactly 1 because 0.70 is unchanged;
- cultural program pass is 21/21, while its four eligible identities remain
  pyramidal.

No shape, placement, PNU, threshold, law, parking or downstream capacity gate
changed. Independent review is active. No live r9 is authorized.

Independent review is **REJECT**. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-spatial-capacity-audit-separation-review.md`.
SHA-256:
`5788592C3D78497E406B2FF02A21C0D232A394F79B178CE438CC2999C21C0588`.

The downstream full audit remains fail-closed, but the spatial-only entrypoint
is too broad: it excludes floor-plan, PNU, site and capacity-alternative
comparisons in addition to the intended achieved-band/measurement result, and
it skips semantic-envelope-hash verification. Independent probes made
semantic-hash, plan, PNU, site and alternative tampering all pass spatial
audit. The legal-field placement implementation was interrupted before
stacking work on this defect.

Required correction: spatial audit still compares plan/PNU/site/requested
alternative and always recomputes the full evidence envelope for
self-consistency. Only the honest post-measurement result fields
`achieved_capacity_band` and `capacity_measurement_hash` may differ from the
pre-measurement spatial context. Re-review before resuming placement.

Correction implemented; re-review active. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-spatial-capacity-audit-separation-correction.md`.
SHA-256:
`D29A7832B5EBB49DE09105CC11BA297214A21EE5C879BA3C217E287E46770B67`.

RED was 3 tests / 5 expected failures for semantic hash plus plan/PNU/site/
requested-alternative replay. GREEN is 3/3, MASS product 32/32 and focused
downstream/capacity 9/9. Root independently ran the four positive/tamper/
context/result-boundary methods: 4/4 GREEN in 0.063 s. Frozen ran once:
N program pass 21/20, released 24, capacity eligible 1; C pass 21/21,
eligible 4, all pyramidal. No PNU.

Independent correction review is **APPROVE**. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-spatial-capacity-audit-separation-correction-review.md`.
SHA-256:
`4ACB7002DF5450333EFB380B3933FD6F072652B7CDAE5A86EB60A1241D256D20`.

The five prior bypass probes now spatial/program REJECT. Honest achieved-band
or measurement-context mismatch alone spatial/program PASS while the full
downstream audit REJECTs. Program/geometry/surface/scaffold/carrier/payload
tamper remains fail-closed. Reviewer focused 6/6 and full MASS-product 32/32
GREEN. Spatial/capacity separation is closed; legal-field placement may resume.

### r9 legal-field affine solver witness GREEN; integrated frozen RED

The bounded solver now screens 36 whole-legal-field Matrix4 alternatives and
exact-compiles at most four. It ranks using the same three vertical samples
per floor used by final SourceMass rather than midpoint only. Focused exact
PNU1 witnesses:

- neighborhood BAR: GFA 236.13, upper/lower 0.6834, non-pyramidal;
- cultural BAR: GFA 174.131, floor areas
  `[35.460562, 35.460562, 35.460562, 35.460562, 32.288814]`,
  upper/lower 0.8567, non-pyramidal;
- all are exact-contained, manifold, watertight, one UnitBox and one site
  Matrix4.

Integration TDD proves a successful solver projection is reused without
duplicate append/compile, failure is fail-closed with no legacy ground-fit
fallback, and same aggregate/different advisory vectors retain selected matrix
and final geometry identity.

The first integrated frozen run completed once in 14.9 s and remains RED:
neighborhood page0 evaluated36/compiled0; page1 36/2/2/program2; two unique
eligible stepped/pyramidal records. Direct canonical feasibility proves all
four unchanged bands are geometrically reachable (about 236/273/299/319 m2).
The actual scheduler binds capacity alternative to genotype/principle hash,
and the only two materializable lineages both received `balanced_yield`.

Next bounded TDD: separate capacity-alternative assignment from genotype hash
and deterministically cycle the four unchanged alternatives by page-local
evaluation ordinal, 9 each in the first 36. Do not change any target, label,
hash, solver axis, exact budget, gate or classifier. No live PNU.

Read-only BOOK control audit:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-book-identity-control-audit.md`.
SHA-256:
`33F69137E1599240CF727E9A6F769DA2E04BF63942FD5B7D06D98E621391E9C5`.

There is no identity/no-op principle in the 30 base operatives. Raw/no-BOOK
finished candidates violate the approved reachable-BOOK architecture, and
skew variation 4 at 0 degrees changes only program hash, not geometry.
Existing `1/1 + book:operative:skew` variation 5 is the minimal legitimate
control: 7.7 degrees, Matrix4 shear amount 0.060842, topology-preserving and a
real geometry delta. Direct exact PNU1 BAR probes:

- N GFA 236.129653, upper/lower 0.6835, non-pyramidal;
- C GFA 174.131127, upper/lower 0.8567, non-pyramidal;
- both have final geometry hashes distinct from raw while retaining exact
  capacity/containment/manifold/watertight authority.

Implementation TDD will reserve exactly two page0 preservation-control
genotypes (canonical BAR and SLAB) at existing 1/1 scope ordinals whose
independently cycled bands are feasible. It must preserve first3, 36 distinct
parents, all other diagonal order and non-diagnostic behavior. This is an
existing BOOK operator lane, not a raw template bypass.

Legal-field placement + control implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-legal-field-affine-placement-implementation.md`.
SHA-256:
`8F2E42DDBABE4DD27519766769FF8C4B4EC768768474DF94D700F1F358508CBB`.

Implemented focused contracts are GREEN:

- 36 cheap screens / exact budget 4, one Matrix4 and exact final CSG;
- success projection reuse, failure fail-closed, final hash identity;
- four diagnostic capacity alternatives exactly 9 each/page;
- page0 ordinal3 SLAB/max and ordinal12 BAR/spatial use real BOOK skew-v5;
- first3, other34, 36 distinct parents, scope/diagonal and non-diagnostic
  defaults preserved;
- focused 8/8, including exact N/C non-pyramidal controls.

But the final frozen run remains RED (9 tests: focused8 PASS/full1 FAIL,
13.993 s): N page0 36/compiled0, page1 36/compiled2, two unique
stepped+pyramidal records. Thus controls are valid through the direct exact
CSG test but disappear in the full program-role/materialization path. No
second run or further implementation occurred. A read-only agent is now
reconstructing the two exact controls stage-by-stage to find whether
`project_program_requirements`, role-scaffold binding, legal-field selection,
bridge identity or semantic evidence is the first loss boundary.

Read-only full-path loss audit:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-control-full-path-loss-audit.md`.
SHA-256:
`F163BC6CC0B7F768568490ABBF7964E68A4261BD7A2DE7C33A769D66B9D2C931`.

Both controls pass raw -> BOOK -> program requirements -> identity scaffold ->
authored compilation/component gate. The first failure is legal-field selector
`None`; SourceMass/semantic stages are never reached. The direct control test
omitted the required production program-projection stage:

- SLAB receives courtyard + join-related and loses 50.82% authored volume;
- BAR receives west threshold notch + join-related and loses 17.07%;
- scaffold changes program hash only; geometry hash/profile are identical.

The current solver uses one fixed 1.06 area factor. Next TDD includes the full
production projection/scaffold and replaces that factor with a bounded,
geometry-derived 2D aggregate-intersection scale solve for each existing
orientation/anisotropy/shear pose. It may not use per-floor advisory targets,
change the exact budget/gates, remove program controllers, or add parcel/
target constants. BAR spatial control is the required witness; impossible
SLAB/max may remain fail-closed.

Scale/rank correction is **REJECT** and fully reverted. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-legal-field-affine-placement-correction-reject.md`.
SHA-256:
`F11EDDA85ADF2E942F30FBC07BCD83E821113F46CD592BC39B7918682D5B572A`.

Production BAR had 16/36 cheap capacity-feasible poses. Their lower/mid/upper
clipped polygons were robust (minimum boundary edge 0.0051 m; top margin
0.0262 m versus 1e-5 gate), but all 16 exact candidates failed `tiny_edge`.
The compiled mesh minimum edge is exactly 0 due to duplicate-coordinate
triangles at floor boundaries such as z=0.5/0.75. Therefore the issue is CSG
triangulation degeneracy, not insufficient scale or a legal polygon sliver.
Dynamic scale and robust-screen experiments were removed; fixed 1.06 baseline
is restored. Canonical N/C witnesses PASS and the production-shaped RED is
retained as a missing-coverage regression. No frozen run.

An active read-only audit is locating whether generic compiler mesh cleanup or
the floorwise band-union construction owns exact duplicate-vertex/zero-area
triangle removal. Gate thresholds must not change.

### r9 combined scale solve + compiler canonical export focused GREEN

The implementation is now production-shaped GREEN, pending report/review:

- compiler export stably welds vertices only when their canonical 8-decimal
  coordinates are exactly equal and drops only repeated-index or exactly
  zero-area faces;
- a deliberately nonzero 1e-6 edge remains in the payload and the unchanged
  gate rejects it as `tiny_edge`;
- normal UnitBox payload and geometry hash are unchanged;
- the aggregate-only bounded scale solve is restored without the rejected
  robust-edge rank; it uses post-program source/legal bounds, not per-floor
  target vectors or target/parcel constants;
- existing orientation/anisotropy/shear axes and exact budget 4 remain.

Production BAR after BOOK skew-v5 + neighborhood program requirements +
identity scaffold:

- screened 16; exact compiled 4; exact feasible 1;
- target 232.6254; achieved 236.167180;
- floor areas `[62.101515, 62.198885, 62.296254, 49.570526]`;
- upper/ground 0.7283, non-pyramidal;
- final 46 vertices / 88 triangles, contained/manifold/watertight;
- one site Matrix4 and source/final program+geometry identity PASS.

No frozen run. Focused regression and independent review are required next.

Implementation report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-csg-export-canonicalization-implementation.md`.
SHA-256:
`3187A99316159062630283A0DEB6E53C32C742F45E5167A7BCDC8D212EE31C68`.

Independent review is **APPROVE**. Report:
`.superpowers/sdd/2026-07-28-single-authority-legal-mass/task-5-r9-csg-export-canonicalization-review.md`.
SHA-256:
`1E64084A3664AF0C0845BE1618508453C5D00F9F3C55E6D0BD29F663764CC946`.

Reviewer fresh 7/7 plus floorwise 8/8 GREEN. It reproduced the full BAR
236.16718 result, 46 unique vertices/88 triangles, surfaces/raw/exported
88/88/88 and all final program/geometry hashes. An independent nonzero
tiny-face probe remains in the payload and is rejected by the unchanged
`tiny_face` gate. Aggregate solver uses only aggregate+legal intersection;
axes 4x3x3 and exact max4 remain. Root independently reran boundary4/4 and
floorwise8/8 GREEN. Frozen may now run once.

Non-blocking review note: the private canonicalizer coerces a synthetic
non-integral triangle index via `int()`, but production `to_mesh64()` supplies
`np.int64`; no current production boundary is affected.

### r9 frozen PNU1 target3 acceptance GREEN

Root ran the exact frozen module once after independent APPROVE:

`python manage.py test design.test_maas_r9_frozen_acceptance --verbosity 2`

Result: **10/10 GREEN**, 88.224 s test time / 92.1 s process wall time.
The full method
`test_neighborhood_and_cultural_have_three_final_solid_choices` now passes:
each frozen PNU1 program has at least three unique eligible final-solid
identities and at least one measured non-pyramidal identity. The other nine
methods confirm real BOOK skew controls, first3/other34/36-parent breadth,
9x4 capacity supply, advisory-vector invariance, fail-closed selection,
projection/hash reuse, exact N/C witnesses and production BAR survival.

This authorizes the first actual PNU1 diagnostic target3 run. It does not yet
prove live Neo4j/law, parking, renderer/PNG, VLM, elevation or PNU2.

### r9 actual PNU1 target3 + Neo4j parking acceptance GREEN

Root ran two bounded actual-PNU probes. The first proved live VWorld law,
law-agent Neo4j evidence, final-solid identity and technical rendering, but
correctly exposed that parking enrichment was still
`local_structured_seed/not_requested`. It was not used as the final evidence
run.

The final probe explicitly set `MAAS_ENABLE_PARKING_NEO4J=1` and removed the
disable flag before running:

`python -m tools.verify_single_authority_mass_pnus --pnu
1168011800104170004 --output-root
docs/playwright/design-route-live-verify/r9-pnu1-target3-neo4j-20260729
--diagnostic-target 3 --inactivity-timeout-seconds 180`

Final run directory:
`docs/playwright/design-route-live-verify/r9-pnu1-target3-neo4j-20260729/20260728T230824304909Z-01-pnu-1168011800104170004`.

Evidence:

- status is intentionally `diagnostic_only`; bounded-probe evidence is hard
  pass. The outer state says `completed_with_failed_gate` only because a
  target3 diagnostic cannot satisfy the separate normal portfolio minimum10/
  scope6 gate;
- neighborhood, gymnasium and cultural each selected 3/3, total 9;
- 9/9 final geometry hashes are unique and selected-row/render/passport
  required channels agree;
- final count9, stepped count6, roof archetype count6, solid phenotype count5,
  and every program has `near_duplicate_pair_count=0`;
- live VWorld PNU area 264.126 m2, second-class general residential zone,
  BCR60/FAR250, adjacent setback0.5 m, landscaping15%, sunlight applies;
- law graph agent is `passed` for 9/9; Neo4j is available with six resolved
  seed articles and zero missing, and law-domain search:8011 returns three
  results per program;
- parking repository is `source=neo4j`, `graph_status=available` for all three
  programs. Neighborhood is 2 required/2 provided for all three; gym is 0/0;
  cultural is 0/0, 1/1, 1/1. All nine parking hard gates pass;
- no live/paid VLM was requested. PNG acceptance here is direct technical
  render inspection, not a VLM claim.

Direct root and independent-agent visual inspection found no missing faces,
exploded triangles, spikes, wire-only output or repetitive plain-box
regression. All three program sheets contain three materially distinguishable
solids. Neighborhood 1 and 3 are the weakest pair because both use oblique
stepped-wedge vocabulary, but they have different silhouettes and hashes.
The two empty cards in each five-card sheet are unused template slots, not
failed members of the requested target3.

Verified copies in `docs/mass`:

- `r9-pnu1-neo4j-target3-neighborhood.png`,
  SHA-256 `5D7665F4E053F43C042BD443F3B56FF38E9080C5C542A1DFE4DC2E10DFE652A9`;
- `r9-pnu1-neo4j-target3-gymnasium.png`,
  SHA-256 `DF73191C2CCF7A43E614347E09B4F95C2F31F5EC7F364C20D5CE7426157C1760`;
- `r9-pnu1-neo4j-target3-cultural.png`,
  SHA-256 `208007ACE169087765F48D00ECA0F5005CF7B0DFE08165D6020603190643EC71`;
- `r9-pnu1-neo4j-target3-all-programs.png`,
  SHA-256 `42F4BB90FA435CD32449BFCE12E1513E6A4E9F6A026EBB8265E45F18A7222EC5`.

Read-only preflight reports:

- live path audit SHA-256
  `AF44A9A54AF9DB5EB35826A436D7DB70CFEA8D87C8A1126F7003B21DFB0880C5`;
- law/Neo4j preflight SHA-256
  `47CA6EF1305B255D0868E8F7D385D294BB893E3A1CE92B7F174A61CB3F72F638`.

PNU1 target3 is accepted. PNU2 target3 is now the next authorized gate.
Target10, paid VLM and elevation remain not authorized/not run.

### r9 actual PNU2 target3 RED — gym dimensional infeasibility

The next authorized probe ran with the same Neo4j law/parking and no-paid-VLM
conditions for PNU `1168011800104670003`. Run directory:
`docs/playwright/design-route-live-verify/r9-pnu2-target3-neo4j-20260729/
20260728T231424666714Z-01-pnu-1168011800104670003`.

This run is **not accepted** and its PNGs were not copied into `docs/mass`.
Neighborhood selected3 and cultural selected3, but gymnasium selected0, so
the final count is6 and `bounded_probe_evidence_hard_pass=false` with
`program_diagnostic_target_not_met` and `downstream_hard_gate_status_failed`.
The six persisted masses do have unique/agreed hashes, law graph evidence
hard-pass, Neo4j parking and parking hard-pass. That does not compensate for
the missing gym target.

The first local diagnostic boundary is before compilation/downstream:
gym evaluated36, compiled0, clean0, program-passed0. Its actual legal
generation field is a 429.700 m2 but extremely long/narrow polygon with
oriented dimensions 6.215 x 85.423 m. The existing program rule estimates
clear span as 0.92 x short axis = 5.718 m. This is below the smallest declared
gym subtype, `compact_training_hall`, whose minimum clear span is 6.0 m.
Program dimensional context therefore returns
`legal_generation_site_cannot_fit_minimum_program_span` and no gym candidate
is authored. The PNG correctly shows `0/3`; this is not a render/template
loss.

Three independent read-only audits are active to decide whether this is a
genuine parcel/program infeasibility or a general placement/span-estimation
bug. No gate, subtype minimum or target has been lowered and no fix/rerun has
occurred.

Independent audits closed the decision: PNU2 gym is a genuine
program/site/legal-field infeasibility. The persisted legal floor plate MRR is
76.956915 x 3.203893 m (area185.849977 m2, 158 vertices), far below the 6 m
clear-span minimum. PNU1 and PNU2 used the same 72 authored gym program
hashes; PNU1 materialized39 while PNU2 materialized0. This rules out
BaseVolume/BOOK seed diversity as the cause. No geometry/gate change is
authorized to force a gym onto PNU2. The separate reporting/control-flow bug
is that an infeasible program still wastes 72 materialization attempts instead
of ending explicitly as `program_site_infeasible`.

Reports:

- feasibility audit SHA-256
  `ECC00192749FA3B89D908E424A3DED3E8A6AF21013C1F531066B0873E6DBA7B7`;
- full-path forensics SHA-256
  `CF45C95018DDD30BE97C45EC7FA8A9D739A5393D19A4D2AFA5B10359EFC26468`.

An alternate larger residential parcel `1150010300111250000` was tried only
for cross-PNU diversity evidence. It made neighborhood progress to
evaluated36/compiled14/program-passed11, but then made no state-file progress
for 180 seconds during final projection/selection and was automatically
terminated by the verifier. Its result is rejected and no PNG was copied.
Next bounded attempt uses the existing medium commercial validation parcel
`1165010800113170029`; this is evidence work, not a replacement for the honest
PNU2 infeasibility record.

The medium commercial PNU attempt also completed but is **not** a full
cross-program acceptance. It selected gym3, neighborhood0 and cultural0
(final count3, scope counts0/3/0). The three gym masses have unique/agreed
final hashes, law-agent Neo4j hard-pass and Neo4j parking2/2 hard-pass.
Direct PNG inspection found three distinguishable clean gym solids. This is
useful comparison evidence that gym/BOOK works on a sufficiently broad parcel
and that PNU2 gym0 is site-specific. However
`bounded_probe_evidence_hard_pass=false`, so no PNG from this partial run was
copied to `docs/mass`.

Cross-PNU stopping decision:

- do not keep sampling parcels until one happens to pass;
- PNU1 is the only full N/G/C target3 acceptance in this session;
- PNU2 is an honest program-site infeasibility and remains rejected;
- the large alternate timed out and the medium commercial alternate is
  gym-only;
- therefore “all PNU x all programs target3” is still open. The next design
  task is explicit program-site applicability/early termination and a
  program-compatible cross-PNU acceptance contract, not gate lowering or
  random PNU looping.

### r9 program-site infeasible early stop GREEN / independently APPROVED

The confirmed PNU2 control-flow bug is fixed without changing any MASS or
acceptance gate. When the actual legal generation field cannot support any
declared program subtype and dimensional status is `infeasible`, the program
now stops before capacity-contract construction and `_program_pool`.

Persisted result:

- `generation_status=program_site_infeasible`;
- selected0 and downstream `status=fail`;
- evaluated/compiled/clean/program-passed all0;
- raw infeasible dimensional evidence remains authoritative, including
  effective height/floors0 and the exact reason;
- the separate law-derived floor-capacity-plan evidence is retained rather
  than replacing the dimensional truth;
- diagnostic target3 and normal minimum10/scope6 failures remain;
- an empty technical board, summary JSON and run-state checkpoint are written;
- compatible dimensional contexts still call the unchanged generation path.

TDD first failed at the forbidden `_program_pool` call, then at accidental
replacement of raw height0 by the separate plan height9, and finally passed.
Implementation focused tests3/3. Root independently ran the two new tests,
the nearby gym dimensional test and diagnostic summary-policy test: 4/4 GREEN
in0.062s, plus `py_compile` GREEN.

Implementation report SHA-256:
`E1B206AE53C341C2B5AFD7AC3460ABBB4E68BB3C547A4464E74AE385C5ABEB28`.

Independent review is **APPROVE**, fresh4/4 GREEN. Review report:
`ARR/docs/superpowers/sdd/2026-07-28-single-authority-legal-mass/
task-5-r9-program-site-infeasible-review.md`, SHA-256
`1C564180D75BBCE94CFB63996A5FB1300E6FD87F71FB10377DCF35FC0E48B906`.

No live/frozen/full benchmark was rerun after this control-flow-only change.
PNU1's previously accepted nine exact solids and copied PNGs remain the
current visual evidence. Compatible cross-PNU all-program target3 acceptance
is still open and must not be claimed complete.
