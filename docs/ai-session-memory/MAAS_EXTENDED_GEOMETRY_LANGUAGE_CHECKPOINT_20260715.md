# MAAS Extended Geometry Language checkpoint

Updated: 2026-07-15

## Purpose

This checkpoint records the first real recursive solid-program layer for MAAS.
It addresses the question "can one box seed become dozens of materially
different architectural masses?" with compiled geometry rather than labels or
parameter-only box variants.

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
`arr.maas.vlm_prompt.graph_edit_geometry_program_edit.v6`.

The LLM author adapter requests explicit assignment-only DSL and parses it into
an acyclic SSA-normalized graph. It rejects prose, invalid references and
duplicate programs. The live OpenAI author/critic request was **not run** in
this session because `OPENAI_API_KEY` was absent. Deterministic closed-loop
tests prove the callback/edit/recompile mechanics, not live model quality.

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
BASE 6 -> OPERATIVE 30 -> COMBINATION 20 -> AGGREGATION 9 -> GeometryNode
```

Selecting a base or operation updates the highlighted relation path, mass glyph
and explicit DSL. DOM attributes carry the same base ID, principle ID,
execution verb and input/output topology used by agents. Browser verification
found 6 base controls, 30 operative controls, selected
`book:operative:bend`, produced
`bend(base, axis=?, angle=?, curvature=?)`, and had zero console/page errors.

Evidence:

- `docs/playwright/design-route-live-verify/mass-brain-base-transform-language-20260715.png`

Mass-Brain `npm run verify` passed 13 unit tests, typecheck, builds, dist smoke,
Vite build and Playwright smoke; `npm audit --audit-level=high` found zero
vulnerabilities. The UI glyphs are explanatory projections; ARR remains the
owner of real geometry and hard gates.

## Verification

- 8 new geometry-language tests pass.
- 31 combined geometry-language, BOOK scope, BOOK language and Mass-Brain
  bridge tests pass.
- the three requested program/BOOK geometry mutation tests pass.
- seven existing VLM graph-edit contract tests pass.
- Python byte-compilation passes.

## Honest unresolved boundary

The current full BOOK/program PNU benchmark remains a visual and downstream
hard-gate failure despite its 60/60 numeric source portfolio. Same-source legal
projection has geometry retention 0/60 and combined legal/retention/parking
pass 0/60. The new solid language has not yet replaced or bypassed that
pipeline. The next integration must adapt recursive solid programs to real
parcel/program/legal/parking constraints without destructive post-clipping and
must measure accepted-source geometry retention. Do not claim competition-grade
or permit-ready completion from the 18/18 language benchmark.
