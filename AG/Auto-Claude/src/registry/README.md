# registry -- Agent Registry and Capability Management

Central registry that tracks all available agents, their capabilities, and reusable pipeline patterns. Used by the orchestrator to discover and match agents to tasks.

## Files

| File | Purpose |
|---|---|
| `agent_registry.py` | Singleton registry mapping agent names to adapter instances and runtime status |
| `capabilities.py` | Static capability definitions and keyword-based matching logic |
| `pattern_registry.py` | Named pipeline patterns (e.g., "auto_claude_full", "research", "legal_validation") |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `AgentRegistry` | agent_registry.py | `register()`, `select_agents()`, `record_success()`, `record_failure()`, `health_check_all()` |
| `AgentCapabilities` | capabilities.py | Declares what an agent can do (skills, task types, keywords) |
| `PatternRegistry` | pattern_registry.py | `register_pattern()`, `get_pattern()`, `list_patterns()` |

## Usage

```python
from src.registry.agent_registry import AgentRegistry
from src.registry.capabilities import AgentCapabilities

registry = AgentRegistry()
registry.register("coder", coder_adapter, AgentCapabilities(skills=["python", "typescript"]))

# Find agents that can handle a coding task
matches = registry.select_agents(task, limit=3)

# Record execution results for future scoring
registry.record_success(AgentType.AUTO_CLAUDE_CODER, response_time_ms=1500)
```

## Notes

- `AgentRegistry` is typically initialized at startup with all known adapters.
- `AgentSelector` in the coordinator queries this registry to score candidates.
- `PatternRegistry` stores reusable pipeline templates that `PipelineBuilder` can instantiate.
- Agents with 3+ consecutive failures are automatically marked unhealthy.
