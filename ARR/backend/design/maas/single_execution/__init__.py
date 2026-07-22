"""Fast, auditable execution boundary for exactly one MASS program."""

from .contracts import SingleMassExecutionResult
from .catalog import (
    is_single_execution_run,
    single_execution_archive_manifest,
    single_execution_passport,
    single_execution_preview,
    single_execution_program,
    single_execution_run_id,
    single_execution_runs,
)
from .pipeline import execute_single_mass

__all__ = [
    "SingleMassExecutionResult",
    "execute_single_mass",
    "is_single_execution_run",
    "single_execution_archive_manifest",
    "single_execution_passport",
    "single_execution_preview",
    "single_execution_program",
    "single_execution_run_id",
    "single_execution_runs",
]
