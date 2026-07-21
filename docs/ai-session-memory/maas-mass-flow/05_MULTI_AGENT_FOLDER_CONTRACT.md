# MAAS Multi-Agent Folder Contract

Canonical shared control plane: `ARR/backend/agents/`.

Canonical specialist-folder reference: `ARR/backend/agents/elevationAgent/`.
Each future specialist is a sibling independent git-native repository with its
own `agent.yaml`, `SOUL.md`, `RULES.md`, `memory/`, `skills/`, `agents/`, `src/`,
`test/`, `docs/`, and examples. Copy structure only; reset identity, private
memory, tools, tests, examples, and repository history.

`ARR/backend/agents/memory/` is shared memory. Specialist `memory/` folders are
private. Handoffs contain typed evidence, not prose-only claims.

`ARR/backend/design/maas/` is the shared GeometryProgram/domain engine. A
future `massAgent` repo will own agent identity and collaboration behavior while
calling this engine. Plans, elevations, facade images, law results, VLM reviews,
and repair requests must all bind to the exact `run_id`, `program_hash`, and
`geometry_hash` so agents collaborate on the same MASS.

Do not create a second source of truth while migrating legacy
`design/maas/agents/` adapters. Preserve imports and declare one executable
owner per capability.
