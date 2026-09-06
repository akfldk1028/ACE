from dataclasses import replace
from types import SimpleNamespace
from unittest import TestCase

from design.maas.geometry_language.ast import GeometryNode as Node, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.llm_adapter import (
    AUTHOR_GEOMETRY_GATE_POLICY, _program_language_contract_issue,
)
from design.maas.geometry_language.gate import compilation_gate


def assembly(floating=False):
    nodes = [Node('unit', 'primitive', 'box', parameters={'width': 1, 'depth': 1, 'height': 1})]
    previous = None
    for index in range(4):
        rotated, placed = f'rotate{index}', f'place{index}'
        nodes.extend([
            Node(rotated, 'transform', 'rotate', ('unit',), {'axis': 'z', 'angle_degrees': index * 12}),
            Node(placed, 'transform', 'translate', (rotated,), {'vector': [0, 0, index * 0.8 + (2 if floating and index == 3 else 0)]}),
        ])
        if previous is None:
            previous = placed
        else:
            joined = f'join{index}'
            nodes.append(Node(joined, 'boolean', 'union', (previous, placed)))
            previous = joined
    return GeometryProgram(tuple(nodes), previous)


class AuthorAssemblyBudgetTests(TestCase):
    context = {'geometry_language_contract': {}, 'author_maximum_body_rule_count': 3}

    def test_joined_rotated_parts_are_one_principle(self):
        program = assembly()
        self.assertEqual(_program_language_contract_issue(program, {
            **self.context, 'author_maximum_body_rule_count': 1,
        }), '')
        compiled = compile_geometry_program(program)
        self.assertEqual(compiled.status, 'compiled')
        self.assertFalse(compilation_gate(compiled, AUTHOR_GEOMETRY_GATE_POLICY))

    def test_floating_piece_still_fails_geometry_gate(self):
        program = assembly(floating=True)
        self.assertEqual(_program_language_contract_issue(program, self.context), '')
        self.assertTrue(compilation_gate(compile_geometry_program(program), AUTHOR_GEOMETRY_GATE_POLICY))

    def test_repeated_deformation_is_not_assembly_placement(self):
        program = assembly()
        nodes = program.nodes + (
            Node('taper1', 'modifier', 'taper', (program.root_id,), {'factor': 0.8}),
            Node('taper2', 'modifier', 'taper', ('taper1',), {'factor': 0.9}),
        )
        result = _program_language_contract_issue(GeometryProgram(nodes, 'taper2'), self.context)
        self.assertIn('body_rule_family_repeated=deformation', result)

    def test_operand_modifiers_remain_counted(self):
        nodes = (
            Node('unit', 'primitive', 'box'),
            Node('taper1', 'modifier', 'taper', ('unit',)),
            Node('taper2', 'modifier', 'taper', ('unit',)),
            Node('place1', 'transform', 'translate', ('taper1',)),
            Node('place2', 'transform', 'translate', ('taper2',)),
            Node('join', 'boolean', 'union', ('place1', 'place2')),
        )
        self.assertIn('body_rule_family_repeated=deformation', _program_language_contract_issue(GeometryProgram(nodes, 'join'), self.context))

    def test_whole_assembly_modifiers_still_exceed_budget(self):
        program = assembly()
        nodes = program.nodes + (
            Node('taper', 'modifier', 'taper', (program.root_id,)),
            Node('notch', 'macro', 'notch', ('taper',)),
            Node('rotate', 'transform', 'rotate', ('notch',)),
        )
        self.assertIn('body_rule_budget=4:maximum=3', _program_language_contract_issue(GeometryProgram(nodes, 'rotate'), self.context))

    def test_difference_cutters_and_semantic_labels_do_not_exempt_transforms(self):
        nodes = (
            Node('unit', 'primitive', 'box'),
            Node('rotate', 'transform', 'rotate', ('unit',), semantic_role='assembly_placement'),
            Node('move', 'transform', 'translate', ('rotate',), semantic_role='assembly_placement'),
            Node('cut', 'boolean', 'difference', ('unit', 'move')),
        )
        self.assertIn('body_rule_family_repeated=transform', _program_language_contract_issue(GeometryProgram(nodes, 'cut'), self.context))

    def test_reused_placement_on_cutting_branch_is_not_exempt(self):
        program = assembly()
        nodes = program.nodes + (Node('cut', 'boolean', 'difference', (program.root_id, 'place1')),)
        result = _program_language_contract_issue(GeometryProgram(nodes, 'cut'), self.context)
        self.assertTrue(result)

    def test_duplicate_join_inputs_do_not_create_assembly_exception(self):
        nodes = (
            Node('unit', 'primitive', 'box'),
            Node('rotate', 'transform', 'rotate', ('unit',)),
            Node('move', 'transform', 'translate', ('rotate',)),
            Node('join', 'boolean', 'union', ('move', 'move')),
        )
        self.assertTrue(_program_language_contract_issue(GeometryProgram(nodes, 'join'), self.context))

    def test_unconfigured_book_context_remains_unchanged(self):
        self.assertEqual(_program_language_contract_issue(assembly(), {'creative_portfolio_run_id': 'book-test'}), '')

    def test_downstream_articulation_uses_same_constructive_graph(self):
        from design.maas.book_language.candidate_analysis import _architectural_articulation_metrics
        program = assembly()
        program = replace(program, nodes=tuple(
            replace(node, provenance={'source': 'openai_llm_geometry_author'})
            for node in program.nodes
        ))
        metrics = _architectural_articulation_metrics(SimpleNamespace(metadata={'geometry_program': program.to_dict()}))
        self.assertEqual(metrics['program_rule_count'], 1)
        self.assertNotIn('program_body_rule_family_repeated', metrics['budget_failures'])

    def test_payload_portfolio_retains_original_and_book_exploration(self):
        from design.maas.creative_program_author import authored_programs_from_payload
        from design.maas.creative_floor_portfolio import build_creative_floor_portfolio_report
        raw = assembly()
        authored = authored_programs_from_payload({'geometry_programs': [raw.to_dict()]}, expected_count=1)
        self.assertTrue(any(node.operator == 'matrix4' for node in authored[0].program.nodes))
        report = build_creative_floor_portfolio_report(target_count=1, capacity_ceiling_m2=400, authored_programs=authored)
        self.assertEqual({row['candidate_origin'] for row in report.candidates}, {'authored_original', 'book_exploration'})
        self.assertEqual(report.rejections, ())
        original = next(row for row in report.candidates if row['candidate_origin'] == 'authored_original')
        self.assertEqual(original['authored_geometry_program'], authored[0].program.to_dict())
