#!/usr/bin/env python3
"""A2A Agent Manager - CLI tool for A2A agent lifecycle management.

Scans directories for A2A agent.py files, generates JSON catalog entries,
registers agents with AutoGen Studio, and provides health checks.

Usage:
    python a2a_manager.py --scan                    # Scan dirs -> generate/update JSON catalog
    python a2a_manager.py --register                # Register all with AutoGen Studio
    python a2a_manager.py --check                   # Health check all agents
    python a2a_manager.py --start calculator        # Start agent in background
    python a2a_manager.py --list                    # Show all agents + status
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
A2A_DIR = BASE_DIR / "a2a_agents"
REGISTRY_PATH = BASE_DIR / "registry.json"

# Default scan directories
DEFAULT_SCAN_DIRS = [
    "D:/Data/22_AG/autogen_a2a_kit/a2a_demo",
    "D:/Data/25_ACE/AG/agent/a2a",
]

# Directories to skip (not A2A servers)
SKIP_DIRS = {"root_agent", "__pycache__", ".git"}


def load_registry() -> dict:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry: dict):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def load_a2a_agents() -> dict[str, dict]:
    """Load all a2a_agents/*.json files. Returns {filename_stem: data}."""
    agents = {}
    if not A2A_DIR.exists():
        return agents
    for f in sorted(A2A_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            agents[f.stem] = json.load(fp)
    return agents


# ---------------------------------------------------------------------------
# --scan: Parse agent.py files and generate JSON catalog
# ---------------------------------------------------------------------------

def parse_agent_file(filepath: Path) -> dict | None:
    """Extract metadata from an agent.py file using regex."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"  [WARN] Cannot read {filepath}: {e}")
        return None

    name = _extract(r'name\s*=\s*["\']([^"\']+)["\']', content)
    description = _extract(r'description\s*=\s*["\']([^"\']+)["\']', content)
    port = _extract(r'port\s*[=:]\s*(\d+)', content)

    if not name or not port:
        return None

    # Extract skills/tools (function definitions with @tool or FunctionTool)
    skills = []
    # Pattern: def func_name(... -> extract name and docstring
    for match in re.finditer(r'def\s+(\w+)\s*\([^)]*\)[^:]*:\s*(?:\n\s+)?"""([^"]*?)"""', content):
        fname, doc = match.groups()
        if fname.startswith("_"):
            continue
        skills.append({"name": fname, "description": doc.strip().split("\n")[0]})

    # Fallback: FunctionTool(func_name, ...) patterns
    if not skills:
        for match in re.finditer(r'FunctionTool\(\s*(\w+)', content):
            fname = match.group(1)
            skills.append({"name": fname, "description": f"{fname} tool"})

    return {
        "name": name,
        "description": description or f"{name} A2A agent",
        "port": int(port),
        "skills": skills,
        "agent_file": str(filepath).replace("\\", "/"),
    }


def _extract(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def scan_agents(scan_dirs: list[str] | None = None):
    """Scan directories for agent.py files and generate/update JSON catalog."""
    dirs = list(scan_dirs) if scan_dirs else list(DEFAULT_SCAN_DIRS)
    env_dirs = os.environ.get("A2A_SCAN_DIRS", "")
    if env_dirs:
        dirs.extend(env_dirs.split(os.pathsep))

    A2A_DIR.mkdir(exist_ok=True)
    found = []

    for scan_dir in dirs:
        scan_path = Path(scan_dir)
        if not scan_path.exists():
            print(f"  [SKIP] {scan_dir} (not found)")
            continue

        for agent_file in sorted(scan_path.glob("*/agent.py")):
            parent_name = agent_file.parent.name
            if parent_name in SKIP_DIRS:
                continue

            meta = parse_agent_file(agent_file)
            if not meta:
                print(f"  [SKIP] {agent_file} (no name/port)")
                continue

            # Normalize: use agent name for file stem
            file_stem = meta["name"] if meta["name"].endswith("_agent") else parent_name
            json_path = A2A_DIR / f"{file_stem}.json"

            agent_json = {
                "provider": "autogenstudio.a2a.A2AAgent",
                "component_type": "agent",
                "version": 1,
                "description": meta["description"],
                "label": meta["name"].replace("_", " ").title(),
                "config": {
                    "name": meta["name"],
                    "a2a_server_url": f"http://localhost:{meta['port']}",
                    "description": meta["description"],
                    "timeout": 300,
                    "skills": meta["skills"],
                },
                "_source": {
                    "agent_file": meta["agent_file"],
                    "port": meta["port"],
                    "framework": "google_adk",
                },
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(agent_json, f, indent=2, ensure_ascii=False)

            print(f"  [OK] {json_path.name} (port {meta['port']}, {len(meta['skills'])} skills)")
            found.append((file_stem, meta))

    # Update registry.json
    registry = load_registry()
    a2a_section = registry.get("a2a_agents", {})
    for file_stem, meta in found:
        # Registry ID: remove _agent suffix for brevity
        rid = file_stem.replace("_agent", "")
        a2a_section[rid] = {
            "file": f"a2a_agents/{file_stem}.json",
            "name": meta["name"],
            "port": meta["port"],
            "label": meta["name"].replace("_", " ").title(),
        }
    registry["a2a_agents"] = a2a_section
    save_registry(registry)

    print(f"\nScanned {len(found)} agents, registry updated.")


# ---------------------------------------------------------------------------
# --register: Register agents with AutoGen Studio
# ---------------------------------------------------------------------------

def register_agents():
    """Register all A2A agents with AutoGen Studio API."""
    try:
        import httpx
    except ImportError:
        print("httpx required: pip install httpx")
        return

    api_base = os.environ.get("AUTOGEN_STUDIO_API", "http://localhost:8081/api")
    agents = load_a2a_agents()

    for name, data in agents.items():
        url = data.get("config", {}).get("a2a_server_url", "")
        if not url:
            print(f"  [SKIP] {name}: no a2a_server_url")
            continue

        try:
            resp = httpx.post(
                f"{api_base}/a2a/registry/register",
                json={"url": url},
                timeout=10,
            )
            if resp.status_code == 200:
                print(f"  [OK] {name} -> registered ({url})")
            else:
                print(f"  [FAIL] {name}: {resp.status_code} {resp.text[:200]}")
        except httpx.ConnectError:
            print(f"  [FAIL] Cannot connect to AutoGen Studio at {api_base}")
            return
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    print(f"\nRegistration complete ({len(agents)} agents).")


# ---------------------------------------------------------------------------
# --check: Health check agents
# ---------------------------------------------------------------------------

def check_agents():
    """Health check all A2A agents by querying their well-known endpoint."""
    try:
        import httpx
    except ImportError:
        print("httpx required: pip install httpx")
        return

    agents = load_a2a_agents()
    online = 0
    offline = 0

    print(f"{'Name':<30} {'Port':<8} {'Status':<10} {'Info'}")
    print("-" * 70)

    for name, data in agents.items():
        source = data.get("_source", {})
        port = source.get("port", 0)
        url = data.get("config", {}).get("a2a_server_url", f"http://localhost:{port}")

        try:
            resp = httpx.get(f"{url}/.well-known/agent.json", timeout=5)
            if resp.status_code == 200:
                info = resp.json()
                agent_name = info.get("name", "?")
                print(f"  {name:<28} {port:<8} {'ONLINE':<10} {agent_name}")
                online += 1
            else:
                print(f"  {name:<28} {port:<8} {'ERROR':<10} HTTP {resp.status_code}")
                offline += 1
        except Exception:
            print(f"  {name:<28} {port:<8} {'OFFLINE':<10}")
            offline += 1

    print(f"\n{online} online, {offline} offline (total: {online + offline})")


# ---------------------------------------------------------------------------
# --start: Start an agent in background
# ---------------------------------------------------------------------------

def start_agent(agent_id: str):
    """Start an A2A agent by looking up its _source.agent_file."""
    try:
        import httpx
    except ImportError:
        print("httpx required: pip install httpx")
        return

    agents = load_a2a_agents()

    # Find matching agent
    match = None
    for name, data in agents.items():
        if agent_id in name or agent_id == name.replace("_agent", ""):
            match = (name, data)
            break

    if not match:
        print(f"Agent not found: {agent_id}")
        print(f"Available: {', '.join(agents.keys())}")
        return

    name, data = match
    source = data.get("_source", {})
    agent_file = source.get("agent_file")
    port = source.get("port")

    if not agent_file:
        print(f"No _source.agent_file for {name}")
        return

    agent_path = Path(agent_file).resolve()
    if not agent_path.exists():
        print(f"Agent file not found: {agent_file}")
        return
    # Validate: must be a .py file under known scan directories
    allowed_roots = [Path(d).resolve() for d in DEFAULT_SCAN_DIRS]
    if not any(agent_path == root or agent_path.is_relative_to(root) for root in allowed_roots):
        print(f"[SECURITY] Agent file outside allowed dirs: {agent_path}")
        return
    if agent_path.suffix != ".py":
        print(f"[SECURITY] Not a Python file: {agent_path}")
        return

    print(f"Starting {name} (port {port})...")
    proc = subprocess.Popen(
        [sys.executable, str(agent_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    print(f"  PID: {proc.pid}")

    # Poll for readiness
    url = f"http://localhost:{port}/.well-known/agent.json"
    for i in range(15):
        time.sleep(2)
        try:
            resp = httpx.get(url, timeout=3)
            if resp.status_code == 200:
                print(f"  [OK] {name} is ready on port {port}")
                return
        except Exception:
            pass
        print(f"  Waiting... ({(i + 1) * 2}s)")

    print(f"  [WARN] Agent started (PID {proc.pid}) but port {port} not responding after 30s")


# ---------------------------------------------------------------------------
# --list: Show all agents
# ---------------------------------------------------------------------------

def list_agents():
    """List all registered A2A agents."""
    agents = load_a2a_agents()
    if not agents:
        print("No A2A agents found in a2a_agents/")
        return

    print(f"{'Name':<30} {'Port':<8} {'Skills':<8} {'Description'}")
    print("-" * 80)

    for name, data in agents.items():
        config = data.get("config", {})
        source = data.get("_source", {})
        port = source.get("port", "?")
        skills = len(config.get("skills", []))
        desc = config.get("description", "")[:40]
        print(f"  {name:<28} {port:<8} {skills:<8} {desc}")

    print(f"\nTotal: {len(agents)} agents")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="A2A Agent Manager - Scan, register, and manage A2A agents"
    )
    parser.add_argument("--scan", action="store_true",
                        help="Scan directories for agent.py files, generate JSON catalog")
    parser.add_argument("--register", action="store_true",
                        help="Register all agents with AutoGen Studio API")
    parser.add_argument("--check", action="store_true",
                        help="Health check all agents")
    parser.add_argument("--start", type=str, metavar="AGENT",
                        help="Start an agent in background")
    parser.add_argument("--list", action="store_true",
                        help="List all registered agents")
    parser.add_argument("--scan-dirs", type=str, nargs="*",
                        help="Additional directories to scan")

    args = parser.parse_args()

    if args.scan:
        extra_dirs = args.scan_dirs or []
        scan_agents(DEFAULT_SCAN_DIRS + extra_dirs)
    elif args.register:
        register_agents()
    elif args.check:
        check_agents()
    elif args.start:
        start_agent(args.start)
    elif args.list:
        list_agents()
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
