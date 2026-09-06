"""BOOK plans and sections come from its export solid, not floor-band proxies."""
import json
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase
from shapely.geometry import box
from design.maas.geometry_language.dsl import parse_geometry_dsl
from design.maas.geometry_language.source_bridge import compile_geometry_program_to_source_mass
from design.maas.source_geometry.ir import SourceVolume

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import presentation


def wedge():
    source = compile_geometry_program_to_source_mass(
        parse_geometry_dsl('result = wedge(10,10,2,10)'), box(95,195,115,215),
        target_plan_area=100, minimum_plan_area=100)
    return replace(source, metadata={**source.metadata, 'authored_height_m':10., 'datum_m':3.})


class BookPresentationMeshTests(SimpleTestCase):
    def test_vertical_section_keeps_continuous_slope_in_translated_coordinate_frame(self):
        source = wedge()
        section = presentation.section_geometry(source, y=205.)
        self.assertAlmostEqual(section.area, 60., places=5)
        self.assertEqual(tuple(round(v,5) for v in section.bounds), (100.,0.,110.,10.))
        # The middle top is six metres; a floor-band terrace cannot answer this.
        self.assertAlmostEqual(section.intersection(box(104.9999,-1,105.0001,11)).area/.0002, 6., places=3)

    def test_plan_uses_actual_slope_even_if_proxy_claims_a_full_box(self):
        source = wedge()
        source = replace(source, volumes=(SourceVolume('proxy', box(100,200,110,210),0,1,'book'),))
        self.assertAlmostEqual(presentation.plan_geometry(source, z=6.).area, 50., places=5)
        self.assertAlmostEqual(presentation.plan_geometry(source, z=2.).area, 100., places=5)

    def test_export_hole_remains_empty_in_plan_and_section(self):
        source = compile_geometry_program_to_source_mass(parse_geometry_dsl(
            'result = difference(box(10,10,10), translate(box(4,4,10), vector=[3,3,0]))'),
            box(-5,-5,15,15), target_plan_area=84, minimum_plan_area=84)
        source = replace(source, metadata={**source.metadata, 'authored_height_m':10.})
        plan = presentation.plan_geometry(source, z=5.)
        self.assertEqual(len(plan.interiors), 1)
        self.assertAlmostEqual(plan.area, 84., places=5)
        section = presentation.section_geometry(source, y=5.)
        self.assertAlmostEqual(section.area, 60., places=5)

    def test_missing_authoritative_mesh_refuses_instead_of_drawing_proxy(self):
        source = replace(wedge(), surfaces=())
        for operation in (lambda: presentation.plan_geometry(source,z=6.),
                          lambda: presentation.section_geometry(source,y=205.)):
            with self.assertRaises(ValueError):
                operation()

    def test_drawing_sidecar_identifies_mesh_basis_and_actual_cut_positions(self):
        source = wedge()
        with TemporaryDirectory() as tmp:
            path = presentation.drawing_evidence('book:wedge',source,box(100,200,110,210),
                                                 Path(tmp),storey_m=3.)
            data = json.loads(path.with_suffix('.json').read_text(encoding='utf8'))
            self.assertEqual(data['geometry_basis'], 'complete_export_surface_mesh')
            self.assertEqual(data['plan_cuts_m'], [4.2,7.2])
            self.assertEqual(data['section_y_m'],205.)
            self.assertFalse(data['proxy_volumes_used'])

    def test_anonymous_jury_panel_retains_actual_cuts_without_private_labels(self):
        from PIL import Image
        source = wedge()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p01.png'
            Image.new('RGB', (1260, 580), 'white').save(path)
            evidence = presentation.append_jury_drawings(path, [
                ('secret-parent', source, 3.), ('secret-child', source, 4.)], box(100,200,110,210))
            rows = evidence['drawings']
            self.assertEqual([r['plan_cuts_m'] for r in rows], [[4.2,7.2], [4.2,8.2]])
            for row in rows:
                self.assertTrue(row['anonymous_image'])
                self.assertNotIn('secret', row['image_footer'])
                self.assertNotIn(row['shape_id'], row['image_footer'])
                self.assertEqual(row['geometry_basis'], 'complete_export_surface_mesh')
            self.assertNotEqual(rows[0]['plan_areas_m2'][1], rows[1]['plan_areas_m2'][1])
            with Image.open(path) as image:
                self.assertEqual(image.size, (1260, 828))
