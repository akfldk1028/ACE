from math import atan2, degrees
from types import SimpleNamespace
from unittest import TestCase
from shapely.geometry import box
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.dsl import parse_geometry_dsl
from design.maas.geometry_language.source_bridge import _pose_metric_vertices_to_host
from design.test_maas_book_delivered_areas import book_import, record

class AuthoredFacingTests(TestCase):
    def test_requested_right_angle_survives_ground_contact_search(self):
        compiled = compile_geometry_program(parse_geometry_dsl('result = box(18,4,4)'))
        placed = _pose_metric_vertices_to_host(compiled, box(0,0,20,6), clip_to_host=True, facing_angle_deg=90)
        self.assertIsNotNone(placed)
        self.assertAlmostEqual(degrees(atan2(placed.matrix4[1][0], placed.matrix4[0][0])), 90)

    def test_unrequested_pose_keeps_best_ground_contact(self):
        compiled = compile_geometry_program(parse_geometry_dsl('result = box(18,4,4)'))
        placed = _pose_metric_vertices_to_host(compiled, box(0,0,20,6), clip_to_host=True)
        self.assertAlmostEqual(placed.achieved_plan_area_m2, 72)
        self.assertAlmostEqual(placed.matrix4[1][0], 0)

    def test_nonfitting_requested_pose_is_refused_without_clipping(self):
        compiled = compile_geometry_program(parse_geometry_dsl('result = box(18,4,4)'))
        self.assertIsNone(_pose_metric_vertices_to_host(compiled, box(0,0,20,6), facing_angle_deg=90))

    def test_north_contradiction_is_refused_but_oblique_consistency_passes(self):
        # Explicit geometry fixture: eastward road, northward legal removal.
        site = SimpleNamespace(plan_at=lambda z: box(0,0,20,20 if z == 0 else 16))
        for road in ((1,0), (1,.3)):
            with self.assertRaisesRegex(ValueError, 'north_side contradicts'):
                book_import._resolve_facing({'access_side':'east', 'north_side':'south'}, site, 12, road_direction=road)
            angle, evidence = book_import._resolve_facing({'access_side':'east', 'north_side':'north'}, site, 12, road_direction=road)
            self.assertEqual(evidence['north_status'], 'verified_nearest_side')

    def test_absent_north_evidence_is_explicitly_unverified(self):
        site = SimpleNamespace(plan_at=lambda z: box(0,0,20,20))
        angle, evidence = book_import._resolve_facing({'access_side':'east', 'north_side':'south'}, site, 12, road_direction=(1,0))
        self.assertEqual(angle, 0)
        self.assertEqual(evidence['north_status'], 'unverified_preference_no_directional_setback')

    def test_optional_ast_facing_reaches_real_site_bound_compile(self):
        from unittest.mock import patch
        rec = record()  # real connected, split upper-floor BOOK-compatible AST
        rec['geometry_artifact']['authoredGeometryProgram'].setdefault('metadata', {})['facing'] = {'access_side': 'south', 'north_side': 'east'}
        site = SimpleNamespace(pnu='unregistered-unit-fixture', ground_capacity_m2=5000,
            far_capacity_m2=20000, floor_height_m=3., parcel_area_m2=10000,
            plan_at=lambda z: box(0,0,100,100 if z == 0 else 95))
        with patch('design.maas.massv2.siting.site_open_side_direction', return_value=(1.,0.)):
            source, entry = book_import._compile_record(rec, box(0,0,100,100), site)
        self.assertIsNotNone(source, entry)
        matrix = entry['delivered_floor_evidence']['normalized_host_fit_matrix4']
        self.assertAlmostEqual(degrees(atan2(matrix[1][0], matrix[0][0])), 90)
        self.assertEqual(entry['facing_evidence']['north_status'], 'verified_nearest_side')
        self.assertAlmostEqual(source.metadata['book_facing_evidence']['executed_angle_deg'], 90)

    def test_ast_author_preserves_optional_facing_and_site_fit(self):
        from design.maas.geometry_language.llm_adapter import geometry_programs_from_author_payload, _author_schema
        import jsonschema
        item = {'name': 'authored_facing', 'dsl': 'result = box(1,1,1)',
                'base_seed': 'block', 'facing': {'access_side': 'east', 'north_side': 'north'}, 'site_fit': 'impose'}
        authored = geometry_programs_from_author_payload({'programs':[item]}, expected_count=1)[0]
        self.assertEqual(authored.metadata.get('facing'), item['facing'])
        self.assertEqual(authored.metadata.get('site_fit'), 'impose')
        properties = _author_schema(1)['properties']['programs']['items']['properties']
        jsonschema.validate(item['facing'], properties['facing'])
        jsonschema.validate('impose', properties['site_fit'])

    def test_ast_author_rejects_invalid_placement_values(self):
        from design.maas.geometry_language.llm_adapter import geometry_programs_from_author_payload, GeometryAuthorError
        for fields in ({'facing': {'access_side': 'road'}}, {'site_fit': 'stretch'}):
            with self.assertRaises(GeometryAuthorError):
                geometry_programs_from_author_payload({'programs': [{'name': 'invalid_placement',
                    'dsl': 'result = box(1,1,1)', 'base_seed':'block', **fields}]}, expected_count=1)

    def test_oblique_ast_facing_cannot_be_changed_by_area_widening(self):
        from design.maas.geometry_language.source_bridge import _fit_vertices_to_host
        compiled = compile_geometry_program(parse_geometry_dsl('result = rotate(box(18,4,4), axis="z", angle_degrees=30)'))
        placed = _fit_vertices_to_host(compiled, box(0,0,100,100), facing_angle_deg=40,
            target_plan_area=20, minimum_plan_area=90, clip_to_host=True)
        self.assertIsNotNone(placed)
        self.assertAlmostEqual(degrees(atan2(placed.matrix4[1][0], placed.matrix4[0][0])), 40)
