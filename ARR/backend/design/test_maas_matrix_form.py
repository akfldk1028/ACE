"""Placed volumes have to reach shapes the face-operation language cannot.

The existing language is face operations on one solid. Measured on a 40x24x18
reference box with every operative pushed to its strongest accepted setting,
departure from the mass's own convex hull tops out at 0.29 - and five of the ten
operatives could not be seen at all by the void axis, because a flattened plan
projection closes any opening that has something above it.

These tests hold three things about the replacement:

  * a plain box measures as a plain box (the measure is not simply generous),
  * a stepped stack is not called plain (plan measures alone said 0.000),
  * the language reaches `porous_field`, which four consecutive live runs of the
    old language never produced once.
"""

from dataclasses import replace

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.massv2 import MatrixForm, compile_matrix_form, measure_form, place
from design.maas.massv2.measure import FormMeasurement
from design.maas.massv2.plausibility import (
    MAX_UNLIT_SHARE,
    Plausibility,
    assess as plausibility_of,
    daylit_depth_m,
    slenderness_limit,
    unlit_share,
)
from design.maas.massv2.select import (
    CORPUS_PIECES,
    OBJECTIVES,
    Candidate,
    _piece_distance,
    choose,
    piece_count,
)
from design.maas.massv2.structure import CANTILEVER_BACKSPAN_RATIO, assess_standing


def _form(name, placements, **kwargs):
    kwargs.setdefault("primary_language", "test_language")
    return MatrixForm(name=name, placements=tuple(placements), **kwargs)


def _measured(form):
    source = compile_matrix_form(form)
    assert source is not None, f"{form.name} failed to compile"
    return source, measure_form(source)


class PlainThingsMeasurePlainTests(SimpleTestCase):
    def test_a_single_extrusion_is_flat_on_every_axis(self):
        _source, measurement = _measured(_form("box", [place("box", size=(30, 20, 16))]))

        self.assertAlmostEqual(0.0, measurement.convexity_drop, places=3)
        self.assertAlmostEqual(0.0, measurement.plan_void_ratio, places=3)
        self.assertAlmostEqual(0.0, measurement.section_change, places=3)
        self.assertAlmostEqual(0.0, measurement.articulation(), places=3)

    def test_a_rotated_box_is_still_flat(self):
        """Void measured against an axis-aligned box reads 0.52 at 45 degrees.

        That is orientation, not void, and it contaminated the void axis until
        it was re-based on the tightest rectangle. Hold that here too.
        """

        _source, measurement = _measured(
            _form("turned", [place("box", size=(30, 20, 16), rotation_degrees=37.0)])
        )

        self.assertAlmostEqual(0.0, measurement.plan_void_ratio, places=3)


class SectionIsArticulationTooTests(SimpleTestCase):
    def test_a_stepped_stack_is_not_reported_plain(self):
        """Every storey of a setback tower is a convex closed rectangle.

        Plan convexity and plan void both read 0.000 for it. Reporting only
        those would file a whole family of massing as a plain box.
        """

        _source, measurement = _measured(
            _form(
                "stack",
                [
                    place("plinth", size=(34, 22, 5)),
                    place("mid", size=(24, 18, 7), at=(6, 2, 4.9)),
                    place("tower", size=(14, 14, 9), at=(2, 6, 11.8)),
                ],
            )
        )

        self.assertAlmostEqual(0.0, measurement.convexity_drop, places=2)
        self.assertGreater(measurement.section_change, 0.2)
        self.assertGreater(measurement.articulation(), 0.2)


class SeparatedPiecesSurviveTests(SimpleTestCase):
    def test_two_bars_with_a_gap_keep_both_bars(self):
        """Keeping only the largest piece of a band deletes half the building.

        Measured before the fix, a paired-bar scheme read 0.05 open because one
        bar was dropped; both present it is a quarter open.
        """

        source, measurement = _measured(
            _form(
                "bars",
                [
                    place("bar_a", size=(36, 9, 18)),
                    place("bar_b", size=(36, 9, 18), at=(0, 15, 0)),
                ],
            )
        )
        ground = [item for item in source.volumes if item.bottom_fraction <= 1e-6]

        self.assertEqual(2, len(ground))
        self.assertGreater(measurement.plan_void_ratio, 0.2)

    def test_the_pieces_of_one_band_share_that_band(self):
        """They are one storey of one building, not two buildings."""

        source, _measurement = _measured(
            _form(
                "bars",
                [
                    place("bar_a", size=(36, 9, 18)),
                    place("bar_b", size=(36, 9, 18), at=(0, 15, 0)),
                ],
            )
        )
        spans = {(item.bottom_fraction, item.top_fraction) for item in source.volumes}

        self.assertEqual(1, len(spans))


class ReachesWhatTheOldLanguageCouldNotTests(SimpleTestCase):
    OLD_LANGUAGE_CEILING = 0.29

    def test_porous_field_is_reachable(self):
        """Four consecutive live runs of the old language produced none."""

        _source, measurement = _measured(
            _form(
                "splayed",
                [
                    place("a", size=(30, 8, 17)),
                    place("b", size=(30, 8, 17), at=(0, 14, 0), rotation_degrees=18.0),
                    place("core", size=(8, 8, 17), at=(0, 7, 0)),
                ],
            )
        )

        self.assertEqual("porous_field", measurement.void_band_id)

    def test_articulation_clears_the_face_operation_ceiling(self):
        _source, measurement = _measured(
            _form(
                "cross",
                [
                    place("base", size=(16, 16, 9)),
                    place("arm", size=(38, 10, 6), at=(-11, 3, 8.9)),
                    place("cap", size=(12, 30, 5), at=(2, -7, 14.5)),
                ],
            )
        )

        self.assertGreater(measurement.articulation(), self.OLD_LANGUAGE_CEILING)


class SubtractionIsPerBandTests(SimpleTestCase):
    def test_a_roofed_court_still_reads_as_a_court_below_the_roof(self):
        """This is the case a flattened union closes and the axis then misses."""

        _source, measurement = _measured(
            _form(
                "roofed_court",
                [
                    place("body", size=(30, 24, 12)),
                    place("court", size=(12, 10, 14), at=(9, 7, -1), kind="subtractive"),
                    place("roof", size=(30, 24, 3), at=(0, 0, 11.9)),
                ],
            )
        )

        self.assertGreater(measurement.plan_void_ratio, 0.0)

    def test_a_cutter_does_not_set_the_building_height(self):
        """A cutter is pushed past the face so its cut lands cleanly.

        Letting it define the height would inflate the building by however far
        it was pushed out.
        """

        form = _form(
            "cut",
            [
                place("body", size=(30, 24, 12)),
                place("court", size=(12, 10, 40), at=(9, 7, -14), kind="subtractive"),
            ],
        )

        self.assertAlmostEqual(12.0, form.height_m(), places=6)


class RankingIgnoresTheCellsOwnCoordinateTests(SimpleTestCase):
    """A cell must not be ranked on the thing that put every occupant in it.

    The void band is one of the grid's two coordinates, so plan void is close
    to constant among a cell's occupants - and it returns much larger numbers
    than convexity or section, so `max()` reported it and hid the rest. On the
    Uijeongbu parcel the porous column all sat at 0.70-0.79 while the solid
    column topped out at 0.32, which is a difference in ceilings rather than in
    quality.
    """

    def _measurement(self, *, void, convexity=0.0, section=0.0):
        return FormMeasurement(
            convexity_drop=convexity,
            plan_void_ratio=void,
            section_change=section,
            void_band_id="porous_field",
            band_count=3,
            footprint_area_m2=400.0,
            height_m=15.0,
            band_profile=((0.0, 1.0),),
        )

    def _candidate(self, name, measurement, placements=None):
        form = _form(name, placements or [place("body", size=(20.0, 20.0, 12.0))])
        source = compile_matrix_form(form)
        assert source is not None
        return Candidate(
            form=form,
            source=source,
            measurement=measurement,
            plausibility=Plausibility(2.0, 20.0, 1.0, True, ()),
            cell="full_ground|porous_field",
            ground_take=0.9,
            far_utilization=0.9,
        )

    def _candidate_at(self, name, *, far, convexity=0.0, section=0.0, void=0.75,
                      placements=None):
        item = self._candidate(name, self._measurement(
            void=void, convexity=convexity, section=section
        ), placements=placements)
        return replace(item, far_utilization=far)

    def test_no_objective_reads_either_grid_coordinate(self):
        """Ground take and plan void say where a scheme sits, not how good it is."""

        reads = [read(self._candidate_at("probe", far=0.5, void=0.99))
                 for _name, read in OBJECTIVES]

        self.assertNotIn(0.99, reads)
        self.assertNotIn(0.9, reads)  # ground_take on the fixture

    def test_one_towering_strength_loses_to_no_weak_side(self):
        """The card deck, in miniature.

        `splayed_fan` won its cell on a single maximum while measuring nothing
        in section and nothing in carving, and every scheme rewritten against
        the critic lost to the one it replaced. Balance is the whole fix: a
        scheme has to be worth something on each count it is asked about.
        """

        # Three, because normalising two candidates makes each of them the best
        # on one objective and the worst on the other, which is a tie by
        # construction and tests nothing.
        spike = self._candidate_at("card_deck", far=1.0, convexity=0.0, section=0.0)
        balanced = self._candidate_at("worked_block", far=0.7, convexity=0.7, section=0.0,
                                      placements=[
                                          place("a", size=(24.0, 14.0, 9.0)),
                                          place("b", size=(10.0, 14.0, 6.0), at=(0.0, 0.0, 9.0)),
                                      ])
        thin = self._candidate_at("all_shape_no_area", far=0.0, convexity=1.0, section=0.0,
                                  placements=[
                                      place("a", size=(20.0, 6.0, 12.0)),
                                      place("b", size=(6.0, 20.0, 12.0), at=(14.0, 0.0, 0.0)),
                                  ])

        chosen = choose([spike, balanced, thin], per_cell=1)

        self.assertEqual([item.form.name for item in chosen], ["worked_block"])

    def test_carving_and_stepping_are_two_ways_to_do_one_thing(self):
        """A courtyard block never steps and a stepped tower is convex in plan.

        Scored as separate objectives, balance punishes each for not being the
        other - on the live parcel that handed full_ground|solid_body to a
        scheme at 0.05 articulation over `stacked_45` at 0.55, purely because
        the stepped one was flat in plan. Substitutes take a maximum; only
        things a scheme owes at the same time take a balance.
        """

        carved = self._candidate_at("courtyard", far=0.8, convexity=0.6, section=0.0)
        stepped = self._candidate_at("setbacks", far=0.8, convexity=0.0, section=0.6,
                                     placements=[
                                         place("a", size=(24.0, 14.0, 9.0)),
                                         place("b", size=(10.0, 14.0, 6.0), at=(0.0, 0.0, 9.0)),
                                     ])
        mediocre = self._candidate_at("even_pile", far=0.8, convexity=0.05, section=0.05,
                                      placements=[
                                          place("a", size=(20.0, 6.0, 12.0)),
                                          place("b", size=(6.0, 20.0, 12.0), at=(14.0, 0.0, 0.0)),
                                      ])

        chosen = choose([carved, stepped, mediocre], per_cell=1)

        self.assertNotEqual([item.form.name for item in chosen], ["even_pile"])

    def test_the_same_scheme_does_not_print_three_times(self):
        """Across cells the composition is remembered by name, not by shape.

        The coverage variants of one scheme legitimately differ in proportion,
        so the geometry signature stops matching between them - and the moment
        the ranking changed, `hollow_market_arch` took its own cell and then two
        more, and sixteen tiles read as nine buildings.
        """

        # The two variants are the same scheme carried along the coverage axis,
        # and growing it does not scale it evenly - so their signatures differ,
        # which is exactly why the signature could not remember them.
        arch_a = replace(self._candidate_at("llm_arch~held_ground", far=0.9, placements=[
            place("west", size=(6.0, 18.0, 14.0), at=(0.0, 0.0, 0.0)),
            place("east", size=(6.0, 18.0, 14.0), at=(10.0, 0.0, 0.0)),
            place("lintel", size=(16.0, 18.0, 4.0), at=(0.0, 0.0, 14.0)),
        ]), cell="held_ground|porous_field")
        arch_b = replace(self._candidate_at("llm_arch~full_ground", far=0.9, placements=[
            place("west", size=(9.0, 18.0, 9.0), at=(0.0, 0.0, 0.0)),
            place("east", size=(9.0, 18.0, 9.0), at=(17.0, 0.0, 0.0)),
            place("lintel", size=(26.0, 18.0, 6.0), at=(0.0, 0.0, 9.0)),
        ]), cell="full_ground|porous_field")
        # Genuinely a different composition. The signature is scale free, so a
        # single box is the same signature at any size, and the within-cell
        # dedupe would fold this into the arch before the cross-cell rule was
        # ever consulted.
        other = replace(
            self._candidate_at("llm_comb~full_ground", far=0.5, placements=[
                place("west", size=(8.0, 20.0, 12.0), at=(0.0, 0.0, 0.0)),
                place("east", size=(8.0, 20.0, 12.0), at=(12.0, 0.0, 0.0)),
            ]),
            cell="full_ground|porous_field",
        )

        chosen = choose([arch_a, arch_b, other], per_cell=1)

        self.assertEqual(
            sorted(item.form.name for item in chosen),
            ["llm_arch~held_ground", "llm_comb~full_ground"],
        )

    def test_the_ring_that_also_steps_wins_its_cell(self):
        # Both are the same kind of building by the grid's own reckoning. Under
        # max() they tie at 0.75 and the cell is decided by floor area; the one
        # that also works in section has to win.
        plain = self._candidate("plain_ring", self._measurement(void=0.75))
        worked = self._candidate(
            "stepped_ring", self._measurement(void=0.75, section=0.30)
        )

        chosen = choose([plain, worked], per_cell=1)

        self.assertEqual([item.form.name for item in chosen], ["stepped_ring"])

    def test_the_carved_ring_beats_the_plain_one_too(self):
        plain = self._candidate("plain_ring", self._measurement(void=0.75))
        carved = self._candidate(
            "quarried_ring", self._measurement(void=0.75, convexity=0.24)
        )

        chosen = choose([plain, carved], per_cell=1)

        self.assertEqual([item.form.name for item in chosen], ["quarried_ring"])


class StandingUpIsAGateNotAScoreTests(SimpleTestCase):
    """The physics the sheet's numbers could not see.

    `splayed_fan` came first in its cell on every measure the sheet carries -
    articulation 0.79, ground take 0.94, 용적률 0.98 - and the critic called it a
    collapsed deck of cards. A metric cannot be patched into noticing that,
    because plausibility of shape and stability of body are not correlated:
    Mezghanni et al. (CVPR 2021) measured a learned discriminator and a
    geometric-plausibility function against real stability and both failed,
    while explicit support-polygon computation succeeded. So it is computed,
    at the gate, and an unbuildable mass stops being an option at all.
    """

    def _standing(self, name, placements):
        form = _form(name, placements)
        source = compile_matrix_form(form)
        self.assertIsNotNone(source, f"{name} failed to compile")
        return assess_standing(source, height_m=form.height_m())

    def test_a_slab_reaching_past_a_third_of_its_backspan_is_refused(self):
        # 24 m of overhang carried on an 8 m backspan: three times the AISC
        # rule of thumb, and not a building anyone frames.
        standing = self._standing("overreach", [
            place("base", size=(8, 20, 4), at=(0, 0, 0)),
            place("arm", size=(32, 20, 4), at=(0, 0, 4)),
        ])

        self.assertFalse(standing.stands)
        self.assertTrue(any("cantilever" in reason for reason in standing.reasons))

    def test_the_same_slab_within_the_rule_is_allowed(self):
        standing = self._standing("held", [
            place("base", size=(24, 20, 4), at=(0, 0, 0)),
            place("arm", size=(30, 20, 4), at=(0, 0, 4)),
        ])

        self.assertTrue(standing.stands, standing.reasons)
        self.assertLess(standing.cantilever_ratio, CANTILEVER_BACKSPAN_RATIO)

    def test_a_bar_bridging_two_towers_is_a_span_and_not_a_cantilever(self):
        """CCTV is not a cantilever and must not be graded as one.

        Held at both ends, the first cut of this gate called this bar 3.4 times
        its own backspan and threw every bridge in the vocabulary off the sheet.
        A piece touching its support in two separated places is a span.
        """

        standing = self._standing("bridge", [
            place("west", size=(10, 12, 24), at=(0, 0, 0)),
            place("east", size=(10, 12, 24), at=(28, 0, 0)),
            place("deck", size=(38, 12, 4), at=(0, 0, 24)),
        ])

        self.assertTrue(standing.stands, standing.reasons)
        self.assertEqual(0.0, standing.cantilever_ratio)
        self.assertGreater(standing.span_to_depth, 0.0)

    def test_a_span_far_longer_than_its_depth_is_still_refused(self):
        standing = self._standing("wire", [
            place("west", size=(3, 12, 24), at=(0, 0, 0)),
            place("east", size=(3, 12, 24), at=(97, 0, 0)),
            place("deck", size=(100, 12, 1.5), at=(0, 0, 24)),
        ])

        self.assertFalse(standing.stands)
        self.assertTrue(any("span" in reason for reason in standing.reasons))

    def test_a_top_heavy_mass_leaning_off_its_own_ground_falls_over(self):
        standing = self._standing("topple", [
            place("foot", size=(6, 6, 3), at=(0, 0, 0)),
            place("crown", size=(20, 20, 24), at=(14, 0, 3)),
        ])

        self.assertFalse(standing.stands)
        self.assertTrue(
            any("centre_of_mass" in reason for reason in standing.reasons),
            standing.reasons,
        )

    def test_two_grounded_bars_with_a_courtyard_between_them_still_stand(self):
        """A table stands between its legs, not on one of them.

        Measured against the union of the ground contacts rather than their
        convex hull, a pair of splayed bars reported its own centre of mass
        2.6 m outside its support and 188 of 333 candidates were thrown out.
        The support polygon is the hull of what touches the ground.
        """

        standing = self._standing("paired", [
            place("north", size=(30, 8, 18), at=(0, 22, 0)),
            place("south", size=(30, 8, 18), at=(0, 0, 0)),
        ])

        self.assertGreater(standing.overturning_margin_m, 0.0)
        # It does not stand as *one* building, and that is a different check:
        # two bars that never meet are two buildings on one parcel. Joined by a
        # podium they are one, and then this passes outright.
        self.assertEqual(standing.body_count, 2)

    def test_two_bars_joined_by_a_podium_are_one_building(self):
        standing = self._standing("paired_on_podium", [
            place("podium", size=(30, 30, 5), at=(0, 0, 0)),
            place("north", size=(30, 8, 18), at=(0, 22, 4)),
            place("south", size=(30, 8, 18), at=(0, 0, 4)),
        ])

        self.assertTrue(standing.stands, standing.reasons)
        self.assertEqual(standing.body_count, 1)

    def test_a_block_hovering_over_another_has_no_load_path(self):
        """Overlapping in plan is not resting on it.

        Two of the delivered alternatives read as a cloud of blocks at different
        heights with nothing between them. The overturning check passed them,
        correctly - it measures the convex hull of the ground contacts, which is
        why a table stands between its legs - and that is exactly why it cannot
        be the check that catches this.
        """

        standing = self._standing("hovering", [
            place("base", size=(14, 14, 6), at=(0, 0, 0)),
            place("floater", size=(10, 10, 6), at=(2, 2, 14)),
        ])

        self.assertFalse(standing.stands)
        self.assertTrue(
            any("reaches_the_ground" in r or "separate_bodies" in r for r in standing.reasons),
            standing.reasons,
        )

    def test_the_gate_speaks_through_plausibility(self):
        """A mass that cannot stand is not occupiable, whatever else it is.

        This is the wiring that matters: `choose` drops what is not occupiable,
        so an unbuildable scheme never reaches the archive, the contact sheet or
        the critic - rather than arriving with a good score and being argued
        about.
        """

        form = _form("overreach", [
            place("base", size=(8, 20, 4), at=(0, 0, 0)),
            place("arm", size=(32, 20, 4), at=(0, 0, 4)),
        ])
        source = compile_matrix_form(form)

        standing = plausibility_of(
            source, parcel_area_m2=2499.69, max_slenderness=5.0
        )

        self.assertFalse(standing.occupiable)
        self.assertIsNotNone(standing.standing)
        self.assertTrue(any("cantilever" in reason for reason in standing.reasons))


class TheParcelSaysHowSlenderTests(SimpleTestCase):
    """The limit that admitted its own counterexample.

    This module opens by naming a chimney at a slenderness of 10.4 as "not a
    근린생활시설 anyone would propose", and then carried a constant of 12 quoted
    from the other pipeline's review gate, which passed it. The bound now comes
    from the parcel, and from the number that already stops growth in `fill`:
    용적률 over 건폐율, the storeys the site affords over the ground it allows.
    """

    def test_the_chimney_this_module_was_written_against_is_refused(self):
        uijeongbu = slenderness_limit(
            far_capacity_m2=2499.691, ground_capacity_m2=499.938
        )

        self.assertAlmostEqual(uijeongbu, 5.0, places=2)
        self.assertLess(uijeongbu, 10.4)

    def test_zoning_that_is_for_towers_allows_slender_ones(self):
        """A constant cannot say this and a ratio can.

        60% 건폐율 with 800% 용적률 is a parcel whose own law is about going up,
        and refusing a slender building there would be the same mistake in the
        other direction.
        """

        downtown = slenderness_limit(
            far_capacity_m2=8.0 * 1000.0, ground_capacity_m2=0.6 * 1000.0
        )

        self.assertGreater(downtown, 13.0)

    def test_a_stick_on_the_live_parcel_is_not_occupiable(self):
        form = _form("chimney", [place("shaft", size=(4.0, 4.0, 40.0))])
        source = compile_matrix_form(form)

        verdict = plausibility_of(
            source,
            parcel_area_m2=2499.69,
            max_slenderness=slenderness_limit(
                far_capacity_m2=2499.691, ground_capacity_m2=499.938
            ),
        )

        self.assertFalse(verdict.occupiable)
        self.assertTrue(any("slenderness" in reason for reason in verdict.reasons))


class DaylightSaysHowDeepTests(SimpleTestCase):
    """The gate asked how thin a mass may be and never how deep.

    A forty-metre-across slab satisfies both ceilings, stands up, and has a
    middle no window reaches - and on a wide parcel the growth loop makes
    exactly that, because filling 용적률 by spreading is cheaper than by
    rising. Reinhart's rule of thumb puts the daylit zone at two to two and a
    half times the window head, which in a storey of this height is the storey
    itself: six metres in from a façade, twelve across when lit from both
    sides. That is the depth every daylit bar in the corpus is built to, and
    the reason a courtyard block, a bar and a comb exist at all.
    """

    def test_a_bar_is_lit_and_a_slab_of_the_same_area_is_not(self):
        bar = Polygon([(0, 0), (12, 0), (12, 100), (0, 100)])
        slab = Polygon([(0, 0), (35, 0), (35, 35), (0, 35)])

        self.assertEqual(unlit_share(bar, floor_height_m=3.0), 0.0)
        self.assertGreater(unlit_share(slab, floor_height_m=3.0), MAX_UNLIT_SHARE)

    def test_a_court_rescues_the_outline_it_was_cut_from(self):
        """Which is the whole reason a courtyard block exists."""

        outline = [(0, 0), (40, 0), (40, 30), (0, 30)]
        solid = Polygon(outline)
        courtyard = Polygon(outline, [[(12, 9), (28, 9), (28, 21), (12, 21)]])

        self.assertGreater(unlit_share(solid, floor_height_m=3.0), MAX_UNLIT_SHARE)
        # Not quite zero: the four corners of a rectangle keep a sliver past
        # six metres from both the outer wall and the court. A corner of a
        # room is not the same claim as its middle.
        self.assertLess(unlit_share(courtyard, floor_height_m=3.0), 0.01)

    def test_the_depth_follows_the_storey_rather_than_a_constant(self):
        self.assertAlmostEqual(daylit_depth_m(3.0), 6.0)
        self.assertAlmostEqual(daylit_depth_m(4.5), 9.0)

    def test_a_deep_slab_is_refused_by_the_gate(self):
        form = _form("slab", [place("plate", size=(38.0, 34.0, 12.0))])
        source = compile_matrix_form(form)

        verdict = plausibility_of(
            source,
            parcel_area_m2=2499.69,
            max_slenderness=slenderness_limit(
                far_capacity_m2=6241.962, ground_capacity_m2=1497.877
            ),
            floor_height_m=3.0,
        )

        self.assertFalse(verdict.occupiable)
        self.assertTrue(any("daylight" in reason for reason in verdict.reasons))

    def test_the_gate_is_silent_when_no_storey_height_is_given(self):
        """Callers that never knew the storey height keep their old verdict."""

        form = _form("slab", [place("plate", size=(38.0, 34.0, 12.0))])
        source = compile_matrix_form(form)

        verdict = plausibility_of(
            source,
            parcel_area_m2=2499.69,
            max_slenderness=slenderness_limit(
                far_capacity_m2=6241.962, ground_capacity_m2=1497.877
            ),
        )

        self.assertFalse(any("daylight" in reason for reason in verdict.reasons))


class TheCorpusSaysHowManyVolumesTests(SimpleTestCase):
    """Measured across 2014-2024 Korean competition winners: 3.4 masses.

    A preference and not a gate. Six volumes is not unlawful, it is simply not
    what wins there, and 3.4 is a distribution rather than a rule - which is the
    mistake `MIN_TIER_CONTRAST` made in the other direction, legislating a
    property that should have emerged. So it only speaks where the evidence
    does: with a brief in hand, meaning the sheet is judged as a Korean entry.
    """

    def _candidate(self, name, count, *, briefed):
        placements = [
            place(f"v{i}", size=(10.0, 10.0, 6.0), at=(i * 14.0, 0.0, 0.0))
            for i in range(count)
        ]
        form = MatrixForm(
            name=name,
            placements=tuple(placements),
            primary_language="test",
            extra={"programme_target": 1000.0} if briefed else {},
        )
        source = compile_matrix_form(form, storey_height_m=3.0)
        return Candidate(
            form=form, source=source, measurement=measure_form(source),
            plausibility=plausibility_of(
                source, parcel_area_m2=2499.69, max_slenderness=5.0
            ),
            cell="base|solid_body", ground_take=0.4, far_utilization=0.5,
        )

    def test_pieces_are_counted_as_placed_not_as_sliced(self):
        """One deformed volume is one piece however many bands it compiles to.

        Under the legal clip the compiler cuts a volume at each storey, because
        the 정북일조 envelope gives every storey a different plan - which is how
        counting bands reported BIG's own signature, a single deformed volume in
        seven of ten projects, at six and a half pieces.
        """

        one = MatrixForm(
            name="one deformed volume",
            placements=(place("body", size=(30.0, 20.0, 15.0)),),
            primary_language="test",
        )
        three = MatrixForm(
            name="three",
            placements=tuple(
                place(f"v{i}", size=(10.0, 10.0, 6.0), at=(i * 12.0, 0.0, 0.0))
                for i in range(3)
            ),
            primary_language="test",
        )

        self.assertEqual(piece_count(one), 1)
        self.assertEqual(piece_count(three), 3)

    def test_a_brief_prefers_the_scheme_nearer_the_winners(self):
        near = self._candidate("near", 3, briefed=True)
        far = self._candidate("far", 9, briefed=True)

        # The gate is not what is under test here - these are synthetic
        # volumes standing apart, which connectivity refuses and should.
        chosen = choose([far, near], per_cell=1, require_occupiable=False)

        self.assertEqual([item.form.name for item in chosen], ["near"])

    def test_without_a_brief_the_count_says_nothing(self):
        near = self._candidate("near", 3, briefed=False)
        far = self._candidate("far", 9, briefed=False)

        self.assertEqual(_piece_distance(near), 0.0)
        self.assertEqual(_piece_distance(far), 0.0)
