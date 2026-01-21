"""
Auto-Claude QA Fixer Agent

Responsible for:
- Fixing bugs found during QA
- Resolving issues from code review
- Debugging problems
- Ensuring fixes don't introduce new issues
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from src.agents.auto_claude.base import BaseAutoClaudeAgent


class AutoClaudeQAFixer(BaseAutoClaudeAgent):
    """
    Auto-Claude QA Fixer Agent.

    Fixes issues found during QA review and debugging.
    """

    SYSTEM_PROMPT = (
        "You are an expert debugger and issue resolver. "
        "Your role is to fix issues found during QA review. "
        "Analyze error messages, identify root causes, and implement fixes. "
        "Ensure fixes don't introduce new issues."
    )

    CAPABILITIES = [
        "debugging",
        "issue-resolution",
        "bug-fixing",
        "root-cause-analysis",
    ]

    def __init__(self):
        """Initialize QA Fixer agent."""
        super().__init__(
            name="auto_claude_qa_fixer",
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
        Fix issues found during QA review.

        Args:
            task_description: Original task description
            context: Context including issues from QA review
            project_dir: Working directory

        Returns:
            Fix result with applied fixes
        """
        issues = context.get("issues_found", [])
        review_report = context.get("review_report", "")

        prompt = f"""
Fix the issues found during QA review.

Task: {task_description}

Issues Found:
{json.dumps(issues, indent=2) if issues else review_report}

Instructions:
1. Analyze each issue carefully
2. Identify the root cause
3. Implement fixes
4. Verify the fix resolves the issue
5. Ensure no new issues are introduced
6. Commit the fixes with descriptive messages

Begin fixing issues.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "fixes_applied": True,
                "fix_report": response,
                "remaining_issues": [],
                "status": "fixed",
                "next_action": "qa_review",
            }

        except Exception as e:
            self.logger.error("qa_fixer_execution_failed", error=str(e))
            return {
                "fixes_applied": False,
                "status": "failed",
                "error": str(e),
                "next_action": "retry",
            }

    async def fix_bug(
        self,
        bug_description: str,
        error_message: str,
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Fix a specific bug.

        Args:
            bug_description: Description of the bug
            error_message: Error message or stack trace
            project_dir: Working directory

        Returns:
            Bug fix result
        """
        prompt = f"""
Fix the following bug.

Bug Description: {bug_description}

Error Message/Stack Trace:
{error_message}

Instructions:
1. Analyze the error message
2. Find the root cause
3. Implement a fix
4. Test that the bug is resolved
5. Ensure no regression

Fix the bug now.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "bug_fixed": True,
                "fix_details": response,
                "status": "fixed",
            }

        except Exception as e:
            self.logger.error("bug_fix_failed", error=str(e))
            return {
                "bug_fixed": False,
                "status": "failed",
                "error": str(e),
            }

    async def fix_issues_list(
        self,
        issues: List[Dict[str, Any]],
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Fix a list of issues.

        Args:
            issues: List of issues with details
            project_dir: Working directory

        Returns:
            Aggregated fix result
        """
        prompt = f"""
Fix the following list of issues.

Issues:
{json.dumps(issues, indent=2)}

For each issue:
1. Identify the root cause
2. Implement a fix
3. Verify the fix
4. Move to the next issue

Fix all issues and report the results.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "all_fixed": True,
                "fix_report": response,
                "status": "fixed",
            }

        except Exception as e:
            self.logger.error("issues_fix_failed", error=str(e))
            return {
                "all_fixed": False,
                "status": "failed",
                "error": str(e),
            }

    async def debug_and_fix(
        self,
        symptom: str,
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Debug an issue and fix it.

        Args:
            symptom: Observable symptom of the issue
            project_dir: Working directory

        Returns:
            Debug and fix result
        """
        prompt = f"""
Debug and fix the following issue.

Symptom: {symptom}

Instructions:
1. Reproduce the issue if possible
2. Add logging or debugging to identify the cause
3. Narrow down the root cause
4. Implement a fix
5. Verify the fix resolves the issue
6. Remove any debug code
7. Commit the fix

Begin debugging.
"""

        try:
            response = await self.run_session(prompt, project_dir)

            return {
                "debugged": True,
                "fixed": True,
                "debug_report": response,
                "status": "fixed",
            }

        except Exception as e:
            self.logger.error("debug_fix_failed", error=str(e))
            return {
                "debugged": False,
                "fixed": False,
                "status": "failed",
                "error": str(e),
            }
