"""Inspect or explicitly populate the content-addressed BOOK scan VLM cache."""

import json

from django.core.management.base import BaseCommand, CommandError

from design.maas.book_language.book_scan_vlm_audit import audit_pages, audit_status


class Command(BaseCommand):
    help = "Report BOOK scan VLM cache status; live calls require an explicit confirmation phrase"

    def add_arguments(self, parser):
        parser.add_argument("--page", action="append", type=int)
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--model", default=None)
        parser.add_argument(
            "--confirm-live",
            default="",
            help="Must equal BOOK-69-LIVE; omitted means status/cache-only and makes zero API requests",
        )

    def handle(self, *args, **options):
        pages = options.get("page") or []
        if options.get("all"):
            pages = list(range(1, 70))
        if not pages:
            self.stdout.write(json.dumps(audit_status(model=options.get("model")), ensure_ascii=False, indent=2))
            return
        invalid = [page for page in pages if not 1 <= int(page) <= 69]
        if invalid:
            raise CommandError(f"BOOK pages must be 1..69: {invalid}")
        confirmed = options.get("confirm_live") == "BOOK-69-LIVE"
        if options.get("confirm_live") and not confirmed:
            raise CommandError("live audit confirmation must be exactly BOOK-69-LIVE")
        results = audit_pages(pages=pages, confirm_live=confirmed, model=options.get("model"))
        self.stdout.write(json.dumps(results, ensure_ascii=False, indent=2))
