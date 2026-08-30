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

import bisect
import collections
import json
from math import ceil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from design.maas.design_space import delivered_ground_take_band, delivered_stature_band
from design.maas.massv2 import compile_matrix_form, measure_form
from design.maas.massv2.measure import gross_floor_area_m2
from design.maas.massv2 import plausibility as plaus
from design.maas.massv2 import ablation as ablate_module
from design.maas.massv2 import postcondition
from design.maas.massv2 import program as programme
from design.maas.massv2.author import _to_form
from design.maas.massv2.execute import execute as execute_parti
from design.maas.massv2 import grammar as grammar_module
from design.maas.massv2.grammar import parti_from_record
from design.maas.massv2.legal import LegalSiteUnavailable, load_legal_site
from design.maas.massv2.execute import realign
from design.maas.massv2.fill import fill_to_site
from design.maas.massv2.legal_fit import fit_to_site
from design.maas.massv2.sampler import read_facts, sample_sentences
from design.maas.massv2.render import render_masses
from design.maas.massv2.select import Candidate, choose, summary as selection_summary
from design.maas.massv2.seeds import seed_forms
from design.maas.massv2.siting import (
    OPEN_SIDE_SITINGS,
    SITINGS,
    open_side_direction,
    place_on_site,
    spread_across_siting,
)
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


def _shortlist(chosen, count: int):
    """The few that go on the sheet, chosen to be different strategies.

    Not the top N by score: three variations on one idea is what the practice
    literature calls a single option sampled three times, and Shah's variety
    framework does not count differences that leave the structure of the concept
    intact. So the shortlist takes one per formal language first - a solid body,
    a carved one, an open figure, a field are four positions, not four scores -
    and only then falls back to rank to fill the remainder.

    The first is the recommendation. Every published scope ends with one: RAIC
    selects an alternative with the client for development, feasibility reports
    recommend a direction, Seattle asks which option the applicant prefers.
    """

    if count <= 0 or count >= len(chosen):
        # Everything fits - but one composition still does not get two tiles.
        # This early return bypassed the dedup entirely, and a starved sheet is
        # exactly where the duplicate shows: 강남 delivered five tiles and two
        # of them were `cctv_a_loop_stood_up` in different cells.
        kept: list = []
        told: set[str] = set()
        for item in chosen:
            if _sentence_of(item) in told:
                continue
            told.add(_sentence_of(item))
            kept.append(item)
        return kept
    picked: list = []
    seen: set[str] = set()
    said: set[str] = set()
    for item in chosen:
        language = item.form.primary_language or ""
        # One per language AND one per sentence, even here: a coverage variant
        # can come back reclassified into a different formal language - its
        # language is re-read off the delivered mass - so on a starved sheet
        # the language pass itself put `cctv_a_loop_stood_up` up twice, in two
        # languages, side by side. 강남 delivered five tiles and two were it.
        if language in seen or _sentence_of(item) in said:
            continue
        seen.add(language)
        said.add(_sentence_of(item))
        picked.append(item)
        if len(picked) == count:
            return picked
    # Then by rank, but never the same sentence twice. A composition carried to
    # another coverage band or another position on the parcel is the same
    # building drawn again - `nishizawa_towada~full_ground^centred` and
    # `nishizawa_towada~held_ground` differ by where they sit, not by what they
    # are - and the paragraph above is the reason: Shah's variety framework does
    # not count differences that leave the structure of the concept intact. Two
    # of the sixteen were a pair of `cctv_a_loop_stood_up` variants standing
    # side by side on the sheet.
    said = {_sentence_of(item) for item in picked}  # carries the language pass's set forward
    for item in chosen:
        if item in picked or _sentence_of(item) in said:
            continue
        said.add(_sentence_of(item))
        picked.append(item)
        if len(picked) == count:
            return picked
    # Only if that leaves the sheet short: a second variant beats an empty tile.
    for item in chosen:
        if item in picked:
            continue
        picked.append(item)
        if len(picked) == count:
            break
    return picked


def _sentence_of(item) -> str:
    """The composition a variant came from, without its band or its position."""

    return str(item.form.name).split("~")[0].split("^")[0]


# What the author aimed a move at. Magnitude is geometric and belongs to the
# executor; direction is programmatic and is the only thing the author states.
_AIM_KEYS = ("on", "at", "toward", "align", "to")


def _sequence_sheet(item, *, book, site, buildable, axis, out_dir):
    """One sheet for one scheme, a frame per word of its sentence.

    The grid this command writes is a workbench: forty-two tiles, one scheme per
    cell of the coverage x void space, each shown only as the thing it finally
    became. `massing-study/` records that this is not how the work is published.
    A Korean 매스 다이어그램 is one sheet per scheme carrying its operation
    sequence, and BIG, OMA and SANAA publish the same way - the argument is the
    order of the moves, and only the last one was ever drawn.

    Nothing here is new. `execute_steps` has returned the form after every word
    since the sequence was first wanted, `render_sequence` draws them on one
    shared scale, and `render_parti_sequence` has been a separate command all
    along. The run simply never called them, so a drawing it could already make
    was being thrown away every time.
    """

    from design.maas.massv2.execute import execute_steps
    from design.maas.massv2.render import render_sequence

    record = book.get(_sentence_of(item))
    if record is None:
        return None
    parti = parti_from_record(record)
    storey = float(parti.floor_height_m or site.floor_height_m)
    asked = max((float(op.params.get("storeys") or 0.0) for op in parti.ops), default=0.0)
    height = max(
        site.floor_height_m * max(
            1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2))),
        asked * storey,
    )
    steps = execute_steps(
        parti, buildable=buildable, axis=axis, height_m=height, storey_height_m=storey,
    )
    if not steps:
        return None

    frames = []
    for op, form in steps:
        # Through the same clip the delivered mass is measured through: a parti
        # that reads as lawful only until its last frame is not the argument.
        source = compile_matrix_form(
            form, storey_height_m=storey, allowed_at=site.plan_at)
        if source is None:
            continue
        frames.append({
            "source": source,
            "verb": op.verb,
            "aim": " · ".join(
                f"{key}: {op.params[key]}" for key in _AIM_KEYS if op.params.get(key)),
            "why": op.why,
        })
    if not frames:
        return None

    # The delivered mass last. The jump from the final authored move to this one
    # is the law and the capacity acting, which is the part of the argument that
    # belongs to this package rather than to the sentence.
    delivered = compile_matrix_form(
        realign(item.form), storey_height_m=storey, allowed_at=site.plan_at)
    if delivered is not None:
        measurement = measure_form(delivered)
        gfa = gross_floor_area_m2(delivered, floor_height_m=storey)
        frames.append({
            "source": delivered,
            "verb": "법정 한도까지",
            "aim": item.cell,
            "why": (
                "문장은 비례만 정한다. 치수는 이 필지가 정한다 — 법규선이 매스를 "
                "자르고, 건폐율과 용적률 중 먼저 닿는 쪽에서 멈춘다."
            ),
            "numbers": (
                f"건폐율 {item.ground_take * site.ground_capacity_m2 / site.parcel_area_m2 * 100:.0f}%  "
                f"용적률 {gfa / site.parcel_area_m2 * 100:.0f}%  "
                f"높이 {measurement.height_m:.1f}m"
            ),
        })

    target = Path(out_dir) / f"parti-{_sentence_of(item)}.png"
    try:
        # A drawing is not worth losing a run over: the grid, the summary and
        # every gate reading are already computed by the time this is called.
        render_sequence(
            frames, target,
            site_ring=list(site.plan_at(0.0).exterior.coords),
            party_edges=site.shared_edges,
            heading=_sentence_of(item).replace("_", " "),
            subheading=" · ".join(
                part for part in (parti.formal_principle, parti.reference_basis) if part),
        )
    except Exception:
        return None
    return target


class Command(BaseCommand):
    help = "Generate matrix-form masses on a live parcel and report the grid."

    def add_arguments(self, parser):
        parser.add_argument("--pnu", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--building-type", default="제1종근린생활시설")
        parser.add_argument(
            "--track",
            choices=("overseas", "korea"),
            default="overseas",
            help=(
                "Which of the two editions this run is. They have different "
                "objective functions and must not share a sheet: overseas lets "
                "the form decide the size and reads 용적률 as whatever it grew "
                "to, korea hands the size to a 실별 소요면적표 and reads 용적률 "
                "as whether the brief was met. Mixed together, the korea masses "
                "look like they failed to fill the cap and the overseas ones "
                "look like they ignored the brief. So korea requires a "
                "schedule and overseas refuses one."
            ),
        )
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
            "--shortlist",
            type=int,
            default=3,
            help=(
                "How many options go on the sheet. Everyone generates many and "
                "shows few: OMA builds 30-150 study models per project and "
                "presents three, Seattle's design review mandates exactly three "
                "with a written rationale each, RAIC has the number agreed "
                "before work starts and one selected for development. A contact "
                "sheet of everything lawful is the workbench, not the study. "
                "0 shows all of them."
            ),
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

        track = options["track"]
        if track == "korea" and not options["program_json"]:
            raise CommandError(
                "the korea edition is brief-driven: pass --program-json a 실별 소요면적표"
            )
        if track == "overseas" and options["program_json"]:
            raise CommandError(
                "the overseas edition lets the form decide its size: "
                "drop --program-json or run --track korea"
            )

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
            # The shared-area rule is stated once for the whole book.
            book_share = book.get("shared_area_share_of_gross")
            for record in book.get("schedules") or ():
                if wanted is None or record.get("name") == wanted:
                    schedule = programme.schedule_from_record(
                        record, shared_share_of_gross=book_share,
                    )
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

        # The refusal ledger is written whatever happens, including a run with no
        # sentences at all - which is the run most in need of it. Defined only
        # inside the branch below, a run given the wrong flag died on an
        # UnboundLocalError after printing "nothing survived to draw", and the
        # summary that would have said so was never written.
        mistyped: list = []
        mute: list = []
        clipped: list = []
        idle: list = []
        closed: list = []
        # Every sentence as written, by name, so the shortlist can be re-run
        # word by word for its sequence sheet.
        parti_book: dict[str, dict] = {}
        if options["parti_json"] or options["sample"]:
            buildable = site.plan_at(0.0)
            axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
            sentences = []
            for path in options["parti_json"] or ():
                sentences.extend(
                    json.loads(Path(path).read_text(encoding="utf-8")).get("schemes") or ()
                )
            parti_book.update({
                str(record.get("name")): record for record in sentences
                if record.get("name")
            })
            if options["sample"]:
                facts = read_facts(site)
                self.stdout.write(json.dumps(facts.evidence(), ensure_ascii=False))
                drawn = sample_sentences(facts, limit=options["sample"])
                sentences.extend(drawn)
                self.stdout.write(f"sampled sentences: {len(drawn)}")
            written = []
            pending_force = []
            authored_height = site.floor_height_m * max(
                1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2))
            )
            if schedule is not None:
                # Under a brief the parcel's own ratio is the wrong number. It
                # is 용적률 over 건폐율 - what the *law* would allow if the plot
                # were filled to both ceilings - and on 의정부 that is 4.2
                # storeys. The brief asks for 1,546 m2 on a plot that may cover
                # 1,498, which is 1.03 storeys' worth of building.
                #
                # Handing every sentence 4.2 and letting the schedule shrink the
                # plan afterwards is what produced the sheet: 63% of the
                # standing pool at 10-19% 건폐율, and fourteen of fifteen picks
                # between four and nine storeys - a 1,546 m2 주민센터 on a
                # 275 m2 footprint, which is a tower on an empty plot. A
                # 주민센터 is two to four storeys and covers its ground.
                #
                # So the brief sets the budget when there is one: the storeys it
                # needs at the coverage the law allows, rounded up, never under
                # two - one storey leaves no section for a sentence to work in.
                # A sentence naming `storeys` still overrides it below, which is
                # how a scheme that wants to stand tall and give ground back -
                # the 청년문화센터 at 7.88% this package cites - still can.
                needed = schedule.storeys_needed(
                    ground_capacity_m2=site.ground_capacity_m2)
                authored_height = site.floor_height_m * max(2, ceil(needed))
            # The parcel's average storeys, handed to every sentence, was a
            # silent flatness budget: a tower, a portal, a twist could never
            # even ask for height - the law admits sixteen sections somewhere
            # on this parcel and the executor was capping every figure at
            # four. A sentence that says storeys gets the height it asked
            # for; whether that height is lawful stays the clip's question.
            base_budget = authored_height
            def _height_budget(record) -> float:
                asked = max(
                    (float(op.get("storeys") or 0) for op in record.get("ops", [])),
                    default=0.0,
                )
                return max(base_budget, asked * site.floor_height_m)
            for record in sentences:
                wrong = grammar_module.mistyped_words(record)
                if wrong:
                    mistyped.append((record.get("name"), wrong))
                parti = parti_from_record(record)
                if parti is None:
                    continue
                authored_height = _height_budget(record)
                # The sentence's own storey. A gallery is not a shop and the
                # corpus can finally say so - every gate below judges the
                # sentence at the floor height it was written for.
                storey = float(parti.floor_height_m or site.floor_height_m)
                # Judge the sentence, not its variants: a word that redraws
                # nothing at the size it was written redraws nothing at any
                # coverage or siting derived from it.
                # The delivered mass is fitted, not clipped, and the difference
                # decides the sentence. `allowed_at` cuts every band to the
                # envelope, so two masses that differ only inside it come out
                # identical and the word between them reads as silent: measured
                # on the six sentences this refused, `twist` scores 0.3145
                # unclipped, 0.0148 clipped and 0.3339 through `fit_to_site` -
                # which is the function the pipeline actually uses, and which
                # scales a scheme down to fit rather than shaving it flush.
                # `interlock` goes 0.0000 to 0.5123 the same way.
                def _delivered_form(form, _site=site):
                    return fit_to_site(form, _site).form

                spoken = postcondition.check_sentence(
                    parti,
                    buildable=buildable,
                    axis=axis,
                    height_m=authored_height,
                    allowed_at=None,
                    storey_height_m=storey,
                    place=_delivered_form,
                )
                spoken_sitings: list[str] = []
                if not spoken.honest:
                    # Silent because the word does nothing, or silent because
                    # the law removed what it did? Measured over this corpus,
                    # six of nine silent words clear the floor comfortably when
                    # the same sentence is compiled without the sunlight
                    # envelope - 0.001 becomes 0.063, 0.000 becomes 0.081. The
                    # author redrew the building they wrote and the envelope
                    # then took that part away, so the sentence is not wrong,
                    # it is wrong *here*.
                    unclipped = postcondition.check_sentence(
                        parti, buildable=buildable, axis=axis,
                        height_m=authored_height, allowed_at=None,
                        storey_height_m=storey,
                    )
                    if not unclipped.honest:
                        mute.append((parti.name, spoken))
                        continue
                    # Wrong HERE is a property of the placement, not of the
                    # sentence: the check above tried one position, and the
                    # envelope's bite moves when the composition does. This
                    # refusal was excluding fourteen sentences wholesale -
                    # the whole twist family among them - whose words all
                    # speak somewhere else on the same parcel. The
                    # constrained-archive literature (FI-MAP-Elites) keeps
                    # the infeasible and searches its neighbourhood; ours is
                    # finite - the four sitings - so each is asked directly,
                    # and the sentence lives only at the placements where
                    # every word speaks.
                    open_side = open_side_direction(buildable, site.shared_edges)
                    sitings = OPEN_SIDE_SITINGS if open_side is not None else SITINGS
                    best = None
                    for siting in sitings:
                        placed = postcondition.check_sentence(
                            parti, buildable=buildable, axis=axis,
                            height_m=authored_height, allowed_at=None,
                            storey_height_m=storey,
                            # Placed, then fitted - the same two steps the grid
                            # takes before it draws anything.
                            place=lambda f, s=siting: _delivered_form(
                                place_on_site(f, buildable, s, open_side=open_side) or f
                            ),
                        )
                        if placed.honest:
                            spoken_sitings.append(siting.siting_id)
                            said_now = list(placed.changed[1:]) or list(placed.changed)
                            if best is None or (sum(said_now) > sum(
                                list(best.changed[1:]) or list(best.changed)
                            )):
                                best = placed
                    if best is None:
                        clipped.append((parti.name, spoken, unclipped))
                        continue
                    spoken = best
                # A sentence about what happens between volumes has to leave
                # something between them. The blind critique round tagged
                # `gaps-not-present` sixteen times and the two alternatives that
                # lost every pair they appeared in were both of this kind - a
                # thesis of standing apart, drawn fused. The executor sets the
                # gap by construction; the growth loop and the legal clip close
                # it, so it is checked on the delivered mass.
                declared_gap, built_gap = ablate_module.gap_survived(
                    parti, buildable=buildable, axis=axis,
                    height_m=authored_height, site=site,
                    storey_height_m=storey,
                )
                # Judged against whichever is smaller: a sentence asking for
                # a room-width gap owes a room-width gap, and one asking for a
                # 20 cm reveal owes 20 cm. `sanaa_bocconi` wrote 0.2 m, built
                # 2.0 m, and the first version of this refused it for delivering
                # ten times what it asked.
                owed = min(declared_gap, ablate_module.GAP_IS_A_SPACE_M)
                if declared_gap > 0.0 and built_gap < owed - ablate_module.GAP_TOLERANCE_M:
                    closed.append((parti.name, declared_gap, built_gap))
                    continue
                built = execute_parti(
                    parti, buildable=buildable, axis=axis, height_m=authored_height,
                    storey_height_m=storey,
                )
                if built is not None:
                    # How hard the sentence's own words hit the mass. The check
                    # already runs it word by word to find the silent ones; the
                    # same numbers say how much each word that did speak redrew,
                    # and that is what the selector reads. The opener is dropped
                    # from a multi-word sentence so a sentence of two words and
                    # one of five stay comparable; for a one-word sentence the
                    # fallback now returns the opener measured against the null
                    # mass rather than the flat 1.0 it used to report against
                    # nothing - `stack` alone was taking that 1.0 as its whole
                    # force and sweeping four cells of the delivered grid.
                    # Each word is worth the geometric mean of its whole-mass
                    # share and its within-reach share. On the whole-mass share
                    # alone a roof word is capped at its band's fraction of the
                    # building (`gable` at 0.17) and the selector prefers
                    # sentences that never look up; on the reach share alone a
                    # tiny complete move saturates at 1.0 (`nest` did) and the
                    # selector is back to optimising noise. Benched over the
                    # 103-sentence corpus the blend leaves the top of the table
                    # standing and lifts the roof sentences out of the floor.
                    # Each word's raw hit is the geometric mean of its
                    # whole-mass and within-reach shares; its VALUE to the
                    # selector is that hit ranked among its own verb's hits
                    # across this run's corpus (computed after the loop, when
                    # the populations exist). An absolute force made the loud
                    # verbs a caste: loop's median is 0.77 and skew's 0.02,
                    # so a sentence was rewarded for which words it chose
                    # before anything was drawn. Local competition is the
                    # quality-diversity answer (NSLC; Dominated Novelty
                    # Search, GECCO 2025): compete against behavioural
                    # neighbours - here, the same verb - not the whole field.
                    word_blends = [
                        (whole * reach) ** 0.5
                        for whole, reach in zip(spoken.changed, spoken.reached)
                    ]
                    # And what each word is worth to the mass that gets drawn,
                    # which is a different question - the growth loop and the
                    # sunlight clip both run after the sentence, and both can
                    # undo it. One extra pipeline run per word.
                    torn = ablate_module.ablate(
                        parti, buildable=buildable, axis=axis,
                        height_m=authored_height, site=site,
                        storey_height_m=storey,
                    )
                    if torn.idle:
                        idle.append((parti.name, torn))
                    built = built.__class__(
                        **{
                            **built.__dict__,
                            "extra": {
                                **dict(built.extra),
                                "ablation_force": torn.force,
                                "ablation": torn.evidence(),
                                # A rescued sentence speaks only at these
                                # placements; variants anywhere else are the
                                # dishonest drawing the check refused.
                                **({"spoken_sitings": tuple(spoken_sitings)}
                                   if spoken_sitings else {}),
                                # A sentence that says storeys is held to
                                # them at delivery, the way a declared gap
                                # is: the eight-storey monolith crushed to
                                # four is not a variant of the sentence, it
                                # is a different building wearing its name.
                                **({"declared_storeys": max(
                                    (float(op.get("storeys") or 0)
                                     for op in record.get("ops", [])),
                                    default=0.0,
                                )} if any(op.get("storeys")
                                          for op in record.get("ops", []))
                                   else {}),
                            },
                        }
                    )
                    pending_force.append(
                        (len(written), tuple(spoken.declared), tuple(word_blends))
                    )
                    if schedule is not None:
                        built = programme.resized_to(
                            built, schedule,
                            weight=options["program_weight"],
                            storey_height_m=storey,
                        )
                        built = built.__class__(
                            **{
                                **built.__dict__,
                                "extra": {
                                    **dict(built.extra),
                                    "far_capacity_m2": site.far_capacity_m2,
                                    # And the ground, so an objective can ask
                                    # how many storeys a coverage implies.
                                    "ground_capacity_m2": site.ground_capacity_m2,
                                },
                            }
                        )
                    written.append(built)
            # Second pass: each word's blend becomes its percentile among its
            # own verb's blends in this run's corpus, shrunk toward the global
            # percentile when the verb has few instances - a mansard alone
            # must not score a perfect redraw for being the only mansard.
            # Populations come from this run on this parcel on purpose:
            # quiet is a property of (word x site), so the competition is
            # local in both senses.
            verb_pop: dict[str, list[float]] = {}
            all_pop: list[float] = []
            for _idx, verbs, blends_ in pending_force:
                for verb, value in zip(verbs, blends_):
                    verb_pop.setdefault(verb, []).append(value)
                    all_pop.append(value)
            for values in verb_pop.values():
                values.sort()
            all_pop.sort()

            def _pct(pop: list[float], x: float) -> float:
                return bisect.bisect_right(pop, x) / len(pop) if pop else 0.0

            _SHRINK = 4.0
            for idx, verbs, blends_ in pending_force:
                pairs = list(zip(verbs, blends_))
                said = pairs[1:] or pairs
                scores = []
                for verb, value in said:
                    pop = verb_pop[verb]
                    local = _pct(pop, value)
                    scores.append(
                        (len(pop) * local + _SHRINK * _pct(all_pop, value))
                        / (len(pop) + _SHRINK)
                    )
                form = written[idx]
                written[idx] = form.__class__(
                    **{
                        **form.__dict__,
                        "extra": {
                            **dict(form.extra),
                            "spoken_force": sum(scores) / max(len(scores), 1),
                        },
                    }
                )
            forms.extend(written)
            if mistyped:
                self.stdout.write(
                    f"words outside their fixed list: {len(mistyped)} sentences refused "
                    "(an axis slot holding a role name is obeyed as \"long\")"
                )
                for name, wrong in mistyped[:6]:
                    said = ", ".join(f"{verb}.{key}={value!r}" for verb, key, value in wrong)
                    self.stdout.write(f"  mistyped: {name} -> {said}")
            self.stdout.write(
                f"parti sentences: {len(written)} spoken, {len(mute)} with a silent word"
            )
            for name, spoken in mute:
                self.stdout.write(
                    f"  silent: {name} -> {','.join(spoken.silent)} "
                    f"{[round(v, 3) for v in spoken.changed]}"
                )
            self.stdout.write(
                f"words the envelope removed: {len(clipped)} sentences "
                f"(the word spoke, the law took it)"
            )
            for name, spoken, unclipped in clipped:
                pairs = ", ".join(
                    f"{verb} {a:.3f}->{c:.3f}"
                    for verb, a, c in zip(spoken.declared, unclipped.changed, spoken.changed)
                    if c < postcondition.MIN_CHANGED_SHARE
                )
                self.stdout.write(f"  clipped: {name} -> {pairs}")
            self.stdout.write(
                f"gaps that closed before delivery: {len(closed)}"
            )
            for name, declared_gap, built_gap in closed:
                self.stdout.write(
                    f"  closed: {name} -> declared {declared_gap:.1f}m, built {built_gap:.1f}m"
                )
            # Spoken at the time and absent from the drawing are different
            # failures. This one is reported and not refused: nothing has been
            # measured yet about whether it predicts anything.
            self.stdout.write(
                f"words the delivered mass does not miss: "
                f"{sum(len(t.idle) for _n, t in idle)} in {len(idle)} sentences"
            )
            for name, torn in idle:
                self.stdout.write(
                    f"  idle: {name} -> {','.join(torn.idle)} "
                    f"{[round(v, 3) for v in torn.removed_share]}"
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

        # A rescued sentence (words silenced by the envelope at some
        # placements) competes only where every word speaks: variants at
        # other sitings - and the unplaced original, whose default position
        # is the one the check refused - are the same drawing the silence
        # gate already rejected.
        before = len(forms)
        forms = [
            form for form in forms
            if not form.extra.get("spoken_sitings")
            or form.extra.get("siting") in form.extra["spoken_sitings"]
        ]
        if len(forms) != before:
            self.stdout.write(
                f"rescued sentences held to their spoken sitings: "
                f"{before - len(forms)} dishonest placements dropped"
            )

        records = []
        renderable = []
        pool: list[Candidate] = []
        cells: collections.Counter[str] = collections.Counter()
        unlawful = 0
        crushed = 0
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
            form_storey = float(
                getattr(form, "floor_height_m", None) or site.floor_height_m
            )
            # A named line is an intent, not a position: the growth loop widened
            # every volume from its own centre and the variants moved the
            # composition, so a sentence obeyed at execute arrives disobeyed.
            # Re-asserted here, under the same guard, on the grown mass.
            source = compile_matrix_form(
                realign(fit.form),
                storey_height_m=form_storey,
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
                floor_height_m=form_storey,
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
                # Stature crossed with void, since the flatness measurement:
                # ground-take crossed with void left height a leftover, and a
                # sheet that owes no cell a tall building ships a flat sheet
                # (16 m average against a 48 m legal section). Ground take is
                # still measured and reported; it is the free variable now.
                stature = delivered_stature_band(
                    measurement.height_m, storey_height_m=form_storey
                ).band_id
                cell = f"{stature}|{measurement.void_band_id}"
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
                # Recorded, not scored. It does not beat `spoken_force` on the
                # two critique rounds there are, and n=10 cannot resolve the
                # difference - so it accumulates until there is enough of it.
                "ablation": form.extra.get("ablation"),
                "spoken_force": form.extra.get("spoken_force"),
            })
            declared = float(form.extra.get("declared_storeys") or 0.0)
            if (declared > 0.0
                    and measurement.height_m < (2.0 / 3.0) * declared * form_storey):
                # Declared stature is held like a declared gap: a sentence
                # that asked for eight storeys and delivered four is not that
                # sentence. The variant stays measured and recorded; it just
                # cannot represent the sentence on the sheet.
                crushed += 1
            elif fit.satisfied:
                # An unlawful mass was being counted and then offered anyway.
                # `central_beheer_islands` came out at 1.17 of the 건폐율 cap
                # after the fitter gave up at two passes, and went onto the
                # sheet as an alternative. A mass the legal fitter could not
                # satisfy is not a low-scoring option, it is not an option -
                # the same argument `plausibility` makes about standing up.
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
        compiled_count = len(renderable)
        if options["per_cell"] > 0:
            chosen = choose(pool, per_cell=options["per_cell"])
            selection = selection_summary(chosen, considered=len(pool))
            shortlist = _shortlist(chosen, options["shortlist"])
            renderable = [
                (
                    item.form.name,
                    item.source,
                    {
                        # The thesis first. A jury does not read `artic 0.36`,
                        # and every massing study in print - RAIC, Seattle SDCI,
                        # OMA's named options - carries a sentence per option
                        # saying what it is for. The sentence was already on the
                        # form and was being dropped at the tile.
                        "thesis": item.form.formal_principle or item.form.secondary_language,
                        "recommended": index == 0,
                        # The number the law was checked against, in the same
                        # form as the 용적률 line below it. `source.footprint`
                        # is not that number twice over: it is what touches the
                        # ground rather than the horizontal projection 건축면적
                        # is defined as, and `compile` keeps only the largest
                        # piece of it when a mass stands on several. On
                        # `oma_blox_copenhagen`, whose sentence lifts one wing
                        # over a road, those read 169.7 m² and 796.7 m² - the
                        # tile said 7% under a drawing of a building covering
                        # 32% of its plot.
                        "건폐율": f"{item.ground_take * site.ground_capacity_m2 / site.parcel_area_m2 * 100:.0f}%",
                        "용적률": f"{item.far_utilization * site.far_capacity_m2 / site.parcel_area_m2 * 100:.0f}%",
                        "cell": item.cell.replace("_ground", "").replace("_body", "").replace("_figure", ""),
                    },
                )
                for index, item in enumerate(shortlist)
            ]
            self.stdout.write(
                f"selected {len(chosen)} from {len(pool)} "
                f"({selection['distinct_compositions']} distinct compositions)"
            )
            self.stdout.write(
                f"shortlist {len(shortlist)} for the sheet, "
                f"recommended: {shortlist[0].form.name if shortlist else '-'}"
            )
            # And the same schemes in the format Korean practice publishes.
            # `massing-study/` records the difference: a 매스 다이어그램 there is
            # one sheet per scheme showing its operation sequence, one frame per
            # move, while the 42-tile grid this command has always written is
            # the workbench behind that sheet. The renderer and the step-wise
            # executor both already existed - `render_parti_sequence` has been a
            # separate command since the sequence was first drawn - so the run
            # was throwing away a drawing it could make.
            for item in shortlist:
                try:
                    written = _sequence_sheet(
                        item, book=parti_book, site=site, buildable=buildable,
                        axis=axis, out_dir=output,
                    )
                except Exception as error:  # noqa: BLE001 - a drawing, not a gate
                    self.stdout.write(f"sequence sheet skipped: {error}")
                    continue
                if written is not None:
                    self.stdout.write(str(written))

        # Which edition, off which vocabulary, against which brief. Two runs of
        # this command produced 용적률 110-229% and 58-60% and nothing in either
        # output said why - the difference was in how the command line was
        # typed. A sheet nobody can trace back to its inputs is not evidence.
        provenance = {
            "track": track,
            # Which 소요면적표 sized these masses. The sheet has to rebuild
            # through the same brief or it draws a different building.
            "programme": schedule.name if schedule is not None else None,
            "corpus": sorted(
                Path(path).name
                for path in (options["authored_json"] or []) + (options["parti_json"] or [])
            ),
            "sampled": options["sample"] or 0,
            # Which ground plane the envelope stood on. §119 datum is opt-in and
            # falls back to a flat 0 m whenever no elevation answers, which is
            # indistinguishable in the drawing from a parcel that is flat. The
            # Uijeongbu parcel is 25.5 km north of the only DEM on this machine,
            # so every grid to date ran on the fallback with the flag reading on
            # and the summary saying nothing either way.
            "datum": (
                {
                    "measured": site.datum_is_measured,
                    "case": site.datum.get("case"),
                    "basis": site.datum.get("basis"),
                    "elevation_source": site.datum.get("elevation_source"),
                }
                if site.datum
                else {"measured": False, "case": None, "basis": "datum_disabled",
                      "elevation_source": None}
            ),
            "brief": (
                {
                    "name": schedule.name,
                    "gross_m2": round(schedule.gross_m2, 1),
                    "weight": options["program_weight"],
                }
                if schedule is not None
                else None
            ),
        }

        site_ring = [(float(x), float(y)) for x, y in site.site_local_utm.exterior.coords[:-1]]
        # A run where every sentence was refused has nothing to draw, and
        # raising there threw away the summary too - which is the one artifact
        # that says *why* they were refused. The drawing is optional; the
        # record is not.
        sheet = None
        if renderable:
            # White model, not clay. `picksheet` has been passing `massing` all
            # along and the difference is not decoration: the same mass reads as
            # a composition in line and as a lump in shaded orange. Looking at
            # forty-four of them side by side is what settled it - the pool is
            # full of masses that read as one move, and the contact sheet was
            # making every one of them look like the same brown block.
            sheet = render_masses(
                renderable, output / "massv2-sheet.png", site_ring=site_ring,
                style="massing", tile=(560, 620))
        else:
            self.stdout.write("nothing survived to draw; writing the record only")

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
                    style="massing",
                )
            (output / "alts.json").write_text(
                json.dumps(
                    {
                        "schema_version": "arr.maas.massv2_alternatives.v1",
                        "provenance": provenance,
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
            "provenance": provenance,
            "site": site.evidence(),
            "form_count": len(forms),
            "compiled": compiled_count,
            "delivered": len(renderable),
            "unlawful": unlawful,
            "implausible": implausible,
            "occupied_cells": len(cells),
            "cells": dict(sorted(cells.items())),
            # Why a sentence never became a record. These four refusals were
            # printed to stdout and kept nowhere else, so a reader of the
            # summary saw 125 families out of 141 and no reason for the other
            # sixteen - which is exactly what happened here for three sessions
            # while I looked for the cause in the gates downstream. The counts
            # are the funnel; the names are so the next question is answerable
            # without re-running the grid.
            "refused": {
                "mistyped": [
                    {"name": name, "words": list(words)} for name, words in mistyped
                ],
                "silent": [
                    {"name": name, "words": list(spoken.silent)} for name, spoken in mute
                ],
                "clipped_by_law": [
                    {"name": name, "words": [
                        verb for verb, changed in zip(spoken.declared, spoken.changed)
                        if changed < postcondition.MIN_CHANGED_SHARE
                    ]}
                    for name, spoken, _unclipped in clipped
                ],
                "gap_closed": [
                    {"name": name, "declared_m": round(float(declared), 2),
                     "built_m": round(float(built), 2)}
                    for name, declared, built in closed
                ],
            },
            "selection": selection,
            "records": records,
        }
        (output / "massv2-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # `renderable` is the shortlist by this point, so reporting it as the
        # compiled count read "compiled 3/1099" on a run that compiled 1,098.
        self.stdout.write(
            f"compiled {compiled_count}/{len(forms)}  delivered {len(renderable)}  "
            f"unlawful {unlawful}  implausible {implausible}  "
            f"crushed {crushed}  cells {len(cells)}/16"
        )
        self.stdout.write(str(sheet) if sheet else str(output))
