"""
Auto-Claude Agents for AG-ACE-BRIDGE

24/7 autonomous coding agents using Claude Agent SDK with OAuth authentication.

Agents:
- AutoClaudePlanner: Project planning, task decomposition
- AutoClaudeCoder: Code implementation
- AutoClaudeQAReviewer: Code review, testing
- AutoClaudeQAFixer: Issue resolution, debugging
"""

from src.agents.auto_claude.base import (
    get_oauth_token,
    require_oauth_token,
    CLAUDE_SDK_AVAILABLE,
    BaseAutoClaudeAgent,
)
from src.agents.auto_claude.planner import AutoClaudePlanner
from src.agents.auto_claude.coder import AutoClaudeCoder
from src.agents.auto_claude.qa_reviewer import AutoClaudeQAReviewer
from src.agents.auto_claude.qa_fixer import AutoClaudeQAFixer

__all__ = [
    # Base utilities
    "get_oauth_token",
    "require_oauth_token",
    "CLAUDE_SDK_AVAILABLE",
    "BaseAutoClaudeAgent",
    # Agent classes
    "AutoClaudePlanner",
    "AutoClaudeCoder",
    "AutoClaudeQAReviewer",
    "AutoClaudeQAFixer",
]
