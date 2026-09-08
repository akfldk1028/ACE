"""A score, its caption and the last sequence frame must describe one mass."""
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from shapely.geometry import Polygon, box

TOOLS = Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'
sys.path.insert(0, str(TOOLS))
import study_sheet
import vlm_shortlist
from design.maas.source_geometry.ir import SourceMass, SourceVolume


def mass(plan=None, height=12):
    plan = box(0, 0, 10, 10) if plan is None else plan
    return SourceMass('fixture', plan, volumes=(SourceVolume('body', plan, 0, 1, 'seed'),),
                      metadata={'authored_height_m': height})


class DeliveryIntegrityTests(unittest.TestCase):
    def test_book_board_candidate_competes_with_authored_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runs/vlm-demo').mkdir(parents=True)
            (root / 'runs/board').mkdir()
            (root / 'runs/vlm-demo/vlm-shortlist.json').write_text(json.dumps([
                {'name': 'bar~wide', 'score': 3.8, 'pass': True, 'shape_id': 'a'}]))
            (root / 'runs/board/board-key.json').write_text(json.dumps([
                {'label': 'O1', 'name': 'book:court', 'score': 4.4, 'shape_id': 'b'},
                {'label': 'C1', 'name': 'canon', 'score': 5, 'shape_id': 'c'}]))
            with patch.object(study_sheet, 'ROOT', root):
                picks = study_sheet._picks('demo', {'bar': {}, 'canon': {}})
            self.assertEqual(picks, [('book:court', 4.4), ('bar~wide', 3.8)])

    def test_plan_hole_changes_shape_identity(self):
        whole = mass()
        court = mass(Polygon(box(0, 0, 10, 10).exterior.coords,
                             [box(3, 3, 7, 7).exterior.coords]))
        self.assertNotEqual(vlm_shortlist.shape_id(whole), vlm_shortlist.shape_id(court))

    def test_identical_plans_with_valley_and_mansard_keep_their_actual_sections(self):
        original = mass()
        volume = original.volumes[0]
        valley = replace(original, volumes=(replace(volume,
            top_drop=.5, top_profile=((0., 1.), (.5, .5), (1., 1.)), profile_across=(1., 0.)),))
        mansard = replace(original, volumes=(replace(volume,
            top_drop=.5, top_profile=((0., .5), (.2, 1.), (.8, 1.), (1., .5)), profile_across=(1., 0.)),))
        self.assertTrue(valley.volumes[0].footprint.equals(mansard.volumes[0].footprint))
        self.assertGreater(valley.plan_at(9.).symmetric_difference(mansard.plan_at(9.)).area, 0.)
        self.assertNotEqual(vlm_shortlist.shape_id(valley), vlm_shortlist.shape_id(mansard))
        self.assertEqual(vlm_shortlist.shape_id(valley),
                         vlm_shortlist.shape_id(replace(valley, name='another source caption')))

    def test_stale_or_unbound_sequence_is_never_attached(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runs/demo').mkdir(parents=True)
            Image.new('RGB', (80, 40)).save(root / 'runs/demo/parti-bar.png')
            tile = root / 'tile.png'
            Image.new('RGB', (80, 80)).save(tile)
            before = tile.read_bytes()
            with patch.object(vlm_shortlist, 'ROOT', root):
                vlm_shortlist._with_sequence(tile, 'demo', 'bar')
            self.assertEqual(tile.read_bytes(), before)

    def test_authored_certificate_uses_own_storey_and_exact_shape(self):
        self.assertTrue(hasattr(vlm_shortlist, 'seat_certificate'))
        source = mass(height=12)
        site = SimpleNamespace(floor_height_m=3, parcel_area_m2=1000)
        cert = vlm_shortlist.seat_certificate('bar~wide', source,
                                            {'bar': {'floor_height_m': 4}}, site)
        self.assertEqual(cert['gross_m2'], 300)
        self.assertEqual(cert['storey_m'], 4)
        self.assertEqual(cert['shape_id'], vlm_shortlist.shape_id(source))
        self.assertEqual(cert['name'], 'bar~wide')

    def test_changed_geometry_cannot_keep_score(self):
        self.assertTrue(hasattr(study_sheet, '_score_matches'))
        source = mass()
        self.assertTrue(study_sheet._score_matches({'shape_id': vlm_shortlist.shape_id(source)}, source))
        self.assertFalse(study_sheet._score_matches({'shape_id': 'stale'}, source))
        self.assertFalse(study_sheet._score_matches({}, source))

    def test_storey_change_invalidates_numeric_certificate_even_if_shape_matches(self):
        source = mass()
        site = SimpleNamespace(floor_height_m=3, parcel_area_m2=1000)
        three = vlm_shortlist.seat_certificate('x', source, {'x': {'floor_height_m': 3}}, site)
        four = vlm_shortlist.seat_certificate('x', source, {'x': {'floor_height_m': 4}}, site)
        self.assertEqual(three['shape_id'], four['shape_id'])
        self.assertNotEqual(three['certificate_id'], four['certificate_id'])

    def test_empty_recommendation_does_not_leave_old_html_published(self):
        site = SimpleNamespace(floor_height_m=3, parcel_area_m2=1000)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / 'runs/study-empty'
            out.mkdir(parents=True)
            (out / 'study.html').write_text('OLD RECOMMENDATION')
            with patch.object(study_sheet, 'ROOT', root), \
                 patch.object(study_sheet, 'seat_context', return_value=({}, site, None, None, 12)), \
                 patch.object(study_sheet, '_candidate_rows', return_value=[]):
                self.assertEqual(study_sheet.main('empty'), 1)
            self.assertNotIn('OLD RECOMMENDATION', (out / 'study.html').read_text(encoding='utf-8'))

    def test_sequence_final_frame_is_the_selected_variant_and_caption(self):
        from presentation import sequence_frames, artifact_stem
        source = mass(height=8)
        cert = {'name': 'book:example~small', 'shape_id': vlm_shortlist.shape_id(source),
                'coverage_pct': 10, 'far_pct': 20, 'storey_m': 4}
        frames = sequence_frames(cert['name'], source, book={}, site=None,
                                 buildable=None, axis=None, certificate=cert)
        self.assertIs(frames[-1]['source'], source)
        self.assertIn('20%', frames[-1]['numbers'])
        with self.assertRaisesRegex(ValueError, 'certificate'):
            sequence_frames('book:example~large', source, book={}, site=None,
                            buildable=None, axis=None, certificate=cert)
        self.assertNotEqual(artifact_stem('x~small', 'same-shape'), artifact_stem('x~large', 'same-shape'))

    def test_sequence_manifest_rejects_modified_png_and_wrong_variant(self):
        import hashlib
        from presentation import artifact_stem, bound_sequence
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / (artifact_stem('x~small', 'shape') + '.png')
            p.write_bytes(b'frame')
            p.with_suffix('.json').write_text(json.dumps({
                'name': 'x~small', 'shape_id': 'shape', 'final_shape_id': 'shape',
                'png_sha256': hashlib.sha256(b'frame').hexdigest()}))
            self.assertEqual(bound_sequence(tmp, 'x~small', 'shape'), p)
            self.assertIsNone(bound_sequence(tmp, 'x~large', 'shape'))
            p.write_bytes(b'other-frame')
            self.assertIsNone(bound_sequence(tmp, 'x~small', 'shape'))

    def test_section_preserves_courtyard_and_plate_underside(self):
        from presentation import section_geometry
        court = mass(Polygon(box(0, 0, 10, 10).exterior.coords,
                             [box(3, 3, 7, 7).exterior.coords]))
        self.assertAlmostEqual(section_geometry(court, y=5).area, 72)
        plate = replace(mass(height=10), volumes=(SourceVolume(
            'roof', box(0, 0, 10, 10), 0, 1, 'warp', top_drop=1,
            warp=((1, 0), (0, 1), (1, 1, 1, 1), True, 0, .1)),))
        section = section_geometry(plate, y=5)
        self.assertAlmostEqual(section.area, 10)
        self.assertEqual(section.bounds, (0, 9, 10, 10))

    def test_board_does_not_label_new_geometry_with_old_score(self):
        import board_render
        self.assertTrue(hasattr(board_render, 'tile_evidence'))
        source = mass()
        row = {'name': 'x', 'score': 4.8, 'shape_id': 'stale'}
        meta, evidence = board_render.tile_evidence(row, source, {'thesis': 'x'})
        self.assertNotIn('4.80', str(meta))
        self.assertTrue(evidence['requires_rejudge'])

    def test_book_jury_caption_has_no_author_narrative_and_measures_projection(self):
        self.assertTrue(hasattr(vlm_shortlist, 'jury_caption'))
        source = mass()
        site = SimpleNamespace(floor_height_m=3, parcel_area_m2=1000)
        caption = vlm_shortlist.jury_caption(source, site, gross_m2=500)
        self.assertEqual(caption['thesis'], '')
        self.assertEqual(caption['건폐율'], '10%')
        self.assertEqual(caption['용적률'], '50%')

    def test_changed_jury_png_cannot_be_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / 'runs/vlm-demo'
            out.mkdir(parents=True)
            (out / 'key.json').write_text(json.dumps([
                {'tile': 't01', 'name': 'bar', 'png_sha256': 'wrong'}]))
            (out / 't01.png').write_bytes(b'changed')
            verdict = root / 'jury.txt'
            verdict.write_text('TILE t01\nWEIGHTED 4.2\n')
            with patch.object(vlm_shortlist, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'image'):
                    vlm_shortlist.score('demo', [str(verdict)])

    def test_book_study_html_and_sequence_share_exact_source_certificate(self):
        import book_import
        from design.test_maas_book_delivered_areas import record
        name = 'book:fixture'
        site = SimpleNamespace(floor_height_m=3, parcel_area_m2=1000,
                               ground_capacity_m2=600, far_capacity_m2=2500,
                               shared_edges=())
        source, entry = book_import._compile_record(record(), box(-5, -5, 15, 15), site)
        self.assertIsNotNone(source, entry)
        registry = {name: {**entry, 'thesis': '실제 원본의 논지'}}
        with patch.object(book_import, 'registry', return_value=registry):
            cert = vlm_shortlist.seat_certificate(name, source, {}, site)
            row = {'name': name, 'score': 4.1, 'round': 'vlm-book-fixture', 'shape_id': cert['shape_id'],
                   'certificate_id': cert['certificate_id']}
            caption = vlm_shortlist.certified_caption(source, site, '', gross_m2=entry['floor_area_m2'])
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'book-fixture.json').write_text(json.dumps({
                    'book_dir': tmp, 'entries': {name: {**registry[name],
                        'delivered_shape_id': cert['shape_id'], 'numeric_certificate': cert}}}), encoding='utf8')
                with patch.object(study_sheet, 'ROOT', root), \
                     patch.object(book_import, 'BOOKS', root), \
                     patch.object(study_sheet, 'seat_context', return_value=({}, site, box(-5, -5, 15, 15), (1, 0), 12)), \
                     patch.object(study_sheet, '_candidate_rows', return_value=[row]), \
                     patch.object(study_sheet, 'rebuild_seat', return_value=(source, caption)):
                    result = study_sheet.main('fixture')
                self.assertEqual(result, 0)
                folder = root / 'runs/study-fixture'
                delivered = json.loads((folder / 'study.json').read_text(encoding='utf-8'))['alternatives'][0]
                sequence = json.loads((folder / delivered['sequence']).with_suffix('.json').read_text(encoding='utf-8'))
                self.assertEqual(delivered['certificate_id'], cert['certificate_id'])
                self.assertEqual(sequence['final_shape_id'], delivered['shape_id'])
                self.assertEqual(sequence['gross_m2'], delivered['gross_m2'])
                page = (folder / 'study.html').read_text(encoding='utf-8')
                self.assertIn(name, page)
                self.assertIn('실제 원본의 논지', page)
                self.assertNotIn('???', page)
                self.assertEqual(page.count('data:image/png;base64,'), 3)


if __name__ == '__main__':
    unittest.main()
