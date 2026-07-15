"""Regression contracts for the recursive solid geometry language."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.geometry_language import (
    GeometryEdit,
    GeometryProgramBuilder,
    apply_geometry_edits,
    architectural_shape_programs,
    compilation_gate,
    compile_geometry_program,
    geometry_equivalent,
    geometry_programs_from_author_payload,
    l_mass_difference_program,
    parse_geometry_dsl,
    program_cost,
    reference_language_programs,
    run_geometry_program_a2a_loop,
)


class MaasGeometryLanguageTest(SimpleTestCase):
    def test_eighteen_architectural_families_compile_to_distinct_gated_solids(self):
        programs = architectural_shape_programs()
        self.assertEqual(len(programs), 18)
        compilations = [compile_geometry_program(program) for program in programs]

        self.assertTrue(all(result.status == "compiled" for result in compilations))
        self.assertTrue(all(not compilation_gate(result) for result in compilations))
        self.assertEqual(len({program.program_hash() for program in programs}), 18)
        self.assertEqual(len({result.geometry_hash for result in compilations}), 18)
        self.assertTrue(all(int(result.metrics["component_count"]) <= 5 for result in compilations))
        operators = {node.operator for program in programs for node in program.nodes}
        self.assertTrue({
            "bend", "radial_array", "courtyard", "notch", "setback", "tapered_tower",
            "leaning_tower", "slice", "cut_corner", "loft", "sweep", "split_wing", "twist",
        }.issubset(operators))
        expansions = {operation for result in compilations for row in result.trace for operation in row["macro_expansion"]}
        self.assertTrue({"difference", "shear"}.issubset(expansions))

    def test_three_photo_languages_are_transferable_programs_not_coordinate_templates(self):
        references = reference_language_programs()
        self.assertEqual(len(references), 3)
        for program in references.values():
            result = compile_geometry_program(program)
            self.assertEqual(result.status, "compiled", result.issues)
            self.assertFalse(compilation_gate(result))
            self.assertNotIn("parcel", str(program.to_dict()).lower())
            self.assertNotIn("pnu", str(program.to_dict()).lower())

    def test_l_mass_canonicalizer_prefers_short_union_but_recognizes_difference_equivalence(self):
        union_program = architectural_shape_programs()[2]
        difference_program = l_mass_difference_program()
        union_result = compile_geometry_program(union_program)
        difference_result = compile_geometry_program(difference_program)

        self.assertTrue(geometry_equivalent(union_result, difference_result))
        self.assertLess(program_cost(union_program, union_result).total, program_cost(difference_program, difference_result).total)

    def test_modifier_order_is_semantic_and_not_flattened(self):
        before = GeometryProgramBuilder("bend_after_carve")
        base = before.add("primitive", "box", parameters={"width": 14, "depth": 4, "height": 4})
        cutter = before.add("primitive", "box", parameters={"width": 4, "depth": 6, "height": 2})
        moved = before.add("transform", "translate", inputs=(cutter,), parameters={"vector": [5, -1, 2]})
        carved = before.add("boolean", "difference", inputs=(base, moved))
        bent_after = before.add("modifier", "bend", inputs=(carved,), parameters={"axis": "x", "angle_degrees": 38, "subdivisions": 4})

        after = GeometryProgramBuilder("carve_after_bend")
        base2 = after.add("primitive", "box", parameters={"width": 14, "depth": 4, "height": 4})
        bent = after.add("modifier", "bend", inputs=(base2,), parameters={"axis": "x", "angle_degrees": 38, "subdivisions": 4})
        cutter2 = after.add("primitive", "box", parameters={"width": 4, "depth": 6, "height": 2})
        moved2 = after.add("transform", "translate", inputs=(cutter2,), parameters={"vector": [5, -1, 2]})
        carved_after = after.add("boolean", "difference", inputs=(bent, moved2))

        first = compile_geometry_program(before.build(bent_after))
        second = compile_geometry_program(after.build(carved_after))
        self.assertEqual(first.status, "compiled")
        self.assertEqual(second.status, "compiled")
        self.assertFalse(geometry_equivalent(first, second))

    def test_text_dsl_reassignment_normalizes_to_acyclic_ssa_and_compiles(self):
        program = parse_geometry_dsl("""
            mass main = box(10, 8, 4)
            mass void = box(4, 4, 5)
            void = move(void, 0, 0, 0.5)
            mass courtyard = subtract(main, void)
            mass tower = box(3, 3, 10)
            tower = taper(tower, axis="z", endScale=[0.5, 0.5])
            tower = shear(tower, axis="x", amount=0.2)
            mass result = union(courtyard, tower)
        """)
        self.assertEqual(program.root_id, "result")
        self.assertIn("void__2", program.node_map)
        self.assertIn("tower__3", program.node_map)
        self.assertFalse([issue for issue in program.validate() if issue.severity == "error"])
        self.assertEqual(compile_geometry_program(program).status, "compiled")

    def test_typed_critic_edit_must_change_both_program_and_compiled_geometry(self):
        program = parse_geometry_dsl("mass result = box(10, 8, 6)")
        parent = compile_geometry_program(program)
        mutation = apply_geometry_edits(program, (
            GeometryEdit("add_node", node_id="critic_taper", node_kind="modifier", operator="taper", input_ids=(program.root_id,)),
            GeometryEdit("set_parameter", target_node_id="critic_taper", parameter_name="end_scale", vector_value=(0.48, 0.66)),
            GeometryEdit("set_parameter", target_node_id="critic_taper", parameter_name="subdivisions", numeric_value=3),
            GeometryEdit("set_root", target_node_id="critic_taper"),
        ))
        self.assertEqual(mutation.status, "revised", mutation.issues)
        child = compile_geometry_program(mutation.program)
        self.assertNotEqual(program.program_hash(), mutation.program.program_hash())
        self.assertNotEqual(parent.geometry_hash, child.geometry_hash)
        self.assertFalse(compilation_gate(child))

    def test_llm_author_payload_becomes_valid_compilable_programs(self):
        programs = geometry_programs_from_author_payload({"programs": [
            {"name": "courtyard_author", "dsl": "mass base = box(12, 9, 5)\nmass result = courtyard(base, margin_ratio=0.28)", "rationale": "carved court"},
            {"name": "fan_author", "dsl": "mass bar = box(11, 2, 3)\nmass moved = move(bar, 0, -1, 0)\nmass result = radial_array(moved, count=5, total_angle_degrees=72)", "rationale": "radial field"},
        ]}, expected_count=2)
        self.assertEqual(len(programs), 2)
        self.assertEqual(len({program.program_hash() for program in programs}), 2)
        self.assertTrue(all(compile_geometry_program(program).status == "compiled" for program in programs))

    def test_closed_loop_recompiles_and_archives_vlm_ast_revision(self):
        original = parse_geometry_dsl("mass result = box(10, 8, 6)", name="author_box")

        def author(_context):
            return (original,)

        def critic(program, _compilation, _preview: Path):
            if program.root_id == "result":
                return {
                    "concept_scores": {"gesture_clarity": 0.35, "hierarchy": 0.55},
                    "critic_actions": ["too_box_like"],
                    "geometry_edits": [
                        {"operation": "add_node", "node_id": "critic_taper", "node_kind": "modifier", "operator": "taper", "input_ids": ["result"]},
                        {"operation": "set_parameter", "target_node_id": "critic_taper", "parameter_name": "end_scale", "vector_value": [0.48, 0.66]},
                        {"operation": "set_parameter", "target_node_id": "critic_taper", "parameter_name": "subdivisions", "numeric_value": 3},
                        {"operation": "set_root", "target_node_id": "critic_taper"},
                    ],
                }
            return {"concept_scores": {"gesture_clarity": 0.82, "hierarchy": 0.8}, "geometry_edits": []}

        with TemporaryDirectory() as directory:
            loop = run_geometry_program_a2a_loop(
                context={},
                target_count=2,
                author_programs=author,
                critic_program=critic,
                max_generations=2,
                preview_dir=directory,
                author_provider="deterministic_test",
                critic_provider="deterministic_test",
            )
        self.assertEqual(loop.trace["status"], "completed")
        self.assertEqual(loop.trace["geometry_revision_count"], 1)
        self.assertEqual(loop.trace["unique_geometry_count"], 2)
        self.assertFalse(loop.trace["vlm_geometry_critic_active"])
        self.assertTrue(loop.trace["critic_callback_active"])
        self.assertTrue(loop.trace["typed_ast_revision_active"])
