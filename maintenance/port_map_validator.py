"""
Port Map Validator - Cross-checks port mappings across 4 sources.

Sources:
1. AG-ACE-BRIDGE ag_a2a_adapter.py (A2A_AGENT_PORTS)
2. AG-ACE-BRIDGE capabilities.py (endpoint URLs)
3. Auto-Claude a2a-handlers.ts (DEFAULT_A2A_AGENTS + portToAgent)
4. AG-ACE-BRIDGE CLAUDE.md (documented ports)
"""

import re
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple

# Base paths
BASE = Path(__file__).resolve().parent.parent
AG_ACE_BRIDGE = BASE / "AG-ACE-BRIDGE"
AUTO_CLAUDE = BASE / "Auto-Claude"


def extract_a2a_adapter_ports() -> Dict[str, int]:
    """Extract ports from ag_a2a_adapter.py A2A_AGENT_PORTS."""
    path = AG_ACE_BRIDGE / "src" / "adapters" / "ag_a2a_adapter.py"
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")
    ports = {}
    # Match patterns like: A2AAgentType.POETRY: 8003,
    for m in re.finditer(r'A2AAgentType\.(\w+):\s*(\d+)', content):
        name = m.group(1).lower()
        port = int(m.group(2))
        ports[name] = port
    return ports


def extract_capabilities_ports() -> Dict[str, int]:
    """Extract ports from capabilities.py endpoint URLs."""
    path = AG_ACE_BRIDGE / "src" / "registry" / "capabilities.py"
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")
    ports = {}
    # Match AG_A2A_* variable definitions with endpoint
    blocks = re.split(r'\n(?=AG_A2A_\w+\s*=)', content)
    for block in blocks:
        name_match = re.match(r'(AG_A2A_\w+)', block)
        port_match = re.search(r'endpoint="http://localhost:(\d+)', block)
        if name_match and port_match:
            name = name_match.group(1).replace("AG_A2A_", "").lower()
            ports[name] = int(port_match.group(1))
    return ports


def extract_auto_claude_ports() -> Tuple[Dict[str, int], Dict[str, int]]:
    """Extract ports from a2a-handlers.ts DEFAULT_A2A_AGENTS and portToAgent."""
    path = AUTO_CLAUDE / "apps" / "AG-Frontend" / "src" / "main" / "ipc-handlers" / "a2a-handlers.ts"
    if not path.exists():
        return {}, {}

    content = path.read_text(encoding="utf-8")

    # DEFAULT_A2A_AGENTS
    default_ports = {}
    for m in re.finditer(r"name:\s*'(\w+)'.*?port:\s*(\d+)", content, re.DOTALL):
        default_ports[m.group(1)] = int(m.group(2))

    # portToAgent map
    port_to_agent = {}
    for m in re.finditer(r"'(\d+)':\s*'(\w+)'", content):
        port_to_agent[m.group(2)] = int(m.group(1))

    return default_ports, port_to_agent


def extract_claude_md_ports() -> Dict[str, int]:
    """Extract A2A agent ports from CLAUDE.md."""
    path = AG_ACE_BRIDGE / "CLAUDE.md"
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")
    ports = {}
    # Match table rows like: | poetry_agent | 8003 | or port references
    for m in re.finditer(r'\|\s*(\w+_agent)\s*\|\s*(\d+)\s*\|', content):
        ports[m.group(1)] = int(m.group(2))
    # Also match AG_A2A_* | ... | port patterns
    for m in re.finditer(r'`AG_A2A_(\w+)`\s*\|[^|]*\|\s*(\d+)', content):
        ports[m.group(1).lower()] = int(m.group(2))
    return ports


def normalize_name(name: str) -> str:
    """Normalize agent name for comparison."""
    name = name.lower().strip()
    name = name.replace("_agent", "").replace("ag_a2a_", "")
    return name


def validate() -> List[str]:
    """Validate port mappings across all sources. Returns list of issues."""
    issues = []

    adapter_ports = extract_a2a_adapter_ports()
    cap_ports = extract_capabilities_ports()
    default_ports, port_to_agent_ports = extract_auto_claude_ports()
    doc_ports = extract_claude_md_ports()

    # Normalize all names
    sources = {
        "ag_a2a_adapter.py": {normalize_name(k): v for k, v in adapter_ports.items()},
        "capabilities.py": {normalize_name(k): v for k, v in cap_ports.items()},
        "a2a-handlers.ts (DEFAULT)": {normalize_name(k): v for k, v in default_ports.items()},
        "a2a-handlers.ts (portToAgent)": {normalize_name(k): v for k, v in port_to_agent_ports.items()},
        "CLAUDE.md": {normalize_name(k): v for k, v in doc_ports.items()},
    }

    # Collect all agent names
    all_agents: Set[str] = set()
    for src_ports in sources.values():
        all_agents.update(src_ports.keys())

    print("=== Port Map Validation ===")
    print(f"\n  {'Agent':<20s}", end="")
    for src_name in sources:
        print(f"  {src_name[:15]:>15s}", end="")
    print()
    print("  " + "-" * 100)

    for agent in sorted(all_agents):
        ports_for_agent = {}
        print(f"  {agent:<20s}", end="")
        for src_name, src_ports in sources.items():
            port = src_ports.get(agent, None)
            if port is not None:
                ports_for_agent[src_name] = port
            print(f"  {str(port or '-'):>15s}", end="")
        print()

        # Check consistency
        unique_ports = set(ports_for_agent.values())
        if len(unique_ports) > 1:
            issues.append(f"Port mismatch for '{agent}': {ports_for_agent}")

        # Check missing
        for src_name in sources:
            if agent not in sources[src_name] and sources[src_name]:
                issues.append(f"Agent '{agent}' missing from {src_name}")

    if issues:
        print(f"\n  Issues found: {len(issues)}")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("\n  All port mappings consistent!")

    return issues


def main() -> bool:
    issues = validate()
    return len(issues) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
