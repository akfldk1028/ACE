"""Generate MASS v2 candidates on a real parcel and report the delivered grid.

    python manage.py generate_massv2 --pnu 4115011300106840001 \
        --output-dir tmp_mass_check/v2-001

Runs the whole v2 path: live legal limits, the seed families sized from those
limits, per-volume legal fit, measurement on both grid axes, and a contact
sheet. No certification layer, no VLM, no 35-minute portfolio solve - this
command exists to answer one question, which is whether the form language
produces masses worth looking at.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas.design_space import delivered_ground_take_band
from design.maas.massv2 import compile_matrix_form, measure_form
from design.maas.massv2.author import _to_form
from design.maas.massv2.legal import LegalSiteUnavailable, load_legal_site
from design.maas.massv2.legal_fit import fit_to_site
from design.maas.massv2.render import render_masses
from design.maas.massv2.seeds import seed_forms


class Command(BaseCommand):
    help = "Generate matrix-form masses on a live parcel and report the grid."

    def add_arguments(self, parser):
        parser.add_argument("--pnu", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--building-type", default="제1종근린생활시설")
        parser.add_argument(
            "--authored-json",
            help=(
                "Path to a model-authored schemes file matching the authoring "
                "schema. Lets an assistant author the programs directly when no "
                "API credential is usable, which is the same contract - the "
                "model writes a program, the executor owns the metres."
            ),
        )
        parser.add_argument(
            "--authored-only",
            action="store_true",
            help="Skip the deterministic seed families and use only authored schemes.",
        )

    def handle(self, *args, **options):
        output = Path(options["output_dir"])
        output.mkdir(parents=True, exist_ok=True)

        try:
            site = load_legal_site(options["pnu"], building_type=options["building_type"])
        except LegalSiteUnavailable as error:
            raise CommandError(str(error)) from error

        self.stdout.write(json.dumps(site.evidence(), ensure_ascii=False))

        forms = []
        if not options["authored_only"]:
            forms.extend(seed_forms(
                ground_capacity_m2=site.ground_capacity_m2,
                far_capacity_m2=site.far_capacity_m2,
                floor_height_m=site.floor_height_m,
            ))

        if options["authored_json"]:
            buildable = site.plan_at(0.0)
            min_x, min_y, max_x, max_y = buildable.bounds
            payload = json.loads(Path(options["authored_json"]).read_text(encoding="utf-8"))
            authored = [
                _to_form(
                    record,
                    width_m=max_x - min_x,
                    depth_m=max_y - min_y,
                    # Legal height is what the FAR capacity affords over a full
                    # footprint; the fit will pull anything taller back in.
                    height_m=site.floor_height_m
                    * max(1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2))),
                )
                for record in payload.get("schemes") or ()
            ]
            forms.extend(item for item in authored if item is not None)
            self.stdout.write(f"authored schemes: {sum(1 for i in authored if i)}")

        records = []
        renderable = []
        cells: collections.Counter[str] = collections.Counter()
        unlawful = 0

        for form in forms:
            fit = fit_to_site(form, site)
            source = compile_matrix_form(fit.form)
            if source is None:
                records.append({"name": form.name, "status": "compile_failed"})
                continue
            measurement = measure_form(source)
            take = fit.ground_area_m2 / max(site.ground_capacity_m2, 1e-9)
            ground_band = delivered_ground_take_band(take).band_id
            cell = f"{ground_band}|{measurement.void_band_id}"
            cells[cell] += 1
            if not fit.satisfied:
                unlawful += 1
            records.append({
                "name": form.name,
                "status": "compiled",
                "cell": cell,
                "legal_fit": fit.evidence(),
                "measurement": measurement.evidence(),
                "language": {
                    "primary": form.primary_language,
                    "secondary": form.secondary_language,
                    "formal_principle": form.formal_principle,
                },
            })
            renderable.append((
                form.name,
                source,
                {
                    "artic": f"{measurement.articulation():.2f}",
                    "take": f"{take:.2f}",
                    "cell": cell.replace("_ground", "").replace("_body", "").replace("_figure", ""),
                },
            ))

        site_ring = [(float(x), float(y)) for x, y in site.site_local_utm.exterior.coords[:-1]]
        sheet = render_masses(renderable, output / "massv2-sheet.png", site_ring=site_ring)

        summary = {
            "schema_version": "arr.maas.massv2_run.v1",
            "site": site.evidence(),
            "form_count": len(forms),
            "compiled": len(renderable),
            "unlawful": unlawful,
            "occupied_cells": len(cells),
            "cells": dict(sorted(cells.items())),
            "records": records,
        }
        (output / "massv2-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self.stdout.write(
            f"compiled {len(renderable)}/{len(forms)}  "
            f"unlawful {unlawful}  cells {len(cells)}/16"
        )
        self.stdout.write(str(sheet))
