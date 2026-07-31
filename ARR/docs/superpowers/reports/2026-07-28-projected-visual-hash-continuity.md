# Projected Visual Hash Continuity

## Scope

- Preserve the validated certified projected visual `CompilationResult` during
  exact archive replay in HTTP and CLI execution paths.
- Use the projected visual hash, not the capacity replay hash, for render
  observations and downstream single-MASS identities.
- Retain the capacity hash separately as audit evidence.

## Root Cause

`compile_executed_mass()` correctly rehydrated and validated the archived
projected visual mesh, but both HTTP and CLI callers discarded that compilation
and passed only its capacity replay `GeometryProgram` to `execute_single_mass()`.
The pipeline compiled that program again, replacing the projected visual hash
with the capacity hash. Separately, `observe_portfolio_render()` ignored the
render evidence hash and used the bridge capacity hash as its observation and
render-node identity.

## Implementation

- `execute_single_mass()` accepts an already validated certified compilation,
  checks exact program identity and certified visual markers, and uses it for
  rendering, collaboration, passport, elevation, and result identities.
- Capacity metrics are retained for the geometry gate while the actual mesh and
  identity remain the certified projected visual mesh.
- HTTP and CLI archive replay pass the validated compilation through instead of
  recompiling the capacity program.
- A replay of a prior single execution follows its immutable source provenance
  back to the original portfolio archive and invokes `compile_executed_mass()`
  again. Missing origins, cycles, and program/geometry mismatches fail closed.
  No weaker mesh sidecar is trusted.
- Render observations require the board evidence projected visual hash to equal
  the source `floorwise_visual_projection.visual_hash`. Observation IDs,
  geometry attributes, and render-node IDs use that visual hash, while
  `capacity_geometry_hash` remains separate.

## TDD Evidence

Initial RED run: 6 tests, 4 failures and 2 errors.

- `validated_compilation` was not accepted.
- CLI and HTTP returned the capacity hash.
- outcome graph returned the capacity hash.
- projected visual certificate mismatch did not raise.

After implementation, the focused verification command passed 32 tests:

```text
python manage.py test \
  design.test_maas_single_execution \
  design.test_maas_outcome_render_memory \
  design.test_maas_flow_regressions.MaasFlowRegressionTest.test_render_observation_uses_certified_projected_visual_hash \
  design.test_maas_flow_regressions.MaasFlowRegressionTest.test_render_observation_rejects_visual_hash_certificate_mismatch \
  design.test_maas_flow_regressions.MaasFlowRegressionTest.test_render_observation_rejects_missing_visual_certificate

Ran 32 tests in 5.330s
OK
```

Additional regressions cover pre-normalization program identity, missing
original archive provenance, recovery through a single-execution chain, and
tampered original archive identity.

## Known Shared-Tree Note

The full `test_maas_flow_regressions` module currently has one independently
owned failure in the authored visual preference fixture introduced by the
concurrent legal-authority work. The hash-continuity tests listed above pass;
this change does not edit the concurrently owned preference implementation.
