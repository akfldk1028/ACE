"""
Coordinator module for AG/Auto-Claude

Central coordination components:
- Orchestrator: 24/7 main loop
- TaskQueue: Persistent task queue
- AgentSelector: Intelligent agent selection
- PipelineBuilder: Dynamic pipeline construction
"""

from .task_queue import (
    TaskQueue,
    TaskStatus,
    create_task_queue,
)

from .agent_selector import (
    AgentSelector,
    AgentSelection,
    get_selector,
)

from .pipeline_builder import (
    PipelineBuilder,
    PipelineTemplate,
    get_builder,
    build_pipeline,
)

from .orchestrator import (
    Orchestrator,
    OrchestratorState,
    run_orchestrator,
)

__all__ = [
    # Task Queue
    "TaskQueue",
    "TaskStatus",
    "create_task_queue",
    # Agent Selector
    "AgentSelector",
    "AgentSelection",
    "get_selector",
    # Pipeline Builder
    "PipelineBuilder",
    "PipelineTemplate",
    "get_builder",
    "build_pipeline",
    # Orchestrator
    "Orchestrator",
    "OrchestratorState",
    "run_orchestrator",
]
