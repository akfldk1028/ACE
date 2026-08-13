"""A model authors a program in fractions; the executor owns the metres.

CoMa (arXiv 2601.08464) asked a VLM for footprint polygons with elevations -
this pipeline's own representation - and reported Site IoU 0.05 with frequent
self-intersecting polygons. Frontier models are measurably weakest exactly
there: GeoGramBench puts GPT-5 at 90% on basic geometric reasoning and 39% on
complex abstract levels.

So the contract is that the model never emits a coordinate. It emits fractions
of the parcel's own buildable plan and legal height, and this layer multiplies
them out. These tests hold that contract, and they run without a key: what needs
verifying is the translation from a model-shaped response into a lawful mass,
not that the network is up.
"""

from django.test import SimpleTestCase

from design.maas.massv2 import compile_matrix_form, measure_form
from design.maas.massv2.author import _to_form


BUILDABLE_W = 60.0
BUILDABLE_D = 40.0
LEGAL_H = 15.0


def _record(**overrides):
    record = {
        "name": "splayed_court",
        "primary_language": "splayed_bars",
        "secondary_language": "court",
        "formal_principle": "rotated_pair",
        "dominant_gesture": "two bars turned apart around a court",
        "reference_basis": "SANAA Rolex Learning Center",
        "placements": [
            {"role": "bar_south", "kind": "additive", "width": 0.9, "depth": 0.22,
             "height": 1.0, "x": 0.05, "y": 0.06, "z": 0.0, "rotation_degrees": -9},
            {"role": "bar_north", "kind": "additive", "width": 0.9, "depth": 0.22,
             "height": 1.0, "x": 0.05, "y": 0.62, "z": 0.0, "rotation_degrees": 11},
            {"role": "link", "kind": "additive", "width": 0.18, "depth": 0.5,
             "height": 0.35, "x": 0.4, "y": 0.25, "z": 0.5, "rotation_degrees": 0},
        ],
    }
    record.update(overrides)
    return record


def _form(**overrides):
    return _to_form(
        _record(**overrides),
        width_m=BUILDABLE_W, depth_m=BUILDABLE_D, height_m=LEGAL_H,
    )


class FractionsBecomeMetresHereTests(SimpleTestCase):
    def test_a_full_width_volume_spans_the_buildable_width(self):
        form = _to_form(
            _record(placements=[{
                "role": "slab", "kind": "additive", "width": 1.0, "depth": 1.0,
                "height": 1.0, "x": 0.0, "y": 0.0, "z": 0.0, "rotation_degrees": 0,
            }]),
            width_m=BUILDABLE_W, depth_m=BUILDABLE_D, height_m=LEGAL_H,
        )
        corners = form.placements[0].corners()

        self.assertAlmostEqual(BUILDABLE_W, max(x for x, _y, _z in corners), places=6)
        self.assertAlmostEqual(LEGAL_H, form.height_m(), places=6)

    def test_the_authored_language_survives_into_the_form(self):
        """Empty language fields collapse every candidate into one family."""

        form = _form()

        self.assertEqual("splayed_bars", form.primary_language)
        self.assertEqual("rotated_pair", form.formal_principle)
        self.assertIn("SANAA", form.reference_basis)

    def test_authored_forms_are_marked_as_authored(self):
        self.assertTrue(_form().name.startswith("llm_"))
        self.assertIn("authored_by=massv2_llm", _form().notes)


class MalformedAnswersDoNotReachGeometryTests(SimpleTestCase):
    def test_a_placement_missing_a_number_is_dropped_not_guessed(self):
        form = _form(placements=[
            {"role": "good", "kind": "additive", "width": 0.8, "depth": 0.5,
             "height": 1.0, "x": 0.0, "y": 0.0, "z": 0.0, "rotation_degrees": 0},
            {"role": "bad", "kind": "additive", "width": 0.5, "depth": 0.5},
        ])

        self.assertEqual(1, len(form.placements))

    def test_an_answer_with_no_additive_volume_is_refused(self):
        """A mass made only of cutters is not a mass."""

        form = _form(placements=[
            {"role": "hole", "kind": "subtractive", "width": 0.4, "depth": 0.4,
             "height": 1.2, "x": 0.2, "y": 0.2, "z": -0.1, "rotation_degrees": 0},
        ])

        self.assertIsNone(form)

    def test_wild_fractions_are_clamped_rather_than_trusted(self):
        """A model that answers 40.0 meant 'as big as possible', not 40x the site."""

        form = _form(placements=[{
            "role": "runaway", "kind": "additive", "width": 40.0, "depth": 0.5,
            "height": 1.0, "x": 0.0, "y": 0.0, "z": 0.0, "rotation_degrees": 900,
        }])
        corners = form.placements[0].corners()
        span = max(x for x, _y, _z in corners) - min(x for x, _y, _z in corners)

        self.assertLess(span, BUILDABLE_W * 2.0)


class AuthoredProgramsCompileAndMeasureTests(SimpleTestCase):
    def test_the_authored_scheme_becomes_a_measurable_mass(self):
        source = compile_matrix_form(_form())
        self.assertIsNotNone(source)
        measurement = measure_form(source)

        self.assertGreater(measurement.articulation(), 0.2)
        self.assertGreater(len(source.volumes), 1)
