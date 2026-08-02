"""Process-wide accounting for actual paid provider network requests."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import os
from threading import Lock
from typing import Any


PAID_PROVIDER_BUDGET_SCHEMA = "arr.maas.paid_provider_budget.v1"
_DEFAULT_LIMIT = 256
_MAXIMUM_LIMIT = 256
_LOCK = Lock()


class PaidProviderBudgetError(RuntimeError):
    """Raised before a paid network request would exceed its hard ceiling."""


@dataclass
class _PaidProviderBudgetState:
    limit: int
    request_count: int = 0
    request_counts_by_kind: Counter[str] = field(default_factory=Counter)


def _environment_limit() -> int:
    try:
        value = int(os.getenv(
            "MAAS_PAID_PROVIDER_MAX_REQUESTS",
            str(_DEFAULT_LIMIT),
        ))
    except (TypeError, ValueError):
        value = _DEFAULT_LIMIT
    return max(1, min(_MAXIMUM_LIMIT, value))


_STATE = _PaidProviderBudgetState(limit=_environment_limit())


def _snapshot_unlocked() -> dict[str, Any]:
    return {
        "schema_version": PAID_PROVIDER_BUDGET_SCHEMA,
        "limit": _STATE.limit,
        "request_count": _STATE.request_count,
        "remaining_count": max(0, _STATE.limit - _STATE.request_count),
        "request_counts_by_kind": dict(sorted(
            _STATE.request_counts_by_kind.items()
        )),
    }


def configure_paid_provider_budget(limit: int) -> None:
    resolved = int(limit)
    if resolved < 1 or resolved > _MAXIMUM_LIMIT:
        raise ValueError(
            f"paid provider request limit must be between 1 and "
            f"{_MAXIMUM_LIMIT}"
        )
    with _LOCK:
        if _STATE.request_count:
            raise PaidProviderBudgetError(
                "paid_provider_budget_already_consumed:"
                f"{_STATE.request_count}"
            )
        _STATE.limit = resolved
        _STATE.request_counts_by_kind.clear()


def reserve_paid_provider_request(kind: str) -> dict[str, Any]:
    normalized = str(kind or "").strip()
    if not normalized:
        raise ValueError("paid provider request kind is required")
    with _LOCK:
        if _STATE.request_count >= _STATE.limit:
            raise PaidProviderBudgetError(
                "paid_provider_request_budget_exhausted:"
                f"{_STATE.request_count}/{_STATE.limit}"
            )
        _STATE.request_count += 1
        _STATE.request_counts_by_kind[normalized] += 1
        return _snapshot_unlocked()


def paid_provider_budget_snapshot() -> dict[str, Any]:
    with _LOCK:
        return _snapshot_unlocked()


def reset_paid_provider_budget_for_tests() -> None:
    with _LOCK:
        _STATE.limit = _environment_limit()
        _STATE.request_count = 0
        _STATE.request_counts_by_kind.clear()


__all__ = [
    "PAID_PROVIDER_BUDGET_SCHEMA",
    "PaidProviderBudgetError",
    "configure_paid_provider_budget",
    "paid_provider_budget_snapshot",
    "reserve_paid_provider_request",
    "reset_paid_provider_budget_for_tests",
]
