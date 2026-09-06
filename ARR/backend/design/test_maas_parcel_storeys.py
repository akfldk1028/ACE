"""Public-1's five-storey limit is not a universal fifteen-metre limit."""
import importlib.util
from types import SimpleNamespace
from django.test import SimpleTestCase
from shapely.geometry import Polygon
from design.test_maas_parcel_frontages import RING
from design.maas.massv2 import MatrixForm, place, compile_matrix_form
from design.maas.massv2.legal import LegalSite
from design.maas.massv2.legal_fit import fit_to_site
from design.maas.massv2.fill import fill_to_site

PNU = '4115011300106840001'


def site():
    return LegalSite(PNU, Polygon(RING), (0, 0),
                     SimpleNamespace(envelope=SimpleNamespace(floor_height=3)),
                     {'bcr_footprint_capacity_m2': 1499, 'statutory_far_capacity_m2': 6240})


def form(storeys=5, storey=3.6, declared=None):
    return MatrixForm(name='public-room', primary_language='solid_body',
                      placements=(place('room', size=(10, 10, storeys * storey), at=(30,25,0)),),
                      floor_height_m=storey,
                      extra={'declared_storeys': declared if declared is not None else storeys,
                             'stature_is_building': True})


class PublicOneStoreysTests(SimpleTestCase):
    def policy(self):
        self.assertIsNotNone(importlib.util.find_spec('design.maas.massv2.parcel_policy'))
        from design.maas.massv2 import parcel_policy
        return parcel_policy

    def test_five_storeys_at_3_6m_is_eighteen_metres_not_illegal_fifteen(self):
        policy = self.policy()
        evidence = policy.storey_limit_evidence(compile_matrix_form(form()), site(), storey_m=3.6)
        self.assertTrue(evidence['satisfied'])
        self.assertEqual(evidence['conceptual_storey_proxy'], 5)
        self.assertEqual(site().max_storeys, 5)
        self.assertIsNone(site().statutory_max_height_m)
        self.assertIn('proxy', evidence['count_basis'])

    def test_six_storey_source_fails_even_with_spare_far(self):
        evidence = self.policy().storey_limit_evidence(compile_matrix_form(form(6)), site(), storey_m=3.6)
        self.assertFalse(evidence['satisfied'])

    def test_shrinking_declared_six_storeys_cannot_erase_the_declaration(self):
        evidence = self.policy().storey_limit_evidence(compile_matrix_form(form(5, declared=6)), site(), storey_m=3.6)
        self.assertFalse(evidence['satisfied'])
        self.assertEqual(evidence['declared_storeys'], 6)

    def test_book_six_floors_cannot_bypass_gate_with_shortened_height(self):
        evidence = self.policy().storey_limit_evidence(compile_matrix_form(form(4, declared=4)), site(),
                   storey_m=3.6, book_floor_count=6, source_kind='book')
        self.assertFalse(evidence['satisfied'])

    def test_book_missing_own_storey_evidence_is_not_certified(self):
        evidence = self.policy().storey_limit_evidence(compile_matrix_form(form(4)), site(),
                   storey_m=None, book_floor_count=None, source_kind='book')
        self.assertFalse(evidence['satisfied'])

    def test_policy_is_parcel_specific_and_does_not_convert_count_to_metres(self):
        policy = self.policy()
        self.assertIsNone(policy.policy_for('unrelated'))
        self.assertEqual(policy.default_building_type(PNU), '업무시설')
        self.assertEqual(policy.default_building_type('unrelated'), '제1종근린생활시설')

    def test_fit_and_fill_respect_five_storeys_without_height_conversion(self):
        controlled = site()
        object.__setattr__(controlled, '_plan_at_cache', {})
        # Only replace the external envelope query; fit/fill and gate are real.
        from unittest.mock import patch
        with patch.object(LegalSite, 'plan_at', return_value=self.policy().registered_buildable(controlled)):
            fit = fit_to_site(form(6), controlled)
            self.assertFalse(fit.satisfied)
            five = fit_to_site(form(5), controlled)
            self.assertTrue(five.satisfied)
            self.assertEqual(five.evidence()['area_limits']['building_line']['evidence_grade'],
                             'official_plan_registered')
            grown = fill_to_site(form(5), controlled)
            source = compile_matrix_form(grown.fit.form)
            evidence = self.policy().storey_limit_evidence(source, controlled, storey_m=3.6)
            self.assertTrue(evidence['satisfied'])
            self.assertLessEqual(evidence['occupied_height_above_datum_m'], 18 + 1e-6)

    def test_book_uniform_half_scale_preserves_four_floors_and_scales_area_square(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
        import book_import
        self.assertTrue(hasattr(book_import, 'scaled_book_metrics'))
        scaled = book_import.scaled_book_metrics(400, 3, 4, .5)
        self.assertEqual(scaled['floor_area_m2'], 100)
        self.assertEqual(scaled['book_storey_height_m'], 1.5)
        self.assertEqual(scaled['book_floor_count'], 4)

    def test_book_100sqm_cannot_pass_a_75sqm_far_budget(self):
        controlled = site()
        controlled.floor_field['statutory_far_capacity_m2'] = 75
        source = compile_matrix_form(form(4, storey=1.5))
        # The common gate consumes a retained BOOK area after its independent
        # measurement contract. An earlier missing-certificate error is not
        # proof that the FAR ceiling itself was enforced.
        evidence = self.policy().area_limit_evidence(source, controlled, 100)
        self.assertFalse(evidence['satisfied'])
        self.assertEqual(evidence['reasons'], ['floor_area_exceeds_capacity'])

    def test_book_import_itself_refuses_six_and_missing_floor_specs(self):
        import sys
        from pathlib import Path
        from unittest.mock import patch
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
        import book_import
        source = compile_matrix_form(form(4))
        record = {'geometry_artifact': {
            'authoredGeometryProgram': {'fixture': True},
            'storeyEvidence': {'storey_count': 6, 'typical_storey_height_m': 3},
            'projectedVisualCertificate': {'physical_height_m': 18},
            'hardGates': {'projectedMetrics': {'footprint_area_m2': 100, 'floor_area_m2': 600}}}}
        with patch('design.maas.geometry_language.ast.GeometryProgram.from_dict'), patch(
                'design.maas.geometry_language.source_bridge.compile_geometry_program_to_source_mass',
                return_value=source):
            rebuilt, reason = book_import._compile_record(record, site().site_local_utm, site())
            self.assertIsNone(rebuilt)
            self.assertIn('book_floor_count_exceeds_limit', reason)
            record['geometry_artifact']['storeyEvidence'] = {}
            rebuilt, reason = book_import._compile_record(record, site().site_local_utm, site())
            self.assertIsNone(rebuilt)
            self.assertIn('missing_book_floor_count', reason)

    def test_certificate_hash_binds_declared_floor_count_and_official_evidence(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
        from vlm_shortlist import seat_certificate
        first = seat_certificate('five', compile_matrix_form(form(5, declared=5)), {}, site())
        second = seat_certificate('five', compile_matrix_form(form(5, declared=4)), {}, site())
        self.assertNotEqual(first['certificate_id'], second['certificate_id'])
        evidence = first['storey_limit']['policy_evidence']
        self.assertEqual(evidence['max_storeys'], 5)
        self.assertEqual(len(evidence['sources'][0]['sha256']), 64)
        self.assertFalse(evidence['datum_measured'])
