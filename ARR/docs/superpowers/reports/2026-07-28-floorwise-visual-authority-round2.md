# Floorwise Visual Authority Round 2

Date: 2026-07-28

Base commit: `5bc0b74 fix(maas): bind preference to certified visual mesh`

This is a separate hardening pass over the preliminary broad-profile,
world-coordinate, and piloti work in `5bc0b74`. It does not modify the
single-execution, archive, outcome-graph, HTTP, CLI, or elevation hash-binding
files owned by the parallel hash-binding task.

## Findings Closed

1. Final legal repair and preference validation consistently treat every
   `surface_type` beginning with `profiled_` as authored visual authority.
   A closed source skin containing `profiled_roof_strip`,
   `profiled_facade_quad`, and `profiled_section_loft` is reprojected and
   preserved rather than cleared.
2. Serialized final surfaces no longer publish `vertices_world_m` as a second,
   unhashed authority. Preview coordinates are derived deterministically from
   the certificate-validated local payload. WGS candidates use UTM meter
   offsets and convert back to WGS; benchmark/projected-frame candidates remain
   in their explicit metric frame. Injected `vertices_world_m` neither changes
   rendering nor the VLM cache key.
3. `_AuthoredSourceRegistry` stores the exact lineage beside an object ID and
   compares the current lineage before returning the fast-path source.
   Identity-less sources are not entered into the ID map, preventing stale
   object-ID reuse or same-object lineage mutation from returning the wrong
   authority.
4. Piloti is an atomic local-mesh transformation: profiled triangles are
   intersected with `z >= void_height_fraction`, crossing polygons are
   triangulated, zero-area and duplicate pieces are removed, and every boundary
   loop is capped with downward-facing `profiled_piloti_underside` triangles.
   The result must be a closed directed two-manifold before a new visual hash is
   certified. Courtyard holes remain holes. Legal floor area, FAR, and floor
   plates remain the separately audited capacity authority.

## TDD Evidence

The persistent round-2 focused run initially found six tests. Three preliminary
tests from `5bc0b74` already passed (broad preference fail-closed behavior and
world-field render/cache indifference). Three strengthened regressions failed:

- `test_piloti_void_clips_and_caps_certified_visual_atomically`: the draft
  retained `vertices_world_m` and only clamped Z, leaving degenerate triangles
  without a cap/manifold proof.
- `test_floorwise_revalidation_preserves_all_profiled_surface_types`: final
  mixed profiled output could not produce the required certified serialized
  authority.
- `test_authored_source_registry_rejects_mutated_same_object_lineage`: the
  object-ID fast path returned the stale source after its lineage changed.

The RED command returned three failures. After implementation, the same six
tests passed in 0.152 seconds. The strengthened piloti cube/manifold test passed
alone in 0.018 seconds, and the final piloti plus courtyard-hole tests passed
2/2 in 0.008 seconds.

A final atomicity regression,
`test_piloti_rejects_open_visual_without_partial_mutation`, then failed because
the invalid open skin raised only after canonical volumes had been changed.
The parking operation now validates a deep working copy and commits its
properties only after the volume and visual updates both succeed. The atomicity
test and the three piloti clipping/idempotence tests passed 4/4 in 0.012
seconds.

The piloti tests independently assert:

- every rendered local vertex is at or above the void plane;
- every triangle has non-zero 3D area;
- every undirected mesh edge has exactly two incident triangles;
- an underside cap exists;
- the courtyard boundary produces two loops and cap area excludes the hole;
- source-surface provenance count is retained;
- projected count, visual hash, void fraction, and closed-mesh hard pass are
  rebound together;
- no serialized world-coordinate field remains;
- a repeated application is idempotent.

## Fresh Verification

```text
C:\Python313\python.exe manage.py test \
  design.test_maas_visual_authority \
  design.test_maas_preference -v 1
```

Result: 61/61 passed in 2.360 seconds.

```text
C:\Python313\python.exe manage.py test \
  design.test_maas_shared_floor_contract \
  design.test_maas_export.MaasLegalVariantsTest.test_piloti_subtraction_keeps_canonical_geometry_and_evidence_synchronized \
  design.test_maas_export.MaasLegalVariantsTest.test_final_floorwise_reprojection_is_idempotent_with_returned_authored_source \
  design.test_maas_export.MaasLegalVariantsTest.test_authored_source_registry_requires_unique_hash_bound_lineage_for_fallback -v 1
```

Result: 40/40 passed in 1.269 seconds.

```text
C:\Python313\python.exe manage.py test \
  design.test_maas_flow_regressions.MaasFlowRegressionTest.test_projected_visual_identity_survives_board_archive_and_elevation \
  design.test_maas_geometry_language.MaasGeometryLanguageTest.test_profiled_hall_macro_compiles_six_distinct_section_families \
  design.test_maas_geometry_language.MaasGeometryLanguageTest.test_profiled_hall_language_generates_twenty_four_distinct_bounded_variants -v 1
```

Result: 3/3 passed in 0.117 seconds.

`py_compile` passed for all round-2 production and test files. Exact-scope
`git diff --check` also passed.

## Separate Hash-Binding Finding

A broader 26-test flow/profiling probe exposed
`test_render_observation_rejects_fabricated_empty_visual_certificate` in the
parallel outcome-graph/hash-binding scope: an empty surface set with
`projected_surface_count=0` was accepted. This round-2 commit does not touch
that owned file. The failure was reported to the hash-binding review task.
