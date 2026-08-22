from django.test import SimpleTestCase
from shapely.geometry import Polygon, box, mapping

from design.maas.geometry_language.legal_envelope import (
    normalized_legal_field_design_context,
)
from design.maas.geometry_language.legal_envelope.seed_conditioning import (
    SCHEMA_VERSION,
    envelope_seed_conditioning,
)


def _context(sections):
    return normalized_legal_field_design_context({
        "candidate_legal_floor_sections": [mapping(s) for s in sections]
    })


class EnvelopeSeedConditioningTests(SimpleTestCase):
    """Seed proportions must be derivable from the lawful field alone."""

    def test_absent_lawful_context_yields_no_conditioning(self):
        for context in ({}, None, {"bands": []}, {"floor_band_count": 0}):
            with self.subTest(context=context):
                self.assertEqual(envelope_seed_conditioning(context), {})

    def test_plan_aspect_and_area_profile_come_from_the_lawful_field(self):
        # 12x8 ground, contracting to 12x6 then 12x4 - a north-sunlight cut.
        context = _context([
            box(0, 0, 12, 8),
            box(0, 0, 12, 6),
            box(0, 0, 12, 4),
        ])

        conditioning = envelope_seed_conditioning(context)

        self.assertEqual(conditioning["schema_version"], SCHEMA_VERSION)
        self.assertEqual(conditioning["plan_aspect"], 1.5)
        self.assertEqual(
            conditioning["band_area_ratios"],
            (1.0, 0.75, 0.5),
        )

    def test_prism_efficiency_ceiling_is_the_mean_lawful_area_ratio(self):
        # A straight prism on the lawful ground can only ever occupy the mean
        # of the band ratios; this is what makes a constant-section seed fail
        # its capacity target inside a contracting field.
        context = _context([
            box(0, 0, 12, 8),
            box(0, 0, 12, 6),
            box(0, 0, 12, 4),
        ])

        conditioning = envelope_seed_conditioning(context)

        self.assertAlmostEqual(
            conditioning["prism_efficiency_ceiling"],
            (1.0 + 0.75 + 0.5) / 3.0,
            places=6,
        )
        self.assertAlmostEqual(conditioning["taper_ratio"], 0.5, places=6)

    def test_conditioning_declares_itself_as_proportion_guidance(self):
        conditioning = envelope_seed_conditioning(
            _context([box(0, 0, 12, 8), box(0, 0, 12, 6)])
        )

        self.assertEqual(
            conditioning["authority"],
            "proportion_guidance_only_not_form_selection",
        )


class EnvelopeContractionDirectionTests(SimpleTestCase):
    """A seed also needs to know which way the lawful field retreats."""

    def _conditioning(self, sections):
        return envelope_seed_conditioning(_context(sections))

    def test_single_axis_contraction_is_named_with_its_retreating_side(self):
        # 12 wide stays, 8 deep shrinks to 4: one axis retreats, from one end.
        conditioning = self._conditioning([
            box(0, 0, 12, 8),
            box(0, 0, 12, 6),
            box(0, 0, 12, 4),
        ])

        self.assertEqual(conditioning["long_axis_retention"], 1.0)
        self.assertAlmostEqual(
            conditioning["short_axis_retention"], 0.5, places=6
        )
        self.assertEqual(conditioning["contraction_axis"], "short")
        self.assertIn(conditioning["contraction_side"], {"min", "max"})
        self.assertNotEqual(conditioning["centroid_drift_short"], 0.0)

    def test_an_unchanging_field_reports_no_contraction(self):
        conditioning = self._conditioning([
            box(0, 0, 12, 8),
            box(0, 0, 12, 8),
        ])

        self.assertEqual(conditioning["contraction_axis"], "none")
        self.assertEqual(conditioning["contraction_side"], "none")
        self.assertEqual(conditioning["long_axis_retention"], 1.0)
        self.assertEqual(conditioning["short_axis_retention"], 1.0)
        self.assertEqual(conditioning["centroid_drift_long"], 0.0)
        self.assertEqual(conditioning["centroid_drift_short"], 0.0)

    def test_both_axes_contracting_is_reported_as_both(self):
        conditioning = self._conditioning([
            box(0, 0, 12, 8),
            box(2, 2, 10, 6),
        ])

        self.assertEqual(conditioning["contraction_axis"], "both")
        self.assertLess(conditioning["long_axis_retention"], 1.0)
        self.assertLess(conditioning["short_axis_retention"], 1.0)

    def test_a_single_band_field_has_nothing_to_contract(self):
        conditioning = self._conditioning([box(0, 0, 12, 8)])

        self.assertEqual(conditioning["contraction_axis"], "none")
        self.assertEqual(conditioning["taper_ratio"], 1.0)


class EnvelopeNumericNoiseTests(SimpleTestCase):
    """Real parcels are not axis-aligned boxes; sub-percent wobble is not a setback."""

    def test_negligible_axis_wobble_is_not_reported_as_contraction(self):
        # The real Gangnam parcel retains 0.999969 of its long axis while the
        # short axis halves. Calling that "both" tells a seed to taper in a
        # direction the law never asked it to.
        ground = Polygon((
            (0.0, 0.0), (12.0, 0.0), (12.0, 8.0), (0.0, 8.0),
        ))
        upper = Polygon((
            (0.0002, 4.0), (11.9998, 4.0), (11.9998, 8.0), (0.0002, 8.0),
        ))

        conditioning = envelope_seed_conditioning(_context([ground, upper]))

        self.assertGreater(conditioning["long_axis_retention"], 0.999)
        self.assertLess(conditioning["short_axis_retention"], 0.6)
        self.assertEqual(conditioning["contraction_axis"], "short")
        self.assertIn(conditioning["contraction_side"], {"min", "max"})
