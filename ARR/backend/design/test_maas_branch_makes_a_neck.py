"""Branch has to leave a void between its arms, or it is a fan.

`_book_branch_macro` selected the terminal part of the trunk, rotated two copies
about a shoulder, and unioned them onto the *whole* input. The original terminal
mass stayed sitting between the arms, so nothing separated them: the arms were
present and the figure read as a solid fan. Measured across the operatives,
only `puncture` articulated at all - branch, notch, carve and fracture produced
no lobes.

Cutting the trunk at the same shoulder the arms pivot about is what makes it a
branch: above the shoulder the volume exists only as the two arms, so the space
between them is void and the junction narrows.
"""

import numpy as np
from django.test import SimpleTestCase
from shapely.geometry import Polygon
from shapely.ops import unary_union

import manifold3d as m3d

from design.maas.design_space import delivered_void_band
from design.maas.geometry_language.compiler import _book_branch_macro


def _plan(solid):
    mesh = solid.to_mesh()
    vertices = np.asarray(mesh.vert_properties)[:, :3]
    faces = [
        Polygon([(vertices[i][0], vertices[i][1]) for i in triangle])
        for triangle in np.asarray(mesh.tri_verts)
    ]
    return unary_union([f for f in faces if f.is_valid and f.area > 1e-9])


def _trunk():
    return m3d.Manifold.cube((40.0, 14.0, 12.0), True)


class BranchMakesANeckTests(SimpleTestCase):
    def setUp(self):
        self.plan = _plan(_book_branch_macro(_trunk(), {}, "test"))

    def test_the_arms_leave_a_void_between_them(self):
        """A fan fills its own convex hull; a branch does not."""

        solidity = self.plan.area / self.plan.convex_hull.area

        self.assertLess(solidity, 0.75)

    def test_the_figure_is_open_enough_to_be_a_position_on_the_void_axis(self):
        void = 1.0 - self.plan.area / self.plan.minimum_rotated_rectangle.area

        self.assertNotEqual("solid_body", delivered_void_band(void).band_id)

    def test_the_result_is_still_one_connected_building(self):
        """A branch is a Y, not two buildings. The neck must hold."""

        result = _book_branch_macro(_trunk(), {}, "test")

        self.assertEqual(1, len(result.decompose()))

    def test_it_is_measurably_more_open_than_keeping_the_whole_trunk(self):
        """Compare like with like rather than against a guessed magnitude.

        The old behaviour is reconstructed here - the same arms unioned onto the
        untouched input - so the assertion is about the change itself: measured
        on a 40x14x12 trunk, solidity falls 0.801 -> 0.676 and the open share of
        the figure rises 0.426 -> 0.511, which moves it to a different position
        on the void axis.
        """

        import design.maas.geometry_language.compiler as compiler

        trunk = _trunk()
        minx, miny, minz, maxx, maxy, maxz = trunk.bounding_box()
        span = maxx - minx
        shoulder = minx + span * 0.42
        overlap = max(span, maxz - minz, 1.0) * 0.035
        arm_source = trunk.trim_by_plane((1.0, 0.0, 0.0), shoulder - overlap)
        pivot = (shoulder, (miny + maxy) / 2.0, (minz + maxz) / 2.0)
        arm_source = compiler._around_pivot(
            arm_source, pivot, lambda item: item.scale((1.0, 0.54 + 0.28 * 0.38, 0.92))
        )
        arms = [
            compiler._around_pivot(
                arm_source, pivot, lambda item, s=s: item.rotate((0.0, 0.0, s))
            )
            for s in (-32.0, 32.0)
        ]
        fan = _plan(m3d.Manifold.batch_boolean([trunk, *arms], m3d.OpType.Add))

        branch_solidity = self.plan.area / self.plan.convex_hull.area
        fan_solidity = fan.area / fan.convex_hull.area

        self.assertLess(branch_solidity, fan_solidity - 0.05)
