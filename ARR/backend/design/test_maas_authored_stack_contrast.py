"""Authored equal tiers are a choice; tests measure the executed solids."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from shapely.geometry import MultiPoint, box
from design.maas.massv2.grammar import parti_from_record
from design.maas.massv2.execute import execute, delivered
from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.form import MatrixForm, place, stack
from design.maas.massv2.structure import assess_standing

sys.path.insert(0, str(Path(__file__).parents[1] / 'tmp_mass_check/_massv2/tools'))
from validate_authored import check


def record(contrast=1.0, grow=False, rotate=True):
    op = {'op': 'stack', 'n': 3, 'grow': grow, 'why': 'Equal occupied tiers share bearing areas'}
    if contrast is not None:
        op['contrast'] = contrast
    ops = [op]
    if rotate:
        ops.append({'op': 'rotate', 'degrees': 18, 'on': 'tier_1',
                    'why': 'Turn the middle room toward a different frontage'})
    return dict(name='equal_rotated_tiers', primary_language='solid_body',
                secondary_language='carved_body', formal_principle='Shared bearing, different frontages',
                dominant_gesture='Turn one occupied body', reference_basis='Abstract relation study', ops=ops)


def form(contrast=1.0, **kwargs):
    return execute(parti_from_record(record(contrast, **kwargs)), buildable=box(0, 0, 20, 16),
                   axis=(1., 0.), height_m=12., storey_height_m=4.)


def areas(value):
    return {p.role: MultiPoint([(x, y) for x, y, _ in p.corners()]).convex_hull.area
            for p in value.placements}


class AuthoredStackContrastTests(unittest.TestCase):
    def test_equal_contrast_is_accepted_by_author_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.json'
            path.write_text(json.dumps({'schemes': [record()]}), encoding='utf-8')
            faults, _, _ = check(path)
        self.assertEqual(faults, [])

    def test_explicit_equal_tiers_survive_rotation_and_delivery(self):
        raw = form()
        for candidate in (raw, delivered(raw, axis=(1., 0.), storey_m=4.)):
            measured = areas(candidate)
            self.assertEqual(len(measured), 3)
            for area in measured.values():
                self.assertAlmostEqual(area, 320., places=6)
            source = compile_matrix_form(candidate, storey_height_m=4.)
            self.assertIsNotNone(source)
        plans = {p.role: MultiPoint([(x,y) for x,y,_ in p.corners()]).convex_hull for p in raw.placements}
        self.assertGreater(plans['tier_0'].symmetric_difference(plans['tier_1']).area, 1.)

    def test_equal_tiers_are_equal_in_both_growth_directions(self):
        for grow in (False, True):
            with self.subTest(grow=grow):
                for area in areas(form(grow=grow)).values():
                    self.assertAlmostEqual(area, 320., places=6)

    def test_small_explicit_contrast_is_not_silently_increased(self):
        measured = areas(form(1.1, rotate=False))
        self.assertAlmostEqual(measured['tier_1'] / measured['tier_0'], 1 / 1.1**2, places=8)

    def test_omitted_contrast_retains_existing_default_shape(self):
        implicit, explicit = form(None), form(1.35)
        self.assertEqual([p.matrix for p in implicit.placements], [p.matrix for p in explicit.placements])

    def test_existing_matrix_stack_already_preserves_equal_plans(self):
        placements = stack('body', size=(20,16,12), storeys=3, twist_degrees=36, taper=1.)
        candidate = MatrixForm(name='matrix stack control', placements=placements, primary_language='solid_body')
        self.assertIsNotNone(compile_matrix_form(candidate, storey_height_m=4.))
        for p in placements:
            self.assertAlmostEqual(MultiPoint([(x,y) for x,y,_ in p.corners()]).convex_hull.area, 320., places=6)

    def test_floating_equal_body_is_still_refused(self):
        candidate = MatrixForm(name='unsupported control', primary_language='solid_body', placements=(
            place('base', size=(20,16,4)), place('floating', size=(20,16,4), at=(0,0,8))))
        source = compile_matrix_form(candidate, storey_height_m=4.)
        self.assertIsNotNone(source)
        self.assertFalse(assess_standing(source, height_m=12.).stands)
