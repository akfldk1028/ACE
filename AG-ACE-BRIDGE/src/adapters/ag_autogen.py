"""
AG Autogen Adapter for AG-ACE-BRIDGE

HTTP adapter for AG autogen_a2a_kit agents.
Communicates via A2A Protocol over HTTP.
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.adapters.base import AgentAdapter
from src.utils.models import Task, Result, ResultStatus, AgentType, TaskType, AgentMcpConfig
from src.utils.logger import Loggers
from src.utils.config import get_settings


class AGAutogenAdapter(AgentAdapter):
    """
    Adapter for AG autogen_a2a_kit agents.

    Connects to autogen agents via HTTP using the A2A Protocol.
    Supports 5 different agent types:
    - Research: Information gathering
    - Analyst: Data analysis
    - Writer: Documentation
    - Reviewer: Quality assessment
    - Coordinator: Task orchestration

    Example:
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)
        await adapter.initialize()

        task = Task(type=TaskType.RESEARCH, description="Research topic X")
        result = await adapter.execute(task, {})
    """

    # Agent endpoint mappings
    AGENT_ENDPOINTS = {
        AgentType.AG_RESEARCH: "/agents/research",
        AgentType.AG_ANALYST: "/agents/analyst",
        AgentType.AG_WRITER: "/agents/writer",
        AgentType.AG_REVIEWER: "/agents/reviewer",
        AgentType.AG_COORDINATOR: "/agents/coordinator",
    }

    CAPABILITIES_MAP = {
        AgentType.AG_RESEARCH: [
            "information-gathering", "web-search", "source-validation",
        ],
        AgentType.AG_ANALYST: [
            "data-analysis", "pattern-detection", "reporting",
        ],
        AgentType.AG_WRITER: [
            "documentation", "content-creation", "technical-writing",
        ],
        AgentType.AG_REVIEWER: [
            "feedback", "quality-assessment",
        ],
        AgentType.AG_COORDINATOR: [
            "orchestration", "task-routing",
        ],
    }

    def __init__(self, agent_type: AgentType):
        """
        Initialize AG Autogen adapter.

        Args:
            agent_type: Type of AG autogen agent
        """
        if agent_type not in self.AGENT_ENDPOINTS:
            raise ValueError(f"Invalid AG autogen agent type: {agent_type}")

        self.agent_type = agent_type
        self.endpoint_path = self.AGENT_ENDPOINTS[agent_type]

        settings = get_settings()
        base_url = settings.ag_autogen_url

        super().__init__(
            name=agent_type.value,
            endpoint_url=f"{base_url}{self.endpoint_path}",
        )

        self.logger = Loggers.adapter()
        self.base_url = base_url
        self.timeout = settings.adapter_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client"""
        await super().initialize()

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        self.logger.info(
            "ag_autogen_adapter_initialized",
            agent_type=self.agent_type.value,
            endpoint=self.endpoint_url,
        )

    async def shutdown(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
        await super().shutdown()
        self.logger.info("ag_autogen_adapter_shutdown", agent_type=self.agent_type.value)

    async def execute(self, task: Task, context: Dict[str, Any], mcp_config: Optional[AgentMcpConfig] = None) -> Result:
        """
        Execute a task via HTTP.

        Args:
            task: Task to execute
            context: Accumulated context

        Returns:
            Result with output or error
        """
        if not self._client:
            await self.initialize()

        start_time = datetime.now()
        self.logger.info(
            "ag_autogen_execute_start",
            task_id=task.id,
            agent_type=self.agent_type.value,
            endpoint=self.endpoint_path,
        )

        try:
            # Build request payload (A2A Protocol format)
            payload = self._build_a2a_request(task, context)

            # Send request
            response = await self._client.post(
                self.endpoint_path,
                json=payload,
            )

            response.raise_for_status()
            response_data = response.json()

            # Parse response
            output = self._parse_a2a_response(response_data)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            result = Result(
                task_id=task.id,
                status=ResultStatus.SUCCESS,
                output=output,
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

            self.logger.info(
                "ag_autogen_execute_success",
                task_id=task.id,
                execution_time_ms=execution_time,
            )

            return result

        except httpx.HTTPStatusError as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "ag_autogen_http_error",
                task_id=task.id,
                status_code=e.response.status_code,
                error=str(e),
            )

            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"HTTP {e.response.status_code}: {str(e)}",
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "ag_autogen_execute_failed",
                task_id=task.id,
                error=str(e),
            )

            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=str(e),
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

    def _build_a2a_request(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build A2A Protocol request payload.

        Args:
            task: Task to execute
            context: Context from previous stages

        Returns:
            A2A Protocol formatted request
        """
        return {
            "jsonrpc": "2.0",
            "method": "execute",
            "params": {
                "task_id": task.id,
                "task_type": task.type if isinstance(task.type, str) else task.type.value,
                "description": task.description,
                "context": context,
                "requirements": task.requirements,
                "metadata": {
                    "priority": task.priority if isinstance(task.priority, str) else task.priority.value,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                },
            },
            "id": task.id,
        }

    def _parse_a2a_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse A2A Protocol response.

        Args:
            response: Raw response data

        Returns:
            Parsed output
        """
        # A2A Protocol response format
        if "result" in response:
            return response["result"]
        elif "error" in response:
            raise Exception(response["error"].get("message", "Unknown error"))
        else:
            return response

    async def health_check(self) -> bool:
        """Check if AG autogen endpoint is accessible"""
        if not self._client:
            try:
                await self.initialize()
            except Exception:
                return False

        try:
            # Try health endpoint
            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.debug("ag_autogen_health_check_failed", error=str(e))
            return False

    def get_capabilities(self) -> List[str]:
        """Get capabilities for this agent type"""
        return self.CAPABILITIES_MAP.get(self.agent_type, [])


# Factory functions for each agent type
def create_research_adapter() -> AGAutogenAdapter:
    """Create AG Research adapter"""
    return AGAutogenAdapter(AgentType.AG_RESEARCH)


def create_analyst_adapter() -> AGAutogenAdapter:
    """Create AG Analyst adapter"""
    return AGAutogenAdapter(AgentType.AG_ANALYST)


def create_writer_adapter() -> AGAutogenAdapter:
    """Create AG Writer adapter"""
    return AGAutogenAdapter(AgentType.AG_WRITER)


def create_reviewer_adapter() -> AGAutogenAdapter:
    """Create AG Reviewer adapter"""
    return AGAutogenAdapter(AgentType.AG_REVIEWER)


def create_coordinator_adapter() -> AGAutogenAdapter:
    """Create AG Coordinator adapter"""
    return AGAutogenAdapter(AgentType.AG_COORDINATOR)
