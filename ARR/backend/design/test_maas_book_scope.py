"""Regression contracts for BOOK p.3 relative-volume materialization."""

from django.test import SimpleTestCase
from shapely.affinity import rotate
from shapely.geometry import Polygon, box

from design.maas.book_language.semantics import BASE_VOLUME_FRACTIONS
from design.maas.grammar.verb_sequence import VerbCall
from design.maas.program_massing import (
    compose_program_with_book_operations,
    materialize_book_scope,
    program_seed_sequences,
    projection_scope,
)
from design.maas.source_geometry import compile_sequence_to_source_mass


class MaasBookScopeTest(SimpleTestCase):
    def test_all_six_book_base_volumes_materialize_inside_oblique_host(self):
        host = rotate(box(0, 0, 80, 30), 23, origin="centroid")
        measured = []
        for label, fraction in BASE_VOLUME_FRACTIONS:
            scope = materialize_book_scope(host, projection_scope(label, "long_axis"))
            self.assertLessEqual(scope.footprint.difference(host).area, 1e-6)
            self.assertAlmostEqual(scope.requested_fraction, fraction, places=6)
            self.assertAlmostEqual(scope.measured_plan_fraction, fraction, delta=0.015)
            measured.append(round(scope.measured_plan_fraction, 4))
        self.assertEqual(len(set(measured)), 6)

    def test_scope_clips_to_concave_host_without_bridging_the_void(self):
        host = Polygon(((0, 0), (60, 0), (60, 20), (28, 20), (28, 48), (0, 48)))
        scope = materialize_book_scope(host, projection_scope("3/8", "short_axis"))

        self.assertLessEqual(scope.footprint.difference(host).area, 1e-6)
        self.assertGreater(scope.footprint.area, 1.0)

    def test_program_projection_records_and_materializes_scope_graph(self):
        host = box(0, 0, 60, 40)
        seed = program_seed_sequences("gymnasium")[0]
        sources = []
        for label, _fraction in BASE_VOLUME_FRACTIONS:
            sequence = compose_program_with_book_operations(
                seed,
                (VerbCall("carve", {}),),
                base_volume_label=label,
                orientation="long_axis",
            )
            source = compile_sequence_to_source_mass(host, sequence)
            self.assertIsNotNone(source)
            evidence = source.metadata["program_book_projection_evidence"]
            self.assertEqual(evidence["scope"]["base_volume_label"], label)
            self.assertEqual(evidence["projection_graph"]["nodes"][1]["operation"], "select_book_scope")
            self.assertLessEqual(source.footprint.difference(host).area, 1e-6)
            projected = next(
                volume for volume in source.volumes
                if "__book_carve" in volume.role
            )
            sources.append(round(projected.footprint.area, 3))
        self.assertEqual(len(set(sources)), 6)

    def test_vertical_scope_is_recorded_as_section_fraction(self):
        scope = materialize_book_scope(box(0, 0, 60, 40), projection_scope("1/4", "vertical"))

        self.assertEqual(scope.measured_plan_fraction, 1.0)
        self.assertEqual(scope.height_fraction, 0.25)

    def test_vertical_sixteenth_preserves_lower_program_host_and_edits_top_band(self):
        host = box(0, 0, 60, 40)
        seed = program_seed_sequences("gymnasium")[0]
        sequence = compose_program_with_book_operations(
            seed,
            (VerbCall("taper", {}),),
            base_volume_label="1/16",
            orientation="vertical",
        )
        source = compile_sequence_to_source_mass(host, sequence)

        self.assertIsNotNone(source)
        evidence = source.metadata["program_book_projection_evidence"]
        self.assertEqual(evidence["retained_vertical_host_volume_count"], 1)
        lower = next(volume for volume in source.volumes if "__book_host" in volume.role)
        upper = next(volume for volume in source.volumes if "__book_taper" in volume.role)
        self.assertAlmostEqual(lower.bottom_fraction, 0.0)
        self.assertAlmostEqual(lower.top_fraction, 15.0 / 16.0)
        self.assertGreaterEqual(upper.bottom_fraction, lower.top_fraction)
        self.assertGreater(upper.top_fraction, upper.bottom_fraction)
        self.assertLessEqual(upper.top_fraction, 1.0)
        self.assertLessEqual(len(source.volumes), 5)
        self.assertTrue(source.signature()["coherence_evidence"]["hard_pass"])

    def test_neighborhood_program_seeds_keep_all_six_scopes_in_typed_projection(self):
        host = box(0, 0, 60, 40)
        seeds = program_seed_sequences("근린생활시설")
        self.assertEqual(len(seeds), 4)
        for seed in seeds:
            measured = []
            for label, _fraction in BASE_VOLUME_FRACTIONS:
                sequence = compose_program_with_book_operations(
                    seed,
                    (VerbCall("carve", {}),),
                    base_volume_label=label,
                    orientation="long_axis",
                )
                source = compile_sequence_to_source_mass(host, sequence)
                self.assertIsNotNone(source, seed.name)
                evidence = source.metadata["program_book_projection_evidence"]
                self.assertEqual(evidence["status"], "materialized", seed.name)
                self.assertEqual(evidence["scope"]["base_volume_label"], label, seed.name)
                self.assertEqual(
                    evidence["projection_graph"]["nodes"][1]["operation"],
                    "select_book_scope",
                    seed.name,
                )
                self.assertLessEqual(source.footprint.difference(host).area, 1e-6)
                measured.append(round(float(evidence["scope"]["measured_plan_fraction"]), 4))
            self.assertEqual(len(set(measured)), 6, seed.name)
