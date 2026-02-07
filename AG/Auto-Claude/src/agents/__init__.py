"""
AG/Auto-Claude Agents Module

All agent implementations are managed here.
Adapters in src/adapters/ wrap these agents for orchestrator use.
"""

from src.agents.auto_claude import (
    AutoClaudePlanner,
    AutoClaudeCoder,
    AutoClaudeQAReviewer,
    AutoClaudeQAFixer,
    get_oauth_token,
    require_oauth_token,
    CLAUDE_SDK_AVAILABLE,
)

__all__ = [
    # Auto-Claude Agents
    "AutoClaudePlanner",
    "AutoClaudeCoder",
    "AutoClaudeQAReviewer",
    "AutoClaudeQAFixer",
    # OAuth utilities
    "get_oauth_token",
    "require_oauth_token",
    "CLAUDE_SDK_AVAILABLE",
]
