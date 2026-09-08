"""Geometry contracts across composed operations, measured after execution."""
from dataclasses import replace
from types import SimpleNamespace
from django.test import SimpleTestCase
from shapely.geometry import box
from design.maas.massv2.execute import _Frame, _lift, _crown
from design.maas.massv2.form import MatrixForm
from design.maas.massv2.compile import _plan, compile_matrix_form
from design.maas.massv2.ops.relational import merge, inscribe
from design.maas.geometry_language.affine_matrix import validate_matrix4

class CompositionPreservationTests(SimpleTestCase):
    def frame(self):
        return _Frame(box(0,0,40,40),(1,0),20,4)

    def source(self, frame):
        return compile_matrix_form(MatrixForm(name="preservation",placements=tuple(frame.placements),primary_language="solid_body"),storey_height_m=4,allowed_at=None)

    def test_merge_retains_gabled_upper_sections(self):
        f=self.frame()
        f.placements=[replace(f.box(name,w=12,d=12,z=0,h=12,dx=dx),top_drop=.4,ridge_along=(1.,0.)) for name,dx in (("a",-7),("b",7))]
        merge(f,SimpleNamespace(params={}))
        source=self.source(f)
        self.assertAlmostEqual(source.plan_at(11).area,60.,places=5)
        self.assertEqual([v.section_kind() for v in source.volumes].count("ridge"),2)

    def test_merge_retains_sloping_upper_sections(self):
        f=self.frame()
        f.placements=[replace(f.box(name,w=12,d=12,z=0,h=12,dx=dx),top_drop=.4,drop_toward=(1.,0.)) for name,dx in (("a",-7),("b",7))]
        merge(f,SimpleNamespace(params={}))
        self.assertAlmostEqual(self.source(f).plan_at(11).area,60.,places=5)

    def test_lift_translates_courtyard_without_shrinking_or_moving_plan(self):
        f=self.frame()
        item=replace(f.box("court",w=20,d=20,z=0,h=8,turn=23),plan_region=box(0,0,1,1).difference(box(.25,.25,.75,.75)))
        f.placements=[item]
        _lift(f,SimpleNamespace(params={"clearance":.2}))
        raised=next(p for p in f.placements if p.role=="court")
        self.assertAlmostEqual(_plan(raised).area,300.,places=6)
        self.assertLess(_plan(raised).symmetric_difference(_plan(item)).area,1e-7)
        self.assertEqual(len(_plan(raised).interiors),1)
        self.assertAlmostEqual(raised.z_span()[0]-item.z_span()[0],4.)
        self.assertAlmostEqual(raised.z_span()[1]-item.z_span()[1],4.)

    def test_lift_preserves_sheared_local_frame(self):
        f=self.frame()
        item=f.box("sheared",w=20,d=20,z=0,h=8)
        rows=[list(row) for row in item.matrix];rows[0][1]=8.
        item=replace(item,matrix=validate_matrix4(rows))
        f.placements=[item]
        _lift(f,SimpleNamespace(params={"clearance":.2}))
        raised=next(p for p in f.placements if p.role=="sheared")
        self.assertLess(_plan(raised).symmetric_difference(_plan(item)).area,1e-7)

    def test_lift_preserves_actual_crown_section_at_translated_height(self):
        f=self.frame();f.placements=[f.box("host",w=20,d=20,z=0,h=8)]
        _crown(f,SimpleNamespace(params={"form":"dome","sag":.35}))
        before=self.source(f).plan_at(7.)
        _lift(f,SimpleNamespace(params={"clearance":.2}))
        after=self.source(f).plan_at(11.)
        self.assertLess(before.symmetric_difference(after).area,1e-7)

    def test_crowned_inscription_keeps_prismatic_cutter_and_explicit_csg_refusal(self):
        f=self.frame();f.placements=[f.box("host",w=20,d=20,z=0,h=12)]
        _crown(f,SimpleNamespace(params={"form":"dome","sag":.35}))
        inscribe(f,SimpleNamespace(params={"size":.35,"depth":.25}))
        cutter=next(p for p in f.placements if p.kind=="subtractive")
        self.assertIsNone(cutter.top_surface)
        with self.assertRaisesRegex(ValueError,"partial-height cutters through explicit surfaces require interval CSG"):
            self.source(f)
