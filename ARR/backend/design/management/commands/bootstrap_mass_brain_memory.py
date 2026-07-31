import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from design import config
from design.maas.historical_memory import build_historical_envelope
from design.maas.preference.reference_corpus import load_reference_tree
from design.models import DesignResult


class Command(BaseCommand):
    help = "Ingest bounded local ARR references and evaluated designs into Mass-Brain."

    def add_arguments(self, parser):
        default_root = Path(settings.BASE_DIR).parent.parent / "docs" / "ai-session-memory" / "reference-corpus"
        parser.add_argument("--reference-root", default=str(default_root))
        parser.add_argument("--reference-limit", type=int, default=500)
        parser.add_argument("--design-limit", type=int, default=500)
        parser.add_argument("--project-key", default="arr-global-precedents")
        parser.add_argument("--output", help="Write the envelope instead of posting it")

    def handle(self, *args, **options):
        reference_root = Path(options["reference_root"]).expanduser().resolve()
        references = load_reference_tree(reference_root)[:max(0, options["reference_limit"])]
        designs = list(
            DesignResult.objects.filter(is_feasible=True)
            .exclude(mass_geojson=None)
            .order_by("-is_pareto_optimal", "ranking", "-id")[:max(0, options["design_limit"])]
        )
        envelope = build_historical_envelope(
            references=references,
            design_results=designs,
            project_key=options["project_key"],
        )
        if options.get("output"):
            output = Path(options["output"]).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(json.dumps({"status": "written", "path": str(output), "references": len(references), "designs": len(designs)})))
            return
        try:
            response = config.mass_brain_client.post("/v1/contracts/ingest", json=envelope)
            response.raise_for_status()
        except Exception as exc:
            raise CommandError(f"Mass-Brain ingest failed: {exc}") from exc
        self.stdout.write(self.style.SUCCESS(json.dumps({"status": "ingested", "references": len(references), "designs": len(designs), "response": response.json()})))

