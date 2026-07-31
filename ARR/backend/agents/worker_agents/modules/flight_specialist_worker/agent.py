"""Flight specialist worker module entrypoint.

This is the GitAgent-style code entrypoint for the worker folder. The underlying
runtime class is re-exported from the existing implementation path to avoid
breaking Django imports while making this folder the inspectable agent unit.
"""

from __future__ import annotations

from ...implementations.flight_specialist_worker import FlightSpecialistWorkerAgent


def get_worker_class() -> type[FlightSpecialistWorkerAgent]:
    return FlightSpecialistWorkerAgent


__all__ = ["FlightSpecialistWorkerAgent", "get_worker_class"]
