"""r340 regressions for exact-shortlist base lineage transport."""

from dataclasses import replace
from unittest import TestCase
from unittest.mock import patch

from design.maas.book_language import candidate_generation
from design.maas.book_language import quality_diversity_archive
from design.maas.book_language import vlm_review
from design.maas.book_language.legal_mass_archive import LegalMassArchive
from design import test_legal_mass_archive as legal_archive_tests
from design.test_maas_floorwise_candidate_rejection import _slab_fallback_case


class R340BaseVlmTransportTests(TestCase):
    @staticmethod
    def _principles():
        base = {
            "principle_id": "book:operative:subtract",
            "lineage_base_operative_id": "book:operative:subtract",
            "generation_stage": "base",
        }
        descendant = {
            "principle_id": "book:combination:setback_notch",
            "lineage_base_operative_id": "book:operative:subtract",
            "generation_stage": "combination",
        }
        return base, descendant

    def test_exact_shortlist_adds_base_with_same_seed_and_variant(self):
        base, descendant = self._principles()
        expand = getattr(
            candidate_generation,
            "_expand_competition_exact_lineage_dependencies",
            lambda keys, _principles: keys,
        )

        expanded = expand(
            frozenset({"7:book:combination:setback_notch:5"}),
            (base, descendant),
        )

        self.assertEqual(
            expanded,
            frozenset({
                "7:book:operative:subtract:5",
                "7:book:combination:setback_notch:5",
            }),
        )

    def test_archived_legal_mass_survives_design_quality_failures_for_base_vlm(self):
        source = legal_archive_tests.LegalMassArchiveTests()._generation_source()
        archive = LegalMassArchive()
        archived_record = candidate_generation._admit_legal_mass_candidate(
            archive,
            source,
            compiler_clean_passed=True,
            site_containment_passed=True,
        )

        authority = candidate_generation._program_review_authority(
            archived_record=archived_record,
            program_evidence={"hard_pass": False},
            program_form_gate={
                "hard_pass": False,
                "failures": ["over_tortuous_mass_outline"],
            },
            gate_pass={
                "role_coverage": True,
                "dominant_ratio": True,
                "site_coverage": False,
                "hierarchy": False,
                "coherence": False,
                "program_form": False,
            },
            coherence_evidence={
                "hard_pass": False,
                "failure_reasons": ["over_tortuous_mass_outline"],
                "polygon_quality_score": 0.21,
            },
        )

        self.assertIsNotNone(archived_record)
        self.assertTrue(authority["hard_pass"])
        self.assertTrue(authority["legal_archive_authority"])
        self.assertFalse(authority["design_quality_hard_gate"])
        self.assertEqual(
            authority["release_authority"],
            "independently_certified_legal_mass_archive",
        )
        self.assertTrue(authority["typed_revision_signal"]["active"])
        self.assertIn("site_coverage", authority["failed_design_gates"])
        self.assertIn("coherence", authority["failed_design_gates"])

    def test_actual_legal_or_structural_failure_cannot_gain_review_authority(self):
        fixture = legal_archive_tests.LegalMassArchiveTests()
        illegal_source = fixture._generation_source(
            legal_capacity_authority={"legal_hard_pass": False},
        )
        invalid_surface_source = fixture._generation_source()
        invalid_surface_source.surfaces = ()
        cases = (
            (illegal_source, True, True),
            (fixture._generation_source(), True, False),
            (invalid_surface_source, True, True),
        )

        for source, compiler_clean, contained in cases:
            with self.subTest(compiler_clean=compiler_clean, contained=contained):
                archived_record = candidate_generation._admit_legal_mass_candidate(
                    LegalMassArchive(),
                    source,
                    compiler_clean_passed=compiler_clean,
                    site_containment_passed=contained,
                )
                authority = candidate_generation._program_review_authority(
                    archived_record=archived_record,
                    program_evidence={"hard_pass": False},
                    program_form_gate={"hard_pass": False, "failures": []},
                    gate_pass={"site_coverage": False, "coherence": False},
                    coherence_evidence={"hard_pass": False},
                )

                self.assertIsNone(archived_record)
                self.assertFalse(authority["hard_pass"])
                self.assertEqual(authority["release_authority"], "none")

    def test_exact_shortlist_does_not_duplicate_selected_base(self):
        base, descendant = self._principles()
        expand = getattr(
            candidate_generation,
            "_expand_competition_exact_lineage_dependencies",
            lambda keys, _principles: keys,
        )

        expanded = expand(
            frozenset({"3:book:operative:subtract:2"}),
            (base, descendant),
        )

        self.assertEqual(expanded, frozenset({"3:book:operative:subtract:2"}))

    def test_exact_shortlist_fails_closed_when_base_dependency_is_missing(self):
        _base, descendant = self._principles()
        expand = getattr(
            candidate_generation,
            "_expand_competition_exact_lineage_dependencies",
            lambda keys, _principles: keys,
        )

        expanded = expand(
            frozenset({"4:book:combination:setback_notch:8"}),
            (descendant,),
        )

        self.assertEqual(expanded, frozenset())

    def test_llm_selected_descendant_returns_base_then_descendant(self):
        base, descendant = self._principles()
        scheduled = ((0, base), (1, descendant))

        selected = candidate_generation._principles_for_seed(
            scheduled,
            seed_index=0,
            llm_authored_seed=True,
            selected_principle_ids=frozenset({descendant["principle_id"]}),
        )

        self.assertEqual(selected, scheduled)

    def test_program_pool_binds_only_archived_base_and_rejects_unarchived_base(self):
        base, descendant = self._principles()
        for principle in (base, descendant):
            principle.update({
                "execution_verbs": ("subtract",),
                "kind": "base_operative"
                if principle is base else "combination",
                "label": principle["principle_id"],
            })
        source, _program, legal_section, seed, _context = _slab_fallback_case()
        floor_context = {
            "hard_pass": True,
            "height_m": 16.0,
            "floors": 4,
            "legal_sections": (legal_section,) * 4,
            "floor_top_heights_m": (4.0, 8.0, 12.0, 16.0),
            "upper_legal_section": legal_section,
            "authority": "r343_live_order",
            "legal_floor_field_hash": "",
        }
        materialized_stages = []
        archive_base = {"enabled": False}
        archive_fixture = (
            legal_archive_tests.LegalMassArchiveTests()._generation_source()
        )
        certified_source = replace(
            source,
            surfaces=archive_fixture.surfaces,
            metadata={
                **source.metadata,
                **archive_fixture.metadata,
                "program_book_projection_evidence": {
                    "status": "materialized",
                },
                "geometry_program_bridge_evidence": {
                    "geometry_hash": "geometry-final",
                    "program_hash": "program-final",
                },
            },
        )

        def compose(active_seed, _operations, *, name_suffix, **_kwargs):
            return replace(
                active_seed,
                name=f"{active_seed.name}__{name_suffix}",
            )

        def materialize(_source, sequence, **_kwargs):
            stage = (
                "base"
                if "operative_subtract" in sequence.name
                else "combination"
            )
            materialized_stages.append(stage)
            if stage == "base" and archive_base["enabled"]:
                return certified_source
            return replace(source, metadata={
                **source.metadata,
                "program_book_projection_evidence": {
                    "status": "materialized",
                },
                "geometry_program_bridge_evidence": {
                    "geometry_hash": f"{stage}-post-book-geometry",
                    "program_hash": f"{stage}-post-book-program",
                },
            })

        def source_feature(*_args, **_kwargs):
            return {"properties": {
                "program_spatial_evidence": {
                    "required_role_hits": (True,),
                    "dominant_ratio_score": 1.0,
                    "site_coverage_score": 1.0,
                    "hierarchy_score": 1.0,
                    "architectural_score": 1.0,
                },
                "source_signature": {
                    "coherence_evidence": {"hard_pass": True},
                },
            }}

        def review_archived_bases(base_pool):
            reviewed = []
            for candidate in base_pool:
                reviewed.append(vlm_review._attach_base_book_vlm_audit(
                    candidate,
                    {
                    "status": "fail",
                    "hard_pass": False,
                    "failures": [
                        "book_stage_feasible_capacity_below_competition_floor"
                    ],
                    "response_id": "r5-small-vlm-response",
                    "critic_actions": ["clarify_primary_gesture"],
                    "geometry_edits": [{"operator": "subtract"}],
                    "vlm_audit": {
                        "status": "fail",
                        "hard_pass": False,
                        "failures": [
                            "book_stage_feasible_capacity_below_competition_floor"
                        ],
                        "response_id": "r5-small-vlm-response",
                        "review_stage": "book_base_operative",
                        "reviewed_exact_post_book_geometry": True,
                    },
                    },
                    reused_from_outcome_graph=False,
                ))
            return reviewed, {
                "reviewed_parent_fingerprints": ["r5-reviewed-base"],
                "hard_pass_count": 0,
            }

        class PassThroughArchive:
            compaction_count = 0
            released_count = 0
            peak_candidate_count = 0

            def __init__(self):
                self.items = []

            def append(self, candidate):
                self.items.append(candidate)
                self.peak_candidate_count = len(self.items)

            def finalize(self):
                self.released_count = len(self.items)
                return list(self.items)

        with (
            patch.object(
                candidate_generation,
                "_agent_mutated_seeds",
                return_value=(seed,),
            ),
            patch.object(
                candidate_generation,
                "_seed_is_llm_authored",
                return_value=True,
            ),
            patch.object(
                candidate_generation,
                "program_seed_variants",
                side_effect=lambda active_seed, **_kwargs: (active_seed,),
            ),
            patch.object(
                candidate_generation,
                "build_book_language_registry",
                return_value={"principles": (base, descendant)},
            ),
            patch.object(
                candidate_generation,
                "_principles_for_seed",
                return_value=((1, descendant), (0, base)),
            ),
            patch.object(
                candidate_generation,
                "diagnostic_anchor_sentence_variants",
                return_value=((),),
            ),
            patch.object(
                candidate_generation,
                "compose_program_with_book_operations",
                side_effect=compose,
            ),
            patch.object(
                candidate_generation,
                "book_probe_scope",
                return_value=("1/2", "long_axis"),
            ),
            patch.object(
                candidate_generation,
                "compile_sequence_to_source_mass",
                return_value=source,
            ),
            patch.object(
                candidate_generation,
                "_candidate_floor_context",
                return_value=floor_context,
            ),
            patch.object(
                candidate_generation,
                "recursive_plan_coverage_floor",
                return_value=0.5,
            ),
            patch.object(
                candidate_generation,
                "_materialize_directed_geometry",
                side_effect=materialize,
            ),
            patch.object(
                candidate_generation,
                "_clean_mass_gate",
                return_value=(True, {"failure_reasons": ()}),
            ),
            patch.object(candidate_generation, "_inside_site", return_value=True),
            patch.object(
                candidate_generation,
                "source_feature",
                side_effect=source_feature,
            ),
            patch.object(
                candidate_generation,
                "attach_program_massing_evidence",
                return_value={"hard_pass": True, "program_fit_score": 1.0},
            ),
            patch.object(
                candidate_generation,
                "_program_form_gate",
                return_value={"hard_pass": True},
            ),
            patch.object(candidate_generation, "_record_gate_diagnostic"),
            patch.object(
                candidate_generation,
                "universal_form_program_pages",
                return_value=(),
            ),
            patch.object(candidate_generation, "program_seed_sequences", return_value=()),
            patch.object(
                quality_diversity_archive,
                "StreamingMapElitesArchive",
                PassThroughArchive,
            ),
        ):
            pool, report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                exact_compile_limit=2,
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
            )
            initial_materialized_stages = list(materialized_stages)

            archive_base["enabled"] = True
            materialized_stages.clear()
            certified_pool, certified_report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                exact_compile_limit=2,
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
                base_review_callback=review_archived_bases,
            )
            certified_materialized_stages = list(materialized_stages)

            materialized_stages.clear()
            no_review_pool, no_review_report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                exact_compile_limit=2,
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
                base_review_callback=lambda _bases: ([], {
                    "reviewed_parent_fingerprints": [],
                    "hard_pass_count": 0,
                }),
            )

            archive_base["enabled"] = False
            materialized_stages.clear()
            legal_false_pool, legal_false_report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                exact_compile_limit=2,
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
                base_review_callback=review_archived_bases,
            )
            archive_base["enabled"] = True

            def conflicting_review(base_pool):
                reviewed, evidence = review_archived_bases(base_pool)
                if not reviewed:
                    return reviewed, evidence
                original = reviewed[0]
                metadata = dict(original.source.metadata)
                metadata["final_geometry_hash"] = "conflicting-final-hash"
                certificate = dict(
                    metadata["authored_legal_projection_certificate"]
                )
                certificate["projected_surface_hash"] = (
                    "conflicting-final-hash"
                )
                metadata["authored_legal_projection_certificate"] = certificate
                return [
                    original,
                    replace(
                        original,
                        source=replace(original.source, metadata=metadata),
                    ),
                ], evidence

            materialized_stages.clear()
            conflict_pool, conflict_report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                exact_compile_limit=2,
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
                base_review_callback=conflicting_review,
            )

        descendant_candidates = [
            candidate
            for candidate in pool
            if candidate.source.metadata["book_generation_lineage"]["stage"]
            != "base"
        ]
        self.assertEqual(initial_materialized_stages, ["base", "combination"])
        self.assertEqual(report["legal_mass_archive"]["record_count"], 0)
        self.assertEqual(descendant_candidates, [])
        self.assertEqual(
            report["book_lineage_gate"][
                "descendant_without_viable_base_count"
            ],
            1,
        )
        certified_descendants = [
            candidate
            for candidate in certified_pool
            if candidate.source.metadata["book_generation_lineage"]["stage"]
            != "base"
        ]
        self.assertEqual(certified_materialized_stages, ["base", "combination"])
        self.assertEqual(
            certified_report["legal_mass_archive"]["record_count"],
            1,
        )
        self.assertEqual(len(certified_descendants), 1)
        self.assertEqual(
            certified_descendants[0].source.metadata[
                "book_generation_lineage"
            ]["parent_geometry_hash"],
            "geometry-final",
        )
        self.assertEqual(
            certified_report["two_phase_base_vlm"][
                "registered_unique_parent_count"
            ],
            1,
        )
        self.assertEqual(
            certified_report["two_phase_base_vlm"][
                "descendant_generation_count"
            ],
            1,
        )
        reviewed_base = next(
            candidate for candidate in certified_pool
            if candidate.source.metadata["book_generation_lineage"]["stage"]
            == "base"
        )
        self.assertFalse(
            reviewed_base.source.metadata["base_book_vlm_audit"][
                "base_selection_hard_pass"
            ]
        )
        self.assertTrue(
            reviewed_base.source.metadata["base_book_vlm_audit"][
                "descendant_development_hard_pass"
            ]
        )
        self.assertFalse(
            reviewed_base.source.metadata["base_book_vlm_audit"][
                "final_selection_authority"
            ]
        )
        self.assertEqual(
            certified_descendants[0].source.metadata[
                "base_book_vlm_parent_audit"
            ]["critic_actions"],
            ["clarify_primary_gesture"],
        )
        self.assertEqual(no_review_pool, [])
        self.assertEqual(
            no_review_report["two_phase_base_vlm"][
                "registered_unique_parent_count"
            ],
            0,
        )
        self.assertFalse(any(
            candidate.source.metadata["book_generation_lineage"]["stage"]
            != "base"
            for candidate in legal_false_pool
        ))
        self.assertEqual(
            legal_false_report["two_phase_base_vlm"][
                "registered_unique_parent_count"
            ],
            0,
        )
        self.assertEqual(
            conflict_report["two_phase_base_vlm"][
                "conflicting_parent_count"
            ],
            1,
        )
        self.assertFalse(any(
            candidate.source.metadata["book_generation_lineage"]["stage"]
            != "base"
            for candidate in conflict_pool
        ))

    def test_llm_selected_base_is_returned_once(self):
        base, descendant = self._principles()
        scheduled = ((0, base), (1, descendant))

        selected = candidate_generation._principles_for_seed(
            scheduled,
            seed_index=0,
            llm_authored_seed=True,
            selected_principle_ids=frozenset({base["principle_id"]}),
        )

        self.assertEqual(selected, (scheduled[0],))

    def test_descendant_probe_enumerates_distinct_book_kinds_for_base(self):
        base, descendant = self._principles()
        descendants = tuple(
            (
                index,
                {
                    **descendant,
                    "principle_id": f"book:descendant:{index}",
                    "kind": kind,
                },
            )
            for index, kind in enumerate(
                ("combination", "case", "operative", "combination"),
                start=1,
            )
        )
        scheduled = ((0, base), *descendants)

        selected = candidate_generation._principles_for_seed(
            scheduled,
            seed_index=0,
            llm_authored_seed=True,
            selected_principle_ids=frozenset({
                base["principle_id"],
                *(item[1]["principle_id"] for item in descendants),
            }),
            descendant_probe_count=3,
        )

        self.assertEqual(selected[0], scheduled[0])
        self.assertEqual(len(selected), 4)
        self.assertEqual(
            {item[1]["kind"] for item in selected[1:]},
            {"combination", "case", "operative"},
        )

    def test_llm_selected_descendant_fails_closed_without_scheduled_base(self):
        _base, descendant = self._principles()
        scheduled = ((1, descendant),)

        selected = candidate_generation._principles_for_seed(
            scheduled,
            seed_index=0,
            llm_authored_seed=True,
            selected_principle_ids=frozenset({descendant["principle_id"]}),
        )

        self.assertEqual(selected, ())

    def test_descendant_binds_exact_compiler_clean_base_geometry_hash(self):
        observe = getattr(
            candidate_generation,
            "_observe_compiler_clean_base_geometry_hash",
            lambda *_args: None,
        )
        bind = getattr(
            candidate_generation,
            "_bind_parent_geometry_hash",
            lambda lineage, _bindings: dict(lineage),
        )
        bindings = {}
        lineage = {
            "stage": "combination",
            "parent_key": "seed:scope:base:variant",
            "geometry_hash": "descendant-geometry-hash",
        }

        observe(bindings, "seed:scope:base:variant", "base-geometry-hash")
        observe(bindings, "seed:scope:base:variant", "base-geometry-hash")

        self.assertEqual(
            bind(lineage, bindings),
            {
                "stage": "combination",
                "parent_key": "seed:scope:base:variant",
                "geometry_hash": "descendant-geometry-hash",
                "parent_geometry_hash": "base-geometry-hash",
            },
        )

    def test_descendant_without_compiler_clean_base_has_no_geometry_binding(self):
        bind = getattr(
            candidate_generation,
            "_bind_parent_geometry_hash",
            lambda lineage, _bindings: dict(lineage),
        )
        lineage = {
            "stage": "combination",
            "parent_key": "seed:scope:base:variant",
            "geometry_hash": "descendant-geometry-hash",
        }

        bound = bind(lineage, {})

        self.assertNotIn("parent_geometry_hash", bound)

    def test_conflicting_base_geometry_hashes_make_binding_unavailable(self):
        observe = getattr(
            candidate_generation,
            "_observe_compiler_clean_base_geometry_hash",
            lambda *_args: None,
        )
        bind = getattr(
            candidate_generation,
            "_bind_parent_geometry_hash",
            lambda lineage, _bindings: dict(lineage),
        )
        bindings = {}
        lineage = {
            "stage": "combination",
            "parent_key": "seed:scope:base:variant",
        }

        observe(bindings, "seed:scope:base:variant", "base-geometry-hash-a")
        observe(bindings, "seed:scope:base:variant", "base-geometry-hash-b")

        self.assertNotIn("parent_geometry_hash", bind(lineage, bindings))


if __name__ == "__main__":
    import unittest

    unittest.main()
