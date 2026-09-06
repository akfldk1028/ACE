"""Study selection must carry the registered parcel frame through every gate."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box
from design.maas.massv2.legal import LegalSite
from design.maas.massv2.parcel_policy import registered_buildable
from design.test_maas_parcel_frontages import PNU, RING
from design.test_maas_book_delivered_areas import record

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import book_import
import study_sheet
import vlm_shortlist


class RegisteredBookStudyTests(SimpleTestCase):
    def setUp(self):
        self.site = LegalSite(PNU, Polygon(RING), (0, 0),
            SimpleNamespace(envelope=SimpleNamespace(floor_height=3.8)),
            {'bcr_footprint_capacity_m2':1497.877, 'statutory_far_capacity_m2':6241.962})
        self.buildable = registered_buildable(self.site)
        self.name = 'book:registered-fixture'
        self.source, entry = book_import._compile_record(record(), self.buildable, self.site)
        self.assertIsNotNone(self.source, entry)
        self.registry = {self.name:entry}

    def run_study(self, root, row):
        caption = vlm_shortlist.certified_caption(self.source, self.site, '',
            gross_m2=self.registry[self.name]['floor_area_m2'])
        with patch.object(study_sheet, 'ROOT', root), \
             patch.object(study_sheet, 'seat_context', return_value=(
                 {}, self.site, self.buildable, (1,0), 15.2)), \
             patch.object(study_sheet, '_candidate_rows', return_value=[row]), \
             patch.object(study_sheet, 'rebuild_seat', return_value=(self.source, caption)):
            return study_sheet.main('registered-fixture')

    def test_top_book_remains_in_study_with_full_registered_frame_and_exact_certificate(self):
        with patch.object(book_import, 'registry', return_value=self.registry):
            cert = vlm_shortlist.seat_certificate(self.name, self.source, {}, self.site)
            self.assertTrue(cert['area_limits']['building_line']['satisfied'])
            row = {'name':self.name, 'score':4.45, 'shape_id':cert['shape_id'],
                   'certificate_id':cert['certificate_id']}
            with TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.assertEqual(self.run_study(root, row), 0)
                out = root/'runs/study-registered-fixture'
                result = json.loads((out/'study.json').read_text(encoding='utf8'))
                self.assertEqual(result['rejected'], [])
                selected = result['alternatives'][0]
                self.assertEqual(selected['name'], self.name)
                self.assertEqual(selected['certificate_id'], cert['certificate_id'])
                self.assertEqual(selected['shape_id'], cert['shape_id'])
                self.assertEqual(selected['delivered_floor_evidence'], cert['delivered_floor_evidence'])
                self.assertTrue(selected['area_limits']['building_line']['satisfied'])
                page = (out/'study.html').read_text(encoding='utf8')
                self.assertIn(self.name, page)
                self.assertIn('4.45/5', page)
                self.assertIn('BOOK', page)
                self.assertIn('마당과 주차 공간', page)
                self.assertEqual(selected['site_parking']['certificate_id'], cert['certificate_id'])
                self.assertFalse(selected['site_parking']['legal_approval'])
                self.assertTrue((out / selected['parking_plan']).exists())

    def test_stale_shape_or_certificate_still_prevents_book_selection(self):
        with patch.object(book_import, 'registry', return_value=self.registry):
            cert = vlm_shortlist.seat_certificate(self.name, self.source, {}, self.site)
            for field in ('shape_id', 'certificate_id'):
                row = {'name':self.name, 'score':4.45, 'shape_id':cert['shape_id'],
                       'certificate_id':cert['certificate_id'], field:'stale'}
                with self.subTest(field=field), TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self.assertEqual(self.run_study(root, row), 1)
                    result = json.loads((root/'runs/study-registered-fixture/study.json').read_text(encoding='utf8'))
                    self.assertEqual(result['alternatives'], [])
                    self.assertEqual(len(result['rejected']), 1)

    def test_authored_study_keeps_real_site_and_own_storey_in_shared_gate(self):
        from design.maas.source_geometry.ir import SourceMass, SourceVolume
        from design.maas.massv2.delivery_gate import assess_delivery
        plan = box(35, 25, 45, 35)
        self.name = 'authored_registered_fixture'
        self.source = SourceMass(self.name, plan,
            volumes=(SourceVolume('room', plan, 0, 1, 'authored'),),
            metadata={'authored_height_m':10.8, 'authored_floor_height_m':3.6})
        cert = vlm_shortlist.seat_certificate(self.name, self.source, {}, self.site)
        self.registry[self.name] = {'floor_area_m2':cert['gross_m2']}
        row = {'name':self.name, 'score':4.1, 'shape_id':cert['shape_id'],
               'certificate_id':cert['certificate_id']}
        with TemporaryDirectory() as tmp, \
             patch.object(study_sheet, 'assess_delivery', wraps=assess_delivery) as gate:
            self.assertEqual(self.run_study(Path(tmp), row), 0)
            self.assertIs(gate.call_args.args[1], self.site)
            self.assertEqual(gate.call_args.kwargs['storey_m'], 3.6)
