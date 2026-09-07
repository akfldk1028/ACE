"""A display title cannot erase distinct evaluated plan geometry."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from design.test_maas_study_registered_book import RegisteredBookStudyTests
from design.test_maas_book_delivered_areas import record
from design.maas.geometry_language.dsl import parse_geometry_dsl
import book_import
import study_sheet
import vlm_shortlist


class StudyGeometryDiversityTests(SimpleTestCase):
    setUp = RegisteredBookStudyTests.setUp

    def test_distinct_geometry_survives_shared_title_but_alias_does_not(self):
        other = record()
        other['geometry_artifact']['authoredGeometryProgram'] = parse_geometry_dsl(
            'result = union(box(24,12,3), translate(box(6,12,6), vector=[0,0,3]), '
            'translate(box(6,12,6), vector=[15,0,3]))').to_dict()
        source_b, entry_b = book_import._compile_record(other, self.buildable, self.site)
        self.assertIsNotNone(source_b, entry_b)
        name_b, alias = 'book:second-plan', 'book:renamed-first-plan'
        registry = {self.name: self.registry[self.name], name_b: entry_b,
                    alias: self.registry[self.name]}
        sources = {self.name: self.source, alias: self.source, name_b: source_b}
        for entry in registry.values():
            entry['design_argument_ko'] = {'title': 'Shared presentation label'}
        self.assertNotEqual(vlm_shortlist.shape_id(self.source), vlm_shortlist.shape_id(source_b))
        with patch.object(book_import, 'registry', return_value=registry):
            rows = []
            entries = {}
            for name, score in ((self.name, 4.5), (alias, 4.4), (name_b, 4.3)):
                cert = vlm_shortlist.seat_certificate(name, sources[name], {}, self.site)
                entries[name] = {**registry[name], 'delivered_shape_id': cert['shape_id'],
                                 'numeric_certificate': cert}
                rows.append({'name': name, 'score': score, 'round': 'vlm-book-fixture', 'shape_id': cert['shape_id'],
                             'certificate_id': cert['certificate_id']})
            def rebuild(name, *_args, **_kwargs):
                return sources[name], vlm_shortlist.certified_caption(
                    sources[name], self.site, '', gross_m2=registry[name]['floor_area_m2'])
            with TemporaryDirectory() as tmp, \
                 patch.object(book_import, 'BOOKS', Path(tmp)), \
                 patch.object(study_sheet, 'ROOT', Path(tmp)), \
                 patch.object(study_sheet, 'seat_context', return_value=(
                     {}, self.site, self.buildable, (1, 0), 15.2)), \
                 patch.object(study_sheet, '_candidate_rows', return_value=rows), \
                 patch.object(study_sheet, 'rebuild_seat', side_effect=rebuild):
                (Path(tmp) / 'book-fixture.json').write_text(json.dumps({
                    'book_dir': tmp, 'entries': entries}), encoding='utf8')
                self.assertEqual(study_sheet.main('geometry-diversity'), 0)
                result = json.loads((Path(tmp)/'runs/study-geometry-diversity/study.json').read_text(encoding='utf8'))
                self.assertEqual([r['name'] for r in result['alternatives']], [self.name, name_b])
