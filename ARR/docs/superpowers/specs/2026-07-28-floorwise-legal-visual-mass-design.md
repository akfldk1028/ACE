# Floorwise Legal Visual MASS Design

## Goal

Preserve the architecture authored by BaseVolume → BOOK → LLM
GeometryProgram while deriving law-, FAR-, floor-, and parking-checked plates
from the same executable geometry. A selected MASS must render, replay, and
hand off to elevation as one hash-bound product rather than a generic stack of
floor boxes.

## Authority model

One MASS has three explicit authorities:

1. `authored GeometryProgram`: genotype, BOOK/LLM provenance, operator path.
2. `capacity SourceVolume stack`: floor area, BCR/FAR, legal-section and
   parking authority.
3. `projected indexed visual mesh`: board, silhouette, VLM, archive replay and
   elevation authority.

The capacity stack and visual mesh are bound by a
`FloorwiseVisualProjectionCertificate` containing the authored program hash,
authored geometry hash, floor-capacity-plan hash, projected visual geometry
hash, legal-section sample results, and exact floor section comparisons.

## Projection

The projector consumes the complete authored triangle mesh and the Matrix4
records already produced by `materialize_floorwise_legal_source`.

- Source surface vertices are converted from `SourceMass.footprint.centroid`
  local coordinates to world coordinates.
- Every vertex uses a piecewise-linear Matrix4 field in normalized Z. Floor
  center samples reproduce the exact floor matrices; values between centers
  interpolate adjacent matrices.
- Triangle topology is retained. No named finished form, parcel coordinate, or
  label-derived shape is inserted.
- The transformed mesh is localized to the final capacity-source footprint
  centroid and stored as indexed/profiler surface triangles.

## Validation

Projection is fail-closed.

- All coordinates must be finite and all retained triangles non-degenerate.
- Every floor-center section of the projected mesh must lie inside the matching
  legal section.
- Each projected floor-center section must match the corresponding capacity
  plate within a bounded symmetric-difference ratio.
- Every floor boundary and interval midpoint is sampled against the applicable
  conservative legal section.
- A source with an authored profiled mesh may not silently become
  `surfaces=()`. Failed projection rejects the floorwise candidate.

The first implementation uses the existing triangle surface transport. It does
not add a general user-authored `indexed_mesh` AST primitive. Exact replay is
provided by a hash-bound canonical projected-mesh payload in the executed
artifact, while the authored AST remains separately available.

## Consumers

- Shared-floor, BCR/FAR, legal and parking gates continue to consume
  `SourceMass.volumes`.
- Board rendering, silhouette distance, final VLM review, selected archive and
  elevation handoff consume the certified projected visual mesh.
- `floorwise_source_to_geometry_program` remains a capacity replay and may not
  be labeled as the selected visual authority.
- Archive and elevation identities must expose the same projected visual
  geometry hash.

## Portfolio contract

- Target is at least 10 selected, pairwise visually distinct MASS alternatives.
- The hard silhouette distance remains `0.10`.
- Six BOOK base scopes remain required where compatible supply exists.
- Cardinality is optimized before coverage and score.
- Smoke controls provider cost only and never lowers portfolio completeness.
- A paid LLM/VLM pass is attempted only after the deterministic portfolio
  reaches the target.

## Parking

- The current neighborhood PNU uses the computed Seoul requirement of two
  spaces; verified piloti/ground geometry is sufficient.
- Basement and semi-basement strategies remain review-only without a
  verifier-issued ramp geometry certificate.
- Multi-family housing uses row 05 household schedule rules; detached housing
  remains row 04.

## Verification

Required regressions:

1. Different authored meshes with identical capacity proxies retain different
   projected visual hashes and silhouettes while preserving identical GFA.
2. An out-of-envelope projected mesh is rejected instead of erased.
3. Board/archive/elevation expose the same projected visual hash.
4. Legal, FAR and parking gates continue to read capacity plates.
5. A free benchmark produces at least 10 accepted cards with zero admitted
   near-duplicate pairs and a manually reviewed PNG.
6. One bounded paid LLM/VLM run and the live `design/language` route are checked
   only after deterministic completion.

