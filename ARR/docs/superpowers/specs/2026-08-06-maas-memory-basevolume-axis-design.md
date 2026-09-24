# MAAS Memory and BaseVolume Axis Design

## Objective

Restore the intended causal authoring order and make it impossible for an AI
worker to confuse form families, affine placement, BOOK fraction scopes, and
deterministic validation.

## Causal contract

Every authored candidate follows this order:

`UnitBox -> authored base-form capability -> one global Matrix4 -> BOOK p.3 fraction scope -> orientation -> ordered BOOK graph operations -> typed CSG -> deterministic legal/capacity certification`

The axes are independent. A fraction such as `1/4` is not a shape family, an
ellipse is not a fraction, and Matrix4 is not a morphology generator.

## Memory architecture

`memory/MEMORY.md` becomes a short mandatory loader. It points to numbered,
single-purpose Markdown modules and a machine-readable `manifest.json` that
defines reading order, authority, and required invariant phrases. Historical
run notes remain preserved in `history/legacy-memory-2026-08-06.md`; they no
longer compete with current contracts near the top of one 700-line file.

## Geometry-language correction

Keep the six exact BOOK p.3 cell scopes unchanged: `1/1`, `3/8`, `1/2`,
`1/4`, `1/8`, `1/16`. Expose normalized UnitBox-derived non-prismatic form
capabilities to the LLM author as a separate axis before BOOK projection.
Elliptical and simplex/tetrahedral capabilities must remain typed operations
with LLM-authored parameters, not deterministic candidate templates. Every
candidate still has exactly one canonical UnitBox and one composed global
Matrix4.

## Harness and gates

The LLM receives a bounded offer that binds base-form capability, fraction,
orientation, Matrix4 contract, and BOOK path. Before persistence or canonical
validation, the exact production selector must produce a legal row and measured
capacity utilization of at least `0.70`. Compiler-only preflight is explicitly
insufficient.

## Verification

Tests must prove:

- the memory manifest is complete, ordered, and loadable;
- the LLM prompt describes the independent axes in the correct order;
- ellipse/simplex capabilities are actually present in the author schema;
- BOOK fractions remain the exact six p.3 scopes;
- source and projected programs preserve one UnitBox and one global Matrix4;
- existing law, capacity, authorship, and mesh suites remain green.

