"""Execute one explicit GeometryProgram without entering portfolio search.

Generation, retrieval, paid VLM critique, and portfolio selection intentionally
live outside this boundary.  Any of those agents can hand this module one AST;
the same compiler, hard geometry gate, renderer, passport, and causal graph then
run deterministically for that one MASS.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any
import uuid

from design.maas.agents.elevation_agent import generate_elevation_bundle
from design.maas.agents.orchestrator.execution_collaboration import (
    AgentExecutor,
    build_default_execution_executors,
    run_execution_collaboration,
)
from design.maas.agents.shared.types import ExecutionIdentity
from design.maas.geometry_language.ast import GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.execution_persistence import (
    passport_path_for_preview,
    write_mass_execution_passport,
)
from design.maas.geometry_language.gate import compilation_gate
from design.maas.geometry_language.render import render_compilation_preview
from design.maas.geometry_language.unitbox_normalization import normalize_unitbox_program

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
    collaboration_executors: Mapping[str, AgentExecutor] | None = None,
) -> SingleMassExecutionResult:
    """Compile, gate, render, and persist exactly one MASS with stage timings."""

    started = perf_counter()
    timings: dict[str, float] = {}

    stage_started = perf_counter()
    resolved_program = (
        program if isinstance(program, GeometryProgram) else GeometryProgram.from_dict(dict(program))
    )
    resolved_program = normalize_unitbox_program(resolved_program)
    validation_issues = tuple(resolved_program.validate())
    timings["parse_validate"] = _elapsed_ms(stage_started)

    program_hash = ""
    if not validation_issues:
        program_hash = resolved_program.program_hash()
    resolved_id = _execution_id(execution_id, resolved_program.name, program_hash)
    directory = Path(output_root).resolve() / resolved_id
    try:
        directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"single MASS execution already exists: {resolved_id}") from exc
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
    elevation_evidence: dict[str, Any] = {}
    if geometry_ready:
        try:
            elevation_evidence = generate_elevation_bundle(
                compilation,
                directory / "elevation",
                execution_id=resolved_id,
            )
        except Exception as exc:
            elevation_evidence = {
                "schema_version": "arr.elevation_agent.bundle.v1",
                "status": "failed",
                "execution_id": resolved_id,
                "program_hash": program_hash,
                "geometry_hash": str(compilation.geometry_hash or ""),
                "error": f"{type(exc).__name__}: {exc}",
                "views": [],
            }
    timings["elevation_agent"] = _elapsed_ms(stage_started)

    stage_started = perf_counter()
    normalized_downstream = dict(downstream_evidence or {})
    identity = ExecutionIdentity(
        execution_id=resolved_id,
        program_hash=program_hash or "PROGRAM_HASH_UNRESOLVED",
        geometry_hash=str(compilation.geometry_hash or "GEOMETRY_HASH_UNRESOLVED"),
        pnu=_resolve_pnu(resolved_program.metadata or {}, normalized_downstream),
    )
    executors = dict(collaboration_executors or build_default_execution_executors(
        compilation=compilation,
        geometry_gate_issues=gate_issues,
        downstream_evidence=normalized_downstream,
        program_metadata=resolved_program.metadata or {},
    ))
    collaboration = run_execution_collaboration(identity, executors=executors)
    timings["agent_collaboration"] = _elapsed_ms(stage_started)

    stage_started = perf_counter()
    passport_path = write_mass_execution_passport(
        compilation,
        preview_path,
        downstream_evidence=downstream_evidence,
        vlm_result=vlm_result,
        geometry_graph_snapshot=geometry_graph_snapshot,
        agent_collaboration=collaboration.to_dict(),
        elevation_evidence=elevation_evidence,
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
        created_at=datetime.now(timezone.utc).isoformat(),
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
    raw = requested.strip() or (
        f"mass-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{uuid.uuid4().hex[:8]}"
    )
    resolved = _SAFE_ID.sub("-", raw).strip("-_")[:96]
    return resolved or f"mass-{program_hash[:12] or 'invalid'}"


def _elapsed_ms(started: float) -> float:
    return max(0.0, (perf_counter() - started) * 1000.0)


def _resolve_pnu(metadata: Mapping[str, Any], downstream: Mapping[str, Any]) -> str:
    site = downstream.get("site")
    site = site if isinstance(site, Mapping) else {}
    metadata_site = metadata.get("site")
    metadata_site = metadata_site if isinstance(metadata_site, Mapping) else {}
    return str(
        site.get("pnu")
        or downstream.get("pnu")
        or metadata.get("pnu")
        or metadata_site.get("pnu")
        or "PNU_UNRESOLVED"
    )


__all__ = ["execute_single_mass"]
