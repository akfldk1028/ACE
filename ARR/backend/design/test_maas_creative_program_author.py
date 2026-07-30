from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.creative_floor_portfolio import (
    build_creative_floor_portfolio,
)
from design.maas.creative_program_author import (
    authored_programs_from_payload,
)
from design.maas.geometry_language.programs import GeometryProgramBuilder
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram


def _authored_unitbox_program():
    builder = GeometryProgramBuilder("llm_authored_unclassified_mass")
    body = builder.add(
        "primitive",
        "box",
        parameters={
            "width": 1.0,
            "depth": 0.72,
            "height": 1.35,
        },
        semantic_role="llm_authored_body",
    )
    return builder.build(
        body,
        author_provider="test_structured_llm",
        author_model="test-model",
        author_response_id="response-001",
        author_prompt_contract="typed_ast_test",
    )


class CreativeProgramAuthorTests(SimpleTestCase):
    def test_exact_geometry_program_document_is_a_replayable_author_payload(
        self,
    ):
        program = _authored_unitbox_program()

        try:
            authored = authored_programs_from_payload(
                program.to_dict(),
                expected_count=1,
            )
        except Exception as exc:
            self.fail(f"exact program replay payload was rejected: {exc}")

        self.assertEqual(len(authored), 1)
        self.assertEqual(
            authored[0].program.program_hash(),
            program.program_hash(),
        )

    def test_llm_box_dimensions_lower_to_one_unitbox_plus_matrix4(self):
        program = GeometryProgram(
            nodes=(GeometryNode(
                "authored_box",
                "primitive",
                "box",
                parameters={
                    "width": 2.8,
                    "depth": 0.62,
                    "height": 0.48,
                },
            ),),
            root_id="authored_box",
            name="raw_llm_box",
            metadata={"author_provider": "structured_llm"},
        )

        try:
            portfolio = build_creative_floor_portfolio(
                count=1,
                authored_programs=(program,),
            )
        except ValueError as exc:
            self.fail(f"LLM box was not normalized to UnitBox: {exc}")

        nodes = portfolio["candidates"][0]["geometry_program"]["nodes"]
        unitboxes = [
            node for node in nodes
            if node["kind"] == "primitive"
            and node["operator"] == "box"
            and node["parameters"]
            == {"width": 1.0, "depth": 1.0, "height": 1.0}
        ]
        matrix_nodes = [
            node for node in nodes
            if node["operator"] == "matrix4"
        ]
        self.assertEqual(len(unitboxes), 1)
        self.assertGreaterEqual(len(matrix_nodes), 2)

    def test_injected_authored_program_never_consults_recipe_registry(self):
        program = _authored_unitbox_program()

        with patch(
            "design.maas.creative_floor_portfolio."
            "balanced_family_schedule",
            side_effect=AssertionError(
                "authored programs must not schedule recipes"
            ),
        ), patch(
            "design.maas.creative_floor_portfolio."
            "registered_creative_recipes",
            side_effect=AssertionError(
                "authored programs must not load recipes"
            ),
        ):
            try:
                portfolio = build_creative_floor_portfolio(
                    count=1,
                    authored_programs=(program,),
                )
            except TypeError as exc:
                self.fail(f"authored program input is unavailable: {exc}")

        candidate = portfolio["candidates"][0]
        self.assertEqual(portfolio["author_mode"], "authored_programs")
        self.assertTrue(candidate["family"].startswith("morph-"))
        self.assertEqual(
            candidate["author_evidence"],
            {
                "schema_version": "arr.maas.creative_author_evidence.v1",
                "source_kind": "llm_authored_geometry_program",
                "provider": "test_structured_llm",
                "model": "test-model",
                "response_id": "response-001",
                "cache_hit": False,
                "prompt_contract": "typed_ast_test",
            },
        )
        self.assertEqual(
            candidate["lineage"]["stages"][0],
            "llm_authored_geometry_program",
        )
