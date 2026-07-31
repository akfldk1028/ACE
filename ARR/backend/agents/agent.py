"""Global ARR agent-infrastructure adapter.

This module gives the global ``ARR/backend/agents`` folder the same code-facing
entrypoint shape as domain agent folders without moving Django views, URLs, or
worker runtime files.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalAgentLayer:
    """Inspectable metadata for the global A2A infrastructure layer."""

    agent_id: str = "arr_global_agents"
    scope: str = "global_infrastructure"
    discovery_module: str = "agents.well_known_urls"
    chat_module: str = "agents.views"
    worker_layer: str = "agents.worker_agents"


def get_agent_layer() -> GlobalAgentLayer:
    return GlobalAgentLayer()


__all__ = ["GlobalAgentLayer", "get_agent_layer"]
