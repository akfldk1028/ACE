# Multi-View Elevation Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate four identity-bound creative facade views for one compiled MASS, reject cross-view contradictions with deterministic and multimodal gates, expose the accepted evidence in the existing MASS passport/graph/frontend, and prove the flow on r230 MASS 03 before attempting MASS 04.

**Architecture:** Keep the six deterministic mesh projections as geometry authority and add a separate `multi-view-alt-01` proposal derived from the four orthographic facade projections. Each facade view is one bounded `gpt-image-2` edit with an exact post-composite silhouette lock; a deterministic gate runs before a single four-image Responses API critic, and only failed views may be regenerated once. The accepted proposal is written atomically into the existing passport and activation graph, then rendered by the existing MASS evidence panel without creating a second authority graph.

**Tech Stack:** Python 3, Django, Pillow, OpenAI Python SDK `>=1.50` (installed `1.109.1`), `gpt-image-2` Image Edits API, Responses API structured outputs, React 18, TypeScript, Vitest, Testing Library, Vite web mode.

## Global Constraints

- The immutable identity is exactly `execution_id + program_hash + geometry_hash`; every creative artifact also carries exactly one of `front`, `right`, `back`, `left`.
- The deterministic `top` and `axon` images remain technical evidence and are never replaced by generated creative images.
- The creative output directory is `elevation/proposals/multi-view-alt-01/`; its manifest is `proposal.json`, view images are `<view>.png`, the critic montage is `critic-montage.png`, and critic evidence is `critic.json`.
- Per MASS, the paid ceiling is four initial image calls plus one critic call, at most four one-time failed-view repair calls plus one final critic call: at most 10 paid calls and zero transport retries.
- A provider exception is recorded as a failed paid attempt; it is never retried by the transport adapter.
- An existing manifest is reusable only when its execution/program/geometry identity, source-view SHA-256 values, strategy SHA-256, and accepted status all match.
- A proposal can be `accepted` only when all four required views exist, all deterministic checks pass, and the joint critic returns `pass`.
- Generated pixels outside the locked MASS mask must equal the deterministic source pixels exactly after post-composite.
- The current MASS activation graph remains the sole causal graph; accepted edges activate only after both gates pass.
- Existing 2026-07-24 backend files are uncommitted user work. Never use broad staging; stage only the exact files listed by the current task and inspect `git diff --cached` before every commit.
- Run the frontend only with `npm run dev -- --host 127.0.0.1`; never launch bare `vite` or Electron.
- Full repository suites have known historical failures. Report focused MASS results separately from global-suite baseline and never describe the entire repository as green unless it actually is.
- Execute r230 MASS 03 first: `r230-radial-roof-render-03-radial-cross`. Execute MASS 04 only after MASS 03 is accepted or its bounded repair budget is exhausted with complete evidence.

---

## File Structure

- Create `backend/design/maas/agents/elevation_agent/multi_view_contract.py`: immutable view names, proposal identity, provider/critic protocols, and serializable result types.
- Create `backend/design/maas/agents/elevation_agent/multi_view_consistency.py`: deterministic source/output identity, dimension, silhouette, floor-guide, extent, and adjacent-corner checks.
- Create `backend/design/maas/agents/elevation_agent/multi_view_proposal.py`: idempotent four-view generation, montage construction, gate ordering, failed-view repair budget, and atomic manifest persistence.
- Create `backend/design/maas/aesthetic/adapters/openai_elevation_critic.py`: one Responses API multi-image structured-output call with request/usage evidence and no retry.
- Modify `backend/design/maas/aesthetic/adapters/openai_image.py`: support a single locked orthographic elevation reference and exact output composite while preserving the legacy sheet path.
- Modify `backend/design/maas/agents/elevation_agent/__init__.py`: export the new contracts and orchestrator.
- Modify `backend/design/maas/elevation_proposal_batch.py`: load and validate an existing execution, call the multi-view orchestrator, and persist passport/execution evidence.
- Modify `backend/design/maas/geometry_language/execution_activation.py`: add or refresh multi-view generator, deterministic gate, critic, and accepted proposal nodes in the existing graph.
- Modify `backend/design/management/commands/generate_maas_elevation_proposals.py`: add an explicit `--mode multi-view` and `--execution-id` path while preserving the existing batch command.
- Modify `backend/design/urls.py` and `backend/design/views.py`: serve allow-listed multi-view images, montage, and JSON evidence.
- Modify `backend/design/test_maas_elevation_agent.py`: focused backend contracts, adapter behavior, budgeting, idempotency, graph, and HTTP tests.
- Create `frontend/src/design/components/book-language-flow/multi-view-elevation.ts`: strict identity-bound evidence extraction.
- Create `frontend/src/design/components/book-language-flow/MultiViewElevationEvidence.tsx`: four-view creative facade grid and consistency report.
- Modify `frontend/src/design/lib/language-system-types.ts`, `ExecutedMassEvidence.tsx`, `book-language-flow.css`, and focused tests to display creative and technical evidence distinctly.

### Task 1: Multi-View Contracts and Deterministic Gate

**Files:**
- Create: `backend/design/maas/agents/elevation_agent/multi_view_contract.py`
- Create: `backend/design/maas/agents/elevation_agent/multi_view_consistency.py`
- Modify: `backend/design/maas/agents/elevation_agent/__init__.py`
- Test: `backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: elevation bundle dictionaries from `generate_elevation_bundle(compilation, output_root, execution_id=execution_id)`.
- Produces: `FACADE_VIEWS`, `MultiViewCritic`, `evaluate_multi_view_consistency(bundle, artifacts) -> dict[str, Any]`, and `proposal_identity(bundle) -> dict[str, str]`.

- [ ] **Step 1: Write failing contract and gate tests**

```python
def test_multi_view_gate_requires_exact_identity_and_four_facades(self):
    result = evaluate_multi_view_consistency(
        bundle,
        {
            "front": artifact("front", identity=bundle_identity),
            "right": artifact("right", identity=bundle_identity),
            "back": artifact("back", identity=bundle_identity),
        },
    )
    self.assertEqual(result["status"], "failed")
    self.assertEqual(result["failed_views"], ["left"])
    self.assertIn("missing_required_view", issue_codes(result))

def test_multi_view_gate_rejects_pixels_changed_outside_locked_mask(self):
    changed = make_generated_view(source_front, outside_pixel=(0, 0))
    result = evaluate_multi_view_consistency(
        bundle,
        complete_artifacts(front_path=changed),
    )
    self.assertEqual(result["status"], "failed")
    self.assertIn("outside_mask_changed", issue_codes(result))
```

- [ ] **Step 2: Run the two tests and verify RED**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests.test_multi_view_gate_requires_exact_identity_and_four_facades design.test_maas_elevation_agent.MaasElevationAgentTests.test_multi_view_gate_rejects_pixels_changed_outside_locked_mask -v 2`

Expected: import failure for `evaluate_multi_view_consistency`.

- [ ] **Step 3: Implement exact contracts and deterministic checks**

```python
FACADE_VIEWS = ("front", "right", "back", "left")

class MultiViewCritic(Protocol):
    name: str
    def evaluate(
        self,
        *,
        identity: Mapping[str, str],
        strategy: Mapping[str, Any],
        artifacts: Mapping[str, Mapping[str, Any]],
        montage_path: Path,
    ) -> dict[str, Any]:
        raise NotImplementedError

def proposal_identity(bundle: Mapping[str, Any]) -> dict[str, str]:
    identity = {
        "execution_id": str(bundle.get("execution_id") or ""),
        "program_hash": str(bundle.get("program_hash") or ""),
        "geometry_hash": str(bundle.get("geometry_hash") or ""),
    }
    if not all(identity.values()):
        raise ValueError("multi-view proposal requires complete execution identity")
    return identity
```

`evaluate_multi_view_consistency` must emit:

```python
{
    "schema_version": "arr.elevation_agent.multi_view_gate.v1",
    "status": "passed" | "failed",
    "required_views": list(FACADE_VIEWS),
    "failed_views": ["left"],
    "checks": {
        view: {
            "identity_match": bool,
            "source_sha256_match": bool,
            "dimensions_match": bool,
            "outside_mask_changed_pixels": int,
            "silhouette_registration_iou": float,
            "floor_guide_alignment_px": float,
            "facade_extent_match": bool,
        }
    },
    "corner_checks": [
        {"views": ["front", "right"], "height_delta_px": int, "status": "passed" | "failed"},
        {"views": ["right", "back"], "height_delta_px": 0, "status": "passed"},
        {"views": ["back", "left"], "height_delta_px": 0, "status": "passed"},
        {"views": ["left", "front"], "height_delta_px": 0, "status": "passed"},
    ],
    "issues": [{"code": str, "view": str, "message": str}],
}
```

Use source image background sampling plus the existing `is_mass_color` rule to derive the editable silhouette. Require equal image dimensions, SHA-bound source artifacts, zero outside-mask changes, silhouette IoU `>= 0.995`, floor-guide alignment `<= 2 px`, and adjacent facade height delta `<= 2 px`.

- [ ] **Step 4: Run all deterministic gate tests and verify GREEN**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests -k multi_view_gate -v 2`

Expected: all `multi_view_gate` tests pass.

- [ ] **Step 5: Commit only Task 1 files**

```powershell
git add -- backend/design/maas/agents/elevation_agent/multi_view_contract.py backend/design/maas/agents/elevation_agent/multi_view_consistency.py backend/design/maas/agents/elevation_agent/__init__.py backend/design/test_maas_elevation_agent.py
git diff --cached --check
git commit -m "feat: add deterministic multi-view elevation gate"
```

### Task 2: Single-View GPT Image Edit With Exact Silhouette Lock

**Files:**
- Modify: `backend/design/maas/aesthetic/adapters/openai_image.py`
- Test: `backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: `RenderedReference.metadata.reference_type == "locked_elevation_view"` and `metadata.view`.
- Produces: one `ProviderResult` whose metadata includes `view`, source/mask/provider/output hashes, `request_id`, usage, `retry_count: 0`, and outside-mask composite evidence.

- [ ] **Step 1: Write failing adapter tests**

```python
def test_openai_locked_elevation_view_uses_one_edit_without_input_fidelity(self):
    result = adapter.generate(job_for("front"), locked_reference("front"))
    request = fake_images.requests[0]
    self.assertEqual(request["model"], "gpt-image-2")
    self.assertNotIn("input_fidelity", request)
    self.assertEqual(len(fake_images.requests), 1)
    self.assertEqual(result.metadata["view"], "front")
    self.assertEqual(result.metadata["retry_count"], 0)

def test_locked_elevation_composite_preserves_every_outside_mask_pixel(self):
    result = composite_locked_elevation_output(generated, source, mask)
    self.assertEqual(result["outside_mask_changed_pixels"], 0)
    self.assertTrue(result["post_composite_silhouette_lock"])
```

- [ ] **Step 2: Run adapter tests and verify RED**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests.test_openai_locked_elevation_view_uses_one_edit_without_input_fidelity design.test_maas_elevation_agent.MaasElevationAgentTests.test_locked_elevation_composite_preserves_every_outside_mask_pixel -v 2`

Expected: missing locked-elevation branch/helper.

- [ ] **Step 3: Implement locked orthographic view behavior**

For `locked_elevation_view`, prepare a square image without changing the projection, write a mask whose transparent pixels are only MASS pixels, call `client.images.edit` once with `model`, `image`, `mask`, `prompt`, `size`, and `n`, and run the exact post-composite before hashing. The prompt must name the current view and repeat the shared facade strategy while forbidding camera, silhouette, roofline, floor-count, setback, void, bridge, and cantilever changes.

The metadata must include:

```python
{
    "view": view,
    "model": model,
    "request_id": request_id,
    "usage": usage,
    "retry_count": 0,
    "source_view_sha256": source_hash,
    "edit_mask_sha256": mask_hash,
    "provider_input_image_sha256": provider_input_hash,
    "output_image_sha256": output_hash,
    "post_composite_silhouette_lock": True,
    "outside_mask_changed_pixels": 0,
}
```

- [ ] **Step 4: Run legacy and new adapter tests**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests -k "openai or locked" -v 2`

Expected: legacy sheet tests and new single-view tests pass.

- [ ] **Step 5: Commit Task 2 files**

```powershell
git add -- backend/design/maas/aesthetic/adapters/openai_image.py backend/design/test_maas_elevation_agent.py
git diff --cached --check
git commit -m "feat: generate locked orthographic facade views"
```

### Task 3: Joint Four-Image Structured Critic

**Files:**
- Create: `backend/design/maas/aesthetic/adapters/openai_elevation_critic.py`
- Modify: `backend/design/maas/aesthetic/adapters/__init__.py`
- Test: `backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: `MultiViewCritic.evaluate(identity=identity, strategy=strategy, artifacts=artifacts, montage_path=montage_path)`.
- Produces: `arr.elevation_agent.multi_view_critic.v1` evidence with `status`, `failed_views`, typed issues, response/request IDs, token usage, and `retry_count: 0`.

- [ ] **Step 1: Write a failing structured critic test**

```python
def test_openai_multi_view_critic_submits_four_images_once_and_parses_schema(self):
    evidence = critic.evaluate(
        identity=identity,
        strategy=strategy,
        artifacts=complete_artifacts(),
        montage_path=montage,
    )
    content = fake_responses.requests[0]["input"][0]["content"]
    self.assertEqual(sum(part["type"] == "input_image" for part in content), 4)
    self.assertEqual(fake_responses.requests[0]["text"]["format"]["type"], "json_schema")
    self.assertTrue(fake_responses.requests[0]["text"]["format"]["strict"])
    self.assertEqual(evidence["status"], "passed")
    self.assertEqual(evidence["retry_count"], 0)
```

- [ ] **Step 2: Run the critic test and verify RED**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests.test_openai_multi_view_critic_submits_four_images_once_and_parses_schema -v 2`

Expected: `OpenAIElevationCritic` import failure.

- [ ] **Step 3: Implement one Responses API call**

Use four Base64 PNG data URLs in the order `front`, `right`, `back`, `left`. Use `OPENAI_ELEVATION_CRITIC_MODEL`, defaulting to `gpt-5.4-mini`, and `text.format`:

```python
{
    "type": "json_schema",
    "name": "multi_view_elevation_critic",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "failed_views", "issues", "summary"],
        "properties": {
            "status": {"type": "string", "enum": ["pass", "fail"]},
            "failed_views": {
                "type": "array",
                "items": {"type": "string", "enum": list(FACADE_VIEWS)},
            },
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["code", "views", "message", "repair_instruction"],
                    "properties": {
                        "code": {"type": "string", "enum": [
                            "material_mismatch", "floor_mismatch", "opening_mismatch",
                            "corner_mismatch", "roof_mismatch", "mass_contradiction"
                        ]},
                        "views": {"type": "array", "items": {"type": "string", "enum": list(FACADE_VIEWS)}},
                        "message": {"type": "string"},
                        "repair_instruction": {"type": "string"},
                    },
                },
            },
            "summary": {"type": "string"},
        },
    },
}
```

Record `response_id`, `_request_id` when available, model, usage, input hashes, and `retry_count: 0`. Convert refusal, incomplete response, invalid parsed content, and provider exceptions into `status: failed` evidence without a second HTTP call.

- [ ] **Step 4: Run critic tests**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests -k critic -v 2`

Expected: pass, fail, refusal, and provider-error fixtures all pass with exactly one call each.

- [ ] **Step 5: Commit Task 3 files**

```powershell
git add -- backend/design/maas/aesthetic/adapters/openai_elevation_critic.py backend/design/maas/aesthetic/adapters/__init__.py backend/design/test_maas_elevation_agent.py
git diff --cached --check
git commit -m "feat: add joint multi-view elevation critic"
```

### Task 4: Bounded Multi-View Orchestrator and Idempotent Manifest

**Files:**
- Create: `backend/design/maas/agents/elevation_agent/multi_view_proposal.py`
- Modify: `backend/design/maas/agents/elevation_agent/__init__.py`
- Test: `backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: a generated elevation bundle, shared facade strategy, `AestheticProvider`, and `MultiViewCritic`.
- Produces: `generate_multi_view_elevation_proposal(bundle, *, adapter, critic, strategy) -> dict[str, Any]`.

- [ ] **Step 1: Write failing orchestration tests**

```python
def test_multi_view_proposal_calls_four_views_then_one_critic(self):
    proposal = generate_multi_view_elevation_proposal(
        bundle, adapter=image_adapter, critic=critic, strategy=strategy,
    )
    self.assertEqual([call[0]["view"] for call in image_adapter.calls], list(FACADE_VIEWS))
    self.assertEqual(len(critic.calls), 1)
    self.assertEqual(proposal["paid_request_attempt_count"], 5)
    self.assertEqual(proposal["status"], "accepted")

def test_multi_view_proposal_repairs_only_failed_view_once(self):
    critic.results = [critic_fail(["right"]), critic_pass()]
    proposal = generate_multi_view_elevation_proposal(
        bundle, adapter=image_adapter, critic=critic, strategy=strategy,
    )
    self.assertEqual([call[0]["view"] for call in image_adapter.calls], [
        "front", "right", "back", "left", "right",
    ])
    self.assertEqual(len(critic.calls), 2)
    self.assertEqual(proposal["paid_request_attempt_count"], 7)
    self.assertEqual(proposal["repair_count_by_view"]["right"], 1)

def test_accepted_matching_manifest_is_reused_without_provider_calls(self):
    first = generate_multi_view_elevation_proposal(
        bundle, adapter=image_adapter, critic=critic, strategy=strategy,
    )
    second = generate_multi_view_elevation_proposal(
        bundle, adapter=image_adapter, critic=critic, strategy=strategy,
    )
    self.assertEqual(second["status"], "accepted")
    self.assertTrue(second["skipped_existing"])
    self.assertEqual(len(image_adapter.calls), 4)
```

- [ ] **Step 2: Run orchestration tests and verify RED**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests -k multi_view_proposal -v 2`

Expected: missing orchestrator.

- [ ] **Step 3: Implement the exact state machine**

```text
validate identity and four deterministic source views
compute source-view hashes and canonical strategy SHA-256
reuse only an accepted matching manifest
generate front/right/back/left once each
run deterministic gate
if deterministic gate passes, build montage and call critic once
union deterministic failed views and critic failed views
regenerate each failed view whose repair count is zero, once
rerun deterministic gate
if deterministic gate passes, rebuild montage and call critic once
accept only when both final gates pass
persist proposal.json and critic.json atomically after every state transition
assert paid_request_attempt_count <= 10
```

Every view artifact must include exact identity, view, source path/hash, output path/hash, provider metadata, initial/repair attempt number, and preview URL:

`/design/maas/single-executions/<execution_id>/elevation-proposals/multi-view-alt-01/<view>/`

The montage must be deterministic: a 2x2 Pillow canvas ordered front/right/back/left with fixed labels and no resampling after the saved view images are loaded.

- [ ] **Step 4: Run budget, repair, failure, and reuse tests**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests -k "multi_view_proposal or paid_request or skipped_existing" -v 2`

Expected: no path can exceed 10 attempts, no view repairs twice, and accepted manifests generate zero new calls.

- [ ] **Step 5: Commit Task 4 files**

```powershell
git add -- backend/design/maas/agents/elevation_agent/multi_view_proposal.py backend/design/maas/agents/elevation_agent/__init__.py backend/design/test_maas_elevation_agent.py
git diff --cached --check
git commit -m "feat: orchestrate bounded multi-view facade generation"
```

### Task 5: Passport, Existing Graph, CLI, and HTTP Evidence

**Files:**
- Modify: `backend/design/maas/elevation_proposal_batch.py`
- Modify: `backend/design/maas/geometry_language/execution_activation.py`
- Modify: `backend/design/management/commands/generate_maas_elevation_proposals.py`
- Modify: `backend/design/urls.py`
- Modify: `backend/design/views.py`
- Test: `backend/design/test_maas_elevation_agent.py`

**Interfaces:**
- Consumes: `generate_multi_view_elevation_proposal`.
- Produces: `generate_execution_multi_view_elevation_proposal(output_root, execution_id, adapter=adapter, critic=critic)`, passport key `elevation_evidence.multi_view_proposal`, graph nodes, CLI mode, and allow-listed HTTP endpoints.

- [ ] **Step 1: Write failing passport/graph/API tests**

```python
def test_execution_multi_view_proposal_updates_one_passport_graph(self):
    result = generate_execution_multi_view_elevation_proposal(
        output_root, execution_id, adapter=image_adapter, critic=critic,
    )
    passport = read_passport()
    self.assertEqual(passport["elevation_evidence"]["multi_view_proposal"]["status"], "accepted")
    self.assertEqual(passport["activation_graph"]["graph_id"], original_graph_id)
    self.assertEqual(active_edge(passport, "accepts_multi_view_elevation"), 1.0)

def test_multi_view_artifact_api_serves_only_allow_listed_files(self):
    response = self.client.get(
        f"/design/maas/single-executions/{execution_id}/"
        "elevation-proposals/multi-view-alt-01/front/"
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(
        self.client.get(
            f"/design/maas/single-executions/{execution_id}/"
            "elevation-proposals/multi-view-alt-01/secret/"
        ).status_code,
        404,
    )
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python manage.py test design.test_maas_elevation_agent.MaasElevationAgentTests -k "execution_multi_view or multi_view_artifact_api" -v 2`

Expected: missing execution function/routes.

- [ ] **Step 3: Persist evidence and extend the existing graph**

Validate persisted program/passport/bundle identity exactly as the legacy function does. Write:

```python
passport["elevation_evidence"]["multi_view_proposal"] = proposal
execution["multi_view_elevation_proposal"] = {
    "status": proposal["status"],
    "paid_request_attempt_count": proposal["paid_request_attempt_count"],
    "manifest_path": proposal["manifest_path"],
    "accepted": proposal["status"] == "accepted",
}
```

Extend the same graph with nodes:

- `elevation:multi_view_generator`
- `elevation:multi_view_gate`
- `elevation:multi_view_critic`
- `elevation:multi_view_proposal`

Activate `accepts_multi_view_elevation` only when `status == "accepted"`; failed and unevaluated evidence remains materialized with activation `0.0`.

Add CLI behavior:

```powershell
python manage.py generate_maas_elevation_proposals `
  --mode multi-view `
  --execution-id r230-radial-roof-render-03-radial-cross
```

The view route accepts only `front`, `right`, `back`, `left`, `critic-montage`; the evidence route returns only `proposal.json` or `critic.json`.

- [ ] **Step 4: Run full focused backend module**

Run: `python manage.py test design.test_maas_elevation_agent -v 2`

Expected: all elevation-agent tests pass, including legacy ALT 01 behavior.

- [ ] **Step 5: Commit Task 5 files**

```powershell
git add -- backend/design/maas/elevation_proposal_batch.py backend/design/maas/geometry_language/execution_activation.py backend/design/management/commands/generate_maas_elevation_proposals.py backend/design/urls.py backend/design/views.py backend/design/test_maas_elevation_agent.py
git diff --cached --check
git commit -m "feat: persist multi-view elevation evidence"
```

### Task 6: MASS Frontend Creative Four-View Evidence

**Files:**
- Create: `frontend/src/design/components/book-language-flow/multi-view-elevation.ts`
- Create: `frontend/src/design/components/book-language-flow/multi-view-elevation.test.ts`
- Create: `frontend/src/design/components/book-language-flow/MultiViewElevationEvidence.tsx`
- Create: `frontend/src/design/components/book-language-flow/MultiViewElevationEvidence.test.tsx`
- Modify: `frontend/src/design/lib/language-system-types.ts`
- Modify: `frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx`
- Modify: `frontend/src/design/components/book-language-flow/ExecutedMassEvidence.test.tsx`
- Modify: `frontend/src/design/components/book-language-flow/book-language-flow.css`

**Interfaces:**
- Consumes: `passport.elevation_evidence.multi_view_proposal`.
- Produces: `extractMultiViewElevation(passport, selected) -> MultiViewElevationEvidence | null` and a four-card creative facade UI.

- [ ] **Step 1: Write failing identity and component tests**

```typescript
it('rejects a multi-view proposal from another geometry', () => {
  expect(extractMultiViewElevation(passport, {
    executionId: 'mass-one',
    programHash: 'program-one',
    geometryHash: 'geometry-two',
  })).toBeNull();
});

it('renders four creative facades and the joint consistency result', () => {
  render(<MultiViewElevationEvidence massLabel="MASS 03" proposal={proposal} />);
  expect(screen.getAllByRole('img')).toHaveLength(4);
  expect(screen.getByText('4 / 4 CREATIVE FACADES')).toBeTruthy();
  expect(screen.getByText('JOINT CONSISTENCY PASS')).toBeTruthy();
  expect(screen.getByText('7 PAID ATTEMPTS · 0 TRANSPORT RETRIES')).toBeTruthy();
});
```

- [ ] **Step 2: Run the new frontend tests and verify RED**

Run: `npm test -- --run src/design/components/book-language-flow/multi-view-elevation.test.ts src/design/components/book-language-flow/MultiViewElevationEvidence.test.tsx`

Expected: missing modules.

- [ ] **Step 3: Implement strict extraction and presentation**

The extractor must require matching passport and proposal identities, exact four unique view names, root-relative preview URLs, and artifact hashes. The component order is `front`, `right`, `back`, `left`; it labels this evidence `GENERATED DESIGN PROPOSAL · NOT GEOMETRY / LEGAL AUTHORITY`, shows deterministic/critic status separately, lists issue codes on failure, and never substitutes the legacy 4-panel ALT for missing views.

Insert `MultiViewElevationEvidence` after `ArchitecturalRenderEvidence` and before `6-VIEW GEOMETRY VERIFICATION`. Use a responsive two-column grid above 760 px and one column below it; preserve full images with `object-fit: contain`.

- [ ] **Step 4: Run focused frontend tests, typecheck, and production web build**

Run:

```powershell
npm test -- --run src/design/components/book-language-flow/elevation-proposal.test.ts src/design/components/book-language-flow/multi-view-elevation.test.ts src/design/components/book-language-flow/MultiViewElevationEvidence.test.tsx src/design/components/book-language-flow/ExecutedMassEvidence.test.tsx
npm run type-check
npx vite build --mode web
```

Expected: focused tests pass, TypeScript exits 0, web build exits 0.

- [ ] **Step 5: Run the React best-practices checklist and commit**

Check component boundaries, hook-free pure extraction, unique keys, image alt text, status text not conveyed by color alone, and no unsafe `unknown` casts in production code.

```powershell
git add -- frontend/src/design/lib/language-system-types.ts frontend/src/design/components/book-language-flow/multi-view-elevation.ts frontend/src/design/components/book-language-flow/multi-view-elevation.test.ts frontend/src/design/components/book-language-flow/MultiViewElevationEvidence.tsx frontend/src/design/components/book-language-flow/MultiViewElevationEvidence.test.tsx frontend/src/design/components/book-language-flow/ExecutedMassEvidence.tsx frontend/src/design/components/book-language-flow/ExecutedMassEvidence.test.tsx frontend/src/design/components/book-language-flow/book-language-flow.css
git diff --cached --check
git commit -m "feat: show consistent four-view facade evidence"
```

### Task 7: r230 MASS 03 Paid Proof and Browser Verification Loop

**Files:**
- Runtime artifacts: `D:\Data\25_ACE\docs\ai-session-memory\maas-service-cache\single-executions\r230-radial-roof-render-03-radial-cross\elevation\proposals\multi-view-alt-01\`
- Modify when proven: `D:\Data\25_ACE\docs\ai-session-memory\maas-mass-flow\02_CURRENT_STATE.md`
- Modify when proven: `D:\Data\25_ACE\docs\ai-session-memory\maas-mass-flow\CHANGELOG.md`
- Modify when proven: `D:\Data\25_ACE\docs\ai-session-memory\maas-mass-flow\current-checkpoint.json`
- Modify when proven: `backend/agents/elevationAgent/memory/MEMORY.md`
- Modify when proven: `backend/design/maas/agents/maas_geometry_agent/memory/MEMORY.md`

**Interfaces:**
- Consumes: the finished command, configured `backend/.env`, r230 MASS 03 immutable artifacts, backend server, and frontend web server.
- Produces: accepted or bounded-failure evidence with exact paid counts, screenshots/console report, and updated session memory.

- [ ] **Step 1: Run zero-cost preflight**

Run:

```powershell
python manage.py test design.test_maas_elevation_agent -v 2
npm test -- --run src/design/components/book-language-flow/elevation-proposal.test.ts src/design/components/book-language-flow/multi-view-elevation.test.ts src/design/components/book-language-flow/MultiViewElevationEvidence.test.tsx src/design/components/book-language-flow/ExecutedMassEvidence.test.tsx
npm run type-check
npx vite build --mode web
```

Expected: all focused checks exit 0. Stop before paid calls if any focused check fails.

- [ ] **Step 2: Confirm secrets and identity without printing secrets**

Load `backend/.env` through the project's normal Django environment path and print only booleans plus the three immutable identity strings. Confirm:

```text
OPENAI_API_KEY_SET=True
execution_id=r230-radial-roof-render-03-radial-cross
program_hash=8c0f2d94de093b6a0183a9841f9385df6cc07980b84bbec420aaf5b58d31550a
geometry_hash=6d6cea4d4d24eddee322aec3bd7614d01017b8ac9c1ab118216ace161ee1179a
```

- [ ] **Step 3: Run the bounded paid MASS 03 command once**

Run from `backend`:

```powershell
python manage.py generate_maas_elevation_proposals --mode multi-view --execution-id r230-radial-roof-render-03-radial-cross
```

Expected: four initial image attempts, one critic if deterministic checks pass, failed-view-only repairs at most once each, one final critic at most, `paid_request_attempt_count <= 10`, and `retry_count == 0`.

- [ ] **Step 4: Audit generated files and evidence**

Verify all file hashes against `proposal.json`, ensure four view identities match, recompute outside-mask changes as zero, confirm gate and critic evidence, and inspect `critic-montage.png` with the local image viewer. If status is failed, retain every artifact and issue; do not start an unbounded extra run.

- [ ] **Step 5: Run browser verification in web mode only**

Start Django and `npm run dev -- --host 127.0.0.1` in hidden background processes. In a browser:

- open the MASS language flow;
- select r230 MASS 03;
- confirm actual compiler MASS;
- confirm legacy ALT remains labeled as a proposal;
- confirm four creative views appear in front/right/back/left order;
- confirm deterministic and joint critic statuses and paid counts;
- confirm the six technical views still include top and axon;
- confirm no failed image requests and no console errors.

Stop both servers after verification and confirm their ports are closed.

- [ ] **Step 6: Update memory with the actual result**

Record exact timestamp, commit, identity, provider models, request IDs, per-view hashes, critic response ID, token usage, deterministic metrics, issue list, accepted/failed status, and remaining evidence gaps. Advance `current-checkpoint.json` from r227 to r230 without rewriting the historical r227 record.

- [ ] **Step 7: Run verification-before-completion and commit/push**

Run:

```powershell
git status --short
git diff --check
python manage.py test design.test_maas_elevation_agent -v 2
npm test -- --run src/design/components/book-language-flow/elevation-proposal.test.ts src/design/components/book-language-flow/multi-view-elevation.test.ts src/design/components/book-language-flow/MultiViewElevationEvidence.test.tsx src/design/components/book-language-flow/ExecutedMassEvidence.test.tsx
npm run type-check
npx vite build --mode web
```

Stage only repository files changed by the feature and repository-local memory files, inspect `git diff --cached --stat` and `git diff --cached`, then:

```powershell
git commit -m "feat: complete multi-view MASS elevation loop"
git push origin HEAD:codex/mass-elevation-frontend-stabilization
```

Report focused evidence and the known global-suite baseline separately.

### Task 8: Conditional r230 MASS 04 Proof

**Files:**
- Runtime artifacts under `D:\Data\25_ACE\docs\ai-session-memory\maas-service-cache\single-executions\r230-radial-roof-render-04-stepped-setback\`
- The same session-memory files from Task 7.

**Interfaces:**
- Consumes: a completed MASS 03 result.
- Produces: a second bounded proof only if MASS 03 is accepted or conclusively exhausted.

- [ ] **Step 1: Check the MASS 03 terminal condition**

Proceed only when `proposal.status == "accepted"` or the manifest proves every eligible repair was consumed and `paid_request_attempt_count <= 10`.

- [ ] **Step 2: Run the same bounded command for MASS 04**

Run:

```powershell
python manage.py generate_maas_elevation_proposals --mode multi-view --execution-id r230-radial-roof-render-04-stepped-setback
```

- [ ] **Step 3: Repeat artifact, browser, and memory verification**

Use the same hash, zero outside-mask, four-view, gate, critic, paid-count, and web-only checks from Task 7. Commit and push only after fresh verification output.
