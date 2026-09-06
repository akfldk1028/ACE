"""Actual material, authored domains and legacy solid-query compatibility."""
from dataclasses import replace

from django.test import SimpleTestCase
from shapely.geometry import Point, Polygon, box

from design.maas.source_geometry.ir import SourceMass, SourceVolume


def volume(**fields):
    return SourceVolume("body", fields.pop("footprint", box(0, 0, 10, 10)),
                        0.0, 1.0, "test", **fields)


class SolidQueryRegressionTests(SimpleTestCase):
    def test_sagged_center_is_empty_above_its_roof(self):
        body = volume(top_drop=1, warp=((1, 0), (0, 1), (1, 1, 1, 1), False, .4))
        self.assertEqual(body.top_z(5, 5, 0, 10), 6)
        self.assertFalse(body.plan_at(8, 0, 10).covers(Point(5, 5)))

    def test_thin_plate_has_no_material_below_underside(self):
        plate = volume(top_drop=1, warp=((1, 0), (0, 1), (1, 1, 1, 1), True, 0, .1))
        self.assertEqual(plate.bottom_z(5, 5, 0, 10), 9)
        self.assertIsNone(plate.plan_at(5, 0, 10))
        self.assertAlmostEqual(plate.plan_at(9.5, 0, 10).area, 100)

    def test_prism_has_finite_vertical_extent(self):
        body = volume()
        self.assertIsNone(body.plan_at(-1, 0, 10))
        self.assertIsNone(body.plan_at(11, 0, 10))
        self.assertTrue(body.plan_at(5, 0, 10).equals(body.footprint))

    def test_clipping_preserves_warp_authored_coordinates(self):
        body = volume(top_drop=1, warp=((1, 0), (0, 1), (0, 1, 1, 0), False))
        fragment = replace(body, footprint=box(0, 0, 5, 10))
        self.assertEqual(body.top_z(5, 5, 0, 10), fragment.top_z(5, 5, 0, 10))

    def test_prism_and_profile_holes_and_exact_areas(self):
        ring = Polygon(box(0, 0, 10, 10).exterior.coords, [box(4, 4, 6, 6).exterior.coords])
        prism = volume(footprint=ring)
        self.assertEqual(prism.plan_at(5, 0, 10).area, 96)
        shed = volume(footprint=ring, top_drop=1, top_profile=((0, 0), (1, 1)), profile_across=(1, 0))
        self.assertAlmostEqual(shed.plan_at(5, 0, 10).area, 48, places=9)
        self.assertFalse(shed.plan_at(5, 0, 10).covers(Point(5.5, 5)))


class SolidSurfaceIntegrationTests(SimpleTestCase):
    def test_solid_volume_and_centroid_are_material_not_band_proxy(self):
        from design.maas.massv2.structure import centre_of_mass
        plate = volume(top_drop=1, warp=((1, 0), (0, 1), (1, 1, 1, 1), True, 0, .1))
        source = SourceMass("plate", plate.footprint, volumes=(plate,), metadata={"authored_height_m": 10})
        self.assertAlmostEqual(plate.solid_volume_m3(0, 10), 100, places=8)
        self.assertAlmostEqual(centre_of_mass(source, height_m=10)[2], 9.5, places=8)

    def test_plate_is_not_supported_by_empty_band_below_it(self):
        from design.maas.massv2.structure import connectivity
        body = replace(volume(), top_fraction=.5)
        plate = volume(top_drop=1, warp=((1, 0), (0, 1), (1, 1, 1, 1), True, 0, .1))
        source = SourceMass("floating", body.footprint, volumes=(body, plate), metadata={"authored_height_m": 10})
        share, bodies = connectivity(source)
        self.assertEqual(bodies, 2)
        self.assertLess(share, 1)

    def test_source_slices_keep_disjoint_vertical_intervals(self):
        lower = replace(volume(), top_fraction=.2)
        upper = replace(volume(), bottom_fraction=.8)
        source = SourceMass("two", lower.footprint, volumes=(lower, upper), metadata={"authored_height_m": 10})
        self.assertIsNone(source.plan_at(5))
        self.assertAlmostEqual(source.plan_at(9).area, 100)

    def test_explicit_surface_compiles_with_custom_plan_hole(self):
        from design.maas.massv2 import MatrixForm, compile_matrix_form, place
        from design.maas.source_geometry.solid import PolynomialSurface, ConstantSurface
        ring = Polygon(box(0, 0, 1, 1).exterior.coords, [box(.4, .4, .6, .6).exterior.coords])
        item = replace(place("custom", size=(10, 10, 10)), plan_region=ring,
                       top_surface=PolynomialSurface(((0, 0, .5), (1, 0, .5))),
                       bottom_surface=ConstantSurface(.2))
        form = MatrixForm(name="custom", placements=(item,), primary_language="test",
                          formal_principle="test", dominant_gesture="test", reference_basis="test")
        source = compile_matrix_form(form)
        self.assertIsNotNone(source)
        self.assertAlmostEqual(source.plan_at(3).area, 96)
        self.assertIsNone(source.plan_at(1))
        self.assertFalse(source.plan_at(3).covers(Point(5, 5)))
        self.assertAlmostEqual(source.volumes[0].top_z(10, 5, 0, 10), 10)

    def test_profile_and_prism_material_integrals_remain_exact(self):
        body = volume()
        self.assertAlmostEqual(body.solid_volume_m3(0, 10), 1000, places=9)
        roof = volume(top_drop=1, top_profile=((0, 0), (.5, 1), (1, 0)), profile_across=(1, 0))
        self.assertAlmostEqual(roof.solid_volume_m3(0, 10), 500, places=9)

    def test_transformed_surface_keeps_authored_heights(self):
        from design.maas.source_geometry.solid import PolynomialSurface, ConstantSurface
        body = volume(top_surface=PolynomialSurface(((1, 0, .1),)), bottom_surface=ConstantSurface(0))
        moved = body.transformed_plan((0, -2, 3, 0, 20, 5))
        self.assertAlmostEqual(moved.top_z(10, 20, 0, 10), body.top_z(5, 5, 0, 10))
        self.assertAlmostEqual(moved.solid_volume_m3(0, 10), 6*body.solid_volume_m3(0, 10), places=7)

    def test_clipped_compiled_warp_keeps_its_uncut_domain(self):
        from design.maas.massv2 import MatrixForm, compile_matrix_form, place
        item = replace(place("roof", size=(10, 10, 10)), top_drop=1,
                       warp=((1, 0), (0, 1), (0, 1, 1, 0), False))
        form = MatrixForm(name="roof", placements=(item,), primary_language="test",
                          formal_principle="test", dominant_gesture="test", reference_basis="test")
        source = compile_matrix_form(form, allowed_at=lambda z: box(0, 0, 5, 10))
        self.assertAlmostEqual(source.volumes[0].top_z(5, 5, 0, 10), 5)

    def test_renderer_uses_explicit_surface_and_preserves_hole_faces(self):
        from design.maas.massv2.render import _slope_of, _top_at, _faces, _PAL
        from design.maas.source_geometry.solid import ConstantSurface
        ring = Polygon(box(0,0,10,10).exterior.coords, [box(4,4,6,6).exterior.coords])
        plate = volume(footprint=ring, top_surface=ConstantSurface(1), bottom_surface=ConstantSurface(.9))
        slope = _slope_of(plate, 0, 10)
        self.assertIsNotNone(slope)
        self.assertAlmostEqual(_top_at(5, 5, 10, slope), 10)
        roof_faces = [points for points,tone,stroke in _faces(ring,0,10,slope) if tone == _PAL.roof and not stroke]
        self.assertGreater(len(roof_faces), 10)
        self.assertAlmostEqual(sum(Polygon([(p[0],p[1]) for p in triangle]).area
                                   for triangle in plate.surface_mesh), 96, places=8)

    def test_curved_shape_measure_sees_sag(self):
        from design.maas.massv2.measure import measure_form
        roof = volume(top_drop=1, warp=((1,0),(0,1),(1,1,1,1),False,.6))
        source = SourceMass("sag", roof.footprint, volumes=(roof,), metadata={"authored_height_m": 10})
        self.assertGreater(measure_form(source).section_change, .01)

    def test_underlying_sag_does_not_support_a_center_column(self):
        from design.maas.massv2.structure import worst_members
        roof = replace(volume(top_drop=1, warp=((1,0),(0,1),(1,1,1,1),False,.4)), top_fraction=.5)
        column = replace(volume(footprint=box(4,4,6,6)), bottom_fraction=.5)
        source = SourceMass("column", roof.footprint, volumes=(roof,column), metadata={"authored_height_m": 10})
        self.assertEqual(worst_members(source, height_m=10)[0], float("inf"))

    def test_external_matrix_form_payload_roundtrips_hole_and_clipped_saddle(self):
        from design.maas.massv2 import MatrixForm, compile_matrix_form, place
        from shapely.geometry import mapping
        ring = Polygon(box(0,0,1,1).exterior.coords, [box(.4,.4,.6,.6).exterior.coords])
        record = {"schema_version": "arr.maas.matrix_form.v1", "name": "saddle",
                  "primary_language": "courtyard", "formal_principle": "continuous_cover",
                  "dominant_gesture": "court_below_saddle", "reference_basis": "site",
                  "placements": [{"role": "cover", "matrix4": place("cover",size=(10,10,10)).matrix,
                                  "plan_region": mapping(ring),
                                  "top_surface": {"type": "polynomial", "terms": [[0,0,.7],[1,0,.3],[0,1,.3],[1,1,-.6]]},
                                  "bottom_surface": {"type": "constant", "height": .2}}]}
        form = MatrixForm.from_record(record)
        source = compile_matrix_form(form, allowed_at=lambda z: box(0,0,5,10))
        self.assertAlmostEqual(source.volumes[0].top_z(5,2,0,10), 8.5, places=8)
        self.assertFalse(source.plan_at(4).covers(Point(4.5,5)))
        replay = MatrixForm.from_record(form.to_record())
        self.assertEqual(compile_matrix_form(replay).volumes[0].signature(),
                         compile_matrix_form(form).volumes[0].signature())

    def test_surface_payload_rejects_unknown_and_unbounded_height(self):
        from design.maas.massv2.form import Placement
        from design.maas.massv2 import place
        for surface in ({"type": "eval", "code": "anything"},
                        {"type": "constant", "height": 2},
                        {"type": "polynomial", "terms": [[-1,0,1]]}):
            with self.subTest(surface=surface), self.assertRaises(ValueError):
                Placement.from_record({"role": "invalid", "matrix4": place("x",size=(10,10,10)).matrix,
                                       "top_surface": surface})

    def test_shape_operation_reaches_execute_steps_and_legal_clipping(self):
        from design.maas.massv2.grammar import parti_from_record
        from design.maas.massv2.execute import execute_steps
        from design.maas.massv2 import compile_matrix_form
        from shapely.geometry import mapping
        region = Polygon(box(0,0,1,1).exterior.coords, [box(.3,.3,.7,.7).exterior.coords])
        parti = parti_from_record({"name":"court_saddle", "ops":[{"op":"extrude"},
            {"op":"shape", "plan_region":mapping(region),
             "top_surface":{"type":"polynomial","terms":[[0,0,.7],[1,0,.3],[0,1,.3],[1,1,-.6]]}}]})
        self.assertEqual([op.verb for op in parti.ops], ["extrude","shape"])
        steps = execute_steps(parti,buildable=box(0,0,20,20),axis=(1,0),height_m=10)
        self.assertEqual(len(steps),2)
        source = compile_matrix_form(steps[-1][1],allowed_at=lambda z: box(0,0,20,20))
        self.assertIsNotNone(source)
        self.assertTrue(any(v.top_surface is not None for v in source.volumes))
        self.assertTrue(any(v.footprint.interiors for v in source.volumes))

    def test_compiler_drops_structural_sheet_with_no_material_contact(self):
        from design.maas.massv2 import MatrixForm, compile_matrix_form, place
        from design.maas.source_geometry.solid import ConstantSurface
        room = place("room",size=(10,10,5))
        sheet = replace(place("roof",size=(10,10,10),occupiable=False),
                        top_surface=ConstantSurface(1),bottom_surface=ConstantSurface(.9))
        source = compile_matrix_form(MatrixForm(name="floating",placements=(room,sheet),primary_language="test"))
        self.assertEqual([v.role for v in source.volumes], ["room"])

    def test_roof_seating_uses_real_underside_clearance(self):
        from design.maas.massv2 import MatrixForm, place
        from design.maas.massv2.compile import _sheets_settled
        room = place("room",size=(30,12,20))
        sheet = replace(place("roof",size=(34,16,2),at=(0,0,20),occupiable=False),
            top_drop=1,warp=((1,0),(0,1),(1,1,1,1),True,.25,.15))
        settled = _sheets_settled(MatrixForm(name="roof",placements=(room,sheet),primary_language="test"))
        low,high = settled.placements[1].z_span()
        material = volume(footprint=box(0,0,34,16),top_drop=1,warp=sheet.warp)
        self.assertAlmostEqual(material.bottom_z(17,8,low,high),20,delta=.01)

    def test_overlapping_members_are_union_material_not_double_weight(self):
        from design.maas.massv2.structure import centre_of_mass
        from design.maas.source_geometry.solid import ConstantSurface
        bottom = replace(volume(),top_fraction=.5)
        upper = volume(top_surface=ConstantSurface(1),bottom_surface=ConstantSurface(.4))
        source = SourceMass("overlap",bottom.footprint,volumes=(bottom,upper),metadata={"authored_height_m":10})
        self.assertAlmostEqual(centre_of_mass(source,height_m=10)[2],5,places=8)
        self.assertAlmostEqual(source.solid_volume_m3(),1000,places=8)

    def test_raised_material_cannot_skip_cantilever_gate_via_band_base(self):
        from design.maas.massv2.structure import worst_members, assess_standing
        from design.maas.source_geometry.solid import ConstantSurface
        slab = volume(footprint=box(-10,-10,10,10),top_surface=ConstantSurface(1),bottom_surface=ConstantSurface(.9))
        column = replace(volume(footprint=box(-1,-1,1,1)),top_fraction=.9)
        source = SourceMass("raised",slab.footprint,volumes=(slab,column),
            metadata={"authored_height_m":10,"structural_bands":[1]})
        self.assertGreater(worst_members(source,height_m=10)[0],1.6)
        self.assertFalse(assess_standing(source,height_m=10).stands)

    def test_remote_partial_cutter_does_not_refuse_explicit_surface(self):
        from design.maas.massv2 import MatrixForm, compile_matrix_form, place
        from design.maas.source_geometry.solid import ConstantSurface
        body = replace(place("body",size=(4,4,10)),top_surface=ConstantSurface(1))
        cutter = place("cut",size=(4,4,2),at=(100,0,2),kind="subtractive")
        source = compile_matrix_form(MatrixForm(name="remote",placements=(body,cutter),primary_language="test"))
        self.assertIsNotNone(source)

    def test_contact_preserves_narrow_authored_profile_valley(self):
        from design.maas.source_geometry.solid import ProfileSurface,ConstantSurface,contact_region
        roof = volume(footprint=box(0,0,20,20),top_surface=ProfileSurface(
            ((0,1),(.181,1),(.185,0),(.189,1),(1,1)),(1,0),(0,20)))
        plate = volume(footprint=box(3.62,0,3.78,20),top_surface=ConstantSurface(1),bottom_surface=ConstantSurface(.9))
        contact = contact_region(roof,plate,(0,10),(0,10),0)
        self.assertAlmostEqual(contact.area,.32,places=7)

    def test_floor_proxy_unions_coincident_flat_and_explicit_members(self):
        from design.maas.massv2.measure import gross_floor_area_m2
        from design.maas.source_geometry.solid import ConstantSurface
        first = volume()
        second = volume(top_surface=ConstantSurface(1))
        source = SourceMass("coincident",first.footprint,volumes=(first,second),metadata={"authored_height_m":12})
        self.assertAlmostEqual(gross_floor_area_m2(source,floor_height_m=3),400)

    def test_floor_proxy_is_not_lost_when_overlap_adds_thin_band_edges(self):
        from design.maas.massv2.measure import gross_floor_area_m2
        from design.maas.source_geometry.solid import ConstantSurface
        tall = volume(top_surface=ConstantSurface(1))
        pieces = tuple(replace(volume(),bottom_fraction=i/24,top_fraction=(i+1)/24) for i in range(24))
        source = SourceMass("split",tall.footprint,volumes=(tall,*pieces),metadata={"authored_height_m":12})
        self.assertAlmostEqual(gross_floor_area_m2(source,floor_height_m=3),400)

    def test_custom_plan_rejects_transform_that_would_fill_its_hole(self):
        from design.maas.massv2 import place
        ring = Polygon(box(0,0,1,1).exterior.coords,[box(.3,.3,.7,.7).exterior.coords])
        with self.assertRaises(ValueError):
            replace(place("lean",size=(10,10,10),lean_degrees=20),plan_region=ring)

    def test_payload_can_author_a_following_thin_saddle_underside(self):
        from design.maas.massv2 import place
        from design.maas.massv2.form import Placement
        top = {"type":"polynomial","terms":[[0,0,.7],[1,0,.3],[0,1,.3],[1,1,-.6]]}
        plate = Placement.from_record({"role":"plate","matrix4":place("x",size=(10,10,10)).matrix,
            "top_surface":top,"bottom_surface":{"type":"affine","surface":top,
                "world_to_authored":[1,0,0,1,0,0],"offset":-.1}})
        self.assertAlmostEqual(plate.top_surface.value(.3,.7)-plate.bottom_surface.value(.3,.7),.1)
