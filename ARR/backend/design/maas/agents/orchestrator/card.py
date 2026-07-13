"""Design orchestrator card export."""

from __future__ import annotations

from .agent import DesignOrchestratorAgent


def build_card() -> dict[str, object]:
    return DesignOrchestratorAgent().build_card()


__all__ = ["build_card"]
