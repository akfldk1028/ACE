import json

from django.test import SimpleTestCase

from design.maas.geometry_language.base_seeds import base_form_program
from design.maas.geometry_language.llm_adapter import _author_node_schema
from design.maas.geometry_language.llm_adapter import (
    geometry_programs_from_author_payload,
)
from design.maas.book_language.agent_authored_supply import _paid_parser_item


class AuthorOutputSchemaTests(SimpleTestCase):
    def test_box_variant_only_offers_unitbox_parameter_names(self):
        schema = _author_node_schema(["box"])

        self.assertEqual(len(schema["anyOf"]), 1)
        box_variant = schema["anyOf"][0]
        parameter_names = sorted(
            item["properties"]["name"]["enum"][0]
            for item in box_variant["properties"]["parameters"]["items"][
                "anyOf"
            ]
        )

        self.assertEqual(
            parameter_names,
            ["center", "depth", "height", "width"],
        )
        self.assertEqual(
            box_variant["properties"]["parameters"]["minItems"],
            4,
        )
        center = next(
            item for item in box_variant["properties"]["parameters"]["items"][
                "anyOf"
            ]
            if item["properties"]["name"]["enum"] == ["center"]
        )
        self.assertEqual(
            center["properties"]["boolean_value"],
            {"type": "boolean", "enum": [True]},
        )
        self.assertNotIn("size", parameter_names)

    def test_parameterless_operator_forbids_parameter_items(self):
        schema = _author_node_schema(["tetrahedralize"])

        self.assertEqual(len(schema["anyOf"]), 1)
        parameters = schema["anyOf"][0]["properties"]["parameters"]

        self.assertEqual(parameters["maxItems"], 0)

    def test_book_scope_variant_offers_executable_book_parameters(self):
        schema = _author_node_schema(["book_base_volume"])

        parameters = schema["anyOf"][0]["properties"]["parameters"]
        parameter_variants = parameters["items"]["anyOf"]
        parameter_names = sorted(
            item["properties"]["name"]["enum"][0]
            for item in parameter_variants
        )

        self.assertEqual(parameter_names, ["label", "orientation"])
        self.assertEqual(parameters["minItems"], 2)
        self.assertEqual(parameters["maxItems"], 2)

        label = next(
            item for item in parameter_variants
            if item["properties"]["name"]["enum"] == ["label"]
        )
        self.assertEqual(label["properties"]["value_type"]["enum"], ["string"])
        self.assertEqual(
            set(label["properties"]["string_value"]["enum"]),
            {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"},
        )

    def test_matrix4_uses_a_real_four_by_four_array_not_a_json_string(self):
        schema = _author_node_schema(["matrix4"])

        parameter = schema["anyOf"][0]["properties"]["parameters"]["items"][
            "anyOf"
        ][0]
        self.assertEqual(
            schema["anyOf"][0]["properties"]["parameters"]["minItems"],
            1,
        )
        self.assertEqual(
            parameter["required"],
            ["name", "value_type", "matrix4_value"],
        )
        self.assertEqual(parameter["properties"]["value_type"]["enum"], ["matrix4"])
        self.assertNotIn("numeric_value", parameter["properties"])
        matrix = parameter["properties"]["matrix4_value"]
        self.assertEqual(matrix["minItems"], 4)
        self.assertEqual(matrix["maxItems"], 4)
        self.assertEqual(matrix["items"]["minItems"], 4)
        self.assertEqual(matrix["items"]["maxItems"], 4)

    def test_author_parser_accepts_typed_matrix4_array(self):
        item = _paid_parser_item(base_form_program("cube").to_dict())
        matrix_parameter = next(
            parameter
            for node in item["nodes"]
            if node["operator"] == "matrix4"
            for parameter in node["parameters"]
            if parameter["name"] == "matrix4"
        )
        matrix_value = json.loads(matrix_parameter.pop("structured_json"))
        matrix_parameter["value_type"] = "matrix4"
        matrix_parameter["matrix4_value"] = matrix_value

        programs = geometry_programs_from_author_payload(
            {"programs": [item]},
            expected_count=1,
        )

        self.assertEqual(len(programs), 1)

    def test_lift_access_side_is_a_bounded_string_contract(self):
        schema = _author_node_schema(["lift"])
        variants = schema["anyOf"][0]["properties"]["parameters"]["items"][
            "anyOf"
        ]
        access_side = next(
            item for item in variants
            if item["properties"]["name"]["enum"] == ["access_side"]
        )

        self.assertEqual(access_side["properties"]["value_type"]["enum"], ["string"])
        self.assertIn("west", access_side["properties"]["string_value"]["enum"])
        self.assertEqual(
            schema["anyOf"][0]["properties"]["parameters"]["minItems"],
            1,
        )

    def test_split_wing_access_side_is_a_bounded_string_contract(self):
        schema = _author_node_schema(["split_wing"])
        variants = schema["anyOf"][0]["properties"]["parameters"]["items"][
            "anyOf"
        ]
        access_side = next(
            item for item in variants
            if item["properties"]["name"]["enum"] == ["access_side"]
        )

        self.assertEqual(access_side["properties"]["value_type"]["enum"], ["string"])
        self.assertEqual(
            set(access_side["properties"]["string_value"]["enum"]),
            {"closed", "east", "west", "north", "south"},
        )

    def test_cut_corner_requires_corner_and_size_for_external_identity(self):
        schema = _author_node_schema(["cut_corner"])

        parameters = schema["anyOf"][0]["properties"]["parameters"]

        self.assertEqual(parameters["minItems"], 2)
