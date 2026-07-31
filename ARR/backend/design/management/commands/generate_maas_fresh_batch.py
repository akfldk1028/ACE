"""Generate a bounded, program-neutral batch of fresh MASS executions."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas.fresh_batch import generate_fresh_mass_batch


class Command(BaseCommand):
    help = (
        "Generate up to ten unique fresh MASS programs through UnitBox, BOOK, "
        "compiler/GATE, render and elevation evidence. No image API is called."
    )

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", required=True, type=str)
        parser.add_argument("--count", default=10, type=int)
        parser.add_argument("--building-type", default="building mass", type=str)
        parser.add_argument("--output-root", default="", type=str)

    def handle(self, *args, **options):
        count = int(options["count"])
        if count < 1 or count > 10:
            raise CommandError("--count must be between 1 and 10")
        output_root = Path(options["output_root"]).resolve() if options["output_root"] else (
            Path(__file__).resolve().parents[5]
            / "docs"
            / "ai-session-memory"
            / "maas-service-cache"
            / "single-executions"
        ).resolve()
        payload = generate_fresh_mass_batch(
            output_root,
            batch_id=str(options["batch_id"]),
            building_type=str(options["building_type"]),
            count=count,
        )
        self.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        if payload["accepted_count"] != payload["requested_count"]:
            raise CommandError(
                f"fresh MASS batch incomplete: "
                f"{payload['accepted_count']}/{payload['requested_count']}"
            )
