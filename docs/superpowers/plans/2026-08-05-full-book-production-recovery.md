# Full BOOK Production Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore cached/fresh LLM and deterministic creative MASS generation to one canonical UnitBox, explicit Matrix4 BaseVolume, executable BOOK scope/principle projection, and truthful 30/20/9 coverage evidence.

**Architecture:** Move affine lowering out of the deterministic recipe fixture into a reusable production normalizer, then introduce a registry-backed BOOK assignment/projection module. Both the authored hybrid loop and deterministic count-100 loop consume the same assignment records; retained candidates persist executable lineage and reports compute coverage from AST evidence rather than labels.

**Tech Stack:** Python 3, Django `SimpleTestCase`, dataclasses, MAAS `GeometryProgram`, Matrix4 helpers, BOOK registry/projection adapter, manifold3d geometry gates.

## Global Constraints

- Exactly one canonical `1/1 UnitBox` is the primitive Base Model authority.
- Persisted normalized ASTs contain no `scale`, `rotate`, `translate`, `mirror`, or `shear` transform shorthands.
- BOOK `1/1`, `3/8`, `1/2`, `1/4`, `1/8`, and `1/16` are derived scope states.
- The registry owns 30 operations, 20 combinations, and 9 aggregations.
- Qatar National Library, Seattle Central Library, SANAA, OMA, and Qatar National Museum remain capability-range evidence only; named operators, recipes, selectors, and quotas are forbidden.
- Existing geometry, morphology, statutory, parking, capacity, program, and VLM thresholds remain unchanged.
- Deterministic verification makes zero paid provider calls.
- Preserve unrelated dirty work; never stage overlapping files unsafely.

## File Structure

- Create `ARR/backend/design/maas/geometry_language/affine_normalization.py`: shared UnitBox/affine lowering and safe Matrix4-chain composition.
- Create `ARR/backend/design/maas/creative_book_supply.py`: registry schedule, typed projection, and AST-derived coverage.
- Modify `creative_program_author.py` and `creative_family_recipes.py`: use the shared affine normalizer.
- Modify `creative_family_contract.py`, both recipe modules, and `creative_floor_portfolio.py`: consume scheduled BOOK assignments.
- Modify `generate_maas_creative_100.py`: persist BOOK and Matrix4 authority evidence.
- Add or extend focused Django tests for every boundary.

---

### Task 1: Shared affine BaseVolume normalization

**Files:**
- Create: `ARR/backend/design/maas/geometry_language/affine_normalization.py`
- Modify: `ARR/backend/design/maas/creative_program_author.py`
- Modify: `ARR/backend/design/maas/creative_family_recipes.py`
- Test: `ARR/backend/design/test_maas_unitbox_matrix.py`
- Test: `ARR/backend/design/test_maas_creative_program_author.py`

**Interfaces:**
- Consumes: `normalize_unitbox_program`, `matrix4_for_transform`, `compose_matrix4`.
- Produces: `normalize_affine_basevolume_program(program: GeometryProgram) -> GeometryProgram`.

- [ ] **Step 1: Write failing tests**

Construct `box(center=True) -> scale -> rotate -> bend` and assert:

```python
normalized = normalize_affine_basevolume_program(program)
operators = [node.operator for node in normalized.topological_nodes()]
self.assertEqual(operators.count("box"), 1)
self.assertFalse({"scale", "rotate", "translate", "mirror", "shear"} & set(operators))
self.assertTrue(any(node.operator == "matrix4" for node in normalized.nodes))
self.assertEqual(
    compile_geometry_program(normalized).geometry_hash,
    compile_geometry_program(program).geometry_hash,
)
```

Add a cached `CreativeAuthoredProgram` test proving `normalize_authored_programs()` uses the same path.

- [ ] **Step 2: Verify RED**

```powershell
python manage.py test design.test_maas_unitbox_matrix design.test_maas_creative_program_author -v 2
```

Expected: import failure because the shared normalizer does not exist.

- [ ] **Step 3: Implement the minimal normalizer**

```python
AFFINE_SHORTHANDS = frozenset({"scale", "rotate", "translate", "mirror", "shear"})

def normalize_affine_basevolume_program(program: GeometryProgram) -> GeometryProgram:
    unitbox_program = normalize_unitbox_program(program)
    lowered = _lower_affine_shorthands(unitbox_program)
    composed = _compose_single_consumer_matrix_chains(lowered)
    _validate_affine_authority(composed)
    return replace(composed, metadata={
        **composed.metadata,
        "base_volume_authority": "1/1 UnitBox",
        "affine_authority": "explicit_matrix4",
    })
```

Resolve center/centroid pivots from compiled ancestor bounds as current `_matrix4_only()` does. Compose only a parent Matrix4 with one consumer, in `compose_matrix4(parent, child)` program order. Preserve `lowered_affine_operator` and `composed_matrix4_node_ids` provenance.

- [ ] **Step 4: Route both callers through it**

Use `normalize_affine_basevolume_program()` in both branches of `normalize_authored_programs()`. Make fixture `_matrix4_only()` delegate to it.

- [ ] **Step 5: Verify GREEN and adjacent regressions**

```powershell
python manage.py test design.test_maas_unitbox_matrix design.test_maas_creative_program_author design.test_maas_creative_family_recipes -v 2
```

- [ ] **Step 6: Commit only isolated Task 1 files**

Run `git diff --check` on the exact files. Commit `fix(maas): normalize authored BaseVolume matrices` only if no task file overlaps unrelated dirty hunks; otherwise record the verified worktree boundary without unsafe staging.

---

### Task 2: Registry-backed BOOK assignment and projection

**Files:**
- Create: `ARR/backend/design/maas/creative_book_supply.py`
- Test: `ARR/backend/design/test_maas_creative_book_supply.py`

**Interfaces:**
- Produces `CreativeBookAssignment` with `principle_id`, `principle_kind`, `execution_verbs`, `aggregation_methods`, `scope_label`, and `orientation`.
- Produces `creative_book_schedule(count)`, `project_creative_book_program(program, assignment)`, and `creative_book_evidence(program)`.

- [ ] **Step 1: Write failing schedule and projection tests**

```python
schedule = creative_book_schedule(100)
self.assertEqual(len(schedule), 100)
self.assertEqual(len({item.principle_id for item in schedule[:59]}), 59)
self.assertEqual(
    Counter(item.principle_kind for item in schedule[:59]),
    Counter({"base_operative": 30, "combination": 20, "aggregation": 9}),
)
self.assertEqual(
    {item.scope_label for item in schedule},
    {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"},
)
```

Also assert no assignment identifier contains `qatar`, `sanaa`, `oma`, `library`, or `museum`, and projected AST contains `book_base_volume` plus active `book_recursive_projection`.

- [ ] **Step 2: Verify RED**

```powershell
python manage.py test design.test_maas_creative_book_supply -v 2
```

- [ ] **Step 3: Implement canonical scheduling**

Read `build_book_language_registry()["principles"]`, filter kinds `base_operative`, `combination`, and `aggregation`, preserve registry order, and repeat only after all 59. Cycle canonical scopes with orientations `long_axis, short_axis, long_axis, short_axis, vertical, vertical`.

- [ ] **Step 4: Implement projection and evidence**

Use `book_sentence_variants(assignment.execution_verbs, count=1)[0]`, `compose_program_with_book_operations()`, and `apply_book_projection_to_geometry_program()`. Persist assignment metadata only after success. `creative_book_evidence()` returns materialized evidence only when selector and projection nodes exist.

- [ ] **Step 5: Verify GREEN with BOOK regressions**

```powershell
python manage.py test design.test_maas_creative_book_supply design.test_maas_book_language design.test_maas_book_scope -v 2
```

- [ ] **Step 6: Commit isolated Task 2 files**

Commit `feat(maas): schedule canonical BOOK production language` after exact-file `git diff --check`.

---

### Task 3: Hybrid supply uses deficit-directed BOOK lineage

**Files:**
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio.py`
- Test: `ARR/backend/design/test_maas_creative_author_supply.py`

**Interfaces:**
- Consumes Task 1 normalization and Task 2 schedule/projection/evidence.
- Adds `CreativeFloorPortfolioReport.language_coverage` and principle/scope fields to typed rejection evidence.

- [ ] **Step 1: Write failing hybrid report tests**

```python
report = build_creative_floor_portfolio_report(
    target_count=20,
    capacity_ceiling_m2=332.322,
    authored_programs=programs,
)
self.assertEqual(len(report.candidates), 20)
self.assertEqual(report.language_coverage["distinct_principle_count"], 20)
self.assertEqual(set(report.language_coverage["scope_counts"]), EXPECTED_SCOPES)
self.assertTrue(all(row["book_language_evidence"]["materialized"] for row in report.candidates))
```

Add a failure test proving the next source retries the same unfilled assignment and the unprojected source never enters candidates.

- [ ] **Step 2: Verify RED**

```powershell
python manage.py test design.test_maas_creative_floor_portfolio design.test_maas_creative_author_supply -v 2
```

- [ ] **Step 3: Assign by retained deficit**

Inside the authored loop use `assignment = schedule[len(candidates)]`. Project before program hashing/compilation. Only advance by retaining a candidate. Record `book_projection_failure`, `book_authority_missing`, exact failure code, principle ID, and scope; never fall back to the unprojected source.

- [ ] **Step 4: Persist and gate coverage**

Set `candidate["book_language_evidence"]` from AST evidence. Compute coverage from retained candidates. A target-20 report is complete only with 20 candidates, 20 distinct principle IDs, and all six scopes.

- [ ] **Step 5: Verify GREEN and morphology regressions**

```powershell
python manage.py test design.test_maas_creative_floor_portfolio design.test_maas_creative_author_supply design.test_maas_creative_morphology -v 2
```

- [ ] **Step 6: Commit only safely isolated Task 3 hunks**

Use exact-file diff review; if task files contain unrelated dirty work, do not stage whole files.

---

### Task 4: Count-100 covers the complete 30/20/9 grammar

**Files:**
- Modify: `ARR/backend/design/maas/creative_family_contract.py`
- Modify: `ARR/backend/design/maas/creative_family_recipes.py`
- Modify: `ARR/backend/design/maas/creative_family_recipes_novel.py`
- Modify: `ARR/backend/design/maas/creative_floor_portfolio.py`
- Test: `ARR/backend/design/test_maas_creative_family_recipes.py`
- Test: `ARR/backend/design/test_maas_creative_floor_portfolio.py`

**Interfaces:**
- Adds defaulted `book_principle_id`, `book_principle_kind`, `book_execution_verbs`, and `book_aggregation_methods` fields to `CreativeRecipeContext`.
- Deterministic schedule fills those fields from `creative_book_schedule(count)`.

- [ ] **Step 1: Write failing count-100 coverage test**

```python
coverage = self.portfolio["book_language_coverage"]
self.assertEqual(coverage["base_operative_count"], 30)
self.assertEqual(coverage["combination_count"], 20)
self.assertEqual(coverage["aggregation_count"], 9)
self.assertEqual(coverage["missing_principle_ids"], [])
```

For every candidate also assert one box and no affine shorthand operators.

- [ ] **Step 2: Verify RED**

```powershell
python manage.py test design.test_maas_creative_floor_portfolio.CreativeFloorPortfolioBaselineTests -v 2
```

Expected: current seven-verb fixture coverage fails 30/20/9.

- [ ] **Step 3: Extend recipe context with defaulted assignment fields**

```python
book_principle_id: str = ""
book_principle_kind: str = ""
book_execution_verbs: tuple[str, ...] = ()
book_aggregation_methods: tuple[str, ...] = ()
```

- [ ] **Step 4: Consume exact scheduled sentences**

When scheduled verbs exist, legacy and novel projection helpers use those exact verbs with `book_sentence_variants(..., count=1)`. Current family default verbs remain only for isolated recipe calls lacking assignments. No named precedent logic is introduced.

- [ ] **Step 5: Add AST-derived fixture coverage**

Add `book_language_coverage` to the payload. Require complete 30/20/9 only for `count == 100`; smaller fixture runs report actual coverage.

- [ ] **Step 6: Verify GREEN with full baseline**

```powershell
python manage.py test design.test_maas_creative_family_recipes design.test_maas_creative_floor_portfolio -v 2
```

Expected: 100 retained, 100 unique program/geometry/normalized-mesh hashes, unchanged morphology thresholds, balanced family/capacity quotas, and complete 30/20/9 coverage.

- [ ] **Step 7: Review the dirty boundary before any Task 4 commit**

Run exact-file `git diff --check` and do not stage overlapping unrelated hunks.

---

### Task 5: Persist v2 coverage ledger and run one bounded diagnostic

**Files:**
- Modify: `ARR/backend/design/management/commands/generate_maas_creative_100.py`
- Modify: `ARR/backend/design/test_maas_creative_floor_portfolio_command.py`
- Modify: `ARR/backend/design/maas/README.md`
- Create after live run: `docs/ai-session-memory/maas-mass-flow/checkpoints/2026-08-05-full-book-production-recovery-r1.md`

**Interfaces:**
- Produces `arr.maas.prelegal_stage_ledger.v2` with `book_language_coverage` and `affine_authority`.

- [ ] **Step 1: Write failing command-ledger test**

```python
self.assertEqual(ledger["schema_version"], "arr.maas.prelegal_stage_ledger.v2")
self.assertEqual(ledger["book_language_coverage"]["distinct_principle_count"], 20)
self.assertEqual(len(ledger["book_language_coverage"]["scope_counts"]), 6)
self.assertEqual(ledger["affine_authority"]["missing_matrix4_count"], 0)
self.assertEqual(ledger["affine_authority"]["shorthand_node_count"], 0)
```

- [ ] **Step 2: Verify RED**

```powershell
python manage.py test design.test_maas_creative_floor_portfolio_command -v 2
```

- [ ] **Step 3: Persist v2 evidence**

Copy report coverage into ledger and summary. Aggregate affine authority from persisted ASTs. Preserve partial boards and exact deficits. Do not change paid author/VLM accounting.

- [ ] **Step 4: Run the deterministic verification set**

```powershell
python manage.py test design.test_maas_unitbox_matrix design.test_maas_book_language design.test_maas_book_scope design.test_maas_creative_book_supply design.test_maas_creative_program_author design.test_maas_creative_author_supply design.test_maas_creative_family_registry design.test_maas_creative_family_recipes design.test_maas_creative_morphology design.test_maas_creative_floor_portfolio design.test_maas_creative_floor_portfolio_command -v 2
python manage.py check
```

- [ ] **Step 5: Run forbidden-name and whitespace checks**

```powershell
rg -n "qatar_|sanaa_|oma_|library_recipe|museum_recipe" ARR/backend/design/maas -g "*.py"
git diff --check -- ARR/backend/design/maas ARR/backend/design/test_maas_creative_book_supply.py ARR/backend/design/test_maas_creative_program_author.py ARR/backend/design/test_maas_creative_floor_portfolio.py ARR/backend/design/test_maas_creative_floor_portfolio_command.py
```

- [ ] **Step 6: Run one zero-paid hybrid target-20 diagnostic**

```powershell
python manage.py generate_maas_creative_100 --count 20 --pnu 1168011800104170004 --capacity-ceiling-m2 332.322 --output-root D:\Data\25_ACE\docs\playwright\design-route-live-verify --run-id full-book-production-recovery-r1 --author-mode hybrid --author-cache-root D:\Data\25_ACE\docs\ai-session-memory\reference-corpus\geometry-author-cache --max-fresh-author-requests 0
```

Expected: paid author 0 and paid VLM 0; either complete 20/20 with twenty principles and six scopes, or a truthful partial result with typed deficits.

- [ ] **Step 7: Inspect artifacts and record checkpoint**

Verify each candidate JSON has one UnitBox, no affine shorthand, BaseVolume Matrix4, materialized BOOK selector, and registry principle ID. Record exact hashes, counts, rejection codes, limitations, and next action.

- [ ] **Step 8: Run fresh final verification before claiming completion**

Repeat Step 4, run `git diff --check`, read every exit code, and report actual results without legal/parking/capacity/program/VLM claims.
