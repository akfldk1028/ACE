"""Offline acceptance for the r8 PNU1 legal field after r9 supply repair."""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import LineString, box, mapping, shape

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_analysis import (
    _solid_morphology_metrics,
)
from design.maas.book_language.capacity_contract import (
    build_feasible_capacity_contract,
)
from design.maas.book_language.floor_capacity_plan import (
    allocate_floor_targets,
    derive_program_floor_capacity_plan,
)
from design.maas.book_language.downstream_hard_gate import (
    LegalGenerationContext,
)
from design.maas.book_language.legal_floor_field import (
    validate_legal_floor_field,
)
from design.maas.geometry_language.source_bridge import (
    compile_site_bound_geometry_program_to_source_mass,
)
from design.maas.geometry_language.base_seeds import base_seed_programs
from design.maas.geometry_language.universal_form_bank import (
    universal_form_programs,
)


_PNU = "1168011800104170004"
_SUMMARY = (
    Path(__file__).resolve().parents[3]
    / ".superpowers"
    / "sdd"
    / "2026-07-28-single-authority-legal-mass"
    / "artifacts"
    / "task5-pnu-probes-r8"
    / "20260728T193417732224Z-01-pnu-1168011800104170004"
    / "maas-book-programs-summary.json"
)


class R9FrozenFinalSolidAcceptanceTests(SimpleTestCase):
    maxDiff = None

    def test_diagnostic_capacity_supply_cycles_independently_of_genotype(self):
        scheduled = [
            candidate_generation._capacity_alternative_schedule_index(
                evaluation_index=index,
                diagnostic_evaluation_cap=36,
                genotype_schedule_index=99,
            )
            for index in range(36)
        ]
        self.assertEqual(scheduled, list(range(36)))
        self.assertEqual(
            [scheduled.count(index) for index in range(4)],
            [1, 1, 1, 1],
        )
        self.assertEqual(
            [
                sum(value % 4 == alternative for value in scheduled)
                for alternative in range(4)
            ],
            [9, 9, 9, 9],
        )
        self.assertEqual(
            candidate_generation._capacity_alternative_schedule_index(
                evaluation_index=7,
                diagnostic_evaluation_cap=0,
                genotype_schedule_index=99,
            ),
            99,
        )

    def test_page_zero_diagnostic_anchors_are_typed_book_programs(self):
        from design.maas.book_language.diagnostic_anchor_scheduler import (
            diagnostic_anchor_spec,
            schedule_diagnostic_anchor_parents,
        )
        from design.maas.geometry_language import GeometryProgram
        from design.maas.program_massing import program_seed_sequences
        from design.maas.grammar.verb_sequence import VerbSequence

        carrier = program_seed_sequences("gymnasium")[0]
        parents = tuple(
            VerbSequence(
                name=f"parent-{index}",
                label=f"parent-{index}",
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
            for index, program in enumerate(universal_form_programs(0)[:13])
        )
        supplied = schedule_diagnostic_anchor_parents(parents)

        self.assertEqual(supplied[3:], parents)
        specs = tuple(diagnostic_anchor_spec(seed) for seed in supplied[:3])
        self.assertEqual(
            [spec.body_family for spec in specs],
            ["prismatic", "stepped", "oblique"],
        )
        self.assertEqual(
            [spec.principle_id for spec in specs],
            [
                "book:operative:skew",
                "book:operative:carve",
                "book:operative:notch",
            ],
        )
        programs = tuple(
            GeometryProgram.from_dict(json.loads(next(
                note.split("=", 1)[1]
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            )))
            for seed in supplied[:3]
        )
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

    def test_page_zero_anchor_schedule_preserves_original_parent_order(self):
        from design.maas.grammar.verb_sequence import VerbSequence
        from design.maas.program_massing import program_seed_sequences

        carrier = program_seed_sequences("gymnasium")[0]
        parents = tuple(
            VerbSequence(
                name=f"diagnostic-parent-{index}",
                label=f"diagnostic-parent-{index}",
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

        def run_trace(base_contract):
            trace = []
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
                    12.0,
                    4,
                    recursive_only=True,
                    parent_variant_indices=(0,),
                    base_capacity_contract=base_contract,
                    diagnostic_scope_labels=("1/1", "3/8", "1/2"),
                    diagnostic_book_probe_count=1,
                    diagnostic_evaluation_cap=36,
                    diagnostic_candidate_cap=12,
                    diagnostic_evaluation_trace_callback=trace.append,
                )
            self.assertEqual(counts["evaluated"], 36)
            return trace

        baseline = run_trace(None)
        controlled = run_trace({
            "minimum_utilization": 0.40,
            "target_utilization": 0.70,
        })
        self.assertEqual(len(controlled), 36)
        self.assertEqual(
            len({record["genotype_hash"] for record in controlled}),
            36,
        )
        self.assertEqual(
            [
                (
                    record["diagnostic_anchor_body_family"],
                    record["principle_id"],
                    record["variant_index"],
                    record["scope_label"],
                    record["capacity_alternative_id"],
                )
                for record in controlled[:3]
            ],
            [
                (
                    "prismatic",
                    "book:operative:skew",
                    5,
                    "1/1",
                    "spatial_reserve",
                ),
                (
                    "stepped",
                    "book:operative:carve",
                    5,
                    "1/1",
                    "balanced_yield",
                ),
                (
                    "oblique",
                    "book:operative:notch",
                    5,
                    "1/1",
                    "brief_target",
                ),
            ],
        )
        self.assertTrue(all(
            controlled[index + 3]["genotype_hash"]
            == baseline[index]["genotype_hash"]
            for index in range(33)
        ))
        self.assertEqual(
            [
                sum(
                    record["capacity_alternative_id"] == alternative
                    for record in controlled
                )
                for alternative in (
                    "spatial_reserve",
                    "balanced_yield",
                    "brief_target",
                    "maximum_feasible",
                )
            ],
            [9, 9, 9, 9],
        )

    def test_book_skew_bar_control_rejects_shrinking_and_passes_contained_fields(
        self,
    ):
        from design.maas.book_language.registry import (
            build_book_language_registry,
        )
        from design.maas.geometry_language import (
            apply_book_projection_to_geometry_program,
        )
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.maas.program_massing import (
            book_sentence_variants,
            compose_program_with_book_operations,
            program_seed_sequences,
        )

        raw = next(
            program for program in base_seed_programs()
            if (program.metadata.get("base_seed") or {}).get("seed_id") == "bar"
        )
        skew = next(
            principle
            for principle in build_book_language_registry()["principles"]
            if principle["principle_id"] == "book:operative:skew"
        )
        operations = book_sentence_variants(
            tuple(skew["execution_verbs"]),
            count=1,
        )[0]
        sequence = compose_program_with_book_operations(
            program_seed_sequences("gymnasium")[0],
            operations,
            base_volume_label="1/1",
            orientation="long_axis",
        )
        authored = apply_book_projection_to_geometry_program(raw, sequence)
        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        records = {
            record["slug"]: record for record in saved["programs"]
            if record["slug"] in {"neighborhood", "cultural"}
        }
        for slug, utilization in (
            ("neighborhood", 0.70),
            ("cultural", 0.40),
        ):
            floor_plan = records[slug]["floor_capacity_plan"]
            legal_sections = tuple(
                shape(section)
                for section in floor_plan["legal_floor_sections"]
            )
            aggregate_target = (
                float(floor_plan["feasible_maximum_gfa_m2"])
                * utilization
            )
            floor_targets = tuple(allocate_floor_targets(
                [float(section.area) for section in legal_sections],
                aggregate_target,
            ))
            rejected = select_legal_field_affine_projection(
                authored,
                legal_sections=legal_sections,
                target_floor_areas_m2=floor_targets,
                floor_capacity_plan_hash=f"skew-shrinking-{slug}",
                aggregate_target_area_m2=aggregate_target,
                maximum_exact_candidates=4,
            )
            self.assertIsNone(rejected, slug)
            contained_sections = tuple(
                legal_sections[0] for _section in legal_sections
            )
            selected = select_legal_field_affine_projection(
                authored,
                legal_sections=contained_sections,
                target_floor_areas_m2=floor_targets,
                floor_capacity_plan_hash=f"skew-control-{slug}",
                aggregate_target_area_m2=aggregate_target,
                maximum_exact_candidates=4,
            )
            self.assertIsNotNone(selected, slug)
            assert selected is not None
            source = compile_site_bound_geometry_program_to_source_mass(
                selected.projection.program,
                contained_sections[0],
                name=f"skew-control-{slug}",
            )
            self.assertIsNotNone(source, slug)
            assert source is not None
            morphology = _solid_morphology_metrics(source)
            self.assertGreaterEqual(
                sum(selected.projection.achieved_floor_areas_m2) + 1e-7,
                aggregate_target * 0.995,
            )
            self.assertFalse(morphology["pyramidal_like"], (slug, morphology))
            self.assertTrue(
                selected.projection.certificate["all_sections_contained"],
            )
            self.assertTrue(selected.projection.certificate["manifold"])
            self.assertTrue(selected.projection.certificate["watertight"])

    def test_production_shaped_nonstepped_bar_outside_legal_field_fails_closed(self):
        from design.maas.book_language.registry import (
            build_book_language_registry,
        )
        from design.maas.geometry_language import (
            apply_book_projection_to_geometry_program,
            compile_geometry_program,
            project_program_requirements,
        )
        from design.maas.geometry_language.legal_field_affine_placement import (
            is_intentional_floorwise_stepped_program,
            select_legal_field_affine_projection,
        )
        from design.maas.program_massing import (
            book_sentence_variants,
            compose_program_with_book_operations,
            program_seed_sequences,
        )
        from design.maas.program_massing.semantic_carriers import (
            bind_source_role_scaffold_to_program,
        )
        from design.maas.source_geometry import (
            compile_sequence_to_source_mass,
        )

        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        record = next(
            item for item in saved["programs"]
            if item["slug"] == "neighborhood"
        )
        floor_plan = record["floor_capacity_plan"]
        legal_sections = tuple(
            shape(section)
            for section in floor_plan["legal_floor_sections"]
        )
        aggregate_target = (
            float(floor_plan["feasible_maximum_gfa_m2"]) * 0.70
        )
        floor_targets = tuple(allocate_floor_targets(
            [float(section.area) for section in legal_sections],
            aggregate_target,
        ))
        raw = next(
            program for program in base_seed_programs()
            if (program.metadata.get("base_seed") or {}).get("seed_id") == "bar"
        )
        skew = next(
            principle
            for principle in build_book_language_registry()["principles"]
            if principle["principle_id"] == "book:operative:skew"
        )
        carrier = program_seed_sequences(record["program"])[0]
        sequence = compose_program_with_book_operations(
            carrier,
            book_sentence_variants(
                tuple(skew["execution_verbs"]),
                count=1,
            )[0],
            base_volume_label="1/1",
            orientation="long_axis",
        )
        book = apply_book_projection_to_geometry_program(raw, sequence)
        required = project_program_requirements(
            book,
            building_type=record["program"],
            access_side="west",
        )
        scaffolded = bind_source_role_scaffold_to_program(
            required,
            compile_sequence_to_source_mass(
                legal_sections[0],
                carrier,
            ),
            program_id=record["program"],
        )
        required_compilation = compile_geometry_program(required)
        scaffolded_compilation = compile_geometry_program(scaffolded)
        self.assertNotEqual(required.program_hash(), scaffolded.program_hash())
        self.assertEqual(
            required_compilation.geometry_hash,
            scaffolded_compilation.geometry_hash,
        )
        self.assertFalse(
            is_intentional_floorwise_stepped_program(scaffolded)
        )
        selected = select_legal_field_affine_projection(
            scaffolded,
            legal_sections=legal_sections,
            target_floor_areas_m2=floor_targets,
            floor_capacity_plan_hash="production-shaped-bar-control",
            aggregate_target_area_m2=aggregate_target,
            maximum_exact_candidates=4,
        )
        self.assertIsNone(selected)

    def test_materialization_reuses_contained_legal_projection_and_hash_identity(self):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.maas.grammar.verb_sequence import VerbSequence
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        record = next(
            item for item in saved["programs"]
            if item["slug"] == "cultural"
        )
        floor_plan = record["floor_capacity_plan"]
        legal_sections = tuple(
            shape(section)
            for section in floor_plan["legal_floor_sections"]
        )
        contained_legal_sections = tuple(
            legal_sections[0]
            for _section in legal_sections
        )
        target = float(floor_plan["feasible_maximum_gfa_m2"]) * 0.40
        target_floor_areas = tuple(allocate_floor_targets(
            [float(section.area) for section in legal_sections],
            target,
        ))
        program = next(
            item for item in base_seed_programs()
            if (item.metadata.get("base_seed") or {}).get("seed_id") == "bar"
        )
        sequence = VerbSequence(
            "r9-legal-field-integration",
            "r9-legal-field-integration",
            (),
            ("geometry_program_directive=r9-legal-field-integration",),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="r9-legal-field",
            site=legal_sections[0],
        )
        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"r9-legal-field-integration": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                wraps=select_legal_field_affine_projection,
                create=True,
            ) as selector,
            patch.object(
                candidate_generation,
                "append_floorwise_legal_projection",
                side_effect=AssertionError("duplicate legal projection"),
                create=True,
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source("r9-legal-field-source"),
                sequence,
                containment_host=contained_legal_sections[0],
                upper_containment_host=contained_legal_sections[-1],
                floor_containment_hosts=contained_legal_sections,
                floor_capacity_plan_hash="r9-legal-field-capacity",
                target_floor_areas_m2=target_floor_areas,
                **semantic_context,
            )

        self.assertIsNotNone(materialized)
        self.assertEqual(selector.call_count, 1)
        assert materialized is not None
        placement = materialized.metadata["legal_field_affine_placement"]
        bridge = materialized.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            placement["projection_mode"],
            "authored_affine_preserved",
        )
        self.assertGreaterEqual(
            placement["achieved_aggregate_area_m2"],
            placement["aggregate_target_area_m2"] * 0.995,
        )
        self.assertEqual(
            materialized.metadata["final_program_hash"],
            bridge["program_hash"],
        )
        self.assertEqual(
            materialized.metadata["final_geometry_hash"],
            bridge["geometry_hash"],
        )

    def test_materialization_rejects_r9_bar_when_closed_band_exits_frozen_legal_field(self):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.maas.grammar.verb_sequence import VerbSequence
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        record = next(
            item for item in saved["programs"]
            if item["slug"] == "cultural"
        )
        floor_plan = record["floor_capacity_plan"]
        legal_sections = tuple(
            shape(section)
            for section in floor_plan["legal_floor_sections"]
        )
        target = float(floor_plan["feasible_maximum_gfa_m2"]) * 0.40
        target_floor_areas = tuple(allocate_floor_targets(
            [float(section.area) for section in legal_sections],
            target,
        ))
        program = next(
            item for item in base_seed_programs()
            if (item.metadata.get("base_seed") or {}).get("seed_id") == "bar"
        )
        sequence = VerbSequence(
            "r9-legal-field-closed-band-rejection",
            "r9-legal-field-closed-band-rejection",
            (),
            (
                "geometry_program_directive="
                "r9-legal-field-closed-band-rejection",
            ),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="r9-legal-field",
            site=legal_sections[0],
        )
        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={
                    "r9-legal-field-closed-band-rejection": program,
                },
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                wraps=select_legal_field_affine_projection,
                create=True,
            ) as selector,
            patch.object(
                candidate_generation,
                "build_program_semantic_carrier_evidence",
                side_effect=AssertionError(
                    "semantic projection must not run after legal rejection"
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source(
                    "r9-legal-field-rejected-source"
                ),
                sequence,
                containment_host=legal_sections[0],
                upper_containment_host=legal_sections[-1],
                floor_containment_hosts=legal_sections,
                floor_capacity_plan_hash="r9-legal-field-capacity",
                target_floor_areas_m2=target_floor_areas,
                **semantic_context,
            )

        self.assertIsNone(materialized)
        self.assertEqual(selector.call_count, 1)

    def test_materialization_fails_closed_when_legal_field_has_no_selection(self):
        from design.maas.grammar.verb_sequence import VerbSequence
        from design.test_task5_regression_fixtures import (
            canonical_gym_semantic_source,
        )

        program = next(iter(base_seed_programs()))
        host = box(-10.0, -10.0, 10.0, 10.0)
        sequence = VerbSequence(
            "r9-legal-field-fail-closed",
            "r9-legal-field-fail-closed",
            (),
            ("geometry_program_directive=r9-legal-field-fail-closed",),
        )
        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"r9-legal-field-fail-closed": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                return_value=None,
                create=True,
            ) as selector,
            patch.object(
                candidate_generation,
                "derive_host_fit_transform",
                side_effect=AssertionError("legacy ground fit fallback"),
                create=True,
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source("r9-fail-closed-source"),
                sequence,
                containment_host=host,
                floor_containment_hosts=(host,),
                floor_capacity_plan_hash="r9-fail-closed-capacity",
                target_floor_areas_m2=(100.0,),
                building_type="gymnasium",
            )

        self.assertIsNone(materialized)
        self.assertEqual(selector.call_count, 1)

    def test_aggregate_target_not_floor_vector_authors_affine_matrix(self):
        from design.maas.geometry_language.affine_matrix import (
            identity_matrix4,
        )
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )

        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        record = next(
            item for item in saved["programs"]
            if item["slug"] == "cultural"
        )
        floor_plan = record["floor_capacity_plan"]
        legal_sections = tuple(
            shape(section)
            for section in floor_plan["legal_floor_sections"]
        )
        aggregate_target = (
            float(floor_plan["feasible_maximum_gfa_m2"]) * 0.40
        )
        balanced = tuple(allocate_floor_targets(
            [float(section.area) for section in legal_sections],
            aggregate_target,
        ))
        front_loaded = (
            balanced[0] + 2.0,
            balanced[1] + 1.0,
            balanced[2],
            balanced[3] - 1.0,
            balanced[4] - 2.0,
        )
        program = next(
            item for item in base_seed_programs()
            if (item.metadata.get("base_seed") or {}).get("seed_id") == "bar"
        )
        first = select_legal_field_affine_projection(
            program,
            legal_sections=legal_sections,
            target_floor_areas_m2=balanced,
            floor_capacity_plan_hash="balanced-hash",
            aggregate_target_area_m2=aggregate_target,
            maximum_exact_candidates=4,
        )
        second = select_legal_field_affine_projection(
            program,
            legal_sections=legal_sections,
            target_floor_areas_m2=front_loaded,
            floor_capacity_plan_hash="front-loaded-hash",
            aggregate_target_area_m2=aggregate_target,
            maximum_exact_candidates=4,
        )

        self.assertAlmostEqual(sum(balanced), sum(front_loaded), places=8)
        self.assertIsNone(first)
        self.assertIsNone(second)

        contained_sections = tuple(
            box(-50.0, -50.0, 50.0, 50.0)
            for _section in legal_sections
        )
        first = select_legal_field_affine_projection(
            program,
            legal_sections=contained_sections,
            target_floor_areas_m2=balanced,
            floor_capacity_plan_hash="contained-balanced-hash",
            aggregate_target_area_m2=aggregate_target,
            maximum_exact_candidates=4,
        )
        second = select_legal_field_affine_projection(
            program,
            legal_sections=contained_sections,
            target_floor_areas_m2=front_loaded,
            floor_capacity_plan_hash="contained-front-loaded-hash",
            aggregate_target_area_m2=aggregate_target,
            maximum_exact_candidates=4,
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        assert first is not None and second is not None
        self.assertEqual(
            first.evidence["selected_matrix_hash"],
            second.evidence["selected_matrix_hash"],
        )
        self.assertEqual(
            first.projection.certificate["final_geometry_hash"],
            second.projection.certificate["final_geometry_hash"],
        )
        self.assertLessEqual(first.evidence["screened_candidate_count"], 36)
        self.assertLessEqual(first.evidence["exact_compiled_candidate_count"], 4)
        self.assertTrue(all(
            matrix == identity_matrix4()
            for matrix in first.projection.floor_matrices
        ))
        self.assertEqual(
            sum(
                node.semantic_role == "site_placement"
                for node in first.projection.program.nodes
            ),
            1,
        )
        self.assertEqual(
            sum(
                node.kind == "primitive"
                and node.operator == "box"
                for node in first.projection.program.nodes
            ),
            1,
        )

    def test_contained_fields_have_exact_nonpyramidal_witnesses_while_shrinking_rejects(
        self,
    ):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )

        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        programs = {
            record["slug"]: record
            for record in saved["programs"]
            if record["slug"] in {"neighborhood", "cultural"}
        }
        canonical = tuple(
            program
            for program in base_seed_programs()
            if (program.metadata.get("base_seed") or {}).get("seed_id")
            in {"bar", "slab"}
        ) + (
            next(
                program
                for program in universal_form_programs(0)
                if program.metadata.get("family") == "agent_shear"
            ),
        )

        witness_diagnostics = {}
        for slug, minimum_utilization in (
            ("neighborhood", 0.70),
            ("cultural", 0.40),
        ):
            floor_plan = programs[slug]["floor_capacity_plan"]
            legal_sections = tuple(
                shape(section)
                for section in floor_plan["legal_floor_sections"]
            )
            aggregate_target = (
                float(floor_plan["feasible_maximum_gfa_m2"])
                * minimum_utilization
            )
            target_floor_areas = tuple(allocate_floor_targets(
                [float(section.area) for section in legal_sections],
                aggregate_target,
            ))
            contained_sections = tuple(
                legal_sections[0] for _section in legal_sections
            )
            witnesses = []
            attempts = []
            for authored in canonical:
                rejected = select_legal_field_affine_projection(
                    authored,
                    legal_sections=legal_sections,
                    target_floor_areas_m2=target_floor_areas,
                    floor_capacity_plan_hash=f"frozen-{slug}-shrinking",
                    maximum_exact_candidates=4,
                )
                self.assertIsNone(rejected, (slug, authored.name))
                selected = select_legal_field_affine_projection(
                    authored,
                    legal_sections=contained_sections,
                    target_floor_areas_m2=target_floor_areas,
                    floor_capacity_plan_hash=f"frozen-{slug}-minimum",
                    maximum_exact_candidates=4,
                )
                if selected is None:
                    attempts.append({
                        "program": authored.name,
                        "status": "no_feasible_selection",
                    })
                    continue
                source = compile_site_bound_geometry_program_to_source_mass(
                    selected.projection.program,
                    contained_sections[0],
                    name=f"frozen-{slug}-{authored.name}",
                    volume_role="geometry_program",
                )
                self.assertIsNotNone(source)
                assert source is not None
                morphology = _solid_morphology_metrics(source)
                achieved = sum(
                    selected.projection.achieved_floor_areas_m2
                )
                placement_nodes = [
                    node
                    for node in selected.projection.program.nodes
                    if node.semantic_role == "site_placement"
                ]
                certificate = selected.projection.certificate
                attempts.append({
                    "program": authored.name,
                    "achieved": round(achieved, 6),
                    "target": round(aggregate_target, 6),
                    "upper_area_ratio": morphology["upper_area_ratio"],
                    "pyramidal_like": morphology["pyramidal_like"],
                    "screened": selected.evidence[
                        "screened_candidate_count"
                    ],
                    "exact_compiled": selected.evidence[
                        "exact_compiled_candidate_count"
                    ],
                })
                self.assertEqual(len(placement_nodes), 1)
                self.assertLessEqual(
                    selected.evidence["exact_compiled_candidate_count"],
                    4,
                )
                self.assertTrue(certificate["manifold"])
                self.assertTrue(certificate["watertight"])
                self.assertTrue(certificate["all_sections_contained"])
                bridge = source.metadata["geometry_program_bridge_evidence"]
                self.assertEqual(
                    bridge["program_hash"],
                    certificate["final_program_hash"],
                )
                self.assertEqual(
                    bridge["geometry_hash"],
                    certificate["final_geometry_hash"],
                )
                if (
                    achieved + 1e-7 >= aggregate_target * 0.995
                    and morphology["pyramidal_like"] is False
                ):
                    witnesses.append((authored.name, selected, morphology))
            witness_diagnostics[slug] = attempts
            self.assertTrue(witnesses, witness_diagnostics)

    def test_current_trusted_fields_have_three_exact_final_solid_choices(
        self,
    ):
        from design.maas.book_language.registry import (
            build_book_language_registry,
        )
        from design.maas.geometry_language import (
            apply_book_projection_to_geometry_program,
        )
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.maas.program_massing import (
            book_sentence_variants,
            compose_program_with_book_operations,
            program_seed_sequences,
        )

        raw_bar = next(
            program
            for program in base_seed_programs()
            if (program.metadata.get("base_seed") or {}).get("seed_id")
            == "bar"
        )
        slab = next(
            program
            for program in base_seed_programs()
            if (program.metadata.get("base_seed") or {}).get("seed_id")
            == "slab"
        )
        agent_shear = next(
            program
            for program in universal_form_programs(0)
            if program.metadata.get("family") == "agent_shear"
        )
        skew = next(
            principle
            for principle in build_book_language_registry()["principles"]
            if principle["principle_id"] == "book:operative:skew"
        )
        operations = book_sentence_variants(
            tuple(skew["execution_verbs"]),
            count=1,
        )[0]
        sequence = compose_program_with_book_operations(
            program_seed_sequences("gymnasium")[0],
            operations,
            base_volume_label="1/1",
            orientation="long_axis",
        )
        skew_bar = apply_book_projection_to_geometry_program(
            raw_bar,
            sequence,
        )
        authored_controls = (skew_bar, slab, agent_shear)

        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        records = {
            record["slug"]: record
            for record in saved["programs"]
            if record["slug"] in {"neighborhood", "cultural"}
        }
        self.assertEqual(set(records), {"neighborhood", "cultural"})

        for slug, minimum_utilization in (
            ("neighborhood", 0.70),
            ("cultural", 0.40),
        ):
            record = records[slug]
            stale_plan = record["floor_capacity_plan"]
            stale_sections = tuple(
                shape(section)
                for section in stale_plan["legal_floor_sections"]
            )
            first_section = stale_sections[0]
            height = float(stale_plan["selected_height_m"])
            floor_height = float(stale_plan["typical_floor_height_m"])
            parcel_side = sqrt(float(stale_plan["parcel_area_m2"]))
            capacity_site = box(0.0, 0.0, parcel_side, parcel_side)
            context = LegalGenerationContext(
                envelope=SimpleNamespace(
                    floor_height=floor_height,
                    height_limit=height,
                    bcr_limit=float(stale_plan["bcr_limit_pct"]),
                    far_limit=float(stale_plan["far_limit_pct"]),
                ),
                generation_site=first_section,
                sunlight_ring=(),
                evidence={
                    "schema_version":
                    "arr.maas.legal_generation_context.v1",
                    "status": "materialized",
                    "generation_precedes_selection": True,
                    "fixture_scope": "contained_current_trusted_field",
                },
            )

            with self.assertRaisesRegex(
                ValueError,
                "legal_floor_field_authority_mismatch",
            ):
                build_feasible_capacity_contract(
                    context,
                    site_local_utm=capacity_site,
                    height_m=height,
                    floors=int(stale_plan["selected_floor_count"]),
                    target_utilization=float(
                        stale_plan["target_utilization"]
                    ),
                    minimum_utilization=minimum_utilization,
                    floor_capacity_plan=stale_plan,
                )

            current_plan = derive_program_floor_capacity_plan(
                context,
                site_local_utm=capacity_site,
                building_type=record["program"],
                target_utilization=float(stale_plan["target_utilization"]),
                legacy_floor_hint=int(stale_plan["legacy_floor_hint"]),
                pnu=_PNU,
            )
            trusted_field = current_plan["legal_floor_field"]
            trusted_hash = current_plan["legal_floor_field_hash"]
            self.assertTrue(validate_legal_floor_field(trusted_field))
            self.assertEqual(
                trusted_hash,
                trusted_field["legal_floor_field_hash"],
            )
            contract = build_feasible_capacity_contract(
                context,
                site_local_utm=capacity_site,
                height_m=float(current_plan["selected_height_m"]),
                floors=int(current_plan["selected_floor_count"]),
                target_utilization=float(
                    current_plan["target_utilization"]
                ),
                minimum_utilization=minimum_utilization,
                floor_capacity_plan=current_plan,
            )
            self.assertEqual(contract["legal_floor_field"], trusted_field)
            self.assertEqual(
                contract["legal_floor_field_hash"],
                trusted_hash,
            )

            legal_sections = tuple(
                shape(section)
                for section in trusted_field["legal_floor_sections"]
            )
            aggregate_target = (
                float(stale_plan["feasible_maximum_gfa_m2"])
                * minimum_utilization
            )
            target_floor_areas = tuple(allocate_floor_targets(
                [float(section.area) for section in stale_sections],
                aggregate_target,
            ))
            identities = set()
            morphologies = []
            for authored in authored_controls:
                selected = select_legal_field_affine_projection(
                    authored,
                    legal_sections=legal_sections,
                    target_floor_areas_m2=target_floor_areas,
                    floor_capacity_plan_hash=current_plan[
                        "floor_capacity_plan_hash"
                    ],
                    aggregate_target_area_m2=aggregate_target,
                    maximum_exact_candidates=4,
                )
                self.assertIsNotNone(selected, (slug, authored.name))
                assert selected is not None
                source = compile_site_bound_geometry_program_to_source_mass(
                    selected.projection.program,
                    legal_sections[0],
                    name=f"trusted-{slug}-{authored.name}",
                )
                self.assertIsNotNone(source, (slug, authored.name))
                assert source is not None
                bridge = source.metadata[
                    "geometry_program_bridge_evidence"
                ]
                certificate = selected.projection.certificate
                self.assertEqual(
                    bridge["program_hash"],
                    certificate["final_program_hash"],
                )
                self.assertEqual(
                    bridge["geometry_hash"],
                    certificate["final_geometry_hash"],
                )
                self.assertTrue(certificate["all_sections_contained"])
                identities.add((
                    bridge["program_hash"],
                    bridge["geometry_hash"],
                ))
                morphologies.append(_solid_morphology_metrics(source))

            self.assertEqual(len(identities), 3, slug)
            self.assertTrue(
                any(
                    morphology["pyramidal_like"] is False
                    for morphology in morphologies
                ),
                slug,
            )

    def _legacy_r8_three_choice_fixture_without_legal_authority(self):
        saved = json.loads(_SUMMARY.read_text(encoding="utf-8"))
        programs = {
            record["slug"]: record
            for record in saved["programs"]
            if record["slug"] in {"neighborhood", "cultural"}
        }
        self.assertEqual(set(programs), {"neighborhood", "cultural"})
        acceptance_results = []

        for slug in ("neighborhood", "cultural"):
            record = programs[slug]
            floor_plan = record["floor_capacity_plan"]
            legal_sections = tuple(
                shape(section)
                for section in floor_plan["legal_floor_sections"]
            )
            height = float(floor_plan["selected_height_m"])
            floors = int(floor_plan["selected_floor_count"])
            floor_height = height / floors
            generation_site = legal_sections[0]
            parcel_side = sqrt(float(floor_plan["parcel_area_m2"]))
            capacity_site = box(0.0, 0.0, parcel_side, parcel_side)
            context = LegalGenerationContext(
                envelope=SimpleNamespace(
                    bcr_limit=float(floor_plan["bcr_limit_pct"]),
                    far_limit=float(floor_plan["far_limit_pct"]),
                ),
                generation_site=generation_site,
                sunlight_ring=(),
                evidence={
                    "schema_version": "arr.maas.legal_generation_context.v1",
                    "status": "materialized",
                    "generation_precedes_selection": True,
                    "original_site_area_m2": float(
                        floor_plan["parcel_area_m2"]
                    ),
                    "generation_site_area_m2": float(generation_site.area),
                    "sunlight_field_status": "materialized",
                    "bcr_limit_pct": float(floor_plan["bcr_limit_pct"]),
                    "far_limit_pct": float(floor_plan["far_limit_pct"]),
                    "height_limit_m": float(
                        floor_plan["legal_height_cap_m"]
                    ),
                },
            )
            capacity_contract = build_feasible_capacity_contract(
                context,
                site_local_utm=capacity_site,
                height_m=height,
                floors=floors,
                target_utilization=float(floor_plan["target_utilization"]),
                minimum_utilization=(
                    0.70 if slug == "neighborhood" else 0.40
                ),
                floor_capacity_plan=floor_plan,
            )
            minx, miny, maxx, maxy = generation_site.bounds
            east_access = mapping(LineString(((maxx, miny), (maxx, maxy))))

            def frozen_section(_context, band_height):
                index = min(
                    floors - 1,
                    max(0, int(round(float(band_height) / floor_height)) - 1),
                )
                return legal_sections[index]

            candidates = []
            page_counts = []
            with (
                patch.object(
                    candidate_generation,
                    "generation_site_at_height",
                    side_effect=frozen_section,
                ),
                patch.object(
                    candidate_generation,
                    "_site_access_side_in_principal_frame",
                    return_value="west",
                ),
            ):
                for page in (0, 1):
                    pool, counts = candidate_generation._program_pool(
                        generation_site,
                        record["program"],
                        height,
                        floors,
                        generation_context=context,
                        parent_variant_indices=(page,),
                        recursive_only=True,
                        program_dimensional_context=record[
                            "program_dimensional_context"
                        ],
                        site_boundary_source="frozen-r8-pnu1",
                        site_access_context={
                            "primary_access_side": "east",
                            "road_width_m": 37.48057265709449,
                        },
                        site_access_geometry=east_access,
                        live_geometry_vlm_revision=False,
                        base_capacity_contract=capacity_contract,
                        capacity_site=capacity_site,
                        pnu=_PNU,
                        diagnostic_scope_labels=("1/1", "3/8", "1/2"),
                        diagnostic_book_probe_count=1,
                        diagnostic_evaluation_cap=36,
                        diagnostic_candidate_cap=12,
                    )
                    page_counts.append(counts)
                    candidates.extend(pool)

            eligible = []
            for candidate in candidates:
                metadata = candidate.source.metadata
                floor_contract = metadata.get("shared_floor_contract") or {}
                capacity = metadata.get("source_capacity_measurement") or {}
                projection = (
                    metadata.get("capacity_alternative_projection") or {}
                )
                bridge = (
                    metadata.get("geometry_program_bridge_evidence") or {}
                )
                compilation = (
                    metadata.get("geometry_program_compilation") or {}
                )
                final_program_hash = str(
                    metadata.get("final_program_hash") or ""
                )
                final_geometry_hash = str(
                    metadata.get("final_geometry_hash") or ""
                )
                if not (
                    floor_contract.get("hard_pass") is True
                    and capacity.get("hard_pass") is True
                    and projection.get("selectable_capacity_hard_pass") is True
                    and final_program_hash
                    and final_geometry_hash
                    and bridge.get("program_hash") == final_program_hash
                    and bridge.get("geometry_hash") == final_geometry_hash
                    and compilation.get("program_hash") == final_program_hash
                    and compilation.get("geometry_hash") == final_geometry_hash
                ):
                    continue
                morphology = _solid_morphology_metrics(candidate)
                self.assertEqual(morphology["component_count"], 1)
                self.assertTrue(candidate.source.surfaces)
                for volume in candidate.source.volumes:
                    midpoint = (
                        float(volume.bottom_fraction)
                        + float(volume.top_fraction)
                    ) / 2.0
                    section_index = min(
                        floors - 1,
                        max(0, int(midpoint * floors)),
                    )
                    outside = volume.footprint.difference(
                        legal_sections[section_index]
                    )
                    self.assertLessEqual(float(outside.area), 1e-7)
                eligible.append((
                    final_program_hash,
                    final_geometry_hash,
                    morphology,
                ))

            identities = {
                (program_hash, geometry_hash)
                for program_hash, geometry_hash, _morphology in eligible
            }
            diagnostics = {
                "slug": slug,
                "page_counts": [
                    {
                        "evaluated": counts["evaluated"],
                        "compiled": counts["compiled"],
                        "clean": counts["clean"],
                        "program_passed": counts["program_passed"],
                        "geometry_stage_counts": counts.get(
                            "geometry_stage_counts"
                        ),
                    }
                    for counts in page_counts
                ],
                "candidate_count": len(candidates),
                "eligible_count": len(eligible),
                "identity_count": len(identities),
                "phenotypes": [
                    morphology["phenotype"]
                    for _program_hash, _geometry_hash, morphology in eligible
                ],
                "pyramidal": [
                    morphology["pyramidal_like"]
                    for _program_hash, _geometry_hash, morphology in eligible
                ],
            }
            acceptance_results.append((
                diagnostics,
                len(identities) >= 3,
                any(
                    morphology["pyramidal_like"] is False
                    for _program_hash, _geometry_hash, morphology in eligible
                ),
            ))

        for diagnostics, enough_identities, has_nonpyramidal in acceptance_results:
            with self.subTest(slug=diagnostics["slug"]):
                self.assertTrue(enough_identities, diagnostics)
                self.assertTrue(has_nonpyramidal, diagnostics)
