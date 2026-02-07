# utils -- Configuration, Models, and Logging

Shared utilities used across all modules: application settings, common data models, and structured logging.

## Files

| File | Purpose |
|---|---|
| `config.py` | Pydantic-settings loaded from environment variables / `.env` files |
| `models.py` | Common data models: Task, Result, Pipeline, Stage, AgentType enums |
| `logger.py` | Pre-configured structlog-based loggers for each module |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `Settings` | config.py | All configuration fields (ports, paths, timeouts, API keys) |
| `get_settings()` | config.py | Returns cached singleton `Settings` instance |
| `Task` | models.py | Unit of work with id, type, description, priority, input, context |
| `Result` | models.py | Execution result with status, output, error, next_tasks |
| `Pipeline` | models.py | Pipeline definition with ordered list of `Stage` objects |
| `Stage` | models.py | Single pipeline stage: agent type, stage type, timeout |
| `Loggers` | logger.py | Namespace-aware logger factory (orchestrator, pipeline, adapter, etc.) |

## Usage

```python
from src.utils.config import get_settings
from src.utils.models import Task, TaskType, Priority, Result, ResultStatus
from src.utils.logger import Loggers

settings = get_settings()
log = Loggers.orchestrator()

task = Task(type=TaskType.CODE, description="Implement login", priority=Priority.HIGH)
log.info("processing_task", task_id=task.id, timeout=settings.stage_timeout_seconds)
```

## Notes

- `Settings` reads from environment variables with an `AG_` prefix (e.g., `AG_TASK_TIMEOUT`).
- Models use Pydantic for validation and serialization.
- Loggers output structured JSON in production and human-readable format in development.
- Key settings: `bridge_port` (8080), `ag_autogen_url`, `ag_law_domain_url`, `max_qa_iterations` (5).
