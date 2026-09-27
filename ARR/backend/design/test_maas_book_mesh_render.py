"""Mesh-authoritative BOOK views must not substitute occupied-band proxies."""
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest import TestCase

from PIL import Image
from shapely.geometry import box
from design.maas.geometry_language.dsl import parse_geometry_dsl
from design.maas.geometry_language.source_bridge import compile_geometry_program_to_source_mass
from design.maas.massv2.render import render_masses, render_sequence
from design.maas.massv2.render_mesh import physical_triangles, actual_xy_projection, mesh_plan_at, mesh_section_at


def mesh_source():
    program = parse_geometry_dsl('result = difference(box(10,8,8), '
                                 'translate(box(4,3,10), vector=[3,2.5,-1]))')
    source = compile_geometry_program_to_source_mass(program, box(0, 0, 20, 20))
    return replace(source, metadata={**source.metadata, 'authored_height_m': 12})


class BookMeshRenderTests(TestCase):
    def test_lower_view_preserves_geometry_and_restores_default_pixels(self):
        source = mesh_source()
        before = physical_triangles(source)
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / f'view-{i}.png' for i in range(3)]
            for path, options in zip(paths, ({}, {'pitch_degrees': 8, 'yaw_degrees': 50}, {})):
                render_masses([('same', source, {})], path, columns=1,
                              tile=(450, 430), style='massing', **options)
            pixels = [Image.open(path).tobytes() for path in paths]
            self.assertNotEqual(pixels[0], pixels[1])
            self.assertEqual(pixels[0], pixels[2])
        self.assertEqual(before, physical_triangles(source))

    def test_camera_restores_after_a_failed_render(self):
        from design.maas.massv2 import render
        original = render._YAW, render._PITCH
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'nothing to render'):
                render_masses([], Path(folder) / 'empty.png', pitch_degrees=8, yaw_degrees=50)
        self.assertEqual(original, (render._YAW, render._PITCH))

    def test_world_coordinates_use_centroid_and_height_without_adding_datum(self):
        source = mesh_source()
        source = replace(source, metadata={**source.metadata, 'datum_m': 2})
        for original, actual in zip(source.surfaces, physical_triangles(source)):
            for local, world in zip(original.vertices_m, actual):
                self.assertEqual(world, (local[0]+source.footprint.centroid.x,
                                         local[1]+source.footprint.centroid.y, local[2]*12))
        self.assertAlmostEqual(min(p[2] for t in physical_triangles(source) for p in t), 0)

    def test_actual_plan_and_vertical_section_preserve_the_courtyard_hole(self):
        source = mesh_source()
        plan = mesh_plan_at(source, 6)
        self.assertEqual(len(plan.interiors), 1)
        self.assertAlmostEqual(plan.area, actual_xy_projection(source).area, places=5)
        section = mesh_section_at(source, axis='y', coordinate=plan.centroid.y)
        self.assertEqual(section.geom_type, 'MultiPolygon')
        self.assertEqual(len(section.geoms), 2)
        self.assertTrue(mesh_plan_at(source, 13).is_empty)

    def test_tile_uses_actual_triangles_even_when_band_proxy_changes(self):
        source = mesh_source()
        wrong_proxy = replace(source, volumes=(replace(source.volumes[0], footprint=box(0, 0, 1, 1)),))
        with tempfile.TemporaryDirectory() as folder:
            files = [Path(folder)/f'{i}.png' for i in range(2)]
            for path, candidate in zip(files, (source, wrong_proxy)):
                render_masses([('same', candidate, {})], path, columns=1, tile=(900, 820), style='massing')
            self.assertEqual(Image.open(files[0]).tobytes(), Image.open(files[1]).tobytes())

    def test_sequence_uses_actual_triangles_even_when_band_proxy_changes(self):
        source = mesh_source()
        wrong_proxy = replace(source, volumes=())
        with tempfile.TemporaryDirectory() as folder:
            files = [Path(folder)/f'{i}.png' for i in range(2)]
            for path, candidate in zip(files, (source, wrong_proxy)):
                render_sequence([{'source': candidate, 'verb': 'same'}], path,
                                site_ring=list(box(0, 0, 20, 20).exterior.coords))
            self.assertEqual(Image.open(files[0]).tobytes(), Image.open(files[1]).tobytes())

    def test_incomplete_authoritative_mesh_refuses_instead_of_proxy_fallback(self):
        source = mesh_source()
        broken = replace(source, surfaces=source.surfaces[:-1])
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'mesh|surface'):
                render_masses([('broken', broken, {})], Path(folder)/'bad.png', columns=1)

    def test_depth_raster_is_independent_of_triangle_order(self):
        source = mesh_source()
        reversed_source = replace(source, surfaces=tuple(reversed(source.surfaces)))
        with tempfile.TemporaryDirectory() as folder:
            files = [Path(folder)/f'{i}.png' for i in range(2)]
            for path, candidate in zip(files, (source, reversed_source)):
                render_masses([('same', candidate, {})], path, columns=1, tile=(450, 430), style='massing')
            self.assertEqual(Image.open(files[0]).tobytes(), Image.open(files[1]).tobytes())

    def test_raster_silhouette_matches_full_projected_mesh(self):
        import numpy as np
        from shapely import contains_xy
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        from design.maas.massv2 import render
        from design.maas.massv2.render_mesh import paint_mesh
        triangles = physical_triangles(mesh_source())
        projected = [render._project(*p) for triangle in triangles for p in triangle]
        xmin, ymin = min(p[0] for p in projected), min(p[1] for p in projected)
        def screen(p):
            return 8+(p[0]-xmin)*5, 8+(p[1]-ymin)*5
        panel = Image.new('RGB', (220, 220), (255, 0, 255))
        paint_mesh(panel, triangles, project=render._project, to_screen=screen,
                   yaw=render._YAW, pitch=render._PITCH, palette=render._MASSING,
                   smooth_turn_cos=render._SMOOTH_TURN_COS)
        silhouette = unary_union([Polygon([screen(render._project(*p)) for p in triangle])
                                  for triangle in triangles])
        xx, yy = np.meshgrid(np.arange(220)+.5, np.arange(220)+.5)
        expected = contains_xy(silhouette, xx, yy)
        drawn = np.any(np.array(panel) != (255, 0, 255), axis=2)
        self.assertTrue(np.array_equal(drawn, expected))
