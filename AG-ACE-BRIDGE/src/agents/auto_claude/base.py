"""
Auto-Claude Base Agent

Common functionality for all Auto-Claude agents:
- OAuth token management
- Claude SDK client creation
- Session execution
"""

import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.utils.logger import Loggers

# Claude Agent SDK imports
try:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    ClaudeAgentOptions = None
    ClaudeSDKClient = None


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def get_oauth_token() -> Optional[str]:
    """
    Get OAuth token from system credential store.

    Checks multiple sources in priority order:
    1. CLAUDE_CODE_OAUTH_TOKEN environment variable
    2. System credential files (Windows/macOS/Linux)

    Returns:
        OAuth token string if found, None otherwise
    """
    # Check environment variable first
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if token and token.startswith("sk-ant-oat01-"):
        return token

    # Check system credential files
    if is_windows():
        return _get_token_from_windows()
    elif is_macos():
        return _get_token_from_macos()
    else:
        return _get_token_from_linux()


def _get_token_from_windows() -> Optional[str]:
    """Get OAuth token from Windows credential files."""
    try:
        cred_paths = [
            os.path.expandvars(r"%USERPROFILE%\.claude\.credentials.json"),
            os.path.expandvars(r"%USERPROFILE%\.claude\credentials.json"),
            os.path.expandvars(r"%LOCALAPPDATA%\Claude\credentials.json"),
            os.path.expandvars(r"%APPDATA%\Claude\credentials.json"),
        ]

        for cred_path in cred_paths:
            if os.path.exists(cred_path):
                with open(cred_path, encoding="utf-8") as f:
                    data = json.load(f)
                    token = data.get("claudeAiOauth", {}).get("accessToken")
                    if token and token.startswith("sk-ant-oat01-"):
                        return token
        return None
    except Exception:
        return None


def _get_token_from_macos() -> Optional[str]:
    """Get OAuth token from macOS Keychain."""
    try:
        import subprocess
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                "Claude Code-credentials",
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        credentials_json = result.stdout.strip()
        if not credentials_json:
            return None

        data = json.loads(credentials_json)
        token = data.get("claudeAiOauth", {}).get("accessToken")

        if token and token.startswith("sk-ant-oat01-"):
            return token
        return None
    except Exception:
        return None


def _get_token_from_linux() -> Optional[str]:
    """Get OAuth token from Linux Secret Service."""
    try:
        import secretstorage
        collection = secretstorage.get_default_collection(None)

        if collection.is_locked():
            collection.unlock()

        items = collection.search_items({"application": "claude-code"})

        for item in items:
            label = item.get_label()
            if label == "Claude Code-credentials":
                secret = item.get_secret()
                if isinstance(secret, bytes):
                    secret = secret.decode("utf-8")
                data = json.loads(secret)
                token = data.get("claudeAiOauth", {}).get("accessToken")
                if token and token.startswith("sk-ant-oat01-"):
                    return token
        return None
    except Exception:
        return None


def require_oauth_token() -> str:
    """
    Get OAuth token or raise error.

    Raises:
        ValueError: If no OAuth token found
    """
    token = get_oauth_token()
    if not token:
        raise ValueError(
            "No OAuth token found.\n\n"
            "AG-ACE-BRIDGE requires Claude Code OAuth authentication.\n"
            "To authenticate:\n"
            "  1. Run: claude\n"
            "  2. Type: /login\n"
            "  3. Complete OAuth login in browser\n"
        )
    return token


class BaseAutoClaudeAgent(ABC):
    """
    Base class for Auto-Claude agents.

    Provides common functionality:
    - OAuth token management
    - Claude SDK client creation
    - Session execution

    Subclasses implement specific agent logic.
    """

    # Default model for Claude sessions
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    # Default allowed tools
    DEFAULT_TOOLS = [
        "Read", "Write", "Edit", "Glob", "Grep",
        "Bash", "WebFetch", "WebSearch",
    ]

    def __init__(self, name: str, system_prompt: str, capabilities: List[str]):
        """
        Initialize Auto-Claude agent.

        Args:
            name: Agent name
            system_prompt: System prompt for this agent
            capabilities: List of agent capabilities
        """
        self.name = name
        self.system_prompt = system_prompt
        self.capabilities = capabilities
        self.logger = Loggers.adapter()
        self._oauth_token: Optional[str] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize agent, verify OAuth token."""
        if not CLAUDE_SDK_AVAILABLE:
            self.logger.warning(
                "claude_sdk_not_available",
                agent=self.name,
                message="Install claude-agent-sdk: pip install claude-agent-sdk",
            )

        try:
            self._oauth_token = require_oauth_token()
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = self._oauth_token
            self.logger.info(
                "auto_claude_agent_initialized",
                agent=self.name,
                oauth_available=True,
            )
        except ValueError as e:
            self.logger.warning(
                "auto_claude_oauth_missing",
                agent=self.name,
                error=str(e),
            )

        self._initialized = True

    async def shutdown(self) -> None:
        """Cleanup agent resources."""
        self._initialized = False
        self.logger.info("auto_claude_agent_shutdown", agent=self.name)

    def _create_client(self, project_dir: Path) -> "ClaudeSDKClient":
        """
        Create Claude SDK client.

        Args:
            project_dir: Working directory for the session

        Returns:
            Configured ClaudeSDKClient
        """
        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError(
                "Claude Agent SDK not available. "
                "Install it with: pip install claude-agent-sdk"
            )

        if not self._oauth_token:
            self._oauth_token = require_oauth_token()
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = self._oauth_token

        # Build system prompt with working directory
        full_prompt = self.system_prompt
        full_prompt += f"\n\nWorking directory: {project_dir.resolve()}"

        options = ClaudeAgentOptions(
            model=self.DEFAULT_MODEL,
            system_prompt=full_prompt,
            allowed_tools=self.DEFAULT_TOOLS,
            max_turns=100,
            cwd=str(project_dir.resolve()),
        )

        return ClaudeSDKClient(options=options)

    async def run_session(self, prompt: str, project_dir: Path) -> str:
        """
        Run a Claude SDK session with the given prompt.

        Args:
            prompt: The prompt to send to Claude
            project_dir: Working directory

        Returns:
            Response text from Claude
        """
        client = self._create_client(project_dir)

        async with client:
            await client.query(prompt)

            response_text = ""
            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            response_text += block.text

            return response_text

    async def health_check(self) -> bool:
        """Check if agent is healthy (SDK + OAuth available)."""
        try:
            if not CLAUDE_SDK_AVAILABLE:
                return False
            token = get_oauth_token()
            return token is not None
        except Exception:
            return False

    @abstractmethod
    async def execute(
        self,
        task_description: str,
        context: Dict[str, Any],
        project_dir: Path,
    ) -> Dict[str, Any]:
        """
        Execute agent-specific task.

        Args:
            task_description: Description of the task
            context: Context from previous stages
            project_dir: Working directory

        Returns:
            Execution result dictionary
        """
        pass
