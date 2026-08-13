"""The fit owes the parcel two ceilings and a shrinking envelope.

Each of these pins a defect that was live, found by measurement on the Uijeongbu
parcel, and fixed. They run without a network: what needs holding is the
arithmetic of the fit, not that Vworld is up.

  건축면적 is a projection, so only plan can pay for it.
  용적률 is plan times storeys, so height pays for it - and it moves in whole
    storeys, because storeys are counted with `round`.
  정북일조 shrinks the legal plan as height rises, and a volume may answer either
    by stepping back or by stopping lower.

The fit and the report must also agree about what a floor is. They did not, and
that alone reported four lawful schemes as over the ceiling.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.massv2 import MatrixForm, compile_matrix_form, place
from design.maas.massv2.legal_fit import _gross_floor_area, fit_to_site
from design.maas.massv2.measure import gross_floor_area_m2, storeys_in
from design.maas.massv2.variations import spread_across_coverage


SITE = Polygon([(0, 0), (80, 0), (80, 60), (0, 60)])


def _site(*, ground_capacity=500.0, far_capacity=2500.0, floor_height=3.0, taper=0.0):
    """A parcel stub whose legal plan optionally shrinks with height.

    `taper` metres of inset per metre of height stands in for the north sunlight
    envelope, which is all the fit needs from it.
    """

    def plan_at(height_m: float):
        inset = taper * float(height_m)
        if inset <= 0.0:
            return SITE
        shrunk = SITE.buffer(-inset)
        return shrunk if not shrunk.is_empty else Polygon()

    return SimpleNamespace(
        ground_capacity_m2=ground_capacity,
        far_capacity_m2=far_capacity,
        floor_height_m=floor_height,
        plan_at=plan_at,
        site_local_utm=SITE,
    )


def _form(*placements, name="scheme", **kwargs):
    kwargs.setdefault("primary_language", "test")
    return MatrixForm(name=name, placements=tuple(placements), **kwargs)


class GroundAreaIsPaidInPlanTests(SimpleTestCase):
    def test_an_oversized_footprint_is_brought_to_the_ceiling(self):
        """It came in at 611.7 m2 against 499.9 and was carved before this."""

        fit = fit_to_site(_form(place("block", size=(40, 30, 12))), _site())

        self.assertLessEqual(fit.ground_area_m2, 500.0 + 1e-6)
        self.assertTrue(fit.satisfied)

    def test_height_is_not_spent_on_ground_area(self):
        """건축면적 is a horizontal projection; paying it in height is a category
        error that would trade one law for another silently."""

        form = _form(place("block", size=(40, 30, 12)))
        fit = fit_to_site(form, _site())
        low = min(item.z_span()[0] for item in fit.form.additive())
        high = max(item.z_span()[1] for item in fit.form.additive())

        self.assertAlmostEqual(12.0, high - low, places=3)

    def test_a_lawful_footprint_is_left_alone(self):
        form = _form(place("block", size=(20, 20, 9)))
        fit = fit_to_site(form, _site())

        self.assertAlmostEqual(1.0, fit.plan_scale_applied, places=6)


class FloorAreaIsPaidInHeightTests(SimpleTestCase):
    def test_a_scheme_over_the_far_ceiling_is_brought_under_it(self):
        # 400 m2 over 30 m at 3 m storeys is 4,000 m2 against a 2,500 ceiling.
        form = _form(place("tower", size=(20, 20, 30)))
        site = _site(far_capacity=2500.0)
        fit = fit_to_site(form, site)

        self.assertLessEqual(fit.gross_floor_area_m2, site.far_capacity_m2 + 1e-6)
        self.assertTrue(fit.satisfied)

    def test_a_lawful_scheme_keeps_its_height(self):
        form = _form(place("block", size=(20, 20, 9)))
        fit = fit_to_site(form, _site())

        self.assertAlmostEqual(9.0, fit.form.height_m(), places=3)


class OneStoreyRuleEverywhereTests(SimpleTestCase):
    def test_the_fit_and_the_report_agree_on_floor_area(self):
        """They did not, and four lawful schemes were reported over the ceiling.

        The fit measured each placement over its own full height while the
        report measured the compiled bands; a volume ten metres tall is three
        storeys whole and four once it is cut at five.
        """

        form = _form(
            place("plinth", size=(24, 20, 6)),
            place("tower", size=(14, 14, 12), at=(4, 3, 5.9)),
        )
        source = compile_matrix_form(form)

        self.assertAlmostEqual(
            _gross_floor_area(form, floor_height_m=3.0),
            gross_floor_area_m2(source, floor_height_m=3.0),
            places=6,
        )

    def test_a_hand_deep_overlap_is_not_a_floor(self):
        """Stacked volumes overlap so the boolean is not degenerate; counting
        that sliver as a storey is what put schemes 1% over the ceiling."""

        self.assertEqual(0, storeys_in(0.1, floor_height_m=3.0))
        self.assertEqual(1, storeys_in(3.0, floor_height_m=3.0))
        self.assertEqual(2, storeys_in(7.0, floor_height_m=3.0))

    def test_the_storey_height_is_the_scheme_s_own_when_it_declares_one(self):
        """A gallery is not a shop. Fixing every scheme at the zoning height
        makes floor count a fact about the parcel instead of the programme."""

        tall = _form(place("hall", size=(20, 20, 24)), floor_height_m=8.0)
        default = _form(place("hall", size=(20, 20, 24)))

        self.assertLess(
            _gross_floor_area(tall, floor_height_m=8.0),
            _gross_floor_area(default, floor_height_m=3.0),
        )


class SunlightMayBePaidEitherWayTests(SimpleTestCase):
    def test_a_volume_just_outside_steps_back_rather_than_shrinking_away(self):
        site = _site(taper=0.10)
        form = _form(place("block", size=(22, 22, 12), at=(2, 2, 0)))
        fit = fit_to_site(form, site)

        self.assertTrue(fit.form.additive())
        self.assertTrue(fit.satisfied)

    def test_a_tall_volume_may_stop_lower_instead_of_being_pinched_away(self):
        """Paying only in plan pinched a tall volume to a sliver or dropped it,
        when stopping below the height where the envelope bites keeps the
        author's proportions."""

        site = _site(taper=0.45)
        form = _form(place("tower", size=(30, 30, 40), at=(24, 14, 0)))
        fit = fit_to_site(form, site)

        self.assertTrue(fit.form.additive(), "the volume was dropped entirely")
        self.assertLess(fit.form.height_m(), 40.0)


class CoverageCopiesHoldOnlyALawfulProgrammeTests(SimpleTestCase):
    def test_a_copy_at_lower_ground_take_is_not_simply_a_smaller_picture(self):
        """A 45% copy at the same height delivers 45% of the floor area and
        reads as an under-built site - measured at 9% 용적률 before this."""

        site = _site()
        form = _form(place("block", size=(30, 24, 15)))
        copies = spread_across_coverage(
            form,
            ground_capacity_m2=site.ground_capacity_m2,
            far_capacity_m2=site.far_capacity_m2,
            floor_height_m=site.floor_height_m,
        )
        smallest = min(copies, key=lambda item: item.height_m())
        tallest = max(copies, key=lambda item: item.height_m())

        self.assertGreater(tallest.height_m(), smallest.height_m())

    def test_an_unlawful_programme_is_not_preserved(self):
        """A U covering most of the buildable plan carried 7,183 m2 against a
        2,500 ceiling; holding that at 45% ground take asked for 6.6x the height
        and produced an 80 m building nothing could trim back.
        """

        site = _site()
        huge = _form(place("slab", size=(78, 58, 15)))
        copies = spread_across_coverage(
            huge,
            ground_capacity_m2=site.ground_capacity_m2,
            far_capacity_m2=site.far_capacity_m2,
            floor_height_m=site.floor_height_m,
        )

        for copy in copies:
            with self.subTest(copy=copy.name):
                self.assertLess(copy.height_m(), 60.0)

    def test_every_copy_survives_the_fit_lawfully(self):
        site = _site(taper=0.05)
        form = _form(
            place("bar_s", size=(34, 9, 15)),
            place("bar_n", size=(34, 9, 15), at=(0, 15, 0)),
        )
        copies = spread_across_coverage(
            form,
            ground_capacity_m2=site.ground_capacity_m2,
            far_capacity_m2=site.far_capacity_m2,
            floor_height_m=site.floor_height_m,
        )

        for copy in copies:
            with self.subTest(copy=copy.name):
                fit = fit_to_site(copy, site)
                self.assertTrue(fit.satisfied)
                self.assertLessEqual(fit.ground_area_m2, site.ground_capacity_m2 + 1e-6)
                self.assertLessEqual(fit.gross_floor_area_m2, site.far_capacity_m2 + 1e-6)
