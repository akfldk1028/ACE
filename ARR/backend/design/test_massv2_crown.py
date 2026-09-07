"""crown: a body's own top as a dome, a dish or a saddle, said in one word.

The typed polynomial surface already compiled, sliced, gated and rendered;
no sentence could reach it except as a table of coefficients. These tests
read the compiled sections, which is what every gate reads.
"""
from django.test import SimpleTestCase
from shapely.geometry import Point, box

from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.execute import CROWN_FORMS, crown_terms, execute
from design.maas.massv2.grammar import parti_from_record


def _parti(form: str, sag: float, **extra):
    return parti_from_record({
        "name": f"crown_{form}",
        "primary_language": "solid_body",
        "ops": [
            {"op": "extrude", "profile": "square", "height": 0.6, "storeys": 3,
             "why": "one body"},
            {"op": "crown", "form": form, "sag": sag, **extra,
             "why": f"a {form} top, said in one word"},
        ],
    })


class CrownTermsTests(SimpleTestCase):
    def _value(self, terms, x, y):
        return sum(c * x ** i * y ** j for i, j, c in terms)

    def test_dome_is_one_at_the_centre_and_lower_at_the_corners(self):
        terms = crown_terms("dome", 0.4)
        self.assertAlmostEqual(self._value(terms, 0.5, 0.5), 1.0)
        self.assertAlmostEqual(self._value(terms, 0.0, 0.0), 0.6)
        self.assertAlmostEqual(self._value(terms, 0.0, 0.5), 0.8)

    def test_dish_is_lowest_at_the_centre_and_one_at_the_corners(self):
        terms = crown_terms("dish", 0.4)
        self.assertAlmostEqual(self._value(terms, 0.5, 0.5), 0.6)
        self.assertAlmostEqual(self._value(terms, 1.0, 1.0), 1.0)

    def test_saddle_rises_along_one_axis_and_falls_along_the_other(self):
        terms = crown_terms("saddle", 0.4)
        self.assertAlmostEqual(self._value(terms, 0.0, 0.5), 1.0)
        self.assertAlmostEqual(self._value(terms, 0.5, 0.0), 0.6)
        self.assertAlmostEqual(self._value(terms, 0.5, 0.5), 0.8)
        swapped = crown_terms("saddle", 0.4, along_x=False)
        self.assertAlmostEqual(self._value(swapped, 0.5, 0.0), 1.0)
        self.assertAlmostEqual(self._value(swapped, 0.0, 0.5), 0.6)

    def test_no_form_exceeds_the_band(self):
        for form in CROWN_FORMS:
            terms = crown_terms(form, 0.6)
            top = max(self._value(terms, x / 10, y / 10) for x in range(11) for y in range(11))
            self.assertLessEqual(top, 1.0 + 1e-9, form)

    def test_unknown_form_is_refused(self):
        with self.assertRaises(ValueError):
            crown_terms("onion", 0.3)


class CrownCompilesTests(SimpleTestCase):
    def setUp(self):
        self.buildable = box(0.0, 0.0, 40.0, 40.0)
        self.height = 12.0

    def _compiled(self, form, sag=0.4, **extra):
        parti = _parti(form, sag, **extra)
        self.assertIsNotNone(parti)
        form_ = execute(parti, buildable=self.buildable, axis=(1.0, 0.0),
                        height_m=self.height, storey_height_m=4.0)
        self.assertIsNotNone(form_)
        source = compile_matrix_form(form_, storey_height_m=4.0, allowed_at=None)
        self.assertIsNotNone(source)
        return source

    def _centre(self, source):
        union = None
        for volume in source.volumes:
            union = volume.footprint if union is None else union.union(volume.footprint)
        return union.centroid

    def test_a_dome_section_keeps_the_centre_and_loses_the_corners_near_the_top(self):
        source = self._compiled("dome", 0.4)
        self.assertTrue(any(v.section_kind() == "surface" for v in source.volumes))
        height = float(source.metadata["authored_height_m"])
        top = max(float(v.top_fraction) for v in source.volumes) * height
        centre = self._centre(source)
        near_top = source.plan_at(top - 0.05 * height)
        self.assertIsNotNone(near_top)
        self.assertTrue(near_top.contains(centre))
        footprint = source.volumes[0].footprint
        self.assertLess(near_top.area, 0.6 * footprint.area)

    def test_a_dish_section_loses_the_centre_first(self):
        source = self._compiled("dish", 0.4)
        height = float(source.metadata["authored_height_m"])
        top = max(float(v.top_fraction) for v in source.volumes) * height
        centre = self._centre(source)
        section = source.plan_at(top - 0.15 * height)
        self.assertIsNotNone(section)
        self.assertFalse(section.contains(centre))

    def test_a_saddle_section_splits_into_two_lobes_below_the_ridge(self):
        source = self._compiled("saddle", 0.5)
        height = float(source.metadata["authored_height_m"])
        top = max(float(v.top_fraction) for v in source.volumes) * height
        section = source.plan_at(top - 0.1 * height)
        self.assertIsNotNone(section)
        parts = getattr(section, "geoms", [section])
        self.assertEqual(len(list(parts)), 2)

    def test_lift_raises_a_crowned_body_with_its_crown_on(self):
        parti = parti_from_record({
            "name": "crown_then_lift",
            "primary_language": "porous_field",
            "ops": [
                {"op": "aggregate", "n": 4, "spread": 1.4, "height": 0.5, "storeys": 3, "tie": 0.2,
                 "why": "four rooms"},
                {"op": "crown", "form": "dish", "sag": 0.35, "why": "dished tops"},
                {"op": "lift", "clearance": 0.3, "why": "on supports"},
            ],
        })
        form_ = execute(parti, buildable=self.buildable, axis=(1.0, 0.0),
                        height_m=self.height, storey_height_m=4.0)
        bodies = [p for p in form_.placements if p.kind == "additive" and p.occupiable]
        self.assertTrue(bodies)
        self.assertTrue(all(p.top_surface is not None for p in bodies),
                        "lift rebuilt the bodies and dropped their crowns")

    def test_the_crowned_body_holds_less_than_its_prism(self):
        prism = self._compiled("dome", 0.05)
        domed = self._compiled("dome", 0.5)
        height = float(domed.metadata["authored_height_m"])
        self.assertLess(domed.mass_properties(height)[0], prism.mass_properties(height)[0])
