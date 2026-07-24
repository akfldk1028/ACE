"""Shared replay context extraction for HTTP and management entry points."""

from __future__ import annotations

from typing import Any


_DOWNSTREAM_STAGE_IDS = frozenset({
    "site",
    "capacity",
    "law",
    "parking",
    "program_fit",
    "selector",
})


def downstream_evidence_from_passport(
    passport: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Preserve evaluated source-stage evidence when one MASS is replayed."""

    return {
        str(stage.get("id")): dict(stage.get("evidence") or {})
        for stage in passport.get("stages") or ()
        if isinstance(stage, dict)
        and stage.get("id") in _DOWNSTREAM_STAGE_IDS
        and stage.get("status") != "not_evaluated"
    }


__all__ = ["downstream_evidence_from_passport"]
