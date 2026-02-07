"""
AutoGen Studio Adapter

Executes workflows designed in AutoGen Studio.
Supports both direct Python execution and HTTP API calls.

Usage:
    adapter = AutogenStudioAdapter()
    await adapter.initialize()

    # Execute a workflow
    result = await adapter.execute_workflow(workflow_data)
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json

from src.adapters.base import AgentAdapter
from src.utils.models import Task, Result, AgentMcpConfig
from src.utils.logger import get_logger

logger = get_logger("autogen_studio_adapter")


@dataclass
class WorkflowResult:
    """Result from AutoGen Studio workflow execution"""
    success: bool
    workflow_name: str
    output: Any
    messages: List[Dict[str, Any]]
    duration_seconds: float
    error: Optional[str] = None


class AutogenStudioAdapter(AgentAdapter):
    """
    Adapter for executing AutoGen Studio workflows.

    Supports two modes:
    1. Direct execution using autogenstudio Python package
    2. HTTP API execution (if AutoGen Studio server is running)
    """

    def __init__(
        self,
        studio_url: Optional[str] = None,
        use_direct: bool = True,
        enable_shared_memory: bool = True,
    ):
        """
        Initialize AutoGen Studio adapter.

        Args:
            studio_url: AutoGen Studio server URL (for HTTP mode)
            use_direct: Use direct Python execution (recommended)
            enable_shared_memory: Enable SharedMemory integration
        """
        self.studio_url = studio_url or "http://localhost:8081"
        super().__init__(
            name="autogen_studio",
            endpoint_url=self.studio_url,
            enable_shared_memory=enable_shared_memory,
        )
        self.use_direct = use_direct
        self._studio = None
        self._team_manager_class = None
        self._component_factory_class = None
        self._http_client = None

    async def initialize(self) -> bool:
        """Initialize the adapter"""
        if self._is_initialized:
            return True

        # Call parent initialize first (for SharedMemory)
        await super().initialize()

        if self.use_direct:
            try:
                # Try to import autogenstudio
                from autogenstudio.database import ComponentFactory
                from autogenstudio.teammanager import TeamManager

                self._team_manager_class = TeamManager
                self._component_factory_class = ComponentFactory

                logger.info("AutoGen Studio adapter initialized (direct mode)")
                return True

            except ImportError as e:
                logger.warning(f"autogenstudio package not available: {e}")
                self.use_direct = False

        # Fallback to HTTP mode
        try:
            import httpx
            self._http_client = httpx.AsyncClient(
                base_url=self.studio_url,
                timeout=300.0,
            )
            logger.info(f"AutoGen Studio adapter initialized (HTTP mode: {self.studio_url})")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize AutoGen Studio adapter: {e}")
            self._is_initialized = False
            return False

    async def health_check(self) -> bool:
        """Check if AutoGen Studio is available"""
        if self.use_direct:
            return self._is_initialized

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.studio_url}/api/version", timeout=5.0)
                return resp.status_code == 200
        except Exception:
            return False

    def get_capabilities(self) -> List[str]:
        """Get the list of capabilities this adapter provides"""
        return [
            "workflow_execution",
            "team_orchestration",
            "multi_agent_coordination",
            "autogen_studio_integration",
        ]

    async def execute(self, task: Task, context: Dict[str, Any], mcp_config: Optional[AgentMcpConfig] = None) -> Result:
        """
        Execute a task using AutoGen Studio workflow.

        The task's input should contain workflow definition or reference.
        """
        # mcp_config maps to McpWorkbench components in AutoGen (MCP server/tool definitions
        # are translated to AutoGen's native McpWorkbench tool configuration when available).
        start_time = datetime.now()

        try:
            # Extract workflow from task
            workflow_data = task.input.get("workflow")
            if not workflow_data:
                workflow_data = task.input  # Assume entire input is workflow

            # Execute workflow
            workflow_result = await self.execute_workflow(
                workflow_data=workflow_data,
                task_description=task.description,
                context=context,
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return Result(
                success=workflow_result.success,
                output={
                    "workflow_name": workflow_result.workflow_name,
                    "result": workflow_result.output,
                    "messages": workflow_result.messages,
                },
                error=workflow_result.error,
                execution_time_ms=execution_time,
                insights=[
                    f"Executed workflow: {workflow_result.workflow_name}",
                    f"Duration: {workflow_result.duration_seconds:.2f}s",
                ],
            )

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"AutoGen Studio execution failed: {e}")

            return Result(
                success=False,
                output={},
                error=str(e),
                execution_time_ms=execution_time,
                insights=[],
            )

    async def execute_workflow(
        self,
        workflow_data: Dict[str, Any],
        task_description: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute an AutoGen Studio workflow.

        Args:
            workflow_data: Workflow definition (nodes, config, etc.)
            task_description: Task to run through the workflow
            context: Additional context

        Returns:
            WorkflowResult with execution details
        """
        workflow_name = workflow_data.get("name", "unnamed_workflow")
        start_time = datetime.now()

        logger.info(
            "executing_autogen_workflow",
            workflow_name=workflow_name,
            task=task_description[:100] if task_description else "none",
        )

        try:
            if self.use_direct and self._is_initialized:
                result = await self._execute_direct(workflow_data, task_description, context)
            else:
                result = await self._execute_http(workflow_data, task_description, context)

            duration = (datetime.now() - start_time).total_seconds()
            result.duration_seconds = duration

            logger.info(
                "autogen_workflow_completed",
                workflow_name=workflow_name,
                success=result.success,
                duration=f"{duration:.2f}s",
            )

            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                "autogen_workflow_failed",
                workflow_name=workflow_name,
                error=str(e),
            )

            return WorkflowResult(
                success=False,
                workflow_name=workflow_name,
                output=None,
                messages=[],
                duration_seconds=duration,
                error=str(e),
            )

    async def _execute_direct(
        self,
        workflow_data: Dict[str, Any],
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute workflow directly using autogenstudio package"""
        workflow_name = workflow_data.get("name", "unnamed")

        try:
            # Build team from workflow data
            team_config = self._workflow_to_team_config(workflow_data)

            # Create team manager
            team_manager = self._team_manager_class()

            # Run the task through the team
            # Note: This is a simplified version - actual implementation
            # would need to match autogenstudio's API
            run_result = await asyncio.to_thread(
                team_manager.run,
                task=task_description,
                team_config=team_config,
            )

            # Extract messages and output
            messages = []
            output = None

            if hasattr(run_result, 'messages'):
                messages = run_result.messages
            if hasattr(run_result, 'output'):
                output = run_result.output
            else:
                output = str(run_result)

            return WorkflowResult(
                success=True,
                workflow_name=workflow_name,
                output=output,
                messages=messages,
                duration_seconds=0,
            )

        except Exception as e:
            return WorkflowResult(
                success=False,
                workflow_name=workflow_name,
                output=None,
                messages=[],
                duration_seconds=0,
                error=str(e),
            )

    async def _execute_http(
        self,
        workflow_data: Dict[str, Any],
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute workflow via AutoGen Studio HTTP API"""
        workflow_name = workflow_data.get("name", "unnamed")

        try:
            import httpx

            # AutoGen Studio API endpoint for running workflows
            async with httpx.AsyncClient() as client:
                # Create a session/run
                response = await client.post(
                    f"{self.studio_url}/api/runs",
                    json={
                        "workflow": workflow_data,
                        "task": task_description,
                        "context": context or {},
                    },
                    timeout=300.0,
                )

                if response.status_code != 200:
                    return WorkflowResult(
                        success=False,
                        workflow_name=workflow_name,
                        output=None,
                        messages=[],
                        duration_seconds=0,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                result = response.json()

                return WorkflowResult(
                    success=result.get("success", True),
                    workflow_name=workflow_name,
                    output=result.get("output"),
                    messages=result.get("messages", []),
                    duration_seconds=result.get("duration", 0),
                    error=result.get("error"),
                )

        except Exception as e:
            return WorkflowResult(
                success=False,
                workflow_name=workflow_name,
                output=None,
                messages=[],
                duration_seconds=0,
                error=str(e),
            )

    def _workflow_to_team_config(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AG-ACE workflow format to AutoGen Studio team config"""
        nodes = workflow_data.get("nodes", [])
        config = workflow_data.get("config", {})

        # Build agents from nodes
        agents = []
        for node in nodes:
            agent_config = {
                "name": node.get("id", "agent"),
                "agent_type": self._map_agent_type(node.get("agent", "")),
                "system_message": node.get("system_prompt", ""),
                "model": config.get("model", "gpt-4"),
            }
            agents.append(agent_config)

        return {
            "name": workflow_data.get("name", "workflow"),
            "agents": agents,
            "type": "sequential" if len(nodes) <= 2 else "group",
        }

    def _map_agent_type(self, ag_ace_type: str) -> str:
        """Map AG-ACE agent type to AutoGen Studio agent type"""
        mapping = {
            "AUTO_CLAUDE_PLANNER": "assistant",
            "AUTO_CLAUDE_CODER": "assistant",
            "AUTO_CLAUDE_QA_REVIEWER": "assistant",
            "AUTO_CLAUDE_QA_FIXER": "assistant",
            "AG_RESEARCH": "assistant",
            "AG_A2A_CALCULATOR": "assistant",
            "AG_A2A_POETRY": "assistant",
        }
        return mapping.get(ag_ace_type, "assistant")

    async def close(self):
        """Clean up resources"""
        if hasattr(self, '_http_client') and self._http_client:
            await self._http_client.aclose()
        logger.info("AutoGen Studio adapter closed")


# Convenience function for pattern execution
async def execute_pattern_with_autogen(
    pattern_data: Dict[str, Any],
    task_description: str = "",
) -> WorkflowResult:
    """
    Execute an AG-ACE pattern using AutoGen Studio.

    Args:
        pattern_data: Pattern definition from PatternRegistry
        task_description: Task to execute

    Returns:
        WorkflowResult with execution details
    """
    adapter = AutogenStudioAdapter()
    await adapter.initialize()

    try:
        return await adapter.execute_workflow(
            workflow_data=pattern_data,
            task_description=task_description,
        )
    finally:
        await adapter.close()
