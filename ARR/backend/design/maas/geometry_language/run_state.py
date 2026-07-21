"""Small durable lifecycle record for long-running MASS portfolio executions."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps
import json
import os
from pathlib import Path
from typing import Any, Callable, TypeVar


RUN_STATE_FILENAME = "maas-run-state.json"
RUN_STATE_SCHEMA = "arr.maas.run_state.v1"

_T = TypeVar("_T")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_run_state(output_dir: Path, payload: dict[str, Any]) -> Path:
    """Atomically persist a bounded, credential-free execution state record."""
    directory = Path(output_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / RUN_STATE_FILENAME
    temporary = directory / f".{RUN_STATE_FILENAME}.{os.getpid()}.tmp"
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def tracked_mass_command(function: Callable[..., _T]) -> Callable[..., _T]:
    """Decorate a Django command handle so normal failures remain discoverable."""
    @wraps(function)
    def wrapped(command: Any, *args: Any, **options: Any) -> _T:
        output_dir = Path(str(options["output_dir"])).resolve()
        created_at = _now()
        base = {
            "schema_version": RUN_STATE_SCHEMA,
            "run_id": output_dir.name,
            "pnu": str(options.get("pnu") or ""),
            "programs": list(options.get("program") or ()),
            "recursive_only": bool(options.get("recursive_only")),
            "live_vlm_requested": bool(options.get("live_vlm")),
            "created_at": created_at,
            "pid": os.getpid(),
        }
        write_run_state(output_dir, {
            **base,
            "updated_at": created_at,
            "status": "running",
            "selected_mass_count": 0,
        })
        try:
            result = function(command, *args, **options)
        except BaseException as exc:
            write_run_state(output_dir, {
                **base,
                "updated_at": _now(),
                "status": "failed",
                "selected_mass_count": 0,
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
            })
            raise
        selected_count = 0
        if isinstance(result, dict):
            selected_count = sum(
                int(item.get("selected_count") or 0)
                for item in result.get("programs") or ()
                if isinstance(item, dict)
            )
        write_run_state(output_dir, {
            **base,
            "updated_at": _now(),
            "status": "completed",
            "selected_mass_count": selected_count,
            "result_status": str(result.get("status") or "unknown")
            if isinstance(result, dict)
            else "unknown",
        })
        return result

    return wrapped


__all__ = [
    "RUN_STATE_FILENAME",
    "RUN_STATE_SCHEMA",
    "tracked_mass_command",
    "write_run_state",
]
