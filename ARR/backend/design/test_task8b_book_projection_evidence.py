import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from design.maas.geometry_language import GeometryProgramBuilder


def _box_program():
    builder = GeometryProgramBuilder("task8b_box")
    root = builder.add(
        "primitive",
        "box",
        parameters={"width": 12.0, "depth": 8.0, "height": 15.0},
        semantic_role="base_seed",
    )
    return builder.build(root)


class Task8BBookProjectionEvidenceTests(TestCase):
    def test_source_role_binding_return_becomes_actual_post_book_program(self):
        from design.maas.book_language.candidate_generation import (
            _bind_book_program_source_role,
        )

        post_book = _box_program()
        bound = object()
        source = object()
        with patch(
            "design.maas.book_language.candidate_generation."
            "bind_source_role_scaffold_to_program",
            return_value=bound,
        ) as binder:
            actual = _bind_book_program_source_role(
                post_book,
                source,
                program_id="neighborhood_living",
            )

        self.assertIs(actual, bound)
        binder.assert_called_once_with(
            post_book,
            source,
            program_id="neighborhood_living",
        )

    def test_book_value_error_retains_typed_failure_evidence(self):
        from design.maas.geometry_language import book_adapter

        program = _box_program()
        calls = (SimpleNamespace(verb="overlap"),)
        scope = SimpleNamespace(label="1/2", requested_fraction=0.5)
        with (
            patch.object(book_adapter, "book_projection_calls", return_value=calls),
            patch.object(book_adapter, "book_projection_scope", return_value=scope),
            patch.object(
                book_adapter,
                "_apply_book_projection_to_geometry_program",
                side_effect=ValueError(
                    "incompatible_book_effect_stack:overlap:protected_split_wing"
                ),
            ),
        ):
            with self.assertRaises(book_adapter.BookProjectionFailure) as raised:
                book_adapter.apply_book_projection_to_geometry_program(
                    program,
                    SimpleNamespace(),
                )

        evidence = raised.exception.evidence
        self.assertEqual(evidence["code"], "incompatible_book_effect_stack")
        self.assertEqual(evidence["scope"]["label"], "1/2")
        self.assertEqual(evidence["verbs"], ["overlap"])
        self.assertIn("chassis", evidence)
        self.assertIn("effect", evidence)
        self.assertEqual(
            evidence["pre_identity"]["program_hash"],
            program.program_hash(),
        )
        self.assertEqual(evidence["post_identity"]["status"], "not_materialized")

    def test_summary_writer_escapes_literal_newlines_as_strict_json(self):
        from design.maas.book_language.portfolio_benchmark import (
            persist_book_program_summary,
        )

        result = {
            "floor_capacity_plan": {
                "derivation": "line one\nline two",
            },
        }
        with TemporaryDirectory() as directory:
            path = persist_book_program_summary(Path(directory), result)
            parsed = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(parsed, result)

