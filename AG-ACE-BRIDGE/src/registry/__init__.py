"""
Agent registry module for AG-ACE-BRIDGE

Provides agent registration, discovery, and capability matching.
Also includes Pattern Registry for AutoGen Studio integration.
"""

from .capabilities import (
    Capability,
    AgentCapabilities,
    ALL_AGENT_CAPABILITIES,
    get_capabilities,
    get_agents_by_task_type,
    get_agents_by_adapter,
    find_best_agents,
)

from .agent_registry import (
    AgentRegistry,
    AgentStatus,
    get_registry,
    reset_registry,
)

from .pattern_registry import (
    PatternRegistry,
    RegisteredPattern,
    PatternStatus,
    PatternType,
)

__all__ = [
    # Capabilities
    "Capability",
    "AgentCapabilities",
    "ALL_AGENT_CAPABILITIES",
    "get_capabilities",
    "get_agents_by_task_type",
    "get_agents_by_adapter",
    "find_best_agents",
    # Agent Registry
    "AgentRegistry",
    "AgentStatus",
    "get_registry",
    "reset_registry",
    # Pattern Registry (AutoGen Studio)
    "PatternRegistry",
    "RegisteredPattern",
    "PatternStatus",
    "PatternType",
]
