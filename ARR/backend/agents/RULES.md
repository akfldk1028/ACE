# ARR Global A2A Agents Rules

1. Do not place MAAS-specific MassDSL grammar, source geometry, legal variant
   selection, or parking interpretation in this folder.
2. Keep this folder responsible for A2A discovery, JSON-RPC transport, worker
   lifecycle, conversation coordination, logs, and shared infrastructure.
3. New reusable worker agents must have a GitAgent-style module folder:
   `worker_agents/modules/{agent_id}/`.
4. Runtime code may remain in existing Django import paths when moving it would
   break compatibility. The module folder is still required as the inspectable
   identity, rule, memory, card, and contract surface.
5. Domain-local teams must synchronize their declarative team graph separately.
