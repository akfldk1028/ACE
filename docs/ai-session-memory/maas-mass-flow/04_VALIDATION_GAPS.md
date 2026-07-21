# Open Validation Gaps

## P0 — visual and geometry integrity

- r188 MASS 07 (`pack · inflate`) contains obvious floating raster fragments
  although current solid-component and clean-mass metadata pass.
- Add a post-render connected-component/noise audit and deeper mesh
  self-intersection, degenerate-face and triangulation checks before archive
  acceptance. Do not hardcode one candidate or one operator pair.
- Produce stable multi-view evidence per selected MASS. One isometric crop can
  hide connecting cores and mislead both humans and VLM.
- Keep component/manifold checks, but never treat them alone as visual proof.

## P0 — portfolio search

- r188 still stops at 16/20. Analyze the final incompatibility graph and report
  which pairwise constraints bound the maximum compatible set.
- Preserve behavior-cell diversity while adding solver-aware compatibility
  reserves. Do not simply relax silhouette, law, parking or capacity gates.
- Feed the paid critic's typed missing-family list into the next authoring run:
  courtyard, split bridge, L/U mass, carve void, lift, notch, terrace and cross.

## P0 — VLM truth

- r188 has one paid board-level audit and three paid individual candidate
  audits. The remaining 13 selected MASSes have no individual VLM evaluation.
- Keep board critic and reference critic as separate graph roles. A future
  bounded reference run must record every submitted image hash, model/response
  ID, cost and `used_by_vlm=true` edge.
- The paid critic missed the obvious MASS 07 fragments, so it cannot replace
  deterministic raster/mesh integrity gates.
- The new individual critic did flag MASS 07 `too_fragmented`, but a stochastic
  critic still cannot replace a deterministic post-render fragmentation gate.
- The legacy elevation condition-pack renderer accepts mass GeoJSON volumes,
  not GeometryProgram indexed meshes. Do not claim elevation generation is
  ready until the mesh projection/condition adapter is implemented and tested.
- r182 was not VLM reviewed. r184 spent 24 calls and produced no final MASS.
  Preserve both facts; never retroactively approve either run.

## P0 — approval-grade legal authority

- Verify current Seoul/Gangnam parking and building-rule sources against
  official ordinance text, effective dates, exceptions and parcel overlays.
- Add source URL, article/appendix, effective date and parsed-text hash.
- Check road/building-line constraints, district-unit plans, fire access,
  evacuation, accessibility, landscape calculation and use restrictions.
- Keep the current result labelled massing preflight, never permit approval.

## P1 — runtime efficiency and observability

- r188 streaming MAP-Elites held memory near 1.1 GB but repeated morphology
  descriptor calculation kept runtime at 4,292 seconds.
- Cache descriptors by geometry hash and add AST/mesh/GATE content-addressed
  caches plus cycle checkpoints with current selected count and stop reason.
- Do not regain speed by deleting rare behavior cells.

## P1 — site semantics and module seams

- Keep explicit evidence fields for parcel geometry used for fit versus absolute
  coordinates used for authoring.
- Continue splitting large policy modules by stable contracts, not by creating
  parallel implementations. Keep one public orchestration path and one
  canonical AST/compiler.
