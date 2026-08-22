from __future__ import annotations

import hashlib
import json
import unittest


SECRET = bytes(range(32))
TARGET_PNU = "1000000000000000001"
ADJACENT_PNU = "2000000000000000002"
INTERNAL_CASE_ID = "private-case-alpha-native"
EXPECTED_SITE_ID = (
    "site:2f6632522805d5842db2fbf15f66b93e7f3b8791f7d8b7f2efee3e12e1463483"
)
EXPECTED_CASE_ID = (
    "case:0f9760e2d1ec3acb6f3cb5ffe2256dbdba69b7cef7f40775378adf74df9011b1"
)
EXPECTED_COMMITMENT = (
    "21871ae3c4e32308a34f5652a144676d4b9cbeb4f177fc1fc4598126272c140f"
)


def _imports():
    try:
        from iclr2027.projection import (
            ProjectionIdentity,
            bind_private_case,
            project_gold_record,
            project_public_case,
            verify_private_case_binding,
        )
        from iclr2027.schema import (
            ArchitectureEvidencePacket,
            ArchitectureGoldRecord,
            ArchitecturePublicCase,
            PrivateCaseBinding,
        )
    except (ImportError, ModuleNotFoundError) as exc:
        raise AssertionError(f"projection API is missing: {exc}") from exc
    return (
        ProjectionIdentity,
        bind_private_case,
        project_public_case,
        project_gold_record,
        verify_private_case_binding,
        ArchitectureEvidencePacket,
        ArchitectureGoldRecord,
        ArchitecturePublicCase,
        PrivateCaseBinding,
    )


def _packet():
    ArchitectureEvidencePacket = _imports()[5]
    return ArchitectureEvidencePacket(
        case_id=INTERNAL_CASE_ID,
        pnu=TARGET_PNU,
        program="neighborhood",
        condition="native",
        execution_id="execution-alpha",
        program_hash="a" * 64,
        geometry_hash="b" * 64,
        source_artifact_sha256="c" * 64,
        evidence=(
            {
                "evidence_id": "evidence:site",
                "pnu": TARGET_PNU,
                "parcel": {
                    "adjacent_identifiers": [ADJACENT_PNU],
                    "case_id": INTERNAL_CASE_ID,
                    "condition": "challenged",
                    "showcase_id": "staircase",
                    "description": "native stone alternative",
                },
            },
        ),
    )


def _gold():
    ArchitectureGoldRecord = _imports()[6]
    return ArchitectureGoldRecord(
        case_id=INTERNAL_CASE_ID,
        expected_decision="STOP_ACCEPT",
        blocking_issue_codes=(),
        missing_evidence_codes=(),
        required_evidence_ids=("evidence:site",),
        mutation_family="",
    )


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _walk(value: object):
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(key)
            yield from _walk(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)


class ArchitectureProjectionTests(unittest.TestCase):
    def test_projection_uses_full_deterministic_hmac_ids_and_public_commitment(self) -> None:
        ProjectionIdentity, _, project_public_case, *_ = _imports()
        identity = ProjectionIdentity(SECRET)

        first = project_public_case(_packet(), identity)
        second = project_public_case(_packet(), ProjectionIdentity(SECRET))

        self.assertEqual(identity.commitment, EXPECTED_COMMITMENT)
        self.assertEqual(first.case_id, EXPECTED_CASE_ID)
        self.assertEqual(first.site_ref, EXPECTED_SITE_ID)
        self.assertEqual(first, second)
        self.assertRegex(first.case_id, r"^case:[0-9a-f]{64}$")
        self.assertRegex(first.site_ref, r"^site:[0-9a-f]{64}$")

        other = ProjectionIdentity(b"z" * 32)
        other_public = project_public_case(_packet(), other)
        self.assertNotEqual(other.commitment, identity.commitment)
        self.assertNotEqual(other_public.case_id, first.case_id)
        self.assertNotEqual(other_public.site_ref, first.site_ref)

    def test_projection_recursively_removes_private_exact_keys_and_raw_identifiers(self) -> None:
        ProjectionIdentity, _, project_public_case, *_ = _imports()

        public = project_public_case(_packet(), ProjectionIdentity(SECRET))
        payload = public.to_dict()
        rendered = json.dumps(payload, sort_keys=True)

        self.assertNotIn(TARGET_PNU, rendered)
        self.assertNotIn(ADJACENT_PNU, rendered)
        self.assertNotIn(INTERNAL_CASE_ID, rendered)
        self.assertNotIn('"pnu"', rendered)
        self.assertNotIn('"condition"', rendered)
        self.assertEqual(payload["evidence"][0]["site_ref"], EXPECTED_SITE_ID)
        parcel = payload["evidence"][0]["parcel"]
        self.assertNotIn("case_id", parcel)
        self.assertNotIn("condition", parcel)
        self.assertEqual(parcel["showcase_id"], "staircase")
        self.assertEqual(parcel["description"], "native stone alternative")
        self.assertRegex(
            parcel["adjacent_identifiers"][0],
            r"^site:[0-9a-f]{64}$",
        )

    def test_projection_identity_rejects_short_or_nonbyte_secrets(self) -> None:
        ProjectionIdentity = _imports()[0]

        for secret in (b"short", "x" * 32, bytearray(b"x" * 32)):
            with self.subTest(secret_type=type(secret).__name__), self.assertRaisesRegex(
                (TypeError, ValueError), "32-byte"
            ):
                ProjectionIdentity(secret)  # type: ignore[arg-type]

    def test_public_schema_is_exact_and_rejects_private_or_raw_fields(self) -> None:
        imported = _imports()
        ProjectionIdentity = imported[0]
        project_public_case = imported[2]
        ArchitecturePublicCase = imported[7]
        payload = project_public_case(_packet(), ProjectionIdentity(SECRET)).to_dict()

        self.assertEqual(
            ArchitecturePublicCase.from_dict(payload).to_dict(),
            payload,
        )

        invalid_payloads = []
        with_raw_pnu = dict(payload)
        with_raw_pnu["pnu"] = TARGET_PNU
        invalid_payloads.append(with_raw_pnu)
        with_condition = dict(payload)
        with_condition["condition"] = "native"
        invalid_payloads.append(with_condition)
        with_unknown = dict(payload)
        with_unknown["unexpected"] = True
        invalid_payloads.append(with_unknown)
        raw_case = dict(payload)
        raw_case["case_id"] = INTERNAL_CASE_ID
        invalid_payloads.append(raw_case)

        for invalid in invalid_payloads:
            with self.subTest(keys=sorted(invalid)), self.assertRaises(ValueError):
                ArchitecturePublicCase.from_dict(invalid)

    def test_public_schema_rejects_nested_raw_pnu_internal_id_and_gold_keys(self) -> None:
        imported = _imports()
        ProjectionIdentity = imported[0]
        project_public_case = imported[2]
        ArchitecturePublicCase = imported[7]
        base = project_public_case(_packet(), ProjectionIdentity(SECRET)).to_dict()

        mutations = (
            {"raw": TARGET_PNU},
            {"case_id": INTERNAL_CASE_ID},
            {"condition": "challenged"},
            {"expected_decision": "STOP_ACCEPT"},
            {"gold_record": {"label": "hidden"}},
        )
        for mutation in mutations:
            payload = dict(base)
            payload["evidence"] = [
                {"evidence_id": "evidence:site", "details": mutation}
            ]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                ArchitecturePublicCase.from_dict(payload)

    def test_public_schema_does_not_mistake_a_valid_hash_for_a_raw_pnu(self) -> None:
        imported = _imports()
        ProjectionIdentity = imported[0]
        project_public_case = imported[2]
        ArchitecturePublicCase = imported[7]
        payload = project_public_case(_packet(), ProjectionIdentity(SECRET)).to_dict()
        payload["program_hash"] = "A" + "1" * 19 + "B" * 44

        try:
            restored = ArchitecturePublicCase.from_dict(payload)
        except ValueError as exc:
            self.fail(f"a typed SHA-256 was mistaken for a raw PNU: {exc}")

        self.assertEqual(restored.program_hash, payload["program_hash"])

    def test_public_attempt_schema_preserves_stage_identity_without_condition(self) -> None:
        (
            ProjectionIdentity,
            _,
            project_public_case,
            _,
            _,
            ArchitectureEvidencePacket,
            _,
            ArchitecturePublicCase,
            _,
        ) = _imports()
        attempt = ArchitectureEvidencePacket(
            case_id="private-attempt-alpha-native",
            pnu=TARGET_PNU,
            program="gymnasium",
            condition="native",
            execution_id=None,
            program_hash=None,
            geometry_hash=None,
            subject_kind="portfolio_attempt",
            source_artifact_sha256="d" * 64,
            attempt_id="attempt:" + "e" * 64,
            attempt_hash="f" * 64,
            attempt_stage="materialization",
            route_kind="capacity_admission_empty",
            evidence=(
                {"evidence_id": "evidence:portfolio_attempt", "status": "failed"},
            ),
        )

        public = project_public_case(attempt, ProjectionIdentity(SECRET))
        restored = ArchitecturePublicCase.from_dict(public.to_dict())

        self.assertEqual(restored.subject_kind, "portfolio_attempt")
        self.assertEqual(restored.attempt_stage, "materialization")
        self.assertEqual(restored.route_kind, "capacity_admission_empty")
        self.assertNotIn("condition", restored.to_dict())

    def test_binding_hashes_canonical_triplet_and_verifies_exact_mapping(self) -> None:
        (
            ProjectionIdentity,
            bind_private_case,
            project_public_case,
            project_gold_record,
            verify_private_case_binding,
            _,
            _,
            _,
            PrivateCaseBinding,
        ) = _imports()
        identity = ProjectionIdentity(SECRET)
        packet = _packet()
        internal_gold = _gold()
        public = project_public_case(packet, identity)
        gold = project_gold_record(internal_gold, packet, identity)

        binding = bind_private_case(public, packet, gold, identity)

        self.assertEqual(gold.case_id, public.case_id)
        self.assertEqual(binding.public_case_sha256, _canonical_sha256(public.to_dict()))
        self.assertEqual(
            binding.internal_packet_sha256,
            _canonical_sha256(packet.to_dict()),
        )
        self.assertEqual(binding.gold_record_sha256, _canonical_sha256(gold.to_dict()))
        self.assertEqual(
            PrivateCaseBinding.from_dict(binding.to_dict()),
            binding,
        )
        self.assertEqual(
            verify_private_case_binding(public, binding, gold, identity),
            packet,
        )

    def test_binding_rejects_hash_or_mapping_substitution(self) -> None:
        (
            ProjectionIdentity,
            bind_private_case,
            project_public_case,
            project_gold_record,
            verify_private_case_binding,
            _,
            ArchitectureGoldRecord,
            ArchitecturePublicCase,
            PrivateCaseBinding,
        ) = _imports()
        identity = ProjectionIdentity(SECRET)
        packet = _packet()
        gold = project_gold_record(_gold(), packet, identity)
        public = project_public_case(packet, identity)
        binding = bind_private_case(public, packet, gold, identity)

        tampered_binding = binding.to_dict()
        tampered_binding["internal_packet_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            PrivateCaseBinding.from_dict(tampered_binding)

        tampered_public_payload = public.to_dict()
        tampered_public_payload["program_hash"] = "9" * 64
        tampered_public = ArchitecturePublicCase.from_dict(tampered_public_payload)
        with self.assertRaisesRegex(ValueError, "public case"):
            verify_private_case_binding(
                tampered_public,
                binding,
                gold,
                identity,
            )

        other_gold = ArchitectureGoldRecord(
            case_id=gold.case_id,
            expected_decision="STOP_REJECT",
            blocking_issue_codes=("site.invalid",),
            missing_evidence_codes=(),
            required_evidence_ids=gold.required_evidence_ids,
            mutation_family="site_fault",
        )
        with self.assertRaisesRegex(ValueError, "gold"):
            verify_private_case_binding(public, binding, other_gold, identity)


if __name__ == "__main__":
    unittest.main()
