"""
Auto-Claude Adapter for AG-ACE-BRIDGE

Thin adapter layer that wraps Auto-Claude agents from src/agents/auto_claude.
Provides the AgentAdapter interface for orchestrator integration.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.adapters.base import AgentAdapter
from src.utils.models import Task, Result, ResultStatus, AgentType
from src.utils.logger import Loggers
from src.utils.config import get_settings

# Import agents and utilities from new agents module
from src.agents.auto_claude import (
    AutoClaudePlanner,
    AutoClaudeCoder,
    AutoClaudeQAReviewer,
    AutoClaudeQAFixer,
    get_oauth_token,
    require_oauth_token,
    CLAUDE_SDK_AVAILABLE,
)

# Re-export for backward compatibility
__all__ = [
    "AutoClaudeAdapter",
    "get_oauth_token",
    "require_oauth_token",
    "CLAUDE_SDK_AVAILABLE",
    "create_planner_adapter",
    "create_coder_adapter",
    "create_qa_reviewer_adapter",
    "create_qa_fixer_adapter",
]


class AutoClaudeAdapter(AgentAdapter):
    """
    Adapter for Auto-Claude agents.

    Wraps the agent implementations from src/agents/auto_claude/
    to provide the AgentAdapter interface.
    """

    # Agent type to agent class mapping
    AGENT_CLASSES = {
        AgentType.AUTO_CLAUDE_PLANNER: AutoClaudePlanner,
        AgentType.AUTO_CLAUDE_CODER: AutoClaudeCoder,
        AgentType.AUTO_CLAUDE_QA_REVIEWER: AutoClaudeQAReviewer,
        AgentType.AUTO_CLAUDE_QA_FIXER: AutoClaudeQAFixer,
    }

    # Agent role mappings (for backward compatibility)
    AGENT_ROLES = {
        AgentType.AUTO_CLAUDE_PLANNER: "planner",
        AgentType.AUTO_CLAUDE_CODER: "coder",
        AgentType.AUTO_CLAUDE_QA_REVIEWER: "qa_reviewer",
        AgentType.AUTO_CLAUDE_QA_FIXER: "qa_fixer",
    }

    CAPABILITIES_MAP = {
        AgentType.AUTO_CLAUDE_PLANNER: [
            "planning", "task-decomposition", "spec-analysis",
        ],
        AgentType.AUTO_CLAUDE_CODER: [
            "implementation", "refactoring", "24/7-autonomous",
        ],
        AgentType.AUTO_CLAUDE_QA_REVIEWER: [
            "code-review", "testing", "validation",
        ],
        AgentType.AUTO_CLAUDE_QA_FIXER: [
            "debugging", "issue-resolution",
        ],
    }

    def __init__(self, agent_type: AgentType):
        """
        Initialize Auto-Claude adapter.

        Args:
            agent_type: Type of Auto-Claude agent
        """
        if agent_type not in self.AGENT_CLASSES:
            raise ValueError(f"Invalid Auto-Claude agent type: {agent_type}")

        self.agent_type = agent_type
        self.role = self.AGENT_ROLES[agent_type]

        super().__init__(
            name=agent_type.value,
            endpoint_url=None,  # SDK-based, not HTTP
        )

        self.logger = Loggers.adapter()
        self.settings = get_settings()

        # Create the actual agent instance
        agent_class = self.AGENT_CLASSES[agent_type]
        self._agent = agent_class()
        self._oauth_token: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the underlying agent."""
        await super().initialize()
        await self._agent.initialize()

        # Get OAuth token for health check purposes
        self._oauth_token = get_oauth_token()

        self.logger.info(
            "auto_claude_adapter_initialized",
            agent_type=self.agent_type.value,
            role=self.role,
            sdk_available=CLAUDE_SDK_AVAILABLE,
            oauth_available=self._oauth_token is not None,
        )

    async def shutdown(self) -> None:
        """Shutdown the underlying agent."""
        await self._agent.shutdown()
        await super().shutdown()
        self.logger.info("auto_claude_adapter_shutdown", agent_type=self.agent_type.value)

    async def execute(self, task: Task, context: Dict[str, Any]) -> Result:
        """
        Execute a task using the underlying agent.

        Args:
            task: Task to execute
            context: Accumulated context

        Returns:
            Result with output or error
        """
        start_time = datetime.now()
        self.logger.info(
            "auto_claude_execute_start",
            task_id=task.id,
            role=self.role,
            task_type=task.type,
        )

        try:
            # Check prerequisites
            if not CLAUDE_SDK_AVAILABLE:
                return Result(
                    task_id=task.id,
                    status=ResultStatus.FAILED,
                    error="Claude Agent SDK not available. Install: pip install claude-agent-sdk",
                    agent_used=self.agent_type.value,
                )

            if not get_oauth_token():
                return Result(
                    task_id=task.id,
                    status=ResultStatus.FAILED,
                    error="No OAuth token. Run 'claude' and '/login' to authenticate.",
                    agent_used=self.agent_type.value,
                )

            # Prepare execution context
            project_dir = Path(context.get("project_dir", "."))

            # Execute using the underlying agent
            output = await self._agent.execute(
                task_description=task.description,
                context={
                    "requirements": task.requirements,
                    "context": task.context,
                    **context,
                },
                project_dir=project_dir,
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            result = Result(
                task_id=task.id,
                status=ResultStatus.SUCCESS,
                output=output,
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

            self.logger.info(
                "auto_claude_execute_success",
                task_id=task.id,
                execution_time_ms=execution_time,
            )

            return result

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "auto_claude_execute_failed",
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

    async def health_check(self) -> bool:
        """Check if the agent is healthy."""
        return await self._agent.health_check()

    def get_capabilities(self) -> List[str]:
        """Get capabilities for this agent type."""
        return self.CAPABILITIES_MAP.get(self.agent_type, [])


# Factory functions for each agent type
def create_planner_adapter() -> AutoClaudeAdapter:
    """Create Auto-Claude Planner adapter."""
    return AutoClaudeAdapter(AgentType.AUTO_CLAUDE_PLANNER)


def create_coder_adapter() -> AutoClaudeAdapter:
    """Create Auto-Claude Coder adapter."""
    return AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)


def create_qa_reviewer_adapter() -> AutoClaudeAdapter:
    """Create Auto-Claude QA Reviewer adapter."""
    return AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_REVIEWER)


def create_qa_fixer_adapter() -> AutoClaudeAdapter:
    """Create Auto-Claude QA Fixer adapter."""
    return AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_FIXER)
