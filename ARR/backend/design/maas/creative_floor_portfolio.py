"""Bounded pre-legal authored MASS portfolio for frontend choice graphs."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import hashlib
import json
from math import isfinite, sqrt
from typing import Any, Iterable

from .creative_family_contract import (
    CreativeRecipeResult,
)
from .creative_family_registry import (
    balanced_family_schedule,
    registered_creative_recipes,
)
from .creative_program_author import (
    CreativeAuthoredProgram,
    authored_program_result,
    normalize_authored_programs,
    posthoc_family_label,
)
from .creative_morphology import (
    GLOBAL_MORPHOLOGY_THRESHOLD,
    MORPHOLOGY_SCHEMA,
    WITHIN_FAMILY_MORPHOLOGY_THRESHOLD,
    accept_morphology,
    build_morphology_descriptor,
)
from .geometry_language.ast import GeometryNode, GeometryProgram
from .geometry_language.compiler import (
    CompilationResult,
    compile_geometry_program,
)
from .geometry_language.gate import GeometryGatePolicy, compilation_gate


CREATIVE_FLOOR_PORTFOLIO_SCHEMA = (
    "arr.maas.creative_floor_portfolio.v1"
)
STOREY_HEIGHT_M = 3.3
CAPACITY_BANDS = (
    "spatial_reserve",
    "balanced_yield",
    "brief_target",
    "maximum_target",
)
CAPACITY_TARGET_RATIOS = {
    "spatial_reserve": 0.70,
    "balanced_yield": 0.80,
    "brief_target": 0.90,
    "maximum_target": 1.00,
}
_CONNECTED_POLICY = GeometryGatePolicy(maximum_components=1)


def build_creative_floor_portfolio(
    *,
    count: int = 100,
    capacity_ceiling_m2: float = 332.322,
    authored_programs: Iterable[
        GeometryProgram | CreativeAuthoredProgram
    ] | None = None,
) -> dict[str, Any]:
    """Return a deterministic compiled choice pool with no legal approval."""

    requested_count = int(count)
    ceiling = float(capacity_ceiling_m2)
    if requested_count < 1 or requested_count > 100:
        raise ValueError("count must be between 1 and 100")
    if not isfinite(ceiling) or ceiling <= 0.0:
        raise ValueError("capacity_ceiling_m2 must be positive")

    program_hashes: set[str] = set()
    geometry_hashes: set[str] = set()
    normalized_authored_mesh_hashes: set[str] = set()
    candidates: list[dict[str, Any]] = []

    if authored_programs is None:
        schedule = balanced_family_schedule(requested_count)
        recipes_by_family = {
            recipe.family_id: recipe
            for recipe in registered_creative_recipes()
        }
        family_order = {
            recipe.family_id: index
            for index, recipe in enumerate(registered_creative_recipes())
        }
        work_items = []
        for item in schedule:
            recipe = recipes_by_family[item.family_id]
            context = item.context
            work_items.append({
                "recipe_result": recipe.builder(context),
                "family": recipe.family_id,
                "family_index": family_order[recipe.family_id],
                "variation_index": context.variation_index,
                "capacity_band": context.capacity_band,
                "author_evidence": {
                    "schema_version": (
                        "arr.maas.creative_author_evidence.v1"
                    ),
                    "source_kind": "recipe_fixture",
                    "provider": "deterministic_fixture",
                    "model": "",
                    "response_id": "",
                    "cache_hit": True,
                    "prompt_contract": "",
                },
                "diagnostic": (
                    f"family={recipe.family_id},"
                    f"recipe={recipe.recipe_id},"
                    f"variation={context.variation_index},"
                    f"book_scope={context.book_scope_label},"
                    f"capacity_band={context.capacity_band}"
                ),
            })
    else:
        authored = normalize_authored_programs(authored_programs)
        if len(authored) < requested_count:
            raise ValueError(
                "authored_programs contains fewer programs than count"
            )
        work_items = []
        for index, authored_item in enumerate(authored[:requested_count]):
            authored_compilation = compile_geometry_program(
                authored_item.program
            )
            if not _connected_compilation(authored_compilation):
                raise RuntimeError(
                    f"invalid authored creative candidate: index={index}"
                )
            family = posthoc_family_label(
                authored_item.program,
                authored_compilation,
            )
            work_items.append({
                "recipe_result": authored_program_result(authored_item),
                "family": family,
                "family_index": index,
                "variation_index": index,
                "capacity_band": CAPACITY_BANDS[
                    index % len(CAPACITY_BANDS)
                ],
                "author_evidence": dict(
                    authored_item.author_evidence
                ),
                "diagnostic": (
                    f"author=llm,index={index},family={family}"
                ),
            })

    for candidate_index, work_item in enumerate(work_items):
        recipe_result = work_item["recipe_result"]
        family = str(work_item["family"])
        candidate = _compile_candidate(
            recipe_result,
            family=family,
            source_family=str(
                recipe_result.recipe_parameters.get("source_family")
                or family
            ),
            family_index=int(work_item["family_index"]),
            variation_index=int(work_item["variation_index"]),
            candidate_index=candidate_index,
            capacity_band=str(work_item["capacity_band"]),
            capacity_ceiling_m2=ceiling,
            author_evidence=dict(work_item["author_evidence"]),
        )
        diagnostic = str(work_item["diagnostic"])
        if candidate is None:
            raise RuntimeError(
                f"invalid scheduled creative candidate: {diagnostic}"
            )
        duplicate_fields = [
            field
            for field, seen in (
                ("program_hash", program_hashes),
                ("geometry_hash", geometry_hashes),
                (
                    "normalized_authored_mesh_hash",
                    normalized_authored_mesh_hashes,
                ),
            )
            if candidate[field] in seen
        ]
        if duplicate_fields:
            raise RuntimeError(
                "duplicate scheduled creative candidate: "
                f"{diagnostic},"
                f"duplicate_fields={','.join(duplicate_fields)}"
            )
        morphology_decision = accept_morphology(candidate, candidates)
        candidate["morphology_evidence"]["decision"] = (
            morphology_decision.to_dict()
        )
        if not morphology_decision:
            raise RuntimeError(
                "morphology quota exhausted: "
                f"{diagnostic},{morphology_decision.diagnostic}"
            )
        candidates.append(candidate)
        program_hashes.add(candidate["program_hash"])
        geometry_hashes.add(candidate["geometry_hash"])
        normalized_authored_mesh_hashes.add(
            candidate["normalized_authored_mesh_hash"]
        )

    family_counts = Counter(row["family"] for row in candidates)
    capacity_counts = Counter(row["capacity_band"] for row in candidates)
    nearest_distances = [
        float(row["morphology_evidence"]["decision"]["nearest_distance"])
        for row in candidates[1:]
    ]
    return {
        "schema_version": CREATIVE_FLOOR_PORTFOLIO_SCHEMA,
        "author_mode": (
            "authored_programs"
            if authored_programs is not None
            else "recipe_fixture"
        ),
        "status": "materialized",
        "choice_pool": True,
        "candidate_count": len(candidates),
        "capacity_ceiling_m2": round(ceiling, 6),
        "capacity_authority": "user_supplied_prelegal_target",
        "family_quotas": dict(family_counts),
        "capacity_band_quotas": dict(capacity_counts),
        "legal_review_status": "not_evaluated",
        "paid_vlm_request_count": 0,
        "morphology_evidence": {
            "schema_version": MORPHOLOGY_SCHEMA,
            "decision": "accepted",
            "accepted_count": len(candidates),
            "rejected_count": 0,
            "global_threshold": GLOBAL_MORPHOLOGY_THRESHOLD,
            "within_family_threshold": (
                WITHIN_FAMILY_MORPHOLOGY_THRESHOLD
            ),
            "nearest_distance_distribution": _distance_distribution(
                nearest_distances
            ),
        },
        "candidates": candidates,
    }


def _normalized_mesh_hash(compilation: CompilationResult) -> str:
    bounds = compilation.metrics.get("bounds") or ()
    if len(bounds) != 2 or not compilation.vertices:
        return ""
    minimum, maximum = bounds
    spans = tuple(
        float(maximum[index]) - float(minimum[index])
        for index in range(3)
    )
    if any(span <= 1e-9 for span in spans):
        return ""
    vertices = [
        [
            round(
                (float(vertex[index]) - float(minimum[index]))
                / spans[index],
                8,
            )
            for index in range(3)
        ]
        for vertex in compilation.vertices
    ]
    payload = {
        "vertices": vertices,
        "triangles": [list(face) for face in compilation.triangles],
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _compile_candidate(
    recipe_result: CreativeRecipeResult,
    *,
    family: str,
    source_family: str,
    family_index: int,
    variation_index: int,
    candidate_index: int,
    capacity_band: str,
    capacity_ceiling_m2: float,
    author_evidence: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    resolved_author_evidence = author_evidence or {
        "schema_version": "arr.maas.creative_author_evidence.v1",
        "source_kind": "recipe_fixture",
        "provider": "deterministic_fixture",
        "model": "",
        "response_id": "",
        "cache_hit": True,
        "prompt_contract": "",
    }
    authored = recipe_result.program
    authored_compilation = compile_geometry_program(authored)
    if not _connected_compilation(authored_compilation):
        return None
    normalized_authored_mesh_hash = _normalized_mesh_hash(
        authored_compilation
    )
    if not normalized_authored_mesh_hash:
        return None

    storey_count = 3 + ((family_index + variation_index) % 4)
    target_height_m = storey_count * STOREY_HEIGHT_M
    target_gfa_m2 = (
        capacity_ceiling_m2 * CAPACITY_TARGET_RATIOS[capacity_band]
    )
    normalized_bounds = authored_compilation.metrics.get("bounds") or ()
    if len(normalized_bounds) != 2:
        return None
    minimum = normalized_bounds[0]
    maximum = normalized_bounds[1]
    normalized_height = float(maximum[2]) - float(minimum[2])
    if normalized_height <= 1e-9:
        return None

    normalized_floor_areas = _slice_floor_areas(
        authored_compilation,
        storey_count=storey_count,
        minimum_z=float(minimum[2]),
        height=normalized_height,
    )
    normalized_gfa = sum(normalized_floor_areas)
    if normalized_gfa <= 1e-9:
        return None
    plan_scale = sqrt(target_gfa_m2 / normalized_gfa)
    height_scale = target_height_m / normalized_height
    center_x = (float(minimum[0]) + float(maximum[0])) / 2.0
    center_y = (float(minimum[1]) + float(maximum[1])) / 2.0
    physical_matrix = (
        (plan_scale, 0.0, 0.0, -center_x * plan_scale),
        (0.0, plan_scale, 0.0, -center_y * plan_scale),
        (0.0, 0.0, height_scale, -float(minimum[2]) * height_scale),
        (0.0, 0.0, 0.0, 1.0),
    )
    physical_envelope = _with_physical_matrix(
        authored,
        matrix=physical_matrix,
        family=family,
        capacity_band=capacity_band,
        storey_count=storey_count,
        target_gfa_m2=target_gfa_m2,
    )
    envelope_compilation = compile_geometry_program(physical_envelope)
    if not _connected_compilation(envelope_compilation):
        return None
    physical_bounds = envelope_compilation.metrics.get("bounds") or ()
    if len(physical_bounds) != 2:
        return None
    physical, cutter_ids, plate_ids = _with_occupied_floor_plates(
        physical_envelope,
        bounds=physical_bounds,
        storey_count=storey_count,
    )
    compilation = compile_geometry_program(physical)
    if not _connected_compilation(compilation):
        return None
    actual_floor_areas = _slice_floor_areas(
        compilation,
        storey_count=storey_count,
        minimum_z=0.0,
        height=target_height_m,
    )
    if (
        len(actual_floor_areas) != storey_count
        or any(area <= 1e-9 for area in actual_floor_areas)
    ):
        return None

    relation_node = physical.node_map.get(recipe_result.contact_node_id)
    if relation_node is None:
        return None
    candidate_id = f"creative-{candidate_index + 1:03d}"
    elevations = [
        round(index * STOREY_HEIGHT_M, 6)
        for index in range(storey_count + 1)
    ]
    actual_gfa = sum(actual_floor_areas)
    metrics = compilation.metrics
    trace_by_node = {
        str(trace.get("node_id") or ""): trace
        for trace in compilation.trace
    }
    witness_trace = trace_by_node.get(relation_node.id) or {}
    witness_volume = float(witness_trace.get("volume") or 0.0)
    plate_volumes = tuple(
        float((trace_by_node.get(node_id) or {}).get("volume") or 0.0)
        for node_id in plate_ids
    )
    final_component_count = int(metrics.get("component_count") or 0)
    if witness_volume <= 0.0 or any(volume <= 0.0 for volume in plate_volumes):
        return None
    matrix_nodes = tuple(
        node
        for node in physical.nodes
        if node.kind == "transform" and node.operator == "matrix4"
    )
    morphology_descriptor = build_morphology_descriptor(
        vertices=compilation.vertices,
        triangles=compilation.triangles,
        floor_areas=actual_floor_areas,
        component_count=final_component_count,
        contact_topology=recipe_result.contact_type,
    )
    return {
        "candidate_id": candidate_id,
        "family": family,
        "source_family": source_family,
        "posthoc_family": posthoc_family_label(
            authored,
            authored_compilation,
        ),
        "form_class": recipe_result.form_class,
        "variation_index": variation_index,
        "capacity_band": capacity_band,
        "program_hash": physical.program_hash(),
        "geometry_hash": compilation.geometry_hash,
        "normalized_authored_mesh_hash": normalized_authored_mesh_hash,
        "geometry_program": physical.to_dict(),
        "author_evidence": resolved_author_evidence,
        "matrix4_trace": [
            {
                "node_id": node.id,
                "semantic_role": node.semantic_role,
                "matrix4": node.parameters["matrix4"],
            }
            for node in matrix_nodes
        ],
        "mesh": {
            "vertices": [list(vertex) for vertex in compilation.vertices],
            "triangles": [list(face) for face in compilation.triangles],
        },
        "mesh_evidence": {
            "connected": int(metrics.get("component_count") or 0) == 1,
            "watertight": metrics.get("watertight") is True,
            "manifold": metrics.get("manifold") is True,
            "closed_solid": metrics.get("closed_solid") is True,
            "component_count": int(metrics.get("component_count") or 0),
            "bounds": metrics.get("bounds"),
            "triangle_count": int(metrics.get("triangle_count") or 0),
        },
        "storey_evidence": {
            "schema_version": "arr.maas.creative_storey_evidence.v1",
            "storey_count": storey_count,
            "typical_storey_height_m": STOREY_HEIGHT_M,
            "floor_elevations_m": elevations,
            "floor_center_elevations_m": [
                round((index + 0.5) * STOREY_HEIGHT_M, 6)
                for index in range(storey_count)
            ],
            "actual_floor_areas_m2": [
                round(area, 6) for area in actual_floor_areas
            ],
            "actual_gfa_m2": round(actual_gfa, 6),
            "target_gfa_m2": round(target_gfa_m2, 6),
            "capacity_band": capacity_band,
            "capacity_authority": "user_supplied_prelegal_target",
            "floor_cutter_node_ids": list(cutter_ids),
            "floor_plate_node_ids": list(plate_ids),
            "floor_plate_compiled_volumes_m3": [
                round(volume, 6) for volume in plate_volumes
            ],
            "authority": "authored_prelegal_horizontal_sections",
            "legal_certified": False,
            "measurement": (
                "final_manifold_occupied_floor_plate_center_slice"
            ),
        },
        "connectivity_evidence": {
            "schema_version": "arr.maas.creative_contact_witness.v1",
            "hard_pass": True,
            "contact_type": recipe_result.contact_type,
            "witness_node_id": relation_node.id,
            "witness_operator": relation_node.operator,
            "witness_compiled_volume": round(witness_volume, 6),
            "final_component_count": final_component_count,
            "compiled_component_count": final_component_count,
            "measurement": (
                "compiler_trace_positive_volume_and_final_component_count"
            ),
        },
        "morphology_evidence": {
            "schema_version": MORPHOLOGY_SCHEMA,
            "descriptor": morphology_descriptor.to_dict(),
        },
        "legal_review": {
            "schema_version": "arr.maas.prelegal_review.v1",
            "status": "not_evaluated",
            "hard_pass": False,
            "capacity_ceiling_m2": round(capacity_ceiling_m2, 6),
            "capacity_authority": "user_supplied_prelegal_target",
            "required_authorities": [
                "neo4j_law_agent",
                "exact_geometry_gate",
            ],
        },
        "lineage": {
            "schema_version": "arr.maas.creative_lineage.v1",
            "stages": [
                *(
                    ["llm_authored_geometry_program"]
                    if resolved_author_evidence.get("source_kind")
                    == "llm_authored_geometry_program"
                    else []
                ),
                "canonical_unitbox",
                "physical_storey_capacity_matrix4",
                "typed_book_relation",
                "connected_mass",
                "storey_contract",
                "legal_review_pending",
            ],
            "unitbox_node_id": _canonical_unitbox(physical).id,
            "relation_node_id": relation_node.id,
            "physical_envelope_node_id": physical_envelope.root_id,
            "physical_root_node_id": physical.root_id,
        },
    }


def _distance_distribution(values: list[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "maximum": None,
        }
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2.0
    )
    return {
        "count": len(ordered),
        "minimum": round(ordered[0], 12),
        "median": round(median, 12),
        "maximum": round(ordered[-1], 12),
    }


def _with_physical_matrix(
    program: GeometryProgram,
    *,
    matrix: tuple[tuple[float, float, float, float], ...],
    family: str,
    capacity_band: str,
    storey_count: int,
    target_gfa_m2: float,
) -> GeometryProgram:
    node = GeometryNode(
        "creative_physical_storey_capacity_matrix4",
        "transform",
        "matrix4",
        inputs=(program.root_id,),
        parameters={"matrix4": [list(row) for row in matrix]},
        semantic_role="physical_storey_capacity_fit",
        provenance={
            "creative_family": family,
            "capacity_band": capacity_band,
            "storey_count": storey_count,
            "target_gfa_m2": round(target_gfa_m2, 6),
        },
    )
    return replace(
        program,
        nodes=(*program.nodes, node),
        root_id=node.id,
        name=f"{program.name}__creative_physical",
        metadata={
            **program.metadata,
            "creative_capacity_band": capacity_band,
            "creative_storey_count": storey_count,
            "creative_target_gfa_m2": round(target_gfa_m2, 6),
        },
    )


def _with_occupied_floor_plates(
    program: GeometryProgram,
    *,
    bounds: tuple[Any, Any] | list[Any],
    storey_count: int,
) -> tuple[GeometryProgram, tuple[str, ...], tuple[str, ...]]:
    minimum, maximum = bounds
    minimum_x, minimum_y, minimum_z = (
        float(minimum[0]),
        float(minimum[1]),
        float(minimum[2]),
    )
    maximum_x, maximum_y, maximum_z = (
        float(maximum[0]),
        float(maximum[1]),
        float(maximum[2]),
    )
    span_x = maximum_x - minimum_x
    span_y = maximum_y - minimum_y
    height = maximum_z - minimum_z
    unitbox = _canonical_unitbox(program)
    cutter_thickness = min(0.12, STOREY_HEIGHT_M * 0.04)
    margin = max(span_x, span_y, 1.0) * 0.02
    nodes = list(program.nodes)
    cutter_ids: list[str] = []
    plate_ids: list[str] = []
    for index in range(storey_count):
        center_z = minimum_z + height * (index + 0.5) / storey_count
        cutter_id = f"creative_floor_{index + 1:02d}_cutter_matrix4"
        plate_id = f"creative_floor_{index + 1:02d}_occupied_plate"
        cutter = GeometryNode(
            cutter_id,
            "transform",
            "matrix4",
            inputs=(unitbox.id,),
            parameters={
                "matrix4": [
                    [span_x + 2.0 * margin, 0.0, 0.0, minimum_x - margin],
                    [0.0, span_y + 2.0 * margin, 0.0, minimum_y - margin],
                    [
                        0.0,
                        0.0,
                        cutter_thickness,
                        center_z - cutter_thickness / 2.0,
                    ],
                    [0.0, 0.0, 0.0, 1.0],
                ],
            },
            semantic_role="occupied_floor_cutter",
            provenance={
                "authority": "canonical_unitbox",
                "storey_number": index + 1,
                "prelegal": True,
            },
        )
        plate = GeometryNode(
            plate_id,
            "boolean",
            "intersection",
            inputs=(program.root_id, cutter_id),
            semantic_role="occupied_floor_plate",
            provenance={
                "authority": "authored_prelegal_storey_contract",
                "storey_number": index + 1,
                "center_elevation_m": round(center_z, 6),
                "legal_certified": False,
            },
        )
        nodes.extend((cutter, plate))
        cutter_ids.append(cutter_id)
        plate_ids.append(plate_id)
    root = GeometryNode(
        "creative_occupied_storeys_union",
        "boolean",
        "union",
        inputs=(program.root_id, *plate_ids),
        semantic_role="connected_mass_with_occupied_floor_plates",
        provenance={
            "authority": "authored_prelegal_storey_contract",
            "floor_plate_node_ids": list(plate_ids),
            "set_identity": "host_union_subsets_equals_host",
            "legal_certified": False,
        },
    )
    nodes.append(root)
    return (
        replace(
            program,
            nodes=tuple(nodes),
            root_id=root.id,
            metadata={
                **program.metadata,
                "creative_floor_cutter_node_ids": list(cutter_ids),
                "creative_floor_plate_node_ids": list(plate_ids),
            },
        ),
        tuple(cutter_ids),
        tuple(plate_ids),
    )


def _slice_floor_areas(
    compilation: CompilationResult,
    *,
    storey_count: int,
    minimum_z: float,
    height: float,
) -> tuple[float, ...]:
    if compilation._solid is None:
        return ()
    areas: list[float] = []
    for floor_index in range(storey_count):
        z = minimum_z + height * (floor_index + 0.5) / storey_count
        try:
            area = abs(float(compilation._solid.slice(z).area()))
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return ()
        if not isfinite(area) or area <= 1e-9:
            return ()
        areas.append(area)
    return tuple(areas)


def _connected_compilation(compilation: CompilationResult) -> bool:
    return bool(
        not compilation_gate(compilation, _CONNECTED_POLICY)
        and int(compilation.metrics.get("component_count") or 0) == 1
        and compilation.metrics.get("watertight") is True
        and compilation.metrics.get("manifold") is True
    )


def _canonical_unitbox(program: GeometryProgram) -> GeometryNode:
    matches = tuple(
        node
        for node in program.nodes
        if (
            node.kind == "primitive"
            and node.operator == "box"
            and node.parameters
            == {"width": 1.0, "depth": 1.0, "height": 1.0}
        )
    )
    if len(matches) != 1:
        raise ValueError("creative program requires one canonical UnitBox")
    return matches[0]


__all__ = [
    "CAPACITY_BANDS",
    "CREATIVE_FLOOR_PORTFOLIO_SCHEMA",
    "STOREY_HEIGHT_M",
    "balanced_family_schedule",
    "build_creative_floor_portfolio",
]
