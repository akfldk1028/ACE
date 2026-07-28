"""Regressions for final legal authored-mesh visual authority."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas import generate_legal_mass_variants
from design.maas.grammar.verb_sequence import VerbSequence, call
from design.maas.morphology_operators import MorphologyVariant
from design.maas.preference.loop import feature_preview_png
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.compiler import source_mass_to_variant
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


class MaasVisualAuthorityTest(SimpleTestCase):
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
