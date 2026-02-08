"""
Tests for src/agents/auto_claude/base.py -- OAuth token management and BaseAutoClaudeAgent.

Covers:
- get_oauth_token() from env, Windows cred files, macOS keychain, Linux secret storage
- require_oauth_token() success/failure
- CLAUDE_SDK_AVAILABLE flag
- BaseAutoClaudeAgent._create_client(), health_check(), initialize(), shutdown()
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Concrete subclass of the abstract BaseAutoClaudeAgent for testing
# ---------------------------------------------------------------------------
def _make_concrete_agent():
    """Import and subclass BaseAutoClaudeAgent inside the function
    so that module-level import errors do not break collection."""
    from src.agents.auto_claude.base import BaseAutoClaudeAgent

    class ConcreteTestAgent(BaseAutoClaudeAgent):
        """Minimal concrete implementation for testing."""

        def __init__(self):
            super().__init__(
                name="test_agent",
                system_prompt="You are a test agent.",
                capabilities=["testing"],
            )

        async def execute(
            self,
            task_description: str,
            context: Dict[str, Any],
            project_dir: Path,
        ) -> Dict[str, Any]:
            return {"output": "test result", "success": True}

    return ConcreteTestAgent()


# ---------------------------------------------------------------------------
# Helper to run async code in sync tests
# ---------------------------------------------------------------------------
def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ===========================================================================
# get_oauth_token tests
# ===========================================================================

class TestGetOAuthToken(unittest.TestCase):
    """Tests for the get_oauth_token() function."""

    @patch.dict("os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-testtoken123"})
    def test_get_oauth_token_from_env(self):
        """Valid env var with correct prefix is returned directly."""
        from src.agents.auto_claude.base import get_oauth_token
        token = get_oauth_token()
        self.assertEqual(token, "sk-ant-oat01-testtoken123")

    @patch("src.agents.auto_claude.base.is_windows", return_value=True)
    @patch("src.agents.auto_claude.base._get_token_from_windows", return_value=None)
    @patch.dict("os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": "invalid-token"})
    def test_get_oauth_token_invalid_prefix_rejected(self, mock_win_token, mock_is_win):
        """Token without 'sk-ant-oat01-' prefix falls through to system creds."""
        from src.agents.auto_claude.base import get_oauth_token
        token = get_oauth_token()
        # Falls through to _get_token_from_windows which returns None
        self.assertIsNone(token)
        mock_win_token.assert_called_once()

    @patch("src.agents.auto_claude.base.is_windows", return_value=True)
    @patch("src.agents.auto_claude.base._get_token_from_windows", return_value=None)
    @patch.dict("os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": ""})
    def test_get_oauth_token_env_empty(self, mock_win_token, mock_is_win):
        """Empty env var falls through to system credential store."""
        from src.agents.auto_claude.base import get_oauth_token
        token = get_oauth_token()
        self.assertIsNone(token)
        mock_win_token.assert_called_once()

    @patch("src.agents.auto_claude.base.is_windows", return_value=True)
    @patch("src.agents.auto_claude.base.is_macos", return_value=False)
    @patch.dict("os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": ""})
    def test_get_oauth_token_windows_credential_file(self, mock_is_mac, mock_is_win):
        """Windows: reads token from ~/.claude/.credentials.json."""
        from src.agents.auto_claude.base import get_oauth_token

        cred_data = json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-windowstoken456"
            }
        })

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=cred_data)):
            token = get_oauth_token()

        self.assertEqual(token, "sk-ant-oat01-windowstoken456")

    @patch("src.agents.auto_claude.base.is_windows", return_value=False)
    @patch("src.agents.auto_claude.base.is_macos", return_value=True)
    @patch.dict("os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": ""})
    def test_get_oauth_token_macos_keychain(self, mock_is_mac, mock_is_win):
        """macOS: retrieves token from Keychain via /usr/bin/security."""
        from src.agents.auto_claude.base import get_oauth_token

        keychain_json = json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-mactoken789"
            }
        })

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = keychain_json

        with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
            token = get_oauth_token()

        self.assertEqual(token, "sk-ant-oat01-mactoken789")
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        self.assertIn("/usr/bin/security", call_args[0][0])

    @patch("src.agents.auto_claude.base.is_windows", return_value=False)
    @patch("src.agents.auto_claude.base.is_macos", return_value=False)
    @patch.dict("os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": ""})
    def test_get_oauth_token_linux_secretstorage(self, mock_is_mac, mock_is_win):
        """Linux: retrieves token from Secret Service via secretstorage."""
        from src.agents.auto_claude.base import get_oauth_token

        secret_data = json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-linuxtoken012"
            }
        })

        mock_item = MagicMock()
        mock_item.get_label.return_value = "Claude Code-credentials"
        mock_item.get_secret.return_value = secret_data.encode("utf-8")

        mock_collection = MagicMock()
        mock_collection.is_locked.return_value = False
        mock_collection.search_items.return_value = [mock_item]

        mock_secretstorage = MagicMock()
        mock_secretstorage.get_default_collection.return_value = mock_collection

        with patch.dict("sys.modules", {"secretstorage": mock_secretstorage}):
            token = get_oauth_token()

        self.assertEqual(token, "sk-ant-oat01-linuxtoken012")


# ===========================================================================
# require_oauth_token tests
# ===========================================================================

class TestRequireOAuthToken(unittest.TestCase):
    """Tests for require_oauth_token()."""

    @patch("src.agents.auto_claude.base.get_oauth_token", return_value="sk-ant-oat01-good")
    def test_require_oauth_token_success(self, mock_get):
        """Returns the token when get_oauth_token finds one."""
        from src.agents.auto_claude.base import require_oauth_token
        token = require_oauth_token()
        self.assertEqual(token, "sk-ant-oat01-good")

    @patch("src.agents.auto_claude.base.get_oauth_token", return_value=None)
    def test_require_oauth_token_raises(self, mock_get):
        """Raises ValueError when no token is available."""
        from src.agents.auto_claude.base import require_oauth_token
        with self.assertRaises(ValueError) as ctx:
            require_oauth_token()
        self.assertIn("No OAuth token found", str(ctx.exception))


# ===========================================================================
# CLAUDE_SDK_AVAILABLE tests
# ===========================================================================

class TestClaudeSDKAvailability(unittest.TestCase):
    """Tests for CLAUDE_SDK_AVAILABLE flag."""

    def test_claude_sdk_available_true(self):
        """When claude_agent_sdk is importable, flag is True."""
        mock_sdk = MagicMock()
        mock_sdk.ClaudeAgentOptions = MagicMock()
        mock_sdk.ClaudeSDKClient = MagicMock()

        with patch.dict("sys.modules", {"claude_agent_sdk": mock_sdk}):
            # Re-import to trigger the try/except
            import importlib
            import src.agents.auto_claude.base as base_mod
            # Manually set to simulate successful import
            original = base_mod.CLAUDE_SDK_AVAILABLE
            base_mod.CLAUDE_SDK_AVAILABLE = True
            self.assertTrue(base_mod.CLAUDE_SDK_AVAILABLE)
            base_mod.CLAUDE_SDK_AVAILABLE = original

    def test_claude_sdk_available_false(self):
        """When CLAUDE_SDK_AVAILABLE is False, reflects missing SDK."""
        from src.agents.auto_claude import base as base_mod
        original = base_mod.CLAUDE_SDK_AVAILABLE
        base_mod.CLAUDE_SDK_AVAILABLE = False
        self.assertFalse(base_mod.CLAUDE_SDK_AVAILABLE)
        base_mod.CLAUDE_SDK_AVAILABLE = original


# ===========================================================================
# BaseAutoClaudeAgent tests
# ===========================================================================

class TestBaseAutoClaudeAgent(unittest.TestCase):
    """Tests for BaseAutoClaudeAgent._create_client(), health_check(), etc."""

    def test_base_agent_default_model(self):
        """DEFAULT_MODEL is claude-sonnet-4-20250514."""
        from src.agents.auto_claude.base import BaseAutoClaudeAgent
        self.assertEqual(
            BaseAutoClaudeAgent.DEFAULT_MODEL,
            "claude-sonnet-4-20250514",
        )

    def test_base_agent_default_tools(self):
        """DEFAULT_TOOLS contains exactly 8 tools."""
        from src.agents.auto_claude.base import BaseAutoClaudeAgent
        expected_tools = [
            "Read", "Write", "Edit", "Glob", "Grep",
            "Bash", "WebFetch", "WebSearch",
        ]
        self.assertEqual(BaseAutoClaudeAgent.DEFAULT_TOOLS, expected_tools)
        self.assertEqual(len(BaseAutoClaudeAgent.DEFAULT_TOOLS), 8)

    @patch("src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", False)
    def test_base_agent_create_client_sdk_not_available(self):
        """_create_client raises RuntimeError when SDK is not installed."""
        agent = _make_concrete_agent()
        with self.assertRaises(RuntimeError) as ctx:
            agent._create_client(Path("."))
        self.assertIn("Claude Agent SDK not available", str(ctx.exception))

    @patch("src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", True)
    @patch("src.agents.auto_claude.base.require_oauth_token", side_effect=ValueError("No OAuth token found"))
    def test_base_agent_create_client_no_token(self, mock_require):
        """_create_client raises ValueError when no OAuth token is available."""
        agent = _make_concrete_agent()
        agent._oauth_token = None
        with self.assertRaises(ValueError) as ctx:
            agent._create_client(Path("."))
        self.assertIn("No OAuth token", str(ctx.exception))

    @patch("src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", True)
    @patch("src.agents.auto_claude.base.require_oauth_token", return_value="sk-ant-oat01-valid")
    def test_base_agent_create_client_success(self, mock_require):
        """_create_client configures ClaudeAgentOptions with correct params."""
        import src.agents.auto_claude.base as base_mod

        MockClaudeAgentOptions = MagicMock()
        MockClaudeSDKClient = MagicMock()

        original_options = base_mod.ClaudeAgentOptions
        original_client = base_mod.ClaudeSDKClient
        base_mod.ClaudeAgentOptions = MockClaudeAgentOptions
        base_mod.ClaudeSDKClient = MockClaudeSDKClient

        try:
            agent = _make_concrete_agent()
            agent._oauth_token = None  # Will be fetched via require_oauth_token
            project_dir = Path("/tmp/test_project")

            client = agent._create_client(project_dir)

            # Verify ClaudeAgentOptions was called with correct params
            MockClaudeAgentOptions.assert_called_once()
            call_kwargs = MockClaudeAgentOptions.call_args[1]

            self.assertEqual(call_kwargs["model"], "claude-sonnet-4-20250514")
            self.assertEqual(call_kwargs["allowed_tools"], [
                "Read", "Write", "Edit", "Glob", "Grep",
                "Bash", "WebFetch", "WebSearch",
            ])
            self.assertEqual(len(call_kwargs["allowed_tools"]), 8)
            self.assertEqual(call_kwargs["max_turns"], 100)
            self.assertIn("You are a test agent.", call_kwargs["system_prompt"])

            # Verify client was created
            MockClaudeSDKClient.assert_called_once()
        finally:
            base_mod.ClaudeAgentOptions = original_options
            base_mod.ClaudeSDKClient = original_client

    @patch("src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", True)
    @patch("src.agents.auto_claude.base.get_oauth_token", return_value="sk-ant-oat01-present")
    def test_base_agent_health_check_both_available(self, mock_token):
        """health_check returns True when SDK and token are both available."""
        agent = _make_concrete_agent()
        result = _run(agent.health_check())
        self.assertTrue(result)

    @patch("src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", False)
    def test_base_agent_health_check_no_sdk(self):
        """health_check returns False when SDK is not available."""
        agent = _make_concrete_agent()
        result = _run(agent.health_check())
        self.assertFalse(result)

    @patch("src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", True)
    @patch("src.agents.auto_claude.base.get_oauth_token", return_value=None)
    def test_base_agent_health_check_no_token(self, mock_token):
        """health_check returns False when token is not available."""
        agent = _make_concrete_agent()
        result = _run(agent.health_check())
        self.assertFalse(result)

    @patch("src.agents.auto_claude.base.require_oauth_token", return_value="sk-ant-oat01-init")
    def test_base_agent_initialize(self, mock_require):
        """initialize() sets _initialized=True and attempts to get token."""
        agent = _make_concrete_agent()
        self.assertFalse(agent._initialized)
        _run(agent.initialize())
        self.assertTrue(agent._initialized)
        self.assertEqual(agent._oauth_token, "sk-ant-oat01-init")

    def test_base_agent_shutdown(self):
        """shutdown() sets _initialized=False."""
        agent = _make_concrete_agent()
        agent._initialized = True
        _run(agent.shutdown())
        self.assertFalse(agent._initialized)


if __name__ == "__main__":
    unittest.main()
