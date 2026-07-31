# GeometryProgram MASS to Elevation Agent Handoff

The elevation agent may consume only an exact executed MASS packet produced by
`design.maas.geometry_language.elevation_handoff`. Identity is the tuple
`run_id + mass_index + program_hash + geometry_hash`; the geometry hash must
replay exactly before any facade or elevation work starts.

The packet contains the typed GeometryProgram, indexed triangle mesh, actual
MASS PNG hash, individual VLM evidence, hard-gate state and required output
views. Facade/elevation work may style or project onto this mesh but must not
change its mass geometry.

Current execution-graph truth (r227, 2026-07-24):

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
- r227 adds a second, optional image-proposal stage without changing this mesh
  authority. `facade_strategy.py` derives a strategy from evaluated geometry
  metrics and operator history; `image_proposal.py` binds every proposal to the
  execution/program/geometry hashes.
- The OpenAI image adapter submits the locked MASS sheet and an edit mask, then
  deterministically composites the result back over the source outside the MASS
  mask. This makes silhouette preservation a local invariant rather than a
  prompt-only request. White/transparent holes inside the editable mask are
  repaired from the locked MASS source.
- Provider calls are explicit, idempotent and bounded: one proposal slot
  (`alt-01`), at most one HTTP attempt per MASS, zero retries. Existing proposal
  manifests are reused and do not incur a second charge.
- Successful evidence adds active edges
  `elevation:condition_pack -> elevation:image_agent ->
  elevation:proposal`. `needs_review`, `fail` and missing artifacts keep those
  edges inactive while preserving the audit record.
- The frontend bottom rail remains MASS-only. Selecting a MASS reveals its six
  technical projections and its own proposal in the right sidebar; identity
  mismatches fail closed and suppress the proposal.

Existing paper and implementation memory:

- `docs/ai-session-memory/maas-aesthetic-texturing/PAPERS.md`
- `docs/ai-session-memory/maas-aesthetic-texturing/IMPLEMENTATION_DECISIONS.md`
- `docs/ai-session-memory/maas-aesthetic-texturing/NEXT_STEPS.md`

Next implementation boundary:

`condition pack + single-view ALT -> multi-view facade/section synthesis ->
cross-view/mesh consistency GATE`. The current ALT is a visual proposal tied to
one MASS sheet. It is not yet a metrically reconstructed facade, floor plan or
code-compliant elevation.

The creative stage belongs to the independent
`ARR/backend/agents/elevationAgent`, not the MASS compiler. It must call image
models through a replaceable provider interface and persist provider/model,
prompt/input/output hashes, response identity and bounded cost evidence. A
future OpenAI image model can be selected at execution time without changing
the GeometryProgram or mesh authority.

Do not route the new mesh through the legacy mass-GeoJSON volume renderer and
call it complete. Add one adapter; do not create a second geometry authority.
