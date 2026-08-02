# Strict UnitBox Diverse MASS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, verify, and expose a maintainable 100-candidate MASS pool with fifteen materially distinct architectural families derived from one canonical UnitBox.

**Architecture:** A small family registry schedules pure GeometryProgram recipe builders. The shared geometry compiler supplies three missing typed operations, while a separate morphology gate proves architectural diversity before rendering. Law truth, portable design outcome memory, optional design Neo4j mirroring, reference/VLM evidence, and frontend presentation remain distinct modules joined by hashes.

**Tech Stack:** Python 3, Django management commands/tests, manifold3d, NumPy, JSON/JSONL, Neo4j Python driver, React/TypeScript/Vitest.

## Global Constraints

- Preserve the current dirty worktree and never reset, discard, or overwrite unrelated user changes.
- Do not add new creative-family branches to `book_language/candidate_generation.py`.
- Keep one canonical `1/1 UnitBox` authority in every creative candidate.
- Record every affine placement as Matrix4; record topology changes as typed architectural operators.
- Keep stepped authorship to one balanced family.
- Never treat pre-legal floor sections as certified legal GFA.
- Never lower geometry, containment, law, parking, or diversity thresholds to fill a quota.
- Never mark a retrieved reference `used_by_vlm=true` unless the exact image was submitted.
- Do not mirror design observations into the configured law Neo4j database.
- Keep the 100-candidate generation under fifteen minutes and paid VLM calls outside the generation loop.
- Because the shared branch contains extensive user work, use task checkpoint files and focused test evidence instead of automatic commits.

---

### Task 1: Lock the family contract and registry

**Files:**
- Create: `ARR/backend/design/maas/creative_family_contract.py`
- Create: `ARR/backend/design/maas/creative_family_registry.py`
- Create: `ARR/backend/design/test_maas_creative_family_registry.py`
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`

**Interfaces:**
- Consumes: `GeometryProgram`, BOOK scope labels, capacity-band strings.
- Produces: `CreativeFamilySpec`, `CreativeRecipeContext`, `CreativeRecipeResult`, `registered_creative_families()`, `balanced_family_schedule(count)`.

- [x] **Step 1: Write the failing registry tests**

```python
EXPECTED = {
    "bent", "carved_void", "courtyard", "cross", "grid",
    "inflated", "notch", "radial", "split_wing", "stepped",
    "triangular_shard", "oblique_crystal", "thin_disc_cluster",
    "interlocking_tilted_discs", "long_span_bridge",
}

def test_registry_has_fifteen_unique_families():
    specs = registered_creative_families()
    assert {spec.family_id for spec in specs} == EXPECTED
    assert len({spec.recipe_id for spec in specs}) == 15

def test_balanced_hundred_schedule_limits_stepped_quota():
    schedule = balanced_family_schedule(100)
    counts = Counter(item.family_id for item in schedule)
    assert len(schedule) == 100
    assert max(counts.values()) - min(counts.values()) <= 1
    assert counts["stepped"] <= 7
```

- [x] **Step 2: Run the tests and confirm missing-module failure**

Run:

```powershell
cd ARR/backend
python manage.py test design.test_maas_creative_family_registry --verbosity 2
```

Expected: import failure for `creative_family_contract` or
`creative_family_registry`.

- [x] **Step 3: Implement immutable contract types**

```python
@dataclass(frozen=True)
class CreativeRecipeContext:
    variation_index: int
    book_scope_label: str
    capacity_band: str

@dataclass(frozen=True)
class CreativeRecipeResult:
    program: GeometryProgram
    contact_type: str
    contact_node_id: str
    form_class: str
    recipe_parameters: dict[str, Any]

@dataclass(frozen=True)
class CreativeFamilySpec:
    family_id: str
    recipe_id: str
    form_class: str
    contact_type: str
```

- [x] **Step 4: Implement deterministic balanced scheduling**

Use stable registry order, distribute `divmod(count, 15)`, and rotate capacity
bands within each family so every family with at least four candidates sees all
four bands. Do not use candidate-index scaling as a variation source.

- [x] **Step 5: Expose the registry schedule without invoking unbuilt recipes**

Expose the registry schedule to `creative_floor_portfolio.py`, but keep the
existing ten-family build path until Task 3 supplies all fifteen builders.
Task 3 removes the old family quota knowledge and completes the portfolio
switch atomically, avoiding placeholder builders or import cycles.

- [x] **Step 6: Run focused tests**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_creative_family_registry `
  design.test_maas_creative_floor_portfolio --verbosity 1
```

Expected: registry tests pass; old ten-family assertion fails until Task 3 is
completed only when the new schedule is explicitly exercised, with no unrelated
error in the existing portfolio path.

### Task 2: Add strict UnitBox architectural operators

**Files:**
- Modify: `ARR/backend/design/maas/geometry_language/ast.py`
- Modify: `ARR/backend/design/maas/geometry_language/compiler.py`
- Create: `ARR/backend/design/test_maas_strict_unitbox_operators.py`

**Interfaces:**
- Consumes: one UnitBox-derived input solid.
- Produces: `circularize` modifier, `matrix_array` pattern, and
  `profile_sweep_3d` modifier/compiler trace.

- [x] **Step 1: Write failing circularize tests**

```python
def test_circularize_consumes_unitbox_derived_input():
    program = unitbox_circularize_program(radius_x=2.0, radius_y=1.0, height=0.4)
    result = compile_geometry_program(program)
    assert result.status == "compiled"
    assert result.metrics["component_count"] == 1
    assert any(row["operator"] == "circularize" for row in result.trace)
    assert exactly_one_canonical_unitbox(program)
```

Also assert deterministic program/geometry hashes, watertightness, manifold
status, and that changing `segments` changes the geometry hash.

- [x] **Step 2: Write failing matrix-array tests**

Create three explicit matrices with different X/Y/Z rotations. Assert three
trace entries, one connected union when overlaps are intentional, and rejection
for malformed/non-finite/non-affine matrices.

- [x] **Step 3: Write failing 3D sweep tests**

Compile a path with nonzero Z change. Assert the result reaches both endpoint
elevations, stays connected, and rejects repeated-point or zero-length paths.

- [x] **Step 4: Confirm unsupported-operator failures**

```powershell
cd ARR/backend
python manage.py test design.test_maas_strict_unitbox_operators --verbosity 2
```

Expected: AST validation or compiler reports unsupported operators.

- [x] **Step 5: Implement `circularize`**

Add `circularize` to modifier operators. Compute the live input bounds and
center, derive an elliptical cylinder from bounded X/Y radii and Z height,
clamp segments to `8..96`, and emit:

```python
["live_bounds", "bounded_circular_section", "extrude", "unitbox_consumed"]
```

The output must depend on the input bounds; it must not ignore its UnitBox
lineage.

- [x] **Step 6: Implement `matrix_array`**

Add `matrix_array` to pattern operators. Validate `2..24` explicit 4×4 affine
matrices with existing `kernel_matrix3x4`, transform the input once per matrix,
and union in listed order. Reject an empty or disconnected final result when
`require_connected=True`.

- [x] **Step 7: Implement `profile_sweep_3d`**

Add `profile_sweep_3d` to modifier operators so it consumes the UnitBox-derived
input bounds as its starting profile. Build rectangular cross-sections at each
path point using deterministic parallel-transport frames, hull consecutive
sections, union segments, and validate the final component count. Expose path
length and frame count in the trace metrics.

- [x] **Step 8: Run operator and geometry regression tests**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_strict_unitbox_operators `
  design.test_maas_geometry_language `
  design.test_maas_unitbox_matrix `
  design.test_maas_extended_csg_contract --verbosity 1
```

Expected: all pass.

### Task 3: Implement fifteen isolated architectural recipes

**Files:**
- Create: `ARR/backend/design/maas/creative_family_recipes.py`
- Modify: `ARR/backend/design/maas/creative_family_registry.py`
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`
- Create: `ARR/backend/design/test_maas_creative_family_recipes.py`
- Modify: `ARR/backend/design/test_maas_creative_floor_portfolio.py`

**Interfaces:**
- Consumes: `CreativeRecipeContext`.
- Produces: fifteen builder functions returning `CreativeRecipeResult`.

- [x] **Step 1: Write recipe lineage tests**

For every recipe, assert:

```python
result = spec.builder(CreativeRecipeContext(
    variation_index=2,
    book_scope_label="1/2",
    capacity_band="balanced_yield",
))
assert exactly_one_canonical_unitbox(result.program)
assert all_non_seed_transforms_are_matrix4(result.program)
assert result.contact_node_id in result.program.node_map
assert result.form_class == spec.form_class
```

- [x] **Step 2: Write new-family topology tests**

Assert:

- `triangular_shard` contains at least two nonparallel `clip` planes.
- `oblique_crystal` contains clip/shear/loft evidence and is not stepped.
- `thin_disc_cluster` contains `circularize` and independent Matrix4 branches.
- `interlocking_tilted_discs` contains `circularize`, `matrix_array`, and a real
  intersecting/bridged contact witness.
- `long_span_bridge` contains two supports/wings and an occupied bridge/sweep
  witness.

- [x] **Step 3: Confirm tests fail before recipe implementation**

```powershell
cd ARR/backend
python manage.py test design.test_maas_creative_family_recipes --verbosity 2
```

- [x] **Step 4: Adapt the existing ten families**

Move their source/BOOK mapping out of `creative_floor_portfolio.py` into pure
builders. Preserve existing compiler semantics and evidence, but remove
index-dependent scale perturbation as a novelty mechanism.

- [x] **Step 5: Implement triangular and crystal recipes**

Start with one canonical UnitBox, apply proportion Matrix4, author multiple
arbitrary-plane clips, and use optional shear/loft branches. Keep every variant
connected and explicitly non-stepped.

- [x] **Step 6: Implement disc recipes**

Use `UnitBox -> Matrix4 thin slab -> circularize`. Apply distinct tilt/scale/
translation matrices. Use overlap, intersection, or an explicit connecting
spine so the final result has exactly one component.

- [x] **Step 7: Implement long-span recipe**

Create two grounded support masses from the shared UnitBox lineage and connect
them with `bridge` or `profile_sweep_3d`. Store span length, support contact,
and occupied connector evidence.

- [x] **Step 8: Update the 100-pool family assertions**

Replace the old ten-by-ten assertion with fifteen balanced quotas. Assert the
five new families are present and stepped count is no greater than seven.

- [x] **Step 9: Run recipe and portfolio tests**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_creative_family_registry `
  design.test_maas_creative_family_recipes `
  design.test_maas_creative_floor_portfolio --verbosity 1
```

Expected: all pass.

### Task 4: Replace hash-only novelty with morphology evidence

**Files:**
- Create: `ARR/backend/design/maas/creative_morphology.py`
- Create: `ARR/backend/design/test_maas_creative_morphology.py`
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`

**Interfaces:**
- Consumes: compiled vertices, triangles, floor sections, and contact evidence.
- Produces: `MorphologyDescriptor`, `morphology_distance(left, right)`,
  `accept_morphology(candidate, accepted)`.

- [x] **Step 1: Write scale-invariance and repetition tests**

```python
def test_uniform_scale_does_not_create_morphology_novelty():
    a = descriptor(mesh)
    b = descriptor(uniformly_scaled(mesh, 1.003))
    assert morphology_distance(a, b) < 0.01

def test_repeated_family_parameter_noise_is_rejected():
    accepted = [candidate_with_descriptor(base)]
    assert not accept_morphology(candidate_with_descriptor(noisy_copy), accepted)
```

- [x] **Step 2: Write cross-family distance tests**

Use representative stepped, triangular, disc-cluster, courtyard, and long-span
fixtures. Assert their required pair distances pass and that the distance is
symmetric and bounded to `0..1`.

- [x] **Step 3: Implement descriptor extraction**

Normalize to centroid and unit diagonal, then calculate fixed-length vectors:
axis ratios, eight Z-slice occupancies, floor-area profile, convexity, void
fraction, twelve normal bins, eight radial bins, three silhouettes, and contact
topology.

- [x] **Step 4: Implement deterministic distance and gates**

Use named weighted components saved alongside the total. Require both global
and within-family thresholds. Reject quota exhaustion with a diagnostic that
names the closest candidate and failed components.

- [x] **Step 5: Remove index-only scale novelty**

Delete `_with_scope_matrix()` behavior whose only purpose is per-index
`0.1..0.3%` scale variation. Legitimate dimensional variation must come from
recipe parameters and capacity intent.

- [x] **Step 6: Persist morphology evidence**

Add the descriptor, pairwise nearest-neighbor distance, threshold, and decision
to every candidate JSON and the portfolio summary.

- [x] **Step 7: Run diversity tests and the full 100 build test**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_creative_morphology `
  design.test_maas_creative_floor_portfolio --verbosity 1
```

Expected: 100 accepted candidates, all material-diversity gates pass, and the
test completes within fifteen minutes.

### Task 5: Separate design memory from law Neo4j

**Files:**
- Create: `ARR/backend/design/maas/design_memory/__init__.py`
- Create: `ARR/backend/design/maas/design_memory/config.py`
- Create: `ARR/backend/design/maas/design_memory/neo4j_adapter.py`
- Create: `ARR/backend/design/test_maas_design_memory_neo4j.py`
- Modify: `ARR/backend/design/maas/geometry_language/outcome_graph.py`

**Interfaces:**
- Consumes: portable outcome graph nodes/edges and
  `MAAS_DESIGN_MEMORY_NEO4J_*`.
- Produces: `DesignMemorySettings.from_environment()`,
  `DesignMemoryNeo4jAdapter.mirror(graph)`.

- [x] **Step 1: Write configuration isolation tests**

Assert that absent design settings disable mirroring, equal law/design
URI+database disables mirroring with `reason="law_database_collision"`, and a
separate design database creates `Neo4jService(database=design_database)`.

- [x] **Step 2: Write graph payload tests**

Assert only design labels are written:

```text
MaasDesignNode
MAAS_DESIGN_RELATION
```

and that law labels/relationships never appear in generated Cypher.

- [x] **Step 3: Implement fail-closed settings**

Read:

```text
MAAS_DESIGN_MEMORY_NEO4J_ENABLED
MAAS_DESIGN_MEMORY_NEO4J_URI
MAAS_DESIGN_MEMORY_NEO4J_USER
MAAS_DESIGN_MEMORY_NEO4J_PASSWORD
MAAS_DESIGN_MEMORY_NEO4J_DATABASE
```

Never fall back to `NEO4J_*` for a write.

- [x] **Step 4: Move mirroring behind the adapter**

Keep `OutcomeGraph.save()` as portable JSON authority. Replace direct
`Neo4jService()` construction in `mirror_to_neo4j()` with the design-memory
adapter.

- [x] **Step 5: Run design-memory and law-identity tests**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_design_memory_neo4j `
  design.test_maas_law_graph_identity `
  design.test_maas_outcome_graph_authored_identity --verbosity 1
```

Expected: all pass without a live Neo4j connection.

### Task 6: Bind reference retrieval, VLM review, and preference memory

**Files:**
- Create: `ARR/backend/design/maas/design_memory/reference_events.py`
- Create: `ARR/backend/design/test_maas_design_reference_events.py`
- Modify: `ARR/backend/design/maas/preference/vlm_scorer.py`
- Modify: `ARR/backend/design/maas/geometry_language/executed_archive.py`
- Modify: `ARR/backend/design/maas/geometry_language/outcome_graph.py`

**Interfaces:**
- Consumes: corpus reference records, exact VLM image inputs, structured VLM
  result, and pairwise labels.
- Produces: retrieval, submission, judgement, typed-edit, and human-choice
  event records linked by hashes.

- [x] **Step 1: Write truth-policy tests**

Retrieve five references, submit two, and assert exactly two records have
`used_by_vlm=true`. Assert every submitted image has local/remote identity,
SHA-256, input order, response ID, program hash, and geometry hash.

- [x] **Step 2: Write preference-memory tests**

Append accepted/rejected pairwise choices and assert the event links reviewer,
session, preferred/rejected candidates, reason, and both geometry hashes.

- [x] **Step 3: Implement typed reference events**

Create schema-versioned immutable dictionaries for:

```text
reference_retrieved
reference_submitted_to_vlm
vlm_judgement
typed_edit_proposed
human_pairwise_choice
```

- [x] **Step 4: Persist events into the portable design graph**

Keep image bytes on disk. Store path/URI, digest, source URL, collection, and
rights/provenance metadata on reference nodes.

- [x] **Step 5: Add a bounded VLM pilot mode**

Add a command option that chooses one morphology-medoid representative per
family, sends at most three retrieved references per representative, uses
low-cost image detail, and caps paid requests at fifteen. The default creative
100 command remains zero-cost.

- [x] **Step 6: Run reference/VLM tests without paid calls**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_design_reference_events `
  design.test_maas_preference `
  design.test_maas_executed_vlm_audit --verbosity 1
```

Expected: all provider calls mocked and all tests pass.

### Task 7: Persist and expose the full 100-card archive

**Files:**
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Modify: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`
- Create: `ARR/backend/design/maas/creative_portfolio_catalog.py`
- Create: `ARR/backend/design/test_maas_creative_portfolio_catalog.py`
- Modify: `ARR/backend/design/maas/single_execution/catalog.py`
- Modify: `ARR/backend/design/views.py`
- Modify: `ARR/backend/design/urls.py`
- Create: `ARR/backend/design/test_maas_creative_portfolio_api.py`

**Interfaces:**
- Consumes: `maas-creative-portfolio.json`.
- Produces: archive rows with exact identity tuple and portable graph/member
  edges.

- [x] **Step 1: Write persistence-contract tests**

Assert one board PNG, 100 individual PNGs, 100 candidate JSON files, one
portfolio JSON, fifteen family facets, four capacity facets, morphology
evidence, full AST/Matrix4/mesh arrays, and `legal_status=not_evaluated`.

- [x] **Step 2: Write catalog discovery tests**

Place a small creative run in a temporary archive root and assert every member
is discoverable with:

```text
run_id
candidate_id
program_hash
geometry_hash
render_png
candidate_json
family
form_class
capacity_band
storeys
legal_status
```

- [x] **Step 3: Implement a dedicated creative catalog adapter**

Validate paths remain under the run directory, validate program/geometry
hashes, reject incomplete members, and emit `geometry_portfolio` plus
`member_of` graph edges.

- [x] **Step 4: Keep legal pending semantics**

Do not fabricate law, parking, elevation, or certified capacity evidence while
adapting the archive.

- [x] **Step 5: Expose a read-only creative portfolio endpoint**

Add a route that returns the validated creative manifest and serves candidate
render assets only from inside the configured `docs/mass` root. Treat `run_id`
as an opaque validated directory name, reject traversal, and never coerce the
payload into `ExecutedMassManifest`.

- [ ] **Step 6: Run command, catalog, and API tests**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_creative_floor_portfolio_command `
  design.test_maas_creative_portfolio_catalog `
  design.test_maas_creative_portfolio_api `
  design.test_maas_single_execution --verbosity 1
```

Expected: all pass.

### Task 8: Show and filter all 100 candidates in the frontend

**Files:**
- Modify: `ARR/frontend/src/design/lib/language-system-types.ts`
- Modify: `ARR/frontend/src/design/lib/api-client.ts`
- Create: `ARR/frontend/src/design/components/book-language-flow/creative-portfolio-adapter.ts`
- Create: `ARR/frontend/test/unit/design/creative-portfolio-adapter.test.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/archive-selection-policy.ts`
- Modify: `ARR/frontend/test/unit/design/archive-selection-policy.test.ts`
- Modify: `ARR/frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `ARR/frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `ARR/frontend/test/unit/design/ExecutedMassEvidence.test.tsx`
- Create: `ARR/frontend/src/design/components/book-language-flow/CreativeMassFilters.tsx`
- Create: `ARR/frontend/test/unit/design/CreativeMassFilters.test.tsx`
- Modify: `ARR/frontend/test/unit/design/maas-single-execution-api.test.ts`
- Modify: `ARR/frontend/test/unit/design/LanguageNetworkCanvas.test.tsx`

**Interfaces:**
- Consumes: creative catalog rows and facets.
- Produces: virtualized/paginated 100-card rail, filters, exact selection
  identity, and pending/certified status display.

- [x] **Step 1: Write the 100-card rendering test**

Feed 100 archive rows and assert card 1, card 25, card 100, and pagination or
virtual-window navigation are reachable. Assert there is no `slice(0, 24)` or
equivalent fixed truncation.

- [x] **Step 2: Write archive-policy separation tests**

Assert creative portfolio selection returns all 100 members while the recent
single-execution timeline retains its existing 24-item cap. The current cap at
`archive-selection-policy.ts:100-104` must no longer apply to creative
portfolio membership.

- [x] **Step 3: Write filtering tests**

Filter by `interlocking_tilted_discs`, `maximum_target`, storeys, and
`not_evaluated`; assert counts and selection identity remain stable.

- [x] **Step 4: Extend the TypeScript and API contracts**

Add `family`, `formClass`, `capacityBand`, `storeys`, `legalStatus`,
`morphologyDistance`, and `portfolioRunId` as explicit typed fields.
Implement `getCreativeMassPortfolio(runId?, signal?)` against the dedicated
backend route.

- [x] **Step 5: Implement the creative portfolio adapter**

Convert the manifest into rail cards plus `NetworkNode`/`NetworkEdge` values,
normalize relative render paths through the backend asset route, preserve the
101-node/100-member-edge portable graph, and distribute family nodes into
stable graph stages. Do not expose execute, paid-VLM, or certified-passport
actions on pre-legal creative cards.

- [x] **Step 6: Implement the full rail and filters**

Use existing component conventions. Preserve selection by the complete
`runId/candidateId/programHash/geometryHash` tuple and distinguish pre-legal
cards visually.

- [x] **Step 7: Run frontend tests**

```powershell
cd ARR/frontend
npx vitest run `
  test/unit/design/archive-selection-policy.test.ts `
  test/unit/design/creative-portfolio-adapter.test.ts `
  test/unit/design/ExecutedMassEvidence.test.tsx `
  test/unit/design/CreativeMassFilters.test.tsx `
  test/unit/design/maas-single-execution-api.test.ts `
  test/unit/design/LanguageNetworkCanvas.test.tsx
```

Expected: all pass.

### Task 9: Generate, inspect, and bounded-VLM review the new 100

**Files:**
- Output: `docs/mass/<new-run-id>/`
- Update: `docs/ai-session-memory/MAAS_COMPETITION20_ACTIVE_20260729.md`
- Update: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: implemented generator and verified archive/frontend adapters.
- Produces: final board, individual PNG/JSON artifacts, optional bounded VLM
  audit, and session checkpoint.

- [x] **Step 1: Run all focused backend tests**

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_strict_unitbox_operators `
  design.test_maas_creative_family_registry `
  design.test_maas_creative_family_recipes `
  design.test_maas_creative_morphology `
  design.test_maas_creative_floor_portfolio `
  design.test_maas_creative_floor_portfolio_command `
  design.test_maas_creative_portfolio_catalog `
  design.test_maas_design_memory_neo4j `
  design.test_maas_design_reference_events --verbosity 1
```

- [x] **Step 2: Generate the real 100**

```powershell
cd ARR/backend
python manage.py generate_maas_creative_100 `
  --count 100 `
  --pnu 1168011800104170004 `
  --output-root D:\Data\25_ACE\docs\mass
```

Expected: exit 0 in less than fifteen minutes and paid request count zero.

- [x] **Step 3: Run artifact verification**

Verify counts, fifteen-family quotas, four capacity bands, 100 unique program/
geometry/normalized-mesh hashes, morphology thresholds, component/watertight/
manifold gates, exact UnitBox authority, Matrix4 traces, and legal-pending
state.

- [x] **Step 4: Inspect the board and representative individual PNGs**

Visually inspect at least one card from every family. Explicitly confirm
triangular, crystal, disc cluster, interlocking tilted discs, long span, and
stepped are visible and not mistaken for one another.

- [x] **Step 5: Run the bounded paid VLM pilot if credentials are configured**

Review one representative per family, at most fifteen requests and at most
three references per request. If credentials are absent, record
`status=not_run_missing_credentials`; do not fake an audit.

- [x] **Step 6: Start the frontend and perform browser verification**

Confirm the design language page loads, all 100 are reachable, filters work,
selection loads the matching graph/passport, and the browser console has no
new errors.

- [x] **Step 7: Update durable session memory**

Record the exact run directory, board PNG, counts, hashes, elapsed time, VLM
request count, Neo4j mirror status, frontend verification evidence, remaining
uncertified legal state, and next action.

### Task 10: Independent review and final regression

**Files:**
- Update only files required by actionable review findings.
- Update: `docs/ai-session-memory/MAAS_COMPETITION20_ACTIVE_20260729.md`
- Update: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`

**Interfaces:**
- Consumes: all implemented tasks and verification artifacts.
- Produces: reviewed, regression-tested handoff.

- [ ] **Step 1: Request separate spec-compliance and code-quality reviews**

Reviewers must check UnitBox authority, operator correctness, material
diversity, module size/responsibility, law/design DB isolation, VLM truth
policy, archive identity, and frontend reachability.

- [ ] **Step 2: Address only verified findings**

For each change, add or strengthen the failing regression test first, apply the
minimal fix in the owning module, and rerun its focused suite.

- [ ] **Step 3: Run backend and frontend regression suites**

Run all focused suites from Tasks 2–8 plus existing MAAS flow regression,
shared floor contract, elevation handoff, and frontend executed-mass tests.

- [ ] **Step 4: Check maintainability**

Assert:

- `candidate_generation.py` has no new creative-family code.
- no new production module exceeds 600 lines;
- each new module has one responsibility;
- no duplicate family tables exist;
- the family registry is the only creative-family discovery source;
- no credentials or image binaries are stored in Neo4j payloads.

- [ ] **Step 5: Finalize the memory checkpoint**

Mark only evidence-backed items complete. Preserve explicit statuses for
unrun paid VLM, unavailable Neo4j, or pending legal certification.
