from django.test import SimpleTestCase
from design.services.constraint_bridge import regulations_to_constraints


class LawConstraintCoverageTests(SimpleTestCase):
    def test_missing_municipal_caps_cannot_become_unconstrained_mass(self):
        with self.assertRaisesRegex(ValueError, 'municipal'):
            regulations_to_constraints({'bcr_pct': None, 'far_pct': None,
                'height_limit_m': 20,
                'municipal_coverage': {'status': 'needs_evidence'}})

    def test_explicit_unresolved_binding_value_does_not_use_legacy_ceiling(self):
        constraints = regulations_to_constraints({'bcr_pct': None, 'bcr_limit': 80,
                                                 'far_pct': None, 'far_limit': 1300})
        self.assertFalse(any(item['name'] in {'bcr', 'far'} for item in constraints))

    def test_eligible_snapshot_still_needs_both_finite_caps(self):
        for caps in [{'bcr_pct': None, 'far_pct': 800}, {'bcr_pct': float('nan'), 'far_pct': 800}]:
            with self.subTest(caps=caps), self.assertRaisesRegex(ValueError, 'caps'):
                regulations_to_constraints({**caps, 'municipal_coverage': {'status': 'available_snapshot'}})

    def test_eligible_snapshot_retains_measured_numeric_constraints(self):
        constraints = regulations_to_constraints({'bcr_pct': 60, 'far_pct': 800,
                                                 'municipal_coverage': {'status': 'available_snapshot'}})
        self.assertEqual({item['name']: item['val'] for item in constraints}, {'bcr': 60, 'far': 800})
