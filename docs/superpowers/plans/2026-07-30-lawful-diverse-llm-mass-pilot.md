# Lawful Diverse LLM MASS Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run one real-PNU target-20 portfolio in which every selected MASS descends from a recipe-independent live LLM `GeometryProgram`, passes deterministic geometry/law/capacity/floor/parking gates, and receives exact final-legal image VLM review under a total paid-request ceiling of 20.

**Architecture:** Reuse `benchmark_maas_book_program_portfolios` as the only lawful execution path. Add a pilot policy that removes named-form requirements, restricts final selection to live-LLM lineage, and shares one network-request budget across the geometry author and VLM transports. Review final candidates in exact two-candidate visual pairs, then review the complete 20-card board once; this normally costs one LLM request, ten pair-VLM requests, and one board-VLM request.

**Tech Stack:** Python 3, Django management commands/tests, Shapely, Pillow, existing typed `GeometryProgram` compiler, existing law/parking agents and Neo4j evidence, OpenAI Responses API.

## Global Constraints

- Use real PNU `1168011800104170004` unless the user explicitly changes it.
- One canonical `1/1 UnitBox` / BaseVolume is the only seed authority.
- Production generation must not select recipe IDs or named families.
- Triangular, disc, long-span, stepped, and all other named forms are optional outcomes, never quotas.
- Stepped MASS receives neither a minimum nor a special prohibition; global morphology caps prevent any phenotype from dominating.
- Every selected candidate must be one connected, watertight, manifold MASS.
- Every selected candidate must pass exact real-PNU law, capacity, floor, GFA, BCR/FAR/height, and parking gates.
- Legal projection must preserve authored identity or reject; it may not silently replace non-stepped authorship with generic stepped prisms.
- Every finally accepted candidate must have exact final-legal image-backed VLM evidence.
- The complete selected board must receive a portfolio-level VLM diversity verdict.
- The total count of actual paid network requests across authoring, candidate VLM, portfolio VLM, reference audit, and repair must never exceed 20.
- Cache hits do not consume the paid-request budget.
- Automatic provider retries and post-failure recovery calls are disabled for this pilot.
- No provider call occurs in unit or integration tests.
- Preserve the dirty worktree and do not stage or commit unrelated files.

---

### Task 1: Add one shared paid-provider request ledger

**Files:**
- Create: `ARR/backend/design/maas/paid_provider_budget.py`
- Modify: `ARR/backend/design/maas/geometry_language/llm_adapter.py`
- Modify: `ARR/backend/design/maas/preference/vlm_scorer.py`
- Create: `ARR/backend/design/test_maas_paid_provider_budget.py`

**Interfaces:**
- Produces: `configure_paid_provider_budget(limit: int) -> None`.
- Produces: `reserve_paid_provider_request(kind: str) -> PaidProviderBudgetSnapshot`.
- Produces: `paid_provider_budget_snapshot() -> dict[str, Any]`.
- Produces: `reset_paid_provider_budget_for_tests() -> None`.
- Consumes: `MAAS_PAID_PROVIDER_MAX_REQUESTS`; the pilot command sets an explicit limit no greater than 20.

- [ ] **Step 1: Write ledger exhaustion and per-kind accounting tests**

```python
class PaidProviderBudgetTests(SimpleTestCase):
    def tearDown(self):
        reset_paid_provider_budget_for_tests()

    def test_shared_budget_counts_author_and_vlm_together(self):
        configure_paid_provider_budget(3)
        reserve_paid_provider_request("geometry_author")
        reserve_paid_provider_request("final_pair_vlm")
        reserve_paid_provider_request("portfolio_vlm")
        evidence = paid_provider_budget_snapshot()
        self.assertEqual(evidence["request_count"], 3)
        self.assertEqual(evidence["request_counts_by_kind"], {
            "final_pair_vlm": 1,
            "geometry_author": 1,
            "portfolio_vlm": 1,
        })
        with self.assertRaisesRegex(
            PaidProviderBudgetError,
            "paid_provider_request_budget_exhausted:3/3",
        ):
            reserve_paid_provider_request("repair")
```

- [ ] **Step 2: Run the test and verify the module is missing**

Run:

```powershell
cd ARR/backend
python manage.py test design.test_maas_paid_provider_budget --verbosity 2
```

Expected: FAIL because `design.maas.paid_provider_budget` does not exist.

- [ ] **Step 3: Implement the thread-safe ledger**

```python
@dataclass(frozen=True)
class PaidProviderBudgetSnapshot:
    limit: int
    request_count: int
    request_counts_by_kind: dict[str, int]

def reserve_paid_provider_request(kind: str) -> PaidProviderBudgetSnapshot:
    normalized = str(kind).strip()
    if not normalized:
        raise ValueError("paid provider request kind is required")
    with _LOCK:
        if _STATE.request_count >= _STATE.limit:
            raise PaidProviderBudgetError(
                f"paid_provider_request_budget_exhausted:"
                f"{_STATE.request_count}/{_STATE.limit}"
            )
        _STATE.request_count += 1
        _STATE.request_counts_by_kind[normalized] += 1
        return _STATE.snapshot()
```

The default non-pilot limit may remain 256 for compatibility. Reject explicit
limits below 1 or above 256. `paid_provider_budget_snapshot()` must return
schema `arr.maas.paid_provider_budget.v1`, the configured limit, total count,
remaining count, and sorted per-kind counts.

- [ ] **Step 4: Reserve only immediately before real HTTP transport**

In `author_geometry_programs_with_openai`, reserve
`geometry_author` after a cache miss and immediately before `urlopen`.

In `vlm_scorer`, replace the independent process counter with delegation:

```python
def _consume_live_vlm_request_budget(kind: str = "vlm") -> int:
    snapshot = reserve_paid_provider_request(kind)
    return snapshot.request_count
```

Pass explicit kinds from the portfolio, reference-audit, single-candidate, and
new pair transports. Do not reserve for cache hits.

- [ ] **Step 5: Prove cache hits consume zero requests**

Patch `urlopen`, call the author twice with an exact saved cache, and assert
`request_count == 1`. Repeat for one VLM cache key.

- [ ] **Step 6: Run focused transport tests**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_paid_provider_budget `
  design.test_maas_geometry_language `
  design.test_maas_book_language --verbosity 1
```

Expected: PASS with zero real HTTP requests.

- [ ] **Step 7: Commit only Task 1 files**

```powershell
git add -- ARR/backend/design/maas/paid_provider_budget.py `
  ARR/backend/design/maas/geometry_language/llm_adapter.py `
  ARR/backend/design/maas/preference/vlm_scorer.py `
  ARR/backend/design/test_maas_paid_provider_budget.py
git commit -m "feat(maas): bound shared paid provider requests"
```

### Task 2: Remove named-form requirements while retaining outcome diversity

**Files:**
- Modify: `ARR/backend/design/maas/book_language/competition_portfolio_contract.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `ARR/backend/design/maas/preference/vlm_scorer.py`
- Modify: `ARR/backend/design/test_maas_book_language.py`
- Modify: `ARR/backend/design/test_maas_portfolio_contract.py`

**Interfaces:**
- Consumes: existing `CompetitionPortfolioContract`.
- Produces: form-neutral target contracts with morphology minima, pair-distance floors, and per-phenotype maxima but no named-form presence rule.
- Produces: portfolio VLM feedback containing typed relational guidance, never a required named family.

- [ ] **Step 1: Replace stepped-presence tests with stepped-neutral tests**

Add tests that target 10 and target 20 both have:

```python
self.assertEqual(contract.visible_stepped_minimum, 0)
self.assertIsNone(contract.visible_stepped_maximum)
self.assertEqual(contract.upper_band_stepped_minimum, 0)
self.assertEqual(contract.upper_band_stepped_bands, ())
```

Keep assertions for `body_phenotype_maximum_each`, minimum distinct
morphologies, roof/chassis/plan distinctness, and pair-distance floors.

- [ ] **Step 2: Add a regression proving zero stepped candidates can pass**

Replace `test_joint_ten_card_solver_rejects_zero_stepped_candidates` with a
fixture containing ten legal candidates that meet global morphology and
capacity constraints but contain zero stepped candidates. Assert the joint
solver does not fail solely for missing stepped MASS.

- [ ] **Step 3: Run the focused tests and confirm the old minima fail**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_portfolio_contract `
  design.test_maas_book_language.MaasBookLanguageRegistryTest.test_joint_ten_card_solver_allows_zero_stepped_candidates `
  --verbosity 2
```

Expected: FAIL because target 10/20 still require a stepped candidate.

- [ ] **Step 4: Remove special stepped minima and maxima**

Set the stepped-specific fields to zero/`None` for targets 3, 10, and 20.
Do not weaken global `body_phenotype_maximum_each`,
`roof_archetype_maximum_each`, `chassis_family_maximum_each`,
`plan_family_maximum_each`, or pair-distance thresholds.

- [ ] **Step 5: Remove the hard-coded triangular requirement**

Delete:

```python
program_visual_directive.setdefault(
    "required_plan_families",
    ["triangular"],
)
```

When the lawful pilot is active, also ignore historic
`required_geometry_program_families`, `required_chassis_families`, and
`required_plan_families` directives. Preserve negative memory, typed relation
guidance, and morphology caps.

- [ ] **Step 6: Remove input-method coverage gates from the pilot only**

The pilot must not require ten distinct BOOK operation IDs or every available
BOOK principle kind. Skip `book_operation_count_below_10` and
`available_book_principle_kind_missing_from_portfolio` only when
`lawful_diverse_llm_pilot=True`. Keep the compiled output morphology,
silhouette, topology, capacity-band, legal, parking, pair-distance, and VLM
gates unchanged.

- [ ] **Step 7: Make portfolio VLM feedback relation-only**

Remove `required_geometry_families` from the portfolio VLM response schema and
prompt. Keep `required_next_relations`, repeated groups, candidate actions,
visible morphology count, dominant share, and rationale.

The prompt must say:

```text
Named forms are descriptions only. Do not require triangular, disc, long-span,
stepped, or any other named form. Fail only for visible repetition, weak
architectural organization, or insufficient material diversity.
```

- [ ] **Step 8: Run selection and portfolio VLM tests**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_portfolio_contract `
  design.test_maas_book_language `
  --verbosity 1
```

Expected: PASS; no test requires a named form to exist.

- [ ] **Step 9: Commit only Task 2 files**

```powershell
git add -- ARR/backend/design/maas/book_language/competition_portfolio_contract.py `
  ARR/backend/design/maas/book_language/portfolio_benchmark.py `
  ARR/backend/design/maas/preference/vlm_scorer.py `
  ARR/backend/design/test_maas_book_language.py `
  ARR/backend/design/test_maas_portfolio_contract.py
git commit -m "fix(maas): make portfolio diversity form neutral"
```

### Task 3: Make target-20 selection entirely live-LLM authored

**Files:**
- Create: `ARR/backend/design/maas/book_language/lawful_diverse_pilot.py`
- Modify: `ARR/backend/design/maas/book_language/authorship_policy.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_contract.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `ARR/backend/design/test_maas_portfolio_contract.py`
- Create: `ARR/backend/design/test_maas_lawful_diverse_pilot.py`

**Interfaces:**
- Produces: `LawfulDiversePilotPolicy`.
- Produces: `lawful_diverse_selection_pool(candidates: Sequence[_Candidate]) -> list[_Candidate]`.
- Extends: `evaluate_portfolio_completion(..., require_all_selected_llm_authored_ast: bool = False)`.
- Extends: `run_book_program_portfolios(..., lawful_diverse_llm_pilot: bool = False)`.

- [ ] **Step 1: Write pilot policy tests**

```python
def test_lawful_pilot_has_no_named_form_requirements(self):
    policy = LawfulDiversePilotPolicy()
    self.assertEqual(policy.target_count, 20)
    self.assertEqual(policy.required_named_forms, ())
    self.assertTrue(policy.require_all_selected_llm_authored_ast)
    self.assertEqual(policy.paid_provider_request_ceiling, 20)
    self.assertFalse(policy.allow_automatic_retry)
```

- [ ] **Step 2: Write selection fail-closed tests**

Build three candidates: two with
`author_provider=openai_llm_geometry_author`, one deterministic fixture. Assert
the pilot selection pool contains only the two authored candidates. Assert a
requested target of three fails instead of filling from the fixture.

- [ ] **Step 3: Write completion tests requiring all selected candidates to be authored**

```python
evidence = evaluate_portfolio_completion(
    requirement,
    selected_count=20,
    selected_scope_count=6,
    runtime_live_vlm=True,
    exact_vlm_hard_pass_count=20,
    require_llm_authored_ast=True,
    require_all_selected_llm_authored_ast=True,
    llm_authored_selected_count=19,
    portfolio_vlm_audit={"evaluated": True, "hard_pass": True},
)
self.assertIn(
    "selected_non_llm_authored_ast_present",
    evidence["failures"],
)
```

- [ ] **Step 4: Run tests and verify current additive author lane fails**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_lawful_diverse_pilot `
  design.test_maas_portfolio_contract --verbosity 2
```

Expected: FAIL because the policy and all-authored completion flag do not exist.

- [ ] **Step 5: Raise one batch author count from 12 to 20**

Set:

```python
MAX_LIVE_LLM_AUTHORED_PROGRAMS = 20
```

Keep `bounded_live_llm_synthesis_requests` at exactly one synthesis request.
The geometry author adapter already sends up to 20 ASTs in one structured
Responses request. Do not loop one request per candidate.

- [ ] **Step 6: Filter the final pilot universe by authored lineage**

In the pilot path, filter after geometry/program/legal/parking hard gates and
before final portfolio selection:

```python
if lawful_diverse_llm_pilot:
    selection_pool = lawful_diverse_selection_pool(selection_pool)
```

Do not filter before hard gates, and do not grant authored candidates a pass or
score bonus. Deterministic candidates may remain diagnostic controls but can
never fill the final pilot board.

- [ ] **Step 7: Enforce all-authored completion**

Pass `require_all_selected_llm_authored_ast=True` only for the pilot. Record:

```json
{
  "authoring_mode": "live_llm_geometry_program_batch",
  "selected_llm_authored_count": 20,
  "selected_non_llm_authored_count": 0,
  "recipe_selection_used": false
}
```

- [ ] **Step 8: Run focused generation tests**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_lawful_diverse_pilot `
  design.test_maas_portfolio_contract `
  design.test_maas_geometry_language --verbosity 1
```

Expected: PASS with provider transports mocked.

- [ ] **Step 9: Commit only Task 3 files**

```powershell
git add -- ARR/backend/design/maas/book_language/lawful_diverse_pilot.py `
  ARR/backend/design/maas/book_language/authorship_policy.py `
  ARR/backend/design/maas/book_language/portfolio_contract.py `
  ARR/backend/design/maas/book_language/portfolio_benchmark.py `
  ARR/backend/design/test_maas_portfolio_contract.py `
  ARR/backend/design/test_maas_lawful_diverse_pilot.py
git commit -m "feat(maas): require all-authored lawful pilot portfolios"
```

### Task 4: Review exact final-legal candidates in bounded VLM pairs

**Files:**
- Create: `ARR/backend/design/maas/preference/paired_vlm_scorer.py`
- Create: `ARR/backend/design/maas/book_language/paired_final_vlm_review.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_contract.py`
- Create: `ARR/backend/design/test_maas_paired_final_vlm_review.py`
- Modify: `ARR/backend/design/test_maas_portfolio_contract.py`

**Interfaces:**
- Produces: `FinalLegalVlmItem(candidate_id, pnu, program_hash, geometry_hash, image_path)`.
- Produces: `review_final_legal_candidate_pairs(items, output_dir, scorer=None) -> dict[str, Any]`.
- Produces: `score_final_legal_pair_with_openai_vlm(left, right, pair_image_path, model=None) -> dict[str, Any]`.
- Consumes: exact selected candidate features after legal/parking finalization.

- [ ] **Step 1: Write pair partition and odd-tail tests**

For 20 items, assert 10 pairs. For 19 items, assert 9 pairs plus one single.
Every item must appear exactly once.

- [ ] **Step 2: Write exact identity and response-binding tests**

The mock scorer returns one response ID and two verdicts. Assert each candidate
record contains its own PNU/program/geometry hash, the shared response ID,
pair-image SHA-256, `cache_hit`, concept scores, critic actions, and hard pass.

Reject missing, duplicate, reordered-with-wrong-ID, or extra candidate verdicts.

- [ ] **Step 3: Write fail-closed transport tests**

If a pair call fails, both candidates receive `status=call_failed` and
`hard_pass=false`. No recovery call occurs. If the shared budget is exhausted,
remaining candidates are `not_reviewed_budget_exhausted`, never accepted.

- [ ] **Step 4: Run tests and verify the pair modules are missing**

Run:

```powershell
cd ARR/backend
python manage.py test design.test_maas_paired_final_vlm_review --verbosity 2
```

Expected: FAIL because the pair reviewer does not exist.

- [ ] **Step 5: Render legible exact-final pair images**

Render each finalized candidate from its exact final legal feature into a
four-view PNG. Compose two labeled panels into one 1536x768 PNG with Pillow.
The label contains only candidate ID and short hash prefixes; legal values stay
in structured text.

Before composing, verify the rendered feature's
`finalLegalGeometryHash` equals the item's geometry hash. Reject mismatch
without calling the provider.

- [ ] **Step 6: Implement strict two-verdict Responses schema**

The schema requires exactly one verdict for every submitted candidate ID:

```json
{
  "candidate_verdicts": [
    {
      "candidate_id": "string",
      "hard_pass": true,
      "architectural_coherence": 0.0,
      "program_fit": 0.0,
      "spatial_legibility": 0.0,
      "silhouette_integrity": 0.0,
      "critic_actions": ["string"],
      "rationale": "string"
    }
  ],
  "pair_rationale": "string"
}
```

The prompt states that named forms are optional, law is already decided
elsewhere, and the critic judges only the exact visible architectural result.
Reserve one `final_pair_vlm` request immediately before HTTP. Use no retry.

- [ ] **Step 7: Integrate pair review after final legal rendering**

For the pilot only:

1. Skip the earlier per-candidate final-book live transport.
2. Select 20 from the all-authored, exact-law/parking hard-pass universe.
3. Render/finalize identities.
4. Run ten pair reviews.
5. Attach each verdict to candidate metadata, row, passport VLM stage, and
   outcome graph.
6. Count exact candidate hard passes from pair evidence.
7. Run the existing complete-board portfolio VLM once.

Non-pilot behavior remains unchanged.

- [ ] **Step 8: Disable hidden paid reference audits and recovery**

The pilot pair critic uses only already-persisted, already-audited cached
reference metadata or no reference. It must not trigger new reference-image
audit calls. Set the pilot evidence fields:

```json
{
  "reference_policy": "cached_only_no_live_reference_audit",
  "automatic_retry_count": 0,
  "recovery_request_count": 0
}
```

- [ ] **Step 9: Require pair hard pass for every accepted card**

The pilot completion gate requires:

```python
exact_vlm_hard_pass_count == selected_count == 20
```

The board-level portfolio audit must also be `evaluated=true` and
`hard_pass=true`. One candidate failure makes the portfolio fail without
removing the evidence.

- [ ] **Step 10: Run pair, completion, and rendering tests**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_paired_final_vlm_review `
  design.test_maas_portfolio_contract `
  design.test_maas_book_language --verbosity 1
```

Expected: PASS with zero live provider requests.

- [ ] **Step 11: Commit only Task 4 files**

```powershell
git add -- ARR/backend/design/maas/preference/paired_vlm_scorer.py `
  ARR/backend/design/maas/book_language/paired_final_vlm_review.py `
  ARR/backend/design/maas/book_language/portfolio_benchmark.py `
  ARR/backend/design/maas/book_language/portfolio_contract.py `
  ARR/backend/design/test_maas_paired_final_vlm_review.py `
  ARR/backend/design/test_maas_portfolio_contract.py
git commit -m "feat(maas): add bounded paired final VLM review"
```

### Task 5: Expose one fail-closed lawful pilot command

**Files:**
- Modify: `ARR/backend/design/management/commands/benchmark_maas_book_program_portfolios.py`
- Modify: `ARR/backend/design/maas/book_language/portfolio_benchmark.py`
- Modify: `ARR/backend/design/test_maas_flow_regressions.py`
- Modify: `ARR/backend/design/test_maas_lawful_diverse_pilot.py`

**Interfaces:**
- Adds CLI: `--lawful-diverse-llm-pilot`.
- Adds CLI: `--paid-request-cap` with pilot default and maximum 20.
- Requires exactly one `--program` for the first bounded paid pilot.
- Produces: `maas-lawful-diverse-pilot-manifest.json`.

- [ ] **Step 1: Write CLI validation tests**

Assert the pilot rejects:

- no `--program`;
- more than one `--program`;
- `--diagnostic-target`;
- `--smoke`;
- `--paid-request-cap` above 20;
- missing live opt-in or API key;
- an existing non-empty output directory.

Each failure must occur before a provider transport.

- [ ] **Step 2: Write a mocked full-flow command test**

Mock VWorld, land/regulation services, law evidence, one 20-program author
response, ten pair VLM responses, and one board VLM response. Assert:

```python
self.assertEqual(manifest["selected_count"], 20)
self.assertEqual(manifest["selected_llm_authored_count"], 20)
self.assertEqual(manifest["selected_non_llm_authored_count"], 0)
self.assertEqual(manifest["paid_provider_budget"]["request_count"], 12)
self.assertLessEqual(manifest["paid_provider_budget"]["request_count"], 20)
self.assertTrue(manifest["all_selected_legal_hard_pass"])
self.assertTrue(manifest["all_selected_parking_hard_pass"])
self.assertTrue(manifest["all_selected_pair_vlm_hard_pass"])
self.assertTrue(manifest["portfolio_vlm_audit"]["hard_pass"])
```

- [ ] **Step 3: Run tests and verify the CLI flag is missing**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_lawful_diverse_pilot `
  design.test_maas_flow_regressions --verbosity 2
```

Expected: FAIL because `--lawful-diverse-llm-pilot` is unsupported.

- [ ] **Step 4: Implement command preflight**

The pilot flag is the explicit paid-action authorization. It implies
`live_llm_author=True`, `live_vlm=True`, target 20, all-authored selection, pair
review, and board review.

Require:

```text
MAAS_LIVE_GEOMETRY_VLM
MAAS_LIVE_VLM_CREDENTIAL_ROTATED
OPENAI_API_KEY
```

Configure the shared budget before PNU fetch. Force:

```text
MAAS_PREFERENCE_VLM_RETRIES=0
pair recovery disabled
reference audit live calls disabled
```

Do not print secret values.

- [ ] **Step 5: Persist one truthful manifest**

Include:

- PNU and program;
- run directory and timestamps;
- law, capacity, floor, GFA, BCR/FAR/height, and parking gate summaries;
- author response IDs and cache-hit flags;
- 20 candidate IDs and all identity hashes;
- pair composition and pair VLM response IDs;
- board VLM response ID;
- paid budget limit, total, remaining, and per-kind counts;
- selected morphology distributions and minimum pair distance;
- exact failure reasons;
- `recipe_selection_used=false`;
- `named_form_quota_used=false`;
- `automatic_retry_count=0`.

- [ ] **Step 6: Run command and flow tests**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_lawful_diverse_pilot `
  design.test_maas_paid_provider_budget `
  design.test_maas_paired_final_vlm_review `
  design.test_maas_flow_regressions --verbosity 1
```

Expected: PASS with zero external network calls.

- [ ] **Step 7: Commit only Task 5 files**

```powershell
git add -- ARR/backend/design/management/commands/benchmark_maas_book_program_portfolios.py `
  ARR/backend/design/maas/book_language/portfolio_benchmark.py `
  ARR/backend/design/test_maas_flow_regressions.py `
  ARR/backend/design/test_maas_lawful_diverse_pilot.py
git commit -m "feat(maas): expose lawful diverse LLM pilot"
```

### Task 6: Run offline regression and artifact contract verification

**Files:**
- Modify only if a verified regression belongs to this feature.

**Interfaces:**
- Consumes: the completed pilot path with provider transports mocked.
- Produces: exact test evidence before any paid run.

- [ ] **Step 1: Run focused backend tests**

Run:

```powershell
cd ARR/backend
python manage.py test `
  design.test_maas_paid_provider_budget `
  design.test_maas_lawful_diverse_pilot `
  design.test_maas_paired_final_vlm_review `
  design.test_maas_portfolio_contract `
  design.test_maas_agent_collaboration `
  design.test_maas_book_language `
  design.test_maas_flow_regressions `
  design.test_maas_geometry_language --verbosity 1
```

Record exact counts and failures. Do not proceed to a paid call if a new
failure touches authoring, identity, law, parking, diversity, rendering, VLM,
or budget enforcement.

- [ ] **Step 2: Run Django validation**

Run:

```powershell
cd ARR/backend
python manage.py check
```

Expected: `System check identified no issues`.

- [ ] **Step 3: Run one fully mocked target-20 artifact audit**

Parse the summary, pilot manifest, 20 candidate passports, pair review records,
board audit, and outcome graph. Verify every relative path remains inside the
run directory and every SHA-256 matches its file.

- [ ] **Step 4: Confirm zero paid requests occurred**

The offline artifact must state:

```json
{
  "provider_transport_mode": "mocked",
  "live_paid_request_count": 0
}
```

- [ ] **Step 5: Commit only verified regression fixes**

If no feature-owned regression exists, create no commit for this task.

### Task 7: Run one bounded live PNU pilot and checkpoint exact truth

**Files:**
- Modify: `docs/ai-session-memory/MAAS_LAWFUL_DIVERSE_LLM_PILOT_20260730.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`

**Interfaces:**
- Consumes: explicit user authorization already given for a bounded pilot.
- Produces: one immutable live run with a hard paid-request ceiling of 20.

- [ ] **Step 1: Run read-only credential and service preflight**

Verify only presence/status, never values:

- `OPENAI_API_KEY` is set;
- VWorld and land regulation fetches return executable PNU data;
- law Neo4j and law-domain service are available;
- output directory does not exist or is empty;
- workstation memory is sufficient for target 20.

Stop before provider calls if any preflight fails.

- [ ] **Step 2: Start one live run**

Run from `ARR/backend`:

```powershell
$env:MAAS_LIVE_GEOMETRY_VLM='1'
$env:MAAS_LIVE_VLM_CREDENTIAL_ROTATED='1'
$env:MAAS_PAID_PROVIDER_MAX_REQUESTS='20'
$env:MAAS_PREFERENCE_VLM_RETRIES='0'
python manage.py benchmark_maas_book_program_portfolios `
  --pnu 1168011800104170004 `
  --program neighborhood `
  --output-dir ../../docs/mass/maas-lawful-diverse-llm-pilot-20260730 `
  --lawful-diverse-llm-pilot `
  --paid-request-cap 20
```

Do not run a second live command after failure without examining the persisted
budget and asking the user if additional paid requests would be required.

- [ ] **Step 3: Monitor the budget and fail closed**

At every persisted phase, confirm request count is at most 20. A budget
exhaustion is a truthful failed pilot, not permission to raise the cap or
switch to fixture recipes.

- [ ] **Step 4: Audit the live result**

Verify:

- every selected candidate is LLM-authored;
- every selected candidate has one canonical UnitBox lineage;
- every selected candidate is connected, watertight, and manifold;
- all law/capacity/floor/GFA/BCR/FAR/height/parking gates pass;
- non-stepped authorship was not silently replaced with stepped prisms;
- all 20 selected candidates have exact pair-VLM evidence;
- the complete board VLM saw exactly 20 candidates;
- global morphology and pair-distance contracts pass;
- no named form was required;
- response IDs, usage, cache flags, and request totals are present.

- [ ] **Step 5: Inspect the final board and representative four-view images**

Use direct image inspection. Confirm the board is not visually collapsed into
one stepped, box/bar, roof, or near-duplicate language. This inspection is
evidence, not a replacement for the VLM or numeric gates.

- [ ] **Step 6: Update durable memory with exact result**

Record run path, status, selected count, legal/parking counts, morphology
distribution, minimum distance, author/VLM response IDs, cache hits, exact paid
request count, VLM failures, board screenshot, tests, and unresolved limits.
Never convert a failed or partially reviewed pilot into acceptance language.

- [ ] **Step 7: Run final JSON and hash verification**

Parse all modified JSON files and rerun the focused tests from Task 6. Confirm
the checkpoint's counts match the live manifest.

- [ ] **Step 8: Commit only the final memory checkpoint**

```powershell
git add -- docs/ai-session-memory/MAAS_LAWFUL_DIVERSE_LLM_PILOT_20260730.md `
  docs/ai-session-memory/maas-mass-flow/current-checkpoint.json `
  docs/ai-session-memory/maas-mass-flow/CHANGELOG.md
git commit -m "docs(maas): checkpoint lawful diverse live pilot"
```
