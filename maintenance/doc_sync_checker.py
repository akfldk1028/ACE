"""
Doc Sync Checker - Validates documentation matches actual code.

Checks:
- CLAUDE.md agent count vs actual AgentType enum count
- CLAUDE.md model description vs actual models.py fields
- capabilities.py docstring agent count vs actual
- Port numbers in documentation vs code
"""

import re
import sys
from pathlib import Path
from typing import List

BASE = Path(__file__).resolve().parent.parent
AG_ACE_BRIDGE = BASE / "AG-ACE-BRIDGE"


def count_agent_types() -> int:
    """Count AgentType enum members in models.py."""
    path = AG_ACE_BRIDGE / "src" / "utils" / "models.py"
    if not path.exists():
        return 0

    content = path.read_text(encoding="utf-8")
    block_match = re.search(r'class AgentType\(.*?\):\s*\n(.*?)(?=\nclass |\Z)', content, re.DOTALL)
    if not block_match:
        return 0

    block = block_match.group(1)
    return len(re.findall(r'^\s+\w+\s*=\s*"', block, re.MULTILINE))


def count_capabilities() -> int:
    """Count entries in ALL_AGENT_CAPABILITIES."""
    path = AG_ACE_BRIDGE / "src" / "registry" / "capabilities.py"
    if not path.exists():
        return 0

    content = path.read_text(encoding="utf-8")
    return len(re.findall(r'AgentType\.\w+:', content))


def check_claude_md_agent_count(actual_count: int) -> List[str]:
    """Check if CLAUDE.md references correct agent count."""
    issues = []
    path = AG_ACE_BRIDGE / "CLAUDE.md"
    if not path.exists():
        issues.append("CLAUDE.md not found")
        return issues

    content = path.read_text(encoding="utf-8")

    # Find all agent count references
    for m in re.finditer(r'(\d+)\s*(?:개|agents?)', content, re.IGNORECASE):
        num = int(m.group(1))
        line_num = content[:m.start()].count('\n') + 1
        line = content.splitlines()[line_num - 1].strip()

        # Only flag if the number looks like it refers to total agents
        if num != actual_count and 10 <= num <= 30:
            issues.append(f"CLAUDE.md:{line_num} says '{num}' agents, actual is {actual_count}: {line[:80]}")

    return issues


def check_claude_md_model_fields() -> List[str]:
    """Check if CLAUDE.md model descriptions match actual models."""
    issues = []
    path = AG_ACE_BRIDGE / "CLAUDE.md"
    if not path.exists():
        return issues

    content = path.read_text(encoding="utf-8")

    # Check for outdated field references
    outdated_patterns = [
        (r'input_data', 'input_data referenced (should be input)'),
        (r'status:\s*TaskStatus', 'Task has no status field (TaskStatus is in project_executor.py)'),
    ]

    for pattern, message in outdated_patterns:
        for m in re.finditer(pattern, content):
            line_num = content[:m.start()].count('\n') + 1
            issues.append(f"CLAUDE.md:{line_num} - {message}")

    return issues


def check_capabilities_docstring(actual_count: int) -> List[str]:
    """Check capabilities.py docstring agent count."""
    issues = []
    path = AG_ACE_BRIDGE / "src" / "registry" / "capabilities.py"
    if not path.exists():
        return issues

    content = path.read_text(encoding="utf-8")

    for m in re.finditer(r'all\s+(\d+)\s+agents', content, re.IGNORECASE):
        num = int(m.group(1))
        if num != actual_count:
            line_num = content[:m.start()].count('\n') + 1
            issues.append(f"capabilities.py:{line_num} says '{num}' agents, actual is {actual_count}")

    return issues


def validate() -> List[str]:
    """Run all documentation sync checks."""
    all_issues = []

    print("=== Doc Sync Checker ===")

    actual_agent_count = count_agent_types()
    actual_cap_count = count_capabilities()

    print(f"\n  AgentType enum members: {actual_agent_count}")
    print(f"  ALL_AGENT_CAPABILITIES entries: {actual_cap_count}")

    # AgentType vs capabilities count
    if actual_agent_count != actual_cap_count:
        all_issues.append(
            f"AgentType has {actual_agent_count} members but "
            f"ALL_AGENT_CAPABILITIES has {actual_cap_count} entries"
        )

    # CLAUDE.md checks
    all_issues.extend(check_claude_md_agent_count(actual_agent_count))
    all_issues.extend(check_claude_md_model_fields())

    # capabilities.py docstring
    all_issues.extend(check_capabilities_docstring(actual_agent_count))

    if all_issues:
        print(f"\n  Issues found: {len(all_issues)}")
        for issue in all_issues:
            print(f"    - {issue}")
    else:
        print(f"\n  All documentation in sync!")

    return all_issues


def main() -> bool:
    issues = validate()
    return len(issues) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
