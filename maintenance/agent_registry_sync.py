"""
Agent Registry Sync - Cross-checks agent registrations across 4 sources.

Sources:
1. models.py AgentType enum
2. capabilities.py ALL_AGENT_CAPABILITIES keys
3. ag_a2a_adapter.py A2AAgentType enum (A2A subset)
4. Auto-Claude a2a-handlers.ts DEFAULT_A2A_AGENTS (A2A subset)
"""

import re
import sys
from pathlib import Path
from typing import Set, List

BASE = Path(__file__).resolve().parent.parent
AG_ACE_BRIDGE = BASE / "AG-ACE-BRIDGE"
AUTO_CLAUDE = BASE / "Auto-Claude"


def extract_agent_types_from_models() -> Set[str]:
    """Extract AgentType enum values from models.py."""
    path = AG_ACE_BRIDGE / "src" / "utils" / "models.py"
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")
    agents = set()
    # Match: AG_A2A_POETRY = "ag.a2a.poetry_agent"
    for m in re.finditer(r'^\s+(\w+)\s*=\s*"([^"]+)"', content, re.MULTILINE):
        enum_name = m.group(1)
        # Only inside AgentType class
        agents.add(enum_name)

    # More precise: extract only AgentType block
    block_match = re.search(r'class AgentType\(.*?\):\s*\n(.*?)(?=\nclass |\Z)', content, re.DOTALL)
    if block_match:
        agents = set()
        block = block_match.group(1)
        for m in re.finditer(r'^\s+(\w+)\s*=\s*"', block, re.MULTILINE):
            agents.add(m.group(1))

    return agents


def extract_capabilities_keys() -> Set[str]:
    """Extract ALL_AGENT_CAPABILITIES keys from capabilities.py."""
    path = AG_ACE_BRIDGE / "src" / "registry" / "capabilities.py"
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")
    keys = set()
    # Match: AgentType.AUTO_CLAUDE_PLANNER: AUTO_CLAUDE_PLANNER,
    for m in re.finditer(r'AgentType\.(\w+):', content):
        keys.add(m.group(1))
    return keys


def extract_a2a_agent_types() -> Set[str]:
    """Extract A2AAgentType enum from ag_a2a_adapter.py."""
    path = AG_ACE_BRIDGE / "src" / "adapters" / "ag_a2a_adapter.py"
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")
    agents = set()
    block_match = re.search(r'class A2AAgentType\(.*?\):\s*\n(.*?)(?=\n\n|\nclass )', content, re.DOTALL)
    if block_match:
        block = block_match.group(1)
        for m in re.finditer(r'^\s+(\w+)\s*=\s*"(\w+)"', block, re.MULTILINE):
            agents.add(m.group(2))  # value like "poetry_agent"
    return agents


def extract_auto_claude_agents() -> Set[str]:
    """Extract agent names from a2a-handlers.ts DEFAULT_A2A_AGENTS."""
    path = AUTO_CLAUDE / "apps" / "AG-Frontend" / "src" / "main" / "ipc-handlers" / "a2a-handlers.ts"
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")
    agents = set()
    for m in re.finditer(r"name:\s*'(\w+)'", content):
        agents.add(m.group(1))
    return agents


def validate() -> List[str]:
    """Validate agent registry sync across all sources."""
    issues = []

    model_agents = extract_agent_types_from_models()
    cap_agents = extract_capabilities_keys()
    a2a_agents = extract_a2a_agent_types()
    ac_agents = extract_auto_claude_agents()

    print("=== Agent Registry Sync ===")
    print(f"\n  models.py AgentType:         {len(model_agents)} agents")
    print(f"  capabilities.py keys:        {len(cap_agents)} agents")
    print(f"  ag_a2a_adapter.py A2A:       {len(a2a_agents)} agents")
    print(f"  a2a-handlers.ts DEFAULT:     {len(ac_agents)} agents")

    # Check 1: All AgentType enum members should be in capabilities
    missing_in_caps = model_agents - cap_agents
    if missing_in_caps:
        for agent in sorted(missing_in_caps):
            issues.append(f"AgentType.{agent} not in ALL_AGENT_CAPABILITIES")
        print(f"\n  Missing from capabilities.py: {sorted(missing_in_caps)}")
    else:
        print(f"\n  All AgentType enums registered in capabilities.py")

    # Check 2: capabilities shouldn't have keys not in AgentType
    extra_in_caps = cap_agents - model_agents
    if extra_in_caps:
        for agent in sorted(extra_in_caps):
            issues.append(f"ALL_AGENT_CAPABILITIES has {agent} but no AgentType enum")
        print(f"  Extra in capabilities.py: {sorted(extra_in_caps)}")

    # Check 3: A2A agents in adapter should match Auto-Claude
    a2a_names = a2a_agents
    ac_names = ac_agents
    missing_in_ac = a2a_names - ac_names
    extra_in_ac = ac_names - a2a_names

    if missing_in_ac:
        for agent in sorted(missing_in_ac):
            issues.append(f"A2A agent '{agent}' in adapter but not in Auto-Claude DEFAULT_A2A_AGENTS")
        print(f"  Missing from Auto-Claude: {sorted(missing_in_ac)}")

    if extra_in_ac:
        for agent in sorted(extra_in_ac):
            issues.append(f"A2A agent '{agent}' in Auto-Claude but not in adapter A2AAgentType")
        print(f"  Extra in Auto-Claude: {sorted(extra_in_ac)}")

    if not missing_in_ac and not extra_in_ac:
        print(f"  A2A agents consistent between adapter and Auto-Claude")

    if issues:
        print(f"\n  Total issues: {len(issues)}")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"\n  All agent registries in sync!")

    return issues


def main() -> bool:
    issues = validate()
    return len(issues) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
