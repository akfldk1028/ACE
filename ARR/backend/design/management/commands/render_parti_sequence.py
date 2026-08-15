"""Draw a parti the way its authors publish one: one frame per move.

    python manage.py render_parti_sequence --pnu 4115011300106840001 \
        --parti-json tmp_mass_check/_massv2/inputs/parti-a.json \
        --name llm_a_lifted_back_court \
        --output-dir tmp_mass_check/_massv2/partis

The masses were already being generated from ordered operation lists, and each
operation already carried the reason its author wrote for it. Only the last
word of the sentence was ever drawn. Across BIG, OMA and SANAA the massing is
published as the sequence - one diagram per caption - so this renders what was
being thrown away rather than generating anything new.

The final frame is the delivered mass: the same sentence after the growth loop
has taken it to the parcel's limits and the legal fit has certified it. The
jump between the last authored move and that frame is the law and the capacity
acting, which is the part of the argument that is ours rather than theirs.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas.massv2 import compile_matrix_form, measure_form
from design.maas.massv2.execute import execute_steps
from design.maas.massv2.fill import fill_to_site
from design.maas.massv2.grammar import parti_from_record
from design.maas.massv2.legal import LegalSiteUnavailable, load_legal_site
from design.maas.massv2.measure import gross_floor_area_m2
from design.maas.massv2.render import render_sequence
from design.maas.massv2.siting import open_side_direction


# What the author aimed the move at. Magnitude is geometric and belongs to the
# executor; direction is programmatic and is the only thing the author states.
_AIM_KEYS = ("on", "at", "toward", "align")


def _aim(op) -> str:
    parts = [f"{key}: {op.params[key]}" for key in _AIM_KEYS if op.params.get(key)]
    return " · ".join(parts)


class Command(BaseCommand):
    help = "Render one authored parti as a captioned sequence of moves."

    def add_arguments(self, parser):
        parser.add_argument("--pnu", required=True)
        parser.add_argument("--parti-json", action="append", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--building-type", default="제1종근린생활시설")
        parser.add_argument(
            "--name",
            action="append",
            help="Sentence to draw. Repeatable; omit to draw every sentence given.",
        )

    def handle(self, *args, **options):
        output = Path(options["output_dir"])
        output.mkdir(parents=True, exist_ok=True)

        try:
            site = load_legal_site(options["pnu"], building_type=options["building_type"])
        except LegalSiteUnavailable as error:
            raise CommandError(str(error)) from error

        buildable = site.plan_at(0.0)
        axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
        height = site.floor_height_m * max(
            1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2))
        )

        records = []
        for path in options["parti_json"]:
            records.extend(
                json.loads(Path(path).read_text(encoding="utf-8")).get("schemes") or ()
            )
        wanted = set(options["name"] or ())
        if wanted:
            records = [item for item in records if item.get("name") in wanted]
        if not records:
            raise CommandError("no sentence matched")

        site_ring = [(float(x), float(y)) for x, y in site.site_local_utm.exterior.coords[:-1]]
        written = 0

        for record in records:
            parti = parti_from_record(record)
            if parti is None:
                continue
            steps = execute_steps(
                parti, buildable=buildable, axis=axis, height_m=height,
                storey_height_m=site.floor_height_m,
            )
            if not steps:
                continue

            frames = []
            for op, form in steps:
                # Drawn through the same clip the delivered mass is measured
                # through. A parti that reads as lawful only until the last
                # frame is not the argument this system is making.
                source = compile_matrix_form(
                    form, storey_height_m=site.floor_height_m, allowed_at=site.plan_at
                )
                if source is None:
                    continue
                frames.append({
                    "source": source,
                    "verb": op.verb,
                    "aim": _aim(op),
                    "why": op.why,
                })

            filled = fill_to_site(form, site)
            delivered = compile_matrix_form(
                filled.fit.form,
                storey_height_m=site.floor_height_m,
                allowed_at=site.plan_at,
            )
            if delivered is not None:
                measurement = measure_form(delivered)
                gfa = gross_floor_area_m2(delivered, floor_height_m=site.floor_height_m)
                parcel = site.parcel_area_m2
                frames.append({
                    "source": delivered,
                    "verb": "법정 한도까지",
                    "aim": "건폐율 · 용적률 · 정북일조 봉투",
                    "why": (
                        "문장은 비례만 정한다. 치수는 이 필지가 정한다 — 법규선은 "
                        "매스를 자르고, 두 상한 중 먼저 닿는 쪽에서 멈춘다. "
                        "같은 문장이 다른 대지에서 다른 크기로 서는 이유다."
                    ),
                    "numbers": (
                        f"건폐율 {filled.fit.ground_area_m2 / parcel * 100:.1f}%  "
                        f"용적률 {gfa / parcel * 100:.0f}%  "
                        f"높이 {measurement.height_m:.1f}m"
                    ),
                })

            name = parti.name
            target = output / f"parti-{name}.png"
            render_sequence(
                frames,
                target,
                site_ring=site_ring,
                party_edges=site.shared_edges,
                heading=name.replace("llm_", "").replace("_", " "),
                subheading=" · ".join(
                    part for part in (
                        parti.formal_principle,
                        parti.reference_basis,
                    ) if part
                ),
            )
            written += 1
            self.stdout.write(f"{target}  {len(frames)} frames")

        self.stdout.write(f"wrote {written} parti sequences")
