"""
AG-ACE-BRIDGE A2A Agent Integration Test

Tests calculator_agent (8006) and poetry_agent (8003) via A2A Protocol.
"""

import asyncio
import sys
sys.path.insert(0, "D:/Data/25_ACE/AG-ACE-BRIDGE")

from src.adapters.ag_a2a_adapter import (
    AGA2AAdapter,
    A2AAgentType,
    create_calculator_adapter,
    create_poetry_adapter,
)
from src.utils.models import Task, TaskType


async def test_calculator_agent():
    """Test Calculator A2A agent"""
    print("\n" + "="*60)
    print("TEST 1: Calculator Agent (Port 8006)")
    print("="*60)

    adapter = create_calculator_adapter()

    # Initialize
    await adapter.initialize()
    print(f"[OK] Adapter initialized: {adapter.agent_type.value}")

    # Health check
    is_healthy = await adapter.health_check()
    print(f"[{'OK' if is_healthy else 'FAIL'}] Health check: {is_healthy}")

    # Get capabilities
    caps = adapter.get_capabilities()
    print(f"[INFO] Capabilities: {caps}")

    # Execute task
    task = Task(
        id="test-calc-001",
        type=TaskType.RESEARCH,  # Using RESEARCH as generic type
        description="Calculate 25 * 4 + 10",
        input_data={"expression": "25 * 4 + 10"}
    )

    print(f"\n[EXECUTING] Task: {task.description}")
    result = await adapter.execute(task, context={})

    print(f"[RESULT] Status: {result.status}")
    print(f"[RESULT] Agent: {result.agent_used}")
    print(f"[RESULT] Time: {result.execution_time_ms}ms")

    if result.output:
        print(f"[RESULT] Output:")
        if isinstance(result.output, dict):
            text = result.output.get("text", str(result.output))
            print(f"  {text[:500]}...")
        else:
            print(f"  {str(result.output)[:500]}...")

    if result.error:
        print(f"[ERROR] {result.error}")

    await adapter.shutdown()
    # Handle both enum and string status
    status = result.status.value if hasattr(result.status, 'value') else str(result.status)
    return status == "success"


async def test_poetry_agent():
    """Test Poetry A2A agent"""
    print("\n" + "="*60)
    print("TEST 2: Poetry Agent (Port 8003)")
    print("="*60)

    adapter = create_poetry_adapter()

    # Initialize
    await adapter.initialize()
    print(f"[OK] Adapter initialized: {adapter.agent_type.value}")

    # Health check
    is_healthy = await adapter.health_check()
    print(f"[{'OK' if is_healthy else 'FAIL'}] Health check: {is_healthy}")

    # Get capabilities
    caps = adapter.get_capabilities()
    print(f"[INFO] Capabilities: {caps}")

    # Execute task
    task = Task(
        id="test-poetry-001",
        type=TaskType.RESEARCH,
        description="Write a short haiku about coding at night",
        input_data={"topic": "coding at night", "style": "haiku"}
    )

    print(f"\n[EXECUTING] Task: {task.description}")
    result = await adapter.execute(task, context={})

    print(f"[RESULT] Status: {result.status}")
    print(f"[RESULT] Agent: {result.agent_used}")
    print(f"[RESULT] Time: {result.execution_time_ms}ms")

    if result.output:
        print(f"[RESULT] Output:")
        if isinstance(result.output, dict):
            text = result.output.get("text", str(result.output))
            print(f"  {text[:500]}...")
        else:
            print(f"  {str(result.output)[:500]}...")

    if result.error:
        print(f"[ERROR] {result.error}")

    await adapter.shutdown()
    # Handle both enum and string status
    status = result.status.value if hasattr(result.status, 'value') else str(result.status)
    return status == "success"


async def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("#  AG-ACE-BRIDGE A2A Agent Integration Test")
    print("#"*60)

    results = {}

    # Test Calculator
    try:
        results["calculator"] = await test_calculator_agent()
    except Exception as e:
        print(f"[EXCEPTION] Calculator test failed: {e}")
        results["calculator"] = False

    # Test Poetry
    try:
        results["poetry"] = await test_poetry_agent()
    except Exception as e:
        print(f"[EXCEPTION] Poetry test failed: {e}")
        results["poetry"] = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for agent, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {agent}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
