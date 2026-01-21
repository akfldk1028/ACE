# AG-ACE-BRIDGE
# 24/7 AI Project Factory

"""
AG-ACE-BRIDGE: Auto-Claude + AG Multi-Agent Integration

A hybrid orchestration system coordinating 17 AI agents for
24/7 autonomous project development.

Components:
- coordinator: 24/7 orchestrator, task queue, pipeline builder
- pipeline: Sequential, Parallel, Critic Loop patterns
- adapters: Auto-Claude SDK, AG HTTP adapters
- registry: Agent capabilities and selection
- memory: Graphiti ↔ Neo4j synchronization (planned)
- utils: Configuration, models, logging

Quick Start:
    from src.coordinator import run_orchestrator
    import asyncio

    asyncio.run(run_orchestrator())
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
