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
from design.maas.massv2.measure import gross_floor_area_m2
from design.maas.massv2 import plausibility as plaus
from design.maas.massv2.author import _to_form
from design.maas.massv2.legal import LegalSiteUnavailable, load_legal_site
from design.maas.massv2.fill import fill_to_site
from design.maas.massv2.render import render_masses
from design.maas.massv2.select import Candidate, choose, summary as selection_summary
from design.maas.massv2.seeds import seed_forms
from design.maas.massv2.variations import spread_across_coverage


class Command(BaseCommand):
    help = "Generate matrix-form masses on a live parcel and report the grid."

    def add_arguments(self, parser):
        parser.add_argument("--pnu", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--building-type", default="제1종근린생활시설")
        parser.add_argument(
            "--authored-json",
            action="append",
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
        parser.add_argument(
            "--no-fill",
            action="store_true",
            help="Skip the growth loop and report schemes at the size they were authored.",
        )
        parser.add_argument(
            "--per-cell",
            type=int,
            default=0,
            help="Keep only the best N per grid cell after deduping compositions.",
        )
        parser.add_argument(
            "--spread-coverage",
            action="store_true",
            help="Carry each authored composition across all four coverage bands.",
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
            records = []
            for path in options["authored_json"]:
                records.extend(
                    json.loads(Path(path).read_text(encoding="utf-8")).get("schemes") or ()
                )
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
                for record in records
            ]
            forms.extend(item for item in authored if item is not None)
            self.stdout.write(f"authored schemes: {sum(1 for i in authored if i)}")

        if options["spread_coverage"]:
            # A composition is one thing; the ground it claims is another. Carry
            # each authored composition across the coverage axis so the grid
            # fills from the vocabulary rather than from more hand authoring.
            spread = [
                variant
                for form in list(forms)
                if form.name.startswith("llm_")
                for variant in spread_across_coverage(
                    form,
                    ground_capacity_m2=site.ground_capacity_m2,
                    far_capacity_m2=site.far_capacity_m2,
                    floor_height_m=site.floor_height_m,
                )
            ]
            forms.extend(spread)
            self.stdout.write(f"coverage variants: {len(spread)}")

        records = []
        renderable = []
        pool: list[Candidate] = []
        cells: collections.Counter[str] = collections.Counter()
        unlawful = 0
        implausible = 0

        for form in forms:
            filled = fill_to_site(form, site, allow_plan_growth=not options["no_fill"])
            fit = filled.fit
            source = compile_matrix_form(fit.form, storey_height_m=site.floor_height_m)
            if source is None:
                records.append({"name": form.name, "status": "compile_failed"})
                continue
            measurement = measure_form(source)
            standing = plaus.assess(
                source,
                parcel_area_m2=site.parcel_area_m2,
                max_slenderness=plaus.slenderness_limit(
                    far_capacity_m2=site.far_capacity_m2,
                    ground_capacity_m2=site.ground_capacity_m2,
                ),
            )
            storey_h = float(
                source.metadata.get("authored_floor_height_m") or site.floor_height_m
            )
            gfa = gross_floor_area_m2(source, floor_height_m=storey_h)
            far_use = gfa / max(site.far_capacity_m2, 1e-9)
            take = fit.ground_area_m2 / max(site.ground_capacity_m2, 1e-9)
            ground_band = delivered_ground_take_band(take).band_id
            cell = f"{ground_band}|{measurement.void_band_id}"
            cells[cell] += 1
            if not fit.satisfied:
                unlawful += 1
            if not standing.occupiable:
                implausible += 1
            records.append({
                "name": form.name,
                "status": "compiled",
                "cell": cell,
                "legal_fit": fit.evidence(),
                "fill": filled.evidence(),
                "gfa_m2": round(gfa, 1),
                "floor_height_m": storey_h,
                "far_utilization": round(far_use, 4),
                "plausibility": standing.evidence(),
                "measurement": measurement.evidence(),
                "language": {
                    "primary": form.primary_language,
                    "secondary": form.secondary_language,
                    "formal_principle": form.formal_principle,
                },
            })
            pool.append(Candidate(
                form=fit.form, source=source, measurement=measurement,
                plausibility=standing, cell=cell, ground_take=take,
                far_utilization=far_use,
            ))
            renderable.append((
                form.name,
                source,
                {
                    "artic": f"{measurement.articulation():.2f}",
                    "take": f"{take:.2f}",
                    "far": f"{far_use:.2f}",
                    "cell": cell.replace("_ground", "").replace("_body", "").replace("_figure", ""),
                },
            ))

        selection = None
        if options["per_cell"] > 0:
            chosen = choose(pool, per_cell=options["per_cell"])
            selection = selection_summary(chosen, considered=len(pool))
            renderable = [
                (
                    item.form.name,
                    item.source,
                    {
                        "artic": f"{item.measurement.articulation():.2f}",
                        "take": f"{item.ground_take:.2f}",
                        "far": f"{item.far_utilization:.2f}",
                        "cell": item.cell.replace("_ground", "").replace("_body", "").replace("_figure", ""),
                    },
                )
                for item in chosen
            ]
            self.stdout.write(
                f"selected {len(chosen)} from {len(pool)} "
                f"({selection['distinct_compositions']} distinct compositions)"
            )

        site_ring = [(float(x), float(y)) for x, y in site.site_local_utm.exterior.coords[:-1]]
        sheet = render_masses(renderable, output / "massv2-sheet.png", site_ring=site_ring)

        summary = {
            "schema_version": "arr.maas.massv2_run.v1",
            "site": site.evidence(),
            "form_count": len(forms),
            "compiled": len(renderable),
            "unlawful": unlawful,
            "implausible": implausible,
            "occupied_cells": len(cells),
            "cells": dict(sorted(cells.items())),
            "selection": selection,
            "records": records,
        }
        (output / "massv2-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self.stdout.write(
            f"compiled {len(renderable)}/{len(forms)}  "
            f"unlawful {unlawful}  implausible {implausible}  cells {len(cells)}/16"
        )
        self.stdout.write(str(sheet))
