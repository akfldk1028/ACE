"""The legal cut keeps the ground floor when two bands share one plan."""
from __future__ import annotations

import unittest

from shapely.geometry import box

from design.maas.geometry_language.source_bridge import _clip_world_mesh_to_host


def _box_mesh(x0, y0, z0, x1, y1, z1):
    import numpy as np
    import manifold3d as m3d
    mesh = m3d.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0)).to_mesh64()
    vertices = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
    triangles = np.asarray(mesh.tri_verts, dtype=int)
    return (tuple(tuple(float(c) for c in v) for v in vertices),
            tuple(tuple(int(i) for i in t) for t in triangles))


class LegalCutSeamTests(unittest.TestCase):
    def test_stacked_bands_with_the_same_plan_leave_one_piece_from_the_ground(self):
        # A bar 0..10 x 0..4, five storeys in fraction height; the parcel is
        # 0..8 x 0..4 on the ground bands and shrinks to 0..6 above 0.4.
        vertices, triangles = _box_mesh(0, 0, 0, 10, 4, 1)
        ground = box(0, 0, 8, 4)
        upper = box(0, 0, 6, 4)
        sections = ((0.0, 0.2, ground), (0.2, 0.4, ground), (0.4, 0.6, upper),
                    (0.6, 0.8, upper), (0.8, 1.0, upper))
        out = _clip_world_mesh_to_host(vertices, triangles, ground, sections=sections)
        self.assertIsNotNone(out)
        zs = [p[2] for p in out[0]]
        self.assertAlmostEqual(min(zs), 0.0, places=6)
        self.assertAlmostEqual(max(zs), 1.0, places=6)
        xs_low = [p[0] for p in out[0] if p[2] < 0.3]
        xs_high = [p[0] for p in out[0] if p[2] > 0.5]
        self.assertAlmostEqual(max(xs_low), 8.0, places=6)
        self.assertAlmostEqual(max(xs_high), 6.0, places=6)


if __name__ == "__main__":
    unittest.main()
