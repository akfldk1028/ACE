# project -- Project Submission and Management

Handles project spec creation, file-system watching for new submissions, CLI-based submission, and persistent binding between projects and agent sessions.

## Files

| File | Purpose |
|---|---|
| `spec.py` | `ProjectSpec` Pydantic model -- defines what a project contains |
| `watcher.py` | Watches `projects/queue/` directory for new `.yaml` / `.json` spec files |
| `cli.py` | CLI entry point for submitting projects and checking status |
| `binding_store.py` | Persists project-to-session bindings (SQLite) for resumption |

## Key Classes / Functions

| Name | Location | Description |
|---|---|---|
| `ProjectSpec` | spec.py | Pydantic model with name, goals, requirements, agents, pipeline config |
| `ProjectWatcher` | watcher.py | `start()`, `stop()` -- monitors inbox directory via watchdog |
| `submit_project(spec)` | cli.py | Validates and enqueues a spec into `TaskQueue` |
| `get_binding_store()` | binding_store.py | Returns the singleton binding store instance |

## Usage

```python
from src.project.spec import ProjectSpec, load_project_spec
from src.project.cli import submit_project

spec = load_project_spec("my_project.yaml")
submit_project(spec)

# Or use the watcher for automatic pickup
from src.project.watcher import ProjectWatcher
watcher = ProjectWatcher(inbox_dir="./projects/queue")
await watcher.start()
```

## Notes

- The watcher integrates with `TaskQueue` to auto-enqueue discovered specs.
- `binding_store.py` uses SQLite to persist which agent session handles which project.
- Spec files support both JSON and YAML formats.
- CLI commands: `submit`, `list`, `status`, `example`.
