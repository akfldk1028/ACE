"""Export the current structured BOOK/MASS/VLM memory contract."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from design.maas.language_memory import build_language_visual_memory, workspace_root


class Command(BaseCommand):
    help = "Export the MAAS language manifest and MASS PNG memory binding contract"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(workspace_root() / "docs" / "ai-session-memory" / "maas-language-visual-memory-current.json"),
        )
        parser.add_argument("--frontend-png", default=None)

    def handle(self, *args, **options):
        output = Path(options["output"])
        payload = build_language_visual_memory(frontend_png=options.get("frontend_png"))
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output)
        self.stdout.write(str(output))
