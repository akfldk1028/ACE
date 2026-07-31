# MASS Multi-Agent Law and Reference Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task and `superpowers:verification-before-completion` before any completion claim.

**Goal:** Make one generated MASS provably traverse geometry, law graph/MCP, parking, review, selector, VLM, persistence, and the single FULL GRAPH with one immutable execution identity.

**Architecture:** Keep the existing geometry compiler and law infrastructure. Add a post-compile collaboration contract owned by `design_orchestrator`; specialist agents consume and append typed evidence bound to `execution_id`, `program_hash`, `geometry_hash`, and PNU. Persist the collaboration trace in the existing MASS passport and activation graph. Resolve VLM references from structured program metadata and keep one program precedent, one form precedent, and one counterfactual, with exact-image deduplication.

**Tech Stack:** Django/Python, dataclasses, existing Neo4j/law-domain HTTP services, existing procedural geometry compiler, React/TypeScript/Vitest, JSON passport sidecars.

## Global Constraints

- Do not duplicate the law Graph DB, MCP, or MASS graph.
- Do not allow external-service failure to become a legal pass.
- Diagnostic compile/render may succeed while final selection remains `needs_evidence`.
- Limit final paid VLM validation to one MASS and at most three reference images.
- Preserve unrelated dirty-worktree changes and commit only files in this plan.
- Every test fixture uses fake adapters; unit tests never require paid API or live law services.

---

## Task 1: Freeze the collaboration and identity contract

**Files:**

- Create: `backend/design/maas/agents/orchestrator/execution_collaboration.py`
- Modify: `backend/design/maas/agents/shared/types.py`
- Test: `backend/design/test_maas_agent_collaboration.py`

**Step 1: Write failing contract tests**

Test that the required order is geometry, law graph, parking, review, selector; every handoff carries the same four-part identity; a hash mismatch fails closed; and `needs_evidence` from law cannot be promoted to accepted.

**Step 2: Run the focused test and observe failure**

Run `python manage.py test design.test_maas_agent_collaboration` from `backend`.

**Step 3: Implement minimal immutable types and runner**

Add `ExecutionIdentity`, `AgentEvidence`, `AgentHandoff`, and `CollaborationTrace`. Keep the existing conversational `run_review_flow` intact; the new runner is specifically for a compiled single-MASS acceptance path.

**Step 4: Re-run the focused test**

Expected: contract tests pass without live services.

## Task 2: Make the law agent own existing law-source retrieval

**Files:**

- Create: `backend/design/maas/agents/law_graph_agent/evidence.py`
- Modify: `backend/design/maas/agents/law_graph_agent/agent.py`
- Modify: `backend/design/maas/agents/parking_agent/agent.py`
- Test: `backend/design/test_maas_agent_collaboration.py`

**Step 1: Write failing source-boundary tests**

Inject fake PNU, law-domain/MCP, and Neo4j adapters. Assert attempts, source IDs, citations, and bounded error categories are returned by `law_graph_agent`; assert unavailable required sources yield `needs_evidence`.

**Step 2: Implement the adapter boundary**

Reuse `design.maas.law_provenance.build_law_provenance_projection` and the existing law-domain search service. Normalize results rather than reproducing graph queries in the orchestrator. Parking consumes the law evidence and preserves its own rule/layout provenance.

**Step 3: Run focused tests**

Expected: both available and unavailable service cases are deterministic.

## Task 3: Integrate collaboration into single-MASS passports

**Files:**

- Modify: `backend/design/maas/single_execution/pipeline.py`
- Modify: `backend/design/maas/geometry_language/execution_passport.py`
- Modify: `backend/design/maas/geometry_language/execution_persistence.py`
- Modify: `backend/design/maas/geometry_language/execution_evidence.py`
- Modify: `backend/design/maas/geometry_language/execution_activation.py`
- Test: `backend/design/test_maas_single_execution.py`
- Test: `backend/design/test_maas_agent_collaboration.py`

**Step 1: Write failing integration tests**

Assert the passport contains one collaboration trace, handoff edges, agent nodes, law request/article nodes, and final selector status. Assert all nodes are linked to the exact MASS hashes. Assert missing law evidence still produces the PNG but blocks acceptance.

**Step 2: Pass the trace through persistence**

Add an explicit `agent_collaboration` input to passport build/write/enrich operations. Preserve it only when program and geometry hashes match.

**Step 3: Extend the existing activation graph**

Append nodes and edges to the selected MASS path; do not create another graph payload or tab. Materialize only actual evidence and attempted-source failures.

**Step 4: Run focused integration tests**

Expected: diagnostic and accepted fixtures both pass with truthful status.

## Task 4: Correct program-conditioned ArchDaily reference selection

**Files:**

- Modify: `backend/design/maas/single_execution/vlm_review.py`
- Modify: `backend/design/maas/preference/reference_corpus.py`
- Test: `backend/design/test_maas_single_execution.py`
- Test: `backend/design/test_maas_preference.py`

**Step 1: Write failing metadata-resolution tests**

Use a program whose only identity is `metadata.program_projection.program_id`. Assert that exact ID reaches retrieval and that no generic fallback is used.

**Step 2: Write failing diversity tests**

Request three references and assert the roles are program, similar, and counterfactual; source identity and exact image digest are unique.

**Step 3: Implement the smallest selector change**

Centralize program identity resolution, set the bounded default to three, and add exact-image digest deduplication. Keep explicit request identity highest priority.

**Step 4: Run focused tests**

Expected: nested metadata and diversity assertions pass without invoking VLM.

## Task 5: Render the specialist path in the existing frontend graph

**Files:**

- Modify: `frontend/src/design/components/book-language-flow/BookLanguageFlow.tsx`
- Modify: `frontend/src/design/components/ExecutedMassEvidence.tsx`
- Modify: relevant types under `frontend/src/design/lib/`
- Test: `frontend/test/unit/design/ExecutedMassEvidence.test.tsx`
- Create: `frontend/test/unit/design/BookLanguageFlow.test.tsx`

**Step 1: Write failing component tests**

Supply one passport containing agent, handoff, law article, MCP attempt, and VLM-reference nodes. Assert the existing FULL GRAPH renders them after selecting the MASS. Assert the right sidebar shows final mass plus agent statuses and source failures.

**Step 2: Implement additive rendering**

Use the existing activation graph payload. Add restrained monochrome/semantic styling and labels; no new graph tab and no BOOK scan image card.

**Step 3: Run unit tests and typecheck**

Run the focused Vitest files and the repository TypeScript check.

## Task 6: Update canonical MASS memory

**Files:**

- Modify: `docs/ai-session-memory/maas-mass-flow/00_READ_FIRST.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/01_FLOW_CONTRACT.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/02_CURRENT_STATE.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/CHANGELOG.md`
- Modify: `docs/ai-session-memory/maas-mass-flow/current-checkpoint.json`
- Modify/Create: `docs/ai-session-memory/maas-mass-flow/05_MULTI_AGENT_FOLDER_CONTRACT.md`

Record that MASS acceptance is specialist-agent collaboration; services are reused; every handoff is hash-bound; missing law evidence blocks acceptance; ArchDaily references are bounded, program-conditioned, and attached to the single FULL GRAPH; new agents follow the `backend/agents/elevationAgent` folder contract.

## Task 7: Verify offline, then perform one live execution

**Step 1: Offline verification**

Run focused backend tests, relevant frontend tests/typecheck, and a single fake-adapter integration execution. Record any unrelated pre-existing suite failures separately.

**Step 2: Ask the user to start existing services**

Request Neo4j and law-domain-agents port 8011 only after offline tests pass. Confirm health before generation.

**Step 3: Execute one real MASS**

Run exactly one program-conditioned MASS. Confirm compile, gate, four-view PNG, legal citations, parking evidence, collaboration trace, selector decision, archive persistence, and frontend retrieval.

**Step 4: Run one bounded paid VLM review**

Use at most three distinct ArchDaily images and no uncontrolled retries. Persist cost/model/image hashes and critic evidence.

**Step 5: Browser verification**

Open `/design/language`, select the newest MASS, confirm the last MASS image, specialist chain, law/VLM source nodes, and no BOOK scan in the result sidebar. Capture one verification PNG.

**Step 6: Commit deliberately**

Review the diff, stage only plan-owned files, commit, and push only after all final evidence is recorded.
