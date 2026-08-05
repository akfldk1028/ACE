# Symmetric Midpoint Weld Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, cumulative-displacement-bounded symmetric midpoint weld for canonical profiled-mesh `tiny_edge` failures, preserve the existing five-attempt contract, and prove unchanged downstream authority through focused tests and an r88 diagnostic run.

**Architecture:** Keep repair inside `profiled_mesh_numeric_repair.py`. A pure typed weld primitive operates on immutable original-vertex groups; `_collapse_edges_attempt` remains the fixed-point coordinator, prefers existing endpoint collapse, and invokes midpoint welding only when one-sided relocation cannot fit but both groups can fit the same attempt budget. Existing profiled clip, source bridge, candidate generation, compiler, law, parking, program, VLM, and selector paths remain authorities; only additive bounded evidence crosses those boundaries.

**Tech Stack:** Python 3, pytest with the existing unittest-style test module, immutable dataclasses, existing GeometryProgram compiler and `compilation_gate`, Shapely-backed floorwise clipping, JSON evidence artifacts, PowerShell, Git patch/index workflows.

## Global Constraints

- Per-original-vertex cumulative physical displacement cap is exactly `5e-7m`.
- Canonical `tiny_edge` means compact-coordinate edge length strictly `< GeometryGatePolicy().minimum_edge_length`, where the existing policy value is `1e-5`.
- The existing five thresholds remain exactly `(1e-8, 3e-8, 1e-7, 3e-7, 5e-7)` metres; no sixth attempt is added.
- Endpoint collapse has priority and remains the operation for edges whose one-sided cumulative relocation fits the active attempt budget.
- Symmetric midpoint weld is eligible only when endpoint collapse cannot fit and every original vertex in both representative groups can reach the midpoint within the active threshold and the absolute `5e-7m` cap.
- No threshold, law, program, parking, VLM, topology, manifold, watertight, component, containment, section-area, symmetric-difference, Hausdorff, self-intersection, or outward-normal relaxation is permitted.
- Every attempted repaired mesh must run the complete existing canonical compiler gate and authority revalidation chain.
- Fixed-point edge rebuilding and output must be deterministic across repeated runs and triangle order.
- All invalid, over-budget, non-finite, component-changing, structurally invalid, or incompletely certified states fail closed with typed evidence and no candidate fabrication.
- No family, PNU, site, BOOK principle, scope, candidate hash, or run-specific branch is permitted.
- Do not stage whole shared dirty files. Every commit requires a task-only patch, clean-worktree applicability check where dependency state permits, cached/index-only application, and staged-diff audit.
- If a task-only patch cannot apply to inner `HEAD` without unrelated prerequisite hunks, stop before staging or committing and report the exact dependency.

---

## Task 1: Add the typed symmetric weld primitive and cumulative group accounting

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py`
- Modify: `ARR/backend/design/test_task8a_profiled_legal_clip_topology.py`

**Interfaces:**
- Consumes: immutable raw vertices, two `_RepresentativeGroup` values, active threshold in metres, and `effective_height_m`.
- Produces: `_SymmetricWeldResult` containing either a merged `_RepresentativeGroup` plus applied evidence or no group plus a typed rejected `ProfiledMeshWeldOperation`.
- Adds: `Vertex3 = tuple[float, float, float]` and `Triangle3 = tuple[int, int, int]` internal aliases.
- Adds: `_RepresentativeGroup(representative_index: int, original_indices: tuple[int, ...], coordinate: Vertex3)`.
- Adds: `ProfiledMeshWeldOperation(operation_type: str, endpoint_indices: tuple[int, int], left_group_size: int, right_group_size: int, midpoint: Vertex3 | None, left_group_max_displacement_m: float, right_group_max_displacement_m: float, combined_group_max_displacement_m: float, compact_edge_length: float, physical_edge_length_m: float, status: str, rejection_code: str = "")`.
- Adds: `_SymmetricWeldResult(group: _RepresentativeGroup | None, operation: ProfiledMeshWeldOperation)`.
- Adds: `_physical_distance_m(left: Vertex3, right: Vertex3, *, effective_height_m: float) -> float`.
- Adds: `_group_max_displacement_m(raw_vertices: tuple[Vertex3, ...], original_indices: tuple[int, ...], coordinate: Vertex3, *, effective_height_m: float) -> float`.
- Adds: `_symmetric_midpoint_weld(raw_vertices: tuple[Vertex3, ...], left: _RepresentativeGroup, right: _RepresentativeGroup, *, threshold_m: float, effective_height_m: float) -> _SymmetricWeldResult`.

- [ ] **Step 1: Capture the pre-task state for hunk isolation**

Run from `D:\Data\25_ACE\ARR`:

```powershell
$taskRoot = 'D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task1'
New-Item -ItemType Directory -Force $taskRoot | Out-Null
Copy-Item backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py "$taskRoot/profiled_mesh_numeric_repair.before.py"
Copy-Item backend/design/test_task8a_profiled_legal_clip_topology.py "$taskRoot/test_task8a.before.py"
```

Expected: two immutable pre-task copies exist outside the inner repository; no index change.

- [ ] **Step 2: Write RED primitive tests**

Add these focused tests to `Task8AProfiledLegalClipTopologyTest` using the exact new interfaces:

```python
def test_symmetric_midpoint_weld_moves_both_singleton_groups_within_cap(self):
    raw = ((0.0, 0.0, 0.0), (8e-7, 0.0, 0.0))
    left = _RepresentativeGroup(0, (0,), raw[0])
    right = _RepresentativeGroup(1, (1,), raw[1])

    result = _symmetric_midpoint_weld(
        raw,
        left,
        right,
        threshold_m=5e-7,
        effective_height_m=1.0,
    )

    self.assertIsNotNone(result.group)
    self.assertEqual(result.group.representative_index, 0)
    self.assertEqual(result.group.original_indices, (0, 1))
    self.assertEqual(result.group.coordinate, (4e-7, 0.0, 0.0))
    self.assertEqual(result.operation.operation_type, "symmetric_midpoint_weld")
    self.assertEqual(result.operation.status, "applied")
    self.assertLessEqual(result.operation.left_group_max_displacement_m, 5e-7)
    self.assertLessEqual(result.operation.right_group_max_displacement_m, 5e-7)

def test_symmetric_midpoint_weld_rejects_cumulative_group_displacement(self):
    raw = ((0.0, 0.0, 0.0), (4e-7, 0.0, 0.0), (8e-7, 0.0, 0.0))
    left = _RepresentativeGroup(0, (0, 1), raw[1])
    right = _RepresentativeGroup(2, (2,), raw[2])

    result = _symmetric_midpoint_weld(
        raw,
        left,
        right,
        threshold_m=5e-7,
        effective_height_m=1.0,
    )

    self.assertIsNone(result.group)
    self.assertEqual(result.operation.status, "rejected")
    self.assertEqual(
        result.operation.rejection_code,
        "symmetric_weld_displacement_exceeded",
    )
    self.assertGreater(result.operation.left_group_max_displacement_m, 5e-7)

def test_symmetric_midpoint_weld_rejects_singleton_edge_over_two_caps(self):
    raw = ((0.0, 0.0, 0.0), (1.2e-6, 0.0, 0.0))
    result = _symmetric_midpoint_weld(
        raw,
        _RepresentativeGroup(0, (0,), raw[0]),
        _RepresentativeGroup(1, (1,), raw[1]),
        threshold_m=5e-7,
        effective_height_m=1.0,
    )

    self.assertIsNone(result.group)
    self.assertEqual(
        result.operation.rejection_code,
        "symmetric_weld_displacement_exceeded",
    )
    self.assertAlmostEqual(
        result.operation.combined_group_max_displacement_m,
        6e-7,
    )
```

Import `_RepresentativeGroup` and `_symmetric_midpoint_weld` from the production module. Do not mock distance calculations.

- [ ] **Step 3: Run RED primitive tests**

Run from `D:\Data\25_ACE\ARR\backend`:

```powershell
$env:DJANGO_SETTINGS_MODULEpython -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
```

Expected RED evidence: import failure for `_RepresentativeGroup` or `_symmetric_midpoint_weld`; zero tests pass accidentally through the existing endpoint-collapse implementation.

- [ ] **Step 4: Implement immutable group accounting and the pure weld**

Add the exact dataclasses and helpers. The core operation must follow this structure:

```python
def _symmetric_midpoint_weld(
    raw_vertices: tuple[Vertex3, ...],
    left: _RepresentativeGroup,
    right: _RepresentativeGroup,
    *,
    threshold_m: float,
    effective_height_m: float,
) -> _SymmetricWeldResult:
    retained, removed = sorted(
        (left, right),
        key=lambda group: (
            group.coordinate,
            min(group.original_indices),
        ),
    )
    midpoint = tuple(
        (left.coordinate[axis] + right.coordinate[axis]) / 2.0
        for axis in range(3)
    )
    left_max = _group_max_displacement_m(
        raw_vertices,
        left.original_indices,
        midpoint,
        effective_height_m=effective_height_m,
    )
    right_max = _group_max_displacement_m(
        raw_vertices,
        right.original_indices,
        midpoint,
        effective_height_m=effective_height_m,
    )
    allowed = min(float(threshold_m), MAXIMUM_CLEANUP_DISPLACEMENT_M)
    rejection = ""
    if not all(isfinite(value) for value in (*midpoint, left_max, right_max)):
        rejection = "symmetric_weld_nonfinite_midpoint"
    elif max(left_max, right_max) > allowed + 1e-12:
        rejection = (
            "symmetric_weld_displacement_exceeded"
            if max(left_max, right_max) > MAXIMUM_CLEANUP_DISPLACEMENT_M + 1e-12
            else "symmetric_weld_threshold_not_reached"
        )
    operation = ProfiledMeshWeldOperation(
        operation_type="symmetric_midpoint_weld",
        endpoint_indices=(left.representative_index, right.representative_index),
        left_group_size=len(left.original_indices),
        right_group_size=len(right.original_indices),
        midpoint=midpoint,
        left_group_max_displacement_m=left_max,
        right_group_max_displacement_m=right_max,
        combined_group_max_displacement_m=max(left_max, right_max),
        compact_edge_length=dist(left.coordinate, right.coordinate),
        physical_edge_length_m=_physical_distance_m(
            left.coordinate,
            right.coordinate,
            effective_height_m=effective_height_m,
        ),
        status="rejected" if rejection else "applied",
        rejection_code=rejection,
    )
    if rejection:
        return _SymmetricWeldResult(group=None, operation=operation)
    return _SymmetricWeldResult(
        group=_RepresentativeGroup(
            representative_index=retained.representative_index,
            original_indices=tuple(sorted(
                (*left.original_indices, *right.original_indices)
            )),
            coordinate=midpoint,
        ),
        operation=operation,
    )
```

Use `math.dist` or the existing equivalent for compact length. Validate `effective_height_m > 0` and return `symmetric_weld_nonfinite_midpoint` rather than raising or returning a partial group.

- [ ] **Step 5: Run GREEN primitive tests**

Run the exact command from Step 3.

Expected GREEN evidence: three tests pass; midpoint is exactly `(4e-7, 0.0, 0.0)`; cumulative and `>2cap` fixtures fail with `symmetric_weld_displacement_exceeded`.

- [ ] **Step 6: Independent Task 1 review gate**

Create a task-only patch against the captured files, then inspect it without staging:

```powershell
git diff --no-index -- "$taskRoot/profiled_mesh_numeric_repair.before.py" backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py > "$taskRoot/production.patch.raw"
git diff --no-index -- "$taskRoot/test_task8a.before.py" backend/design/test_task8a_profiled_legal_clip_topology.py > "$taskRoot/tests.patch.raw"
Select-String -Path "$taskRoot/*.patch.raw" -Pattern '5e-7|1e-5|symmetric_midpoint_weld|symmetric_weld_displacement_exceeded'
```

Expected review evidence: only typed primitive/group/test additions; no gate constant, law, parking, program, VLM, or unrelated candidate changes. A reviewer must explicitly approve cumulative displacement measured from immutable raw vertices before Task 2 starts.

- [ ] **Step 7: Commit Task 1 only if a dependency-complete task patch is safe**

Normalize the reviewed patch to inner-repo `a/backend/...` and `b/backend/...` paths, validate it in a temporary clean worktree, then apply the identical patch to the index only:

```powershell
git -C D:\Data\25_ACE\ARR apply --cached --check D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task1.patch
git -C D:\Data\25_ACE\ARR apply --cached D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task1.patch
git -C D:\Data\25_ACE\ARR diff --cached --check
git -C D:\Data\25_ACE\ARR diff --cached --name-only
git -C D:\Data\25_ACE\ARR commit -m "fix: add bounded symmetric midpoint weld"
```

Expected staged names: only the production repair module and focused test. If either file is absent from `HEAD` or the patch requires unrelated untracked/shared dependencies, do not stage or commit; record the dependency and continue only in the working tree after user approval.

---

## Task 2: Integrate canonical tiny-edge classification, endpoint priority, and fixed point

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py`
- Modify: `ARR/backend/design/test_task8a_profiled_legal_clip_topology.py`

**Interfaces:**
- Consumes: Task 1 `_RepresentativeGroup`, `_symmetric_midpoint_weld`, and `ProfiledMeshWeldOperation`.
- Preserves: `_collapse_edges_attempt(vertices: tuple[Vertex3, ...], triangles: tuple[Triangle3, ...], *, maximum_length: float, effective_height_m: float, fixed_point: bool = True) -> ProfiledMeshCollapseAttempt`.
- Adds: `_CanonicalTinyEdge(left: int, right: int, compact_length: float, physical_length_m: float)`.
- Adds: `_canonical_tiny_edges(groups: Mapping[int, _RepresentativeGroup], triangles: tuple[Triangle3, ...], *, effective_height_m: float, minimum_edge_length: float) -> tuple[_CanonicalTinyEdge, ...]`.
- Extends: `ProfiledMeshCollapseAttempt.operation_records: tuple[ProfiledMeshWeldOperation, ...] = ()`.
- Preserves: `revalidate_or_repair_profiled_mesh(...)` and its public revalidation return contract.

- [ ] **Step 1: Capture Task 2 pre-state**

```powershell
$taskRoot = 'D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task2'
New-Item -ItemType Directory -Force $taskRoot | Out-Null
Copy-Item backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py "$taskRoot/profiled_mesh_numeric_repair.before.py"
Copy-Item backend/design/test_task8a_profiled_legal_clip_topology.py "$taskRoot/test_task8a.before.py"
```

Expected: task-local snapshots only; no index change.

- [ ] **Step 2: Add a concrete closed beveled-box fixture**

Add this deterministic helper to the focused test module:

```python
def _closed_beveled_box_mesh(
    edge_length: float,
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, int, int], ...],
]:
    plan = (
        (0.0, 0.0),
        (edge_length, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    )
    count = len(plan)
    vertices = tuple(
        (x, y, z)
        for z in (0.0, 1.0)
        for x, y in plan
    )
    bottom = tuple((0, index + 1, index) for index in range(1, count - 1))
    top = tuple(
        (count, count + index, count + index + 1)
        for index in range(1, count - 1)
    )
    sides = tuple(
        triangle
        for index in range(count)
        for triangle in (
            (index, (index + 1) % count, count + (index + 1) % count),
            (index, count + (index + 1) % count, count + index),
        )
    )
    return vertices, tuple((*bottom, *top, *sides))
```

This fixture creates a closed prism with a removable tiny bevel and no site-specific data.

- [ ] **Step 3: Write RED canonical integration tests**

Add these tests:

```python
def test_canonical_tiny_edge_classifier_uses_policy_strictly_below(self):
    policy = GeometryGatePolicy()
    below, triangles = _closed_beveled_box_mesh(
        policy.minimum_edge_length * 0.08
    )
    at_limit, at_triangles = _closed_beveled_box_mesh(
        policy.minimum_edge_length
    )

    self.assertTrue(_canonical_tiny_edges_for_raw_mesh(
        below,
        triangles,
        effective_height_m=1.0,
    ))
    self.assertFalse(_canonical_tiny_edges_for_raw_mesh(
        at_limit,
        at_triangles,
        effective_height_m=1.0,
    ))

def test_endpoint_collapse_precedes_symmetric_weld_when_one_sided_fits(self):
    vertices, triangles = _closed_beveled_box_mesh(4e-7)
    attempt = _collapse_edges_attempt(
        vertices,
        triangles,
        maximum_length=5e-7,
        effective_height_m=1.0,
        fixed_point=True,
    )

    self.assertEqual(attempt.termination_reason, "completed")
    self.assertGreater(attempt.collapse_count, 0)
    self.assertTrue(attempt.operation_records)
    self.assertEqual(attempt.operation_records[0].operation_type, "endpoint_collapse")
    self.assertNotIn(
        "symmetric_midpoint_weld",
        [row.operation_type for row in attempt.operation_records],
    )

def test_symmetric_weld_repairs_closed_manifold_when_endpoint_cannot_fit(self):
    vertices, triangles = _closed_beveled_box_mesh(8e-7)
    result = revalidate_or_repair_profiled_mesh(
        vertices,
        triangles,
        effective_height_m=1.0,
    )

    self.assertTrue(result.hard_pass)
    selected = [row for row in result.attempt_records if row.selected_as_final]
    self.assertEqual(len(selected), 1)
    self.assertIn(
        "symmetric_midpoint_weld",
        [row.operation_type for row in selected[0].operation_records],
    )
    self.assertEqual(result.post_repair_gate_codes, ())
    self.assertEqual(result.raw_component_count, result.post_repair_component_count)

def test_fixed_point_symmetric_weld_is_triangle_order_independent(self):
    vertices, triangles = _closed_beveled_box_mesh(8e-7)
    forward = revalidate_or_repair_profiled_mesh(
        vertices,
        triangles,
        effective_height_m=1.0,
    )
    reverse = revalidate_or_repair_profiled_mesh(
        vertices,
        tuple(reversed(triangles)),
        effective_height_m=1.0,
    )

    self.assertEqual(forward.certified_vertices, reverse.certified_vertices)
    self.assertEqual(forward.certified_triangles, reverse.certified_triangles)
    self.assertEqual(forward.clean_indexed_mesh_hash, reverse.clean_indexed_mesh_hash)
    self.assertEqual(forward.evidence(), reverse.evidence())
```

Add `_canonical_tiny_edges_for_raw_mesh(...)` only as a thin testable production wrapper around `_canonical_tiny_edges`; it must construct singleton groups and use `GeometryGatePolicy().minimum_edge_length`.

- [ ] **Step 4: Run RED canonical tests**

```powershell
$env:DJANGO_SETTINGS_MODULEpython -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
```

Expected RED evidence: missing classifier/operation integration, absent `operation_records`, or the `8e-7` beveled mesh remains `tiny_edge`. Endpoint precedence and triangle-order determinism must not be satisfied by test-only labels.

- [ ] **Step 5: Implement canonical classification and fixed-point operation selection**

Use the real policy value:

```python
minimum_edge_length = GeometryGatePolicy().minimum_edge_length
tiny_edges = _canonical_tiny_edges(
    groups,
    representative_triangles,
    effective_height_m=effective_height_m,
    minimum_edge_length=minimum_edge_length,
)
```

Sort `_CanonicalTinyEdge` values by:

```python
(
    edge.compact_length,
    edge.physical_length_m,
    groups[edge.left].coordinate,
    groups[edge.right].coordinate,
    min(groups[edge.left].original_indices),
    min(groups[edge.right].original_indices),
)
```

For the first edge, evaluate deterministic one-sided endpoint targets first. Compute displacement from every immutable raw member to the proposed retained coordinate. If either orientation fits the active threshold and absolute cap, select the orientation by the existing representative order and emit `endpoint_collapse`. Only if neither orientation fits, call `_symmetric_midpoint_weld`.

After every applied operation, rebuild representative triangles and invoke `_canonical_tiny_edges` again. If midpoint exceeds only a lower threshold, record `symmetric_weld_threshold_not_reached` and end that attempt without a candidate mesh. If it exceeds the absolute cap, record `symmetric_weld_displacement_exceeded` and fail closed. Never return a partially mutated mesh from a rejected operation.

Keep all five attempts independent by rebuilding singleton groups from raw vertices inside each threshold iteration.

- [ ] **Step 6: Run GREEN canonical tests and existing fixed-point tests**

Run the Step 4 command, followed by:

```powershell
python manage.py test `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_public_revalidation_repairs_closed_manifold_chain_to_fixed_point `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_collapse_rebuilds_new_subthreshold_representative_edges `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_fixed_point_chain_collapse_is_deterministic_and_repeatable `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_real_collapse_uses_physical_xy_and_normalized_z_displacement `
  -v 2
```

Expected GREEN evidence: eight tests pass; endpoint precedence remains; `8e-7` uses symmetric midpoint; gate-clean output is deterministic; physical Z accounting remains unchanged.

- [ ] **Step 7: Independent Task 2 review gate**

Create and inspect task-only diffs against Step 1 snapshots. Reviewer checks must explicitly confirm:

- classifier imports `GeometryGatePolicy` rather than introducing another `1e-5` literal;
- all group displacement starts from immutable raw vertices;
- endpoint collapse is attempted before midpoint;
- edge set is rebuilt after each weld;
- rejected operations return no partial mesh;
- each threshold restarts from raw mesh;
- no gate or downstream file changed.

Run:

```powershell
git diff --no-index -- "$taskRoot/profiled_mesh_numeric_repair.before.py" backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py > "$taskRoot/production.patch.raw"
git diff --no-index -- "$taskRoot/test_task8a.before.py" backend/design/test_task8a_profiled_legal_clip_topology.py > "$taskRoot/tests.patch.raw"
Select-String -Path "$taskRoot/*.patch.raw" -Pattern 'GeometryGatePolicy|minimum_edge_length|endpoint_collapse|symmetric_midpoint_weld|fixed_point'
```

Expected: no threshold assignment, family string, PNU, BOOK principle, law, parking, program, VLM, or selector edit.

- [ ] **Step 8: Commit Task 2 with a reviewed index-only patch**

```powershell
git -C D:\Data\25_ACE\ARR apply --cached --check D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task2.patch
git -C D:\Data\25_ACE\ARR apply --cached D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task2.patch
git -C D:\Data\25_ACE\ARR diff --cached --check
git -C D:\Data\25_ACE\ARR diff --cached --name-only
git -C D:\Data\25_ACE\ARR commit -m "fix: align profiled repair with canonical tiny edges"
```

Expected staged names: only repair module and focused test. Stop without commit if clean `HEAD` cannot accept the exact patch.

---

## Task 3: Add v2 bounded witness and propagate it through terminal artifacts

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py`
- Modify: `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Modify: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Modify: `ARR/backend/design/test_task8a_profiled_legal_clip_topology.py`

**Interfaces:**
- Adds: `MESH_NUMERIC_REPAIR_SCHEMA_V2 = "arr.maas.profiled_mesh_numeric_repair.v2"` while retaining v1 reading.
- Adds: `ProfiledMeshWeldOperation.evidence() -> dict[str, Any]`.
- Extends: `ProfiledMeshCollapseAttempt.evidence() -> dict[str, Any]` with `operation_records`, `operation_record_count`, `operation_records_truncated`, and `operation_counts`.
- Preserves: maximum five attempt records and maximum 24 operation records per attempt.
- Preserves: source bridge terminal-failure and candidate-generation outcome interfaces; only their allowlisted sanitizer fields expand.
- Produces: bounded v2 evidence in profiled clip certificate, source bridge terminal sink, candidate report, failed `StageOutcome`, and outcome graph observation.

- [ ] **Step 1: Capture Task 3 pre-state**

```powershell
$taskRoot = 'D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task3'
New-Item -ItemType Directory -Force $taskRoot | Out-Null
Copy-Item backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py "$taskRoot/profiled_mesh_numeric_repair.before.py"
Copy-Item backend/design/maas/geometry_language/source_bridge.py "$taskRoot/source_bridge.before.py"
Copy-Item backend/design/maas/book_language/candidate_generation.py "$taskRoot/candidate_generation.before.py"
Copy-Item backend/design/test_task8a_profiled_legal_clip_topology.py "$taskRoot/test_task8a.before.py"
```

Expected: four task snapshots and no staged change.

- [ ] **Step 2: Write RED bounded evidence tests**

Add tests that construct 26 operation records, then assert exact v2 behavior:

```python
def test_symmetric_weld_v2_evidence_is_bounded_and_typed(self):
    operations = tuple(
        ProfiledMeshWeldOperation(
            operation_type="symmetric_midpoint_weld",
            endpoint_indices=(index, index + 1),
            left_group_size=1,
            right_group_size=1,
            midpoint=(index * 1e-8, 0.0, 0.0),
            left_group_max_displacement_m=4e-7,
            right_group_max_displacement_m=4e-7,
            combined_group_max_displacement_m=4e-7,
            compact_edge_length=8e-7,
            physical_edge_length_m=8e-7,
            status="applied" if index < 25 else "rejected",
            rejection_code=(
                "" if index < 25 else "symmetric_weld_displacement_exceeded"
            ),
        )
        for index in range(26)
    )
    attempt = ProfiledMeshCollapseAttempt(
        threshold_m=5e-7,
        collapse_count=25,
        termination_reason="completed",
        max_chain_displacement_m=4e-7,
        minimum_surviving_edge_physical_m=2e-5,
        minimum_surviving_edge_coordinate=2e-5,
        minimum_edge_endpoint_indices=(0, 1),
        minimum_edge_delta_xyz=(2e-5, 0.0, 0.0),
        operation_records=operations,
    )

    evidence = attempt.evidence()
    self.assertEqual(evidence["schema_version"], MESH_NUMERIC_REPAIR_SCHEMA_V2)
    self.assertEqual(len(evidence["operation_records"]), 24)
    self.assertEqual(evidence["operation_record_count"], 26)
    self.assertTrue(evidence["operation_records_truncated"])
    self.assertEqual(
        evidence["operation_counts"]["symmetric_midpoint_weld:applied"],
        25,
    )
    self.assertEqual(len(evidence["operation_records"][0]["midpoint"]), 3)

def test_symmetric_weld_rejection_survives_terminal_outcome_sanitizers(self):
    failure = _profiled_failure_with_symmetric_weld_evidence(
        rejection_code="symmetric_weld_displacement_exceeded"
    )
    propagated = _propagate_profiled_failure_through_production(failure)

    for evidence in propagated:
        operation = evidence["failure_witness"][
            "profiled_mesh_revalidation"
        ]["attempt_records"][-1]["operation_records"][-1]
        self.assertEqual(
            operation["rejection_code"],
            "symmetric_weld_displacement_exceeded",
        )
        self.assertEqual(operation["endpoint_indices"], [0, 1])
        self.assertEqual(len(operation["midpoint"]), 3)
        self.assertNotIn("secret", json.dumps(evidence).lower())
        self.assertNotIn("provider_body", json.dumps(evidence).lower())
```

Implement `_profiled_failure_with_symmetric_weld_evidence` and `_propagate_profiled_failure_through_production` as test helpers using the same existing source-bridge/candidate-generation production harness used by `test_five_attempt_records_survive_complete_failure_outcome_path`; do not manually fabricate final outcome-graph dictionaries.

- [ ] **Step 3: Run RED evidence tests**

```powershell
$env:DJANGO_SETTINGS_MODULEpython -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
```

Expected RED evidence: missing v2 schema/operation fields, more than 24 records, or sanitizer drops typed rejection before the outcome graph.

- [ ] **Step 4: Implement additive v2 serialization**

Implement the operation serializer with a fixed key set:

```python
def evidence(self) -> dict[str, Any]:
    return {
        "operation_type": self.operation_type,
        "endpoint_indices": list(self.endpoint_indices[:2]),
        "left_group_size": int(self.left_group_size),
        "right_group_size": int(self.right_group_size),
        "midpoint": (
            None if self.midpoint is None
            else [float(value) for value in self.midpoint]
        ),
        "left_group_max_displacement_m": float(
            self.left_group_max_displacement_m
        ),
        "right_group_max_displacement_m": float(
            self.right_group_max_displacement_m
        ),
        "combined_group_max_displacement_m": float(
            self.combined_group_max_displacement_m
        ),
        "compact_edge_length": float(self.compact_edge_length),
        "physical_edge_length_m": float(self.physical_edge_length_m),
        "status": self.status,
        "rejection_code": self.rejection_code,
    }
```

`ProfiledMeshCollapseAttempt.evidence()` must emit at most 24 operation dictionaries, total count, truncation boolean, and deterministic `operation_counts` sorted by `operation_type:status`. Emit v2 only when `operation_records` is present; retain current v1 shape for legacy endpoint-only evidence without operation records.

- [ ] **Step 5: Extend only existing allowlisted sanitizers**

In `source_bridge.py`, preserve only these nested operation fields:

```python
_SYMMETRIC_WELD_EVIDENCE_FIELDS = frozenset((
    "operation_type",
    "endpoint_indices",
    "left_group_size",
    "right_group_size",
    "midpoint",
    "left_group_max_displacement_m",
    "right_group_max_displacement_m",
    "combined_group_max_displacement_m",
    "compact_edge_length",
    "physical_edge_length_m",
    "status",
    "rejection_code",
))
```

Cap endpoint indices at two non-negative integers, midpoint at three finite numeric values, operation records at 24, attempts at the existing five, and strings at the existing terminal evidence limit. Preserve aggregate counts even when records are truncated.

In `candidate_generation.py`, extend the existing bounded terminal evidence copier rather than adding a second serializer. It must carry the already-sanitized `profiled_mesh_revalidation` mapping unchanged within existing depth/node limits. It must not copy arbitrary siblings from provider audit, candidate metadata, or failure payload.

- [ ] **Step 6: Run GREEN evidence tests and existing propagation regression**

Run Step 3, then:

```powershell
python manage.py test `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_revalidation_failure_evidence_reaches_profiled_clip_certificate `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_five_attempt_records_survive_complete_failure_outcome_path `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_midplane_mismatch_witness_survives_source_bridge_failure_evidence `
  design.test_task8a_profiled_legal_clip_topology.Task8AProfiledLegalClipTopologyTest.test_real_midplane_mismatch_witness_survives_production_propagation `
  -v 2
```

Expected GREEN evidence: six tests pass; v2 is additive and bounded; all five attempts and typed symmetric rejection survive the real terminal path; existing Hausdorff witness remains intact.

- [ ] **Step 7: Independent Task 3 security and causality review gate**

Review task-only diffs against snapshots. Reviewer must confirm:

- operation fields are fixed/allowlisted;
- evidence caps are 5 attempts and 24 operations per attempt;
- midpoint and displacement values require finite numerics;
- no arbitrary exception string, provider body, URL, secret, prompt, or candidate prose is serialized;
- truncation is diagnostic only;
- source bridge and candidate generation do not mutate provider/candidate audit objects;
- terminal behavior is unchanged.

Run:

```powershell
git diff --no-index -- "$taskRoot/source_bridge.before.py" backend/design/maas/geometry_language/source_bridge.py > "$taskRoot/source_bridge.patch.raw"
git diff --no-index -- "$taskRoot/candidate_generation.before.py" backend/design/maas/book_language/candidate_generation.py > "$taskRoot/candidate_generation.patch.raw"
Select-String -Path "$taskRoot/*.patch.raw" -Pattern 'operation_records|24|midpoint|rejection_code|deepcopy'
```

Expected: bounded propagation only; no selection, quota, provider, generation geometry, or VLM changes.

- [ ] **Step 8: Commit Task 3 with an exact reviewed patch**

```powershell
git -C D:\Data\25_ACE\ARR apply --cached --check D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task3.patch
git -C D:\Data\25_ACE\ARR apply --cached D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task3.patch
git -C D:\Data\25_ACE\ARR diff --cached --check
git -C D:\Data\25_ACE\ARR diff --cached --name-only
git -C D:\Data\25_ACE\ARR commit -m "fix: propagate bounded symmetric weld evidence"
```

Expected staged names: repair module, source bridge, candidate generation, and focused test only. Stop if any unrelated hunk appears.

---

## Task 4: Complete non-relaxation and full-authority regression coverage

**Files:**
- Modify: `ARR/backend/design/test_task8a_profiled_legal_clip_topology.py`
- Test without modification: `ARR/backend/design/test_maas_visual_authority.py`

**Interfaces:**
- Consumes: production repair, floorwise clip, source bridge, candidate generation, canonical compiler gate, and existing authority certificates.
- Produces: regression proof that clean symmetric welds still undergo component, structural, floor-section, containment, and Hausdorff authority.
- Does not modify production behavior.

- [ ] **Step 1: Capture the focused test pre-state**

```powershell
$taskRoot = 'D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task4'
New-Item -ItemType Directory -Force $taskRoot | Out-Null
Copy-Item backend/design/test_task8a_profiled_legal_clip_topology.py "$taskRoot/test_task8a.before.py"
```

Expected: one test snapshot; no source or index change.

- [ ] **Step 2: Write RED full-regression tests**

Add these focused cases using real compilation and existing floorwise helpers:

```python
def test_symmetric_weld_preserves_two_closed_components(self):
    left_vertices, left_triangles = _closed_beveled_box_mesh(8e-7)
    right_vertices, right_triangles = _translated_indexed_mesh(
        *_closed_beveled_box_mesh(2e-5),
        dx=2.0,
    )
    vertices, triangles = _join_indexed_meshes(
        (left_vertices, left_triangles),
        (right_vertices, right_triangles),
    )

    result = revalidate_or_repair_profiled_mesh(
        vertices,
        triangles,
        effective_height_m=1.0,
    )

    self.assertTrue(result.hard_pass)
    self.assertEqual(result.raw_component_count, 2)
    self.assertEqual(result.post_repair_component_count, 2)
    self.assertTrue(result.compilation.metrics["watertight"])
    self.assertTrue(result.compilation.metrics["manifold"])

def test_symmetric_weld_cannot_mask_tiny_face_or_component_loss(self):
    tiny_face = _closed_mesh_with_tiny_face_and_midpoint_edge()
    result = revalidate_or_repair_profiled_mesh(
        *tiny_face,
        effective_height_m=1.0,
    )

    self.assertFalse(result.hard_pass)
    self.assertIn("tiny_face", result.post_repair_gate_codes)
    self.assertIsNone(result.certified_vertices)
    self.assertIsNone(result.certified_triangles)

def test_canonical_clean_symmetric_weld_still_fails_hausdorff_terminally(self):
    terminal = _run_symmetric_weld_profiled_clip_with_section_offset(
        edge_length=8e-7,
        section_offset_m=2e-5,
    )

    self.assertEqual(
        terminal["failure_reason"],
        "profiled_legal_clip_midplane_topology_mismatch",
    )
    self.assertIn(
        "hausdorff_distance_exceeds_bound",
        terminal["failure_witness"]["failed_predicates"],
    )
    self.assertEqual(
        terminal["failure_witness"]["profiled_mesh_revalidation"][
            "post_repair_gate_codes"
        ],
        [],
    )
```

Implement `_translated_indexed_mesh`, `_join_indexed_meshes`, `_closed_mesh_with_tiny_face_and_midpoint_edge`, and `_run_symmetric_weld_profiled_clip_with_section_offset` as deterministic test helpers. Use the existing real floorwise clip/source bridge harness; no production gate result may be mocked.

- [ ] **Step 3: Run RED full-regression tests**

```powershell
$env:DJANGO_SETTINGS_MODULEpython -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
```

Expected RED evidence: missing helpers/asserted evidence, component mismatch, or failure witness not yet exercising the symmetric path. A test must not pass by bypassing canonical repair.

- [ ] **Step 4: Complete test fixtures without production changes**

Build fixtures from explicit indexed vertices/triangles and existing real authority functions. The tiny-face fixture must receive `tiny_face` from the real canonical gate. The Hausdorff fixture must show post-repair gate codes empty before the unchanged floor-midplane certificate rejects it.

If a RED test exposes a production defect outside the approved symmetric-weld contract, stop and report it. Do not expand production scope in this task.

- [ ] **Step 5: Run GREEN focused and adjacent suites**

```powershell
$env:DJANGO_SETTINGS_MODULE='config.settings'
python -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
python -m pytest backend/design/test_maas_visual_authority.py -q
```

Expected GREEN evidence: both suites pass. Capture exact test counts and runtime from Django output. Any unrelated broader failure is reported by exact test name and traceback without changing unrelated files.

- [ ] **Step 6: Run unchanged-threshold audit**

```powershell
rg -n "minimum_edge_length|MAXIMUM_CLEANUP_DISPLACEMENT_M|Hausdorff|hausdorff|containment|manifold|watertight|component" `
  backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py `
  backend/design/maas/geometry_language/gate.py `
  backend/design/maas/geometry_language/floorwise_profiled_legal_clip.py
```

Expected evidence: canonical minimum edge remains `1e-5`, cleanup cap remains `5e-7`, and downstream threshold definitions are unchanged from pre-task state.

- [ ] **Step 7: Independent Task 4 review gate**

```powershell
git diff --no-index -- "$taskRoot/test_task8a.before.py" backend/design/test_task8a_profiled_legal_clip_topology.py > "$taskRoot/tests.patch.raw"
git -C D:\Data\25_ACE\ARR diff --check
```

Reviewer confirms this task contains test helpers/assertions only, uses real gates, and does not weaken expectations to match implementation.

- [ ] **Step 8: Commit focused regression tests only**

```powershell
git -C D:\Data\25_ACE\ARR apply --cached --check D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task4.patch
git -C D:\Data\25_ACE\ARR apply --cached D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-task4.patch
git -C D:\Data\25_ACE\ARR diff --cached --check
git -C D:\Data\25_ACE\ARR diff --cached --name-only
git -C D:\Data\25_ACE\ARR commit -m "test: cover symmetric profiled mesh authority"
```

Expected staged name: only `backend/design/test_task8a_profiled_legal_clip_topology.py`. If the test file is untracked or dependency-incomplete relative to `HEAD`, do not commit a whole-file addition containing unrelated tests; report the dependency.

---

## Task 5: Run r88, audit measured acceptance, and record dated memory

**Files:**
- Create through benchmark: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r88/maas-book-programs-summary.json`
- Create through benchmark: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r88/maas-geometry-mutation-outcome-graph.json`
- Create through benchmark: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r88/maas-book-neighborhood-5.png`
- Create through benchmark: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r88/maas-book-neighborhood-5-witness.png`
- Create through benchmark: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r88/maas-book-programs-60-summary.png`
- Create through benchmark: `docs/playwright/design-route-live-verify/book-program-portfolios-legal-archive-target5-r88/maas-book-neighborhood-0-legal-archive.png`
- Create: `docs/superpowers/plans/2026-08-05-r88-symmetric-midpoint-weld-results.md`

**Interfaces:**
- Consumes: reviewed implementation and focused GREEN suites from Tasks 1-4.
- Produces: immutable r88 artifact directory and a dated evidence checkpoint.
- Does not alter source, tests, thresholds, provider behavior, or selection behavior in response to benchmark outcome.

- [ ] **Step 1: Confirm focused GREEN and clean task index before live execution**

```powershell
git -C D:\Data\25_ACE\ARR diff --cached --check
git -C D:\Data\25_ACE\ARR diff --cached --name-only
$env:DJANGO_SETTINGS_MODULE='config.settings'
python -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
python -m pytest backend/design/test_maas_visual_authority.py -q
```

Expected: focused suites pass; index is empty after prior commits or contains only an explicitly reviewed pending task patch. Do not run r88 against an ambiguous mixed implementation.

- [ ] **Step 2: Run the exact r88 diagnostic command once**

Run from `D:\Data\25_ACE\ARR\backend`:

```powershell
python manage.py benchmark_maas_book_program_portfolios `
  --pnu 1168011800104170004 `
  --program neighborhood `
  --recursive-only `
  --live-vlm `
  --live-llm-author `
  --progressive-target 5 `
  --output-dir D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r88
```

Expected: the command exits normally and may report an internal portfolio status of fail when fewer than five masses pass. Any process crash or nonzero command exit is an execution failure. Required evidence is a completed artifact set with explicit status, runtime, funnel, and no crash. Do not rerun merely to seek a better provider result.

- [ ] **Step 3: Extract exact r88 repair and funnel evidence**

Run this read-only audit:

```powershell
@'
import json
from collections import Counter
from pathlib import Path

root = Path(r"D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r88")
summary = json.loads((root / "maas-book-programs-summary.json").read_text(encoding="utf-8"))
graph = json.loads((root / "maas-geometry-mutation-outcome-graph.json").read_text(encoding="utf-8"))
program = summary["programs"][0]
counts = program["counts"]

raw_codes = Counter()
post_codes = Counter()
operations = Counter()
rejections = Counter()
clean_repairs = []
for observation in graph["observations"]:
    terminal = observation.get("terminal_materialization_evidence") or {}
    witness = terminal.get("failure_witness") or {}
    repair = witness.get("profiled_mesh_revalidation") or {}
    if not repair:
        continue
    raw_codes.update(repair.get("raw_gate_codes") or ())
    post_codes.update(repair.get("post_repair_gate_codes") or ())
    if repair.get("repair_attempted") and not repair.get("post_repair_gate_codes"):
        clean_repairs.append({
            "program_hash": observation.get("program_hash"),
            "family": observation.get("geometry_family"),
            "next_reason": terminal.get("failure_reason"),
        })
    for attempt in repair.get("attempt_records") or ():
        for operation in attempt.get("operation_records") or ():
            operations[operation.get("operation_type") or "missing"] += 1
            if operation.get("rejection_code"):
                rejections[operation["rejection_code"]] += 1

report = {
    "runtime_seconds": program.get("duration_seconds"),
    "status": program.get("status"),
    "selected_count": program.get("selected_count"),
    "evaluated": counts.get("evaluated"),
    "compiled": counts.get("compiled"),
    "materialization_invocations": counts.get("materialization_invocation_count"),
    "clean": counts.get("clean"),
    "program_passed": counts.get("program_passed"),
    "combined_hard_pass": (counts.get("preselection_hard_gate") or {}).get("combined_hard_pass_count"),
    "final_vlm_hard_pass": (counts.get("initial_final_book_vlm_gate") or {}).get("hard_pass_count"),
    "final_selection_pool": counts.get("final_hard_pass_selection_pool_count"),
    "raw_codes": dict(raw_codes),
    "post_codes": dict(post_codes),
    "operations": dict(operations),
    "rejections": dict(rejections),
    "clean_repairs": clean_repairs,
    "paid_provider_budget": summary.get("paid_provider_budget"),
}
print(json.dumps(report, indent=2, sort_keys=True))
'@ | python -
```

Expected evidence: exact measured values, operation/rejection histograms, and immediate next reason for every canonical-clean repaired observation. No expected count is hardcoded except that all values must reconcile with artifact records.

- [ ] **Step 4: Verify r88 PNG artifact existence and hashes**

```powershell
$root = 'D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r88'
$pngs = Get-ChildItem -LiteralPath $root -Filter '*.png' -File
$pngs | Select-Object FullName,Length
$pngs | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash
```

Expected: the MASS board `maas-book-neighborhood-5.png` exists with nonzero length; every PNG actually emitted by the benchmark has a recorded SHA-256 hash. This is artifact integrity evidence, not visual-quality acceptance.

- [ ] **Step 5: Write the dated r88 memory checkpoint**

Create `D:\Data\25_ACE\docs\superpowers\plans\2026-08-05-r88-symmetric-midpoint-weld-results.md` with these exact sections:

```markdown
# r88 Symmetric Midpoint Weld Results

**Date:** 2026-08-05

## Command and runtime
## Unchanged constraints
## Funnel compared with r87
## Raw/post gate-code histograms
## Endpoint and symmetric operation counts
## Typed rejection histogram
## Canonical-clean repairs and immediate downstream outcomes
## Component/manifold/watertight evidence
## Provider cache, paid request, 429, and cooldown context
## Absolute PNG paths and SHA-256 hashes
## Acceptance decision
## Explicit non-claims
```

Populate every section with extracted values. State explicitly that r88 may remain `1/5`, and make no `5/5` or competition-grade claim unless the artifacts independently prove it.

- [ ] **Step 6: Independent r88 review gate**

A reviewer compares the memory checkpoint directly with both r88 JSON artifacts and checks:

- funnel numbers reconcile;
- raw/post histograms reconcile with observations;
- all v2 attempts have at most five attempts and 24 operation records each;
- every clean repair names its immediate next authority result;
- component and structural gates remain enforced;
- provider credit/cache context is factual;
- all PNG paths and hashes are exact;
- no success claim exceeds measured evidence.

Expected review result: approved evidence checkpoint or exact corrections before commit. Do not modify production code based on r88 during this task.

- [ ] **Step 7: Commit only the reviewed dated memory file**

If `D:\Data\25_ACE` is an outer Git repository, stage only the new checkpoint path and inspect it:

```powershell
git -C D:\Data\25_ACE add -- docs/superpowers/plans/2026-08-05-r88-symmetric-midpoint-weld-results.md
git -C D:\Data\25_ACE diff --cached --check
git -C D:\Data\25_ACE diff --cached --name-only
git -C D:\Data\25_ACE commit -m "docs: record r88 symmetric weld evidence"
```

Expected staged name: only the dated r88 memory file. Do not stage generated PNG/JSON artifacts, shared dirty files, source, tests, or earlier context documents unless separately approved.

---

## Task 6: Final dependency-complete safe-commit and rollback audit

**Files:**
- Audit: `ARR/backend/design/maas/geometry_language/profiled_mesh_numeric_repair.py`
- Audit: `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Audit: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Audit: `ARR/backend/design/test_task8a_profiled_legal_clip_topology.py`
- Audit without modification: `ARR/backend/design/maas/geometry_language/gate.py`
- Audit without modification: `ARR/backend/design/maas/geometry_language/floorwise_profiled_legal_clip.py`

**Interfaces:**
- Consumes: all reviewed task commits or pending task-only patches and r88 evidence.
- Produces: a dependency-complete commit inventory, rollback instructions, and explicit unresolved-overlap report if clean staging is impossible.
- Does not add implementation behavior.

- [ ] **Step 1: Audit final inner commit and working-tree scope**

```powershell
git -C D:\Data\25_ACE\ARR status --short
git -C D:\Data\25_ACE\ARR log -6 --oneline
git -C D:\Data\25_ACE\ARR show --stat --oneline HEAD
git -C D:\Data\25_ACE\ARR diff --cached --check
```

Expected: every symmetric-weld commit lists only approved files/hunks. Existing unrelated dirty files remain untouched.

- [ ] **Step 2: Validate the combined task patch against a temporary clean worktree**

Build a combined patch from the reviewed Task 1-4 patches, then:

```powershell
$temp = 'D:\Data\25_ACE\.superpowers\worktrees\symmetric-midpoint-weld-clean'
git -C D:\Data\25_ACE\ARR worktree add --detach $temp HEAD
git -C $temp apply --check D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-combined.patch
git -C $temp apply D:\Data\25_ACE\.superpowers\sdd\symmetric-midpoint-weld-combined.patch
Set-Location "$temp\backend"
$env:DJANGO_SETTINGS_MODULE='config.settings'
python -m pytest backend/design/test_task8a_profiled_legal_clip_topology.py -q
python -m pytest backend/design/test_maas_visual_authority.py -q
```

Expected: patch applies and focused suites pass from clean `HEAD`. If it cannot apply because approved dependencies are not in `HEAD`, stop and list exact missing files/hunks. Do not absorb unrelated dirty work into the task commit.

- [ ] **Step 3: Record rollback behavior**

Confirm rollback consists only of reverting symmetric operation selection while retaining endpoint collapse, five thresholds, v1/v2 readers, historical evidence, and every canonical/downstream gate. Record the exact task commit hashes in the r88 memory checkpoint under `Acceptance decision`.

Expected: no database migration, artifact rewrite, or threshold edit is required for rollback.

- [ ] **Step 4: Remove the temporary worktree safely**

After tests and patch inspection complete:

```powershell
Set-Location D:\Data\25_ACE
git -C D:\Data\25_ACE\ARR worktree remove D:\Data\25_ACE\.superpowers\worktrees\symmetric-midpoint-weld-clean
git -C D:\Data\25_ACE\ARR worktree prune
```

Expected: temporary worktree is removed; main shared working tree remains unchanged beyond approved task work.

- [ ] **Step 5: Final independent review decision**

The final reviewer must issue one of two explicit decisions:

```text
APPROVED: dependency-complete symmetric midpoint weld task commits are isolated,
focused suites are green, r88 evidence is truthful, and rollback is bounded.
```

```text
BLOCKED: exact prerequisite files/hunks are not in HEAD or staged scope contains
unrelated work; no unsafe commit was made.
```

Expected: no ambiguous partial approval and no claim of `5/5` or competition-grade success.
