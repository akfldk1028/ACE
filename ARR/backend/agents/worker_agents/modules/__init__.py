"""GitAgent-style worker module registry."""

from __future__ import annotations

from .flight_specialist_worker.agent import FlightSpecialistWorkerAgent

__all__ = ["FlightSpecialistWorkerAgent"]
