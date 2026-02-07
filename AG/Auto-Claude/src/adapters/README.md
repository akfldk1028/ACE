# adapters -- Agent Connection Adapters

Uniform interface layer for connecting to 20+ heterogeneous agents. Each adapter normalizes a specific agent backend into the common `AgentAdapter` protocol.

## Files

| File | Purpose |
|---|---|
| `base.py` | Abstract `AgentAdapter` base class defining the adapter contract |
| `auto_claude.py` | Adapter for Auto-Claude agents (OAuth-based Claude SDK) |
| `ag_autogen.py` | Adapter for AG-AutoGen agents (HTTP / A2A JSON-RPC 2.0) |
| `ag_a2a_adapter.py` | Adapter for A2A protocol agents (Google ADK, ports 8003-8120) |
| `ag_law_domain.py` | Adapter for AG law-domain specialized agents (FastAPI REST) |
| `autogen_studio_adapter.py` | Adapter for AutoGen Studio workflows (direct or HTTP mode) |

## Key Classes

| Name | Location | Description |
|---|---|---|
| `AgentAdapter` | base.py | ABC -- `execute(task, context)`, `health_check()`, `get_capabilities()` |
| `AutoClaudeAdapter` | auto_claude.py | Sends tasks to Auto-Claude via Claude SDK with OAuth tokens |
| `AGAutogenAdapter` | ag_autogen.py | Connects to AG-AutoGen team sessions over HTTP |
| `AGA2AAdapter` | ag_a2a_adapter.py | Uses A2A JSON-RPC protocol for cross-agent messaging |
| `AGLawDomainAdapter` | ag_law_domain.py | Domain-specific adapter for legal analysis agents |
| `AutogenStudioAdapter` | autogen_studio_adapter.py | Runs AutoGen Studio workflows (direct or via port 8081) |

## Usage

```python
from src.adapters.ag_autogen import AGAutogenAdapter
from src.adapters.auto_claude import AutoClaudeAdapter

adapter = AGAutogenAdapter(base_url="http://localhost:8000")
if await adapter.health_check():
    result = await adapter.execute(task, context)

# Or use factory functions
from src.adapters import create_coder_adapter
coder = create_coder_adapter()
await coder.initialize()
```

## Notes

- All adapters inherit from `AgentAdapter` and must implement `execute()` and `health_check()`.
- The `AgentRegistry` maps agent names to their adapter instances.
- New agents are added by subclassing `AgentAdapter` and registering in the registry.
- SharedMemory integration is optional via `enable_shared_memory=True`.
