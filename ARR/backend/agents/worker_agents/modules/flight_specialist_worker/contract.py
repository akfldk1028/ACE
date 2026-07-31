"""Contract metadata for the flight specialist worker module."""

from __future__ import annotations

from typing import Final


WORKER_CONTRACT: Final[dict[str, object]] = {
    "agent_id": "flight_specialist_worker",
    "worker_type": "flight-specialist",
    "runtime_class": "FlightSpecialistWorkerAgent",
    "card": "ARR/backend/agents/worker_agents/cards/flight_specialist_card.json",
    "implementation": "ARR/backend/agents/worker_agents/implementations/flight_specialist_worker.py",
    "scope": "global_reusable_worker",
    "not_scope": ["maas_legal_massing", "parking_code_review", "massdsl_geometry"],
}


__all__ = ["WORKER_CONTRACT"]
