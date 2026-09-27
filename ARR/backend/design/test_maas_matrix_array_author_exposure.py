"""An implemented array must accept its actual matrices through the author schema."""
import json
from unittest import TestCase

import jsonschema
from design.maas.geometry_language.llm_adapter import (
    _author_node_schema, _program_from_structured_author_item,
)
from design.maas.geometry_language.compiler import compile_geometry_program


def parameter(name, kind, value):
    fields = dict(name=name, value_type=kind)
    fields[{'structured_json': 'structured_json', 'boolean': 'boolean_value',
            'number': 'numeric_value'}[kind]] = value
    return fields


class MatrixArrayAuthorExposureTests(TestCase):
    def item(self, connected=True, gap=.5):
        matrices = [[[1, 0, 0, x], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
                    for x in (0, gap)]
        array = dict(id='group', kind='pattern', operator='matrix_array', inputs=['body'],
                     semantic_role='dominant_mass', parameters=[
                         parameter('matrices', 'structured_json', json.dumps(matrices)),
                         parameter('require_connected', 'boolean', connected)])
        body = dict(id='body', kind='primitive', operator='box', inputs=[],
                    semantic_role='dominant_mass', parameters=[
                        parameter(k, 'number', 1) for k in ('width', 'depth', 'height')])
        return dict(name='explicit_array', nodes=[body, array], root_id='group')

    def test_author_schema_decodes_and_executes_actual_matrix_array(self):
        item = self.item()
        jsonschema.validate(item['nodes'][-1], _author_node_schema(['matrix_array']))
        program = _program_from_structured_author_item(item, index=0)
        result = compile_geometry_program(program)
        self.assertEqual(result.status, 'compiled')
        self.assertAlmostEqual(result.metrics['volume'], 1.5)

    def test_exposed_connectivity_option_still_enforces_existing_gate(self):
        item = self.item(gap=2)
        jsonschema.validate(item['nodes'][-1], _author_node_schema(['matrix_array']))
        result = compile_geometry_program(_program_from_structured_author_item(item, index=0))
        self.assertNotEqual(result.status, 'compiled')
        self.assertTrue(any('disconnected_matrix_array' in str(issue) for issue in result.issues))
