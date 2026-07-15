"""OpenAI LLM author for bounded architectural geometry programs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .ast import GeometryProgram
from .dsl import GeometryDslError, parse_geometry_dsl


DEFAULT_GEOMETRY_AUTHOR_MODEL = "gpt-5.4-mini"


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
    selected_model = model or os.getenv("MAAS_GEOMETRY_AUTHOR_MODEL") or DEFAULT_GEOMETRY_AUTHOR_MODEL
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
                "schema": _author_schema(count),
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
    return geometry_programs_from_author_payload(payload, expected_count=count)


def geometry_programs_from_author_payload(
    payload: dict[str, Any],
    *,
    expected_count: int | None = None,
) -> tuple[GeometryProgram, ...]:
    programs: list[GeometryProgram] = []
    seen_hashes: set[str] = set()
    rejected: list[str] = []
    for index, item in enumerate(payload.get("programs") or []):
        if not isinstance(item, dict):
            continue
        try:
            program = parse_geometry_dsl(
                str(item.get("dsl") or ""),
                name=str(item.get("name") or f"llm_geometry_{index + 1:02d}"),
            )
        except GeometryDslError as exc:
            rejected.append(f"{index + 1}:{exc}")
            continue
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
    return tuple(programs[:minimum])


def _author_prompt(context: dict[str, Any], count: int) -> str:
    context_text = json.dumps(context, ensure_ascii=False, sort_keys=True)[:12000]
    return f"""Create exactly {count} executable and materially different architectural mass programs.

Core assignment DSL examples:
mass base = box(12, 8, 4)
mass court = courtyard(base, margin_ratio=0.28)
mass result = bend(court, axis="x", angle_degrees=28, subdivisions=4)

Allowed primitives: box, cylinder, extruded_polygon, wedge, sweep, loft.
Allowed transforms: translate/move, rotate, scale, mirror, shear.
Allowed modifiers: bend, taper, twist, slice, clip, cut_corner.
Allowed booleans: union, subtract/difference, intersection.
Allowed patterns: duplicate, linear_array, radial_array, mirror_array, stack.
Allowed compositions: attach, bridge.
Allowed macros: courtyard, carve_void, notch, setback, terrace, cantilever, bridge,
cross_mass, bent_bar, split_wing, attach_volume, tapered_tower, leaning_tower,
cut_corner, stepped_mass.

Rules:
- Every right-hand side is one function call; parameters are explicit literals.
- A prior variable can be reused; reassignment is normalized to an acyclic SSA graph.
- Use bounded local normalized dimensions, not parcel coordinates and not a copied famous building.
- Do not produce parameter-only variants. Vary tree structure, topology, void/section/roof/composition language.
- Prefer <=5 visible connected volumes and clean solids.
- Include a final variable named result.

Program/site context:
{context_text}
"""


def _author_schema(count: int) -> dict[str, Any]:
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
                    "required": ["name", "dsl", "rationale"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 120},
                        "dsl": {"type": "string", "minLength": 20, "maxLength": 8000},
                        "rationale": {"type": "string", "maxLength": 600},
                    },
                },
            }
        },
    }


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


__all__ = [
    "GeometryAuthorError",
    "author_geometry_programs_with_openai",
    "geometry_programs_from_author_payload",
]
