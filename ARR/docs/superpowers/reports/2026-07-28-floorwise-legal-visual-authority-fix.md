# Floorwise Legal Visual Authority Fix

Date: 2026-07-28

## Outcome

Final floorwise legal repair now preserves a typed `SourceMass` until the legal
capacity stack is known, reprojects authored indexed recursive meshes onto that
stack, and binds the exact projected triangles to a non-empty certification
hash. Renderer/VLM preview generation fails closed when an authored recursive
mesh lacks that binding. Capacity-only proxy candidates remain valid with an
explicit `not_applicable_no_authored_mesh` certificate.

The canonical legal floor plates and volumes remain the GFA authority. The
reprojected authored surfaces are visual authority only; they do not replace or
inflate the legal capacity geometry.

## Root Cause

`source_mass_to_variant()` retained only serialized summaries. Final floorwise
repair then rebuilt the capacity stack and unconditionally removed authored
surfaces, so the exact typed mesh needed for legal reprojection was unavailable
before preference rendering. The renderer also accepted authored profiled mesh
records without verifying that their triangle list matched a successful
floorwise projection certificate.

## Changes

- Added a runtime-only typed `source_mass` field to `MorphologyVariant` and
  carried it through the legal optimizer using transient, per-call identity and
  lineage maps.
- Re-materialized authored recursive mesh sources against the final legal
  sections and rebound canonical plates/volumes from the materialized source.
- Preserved program hash, geometry hash, graph snapshot, variant identity, and
  law-agent review evidence while publishing exact (unrounded) triangle
  coordinates and their certificate hash.
- Rejected authored meshes when typed-source recovery or certified
  reprojection is unavailable, using
  `authored_floorwise_visual_reprojection_failed`.
- Added a preview hard gate that reconstructs `SourceSurface` records and
  verifies the canonical projected visual hash.
- Kept surface-empty legal proxy output valid, explicitly identifying it as
  `floorwise_capacity_proxy_only`.

## TDD Evidence

Focused red/green coverage:

```text
C:\Python313\python.exe manage.py test \
  design.test_maas_export.MaasLegalVariantsTest.test_final_floorwise_repair_reprojects_authored_visual_and_preserves_lineage \
  design.test_maas_export.MaasLegalVariantsTest.test_final_floorwise_reprojection_is_idempotent_with_returned_authored_source \
  design.test_maas_export.MaasLegalVariantsTest.test_authored_source_registry_requires_unique_hash_bound_lineage_for_fallback \
  design.test_maas_export.MaasLegalVariantsTest.test_final_floorwise_authored_visual_without_reprojection_rejects_closed \
  design.test_maas_export.MaasLegalVariantsTest.test_final_floorwise_proxy_anchor_may_remain_surface_empty \
  design.test_maas_visual_authority \
  design.test_maas_preference.MaasPreferenceDistillationTest.test_preview_rejects_authored_profiled_mesh_without_certified_binding \
  design.test_maas_preference.MaasPreferenceDistillationTest.test_preview_renders_certified_authored_profiled_mesh -v 1
```

Result: 10/10 passed in 1.821 seconds. The original focused run was 8/8 in
1.660 seconds. Before implementation, the direct tests failed on the missing
`authored_source` contract, absent fail-closed behavior, and missing proxy
certificate. The preview tests failed before the certificate gate/hash API
existed. The production handoff and rejection-reason tests were also
individually forced through a red state by temporarily disabling the new source
lookup/reason mapping before restoring the implementation.

Reviewer follow-up added two regressions for repeated revalidation and copied
candidate recovery. The first draft accidentally supplied identical complete
identity inputs while expecting different lookup results; that identical-input
contradiction was corrected so the negative fixture actually omits
`geometry_program_bridge_evidence`. The registry test then failed because
`_AuthoredSourceRegistry` did not exist. Repeated repair now retains the
original immutable authored sidecar, and copied-feature fallback requires a
complete unique design/program/geometry identity; colliding lineages are marked
ambiguous and cannot fall back.

Fresh related regression run:

```text
C:\Python313\python.exe manage.py test \
  design.test_maas_preference \
  design.test_maas_shared_floor_contract \
  design.test_maas_visual_authority -v 1
```

Result after the reviewer fixes: 89/89 passed in 3.036 seconds.

Syntax verification:

```text
C:\Python313\python.exe -m py_compile \
  ARR/backend/design/maas/final_floorwise_legal.py \
  ARR/backend/design/maas/geometry_language/floorwise_visual_projection.py \
  ARR/backend/design/maas/legal_mesh_optimizer.py \
  ARR/backend/design/maas/morphology_operators.py \
  ARR/backend/design/maas/preference/loop.py \
  ARR/backend/design/maas/source_geometry/compiler.py \
  ARR/backend/design/test_maas_preference.py \
  ARR/backend/design/test_maas_visual_authority.py
```

Result: passed.

## Broader Baseline

The broader scoped run contained 166 tests: 154 passed and 12 failed. No
failures occurred in `test_maas_preference`,
`test_maas_shared_floor_contract`, or `test_maas_visual_authority`. The exact
12 `MaasLegalVariantsTest` failure records from the 197.807-second confirmation
run were:

1. `test_final_selection_keeps_stepback_and_weak_llm_caps_after_replacement`
2. `test_formal_compiler_records_genome_strategy_specific_roles`
   (`grammar_overlap_shift_terrace__sweep_lift_low`)
3. `test_formal_principle_generates_stacked_platform_roles`
4. `test_interactive_offset_edge_returns_agent_reviewed_legal_mass`
5. `test_maas_agent_registry_exposes_flow_cards`
6. `test_massdsl_agent_contract_compiles_from_candidate_evidence`
7. `test_massing_genome_prioritizes_family_over_taper_tokens`
   (`grammar_courtyard_lift_taper__sweep_court_open`)
8. `test_massing_genome_prioritizes_family_over_taper_tokens`
   (`grammar_diagonal_step_connector__sweep_taper_sharp`)
9. `test_massing_genome_prioritizes_family_over_taper_tokens`
   (`grammar_sloped_roof_envelope__sweep_taper_sharp`)
10. `test_massing_genome_prioritizes_family_over_taper_tokens`
    (`grammar_interlock_step_taper__sweep_interlock_thick`)
11. `test_typology_selection_filters_fail_and_repair_even_when_under_limit`
12. `test_variant_selection_preserves_capacity_and_shape_diversity`

The failures concern existing agent-flow, genome-inference/formal-compiler,
selection-count/replacement, interactive-seed, and MassDSL review expectations.
As an additional non-causality check, two pre-existing selection failures were
rerun after narrowing the new hard gate to indexed recursive meshes; both
failed unchanged while all six visual-authority tests passed.
