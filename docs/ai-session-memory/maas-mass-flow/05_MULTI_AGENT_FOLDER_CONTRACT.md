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
and repair requests must all bind to the exact `execution_id`, `program_hash`,
`geometry_hash`, and `PNU` so agents collaborate on the same MASS.

New MASS acceptance uses the required specialist order
`design_orchestrator -> maas_geometry_agent -> law_graph_agent -> parking_agent
-> review_agent -> selector`. The orchestrator routes and persists; it does not
replace specialist evidence with direct service calls. `law_graph_agent` reuses
the existing law-domain/MCP and Neo4j systems. Unavailable required sources are
typed `needs_evidence` results, not passes.

Do not create a second source of truth while migrating legacy
`design/maas/agents/` adapters. Preserve imports and declare one executable
owner per capability.
