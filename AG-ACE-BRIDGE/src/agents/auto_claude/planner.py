"""
Auto-Claude Planner Agent

Responsible for:
- Analyzing requirements
- Creating implementation plans
- Breaking down complex tasks
- Identifying dependencies and risks
"""

import json
from pathlib import Path
from typing import Dict, Any

from src.agents.auto_claude.base import BaseAutoClaudeAgent


class AutoClaudePlanner(BaseAutoClaudeAgent):
    """
    Auto-Claude Planner Agent.

    Analyzes tasks and creates detailed implementation plans
    with subtasks, dependencies, and execution order.
    """

    SYSTEM_PROMPT = (
        "You are an expert software architect and planner. "
        "Your role is to analyze requirements and create detailed implementation plans. "
        "Break down complex tasks into smaller, manageable subtasks. "
        "Consider dependencies, potential risks, and optimal execution order."
    )

    CAPABILITIES = [
        "planning",
        "task-decomposition",
        "spec-analysis",
        "dependency-mapping",
        "risk-assessment",
    ]

    def __init__(self):
        """Initialize Planner agent."""
        super().__init__(
            name="auto_claude_planner",
            system_prompt=self.SYSTEM_PROMPT,
            capabilities=self.CAPABILITIES,
        )

    async def execute(
        self,
        task_description: str,
        context: Dict[str, Any],
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Create implementation plan for a task.

        Args:
            task_description: Description of the task to plan
            context: Context from previous stages
            project_dir: Working directory

        Returns:
            Plan with subtasks, dependencies, and execution order
        """
        requirements = context.get("requirements", {})
        existing_context = context.get("context", {})

        prompt = f"""
Analyze the following task and create a detailed implementation plan.

Task: {task_description}

Requirements:
{json.dumps(requirements, indent=2) if requirements else "None specified"}

Context:
{json.dumps(existing_context, indent=2) if existing_context else "None provided"}

Please provide:
1. A breakdown of subtasks needed
2. Dependencies between subtasks
3. Estimated complexity for each (low/medium/high)
4. Recommended execution order
5. Potential risks and mitigations

Output your plan in a structured format.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "plan": response,
                "status": "planned",
                "next_action": "code",
            }

        except Exception as e:
            self.logger.error("planner_execution_failed", error=str(e))
            return {
                "plan": f"Planning failed: {e}. Manual planning required.",
                "status": "failed",
                "error": str(e),
            }

    async def decompose_task(
        self,
        task_description: str,
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Decompose a complex task into subtasks.

        Args:
            task_description: Complex task to decompose
            project_dir: Working directory

        Returns:
            List of subtasks with metadata
        """
        prompt = f"""
Decompose the following task into smaller, actionable subtasks.

Task: {task_description}

For each subtask, provide:
- Title
- Description
- Estimated complexity (low/medium/high)
- Dependencies (which subtasks must be completed first)

Output as a numbered list.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "subtasks": response,
                "status": "decomposed",
            }

        except Exception as e:
            self.logger.error("task_decomposition_failed", error=str(e))
            return {
                "subtasks": [],
                "status": "failed",
                "error": str(e),
            }
