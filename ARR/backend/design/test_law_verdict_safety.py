"""Regression cases for the 2026-09 LawAgent audit, using offline sources."""
from copy import deepcopy
from django.test import SimpleTestCase

from design.maas.agents.shared.types import ExecutionIdentity
from design.maas.agents.law_graph_agent.evidence import (
    bind_law_agent_evidence, collect_law_source_snapshot,
    canonical_agent_evidence_hash, validate_persisted_law_agent_evidence,
)


class LawVerdictSafetyTests(SimpleTestCase):
    def setUp(self):
        self.identity = ExecutionIdentity('audit', 'program', 'geometry', 'floor', '1168010100106770000')
        self.snapshot = collect_law_source_snapshot(
            {'building_type': 'office'},
            graph_loader=lambda: {'graph_status': {'attempted': True, 'available': True},
                                  'articles': [{'id': 'article:84'}]},
            searcher=lambda query, limit: {'attempted': True, 'available': True,
                                         'results': [{'hang_id': 'hang:84'}]},
        )

    def bind(self, law, snapshot=None):
        return bind_law_agent_evidence(self.identity, {'law': law, 'building_type': 'office'},
                                      self.snapshot if snapshot is None else snapshot)

    def test_partial_or_nonboolean_success_never_passes(self):
        for law in [{}, {'evaluated': True}, {'hard_pass': True},
                    {'evaluated': False, 'hard_pass': True}, {'status': 'passed'},
                    {'evaluated': True, 'hard_pass': 1},
                    *[{'evaluated': True, 'hard_pass': True, 'status': value} for value in [False, 0, [], {}]],
                    {'evaluated': True, 'hard_pass': True, 'status': 'unknown'}]:
            with self.subTest(law=law):
                self.assertEqual(self.bind(law).status, 'needs_evidence')

    def test_explicit_failure_wins_even_with_conflicting_success(self):
        for law in [{'hard_pass': False}, {'status': 'fail'}, {'status': 'FAIL'},
                    {'evaluated': True, 'hard_pass': True, 'status': 'failed'},
                    {'evaluated': True, 'hard_pass': False, 'status': 'pass'}]:
            with self.subTest(law=law):
                self.assertEqual(self.bind(law).status, 'failed')

    def test_complete_success_agrees_with_persisted_validator(self):
        for status in [None, 'pass', 'passed', 'PASS']:
            law = {'evaluated': True, 'hard_pass': True}
            if status:
                law['status'] = status
            evidence = self.bind(law)
            self.assertEqual(evidence.status, 'passed')
            self.assertEqual(validate_persisted_law_agent_evidence(
                evidence.to_dict(), canonical_agent_evidence_hash(evidence),
                expected_identity=self.identity), ())

    def test_source_snapshot_tampering_blocks_binding(self):
        snapshot = deepcopy(self.snapshot)
        snapshot['articles'][0]['id'] = 'changed:article'
        result = self.bind({'evaluated': True, 'hard_pass': True}, snapshot)
        self.assertEqual(result.status, 'needs_evidence')
        self.assertIn('source_snapshot_hash_mismatch', result.evidence['missing_evidence'])

    def test_snapshot_program_mismatch_blocks_binding(self):
        evidence = bind_law_agent_evidence(self.identity,
            {'building_type': 'housing', 'law': {'evaluated': True, 'hard_pass': True}}, self.snapshot)
        self.assertEqual(evidence.status, 'needs_evidence')
        self.assertIn('source_program_mismatch', evidence.evidence['missing_evidence'])

    def test_passed_numeric_scope_is_not_a_whole_permit_certificate(self):
        result = self.bind({'evaluated': True, 'hard_pass': True})
        self.assertEqual(result.evidence.get('assessment_scope'), 'supplied_numeric_preflight')
        self.assertIs(result.evidence.get('permit_compliance_verified'), False)

    def test_every_unresolved_identity_field_blocks_live_binding(self):
        for key in ['program_hash', 'geometry_hash', 'execution_id', 'pnu']:
            values = self.identity.to_dict()
            values[key] = key.upper() + '_UNRESOLVED'
            with self.subTest(key=key):
                result = bind_law_agent_evidence(ExecutionIdentity(**values),
                    {'law': {'evaluated': True, 'hard_pass': True}, 'building_type': 'office'}, self.snapshot)
                self.assertEqual(result.status, 'needs_evidence')

    def test_unattempted_source_cannot_claim_available(self):
        snapshot = collect_law_source_snapshot({'building_type': 'office'},
            graph_loader=lambda: {'graph_status': {'attempted': False, 'available': True},
                                  'articles': [{'id': 'article'}]},
            searcher=lambda query, limit: {'attempted': True, 'available': True,
                                         'results': [{'hang_id': 'hang'}]})
        self.assertEqual(self.bind({'evaluated': True, 'hard_pass': True}, snapshot).status, 'needs_evidence')
