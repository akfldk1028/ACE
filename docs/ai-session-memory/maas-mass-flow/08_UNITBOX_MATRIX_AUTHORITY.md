# Implemented UnitBox Matrix Authority

## Public root

The only public Base Model is `book:base-model:1-1`, a normalized UnitBox with
identity matrix:

```text
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
```

BOOK `3/8`, `1/2`, `1/4`, `1/8`, and `1/16` are `derived_volume` children.
Their cell occupancy contract stays separate from affine transformation.

## Code ownership

- Matrix math: `ARR/backend/design/maas/geometry_language/affine_matrix.py`
- AST/compiler: `ast.py`, `compiler.py`
- UnitBox lowering for 18 executable probes: `programs.py`
- BOOK root/derivation graph: `book_exploration_graph.py`, `language_system.py`
- Execution trace/passport: `execution_activation.py`, `execution_passport.py`
- One frontend graph: `BookLanguageFlow.tsx`, `LanguageNetworkCanvas.tsx`
- Contract tests: `test_maas_unitbox_matrix.py`,
  `LanguageNetworkCanvas.test.tsx`

## Matrix convention

Matrices are row-major and multiply column vectors. Program-order composition
`scale` then `translate` evaluates as `T * S`. Pivoted transforms evaluate as
`T(p) * M * T(-p)`. The geometry kernel receives the top 3x4 affine block.

Do not put redundant matrix fields into author-program metadata merely for UI.
That changes `program_hash` and can perturb deterministic search. Derive the
matrix in compiler trace and graph projections instead.

## r206 proof

Execution: `single-execution:r206-unitbox-two-matrix-elevation-trace`.

- Primitive volume: `1.0` (`UnitBox`).
- Host matrix: diagonal `[5, 5, 16, 1]`.
- Lean matrix: row 0 contains `z shear = 0.2`.
- Geometry: compiled, watertight, one component, gate pass.
- Geometry hash: `0c8e115eb859e1b66ca3480fc1c1f4be1458473ffeba5cd00aeed18dada50015`.
- Final status: `needs_evidence` because PNU/capacity/parking/VLM were not
  supplied; geometry readiness is not legal/design acceptance.

Browser evidence:

- `docs/playwright/design-route-live-verify/r206-unitbox-two-matrix-elevation-graph.png`
- `docs/playwright/design-route-live-verify/r206-unitbox-two-matrix-elevation-selected-path.png`
- `docs/playwright/design-route-live-verify/r206-unitbox-two-matrix-elevation-selected-path-right.png`

The full graph has three matrix glyphs: UnitBox identity, host scale and lean.
The selected execution path intentionally shows only the latter two authored
execution matrices. It also shows the generated MASS and the three pending
elevation continuation nodes on the same horizontal causal graph.

## Elevation truth

The graph now exposes the intended continuation, but only as pending:

`MASS result -> mesh handoff -> condition pack -> elevation result`.

The existing `elevationAgent` is not an implemented elevation consumer. The
next real work is indexed mesh face extraction, stable facade IDs, camera/depth/
normal/silhouette/floor-guide generation, then multi-view generation and a
cross-view/mesh consistency gate. Until real files exist, the UI must show
`not_evaluated` and `artifact_exists=false`.
