"""
Error Type Classification
=========================
Classify errors from experiment runs into categories.
"""

import re
from enum import Enum


class ErrorType(str, Enum):
    TOOL_CALL = "tool_call"             # Tool call parsing/execution failure
    HANDOFF = "handoff"                 # Handoff loop or invalid target
    TIMEOUT = "timeout"                 # Execution timeout
    KEYWORD_MISS = "keyword_miss"       # Termination keyword not produced
    MODEL_ERROR = "model_error"         # LLM API/SDK error
    CONTEXT_OVERFLOW = "context_overflow"  # Context window exceeded
    SELECTOR_FAIL = "selector_fail"     # Selector couldn't pick a valid agent
    UNKNOWN = "unknown"


def classify_error(error_str: str | None, stop_reason: str | None,
                   terminated_by: str | None) -> ErrorType | None:
    """Classify an error into ErrorType categories.

    Returns None if no error occurred.
    """
    if not error_str and terminated_by != "max_messages":
        return None

    # Max messages with no keyword = keyword miss
    if terminated_by == "max_messages" and not error_str:
        return ErrorType.KEYWORD_MISS

    if not error_str:
        return None

    error_lower = error_str.lower()

    if "timeout" in error_lower or "timed out" in error_lower:
        return ErrorType.TIMEOUT

    if "context" in error_lower and ("overflow" in error_lower or "length" in error_lower or "too long" in error_lower):
        return ErrorType.CONTEXT_OVERFLOW

    if "handoff" in error_lower or "transfer" in error_lower:
        return ErrorType.HANDOFF

    if "tool" in error_lower or "function_call" in error_lower:
        return ErrorType.TOOL_CALL

    if "selector" in error_lower or "max_selector_attempts" in error_lower:
        return ErrorType.SELECTOR_FAIL

    if any(kw in error_lower for kw in ["api", "sdk", "claude", "model", "rate_limit", "connection"]):
        return ErrorType.MODEL_ERROR

    return ErrorType.UNKNOWN


def classify_run(run_dict: dict) -> dict:
    """Classify a single run result dict and return error info."""
    error_type = classify_error(
        error_str=run_dict.get("error"),
        stop_reason=run_dict.get("stop_reason"),
        terminated_by=run_dict.get("terminated_by"),
    )

    return {
        "pattern": run_dict.get("pattern"),
        "pattern_category": run_dict.get("pattern_category"),
        "task_id": run_dict.get("task_id"),
        "agent_count": run_dict.get("agent_count"),
        "has_error": error_type is not None,
        "error_type": error_type.value if error_type else None,
        "error_text": run_dict.get("error", "")[:200] if run_dict.get("error") else "",
    }
