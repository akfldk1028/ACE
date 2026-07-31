# UnitBox 4x4 MASS Authority Design

## Decision

MAAS has exactly one public geometry origin: the normalized `1/1 UnitBox`.
`3/8`, `1/2`, `1/4`, `1/8`, and `1/16` are derived BOOK volume states. `BLOCK`,
`SLAB`, `BAR`, and `TOWER` are reusable proportion presets, not sibling base
models. A profiled prism is a derived profile/cut program, not another base
authority.

The term "4x4 matrix" has two distinct representations and they must not be
collapsed:

1. A homogeneous 4x4 affine matrix represents translate, rotate, scale,
   reflect, and shear in the current Solid's local frame.
2. A BOOK occupancy/partition contract represents topology-changing volume
   selection. It may use normalized cells, but it is not an affine matrix.

Boolean, cut, bend, twist, repetition, attachment, sweep, and composition stay
recursive Solid-to-Solid programs because an affine matrix cannot change
topology or perform a nonlinear deformation.

## Canonical causal graph

The single frontend graph and every execution passport use this order:

`1/1 UnitBox -> affine/proportion derivation -> BOOK volume derivation ->`
`orientation -> BOOK operation -> recursive GeometryProgram -> compiler ->`
`geometry gate -> MASS render -> law/parking/VLM -> selector -> MASS result ->`
`face extraction -> elevation condition pack -> elevation result -> elevation gate`

Only materialized execution edges are highlighted for a selected MASS. The
full graph may show available language, but it must not imply that every edge
was executed.

## Geometry representation

Every affine transform node exposes a row-major `matrix4`:

```json
{
  "type": "transform",
  "operator": "matrix4",
  "input": "unit_box",
  "parameters": {
    "matrix4": [
      [2.8, 0.0, 0.0, 0.0],
      [0.0, 0.62, 0.0, 0.0],
      [0.0, 0.0, 0.48, 0.0],
      [0.0, 0.0, 0.0, 1.0]
    ]
  }
}
```

Author-friendly `translate`, `rotate`, `scale`, `mirror`, and `shear` remain
valid DSL operators. Semantic validation converts each to a matrix, composes
adjacent affine transforms in program order, and records both the authored
operators and the evaluated matrix. Pivot transforms use
`T(pivot) * M * T(-pivot)`.

BOOK volume derivation records its normalized occupied cells and the current
host geometry hash. A `3/8` L is therefore a traceable union/intersection of
three normalized octants, never a fake non-uniform scale.

## Compatibility boundary

Existing seed names remain accepted as authoring presets during migration.
They expand below UnitBox and are hidden from public root authority. Existing
programs do not need to be rewritten at once. New programs and graph manifests
must expose `canonical_base_model = 1/1 UnitBox` and explicit transform
matrices.

## Frontend graphics

The first graph card contains one UnitBox. The next card displays the active
4x4 transform matrix and, when present, a separate normalized BOOK occupancy
glyph. Derived ratios are children of UnitBox. Selecting a MASS dims all
unexecuted edges and shows the exact matrix, occupied cells, GeometryProgram,
MASS PNG, hashes, and downstream agent/elevation nodes in the same canvas.

No BOOK scan raster appears in the causal UI. Reference photographs appear
only as reference nodes and are marked pending until the recorded VLM request
actually used their exact bytes.

## Elevation boundary

Elevation never starts from an unselected or rejected candidate. It consumes a
hash-bound accepted/explicitly-selected MASS packet containing:

- execution ID, program hash, geometry hash, and PNU;
- indexed vertices and triangle faces;
- extracted facade planes and stable face IDs;
- camera poses, silhouettes, metric depth, normals, floor guides, and masks.

`elevationAgent` must validate the packet, generate a condition-pack manifest,
produce multi-view elevation artifacts, and return an elevation result bound to
the same hashes. Cross-view consistency, projection-to-face consistency, and
artifact existence are hard gates. Until those stages exist, the frontend must
show `condition_pack_pending`, never an invented elevation result.

## Verification

Acceptance requires:

1. Backend tests prove one root Base Model and matrix composition.
2. Existing transforms compile to equivalent non-empty solids.
3. `3/8` remains the connected three-octant L with exact volume.
4. The manifest exposes one root plus derived BOOK volumes.
5. The frontend renders a matrix glyph and selected causal path.
6. A real GeometryProgram produces a MASS PNG and execution passport.
7. Browser verification confirms one graph, no BOOK raster, and no console
   errors.
8. Elevation is reported honestly as pending until a real condition pack and
   image artifacts exist.
