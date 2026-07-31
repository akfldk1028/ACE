"""
Health Check - Server health verification for AG-ACE ecosystem.

Checks:
- AG-ACE-BRIDGE dashboard (8080)
- AutoGen Studio (8081)
- SharedMemory (8101)
- A2A agents (8003-8120)
- Claude CLI Plan agent (9018)
"""

import asyncio
import sys
from typing import Dict, Tuple

try:
    import httpx
except ImportError:
    httpx = None


# All servers/services to check
SERVERS = {
    "AG-ACE-BRIDGE Dashboard": ("http://localhost:8080", "/"),
    "AutoGen Studio": ("http://localhost:8081", "/api/version"),
    "SharedMemory": ("http://localhost:8101", "/health"),
    "A2A poetry_agent": ("http://localhost:8003", "/.well-known/agent.json"),
    "A2A philosophy_agent": ("http://localhost:8004", "/.well-known/agent.json"),
    "A2A history_agent": ("http://localhost:8005", "/.well-known/agent.json"),
    "A2A calculator_agent": ("http://localhost:8006", "/.well-known/agent.json"),
    "A2A gui_test_agent": ("http://localhost:8120", "/.well-known/agent.json"),
    "Claude CLI Plan": ("http://localhost:9018", "/.well-known/agent.json"),
}


async def check_server(name: str, base_url: str, path: str, timeout: float = 5.0) -> Tuple[str, bool, str]:
    """Check if a server is responding."""
    url = f"{base_url}{path}"
    try:
        if httpx:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=timeout)
                if resp.status_code < 500:
                    return (name, True, f"HTTP {resp.status_code}")
                return (name, False, f"HTTP {resp.status_code}")
        else:
            # Fallback: use urllib
            import urllib.request
            import urllib.error
            req = urllib.request.Request(url)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return (name, True, f"HTTP {resp.status}")
            except urllib.error.HTTPError as e:
                if e.code < 500:
                    return (name, True, f"HTTP {e.code}")
                return (name, False, f"HTTP {e.code}")
    except Exception as e:
        error_type = type(e).__name__
        return (name, False, f"{error_type}: {str(e)[:80]}")


async def run_health_check() -> Dict[str, bool]:
    """Run health checks on all servers."""
    tasks = [
        check_server(name, base_url, path)
        for name, (base_url, path) in SERVERS.items()
    ]
    results = await asyncio.gather(*tasks)

    status = {}
    for name, is_ok, detail in results:
        status[name] = is_ok
        icon = "OK" if is_ok else "FAIL"
        print(f"  [{icon:4s}] {name:30s} {detail}")

    return status


def main() -> bool:
    """Run health check and return True if all pass."""
    print("=== Health Check ===")
    status = asyncio.run(run_health_check())

    online = sum(1 for v in status.values() if v)
    total = len(status)
    print(f"\n  {online}/{total} servers online")

    return all(status.values())


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
