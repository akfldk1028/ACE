# memory -- SharedMemory Client for AG-CLI

Client library for the AG-CLI SharedMemory MCP server running on port 8101. Provides key-value storage and event publishing for cross-agent coordination.

## Files

| File | Purpose |
|---|---|
| `shared_memory_client.py` | HTTP client wrapping the SharedMemory server API |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `SharedMemoryClient` | shared_memory_client.py | Main client class |
| `.store(key, value)` | shared_memory_client.py | Write a value to shared memory |
| `.get(key)` | shared_memory_client.py | Read a value from shared memory |
| `.publish_event(type, data)` | shared_memory_client.py | Publish a coordination event to the bus |
| `store()`, `get()`, `publish_event()` | shared_memory_client.py | Module-level convenience functions (singleton client) |

## Usage

```python
from src.memory.shared_memory_client import SharedMemoryClient

client = SharedMemoryClient(base_url="http://localhost:8101")

# Store and retrieve data
await client.store("project/status", {"phase": "coding", "progress": 0.6})
status = await client.get("project/status")

# Publish an event for other agents
await client.publish_event("task_complete", {"task_id": "abc-123"})

# Pipeline helpers
await client.store_task_result(task_id="t-1", stage=0, result=output, agent_type="coder")
context = await client.get_task_context("t-1")
```

## Notes

- The SharedMemory server (port 8101) is part of the AG-CLI MCP infrastructure.
- All values are JSON-serialized. Keys support namespaced paths (e.g., `"swarm/coder/status"`).
- Events published via `publish_event()` are broadcast through the MessageBus (port 8100).
- SharedMemory errors are silently caught so they never block core pipeline execution.
