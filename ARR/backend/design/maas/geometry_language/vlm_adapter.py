"""Adapter from compiled geometry programs to the existing OpenAI VLM critic."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Callable

from design.maas.preference.vlm_scorer import score_candidate_with_openai_vlm

from .ast import GeometryProgram
from .base_seeds import base_seed_catalog
from .compiler import CompilationResult
from .mutation import ALLOWED_EDIT_OPERATIONS


OPERATOR_EFFECTS = {
    "box": "establish a rectilinear solid datum",
    "extruded_polygon": "establish a profiled plan extrusion",
    "translate": "move a solid without changing its topology",
    "scale": "change normalized width, depth or height proportion",
    "rotate": "change orientation about a declared pivot",
    "shear": "lean one section while retaining a continuous solid",
    "bend": "curve a continuous longitudinal solid axis",
    "taper": "change section scale along an axis",
    "twist": "rotate successive sections along an axis",
    "pinch": "contract an intermediate waist while preserving both ends",
    "inflate": "swell the middle of a continuous solid without adding fragments",
    "slice": "retain one side of a declared cutting plane",
    "clip_fraction": "select a normalized BOOK p.3 fraction of the live solid bounds",
    "cut_corner": "remove a bounded corner with a plane cut",
    "lift": "raise a dominant body over bounded structural supports",
    "puncture": "subtract a bounded array of through-openings",
    "union": "join input solids into one Boolean result",
    "difference": "subtract the second input from the first",
    "radial_array": "repeat and rotate a solid about a pivot",
    "stack": "repeat a solid across height levels",
    "courtyard": "carve an inner public or environmental void",
    "setback": "form successively reduced occupied levels",
    "split_wing": "separate wings and optionally reconnect them",
    "sweep": "carry a profile along an explicit spatial path",
    "loft": "interpolate a solid between explicit profiles",
}


def build_geometry_graph_notes(
    program: GeometryProgram,
    compilation: CompilationResult,
) -> list[dict[str, Any]]:
    """Expose agent-readable intent without making notes executable geometry."""
    trace_by_node = {str(item.get("node_id") or ""): item for item in compilation.trace}
    notes = []
    for node in program.topological_nodes():
        provenance = node.provenance if isinstance(node.provenance, dict) else {}
        trace = trace_by_node.get(node.id, {})
        notes.append({
            "node_id": node.id,
            "semantic_role": node.semantic_role or "unspecified",
            "operator": node.operator,
            "input_ids": list(node.inputs),
            "design_intent": str(
                provenance.get("rationale")
                or provenance.get("architectural_use")
                or OPERATOR_EFFECTS.get(node.operator, f"apply typed {node.operator} geometry operation")
            ),
            "expected_geometry_effect": OPERATOR_EFFECTS.get(node.operator, f"apply typed {node.operator} geometry operation"),
            "editable_parameters": sorted(node.parameters),
            "preserve": ["declared input references", "closed manifold solid", "hard-gate constraints"],
            "compiled_evidence": {
                "triangle_count": int(trace.get("triangle_count") or 0),
                "volume": float(trace.get("volume") or 0.0),
            },
            "note_is_non_executable": True,
        })
    return notes


def build_geometry_graph_snapshot(
    program: GeometryProgram,
    compilation: CompilationResult,
) -> dict[str, Any]:
    """Return the stable, machine-readable graph contract used by AI agents.

    The program AST remains authoritative.  Notes and compiled measurements are
    observation data bound to node IDs, never an alternate source of geometry.
    """
    notes = build_geometry_graph_notes(program, compilation)
    return {
        "schema_version": "arr.maas.ai_readable_geometry_graph.v1",
        "program_name": program.name,
        "root_node_id": program.root_id,
        "nodes": notes,
        "edges": [
            {
                "source_node_id": input_id,
                "target_node_id": node.id,
                "input_index": input_index,
                "relation": "solid_input",
            }
            for node in program.topological_nodes()
            for input_index, input_id in enumerate(node.inputs)
        ],
        "agent_edit_contract": {
            "authoritative_source": "geometry_program",
            "target_selector": "node_id",
            "response_field": "geometry_edits",
            "allowed_operations": sorted(ALLOWED_EDIT_OPERATIONS),
            "requires_semantic_validation": True,
            "requires_recompile_and_rerender": True,
            "requires_geometry_hash_change": True,
            "requires_hard_gate_recheck": True,
        },
        "compiled_root_evidence": {
            "status": compilation.status,
            "geometry_hash": compilation.geometry_hash,
            "triangle_count": int(compilation.metrics.get("triangle_count") or 0),
            "volume": float(compilation.metrics.get("volume") or 0.0),
        },
    }


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
            "geometry_graph_notes": build_geometry_graph_notes(program, compilation),
            "geometry_graph_snapshot": build_geometry_graph_snapshot(program, compilation),
            "base_seed_catalog": list(base_seed_catalog()),
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


__all__ = [
    "build_geometry_graph_notes",
    "build_geometry_graph_snapshot",
    "openai_vlm_geometry_critic",
    "score_geometry_program_with_openai_vlm",
]
