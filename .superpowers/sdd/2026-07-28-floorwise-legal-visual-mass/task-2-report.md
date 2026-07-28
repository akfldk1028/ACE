# Task 2 Report — Projected Visual Mesh Archive and Elevation Binding

## Status

DONE. The Task 1 certified projected triangle skin is now the renderer/archive/elevation visual authority. The floorwise `GeometryProgram` remains capacity replay metadata and provenance.

Implementation commit: `5da2512` (`feat(maas): bind certified visual mesh through archive`)

## Files

- `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- `ARR/backend/design/maas/geometry_language/executed_archive.py`
- `ARR/backend/design/maas/geometry_language/elevation_handoff.py`
- `ARR/backend/design/test_maas_flow_regressions.py`

Unrelated pre-existing working-tree hunks in the portfolio and test files were left unstaged and uncommitted. `test_maas_export.py` was not changed by Task 2.

## Contract Implemented

- Portfolio artifacts persist the exact, unrounded Task 1 triangle records as `projectedVisualMesh`, alongside `projectedVisualCertificate` and `projectedVisualGeometryHash`.
- Portfolio board evidence carries the same projected visual hash, and rendering consumes exact local triangle coordinates rather than the older three-decimal surface signatures.
- Artifact `identity.geometryHash` is the certified projected visual hash.
- The floorwise program is explicitly labeled `capacity_replay_metadata_and_provenance`; it is not declared visual authority.
- Executed archive hydration validates schema, certificate status, coordinate frame, capacity program identity, triangle counts, finite coordinates, and the canonical Task 1 visual hash before returning vertices/triangles.
- Partial, malformed, or hash-altered projected mesh bindings fail closed.
- Elevation handoff uses the validated archived vertices, triangles, coordinate frame, certificate, and projected visual hash.
- Archives without the new projected-visual fields retain their legacy replay path.

## TDD Evidence

### RED

Command:

`C:\Python313\python.exe manage.py test design.test_maas_flow_regressions.MaasFlowRegressionTest.test_projected_visual_identity_survives_board_archive_and_elevation design.test_maas_flow_regressions.MaasFlowRegressionTest.test_projected_visual_archive_tamper_fails_closed -v 2`

Result: `FAILED (errors=2)`.

Both tests failed at the intended missing boundary:

`AttributeError: module 'design.maas.book_language.portfolio_benchmark' has no attribute '_certified_projected_visual_artifact'`

### Focused GREEN

Same command after production implementation:

`Ran 2 tests in 0.071s — OK`

The identity test checks exact float payload preservation, board hash, executed archive hash/mesh, elevation hash/mesh, coordinate space, and capacity-program demotion. The tamper test changes one archived coordinate and verifies a fail-closed `projected visual mesh hash mismatch`.

### Full Flow Module

`C:\Python313\python.exe manage.py test design.test_maas_flow_regressions -v 1`

`Ran 11 tests in 0.284s — OK`

### Mandated Combined Modules

`C:\Python313\python.exe manage.py test design.test_maas_export design.test_maas_flow_regressions -v 1`

Result: `Ran 99 tests in 237.348s — FAILED (failures=16)`.

All Task 2 focused tests and all 11 flow regressions passed. The 16 failures were confined to existing `MaasLegalVariantsTest` export-domain assertions:

1. `test_buildable_max_variant_can_outgrow_small_source_mass`
2. `test_edge_specific_setback_geometry_avoids_global_road_buffer`
3. `test_final_selection_keeps_stepback_and_weak_llm_caps_after_replacement`
4. `test_formal_compiler_records_genome_strategy_specific_roles` (`grammar_overlap_shift_terrace__sweep_lift_low`)
5. `test_formal_principle_generates_stacked_platform_roles`
6. `test_interactive_offset_edge_returns_agent_reviewed_legal_mass`
7. `test_layered_stack_uses_floor_by_floor_envelope`
8. `test_maas_agent_registry_exposes_flow_cards`
9. `test_massdsl_agent_contract_compiles_from_candidate_evidence`
10. `test_massing_genome_prioritizes_family_over_taper_tokens` (`grammar_courtyard_lift_taper__sweep_court_open`)
11. `test_massing_genome_prioritizes_family_over_taper_tokens` (`grammar_diagonal_step_connector__sweep_taper_sharp`)
12. `test_massing_genome_prioritizes_family_over_taper_tokens` (`grammar_sloped_roof_envelope__sweep_taper_sharp`)
13. `test_massing_genome_prioritizes_family_over_taper_tokens` (`grammar_interlock_step_taper__sweep_interlock_thick`)
14. `test_sunlight_cap_and_bcr_fill_are_prioritized`
15. `test_typology_selection_filters_fail_and_repair_even_when_under_limit`
16. `test_variant_selection_preserves_capacity_and_shape_diversity`

Observed assertion roots were unrelated legal-variant choice/capacity expectations, morphology role/genome expectations, and agent registry/review expectations. No failure entered the Task 2 serializer, archive validator, or elevation handoff.

Baseline limitation: this is a heavily dirty shared worktree, and no destructive stash/reset or isolated clean-baseline rerun was authorized. The non-Task-2 attribution is supported by the scoped commit diff (no `test_maas_export.py`, legal optimizer, morphology, or agent-registry changes), the passing focused tests, and the passing complete flow-regression module; it is not claimed as a clean-baseline reproduction.

## Self-review

- Verified the archive hash algorithm matches Task 1 field selection, ordering, eight-decimal normalization, sorted JSON keys, and compact separators.
- Verified the stored coordinates themselves are not rounded.
- Verified elevation does not recompile floor-box geometry as visual authority.
- Verified malformed counts, coordinate frames, certificate identity, program identity, non-finite values, and payload tampering fail closed.
- Verified only allowed production/test files were included in the implementation commit.
- `git diff --check` passed; only existing Windows line-ending notices were emitted.

## Concerns

- The combined export suite is not fully green due to the 16 unrelated failures listed above.
- Legacy archives without Task 1 projected-visual fields intentionally use the previous geometry-program replay behavior for backward compatibility.
