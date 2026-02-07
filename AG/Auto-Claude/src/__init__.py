# AG/Auto-Claude CLI
# 24/7 AI Project Factory

"""
AG/Auto-Claude: CLI-Only 24/7 Autonomous Coding Hub

A hybrid orchestration system coordinating 20 AI agents for
24/7 autonomous project development.

Components:
- coordinator: 24/7 orchestrator, task queue, pipeline builder
- pipeline: Sequential, Parallel, Critic Loop patterns
- adapters: Auto-Claude SDK, AG HTTP adapters
- bridge: WorkflowExecutor (spec_runner.py + run.py)
- registry: Agent capabilities and selection
- project: Spec submission, watcher, binding store
- memory: SharedMemory client (AG-CLI 8101)
- utils: Configuration, models, logging

Quick Start:
    python cli.py          # 24/7 factory
    python cli.py --help   # all commands
"""

__version__ = "0.1.0"
__author__ = "25_ACE Project"

# Core models
from src.utils.models import (
    Task,
    Result,
    Pipeline,
    Stage,
    TaskType,
    Priority,
    ResultStatus,
    AgentType,
    StageType,
)

# Configuration
from src.utils.config import get_settings, Settings

# Logging
from src.utils.logger import get_logger, configure_logging, Loggers

# Registry
from src.registry import (
    AgentRegistry,
    get_registry,
    AgentCapabilities,
    get_capabilities,
    find_best_agents,
)

# Coordinator
from src.coordinator import (
    Orchestrator,
    run_orchestrator,
    TaskQueue,
    create_task_queue,
    build_pipeline,
)

# Pipeline
from src.pipeline import (
    SequentialPipeline,
    ParallelPipeline,
    CriticLoopPipeline,
    run_sequential,
    run_parallel,
    run_critic_loop,
)

# Adapters
from src.adapters import AgentAdapter

__all__ = [
    # Version
    "__version__",
    # Models
    "Task",
    "Result",
    "Pipeline",
    "Stage",
    "TaskType",
    "Priority",
    "ResultStatus",
    "AgentType",
    "StageType",
    # Config
    "get_settings",
    "Settings",
    # Logging
    "get_logger",
    "configure_logging",
    "Loggers",
    # Registry
    "AgentRegistry",
    "get_registry",
    "AgentCapabilities",
    "get_capabilities",
    "find_best_agents",
    # Coordinator
    "Orchestrator",
    "run_orchestrator",
    "TaskQueue",
    "create_task_queue",
    "build_pipeline",
    # Pipeline
    "SequentialPipeline",
    "ParallelPipeline",
    "CriticLoopPipeline",
    "run_sequential",
    "run_parallel",
    "run_critic_loop",
    # Adapters
    "AgentAdapter",
]
