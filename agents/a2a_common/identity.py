"""Which code is answering - standard library only, so the tool surface can say it.

ONE OWNER: agents/a2a_common/identity.py, copied byte-for-byte into every agent's
a2a_service/identity.py the same way protocol.py is; each agent's conformance test guards
both copies. Change it here, then copy.

It is deliberately free of the a2a SDK. tools.py imports it, and tools.py has to stay
importable in any interpreter - the rules tests run without the transport installed
(agents/docs/AGENT_MODULE_CONVENTIONS.md section 3-1: the rules/tool surface never pulls
the transport SDK). protocol.py does not import this module; the two are independent.

`code_identity` reads the checkout's git hash so the card version, the health reply and
the caller's receipt all say the same thing; "is the fix live?" then has an answer other
than sending a query and guessing. A fix is not live until the process is replaced.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def code_identity(root: Path, entry: Path, git: str | None = "git") -> dict[str, Any]:
    """`{"git": short hash | None, "dirty": bool | None, "entry_mtime": iso | None}`. Never raises.

    `git` first: `rev-parse --short HEAD` and `status --porcelain`. Without a usable git
    (ProgramAgent and the Orchestrator worker are launched from PowerShell, where it may
    be off PATH) the hash is read straight from `.git/HEAD` and the ref it names; `dirty`
    is then None rather than a guess. A server must boot without git, and a health reply
    must say what it does not know.
    """
    identity: dict[str, Any] = {"git": None, "dirty": None, "entry_mtime": None}
    try:
        identity["entry_mtime"] = datetime.fromtimestamp(
            entry.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    except OSError:
        pass
    if git:
        try:
            def run(*args: str) -> str:
                return subprocess.run([git, "-C", str(root), *args], capture_output=True, text=True,
                                      timeout=5, check=True).stdout.strip()
            identity["git"] = run("rev-parse", "--short", "HEAD") or None
            identity["dirty"] = bool(run("status", "--porcelain"))
            return identity
        except Exception:
            pass
    try:
        dot_git = root / ".git"
        head = (dot_git / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = head[5:]
            ref_file = dot_git / ref
            if ref_file.exists():
                sha = ref_file.read_text(encoding="utf-8").strip()
            else:
                sha = next((line.split()[0] for line in
                            (dot_git / "packed-refs").read_text(encoding="utf-8").splitlines()
                            if line.endswith(" " + ref)), "")
        else:
            sha = head
        identity["git"] = sha[:7] or None
    except Exception:
        pass
    return identity


def version_string(base: str, identity: dict[str, Any]) -> str:
    """`0.1.0+4ed9e4c`, `0.1.0+4ed9e4c.dirty`, or the bare base when no hash is known."""
    if not identity.get("git"):
        return base
    return f"{base}+{identity['git']}" + (".dirty" if identity.get("dirty") else "")


__all__ = ["code_identity", "version_string"]
