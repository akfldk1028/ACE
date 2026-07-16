"""Tests for MAAS second-stage preference distillation."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from design.maas.preference.candidate_crops import crop_candidate_images
from design.maas.llm_proposals import _prompt, _stable_hash
from design.maas.preference import build_preference_distillation, build_vlm_generation_feedback, rerank_candidates
from design.maas.preference.harness import export_generation_feedback, run_preference_harness
from design.maas.preference.pairwise_store import PairwisePreference, append_pairwise_label, load_pairwise_labels, pairwise_win_counts
from design.maas.preference.quality_audit import audit_preference_output
from design.maas.preference.reference_corpus import (
    ReferenceItem,
    archdaily_api_collection_dir,
    load_reference_tree,
    match_reference_context,
    write_reference_items,
)
from design.maas.preference.loop import (
    PreferenceLoopCallbacks,
    _opaque_profiled_surface_fill,
    apply_preference_loop,
    preference_loop_config,
    preference_vlm_scored,
)
from design.maas.program_massing.language_quality import assess_language_geometry
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import _feature as _program_feature
from design.maas.program_massing.vlm_a2a import _sequence_from_record, _sequence_record, _vlm_cache_key
from design.maas.selection.preference_guards import (
    PreferenceGuardCallbacks,
    clean_mass_failures,
    enforce_final_vlm_preference_minimum,
)
from design.maas.legal_mesh_optimizer import (
    _architectural_order_gate,
    _design_review_quality_key,
    _formal_principle,
    _has_review_source_geometry,
    _is_direct_openai_llm_candidate,
    _is_plain_capacity_anchor,
    _is_reviewable_architectural_mass,
    _research_mass_language,
    _source_family,
)
from design.maas.selection import final_mass_stage_parking_pass
from design.maas.evolution.critic_loop import _mutations, run_critic_geometry_loop
from design.maas.grammar.component_graph import MassComponentGraph, MassComponentNode, graph_from_sequence
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.morphology_operators import MorphologyVariant
from design.maas.source_geometry.coherence import evaluate_source_volume_coherence
from design.maas.source_geometry.compiler import _array_units, compile_component_graph_to_source_mass, compile_sequence_to_source_mass
from design.maas.source_geometry.ir import SourceVolume
from design.maas.source_geometry.parametric_curves import catmull_rom_path, swept_ribbon
from design.maas.source_geometry.design_fields import build_ribbon_design_field
from shapely.affinity import rotate
from shapely.geometry import box


class MaasPreferenceDistillationTest(TestCase):
    def test_profiled_program_and_recursive_surfaces_share_opaque_preview_material(self):
        gable_roof = [[0.0, 0.0, 0.5], [5.0, 0.0, 1.0], [5.0, 8.0, 1.0], [0.0, 8.0, 0.5]]
        recursive_triangle = [[0.0, 0.0, 0.5], [5.0, 0.0, 1.0], [5.0, 8.0, 1.0]]

        program_fill = _opaque_profiled_surface_fill(gable_roof)
        recursive_fill = _opaque_profiled_surface_fill(recursive_triangle)

        self.assertEqual(program_fill, recursive_fill)
        self.assertEqual(program_fill[3], 255)

    def test_vlm_cache_key_ignores_archive_name_for_identical_executable_geometry(self):
        calls = (VerbCall("base", {}), VerbCall("bar", {"axis": "x", "factor": 0.62}))
        first = VerbSequence("original", "original", calls)
        restored = VerbSequence("llm_accepted_seed_original", "accepted", calls)
        first_mass = compile_sequence_to_source_mass(box(0, 0, 30, 18), first)
        restored_mass = compile_sequence_to_source_mass(box(0, 0, 30, 18), restored)

        first_key = _vlm_cache_key(SimpleNamespace(source=first_mass), [], model="test-vlm")
        restored_key = _vlm_cache_key(SimpleNamespace(source=restored_mass), [], model="test-vlm")

        self.assertEqual(first_key, restored_key)

    def test_vlm_cache_key_changes_with_visual_site_boundary(self):
        sequence = VerbSequence(
            "site_cache_key",
            "site cache key",
            (VerbCall("base", {}), VerbCall("bar", {"axis": "x", "factor": 0.62})),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 30, 18), sequence)
        first = SimpleNamespace(
            source=source,
            feature={"properties": {"site_boundary_geometry": box(0, 0, 30, 18).__geo_interface__}},
        )
        second = SimpleNamespace(
            source=source,
            feature={"properties": {"site_boundary_geometry": box(0, 0, 24, 22).__geo_interface__}},
        )

        self.assertNotEqual(
            _vlm_cache_key(first, [], model="test-vlm"),
            _vlm_cache_key(second, [], model="test-vlm"),
        )

        east_access = SimpleNamespace(
            source=source,
            feature={"properties": {
                "site_boundary_geometry": box(0, 0, 30, 18).__geo_interface__,
                "site_access_context": {"primary_access_edge": "east"},
                "site_access_geometry": {
                    "type": "LineString",
                    "coordinates": [[30.0, 0.0], [30.0, 18.0]],
                },
            }},
        )
        west_access = SimpleNamespace(
            source=source,
            feature={"properties": {
                "site_boundary_geometry": box(0, 0, 30, 18).__geo_interface__,
                "site_access_context": {"primary_access_edge": "west"},
                "site_access_geometry": {
                    "type": "LineString",
                    "coordinates": [[0.0, 0.0], [0.0, 18.0]],
                },
            }},
        )
        self.assertNotEqual(
            _vlm_cache_key(east_access, [], model="test-vlm"),
            _vlm_cache_key(west_access, [], model="test-vlm"),
        )

    def test_array_units_allocate_separated_cells_instead_of_overlapping_parcel_copies(self):
        site = box(0, 0, 60, 40)

        units = _array_units(site, "x", 4, 0.19, 0.78)

        self.assertEqual(len(units), 4)
        self.assertTrue(all(site.covers(unit) for unit in units))
        self.assertTrue(all(left.disjoint(right) for index, left in enumerate(units) for right in units[index + 1:]))
        self.assertGreater(sum(unit.area for unit in units) / site.area, 0.45)
        self.assertLess(sum(unit.area for unit in units) / site.area, 0.65)

    def test_replenishment_sequence_round_trip_marks_persisted_accepted_seed(self):
        original = VerbSequence(
            "llm_archive_step",
            "accepted step",
            (VerbCall("base", {}), VerbCall("stack", {"levels": 3})),
            ("formal_principle=stacked_shifted_platforms",),
        )

        restored = _sequence_from_record(_sequence_record(original))

        self.assertIsNotNone(restored)
        self.assertTrue(restored.name.startswith("llm_accepted_seed_"))
        self.assertFalse(restored.name.startswith("llm_accepted_seed_llm_accepted_seed_"))
        self.assertIn("replenishment_accepted_seed=true", restored.notes)
        self.assertEqual(restored.to_list(), original.to_list())

    def test_language_quality_accepts_coherent_step_and_rejects_detached_box_stack(self):
        feature = {
            "properties": {
                "source_signature": {"coherence_evidence": {
                    "hard_pass": True,
                    "small_fragment_count": 0,
                    "redundant_overlap_pair_count": 0,
                    "collision_energy": 0.0,
                }},
                "program_spatial_evidence": {"spatial_role_projection": {}},
            }
        }
        coherent = SimpleNamespace(volumes=(
            SourceVolume("primary_step_ground", box(0, 0, 10, 8), 0.0, 0.42, "stack"),
            SourceVolume("support_step_middle", box(1, 1, 9, 7), 0.38, 0.72, "shift"),
            SourceVolume("support_step_upper", box(2, 2, 8, 6), 0.68, 1.0, "terrace_link"),
        ))
        detached = SimpleNamespace(volumes=(
            SourceVolume("primary_box", box(0, 0, 4, 4), 0.0, 0.42, "stack"),
            SourceVolume("support_box", box(8, 0, 12, 4), 0.38, 0.72, "shift"),
            SourceVolume("support_box_2", box(16, 0, 20, 4), 0.68, 1.0, "terrace_link"),
        ))

        coherent_evidence = assess_language_geometry(coherent, feature, "stepped_capacity")
        detached_evidence = assess_language_geometry(detached, feature, "stepped_capacity")

        self.assertTrue(coherent_evidence["geometry_pass"])
        self.assertGreaterEqual(coherent_evidence["adjacent_plan_overlap_mean"], 0.9)
        self.assertFalse(detached_evidence["geometry_pass"])

    def test_language_quality_counts_interlock_bodies_separately_from_connector(self):
        feature = {
            "properties": {
                "source_signature": {"coherence_evidence": {
                    "hard_pass": True,
                    "small_fragment_count": 0,
                    "redundant_overlap_pair_count": 0,
                    "collision_energy": 0.0,
                }},
                "program_spatial_evidence": {"spatial_role_projection": {}},
            }
        }
        source = SimpleNamespace(volumes=(
            SourceVolume("primary_interlock_bar", box(0, 2, 12, 6), 0.0, 0.46, "interlock"),
            SourceVolume("support_interlock_bar", box(4, 0, 8, 10), 0.40, 0.78, "interlock"),
            SourceVolume("connector_graph_link_bridge", box(3, 4, 9, 5), 0.56, 0.72, "diagonal_connect"),
        ))

        evidence = assess_language_geometry(source, feature, "bridge_interlock")

        self.assertTrue(evidence["geometry_pass"])
        self.assertEqual(evidence["body_count"], 2)
        self.assertEqual(evidence["connector_count"], 1)

    def test_parametric_ribbon_is_continuous_and_clipped(self):
        site = box(0, 0, 30, 18)
        controls = ((1.0, 4.0), (8.0, 9.0), (16.0, 6.0), (23.0, 12.0), (29.0, 8.0))

        path = catmull_rom_path(controls, samples_per_span=3)
        ribbon = swept_ribbon(controls, half_width=1.2, clip=site)

        self.assertGreater(len(path), len(controls))
        self.assertIsNotNone(ribbon)
        self.assertTrue(site.covers(ribbon))
        self.assertGreater(ribbon.area, 40.0)

    def test_ribbon_field_consumes_graph_authored_normalized_controls(self):
        field = build_ribbon_design_field(box(0, 0, 60, 40), {
            "lane_count": 3,
            "lane_width_ratio": 0.065,
            "curvature": 0.14,
            "vertical_mode": "terraced",
            "control_points": [[0.04, 0.22], [0.31, 0.70], [0.69, 0.30], [0.96, 0.76]],
        })

        self.assertIsNotNone(field)
        self.assertEqual(field.evidence["authored_control_point_count"], 4)
        self.assertEqual(field.evidence["vertical_mode"], "terraced")
        self.assertGreater(max(point[1] for point in field.paths[1]) - min(point[1] for point in field.paths[1]), 8.0)

    def test_ribbon_field_follows_rotated_parcel_long_axis(self):
        site = rotate(box(0, 0, 80, 28), 31.0, origin="centroid")

        field = build_ribbon_design_field(site, {
            "lane_count": 3,
            "lane_width_ratio": 0.085,
            "curvature": 0.10,
        })

        self.assertIsNotNone(field)
        self.assertEqual(field.evidence["coordinate_frame"], "minimum_rotated_long_axis")
        self.assertAlmostEqual(abs(field.evidence["dominant_axis_world_degrees"]), 31.0, delta=0.1)
        for path, half_width in zip(field.paths, field.half_widths):
            ribbon = swept_ribbon(path, half_width=half_width, clip=site)
            self.assertIsNotNone(ribbon)
            self.assertTrue(site.covers(ribbon))

    def test_courtyard_open_side_turns_internal_hole_into_access_court(self):
        closed = VerbSequence("closed_court", "closed", (
            VerbCall("base", {}),
            VerbCall("courtyard", {"ratio": 0.30, "open_side": "closed"}),
        ))
        open_south = VerbSequence("open_court", "open", (
            VerbCall("base", {}),
            VerbCall("courtyard", {"ratio": 0.30, "open_side": "south"}),
        ))

        closed_mass = compile_sequence_to_source_mass(box(0, 0, 30, 18), closed)
        open_mass = compile_sequence_to_source_mass(box(0, 0, 30, 18), open_south)

        self.assertIsNotNone(closed_mass)
        self.assertIsNotNone(open_mass)
        self.assertGreater(closed_mass.footprint.area, open_mass.footprint.area)
        self.assertGreater(closed_mass.footprint.intersection(box(13, 0, 17, 1)).area, 0.0)
        self.assertEqual(open_mass.footprint.intersection(box(13, 0, 17, 1)).area, 0.0)

    def test_component_graph_makes_mass_hierarchy_explicit(self):
        sequence = VerbSequence("graph", "graph", (
            VerbCall("base", {}),
            VerbCall("bar", {"factor": 0.72}),
            VerbCall("courtyard", {"ratio": 0.22}),
            VerbCall("bridge", {"axis": "x"}),
        ))
        graph = graph_from_sequence(sequence)

        self.assertEqual(graph.validate(), [])
        self.assertEqual([node.role for node in graph.nodes], ["root", "primary", "void", "connector"])
        self.assertEqual(graph.nodes[2].parent_id, graph.nodes[1].node_id)
        self.assertEqual(graph.to_dict()["schema_version"], "arr.maas.component_graph.v2")

    def test_component_graph_round_trip_preserves_branches_and_relations(self):
        root = MassComponentNode("root", "root", VerbCall("base", {}))
        primary = MassComponentNode(
            "primary_bar", "primary", VerbCall("bar", {"axis": "x", "factor": 0.62}), "root"
        )
        void = MassComponentNode(
            "court", "void", VerbCall("courtyard", {"ratio": 0.24}), "primary_bar", relation="subtract"
        )
        bridge = MassComponentNode(
            "bridge", "connector", VerbCall("bridge", {"axis": "x"}), "primary_bar", relation="connect"
        )
        graph = MassComponentGraph("branched", "branched", (root, primary, void, bridge))

        restored = graph_from_sequence(graph.to_sequence())

        self.assertEqual(restored.validate(), [])
        self.assertEqual(restored.nodes[2].parent_id, "primary_bar")
        self.assertEqual(restored.nodes[3].parent_id, "primary_bar")
        self.assertEqual(restored.nodes[2].relation, "subtract")
        self.assertEqual(restored.nodes[3].relation, "connect")

    def test_coherence_objective_rejects_redundant_overlapping_solids(self):
        footprint = box(0, 0, 10, 10)
        volumes = tuple(
            SourceVolume(f"secondary_helper_{index}", footprint, 0.0, 1.0, "overlap")
            for index in range(4)
        )

        evidence = evaluate_source_volume_coherence(volumes)

        self.assertFalse(evidence["hard_pass"])
        self.assertGreater(evidence["redundant_overlap_pair_count"], 1)
        self.assertLess(evidence["score"], 0.62)

    def test_graph_parent_relation_changes_compiled_geometry(self):
        root = MassComponentNode("root", "root", VerbCall("base", {}))
        primary = MassComponentNode(
            "primary_bar", "primary", VerbCall("bar", {"axis": "x", "factor": 0.52}), "root"
        )
        notch_on_primary = MassComponentNode(
            "void_notch", "void", VerbCall("notch", {"corner": "+x+y", "ratio": 0.28}), "primary_bar"
        )
        notch_on_root = MassComponentNode(
            "void_notch", "void", VerbCall("notch", {"corner": "+x+y", "ratio": 0.28}), "root"
        )
        child_graph = MassComponentGraph("child", "child", (root, primary, notch_on_primary))
        root_graph = MassComponentGraph("root_target", "root target", (root, primary, notch_on_root))

        child_mass = compile_component_graph_to_source_mass(box(0, 0, 20, 12), child_graph)
        root_mass = compile_component_graph_to_source_mass(box(0, 0, 20, 12), root_graph)

        self.assertIsNotNone(child_mass)
        self.assertIsNotNone(root_mass)
        self.assertNotAlmostEqual(child_mass.footprint.area, root_mass.footprint.area)
        self.assertNotEqual(child_mass.metadata["family"], root_mass.metadata["family"])

    def test_graph_native_branches_are_not_replaced_by_formal_template(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "bar", "primary", VerbCall("bar", {"axis": "x", "factor": 0.68}), "root", constraints=authored
        )
        carved = MassComponentNode(
            "court", "void", VerbCall("courtyard", {"ratio": 0.24}), "bar", constraints=authored, relation="subtract"
        )
        connector = MassComponentNode(
            "link", "connector", VerbCall("diagonal_connect", {"axis": "x", "distance_ratio": 0.12}),
            "bar", constraints=authored, relation="connect",
        )
        graph = MassComponentGraph("llm_branched", "branched", (root, primary, carved, connector))

        mass = compile_component_graph_to_source_mass(box(0, 0, 30, 18), graph)

        self.assertIsNotNone(mass)
        evidence = mass.signature()["graph_materialization_evidence"]
        self.assertEqual(evidence["branching_parent_count"], 1)
        self.assertFalse(evidence["template_name_used"])
        self.assertIn("court", evidence["subtractive_node_ids"])
        self.assertFalse(evidence["cumulative_terminal_states_emitted"])
        self.assertTrue(any("primary_graph" in volume.role for volume in mass.volumes))
        # A subtractive node reshapes its parent; it must never be extruded as
        # a positive "void solid" merely because it is a terminal branch.
        self.assertFalse(any("void_graph" in volume.role for volume in mass.volumes))

    def test_graph_native_root_sibling_void_subtracts_from_primary_mass(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "street_bar", "primary", VerbCall("bar", {"axis": "x", "factor": 0.68}),
            "root", constraints=authored, relation="deform",
        )
        courtyard = MassComponentNode(
            "root_court", "void", VerbCall("courtyard", {"ratio": 0.28}),
            "root", constraints=authored, relation="subtract",
        )
        lift = MassComponentNode(
            "root_lift", "support", VerbCall("lift", {"upper_ratio": 0.76}),
            "root", constraints=authored, relation="attach",
        )
        graph = MassComponentGraph(
            "llm_root_sibling_void", "root sibling void", (root, primary, courtyard, lift),
            notes=("formal_principle=carved_atrium",),
        )

        mass = compile_component_graph_to_source_mass(box(0, 0, 30, 18), graph)

        self.assertIsNotNone(mass)
        evidence = mass.signature()["graph_materialization_evidence"]
        self.assertIn("root_court", evidence["subtractive_node_ids"])
        self.assertIn("root_lift", evidence["consumed_node_ids"])
        self.assertGreaterEqual(sum(len(volume.footprint.interiors) for volume in mass.volumes), 1)
        self.assertLess(max(volume.footprint.area for volume in mass.volumes), 30.0 * 18.0 * 0.68)

    def test_graph_native_array_preserves_cells_and_treats_gap_as_field_void(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "array_primary", "primary",
            VerbCall("array", {"axis": "x", "n": 4, "spacing_ratio": 0.19, "unit_scale": 0.78}),
            "root", constraints=authored,
        )
        courtyard = MassComponentNode(
            "field_void", "void", VerbCall("courtyard", {"ratio": 0.32}),
            "array_primary", constraints=authored, relation="subtract",
        )
        lift = MassComponentNode(
            "height_support", "support", VerbCall("lift", {"upper_ratio": 0.72}),
            "array_primary", constraints=authored, relation="attach",
        )
        graph = MassComponentGraph(
            "llm_array_field", "array field", (root, primary, courtyard, lift),
            notes=("formal_principle=stacked_shifted_platforms",),
        )

        mass = compile_component_graph_to_source_mass(box(0, 0, 60, 40), graph)

        self.assertIsNotNone(mass)
        self.assertEqual(len(mass.volumes), 4)
        self.assertTrue(all("_unit_" in volume.role for volume in mass.volumes))
        evidence = mass.signature()["coherence_evidence"]
        self.assertTrue(evidence["intentional_cluster_exception"])
        self.assertTrue(evidence["hard_pass"])
        self.assertEqual(evidence["plan_component_count"], 4)
        self.assertIn("field_void", mass.signature()["graph_materialization_evidence"]["consumed_node_ids"])
        self.assertIn("height_support", mass.signature()["graph_materialization_evidence"]["consumed_node_ids"])
        feature = _program_feature(
            mass, graph.to_sequence(), building_type="neighborhood living",
            height=15.0, floors=5, site_area=2400.0,
        )
        program = attach_program_massing_evidence(feature, building_type="neighborhood living")
        self.assertTrue(program["hard_pass"])
        self.assertGreaterEqual(feature["properties"]["program_spatial_evidence"]["dominant_ratio_score"], 0.55)

    def test_graph_native_split_materializes_two_clean_bodies_and_elevated_connector(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "split_primary", "primary",
            VerbCall("split", {"axis": "x", "gap_ratio": 0.18, "bridge_ratio": 0.22}),
            "root", constraints=authored,
        )
        connector = MassComponentNode(
            "raised_link", "connector",
            VerbCall("diagonal_connect", {"axis": "x", "angle": 24.0}),
            "split_primary", constraints=authored, relation="connect",
        )
        support = MassComponentNode(
            "section_support", "support", VerbCall("stack", {"levels": 4}),
            "split_primary", constraints=authored, relation="attach",
        )
        graph = MassComponentGraph(
            "llm_split_bridge", "split bridge", (root, primary, connector, support),
            notes=("formal_principle=split_bridge_connector",),
        )

        mass = compile_component_graph_to_source_mass(box(0, 0, 60, 40), graph)

        self.assertIsNotNone(mass)
        self.assertEqual(sum("_body_" in volume.role for volume in mass.volumes), 2)
        self.assertEqual(sum("bridge" in volume.role for volume in mass.volumes), 1)
        self.assertTrue(mass.signature()["coherence_evidence"]["hard_pass"])
        feature = _program_feature(
            mass, graph.to_sequence(), building_type="neighborhood living",
            height=15.0, floors=5, site_area=2400.0,
        )
        attach_program_massing_evidence(feature, building_type="neighborhood living")
        quality = assess_language_geometry(mass, feature, "bridge_interlock")
        self.assertTrue(quality["geometry_pass"])
        self.assertEqual(quality["body_count"], 2)
        self.assertEqual(quality["elevated_connector_count"], 1)

    def test_graph_native_interlock_preserves_two_crossing_height_banded_bodies(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "cross_primary", "primary",
            VerbCall("interlock", {"angle": 32.0, "bar_ratio": 0.66}),
            "root", constraints=authored,
        )
        support = MassComponentNode(
            "stack_support", "support", VerbCall("stack", {"levels": 4}),
            "cross_primary", constraints=authored, relation="attach",
        )
        graph = MassComponentGraph(
            "llm_interlock", "cross interlock", (root, primary, support),
            notes=("formal_principle=split_bridge_connector",),
        )

        mass = compile_component_graph_to_source_mass(box(0, 0, 60, 40), graph)

        self.assertIsNotNone(mass)
        self.assertEqual(len(mass.volumes), 2)
        self.assertTrue(all("_body_" in volume.role for volume in mass.volumes))
        self.assertNotEqual(mass.volumes[0].bottom_fraction, mass.volumes[1].bottom_fraction)
        self.assertTrue(mass.signature()["coherence_evidence"]["hard_pass"])
        feature = _program_feature(
            mass, graph.to_sequence(), building_type="neighborhood living",
            height=15.0, floors=5, site_area=2400.0,
        )
        attach_program_massing_evidence(feature, building_type="neighborhood living")
        quality = assess_language_geometry(mass, feature, "bridge_interlock")
        self.assertTrue(quality["geometry_pass"])
        self.assertGreaterEqual(quality["interlock_pair_count"], 1)

    def test_graph_native_primary_verb_drives_profiled_surface_materialization(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "folded_primary",
            "primary",
            VerbCall("sloped_roof_mass", {"axis": "x", "factor": 0.68}),
            "root",
            constraints=authored,
        )
        graph = MassComponentGraph(
            "llm_graph_folded",
            "graph authored folded mass",
            (root, primary),
            notes=("formal_principle=folded_section",),
        )

        mass = compile_component_graph_to_source_mass(box(0, 0, 30, 18), graph)

        self.assertIsNotNone(mass)
        self.assertTrue(any(volume.verb == "sloped_roof_mass" for volume in mass.volumes))
        roofs = [surface for surface in mass.surfaces if surface.surface_type == "profiled_formal_roof"]
        self.assertGreaterEqual(len(roofs), 1)
        self.assertTrue(all(len({round(vertex[2], 4) for vertex in roof.vertices_m}) >= 2 for roof in roofs))
        self.assertTrue(mass.signature()["continuous_surface_evidence"]["hard_pass"])

    def test_graph_support_chain_materializes_as_section_bands_not_cumulative_boxes(self):
        authored = {"inside_legal_envelope": True, "author_graph_native": True}
        root = MassComponentNode("root", "root", VerbCall("base", {}), constraints=authored)
        primary = MassComponentNode(
            "primary", "primary", VerbCall("bar", {"axis": "x", "factor": 0.82}),
            "root", constraints=authored,
        )
        taper = MassComponentNode(
            "taper", "support", VerbCall("taper", {"x_ratio": 0.74, "y_ratio": 0.82}),
            "primary", constraints=authored, relation="deform",
        )
        roof = MassComponentNode(
            "roof", "support", VerbCall("sloped_roof_mass", {"x_ratio": 0.58, "y_ratio": 0.76}),
            "taper", constraints=authored, relation="deform",
        )
        graph = MassComponentGraph(
            "llm_section_chain", "section chain", (root, primary, taper, roof),
            notes=("formal_principle=folded_section",),
        )

        mass = compile_component_graph_to_source_mass(box(0, 0, 30, 18), graph)

        self.assertIsNotNone(mass)
        self.assertEqual(len(mass.volumes), 3)
        self.assertEqual(
            [(round(volume.bottom_fraction, 2), round(volume.top_fraction, 2)) for volume in mass.volumes],
            [(0.0, 0.42), (0.38, 0.72), (0.68, 1.0)],
        )
        self.assertEqual([volume.verb for volume in mass.volumes], ["bar", "taper", "sloped_roof_mass"])
        evidence = mass.signature()["graph_materialization_evidence"]
        self.assertFalse(evidence["cumulative_terminal_states_emitted"])
        self.assertIn("taper", evidence["consumed_node_ids"])
        self.assertIn("roof", evidence["consumed_node_ids"])

    def test_executable_family_prevents_false_folded_principle_collapse(self):
        sequence = VerbSequence(
            "llm_branch_declared_folded",
            "branch",
            (VerbCall("base", {}), VerbCall("branch", {"angle": 34.0, "trunk_ratio": 0.3, "arm_ratio": 0.2})),
            ("formal_principle=folded_section",),
        )

        mass = compile_sequence_to_source_mass(box(0, 0, 20, 12), sequence)

        self.assertIsNotNone(mass)
        self.assertEqual(mass.metadata["family"], "branch")
        self.assertEqual(mass.metadata["formal_principle"], "torqued_stack")

    def _feature(self, variant_id="maas_01", family="courtyard", score=0.7):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [127.0, 37.0],
                    [127.0001, 37.0],
                    [127.0001, 37.0001],
                    [127.0, 37.0001],
                    [127.0, 37.0],
                ]],
            },
            "properties": {
                "variant_id": variant_id,
                "mass_shape": f"llm_{family}",
                "operator_family": family,
                "far": 35.0,
                "bcr": 25.0,
                "height": 8.4,
                "far_utilization": 0.72,
                "bcr_utilization": 0.45,
                "diversity_score": 0.5,
                "geometry_resolution": {"status": "source_geometry_used"},
                "mass_volumes": [
                    {
                        "bottom_height": 0.0,
                        "top_height": 2.8,
                        "role": "base",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.0, 37.0],
                                [127.0001, 37.0],
                                [127.0001, 37.0001],
                                [127.0, 37.0001],
                                [127.0, 37.0],
                            ]],
                        },
                    },
                    {
                        "bottom_height": 2.8,
                        "top_height": 5.6,
                        "role": "body",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.00002, 37.00001],
                                [127.0001, 37.00001],
                                [127.00009, 37.00009],
                                [127.00002, 37.00009],
                                [127.00002, 37.00001],
                            ]],
                        },
                    },
                    {
                        "bottom_height": 5.6,
                        "top_height": 8.4,
                        "role": "top",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [127.00003, 37.00002],
                                [127.00009, 37.00002],
                                [127.00008, 37.00008],
                                [127.00003, 37.00008],
                                [127.00003, 37.00002],
                            ]],
                        },
                    },
                ],
                "source_signature": {
                    "family": family,
                    "formal_principle": "carved_atrium" if family == "courtyard" else "split_bridge_connector",
                    "primary_language": family,
                    "secondary_language": "void",
                    "surface_count": 24,
                    "volume_count": 4,
                    "rule_evidence": {"generator_mode": "subtractive"},
                },
                "visual_diversity_evidence": {
                    "mass_language": family,
                    "volume_count": 4,
                    "hole_count": 1 if family == "courtyard" else 0,
                },
                "orderliness_evidence": {
                    "schema_version": "arr.maas.orderliness.v1",
                    "orderliness_score": score,
                    "main_mass_area_ratio": 0.55,
                },
                "architectural_ambition_evidence": {
                    "schema_version": "arr.maas.architectural_ambition.v1",
                    "architecture_grade_pass": True,
                    "formal_principle": "carved_atrium" if family == "courtyard" else "split_bridge_connector",
                    "dominant_gesture": "void-defined mass",
                    "silhouette_strength": 0.78,
                    "sectional_diagram_clarity": 0.75,
                },
                "repair_delta": {
                    "schema_version": "arr.maas.repair_delta.v1",
                    "area_retention": 0.94,
                    "scope": "legal_footprint",
                },
                "parking_precheck": {
                    "layout_candidate": {
                        "status": "needs_mechanical_parking_review",
                        "mass_stage_parking": {"status": "pass"},
                    }
                },
            },
        }

    def _loop_callbacks(self):
        return PreferenceLoopCallbacks(
            design_review_quality_key=_design_review_quality_key,
            final_mass_stage_parking_pass=final_mass_stage_parking_pass,
            has_review_source_geometry=_has_review_source_geometry,
            is_plain_capacity_anchor=_is_plain_capacity_anchor,
            is_reviewable_architectural_mass=_is_reviewable_architectural_mass,
            source_family=_source_family,
        )

    def _guard_callbacks(self):
        return PreferenceGuardCallbacks(
            architectural_order_gate=_architectural_order_gate,
            design_review_quality_key=_design_review_quality_key,
            final_mass_stage_parking_pass=final_mass_stage_parking_pass,
            formal_principle=_formal_principle,
            has_review_source_geometry=_has_review_source_geometry,
            is_direct_openai_llm_candidate=_is_direct_openai_llm_candidate,
            is_plain_capacity_anchor=_is_plain_capacity_anchor,
            is_reviewable_architectural_mass=_is_reviewable_architectural_mass,
            preference_vlm_scored=preference_vlm_scored,
            research_mass_language=_research_mass_language,
            source_family=_source_family,
        )

    def test_build_preference_distillation_preserves_hard_gates(self):
        evidence = build_preference_distillation(self._feature())

        self.assertEqual(evidence["schema_version"], "arr.maas.preference_distill.v1")
        self.assertEqual(evidence["mode"], "vlm_ready_geometry_proxy")
        self.assertTrue(evidence["hard_gates"]["legal_gate_preserved"])
        self.assertTrue(evidence["hard_gates"]["parking_mass_stage_gate_preserved"])
        self.assertEqual(len(evidence["concept_scores"]), 6)

    def test_same_run_critic_loop_mutates_rescores_and_accepts_improvement(self):
        parent = self._feature(variant_id="parent")
        parent["properties"]["mass_shape"] = "llm_parent"
        parent["properties"]["maas_verb_sequence"] = [
            {"verb": "base", "params": {}},
            {"verb": "overlap", "params": {"slab_ratio": 0.4}},
            {"verb": "terrace_link", "params": {"upper_ratio": 0.8}},
            {"verb": "shift", "params": {"distance_ratio": 0.1}},
        ]
        parent["properties"]["preference_distillation"] = {
            "mode": "vlm_scored",
            "vlm_status": "scored",
            "critic_actions": ["too_fragmented"],
        }
        parent["properties"]["critic_test_score"] = 1

        def interpret(_base, sequence):
            return MorphologyVariant(
                operator=sequence.name,
                footprint=box(0, 0, 10, 10),
                notes=sequence.notes,
                verb_sequence=tuple(sequence.to_list()),
            )

        def evaluate(variant):
            return {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "mass_shape": variant.operator,
                    "critic_test_score": 0,
                    "maas_verb_sequence": list(variant.verb_sequence),
                },
            }

        def rescore(children):
            for child in children:
                child["properties"]["critic_test_score"] = 2

        result = run_critic_geometry_loop(
            base_footprint=box(0, 0, 10, 10),
            scored_features=[parent],
            interpret=interpret,
            evaluate=evaluate,
            rescore=rescore,
            quality_key=lambda feature: (float(feature["properties"].get("critic_test_score") or 0),),
            max_generations=1,
        )

        self.assertEqual(len(result.accepted), 1)
        self.assertEqual(result.trace["accepted_child_count"], 1)
        self.assertEqual(result.trace["status"], "accepted_revisions")
        self.assertEqual(
            result.accepted[0]["properties"]["critic_revision_evidence"]["critic_actions"],
            ["too_fragmented"],
        )

    def test_box_bias_vlm_action_becomes_continuous_geometry_mutation(self):
        parent = VerbSequence(
            "box_parent",
            "box parent",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("stack", {"levels": 3, "upper_ratio": 0.76}),
            ),
        )
        mutations = _mutations(parent, ["too_box_like", "needs_profiled_surface"], 1)
        ribbon = next(sequence for sequence in mutations if any(call.verb == "bend" for call in sequence.calls))
        source = compile_sequence_to_source_mass(box(0, 0, 42, 30), ribbon)

        self.assertIsNotNone(source)
        evidence = source.signature()["continuous_surface_evidence"]
        self.assertTrue(evidence["hard_pass"])
        self.assertEqual(evidence["principle"], "continuous_ribbon_field")

    def test_clean_mass_gate_rejects_surface_and_volume_fragmentation(self):
        feature = self._feature()
        feature["properties"]["architectural_ambition_evidence"]["implemented_volume_roles"] = [
            "primary", "secondary", "support",
        ]
        feature["properties"]["source_signature"]["surface_count"] = 37
        feature["properties"]["mass_volumes"] *= 2

        passed, issues = _architectural_order_gate(feature)
        failures = clean_mass_failures(feature)

        self.assertFalse(passed)
        self.assertIn("over_complex_source_surfaces", issues)
        self.assertIn("too_many_visible_volumes", issues)
        self.assertEqual(failures["surface_over"], 1)
        self.assertEqual(failures["volume_over"], 1)

    def test_clean_mass_quality_key_beats_vlm_scored_fragmented_mass(self):
        clean = self._feature(variant_id="clean")
        noisy = self._feature(variant_id="noisy")
        for feature in (clean, noisy):
            feature["properties"]["architectural_ambition_evidence"]["implemented_volume_roles"] = [
                "primary", "secondary", "support",
            ]
        noisy["properties"]["source_signature"]["surface_count"] = 68
        noisy["properties"]["mass_volumes"] *= 2
        noisy["properties"]["preference_distillation"] = {
            "mode": "vlm_scored", "vlm_status": "scored", "aggregate_score": 0.99,
        }

        self.assertGreater(_design_review_quality_key(clean), _design_review_quality_key(noisy))

    def test_reference_matching_uses_architectural_tags(self):
        feature = self._feature(family="courtyard")
        refs = [
            ReferenceItem(source="hf", source_id="1", title="Courtyard atrium building", tags=("courtyard", "atrium")),
            ReferenceItem(source="hf", source_id="2", title="highway bridge", tags=("infrastructure",)),
        ]

        matches = match_reference_context(feature, refs)

        self.assertEqual(matches[0]["source_id"], "1")
        self.assertIn("courtyard", matches[0]["matched_tags"])

    def test_reference_matching_reserves_image_backed_counterfactual(self):
        feature = self._feature(family="courtyard")
        refs = [
            ReferenceItem(
                source="archdaily_api",
                source_id="similar_1",
                title="Courtyard atrium",
                local_path="courtyard.jpg",
                tags=("courtyard", "atrium"),
            ),
            ReferenceItem(
                source="archdaily_api",
                source_id="similar_2",
                title="Public court",
                local_path="court.jpg",
                tags=("court", "void"),
            ),
            ReferenceItem(
                source="archdaily_api",
                source_id="contrast_1",
                title="Continuous folded ribbon",
                local_path="ribbon.jpg",
                tags=("ribbon", "folded", "terraced", "bend"),
            ),
        ]

        matches = match_reference_context(feature, refs, limit=3)

        self.assertEqual(matches[0]["source_id"], "similar_1")
        self.assertEqual(matches[2]["source_id"], "contrast_1")
        self.assertEqual(matches[2]["selection_role"], "counterfactual")

    def test_reference_signal_changes_precedent_score(self):
        feature = self._feature(family="courtyard")
        without_refs = build_preference_distillation(feature)
        with_refs = build_preference_distillation(feature, reference_matches=[
            {
                "source": "archdaily_api",
                "source_id": "archdaily_1",
                "title": "Courtyard precedent",
                "score": 2,
                "local_path": "reference.jpg",
            }
        ])

        self.assertGreater(
            with_refs["concept_scores"]["precedent_resonance"],
            without_refs["concept_scores"]["precedent_resonance"],
        )
        self.assertGreater(with_refs["distilled_preference_score"], without_refs["distilled_preference_score"])
        self.assertEqual(with_refs["reference_signal"]["matched_reference_count"], 1)

    def test_pairwise_wins_adjust_reranking(self):
        first = self._feature("maas_01", "courtyard", 0.7)
        second = self._feature("maas_02", "split", 0.7)
        first["properties"]["preference_distillation"] = build_preference_distillation(first)
        second["properties"]["preference_distillation"] = build_preference_distillation(second)

        ranked = rerank_candidates([first, second], pairwise_wins={"maas_02": 3}, diversity_reserve=0)

        self.assertEqual(ranked[0]["properties"]["variant_id"], "maas_02")
        self.assertEqual(ranked[0]["properties"]["preference_rerank"]["rank"], 1)

    def test_preference_loop_scores_top_k_and_changes_quality_key(self):
        first = self._feature("maas_01", "courtyard", 0.7)
        second = self._feature("maas_02", "split", 0.7)

        def fake_scorer(**kwargs):
            feature = kwargs["feature"]
            variant_id = feature["properties"]["variant_id"]
            high = variant_id == "maas_02"
            score = 0.95 if high else 0.45
            return {
                "schema_version": "arr.maas.vlm_concept_scores.v1",
                "model": "fake-vlm",
                "concept_scores": {
                    "gesture_clarity": score,
                    "hierarchy": score,
                    "non_stair_silhouette": score,
                    "void_publicness": score,
                    "repair_integrity": score,
                    "precedent_resonance": score,
                },
            }

        artifact = apply_preference_loop(
            [first, second],
            config={
                "enabled": True,
                "require_vlm": True,
                "top_k": 2,
                "parallel_workers": 2,
                "model": "fake-vlm",
                "reference_root": "",
            },
            callbacks=self._loop_callbacks(),
            scorer=fake_scorer,
        )

        self.assertEqual(artifact["vlm_scored_count"], 2)
        self.assertEqual(artifact["parallel_workers"], 2)
        self.assertTrue(preference_vlm_scored(second))
        self.assertGreater(_design_review_quality_key(second), _design_review_quality_key(first))
        self.assertEqual(second["properties"]["preference_distillation"]["mode"], "vlm_scored")

    def test_final_vlm_preference_minimum_replaces_proxy_candidate(self):
        proxy = self._feature("maas_01", "courtyard", 0.7)
        scored = self._feature("maas_02", "split", 0.7)
        proxy["properties"]["mass_shape"] = "proxy_courtyard"
        scored["properties"]["mass_shape"] = "vlm_split"
        scored["properties"]["orderliness_evidence"]["orderliness_score"] = 0.92
        scored["properties"]["architectural_ambition_evidence"]["implemented_volume_roles"] = ["base", "body", "top"]
        scored["properties"]["preference_distillation"] = build_preference_distillation(
            scored,
            vlm_model="fake-vlm",
            vlm_scores={
                "gesture_clarity": 0.9,
                "hierarchy": 0.9,
                "non_stair_silhouette": 0.9,
                "void_publicness": 0.9,
                "repair_integrity": 0.9,
                "precedent_resonance": 0.9,
            },
            vlm_status="scored",
        )

        selected = enforce_final_vlm_preference_minimum(
            [proxy],
            source_pool=[proxy, scored],
            final_limit=1,
            min_count=1,
            callbacks=self._guard_callbacks(),
        )

        self.assertEqual(selected[0]["properties"]["mass_shape"], "vlm_split")
        self.assertTrue(preference_vlm_scored(selected[0]))

    def test_preference_loop_require_vlm_rejects_silent_proxy(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                apply_preference_loop(
                    [self._feature()],
                    config={
                        "enabled": True,
                        "require_vlm": True,
                        "top_k": 1,
                        "model": "fake-vlm",
                        "reference_root": "",
                    },
                    callbacks=self._loop_callbacks(),
                    scorer=None,
                )

    def test_preference_loop_config_defaults_to_top_40(self):
        config = preference_loop_config({"maas_preference_loop": {"enabled": True, "require_vlm": True}})

        self.assertTrue(config["enabled"])
        self.assertEqual(config["top_k"], 40)
        self.assertEqual(config["parallel_workers"], 4)
        self.assertEqual(config["min_final_vlm_scored"], 16)

    def test_harness_merges_reference_and_preference_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            reference_root = root / "reference-corpus"
            refs_path = reference_root / "huggingface" / "metadata.jsonl"
            write_reference_items(refs_path, [
                ReferenceItem(source="hf", source_id="1", title="Courtyard architecture", tags=("courtyard", "atrium")),
            ])
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")

            summary = run_preference_harness(
                input_json=input_json,
                output_json=output_json,
                reference_root=reference_root,
                use_vlm=False,
            )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            props = output["response"]["feature_collection"]["features"][0]["properties"]

        self.assertEqual(summary["reference_count"], 1)
        self.assertEqual(props["preference_distillation"]["schema_version"], "arr.maas.preference_distill.v1")
        self.assertEqual(props["preference_distillation"]["reference_matches"][0]["source_id"], "1")
        self.assertEqual(props["paper_alignment_evidence"]["schema_version"], "arr.maas.paper_alignment.v1")

    def test_harness_loads_structured_archdaily_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            reference_root = root / "reference-corpus"
            collection_dir = archdaily_api_collection_dir(
                reference_root,
                start_path="/projects/categories/houses",
                collection_name="houses_smoke",
            )
            write_reference_items(collection_dir / "metadata.jsonl", [
                ReferenceItem(
                    source="archdaily_api",
                    source_id="archdaily_1",
                    title="Courtyard house precedent",
                    local_path=str(collection_dir / "images" / "archdaily_1.jpg"),
                    tags=("courtyard", "house"),
                ),
            ])
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")

            summary = run_preference_harness(
                input_json=input_json,
                output_json=output_json,
                reference_root=reference_root,
                use_vlm=False,
            )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            matches = output["response"]["feature_collection"]["features"][0]["properties"]["preference_distillation"]["reference_matches"]
            audit = output["response"]["preference_quality_audit"]
            reference_count = len(load_reference_tree(reference_root))

        self.assertEqual(reference_count, 1)
        self.assertEqual(summary["reference_count"], 1)
        self.assertEqual(matches[0]["source"], "archdaily_api")
        self.assertEqual(audit["schema_version"], "arr.maas.preference_quality_audit.v1")

    def test_pairwise_jsonl_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.jsonl"
            append_pairwise_label(path, PairwisePreference(
                preferred_candidate_id="maas_02",
                rejected_candidate_id="maas_01",
                reviewer_id="professor",
            ))
            labels = load_pairwise_labels(path)

        self.assertEqual(len(labels), 1)
        self.assertEqual(pairwise_win_counts(labels, reviewer_id="professor"), {"maas_02": 1})

    def test_harness_records_vlm_failure_as_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            image_path = root / "candidate.png"
            image_path.write_bytes(b"not-a-real-png")
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")
            with patch("design.maas.preference.harness.score_candidate_with_openai_vlm", side_effect=Exception("boom")):
                run_preference_harness(
                    input_json=input_json,
                    output_json=output_json,
                    image_path=image_path,
                    reference_root=root / "reference-corpus",
                    use_vlm=True,
                )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            evidence = output["response"]["feature_collection"]["features"][0]["properties"]["preference_distillation"]

        self.assertEqual(evidence["mode"], "geometry_proxy_fallback")
        self.assertEqual(evidence["vlm_status"], "failed")

    def test_harness_sends_candidate_crop_to_vlm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            image_path = root / "sheet.png"
            crop_dir = root / "crops"
            from PIL import Image

            Image.new("RGB", (900, 420), "#ffffff").save(image_path)
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature("maas_01"), self._feature("maas_02", "split")],
                    }
                }
            }), encoding="utf-8")
            seen_paths = []

            def fake_vlm(**kwargs):
                seen_paths.append(Path(kwargs["image_path"]).name)
                return {
                    "schema_version": "arr.maas.vlm_concept_scores.v1",
                    "model": "fake-vlm",
                    "concept_scores": {
                        "gesture_clarity": 0.8,
                        "hierarchy": 0.8,
                        "non_stair_silhouette": 0.8,
                        "void_publicness": 0.8,
                        "repair_integrity": 0.8,
                        "precedent_resonance": 0.8,
                    },
                }

            with patch("design.maas.preference.harness.score_candidate_with_openai_vlm", side_effect=fake_vlm):
                run_preference_harness(
                    input_json=input_json,
                    output_json=output_json,
                    image_path=image_path,
                    reference_root=root / "reference-corpus",
                    use_vlm=True,
                    candidate_crop_dir=crop_dir,
                )
            output = json.loads(output_json.read_text(encoding="utf-8"))
            by_id = {
                feature["properties"]["variant_id"]: feature["properties"]["preference_distillation"]
                for feature in output["response"]["feature_collection"]["features"]
            }

        self.assertEqual(seen_paths, ["maas_01.png", "maas_02.png"])
        self.assertEqual(by_id["maas_01"]["mode"], "vlm_scored")
        self.assertIn("maas_01.png", by_id["maas_01"]["image_uri"])

    def test_vlm_generation_feedback_extracts_next_generation_brief(self):
        top = self._feature("maas_01", "diagonal_connect", 0.9)
        bottom = self._feature("maas_02", "legal_layered", 0.6)
        top["properties"]["preference_distillation"] = build_preference_distillation(
            top,
            vlm_model="fake-vlm",
            vlm_scores={
                "gesture_clarity": 0.9,
                "hierarchy": 0.85,
                "non_stair_silhouette": 0.85,
                "void_publicness": 0.8,
                "repair_integrity": 0.9,
                "precedent_resonance": 0.9,
            },
            vlm_status="scored",
        )
        bottom["properties"]["mass_shape"] = "legal_layered_max"
        bottom["properties"]["preference_distillation"] = build_preference_distillation(
            bottom,
            vlm_model="fake-vlm",
            vlm_scores={
                "gesture_clarity": 0.6,
                "hierarchy": 0.6,
                "non_stair_silhouette": 0.3,
                "void_publicness": 0.2,
                "repair_integrity": 0.8,
                "precedent_resonance": 0.4,
            },
            vlm_status="scored",
        )
        payload = {
            "feature_collection": {"features": [top, bottom]},
            "preference_quality_audit": {"top_reference_delta_saturated_count": 2, "reference_delta_unique_count": 1},
        }

        feedback = build_vlm_generation_feedback(payload, top_n=1, bottom_n=1)

        self.assertEqual(feedback["schema_version"], "arr.maas.vlm_generation_feedback.v1")
        self.assertIn("diagonal", feedback["must_use"])
        self.assertIn("legal_layered_max", feedback["avoid"])
        self.assertIn("formal_principle_targets", feedback)

    def test_harness_requires_real_vlm_for_feedback_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            output_json = root / "output.json"
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [self._feature()],
                    }
                }
            }), encoding="utf-8")

            with self.assertRaises(RuntimeError):
                run_preference_harness(
                    input_json=input_json,
                    output_json=output_json,
                    reference_root=root / "reference-corpus",
                    use_vlm=False,
                    require_vlm_feedback=True,
                )

    def test_feedback_only_exports_without_rewriting_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "input.json"
            feedback_json = root / "feedback.json"
            feature = self._feature("maas_01", "diagonal_connect", 0.9)
            feature["properties"]["preference_distillation"] = build_preference_distillation(
                feature,
                vlm_model="fake-vlm",
                vlm_scores={
                    "gesture_clarity": 0.9,
                    "hierarchy": 0.85,
                    "non_stair_silhouette": 0.85,
                    "void_publicness": 0.8,
                    "repair_integrity": 0.9,
                    "precedent_resonance": 0.9,
                },
                vlm_status="scored",
            )
            input_json.write_text(json.dumps({
                "response": {
                    "feature_collection": {
                        "type": "FeatureCollection",
                        "features": [feature],
                    }
                }
            }), encoding="utf-8")

            feedback = export_generation_feedback(
                input_json=input_json,
                feedback_json=feedback_json,
                require_vlm_feedback=True,
            )
            after = json.loads(input_json.read_text(encoding="utf-8"))
            feedback_exists = feedback_json.exists()

        self.assertEqual(feedback["vlm_scored_count"], 1)
        self.assertTrue(feedback_exists)
        self.assertEqual(
            after["response"]["feature_collection"]["features"][0]["properties"]["preference_distillation"]["mode"],
            "vlm_scored",
        )

    def test_generation_feedback_changes_llm_prompt_hash(self):
        site_context = {"building_type": "공동주택", "site_area_m2": 100.0, "limits": {"far": 200}}
        feedback = {
            "schema_version": "arr.maas.vlm_generation_feedback.v1",
            "must_use": ["diagonal", "undercut"],
            "avoid": ["legal_layered_max"],
            "quota": {"diagonal_or_split_bridge": 4},
            "formal_principle_targets": ["undercut_tapered_tower"],
        }

        base_hash = _stable_hash(_prompt(site_context, 3, batch_index=1))
        feedback_hash = _stable_hash(_prompt(site_context, 3, batch_index=1, generation_feedback=feedback))

        self.assertNotEqual(base_hash, feedback_hash)

    def test_preference_quality_audit_flags_missing_reference_signal(self):
        feature = self._feature()
        feature["properties"]["preference_distillation"] = build_preference_distillation(feature)
        payload = {"feature_collection": {"features": [feature for _ in range(10)]}}

        audit = audit_preference_output(payload)

        self.assertEqual(audit["status"], "fail")
        self.assertIn("top_reference_coverage_too_low", audit["failures"])
