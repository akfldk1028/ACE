"""
Project submission module for AG/Auto-Claude

Provides project spec definition, watcher, and CLI for
24/7 automatic project execution.
"""

from .spec import (
    ProjectSpec,
    ProjectPhase,
    ProjectStatus,
    load_project_spec,
    save_project_spec,
)

from .watcher import (
    ProjectWatcher,
    start_watcher,
)

from .cli import (
    submit_project,
    list_projects,
    get_project_status,
)

__all__ = [
    # Spec
    "ProjectSpec",
    "ProjectPhase",
    "ProjectStatus",
    "load_project_spec",
    "save_project_spec",
    # Watcher
    "ProjectWatcher",
    "start_watcher",
    # CLI
    "submit_project",
    "list_projects",
    "get_project_status",
]
