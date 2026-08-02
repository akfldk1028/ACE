# Creative Authored 100 MASS Preview Implementation Plan

> **Goal:** Produce a bounded 100-candidate architectural MASS choice pool for the frontend graph. The pool must preserve authored form diversity, expose real storey/capacity evidence, and never present pre-legal candidates as legal approvals.

## Product contract

- The output is a **choice pool**, not the final automatic winner set.
- Each candidate starts at the canonical `1/1 UnitBox`, derives its working scope through Matrix4, applies typed BOOK/architectural relations, and remains traceable as a graph.
- The pool contains 100 distinct compiled meshes across at least ten architectural families.
- One MASS may contain wings, courts, bridges, or cuts, but occupied parts must have an intentional contact, hub, spine, bridge, or core relationship. Accidental disconnected solids are rejected.
- Capacity is stratified across `spatial_reserve`, `balanced_yield`, `brief_target`, and `maximum_feasible`; maximum capacity is not the universal objective.
- Storeys are explicit evidence. Every row records floor count, floor elevations, measured/estimated occupied floor areas, target GFA, and capacity band.
- The fast preview performs no paid VLM call. Legal status is `not_evaluated` until the Neo4j/law-agent and exact geometry gates run.
- Outputs live under `docs/mass/<run-id>/`:
  - one 100-card board PNG;
  - one PNG per candidate;
  - one portfolio JSON;
- one candidate JSON per candidate containing GeometryProgram, Matrix4 trace, vertices, triangles, hashes, storey/capacity evidence, connectivity evidence, and legal-review state.

The `docs/mass` portfolio is a portable graph-facing artifact. The current
frontend does not discover arbitrary `docs/mass` JSON directly; it currently
loads only the executed-archive manifest and shows at most 24 recent cards.
Live 100-card selection therefore needs the adapter work recorded in Task 4.

## Root cause being isolated

The law does not require every MASS to become stepped. Current survivor bias is caused by:

1. non-uniform legal floors bypassing whole-authored affine placement;
2. generic floorwise replay converting the source into per-floor extrusions;
3. the legal visual clip accepting only a single exterior ring, which structurally disadvantages courtyard holes and split-wing multi-polygons.

The creative 100 preview therefore remains upstream of this destructive fallback. It is not a substitute for legal certification; it is the authored input pool that the legal agent must preserve or reject.

## Task 1: Add the creative portfolio contract

**Files**

- Create: `ARR/backend/design/maas/creative_floor_portfolio.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio.py`

**TDD assertions**

1. A deterministic request for 100 returns exactly 100 unique program and geometry hashes.
2. Ten named families each contribute ten candidates.
3. Four capacity bands are all present and none exceeds its quota.
4. Stepped candidates occupy at most one family quota.
5. Every program contains exactly one canonical UnitBox authority and at least one derived Matrix4 node.
6. Every compiled mesh passes connected, watertight, and manifold checks.
7. Every candidate has 3 or more explicit storeys and positive floor-area/GFA evidence.
8. Every split/radial/courtyard-like relation has a typed contact witness such as `hub`, `spine`, `bridge`, `core`, or `shared_edge`.
9. Legal review is explicitly `not_evaluated`, never `passed`.

**Implementation**

- Reuse the focused family contracts and shared geometry compiler.
- Expand the stable family lattice through deterministic variation indices rather than appending branches to `candidate_generation.py`.
- Assign capacity bands round-robin before geometry sampling.
- Derive storey count and floor elevations from the candidate height/capacity contract.
- Measure horizontal occupied sections where possible; fail closed if a candidate cannot provide architectural floor evidence.
- Persist the graph-facing lineage:
  `UnitBox -> derived scope Matrix4 -> BOOK relation -> connected MASS -> storey contract -> legal review pending`.

## Task 2: Add bounded rendering and persistence

**Files**

- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`
- Create: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio.py`

**TDD assertions**

1. The command rejects counts outside 1..100.
2. A small command run writes board, individual PNG, portfolio JSON, and candidate JSON.
3. Candidate JSON contains full vertices, triangles, Matrix4 trace, floor evidence, contact evidence, and legal status.
4. The portfolio JSON contains frontend graph nodes/edges and filter facets for family, capacity band, storeys, and legal status.
5. Paid image/VLM request count is zero.

**Implementation**

- Compile and render once per candidate.
- Use a compact 10-column contact sheet for the 100-card overview.
- Draw floor lines and labels from the same storey evidence saved in JSON.
- Write artifacts atomically under a new timestamped `docs/mass` directory.
- Keep the command bounded: no recursive replenishment loop and no paid provider call.

## Task 3: Generate and inspect the 100-candidate pool

**Run**

```powershell
cd ARR/backend
python manage.py generate_maas_creative_100 `
  --count 100 `
  --pnu 1168011800104170004 `
  --output-root D:\Data\25_ACE\docs\mass
```

**Verification**

- Exactly 100 cards and 100 candidate JSON files.
- Exactly ten family quotas of ten.
- Four capacity bands represented approximately evenly.
- No duplicate program/geometry hash.
- No disconnected or non-manifold result.
- At least three non-stepped body families are visibly distinct from one another.
- Storey evidence and Matrix4/mesh arrays exist for all 100.
- Board and a representative family sample are visually inspected.

## Task 4: Preserve the pool through legal projection

This is subsequent certification work, not a prerequisite for showing the authored 100 pool.

- Introduce a relation-late legal projector:
  `legal floor Matrix4 -> typed relation/CSG -> post-CSG GFA and containment certificate`.
- Permit floorwise rebuilding only for intentionally stepped authorship.
- For non-stepped authorship, preservation failure rejects the candidate instead of silently rewriting it.
- Add topology-aware handling for holes and connected multi-wing sections.
- Send certified survivors back to the same frontend graph with law-agent/Neo4j evidence and unchanged program/capacity/visual hashes.

## Task 4b: Connect the 100-card choice pool to the frontend

- Add an executed-archive source adapter for the creative portfolio run instead
  of pretending that an arbitrary portfolio JSON is already discoverable.
- Preserve the archive identity tuple `run_id/index/program_hash/geometry_hash`.
- Emit a `geometry_portfolio` node and `member_of` edges using the established
  outcome-graph schema.
- Paginate or virtualize the current 24-card rail so all 100 candidates remain
  selectable.
- Pass family, capacity band, storeys, and legal status through the compact
  outcome-graph allowlist and expose them as filters.
- Keep pre-legal passports pending; never materialize site/law/parking as
  evaluated before the specialist agents have actually run.

## Task 5: Session continuity

- Update `docs/ai-session-memory/MAAS_COMPETITION20_ACTIVE_20260729.md`.
- Update `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`.
- Record the exact run directory, verification counts, known uncertified status, and next legal-projection task so another session does not rerun the old stepped-only loop.
