"""Worker-agent layer adapter.

The executable worker implementations remain in their stable Django import
paths, while GitAgent-style module folders expose identity, rules, cards, and
contracts.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerAgentLayer:
    agent_id: str = "arr_worker_agents"
    scope: str = "global_worker_layer"
    factory_module: str = "agents.worker_agents.worker_factory"
    manager_module: str = "agents.worker_agents.worker_manager"
    modules_package: str = "agents.worker_agents.modules"


def get_worker_layer() -> WorkerAgentLayer:
    return WorkerAgentLayer()


__all__ = ["WorkerAgentLayer", "get_worker_layer"]
