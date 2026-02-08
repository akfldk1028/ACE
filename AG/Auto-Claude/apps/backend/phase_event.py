"""
Phase event facade for AG-Frontend synchronization.
Re-exports from core.phase_event for clean imports.
"""

from core.phase_event import (
    PHASE_MARKER_PREFIX,
    ExecutionPhase,
    emit_phase,
)

__all__ = [
    "PHASE_MARKER_PREFIX",
    "ExecutionPhase",
    "emit_phase",
]
