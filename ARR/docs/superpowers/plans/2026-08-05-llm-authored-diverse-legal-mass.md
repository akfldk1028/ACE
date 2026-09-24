# LLM-Authored Diverse Legal MASS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce and verify exactly 20 law-passing, LLM-authored MASS alternatives whose authored architectural identities survive legal placement and whose combined PNG satisfies the strict diversity contract.

**Architecture:** Keep LLM authorship upstream of typed GeometryProgram compilation and deterministic legal gates. Restore global Matrix4 relative-pose preservation in the legal bridge, keep typed diversity caps in every selection path, and replenish missing compatible language cells instead of converting rejected forms into legal stair stacks.

**Tech Stack:** Python 3.13, Django management commands, Shapely, typed GeometryProgram/Matrix4/CSG, unittest/pytest, JSON evidence manifests, Playwright/browser frontend verification.

## Global Constraints

- Final selected count, deterministic legal/final hard-pass count, and LLM-authored AST count must all equal 20.
- All six BOOK scopes must be represented and no typed portfolio cap may be violated.
- A legal floor fit may not independently recenter or realign an authored floor.
- Every selected MASS must preserve UnitBox -> BaseVolume -> global Matrix4
  provenance, and `pose_fallback_used` must be false for all 20 selections.
- Failed geometry is replenished, never replaced with forced stepped replay, cloned mesh, or count-only fallback.
- Law, BCR, FAR, parking, capacity, mesh validity, and portfolio compatibility remain deterministic authorities.
- Completion requires inspection of the combined 20-candidate PNG and the `/design/language` portfolio using the same persisted identities.

---

### Task 1: Preserve Authored Relative Pose Through Legal Placement

**Files:**
- Modify: `backend/design/maas/geometry_language/source_bridge.py`
- Test: `backend/design/test_maas_shared_floor_contract.py`

**Interfaces:**
- Consumes: `materialize_floorwise_legal_source(source, legal_sections, target_plan_coverage, target_floor_areas_m2, ...) -> SourceMass | None`
- Produces: `floorwise_legal_matrix_stack.pose_fit == "single_global_rotation_translation_with_floor_relative_pose_preserved"` and floor matrices derived from one global plan frame.

- [ ] **Step 1: Add a real-mesh regression assertion**

Extend `test_floorwise_legal_stack_samples_exact_authored_mesh_sections` to assert the shifted result's stack uses the global relative-pose mode and that `pose_fallback_used` is false.

```python
stack = shifted.metadata["floorwise_legal_matrix_stack"]
self.assertEqual(
    stack["pose_fit"],
    "single_global_rotation_translation_with_floor_relative_pose_preserved",
)
self.assertFalse(stack["pose_fallback_used"])
```

- [ ] **Step 2: Run the regression before implementation**

Run from `backend`:

```powershell
$env:DJANGO_SETTINGS_MODULE='backend.settings'
python -m pytest design/test_maas_shared_floor_contract.py -q -k "floorwise_legal_stack_samples_exact_authored_mesh_sections"
```

Expected before the fix: FAIL because the shifted upper centroid is erased or the pose mode is floorwise-axis-fit.

- [ ] **Step 3: Restore the global Matrix4 placement**

In `materialize_floorwise_legal_source`, derive `target_reference_center` from the repaired ground legal section. For each floor, transform the authored centroid delta through the global source/target frames and `global_x_scale/global_y_scale`; pass that target center and `global_anisotropy_ratio` to `_matrix_fit_polygon_to_host`. Persist the global relative-pose mode.

In `_matrix_fit_polygon_to_host`, only consider `host.representative_point()` when no explicit `target_center` was supplied. An explicit center must not silently reflow to the host centroid.

- [ ] **Step 4: Run focused geometry tests**

```powershell
python -m pytest design/test_maas_shared_floor_contract.py -q -k "floorwise_legal_stack_samples_exact_authored_mesh_sections or floorwise_visual_projection_preserves_authored_mesh or floorwise_matrix_fit_search_reaches_feasible_target_in_irregular_host"
```

Expected: 3 passed.

- [ ] **Step 5: Commit the isolated geometry regression**

```powershell
git add backend/design/maas/geometry_language/source_bridge.py backend/design/test_maas_shared_floor_contract.py
git commit -m "fix: preserve authored floor pose in legal mass fit"
```

---

### Task 2: Keep Typed Diversity Caps in Target-20 Recovery

**Files:**
- Modify: `backend/design/maas/book_language/portfolio_selection.py`
- Test: `backend/design/test_maas_book_language.py`

**Interfaces:**
- Consumes: `_select(candidates, target=20, allow_diagnostic_fallback=True, ...)`
- Produces: a compatible strict/relaxed subset that retains certified-cluster, operation, seed, section, roof, chassis, concept, phenotype, wedge, pyramidal, and memory-family maximum counts.

- [ ] **Step 1: Change the preview recovery test to require typed caps**

In the existing target-20 diagnostic preview test, replace the empty-map assertion with:

```python
maximum_counts = preview_solver.call_args.kwargs["maximum_key_counts"]
self.assertEqual(maximum_counts["operation:operation_0"], 3)
self.assertEqual(maximum_counts["phenotype:prismatic"], 20)
self.assertTrue(any(key.startswith("certified_mesh_cluster:") for key in maximum_counts))
```

- [ ] **Step 2: Run the test and observe RED**

```powershell
python -m pytest design/test_maas_book_language.py -q -k "target_20_diagnostic_preview"
```

Expected: FAIL because the preview calls `build_joint_payload(..., enforce_typed_caps=False)` and supplies `{}`.

- [ ] **Step 3: Remove cap-free payload construction**

Change both target-20 preview branches to call `build_joint_payload(preview_contract)` with its default `enforce_typed_caps=True`. Do not alter hard gates or set stepped maxima to unlimited in the original strict contract. A partial compatible set must remain partial so replenishment receives the deficit.

- [ ] **Step 4: Run selection tests**

```powershell
python -m pytest design/test_maas_book_language.py -q -k "target_20_diagnostic_preview or competition_portfolio or visible_stepped"
```

Expected: all selected tests pass and the solver receives nonempty typed caps.

- [ ] **Step 5: Commit the selector contract**

```powershell
git add backend/design/maas/book_language/portfolio_selection.py backend/design/test_maas_book_language.py
git commit -m "fix: retain mass diversity caps during target recovery"
```

---

### Task 3: Bind the Competition Brief to Live LLM Authorship

**Files:**
- Modify: `backend/design/maas/book_language/authorship_policy.py`
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Test: `backend/design/test_maas_portfolio_contract.py`
- Test: `backend/design/test_maas_progressive_run_budget.py`

**Interfaces:**
- Consumes: `bounded_live_llm_synthesis_requests(building_type, source_seed_names, target_count, prior_requests) -> tuple[dict, ...]`
- Produces: bounded live-author requests carrying typed architectural strategy tags and a completion contract requiring every selected member to have authored AST identity.

- [ ] **Step 1: Add authorship request tests**

Assert every request for target 20 includes a nonempty `required_architectural_strategies` list containing at least `interlock`, `courtyard`, `void_notch`, `wing`, and `terrace_link`, and includes:

```python
self.assertEqual(request["authorship_completion_policy"], "all_selected_llm_authored")
self.assertEqual(request["legal_authority"], "deterministic_only")
self.assertEqual(request["shape_reference_policy"], "capability_not_template")
```

- [ ] **Step 2: Run authorship tests and observe RED**

```powershell
python -m pytest design/test_maas_portfolio_contract.py design/test_maas_progressive_run_budget.py -q -k "authorship or authored"
```

Expected: FAIL because the strategy and authority fields are absent.

- [ ] **Step 3: Add the typed author brief**

Define an immutable strategy tuple in `authorship_policy.py` and attach it to every bounded synthesis request. Merge prior `intent_tags` without removing the required strategy schedule. In `portfolio_benchmark.py`, persist the effective brief in `program_visual_directive` and continue passing `require_llm_authored_ast=live_llm_author` to completion evaluation.

- [ ] **Step 4: Run authorship and completion tests**

```powershell
python -m pytest design/test_maas_portfolio_contract.py design/test_maas_progressive_run_budget.py -q
```

Expected: all tests pass, including the existing failure when `llm_authored_selected_count < selected_count`.

- [ ] **Step 5: Commit the live-author brief**

```powershell
git add backend/design/maas/book_language/authorship_policy.py backend/design/maas/book_language/portfolio_benchmark.py backend/design/test_maas_portfolio_contract.py backend/design/test_maas_progressive_run_budget.py
git commit -m "feat: bind competition mass brief to LLM authorship"
```

---

### Task 4: Import Codex OAuth Agent-Authored Geometry Programs

**Files:**
- Create: `backend/design/maas/book_language/agent_authored_supply.py`
- Modify: `backend/design/maas/book_language/candidate_analysis.py`
- Modify: `backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `backend/design/maas/agents/maas_geometry_agent/memory/MEMORY.md`
- Test: `backend/design/test_maas_agent_authored_supply.py`

**Interfaces:**
- Consumes: a persisted JSON manifest containing typed GeometryProgram
  payloads authored by the current Codex OAuth LLM session.
- Produces: validated `GeometryProgram` objects with provider
  `codex_oauth_llm_geometry_author`, session/request lineage, and the same
  compiler/gate eligibility as paid-provider LLM programs.

- [ ] **Step 1: Write failing manifest and provenance tests**

Test that procedural programs cannot be relabeled, invalid AST nodes fail
closed, and valid agent-authored payloads preserve provider/session/request
identity. Test `_llm_authored_candidate` recognizes only validated paid-provider
or Codex OAuth author identities.

- [ ] **Step 2: Implement a provider-neutral typed manifest importer**

Reuse the existing GeometryProgram payload parser and compiler validator. Do
not duplicate AST validation and do not accept completed meshes or parcel
coordinates. Bind manifest hash, authoring session ID, request ID, provider,
and program hash into metadata.

- [ ] **Step 3: Wire the manifest into Full BOOK supply**

Add an explicit management/runtime option for the manifest. When supplied,
inject only its validated programs into the LLM-authored pre-BOOK path and
require all final selections to retain their Codex OAuth lineage. Do not fall
back to deterministic authoring under this option.

- [ ] **Step 4: Persist the user contract in MASS memory**

Record: LLM authorship is mandatory; deterministic-only completion is
forbidden; every selected form must preserve UnitBox -> BaseVolume -> global
Matrix4 -> BOOK -> CSG provenance; selected pose fallback count must be zero;
and count 20 may not disable diversity caps.

- [ ] **Step 5: Run focused tests**

Run the new importer tests plus authorship, portfolio-completion, geometry-pose,
and selector-cap tests. Expected: all pass without a paid-provider request.

---

### Task 5: Verify Supply Before the Full Run

**Files:**
- Inspect: `backend/design/maas/book_language/candidate_generation.py`
- Inspect: `backend/design/maas/book_language/portfolio_replenishment.py`
- Inspect: generated probe artifacts under `docs/playwright/design-route-live-verify/`

**Interfaces:**
- Consumes: Django `benchmark_maas_book_program_portfolios` command with live PNU and authored request supply.
- Produces: candidate counts, LLM author stage/failure counts, scope/family supply, pose modes, typed deficits, and renders suitable for a go/no-go decision.

- [ ] **Step 1: Run the focused backend suite**

```powershell
$env:DJANGO_SETTINGS_MODULE='backend.settings'
python -m pytest design/test_maas_shared_floor_contract.py design/test_maas_portfolio_contract.py design/test_maas_progressive_run_budget.py -q -k "floorwise or authorship or authored or portfolio_completion"
```

Expected: all focused tests pass.

- [ ] **Step 2: Run a target-3 progressive live probe**

Load `backend/.env` through the existing Django settings/runtime and run:

```powershell
python manage.py benchmark_maas_book_program_portfolios --program neighborhood --recursive-only --progressive-target 3 --output-dir ../docs/playwright/design-route-live-verify/legal-mass-portfolio-live-probe-v14
```

Expected: live author request executed, 3 LLM-authored selected ASTs, explicit
BaseVolume/Matrix4 provenance, global relative-pose mode only,
`pose_fallback_used=false` for all three, deterministic hard passes, and no
credential/provider failure.

- [ ] **Step 3: Inspect probe evidence and images**

Read `maas-book-programs-summary.json`, `maas-run-state.json`, the combined PNG, and individual candidate renders. Reject the probe if LLM stage counts are zero, any selected pose mode is floorwise centroid reflow, or the three silhouettes collapse to one family.

- [ ] **Step 4: Fix only evidence-backed probe failures**

For a failure, add one failing focused test at the terminal stage named by the persisted evidence, implement the smallest change in that stage, rerun its test, and repeat the target-3 probe. Do not relax a gate to advance.

---

### Task 6: Run and Audit the Final 20

**Files:**
- Generate: `docs/playwright/design-route-live-verify/legal-mass-portfolio-20-final-v14/`
- Verify frontend: `frontend/src/design/components/book-language-flow/`

**Interfaces:**
- Consumes: the verified live-author pipeline and live PNU context.
- Produces: one persisted 20-member portfolio, combined PNG, individual renders, evaluation ledger, exact geometry archive, and `/design/language` evidence UI.

- [ ] **Step 1: Run the full progressive target**

```powershell
python manage.py benchmark_maas_book_program_portfolios --program neighborhood --recursive-only --progressive-target 20 --output-dir ../docs/playwright/design-route-live-verify/legal-mass-portfolio-20-final-v14
```

Expected: command completes without a failed completion gate.

- [ ] **Step 2: Audit machine evidence**

Assert from persisted JSON: selected 20, legal/final hard pass 20, LLM-authored
selected 20, UnitBox/BaseVolume/global-Matrix4 provenance 20, pose fallback 0,
scopes 6/6, measured capacity utilization at least 0.70 for every card,
visible stepped at most 3, body phenotype at most 4 each, no portfolio
violations, no clone/duplicate certificate, and no floorwise reflow pose mode.
Capacity-band labels remain diagnostic evidence and have no exact-count quota.

- [ ] **Step 3: Inspect the combined PNG**

Open `maas-book-neighborhood-20.png` and compare individual renders. Fail acceptance if the board is all or nearly all staircase-like despite label diversity.

- [ ] **Step 4: Verify `/design/language` end to end**

Start the existing backend/frontend dev servers, load `/design/language`, select `MASS PORTFOLIO`, confirm all 20 cards appear together, and verify card identity, status, graph highlight, evidence panel, and preview against the persisted evaluation ledger.

- [ ] **Step 5: Run final regression checks**

Run relevant backend and frontend unit suites plus `git diff --check`. Report exact commands, pass counts, artifact paths, and any remaining non-claim. Do not claim completion when any acceptance item fails.
