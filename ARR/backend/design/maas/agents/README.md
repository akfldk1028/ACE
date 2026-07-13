# MAAS Design Agents

Updated: 2026-07-07

This folder defines the deterministic ARR-side agent layer for MAAS legal
massing. The structure follows a GitAgent-style folder contract plus local
A2A/card contracts: each agent has its own package, card builder, contract,
identity, rules, and memory, while `orchestrator/flow.py` owns the canonical
handoff sequence.

## Flow

`design_orchestrator -> law_graph_agent -> parking_agent -> llm_architect_agent -> massdsl_agent -> maas_geometry_agent -> grammar_critic_agent -> preference_distiller_agent -> review_agent`

- `design_orchestrator`: routes a PNU/design candidate into the law-to-design flow.
- `law_graph_agent`: checks FAR/BCR/height against structured legal constraints.
- `parking_agent`: summarizes parking count and layout precheck evidence.
- `llm_architect_agent`: owns LLM-authored architectural language, primary/secondary language, composition rule, authored parameter source, and revision request.
- `massdsl_agent`: converts legal/parking evidence and selected candidate data
  into the deterministic `arr.maas.massdsl.proposal.v1` contract.
- `maas_geometry_agent`: explains the selected MAAS repair/shape operation.
- `grammar_critic_agent`: checks MassDSL/geometry language, section connector
  evidence, parking evidence, and weak repeated extrusion risks.
- `preference_distiller_agent`: second-stage critic/reranker for rendered legal
  candidates. It may use VLM concept scoring and human pairwise labels, but it
  cannot override law, parking, or geometry hard gates.
- `review_agent`: summarizes rejected candidates and final audit state.

## 2026-07-08 Preference Distiller Agent

- Added `preference_distiller_agent/` as a folder-based module, not a markdown
  note.
- Runtime library lives in `design.maas.preference`.
- The first implementation emits `arr.maas.preference_distill.v1` in
  `vlm_ready_geometry_proxy` mode. This is explicit evidence that real VLM
  inference has not necessarily run yet.
- Future VLM integration should switch the same contract to `vlm_scored` only
  when rendered PNGs and model output are attached.
- Preference score is post-legal and post-parking. It cannot rescue failed
  candidates.

`contracts.py` is a compatibility wrapper used by the existing interactive
operation endpoint. It now delegates to `shared/registry.py`, so future agent
implementations can replace one folder without changing the endpoint response
shape.

## A2UI

`a2ui_surface.py` emits v0.9-style A2UI messages using the ARR catalog id
`arr.maas.agent_review.v0`. The frontend React Flow surface maps the same agent
ids, and the AG-light CLI imports `orchestrator.flow.FLOW_STEPS` so CLI and UI
stay aligned.

## Modular Agent Contract

This agent tree must stay aligned with three project layers:

1. `ARR/backend/design/maas/agents/`: executable local agent contracts and candidate evidence attachment.
2. `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`: declarative AG/AutoGen team graph.
3. `ARR/frontend/src/design/components/ag-light-flow/agents/`: AG-light UI participant mapping.

Reference implementations:

- `clone/gitagent`: repo-native agent modularity (`agent.yaml`, `SOUL.md`, `RULES.md`, `memory/`, `skills/`, `hooks/`).
- `clone/openai-agents-python`: agent workflow concepts (agents, handoffs, tools, guardrails, sessions, tracing).
- `docs/ai-session-memory/MAAS_PAPER_METHOD_AGENT_MATRIX.md`: maps paper method layers to MAAS agents.
- `docs/ai-session-memory/MAAS_AGENT_FOLDER_BOUNDARIES.md`: explains why
  `ARR/backend/agents/` is global A2A infrastructure while this folder is the
  MAAS domain-local specialist layer.
- `docs/ai-session-memory/AGENT_FOLDER_STANDARD.md`: shared folder standard for
  global and MAAS agents.

Each MAAS specialist folder should contain:

```text
{agent_id}/
  agent.py
  card.py
  contract.py
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```

This is not markdown-only documentation. The folder is the inspectable agent
unit: executable adapter, public card, contract boundary, identity, rules, and
versioned memory live together.

## 2026-07-07 LLM Architect Agent

- Added `llm_architect_agent/` because the live OpenAI-backed proposal loop in
  `design.maas.llm_proposals` previously sat outside the MAAS agent graph.
- The LLM agent does not decide law, parking, or geometry finality.
- It owns:
  - LLM-authored architectural language,
  - primary/secondary language checks,
  - composition rule evidence,
  - parameter-source audit,
  - revision request when parking/legal/orderliness fails.
- `parking_agent` now hands off to `llm_architect_agent`, and
  `llm_architect_agent` hands off to `massdsl_agent`.

## 2026-06-30 MassDSL Agent Loop V1

- Backend agent folders are intentionally separated:
  - `llm_architect_agent/{agent.py,card.py,agent.yaml,SOUL.md,RULES.md,memory/MEMORY.md}`
  - `massdsl_agent/{agent.py,card.py,contract.py}`
  - `grammar_critic_agent/{agent.py,card.py,contract.py}`
- `/design/maas/legal-variants/` now returns additive agent fields:
  `agent_reviews`, `agent_trace`, `a2ui_messages`, `massdsl_proposals`,
  `grammar_review`, and `grammar_reviews`.
- Each returned candidate also carries `properties.massdsl_proposal` and
  `properties.grammar_review`; if `properties.maas_model` exists, the same
  evidence is mirrored there for UI/PNG inspection.
- `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json` was expanded to the
  same six-agent review sequence so ARR frontend React Flow and AG/AutoGen
  team metadata stay aligned.
- Verification for this slice:
  - `cd ARR/backend && .venv/bin/python -m py_compile ...` passed.
  - Focused Django tests passed for registry, endpoint evidence, MassDSL
    contract, grammar variants, and source-signature diversity.
  - `cd ARR/frontend && npm run type-check` passed.
  - PNG loop generated
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png` and
    `.json`; latest JSON has 20 candidates, 20 MassDSL proposals, 20 grammar
    reviews, and six agent reviews.
  - AG-light Playwright verifier passed with 8 nodes and 7 overlay edges:
    `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782807801354.png`.
  - The verifier uses navigation-only HTML `Accept` routing. Do not set a
    global Playwright `Accept` header, because it breaks Vite `/@vite/client`
    and API fetches.
