import hashlib
import json
from copy import deepcopy
from math import inf, nan
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language.actual_gfa_stop_certificate import (
    certify_candidate_actual_gfa_stop,
)
from design.maas.book_language import actual_gfa_stop_certificate as gfa_stop
from design.maas.book_language.floor_capacity_plan import (
    derive_program_floor_capacity_plan,
)
from design.maas.book_language.legal_floor_field import (
    materialize_legal_floor_field,
    validate_legal_floor_field,
)


def _context(*, legal_floors=25, far_limit=562.5):
    return SimpleNamespace(
        envelope=SimpleNamespace(
            floor_height=3.0,
            height_limit=legal_floors * 3.0,
            bcr_limit=60.0,
            far_limit=far_limit,
        ),
        generation_site=box(0.0, 0.0, 10.0, 10.0),
        sunlight_ring=(),
        evidence={},
    )


def _field(*, target_utilization=0.90, pnu="1168011800104170004"):
    plan = derive_program_floor_capacity_plan(
        _context(),
        site_local_utm=box(0.0, 0.0, 20.0, 20.0),
        building_type="neighborhood living",
        target_utilization=target_utilization,
        legacy_floor_hint=5,
        pnu=pnu,
    )
    return plan["legal_floor_field"]


def _identity(seed):
    return {
        "program_hash": seed * 64,
        "final_geometry_hash": chr(ord(seed) + 1) * 64,
        "visual_hash": chr(ord(seed) + 2) * 64,
    }


def _reseal_field(field):
    payload = dict(field)
    payload.pop("legal_floor_field_hash", None)
    payload["legal_floor_field_hash"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def _reseal_certificate(certificate):
    payload = dict(certificate)
    payload.pop("candidate_actual_gfa_stop_hash", None)
    payload["candidate_actual_gfa_stop_hash"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def _containment_rows(field, identity, areas):
    return [
        {
            "floor_number": index + 1,
            "contained": True,
            "actual_area_m2": area,
            "legal_floor_field_hash": field["legal_floor_field_hash"],
            **identity,
        }
        for index, area in enumerate(areas)
    ]


def _certify(field, *, identity, areas, target):
    return certify_candidate_actual_gfa_stop(
        legal_floor_field=field,
        expected_legal_floor_field_hash=field["legal_floor_field_hash"],
        expected_pnu=field["pnu"],
        expected_identity=identity,
        measured_identity=dict(identity),
        actual_floor_areas_m2=areas,
        containment_evidence=_containment_rows(field, identity, areas),
        target_gfa_m2=target,
    )


class _StringSubclass(str):
    pass


class _ListSubclass(list):
    pass


class _DictSubclass(dict):
    pass


class CandidateActualGfaStopCertificateTests(SimpleTestCase):
    def test_candidate_boundaries_require_trusted_legal_floor_field_hash(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        rows = _containment_rows(field, identity, areas)
        trusted_hash = field["legal_floor_field_hash"]

        try:
            certificate = certify_candidate_actual_gfa_stop(
                legal_floor_field=field,
                expected_legal_floor_field_hash=trusted_hash,
                expected_pnu=field["pnu"],
                expected_identity=identity,
                measured_identity=identity,
                actual_floor_areas_m2=areas,
                containment_evidence=rows,
                target_gfa_m2=100.0,
            )
        except TypeError as exc:
            self.fail(f"producer lacks required trusted-hash API: {exc}")
        self.assertTrue(certificate["hard_pass"])

        try:
            valid = (
                gfa_stop.validate_candidate_actual_gfa_stop_certificate(
                    certificate,
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=trusted_hash,
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    expected_target=100.0,
                )
            )
        except TypeError as exc:
            self.fail(f"validator lacks required trusted-hash API: {exc}")
        self.assertTrue(valid)

        malformed_hashes = (
            None,
            True,
            1,
            trusted_hash.upper(),
            f" {trusted_hash}",
            _StringSubclass(trusted_hash),
            "not-a-sha256",
        )
        for malformed_hash in malformed_hashes:
            with self.subTest(expected_hash=repr(malformed_hash)):
                rejected = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=malformed_hash,
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=rows,
                    target_gfa_m2=100.0,
                )
                self.assertFalse(rejected["hard_pass"])
                self.assertIn(
                    "invalid_expected_legal_floor_field_hash",
                    rejected["failure_reasons"],
                )
                self.assertFalse(
                    gfa_stop.validate_candidate_actual_gfa_stop_certificate(
                        certificate,
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=malformed_hash,
                        expected_pnu=field["pnu"],
                        expected_identity=identity,
                        expected_target=100.0,
                    )
                )

    def test_shortened_resealed_field_cannot_replace_trusted_authority(self):
        field = _field()
        trusted_hash = field["legal_floor_field_hash"]
        shortened = deepcopy(field)
        for key in (
            "legal_floor_top_heights_m",
            "legal_floor_section_areas_m2",
            "bcr_adjusted_floor_capacities_m2",
            "legal_floor_sections",
        ):
            shortened[key] = shortened[key][:-1]
        shortened["measured_usable_floor_count"] = 24
        shortened["height_field_capacity_m2"] = round(
            sum(shortened["bcr_adjusted_floor_capacities_m2"]),
            3,
        )
        shortened["feasible_maximum_gfa_m2"] = round(
            min(
                shortened["height_field_capacity_m2"],
                shortened["statutory_far_capacity_m2"],
            ),
            3,
        )
        shortened["statutory_far_reachable"] = bool(
            shortened["height_field_capacity_m2"] + 1e-9
            >= shortened["statutory_far_capacity_m2"]
        )
        shortened["terminal_floor_exclusion_reasons"] = []
        shortened = _reseal_field(shortened)

        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 23
        rows = _containment_rows(shortened, identity, areas)
        try:
            certificate = certify_candidate_actual_gfa_stop(
                legal_floor_field=shortened,
                expected_legal_floor_field_hash=trusted_hash,
                expected_pnu=shortened["pnu"],
                expected_identity=identity,
                measured_identity=identity,
                actual_floor_areas_m2=areas,
                containment_evidence=rows,
                target_gfa_m2=100.0,
            )
        except TypeError as exc:
            self.fail(f"producer lacks required trusted-hash API: {exc}")

        self.assertFalse(validate_legal_floor_field(shortened))
        self.assertFalse(certificate["hard_pass"])
        self.assertIn(
            "legal_floor_field_identity_mismatch",
            certificate["failure_reasons"],
        )
        self.assertEqual(
            certificate["failure_reasons"],
            ["legal_floor_field_identity_mismatch"],
        )
        self.assertFalse(
            gfa_stop.validate_candidate_actual_gfa_stop_certificate(
                certificate,
                legal_floor_field=shortened,
                expected_legal_floor_field_hash=trusted_hash,
                expected_pnu=shortened["pnu"],
                expected_identity=identity,
                expected_target=100.0,
            )
        )

    def test_full_legal_height_rejects_terminal_exclusion_reason(self):
        field = _field()
        forged = _reseal_field({
            **field,
            "terminal_floor_exclusion_reasons": [
                "missing_legal_floor_section",
            ],
        })

        self.assertFalse(validate_legal_floor_field(forged))

    def test_shortened_legal_field_requires_terminal_exclusion_reason(self):
        field = _field()
        shortened = deepcopy(field)
        for key in (
            "legal_floor_top_heights_m",
            "legal_floor_section_areas_m2",
            "bcr_adjusted_floor_capacities_m2",
            "legal_floor_sections",
        ):
            shortened[key] = shortened[key][:-1]
        shortened["measured_usable_floor_count"] = 24
        shortened["height_field_capacity_m2"] = round(
            sum(shortened["bcr_adjusted_floor_capacities_m2"]),
            3,
        )
        shortened["feasible_maximum_gfa_m2"] = round(
            min(
                shortened["height_field_capacity_m2"],
                shortened["statutory_far_capacity_m2"],
            ),
            3,
        )
        shortened["statutory_far_reachable"] = bool(
            shortened["height_field_capacity_m2"] + 1e-9
            >= shortened["statutory_far_capacity_m2"]
        )
        shortened["terminal_floor_exclusion_reasons"] = []

        self.assertFalse(
            validate_legal_floor_field(_reseal_field(shortened))
        )

    def test_terminal_exclusion_reason_requires_exact_allowlist(self):
        field = _field()
        unknown = _reseal_field({
            **field,
            "terminal_floor_exclusion_reasons": [
                "forged_terminal_reason",
            ],
        })

        self.assertFalse(validate_legal_floor_field(unknown))

    def test_genuine_terminal_area_and_clear_depth_fields_remain_valid(self):
        cases = (
            (
                lambda _context, top: (
                    box(0.0, 0.0, 10.0, 10.0)
                    if top <= 3.0
                    else (
                        box(0.0, 0.0, 10.0, 8.0)
                        if top <= 6.0
                        else box(0.0, 0.0, 2.0, 1.0)
                    )
                ),
                "insufficient_floor_area",
            ),
            (
                lambda _context, top: (
                    box(0.0, 0.0, 10.0, 10.0)
                    if top <= 3.0
                    else (
                        box(0.0, 0.0, 10.0, 8.0)
                        if top <= 6.0
                        else box(0.0, 0.0, 20.0, 1.5)
                    )
                ),
                "insufficient_clear_floor_depth",
            ),
        )

        for side_effect, expected_reason in cases:
            with self.subTest(reason=expected_reason), patch(
                "design.maas.book_language.legal_floor_field."
                "generation_site_at_height",
                side_effect=side_effect,
            ):
                field = materialize_legal_floor_field(
                    _context(),
                    site_local_utm=box(0.0, 0.0, 20.0, 20.0),
                    pnu="1168011800104170004",
                )
                self.assertTrue(validate_legal_floor_field(field))
                self.assertEqual(
                    field["measured_usable_floor_count"],
                    2,
                )
                self.assertIn(
                    expected_reason,
                    field["terminal_floor_exclusion_reasons"],
                )

    def test_pnu_authority_requires_exact_canonical_ascii_string(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        malformed_values = (
            1168011800104170004,
            1168011800104170004.0,
            True,
            _StringSubclass(field["pnu"]),
            f" {field['pnu']}",
            f"{field['pnu']} ",
            "１１６８０１１８００１０４１７０００４",
        )

        for malformed_pnu in malformed_values:
            with self.subTest(pnu=repr(malformed_pnu)):
                malformed_field = _reseal_field({
                    **field,
                    "pnu": malformed_pnu,
                })
                self.assertFalse(validate_legal_floor_field(malformed_field))
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=malformed_field,
                    expected_legal_floor_field_hash=(
                        malformed_field["legal_floor_field_hash"]
                    ),
                    expected_pnu=malformed_pnu,
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=_containment_rows(
                        malformed_field,
                        identity,
                        areas,
                    ),
                    target_gfa_m2=100.0,
                )
                self.assertFalse(certificate["hard_pass"])

                canonical_field_certificate = (
                    certify_candidate_actual_gfa_stop(
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=malformed_pnu,
                        expected_identity=identity,
                        measured_identity=identity,
                        actual_floor_areas_m2=areas,
                        containment_evidence=_containment_rows(
                            field,
                            identity,
                            areas,
                        ),
                        target_gfa_m2=100.0,
                    )
                )
                self.assertFalse(
                    canonical_field_certificate["hard_pass"],
                )
                self.assertIn(
                    "invalid_expected_pnu",
                    canonical_field_certificate["failure_reasons"],
                )

    def test_public_validator_requires_exact_expected_pnu(self):
        field = _field()
        identity = _identity("1")
        certificate = _certify(
            field,
            identity=identity,
            areas=(100.0,) + (0.0,) * 24,
            target=100.0,
        )
        validator = (
            gfa_stop.validate_candidate_actual_gfa_stop_certificate
        )

        self.assertTrue(
            validator(
                certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=100.0,
            )
        )
        for malformed_pnu in (
            None,
            1168011800104170004,
            1168011800104170004.0,
            True,
            _StringSubclass(field["pnu"]),
            f" {field['pnu']}",
            "1168011800104179999",
        ):
            with self.subTest(pnu=repr(malformed_pnu)):
                self.assertFalse(
                    validator(
                        certificate,
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=malformed_pnu,
                        expected_identity=identity,
                        expected_target=100.0,
                    )
                )

    def test_terminal_floor_exclusion_reasons_require_exact_bounded_strings(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        malformed_values = (
            "none",
            ("none",),
            [1],
            [True],
            [""],
            ["   "],
            ["x" * 257],
            [_StringSubclass("missing_legal_floor_section")],
            _ListSubclass(["missing_legal_floor_section"]),
        )

        for malformed_reasons in malformed_values:
            with self.subTest(reasons=repr(malformed_reasons)[:80]):
                malformed = _reseal_field({
                    **field,
                    "terminal_floor_exclusion_reasons": malformed_reasons,
                })
                self.assertFalse(validate_legal_floor_field(malformed))
                certificate = _certify(
                    malformed,
                    identity=identity,
                    areas=areas,
                    target=100.0,
                )
                self.assertFalse(certificate["hard_pass"])

    def test_legal_field_authority_containers_and_strings_are_exact_types(self):
        field = _field()
        typed_edits = (
            ("schema_version", _StringSubclass(field["schema_version"])),
            ("status", _StringSubclass(field["status"])),
            ("authority", _StringSubclass(field["authority"])),
            (
                "legal_floor_sections",
                _ListSubclass(field["legal_floor_sections"]),
            ),
            (
                "legal_floor_section_areas_m2",
                _ListSubclass(field["legal_floor_section_areas_m2"]),
            ),
            (
                "bcr_adjusted_floor_capacities_m2",
                _ListSubclass(field["bcr_adjusted_floor_capacities_m2"]),
            ),
            (
                "legal_floor_top_heights_m",
                _ListSubclass(field["legal_floor_top_heights_m"]),
            ),
        )
        for key, value in typed_edits:
            with self.subTest(key=key):
                self.assertFalse(
                    validate_legal_floor_field(
                        _reseal_field({
                            **field,
                            key: value,
                        })
                    )
                )

        first_section = _DictSubclass(field["legal_floor_sections"][0])
        malformed_sections = [
            first_section,
            *field["legal_floor_sections"][1:],
        ]
        self.assertFalse(
            validate_legal_floor_field(
                _reseal_field({
                    **field,
                    "legal_floor_sections": malformed_sections,
                })
            )
        )

        hash_subclass = {
            **field,
            "legal_floor_field_hash": _StringSubclass(
                field["legal_floor_field_hash"]
            ),
        }
        self.assertFalse(validate_legal_floor_field(hash_subclass))

    def test_legal_field_requires_exact_closed_schema_before_hashing(self):
        field = _field()
        required_keys = {
            "schema_version",
            "status",
            "authority",
            "pnu",
            "typical_floor_height_m",
            "legal_height_cap_m",
            "parcel_area_m2",
            "bcr_limit_pct",
            "bcr_footprint_capacity_m2",
            "far_limit_pct",
            "statutory_far_capacity_m2",
            "legal_floor_top_heights_m",
            "legal_floor_section_areas_m2",
            "bcr_adjusted_floor_capacities_m2",
            "legal_floor_sections",
            "measured_usable_floor_count",
            "height_field_capacity_m2",
            "feasible_maximum_gfa_m2",
            "statutory_far_reachable",
            "terminal_floor_exclusion_reasons",
            "candidate_floor_count",
            "candidate_target_gfa_m2",
            "candidate_identity",
            "legal_floor_field_hash",
        }
        self.assertEqual(set(field), required_keys)

        for unknown_key in (
            "extra_scalar",
            "candidate_selected_floor_count",
            "forged_far_authority",
        ):
            with self.subTest(unknown_key=unknown_key):
                malformed = _reseal_field({
                    **field,
                    unknown_key: 1,
                })
                self.assertFalse(validate_legal_floor_field(malformed))

        for missing_key in sorted(required_keys):
            with self.subTest(missing_key=missing_key):
                malformed = dict(field)
                malformed.pop(missing_key)
                if missing_key != "legal_floor_field_hash":
                    malformed = _reseal_field(malformed)
                self.assertFalse(validate_legal_floor_field(malformed))

    def test_legal_field_geojson_requires_exact_plain_nested_types(self):
        field = _field()

        malformed_sections = []

        extra_key = deepcopy(field["legal_floor_sections"])
        extra_key[0]["forged"] = 1
        malformed_sections.append(extra_key)

        missing_key = deepcopy(field["legal_floor_sections"])
        missing_key[0].pop("type")
        malformed_sections.append(missing_key)

        type_subclass = deepcopy(field["legal_floor_sections"])
        type_subclass[0]["type"] = _StringSubclass("Polygon")
        malformed_sections.append(type_subclass)

        outer_subclass = deepcopy(field["legal_floor_sections"])
        outer_subclass[0]["coordinates"] = _ListSubclass(
            outer_subclass[0]["coordinates"]
        )
        malformed_sections.append(outer_subclass)

        ring_subclass = deepcopy(field["legal_floor_sections"])
        coordinates = list(ring_subclass[0]["coordinates"])
        coordinates[0] = _ListSubclass(coordinates[0])
        ring_subclass[0]["coordinates"] = tuple(coordinates)
        malformed_sections.append(ring_subclass)

        point_subclass = deepcopy(field["legal_floor_sections"])
        coordinates = list(point_subclass[0]["coordinates"])
        ring = list(coordinates[0])
        ring[0] = _ListSubclass(ring[0])
        coordinates[0] = tuple(ring)
        point_subclass[0]["coordinates"] = tuple(coordinates)
        malformed_sections.append(point_subclass)

        bool_coordinate = deepcopy(field["legal_floor_sections"])
        coordinates = list(bool_coordinate[0]["coordinates"])
        ring = list(coordinates[0])
        point = list(ring[0])
        point[1] = False
        ring[0] = tuple(point)
        coordinates[0] = tuple(ring)
        bool_coordinate[0]["coordinates"] = tuple(coordinates)
        malformed_sections.append(bool_coordinate)

        string_coordinate = deepcopy(field["legal_floor_sections"])
        coordinates = list(string_coordinate[0]["coordinates"])
        ring = list(coordinates[0])
        point = list(ring[0])
        point[1] = str(point[1])
        ring[0] = tuple(point)
        coordinates[0] = tuple(ring)
        string_coordinate[0]["coordinates"] = tuple(coordinates)
        malformed_sections.append(string_coordinate)

        for index, sections in enumerate(malformed_sections):
            with self.subTest(index=index):
                malformed = _reseal_field({
                    **field,
                    "legal_floor_sections": sections,
                })
                self.assertFalse(validate_legal_floor_field(malformed))

    def test_identity_boundaries_require_exact_plain_closed_maps(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        rows = _containment_rows(field, identity, areas)
        valid_certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=100.0,
        )
        validator = gfa_stop.validate_candidate_actual_gfa_stop_certificate

        malformed_identities = (
            _DictSubclass(identity),
            {**identity, "extra": "forged"},
            {
                key: value
                for key, value in identity.items()
                if key != "visual_hash"
            },
            {
                **identity,
                "visual_hash": _StringSubclass(identity["visual_hash"]),
            },
        )
        for index, malformed_identity in enumerate(malformed_identities):
            with self.subTest(boundary="expected", index=index):
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=malformed_identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=rows,
                    target_gfa_m2=100.0,
                )
                self.assertFalse(certificate["hard_pass"])
                self.assertFalse(
                    validator(
                        valid_certificate,
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=field["pnu"],
                        expected_identity=malformed_identity,
                        expected_target=100.0,
                    )
                )

            with self.subTest(boundary="measured", index=index):
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=malformed_identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=rows,
                    target_gfa_m2=100.0,
                )
                self.assertFalse(certificate["hard_pass"])

    def test_containment_requires_exact_closed_plain_row_schema(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        valid_rows = _containment_rows(field, identity, areas)
        malformed_rows = []

        row_subclass = list(valid_rows)
        row_subclass[0] = _DictSubclass(row_subclass[0])
        malformed_rows.append(row_subclass)

        extra_key = [dict(row) for row in valid_rows]
        extra_key[0]["extra"] = "forged"
        malformed_rows.append(extra_key)

        missing_key = [dict(row) for row in valid_rows]
        missing_key[0].pop("visual_hash")
        malformed_rows.append(missing_key)

        string_subclass = [dict(row) for row in valid_rows]
        string_subclass[0]["legal_floor_field_hash"] = _StringSubclass(
            string_subclass[0]["legal_floor_field_hash"]
        )
        malformed_rows.append(string_subclass)

        for index, rows in enumerate(malformed_rows):
            with self.subTest(index=index):
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=rows,
                    target_gfa_m2=100.0,
                )
                self.assertFalse(certificate["hard_pass"])

        certificate = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=identity,
            measured_identity=identity,
            actual_floor_areas_m2=areas,
            containment_evidence=_ListSubclass(valid_rows),
            target_gfa_m2=100.0,
        )
        self.assertFalse(certificate["hard_pass"])

    def test_public_validator_requires_exact_closed_certificate_schema(self):
        field = _field()
        identity = _identity("1")
        certificate = _certify(
            field,
            identity=identity,
            areas=(100.0,) + (0.0,) * 24,
            target=100.0,
        )
        validator = gfa_stop.validate_candidate_actual_gfa_stop_certificate
        required_keys = {
            "schema_version",
            "status",
            "hard_pass",
            "legal_floor_field_hash",
            "identity",
            "program_hash",
            "final_geometry_hash",
            "visual_hash",
            "pnu",
            "target_gfa_m2",
            "actual_floor_areas_m2",
            "containment_evidence",
            "selected_floor_count",
            "terminal_floor_number",
            "achieved_gfa_m2",
            "terminal_residual_area_m2",
            "terminal_actual_area_m2",
            "terminal_overshoot_area_m2",
            "terminal_handling",
            "geometry_was_mutated",
            "failure_reasons",
            "candidate_actual_gfa_stop_hash",
        }
        self.assertEqual(set(certificate), required_keys)
        self.assertEqual(
            set(certificate["identity"]),
            {
                "program_hash",
                "final_geometry_hash",
                "visual_hash",
                "pnu",
            },
        )
        self.assertEqual(
            set(certificate["containment_evidence"][0]),
            {
                "floor_number",
                "contained",
                "actual_area_m2",
                "legal_floor_field_hash",
                "program_hash",
                "final_geometry_hash",
                "visual_hash",
            },
        )

        unknown = _reseal_certificate({
            **certificate,
            "unknown": "forged",
        })
        self.assertFalse(
            validator(
                unknown,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=100.0,
            )
        )
        for missing_key in sorted(required_keys):
            with self.subTest(missing_key=missing_key):
                malformed = dict(certificate)
                malformed.pop(missing_key)
                if missing_key != "candidate_actual_gfa_stop_hash":
                    malformed = _reseal_certificate(malformed)
                self.assertFalse(
                    validator(
                        malformed,
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=field["pnu"],
                        expected_identity=identity,
                        expected_target=100.0,
                    )
                )

        type_edits = (
            ("schema_version", _StringSubclass(certificate["schema_version"])),
            ("status", _StringSubclass(certificate["status"])),
            ("hard_pass", 1),
            (
                "legal_floor_field_hash",
                _StringSubclass(certificate["legal_floor_field_hash"]),
            ),
            ("program_hash", _StringSubclass(certificate["program_hash"])),
            ("selected_floor_count", True),
            ("terminal_floor_number", True),
            (
                "terminal_handling",
                _StringSubclass(certificate["terminal_handling"]),
            ),
            ("geometry_was_mutated", 0),
            (
                "failure_reasons",
                _ListSubclass(certificate["failure_reasons"]),
            ),
        )
        for key, value in type_edits:
            with self.subTest(key=key):
                malformed = _reseal_certificate({
                    **certificate,
                    key: value,
                })
                self.assertFalse(
                    validator(
                        malformed,
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=field["pnu"],
                        expected_identity=identity,
                        expected_target=100.0,
                    )
                )

        nested_identity = {
            **certificate["identity"],
            "pnu": _StringSubclass(certificate["identity"]["pnu"]),
        }
        malformed = _reseal_certificate({
            **certificate,
            "identity": nested_identity,
        })
        self.assertFalse(
            validator(
                malformed,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=100.0,
            )
        )

    def test_target_and_actual_total_above_legal_far_capacity_fail_closed(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) * 23 + (0.0,) * 2

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=2300.0,
        )

        self.assertEqual(field["feasible_maximum_gfa_m2"], 2250.0)
        self.assertFalse(certificate["hard_pass"])
        self.assertEqual(certificate["status"], "rejected")
        self.assertIn(
            "target_gfa_exceeds_legal_capacity",
            certificate["failure_reasons"],
        )
        self.assertIn(
            "actual_gfa_exceeds_legal_capacity",
            certificate["failure_reasons"],
        )

    def test_malformed_self_rehashed_floor_count_fails_without_exception(self):
        field = _field()
        malformed = _reseal_field({
            **field,
            "measured_usable_floor_count": "x",
        })
        identity = _identity("1")

        self.assertFalse(validate_legal_floor_field(malformed))
        certificate = _certify(
            malformed,
            identity=identity,
            areas=(100.0,) + (0.0,) * 24,
            target=100.0,
        )
        self.assertFalse(certificate["hard_pass"])
        self.assertIn(
            "invalid_legal_floor_field",
            certificate["failure_reasons"],
        )

    def test_public_validator_recomputes_and_rejects_self_rehashed_edits(self):
        validator = getattr(
            gfa_stop,
            "validate_candidate_actual_gfa_stop_certificate",
            None,
        )
        self.assertIsNotNone(validator)

        field = _field()
        identity = _identity("1")
        areas = (100.0, 100.0, 10.0) + (0.0,) * 22
        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=210.0,
        )

        self.assertIn("containment_evidence", certificate)
        self.assertTrue(
            validator(
                certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=210.0,
            )
        )
        tampered_payloads = (
            {
                **certificate,
                "status": "rejected",
                "hard_pass": False,
            },
            {
                **certificate,
                "pnu": "1168011800104179999",
                "identity": {
                    **certificate["identity"],
                    "pnu": "1168011800104179999",
                },
            },
            {
                **certificate,
                "legal_floor_field_hash": "f" * 64,
            },
            {
                **certificate,
                "actual_floor_areas_m2": [
                    100.0,
                    100.0,
                    9.0,
                    *([0.0] * 22),
                ],
            },
            {
                **certificate,
                "selected_floor_count": 4,
                "terminal_floor_number": 4,
            },
            {
                **certificate,
                "terminal_actual_area_m2": 9.0,
            },
        )
        for tampered in tampered_payloads:
            with self.subTest(tampered=tuple(sorted(
                key
                for key in tampered
                if tampered.get(key) != certificate.get(key)
            ))):
                self.assertFalse(
                    validator(
                        _reseal_certificate(tampered),
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=field["pnu"],
                        expected_identity=identity,
                        expected_target=210.0,
                    )
                )

        self.assertFalse(
            validator(
                certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity={
                    **identity,
                    "visual_hash": "f" * 64,
                },
                expected_target=210.0,
            )
        )
        self.assertFalse(
            validator(
                certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=211.0,
            )
        )

    def test_public_validator_rejects_nonserializable_payload_without_exception(self):
        validator = getattr(
            gfa_stop,
            "validate_candidate_actual_gfa_stop_certificate",
        )
        field = _field()
        identity = _identity("1")
        certificate = _certify(
            field,
            identity=identity,
            areas=(100.0,) + (0.0,) * 24,
            target=100.0,
        )
        malformed = {
            **certificate,
            "containment_evidence": [object()],
        }

        self.assertFalse(
            validator(
                malformed,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=100.0,
            )
        )

    def test_public_validator_rejects_invalid_expected_authority_inputs(self):
        validator = gfa_stop.validate_candidate_actual_gfa_stop_certificate
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        rows = _containment_rows(field, identity, areas)
        invalid_target_certificate = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=identity,
            measured_identity=identity,
            actual_floor_areas_m2=areas,
            containment_evidence=rows,
            target_gfa_m2="100.0",
        )
        invalid_identity = {
            **identity,
            "visual_hash": "not-a-sha256",
        }
        invalid_identity_certificate = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=invalid_identity,
            measured_identity=invalid_identity,
            actual_floor_areas_m2=areas,
            containment_evidence=_containment_rows(
                field,
                invalid_identity,
                areas,
            ),
            target_gfa_m2=100.0,
        )

        self.assertFalse(
            validator(
                invalid_target_certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target="100.0",
            )
        )
        self.assertFalse(
            validator(
                invalid_identity_certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=invalid_identity,
                expected_target=100.0,
            )
        )

    def test_tolerance_override_cannot_change_legal_authority(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) * 22 + (50.0,) + (0.0,) * 2
        rows = _containment_rows(field, identity, areas)

        for invalid_tolerance in (
            1.0,
            inf,
            1e300,
            nan,
            None,
            "0.001",
            True,
            0.0,
            -1.0,
        ):
            with self.subTest(tolerance=invalid_tolerance):
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=rows,
                    target_gfa_m2=2251.0,
                    tolerance_m2=invalid_tolerance,
                )

                self.assertFalse(certificate["hard_pass"])
                self.assertEqual(certificate["status"], "rejected")
                self.assertIn(
                    "invalid_tolerance_m2",
                    certificate["failure_reasons"],
                )

        default_certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=2250.0,
        )
        exact_constant_certificate = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=identity,
            measured_identity=identity,
            actual_floor_areas_m2=areas,
            containment_evidence=rows,
            target_gfa_m2=2250.0,
            tolerance_m2=1e-6,
        )
        self.assertTrue(default_certificate["hard_pass"])
        self.assertEqual(default_certificate, exact_constant_certificate)

    def test_producer_rejects_non_json_containment_without_exception(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        valid_rows = _containment_rows(field, identity, areas)
        malformed_cases = (
            [object()] * 25,
            [
                {
                    **row,
                    "nonserializable_extra": object(),
                }
                for row in valid_rows
            ],
            [
                {
                    **row,
                    "floor_number": inf if index == 0 else index + 1,
                }
                for index, row in enumerate(valid_rows)
            ],
        )

        for malformed in malformed_cases:
            with self.subTest(kind=type(malformed[0]).__name__):
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=malformed,
                    target_gfa_m2=100.0,
                )

                self.assertFalse(certificate["hard_pass"])
                self.assertEqual(certificate["status"], "rejected")
                self.assertIn(
                    "invalid_containment_evidence",
                    certificate["failure_reasons"],
                )
                self.assertEqual(
                    len(certificate["candidate_actual_gfa_stop_hash"]),
                    64,
                )
                json.dumps(certificate, allow_nan=False)

    def test_containment_rows_require_exact_json_scalar_types(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        valid_rows = _containment_rows(field, identity, areas)
        valid_certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=100.0,
        )
        validator = gfa_stop.validate_candidate_actual_gfa_stop_certificate
        edits = (
            ("floor_number", "1"),
            ("floor_number", True),
            ("floor_number", 1.0),
            ("floor_number", inf),
            ("actual_area_m2", "100.0"),
            ("actual_area_m2", True),
            ("actual_area_m2", inf),
            ("actual_area_m2", nan),
        )

        for key, value in edits:
            with self.subTest(key=key, value=value):
                rows = [dict(row) for row in valid_rows]
                rows[0][key] = value
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=rows,
                    target_gfa_m2=100.0,
                )
                self.assertFalse(certificate["hard_pass"])
                self.assertIn(
                    "invalid_containment_evidence",
                    certificate["failure_reasons"],
                )

                tampered = {
                    **valid_certificate,
                    "containment_evidence": rows,
                }
                self.assertFalse(
                    validator(
                        _reseal_certificate(tampered),
                        legal_floor_field=field,
                        expected_legal_floor_field_hash=(
                            field["legal_floor_field_hash"]
                        ),
                        expected_pnu=field["pnu"],
                        expected_identity=identity,
                        expected_target=100.0,
                    )
                )

    def test_actual_area_vector_requires_finite_json_numbers_not_bool_or_string(self):
        field = _field()
        identity = _identity("1")

        for invalid_area in ("100.0", True, inf, nan):
            with self.subTest(area=invalid_area):
                areas = (invalid_area,) + (0.0,) * 24
                certificate = certify_candidate_actual_gfa_stop(
                    legal_floor_field=field,
                    expected_legal_floor_field_hash=(
                        field["legal_floor_field_hash"]
                    ),
                    expected_pnu=field["pnu"],
                    expected_identity=identity,
                    measured_identity=identity,
                    actual_floor_areas_m2=areas,
                    containment_evidence=_containment_rows(
                        field,
                        identity,
                        areas,
                    ),
                    target_gfa_m2=100.0,
                )
                self.assertFalse(certificate["hard_pass"])
                self.assertIn(
                    "invalid_actual_floor_area",
                    certificate["failure_reasons"],
                )

        integer_areas = (100,) + (0,) * 24
        integer_certificate = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=identity,
            measured_identity=identity,
            actual_floor_areas_m2=integer_areas,
            containment_evidence=_containment_rows(
                field,
                identity,
                integer_areas,
            ),
            target_gfa_m2=100,
        )
        self.assertTrue(integer_certificate["hard_pass"])
        self.assertTrue(
            gfa_stop.validate_candidate_actual_gfa_stop_certificate(
                integer_certificate,
                legal_floor_field=field,
                expected_legal_floor_field_hash=(
                    field["legal_floor_field_hash"]
                ),
                expected_pnu=field["pnu"],
                expected_identity=identity,
                expected_target=100,
            )
        )

    def test_legal_field_rejects_self_rehashed_numeric_type_edits(self):
        field = _field()

        for key in (
            "typical_floor_height_m",
            "statutory_far_capacity_m2",
            "feasible_maximum_gfa_m2",
        ):
            with self.subTest(key=key):
                malformed = _reseal_field({
                    **field,
                    key: str(field[key]),
                })
                self.assertFalse(validate_legal_floor_field(malformed))

    def test_shared_legal_field_is_independent_of_target_and_candidate_floor_count(self):
        field_a = _field(target_utilization=0.70)
        field_b = _field(target_utilization=0.95)

        self.assertTrue(validate_legal_floor_field(field_a))
        self.assertEqual(
            field_a["legal_floor_field_hash"],
            field_b["legal_floor_field_hash"],
        )
        self.assertEqual(field_a["measured_usable_floor_count"], 25)
        self.assertEqual(field_a["pnu"], "1168011800104170004")
        self.assertNotEqual(
            field_a["legal_floor_field_hash"],
            _field(pnu="1168011800104170005")["legal_floor_field_hash"],
        )

        identity_a = _identity("1")
        identity_b = _identity("4")
        areas_3 = (100.0, 100.0, 10.0) + (0.0,) * 22
        areas_7 = (100.0,) * 6 + (50.0,) + (0.0,) * 18
        certificate_3 = _certify(
            field_a,
            identity=identity_a,
            areas=areas_3,
            target=210.0,
        )
        certificate_7 = _certify(
            field_a,
            identity=identity_b,
            areas=areas_7,
            target=650.0,
        )

        self.assertTrue(certificate_3["hard_pass"])
        self.assertEqual(certificate_3["selected_floor_count"], 3)
        self.assertTrue(certificate_7["hard_pass"])
        self.assertEqual(certificate_7["selected_floor_count"], 7)
        self.assertEqual(
            certificate_3["legal_floor_field_hash"],
            certificate_7["legal_floor_field_hash"],
        )

    def test_twenty_plus_floor_candidate_stops_at_minimal_actual_floor(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) * 22 + (50.0,) + (0.0,) * 2

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=2250.0,
        )

        self.assertTrue(certificate["hard_pass"])
        self.assertEqual(certificate["status"], "certified")
        self.assertEqual(certificate["selected_floor_count"], 23)
        self.assertEqual(certificate["terminal_floor_number"], 23)
        self.assertEqual(certificate["terminal_residual_area_m2"], 50.0)
        self.assertEqual(certificate["terminal_overshoot_area_m2"], 0.0)
        self.assertEqual(certificate["terminal_handling"], "exact_stop")

    def test_unauthored_terminal_overshoot_fails_closed(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0, 100.0, 20.0) + (0.0,) * 22

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=210.0,
        )

        self.assertFalse(certificate["hard_pass"])
        self.assertEqual(certificate["status"], "rejected")
        self.assertEqual(certificate["selected_floor_count"], 3)
        self.assertEqual(certificate["terminal_residual_area_m2"], 10.0)
        self.assertEqual(certificate["terminal_overshoot_area_m2"], 10.0)
        self.assertEqual(
            certificate["terminal_handling"],
            "reject_unauthored_terminal_adjustment",
        )
        self.assertIn(
            "uncorrected_gfa_overshoot",
            certificate["failure_reasons"],
        )

    def test_floor_sum_accepts_bounded_mesh_overlay_error(self):
        field = _field()
        identity = _identity("1")
        areas = (
            50.000003,
            50.000003,
            50.000002,
            50.000002,
        ) + (0.0,) * 21

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=200.0,
        )

        self.assertTrue(certificate["hard_pass"])
        self.assertEqual(certificate["status"], "certified")
        self.assertEqual(certificate["selected_floor_count"], 4)
        self.assertEqual(certificate["terminal_overshoot_area_m2"], 0.00001)

    def test_floor_sum_overshoot_above_mesh_overlay_bound_fails_closed(self):
        field = _field()
        identity = _identity("1")
        areas = (
            50.000005,
            50.000005,
            50.000005,
            50.000005,
        ) + (0.0,) * 21

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=200.0,
        )

        self.assertFalse(certificate["hard_pass"])
        self.assertIn(
            "uncorrected_gfa_overshoot",
            certificate["failure_reasons"],
        )

    def test_legal_field_exhaustion_returns_target_unreachable(self):
        field = _field()
        identity = _identity("1")
        areas = (50.0,) * 25

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=2250.0,
        )

        self.assertFalse(certificate["hard_pass"])
        self.assertEqual(certificate["status"], "target_unreachable")
        self.assertIn(
            "legal_floor_field_exhausted_before_target",
            certificate["failure_reasons"],
        )

    def test_positive_floor_above_first_target_hit_is_nonminimal(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0, 100.0, 10.0, 5.0) + (0.0,) * 21

        certificate = _certify(
            field,
            identity=identity,
            areas=areas,
            target=210.0,
        )

        self.assertEqual(certificate["status"], "rejected")
        self.assertEqual(certificate["selected_floor_count"], 3)
        self.assertIn("nonminimal_floor_count", certificate["failure_reasons"])

    def test_nonfinite_area_and_missing_containment_fail_closed(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0, nan) + (0.0,) * 23
        nonfinite = _certify(
            field,
            identity=identity,
            areas=areas,
            target=100.0,
        )

        self.assertEqual(nonfinite["status"], "rejected")
        self.assertIn("nonfinite_actual_floor_area", nonfinite["failure_reasons"])

        valid_areas = (100.0,) + (0.0,) * 24
        missing = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=identity,
            measured_identity=dict(identity),
            actual_floor_areas_m2=valid_areas,
            containment_evidence=_containment_rows(
                field,
                identity,
                valid_areas,
            )[:-1],
            target_gfa_m2=100.0,
        )

        self.assertEqual(missing["status"], "rejected")
        self.assertIn(
            "containment_evidence_count_mismatch",
            missing["failure_reasons"],
        )

    def test_identity_mismatch_and_field_tamper_fail_closed(self):
        field = _field()
        identity = _identity("1")
        areas = (100.0,) + (0.0,) * 24
        forged_identity = dict(identity)
        forged_identity["visual_hash"] = "f" * 64

        mismatch = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu=field["pnu"],
            expected_identity=identity,
            measured_identity=forged_identity,
            actual_floor_areas_m2=areas,
            containment_evidence=_containment_rows(
                field,
                forged_identity,
                areas,
            ),
            target_gfa_m2=100.0,
        )

        self.assertEqual(mismatch["status"], "rejected")
        self.assertIn("candidate_identity_mismatch", mismatch["failure_reasons"])

        wrong_pnu = certify_candidate_actual_gfa_stop(
            legal_floor_field=field,
            expected_legal_floor_field_hash=(
                field["legal_floor_field_hash"]
            ),
            expected_pnu="1168011800104179999",
            expected_identity=identity,
            measured_identity=dict(identity),
            actual_floor_areas_m2=areas,
            containment_evidence=_containment_rows(
                field,
                identity,
                areas,
            ),
            target_gfa_m2=100.0,
        )
        self.assertEqual(wrong_pnu["status"], "rejected")
        self.assertIn("pnu_identity_mismatch", wrong_pnu["failure_reasons"])

        tampered_field = {
            **field,
            "far_limit_pct": field["far_limit_pct"] + 1.0,
        }
        tampered = _certify(
            tampered_field,
            identity=identity,
            areas=areas,
            target=100.0,
        )
        self.assertEqual(tampered["status"], "rejected")
        self.assertIn("invalid_legal_floor_field", tampered["failure_reasons"])

    def test_self_rehashed_inconsistent_capacity_and_floor_cadence_are_rejected(self):
        field = _field()
        inconsistent_capacity = _reseal_field({
            **field,
            "feasible_maximum_gfa_m2": (
                field["feasible_maximum_gfa_m2"] + 1.0
            ),
        })
        self.assertFalse(validate_legal_floor_field(inconsistent_capacity))

        wrong_tops = list(field["legal_floor_top_heights_m"])
        wrong_tops[3] += 0.25
        inconsistent_cadence = _reseal_field({
            **field,
            "legal_floor_top_heights_m": wrong_tops,
        })
        self.assertFalse(validate_legal_floor_field(inconsistent_cadence))
