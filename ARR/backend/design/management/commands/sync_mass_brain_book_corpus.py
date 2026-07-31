"""Publish the audited architect BOOK registry to Mass-Brain."""

from django.core.management.base import BaseCommand

from design.maas.mass_brain import sync_book_language_corpus


class Command(BaseCommand):
    help = "Sync the audited 69-page BOOK language registry to Mass-Brain"

    def handle(self, *args, **options):
        result = sync_book_language_corpus()
        if result.get("status") != "synced":
            raise RuntimeError(result.get("error") or "BOOK corpus sync failed")
        self.stdout.write(self.style.SUCCESS(
            "BOOK corpus synced: "
            f"{result.get('pageCount')} pages, "
            f"{result.get('baseOperativeCount')} base operations, "
            f"{result.get('principleCount')} executable principles"
        ))
