"""
AG/Auto-Claude Modules

Provides access to Auto-Claude backend utilities (prompts, etc.).
Uses config-based path resolution instead of git submodule.
"""

import sys
from pathlib import Path

from src.utils.config import get_settings

# Resolve Auto-Claude backend path from config
_settings = get_settings()
AUTO_CLAUDE_PATH = Path(_settings.auto_claude_path)

if AUTO_CLAUDE_PATH.exists():
    sys.path.insert(0, str(AUTO_CLAUDE_PATH))
    AUTO_CLAUDE_AVAILABLE = True
else:
    AUTO_CLAUDE_AVAILABLE = False

__all__ = ["AUTO_CLAUDE_AVAILABLE", "AUTO_CLAUDE_PATH"]
