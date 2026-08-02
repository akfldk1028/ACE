"""Typed target3 anchor scheduling before exhaustive GeometryProgram probes."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import (
    candidate_generation,
    diagnostic_anchor_scheduler,
)
from design.maas.book_language.diagnostic_anchor_scheduler import (
    diagnostic_anchor_schedule_active,
    diagnostic_anchor_sentence_variants,
    diagnostic_anchor_spec,
    schedule_diagnostic_anchor_parents,
)
from design.maas.book_language.registry import build_book_language_registry
from design.maas.geometry_language import (
    GeometryProgram,
    apply_book_projection_to_geometry_program,
)
from design.maas.geometry_language.universal_form_bank import (
    universal_form_programs,
)
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import (
    book_sentence_variants,
    compose_program_with_book_operations,
    program_seed_sequences,
)


class DiagnosticAnchorSchedulerTests(SimpleTestCase):
    def _parents(self) -> tuple[VerbSequence, ...]:
        carrier = program_seed_sequences("gymnasium")[0]
        return tuple(
            VerbSequence(
                name=f"page-zero-parent-{index}",
                label=f"page-zero-parent-{index}",
                calls=carrier.calls,
                notes=(
                    *carrier.notes,
                    "geometry_program_payload="
                    + json.dumps(
                        program.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    f"geometry_program_source_seed=carrier-{index}",
                    "geometry_program_source=universal_form_bank",
                ),
            )
            for index, program in enumerate(universal_form_programs(0)[:36])
        )

    def test_target3_anchors_precede_every_original_parent(self):
        parents = self._parents()
        scheduled = schedule_diagnostic_anchor_parents(parents)

        self.assertEqual(len(scheduled), len(parents) + 3)
        self.assertEqual(scheduled[3:], parents)
        specs = tuple(diagnostic_anchor_spec(seed) for seed in scheduled[:3])
        self.assertEqual(
            [spec.body_family for spec in specs],
            ["prismatic", "stepped", "oblique"],
        )
        self.assertEqual(
            [spec.principle_id for spec in specs],
            [
                "book:operative:skew",
                "book:operative:expand",
                "book:operative:notch",
            ],
        )
        self.assertTrue(all(spec.scope_label == "1/1" for spec in specs))
        self.assertEqual(
            [spec.orientation for spec in specs],
            ["long_axis", "short_axis", "long_axis"],
        )
        self.assertEqual(
            [spec.variant_index for spec in specs],
            [5, 7, 5],
        )

        programs = []
        for seed in scheduled[:3]:
            payload = next(
                note.split("=", 1)[1]
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            )
            programs.append(GeometryProgram.from_dict(json.loads(payload)))
        self.assertEqual(
            (programs[0].metadata.get("base_seed") or {}).get("seed_id"),
            "bar",
        )
        self.assertIn(
            "stepped_mass",
            {node.operator for node in programs[1].nodes},
        )
        self.assertIn(
            "slice",
            {node.operator for node in programs[2].nodes},
        )
        self.assertEqual(programs[2].metadata.get("base_seed"), "slab")

    def test_scheduler_source_contains_no_pnu_or_frozen_program_hash(self):
        source = (
            Path(__file__).resolve().parent
            / "maas"
            / "book_language"
            / "diagnostic_anchor_scheduler.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("1168011800104170004", source)
        self.assertNotRegex(source, r"[0-9a-f]{64}")

    def test_anchor_schedule_is_target3_diagnostic_only(self):
        common = {
            "recursive_only": True,
            "evaluation_cap": 36,
            "parent_indices": (0,),
            "has_capacity_contract": True,
        }
        self.assertTrue(
            diagnostic_anchor_schedule_active(target_count=0, **common)
        )
        self.assertTrue(
            diagnostic_anchor_schedule_active(target_count=3, **common)
        )
        self.assertFalse(
            diagnostic_anchor_schedule_active(target_count=10, **common)
        )
        self.assertFalse(
            diagnostic_anchor_schedule_active(target_count=20, **common)
        )

    def test_only_typed_anchors_select_spatial_reserve_schedule_index(self):
        scheduled = schedule_diagnostic_anchor_parents(self._parents())
        resolver = getattr(
            diagnostic_anchor_scheduler,
            "diagnostic_anchor_capacity_schedule_index",
            None,
        )
        self.assertIsNotNone(resolver)

        self.assertEqual(
            [
                resolver(
                    seed,
                    default_index=index + 1,
                )
                for index, seed in enumerate(scheduled[:3])
            ],
            [0, 0, 0],
        )
        self.assertEqual(
            resolver(
                scheduled[3],
                default_index=11,
            ),
            11,
        )

    def test_anchor_executes_exact_master_lattice_parameters(self):
        scheduled = schedule_diagnostic_anchor_parents(self._parents())
        principles = {
            principle["principle_id"]: principle
            for principle in build_book_language_registry()["principles"]
        }
        for seed in scheduled[:3]:
            spec = diagnostic_anchor_spec(seed)
            execution_verbs = tuple(
                principles[spec.principle_id]["execution_verbs"]
            )
            actual = diagnostic_anchor_sentence_variants(
                seed,
                execution_verbs,
                default_count=1,
            )
            lattice = book_sentence_variants(
                execution_verbs,
                count=12,
            )
            self.assertEqual(actual, (lattice[spec.variant_index],))
        oblique_seed = scheduled[2]
        payload = next(
            note.split("=", 1)[1]
            for note in oblique_seed.notes
            if note.startswith("geometry_program_payload=")
        )
        oblique_program = GeometryProgram.from_dict(json.loads(payload))
        oblique_spec = diagnostic_anchor_spec(oblique_seed)
        notch = principles[oblique_spec.principle_id]
        operations = diagnostic_anchor_sentence_variants(
            oblique_seed,
            tuple(notch["execution_verbs"]),
            default_count=1,
        )[0]
        composed = compose_program_with_book_operations(
            oblique_seed,
            operations,
            name_suffix="notch",
            base_volume_label=oblique_spec.scope_label,
            orientation=oblique_spec.orientation,
        )
        projected = apply_book_projection_to_geometry_program(
            oblique_program,
            composed,
        )
        self.assertEqual(
            projected.program_hash(),
            "a83b159dca13a7bea98395be1474bb9b31f2c5f6fe3a5fb1362b88cf9f867d14",
        )
        stepped_seed = scheduled[1]
        stepped_payload = next(
            note.split("=", 1)[1]
            for note in stepped_seed.notes
            if note.startswith("geometry_program_payload=")
        )
        stepped_program = GeometryProgram.from_dict(json.loads(
            stepped_payload
        ))
        stepped_spec = diagnostic_anchor_spec(stepped_seed)
        self.assertEqual(
            stepped_spec.principle_id,
            "book:operative:expand",
        )
        self.assertEqual(stepped_spec.variant_index, 7)
        expand = principles[stepped_spec.principle_id]
        stepped_operations = diagnostic_anchor_sentence_variants(
            stepped_seed,
            tuple(expand["execution_verbs"]),
            default_count=1,
        )[0]
        stepped_lattice = book_sentence_variants(
            tuple(expand["execution_verbs"]),
            count=12,
        )
        self.assertEqual(stepped_operations, stepped_lattice[7])
        stepped_composed = compose_program_with_book_operations(
            stepped_seed,
            stepped_operations,
            name_suffix="expand",
            base_volume_label=stepped_spec.scope_label,
            orientation=stepped_spec.orientation,
        )
        stepped_projected = apply_book_projection_to_geometry_program(
            stepped_program,
            stepped_composed,
        )
        self.assertNotEqual(
            stepped_projected.program_hash(),
            stepped_program.program_hash(),
        )

    def test_target3_pool_consumes_typed_anchors_in_capacity_order(self):
        trace: list[dict] = []
        parents = self._parents()
        with (
            patch.object(
                candidate_generation,
                "_agent_mutated_seeds",
                return_value=parents,
            ),
            patch.object(
                candidate_generation,
                "program_seed_variants",
                side_effect=lambda seed, **_kwargs: (seed,),
            ),
            patch.object(
                candidate_generation,
                "capacity_contract_for_alternative",
                return_value={},
            ),
            patch.object(
                candidate_generation,
                "compile_sequence_to_source_mass",
                return_value=None,
            ),
        ):
            _pool, counts = candidate_generation._program_pool(
                box(0.0, 0.0, 20.0, 20.0),
                "gymnasium",
                14.0,
                4,
                recursive_only=True,
                parent_variant_indices=(0,),
                base_capacity_contract={
                    "minimum_utilization": 0.40,
                    "target_utilization": 0.70,
                },
                diagnostic_scope_labels=("1/1", "3/8", "1/2"),
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=36,
                diagnostic_candidate_cap=12,
                diagnostic_evaluation_trace_callback=trace.append,
            )

        self.assertEqual(counts["evaluated"], 36)
        self.assertEqual(
            [
                record["diagnostic_anchor_body_family"]
                for record in trace[:3]
            ],
            ["prismatic", "stepped", "oblique"],
        )
        self.assertEqual(
            [record["principle_id"] for record in trace[:3]],
            [
                "book:operative:skew",
                "book:operative:expand",
                "book:operative:notch",
            ],
        )
        self.assertEqual(
            [record["scope_label"] for record in trace[:3]],
            ["1/1", "1/1", "1/1"],
        )
        self.assertEqual(
            [
                record["capacity_alternative_id"]
                for record in trace[:3]
            ],
            ["spatial_reserve", "spatial_reserve", "spatial_reserve"],
        )
