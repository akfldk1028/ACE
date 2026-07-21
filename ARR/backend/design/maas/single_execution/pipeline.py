"""Execute one explicit GeometryProgram without entering portfolio search.

Generation, retrieval, paid VLM critique, and portfolio selection intentionally
live outside this boundary.  Any of those agents can hand this module one AST;
the same compiler, hard geometry gate, renderer, passport, and causal graph then
run deterministically for that one MASS.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any

from design.maas.geometry_language.ast import GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.execution_persistence import (
    passport_path_for_preview,
    write_mass_execution_passport,
)
from design.maas.geometry_language.gate import compilation_gate
from design.maas.geometry_language.render import render_compilation_preview

from .contracts import SingleMassExecutionResult
from .persistence import write_json_atomic


_SAFE_ID = re.compile(r"[^a-zA-Z0-9_-]+")


def execute_single_mass(
    program: GeometryProgram | Mapping[str, Any],
    *,
    output_root: str | Path,
    execution_id: str = "",
    title: str = "",
    downstream_evidence: Mapping[str, Any] | None = None,
    vlm_result: Mapping[str, Any] | None = None,
    geometry_graph_snapshot: Mapping[str, Any] | None = None,
) -> SingleMassExecutionResult:
    """Compile, gate, render, and persist exactly one MASS with stage timings."""

    started = perf_counter()
    timings: dict[str, float] = {}

    stage_started = perf_counter()
    resolved_program = (
        program if isinstance(program, GeometryProgram) else GeometryProgram.from_dict(dict(program))
    )
    validation_issues = tuple(resolved_program.validate())
    timings["parse_validate"] = _elapsed_ms(stage_started)

    program_hash = ""
    if not validation_issues:
        program_hash = resolved_program.program_hash()
    resolved_id = _execution_id(execution_id, resolved_program.name, program_hash)
    directory = Path(output_root).resolve() / resolved_id
    program_path = directory / "program.json"
    preview_path = directory / "mass.png"
    passport_path = passport_path_for_preview(preview_path)
    manifest_path = directory / "execution.json"

    stage_started = perf_counter()
    compilation = compile_geometry_program(resolved_program)
    timings["compile"] = _elapsed_ms(stage_started)

    stage_started = perf_counter()
    gate_issues = tuple(compilation_gate(compilation))
    timings["geometry_gate"] = _elapsed_ms(stage_started)
    geometry_ready = compilation.status == "compiled" and not gate_issues

    stage_started = perf_counter()
    if geometry_ready:
        render_compilation_preview(
            compilation,
            preview_path,
            title=title or resolved_program.name,
        )
    timings["render"] = _elapsed_ms(stage_started)

    stage_started = perf_counter()
    passport_path = write_mass_execution_passport(
        compilation,
        preview_path,
        downstream_evidence=downstream_evidence,
        vlm_result=vlm_result,
        geometry_graph_snapshot=geometry_graph_snapshot,
    )
    passport = json.loads(passport_path.read_text(encoding="utf-8"))
    timings["passport"] = _elapsed_ms(stage_started)

    stage_started = perf_counter()
    write_json_atomic(program_path, resolved_program.to_dict())
    timings["persist"] = _elapsed_ms(stage_started)
    timings["total"] = _elapsed_ms(started)

    status = (
        "geometry_ready"
        if geometry_ready
        else "geometry_gate_failed"
        if compilation.status == "compiled" and gate_issues
        else compilation.status
    )
    result = SingleMassExecutionResult(
        execution_id=resolved_id,
        status=status,
        geometry_ready=geometry_ready,
        full_flow_status=str(passport.get("status") or "in_progress"),
        program_hash=program_hash,
        geometry_hash=str(compilation.geometry_hash or ""),
        timings_ms={key: round(value, 3) for key, value in timings.items()},
        gate_issues=tuple(issue.to_dict() for issue in gate_issues),
        output_directory=directory,
        program_path=program_path,
        preview_path=preview_path,
        passport_path=passport_path,
        manifest_path=manifest_path,
        passport=passport,
    )
    write_json_atomic(manifest_path, result.to_dict())
    return result


def _execution_id(requested: str, name: str, program_hash: str) -> str:
    raw = requested.strip() or f"{name}-{program_hash[:12] or 'invalid'}"
    resolved = _SAFE_ID.sub("-", raw).strip("-_")[:96]
    return resolved or f"mass-{program_hash[:12] or 'invalid'}"


def _elapsed_ms(started: float) -> float:
    return max(0.0, (perf_counter() - started) * 1000.0)


__all__ = ["execute_single_mass"]
