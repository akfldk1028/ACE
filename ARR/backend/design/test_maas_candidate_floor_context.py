from copy import deepcopy
from math import inf, nan
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box, mapping

from design.maas.book_language.candidate_generation import (
    _candidate_floor_context,
    _compact_candidate_capacity_evidence,
    _program_pool,
    _shared_floor_capacity_measurement,
)
from design.maas.book_language.capacity_alternatives import (
    capacity_contract_for_alternative,
)
from design.maas.book_language.capacity_contract import (
    build_feasible_capacity_contract,
)
from design.maas.book_language.floor_capacity_plan import (
    derive_program_floor_capacity_plan,
)
from design.maas.source_geometry.ir import SourceMass, SourceVolume


PNU = "1168011800104170004"


class _IntSubclass(int):
    pass


class _ListSubclass(list):
    pass


class _ForgedEqualList(list):
    def __eq__(self, _other):
        return True

    def __ne__(self, _other):
        return False


class _DictSubclass(dict):
    def __eq__(self, _other):
        return True

    def __ne__(self, _other):
        return False


def _context(*, floor_height=3.0, legal_floors=25, far_limit=562.5):
    return SimpleNamespace(
        envelope=SimpleNamespace(
            floor_height=floor_height,
            height_limit=floor_height * legal_floors,
            bcr_limit=60.0,
            far_limit=far_limit,
        ),
        generation_site=box(0.0, 0.0, 10.0, 10.0),
        sunlight_ring=(),
        evidence={},
    )


def _floor_plan(*, pnu=PNU):
    context = _context()
    site = box(0.0, 0.0, 20.0, 20.0)
    return derive_program_floor_capacity_plan(
        context,
        site_local_utm=site,
        building_type="neighborhood living",
        target_utilization=0.90,
        legacy_floor_hint=5,
        pnu=pnu,
    )


def _base_contract(*, pnu=PNU):
    context = _context()
    site = box(0.0, 0.0, 20.0, 20.0)
    return build_feasible_capacity_contract(
        context,
        site_local_utm=site,
        height_m=15.0,
        floors=5,
        target_utilization=0.90,
        minimum_utilization=0.40,
        floor_capacity_plan=_floor_plan(pnu=pnu),
    )


def _four_floor_design_reserve_contract(*, pnu=PNU):
    context = _context(legal_floors=4, far_limit=100.0)
    site = box(0.0, 0.0, 20.0, 20.0)
    floor_plan = derive_program_floor_capacity_plan(
        context,
        site_local_utm=site,
        building_type="neighborhood living",
        target_utilization=0.90,
        legacy_floor_hint=4,
        pnu=pnu,
    )
    return build_feasible_capacity_contract(
        context,
        site_local_utm=site,
        height_m=12.0,
        floors=4,
        target_utilization=0.90,
        minimum_utilization=0.40,
        floor_capacity_plan=floor_plan,
    )


class CandidateSpecificFloorContextTests(SimpleTestCase):
    def _trusted_context(self, projected, base):
        return _candidate_floor_context(
            projected,
            fallback_height=15.0,
            fallback_floors=5,
            trusted_legal_floor_field=base["legal_floor_field"],
            expected_legal_floor_field_hash=base[
                "legal_floor_field_hash"
            ],
        )

    def test_alternative_target_derives_minimum_three_seven_and_twenty_plus_prefix(self):
        base = _base_contract()
        field = base["legal_floor_field"]
        original_field = dict(field)

        cases = (
            (210.0, 3, 9.0),
            (650.0, 7, 21.0),
            (2250.0, 23, 69.0),
        )
        hashes = set()
        for target, expected_floors, expected_height in cases:
            with self.subTest(expected_floors=expected_floors):
                projected = capacity_contract_for_alternative(
                    base,
                    {
                        "alternative_id": f"target_{expected_floors}",
                        "target_utilization": target / 2250.0,
                        "target_floor_area_m2": target,
                        "target_base_plan_area_m2": target / expected_floors,
                        "target_base_plan_coverage": 0.7,
                    },
                )

                self.assertEqual(projected["requested_floors"], expected_floors)
                self.assertEqual(projected["requested_height_m"], expected_height)
                self.assertEqual(
                    len(projected["candidate_legal_floor_sections"]),
                    expected_floors,
                )
                self.assertEqual(
                    len(projected["bcr_adjusted_floor_areas_m2"]),
                    expected_floors,
                )
                self.assertEqual(
                    len(projected["target_floor_areas_m2"]),
                    expected_floors,
                )
                self.assertAlmostEqual(
                    sum(projected["target_floor_areas_m2"]),
                    target,
                    places=3,
                )
                self.assertTrue(all(
                    value > 0.0
                    for value in projected["target_floor_areas_m2"]
                ))
                self.assertEqual(
                    projected["candidate_floor_count_authority"],
                    "minimum_legal_capacity_prefix_for_candidate_target",
                )
                self.assertEqual(
                    projected["legal_floor_field"],
                    original_field,
                )
                hashes.add(projected["legal_floor_field_hash"])

                floor_context = _candidate_floor_context(
                    projected,
                    fallback_height=15.0,
                    fallback_floors=5,
                    trusted_legal_floor_field=base[
                        "legal_floor_field"
                    ],
                    expected_legal_floor_field_hash=base[
                        "legal_floor_field_hash"
                    ],
                )
                self.assertTrue(floor_context["hard_pass"])
                self.assertEqual(floor_context["floors"], expected_floors)
                self.assertEqual(floor_context["height_m"], expected_height)
                self.assertEqual(
                    len(floor_context["legal_sections"]),
                    expected_floors,
                )
                self.assertTrue(all(
                    isinstance(section, Polygon)
                    for section in floor_context["legal_sections"]
                ))

        self.assertEqual(hashes, {field["legal_floor_field_hash"]})
        self.assertEqual(base["legal_floor_field"], original_field)

    def test_spatial_reserve_preserves_full_lawful_design_reserve_stack(self):
        base = _four_floor_design_reserve_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "spatial_reserve",
                "target_utilization": 0.40,
                "target_floor_area_m2": 160.0,
                "target_base_plan_area_m2": 40.0,
                "target_base_plan_coverage": 0.40,
            },
        )

        self.assertEqual(projected["requested_floors"], 4)
        self.assertEqual(projected["requested_height_m"], 12.0)
        self.assertEqual(projected["target_floor_areas_m2"], [40.0] * 4)
        self.assertEqual(
            projected["target_base_plan_coverage"],
            base["target_base_plan_coverage"],
        )
        self.assertGreater(
            projected["target_base_plan_coverage"],
            0.40,
        )
        self.assertEqual(
            projected["candidate_floor_count_authority"],
            "full_lawful_design_reserve_stack_for_spatial_reserve",
        )

        context = self._trusted_context(projected, base)
        self.assertTrue(context["hard_pass"], context)
        self.assertEqual(context["floors"], 4)

    def test_proportional_targets_do_not_create_sequential_full_slab_terminal_trim(self):
        projected = capacity_contract_for_alternative(
            _base_contract(),
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )

        self.assertEqual(projected["target_floor_areas_m2"], [70.0, 70.0, 70.0])
        self.assertEqual(
            projected["floor_target_distribution"],
            "proportional_across_candidate_prefix_for_authored_fit",
        )

    def test_compact_candidate_evidence_keeps_hash_and_prefix_identity_without_polygons(self):
        projected = capacity_contract_for_alternative(
            _base_contract(),
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )

        compact = _compact_candidate_capacity_evidence(projected)

        self.assertNotIn("legal_floor_field", compact)
        self.assertNotIn("candidate_legal_floor_sections", compact)
        self.assertEqual(
            compact["legal_floor_field_hash"],
            projected["legal_floor_field_hash"],
        )
        self.assertEqual(compact["requested_floors"], 3)
        self.assertEqual(compact["target_floor_areas_m2"], [70.0, 70.0, 70.0])

    def test_candidate_context_rejects_self_consistent_field_resealed_against_wrong_trusted_base(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        replacement = capacity_contract_for_alternative(
            _base_contract(pnu="1168011800104170005"),
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        projected["legal_floor_field"] = replacement["legal_floor_field"]
        projected["legal_floor_field_hash"] = replacement[
            "legal_floor_field_hash"
        ]
        projected["candidate_legal_floor_field_hash"] = replacement[
            "candidate_legal_floor_field_hash"
        ]
        projected["candidate_legal_floor_sections"] = replacement[
            "candidate_legal_floor_sections"
        ]

        floor_context = _candidate_floor_context(
            projected,
            fallback_height=15.0,
            fallback_floors=5,
            trusted_legal_floor_field=base["legal_floor_field"],
            expected_legal_floor_field_hash=base[
                "legal_floor_field_hash"
            ],
        )

        self.assertFalse(floor_context["hard_pass"])
        self.assertEqual(
            floor_context["failure_reasons"],
            ["untrusted_legal_floor_field_identity"],
        )

    def test_candidate_context_rejects_one_floor_forty_thousand_square_metre_forged_prefix(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "forged_one_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 210.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        projected.update({
            "requested_floors": 1,
            "requested_height_m": 3.0,
            "candidate_legal_floor_sections": [
                mapping(box(0.0, 0.0, 200.0, 200.0))
            ],
            "candidate_floor_top_heights_m": [3.0],
            "legal_floor_section_areas_m2": [40000.0],
            "bcr_adjusted_floor_areas_m2": [40000.0],
            "target_floor_areas_m2": [210.0],
            "candidate_prefix_capacity_m2": 40000.0,
        })

        context = self._trusted_context(projected, base)

        self.assertFalse(context["hard_pass"])
        self.assertIn(
            "candidate_floor_count_not_minimum_legal_prefix",
            context["failure_reasons"],
        )

    def test_trusted_anchor_rejects_stripped_candidate_identity_without_resampling(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        for key in (
            "legal_floor_field",
            "legal_floor_field_hash",
            "candidate_legal_floor_field_hash",
        ):
            projected.pop(key, None)

        context = _candidate_floor_context(
            projected,
            fallback_height=15.0,
            fallback_floors=5,
            fallback_legal_sections=(
                box(0.0, 0.0, 1.0, 1.0),
            ) * 5,
            trusted_legal_floor_field=base["legal_floor_field"],
            expected_legal_floor_field_hash=base[
                "legal_floor_field_hash"
            ],
        )

        self.assertFalse(context["hard_pass"])
        self.assertEqual(
            context["failure_reasons"],
            ["missing_candidate_legal_floor_identity"],
        )

        source = SourceMass(
            name="stripped_identity",
            footprint=box(0.0, 0.0, 1.0, 1.0),
            volumes=(),
            metadata={},
        )
        with patch(
            "design.maas.book_language.candidate_generation."
            "generation_site_at_height",
            side_effect=AssertionError(
                "anchored stripped identity must not resample"
            ),
        ):
            floor_contract, measurement = (
                _shared_floor_capacity_measurement(
                    source,
                    projected,
                    generation_context=_context(),
                    capacity_site=box(0.0, 0.0, 20.0, 20.0),
                    height=15.0,
                    floors=5,
                    pnu=PNU,
                    trusted_legal_floor_field=base[
                        "legal_floor_field"
                    ],
                    expected_legal_floor_field_hash=base[
                        "legal_floor_field_hash"
                    ],
                )
            )
        self.assertFalse(floor_contract["hard_pass"])
        self.assertFalse(measurement["hard_pass"])
        self.assertEqual(
            floor_contract["failure_reasons"],
            ["missing_candidate_legal_floor_identity"],
        )

    def test_projected_candidate_mutation_cannot_poison_base_or_sibling(self):
        base = _base_contract()
        base_snapshot = deepcopy(base)
        first = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "first",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        sibling = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "sibling",
                "target_utilization": 650.0 / 2250.0,
                "target_floor_area_m2": 650.0,
                "target_base_plan_area_m2": 650.0 / 7.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        sibling_snapshot = deepcopy(sibling)

        self.assertIsNot(
            first["legal_floor_field"],
            base["legal_floor_field"],
        )
        self.assertIsNot(
            first["candidate_legal_floor_sections"],
            base["candidate_legal_floor_sections"],
        )
        first["legal_floor_field"]["pnu"] = "1111111111111111111"
        first["candidate_legal_floor_sections"][0]["type"] = "Point"
        first["target_floor_areas_m2"][0] = 999999.0

        self.assertEqual(base, base_snapshot)
        self.assertEqual(sibling, sibling_snapshot)

    def test_candidate_context_rejects_coercive_floor_count_types(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        for malformed in (3.7, "3", True, _IntSubclass(3)):
            with self.subTest(malformed=repr(malformed)):
                candidate = deepcopy(projected)
                candidate["requested_floors"] = malformed
                context = self._trusted_context(candidate, base)
                self.assertFalse(context["hard_pass"])
                self.assertEqual(
                    context["failure_reasons"],
                    ["invalid_candidate_requested_floors"],
                )

    def test_candidate_context_rejects_coercive_top_and_target_types(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        corruptions = (
            (
                "string_top",
                {"candidate_floor_top_heights_m": ["3.0", 6.0, 9.0]},
                "invalid_candidate_floor_top_schema",
            ),
            (
                "boolean_top",
                {"candidate_floor_top_heights_m": [True, 6.0, 9.0]},
                "invalid_candidate_floor_top_schema",
            ),
            (
                "string_floor_target",
                {"target_floor_areas_m2": ["70.0", 70.0, 70.0]},
                "invalid_candidate_floor_target_schema",
            ),
            (
                "boolean_floor_target",
                {"target_floor_areas_m2": [True, 70.0, 70.0]},
                "invalid_candidate_floor_target_schema",
            ),
            (
                "string_aggregate_target",
                {"candidate_target_gfa_m2": "210.0"},
                "invalid_candidate_target_gfa_schema",
            ),
        )
        for label, changes, expected_failure in corruptions:
            with self.subTest(label=label):
                candidate = deepcopy(projected)
                candidate.update(changes)
                context = self._trusted_context(candidate, base)
                self.assertFalse(context["hard_pass"])
                self.assertEqual(
                    context["failure_reasons"],
                    [expected_failure],
                )

    def test_candidate_context_rejects_nan_and_infinity_before_identity_math(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        attacks = (
            (
                "candidate_target_gfa_m2",
                "scalar",
                "invalid_candidate_target_gfa",
            ),
            (
                "target_floor_area_m2",
                "scalar",
                "invalid_candidate_target_gfa",
            ),
            (
                "requested_height_m",
                "scalar",
                "invalid_candidate_floor_heights",
            ),
            (
                "candidate_prefix_capacity_m2",
                "scalar",
                "candidate_prefix_capacity_identity_mismatch",
            ),
            (
                "candidate_floor_top_heights_m",
                "vector",
                "invalid_candidate_floor_heights",
            ),
            (
                "legal_floor_section_areas_m2",
                "vector",
                "invalid_candidate_floor_area_vector",
            ),
            (
                "bcr_adjusted_floor_areas_m2",
                "vector",
                "invalid_candidate_floor_capacity_vector",
            ),
            (
                "target_floor_areas_m2",
                "vector",
                "invalid_candidate_floor_target_vector",
            ),
        )
        for value in (nan, inf, -inf):
            for key, mode, expected_failure in attacks:
                with self.subTest(key=key, value=value):
                    candidate = deepcopy(projected)
                    if mode == "vector":
                        candidate[key][0] = value
                    else:
                        candidate[key] = value
                    context = self._trusted_context(candidate, base)
                    self.assertFalse(context["hard_pass"])
                    self.assertEqual(
                        context["failure_reasons"],
                        [expected_failure],
                    )

    def test_candidate_context_rejects_nonplain_outer_vector_containers_before_equality(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        vector_keys = (
            "candidate_legal_floor_sections",
            "candidate_floor_top_heights_m",
            "legal_floor_section_areas_m2",
            "bcr_adjusted_floor_areas_m2",
            "target_floor_areas_m2",
        )
        for wrapper in (_ListSubclass, tuple):
            for key in vector_keys:
                with self.subTest(wrapper=wrapper.__name__, key=key):
                    candidate = deepcopy(projected)
                    candidate[key] = wrapper(candidate[key])
                    context = self._trusted_context(candidate, base)
                    self.assertFalse(context["hard_pass"])
                    self.assertEqual(
                        context["failure_reasons"],
                        ["invalid_candidate_floor_vector_schema"],
                    )

        candidate = deepcopy(projected)
        forged = _ForgedEqualList(
            candidate["candidate_legal_floor_sections"]
        )
        forged[0] = mapping(box(0.0, 0.0, 200.0, 200.0))
        candidate["candidate_legal_floor_sections"] = forged
        context = self._trusted_context(candidate, base)
        self.assertFalse(context["hard_pass"])
        self.assertEqual(
            context["failure_reasons"],
            ["invalid_candidate_floor_vector_schema"],
        )

    def test_candidate_context_rejects_nonplain_or_substituted_nested_geojson_without_overloaded_equality(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )

        attacks = []
        forged_dict = _DictSubclass(
            mapping(box(0.0, 0.0, 200.0, 200.0))
        )
        attacks.append((
            "forged_geometry_dict",
            lambda candidate: candidate[
                "candidate_legal_floor_sections"
            ].__setitem__(0, forged_dict),
            "invalid_candidate_legal_section_schema",
        ))
        attacks.append((
            "coordinate_container_subclass",
            lambda candidate: candidate[
                "candidate_legal_floor_sections"
            ][0].__setitem__(
                "coordinates",
                _ListSubclass(
                    candidate["candidate_legal_floor_sections"][0][
                        "coordinates"
                    ]
                ),
            ),
            "invalid_candidate_legal_section_schema",
        ))
        attacks.append((
            "coordinate_tuple_to_list",
            lambda candidate: candidate[
                "candidate_legal_floor_sections"
            ][0].__setitem__(
                "coordinates",
                list(
                    candidate["candidate_legal_floor_sections"][0][
                        "coordinates"
                    ]
                ),
            ),
            "candidate_legal_floor_prefix_mismatch",
        ))
        for label, mutation, expected_failure in attacks:
            with self.subTest(label=label):
                candidate = deepcopy(projected)
                mutation(candidate)
                context = self._trusted_context(candidate, base)
                self.assertFalse(context["hard_pass"])
                self.assertEqual(
                    context["failure_reasons"],
                    [expected_failure],
                )

        for label, path in (
            ("ring_container_subclass", "ring"),
            ("point_container_subclass", "point"),
        ):
            with self.subTest(label=label):
                candidate = deepcopy(projected)
                coordinates = candidate[
                    "candidate_legal_floor_sections"
                ][0]["coordinates"]
                rings = list(coordinates)
                if path == "ring":
                    rings[0] = _ListSubclass(rings[0])
                else:
                    points = list(rings[0])
                    points[0] = _ListSubclass(points[0])
                    rings[0] = tuple(points)
                candidate["candidate_legal_floor_sections"][0][
                    "coordinates"
                ] = tuple(rings)
                context = self._trusted_context(candidate, base)
                self.assertFalse(context["hard_pass"])
                self.assertEqual(
                    context["failure_reasons"],
                    ["invalid_candidate_legal_section_schema"],
                )

        for label, path in (
            ("ring_tuple_to_list", "ring"),
            ("point_tuple_to_list", "point"),
        ):
            with self.subTest(label=label):
                candidate = deepcopy(projected)
                coordinates = candidate[
                    "candidate_legal_floor_sections"
                ][0]["coordinates"]
                rings = list(coordinates)
                if path == "ring":
                    rings[0] = list(rings[0])
                else:
                    points = list(rings[0])
                    points[0] = list(points[0])
                    rings[0] = tuple(points)
                candidate["candidate_legal_floor_sections"][0][
                    "coordinates"
                ] = tuple(rings)
                context = self._trusted_context(candidate, base)
                self.assertFalse(context["hard_pass"])
                self.assertEqual(
                    context["failure_reasons"],
                    ["candidate_legal_floor_prefix_mismatch"],
                )

    def test_candidate_context_rejects_invalid_target_vector_and_nonminimum_prefix(self):
        base = _base_contract()
        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        corruptions = (
            (
                "nonfinite_target",
                {"candidate_target_gfa_m2": nan},
                "invalid_candidate_target_gfa",
            ),
            (
                "nonfinite_vector",
                {"target_floor_areas_m2": [nan, 70.0, 70.0]},
                "invalid_candidate_floor_target_vector",
            ),
            (
                "capacity_exceeded",
                {"target_floor_areas_m2": [110.0, 50.0, 50.0]},
                "candidate_floor_target_exceeds_trusted_capacity",
            ),
            (
                "sum_mismatch",
                {"target_floor_areas_m2": [60.0, 60.0, 60.0]},
                "candidate_floor_target_sum_mismatch",
            ),
            (
                "aggregate_target_alias_mismatch",
                {"target_floor_area_m2": 211.0},
                "candidate_target_gfa_identity_mismatch",
            ),
            (
                "prefix_capacity_alias_mismatch",
                {"candidate_prefix_capacity_m2": 999.0},
                "candidate_prefix_capacity_identity_mismatch",
            ),
            (
                "forged_polygon_same_floor_count",
                {
                    "candidate_legal_floor_sections": [
                        mapping(box(0.0, 0.0, 200.0, 200.0)),
                        *projected["candidate_legal_floor_sections"][1:],
                    ],
                },
                "candidate_legal_floor_prefix_mismatch",
            ),
            (
                "floor_area_prefix_mismatch",
                {"legal_floor_section_areas_m2": [101.0, 100.0, 100.0]},
                "candidate_floor_area_prefix_mismatch",
            ),
            (
                "floor_capacity_prefix_mismatch",
                {"bcr_adjusted_floor_areas_m2": [99.0, 100.0, 100.0]},
                "candidate_floor_capacity_prefix_mismatch",
            ),
            (
                "nonminimum_prefix",
                {
                    "candidate_target_gfa_m2": 70.0,
                    "target_floor_area_m2": 70.0,
                    "target_floor_areas_m2": [
                        70.0 / 3.0,
                        70.0 / 3.0,
                        70.0 / 3.0,
                    ],
                },
                "candidate_floor_count_not_minimum_legal_prefix",
            ),
        )
        for label, changes, expected_failure in corruptions:
            with self.subTest(label=label):
                candidate = deepcopy(projected)
                candidate.update(changes)
                context = self._trusted_context(candidate, base)
                self.assertFalse(context["hard_pass"])
                self.assertIn(
                    expected_failure,
                    context["failure_reasons"],
                )

    def test_base_contract_rejects_embedded_legal_field_that_does_not_match_plan_anchor(self):
        plan = _floor_plan()
        plan["legal_floor_field"] = _floor_plan(
            pnu="1168011800104170005"
        )["legal_floor_field"]

        with self.assertRaisesRegex(
            ValueError,
            "legal_floor_field_authority_mismatch",
        ):
            build_feasible_capacity_contract(
                _context(),
                site_local_utm=box(0.0, 0.0, 20.0, 20.0),
                height_m=15.0,
                floors=5,
                target_utilization=0.90,
                minimum_utilization=0.40,
                floor_capacity_plan=plan,
            )

    def test_program_pool_rejects_coordinated_base_field_and_hash_replacement_against_run_anchor(self):
        trusted = _base_contract()
        coordinated = _base_contract(
            pnu="1168011800104170005"
        )

        with self.assertRaisesRegex(
            ValueError,
            "trusted_run_legal_floor_authority_mismatch",
        ):
            _program_pool(
                box(0.0, 0.0, 10.0, 10.0),
                "neighborhood living",
                15.0,
                5,
                base_capacity_contract=coordinated,
                trusted_legal_floor_field=trusted["legal_floor_field"],
                trusted_legal_floor_field_hash=trusted[
                    "legal_floor_field_hash"
                ],
                diagnostic_scope_labels=("1/1",),
                diagnostic_book_probe_count=1,
                diagnostic_evaluation_cap=1,
                diagnostic_candidate_cap=1,
            )

    def test_clear_span_explicit_dimensional_floor_count_is_preserved(self):
        context = _context(
            floor_height=4.0,
            legal_floors=7,
            far_limit=300.0,
        )
        site = box(0.0, 0.0, 20.0, 20.0)
        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="gymnasium",
            target_utilization=0.85,
            dimensional_context={
                "status": "feasible",
                "effective_height_m": 18.0,
                "effective_floors": 3,
            },
            pnu=PNU,
        )
        base = build_feasible_capacity_contract(
            context,
            site_local_utm=site,
            height_m=18.0,
            floors=3,
            target_utilization=0.85,
            floor_capacity_plan=plan,
        )

        projected = capacity_contract_for_alternative(
            base,
            {
                "alternative_id": "clear_span_low_target",
                "target_utilization": 0.50,
                "target_floor_area_m2": 120.0,
                "target_base_plan_area_m2": 40.0,
                "target_base_plan_coverage": 0.4,
            },
        )

        self.assertEqual(projected["requested_floors"], 3)
        self.assertEqual(projected["requested_height_m"], 18.0)
        self.assertEqual(
            projected["candidate_floor_count_authority"],
            "explicit_clear_span_dimensional_invariant",
        )
        self.assertEqual(len(projected["candidate_legal_floor_sections"]), 3)
        floor_context = _candidate_floor_context(
            projected,
            fallback_height=18.0,
            fallback_floors=3,
            trusted_legal_floor_field=base["legal_floor_field"],
            expected_legal_floor_field_hash=base[
                "legal_floor_field_hash"
            ],
            trusted_clear_span_floor_plan=plan,
        )
        self.assertTrue(floor_context["hard_pass"], floor_context)
        self.assertEqual(floor_context["floors"], 3)
        self.assertEqual(floor_context["height_m"], 18.0)

    def test_shared_floor_measurement_uses_prefix_without_resampling_or_upper_hosts(self):
        context = _context()
        site = box(0.0, 0.0, 20.0, 20.0)
        projected = capacity_contract_for_alternative(
            _base_contract(),
            {
                "alternative_id": "three_floor",
                "target_utilization": 210.0 / 2250.0,
                "target_floor_area_m2": 210.0,
                "target_base_plan_area_m2": 70.0,
                "target_base_plan_coverage": 0.7,
            },
        )
        plate = box(0.0, 0.0, 8.0, 8.0)
        source = SourceMass(
            name="candidate_three_floor",
            footprint=plate,
            volumes=(
                SourceVolume(
                    "main",
                    plate,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={
                "geometry_program_bridge_evidence": {
                    "program_hash": "a" * 64,
                    "geometry_hash": "b" * 64,
                },
            },
        )

        with patch(
            "design.maas.book_language.candidate_generation."
            "generation_site_at_height",
            side_effect=AssertionError("legal field must not be resampled"),
        ):
            floor_contract, measurement = _shared_floor_capacity_measurement(
                source,
                projected,
                generation_context=context,
                capacity_site=site,
                height=15.0,
                floors=5,
                pnu=PNU,
                trusted_legal_floor_field=projected[
                    "legal_floor_field"
                ],
                expected_legal_floor_field_hash=projected[
                    "legal_floor_field_hash"
                ],
            )

        self.assertEqual(floor_contract["totals"]["requested_floors"], 3)
        self.assertEqual(len(floor_contract["plates"]), 3)
        self.assertEqual(measurement["floor_area_m2"], 192.0)
