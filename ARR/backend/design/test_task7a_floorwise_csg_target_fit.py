from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import MultiPolygon, Polygon, box

from design.maas.geometry_language.source_bridge import (
    compile_geometry_program_to_source_mass,
    _floor_target_fit_is_legal,
    _matrix_fit_polygon_to_host,
    materialize_floorwise_legal_source,
)
from design.maas.geometry_language.programs import architectural_shape_programs
from design.maas.geometry_language.floorwise_visual_projection import (
    FloorwiseVisualProjectionCertificate,
)
from design.maas.book_language.candidate_generation import (
    _propagate_terminal_materialization_failure,
)
from design.maas.source_geometry.ir import SourceMass, SourceVolume


class FloorwiseCsgTargetFitContractTest(SimpleTestCase):
    def setUp(self):
        self.source = box(-5.0, -5.0, 5.0, 5.0)
        self.irregular_host = Polygon((
            (0.0, 0.0),
            (12.0, 0.0),
            (12.0, 4.0),
            (8.0, 4.0),
            (8.0, 12.0),
            (0.0, 12.0),
        ))

    def test_irregular_csg_returns_maximum_lower_not_over_target_upper(self):
        evidence = {}

        fitted = _matrix_fit_polygon_to_host(
            self.source,
            self.irregular_host,
            target_area=80.0,
            target_center=(6.0, 6.0),
            allow_legal_csg_projection=True,
            minimum_contained_area_ratio=0.78,
            fit_evidence=evidence,
        )

        self.assertIsNotNone(fitted)
        occupied, _matrix = fitted
        self.assertGreater(occupied.area, 0.0)
        self.assertLessEqual(occupied.area, 80.0)
        self.assertTrue(_floor_target_fit_is_legal(
            achieved_area_m2=occupied.area,
            maximum_legal_area_m2=float(self.irregular_host.area),
        ))
        self.assertTrue(self.irregular_host.buffer(1e-7).covers(occupied))
        self.assertEqual(evidence["fit_mode"], "legal_csg_maximum_lower")
        self.assertLessEqual(evidence["lower_area_m2"], 80.0)
        self.assertGreater(evidence["upper_area_m2"], 80.0)

    def test_csg_does_not_require_seventy_eight_percent_contained_affine_fit(self):
        legal_host = Polygon((
            (-2.0, -6.0),
            (2.0, -6.0),
            (2.0, -2.0),
            (6.0, -2.0),
            (6.0, 2.0),
            (2.0, 2.0),
            (2.0, 6.0),
            (-2.0, 6.0),
            (-2.0, 2.0),
            (-6.0, 2.0),
            (-6.0, -2.0),
            (-2.0, -2.0),
        ))
        evidence = {}

        fitted = _matrix_fit_polygon_to_host(
            self.source,
            legal_host,
            target_area=64.0,
            target_center=(0.0, 0.0),
            allow_legal_csg_projection=True,
            minimum_contained_area_ratio=0.78,
            fit_evidence=evidence,
        )

        self.assertIsNotNone(fitted)
        occupied, _matrix = fitted
        self.assertTrue(_floor_target_fit_is_legal(
            achieved_area_m2=occupied.area,
            maximum_legal_area_m2=float(legal_host.area),
        ))
        self.assertLessEqual(occupied.area, 64.0)
        self.assertTrue(legal_host.buffer(1e-7).covers(occupied))
        self.assertEqual(evidence["fit_mode"], "legal_csg_maximum_lower")
        self.assertGreaterEqual(evidence["lower_scale"], 0.0)
        self.assertLessEqual(evidence["upper_scale"], 8.0)

    def test_exact_target_remains_exact_and_contained(self):
        evidence = {}
        fitted = _matrix_fit_polygon_to_host(
            self.source,
            box(0.0, 0.0, 10.0, 10.0),
            target_area=64.0,
            target_center=(5.0, 5.0),
            allow_legal_csg_projection=True,
            fit_evidence=evidence,
        )

        self.assertIsNotNone(fitted)
        occupied, _matrix = fitted
        self.assertAlmostEqual(occupied.area, 64.0, places=6)
        self.assertTrue(box(0.0, 0.0, 10.0, 10.0).covers(occupied))

    def test_impossible_positive_lower_fails_closed_with_typed_fit_evidence(self):
        evidence = {}
        fitted = _matrix_fit_polygon_to_host(
            self.source,
            Polygon(),
            target_area=64.0,
            allow_legal_csg_projection=True,
            fit_evidence=evidence,
        )

        self.assertIsNone(fitted)
        self.assertEqual(evidence["failure_reason"], "no_positive_lower_projection")

    def test_unreachable_target_returns_largest_positive_underfill(self):
        evidence = {}

        fitted = _matrix_fit_polygon_to_host(
            self.source,
            self.irregular_host,
            target_area=120.0,
            target_center=(6.0, 6.0),
            allow_legal_csg_projection=True,
            minimum_contained_area_ratio=0.0,
            fit_evidence=evidence,
        )

        self.assertIsNotNone(fitted)
        occupied, _matrix = fitted
        self.assertGreater(occupied.area, 110.0)
        self.assertLessEqual(occupied.area, 120.0)
        self.assertTrue(self.irregular_host.buffer(1e-7).covers(occupied))
        self.assertEqual(evidence["fit_mode"], "legal_csg_maximum_lower")
        self.assertAlmostEqual(evidence["lower_area_m2"], occupied.area)
        self.assertLess(evidence["lower_scale"], 8.0)
        self.assertAlmostEqual(
            evidence["best_sampled_lower_area_m2"],
            occupied.area,
        )

    def test_multifloor_materialization_never_overfills_target_total(self):
        targets = (90.0, 72.0)
        fitted_floors = tuple(
            _matrix_fit_polygon_to_host(
                self.source,
                self.irregular_host,
                target_area=target,
                target_center=(6.0, 6.0),
                allow_legal_csg_projection=True,
                minimum_contained_area_ratio=0.78,
                fit_evidence={},
            )
            for target in targets
        )

        self.assertTrue(all(result is not None for result in fitted_floors))
        achieved = sum(result[0].area for result in fitted_floors if result)
        self.assertGreater(achieved, 0.0)
        self.assertLessEqual(achieved, sum(targets) + 1e-6)

    def test_endpoint_floor_union_preserves_valid_disconnected_aggregate(self):
        legal = box(0.0, 0.0, 10.0, 10.0)
        source = compile_geometry_program_to_source_mass(
            architectural_shape_programs()[0],
            legal,
            target_plan_area=36.0,
            name="task7a-connected-authored-source",
        )
        self.assertIsNotNone(source)
        self.assertEqual(
            source.metadata["geometry_program_compilation"]["metrics"][
                "component_count"
            ],
            1,
        )
        endpoint_union = MultiPolygon((
            box(1.0, 1.0, 1.8, 1.8),
            box(3.0, 1.0, 3.8, 1.8),
        ))
        identity_matrix = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
        certificate = FloorwiseVisualProjectionCertificate(
            hard_pass=True,
            status="certified",
            certification_mode="matrix4_authored_surface",
            failure_reasons=(),
        )
        projection = SimpleNamespace(
            certificate=certificate,
            surfaces=source.surfaces,
        )
        original_bridge = source.metadata["geometry_program_bridge_evidence"]
        sink = []

        with patch(
            "design.maas.geometry_language.source_bridge._exact_authored_mesh_section",
            return_value=endpoint_union,
        ), patch(
            "design.maas.geometry_language.source_bridge._matrix_fit_polygon_to_host",
            return_value=(endpoint_union, identity_matrix),
        ), patch(
            "design.maas.geometry_language.floorwise_visual_projection.project_floorwise_visual_mesh",
            return_value=projection,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(legal,),
                target_plan_coverage=0.5,
                floor_capacity_plan_hash="task7a-disconnected-endpoint",
                target_floor_areas_m2=(1.28,),
                terminal_failure_sink=sink,
            )

        self.assertIsNotNone(result, sink)
        self.assertEqual(result.footprint.geom_type, "MultiPolygon")
        self.assertAlmostEqual(result.footprint.area, 1.28, places=6)
        self.assertEqual(len(result.footprint.geoms), 2)
        self.assertEqual(len(result.volumes), 2)
        self.assertTrue(all(
            volume.footprint.area < 1.0 for volume in result.volumes
        ))
        self.assertEqual(result.surfaces, source.surfaces)
        self.assertEqual(
            result.metadata["floorwise_legal_matrix_stack"]["floor_count"],
            1,
        )
        self.assertEqual(
            result.metadata["geometry_program_compilation"]["metrics"][
                "component_count"
            ],
            1,
        )
        result_bridge = result.metadata["geometry_program_bridge_evidence"]
        for key in ("program_hash", "geometry_hash", "surface_payload_hash"):
            self.assertEqual(result_bridge.get(key), original_bridge.get(key))

    def test_floor_union_repair_mutates_empty_caller_diagnostics_on_none(self):
        from design.maas.geometry_language.source_bridge import (
            _repair_polygonal_floor_union,
        )

        diagnostics = {}

        repaired, returned_diagnostics = _repair_polygonal_floor_union(
            Polygon(),
            minimum_area=1.0,
            diagnostics=diagnostics,
        )

        self.assertIsNone(repaired)
        self.assertIs(returned_diagnostics, diagnostics)
        self.assertEqual(diagnostics["geom_type"], "Polygon")
        self.assertIs(diagnostics["is_valid"], True)
        self.assertEqual(diagnostics["validity_reason"], "Valid Geometry")
        self.assertIs(diagnostics["is_empty"], True)
        self.assertEqual(diagnostics["aggregate_area_m2"], 0.0)
        self.assertEqual(diagnostics["component_count"], 0)
        self.assertEqual(diagnostics["largest_polygon_area_m2"], 0.0)
        self.assertEqual(diagnostics["post_repair_geom_type"], "None")
        self.assertEqual(diagnostics["failure_branch"], "input_empty")

    def test_upper_endpoint_positive_taper_below_one_square_meter_is_valid(self):
        legal = box(0.0, 0.0, 10.0, 10.0)
        source = compile_geometry_program_to_source_mass(
            architectural_shape_programs()[0],
            legal,
            target_plan_area=36.0,
            name="task7a-valid-upper-taper",
        )
        self.assertIsNotNone(source)
        certificate = FloorwiseVisualProjectionCertificate(
            hard_pass=True,
            status="certified",
            certification_mode="matrix4_authored_surface",
            failure_reasons=(),
        )
        projection = SimpleNamespace(
            certificate=certificate,
            surfaces=source.surfaces,
        )
        sink = []

        with patch(
            "design.maas.geometry_language.source_bridge._exact_authored_mesh_section",
            return_value=source.footprint,
        ), patch(
            "design.maas.geometry_language.floorwise_visual_projection.project_floorwise_visual_mesh",
            return_value=projection,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(legal, legal),
                target_plan_coverage=0.5,
                floor_capacity_plan_hash="task7a-valid-upper-taper",
                target_floor_areas_m2=(2.0, 0.5),
                terminal_failure_sink=sink,
            )

        self.assertIsNone(result)
        self.assertEqual(
            sink[-1]["evidence"]["failure_reason"],
            "revalidation_floor_section_area_mismatch",
        )
        self.assertFalse(any(
            record.get("evidence", {}).get("failure_reason")
            == "revalidation_floor_union_invalid"
            for record in sink
        ))

    def test_upper_endpoint_positive_area_policy_still_rejects_bad_geometry(self):
        from shapely.geometry import LineString
        from design.maas.geometry_language.source_bridge import (
            _repair_polygonal_floor_union,
        )

        invalid_polygonal_payload = SimpleNamespace(
            geom_type="Polygon",
            is_empty=False,
            is_valid=False,
        )
        cases = (
            (Polygon(), "input_empty"),
            (LineString(((0.0, 0.0), (1.0, 0.0))), "aggregate_missing"),
            (invalid_polygonal_payload, "repair_exception"),
        )

        for geometry, expected_branch in cases:
            with self.subTest(expected_branch=expected_branch):
                repaired, diagnostics = _repair_polygonal_floor_union(
                    geometry,
                    minimum_area=0.0,
                    diagnostics={},
                )
                self.assertIsNone(repaired)
                self.assertEqual(
                    diagnostics["failure_branch"],
                    expected_branch,
                )

    def test_invalid_floor_union_terminal_evidence_is_typed_for_both_endpoints(self):
        legal = box(0.0, 0.0, 10.0, 10.0)
        source = compile_geometry_program_to_source_mass(
            architectural_shape_programs()[0],
            legal,
            target_plan_area=36.0,
            name="task7a-floor-union-diagnostics",
        )
        self.assertIsNotNone(source)
        endpoint_union = MultiPolygon((
            box(1.0, 1.0, 1.5, 1.5),
            box(3.0, 1.0, 3.5, 1.5),
        ))
        identity_matrix = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
        sink = []

        with patch(
            "design.maas.geometry_language.source_bridge._exact_authored_mesh_section",
            return_value=endpoint_union,
        ), patch(
            "design.maas.geometry_language.source_bridge._matrix_fit_polygon_to_host",
            return_value=(endpoint_union, identity_matrix),
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(legal,),
                target_plan_coverage=0.5,
                floor_capacity_plan_hash="task7a-floor-union-diagnostics",
                target_floor_areas_m2=(0.5,),
                terminal_failure_sink=sink,
            )

        self.assertIsNone(result)
        self.assertEqual(len(sink), 1)
        evidence = sink[0]["evidence"]
        self.assertEqual(evidence["failure_reason"], "revalidation_floor_union_invalid")
        for endpoint in ("ground", "upper"):
            self.assertIn(f"{endpoint}_geom_type", evidence)
            self.assertEqual(evidence[f"{endpoint}_geom_type"], "MultiPolygon")
            self.assertIs(evidence[f"{endpoint}_is_valid"], True)
            self.assertEqual(
                evidence[f"{endpoint}_validity_reason"],
                "Valid Geometry",
            )
            self.assertIs(evidence[f"{endpoint}_is_empty"], False)
            self.assertAlmostEqual(
                evidence[f"{endpoint}_aggregate_area_m2"],
                0.5,
                places=6,
            )
            self.assertEqual(evidence[f"{endpoint}_polygon_count"], 2)
            self.assertEqual(evidence[f"{endpoint}_component_count"], 2)
            self.assertAlmostEqual(
                evidence[f"{endpoint}_largest_polygon_area_m2"],
                0.25,
                places=6,
            )
            self.assertEqual(
                evidence[f"{endpoint}_post_repair_geom_type"],
                "MultiPolygon",
            )
            self.assertEqual(
                evidence[f"{endpoint}_failure_branch"],
                (
                    "aggregate_below_minimum_area"
                    if endpoint == "ground"
                    else ""
                ),
            )

    def test_floor_affine_terminal_evidence_preserves_identity_frame_and_bracket(self):
        mass = SourceMass(
            name="task7a-terminal",
            footprint=self.source,
            volumes=(
                SourceVolume("body", self.source, 0.0, 1.0, "geometry_program"),
            ),
            metadata={
                "geometry_program_bridge_evidence": {
                    "program_hash": "program-task7a-terminal",
                    "geometry_family": "llm_slice_notch",
                },
                "book_scope": "1/8",
            },
        )
        sink = []
        fit_evidence = {
            "failure_reason": "no_positive_lower_projection",
            "requested_center_x": 6.0,
            "requested_center_y": 6.0,
            "representative_center_x": 4.0,
            "representative_center_y": 4.0,
            "frame_angle_degrees": 29.0,
            "anisotropy_ratio": 1.4,
            "scale_factor": 1.2,
            "target_area_m2": 90.0,
            "achieved_area_m2": 0.0,
            "lower_scale": 1.0,
            "upper_scale": 1.25,
            "legal_section_hash": "legal-task7a",
        }

        with patch(
            "design.maas.geometry_language.source_bridge._matrix_fit_polygon_to_host",
            side_effect=lambda *args, **kwargs: (
                kwargs["fit_evidence"].update(fit_evidence) or None
            ),
        ):
            result = materialize_floorwise_legal_source(
                mass,
                legal_sections=(self.irregular_host,),
                target_plan_coverage=0.8,
                floor_capacity_plan_hash="capacity-task7a",
                target_floor_areas_m2=(90.0,),
                terminal_failure_sink=sink,
            )

        self.assertIsNone(result)
        self.assertEqual(len(sink), 1)
        terminal = sink[0]
        self.assertEqual(terminal["stage"], "floor_affine_fit")
        evidence = terminal["evidence"]
        self.assertEqual(evidence["failure_reason"], "no_positive_lower_projection")
        self.assertEqual(evidence["program_hash"], "program-task7a-terminal")
        self.assertEqual(evidence["geometry_family"], "llm_slice_notch")
        self.assertEqual(evidence["book_scope"], "1/8")
        self.assertEqual(evidence["floor_index"], 0)
        self.assertNotEqual(evidence["legal_section_hash"], "legal-task7a")
        self.assertEqual(
            evidence["claimed_legal_section_hash"],
            "legal-task7a",
        )
        self.assertIn("requested_center_x", evidence)
        self.assertIn("representative_center_x", evidence)
        self.assertIn("frame_angle_degrees", evidence)
        self.assertIn("anisotropy_ratio", evidence)
        self.assertIn("scale_factor", evidence)
        self.assertIn("target_area_m2", evidence)
        self.assertIn("achieved_area_m2", evidence)
        self.assertIn("lower_scale", evidence)
        self.assertIn("upper_scale", evidence)

    def test_production_multifloor_materialization_preserves_floor_contract(self):
        legal = box(0.0, 0.0, 30.0, 20.0)
        source = compile_geometry_program_to_source_mass(
            architectural_shape_programs()[0],
            legal,
            target_plan_area=180.0,
            name="task7a-production-multifloor",
        )
        self.assertIsNotNone(source)
        targets = (180.0, 180.0, 180.0, 180.0)
        sink = []

        result = materialize_floorwise_legal_source(
            source,
            legal_sections=(legal,) * len(targets),
            target_plan_coverage=0.6,
            floor_capacity_plan_hash="task7a-production-plan",
            target_floor_areas_m2=targets,
            terminal_failure_sink=sink,
        )

        self.assertIsNotNone(result, sink)
        self.assertTrue(result.volumes)
        achieved_by_floor = []
        for floor_index, target in enumerate(targets):
            bottom = floor_index / len(targets)
            top = (floor_index + 1) / len(targets)
            floor_volumes = tuple(
                volume
                for volume in result.volumes
                if abs(volume.bottom_fraction - bottom) <= 1e-9
                and abs(volume.top_fraction - top) <= 1e-9
            )
            self.assertTrue(floor_volumes)
            achieved = sum(volume.footprint.area for volume in floor_volumes)
            achieved_by_floor.append(achieved)
            self.assertGreater(achieved, 0.0)
            self.assertLessEqual(achieved, target + 1e-6)
            self.assertTrue(all(
                legal.buffer(1e-7).covers(volume.footprint)
                for volume in floor_volumes
            ))
        self.assertLessEqual(sum(achieved_by_floor), sum(targets) + 1e-6)
        stack = result.metadata["floorwise_legal_matrix_stack"]
        self.assertEqual(stack["target_floor_areas_m2"], list(targets))
        self.assertAlmostEqual(
            sum(stack["allocated_floor_areas_m2"]),
            sum(targets),
            places=6,
        )
        self.assertEqual(len(stack["floors"]), len(targets))
        for floor_index, floor in enumerate(stack["floors"]):
            self.assertAlmostEqual(
                floor["target_plan_area_m2"],
                stack["allocated_floor_areas_m2"][floor_index],
                places=4,
            )
            self.assertGreater(floor["achieved_plan_area_m2"], 0.0)
            self.assertLessEqual(
                floor["achieved_plan_area_m2"],
                floor["target_plan_area_m2"] + 1e-6,
            )
            self.assertAlmostEqual(
                floor["achieved_plan_area_m2"],
                achieved_by_floor[floor_index],
                places=4,
            )
        self.assertAlmostEqual(
            sum(floor["achieved_plan_area_m2"] for floor in stack["floors"]),
            sum(achieved_by_floor),
            places=4,
        )

        failed_sink = []
        with patch(
            "design.maas.geometry_language.source_bridge._matrix_fit_polygon_to_host",
            return_value=None,
        ):
            failed = materialize_floorwise_legal_source(
                source,
                legal_sections=(legal,) * len(targets),
                target_plan_coverage=0.6,
                floor_capacity_plan_hash="task7a-production-plan",
                target_floor_areas_m2=targets,
                terminal_failure_sink=failed_sink,
            )
        self.assertIsNone(failed)
        self.assertEqual(len(failed_sink), 1)
        self.assertEqual(failed_sink[0]["stage"], "floor_affine_fit")
        self.assertEqual(failed_sink[0]["evidence"]["floor_index"], 0)

    def test_candidate_terminal_propagation_keeps_structured_evidence(self):
        class FakeProgram:
            def program_hash(self):
                return "program-task7a-propagation"

            def to_dict(self):
                return {
                    "name": "task7a",
                    "metadata": {"family": "llm_slice_notch"},
                }

        class FakeOutcomeGraph:
            def __init__(self):
                self.observations = []

            def observe_geometry_gate_failure(self, **kwargs):
                self.observations.append({
                    "geometry_gate_stage": kwargs["stage"],
                    "geometry_failure_reasons": list(kwargs["failure_reasons"]),
                    "program_slug": kwargs["program_slug"],
                })

        graph = FakeOutcomeGraph()
        report_records = []
        terminal = {
            "stage": "floor_affine_fit",
            "evidence": {
                "failure_reason": "no_positive_lower_projection",
                "floor_index": 2,
                "target_area_m2": 90.0,
                "achieved_area_m2": 0.0,
                "lower_scale": 1.0,
                "upper_scale": 1.25,
                "legal_section_hash": "authoritative-legal-hash",
            },
        }

        _propagate_terminal_materialization_failure(
            terminal_record=terminal,
            report_records=report_records,
            outcome_graph=graph,
            program_slug="task7a",
            source_seed="slab",
            program=FakeProgram(),
            principle_id="book:test",
            book_scope="1/4",
        )

        self.assertEqual(report_records[0]["stage"], terminal["stage"])
        bounded_evidence = {
            "failure_reason": "no_positive_lower_projection",
            "floor_index": 2,
        }
        self.assertEqual(report_records[0]["evidence"], bounded_evidence)
        self.assertTrue(
            report_records[0]["terminal_certificate_evidence"][
                "hard_fail_closed"
            ] is False
        )
        observation = graph.observations[0]
        self.assertEqual(
            observation["terminal_materialization_evidence"],
            bounded_evidence,
        )
        self.assertIsInstance(
            observation["terminal_materialization_evidence"],
            dict,
        )
        self.assertIn(
            "no_positive_lower_projection",
            observation["geometry_failure_reasons"],
        )

    def test_candidate_report_preserves_floor_union_endpoint_diagnostics(self):
        class FakeProgram:
            def program_hash(self):
                return "program-task7a-floor-union-report"

            def to_dict(self):
                return {
                    "metadata": {"family": "llm_scale_courtyard"},
                }

        class FakeOutcomeGraph:
            def __init__(self):
                self.observations = []

            def observe_geometry_gate_failure(self, **kwargs):
                self.observations.append({
                    "geometry_gate_stage": kwargs["stage"],
                    "program_slug": kwargs["program_slug"],
                })

        endpoint = {
            "geom_type": "MultiPolygon",
            "is_valid": True,
            "validity_reason": "Valid Geometry",
            "is_empty": False,
            "aggregate_area_m2": 0.5,
            "component_count": 2,
            "polygon_count": 2,
            "largest_polygon_area_m2": 0.25,
            "post_repair_geom_type": "MultiPolygon",
            "failure_branch": "aggregate_below_minimum_area",
        }
        evidence = {
            "failure_reason": "revalidation_floor_union_invalid",
            "floor_union_count": 4,
            **{f"ground_{key}": value for key, value in endpoint.items()},
            **{f"upper_{key}": value for key, value in endpoint.items()},
        }
        report_records = []
        graph = FakeOutcomeGraph()

        _propagate_terminal_materialization_failure(
            terminal_record={
                "stage": "authored_visual_authority",
                "evidence": evidence,
            },
            report_records=report_records,
            outcome_graph=graph,
            program_slug="task7a",
            source_seed="active_bar",
            program=FakeProgram(),
            principle_id="book:operative:expand",
            book_scope="1/1",
        )

        for destination in (
            report_records[0]["evidence"],
            graph.observations[0]["terminal_materialization_evidence"],
        ):
            for endpoint_name in ("ground", "upper"):
                for key, value in endpoint.items():
                    self.assertEqual(
                        destination[f"{endpoint_name}_{key}"],
                        value,
                    )
