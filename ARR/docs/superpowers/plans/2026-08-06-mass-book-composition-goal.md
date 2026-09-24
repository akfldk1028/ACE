# MASS BOOK Composition Goal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and verify exactly twenty trusted LLM-authored MASS alternatives selected from the full executable BOOK composition lattice, with no deterministic authorship fallback or stepped legal-projection collapse.

**Architecture:** BOOK composition creates a large typed path population from BaseVolume scope, orientation, operative, combination, aggregation, and case-study relations. The LLM authors and ranks ASTs from those paths. A continuous legal-envelope CSG preserves authored visible geometry while exact floor plates remain independent GFA authority; production gates then select only legal, parking-clean, capacity-`>=0.70`, visibly distinct final meshes.

**Tech Stack:** Django management commands, Python dataclasses/typed JSON ASTs, Shapely, manifold3d, Pillow renderer, existing MAAS BOOK and portfolio contracts.

## Global Constraints

- Selected lineage is `UnitBox -> BaseVolume -> one global 4x4 Matrix4 -> ordered BOOK operations -> CSG`.
- Exactly twenty final selected candidates must be trusted Codex/OAuth LLM-authored typed ASTs.
- Deterministic code may expand graph paths and certify law, parking, mesh, capacity, and diversity; it may not author or replace form.
- No pose fallback, per-floor recentering/scaling, morphology anchor, fallback relabeling, or capacity-derived visible section-loft.
- Final measured capacity utilization is at least `0.70` for every selected candidate.
- Diversity must pass in graph/topology space before BOOK and certified visible-mesh/combined-PNG space after legal projection.
- Exact law-derived floor plates remain GFA authority even when visible legal projection uses a continuous envelope.

---

### Task 1: Continuous Legal Envelope Mesh Builder

**Files:**
- Modify: `backend/design/maas/geometry_language/floorwise_section_loft.py`
- Test: `backend/design/test_maas_shared_floor_contract.py`

**Interfaces:**
- Consumes: ordered single-ring legal `Polygon` sections and output origin.
- Produces: `build_continuous_legal_envelope_mesh(...) -> ContinuousLegalEnvelopeMesh | failure`, containing world-frame vertices, triangles, legal-sample evidence, and closed-manifold evidence without `SourceSurface` substitution.

- [ ] Write a failing test with four shrinking/shifted rectangles asserting a closed manifold, continuous boundary sections, and zero internal horizontal terrace faces.
- [ ] Run the exact test and confirm failure because the builder does not exist.
- [ ] Extract the existing ring alignment, seam, triangulation, cap, and per-triangle legal checks into the new focused builder.
- [ ] Run the exact test and the existing floorwise section-loft topology tests.
- [ ] Add fail-closed tests for holes, MultiPolygon, disjoint seam, and concave interpolation outside legal authority.

### Task 2: Authored Mesh Intersection With Continuous Envelope

**Files:**
- Modify: `backend/design/maas/geometry_language/floorwise_profiled_legal_clip.py`
- Modify: `backend/design/maas/geometry_language/source_bridge.py`
- Test: `backend/design/test_task8a_profiled_legal_clip_topology.py`
- Test: `backend/design/test_task7b_authored_projection_identity.py`

**Interfaces:**
- Consumes: projected authored manifold plus Task 1 continuous legal envelope.
- Produces: certification mode `floorwise_profiled_continuous_envelope_clip` and operation `authored_profiled_mesh_continuous_legal_envelope_intersection`.

- [ ] Write a failing real-geometry test proving an authored oblique/void body clipped by shrinking legal sections has no band terrace and retains its authored carrier.
- [ ] Run the exact test and confirm the current per-floor `_legal_prism` intersection fails it.
- [ ] Replace per-band intersect/union with one authored-manifold/interpolated-envelope intersection.
- [ ] Keep existing numeric repair, component-volume, exact-surface-hash, legal sampling, and fail-closed behavior.
- [ ] Separate visible-mesh containment from capacity-plate equality; preserve occupied/legal binding hashes.
- [ ] Run Task 2 tests and the authored identity predicate suite.

### Task 3: Continuous Projection Certificate Contract

**Files:**
- Modify: `backend/design/maas/geometry_language/floorwise_visual_projection.py`
- Modify: `backend/design/maas/geometry_language/projected_visual_contract.py`
- Modify: `backend/design/maas/book_language/candidate_analysis.py`
- Modify: `backend/design/maas/book_language/candidate_generation.py`
- Modify: `backend/design/maas/program_massing/competition_gestalt.py`
- Test: `backend/design/test_task8a_profiled_legal_clip_topology.py`
- Test: `backend/design/test_task7c_authored_visual_authority.py`

**Interfaces:**
- Consumes: Task 2 certificate and exact authority hashes.
- Produces: transport/load/rebind validation that accepts only untampered continuous-envelope artifacts.

- [ ] Write failing tamper tests for legal WKB, section binding, surface hash, capacity hash, legal witness, and manifold evidence.
- [ ] Add the new certification mode to exact-authority allowlists without treating it as permission for `visible_stepped`.
- [ ] Require `capacity_authority=floorwise_legal_volumes` and `visible_capacity_relation=independent_contained_mask`.
- [ ] Run certificate, archive transport, authored identity, and renderer-authority tests.

### Task 4: Full BOOK Composition Lattice

**Files:**
- Create: `backend/design/maas/book_language/composition_lattice.py`
- Modify: `backend/design/maas/book_language/registry.py`
- Modify: `backend/design/maas/book_language/corpus_contract.py`
- Test: `backend/design/test_maas_book_language.py`

**Interfaces:**
- Consumes: six BaseVolume fractions, three orientations, thirty base operatives, bounded variants, combination contracts, aggregation contracts, and case-study relation paths.
- Produces: stable, content-addressed `BookCompositionPath` records and a lazily iterable lattice with provenance and compatibility evidence.

- [ ] Write failing tests proving the lattice contains thousands of unique executable paths and covers every source graph relation without materializing parcel coordinates or completed forms.
- [ ] Implement stable path identity across scope, orientation, ordered operations, graph edges, topology class, and parameters.
- [ ] Reject incompatible/self-referential compositions before LLM authoring while retaining failure evidence.
- [ ] Verify deterministic ordering and identical hashes across repeated runs.

### Task 5: LLM Authorship and Ranking From the Lattice

**Files:**
- Modify: `backend/design/maas/geometry_language/llm_adapter.py`
- Modify: `backend/design/maas/book_language/authorship_policy.py`
- Modify: `backend/design/maas/book_language/agent_authored_supply.py`
- Test: `backend/design/test_maas_geometry_language.py`
- Test: `backend/design/test_llm_author_request_outcomes.py`

**Interfaces:**
- Consumes: bounded slices of `BookCompositionPath`, program/site context, and typed production failure feedback.
- Produces: trusted typed GeometryProgram ASTs binding exact selected graph-path ids.

- [ ] Write failing tests proving the prompt carries exact path records rather than a one-language-per-output checklist.
- [ ] Require each authored AST to bind one supplied path and preserve its ordered graph topology.
- [ ] Add graph-distance batch admission so parameter-only duplicates are rejected before compilation.
- [ ] Replenish from underrepresented graph regions using terminal production evidence; never deterministic anchors.
- [ ] Verify Codex/OAuth manifest session, request, SHA-256, path hashes, and program hashes at admission.

### Task 6: Production Selection and End-to-End Evidence

**Files:**
- Modify: `backend/design/maas/book_language/portfolio_selection.py`
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `backend/design/maas/book_language/portfolio_witness.py`
- Test: `backend/design/test_maas_book_language.py`
- Test: `backend/design/test_mass_flow_rewiring_integration.py`

**Interfaces:**
- Consumes: legal/capacity-passing certified final meshes and their bound graph paths.
- Produces: selected target3/target20 portfolios, machine-readable completion evidence, combined PNG, and frontend graph/archive evidence.

- [ ] Write failing selection tests requiring both graph/topology and final silhouette compatibility.
- [ ] Run target3 through the exact production BOOK/program/legal/parking/capacity schedule; inspect every selected card and combined PNG.
- [ ] Feed measured failures back to Task 5 until target3 has three trusted, non-stepped, capacity-`>=0.70` selections.
- [ ] Run target20 without reduced gates or diagnostic fallback.
- [ ] Verify all twenty trusted LLM lineages, legal/parking/capacity/mesh gates, zero fallbacks, graph diversity, final mesh diversity, one combined PNG, and frontend display.
- [ ] Run the full relevant Django test modules, `python manage.py check`, artifact audit command, and direct PNG inspection before goal completion.

## Self-Review

- Coverage: continuous projection, independent GFA authority, full BOOK graph, LLM selection, trust admission, target3, target20, PNG, and frontend evidence are all assigned.
- Placeholder scan: no deferred implementation placeholders are used.
- Type consistency: Tasks 2-3 consume Task 1 mesh output; Task 5 consumes Task 4 paths; Task 6 consumes Tasks 3 and 5 evidence.
- Worktree safety: commits, if made, must stage only files belonging to the corresponding task because this is a shared dirty worktree.
