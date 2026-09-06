from dataclasses import replace
import unittest

from shapely.geometry import Polygon, box
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.creative_program_author import authored_programs_from_payload, authored_program_result, normalize_authored_programs
from design.maas.creative_floor_portfolio import _compile_candidate


def intent(**overrides):
    return dict(schema_version='arr.maas.dimensional_intent.v1', storey_count=4,
                storey_height_m=3.5, target_gfa_m2=320.0,
                delivery_policy='preserve_physical_dimensions', programme_status='unknown', **overrides)


def source(contract=None):
    return GeometryProgram(name='authored_bar', root_id='body', nodes=(
        GeometryNode('body', 'primitive', 'box', parameters={'width': 2., 'depth': 1., 'height': 1.}),
    ), metadata={} if contract is None else {'dimensional_intent': contract})


def physical(program, index=0):
    authored = normalize_authored_programs((program,))[0]
    return _compile_candidate(authored_program_result(authored), family='test', source_family='llm_authored',
        family_index=index, variation_index=index, candidate_index=index,
        capacity_band='spatial_reserve' if index == 0 else 'balanced_yield', capacity_ceiling_m2=1000.)


class DimensionalIntentTests(unittest.TestCase):
    def test_explicit_physical_dimensions_do_not_depend_on_index(self):
        first, second = physical(source(intent()), 0), physical(source(intent()), 1)
        self.assertIsNotNone(first)
        self.assertEqual(first['geometry_hash'], second['geometry_hash'])
        self.assertEqual(first['storey_evidence']['storey_count'], 4)
        self.assertAlmostEqual(first['storey_evidence']['actual_gfa_m2'], 320., places=3)

    def test_invalid_exact_payload_contract_is_rejected_at_ingestion(self):
        for field, value in [('storey_count', True), ('storey_count', 2.5), ('storey_height_m', float('nan')),
                             ('target_gfa_m2', -1), ('delivery_policy', 'grow_to_far'), ('programme_status', 'compliant')]:
            bad = intent(); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                authored_programs_from_payload({'geometry_programs':[source(bad).to_dict()]}, expected_count=1)

    def test_metric_pose_on_irregular_host_or_explicit_refusal(self):
        from design.maas.geometry_language.source_bridge import compile_geometry_program_to_source_mass
        program = GeometryProgram.from_dict(physical(source(intent()))['geometry_program'])
        host = Polygon([(0,0),(45,0),(45,26),(22,36),(0,30)])
        result = compile_geometry_program_to_source_mass(program, host,
            placement_policy='preserve_physical_dimensions', max_volume_bands=4)
        self.assertIsNotNone(result)
        matrix = result.metadata['geometry_program_bridge_evidence']['host_fit_matrix4']
        self.assertAlmostEqual(sum(matrix[i][0]**2 for i in range(2)), 1., places=8)
        self.assertAlmostEqual(sum(matrix[i][1]**2 for i in range(2)), 1., places=8)
        self.assertIsNone(compile_geometry_program_to_source_mass(program, box(0,0,2,2),
            placement_policy='preserve_physical_dimensions', max_volume_bands=4))

    def test_legacy_index_behavior_remains(self):
        self.assertEqual(physical(source(), 0)['storey_evidence']['storey_count'], 3)
        self.assertEqual(physical(source(), 1)['storey_evidence']['storey_count'], 5)

    def test_import_retains_requested_effective_delivered_and_refuses_changed_schedule(self):
        from copy import deepcopy
        from types import SimpleNamespace
        from design.test_maas_book_delivered_areas import book_import
        candidate = physical(source(intent()))
        rec = {'trace_sequence_name': 'dimensional-test', 'geometry_artifact': {
            'authoredGeometryProgram': candidate['geometry_program'], 'storeyEvidence': candidate['storey_evidence'],
            'projectedVisualCertificate': {'physical_height_m': 14.0},
            'hardGates': {'projectedMetrics': {'footprint_area_m2': 80., 'floor_area_m2': 320.}}}}
        site = SimpleNamespace(pnu='test', ground_capacity_m2=1500, far_capacity_m2=6000,
                               floor_height_m=3.8, parcel_area_m2=10000)
        host = Polygon([(0,0),(45,0),(45,26),(22,36),(0,30)])
        delivered, entry = book_import._compile_record(rec, host, site)
        self.assertIsNotNone(delivered, entry)
        proof = entry['dimensional_intent_evidence']
        self.assertEqual(proof['programme_status'], 'unknown')
        self.assertEqual(proof['requested'], intent())
        self.assertAlmostEqual(proof['delivered']['gfa_m2'], 320., places=3)
        self.assertEqual(proof['delivered']['height_m'], 14.)
        refused, reason = book_import._compile_record(rec, box(0,0,2,2), site)
        self.assertIsNone(refused)
        self.assertIn('without resizing', reason)
        rec['geometry_artifact']['storeyEvidence']['typical_storey_height_m'] = 4.
        refused, reason = book_import._compile_record(rec, host, site)
        self.assertIsNone(refused)
        self.assertIn('disagrees', reason)

    def test_book_projection_retains_explicit_schedule_and_original_intent(self):
        from design.maas.creative_floor_portfolio import build_creative_floor_portfolio
        result = build_creative_floor_portfolio(count=1, capacity_ceiling_m2=1000., authored_programs=[source(intent())])
        self.assertEqual(result['original_count'], 1)
        self.assertEqual(result['exploration_count'], 1)
        for candidate in result['candidates']:
            self.assertEqual(candidate['storey_evidence']['storey_count'], 4)
            self.assertEqual(candidate['dimensional_intent_evidence']['requested'], intent())
            self.assertAlmostEqual(candidate['storey_evidence']['actual_gfa_m2'], 320., places=3)

    def test_structured_contract_survives_author_conversion(self):
        from design.maas.geometry_language.llm_adapter import _author_schema
        payload = {'programs': [{'name': 'explicit_proposal', 'base_seed':'block', 'base_form_id':'cube',
            'intent_tags':['programme_unknown'], 'rationale':'One physical proposal among differing alternatives',
            'dsl': 'base = box(1, 1, 1)\nresult = matrix4(base, matrix4=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])',
            'dimensional_intent': intent()}]}
        programs = authored_programs_from_payload(payload, expected_count=1)
        self.assertEqual(programs[0].program.metadata['dimensional_intent'], intent())
        self.assertIn('dimensional_intent', _author_schema(1)['properties']['programs']['items']['properties'])
        payload['programs'][0]['dimensional_intent']['delivery_policy'] = 'grow_to_far'
        with self.assertRaises(ValueError):
            authored_programs_from_payload(payload, expected_count=1)

    def test_rotated_stack_levels_survive_explicit_physicalization_and_delivery(self):
        from design.maas.geometry_language.dsl import parse_geometry_dsl
        from design.maas.geometry_language.source_bridge import compile_geometry_program_to_source_mass, mesh_section_solid, solid_section_polygon
        program = parse_geometry_dsl('result = union(box(2,1,0.8), translate(rotate(box(2,1,0.8), axis="z", angle_degrees=20), vector=[0,0,0.7]), translate(rotate(box(2,1,0.8), axis="z", angle_degrees=-20), vector=[0,0,1.4]), translate(rotate(box(2,1,0.8), axis="z", angle_degrees=10), vector=[0,0,2.1]))')
        program = replace(program, metadata={**program.metadata, 'dimensional_intent':intent()})
        candidate = physical(program)
        self.assertIsNotNone(candidate)
        result = compile_geometry_program_to_source_mass(GeometryProgram.from_dict(candidate['geometry_program']),
            Polygon([(0,0),(45,0),(45,26),(22,36),(0,30)]), placement_policy='preserve_physical_dimensions', max_volume_bands=4)
        self.assertIsNotNone(result)
        vertices = tuple(p for surface in result.surfaces for p in surface.vertices_m)
        solid = mesh_section_solid(vertices, tuple((i,i+1,i+2) for i in range(0,len(vertices),3)))
        sections = [solid_section_polygon(solid,(i+.5)/4) for i in range(4)]
        self.assertTrue(all(p is not None and p.area>0 for p in sections))
        self.assertEqual(len({p.normalize().wkb for p in sections}),4)

    def test_provider_schema_required_nullable_contract_and_null_is_legacy(self):
        from design.maas.geometry_language.llm_adapter import _author_schema
        schema = _author_schema(1)['properties']['programs']['items']
        self.assertIn('dimensional_intent', schema['required'])
        self.assertIn({'type':'null'}, schema['properties']['dimensional_intent']['anyOf'])
        authored = authored_programs_from_payload({'geometry_programs':[source().to_dict()]}, expected_count=1)[0]
        explicit_null = authored_programs_from_payload({'geometry_programs':[replace(source(), metadata={'dimensional_intent':None}).to_dict()]}, expected_count=1)[0]
        self.assertEqual(physical(authored.program)['geometry_hash'],physical(explicit_null.program)['geometry_hash'])

    def test_macro_anchor_is_offered_as_supported_string_parameter(self):
        from design.maas.geometry_language.ast import MACRO_VERTICAL_ANCHORS, MACRO_VERTICAL_ANCHOR_OPERATORS
        from design.maas.geometry_language.mutation import OPERATOR_PARAMETER_CONTRACTS
        from design.maas.geometry_language.author_parameter_contract import author_parameter_value_contract
        for operator in MACRO_VERTICAL_ANCHOR_OPERATORS:
            self.assertIn('vertical_anchor',OPERATOR_PARAMETER_CONTRACTS[operator])
            self.assertEqual(author_parameter_value_contract(operator,'vertical_anchor'),
                             {'type':'string','enum':sorted(MACRO_VERTICAL_ANCHORS)})

    def test_exact_development_transitions_proposal_to_verified_parent_authority(self):
        from design.maas.book_development import MODE, build_exact_development_portfolio
        context = dict(parent='p',parent_shape_id='shape',parent_program_hash='hash',parent_certificate_id='cert',
                       site_pnu='test',storey_count=4,storey_height_m=3.5,height_m=14.,target_gfa_m2=320.00001)
        payload = dict(mode=MODE,inherit_parent_dimensions=True,parent='p',parent_shape_id='shape',
                       parent_program_hash='hash',geometry_programs=[source(intent()).to_dict()])
        child = build_exact_development_portfolio(payload,context,expected_count=1)['candidates'][0]
        metadata = child['geometry_program']['metadata']
        self.assertNotIn('dimensional_intent',metadata)
        self.assertEqual(metadata['dimensional_intent_transition']['historical_proposal'],intent())
        self.assertEqual(child['development_lineage']['authored_program']['metadata']['dimensional_intent'],intent())
        self.assertAlmostEqual(child['storey_evidence']['target_gfa_m2'],context['target_gfa_m2'],places=5)
        payload['geometry_programs'][0]['metadata']['dimensional_intent']['storey_count']=3
        with self.assertRaisesRegex(ValueError,'conflicts'):
            build_exact_development_portfolio(payload,context,expected_count=1)
