# Competition-Grade 20-MASS Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a fast, fail-closed, legally certified 20-card MASS board whose final meshes retain genuinely different architectural languages.

**Architecture:** Preserve authored geometry with a single legal site Matrix4 whenever its measured floor sections are valid, reserve floorwise legal CSG for intentionally stepped alternatives, and select the final board with one quota-aware solver. A breadth-first cheap screen samples the existing UnitBox/BaseVolume/BOOK combinatorial lattice before bounded exact CSG, so runtime grows with useful legal diversity rather than the full Cartesian product.

**Tech Stack:** Python 3, Django management commands/tests, Shapely, NumPy/SciPy MILP, the existing typed GeometryProgram compiler, Neo4j law evidence, Pillow/archive renderer, React/Vite frontend.

## Global Constraints

- The canonical primitive is exactly one `box(width=1.0, depth=1.0, height=1.0)`.
- Affine placement uses Matrix4; non-affine form operations use existing typed CSG/macros.
- Do not lower legal, parking, program, capacity, manifold, watertight, containment, or hash gates.
- Do not use `surfaces=()` or a proxy mesh to erase the authored visible form.
- Target 20 is the product contract; target 3 is diagnostic only.
- Ordinary MASS storey count is arbitrary lawful `N`; do not let historical
  catalog hints or program target ranges cap PNU-derived capacity.
- Stop on certified actual cumulative GFA at the selected FAR/GFA target and
  fail if lawful height is exhausted first. Meet residual area through
  authored/form-preserving parameters; generic terminal-floor trimming is
  forbidden except for intentional stepped/terraced typed languages.
- Exact target-20 quotas and distance floors come from `docs/superpowers/specs/2026-07-29-competition-grade-20-mass-portfolio-design.md`.
- Selection is fail-closed and returns typed deficits; it never fills a board by relaxing caps.
- AST-valid `unknown_bounds` records may use quota-protected
  `exact_required` slots inside the same 64-candidate exact cap. They remain
  cheap failures and receive no legal/capacity authority until exact gates
  pass; invalid ASTs and known cheap failures are excluded.
- Write a failing test and observe the expected failure before every production change.
- Preserve unrelated dirty-worktree changes and stage only task-owned paths if commits are safe.

---

### Task 0: PNU Legal-Floor Field and Candidate-Specific GFA Stop

**Files:**
- Create: `ARR/backend/design/maas/book_language/legal_floor_field.py`
- Create: `ARR/backend/design/maas/book_language/actual_gfa_stop_certificate.py`
- Modify: `ARR/backend/design/maas/book_language/floor_capacity_plan.py`
- Modify: `ARR/backend/design/maas/book_language/capacity_contract.py`
- Modify: `ARR/backend/design/maas/book_language/capacity_alternatives.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Modify after Task 4 review: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Test: `ARR/backend/design/test_maas_floor_capacity_stop.py`
- Test: `ARR/backend/design/test_maas_actual_gfa_stop_certificate.py`

**Interfaces:**
- One target-independent `legal_floor_field_hash` covers the resolved PNU,
  legal height, all viable floor sections, BCR/FAR, and section capacities.
- Each candidate receives its own provisional target/N materialization and a
  final-mesh `candidate_actual_gfa_stop_hash`.

- [ ] **Step 1: Remove program-range floor authority**

Prove ordinary 1, 3, 7, 23, and 20+ floor cases are controlled by the PNU
height/section field, while explicit clear-span dimensional programs retain
their hard invariant. `target_floor_range` and legacy catalog values remain
reporting/scoring preferences only.

- [ ] **Step 2: Materialize and seal the shared legal field**

Enumerate all viable PNU floor sections through legal height. Bind the exact
resolved PNU and internally recalculate section areas, capacities, height
cadence, feasible GFA, and statutory-FAR reachability before accepting the
hash. Candidate target, candidate floor count, and geometry identity must not
change this shared hash.

- [ ] **Step 3: Certify the candidate's actual stop**

From final certified-mesh floor areas and containment rows, find the first
floor where cumulative actual GFA reaches the candidate target. Reject
positive occupiable floors above that point, missing/forged identity,
non-finite data, containment failure, legal-field tampering, target shortfall,
and uncorrected overshoot. The certificate never mutates geometry.

- [ ] **Step 4: Materialize candidate-specific N before exact geometry**

For each capacity alternative, choose the minimum legal prefix capable of its
target and distribute the target across that prefix. Truncate candidate
height, legal hosts, and target arrays to that `N`; keep the full shared legal
field unchanged. Meet residual area through authored/form-preserving
parameters. Generic terminal trimming is forbidden.

- [ ] **Step 5: Bind exact output and publish evidence**

After authored preservation or intentional stepped projection, derive actual
floor areas from the final mesh, build the stop certificate, and bind its hash
through capacity evidence, archive/passport, selection, and elevation. The
publishable portfolio shares one legal-field hash but may contain different
candidate floor counts.

---

### Task 1: Unified Target-Aware Portfolio Contract

**Files:**
- Create: `ARR/backend/design/maas/book_language/competition_portfolio_contract.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_constraint_solver.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_selection.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `ARR/backend/design/test_maas_book_language.py`

**Interfaces:**
- Produces: `CompetitionPortfolioContract`, `competition_portfolio_contract(target_count: int)`, and solver evidence `portfolio_contract_deficits`.
- Consumes: existing measured candidate facts, compatibility matrix, BaseVolume scope, capacity band, phenotype, roof, chassis, and plan-family descriptors.

- [ ] **Step 1: Write failing contract tests**

Add tests that assert:

```python
contract = competition_portfolio_contract(20)
self.assertEqual(contract.target_count, 20)
self.assertEqual(contract.capacity_band_exact_counts, {
    "spatial_reserve": 5,
    "balanced_yield": 5,
    "brief_target": 5,
    "maximum_feasible": 5,
})
self.assertEqual(contract.visible_stepped_minimum, 1)
self.assertEqual(contract.visible_stepped_maximum, 3)
self.assertEqual(contract.body_phenotype_minimum_distinct, 5)
self.assertEqual(contract.body_phenotype_maximum_each, 4)
self.assertEqual(contract.roof_archetype_minimum_distinct, 7)
self.assertEqual(contract.roof_archetype_maximum_each, 3)
```

Add a target-three fixture with three legal candidates where two are stepped;
assert the unified solver returns no selection and a
`visible_stepped:max_1` deficit. Add a target-20 balanced fixture that selects
exactly 20, then mutate one capacity band to four cards and assert
`capacity_band:*:exact_5` appears.

- [ ] **Step 2: Run the new tests and verify RED**

Run from `ARR/backend`:

```powershell
python manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_competition_target_20_contract design.test_maas_book_language.MaasBookLanguageRegistryTest.test_target_3_rejects_two_visible_stepped_cards design.test_maas_book_language.MaasBookLanguageRegistryTest.test_target_20_requires_five_cards_per_capacity_band --verbosity 2
```

Expected: imports or assertions fail because the target-aware contract and
joint constraints do not exist.

- [ ] **Step 3: Implement the immutable contract**

Create a frozen dataclass with explicit target-3 and target-20 values. Extend
`ConstraintCandidateFacts` only with measured fields required by the contract:

```python
visible_stepped: bool = False
body_phenotype: str = ""
roof_archetype: str = ""
chassis_family: str = ""
plan_family: str = ""
base_scope: str = ""
capacity_band: str = ""
body_roof_signature: str = ""
```

Encode exact counts, minimum distinct coverage, and maximum repeats in the
existing MILP rows. Populate a typed infeasibility certificate when no exact
set exists.

- [ ] **Step 4: Route every target through the joint solver**

Replace the `if target == 10` special case with
`competition_portfolio_contract(target)`. Remove target-specific fallback
selection that can return a cap-violating set. Make
`_achieved_capacity_balance_pass` derive exact target-aware counts instead of
the impossible fixed two-to-three rule.

- [ ] **Step 5: Run focused and neighboring tests**

```powershell
python manage.py test design.test_maas_book_language --verbosity 1
```

Expected: all tests pass and target-three/target-20 evidence uses the unified
solver.

### Task 2: Preserve Authored Legal Geometry Before Floorwise CSG

**Files:**
- Create: `ARR/backend/design/maas/geometry_language/authored_legal_preservation.py`
- Modify: `ARR/backend/design/maas/geometry_language/legal_field_affine_placement.py`
- Modify: `ARR/backend/design/maas/geometry_language/floorwise_legal_program.py`
- Test: `ARR/backend/design/test_maas_floorwise_legal_program.py`

**Interfaces:**
- Produces: `AuthoredLegalPreservationResult` and
  `certify_authored_affine_program(program, legal_sections, target_floor_areas_m2, floor_capacity_plan_hash)`.
- Consumes: a site-placed typed GeometryProgram and the exact law-derived
  per-floor legal sections.
- Returns the original site-placed program unchanged when its measured sections
  pass; otherwise returns `None` without repairing it.
- Treats an already-authored taper, curve, void, wing, or other bounded AST
  parameterization as `authored_adaptive`; the legal stage may select among
  those compiled authored variants but must not inject a new form verb.

- [ ] **Step 1: Write failing preservation tests**

Build a non-stepped authored program fully inside constant legal sections and
assert:

```python
result = certify_authored_affine_program(...)
self.assertIsNotNone(result)
self.assertEqual(result.program.program_hash(), placed.program_hash())
self.assertEqual(result.certificate["projection_mode"], "authored_affine_preserved")
self.assertTrue(result.certificate["all_sections_contained"])
```

Build a courtyard or curved program inside shrinking sections that remains
contained; assert its compiled vertex/triangle hash is unchanged. Build an
outside program and assert `None`. Build a capacity-short program and assert
`None`.

- [ ] **Step 2: Run tests and verify RED**

```powershell
python manage.py test design.test_maas_floorwise_legal_program.AuthoredLegalPreservationTests --verbosity 2
```

Expected: import failure for the new preservation module.

- [ ] **Step 3: Implement measured floor-section certification**

Compile the placed program once, reject non-manifold/watertight results, slice
the final mesh at each floor band using the existing floor evidence helpers,
and verify:

```python
achieved_total >= aggregate_target * 0.995
section.within(legal_section) or legal_section.covers(section)
```

Record per-floor achieved area, containment margin, program hash,
floor-capacity-plan hash, and `projection_mode`. Do not append geometry nodes.

- [ ] **Step 4: Prefer preservation in affine selection**

For each exact affine shortlist pose, call preservation first. Only candidates
whose authored AST explicitly contains a stepped body operation may enter
`append_floorwise_legal_projection`; all other failed preservation poses are
rejected so legal CSG cannot silently become their design author. Mark the
existing lane `intentional_floorwise_stepped`.

- [ ] **Step 5: Verify focused geometry tests**

```powershell
python manage.py test design.test_maas_floorwise_legal_program design.test_maas_unitbox_matrix --verbosity 1
```

Expected: preservation, containment, hashes, UnitBox, and Matrix4 tests pass.

### Task 3: Certified-Mesh Gestalt and Step-Origin Measurement

**Files:**
- Create: `ARR/backend/design/maas/program_massing/competition_gestalt.py`
- Modify: `ARR/backend/design/maas/book_language/candidate_analysis.py`
- Modify: `ARR/backend/design/maas/program_massing/visual_silhouette.py`
- Modify: `ARR/backend/design/maas/book_language/compatibility_analysis.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_selection.py`
- Test: `ARR/backend/design/test_maas_book_language.py`

**Interfaces:**
- Produces: `competition_gestalt_key(source)`,
  `competition_gestalt_distance(left, right)`, and morphology fields
  `visible_stepped`, `authored_stepped`, `legal_seam_stepped`.
- Consumes only the certified final mesh plus explicit projection provenance.

- [ ] **Step 1: Add failing same-gestalt tests**

Use two fixtures with different top footprints and hashes but the same
floorwise stepped front/side gestalt. Assert the legacy silhouette distance is
above 0.10 while the new composite rejects them below 0.22. Add a preserved
courtyard and curved body pair that passes the ordinary 0.14 floor.

- [ ] **Step 2: Run tests and verify RED**

```powershell
python manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_competition_gestalt_rejects_same_stair_language design.test_maas_book_language.MaasBookLanguageRegistryTest.test_competition_gestalt_keeps_courtyard_and_curve --verbosity 2
```

Expected: missing gestalt API or wrong legacy acceptance.

- [ ] **Step 3: Implement the composite descriptor**

Cache normalized certified-mesh top/front/side silhouettes, isometric edge
projection, floor-area-by-height samples, setback transition sequence, and
roof breakline profile. Compute a bounded 0..1 distance. Keep the existing
silhouette function for historical evidence but use the composite for the
competition contract.

- [ ] **Step 4: Separate authored and legal step origins**

Set `authored_stepped` from typed AST step operators,
`legal_seam_stepped` from floorwise projection provenance, and
`visible_stepped` from final mesh levels/edge profile. Feed
`visible_stepped` to the solver and preserve all three in JSON evidence.

- [ ] **Step 5: Run morphology, selection, and cache tests**

```powershell
python manage.py test design.test_maas_book_language design.test_maas_flow_regressions --verbosity 1
```

Expected: all tests pass with no threshold relaxation.

### Task 4: Quota-Aware Six-Scope Breadth Scheduler

**Files:**
- Create: `ARR/backend/design/maas/book_language/competition_breadth_scheduler.py`
- Modify: `ARR/backend/design/maas/book_language/candidate_generation.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_replenishment.py`
- Modify: `ARR/backend/design/maas/book_language/quality_diversity_archive.py`
- Test: `ARR/backend/design/test_maas_book_language.py`

**Interfaces:**
- Produces: `CompetitionBreadthScheduler`, `BreadthDeficit`,
  `cheap_screen_records`, and a 48..64 exact shortlist.
- Consumes universal form-bank pages, all `BASE_VOLUME_FRACTIONS`, BOOK
  principle variants, legal sections, and the target-aware portfolio contract.

- [ ] **Step 1: Write failing scheduler tests**

Assert that the first deterministic breadth cycle visits all six scopes before
repeating a scope, does not stop at the historical 36-evaluation cap for
target 20, and preserves at least one candidate from every supplied body,
roof, chassis, and plan quota cell. Assert that exact shortlist size never
exceeds 64 and that an infeasible supply returns per-cell deficits.

- [ ] **Step 2: Run tests and verify RED**

```powershell
python manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_competition_breadth_visits_all_six_scopes design.test_maas_book_language.MaasBookLanguageRegistryTest.test_competition_breadth_shortlist_is_bounded design.test_maas_book_language.MaasBookLanguageRegistryTest.test_competition_breadth_reports_cell_deficits --verbosity 2
```

Expected: scheduler imports fail or the first cycle repeats only three scopes.

- [ ] **Step 3: Implement balanced enumeration and cheap screen**

Enumerate round-robin by:

```python
(base_scope, genotype_family, book_principle_kind,
 body_family, roof_family, capacity_band)
```

Compile the typed AST once, screen floor sections and approximate capacity
without exact 3D CSG, then score candidates by outstanding contract deficits.
Do not use final score alone to evict the only member of a required cell.

- [ ] **Step 4: Integrate bounded replenishment**

Run exact CSG only for 48..64 shortlisted records. Stop when 24..28 exact
hard-pass records contain a feasible 20-set; otherwise advance one deterministic
form-bank page and persist `BreadthDeficit` plus stage-specific failure counts:
BOOK bind, authored compile, legal section screen, affine screen, exact CSG,
capacity, parking, and hash bridge.

- [ ] **Step 5: Run generation and resource regression tests**

```powershell
python manage.py test design.test_maas_book_language design.test_maas_flow_regressions --verbosity 1
```

Expected: all tests pass; peak exact shortlist is bounded.

### Task 5: PNU 20-Card Acceptance, PNG, Frontend, and Memory

**Files:**
- Modify: `ARR/backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Modify: `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/selected-runtime-passport.ts`
- Test: `ARR/frontend/src/design/components/book-language-flow/selected-runtime-passport.test.ts`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`
- Modify: `.superpowers/sdd/2026-07-28-single-authority-legal-mass/progress.md`

**Interfaces:**
- Consumes the exact 20-card backend manifest and shared
  floor-capacity-plan/program/geometry/visual hashes.
- Produces the final 20-card PNG, `docs/mass` copy, frontend archive, browser
  verification, timing evidence, and durable handoff record.

- [ ] **Step 1: Add failing command and frontend identity tests**

Assert that a publishable run rejects `diagnostic_target=3`, emits phase timing
and quota evidence for target 20, and that a selected card binds only to a
passport with matching program, geometry, visual, and floor-capacity-plan
hashes.

- [ ] **Step 2: Run tests and verify RED**

Backend:

```powershell
python manage.py test design.test_maas_book_language.MaasBookLanguageRegistryTest.test_publishable_command_requires_twenty_card_contract --verbosity 2
```

Frontend:

```powershell
npm test -- --run src/design/components/book-language-flow/selected-runtime-passport.test.ts
```

Expected: publishable/diagnostic identity or visual-hash assertion fails.

- [ ] **Step 3: Implement command and manifest wiring**

Expose explicit `--publishable-20` and retain `--diagnostic-target` only for
diagnostics. Persist each phase duration, contract metrics, exact identity
hashes, and typed failure deficits. Make the frontend load the newly generated
run rather than a stale exact-replay passport.

- [ ] **Step 4: Run one real PNU/program target-20 acceptance**

Use PNU `1168011800104170004` and neighborhood first, with Neo4j law evidence
enabled and per-card paid VLM disabled. Require:

```text
selected_count=20
law/parking/program/hash hard pass=20/20
stepped=1..3
body phenotype distinct>=5
roof/section distinct>=7
chassis distinct>=6
plan family distinct>=5
capacity bands=5/5/5/5
```

Copy the generated board to `docs/mass` only after these checks pass.

- [ ] **Step 5: Verify PNG and frontend**

Inspect the board directly. Start or reuse the frontend at
`http://127.0.0.1:5178/design/language`, load the new run, assert 20 visible
cards, no broken images, no console errors, and no passport mismatch warning.
Save a browser screenshot beside the backend run evidence.

- [ ] **Step 6: Update durable memory**

Record exact commands, durations, hashes, PNG paths, counts, remaining
limitations, and whether visual review passed. Explicitly mark prior r9
target-three acceptance as diagnostic/legal-only and superseded for portfolio
quality.

### Task 6: Exact Legal-Section Loft for Non-Stepped Visual Authority

This recovery task supersedes Task 2's restriction of all non-affine legal
projection to intentionally stepped bodies. The user-approved later authority
split is: law/GFA use exact floor volumes; MASS/VLM/elevation use a legal,
certified indexed visual mesh; program, capacity, legal-field, Matrix4, and
visual hashes bind both into one product.

**Files:**
- Create: `ARR/backend/design/maas/geometry_language/floorwise_section_loft.py`
- Modify: `ARR/backend/design/maas/geometry_language/source_bridge.py`
- Test: `ARR/backend/design/test_maas_shared_floor_contract.py`
- Test: `ARR/backend/design/test_maas_mass_stage.py`

**Interfaces:**
- Produces:
  `loft_floorwise_legal_sections(source, occupied_sections, legal_sections,
  capacity_plates, output_origin) -> FloorwiseVisualProjection`.
- Consumes the exact post-Matrix4/post-legal-CSG occupied polygon at every
  floor, the trusted legal sections, and the same capacity plates used for
  GFA.
- Supports only a proved-compatible single-Polygon topology in the first
  implementation. A hole/part-count topology change fails closed with
  `section_loft_topology_incompatible`.

- [ ] **Step 1: Write RED tests**

Test nested/shifted three-floor polygons for a closed manifold, exact
mid-floor section areas, legal containment, and at least one nonvertical side.
Test a pre-CSG Matrix4 mesh that exits the host but whose exact CSG sections
produce `floorwise_csg_section_loft`, not prism replay. Test a hole/part
topology mismatch and require a typed fail-closed result with no stale source
surface reuse.

- [ ] **Step 2: Implement exact section-profile loft**

Place exact occupied profiles at each floor mid-height. Insert a compatible
seam profile inside `legal_i intersection legal_{i+1}` at every floor
boundary. Normalize winding, resample compatible rings by arclength, align
cyclic starts by minimum distance, then preserve every original corner by
splitting both rings at the union of their cumulative perimeter fractions.
Stitch directed side triangles and cap only the whole bottom/top; do not cap
internal center/seam profiles. Reject any topology, degeneracy, or containment
ambiguity.

- [ ] **Step 3: Certify and bind**

Reuse existing triangle legal-containment checks, exact midplane section
measurement, surface hashing, and mesh revalidation. Certificate mode is
`floorwise_csg_section_loft`; visible operation is
`exact_legal_section_profile_loft`. Bind section-profile, capacity-volume,
floor-capacity-plan, Matrix4-stack, and exact surface hashes. Any fallback
prism must record `visible_step_fallback=true` and must not count as a
non-stepped quota witness.

- [ ] **Step 4: Prove live supply before retaining**

Run the real PNU direct supply probe. Retain the implementation only if at
least one non-stepped authored family passes beyond the existing
bar/spatial-reserve control without relaxing legal containment, GFA, compiler,
hash, or morphology gates. Then rerun `--publishable-20`.

## Self-Review

- Spec coverage: legal preservation, six-scope breadth, target-aware quotas,
  gestalt metrics, PNU PNG, frontend identity, latency, and memory each have a
  task.
- Placeholder scan: every code-producing step names its concrete behavior,
  command, and expected result.
- Type consistency: the contract, preservation result, gestalt API, breadth
  deficit, and manifest evidence have one producer before their consumers.
