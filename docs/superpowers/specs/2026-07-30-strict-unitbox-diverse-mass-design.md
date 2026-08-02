# Strict UnitBox Diverse MASS Design

## Objective

Produce a maintainable 100-candidate architectural MASS choice pool whose
diversity comes from typed architectural recipes rather than index-dependent
scale noise. Preserve one canonical `1/1 UnitBox` authority, keep stepped mass
as only one alternative, expose full Matrix4/mesh lineage, and prevent visual
memory from contaminating the law graph.

## Current diagnosis

- The existing compiler already supports arbitrary plane clips, polygon
  extrusion, wedges, lofts, cylinders, affine Matrix4 transforms, booleans,
  arrays, bridges, and BOOK macros.
- The current 100-card generator samples only ten hard-coded source families.
  It therefore emits ten recognizable families repeatedly and never routes the
  existing triangular profile or a tilted-disc recipe into the pool.
- Program and geometry hashes prove byte/mesh difference, not architectural
  difference. Index-dependent scale perturbations must not count as diversity.
- `candidate_generation.py` is already too large. New creative family behavior
  must not be added to `_program_pool()`.
- The ArchDaily corpus already contains 13 collections, 313 unique items, and
  375 local images. Retrieval and pairwise preference storage exist, but design
  outcome mirroring can still use the same default Neo4j database as law data.

## Authority model

The sole geometric seed authority is:

```text
canonical 1/1 UnitBox
```

All building proportions, site axes, and placement are represented by Matrix4.
Topology-changing actions are typed architectural operators that consume a
UnitBox-derived solid:

```text
UnitBox
  -> scope/proportion Matrix4
  -> architectural modifier or composition
  -> BOOK relation
  -> connected authored MASS
  -> occupied floor evidence
  -> legal projection/certification
```

`circularize`, `clip`, `loft`, boolean CSG, and bridge operations are therefore
architectural language, not additional base-volume authorities. Direct
`cylinder` and `extruded_polygon` primitives remain valid compiler facilities
for compatibility, but the creative 100 path must use UnitBox-derived recipes.

## Module boundaries

### Family contract and registry

`creative_family_contract.py` owns immutable recipe interfaces and evidence
types. `creative_family_registry.py` owns family registration, quotas, and
deterministic ordering. Neither module compiles, renders, accesses law, or
writes files.

### Family recipes

`creative_family_recipes.py` owns typed GeometryProgram construction. A recipe
receives a canonical UnitBox program, a variation index, BOOK scope, and
capacity band. It returns an authored GeometryProgram plus declared contact and
form-class evidence.

The registry contains fifteen families:

1. bent
2. carved_void
3. courtyard
4. cross
5. grid
6. inflated
7. notch
8. radial
9. split_wing
10. stepped
11. triangular_shard
12. oblique_crystal
13. thin_disc_cluster
14. interlocking_tilted_discs
15. long_span_bridge

The final five are not references to a specific building. They encode
transferable principles such as faceting, oblique cuts, interlocking inclined
plates, and occupied spanning connections.

### Minimal geometry-language additions

- `circularize`: consumes a UnitBox-derived solid and creates a bounded
  cylindrical/elliptical solid using its live bounds.
- `matrix_array`: applies an explicit ordered list of validated Matrix4 values
  to one input solid and unions the copies. It supports independent X/Y/Z tilt.
- `profile_sweep_3d`: transports a rectangular profile along a 3D path using a
  deterministic parallel-transport frame. Degenerate paths fail closed.

All three operators must appear in the AST allowlist, compiler trace, program
hash, geometry hash, and tests.

## Diversity contract

Hash uniqueness is necessary but insufficient. Every accepted candidate gets a
scale-invariant morphology descriptor containing:

- normalized axis ratios;
- normalized floor-area profile;
- Z-slice area profile;
- convexity/solid-to-hull ratio;
- void fraction;
- surface-normal orientation histogram;
- radial distribution histogram;
- component count and declared contact topology;
- silhouette occupancy signatures for fixed isometric/front/side views.

Acceptance requires:

- one connected, watertight, manifold component;
- unique program, geometry, and normalized-mesh hashes;
- minimum morphology distance from every accepted candidate;
- minimum within-family distance;
- correct family topology witness;
- no index-only Matrix4 perturbation accepted as novelty.

For 100 candidates across 15 families, quotas differ by at most one. The
stepped family receives no more than its balanced quota. Four capacity bands
are balanced globally and each family sees every band when its quota permits.

## Storey and legal boundary

The creative board remains a pre-legal choice pool. Storeys are explicit
horizontal occupied sections used to communicate architectural scale and
capacity intent; they are not final floor plans or legal GFA certificates.

The legal agent remains fail-closed:

- law/PNU/parking truth comes from law services and cited Neo4j evidence;
- legal projection may preserve or reject authored form;
- non-stepped candidates may not silently become stepped floor prisms;
- only an intentionally stepped recipe may carry stepped authorship;
- final law, capacity, and visual artifacts bind through program, geometry,
  floor-capacity-plan, and visual hashes.

## Design memory boundary

Actual image bytes remain in the reference asset store. Design memory stores
only URI/path, SHA-256, provenance, rights metadata, embeddings, extracted
principles, retrieval events, VLM judgements, and human pairwise choices.

Law and design memory use separate connection settings:

```text
NEO4J_*                        -> law graph
MAAS_DESIGN_MEMORY_NEO4J_*     -> design memory graph
```

If design-memory settings are absent or point at the configured law database,
Neo4j mirroring is disabled. The portable JSON outcome graph remains available;
there is no silent fallback that writes design observations into the law DB.

## Reference and VLM policy

Reference images supplied to a VLM are request context, not persistent model
training. The system uses retrieval-augmented vision and preference memory:

```text
authorized reference corpus
  -> provenance and digest
  -> program/form retrieval
  -> candidate plus at most three references
  -> structured VLM critique
  -> typed edit directive
  -> compiler and hard gates
  -> stored review and user preference
```

The first paid pilot reviews one representative per family at low-cost detail.
Only if that bounded pilot succeeds are up to twenty finalists reviewed at
higher detail. Retrieval alone never creates `used_by_vlm=true`.

## Frontend contract

The creative portfolio becomes a real archive source, not a loose JSON file
that the frontend happens to know about. The adapter preserves
`run_id/candidate_id/program_hash/geometry_hash`, exposes all 100 members, and
emits family, form class, capacity band, storeys, legal status, and morphology
facets.

The frontend virtualizes or paginates the full 100-card rail. Selecting a card
loads its portable graph and exact candidate passport. Pending legal state is
visually distinct from certified state.

## Acceptance

- Fifteen registered families are exercised.
- A 100-candidate run completes within fifteen minutes.
- All 100 meshes are connected, watertight, manifold, and materially distinct.
- Triangular, oblique crystal, disc, interlocking-disc, long-span, and stepped
  representatives are visible on the board.
- Exactly one balanced family is stepped.
- Candidate JSON contains typed AST, Matrix4 trace, vertices, triangles,
  morphology descriptor, hashes, floor evidence, contact evidence, and legal
  pending state.
- Paid VLM calls are bounded and recorded; retrieval is never mislabeled.
- Law and design Neo4j settings cannot silently share a database.
- The frontend can browse and select all 100 candidates.
- Session memory records exact artifacts, verification commands, limitations,
  and the next action.
