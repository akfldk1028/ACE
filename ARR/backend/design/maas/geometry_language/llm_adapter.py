"""OpenAI LLM author for bounded architectural geometry programs."""

from __future__ import annotations

import json
import hashlib
from math import isfinite
import os
from dataclasses import replace
from pathlib import Path
import urllib.error
import urllib.request
import uuid
from typing import Any

from .ast import GeometryNode, GeometryProgram, OPERATORS_BY_KIND
from .base_seeds import BASE_SEED_SPECS
from .compiler import compile_geometry_program
from .dsl import GeometryDslError, parse_geometry_dsl, program_to_dsl
from .gate import GeometryGatePolicy, compilation_gate
from .mutation import (
    BOOLEAN_PARAMETERS,
    INTEGER_PARAMETERS,
    NUMERIC_BOUNDS,
    OPERATOR_PARAMETER_CONTRACTS,
    OPERATOR_VECTOR_LENGTHS,
    STRING_PARAMETER_VALUES,
    VECTOR_LENGTHS,
)


DEFAULT_GEOMETRY_AUTHOR_MODEL = "gpt-5.4-mini"
GEOMETRY_AUTHOR_PROMPT_CONTRACT = "arr.maas.geometry_llm_author.v25_typed_surface_shell"
MAX_AUTHOR_COMPILER_REPAIR_GENERATIONS = 3

SEMANTIC_MACRO_BASE_SEEDS: dict[str, frozenset[str]] = {
    "leaning_tower": frozenset({"tower"}),
    "tapered_tower": frozenset({"tower"}),
    "profiled_hall": frozenset({"bar", "slab", "profiled_prism"}),
    "bent_bar": frozenset({"bar", "slab", "profiled_prism"}),
    "cross_mass": frozenset({"bar", "slab", "profiled_prism"}),
    "grid_mass": frozenset({"bar"}),
    "split_wing": frozenset({"bar", "slab", "profiled_prism"}),
}

CANONICAL_OPERATOR_KIND: dict[str, str] = {
    # These names exist in both a low-level and architectural layer. The AST
    # stores one executable node, so a wrong redundant kind label must lower to
    # a deterministic compiler kind instead of becoming an unknown operator.
    "bridge": "composition",
    "cut_corner": "modifier",
}

AUTHOR_GEOMETRY_GATE_POLICY = GeometryGatePolicy(maximum_components=1)


class GeometryAuthorError(RuntimeError):
    pass


def author_geometry_programs_with_openai(
    context: dict[str, Any],
    *,
    target_count: int = 8,
    model: str | None = None,
    timeout: float = 150.0,
) -> tuple[GeometryProgram, ...]:
    """Generate explicit DSL programs; never accept prose or uncompiled labels."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise GeometryAuthorError("OPENAI_API_KEY is not set")
    count = max(1, min(20, int(target_count)))
    author_program_context = _author_validation_context(context)
    selected_model = model or os.getenv("MAAS_GEOMETRY_AUTHOR_MODEL") or DEFAULT_GEOMETRY_AUTHOR_MODEL
    cache_path = _author_cache_path(context=context, count=count, model=selected_model)
    cached = _load_author_cache(cache_path)
    if cached is not None:
        if isinstance(cached.get("compiled_programs"), list):
            programs = tuple(
                GeometryProgram.from_dict(item)
                for item in cached["compiled_programs"]
                if isinstance(item, dict)
            )
        else:
            programs = geometry_programs_from_author_payload(
                cached["payload"], expected_count=1,
            )
        return _decorate_author_programs(
            programs,
            model=str(cached.get("model") or selected_model),
            response_id=str(cached.get("response_id") or ""),
            cache_hit=True,
        )
    body = {
        "model": selected_model,
        "input": [
            {
                "role": "system",
                "content": [{
                    "type": "input_text",
                    "text": (
                        "You author executable architectural mass programs. Return deterministic assignment-only DSL, "
                        "not prose and not a completed-building coordinate template. Each candidate must have a materially "
                        "different operator-tree topology and architectural spatial idea."
                    ),
                }],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": _author_prompt(context, count)}],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "maas_geometry_program_batch",
                "strict": True,
                "schema": _author_schema(
                    count,
                    allowed_base_seeds=_allowed_author_base_seeds(context),
                    allowed_operators=_allowed_author_operators(context),
                ),
            }
        },
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GeometryAuthorError(f"geometry author request failed: {exc}") from exc
    raw_text = _response_output_text(response_data)
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GeometryAuthorError("geometry author returned invalid JSON") from exc
    response_id = str(response_data.get("id") or "")
    parse_error: GeometryAuthorError | None = None
    try:
        initial_programs = geometry_programs_from_author_payload(
            payload,
            expected_count=1,
            program_context=author_program_context,
        )
    except GeometryAuthorError as exc:
        initial_programs = ()
        parse_error = exc
    programs = list(_decorate_author_programs(
        initial_programs,
        model=selected_model,
        response_id=response_id,
        cache_hit=False,
    ))
    repair_generation = int(context.get("author_compiler_repair_generation") or 0)
    programs = [replace(program, metadata={
        **program.metadata,
        "author_compiler_repair_generation": repair_generation,
    }) for program in programs]
    repair_diagnostics = _author_payload_compiler_diagnostics(
        payload,
        program_context=author_program_context,
    )
    if (
        len(programs) < count
        and repair_generation < MAX_AUTHOR_COMPILER_REPAIR_GENERATIONS
    ):
        repair_context = {
            **context,
            "author_compiler_repair_generation": repair_generation + 1,
            "compiler_repair_feedback": repair_diagnostics,
            "already_valid_programs": [
                {
                    "name": program.name,
                    "base_seed": str(program.metadata.get("base_seed") or ""),
                    "operator_path": list(program.metadata.get("operator_path") or ()),
                }
                for program in programs
            ],
            "instruction": (
                "Author only the missing valid programs. Use the compiler feedback as negative constraints; "
                "do not repeat invalid node-kind/operator pairs, degenerate relations, or invalid parameter types."
            ),
        }
        try:
            repaired = author_geometry_programs_with_openai(
                repair_context,
                target_count=count - len(programs),
                model=selected_model,
                timeout=timeout,
            )
        except GeometryAuthorError:
            repaired = ()
        seen_hashes = {program.program_hash() for program in programs}
        for program in repaired:
            if program.program_hash() in seen_hashes:
                continue
            seen_hashes.add(program.program_hash())
            programs.append(program)
    if not programs:
        exc = parse_error or GeometryAuthorError("geometry author and compiler repair yielded no valid programs")
        _save_author_cache(cache_path.with_suffix(".rejected.json"), {
            "cache_schema_version": "arr.maas.geometry_llm_author_cache.v3",
            "validation_status": "rejected",
            "validation_error": str(exc)[:2000],
            "model": selected_model,
            "response_id": response_id,
            "payload": payload,
            "compiler_repair_feedback": repair_diagnostics,
        })
        raise exc
    _save_author_cache(cache_path, {
        "cache_schema_version": "arr.maas.geometry_llm_author_cache.v3",
        "validation_status": "accepted",
        "model": selected_model,
        "response_id": response_id,
        "payload": payload,
        "compiled_programs": [program.to_dict() for program in programs],
        "compiler_repair_feedback": repair_diagnostics,
        "compiler_repair_generation_count": max((
            int(program.metadata.get("author_compiler_repair_generation") or 0)
            for program in programs
        ), default=0),
    })
    return tuple(programs)


def _decorate_author_programs(
    programs: tuple[GeometryProgram, ...] | list[GeometryProgram],
    *,
    model: str,
    response_id: str,
    cache_hit: bool,
) -> tuple[GeometryProgram, ...]:
    return tuple(replace(program, metadata={
        **program.metadata,
        "author_provider": "openai_llm_geometry_author",
        "author_model": model,
        "author_response_id": response_id or str(program.metadata.get("author_response_id") or ""),
        "author_cache_hit": bool(cache_hit),
        "author_prompt_contract": GEOMETRY_AUTHOR_PROMPT_CONTRACT,
    }) for program in programs)


def _author_payload_compiler_diagnostics(
    payload: dict[str, Any],
    *,
    program_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("programs") or ()):
        if not isinstance(item, dict):
            continue
        try:
            program = _program_from_structured_author_item(item, index=index)
            program = _canonicalize_program_relation_suffix(program)
            compilation = compile_geometry_program(program)
            issues = tuple(
                compilation.issues
                or compilation_gate(compilation, AUTHOR_GEOMETRY_GATE_POLICY)
            )
            inferred_seed = _infer_base_seed(program)
            incompatible_macro = next((
                node.operator
                for node in program.topological_nodes()
                if node.operator in SEMANTIC_MACRO_BASE_SEEDS
                and inferred_seed not in SEMANTIC_MACRO_BASE_SEEDS[node.operator]
            ), "")
            nonterminal_relation = _nonterminal_program_relation(program)
            access_relation_issue = _misaligned_access_relation(program, program_context or {})
            language_contract_issue = _program_language_contract_issue(program, program_context or {})
            if (
                compilation.status == "compiled"
                and not issues
                and not incompatible_macro
                and not nonterminal_relation
                and not access_relation_issue
                and not language_contract_issue
            ):
                continue
            issue_records = [
                {"code": issue.code, "node_id": issue.node_id, "message": issue.message[:240]}
                for issue in issues[:6]
            ]
            if incompatible_macro:
                issue_records.append({
                    "code": "semantic_macro_base_seed_mismatch",
                    "node_id": "",
                    "message": f"{incompatible_macro} is incompatible with {inferred_seed} base seed",
                })
            if nonterminal_relation:
                issue_records.append({
                    "code": "program_relation_not_terminal_suffix",
                    "node_id": nonterminal_relation.split(",", 1)[0],
                    "message": (
                        "public threshold/court/entry relations must follow body transforms; "
                        f"nonterminal nodes: {nonterminal_relation}"
                    ),
                })
            if access_relation_issue:
                issue_records.append({
                    "code": "program_access_relation_not_bound",
                    "node_id": access_relation_issue.split(":", 1)[0],
                    "message": access_relation_issue,
                })
            if language_contract_issue:
                issue_records.append({
                    "code": "program_geometry_language_contract_failed",
                    "node_id": language_contract_issue.split(":", 1)[0],
                    "message": language_contract_issue,
                })
            diagnostics.append({
                "candidate_name": str(item.get("name") or f"candidate-{index + 1}"),
                "declared_base_seed": str(item.get("base_seed") or ""),
                "inferred_base_seed": inferred_seed,
                "compile_status": compilation.status,
                "issues": issue_records,
                "repair_contract": "return a new typed AST; do not return prose or patch text",
            })
        except (GeometryDslError, TypeError, ValueError, json.JSONDecodeError) as exc:
            diagnostics.append({
                "candidate_name": str(item.get("name") or f"candidate-{index + 1}"),
                "compile_status": "decode_failed",
                "issues": [{"code": type(exc).__name__, "node_id": "", "message": str(exc)[:240]}],
                "repair_contract": "return a new typed AST; do not return prose or patch text",
            })
    return diagnostics


def geometry_programs_from_author_payload(
    payload: dict[str, Any],
    *,
    expected_count: int | None = None,
    program_context: dict[str, Any] | None = None,
) -> tuple[GeometryProgram, ...]:
    programs: list[GeometryProgram] = []
    seen_hashes: set[str] = set()
    rejected: list[str] = []
    for index, item in enumerate(payload.get("programs") or []):
        if not isinstance(item, dict):
            continue
        try:
            if isinstance(item.get("nodes"), list):
                program = _program_from_structured_author_item(item, index=index)
            else:
                # v4 cache/test compatibility. Live v5 responses are typed
                # node graphs and never rely on a free-form DSL string.
                program = parse_geometry_dsl(
                    str(item.get("dsl") or ""),
                    name=str(item.get("name") or f"llm_geometry_{index + 1:02d}"),
                )
            program = _canonicalize_program_relation_suffix(program)
        except (GeometryDslError, TypeError, ValueError, json.JSONDecodeError) as exc:
            rejected.append(f"{index + 1}:{exc}")
            continue
        compilation = compile_geometry_program(program)
        gate_issues = compilation_gate(compilation, AUTHOR_GEOMETRY_GATE_POLICY)
        if compilation.status != "compiled" or gate_issues:
            reason = (
                compilation.status
                if compilation.status != "compiled"
                else ",".join(issue.code for issue in gate_issues[:4])
            )
            rejected.append(f"{index + 1}:compile_or_clean_gate:{reason}")
            continue
        known_seeds = {spec.seed_id for spec in BASE_SEED_SPECS}
        declared_seed = str(item.get("base_seed") or "").strip().lower()
        inferred_seed = _infer_base_seed(program)
        if declared_seed in known_seeds and declared_seed != inferred_seed:
            rejected.append(
                f"{index + 1}:declared_base_seed_{declared_seed}_does_not_match_{inferred_seed}"
            )
            continue
        base_seed = inferred_seed
        incompatible_macro = next((
            node.operator
            for node in program.topological_nodes()
            if node.operator in SEMANTIC_MACRO_BASE_SEEDS
            and base_seed not in SEMANTIC_MACRO_BASE_SEEDS[node.operator]
        ), "")
        if incompatible_macro:
            rejected.append(
                f"{index + 1}:semantic_macro_{incompatible_macro}_incompatible_with_{base_seed}_seed"
            )
            continue
        nonterminal_relation = _nonterminal_program_relation(program)
        if nonterminal_relation:
            rejected.append(
                f"{index + 1}:program_relation_must_be_terminal_suffix:{nonterminal_relation}"
            )
            continue
        access_relation_issue = _misaligned_access_relation(program, program_context or {})
        if access_relation_issue:
            rejected.append(f"{index + 1}:program_access_relation_not_bound:{access_relation_issue}")
            continue
        language_contract_issue = _program_language_contract_issue(program, program_context or {})
        if language_contract_issue:
            rejected.append(
                f"{index + 1}:program_geometry_language_contract_failed:{language_contract_issue}"
            )
            continue
        base_seed_controller_id = _base_seed_controller_id(program, base_seed)
        if base_seed_controller_id:
            program = program.with_nodes(
                replace(node, semantic_role="base_seed")
                if node.id == base_seed_controller_id
                else node
                for node in program.nodes
            )
        program = program.with_nodes(
            replace(node, provenance={
                **(node.provenance or {}),
                "program_invariant": True,
                "program_invariant_kind": (
                    "section" if node.operator == "profiled_hall" else "access_relation"
                ),
            })
            if _is_program_relation_node(node)
            else node
            for node in program.nodes
        )
        operator_path = [
            node.operator for node in program.topological_nodes()
            if node.kind != "primitive" and node.semantic_role != "base_seed"
        ]
        program = replace(program, metadata={
            **program.metadata,
            "language_layer": "llm_authored_recursive_geometry",
            "family": "llm_" + ("_".join(operator_path) if operator_path else "prismatic"),
            "base_seed": base_seed,
            "intent_tags": [str(value) for value in item.get("intent_tags") or ()][:12],
            "operator_path": operator_path or ["prismatic"],
            "author_provider": "structured_geometry_dsl_payload",
            "parcel_coordinates_in_program": False,
            "completed_building_template": False,
            "author_representation": (
                "typed_json_ast" if isinstance(item.get("nodes"), list) else "legacy_dsl"
            ),
            "canonical_dsl": program_to_dsl(program),
        })
        program_hash = program.program_hash()
        if program_hash in seen_hashes:
            rejected.append(f"{index + 1}:duplicate_program")
            continue
        seen_hashes.add(program_hash)
        programs.append(program)
    minimum = max(1, int(expected_count or 1))
    if len(programs) < minimum:
        raise GeometryAuthorError(
            f"geometry author yielded {len(programs)}/{minimum} valid unique programs"
            + (f" ({'; '.join(rejected[:5])})" if rejected else "")
        )
    input_count = len(payload.get("programs") or ())
    return tuple(replace(program, metadata={
        **program.metadata,
        "author_batch_requested_count": input_count,
        "author_batch_valid_count": len(programs),
        "author_batch_rejected_count": max(0, input_count - len(programs)),
    }) for program in programs)


def _program_from_structured_author_item(item: dict[str, Any], *, index: int) -> GeometryProgram:
    """Decode the strict Responses schema directly into a typed AST.

    Parameter values are discriminated JSON fields. This removes the v4
    failure mode where the outer response was valid JSON but its embedded DSL
    string contained variable-valued parameters or other non-literals.
    """
    raw_nodes = [raw for raw in item.get("nodes") or () if isinstance(raw, dict)]
    identity_aliases: dict[str, str] = {}
    kind_corrections: list[dict[str, str]] = []
    parameter_type_corrections: list[dict[str, str]] = []
    for raw in raw_nodes:
        inputs = [str(value) for value in raw.get("inputs") or ()]
        if (
            str(raw.get("operator") or "") in {"union", "intersection"}
            and len(inputs) == 1
            and not (raw.get("parameters") or ())
        ):
            identity_aliases[str(raw.get("id") or "")] = inputs[0]

    def resolve_alias(node_id: str) -> str:
        visited: set[str] = set()
        while node_id in identity_aliases and node_id not in visited:
            visited.add(node_id)
            node_id = identity_aliases[node_id]
        return node_id

    for raw in raw_nodes:
        operator = str(raw.get("operator") or "")
        inputs = [resolve_alias(str(value)) for value in raw.get("inputs") or ()]
        if operator in {
            "union", "difference", "intersection", "attach", "bridge", "attach_volume",
        } and len(inputs) > 1 and len(set(inputs)) != len(inputs):
            node_id = str(raw.get("id") or "")
            raise ValueError(
                f"{node_id}:{operator}:composition inputs must reference distinct earlier solids"
            )

    nodes: list[GeometryNode] = []
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise TypeError("structured author node must be an object")
        if str(raw.get("id") or "") in identity_aliases:
            continue
        operator = str(raw.get("operator") or "")
        allowed_parameters = OPERATOR_PARAMETER_CONTRACTS.get(operator)
        if allowed_parameters is None:
            raise ValueError(
                f"unsupported structured author operator {operator}"
            )
        raw_kind = str(raw.get("kind") or "")
        compatible_kinds = [
            kind for kind, operators in OPERATORS_BY_KIND.items()
            if operator in operators
        ]
        kind = raw_kind
        if raw_kind not in compatible_kinds and (
            len(compatible_kinds) == 1 or operator in CANONICAL_OPERATOR_KIND
        ):
            kind = CANONICAL_OPERATOR_KIND.get(operator, compatible_kinds[0])
            kind_corrections.append({
                "node_id": str(raw.get("id") or ""),
                "declared_kind": raw_kind,
                "contract_kind": kind,
                "operator": operator,
            })
        parameters: dict[str, Any] = {}
        for parameter in raw.get("parameters") or ():
            if not isinstance(parameter, dict):
                raise TypeError("structured author parameter must be an object")
            name = str(parameter.get("name") or "").strip()
            if not name:
                raise ValueError("structured author parameter name is required")
            if name not in allowed_parameters:
                raise ValueError(
                    "unsupported structured author parameter "
                    f"{operator}.{name}"
                )
            declared_value_type = str(parameter.get("value_type") or "")
            value_contract = _author_parameter_value_contract(operator, name)
            contract_type = str(value_contract.get("type") or "")
            value_type = {
                "numeric_vector": "vector",
                "structured_literal": "structured_json",
                "literal": declared_value_type,
            }.get(contract_type, contract_type)
            if value_type not in {"number", "string", "boolean", "vector", "structured_json"}:
                value_type = declared_value_type
            if value_type != declared_value_type:
                parameter_type_corrections.append({
                    "node_id": str(raw.get("id") or ""),
                    "operator": operator,
                    "parameter": name,
                    "declared_value_type": declared_value_type,
                    "contract_value_type": value_type,
                })
            if value_type == "number":
                value: Any = float(parameter.get("numeric_value") or 0.0)
            elif value_type == "string":
                value = str(parameter.get("string_value") or "")
            elif value_type == "boolean":
                value = bool(parameter.get("boolean_value"))
            elif value_type == "vector":
                value = [float(component) for component in parameter.get("vector_value") or ()]
            elif value_type == "structured_json":
                value = json.loads(str(parameter.get("structured_json") or "null"))
            else:
                raise ValueError(f"unsupported structured parameter value_type {value_type}")
            _validate_structured_author_parameter_value(
                operator,
                name,
                value,
                value_contract,
            )
            if (
                contract_type == "number"
                and bool(value_contract.get("integer"))
            ):
                value = int(float(value))
            parameters[name] = value
        nodes.append(GeometryNode(
            id=str(raw.get("id") or ""),
            kind=kind,
            operator=operator,
            inputs=tuple(resolve_alias(str(value)) for value in raw.get("inputs") or ()),
            parameters=parameters,
            semantic_role=str(raw.get("semantic_role") or ""),
            provenance={
                "source": "openai_llm_geometry_author",
                "representation": "typed_json_ast",
            },
        ))
    return GeometryProgram(
        nodes=tuple(nodes),
        root_id=resolve_alias(str(item.get("root_id") or "")),
        name=str(item.get("name") or f"llm_geometry_{index + 1:02d}"),
        metadata={
            "authored_structured_ast": True,
            "canonicalized_identity_boolean_node_ids": sorted(identity_aliases),
            "contract_lowered_node_kind_corrections": kind_corrections,
            "contract_lowered_parameter_type_corrections": parameter_type_corrections,
        },
    )


def _author_prompt(context: dict[str, Any], count: int) -> str:
    # Source-level graph memory is already bounded and coordinate-free. Keep
    # enough room for transferable post-BOOK repair priors; the previous 12k
    # cut could silently drop the final keys after successful genotype priors.
    context_text = json.dumps(context, ensure_ascii=False, sort_keys=True)[:24000]
    parameter_contracts = json.dumps({
        operator: {
            parameter: _author_parameter_value_contract(operator, parameter)
            for parameter in sorted(parameters)
        }
        for operator, parameters in sorted(OPERATOR_PARAMETER_CONTRACTS.items())
    }, ensure_ascii=False, sort_keys=True)
    allowed_base_seeds = ", ".join(_allowed_author_base_seeds(context))
    allowed_macro_operators = ", ".join(_allowed_author_macro_operators(context))
    program_context = (
        context.get("program_context")
        if isinstance(context.get("program_context"), dict)
        else {}
    )
    semantic_invariants = [
        item
        for item in program_context.get("semantic_invariants") or ()
        if isinstance(item, dict)
    ]
    program_role_vocabulary = sorted({
        str(item.get(key) or "").strip()
        for item in semantic_invariants
        for key in ("subject_role", "object_role")
        if str(item.get(key) or "").strip()
    })
    role_vocabulary_text = ", ".join(program_role_vocabulary) or (
        "dominant_mass, public_threshold, program_space"
    )
    program_id = str(
        program_context.get("program_id")
        or context.get("building_type")
        or "program"
    )
    return f"""Create exactly {count} executable and materially different architectural mass programs as typed AST node graphs.

If mass_execution_agent_context is present, it is the measured causal trace from a prior candidate: preserve
successful active relations, repair failed_stages, never assume pending_required_stages passed, and target only
exact editable_ast_nodes that remain valid in the current program contract. It is not hidden-neuron evidence.

Use the response schema's nodes array. Nodes are ordered acyclic SSA: every input id must refer to an earlier node,
and root_id must reference the final intended solid. Encode every parameter through one discriminated value_type:
number, string, boolean, vector, or structured_json. Unused value fields stay at their schema defaults.
Do not create a one-input union/intersection merely to name result; root_id may point directly to the last meaningful node.
Example concept (the schema, not prose, is authoritative): unit box -> scale vector [2.2,1.45,0.28]
-> bend axis x, angle_degrees 28, subdivisions 4 -> courtyard margin_ratio 0.28, open_side matching access.

Allowed primitives: box, cylinder, extruded_polygon, wedge, sweep, loft.
Allowed transforms: matrix4, translate/move, rotate, scale, mirror, shear.
Allowed modifiers: bend, taper, twist, pinch, inflate, slice, clip, clip_fraction, cut_corner,
circularize, profile_sweep_3d.
Allowed booleans: union, subtract/difference, intersection.
Allowed patterns: duplicate, linear_array, radial_array, mirror_array, stack, matrix_array.
Allowed compositions: attach, bridge.
Allowed surface constructors: section_surface, loft_surface, host_face_surface.
Allowed surface-to-solid conversion: shell_thicken.
Program-conditioned allowed macros: {allowed_macro_operators}.

Rules:
- Every node is one typed function call; parameters are explicit typed JSON values.
- A prior node can be reused; input references must remain acyclic.
- Surface nodes are typed intermediate values, never roots. Every surface path must end in shell_thicken,
  and only the resulting positive-thickness closed solid may be root_id. Zero-thickness planes are forbidden.
- Surface controls and thickness ratios are normalized to the current live BaseVolume bounds, never copied
  parcel coordinates. shell_thicken does not bypass the unchanged connected, watertight and manifold gate.
- Named buildings and precedents are capability evidence only, never output recipes, operators, requested
  silhouettes or permission to claim that a generated shell is occupiable.
- semantic_role must name the architectural job carried by that executable node, using program_context
  semantic-invariant roles where applicable. The current program is {program_id}; its role vocabulary is:
  {role_vocabulary_text}. Do not borrow hall, gallery, tower, roof-section, or other roles from another program
  profile. Labels never substitute for geometry: the named role must be supported by
  that node's operator, ancestry and visible relation in the compiled solid.
- root_id may point directly to the final meaningful body or access-relation node. Never append a fake result,
  hall, bridge, lift, union or attach node merely to rename the solid or give it a terminal semantic label.
  `profiled_hall` and hall/roof-section roles are valid only when profiled_hall appears in the program-conditioned
  allowed macro list and the program semantic invariants require a long-span hall.
- Program public-threshold/court/entry nodes are terminal invariants: place courtyard, carve_void, notch, lift,
  cantilever or split_wing nodes with threshold/public/court/entry semantic roles after all body transforms and
  modifiers. A required profiled_hall section comes last. The BOOK compiler inserts its body mutations before
  this suffix so later transforms cannot erase or rotate the verified access relation.
- All body shaping, cut_corner, taper, bend, array, union, attach and bridge work must precede that terminal
  access suffix. If more than one public relation is used, they must form one unary ancestry chain; never put a
  public court/entry on a parallel branch and never transform, cut, union or attach after it.
- When program_context.site_access_side_in_program_frame is east/west/north/south, every public courtyard or
  carve_void must explicitly set open_side to that side, and every entry/public notch must explicitly set side to
  that side. An access-bound lift or split_wing must set access_side to that same side. A corner label alone is not
  an access binding. Use open_side="closed" only for a node whose semantic
  role is explicitly an internal environmental court, not the public threshold.
- Use bounded local normalized dimensions, not parcel coordinates and not a copied famous building.
- Keep parcel scope and base seed separate. Scope is supplied by the site graph. Select a normalized
  base seed only from this program-profile allow-list: {allowed_base_seeds}. BLOCK is [1,1,1],
  SLAB is [2.2,1.45,0.28], BAR is [2.8,0.62,0.48], and TOWER is [0.68,0.68,2.5], all made
  by scaling the same UnitBox; PROFILED PRISM uses an explicit extruded_polygon. Never introduce
  a base seed omitted from the allow-list even if it exists in the global language.
- Do not produce parameter-only variants. Vary tree structure, topology, void/section/roof/composition language.
- Use at most {_author_body_rule_budget(context)} dominant body rules, from distinct
  effect families, plus exactly one access-bound court/carve/notch threshold when the program requires one.
  This is the same cross-layer budget applied after BOOK projection; do not stack courtyard+notch or
  carve_void+notch merely to make the graph look more detailed.
- For this request, BODY RULE BUDGET = {_author_body_rule_budget(context)} and PUBLIC ACCESS RULE BUDGET = 1.
  Count executable operators, not rationale words. A typical valid chain is normalized base seed -> one BODY rule
  -> one ACCESS rule -> root_id. Do not add a second bend/setback/terrace/cut/array/composition body rule and do not
  stack courtyard+notch, carve_void+lift, or lift+notch. The compiler rejects the whole candidate when either count
  is exceeded; extra nodes are not extra design quality.
- The compiled author mesh must be one connected solid. Split/array/duplicate wings require an explicit physical
  bridge, spine or overlapping union; disconnected Lego pieces are invalid. The later architectural source may
  expose at most five legible volume bands, but that is not permission for disconnected author geometry.
- Cantilever is a horizontal backspan relation, so its vector z component must be 0. Use lift as a separate
  terminal relation when vertical clearance is intended.
- Use a stable final node id such as result and set root_id to it.
- Use only the executable parameter names in this compiler contract; an unknown or decorative parameter is rejected:
  {parameter_contracts}
- vector3 means a literal such as [0.04, 0, 0], never a scalar. Corner values are ne/nw/se/sw.
- setback/terrace/stepped_mass direction is x or y, never z. A composition bridge takes two prior solids.
- Every boolean/composition input must reference a distinct prior solid. `bridge(A, A)`, `attach(A, A)` and
  `union(A, A)` are invalid. A split_wing is already one relational solid: either use ground_spine=true or create
  two genuinely distinct transformed branches before bridge; never bridge the split_wing node to itself.
- Macro inputs are semantically typed: leaning_tower/tapered_tower require a TOWER seed; profiled_hall,
  bent_bar, cross_mass and split_wing require BAR, SLAB, or PROFILED PRISM. Prefer BAR for cross_mass,
  split_wing and bent_bar when it is available so the relation reads as long architectural wings instead
  of rotated or separated cube fragments. To make an oblique block, use shear, rotate, cantilever,
  cut_corner, or another compatible operator instead of mislabelling it as a tower or wing system.
- Never follow cross_mass, radial_array, or split_wing with an access-bound open courtyard/carve_void.
  Cutting an already repeated footprint through one edge produces separated toy fragments. split_wing must
  carry its own access_side; cross_mass should use one access-bound lift or a shallow side notch instead.
- Read outcome_graph_memory causally. Successful genotype operator paths are reusable relation priors,
  not completed-form templates. common_authored_body_failures are hard negative evidence for the new body.
  conditional_book_projection_failures identify relations the new body must make legible before projection.
- Do not repeat a topology associated with frequent final VLM failure merely because it compiles. For example,
  when the measured memory reports repeated box-like, pyramidal, fragmented, weak-threshold, or wrong-typology
  failures, choose a materially different tree and explicitly resolve that relation. A topology with zero
  visually verified projections is not a positive precedent.
- outcome_graph_memory.portfolio_visual_feedback is the board-level sibling verdict. Treat repeated_family_groups
  as a batch-level negative constraint and distribute new tree topologies toward required_next_relations; it is not
  permission to reject an otherwise valid individual without compiling and rendering the new portfolio.
- Read reference_vlm_language before authoring. It contains only VLM-audited whole-building traits from
  program-compatible precedent images. Translate those traits into relations and executable operators; never
  copy one reference's completed silhouette, dimensions, or coordinates. If its hard_pass is false, do not
  invent precedent evidence and rely on the program semantic invariants instead.
- Across the requested batch, distribute primary ideas across continuous deformation, carved void, wing/court,
  sectional profile, overlap/bridge, and oblique cut where the program context permits. Do not let setback,
  terrace, roof pitch, or any single macro dominate the batch.

Program/site context:
{context_text}
"""


def _allowed_author_base_seeds(context: dict[str, Any]) -> list[str]:
    known = {spec.seed_id for spec in BASE_SEED_SPECS}
    requested = [
        str(value).strip().lower()
        for value in context.get("base_seeds") or ()
        if str(value).strip().lower() in known
    ]
    return list(dict.fromkeys(requested)) or [spec.seed_id for spec in BASE_SEED_SPECS]


def _geometry_language_contract(context: dict[str, Any]) -> dict[str, Any]:
    program_context = context.get("program_context")
    if not isinstance(program_context, dict):
        return {}
    contract = program_context.get("geometry_language_contract")
    return dict(contract) if isinstance(contract, dict) else {}


def _allowed_author_macro_operators(context: dict[str, Any]) -> list[str]:
    known = set(OPERATORS_BY_KIND["macro"])
    requested = [
        str(value).strip().lower()
        for value in _geometry_language_contract(context).get("allowed_macro_operators") or ()
        if str(value).strip().lower() in known
    ]
    return list(dict.fromkeys(requested)) or sorted(known)


def _allowed_author_operators(context: dict[str, Any]) -> list[str]:
    core = {
        operator
        for kind, values in OPERATORS_BY_KIND.items()
        if kind != "macro"
        for operator in values
    }
    return sorted(core | set(_allowed_author_macro_operators(context)))


def _author_schema(
    count: int,
    *,
    allowed_base_seeds: list[str] | tuple[str, ...] | None = None,
    allowed_operators: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    operators = list(allowed_operators or sorted({
        operator
        for values in OPERATORS_BY_KIND.values()
        for operator in values
    }))
    node_schema = _author_node_schema(operators)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["programs"],
        "properties": {
            "programs": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "name", "base_seed", "intent_tags", "nodes", "root_id", "rationale",
                    ],
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 120},
                        "base_seed": {
                            "enum": list(allowed_base_seeds or [spec.seed_id for spec in BASE_SEED_SPECS]),
                        },
                        "intent_tags": {
                            "type": "array",
                            "maxItems": 12,
                            "items": {"type": "string", "maxLength": 80},
                        },
                        "nodes": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 24,
                            "items": node_schema,
                        },
                        "root_id": {"type": "string", "minLength": 1, "maxLength": 80},
                        "rationale": {"type": "string", "maxLength": 600},
                    },
                },
            }
        },
    }


def _author_node_schema(allowed_operators: list[str]) -> dict[str, Any]:
    """Return an arity-discriminated strict schema for executable AST nodes.

    A single unconstrained ``inputs`` array let the author emit syntactically
    valid JSON that could never be a GeometryNode (most often ``union(A)`` or
    ``bridge(A, A)``).  Arity is part of the language type, so enforce it at
    generation time rather than spending compiler-repair turns rediscovering
    it. Distinct-input semantics are checked while decoding because JSON Schema
    cannot express uniqueness after ID-alias resolution.
    """

    parameter_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "name", "value_type", "numeric_value", "string_value",
            "boolean_value", "vector_value", "structured_json",
        ],
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 80},
            "value_type": {
                "enum": ["number", "string", "boolean", "vector", "structured_json"],
            },
            "numeric_value": {"type": "number"},
            "string_value": {"type": "string", "maxLength": 200},
            "boolean_value": {"type": "boolean"},
            "vector_value": {
                "type": "array",
                "maxItems": 48,
                "items": {"type": "number"},
            },
            "structured_json": {"type": "string", "maxLength": 4000},
        },
    }

    allowed = set(allowed_operators)

    def variant(
        kind: str,
        operators: set[str] | frozenset[str],
        *,
        minimum_inputs: int,
        maximum_inputs: int,
    ) -> dict[str, Any] | None:
        available = sorted(set(operators) & allowed)
        if not available:
            return None
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "kind", "operator", "inputs", "parameters", "semantic_role"],
            "properties": {
                "id": {"type": "string", "minLength": 1, "maxLength": 80},
                "kind": {"enum": [kind]},
                "operator": {"enum": available},
                "inputs": {
                    "type": "array",
                    "minItems": minimum_inputs,
                    "maxItems": maximum_inputs,
                    "items": {"type": "string", "minLength": 1, "maxLength": 80},
                },
                "parameters": {
                    "type": "array",
                    "maxItems": 20,
                    "items": parameter_schema,
                },
                "semantic_role": {"type": "string", "maxLength": 80},
            },
        }

    variants = [
        variant("primitive", OPERATORS_BY_KIND["primitive"], minimum_inputs=0, maximum_inputs=0),
        variant("transform", OPERATORS_BY_KIND["transform"], minimum_inputs=1, maximum_inputs=1),
        variant("modifier", OPERATORS_BY_KIND["modifier"], minimum_inputs=1, maximum_inputs=1),
        variant("pattern", OPERATORS_BY_KIND["pattern"], minimum_inputs=1, maximum_inputs=1),
        variant("surface", OPERATORS_BY_KIND["surface"], minimum_inputs=1, maximum_inputs=1),
        variant("conversion", OPERATORS_BY_KIND["conversion"], minimum_inputs=1, maximum_inputs=1),
        variant("boolean", {"difference"}, minimum_inputs=2, maximum_inputs=2),
        variant("boolean", {"union", "intersection"}, minimum_inputs=2, maximum_inputs=4),
        variant("composition", {"attach"}, minimum_inputs=2, maximum_inputs=4),
        variant("composition", {"bridge"}, minimum_inputs=2, maximum_inputs=2),
        variant("macro", set(OPERATORS_BY_KIND["macro"]) - {"bridge"}, minimum_inputs=1, maximum_inputs=4),
        variant("macro", {"bridge"}, minimum_inputs=2, maximum_inputs=2),
    ]
    return {"anyOf": [item for item in variants if item is not None]}


def _response_output_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    for output in data.get("output") or []:
        if not isinstance(output, dict):
            continue
        for content in output.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    raise GeometryAuthorError("geometry author response contained no output text")


def _infer_base_seed(program: GeometryProgram) -> str:
    ordered = program.topological_nodes()
    node_map = program.node_map
    for node in ordered:
        if node.operator != "scale" or len(node.inputs) != 1:
            continue
        parent = node_map.get(node.inputs[0])
        if parent is None or parent.operator != "box":
            continue
        try:
            vector = tuple(float(value) for value in node.parameters.get("vector") or ())
        except (TypeError, ValueError):
            vector = ()
        if len(vector) != 3 or min(vector) <= 0:
            continue
        for spec in BASE_SEED_SPECS:
            if spec.primitive_operator != "box":
                continue
            if max(abs(vector[index] - spec.normalized_scale[index]) for index in range(3)) <= 0.08:
                return spec.seed_id
    primitive = next((node for node in ordered if node.kind == "primitive"), None)
    if primitive is None:
        return "block"
    if primitive.operator == "extruded_polygon":
        return "profiled_prism"
    if primitive.operator != "box":
        return "block"
    try:
        width = float(primitive.parameters.get("width") or 1.0)
        depth = float(primitive.parameters.get("depth") or 1.0)
        height = float(primitive.parameters.get("height") or 1.0)
    except (TypeError, ValueError):
        return "block"
    plan_aspect = max(width, depth) / max(min(width, depth), 1e-9)
    if height > max(width, depth) * 1.35:
        return "tower"
    if plan_aspect >= 2.2:
        return "bar"
    if height < min(width, depth) * 0.48:
        return "slab"
    return "block"


_PROGRAM_RELATION_OPERATORS = frozenset({
    "courtyard", "carve_void", "notch", "lift", "cantilever", "split_wing",
})


def _is_program_relation_node(node: GeometryNode) -> bool:
    if node.operator == "profiled_hall":
        return True
    role = str(node.semantic_role or "").strip().lower()
    return bool(
        node.operator in _PROGRAM_RELATION_OPERATORS
        and any(
            token in role
            for token in (
                "threshold", "entry", "public", "court", "atrium", "ground",
                "void", "terrace", "access",
            )
        )
    )


def _nonterminal_program_relation(program: GeometryProgram) -> str:
    """Return relation node IDs that body operations can still erase."""

    relation_ids = {
        node.id for node in program.topological_nodes()
        if _is_program_relation_node(node)
    }
    if not relation_ids:
        return ""
    terminal_ids: set[str] = set()
    cursor = program.node_map.get(program.root_id)
    while cursor is not None and _is_program_relation_node(cursor) and len(cursor.inputs) == 1:
        terminal_ids.add(cursor.id)
        cursor = program.node_map.get(cursor.inputs[0])
    return ",".join(sorted(relation_ids - terminal_ids))


def _canonicalize_program_relation_suffix(program: GeometryProgram) -> GeometryProgram:
    """Lower one linear architectural modifier stack to the semantic order.

    The high-level author may list a court before a setback even though the
    executable Core AST must shape the body first. Only a graph whose complete
    root ancestry is one unary chain can be reordered without inventing branch
    semantics. Branched/composition graphs remain explicit and are rejected by
    the terminal-relation validator when their public relation is misplaced.
    """

    if not _nonterminal_program_relation(program):
        return program
    node_map = program.node_map
    chain: list[GeometryNode] = []
    cursor = node_map.get(program.root_id)
    while cursor is not None:
        chain.append(cursor)
        if not cursor.inputs:
            break
        if len(cursor.inputs) != 1:
            return program
        cursor = node_map.get(cursor.inputs[0])
    chain.reverse()
    if len(chain) != len(program.nodes) or not chain or chain[0].kind != "primitive":
        return program
    primitive = chain[0]
    operators = chain[1:]
    body = [
        node for node in operators
        if not _is_program_relation_node(node) and node.operator != "profiled_hall"
    ]
    relations = [
        node for node in operators
        if _is_program_relation_node(node) and node.operator != "profiled_hall"
    ]
    sections = [node for node in operators if node.operator == "profiled_hall"]
    ordered = [primitive, *body, *relations, *sections]
    previous_id = ""
    rebuilt: list[GeometryNode] = []
    for node in ordered:
        rebuilt.append(replace(node, inputs=(() if not previous_id else (previous_id,))))
        previous_id = node.id
    old_order = [node.id for node in chain]
    new_order = [node.id for node in ordered]
    if old_order == new_order:
        return program
    return replace(
        program,
        nodes=tuple(rebuilt),
        root_id=previous_id,
        metadata={
            **program.metadata,
            "architectural_relation_suffix_canonicalized": True,
            "precanonical_node_order": old_order,
            "canonical_node_order": new_order,
            "canonicalization_contract": "body_then_access_relation_suffix_then_section",
        },
    )


def _misaligned_access_relation(
    program: GeometryProgram,
    program_context: dict[str, Any],
) -> str:
    target = str(program_context.get("site_access_side_in_program_frame") or "closed").lower()
    language_contract = program_context.get("geometry_language_contract")
    requires_access = bool(
        isinstance(language_contract, dict)
        and language_contract.get("requires_access_bound_relation")
    )
    access_nodes = [
        node for node in program.topological_nodes()
        if _is_program_relation_node(node)
        and node.operator in {"courtyard", "carve_void", "notch", "lift", "split_wing"}
    ]
    if requires_access and not access_nodes:
        return "program:missing_access_bound_relation"
    if target not in {"east", "west", "north", "south"}:
        return ""
    for node in access_nodes:
        role = str(node.semantic_role or "").lower()
        if node.operator in {"courtyard", "carve_void"}:
            if "internal" in role and "public" not in role and "threshold" not in role:
                continue
            actual = str(node.parameters.get("open_side") or "closed").lower()
            if actual != target:
                return f"{node.id}:open_side={actual}:required={target}"
        if node.operator == "notch" and any(
            token in role for token in ("threshold", "entry", "public", "ground")
        ):
            actual = str(node.parameters.get("side") or "missing").lower()
            if actual != target:
                return f"{node.id}:side={actual}:required={target}"
        if node.operator in {"lift", "split_wing"}:
            actual = str(node.parameters.get("access_side") or "missing").lower()
            if actual != target:
                return f"{node.id}:access_side={actual}:required={target}"
    return ""


def _program_language_contract_issue(
    program: GeometryProgram,
    program_context: dict[str, Any],
) -> str:
    language_contract = program_context.get("geometry_language_contract")
    if not isinstance(language_contract, dict):
        return ""
    known_macros = set(OPERATORS_BY_KIND["macro"])
    actual = [node for node in program.topological_nodes() if node.kind == "macro"]
    repeated_plan_relation = next((
        node for node in program.topological_nodes()
        if node.operator in {"cross_mass", "grid_mass", "radial_array", "split_wing"}
    ), None)
    open_court_relation = next((
        node for node in program.topological_nodes()
        if node.operator in {"courtyard", "carve_void"}
        and str(node.parameters.get("open_side") or "closed") != "closed"
    ), None)
    if repeated_plan_relation is not None and open_court_relation is not None:
        return (
            f"{open_court_relation.id}:open_court_after_{repeated_plan_relation.operator}"
            ":fragments_repeated_plan_use_lift_or_side_notch"
        )
    allowed = {
        str(value).strip().lower()
        for value in language_contract.get("allowed_macro_operators") or ()
        if str(value).strip().lower() in known_macros
    }
    if allowed:
        disallowed = next((node for node in actual if node.operator not in allowed), None)
        if disallowed is not None:
            return f"{disallowed.id}:macro={disallowed.operator}:not_allowed_for_program"
    actual_operators = {node.operator for node in actual}
    required_all = {
        str(value).strip().lower()
        for value in language_contract.get("required_macro_operators_all") or ()
        if str(value).strip()
    }
    missing_all = sorted(required_all - actual_operators)
    if missing_all:
        return f"program:missing_required_macros={','.join(missing_all)}"
    required_any = {
        str(value).strip().lower()
        for value in language_contract.get("required_macro_operators_any") or ()
        if str(value).strip()
    }
    if required_any and not (required_any & actual_operators):
        return f"program:missing_any_required_macro={','.join(sorted(required_any))}"
    base_controller_id = _base_seed_controller_id(program, _infer_base_seed(program))
    body_families: list[str] = []
    public_threshold_count = 0
    for node in program.topological_nodes():
        if node.id == base_controller_id or node.operator == "profiled_hall":
            continue
        family = _AUTHOR_BODY_RULE_FAMILIES.get(node.operator)
        if family is None:
            continue
        public_threshold = bool(
            node.operator in {"courtyard", "carve_void"}
            and str(node.parameters.get("open_side") or "closed") != "closed"
        ) or bool(node.operator == "notch" and node.parameters.get("side")) \
            or bool(
                node.operator in {"lift", "split_wing"}
                and str(node.parameters.get("access_side") or "closed") != "closed"
            )
        if public_threshold:
            public_threshold_count += 1
        else:
            body_families.append(family)
    maximum_body_rules = max(0, int(program_context.get("author_maximum_body_rule_count") or 0))
    maximum_threshold_rules = max(0, int(program_context.get("author_maximum_public_threshold_rule_count") or 0))
    if maximum_body_rules and len(body_families) > maximum_body_rules:
        return f"program:body_rule_budget={len(body_families)}:maximum={maximum_body_rules}"
    duplicated_body_families = sorted({
        family for family in body_families if body_families.count(family) > 1
    })
    if duplicated_body_families:
        return f"program:body_rule_family_repeated={','.join(duplicated_body_families)}"
    if maximum_threshold_rules and public_threshold_count > maximum_threshold_rules:
        return (
            f"program:public_threshold_rule_budget={public_threshold_count}:"
            f"maximum={maximum_threshold_rules}"
        )
    return ""


_AUTHOR_BODY_RULE_FAMILIES = {
    "bend": "deformation", "bent_bar": "deformation", "twist": "deformation",
    "inflate": "deformation", "pinch": "deformation", "taper": "deformation",
    "shear": "deformation", "circularize": "deformation",
    "profile_sweep_3d": "deformation", "setback": "step", "stepped_mass": "step",
    "terrace": "step", "courtyard": "void", "carve_void": "void",
    "notch": "void", "puncture": "void", "cut_corner": "void",
    "slice": "cut", "clip": "cut", "radial_array": "array",
    "matrix_array": "array",
    "linear_array": "array", "mirror_array": "array", "cross_mass": "array", "grid_mass": "array",
    "split_wing": "array", "cantilever": "support", "lift": "support",
    "matrix4": "transform", "scale": "transform", "translate": "transform", "rotate": "transform",
    "union": "composition", "intersection": "composition", "difference": "composition",
    "attach": "composition", "bridge": "composition",
    "shell_thicken": "surface_shell",
}


def _author_validation_context(context: dict[str, Any]) -> dict[str, Any]:
    """Align the LLM author with the unchanged downstream body-rule gate."""
    program_context = (
        dict(context.get("program_context"))
        if isinstance(context.get("program_context"), dict)
        else {}
    )
    maximum_body_rules = _author_body_rule_budget(context)
    program_context.update({
        "author_maximum_body_rule_count": maximum_body_rules,
        "author_maximum_public_threshold_rule_count": 1,
    })
    return program_context


def _author_body_rule_budget(context: dict[str, Any]) -> int:
    """Return the source share of the cross-layer visual-rule budget."""
    try:
        maximum_depth = max(1, min(3, int(context.get("maximum_operator_depth") or 2)))
        downstream_reserve = max(
            0,
            min(2, int(context.get("downstream_body_rule_reserve") or 0)),
        )
    except (TypeError, ValueError):
        maximum_depth, downstream_reserve = 2, 0
    return max(1, maximum_depth - downstream_reserve)


def _base_seed_controller_id(program: GeometryProgram, seed_id: str) -> str:
    """Return the typed node that establishes the normalized start proportion."""
    ordered = program.topological_nodes()
    node_map = program.node_map
    matching_spec = next((spec for spec in BASE_SEED_SPECS if spec.seed_id == seed_id), None)
    if matching_spec is not None and matching_spec.primitive_operator == "box":
        for node in ordered:
            if node.operator != "scale" or len(node.inputs) != 1:
                continue
            parent = node_map.get(node.inputs[0])
            if parent is None or parent.operator != "box":
                continue
            try:
                vector = tuple(float(value) for value in node.parameters.get("vector") or ())
            except (TypeError, ValueError):
                continue
            if len(vector) == 3 and max(
                abs(vector[index] - matching_spec.normalized_scale[index])
                for index in range(3)
            ) <= 0.08:
                return node.id
    if seed_id == "profiled_prism":
        profiled = next(
            (node for node in ordered if node.operator in {"extruded_polygon", "wedge", "sweep", "loft", "profiled_hall"}),
            None,
        )
        if profiled is not None:
            return profiled.id
    primitive = next((node for node in ordered if node.kind == "primitive"), None)
    return primitive.id if primitive is not None else ""


def _author_parameter_value_contract(operator: str, parameter: str) -> Any:
    allowed = STRING_PARAMETER_VALUES.get((operator, parameter))
    if allowed is not None:
        return {"type": "string", "enum": sorted(allowed)}
    if parameter == "axis":
        return {"type": "string", "enum": ["x", "y", "z"]}
    operator_lengths = OPERATOR_VECTOR_LENGTHS.get((operator, parameter))
    if operator_lengths is not None:
        return {
            "type": "numeric_vector",
            "lengths": list(operator_lengths),
        }
    if parameter in VECTOR_LENGTHS:
        return {"type": "numeric_vector", "lengths": list(VECTOR_LENGTHS[parameter])}
    if parameter in NUMERIC_BOUNDS:
        lower, upper = NUMERIC_BOUNDS[parameter]
        return {
            "type": "number",
            "minimum": lower,
            "maximum": upper,
            **({"integer": True} if parameter in INTEGER_PARAMETERS else {}),
        }
    if parameter in {"x", "y", "z"}:
        # Normalized local translation/bridge coordinates. These parameters
        # are intentionally absent from the mutation clamp table because the
        # site fitter rebases them later, but their JSON type is still numeric.
        return {"type": "number", "minimum": -4.0, "maximum": 4.0}
    if parameter in BOOLEAN_PARAMETERS:
        return {"type": "boolean"}
    if parameter in {
        "matrix4", "matrices", "points", "holes", "path", "profiles",
        "section_controls",
    }:
        return {"type": "structured_literal"}
    return {"type": "literal"}


def _validate_structured_author_parameter_value(
    operator: str,
    parameter: str,
    value: Any,
    contract: dict[str, Any],
) -> None:
    """Fail closed when an authored value violates its executable contract."""

    label = f"{operator}.{parameter}"
    contract_type = str(contract.get("type") or "")
    if contract_type == "number":
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be a finite number") from exc
        if not isfinite(number):
            raise ValueError(f"{label} must be a finite number")
        if bool(contract.get("integer")) and not number.is_integer():
            raise ValueError(f"{label} must be an integer")
        minimum = float(contract["minimum"])
        maximum = float(contract["maximum"])
        if number < minimum or number > maximum:
            raise ValueError(
                f"{label} must be between {minimum:g} and {maximum:g}"
            )
        return
    if contract_type == "string":
        allowed = [str(item) for item in contract.get("enum") or ()]
        if allowed and str(value) not in allowed:
            raise ValueError(
                f"{label} must be one of {', '.join(allowed)}"
            )
        return
    if contract_type == "numeric_vector":
        lengths = [int(item) for item in contract.get("lengths") or ()]
        if not isinstance(value, list) or len(value) not in lengths:
            raise ValueError(f"{label} expects vector lengths {lengths}")
        try:
            finite = all(isfinite(float(component)) for component in value)
        except (TypeError, ValueError):
            finite = False
        if not finite:
            raise ValueError(f"{label} vector values must be finite numbers")


def _author_cache_path(*, context: dict[str, Any], count: int, model: str) -> Path:
    payload = json.dumps({
        "schema": GEOMETRY_AUTHOR_PROMPT_CONTRACT,
        "model": model,
        "count": count,
        "context": context,
    }, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    key = hashlib.sha256(payload).hexdigest()
    root = Path(os.getenv(
        "MAAS_GEOMETRY_AUTHOR_CACHE_DIR",
        "docs/ai-session-memory/reference-corpus/geometry-author-cache",
    ))
    return root / f"{key}.json"


def _load_author_cache(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    if (
        isinstance(payload, dict)
        and payload.get("cache_schema_version") in {
            "arr.maas.geometry_llm_author_cache.v1",
            "arr.maas.geometry_llm_author_cache.v2",
            "arr.maas.geometry_llm_author_cache.v3",
        }
        and payload.get("validation_status", "accepted") == "accepted"
        and (
            isinstance(payload.get("payload"), dict)
            or isinstance(payload.get("compiled_programs"), list)
        )
    ):
        return payload
    return None


def _save_author_cache(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError:
        pass


__all__ = [
    "GeometryAuthorError",
    "author_geometry_programs_with_openai",
    "geometry_programs_from_author_payload",
]
