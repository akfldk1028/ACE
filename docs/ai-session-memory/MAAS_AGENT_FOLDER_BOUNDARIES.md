# MAAS Agent Folder Boundaries

Updated: 2026-07-07

The project has several folders named `agents`. They are not interchangeable.

## Folder Roles

| Folder | Scope | What It Owns | Do Not Put Here |
|---|---|---|---|
| `ARR/backend/agents/` | Global Django A2A/worker-agent app | agent database models, A2A discovery endpoints, generic worker lifecycle, conversation logs, LangGraph/A2A infrastructure | MAAS-specific MassDSL grammar, source geometry, legal variant selection |
| `ARR/backend/design/maas/agents/` | MAAS domain-local agents | law/parking/LLM-language/MassDSL/geometry/critic/review contracts attached to MAAS candidates | global agent DB models, generic A2A worker infrastructure |
| `ARR/frontend/src/design/components/ag-light-flow/agents/` | AG-light UI mapping | frontend participant modules mapped from `JSON_MODULES` team JSON | backend generation logic |
| `AG-light/server/agents/` | AG-light collaboration runtime | message bus, shared memory, collaborative server behavior | ARR Django MAAS optimizer internals |
| `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json` | Declarative team graph | AutoGen/AG-light visible team participants and selector routing | Python implementation code |

## Shared Agent Folder Standard

Both the global infrastructure layer and the MAAS domain layer must follow the
same GitAgent-style inspection vocabulary:

```text
{agent_id}/
  agent.py or runtime_adapter.md
  card.py or card.json
  contract.py or contracts/README.md
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```

Reference:

`docs/ai-session-memory/AGENT_FOLDER_STANDARD.md`

Applied examples:

```text
ARR/backend/agents/
  agent.py
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
  contracts/README.md
  worker_agents/
    agent.py
    agent.yaml
    SOUL.md
    RULES.md
    memory/MEMORY.md
    modules/flight_specialist_worker/
      agent.py
      card.py
      contract.py
      agent.yaml
      SOUL.md
      RULES.md
      memory/MEMORY.md

ARR/backend/design/maas/agents/law_graph_agent/
  agent.py
  card.py
  contract.py
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```

The global layer can keep Python runtime adapters in existing import paths. The
folder contract still makes each agent inspectable in the same way.

## Current Canonical MAAS Agent Flow

```text
law_graph_agent
  -> parking_agent
  -> llm_architect_agent
  -> massdsl_agent
  -> maas_geometry_agent
  -> grammar_critic_agent
  -> review_agent
```

This flow must be synchronized across:

1. `ARR/backend/design/maas/agents/orchestrator/flow.py`
2. `ARR/backend/design/maas/agents/shared/registry.py`
3. `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json`
4. `AG-light/data/teams/041_MAAS_Legal_Design_Team.json`
5. `ARR/frontend/src/design/components/ag-light-flow/agents/index.ts`

## Rule

If adding a MAAS specialist agent, add it to the MAAS domain-local folder first:

```text
ARR/backend/design/maas/agents/{agent_id}/
  agent.py
  card.py
  contract.py optional
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```

Then synchronize the team JSON and AG-light UI mapping.

If adding a reusable global worker, add the runtime adapter and mirror it as:

```text
ARR/backend/agents/worker_agents/modules/{agent_id}/
  agent.py
  card.py
  contract.py
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```
