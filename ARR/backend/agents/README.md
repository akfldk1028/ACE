# agents

This is the global Django A2A/worker-agent app. It is required alongside the
MAAS domain-agent folder, but it owns a different layer.

For MAAS legal-design specialists, use:

`ARR/backend/design/maas/agents/`

Boundary reference:

`docs/ai-session-memory/MAAS_AGENT_FOLDER_BOUNDARIES.md`

Folder standard:

`docs/ai-session-memory/AGENT_FOLDER_STANDARD.md`

A2A-compliant multi-agent system with LangGraph workers.

## Structure
```
agents/
├── agent.yaml             # GitAgent-style root identity for global A2A infra
├── agent.py               # inspectable code adapter for global A2A infra
├── SOUL.md                # global infrastructure purpose
├── RULES.md               # global/domain boundary rules
├── memory/MEMORY.md       # versioned global-agent memory
├── contracts/README.md    # global A2A/JSON-RPC contract boundary
├── models.py              # Agent model (types: gemini/gpt/claude/custom)
├── views.py               # Agent card endpoints, chat interface
├── urls.py                # /agents/{slug}/chat/, /.well-known/agent-card/
├── a2a_client.py          # A2A JSON-RPC 2.0 client
├── langgraph_agent.py     # LangGraph integration
├── well_known_urls.py     # /.well-known/ discovery
├── database/neo4j/        # Neo4j service layer (queries, indexes, stats)
├── worker_agents/         # Worker implementations
│   ├── agent.yaml                    # worker-layer identity
│   ├── agent.py                      # inspectable code adapter for worker layer
│   ├── SOUL.md / RULES.md / memory/  # worker-layer policy and memory
│   ├── base/base_worker.py           # Abstract BaseWorkerAgent
│   ├── implementations/              # GeneralWorker, FlightSpecialistWorker
│   ├── modules/                      # GitAgent-style worker folders
│   ├── cards/                        # A2A agent card JSONs
│   ├── worker_factory.py             # Factory pattern
│   ├── worker_manager.py             # Lifecycle management
│   ├── conversation_coordinator.py   # Multi-agent coordination
│   └── a2a_streaming.py             # Streaming A2A responses
└── voice/                 # Voice A2A integration (WebSocket)
```

## A2A Endpoints
- `GET /.well-known/agent-card/{slug}.json` - Agent discovery
- `POST /agents/{slug}/chat/` - JSON-RPC 2.0 message/send
- `GET /agents/list/` - All agents

## Dependencies
- `core.models.BaseModel`, `Organization`, `Tag`
- Neo4j (optional, for graph features)

## Folder Contract

Reusable workers must be represented as independent folders under:

```text
worker_agents/modules/{agent_id}/
  agent.py
  card.py
  contract.py
  agent.yaml
  SOUL.md
  RULES.md
  memory/MEMORY.md
```

Runtime Python adapters can remain in `worker_agents/implementations/` when
that preserves stable Django imports. The module folder is the reviewable agent
identity/rules/memory surface.
