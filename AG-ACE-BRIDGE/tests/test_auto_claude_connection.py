"""
Auto-Claude Connection Test

Quick test to verify Claude SDK connection works with OAuth token.
Run: python tests/test_auto_claude_connection.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters.auto_claude import (
    get_oauth_token,
    require_oauth_token,
    CLAUDE_SDK_AVAILABLE,
    AutoClaudeAdapter,
)
from src.utils.models import AgentType, Task, TaskType, Priority


def test_sdk_available():
    """Test 1: SDK import"""
    print("\n[Test 1] Claude Agent SDK Import")
    print(f"  SDK Available: {CLAUDE_SDK_AVAILABLE}")

    if CLAUDE_SDK_AVAILABLE:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        print(f"  ClaudeSDKClient: {ClaudeSDKClient}")
        print(f"  ClaudeAgentOptions: {ClaudeAgentOptions}")
        print("  Result: PASS")
        return True
    else:
        print("  Result: FAIL")
        return False


def test_oauth_token():
    """Test 2: OAuth token availability"""
    print("\n[Test 2] OAuth Token")

    token = get_oauth_token()
    if token:
        print(f"  Token Found: {token[:25]}...")
        print(f"  Token Format: {'VALID' if token.startswith('sk-ant-oat01-') else 'INVALID'}")
        print("  Result: PASS [OK]")
        return True
    else:
        print("  Token: NOT FOUND")
        print("  Result: FAIL [FAIL]")
        print("\n  To fix: Run 'claude' command and type '/login'")
        return False


async def test_adapter_initialize():
    """Test 3: Adapter initialization"""
    print("\n[Test 3] AutoClaudeAdapter Initialize")

    try:
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        await adapter.initialize()

        print(f"  Agent Type: {adapter.agent_type.value}")
        print(f"  Role: {adapter.role}")
        print(f"  OAuth Token: {'Available' if adapter._oauth_token else 'Missing'}")
        print("  Result: PASS [OK]")
        return True

    except Exception as e:
        print(f"  Error: {e}")
        print("  Result: FAIL [FAIL]")
        return False


async def test_health_check():
    """Test 4: Health check"""
    print("\n[Test 4] Health Check")

    try:
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        await adapter.initialize()

        healthy = await adapter.health_check()
        print(f"  Healthy: {healthy}")
        print(f"  Result: {'PASS [OK]' if healthy else 'FAIL [FAIL]'}")
        return healthy

    except Exception as e:
        print(f"  Error: {e}")
        print("  Result: FAIL [FAIL]")
        return False


async def test_simple_query():
    """Test 5: Simple SDK query (optional, requires actual API call)"""
    print("\n[Test 5] Simple Query (Quick Test)")

    if not CLAUDE_SDK_AVAILABLE:
        print("  Skipped: SDK not available")
        return None

    token = get_oauth_token()
    if not token:
        print("  Skipped: No OAuth token")
        return None

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        options = ClaudeAgentOptions(
            model="claude-sonnet-4-20250514",
            system_prompt="You are a helpful assistant. Respond briefly.",
            max_turns=1,
        )

        client = ClaudeSDKClient(options=options)

        print("  Connecting to Claude...")
        async with client:
            await client.query("Say 'Hello from AG-ACE-BRIDGE!' and nothing else.")

            response = ""
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            response += block.text

            print(f"  Response: {response[:100]}...")
            print("  Result: PASS [OK]")
            return True

    except Exception as e:
        print(f"  Error: {e}")
        print("  Result: FAIL [FAIL]")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Auto-Claude Connection Test Suite")
    print("=" * 60)

    results = {
        "SDK Import": test_sdk_available(),
        "OAuth Token": test_oauth_token(),
        "Adapter Init": await test_adapter_initialize(),
        "Health Check": await test_health_check(),
    }

    # Ask before running actual query (costs money/tokens)
    print("\n" + "=" * 60)
    try:
        run_query = input("Run actual API query test? (y/N): ").strip().lower()
    except EOFError:
        run_query = 'n'  # Non-interactive mode

    if run_query == 'y':
        results["Simple Query"] = await test_simple_query()
    else:
        print("\n[Test 5] Simple Query - Skipped")
        results["Simple Query"] = None

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for name, result in results.items():
        status = "PASS [OK]" if result is True else "FAIL [FAIL]" if result is False else "SKIP -"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    # 24/7 Readiness
    print("\n" + "=" * 60)
    print("24/7 Readiness Check")
    print("=" * 60)

    ready = results["SDK Import"] and results["OAuth Token"] and results["Adapter Init"]

    if ready:
        print("  Status: READY [OK]")
        print("  Auto-Claude 24/7 operation is possible!")
    else:
        print("  Status: NOT READY [FAIL]")
        if not results["SDK Import"]:
            print("  - Install SDK: pip install claude-agent-sdk")
        if not results["OAuth Token"]:
            print("  - Login: Run 'claude' and type '/login'")

    return 0 if ready else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
