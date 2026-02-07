"""
Auto-Claude Prompts Wrapper

Provides access to Auto-Claude's system prompts.
Uses config-based path resolution.
"""

from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache

from src.utils.config import get_settings

# Prompts directory path (resolved from config: auto_claude_path / prompts)
PROMPTS_DIR = Path(get_settings().auto_claude_path) / "prompts"


@lru_cache(maxsize=32)
def load_prompt(name: str) -> Optional[str]:
    """
    Load a prompt from Auto-Claude prompts directory.

    Args:
        name: Prompt name (without .md extension)

    Returns:
        Prompt content or None if not found
    """
    prompt_file = PROMPTS_DIR / f"{name}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return None


def get_planner_prompt() -> str:
    """Get the planner agent system prompt."""
    return load_prompt("planner") or ""


def get_coder_prompt() -> str:
    """Get the coder agent system prompt."""
    return load_prompt("coder") or ""


def get_qa_reviewer_prompt() -> str:
    """Get the QA reviewer agent system prompt."""
    return load_prompt("qa_reviewer") or ""


def get_qa_fixer_prompt() -> str:
    """Get the QA fixer agent system prompt."""
    return load_prompt("qa_fixer") or ""


def get_spec_gatherer_prompt() -> str:
    """Get the spec gatherer agent system prompt."""
    return load_prompt("spec_gatherer") or ""


def get_spec_writer_prompt() -> str:
    """Get the spec writer agent system prompt."""
    return load_prompt("spec_writer") or ""


def get_spec_critic_prompt() -> str:
    """Get the spec critic agent system prompt."""
    return load_prompt("spec_critic") or ""


def list_available_prompts() -> Dict[str, bool]:
    """
    List all available prompts and their availability.

    Returns:
        Dict mapping prompt name to availability status
    """
    prompts = {}
    if PROMPTS_DIR.exists():
        for prompt_file in PROMPTS_DIR.glob("*.md"):
            prompts[prompt_file.stem] = True
    return prompts


__all__ = [
    "load_prompt",
    "get_planner_prompt",
    "get_coder_prompt",
    "get_qa_reviewer_prompt",
    "get_qa_fixer_prompt",
    "get_spec_gatherer_prompt",
    "get_spec_writer_prompt",
    "get_spec_critic_prompt",
    "list_available_prompts",
    "PROMPTS_DIR",
]
