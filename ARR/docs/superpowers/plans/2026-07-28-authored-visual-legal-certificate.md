# Authored Visual Legal Certificate Implementation Plan

> **For agentic workers:** Execute inline in the current shared workspace. Do
> not use git worktrees, staging, commits, attributes, or long portfolio
> benchmarks for this task.

**Goal:** Certify the exact authored visual mesh independently of capacity,
carry that certificate through initial generation and typed VLM repair, and
reject any authored surface that escapes the height-dependent legal envelope.

**Architecture:** Add one capacity-free
`certify_authored_visual_mesh(source, legal_sections)` helper beside the
existing floorwise visual projection code. The helper preserves the exact
`SourceSurface` tuple and canonical visual hash, validates complete finite
nondegenerate closed geometry, and samples surface vertices, edge midpoints,
triangle centroids, and height-section intersections. Initial generation and
VLM repair call the same helper; downstream uses the same authored-surface
containment authority. Capacity sibling/shared-floor evidence remains
diagnostic and cannot create or modify the certificate.

**Tech Stack:** Python 3.13, Django `SimpleTestCase`, Shapely, existing
`SourceMass`/`SourceSurface` contracts and projected-visual archive serializer.

## Global Constraints

- Preserve exact authored surfaces and visual hash; do not transform or rebuild
  visible geometry from capacity targets.
- Missing, malformed, empty, nonfinite, degenerate, open, or legally escaping
  authored surfaces fail closed.
- Capacity evidence cannot authorize or mutate the visual certificate.
- Portfolio benchmark is read-only; do not run a long benchmark.
- Before any GREEN test execution, report `TASK8_READY_TO_FREEZE` to the parent.
- Do not stage or commit.

---

### Task 1: Real-path RED coverage

**Files:**
- Modify: `backend/design/test_maas_mass_stage.py`
- Modify only if required by the existing real repair fixture:
  `backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Exercises initial `_materialize_directed_geometry`, real archive serializer
  and validator, `_repair_exact_post_book_candidates_from_vlm`, elevation
  handoff identity, and downstream `_evaluate_candidate`.
- Expected certificate mode:
  `authored_visual_legal_validation`.

- [ ] Extend the sibling-unavailable initial-generation test through
  `_certified_projected_visual_artifact` and
  `validate_projected_visual_artifact`.
- [ ] Assert two capacity target plans retain byte-equivalent surface records,
  visual hash, and authored certificate payload fields.
- [ ] Extend the real typed-repair test through archive serialization and
  elevation identity.
- [ ] Add a legal-SourceVolume/surface-only-overhang downstream rejection.
- [ ] Add empty, malformed, nonfinite, degenerate, and open authored-surface
  failures.
- [ ] Run only the new tests and verify failures are caused by missing authored
  certification/surface containment.

### Task 2: Capacity-independent authored certification helper

**Files:**
- Modify: `backend/design/maas/geometry_language/floorwise_visual_projection.py`
- Modify: `backend/design/maas/geometry_language/projected_visual_contract.py`

**Interfaces:**
- Produce:
  `certify_authored_visual_mesh(source: SourceMass, legal_sections:
  Sequence[Polygon]) -> FloorwiseVisualProjection`.
- Certificate retains schema
  `arr.maas.floorwise_visual_projection.v1`, canonical frames/convention,
  exact authored visual hash/count, containment sample evidence, and
  `certification_mode=authored_visual_legal_validation`.

- [ ] Reuse the existing completeness, closed directed-edge topology, finite
  triangle, sample-point, and height-section helpers without applying matrices.
- [ ] Convert each authored local XY vertex to world XY using the source
  footprint centroid only for containment checks; return the original surfaces.
- [ ] Reject incomplete legal sections and every invalid or escaping surface.
- [ ] Update archive certificate validation to accept the canonical authored
  mode while keeping exact triangle payload/hash validation unchanged.

### Task 3: Generation, repair, and downstream integration

**Files:**
- Modify: `backend/design/maas/book_language/candidate_generation.py`
- Modify: `backend/design/maas/book_language/vlm_review.py`
- Modify: `backend/design/maas/book_language/downstream_hard_gate.py`

**Interfaces:**
- Candidate generation certifies immediately after authored materialization and
  before any capacity sibling result is consulted.
- VLM repair certifies the repaired authored source from generation-context
  legal sections before capacity/shared-floor evidence.
- Downstream rejects missing/failed authored certificates and independently
  checks the same exact surfaces against its height-dependent sections.

- [ ] Replace sibling-derived authored certificate fabrication with the shared
  helper result.
- [ ] Call the helper on both capacity-sibling success and unavailable paths.
- [ ] Call the same helper after repaired `SourceMass` materialization.
- [ ] Make helper failure reject candidate/repair without clipping.
- [ ] Add surface containment failure evidence to downstream legal failures;
  do not change volume thresholds or capacity advisory behavior.

### Task 4: Freeze handoff and verification

**Files:**
- Create:
  `.superpowers/sdd/2026-07-28-floorwise-legal-visual-mass/task-8-authored-visual-legal-certificate-report.md`

- [ ] Review the complete diff and send `TASK8_READY_TO_FREEZE` before GREEN.
- [ ] Run focused new tests.
- [ ] Run:
  `C:\Python313\python.exe manage.py test design.test_maas_mass_stage design.test_maas_book_language design.test_maas_shared_floor_contract design.test_maas_geometry_language design.test_maas_flow_regressions --verbosity 1`.
- [ ] Run task-scoped whitespace checks.
- [ ] Record RED/GREEN commands, changed files, broad results, exact authority
  semantics, and dirty-worktree concerns in the Task 8 report.
