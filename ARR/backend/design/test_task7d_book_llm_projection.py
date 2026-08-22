"""Task7D regressions for BOOK projection over live LLM-authored ASTs."""

import json
from dataclasses import replace
from unittest import TestCase

from shapely.geometry import box

from design.maas.book_language.candidate_generation import (
    _body_program_for_book_projection,
    _materialize_directed_geometry,
    _program_projection_evidence,
    _required_book_projection_failure,
)
from design.maas.geometry_language import (
    GeometryNode,
    base_seed_program,
    compile_geometry_program,
    compile_geometry_program_to_source_mass,
    parse_geometry_dsl,
)
from design.maas.geometry_language.affine_matrix import (
    identity_matrix4,
    matrix4_to_lists,
)
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.program_massing.book_projection import (
    compose_program_with_book_operations,
)


class Task7DBookLlmProjectionTests(TestCase):
    def _llm_program(self, name):
        dsl = {
            "llm_split_wing": (
                "mass base = box(12, 6, 5)\n"
                "mass result = move(base, 0.4, 0, 0)"
            ),
            "llm_translate_carve_void": (
                "mass base = box(12, 7, 5)\n"
                "mass voided = carve_void(base, margin_ratio=0.22, "
                "open_side='west')\n"
                "mass result = move(voided, 0.4, -0.2, 0)"
            ),
        }[name]
        program = parse_geometry_dsl(dsl, name=name)
        return replace(
            program,
            metadata={
                **program.metadata,
                "author_provider": "openai_llm_geometry_author",
                "llm_geometry_author_active": True,
                "author_model": "gpt-task7d-geometry",
                "author_response_id": f"response-{name}",
                "language_layer": "llm_authored_recursive_geometry",
            },
        )

    @staticmethod
    def _book_sequence(name, operations, scope, *, program=None):
        notes = ()
        if program is not None:
            notes = (
                "geometry_program_payload="
                + json.dumps(program.to_dict(), sort_keys=True),
                "geometry_program_legal_fit_strength=0",
                "geometry_program_source=procedural_geometry_synthesis_agent",
                "geometry_program_source_seed=task7d-llm-seed",
            )
        return compose_program_with_book_operations(
            VerbSequence(
                name=name,
                label=name,
                calls=(VerbCall("base", {}),),
                notes=notes,
            ),
            operations,
            base_volume_label=scope,
            orientation="long_axis",
        )

    def _project(self, program, sequence):
        post_book = _body_program_for_book_projection(program, sequence)
        return (
            post_book,
            compile_geometry_program(program),
            compile_geometry_program(post_book),
        )

    def test_r335_llm_carve_offset_quarter_scope_uses_generic_book_adapter(self):
        pre_book = self._llm_program("llm_split_wing")
        sequence = self._book_sequence(
            "r335_carve_offset",
            (
                VerbCall("carve", {"width_ratio": 0.36, "depth_ratio": 0.24}),
                VerbCall("offset", {"distance_ratio": 0.21, "other_scale": 0.48}),
            ),
            "1/4",
        )

        post_book, pre_compilation, post_compilation = self._project(
            pre_book, sequence
        )
        projection = post_book.metadata["book_recursive_projection"]
        provenance = _program_projection_evidence(post_book, {
            "status": "materialized",
            "program_hash": post_book.program_hash(),
            "geometry_hash": post_compilation.geometry_hash,
        })

        self.assertEqual(pre_book.node_map[pre_book.root_id].operator, "translate")
        self.assertGreater(len(pre_book.nodes), 1)
        self.assertTrue(projection["active"])
        self.assertEqual(projection["scope_label"], "1/4")
        self.assertEqual(projection["ordered_verbs"], ["carve", "offset"])
        self.assertEqual(post_book.metadata["author_provider"], "openai_llm_geometry_author")
        self.assertNotEqual(pre_book.program_hash(), post_book.program_hash())
        self.assertEqual(pre_compilation.status, "compiled")
        self.assertEqual(post_compilation.status, "compiled")
        self.assertNotEqual(pre_compilation.geometry_hash, post_compilation.geometry_hash)
        self.assertEqual(provenance["authoritative_program_hash"], post_book.program_hash())

    def test_r335_llm_overlap_expand_half_scope_uses_generic_book_adapter(self):
        pre_book = self._llm_program("llm_translate_carve_void")
        sequence = self._book_sequence(
            "r335_overlap_expand",
            (
                VerbCall("overlap", {"slab_ratio": 0.58, "vertical_overlap": 0.22}),
                VerbCall("expand", {"factor": 0.31}),
            ),
            "1/2",
        )

        post_book, pre_compilation, post_compilation = self._project(
            pre_book, sequence
        )
        projection = post_book.metadata["book_recursive_projection"]

        self.assertEqual(pre_book.node_map[pre_book.root_id].operator, "translate")
        self.assertIn("carve_void", {node.operator for node in pre_book.nodes})
        self.assertTrue(projection["active"])
        self.assertEqual(projection["scope_label"], "1/2")
        self.assertEqual(projection["ordered_verbs"], ["overlap", "expand"])
        self.assertNotEqual(pre_book.program_hash(), post_book.program_hash())
        self.assertEqual(pre_compilation.status, "compiled")
        self.assertEqual(post_compilation.status, "compiled")
        self.assertNotEqual(pre_compilation.geometry_hash, post_compilation.geometry_hash)

    def test_non_llm_program_without_book_calls_is_unchanged(self):
        program = base_seed_program("bar")
        sequence = VerbSequence(
            name="procedural_no_book",
            label="procedural no BOOK",
            calls=(VerbCall("base", {}),),
        )

        self.assertIs(_body_program_for_book_projection(program, sequence), program)

    def test_required_book_projection_rejects_post_book_compile_failure(self):
        pre_book = self._llm_program("llm_split_wing")
        sequence = self._book_sequence(
            "post_compile_failure",
            (VerbCall("expand", {"factor": 0.3}),),
            "1/2",
        )
        post_book = _body_program_for_book_projection(pre_book, sequence)
        invalid_post_book = replace(post_book, root_id="missing_root")
        pre_compilation = compile_geometry_program(pre_book)
        post_compilation = compile_geometry_program(invalid_post_book)

        self.assertEqual(pre_compilation.status, "compiled")
        self.assertEqual(post_compilation.status, "invalid_program")

        failure = _required_book_projection_failure(
            sequence,
            pre_book_program=pre_book,
            pre_book_compilation=pre_compilation,
            post_book_program=invalid_post_book,
            post_book_compilation=post_compilation,
        )

        self.assertEqual(
            failure["book_projection_failure"],
            "book_projection_post_compile_failed",
        )

    def test_required_book_projection_rejects_missing_or_inactive_metadata(self):
        pre_book = self._llm_program("llm_split_wing")
        sequence = self._book_sequence(
            "inactive_projection_metadata",
            (VerbCall("expand", {"factor": 0.3}),),
            "1/2",
        )
        adapted = _body_program_for_book_projection(pre_book, sequence)
        missing = replace(adapted, metadata={
            key: value
            for key, value in adapted.metadata.items()
            if key != "book_recursive_projection"
        })
        inactive = replace(adapted, metadata={
            **adapted.metadata,
            "book_recursive_projection": {
                **adapted.metadata["book_recursive_projection"],
                "active": False,
            },
        })
        pre_compilation = compile_geometry_program(pre_book)

        for label, post_book in (("missing", missing), ("inactive", inactive)):
            with self.subTest(label):
                post_compilation = compile_geometry_program(post_book)
                self.assertEqual(post_compilation.status, "compiled")
                failure = _required_book_projection_failure(
                    sequence,
                    pre_book_program=pre_book,
                    pre_book_compilation=pre_compilation,
                    post_book_program=post_book,
                    post_book_compilation=post_compilation,
                )
                self.assertEqual(
                    failure["book_projection_failure"],
                    "book_projection_adapter_inactive",
                )

    def test_required_book_projection_rejects_equal_program_hash(self):
        pre_book = self._llm_program("llm_split_wing")
        sequence = self._book_sequence(
            "program_hash_noop",
            (VerbCall("expand", {"factor": 0.3}),),
            "1/2",
        )
        post_book = replace(pre_book, metadata={
            **pre_book.metadata,
            "book_recursive_projection": {"active": True},
            "projection_provenance_probe": "metadata_only_difference",
        })
        pre_compilation = compile_geometry_program(pre_book)
        post_compilation = compile_geometry_program(post_book)

        self.assertIsNot(pre_book, post_book)
        self.assertNotEqual(pre_book.metadata, post_book.metadata)
        self.assertEqual(pre_book.program_hash(), post_book.program_hash())
        self.assertEqual(pre_compilation.status, "compiled")
        self.assertEqual(post_compilation.status, "compiled")
        failure = _required_book_projection_failure(
            sequence,
            pre_book_program=pre_book,
            pre_book_compilation=pre_compilation,
            post_book_program=post_book,
            post_book_compilation=post_compilation,
        )

        self.assertEqual(
            failure["book_projection_failure"],
            "book_projection_program_noop",
        )

    def test_required_book_projection_rejects_equal_geometry_after_ast_change(self):
        pre_book = base_seed_program("bar")
        sequence = self._book_sequence(
            "geometry_hash_noop",
            (VerbCall("expand", {"factor": 0.3}),),
            "1/2",
        )
        identity_node = GeometryNode(
            id="task7d_semantic_identity",
            kind="transform",
            operator="matrix4",
            inputs=(pre_book.root_id,),
            parameters={"matrix4": matrix4_to_lists(identity_matrix4())},
            semantic_role="semantic_identity_noop",
            provenance={"source": "task7d_semantic_identity_probe"},
        )
        post_book = replace(
            pre_book,
            nodes=(*pre_book.nodes, identity_node),
            root_id=identity_node.id,
            metadata={
                **pre_book.metadata,
                "book_recursive_projection": {"active": True},
            },
        )
        pre_compilation = compile_geometry_program(pre_book)
        post_compilation = compile_geometry_program(post_book)

        self.assertEqual(pre_compilation.status, "compiled")
        self.assertEqual(post_compilation.status, "compiled")
        self.assertNotEqual(pre_book.program_hash(), post_book.program_hash())
        self.assertEqual(
            pre_compilation.geometry_hash,
            post_compilation.geometry_hash,
        )

        failure = _required_book_projection_failure(
            sequence,
            pre_book_program=pre_book,
            pre_book_compilation=pre_compilation,
            post_book_program=post_book,
            post_book_compilation=post_compilation,
        )

        self.assertEqual(
            failure["book_projection_failure"],
            "book_projection_geometry_noop",
        )

    def test_legal_success_keeps_post_book_ast_as_final_program_without_replay(self):
        from design.maas.program_massing.semantic_carriers import (
            bind_source_role_scaffold_to_program,
        )
        from design.maas.program_massing.sequences import program_seed_sequences
        from design.maas.source_geometry import compile_sequence_to_source_mass

        building_type = "neighborhood_living"
        pre_book = self._llm_program("llm_split_wing")
        pre_compilation = compile_geometry_program(pre_book)
        pre_book = replace(pre_book, metadata={
            **pre_book.metadata,
            "base_primitive_geometry_hash": pre_compilation.geometry_hash,
        })
        sequence = self._book_sequence(
            "legal_success",
            (
                VerbCall("carve", {"width_ratio": 0.36, "depth_ratio": 0.24}),
                VerbCall("offset", {"distance_ratio": 0.21, "other_scale": 0.48}),
            ),
            "1/4",
            program=pre_book,
        )
        post_book = _body_program_for_book_projection(pre_book, sequence)
        post_compilation = compile_geometry_program(post_book)
        host = box(-20.0, -20.0, 20.0, 20.0)
        source = compile_sequence_to_source_mass(
            host,
            program_seed_sequences(building_type)[0],
        )
        self.assertIsNotNone(source)
        source = replace(source, metadata={
            **source.metadata,
            "candidate_floor_context": {"height_m": 10.0, "floors": 1},
        })
        terminal_records = []

        materialized = _materialize_directed_geometry(
            source,
            sequence,
            containment_host=host,
            floor_containment_hosts=(host,),
            minimum_host_plan_coverage=0.05,
            floor_capacity_plan_hash="task7d-floor-plan",
            target_floor_areas_m2=(100.0,),
            building_type=building_type,
            pnu="task7d-pnu",
            capacity_alternative_id="task7d-capacity-alternative",
            achieved_capacity_band="task7d-achieved-band",
            capacity_measurement_hash="task7d-capacity-measurement",
            site_context_hash="task7d-site-context",
            legal_floor_field_hash="task7d-legal-field",
            terminal_failure_sink=terminal_records,
        )

        self.assertIsNotNone(materialized, terminal_records)
        metadata = materialized.metadata
        bridge = metadata["geometry_program_bridge_evidence"]
        certificate = metadata["authored_legal_projection_certificate"]
        expected_final_program = bind_source_role_scaffold_to_program(
            post_book,
            source,
            program_id=building_type,
        )
        self.assertIsNotNone(expected_final_program)
        expected_final_compilation = compile_geometry_program(
            expected_final_program
        )
        self.assertEqual(
            metadata["final_program_hash"],
            expected_final_program.program_hash(),
        )
        self.assertEqual(
            metadata["geometry_program"], expected_final_program.to_dict()
        )
        self.assertEqual(
            metadata["authored_geometry_program"],
            expected_final_program.to_dict(),
        )
        self.assertEqual(bridge["author_provider"], "openai_llm_geometry_author")
        self.assertTrue(bridge["llm_geometry_author_active"])
        self.assertEqual(bridge["author_source"], "openai_llm_geometry_author")
        self.assertEqual(bridge["author_model"], "gpt-task7d-geometry")
        self.assertEqual(
            bridge["llm_geometry_author_model"],
            "gpt-task7d-geometry",
        )
        self.assertEqual(
            bridge["author_response_id"],
            "response-llm_split_wing",
        )
        self.assertEqual(
            bridge["llm_geometry_author_response_id"],
            "response-llm_split_wing",
        )
        self.assertEqual(
            bridge["initial_llm_authored_pre_book_program_hash"],
            pre_book.program_hash(),
        )
        self.assertEqual(
            bridge["initial_llm_authored_pre_book_geometry_hash"],
            pre_compilation.geometry_hash,
        )
        self.assertEqual(
            bridge["post_book_authored_program_hash"],
            expected_final_program.program_hash(),
        )
        self.assertEqual(
            bridge["post_book_authored_geometry_hash"],
            expected_final_compilation.geometry_hash,
        )
        self.assertEqual(
            bridge["final_projected_surface_hash"],
            metadata["final_geometry_hash"],
        )
        self.assertEqual(
            certificate["input_authored_program_hash"],
            expected_final_program.program_hash(),
        )
        self.assertEqual(
            certificate["input_authored_geometry_hash"],
            expected_final_compilation.geometry_hash,
        )
        self.assertEqual(
            certificate["projected_surface_hash"],
            metadata["final_geometry_hash"],
        )
        operators = {
            node.get("operator") for node in metadata["geometry_program"]["nodes"]
        }
        self.assertNotIn("extruded_polygon", operators)
        self.assertNotEqual(
            metadata["geometry_program"]["metadata"].get("family"),
            "materialized_floorwise_legal_projection",
        )
        self.assertFalse(bridge["legal_floor_loft_or_prism_replay_allowed"])
        self.assertNotEqual(
            metadata["authored_geometry_provenance"]["authority"],
            "upstream_provenance_only",
        )
