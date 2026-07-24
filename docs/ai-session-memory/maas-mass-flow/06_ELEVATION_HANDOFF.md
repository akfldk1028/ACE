# GeometryProgram MASS to Elevation Agent Handoff

The elevation agent may consume only an exact executed MASS packet produced by
`design.maas.geometry_language.elevation_handoff`. Identity is the tuple
`run_id + mass_index + program_hash + geometry_hash`; the geometry hash must
replay exactly before any facade or elevation work starts.

The packet contains the typed GeometryProgram, indexed triangle mesh, actual
MASS PNG hash, individual VLM evidence, hard-gate state and required output
views. Facade/elevation work may style or project onto this mesh but must not
change its mass geometry.

Current execution-graph truth (r211-r216, 2026-07-24):

- `elevationAgent` consumes the exact compiled indexed mesh after the MASS
  render and writes a hash-bound condition pack plus six PNG views.
- The camera contract is semantic (`direction` and `up`). Horizontal, vertical
  and depth axes and the row-major affine `view_matrix4` are derived by vector
  normalization and cross products; precomputed camera-basis decimals are not
  an authoring authority.
- Condition-pack outputs include stable face IDs, camera poses, silhouette
  bounds, metric depth, triangle normals, 3.3 m floor guides and four facade
  planes. `geometry_mutation_allowed=false`.
- Every new passport carries active nodes in the same causal graph:
  `elevation:mesh_handoff -> elevation:condition_pack -> elevation:result`.
  Their evidence is generated only after the files exist and their program and
  geometry hashes match the MASS.
- r211-r216 each generated front/right/back/left/top/axon views. Clicking a
  bottom MASS card changes the graph and the right-sidebar elevation bundle to
  the same execution ID. Elevations never become bottom-archive MASS cards.

Existing paper and implementation memory:

- `docs/ai-session-memory/maas-aesthetic-texturing/PAPERS.md`
- `docs/ai-session-memory/maas-aesthetic-texturing/IMPLEMENTATION_DECISIONS.md`
- `docs/ai-session-memory/maas-aesthetic-texturing/NEXT_STEPS.md`

Next implementation boundary:

`condition pack -> actual facade/section synthesis -> cross-view/mesh
consistency GATE`. The current views are deterministic mesh projections, not a
claim that a designed facade, floor plan or code-compliant elevation exists.

Do not route the new mesh through the legacy mass-GeoJSON volume renderer and
call it complete. Add one adapter; do not create a second geometry authority.
