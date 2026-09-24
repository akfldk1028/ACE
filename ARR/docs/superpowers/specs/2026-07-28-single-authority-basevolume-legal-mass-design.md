# Single-Authority BaseVolume and Legal MASS Design

**Date:** 2026-07-28  
**Status:** Approved architecture; selector counts below require final review  
**Supersedes:** The three-authority model in
`2026-07-28-floorwise-legal-visual-mass-design.md`

## Goal

Generate diverse, capacity-credible MASS alternatives from one canonical
`1/1 UnitBox`, preserve the actual BOOK/LLM-authored solid through legal
adaptation, and make every downstream claim from one final compiled geometry.

The selected MASS used for render, VLM, GFA/FAR, parking, archive replay and
elevation must be the same hash-bound solid.

## Source-faithful generation order

The BOOK p.3 scan defines six relative BaseVolume states:

`1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`.

They are volume fractions and topological occupancy states, not six public
primitives and not plan aspect ratios.

```text
canonical 1/1 UnitBox
  -> BOOK BaseVolume state
  -> orientation
  -> host morphology / base seed
  -> chassis
  -> BOOK single operation
  -> BOOK sequential combination / aggregation / case-study composition
  -> LLM-authored typed GeometryProgram/AST
  -> compiler
  -> floorwise legal CSG projection
  -> exact law/FAR/parking gates
  -> render and typed VLM review
  -> portfolio selection
  -> elevation
```

Examples:

- `1/1 + slab` reads as a wide full plate or podium datum.
- `1/2 + slab` reads as a half plate.
- `1/4 + bar` reads as a local linear wing.
- A wide plate, bar or tower is a host-morphology/base-seed state, not a
  seventh BaseVolume.

## Geometry authority

There is exactly one initial primitive authority: a normalized `1/1 UnitBox`.

Every derived cell instance and every affine placement is represented by a
homogeneous 4x4 matrix:

- scale;
- translate;
- rotate;
- mirror;
- shear;
- principal-frame site placement.

An affine matrix cannot change topology. Therefore topology-changing states
and operations remain explicit typed nodes:

- the BOOK `3/8` L-state is three Matrix4-derived UnitBox cells joined by CSG
  union;
- carve, void, split, notch and legal clipping use typed CSG;
- bend, taper, twist, sweep and loft use typed compiler macros;
- each macro may contain Matrix4 placements but cannot be replaced by one
  misleading matrix.

The canonical implementation statement is:

`one 1/1 UnitBox authority + Matrix4 transform graph + typed CSG/macro graph`.

## Final legal projection

The old generic plan-refit retry and the hidden floor-area sibling are
excluded.

The existing continuously interpolated floorwise visual projector is also
excluded from final authority because it can produce pinched, sloped and
hourglass faces between floor centers.

For each candidate:

1. Compile the authored BaseVolume/BOOK/LLM root solid.
2. Intersect that exact root with one horizontal CSG band per floor.
3. Apply one constant principal-frame Matrix4 to each isolated band.
4. Intersect the transformed band with the matching extruded legal polygon.
5. Union all legal bands into one final GeometryProgram root.
6. Compile and hash the final root.

There is no Matrix4 interpolation between floors. A stepped result is therefore
real final geometry, not a capacity-only proxy.

## One downstream product

All consumers use the same final compiled solid:

- floor sections and GFA/FAR;
- building coverage and legal containment;
- parking demand and parking layout;
- board render and silhouette distance;
- VLM review and typed repair;
- selected archive and exact replay;
- elevation and multi-view geometry.

The authored pre-projection program hash remains provenance, but it cannot
serve as a second geometric authority.

The final product binds:

- authored program hash;
- authored geometry hash;
- legal projection program hash;
- final geometry hash;
- floor-capacity-plan hash;
- law-graph evidence hash;
- parking evidence hash;
- render/VLM/elevation geometry hash.

## Capacity alternatives

The four alternatives remain a separate axis from BaseVolume:

- `spatial_reserve`;
- `balanced_yield`;
- `brief_target`;
- `maximum_feasible`.

Their numerical targets are derived from each live PNU/program capacity
contract. They are not fixed FAR percentages and are not additional building
types.

After final CSG projection, the system measures achieved utilization from the
exact final solid. A candidate may carry a capacity label only when it reaches
that label's measured target. Requested-but-missed labels are diagnostic only
and cannot satisfy selector coverage.

## Proposed ten-MASS portfolio contract

The selector returns exactly ten only when all conditions pass:

- all six BOOK BaseVolume lineages appear at least once;
- all four measured capacity alternatives appear;
- capacity-band counts differ by at most one, giving a 2/2/3/3 distribution
  in some order;
- stepped MASS count is at least one and at most three;
- at least one stepped MASS reaches `brief_target` or `maximum_feasible`;
- no roof archetype or solid phenotype appears more than three times;
- pairwise final-solid silhouette distance is at least `0.10`;
- all ten pass final geometry, legal, parking and exact-source gates.

Scope and capacity are orthogonal. One card simultaneously satisfies one
BaseVolume lineage and one measured capacity band.

The solver must treat cardinality, six-scope coverage, four-band balance and
the stepped range as one joint feasibility problem. It may not first maximize
ten cards and then silently fall back to an uncovered set.

If the contract is infeasible, the board fails with serialized unsatisfied
constraints. It is never padded and no threshold is relaxed.

## PNU verification ladder

Use short, isolated output directories and never overwrite prior artifacts.

Strict cached PNU checks:

1. `1168011800104170004`
2. `1168011800104670003`

Conditional diagnostic:

3. `1168011800104230007`

The third PNU must not be called fully verified until its land-analysis
provenance is strengthened.

For each PNU:

1. compile a three-candidate diagnostic probe before a portfolio run;
2. inspect current authored, floor-band projected and final legally clipped
   geometry;
3. verify final GFA/FAR, law containment and parking from the same hash;
4. render PNG and inspect BaseVolume/BOOK feature retention;
5. only then run the bounded ten-card selector.

## Regression requirements

Tests must fail before production changes and prove:

1. one canonical UnitBox remains the only primitive root;
2. all six BOOK states derive from that root through Matrix4 plus typed CSG;
3. per-floor matrices are constant within bands and never interpolated;
4. final GFA/FAR and parking are measured from the rendered final solid;
5. a requested-but-missed capacity band cannot satisfy coverage;
6. all six scopes and balanced four-band coverage are jointly hard;
7. stepped is between one and three, including one upper-band candidate;
8. a valid `1/16` candidate cannot be discarded by cardinality-first fallback;
9. board, archive, VLM and elevation expose the same final geometry hash;
10. cross-PNU probes preserve visibly different BOOK-derived forms.

## Non-goals

- This stage does not create detailed floor plans.
- Floor sections exist only to measure and certify the MASS product.
- Parking solver evidence is a mass-stage precheck, not permit approval.
- Live VLM cannot repair missing deterministic supply or legal infeasibility.
