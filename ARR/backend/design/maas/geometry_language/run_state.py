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


def _read_run_state(output_dir: Path) -> dict[str, Any]:
    target = Path(output_dir).resolve() / RUN_STATE_FILENAME
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def update_run_progress(output_dir: Path, **progress: Any) -> Path:
    """Merge bounded progress into a running lifecycle record."""

    directory = Path(output_dir).resolve()
    current = _read_run_state(directory)
    if not current:
        current = {
            "schema_version": RUN_STATE_SCHEMA,
            "run_id": directory.name,
            "created_at": _now(),
            "pid": os.getpid(),
        }
    if not isinstance(current, dict):
        current = {}
    safe_progress = {
        key: value for key, value in progress.items()
        if key in {
            "phase", "program", "cycle_index", "cycle_budget",
            "selection_pool_count", "selected_mass_count",
            "required_scope_count", "selected_scope_count", "stop_reason",
        }
    }
    return write_run_state(directory, {
        **current,
        **safe_progress,
        "schema_version": RUN_STATE_SCHEMA,
        "run_id": directory.name,
        "pid": int(current.get("pid") or os.getpid()),
        "status": "running",
        "updated_at": _now(),
    })


def tracked_mass_command(function: Callable[..., _T]) -> Callable[..., _T]:
    """Decorate a Django command handle so normal failures remain discoverable."""
    @wraps(function)
    def wrapped(command: Any, *args: Any, **options: Any) -> _T:
        output_dir = Path(str(options["output_dir"])).resolve()
        created_at = _now()
        try:
            from design.maas.book_language.quality_diversity_archive import qd_archive_policy

            quality_diversity = qd_archive_policy()
        except (ImportError, ValueError):
            quality_diversity = {}
        base = {
            "schema_version": RUN_STATE_SCHEMA,
            "run_id": output_dir.name,
            "pnu": str(options.get("pnu") or ""),
            "programs": list(options.get("program") or ()),
            "recursive_only": bool(options.get("recursive_only")),
            "live_vlm_requested": bool(options.get("live_vlm")),
            "outcome_graph_path": str(options.get("outcome_graph") or ""),
            "quality_diversity_archive": quality_diversity,
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
            command_result = function(command, *args, **options)
        except BaseException as exc:
            current = _read_run_state(output_dir)
            write_run_state(output_dir, {
                **base,
                **current,
                "updated_at": _now(),
                "status": "failed",
                "selected_mass_count": int(current.get("selected_mass_count") or 0),
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
            })
            raise
        evidence_result = command_result
        if not isinstance(evidence_result, dict):
            summary_path = output_dir / "maas-book-programs-summary.json"
            if summary_path.is_file():
                try:
                    persisted = json.loads(summary_path.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError):
                    persisted = None
                if isinstance(persisted, dict):
                    evidence_result = persisted
        selected_count = 0
        if isinstance(evidence_result, dict):
            selected_count = sum(
                int(item.get("selected_count") or 0)
                for item in evidence_result.get("programs") or ()
                if isinstance(item, dict)
            )
        result_status = (
            str(evidence_result.get("status") or "unknown")
            if isinstance(evidence_result, dict)
            else "unknown"
        )
        current = _read_run_state(output_dir)
        write_run_state(output_dir, {
            **base,
            **current,
            "updated_at": _now(),
            "status": (
                "completed"
                if result_status == "pass"
                else "completed_with_failed_gate"
            ),
            "selected_mass_count": selected_count,
            "result_status": result_status,
        })
        return command_result

    return wrapped


__all__ = [
    "RUN_STATE_FILENAME",
    "RUN_STATE_SCHEMA",
    "tracked_mass_command",
    "update_run_progress",
    "write_run_state",
]
