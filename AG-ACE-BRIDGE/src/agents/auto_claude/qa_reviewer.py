"""
Auto-Claude QA Reviewer Agent

Responsible for:
- Code review
- Running tests
- Validating acceptance criteria
- Identifying bugs and issues
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from src.agents.auto_claude.base import BaseAutoClaudeAgent


class AutoClaudeQAReviewer(BaseAutoClaudeAgent):
    """
    Auto-Claude QA Reviewer Agent.

    Reviews code changes, runs tests, and validates
    implementation meets requirements.
    """

    SYSTEM_PROMPT = (
        "You are an expert QA engineer. "
        "Your role is to review code changes and validate they meet acceptance criteria. "
        "Run tests, check for bugs, verify edge cases, and ensure code quality. "
        "Provide detailed feedback on any issues found."
    )

    CAPABILITIES = [
        "code-review",
        "testing",
        "validation",
        "bug-detection",
        "quality-assessment",
    ]

    def __init__(self):
        """Initialize QA Reviewer agent."""
        super().__init__(
            name="auto_claude_qa_reviewer",
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
        Review code changes for a task.

        Args:
            task_description: Description of the implemented task
            context: Context including acceptance criteria
            project_dir: Working directory

        Returns:
            Review result with pass/fail and issues
        """
        requirements = context.get("requirements", {})
        acceptance_criteria = context.get("acceptance_criteria", [])

        prompt = f"""
Review the recent code changes for the following task.

Task: {task_description}

Requirements:
{json.dumps(requirements, indent=2) if requirements else "None specified"}

Acceptance Criteria:
{json.dumps(acceptance_criteria, indent=2) if acceptance_criteria else "None specified"}

Instructions:
1. Review the code changes made
2. Run existing tests to verify nothing is broken
3. Test the new functionality manually if needed
4. Check for:
   - Bugs or logical errors
   - Edge cases not handled
   - Code quality issues
   - Security concerns
   - Performance issues
5. Provide a detailed QA report

If issues are found, list them clearly. If all checks pass, confirm approval.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            # Parse response to determine if review passed
            response_lower = response.lower()
            review_passed = (
                "approved" in response_lower or
                "pass" in response_lower or
                "lgtm" in response_lower
            ) and (
                "fail" not in response_lower and
                "reject" not in response_lower
            )

            return {
                "review_passed": review_passed,
                "review_report": response,
                "issues_found": [] if review_passed else ["See review report"],
                "status": "reviewed",
                "next_action": "merge" if review_passed else "fix",
            }

        except Exception as e:
            self.logger.error("qa_review_execution_failed", error=str(e))
            return {
                "review_passed": False,
                "status": "failed",
                "error": str(e),
                "next_action": "retry",
            }

    async def review_code(
        self,
        files_to_review: List[str],
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Review specific code files.

        Args:
            files_to_review: List of file paths to review
            project_dir: Working directory

        Returns:
            Code review result
        """
        prompt = f"""
Review the following code files for quality, bugs, and best practices.

Files to Review:
{json.dumps(files_to_review, indent=2)}

Check for:
1. Code quality and readability
2. Potential bugs or errors
3. Security vulnerabilities
4. Performance issues
5. Missing error handling
6. Test coverage

Provide detailed feedback for each file.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "review_complete": True,
                "feedback": response,
                "status": "reviewed",
            }

        except Exception as e:
            self.logger.error("code_review_failed", error=str(e))
            return {
                "review_complete": False,
                "status": "failed",
                "error": str(e),
            }

    async def run_tests(
        self,
        test_command: str,
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Run tests and report results.

        Args:
            test_command: Command to run tests
            project_dir: Working directory

        Returns:
            Test execution result
        """
        prompt = f"""
Run the tests and report the results.

Test Command: {test_command}

Instructions:
1. Execute the test command
2. Analyze the output
3. Report:
   - Total tests run
   - Tests passed
   - Tests failed
   - Any errors or issues
4. If tests fail, identify the cause

Execute the tests now.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            tests_passed = (
                "all tests pass" in response.lower() or
                "100%" in response or
                "0 failed" in response.lower()
            )

            return {
                "tests_run": True,
                "tests_passed": tests_passed,
                "test_report": response,
                "status": "tested",
            }

        except Exception as e:
            self.logger.error("test_execution_failed", error=str(e))
            return {
                "tests_run": False,
                "tests_passed": False,
                "status": "failed",
                "error": str(e),
            }
