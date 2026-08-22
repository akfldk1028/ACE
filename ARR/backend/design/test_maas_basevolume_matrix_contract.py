from dataclasses import replace

from django.test import SimpleTestCase

from design.maas.geometry_language.base_seeds import (
    BASE_FORM_SPECS,
    base_form_program,
    base_seed_program,
)
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.ast import GeometryNode
from design.maas.geometry_language.legal_field_affine_placement import (
    _source_floor_sections,
)
from design.maas.geometry_language.affine_normalization import (
    normalize_affine_basevolume_program,
)
from design.maas.geometry_language.llm_adapter import (
    GeometryAuthorError,
    geometry_programs_from_author_payload,
)
from design.maas.book_language.agent_authored_supply import _paid_parser_item
from design.maas.geometry_language.book_adapter import (
    apply_book_projection_to_geometry_program,
)
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.program_massing import compose_program_with_book_operations


class BaseVolumeMatrixContractTests(SimpleTestCase):
    def test_normalized_source_export_does_not_apply_a_site_fit(self):
        from design.maas.geometry_language.source_bridge import (
            compile_normalized_geometry_program_to_source_mass,
        )

        program = base_form_program("elliptical")
        compilation = compile_geometry_program(program)
        source = compile_normalized_geometry_program_to_source_mass(
            program,
            max_volume_bands=4,
        )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(bridge["geometry_hash"], compilation.geometry_hash)
        self.assertEqual(
            bridge["host_fit_matrix4"],
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        )
        self.assertEqual(bridge["legal_fit_mode"], "normalized_authored_identity")
        self.assertFalse(bridge["parcel_coordinates_in_program"])

    def test_normalized_source_export_normalizes_height_without_plan_reflow(self):
        from design.maas.geometry_language.source_bridge import (
            compile_normalized_geometry_program_to_source_mass,
        )

        program = base_form_program("cube")
        matrix_node = next(
            node for node in program.nodes if node.operator == "matrix4"
        )
        matrix = [list(row) for row in matrix_node.parameters["matrix4"]]
        matrix[2][2] = 0.25
        shortened = replace(
            program,
            nodes=tuple(
                replace(
                    node,
                    parameters={**node.parameters, "matrix4": matrix},
                )
                if node.id == matrix_node.id
                else node
                for node in program.nodes
            ),
        )

        source = compile_normalized_geometry_program_to_source_mass(
            shortened,
            max_volume_bands=4,
        )

        self.assertIsNotNone(source)
        assert source is not None
        exported_matrix = source.metadata["geometry_program_bridge_evidence"][
            "host_fit_matrix4"
        ]
        self.assertEqual(
            [row[:2] for row in exported_matrix[:2]],
            [[1.0, 0.0], [0.0, 1.0]],
        )
        self.assertEqual(exported_matrix[0][3], 0.0)
        self.assertEqual(exported_matrix[1][3], 0.0)
        self.assertAlmostEqual(exported_matrix[2][2], 4.0)

    def test_normalized_voided_form_export_is_not_a_site_containment_gate(self):
        from design.maas.geometry_language.source_bridge import (
            compile_normalized_geometry_program_to_source_mass,
        )

        program = base_form_program("elliptical")
        void = GeometryNode(
            id="open_court",
            kind="macro",
            operator="carve_void",
            inputs=(program.root_id,),
            parameters={"margin_ratio": 0.4, "open_side": "west"},
            semantic_role="public_threshold",
        )
        authored_nodes = tuple(
            replace(node, parameters={"segments": 28})
            if node.operator == "ellipsoidize"
            else replace(node, parameters={
                **node.parameters,
                "matrix4": [
                    [1.08, 0.0, 0.0, 0.0],
                    [0.0, 0.96, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
            })
            if node.operator == "matrix4"
            else node
            for node in program.nodes
        )
        voided = replace(
            program,
            nodes=(*authored_nodes, void),
            root_id=void.id,
        )

        source = compile_normalized_geometry_program_to_source_mass(
            voided,
            max_volume_bands=4,
        )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(bridge["legal_fit_mode"], "normalized_authored_identity")
        self.assertFalse(bridge["parcel_coordinates_in_program"])

    def test_taper_preserves_authored_lower_fraction_before_continuous_recession(self):
        program = base_form_program("cube")
        taper = GeometryNode(
            id="shouldered_taper",
            kind="modifier",
            operator="taper",
            inputs=(program.root_id,),
            parameters={
                "axis": "z",
                "start_scale": [1.0, 1.0],
                "end_scale": [1.0, 0.5],
                "lower_floor_fraction": 0.5,
                "subdivisions": 6,
            },
            semantic_role="continuous_section",
        )
        program = replace(
            program,
            nodes=(*program.nodes, taper),
            root_id=taper.id,
        )
        compilation = compile_geometry_program(program)
        self.assertEqual(compilation.status, "compiled", compilation.issues)
        sections = _source_floor_sections(compilation, floor_count=4)
        self.assertIsNotNone(sections)
        areas = [float(section.area) for section in sections]
        self.assertAlmostEqual(areas[0], areas[1], places=5)
        self.assertGreater(areas[1], areas[2])
        self.assertGreater(areas[2], areas[3])

    def test_author_payload_binds_declared_base_form_to_executable_ancestry(self):
        elliptical = base_form_program("elliptical").to_dict()
        valid = _paid_parser_item(elliptical)
        valid["base_form_id"] = "elliptical"

        parsed = geometry_programs_from_author_payload(
            {"programs": [valid]}, expected_count=1
        )[0]
        self.assertEqual(parsed.metadata["base_form_id"], "elliptical")

        invalid = dict(valid)
        invalid["base_form_id"] = "cube"
        with self.assertRaisesMessage(
            GeometryAuthorError,
            "declared_base_form_cube_does_not_match_elliptical",
        ):
            geometry_programs_from_author_payload(
                {"programs": [invalid]}, expected_count=1
            )

    def test_cube_base_form_survives_an_explicit_bar_seed_scale(self):
        base = base_form_program("cube")
        unit, matrix = base.nodes
        seed = GeometryNode(
            "seed_bar",
            "transform",
            "scale",
            inputs=(unit.id,),
            parameters={
                "scale": (2.8, 0.62, 0.48),
                "pivot": (0.0, 0.0, 0.0),
            },
            semantic_role="base_seed",
        )
        program = replace(
            base,
            nodes=(unit, seed, replace(matrix, inputs=(seed.id,))),
        )
        raw = _paid_parser_item(program.to_dict())
        raw["base_form_id"] = "cube"
        raw["base_seed"] = "bar"

        parsed = geometry_programs_from_author_payload(
            {"programs": [raw]}, expected_count=1
        )[0]

        self.assertEqual(parsed.metadata["base_form_id"], "cube")
        self.assertEqual(parsed.metadata["base_seed"], "bar")

    def test_affine_normalization_preserves_form_before_global_matrix(self):
        for form_id in ("elliptical", "tetrahedral"):
            with self.subTest(base_form=form_id):
                normalized = normalize_affine_basevolume_program(
                    base_form_program(form_id)
                )
                ordered = normalized.topological_nodes()
                matrices = [node for node in ordered if node.operator == "matrix4"]
                form = next(
                    node for node in ordered
                    if node.operator in {"ellipsoidize", "tetrahedralize"}
                )
                self.assertEqual(len(matrices), 1)
                self.assertLess(ordered.index(form), ordered.index(matrices[0]))
                self.assertEqual(matrices[0].inputs, (form.id,))

    def test_book_projection_preserves_form_matrix_scope_operation_order(self):
        sequence = compose_program_with_book_operations(
            VerbSequence(
                "base_form_source",
                "Base Form Source",
                (VerbCall("base", {}),),
                (),
            ),
            (VerbCall("inflate", {}),),
            base_volume_label="1/4",
            orientation="short_axis",
        )
        projected = apply_book_projection_to_geometry_program(
            base_form_program("elliptical"), sequence
        )
        ordered = projected.topological_nodes()
        operators = [node.operator for node in ordered]

        self.assertLess(operators.index("box"), operators.index("ellipsoidize"))
        self.assertLess(operators.index("ellipsoidize"), operators.index("matrix4"))
        self.assertLess(operators.index("matrix4"), operators.index("book_base_volume"))
        self.assertLess(operators.index("book_base_volume"), operators.index("inflate"))
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled", compilation.issues)

    def test_author_parser_rejects_unknown_operator_parameters(self):
        program = base_form_program("cube").to_dict()
        program["nodes"].append({
            "id": "bad_taper",
            "kind": "modifier",
            "operator": "taper",
            "inputs": [program["root_id"]],
            "parameters": {
                "axis": "z",
                "start": [1.0, 1.0],
                "end": [0.6, 0.7],
                "subdivisions": 6,
            },
            "semantic_role": "body",
        })
        program["root_id"] = "bad_taper"
        raw = _paid_parser_item(program)
        raw["base_form_id"] = "cube"

        with self.assertRaisesMessage(
            GeometryAuthorError,
            "unknown_author_parameter:taper.end",
        ):
            geometry_programs_from_author_payload(
                {"programs": [raw]}, expected_count=1
            )

    def test_author_parser_rejects_parameter_values_outside_contract(self):
        program = base_form_program("cube").to_dict()
        program["nodes"].append({
            "id": "bad_notch",
            "kind": "macro",
            "operator": "notch",
            "inputs": [program["root_id"]],
            "parameters": {
                "side": "west",
                "ratio": 0.022,
                "width_ratio": 0.15,
                "height_ratio": 0.14,
            },
            "semantic_role": "public_threshold",
        })
        program["root_id"] = "bad_notch"
        raw = _paid_parser_item(program)
        raw["base_form_id"] = "cube"

        with self.assertRaisesMessage(
            GeometryAuthorError,
            "author_parameter_below_minimum:notch.ratio",
        ):
            geometry_programs_from_author_payload(
                {"programs": [raw]}, expected_count=1
            )

    def test_author_parser_rejects_feedback_forbidden_body_family(self):
        program = base_form_program("cube").to_dict()
        program["nodes"].append({
            "id": "repeated_step",
            "kind": "macro",
            "operator": "setback",
            "inputs": [program["root_id"]],
            "parameters": {
                "levels": 3,
                "setback_ratio": 0.12,
                "direction": "x",
                "shift_per_level": [0.02, 0.0, 0.0],
            },
            "semantic_role": "body",
        })
        program["root_id"] = "repeated_step"
        raw = _paid_parser_item(program)
        raw["base_form_id"] = "cube"

        with self.assertRaisesMessage(
            GeometryAuthorError,
            "author_body_rule_family_forbidden:step",
        ):
            geometry_programs_from_author_payload(
                {"programs": [raw]},
                expected_count=1,
                program_context={
                    "author_forbidden_body_rule_families": ["step"],
                },
            )

    def test_author_parser_rejects_feedback_forbidden_operator(self):
        program = base_form_program("cube").to_dict()
        program["nodes"].append({
            "id": "repeated_taper",
            "kind": "modifier",
            "operator": "taper",
            "inputs": [program["root_id"]],
            "parameters": {
                "axis": "z",
                "start_scale": [1.0, 1.0],
                "end_scale": [0.75, 0.75],
                "subdivisions": 6,
            },
            "semantic_role": "body",
        })
        program["root_id"] = "repeated_taper"
        raw = _paid_parser_item(program)
        raw["base_form_id"] = "cube"

        with self.assertRaisesMessage(
            GeometryAuthorError,
            "author_operator_forbidden:taper",
        ):
            geometry_programs_from_author_payload(
                {"programs": [raw]},
                expected_count=1,
                program_context={"author_forbidden_operators": ["taper"]},
            )

    def test_base_form_catalog_lowers_from_unitbox_before_one_global_matrix(self):
        measured_volumes = {}
        for spec in BASE_FORM_SPECS:
            with self.subTest(base_form=spec.form_id):
                program = base_form_program(spec.form_id)
                ordered = program.topological_nodes()
                unitboxes = [
                    node for node in ordered
                    if node.operator == "box"
                    and node.parameters == {
                        "width": 1.0,
                        "depth": 1.0,
                        "height": 1.0,
                    }
                ]
                matrices = [node for node in ordered if node.operator == "matrix4"]
                self.assertEqual(len(unitboxes), 1)
                self.assertEqual(len(matrices), 1)
                self.assertLess(ordered.index(unitboxes[0]), ordered.index(matrices[0]))
                if spec.operator:
                    form_node = next(
                        node for node in ordered if node.operator == spec.operator
                    )
                    self.assertLess(ordered.index(form_node), ordered.index(matrices[0]))
                    self.assertEqual(form_node.inputs, (unitboxes[0].id,))
                    self.assertEqual(matrices[0].inputs, (form_node.id,))
                else:
                    self.assertEqual(matrices[0].inputs, (unitboxes[0].id,))

                compilation = compile_geometry_program(program)
                self.assertEqual(compilation.status, "compiled", compilation.issues)
                self.assertEqual(compilation.metrics["component_count"], 1)
                self.assertTrue(compilation.metrics["watertight"])
                self.assertTrue(compilation.metrics["manifold"])
                measured_volumes[spec.form_id] = compilation.metrics["volume"]

        self.assertAlmostEqual(measured_volumes["cube"], 1.0, places=6)
        self.assertLess(measured_volumes["elliptical"], measured_volumes["cube"])
        self.assertLess(measured_volumes["tetrahedral"], measured_volumes["elliptical"])

    def test_affine_seeds_persist_explicit_matrix4(self):
        for seed_id in ("block", "slab", "bar", "tower"):
            with self.subTest(seed_id=seed_id):
                program = base_seed_program(seed_id)
                primitive_nodes = [
                    node for node in program.nodes
                    if node.kind == "primitive"
                ]
                matrix_nodes = [
                    node for node in program.nodes
                    if node.operator == "matrix4"
                ]

                self.assertEqual(len(primitive_nodes), 1)
                self.assertEqual(primitive_nodes[0].operator, "box")
                self.assertEqual(len(matrix_nodes), 1)
                self.assertEqual(
                    matrix_nodes[0].parameters["matrix4"][3],
                    [0.0, 0.0, 0.0, 1.0],
                )
                self.assertEqual(program.root_id, matrix_nodes[0].id)
                self.assertEqual(
                    program.metadata["canonical_root"],
                    "1/1 UnitBox",
                )
                self.assertEqual(
                    program.metadata["basevolume_affine_authority"],
                    "explicit_matrix4",
                )

                compilation = compile_geometry_program(program)
                self.assertEqual(
                    compilation.status,
                    "compiled",
                    compilation.issues,
                )
                self.assertEqual(compilation.metrics["component_count"], 1)
