"""Adapter from compiled geometry programs to the existing OpenAI VLM critic."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable
import uuid

from design.maas.preference.vlm_scorer import (
    DEFAULT_VLM_MODEL,
    VLM_PROMPT_CONTRACT_VERSION,
    score_candidate_with_openai_vlm,
)
from design.maas.preference.reference_corpus import (
    ReferenceItem,
    default_reference_root,
    load_reference_tree,
    match_reference_context,
)
from design.maas.program_massing.profiles import program_reference_contract

from .ast import GeometryProgram
from .base_seeds import base_seed_catalog
from .compiler import CompilationResult
from .mutation import ALLOWED_EDIT_OPERATIONS, OPERATOR_PARAMETER_CONTRACTS


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
    "profiled_hall": "compile a normalized long-span roof/section profile over the live base solid",
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
            "operator_parameter_contract": sorted(OPERATOR_PARAMETER_CONTRACTS.get(node.operator, ())),
            "protected_program_invariant": bool(
                node.operator == "profiled_hall"
                or node.semantic_role == "program_section_invariant"
                or provenance.get("program_invariant")
            ),
            "allowed_edit_operations": (
                ["set_parameter:section_family", "set_parameter:span_axis"]
                if node.operator == "profiled_hall"
                else sorted(ALLOWED_EDIT_OPERATIONS)
            ),
            "preserve": [
                "declared input references", "closed manifold solid", "hard-gate constraints",
                *( ["program section invariant"] if node.operator == "profiled_hall" else [] ),
            ],
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
    *,
    program_context: dict[str, Any] | None = None,
    reference_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the stable, machine-readable graph contract used by AI agents.

    The program AST remains authoritative.  Notes and compiled measurements are
    observation data bound to node IDs, never an alternate source of geometry.
    """
    notes = build_geometry_graph_notes(program, compilation)
    protected_node_ids = [
        str(note["node_id"])
        for note in notes
        if note.get("protected_program_invariant")
    ]
    context = dict(program_context or {})
    invariants = [
        dict(item) for item in context.get("semantic_invariants") or ()
        if isinstance(item, dict) and item.get("id")
    ]
    reference_nodes = [
        {
            "node_id": f"reference:{str(item.get('source_id') or item.get('title') or index)}",
            "node_kind": "reference_evidence",
            "source_id": str(item.get("source_id") or ""),
            "title": str(item.get("title") or ""),
            "selection_role": str(item.get("selection_role") or ""),
            "program_match_tier": str(item.get("program_match_tier") or ""),
            "reference_collection": str(item.get("reference_collection") or ""),
            "program_matched_terms": list(item.get("program_matched_terms") or ()),
            "editable": False,
        }
        for index, item in enumerate(reference_matches or ())
        if isinstance(item, dict)
    ]
    program_node_id = f"program:{str(context.get('program_id') or 'generic')}"
    context_graph = {
        "schema_version": "arr.maas.program_context_graph.v1",
        "root_node_id": program_node_id,
        "nodes": [
            {
                "node_id": program_node_id,
                "node_kind": "program_contract",
                "program_id": str(context.get("program_id") or "generic"),
                "design_intent": str(context.get("design_intent") or ""),
                "editable": False,
            },
            *[
                {
                    "node_id": f"invariant:{item['id']}",
                    "node_kind": "semantic_invariant",
                    **item,
                    "editable": False,
                }
                for item in invariants
            ],
            *reference_nodes,
        ],
        "edges": [
            *[
                {
                    "source_node_id": f"invariant:{item['id']}",
                    "target_node_id": program_node_id,
                    "relation": "required_by_program",
                }
                for item in invariants
            ],
            *[
                {
                    "source_node_id": item["node_id"],
                    "target_node_id": program_node_id,
                    "relation": "retrieved_as_program_evidence",
                }
                for item in reference_nodes
            ],
        ],
        "context_nodes_are_edit_targets": False,
    }
    return {
        "schema_version": "arr.maas.ai_readable_geometry_graph.v2",
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
            "must_preserve_program_context_graph": True,
            "protected_geometry_node_ids": protected_node_ids,
            "protected_node_rule": "never replace/remove/rewire; a new root must keep protected nodes in its ancestry",
            "operator_parameter_contracts": {
                operator: sorted(parameters)
                for operator, parameters in sorted(OPERATOR_PARAMETER_CONTRACTS.items())
            },
        },
        "program_context_graph": context_graph,
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
    outcome_memory_context: dict[str, Any] | None = None,
    building_type: str = "",
    program_context: dict[str, Any] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Ask the live critic for bounded typed AST edits, not descriptive labels."""
    context = dict(program_context or program_reference_contract(building_type))
    feature = {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "candidate_id": program.name,
            "geometry_program": program.to_dict(),
            "geometry_program_compilation": compilation.to_dict(include_mesh=False),
            "geometry_graph_notes": build_geometry_graph_notes(program, compilation),
            "program_context": context,
            "geometry_graph_snapshot": build_geometry_graph_snapshot(
                program,
                compilation,
                program_context=context,
                reference_matches=reference_matches or [],
            ),
            "base_seed_catalog": list(base_seed_catalog()),
            "geometry_language": sorted({node.operator for node in program.nodes}),
            "outcome_memory_context": outcome_memory_context or {
                "schema_version": "arr.maas.geometry_agent_neighborhood.v1",
                "observation_count": 0,
                "status": "no_prior_observation",
            },
        },
    }
    cache_path = _geometry_vlm_cache_path(
        program=program,
        compilation=compilation,
        preview_path=preview_path,
        reference_matches=reference_matches or [],
        program_context=context,
        model=model,
    )
    result: dict[str, Any] | None = None
    try:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if (
            isinstance(cached, dict)
            and cached.get("cache_schema_version") == "arr.maas.geometry_vlm_cache.v1"
            and isinstance(cached.get("concept_scores"), dict)
        ):
            result = {**cached, "cache_hit": True}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    if result is None:
        result = score_candidate_with_openai_vlm(
            feature=feature,
            image_path=preview_path,
            reference_matches=reference_matches or [],
            model=model,
        )
        result = {
            **result,
            "cache_schema_version": "arr.maas.geometry_vlm_cache.v1",
            "cache_hit": False,
        }
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
            temporary.write_text(
                json.dumps(result, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            temporary.replace(cache_path)
        except OSError:
            # A cache failure must not turn a valid live critic result into a
            # fabricated geometry failure.
            pass
    result["maas_causal_context"] = {
        "schema_version": "arr.maas.vlm_geometry_causal_context.v1",
        "reference_matches": [
            {
                key: item.get(key)
                for key in (
                    "source", "source_id", "title", "selection_role", "matched_tags", "score",
                    "program_id", "program_match_tier", "program_matched_terms",
                    "reference_collection", "program_relevance_score",
                )
                if item.get(key) not in (None, "", [])
            }
            for item in (reference_matches or [])
            if isinstance(item, dict)
        ],
        "program_context": context,
        "reference_assessments": list(result.get("reference_assessments") or ()),
        "outcome_memory": outcome_memory_context or {},
    }
    return result


def _geometry_vlm_cache_path(
    *,
    program: GeometryProgram,
    compilation: CompilationResult,
    preview_path: Path,
    reference_matches: list[dict[str, Any]],
    program_context: dict[str, Any],
    model: str | None,
) -> Path:
    """Address immutable critic evidence without storing credentials.

    Outcome-memory observations are deliberately not part of the identity:
    they guide a fresh critique but do not invalidate an already recorded
    review of the same rendered solid, program contract and references.
    Prompt-contract changes do invalidate the cache.
    """
    try:
        preview_hash = hashlib.sha256(preview_path.read_bytes()).hexdigest()
    except OSError:
        preview_hash = "missing-preview"
    payload = {
        "schema": "arr.maas.geometry_vlm_cache_key.v1",
        "prompt_contract": VLM_PROMPT_CONTRACT_VERSION,
        "model": model or os.getenv("MAAS_PREFERENCE_VLM_MODEL") or DEFAULT_VLM_MODEL,
        "program_hash": program.program_hash(),
        "geometry_hash": compilation.geometry_hash,
        "preview_hash": preview_hash,
        "program_context": program_context,
        "references": [
            {
                "source": item.get("source"),
                "source_id": item.get("source_id"),
                "local_path": item.get("local_path"),
                "reference_collection": item.get("reference_collection"),
                "program_match_tier": item.get("program_match_tier"),
            }
            for item in reference_matches
            if isinstance(item, dict)
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    key = hashlib.sha256(encoded).hexdigest()
    root = Path(os.getenv(
        "MAAS_GEOMETRY_VLM_CACHE_DIR",
        "docs/ai-session-memory/reference-corpus/geometry-vlm-cache",
    ))
    return root / f"{key}.json"


@lru_cache(maxsize=4)
def _cached_reference_items(root: str) -> tuple[ReferenceItem, ...]:
    return tuple(load_reference_tree(Path(root)))


def retrieve_geometry_reference_matches(
    program: GeometryProgram,
    *,
    building_type: str,
    explicit_matches: list[dict[str, Any]] | None = None,
    reference_root: str | Path | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve image-backed precedents from intent, never parcel coordinates."""
    root = Path(reference_root) if reference_root is not None else default_reference_root() / "archdaily"
    context = program_reference_contract(building_type)
    feature = {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "operator_family": " ".join(str(item) for item in program.metadata.get("operator_path") or ()),
            "source_signature": {
                "family": str(program.metadata.get("family") or building_type),
                "formal_principle": " ".join(str(item) for item in program.metadata.get("intent_tags") or ()),
                "primary_language": " ".join(sorted({node.operator for node in program.nodes})),
                "secondary_language": str(program.metadata.get("base_seed") or ""),
            },
        },
    }
    retrieved = match_reference_context(
        feature,
        _cached_reference_items(str(root.resolve())),
        limit=max(3, int(limit)),
        program_contract=context,
    )
    # The minimum primary evidence should come from the curated program
    # collection when it exists. Semantic matches remain useful as later
    # counterfactuals, but a generic residential "court" must not displace a
    # sports hall in the first gym references.
    retrieved = sorted(
        retrieved,
        key=lambda item: (
            str(item.get("program_match_tier") or "") == "preferred_collection",
            float(item.get("program_relevance_score") or 0.0),
            float(item.get("score") or 0.0),
        ),
        reverse=True,
    )
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    ordered = (*retrieved[:3], *(explicit_matches or []), *retrieved[3:])
    for item in ordered:
        if not isinstance(item, dict) or not (item.get("local_path") or item.get("image_url")):
            continue
        key = (
            str(item.get("source") or "explicit"),
            str(item.get("source_id") or item.get("local_path") or item.get("image_url") or item.get("title") or ""),
        )
        if not key[1] or key in seen:
            continue
        seen.add(key)
        merged.append(dict(item))
    result = merged[: max(3, int(limit))]
    minimum = int(context.get("minimum_program_specific_images") or 0)
    program_specific_count = sum(
        str(item.get("program_match_tier") or "") in {"preferred_collection", "semantic_program_match"}
        for item in result
    )
    for item in result:
        item["reference_contract"] = {
            "program_id": str(context.get("program_id") or "generic"),
            "minimum_program_specific_images": minimum,
            "program_specific_image_count": program_specific_count,
            "hard_pass": program_specific_count >= minimum,
        }
    return result


def openai_vlm_geometry_critic(
    *,
    reference_matches: list[dict[str, Any]] | None = None,
    reference_provider: Callable[[GeometryProgram], list[dict[str, Any]]] | None = None,
    memory_provider: Callable[[GeometryProgram], dict[str, Any]] | None = None,
    building_type: str = "",
    program_context: dict[str, Any] | None = None,
    model: str | None = None,
) -> Callable[[GeometryProgram, CompilationResult, Path], dict[str, Any]]:
    static_matches = list(reference_matches or [])

    def critic(program: GeometryProgram, compilation: CompilationResult, preview_path: Path) -> dict[str, Any]:
        dynamic_matches = reference_provider(program) if reference_provider is not None else []
        memory = memory_provider(program) if memory_provider is not None else {}
        return score_geometry_program_with_openai_vlm(
            program,
            compilation,
            preview_path,
            reference_matches=dynamic_matches or static_matches,
            outcome_memory_context=memory,
            building_type=building_type,
            program_context=program_context,
            model=model,
        )

    return critic


__all__ = [
    "build_geometry_graph_notes",
    "build_geometry_graph_snapshot",
    "openai_vlm_geometry_critic",
    "retrieve_geometry_reference_matches",
    "score_geometry_program_with_openai_vlm",
]
