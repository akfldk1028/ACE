# Single-Authority Legal MASS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce ten diverse, law- and parking-checked MASS alternatives from
one `1/1 UnitBox`, with BaseVolume/BOOK/LLM authorship, floorwise legal
adaptation, capacity measurement, render and elevation all bound to one final
compiled solid.

**Architecture:** Convert the existing vertex-only host fitting into an
explicit Matrix4 program transform, append constant-per-floor CSG projection
nodes to the same authored GeometryProgram, and export the resulting
site-bound program directly as the one SourceMass authority. Make achieved
capacity, all six BaseVolume scopes and morphology caps a joint portfolio
feasibility problem rather than advisory labels.

**Tech Stack:** Python 3, Django test runner, Shapely, Manifold3D,
`GeometryProgram` typed AST, SciPy MILP, JSON evidence artifacts, matplotlib
PNG benchmark renderer.

## Global Constraints

- The sole primitive root is one normalized `1/1 UnitBox`.
- Every affine scale, placement, orientation, rotation and shear is an
  explicit row-major homogeneous 4x4 matrix multiplying column vectors.
- Topology-changing work remains typed CSG/macro language; `3/8` is three
  Matrix4-derived UnitBox cells joined by union.
- The six BOOK states are exactly `1/1`, `3/8`, `1/2`, `1/4`, `1/8`, `1/16`.
- Do not restore generic plan refit, continuous floor-matrix interpolation or
  a hidden area-only sibling.
- Render, GFA/FAR, legal, parking, selection, archive and elevation consume
  the same final compiled geometry hash.
- Requested-but-missed capacity labels are diagnostic only.
- A valid ten-card result has all six scopes; four achieved capacity bands
  balanced 2/2/3/3; stepped count 1-3 with one upper-band stepped candidate;
  roof and solid phenotype caps of 3; pairwise silhouette distance at least
  `0.10`; all ten legal/geometry/parking hard-pass.
- The declared search space remains available: `21,039,480` theoretical paths
  from 6 scopes, 3 orientations, 5 seeds, 11 chassis, 69 principles, 11
  variations, 7 programs and 4 capacity alternatives. Do not brute-force all
  paths; preserve the axes and use bounded stratified/QD exploration.
- Existing uncommitted changes in the shared `DK-BB` workspace belong to the
  ongoing MASS work. Preserve them, do not reset them, and do not create
  commits that accidentally capture unrelated edits.
- After every task, append evidence to
  `docs/ai-session-memory/MAAS_R293_V6_SOLID_ELEVATION_DELTA_20260728.md`.

---

### Task 1: Explicit Matrix4 Host Fit and Site-Bound Program Export

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Modify: `ARR/backend/design/maas/geometry_language/affine_matrix.py`
- Test: `ARR/backend/design/test_maas_unitbox_matrix.py`
- Test: `ARR/backend/design/test_maas_geometry_language.py`

**Interfaces:**
- Produces: `HostFitTransform` with
  `matrix4: Matrix4`, `inverse_matrix4: Matrix4`,
  `world_vertices: tuple[Point3, ...]`,
  `achieved_plan_area_m2: float`.
- Produces:
  `append_site_placement_matrix(program: GeometryProgram, fit:
  HostFitTransform) -> GeometryProgram`.
- Produces:
  `compile_site_bound_geometry_program_to_source_mass(program:
  GeometryProgram, legal_host: Polygon, *, name: str | None = None,
  volume_role: str = "recursive_solid_primary") -> SourceMass | None`.
- Preserves: `compile_geometry_program_to_source_mass()` public behavior for
  non-projected callers.

- [ ] **Step 1: Write failing Matrix4 equivalence tests**

Add tests that compile one non-axis-aligned `1/1 UnitBox + slab + rotate`
program, fit it to a rotated polygon, and assert:

```python
fit = derive_host_fit_transform(compilation, host)
placed = append_site_placement_matrix(program, fit)
recompiled = compile_geometry_program(placed)

self.assertEqual(recompiled.status, "compiled")
self.assertEqual(fit.matrix4[3], (0.0, 0.0, 0.0, 1.0))
self.assertLess(
    _maximum_vertex_delta(recompiled.vertices, fit.world_vertices),
    1e-7,
)
```

Also assert that the placed program still has exactly one canonical UnitBox
primitive and an appended `matrix4` node at the root.

- [ ] **Step 2: Run the tests and verify the intended failure**

Run:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_unitbox_matrix `
  design.test_maas_geometry_language -v 2
```

Expected failure: `derive_host_fit_transform` and
`append_site_placement_matrix` do not yet exist.

- [ ] **Step 3: Implement Matrix4 host fitting**

Refactor `_fit_vertices_to_host()` so every operation already performed on
vertices is represented by a composed matrix:

```python
matrix = compose_matrix4(
    translation_matrix4((-source_center.x, -source_center.y, -min_z)),
    rotation_matrix4((0.0, 0.0, -source_angle)),
    scale_matrix4((long_scale * factor, short_scale * factor, 1.0 / z_span)),
    rotation_matrix4((0.0, 0.0, target_angle)),
    translation_matrix4((target_center.x, target_center.y, 0.0)),
)
```

When target-area shrink or short-axis widening is selected, compose that
additional affine transform into the returned matrix instead of mutating only
the vertex list. Add a general affine 4x4 inverse helper that rejects singular
matrices and keeps the last row `[0, 0, 0, 1]`.

- [ ] **Step 4: Append the site matrix and export without a second fit**

`append_site_placement_matrix()` copies the program nodes, adds one transform
node consuming the old root, updates `root_id`, and stores the upstream
program hash and placement matrix in metadata.

`compile_site_bound_geometry_program_to_source_mass()` compiles the already
placed program, samples volume bands and surfaces from those exact vertices,
and verifies containment against `legal_host`. It must not perform another
principal-frame fit.

- [ ] **Step 5: Run focused tests**

Run the Task 1 command again. Expected: all tests pass and the old direct
bridge tests remain unchanged.

- [ ] **Step 6: Record Task 1 evidence**

Append the exact command, pass count, matrix node ID and maximum vertex delta
to the session memory file.

---

### Task 2: Constant-Band Legal CSG Projection on the Same AST

**Files:**
- Create:
  `ARR/backend/design/maas/geometry_language/floorwise_legal_program.py`
- Modify: `ARR/backend/design/maas/geometry_language/ast.py`
- Modify: `ARR/backend/design/maas/geometry_language/compiler.py`
- Modify: `ARR/backend/design/maas/geometry_language/__init__.py`
- Test: `ARR/backend/design/test_maas_floorwise_legal_program.py`

**Interfaces:**
- Consumes: site-bound `GeometryProgram` from Task 1.
- Produces:
  `FloorwiseLegalProgramResult(program: GeometryProgram,
  floor_matrices: tuple[Matrix4, ...], achieved_floor_areas_m2:
  tuple[float, ...], certificate: dict[str, Any])`.
- Produces:
  `append_floorwise_legal_projection(program: GeometryProgram, *,
  legal_sections: tuple[Polygon, ...], target_floor_areas_m2:
  tuple[float, ...], floor_capacity_plan_hash: str) ->
  FloorwiseLegalProgramResult | None`.

- [ ] **Step 1: Write failing floor-band tests**

Use a four-floor U-shaped authored program and shrinking legal sections.
Assert:

```python
result = append_floorwise_legal_projection(
    placed_program,
    legal_sections=sections,
    target_floor_areas_m2=(97.784, 97.784, 71.240, 48.898),
    floor_capacity_plan_hash="capacity-plan:test",
)
self.assertIsNotNone(result)
self.assertEqual(len(result.floor_matrices), 4)
self.assertEqual(
    [node.operator for node in result.program.nodes[-1:]],
    ["union"],
)
self.assertFalse(result.certificate["matrix_interpolation"])
```

Compile the result and assert every measured floor section is contained by its
matching legal section. Assert each band has one constant Matrix4 and no
continuous interpolation node or projected surface-only payload.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_floorwise_legal_program -v 2
```

Expected failure: module/function missing.

- [ ] **Step 3: Build the explicit floorwise program**

For every floor:

1. instance the existing canonical UnitBox through Matrix4 to form the
   horizontal band slab; do not add another primitive node;
2. add `intersection(authored_site_root, band_slab)`;
3. derive a fixed principal-frame Matrix4 from the authored band section to
   the requested floor area;
4. add a `matrix4` transform consuming that isolated band;
5. apply an execution-only typed `legal_section_clip` CSG/macro consuming the
   transformed band with polygon exterior, holes and Z-band parameters;
6. keep the program's total primitive-node count exactly one: the original
   normalized UnitBox.

Union the resulting bands. Serialize the floor index, capacity-plan hash,
target area, achieved area and matrix on the corresponding nodes.

- [ ] **Step 4: Measure the final compiled solid**

Recompile the union, section it at bounded lower/mid/upper samples per floor,
and derive `achieved_floor_areas_m2` from that result. The certificate
hard-passes only when all sampled sections are contained and all coordinates
are finite/manifold.

- [ ] **Step 5: Add shape-retention and no-hourglass regressions**

Compare the pre/post projection topological signatures:

- U void remains a void unless legal clipping makes it infeasible;
- `3/8` remains connected L-derived geometry;
- vertical walls within one band do not interpolate toward the next floor
  matrix;
- adjacent floors may form real horizontal steps.

- [ ] **Step 6: Run focused tests and record evidence**

Run the Task 2 test plus
`design.test_maas_geometry_language`. Record pass count, final program hash,
floor areas and containment certificate in session memory.

---

### Task 3: Candidate Generation Uses the Final Projected Program as Sole Authority

**Files:**
- Modify:
  `ARR/backend/design/maas/book_language/candidate_generation.py`
- Modify:
  `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Modify:
  `ARR/backend/design/maas/book_language/downstream_hard_gate.py`
- Test: `ARR/backend/design/test_maas_mass_stage.py`
- Test: `ARR/backend/design/test_maas_shared_floor_contract.py`
- Test: `ARR/backend/design/test_maas_book_language.py`

**Interfaces:**
- Consumes: `append_floorwise_legal_projection()` from Task 2.
- Produces: candidate `SourceMass` whose volumes, surfaces and geometry bridge
  all originate from the final projected program.
- Removes from selection authority:
  `stable_all_floor_section_intersection`,
  `floorwise_legal_sibling_evidence`, and diagnostic-only retry replacement.

- [ ] **Step 1: Replace tests that encode the old low-capacity authority**

Write failures asserting that `_materialize_directed_geometry()`:

```python
self.assertEqual(
    materialized.metadata["geometry_authority"],
    "final_floorwise_legal_geometry_program",
)
self.assertNotIn(
    "floorwise_legal_sibling_evidence",
    materialized.metadata,
)
self.assertEqual(
    materialized.metadata["geometry_authority"],
    "final_floorwise_legal_geometry_program",
)
```

Add an r293-shaped fixture whose floor legal caps are
`102.931, 102.931, 74.989, 51.471` and prove the materializer can exceed the
old constant-stack ceiling of `205.884 m2`. That fixture may assert its own
achieved area, but production must not reject another valid final solid merely
because it misses a requested capacity target; Task 4 classifies achieved
bands.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python ARR/backend/manage.py test `
  design.test_maas_mass_stage `
  design.test_maas_shared_floor_contract `
  design.test_maas_book_language -v 2
```

Expected: the old stable-host and sibling-authority assertions fail.

- [ ] **Step 3: Replace the stable-host branch**

In `_materialize_directed_geometry()`:

1. apply BOOK and program projections to the authored program;
2. derive and append its site placement Matrix4;
3. append the Task 2 floorwise legal projection;
4. compile the final site-bound program directly to SourceMass;
5. store the final program and final geometry hashes as authority;
6. keep authored program/geometry hashes only as upstream provenance.

Do not call `materialize_floorwise_legal_source()` for selectable candidates.
Do not copy sibling metadata onto an unrelated visible source.

- [ ] **Step 4: Recompute all downstream measurements**

Pass the final SourceMass unchanged into shared-floor, GFA/FAR, legal
containment, parking and geometry-retention gates. Assert each evidence bundle
records the same final geometry hash.

- [ ] **Step 5: Enforce fail-closed projection**

Return no candidate when:

- floor projection cannot materialize;
- legal containment fails;
- final program is empty/non-manifold;
- the final source exports fewer surfaces than the compiler's complete
  triangle payload;
- recomputing the actual SourceMass surface hash differs from the bound render
  payload hash;
- final source/hash differs between measurement and render payload.

Do not hard-reject a geometrically valid candidate only for requested floor
area shortfall. Preserve measured achieved areas and let Task 4 decide whether
the candidate satisfies a capacity band.

- [ ] **Step 6: Run focused tests and a three-candidate r293 diagnostic**

Run the Task 3 test set. Then invoke the existing benchmark in its smallest
deterministic/no-VLM mode for PNU `1168011800104170004`, target three, in a
new output directory. Record compile count, achieved FAR range and projection
failures in session memory before any ten-card run.

---

### Task 4: Achieved Capacity and Joint Ten-Card Portfolio Solver

**Files:**
- Modify:
  `ARR/backend/design/maas/book_language/candidate_analysis.py`
- Modify:
  `ARR/backend/design/maas/book_language/quality_diversity_archive.py`
- Modify:
  `ARR/backend/design/maas/book_language/portfolio_constraint_solver.py`
- Modify:
  `ARR/backend/design/maas/book_language/portfolio_selection.py`
- Modify:
  `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `ARR/backend/design/test_maas_book_language.py`

**Interfaces:**
- `capacity_alternative_key(candidate)` returns only the realized selectable
  band or `""`; it never falls back to the requested label.
- `solve_milp_compatible_subset()` accepts joint scope, capacity-count,
  stepped-count, upper-band-stepped and morphology-cap constraints.
- Selection returns an explicit infeasibility certificate instead of a
  cardinality-only fallback.

- [ ] **Step 1: Write failing realized-capacity tests**

Create one requested `maximum_feasible` candidate with achieved utilization
below its target and assert:

```python
self.assertEqual(_capacity_alternative_key(candidate), "")
self.assertFalse(_capacity_target_gate(candidate))
```

Create ten compatible candidates with capacity counts `4/2/2/2` and assert
the portfolio fails balance. Create a `3/3/2/2` set covering all six scopes
and assert it passes.

- [ ] **Step 2: Write failing joint-constraint tests**

Prove the solver:

- includes the sole valid `1/16` candidate by replacing a conflicting card;
- rejects four stepped candidates;
- rejects zero stepped candidates;
- requires one stepped candidate in `brief_target` or `maximum_feasible`;
- caps roof archetype and solid phenotype at three;
- never returns ten while silently dropping a required scope or band.

- [ ] **Step 3: Verify RED**

Run:

```powershell
python ARR/backend/manage.py test design.test_maas_book_language -v 2
```

- [ ] **Step 4: Make realized capacity a hard archive descriptor**

Remove requested-label fallback from candidate analysis, QD and board
ordering. A capacity miss remains searchable diagnostic evidence but cannot
enter measured capacity coverage.

- [ ] **Step 5: Solve all portfolio constraints jointly**

Express in one MILP:

- exactly ten selections;
- six scope lower bounds of one;
- four capacity-band lower bounds of two and upper bounds of three;
- stepped lower bound one and upper bound three;
- upper-band-stepped lower bound one;
- roof and solid phenotype upper bounds three;
- existing silhouette incompatibility edges.

If infeasible, return no completed board and serialize the unsatisfied
constraint names plus maximum achievable cardinality.

- [ ] **Step 6: Align final audit and selector caps**

Remove the selector default `max(4, target // 4)`. For target ten, the selector
and final audit both enforce three. Ensure diagnostic counters report achieved
capacity bands separately from requested alternatives.

- [ ] **Step 7: Run tests and record distribution evidence**

Run the Task 4 test set. Record selected scope counts, achieved capacity
counts, stepped/roof/phenotype counts and any MILP infeasibility certificate
in session memory.

---

### Task 5: Hash-Bound Replay, Cross-PNU Probes and PNG Acceptance

**Files:**
- Modify:
  `ARR/backend/design/maas/mass_product_evidence.py`
- Modify:
  `ARR/backend/design/maas/single_execution/pipeline.py`
- Modify:
  `ARR/backend/design/maas/agents/elevation_agent/runtime.py`
- Modify:
  `ARR/backend/tools/benchmark_maas_book_program_portfolios.py`
- Create:
  `ARR/backend/tools/verify_single_authority_mass_pnus.py`
- Test: `ARR/backend/design/test_maas_mass_product_evidence.py`
- Test: `ARR/backend/design/test_maas_single_execution.py`
- Test: `ARR/backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- One final geometry identity is exposed as
  `final_legal_geometry_hash` across portfolio, archive, single execution,
  render and elevation.
- The cross-PNU tool invokes one PNU per isolated benchmark directory and
  writes a combined JSON summary without reusing candidate caches as proof.
- The benchmark exposes `--diagnostic-target` for values 1-3 only. This mode
  is explicitly `diagnostic_only`, may not set portfolio-complete/final-pass,
  and must not weaken the exact-ten production contract.

- [ ] **Step 1: Write failing hash-identity tests**

Assert:

```python
hashes = {
    passport["final_legal_geometry_hash"],
    render["final_legal_geometry_hash"],
    elevation["final_legal_geometry_hash"],
    archive["final_legal_geometry_hash"],
}
self.assertEqual(len(hashes), 1)
```

Also assert authored upstream hashes remain present but cannot substitute for
the final hash.

- [ ] **Step 2: Verify RED and implement hash propagation**

Run the three Task 5 test modules, then propagate the final projected program
identity through mass evidence, single execution and elevation.

- [ ] **Step 3: Add the bounded PNU verification runner**

The runner accepts repeated `--pnu`, creates one unique output directory per
PNU, invokes the authoritative BOOK benchmark separately, and aggregates:

- final count;
- six-scope counts;
- four achieved-capacity counts;
- FAR range;
- stepped/roof/phenotype counts;
- law-graph evidence hash;
- parking requirement/layout status;
- final geometry hash agreement;
- PNG paths and pass/fail reasons.

Default strict PNUs:

```python
(
    "1168011800104170004",
    "1168011800104670003",
)
```

The optional third `1168011800104230007` is labeled diagnostic until parcel
provenance is complete.

Add a mutually isolated bounded probe interface:

```python
parser.add_argument(
    "--diagnostic-target",
    type=int,
    choices=(1, 2, 3),
    default=None,
)
```

When set, propagate the small target into candidate-generation/render limits,
mark every summary `diagnostic_only=true`, and suppress final portfolio pass
claims. Do not implement a general target below ten for production selection.

- [ ] **Step 4: Run three-candidate probes first**

For each strict PNU, run target three with VLM disabled and new output paths.
Inspect generated PNGs at original resolution. Stop the ten-card run if the
forms converge to generic stairs, lose the BOOK void/L/branch features, or
reintroduce hourglass interpolation.

- [ ] **Step 5: Run bounded ten-card acceptance**

Only after both probes pass, run target ten per strict PNU. Require:

- ten cards;
- six scopes;
- achieved capacity `2/2/3/3`;
- stepped 1-3 with one upper-band stepped;
- legal/geometry/parking 10/10;
- no silhouette pair under `0.10`;
- identical final hash across render/archive/elevation.

- [ ] **Step 6: Inspect and copy final PNG evidence**

Copy only the accepted contact sheets and final summary into
`docs/mass/` using run-specific filenames. Do not overwrite r293/v6 evidence.

- [ ] **Step 7: Run scoped regression and update memory**

Run all modified MAAS test modules, `python -m compileall` on modified backend
packages, and `git diff --check` on scoped files. Record exact pass/fail counts,
artifact paths, remaining caveats and the law/parking authority boundary in
session memory.

---

## Plan Self-Review

- Spec coverage: UnitBox/Matrix4, typed CSG, one final authority, achieved
  capacity, six scopes, balanced four bands, stepped cap, cross-PNU PNG,
  parking/law and hash identity each have an implementation task.
- Placeholder scan: no deferred implementation markers are present.
- Type consistency: Task 1 produces the placed program consumed by Task 2;
  Task 2 produces the projected program consumed by Task 3; Task 3 candidates
  supply realized measurements to Task 4; Task 5 consumes the final hash.
- Execution safety: the plan preserves the dirty shared workspace, uses new
  artifact directories, and requires a three-candidate probe before any long
  ten-card run.
