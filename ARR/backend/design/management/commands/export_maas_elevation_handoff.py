import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas.geometry_language.elevation_handoff import write_executed_mass_elevation_handoff


class Command(BaseCommand):
    help = "Export one exact executed GeometryProgram MASS for elevationAgent"

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--index", required=True, type=int)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            path = write_executed_mass_elevation_handoff(
                run_id=str(options["run_id"]),
                index=int(options["index"]),
                output_path=Path(options["output"]),
            )
        except Exception as exc:
            raise CommandError(f"elevation handoff export failed: {type(exc).__name__}: {exc}") from exc
        self.stdout.write(json.dumps({"status": "exported", "path": str(path)}, ensure_ascii=False))
