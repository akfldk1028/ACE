"""Fast, auditable execution boundary for exactly one MASS program."""

from .contracts import SingleMassExecutionResult
from .pipeline import execute_single_mass

__all__ = ["SingleMassExecutionResult", "execute_single_mass"]
