# coordinator -- 24/7 Orchestration Engine

The always-on orchestration loop that polls for tasks, scores and selects agents, builds pipelines, and dispatches work continuously.

## Files

| File | Purpose |
|---|---|
| `orchestrator.py` | Main 24/7 run-loop: poll queue, build pipeline, execute, report |
| `task_queue.py` | SQLite-backed priority queue with status tracking and retry logic |
| `agent_selector.py` | Score-based agent selection using capability matching |
| `pipeline_builder.py` | Dynamically constructs pipelines from spec + available agents |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `Orchestrator` | orchestrator.py | Core loop -- `start()`, `stop()`, `run_once()` |
| `TaskQueue` | task_queue.py | `enqueue()`, `dequeue()`, `complete()`, `fail()`, `get_stats()` |
| `AgentSelector` | agent_selector.py | `select(task) -> AgentSelection` using weighted capability scores |
| `PipelineBuilder` | pipeline_builder.py | `build(task, selection) -> Pipeline` from templates or auto-generation |

## Usage

```python
from src.coordinator.orchestrator import Orchestrator
from src.coordinator.task_queue import TaskQueue

queue = TaskQueue(db_path="tasks.db")
orchestrator = Orchestrator(queue=queue)

# Start the 24/7 loop (blocking)
await orchestrator.start()

# Or run a single iteration for testing
await orchestrator.run_once()
```

## Notes

- The orchestrator polls `TaskQueue` on a configurable interval (default 1s).
- `AgentSelector` ranks agents from `AgentRegistry` against the task's required capabilities.
- `PipelineBuilder` chooses sequential, parallel, or critic-loop patterns based on task complexity.
- Failed tasks are automatically retried up to `max_retries` (default 3).
