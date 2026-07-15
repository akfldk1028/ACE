# MAAS sectional-monolith handoff — 2026-07-15

## Correct reading of the user references

The three `KakaoTalk_20260715_095428011*.jpg` references are not primarily
plan-polygon examples. They require elevation/section operations:

- a leaning/wedge outer silhouette with a triangular ground opening;
- a compact monolith cut by a diagonal ground undercut;
- a monolith with a large elevated through-opening and cantilevered material.

The prior polygon-ring loft remains useful, but it changes plan/ring geometry
and therefore cannot by itself represent all three cases. Do not respond by
adding more plan polygons or decorative boxes.

## Representation-level correction

`source_geometry/sectional_monolith_fields.py` implements one generic,
agent-authored solid/void section genotype:

- `section_outer_control_points`: 4-8 normalized
  `[horizontal_position, height]` vertices;
- optional `section_void_control_points`: 3-8 normalized subtractive vertices;
- `section_depth_ratio` and `section_depth_shift_ratio`;
- extrusion along the parcel's minimum-rotated frame.

This is not a named precedent template and contains no parcel coordinates.
Wedges, diagonal undercuts and mega-void/cantilever forms are consequences of
the same editable section representation.

The compiler separates:

- one conservative `primary_agent_sectional_monolith_proxy` for later
  FAR/legal projection;
- an actual `agent_sectional_monolith_mesh` for PNG/VLM review;
- `section_solid_void_extrusion` front/back/reveal surfaces.

A routing bug was found and fixed: an authored primary `extrude` with section
controls was previously overwritten by the generic
`extrude -> slender_podium_tower` family mapping. Executable section controls
now route to `sectional_monolith_cut` before labels or legacy defaults.

## Closed-loop integration

- LLM author prompt and typed validation now distinguish SECTION controls from
  taper PLAN controls and reject self-crossing/disconnected fields.
- Search mutates outer and void vertices and recompiles visible geometry.
- VLM `set_control_point` can edit either section field by exact parameter
  name; edits are rejected if they break the remaining material section.
- Language and spatial gates recognize the actual mesh, require a diagonal
  edge or meaningful void, one clean mass, and at most 48 surfaces.
- Final 20-card selection requires one `sectional_monolith` and permits at
  most two. The plan-oblique family is now optional and capped at one. This
  prevents another all-polygon monoculture.

VLM remains a critic/reranker and typed graph editor. The deterministic source
geometry compiler materializes the edited graph; do not claim that VLM itself
directly generates the mesh.

## Verified evidence

Capability probe:

- `docs/playwright/design-route-live-verify/maas-sectional-monolith-probe-latest.json`
- `docs/playwright/design-route-live-verify/maas-sectional-monolith-probe-latest.png`
- six distinct section solid/void cases;
- one volume each, 11-27 surfaces;
- visible wedge gate, diagonal undercut, elevated mega void, leaning court,
  ground portal and cantilever window.

Focused tests pass:

- section author normalization and invalid-polygon rejection;
- three distinct meshes from one generic representation;
- one clean proxy volume and <=48 surfaces;
- VLM typed section control edit;
- bounded search section mutation and recompilation;
- previous oblique-envelope and generic A2A edit regressions.

This is a capability proof, not a completed real-PNU 20-card run. Law, parking,
FAR projection and geometry-retention measurement were not run for this new
family. Do not call it competition-grade or permit-complete yet.

## Next required run

Run a fresh real-PNU full author -> compile -> clean/capacity gates -> PNG/VLM
critic -> typed mutation -> balanced 20 selection. Confirm exactly 1-2
sectional-monolith survivors among the other architectural languages, then
run deterministic legal/FAR/parking projection and compare the post-repair
section mesh against the accepted source geometry.
