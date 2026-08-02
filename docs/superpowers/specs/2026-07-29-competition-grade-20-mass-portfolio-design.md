# Competition-Grade 20-MASS Portfolio Design

## Objective

For one PNU and one program, produce exactly 20 legally certified MASS
alternatives that can be reviewed together as a competition-grade design
board. The default product output is 20; a three-card run is diagnostic only
and must never be reported as portfolio completion.

## Invariants

- Geometry starts from exactly one canonical `UnitBox(1, 1, 1)`.
- `1/1`, `1/2`, `3/8`, `1/4`, `1/8`, and `1/16` are BaseVolume scopes
  derived from that UnitBox, not six finished templates.
- Axis, placement, translation, rotation, scale, shear, and affine fitting
  use Matrix4 nodes.
- Courtyard, subtraction, union, branching, bending, profiled sections, and
  other non-affine architectural verbs remain typed CSG or typed macros.
- Neo4j law evidence, the shared legal-floor-field hash, each candidate's
  actual-GFA-stop hash, parking evidence, program hash, geometry hash, and
  visual hash remain hard authorities.
- Ordinary occupiable floor count is an unresolved lawful `N`, not a catalog
  3/4/5-storey choice. PNU height and per-floor legal sections bound the
  search; certified actual floor-plate GFA determines when it stops.
- Accumulate actual GFA floor by floor and stop at the minimum `N` that can
  carry the selected FAR/GFA target. Distribute the target through authored
  parameters or a form-preserving affine fit, then certify the final mesh's
  actual floor plates. Exhausting the lawful field first is
  `target_unreachable`.
- Do not generically trim the terminal floor after authorship: that would turn
  unrelated forms into stepped masses. A terminal residual plate is allowed
  only when an intentional stepped/terraced typed language authored it;
  otherwise an uncorrectable overshoot rejects the candidate.
- Historical floor hints and `target_floor_range` are design preferences, not
  law/capacity maxima. Only explicit dimensional program invariants may impose
  a hard storey range.
- The shared legal-floor-field hash identifies the complete PNU legal floor
  field, not one mandatory building storey count. Alternatives may stop at
  different lawful `N` values while each carrying its own certified
  actual-GFA-stop hash.
- A unique hash proves identity only. It never proves visual diversity.
- VLM may review a completed board but may not author legal geometry or relax
  any numeric gate.

## Confirmed Failure

The r9 diagnostic did not exercise the combinatorial system:

- 164 seed/carrier combinations were reduced to 36 evaluations.
- Only three of six BaseVolume scopes were evaluated.
- Each genotype received one BOOK probe.
- Final hard-pass supply was only 5 neighborhood, 15 gymnasium, and 18
  cultural candidates.
- The affine selector exact-compiled only four poses and required at least
  99.5% of the assigned aggregate capacity target.
- The final visual solid was made by intersecting each authored floor band
  with shrinking legal sections and unioning the bands. This rewrote
  non-stepped cultural forms as stepped solids.
- Target-three selection allowed three copies of one phenotype and one roof
  family.
- The target-20 capacity balance gate allowed only two to three cards in each
  of four bands, so a 20-card result could never pass.

## Architecture

### 1. Breadth scheduler

Enumerate the deterministic universal form bank across all six BaseVolume
scopes with balanced round-robin coverage of genotype, axis, BOOK principle,
body language, roof/section language, and capacity band. Do not exact-compile
the Cartesian product.

Run a cheap phase first:

1. typed AST compile and geometry gate;
2. 2D per-floor legal-section screen;
3. approximate capacity and containment;
4. quota-deficit scoring.

An AST-valid candidate whose conservative bounds are `unknown_bounds` is not
a cheap pass and may not claim legal/capacity evidence. It may enter a
quota-protected `exact_required` lane when it supplies a missing scope, BOOK,
body, roof, chassis, plan, curved, or winged cell. Known cheap failures and
invalid ASTs never enter this lane.

Keep one combined quota-aware exact shortlist of 48 to 64 candidates,
including proven-cheap and `exact_required` records. `exact_required` survives
only if the existing exact compile, legal containment, capacity, parking, and
hash gates pass; the lane does not relax a gate. Continue through deterministic
form-bank pages until the final hard-pass pool contains 24 to 28 candidates
satisfying every required diversity cell, or a bounded budget returns a typed
deficit certificate.

### 2. Legal projection modes

`authored_affine_preserved` is the default mode. Apply one site Matrix4 to the
authored solid, slice the compiled solid at every floor for capacity evidence,
and accept it unchanged only when every section is contained in its legal
section, the certified capacity target is met, and the compiled mesh remains
watertight and manifold.

`authored_adaptive` is allowed only when the deformation is already present as
typed authored AST controls. Legal evidence may choose bounded parameters but
may not introduce a new architectural verb. The resulting single compiled
solid must pass the same floor-section containment and capacity certificate.

`intentional_floorwise_stepped` retains the existing floor-band legal CSG for
alternatives whose visible architectural language is intentionally stepped.
It is limited by the final stepped quota and may not be used as a generic
repair fallback.

Floor-capacity evidence measures the accepted final solid. It does not create a
second larger building hidden behind a smaller visual mesh.

The pre-authoring capacity plan may estimate the required stack, but it may
not certify the estimate as the finished building. The authoritative stop
certificate is recomputed from the accepted final solid's actual floor plates
and must bind the trusted shared legal-floor-field hash, candidate target,
program, final-geometry, and visual identities.

### 3. Visible morphology evidence

Measure the certified final mesh, not labels:

- top, front, and side silhouettes;
- isometric edge map;
- normalized floor-area-by-height curve;
- authored step transitions;
- legal floor seam transitions;
- roof breaklines;
- plan convexity and voids;
- component and chassis relations.

Record `visible_stepped`, `authored_stepped`, and `legal_seam_stepped`
separately. A floorwise repair that looks stepped remains visibly stepped even
when the original BOOK program did not author a setback.

### 4. One portfolio solver

Targets 3, 10, and 20 use the same fail-closed MILP/set solver. There is no
post-solver fallback that relaxes a morphology cap.

The publishable target-20 contract is:

- exactly 20 legal, parking, program, and hash hard-pass cards;
- four capacity bands with exactly five cards each;
- all six BaseVolume scopes, each represented three or four times;
- at least five measured body phenotypes, no phenotype above four;
- visible stepped count between one and three;
- at least seven roof/section archetypes, no archetype above three;
- at least six chassis families, no chassis above four;
- at least five plan families, no plan family above four;
- at least three voided/courtyard cards;
- at least three winged/curved cards in total;
- wedge-like count at most two and pyramidal-like count at most two;
- at least ten distinct BOOK principle identifiers;
- certified-mesh silhouette distance at least 0.14 for every pair;
- when a pair shares body phenotype or roof archetype, composite
  silhouette/edge/height-profile distance at least 0.22.

The target-three regression contract is:

- exactly three cards;
- visible stepped count at most one;
- three distinct body phenotypes;
- three distinct body-plus-roof signatures;
- certified-mesh pair distance at least 0.16.

If the contract is infeasible, return per-cell supply deficits and request the
next breadth page. Never backfill with a repeated stepped form.

### 5. Runtime and review

The first acceptance run is one PNU and one program. It must create one
20-card PNG before any per-card paid VLM work. Exact geometry work is bounded
and parallel; silhouette views are built once per shortlisted candidate and
cached for pair comparison. A single optional board-level VLM review runs only
after the numeric and legal portfolio passes.

Record phase durations for breadth enumeration, cheap screen, exact compile,
law, parking, solver, and render. The implementation target is a first board in
at most 120 seconds on the current workstation; if it misses, the run must
still checkpoint its exact phase and deficit rather than hang without status.

## Acceptance Evidence

- Focused unit and integration tests pass.
- The selected 20 records have unique `(program_hash, geometry_hash,
  visual_hash)` identities, one trusted shared legal-floor-field hash, and
  twenty valid candidate actual-GFA-stop hashes.
- Neo4j law evidence and parking hard-pass are present for all 20.
- The generated PNG visibly contains 20 cards and satisfies the numeric
  distribution contract.
- The PNG is copied to `docs/mass`.
- The frontend loads the same run and card count without console errors.
- Session memory states whether the result is a technical pass, visual pass,
  or still needs review; a target-three diagnostic is never called complete.
