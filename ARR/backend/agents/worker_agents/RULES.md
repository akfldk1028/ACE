# ARR Worker Agents Rules

1. Every long-lived worker must have a module folder under `modules/{agent_id}/`.
2. Each module folder must include `agent.yaml`, `SOUL.md`, `RULES.md`, and
   `memory/MEMORY.md`.
3. Each module must point to its executable adapter and public card.
4. Worker agents must not silently claim MAAS legal or geometry authority unless
   explicitly wired through the MAAS domain agent flow.
