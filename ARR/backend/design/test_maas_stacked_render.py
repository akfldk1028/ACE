"""A discrete solid stack must not be replaced by an inferred loft."""
import unittest
from unittest.mock import patch

from shapely.affinity import rotate
from shapely.geometry import box
from shapely.ops import unary_union

from design.maas.massv2 import render
from design.maas.source_geometry.ir import SourceMass, SourceVolume


class StackedRenderTests(unittest.TestCase):
    def test_four_rotated_blocks_keep_four_prism_walls(self):
        volumes = tuple(SourceVolume(
            f'block-{i}', rotate(box(-9, -6, 9, 6), angle, origin=(0, 0)),
            i / 4, (i + 1) / 4, 'fixture')
            for i, angle in enumerate((0, 24, -12, 18)))
        footprint = unary_union([v.footprint for v in volumes])
        source = SourceMass('four-blocks', footprint, volumes=volumes,
                            metadata={'authored_height_m': 14.4})
        with patch.object(render, '_faces', wraps=render._faces) as faces:
            render._render_one(source, (500, 500), site_ring=None,
                               title='', caption={})
        actual = [(call.args[1], call.args[2]) for call in faces.call_args_list]
        self.assertEqual(len(actual), 4, 'Each real occupied block needs its own walls')
        for got, expected in zip(actual, [(0, 3.6), (3.6, 7.2), (7.2, 10.8), (10.8, 14.4)]):
            self.assertAlmostEqual(got[0], expected[0])
            self.assertAlmostEqual(got[1], expected[1])

    def test_identical_adjacent_bands_still_merge_without_false_seams(self):
        plan = box(0, 0, 10, 10)
        volumes = tuple(SourceVolume(str(i), plan, i / 4, (i + 1) / 4, 'fixture')
                        for i in range(4))
        source = SourceMass('continuous-prism', plan, volumes=volumes,
                            metadata={'authored_height_m': 14.4})
        with patch.object(render, '_faces', wraps=render._faces) as faces:
            render._render_one(source, (500, 500), site_ring=None, title='', caption={})
        self.assertEqual(len(faces.call_args_list), 1)
        self.assertEqual(faces.call_args.args[1:3], (0, 14.4))
