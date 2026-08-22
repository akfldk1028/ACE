from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from design.maas.book_language.cumulative_candidate_pool import (
    build_cumulative_candidate_pool,
    select_recovery_records,
)
from design.maas.book_language.legal_mass_archive_board import (
    render_legal_mass_archive_board,
)


LEDGER_FILENAME = "maas-cumulative-candidate-ledger.json"
JOURNAL_FILENAME = "maas-cumulative-flow-journal.json"


class Command(BaseCommand):
    help = "Recover an exact, deduplicated MASS candidate pool across compatible runs."

    def add_arguments(self, parser):
        parser.add_argument("--archive-root", action="append", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--pnu", required=True)
        parser.add_argument("--legal-floor-field-hash", default="")
        parser.add_argument("--floor-capacity-plan-hash", default="")
        parser.add_argument("--program-slug", default="neighborhood")
        parser.add_argument("--target-count", type=int, default=5)

    def handle(self, *args, **options):
        roots = [Path(value).resolve() for value in options["archive_root"]]
        missing_roots = [str(root) for root in roots if not root.exists()]
        if missing_roots:
            raise CommandError(f"archive roots do not exist: {', '.join(missing_roots)}")
        target_count = int(options["target_count"])
        if target_count < 1:
            raise CommandError("--target-count must be at least 1")
        output_dir = Path(options["output_dir"]).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        started_at = datetime.now(timezone.utc).isoformat()
        pool = build_cumulative_candidate_pool(
            roots,
            pnu=str(options["pnu"]),
            legal_floor_field_hash=str(options["legal_floor_field_hash"]),
            floor_capacity_plan_hash=str(options["floor_capacity_plan_hash"]),
        )
        selected_records = select_recovery_records(
            pool,
            target_count=target_count,
        )
        board = render_legal_mass_archive_board(
            output_dir=output_dir,
            program_slug=f"{options['program_slug']}-cumulative-recovery",
            target_count=target_count,
            selected_count=len(selected_records),
            archive_records=selected_records,
        )
        selected_identities = [
            {
                "geometry_hash": str(record.get("geometry_hash") or ""),
                "program_hash": str(record.get("program_hash") or ""),
                "surface_payload_hash": str(
                    record.get("final_surface_payload_hash") or ""
                ),
                "source_run_id": str(
                    (record.get("lineage") or {}).get("source_run_id") or ""
                ),
                "book_scope": str(
                    (record.get("scope") or {}).get("book_scope") or ""
                ),
                "family": str(record.get("family") or ""),
            }
            for record in selected_records
        ]
        ledger = {
            **pool,
            "selected_recovery_count": len(selected_records),
            "selected_recovery_identities": selected_identities,
            "recovery_board": board,
            "canonical_publishable_20": False,
            "canonical_note": (
                "Recovery evidence only; current candidate finalization and law graph "
                "gates remain authoritative."
            ),
        }
        journal = {
            "schema_version": "arr.maas.cumulative_candidate_flow_journal.v1",
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "context": pool["context"],
            "stages": [
                {
                    "stage": "exact_archives_discovered",
                    "archive_file_count": pool["archive_file_count"],
                    "malformed_archive_count": pool["malformed_archive_count"],
                },
                {
                    "stage": "legal_context_locked",
                    "compatible_record_count": pool["compatible_record_count"],
                    "incompatible_record_count": pool["incompatible_record_count"],
                },
                {
                    "stage": "exact_geometry_deduplicated",
                    "unique_candidate_count": pool["unique_candidate_count"],
                    "duplicate_record_count": pool["duplicate_record_count"],
                },
                {
                    "stage": "current_gate_status_classified",
                    "mass_eligible_unique_count": pool[
                        "mass_eligible_unique_count"
                    ],
                    "publishable_unique_count": pool["publishable_unique_count"],
                },
                {
                    "stage": "recovery_candidates_selected",
                    "selected_recovery_count": len(selected_records),
                    "selected_geometry_hashes": [
                        identity["geometry_hash"] for identity in selected_identities
                    ],
                },
                {
                    "stage": "exact_board_rendered",
                    "png_path": board["png_path"],
                    "png_sha256": board["png_sha256"],
                    "card_count": board["card_count"],
                },
            ],
        }
        ledger_path = output_dir / LEDGER_FILENAME
        journal_path = output_dir / JOURNAL_FILENAME
        _write_json_atomic(ledger_path, ledger)
        _write_json_atomic(journal_path, journal)
        self.stdout.write(
            self.style.SUCCESS(
                " ".join(
                    (
                        f"compatible={pool['compatible_record_count']}",
                        f"unique={pool['unique_candidate_count']}",
                        f"mass_eligible={pool['mass_eligible_unique_count']}",
                        f"publishable={pool['publishable_unique_count']}",
                        f"selected={len(selected_records)}/{target_count}",
                        f"ledger={ledger_path}",
                        f"png={board['png_path']}",
                    )
                )
            )
        )


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    temporary = path.with_name(
        f".{path.name}.{hashlib.sha256(encoded).hexdigest()[:12]}.tmp"
    )
    temporary.write_bytes(encoded)
    temporary.replace(path)
