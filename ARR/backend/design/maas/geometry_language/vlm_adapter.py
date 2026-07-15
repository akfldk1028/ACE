"""Adapter from compiled geometry programs to the existing OpenAI VLM critic."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Callable

from design.maas.preference.vlm_scorer import score_candidate_with_openai_vlm

from .ast import GeometryProgram
from .compiler import CompilationResult


def score_geometry_program_with_openai_vlm(
    program: GeometryProgram,
    compilation: CompilationResult,
    preview_path: Path,
    *,
    reference_matches: list[dict[str, Any]] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Ask the live critic for bounded typed AST edits, not descriptive labels."""
    feature = {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "candidate_id": program.name,
            "geometry_program": program.to_dict(),
            "geometry_program_compilation": compilation.to_dict(include_mesh=False),
            "geometry_language": sorted({node.operator for node in program.nodes}),
        },
    }
    return score_candidate_with_openai_vlm(
        feature=feature,
        image_path=preview_path,
        reference_matches=reference_matches or [],
        model=model,
    )


def openai_vlm_geometry_critic(
    *,
    reference_matches: list[dict[str, Any]] | None = None,
    model: str | None = None,
) -> Callable[[GeometryProgram, CompilationResult, Path], dict[str, Any]]:
    return partial(
        score_geometry_program_with_openai_vlm,
        reference_matches=reference_matches or [],
        model=model,
    )


__all__ = ["openai_vlm_geometry_critic", "score_geometry_program_with_openai_vlm"]
