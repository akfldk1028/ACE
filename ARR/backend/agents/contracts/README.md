# ARR Global A2A Contracts

This global layer exposes application-wide agent contracts:

- A2A agent-card discovery through `.well-known` endpoints.
- JSON-RPC chat/message transport.
- Worker lifecycle and coordination APIs.
- Conversation and communication logs.

This is not the MAAS candidate contract layer. MAAS candidate contracts live in:

```text
ARR/backend/design/maas/agents/contracts.py
ARR/backend/design/maas/agents/{agent_id}/contract.py
```

Global worker modules may mirror their public card and local handoff rules under:

```text
ARR/backend/agents/worker_agents/modules/{agent_id}/
```
