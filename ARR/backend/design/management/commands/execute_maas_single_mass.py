"""Execute one MASS AST without invoking the portfolio benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas.geometry_language import GeometryProgram, architectural_shape_programs
from design.maas.geometry_language.executed_archive import (
    compile_executed_mass,
    materialize_executed_mass_passport,
)
from design.maas.single_execution import execute_single_mass
from design.maas.single_execution.replay import downstream_evidence_from_passport


class Command(BaseCommand):
    help = (
        "Compile, gate, render, and trace exactly one MASS. "
        "Use --shape-index, --program-json, or --run-id with --mass-index."
    )

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group()
        source.add_argument("--shape-index", type=int)
        source.add_argument("--program-json", type=str)
        source.add_argument("--run-id", type=str)
        parser.add_argument("--mass-index", type=int, default=1)
        parser.add_argument("--execution-id", type=str, default="")
        parser.add_argument(
            "--execution-mode",
            choices=("explicit_program", "fresh_synthesis"),
            default="explicit_program",
        )
        parser.add_argument("--title", type=str, default="")
        parser.add_argument("--output-root", type=str, default="")

    def handle(self, *args, **options):
        program, downstream_evidence = self._execution_source(options)
        output_root = Path(options["output_root"]).resolve() if options["output_root"] else (
            Path(__file__).resolve().parents[5]
            / "docs" / "ai-session-memory" / "maas-service-cache" / "single-executions"
        ).resolve()
        result = execute_single_mass(
            program,
            output_root=output_root,
            execution_id=str(options["execution_id"] or ""),
            title=str(options["title"] or ""),
            downstream_evidence=downstream_evidence,
            execution_mode=(
                "exact_replay"
                if options.get("run_id")
                else str(options.get("execution_mode") or "explicit_program")
            ),
            source_run_id=str(options.get("run_id") or ""),
            source_mass_index=int(options["mass_index"]) if options.get("run_id") else 0,
        )
        self.stdout.write(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))

    def _execution_source(
        self,
        options,
    ) -> tuple[GeometryProgram, dict[str, dict] | None]:
        if options.get("program_json"):
            path = Path(str(options["program_json"])).resolve()
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise CommandError(f"cannot read GeometryProgram JSON: {exc}") from exc
            if isinstance(payload, dict) and isinstance(payload.get("geometryProgram"), dict):
                payload = payload["geometryProgram"]
            try:
                return GeometryProgram.from_dict(payload), None
            except (TypeError, ValueError) as exc:
                raise CommandError(f"invalid GeometryProgram JSON: {exc}") from exc
        if options.get("run_id"):
            try:
                compilation, _, _, _ = compile_executed_mass(
                    int(options["mass_index"]),
                    str(options["run_id"]),
                )
                source_passport = materialize_executed_mass_passport(
                    int(options["mass_index"]),
                    str(options["run_id"]),
                )
            except (OSError, ValueError, IndexError, KeyError) as exc:
                raise CommandError(f"cannot replay archived MASS: {exc}") from exc
            return (
                compilation.program,
                downstream_evidence_from_passport(source_passport),
            )
        shape_index = int(options.get("shape_index") or 1)
        programs = architectural_shape_programs()
        if not 1 <= shape_index <= len(programs):
            raise CommandError(f"shape-index must be between 1 and {len(programs)}")
        return programs[shape_index - 1], None
