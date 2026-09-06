"""Export-grid collinearity must not open a previously closed surface."""
from collections import Counter
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.geometry_language.compiler import _canonicalize_export_mesh
from design.maas.geometry_language.gate import compilation_gate
from design.maas.geometry_language.export_mesh import EXPORT_DECIMAL_PLACES


def edge_counts(triangles):
    return Counter((a, b) for tri in triangles
                   for a, b in zip(tri, (*tri[1:], tri[0])))


def grid_volume6(vertices, triangles):
    points = [tuple(int(Decimal(str(x)) * 10**EXPORT_DECIMAL_PLACES) for x in v) for v in vertices]
    return sum(a[0]*(b[1]*c[2]-b[2]*c[1])
               + a[1]*(b[2]*c[0]-b[0]*c[2])
               + a[2]*(b[0]*c[1]-b[1]*c[0])
               for a,b,c in ([points[i] for i in tri] for tri in triangles))


def closed_tetra_with_collinear_face():
    # Actual BOOK failure coordinates, with a midpoint splitting one side of
    # a tetrahedron edge but a zero-area face joining it to the unsplit side.
    a=(7.26832830,7.66478257,10.15384615)
    middle=(8.72199396,6.70668475,10.15384615)
    c=(10.17565962,5.74858693,10.15384615)
    vertices=(a,(a[0],a[1]+2,a[2]),c,(a[0],a[1],a[2]+2),middle)
    triangles=((0,1,4),(4,1,2),(0,4,2),(0,2,3),(0,3,1),(1,3,2))
    return vertices,triangles


class ExportCollinearityTests(SimpleTestCase):
    def test_book_collinear_face_retriangulates_without_changing_boundary_or_volume(self):
        vertices,triangles=closed_tetra_with_collinear_face()
        before=edge_counts(triangles)
        self.assertTrue(all(before[b,a]==1 for a,b in before))
        result_vertices,result_triangles=_canonicalize_export_mesh(vertices,triangles)
        self.assertEqual(result_vertices,vertices)
        self.assertEqual(len(result_triangles),len(triangles))
        after=edge_counts(result_triangles)
        self.assertTrue(all(n==1 and after[b,a]==1 for (a,b),n in after.items()))
        self.assertEqual(grid_volume6(vertices,triangles),grid_volume6(result_vertices,result_triangles))
        result=SimpleNamespace(status="compiled",vertices=result_vertices,triangles=result_triangles,
                               metrics={"volume":1,"watertight":True,"manifold":True,
                                        "closed_solid":True,"self_intersection_checked_by_kernel":True,
                                        "outward_normals":True})
        self.assertEqual(compilation_gate(result),())
        self.assertEqual(_canonicalize_export_mesh(result_vertices,result_triangles),
                         (result_vertices,result_triangles))

    def test_real_nonzero_tiny_face_remains_for_hard_gate(self):
        vertices=((0.,0.,0.),(.0001,0.,0.),(.0002,.00000001,0.))
        triangles=((0,1,2),)
        self.assertEqual(_canonicalize_export_mesh(vertices,triangles),(vertices,triangles))
        result=SimpleNamespace(status="compiled",vertices=vertices,triangles=triangles,metrics={})
        self.assertIn("tiny_face",{i.code for i in compilation_gate(result)})

    def test_nonmanifold_neighborhood_is_not_repaired(self):
        vertices,triangles=closed_tetra_with_collinear_face()
        triangles=(*triangles,triangles[3])
        self.assertEqual(_canonicalize_export_mesh(vertices,triangles),(vertices,triangles))

    def test_wrong_winding_neighbor_is_not_repaired(self):
        vertices,triangles=closed_tetra_with_collinear_face()
        triangles=tuple(tuple(reversed(t)) if i==3 else t for i,t in enumerate(triangles))
        self.assertEqual(_canonicalize_export_mesh(vertices,triangles),(vertices,triangles))

    def test_exact_float_collinear_face_also_preserves_closed_topology(self):
        vertices=((0.,0.,0.),(0.,2.,0.),(2.,0.,0.),(0.,0.,2.),(1.,0.,0.))
        triangles=closed_tetra_with_collinear_face()[1]
        out_vertices,out_triangles=_canonicalize_export_mesh(vertices,triangles)
        edges=edge_counts(out_triangles)
        self.assertTrue(all(edges[b,a]==1 for a,b in edges))
        self.assertEqual(grid_volume6(vertices,triangles),grid_volume6(out_vertices,out_triangles))
