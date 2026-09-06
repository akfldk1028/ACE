from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.test_maas_creative_program_author import _authored_unitbox_program
from design.maas import creative_floor_portfolio as portfolio
from design.maas.geometry_language.ast import GeometryProgram


class ExactBookDevelopmentTests(SimpleTestCase):
    def context(self):
        return {'parent': 'book:test:parent', 'parent_shape_id': 'parent-shape',
                'parent_program_hash': _authored_unitbox_program().program_hash(),
                'parent_certificate_id': 'parent-certificate', 'site_pnu': 'test',
                'storey_count': 3, 'storey_height_m': 5.2, 'target_gfa_m2': 1000.0,
                'height_m': 15.6}

    def payload(self):
        context = self.context()
        return {**{k: context[k] for k in ('parent', 'parent_shape_id', 'parent_program_hash')},
                'mode': 'exact-authored-development', 'inherit_parent_dimensions': True,
                'geometry_programs': [replace(_authored_unitbox_program(), name='child-a').to_dict()]}

    def test_parent_binding_and_exact_count_before_compilation(self):
        from design.maas.book_development import validate_development_payload
        for key in ('parent', 'parent_shape_id', 'parent_program_hash'):
            payload = self.payload()
            payload[key] = 'wrong'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                validate_development_payload(payload, self.context(), expected_count=1)
        with self.assertRaisesRegex(ValueError, 'exactly'):
            validate_development_payload(self.payload(), self.context(), expected_count=2)
        with self.assertRaisesRegex(ValueError, 'exactly'):
            validate_development_payload(self.payload(), self.context(), expected_count=0)

    def test_exact_program_preserves_own_ruler_without_book_projection(self):
        from design.maas.book_development import build_exact_development_portfolio
        with patch.object(portfolio, 'project_creative_book_program', side_effect=AssertionError('unrequested BOOK operation')):
            result = build_exact_development_portfolio(self.payload(), self.context(), expected_count=1)
        child = result['candidates'][0]
        self.assertEqual(child['storey_evidence']['storey_count'], 3)
        self.assertEqual(child['storey_evidence']['typical_storey_height_m'], 5.2)
        self.assertAlmostEqual(child['mesh_evidence']['bounds'][1][2], 15.6, places=5)
        self.assertAlmostEqual(child['storey_evidence']['actual_gfa_m2'], 1000, places=3)
        nodes = child['geometry_program']['nodes']
        self.assertFalse(any(n.get('provenance', {}).get('source') == 'book_recursive_projection' for n in nodes))
        self.assertEqual(child['development_lineage']['authored_program'], self.payload()['geometry_programs'][0])

    def test_reordering_does_not_change_each_child_geometry_or_storeys(self):
        from design.maas.book_development import build_exact_development_portfolio
        payload = self.payload()
        second = deepcopy(payload['geometry_programs'][0])
        second['name'] = 'child-b'
        second['nodes'][0]['parameters']['depth'] = 0.9
        payload['geometry_programs'].append(second)
        a = build_exact_development_portfolio(payload, self.context(), expected_count=2)
        payload['geometry_programs'].reverse()
        b = build_exact_development_portfolio(payload, self.context(), expected_count=2)
        key = lambda r: {c['development_lineage']['authored_program']['name']: c['geometry_hash'] for c in r['candidates']}
        self.assertEqual(key(a), key(b))

    def test_default_exploration_ast_and_mesh_are_unchanged(self):
        result = portfolio.build_creative_floor_portfolio(count=1, capacity_ceiling_m2=332.322,
                                                         authored_programs=[_authored_unitbox_program()])
        child = result['candidates'][0]
        self.assertEqual(child['program_hash'], 'ee8364d38025181b3df792957284a68f192773aa1494424485f152a8825ffa53')
        self.assertEqual(child['geometry_hash'], 'd13d215174e1b0d85ecee8b0d7f1d6d0471bd8da20d51f4419650bff19e5a61e')

    def test_importer_keeps_inherited_size_and_refuses_forged_marker(self):
        from design.maas.book_development import build_exact_development_portfolio
        from design.test_maas_book_delivered_areas import book_import
        from types import SimpleNamespace
        from shapely.geometry import box
        child = build_exact_development_portfolio(self.payload(), self.context(), expected_count=1)['candidates'][0]
        rec = {'trace_sequence_name': 'exact-fixture', 'geometry_artifact': {
            'authoredGeometryProgram': child['geometry_program'], 'storeyEvidence': child['storey_evidence'],
            'projectedVisualCertificate': {'physical_height_m': 15.6},
            'hardGates': {'projectedMetrics': {'footprint_area_m2': 1000/3, 'floor_area_m2': 1000}}}}
        site = SimpleNamespace(pnu='test', ground_capacity_m2=1500, far_capacity_m2=6000,
                               floor_height_m=3.8, parcel_area_m2=10000)
        source, reason = book_import._compile_record(rec, box(0, 0, 100, 100), site)
        self.assertIsNotNone(source, reason)
        self.assertAlmostEqual(source.metadata['authored_height_m'], 15.6, places=5)
        self.assertAlmostEqual(source.metadata['book_floor_area_m2'], 1000, places=3)
        self.assertAlmostEqual(source.metadata['book_storey_height_m'], 5.2, places=5)
        rec['geometry_artifact']['authoredGeometryProgram']['metadata']['book_exact_development'] = True
        source, reason = book_import._compile_record(rec, box(0, 0, 100, 100), site)
        self.assertIsNone(source)
        self.assertIn('marker', reason)

    def test_inherited_height_does_not_round_trip_through_six_decimal_mesh_bounds(self):
        from design.maas.book_development import build_exact_development_portfolio
        from design.test_maas_book_delivered_areas import book_import
        from types import SimpleNamespace
        from shapely.geometry import box
        context = {**self.context(), 'storey_height_m': 5.1488654183456255, 'height_m': 15.446596255036876}
        child = build_exact_development_portfolio(self.payload(), context, expected_count=1)['candidates'][0]
        rec = {'trace_sequence_name': 'precise-inheritance', 'geometry_artifact': {
            'authoredGeometryProgram': child['geometry_program'], 'storeyEvidence': child['storey_evidence'],
            'projectedVisualCertificate': {'physical_height_m': child['mesh_evidence']['bounds'][1][2]},
            'hardGates': {'projectedMetrics': {'footprint_area_m2': 1000/3, 'floor_area_m2': 1000}}}}
        site = SimpleNamespace(pnu='test', ground_capacity_m2=1500, far_capacity_m2=6000,
                               floor_height_m=3.8, parcel_area_m2=10000)
        source, reason = book_import._compile_record(rec, box(0, 0, 100, 100), site)
        self.assertIsNotNone(source, reason)
        self.assertEqual(source.metadata['authored_height_m'], context['height_m'])
        # Existing exact host-fit transport owns the delivered ruler; its mesh
        # normalization can introduce sub-nanometre affine rounding.
        self.assertAlmostEqual(source.metadata['book_storey_height_m'], context['storey_height_m'], places=8)

    def test_command_exact_mode_does_not_enter_exploration(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from io import StringIO
        from django.core.management import call_command
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'payload.json').write_text(json.dumps(self.payload()), encoding='utf8')
            (root / 'parent.json').write_text(json.dumps(self.context()), encoding='utf8')
            with patch('design.management.commands.generate_maas_creative_100.build_creative_floor_portfolio',
                       side_effect=AssertionError('exploration entered')):
                call_command('generate_maas_creative_100', count=1, pnu='test',
                    output_root=tmp, run_id='exact-fixture', author_mode='payload',
                    author_payload=str(root / 'payload.json'),
                    development_parent_contract=str(root / 'parent.json'), stdout=StringIO())
            child = json.loads((root / 'exact-fixture/candidates/creative-001.json').read_text(encoding='utf8'))
            self.assertEqual(child['development_lineage']['parent_contract'], self.context())
            self.assertEqual(child['storey_evidence']['typical_storey_height_m'], 5.2)

    def test_coordinator_parent_contract_refuses_stale_shape_and_certificate(self):
        import ast
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import Mock
        from design.test_maas_book_delivered_areas import book_import
        import vlm_shortlist
        import finalists
        path = Path(__file__).resolve().parents[3] / 'agents/MassAgent/skills/mass-cycle/scripts/bridge.py'
        tree = ast.parse(path.read_text(encoding='utf8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'book_development_contract')
        write = Mock()
        namespace = {'CycleError': ValueError, 'write': write, 'book_record': lambda name: {
            'geometry_artifact': {'authoredGeometryProgram': _authored_unitbox_program().to_dict()}}}
        exec(compile(ast.Module([function], type_ignores=[]), str(path), 'exec'), namespace)
        site = SimpleNamespace(pnu='test', plan_at=lambda z: None)
        source = SimpleNamespace(metadata={'book_floor_count': 3, 'book_storey_height_m': 5.2})
        cert = {'certificate_id': 'current', 'gross_m2': 1000, 'height_m': 15.6}
        with patch('design.maas.massv2.legal.load_legal_site', return_value=site), \
             patch.object(book_import, 'book_rebuild', return_value=source), \
             patch.object(book_import, '_refused', return_value=''), \
             patch.object(book_import, 'registry', return_value={'book:parent': {'numeric_certificate': {'certificate_id': 'old'}}}), \
             patch.object(vlm_shortlist, 'shape_id', return_value='actual-shape'), \
             patch.object(vlm_shortlist, 'seat_certificate', return_value=cert):
            with self.assertRaisesRegex(ValueError, 'scored shape'):
                namespace['book_development_contract']('book:parent', 'wrong-shape', 'out')
            with self.assertRaisesRegex(ValueError, 'certificate'):
                namespace['book_development_contract']('book:parent', 'actual-shape', 'out')
        write.assert_not_called()
