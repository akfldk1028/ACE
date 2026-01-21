"""
Base Agent Adapter Interface

All adapters must implement this interface for consistent agent interaction.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from ..utils.models import Task, Result, AgentCapability


class AgentAdapter(ABC):
    """
    Base class for all agent adapters.

    Provides a consistent interface for executing tasks on different agent systems:
    - Auto-Claude (Claude Agent SDK)
    - AG autogen_a2a_kit (HTTP/A2A Protocol)
    - AG law-domain-agents (HTTP/FastAPI)
    """

    def __init__(self, name: str, endpoint_url: str = None):
        """
        Initialize the adapter.

        Args:
            name: Unique identifier for this adapter
            endpoint_url: URL for HTTP-based agents (optional)
        """
        self.name = name
        self.endpoint_url = endpoint_url
        self._is_initialized = False

    async def initialize(self) -> None:
        """
        Initialize the adapter (e.g., establish connections).
        Called once before first use.
        """
        self._is_initialized = True

    async def shutdown(self) -> None:
        """
        Clean up resources when shutting down.
        """
        self._is_initialized = False

    @abstractmethod
    async def execute(self, task: Task, context: Dict[str, Any]) -> Result:
        """
        Execute a task using this agent.

        Args:
            task: The task to execute
            context: Accumulated context from previous pipeline stages

        Returns:
            Result containing output, status, and any follow-up tasks
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the agent is available and healthy.

        Returns:
            True if agent is available, False otherwise
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this agent provides.

        Returns:
            List of capability strings (e.g., ["research", "analysis"])
        """
        pass

    def get_agent_info(self) -> AgentCapability:
        """
        Get full agent capability information.

        Returns:
            AgentCapability model with all metadata
        """
        from ..utils.models import AgentType

        return AgentCapability(
            agent=AgentType(self.name) if self.name in [e.value for e in AgentType] else AgentType.AUTO_CLAUDE_CODER,
            capabilities=self.get_capabilities(),
            description=self.__class__.__doc__ or f"Adapter for {self.name}",
            endpoint_url=self.endpoint_url,
            is_available=self._is_initialized,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, initialized={self._is_initialized})"
