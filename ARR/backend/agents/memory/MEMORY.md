# ARR Global A2A Agents Memory

## 2026-07-07

- Clarified that this folder is required alongside MAAS domain agents.
- Added GitAgent-style root metadata so global infrastructure can be inspected
  with the same folder vocabulary as domain agents.
- Existing runtime files are not moved because Django imports and URL routing
  depend on the current module paths.

## 2026-07-21 - Specialist repositories and shared memory

- `ARR/backend/agents/` is the shared multi-agent control plane and shared
  memory/contract layer.
- `ARR/backend/agents/elevationAgent/` is the structural reference for future
  sibling specialist repositories such as `massAgent`, `planAgent`, and
  `lawAgent`.
- Clone the folder vocabulary, never the existing identity, `.git` history, or
  task-specific memory content. Every specialist initializes its own identity,
  rules, memory, skills, tools, tests, and repository history.
- `ARR/backend/design/maas/` remains the shared massing domain engine. A future
  `massAgent` invokes it through typed contracts rather than copying its code.
- Cross-agent artifacts use `run_id`, `program_hash`, `geometry_hash`, PNU,
  evidence IDs, and explicit evaluated/not-evaluated status.
- Full contract: `ARR/backend/agents/SHARED_AGENT_ARCHITECTURE.md`.
