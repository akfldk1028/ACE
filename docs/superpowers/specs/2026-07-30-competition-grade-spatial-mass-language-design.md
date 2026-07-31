# Competition-Grade Spatial MASS Language Design

Updated: 2026-07-30 KST

## 1. Goal

Produce a twenty-candidate architectural MASS portfolio in which every
candidate:

- is evaluated on one exact real parcel and one shared program;
- is derived from the single canonical `1/1 UnitBox` BaseVolume authority;
- may organize volume, thickened plates, slabs, walls, roofs, voids,
  intersections, supports, bridges, and continuous sections;
- contains provably occupiable architectural space rather than only an
  interesting exterior solid;
- is evaluated against exact BCR, FAR, GFA, height, floor, access, parking,
  and other PNU-derived constraints;
- remains visually and geometrically faithful to the authored idea through
  legal evaluation;
- is preserved on the final board even when rejected; and
- cannot receive visual acceptance without an image-backed VLM review of the
  exact final legal evidence image.

The target is competition-grade strategic breadth, not maximum FAR, maximum
site coverage, named-style imitation, hash uniqueness, or a board of unrelated
normalized sculptures.

## 2. Current evidence and root cause

The latest 5x4 board proves that twenty unique connected, watertight, manifold
programs can be persisted and viewed. It does not prove that the twenty
candidates occupy the same parcel, satisfy the law, contain useful space, or
have been visually reviewed. Its PNU is stored as metadata, while its geometry
is still normalized pre-legal geometry. The run intentionally omitted the
opt-in VLM pilot.

The geometry kernel already supports most of the required low-level language:

- `matrix4`, affine transforms, `slice`, and `clip`;
- `circularize` and arbitrary connected `matrix_array`;
- `profile_sweep_3d`, `loft`, wedge, and profiled sections;
- `union`, `difference`, and `intersection`;
- `attach`, `bridge`, lift supports, and access-bound service spines.

The main immediate defect is contract wiring. `circularize`,
`matrix_array`, `profile_sweep_3d`, and important attach/bridge parameters are
not consistently exposed in the LLM author prompt, executable parameter
contract, VLM operator-effect vocabulary, and body-complexity classification.
Named deterministic fixtures currently exercise capabilities that direct
authorship cannot reliably request.

The deeper defect is that the current AST is closed-solid-only. A thin
UnitBox can act as a planar plate, but a true controlled surface followed by a
constant-thickness shell is not representable. Existing profiled and swept
solids can approximate a continuous floor-wall-roof section, but they cannot
serve as a general surface grammar.

## 3. Considered approaches

### A. Wire only the existing solid kernel

Expose the missing existing operators and author direct ASTs from them.

This is the fastest and lowest-risk route. It can generate arbitrary tilted
plates, connected interlocking discs, bridges, profiled volumes, and many
sectional organizations. It cannot fully represent a general
constant-thickness continuous shell or distinguish an envelope from its
occupiable spatial carrier.

### B. Replace the solid AST with a full boundary-representation grammar

Introduce curves, surfaces, shells, solids, topology editing, offsets, and
their complete type system in one change.

This is theoretically general but too broad for the current competition
checkpoint. It would disturb the certified solid compiler, legality gates,
hash authority, and tested UnitBox invariant at the same time.

### C. Staged typed extension over the current kernel

First expose every existing generic capability consistently. Then add a small
typed surface-to-solid extension while preserving the current solid compiler
and hashes.

This is the selected approach. It provides immediate interlocking
plate/disc capability, adds the missing continuous-section abstraction, and
keeps the existing legal and geometry evidence path intact.

## 4. Canonical geometry language

### 4.1 One authority

There is one geometric source authority: `1/1 UnitBox`. Other boxes, plates,
slabs, walls, roofs, supports, and discs are derived states.

The production author must not introduce a second independent cylinder,
completed loft, building template, or named-form primitive. Existing primitive
support may remain for compatibility and regression fixtures, but production
normalization must record exactly one canonical UnitBox authority.

### 4.2 Existing solid operators to expose

The author schema, parameter contracts, compiler trace, VLM vocabulary, and
cost/body classification must agree on:

- `matrix4` with arbitrary positive scale, rotation, shear, pivot, and
  translation;
- `circularize` of the live solid bounds;
- `matrix_array` with explicit 4x4 transforms and connectedness enforcement;
- `profile_sweep_3d`;
- `slice`, `clip`, `bend`, `taper`, and profiled section;
- `union`, `difference`, and `intersection`;
- `attach` using host face, anchor, guest extent, engagement, and rotation;
- `bridge` using its actual width and embed parameters; and
- support/service-spine relations required by lifted or spanning bodies.

An interlocking-disc candidate is therefore an unnamed composition such as:

```text
UnitBox
  -> thin positive-thickness matrix4
  -> circularize
  -> connected arbitrary matrix_array
  -> intersection/union/support relation
```

The path is generic. No Qatar, SANAA, OMA, museum, library, or other named
operator is allowed.

### 4.3 Minimal surface-to-solid extension

Add typed intermediate geometry values without replacing solid nodes:

- `section_surface`: derives a bounded ruled or piecewise-planar surface from
  normalized section controls over the live BaseVolume frame;
- `loft_surface`: derives a bounded surface from two to twelve normalized
  ordered section curves;
- `host_face_surface`: references a face or bounded sub-face of an existing
  solid in normalized host coordinates;
- `shell_thicken`: converts one bounded surface to a closed positive-volume
  solid with a positive thickness, centered/inward/outward side rule, explicit
  edge closure, and self-intersection rejection.

The compiler value type becomes `solid | surface`. Boolean, pattern,
composition, law, floor, render, and final-root operations accept only solids.
Surface nodes cannot be final roots. `shell_thicken` is the single boundary
where a surface becomes a certified solid.

Zero-thickness architectural geometry is never accepted as MASS. Thickness is
positive, dimensionless relative to the live host during authorship, converted
to site-scale meters during exact parcel placement, and recorded in the
program trace.

### 4.4 Architectural role semantics

Geometry nodes may declare one non-authoritative semantic role:

- `envelope`
- `occupied_slab`
- `wall`
- `roof`
- `support`
- `circulation_core`
- `public_threshold`
- `void_boundary`

Roles guide evidence extraction and VLM explanation; they never excuse invalid
geometry or replace measured evidence. The exact final mesh remains the
authority.

## 5. Same-parcel execution

### 5.1 Shared site packet

Resolve the PNU once per run into an immutable packet containing:

- parcel polygon and area;
- road and primary-access edge/orientation;
- buildable footprint and height-dependent legal fields;
- BCR and FAR limits;
- height, setback, sunlight, landscaping, and parking evidence;
- program and required minimum usable GFA; and
- `site_context_hash`.

Every candidate in a board must reference the same `site_context_hash`.
Merely storing the same PNU string is insufficient.

### 5.2 Placement and identity

The authored program uses normalized local coordinates. A recorded affine
placement maps it to the shared buildable-field frame and access orientation.
The placement must be identical in meaning for all candidates and may vary
only where the authored program declares a normalized site relation.

The legal stage checks the exact placed solid. It may not silently replace a
non-stepped design with floorwise stepped prisms. A geometry-changing repair
creates a new program/geometry hash and repeats every downstream gate.
Otherwise the candidate is rejected with its image preserved.

### 5.3 Wide-site readiness

The current regression PNU `1168011800104170004` has parcel area
`264.126 m2` and a generation host near `102.931 m2`; it is not a wide-site
competition test.

The pipeline must therefore be site-parameterized and include:

- the current PNU as an exact-law regression;
- a deterministic wide-site geometry fixture for free language and spatial
  tests; and
- a user-selected real wider PNU before any wide-site candidate is called
  lawful or before the paid VLM smoke test.

The implementation must not invent legal approval for the geometry fixture.
The real wider PNU remains an explicit run input rather than a hard-coded
site.

## 6. Spatial and statutory gates

Gates run in this order and fail closed:

1. AST type and parameter validation.
2. Surface closure/thickening validation where used.
3. Connected, watertight, manifold, positive-volume solid validation.
4. Exact shared-site placement and access relation.
5. PNU buildable-field, setback, sunlight, and height checks.
6. Occupied-floor extraction from the exact placed final mesh.
7. Usable-space checks.
8. Program capacity, BCR, FAR, GFA, landscaping, and parking checks.
9. Authored-identity preservation check.
10. Local portfolio diversity selection.
11. Bounded VLM review.

### 6.1 Usable-space evidence

Each candidate must persist:

- occupied floor polygons and areas by elevation;
- clear floor-to-floor and clear internal height;
- useful floor-plate depth and minimum connected usable region;
- vertical-circulation core feasibility across occupied levels;
- entrance/public-threshold connection from the access edge;
- support/contact evidence for elevated plates;
- exact actual GFA; and
- program allocation feasibility.

A decorative plate, token connector, inaccessible floating solid, or large
exterior volume with insufficient occupied space fails before VLM.

### 6.2 BCR and FAR

For every exact final candidate:

```text
actual_BCR = exact_ground_coverage_area / parcel_area
actual_FAR = exact_certified_GFA / parcel_area
```

Both values are recomputed from the placed final geometry and compared with
the PNU legal limits. Authored estimates and target ratios are not authority.

The system must not optimize all candidates toward the legal FAR maximum.
Program-minimum GFA and statutory maximum FAR are hard gates. Within that
legal interval, FAR utilization, site coverage, open-space reserve, and
sectional generosity are portfolio diversity dimensions. A lower-FAR
candidate may outrank a fuller candidate when its spatial organization,
public realm, circulation, or competition strategy is stronger.

No fixed equal quota is required for reserve, balanced, and higher-yield
solutions. The final selector instead maximizes measured distance across FAR
utilization and architectural descriptors while preserving quality gates.

## 7. Candidate authoring and selection

Paid text LLM authoring is optional. The active AI may provide direct typed
AST payloads. Production authoring receives:

- the shared site packet in normalized semantic form;
- the program and spatial requirements;
- the complete operator and parameter contract;
- known rejected-body evidence; and
- a request for materially different tree, topology, void, section, plate,
  support, and circulation organizations.

It does not receive named style recipes or required form-family labels.

The free candidate pool is larger than twenty. Candidates are deduplicated by
program hash, geometry hash, normalized geometry, and spatial organization.
Selection uses max-min distance over measured descriptors including:

- plan compactness and elongation;
- height and section profile;
- obliquity and curvature;
- plate/shell slenderness;
- void and court organization;
- floor continuity and circulation topology;
- ground openness and public threshold;
- support, span, and intersection relations;
- BCR and FAR utilization; and
- program distribution.

Post-hoc labels are reporting aids only. They do not generate candidates or
create quotas. A board dominated by generic boxes or steps fails the
portfolio-level repetition gate even if all hashes differ.

## 8. Board and retained evidence

The comparison artifact is one 5x4 PNG. Every card uses:

- the same site outline, north/access orientation, camera, and scale;
- an exact site-plan view plus a comparable axonometric view;
- candidate ID and immutable identity hashes;
- actual floors, GFA, BCR, FAR, and legal limits;
- geometry, space, law, parking, identity, and VLM status; and
- a concise rejection reason when applicable.

All attempted candidates receive individual evidence images. Failed
candidates do not disappear. The board clearly separates:

- `PRE-LEGAL`
- `LEGAL REJECT`
- `SPATIAL REJECT`
- `READY FOR VLM`
- `VLM REJECT`
- `ACCEPTED`

## 9. Minimal paid VLM test

The first live test spends exactly one candidate-review request:

1. Select one locally verified `READY FOR VLM` survivor.
2. Build one exact evidence sheet from the final legal geometry containing
   site plan, comparable axonometric views, occupied-floor evidence, and one
   explanatory section.
3. Attach actual local ArchDaily reference images, limited to the smallest
   relevant set.
4. Submit the exact candidate and reference images in one VLM request.
5. Persist response ID, model, token usage, request count, candidate image
   SHA-256, reference image SHA-256 values, program hash, geometry hash, PNU,
   and site-context hash.
6. Require structured judgements for spatial inhabitation, slab/wall/roof and
   void relations, circulation, entry/threshold, program fit, generic
   box/step repetition, authored continuity, and use of references.

Automatic retry count is zero. A transport, schema, image-binding, or identity
failure stops the paid stage. No second paid request occurs without a new
explicit decision after inspecting the first result.

VLM approval is necessary but not sufficient. It cannot override a failed
law, space, geometry, capacity, parking, or identity gate.

## 10. Failure behavior

- Unknown/missing operator parameters: reject before compilation.
- Invalid surface or self-intersecting thickness: reject and persist preview
  if safely renderable.
- Disconnected/non-manifold/non-watertight result: reject.
- Missing real-PNU evidence: `needs_evidence`, never accepted.
- FAR/BCR/GFA mismatch: reject using measured values.
- Legal repair changes identity: issue new hashes and repeat all gates.
- Too few valid candidates: publish the partial board with deficits rather
  than fabricating acceptance.
- VLM unavailable or paid test not authorized: preserve `READY FOR VLM`;
  never infer visual approval.

## 11. Test strategy

Implementation follows red-green-refactor.

Required tests include:

- existing operator exposure agrees across author schema, parameter contract,
  compiler, VLM vocabulary, and complexity classification;
- a direct non-recipe `UnitBox -> circularize -> matrix_array` program creates
  one connected watertight manifold interlocking-disc solid;
- disconnected disc placement rejects;
- arbitrary thin UnitBox plates remain positive-volume solids;
- `section_surface -> shell_thicken` creates a valid closed solid;
- zero/negative thickness, open edges, and self-intersection reject;
- surface nodes cannot be roots or enter solid-only Boolean operations;
- exact site packet hash is shared across every candidate;
- current-PNU regression keeps exact legal authority;
- wide-site fixture proves scale independence without claiming law;
- occupied-space, circulation, clear-height/depth, and program-capacity gates
  reject sculptural false positives;
- actual BCR/FAR are recomputed from final placed geometry;
- lower legal FAR candidates are not discarded merely for unused capacity;
- legal projection cannot collapse authored identity silently;
- board preserves every reject and uses the same site/camera/scale;
- paid VLM smoke test makes one request, uses actual candidate/reference
  images, binds all hashes, and performs zero automatic retries; and
- provider calls remain zero in all non-live tests.

## 12. Acceptance criteria

The feature is complete only when:

- all twenty displayed candidates share one exact real `site_context_hash`;
- every candidate derives from one canonical UnitBox authority;
- the portfolio contains materially different measured spatial strategies
  without named recipes or quotas;
- plate/disc intersection and continuous thickened-section capabilities are
  directly authored through generic operators;
- no displayed survivor is merely a non-inhabitable sculpture;
- exact law, BCR, FAR, GFA, floor, access, parking, and identity status is
  visible per card;
- rejected candidates remain visible;
- the final board is visually reviewed directly; and
- one explicitly authorized VLM smoke request successfully reviews the exact
  final legal evidence image with actual reference images and complete hash
  evidence.

Until these criteria hold, the portfolio is diagnostic evidence, not
competition-grade acceptance.
