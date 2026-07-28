"""Regressions for final legal authored-mesh visual authority."""

import copy
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Point, box

from design.maas import generate_legal_mass_variants
from design.maas.final_floorwise_legal import revalidate_final_floorwise_feature
from design.maas.geometry_language.floorwise_visual_projection import (
    projected_surface_visual_hash,
)
from design.maas.grammar.verb_sequence import VerbSequence, call
from design.maas.legal_envelope import build_legal_envelope
from design.maas.legal_mesh_optimizer import _apply_piloti_parking_void
from design.maas.morphology_operators import MorphologyVariant
from design.maas.preference.loop import (
    _surface_vertices_world,
    _vlm_cache_key,
    feature_preview_png,
)
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.compiler import source_mass_to_variant
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.services.site_geometry import geojson_to_polygon, utm_to_wgs84, wgs84_to_utm


class MaasVisualAuthorityTest(SimpleTestCase):
    def _certified_profiled_feature(
        self,
        *,
        surface_type="profiled_recursive_solid_mesh",
        include_certificate=True,
    ):
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [127.0000, 37.0000],
                [127.0005, 37.0000],
                [127.0005, 37.0004],
                [127.0000, 37.0004],
                [127.0000, 37.0000],
            ]],
        }
        surface = SourceSurface(
            role="certified:triangle:01",
            volume_role="profiled_mass",
            verb="geometry_program",
            surface_type=surface_type,
            vertices_m=((-10.0, -6.0, 0.0), (10.0, -6.0, 0.5), (0.0, 6.0, 1.0)),
            semantic_patch_id="certified:triangle:01",
        )
        record = surface.signature()
        record["vertices_m"] = [list(vertex) for vertex in surface.vertices_m]
        certificate = {
            "schema_version": "arr.maas.floorwise_visual_projection.v1",
            "status": "certified",
            "hard_pass": True,
            "failure_reasons": [],
            "visual_hash": projected_surface_visual_hash((surface,)),
            "source_surface_count": 1,
            "projected_surface_count": 1,
            "capacity_gfa_m2": 240.0,
        }
        properties = {
            "height": 6.0,
            "num_floors": 2,
            "floor_height": 3.0,
            "mass_shape": "certified-profiled-probe",
            "floor_area": 240.0,
            "far": 200.0,
            "source_surfaces": [record],
            "mass_volumes": [{
                "geometry": geometry,
                "bottom_height": 0.0,
                "top_height": 6.0,
                "role": "profiled_mass",
            }],
            "maas_model": {
                "source_surfaces": [copy.deepcopy(record)],
            },
        }
        if include_certificate:
            properties["floorwise_visual_projection"] = certificate
            properties["maas_model"]["floorwise_visual_projection"] = copy.deepcopy(certificate)
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        }

    def test_preference_render_and_cache_ignore_unhashed_world_vertices(self):
        feature = self._certified_profiled_feature()
        tampered = copy.deepcopy(feature)
        tampered["properties"]["source_surfaces"][0]["vertices_world_m"] = [
            [0.0, 0.0, -999.0],
            [500.0, 500.0, -999.0],
            [1000.0, 0.0, -999.0],
        ]
        ground = wgs84_to_utm(geojson_to_polygon(feature["geometry"]))
        origin = ground.centroid
        expected_xy = utm_to_wgs84(Point(origin.x - 10.0, origin.y - 6.0))

        trusted = _surface_vertices_world(
            feature["properties"]["source_surfaces"][0],
            feature,
        )
        actual = _surface_vertices_world(
            tampered["properties"]["source_surfaces"][0],
            tampered,
        )

        self.assertEqual(actual, trusted)
        self.assertAlmostEqual(actual[0][0], expected_xy.x, places=8)
        self.assertAlmostEqual(actual[0][1], expected_xy.y, places=8)
        self.assertEqual(actual[0][2], 0.0)
        self.assertEqual(_vlm_cache_key(feature, [], "probe"), _vlm_cache_key(tampered, [], "probe"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            trusted_png = feature_preview_png(feature, root).read_bytes()
            tampered_png = feature_preview_png(tampered, root).read_bytes()
        self.assertEqual(tampered_png, trusted_png)

    def test_piloti_void_clamps_certified_visual_and_rebinds_hash(self):
        feature = self._certified_profiled_feature()
        props = feature["properties"]
        props.update({
            "parking_strategy": "piloti_ground",
            "parking_precheck": {
                "layout_candidate": {"stalls": [{"id": "stall-1"}]},
            },
            "source_volumes": copy.deepcopy(props["mass_volumes"]),
            "floor_plates": [
                {"floor": 1, "top_height": 3.0, "area": 120.0, "geometry": feature["geometry"]},
                {"floor": 2, "top_height": 6.0, "area": 120.0, "geometry": feature["geometry"]},
            ],
            "floorwise_legal_evidence": {
                "status": "pass",
                "checked_mass_volume_count": 1,
                "capacity_gfa_m2": 240.0,
            },
        })
        props["source_surfaces"][0]["vertices_world_m"] = [
            [1.0, 1.0, 0.0],
            [1.0, 1.0, 3.0],
            [1.0, 1.0, 6.0],
        ]
        props["floorwise_visual_projection"]["source_surface_count"] = 2
        props["maas_model"].update({
            "volumes": copy.deepcopy(props["mass_volumes"]),
            "source_volumes": copy.deepcopy(props["source_volumes"]),
            "floor_plates": copy.deepcopy(props["floor_plates"]),
            "floorwise_legal_evidence": copy.deepcopy(props["floorwise_legal_evidence"]),
            "source_surfaces": copy.deepcopy(props["source_surfaces"]),
        })
        original_hash = props["floorwise_visual_projection"]["visual_hash"]
        legal_capacity = {
            "floor_area": props["floor_area"],
            "far": props["far"],
            "floor_plates": copy.deepcopy(props["floor_plates"]),
            "capacity_gfa_m2": props["floorwise_legal_evidence"]["capacity_gfa_m2"],
        }

        _apply_piloti_parking_void(feature)

        void_height = props["parking_piloti_void"]["void_height_m"]
        surface = props["source_surfaces"][0]
        self.assertTrue(all(
            float(vertex[2]) * float(props["height"]) >= void_height
            for vertex in surface["vertices_m"]
        ))
        self.assertTrue(all(
            float(vertex[2]) >= void_height
            for vertex in surface["vertices_world_m"]
        ))
        rebound = SourceSurface(
            role=surface["role"],
            volume_role=surface["volume_role"],
            verb=surface["verb"],
            surface_type=surface["surface_type"],
            vertices_m=tuple(tuple(vertex) for vertex in surface["vertices_m"]),
            operator=surface["operator"],
            semantic_patch_id=surface["semantic_patch_id"],
        )
        certificate = props["floorwise_visual_projection"]
        self.assertNotEqual(certificate["visual_hash"], original_hash)
        self.assertEqual(certificate["visual_hash"], projected_surface_visual_hash((rebound,)))
        self.assertEqual(certificate["source_surface_count"], 2)
        self.assertEqual(props["maas_model"]["source_surfaces"], props["source_surfaces"])
        self.assertEqual(
            props["maas_model"]["floorwise_visual_projection"],
            certificate,
        )
        self.assertEqual(props["floor_area"], legal_capacity["floor_area"])
        self.assertEqual(props["far"], legal_capacity["far"])
        self.assertEqual(props["floor_plates"], legal_capacity["floor_plates"])
        self.assertEqual(
            props["floorwise_legal_evidence"]["capacity_gfa_m2"],
            legal_capacity["capacity_gfa_m2"],
        )

    def test_preference_rejects_any_profiled_surface_without_certificate(self):
        feature = self._certified_profiled_feature(
            surface_type="profiled_formal_roof",
            include_certificate=False,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "certified nonempty projection"):
                feature_preview_png(feature, Path(temp_dir))

    def test_floorwise_revalidation_rejects_profiled_surface_without_typed_source(self):
        feature = self._certified_profiled_feature(
            surface_type="profiled_formal_roof",
        )
        envelope = build_legal_envelope(
            site_utm=wgs84_to_utm(geojson_to_polygon(feature["geometry"])),
            constraints=[
                {
                    "name": "bcr",
                    "type": "Constraint",
                    "Requirement": "Less than",
                    "val": 100,
                    "unit": "%",
                },
                {
                    "name": "far",
                    "type": "Constraint",
                    "Requirement": "Less than",
                    "val": 500,
                    "unit": "%",
                },
                {
                    "name": "height",
                    "type": "Constraint",
                    "Requirement": "Less than",
                    "val": 20,
                    "unit": "m",
                },
            ],
            building_type="profiled-authority-probe",
            sunlight_envelope=None,
        )

        result = revalidate_final_floorwise_feature(
            feature,
            envelope=envelope,
            sunlight_envelope=None,
            building_type="profiled-authority-probe",
            authored_source=None,
        )

        self.assertIsNone(result.feature)
        self.assertIn(
            "authored_source_unavailable",
            result.evidence["failed_checks"],
        )

    def _authored_indexed_source(self, footprint):
        minx, miny, maxx, maxy = footprint.bounds
        cx, cy = float(footprint.centroid.x), float(footprint.centroid.y)
        vertices = (
            (minx - cx, miny - cy, 0.0),
            (maxx - cx, miny - cy, 0.0),
            (maxx - cx, maxy - cy, 0.0),
            (minx - cx, maxy - cy, 0.0),
            (minx - cx, miny - cy, 1.0),
            (maxx - cx, miny - cy, 1.0),
            (maxx - cx, maxy - cy, 1.0),
            (minx - cx, maxy - cy, 1.0),
        )
        triangles = (
            (0, 2, 1), (0, 3, 2),
            (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6),
            (3, 0, 4), (3, 4, 7),
        )
        surfaces = tuple(
            SourceSurface(
                role=f"indexed:{index:02d}",
                volume_role="recursive_solid_primary",
                verb="geometry_program",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=tuple(vertices[vertex] for vertex in triangle),
                semantic_patch_id=f"indexed:{index:02d}",
            )
            for index, triangle in enumerate(triangles, start=1)
        )
        return SourceMass(
            name="agent_indexed_mesh_probe",
            footprint=footprint,
            volumes=(
                SourceVolume(
                    "recursive_solid_primary",
                    footprint,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            surfaces=surfaces,
            metadata={
                "family": "indexed_mesh_probe",
                "formal_principle": "indexed_mesh_probe",
                "dominant_gesture": "indexed_mesh_probe",
                "geometry_program": {"name": "indexed_mesh_probe"},
                "geometry_graph_snapshot": {
                    "nodes": [{"id": "base-volume"}, {"id": "book-operation"}],
                },
                "geometry_program_bridge_evidence": {
                    "program_hash": "indexed-program",
                    "geometry_hash": "indexed-geometry",
                    "raw_mesh_triangle_count": len(surfaces),
                    "exported_surface_count": len(surfaces),
                },
                "continuous_surface_evidence": {
                    "hard_pass": True,
                    "surface_count": len(surfaces),
                },
            },
        )

    def test_source_variant_retains_exact_typed_authority_transiently(self):
        sequence = VerbSequence(
            "typed_authority_probe",
            "typed authority probe",
            (call("base", proportion="site"), call("bar", axis="x", factor=0.7)),
        )
        source = compile_sequence_to_source_mass(box(0, 0, 30, 18), sequence)
        self.assertIsNotNone(source)

        variant = source_mass_to_variant(source, sequence)

        self.assertIs(variant.source_mass, source)

    def _generate_indexed_candidate(self, *, retain_typed_source):
        site = {
            "type": "Polygon",
            "coordinates": [[
                [127.0, 37.0],
                [127.001, 37.0],
                [127.001, 37.001],
                [127.0, 37.001],
                [127.0, 37.0],
            ]],
        }
        mass = {
            "type": "Feature",
            "geometry": site,
            "properties": {"height": 12.0, "num_floors": 4},
        }

        def indexed_seed(base_footprint, _envelope, **_kwargs):
            source = self._authored_indexed_source(base_footprint)
            return [MorphologyVariant(
                operator=source.name,
                footprint=source.footprint,
                source_geometry_status=source.status,
                source_signature=source.signature(),
                source_volumes=source.source_volume_signatures(),
                source_surfaces=source.source_surface_signatures(),
                source_mass=source if retain_typed_source else None,
            )]

        with patch(
            "design.maas.legal_mesh_optimizer.generate_seed_variants",
            side_effect=indexed_seed,
        ):
            return generate_legal_mass_variants(
                mass_geojson=mass,
                site_polygon_geojson=site,
                constraints=[
                    {
                        "name": "bcr",
                        "type": "Constraint",
                        "Requirement": "Less than",
                        "val": 100,
                        "unit": "%",
                    },
                    {
                        "name": "far",
                        "type": "Constraint",
                        "Requirement": "Less than",
                        "val": 600,
                        "unit": "%",
                    },
                    {
                        "name": "height",
                        "type": "Constraint",
                        "Requirement": "Less than",
                        "val": 24,
                        "unit": "m",
                    },
                ],
                building_type="visual-authority-probe",
                max_variants=1,
                preferred_operator="agent_indexed_mesh_probe",
            )

    def test_legal_optimizer_rebinds_typed_authored_source_before_preference(self):
        result = self._generate_indexed_candidate(retain_typed_source=True)

        self.assertEqual(result["count"], 1, result.get("rejected"))
        props = result["feature_collection"]["features"][0]["properties"]
        self.assertGreater(len(props["source_surfaces"]), 0)
        self.assertEqual(
            props["floorwise_visual_projection"]["status"],
            "certified",
        )
        self.assertTrue(props["floorwise_visual_projection"]["hard_pass"])
        self.assertEqual(
            props["floorwise_legal_evidence"]["visual_authority"],
            "certified_projected_authored_mesh",
        )
        self.assertEqual(
            props["source_signature"]["geometry_program_bridge_evidence"][
                "geometry_hash"
            ],
            "indexed-geometry",
        )
        self.assertEqual(
            props["source_signature"]["geometry_graph_snapshot"]["nodes"],
            [{"id": "base-volume"}, {"id": "book-operation"}],
        )
        self.assertEqual(props["variant_id"], "maas_01")
        self.assertTrue(any(
            review.get("agent") == "law_graph_agent"
            for review in result["agent_reviews"]
        ))
        with tempfile.TemporaryDirectory() as temp_dir:
            preview = feature_preview_png(
                result["feature_collection"]["features"][0],
                Path(temp_dir),
            )
            self.assertTrue(preview.exists())

    def test_legal_optimizer_rejects_authored_mesh_without_typed_reprojection(self):
        result = self._generate_indexed_candidate(retain_typed_source=False)

        failures = [
            rejection
            for rejection in result["rejected"]
            if rejection.get("operator") == "agent_indexed_mesh_probe"
        ]
        self.assertTrue(failures)
        self.assertEqual(
            failures[0]["reason"],
            "authored_floorwise_visual_reprojection_failed",
        )
        self.assertIn(
            "authored_floorwise_visual_reprojection_failed",
            failures[0]["failed_checks"],
        )
