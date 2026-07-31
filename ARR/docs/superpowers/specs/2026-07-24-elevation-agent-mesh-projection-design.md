# MASS Elevation Agent Mesh Projection Design

## Goal

Every geometry-ready single MASS execution must produce hash-bound, inspectable
elevation evidence from its actual compiled mesh. A handoff packet alone is not
an elevation result.

## Chosen boundary

The first complete elevationAgent is deterministic, not generative. It consumes
the exact `GeometryProgram` compilation and generates front, right, back, left,
top, and axon PNGs plus a condition-pack manifest. A later facade-design VLM may
consume these artifacts, but it may not modify the MASS geometry or replace the
deterministic evidence.

## Architecture

- `contract.py` defines the immutable execution identity and bundle result.
- `projection.py` projects indexed triangle mesh views and writes PNG evidence.
- `runtime.py` validates hashes, builds condition data, calls the projector, and
  persists one atomic manifest under the MASS execution directory.
- `single_execution/pipeline.py` invokes the agent only after geometry GATE and
  passes its manifest to the execution passport.
- `execution_activation.py` materializes active elevation handoff, condition,
  and result nodes only when matching artifacts exist.
- `/design/language` reuses the single passport graph and displays elevation
  result thumbnails; no second graph is introduced.

## Data and truth contract

Every elevation bundle stores `execution_id`, `program_hash`, `geometry_hash`,
view name, file SHA-256, mesh counts, orthographic projection axes, silhouette
bounds, depth range, triangle normals, floor guides, and four facade planes.
The bundle status is `generated` only when all six PNGs exist and their hashes
match. Missing or mismatched artifacts remain failed evidence and never become
an active graph edge.

## Rendering

The projector uses the compiled triangle mesh, fixed orthographic cameras, a
neutral white/gray/black architectural drawing palette, equal metric scaling,
and deterministic view ordering. It does not synthesize windows, materials, or
stylistic facade content.

## Validation

Tests cover six-view artifact generation, hash identity, persisted condition
pack, single-execution integration, active passport graph nodes, invalid mesh
failure, UnitBox normalization, and frontend new-run selection. Browser
verification must show the newly executed MASS selected automatically with its
MASS render and generated elevation result in the same graph.
