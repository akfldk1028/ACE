"""BOOK surface bounds must cut actual occupied material, not redraw its box."""
from dataclasses import replace
import json

from django.test import SimpleTestCase
import manifold3d as m3d

from design.maas.creative_program_author import authored_programs_from_payload
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.author_output_schema import author_node_schema
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.gate import compilation_gate
from design.maas.geometry_language.llm_adapter import geometry_programs_from_author_payload


DOME = {"type": "polynomial", "terms": [
    [0, 0, .6], [1, 0, .8], [2, 0, -.8], [0, 1, .8], [0, 2, -.8],
]}
GROUND = {"type": "constant", "height": 0}


def base_nodes(size=(20, 10, 10)):
    return [
        GeometryNode("unit", "primitive", "box", parameters={"width": 1, "depth": 1, "height": 1}),
        GeometryNode("body", "transform", "matrix4", ("unit",), {"matrix4": [
            [size[0], 0, 0, 0], [0, size[1], 0, 0], [0, 0, size[2], 0], [0, 0, 0, 1],
        ]}),
    ]


def surface_node(node_id="roof", input_id="body", top=DOME, bottom=GROUND):
    return GeometryNode(node_id, "modifier", "bound_surfaces", (input_id,),
                        {"top_surface": top, "bottom_surface": bottom})


def program(nodes):
    return GeometryProgram(tuple(nodes), nodes[-1].id, "surface_probe")


def section_area(result, z):
    return float(result._solid.slice(z).area())


class BookSurfaceBoundsTests(SimpleTestCase):
    def compiled(self, nodes):
        result = compile_geometry_program(program(nodes))
        self.assertEqual(result.status, "compiled", [i.to_dict() for i in result.issues])
        self.assertFalse(compilation_gate(result), [i.to_dict() for i in compilation_gate(result)])
        return result

    def test_exact_payload_cannot_silently_ignore_surface_fields(self):
        for incompatible in (
            GeometryNode("wrong", "macro", "profiled_hall", ("body",), {
                "section_controls": [[0, 1], [1, 1]], "top_surface": DOME}),
            GeometryNode("wrong", "primitive", "box", parameters={
                "width": 20, "depth": 10, "height": 10, "top_surface": DOME}),
        ):
            with self.subTest(operator=incompatible.operator):
                nodes = base_nodes() + [incompatible] if incompatible.inputs else [incompatible]
                result = compile_geometry_program(program(nodes))
                self.assertNotEqual(result.status, "compiled")
                self.assertIn("unsupported_surface_parameters", {i.code for i in result.issues})
                with self.assertRaisesRegex(ValueError, "unsupported_surface_parameters"):
                    authored_programs_from_payload({"geometry_programs": [program(nodes).to_dict()]}, expected_count=1)

    def test_exact_author_payload_preserves_surface_fields_and_matrix_ancestry(self):
        try:
            authored = authored_programs_from_payload({"geometry_programs": [
                program(base_nodes() + [surface_node()]).to_dict(),
            ]}, expected_count=1)[0].program
        except ValueError as exc:
            self.fail(f"Valid surface bounds must survive author normalization: {exc}")
        result = compile_geometry_program(authored)
        self.assertEqual(result.status, "compiled", result.issues)
        self.assertLess(section_area(result, 9), 80)
        self.assertEqual(len([n for n in authored.nodes if n.operator == "box"]), 1)
        self.assertTrue(any(t.get("matrix4") for t in result.trace))
        self.assertEqual(authored.node_map["roof"].inputs, ("body",))
        replay = compile_geometry_program(GeometryProgram.from_dict(authored.to_dict()))
        self.assertEqual(result.geometry_hash, replay.geometry_hash)

    def test_structured_author_schema_and_parser_accept_surface_records(self):
        schema = author_node_schema(["bound_surfaces"])
        self.assertIn("bound_surfaces", json.dumps(schema))
        item = {"name": "structured_surface", "base_seed": "block", "base_form_id": "cube",
                "root_id": "roof", "nodes": []}
        for node in base_nodes() + [surface_node()]:
            parameters = []
            for key, value in node.parameters.items():
                if key == "matrix4":
                    parameters.append({"name": key, "value_type": "matrix4", "matrix4_value": value})
                elif isinstance(value, dict):
                    parameters.append({"name": key, "value_type": "structured_json", "structured_json": json.dumps(value)})
                else:
                    parameters.append({"name": key, "value_type": "number", "numeric_value": value})
            item["nodes"].append({"id": node.id, "kind": node.kind, "operator": node.operator,
                                  "inputs": list(node.inputs), "parameters": parameters, "semantic_role": ""})
        parsed = geometry_programs_from_author_payload({"programs": [item]}, expected_count=1)
        result = compile_geometry_program(parsed[0])
        self.assertLess(section_area(result, 9), 80)
        self.assertEqual(parsed[0].node_map["roof"].parameters["top_surface"], DOME)

    def test_dome_is_sampled_at_live_physical_scale(self):
        result = self.compiled(base_nodes() + [surface_node()])
        # Analytic dome integral is 2000*(.6+.8/6+.8/6)=1733.3333.
        # The old unit-grid-then-scale shortcut instead produces 1600.
        self.assertAlmostEqual(result.metrics["volume"], 1733.333333, delta=4)
        self.assertGreater(section_area(result, 9), 76)
        self.assertLess(section_area(result, 9), 80)
        self.assertAlmostEqual(section_area(result, 3), 200, places=6)

    def test_following_underside_keeps_air_out_of_occupied_floor(self):
        underside = {"type": "affine", "surface": DOME,
                     "world_to_authored": [1, 0, 0, 1, 0, 0], "offset": -.1}
        result = self.compiled(base_nodes() + [surface_node(bottom=underside)])
        self.assertAlmostEqual(result.metrics["volume"], 200, places=5)
        self.assertEqual(section_area(result, 3), 0)

    def test_envelope_intersection_preserves_existing_hole_and_profile(self):
        nodes = base_nodes() + [
            GeometryNode("hole", "primitive", "box", parameters={"width": 4, "depth": 4, "height": 10}),
            GeometryNode("cut_pose", "transform", "translate", ("hole",), {"vector": [8, 3, 0]}),
            GeometryNode("ring", "boolean", "difference", ("body", "cut_pose")),
            GeometryNode("profile", "macro", "profiled_hall", ("ring",), {
                "section_controls": [[0, .5], [.5, 1], [1, .5]], "span_axis": "x"}),
        ]
        before = self.compiled(nodes)
        after = self.compiled(nodes + [surface_node(input_id="profile")])
        self.assertAlmostEqual(section_area(after, 3), 184, places=6)
        added = m3d.Manifold.batch_boolean([after._solid, before._solid], m3d.OpType.Subtract)
        self.assertAlmostEqual(added.volume(), 0, places=8)
        self.assertLess(after.metrics["volume"], before.metrics["volume"])

    def test_finite_height_csg_removes_only_its_vertical_interval(self):
        nodes = base_nodes() + [surface_node(),
            GeometryNode("cut", "primitive", "box", parameters={"width": 4, "depth": 4, "height": 2}),
            GeometryNode("cut_pose", "transform", "translate", ("cut",), {"vector": [2, 2, 3]}),
            GeometryNode("result", "boolean", "difference", ("roof", "cut_pose"))]
        result = self.compiled(nodes)
        self.assertAlmostEqual(section_area(result, 4), 184, places=6)
        self.assertAlmostEqual(section_area(result, 2), 200, places=6)
        # Also preserve a finite-height void that predates the new modifier.
        nodes = [n for n in nodes if n.id != "roof"]
        nodes[-1] = replace(nodes[-1], inputs=("body", "cut_pose"))
        result = self.compiled(nodes + [surface_node(input_id="result")])
        self.assertAlmostEqual(section_area(result, 4), 184, places=6)
        self.assertAlmostEqual(section_area(result, 2), 200, places=6)

    def test_zero_thickness_boundary_closes_as_wedge_without_filling_below(self):
        top = {"type": "polynomial", "terms": [[1, 0, 1]]}
        result = self.compiled(base_nodes() + [surface_node(top=top)])
        self.assertAlmostEqual(result.metrics["volume"], 1000, places=6)
        self.assertAlmostEqual(section_area(result, 5), 100, places=6)

    def test_shared_profile_record_keeps_authored_fold_station(self):
        top = {"type": "profile", "points": [[0, .4], [.37, 1], [1, .4]],
               "axis": [1, 0], "span": [0, 1]}
        result = self.compiled(base_nodes() + [surface_node(top=top)])
        self.assertAlmostEqual(result.metrics["volume"], 1400, places=6)
        # At 70% height, exactly half the gable plan is occupied.
        self.assertAlmostEqual(section_area(result, 7), 100, places=6)

    def test_physical_candidate_preserves_explicit_schedule_and_actual_gfa(self):
        from design.test_maas_dimensional_intent import physical, intent

        source = replace(program(base_nodes() + [surface_node()]),
                         metadata={"dimensional_intent": intent()})
        candidate = physical(source)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["storey_evidence"]["storey_count"], 4)
        self.assertAlmostEqual(candidate["storey_evidence"]["actual_gfa_m2"], 320, places=3)
        self.assertEqual(candidate["dimensional_intent_evidence"]["requested"], intent())
        physical_program = GeometryProgram.from_dict(candidate["geometry_program"])
        self.assertEqual(physical_program.node_map["roof"].parameters["top_surface"], DOME)

    def test_separate_curved_halls_and_low_connector_leave_court_open(self):
        nodes = base_nodes((8, 20, 10)) + [surface_node("west"),
            GeometryNode("east_base", "transform", "matrix4", ("unit",), {"matrix4": [
                [10, 0, 0, 16], [0, 20, 0, 0], [0, 0, 10, 0], [0, 0, 0, 1]]}),
            surface_node("east", "east_base", top={"type": "polynomial", "terms": [
                [0, 0, .6], [1, 0, .4], [0, 1, .4], [1, 1, -.8]]}),
            GeometryNode("connector", "transform", "matrix4", ("unit",), {"matrix4": [
                [26, 0, 0, 0], [0, 4, 0, 18], [0, 0, 3.5, 0], [0, 0, 0, 1]]}),
            GeometryNode("halls", "boolean", "union", ("west", "east", "connector"))]
        result = self.compiled(nodes)
        self.assertEqual(result.metrics["component_count"], 1)
        court = m3d.Manifold.cube((8, 12, 20)).translate((8, 2, 0))
        self.assertAlmostEqual(m3d.Manifold.batch_boolean([result._solid, court], m3d.OpType.Intersect).volume(), 0, places=8)
        self.assertAlmostEqual(section_area(result, 2), 428, places=6)
        self.assertEqual({t["node_id"] for t in result.trace if t["operator"] == "bound_surfaces"}, {"west", "east"})

    def test_later_rotation_carries_surfaces_without_reinterpreting_bounds(self):
        nodes = base_nodes() + [surface_node()]
        before = self.compiled(nodes)
        nodes += [GeometryNode("rotated", "transform", "rotate", ("roof",), {"axis": "z", "angle": 31})]
        after = self.compiled(nodes)
        self.assertAlmostEqual(after.metrics["volume"], before.metrics["volume"], places=5)
        self.assertAlmostEqual(section_area(after, 9), section_area(before, 9), places=5)

    def test_coarse_surface_cannot_be_enlarged_after_sampling(self):
        nodes = base_nodes((2, 1, 1)) + [surface_node(),
            GeometryNode("enlarge", "transform", "scale", ("roof",), {"vector": [10, 10, 10]})]
        result = compile_geometry_program(program(nodes))
        self.assertNotEqual(result.status, "compiled")
        self.assertIn("surface_sampling_requires_prior_sizing", {i.code for i in result.issues})

    def test_composed_canceling_scales_and_rigid_rotation_are_not_refused(self):
        nodes = base_nodes((2, 1, 1)) + [surface_node(),
            GeometryNode("large", "transform", "scale", ("roof",), {"vector": [10, 10, 10]}),
            GeometryNode("pose", "transform", "rotate", ("large",), {"axis": "z", "angle_degrees": 31}),
            GeometryNode("restore", "transform", "scale", ("pose",), {"vector": [.1, .1, .1]})]
        result = self.compiled(nodes)
        before = self.compiled(base_nodes((2, 1, 1)) + [surface_node()])
        self.assertAlmostEqual(result.metrics["volume"], before.metrics["volume"], places=6)

    def test_sampling_guard_checks_each_reused_consumer(self):
        nodes = base_nodes((2, 1, 1)) + [surface_node(),
            GeometryNode("large", "transform", "scale", ("roof",), {"vector": [10, 10, 10]}),
            GeometryNode("both", "boolean", "union", ("roof", "large"))]
        result = compile_geometry_program(program(nodes))
        self.assertIn("surface_sampling_requires_prior_sizing", {i.code for i in result.issues})

    def test_anisotropic_enlargement_cannot_hide_behind_resolved_long_axis(self):
        nodes = base_nodes((20, 1, 10)) + [surface_node(),
            GeometryNode("wide", "transform", "scale", ("roof",), {"vector": [1, 50, 1]})]
        result = compile_geometry_program(program(nodes))
        self.assertIn("surface_sampling_requires_prior_sizing", {i.code for i in result.issues})

    def test_resolved_surface_uniform_enlargement_preserves_mesh(self):
        nodes = base_nodes() + [surface_node()]
        before = self.compiled(nodes)
        after = self.compiled(nodes + [
            GeometryNode("large", "transform", "scale", ("roof",), {"vector": [2, 2, 2]})])
        self.assertAlmostEqual(after.metrics["volume"], before.metrics["volume"] * 8, places=5)

    def test_attach_guest_scaling_obeys_surface_sampling(self):
        for size, accepted in [((2, 1, 1), False), ((20, 10, 10), True)]:
            with self.subTest(size=size):
                nodes = base_nodes(size) + [surface_node(),
                    GeometryNode("host", "transform", "matrix4", ("unit",), {"matrix4": [
                        [20, 0, 0, 0], [0, 10, 0, 0], [0, 0, 10, 0], [0, 0, 0, 1]]}),
                    GeometryNode("joined", "composition", "attach", ("host", "roof"), {
                        "host_face": "top", "guest_extent": [.48, .82, .82], "engagement": .1})]
                result = compile_geometry_program(program(nodes))
                if accepted:
                    self.assertEqual(result.status, "compiled", result.issues)
                else:
                    self.assertIn("surface_sampling_requires_prior_sizing", {i.code for i in result.issues})

    def test_post_surface_warp_with_unproven_sampling_is_refused(self):
        nodes = base_nodes((2, 1, 1)) + [surface_node(),
            GeometryNode("widen", "modifier", "taper", ("roof",), {
                "axis": "z", "start_scale": [1, 1], "end_scale": [4, 4]})]
        result = compile_geometry_program(program(nodes))
        self.assertIn("surface_sampling_unsupported_transform", {i.code for i in result.issues})

    def test_constant_taper_uses_affine_sampling_proof(self):
        for scale, accepted in [(4, False), (.5, True)]:
            nodes = base_nodes((2, 1, 1)) + [surface_node(),
                GeometryNode("taper", "modifier", "taper", ("roof",), {
                    "axis": "z", "start_scale": [scale, scale], "end_scale": [scale, scale]})]
            result = compile_geometry_program(program(nodes))
            if accepted:
                self.assertEqual(result.status, "compiled", result.issues)
            else:
                self.assertIn("surface_sampling_requires_prior_sizing", {i.code for i in result.issues})

    def test_invalid_or_inverted_surface_payload_fails_before_execution(self):
        cases = [
            {},
            {"top_surface": {"type": "unknown"}},
            {"top_surface": {"type": "constant", "height": 1.2}},
            {"top_surface": {"type": "polynomial", "terms": [[-1, 0, 1]]}},
            {"top_surface": {"type": "constant", "height": .2}, "bottom_surface": {"type": "constant", "height": .3}},
            {"top_surface": DOME, "unsupported_option": True},
        ]
        for parameters in cases:
            with self.subTest(parameters=parameters):
                result = compile_geometry_program(program(base_nodes() + [replace(surface_node(), parameters=parameters)]))
                self.assertEqual(result.status, "invalid_program")
                self.assertIn("invalid_surface_bounds", {i.code for i in result.issues})
