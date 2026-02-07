# bridge -- AutoGen to Auto-Claude Execution Bridge

Translates AutoGen workflow definitions into Auto-Claude executable specs and dispatches them. Supports both AI-driven mode (LLM selects steps) and template mode (predefined patterns).

## Files

| File | Purpose |
|---|---|
| `workflow_executor.py` | Core executor with AI mode and template mode dispatch |
| `auto_claude_runner.py` | Launches and monitors Auto-Claude CLI processes |
| `autogen_to_spec.py` | Converts AutoGen workflow JSON into `ProjectSpec` objects |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `WorkflowExecutor` | workflow_executor.py | `execute(workflow)` -- AI mode or template mode |
| `AutoClaudeRunner` | auto_claude_runner.py | `run(spec)` -- spawns CLI, streams output, collects result |
| `AutogenToSpec` | autogen_to_spec.py | `convert(workflow_json) -> ProjectSpec` |

## Usage

```python
from src.bridge.workflow_executor import WorkflowExecutor
from src.bridge.autogen_to_spec import AutogenToSpec

# Convert an AutoGen workflow to a project spec
spec = AutogenToSpec.convert(workflow_json)

# Execute via the bridge
executor = WorkflowExecutor(mode="ai")
result = await executor.execute(spec)
```

## Notes

- AI mode uses an LLM to dynamically decide execution steps from the spec.
- Template mode maps workflow types to predefined pipeline patterns.
- `AutoClaudeRunner` handles process lifecycle, timeout, and output capture.
