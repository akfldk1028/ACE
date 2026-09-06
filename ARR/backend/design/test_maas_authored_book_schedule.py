from collections import Counter
import unittest

from design.maas.creative_book_supply import creative_book_schedule, project_creative_book_program, creative_book_evidence
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program


class AuthoredBookScheduleTests(unittest.TestCase):
    def test_authored_twelve_interleave_all_kinds_and_ignore_input_order(self):
        schedule = creative_book_schedule(12, authored_source_ids=['gamma','alpha','beta'])
        self.assertEqual(schedule, creative_book_schedule(12, authored_source_ids=['beta','gamma','alpha']))
        self.assertEqual(Counter(a.principle_kind for a in schedule),
                         Counter(base_operative=4, combination=4, aggregation=4))
        self.assertEqual(len({a.principle_id for a in schedule}),12)
        self.assertNotEqual(schedule,creative_book_schedule(12, authored_source_ids=['delta','alpha','beta']))

    def test_authored_schedule_exhausts_entire_registry_before_repeating(self):
        schedule = creative_book_schedule(118, authored_source_ids=['stable-source'])
        legacy = creative_book_schedule(59)
        self.assertEqual({a.principle_id for a in schedule[:59]}, {a.principle_id for a in legacy})
        self.assertEqual(len({a.principle_id for a in schedule[:59]}),59)
        self.assertEqual([a.principle_id for a in schedule[:59]], [a.principle_id for a in schedule[59:]])
        self.assertEqual(Counter(a.principle_kind for a in schedule[:59]),Counter(base_operative=30,combination=20,aggregation=9))

    def test_default_fixture_prefix_is_unchanged(self):
        legacy = creative_book_schedule(59)
        self.assertEqual([a.principle_kind for a in legacy[:30]],['base_operative']*30)
        self.assertEqual(creative_book_schedule(12),legacy[:12])

    def test_schedule_change_does_not_rewrite_original_candidate(self):
        from unittest.mock import patch
        from design.maas.creative_floor_portfolio import build_creative_floor_portfolio_report
        from design.test_maas_dimensional_intent import source,intent
        arguments=dict(target_count=1,capacity_ceiling_m2=1000.,authored_programs=[source(intent())])
        changed=build_creative_floor_portfolio_report(**arguments)
        with patch('design.maas.creative_floor_portfolio.creative_book_schedule',
                   side_effect=lambda count,**_kwargs:creative_book_schedule(count)):
            prior=build_creative_floor_portfolio_report(**arguments)
        original=lambda report:next(c for c in report.candidates if c['candidate_origin']=='authored_original')
        self.assertEqual(original(changed),original(prior))

    def test_each_offered_kind_has_an_actual_projection_and_ast_witness(self):
        program=GeometryProgram(name='neutral',root_id='body',nodes=(GeometryNode('body','primitive','box',
            parameters={'width':3.4,'depth':2.6,'height':4.2}),))
        seen=set()
        for assignment in creative_book_schedule(12,authored_source_ids=['neutral']):
            projected=project_creative_book_program(program,assignment)
            compiled=compile_geometry_program(projected)
            evidence=creative_book_evidence(projected)
            if compiled.status=='compiled' and evidence.get('materialized'):
                self.assertTrue(evidence['projected_node_ids'])
                self.assertEqual(evidence['principle_id'],assignment.principle_id)
                seen.add(assignment.principle_kind)
            if len(seen)==3:break
        self.assertEqual(seen,{'base_operative','combination','aggregation'})

    def test_actual_command_persists_offered_schedule_separately_from_materialized_evidence(self):
        import json
        from io import StringIO
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from django.core.management import call_command
        from design.test_maas_dimensional_intent import source, intent
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            payload=root/'author.json'
            payload.write_text(json.dumps({'geometry_programs':[source(intent()).to_dict()]}),encoding='utf8')
            call_command('generate_maas_creative_100',count=1,pnu='test',output_root=str(root),
                         run_id='schedule-test',author_mode='payload',author_payload=str(payload),stdout=StringIO())
            emitted=json.loads((root/'schedule-test/maas-creative-portfolio.json').read_text(encoding='utf8'))
            schedule=emitted['book_schedule']
            self.assertEqual(schedule,emitted['book_language_coverage']['offered_schedule'])
            self.assertEqual(len(schedule['ordered_assignments']),1)
            self.assertEqual(len(schedule['key']),64)
            materialized=[]
            for entry in emitted['candidates']:
                candidate=json.loads((root/'schedule-test'/entry['candidate_json']).read_text(encoding='utf8'))
                if candidate['candidate_origin']=='book_exploration':
                    evidence=candidate['book_language_evidence']
                    self.assertTrue(evidence['materialized'])
                    self.assertTrue(evidence['projected_node_ids'])
                    materialized.append(evidence['principle_id'])
            self.assertEqual(materialized,[schedule['ordered_assignments'][0]['principle_id']])
