# Agent Folder Standard

Updated: 2026-07-07

This repository follows a GitAgent-style folder contract for agents. An agent is
not just a Python file or a markdown note. It is a versioned folder with identity,
rules, memory, runtime adapter, and an exchange contract.

Reference implementation checked in `clone/gitagent/`:

```text
agent.yaml
SOUL.md
RULES.md
memory/MEMORY.md
tools/
skills/
hooks/
agents/{child_agent}/agent.yaml
agents/{child_agent}/SOUL.md
agents/{child_agent}/RULES.md
```

## Required Folder Shape

Every project-local agent folder should expose this shape:

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

## Meaning

| File or Folder | Role |
|---|---|
| `agent.yaml` | machine-readable identity, model preference, routing, tools, memory path |
| `SOUL.md` | stable design intent and responsibility |
| `RULES.md` | non-negotiable behavior and handoff constraints |
| `memory/MEMORY.md` | versioned lessons, failures, and current state |
| `agent.py` | executable runtime when the agent is implemented in Python |
| `card.py` or `card.json` | A2A/AG-light/public capability card |
| `contract.py` or `contracts/README.md` | input/output schema and ownership boundary |

Code-first rule:

- If the agent is executable Python, the folder must contain `agent.py`.
- If the stable implementation lives elsewhere for import compatibility,
  `agent.py` must re-export or adapt that implementation.
- Markdown files are not enough to declare an agent module.

## Scope Rule

`ARR/backend/agents/` and `ARR/backend/design/maas/agents/` are both needed, but
they do not own the same layer.

- `ARR/backend/agents/`: global Django A2A and worker-agent infrastructure.
- `ARR/backend/design/maas/agents/`: MAAS legal massing domain specialists.

Both should follow the same folder vocabulary so a reviewer can inspect any
agent the same way.
