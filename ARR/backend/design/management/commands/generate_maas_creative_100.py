"""Persist a bounded pre-legal creative MASS choice pool."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw

from design.maas.creative_floor_portfolio import (
    build_creative_floor_portfolio,
)
from design.maas.creative_morphology import morphology_distance
from design.maas.creative_program_author import (
    authored_programs_from_cache_pool,
    authored_programs_from_payload,
)
from design.maas.creative_research_bundle import (
    write_creative_mass_research_bundle,
)
from design.maas.design_memory.reference_events import (
    build_reference_review_events,
    mutable_event,
)
from design.maas.geometry_language import (
    CompilationResult,
    GeometryAuthorError,
    GeometryProgram,
    author_geometry_programs_with_openai,
    render_compilation_preview,
)
from design.maas.geometry_language.vlm_adapter import (
    retrieve_geometry_reference_matches,
)
from design.maas.preference.vlm_scorer import (
    score_candidate_with_openai_vlm,
)


_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_BOARD_COLUMNS = 10
_BOARD_CARD_WIDTH = 300
_BOARD_IMAGE_HEIGHT = 227
_BOARD_LABEL_HEIGHT = 23
_VLM_PILOT_MAX_REQUESTS = 15


class Command(BaseCommand):
    help = (
        "Generate up to 100 compiled four-view creative MASS candidates. "
        "The output is a pre-legal choice pool; paid review is opt-in only."
    )

    def add_arguments(self, parser):
        parser.add_argument("--count", default=100, type=int)
        parser.add_argument("--pnu", required=True, type=str)
        parser.add_argument(
            "--capacity-ceiling-m2",
            default=332.322,
            type=float,
        )
        parser.add_argument("--output-root", required=True, type=str)
        parser.add_argument("--run-id", default="", type=str)
        parser.add_argument(
            "--author-mode",
            required=True,
            choices=("payload", "llm", "cache_pool", "recipe_fixture"),
            help=(
                "payload or llm is the production path; recipe_fixture is "
                "an explicit deterministic regression/demo source"
            ),
        )
        parser.add_argument("--author-payload", default="", type=str)
        parser.add_argument("--author-cache-root", default="", type=str)
        parser.add_argument("--author-model", default="", type=str)
        parser.add_argument(
            "--vlm-pilot",
            action="store_true",
            help=(
                "Opt in to at most 15 low-detail VLM calls, one morphology "
                "medoid per family."
            ),
        )
        parser.add_argument("--vlm-model", default="", type=str)

    def handle(self, *args, **options):
        count = int(options["count"])
        if count < 1 or count > 100:
            raise CommandError("--count must be between 1 and 100")
        pnu = str(options["pnu"] or "").strip()
        if not pnu:
            raise CommandError("--pnu is required")
        run_id = str(options.get("run_id") or "").strip() or (
            f"maas-creative-{count}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        )
        if (
            not _RUN_ID_PATTERN.fullmatch(run_id)
            or run_id in {".", ".."}
        ):
            raise CommandError("--run-id contains unsupported characters")

        output_root = Path(options["output_root"]).resolve()
        run_directory = (output_root / run_id).resolve()
        if run_directory.parent != output_root:
            raise CommandError("--run-id must resolve inside --output-root")
        if run_directory.exists() and any(run_directory.iterdir()):
            raise CommandError(f"run directory is not empty: {run_directory}")
        candidates_directory = run_directory / "candidates"
        renders_directory = run_directory / "renders"
        candidates_directory.mkdir(parents=True, exist_ok=True)
        renders_directory.mkdir(parents=True, exist_ok=True)

        try:
            authored_programs = _resolve_authored_programs(
                mode=str(options["author_mode"]),
                payload_path=str(options.get("author_payload") or ""),
                cache_root=str(options.get("author_cache_root") or ""),
                model=str(options.get("author_model") or ""),
                count=count,
                context={
                    "pnu": pnu,
                    "capacity_ceiling_m2": float(
                        options["capacity_ceiling_m2"]
                    ),
                    "creative_portfolio_run_id": run_id,
                    "instruction": (
                        "Author materially different executable typed MASS "
                        "ASTs. Do not select or imitate a named family recipe."
                    ),
                },
            )
            portfolio = build_creative_floor_portfolio(
                count=count,
                capacity_ceiling_m2=float(
                    options["capacity_ceiling_m2"]
                ),
                authored_programs=authored_programs,
            )
        except (
            GeometryAuthorError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as exc:
            raise CommandError(str(exc)) from exc
        candidates = portfolio.get("candidates")
        if (
            not isinstance(candidates, list)
            or len(candidates) != count
        ):
            raise CommandError(
                "creative portfolio candidate count does not match request"
            )

        persisted_candidates: list[dict[str, Any]] = []
        preview_items: list[tuple[str, Path]] = []
        for candidate in candidates:
            persisted, preview = _persist_candidate(
                candidate,
                run_directory=run_directory,
                candidates_directory=candidates_directory,
                renders_directory=renders_directory,
                run_id=run_id,
                pnu=pnu,
            )
            persisted_candidates.append(persisted)
            preview_items.append((
                (
                    f"{persisted['candidate_id']} "
                    f"{persisted['family']} "
                    f"{persisted['capacity_band']}"
                ),
                preview,
            ))

        board_path = run_directory / "maas-creative-board.png"
        board = _write_board(preview_items, board_path)
        graph = _frontend_graph(
            persisted_candidates,
            run_id=run_id,
            pnu=pnu,
        )
        pilot = (
            _run_bounded_vlm_pilot(
                persisted_candidates,
                run_directory=run_directory,
                model=str(options.get("vlm_model") or "") or None,
            )
            if bool(options.get("vlm_pilot"))
            else {
                "schema_version": "arr.maas.creative_vlm_pilot.v1",
                "status": "not_requested",
                "request_count": 0,
                "max_request_count": _VLM_PILOT_MAX_REQUESTS,
                "reference_limit_per_request": 3,
                "candidate_image_detail": "low",
                "records": [],
                "events": [],
            }
        )
        paid_author_response_ids = {
            str(
                (candidate.get("author_evidence") or {}).get(
                    "response_id"
                )
                or ""
            )
            for candidate in persisted_candidates
            if str(options["author_mode"]) == "llm"
            and not bool(
                (candidate.get("author_evidence") or {}).get(
                    "cache_hit"
                )
            )
            and str(
                (candidate.get("author_evidence") or {}).get(
                    "response_id"
                )
                or ""
            )
        }
        paid_author_request_count = len(paid_author_response_ids)
        payload = {
            **{
                key: deepcopy(value)
                for key, value in portfolio.items()
                if key != "candidates"
            },
            "run_id": run_id,
            "author_mode": str(options["author_mode"]),
            "pnu": pnu,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "candidate_count": len(persisted_candidates),
            "candidates": [
                {
                    "candidate_id": candidate["candidate_id"],
                    "family": candidate["family"],
                    "capacity_band": candidate["capacity_band"],
                    "storeys": candidate["storey_evidence"][
                        "storey_count"
                    ],
                    "legal_status": candidate["legal_review"]["status"],
                    "program_hash": candidate["program_hash"],
                    "geometry_hash": candidate["geometry_hash"],
                    "candidate_json": candidate["candidate_json"],
                    "render_png": candidate["render_png"],
                    "mass_directory": candidate["mass_directory"],
                    "mass_manifest": candidate["mass_manifest"],
                    "elevation_research_handoff": candidate[
                        "elevation_research_handoff"
                    ],
                }
                for candidate in persisted_candidates
            ],
            "board": board,
            "vlm_pilot": pilot,
            "paid_vlm_request_count": int(pilot["request_count"]),
            "paid_author_request_count": paid_author_request_count,
            "paid_author_request_count_authority": (
                "confirmed_noncache_response_ids_in_current_llm_mode"
            ),
            "frontend_graph": graph,
            "filter_facets": _filter_facets(persisted_candidates),
            "artifact_contract": {
                "candidate_json_contains_full_program_trace_and_mesh": True,
                "individual_render": "deterministic_four_view_png",
                "mass_research_folder": (
                    "program_matrix_mesh_obj_csv_six_views_elevation_handoff"
                ),
                "legal_authority": "not_evaluated",
                "paid_provider_calls": (
                    int(pilot["request_count"])
                    + paid_author_request_count
                ),
            },
        }
        portfolio_path = (
            run_directory / "maas-creative-portfolio.json"
        )
        _write_json_atomic(portfolio_path, payload)
        self.stdout.write(json.dumps({
            "run_id": run_id,
            "run_directory": str(run_directory),
            "candidate_count": len(persisted_candidates),
            "portfolio_json": str(portfolio_path),
            "board_png": str(board_path),
            "paid_vlm_request_count": int(
                payload.get("paid_vlm_request_count") or 0
            ),
            "paid_author_request_count": paid_author_request_count,
            "legal_review_status": payload["legal_review_status"],
        }, ensure_ascii=False, sort_keys=True))


def _resolve_authored_programs(
    *,
    mode: str,
    payload_path: str,
    cache_root: str,
    model: str,
    count: int,
    context: dict[str, Any],
) -> tuple[GeometryProgram, ...] | None:
    if mode == "recipe_fixture":
        return None
    if mode == "cache_pool":
        if not cache_root.strip():
            raise ValueError(
                "--author-cache-root is required for cache_pool author mode"
            )
        return tuple(
            item.program
            for item in authored_programs_from_cache_pool(
                Path(cache_root).expanduser().resolve(),
                expected_count=count,
            )
        )
    if mode == "payload":
        if not payload_path.strip():
            raise ValueError(
                "--author-payload is required for payload author mode"
            )
        path = Path(payload_path).expanduser().resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("author payload must be a JSON object")
        return tuple(
            item.program
            for item in authored_programs_from_payload(
                payload,
                expected_count=count,
                program_context=context,
            )
        )
    if mode != "llm":
        raise ValueError(f"unsupported author mode: {mode}")
    programs: list[GeometryProgram] = []
    for batch_index, start in enumerate(range(0, count, 20)):
        batch_count = min(20, count - start)
        programs.extend(author_geometry_programs_with_openai(
            {
                **context,
                "creative_author_batch_index": batch_index,
                "creative_author_batch_offset": start,
            },
            target_count=batch_count,
            model=model or None,
        ))
    if len(programs) < count:
        raise GeometryAuthorError(
            f"geometry author yielded {len(programs)}/{count} programs"
        )
    return tuple(programs[:count])


def _select_morphology_medoids(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Choose one deterministic minimum-total-distance member per family."""

    families: dict[str, list[dict[str, Any]]] = {}
    family_order: list[str] = []
    for candidate in candidates:
        family = str(candidate.get("family") or "")
        if family not in families:
            families[family] = []
            family_order.append(family)
        families[family].append(candidate)
    representatives: list[dict[str, Any]] = []
    for family in family_order[:_VLM_PILOT_MAX_REQUESTS]:
        members = families[family]
        representative = min(
            members,
            key=lambda candidate: (
                sum(
                    float(morphology_distance(
                        candidate["morphology_evidence"]["descriptor"],
                        other["morphology_evidence"]["descriptor"],
                    ))
                    for other in members
                ),
                str(candidate.get("candidate_id") or ""),
            ),
        )
        representatives.append(representative)
    return representatives


def _run_bounded_vlm_pilot(
    candidates: list[dict[str, Any]],
    *,
    run_directory: Path,
    model: str | None,
) -> dict[str, Any]:
    """Run only the explicit, family-medoid, low-detail paid pilot."""

    records: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    representatives = _select_morphology_medoids(candidates)
    for candidate in representatives[:_VLM_PILOT_MAX_REQUESTS]:
        program_payload = candidate.get("geometry_program")
        program = (
            GeometryProgram.from_dict(program_payload)
            if isinstance(program_payload, dict)
            else program_payload
        )
        references = list(retrieve_geometry_reference_matches(
            program,
            building_type=str(candidate.get("family") or "generic"),
            limit=3,
        ))[:3]
        preview_path = (
            run_directory / str(candidate.get("render_png") or "")
        ).resolve()
        result = score_candidate_with_openai_vlm(
            feature={
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "candidate_id": str(candidate.get("candidate_id") or ""),
                    "geometry_program": deepcopy(program_payload),
                    "creative_family": str(candidate.get("family") or ""),
                },
            },
            image_path=preview_path,
            reference_matches=references,
            model=model,
            image_detail="low",
            program_hash=str(candidate.get("program_hash") or ""),
            geometry_hash=str(candidate.get("geometry_hash") or ""),
        )
        candidate_events = build_reference_review_events(
            retrieved_references=references,
            vlm_result=result,
            program_hash=str(candidate.get("program_hash") or ""),
            geometry_hash=str(candidate.get("geometry_hash") or ""),
        )
        events.extend(mutable_event(event) for event in candidate_events)
        records.append({
            "candidate_id": str(candidate.get("candidate_id") or ""),
            "family": str(candidate.get("family") or ""),
            "program_hash": str(candidate.get("program_hash") or ""),
            "geometry_hash": str(candidate.get("geometry_hash") or ""),
            "reference_count": len(references),
            "model": str(result.get("model") or model or ""),
            "response_id": str(result.get("response_id") or ""),
            "vlm_result": deepcopy(result),
        })
    return {
        "schema_version": "arr.maas.creative_vlm_pilot.v1",
        "status": "completed",
        "request_count": len(records),
        "max_request_count": _VLM_PILOT_MAX_REQUESTS,
        "reference_limit_per_request": 3,
        "candidate_image_detail": "low",
        "representative_policy": "one_morphology_medoid_per_family",
        "records": records,
        "events": events,
    }


def _persist_candidate(
    candidate: Any,
    *,
    run_directory: Path,
    candidates_directory: Path,
    renders_directory: Path,
    run_id: str,
    pnu: str,
) -> tuple[dict[str, Any], Path]:
    if not isinstance(candidate, dict):
        raise CommandError("creative portfolio candidate must be an object")
    payload = deepcopy(candidate)
    candidate_id = str(payload.get("candidate_id") or "").strip()
    program_hash = str(payload.get("program_hash") or "").strip()
    geometry_hash = str(payload.get("geometry_hash") or "").strip()
    program_payload = payload.get("geometry_program")
    mesh = payload.get("mesh")
    if (
        not candidate_id
        or not program_hash
        or not geometry_hash
        or not isinstance(program_payload, dict)
        or not isinstance(mesh, dict)
        or not mesh.get("vertices")
        or not mesh.get("triangles")
    ):
        raise CommandError("creative portfolio candidate is incomplete")
    try:
        program = GeometryProgram.from_dict(program_payload)
    except (TypeError, ValueError) as exc:
        raise CommandError(
            f"{candidate_id} has an invalid GeometryProgram"
        ) from exc
    if program.program_hash() != program_hash:
        raise CommandError(f"{candidate_id} program hash mismatch")

    vertices = tuple(
        tuple(float(value) for value in vertex)
        for vertex in mesh["vertices"]
    )
    triangles = tuple(
        tuple(int(value) for value in triangle)
        for triangle in mesh["triangles"]
    )
    mesh_evidence = (
        payload.get("mesh_evidence")
        if isinstance(payload.get("mesh_evidence"), dict)
        else {}
    )
    metrics = {
        **deepcopy(mesh_evidence),
        "triangle_count": len(triangles),
        "vertex_count": len(vertices),
    }
    result = CompilationResult(
        program=program,
        status="compiled",
        vertices=vertices,
        triangles=triangles,
        metrics=metrics,
        trace=tuple(deepcopy(payload.get("matrix4_trace") or ())),
        geometry_hash=geometry_hash,
    )
    preview_path = renders_directory / f"{candidate_id}.png"
    render_compilation_preview(
        result,
        preview_path,
        title=f"{candidate_id} {payload.get('family') or ''}",
    )

    candidate_path = candidates_directory / f"{candidate_id}.json"
    relative_candidate = candidate_path.relative_to(run_directory).as_posix()
    relative_preview = preview_path.relative_to(run_directory).as_posix()
    payload.update({
        "run_id": run_id,
        "pnu": pnu,
        "identity": {
            "schema_version": (
                "arr.maas.creative_candidate_identity.v1"
            ),
            "candidate_id": candidate_id,
            "program_hash": program_hash,
            "geometry_hash": geometry_hash,
        },
        "candidate_json": relative_candidate,
        "render_png": relative_preview,
    })
    legal_review = payload.get("legal_review")
    if (
        not isinstance(legal_review, dict)
        or legal_review.get("status") != "not_evaluated"
        or legal_review.get("hard_pass") is not False
    ):
        raise CommandError(
            f"{candidate_id} must remain legally not_evaluated"
        )
    try:
        research_bundle = write_creative_mass_research_bundle(
            payload,
            run_directory=run_directory,
            run_id=run_id,
            pnu=pnu,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise CommandError(
            f"{candidate_id} research bundle failed: {exc}"
        ) from exc
    payload.update({
        "mass_directory": research_bundle["mass_directory"],
        "mass_manifest": research_bundle["mass_manifest"],
        "elevation_research_handoff": research_bundle[
            "elevation_research_handoff"
        ],
    })
    _write_json_atomic(candidate_path, payload)
    return payload, preview_path


def _frontend_graph(
    candidates: list[dict[str, Any]],
    *,
    run_id: str,
    pnu: str,
) -> dict[str, Any]:
    portfolio_id = f"creative:portfolio:{run_id}"
    nodes: list[dict[str, Any]] = [{
        "id": portfolio_id,
        "kind": "geometry_portfolio",
        "identity": run_id,
        "label": f"Creative authored choice pool · {len(candidates)}",
        "attributes": {
            "run_id": run_id,
            "pnu": pnu,
            "candidate_count": len(candidates),
            "choice_pool": True,
            "legal_status": "not_evaluated",
        },
    }]
    edges: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        node_id = f"creative:candidate:{candidate_id}"
        nodes.append({
            "id": node_id,
            "kind": "creative_mass_candidate",
            "identity": candidate["geometry_hash"],
            "label": f"{candidate_id} · {candidate['family']}",
            "attributes": {
                "candidate_id": candidate_id,
                "family": candidate["family"],
                "capacity_band": candidate["capacity_band"],
                "storeys": candidate["storey_evidence"]["storey_count"],
                "legal_status": candidate["legal_review"]["status"],
                "program_hash": candidate["program_hash"],
                "geometry_hash": candidate["geometry_hash"],
                "candidate_json": candidate["candidate_json"],
                "render_png": candidate["render_png"],
            },
        })
        edges.append({
            "id": f"creative:member:{candidate_id}",
            "source": node_id,
            "target": portfolio_id,
            "kind": "member_of",
        })
    return {
        "schema_version": "arr.maas.creative_frontend_graph.v1",
        "graph_id": portfolio_id,
        "root_node_ids": [portfolio_id],
        "nodes": nodes,
        "edges": edges,
    }


def _filter_facets(
    candidates: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    values = {
        "family": Counter(
            str(candidate["family"]) for candidate in candidates
        ),
        "capacity_band": Counter(
            str(candidate["capacity_band"]) for candidate in candidates
        ),
        "storeys": Counter(
            str(candidate["storey_evidence"]["storey_count"])
            for candidate in candidates
        ),
        "legal_status": Counter(
            str(candidate["legal_review"]["status"])
            for candidate in candidates
        ),
    }
    return {
        facet: [
            {"value": value, "count": count}
            for value, count in sorted(counter.items())
        ]
        for facet, counter in values.items()
    }


def _write_board(
    items: list[tuple[str, Path]],
    output_path: Path,
) -> dict[str, Any]:
    columns = 5 if len(items) == 20 else _BOARD_COLUMNS
    rows = max(1, (len(items) + columns - 1) // columns)
    card_height = _BOARD_IMAGE_HEIGHT + _BOARD_LABEL_HEIGHT
    image = Image.new(
        "RGB",
        (_BOARD_CARD_WIDTH * columns, card_height * rows),
        "#e8eef5",
    )
    draw = ImageDraw.Draw(image)
    for index, (label, path) in enumerate(items):
        row, column = divmod(index, columns)
        x = column * _BOARD_CARD_WIDTH
        y = row * card_height
        with Image.open(path) as source:
            thumbnail = source.convert("RGB").crop(
                (0, 0, 450, 325)
            ).resize(
                (_BOARD_CARD_WIDTH, _BOARD_IMAGE_HEIGHT),
                Image.Resampling.LANCZOS,
            )
        image.paste(thumbnail, (x, y))
        draw.rectangle(
            (
                x,
                y + _BOARD_IMAGE_HEIGHT,
                x + _BOARD_CARD_WIDTH,
                y + card_height,
            ),
            fill="#ffffff",
        )
        draw.text(
            (x + 7, y + _BOARD_IMAGE_HEIGHT + 5),
            f"{index + 1:03d} PRE-LEGAL {label[:34]}",
            fill="#172033",
        )
    temporary = output_path.with_suffix(".tmp.png")
    image.save(temporary)
    temporary.replace(output_path)
    return {
        "path": output_path.name,
        "status": "pre_legal_not_evaluated",
        "columns": columns,
        "rows": rows,
        "card_width_px": _BOARD_CARD_WIDTH,
        "card_height_px": card_height,
        "candidate_count": len(items),
    }


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
