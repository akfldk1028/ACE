"""
Agent Registry for AG/Auto-Claude

Central registry for all agents with health monitoring,
capability matching, and dynamic agent selection.
"""

import asyncio
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from src.utils.models import Task, AgentType, TaskType
from src.utils.logger import Loggers
from src.registry.capabilities import (
    AgentCapabilities,
    ALL_AGENT_CAPABILITIES,
    get_capabilities,
    get_agents_by_task_type,
    find_best_agents,
)


@dataclass
class AgentStatus:
    """Runtime status of an agent"""
    agent_type: AgentType
    is_available: bool = True
    is_healthy: bool = True
    current_task_id: Optional[str] = None

    # Health tracking
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0

    # Performance metrics
    avg_response_time_ms: float = 0.0
    last_response_time_ms: Optional[int] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.total_tasks_completed + self.total_tasks_failed
        if total == 0:
            return 1.0
        return self.total_tasks_completed / total

    def record_success(self, response_time_ms: int) -> None:
        """Record successful task completion"""
        self.total_tasks_completed += 1
        self.consecutive_failures = 0
        self.last_response_time_ms = response_time_ms
        self._update_avg_response_time(response_time_ms)

    def record_failure(self) -> None:
        """Record task failure"""
        self.total_tasks_failed += 1
        self.consecutive_failures += 1

    def _update_avg_response_time(self, new_time_ms: int) -> None:
        """Update rolling average response time"""
        if self.avg_response_time_ms == 0:
            self.avg_response_time_ms = float(new_time_ms)
        else:
            # Exponential moving average
            self.avg_response_time_ms = (
                0.8 * self.avg_response_time_ms + 0.2 * new_time_ms
            )


class AgentRegistry:
    """
    Central registry for managing all agents.

    Features:
    - Agent registration and discovery
    - Health monitoring
    - Capability-based selection
    - Load balancing

    Example:
        registry = AgentRegistry()
        registry.initialize()

        # Find agents for a task
        agents = registry.select_agents(task)

        # Record task completion
        registry.record_success(AgentType.AUTO_CLAUDE_CODER, 1500)
    """

    def __init__(self):
        self.logger = Loggers.registry()
        self._capabilities: Dict[AgentType, AgentCapabilities] = {}
        self._statuses: Dict[AgentType, AgentStatus] = {}
        self._adapters: Dict[AgentType, Any] = {}
        self._health_check_interval: int = 60  # seconds
        self._unhealthy_threshold: int = 3  # consecutive failures

    def initialize(self) -> None:
        """Initialize registry with all known agents"""
        for agent_type, capabilities in ALL_AGENT_CAPABILITIES.items():
            self._capabilities[agent_type] = capabilities
            self._statuses[agent_type] = AgentStatus(agent_type=agent_type)

        self.logger.info(
            "registry_initialized",
            agent_count=len(self._capabilities),
        )

    def register_adapter(self, agent_type: AgentType, adapter: Any) -> None:
        """
        Register an adapter for an agent.

        Args:
            agent_type: Type of agent
            adapter: Adapter instance
        """
        self._adapters[agent_type] = adapter
        self.logger.info("adapter_registered", agent_type=agent_type.value)

    def get_adapter(self, agent_type: AgentType) -> Optional[Any]:
        """Get adapter for an agent type"""
        return self._adapters.get(agent_type)

    def get_capabilities(self, agent_type: AgentType) -> Optional[AgentCapabilities]:
        """Get capabilities for an agent type"""
        return self._capabilities.get(agent_type)

    def get_status(self, agent_type: AgentType) -> Optional[AgentStatus]:
        """Get runtime status of an agent"""
        return self._statuses.get(agent_type)

    def get_all_agents(self) -> List[AgentType]:
        """Get all registered agent types"""
        return list(self._capabilities.keys())

    def get_available_agents(self) -> List[AgentType]:
        """Get all available (healthy and not busy) agents"""
        return [
            agent_type for agent_type, status in self._statuses.items()
            if status.is_available and status.is_healthy
        ]

    def select_agents(
        self,
        task: Task,
        limit: int = 3,
        prefer_available: bool = True,
    ) -> List[AgentType]:
        """
        Select best agents for a task.

        Args:
            task: Task to find agents for
            limit: Maximum number of agents to return
            prefer_available: Prefer currently available agents

        Returns:
            List of agent types, best match first
        """
        # Get candidates based on task type and requirements
        candidates = find_best_agents(
            task_type=TaskType(task.type) if isinstance(task.type, str) else task.type,
            requirements=task.requirements,
            limit=limit * 2,  # Get extra for filtering
        )

        # Score candidates based on availability and health
        scored = []
        for cap in candidates:
            status = self._statuses.get(cap.agent_type)
            if not status:
                continue

            score = cap.matches_requirements(task.requirements)

            # Bonus for availability
            if prefer_available:
                if status.is_available and status.is_healthy:
                    score += 0.3
                elif status.is_healthy:
                    score += 0.1

            # Bonus for success rate
            score += status.success_rate * 0.2

            # Penalty for consecutive failures
            score -= status.consecutive_failures * 0.1

            scored.append((score, cap.agent_type))

        # Sort by score and return
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [agent_type for _, agent_type in scored[:limit]]

        self.logger.debug(
            "agents_selected",
            task_id=task.id,
            selected=[a.value for a in selected],
        )

        return selected

    def select_single_agent(
        self,
        task: Task,
        prefer_available: bool = True,
    ) -> Optional[AgentType]:
        """Select best single agent for a task"""
        agents = self.select_agents(task, limit=1, prefer_available=prefer_available)
        return agents[0] if agents else None

    def mark_busy(self, agent_type: AgentType, task_id: str) -> None:
        """Mark agent as busy with a task"""
        if agent_type in self._statuses:
            self._statuses[agent_type].is_available = False
            self._statuses[agent_type].current_task_id = task_id
            self.logger.debug("agent_busy", agent_type=agent_type.value, task_id=task_id)

    def mark_available(self, agent_type: AgentType) -> None:
        """Mark agent as available"""
        if agent_type in self._statuses:
            self._statuses[agent_type].is_available = True
            self._statuses[agent_type].current_task_id = None
            self.logger.debug("agent_available", agent_type=agent_type.value)

    def record_success(
        self,
        agent_type: AgentType,
        response_time_ms: int,
    ) -> None:
        """Record successful task completion"""
        if agent_type in self._statuses:
            self._statuses[agent_type].record_success(response_time_ms)
            self._statuses[agent_type].is_available = True
            self._statuses[agent_type].current_task_id = None
            self.logger.debug(
                "agent_success_recorded",
                agent_type=agent_type.value,
                response_time_ms=response_time_ms,
            )

    def record_failure(self, agent_type: AgentType) -> None:
        """Record task failure"""
        if agent_type in self._statuses:
            status = self._statuses[agent_type]
            status.record_failure()
            status.is_available = True
            status.current_task_id = None

            # Mark unhealthy if too many failures
            if status.consecutive_failures >= self._unhealthy_threshold:
                status.is_healthy = False
                self.logger.warning(
                    "agent_marked_unhealthy",
                    agent_type=agent_type.value,
                    consecutive_failures=status.consecutive_failures,
                )
            else:
                self.logger.warning(
                    "agent_failure_recorded",
                    agent_type=agent_type.value,
                    consecutive_failures=status.consecutive_failures,
                )

    def mark_healthy(self, agent_type: AgentType) -> None:
        """Mark agent as healthy (after recovery)"""
        if agent_type in self._statuses:
            self._statuses[agent_type].is_healthy = True
            self._statuses[agent_type].consecutive_failures = 0
            self._statuses[agent_type].last_health_check = datetime.now()
            self.logger.info("agent_marked_healthy", agent_type=agent_type.value)

    def mark_unhealthy(self, agent_type: AgentType) -> None:
        """Mark agent as unhealthy"""
        if agent_type in self._statuses:
            self._statuses[agent_type].is_healthy = False
            self.logger.warning("agent_marked_unhealthy", agent_type=agent_type.value)

    async def health_check(self, agent_type: AgentType) -> bool:
        """
        Perform health check on an agent.

        Args:
            agent_type: Agent to check

        Returns:
            True if healthy
        """
        adapter = self._adapters.get(agent_type)
        if not adapter:
            return False

        try:
            is_healthy = await adapter.health_check()
            if is_healthy:
                self.mark_healthy(agent_type)
            else:
                self.mark_unhealthy(agent_type)
            return is_healthy
        except Exception as e:
            self.logger.error(
                "health_check_failed",
                agent_type=agent_type.value,
                error=str(e),
            )
            self.mark_unhealthy(agent_type)
            return False

    async def health_check_all(self) -> Dict[AgentType, bool]:
        """
        Perform health check on all agents with registered adapters.

        Returns:
            Dict of agent type to health status
        """
        results = {}
        tasks = []

        for agent_type in self._adapters:
            tasks.append(self.health_check(agent_type))

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        for agent_type, result in zip(self._adapters.keys(), health_results):
            if isinstance(result, Exception):
                results[agent_type] = False
            else:
                results[agent_type] = result

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total = len(self._capabilities)
        available = len(self.get_available_agents())
        healthy = sum(1 for s in self._statuses.values() if s.is_healthy)
        busy = sum(1 for s in self._statuses.values() if not s.is_available)

        return {
            "total_agents": total,
            "available_agents": available,
            "healthy_agents": healthy,
            "busy_agents": busy,
            "adapters_registered": len(self._adapters),
        }

    def get_agent_stats(self, agent_type: AgentType) -> Optional[Dict[str, Any]]:
        """Get detailed stats for a specific agent"""
        status = self._statuses.get(agent_type)
        cap = self._capabilities.get(agent_type)

        if not status or not cap:
            return None

        return {
            "agent_type": agent_type.value,
            "name": cap.name,
            "is_available": status.is_available,
            "is_healthy": status.is_healthy,
            "current_task_id": status.current_task_id,
            "success_rate": status.success_rate,
            "avg_response_time_ms": status.avg_response_time_ms,
            "total_completed": status.total_tasks_completed,
            "total_failed": status.total_tasks_failed,
            "consecutive_failures": status.consecutive_failures,
            "capabilities": [c.name for c in cap.capabilities],
        }

    def get_agents_by_capability(self, capability: str) -> List[AgentType]:
        """Find agents that have a specific capability"""
        matching = []
        capability_lower = capability.lower()

        for agent_type, cap in self._capabilities.items():
            keywords = cap.get_all_keywords()
            cap_names = [c.name.lower() for c in cap.capabilities]

            if any(
                capability_lower in kw or capability_lower in name
                for kw in keywords
                for name in cap_names
            ):
                matching.append(agent_type)

        return matching


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get or create global registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
        _registry.initialize()
    return _registry


def reset_registry() -> None:
    """Reset global registry (for testing)"""
    global _registry
    _registry = None
