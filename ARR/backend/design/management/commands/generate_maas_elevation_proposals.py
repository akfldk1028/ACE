from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from design.maas.aesthetic.adapters import OpenAIImageAdapter
from design.maas.elevation_proposal_batch import generate_batch_elevation_proposals


class Command(BaseCommand):
    help = "Generate at most one facade image proposal per inspected MASS."

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", required=True)
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--provider", choices=("gpt-image",), default="gpt-image")
        parser.add_argument("--output-root", default="")

    def handle(self, *args, **options):
        root = Path(options["output_root"]).resolve() if options["output_root"] else (
            Path(settings.BASE_DIR).resolve().parents[1]
            / "docs"
            / "ai-session-memory"
            / "maas-service-cache"
            / "single-executions"
        ).resolve()
        adapter = OpenAIImageAdapter(
            output_dir=root / "_provider_outputs" / str(options["batch_id"])
        )
        try:
            payload = generate_batch_elevation_proposals(
                root,
                batch_id=str(options["batch_id"]),
                adapter=adapter,
                limit=int(options["limit"]),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
