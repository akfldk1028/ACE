"""Actual author payloads must reach implemented sweep and face placement."""
import json
from unittest import TestCase

import jsonschema
from design.maas.geometry_language.llm_adapter import _author_node_schema, _program_from_structured_author_item
from design.maas.geometry_language.compiler import compile_geometry_program


def parameter(name, kind, value):
    field = {'number': 'numeric_value', 'string': 'string_value', 'vector': 'vector_value',
             'structured_json': 'structured_json'}[kind]
    return dict(name=name, value_type=kind, **{field: value})


def box(name):
    return dict(id=name, kind='primitive', operator='box', inputs=[], semantic_role='dominant_mass',
                parameters=[parameter(k, 'number', 1) for k in ('width', 'depth', 'height')])


def item(operator, parameters):
    nodes = [box('host')]
    inputs = ['host']
    if operator == 'attach':
        nodes.append(box('guest'))
        inputs.append('guest')
    nodes.append(dict(id='result', kind='composition' if operator == 'attach' else 'modifier',
                      operator=operator, inputs=inputs, semantic_role='dominant_mass', parameters=parameters))
    return dict(name='author_exposure', nodes=nodes, root_id='result')


class SweepAttachAuthorExposureTests(TestCase):
    def compile(self, payload):
        node = payload['nodes'][-1]
        jsonschema.validate(node, _author_node_schema([node['operator']]))
        program = _program_from_structured_author_item(payload, index=0)
        self.assertEqual(program.metadata['contract_lowered_parameter_type_corrections'], [])
        return compile_geometry_program(program)

    def test_required_sweep_path_reaches_compiler(self):
        result = self.compile(item('profile_sweep_3d', [
            parameter('path', 'structured_json', json.dumps([[0, 0, 0], [0, 0, 2]]))]))
        self.assertEqual(result.status, 'compiled', result.issues)
        self.assertAlmostEqual(result.metrics['volume'], 2)

    def test_face_parameters_change_real_attachment(self):
        volumes = []
        for face, expected_bounds in (
            ('east', [[0, 0, 0], [1.18, 1, 1]]),
            ('top', [[0, 0, 0], [1, 1, 1.18]]),
            ('bottom', [[0, 0, -.18], [1, 1, 1]]),
        ):
            result = self.compile(item('attach', [parameter('host_face', 'string', face),
                parameter('anchor', 'vector', [0, 0]),
                parameter('guest_extent', 'vector', [.2, .5, .5]),
                parameter('engagement', 'number', .1),
                parameter('rotation_degrees', 'number', 0)]))
            self.assertEqual(result.status, 'compiled', result.issues)
            self.assertEqual(result.metrics['component_count'], 1)
            self.assertTrue(result.metrics['watertight'])
            for actual, expected in zip(result.metrics['bounds'], expected_bounds):
                for coordinate, wanted in zip(actual, expected):
                    self.assertAlmostEqual(coordinate, wanted, places=5)
            volumes.append(result.metrics['volume'])
        for volume in volumes:
            self.assertAlmostEqual(volume, 1.045, places=5)

    def test_attachment_aliases_decode_with_actual_numeric_types(self):
        result = self.compile(item('attach', [parameter('host_face', 'string', 'north'),
            *[parameter(k, 'number', v) for k, v in dict(anchor_u=0, anchor_v=0,
                depth_ratio=.2, width_ratio=.5, height_ratio=.5, embed_ratio=.1).items()]]))
        self.assertEqual(result.status, 'compiled', result.issues)
        self.assertAlmostEqual(result.metrics['volume'], 1.045, places=5)

    def test_malformed_sweep_keeps_geometry_validation(self):
        for path in ([[0, 0, 0]], [[0, 0, 0], [0, 0, 0]], [[0, 0], [0, 1]]):
            result = self.compile(item('profile_sweep_3d', [parameter('path', 'structured_json', json.dumps(path))]))
            self.assertNotEqual(result.status, 'compiled')
            self.assertTrue(result.issues)

    def test_attachment_schema_rejects_bad_face_and_vector_shapes(self):
        for invalid in (parameter('host_face', 'string', 'roof'),
                        parameter('anchor', 'vector', [0, 0, 0]),
                        parameter('guest_extent', 'vector', [.2, .5]),
                        parameter('engagement', 'string', 'deep')):
            payload = item('attach', [invalid])
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(payload['nodes'][-1], _author_node_schema(['attach']))
