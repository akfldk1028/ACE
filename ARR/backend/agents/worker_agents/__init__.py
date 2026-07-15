"""
Worker Agents Package

Clean, organized structure for all worker agents:
- base/: Base classes and common functionality
- implementations/: Specific worker agent implementations
- cards/: Agent card definitions and templates
- worker_factory.py: Factory for creating workers
- worker_manager.py: Manager for worker lifecycle

Usage:
    from agents.worker_agents import get_worker_for_slug, WorkerAgentFactory
"""

from .base import BaseWorkerAgent
from .worker_factory import WorkerAgentFactory
from .worker_manager import worker_manager, get_worker_for_slug, get_worker_card_for_slug


def __getattr__(name):
    """Lazy worker exports.

    Some worker implementations require optional LLM packages. Package-level
    imports should not fail when callers only need the factory or manager.
    """
    if name == "FlightSpecialistWorkerAgent":
        from .modules.flight_specialist_worker.agent import FlightSpecialistWorkerAgent

        return FlightSpecialistWorkerAgent
    if name == "GeneralWorkerAgent":
        from .implementations.general_worker import GeneralWorkerAgent

        return GeneralWorkerAgent
    raise AttributeError(name)

__all__ = [
    'BaseWorkerAgent',
    'WorkerAgentFactory',
    'worker_manager',
    'get_worker_for_slug',
    'get_worker_card_for_slug',
    'GeneralWorkerAgent',
    'FlightSpecialistWorkerAgent'
]
