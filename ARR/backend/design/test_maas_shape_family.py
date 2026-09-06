from unittest import TestCase
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

from shapely import affinity
from shapely.geometry import box, mapping
from shapely.ops import unary_union

from design.maas.massv2.family import family_key


class ShapeFamilyTests(TestCase):
    def test_flat_surface_values_are_not_a_section_family(self):
        base = {"ops": [{"op": "extrude", "height": .4}]}
        for height in (1., .8, .80001):
            shaped = {"ops": base["ops"] + [{"op": "shape", "top_surface": {"type": "constant", "height": height},
                        "bottom_surface": {"type": "constant", "height": 0}}]}
            self.assertEqual(family_key(base), family_key(shaped))

    def test_plan_only_authorship_uses_plan_family(self):
        scheme = {"ops": [{"op": "extrude"}, {"op": "shape", "plan_region": mapping(
            box(0,0,1,1).difference(box(.25,.25,.75,.75)))}]}
        self.assertIn('plan', next(iter(family_key(scheme)[1])))

    def records(self):
        return json.loads((Path(__file__).parent/'test_fixtures/comp04-family.json').read_text())['payload']['schemes']

    def test_actual_comp04_spatial_compositions_are_four_families(self):
        records = self.records()
        self.assertEqual(len({family_key(r) for r in records}), 4)

    def test_renamed_metadata_and_targets_keep_the_actual_family(self):
        for record in self.records():
            alias = deepcopy(record)
            for field in ('name','primary_language','secondary_language','formal_principle','dominant_gesture','reference_basis'):
                alias[field] = 'unrelated alias'
            names = {op[field]: f'neutral_{i}_{field}' for i, op in enumerate(alias['ops'])
                     for field in ('first','second') if field in op}
            for op in alias['ops']:
                op['why'] = 'different text'
                for field in ('first','second','on'):
                    if op.get(field) in names:
                        op[field] = names[op[field]]
            self.assertEqual(family_key(record), family_key(alias))

    def test_small_dimension_changes_and_polygon_traversal_keep_the_family(self):
        for record in self.records():
            variant = deepcopy(record)
            for op in variant['ops']:
                for field in ('ratio','gap','contrast'):
                    if field in op:
                        op[field] += .00001
                if 'plan_region' in op:
                    # An affine in-plan perturbation changes dimensions, not holes or connectedness.
                    for ring in op['plan_region']['coordinates']:
                        for point in ring:
                            point[0] *= .99999
                        ring.reverse()
                surface = op.get('top_surface', {})
                if surface.get('type') == 'profile':
                    for point in surface['points']:
                        point[1] = .99999*point[1]
            self.assertEqual(family_key(record), family_key(variant))

    def test_actual_rigid_translation_and_rotation_keep_the_family(self):
        from design.maas.massv2.compile import compile_matrix_form
        from design.maas.massv2.execute import execute
        from design.maas.massv2.family import SHAPE_FAMILY_REFERENCE_SPAN_M
        from design.maas.massv2.grammar import parti_from_record

        def projection(record):
            span = SHAPE_FAMILY_REFERENCE_SPAN_M
            form = execute(parti_from_record(record), buildable=box(0, 0, span, span),
                           axis=(1., 0.), height_m=span)
            source = compile_matrix_form(form, storey_height_m=0.)
            return unary_union([volume.footprint for volume in source.volumes])

        for record in self.records():
            original = projection(record)
            for op in ({'op': 'shift', 'ratio': .23, 'toward': 'cross'},
                       {'op': 'rotate', 'degrees': 37}):
                with self.subTest(name=record['name'], op=op['op']):
                    variant = deepcopy(record)
                    variant['ops'].append(op)
                    transformed = projection(variant)
                    # Verify that these grammar parameters really move the geometry,
                    # rather than accidentally testing an ignored/no-op argument.
                    self.assertGreater(original.symmetric_difference(transformed).area, 1.)
                    self.assertAlmostEqual(original.area, transformed.area, places=7)
                    if op['op'] == 'shift':
                        delta = (transformed.centroid.x-original.centroid.x,
                                 transformed.centroid.y-original.centroid.y)
                        restored = affinity.translate(transformed, -delta[0], -delta[1])
                    else:
                        # A common pivot only affects translation after undoing rotation.
                        restored = affinity.rotate(transformed, -op['degrees'], origin=(0, 0))
                        restored = affinity.translate(restored,
                            original.centroid.x-restored.centroid.x,
                            original.centroid.y-restored.centroid.y)
                    self.assertAlmostEqual(original.symmetric_difference(restored).area, 0., places=7)
                    self.assertEqual(family_key(record), family_key(variant))

    def test_removed_identity_shape_and_overwritten_surface_do_not_create_a_family(self):
        houses = self.records()[3]
        alias = deepcopy(houses)
        alias['ops'].append({'op':'shape','on':'resident','plan_region':mapping(box(0,0,1,1)),
            'top_surface':{'type':'constant','height':1},'bottom_surface':{'type':'constant','height':0}})
        self.assertEqual(family_key(houses), family_key(alias))
        base = {'ops':[{'op':'extrude','height':.4}]}
        overwritten = deepcopy(base)
        overwritten['ops'] += [{'op':'shape','top_surface':{'type':'profile','points':[[0,.5],[1,1]],'axis':[1,0],'span':[0,1]}},
                              {'op':'shape','top_surface':{'type':'constant','height':1}}]
        self.assertEqual(family_key(base), family_key(overwritten))

    def test_profile_ridge_and_valley_are_distinct_but_linear_surface_encodings_agree(self):
        def with_surface(surface):
            return {'ops':[{'op':'extrude','height':.5},{'op':'shape','top_surface':surface}]}
        def profile(points):
            return {'type':'profile','points':points,'axis':[1,0],'span':[0,1]}
        self.assertNotEqual(family_key(with_surface(profile([[0,.5],[.5,1],[1,.5]]))),
                            family_key(with_surface(profile([[0,1],[.5,.5],[1,1]]))))
        self.assertEqual(family_key(with_surface(profile([[0,.5],[1,1]]))),
                         family_key(with_surface({'type':'polynomial','terms':[[0,0,.5],[1,0,.5]]})))

    def test_nonshape_family_contract_is_preserved(self):
        for ops, expected in [
            ([{'op':'extrude','height':.4}], ('extrude',frozenset(), 'low')),
            ([{'op':'extrude','height':.6},{'op':'split'},{'op':'split'}], ('extrude',frozenset({'cut'}),'mid')),
            ([{'op':'extrude','height':.8},{'op':'gable'}], ('extrude',frozenset({'gable'}),'tall')),
            ([{'op':'aggregate','method':'stack','height':.5},{'op':'nest'}], ('aggregate_stack',frozenset({'relational'}),'mid'))]:
            self.assertEqual(family_key({'ops':ops}), expected)

    def test_shared_validator_accepts_four_actual_records_and_rejects_a_renamed_duplicate(self):
        sys.path.insert(0, str(Path(__file__).parent.parent/'tmp_mass_check/_massv2/tools'))
        from validate_authored import _repeated_families
        records = self.records()
        self.assertEqual(_repeated_families(records), [])
        duplicate = deepcopy(records[0]); duplicate['name'] = 'new name'
        self.assertEqual(len(_repeated_families(records+[duplicate])), 1)

    def test_complete_shared_validator_accepts_frozen_comp04_payload(self):
        sys.path.insert(0, str(Path(__file__).parent.parent/'tmp_mass_check/_massv2/tools'))
        from validate_authored import check
        fixture = json.loads((Path(__file__).parent/'test_fixtures/comp04-family.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'authored.json'
            path.write_text(json.dumps(fixture['payload'], ensure_ascii=False), encoding='utf-8')
            faults, _, _ = check(path)
        self.assertEqual(faults, [])
