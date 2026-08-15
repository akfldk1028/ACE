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
from design.maas.massv2 import postcondition
from design.maas.massv2 import program as programme
from design.maas.massv2.author import _to_form
from design.maas.massv2.execute import execute as execute_parti
from design.maas.massv2.grammar import parti_from_record
from design.maas.massv2.legal import LegalSiteUnavailable, load_legal_site
from design.maas.massv2.fill import fill_to_site
from design.maas.massv2.sampler import read_facts, sample_sentences
from design.maas.massv2.render import render_masses
from design.maas.massv2.select import Candidate, choose, summary as selection_summary
from design.maas.massv2.seeds import seed_forms
from design.maas.massv2.siting import open_side_direction, spread_across_siting
from design.maas.massv2.variations import spread_across_coverage


def _is_authored(form) -> bool:
    """A composition somebody chose, as opposed to a deterministic seed family.

    Only these are carried along the coverage and siting axes: a seed family is
    already a sweep, and spreading it again just multiplies the same box. The
    test used to be the `llm_` name prefix, which silently excluded sentences
    drawn from the parcel by the sampler - they carry a parti like any other
    authored sentence, so that is what the test reads now.
    """

    return bool(form.extra.get("parti")) or form.name.startswith("llm_")


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
            "--parti-json",
            action="append",
            help=(
                "Path to a file of authored parti sentences - ordered "
                "operation lists rather than volume coordinates. The seed "
                "comes from the parcel, so the site is present from the first "
                "move instead of arriving at the end as a cutter."
            ),
        )
        parser.add_argument(
            "--authored-only",
            action="store_true",
            help="Skip the deterministic seed families and use only authored schemes.",
        )
        parser.add_argument(
            "--sample",
            type=int,
            default=0,
            help=(
                "Draw N sentences from the parcel itself rather than from a file. "
                "Magnitudes and reasons are read off this site's own limits, so "
                "the vocabulary is not inherited from the parcel it was written on."
            ),
        )
        parser.add_argument(
            "--program-json",
            help=(
                "A 실별 소요면적표 file. The sentence still says which operations "
                "and where they aim; the schedule says how much of the building "
                "each volume holds."
            ),
        )
        parser.add_argument(
            "--program-name",
            help="Which schedule in the file to use. Defaults to the first.",
        )
        parser.add_argument(
            "--program-weight",
            type=float,
            default=1.0,
            help=(
                "0 leaves the sentence's own proportions, 1 hands the volume "
                "sizes to the schedule, between the two mixes them."
            ),
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
            "--alt-png",
            action="store_true",
            help="Also write one large PNG per delivered alternative, alt-NN.png.",
        )
        parser.add_argument(
            "--spread-siting",
            action="store_true",
            help="Carry each authored composition to each position it can take on the parcel.",
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

        schedule = None
        if options["program_json"]:
            book = json.loads(Path(options["program_json"]).read_text(encoding="utf-8"))
            wanted = options["program_name"]
            for record in book.get("schedules") or ():
                if wanted is None or record.get("name") == wanted:
                    schedule = programme.schedule_from_record(record)
                    break
            if schedule is None:
                raise CommandError("no schedule matched")
            self.stdout.write(json.dumps(
                {k: v for k, v in schedule.evidence().items() if k != "rooms"},
                ensure_ascii=False,
            ))
            self.stdout.write(
                f"programme weight {options['program_weight']}  "
                f"fits FAR: {schedule.fits(far_capacity_m2=site.far_capacity_m2)}"
            )

        if options["parti_json"] or options["sample"]:
            buildable = site.plan_at(0.0)
            axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
            sentences = []
            for path in options["parti_json"] or ():
                sentences.extend(
                    json.loads(Path(path).read_text(encoding="utf-8")).get("schemes") or ()
                )
            if options["sample"]:
                facts = read_facts(site)
                self.stdout.write(json.dumps(facts.evidence(), ensure_ascii=False))
                drawn = sample_sentences(facts, limit=options["sample"])
                sentences.extend(drawn)
                self.stdout.write(f"sampled sentences: {len(drawn)}")
            written = []
            mute = []
            authored_height = site.floor_height_m * max(
                1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2))
            )
            for record in sentences:
                parti = parti_from_record(record)
                if parti is None:
                    continue
                # Judge the sentence, not its variants: a word that redraws
                # nothing at the size it was written redraws nothing at any
                # coverage or siting derived from it.
                spoken = postcondition.check_sentence(
                    parti,
                    buildable=buildable,
                    axis=axis,
                    height_m=authored_height,
                    allowed_at=site.plan_at,
                    storey_height_m=site.floor_height_m,
                )
                if not spoken.honest:
                    mute.append((parti.name, spoken))
                    continue
                built = execute_parti(
                    parti, buildable=buildable, axis=axis, height_m=authored_height,
                    storey_height_m=site.floor_height_m,
                )
                if built is not None:
                    if schedule is not None:
                        built = programme.resized_to(
                            built, schedule,
                            weight=options["program_weight"],
                            storey_height_m=site.floor_height_m,
                        )
                    written.append(built)
            forms.extend(written)
            self.stdout.write(
                f"parti sentences: {len(written)} spoken, {len(mute)} with a silent word"
            )
            for name, spoken in mute:
                self.stdout.write(
                    f"  silent: {name} -> {','.join(spoken.silent)} "
                    f"{[round(v, 3) for v in spoken.changed]}"
                )

        if options["spread_coverage"]:
            # A composition is one thing; the ground it claims is another. Carry
            # each authored composition across the coverage axis so the grid
            # fills from the vocabulary rather than from more hand authoring.
            spread = [
                variant
                for form in list(forms)
                if _is_authored(form)
                for variant in spread_across_coverage(
                    form,
                    ground_capacity_m2=site.ground_capacity_m2,
                    far_capacity_m2=site.far_capacity_m2,
                    floor_height_m=site.floor_height_m,
                )
            ]
            forms.extend(spread)
            self.stdout.write(f"coverage variants: {len(spread)}")

        if options["spread_siting"]:
            # Where a scheme stands is a decision the archive was making once,
            # for everything, by centring it. A low-coverage scheme has room to
            # hold one end and leave a yard, and that is a different proposal.
            buildable = site.plan_at(0.0)
            open_side = open_side_direction(buildable, site.shared_edges)
            self.stdout.write(
                f"open side: {open_side}"
                if open_side
                else "open side: unknown, siting on the parcel's own axes"
            )
            placed = [
                variant
                for form in list(forms)
                if _is_authored(form)
                for variant in spread_across_siting(
                    form, buildable=buildable, open_side=open_side
                )
            ]
            forms.extend(placed)
            self.stdout.write(f"siting variants: {len(placed)}")

        records = []
        renderable = []
        pool: list[Candidate] = []
        cells: collections.Counter[str] = collections.Counter()
        unlawful = 0
        implausible = 0

        for form in forms:
            # A brief asks for a size; the law only forbids one. Growth aims at
            # whichever of the two the scheme actually has.
            wanted = form.extra.get("programme_target")
            filled = fill_to_site(
                form,
                site,
                allow_plan_growth=not options["no_fill"],
                target_utilization=(
                    float(wanted) / max(site.far_capacity_m2, 1e-9)
                    if wanted else None
                ),
            )
            fit = filled.fit
            # The same clip the legal fit measured through. Compiling without
            # it is how the sheet came to print 용적률 of 1.52 on a run the fit
            # certified lawful - two measures of one building again.
            source = compile_matrix_form(
                fit.form,
                storey_height_m=site.floor_height_m,
                allowed_at=site.plan_at,
            )
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
                floor_height_m=site.floor_height_m,
            )
            storey_h = float(
                source.metadata.get("authored_floor_height_m") or site.floor_height_m
            )
            gfa = gross_floor_area_m2(source, floor_height_m=storey_h)
            far_use = gfa / max(site.far_capacity_m2, 1e-9)
            take = fit.ground_area_m2 / max(site.ground_capacity_m2, 1e-9)
            # With a brief, the coverage axis stops meaning anything: a
            # 1,428 m² schedule on a 2,500 m² parcel cannot reach the full
            # band however it is composed, and the grid emptied. What the
            # brief does give is a decision worth an axis - where its one big
            # room went - which Korean practice treats as a discrete choice
            # between a detached volume, the base, a middle floor and the top.
            if schedule is not None:
                cell = (
                    f"{programme.large_span_strategy(source, storey_height_m=site.floor_height_m)}"
                    f"|{measurement.void_band_id}"
                )
            else:
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

        if options["alt_png"]:
            # A contact sheet is for comparing; one drawing per alternative is
            # for looking at. Same renderer, one tile, four times the size.
            for index, item in enumerate(renderable, start=1):
                render_masses(
                    [item],
                    output / f"alt-{index:02d}.png",
                    site_ring=site_ring,
                    columns=1,
                    tile=(900, 760),
                )
            (output / "alts.json").write_text(
                json.dumps(
                    {
                        "schema_version": "arr.maas.massv2_alternatives.v1",
                        "site": site.evidence(),
                        "alternatives": [
                            {"index": i, "png": f"alt-{i:02d}.png", "name": n, **cap}
                            for i, (n, _src, cap) in enumerate(renderable, start=1)
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.stdout.write(f"wrote {len(renderable)} alternative drawings")

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
