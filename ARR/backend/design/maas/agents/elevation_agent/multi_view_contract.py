"""Shared contracts for identity-bound creative facade views."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol


FACADE_VIEWS = ("front", "right", "back", "left")


class MultiViewCritic(Protocol):
    name: str

    def evaluate(
        self,
        *,
        identity: Mapping[str, str],
        strategy: Mapping[str, Any],
        artifacts: Mapping[str, Mapping[str, Any]],
        montage_path: Path,
    ) -> dict[str, Any]:
        """Evaluate all four creative facade views in one bounded call."""


def proposal_identity(bundle: Mapping[str, Any]) -> dict[str, str]:
    identity = {
        "execution_id": str(bundle.get("execution_id") or ""),
        "program_hash": str(bundle.get("program_hash") or ""),
        "geometry_hash": str(bundle.get("geometry_hash") or ""),
    }
    if not all(identity.values()):
        raise ValueError("multi-view proposal requires complete execution identity")
    return identity


__all__ = ["FACADE_VIEWS", "MultiViewCritic", "proposal_identity"]
