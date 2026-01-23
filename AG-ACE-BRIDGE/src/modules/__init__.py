"""
AG-ACE-BRIDGE Modules

External modules integrated via git submodule:
- Auto-Claude: 24/7 autonomous coding framework (AndyMik90/Auto-Claude)
"""

import sys
from pathlib import Path

# Add Auto-Claude backend to Python path
AUTO_CLAUDE_PATH = Path(__file__).parent.parent.parent / "modules" / "Auto-Claude" / "apps" / "backend"

if AUTO_CLAUDE_PATH.exists():
    sys.path.insert(0, str(AUTO_CLAUDE_PATH))
    AUTO_CLAUDE_AVAILABLE = True
else:
    AUTO_CLAUDE_AVAILABLE = False

__all__ = ["AUTO_CLAUDE_AVAILABLE", "AUTO_CLAUDE_PATH"]
