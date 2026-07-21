"""Run one paid VLM audit over an already rendered MASS portfolio board."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from design.maas.geometry_language import GeometryOutcomeGraph
from design.maas.preference.vlm_scorer import score_portfolio_board_with_openai_vlm
from design.maas.program_massing import program_reference_contract


CONFIRMATION = "PORTFOLIO-LIVE"


def _read_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise CommandError(f"invalid JSON artifact: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CommandError(f"JSON artifact must be an object: {path}")
    return payload


def _write_object(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _artifact_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in payload.get("records") or ():
        if not isinstance(record, dict):
            continue
        artifact = record.get("geometry_artifact")
        if not isinstance(artifact, dict):
            continue
        source_sequence = str(artifact.get("sourceSequence") or "")
        if source_sequence:
            result[source_sequence] = artifact
    return result


class Command(BaseCommand):
    help = "Run exactly one paid visual audit on an existing final MASS board"

    def add_arguments(self, parser):
        parser.add_argument("--run-dir", required=True)
        parser.add_argument("--program", default="neighborhood")
        parser.add_argument("--model", default=None)
        parser.add_argument("--confirm-live", required=True)

    def handle(self, *args, **options):
        if str(options["confirm_live"]) != CONFIRMATION:
            raise CommandError(f"paid call requires --confirm-live {CONFIRMATION}")
        run_dir = Path(str(options["run_dir"])).resolve()
        summary_path = run_dir / "maas-book-programs-summary.json"
        artifact_path = run_dir / "maas-book-exact-geometry-artifacts.json"
        summary = _read_object(summary_path)
        artifacts = _artifact_index(_read_object(artifact_path))
        slug = str(options["program"])
        program = next((
            item for item in summary.get("programs") or ()
            if isinstance(item, dict) and str(item.get("slug") or "") == slug
        ), None)
        if program is None:
            raise CommandError(f"program not found in summary: {slug}")
        rows = [item for item in program.get("rows") or () if isinstance(item, dict)]
        board = Path(str(program.get("png") or run_dir / f"maas-book-{slug}-20.png"))
        if not board.is_absolute():
            board = (run_dir / board).resolve()
        if not board.is_file():
            fallback = run_dir / f"maas-book-{slug}-20.png"
            board = fallback.resolve()
        if not board.is_file():
            raise CommandError(f"portfolio board not found: {board}")

        candidate_summaries = []
        geometry_hashes = []
        for row in rows:
            artifact = artifacts.get(str(row.get("source_sequence") or ""), {})
            geometry_program = artifact.get("geometryProgram") if isinstance(artifact, dict) else {}
            metadata = (
                geometry_program.get("metadata")
                if isinstance(geometry_program, dict)
                and isinstance(geometry_program.get("metadata"), dict)
                else {}
            )
            identity = artifact.get("identity") if isinstance(artifact, dict) else {}
            geometry_hash = str(
                identity.get("geometryHash")
                if isinstance(identity, dict)
                else ""
            )
            if geometry_hash:
                geometry_hashes.append(geometry_hash)
            candidate_summaries.append({
                "candidate_id": str(row.get("variant_id") or ""),
                "book_scope": str((row.get("book_scope") or {}).get("base_volume_label") or ""),
                "base_seed": str((row.get("design_concept") or {}).get("base_seed") or ""),
                "body_phenotype": row.get("body_phenotype"),
                "roof_archetype": row.get("roof_archetype"),
                "ground_strategy": row.get("ground_strategy"),
                "design_concept_key": row.get("design_concept_key"),
                "geometry_family": str(metadata.get("family") or ""),
                "form_bank_lane": str(metadata.get("form_bank_lane") or ""),
                "chassis_family": row.get("chassis_family"),
            })

        program_context = {
            **program_reference_contract(str(program.get("program") or slug)),
            "pnu": str(summary.get("pnu") or ""),
            "program_slug": slug,
            "numeric_portfolio_status": str(summary.get("book_program_numeric_status") or ""),
            "candidate_count": len(candidate_summaries),
        }
        audit = score_portfolio_board_with_openai_vlm(
            image_path=board,
            program_context=program_context,
            candidate_summaries=candidate_summaries,
            model=str(options.get("model") or "") or None,
        )
        audit["execution_stage"] = "post_run_final_board"
        audit["run_id"] = run_dir.name
        audit["board_path"] = str(board)
        audit_path = run_dir / "maas-paid-portfolio-vlm-audit.json"
        _write_object(audit_path, audit)

        graph_path = run_dir / "maas-geometry-mutation-outcome-graph.json"
        graph = GeometryOutcomeGraph.load(graph_path, pnu=str(summary.get("pnu") or ""))
        graph.observe_portfolio_vlm_audit(
            program_slug=slug,
            candidate_geometry_hashes=geometry_hashes,
            audit=audit,
        )
        graph_payload = graph.save()

        program["portfolio_vlm_audit"] = audit
        counts = program.get("counts")
        if isinstance(counts, dict):
            counts["portfolio_vlm_audit"] = audit
        summary["post_run_paid_portfolio_vlm"] = {
            "status": str(audit.get("status") or "unknown"),
            "hard_pass": bool(audit.get("hard_pass")),
            "program_slug": slug,
            "audit_path": str(audit_path),
            "response_id": str(audit.get("response_id") or ""),
            "graph_node_count": int(graph_payload.get("node_count") or 0),
            "graph_edge_count": int(graph_payload.get("edge_count") or 0),
        }
        _write_object(summary_path, summary)
        self.stdout.write(self.style.SUCCESS(
            f"paid portfolio VLM {audit.get('status')}: "
            f"{audit.get('visible_family_count', 0)} visible families; "
            f"dominant share {audit.get('dominant_family_share', 0)}"
        ))
