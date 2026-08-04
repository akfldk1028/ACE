from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image

from design.maas.preference.loop import (
    _surface_vertices_world,
    _vlm_cache_key,
    feature_preview_png,
    openai_preview_preference_scorer,
)


def _box_triangles(x0, y0, z0, x1, y1, z1):
    vertices = [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ]
    faces = (
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    )
    return [[vertices[index] for index in face] for face in faces]


class PreferenceRenderFramingTests(SimpleTestCase):
    def _canonical_v2_feature(self):
        triangles = _box_triangles(-6.0, -4.0, 0.0, 6.0, 4.0, 14.0)
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [-6.0, -4.0], [6.0, -4.0], [6.0, 4.0],
                [-6.0, 4.0], [-6.0, -4.0],
            ]],
        }
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "variant_id": "r67-v2-physical",
                "height": 14.0,
                "mass_volumes": [{
                    "geometry": geometry,
                    "bottom_height": 0.0,
                    "top_height": 14.0,
                    "role": "visual-mesh",
                }],
                "source_surfaces": [{
                    "surface_type": "profiled_recursive_solid_mesh",
                    "volume_role": "visual-mesh",
                    "vertices_m": triangle,
                } for triangle in triangles],
                "geometry_artifact": {
                    "projectedVisualMesh": {
                        "schemaVersion": "arr.maas.projected_visual_mesh.v2",
                        "coordinateSpace": "source_footprint_centroid_local_xyz_m",
                    },
                },
            },
        }

    def _render(self, bounds):
        x0, y0, z0, x1, y1, z1 = bounds
        triangles = _box_triangles(*bounds)
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]
                ]],
            },
            "properties": {
                "variant_id": "framing-fixture",
                "height": z1,
                "mass_volumes": [{
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]
                        ]],
                    },
                    "bottom_height": z0,
                    "top_height": z1,
                    "role": "visual-mesh",
                }],
                "source_surfaces": [{
                    "surface_type": "profiled_recursive_solid_mesh",
                    "volume_role": "visual-mesh",
                    "vertices_m": triangle,
                } for triangle in triangles],
            },
        }
        original = deepcopy(feature)
        with TemporaryDirectory() as temporary, patch(
            "design.maas.preference.loop._require_certified_authored_visual"
        ), patch(
            "design.maas.preference.loop._surface_vertices_world",
            side_effect=lambda surface, _feature: surface["vertices_m"],
        ):
            path = feature_preview_png(feature, Path(temporary))
            image = Image.open(path).convert("RGB").crop((0, 0, 350, 235))
            mass_pixels = [
                (x, y)
                for y in range(image.height)
                for x in range(image.width)
                if (
                    image.getpixel((x, y))[0] > 70
                    and image.getpixel((x, y))[1] < 180
                    and image.getpixel((x, y))[2] < 120
                )
            ]
        self.assertEqual(feature, original)
        self.assertGreater(len(mass_pixels), 500)
        xs = [point[0] for point in mass_pixels]
        ys = [point[1] for point in mass_pixels]
        self.assertGreater(max(xs) - min(xs), 40)
        self.assertGreater(max(ys) - min(ys), 40)
        self.assertGreaterEqual(min(xs), 5)
        self.assertLessEqual(max(xs), 344)
        self.assertGreaterEqual(min(ys), 5)
        self.assertLessEqual(max(ys), 229)

    def test_physical_meter_translated_visual_vertices_are_centered_and_visible(self):
        self._render((214320.0, 4478120.0, 0.0, 214350.0, 4478140.0, 14.0))

    def test_legacy_normalized_visual_vertices_remain_centered_and_visible(self):
        self._render((-0.8, -0.5, 0.0, 0.8, 0.5, 1.0))

    def test_r67_v2_physical_height_remains_14m_through_world_and_render(self):
        feature = self._canonical_v2_feature()
        world_vertices = [
            vertex
            for surface in feature["properties"]["source_surfaces"]
            for vertex in _surface_vertices_world(surface, feature)
        ]
        self.assertEqual(min(vertex[2] for vertex in world_vertices), 0.0)
        self.assertEqual(max(vertex[2] for vertex in world_vertices), 14.0)

        with TemporaryDirectory() as temporary, patch(
            "design.maas.preference.loop._require_certified_authored_visual"
        ):
            path = feature_preview_png(feature, Path(temporary))
            image = Image.open(path).convert("RGB").crop((0, 0, 350, 235))
        mass_pixels = [
            (x, y)
            for y in range(image.height)
            for x in range(image.width)
            if (
                image.getpixel((x, y))[0] > 70
                and image.getpixel((x, y))[1] < 180
                and image.getpixel((x, y))[2] < 120
            )
        ]
        xs = [point[0] for point in mass_pixels]
        ys = [point[1] for point in mass_pixels]
        self.assertGreater(max(xs) - min(xs), 70)
        self.assertGreater(max(ys) - min(ys), 70)

    def test_r67_final_vlm_cache_misses_stale_png_then_hits_identical_render(self):
        feature = self._canonical_v2_feature()
        provider_result = {
            "status": "pass",
            "hard_pass": True,
            "concept_scores": {"gesture_clarity": 0.8},
        }
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            stale_key = _vlm_cache_key(
                feature,
                [],
                "test-model",
                rendered_png_sha256="r63-distorted-png",
                renderer_coordinate_contract_version="legacy-normalized-z",
            )
            (cache / f"{stale_key}.json").write_text(
                json.dumps(provider_result),
                encoding="utf-8",
            )
            scorer = openai_preview_preference_scorer(
                preview_dir=root / "previews",
                cache_dir=cache,
            )
            with patch(
                "design.maas.preference.loop._require_certified_authored_visual"
            ), patch(
                "design.maas.preference.loop.score_candidate_with_openai_vlm",
                return_value=provider_result,
            ) as provider:
                first = scorer(
                    feature=feature,
                    reference_matches=[],
                    model="test-model",
                )
                second = scorer(
                    feature=feature,
                    reference_matches=[],
                    model="test-model",
                )
        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])
        provider.assert_called_once()
