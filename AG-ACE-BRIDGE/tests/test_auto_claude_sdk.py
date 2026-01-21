"""
Test Auto-Claude SDK Integration

Verifies:
1. Claude Agent SDK can be imported
2. OAuth token is accessible from system credentials
3. AutoClaudeAdapter can be initialized
"""

import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_sdk_import():
    """Test that Claude Agent SDK can be imported"""
    print("=" * 60)
    print("Test 1: Claude Agent SDK Import")
    print("=" * 60)

    try:
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
        print("✓ claude_agent_sdk imported successfully")
        print(f"  - ClaudeAgentOptions: {ClaudeAgentOptions}")
        print(f"  - ClaudeSDKClient: {ClaudeSDKClient}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import claude_agent_sdk: {e}")
        print("  Install with: pip install claude-agent-sdk")
        return False


def test_oauth_token():
    """Test that OAuth token is accessible"""
    print("\n" + "=" * 60)
    print("Test 2: OAuth Token Access")
    print("=" * 60)

    from src.adapters.auto_claude import get_oauth_token, is_windows

    token = get_oauth_token()

    if token:
        print("✓ OAuth token found")
        print(f"  - Token prefix: {token[:20]}...")
        print(f"  - Token length: {len(token)} characters")
        print(f"  - Format valid: {token.startswith('sk-ant-oat01-')}")
        return True
    else:
        print("✗ No OAuth token found")
        if is_windows():
            print("  Check: %USERPROFILE%\\.claude\\.credentials.json")
        else:
            print("  Run: claude login")
        return False


def test_adapter_initialization():
    """Test that AutoClaudeAdapter can be initialized"""
    print("\n" + "=" * 60)
    print("Test 3: AutoClaudeAdapter Initialization")
    print("=" * 60)

    from src.utils.models import AgentType
    from src.adapters.auto_claude import AutoClaudeAdapter, CLAUDE_SDK_AVAILABLE

    print(f"  - SDK Available: {CLAUDE_SDK_AVAILABLE}")

    try:
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        print(f"✓ Adapter created successfully")
        print(f"  - Agent type: {adapter.agent_type}")
        print(f"  - Role: {adapter.role}")
        print(f"  - Name: {adapter.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to create adapter: {e}")
        return False


async def test_adapter_initialize():
    """Test async initialization of adapter"""
    print("\n" + "=" * 60)
    print("Test 4: Adapter Async Initialize")
    print("=" * 60)

    from src.utils.models import AgentType
    from src.adapters.auto_claude import AutoClaudeAdapter

    try:
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        await adapter.initialize()
        print(f"✓ Adapter initialized successfully")
        print(f"  - OAuth token available: {adapter._oauth_token is not None}")

        # Health check
        healthy = await adapter.health_check()
        print(f"  - Health check: {'✓ Passed' if healthy else '✗ Failed'}")

        await adapter.shutdown()
        print(f"  - Shutdown: Complete")
        return healthy
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("   AG-ACE-BRIDGE: Auto-Claude SDK Integration Tests")
    print("=" * 60)

    results = []

    # Test 1: SDK Import
    results.append(("SDK Import", test_sdk_import()))

    # Test 2: OAuth Token
    results.append(("OAuth Token", test_oauth_token()))

    # Test 3: Adapter Creation
    results.append(("Adapter Creation", test_adapter_initialization()))

    # Test 4: Async Initialize
    results.append(("Async Initialize", asyncio.run(test_adapter_initialize())))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Auto-Claude SDK integration is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
