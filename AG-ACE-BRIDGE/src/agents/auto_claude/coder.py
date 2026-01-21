"""
Auto-Claude Coder Agent

Responsible for:
- Code implementation
- Following existing patterns
- Writing clean, maintainable code
- Creating tests
"""

import json
from pathlib import Path
from typing import Dict, Any

from src.agents.auto_claude.base import BaseAutoClaudeAgent


class AutoClaudeCoder(BaseAutoClaudeAgent):
    """
    Auto-Claude Coder Agent.

    Implements features and writes code based on plans
    and specifications.
    """

    SYSTEM_PROMPT = (
        "You are an expert full-stack developer. "
        "Your role is to implement features based on the provided plan and specifications. "
        "Write clean, maintainable code following best practices. "
        "Use existing patterns in the codebase and verify your work through testing."
    )

    CAPABILITIES = [
        "implementation",
        "refactoring",
        "24/7-autonomous",
        "code-generation",
        "testing",
    ]

    def __init__(self):
        """Initialize Coder agent."""
        super().__init__(
            name="auto_claude_coder",
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
        Implement code based on task and plan.

        Args:
            task_description: Description of the task
            context: Context including plan from planner
            project_dir: Working directory

        Returns:
            Implementation result with files modified
        """
        plan = context.get("plan", "")
        requirements = context.get("requirements", {})

        prompt = f"""
Implement the following task.

Task: {task_description}

Implementation Plan:
{plan if plan else "No plan provided. Implement based on the task description."}

Requirements:
{json.dumps(requirements, indent=2) if requirements else "None specified"}

Instructions:
1. Analyze the existing codebase structure
2. Implement the required changes
3. Follow existing code patterns and conventions
4. Write clean, maintainable code
5. Add necessary tests if applicable
6. Commit your changes with a descriptive message

Begin implementation.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "code_generated": True,
                "response": response,
                "files_modified": [],  # Would need to parse from response
                "status": "implemented",
                "next_action": "qa_review",
            }

        except Exception as e:
            self.logger.error("coder_execution_failed", error=str(e))
            return {
                "code_generated": False,
                "status": "failed",
                "error": str(e),
                "next_action": "retry",
            }

    async def implement_feature(
        self,
        feature_description: str,
        plan: str,
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Implement a specific feature.

        Args:
            feature_description: Feature to implement
            plan: Implementation plan
            project_dir: Working directory

        Returns:
            Implementation result
        """
        return await self.execute(
            task_description=feature_description,
            context={"plan": plan},
            project_dir=project_dir,
        )

    async def refactor_code(
        self,
        refactor_description: str,
        target_files: list,
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Refactor existing code.

        Args:
            refactor_description: What to refactor and how
            target_files: Files to refactor
            project_dir: Working directory

        Returns:
            Refactoring result
        """
        prompt = f"""
Refactor the following code.

Refactoring Goal: {refactor_description}

Target Files:
{json.dumps(target_files, indent=2)}

Instructions:
1. Read and understand the existing code
2. Plan the refactoring approach
3. Make incremental changes
4. Ensure tests still pass
5. Commit with descriptive messages

Begin refactoring.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "refactored": True,
                "response": response,
                "status": "refactored",
            }

        except Exception as e:
            self.logger.error("refactor_execution_failed", error=str(e))
            return {
                "refactored": False,
                "status": "failed",
                "error": str(e),
            }
