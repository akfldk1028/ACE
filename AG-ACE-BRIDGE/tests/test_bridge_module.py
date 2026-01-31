"""
Bridge Module Test
==================

AutoGen -> Auto-Claude Bridge Module Test.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add module path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bridge import AutogenToSpec, AutoClaudeRunner, WorkflowExecutor


def test_autogen_to_spec():
    """AutogenToSpec Test."""
    print("\n" + "=" * 60)
    print("TEST: AutogenToSpec")
    print("=" * 60)

    converter = AutogenToSpec()

    # Test 1: Basic conversion
    print("\n[1] Basic conversion test...")
    spec_path = converter.convert(
        task_description="Test Calculator App",
        workflow_name="test_calculator",
        goals=["Basic Operations", "Write Tests"]
    )

    assert spec_path.exists(), f"Spec folder not created: {spec_path}"
    assert (spec_path / "spec.md").exists(), "spec.md missing"
    assert (spec_path / "requirements.json").exists(), "requirements.json missing"
    assert (spec_path / "context.json").exists(), "context.json missing"
    assert (spec_path / "implementation_plan.json").exists(), "implementation_plan.json missing"

    print(f"   [OK] Spec created: {spec_path}")

    # Test 2: AutoGen workflow conversion
    print("\n[2] AutoGen workflow conversion test...")
    autogen_workflow = {
        "name": "test_workflow",
        "nodes": [
            {"id": "node_1", "agent": "planner", "task": "Create plan"},
            {"id": "node_2", "agent": "coder", "task": "Implementation"},
            {"id": "node_3", "agent": "qa_reviewer", "task": "Review"}
        ]
    }

    spec_path2 = converter.convert(
        task_description="AutoGen Workflow Test",
        workflow_name="autogen_test",
        autogen_workflow=autogen_workflow
    )

    plan_path = spec_path2 / "implementation_plan.json"
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    assert len(plan["phases"]) == 3, f"Phase count mismatch: {len(plan['phases'])} != 3"
    assert (spec_path2 / "autogen_workflow.json").exists(), "autogen_workflow.json missing"

    print(f"   [OK] AutoGen workflow converted: {spec_path2}")

    # Test 3: Korean name handling
    print("\n[3] Name sanitization test...")
    spec_path3 = converter.convert(
        task_description="Calculator App"
        # workflow_name auto-generated
    )

    folder_name = spec_path3.name
    assert "-" in folder_name, f"Folder name format error: {folder_name}"

    print(f"   [OK] Name sanitized: {folder_name}")

    print("\n[PASS] AutogenToSpec all tests passed!")
    return True


def test_auto_claude_runner():
    """AutoClaudeRunner Test."""
    print("\n" + "=" * 60)
    print("TEST: AutoClaudeRunner")
    print("=" * 60)

    runner = AutoClaudeRunner()

    # Test 1: Python path check
    print("\n[1] Python path check...")
    print(f"   Python: {runner.python_path}")
    assert Path(runner.python_path).exists() or "python" in runner.python_path.lower()
    print(f"   [OK] Python path valid")

    # Test 2: Spec list query
    print("\n[2] Spec list query...")
    specs = runner.get_specs()
    print(f"   Found Specs: {len(specs)}")
    for spec in specs[:5]:  # Show max 5
        print(f"     - {spec['number']}: {spec['name']}")
    print(f"   [OK] Spec list query success")

    # Test 3: Spec status check
    if specs:
        print("\n[3] Spec status check...")
        status = runner.check_spec_status(specs[0]["number"])
        print(f"   Spec: {status.get('spec', {}).get('folder', 'N/A')}")
        print(f"   Status: {status.get('status', 'N/A')}")
        print(f"   Progress: {status.get('progress', {})}")
        print(f"   [OK] Spec status check success")
    else:
        print("\n[3] Spec status check... (SKIP - No Specs)")

    print("\n[PASS] AutoClaudeRunner all tests passed!")
    return True


def test_workflow_executor():
    """WorkflowExecutor Test."""
    print("\n" + "=" * 60)
    print("TEST: WorkflowExecutor")
    print("=" * 60)

    executor = WorkflowExecutor()

    # Test 1: Initialization check
    print("\n[1] Initialization check...")
    assert executor.converter is not None
    assert executor.runner is not None
    print(f"   [OK] Converter: {type(executor.converter).__name__}")
    print(f"   [OK] Runner: {type(executor.runner).__name__}")

    # Test 2: Spec list query
    print("\n[2] Spec list query (via Executor)...")
    specs = executor.list_specs()
    print(f"   Found Specs: {len(specs)}")
    print(f"   [OK] Spec list query success")

    # Test 3: Execution history check
    print("\n[3] Execution history check...")
    history = executor.get_execution_history()
    print(f"   Existing history: {len(history)}")
    print(f"   [OK] Execution history query success")

    print("\n[PASS] WorkflowExecutor all tests passed!")
    return True


def test_end_to_end_dry_run():
    """E2E Dry Run Test (without actual Auto-Claude execution)."""
    print("\n" + "=" * 60)
    print("TEST: E2E Dry Run")
    print("=" * 60)

    executor = WorkflowExecutor()

    # Test: Spec creation only (no actual execution)
    print("\n[1] Spec creation test...")

    # Use converter directly
    spec_path = executor.converter.convert(
        task_description="E2E Test - Simple CLI Tool",
        workflow_name="e2e_test_cli",
        goals=[
            "Create main entry point",
            "Output help message",
            "Write tests"
        ]
    )

    print(f"   Spec path: {spec_path}")

    # File check
    files = list(spec_path.iterdir())
    print(f"   Created files: {len(files)}")
    for f in files:
        print(f"     - {f.name}")

    # Check implementation_plan.json
    plan_path = spec_path / "implementation_plan.json"
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    print(f"\n   Implementation Plan:")
    print(f"     Feature: {plan.get('feature')}")
    print(f"     Phases: {len(plan.get('phases', []))}")

    # Status check
    spec_id = spec_path.name.split("-", 1)[0]
    status = executor.get_status(spec_id)
    print(f"\n   Status: {status.get('status', 'N/A')}")

    print("\n[PASS] E2E Dry Run test passed!")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AG-ACE-BRIDGE: Bridge Module Tests")
    print("=" * 60)

    results = {}

    try:
        results["AutogenToSpec"] = test_autogen_to_spec()
    except Exception as e:
        print(f"\n[FAIL] AutogenToSpec test failed: {e}")
        results["AutogenToSpec"] = False

    try:
        results["AutoClaudeRunner"] = test_auto_claude_runner()
    except Exception as e:
        print(f"\n[FAIL] AutoClaudeRunner test failed: {e}")
        results["AutoClaudeRunner"] = False

    try:
        results["WorkflowExecutor"] = test_workflow_executor()
    except Exception as e:
        print(f"\n[FAIL] WorkflowExecutor test failed: {e}")
        results["WorkflowExecutor"] = False

    try:
        results["E2E Dry Run"] = test_end_to_end_dry_run()
    except Exception as e:
        print(f"\n[FAIL] E2E Dry Run test failed: {e}")
        results["E2E Dry Run"] = False

    # Result summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\nTotal {passed}/{total} tests passed")

    if passed == total:
        print("\n*** All tests passed! ***")
        return 0
    else:
        print("\n!!! Some tests failed !!!")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
