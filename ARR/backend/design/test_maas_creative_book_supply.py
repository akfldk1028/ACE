from __future__ import annotations

from collections import Counter

from django.test import SimpleTestCase

from design.maas.creative_book_supply import (
    creative_book_evidence,
    creative_book_schedule,
    project_creative_book_program,
)
from design.maas.geometry_language.affine_matrix import (
    matrix4_to_lists,
    scale_matrix4,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program


class CreativeBookSupplyTests(SimpleTestCase):
    def test_schedule_exhausts_30_20_9_before_repeating(self):
        schedule = creative_book_schedule(100)

        self.assertEqual(len(schedule), 100)
        self.assertEqual(
            len({item.principle_id for item in schedule[:59]}),
            59,
        )
        self.assertEqual(
            Counter(item.principle_kind for item in schedule[:59]),
            Counter({
                "base_operative": 30,
                "combination": 20,
                "aggregation": 9,
            }),
        )
        self.assertEqual(
            {item.scope_label for item in schedule},
            {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"},
        )
        self.assertEqual(
            schedule[59].principle_id,
            schedule[0].principle_id,
        )
        forbidden = ("qatar", "sanaa", "oma", "library", "museum")
        self.assertFalse(any(
            token in item.principle_id.lower()
            for item in schedule
            for token in forbidden
        ))

    def test_projection_materializes_scope_and_registry_lineage(self):
        unitbox = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
            semantic_role="base_authority",
        )
        basevolume = GeometryNode(
            "base_volume",
            "transform",
            "matrix4",
            inputs=(unitbox.id,),
            parameters={
                "matrix4": matrix4_to_lists(
                    scale_matrix4((3.4, 2.6, 4.2))
                ),
            },
            semantic_role="base_volume",
        )
        program = GeometryProgram(
            nodes=(unitbox, basevolume),
            root_id=basevolume.id,
            name="neutral_creative_basevolume",
        )
        assignment = creative_book_schedule(1)[0]

        projected = project_creative_book_program(program, assignment)
        evidence = creative_book_evidence(projected)
        compilation = compile_geometry_program(projected)

        self.assertEqual(compilation.status, "compiled")
        self.assertTrue(evidence["materialized"])
        self.assertEqual(evidence["principle_id"], assignment.principle_id)
        self.assertEqual(evidence["scope_label"], assignment.scope_label)
        self.assertTrue(evidence["selector_node_id"])
        self.assertTrue(evidence["projected_node_ids"])
        self.assertTrue(
            projected.metadata["book_recursive_projection"]["active"]
        )
        self.assertTrue(any(
            node.operator == "book_base_volume"
            for node in projected.topological_nodes()
        ))



class AuthorPromptRendersItsTemplateTests(SimpleTestCase):
    """The author prompt is an f-string template with a catalogue in it.

    A rule paragraph spliced in as `""" + text + """` closed the f-string, and
    everything after it - the operator catalogue among it - went out as the
    literal placeholder `{parameter_contracts}`. The prompt shrank from 161 KB
    to 21 KB and nothing noticed for an afternoon, because no test rendered it
    with a real context and read it back.
    """

    def test_prompt_has_no_unrendered_placeholders_and_carries_the_catalogue(self):
        import re
        from design.maas.book_language.candidate_generation import _book_graph_author_vocabulary
        from design.maas.geometry_language.llm_adapter import _author_prompt

        context = {
            "pnu": "4115011300106840001",
            "capacity_ceiling_m2": 1497.877,
            "creative_portfolio_run_id": "book-test",
            "book_graph_vocabulary": _book_graph_author_vocabulary(),
        }
        prompt = _author_prompt(context, 12)
        leftover = sorted(set(re.findall(r"\{[a-z_]+\}", prompt)))
        self.assertEqual(leftover, [], f"unrendered template fields: {leftover}")
        self.assertIn('"value_type": [', prompt, "the operator catalogue is missing")
        self.assertNotIn('"type": "literal"', prompt, "the catalogue leaks its internal kind word")
        self.assertIn("Some macros only fit some seeds", prompt, "the derived rules are missing")
        self.assertEqual(prompt.count("`base_seed` is checked against"), 1, "the seed rule must appear once")
