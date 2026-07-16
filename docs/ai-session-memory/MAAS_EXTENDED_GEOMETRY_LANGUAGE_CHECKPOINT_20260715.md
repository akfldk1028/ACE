# MAAS Extended Geometry Language checkpoint

Updated: 2026-07-15

## Purpose

This checkpoint records the first real recursive solid-program layer for MAAS.
It separates parcel-relative p.3 `SITE SCOPE`, normalized `BASE SEED`, and
kernel `Primitive`. BLOCK, SLAB, BAR and TOWER are exact `Scale(UnitBox)`
programs; PROFILED PRISM is a separate profile/extrusion seed. Recursive
operations can turn these seeds into materially different solids.

Important correction: the original 18 demonstration programs are **not** all
derived from one identical cube. An audit found different primitive signatures
across all 18 programs (21 Box nodes plus one Sweep and one Loft in total).
Never describe 18/18 as literal proof that one unchanged cube produced every
result. It proves recursive language-family and solid diversity. The separate
five-seed benchmark proves that four useful base proportions share UnitBox.

The system is an extended CSG procedural architectural massing language:

```text
Architectural macro / text DSL / JSON AST
  -> semantic validation and acyclic reference check
  -> recursive solid evaluation
  -> transform / Boolean / deformation / cut / pattern / composition
  -> manifold solid kernel
  -> mesh and four-view render
  -> geometry hard gate
  -> VLM typed AST edits
  -> recompile, re-render and re-gate
```

Every primitive and every operation returns a `GeometryNode` solid, so Boolean,
bend, taper, twist, slice, sweep, loft, array, stack and composition results can
be nested again. The runtime kernel is `manifold3d>=3.4,<4.0`; the existing
parcel-derived 2.5D `SourceMass` remains intact and is not silently replaced.

## Implemented files

- `ARR/backend/design/maas/geometry_language/ast.py`
- `ARR/backend/design/maas/geometry_language/base_seeds.py`
- `ARR/backend/design/maas/geometry_language/compiler.py`
- `ARR/backend/design/maas/geometry_language/dsl.py`
- `ARR/backend/design/maas/geometry_language/mutation.py`
- `ARR/backend/design/maas/geometry_language/gate.py`
- `ARR/backend/design/maas/geometry_language/cost.py`
- `ARR/backend/design/maas/geometry_language/render.py`
- `ARR/backend/design/maas/geometry_language/programs.py`
- `ARR/backend/design/maas/geometry_language/llm_adapter.py`
- `ARR/backend/design/maas/geometry_language/vlm_adapter.py`
- `ARR/backend/design/maas/geometry_language/loop.py`
- `ARR/backend/design/management/commands/benchmark_maas_geometry_language.py`
- `ARR/backend/design/test_maas_geometry_language.py`

The existing VLM response contract now includes bounded typed geometry edits:
`set_parameter`, `replace_operator`, `add_node`, `remove_node`, `rewire_input`
and `set_root`. A revision is admitted only when the AST hash and compiled
geometry hash both change and the complete solid gate passes again. Existing
component-graph edits remain supported; the contract version is
`arr.maas.vlm_prompt.ai_readable_graph_snapshot_geometry_program_edit.v8`.

The VLM payload now contains `geometry_graph_snapshot` with stable node IDs,
solid-input edges, semantic role, editable parameters, expected effect,
compiled triangle/volume evidence and the bounded edit contract. The AST is
authoritative; graph notes are explicitly non-executable observations. A VLM
edit is accepted only through node-bound `geometry_edits`, validation,
recompile, rerender, geometry-hash change and hard-gate recheck.

The LLM author adapter requests explicit assignment-only DSL and parses it into
an acyclic SSA-normalized graph. It rejects prose, invalid references and
duplicate programs. The live OpenAI author/critic request was **not run** in
this session. A key posted in chat was treated as compromised and was not used
or stored. It must be revoked and replaced through a secure environment
variable. Deterministic tests prove callback/edit/recompile mechanics, not live
model quality.

## Scope and normalized base seeds

```text
SITE SCOPE 6 -> BASE SEED 5 -> ordered recursive operations -> RESULT SOLID
```

- SITE SCOPE: 1/1, 3/8, 1/2, 1/4, 1/8, 1/16 of the parcel envelope.
- BLOCK: `Scale(UnitBox, [1.0, 1.0, 1.0])`
- SLAB: `Scale(UnitBox, [2.2, 1.45, 0.28])`
- BAR: `Scale(UnitBox, [2.8, 0.62, 0.48])`
- TOWER: `Scale(UnitBox, [0.68, 0.68, 2.5])`
- PROFILED PRISM: `Extrude(PolygonProfile, height)`

The first four reuse the same 1x1x1 Box node. Named seeds are semantic search
priors, not extra kernel primitives or completed-building templates. SITE SCOPE
is a parcel constraint and is not a synonym for seed proportion.

## Eighteen real compiled language families

`architectural_shape_programs()` contains:

1. bent linear mass
2. radial fan mass
3. L mass
4. U mass
5. courtyard mass
6. attached volume
7. overlapping rotated mass
8. setback mass
9. cross mass
10. tapered mass
11. leaning tower
12. notched mass
13. diagonal slice
14. cut-corner polyhedron
15. lofted top/bottom mass
16. swept curved bar
17. split-wing bridge
18. twisted mass

Latest benchmark:

- compile/gate: 18/18
- unique program hash: 18/18
- unique solid geometry hash: 18/18
- visible connected components: all <= 5
- four-view perceptual near-duplicate pairs below distance 0.10: 0
- minimum pair distance: 0.148438
- visual-language verdict: PASS for language-family separation

This does **not** mean every probe is competition-grade architecture. Several
families intentionally remain elementary L/U/courtyard/attached primitives.
The benchmark proves the language can leave the box family and construct
different solid/topological programs; it is not an aesthetic superiority test.

Evidence:

- `docs/playwright/design-route-live-verify/geometry-language/maas-geometry-language-18.png`
- `docs/playwright/design-route-live-verify/geometry-language/maas-reference-language-3.png`
- `docs/playwright/design-route-live-verify/geometry-language/maas-geometry-language-summary.json`

## Supplied photo language probes

The three supplied photographs were abstracted into transferable operator
programs rather than parcel coordinates or copied completed-building templates:

- SongEun: oblique tapered/lofted monolith plus subtractive wedge
- Amorepacific: carved cube/large void plus cantilever relation
- Photography Seoul Museum: lifted/leaning envelope plus diagonal undercut

All three compile and pass the solid gate. Their current renders are low-detail
language probes, not claims of photo matching or design equivalence.

## Mass-Brain 5210 UI

The related Mass-Brain debug UI at `D:\Data\Mass-Brain` now renders a clickable
machine-readable flow:

```text
SITE SCOPE 6 -> BASE SEED 5 -> OPERATIVE 30 -> COMBINATION 20
  -> AGGREGATION 9 -> GeometryNode
```

Scope, seed and operation nodes are interactive. The selected node exposes an
`arr.maas.ai_readable_geometry_graph.v1` JSON snapshot with node ID, inputs,
semantic role, parameters, editable fields, expected effect and typed mutation
acceptance contract. The UI also makes the real loop legible as Reference VLM
-> LLM author -> compiler -> VLM critic -> gate -> selector. It labels the
contract as wired, not as a completed live model call.

Evidence:

- `docs/playwright/design-route-live-verify/mass-brain-scope-seed-transform-language-20260715.png`
- `docs/playwright/design-route-live-verify/geometry-language/maas-base-seed-5.png`

Mass-Brain `npm run verify` passed 13 unit tests, typecheck, builds, dist smoke,
Vite build and Playwright smoke; `npm audit --audit-level=high` found zero
vulnerabilities. The UI glyphs are explanatory projections; ARR remains the
owner of real geometry and hard gates.

## Verification

- 11 geometry-language tests pass.
- 34 combined geometry-language, BOOK scope, BOOK language and Mass-Brain
  bridge tests pass.
- the three requested program/BOOK geometry mutation tests pass.
- seven existing VLM graph-edit contract tests pass.
- Python byte-compilation passes.

Mass-Brain `npm run verify` passed 13 unit tests, typecheck, builds, dist smoke,
Vite build and Playwright interaction smoke. The browser test verifies 6 scope
controls, 5 seed controls, 30 operative controls, the node-bound JSON snapshot
and six-stage VLM loop. `npm audit --audit-level=high` found 0 vulnerabilities.

## Research alignment checked on 2026-07-15

- CoMa (2026): contextual architectural massing as VLM-conditioned structured
  geometry over program, site contour and contextual imagery.
- CAD-Assistant (ICCV 2025): a VLLM uses CAD tools, observes geometry and
  adapts subsequent actions in a closed loop.
- CAD-Llama (CVPR 2025): hierarchical semantic annotation plus code-like
  parametric commands rather than free-form mesh prose.
- ShapeWalk (CVPR 2024): stable multi-step language edits in a shape-program
  parameter space.
- LayoutVLM (CVPR 2025): visually marked representation paired with a
  structured scene representation and downstream physical optimization.

These papers support the architecture but do not prove MAAS quality. CoMa's
code/data were announced for later release in the checked arXiv version, so it
is not yet an executable dependency here.

## Honest unresolved boundary

The current full BOOK/program PNU benchmark remains a visual and downstream
hard-gate failure despite its 60/60 numeric source portfolio. Same-source legal
projection has geometry retention 0/60 and combined legal/retention/parking
pass 0/60. The new solid language has not yet replaced or bypassed that
pipeline. The next integration must adapt recursive solid programs to real
parcel/program/legal/parking constraints without destructive post-clipping and
must measure accepted-source geometry retention. Do not claim competition-grade
or permit-ready completion from the 18/18 language benchmark.

## 2026-07-16 program integration correction (latest; supersedes the unresolved boundary above)

The recursive solid language is now connected to real program sources, BOOK
p.3 scope, BOOK principles, legal-envelope-first generation, spatial hard
gates, same-source legal/FAR/parking evaluation and a persistent typed outcome
graph. A compiled manifold is bridged into `SourceMass` as authoritative mesh
geometry; subordinate entry/service/gallery components become normalized role
zones rather than floating Lego boxes. The target plan area absorbs the union
of the original program-role components before site fitting.

Agent synthesis is deterministic and auditable:

- input: program role lineage, normalized base-seed set, architectural intent
  tags, bounded candidate count and maximum operator depth;
- output: acyclic `GeometryProgram` AST with stable node IDs and explicit
  parameters;
- authority: only the compiler can create the solid;
- feedback: program/legal/retention outcomes are stored by genotype, scope and
  BOOK principle in a portable graph, with optional Neo4j mirroring;
- VLM: optional critic/revision loop must emit typed node edits and pass AST
  hash change, geometry hash change and complete solid gates.

Profile inference now includes a calm prismatic control and explores up to 12
candidates per lineage. This is a grammar-level correction: without a control,
profiles whose preferred families were all cuts or setbacks collapsed to one
wedge/terrace family. It does not prescribe a final box. The reviewed PNU uses
two independent role lineages and 24 bounded candidates per lineage for each
of neighborhood, gym and cultural programs.

Latest `recursive-pnu-three-program-r32` result on live PNU
`1168011800104170004`:

- recursive portfolios: 60/60 selected;
- BOOK operation counts: neighborhood 19, gym 18, cultural 17;
- selected visual-language keys: 13, 11, 17;
- all six p.3 scopes and all six measured phenotypes occur in every program;
- pose-invariant near-duplicate silhouette pairs: 0 in every program;
- downstream legal/FAR/parking/retention combined hard pass: 60/60;
- retained-volume means: 0.8892, 0.9036, 0.9321;
- minimum selected retained volume: 0.8004.

Measured clean gates remain visible volumes <=5 and effective surfaces <=48.
The compiler also reports connected-component volume ratios; fragments below
8% of total volume are rejected. Portfolio morphology rejects degenerate
connected sheets/spikes using upper-area, horizontal-level, surface-normal and
orientation evidence, and caps measured pyramidal/wedge families rather than
trusting operator labels.

Direct PNG review now passes the narrower procedural mass-diversity question:
calm blocks, long bars, curves, courts, split wings, steps and oblique/cut forms
coexist, and no box/gable/terrace family dominates all alternatives. Program
language also differs quantitatively: gym mean oriented plan aspect is 2.1086,
versus 1.6413 neighborhood and 1.9387 cultural. This still does not validate
circulation, structural span, facade, public realm or competition-level
architectural resolution. `architecture_grade_claim_allowed` remains false.

The exposed OpenAI key was not used or written to the repository. Live VLM
revision stayed disabled; stored typed directives exercised the same graph
contract reproducibly. Revoke the exposed key before any future live run.
