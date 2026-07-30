from __future__ import annotations

from itertools import combinations
import importlib
import importlib.util
import unittest


MODULE = "design.maas.creative_morphology"
EXPECTED_DISTANCE_COMPONENTS = {
    "component",
    "axis",
    "z_slice",
    "floor",
    "convexity",
    "void",
    "normal",
    "radial",
    "silhouette",
    "contact",
}


def _morphology():
    if importlib.util.find_spec(MODULE) is None:
        raise AssertionError("creative_morphology module must exist")
    return importlib.import_module(MODULE)


def _add_box(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    bounds: tuple[float, float, float, float, float, float],
) -> None:
    x0, y0, z0, x1, y1, z1 = bounds
    offset = len(vertices)
    vertices.extend((
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ))
    triangles.extend(
        tuple(offset + index for index in face)
        for face in (
            (0, 2, 1), (0, 3, 2),
            (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6),
            (3, 0, 4), (3, 4, 7),
        )
    )


def _add_triangular_prism(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    *,
    length: float,
    depth: float,
    height: float,
) -> None:
    offset = len(vertices)
    vertices.extend((
        (-length / 2.0, -depth / 2.0, 0.0),
        (length / 2.0, -depth / 2.0, 0.0),
        (0.0, -depth / 2.0, height),
        (-length / 2.0, depth / 2.0, 0.0),
        (length / 2.0, depth / 2.0, 0.0),
        (0.0, depth / 2.0, height),
    ))
    triangles.extend(
        tuple(offset + index for index in face)
        for face in (
            (0, 1, 2), (3, 5, 4),
            (0, 3, 4), (0, 4, 1),
            (1, 4, 5), (1, 5, 2),
            (2, 5, 3), (2, 3, 0),
        )
    )


def _add_disc(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    *,
    center: tuple[float, float],
    radius: float,
    height: float,
    segments: int = 12,
) -> None:
    from math import cos, pi, sin

    offset = len(vertices)
    cx, cy = center
    vertices.extend((
        (cx, cy, 0.0),
        (cx, cy, height),
    ))
    for index in range(segments):
        angle = 2.0 * pi * index / segments
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        vertices.extend(((x, y, 0.0), (x, y, height)))
    for index in range(segments):
        following = (index + 1) % segments
        bottom = offset + 2 + 2 * index
        top = bottom + 1
        next_bottom = offset + 2 + 2 * following
        next_top = next_bottom + 1
        triangles.extend((
            (offset, next_bottom, bottom),
            (offset + 1, top, next_top),
            (bottom, next_bottom, next_top),
            (bottom, next_top, top),
        ))


def _family_fixture(
    family: str,
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, int, int], ...],
    tuple[float, ...],
    str,
]:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    if family == "stepped":
        _add_box(vertices, triangles, (-2.0, -1.0, 0.0, 2.0, 1.0, 1.0))
        _add_box(vertices, triangles, (-1.4, -0.8, 1.0, 1.4, 0.8, 2.1))
        _add_box(vertices, triangles, (-0.7, -0.6, 2.1, 0.7, 0.6, 3.2))
        floors = (8.0, 4.48, 1.68)
        contact = "core"
    elif family == "triangular_shard":
        _add_triangular_prism(
            vertices,
            triangles,
            length=4.8,
            depth=1.3,
            height=4.0,
        )
        floors = (5.5, 3.8, 2.0, 0.7)
        contact = "core"
    elif family == "thin_disc_cluster":
        _add_disc(
            vertices,
            triangles,
            center=(-0.9, 0.0),
            radius=1.35,
            height=0.55,
        )
        _add_disc(
            vertices,
            triangles,
            center=(0.9, 0.0),
            radius=1.35,
            height=0.55,
        )
        floors = (8.7, 8.7)
        contact = "hub"
    elif family == "courtyard":
        _add_box(vertices, triangles, (-3.0, -2.5, 0.0, -1.7, 2.5, 2.4))
        _add_box(vertices, triangles, (1.7, -2.5, 0.0, 3.0, 2.5, 2.4))
        _add_box(vertices, triangles, (-1.7, -2.5, 0.0, 1.7, -1.2, 2.4))
        _add_box(vertices, triangles, (-1.7, 1.2, 0.0, 1.7, 2.5, 2.4))
        floors = (19.78, 19.78, 19.78)
        contact = "core"
    elif family == "long_span_bridge":
        _add_box(vertices, triangles, (-5.0, -1.1, 0.0, -3.6, 1.1, 3.8))
        _add_box(vertices, triangles, (3.6, -1.1, 0.0, 5.0, 1.1, 3.8))
        _add_box(vertices, triangles, (-3.6, -0.45, 2.6, 3.6, 0.45, 3.5))
        floors = (6.16, 6.16, 12.64, 12.64)
        contact = "bridge"
    else:
        raise AssertionError(f"unknown literal fixture: {family}")
    return tuple(vertices), tuple(triangles), floors, contact


def _descriptor(family: str):
    module = _morphology()
    vertices, triangles, floors, contact = _family_fixture(family)
    return module.build_morphology_descriptor(
        vertices=vertices,
        triangles=triangles,
        floor_areas=floors,
        component_count=1,
        contact_topology=contact,
    )


class CreativeMorphologyDescriptorTests(unittest.TestCase):
    def test_uniform_scale_does_not_create_morphology_novelty(self):
        module = _morphology()
        vertices, triangles, floors, contact = _family_fixture("stepped")
        scaled = tuple(
            tuple(coordinate * 1.003 for coordinate in vertex)
            for vertex in vertices
        )

        base = module.build_morphology_descriptor(
            vertices=vertices,
            triangles=triangles,
            floor_areas=floors,
            component_count=1,
            contact_topology=contact,
        )
        copy = module.build_morphology_descriptor(
            vertices=scaled,
            triangles=triangles,
            floor_areas=tuple(area * 1.003**2 for area in floors),
            component_count=1,
            contact_topology=contact,
        )

        self.assertLess(module.morphology_distance(base, copy), 0.01)

    def test_descriptor_is_deterministic_fixed_length_and_named(self):
        module = _morphology()
        descriptor = _descriptor("courtyard")

        self.assertEqual(descriptor, _descriptor("courtyard"))
        self.assertEqual(len(descriptor.axis_ratios), 3)
        self.assertEqual(len(descriptor.z_slice_occupancies), 8)
        self.assertEqual(len(descriptor.floor_area_profile), 8)
        self.assertEqual(len(descriptor.normal_bins), 12)
        self.assertEqual(len(descriptor.radial_bins), 8)
        self.assertEqual(len(descriptor.silhouette_front), 16)
        self.assertEqual(len(descriptor.silhouette_side), 16)
        self.assertEqual(len(descriptor.silhouette_isometric), 16)
        self.assertEqual(
            set(descriptor.to_dict()),
            {
                "schema_version",
                "axis_ratios",
                "z_slice_occupancies",
                "floor_area_profile",
                "convexity",
                "void_fraction",
                "normal_bins",
                "radial_bins",
                "silhouette_front",
                "silhouette_side",
                "silhouette_isometric",
                "component_count",
                "contact_topology",
            },
        )

    def test_cross_family_literal_fixtures_clear_global_threshold(self):
        module = _morphology()
        descriptors = {
            family: _descriptor(family)
            for family in (
                "stepped",
                "triangular_shard",
                "thin_disc_cluster",
                "courtyard",
                "long_span_bridge",
            )
        }
        required_pairs = (
            ("stepped", "triangular_shard"),
            ("stepped", "thin_disc_cluster"),
            ("thin_disc_cluster", "courtyard"),
            ("courtyard", "long_span_bridge"),
            ("triangular_shard", "long_span_bridge"),
        )

        for left_name, right_name in required_pairs:
            distance = module.morphology_distance(
                descriptors[left_name],
                descriptors[right_name],
            )
            self.assertGreaterEqual(
                distance,
                module.GLOBAL_MORPHOLOGY_THRESHOLD,
                (left_name, right_name, float(distance)),
            )

    def test_distance_is_symmetric_bounded_and_saves_named_components(self):
        module = _morphology()
        descriptors = tuple(
            _descriptor(family)
            for family in ("stepped", "courtyard", "long_span_bridge")
        )

        for left, right in combinations(descriptors, 2):
            forward = module.morphology_distance(left, right)
            reverse = module.morphology_distance(right, left)
            self.assertGreaterEqual(forward, 0.0)
            self.assertLessEqual(forward, 1.0)
            self.assertAlmostEqual(forward, reverse, places=12)
            self.assertEqual(
                set(forward.components),
                EXPECTED_DISTANCE_COMPONENTS,
            )
            self.assertEqual(
                set(forward.to_dict()["components"]),
                EXPECTED_DISTANCE_COMPONENTS,
            )


class CreativeMorphologyGateTests(unittest.TestCase):
    def test_repeated_family_parameter_noise_is_rejected(self):
        module = _morphology()
        base = _descriptor("stepped")
        vertices, triangles, floors, contact = _family_fixture("stepped")
        noisy = tuple(
            (
                x * 1.002 + (0.0002 if index % 2 else -0.0002),
                y * 1.002,
                z * 1.002,
            )
            for index, (x, y, z) in enumerate(vertices)
        )
        copy = module.build_morphology_descriptor(
            vertices=noisy,
            triangles=triangles,
            floor_areas=tuple(area * 1.002**2 for area in floors),
            component_count=1,
            contact_topology=contact,
        )
        accepted = [{
            "candidate_id": "creative-001",
            "family": "stepped",
            "morphology_descriptor": base.to_dict(),
        }]

        decision = module.accept_morphology(
            {
                "candidate_id": "creative-002",
                "family": "stepped",
                "morphology_descriptor": copy.to_dict(),
            },
            accepted,
        )

        self.assertFalse(decision)
        self.assertEqual(decision.closest_candidate_id, "creative-001")
        self.assertIn("global", decision.failed_components)
        self.assertIn("within_family", decision.failed_components)

    def test_cross_family_candidate_is_accepted_with_auditable_thresholds(self):
        module = _morphology()
        accepted = [{
            "candidate_id": "creative-001",
            "family": "courtyard",
            "morphology_descriptor": _descriptor("courtyard").to_dict(),
        }]

        decision = module.accept_morphology(
            {
                "candidate_id": "creative-002",
                "family": "long_span_bridge",
                "morphology_descriptor": _descriptor(
                    "long_span_bridge"
                ).to_dict(),
            },
            accepted,
        )

        self.assertTrue(decision)
        self.assertEqual(
            decision.threshold,
            module.GLOBAL_MORPHOLOGY_THRESHOLD,
        )
        self.assertGreaterEqual(decision.nearest_distance, decision.threshold)
        self.assertEqual(decision.failed_components, ())

    def test_read_only_audit_collects_rejections_without_retrying(self):
        module = _morphology()
        self.assertTrue(
            hasattr(module, "audit_morphology_portfolio"),
            "read-only morphology audit must exist",
        )
        base = {
            "candidate_id": "creative-001",
            "family": "stepped",
            "morphology_descriptor": _descriptor("stepped").to_dict(),
        }
        repeated = {
            "candidate_id": "creative-002",
            "family": "stepped",
            "morphology_descriptor": _descriptor("stepped").to_dict(),
        }
        cross_family = {
            "candidate_id": "creative-003",
            "family": "long_span_bridge",
            "morphology_descriptor": _descriptor(
                "long_span_bridge"
            ).to_dict(),
        }

        audit = module.audit_morphology_portfolio(
            (base, repeated, cross_family)
        )

        self.assertEqual(audit["candidate_count"], 3)
        self.assertEqual(audit["accepted_count"], 2)
        self.assertEqual(audit["rejected_count"], 1)
        self.assertEqual(len(audit["decisions"]), 3)
        self.assertEqual(
            audit["rejections"][0]["candidate_id"],
            "creative-002",
        )
        self.assertEqual(
            audit["rejections"][0]["closest_candidate_id"],
            "creative-001",
        )
        self.assertEqual(
            audit["rejections"][0]["failed_components"],
            ["global", "within_family"],
        )


if __name__ == "__main__":
    unittest.main()
