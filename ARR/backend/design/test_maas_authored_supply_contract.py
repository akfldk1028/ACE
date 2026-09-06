from django.test import SimpleTestCase
from django.core.management.base import CommandError


class AuthoredSupplyContractTests(SimpleTestCase):
    def original(self):
        from design.maas.geometry_language.programs import GeometryProgramBuilder
        builder = GeometryProgramBuilder('parent')
        node = builder.add('primitive', 'box', parameters={'width': 1., 'depth': 1., 'height': 1.})
        program = builder.build(node)
        return dict(candidate_origin='authored_original', candidate_id='a',
                    program_hash='physical-parent', source_program_hash=program.program_hash(),
                    authored_geometry_program=program.to_dict())

    def validate(self, rows, *, count=1, hybrid=False):
        from design.management.commands.generate_maas_creative_100 import _validate_candidate_supply
        return _validate_candidate_supply(rows, count=count, hybrid=hybrid)

    def test_original_and_exploration_are_both_kept(self):
        original = self.original()
        rows = [original,
                dict(candidate_origin='book_exploration', candidate_id='b',
                     program_hash='child', source_program_hash=original['source_program_hash'],
                     parent_program_hash=original['source_program_hash'],
                     parent_geometry_program=original['authored_geometry_program'])]
        self.validate(rows)
        self.assertEqual(len(rows), 2)

    def test_exploration_parent_ast_must_match_recorded_hash(self):
        original = self.original()
        with self.assertRaises(CommandError):
            self.validate([dict(candidate_origin='book_exploration', candidate_id='b',
                                source_program_hash='wrong', parent_program_hash='wrong',
                                parent_geometry_program=original['authored_geometry_program'])])

    def test_original_does_not_satisfy_exploration_quota(self):
        with self.assertRaises(CommandError):
            self.validate([self.original()])

    def test_invalid_lineage_is_rejected(self):
        for origin in ('authored_original', 'book_exploration'):
            with self.subTest(origin=origin), self.assertRaises(CommandError):
                self.validate([dict(candidate_origin=origin, candidate_id='a',
                                    program_hash='changed', source_program_hash='original')])

    def test_legacy_exact_count_is_preserved(self):
        self.validate([dict(candidate_id='old')])
        with self.assertRaises(CommandError):
            self.validate([dict(candidate_id='a'), dict(candidate_id='b')])

    def test_partial_hybrid_does_not_get_fake_completion(self):
        self.validate([], hybrid=True)
        with self.assertRaises(CommandError):
            self.validate([])
