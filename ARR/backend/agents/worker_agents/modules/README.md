# Worker Agent Modules

This folder mirrors reusable global workers as GitAgent-style agent folders.

Runtime compatibility rule:

- Python execution can stay in `../implementations/`.
- Agent identity, rules, memory, card links, and contract notes must live here.

Standard shape:

```text
modules/{agent_id}/
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```

This keeps the folder structure consistent with MAAS domain agents without
forcing a risky import-path migration.
