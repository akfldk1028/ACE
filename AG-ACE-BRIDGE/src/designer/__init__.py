"""
Project Designer Module

Provides end-to-end project design and execution:
- ProjectDesigner: AI-powered project design using Auto-Claude Planner
- PatternMatcher: Match tasks to existing patterns
- ProjectExecutor: Execute projects through pattern orchestration

Usage:
    designer = ProjectDesigner(planner_adapter)
    project = await designer.design("Create a calculator app")

    executor = ProjectExecutor(scheduler, registry)
    await executor.execute(project)
"""

from .project_designer import ProjectDesigner, ProjectSpec, ProjectPhase, ProjectTask
from .pattern_matcher import PatternMatcher
from .project_executor import ProjectExecutor

__all__ = [
    "ProjectDesigner",
    "ProjectSpec",
    "ProjectPhase",
    "ProjectTask",
    "PatternMatcher",
    "ProjectExecutor",
]
