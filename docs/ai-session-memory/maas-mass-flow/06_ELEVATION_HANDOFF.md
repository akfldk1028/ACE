# GeometryProgram MASS to Elevation Agent Handoff

The elevation agent may consume only an exact executed MASS packet produced by
`design.maas.geometry_language.elevation_handoff`. Identity is the tuple
`run_id + mass_index + program_hash + geometry_hash`; the geometry hash must
replay exactly before any facade or elevation work starts.

The packet contains the typed GeometryProgram, indexed triangle mesh, actual
MASS PNG hash, individual VLM evidence, hard-gate state and required output
views. Facade/elevation work may style or project onto this mesh but must not
change its mass geometry.

Current proof packet:

- r188 MASS 10
- 82 vertices, 160 triangles
- geometry replay match: true
- individual VLM program fit: false
- final-elevation approval: false
- status: `mesh_handoff_ready_condition_pack_adapter_pending`

Current execution-graph truth (r206, 2026-07-22):

- Every new MASS passport now carries three downstream nodes in the same causal
  graph: `elevation:mesh_handoff`, `elevation:condition_pack`, and
  `elevation:result`.
- All three are deliberately `not_evaluated` with `artifact_exists=false`.
  This makes the missing continuation visible without inventing an elevation.
- `elevationAgent` is still a renamed generic GitAgent and does not consume the
  GeometryProgram mesh. No generated elevation PNG exists yet.
- Do not change these nodes to passed until a hash-bound consumer writes a real
  condition pack and multi-view result for the exact program/geometry/PNU.

Existing paper and implementation memory:

- `docs/ai-session-memory/maas-aesthetic-texturing/PAPERS.md`
- `docs/ai-session-memory/maas-aesthetic-texturing/IMPLEMENTATION_DECISIONS.md`
- `docs/ai-session-memory/maas-aesthetic-texturing/NEXT_STEPS.md`

Next implementation boundary:

`GeometryProgram indexed mesh -> camera poses -> metric depth + normals +
silhouettes + floor guides -> facade planes -> projection manifest -> locked
multi-view elevation generation -> cross-view/mesh consistency GATE`.

Do not route the new mesh through the legacy mass-GeoJSON volume renderer and
call it complete. Add one adapter; do not create a second geometry authority.
