"""OpenAI VLM scorer for MAAS second-stage preference distillation."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .reference_paths import resolve_reference_image_path


VLM_SCORE_SCHEMA_VERSION = "arr.maas.vlm_concept_scores.v1"
DEFAULT_VLM_MODEL = "gpt-5.4-mini"


class VlmScoringError(RuntimeError):
    pass


def score_candidate_with_openai_vlm(
    *,
    feature: dict[str, Any],
    image_path: str | Path,
    reference_matches: list[dict[str, Any]] | None = None,
    model: str | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Score a candidate PNG with OpenAI's Responses API.

    The VLM is not asked to judge law or parking. It returns architecture
    concept scores only.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise VlmScoringError("OPENAI_API_KEY is not set")
    image_data_url = _image_data_url(Path(image_path))
    selected_model = model or os.getenv("MAAS_PREFERENCE_VLM_MODEL") or DEFAULT_VLM_MODEL
    user_content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": _prompt_text(feature, reference_matches or []),
        },
        {
            "type": "input_image",
            "image_url": image_data_url,
        },
    ]
    user_content.extend(_reference_image_content(reference_matches or []))
    body = {
        "model": selected_model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are an architectural massing critic. Score only visible massing quality. "
                            "Do not judge legal compliance, zoning, parking approval, facade beauty, or rendering polish."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "maas_architecture_preference_scores",
                "strict": True,
                "schema": _response_schema(),
            }
        },
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    retry_count = max(0, int(os.getenv("MAAS_PREFERENCE_VLM_RETRIES", "2")))
    data: dict[str, Any] | None = None
    last_error: Exception | None = None
    for attempt in range(retry_count + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code < 500 and exc.code != 429:
                try:
                    detail = exc.read().decode("utf-8")[:500]
                except Exception:
                    detail = str(exc)
                raise VlmScoringError(f"OpenAI VLM response failed: HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            last_error = exc
        if attempt < retry_count:
            time.sleep(1.25 * (attempt + 1))
    if data is None:
        raise VlmScoringError(f"OpenAI VLM response failed after {retry_count + 1} attempts: {last_error}") from last_error
    output_text = _extract_text(data)
    if not output_text:
        raise VlmScoringError("OpenAI VLM response did not include output text")
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise VlmScoringError("OpenAI VLM response was not valid JSON") from exc
    return _normalize_vlm_result(parsed, model=selected_model, response_id=str(data.get("id") or ""))


def _prompt_text(feature: dict[str, Any], reference_matches: list[dict[str, Any]]) -> str:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    source = props.get("source_signature") if isinstance(props.get("source_signature"), dict) else {}
    ambition = props.get("architectural_ambition_evidence") if isinstance(props.get("architectural_ambition_evidence"), dict) else {}
    summary = {
        "variant_id": props.get("variant_id"),
        "mass_shape": props.get("mass_shape"),
        "family": source.get("family") or props.get("operator_family"),
        "formal_principle": ambition.get("formal_principle") or source.get("formal_principle"),
        "dominant_gesture": ambition.get("dominant_gesture") or source.get("dominant_gesture"),
        "primary_language": source.get("primary_language"),
        "secondary_language": source.get("secondary_language"),
        "reference_matches": reference_matches[:5],
        "component_graph": props.get("component_graph") or {},
        "site_boundary_source": props.get("site_boundary_source"),
        "site_access_context": props.get("site_access_context") or {},
        "site_design_field": ambition.get("site_design_field") or source.get("site_design_field"),
    }
    return (
        "Score this MAAS candidate four-view PNG as an early-stage architectural massing diagram. "
        "Reject a form when it is coherent in only one view or when solids visibly collide across views.\n"
        "When a thin green polygon is present it is the actual parcel boundary. Judge whether the dominant "
        "gesture, open-space figure, and orientation respond coherently to that parcel; do not reward a mass "
        "that merely fills a bounding box. Parcel containment itself remains a deterministic hard gate.\n"
        "A thick blue segment marks the verified primary road frontage/access edge. Reward a public void, "
        "court, undercut, entry seam, or other legible ground response to that edge; penalize a sealed or "
        "semantically opposite access response.\n"
        "The first image is the candidate. Any following images are external architectural reference images "
        "retrieved from the reference corpus. Use them only as massing-quality precedent signals; do not reward "
        "facade rendering, photography quality, materials, or direct copying.\n"
        "Return strict JSON. Each concept score must be between 0 and 1. Use component_graph node_id values "
        "when proposing graph edits; do not invent parcel coordinates.\n"
        "Concepts:\n"
        "- gesture_clarity: one readable dominant massing idea.\n"
        "- hierarchy: clear main/support relationship, not random fragments.\n"
        "- non_stair_silhouette (legacy field name): score silhouette resolution, not a blanket ban on steps. "
        "Give a high score to a coherent capacity-bearing stepped landform, inhabited terrace section, or one "
        "continuous cascading mass. Give a low score only to repetitive code-minimum stepbacks, arbitrary cake tiers, "
        "or stairs without program/ground/void consequence.\n"
        "- void_publicness: meaningful void/courtyard/undercut/open ground logic.\n"
        "- repair_integrity: visually coherent and likely not over-clipped by legal repair.\n"
        "- precedent_resonance: resonates with reference massing principles without copying.\n"
        "Critic actions: return any applicable structured actions from this set: "
        "too_fragmented, weak_primary_mass, needs_clean_anchor, too_many_surface_pieces, overlapping_volumes, "
        "too_box_like, weak_form_continuity, needs_profiled_surface, needs_carved_void, "
        "good_void, good_step_mass, preserve_dominant_gesture. Use too_box_like when the proposal is mainly "
        "generic rectangular extrusion/stacking; use weak_form_continuity when pieces do not form one spatial "
        "rule; use needs_profiled_surface for a flat roof/section that should become folded or ribbon-like; "
        "use needs_carved_void when solid/void organization is missing. These actions must describe "
        "geometry changes for the next MassDSL generation, not legal or parking judgments.\n"
        "For graph_edits return only bounded genotype edits: set_parameter, replace_operation, add_operation, "
        "remove_optional, or reparent. For numeric parameters use numeric_value and leave string_value empty. "
        "For axis/side/corner/open_side/field_topology/vertical_mode use string_value. A replace_operation or "
        "add_operation must be immediately followed by at least one valid set_parameter for the affected node; "
        "empty-default topology edits are rejected. add_operation may add only support, void, or connector nodes, "
        "and must identify a new node_id and an existing parent_node_id. Geometry and hard gates validate every edit.\n"
        f"Candidate JSON summary:\n{json.dumps(summary, ensure_ascii=False, sort_keys=True)}"
    )


def _reference_image_content(reference_matches: list[dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for index, match in enumerate(reference_matches[:limit], start=1):
        image_url = _reference_image_url(match)
        if not image_url:
            continue
        content.append({
            "type": "input_text",
            "text": (
                f"Reference image {index}: {match.get('title') or match.get('source_id') or 'architecture reference'}; "
                f"matched_tags={match.get('matched_tags') or []}; source={match.get('source') or ''}."
            ),
        })
        content.append({
            "type": "input_image",
            "image_url": image_url,
        })
    return content


def _reference_image_url(match: dict[str, Any]) -> str:
    local = str(match.get("local_path") or "")
    if local:
        path = resolve_reference_image_path(local)
        if path is not None:
            return _image_data_url(path)
    remote = str(match.get("image_url") or "")
    if remote.startswith(("http://", "https://", "data:")):
        return remote
    return ""


def _response_schema() -> dict[str, Any]:
    score_schema = {"type": "number", "minimum": 0, "maximum": 1}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["concept_scores", "rationale", "warnings", "critic_actions", "graph_edits"],
        "properties": {
            "concept_scores": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "gesture_clarity",
                    "hierarchy",
                    "non_stair_silhouette",
                    "void_publicness",
                    "repair_integrity",
                    "precedent_resonance",
                ],
                "properties": {
                    "gesture_clarity": score_schema,
                    "hierarchy": score_schema,
                    "non_stair_silhouette": score_schema,
                    "void_publicness": score_schema,
                    "repair_integrity": score_schema,
                    "precedent_resonance": score_schema,
                },
            },
            "rationale": {"type": "string"},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "critic_actions": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "too_fragmented",
                        "weak_primary_mass",
                        "needs_clean_anchor",
                        "too_many_surface_pieces",
                        "overlapping_volumes",
                        "too_box_like",
                        "weak_form_continuity",
                        "needs_profiled_surface",
                        "needs_carved_void",
                        "good_void",
                        "good_step_mass",
                        "preserve_dominant_gesture",
                    ],
                },
            },
            "graph_edits": {
                "type": "array",
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "operation", "target_node_id", "parent_node_id", "node_id", "role",
                        "verb", "parameter_name", "numeric_value", "string_value", "rationale",
                    ],
                    "properties": {
                        "operation": {"type": "string", "enum": ["set_parameter", "replace_operation", "add_operation", "remove_optional", "reparent"]},
                        "target_node_id": {"type": "string"},
                        "parent_node_id": {"type": "string"},
                        "node_id": {"type": "string"},
                        "role": {"type": "string", "enum": ["", "primary", "support", "void", "connector"]},
                        "verb": {"type": "string"},
                        "parameter_name": {"type": "string"},
                        "numeric_value": {"type": "number", "minimum": -70, "maximum": 70},
                        "string_value": {"type": "string"},
                        "rationale": {"type": "string"},
                    },
                },
            },
        },
    }


def _normalize_vlm_result(data: dict[str, Any], *, model: str, response_id: str) -> dict[str, Any]:
    raw_scores = data.get("concept_scores") if isinstance(data.get("concept_scores"), dict) else {}
    scores = {
        key: round(max(0.0, min(1.0, float(raw_scores.get(key, 0.0)))), 3)
        for key in (
            "gesture_clarity",
            "hierarchy",
            "non_stair_silhouette",
            "void_publicness",
            "repair_integrity",
            "precedent_resonance",
        )
    }
    actions = [str(item) for item in data.get("critic_actions") or [] if str(item) in {
        "too_fragmented", "weak_primary_mass", "needs_clean_anchor",
        "too_many_surface_pieces", "overlapping_volumes", "good_void", "good_step_mass",
        "too_box_like", "weak_form_continuity", "needs_profiled_surface", "needs_carved_void",
        "preserve_dominant_gesture",
    }]
    if scores["hierarchy"] < 0.55:
        actions.append("weak_primary_mass")
    if scores["gesture_clarity"] < 0.60:
        actions.append("needs_clean_anchor")
    if scores["hierarchy"] < 0.60 or scores["repair_integrity"] < 0.55:
        actions.append("too_fragmented")
    if scores["gesture_clarity"] >= 0.75 and scores["hierarchy"] >= 0.70:
        actions.append("preserve_dominant_gesture")
    actions = list(dict.fromkeys(actions))
    graph_edits = []
    # Critic language is intentionally architectural, while the executable
    # genotype has a smaller typed vocabulary.  Translate common architectural
    # edit words at this single boundary instead of silently dropping them in
    # the graph reviser.
    verb_aliases = {
        "carve": "courtyard",
        "bridge": "diagonal_connect",
        "fold": "sloped_roof_mass",
        "sweep": "bend",
        "terrace": "terrace_link",
    }
    for item in data.get("graph_edits") or []:
        if not isinstance(item, dict) or str(item.get("operation") or "") not in {
            "set_parameter", "replace_operation", "add_operation", "remove_optional", "reparent",
        }:
            continue
        verb = str(item.get("verb") or "")[:48].strip().lower()
        graph_edits.append({
            "operation": str(item.get("operation") or ""),
            "target_node_id": str(item.get("target_node_id") or "")[:80],
            "parent_node_id": str(item.get("parent_node_id") or "")[:80],
            "node_id": str(item.get("node_id") or "")[:80],
            "role": str(item.get("role") or ""),
            "verb": verb_aliases.get(verb, verb),
            "parameter_name": str(item.get("parameter_name") or "")[:64],
            "numeric_value": max(-70.0, min(70.0, float(item.get("numeric_value") or 0.0))),
            "string_value": str(item.get("string_value") or "")[:64].strip().lower(),
            "rationale": str(item.get("rationale") or "")[:500],
        })
    return {
        "schema_version": VLM_SCORE_SCHEMA_VERSION,
        "provider": "openai",
        "model": model,
        "response_id": response_id,
        "concept_scores": scores,
        "rationale": str(data.get("rationale") or ""),
        "warnings": [str(item) for item in data.get("warnings") or []],
        "critic_actions": actions,
        "graph_edits": graph_edits[:6],
    }


def _extract_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    chunks: list[str] = []
    for item in response.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict):
                text = content.get("text")
                if isinstance(text, str):
                    chunks.append(text)
    return "\n".join(chunks)


def _image_data_url(path: Path) -> str:
    if not path.exists():
        raise VlmScoringError(f"Image file does not exist: {path}")
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


__all__ = ["DEFAULT_VLM_MODEL", "VLM_SCORE_SCHEMA_VERSION", "VlmScoringError", "score_candidate_with_openai_vlm"]
