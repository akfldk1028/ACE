import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas import generate_legal_mass_variants
from design.maas.service_cache import request_cache_key, store_verified_result


class Command(BaseCommand):
    help = "Generate a verified MAAS review set offline and atomically publish it to the service cache."

    def add_arguments(self, parser):
        parser.add_argument("payload", help="Path to the legal-variants request JSON")

    def handle(self, *args, **options):
        payload_path = Path(options["payload"]).expanduser().resolve()
        try:
            body = json.loads(payload_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CommandError(f"cannot load payload: {exc}") from exc
        mass_geojson = body.get("mass_geojson")
        site_polygon = body.get("site_polygon")
        if not isinstance(mass_geojson, dict) or not isinstance(site_polygon, dict):
            raise CommandError("payload requires mass_geojson and site_polygon")
        result = generate_legal_mass_variants(
            mass_geojson=mass_geojson,
            site_polygon_geojson=site_polygon,
            constraints=body.get("constraints") if isinstance(body.get("constraints"), list) else [],
            building_type=body.get("building_type") if isinstance(body.get("building_type"), str) else "공동주택",
            max_variants=int(body.get("max_variants") or 20),
            sunlight_envelope=body.get("sunlight_envelope") if isinstance(body.get("sunlight_envelope"), dict) else None,
            setback_geometries=body.get("setback_geometries") if isinstance(body.get("setback_geometries"), dict) else None,
            include_interactive_seed=bool(body.get("include_interactive_seed")),
            preferred_operator=body.get("preferred_operator") if isinstance(body.get("preferred_operator"), str) else None,
            pnu=body.get("pnu") if isinstance(body.get("pnu"), str) else None,
            parking_options=body.get("parking_options") if isinstance(body.get("parking_options"), dict) else None,
        )
        key = request_cache_key(body)
        path = store_verified_result(key, result)
        self.stdout.write(self.style.SUCCESS(json.dumps({"status": "published", "cache_key": key, "path": str(path)})))
