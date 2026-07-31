"""Run an explicitly confirmed, bounded post-run MASS VLM audit."""

import json

from django.core.management.base import BaseCommand, CommandError

from design.maas.geometry_language.executed_vlm_audit import audit_executed_masses_with_openai_vlm


class Command(BaseCommand):
    help = "Audit actual archived MASS PNGs with actual retrieved reference images"

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--index", action="append", type=int, required=True)
        parser.add_argument("--model", default=None)
        parser.add_argument("--reference-limit", type=int, default=3)
        parser.add_argument(
            "--confirm-live",
            default="",
            help="Must equal EXECUTED-MASS-LIVE; otherwise zero paid requests are made",
        )

    def handle(self, *args, **options):
        if options.get("confirm_live") != "EXECUTED-MASS-LIVE":
            raise CommandError("live audit confirmation must be exactly EXECUTED-MASS-LIVE")
        try:
            result = audit_executed_masses_with_openai_vlm(
                run_id=str(options["run_id"]),
                indices=options["index"],
                model=options.get("model"),
                reference_limit=int(options.get("reference_limit") or 3),
            )
        except Exception as exc:
            raise CommandError(f"executed MASS VLM audit failed: {type(exc).__name__}: {exc}") from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
